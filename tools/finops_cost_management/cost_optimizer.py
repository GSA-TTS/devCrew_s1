"""
Cost optimization recommendation engine for multi-cloud environments.

This module analyzes cloud resource usage patterns and provides actionable
recommendations to reduce costs through right-sizing, unused resource detection,
reserved instance analysis, spot instance opportunities, and storage optimization.

Supports AWS, Azure, and GCP with provider-specific optimization strategies.
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import boto3
import numpy as np
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class OptimizationCategory(str, Enum):
    """Categories of cost optimization recommendations."""

    RIGHT_SIZING = "right-sizing"
    UNUSED_RESOURCES = "unused-resources"
    RESERVED_INSTANCES = "reserved-instances"
    SPOT_INSTANCES = "spot-instances"
    STORAGE_OPTIMIZATION = "storage-optimization"


class ImpactLevel(str, Enum):
    """Impact level of implementing a recommendation."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskLevel(str, Enum):
    """Risk level associated with implementing a recommendation."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class OptimizerConfig(BaseModel):
    """Configuration for cost optimizer."""

    min_savings_threshold: float = Field(
        default=10.0, description="Minimum monthly $ savings to recommend"
    )
    utilization_threshold: float = Field(
        default=0.3, description="CPU/memory threshold for right-sizing"
    )
    idle_days_threshold: int = Field(
        default=7, description="Days to consider resource idle"
    )
    include_reserved_instances: bool = Field(
        default=True, description="Include reserved instance analysis"
    )
    include_spot_instances: bool = Field(
        default=True, description="Include spot instance opportunities"
    )
    lookback_days: int = Field(
        default=14, description="Days of historical data to analyze"
    )
    max_cpu_threshold: float = Field(
        default=0.7, description="Max CPU for right-sizing consideration"
    )
    max_memory_threshold: float = Field(
        default=0.7, description="Max memory for right-sizing consideration"
    )
    network_idle_threshold_mb: float = Field(
        default=1.0, description="Network MB/day threshold for idle detection"
    )

    @field_validator(
        "utilization_threshold", "max_cpu_threshold", "max_memory_threshold"
    )
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        return v


class OptimizationRecommendation(BaseModel):
    """A cost optimization recommendation."""

    resource_id: str
    resource_type: str
    provider: str
    category: OptimizationCategory
    current_config: Dict[str, Any]
    recommended_config: Dict[str, Any]
    estimated_savings: float = Field(description="Estimated monthly savings in USD")
    confidence: float = Field(description="Confidence score 0-1", ge=0.0, le=1.0)
    impact: ImpactLevel
    implementation_steps: List[str]
    risk_level: RiskLevel
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return v


class CostOptimizerError(Exception):
    """Base exception for cost optimizer operations."""

    pass


class CostOptimizer:
    """
    Cost optimization recommendation engine.

    Analyzes cloud resources across AWS, Azure, and GCP to identify
    cost-saving opportunities through various optimization strategies.
    """

    # AWS pricing data (simplified - production would use AWS Pricing API)
    AWS_PRICING = {
        "t2.micro": 0.0116,
        "t2.small": 0.023,
        "t2.medium": 0.0464,
        "t2.large": 0.0928,
        "t3.micro": 0.0104,
        "t3.small": 0.0208,
        "t3.medium": 0.0416,
        "t3.large": 0.0832,
        "m5.large": 0.096,
        "m5.xlarge": 0.192,
        "m5.2xlarge": 0.384,
        "c5.large": 0.085,
        "c5.xlarge": 0.17,
    }

    # Reserved instance discount percentages
    RI_DISCOUNT = {"1year_no_upfront": 0.30, "1year_partial": 0.35, "3year": 0.50}

    # Spot instance discount (approximate)
    SPOT_DISCOUNT = 0.70

    # Storage pricing (per GB/month)
    STORAGE_PRICING = {
        "aws": {"gp2": 0.10, "gp3": 0.08, "sc1": 0.015, "st1": 0.045},
        "azure": {"premium": 0.135, "standard": 0.05},
        "gcp": {"pd-standard": 0.04, "pd-ssd": 0.17, "pd-balanced": 0.10},
    }

    def __init__(
        self,
        config: Optional[OptimizerConfig] = None,
        providers: Optional[List[str]] = None,
    ):
        """
        Initialize cost optimizer.

        Args:
            config: Optimizer configuration
            providers: List of cloud providers to analyze (aws, azure, gcp)
        """
        self.config = config or OptimizerConfig()
        self.providers = providers or ["aws", "azure", "gcp"]
        self._aws_clients: Dict[str, Any] = {}
        self._azure_clients: Dict[str, Any] = {}
        self._gcp_clients: Dict[str, Any] = {}

        logger.info(f"CostOptimizer initialized for providers: {self.providers}")

    def _get_aws_client(self, service: str, region: str = "us-east-1") -> Any:
        """Get or create AWS client for service."""
        key = f"{service}_{region}"
        if key not in self._aws_clients:
            try:
                self._aws_clients[key] = boto3.client(service, region_name=region)
                logger.debug(f"Created AWS {service} client for {region}")
            except Exception as e:
                logger.error(f"Failed to create AWS {service} client: {e}")
                raise CostOptimizerError(f"AWS client creation failed: {e}") from e
        return self._aws_clients[key]

    def _get_azure_clients(
        self, subscription_id: str
    ) -> Tuple[ComputeManagementClient, MonitorManagementClient]:
        """Get or create Azure clients."""
        if subscription_id not in self._azure_clients:
            try:
                credential = DefaultAzureCredential()
                compute_client = ComputeManagementClient(credential, subscription_id)
                monitor_client = MonitorManagementClient(credential, subscription_id)
                self._azure_clients[subscription_id] = (compute_client, monitor_client)
                logger.debug(
                    f"Created Azure clients for subscription {subscription_id}"
                )
            except Exception as e:
                logger.error(f"Failed to create Azure clients: {e}")
                raise CostOptimizerError(f"Azure client creation failed: {e}") from e
        return self._azure_clients[subscription_id]

    def analyze(
        self, providers: Optional[List[str]] = None
    ) -> List[OptimizationRecommendation]:
        """
        Analyze all providers and generate optimization recommendations.

        Args:
            providers: List of providers to analyze (overrides init providers)

        Returns:
            List of optimization recommendations sorted by estimated savings
        """
        providers = providers or self.providers
        all_recommendations: List[OptimizationRecommendation] = []

        logger.info(f"Starting optimization analysis for providers: {providers}")

        for provider in providers:
            try:
                logger.info(f"Analyzing {provider}...")
                recommendations = self._analyze_provider(provider)
                all_recommendations.extend(recommendations)
                logger.info(
                    f"Found {len(recommendations)} recommendations for {provider}"
                )
            except Exception as e:
                logger.error(f"Error analyzing {provider}: {e}", exc_info=True)
                continue

        # Filter by minimum savings threshold
        filtered = [
            r
            for r in all_recommendations
            if r.estimated_savings >= self.config.min_savings_threshold
        ]

        # Sort by estimated savings (descending)
        filtered.sort(key=lambda x: x.estimated_savings, reverse=True)

        logger.info(
            f"Analysis complete. {len(filtered)} recommendations "
            f"(filtered from {len(all_recommendations)})"
        )

        return filtered

    def _analyze_provider(self, provider: str) -> List[OptimizationRecommendation]:
        """Analyze a single provider for all optimization categories."""
        recommendations: List[OptimizationRecommendation] = []

        # Right-sizing analysis
        recommendations.extend(self._analyze_right_sizing(provider))

        # Unused resource detection
        recommendations.extend(self._detect_unused_resources(provider))

        # Reserved instance analysis
        if self.config.include_reserved_instances:
            recommendations.extend(self._analyze_reserved_instances(provider))

        # Spot instance analysis
        if self.config.include_spot_instances:
            recommendations.extend(self._analyze_spot_instances(provider))

        # Storage optimization
        recommendations.extend(self._analyze_storage(provider))

        return recommendations

    def _analyze_right_sizing(self, provider: str) -> List[OptimizationRecommendation]:
        """Analyze instances for right-sizing opportunities."""
        recommendations: List[OptimizationRecommendation] = []

        if provider == "aws":
            recommendations.extend(self._analyze_aws_right_sizing())
        elif provider == "azure":
            recommendations.extend(self._analyze_azure_right_sizing())
        elif provider == "gcp":
            recommendations.extend(self._analyze_gcp_right_sizing())

        return recommendations

    def _analyze_aws_right_sizing(self) -> List[OptimizationRecommendation]:
        """Analyze AWS EC2 instances for right-sizing."""
        recommendations: List[OptimizationRecommendation] = []

        try:
            ec2 = self._get_aws_client("ec2")
            cloudwatch = self._get_aws_client("cloudwatch")

            # Get all running instances
            response = ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
            )

            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    instance_id = instance["InstanceId"]
                    instance_type = instance["InstanceType"]

                    # Get CPU utilization metrics
                    cpu_stats = self._get_aws_cpu_utilization(cloudwatch, instance_id)

                    if (
                        cpu_stats
                        and cpu_stats["average"] < self.config.utilization_threshold
                    ):
                        # Suggest smaller instance type
                        recommended_type = self._get_smaller_instance_type(
                            instance_type, "aws"
                        )

                        if recommended_type:
                            current_cost = (
                                self.AWS_PRICING.get(instance_type, 0.0) * 730
                            )
                            recommended_cost = (
                                self.AWS_PRICING.get(recommended_type, 0.0) * 730
                            )
                            savings = current_cost - recommended_cost

                            if savings > 0:
                                recommendation = OptimizationRecommendation(
                                    resource_id=instance_id,
                                    resource_type="ec2_instance",
                                    provider="aws",
                                    category=OptimizationCategory.RIGHT_SIZING,
                                    current_config={
                                        "instance_type": instance_type,
                                        "monthly_cost": round(current_cost, 2),
                                        "avg_cpu_utilization": round(
                                            cpu_stats["average"], 2
                                        ),
                                        "max_cpu_utilization": round(
                                            cpu_stats["max"], 2
                                        ),
                                    },
                                    recommended_config={
                                        "instance_type": recommended_type,
                                        "monthly_cost": round(recommended_cost, 2),
                                    },
                                    estimated_savings=round(savings, 2),
                                    confidence=self._calculate_confidence(cpu_stats),
                                    impact=self._determine_impact(savings),
                                    risk_level=RiskLevel.LOW,
                                    implementation_steps=[
                                        "1. Create AMI backup of current instance",
                                        f"2. Stop instance {instance_id}",
                                        f"3. Change instance type to "
                                        f"{recommended_type}",
                                        "4. Start instance and verify application "
                                        "functionality",
                                        "5. Monitor performance for 24-48 hours",
                                    ],
                                    metadata={
                                        "cpu_metrics": cpu_stats,
                                        "analysis_period_days": (
                                            self.config.lookback_days
                                        ),
                                    },
                                )
                                recommendations.append(recommendation)

        except Exception as e:
            logger.error(f"Error analyzing AWS right-sizing: {e}", exc_info=True)

        return recommendations

    def _analyze_azure_right_sizing(self) -> List[OptimizationRecommendation]:
        """Analyze Azure VMs for right-sizing."""
        recommendations: List[OptimizationRecommendation] = []

        # Placeholder for Azure implementation
        # In production, would use Azure Monitor to get VM metrics
        logger.debug("Azure right-sizing analysis not fully implemented")

        return recommendations

    def _analyze_gcp_right_sizing(self) -> List[OptimizationRecommendation]:
        """Analyze GCP instances for right-sizing."""
        recommendations: List[OptimizationRecommendation] = []

        # Placeholder for GCP implementation
        # In production, would use Cloud Monitoring API
        logger.debug("GCP right-sizing analysis not fully implemented")

        return recommendations

    def _detect_unused_resources(
        self, provider: str
    ) -> List[OptimizationRecommendation]:
        """Detect unused or idle resources."""
        recommendations: List[OptimizationRecommendation] = []

        if provider == "aws":
            recommendations.extend(self._detect_aws_unused_resources())
        elif provider == "azure":
            recommendations.extend(self._detect_azure_unused_resources())
        elif provider == "gcp":
            recommendations.extend(self._detect_gcp_unused_resources())

        return recommendations

    def _detect_aws_unused_resources(self) -> List[OptimizationRecommendation]:
        """Detect unused AWS resources."""
        recommendations: List[OptimizationRecommendation] = []

        # Detect unattached EBS volumes
        recommendations.extend(self._detect_aws_unattached_volumes())

        # Detect idle EC2 instances
        recommendations.extend(self._detect_aws_idle_instances())

        # Detect unused Elastic IPs
        recommendations.extend(self._detect_aws_unused_eips())

        return recommendations

    def _detect_aws_unattached_volumes(self) -> List[OptimizationRecommendation]:
        """Detect unattached EBS volumes."""
        recommendations: List[OptimizationRecommendation] = []

        try:
            ec2 = self._get_aws_client("ec2")
            response = ec2.describe_volumes(
                Filters=[{"Name": "status", "Values": ["available"]}]
            )

            for volume in response["Volumes"]:
                volume_id = volume["VolumeId"]
                size_gb = volume["Size"]
                volume_type = volume["VolumeType"]

                # Calculate monthly cost
                price_per_gb = self.STORAGE_PRICING["aws"].get(volume_type, 0.10)
                monthly_cost = size_gb * price_per_gb

                if monthly_cost >= self.config.min_savings_threshold:
                    recommendation = OptimizationRecommendation(
                        resource_id=volume_id,
                        resource_type="ebs_volume",
                        provider="aws",
                        category=OptimizationCategory.UNUSED_RESOURCES,
                        current_config={
                            "volume_type": volume_type,
                            "size_gb": size_gb,
                            "monthly_cost": round(monthly_cost, 2),
                            "status": "available",
                        },
                        recommended_config={"action": "delete_volume"},
                        estimated_savings=round(monthly_cost, 2),
                        confidence=0.95,
                        impact=self._determine_impact(monthly_cost),
                        risk_level=RiskLevel.MEDIUM,
                        implementation_steps=[
                            f"1. Verify volume {volume_id} is not needed",
                            "2. Create snapshot if data retention required",
                            f"3. Delete volume {volume_id}",
                            "4. Verify snapshot if created",
                        ],
                        metadata={
                            "create_time": (
                                volume.get("CreateTime", "").isoformat()
                                if volume.get("CreateTime")
                                else None
                            ),
                        },
                    )
                    recommendations.append(recommendation)

        except Exception as e:
            logger.error(f"Error detecting unattached volumes: {e}", exc_info=True)

        return recommendations

    def _detect_aws_idle_instances(self) -> List[OptimizationRecommendation]:
        """Detect idle EC2 instances."""
        recommendations: List[OptimizationRecommendation] = []

        try:
            ec2 = self._get_aws_client("ec2")
            cloudwatch = self._get_aws_client("cloudwatch")

            response = ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
            )

            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    instance_id = instance["InstanceId"]
                    instance_type = instance["InstanceType"]

                    # Check CPU and network activity
                    cpu_stats = self._get_aws_cpu_utilization(cloudwatch, instance_id)
                    network_stats = self._get_aws_network_utilization(
                        cloudwatch, instance_id
                    )

                    # Consider idle if very low CPU and network
                    is_idle = False
                    if cpu_stats and network_stats:
                        avg_cpu = cpu_stats["average"]
                        avg_network_mb = network_stats["average"] / (1024 * 1024)

                        if (
                            avg_cpu < 0.05
                            and avg_network_mb < self.config.network_idle_threshold_mb
                        ):
                            is_idle = True

                    if is_idle and cpu_stats:
                        monthly_cost = self.AWS_PRICING.get(instance_type, 0.0) * 730

                        recommendation = OptimizationRecommendation(
                            resource_id=instance_id,
                            resource_type="ec2_instance",
                            provider="aws",
                            category=OptimizationCategory.UNUSED_RESOURCES,
                            current_config={
                                "instance_type": instance_type,
                                "monthly_cost": round(monthly_cost, 2),
                                "avg_cpu": round(cpu_stats["average"] * 100, 2),
                                "avg_network_mb_day": round(avg_network_mb, 2),
                            },
                            recommended_config={
                                "action": "stop_or_terminate",
                            },
                            estimated_savings=round(monthly_cost, 2),
                            confidence=0.85,
                            impact=self._determine_impact(monthly_cost),
                            risk_level=RiskLevel.MEDIUM,
                            implementation_steps=[
                                f"1. Verify instance {instance_id} purpose",
                                "2. Check with application owner",
                                "3. Stop instance if temporary workload",
                                "4. Terminate if no longer needed",
                                "5. Monitor for impact on services",
                            ],
                            metadata={
                                "idle_days": self.config.idle_days_threshold,
                            },
                        )
                        recommendations.append(recommendation)

        except Exception as e:
            logger.error(f"Error detecting idle instances: {e}", exc_info=True)

        return recommendations

    def _detect_aws_unused_eips(self) -> List[OptimizationRecommendation]:
        """Detect unused Elastic IP addresses."""
        recommendations: List[OptimizationRecommendation] = []

        try:
            ec2 = self._get_aws_client("ec2")
            response = ec2.describe_addresses()

            for address in response["Addresses"]:
                # EIP is unused if not associated with an instance
                if "InstanceId" not in address:
                    allocation_id = address.get("AllocationId", "")
                    public_ip = address.get("PublicIp", "")

                    # Unused EIPs cost $0.005/hour = ~$3.65/month
                    monthly_cost = 0.005 * 730

                    recommendation = OptimizationRecommendation(
                        resource_id=allocation_id or public_ip,
                        resource_type="elastic_ip",
                        provider="aws",
                        category=OptimizationCategory.UNUSED_RESOURCES,
                        current_config={
                            "public_ip": public_ip,
                            "monthly_cost": round(monthly_cost, 2),
                            "status": "unassociated",
                        },
                        recommended_config={"action": "release_eip"},
                        estimated_savings=round(monthly_cost, 2),
                        confidence=0.99,
                        impact=ImpactLevel.LOW,
                        risk_level=RiskLevel.LOW,
                        implementation_steps=[
                            f"1. Verify EIP {public_ip} is not reserved for future use",
                            f"2. Release allocation {allocation_id}",
                            "3. Update DNS records if necessary",
                        ],
                    )
                    recommendations.append(recommendation)

        except Exception as e:
            logger.error(f"Error detecting unused EIPs: {e}", exc_info=True)

        return recommendations

    def _detect_azure_unused_resources(self) -> List[OptimizationRecommendation]:
        """Detect unused Azure resources."""
        recommendations: List[OptimizationRecommendation] = []
        logger.debug("Azure unused resource detection not fully implemented")
        return recommendations

    def _detect_gcp_unused_resources(self) -> List[OptimizationRecommendation]:
        """Detect unused GCP resources."""
        recommendations: List[OptimizationRecommendation] = []
        logger.debug("GCP unused resource detection not fully implemented")
        return recommendations

    def _analyze_reserved_instances(
        self, provider: str
    ) -> List[OptimizationRecommendation]:
        """Analyze reserved instance opportunities."""
        recommendations: List[OptimizationRecommendation] = []

        if provider == "aws":
            recommendations.extend(self._analyze_aws_reserved_instances())
        elif provider == "azure":
            recommendations.extend(self._analyze_azure_reserved_instances())
        elif provider == "gcp":
            recommendations.extend(self._analyze_gcp_committed_use())

        return recommendations

    def _analyze_aws_reserved_instances(self) -> List[OptimizationRecommendation]:
        """Analyze AWS reserved instance opportunities."""
        recommendations: List[OptimizationRecommendation] = []

        try:
            ec2 = self._get_aws_client("ec2")

            # Get running instances grouped by type
            instance_counts: Dict[str, int] = {}
            response = ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
            )

            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    instance_type = instance["InstanceType"]
                    instance_counts[instance_type] = (
                        instance_counts.get(instance_type, 0) + 1
                    )

            # Get existing reserved instances
            ri_response = ec2.describe_reserved_instances(
                Filters=[{"Name": "state", "Values": ["active"]}]
            )

            reserved_counts: Dict[str, int] = {}
            for ri in ri_response["ReservedInstances"]:
                ri_type = ri["InstanceType"]
                ri_count = ri["InstanceCount"]
                reserved_counts[ri_type] = reserved_counts.get(ri_type, 0) + ri_count

            # Recommend RIs for instance types with consistent usage
            for instance_type, count in instance_counts.items():
                reserved = reserved_counts.get(instance_type, 0)
                unreserved = count - reserved

                # Recommend RI if 3+ unreserved instances of same type
                if unreserved >= 3:
                    hourly_cost = self.AWS_PRICING.get(instance_type, 0.0)
                    monthly_on_demand = hourly_cost * 730 * unreserved

                    # 1-year partial upfront RI discount
                    discount = self.RI_DISCOUNT["1year_partial"]
                    monthly_ri = monthly_on_demand * (1 - discount)
                    savings = monthly_on_demand - monthly_ri

                    recommendation = OptimizationRecommendation(
                        resource_id=f"ri_{instance_type}",
                        resource_type="reserved_instance_opportunity",
                        provider="aws",
                        category=OptimizationCategory.RESERVED_INSTANCES,
                        current_config={
                            "instance_type": instance_type,
                            "unreserved_count": unreserved,
                            "monthly_on_demand_cost": round(monthly_on_demand, 2),
                        },
                        recommended_config={
                            "purchase": "1-year reserved instance",
                            "term": "1 year",
                            "payment": "partial upfront",
                            "count": unreserved,
                            "monthly_cost": round(monthly_ri, 2),
                        },
                        estimated_savings=round(savings, 2),
                        confidence=0.90,
                        impact=self._determine_impact(savings),
                        risk_level=RiskLevel.LOW,
                        implementation_steps=[
                            f"1. Verify {unreserved}x {instance_type} have "
                            "consistent usage",
                            "2. Purchase 1-year reserved instances",
                            "3. Monitor RI utilization",
                            "4. Consider 3-year term for additional savings",
                        ],
                        metadata={
                            "discount_percentage": discount * 100,
                            "total_instances": count,
                            "already_reserved": reserved,
                        },
                    )
                    recommendations.append(recommendation)

        except Exception as e:
            logger.error(f"Error analyzing AWS RIs: {e}", exc_info=True)

        return recommendations

    def _analyze_azure_reserved_instances(self) -> List[OptimizationRecommendation]:
        """Analyze Azure reserved VM instances."""
        recommendations: List[OptimizationRecommendation] = []
        logger.debug("Azure RI analysis not fully implemented")
        return recommendations

    def _analyze_gcp_committed_use(self) -> List[OptimizationRecommendation]:
        """Analyze GCP committed use discounts."""
        recommendations: List[OptimizationRecommendation] = []
        logger.debug("GCP committed use analysis not fully implemented")
        return recommendations

    def _analyze_spot_instances(
        self, provider: str
    ) -> List[OptimizationRecommendation]:
        """Analyze spot/preemptible instance opportunities."""
        recommendations: List[OptimizationRecommendation] = []

        if provider == "aws":
            recommendations.extend(self._analyze_aws_spot_instances())
        elif provider == "azure":
            recommendations.extend(self._analyze_azure_spot_vms())
        elif provider == "gcp":
            recommendations.extend(self._analyze_gcp_preemptible())

        return recommendations

    def _analyze_aws_spot_instances(self) -> List[OptimizationRecommendation]:
        """Analyze AWS spot instance opportunities."""
        recommendations: List[OptimizationRecommendation] = []

        try:
            ec2 = self._get_aws_client("ec2")
            response = ec2.describe_instances(
                Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
            )

            for reservation in response["Reservations"]:
                for instance in reservation["Instances"]:
                    # Skip if already spot instance
                    if instance.get("InstanceLifecycle") == "spot":
                        continue

                    instance_id = instance["InstanceId"]
                    instance_type = instance["InstanceType"]

                    # Check tags for workload type
                    tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
                    workload = tags.get("Workload", "").lower()

                    # Recommend spot for batch, dev, test workloads
                    if workload in ["batch", "dev", "test", "development"]:
                        hourly_cost = self.AWS_PRICING.get(instance_type, 0.0)
                        monthly_on_demand = hourly_cost * 730
                        monthly_spot = monthly_on_demand * (1 - self.SPOT_DISCOUNT)
                        savings = monthly_on_demand - monthly_spot

                        recommendation = OptimizationRecommendation(
                            resource_id=instance_id,
                            resource_type="ec2_instance",
                            provider="aws",
                            category=OptimizationCategory.SPOT_INSTANCES,
                            current_config={
                                "instance_type": instance_type,
                                "lifecycle": "on-demand",
                                "monthly_cost": round(monthly_on_demand, 2),
                                "workload": workload,
                            },
                            recommended_config={
                                "lifecycle": "spot",
                                "monthly_cost": round(monthly_spot, 2),
                            },
                            estimated_savings=round(savings, 2),
                            confidence=0.75,
                            impact=self._determine_impact(savings),
                            risk_level=RiskLevel.MEDIUM,
                            implementation_steps=[
                                "1. Ensure application can handle interruptions",
                                "2. Implement spot instance request",
                                "3. Configure interruption handling",
                                "4. Test failover behavior",
                                "5. Monitor spot pricing and interruptions",
                            ],
                            metadata={
                                "estimated_discount": self.SPOT_DISCOUNT * 100,
                                "interruption_risk": "medium",
                            },
                        )
                        recommendations.append(recommendation)

        except Exception as e:
            logger.error(f"Error analyzing spot instances: {e}", exc_info=True)

        return recommendations

    def _analyze_azure_spot_vms(self) -> List[OptimizationRecommendation]:
        """Analyze Azure spot VM opportunities."""
        recommendations: List[OptimizationRecommendation] = []
        logger.debug("Azure spot VM analysis not fully implemented")
        return recommendations

    def _analyze_gcp_preemptible(self) -> List[OptimizationRecommendation]:
        """Analyze GCP preemptible VM opportunities."""
        recommendations: List[OptimizationRecommendation] = []
        logger.debug("GCP preemptible VM analysis not fully implemented")
        return recommendations

    def _analyze_storage(self, provider: str) -> List[OptimizationRecommendation]:
        """Analyze storage optimization opportunities."""
        recommendations: List[OptimizationRecommendation] = []

        if provider == "aws":
            recommendations.extend(self._analyze_aws_storage())
        elif provider == "azure":
            recommendations.extend(self._analyze_azure_storage())
        elif provider == "gcp":
            recommendations.extend(self._analyze_gcp_storage())

        return recommendations

    def _analyze_aws_storage(self) -> List[OptimizationRecommendation]:
        """Analyze AWS storage optimization."""
        recommendations: List[OptimizationRecommendation] = []

        try:
            ec2 = self._get_aws_client("ec2")
            cloudwatch = self._get_aws_client("cloudwatch")

            # Analyze EBS volumes for tier optimization
            response = ec2.describe_volumes(
                Filters=[{"Name": "status", "Values": ["in-use"]}]
            )

            for volume in response["Volumes"]:
                volume_id = volume["VolumeId"]
                volume_type = volume["VolumeType"]
                size_gb = volume["Size"]

                # Skip if already on cheapest tier
                if volume_type in ["sc1", "st1"]:
                    continue

                # Get IOPS utilization
                iops_stats = self._get_aws_volume_iops(cloudwatch, volume_id)

                if iops_stats and iops_stats["average"] < 100:
                    # Recommend cheaper storage tier
                    current_price = self.STORAGE_PRICING["aws"].get(volume_type, 0.10)
                    recommended_type = "st1" if size_gb >= 125 else "gp3"
                    recommended_price = self.STORAGE_PRICING["aws"].get(
                        recommended_type, 0.08
                    )

                    current_cost = size_gb * current_price
                    recommended_cost = size_gb * recommended_price
                    savings = current_cost - recommended_cost

                    if savings > 0:
                        recommendation = OptimizationRecommendation(
                            resource_id=volume_id,
                            resource_type="ebs_volume",
                            provider="aws",
                            category=OptimizationCategory.STORAGE_OPTIMIZATION,
                            current_config={
                                "volume_type": volume_type,
                                "size_gb": size_gb,
                                "monthly_cost": round(current_cost, 2),
                                "avg_iops": round(iops_stats["average"], 2),
                            },
                            recommended_config={
                                "volume_type": recommended_type,
                                "monthly_cost": round(recommended_cost, 2),
                            },
                            estimated_savings=round(savings, 2),
                            confidence=0.85,
                            impact=self._determine_impact(savings),
                            risk_level=RiskLevel.LOW,
                            implementation_steps=[
                                f"1. Create snapshot of volume {volume_id}",
                                "2. Create new volume from snapshot with "
                                f"{recommended_type} type",
                                "3. Stop attached instance",
                                "4. Detach old volume and attach new volume",
                                "5. Start instance and verify functionality",
                                "6. Delete old volume after verification",
                            ],
                            metadata={
                                "iops_stats": iops_stats,
                            },
                        )
                        recommendations.append(recommendation)

        except Exception as e:
            logger.error(f"Error analyzing AWS storage: {e}", exc_info=True)

        return recommendations

    def _analyze_azure_storage(self) -> List[OptimizationRecommendation]:
        """Analyze Azure storage optimization."""
        recommendations: List[OptimizationRecommendation] = []
        logger.debug("Azure storage analysis not fully implemented")
        return recommendations

    def _analyze_gcp_storage(self) -> List[OptimizationRecommendation]:
        """Analyze GCP storage optimization."""
        recommendations: List[OptimizationRecommendation] = []
        logger.debug("GCP storage analysis not fully implemented")
        return recommendations

    def _get_aws_cpu_utilization(
        self, cloudwatch: Any, instance_id: str
    ) -> Optional[Dict[str, float]]:
        """Get CPU utilization statistics from CloudWatch."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=self.config.lookback_days)

            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=["Average", "Maximum"],
            )

            if response["Datapoints"]:
                averages = [dp["Average"] for dp in response["Datapoints"]]
                maximums = [dp["Maximum"] for dp in response["Datapoints"]]

                return {
                    "average": np.mean(averages) / 100,
                    "max": np.max(maximums) / 100,
                    "min": np.min(averages) / 100,
                    "datapoints": len(averages),
                }

        except Exception as e:
            logger.debug(f"Error getting CPU metrics for {instance_id}: {e}")

        return None

    def _get_aws_network_utilization(
        self, cloudwatch: Any, instance_id: str
    ) -> Optional[Dict[str, float]]:
        """Get network utilization statistics from CloudWatch."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=self.config.lookback_days)

            # Get network in bytes
            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="NetworkIn",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # 1 day
                Statistics=["Sum"],
            )

            if response["Datapoints"]:
                sums = [dp["Sum"] for dp in response["Datapoints"]]
                return {
                    "average": np.mean(sums),
                    "max": np.max(sums),
                    "datapoints": len(sums),
                }

        except Exception as e:
            logger.debug(f"Error getting network metrics for {instance_id}: {e}")

        return None

    def _get_aws_volume_iops(
        self, cloudwatch: Any, volume_id: str
    ) -> Optional[Dict[str, float]]:
        """Get volume IOPS statistics from CloudWatch."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=self.config.lookback_days)

            response = cloudwatch.get_metric_statistics(
                Namespace="AWS/EBS",
                MetricName="VolumeReadOps",
                Dimensions=[{"Name": "VolumeId", "Value": volume_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=["Average", "Maximum"],
            )

            if response["Datapoints"]:
                averages = [dp["Average"] for dp in response["Datapoints"]]
                return {
                    "average": np.mean(averages),
                    "max": np.max(averages),
                    "datapoints": len(averages),
                }

        except Exception as e:
            logger.debug(f"Error getting IOPS metrics for {volume_id}: {e}")

        return None

    def _get_smaller_instance_type(
        self, current_type: str, provider: str
    ) -> Optional[str]:
        """Get a smaller instance type recommendation."""
        if provider != "aws":
            return None

        # Simple instance family downgrade logic
        size_order = ["micro", "small", "medium", "large", "xlarge", "2xlarge"]

        for i, size in enumerate(size_order):
            if size in current_type and i > 0:
                # Suggest one size down
                smaller_size = size_order[i - 1]
                family = current_type.split(".")[0]
                return f"{family}.{smaller_size}"

        return None

    def _calculate_confidence(self, cpu_stats: Dict[str, float]) -> float:
        """Calculate confidence score based on metric quality."""
        base_confidence = 0.7

        # More datapoints = higher confidence
        datapoints = cpu_stats.get("datapoints", 0)
        if datapoints >= 100:
            base_confidence += 0.2
        elif datapoints >= 50:
            base_confidence += 0.1

        # Low variance = higher confidence
        avg = cpu_stats.get("average", 0)
        max_val = cpu_stats.get("max", 0)
        if max_val > 0:
            variance = (max_val - avg) / max_val
            if variance < 0.2:
                base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _determine_impact(self, savings: float) -> ImpactLevel:
        """Determine impact level based on savings amount."""
        if savings >= 500:
            return ImpactLevel.HIGH
        elif savings >= 100:
            return ImpactLevel.MEDIUM
        else:
            return ImpactLevel.LOW

    def get_summary(
        self, recommendations: List[OptimizationRecommendation]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for recommendations.

        Args:
            recommendations: List of recommendations to summarize

        Returns:
            Dictionary with summary statistics
        """
        if not recommendations:
            return {
                "total_recommendations": 0,
                "total_savings": 0.0,
                "by_category": {},
                "by_provider": {},
                "by_impact": {},
            }

        total_savings = sum(r.estimated_savings for r in recommendations)

        # Group by category
        by_category: Dict[str, Dict[str, Any]] = {}
        for rec in recommendations:
            cat = rec.category.value
            if cat not in by_category:
                by_category[cat] = {"count": 0, "savings": 0.0}
            by_category[cat]["count"] += 1
            by_category[cat]["savings"] += rec.estimated_savings

        # Group by provider
        by_provider: Dict[str, Dict[str, Any]] = {}
        for rec in recommendations:
            prov = rec.provider
            if prov not in by_provider:
                by_provider[prov] = {"count": 0, "savings": 0.0}
            by_provider[prov]["count"] += 1
            by_provider[prov]["savings"] += rec.estimated_savings

        # Group by impact
        by_impact: Dict[str, int] = {}
        for rec in recommendations:
            impact = rec.impact.value
            by_impact[impact] = by_impact.get(impact, 0) + 1

        return {
            "total_recommendations": len(recommendations),
            "total_monthly_savings": round(total_savings, 2),
            "total_annual_savings": round(total_savings * 12, 2),
            "by_category": {
                k: {
                    "count": v["count"],
                    "monthly_savings": round(v["savings"], 2),
                    "annual_savings": round(v["savings"] * 12, 2),
                }
                for k, v in by_category.items()
            },
            "by_provider": {
                k: {
                    "count": v["count"],
                    "monthly_savings": round(v["savings"], 2),
                    "annual_savings": round(v["savings"] * 12, 2),
                }
                for k, v in by_provider.items()
            },
            "by_impact": by_impact,
            "average_confidence": round(
                np.mean([r.confidence for r in recommendations]), 2
            ),
        }

    def export_recommendations(
        self, recommendations: List[OptimizationRecommendation], format: str = "json"
    ) -> str:
        """
        Export recommendations to specified format.

        Args:
            recommendations: List of recommendations to export
            format: Export format (json, csv, markdown)

        Returns:
            Formatted string representation
        """
        if format == "json":
            return json.dumps(
                [r.model_dump(mode="json") for r in recommendations], indent=2
            )

        elif format == "csv":
            if not recommendations:
                return "No recommendations"

            rows = []
            for rec in recommendations:
                rows.append(
                    {
                        "Resource ID": rec.resource_id,
                        "Type": rec.resource_type,
                        "Provider": rec.provider,
                        "Category": rec.category.value,
                        "Monthly Savings": f"${rec.estimated_savings:.2f}",
                        "Impact": rec.impact.value,
                        "Risk": rec.risk_level.value,
                        "Confidence": f"{rec.confidence:.0%}",
                    }
                )

            df = pd.DataFrame(rows)
            return df.to_csv(index=False)

        elif format == "markdown":
            lines = ["# Cost Optimization Recommendations\n"]

            summary = self.get_summary(recommendations)
            lines.append(
                f"**Total Recommendations:** {summary['total_recommendations']}"
            )
            lines.append(
                f"**Total Monthly Savings:** ${summary['total_monthly_savings']:.2f}"
            )
            lines.append(
                f"**Total Annual Savings:** ${summary['total_annual_savings']:.2f}\n"
            )

            for rec in recommendations:
                lines.append(f"## {rec.resource_id}")
                lines.append(f"- **Type:** {rec.resource_type}")
                lines.append(f"- **Provider:** {rec.provider}")
                lines.append(f"- **Category:** {rec.category.value}")
                lines.append(f"- **Monthly Savings:** ${rec.estimated_savings:.2f}")
                lines.append(f"- **Impact:** {rec.impact.value}")
                lines.append(f"- **Risk:** {rec.risk_level.value}")
                lines.append(f"- **Confidence:** {rec.confidence:.0%}")
                lines.append("\n**Implementation Steps:**")
                for step in rec.implementation_steps:
                    lines.append(f"  {step}")
                lines.append("")

            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported format: {format}")
