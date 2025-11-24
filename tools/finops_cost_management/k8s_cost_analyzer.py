"""
Kubernetes Cost Analyzer with Kubecost Integration.

Provides comprehensive cost attribution and analysis for Kubernetes clusters using
Kubecost API. Tracks pod, namespace, and container-level costs, identifies idle
resources, and enables cost allocation by custom labels and annotations.

Features:
- Real-time cost attribution for pods/namespaces
- Cost breakdown by resource type (CPU, memory, storage, network)
- Idle resource identification with configurable thresholds
- Cost allocation by team/project labels
- Multi-cluster support
- Time-series cost analysis

Protocol Coverage:
- P-CLOUD-VALIDATION: Validate K8s resource costs
- P-FINOPS-COST-MONITOR: Real-time K8s cost monitoring
- P-OBSERVABILITY: Cost metrics export
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from pydantic import BaseModel, Field, field_validator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class KubecostConfig(BaseModel):
    """Configuration for Kubecost API integration."""

    kubecost_url: str = Field(
        default="http://localhost:9090", description="Base URL for Kubecost API"
    )
    cluster_name: str = Field(
        default="default", description="Name of the Kubernetes cluster"
    )
    api_key: Optional[str] = Field(
        default=None, description="API key for Kubecost authentication"
    )
    timeout: int = Field(
        default=30, description="Request timeout in seconds", ge=1, le=300
    )
    retry_attempts: int = Field(
        default=3,
        description="Number of retry attempts for failed requests",
        ge=0,
        le=10,
    )
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")

    @field_validator("kubecost_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate Kubecost URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("kubecost_url must start with http:// or https://")
        return v.rstrip("/")


class K8sCostData(BaseModel):
    """Kubernetes cost data for a specific resource."""

    namespace: str = Field(description="Kubernetes namespace")
    pod: Optional[str] = Field(default=None, description="Pod name")
    container: Optional[str] = Field(default=None, description="Container name")
    labels: Dict[str, str] = Field(
        default_factory=dict, description="Kubernetes labels"
    )
    annotations: Dict[str, str] = Field(
        default_factory=dict, description="Kubernetes annotations"
    )
    cpu_cost: float = Field(description="CPU cost in USD", ge=0)
    memory_cost: float = Field(description="Memory cost in USD", ge=0)
    storage_cost: float = Field(description="Storage cost in USD", ge=0)
    network_cost: float = Field(description="Network cost in USD", ge=0)
    total_cost: float = Field(description="Total cost in USD", ge=0)
    cpu_cores: float = Field(default=0.0, description="CPU cores used", ge=0)
    memory_gb: float = Field(default=0.0, description="Memory in GB used", ge=0)
    storage_gb: float = Field(default=0.0, description="Storage in GB used", ge=0)
    start_date: datetime = Field(description="Start of cost period")
    end_date: datetime = Field(description="End of cost period")
    cluster: str = Field(default="default", description="Cluster name")

    @field_validator("total_cost")
    @classmethod
    def validate_total_cost(cls, v: float, info: Any) -> float:
        """Validate total cost matches sum of component costs."""
        if "cpu_cost" in info.data and "memory_cost" in info.data:
            expected = (
                info.data.get("cpu_cost", 0)
                + info.data.get("memory_cost", 0)
                + info.data.get("storage_cost", 0)
                + info.data.get("network_cost", 0)
            )
            if abs(v - expected) > 0.01:  # Allow small floating point differences
                logger.warning(
                    f"Total cost {v} does not match sum {expected}, using total"
                )
        return v


class IdleResource(BaseModel):
    """Idle or underutilized resource information."""

    namespace: str = Field(description="Kubernetes namespace")
    pod: str = Field(description="Pod name")
    container: Optional[str] = Field(default=None, description="Container name")
    resource_type: str = Field(description="Type of resource (cpu, memory, storage)")
    allocated: float = Field(description="Allocated resources", ge=0)
    used: float = Field(description="Actually used resources", ge=0)
    utilization: float = Field(description="Utilization percentage", ge=0, le=100)
    waste_cost: float = Field(description="Cost of unused resources", ge=0)
    recommendation: str = Field(description="Optimization recommendation")
    labels: Dict[str, str] = Field(default_factory=dict)


class CostAllocation(BaseModel):
    """Cost allocation by specific dimension."""

    dimension: str = Field(description="Allocation dimension (team, project, etc)")
    allocations: Dict[str, float] = Field(description="Map of dimension value to cost")
    total_cost: float = Field(description="Total allocated cost", ge=0)
    unallocated_cost: float = Field(
        default=0.0, description="Cost that couldn't be allocated", ge=0
    )
    start_date: datetime = Field(description="Start of allocation period")
    end_date: datetime = Field(description="End of allocation period")

    @field_validator("total_cost")
    @classmethod
    def validate_total(cls, v: float, info: Any) -> float:
        """Validate total cost matches allocations sum."""
        if "allocations" in info.data:
            allocated_sum = sum(info.data["allocations"].values())
            unallocated = info.data.get("unallocated_cost", 0)
            expected = allocated_sum + unallocated
            if abs(v - expected) > 0.01:
                logger.warning(f"Total {v} doesn't match allocated {expected}")
        return v


class K8sCostAnalyzer:
    """
    Kubernetes Cost Analyzer with Kubecost integration.

    Provides comprehensive cost analysis and attribution for Kubernetes workloads
    using Kubecost API. Supports namespace, pod, and container-level cost tracking,
    idle resource identification, and custom label-based cost allocation.
    """

    def __init__(self, config: KubecostConfig) -> None:
        """
        Initialize K8s Cost Analyzer.

        Args:
            config: Kubecost configuration
        """
        self.config = config
        self.session = self._create_session()
        logger.info(f"Initialized K8sCostAnalyzer for cluster '{config.cluster_name}'")

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry logic."""
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=self.config.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Add API key if provided
        if self.config.api_key:
            session.headers.update({"Authorization": f"Bearer {self.config.api_key}"})

        return session

    def _make_request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Kubecost API.

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            Response data as dictionary

        Raises:
            requests.RequestException: On request failure
        """
        url = urljoin(self.config.kubecost_url, endpoint)
        logger.debug(f"Making request to {url} with params {params}")

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"Kubecost API request failed: {e}")
            raise

    def _parse_cost_data(
        self, data: Dict[str, Any], start_date: datetime, end_date: datetime
    ) -> K8sCostData:
        """
        Parse Kubecost API response into K8sCostData.

        Args:
            data: Raw API response data
            start_date: Start of cost period
            end_date: End of cost period

        Returns:
            Parsed cost data
        """
        # Extract cost components
        properties = data.get("properties", {})
        cpu_cost = properties.get("cpuCost", 0.0)
        memory_cost = properties.get("ramCost", 0.0)
        storage_cost = properties.get("pvCost", 0.0)
        network_cost = properties.get("networkCost", 0.0)

        # Extract resource usage
        cpu_cores = properties.get("cpuCores", 0.0)
        memory_bytes = properties.get("ramBytes", 0.0)
        memory_gb = memory_bytes / (1024**3) if memory_bytes > 0 else 0.0
        storage_bytes = properties.get("pvBytes", 0.0)
        storage_gb = storage_bytes / (1024**3) if storage_bytes > 0 else 0.0

        # Parse name (format: namespace/pod/container)
        name = data.get("name", "")
        parts = name.split("/")
        namespace = parts[0] if len(parts) > 0 else "unknown"
        pod = parts[1] if len(parts) > 1 else None
        container = parts[2] if len(parts) > 2 else None

        # Extract labels and annotations
        labels = properties.get("labels", {})
        annotations = properties.get("annotations", {})

        return K8sCostData(
            namespace=namespace,
            pod=pod,
            container=container,
            labels=labels,
            annotations=annotations,
            cpu_cost=cpu_cost,
            memory_cost=memory_cost,
            storage_cost=storage_cost,
            network_cost=network_cost,
            total_cost=cpu_cost + memory_cost + storage_cost + network_cost,
            cpu_cores=cpu_cores,
            memory_gb=memory_gb,
            storage_gb=storage_gb,
            start_date=start_date,
            end_date=end_date,
            cluster=self.config.cluster_name,
        )

    def get_namespace_costs(
        self, start_date: str, end_date: str, aggregation: str = "namespace"
    ) -> List[K8sCostData]:
        """
        Get cost breakdown by namespace.

        Args:
            start_date: Start date (YYYY-MM-DD or ISO format)
            end_date: End date (YYYY-MM-DD or ISO format)
            aggregation: Aggregation level (namespace, pod, container)

        Returns:
            List of cost data per namespace

        Raises:
            ValueError: On invalid date format
            requests.RequestException: On API failure
        """
        logger.info(f"Fetching namespace costs from {start_date} to {end_date}")

        # Parse dates
        start_dt = self._parse_date(start_date)
        end_dt = self._parse_date(end_date)

        # Format for Kubecost API (RFC3339)
        window = f"{start_dt.isoformat()},{end_dt.isoformat()}"

        # Make API request
        params = {
            "window": window,
            "aggregate": aggregation,
            "accumulate": "true",
        }

        try:
            response = self._make_request("/model/allocation", params)
            data = response.get("data", [])

            # Parse cost data
            costs = []
            for item in data:
                for _, cost_data in item.items():
                    if isinstance(cost_data, dict):
                        try:
                            cost = self._parse_cost_data(cost_data, start_dt, end_dt)
                            costs.append(cost)
                        except Exception as e:
                            logger.warning(f"Failed to parse cost data: {e}")
                            continue

            logger.info(f"Retrieved {len(costs)} namespace cost entries")
            return costs

        except Exception as e:
            logger.error(f"Failed to get namespace costs: {e}")
            raise

    def get_pod_costs(
        self, namespace: str, start_date: str, end_date: str
    ) -> List[K8sCostData]:
        """
        Get cost breakdown by pod in a specific namespace.

        Args:
            namespace: Kubernetes namespace
            start_date: Start date (YYYY-MM-DD or ISO format)
            end_date: End date (YYYY-MM-DD or ISO format)

        Returns:
            List of cost data per pod

        Raises:
            ValueError: On invalid date format
            requests.RequestException: On API failure
        """
        logger.info(
            f"Fetching pod costs for namespace '{namespace}' "
            f"from {start_date} to {end_date}"
        )

        # Get all costs aggregated by pod
        all_costs = self.get_namespace_costs(start_date, end_date, "pod")

        # Filter by namespace
        pod_costs = [c for c in all_costs if c.namespace == namespace]

        logger.info(
            f"Retrieved {len(pod_costs)} pod cost entries for "
            f"namespace '{namespace}'"
        )
        return pod_costs

    def get_costs_by_label(
        self,
        label_key: str,
        start_date: str,
        end_date: str,
        label_value: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Get costs grouped by label value.

        Args:
            label_key: Label key to group by (e.g., 'team', 'app')
            start_date: Start date (YYYY-MM-DD or ISO format)
            end_date: End date (YYYY-MM-DD or ISO format)
            label_value: Optional specific label value to filter

        Returns:
            Dictionary mapping label values to total cost

        Raises:
            ValueError: On invalid date format
            requests.RequestException: On API failure
        """
        logger.info(
            f"Fetching costs by label '{label_key}' " f"from {start_date} to {end_date}"
        )

        # Get all costs at pod level
        all_costs = self.get_namespace_costs(start_date, end_date, "pod")

        # Group by label value
        label_costs: Dict[str, float] = {}
        untagged_cost = 0.0

        for cost in all_costs:
            if label_key in cost.labels:
                value = cost.labels[label_key]
                if label_value is None or value == label_value:
                    label_costs[value] = label_costs.get(value, 0.0) + cost.total_cost
            else:
                untagged_cost += cost.total_cost

        # Add untagged costs if any
        if untagged_cost > 0:
            label_costs["__untagged__"] = untagged_cost

        logger.info(
            f"Grouped costs into {len(label_costs)} label values "
            f"for key '{label_key}'"
        )
        return label_costs

    def identify_idle_resources(
        self,
        threshold: float = 0.2,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[IdleResource]:
        """
        Identify idle or underutilized resources.

        Args:
            threshold: Utilization threshold (0.0-1.0)
            start_date: Start date (defaults to 24h ago)
            end_date: End date (defaults to now)

        Returns:
            List of idle resources with recommendations

        Raises:
            ValueError: On invalid threshold or dates
            requests.RequestException: On API failure
        """
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")

        # Default to last 24 hours
        if end_date is None:
            end_dt = datetime.utcnow()
            end_date = end_dt.isoformat()
        else:
            end_dt = self._parse_date(end_date)

        if start_date is None:
            start_dt = end_dt - timedelta(days=1)
            start_date = start_dt.isoformat()
        else:
            start_dt = self._parse_date(start_date)

        logger.info(
            f"Identifying idle resources with threshold {threshold:.0%} "
            f"from {start_date} to {end_date}"
        )

        # Get pod-level costs with resource usage
        costs = self.get_namespace_costs(start_date, end_date, "pod")

        idle_resources: List[IdleResource] = []

        # Analyze each pod for underutilization
        for cost in costs:
            if cost.pod is None:
                continue

            # Check CPU utilization (simplified - in production would use
            # actual usage metrics from Prometheus)
            cpu_utilization = self._estimate_utilization(cost.cpu_cores, cost.cpu_cost)
            if cpu_utilization < threshold and cost.cpu_cost > 0:
                waste_cost = cost.cpu_cost * (1 - cpu_utilization)
                idle_resources.append(
                    IdleResource(
                        namespace=cost.namespace,
                        pod=cost.pod,
                        container=cost.container,
                        resource_type="cpu",
                        allocated=cost.cpu_cores,
                        used=cost.cpu_cores * cpu_utilization,
                        utilization=cpu_utilization * 100,
                        waste_cost=waste_cost,
                        recommendation=self._generate_cpu_recommendation(
                            cost.cpu_cores, cpu_utilization
                        ),
                        labels=cost.labels,
                    )
                )

            # Check memory utilization
            mem_utilization = self._estimate_utilization(
                cost.memory_gb, cost.memory_cost
            )
            if mem_utilization < threshold and cost.memory_cost > 0:
                waste_cost = cost.memory_cost * (1 - mem_utilization)
                idle_resources.append(
                    IdleResource(
                        namespace=cost.namespace,
                        pod=cost.pod,
                        container=cost.container,
                        resource_type="memory",
                        allocated=cost.memory_gb,
                        used=cost.memory_gb * mem_utilization,
                        utilization=mem_utilization * 100,
                        waste_cost=waste_cost,
                        recommendation=self._generate_memory_recommendation(
                            cost.memory_gb, mem_utilization
                        ),
                        labels=cost.labels,
                    )
                )

        # Sort by waste cost descending
        idle_resources.sort(key=lambda x: x.waste_cost, reverse=True)

        logger.info(f"Identified {len(idle_resources)} idle resources")
        return idle_resources

    def get_cost_allocation(
        self,
        allocation_key: str,
        start_date: str,
        end_date: str,
        allocation_type: str = "label",
    ) -> CostAllocation:
        """
        Get cost allocation by specific dimension.

        Args:
            allocation_key: Key to allocate by (e.g., 'team', 'project')
            start_date: Start date (YYYY-MM-DD or ISO format)
            end_date: End date (YYYY-MM-DD or ISO format)
            allocation_type: Type of allocation (label, annotation, namespace)

        Returns:
            Cost allocation breakdown

        Raises:
            ValueError: On invalid parameters
            requests.RequestException: On API failure
        """
        logger.info(
            f"Getting cost allocation by {allocation_type}:{allocation_key} "
            f"from {start_date} to {end_date}"
        )

        # Parse dates
        start_dt = self._parse_date(start_date)
        end_dt = self._parse_date(end_date)

        # Get costs based on allocation type
        if allocation_type == "label":
            allocations = self.get_costs_by_label(allocation_key, start_date, end_date)
        elif allocation_type == "namespace":
            costs = self.get_namespace_costs(start_date, end_date, "namespace")
            allocations = {c.namespace: c.total_cost for c in costs}
        elif allocation_type == "annotation":
            costs = self.get_namespace_costs(start_date, end_date, "pod")
            allocations = {}
            unallocated = 0.0
            for cost in costs:
                if allocation_key in cost.annotations:
                    value = cost.annotations[allocation_key]
                    allocations[value] = allocations.get(value, 0.0) + cost.total_cost
                else:
                    unallocated += cost.total_cost
            allocations["__untagged__"] = unallocated
        else:
            raise ValueError(
                f"Invalid allocation_type: {allocation_type}. "
                f"Must be 'label', 'annotation', or 'namespace'"
            )

        # Calculate totals
        unallocated_cost = allocations.pop("__untagged__", 0.0)
        total_cost = sum(allocations.values()) + unallocated_cost

        allocation = CostAllocation(
            dimension=f"{allocation_type}:{allocation_key}",
            allocations=allocations,
            total_cost=total_cost,
            unallocated_cost=unallocated_cost,
            start_date=start_dt,
            end_date=end_dt,
        )

        logger.info(
            f"Cost allocation: {len(allocations)} values, " f"total ${total_cost:.2f}"
        )
        return allocation

    def get_cluster_efficiency(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Calculate cluster efficiency metrics.

        Args:
            start_date: Start date (YYYY-MM-DD or ISO format)
            end_date: End date (YYYY-MM-DD or ISO format)

        Returns:
            Dictionary with efficiency metrics

        Raises:
            ValueError: On invalid dates
            requests.RequestException: On API failure
        """
        logger.info(f"Calculating cluster efficiency from {start_date} to {end_date}")

        # Get all costs
        costs = self.get_namespace_costs(start_date, end_date, "pod")

        # Calculate aggregate metrics
        total_cost = sum(c.total_cost for c in costs)
        total_cpu_cores = sum(c.cpu_cores for c in costs)
        total_memory_gb = sum(c.memory_gb for c in costs)

        # Estimate utilization (in production, use actual metrics)
        avg_cpu_util = (
            sum(
                self._estimate_utilization(c.cpu_cores, c.cpu_cost) * c.cpu_cores
                for c in costs
            )
            / total_cpu_cores
            if total_cpu_cores > 0
            else 0
        )

        avg_mem_util = (
            sum(
                self._estimate_utilization(c.memory_gb, c.memory_cost) * c.memory_gb
                for c in costs
            )
            / total_memory_gb
            if total_memory_gb > 0
            else 0
        )

        # Identify idle resources
        idle_resources = self.identify_idle_resources(0.2, start_date, end_date)
        total_waste = sum(r.waste_cost for r in idle_resources)

        efficiency = {
            "cluster": self.config.cluster_name,
            "period": {"start": start_date, "end": end_date},
            "total_cost": total_cost,
            "total_cpu_cores": total_cpu_cores,
            "total_memory_gb": total_memory_gb,
            "avg_cpu_utilization": avg_cpu_util,
            "avg_memory_utilization": avg_mem_util,
            "idle_resource_count": len(idle_resources),
            "estimated_waste": total_waste,
            "efficiency_score": (
                1 - (total_waste / total_cost) if total_cost > 0 else 1
            ),  # noqa: E501
            "potential_savings": total_waste,
        }

        logger.info(
            f"Cluster efficiency: {efficiency['efficiency_score']:.1%}, "
            f"potential savings ${total_waste:.2f}"
        )
        return efficiency

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        """
        Parse date string to datetime.

        Args:
            date_str: Date string (YYYY-MM-DD or ISO format)

        Returns:
            Parsed datetime

        Raises:
            ValueError: On invalid format
        """
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            try:
                # Try simple date format
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid date format: {date_str}. " f"Use YYYY-MM-DD or ISO format"
                )

    @staticmethod
    def _estimate_utilization(resource_amount: float, cost: float) -> float:
        """
        Estimate resource utilization based on cost.

        This is a simplified estimation. In production, integrate with
        Prometheus metrics for actual utilization data.

        Args:
            resource_amount: Amount of resource allocated
            cost: Cost of resource

        Returns:
            Estimated utilization (0.0-1.0)
        """
        if resource_amount == 0 or cost == 0:
            return 0.0

        # Simple heuristic: assume cost correlates with usage
        # In reality, use actual usage metrics from Prometheus
        cost_per_unit = cost / resource_amount
        # Normalize to 0-1 range (assuming typical cloud pricing)
        estimated = min(cost_per_unit / 0.1, 1.0)
        return max(estimated, 0.0)

    @staticmethod
    def _generate_cpu_recommendation(cpu_cores: float, utilization: float) -> str:
        """Generate CPU optimization recommendation."""
        if utilization < 0.1:
            return (
                f"Consider reducing CPU request from {cpu_cores:.2f} cores. "
                f"Current utilization is very low ({utilization:.1%})."
            )
        elif utilization < 0.3:
            target = cpu_cores * 0.5
            return (
                f"Reduce CPU request from {cpu_cores:.2f} to ~{target:.2f} cores. "
                f"Current utilization: {utilization:.1%}."
            )
        else:
            target = cpu_cores * 0.7
            return (
                f"Consider reducing CPU request to ~{target:.2f} cores. "
                f"Current utilization: {utilization:.1%}."
            )

    @staticmethod
    def _generate_memory_recommendation(memory_gb: float, utilization: float) -> str:
        """Generate memory optimization recommendation."""
        if utilization < 0.1:
            return (
                f"Consider reducing memory request from {memory_gb:.2f}GB. "
                f"Current utilization is very low ({utilization:.1%})."
            )
        elif utilization < 0.3:
            target = memory_gb * 0.5
            return (
                f"Reduce memory request from {memory_gb:.2f}GB to "
                f"~{target:.2f}GB. Current utilization: {utilization:.1%}."
            )
        else:
            target = memory_gb * 0.7
            return (
                f"Consider reducing memory request to ~{target:.2f}GB. "
                f"Current utilization: {utilization:.1%}."
            )
