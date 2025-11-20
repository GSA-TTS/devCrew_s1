"""
Prometheus Integration Wrapper for APM & Monitoring Platform.

This module provides a high-level wrapper around the Prometheus HTTP API
for querying metrics, checking service health, and managing metric collection.

Supports:
- Prometheus client setup and configuration
- Metric registration and collection
- Query execution and result parsing
- Error handling and retry logic
- Connection pooling and timeout management
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class PrometheusError(Exception):
    """Base exception for Prometheus-related errors."""

    pass


class PrometheusConnectionError(PrometheusError):
    """Raised when unable to connect to Prometheus server."""

    pass


class PrometheusQueryError(PrometheusError):
    """Raised when a Prometheus query fails."""

    pass


class PrometheusWrapper:
    """
    Wrapper class for Prometheus HTTP API interactions.

    Provides methods for:
    - Executing instant and range queries
    - Checking Prometheus server health
    - Retrieving metric metadata
    - Managing query timeouts and retries
    """

    def __init__(
        self,
        base_url: str = "http://localhost:9090",
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: bool = True,
    ):
        """
        Initialize Prometheus wrapper.

        Args:
            base_url: Base URL of Prometheus server
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.info(f"Initialized PrometheusWrapper with base_url={base_url}")

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for API endpoint."""
        return urljoin(self.base_url, endpoint)

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Prometheus API.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            params: Query parameters
            data: Request body data

        Returns:
            Parsed JSON response

        Raises:
            PrometheusConnectionError: If connection fails
            PrometheusQueryError: If query returns error status
        """
        url = self._build_url(endpoint)

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                data=data,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            result = response.json()

            # Check Prometheus API status
            if result.get("status") == "error":
                error_msg = result.get("error", "Unknown error")
                logger.error(f"Prometheus query error: {error_msg}")
                raise PrometheusQueryError(f"Query failed: {error_msg}")

            return result

        except requests.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to Prometheus: {e}")
            raise PrometheusConnectionError(
                f"Cannot connect to Prometheus at {url}"
            ) from e
        except requests.exceptions.Timeout as e:
            logger.error(f"Prometheus request timeout: {e}")
            raise PrometheusConnectionError(f"Request timeout: {url}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Prometheus request failed: {e}")
            raise PrometheusError(f"Request failed: {e}") from e

    def query(self, query: str, time_param: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute instant Prometheus query.

        Args:
            query: PromQL query string
            time_param: Optional evaluation timestamp (RFC3339 or Unix timestamp)

        Returns:
            Query result dictionary with 'data' key containing results

        Raises:
            PrometheusQueryError: If query fails
        """
        logger.debug(f"Executing instant query: {query}")

        params = {"query": query}
        if time_param:
            params["time"] = time_param

        result = self._make_request("GET", "/api/v1/query", params=params)

        logger.info(f"Query returned {len(result.get('data', {}).get('result', []))} results")
        return result

    def query_range(
        self,
        query: str,
        start: Union[str, datetime],
        end: Union[str, datetime],
        step: str = "15s",
    ) -> Dict[str, Any]:
        """
        Execute range Prometheus query.

        Args:
            query: PromQL query string
            start: Range start time (RFC3339, Unix timestamp, or datetime)
            end: Range end time (RFC3339, Unix timestamp, or datetime)
            step: Query resolution step width (e.g., '15s', '1m', '1h')

        Returns:
            Query result dictionary with time series data

        Raises:
            PrometheusQueryError: If query fails
        """
        logger.debug(f"Executing range query: {query} from {start} to {end}")

        # Convert datetime objects to Unix timestamps
        if isinstance(start, datetime):
            start = str(int(start.timestamp()))
        if isinstance(end, datetime):
            end = str(int(end.timestamp()))

        params = {"query": query, "start": start, "end": end, "step": step}

        result = self._make_request("GET", "/api/v1/query_range", params=params)

        logger.info(f"Range query returned {len(result.get('data', {}).get('result', []))} series")
        return result

    def check_health(self) -> bool:
        """
        Check if Prometheus server is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            result = self._make_request("GET", "/-/healthy")
            logger.info("Prometheus health check: OK")
            return True
        except PrometheusError as e:
            logger.warning(f"Prometheus health check failed: {e}")
            return False

    def check_ready(self) -> bool:
        """
        Check if Prometheus server is ready to serve traffic.

        Returns:
            True if ready, False otherwise
        """
        try:
            result = self._make_request("GET", "/-/ready")
            logger.info("Prometheus readiness check: OK")
            return True
        except PrometheusError as e:
            logger.warning(f"Prometheus readiness check failed: {e}")
            return False

    def get_labels(self, match: Optional[List[str]] = None) -> List[str]:
        """
        Get list of label names.

        Args:
            match: Optional list of series selectors to filter labels

        Returns:
            List of label names
        """
        logger.debug("Fetching label names")

        params = {}
        if match:
            params["match[]"] = match

        result = self._make_request("GET", "/api/v1/labels", params=params)

        labels = result.get("data", [])
        logger.info(f"Retrieved {len(labels)} labels")
        return labels

    def get_label_values(
        self, label: str, match: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get list of values for a specific label.

        Args:
            label: Label name
            match: Optional list of series selectors to filter values

        Returns:
            List of label values
        """
        logger.debug(f"Fetching values for label: {label}")

        params = {}
        if match:
            params["match[]"] = match

        result = self._make_request(
            "GET", f"/api/v1/label/{label}/values", params=params
        )

        values = result.get("data", [])
        logger.info(f"Retrieved {len(values)} values for label {label}")
        return values

    def get_series(
        self,
        match: List[str],
        start: Optional[Union[str, datetime]] = None,
        end: Optional[Union[str, datetime]] = None,
    ) -> List[Dict[str, str]]:
        """
        Get list of time series matching selectors.

        Args:
            match: List of series selectors
            start: Optional start time
            end: Optional end time

        Returns:
            List of series label sets
        """
        logger.debug(f"Fetching series for matchers: {match}")

        params = {"match[]": match}

        if start:
            if isinstance(start, datetime):
                start = str(int(start.timestamp()))
            params["start"] = start

        if end:
            if isinstance(end, datetime):
                end = str(int(end.timestamp()))
            params["end"] = end

        result = self._make_request("GET", "/api/v1/series", params=params)

        series = result.get("data", [])
        logger.info(f"Retrieved {len(series)} series")
        return series

    def get_targets(self) -> Dict[str, Any]:
        """
        Get current state of target discovery.

        Returns:
            Dictionary with active and dropped targets
        """
        logger.debug("Fetching targets")

        result = self._make_request("GET", "/api/v1/targets")

        data = result.get("data", {})
        active_count = len(data.get("activeTargets", []))
        dropped_count = len(data.get("droppedTargets", []))

        logger.info(f"Retrieved {active_count} active and {dropped_count} dropped targets")
        return data

    def get_rules(self) -> Dict[str, Any]:
        """
        Get currently loaded alerting and recording rules.

        Returns:
            Dictionary with rule groups
        """
        logger.debug("Fetching rules")

        result = self._make_request("GET", "/api/v1/rules")

        data = result.get("data", {})
        groups = data.get("groups", [])

        logger.info(f"Retrieved {len(groups)} rule groups")
        return data

    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Get list of all active alerts.

        Returns:
            List of active alerts
        """
        logger.debug("Fetching alerts")

        result = self._make_request("GET", "/api/v1/alerts")

        alerts = result.get("data", {}).get("alerts", [])
        logger.info(f"Retrieved {len(alerts)} active alerts")
        return alerts

    def close(self):
        """Close the session and cleanup resources."""
        self.session.close()
        logger.info("PrometheusWrapper session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
