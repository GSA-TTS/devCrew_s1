# FinOps & Cost Management Platform

Comprehensive cloud cost monitoring, optimization, and budgeting platform supporting AWS, Azure, and Google Cloud Platform. Provides real-time cost tracking, ML-based anomaly detection, actionable optimization recommendations, accurate cost forecasting, Kubernetes cost attribution, and intelligent budget management with multi-channel alerting.

## Overview

This platform implements TOOL-FINOPS-001 to provide enterprise-grade FinOps capabilities for multi-cloud environments. It enables organizations to monitor spending, detect cost anomalies, optimize resource usage, forecast future costs, track Kubernetes workloads, and manage budgets effectively.

### Protocol Coverage

- **P-CLOUD-VALIDATION**: Validate cloud resource configurations for cost efficiency
- **P-FINOPS-COST-MONITOR**: Continuous cost monitoring with real-time anomaly detection
- **P-OBSERVABILITY**: Cost metrics export to Prometheus, Grafana, and other monitoring systems

### Key Features

#### Multi-Cloud Cost Aggregation
- **AWS Cost Explorer Integration**: Real-time cost data from AWS Cost Explorer API
- **Azure Cost Management**: Native integration with Azure Cost Management APIs
- **Google Cloud Billing**: GCP billing API integration with Cloud Asset Inventory
- **Unified Cost View**: Aggregate costs across all providers with consistent data model
- **Flexible Grouping**: Group by provider, service, region, resource type, or custom tags
- **Tag-Based Filtering**: Filter and analyze costs using resource tags and labels

#### ML-Based Anomaly Detection
- **Isolation Forest Algorithm**: Detect outliers in cost patterns using unsupervised learning
- **Statistical Analysis**: Z-score based detection for identifying significant deviations
- **Configurable Sensitivity**: Adjust detection thresholds based on environment
- **Severity Classification**: Automatic severity assignment (Low, Medium, High, Critical)
- **Historical Context**: Compare current costs against historical baselines
- **Service-Level Detection**: Identify anomalies at service and resource level

#### Cost Optimization
- **Idle Resource Detection**: Identify underutilized or idle cloud resources
- **Rightsizing Recommendations**: Suggest optimal instance sizes based on usage patterns
- **Reserved Instance Analysis**: Identify opportunities for reserved capacity purchases
- **Storage Optimization**: Recommend lifecycle policies and storage tier changes
- **Network Optimization**: Detect inefficient data transfer patterns
- **Database Optimization**: Identify oversized databases and unused replicas
- **Priority Scoring**: Rank recommendations by potential savings and effort

#### Cost Forecasting
- **Prophet Time-Series Model**: Facebook Prophet for seasonal trend analysis
- **Linear Regression**: Simple linear models for stable workloads
- **Auto Model Selection**: Automatically choose best model based on data characteristics
- **Confidence Intervals**: Provide upper and lower bounds for forecasts
- **Growth Rate Analysis**: Calculate and project cost growth trends
- **Seasonal Patterns**: Detect and account for weekly, monthly, and yearly patterns
- **Visualization**: Generate forecast charts with historical and projected data

#### Kubernetes Cost Attribution
- **Kubecost Integration**: Direct integration with Kubecost API
- **Namespace Costs**: Track costs by Kubernetes namespace
- **Pod-Level Attribution**: Detailed cost breakdown by pod and container
- **Label-Based Allocation**: Allocate costs using custom Kubernetes labels
- **Idle Resource Detection**: Identify underutilized K8s resources with configurable thresholds
- **Cost Recommendations**: Generate rightsizing recommendations for pods
- **Multi-Cluster Support**: Track costs across multiple Kubernetes clusters
- **Resource Efficiency**: Calculate cluster efficiency and utilization metrics

#### Budget Management
- **Flexible Periods**: Support for daily, weekly, monthly, quarterly, and yearly budgets
- **Multi-Threshold Alerts**: Configure multiple alert thresholds per budget
- **Burn Rate Tracking**: Monitor spending velocity and project budget exhaustion
- **Projected Spend**: Forecast end-of-period spend based on current burn rate
- **Status Tracking**: Real-time budget status (On Track, At Risk, Over Budget)
- **Multi-Channel Notifications**: Email, Slack, webhooks, and logging
- **Historical Analysis**: Track budget performance over time
- **Auto-Adjustment**: Optional automatic budget adjustment based on trends

## Installation

### Prerequisites

- Python 3.9 or higher
- Cloud provider credentials (AWS, Azure, GCP)
- Kubecost installation (for Kubernetes cost analysis)
- SMTP server (optional, for email notifications)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Cloud Credentials Setup

#### AWS Configuration

Configure AWS credentials using the AWS CLI or environment variables:

```bash
# Using AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"
```

Grant the following IAM permissions:
- `ce:GetCostAndUsage`
- `ce:GetCostForecast`
- `ce:GetDimensionValues`
- `organizations:ListAccounts` (for multi-account)

#### Azure Configuration

Set up Azure credentials:

```bash
# Using Azure CLI
az login

# Or use service principal
export AZURE_TENANT_ID="your-tenant-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
```

Grant the following roles:
- `Cost Management Reader`
- `Billing Reader`

#### Google Cloud Configuration

Configure GCP credentials:

```bash
# Using gcloud CLI
gcloud auth application-default login

# Or set service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

Grant the following roles:
- `roles/billing.viewer`
- `roles/billing.accountCostViewer`
- `roles/cloudasset.viewer`

#### Kubecost Configuration

Deploy Kubecost to your Kubernetes cluster:

```bash
# Using Helm
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost --create-namespace

# Get Kubecost URL
kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090
```

## Quick Start

### Command-Line Interface

The platform provides a comprehensive CLI for all operations:

```bash
# View costs for the last month grouped by service
python -m finops_cost_management.finops_cli cost \
  --period month \
  --group-by service

# Detect cost anomalies in the last 30 days
python -m finops_cost_management.finops_cli anomalies \
  --days 30 \
  --sensitivity 0.05

# Get optimization recommendations
python -m finops_cost_management.finops_cli optimize \
  --category compute \
  --min-savings 50

# Forecast costs for next 30 days
python -m finops_cost_management.finops_cli forecast \
  --days 30 \
  --output forecast.png

# Create a monthly budget
python -m finops_cost_management.finops_cli budget create \
  --name "Engineering Team" \
  --amount 10000 \
  --period monthly \
  --threshold 0.8 \
  --threshold 0.9

# Check budgets and send alerts
python -m finops_cost_management.finops_cli budget check

# Analyze Kubernetes costs
python -m finops_cost_management.finops_cli k8s \
  --kubecost-url http://localhost:9090 \
  --group-by namespace

# Export cost data
python -m finops_cost_management.finops_cli export \
  --format csv \
  --output costs.csv \
  --days 90
```

### Python API

Use the platform programmatically in your applications:

```python
from finops_cost_management import (
    CostAggregator,
    AnomalyDetector,
    CostOptimizer,
    CostForecaster,
    BudgetManager,
    K8sCostAnalyzer,
)

# Initialize cost aggregator
aggregator = CostAggregator()

# Get costs for a date range
costs = aggregator.get_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
    providers=[CloudProvider.AWS],
)

# Detect anomalies
detector = AnomalyDetector(aggregator)
anomalies = detector.detect_anomalies(days=30)

# Get optimization recommendations
optimizer = CostOptimizer(aggregator)
recommendations = optimizer.get_recommendations(
    categories=["compute", "storage"],
    min_savings=50.0,
)

# Forecast future costs
forecaster = CostForecaster(aggregator)
forecast = forecaster.forecast_costs(days=30)

# Manage budgets
budget_manager = BudgetManager(aggregator)
budget = budget_manager.create_budget(
    BudgetConfig(
        name="Q1 Budget",
        amount=50000.0,
        period=BudgetPeriod.QUARTERLY,
        alert_thresholds=[0.5, 0.8, 1.0],
    )
)

# Analyze Kubernetes costs
k8s_analyzer = K8sCostAnalyzer(
    KubecostConfig(
        kubecost_url="http://localhost:9090",
        cluster_name="production",
    )
)
namespace_costs = k8s_analyzer.get_namespace_costs(
    "2024-01-01",
    "2024-01-31"
)
```

## Configuration

### Cost Aggregator Configuration

The cost aggregator automatically uses cloud provider credentials from environment variables. No additional configuration required.

```python
# Advanced configuration
aggregator = CostAggregator()

# Filter by tags
costs = aggregator.get_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
    filters={
        "tags": {"Environment": "Production"},
        "service": "EC2",
    }
)
```

### Anomaly Detector Configuration

```python
from finops_cost_management import AnomalyDetector, AnomalyConfig

config = AnomalyConfig(
    contamination=0.05,  # Expected anomaly rate (5%)
    min_cost_threshold=10.0,  # Minimum cost to flag
    detection_methods=["isolation_forest", "statistical"],
    lookback_days=60,
)

detector = AnomalyDetector(aggregator, config=config)
```

### Cost Optimizer Configuration

```python
from finops_cost_management import CostOptimizer, OptimizerConfig

config = OptimizerConfig(
    min_savings_threshold=50.0,  # Minimum monthly savings
    analysis_period_days=30,
    include_categories=["compute", "storage", "database"],
    confidence_level=0.8,
)

optimizer = CostOptimizer(aggregator, config=config)
```

### Cost Forecaster Configuration

```python
from finops_cost_management import CostForecaster, ForecastConfig

config = ForecastConfig(
    forecast_days=30,
    model_type="auto",  # auto, prophet, or linear
    confidence_interval=0.95,
    include_seasonality=True,
)

forecaster = CostForecaster(aggregator, config=config)
```

### Kubecost Configuration

```python
from finops_cost_management import K8sCostAnalyzer, KubecostConfig

config = KubecostConfig(
    kubecost_url="http://kubecost.example.com:9090",
    cluster_name="production",
    api_key="your-api-key",  # Optional
    timeout=30,
    verify_ssl=True,
)

analyzer = K8sCostAnalyzer(config)
```

### Budget Configuration

```python
from finops_cost_management import BudgetConfig, BudgetPeriod

config = BudgetConfig(
    name="Engineering Monthly Budget",
    amount=10000.0,
    period=BudgetPeriod.MONTHLY,
    alert_thresholds=[0.5, 0.8, 0.9, 1.0],
    notification_channels=[
        "email:team@example.com",
        "slack:https://hooks.slack.com/services/...",
        "webhook:https://api.example.com/alerts",
    ],
    filters={
        "tags": {"Team": "Engineering"},
    },
    notification_cooldown=3600,  # 1 hour between alerts
)
```

## Cost Aggregation

### Multi-Cloud Cost Retrieval

Get costs across all cloud providers:

```python
from finops_cost_management import CostAggregator, CloudProvider

aggregator = CostAggregator()

# Get all costs
all_costs = aggregator.get_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
)

# Get costs for specific provider
aws_costs = aggregator.get_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
    providers=[CloudProvider.AWS],
)

# Get daily aggregated costs
daily_costs = aggregator.get_daily_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
)
print(daily_costs)  # {date: total_cost}
```

### Cost Grouping and Filtering

```python
# Group by service
costs = aggregator.get_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
)

by_service = {}
for cost in costs:
    by_service[cost.service] = by_service.get(cost.service, 0) + cost.cost

# Group by region
by_region = {}
for cost in costs:
    by_region[cost.region] = by_region.get(cost.region, 0) + cost.cost

# Filter by tags
tagged_costs = [
    c for c in costs
    if c.tags.get("Environment") == "Production"
]
```

### AWS-Specific Features

```python
# Get EC2 costs by instance type
ec2_costs = aggregator.get_aws_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
    group_by=["SERVICE", "USAGE_TYPE"],
    filter={
        "SERVICE": ["Amazon Elastic Compute Cloud - Compute"]
    }
)

# Get costs by account (for Organizations)
account_costs = aggregator.get_aws_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
    group_by=["LINKED_ACCOUNT"],
)
```

### Azure-Specific Features

```python
# Get costs by resource group
rg_costs = aggregator.get_azure_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
    scope="resourceGroups/production",
)

# Get costs by meter category
meter_costs = aggregator.get_azure_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
    group_by="meterCategory",
)
```

### GCP-Specific Features

```python
# Get costs by project
project_costs = aggregator.get_gcp_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
    group_by="project.id",
)

# Get costs by SKU
sku_costs = aggregator.get_gcp_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
    group_by="sku.description",
)
```

## Anomaly Detection

### Basic Anomaly Detection

```python
from finops_cost_management import AnomalyDetector

detector = AnomalyDetector(aggregator)

# Detect anomalies in last 30 days
anomalies = detector.detect_anomalies(days=30)

for anomaly in anomalies:
    print(f"Anomaly detected on {anomaly.date}")
    print(f"  Service: {anomaly.service}")
    print(f"  Expected: ${anomaly.expected_cost:.2f}")
    print(f"  Actual: ${anomaly.actual_cost:.2f}")
    print(f"  Impact: ${anomaly.cost_impact:.2f}")
    print(f"  Severity: {anomaly.severity.value}")
```

### Configuring Detection Sensitivity

```python
from finops_cost_management import AnomalyConfig

# High sensitivity (detect smaller anomalies)
config = AnomalyConfig(
    contamination=0.1,  # Expect 10% anomalies
    min_cost_threshold=5.0,
)
detector = AnomalyDetector(aggregator, config=config)

# Low sensitivity (only large anomalies)
config = AnomalyConfig(
    contamination=0.01,  # Expect 1% anomalies
    min_cost_threshold=100.0,
)
detector = AnomalyDetector(aggregator, config=config)
```

### Provider-Specific Anomaly Detection

```python
# Detect anomalies only in AWS
aws_anomalies = detector.detect_anomalies(
    days=30,
    providers=[CloudProvider.AWS],
)

# Detect anomalies in specific service
ec2_anomalies = [
    a for a in anomalies
    if a.service == "EC2"
]
```

### Anomaly Analysis

```python
# Group anomalies by service
by_service = {}
for anomaly in anomalies:
    if anomaly.service not in by_service:
        by_service[anomaly.service] = []
    by_service[anomaly.service].append(anomaly)

# Calculate total impact
total_impact = sum(a.cost_impact for a in anomalies)

# Filter by severity
critical_anomalies = [
    a for a in anomalies
    if a.severity == AnomalySeverity.CRITICAL
]
```

## Optimization Recommendations

### Getting Recommendations

```python
from finops_cost_management import CostOptimizer

optimizer = CostOptimizer(aggregator)

# Get all recommendations
recommendations = optimizer.get_recommendations()

for rec in recommendations:
    print(f"Recommendation: {rec.recommendation}")
    print(f"  Resource: {rec.resource_id}")
    print(f"  Category: {rec.category.value}")
    print(f"  Current Cost: ${rec.current_cost:.2f}/mo")
    print(f"  Savings: ${rec.estimated_monthly_savings:.2f}/mo")
    print(f"  Priority: {rec.priority.value}")
    print(f"  Effort: {rec.implementation_effort}")
```

### Filtering Recommendations

```python
# Get only compute recommendations
compute_recs = optimizer.get_recommendations(
    categories=["compute"],
)

# Get recommendations with minimum savings
high_value_recs = optimizer.get_recommendations(
    min_savings=100.0,
)

# Get recommendations for specific provider
aws_recs = optimizer.get_recommendations(
    providers=[CloudProvider.AWS],
)
```

### Recommendation Categories

The optimizer provides recommendations in these categories:

#### Compute Optimization
- Idle instance detection and termination
- Instance rightsizing (downsize oversized instances)
- Reserved Instance and Savings Plan opportunities
- Spot instance migration for fault-tolerant workloads
- Auto Scaling configuration improvements

#### Storage Optimization
- Unused volume detection and deletion
- Storage lifecycle policies for infrequent access
- Snapshot cleanup for old/unused snapshots
- Storage tier optimization (e.g., gp3 to st1)
- Archive storage for long-term retention

#### Network Optimization
- Data transfer cost reduction
- VPC endpoint usage for AWS services
- Content delivery network (CDN) usage
- Regional data transfer optimization
- NAT Gateway cost optimization

#### Database Optimization
- Idle database instance detection
- Database rightsizing based on metrics
- Read replica optimization
- Reserved database instance purchases
- Database storage optimization

### Prioritizing Recommendations

```python
# Sort by potential savings
sorted_recs = sorted(
    recommendations,
    key=lambda r: r.estimated_monthly_savings,
    reverse=True,
)

# Filter by priority
high_priority = [
    r for r in recommendations
    if r.priority in [Priority.HIGH, Priority.CRITICAL]
]

# Filter by implementation effort
quick_wins = [
    r for r in recommendations
    if r.implementation_effort == "low"
    and r.estimated_monthly_savings > 50
]
```

## Cost Forecasting

### Basic Forecasting

```python
from finops_cost_management import CostForecaster

forecaster = CostForecaster(aggregator)

# Forecast next 30 days
forecast = forecaster.forecast_costs(days=30)

print(f"Historical Total: ${forecast.historical_total:,.2f}")
print(f"Forecasted Total: ${forecast.forecasted_total:,.2f}")
print(f"Lower Bound: ${forecast.lower_bound_total:,.2f}")
print(f"Upper Bound: ${forecast.upper_bound_total:,.2f}")
print(f"Growth Rate: {forecast.growth_rate:.2%}")
print(f"Model: {forecast.model_type}")
```

### Model Selection

```python
from finops_cost_management import ForecastConfig

# Use Prophet for seasonal data
config = ForecastConfig(
    forecast_days=30,
    model_type="prophet",
    confidence_interval=0.95,
)
forecaster = CostForecaster(aggregator, config=config)

# Use linear regression for stable trends
config = ForecastConfig(
    forecast_days=30,
    model_type="linear",
    confidence_interval=0.90,
)
forecaster = CostForecaster(aggregator, config=config)

# Auto-select best model
config = ForecastConfig(
    forecast_days=30,
    model_type="auto",
)
forecaster = CostForecaster(aggregator, config=config)
```

### Visualizing Forecasts

```python
# Generate forecast chart
forecast = forecaster.forecast_costs(days=30)
forecaster.plot_forecast(forecast, "forecast.png")
```

The chart includes:
- Historical actual costs
- Forecasted costs
- Confidence interval bands
- Trend line
- Seasonal patterns (if detected)

### Provider-Specific Forecasting

```python
# Forecast AWS costs only
aws_forecast = forecaster.forecast_costs(
    days=30,
    providers=[CloudProvider.AWS],
)

# Forecast by service
ec2_costs = [c for c in aggregator.get_costs(...) if c.service == "EC2"]
# Build custom forecast for EC2 service
```

### Analyzing Forecast Results

```python
forecast = forecaster.forecast_costs(days=30)

# Calculate forecast accuracy
if forecast.forecasted_total > forecast.historical_total:
    growth = forecast.forecasted_total - forecast.historical_total
    print(f"Expected growth: ${growth:,.2f}")

# Budget planning based on forecast
recommended_budget = forecast.upper_bound_total * 1.1  # 10% buffer
print(f"Recommended budget: ${recommended_budget:,.2f}")

# Risk assessment
uncertainty = forecast.upper_bound_total - forecast.lower_bound_total
if uncertainty > forecast.forecasted_total * 0.3:
    print("Warning: High forecast uncertainty")
```

## Kubernetes Cost Attribution

### Namespace Cost Analysis

```python
from finops_cost_management import K8sCostAnalyzer, KubecostConfig

# Configure analyzer
config = KubecostConfig(
    kubecost_url="http://localhost:9090",
    cluster_name="production",
)
analyzer = K8sCostAnalyzer(config)

# Get namespace costs
namespace_costs = analyzer.get_namespace_costs(
    start_date="2024-01-01",
    end_date="2024-01-31",
)

for cost in namespace_costs:
    print(f"Namespace: {cost.namespace}")
    print(f"  CPU: ${cost.cpu_cost:.2f}")
    print(f"  Memory: ${cost.memory_cost:.2f}")
    print(f"  Storage: ${cost.storage_cost:.2f}")
    print(f"  Network: ${cost.network_cost:.2f}")
    print(f"  Total: ${cost.total_cost:.2f}")
```

### Pod-Level Cost Breakdown

```python
# Get pod costs for a namespace
pod_costs = analyzer.get_pod_costs(
    namespace="production",
    start_date="2024-01-01",
    end_date="2024-01-31",
)

for cost in pod_costs:
    print(f"Pod: {cost.pod}")
    print(f"  Container: {cost.container}")
    print(f"  CPU Cores: {cost.cpu_cores:.2f}")
    print(f"  Memory GB: {cost.memory_gb:.2f}")
    print(f"  Total Cost: ${cost.total_cost:.2f}")
```

### Label-Based Cost Allocation

```python
# Get costs by team label
team_costs = analyzer.get_costs_by_label(
    label_key="team",
    start_date="2024-01-01",
    end_date="2024-01-31",
)

for team, cost in team_costs.items():
    print(f"Team {team}: ${cost:,.2f}")

# Get costs for specific label value
backend_costs = analyzer.get_costs_by_label(
    label_key="app",
    label_value="backend",
    start_date="2024-01-01",
    end_date="2024-01-31",
)
```

### Idle Resource Detection

```python
# Identify idle resources with 20% utilization threshold
idle_resources = analyzer.identify_idle_resources(
    threshold=0.2,
    start_date="2024-01-01",
    end_date="2024-01-31",
)

for resource in idle_resources:
    print(f"Idle Resource: {resource.namespace}/{resource.pod}")
    print(f"  Type: {resource.resource_type}")
    print(f"  Allocated: {resource.allocated:.2f}")
    print(f"  Used: {resource.used:.2f}")
    print(f"  Utilization: {resource.utilization:.1f}%")
    print(f"  Waste Cost: ${resource.waste_cost:.2f}")
    print(f"  Recommendation: {resource.recommendation}")
```

### Cost Allocation by Dimension

```python
# Allocate costs by team label
allocation = analyzer.get_cost_allocation(
    allocation_key="team",
    start_date="2024-01-01",
    end_date="2024-01-31",
    allocation_type="label",
)

print(f"Dimension: {allocation.dimension}")
print(f"Total Cost: ${allocation.total_cost:,.2f}")
print(f"Unallocated: ${allocation.unallocated_cost:,.2f}")

for value, cost in allocation.allocations.items():
    percentage = (cost / allocation.total_cost) * 100
    print(f"  {value}: ${cost:,.2f} ({percentage:.1f}%)")
```

### Cluster Efficiency Analysis

```python
# Get cluster efficiency metrics
efficiency = analyzer.get_cluster_efficiency(
    start_date="2024-01-01",
    end_date="2024-01-31",
)

print(f"Cluster: {efficiency['cluster']}")
print(f"Total Cost: ${efficiency['total_cost']:,.2f}")
print(f"CPU Utilization: {efficiency['avg_cpu_utilization']:.1%}")
print(f"Memory Utilization: {efficiency['avg_memory_utilization']:.1%}")
print(f"Idle Resources: {efficiency['idle_resource_count']}")
print(f"Estimated Waste: ${efficiency['estimated_waste']:,.2f}")
print(f"Efficiency Score: {efficiency['efficiency_score']:.1%}")
print(f"Potential Savings: ${efficiency['potential_savings']:,.2f}")
```

### Multi-Cluster Management

```python
# Analyze multiple clusters
clusters = [
    KubecostConfig(
        kubecost_url="http://prod-kubecost:9090",
        cluster_name="production",
    ),
    KubecostConfig(
        kubecost_url="http://staging-kubecost:9090",
        cluster_name="staging",
    ),
]

for config in clusters:
    analyzer = K8sCostAnalyzer(config)
    costs = analyzer.get_namespace_costs("2024-01-01", "2024-01-31")
    total = sum(c.total_cost for c in costs)
    print(f"{config.cluster_name}: ${total:,.2f}")
```

## Budget Management

### Creating Budgets

```python
from finops_cost_management import (
    BudgetManager,
    BudgetConfig,
    BudgetPeriod,
)

manager = BudgetManager(aggregator)

# Create monthly budget
config = BudgetConfig(
    name="Engineering Monthly Budget",
    amount=10000.0,
    period=BudgetPeriod.MONTHLY,
    alert_thresholds=[0.5, 0.8, 0.9, 1.0],
    notification_channels=[
        "email:team@example.com",
        "log",
    ],
)
budget = manager.create_budget(config)

print(f"Budget ID: {budget.id}")
print(f"Status: {budget.status.value}")
```

### Listing and Managing Budgets

```python
# List all budgets
budgets = manager.list_budgets()

# Filter by status
at_risk_budgets = manager.list_budgets(
    status=BudgetStatus.AT_RISK
)

# Get specific budget
budget = manager.get_budget(budget_id)

# Update budget
budget.current_spend = 5000.0
manager.update_budget(budget)

# Delete budget
manager.delete_budget(budget_id)
```

### Budget Status and Metrics

```python
budget = manager.get_budget(budget_id)

# Get usage metrics
print(f"Current Spend: ${budget.current_spend:,.2f}")
print(f"Budget Amount: ${budget.config.amount:,.2f}")
print(f"Percentage Used: {budget.get_percentage_used():.1f}%")
print(f"Remaining: ${budget.get_remaining_budget():,.2f}")

# Get projections
print(f"Burn Rate: ${budget.burn_rate:.2f}/day")
print(f"Days Remaining: {budget.days_remaining}")
print(f"Projected Spend: ${budget.projected_spend:,.2f}")
print(f"Status: {budget.status.value}")
```

### Checking Budgets and Alerts

```python
# Check all budgets and generate alerts
alerts = manager.check_budgets()

for alert in alerts:
    print(f"Alert: {alert.budget_name}")
    print(f"  Threshold: {alert.threshold:.0%}")
    print(f"  Current: ${alert.current_spend:,.2f}")
    print(f"  Budget: ${alert.budget_amount:,.2f}")
    print(f"  Status: {alert.status.value}")
    print(f"  Message: {alert.message}")

    # Send alert
    manager.send_alert(alert)
```

### Notification Channels

Configure multiple notification channels:

```python
# Email notifications
config = BudgetConfig(
    name="Budget",
    amount=10000.0,
    period=BudgetPeriod.MONTHLY,
    notification_channels=[
        "email:admin@example.com",
    ],
)

# Slack notifications
config.notification_channels.append(
    "slack:https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
)

# Generic webhook
config.notification_channels.append(
    "webhook:https://api.example.com/alerts"
)

# Log only (default)
config.notification_channels.append("log")
```

### Budget Summary and Reporting

```python
# Get overall budget summary
summary = manager.get_budget_summary()

print(f"Total Budgets: {summary['total_budgets']}")
print(f"Total Allocated: ${summary['total_allocated']:,.2f}")
print(f"Total Spent: ${summary['total_spent']:,.2f}")
print(f"Total Remaining: ${summary['total_remaining']:,.2f}")
print(f"Utilization: {summary['utilization_percentage']:.1f}%")

# Status breakdown
for status, count in summary['status_breakdown'].items():
    print(f"  {status}: {count}")

# Get budget history
history = manager.get_budget_history(budget_id, limit=12)

for record in history:
    print(f"Period: {record.period_start} to {record.period_end}")
    print(f"  Budgeted: ${record.budgeted_amount:,.2f}")
    print(f"  Actual: ${record.actual_spend:,.2f}")
    print(f"  Variance: ${record.variance:,.2f} ({record.variance_percentage:.1f}%)")  # noqa: E501
```

## CLI Reference

### Global Options

```bash
# Enable debug logging
python -m finops_cost_management.finops_cli --debug <command>

# Show version
python -m finops_cost_management.finops_cli --version

# Show help
python -m finops_cost_management.finops_cli --help
```

### Cost Command

View multi-cloud costs with flexible grouping and filtering:

```bash
# Basic usage
python -m finops_cost_management.finops_cli cost

# Specify provider
python -m finops_cost_management.finops_cli cost --provider aws

# Specify time period
python -m finops_cost_management.finops_cli cost --period week
python -m finops_cost_management.finops_cli cost --period month
python -m finops_cost_management.finops_cli cost --period quarter

# Custom date range
python -m finops_cost_management.finops_cli cost \
  --period custom \
  --start-date 2024-01-01 \
  --end-date 2024-01-31

# Group by different dimensions
python -m finops_cost_management.finops_cli cost --group-by provider
python -m finops_cost_management.finops_cli cost --group-by service
python -m finops_cost_management.finops_cli cost --group-by region
python -m finops_cost_management.finops_cli cost --group-by tag --tag-key team

# Output formats
python -m finops_cost_management.finops_cli cost --format table
python -m finops_cost_management.finops_cli cost --format json
python -m finops_cost_management.finops_cli cost --format csv --output costs.csv
```

### Anomalies Command

Detect cost anomalies using ML algorithms:

```bash
# Basic usage
python -m finops_cost_management.finops_cli anomalies

# Specify provider and time range
python -m finops_cost_management.finops_cli anomalies \
  --provider aws \
  --days 30

# Adjust sensitivity
python -m finops_cost_management.finops_cli anomalies \
  --sensitivity 0.05 \
  --min-cost 10

# JSON output
python -m finops_cost_management.finops_cli anomalies --format json
```

### Optimize Command

Get actionable cost optimization recommendations:

```bash
# Basic usage
python -m finops_cost_management.finops_cli optimize

# Filter by category
python -m finops_cost_management.finops_cli optimize --category compute
python -m finops_cost_management.finops_cli optimize --category storage
python -m finops_cost_management.finops_cli optimize --category network
python -m finops_cost_management.finops_cli optimize --category database

# Set minimum savings threshold
python -m finops_cost_management.finops_cli optimize \
  --min-savings 100

# Specific provider
python -m finops_cost_management.finops_cli optimize \
  --provider aws \
  --category compute

# JSON output
python -m finops_cost_management.finops_cli optimize --format json
```

### Forecast Command

Forecast future costs using time-series models:

```bash
# Basic usage
python -m finops_cost_management.finops_cli forecast

# Specify forecast period
python -m finops_cost_management.finops_cli forecast --days 30
python -m finops_cost_management.finops_cli forecast --days 90

# Select model
python -m finops_cost_management.finops_cli forecast --model prophet
python -m finops_cost_management.finops_cli forecast --model linear
python -m finops_cost_management.finops_cli forecast --model auto

# Set confidence interval
python -m finops_cost_management.finops_cli forecast --confidence 0.95

# Generate chart
python -m finops_cost_management.finops_cli forecast \
  --days 30 \
  --output forecast.png

# Specific provider
python -m finops_cost_management.finops_cli forecast \
  --provider aws \
  --days 60
```

### Budget Commands

Manage budgets and alerts:

```bash
# Create budget
python -m finops_cost_management.finops_cli budget create \
  --name "Engineering Team" \
  --amount 10000 \
  --period monthly \
  --threshold 0.8 \
  --threshold 0.9 \
  --channel "email:team@example.com" \
  --channel "log"

# List budgets
python -m finops_cost_management.finops_cli budget list
python -m finops_cost_management.finops_cli budget list --status at_risk
python -m finops_cost_management.finops_cli budget list --format json

# Check budgets and send alerts
python -m finops_cost_management.finops_cli budget check

# Get budget summary
python -m finops_cost_management.finops_cli budget summary
```

### K8s Command

Analyze Kubernetes costs with Kubecost:

```bash
# Basic usage (requires Kubecost)
python -m finops_cost_management.finops_cli k8s

# Specify Kubecost URL and cluster
python -m finops_cost_management.finops_cli k8s \
  --kubecost-url http://kubecost.example.com:9090 \
  --cluster production

# Group by namespace or pod
python -m finops_cost_management.finops_cli k8s --group-by namespace
python -m finops_cost_management.finops_cli k8s --group-by pod

# Costs by label
python -m finops_cost_management.finops_cli k8s \
  --group-by label \
  --label-key team

# Time period
python -m finops_cost_management.finops_cli k8s --period today
python -m finops_cost_management.finops_cli k8s --period week
python -m finops_cost_management.finops_cli k8s --period month

# Identify idle resources
python -m finops_cost_management.finops_cli k8s \
  --idle \
  --threshold 0.2
```

### Export Command

Export cost data to various formats:

```bash
# Export to JSON
python -m finops_cost_management.finops_cli export \
  --format json \
  --output costs.json \
  --days 30

# Export to CSV
python -m finops_cost_management.finops_cli export \
  --format csv \
  --output costs.csv \
  --days 90

# Export to Excel
python -m finops_cost_management.finops_cli export \
  --format excel \
  --output costs.xlsx \
  --days 365

# Specific provider
python -m finops_cost_management.finops_cli export \
  --format csv \
  --output aws_costs.csv \
  --provider aws \
  --days 30
```

## Protocol Integration

### P-CLOUD-VALIDATION Protocol

Validate cloud resource configurations for cost efficiency:

```python
from finops_cost_management import CostOptimizer

optimizer = CostOptimizer(aggregator)

# Get all recommendations
recommendations = optimizer.get_recommendations()

# Validate configurations
for rec in recommendations:
    if rec.category == OptimizationCategory.COMPUTE:
        # Validate compute resource sizes
        print(f"VALIDATION: {rec.recommendation}")
    elif rec.category == OptimizationCategory.STORAGE:
        # Validate storage configurations
        print(f"VALIDATION: {rec.recommendation}")
```

### P-FINOPS-COST-MONITOR Protocol

Continuous cost monitoring with anomaly detection:

```python
from finops_cost_management import AnomalyDetector, BudgetManager

# Monitor for anomalies
detector = AnomalyDetector(aggregator)
anomalies = detector.detect_anomalies(days=1)

for anomaly in anomalies:
    print(f"ALERT: Cost anomaly in {anomaly.service}")
    print(f"  Impact: ${anomaly.cost_impact:.2f}")

# Monitor budgets
manager = BudgetManager(aggregator)
alerts = manager.check_budgets()

for alert in alerts:
    print(f"ALERT: Budget threshold reached")
    print(f"  Budget: {alert.budget_name}")
    print(f"  Usage: {alert.get_percentage_used():.1f}%")
    manager.send_alert(alert)
```

### P-OBSERVABILITY Protocol

Export cost metrics to monitoring systems:

```python
from prometheus_client import Gauge, Counter
import time

# Define Prometheus metrics
cost_gauge = Gauge(
    'cloud_cost_total',
    'Total cloud cost',
    ['provider', 'service', 'region']
)

anomaly_counter = Counter(
    'cost_anomalies_total',
    'Total cost anomalies detected',
    ['provider', 'severity']
)

# Export metrics periodically
while True:
    # Get current costs
    costs = aggregator.get_costs(
        start_date=datetime.now().date().isoformat(),
        end_date=datetime.now().date().isoformat(),
    )

    # Update Prometheus metrics
    for cost in costs:
        cost_gauge.labels(
            provider=cost.provider.value,
            service=cost.service,
            region=cost.region,
        ).set(cost.cost)

    # Check for anomalies
    anomalies = detector.detect_anomalies(days=1)
    for anomaly in anomalies:
        anomaly_counter.labels(
            provider=anomaly.provider.value,
            severity=anomaly.severity.value,
        ).inc()

    time.sleep(300)  # Update every 5 minutes
```

## Troubleshooting

### Common Issues

#### AWS Credentials Not Found

**Problem**: `NoCredentialsError: Unable to locate credentials`

**Solution**:
```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"

# Verify credentials
aws sts get-caller-identity
```

#### Azure Authentication Failed

**Problem**: `ClientAuthenticationError: Authentication failed`

**Solution**:
```bash
# Login with Azure CLI
az login

# Or use service principal
az login --service-principal \
  --username $AZURE_CLIENT_ID \
  --password $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID

# Verify authentication
az account show
```

#### GCP Permission Denied

**Problem**: `PermissionDenied: 403 The caller does not have permission`

**Solution**:
```bash
# Authenticate with gcloud
gcloud auth application-default login

# Or set service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# Grant required roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT" \
  --role="roles/billing.viewer"
```

#### Kubecost Connection Failed

**Problem**: `ConnectionError: Failed to connect to Kubecost`

**Solution**:
```bash
# Verify Kubecost is running
kubectl get pods -n kubecost

# Port forward to access locally
kubectl port-forward -n kubecost \
  svc/kubecost-cost-analyzer 9090:9090

# Test connection
curl http://localhost:9090/model/allocation
```

#### Prophet Installation Failed

**Problem**: `ImportError: No module named 'prophet'`

**Solution**:
```bash
# Install Prophet with dependencies
pip install prophet

# On macOS, may need additional libraries
brew install cmake
pip install prophet
```

#### Insufficient Historical Data

**Problem**: `ValueError: Insufficient data for forecasting`

**Solution**: Ensure at least 14 days of historical cost data exists. For Prophet models, 30+ days recommended for better accuracy.

### Performance Optimization

#### Large Dataset Handling

For large cost datasets (1000+ records):

```python
# Use date range batching
from datetime import timedelta

def get_costs_batched(start_date, end_date, batch_days=7):
    costs = []
    current = start_date

    while current < end_date:
        batch_end = min(current + timedelta(days=batch_days), end_date)
        batch = aggregator.get_costs(
            start_date=current.isoformat(),
            end_date=batch_end.isoformat(),
        )
        costs.extend(batch)
        current = batch_end

    return costs
```

#### Caching Recommendations

Cache optimization recommendations:

```python
import pickle
from pathlib import Path

# Save recommendations
recommendations = optimizer.get_recommendations()
Path("recs.pkl").write_bytes(pickle.dumps(recommendations))

# Load cached recommendations
cached_recs = pickle.loads(Path("recs.pkl").read_bytes())
```

### Debugging

Enable debug logging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# All API calls and errors will be logged
```

Use CLI debug mode:

```bash
python -m finops_cost_management.finops_cli --debug cost
```

## Development

### Running Tests

```bash
# Run all tests
pytest test_finops_cost_management.py -v

# Run specific test class
pytest test_finops_cost_management.py::TestCostAggregator -v

# Run with coverage
pytest test_finops_cost_management.py --cov=finops_cost_management

# Run tests matching pattern
pytest test_finops_cost_management.py -k "anomaly" -v
```

### Code Quality

```bash
# Format code with Black
black finops_cost_management/

# Sort imports
isort finops_cost_management/

# Type checking
mypy finops_cost_management/ --ignore-missing-imports

# Linting
flake8 finops_cost_management/
pylint finops_cost_management/

# Security scanning
bandit -r finops_cost_management/
```

### Contributing

Contributions welcome! Please ensure:
- All tests pass
- Code coverage > 85%
- Type hints on all functions
- Docstrings in Google style
- Black formatting (88 char line length)
- No pylint/flake8 violations

## License

This project is part of devCrew_s1 and follows the repository's license terms.

## Support

For issues, questions, or feature requests, please file an issue in the devCrew_s1 repository referencing TOOL-FINOPS-001.

## Changelog

### Version 1.0.0

Initial release with complete feature set:
- Multi-cloud cost aggregation (AWS, Azure, GCP)
- ML-based anomaly detection
- Cost optimization recommendations
- Time-series cost forecasting
- Kubernetes cost attribution via Kubecost
- Budget management with multi-channel alerting
- Comprehensive CLI and Python API
- Protocol support (P-CLOUD-VALIDATION, P-FINOPS-COST-MONITOR, P-OBSERVABILITY)

## References

- AWS Cost Explorer API: https://docs.aws.amazon.com/cost-management/
- Azure Cost Management: https://docs.microsoft.com/azure/cost-management-billing/
- Google Cloud Billing: https://cloud.google.com/billing/docs
- Kubecost: https://www.kubecost.com/
- Prophet: https://facebook.github.io/prophet/
- FinOps Foundation: https://www.finops.org/
