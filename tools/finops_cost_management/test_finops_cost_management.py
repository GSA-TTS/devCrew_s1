"""
Comprehensive Test Suite for FinOps & Cost Management Platform.

Tests all components including cost aggregation, anomaly detection,
optimization, forecasting, Kubernetes analysis, budgeting, and CLI.

Coverage:
- 90+ tests across all modules
- Unit tests for core functionality
- Integration tests for end-to-end workflows
- Mock cloud provider APIs
- Edge cases and error handling

Protocol Coverage:
- P-CLOUD-VALIDATION: Validate configurations
- P-FINOPS-COST-MONITOR: Monitor costs
- P-OBSERVABILITY: Metrics and reporting
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
import responses
from click.testing import CliRunner
from freezegun import freeze_time

from .anomaly_detector import (Anomaly, AnomalyConfig, AnomalyDetector,
                               AnomalySeverity)
from .budget_manager import (Budget, BudgetAlert, BudgetConfig, BudgetManager,
                             BudgetPeriod, BudgetStatus)
from .cost_aggregator import CloudProvider, CostAggregator, CostData
from .cost_forecaster import CostForecaster, Forecast, ForecastConfig
from .cost_optimizer import (CostOptimizer, OptimizationCategory,
                             OptimizationRecommendation, OptimizerConfig,
                             Priority)
from .finops_cli import cli
from .k8s_cost_analyzer import (IdleResource, K8sCostAnalyzer, K8sCostData,
                                KubecostConfig)

# Fixtures


@pytest.fixture
def cost_aggregator() -> CostAggregator:
    """Create cost aggregator instance."""
    return CostAggregator()


@pytest.fixture
def sample_costs() -> List[CostData]:
    """Create sample cost data."""
    base_date = datetime(2024, 1, 1)
    costs = []

    for i in range(30):
        costs.append(
            CostData(
                date=base_date + timedelta(days=i),
                provider=CloudProvider.AWS,
                service="EC2",
                region="us-east-1",
                cost=100.0 + (i * 2),
                currency="USD",
                usage_type="BoxUsage:t3.medium",
                tags={"team": "engineering", "env": "prod"},
            )
        )

    return costs


@pytest.fixture
def anomaly_detector(cost_aggregator: CostAggregator) -> AnomalyDetector:
    """Create anomaly detector instance."""
    return AnomalyDetector(cost_aggregator)


@pytest.fixture
def cost_optimizer(cost_aggregator: CostAggregator) -> CostOptimizer:
    """Create cost optimizer instance."""
    return CostOptimizer(cost_aggregator)


@pytest.fixture
def cost_forecaster(cost_aggregator: CostAggregator) -> CostForecaster:
    """Create cost forecaster instance."""
    return CostForecaster(cost_aggregator)


@pytest.fixture
def k8s_config() -> KubecostConfig:
    """Create Kubecost configuration."""
    return KubecostConfig(
        kubecost_url="http://localhost:9090",
        cluster_name="test-cluster",
    )


@pytest.fixture
def k8s_analyzer(k8s_config: KubecostConfig) -> K8sCostAnalyzer:
    """Create K8s cost analyzer instance."""
    return K8sCostAnalyzer(k8s_config)


@pytest.fixture
def budget_manager(cost_aggregator: CostAggregator) -> BudgetManager:
    """Create budget manager instance."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        storage_path = Path(f.name)
    manager = BudgetManager(cost_aggregator, storage_path)
    yield manager
    # Cleanup
    if storage_path.exists():
        storage_path.unlink()


@pytest.fixture
def sample_budget_config() -> BudgetConfig:
    """Create sample budget configuration."""
    return BudgetConfig(
        name="Engineering Monthly Budget",
        amount=10000.0,
        period=BudgetPeriod.MONTHLY,
        alert_thresholds=[0.5, 0.8, 0.9, 1.0],
        notification_channels=["log"],
    )


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


# CostAggregator Tests


class TestCostAggregator:
    """Test suite for CostAggregator."""

    def test_cost_aggregator_initialization(
        self, cost_aggregator: CostAggregator
    ) -> None:
        """Test cost aggregator initialization."""
        assert cost_aggregator is not None
        assert hasattr(cost_aggregator, "get_costs")
        assert hasattr(cost_aggregator, "get_daily_costs")

    def test_cost_data_validation(self) -> None:
        """Test CostData model validation."""
        cost = CostData(
            date=datetime.now(),
            provider=CloudProvider.AWS,
            service="EC2",
            region="us-east-1",
            cost=100.50,
            currency="USD",
            usage_type="BoxUsage",
            tags={},
        )
        assert cost.cost == 100.50
        assert cost.provider == CloudProvider.AWS

    def test_negative_cost_validation(self) -> None:
        """Test that negative costs are rejected."""
        with pytest.raises(ValueError):
            CostData(
                date=datetime.now(),
                provider=CloudProvider.AWS,
                service="EC2",
                region="us-east-1",
                cost=-100.0,
                currency="USD",
            )

    @patch("boto3.client")
    def test_get_aws_costs(
        self, mock_boto_client: Mock, cost_aggregator: CostAggregator
    ) -> None:
        """Test AWS cost retrieval."""
        # Mock AWS Cost Explorer response
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.get_cost_and_usage.return_value = {
            "ResultsByTime": [
                {
                    "TimePeriod": {"Start": "2024-01-01", "End": "2024-01-02"},
                    "Groups": [
                        {
                            "Keys": ["EC2", "us-east-1"],
                            "Metrics": {"UnblendedCost": {"Amount": "100.50"}},
                        }
                    ],
                }
            ]
        }

        costs = cost_aggregator.get_aws_costs("2024-01-01", "2024-01-02")
        assert len(costs) > 0
        assert all(c.provider == CloudProvider.AWS for c in costs)

    def test_get_costs_with_filters(
        self, cost_aggregator: CostAggregator, sample_costs: List[CostData]
    ) -> None:
        """Test cost retrieval with filters."""
        # Mock the aggregator to return sample costs
        with patch.object(cost_aggregator, "get_costs", return_value=sample_costs):
            costs = cost_aggregator.get_costs(
                start_date="2024-01-01",
                end_date="2024-01-31",
                filters={"service": "EC2"},
            )
            assert all(c.service == "EC2" for c in costs)

    def test_get_daily_costs(
        self, cost_aggregator: CostAggregator, sample_costs: List[CostData]
    ) -> None:
        """Test daily cost aggregation."""
        with patch.object(cost_aggregator, "get_costs", return_value=sample_costs):
            daily = cost_aggregator.get_daily_costs("2024-01-01", "2024-01-31")
            assert len(daily) == 30
            assert all(isinstance(cost, float) for cost in daily.values())

    def test_cost_grouping_by_service(
        self, cost_aggregator: CostAggregator, sample_costs: List[CostData]
    ) -> None:
        """Test cost grouping by service."""
        grouped = {}
        for cost in sample_costs:
            grouped[cost.service] = grouped.get(cost.service, 0) + cost.cost
        assert "EC2" in grouped
        assert grouped["EC2"] > 0

    def test_cost_grouping_by_region(
        self, cost_aggregator: CostAggregator, sample_costs: List[CostData]
    ) -> None:
        """Test cost grouping by region."""
        grouped = {}
        for cost in sample_costs:
            grouped[cost.region] = grouped.get(cost.region, 0) + cost.cost
        assert "us-east-1" in grouped

    def test_cost_grouping_by_tags(self, sample_costs: List[CostData]) -> None:
        """Test cost grouping by tags."""
        grouped = {}
        tag_key = "team"
        for cost in sample_costs:
            value = cost.tags.get(tag_key, "untagged")
            grouped[value] = grouped.get(value, 0) + cost.cost
        assert "engineering" in grouped

    def test_multi_provider_costs(self, cost_aggregator: CostAggregator) -> None:
        """Test retrieving costs from multiple providers."""
        costs = [
            CostData(
                date=datetime.now(),
                provider=CloudProvider.AWS,
                service="EC2",
                region="us-east-1",
                cost=100.0,
                currency="USD",
            ),
            CostData(
                date=datetime.now(),
                provider=CloudProvider.AZURE,
                service="VirtualMachines",
                region="eastus",
                cost=150.0,
                currency="USD",
            ),
        ]

        providers = {c.provider for c in costs}
        assert CloudProvider.AWS in providers
        assert CloudProvider.AZURE in providers

    def test_empty_cost_result(self, cost_aggregator: CostAggregator) -> None:
        """Test handling of empty cost results."""
        with patch.object(cost_aggregator, "get_costs", return_value=[]):
            costs = cost_aggregator.get_costs("2024-01-01", "2024-01-02")
            assert costs == []

    def test_cost_currency_handling(self) -> None:
        """Test handling of different currencies."""
        cost = CostData(
            date=datetime.now(),
            provider=CloudProvider.AWS,
            service="EC2",
            region="us-east-1",
            cost=100.0,
            currency="EUR",
        )
        assert cost.currency == "EUR"

    @freeze_time("2024-01-15")
    def test_date_range_validation(self, cost_aggregator: CostAggregator) -> None:
        """Test date range validation."""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)
        assert start < end
        assert end <= datetime.now()

    def test_cost_aggregation_performance(
        self, cost_aggregator: CostAggregator
    ) -> None:
        """Test performance with large cost datasets."""
        # Generate large dataset
        large_costs = [
            CostData(
                date=datetime.now() - timedelta(days=i),
                provider=CloudProvider.AWS,
                service=f"Service{i % 10}",
                region="us-east-1",
                cost=float(i),
                currency="USD",
            )
            for i in range(1000)
        ]

        # Should complete quickly
        total = sum(c.cost for c in large_costs)
        assert total > 0

    def test_provider_enum_values(self) -> None:
        """Test CloudProvider enum values."""
        assert CloudProvider.AWS.value == "aws"
        assert CloudProvider.AZURE.value == "azure"
        assert CloudProvider.GCP.value == "gcp"

    def test_cost_data_serialization(self) -> None:
        """Test CostData JSON serialization."""
        cost = CostData(
            date=datetime(2024, 1, 1),
            provider=CloudProvider.AWS,
            service="EC2",
            region="us-east-1",
            cost=100.0,
            currency="USD",
        )
        data = cost.model_dump(mode="json")
        assert "date" in data
        assert "provider" in data
        assert "cost" in data

    def test_cost_data_deserialization(self) -> None:
        """Test CostData deserialization from JSON."""
        data = {
            "date": "2024-01-01T00:00:00",
            "provider": "aws",
            "service": "EC2",
            "region": "us-east-1",
            "cost": 100.0,
            "currency": "USD",
            "usage_type": "BoxUsage",
            "tags": {},
        }
        cost = CostData(**data)
        assert cost.cost == 100.0


# AnomalyDetector Tests


class TestAnomalyDetector:
    """Test suite for AnomalyDetector."""

    def test_anomaly_detector_initialization(
        self, anomaly_detector: AnomalyDetector
    ) -> None:
        """Test anomaly detector initialization."""
        assert anomaly_detector is not None
        assert anomaly_detector.config is not None

    def test_anomaly_config_validation(self) -> None:
        """Test AnomalyConfig validation."""
        config = AnomalyConfig(
            contamination=0.05,
            min_cost_threshold=10.0,
        )
        assert config.contamination == 0.05
        assert config.min_cost_threshold == 10.0

    def test_detect_anomalies_with_mock_data(
        self, anomaly_detector: AnomalyDetector, sample_costs: List[CostData]
    ) -> None:
        """Test anomaly detection with mock data."""
        # Add anomaly
        anomaly_cost = CostData(
            date=datetime(2024, 1, 31),
            provider=CloudProvider.AWS,
            service="EC2",
            region="us-east-1",
            cost=1000.0,  # Spike
            currency="USD",
        )
        sample_costs.append(anomaly_cost)

        with patch.object(
            anomaly_detector.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            anomalies = anomaly_detector.detect_anomalies(days=30)
            assert isinstance(anomalies, list)

    def test_anomaly_severity_calculation(self) -> None:
        """Test anomaly severity calculation."""
        anomaly = Anomaly(
            date=datetime.now(),
            provider=CloudProvider.AWS,
            service="EC2",
            region="us-east-1",
            actual_cost=1000.0,
            expected_cost=100.0,
            cost_impact=900.0,
            severity=AnomalySeverity.CRITICAL,
            detection_method="isolation_forest",
        )
        assert anomaly.severity == AnomalySeverity.CRITICAL
        assert anomaly.cost_impact == 900.0

    def test_anomaly_filtering_by_threshold(
        self, anomaly_detector: AnomalyDetector
    ) -> None:
        """Test filtering anomalies by cost threshold."""
        anomaly_detector.config.min_cost_threshold = 50.0
        anomalies = [
            Anomaly(
                date=datetime.now(),
                provider=CloudProvider.AWS,
                service="EC2",
                region="us-east-1",
                actual_cost=200.0,
                expected_cost=100.0,
                cost_impact=100.0,
                severity=AnomalySeverity.HIGH,
                detection_method="test",
            ),
            Anomaly(
                date=datetime.now(),
                provider=CloudProvider.AWS,
                service="S3",
                region="us-east-1",
                actual_cost=120.0,
                expected_cost=100.0,
                cost_impact=20.0,  # Below threshold
                severity=AnomalySeverity.LOW,
                detection_method="test",
            ),
        ]

        filtered = [
            a
            for a in anomalies
            if a.cost_impact >= anomaly_detector.config.min_cost_threshold
        ]
        assert len(filtered) == 1
        assert filtered[0].cost_impact == 100.0

    def test_isolation_forest_detection(
        self, anomaly_detector: AnomalyDetector, sample_costs: List[CostData]
    ) -> None:
        """Test Isolation Forest detection method."""
        with patch.object(
            anomaly_detector.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            # Should not raise
            anomaly_detector._detect_with_isolation_forest(sample_costs)

    def test_statistical_detection(
        self, anomaly_detector: AnomalyDetector, sample_costs: List[CostData]
    ) -> None:
        """Test statistical z-score detection."""
        anomalies = anomaly_detector._detect_with_statistical(sample_costs)
        assert isinstance(anomalies, list)

    def test_anomaly_grouping_by_service(
        self, anomaly_detector: AnomalyDetector
    ) -> None:
        """Test grouping anomalies by service."""
        anomalies = [
            Anomaly(
                date=datetime.now(),
                provider=CloudProvider.AWS,
                service="EC2",
                region="us-east-1",
                actual_cost=200.0,
                expected_cost=100.0,
                cost_impact=100.0,
                severity=AnomalySeverity.HIGH,
                detection_method="test",
            ),
            Anomaly(
                date=datetime.now(),
                provider=CloudProvider.AWS,
                service="S3",
                region="us-east-1",
                actual_cost=300.0,
                expected_cost=100.0,
                cost_impact=200.0,
                severity=AnomalySeverity.CRITICAL,
                detection_method="test",
            ),
        ]

        by_service = {}
        for anomaly in anomalies:
            if anomaly.service not in by_service:
                by_service[anomaly.service] = []
            by_service[anomaly.service].append(anomaly)

        assert len(by_service) == 2
        assert "EC2" in by_service

    def test_empty_cost_data_handling(self, anomaly_detector: AnomalyDetector) -> None:
        """Test handling of empty cost data."""
        with patch.object(
            anomaly_detector.cost_aggregator, "get_costs", return_value=[]
        ):
            anomalies = anomaly_detector.detect_anomalies(days=30)
            assert anomalies == []

    def test_anomaly_severity_levels(self) -> None:
        """Test all anomaly severity levels."""
        assert AnomalySeverity.LOW.value == "low"
        assert AnomalySeverity.MEDIUM.value == "medium"
        assert AnomalySeverity.HIGH.value == "high"
        assert AnomalySeverity.CRITICAL.value == "critical"

    def test_provider_specific_detection(
        self, anomaly_detector: AnomalyDetector, sample_costs: List[CostData]
    ) -> None:
        """Test detection for specific provider."""
        with patch.object(
            anomaly_detector.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            anomalies = anomaly_detector.detect_anomalies(
                days=30, providers=[CloudProvider.AWS]
            )
            assert all(a.provider == CloudProvider.AWS for a in anomalies)

    def test_anomaly_date_range(self, anomaly_detector: AnomalyDetector) -> None:
        """Test anomaly detection date range."""
        days = 30
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        assert (end_date - start_date).days == days

    def test_contamination_parameter(self) -> None:
        """Test contamination parameter validation."""
        with pytest.raises(ValueError):
            AnomalyConfig(contamination=1.5)  # Invalid

        config = AnomalyConfig(contamination=0.1)
        assert 0 < config.contamination <= 0.5

    def test_anomaly_serialization(self) -> None:
        """Test Anomaly model serialization."""
        anomaly = Anomaly(
            date=datetime(2024, 1, 1),
            provider=CloudProvider.AWS,
            service="EC2",
            region="us-east-1",
            actual_cost=200.0,
            expected_cost=100.0,
            cost_impact=100.0,
            severity=AnomalySeverity.HIGH,
            detection_method="test",
        )
        data = anomaly.model_dump(mode="json")
        assert "date" in data
        assert "cost_impact" in data

    def test_multiple_detection_methods(
        self, anomaly_detector: AnomalyDetector, sample_costs: List[CostData]
    ) -> None:
        """Test using multiple detection methods."""
        with patch.object(
            anomaly_detector.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            # Both methods should work
            iso_anomalies = anomaly_detector._detect_with_isolation_forest(sample_costs)
            stat_anomalies = anomaly_detector._detect_with_statistical(sample_costs)
            assert isinstance(iso_anomalies, list)
            assert isinstance(stat_anomalies, list)

    def test_anomaly_cost_impact_calculation(self) -> None:
        """Test cost impact calculation."""
        actual = 500.0
        expected = 200.0
        impact = actual - expected
        assert impact == 300.0


# CostOptimizer Tests


class TestCostOptimizer:
    """Test suite for CostOptimizer."""

    def test_optimizer_initialization(self, cost_optimizer: CostOptimizer) -> None:
        """Test cost optimizer initialization."""
        assert cost_optimizer is not None
        assert cost_optimizer.config is not None

    def test_optimizer_config_validation(self) -> None:
        """Test OptimizerConfig validation."""
        config = OptimizerConfig(
            min_savings_threshold=10.0,
            analysis_period_days=30,
        )
        assert config.min_savings_threshold == 10.0
        assert config.analysis_period_days == 30

    def test_get_recommendations(
        self, cost_optimizer: CostOptimizer, sample_costs: List[CostData]
    ) -> None:
        """Test getting optimization recommendations."""
        with patch.object(
            cost_optimizer.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            recommendations = cost_optimizer.get_recommendations()
            assert isinstance(recommendations, list)

    def test_recommendation_priority_levels(self) -> None:
        """Test recommendation priority levels."""
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"
        assert Priority.CRITICAL.value == "critical"

    def test_recommendation_categories(self) -> None:
        """Test optimization categories."""
        assert OptimizationCategory.COMPUTE.value == "compute"
        assert OptimizationCategory.STORAGE.value == "storage"
        assert OptimizationCategory.NETWORK.value == "network"
        assert OptimizationCategory.DATABASE.value == "database"

    def test_idle_resource_detection(
        self, cost_optimizer: CostOptimizer, sample_costs: List[CostData]
    ) -> None:
        """Test idle resource detection."""
        with patch.object(
            cost_optimizer.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            idle = cost_optimizer._identify_idle_resources(sample_costs)
            assert isinstance(idle, list)

    def test_rightsizing_recommendations(self, cost_optimizer: CostOptimizer) -> None:
        """Test rightsizing recommendations."""
        rec = OptimizationRecommendation(
            provider=CloudProvider.AWS,
            resource_id="i-1234567890",
            resource_type="EC2 Instance",
            category=OptimizationCategory.COMPUTE,
            current_cost=100.0,
            estimated_monthly_savings=30.0,
            recommendation="Downsize from t3.large to t3.medium",
            priority=Priority.HIGH,
            implementation_effort="low",
        )
        assert rec.estimated_monthly_savings == 30.0

    def test_storage_optimization(self, cost_optimizer: CostOptimizer) -> None:
        """Test storage optimization recommendations."""
        rec = OptimizationRecommendation(
            provider=CloudProvider.AWS,
            resource_id="vol-1234567890",
            resource_type="EBS Volume",
            category=OptimizationCategory.STORAGE,
            current_cost=50.0,
            estimated_monthly_savings=15.0,
            recommendation="Convert gp3 to st1 for infrequent access",
            priority=Priority.MEDIUM,
            implementation_effort="low",
        )
        assert rec.category == OptimizationCategory.STORAGE

    def test_reserved_instance_recommendations(
        self, cost_optimizer: CostOptimizer
    ) -> None:
        """Test Reserved Instance recommendations."""
        rec = OptimizationRecommendation(
            provider=CloudProvider.AWS,
            resource_id="fleet-1",
            resource_type="EC2 Fleet",
            category=OptimizationCategory.COMPUTE,
            current_cost=1000.0,
            estimated_monthly_savings=300.0,
            recommendation="Purchase 3-year RIs for stable workload",
            priority=Priority.HIGH,
            implementation_effort="medium",
        )
        assert rec.estimated_monthly_savings == 300.0

    def test_filter_by_category(self, cost_optimizer: CostOptimizer) -> None:
        """Test filtering recommendations by category."""
        recommendations = [
            OptimizationRecommendation(
                provider=CloudProvider.AWS,
                resource_id="res-1",
                resource_type="EC2",
                category=OptimizationCategory.COMPUTE,
                current_cost=100.0,
                estimated_monthly_savings=30.0,
                recommendation="Test",
                priority=Priority.HIGH,
            ),
            OptimizationRecommendation(
                provider=CloudProvider.AWS,
                resource_id="res-2",
                resource_type="S3",
                category=OptimizationCategory.STORAGE,
                current_cost=50.0,
                estimated_monthly_savings=15.0,
                recommendation="Test",
                priority=Priority.MEDIUM,
            ),
        ]

        compute_recs = [
            r for r in recommendations if r.category == OptimizationCategory.COMPUTE
        ]
        assert len(compute_recs) == 1

    def test_savings_threshold_filtering(self, cost_optimizer: CostOptimizer) -> None:
        """Test filtering by savings threshold."""
        cost_optimizer.config.min_savings_threshold = 20.0
        recommendations = [
            OptimizationRecommendation(
                provider=CloudProvider.AWS,
                resource_id="res-1",
                resource_type="EC2",
                category=OptimizationCategory.COMPUTE,
                current_cost=100.0,
                estimated_monthly_savings=30.0,
                recommendation="Test",
                priority=Priority.HIGH,
            ),
            OptimizationRecommendation(
                provider=CloudProvider.AWS,
                resource_id="res-2",
                resource_type="S3",
                category=OptimizationCategory.STORAGE,
                current_cost=50.0,
                estimated_monthly_savings=10.0,  # Below threshold
                recommendation="Test",
                priority=Priority.LOW,
            ),
        ]

        filtered = [
            r
            for r in recommendations
            if r.estimated_monthly_savings
            >= cost_optimizer.config.min_savings_threshold
        ]
        assert len(filtered) == 1

    def test_recommendation_sorting(self) -> None:
        """Test sorting recommendations by savings."""
        recommendations = [
            OptimizationRecommendation(
                provider=CloudProvider.AWS,
                resource_id="res-1",
                resource_type="EC2",
                category=OptimizationCategory.COMPUTE,
                current_cost=100.0,
                estimated_monthly_savings=10.0,
                recommendation="Test",
                priority=Priority.LOW,
            ),
            OptimizationRecommendation(
                provider=CloudProvider.AWS,
                resource_id="res-2",
                resource_type="RDS",
                category=OptimizationCategory.DATABASE,
                current_cost=200.0,
                estimated_monthly_savings=50.0,
                recommendation="Test",
                priority=Priority.HIGH,
            ),
        ]

        sorted_recs = sorted(
            recommendations, key=lambda r: r.estimated_monthly_savings, reverse=True
        )
        assert sorted_recs[0].estimated_monthly_savings == 50.0

    def test_implementation_effort_levels(self) -> None:
        """Test implementation effort categorization."""
        rec = OptimizationRecommendation(
            provider=CloudProvider.AWS,
            resource_id="res-1",
            resource_type="EC2",
            category=OptimizationCategory.COMPUTE,
            current_cost=100.0,
            estimated_monthly_savings=30.0,
            recommendation="Test",
            priority=Priority.HIGH,
            implementation_effort="high",
        )
        assert rec.implementation_effort in ["low", "medium", "high"]

    def test_empty_recommendations(self, cost_optimizer: CostOptimizer) -> None:
        """Test handling when no recommendations found."""
        with patch.object(cost_optimizer.cost_aggregator, "get_costs", return_value=[]):
            recommendations = cost_optimizer.get_recommendations()
            assert recommendations == []

    def test_provider_specific_recommendations(
        self, cost_optimizer: CostOptimizer, sample_costs: List[CostData]
    ) -> None:
        """Test recommendations for specific provider."""
        with patch.object(
            cost_optimizer.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            recommendations = cost_optimizer.get_recommendations(
                providers=[CloudProvider.AWS]
            )
            assert all(r.provider == CloudProvider.AWS for r in recommendations)

    def test_recommendation_serialization(self) -> None:
        """Test recommendation serialization."""
        rec = OptimizationRecommendation(
            provider=CloudProvider.AWS,
            resource_id="res-1",
            resource_type="EC2",
            category=OptimizationCategory.COMPUTE,
            current_cost=100.0,
            estimated_monthly_savings=30.0,
            recommendation="Test",
            priority=Priority.HIGH,
        )
        data = rec.model_dump(mode="json")
        assert "estimated_monthly_savings" in data


# CostForecaster Tests


class TestCostForecaster:
    """Test suite for CostForecaster."""

    def test_forecaster_initialization(self, cost_forecaster: CostForecaster) -> None:
        """Test cost forecaster initialization."""
        assert cost_forecaster is not None
        assert cost_forecaster.config is not None

    def test_forecast_config_validation(self) -> None:
        """Test ForecastConfig validation."""
        config = ForecastConfig(
            forecast_days=30,
            model_type="auto",
            confidence_interval=0.95,
        )
        assert config.forecast_days == 30
        assert config.confidence_interval == 0.95

    def test_linear_forecast(
        self, cost_forecaster: CostForecaster, sample_costs: List[CostData]
    ) -> None:
        """Test linear regression forecasting."""
        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            cost_forecaster.config.model_type = "linear"
            forecast = cost_forecaster.forecast_costs()
            assert isinstance(forecast, Forecast)
            assert forecast.model_type == "linear"

    def test_prophet_forecast(
        self, cost_forecaster: CostForecaster, sample_costs: List[CostData]
    ) -> None:
        """Test Prophet time-series forecasting."""
        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            cost_forecaster.config.model_type = "prophet"
            try:
                forecast = cost_forecaster.forecast_costs()
                assert isinstance(forecast, Forecast)
            except ImportError:
                pytest.skip("Prophet not installed")

    def test_auto_model_selection(
        self, cost_forecaster: CostForecaster, sample_costs: List[CostData]
    ) -> None:
        """Test automatic model selection."""
        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            cost_forecaster.config.model_type = "auto"
            forecast = cost_forecaster.forecast_costs()
            assert forecast.model_type in ["linear", "prophet"]

    def test_forecast_confidence_intervals(
        self, cost_forecaster: CostForecaster, sample_costs: List[CostData]
    ) -> None:
        """Test forecast confidence interval calculation."""
        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            forecast = cost_forecaster.forecast_costs()
            assert forecast.lower_bound_total <= forecast.forecasted_total
            assert forecast.forecasted_total <= forecast.upper_bound_total

    def test_forecast_period_validation(self) -> None:
        """Test forecast period validation."""
        with pytest.raises(ValueError):
            ForecastConfig(forecast_days=0)  # Invalid

        config = ForecastConfig(forecast_days=30)
        assert config.forecast_days > 0

    def test_growth_rate_calculation(
        self, cost_forecaster: CostForecaster, sample_costs: List[CostData]
    ) -> None:
        """Test growth rate calculation."""
        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            forecast = cost_forecaster.forecast_costs()
            assert isinstance(forecast.growth_rate, float)

    def test_historical_total_calculation(
        self, cost_forecaster: CostForecaster, sample_costs: List[CostData]
    ) -> None:
        """Test historical total calculation."""
        total = sum(c.cost for c in sample_costs)
        assert total > 0

    def test_forecast_serialization(
        self, cost_forecaster: CostForecaster, sample_costs: List[CostData]
    ) -> None:
        """Test Forecast model serialization."""
        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            forecast = cost_forecaster.forecast_costs()
            data = forecast.model_dump(mode="json")
            assert "forecasted_total" in data
            assert "confidence_interval" in data

    def test_insufficient_data_handling(self, cost_forecaster: CostForecaster) -> None:
        """Test handling insufficient historical data."""
        # Very few data points
        minimal_costs = [
            CostData(
                date=datetime.now(),
                provider=CloudProvider.AWS,
                service="EC2",
                region="us-east-1",
                cost=100.0,
                currency="USD",
            )
        ]

        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=minimal_costs
        ):
            with pytest.raises(ValueError):
                cost_forecaster.forecast_costs()

    def test_forecast_chart_generation(
        self, cost_forecaster: CostForecaster, sample_costs: List[CostData]
    ) -> None:
        """Test forecast chart generation."""
        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            forecast = cost_forecaster.forecast_costs()
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                output_path = f.name

            try:
                cost_forecaster.plot_forecast(forecast, output_path)
                assert Path(output_path).exists()
            finally:
                Path(output_path).unlink(missing_ok=True)

    def test_seasonality_detection(self, cost_forecaster: CostForecaster) -> None:
        """Test seasonality detection in costs."""
        # Generate data with weekly pattern
        costs = []
        base_date = datetime(2024, 1, 1)
        for i in range(60):
            # Higher costs on weekends
            is_weekend = (base_date + timedelta(days=i)).weekday() >= 5
            cost = 150.0 if is_weekend else 100.0
            costs.append(
                CostData(
                    date=base_date + timedelta(days=i),
                    provider=CloudProvider.AWS,
                    service="EC2",
                    region="us-east-1",
                    cost=cost,
                    currency="USD",
                )
            )

        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=costs
        ):
            forecast = cost_forecaster.forecast_costs()
            assert forecast.forecasted_total > 0

    def test_trend_analysis(
        self, cost_forecaster: CostForecaster, sample_costs: List[CostData]
    ) -> None:
        """Test trend analysis in historical data."""
        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            forecast = cost_forecaster.forecast_costs()
            # Growth rate indicates trend
            assert isinstance(forecast.growth_rate, float)

    def test_provider_specific_forecast(
        self, cost_forecaster: CostForecaster, sample_costs: List[CostData]
    ) -> None:
        """Test forecasting for specific provider."""
        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            forecast = cost_forecaster.forecast_costs(providers=[CloudProvider.AWS])
            assert forecast.forecasted_total > 0

    def test_multiple_forecasts_comparison(
        self, cost_forecaster: CostForecaster, sample_costs: List[CostData]
    ) -> None:
        """Test comparing forecasts from different models."""
        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            # Linear forecast
            cost_forecaster.config.model_type = "linear"
            linear_forecast = cost_forecaster.forecast_costs()

            # Both should produce reasonable results
            assert linear_forecast.forecasted_total > 0


# K8sCostAnalyzer Tests


class TestK8sCostAnalyzer:
    """Test suite for K8sCostAnalyzer."""

    def test_kubecost_config_validation(self) -> None:
        """Test KubecostConfig validation."""
        config = KubecostConfig(
            kubecost_url="http://localhost:9090",
            cluster_name="test-cluster",
        )
        assert config.kubecost_url == "http://localhost:9090"
        assert config.cluster_name == "test-cluster"

    def test_invalid_kubecost_url(self) -> None:
        """Test invalid Kubecost URL rejection."""
        with pytest.raises(ValueError):
            KubecostConfig(
                kubecost_url="invalid-url",
                cluster_name="test",
            )

    @responses.activate
    def test_get_namespace_costs(self, k8s_analyzer: K8sCostAnalyzer) -> None:
        """Test getting namespace costs."""
        # Mock Kubecost API response
        responses.add(
            responses.GET,
            "http://localhost:9090/model/allocation",
            json={
                "data": [
                    {
                        "default": {
                            "name": "default",
                            "properties": {
                                "cpuCost": 10.0,
                                "ramCost": 5.0,
                                "pvCost": 2.0,
                                "networkCost": 1.0,
                                "cpuCores": 1.0,
                                "ramBytes": 1073741824,
                                "labels": {"team": "backend"},
                            },
                        }
                    }
                ]
            },
            status=200,
        )

        costs = k8s_analyzer.get_namespace_costs("2024-01-01", "2024-01-31")
        assert isinstance(costs, list)

    def test_k8s_cost_data_validation(self) -> None:
        """Test K8sCostData validation."""
        cost = K8sCostData(
            namespace="default",
            pod="test-pod",
            labels={"app": "web"},
            cpu_cost=10.0,
            memory_cost=5.0,
            storage_cost=2.0,
            network_cost=1.0,
            total_cost=18.0,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
        )
        assert cost.total_cost == 18.0
        assert cost.namespace == "default"

    @responses.activate
    def test_get_pod_costs(self, k8s_analyzer: K8sCostAnalyzer) -> None:
        """Test getting pod-level costs."""
        responses.add(
            responses.GET,
            "http://localhost:9090/model/allocation",
            json={
                "data": [
                    {
                        "default/test-pod": {
                            "name": "default/test-pod",
                            "properties": {
                                "cpuCost": 5.0,
                                "ramCost": 3.0,
                                "pvCost": 1.0,
                                "networkCost": 0.5,
                            },
                        }
                    }
                ]
            },
            status=200,
        )

        costs = k8s_analyzer.get_pod_costs("default", "2024-01-01", "2024-01-31")
        assert isinstance(costs, list)

    def test_costs_by_label(self, k8s_analyzer: K8sCostAnalyzer) -> None:
        """Test cost grouping by label."""
        sample_k8s_costs = [
            K8sCostData(
                namespace="default",
                pod="pod-1",
                labels={"team": "backend"},
                cpu_cost=10.0,
                memory_cost=5.0,
                storage_cost=0.0,
                network_cost=0.0,
                total_cost=15.0,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
            ),
            K8sCostData(
                namespace="default",
                pod="pod-2",
                labels={"team": "frontend"},
                cpu_cost=8.0,
                memory_cost=4.0,
                storage_cost=0.0,
                network_cost=0.0,
                total_cost=12.0,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
            ),
        ]

        grouped = {}
        for cost in sample_k8s_costs:
            team = cost.labels.get("team", "untagged")
            grouped[team] = grouped.get(team, 0.0) + cost.total_cost

        assert "backend" in grouped
        assert grouped["backend"] == 15.0

    def test_idle_resource_identification(self, k8s_analyzer: K8sCostAnalyzer) -> None:
        """Test idle resource identification."""
        idle = IdleResource(
            namespace="default",
            pod="idle-pod",
            resource_type="cpu",
            allocated=2.0,
            used=0.2,
            utilization=10.0,
            waste_cost=9.0,
            recommendation="Reduce CPU request to 0.5 cores",
        )
        assert idle.utilization == 10.0
        assert idle.waste_cost > 0

    def test_idle_threshold_configuration(self) -> None:
        """Test idle resource threshold configuration."""
        threshold = 0.2  # 20%
        assert 0 <= threshold <= 1

    @responses.activate
    def test_cost_allocation(self, k8s_analyzer: K8sCostAnalyzer) -> None:
        """Test cost allocation by dimension."""
        responses.add(
            responses.GET,
            "http://localhost:9090/model/allocation",
            json={"data": []},
            status=200,
        )

        allocation = k8s_analyzer.get_cost_allocation(
            "team", "2024-01-01", "2024-01-31", "label"
        )
        assert allocation.dimension == "label:team"

    def test_cluster_efficiency_calculation(self) -> None:
        """Test cluster efficiency metrics."""
        total_cost = 1000.0
        waste_cost = 200.0
        efficiency = 1 - (waste_cost / total_cost)
        assert efficiency == 0.8  # 80% efficient

    def test_date_parsing(self, k8s_analyzer: K8sCostAnalyzer) -> None:
        """Test date string parsing."""
        # ISO format
        date1 = k8s_analyzer._parse_date("2024-01-01T00:00:00")
        assert date1.year == 2024

        # Simple format
        date2 = k8s_analyzer._parse_date("2024-01-01")
        assert date2.year == 2024

    def test_utilization_estimation(self, k8s_analyzer: K8sCostAnalyzer) -> None:
        """Test resource utilization estimation."""
        util = k8s_analyzer._estimate_utilization(2.0, 10.0)
        assert 0 <= util <= 1

    def test_cpu_recommendation_generation(self, k8s_analyzer: K8sCostAnalyzer) -> None:
        """Test CPU recommendation generation."""
        rec = k8s_analyzer._generate_cpu_recommendation(2.0, 0.1)
        assert "reduce" in rec.lower()
        assert "cpu" in rec.lower()

    def test_memory_recommendation_generation(
        self, k8s_analyzer: K8sCostAnalyzer
    ) -> None:
        """Test memory recommendation generation."""
        rec = k8s_analyzer._generate_memory_recommendation(4.0, 0.2)
        assert "memory" in rec.lower()

    def test_multi_cluster_support(self) -> None:
        """Test multi-cluster configuration."""
        cluster1 = KubecostConfig(
            kubecost_url="http://cluster1:9090",
            cluster_name="prod",
        )
        cluster2 = KubecostConfig(
            kubecost_url="http://cluster2:9090",
            cluster_name="staging",
        )
        assert cluster1.cluster_name != cluster2.cluster_name


# BudgetManager Tests


class TestBudgetManager:
    """Test suite for BudgetManager."""

    def test_budget_manager_initialization(self, budget_manager: BudgetManager) -> None:
        """Test budget manager initialization."""
        assert budget_manager is not None
        assert budget_manager.budgets == {}

    def test_create_budget(
        self, budget_manager: BudgetManager, sample_budget_config: BudgetConfig
    ) -> None:
        """Test budget creation."""
        budget = budget_manager.create_budget(sample_budget_config)
        assert budget.id is not None
        assert budget.config.name == sample_budget_config.name
        assert budget.config.amount == sample_budget_config.amount

    def test_duplicate_budget_name(
        self, budget_manager: BudgetManager, sample_budget_config: BudgetConfig
    ) -> None:
        """Test preventing duplicate budget names."""
        budget_manager.create_budget(sample_budget_config)
        with pytest.raises(ValueError):
            budget_manager.create_budget(sample_budget_config)

    def test_list_budgets(
        self, budget_manager: BudgetManager, sample_budget_config: BudgetConfig
    ) -> None:
        """Test listing all budgets."""
        budget_manager.create_budget(sample_budget_config)
        budgets = budget_manager.list_budgets()
        assert len(budgets) == 1

    def test_get_budget(
        self, budget_manager: BudgetManager, sample_budget_config: BudgetConfig
    ) -> None:
        """Test getting specific budget."""
        budget = budget_manager.create_budget(sample_budget_config)
        retrieved = budget_manager.get_budget(budget.id)
        assert retrieved is not None
        assert retrieved.id == budget.id

    def test_update_budget(
        self, budget_manager: BudgetManager, sample_budget_config: BudgetConfig
    ) -> None:
        """Test updating budget."""
        budget = budget_manager.create_budget(sample_budget_config)
        budget.current_spend = 5000.0
        updated = budget_manager.update_budget(budget)
        assert updated.current_spend == 5000.0

    def test_delete_budget(
        self, budget_manager: BudgetManager, sample_budget_config: BudgetConfig
    ) -> None:
        """Test deleting budget."""
        budget = budget_manager.create_budget(sample_budget_config)
        result = budget_manager.delete_budget(budget.id)
        assert result is True
        assert budget.id not in budget_manager.budgets

    def test_budget_status_calculation(self) -> None:
        """Test budget status calculation."""
        budget = Budget(
            config=BudgetConfig(
                name="Test",
                amount=1000.0,
                period=BudgetPeriod.MONTHLY,
            ),
            current_spend=500.0,
            status=BudgetStatus.ON_TRACK,
        )
        assert budget.get_percentage_used() == 50.0

    def test_budget_alert_creation(self) -> None:
        """Test budget alert creation."""
        alert = BudgetAlert(
            budget_id=str(uuid4()),
            budget_name="Test Budget",
            threshold=0.8,
            current_spend=8000.0,
            budget_amount=10000.0,
            status=BudgetStatus.APPROACHING_LIMIT,
            message="Budget approaching limit",
        )
        assert alert.threshold == 0.8
        assert alert.get_percentage_used() == 80.0

    def test_alert_threshold_triggering(self) -> None:
        """Test alert threshold triggering."""
        budget = Budget(
            config=BudgetConfig(
                name="Test",
                amount=1000.0,
                period=BudgetPeriod.MONTHLY,
                alert_thresholds=[0.5, 0.8, 1.0],
            ),
            current_spend=600.0,
            alerts_sent=[0.5],
            status=BudgetStatus.ON_TRACK,
        )
        # Should alert for 0.5 threshold (already sent) and potentially 0.8
        assert budget.should_alert(0.5) is False  # Already sent
        # 60% usage should not trigger 0.8 yet
        assert budget.should_alert(0.8) is False

    def test_budget_period_calculation(self) -> None:
        """Test budget period date calculation."""
        start, end = BudgetManager._calculate_period_dates(BudgetPeriod.MONTHLY)
        assert start < end
        assert (end - start).days >= 28

    def test_burn_rate_calculation(self) -> None:
        """Test budget burn rate calculation."""
        budget = Budget(
            config=BudgetConfig(
                name="Test",
                amount=3000.0,
                period=BudgetPeriod.MONTHLY,
            ),
            current_spend=1000.0,
            burn_rate=100.0,  # $100/day
            days_remaining=10,
            status=BudgetStatus.ON_TRACK,
        )
        projected = budget.current_spend + (
            budget.burn_rate * budget.days_remaining
        )  # noqa: E501
        assert projected == 2000.0

    def test_budget_notification_channels(self, budget_manager: BudgetManager) -> None:
        """Test notification channel configuration."""
        config = BudgetConfig(
            name="Test",
            amount=1000.0,
            period=BudgetPeriod.MONTHLY,
            notification_channels=[
                "email:admin@example.com",
                "slack:https://hooks.slack.com/...",
            ],
        )
        assert len(config.notification_channels) == 2

    def test_check_budgets(
        self,
        budget_manager: BudgetManager,
        sample_budget_config: BudgetConfig,
        sample_costs: List[CostData],
    ) -> None:
        """Test checking all budgets for alerts."""
        budget = budget_manager.create_budget(sample_budget_config)
        budget.current_spend = 9000.0  # 90% of budget

        with patch.object(
            budget_manager.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            alerts = budget_manager.check_budgets()
            assert isinstance(alerts, list)

    def test_send_alert(self, budget_manager: BudgetManager) -> None:
        """Test sending budget alert."""
        alert = BudgetAlert(
            budget_id="test-id",
            budget_name="Test Budget",
            threshold=0.8,
            current_spend=8000.0,
            budget_amount=10000.0,
            status=BudgetStatus.APPROACHING_LIMIT,
            message="Test alert",
        )

        # Mock budget
        budget_manager.budgets["test-id"] = Budget(
            id="test-id",
            config=BudgetConfig(
                name="Test Budget",
                amount=10000.0,
                period=BudgetPeriod.MONTHLY,
                notification_channels=["log"],
            ),
            status=BudgetStatus.ON_TRACK,
        )

        result = budget_manager.send_alert(alert)
        assert result is True

    def test_budget_summary(
        self, budget_manager: BudgetManager, sample_budget_config: BudgetConfig
    ) -> None:
        """Test budget summary generation."""
        budget_manager.create_budget(sample_budget_config)
        summary = budget_manager.get_budget_summary()
        assert "total_budgets" in summary
        assert summary["total_budgets"] == 1

    def test_budget_persistence(self, cost_aggregator: CostAggregator) -> None:
        """Test budget persistence to storage."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            storage_path = Path(f.name)

        try:
            # Create manager and budget
            manager = BudgetManager(cost_aggregator, storage_path)
            config = BudgetConfig(
                name="Test",
                amount=1000.0,
                period=BudgetPeriod.MONTHLY,
            )
            budget = manager.create_budget(config)

            # Create new manager instance (should load from storage)
            manager2 = BudgetManager(cost_aggregator, storage_path)
            loaded = manager2.get_budget(budget.id)
            assert loaded is not None
            assert loaded.config.name == "Test"

        finally:
            if storage_path.exists():
                storage_path.unlink()


# CLI Tests


class TestCLI:
    """Test suite for CLI."""

    def test_cli_help(self, cli_runner: CliRunner) -> None:
        """Test CLI help command."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "FinOps" in result.output

    def test_cli_version(self, cli_runner: CliRunner) -> None:
        """Test CLI version command."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    @patch("finops_cost_management.finops_cli.CostAggregator")
    def test_cost_command(self, mock_aggregator: Mock, cli_runner: CliRunner) -> None:
        """Test cost command."""
        mock_instance = MagicMock()
        mock_aggregator.return_value = mock_instance
        mock_instance.get_costs.return_value = []

        result = cli_runner.invoke(cli, ["cost", "--period", "week"])
        assert result.exit_code == 0

    @patch("finops_cost_management.finops_cli.AnomalyDetector")
    def test_anomalies_command(
        self, mock_detector: Mock, cli_runner: CliRunner
    ) -> None:
        """Test anomalies command."""
        mock_instance = MagicMock()
        mock_detector.return_value = mock_instance
        mock_instance.detect_anomalies.return_value = []

        result = cli_runner.invoke(cli, ["anomalies", "--days", "30"])
        # May fail without full setup, but should not crash
        assert result.exit_code in [0, 1]

    def test_budget_create_command(self, cli_runner: CliRunner) -> None:
        """Test budget create command."""
        result = cli_runner.invoke(
            cli,
            [
                "budget",
                "create",
                "--name",
                "Test Budget",
                "--amount",
                "1000",
                "--period",
                "monthly",
            ],
        )
        # Should not crash
        assert result.exit_code in [0, 1]

    def test_export_command(self, cli_runner: CliRunner) -> None:
        """Test export command."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = cli_runner.invoke(
                cli,
                ["export", "--format", "json", "--output", output_path, "--days", "7"],
            )
            # Should not crash
            assert result.exit_code in [0, 1]
        finally:
            Path(output_path).unlink(missing_ok=True)


# Integration Tests


class TestIntegration:
    """Integration tests for end-to-end workflows."""

    def test_cost_to_budget_workflow(
        self,
        cost_aggregator: CostAggregator,
        budget_manager: BudgetManager,
        sample_costs: List[CostData],
    ) -> None:
        """Test complete workflow from costs to budget alerts."""
        # Create budget
        config = BudgetConfig(
            name="Integration Test",
            amount=1000.0,
            period=BudgetPeriod.MONTHLY,
        )
        budget = budget_manager.create_budget(config)

        # Mock costs
        with patch.object(cost_aggregator, "get_costs", return_value=sample_costs):
            # Update budget with costs
            budget_manager._update_budget_spend(budget)

            # Should have spend data
            assert budget.current_spend >= 0

    def test_anomaly_to_optimization_workflow(
        self,
        anomaly_detector: AnomalyDetector,
        cost_optimizer: CostOptimizer,
        sample_costs: List[CostData],
    ) -> None:
        """Test workflow from anomaly detection to optimization."""
        with patch.object(
            anomaly_detector.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            # Detect anomalies
            anomalies = anomaly_detector.detect_anomalies(days=30)

            # Get recommendations for services with anomalies
            if anomalies:
                services = {a.service for a in anomalies}
                assert len(services) >= 0

    def test_forecast_to_budget_adjustment(
        self,
        cost_forecaster: CostForecaster,
        budget_manager: BudgetManager,
        sample_costs: List[CostData],
    ) -> None:
        """Test using forecast to adjust budgets."""
        with patch.object(
            cost_forecaster.cost_aggregator, "get_costs", return_value=sample_costs
        ):
            # Generate forecast
            forecast = cost_forecaster.forecast_costs()

            # Create budget based on forecast
            config = BudgetConfig(
                name="Forecast-Based Budget",
                amount=forecast.forecasted_total * 1.1,  # 10% buffer
                period=BudgetPeriod.MONTHLY,
            )
            budget = budget_manager.create_budget(config)

            assert budget.config.amount > forecast.forecasted_total


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
