"""
ML-based cost anomaly detection system for FinOps platform.

This module provides sophisticated anomaly detection using Isolation Forest algorithm,
with support for root cause analysis, severity classification, and actionable insights.

Protocol Coverage:
- P-FINOPS-COST-MONITOR: Continuous cost monitoring with anomaly detection
- P-OBSERVABILITY: Cost metrics export and alerting

Author: devCrew_s1
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, field_validator
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from .cost_aggregator import CostData

logger = logging.getLogger(__name__)


class AnomalyConfig(BaseModel):
    """Configuration for anomaly detection."""

    sensitivity: float = Field(default=0.95, ge=0.0, le=1.0)
    contamination: float = Field(default=0.1, ge=0.0, le=0.5)
    window_days: int = Field(default=30, ge=7)
    min_observations: int = Field(default=7, ge=3)
    use_scaling: bool = True
    detect_spikes: bool = True
    detect_drift: bool = True
    min_cost_threshold: float = Field(default=1.0, ge=0.0)
    historical_comparison: bool = True
    n_estimators: int = Field(default=100, ge=10)
    random_state: int = 42


class AnomalySeverity(str):
    """Severity levels for cost anomalies."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Anomaly(BaseModel):
    """Individual cost anomaly record."""

    date: datetime
    provider: str
    service: str
    cost: float
    expected_cost: float
    variance_percent: float
    anomaly_score: float = Field(ge=-1.0, le=1.0)
    severity: str
    root_cause: Optional[str] = None
    affected_resources: List[str] = Field(default_factory=list)
    contributing_factors: Dict[str, Any] = Field(default_factory=dict)
    region: Optional[str] = None
    usage_type: Optional[str] = None

    @field_validator("variance_percent")
    @classmethod
    def round_variance(cls, v: float) -> float:
        """Round variance to 2 decimal places."""
        return round(v, 2)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class AnomalyReport(BaseModel):
    """Aggregated anomaly detection report."""

    detection_date: datetime
    period_start: datetime
    period_end: datetime
    total_anomalies: int
    anomalies: List[Anomaly]
    summary: Dict[str, Any]
    recommendations: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnomalyDetector:
    """
    ML-based cost anomaly detection system.

    Uses Isolation Forest algorithm for unsupervised anomaly detection
    with statistical analysis for severity classification and root cause analysis.
    """

    def __init__(self, config: Optional[AnomalyConfig] = None):
        """
        Initialize anomaly detector.

        Args:
            config: Optional configuration settings
        """
        self.config = config or AnomalyConfig()
        self._model: Optional[IsolationForest] = None
        self._scaler: Optional[StandardScaler] = None
        self._trained: bool = False

        logger.info(
            f"Initialized AnomalyDetector with sensitivity="
            f"{self.config.sensitivity}"
        )

    def detect(
        self, cost_data: List[CostData], training_days: Optional[int] = None
    ) -> List[Anomaly]:
        """
        Detect cost anomalies in provided data.

        Args:
            cost_data: List of cost data records to analyze
            training_days: Optional number of days for training data

        Returns:
            List of detected anomalies
        """
        if not cost_data:
            logger.warning("No cost data provided for anomaly detection")
            return []

        if len(cost_data) < self.config.min_observations:
            logger.warning(
                f"Insufficient data: {len(cost_data)} records "
                f"(minimum: {self.config.min_observations})"
            )
            return []

        # Convert to DataFrame for analysis
        df = self._prepare_dataframe(cost_data)

        # Split into training and detection datasets
        training_df, detection_df = self._split_data(df, training_days)

        # Train model on historical data
        if not self._trained or training_days is not None:
            self._train_model(training_df)

        # Detect anomalies
        anomalies = self._detect_anomalies(detection_df, training_df)

        logger.info(f"Detected {len(anomalies)} anomalies")
        return anomalies

    def _prepare_dataframe(self, cost_data: List[CostData]) -> pd.DataFrame:
        """
        Convert cost data to pandas DataFrame with feature engineering.

        Args:
            cost_data: List of cost data records

        Returns:
            DataFrame with engineered features
        """
        # Convert to DataFrame
        data = []
        for record in cost_data:
            data.append(
                {
                    "date": record.date,
                    "provider": record.provider.value,
                    "service": record.service,
                    "cost": record.cost,
                    "region": record.region or "unknown",
                    "usage_type": record.usage_type or "unknown",
                    "resource_id": record.resource_id or "unknown",
                }
            )

        df = pd.DataFrame(data)

        # Ensure date is datetime
        df["date"] = pd.to_datetime(df["date"])

        # Sort by date
        df = df.sort_values("date")

        # Add time-based features
        df["day_of_week"] = df["date"].dt.dayofweek
        df["day_of_month"] = df["date"].dt.day
        df["month"] = df["date"].dt.month
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

        # Add rolling statistics per service
        for service in df["service"].unique():
            mask = df["service"] == service
            df.loc[mask, "rolling_mean_7d"] = (
                df.loc[mask, "cost"].rolling(window=7, min_periods=1).mean()
            )
            df.loc[mask, "rolling_std_7d"] = (
                df.loc[mask, "cost"].rolling(window=7, min_periods=1).std()
            )

        # Fill NaN values
        df["rolling_std_7d"].fillna(0, inplace=True)

        return df

    def _split_data(
        self, df: pd.DataFrame, training_days: Optional[int] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into training and detection sets.

        Args:
            df: Full dataset
            training_days: Optional number of days for training

        Returns:
            Tuple of (training_df, detection_df)
        """
        if training_days is None:
            training_days = self.config.window_days

        # Get date range
        max_date = df["date"].max()
        split_date = max_date - timedelta(days=training_days)

        # Split data
        training_df = df[df["date"] <= split_date].copy()
        detection_df = df[df["date"] > split_date].copy()

        # If not enough training data, use all data for training
        if len(training_df) < self.config.min_observations:
            logger.warning(
                "Insufficient training data, using full dataset for training"
            )
            training_df = df.copy()
            detection_df = df.copy()

        return training_df, detection_df

    def _train_model(self, training_df: pd.DataFrame) -> IsolationForest:
        """
        Train Isolation Forest model on historical data.

        Args:
            training_df: Training dataset

        Returns:
            Trained IsolationForest model
        """
        if len(training_df) < self.config.min_observations:
            logger.warning(f"Insufficient training data: {len(training_df)} records")
            # Create a dummy model
            self._model = IsolationForest(
                contamination=self.config.contamination,
                n_estimators=self.config.n_estimators,
                random_state=self.config.random_state,
            )
            self._trained = False
            return self._model

        # Select features for training
        feature_cols = ["cost", "day_of_week", "day_of_month", "is_weekend"]

        # Add rolling features if available
        if "rolling_mean_7d" in training_df.columns:
            feature_cols.extend(["rolling_mean_7d", "rolling_std_7d"])

        # Filter out low-cost records for training
        training_data = training_df[
            training_df["cost"] >= self.config.min_cost_threshold
        ].copy()

        if len(training_data) < self.config.min_observations:
            logger.warning("Insufficient high-cost records for training")
            training_data = training_df.copy()

        # Extract features
        X_train = training_data[feature_cols].values

        # Handle missing values
        X_train = np.nan_to_num(X_train, nan=0.0)

        # Scale features
        if self.config.use_scaling:
            self._scaler = StandardScaler()
            X_train = self._scaler.fit_transform(X_train)

        # Train model
        self._model = IsolationForest(
            contamination=self.config.contamination,
            n_estimators=self.config.n_estimators,
            random_state=self.config.random_state,
        )

        self._model.fit(X_train)
        self._trained = True

        logger.info(f"Trained Isolation Forest on {len(training_data)} records")
        return self._model

    def _detect_anomalies(
        self, detection_df: pd.DataFrame, training_df: pd.DataFrame
    ) -> List[Anomaly]:
        """
        Detect anomalies in detection dataset.

        Args:
            detection_df: Dataset to check for anomalies
            training_df: Historical training data

        Returns:
            List of detected anomalies
        """
        if not self._trained or self._model is None:
            logger.warning("Model not trained, cannot detect anomalies")
            return []

        anomalies: List[Anomaly] = []

        # Group by service and provider for per-service analysis
        for (provider, service), group in detection_df.groupby(["provider", "service"]):
            # Skip low-cost services
            if group["cost"].sum() < self.config.min_cost_threshold * 7:
                continue

            # Get historical data for this service
            historical = training_df[
                (training_df["provider"] == provider)
                & (training_df["service"] == service)
            ]

            if len(historical) < self.config.min_observations:
                continue

            # Calculate expected costs
            historical_mean = historical["cost"].mean()
            historical_std = historical["cost"].std()

            # Detect anomalies for each record
            for _, row in group.iterrows():
                cost = row["cost"]

                # Skip low costs
                if cost < self.config.min_cost_threshold:
                    continue

                # Calculate expected cost
                expected_cost = self._calculate_expected_cost(row["date"], historical)

                # Calculate variance
                if expected_cost > 0:
                    variance_percent = (cost - expected_cost) / expected_cost * 100
                else:
                    variance_percent = 0

                # Check if anomaly using statistical method
                is_anomaly_stat = False
                if historical_std > 0:
                    z_score = abs((cost - historical_mean) / historical_std)
                    threshold = 2.0 * (1 / self.config.sensitivity)
                    is_anomaly_stat = z_score > threshold

                # Check using ML model
                is_anomaly_ml = False
                anomaly_score = 0.0

                if self._model is not None:
                    # Prepare features
                    features = [
                        cost,
                        row["day_of_week"],
                        row["day_of_month"],
                        row["is_weekend"],
                    ]

                    if "rolling_mean_7d" in row.index:
                        features.extend([row["rolling_mean_7d"], row["rolling_std_7d"]])

                    X = np.array(features).reshape(1, -1)

                    # Handle missing values
                    X = np.nan_to_num(X, nan=0.0)

                    # Scale if needed
                    if self.config.use_scaling and self._scaler is not None:
                        X = self._scaler.transform(X)

                    # Predict
                    prediction = self._model.predict(X)[0]
                    anomaly_score = self._model.score_samples(X)[0]

                    is_anomaly_ml = prediction == -1

                # Combine detection methods
                is_anomaly = is_anomaly_stat or is_anomaly_ml

                # Additional checks
                if self.config.detect_spikes:
                    # Detect sudden spikes (>50% increase)
                    if variance_percent > 50:
                        is_anomaly = True

                if self.config.detect_drift:
                    # Detect sustained drift from baseline
                    if abs(variance_percent) > 30:
                        is_anomaly = True

                # Create anomaly record if detected
                if is_anomaly:
                    severity = self._determine_severity(variance_percent)

                    # Analyze root cause
                    root_cause = self._analyze_root_cause(row, group, historical)

                    # Identify affected resources
                    affected_resources = self._identify_affected_resources(row, group)

                    # Calculate contributing factors
                    contributing_factors = self._calculate_contributing_factors(
                        row, group, historical
                    )

                    anomaly = Anomaly(
                        date=row["date"],
                        provider=provider,
                        service=service,
                        cost=cost,
                        expected_cost=expected_cost,
                        variance_percent=variance_percent,
                        anomaly_score=float(anomaly_score),
                        severity=severity,
                        root_cause=root_cause,
                        affected_resources=affected_resources,
                        contributing_factors=contributing_factors,
                        region=row.get("region"),
                        usage_type=row.get("usage_type"),
                    )

                    anomalies.append(anomaly)

        return anomalies

    def _calculate_expected_cost(
        self, date: datetime, historical: pd.DataFrame
    ) -> float:
        """
        Calculate expected cost based on historical patterns.

        Args:
            date: Date to calculate expected cost for
            historical: Historical data

        Returns:
            Expected cost value
        """
        if len(historical) == 0:
            return 0.0

        # Get same day of week historical data
        day_of_week = date.weekday()
        same_day = historical[historical["day_of_week"] == day_of_week]

        if len(same_day) >= 3:
            # Use median of same day of week
            return float(same_day["cost"].median())
        else:
            # Use overall median
            return float(historical["cost"].median())

    def _determine_severity(self, variance_percent: float) -> str:
        """
        Determine anomaly severity based on variance.

        Args:
            variance_percent: Percentage variance from expected

        Returns:
            Severity level (LOW, MEDIUM, HIGH, CRITICAL)
        """
        abs_variance = abs(variance_percent)

        if abs_variance >= 100:
            return AnomalySeverity.CRITICAL
        elif abs_variance >= 50:
            return AnomalySeverity.HIGH
        elif abs_variance >= 20:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW

    def _analyze_root_cause(
        self,
        row: pd.Series,
        group: pd.DataFrame,
        historical: pd.DataFrame,
    ) -> str:
        """
        Analyze potential root cause of anomaly.

        Args:
            row: Anomalous record
            group: Group data for same service/provider
            historical: Historical data

        Returns:
            Root cause description
        """
        causes: List[str] = []

        cost = row["cost"]
        expected = self._calculate_expected_cost(row["date"], historical)
        variance_pct = ((cost - expected) / expected * 100) if expected > 0 else 0

        # Check for sudden spike
        if variance_pct > 100:
            causes.append(f"Sudden cost spike of {variance_pct:.1f}% from baseline")

        # Check for new resources
        if row["resource_id"] != "unknown":
            resource_costs = group[group["resource_id"] == row["resource_id"]]
            if len(resource_costs) == 1:
                causes.append(f"New resource detected: {row['resource_id']}")

        # Check for usage type changes
        if row["usage_type"] != "unknown":
            usage_costs = historical[historical["usage_type"] == row["usage_type"]]
            if len(usage_costs) < 3:
                causes.append(f"Unusual usage type: {row['usage_type']}")

        # Check for regional anomalies
        if row["region"] != "unknown":
            regional_avg = group[group["region"] == row["region"]]["cost"].mean()
            overall_avg = group["cost"].mean()
            if regional_avg > overall_avg * 1.5:
                causes.append(f"Higher costs in region: {row['region']}")

        # Check for sustained increase
        recent_costs = group.tail(7)["cost"].mean()
        historical_avg = historical["cost"].mean()
        if recent_costs > historical_avg * 1.3:
            causes.append("Sustained cost increase over past 7 days")

        if causes:
            return "; ".join(causes)
        else:
            return "Anomalous cost pattern detected"

    def _identify_affected_resources(
        self, row: pd.Series, group: pd.DataFrame
    ) -> List[str]:
        """
        Identify resources contributing to anomaly.

        Args:
            row: Anomalous record
            group: Group data for same service/provider

        Returns:
            List of affected resource identifiers
        """
        resources: List[str] = []

        # Add primary resource if available
        if row["resource_id"] != "unknown":
            resources.append(row["resource_id"])

        # Find other high-cost resources on same date
        same_date = group[group["date"] == row["date"]]
        if len(same_date) > 1:
            # Get top 3 resources by cost
            top_resources = (
                same_date.nlargest(3, "cost")["resource_id"].unique().tolist()
            )
            resources.extend(
                [r for r in top_resources if r != "unknown" and r not in resources]
            )

        return resources[:5]  # Limit to top 5

    def _calculate_contributing_factors(
        self,
        row: pd.Series,
        group: pd.DataFrame,
        historical: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Calculate factors contributing to anomaly.

        Args:
            row: Anomalous record
            group: Group data for same service/provider
            historical: Historical data

        Returns:
            Dictionary of contributing factors
        """
        factors: Dict[str, Any] = {}

        # Cost metrics
        factors["current_cost"] = round(float(row["cost"]), 2)
        factors["historical_avg"] = round(float(historical["cost"].mean()), 2)
        factors["historical_max"] = round(float(historical["cost"].max()), 2)

        # Time-based factors
        factors["day_of_week"] = row["date"].strftime("%A")
        factors["is_weekend"] = bool(row["is_weekend"])

        # Recent trend
        recent = group.tail(7)
        if len(recent) > 1:
            trend_change = (
                (recent["cost"].iloc[-1] - recent["cost"].iloc[0])
                / recent["cost"].iloc[0]
                * 100
                if recent["cost"].iloc[0] > 0
                else 0
            )
            factors["7day_trend"] = f"{trend_change:+.1f}%"

        # Usage patterns
        if row["usage_type"] != "unknown":
            factors["usage_type"] = row["usage_type"]

        if row["region"] != "unknown":
            factors["region"] = row["region"]

        return factors

    def get_anomaly_report(
        self,
        anomalies: List[Anomaly],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> AnomalyReport:
        """
        Generate comprehensive anomaly report.

        Args:
            anomalies: List of detected anomalies
            start_date: Optional period start date
            end_date: Optional period end date

        Returns:
            Structured anomaly report
        """
        if not anomalies:
            return AnomalyReport(
                detection_date=datetime.now(),
                period_start=start_date or datetime.now(),
                period_end=end_date or datetime.now(),
                total_anomalies=0,
                anomalies=[],
                summary={},
                recommendations=[],
            )

        # Calculate summary statistics
        total_anomalies = len(anomalies)
        total_excess_cost = sum(max(0, a.cost - a.expected_cost) for a in anomalies)

        # Group by severity
        by_severity: Dict[str, int] = {}
        for anomaly in anomalies:
            severity = anomaly.severity
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # Group by provider
        by_provider: Dict[str, int] = {}
        for anomaly in anomalies:
            provider = anomaly.provider
            by_provider[provider] = by_provider.get(provider, 0) + 1

        # Group by service
        by_service: Dict[str, int] = {}
        service_costs: Dict[str, float] = {}
        for anomaly in anomalies:
            service = anomaly.service
            by_service[service] = by_service.get(service, 0) + 1
            excess = max(0, anomaly.cost - anomaly.expected_cost)
            service_costs[service] = service_costs.get(service, 0) + excess

        # Top anomalies by cost impact
        top_anomalies = sorted(
            anomalies,
            key=lambda a: a.cost - a.expected_cost,
            reverse=True,
        )[:10]

        # Generate recommendations
        recommendations = self._generate_recommendations(
            anomalies, by_severity, service_costs
        )

        # Build summary
        summary = {
            "total_anomalies": total_anomalies,
            "total_excess_cost": round(total_excess_cost, 2),
            "by_severity": by_severity,
            "by_provider": by_provider,
            "by_service": by_service,
            "top_services_by_impact": {
                k: round(v, 2)
                for k, v in sorted(
                    service_costs.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
            },
            "average_variance": round(
                np.mean([a.variance_percent for a in anomalies]), 2
            ),
        }

        # Determine date range
        if start_date is None:
            start_date = min(a.date for a in anomalies)
        if end_date is None:
            end_date = max(a.date for a in anomalies)

        return AnomalyReport(
            detection_date=datetime.now(),
            period_start=start_date,
            period_end=end_date,
            total_anomalies=total_anomalies,
            anomalies=top_anomalies,  # Include only top anomalies
            summary=summary,
            recommendations=recommendations,
            metadata={
                "config": self.config.model_dump(),
                "model_trained": self._trained,
            },
        )

    def _generate_recommendations(
        self,
        anomalies: List[Anomaly],
        by_severity: Dict[str, int],
        service_costs: Dict[str, float],
    ) -> List[str]:
        """
        Generate actionable recommendations based on detected anomalies.

        Args:
            anomalies: List of anomalies
            by_severity: Anomaly counts by severity
            service_costs: Excess costs by service

        Returns:
            List of recommendations
        """
        recommendations: List[str] = []

        # Critical anomalies
        critical_count = by_severity.get(AnomalySeverity.CRITICAL, 0)
        if critical_count > 0:
            recommendations.append(
                f"URGENT: {critical_count} critical cost anomalies "
                "detected. Immediate investigation required."
            )

        # High-impact services
        if service_costs:
            top_service = max(service_costs.items(), key=lambda x: x[1])
            recommendations.append(
                f"Review {top_service[0]} service: "
                f"${top_service[1]:.2f} in excess costs"
            )

        # Resource-specific recommendations
        resource_anomalies = [a for a in anomalies if a.affected_resources]
        if resource_anomalies:
            recommendations.append(
                f"Investigate {len(resource_anomalies)} resource-specific "
                "anomalies for potential right-sizing or termination"
            )

        # Regional anomalies
        regional_anomalies = [a for a in anomalies if a.region]
        if regional_anomalies:
            regions = list(set(a.region for a in regional_anomalies if a.region))
            if len(regions) <= 3:
                recommendations.append(
                    f"Regional cost spikes detected in: " f"{', '.join(regions)}"
                )

        # Trend-based recommendations
        positive_variance = [a for a in anomalies if a.variance_percent > 0]
        if len(positive_variance) > len(anomalies) * 0.8:
            recommendations.append(
                "Overall cost increase trend detected. "
                "Consider implementing cost optimization measures."
            )

        # Weekend anomalies
        weekend_anomalies = [a for a in anomalies if a.date.weekday() in [5, 6]]
        if len(weekend_anomalies) > len(anomalies) * 0.3:
            recommendations.append(
                "Significant weekend activity detected. "
                "Review auto-scaling policies and scheduled shutdowns."
            )

        # Generic recommendation if nothing specific
        if not recommendations:
            recommendations.append(
                "Monitor cost trends and set up budget alerts "
                "to prevent future anomalies."
            )

        return recommendations

    def set_sensitivity(self, sensitivity: float) -> None:
        """
        Update detection sensitivity and retrain model.

        Args:
            sensitivity: New sensitivity value (0.0 to 1.0)
        """
        if not 0.0 <= sensitivity <= 1.0:
            raise ValueError("Sensitivity must be between 0.0 and 1.0")

        self.config.sensitivity = sensitivity
        self._trained = False
        logger.info(f"Updated sensitivity to {sensitivity}")

    def export_anomalies_csv(self, anomalies: List[Anomaly], output_path: str) -> None:
        """
        Export anomalies to CSV file.

        Args:
            anomalies: List of anomalies to export
            output_path: Path to output CSV file
        """
        if not anomalies:
            logger.warning("No anomalies to export")
            return

        # Convert to DataFrame
        data = []
        for anomaly in anomalies:
            data.append(
                {
                    "date": anomaly.date.strftime("%Y-%m-%d"),
                    "provider": anomaly.provider,
                    "service": anomaly.service,
                    "cost": anomaly.cost,
                    "expected_cost": anomaly.expected_cost,
                    "variance_percent": anomaly.variance_percent,
                    "severity": anomaly.severity,
                    "root_cause": anomaly.root_cause,
                    "region": anomaly.region,
                    "usage_type": anomaly.usage_type,
                }
            )

        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(anomalies)} anomalies to {output_path}")
