"""
Hub-and-Spoke Coordinator - Hierarchical multi-agent coordination pattern.

Implements hub-and-spoke coordination where a central hub agent decomposes
high-level objectives into sub-tasks and delegates them to specialized spoke
agents. Uses Celery chord pattern for parallel execution with synchronous
aggregation.

Issue #46: Multi-Agent Orchestration Platform - Hub-and-Spoke Coordinator
"""

import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import redis
from celery import Celery
from pydantic import BaseModel, Field, field_validator
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class DecompositionStrategy(str, Enum):
    """Objective decomposition strategies."""

    FUNCTIONAL = "functional"  # By functional area (UI, API, DB)
    SEQUENTIAL = "sequential"  # By execution order (step 1, 2, 3)
    PARALLEL = "parallel"  # Independent parallel tasks
    HIERARCHICAL = "hierarchical"  # Nested sub-objectives
    DOMAIN = "domain"  # By domain/business area


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SpokeStatus(str, Enum):
    """Spoke agent execution status."""

    IDLE = "idle"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class HubAgent(BaseModel):
    """
    Hub agent model - coordinator role.

    The hub agent receives high-level objectives, decomposes them into
    sub-tasks, and coordinates spoke agents.
    """

    hub_id: str = Field(..., description="Unique hub agent identifier")
    hub_type: str = Field(
        default="coordinator",
        description="Type of hub agent",
    )
    specializations: List[str] = Field(
        default_factory=list,
        description="Hub specializations for objective decomposition",
    )
    decomposition_strategy: DecompositionStrategy = Field(
        default=DecompositionStrategy.FUNCTIONAL,
        description="Default decomposition strategy",
    )
    max_spokes: int = Field(
        default=10,
        description="Maximum number of spoke agents",
        ge=1,
        le=100,
    )
    timeout: int = Field(
        default=3600,
        description="Hub operation timeout in seconds",
        ge=60,
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional hub metadata",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Hub creation timestamp",
    )

    @field_validator("hub_id", "hub_type")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class SpokeAgent(BaseModel):
    """
    Spoke agent model - specialized worker.

    Spoke agents execute specific sub-tasks delegated by the hub agent.
    """

    spoke_id: str = Field(..., description="Unique spoke agent identifier")
    spoke_type: str = Field(..., description="Type of spoke agent")
    specializations: List[str] = Field(
        ...,
        description="Spoke specializations/capabilities",
    )
    max_concurrent_tasks: int = Field(
        default=3,
        description="Maximum concurrent tasks",
        ge=1,
        le=20,
    )
    priority_weight: int = Field(
        default=10,
        description="Spoke priority weight for selection",
        ge=1,
        le=100,
    )
    available: bool = Field(
        default=True,
        description="Spoke availability status",
    )
    status: SpokeStatus = Field(
        default=SpokeStatus.IDLE,
        description="Current spoke status",
    )
    current_load: int = Field(
        default=0,
        description="Number of active tasks",
        ge=0,
    )
    success_rate: float = Field(
        default=1.0,
        description="Historical success rate (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional spoke metadata",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Spoke creation timestamp",
    )

    @field_validator("specializations")
    @classmethod
    def validate_specializations(cls, v: List[str]) -> List[str]:
        """Validate specializations list is not empty."""
        if not v:
            raise ValueError("Spoke must have at least one specialization")
        return [spec.lower().strip() for spec in v]

    @field_validator("spoke_id", "spoke_type")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @property
    def has_capacity(self) -> bool:
        """Check if spoke has capacity for more tasks."""
        return (
            self.available
            and self.status != SpokeStatus.FAILED
            and self.current_load < self.max_concurrent_tasks
        )

    @property
    def load_percentage(self) -> float:
        """Calculate spoke load as percentage."""
        if self.max_concurrent_tasks == 0:
            return 100.0
        return (self.current_load / self.max_concurrent_tasks) * 100.0


class Objective(BaseModel):
    """
    High-level objective for hub agent.

    The objective contains the goal to be achieved and context for
    decomposition into sub-tasks.
    """

    objective_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique objective identifier",
    )
    description: str = Field(
        ...,
        description="High-level objective description",
    )
    requirements: List[str] = Field(
        default_factory=list,
        description="Specific requirements for objective",
    )
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Constraints (timeline, resources, etc.)",
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for decomposition",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Objective priority",
    )
    decomposition_strategy: Optional[DecompositionStrategy] = Field(
        default=None,
        description="Override decomposition strategy",
    )
    timeout: int = Field(
        default=3600,
        description="Objective timeout in seconds",
        ge=60,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Objective creation timestamp",
    )

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is not empty."""
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()


class SubTask(BaseModel):
    """
    Sub-task decomposed from objective.

    Represents a specific task to be delegated to a spoke agent.
    """

    subtask_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique sub-task identifier",
    )
    objective_id: str = Field(
        ...,
        description="Parent objective identifier",
    )
    description: str = Field(
        ...,
        description="Sub-task description",
    )
    required_specializations: List[str] = Field(
        ...,
        description="Required spoke specializations",
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Sub-task IDs this task depends on",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Sub-task priority",
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Sub-task execution context",
    )
    estimated_duration: int = Field(
        default=600,
        description="Estimated duration in seconds",
        ge=1,
    )
    timeout: int = Field(
        default=1800,
        description="Sub-task timeout in seconds",
        ge=1,
    )
    assigned_spoke_id: Optional[str] = Field(
        default=None,
        description="Assigned spoke agent ID",
    )
    status: SpokeStatus = Field(
        default=SpokeStatus.IDLE,
        description="Sub-task status",
    )
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Sub-task execution result",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Sub-task creation timestamp",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Sub-task completion timestamp",
    )

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is not empty."""
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()

    @field_validator("required_specializations")
    @classmethod
    def validate_specializations(cls, v: List[str]) -> List[str]:
        """Validate specializations list is not empty."""
        if not v:
            raise ValueError("Sub-task must require at least one specialization")
        return [spec.lower().strip() for spec in v]


class HubSpokeResult(BaseModel):
    """
    Aggregated result from hub-and-spoke execution.

    Contains results from all spoke agents and synthesized output from hub.
    """

    objective_id: str = Field(..., description="Objective identifier")
    hub_id: str = Field(..., description="Hub agent identifier")
    success: bool = Field(..., description="Overall success status")
    total_subtasks: int = Field(
        default=0,
        description="Total number of sub-tasks",
        ge=0,
    )
    completed_subtasks: int = Field(
        default=0,
        description="Number of completed sub-tasks",
        ge=0,
    )
    failed_subtasks: int = Field(
        default=0,
        description="Number of failed sub-tasks",
        ge=0,
    )
    spoke_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Results from spoke agents",
    )
    synthesized_output: Dict[str, Any] = Field(
        default_factory=dict,
        description="Synthesized output from hub",
    )
    artifacts: List[str] = Field(
        default_factory=list,
        description="Artifacts produced by spokes",
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Error messages from failed sub-tasks",
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution start timestamp",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Execution completion timestamp",
    )
    duration_seconds: float = Field(
        default=0.0,
        description="Execution duration in seconds",
        ge=0.0,
    )

    @property
    def success_rate(self) -> float:
        """Calculate success rate of sub-tasks."""
        if self.total_subtasks == 0:
            return 0.0
        return (self.completed_subtasks / self.total_subtasks) * 100.0


class HubSpokeCoordinator:
    """
    Hub-and-Spoke coordination pattern implementation.

    Manages hierarchical coordination where a hub agent decomposes objectives
    into sub-tasks and delegates them to specialized spoke agents using
    Celery chord pattern for parallel execution and aggregation.
    """

    # Redis key prefixes
    HUB_PREFIX = "hub:"
    SPOKE_PREFIX = "spoke:"
    OBJECTIVE_PREFIX = "objective:"
    SUBTASK_PREFIX = "subtask:"
    HUB_INDEX_KEY = "hubs:index"
    SPOKE_INDEX_KEY = "spokes:index"
    SPOKE_SPEC_INDEX = "spokes:spec:"

    # TTL settings
    HUB_TTL_SECONDS = 3600  # 1 hour
    SPOKE_TTL_SECONDS = 3600  # 1 hour
    OBJECTIVE_TTL_SECONDS = 86400  # 24 hours
    SUBTASK_TTL_SECONDS = 86400  # 24 hours

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        celery_broker_url: Optional[str] = None,
        celery_backend_url: Optional[str] = None,
    ):  # noqa: E501
        """
        Initialize the hub-and-spoke coordinator.

        Args:
            redis_url: Redis connection URL
            redis_db: Redis database number
            redis_password: Redis password (if required)
            celery_broker_url: Celery broker URL (defaults to redis_url)
            celery_backend_url: Celery backend URL (defaults to redis_url)

        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self.redis_url = redis_url

        try:
            # Initialize Redis client
            self.redis_client = redis.from_url(
                redis_url,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                max_connections=20,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_url}")

        except (RedisConnectionError, RedisError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise RedisConnectionError(
                f"Cannot connect to Redis at {redis_url}: {e}"
            ) from e

        # Initialize Celery
        broker = celery_broker_url or redis_url
        backend = celery_backend_url or redis_url

        self.celery_app = Celery(
            "hub_spoke_coordinator",
            broker=broker,
            backend=backend,
        )

        # Configure Celery
        self.celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            enable_utc=True,
            task_track_started=True,
            task_time_limit=3600,  # 1 hour hard limit
            task_soft_time_limit=3300,  # 55 minutes soft limit
            result_expires=86400,  # Results expire after 24 hours
            worker_prefetch_multiplier=1,
            task_acks_late=True,
            task_reject_on_worker_lost=True,
        )

        logger.info("Celery app initialized")

    def register_hub(
        self,
        hub_id: str,
        hub_type: str = "coordinator",
        specializations: Optional[List[str]] = None,
        decomposition_strategy: DecompositionStrategy = (
            DecompositionStrategy.FUNCTIONAL
        ),
        max_spokes: int = 10,
        timeout: int = 3600,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Register a hub agent.

        Args:
            hub_id: Unique hub identifier
            hub_type: Type of hub agent
            specializations: Hub specializations
            decomposition_strategy: Default decomposition strategy
            max_spokes: Maximum number of spoke agents
            timeout: Hub operation timeout in seconds
            metadata: Additional metadata

        Returns:
            True if registration successful

        Raises:
            ValueError: If validation fails
            RedisError: If Redis operation fails
        """
        try:
            hub = HubAgent(
                hub_id=hub_id,
                hub_type=hub_type,
                specializations=specializations or [],
                decomposition_strategy=decomposition_strategy,
                max_spokes=max_spokes,
                timeout=timeout,
                metadata=metadata or {},
            )

            # Serialize hub data
            hub_data = hub.model_dump_json()
            hub_key = f"{self.HUB_PREFIX}{hub_id}"

            # Store hub data with TTL
            pipeline = self.redis_client.pipeline()
            pipeline.setex(hub_key, self.HUB_TTL_SECONDS, hub_data)
            pipeline.sadd(self.HUB_INDEX_KEY, hub_id)
            pipeline.execute()

            logger.info(f"Registered hub {hub_id} of type {hub_type}")
            return True

        except ValueError as e:
            logger.error(f"Hub validation failed: {e}")
            raise

        except RedisError as e:
            logger.error(f"Failed to register hub {hub_id}: {e}")
            raise

    def register_spoke(
        self,
        spoke_id: str,
        spoke_type: str,
        specializations: List[str],
        max_concurrent_tasks: int = 3,
        priority_weight: int = 10,
        available: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Register a spoke agent.

        Args:
            spoke_id: Unique spoke identifier
            spoke_type: Type of spoke agent
            specializations: Spoke specializations/capabilities
            max_concurrent_tasks: Maximum concurrent tasks
            priority_weight: Spoke priority weight (1-100)
            available: Spoke availability status
            metadata: Additional metadata

        Returns:
            True if registration successful

        Raises:
            ValueError: If validation fails
            RedisError: If Redis operation fails
        """
        try:
            spoke = SpokeAgent(
                spoke_id=spoke_id,
                spoke_type=spoke_type,
                specializations=specializations,
                max_concurrent_tasks=max_concurrent_tasks,
                priority_weight=priority_weight,
                available=available,
                metadata=metadata or {},
            )

            # Serialize spoke data
            spoke_data = spoke.model_dump_json()
            spoke_key = f"{self.SPOKE_PREFIX}{spoke_id}"

            # Store spoke data with TTL
            pipeline = self.redis_client.pipeline()
            pipeline.setex(spoke_key, self.SPOKE_TTL_SECONDS, spoke_data)
            pipeline.sadd(self.SPOKE_INDEX_KEY, spoke_id)

            # Add to specialization indices
            for spec in spoke.specializations:
                spec_index = f"{self.SPOKE_SPEC_INDEX}{spec}"
                pipeline.sadd(spec_index, spoke_id)

            pipeline.execute()

            logger.info(
                f"Registered spoke {spoke_id} of type {spoke_type} "
                f"with specializations: {specializations}"
            )
            return True

        except ValueError as e:
            logger.error(f"Spoke validation failed: {e}")
            raise

        except RedisError as e:
            logger.error(f"Failed to register spoke {spoke_id}: {e}")
            raise

    def decompose_objective(
        self,
        objective: Objective,
        hub_agent: HubAgent,
    ) -> List[SubTask]:
        """
        Decompose objective into sub-tasks using hub's strategy.

        Args:
            objective: Objective to decompose
            hub_agent: Hub agent performing decomposition

        Returns:
            List of sub-tasks

        Raises:
            ValueError: If decomposition fails
        """
        try:
            strategy = (
                objective.decomposition_strategy or hub_agent.decomposition_strategy
            )

            logger.info(
                f"Decomposing objective {objective.objective_id} "
                f"using {strategy.value} strategy"
            )

            subtasks = []

            if strategy == DecompositionStrategy.FUNCTIONAL:
                subtasks = self._decompose_functional(objective)
            elif strategy == DecompositionStrategy.SEQUENTIAL:
                subtasks = self._decompose_sequential(objective)
            elif strategy == DecompositionStrategy.PARALLEL:
                subtasks = self._decompose_parallel(objective)
            elif strategy == DecompositionStrategy.HIERARCHICAL:
                subtasks = self._decompose_hierarchical(objective)
            elif strategy == DecompositionStrategy.DOMAIN:
                subtasks = self._decompose_domain(objective)
            else:
                raise ValueError(f"Unknown decomposition strategy: {strategy}")

            # Store sub-tasks in Redis
            for subtask in subtasks:
                subtask_key = f"{self.SUBTASK_PREFIX}{subtask.subtask_id}"
                self.redis_client.setex(
                    subtask_key,
                    self.SUBTASK_TTL_SECONDS,
                    subtask.model_dump_json(),
                )

            logger.info(
                f"Decomposed objective {objective.objective_id} "
                f"into {len(subtasks)} sub-tasks"
            )

            return subtasks

        except Exception as e:
            logger.error(f"Failed to decompose objective: {e}")
            raise ValueError(f"Decomposition failed: {e}") from e

    def _decompose_functional(self, objective: Objective) -> List[SubTask]:
        """
        Decompose by functional area (UI, API, Database, Infrastructure).

        Args:
            objective: Objective to decompose

        Returns:
            List of functional sub-tasks
        """
        subtasks = []

        # Parse objective description for functional areas
        description_lower = objective.description.lower()

        # API/Backend development
        if any(
            keyword in description_lower
            for keyword in [
                "api",
                "backend",
                "endpoint",
                "service",
                "server",
            ]
        ):
            subtasks.append(
                SubTask(
                    objective_id=objective.objective_id,
                    description=(
                        f"Design and implement API/backend for: "
                        f"{objective.description}"
                    ),
                    required_specializations=list(
                        [
                            "api-development",
                            "backend-engineer",
                        ]
                    ),
                    priority=objective.priority,
                    context={
                        **objective.context,
                        "functional_area": "backend",
                    },
                    timeout=objective.timeout // 3,
                )
            )

        # UI/Frontend development
        if any(
            keyword in description_lower
            for keyword in [
                "ui",
                "frontend",
                "interface",
                "design",
                "user experience",
            ]
        ):
            subtasks.append(
                SubTask(
                    objective_id=objective.objective_id,
                    description=(
                        f"Design and implement UI/frontend for: "
                        f"{objective.description}"
                    ),
                    required_specializations=list(
                        [
                            "ui-development",
                            "frontend-engineer",
                        ]
                    ),
                    priority=objective.priority,
                    context={
                        **objective.context,
                        "functional_area": "frontend",
                    },
                    timeout=objective.timeout // 3,
                )
            )

        # Database/Data layer
        if any(
            keyword in description_lower
            for keyword in [
                "database",
                "data",
                "storage",
                "schema",
                "migration",
            ]
        ):
            subtasks.append(
                SubTask(
                    objective_id=objective.objective_id,
                    description=(
                        f"Design and implement database/data layer for: "
                        f"{objective.description}"
                    ),
                    required_specializations=list(
                        [
                            "database-design",
                            "data-engineer",
                        ]
                    ),
                    priority=objective.priority,
                    context={
                        **objective.context,
                        "functional_area": "database",
                    },
                    timeout=objective.timeout // 3,
                )
            )

        # Infrastructure/DevOps
        if any(
            keyword in description_lower
            for keyword in [
                "infrastructure",
                "deploy",
                "cloud",
                "devops",
                "setup",
            ]
        ):
            subtasks.append(
                SubTask(
                    objective_id=objective.objective_id,
                    description=(
                        f"Set up infrastructure for: " f"{objective.description}"
                    ),
                    required_specializations=list(
                        [
                            "infrastructure",
                            "devops-engineer",
                        ]
                    ),
                    priority=objective.priority,
                    context={
                        **objective.context,
                        "functional_area": "infrastructure",
                    },
                    timeout=objective.timeout // 3,
                )
            )

        # Testing/QA
        if any(
            keyword in description_lower
            for keyword in [
                "test",
                "quality",
                "qa",
                "validation",
            ]
        ):
            subtasks.append(
                SubTask(
                    objective_id=objective.objective_id,
                    description=(f"Implement testing for: {objective.description}"),
                    required_specializations=["testing", "qa-engineer"],
                    priority=objective.priority,
                    context={
                        **objective.context,
                        "functional_area": "testing",
                    },
                    timeout=objective.timeout // 3,
                    dependencies=[st.subtask_id for st in subtasks],
                )
            )

        # If no specific areas detected, create generic sub-tasks
        if not subtasks:
            subtasks = [
                SubTask(
                    objective_id=objective.objective_id,
                    description=f"Implement: {objective.description}",
                    required_specializations=["general"],
                    priority=objective.priority,
                    context=objective.context,
                    timeout=objective.timeout,
                )
            ]

        return subtasks

    def _decompose_sequential(self, objective: Objective) -> List[SubTask]:
        """
        Decompose into sequential steps with dependencies.

        Args:
            objective: Objective to decompose

        Returns:
            List of sequential sub-tasks
        """
        # Create 3-phase sequential execution
        phases = [
            {
                "name": "Planning and Design",
                "specializations": ["architecture", "design"],
            },
            {
                "name": "Implementation",
                "specializations": ["development", "implementation"],
            },
            {
                "name": "Testing and Validation",
                "specializations": ["testing", "validation"],
            },
        ]

        subtasks = []
        previous_id = None

        for i, phase in enumerate(phases):
            subtask = SubTask(
                objective_id=objective.objective_id,
                description=f"{phase['name']}: {objective.description}",
                required_specializations=list(phase["specializations"]),
                priority=objective.priority,
                context={
                    **objective.context,
                    "phase": phase["name"],
                    "phase_number": i + 1,
                },
                dependencies=[previous_id] if previous_id else [],
                timeout=objective.timeout // len(phases),
            )
            subtasks.append(subtask)
            previous_id = subtask.subtask_id

        return subtasks

    def _decompose_parallel(self, objective: Objective) -> List[SubTask]:
        """
        Decompose into independent parallel tasks.

        Args:
            objective: Objective to decompose

        Returns:
            List of parallel sub-tasks
        """
        # Create parallel independent tasks
        parallel_areas = [
            {"name": "Component A", "specializations": ["development"]},
            {"name": "Component B", "specializations": ["development"]},
            {"name": "Component C", "specializations": ["development"]},
        ]

        subtasks = []

        for i, area in enumerate(parallel_areas):
            subtask = SubTask(
                objective_id=objective.objective_id,
                description=f"{area['name']}: {objective.description}",
                required_specializations=list(area["specializations"]),
                priority=objective.priority,
                context={
                    **objective.context,
                    "component": area["name"],
                    "component_number": i + 1,
                },
                dependencies=[],  # No dependencies for parallel execution
                timeout=objective.timeout,
            )
            subtasks.append(subtask)

        return subtasks

    def _decompose_hierarchical(self, objective: Objective) -> List[SubTask]:
        """
        Decompose with nested sub-objectives.

        Args:
            objective: Objective to decompose

        Returns:
            List of hierarchical sub-tasks
        """
        # Create hierarchical structure with parent-child relationships
        subtasks = []

        # Level 1: High-level sub-objectives
        parent_subtask = SubTask(
            objective_id=objective.objective_id,
            description=f"Coordinate: {objective.description}",
            required_specializations=["coordination", "management"],
            priority=objective.priority,
            context={
                **objective.context,
                "level": 1,
            },
            timeout=objective.timeout // 2,
        )
        subtasks.append(parent_subtask)

        # Level 2: Detailed implementation tasks
        child_areas = [
            "Requirements Analysis",
            "Architecture Design",
            "Implementation",
        ]

        for area in child_areas:
            child_subtask = SubTask(
                objective_id=objective.objective_id,
                description=f"{area}: {objective.description}",
                required_specializations=["development"],
                priority=objective.priority,
                context={
                    **objective.context,
                    "level": 2,
                    "parent": parent_subtask.subtask_id,
                },
                dependencies=[parent_subtask.subtask_id],
                timeout=objective.timeout // 4,
            )
            subtasks.append(child_subtask)

        return subtasks

    def _decompose_domain(self, objective: Objective) -> List[SubTask]:
        """
        Decompose by domain/business area.

        Args:
            objective: Objective to decompose

        Returns:
            List of domain-specific sub-tasks
        """
        # Extract domain from context or description
        domains = objective.context.get("domains", [])

        if not domains:
            # Default domains
            domains = ["business-logic", "data-layer", "presentation"]

        subtasks = []

        for domain in domains:
            subtask = SubTask(
                objective_id=objective.objective_id,
                description=f"Implement {domain} for: {objective.description}",
                required_specializations=[domain.lower(), "domain-expert"],
                priority=objective.priority,
                context={
                    **objective.context,
                    "domain": domain,
                },
                timeout=objective.timeout // len(domains),
            )
            subtasks.append(subtask)

        return subtasks

    def match_spoke(
        self,
        sub_task: SubTask,
        spokes: Optional[List[SpokeAgent]] = None,
    ) -> Optional[SpokeAgent]:
        """
        Match sub-task to best spoke agent based on specialization.

        Args:
            sub_task: Sub-task to match
            spokes: Optional list of spoke agents (fetched if not provided)

        Returns:
            Best matching spoke agent or None

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            # Get available spokes if not provided
            if spokes is None:
                spokes = self._get_available_spokes()

            if not spokes:
                logger.warning("No available spokes for matching")
                return None

            # Score each spoke
            scored_spokes: List[Tuple[SpokeAgent, float]] = []

            for spoke in spokes:
                # Skip unavailable or at-capacity spokes
                if not spoke.has_capacity:
                    continue

                # Calculate match score
                score = self._calculate_spoke_score(
                    spoke,
                    sub_task.required_specializations,
                    sub_task.priority,
                )

                if score > 0.0:
                    scored_spokes.append((spoke, score))

            if not scored_spokes:
                logger.warning(
                    f"No suitable spoke found for sub-task " f"{sub_task.subtask_id}"
                )
                return None

            # Sort by score (descending)
            scored_spokes.sort(key=lambda x: x[1], reverse=True)

            best_spoke = scored_spokes[0][0]

            logger.info(
                f"Matched sub-task {sub_task.subtask_id} to spoke "
                f"{best_spoke.spoke_id} (score: {scored_spokes[0][1]:.3f})"
            )

            return best_spoke

        except RedisError as e:
            logger.error(f"Failed to match spoke: {e}")
            raise

    def _get_available_spokes(self) -> List[SpokeAgent]:
        """
        Get all available spoke agents.

        Returns:
            List of available spoke agents
        """
        try:
            spoke_ids = self.redis_client.smembers(self.SPOKE_INDEX_KEY)

            spokes = []

            for spoke_id in spoke_ids:
                spoke_key = f"{self.SPOKE_PREFIX}{spoke_id}"
                spoke_data = self.redis_client.get(spoke_key)

                if not spoke_data:
                    # Spoke expired, clean up
                    self.redis_client.srem(self.SPOKE_INDEX_KEY, spoke_id)
                    continue

                spoke = SpokeAgent.model_validate_json(spoke_data)
                spokes.append(spoke)

            return spokes

        except RedisError as e:
            logger.error(f"Failed to get available spokes: {e}")
            return []

    def _calculate_spoke_score(
        self,
        spoke: SpokeAgent,
        required_specs: List[str],
        priority: TaskPriority,
    ) -> float:
        """
        Calculate spoke matching score.

        Args:
            spoke: Spoke agent
            required_specs: Required specializations
            priority: Task priority

        Returns:
            Match score (0.0 to 1.0)
        """
        # Normalize specializations to lowercase
        spoke_specs = {spec.lower() for spec in spoke.specializations}
        required_specs_set = {spec.lower() for spec in required_specs}

        # Calculate specialization match
        matched = spoke_specs.intersection(required_specs_set)
        missing = required_specs_set - spoke_specs

        if not matched:
            return 0.0

        if not missing:
            spec_score = 1.0  # Perfect match
        else:
            spec_score = len(matched) / len(required_specs_set)

        # Load factor (prefer less loaded spokes)
        load_factor = 1.0 - (spoke.current_load / spoke.max_concurrent_tasks)

        # Priority weight factor
        priority_factor = spoke.priority_weight / 100.0

        # Success rate factor
        success_factor = spoke.success_rate

        # Weighted combination
        score = (
            spec_score * 0.5  # 50% specialization match
            + load_factor * 0.2  # 20% load balancing
            + priority_factor * 0.15  # 15% priority weight
            + success_factor * 0.15  # 15% success rate
        )

        return min(1.0, max(0.0, score))

    def delegate_to_spoke(
        self,
        hub: HubAgent,
        spoke: SpokeAgent,
        sub_task: SubTask,
    ) -> Dict[str, Any]:
        """
        Delegate sub-task to spoke agent.

        Args:
            hub: Hub agent delegating the task
            spoke: Spoke agent receiving the task
            sub_task: Sub-task to delegate

        Returns:
            Delegation result dictionary

        Raises:
            ValueError: If delegation fails validation
            RedisError: If Redis operation fails
        """
        try:
            # Verify spoke has capacity
            if not spoke.has_capacity:
                raise ValueError(
                    f"Spoke {spoke.spoke_id} has no capacity "
                    f"(load: {spoke.current_load}/"
                    f"{spoke.max_concurrent_tasks})"
                )

            # Update sub-task status
            sub_task.assigned_spoke_id = spoke.spoke_id
            sub_task.status = SpokeStatus.ASSIGNED

            # Store updated sub-task
            subtask_key = f"{self.SUBTASK_PREFIX}{sub_task.subtask_id}"
            self.redis_client.setex(
                subtask_key,
                self.SUBTASK_TTL_SECONDS,
                sub_task.model_dump_json(),
            )

            # Update spoke load
            spoke.current_load += 1
            spoke.status = SpokeStatus.ASSIGNED

            spoke_key = f"{self.SPOKE_PREFIX}{spoke.spoke_id}"
            self.redis_client.setex(
                spoke_key,
                self.SPOKE_TTL_SECONDS,
                spoke.model_dump_json(),
            )  # noqa: E501

            delegation_result = {
                "subtask_id": sub_task.subtask_id,
                "hub_id": hub.hub_id,
                "spoke_id": spoke.spoke_id,
                "spoke_type": spoke.spoke_type,
                "delegated_at": datetime.now(timezone.utc).isoformat(),
                "description": sub_task.description,
                "required_specializations": sub_task.required_specializations,
                "priority": sub_task.priority.value,
                "timeout": sub_task.timeout,
            }

            logger.info(
                f"Delegated sub-task {sub_task.subtask_id} from hub "
                f"{hub.hub_id} to spoke {spoke.spoke_id}"
            )

            return delegation_result

        except ValueError as e:
            logger.error(f"Delegation validation failed: {e}")
            raise

        except RedisError as e:
            logger.error(f"Failed to delegate to spoke: {e}")
            raise

    def execute_hub_spoke(
        self,
        objective: Objective,
        hub_id: str,
        spoke_ids: Optional[List[str]] = None,
    ) -> HubSpokeResult:  # noqa: E501
        """
        Execute hub-and-spoke coordination for objective.

        Uses Celery chord pattern: parallel spoke execution → hub aggregation.

        Args:
            objective: Objective to execute
            hub_id: Hub agent identifier
            spoke_ids: Optional list of specific spoke IDs to use

        Returns:
            HubSpokeResult with aggregated results

        Raises:
            ValueError: If hub not found or validation fails
            RuntimeError: If execution fails
        """
        started_at = datetime.now(timezone.utc)

        try:
            # Get hub agent
            hub_key = f"{self.HUB_PREFIX}{hub_id}"
            hub_data = self.redis_client.get(hub_key)

            if not hub_data:
                raise ValueError(f"Hub {hub_id} not found")

            hub = HubAgent.model_validate_json(hub_data)

            logger.info(
                f"Starting hub-and-spoke execution for objective "
                f"{objective.objective_id} with hub {hub_id}"
            )

            # Store objective
            objective_key = f"{self.OBJECTIVE_PREFIX}{objective.objective_id}"
            self.redis_client.setex(
                objective_key,
                self.OBJECTIVE_TTL_SECONDS,
                objective.model_dump_json(),
            )

            # Decompose objective into sub-tasks
            subtasks = self.decompose_objective(objective, hub)

            if not subtasks:
                raise ValueError("No sub-tasks generated from objective")

            # Get available spokes
            if spoke_ids:
                spokes = []
                for spoke_id in spoke_ids:
                    spoke_key = f"{self.SPOKE_PREFIX}{spoke_id}"
                    spoke_data = self.redis_client.get(spoke_key)
                    if spoke_data:
                        spoke_agent = SpokeAgent.model_validate_json(spoke_data)
                        spokes.append(spoke_agent)
            else:
                spokes = self._get_available_spokes()

            if not spokes:
                raise ValueError("No available spokes for execution")

            # Match and delegate sub-tasks to spokes
            delegations = []

            for subtask in subtasks:
                spoke = self.match_spoke(subtask, spokes)

                if not spoke:
                    # Handle no matching spoke
                    logger.warning(
                        f"No spoke available for sub-task "
                        f"{subtask.subtask_id}, marking as failed"
                    )
                    subtask.status = SpokeStatus.FAILED
                    subtask.error = "No suitable spoke found"
                    continue

                # Delegate to spoke
                delegation = self.delegate_to_spoke(hub, spoke, subtask)
                delegations.append(delegation)

            # Execute sub-tasks using Celery chord
            # Note: In production, this would create actual Celery tasks
            # For now, we simulate the execution
            spoke_results = []

            for delegation in delegations:
                # Simulate spoke execution
                result = self._simulate_spoke_execution(
                    delegation["subtask_id"],
                    delegation["spoke_id"],
                )
                spoke_results.append(result)

            # Aggregate results
            completed = sum(1 for r in spoke_results if r["success"])
            failed = sum(1 for r in spoke_results if not r["success"])

            synthesized_output = self.aggregate_results(hub, spoke_results)

            # Collect artifacts and errors
            artifacts = []
            errors = []

            for result in spoke_results:
                if result.get("artifacts"):
                    artifacts.extend(result["artifacts"])
                if result.get("error"):
                    errors.append(result["error"])

            completed_at = datetime.now(timezone.utc)
            duration = (completed_at - started_at).total_seconds()

            hub_spoke_result = HubSpokeResult(
                objective_id=objective.objective_id,
                hub_id=hub_id,
                success=(failed == 0),
                total_subtasks=len(subtasks),
                completed_subtasks=completed,
                failed_subtasks=failed,
                spoke_results=spoke_results,
                synthesized_output=synthesized_output,
                artifacts=artifacts,
                errors=errors,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )

            logger.info(
                f"Hub-and-spoke execution completed for objective "
                f"{objective.objective_id}: {completed}/{len(subtasks)} "
                f"sub-tasks completed"
            )

            return hub_spoke_result

        except ValueError as e:
            logger.error(f"Validation failed: {e}")
            raise

        except Exception as e:
            logger.error(f"Hub-and-spoke execution failed: {e}")
            raise RuntimeError(f"Execution failed: {e}") from e

    def _simulate_spoke_execution(
        self,
        subtask_id: str,
        spoke_id: str,
    ) -> Dict[str, Any]:
        """
        Simulate spoke execution (placeholder for actual Celery task).

        In production, this would be a Celery task that executes the sub-task.

        Args:
            subtask_id: Sub-task identifier
            spoke_id: Spoke agent identifier

        Returns:
            Execution result dictionary
        """
        # Get sub-task
        subtask_key = f"{self.SUBTASK_PREFIX}{subtask_id}"
        subtask_data = self.redis_client.get(subtask_key)

        if not subtask_data:
            return {
                "subtask_id": subtask_id,
                "spoke_id": spoke_id,
                "success": False,
                "error": "Sub-task not found",
            }

        subtask = SubTask.model_validate_json(subtask_data)

        # Simulate execution
        subtask.status = SpokeStatus.EXECUTING

        # Update in Redis
        self.redis_client.setex(
            subtask_key,
            self.SUBTASK_TTL_SECONDS,
            subtask.model_dump_json(),
        )

        # Simulate work (in production, this would be actual task execution)
        # For now, assume success
        subtask.status = SpokeStatus.COMPLETED
        subtask.completed_at = datetime.now(timezone.utc)
        subtask.result = {
            "status": "completed",
            "output": f"Completed: {subtask.description}",
        }

        # Update in Redis
        self.redis_client.setex(
            subtask_key,
            self.SUBTASK_TTL_SECONDS,
            subtask.model_dump_json(),
        )

        # Update spoke load
        spoke_key = f"{self.SPOKE_PREFIX}{spoke_id}"
        spoke_data = self.redis_client.get(spoke_key)

        if spoke_data:
            spoke = SpokeAgent.model_validate_json(spoke_data)
            spoke.current_load = max(0, spoke.current_load - 1)
            spoke.status = (
                SpokeStatus.IDLE if spoke.current_load == 0 else SpokeStatus.EXECUTING
            )
            self.redis_client.setex(
                spoke_key,
                self.SPOKE_TTL_SECONDS,
                spoke.model_dump_json(),
            )

        return {
            "subtask_id": subtask_id,
            "spoke_id": spoke_id,
            "spoke_type": spoke.spoke_type if spoke_data else "unknown",
            "success": True,
            "description": subtask.description,
            "output": subtask.result,
            "artifacts": [f"artifact_{subtask_id}.json"],
            "started_at": subtask.created_at.isoformat(),
            "completed_at": (
                subtask.completed_at.isoformat() if subtask.completed_at else None
            ),
        }

    def aggregate_results(
        self,
        hub: HubAgent,
        spoke_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Aggregate results from spoke agents and synthesize output.

        Args:
            hub: Hub agent performing aggregation
            spoke_results: List of results from spoke agents

        Returns:
            Synthesized output dictionary
        """
        try:
            # Calculate statistics
            total_spokes = len(spoke_results)
            successful_spokes = sum(1 for r in spoke_results if r["success"])
            failed_spokes = total_spokes - successful_spokes
            success_rate = (
                (successful_spokes / total_spokes * 100) if total_spokes > 0 else 0.0
            )

            # Group results by spoke type
            results_by_type: Dict[str, List[Dict[str, Any]]] = {}

            for result in spoke_results:
                spoke_type = result.get("spoke_type", "unknown")
                if spoke_type not in results_by_type:
                    results_by_type[spoke_type] = []
                results_by_type[spoke_type].append(result)

            # Synthesize summary
            summary = (
                f"Hub {hub.hub_id} coordinated {total_spokes} spoke agents. "
                f"{successful_spokes} completed successfully, "
                f"{failed_spokes} failed. "
                f"Success rate: {success_rate:.1f}%"
            )

            # Collect outputs
            outputs = []
            for result in spoke_results:
                if result["success"] and result.get("output"):
                    outputs.append(result["output"])

            synthesized = {
                "hub_id": hub.hub_id,
                "hub_type": hub.hub_type,
                "total_spokes": total_spokes,
                "successful_spokes": successful_spokes,
                "failed_spokes": failed_spokes,
                "success_rate": success_rate,
                "results_by_type": results_by_type,
                "summary": summary,
                "outputs": outputs,
                "aggregated_at": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(f"Aggregated results from {total_spokes} spokes")

            return synthesized

        except Exception as e:
            logger.error(f"Failed to aggregate results: {e}")
            return {
                "error": f"Aggregation failed: {e}",
                "partial_results": spoke_results,
            }

    def handle_spoke_failure(
        self,
        spoke_id: str,
        sub_task: SubTask,
    ) -> Dict[str, Any]:
        """
        Handle spoke agent failure.

        Args:
            spoke_id: Failed spoke identifier
            sub_task: Sub-task that failed

        Returns:
            Failure handling result
        """
        try:
            logger.warning(
                f"Handling failure for spoke {spoke_id} "
                f"on sub-task {sub_task.subtask_id}"
            )

            # Update sub-task status
            sub_task.status = SpokeStatus.FAILED
            sub_task.error = f"Spoke {spoke_id} failed to complete task"
            sub_task.completed_at = datetime.now(timezone.utc)

            # Store updated sub-task
            subtask_key = f"{self.SUBTASK_PREFIX}{sub_task.subtask_id}"
            self.redis_client.setex(
                subtask_key,
                self.SUBTASK_TTL_SECONDS,
                sub_task.model_dump_json(),
            )

            # Update spoke status
            spoke_key = f"{self.SPOKE_PREFIX}{spoke_id}"
            spoke_data = self.redis_client.get(spoke_key)

            if spoke_data:
                spoke = SpokeAgent.model_validate_json(spoke_data)
                spoke.current_load = max(0, spoke.current_load - 1)
                spoke.status = SpokeStatus.FAILED
                spoke.success_rate = max(0.0, spoke.success_rate - 0.1)

                self.redis_client.setex(
                    spoke_key,
                    self.SPOKE_TTL_SECONDS,
                    spoke.model_dump_json(),
                )

            # Try to find alternative spoke for retry
            alternative_spoke = self.match_spoke(sub_task)

            return {
                "subtask_id": sub_task.subtask_id,
                "failed_spoke_id": spoke_id,
                "failure_handled": True,
                "alternative_spoke_available": (alternative_spoke is not None),
                "alternative_spoke_id": (
                    alternative_spoke.spoke_id if alternative_spoke else None
                ),
                "error": sub_task.error,
                "handled_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to handle spoke failure: {e}")
            return {
                "subtask_id": sub_task.subtask_id,
                "failed_spoke_id": spoke_id,
                "failure_handled": False,
                "error": str(e),
            }

    def get_coordination_status(
        self,
        objective_id: str,
    ) -> Dict[str, Any]:
        """
        Get coordination status for an objective.

        Args:
            objective_id: Objective identifier

        Returns:
            Coordination status dictionary
        """
        try:
            # Get objective
            objective_key = f"{self.OBJECTIVE_PREFIX}{objective_id}"
            objective_data = self.redis_client.get(objective_key)

            if not objective_data:
                return {
                    "objective_id": objective_id,
                    "found": False,
                    "error": "Objective not found",
                }

            objective = Objective.model_validate_json(objective_data)

            # Get all sub-tasks for this objective
            subtask_keys = self.redis_client.keys(f"{self.SUBTASK_PREFIX}*")
            subtasks = []

            for key in subtask_keys:
                subtask_data = self.redis_client.get(key)
                if subtask_data:
                    subtask = SubTask.model_validate_json(subtask_data)
                    if subtask.objective_id == objective_id:
                        subtasks.append(subtask)

            # Calculate statistics
            total_subtasks = len(subtasks)
            completed = sum(1 for st in subtasks if st.status == SpokeStatus.COMPLETED)
            failed = sum(1 for st in subtasks if st.status == SpokeStatus.FAILED)
            executing = sum(1 for st in subtasks if st.status == SpokeStatus.EXECUTING)
            pending = sum(
                1
                for st in subtasks
                if st.status in [SpokeStatus.IDLE, SpokeStatus.ASSIGNED]
            )

            # Get spoke assignments
            spoke_assignments: Dict[str, List[Dict[str, Any]]] = {}
            for subtask in subtasks:
                if subtask.assigned_spoke_id:
                    if subtask.assigned_spoke_id not in spoke_assignments:
                        spoke_assignments[subtask.assigned_spoke_id] = []
                    spoke_assignments[subtask.assigned_spoke_id].append(
                        {
                            "subtask_id": subtask.subtask_id,
                            "description": subtask.description,
                            "status": subtask.status.value,
                        }
                    )

            return {
                "objective_id": objective_id,
                "found": True,
                "description": objective.description,
                "priority": objective.priority.value,
                "created_at": objective.created_at.isoformat(),
                "total_subtasks": total_subtasks,
                "completed": completed,
                "failed": failed,
                "executing": executing,
                "pending": pending,
                "progress_percentage": (
                    (completed / total_subtasks * 100) if total_subtasks > 0 else 0.0
                ),
                "spoke_assignments": spoke_assignments,
                "subtasks": [
                    {
                        "subtask_id": st.subtask_id,
                        "description": st.description,
                        "status": st.status.value,
                        "assigned_spoke_id": st.assigned_spoke_id,
                        "required_specializations": (st.required_specializations),
                    }
                    for st in subtasks
                ],
            }

        except Exception as e:
            logger.error(f"Failed to get coordination status: {e}")
            return {
                "objective_id": objective_id,
                "found": False,
                "error": str(e),
            }

    def get_hub_status(self, hub_id: str) -> Optional[Dict[str, Any]]:
        """
        Get hub agent status.

        Args:
            hub_id: Hub identifier

        Returns:
            Hub status dictionary or None if not found
        """
        try:
            hub_key = f"{self.HUB_PREFIX}{hub_id}"
            hub_data = self.redis_client.get(hub_key)

            if not hub_data:
                return None

            hub = HubAgent.model_validate_json(hub_data)

            # Get TTL
            ttl = self.redis_client.ttl(hub_key)

            return {
                "hub_id": hub.hub_id,
                "hub_type": hub.hub_type,
                "specializations": hub.specializations,
                "decomposition_strategy": hub.decomposition_strategy.value,
                "max_spokes": hub.max_spokes,
                "timeout": hub.timeout,
                "ttl_seconds": ttl,
                "created_at": hub.created_at.isoformat(),
                "metadata": hub.metadata,
            }

        except RedisError as e:
            logger.error(f"Failed to get hub status: {e}")
            return None

    def get_spoke_status(self, spoke_id: str) -> Optional[Dict[str, Any]]:
        """
        Get spoke agent status.

        Args:
            spoke_id: Spoke identifier

        Returns:
            Spoke status dictionary or None if not found
        """
        try:
            spoke_key = f"{self.SPOKE_PREFIX}{spoke_id}"
            spoke_data = self.redis_client.get(spoke_key)

            if not spoke_data:
                return None

            spoke = SpokeAgent.model_validate_json(spoke_data)

            # Get TTL
            ttl = self.redis_client.ttl(spoke_key)

            return {
                "spoke_id": spoke.spoke_id,
                "spoke_type": spoke.spoke_type,
                "specializations": spoke.specializations,
                "available": spoke.available,
                "status": spoke.status.value,
                "current_load": spoke.current_load,
                "max_concurrent_tasks": spoke.max_concurrent_tasks,
                "load_percentage": spoke.load_percentage,
                "has_capacity": spoke.has_capacity,
                "priority_weight": spoke.priority_weight,
                "success_rate": spoke.success_rate,
                "ttl_seconds": ttl,
                "created_at": spoke.created_at.isoformat(),
                "metadata": spoke.metadata,
            }

        except RedisError as e:
            logger.error(f"Failed to get spoke status: {e}")
            return None

    def list_hubs(self) -> List[Dict[str, Any]]:
        """
        List all registered hubs.

        Returns:
            List of hub status dictionaries
        """
        try:
            hub_ids = self.redis_client.smembers(self.HUB_INDEX_KEY)

            hubs = []

            for hub_id in hub_ids:
                status = self.get_hub_status(hub_id)
                if status:
                    hubs.append(status)
                else:
                    # Clean up expired hub
                    self.redis_client.srem(self.HUB_INDEX_KEY, hub_id)

            hubs.sort(key=lambda h: h["hub_id"])

            return hubs

        except RedisError as e:
            logger.error(f"Failed to list hubs: {e}")
            return []

    def list_spokes(
        self,
        filter_specialization: Optional[str] = None,
        available_only: bool = False,
    ) -> List[Dict[str, Any]]:  # noqa: E501
        """
        List all registered spokes with optional filters.

        Args:
            filter_specialization: Filter by specialization
            available_only: Only return available spokes

        Returns:
            List of spoke status dictionaries
        """
        try:
            # Get spoke IDs
            if filter_specialization:
                spec_index = (
                    f"{self.SPOKE_SPEC_INDEX}" f"{filter_specialization.lower()}"
                )
                spoke_ids = self.redis_client.smembers(spec_index)
            else:
                spoke_ids = self.redis_client.smembers(self.SPOKE_INDEX_KEY)

            spokes = []

            for spoke_id in spoke_ids:
                status = self.get_spoke_status(spoke_id)

                if not status:
                    # Clean up expired spoke
                    self.redis_client.srem(self.SPOKE_INDEX_KEY, spoke_id)
                    continue

                # Apply filters
                if available_only and not status["available"]:
                    continue

                spokes.append(status)

            spokes.sort(key=lambda s: s["spoke_id"])

            return spokes

        except RedisError as e:
            logger.error(f"Failed to list spokes: {e}")
            return []

    def close(self) -> None:
        """Close Redis connection."""
        try:
            self.redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
