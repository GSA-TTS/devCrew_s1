"""
SLO (Service Level Objective) Tracker for APM & Monitoring Platform.

This module provides comprehensive SLO monitoring and error budget tracking
capabilities, including SLO definition, compliance monitoring, error budget
calculation, and reporting.

Supports:
- SLO definition and configuration
- Error budget calculation and tracking
- Availability and latency SLO types
- Multi-window SLO evaluation (rolling, calendar)
- SLO compliance monitoring and alerting
- Error budget burn rate analysis
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class SLOType(Enum):
    """SLO type enumeration."""

    AVAILABILITY = "availability"
    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    CUSTOM = "custom"


class WindowType(Enum):
    """Time window type for SLO evaluation."""

    ROLLING = "rolling"  # Rolling window (e.g., last 30 days)
    CALENDAR = "calendar"  # Calendar period (e.g., current month)


@dataclass
class SLODefinition:
    """Definition of a Service Level Objective."""

    name: str
    slo_type: SLOType
    target: float  # Target percentage (e.g., 99.9 for 99.9%)
    window_days: int = 30  # Evaluation window in days
    window_type: WindowType = WindowType.ROLLING
    description: str = ""
    service: str = ""
    labels: Dict[str, str] = field(default_factory=dict)

    # Type-specific configuration
    latency_threshold_ms: Optional[float] = None  # For latency SLOs
    success_query: Optional[str] = None  # PromQL query for successes
    total_query: Optional[str] = None  # PromQL query for total requests

    def validate(self) -> bool:
        """Validate SLO definition."""
        if self.target <= 0 or self.target > 100:
            raise ValueError("SLO target must be between 0 and 100")

        if self.window_days <= 0:
            raise ValueError("Window days must be positive")

        if self.slo_type == SLOType.LATENCY and self.latency_threshold_ms is None:
            raise ValueError("Latency SLO requires latency_threshold_ms")

        return True


@dataclass
class SLOStatus:
    """Current status of an SLO."""

    slo_name: str
    target: float
    actual: float
    error_budget_remaining: float  # Percentage of budget remaining
    error_budget_minutes: float  # Minutes of budget remaining
    is_compliant: bool
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    evaluation_window_start: Optional[datetime] = None
    evaluation_window_end: Optional[datetime] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "slo_name": self.slo_name,
            "target": self.target,
            "actual": self.actual,
            "error_budget_remaining": self.error_budget_remaining,
            "error_budget_minutes": self.error_budget_minutes,
            "is_compliant": self.is_compliant,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "evaluation_window_start": (
                self.evaluation_window_start.isoformat()
                if self.evaluation_window_start
                else None
            ),
            "evaluation_window_end": (
                self.evaluation_window_end.isoformat()
                if self.evaluation_window_end
                else None
            ),
            "timestamp": self.timestamp.isoformat(),
        }


class SLOTracker:
    """
    SLO monitoring and error budget tracker.

    Tracks Service Level Objectives, calculates error budgets, monitors
    compliance, and generates SLO reports.
    """

    def __init__(self):
        """Initialize SLO tracker."""
        self.slos: Dict[str, SLODefinition] = {}
        self.history: Dict[str, List[SLOStatus]] = {}
        logger.info("Initialized SLOTracker")

    def add_slo(self, slo: SLODefinition):
        """
        Add SLO definition.

        Args:
            slo: SLO definition

        Raises:
            ValueError: If SLO definition is invalid
        """
        slo.validate()
        self.slos[slo.name] = slo
        self.history[slo.name] = []
        logger.info(f"Added SLO: {slo.name} ({slo.slo_type.value}, target={slo.target}%)")

    def remove_slo(self, name: str):
        """
        Remove SLO definition.

        Args:
            name: SLO name
        """
        if name in self.slos:
            del self.slos[name]
            del self.history[name]
            logger.info(f"Removed SLO: {name}")

    def calculate_availability_slo(
        self,
        slo: SLODefinition,
        prometheus_client,
    ) -> SLOStatus:
        """
        Calculate availability SLO status.

        Args:
            slo: SLO definition
            prometheus_client: PrometheusWrapper instance

        Returns:
            SLO status
        """
        logger.debug(f"Calculating availability SLO: {slo.name}")

        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=slo.window_days)

        # Query total requests
        if slo.total_query:
            total_result = prometheus_client.query_range(
                query=slo.total_query,
                start=start_time,
                end=end_time,
                step="1h",
            )
            total_requests = self._sum_query_results(total_result)
        else:
            # Default query: sum all requests
            total_result = prometheus_client.query_range(
                query=f'sum(rate(http_requests_total{{service="{slo.service}"}}[5m]))',
                start=start_time,
                end=end_time,
                step="1h",
            )
            total_requests = self._sum_query_results(total_result)

        # Query successful requests
        if slo.success_query:
            success_result = prometheus_client.query_range(
                query=slo.success_query,
                start=start_time,
                end=end_time,
                step="1h",
            )
            successful_requests = self._sum_query_results(success_result)
        else:
            # Default query: requests with status code < 500
            success_result = prometheus_client.query_range(
                query=f'sum(rate(http_requests_total{{service="{slo.service}",code!~"5.."}}[5m]))',
                start=start_time,
                end=end_time,
                step="1h",
            )
            successful_requests = self._sum_query_results(success_result)

        # Calculate availability
        if total_requests > 0:
            actual_availability = (successful_requests / total_requests) * 100
        else:
            actual_availability = 100.0  # No requests = 100% availability

        # Calculate error budget
        error_budget_remaining = self._calculate_error_budget(
            target=slo.target,
            actual=actual_availability,
            window_days=slo.window_days,
        )

        # Calculate error budget in minutes
        total_minutes = slo.window_days * 24 * 60
        error_budget_minutes = (error_budget_remaining / 100) * total_minutes

        status = SLOStatus(
            slo_name=slo.name,
            target=slo.target,
            actual=actual_availability,
            error_budget_remaining=error_budget_remaining,
            error_budget_minutes=error_budget_minutes,
            is_compliant=actual_availability >= slo.target,
            total_requests=int(total_requests),
            successful_requests=int(successful_requests),
            failed_requests=int(total_requests - successful_requests),
            evaluation_window_start=start_time,
            evaluation_window_end=end_time,
        )

        logger.info(
            f"SLO {slo.name}: {actual_availability:.3f}% "
            f"(target={slo.target}%, budget={error_budget_remaining:.2f}%)"
        )

        return status

    def calculate_latency_slo(
        self,
        slo: SLODefinition,
        prometheus_client,
    ) -> SLOStatus:
        """
        Calculate latency SLO status.

        Args:
            slo: SLO definition
            prometheus_client: PrometheusWrapper instance

        Returns:
            SLO status
        """
        logger.debug(f"Calculating latency SLO: {slo.name}")

        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=slo.window_days)

        # Query total requests
        if slo.total_query:
            total_result = prometheus_client.query_range(
                query=slo.total_query,
                start=start_time,
                end=end_time,
                step="1h",
            )
            total_requests = self._sum_query_results(total_result)
        else:
            # Default query
            total_result = prometheus_client.query_range(
                query=f'sum(rate(http_request_duration_seconds_count{{service="{slo.service}"}}[5m]))',
                start=start_time,
                end=end_time,
                step="1h",
            )
            total_requests = self._sum_query_results(total_result)

        # Query requests within latency threshold
        if slo.success_query:
            success_result = prometheus_client.query_range(
                query=slo.success_query,
                start=start_time,
                end=end_time,
                step="1h",
            )
            successful_requests = self._sum_query_results(success_result)
        else:
            # Default query: requests below threshold
            threshold_seconds = (slo.latency_threshold_ms or 1000) / 1000
            success_result = prometheus_client.query_range(
                query=f'sum(rate(http_request_duration_seconds_bucket{{service="{slo.service}",le="{threshold_seconds}"}}[5m]))',
                start=start_time,
                end=end_time,
                step="1h",
            )
            successful_requests = self._sum_query_results(success_result)

        # Calculate percentage of requests meeting latency target
        if total_requests > 0:
            actual_percentage = (successful_requests / total_requests) * 100
        else:
            actual_percentage = 100.0

        # Calculate error budget
        error_budget_remaining = self._calculate_error_budget(
            target=slo.target,
            actual=actual_percentage,
            window_days=slo.window_days,
        )

        # Calculate error budget in minutes
        total_minutes = slo.window_days * 24 * 60
        error_budget_minutes = (error_budget_remaining / 100) * total_minutes

        status = SLOStatus(
            slo_name=slo.name,
            target=slo.target,
            actual=actual_percentage,
            error_budget_remaining=error_budget_remaining,
            error_budget_minutes=error_budget_minutes,
            is_compliant=actual_percentage >= slo.target,
            total_requests=int(total_requests),
            successful_requests=int(successful_requests),
            failed_requests=int(total_requests - successful_requests),
            evaluation_window_start=start_time,
            evaluation_window_end=end_time,
        )

        logger.info(
            f"SLO {slo.name}: {actual_percentage:.3f}% requests < "
            f"{slo.latency_threshold_ms}ms (target={slo.target}%, "
            f"budget={error_budget_remaining:.2f}%)"
        )

        return status

    def calculate_slo(
        self,
        name: str,
        prometheus_client,
    ) -> SLOStatus:
        """
        Calculate SLO status.

        Args:
            name: SLO name
            prometheus_client: PrometheusWrapper instance

        Returns:
            SLO status

        Raises:
            KeyError: If SLO not found
        """
        if name not in self.slos:
            raise KeyError(f"SLO not found: {name}")

        slo = self.slos[name]

        if slo.slo_type == SLOType.AVAILABILITY:
            status = self.calculate_availability_slo(slo, prometheus_client)
        elif slo.slo_type == SLOType.LATENCY:
            status = self.calculate_latency_slo(slo, prometheus_client)
        elif slo.slo_type == SLOType.ERROR_RATE:
            # Error rate is inverse of availability
            status = self.calculate_availability_slo(slo, prometheus_client)
        else:
            raise ValueError(f"Unsupported SLO type: {slo.slo_type}")

        # Store in history
        self._add_to_history(name, status)

        return status

    def calculate_all_slos(self, prometheus_client) -> Dict[str, SLOStatus]:
        """
        Calculate status for all SLOs.

        Args:
            prometheus_client: PrometheusWrapper instance

        Returns:
            Dictionary mapping SLO names to statuses
        """
        logger.info(f"Calculating {len(self.slos)} SLOs")

        statuses = {}
        for name in self.slos:
            try:
                statuses[name] = self.calculate_slo(name, prometheus_client)
            except Exception as e:
                logger.error(f"Error calculating SLO {name}: {e}", exc_info=True)

        compliant_count = sum(1 for s in statuses.values() if s.is_compliant)
        logger.info(f"SLO evaluation complete: {compliant_count}/{len(statuses)} compliant")

        return statuses

    def _sum_query_results(self, result: Dict[str, Any]) -> float:
        """Sum all values from query result."""
        data = result.get("data", {})
        results = data.get("result", [])

        total = 0.0
        for series in results:
            values = series.get("values", [])
            for timestamp, value_str in values:
                try:
                    total += float(value_str)
                except (ValueError, TypeError):
                    pass

        return total

    def _calculate_error_budget(
        self, target: float, actual: float, window_days: int
    ) -> float:
        """
        Calculate remaining error budget percentage.

        Args:
            target: Target SLO percentage
            actual: Actual achieved percentage
            window_days: Evaluation window in days

        Returns:
            Remaining error budget as percentage
        """
        # Total error budget is (100 - target)
        total_budget = 100 - target

        if total_budget == 0:
            return 100.0 if actual >= target else 0.0

        # Used budget is (100 - actual)
        used_budget = 100 - actual

        # Remaining budget percentage
        remaining = ((total_budget - used_budget) / total_budget) * 100

        return max(0.0, min(100.0, remaining))

    def calculate_burn_rate(
        self,
        name: str,
        window_hours: int = 1,
    ) -> float:
        """
        Calculate error budget burn rate.

        Args:
            name: SLO name
            window_hours: Window to calculate burn rate over

        Returns:
            Burn rate (1.0 = burning at nominal rate)
        """
        if name not in self.history or not self.history[name]:
            return 0.0

        # Get recent history
        cutoff_time = datetime.utcnow() - timedelta(hours=window_hours)
        recent_statuses = [
            s for s in self.history[name] if s.timestamp >= cutoff_time
        ]

        if len(recent_statuses) < 2:
            return 0.0

        # Calculate budget consumed in window
        earliest = recent_statuses[0]
        latest = recent_statuses[-1]

        budget_consumed = (
            earliest.error_budget_remaining - latest.error_budget_remaining
        )

        # Calculate expected consumption rate
        slo = self.slos[name]
        total_hours = slo.window_days * 24
        expected_rate = 100 / total_hours  # Budget consumed per hour at nominal rate

        # Actual rate
        actual_rate = budget_consumed / window_hours if window_hours > 0 else 0.0

        # Burn rate (actual / expected)
        burn_rate = actual_rate / expected_rate if expected_rate > 0 else 0.0

        logger.debug(f"SLO {name} burn rate: {burn_rate:.2f}x over {window_hours}h")

        return burn_rate

    def _add_to_history(self, name: str, status: SLOStatus):
        """Add status to history."""
        if name not in self.history:
            self.history[name] = []

        self.history[name].append(status)

        # Keep last 1000 entries
        if len(self.history[name]) > 1000:
            self.history[name] = self.history[name][-1000:]

    def get_history(
        self,
        name: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[SLOStatus]:
        """
        Get historical SLO statuses.

        Args:
            name: SLO name
            since: Optional start time filter
            limit: Optional maximum number of results

        Returns:
            List of SLO statuses
        """
        if name not in self.history:
            return []

        statuses = self.history[name]

        if since:
            statuses = [s for s in statuses if s.timestamp >= since]

        if limit:
            statuses = statuses[-limit:]

        return statuses

    def generate_report(self, prometheus_client) -> Dict[str, Any]:
        """
        Generate comprehensive SLO report.

        Args:
            prometheus_client: PrometheusWrapper instance

        Returns:
            Report dictionary
        """
        logger.info("Generating SLO report")

        statuses = self.calculate_all_slos(prometheus_client)

        # Calculate summary statistics
        total_slos = len(statuses)
        compliant_slos = sum(1 for s in statuses.values() if s.is_compliant)
        non_compliant_slos = total_slos - compliant_slos

        # Get burn rates
        burn_rates = {}
        for name in self.slos:
            burn_rates[name] = self.calculate_burn_rate(name, window_hours=1)

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_slos": total_slos,
                "compliant_slos": compliant_slos,
                "non_compliant_slos": non_compliant_slos,
                "compliance_rate": (
                    (compliant_slos / total_slos * 100) if total_slos > 0 else 0.0
                ),
            },
            "slos": {
                name: {
                    **status.to_dict(),
                    "burn_rate_1h": burn_rates.get(name, 0.0),
                }
                for name, status in statuses.items()
            },
        }

        logger.info(
            f"Report generated: {compliant_slos}/{total_slos} SLOs compliant"
        )

        return report
