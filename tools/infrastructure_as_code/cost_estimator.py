"""
Cost estimation for Terraform-managed infrastructure.

This module analyzes Terraform plans to estimate cloud infrastructure
costs across AWS, Azure, and GCP providers.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from decimal import Decimal


logger = logging.getLogger(__name__)


class CostEstimationError(Exception):
    """Base exception for cost estimation operations."""
    pass


@dataclass
class ResourceCost:
    """Container for individual resource cost."""
    resource_type: str
    resource_name: str
    resource_address: str
    monthly_cost: Decimal
    hourly_cost: Decimal
    cost_components: Dict[str, Decimal]


@dataclass
class CostEstimate:
    """Container for cost estimation results."""
    timestamp: str
    provider: str
    total_monthly_cost: Decimal
    total_hourly_cost: Decimal
    resource_costs: List[ResourceCost]
    currency: str = "USD"


class CostEstimator:
    """
    Cost estimator for Terraform infrastructure.

    Analyzes Terraform plans and estimates infrastructure costs
    based on cloud provider pricing.
    """

    # Simplified pricing data (in reality, would use cloud pricing APIs)
    AWS_PRICING = {
        "aws_instance": {
            "t2.micro": {"hourly": 0.0116},
            "t2.small": {"hourly": 0.023},
            "t2.medium": {"hourly": 0.0464},
            "t3.micro": {"hourly": 0.0104},
            "t3.small": {"hourly": 0.0208},
            "t3.medium": {"hourly": 0.0416},
            "m5.large": {"hourly": 0.096},
            "m5.xlarge": {"hourly": 0.192},
        },
        "aws_db_instance": {
            "db.t2.micro": {"hourly": 0.017},
            "db.t2.small": {"hourly": 0.034},
            "db.t3.micro": {"hourly": 0.018},
            "db.t3.small": {"hourly": 0.036},
        },
        "aws_s3_bucket": {
            "storage_gb": {"monthly": 0.023},
        },
        "aws_ebs_volume": {
            "gp2": {"per_gb_month": 0.10},
            "gp3": {"per_gb_month": 0.08},
            "io1": {"per_gb_month": 0.125},
        },
    }

    AZURE_PRICING = {
        "azurerm_virtual_machine": {
            "Standard_B1s": {"hourly": 0.0104},
            "Standard_B1ms": {"hourly": 0.0207},
            "Standard_B2s": {"hourly": 0.0416},
            "Standard_D2s_v3": {"hourly": 0.096},
        },
        "azurerm_storage_account": {
            "storage_gb": {"monthly": 0.0184},
        },
    }

    GCP_PRICING = {
        "google_compute_instance": {
            "f1-micro": {"hourly": 0.0076},
            "g1-small": {"hourly": 0.0257},
            "n1-standard-1": {"hourly": 0.0475},
            "n1-standard-2": {"hourly": 0.095},
        },
        "google_storage_bucket": {
            "storage_gb": {"monthly": 0.020},
        },
    }

    def __init__(self, terraform_wrapper, provider: str = "aws"):
        """
        Initialize cost estimator.

        Args:
            terraform_wrapper: TerraformWrapper instance
            provider: Cloud provider (aws, azure, gcp)
        """
        self.terraform = terraform_wrapper
        self.provider = provider.lower()

        # Select pricing data based on provider
        if self.provider == "aws":
            self.pricing_data = self.AWS_PRICING
        elif self.provider == "azure":
            self.pricing_data = self.AZURE_PRICING
        elif self.provider == "gcp":
            self.pricing_data = self.GCP_PRICING
        else:
            raise CostEstimationError(f"Unsupported provider: {provider}")

    def estimate_costs(self) -> CostEstimate:
        """
        Estimate infrastructure costs from Terraform plan.

        Returns:
            CostEstimate with cost breakdown

        Raises:
            CostEstimationError: If cost estimation fails
        """
        logger.info("Estimating infrastructure costs...")

        try:
            # Get Terraform plan in JSON format
            plan_json = self.terraform.plan_json()

            # Extract resources from plan
            resource_costs = self._estimate_resources(plan_json)

            # Calculate totals
            total_monthly = sum(rc.monthly_cost for rc in resource_costs)
            total_hourly = sum(rc.hourly_cost for rc in resource_costs)

            timestamp = datetime.now().isoformat()

            estimate = CostEstimate(
                timestamp=timestamp,
                provider=self.provider,
                total_monthly_cost=total_monthly,
                total_hourly_cost=total_hourly,
                resource_costs=resource_costs,
                currency="USD"
            )

            logger.info(
                f"Cost estimation complete: ${total_monthly:.2f}/month"
            )

            return estimate

        except Exception as e:
            raise CostEstimationError(f"Cost estimation failed: {e}")

    def _estimate_resources(
        self,
        plan_json: Dict[str, Any]
    ) -> List[ResourceCost]:
        """
        Estimate costs for resources in plan.

        Args:
            plan_json: Parsed Terraform plan JSON

        Returns:
            List of ResourceCost objects
        """
        resource_costs = []

        resource_changes = plan_json.get("resource_changes", [])

        for change in resource_changes:
            # Only estimate costs for resources being created or updated
            actions = change.get("change", {}).get("actions", [])

            if "create" in actions or "update" in actions:
                cost = self._estimate_resource_cost(change)
                if cost:
                    resource_costs.append(cost)

        return resource_costs

    def _estimate_resource_cost(
        self,
        resource_change: Dict[str, Any]
    ) -> Optional[ResourceCost]:
        """
        Estimate cost for a single resource.

        Args:
            resource_change: Resource change from plan

        Returns:
            ResourceCost if estimable, None otherwise
        """
        resource_type = resource_change.get("type", "")
        resource_name = resource_change.get("name", "")
        resource_address = resource_change.get("address", "")

        # Get resource configuration
        after = resource_change.get("change", {}).get("after", {})

        if not after:
            return None

        # Estimate based on resource type
        if self.provider == "aws":
            return self._estimate_aws_resource(
                resource_type, resource_name, resource_address, after
            )
        elif self.provider == "azure":
            return self._estimate_azure_resource(
                resource_type, resource_name, resource_address, after
            )
        elif self.provider == "gcp":
            return self._estimate_gcp_resource(
                resource_type, resource_name, resource_address, after
            )

        return None

    def _estimate_aws_resource(
        self,
        resource_type: str,
        resource_name: str,
        resource_address: str,
        config: Dict[str, Any]
    ) -> Optional[ResourceCost]:
        """Estimate AWS resource cost."""
        cost_components = {}
        hourly_cost = Decimal("0")
        monthly_cost = Decimal("0")

        if resource_type == "aws_instance":
            instance_type = config.get("instance_type", "t2.micro")
            pricing = self.pricing_data.get("aws_instance", {}).get(
                instance_type, {"hourly": 0.0116}
            )

            hourly = Decimal(str(pricing["hourly"]))
            hourly_cost = hourly
            monthly_cost = hourly * 730  # Average hours per month

            cost_components["compute"] = monthly_cost

        elif resource_type == "aws_db_instance":
            instance_class = config.get("instance_class", "db.t2.micro")
            pricing = self.pricing_data.get("aws_db_instance", {}).get(
                instance_class, {"hourly": 0.017}
            )

            hourly = Decimal(str(pricing["hourly"]))
            hourly_cost = hourly
            monthly_cost = hourly * 730

            cost_components["database"] = monthly_cost

        elif resource_type == "aws_s3_bucket":
            # Estimate based on expected storage (would need additional input)
            estimated_gb = Decimal("100")  # Default estimate
            pricing = self.pricing_data.get("aws_s3_bucket", {}).get(
                "storage_gb", {"monthly": 0.023}
            )

            monthly = Decimal(str(pricing["monthly"]))
            monthly_cost = estimated_gb * monthly

            cost_components["storage"] = monthly_cost

        elif resource_type == "aws_ebs_volume":
            volume_type = config.get("type", "gp2")
            size = Decimal(str(config.get("size", 8)))

            pricing = self.pricing_data.get("aws_ebs_volume", {}).get(
                volume_type, {"per_gb_month": 0.10}
            )

            per_gb = Decimal(str(pricing["per_gb_month"]))
            monthly_cost = size * per_gb

            cost_components["storage"] = monthly_cost

        else:
            # Unknown resource type
            logger.debug(f"No pricing data for {resource_type}")
            return None

        if monthly_cost == 0:
            return None

        return ResourceCost(
            resource_type=resource_type,
            resource_name=resource_name,
            resource_address=resource_address,
            monthly_cost=monthly_cost,
            hourly_cost=hourly_cost,
            cost_components=cost_components
        )

    def _estimate_azure_resource(
        self,
        resource_type: str,
        resource_name: str,
        resource_address: str,
        config: Dict[str, Any]
    ) -> Optional[ResourceCost]:
        """Estimate Azure resource cost."""
        cost_components = {}
        hourly_cost = Decimal("0")
        monthly_cost = Decimal("0")

        if resource_type == "azurerm_virtual_machine" or \
           resource_type == "azurerm_linux_virtual_machine" or \
           resource_type == "azurerm_windows_virtual_machine":

            vm_size = config.get("size", "Standard_B1s")
            pricing = self.pricing_data.get("azurerm_virtual_machine", {}).get(
                vm_size, {"hourly": 0.0104}
            )

            hourly = Decimal(str(pricing["hourly"]))
            hourly_cost = hourly
            monthly_cost = hourly * 730

            cost_components["compute"] = monthly_cost

        elif resource_type == "azurerm_storage_account":
            estimated_gb = Decimal("100")
            pricing = self.pricing_data.get("azurerm_storage_account", {}).get(
                "storage_gb", {"monthly": 0.0184}
            )

            monthly = Decimal(str(pricing["monthly"]))
            monthly_cost = estimated_gb * monthly

            cost_components["storage"] = monthly_cost

        else:
            logger.debug(f"No pricing data for {resource_type}")
            return None

        if monthly_cost == 0:
            return None

        return ResourceCost(
            resource_type=resource_type,
            resource_name=resource_name,
            resource_address=resource_address,
            monthly_cost=monthly_cost,
            hourly_cost=hourly_cost,
            cost_components=cost_components
        )

    def _estimate_gcp_resource(
        self,
        resource_type: str,
        resource_name: str,
        resource_address: str,
        config: Dict[str, Any]
    ) -> Optional[ResourceCost]:
        """Estimate GCP resource cost."""
        cost_components = {}
        hourly_cost = Decimal("0")
        monthly_cost = Decimal("0")

        if resource_type == "google_compute_instance":
            machine_type = config.get("machine_type", "f1-micro")
            # Extract just the machine type name
            machine_type_name = machine_type.split("/")[-1]

            pricing = self.pricing_data.get("google_compute_instance", {}).get(
                machine_type_name, {"hourly": 0.0076}
            )

            hourly = Decimal(str(pricing["hourly"]))
            hourly_cost = hourly
            monthly_cost = hourly * 730

            cost_components["compute"] = monthly_cost

        elif resource_type == "google_storage_bucket":
            estimated_gb = Decimal("100")
            pricing = self.pricing_data.get("google_storage_bucket", {}).get(
                "storage_gb", {"monthly": 0.020}
            )

            monthly = Decimal(str(pricing["monthly"]))
            monthly_cost = estimated_gb * monthly

            cost_components["storage"] = monthly_cost

        else:
            logger.debug(f"No pricing data for {resource_type}")
            return None

        if monthly_cost == 0:
            return None

        return ResourceCost(
            resource_type=resource_type,
            resource_name=resource_name,
            resource_address=resource_address,
            monthly_cost=monthly_cost,
            hourly_cost=hourly_cost,
            cost_components=cost_components
        )

    def generate_cost_report(
        self,
        estimate: CostEstimate,
        output_format: str = "text",
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate cost report in specified format.

        Args:
            estimate: CostEstimate to format
            output_format: Report format (text, json, html)
            output_file: Optional file to write report to

        Returns:
            Formatted report as string
        """
        if output_format == "json":
            report_str = self._generate_json_report(estimate)
        elif output_format == "html":
            report_str = self._generate_html_report(estimate)
        else:
            report_str = self._generate_text_report(estimate)

        if output_file:
            Path(output_file).write_text(report_str)
            logger.info(f"Cost report written to: {output_file}")

        return report_str

    def _generate_text_report(self, estimate: CostEstimate) -> str:
        """Generate text format cost report."""
        lines = [
            "=" * 80,
            "Terraform Cost Estimation Report",
            "=" * 80,
            f"Provider: {estimate.provider.upper()}",
            f"Timestamp: {estimate.timestamp}",
            f"Currency: {estimate.currency}",
            "",
            f"Total Monthly Cost: ${estimate.total_monthly_cost:.2f}",
            f"Total Hourly Cost: ${estimate.total_hourly_cost:.4f}",
            "",
            "=" * 80,
            "Resource Breakdown:",
            "=" * 80,
        ]

        if not estimate.resource_costs:
            lines.append("\nNo resources with cost estimates found.")
        else:
            for i, resource in enumerate(estimate.resource_costs, 1):
                lines.extend([
                    f"\n{i}. {resource.resource_address}",
                    f"   Type: {resource.resource_type}",
                    f"   Monthly Cost: ${resource.monthly_cost:.2f}",
                    f"   Hourly Cost: ${resource.hourly_cost:.4f}",
                    "   Cost Components:",
                ])

                for component, cost in resource.cost_components.items():
                    lines.append(f"     - {component}: ${cost:.2f}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    def _generate_json_report(self, estimate: CostEstimate) -> str:
        """Generate JSON format cost report."""
        report_data = {
            "timestamp": estimate.timestamp,
            "provider": estimate.provider,
            "currency": estimate.currency,
            "total_monthly_cost": float(estimate.total_monthly_cost),
            "total_hourly_cost": float(estimate.total_hourly_cost),
            "resource_costs": [
                {
                    "resource_type": rc.resource_type,
                    "resource_name": rc.resource_name,
                    "resource_address": rc.resource_address,
                    "monthly_cost": float(rc.monthly_cost),
                    "hourly_cost": float(rc.hourly_cost),
                    "cost_components": {
                        k: float(v) for k, v in rc.cost_components.items()
                    }
                }
                for rc in estimate.resource_costs
            ]
        }

        return json.dumps(report_data, indent=2)

    def _generate_html_report(self, estimate: CostEstimate) -> str:
        """Generate HTML format cost report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Terraform Cost Estimation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f0f0f0; padding: 15px; margin: 20px 0; }}
        .cost-box {{ background: #e3f2fd; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .resource {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; }}
        .total {{ font-size: 24px; font-weight: bold; color: #1976d2; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <h1>Terraform Cost Estimation Report</h1>

    <div class="summary">
        <p>Provider: {estimate.provider.upper()}</p>
        <p>Timestamp: {estimate.timestamp}</p>
        <p>Currency: {estimate.currency}</p>
    </div>

    <div class="cost-box">
        <p class="total">Total Monthly Cost: ${estimate.total_monthly_cost:.2f}</p>
        <p>Total Hourly Cost: ${estimate.total_hourly_cost:.4f}</p>
    </div>

    <h2>Resource Breakdown</h2>
"""

        if not estimate.resource_costs:
            html += "    <p>No resources with cost estimates found.</p>\n"
        else:
            html += """
    <table>
        <tr>
            <th>Resource</th>
            <th>Type</th>
            <th>Monthly Cost</th>
            <th>Hourly Cost</th>
        </tr>
"""
            for resource in estimate.resource_costs:
                html += f"""
        <tr>
            <td>{resource.resource_address}</td>
            <td>{resource.resource_type}</td>
            <td>${resource.monthly_cost:.2f}</td>
            <td>${resource.hourly_cost:.4f}</td>
        </tr>
"""

            html += "    </table>\n"

        html += """
</body>
</html>
"""

        return html

    def compare_costs(
        self,
        before_estimate: CostEstimate,
        after_estimate: CostEstimate
    ) -> Dict[str, Any]:
        """
        Compare two cost estimates.

        Args:
            before_estimate: Cost estimate before changes
            after_estimate: Cost estimate after changes

        Returns:
            Cost comparison dictionary
        """
        monthly_diff = after_estimate.total_monthly_cost - \
            before_estimate.total_monthly_cost
        monthly_percent = (monthly_diff / before_estimate.total_monthly_cost * 100) \
            if before_estimate.total_monthly_cost > 0 else 0

        return {
            "before_monthly": float(before_estimate.total_monthly_cost),
            "after_monthly": float(after_estimate.total_monthly_cost),
            "difference_monthly": float(monthly_diff),
            "percent_change": float(monthly_percent),
            "currency": after_estimate.currency,
        }

    def check_budget_alert(
        self,
        estimate: CostEstimate,
        budget_limit: Decimal
    ) -> Dict[str, Any]:
        """
        Check if estimated cost exceeds budget.

        Args:
            estimate: CostEstimate to check
            budget_limit: Monthly budget limit

        Returns:
            Budget alert information
        """
        exceeds_budget = estimate.total_monthly_cost > budget_limit

        if exceeds_budget:
            overage = estimate.total_monthly_cost - budget_limit
            percent_over = (overage / budget_limit * 100) if budget_limit > 0 else 0

            return {
                "exceeds_budget": True,
                "budget_limit": float(budget_limit),
                "estimated_cost": float(estimate.total_monthly_cost),
                "overage": float(overage),
                "percent_over": float(percent_over),
                "message": f"Estimated cost ${estimate.total_monthly_cost:.2f} "
                          f"exceeds budget ${budget_limit:.2f} by "
                          f"${overage:.2f} ({percent_over:.1f}%)"
            }

        utilization = (estimate.total_monthly_cost / budget_limit * 100) \
            if budget_limit > 0 else 0

        return {
            "exceeds_budget": False,
            "budget_limit": float(budget_limit),
            "estimated_cost": float(estimate.total_monthly_cost),
            "budget_utilization": float(utilization),
            "message": f"Estimated cost ${estimate.total_monthly_cost:.2f} "
                      f"is within budget ${budget_limit:.2f} "
                      f"({utilization:.1f}% utilization)"
        }
