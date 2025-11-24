"""
Delegation Manager - Intelligent task routing to agents.

Routes tasks to agents based on capability matching, availability, and load
balancing with Redis-based agent registry and health monitoring.
"""

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import redis
from pydantic import BaseModel, Field, field_validator
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RetryBackoff(str, Enum):
    """Retry backoff strategies."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"


class ResourceLimits(BaseModel):
    """Resource limits for agent execution."""

    memory_mb: int = Field(
        default=1024,
        description="Maximum memory in megabytes",
        ge=128,
    )
    cpu_cores: int = Field(
        default=1,
        description="Number of CPU cores",
        ge=1,
    )
    disk_mb: Optional[int] = Field(
        default=None,
        description="Disk space in megabytes",
        ge=0,
    )
    network_mbps: Optional[int] = Field(
        default=None,
        description="Network bandwidth in Mbps",
        ge=0,
    )


class RetryPolicy(BaseModel):
    """Task retry policy configuration."""

    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
        ge=0,
        le=10,
    )
    backoff: RetryBackoff = Field(
        default=RetryBackoff.EXPONENTIAL,
        description="Backoff strategy for retries",
    )
    initial_delay: int = Field(
        default=1,
        description="Initial delay in seconds",
        ge=1,
    )
    max_delay: int = Field(
        default=300,
        description="Maximum delay in seconds",
        ge=1,
    )


class AgentCapability(BaseModel):
    """Agent capability descriptor for registration."""

    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type/category of agent")
    capabilities: List[str] = Field(
        ..., description="List of agent capabilities/skills"
    )
    max_concurrent_tasks: int = Field(
        default=3,
        description="Maximum concurrent tasks",
        ge=1,
        le=100,
    )
    priority_weight: int = Field(
        default=10,
        description="Agent priority weight for selection",
        ge=1,
        le=100,
    )
    available: bool = Field(
        default=True,
        description="Agent availability status",
    )
    resource_limits: ResourceLimits = Field(
        default_factory=ResourceLimits,
        description="Resource limits for agent",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional agent metadata",
    )

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, v: List[str]) -> List[str]:
        """Validate capabilities list is not empty."""
        if not v:
            raise ValueError("Agent must have at least one capability")
        # Normalize capabilities to lowercase
        return [cap.lower().strip() for cap in v]

    @field_validator("agent_id", "agent_type")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class TaskRequest(BaseModel):
    """Task delegation request with routing criteria."""

    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Type of task to execute")
    required_capabilities: List[str] = Field(
        ..., description="Required agent capabilities"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Task priority level",
    )
    estimated_duration: int = Field(
        default=600,
        description="Estimated duration in seconds",
        ge=1,
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task execution context/payload",
    )
    timeout: int = Field(
        default=3600,
        description="Task timeout in seconds",
        ge=1,
    )
    retry_policy: RetryPolicy = Field(
        default_factory=RetryPolicy,
        description="Retry policy for task failures",
    )
    required_agent_type: Optional[str] = Field(
        default=None,
        description="Specific agent type required",
    )
    exclude_agents: List[str] = Field(
        default_factory=list,
        description="Agent IDs to exclude from selection",
    )

    @field_validator("required_capabilities")
    @classmethod
    def validate_capabilities(cls, v: List[str]) -> List[str]:
        """Validate capabilities list is not empty."""
        if not v:
            raise ValueError("Task must require at least one capability")
        # Normalize capabilities to lowercase
        return [cap.lower().strip() for cap in v]


class AgentMatch(BaseModel):
    """Agent matching result with capability scoring."""

    agent_id: str = Field(..., description="Matched agent identifier")
    agent_type: str = Field(..., description="Agent type")
    score: float = Field(
        ...,
        description="Match score (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )
    matched_capabilities: List[str] = Field(
        default_factory=list,
        description="Capabilities that matched requirements",
    )
    missing_capabilities: List[str] = Field(
        default_factory=list,
        description="Required capabilities not present",
    )
    current_load: int = Field(
        default=0,
        description="Current number of active tasks",
        ge=0,
    )
    max_load: int = Field(
        default=3,
        description="Maximum concurrent tasks",
        ge=1,
    )
    available: bool = Field(
        default=True,
        description="Agent availability",
    )
    priority_weight: int = Field(
        default=10,
        description="Agent priority weight",
        ge=1,
    )

    @property
    def has_capacity(self) -> bool:
        """Check if agent has capacity for more tasks."""
        return self.available and self.current_load < self.max_load

    @property
    def load_percentage(self) -> float:
        """Calculate agent load as percentage."""
        if self.max_load == 0:
            return 100.0
        return (self.current_load / self.max_load) * 100.0

    @property
    def effective_score(self) -> float:
        """
        Calculate effective score considering load and priority.

        Lower load and higher priority increase the effective score.
        """
        if not self.available or self.current_load >= self.max_load:
            return 0.0

        # Base score from capability matching
        base_score = self.score

        # Load factor: prefer agents with lower load
        # Normalize load to 0-1 range (inverted so lower load = higher score)
        load_factor = 1.0 - (self.current_load / self.max_load)

        # Priority factor: normalize priority weight to 0-1 range
        priority_factor = self.priority_weight / 100.0

        # Weighted combination
        effective = (
            base_score * 0.5  # 50% capability match
            + load_factor * 0.3  # 30% load balancing
            + priority_factor * 0.2  # 20% priority weight
        )

        return min(1.0, max(0.0, effective))


class DelegationManager:
    """
    Intelligent task routing to agents based on capabilities.

    Manages agent registry, capability matching, load balancing,
    and task delegation with Redis-based persistence.
    """

    # Redis key prefixes
    AGENT_PREFIX = "agent:"
    AGENT_LOAD_PREFIX = "agent:load:"
    AGENT_INDEX_KEY = "agents:index"
    AGENT_TYPE_INDEX = "agents:type:"
    TASK_QUEUE_PREFIX = "task:queue:"

    # Agent TTL settings
    AGENT_TTL_SECONDS = 300  # 5 minutes
    AGENT_HEARTBEAT_INTERVAL = 60  # 1 minute

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        redis_db: int = 0,
        redis_password: Optional[str] = None,
        connection_pool_size: int = 10,
    ):
        """
        Initialize the delegation manager.

        Args:
            redis_url: Redis connection URL
            redis_db: Redis database number
            redis_password: Redis password (if required)
            connection_pool_size: Redis connection pool size

        Raises:
            RedisConnectionError: If Redis connection fails
        """
        self.redis_url = redis_url

        try:
            # Parse Redis URL and create connection pool
            self.redis_client = redis.from_url(
                redis_url,
                db=redis_db,
                password=redis_password,
                decode_responses=True,
                max_connections=connection_pool_size,
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

    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str],
        max_concurrent_tasks: int = 3,
        priority_weight: int = 10,
        available: bool = True,
        resource_limits: Optional[ResourceLimits] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Register an agent with the delegation manager.

        Args:
            agent_id: Unique agent identifier
            agent_type: Type/category of agent
            capabilities: List of agent capabilities
            max_concurrent_tasks: Maximum concurrent tasks
            priority_weight: Agent priority weight (1-100)
            available: Agent availability status
            resource_limits: Resource limits for agent
            metadata: Additional agent metadata

        Returns:
            True if registration successful

        Raises:
            ValueError: If validation fails
            RedisError: If Redis operation fails
        """
        try:
            # Create agent capability descriptor
            agent_cap = AgentCapability(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities,
                max_concurrent_tasks=max_concurrent_tasks,
                priority_weight=priority_weight,
                available=available,
                resource_limits=resource_limits or ResourceLimits(),
                metadata=metadata or {},
            )

            # Serialize agent data
            agent_data = agent_cap.model_dump_json()
            agent_key = f"{self.AGENT_PREFIX}{agent_id}"

            # Store agent data with TTL
            pipeline = self.redis_client.pipeline()
            pipeline.setex(
                agent_key,
                self.AGENT_TTL_SECONDS,
                agent_data,
            )

            # Add to agent index
            pipeline.sadd(self.AGENT_INDEX_KEY, agent_id)

            # Add to agent type index
            type_index_key = f"{self.AGENT_TYPE_INDEX}{agent_type}"
            pipeline.sadd(type_index_key, agent_id)

            # Initialize load counter
            load_key = f"{self.AGENT_LOAD_PREFIX}{agent_id}"
            pipeline.set(load_key, 0)

            pipeline.execute()

            logger.info(
                f"Registered agent {agent_id} of type {agent_type} "
                f"with capabilities: {capabilities}"
            )
            return True

        except ValueError as e:
            logger.error(f"Agent validation failed: {e}")
            raise

        except RedisError as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            raise

    def deregister_agent(self, agent_id: str) -> bool:
        """
        Deregister an agent from the delegation manager.

        Args:
            agent_id: Agent identifier to deregister

        Returns:
            True if deregistration successful, False if agent not found

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            agent_key = f"{self.AGENT_PREFIX}{agent_id}"

            # Get agent data to find type
            agent_data = self.redis_client.get(agent_key)
            if not agent_data:
                # fmt: off
                logger.warning(
                    f"Agent {agent_id} not found for deregistration"
                )
                # fmt: on
                return False

            agent = AgentCapability.model_validate_json(agent_data)

            # Remove agent data
            pipeline = self.redis_client.pipeline()
            pipeline.delete(agent_key)

            # Remove from indices
            pipeline.srem(self.AGENT_INDEX_KEY, agent_id)

            type_index_key = f"{self.AGENT_TYPE_INDEX}{agent.agent_type}"
            pipeline.srem(type_index_key, agent_id)

            # Remove load counter
            load_key = f"{self.AGENT_LOAD_PREFIX}{agent_id}"
            pipeline.delete(load_key)

            pipeline.execute()

            logger.info(f"Deregistered agent {agent_id}")
            return True

        except RedisError as e:
            logger.error(f"Failed to deregister agent {agent_id}: {e}")
            raise

    def _calculate_capability_score(
        self,
        agent_capabilities: List[str],
        required_capabilities: List[str],
    ) -> tuple[float, List[str], List[str]]:
        """
        Calculate capability match score.

        Args:
            agent_capabilities: Agent's capabilities
            required_capabilities: Required capabilities

        Returns:
            Tuple of (score, matched_capabilities, missing_capabilities)
        """
        # Normalize to lowercase sets
        # fmt: off
        agent_caps_set = {
            cap.lower().strip() for cap in agent_capabilities
        }
        required_caps_set = {
            cap.lower().strip() for cap in required_capabilities
        }
        # fmt: on

        # Calculate matches
        matched = agent_caps_set.intersection(required_caps_set)
        missing = required_caps_set - agent_caps_set

        # Calculate score
        if not required_caps_set:
            score = 1.0  # No requirements = perfect match
        elif not matched:
            score = 0.0  # No matches = no score
        elif not missing:
            score = 1.0  # All requirements met = perfect match
        else:
            # Partial match: ratio of matched to required
            score = len(matched) / len(required_caps_set)

        return score, list(matched), list(missing)

    def find_best_agent(
        self,
        task_request: TaskRequest,
    ) -> Optional[AgentMatch]:
        """
        Find the best agent for a task request.

        Considers capability matching, load balancing, and agent priority.

        Args:
            task_request: Task delegation request

        Returns:
            Best matching agent or None if no suitable agent found

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            # Get candidate agents
            # fmt: off
            if task_request.required_agent_type:
                # Filter by specific agent type
                type_index = (
                    f"{self.AGENT_TYPE_INDEX}"
                    f"{task_request.required_agent_type}"
                )
                candidate_ids = self.redis_client.smembers(type_index)
            else:
                # Get all agents
                candidate_ids = self.redis_client.smembers(
                    self.AGENT_INDEX_KEY
                )
            # fmt: on

            if not candidate_ids:
                logger.warning("No agents available for task delegation")
                return None

            # Filter excluded agents
            exclude_set = set(task_request.exclude_agents)
            candidate_ids = {aid for aid in candidate_ids if aid not in exclude_set}

            if not candidate_ids:
                logger.warning("All available agents are excluded")
                return None

            # Score each candidate
            matches: List[AgentMatch] = []

            for agent_id in candidate_ids:
                agent_key = f"{self.AGENT_PREFIX}{agent_id}"
                agent_data = self.redis_client.get(agent_key)

                if not agent_data:
                    # Agent expired, remove from index
                    self.redis_client.srem(self.AGENT_INDEX_KEY, agent_id)
                    continue

                # Parse agent data
                agent = AgentCapability.model_validate_json(agent_data)

                # Skip unavailable agents
                if not agent.available:
                    continue

                # Get current load
                load_key = f"{self.AGENT_LOAD_PREFIX}{agent_id}"
                current_load = int(self.redis_client.get(load_key) or 0)

                # Skip agents at capacity
                if current_load >= agent.max_concurrent_tasks:
                    continue

                # Calculate capability score
                score, matched, missing = self._calculate_capability_score(
                    agent.capabilities,
                    task_request.required_capabilities,
                )

                # Skip agents with no matching capabilities
                if score == 0.0:
                    continue

                # Create match result
                match = AgentMatch(
                    agent_id=agent_id,
                    agent_type=agent.agent_type,
                    score=score,
                    matched_capabilities=matched,
                    missing_capabilities=missing,
                    current_load=current_load,
                    max_load=agent.max_concurrent_tasks,
                    available=agent.available,
                    priority_weight=agent.priority_weight,
                )

                matches.append(match)

            if not matches:
                logger.warning(
                    f"No suitable agent found for task {task_request.task_id}"
                )
                return None

            # Sort by effective score (descending)
            matches.sort(key=lambda m: m.effective_score, reverse=True)

            best_match = matches[0]

            logger.info(
                f"Selected agent {best_match.agent_id} for task "
                f"{task_request.task_id} "
                f"(score: {best_match.effective_score:.3f})"
            )

            return best_match

        except RedisError as e:
            logger.error(f"Failed to find best agent: {e}")
            raise

    def find_agent(
        self,
        required_capabilities: List[str],
        agent_type: Optional[str] = None,
        exclude_agents: Optional[List[str]] = None,
    ) -> Optional[AgentMatch]:
        """
        Find an agent with specific capabilities.

        Simplified version of find_best_agent for direct capability queries.

        Args:
            required_capabilities: Required capabilities
            agent_type: Optional specific agent type
            exclude_agents: Optional list of agent IDs to exclude

        Returns:
            Best matching agent or None if not found

        Raises:
            RedisError: If Redis operation fails
        """
        # Create a minimal task request
        task_request = TaskRequest(
            task_id="direct_query",
            task_type="capability_query",
            required_capabilities=required_capabilities,
            required_agent_type=agent_type,
            exclude_agents=exclude_agents or [],
        )

        return self.find_best_agent(task_request)

    def delegate_task(
        self,
        task_request: TaskRequest,
        agent_match: AgentMatch,
    ) -> Dict[str, Any]:
        """
        Delegate a task to a matched agent.

        Updates agent load and returns delegation details.

        Args:
            task_request: Task request to delegate
            agent_match: Matched agent to receive task

        Returns:
            Dictionary with delegation details

        Raises:
            ValueError: If agent has no capacity
            RedisError: If Redis operation fails
        """
        try:
            # Verify agent has capacity
            if not agent_match.has_capacity:
                raise ValueError(
                    f"Agent {agent_match.agent_id} has no capacity "
                    f"(load: {agent_match.current_load}/"
                    f"{agent_match.max_load})"
                )

            # Increment agent load
            load_key = f"{self.AGENT_LOAD_PREFIX}{agent_match.agent_id}"
            new_load = self.redis_client.incr(load_key)

            # Record delegation timestamp
            delegation_time = datetime.now(timezone.utc)

            delegation_result = {
                "task_id": task_request.task_id,
                "agent_id": agent_match.agent_id,
                "agent_type": agent_match.agent_type,
                "delegated_at": delegation_time.isoformat(),
                "match_score": agent_match.score,
                "effective_score": agent_match.effective_score,
                "agent_load": new_load,
                "max_load": agent_match.max_load,
                "matched_capabilities": agent_match.matched_capabilities,
                "missing_capabilities": agent_match.missing_capabilities,
                "estimated_duration": task_request.estimated_duration,
                "timeout": task_request.timeout,
                "priority": task_request.priority.value,
            }

            logger.info(
                f"Delegated task {task_request.task_id} to agent "
                f"{agent_match.agent_id} "
                f"(load: {new_load}/{agent_match.max_load})"
            )

            return delegation_result

        except ValueError as e:
            logger.error(f"Task delegation failed: {e}")
            raise

        except RedisError as e:
            logger.error(f"Failed to delegate task: {e}")
            raise

    def complete_task(
        self,
        agent_id: str,
        task_id: str,
    ) -> bool:
        """
        Mark a task as complete and decrement agent load.

        Args:
            agent_id: Agent identifier
            task_id: Task identifier

        Returns:
            True if successful

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            load_key = f"{self.AGENT_LOAD_PREFIX}{agent_id}"
            current_load = int(self.redis_client.get(load_key) or 0)

            if current_load > 0:
                new_load = self.redis_client.decr(load_key)
                logger.info(
                    f"Task {task_id} completed on agent {agent_id} "
                    f"(load: {new_load})"
                )
            else:
                logger.warning(
                    f"Agent {agent_id} load already at 0, " "cannot decrement"
                )

            return True

        except RedisError as e:
            logger.error(f"Failed to complete task: {e}")
            raise

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent status dictionary or None if not found

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            agent_key = f"{self.AGENT_PREFIX}{agent_id}"
            agent_data = self.redis_client.get(agent_key)

            if not agent_data:
                return None

            agent = AgentCapability.model_validate_json(agent_data)

            # Get current load
            load_key = f"{self.AGENT_LOAD_PREFIX}{agent_id}"
            current_load = int(self.redis_client.get(load_key) or 0)

            # Get TTL
            ttl = self.redis_client.ttl(agent_key)

            # fmt: off
            return {
                "agent_id": agent.agent_id,
                "agent_type": agent.agent_type,
                "capabilities": agent.capabilities,
                "available": agent.available,
                "current_load": current_load,
                "max_concurrent_tasks": agent.max_concurrent_tasks,
                "load_percentage": (
                    (current_load / agent.max_concurrent_tasks) * 100
                    if agent.max_concurrent_tasks > 0
                    else 0
                ),
                "has_capacity": (
                    agent.available
                    and current_load < agent.max_concurrent_tasks
                ),
                "priority_weight": agent.priority_weight,
                "resource_limits": agent.resource_limits.model_dump(),
                "ttl_seconds": ttl,
                "metadata": agent.metadata,
            }
            # fmt: on

        except RedisError as e:
            logger.error(f"Failed to get agent status: {e}")
            raise

    def set_agent_availability(
        self,
        agent_id: str,
        available: bool,
    ) -> bool:
        """
        Set agent availability status.

        Args:
            agent_id: Agent identifier
            available: Availability status

        Returns:
            True if successful, False if agent not found

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            agent_key = f"{self.AGENT_PREFIX}{agent_id}"
            agent_data = self.redis_client.get(agent_key)

            if not agent_data:
                logger.warning(f"Agent {agent_id} not found")
                return False

            agent = AgentCapability.model_validate_json(agent_data)
            agent.available = available

            # Update agent data preserving TTL
            ttl = self.redis_client.ttl(agent_key)
            self.redis_client.setex(
                agent_key,
                max(ttl, self.AGENT_TTL_SECONDS),
                agent.model_dump_json(),
            )

            logger.info(f"Set agent {agent_id} availability to {available}")
            return True

        except RedisError as e:
            logger.error(f"Failed to set agent availability: {e}")
            raise

    def set_agent_load(
        self,
        agent_id: str,
        active_tasks: int,
    ) -> bool:
        """
        Set agent load (active tasks count).

        Args:
            agent_id: Agent identifier
            active_tasks: Number of active tasks

        Returns:
            True if successful

        Raises:
            ValueError: If active_tasks is negative
            RedisError: If Redis operation fails
        """
        if active_tasks < 0:
            raise ValueError("Active tasks cannot be negative")

        try:
            load_key = f"{self.AGENT_LOAD_PREFIX}{agent_id}"
            self.redis_client.set(load_key, active_tasks)

            logger.debug(f"Set agent {agent_id} load to {active_tasks}")
            return True

        except RedisError as e:
            logger.error(f"Failed to set agent load: {e}")
            raise

    def heartbeat_agent(self, agent_id: str) -> bool:
        """
        Refresh agent TTL (heartbeat mechanism).

        Args:
            agent_id: Agent identifier

        Returns:
            True if successful, False if agent not found

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            agent_key = f"{self.AGENT_PREFIX}{agent_id}"

            # Extend TTL
            # fmt: off
            result = self.redis_client.expire(
                agent_key, self.AGENT_TTL_SECONDS
            )
            # fmt: on

            if result:
                logger.debug(f"Heartbeat received for agent {agent_id}")
            else:
                logger.warning(f"Agent {agent_id} not found for heartbeat")

            return bool(result)

        except RedisError as e:
            logger.error(f"Failed to heartbeat agent: {e}")
            raise

    def list_agents(
        self,
        filter_type: Optional[str] = None,
        available_only: bool = False,
        has_capacity: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List all registered agents with optional filters.

        Args:
            filter_type: Filter by agent type
            available_only: Only return available agents
            has_capacity: Only return agents with available capacity

        Returns:
            List of agent status dictionaries

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            # Get agent IDs
            if filter_type:
                type_index = f"{self.AGENT_TYPE_INDEX}{filter_type}"
                agent_ids = self.redis_client.smembers(type_index)
            else:
                agent_ids = self.redis_client.smembers(self.AGENT_INDEX_KEY)

            agents = []

            for agent_id in agent_ids:
                status = self.get_agent_status(agent_id)

                if not status:
                    # Agent expired, clean up
                    self.redis_client.srem(self.AGENT_INDEX_KEY, agent_id)
                    continue

                # Apply filters
                if available_only and not status["available"]:
                    continue

                if has_capacity and not status["has_capacity"]:
                    continue

                agents.append(status)

            # Sort by agent_id for consistent ordering
            agents.sort(key=lambda a: a["agent_id"])

            return agents

        except RedisError as e:
            logger.error(f"Failed to list agents: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get delegation manager statistics.

        Returns:
            Statistics dictionary

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            total_agents = self.redis_client.scard(self.AGENT_INDEX_KEY)
            agents = self.list_agents()

            # fmt: off
            available_agents = sum(
                1 for a in agents if a["available"]
            )
            agents_with_capacity = sum(
                1 for a in agents if a["has_capacity"]
            )
            total_load = sum(a["current_load"] for a in agents)
            max_capacity = sum(
                a["max_concurrent_tasks"] for a in agents
            )

            # Calculate average load percentage
            avg_load_pct = (
                sum(a["load_percentage"] for a in agents) / len(agents)
                if agents
                else 0.0
            )

            # Group by type
            agents_by_type: Dict[str, int] = {}
            for agent in agents:
                agent_type = agent["agent_type"]
                agents_by_type[agent_type] = (
                    agents_by_type.get(agent_type, 0) + 1
                )
            # fmt: on

            # fmt: off
            return {
                "total_agents": total_agents,
                "available_agents": available_agents,
                "agents_with_capacity": agents_with_capacity,
                "total_active_tasks": total_load,
                "max_capacity": max_capacity,
                "capacity_utilization": (
                    (total_load / max_capacity * 100)
                    if max_capacity > 0
                    else 0.0
                ),
                "average_load_percentage": avg_load_pct,
                "agents_by_type": agents_by_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            # fmt: on

        except RedisError as e:
            logger.error(f"Failed to get statistics: {e}")
            raise

    def cleanup_expired_agents(self) -> int:
        """
        Remove expired agents from indices.

        Returns:
            Number of agents cleaned up

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            agent_ids = self.redis_client.smembers(self.AGENT_INDEX_KEY)
            cleaned = 0

            for agent_id in agent_ids:
                agent_key = f"{self.AGENT_PREFIX}{agent_id}"

                if not self.redis_client.exists(agent_key):
                    # Agent expired, remove from indices
                    self.redis_client.srem(self.AGENT_INDEX_KEY, agent_id)

                    # Get all type indices and remove
                    type_indices = self.redis_client.keys(f"{self.AGENT_TYPE_INDEX}*")
                    for type_index in type_indices:
                        self.redis_client.srem(type_index, agent_id)

                    # Remove load counter
                    load_key = f"{self.AGENT_LOAD_PREFIX}{agent_id}"
                    self.redis_client.delete(load_key)

                    cleaned += 1
                    logger.info(f"Cleaned up expired agent {agent_id}")

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired agents")

            return cleaned

        except RedisError as e:
            logger.error(f"Failed to cleanup expired agents: {e}")
            raise

    def reset(self) -> bool:
        """
        Reset all delegation manager state (for testing/maintenance).

        WARNING: This removes all agent registrations and state.

        Returns:
            True if successful

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            # Get all agent IDs
            agent_ids = self.redis_client.smembers(self.AGENT_INDEX_KEY)

            # Delete all agent-related keys
            pipeline = self.redis_client.pipeline()

            for agent_id in agent_ids:
                agent_key = f"{self.AGENT_PREFIX}{agent_id}"
                load_key = f"{self.AGENT_LOAD_PREFIX}{agent_id}"
                pipeline.delete(agent_key)
                pipeline.delete(load_key)

            # Delete indices
            pipeline.delete(self.AGENT_INDEX_KEY)

            # Delete all type indices
            type_indices = self.redis_client.keys(f"{self.AGENT_TYPE_INDEX}*")
            for type_index in type_indices:
                pipeline.delete(type_index)

            # Delete all task queues
            task_queues = self.redis_client.keys(f"{self.TASK_QUEUE_PREFIX}*")
            for queue in task_queues:
                pipeline.delete(queue)

            pipeline.execute()

            logger.warning("Delegation manager state reset")
            return True

        except RedisError as e:
            logger.error(f"Failed to reset delegation manager: {e}")
            raise

    def close(self) -> None:
        """Close Redis connection."""
        try:
            self.redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
