"""
Alert Manager Integration for APM & Monitoring Platform.

This module provides comprehensive alert management capabilities including
rule configuration, threshold monitoring, alert firing, and AlertManager
integration for routing and notification.

Supports:
- Alert rule management and evaluation
- Threshold monitoring with flexible conditions
- Alert state tracking (pending, firing, resolved)
- AlertManager API integration
- Alert silencing and inhibition
- Notification routing and grouping
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import requests
import yaml

logger = logging.getLogger(__name__)


class AlertState(Enum):
    """Alert state enumeration."""

    INACTIVE = "inactive"
    PENDING = "pending"
    FIRING = "firing"
    RESOLVED = "resolved"


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AlertRule:
    """Definition of an alert rule."""

    name: str
    query: str
    duration: str = "5m"
    severity: AlertSeverity = AlertSeverity.WARNING
    threshold: Optional[float] = None
    comparison: str = ">"  # >, <, >=, <=, ==, !=
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)

    def to_prometheus_rule(self) -> Dict[str, Any]:
        """Convert to Prometheus rule format."""
        rule = {
            "alert": self.name,
            "expr": self.query,
            "for": self.duration,
            "labels": {
                **self.labels,
                "severity": self.severity.value,
            },
            "annotations": self.annotations,
        }
        return rule


@dataclass
class Alert:
    """Active alert instance."""

    name: str
    state: AlertState
    value: Optional[float] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    active_at: Optional[datetime] = None
    fired_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "state": self.state.value,
            "value": self.value,
            "labels": self.labels,
            "annotations": self.annotations,
            "active_at": self.active_at.isoformat() if self.active_at else None,
            "fired_at": self.fired_at.isoformat() if self.fired_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class AlertManager:
    """
    Alert configuration and firing manager with AlertManager integration.

    Manages alert rules, evaluates conditions, tracks alert states, and
    integrates with Prometheus AlertManager for notification routing.
    """

    def __init__(
        self,
        prometheus_url: str = "http://localhost:9090",
        alertmanager_url: str = "http://localhost:9093",
        timeout: int = 30,
    ):
        """
        Initialize AlertManager.

        Args:
            prometheus_url: URL of Prometheus server
            alertmanager_url: URL of AlertManager server
            timeout: Request timeout in seconds
        """
        self.prometheus_url = prometheus_url.rstrip("/")
        self.alertmanager_url = alertmanager_url.rstrip("/")
        self.timeout = timeout

        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}

        self.session = requests.Session()

        logger.info(
            f"Initialized AlertManager with prometheus={prometheus_url}, "
            f"alertmanager={alertmanager_url}"
        )

    def add_rule(self, rule: AlertRule):
        """
        Add alert rule.

        Args:
            rule: Alert rule configuration
        """
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, name: str):
        """
        Remove alert rule.

        Args:
            name: Rule name
        """
        if name in self.rules:
            del self.rules[name]
            logger.info(f"Removed alert rule: {name}")

    def load_rules_from_file(self, filepath: str):
        """
        Load alert rules from YAML file.

        Args:
            filepath: Path to YAML file with alert rules
        """
        logger.info(f"Loading alert rules from {filepath}")

        with open(filepath, "r") as f:
            data = yaml.safe_load(f)

        groups = data.get("groups", [])

        for group in groups:
            rules = group.get("rules", [])

            for rule_data in rules:
                # Skip recording rules
                if "record" in rule_data:
                    continue

                # Parse alert rule
                rule = AlertRule(
                    name=rule_data["alert"],
                    query=rule_data["expr"],
                    duration=rule_data.get("for", "5m"),
                    labels=rule_data.get("labels", {}),
                    annotations=rule_data.get("annotations", {}),
                )

                # Set severity from labels
                severity_str = rule.labels.get("severity", "warning")
                try:
                    rule.severity = AlertSeverity(severity_str)
                except ValueError:
                    rule.severity = AlertSeverity.WARNING

                self.add_rule(rule)

        logger.info(f"Loaded {len(self.rules)} alert rules")

    def save_rules_to_file(self, filepath: str):
        """
        Save alert rules to Prometheus rule file format.

        Args:
            filepath: Output file path
        """
        logger.info(f"Saving alert rules to {filepath}")

        # Convert rules to Prometheus format
        rule_list = [rule.to_prometheus_rule() for rule in self.rules.values()]

        data = {
            "groups": [
                {
                    "name": "apm_alerts",
                    "rules": rule_list,
                }
            ]
        }

        with open(filepath, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        logger.info(f"Saved {len(rule_list)} alert rules")

    def evaluate_rule(
        self, rule: AlertRule, prometheus_client
    ) -> Optional[Alert]:
        """
        Evaluate alert rule against current metrics.

        Args:
            rule: Alert rule to evaluate
            prometheus_client: PrometheusWrapper instance

        Returns:
            Alert instance if rule is firing, None otherwise
        """
        logger.debug(f"Evaluating alert rule: {rule.name}")

        try:
            # Query Prometheus
            result = prometheus_client.query(rule.query)
            data = result.get("data", {})
            result_type = data.get("resultType")
            results = data.get("result", [])

            if not results:
                logger.debug(f"Rule {rule.name}: no results")
                return None

            # For vector results, check each series
            firing_alerts = []

            for series in results:
                metric = series.get("metric", {})
                value_pair = series.get("value", [])

                if len(value_pair) < 2:
                    continue

                timestamp, value_str = value_pair
                try:
                    value = float(value_str)
                except (ValueError, TypeError):
                    logger.warning(
                        f"Invalid value for rule {rule.name}: {value_str}"
                    )
                    continue

                # Evaluate threshold condition if specified
                if rule.threshold is not None:
                    should_fire = self._evaluate_condition(
                        value, rule.comparison, rule.threshold
                    )

                    if should_fire:
                        # Create alert with metric labels
                        alert = Alert(
                            name=rule.name,
                            state=AlertState.FIRING,
                            value=value,
                            labels={**rule.labels, **metric},
                            annotations=rule.annotations,
                            fired_at=datetime.utcnow(),
                        )
                        firing_alerts.append(alert)

                        logger.info(
                            f"Rule {rule.name} firing: {value} {rule.comparison} "
                            f"{rule.threshold}"
                        )

            # Return first firing alert (can be extended to return all)
            return firing_alerts[0] if firing_alerts else None

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.name}: {e}", exc_info=True)
            return None

    def _evaluate_condition(
        self, value: float, comparison: str, threshold: float
    ) -> bool:
        """Evaluate comparison condition."""
        if comparison == ">":
            return value > threshold
        elif comparison == "<":
            return value < threshold
        elif comparison == ">=":
            return value >= threshold
        elif comparison == "<=":
            return value <= threshold
        elif comparison == "==":
            return value == threshold
        elif comparison == "!=":
            return value != threshold
        else:
            logger.warning(f"Unknown comparison operator: {comparison}")
            return False

    def evaluate_all_rules(self, prometheus_client) -> List[Alert]:
        """
        Evaluate all alert rules.

        Args:
            prometheus_client: PrometheusWrapper instance

        Returns:
            List of firing alerts
        """
        logger.info(f"Evaluating {len(self.rules)} alert rules")

        firing_alerts = []

        for rule in self.rules.values():
            alert = self.evaluate_rule(rule, prometheus_client)
            if alert:
                firing_alerts.append(alert)
                # Track in active alerts
                alert_key = f"{alert.name}:{str(sorted(alert.labels.items()))}"
                self.active_alerts[alert_key] = alert

        logger.info(f"Found {len(firing_alerts)} firing alerts")

        return firing_alerts

    def fire_alert(self, alert: Alert) -> bool:
        """
        Fire alert by sending to AlertManager.

        Args:
            alert: Alert to fire

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Firing alert: {alert.name}")

        # Build AlertManager alert payload
        payload = [
            {
                "labels": {
                    "alertname": alert.name,
                    **alert.labels,
                },
                "annotations": alert.annotations,
                "startsAt": (alert.fired_at or datetime.utcnow()).isoformat(),
                "generatorURL": f"{self.prometheus_url}/alerts",
            }
        ]

        if alert.value is not None:
            payload[0]["annotations"]["value"] = str(alert.value)

        try:
            response = self.session.post(
                f"{self.alertmanager_url}/api/v2/alerts",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(f"Successfully fired alert: {alert.name}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fire alert {alert.name}: {e}")
            return False

    def resolve_alert(self, alert: Alert) -> bool:
        """
        Resolve alert by sending end time to AlertManager.

        Args:
            alert: Alert to resolve

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Resolving alert: {alert.name}")

        alert.state = AlertState.RESOLVED
        alert.resolved_at = datetime.utcnow()

        # Build AlertManager alert payload with end time
        payload = [
            {
                "labels": {
                    "alertname": alert.name,
                    **alert.labels,
                },
                "annotations": alert.annotations,
                "startsAt": (alert.fired_at or datetime.utcnow()).isoformat(),
                "endsAt": alert.resolved_at.isoformat(),
            }
        ]

        try:
            response = self.session.post(
                f"{self.alertmanager_url}/api/v2/alerts",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(f"Successfully resolved alert: {alert.name}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to resolve alert {alert.name}: {e}")
            return False

    def get_active_alerts(self) -> List[Alert]:
        """
        Get list of active alerts from AlertManager.

        Returns:
            List of active alerts
        """
        logger.debug("Fetching active alerts from AlertManager")

        try:
            response = self.session.get(
                f"{self.alertmanager_url}/api/v2/alerts",
                timeout=self.timeout,
            )
            response.raise_for_status()

            alerts_data = response.json()
            alerts = []

            for alert_data in alerts_data:
                alert = Alert(
                    name=alert_data["labels"].get("alertname", "unknown"),
                    state=AlertState.FIRING,
                    labels=alert_data.get("labels", {}),
                    annotations=alert_data.get("annotations", {}),
                )

                # Parse timestamps
                if "startsAt" in alert_data:
                    alert.fired_at = datetime.fromisoformat(
                        alert_data["startsAt"].replace("Z", "+00:00")
                    )

                alerts.append(alert)

            logger.info(f"Retrieved {len(alerts)} active alerts")
            return alerts

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []

    def create_silence(
        self,
        matchers: Dict[str, str],
        duration: timedelta,
        comment: str = "Created via APM",
        created_by: str = "apm-monitor",
    ) -> Optional[str]:
        """
        Create silence in AlertManager.

        Args:
            matchers: Label matchers to silence (e.g., {"alertname": "HighLatency"})
            duration: How long to silence alerts
            comment: Comment for the silence
            created_by: Creator identifier

        Returns:
            Silence ID if successful, None otherwise
        """
        logger.info(f"Creating silence for matchers: {matchers}")

        start_time = datetime.utcnow()
        end_time = start_time + duration

        # Build matchers in AlertManager format
        matcher_list = [
            {
                "name": name,
                "value": value,
                "isRegex": False,
                "isEqual": True,
            }
            for name, value in matchers.items()
        ]

        payload = {
            "matchers": matcher_list,
            "startsAt": start_time.isoformat() + "Z",
            "endsAt": end_time.isoformat() + "Z",
            "comment": comment,
            "createdBy": created_by,
        }

        try:
            response = self.session.post(
                f"{self.alertmanager_url}/api/v2/silences",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()
            silence_id = result.get("silenceID")

            logger.info(f"Created silence: {silence_id}")
            return silence_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create silence: {e}")
            return None

    def delete_silence(self, silence_id: str) -> bool:
        """
        Delete silence from AlertManager.

        Args:
            silence_id: Silence ID to delete

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Deleting silence: {silence_id}")

        try:
            response = self.session.delete(
                f"{self.alertmanager_url}/api/v2/silence/{silence_id}",
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(f"Successfully deleted silence: {silence_id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to delete silence {silence_id}: {e}")
            return False

    def close(self):
        """Close the session and cleanup resources."""
        self.session.close()
        logger.info("AlertManager session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
