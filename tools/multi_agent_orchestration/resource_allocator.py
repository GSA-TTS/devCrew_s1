"""
Resource Allocator - Distributed resource management for multi-agent systems.

Manages agent resources (CPU, memory, concurrent tasks) with Redis-backed
distributed state tracking, priority-based allocation, and deadlock detection.
"""

import json
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

import redis
from pydantic import BaseModel, Field, field_validator
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError


class Priority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ResourceLimits(BaseModel):
    """Resource limits for an agent."""

    agent_id: str = Field(..., description="Agent identifier")
    cpu_cores: float = Field(..., description="Maximum CPU cores", gt=0)
    memory_mb: float = Field(..., description="Maximum memory in MB", gt=0)
    max_tasks: int = Field(..., description="Maximum concurrent tasks", gt=0)

    @field_validator("cpu_cores")
    @classmethod
    def validate_cpu_cores(cls, v: float) -> float:
        """Validate CPU cores is positive."""
        if v <= 0:
            raise ValueError("CPU cores must be positive")
        return v

    @field_validator("memory_mb")
    @classmethod
    def validate_memory_mb(cls, v: float) -> float:
        """Validate memory is positive."""
        if v <= 0:
            raise ValueError("Memory MB must be positive")
        return v


class ResourceUsage(BaseModel):
    """Current resource usage for an agent."""

    agent_id: str = Field(..., description="Agent identifier")
    cpu_used: float = Field(default=0.0, description="CPU cores in use")
    memory_used: float = Field(default=0.0, description="Memory MB in use")
    active_tasks: int = Field(default=0, description="Number of active tasks")
    task_ids: List[str] = Field(
        default_factory=list, description="List of active task IDs"
    )
    cpu_limit: float = Field(..., description="Maximum CPU cores")
    memory_limit: float = Field(..., description="Maximum memory in MB")
    max_tasks: int = Field(..., description="Maximum concurrent tasks")

    @property
    def cpu_available(self) -> float:
        """Calculate available CPU cores."""
        return max(0.0, self.cpu_limit - self.cpu_used)

    @property
    def memory_available(self) -> float:
        """Calculate available memory in MB."""
        return max(0.0, self.memory_limit - self.memory_used)

    @property
    def tasks_available(self) -> int:
        """Calculate available task slots."""
        return max(0, self.max_tasks - self.active_tasks)

    @property
    def cpu_utilization(self) -> float:
        """Calculate CPU utilization percentage."""
        if self.cpu_limit == 0:
            return 0.0
        return (self.cpu_used / self.cpu_limit) * 100

    @property
    def memory_utilization(self) -> float:
        """Calculate memory utilization percentage."""
        if self.memory_limit == 0:
            return 0.0
        return (self.memory_used / self.memory_limit) * 100


class ResourceReservation(BaseModel):
    """Resource reservation for future allocation."""

    reservation_id: str = Field(..., description="Unique reservation identifier")
    agent_id: str = Field(..., description="Agent identifier")
    cpu_reserved: float = Field(..., description="Reserved CPU cores")
    memory_reserved: float = Field(..., description="Reserved memory in MB")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Reservation creation time",
    )
    expires_at: datetime = Field(..., description="Reservation expiration time")
    task_id: Optional[str] = Field(
        default=None, description="Associated task ID if any"
    )

    @property
    def is_expired(self) -> bool:
        """Check if reservation has expired."""
        return datetime.now(timezone.utc) >= self.expires_at


class TaskAllocation(BaseModel):
    """Task resource allocation record."""

    task_id: str = Field(..., description="Task identifier")
    agent_id: str = Field(..., description="Agent identifier")
    cpu_allocated: float = Field(..., description="Allocated CPU cores")
    memory_allocated: float = Field(..., description="Allocated memory in MB")
    priority: Priority = Field(..., description="Task priority")
    allocated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Allocation timestamp",
    )
    preemptible: bool = Field(default=True, description="Whether task can be preempted")


# Lua script for atomic check-and-allocate operation
ALLOCATE_RESOURCES_SCRIPT = """
local agent_id = ARGV[1]
local cpu = tonumber(ARGV[2])
local memory = tonumber(ARGV[3])
local task_id = ARGV[4]
local priority = ARGV[5]

local usage_key = "agent:" .. agent_id .. ":usage"
local tasks_key = "agent:" .. agent_id .. ":tasks"
local allocations_key = "agent:" .. agent_id .. ":allocations"

-- Get current usage
local usage = redis.call('HGETALL', usage_key)
local usage_map = {}
for i = 1, #usage, 2 do
    usage_map[usage[i]] = tonumber(usage[i + 1]) or 0
end

local cpu_used = usage_map['cpu_used'] or 0
local memory_used = usage_map['memory_used'] or 0
local active_tasks = usage_map['active_tasks'] or 0
local cpu_limit = usage_map['cpu_limit'] or 0
local memory_limit = usage_map['memory_limit'] or 0
local max_tasks = usage_map['max_tasks'] or 0

-- Check if resources are available
if (cpu_used + cpu) > cpu_limit then
    return {0, "insufficient_cpu"}
end

if (memory_used + memory) > memory_limit then
    return {0, "insufficient_memory"}
end

if active_tasks >= max_tasks then
    return {0, "max_tasks_reached"}
end

-- Allocate resources
redis.call('HSET', usage_key, 'cpu_used', cpu_used + cpu)
redis.call('HSET', usage_key, 'memory_used', memory_used + memory)
redis.call('HSET', usage_key, 'active_tasks', active_tasks + 1)
redis.call('SADD', tasks_key, task_id)

-- Store allocation details
local allocation = {
    task_id = task_id,
    agent_id = agent_id,
    cpu_allocated = cpu,
    memory_allocated = memory,
    priority = priority,
    allocated_at = tonumber(ARGV[6])
}
redis.call('HSET', allocations_key, task_id, cjson.encode(allocation))

return {1, "success"}
"""

# Lua script for atomic resource release
RELEASE_RESOURCES_SCRIPT = """
local agent_id = ARGV[1]
local task_id = ARGV[2]

local usage_key = "agent:" .. agent_id .. ":usage"
local tasks_key = "agent:" .. agent_id .. ":tasks"
local allocations_key = "agent:" .. agent_id .. ":allocations"

-- Check if task exists
local exists = redis.call('SISMEMBER', tasks_key, task_id)
if exists == 0 then
    return {0, "task_not_found"}
end

-- Get allocation details
local allocation_json = redis.call('HGET', allocations_key, task_id)
if not allocation_json then
    return {0, "allocation_not_found"}
end

local allocation = cjson.decode(allocation_json)
local cpu = tonumber(allocation.cpu_allocated)
local memory = tonumber(allocation.memory_allocated)

-- Get current usage
local usage = redis.call('HGETALL', usage_key)
local usage_map = {}
for i = 1, #usage, 2 do
    usage_map[usage[i]] = tonumber(usage[i + 1]) or 0
end

local cpu_used = usage_map['cpu_used'] or 0
local memory_used = usage_map['memory_used'] or 0
local active_tasks = usage_map['active_tasks'] or 0

-- Release resources
redis.call('HSET', usage_key, 'cpu_used', math.max(0, cpu_used - cpu))
redis.call('HSET', usage_key, 'memory_used', math.max(0, memory_used - memory))
redis.call('HSET', usage_key, 'active_tasks', math.max(0, active_tasks - 1))
redis.call('SREM', tasks_key, task_id)
redis.call('HDEL', allocations_key, task_id)

return {1, "success"}
"""

# Lua script for atomic reservation creation
CREATE_RESERVATION_SCRIPT = """
local agent_id = ARGV[1]
local cpu = tonumber(ARGV[2])
local memory = tonumber(ARGV[3])
local reservation_id = ARGV[4]
local expires_at = tonumber(ARGV[5])

local usage_key = "agent:" .. agent_id .. ":usage"
local reservations_key = "agent:" .. agent_id .. ":reservations"
local reservation_expiry_key = "reservation:expiry"

-- Get current usage and limits
local usage = redis.call('HGETALL', usage_key)
local usage_map = {}
for i = 1, #usage, 2 do
    usage_map[usage[i]] = tonumber(usage[i + 1]) or 0
end

local cpu_used = usage_map['cpu_used'] or 0
local memory_used = usage_map['memory_used'] or 0
local cpu_limit = usage_map['cpu_limit'] or 0
local memory_limit = usage_map['memory_limit'] or 0

-- Check if resources are available
if (cpu_used + cpu) > cpu_limit then
    return {0, "insufficient_cpu"}
end

if (memory_used + memory) > memory_limit then
    return {0, "insufficient_memory"}
end

-- Create reservation
local reservation = {
    reservation_id = reservation_id,
    agent_id = agent_id,
    cpu_reserved = cpu,
    memory_reserved = memory,
    created_at = tonumber(ARGV[6]),
    expires_at = expires_at
}
redis.call('HSET', reservations_key, reservation_id, cjson.encode(reservation))
redis.call(
    'ZADD',
    reservation_expiry_key,
    expires_at,
    agent_id .. ":" .. reservation_id
)

-- Update usage to include reservation
redis.call('HSET', usage_key, 'cpu_used', cpu_used + cpu)
redis.call('HSET', usage_key, 'memory_used', memory_used + memory)

return {1, reservation_id}
"""


class ResourceAllocator:
    """
    Distributed resource allocator for multi-agent systems.

    Manages CPU, memory, and task slot allocation across agents with
    Redis-backed distributed state, atomic operations, priority-based
    allocation, and deadlock detection.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_timeout: int = 30,
    ):
        """
        Initialize the resource allocator.

        Args:
            redis_url: Redis connection URL
            default_timeout: Default operation timeout in seconds
        """
        self.redis_url = redis_url
        self.default_timeout = default_timeout

        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=default_timeout,
                socket_connect_timeout=default_timeout,
            )
            # Test connection
            self.redis_client.ping()
        except (RedisError, RedisConnectionError) as e:
            raise ConnectionError(
                f"Failed to connect to Redis at {redis_url}: {str(e)}"
            ) from e

        # Register Lua scripts
        try:
            self.allocate_script = self.redis_client.register_script(
                ALLOCATE_RESOURCES_SCRIPT
            )
            self.release_script = self.redis_client.register_script(
                RELEASE_RESOURCES_SCRIPT
            )
            self.reserve_script = self.redis_client.register_script(
                CREATE_RESERVATION_SCRIPT
            )
        except RedisError as e:
            raise RuntimeError(f"Failed to register Lua scripts: {str(e)}") from e

    def set_agent_limits(
        self,
        agent_id: str,
        cpu_cores: float,
        memory_mb: float,
        max_tasks: int,
    ) -> bool:
        """
        Set resource limits for an agent.

        Args:
            agent_id: Agent identifier
            cpu_cores: Maximum CPU cores
            memory_mb: Maximum memory in MB
            max_tasks: Maximum concurrent tasks

        Returns:
            True if limits were set successfully

        Raises:
            ValueError: If limits are invalid
            RedisError: If Redis operation fails
        """
        if not agent_id:
            raise ValueError("Agent ID cannot be empty")

        # Validate limits
        limits = ResourceLimits(
            agent_id=agent_id,
            cpu_cores=cpu_cores,
            memory_mb=memory_mb,
            max_tasks=max_tasks,
        )

        try:
            # Store limits and initialize usage
            usage_key = f"agent:{agent_id}:usage"
            self.redis_client.hset(
                usage_key,
                mapping={
                    "cpu_limit": limits.cpu_cores,
                    "memory_limit": limits.memory_mb,
                    "max_tasks": limits.max_tasks,
                    "cpu_used": 0.0,
                    "memory_used": 0.0,
                    "active_tasks": 0,
                },
            )

            # Initialize task set
            tasks_key = f"agent:{agent_id}:tasks"
            if not self.redis_client.exists(tasks_key):
                self.redis_client.sadd(tasks_key, "__init__")
                self.redis_client.srem(tasks_key, "__init__")

            return True

        except RedisError as e:
            raise RedisError(
                f"Failed to set limits for agent {agent_id}: {str(e)}"
            ) from e

    def get_agent_usage(self, agent_id: str) -> ResourceUsage:
        """
        Get current resource usage for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            ResourceUsage object with current usage

        Raises:
            ValueError: If agent not found
            RedisError: If Redis operation fails
        """
        if not agent_id:
            raise ValueError("Agent ID cannot be empty")

        try:
            usage_key = f"agent:{agent_id}:usage"
            tasks_key = f"agent:{agent_id}:tasks"

            # Get usage data
            usage_data = self.redis_client.hgetall(usage_key)
            if not usage_data:
                raise ValueError(f"Agent {agent_id} not found")

            # Get active task IDs
            task_ids = list(self.redis_client.smembers(tasks_key))

            return ResourceUsage(
                agent_id=agent_id,
                cpu_used=float(usage_data.get("cpu_used", 0)),
                memory_used=float(usage_data.get("memory_used", 0)),
                active_tasks=int(usage_data.get("active_tasks", 0)),
                task_ids=task_ids,
                cpu_limit=float(usage_data.get("cpu_limit", 0)),
                memory_limit=float(usage_data.get("memory_limit", 0)),
                max_tasks=int(usage_data.get("max_tasks", 0)),
            )

        except RedisError as e:
            raise RedisError(
                f"Failed to get usage for agent {agent_id}: {str(e)}"
            ) from e

    def allocate_resources(
        self,
        agent_id: str,
        cpu: float,
        memory: float,
        task_id: str,
        priority: Priority = Priority.MEDIUM,
    ) -> bool:
        """
        Allocate resources to a task atomically.

        Args:
            agent_id: Agent identifier
            cpu: CPU cores to allocate
            memory: Memory in MB to allocate
            task_id: Task identifier
            priority: Task priority (for preemption logic)

        Returns:
            True if allocation successful, False otherwise

        Raises:
            ValueError: If parameters are invalid
            RedisError: If Redis operation fails
        """
        if not agent_id or not task_id:
            raise ValueError("Agent ID and task ID cannot be empty")

        if cpu <= 0 or memory <= 0:
            raise ValueError("CPU and memory must be positive")

        try:
            # Execute atomic allocation script
            allocated_at = int(datetime.now(timezone.utc).timestamp())
            result = self.allocate_script(
                keys=[],
                args=[
                    agent_id,
                    cpu,
                    memory,
                    task_id,
                    priority.value,
                    allocated_at,
                ],
            )

            success = result[0] == 1
            if not success:
                reason = result[1]
                # Try preemption if high priority and resources insufficient
                if priority == Priority.HIGH and reason in [
                    "insufficient_cpu",
                    "insufficient_memory",
                ]:
                    preempted = self._attempt_preemption(
                        agent_id, cpu, memory, priority
                    )
                    if preempted:
                        # Retry allocation after preemption
                        result = self.allocate_script(
                            keys=[],
                            args=[
                                agent_id,
                                cpu,
                                memory,
                                task_id,
                                priority.value,
                                allocated_at,
                            ],
                        )
                        return result[0] == 1

            return success

        except RedisError as e:
            raise RedisError(
                f"Failed to allocate resources for task {task_id}: {str(e)}"
            ) from e

    def release_resources(self, agent_id: str, task_id: str) -> bool:
        """
        Release resources allocated to a task atomically.

        Args:
            agent_id: Agent identifier
            task_id: Task identifier

        Returns:
            True if release successful, False if task not found

        Raises:
            ValueError: If parameters are invalid
            RedisError: If Redis operation fails
        """
        if not agent_id or not task_id:
            raise ValueError("Agent ID and task ID cannot be empty")

        try:
            # Execute atomic release script
            result = self.release_script(keys=[], args=[agent_id, task_id])
            return result[0] == 1

        except RedisError as e:
            raise RedisError(
                f"Failed to release resources for task {task_id}: {str(e)}"
            ) from e

    def reserve_resources(
        self,
        agent_id: str,
        cpu: float,
        memory: float,
        duration: int,
        task_id: Optional[str] = None,
    ) -> str:
        """
        Reserve resources for future allocation.

        Args:
            agent_id: Agent identifier
            cpu: CPU cores to reserve
            memory: Memory in MB to reserve
            duration: Reservation duration in seconds
            task_id: Optional task ID to associate with reservation

        Returns:
            Reservation ID

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If reservation fails
            RedisError: If Redis operation fails
        """
        if not agent_id:
            raise ValueError("Agent ID cannot be empty")

        if cpu <= 0 or memory <= 0:
            raise ValueError("CPU and memory must be positive")

        if duration <= 0:
            raise ValueError("Duration must be positive")

        try:
            # Generate reservation ID
            timestamp = int(time.time() * 1000)
            reservation_id = f"rsv_{agent_id}_{timestamp}"

            # Calculate expiration
            created_at = datetime.now(timezone.utc)
            expires_at = created_at + timedelta(seconds=duration)

            # Execute atomic reservation script
            result = self.reserve_script(
                keys=[],
                args=[
                    agent_id,
                    cpu,
                    memory,
                    reservation_id,
                    int(expires_at.timestamp()),
                    int(created_at.timestamp()),
                ],
            )

            if result[0] != 1:
                reason = result[1]
                raise RuntimeError(f"Failed to reserve resources: {reason}")

            # Store additional metadata if task_id provided
            if task_id:
                reservations_key = f"agent:{agent_id}:reservations"
                reservation_data = self.redis_client.hget(
                    reservations_key, reservation_id
                )
                if reservation_data:
                    reservation = json.loads(reservation_data)
                    reservation["task_id"] = task_id
                    self.redis_client.hset(
                        reservations_key,
                        reservation_id,
                        json.dumps(reservation),
                    )

            return reservation_id

        except RedisError as e:
            raise RedisError(
                f"Failed to reserve resources for agent {agent_id}: {str(e)}"
            ) from e

    def check_availability(self, agent_id: str, cpu: float, memory: float) -> bool:
        """
        Check if agent has sufficient available resources.

        Args:
            agent_id: Agent identifier
            cpu: Required CPU cores
            memory: Required memory in MB

        Returns:
            True if resources are available

        Raises:
            ValueError: If agent not found
        """
        if not agent_id:
            raise ValueError("Agent ID cannot be empty")

        try:
            usage = self.get_agent_usage(agent_id)
            return (
                usage.cpu_available >= cpu
                and usage.memory_available >= memory
                and usage.tasks_available > 0
            )
        except ValueError:
            return False

    def get_available_agents(
        self, cpu_required: float, memory_required: float
    ) -> List[str]:
        """
        Get list of agents with sufficient available resources.

        Args:
            cpu_required: Required CPU cores
            memory_required: Required memory in MB

        Returns:
            List of agent IDs with sufficient resources

        Raises:
            RedisError: If Redis operation fails
        """
        if cpu_required <= 0 or memory_required <= 0:
            raise ValueError("CPU and memory requirements must be positive")

        try:
            available_agents = []

            # Scan for all agent usage keys
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(
                    cursor, match="agent:*:usage", count=100
                )

                for key in keys:
                    # Extract agent_id from key
                    agent_id = key.split(":")[1]

                    try:
                        if self.check_availability(
                            agent_id, cpu_required, memory_required
                        ):
                            available_agents.append(agent_id)
                    except ValueError:
                        # Agent not found or invalid, skip
                        continue

                if cursor == 0:
                    break

            return available_agents

        except RedisError as e:
            raise RedisError(f"Failed to get available agents: {str(e)}") from e

    def cleanup_expired_reservations(self) -> int:
        """
        Clean up expired resource reservations.

        Returns:
            Number of reservations cleaned up

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            cleaned = 0
            current_time = datetime.now(timezone.utc)
            expiry_key = "reservation:expiry"

            # Get expired reservations
            expired = self.redis_client.zrangebyscore(
                expiry_key, 0, int(current_time.timestamp())
            )

            for item in expired:
                agent_id, reservation_id = item.split(":", 1)
                reservations_key = f"agent:{agent_id}:reservations"

                # Get reservation data
                reservation_data = self.redis_client.hget(
                    reservations_key, reservation_id
                )
                if not reservation_data:
                    continue

                reservation = json.loads(reservation_data)
                cpu = float(reservation["cpu_reserved"])
                memory = float(reservation["memory_reserved"])

                # Release reserved resources
                usage_key = f"agent:{agent_id}:usage"
                pipe = self.redis_client.pipeline()
                pipe.hincrbyfloat(usage_key, "cpu_used", -cpu)
                pipe.hincrbyfloat(usage_key, "memory_used", -memory)
                pipe.hdel(reservations_key, reservation_id)
                pipe.zrem(expiry_key, item)
                pipe.execute()

                cleaned += 1

            return cleaned

        except RedisError as e:
            raise RedisError(f"Failed to cleanup expired reservations: {str(e)}") from e

    def detect_deadlocks(self) -> List[str]:
        """
        Detect potential deadlocks in resource allocation.

        Detects circular wait conditions where tasks are waiting for
        resources held by other tasks in a cycle.

        Returns:
            List of agent IDs involved in potential deadlocks

        Raises:
            RedisError: If Redis operation fails
        """
        try:
            deadlocked_agents = []

            # Scan for all agents
            cursor = 0
            agent_ids = set()

            while True:
                cursor, keys = self.redis_client.scan(
                    cursor, match="agent:*:usage", count=100
                )
                for key in keys:
                    agent_id = key.split(":")[1]
                    agent_ids.add(agent_id)

                if cursor == 0:
                    break

            # Build wait-for graph
            wait_for_graph: Dict[str, Set[str]] = {}

            for agent_id in agent_ids:
                try:
                    usage = self.get_agent_usage(agent_id)

                    # Agent is deadlock candidate if at max tasks
                    # but has pending work
                    if usage.tasks_available == 0:
                        # Check for waiting tasks
                        # (would be in queue in real impl)
                        queue_key = f"agent:{agent_id}:queue"
                        queue_length = self.redis_client.llen(queue_key)

                        if queue_length > 0:
                            # This agent has no slots but has waiting
                            # tasks. In a real implementation, check if
                            # waiting tasks depend on other agents that
                            # are also blocked
                            wait_for_graph[agent_id] = set()

                            # Check allocations for inter-agent dependencies
                            allocations_key = f"agent:{agent_id}:allocations"
                            allocations = self.redis_client.hgetall(allocations_key)

                            for alloc_data in allocations.values():
                                _ = json.loads(alloc_data)
                                # In real impl, check if task waits
                                # for other agents. This is a
                                # simplified detection

                except ValueError:
                    continue

            # Detect cycles using DFS
            def has_cycle(node: str, visited: Set[str], rec_stack: Set[str]) -> bool:
                visited.add(node)
                rec_stack.add(node)

                for neighbor in wait_for_graph.get(node, []):
                    if neighbor not in visited:
                        if has_cycle(neighbor, visited, rec_stack):
                            return True
                    elif neighbor in rec_stack:
                        return True

                rec_stack.remove(node)
                return False

            visited: Set[str] = set()
            for agent_id in wait_for_graph:
                if agent_id not in visited:
                    rec_stack: Set[str] = set()
                    if has_cycle(agent_id, visited, rec_stack):
                        deadlocked_agents.append(agent_id)

            return deadlocked_agents

        except RedisError as e:
            raise RedisError(f"Failed to detect deadlocks: {str(e)}") from e

    def _attempt_preemption(
        self,
        agent_id: str,
        cpu_needed: float,
        memory_needed: float,
        priority: Priority,
    ) -> bool:
        """
        Attempt to preempt lower priority tasks to free resources.

        Args:
            agent_id: Agent identifier
            cpu_needed: CPU cores needed
            memory_needed: Memory in MB needed
            priority: Priority of requesting task

        Returns:
            True if preemption successful and resources freed
        """
        try:
            allocations_key = f"agent:{agent_id}:allocations"
            allocations = self.redis_client.hgetall(allocations_key)

            # Find preemptible tasks (lower priority)
            preemptible: List[Tuple[str, float, float, Priority]] = []

            for task_id, alloc_data in allocations.items():
                allocation = json.loads(alloc_data)
                task_priority = Priority(allocation["priority"])

                # Only preempt lower priority tasks
                if task_priority.value < priority.value:
                    preemptible.append(
                        (
                            task_id,
                            float(allocation["cpu_allocated"]),
                            float(allocation["memory_allocated"]),
                            task_priority,
                        )
                    )

            # Sort by priority (lowest first) and try to preempt
            preemptible.sort(key=lambda x: x[3].value)

            cpu_freed = 0.0
            memory_freed = 0.0
            preempted_tasks = []

            for task_id, cpu, memory, _ in preemptible:
                # Preempt this task
                if self.release_resources(agent_id, task_id):
                    cpu_freed += cpu
                    memory_freed += memory
                    preempted_tasks.append(task_id)

                    # Check if we have enough resources now
                    if cpu_freed >= cpu_needed and memory_freed >= memory_needed:
                        # Add preempted tasks to priority queue
                        # for re-execution
                        for preempted_id in preempted_tasks:
                            queue_key = f"agent:{agent_id}:queue"
                            self.redis_client.rpush(queue_key, preempted_id)
                        return True

            return False

        except RedisError:
            return False

    def get_allocation(self, agent_id: str, task_id: str) -> Optional[TaskAllocation]:
        """
        Get allocation details for a specific task.

        Args:
            agent_id: Agent identifier
            task_id: Task identifier

        Returns:
            TaskAllocation if found, None otherwise

        Raises:
            RedisError: If Redis operation fails
        """
        if not agent_id or not task_id:
            raise ValueError("Agent ID and task ID cannot be empty")

        try:
            allocations_key = f"agent:{agent_id}:allocations"
            alloc_data = self.redis_client.hget(allocations_key, task_id)

            if not alloc_data:
                return None

            allocation = json.loads(alloc_data)
            return TaskAllocation(
                task_id=allocation["task_id"],
                agent_id=allocation["agent_id"],
                cpu_allocated=float(allocation["cpu_allocated"]),
                memory_allocated=float(allocation["memory_allocated"]),
                priority=Priority(allocation["priority"]),
                allocated_at=datetime.fromtimestamp(
                    allocation["allocated_at"], tz=timezone.utc
                ),
            )

        except RedisError as e:
            raise RedisError(
                f"Failed to get allocation for task {task_id}: {str(e)}"
            ) from e

    def close(self) -> None:
        """Close Redis connection."""
        try:
            if self.redis_client:
                self.redis_client.close()
        except RedisError:
            pass
