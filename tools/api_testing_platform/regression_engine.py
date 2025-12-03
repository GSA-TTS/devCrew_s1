"""
RegressionEngine for API Testing Platform

Provides baseline capture, response diff detection, performance regression
tracking, breaking change identification, and historical trend analysis for
API testing.
"""

import json
import logging
import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from deepdiff import DeepDiff

logger = logging.getLogger(__name__)


@dataclass
class StructureChange:
    """Represents a structural change in API response."""

    change_type: str  # added, removed, type_changed
    path: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    severity: str = "medium"  # critical, high, medium, low


@dataclass
class DataChange:
    """Represents a data value change in API response."""

    path: str
    old_value: Any
    new_value: Any
    change_type: str  # value_changed, iterable_item_added, removed


@dataclass
class PerformanceChange:
    """Represents performance metrics and changes."""

    current_latency_ms: float
    baseline_latency_ms: float
    change_percent: float
    threshold_exceeded: bool
    p50_current: Optional[float] = None
    p50_baseline: Optional[float] = None
    p95_current: Optional[float] = None
    p95_baseline: Optional[float] = None


@dataclass
class BreakingChange:
    """Represents a breaking API change."""

    change_type: str  # removed_field, type_change, status_change, etc.
    description: str
    path: str
    impact: str  # critical, high, medium
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None


@dataclass
class DiffReport:
    """Complete diff report for API response comparison."""

    endpoint: str
    method: str
    has_changes: bool
    structure_changes: List[StructureChange] = field(default_factory=list)
    data_changes: List[DataChange] = field(default_factory=list)
    performance_changes: Optional[PerformanceChange] = None
    breaking_changes: List[BreakingChange] = field(default_factory=list)
    severity: str = "low"  # critical, high, medium, low
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def has_breaking_changes(self) -> bool:
        """Check if report contains breaking changes."""
        return len(self.breaking_changes) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


@dataclass
class BaselineData:
    """Baseline data structure for API endpoint."""

    endpoint: str
    method: str
    timestamp: str
    response: Dict[str, Any]
    performance: Dict[str, float]
    version: str = "1.0"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaselineData":
        """Create BaselineData from dictionary."""
        return cls(
            endpoint=data["endpoint"],
            method=data["method"],
            timestamp=data["timestamp"],
            response=data["response"],
            performance=data["performance"],
            version=data.get("version", "1.0"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class RegressionEngineError(Exception):
    """Base exception for RegressionEngine errors."""

    pass


class BaselineNotFoundError(RegressionEngineError):
    """Raised when baseline file is not found."""

    pass


class CorruptedBaselineError(RegressionEngineError):
    """Raised when baseline data is corrupted."""

    pass


class InvalidDiffError(RegressionEngineError):
    """Raised when diff comparison is invalid."""

    pass


class RegressionEngine:
    """
    API Regression Testing Engine.

    Manages baseline capture, response comparison, performance tracking,
    and breaking change detection for API testing.
    """

    def __init__(
        self,
        baseline_dir: str = ".baselines/",
        ignore_fields: Optional[List[str]] = None,
        performance_threshold: float = 0.20,
        approval_required: bool = True,
        retention_days: int = 90,
    ):
        """
        Initialize RegressionEngine.

        Args:
            baseline_dir: Directory to store baseline files
            ignore_fields: Fields to ignore in diff comparison
            performance_threshold: Performance degradation threshold
                (0.20 = 20%)
            approval_required: Whether baseline updates require approval
            retention_days: Days to retain historical data
        """
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

        self.ignore_fields = ignore_fields or ["timestamp", "request_id"]
        self.performance_threshold = performance_threshold
        self.approval_required = approval_required
        self.retention_days = retention_days

        # History tracking
        self.history_dir = self.baseline_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

        logger.info("RegressionEngine initialized with " f"baseline_dir={baseline_dir}")

    def _get_baseline_path(self, endpoint: str, method: str = "GET") -> Path:
        """
        Get baseline file path for endpoint.

        Args:
            endpoint: API endpoint path
            method: HTTP method

        Returns:
            Path to baseline file
        """
        # Sanitize endpoint for filename
        safe_endpoint = endpoint.replace("/", "_").replace(":", "_")
        filename = f"{method.lower()}_{safe_endpoint}.json"
        return self.baseline_dir / filename

    def _get_history_path(self, endpoint: str, method: str = "GET") -> Path:
        """
        Get history file path for endpoint.

        Args:
            endpoint: API endpoint path
            method: HTTP method

        Returns:
            Path to history file
        """
        safe_endpoint = endpoint.replace("/", "_").replace(":", "_")
        filename = f"{method.lower()}_{safe_endpoint}_history.jsonl"
        return self.history_dir / filename

    def capture_baseline(
        self,
        endpoint: str,
        response: Dict[str, Any],
        method: str = "GET",
        latency_ms: Optional[float] = None,
        percentiles: Optional[Dict[str, float]] = None,
    ) -> BaselineData:
        """
        Capture baseline API response.

        Args:
            endpoint: API endpoint path
            response: Response data with status_code, headers, body
            method: HTTP method
            latency_ms: Response latency in milliseconds
            percentiles: Performance percentiles (p50, p95, p99)

        Returns:
            BaselineData object

        Raises:
            RegressionEngineError: If capture fails
        """
        try:
            performance = {
                "latency_ms": latency_ms or 0.0,
                "p50": percentiles.get("p50", 0.0) if percentiles else 0.0,
                "p95": percentiles.get("p95", 0.0) if percentiles else 0.0,
                "p99": percentiles.get("p99", 0.0) if percentiles else 0.0,
            }

            baseline = BaselineData(
                endpoint=endpoint,
                method=method,
                timestamp=datetime.utcnow().isoformat(),
                response=response,
                performance=performance,
            )

            # Save baseline
            baseline_path = self._get_baseline_path(endpoint, method)
            with open(baseline_path, "w") as f:
                json.dump(baseline.to_dict(), f, indent=2)

            # Save to history
            self._append_history(endpoint, method, response, latency_ms)

            logger.info(
                f"Baseline captured for {method} {endpoint} at " f"{baseline_path}"
            )
            return baseline

        except Exception as e:
            logger.error(f"Failed to capture baseline: {e}")
            raise RegressionEngineError(f"Baseline capture failed: {e}") from e

    def _append_history(
        self,
        endpoint: str,
        method: str,
        response: Dict[str, Any],
        latency_ms: Optional[float],
    ) -> None:
        """
        Append response data to history file.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            response: Response data
            latency_ms: Response latency
        """
        history_path = self._get_history_path(endpoint, method)

        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "status_code": response.get("status_code"),
            "latency_ms": latency_ms,
            "body_hash": hash(json.dumps(response.get("body", {}), sort_keys=True)),
        }

        try:
            with open(history_path, "a") as f:
                f.write(json.dumps(history_entry) + "\n")
        except Exception as e:
            logger.warning("Failed to append history: %s", e)

    def load_baseline(self, endpoint: str, method: str = "GET") -> BaselineData:
        """
        Load baseline data for endpoint.

        Args:
            endpoint: API endpoint path
            method: HTTP method

        Returns:
            BaselineData object

        Raises:
            BaselineNotFoundError: If baseline doesn't exist
            CorruptedBaselineError: If baseline data is invalid
        """
        baseline_path = self._get_baseline_path(endpoint, method)

        if not baseline_path.exists():
            raise BaselineNotFoundError(f"No baseline found for {method} {endpoint}")

        try:
            with open(baseline_path, "r") as f:
                data = json.load(f)
            return BaselineData.from_dict(data)
        except json.JSONDecodeError as e:
            raise CorruptedBaselineError(
                f"Baseline file corrupted for {method} {endpoint}"
            ) from e
        except Exception as e:
            raise RegressionEngineError(f"Failed to load baseline: {e}") from e

    def compare_with_baseline(
        self,
        endpoint: str,
        response: Dict[str, Any],
        method: str = "GET",
        latency_ms: Optional[float] = None,
    ) -> DiffReport:
        """
        Compare current response with baseline.

        Args:
            endpoint: API endpoint path
            response: Current response data
            method: HTTP method
            latency_ms: Current response latency

        Returns:
            DiffReport with all detected changes

        Raises:
            BaselineNotFoundError: If no baseline exists
        """
        baseline = self.load_baseline(endpoint, method)

        # Detect structure changes
        structure_changes = self._detect_structure_changes(baseline.response, response)

        # Detect data changes
        data_changes = self._detect_data_changes(baseline.response, response)

        # Detect performance changes
        performance_changes = None
        if latency_ms is not None:
            performance_changes = self._detect_performance_changes(
                baseline.performance["latency_ms"], latency_ms
            )

        # Detect breaking changes
        breaking_changes = self.detect_breaking_changes(baseline.response, response)

        # Determine severity
        severity = self._calculate_severity(
            structure_changes,
            data_changes,
            breaking_changes,
            performance_changes,
        )

        has_changes = bool(
            structure_changes
            or data_changes
            or breaking_changes
            or (performance_changes and performance_changes.threshold_exceeded)
        )

        report = DiffReport(
            endpoint=endpoint,
            method=method,
            has_changes=has_changes,
            structure_changes=structure_changes,
            data_changes=data_changes,
            performance_changes=performance_changes,
            breaking_changes=breaking_changes,
            severity=severity,
        )

        logger.info(
            f"Comparison complete for {method} {endpoint}: "
            f"{len(breaking_changes)} breaking changes, "
            f"severity={severity}"
        )

        return report

    def _detect_structure_changes(
        self, baseline: Dict[str, Any], current: Dict[str, Any]
    ) -> List[StructureChange]:
        """
        Detect structural changes between responses.

        Args:
            baseline: Baseline response
            current: Current response

        Returns:
            List of StructureChange objects
        """
        changes = []

        baseline_body = baseline.get("body", {})
        current_body = current.get("body", {})

        # Use DeepDiff to find structural differences
        diff = DeepDiff(
            baseline_body,
            current_body,
            ignore_order=True,
            exclude_paths=[f"root['{field}']" for field in self.ignore_fields],
        )

        # Handle type changes
        if "type_changes" in diff:
            for path, change in diff["type_changes"].items():
                changes.append(
                    StructureChange(
                        change_type="type_changed",
                        path=path,
                        old_value=str(change["old_type"]),
                        new_value=str(change["new_type"]),
                        severity="high",
                    )
                )

        # Handle added fields
        if "dictionary_item_added" in diff:
            for path in diff["dictionary_item_added"]:
                changes.append(
                    StructureChange(
                        change_type="added",
                        path=str(path),
                        new_value="<field_added>",
                        severity="low",
                    )
                )

        # Handle removed fields
        if "dictionary_item_removed" in diff:
            for path in diff["dictionary_item_removed"]:
                changes.append(
                    StructureChange(
                        change_type="removed",
                        path=str(path),
                        old_value="<field_removed>",
                        severity="high",
                    )
                )

        return changes

    def _detect_data_changes(
        self, baseline: Dict[str, Any], current: Dict[str, Any]
    ) -> List[DataChange]:
        """
        Detect data value changes between responses.

        Args:
            baseline: Baseline response
            current: Current response

        Returns:
            List of DataChange objects
        """
        changes = []

        baseline_body = baseline.get("body", {})
        current_body = current.get("body", {})

        diff = DeepDiff(
            baseline_body,
            current_body,
            ignore_order=True,
            exclude_paths=[f"root['{field}']" for field in self.ignore_fields],
        )

        # Handle value changes
        if "values_changed" in diff:
            for path, change in diff["values_changed"].items():
                changes.append(
                    DataChange(
                        path=str(path),
                        old_value=change["old_value"],
                        new_value=change["new_value"],
                        change_type="value_changed",
                    )
                )

        # Handle iterable item additions
        if "iterable_item_added" in diff:
            for path, value in diff["iterable_item_added"].items():
                changes.append(
                    DataChange(
                        path=str(path),
                        old_value=None,
                        new_value=value,
                        change_type="iterable_item_added",
                    )
                )

        # Handle iterable item removals
        if "iterable_item_removed" in diff:
            for path, value in diff["iterable_item_removed"].items():
                changes.append(
                    DataChange(
                        path=str(path),
                        old_value=value,
                        new_value=None,
                        change_type="iterable_item_removed",
                    )
                )

        return changes

    def _detect_performance_changes(
        self, baseline_latency: float, current_latency: float
    ) -> PerformanceChange:
        """
        Detect performance regression.

        Args:
            baseline_latency: Baseline latency in ms
            current_latency: Current latency in ms

        Returns:
            PerformanceChange object
        """
        if baseline_latency == 0:
            change_percent = 0.0
        else:
            change_percent = (current_latency - baseline_latency) / baseline_latency

        threshold_exceeded = change_percent > self.performance_threshold

        return PerformanceChange(
            current_latency_ms=current_latency,
            baseline_latency_ms=baseline_latency,
            change_percent=change_percent,
            threshold_exceeded=threshold_exceeded,
        )

    def detect_breaking_changes(
        self, old_response: Dict[str, Any], new_response: Dict[str, Any]
    ) -> List[BreakingChange]:
        """
        Detect breaking changes between API responses.

        Args:
            old_response: Previous response
            new_response: New response

        Returns:
            List of BreakingChange objects
        """
        breaking_changes = []

        # Check status code changes
        old_status = old_response.get("status_code")
        new_status = new_response.get("status_code")

        if old_status != new_status:
            if new_status in [400, 401, 403, 404, 500, 502, 503]:
                breaking_changes.append(
                    BreakingChange(
                        change_type="status_change",
                        description=(
                            f"Status code changed from {old_status} " f"to {new_status}"
                        ),
                        path="status_code",
                        impact="critical",
                        old_value=old_status,
                        new_value=new_status,
                    )
                )

        old_body = old_response.get("body", {})
        new_body = new_response.get("body", {})

        # Check for removed fields
        removed_fields = self._find_removed_fields(old_body, new_body)
        for field_path in removed_fields:
            breaking_changes.append(
                BreakingChange(
                    change_type="removed_field",
                    description=f"Field removed: {field_path}",
                    path=field_path,
                    impact="high",
                    old_value="<exists>",
                    new_value=None,
                )
            )

        # Check for type changes
        type_changes = self._find_type_changes(old_body, new_body)
        for field_path, (old_type, new_type) in type_changes.items():
            breaking_changes.append(
                BreakingChange(
                    change_type="type_change",
                    description=(
                        f"Field type changed from {old_type} " f"to {new_type}"
                    ),
                    path=field_path,
                    impact="critical",
                    old_value=old_type,
                    new_value=new_type,
                )
            )

        # Check authentication changes
        old_auth = old_response.get("headers", {}).get("www-authenticate")
        new_auth = new_response.get("headers", {}).get("www-authenticate")

        if old_auth != new_auth and new_auth:
            breaking_changes.append(
                BreakingChange(
                    change_type="auth_change",
                    description="Authentication requirements changed",
                    path="headers.www-authenticate",
                    impact="critical",
                    old_value=old_auth,
                    new_value=new_auth,
                )
            )

        return breaking_changes

    def _find_removed_fields(
        self,
        old_dict: Dict[str, Any],
        new_dict: Dict[str, Any],
        prefix: str = "",
    ) -> List[str]:
        """
        Recursively find removed fields.

        Args:
            old_dict: Old dictionary
            new_dict: New dictionary
            prefix: Path prefix for nested fields

        Returns:
            List of removed field paths
        """
        removed = []

        for key, value in old_dict.items():
            if key in self.ignore_fields:
                continue

            current_path = f"{prefix}.{key}" if prefix else key

            if key not in new_dict:
                removed.append(current_path)
            elif isinstance(value, dict) and isinstance(new_dict[key], dict):
                removed.extend(
                    self._find_removed_fields(value, new_dict[key], current_path)
                )

        return removed

    def _find_type_changes(
        self,
        old_dict: Dict[str, Any],
        new_dict: Dict[str, Any],
        prefix: str = "",
    ) -> Dict[str, tuple]:
        """
        Recursively find type changes.

        Args:
            old_dict: Old dictionary
            new_dict: New dictionary
            prefix: Path prefix for nested fields

        Returns:
            Dictionary of field paths to (old_type, new_type) tuples
        """
        changes = {}

        for key in set(old_dict.keys()) & set(new_dict.keys()):
            if key in self.ignore_fields:
                continue

            current_path = f"{prefix}.{key}" if prefix else key
            old_value = old_dict[key]
            new_value = new_dict[key]

            old_type = type(old_value).__name__
            new_type = type(new_value).__name__

            if old_type != new_type:
                changes[current_path] = (old_type, new_type)
            elif isinstance(old_value, dict) and isinstance(new_value, dict):
                changes.update(
                    self._find_type_changes(old_value, new_value, current_path)
                )

        return changes

    def _calculate_severity(
        self,
        structure_changes: List[StructureChange],
        data_changes: List[DataChange],
        breaking_changes: List[BreakingChange],
        performance_changes: Optional[PerformanceChange],
    ) -> str:
        """
        Calculate overall severity of changes.

        Args:
            structure_changes: List of structure changes
            data_changes: List of data changes
            breaking_changes: List of breaking changes
            performance_changes: Performance change data

        Returns:
            Severity level: critical, high, medium, low
        """
        if breaking_changes:
            # Check for critical breaking changes
            if any(bc.impact == "critical" for bc in breaking_changes):
                return "critical"
            return "high"

        if structure_changes:
            # Check for high severity structure changes
            if any(sc.severity == "high" for sc in structure_changes):
                return "high"

        if performance_changes and performance_changes.threshold_exceeded:
            if performance_changes.change_percent > 0.5:  # 50% degradation
                return "high"
            return "medium"

        if data_changes or structure_changes:
            return "medium"

        return "low"

    def track_performance(
        self, endpoint: str, latency: float, method: str = "GET"
    ) -> None:
        """
        Track performance metrics for endpoint.

        Args:
            endpoint: API endpoint path
            latency: Response latency in milliseconds
            method: HTTP method
        """
        history_path = self._get_history_path(endpoint, method)

        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": latency,
        }

        try:
            with open(history_path, "a") as f:
                f.write(json.dumps(history_entry) + "\n")

            logger.debug(f"Performance tracked for {method} {endpoint}: {latency}ms")
        except Exception as e:
            logger.error(f"Failed to track performance: {e}")

    def get_trend_analysis(
        self, endpoint: str, days: int = 7, method: str = "GET"
    ) -> Dict[str, Any]:
        """
        Get historical trend analysis for endpoint.

        Args:
            endpoint: API endpoint path
            days: Number of days to analyze
            method: HTTP method

        Returns:
            Dictionary with trend analysis data
        """
        history_path = self._get_history_path(endpoint, method)

        if not history_path.exists():
            return {
                "endpoint": endpoint,
                "method": method,
                "days": days,
                "error": "No history data available",
            }

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        latencies = []
        timestamps = []
        error_count = 0

        try:
            with open(history_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry["timestamp"])

                        if entry_time >= cutoff_date:
                            timestamps.append(entry["timestamp"])
                            if "latency_ms" in entry:
                                latencies.append(entry["latency_ms"])
                            if entry.get("status_code", 200) >= 400:
                                error_count += 1
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue

            if not latencies:
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "days": days,
                    "data_points": 0,
                    "error": "No latency data in time range",
                }

            # Calculate statistics
            analysis = {
                "endpoint": endpoint,
                "method": method,
                "days": days,
                "data_points": len(latencies),
                "latency": {
                    "min": min(latencies),
                    "max": max(latencies),
                    "mean": statistics.mean(latencies),
                    "median": statistics.median(latencies),
                    "stdev": (
                        statistics.stdev(latencies) if len(latencies) > 1 else 0.0
                    ),
                },
                "error_count": error_count,
                "error_rate": (error_count / len(timestamps) if timestamps else 0.0),
                "time_range": {
                    "start": timestamps[0] if timestamps else None,
                    "end": timestamps[-1] if timestamps else None,
                },
            }

            # Calculate percentiles
            if len(latencies) >= 10:
                sorted_latencies = sorted(latencies)
                p50 = self._percentile(sorted_latencies, 50)
                p95 = self._percentile(sorted_latencies, 95)
                p99 = self._percentile(sorted_latencies, 99)
                latency_dict = analysis["latency"]
                assert isinstance(latency_dict, dict)
                latency_dict["p50"] = p50
                latency_dict["p95"] = p95
                latency_dict["p99"] = p99

            # Detect degradation trend
            if len(latencies) >= 10:
                mid_point = len(latencies) // 2
                first_half_mean = statistics.mean(latencies[:mid_point])
                second_half_mean = statistics.mean(latencies[mid_point:])

                if first_half_mean > 0:
                    trend_change = (
                        second_half_mean - first_half_mean
                    ) / first_half_mean
                    analysis["trend"] = {
                        "direction": ("degrading" if trend_change > 0.1 else "stable"),
                        "change_percent": trend_change,
                    }

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze trends: {e}")
            return {
                "endpoint": endpoint,
                "method": method,
                "days": days,
                "error": str(e),
            }

    @staticmethod
    def _percentile(sorted_data: List[float], percentile: int) -> float:
        """
        Calculate percentile value.

        Args:
            sorted_data: Sorted list of values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not sorted_data:
            return 0.0

        index = (percentile / 100.0) * (len(sorted_data) - 1)
        lower = int(index)
        upper = lower + 1

        if upper >= len(sorted_data):
            return sorted_data[-1]

        weight = index - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight

    def update_baseline(
        self, endpoint: str, approval_token: str, method: str = "GET"
    ) -> bool:
        """
        Update baseline with approval.

        Args:
            endpoint: API endpoint path
            approval_token: Approval token for update
            method: HTTP method

        Returns:
            True if update successful

        Raises:
            RegressionEngineError: If update fails
        """
        if self.approval_required and not approval_token:
            raise RegressionEngineError("Approval token required for baseline update")

        # In production, validate approval_token against auth system
        # For now, just check it's not empty
        if self.approval_required and len(approval_token) < 10:
            raise RegressionEngineError("Invalid approval token")

        baseline_path = self._get_baseline_path(endpoint, method)

        if not baseline_path.exists():
            raise BaselineNotFoundError(f"No baseline found for {method} {endpoint}")

        try:
            # Create backup
            backup_path = baseline_path.with_suffix(
                f".backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            )
            backup_path.write_text(baseline_path.read_text())

            logger.info(
                f"Baseline backup created at {backup_path} for " f"{method} {endpoint}"
            )

            # In real implementation, would fetch latest response
            # and save as new baseline. For now, just log the approval
            logger.info(
                f"Baseline update approved for {method} {endpoint} "
                f"with token {approval_token[:10]}..."
            )

            return True

        except Exception as e:
            logger.error(f"Failed to update baseline: {e}")
            raise RegressionEngineError(f"Baseline update failed: {e}") from e

    def cleanup_old_history(self) -> int:
        """
        Clean up history files older than retention period.

        Returns:
            Number of entries cleaned up
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        cleaned_count = 0

        try:
            for history_file in self.history_dir.glob("*_history.jsonl"):
                temp_file = history_file.with_suffix(".tmp")
                kept_count = 0

                with open(history_file, "r") as infile, open(temp_file, "w") as outfile:
                    for line in infile:
                        try:
                            entry = json.loads(line.strip())
                            entry_time = datetime.fromisoformat(entry["timestamp"])

                            if entry_time >= cutoff_date:
                                outfile.write(line)
                                kept_count += 1
                            else:
                                cleaned_count += 1
                        except (json.JSONDecodeError, KeyError, ValueError):
                            continue

                # Replace original with cleaned file
                if kept_count > 0:
                    temp_file.replace(history_file)
                else:
                    temp_file.unlink()
                    history_file.unlink()

            logger.info(f"Cleaned up {cleaned_count} old history entries")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup history: {e}")
            return 0
