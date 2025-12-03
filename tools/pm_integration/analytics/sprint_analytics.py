"""
Sprint Analytics Engine for Project Management Integration Platform.

This module provides comprehensive sprint reporting and analytics
capabilities including velocity calculation, burndown/burnup charts,
cycle time metrics, sprint predictability analysis, and release
forecasting based on historical data.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class SprintConfig(BaseModel):
    """Configuration for sprint analytics."""

    output_dir: Path = Field(
        default=Path("sprint_reports"),
        description="Directory for output files",
    )
    chart_format: str = Field(
        default="png",
        description="Chart output format (png, svg, pdf)",
    )
    include_weekends: bool = Field(
        default=False, description="Include weekends in burndown"
    )
    confidence_level: float = Field(
        default=0.95,
        description="Confidence level for predictions",
        ge=0.5,
        le=0.99,
    )
    velocity_window: int = Field(
        default=5,
        description="Number of sprints for velocity calculation",
        ge=1,
    )
    chart_style: str = Field(
        default="seaborn-v0_8", description="Matplotlib style"
    )
    dpi: int = Field(default=300, description="Chart DPI", ge=72, le=600)
    figsize: Tuple[int, int] = Field(
        default=(12, 8), description="Chart figure size (width, height)"
    )

    @field_validator("chart_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate chart format."""
        allowed = ["png", "svg", "pdf"]
        if v.lower() not in allowed:
            raise ValueError(f"chart_format must be one of {allowed}")
        return v.lower()

    @field_validator("confidence_level")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence level."""
        if not 0.5 <= v <= 0.99:
            raise ValueError("confidence_level must be between 0.5 and 0.99")
        return v


class IssueData(BaseModel):
    """Issue data for sprint analytics."""

    issue_id: str
    issue_type: str
    status: str
    story_points: Optional[float] = None
    created_date: datetime
    completed_date: Optional[datetime] = None
    sprint_id: str
    sprint_name: str
    assignee: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    priority: Optional[str] = None

    @field_validator("story_points")
    @classmethod
    def validate_points(cls, v: Optional[float]) -> Optional[float]:
        """Validate story points are non-negative."""
        if v is not None and v < 0:
            raise ValueError("story_points must be non-negative")
        return v


class SprintData(BaseModel):
    """Sprint metadata and metrics."""

    sprint_id: str
    sprint_name: str
    start_date: datetime
    end_date: datetime
    committed_points: float = Field(ge=0.0)
    completed_points: float = Field(ge=0.0)
    team_capacity: Optional[float] = None
    issues: List[IssueData] = Field(default_factory=list)

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: datetime, info: Any) -> datetime:
        """Validate end_date is after start_date."""
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class VelocityMetrics(BaseModel):
    """Velocity calculation results."""

    mean_velocity: float
    median_velocity: float
    std_dev: float
    min_velocity: float
    max_velocity: float
    velocity_trend: str  # "INCREASING", "DECREASING", "STABLE"
    trend_percentage: float
    sprints_analyzed: int
    velocity_history: List[float]


class CycleTimeMetrics(BaseModel):
    """Cycle time and lead time metrics."""

    avg_cycle_time_days: float
    median_cycle_time_days: float
    avg_lead_time_days: float
    median_lead_time_days: float
    p50_cycle_time: float
    p75_cycle_time: float
    p90_cycle_time: float
    issues_analyzed: int


class PredictabilityMetrics(BaseModel):
    """Sprint predictability analysis."""

    commitment_accuracy: float  # % of committed points completed
    velocity_variance: float
    consistency_score: float  # 0-100 scale
    prediction_confidence: float
    risk_level: str  # "LOW", "MEDIUM", "HIGH"


class ReleaseForecast(BaseModel):
    """Release forecasting based on historical velocity."""

    target_points: float
    estimated_sprints: int
    estimated_completion_date: datetime
    confidence_interval_low: int
    confidence_interval_high: int
    completion_probability: float
    based_on_sprints: int


class SprintAnalytics:
    """
    Sprint Analytics Engine for comprehensive sprint reporting.

    Features:
    - Velocity calculation and trending
    - Burndown and burnup chart generation
    - Cycle time and lead time metrics
    - Sprint predictability analysis
    - Team capacity planning
    - Release forecasting
    - Statistical analysis and reporting
    """

    def __init__(self, config: Optional[SprintConfig] = None):
        """
        Initialize Sprint Analytics Engine.

        Args:
            config: Sprint analytics configuration
        """
        self.config = config or SprintConfig()
        self.sprints: List[SprintData] = []
        self._setup_output_dir()
        self._setup_matplotlib()

    def _setup_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {self.config.output_dir}")

    def _setup_matplotlib(self) -> None:
        """Configure matplotlib settings."""
        try:
            plt.style.use(self.config.chart_style)
        except Exception as e:
            logger.warning(
                f"Could not set style {self.config.chart_style}: {e}"
            )
            plt.style.use("default")

    def add_sprint(self, sprint: SprintData) -> None:
        """
        Add sprint data for analysis.

        Args:
            sprint: Sprint data to add
        """
        self.sprints.append(sprint)
        logger.info(
            f"Added sprint: {sprint.sprint_name} "
            f"({sprint.committed_points} committed, "
            f"{sprint.completed_points} completed)"
        )

    def load_sprints_from_dict(
        self, sprints_data: List[Dict[str, Any]]
    ) -> None:
        """
        Load sprint data from dictionary list.

        Args:
            sprints_data: List of sprint dictionaries
        """
        for sprint_dict in sprints_data:
            sprint = SprintData(**sprint_dict)
            self.add_sprint(sprint)

    def load_sprints_from_json(self, json_path: Path) -> None:
        """
        Load sprint data from JSON file.

        Args:
            json_path: Path to JSON file
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.load_sprints_from_dict(data)

    def calculate_velocity(
        self, num_sprints: Optional[int] = None
    ) -> VelocityMetrics:
        """
        Calculate velocity metrics over recent sprints.

        Args:
            num_sprints: Number of recent sprints to analyze (default: config)

        Returns:
            VelocityMetrics with statistical analysis

        Raises:
            ValueError: If no sprint data available
        """
        if not self.sprints:
            raise ValueError("No sprint data available")

        num_sprints = num_sprints or self.config.velocity_window
        recent_sprints = sorted(self.sprints, key=lambda s: s.start_date)[
            -num_sprints:
        ]

        velocities = [s.completed_points for s in recent_sprints]

        # Statistical calculations
        mean_vel = float(np.mean(velocities))
        median_vel = float(np.median(velocities))
        std_dev = float(np.std(velocities))
        min_vel = float(np.min(velocities))
        max_vel = float(np.max(velocities))

        # Trend analysis using linear regression
        if len(velocities) >= 2:
            x = np.arange(len(velocities)).reshape(-1, 1)
            y = np.array(velocities)
            slope = float(np.polyfit(x.flatten(), y, 1)[0])

            # Determine trend
            if abs(slope) < std_dev * 0.1:
                trend = "STABLE"
                trend_pct = 0.0
            elif slope > 0:
                trend = "INCREASING"
                trend_pct = (slope / mean_vel) * 100
            else:
                trend = "DECREASING"
                trend_pct = (slope / mean_vel) * 100
        else:
            trend = "STABLE"
            trend_pct = 0.0

        return VelocityMetrics(
            mean_velocity=mean_vel,
            median_velocity=median_vel,
            std_dev=std_dev,
            min_velocity=min_vel,
            max_velocity=max_vel,
            velocity_trend=trend,
            trend_percentage=trend_pct,
            sprints_analyzed=len(recent_sprints),
            velocity_history=velocities,
        )

    def calculate_cycle_time(
        self, sprint_id: Optional[str] = None
    ) -> CycleTimeMetrics:
        """
        Calculate cycle time and lead time metrics.

        Cycle time: Time from work started to completion
        Lead time: Time from issue creation to completion

        Args:
            sprint_id: Specific sprint to analyze (default: all sprints)

        Returns:
            CycleTimeMetrics with timing analysis
        """
        issues = []
        if sprint_id:
            sprint = next(
                (s for s in self.sprints if s.sprint_id == sprint_id), None
            )
            if sprint:
                issues = sprint.issues
        else:
            for sprint in self.sprints:
                issues.extend(sprint.issues)

        completed_issues = [i for i in issues if i.completed_date is not None]

        if not completed_issues:
            return CycleTimeMetrics(
                avg_cycle_time_days=0.0,
                median_cycle_time_days=0.0,
                avg_lead_time_days=0.0,
                median_lead_time_days=0.0,
                p50_cycle_time=0.0,
                p75_cycle_time=0.0,
                p90_cycle_time=0.0,
                issues_analyzed=0,
            )

        # Calculate cycle times (simplified: using created_date as start)
        cycle_times = [
            (issue.completed_date - issue.created_date).days  # type: ignore
            for issue in completed_issues
        ]

        # Lead time is same as cycle time in this simplified model
        lead_times = cycle_times

        return CycleTimeMetrics(
            avg_cycle_time_days=float(np.mean(cycle_times)),
            median_cycle_time_days=float(np.median(cycle_times)),
            avg_lead_time_days=float(np.mean(lead_times)),
            median_lead_time_days=float(np.median(lead_times)),
            p50_cycle_time=float(np.percentile(cycle_times, 50)),
            p75_cycle_time=float(np.percentile(cycle_times, 75)),
            p90_cycle_time=float(np.percentile(cycle_times, 90)),
            issues_analyzed=len(completed_issues),
        )

    def calculate_predictability(
        self, num_sprints: Optional[int] = None
    ) -> PredictabilityMetrics:
        """
        Analyze sprint predictability and consistency.

        Args:
            num_sprints: Number of recent sprints to analyze

        Returns:
            PredictabilityMetrics with consistency analysis
        """
        num_sprints = num_sprints or self.config.velocity_window
        recent_sprints = sorted(self.sprints, key=lambda s: s.start_date)[
            -num_sprints:
        ]

        if not recent_sprints:
            return PredictabilityMetrics(
                commitment_accuracy=0.0,
                velocity_variance=0.0,
                consistency_score=0.0,
                prediction_confidence=0.0,
                risk_level="HIGH",
            )

        # Commitment accuracy
        accuracies = []
        for sprint in recent_sprints:
            if sprint.committed_points > 0:
                accuracy = (
                    sprint.completed_points / sprint.committed_points
                ) * 100
                accuracies.append(min(accuracy, 100.0))

        avg_accuracy = float(np.mean(accuracies)) if accuracies else 0.0

        # Velocity variance
        velocities = [s.completed_points for s in recent_sprints]
        velocity_var = float(np.var(velocities))

        # Consistency score (0-100, higher is better)
        # Based on coefficient of variation (lower CV = higher consistency)
        mean_vel = float(np.mean(velocities))
        if mean_vel > 0:
            cv = float(np.std(velocities)) / mean_vel
            consistency = max(0.0, 100.0 - (cv * 100))
        else:
            consistency = 0.0

        # Prediction confidence
        confidence = (avg_accuracy + consistency) / 2

        # Risk level
        if consistency >= 70 and avg_accuracy >= 80:
            risk = "LOW"
        elif consistency >= 50 and avg_accuracy >= 60:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        return PredictabilityMetrics(
            commitment_accuracy=avg_accuracy,
            velocity_variance=velocity_var,
            consistency_score=consistency,
            prediction_confidence=confidence / 100,
            risk_level=risk,
        )

    def forecast_release(
        self, target_points: float, num_sprints: Optional[int] = None
    ) -> ReleaseForecast:
        """
        Forecast release completion based on historical velocity.

        Args:
            target_points: Total story points to complete
            num_sprints: Number of sprints for velocity calculation

        Returns:
            ReleaseForecast with completion estimates
        """
        velocity_metrics = self.calculate_velocity(num_sprints)

        # Calculate sprints needed
        estimated_sprints = int(
            np.ceil(target_points / velocity_metrics.mean_velocity)
        )

        # Confidence intervals using std dev
        z_score = 1.96  # 95% confidence
        sprints_count = velocity_metrics.sprints_analyzed
        margin = z_score * (velocity_metrics.std_dev / np.sqrt(sprints_count))

        lower_velocity = max(1.0, velocity_metrics.mean_velocity - margin)
        upper_velocity = velocity_metrics.mean_velocity + margin

        ci_low = int(np.ceil(target_points / upper_velocity))
        ci_high = int(np.ceil(target_points / lower_velocity))

        # Estimate completion date (assuming 2-week sprints)
        last_sprint = sorted(self.sprints, key=lambda s: s.end_date)[-1]
        sprint_duration = (last_sprint.end_date - last_sprint.start_date).days
        estimated_date = last_sprint.end_date + timedelta(
            days=estimated_sprints * sprint_duration
        )

        # Completion probability based on consistency
        predictability = self.calculate_predictability(num_sprints)
        completion_prob = predictability.prediction_confidence

        return ReleaseForecast(
            target_points=target_points,
            estimated_sprints=estimated_sprints,
            estimated_completion_date=estimated_date,
            confidence_interval_low=ci_low,
            confidence_interval_high=ci_high,
            completion_probability=completion_prob,
            based_on_sprints=velocity_metrics.sprints_analyzed,
        )

    def generate_burndown_chart(
        self, sprint_id: str, output_filename: Optional[str] = None
    ) -> Path:
        """
        Generate burndown chart for a specific sprint.

        Args:
            sprint_id: Sprint identifier
            output_filename: Custom output filename

        Returns:
            Path to generated chart

        Raises:
            ValueError: If sprint not found
        """
        sprint = next(
            (s for s in self.sprints if s.sprint_id == sprint_id), None
        )
        if not sprint:
            raise ValueError(f"Sprint {sprint_id} not found")

        # Create burndown data
        total_days = (sprint.end_date - sprint.start_date).days
        dates = [
            sprint.start_date + timedelta(days=i)
            for i in range(total_days + 1)
        ]

        # Filter out weekends if configured
        if not self.config.include_weekends:
            dates = [d for d in dates if d.weekday() < 5]

        # Ideal burndown
        ideal_remaining = np.linspace(sprint.committed_points, 0, len(dates))

        # Actual burndown (simulated based on completed points)
        completed_by_end = sprint.completed_points
        actual_remaining = np.linspace(
            sprint.committed_points,
            sprint.committed_points - completed_by_end,
            len(dates),
        )

        # Create figure
        fig, ax = plt.subplots(figsize=self.config.figsize)

        ax.plot(
            dates,
            ideal_remaining,
            label="Ideal Burndown",
            linestyle="--",
            linewidth=2,
            color="green",
        )
        ax.plot(
            dates,
            actual_remaining,
            label="Actual Burndown",
            linewidth=2,
            color="blue",
            marker="o",
            markersize=4,
        )

        ax.fill_between(dates, 0, actual_remaining, alpha=0.2, color="blue")

        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Story Points Remaining", fontsize=12)
        ax.set_title(
            f"Sprint Burndown Chart - {sprint.sprint_name}",
            fontsize=14,
            fontweight="bold",
        )
        ax.legend(loc="upper right")
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        # Save chart
        if not output_filename:
            output_filename = (
                f"burndown_{sprint.sprint_id}.{self.config.chart_format}"
            )
        output_path = self.config.output_dir / output_filename
        plt.savefig(output_path, dpi=self.config.dpi, bbox_inches="tight")
        plt.close()

        logger.info(f"Burndown chart saved: {output_path}")
        return output_path

    def generate_burnup_chart(
        self, sprint_id: str, output_filename: Optional[str] = None
    ) -> Path:
        """
        Generate burnup chart for a specific sprint.

        Args:
            sprint_id: Sprint identifier
            output_filename: Custom output filename

        Returns:
            Path to generated chart
        """
        sprint = next(
            (s for s in self.sprints if s.sprint_id == sprint_id), None
        )
        if not sprint:
            raise ValueError(f"Sprint {sprint_id} not found")

        # Create burnup data
        total_days = (sprint.end_date - sprint.start_date).days
        dates = [
            sprint.start_date + timedelta(days=i)
            for i in range(total_days + 1)
        ]

        if not self.config.include_weekends:
            dates = [d for d in dates if d.weekday() < 5]

        # Scope line (committed points)
        scope = np.full(len(dates), sprint.committed_points)

        # Work completed (simulated)
        completed = np.linspace(0, sprint.completed_points, len(dates))

        # Ideal completion
        ideal_completed = np.linspace(0, sprint.committed_points, len(dates))

        # Create figure
        fig, ax = plt.subplots(figsize=self.config.figsize)

        ax.plot(
            dates,
            scope,
            label="Sprint Scope",
            linestyle="-",
            linewidth=2,
            color="red",
        )
        ax.plot(
            dates,
            ideal_completed,
            label="Ideal Progress",
            linestyle="--",
            linewidth=2,
            color="green",
        )
        ax.plot(
            dates,
            completed,
            label="Actual Progress",
            linewidth=2,
            color="blue",
            marker="o",
            markersize=4,
        )

        ax.fill_between(dates, 0, completed, alpha=0.2, color="blue")

        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Story Points Completed", fontsize=12)
        ax.set_title(
            f"Sprint Burnup Chart - {sprint.sprint_name}",
            fontsize=14,
            fontweight="bold",
        )
        ax.legend(loc="lower right")
        ax.grid(True, alpha=0.3)
        ax.set_ylim(bottom=0)

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        # Save chart
        if not output_filename:
            output_filename = (
                f"burnup_{sprint.sprint_id}.{self.config.chart_format}"
            )
        output_path = self.config.output_dir / output_filename
        plt.savefig(output_path, dpi=self.config.dpi, bbox_inches="tight")
        plt.close()

        logger.info(f"Burnup chart saved: {output_path}")
        return output_path

    def generate_velocity_chart(
        self,
        num_sprints: Optional[int] = None,
        output_filename: Optional[str] = None,
    ) -> Path:
        """
        Generate velocity trend chart.

        Args:
            num_sprints: Number of recent sprints to include
            output_filename: Custom output filename

        Returns:
            Path to generated chart
        """
        num_sprints = num_sprints or len(self.sprints)
        recent_sprints = sorted(self.sprints, key=lambda s: s.start_date)[
            -num_sprints:
        ]

        sprint_names = [s.sprint_name for s in recent_sprints]
        committed = [s.committed_points for s in recent_sprints]
        completed = [s.completed_points for s in recent_sprints]

        velocity_metrics = self.calculate_velocity(num_sprints)

        # Create figure
        fig, ax = plt.subplots(figsize=self.config.figsize)

        x = np.arange(len(sprint_names))
        width = 0.35

        ax.bar(
            x - width / 2,
            committed,
            width,
            label="Committed",
            color="lightblue",
        )
        ax.bar(
            x + width / 2,
            completed,
            width,
            label="Completed",
            color="darkblue",
        )

        # Add average line
        ax.axhline(
            y=velocity_metrics.mean_velocity,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Average ({velocity_metrics.mean_velocity:.1f})",
        )

        ax.set_xlabel("Sprint", fontsize=12)
        ax.set_ylabel("Story Points", fontsize=12)
        ax.set_title("Velocity Trend Analysis", fontsize=14, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(sprint_names, rotation=45, ha="right")
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")

        plt.tight_layout()

        # Save chart
        if not output_filename:
            output_filename = f"velocity_trend.{self.config.chart_format}"
        output_path = self.config.output_dir / output_filename
        plt.savefig(output_path, dpi=self.config.dpi, bbox_inches="tight")
        plt.close()

        logger.info(f"Velocity chart saved: {output_path}")
        return output_path

    def generate_cycle_time_chart(
        self, output_filename: Optional[str] = None
    ) -> Path:
        """
        Generate cycle time distribution chart.

        Args:
            output_filename: Custom output filename

        Returns:
            Path to generated chart
        """
        all_issues = []
        for sprint in self.sprints:
            all_issues.extend(sprint.issues)

        completed_issues = [
            i for i in all_issues if i.completed_date is not None
        ]
        cycle_times = [
            (issue.completed_date - issue.created_date).days  # type: ignore
            for issue in completed_issues
        ]

        if not cycle_times:
            raise ValueError("No completed issues for cycle time analysis")

        metrics = self.calculate_cycle_time()

        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Histogram
        ax1.hist(
            cycle_times, bins=20, color="skyblue", edgecolor="black", alpha=0.7
        )
        ax1.axvline(
            metrics.avg_cycle_time_days,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Mean ({metrics.avg_cycle_time_days:.1f} days)",
        )
        ax1.axvline(
            metrics.median_cycle_time_days,
            color="green",
            linestyle="--",
            linewidth=2,
            label=f"Median ({metrics.median_cycle_time_days:.1f} days)",
        )
        ax1.set_xlabel("Cycle Time (days)", fontsize=12)
        ax1.set_ylabel("Frequency", fontsize=12)
        ax1.set_title(
            "Cycle Time Distribution", fontsize=14, fontweight="bold"
        )
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Box plot
        ax2.boxplot([cycle_times], labels=["Cycle Time"])
        ax2.set_ylabel("Days", fontsize=12)
        ax2.set_title("Cycle Time Box Plot", fontsize=14, fontweight="bold")
        ax2.grid(True, alpha=0.3, axis="y")

        # Add percentile annotations
        ax2.text(
            1.15,
            metrics.p50_cycle_time,
            f"P50: {metrics.p50_cycle_time:.1f}",
            fontsize=10,
        )
        ax2.text(
            1.15,
            metrics.p75_cycle_time,
            f"P75: {metrics.p75_cycle_time:.1f}",
            fontsize=10,
        )
        ax2.text(
            1.15,
            metrics.p90_cycle_time,
            f"P90: {metrics.p90_cycle_time:.1f}",
            fontsize=10,
        )

        plt.tight_layout()

        # Save chart
        if not output_filename:
            output_filename = (
                f"cycle_time_distribution.{self.config.chart_format}"
            )
        output_path = self.config.output_dir / output_filename
        plt.savefig(output_path, dpi=self.config.dpi, bbox_inches="tight")
        plt.close()

        logger.info(f"Cycle time chart saved: {output_path}")
        return output_path

    def export_to_csv(self, output_filename: Optional[str] = None) -> Path:
        """
        Export sprint data to CSV.

        Args:
            output_filename: Custom output filename

        Returns:
            Path to CSV file
        """
        if not self.sprints:
            raise ValueError("No sprint data to export")

        data = []
        for sprint in self.sprints:
            data.append(
                {
                    "sprint_id": sprint.sprint_id,
                    "sprint_name": sprint.sprint_name,
                    "start_date": sprint.start_date.isoformat(),
                    "end_date": sprint.end_date.isoformat(),
                    "committed_points": sprint.committed_points,
                    "completed_points": sprint.completed_points,
                    "team_capacity": sprint.team_capacity,
                    "num_issues": len(sprint.issues),
                }
            )

        df = pd.DataFrame(data)

        if not output_filename:
            output_filename = "sprint_data.csv"
        output_path = self.config.output_dir / output_filename

        df.to_csv(output_path, index=False)
        logger.info(f"Sprint data exported to CSV: {output_path}")
        return output_path

    def export_to_json(self, output_filename: Optional[str] = None) -> Path:
        """
        Export comprehensive analytics to JSON.

        Args:
            output_filename: Custom output filename

        Returns:
            Path to JSON file
        """
        velocity = self.calculate_velocity()
        cycle_time = self.calculate_cycle_time()
        predictability = self.calculate_predictability()

        report = {
            "generated_at": datetime.now().isoformat(),
            "total_sprints": len(self.sprints),
            "velocity_metrics": velocity.model_dump(),
            "cycle_time_metrics": cycle_time.model_dump(),
            "predictability_metrics": predictability.model_dump(),
            "sprints": [
                {
                    "sprint_id": s.sprint_id,
                    "sprint_name": s.sprint_name,
                    "start_date": s.start_date.isoformat(),
                    "end_date": s.end_date.isoformat(),
                    "committed_points": s.committed_points,
                    "completed_points": s.completed_points,
                    "completion_rate": (
                        (s.completed_points / s.committed_points * 100)
                        if s.committed_points > 0
                        else 0
                    ),
                }
                for s in sorted(self.sprints, key=lambda x: x.start_date)
            ],
        }

        if not output_filename:
            output_filename = "sprint_analytics_report.json"
        output_path = self.config.output_dir / output_filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Analytics report exported to JSON: {output_path}")
        return output_path

    def generate_comprehensive_report(
        self, sprint_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report.

        Args:
            sprint_id: Specific sprint to analyze (default: all sprints)

        Returns:
            Complete analytics report dictionary
        """
        velocity = self.calculate_velocity()
        cycle_time = self.calculate_cycle_time(sprint_id)
        predictability = self.calculate_predictability()

        total_committed = sum(s.committed_points for s in self.sprints)
        total_completed = sum(s.completed_points for s in self.sprints)

        report = {
            "summary": {
                "total_sprints": len(self.sprints),
                "total_committed_points": total_committed,
                "total_completed_points": total_completed,
                "overall_completion_rate": (
                    total_completed / total_committed * 100
                    if total_committed > 0
                    else 0
                ),
            },
            "velocity_analysis": velocity.model_dump(),
            "cycle_time_analysis": cycle_time.model_dump(),
            "predictability_analysis": predictability.model_dump(),
            "recommendations": self._generate_recommendations(
                velocity, predictability
            ),
        }

        logger.info("Comprehensive report generated")
        return report

    def _generate_recommendations(
        self, velocity: VelocityMetrics, predictability: PredictabilityMetrics
    ) -> List[str]:
        """
        Generate actionable recommendations based on metrics.

        Args:
            velocity: Velocity metrics
            predictability: Predictability metrics

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Velocity recommendations
        if velocity.velocity_trend == "DECREASING":
            recommendations.append(
                "VELOCITY TREND: Velocity is decreasing. "
                "Consider investigating team capacity, technical debt, "
                "or estimation accuracy."
            )
        elif velocity.velocity_trend == "INCREASING":
            recommendations.append(
                "VELOCITY TREND: Positive velocity trend detected. "
                "Team performance is improving."
            )

        # Predictability recommendations
        if predictability.commitment_accuracy < 70:
            recommendations.append(
                "COMMITMENT ACCURACY: Low commitment accuracy detected. "
                "Consider improving estimation practices or reducing "
                "sprint scope changes."
            )

        if predictability.consistency_score < 60:
            recommendations.append(
                "CONSISTENCY: High velocity variance detected. "
                "Work on stabilizing sprint planning and reducing "
                "unexpected work items."
            )

        if predictability.risk_level == "HIGH":
            recommendations.append(
                "RISK LEVEL: High risk detected. "
                "Focus on improving sprint predictability through better "
                "planning and scope management."
            )

        # Positive feedback
        if (
            predictability.consistency_score >= 70
            and predictability.commitment_accuracy >= 80
        ):
            recommendations.append(
                "TEAM PERFORMANCE: Excellent sprint consistency and "
                "commitment accuracy. Maintain current practices."
            )

        return recommendations
