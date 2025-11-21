"""Drift detection for live vs desired configuration state."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from deepdiff import DeepDiff


class DriftSeverity(Enum):
    """Severity levels for drift detection."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class DriftItem:
    """A single drift item."""

    path: str
    drift_type: str
    expected: Any
    actual: Any
    severity: DriftSeverity = DriftSeverity.WARNING
    message: str = ""


@dataclass
class DriftReport:
    """Report of configuration drift."""

    config_name: str
    timestamp: datetime
    has_drift: bool
    drift_items: List[DriftItem] = field(default_factory=list)
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def critical_count(self) -> int:
        """Count of critical drift items."""
        return sum(
            1 for item in self.drift_items if item.severity == DriftSeverity.CRITICAL
        )

    @property
    def warning_count(self) -> int:
        """Count of warning drift items."""
        return sum(
            1 for item in self.drift_items if item.severity == DriftSeverity.WARNING
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "config_name": self.config_name,
            "timestamp": self.timestamp.isoformat(),
            "has_drift": self.has_drift,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "drift_items": [
                {
                    "path": item.path,
                    "drift_type": item.drift_type,
                    "expected": item.expected,
                    "actual": item.actual,
                    "severity": item.severity.value,
                    "message": item.message,
                }
                for item in self.drift_items
            ],
            "summary": self.summary,
            "metadata": self.metadata,
        }


class DriftDetector:
    """Detector for configuration drift between desired and live state."""

    def __init__(self) -> None:
        """Initialize the drift detector."""
        self._severity_rules: Dict[str, DriftSeverity] = {}
        self._ignore_paths: List[str] = []
        self._live_state_fetchers: Dict[str, Callable[[], Dict[str, Any]]] = {}

    def set_severity_rule(self, path_pattern: str, severity: DriftSeverity) -> None:
        """Set severity level for a path pattern.

        Args:
            path_pattern: Path pattern to match.
            severity: Severity level for matching paths.
        """
        self._severity_rules[path_pattern] = severity

    def add_ignore_path(self, path: str) -> None:
        """Add a path to ignore in drift detection.

        Args:
            path: Path to ignore.
        """
        self._ignore_paths.append(path)

    def register_live_state_fetcher(
        self,
        config_name: str,
        fetcher: Callable[[], Dict[str, Any]],
    ) -> None:
        """Register a function to fetch live state for a configuration.

        Args:
            config_name: Name of the configuration.
            fetcher: Function that returns the live state.
        """
        self._live_state_fetchers[config_name] = fetcher

    def _get_severity(self, path: str) -> DriftSeverity:
        """Get severity for a path based on rules.

        Args:
            path: Path to check.

        Returns:
            Matching severity or WARNING as default.
        """
        for pattern, severity in self._severity_rules.items():
            if pattern in path:
                return severity
        return DriftSeverity.WARNING

    def _should_ignore(self, path: str) -> bool:
        """Check if a path should be ignored.

        Args:
            path: Path to check.

        Returns:
            True if path should be ignored.
        """
        for ignore_path in self._ignore_paths:
            if ignore_path in path:
                return True
        return False

    def compare(
        self,
        desired: Dict[str, Any],
        live: Dict[str, Any],
        config_name: str = "config",
    ) -> DriftReport:
        """Compare desired and live configurations.

        Args:
            desired: Desired configuration state.
            live: Live configuration state.
            config_name: Name of the configuration.

        Returns:
            DriftReport with comparison results.
        """
        diff = DeepDiff(desired, live, ignore_order=True)
        drift_items: List[DriftItem] = []

        if "dictionary_item_added" in diff:
            added_items = diff["dictionary_item_added"]
            for path in added_items:
                path_str = str(path)
                if self._should_ignore(path_str):
                    continue
                # DeepDiff stores added items as a set, get value from live config
                actual_value = live
                for key in path_str.replace("root", "").strip("[]'\"").split("']['"):
                    if key and isinstance(actual_value, dict):
                        actual_value = actual_value.get(key)
                drift_items.append(
                    DriftItem(
                        path=path_str,
                        drift_type="added",
                        expected=None,
                        actual=actual_value,
                        severity=self._get_severity(path_str),
                        message=f"Unexpected item in live state: {path_str}",
                    )
                )

        if "dictionary_item_removed" in diff:
            removed_items = diff["dictionary_item_removed"]
            for path in removed_items:
                path_str = str(path)
                if self._should_ignore(path_str):
                    continue
                # DeepDiff stores removed items as a set, get value from desired config
                expected_value = desired
                for key in path_str.replace("root", "").strip("[]'\"").split("']['"):
                    if key and isinstance(expected_value, dict):
                        expected_value = expected_value.get(key)
                drift_items.append(
                    DriftItem(
                        path=path_str,
                        drift_type="removed",
                        expected=expected_value,
                        actual=None,
                        severity=self._get_severity(path_str),
                        message=f"Missing item in live state: {path_str}",
                    )
                )

        if "values_changed" in diff:
            for path, change in diff["values_changed"].items():
                path_str = str(path)
                if self._should_ignore(path_str):
                    continue
                drift_items.append(
                    DriftItem(
                        path=path_str,
                        drift_type="changed",
                        expected=change["new_value"],
                        actual=change["old_value"],
                        severity=self._get_severity(path_str),
                        message=f"Value changed: {path_str}",
                    )
                )

        if "type_changes" in diff:
            for path, change in diff["type_changes"].items():
                path_str = str(path)
                if self._should_ignore(path_str):
                    continue
                drift_items.append(
                    DriftItem(
                        path=path_str,
                        drift_type="type_changed",
                        expected=change["new_value"],
                        actual=change["old_value"],
                        severity=DriftSeverity.CRITICAL,
                        message=f"Type changed: {path_str}",
                    )
                )

        has_drift = len(drift_items) > 0
        summary = f"Found {len(drift_items)} drift items" if has_drift else "No drift"

        return DriftReport(
            config_name=config_name,
            timestamp=datetime.now(),
            has_drift=has_drift,
            drift_items=drift_items,
            summary=summary,
        )

    def detect(
        self,
        config_name: str,
        desired: Dict[str, Any],
    ) -> DriftReport:
        """Detect drift using registered live state fetcher.

        Args:
            config_name: Name of the configuration.
            desired: Desired configuration state.

        Returns:
            DriftReport with detection results.

        Raises:
            KeyError: If no fetcher is registered for the config.
        """
        if config_name not in self._live_state_fetchers:
            raise KeyError(f"No live state fetcher registered for: {config_name}")

        live = self._live_state_fetchers[config_name]()
        return self.compare(desired, live, config_name)

    def generate_reconciliation_plan(
        self,
        report: DriftReport,
    ) -> List[Dict[str, Any]]:
        """Generate a plan to reconcile drift.

        Args:
            report: DriftReport to reconcile.

        Returns:
            List of reconciliation actions.
        """
        actions: List[Dict[str, Any]] = []

        for item in report.drift_items:
            if item.drift_type == "added":
                actions.append(
                    {
                        "action": "remove",
                        "path": item.path,
                        "current_value": item.actual,
                        "reason": "Item exists in live but not in desired state",
                    }
                )
            elif item.drift_type == "removed":
                actions.append(
                    {
                        "action": "add",
                        "path": item.path,
                        "value": item.expected,
                        "reason": "Item missing in live state",
                    }
                )
            elif item.drift_type in ("changed", "type_changed"):
                actions.append(
                    {
                        "action": "update",
                        "path": item.path,
                        "from_value": item.actual,
                        "to_value": item.expected,
                        "reason": "Value differs from desired state",
                    }
                )

        return actions
