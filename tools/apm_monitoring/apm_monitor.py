#!/usr/bin/env python3
"""
APM Monitor - Main CLI Interface for APM & Monitoring Platform.

This module provides the command-line interface for all APM operations including
health checks, metrics collection, SLO monitoring, and query execution.

Supports:
- Health check monitoring
- Metrics collection and querying
- SLO tracking and reporting
- Alert management
- Dashboard generation
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import yaml

# Import APM components
from issue_35_alert_manager import AlertManager, AlertRule, AlertSeverity
from issue_35_grafana_dashboard import GrafanaDashboard
from issue_35_health_checker import HealthCheckConfig, HealthChecker
from issue_35_metrics_collector import MetricsCollector, get_default_collector
from issue_35_prometheus_wrapper import PrometheusWrapper
from issue_35_slo_tracker import SLODefinition, SLOTracker, SLOType, WindowType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class APMMonitor:
    """Main APM monitoring application."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize APM Monitor.

        Args:
            config_file: Path to configuration file
        """
        self.config = self._load_config(config_file)

        # Initialize components
        self.prometheus = PrometheusWrapper(
            base_url=self.config.get("prometheus", {}).get("url", "http://localhost:9090"),
            timeout=self.config.get("prometheus", {}).get("timeout", 30),
        )

        self.health_checker = HealthChecker(
            check_interval=self.config.get("health_check", {}).get("interval", 30),
        )

        self.alert_manager = AlertManager(
            prometheus_url=self.config.get("prometheus", {}).get("url", "http://localhost:9090"),
            alertmanager_url=self.config.get("alertmanager", {}).get("url", "http://localhost:9093"),
        )

        self.slo_tracker = SLOTracker()

        self.grafana = GrafanaDashboard(
            base_url=self.config.get("grafana", {}).get("url", "http://localhost:3000"),
            api_key=self.config.get("grafana", {}).get("api_key"),
            username=self.config.get("grafana", {}).get("username", "admin"),
            password=self.config.get("grafana", {}).get("password", "admin"),
        )

        self.metrics_collector = get_default_collector()

        logger.info("APM Monitor initialized")

    def _load_config(self, config_file: Optional[str]) -> dict:
        """Load configuration from file."""
        if not config_file:
            return {}

        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {config_file}")
                return config or {}
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_file}")
            return {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def check_health(self, endpoint: Optional[str] = None) -> int:
        """
        Run health checks.

        Args:
            endpoint: Optional specific endpoint to check

        Returns:
            Exit code (0 for success)
        """
        logger.info("Running health checks...")

        # Load endpoints from config
        endpoints_config = self.config.get("health_check", {}).get("endpoints", [])

        for ep_config in endpoints_config:
            config = HealthCheckConfig(
                url=ep_config["url"],
                name=ep_config["name"],
                interval_seconds=ep_config.get("interval", 30),
                timeout_seconds=ep_config.get("timeout", 10),
                expected_status_code=ep_config.get("expected_status", 200),
            )
            self.health_checker.add_endpoint(config)

        # Check specific endpoint or all
        if endpoint:
            result = self.health_checker.check_endpoint(endpoint)
            print(json.dumps(result.to_dict(), indent=2))
        else:
            results = self.health_checker.check_all_endpoints()
            summary = self.health_checker.get_summary()
            print(json.dumps(summary, indent=2))

        return 0

    def collect_metrics(self, output_file: Optional[str] = None) -> int:
        """
        Collect and export metrics.

        Args:
            output_file: Optional file to write metrics to

        Returns:
            Exit code (0 for success)
        """
        logger.info("Collecting metrics...")

        metrics_data = self.metrics_collector.export_metrics()

        if output_file:
            Path(output_file).write_bytes(metrics_data)
            logger.info(f"Metrics written to {output_file}")
        else:
            print(metrics_data.decode("utf-8"))

        # Print summary
        summary = self.metrics_collector.get_metrics_summary()
        print(f"\nMetrics Summary: {summary}")

        return 0

    def query_metrics(self, query: str, range_query: bool = False) -> int:
        """
        Query Prometheus metrics.

        Args:
            query: PromQL query string
            range_query: Whether to execute range query

        Returns:
            Exit code (0 for success)
        """
        logger.info(f"Querying metrics: {query}")

        try:
            if range_query:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(hours=1)
                result = self.prometheus.query_range(
                    query=query,
                    start=start_time,
                    end=end_time,
                    step="1m",
                )
            else:
                result = self.prometheus.query(query=query)

            print(json.dumps(result, indent=2))
            return 0

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return 1

    def check_slo(self, slo_name: Optional[str] = None, report: bool = False) -> int:
        """
        Check SLO compliance.

        Args:
            slo_name: Optional specific SLO to check
            report: Generate full report

        Returns:
            Exit code (0 for success)
        """
        logger.info("Checking SLOs...")

        # Load SLOs from config
        slos_config = self.config.get("slos", [])

        for slo_config in slos_config:
            slo = SLODefinition(
                name=slo_config["name"],
                slo_type=SLOType(slo_config["type"]),
                target=slo_config["target"],
                window_days=slo_config.get("window_days", 30),
                window_type=WindowType(slo_config.get("window_type", "rolling")),
                description=slo_config.get("description", ""),
                service=slo_config.get("service", ""),
                success_query=slo_config.get("success_query"),
                total_query=slo_config.get("total_query"),
                latency_threshold_ms=slo_config.get("latency_threshold_ms"),
            )
            self.slo_tracker.add_slo(slo)

        # Check specific SLO or generate report
        try:
            if slo_name:
                status = self.slo_tracker.calculate_slo(slo_name, self.prometheus)
                print(json.dumps(status.to_dict(), indent=2))
            elif report:
                report_data = self.slo_tracker.generate_report(self.prometheus)
                print(json.dumps(report_data, indent=2))
            else:
                statuses = self.slo_tracker.calculate_all_slos(self.prometheus)
                for name, status in statuses.items():
                    print(f"\n{name}:")
                    print(json.dumps(status.to_dict(), indent=2))

            return 0

        except Exception as e:
            logger.error(f"SLO check failed: {e}")
            return 1

    def manage_alerts(
        self,
        action: str,
        rules_file: Optional[str] = None,
        alert_name: Optional[str] = None,
    ) -> int:
        """
        Manage alerts.

        Args:
            action: Action to perform (load, list, evaluate)
            rules_file: Path to alert rules file
            alert_name: Specific alert to evaluate

        Returns:
            Exit code (0 for success)
        """
        logger.info(f"Managing alerts: {action}")

        try:
            if action == "load" and rules_file:
                self.alert_manager.load_rules_from_file(rules_file)
                print(f"Loaded {len(self.alert_manager.rules)} alert rules")

            elif action == "list":
                for name, rule in self.alert_manager.rules.items():
                    print(f"{name}: {rule.query} (severity={rule.severity.value})")

            elif action == "evaluate":
                if alert_name:
                    if alert_name in self.alert_manager.rules:
                        rule = self.alert_manager.rules[alert_name]
                        alert = self.alert_manager.evaluate_rule(rule, self.prometheus)
                        if alert:
                            print(f"FIRING: {json.dumps(alert.to_dict(), indent=2)}")
                        else:
                            print(f"OK: Alert {alert_name} not firing")
                    else:
                        print(f"Error: Alert rule not found: {alert_name}")
                        return 1
                else:
                    alerts = self.alert_manager.evaluate_all_rules(self.prometheus)
                    print(f"Found {len(alerts)} firing alerts:")
                    for alert in alerts:
                        print(json.dumps(alert.to_dict(), indent=2))

            elif action == "active":
                alerts = self.alert_manager.get_active_alerts()
                print(f"Active alerts: {len(alerts)}")
                for alert in alerts:
                    print(json.dumps(alert.to_dict(), indent=2))

            return 0

        except Exception as e:
            logger.error(f"Alert management failed: {e}")
            return 1

    def create_dashboard(
        self,
        service_name: str,
        output_file: Optional[str] = None,
    ) -> int:
        """
        Create Grafana dashboard.

        Args:
            service_name: Service name for dashboard
            output_file: Optional file to save dashboard JSON

        Returns:
            Exit code (0 for success)
        """
        logger.info(f"Creating dashboard for service: {service_name}")

        try:
            if output_file:
                # Generate dashboard JSON and save to file
                from issue_35_grafana_dashboard import PanelConfig

                panels = []
                # Add basic panels (simplified for export)
                panels.append(
                    PanelConfig(
                        title="Request Rate",
                        panel_type="graph",
                        targets=[
                            {
                                "expr": f'sum(rate(http_requests_total{{service="{service_name}"}}[5m]))',
                                "refId": "A",
                            }
                        ],
                    )
                )

                dashboard_json = {
                    "title": f"APM - {service_name}",
                    "panels": [p.to_json(i + 1) for i, p in enumerate(panels)],
                    "tags": ["apm", service_name],
                }

                with open(output_file, "w") as f:
                    json.dump(dashboard_json, f, indent=2)

                print(f"Dashboard JSON saved to {output_file}")
            else:
                # Create dashboard in Grafana
                result = self.grafana.generate_apm_dashboard(service_name)
                print(f"Dashboard created: {result.get('url')}")

            return 0

        except Exception as e:
            logger.error(f"Dashboard creation failed: {e}")
            return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="APM Monitor - Application Performance Monitoring Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config",
        "-c",
        help="Path to configuration file",
        default="issue_35_config.yaml",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Health check command
    health_parser = subparsers.add_parser("health-check", help="Run health checks")
    health_parser.add_argument("--endpoint", help="Specific endpoint to check")

    # Collect metrics command
    metrics_parser = subparsers.add_parser("collect-metrics", help="Collect metrics")
    metrics_parser.add_argument("--output", "-o", help="Output file for metrics")

    # Query metrics command
    query_parser = subparsers.add_parser("query-metrics", help="Query Prometheus")
    query_parser.add_argument("query", help="PromQL query string")
    query_parser.add_argument(
        "--range", action="store_true", help="Execute range query"
    )

    # SLO check command
    slo_parser = subparsers.add_parser("check-slo", help="Check SLO compliance")
    slo_parser.add_argument("--slo", help="Specific SLO to check")
    slo_parser.add_argument("--report", action="store_true", help="Generate full report")

    # Alert management command
    alert_parser = subparsers.add_parser("alerts", help="Manage alerts")
    alert_parser.add_argument(
        "action",
        choices=["load", "list", "evaluate", "active"],
        help="Alert action",
    )
    alert_parser.add_argument("--rules-file", help="Path to alert rules file")
    alert_parser.add_argument("--alert", help="Specific alert to evaluate")

    # Dashboard creation command
    dashboard_parser = subparsers.add_parser("create-dashboard", help="Create dashboard")
    dashboard_parser.add_argument("service", help="Service name")
    dashboard_parser.add_argument("--output", "-o", help="Save dashboard JSON to file")

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize APM Monitor
    try:
        monitor = APMMonitor(config_file=args.config)
    except Exception as e:
        logger.error(f"Failed to initialize APM Monitor: {e}")
        return 1

    # Execute command
    try:
        if args.command == "health-check":
            return monitor.check_health(endpoint=args.endpoint)

        elif args.command == "collect-metrics":
            return monitor.collect_metrics(output_file=args.output)

        elif args.command == "query-metrics":
            return monitor.query_metrics(query=args.query, range_query=args.range)

        elif args.command == "check-slo":
            return monitor.check_slo(slo_name=args.slo, report=args.report)

        elif args.command == "alerts":
            return monitor.manage_alerts(
                action=args.action,
                rules_file=args.rules_file,
                alert_name=args.alert,
            )

        elif args.command == "create-dashboard":
            return monitor.create_dashboard(
                service_name=args.service,
                output_file=args.output,
            )

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
