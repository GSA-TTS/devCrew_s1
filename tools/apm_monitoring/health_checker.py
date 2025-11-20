"""
Health Check Monitoring for APM & Monitoring Platform.

This module provides comprehensive health checking capabilities for services,
including HTTP endpoint monitoring, service availability tracking, response
time measurement, and health status aggregation.

Supports:
- HTTP endpoint health checks with configurable intervals
- Service availability tracking over time
- Response time monitoring and statistics
- Health status aggregation across multiple endpoints
- Custom health check validators
"""

import logging
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""

    endpoint: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "endpoint": self.endpoint,
            "status": self.status.value,
            "response_time_ms": self.response_time_ms,
            "status_code": self.status_code,
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class HealthCheckConfig:
    """Configuration for a health check endpoint."""

    url: str
    name: str
    interval_seconds: int = 30
    timeout_seconds: int = 10
    expected_status_code: int = 200
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
    validator: Optional[Callable[[requests.Response], bool]] = None


class HealthChecker:
    """
    Service health check monitor with configurable intervals and validators.

    Monitors HTTP endpoints for availability, response times, and custom
    health criteria. Maintains history of check results for trend analysis.
    """

    def __init__(
        self,
        check_interval: int = 30,
        max_history: int = 1000,
    ):
        """
        Initialize health checker.

        Args:
            check_interval: Default interval between checks in seconds
            max_history: Maximum number of historical results to retain per endpoint
        """
        self.check_interval = check_interval
        self.max_history = max_history
        self.endpoints: Dict[str, HealthCheckConfig] = {}
        self.history: Dict[str, List[HealthCheckResult]] = {}
        self.session = requests.Session()

        logger.info(
            f"Initialized HealthChecker with interval={check_interval}s, "
            f"max_history={max_history}"
        )

    def add_endpoint(self, config: HealthCheckConfig):
        """
        Add endpoint to monitor.

        Args:
            config: Health check configuration
        """
        self.endpoints[config.name] = config
        self.history[config.name] = []
        logger.info(f"Added endpoint for monitoring: {config.name} ({config.url})")

    def remove_endpoint(self, name: str):
        """
        Remove endpoint from monitoring.

        Args:
            name: Endpoint name
        """
        if name in self.endpoints:
            del self.endpoints[name]
            del self.history[name]
            logger.info(f"Removed endpoint from monitoring: {name}")

    def check_endpoint(self, name: str) -> HealthCheckResult:
        """
        Perform health check on a specific endpoint.

        Args:
            name: Endpoint name

        Returns:
            Health check result

        Raises:
            KeyError: If endpoint not found
        """
        if name not in self.endpoints:
            raise KeyError(f"Endpoint not found: {name}")

        config = self.endpoints[name]
        logger.debug(f"Checking health of endpoint: {name}")

        start_time = time.time()
        result = HealthCheckResult(
            endpoint=name,
            status=HealthStatus.UNKNOWN,
        )

        try:
            response = self.session.request(
                method=config.method,
                url=config.url,
                headers=config.headers,
                timeout=config.timeout_seconds,
                verify=config.verify_ssl,
            )

            response_time_ms = (time.time() - start_time) * 1000
            result.response_time_ms = response_time_ms
            result.status_code = response.status_code

            # Check status code
            if response.status_code != config.expected_status_code:
                result.status = HealthStatus.UNHEALTHY
                result.error_message = (
                    f"Unexpected status code: {response.status_code} "
                    f"(expected {config.expected_status_code})"
                )
                logger.warning(
                    f"Endpoint {name} returned unexpected status: "
                    f"{response.status_code}"
                )
            else:
                # Run custom validator if provided
                if config.validator:
                    try:
                        if config.validator(response):
                            result.status = HealthStatus.HEALTHY
                        else:
                            result.status = HealthStatus.DEGRADED
                            result.error_message = "Custom validator failed"
                            logger.warning(
                                f"Endpoint {name} failed custom validation"
                            )
                    except Exception as e:
                        result.status = HealthStatus.DEGRADED
                        result.error_message = f"Validator error: {str(e)}"
                        logger.error(
                            f"Validator error for endpoint {name}: {e}",
                            exc_info=True,
                        )
                else:
                    result.status = HealthStatus.HEALTHY

            logger.info(
                f"Endpoint {name}: {result.status.value} "
                f"({response_time_ms:.2f}ms)"
            )

        except requests.exceptions.Timeout:
            result.status = HealthStatus.UNHEALTHY
            result.error_message = f"Timeout after {config.timeout_seconds}s"
            logger.warning(f"Endpoint {name} timed out")

        except requests.exceptions.ConnectionError as e:
            result.status = HealthStatus.UNHEALTHY
            result.error_message = f"Connection error: {str(e)}"
            logger.error(f"Connection error for endpoint {name}: {e}")

        except requests.exceptions.RequestException as e:
            result.status = HealthStatus.UNHEALTHY
            result.error_message = f"Request error: {str(e)}"
            logger.error(f"Request error for endpoint {name}: {e}")

        except Exception as e:
            result.status = HealthStatus.UNKNOWN
            result.error_message = f"Unexpected error: {str(e)}"
            logger.error(
                f"Unexpected error checking endpoint {name}: {e}", exc_info=True
            )

        # Store result in history
        self._add_to_history(name, result)

        return result

    def check_all_endpoints(self) -> Dict[str, HealthCheckResult]:
        """
        Check health of all registered endpoints.

        Returns:
            Dictionary mapping endpoint names to health check results
        """
        logger.info(f"Checking health of {len(self.endpoints)} endpoints")

        results = {}
        for name in self.endpoints:
            results[name] = self.check_endpoint(name)

        healthy_count = sum(
            1 for r in results.values() if r.status == HealthStatus.HEALTHY
        )
        logger.info(
            f"Health check complete: {healthy_count}/{len(results)} endpoints healthy"
        )

        return results

    def _add_to_history(self, name: str, result: HealthCheckResult):
        """Add result to history, maintaining max size."""
        if name not in self.history:
            self.history[name] = []

        self.history[name].append(result)

        # Trim history if needed
        if len(self.history[name]) > self.max_history:
            self.history[name] = self.history[name][-self.max_history :]

    def get_history(
        self,
        name: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[HealthCheckResult]:
        """
        Get historical health check results for an endpoint.

        Args:
            name: Endpoint name
            since: Optional start time filter
            limit: Optional maximum number of results

        Returns:
            List of health check results
        """
        if name not in self.history:
            return []

        results = self.history[name]

        # Filter by time if specified
        if since:
            results = [r for r in results if r.timestamp >= since]

        # Apply limit if specified
        if limit:
            results = results[-limit:]

        return results

    def get_availability(
        self,
        name: str,
        window: timedelta = timedelta(hours=1),
    ) -> float:
        """
        Calculate availability percentage for an endpoint.

        Args:
            name: Endpoint name
            window: Time window to calculate over

        Returns:
            Availability percentage (0-100)
        """
        since = datetime.utcnow() - window
        results = self.get_history(name, since=since)

        if not results:
            return 0.0

        healthy_count = sum(
            1 for r in results if r.status == HealthStatus.HEALTHY
        )

        availability = (healthy_count / len(results)) * 100
        logger.debug(
            f"Endpoint {name} availability: {availability:.2f}% "
            f"over {len(results)} checks"
        )

        return availability

    def get_response_time_stats(
        self,
        name: str,
        window: timedelta = timedelta(hours=1),
    ) -> Dict[str, float]:
        """
        Calculate response time statistics for an endpoint.

        Args:
            name: Endpoint name
            window: Time window to calculate over

        Returns:
            Dictionary with min, max, mean, median, p95, p99 response times
        """
        since = datetime.utcnow() - window
        results = self.get_history(name, since=since)

        # Filter out results without response times
        response_times = [
            r.response_time_ms
            for r in results
            if r.response_time_ms is not None
        ]

        if not response_times:
            return {
                "min": 0.0,
                "max": 0.0,
                "mean": 0.0,
                "median": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "count": 0,
            }

        sorted_times = sorted(response_times)

        stats = {
            "min": min(response_times),
            "max": max(response_times),
            "mean": statistics.mean(response_times),
            "median": statistics.median(response_times),
            "p95": sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0.0,
            "p99": sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0.0,
            "count": len(response_times),
        }

        logger.debug(f"Endpoint {name} response time stats: {stats}")

        return stats

    def get_overall_status(self) -> HealthStatus:
        """
        Get overall health status across all endpoints.

        Returns:
            HEALTHY if all endpoints healthy,
            DEGRADED if some endpoints unhealthy,
            UNHEALTHY if all endpoints unhealthy,
            UNKNOWN if no endpoints configured
        """
        if not self.endpoints:
            return HealthStatus.UNKNOWN

        # Check most recent result for each endpoint
        statuses = []
        for name in self.endpoints:
            history = self.history.get(name, [])
            if history:
                statuses.append(history[-1].status)

        if not statuses:
            return HealthStatus.UNKNOWN

        healthy_count = statuses.count(HealthStatus.HEALTHY)

        if healthy_count == len(statuses):
            return HealthStatus.HEALTHY
        elif healthy_count == 0:
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all endpoint health statuses.

        Returns:
            Dictionary with overall status and per-endpoint details
        """
        overall_status = self.get_overall_status()

        endpoint_summaries = {}
        for name in self.endpoints:
            history = self.history.get(name, [])
            latest = history[-1] if history else None

            endpoint_summaries[name] = {
                "url": self.endpoints[name].url,
                "latest_status": latest.status.value if latest else "unknown",
                "latest_response_time_ms": latest.response_time_ms if latest else None,
                "latest_check": latest.timestamp.isoformat() if latest else None,
                "availability_1h": self.get_availability(name),
                "total_checks": len(history),
            }

        return {
            "overall_status": overall_status.value,
            "total_endpoints": len(self.endpoints),
            "endpoints": endpoint_summaries,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def close(self):
        """Close the session and cleanup resources."""
        self.session.close()
        logger.info("HealthChecker session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
