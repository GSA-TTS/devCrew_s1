"""
Grafana Dashboard Generation for APM & Monitoring Platform.

This module provides comprehensive Grafana dashboard creation and management
capabilities, including dashboard JSON generation, panel configuration, data
source setup, and Grafana API integration.

Supports:
- Grafana API integration
- Dashboard JSON generation
- Panel configuration (graph, stat, table, etc.)
- Data source management
- Dashboard import/export
- Folder organization
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class GrafanaError(Exception):
    """Base exception for Grafana-related errors."""

    pass


@dataclass
class PanelConfig:
    """Configuration for a Grafana panel."""

    title: str
    panel_type: str  # graph, stat, table, heatmap, etc.
    targets: List[Dict[str, Any]]
    grid_pos: Dict[str, int] = field(
        default_factory=lambda: {"x": 0, "y": 0, "w": 12, "h": 8}
    )
    options: Dict[str, Any] = field(default_factory=dict)
    field_config: Dict[str, Any] = field(default_factory=dict)

    def to_json(self, panel_id: int) -> Dict[str, Any]:
        """Convert to Grafana panel JSON format."""
        panel = {
            "id": panel_id,
            "title": self.title,
            "type": self.panel_type,
            "targets": self.targets,
            "gridPos": self.grid_pos,
            "options": self.options,
            "fieldConfig": self.field_config,
        }
        return panel


class GrafanaDashboard:
    """
    Grafana dashboard generator and API integration.

    Provides methods for creating dashboards, configuring panels, managing
    data sources, and interacting with the Grafana HTTP API.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        api_key: Optional[str] = None,
        username: str = "admin",
        password: str = "admin",
        timeout: int = 30,
    ):
        """
        Initialize Grafana dashboard manager.

        Args:
            base_url: Base URL of Grafana server
            api_key: Optional API key for authentication
            username: Username for basic auth (if no API key)
            password: Password for basic auth (if no API key)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()

        # Setup authentication
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        else:
            self.session.auth = (username, password)

        logger.info(f"Initialized GrafanaDashboard with base_url={base_url}")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Grafana API.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            json_data: JSON request body
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            GrafanaError: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Some endpoints return empty responses
            if response.text:
                return response.json()
            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Grafana API request failed: {e}")
            raise GrafanaError(f"Request failed: {e}") from e

    def create_dashboard(
        self,
        title: str,
        panels: List[PanelConfig],
        uid: Optional[str] = None,
        folder_id: int = 0,
        tags: Optional[List[str]] = None,
        timezone: str = "utc",
        refresh: str = "30s",
    ) -> Dict[str, Any]:
        """
        Create Grafana dashboard.

        Args:
            title: Dashboard title
            panels: List of panel configurations
            uid: Optional unique identifier
            folder_id: Folder ID (0 for General)
            tags: Optional list of tags
            timezone: Dashboard timezone
            refresh: Auto-refresh interval

        Returns:
            Created dashboard response
        """
        logger.info(f"Creating dashboard: {title}")

        # Generate panel JSONs
        panel_list = []
        for i, panel_config in enumerate(panels):
            panel_json = panel_config.to_json(panel_id=i + 1)
            panel_list.append(panel_json)

        # Build dashboard JSON
        dashboard = {
            "dashboard": {
                "title": title,
                "panels": panel_list,
                "tags": tags or [],
                "timezone": timezone,
                "refresh": refresh,
                "schemaVersion": 27,
                "version": 0,
                "uid": uid,
            },
            "folderId": folder_id,
            "overwrite": True,
        }

        result = self._make_request("POST", "/api/dashboards/db", json_data=dashboard)

        logger.info(f"Dashboard created: {title} (uid={result.get('uid')})")
        return result

    def get_dashboard(self, uid: str) -> Dict[str, Any]:
        """
        Get dashboard by UID.

        Args:
            uid: Dashboard UID

        Returns:
            Dashboard JSON
        """
        logger.debug(f"Fetching dashboard: {uid}")

        result = self._make_request("GET", f"/api/dashboards/uid/{uid}")
        return result.get("dashboard", {})

    def delete_dashboard(self, uid: str) -> bool:
        """
        Delete dashboard by UID.

        Args:
            uid: Dashboard UID

        Returns:
            True if successful
        """
        logger.info(f"Deleting dashboard: {uid}")

        try:
            self._make_request("DELETE", f"/api/dashboards/uid/{uid}")
            return True
        except GrafanaError:
            return False

    def list_dashboards(self) -> List[Dict[str, Any]]:
        """
        List all dashboards.

        Returns:
            List of dashboard summaries
        """
        logger.debug("Listing dashboards")

        result = self._make_request("GET", "/api/search", params={"type": "dash-db"})
        return result if isinstance(result, list) else []

    def create_data_source(
        self,
        name: str,
        ds_type: str,
        url: str,
        access: str = "proxy",
        is_default: bool = False,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create data source.

        Args:
            name: Data source name
            ds_type: Type (prometheus, graphite, etc.)
            url: Data source URL
            access: Access mode (proxy or direct)
            is_default: Set as default data source
            json_data: Additional JSON configuration

        Returns:
            Created data source response
        """
        logger.info(f"Creating data source: {name} ({ds_type})")

        data_source = {
            "name": name,
            "type": ds_type,
            "url": url,
            "access": access,
            "isDefault": is_default,
            "jsonData": json_data or {},
        }

        result = self._make_request("POST", "/api/datasources", json_data=data_source)

        logger.info(f"Data source created: {name} (id={result.get('id')})")
        return result

    def get_data_sources(self) -> List[Dict[str, Any]]:
        """
        Get all data sources.

        Returns:
            List of data sources
        """
        logger.debug("Fetching data sources")

        result = self._make_request("GET", "/api/datasources")
        return result if isinstance(result, list) else []

    def create_folder(self, title: str) -> Dict[str, Any]:
        """
        Create dashboard folder.

        Args:
            title: Folder title

        Returns:
            Created folder response
        """
        logger.info(f"Creating folder: {title}")

        folder = {"title": title}

        result = self._make_request("POST", "/api/folders", json_data=folder)

        logger.info(f"Folder created: {title} (id={result.get('id')})")
        return result

    def generate_apm_dashboard(
        self,
        service_name: str,
        datasource: str = "Prometheus",
    ) -> Dict[str, Any]:
        """
        Generate comprehensive APM dashboard for a service.

        Args:
            service_name: Service name to monitor
            datasource: Data source name

        Returns:
            Generated dashboard JSON
        """
        logger.info(f"Generating APM dashboard for service: {service_name}")

        panels = []

        # Panel 1: Request Rate
        panels.append(
            PanelConfig(
                title="Request Rate",
                panel_type="graph",
                targets=[
                    {
                        "expr": f'sum(rate(http_requests_total{{service="{service_name}"}}[5m]))',
                        "legendFormat": "Total Requests/sec",
                        "refId": "A",
                    }
                ],
                grid_pos={"x": 0, "y": 0, "w": 12, "h": 8},
                options={"legend": {"displayMode": "list"}},
            )
        )

        # Panel 2: Error Rate
        panels.append(
            PanelConfig(
                title="Error Rate",
                panel_type="graph",
                targets=[
                    {
                        "expr": f'sum(rate(http_requests_total{{service="{service_name}",code=~"5.."}}[5m]))',
                        "legendFormat": "5xx Errors/sec",
                        "refId": "A",
                    }
                ],
                grid_pos={"x": 12, "y": 0, "w": 12, "h": 8},
                field_config={
                    "defaults": {"color": {"mode": "palette-classic"}}
                },
            )
        )

        # Panel 3: Response Time (p50, p95, p99)
        panels.append(
            PanelConfig(
                title="Response Time",
                panel_type="graph",
                targets=[
                    {
                        "expr": f'histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{{service="{service_name}"}}[5m])) by (le))',
                        "legendFormat": "p50",
                        "refId": "A",
                    },
                    {
                        "expr": f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{service="{service_name}"}}[5m])) by (le))',
                        "legendFormat": "p95",
                        "refId": "B",
                    },
                    {
                        "expr": f'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{{service="{service_name}"}}[5m])) by (le))',
                        "legendFormat": "p99",
                        "refId": "C",
                    },
                ],
                grid_pos={"x": 0, "y": 8, "w": 12, "h": 8},
            )
        )

        # Panel 4: Availability (SLO)
        panels.append(
            PanelConfig(
                title="Availability (SLO)",
                panel_type="stat",
                targets=[
                    {
                        "expr": f'(sum(rate(http_requests_total{{service="{service_name}",code!~"5.."}}[1h])) / sum(rate(http_requests_total{{service="{service_name}"}}[1h]))) * 100',
                        "refId": "A",
                    }
                ],
                grid_pos={"x": 12, "y": 8, "w": 6, "h": 4},
                options={
                    "reduceOptions": {"values": False, "calcs": ["lastNotNull"]},
                    "textMode": "value_and_name",
                },
                field_config={
                    "defaults": {
                        "unit": "percent",
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"value": 0, "color": "red"},
                                {"value": 99, "color": "yellow"},
                                {"value": 99.9, "color": "green"},
                            ],
                        },
                    }
                },
            )
        )

        # Panel 5: Active Alerts
        panels.append(
            PanelConfig(
                title="Active Alerts",
                panel_type="stat",
                targets=[
                    {
                        "expr": f'count(ALERTS{{service="{service_name}",alertstate="firing"}})',
                        "refId": "A",
                    }
                ],
                grid_pos={"x": 18, "y": 8, "w": 6, "h": 4},
                field_config={
                    "defaults": {
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"value": 0, "color": "green"},
                                {"value": 1, "color": "yellow"},
                                {"value": 3, "color": "red"},
                            ],
                        }
                    }
                },
            )
        )

        # Panel 6: CPU Usage
        panels.append(
            PanelConfig(
                title="CPU Usage",
                panel_type="graph",
                targets=[
                    {
                        "expr": f'rate(process_cpu_seconds_total{{service="{service_name}"}}[5m]) * 100',
                        "legendFormat": "CPU %",
                        "refId": "A",
                    }
                ],
                grid_pos={"x": 0, "y": 16, "w": 12, "h": 8},
            )
        )

        # Panel 7: Memory Usage
        panels.append(
            PanelConfig(
                title="Memory Usage",
                panel_type="graph",
                targets=[
                    {
                        "expr": f'process_resident_memory_bytes{{service="{service_name}"}}',
                        "legendFormat": "Memory",
                        "refId": "A",
                    }
                ],
                grid_pos={"x": 12, "y": 16, "w": 12, "h": 8},
                field_config={"defaults": {"unit": "bytes"}},
            )
        )

        # Create dashboard
        dashboard_title = f"APM - {service_name}"
        dashboard_uid = f"apm-{service_name.lower().replace(' ', '-')}"

        return self.create_dashboard(
            title=dashboard_title,
            panels=panels,
            uid=dashboard_uid,
            tags=["apm", "monitoring", service_name],
        )

    def export_dashboard(self, uid: str, filepath: str):
        """
        Export dashboard to JSON file.

        Args:
            uid: Dashboard UID
            filepath: Output file path
        """
        logger.info(f"Exporting dashboard {uid} to {filepath}")

        dashboard = self.get_dashboard(uid)

        with open(filepath, "w") as f:
            json.dump(dashboard, f, indent=2)

        logger.info(f"Dashboard exported to {filepath}")

    def import_dashboard(self, filepath: str, folder_id: int = 0) -> Dict[str, Any]:
        """
        Import dashboard from JSON file.

        Args:
            filepath: Input file path
            folder_id: Target folder ID

        Returns:
            Import response
        """
        logger.info(f"Importing dashboard from {filepath}")

        with open(filepath, "r") as f:
            dashboard_json = json.load(f)

        # Wrap in API format if needed
        if "dashboard" not in dashboard_json:
            dashboard_json = {
                "dashboard": dashboard_json,
                "folderId": folder_id,
                "overwrite": True,
            }

        result = self._make_request("POST", "/api/dashboards/db", json_data=dashboard_json)

        logger.info(f"Dashboard imported: {result.get('uid')}")
        return result

    def close(self):
        """Close the session and cleanup resources."""
        self.session.close()
        logger.info("GrafanaDashboard session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
