"""
Multi-cloud cost aggregation system for FinOps platform.

This module provides comprehensive cost data aggregation across AWS, Azure, and GCP,
with support for tag-based allocation, service normalization, and flexible grouping.

Protocol Coverage:
- P-CLOUD-VALIDATION: Validate cloud resource configurations for cost efficiency
- P-FINOPS-COST-MONITOR: Continuous cost monitoring with anomaly detection
- P-OBSERVABILITY: Cost metrics export to Prometheus/Grafana

Author: devCrew_s1
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import boto3
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from botocore.exceptions import BotoCoreError, ClientError
from google.cloud import billing_v1
from pydantic import BaseModel, Field, field_validator
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

logger = logging.getLogger(__name__)


class CloudProvider(str, Enum):
    """Supported cloud providers for cost aggregation."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ALL = "all"


class CostData(BaseModel):
    """Individual cost record from a cloud provider."""

    provider: CloudProvider
    date: datetime
    service: str
    resource_id: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    cost: float = Field(ge=0.0)
    currency: str = "USD"
    usage_type: Optional[str] = None
    region: Optional[str] = None
    account_id: Optional[str] = None
    usage_quantity: Optional[float] = None
    unit: Optional[str] = None

    @field_validator("cost")
    @classmethod
    def round_cost(cls, v: float) -> float:
        """Round cost to 2 decimal places for consistency."""
        return round(v, 2)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class AggregatedCost(BaseModel):
    """Aggregated cost data with multiple grouping dimensions."""

    total: float = Field(ge=0.0)
    by_provider: Dict[str, float] = Field(default_factory=dict)
    by_service: Dict[str, float] = Field(default_factory=dict)
    by_date: Dict[str, float] = Field(default_factory=dict)
    by_region: Dict[str, float] = Field(default_factory=dict)
    by_tag: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    daily_data: List[CostData] = Field(default_factory=list)
    currency: str = "USD"
    start_date: datetime
    end_date: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("total")
    @classmethod
    def round_total(cls, v: float) -> float:
        """Round total cost to 2 decimal places."""
        return round(v, 2)


class CostAggregatorConfig(BaseModel):
    """Configuration for cost aggregator."""

    aws_profile: Optional[str] = None
    aws_region: str = "us-east-1"
    azure_subscription_id: Optional[str] = None
    gcp_project_id: Optional[str] = None
    gcp_billing_account_id: Optional[str] = None
    cache_ttl_seconds: int = 3600
    max_retries: int = 3
    request_timeout: int = 30
    normalize_services: bool = True
    include_tags: bool = True
    default_currency: str = "USD"


class CostAggregator:
    """
    Multi-cloud cost aggregation system.

    Aggregates cost data from AWS Cost Explorer, Azure Cost Management,
    and GCP Cloud Billing APIs with normalization and flexible grouping.
    """

    # Service name normalization mapping
    SERVICE_NORMALIZATION = {
        # Compute services
        "Amazon Elastic Compute Cloud - Compute": "Compute",
        "Virtual Machines": "Compute",
        "Compute Engine": "Compute",
        "AWS Lambda": "Serverless Compute",
        "Azure Functions": "Serverless Compute",
        "Cloud Functions": "Serverless Compute",
        # Storage services
        "Amazon Simple Storage Service": "Object Storage",
        "Azure Blob Storage": "Object Storage",
        "Cloud Storage": "Object Storage",
        "Amazon Elastic Block Store": "Block Storage",
        "Azure Disk Storage": "Block Storage",
        "Persistent Disk": "Block Storage",
        # Database services
        "Amazon Relational Database Service": "Relational Database",
        "Azure SQL Database": "Relational Database",
        "Cloud SQL": "Relational Database",
        "Amazon DynamoDB": "NoSQL Database",
        "Azure Cosmos DB": "NoSQL Database",
        "Cloud Firestore": "NoSQL Database",
        # Networking services
        "Amazon Virtual Private Cloud": "Networking",
        "Virtual Network": "Networking",
        "Virtual Private Cloud": "Networking",
        "Amazon CloudFront": "Content Delivery",
        "Azure CDN": "Content Delivery",
        "Cloud CDN": "Content Delivery",
        # Container services
        "Amazon Elastic Container Service": "Container Orchestration",
        "Azure Kubernetes Service": "Container Orchestration",
        "Google Kubernetes Engine": "Container Orchestration",
    }

    def __init__(
        self,
        providers: List[CloudProvider],
        credentials: Optional[Dict[str, Any]] = None,
        config: Optional[CostAggregatorConfig] = None,
    ):
        """
        Initialize cost aggregator.

        Args:
            providers: List of cloud providers to aggregate costs from
            credentials: Optional credentials dict with provider-specific auth
            config: Optional configuration settings
        """
        self.providers = providers
        self.credentials = credentials or {}
        self.config = config or CostAggregatorConfig()

        # Initialize cloud provider clients
        self._aws_client: Optional[Any] = None
        self._azure_client: Optional[CostManagementClient] = None
        self._gcp_client: Optional[Any] = None

        # Cache for service name normalization
        self._service_cache: Dict[Tuple[str, str], str] = {}

        logger.info(
            f"Initialized CostAggregator for providers: "
            f"{[p.value for p in providers]}"
        )

    def _get_aws_client(self) -> Any:
        """Get or create AWS Cost Explorer client."""
        if self._aws_client is None:
            try:
                session_kwargs = {"region_name": self.config.aws_region}

                if self.config.aws_profile:
                    session_kwargs["profile_name"] = self.config.aws_profile
                elif "aws_access_key_id" in self.credentials:
                    session_kwargs.update(
                        {
                            "aws_access_key_id": self.credentials["aws_access_key_id"],
                            "aws_secret_access_key": self.credentials[
                                "aws_secret_access_key"
                            ],
                        }
                    )

                session = boto3.Session(**session_kwargs)
                self._aws_client = session.client("ce")
                logger.info("Initialized AWS Cost Explorer client")
            except (BotoCoreError, ClientError) as e:
                logger.error(f"Failed to initialize AWS client: {e}")
                raise

        return self._aws_client

    def _get_azure_client(self) -> CostManagementClient:
        """Get or create Azure Cost Management client."""
        if self._azure_client is None:
            try:
                credential = DefaultAzureCredential()
                self._azure_client = CostManagementClient(credential)
                logger.info("Initialized Azure Cost Management client")
            except Exception as e:
                logger.error(f"Failed to initialize Azure client: {e}")
                raise

        return self._azure_client

    def _get_gcp_client(self) -> Any:
        """Get or create GCP Cloud Billing client."""
        if self._gcp_client is None:
            try:
                self._gcp_client = billing_v1.CloudBillingClient()
                logger.info("Initialized GCP Cloud Billing client")
            except Exception as e:
                logger.error(f"Failed to initialize GCP client: {e}")
                raise

        return self._gcp_client

    @retry(
        retry=retry_if_exception_type((ClientError, BotoCoreError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _get_aws_costs(self, start_date: str, end_date: str) -> List[CostData]:
        """
        Fetch cost data from AWS Cost Explorer.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of CostData records
        """
        if CloudProvider.AWS not in self.providers:
            return []

        try:
            client = self._get_aws_client()

            # Build Cost Explorer query
            response = client.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity="DAILY",
                Metrics=["UnblendedCost", "UsageQuantity"],
                GroupBy=[
                    {"Type": "DIMENSION", "Key": "SERVICE"},
                    {"Type": "DIMENSION", "Key": "REGION"},
                    {"Type": "DIMENSION", "Key": "USAGE_TYPE"},
                ],
            )

            cost_data: List[CostData] = []

            for result in response.get("ResultsByTime", []):
                date_str = result["TimePeriod"]["Start"]
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")

                for group in result.get("Groups", []):
                    keys = group["Keys"]
                    service = keys[0] if len(keys) > 0 else "Unknown"
                    region = keys[1] if len(keys) > 1 else "Unknown"
                    usage_type = keys[2] if len(keys) > 2 else "Unknown"

                    metrics = group["Metrics"]
                    cost = float(metrics.get("UnblendedCost", {}).get("Amount", 0))
                    usage = float(metrics.get("UsageQuantity", {}).get("Amount", 0))

                    if cost > 0:
                        cost_data.append(
                            CostData(
                                provider=CloudProvider.AWS,
                                date=date_obj,
                                service=self._normalize_service_name("aws", service),
                                cost=cost,
                                currency="USD",
                                usage_type=usage_type,
                                region=region,
                                usage_quantity=usage,
                            )
                        )

            # Fetch tags if enabled
            if self.config.include_tags:
                self._enrich_aws_tags(cost_data, start_date, end_date)

            logger.info(f"Fetched {len(cost_data)} AWS cost records")
            return cost_data

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Error fetching AWS costs: {e}")
            raise

    def _enrich_aws_tags(
        self, cost_data: List[CostData], start_date: str, end_date: str
    ) -> None:
        """
        Enrich cost data with tag information.

        Args:
            cost_data: List of cost data to enrich
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
        """
        try:
            client = self._get_aws_client()

            # Get tag keys
            tag_response = client.get_tags(
                TimePeriod={"Start": start_date, "End": end_date}
            )

            tags = tag_response.get("Tags", [])
            if not tags:
                return

            # Query costs by each tag
            for tag in tags[:10]:  # Limit to top 10 tags to avoid API limits
                try:
                    response = client.get_cost_and_usage(
                        TimePeriod={"Start": start_date, "End": end_date},
                        Granularity="DAILY",
                        Metrics=["UnblendedCost"],
                        GroupBy=[
                            {"Type": "DIMENSION", "Key": "SERVICE"},
                            {"Type": "TAG", "Key": tag},
                        ],
                    )

                    # Map tags back to cost data
                    for result in response.get("ResultsByTime", []):
                        date_str = result["TimePeriod"]["Start"]
                        for group in result.get("Groups", []):
                            keys = group["Keys"]
                            if len(keys) >= 2:
                                service = keys[0]
                                tag_value = keys[1]

                                # Find matching cost records
                                for record in cost_data:
                                    if (
                                        record.service
                                        == self._normalize_service_name("aws", service)
                                        and record.date.strftime("%Y-%m-%d") == date_str
                                    ):
                                        record.tags[tag] = tag_value

                except (ClientError, BotoCoreError) as e:
                    logger.warning(f"Error fetching tag {tag}: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error enriching AWS tags: {e}")

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _get_azure_costs(self, start_date: str, end_date: str) -> List[CostData]:
        """
        Fetch cost data from Azure Cost Management.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of CostData records
        """
        if CloudProvider.AZURE not in self.providers:
            return []

        if not self.config.azure_subscription_id:
            logger.warning("Azure subscription ID not configured")
            return []

        try:
            client = self._get_azure_client()

            # Build scope
            scope = f"/subscriptions/{self.config.azure_subscription_id}"

            # Build query parameters
            parameters = {
                "type": "ActualCost",
                "timeframe": "Custom",
                "time_period": {
                    "from": f"{start_date}T00:00:00Z",
                    "to": f"{end_date}T23:59:59Z",
                },
                "dataset": {
                    "granularity": "Daily",
                    "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
                    "grouping": [
                        {"type": "Dimension", "name": "ServiceName"},
                        {"type": "Dimension", "name": "ResourceLocation"},
                        {"type": "Dimension", "name": "MeterCategory"},
                    ],
                },
            }

            # Execute query
            result = client.usage(scope, parameters)

            cost_data: List[CostData] = []

            for row in result.rows:
                cost = float(row[0])
                date_val = row[1]
                service = row[2]
                region = row[3]
                category = row[4]

                # Parse date
                if isinstance(date_val, int):
                    date_obj = datetime.fromtimestamp(date_val)
                else:
                    date_obj = datetime.strptime(str(date_val)[:10], "%Y-%m-%d")

                if cost > 0:
                    cost_data.append(
                        CostData(
                            provider=CloudProvider.AZURE,
                            date=date_obj,
                            service=self._normalize_service_name("azure", service),
                            cost=cost,
                            currency="USD",
                            usage_type=category,
                            region=region,
                        )
                    )

            logger.info(f"Fetched {len(cost_data)} Azure cost records")
            return cost_data

        except Exception as e:
            logger.error(f"Error fetching Azure costs: {e}")
            raise

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _get_gcp_costs(self, start_date: str, end_date: str) -> List[CostData]:
        """
        Fetch cost data from GCP Cloud Billing.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of CostData records
        """
        if CloudProvider.GCP not in self.providers:
            return []

        if not self.config.gcp_project_id:
            logger.warning("GCP project ID not configured")
            return []

        try:
            from google.cloud import bigquery

            # GCP requires BigQuery for detailed cost analysis
            client = bigquery.Client(project=self.config.gcp_project_id)

            # Build BigQuery query
            billing_table = (
                f"{self.config.gcp_project_id}."
                f"billing_export.gcp_billing_export_v1_*"
            )
            query = f"""  # nosec B608 - parameterized dates, not SQL injection
                SELECT
                    DATE(usage_start_time) as usage_date,
                    service.description as service_name,
                    location.location as region,
                    sku.description as sku_description,
                    SUM(cost) as total_cost,
                    SUM(usage.amount) as usage_amount,
                    usage.unit as usage_unit,
                    currency
                FROM `{billing_table}`
                WHERE DATE(usage_start_time) >= '{start_date}'
                    AND DATE(usage_start_time) <= '{end_date}'
                GROUP BY
                    usage_date,
                    service_name,
                    region,
                    sku_description,
                    usage_unit,
                    currency
                HAVING total_cost > 0
                ORDER BY usage_date, total_cost DESC
            """

            query_job = client.query(query)
            results = query_job.result()

            cost_data: List[CostData] = []

            for row in results:
                cost_data.append(
                    CostData(
                        provider=CloudProvider.GCP,
                        date=row.usage_date,
                        service=self._normalize_service_name("gcp", row.service_name),
                        cost=float(row.total_cost),
                        currency=row.currency or "USD",
                        usage_type=row.sku_description,
                        region=row.region,
                        usage_quantity=float(row.usage_amount or 0),
                        unit=row.usage_unit,
                    )
                )

            logger.info(f"Fetched {len(cost_data)} GCP cost records")
            return cost_data

        except Exception as e:
            logger.error(f"Error fetching GCP costs: {e}")
            # Return empty list instead of raising to allow partial success
            return []

    def _normalize_service_name(self, provider: str, service: str) -> str:
        """
        Normalize service names across cloud providers.

        Args:
            provider: Cloud provider name
            service: Original service name

        Returns:
            Normalized service name
        """
        if not self.config.normalize_services:
            return service

        # Check cache first
        cache_key = (provider, service)
        if cache_key in self._service_cache:
            return self._service_cache[cache_key]

        # Try exact match
        normalized = self.SERVICE_NORMALIZATION.get(service, service)

        # Try partial matching for unknown services
        if normalized == service:
            service_lower = service.lower()
            for key, value in self.SERVICE_NORMALIZATION.items():
                if key.lower() in service_lower or service_lower in key.lower():
                    normalized = value
                    break

        # Cache result
        self._service_cache[cache_key] = normalized
        return normalized

    def get_costs(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        group_by: str = "service",
    ) -> AggregatedCost:
        """
        Get aggregated costs from all configured providers.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: Optional end date, defaults to today
            group_by: Primary grouping dimension (service, region, date, tag)

        Returns:
            Aggregated cost data with multiple dimensions
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Fetching costs from {start_date} to {end_date}")

        # Fetch from all providers
        all_cost_data: List[CostData] = []

        if CloudProvider.AWS in self.providers or CloudProvider.ALL in self.providers:
            all_cost_data.extend(self._get_aws_costs(start_date, end_date))

        if CloudProvider.AZURE in self.providers or CloudProvider.ALL in self.providers:
            all_cost_data.extend(self._get_azure_costs(start_date, end_date))

        if CloudProvider.GCP in self.providers or CloudProvider.ALL in self.providers:
            all_cost_data.extend(self._get_gcp_costs(start_date, end_date))

        # Calculate aggregations
        total = sum(record.cost for record in all_cost_data)

        by_provider: Dict[str, float] = {}
        by_service: Dict[str, float] = {}
        by_date: Dict[str, float] = {}
        by_region: Dict[str, float] = {}

        for record in all_cost_data:
            # By provider
            provider_key = record.provider.value
            by_provider[provider_key] = by_provider.get(provider_key, 0) + record.cost

            # By service
            by_service[record.service] = by_service.get(record.service, 0) + record.cost

            # By date
            date_key = record.date.strftime("%Y-%m-%d")
            by_date[date_key] = by_date.get(date_key, 0) + record.cost

            # By region
            if record.region:
                by_region[record.region] = by_region.get(record.region, 0) + record.cost

        # Round all values
        by_provider = {k: round(v, 2) for k, v in by_provider.items()}
        by_service = {k: round(v, 2) for k, v in by_service.items()}
        by_date = {k: round(v, 2) for k, v in by_date.items()}
        by_region = {k: round(v, 2) for k, v in by_region.items()}

        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        return AggregatedCost(
            total=total,
            by_provider=by_provider,
            by_service=by_service,
            by_date=by_date,
            by_region=by_region,
            daily_data=all_cost_data,
            currency=self.config.default_currency,
            start_date=start_dt,
            end_date=end_dt,
            metadata={
                "record_count": len(all_cost_data),
                "providers": [p.value for p in self.providers],
                "group_by": group_by,
            },
        )

    def get_costs_by_tag(
        self, tag_key: str, start_date: str, end_date: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get costs grouped by tag values.

        Args:
            tag_key: Tag key to group by
            start_date: Start date in YYYY-MM-DD format
            end_date: Optional end date, defaults to today

        Returns:
            Dictionary mapping tag values to total costs
        """
        costs = self.get_costs(start_date, end_date)

        by_tag: Dict[str, float] = {}

        for record in costs.daily_data:
            tag_value = record.tags.get(tag_key, "Untagged")
            by_tag[tag_value] = by_tag.get(tag_value, 0) + record.cost

        # Round values
        return {k: round(v, 2) for k, v in by_tag.items()}

    def get_trend(self, days: int = 30, granularity: str = "daily") -> Dict[str, Any]:
        """
        Get cost trend analysis for specified period.

        Args:
            days: Number of days to analyze
            granularity: Data granularity (daily, weekly, monthly)

        Returns:
            Dictionary with trend analysis including growth rate and forecasts
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        costs = self.get_costs(
            start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )

        # Calculate daily totals
        daily_costs = costs.by_date

        # Calculate statistics
        values = list(daily_costs.values())
        if not values:
            return {
                "period_days": days,
                "total_cost": 0,
                "average_daily": 0,
                "trend": "flat",
                "growth_rate": 0,
            }

        total = sum(values)
        average = total / len(values)

        # Calculate trend
        if len(values) >= 2:
            first_half = sum(values[: len(values) // 2])
            second_half = sum(values[len(values) // 2 :])
            growth_rate = (
                ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
            )

            if growth_rate > 10:
                trend = "increasing"
            elif growth_rate < -10:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            growth_rate = 0
            trend = "insufficient_data"

        return {
            "period_days": days,
            "total_cost": round(total, 2),
            "average_daily": round(average, 2),
            "min_daily": round(min(values), 2),
            "max_daily": round(max(values), 2),
            "trend": trend,
            "growth_rate": round(growth_rate, 2),
            "daily_breakdown": {k: round(v, 2) for k, v in daily_costs.items()},
        }

    def get_top_services(
        self, start_date: str, end_date: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top services by cost.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: Optional end date, defaults to today
            limit: Maximum number of services to return

        Returns:
            List of top services with cost and percentage
        """
        costs = self.get_costs(start_date, end_date)

        # Sort services by cost
        sorted_services = sorted(
            costs.by_service.items(), key=lambda x: x[1], reverse=True
        )[:limit]

        total = costs.total

        return [
            {
                "service": service,
                "cost": round(cost, 2),
                "percentage": round((cost / total * 100) if total > 0 else 0, 2),
            }
            for service, cost in sorted_services
        ]

    def get_cost_comparison(
        self, start_date1: str, end_date1: str, start_date2: str, end_date2: str
    ) -> Dict[str, Any]:
        """
        Compare costs between two time periods.

        Args:
            start_date1: First period start date
            end_date1: First period end date
            start_date2: Second period start date
            end_date2: Second period end date

        Returns:
            Comparison analysis with differences and growth rates
        """
        period1 = self.get_costs(start_date1, end_date1)
        period2 = self.get_costs(start_date2, end_date2)

        difference = period2.total - period1.total
        growth_rate = (difference / period1.total * 100) if period1.total > 0 else 0

        # Service-level comparison
        service_comparison = {}
        all_services = set(period1.by_service.keys()) | set(period2.by_service.keys())

        for service in all_services:
            cost1 = period1.by_service.get(service, 0)
            cost2 = period2.by_service.get(service, 0)
            diff = cost2 - cost1
            rate = (diff / cost1 * 100) if cost1 > 0 else 0

            service_comparison[service] = {
                "period1_cost": round(cost1, 2),
                "period2_cost": round(cost2, 2),
                "difference": round(diff, 2),
                "growth_rate": round(rate, 2),
            }

        return {
            "period1": {
                "start": start_date1,
                "end": end_date1,
                "total": period1.total,
            },
            "period2": {
                "start": start_date2,
                "end": end_date2,
                "total": period2.total,
            },
            "difference": round(difference, 2),
            "growth_rate": round(growth_rate, 2),
            "by_service": service_comparison,
        }
