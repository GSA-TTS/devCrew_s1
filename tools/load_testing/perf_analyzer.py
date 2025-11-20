"""
Issue #37: Performance Analyzer Module
Analyzes load test results and provides insights.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import structlog
from scipy import stats

logger = structlog.get_logger()


class TestType(Enum):
    """Types of load tests."""

    LOAD = "load"  # Sustained load
    STRESS = "stress"  # Increasing load to find limits
    SPIKE = "spike"  # Sudden traffic spike
    SOAK = "soak"  # Extended duration test
    BASELINE = "baseline"  # Baseline performance


class BottleneckType(Enum):
    """Types of performance bottlenecks."""

    HIGH_LATENCY = "high_latency"
    HIGH_ERROR_RATE = "high_error_rate"
    THROUGHPUT_LIMIT = "throughput_limit"
    MEMORY_ISSUE = "memory_issue"
    CPU_BOUND = "cpu_bound"
    IO_BOUND = "io_bound"
    CONNECTION_LIMIT = "connection_limit"


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics."""

    # Response time metrics (milliseconds)
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p90_response_time: float
    p95_response_time: float
    p99_response_time: float
    std_response_time: float

    # Throughput metrics
    total_requests: int
    requests_per_second: float
    data_received_bytes: int
    data_sent_bytes: int

    # Error metrics
    total_errors: int
    error_rate: float  # Percentage
    status_code_distribution: Dict[int, int]

    # Connection metrics
    connections_active: int
    connections_waiting: int
    connection_duration_avg: float

    # Test duration
    test_duration_seconds: float


@dataclass
class Bottleneck:
    """Identified performance bottleneck."""

    type: BottleneckType
    severity: str  # "low", "medium", "high", "critical"
    description: str
    metric_value: float
    threshold_value: Optional[float]
    recommendation: str


@dataclass
class CapacityRecommendation:
    """Capacity planning recommendation."""

    max_sustainable_load: int  # VUs
    recommended_max_load: int  # VUs (with safety margin)
    safety_margin: float  # Percentage
    limiting_factor: str
    confidence_level: str  # "low", "medium", "high"
    notes: List[str]


@dataclass
class SLAValidation:
    """SLA validation result."""

    passed: bool
    sla_name: str
    metric_name: str
    expected_value: float
    actual_value: float
    deviation_percentage: float
    notes: str


class PerformanceAnalyzer:
    """Analyze load test results and provide insights."""

    def __init__(
        self,
        metrics: Dict[str, Any],
        test_duration: float,
        test_type: TestType = TestType.LOAD,
    ):
        """
        Initialize performance analyzer.

        Args:
            metrics: Raw metrics from k6 test
            test_duration: Test duration in seconds
            test_type: Type of load test
        """
        self.raw_metrics = metrics
        self.test_duration = test_duration
        self.test_type = test_type
        self.aggregated_metrics: Optional[PerformanceMetrics] = None
        self._analyze()

    def _analyze(self) -> None:
        """Perform initial analysis of metrics."""
        self.aggregated_metrics = self._aggregate_metrics()
        logger.info(
            "metrics_analyzed",
            test_type=self.test_type.value,
            total_requests=self.aggregated_metrics.total_requests,
            avg_response_time=self.aggregated_metrics.avg_response_time,
            error_rate=self.aggregated_metrics.error_rate,
        )

    def _aggregate_metrics(self) -> PerformanceMetrics:
        """Aggregate raw metrics into structured performance metrics."""
        # Extract response time data
        response_times = self._extract_metric_values("http_req_duration")
        if not response_times:
            response_times = [0.0]

        response_times_array = np.array(response_times)

        # Calculate percentiles
        percentiles = np.percentile(
            response_times_array, [50, 90, 95, 99]
        ).tolist()

        # Extract request counts
        total_requests = len(response_times)
        failed_requests = self._extract_metric_values("http_req_failed")
        total_errors = sum(1 for x in failed_requests if x > 0)

        # Calculate error rate
        error_rate = (
            (total_errors / total_requests * 100) if total_requests > 0 else 0.0
        )

        # Extract throughput data
        data_received = sum(self._extract_metric_values("data_received") or [0])
        data_sent = sum(self._extract_metric_values("data_sent") or [0])

        # Calculate RPS
        rps = total_requests / self.test_duration if self.test_duration > 0 else 0

        # Extract connection metrics
        connections = self._extract_metric_values("http_req_connecting") or [0]
        connection_duration_avg = float(np.mean(connections)) if connections else 0

        # Status code distribution
        status_codes = self._extract_status_codes()

        return PerformanceMetrics(
            avg_response_time=float(np.mean(response_times_array)),
            min_response_time=float(np.min(response_times_array)),
            max_response_time=float(np.max(response_times_array)),
            p50_response_time=percentiles[0],
            p90_response_time=percentiles[1],
            p95_response_time=percentiles[2],
            p99_response_time=percentiles[3],
            std_response_time=float(np.std(response_times_array)),
            total_requests=total_requests,
            requests_per_second=rps,
            data_received_bytes=int(data_received),
            data_sent_bytes=int(data_sent),
            total_errors=total_errors,
            error_rate=error_rate,
            status_code_distribution=status_codes,
            connections_active=len(connections),
            connections_waiting=0,  # Would need specific k6 metric
            connection_duration_avg=connection_duration_avg,
            test_duration_seconds=self.test_duration,
        )

    def _extract_metric_values(self, metric_name: str) -> List[float]:
        """Extract all values for a specific metric."""
        if metric_name not in self.raw_metrics:
            return []
        return self.raw_metrics[metric_name]

    def _extract_status_codes(self) -> Dict[int, int]:
        """Extract HTTP status code distribution."""
        # This would be extracted from k6 metrics with tags
        # For now, return empty dict - would need k6 output with tags
        return {}

    def identify_bottlenecks(
        self,
        latency_threshold_ms: float = 500,
        error_rate_threshold: float = 1.0,
        rps_expected: Optional[float] = None,
    ) -> List[Bottleneck]:
        """
        Identify performance bottlenecks.

        Args:
            latency_threshold_ms: P95 latency threshold in milliseconds
            error_rate_threshold: Acceptable error rate percentage
            rps_expected: Expected requests per second

        Returns:
            List of identified bottlenecks
        """
        if not self.aggregated_metrics:
            return []

        bottlenecks = []

        # Check latency
        if self.aggregated_metrics.p95_response_time > latency_threshold_ms:
            severity = self._calculate_severity(
                self.aggregated_metrics.p95_response_time,
                latency_threshold_ms,
                [latency_threshold_ms * 1.5, latency_threshold_ms * 2],
            )
            bottlenecks.append(
                Bottleneck(
                    type=BottleneckType.HIGH_LATENCY,
                    severity=severity,
                    description=(
                        f"P95 response time ({self.aggregated_metrics.p95_response_time:.2f}ms) "
                        f"exceeds threshold ({latency_threshold_ms}ms)"
                    ),
                    metric_value=self.aggregated_metrics.p95_response_time,
                    threshold_value=latency_threshold_ms,
                    recommendation=(
                        "Investigate slow database queries, optimize algorithms, "
                        "add caching, or scale horizontally"
                    ),
                )
            )

        # Check error rate
        if self.aggregated_metrics.error_rate > error_rate_threshold:
            severity = self._calculate_severity(
                self.aggregated_metrics.error_rate,
                error_rate_threshold,
                [error_rate_threshold * 2, error_rate_threshold * 5],
            )
            bottlenecks.append(
                Bottleneck(
                    type=BottleneckType.HIGH_ERROR_RATE,
                    severity=severity,
                    description=(
                        f"Error rate ({self.aggregated_metrics.error_rate:.2f}%) "
                        f"exceeds threshold ({error_rate_threshold}%)"
                    ),
                    metric_value=self.aggregated_metrics.error_rate,
                    threshold_value=error_rate_threshold,
                    recommendation=(
                        "Review error logs, check resource limits (memory, "
                        "connections, file descriptors), fix application errors"
                    ),
                )
            )

        # Check throughput
        if rps_expected and self.aggregated_metrics.requests_per_second < rps_expected:
            deficit = rps_expected - self.aggregated_metrics.requests_per_second
            severity = self._calculate_severity(
                deficit,
                rps_expected * 0.1,
                [rps_expected * 0.2, rps_expected * 0.5],
            )
            bottlenecks.append(
                Bottleneck(
                    type=BottleneckType.THROUGHPUT_LIMIT,
                    severity=severity,
                    description=(
                        f"Throughput ({self.aggregated_metrics.requests_per_second:.2f} RPS) "
                        f"below expected ({rps_expected} RPS)"
                    ),
                    metric_value=self.aggregated_metrics.requests_per_second,
                    threshold_value=rps_expected,
                    recommendation=(
                        "Scale application instances, optimize request handling, "
                        "reduce per-request overhead"
                    ),
                )
            )

        # Check variability (high standard deviation indicates inconsistency)
        cv = (
            self.aggregated_metrics.std_response_time
            / self.aggregated_metrics.avg_response_time
            if self.aggregated_metrics.avg_response_time > 0
            else 0
        )
        if cv > 1.0:  # Coefficient of variation > 1 indicates high variability
            bottlenecks.append(
                Bottleneck(
                    type=BottleneckType.IO_BOUND,
                    severity="medium",
                    description=(
                        f"High response time variability (CV={cv:.2f}) "
                        "suggests inconsistent performance"
                    ),
                    metric_value=cv,
                    threshold_value=1.0,
                    recommendation=(
                        "Check for background processes, network instability, "
                        "or resource contention"
                    ),
                )
            )

        logger.info("bottlenecks_identified", count=len(bottlenecks))
        return bottlenecks

    def _calculate_severity(
        self, actual: float, threshold: float, levels: List[float]
    ) -> str:
        """Calculate severity based on how much actual exceeds threshold."""
        excess = actual - threshold
        if excess <= 0:
            return "low"
        if excess < levels[0]:
            return "medium"
        if excess < levels[1]:
            return "high"
        return "critical"

    def recommend_capacity(
        self,
        target_latency_ms: float = 500,
        target_error_rate: float = 1.0,
        safety_margin: float = 0.2,  # 20% safety margin
    ) -> CapacityRecommendation:
        """
        Generate capacity planning recommendations.

        Args:
            target_latency_ms: Target P95 latency
            target_error_rate: Target error rate percentage
            safety_margin: Safety margin for recommendations (0.2 = 20%)

        Returns:
            Capacity recommendation
        """
        if not self.aggregated_metrics:
            return CapacityRecommendation(
                max_sustainable_load=0,
                recommended_max_load=0,
                safety_margin=safety_margin,
                limiting_factor="unknown",
                confidence_level="low",
                notes=["Insufficient data for capacity planning"],
            )

        # Determine limiting factor
        limiting_factor = "latency"
        confidence = "medium"
        notes = []

        # Simple linear extrapolation (in production, use more sophisticated models)
        # This is a placeholder - real implementation would use regression analysis
        if self.aggregated_metrics.error_rate > target_error_rate:
            limiting_factor = "error_rate"
            max_load = int(
                self.aggregated_metrics.total_requests
                * (target_error_rate / self.aggregated_metrics.error_rate)
            )
            notes.append(
                "Error rate is primary limiting factor. "
                "Consider resource scaling or error handling improvements."
            )
        elif self.aggregated_metrics.p95_response_time > target_latency_ms:
            limiting_factor = "latency"
            max_load = int(
                self.aggregated_metrics.total_requests
                * (target_latency_ms / self.aggregated_metrics.p95_response_time)
            )
            notes.append(
                "Latency is primary limiting factor. "
                "Consider performance optimization or scaling."
            )
        else:
            # System is performing well, extrapolate based on current metrics
            max_load = int(self.aggregated_metrics.total_requests * 1.5)
            confidence = "low"
            notes.append(
                "System performing within targets. "
                "Recommendation based on conservative extrapolation."
            )
            notes.append("Run stress test to find actual capacity limits.")

        recommended_load = int(max_load * (1 - safety_margin))

        logger.info(
            "capacity_recommended",
            max_load=max_load,
            recommended_load=recommended_load,
            limiting_factor=limiting_factor,
        )

        return CapacityRecommendation(
            max_sustainable_load=max_load,
            recommended_max_load=recommended_load,
            safety_margin=safety_margin,
            limiting_factor=limiting_factor,
            confidence_level=confidence,
            notes=notes,
        )

    def validate_sla(
        self,
        sla_definitions: List[Dict[str, Any]],
    ) -> List[SLAValidation]:
        """
        Validate test results against SLA definitions.

        Args:
            sla_definitions: List of SLA definitions with format:
                {
                    "name": "API Response Time",
                    "metric": "p95_response_time",
                    "threshold": 500,
                    "operator": "less_than"
                }

        Returns:
            List of SLA validation results
        """
        if not self.aggregated_metrics:
            return []

        validations = []

        for sla in sla_definitions:
            name = sla.get("name", "Unnamed SLA")
            metric = sla.get("metric")
            threshold = sla.get("threshold")
            operator = sla.get("operator", "less_than")

            if not metric or threshold is None:
                continue

            # Get actual value from aggregated metrics
            actual_value = getattr(self.aggregated_metrics, metric, None)
            if actual_value is None:
                continue

            # Evaluate based on operator
            passed = False
            if operator == "less_than":
                passed = actual_value < threshold
            elif operator == "less_than_or_equal":
                passed = actual_value <= threshold
            elif operator == "greater_than":
                passed = actual_value > threshold
            elif operator == "greater_than_or_equal":
                passed = actual_value >= threshold

            # Calculate deviation
            deviation = (
                ((actual_value - threshold) / threshold * 100)
                if threshold != 0
                else 0
            )

            notes = f"SLA {'passed' if passed else 'failed'}"
            if not passed:
                notes += f" by {abs(deviation):.1f}%"

            validations.append(
                SLAValidation(
                    passed=passed,
                    sla_name=name,
                    metric_name=metric,
                    expected_value=threshold,
                    actual_value=actual_value,
                    deviation_percentage=deviation,
                    notes=notes,
                )
            )

        logger.info(
            "sla_validated",
            total=len(validations),
            passed=sum(1 for v in validations if v.passed),
        )

        return validations

    def compare_with_baseline(
        self,
        baseline_metrics: PerformanceMetrics,
        significance_level: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Compare current results with baseline performance.

        Args:
            baseline_metrics: Baseline performance metrics
            significance_level: Statistical significance level

        Returns:
            Comparison analysis with regression detection
        """
        if not self.aggregated_metrics:
            return {}

        comparison = {
            "has_regression": False,
            "regressions": [],
            "improvements": [],
            "summary": {},
        }

        # Compare key metrics
        metrics_to_compare = [
            ("avg_response_time", "Average Response Time", "ms", "lower"),
            ("p95_response_time", "P95 Response Time", "ms", "lower"),
            ("p99_response_time", "P99 Response Time", "ms", "lower"),
            ("error_rate", "Error Rate", "%", "lower"),
            ("requests_per_second", "Throughput", "RPS", "higher"),
        ]

        for metric_name, display_name, unit, better_direction in metrics_to_compare:
            current = getattr(self.aggregated_metrics, metric_name)
            baseline = getattr(baseline_metrics, metric_name)

            if baseline == 0:
                continue

            change_pct = ((current - baseline) / baseline) * 100

            is_regression = (
                (better_direction == "lower" and change_pct > 10)
                or (better_direction == "higher" and change_pct < -10)
            )

            is_improvement = (
                (better_direction == "lower" and change_pct < -5)
                or (better_direction == "higher" and change_pct > 5)
            )

            if is_regression:
                comparison["has_regression"] = True
                comparison["regressions"].append(
                    {
                        "metric": display_name,
                        "baseline": baseline,
                        "current": current,
                        "change_pct": change_pct,
                        "unit": unit,
                    }
                )

            if is_improvement:
                comparison["improvements"].append(
                    {
                        "metric": display_name,
                        "baseline": baseline,
                        "current": current,
                        "change_pct": change_pct,
                        "unit": unit,
                    }
                )

            comparison["summary"][metric_name] = {
                "baseline": baseline,
                "current": current,
                "change_pct": change_pct,
                "regression": is_regression,
                "improvement": is_improvement,
            }

        logger.info(
            "baseline_compared",
            regressions=len(comparison["regressions"]),
            improvements=len(comparison["improvements"]),
        )

        return comparison
