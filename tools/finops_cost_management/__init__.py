"""
FinOps & Cost Management Platform.

Comprehensive cloud cost monitoring, optimization recommendations, anomaly detection,
and FinOps practices. Tracks cloud spending across AWS, Azure, and GCS, identifies
cost anomalies using ML-based detection, provides actionable optimization
recommendations, and enables Kubernetes cost attribution with Kubecost integration.

Protocol Coverage:
- P-CLOUD-VALIDATION: Validate cloud resource configurations for cost efficiency
- P-FINOPS-COST-MONITOR: Continuous cost monitoring with anomaly detection
- P-OBSERVABILITY: Cost metrics export to Prometheus/Grafana
"""

__version__ = "1.0.0"
__author__ = "devCrew_s1"

from .anomaly_detector import Anomaly, AnomalyConfig, AnomalyDetector
from .budget_manager import Budget, BudgetAlert, BudgetConfig, BudgetManager
from .cost_aggregator import CloudProvider, CostAggregator, CostData
from .cost_forecaster import CostForecaster, Forecast, ForecastConfig
from .cost_optimizer import (CostOptimizer, OptimizationRecommendation,
                             OptimizerConfig)
from .k8s_cost_analyzer import K8sCostAnalyzer, K8sCostData, KubecostConfig

__all__ = [
    "CostAggregator",
    "CostData",
    "CloudProvider",
    "AnomalyDetector",
    "Anomaly",
    "AnomalyConfig",
    "CostOptimizer",
    "OptimizationRecommendation",
    "OptimizerConfig",
    "CostForecaster",
    "Forecast",
    "ForecastConfig",
    "K8sCostAnalyzer",
    "K8sCostData",
    "KubecostConfig",
    "BudgetManager",
    "Budget",
    "BudgetAlert",
    "BudgetConfig",
]
