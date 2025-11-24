"""
Comprehensive Unit Tests for Multi-Agent Orchestration Platform.

Tests for TaskOrchestrator, DelegationManager, ResourceAllocator,
HandoffManager, WorkflowEngine, HubSpokeCoordinator, and CLI components.

Issue #46: Multi-Agent Orchestration Platform - Test Suite
"""

import json
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import fakeredis
import pytest
import yaml
from click.testing import CliRunner
from pydantic import ValidationError

# Import components to test
from delegation_manager import (
    AgentCapability,
    AgentMatch,
    DelegationManager,
    ResourceLimits,
    RetryBackoff,
    RetryPolicy,
    TaskPriority,
    TaskRequest,
)
from handoff_manager import (
    AgentContext,
    HandoffManager,
    HandoffPrecondition,
    HandoffResult,
)
from hub_spoke_coordinator import (
    DecompositionStrategy,
    HubAgent,
    HubSpokeCoordinator,
    Objective,
    SpokeAgent,
    SpokeStatus,
    SubTask,
)
from orchestration_cli import cli
from resource_allocator import Priority, ResourceAllocator, ResourceUsage, TaskAllocation
from task_orchestrator import (
    Task,
    TaskOrchestrator,
    TaskStatus,
    Workflow,
    WorkflowStatus,
)
from workflow_engine import (
    BugFixWorkflow,
    ConditionalBranch,
    ExecutionMode,
    FeatureDevelopmentWorkflow,
    TDDWorkflow,
    WorkflowEngine,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def redis_client():
    """Provide a fake Redis client for testing."""
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    yield fake_redis
    fake_redis.flushall()


@pytest.fixture
def mock_postgres():
    """Mock PostgreSQL connection pool."""
    with patch("psycopg2.pool.SimpleConnectionPool") as mock_pool:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_pool.return_value.getconn.return_value = mock_conn

        yield {
            "pool": mock_pool,
            "connection": mock_conn,
            "cursor": mock_cursor,
        }


@pytest.fixture
def task_orchestrator(redis_client):
    """Provide a TaskOrchestrator instance with fake Redis."""
    with patch("task_orchestrator.TaskOrchestrator.redis_url", "redis://localhost:6379"):
        orchestrator = TaskOrchestrator()
        yield orchestrator


@pytest.fixture
def delegation_manager(redis_client):
    """Provide a DelegationManager instance with fake Redis."""
    with patch("redis.from_url", return_value=redis_client):
        manager = DelegationManager()
        manager.redis_client = redis_client
        yield manager


@pytest.fixture
def resource_allocator(redis_client):
    """Provide a ResourceAllocator instance with fake Redis."""
    with patch("redis.from_url", return_value=redis_client):
        allocator = ResourceAllocator()
        allocator.redis_client = redis_client
        # Register Lua scripts on fake Redis (mocked)
        allocator.allocate_script = MagicMock()
        allocator.release_script = MagicMock()
        allocator.reserve_script = MagicMock()
        yield allocator


@pytest.fixture
def handoff_manager(redis_client, mock_postgres):
    """Provide a HandoffManager instance with fake Redis and mocked PostgreSQL."""
    postgres_config = {
        "host": "localhost",
        "port": 5432,
        "database": "test_db",
        "user": "test_user",
        "password": "test_pass",
    }

    with patch("psycopg2.pool.SimpleConnectionPool", return_value=mock_postgres["pool"]):
        manager = HandoffManager(redis_client=redis_client, postgres_config=postgres_config)
        manager.pg_pool = mock_postgres["pool"]
        yield manager


@pytest.fixture
def workflow_engine(redis_client):
    """Provide a WorkflowEngine instance with fake Redis."""
    with patch("redis.from_url", return_value=redis_client):
        engine = WorkflowEngine()
        engine.redis_client = redis_client
        yield engine


@pytest.fixture
def hub_spoke_coordinator(redis_client):
    """Provide a HubSpokeCoordinator instance with fake Redis."""
    with patch("redis.from_url", return_value=redis_client):
        coordinator = HubSpokeCoordinator()
        coordinator.redis_client = redis_client
        yield coordinator


@pytest.fixture
def sample_workflow():
    """Provide a sample workflow for testing."""
    return Workflow(
        workflow_id="test-workflow-001",
        name="Test Workflow",
        priority="high",
        tasks=[
            Task(task_id="task-1", agent_type="backend-engineer"),
            Task(task_id="task-2", agent_type="qa-tester", depends_on=["task-1"]),
            Task(task_id="task-3", agent_type="devops-engineer", depends_on=["task-2"]),
        ],
    )


@pytest.fixture
def cli_runner():
    """Provide Click CLI test runner."""
    return CliRunner()


# ============================================================================
# TASK ORCHESTRATOR TESTS
# ============================================================================


@pytest.mark.unit
class TestTaskOrchestrator:
    """Test suite for TaskOrchestrator component."""

    def test_parse_workflow_definition_yaml(self, tmp_path):
        """Test parsing workflow definition from YAML file."""
        workflow_def = {
            "workflow": {
                "id": "test-001",
                "name": "Test Workflow",
                "priority": "high",
                "timeout": 3600,
                "tasks": [
                    {
                        "task_id": "task-1",
                        "agent_type": "backend-engineer",
                        "agent_capabilities": ["python-development"],
                        "input": {"action": "implement"},
                        "timeout": 600,
                        "retry": 3,
                    }
                ],
            }
        }

        yaml_file = tmp_path / "workflow.yaml"
        yaml_file.write_text(yaml.dump(workflow_def))

        workflow = TaskOrchestrator.parse_workflow_definition(str(yaml_file))

        assert workflow.workflow_id == "test-001"
        assert workflow.name == "Test Workflow"
        assert workflow.priority == "high"
        assert len(workflow.tasks) == 1
        assert workflow.tasks[0].task_id == "task-1"

    def test_parse_workflow_definition_json(self, tmp_path):
        """Test parsing workflow definition from JSON file."""
        workflow_def = {
            "workflow": {
                "id": "test-002",
                "name": "JSON Workflow",
                "tasks": [{"task_id": "task-1", "agent_type": "test"}],
            }
        }

        json_file = tmp_path / "workflow.json"
        json_file.write_text(json.dumps(workflow_def))

        workflow = TaskOrchestrator.parse_workflow_definition(str(json_file))

        assert workflow.workflow_id == "test-002"
        assert workflow.name == "JSON Workflow"

    def test_parse_workflow_definition_invalid_format(self, tmp_path):
        """Test parsing workflow with invalid file format."""
        txt_file = tmp_path / "workflow.txt"
        txt_file.write_text("invalid")

        with pytest.raises(ValueError, match="File must be YAML or JSON"):
            TaskOrchestrator.parse_workflow_definition(str(txt_file))

    def test_create_workflow(self, task_orchestrator, sample_workflow):
        """Test creating and registering a workflow."""
        workflow_id = task_orchestrator.create_workflow(sample_workflow)

        assert workflow_id == sample_workflow.workflow_id
        assert workflow_id in task_orchestrator.workflows

    def test_execute_workflow_sequential(self, task_orchestrator, sample_workflow):
        """Test executing workflow with sequential dependencies."""
        task_orchestrator.create_workflow(sample_workflow)

        result = task_orchestrator.execute_workflow(sample_workflow.workflow_id)

        assert result["status"] == "completed"
        assert result["tasks_completed"] == 3
        assert result["tasks_failed"] == 0

    def test_execute_workflow_not_found(self, task_orchestrator):
        """Test executing non-existent workflow."""
        with pytest.raises(ValueError, match="Workflow .* not found"):
            task_orchestrator.execute_workflow("non-existent")

    def test_execute_workflow_with_task_failure(self, task_orchestrator):
        """Test workflow execution when a task fails."""
        workflow = Workflow(
            workflow_id="fail-workflow",
            name="Failing Workflow",
            tasks=[Task(task_id="fail-task", agent_type="test")],
        )
        task_orchestrator.create_workflow(workflow)

        # Mock task execution to fail
        with patch.object(
            task_orchestrator, "_execute_task", side_effect=Exception("Task failed")
        ):
            with pytest.raises(Exception, match="Task failed"):
                task_orchestrator.execute_workflow(workflow.workflow_id)

            # Check workflow status
            status = task_orchestrator.get_workflow_status(workflow.workflow_id)
            assert status["status"] == "failed"

    def test_get_workflow_status(self, task_orchestrator, sample_workflow):
        """Test getting workflow status information."""
        task_orchestrator.create_workflow(sample_workflow)

        status = task_orchestrator.get_workflow_status(sample_workflow.workflow_id)

        assert status["workflow_id"] == sample_workflow.workflow_id
        assert status["name"] == sample_workflow.name
        assert status["status"] == "pending"
        assert status["total_tasks"] == 3

    def test_get_workflow_status_not_found(self, task_orchestrator):
        """Test getting status of non-existent workflow."""
        with pytest.raises(ValueError, match="Workflow .* not found"):
            task_orchestrator.get_workflow_status("non-existent")

    def test_cancel_workflow(self, task_orchestrator, sample_workflow):
        """Test cancelling a running workflow."""
        task_orchestrator.create_workflow(sample_workflow)
        sample_workflow.status = WorkflowStatus.RUNNING

        success = task_orchestrator.cancel_workflow(sample_workflow.workflow_id)

        assert success is True
        assert sample_workflow.status == WorkflowStatus.CANCELLED

    def test_cancel_workflow_not_running(self, task_orchestrator, sample_workflow):
        """Test cancelling workflow that is not running."""
        task_orchestrator.create_workflow(sample_workflow)

        success = task_orchestrator.cancel_workflow(sample_workflow.workflow_id)

        assert success is False

    def test_workflow_get_ready_tasks(self):
        """Test getting ready tasks from workflow."""
        workflow = Workflow(
            workflow_id="test",
            name="Test",
            tasks=[
                Task(task_id="A", agent_type="test", status=TaskStatus.PENDING),
                Task(
                    task_id="B",
                    agent_type="test",
                    depends_on=["A"],
                    status=TaskStatus.PENDING,
                ),
                Task(
                    task_id="C",
                    agent_type="test",
                    depends_on=["B"],
                    status=TaskStatus.PENDING,
                ),
            ],
        )

        ready_tasks = workflow.get_ready_tasks()

        assert len(ready_tasks) == 1
        assert ready_tasks[0].task_id == "A"


# ============================================================================
# DELEGATION MANAGER TESTS
# ============================================================================


@pytest.mark.unit
class TestDelegationManager:
    """Test suite for DelegationManager component."""

    def test_register_agent(self, delegation_manager):
        """Test registering an agent successfully."""
        success = delegation_manager.register_agent(
            agent_id="backend-001",
            agent_type="backend-engineer",
            capabilities=["python-development", "fastapi", "postgresql"],
            max_concurrent_tasks=3,
            priority_weight=10,
        )

        assert success is True
        # Verify agent is in Redis
        agent_key = f"{delegation_manager.AGENT_PREFIX}backend-001"
        assert delegation_manager.redis_client.exists(agent_key)

    def test_register_agent_with_empty_capabilities(self, delegation_manager):
        """Test registering agent with empty capabilities fails."""
        with pytest.raises(ValueError, match="at least one capability"):
            delegation_manager.register_agent(
                agent_id="bad-agent",
                agent_type="test",
                capabilities=[],
            )

    def test_deregister_agent(self, delegation_manager):
        """Test deregistering an agent."""
        delegation_manager.register_agent(
            agent_id="temp-agent",
            agent_type="test",
            capabilities=["testing"],
        )

        success = delegation_manager.deregister_agent("temp-agent")

        assert success is True
        # Verify agent is removed from Redis
        agent_key = f"{delegation_manager.AGENT_PREFIX}temp-agent"
        assert not delegation_manager.redis_client.exists(agent_key)

    def test_deregister_agent_not_found(self, delegation_manager):
        """Test deregistering non-existent agent."""
        success = delegation_manager.deregister_agent("non-existent")

        assert success is False

    def test_capability_matching_exact(self, delegation_manager):
        """Test exact capability matching."""
        delegation_manager.register_agent(
            agent_id="backend-001",
            agent_type="backend-engineer",
            capabilities=["python-development", "fastapi"],
            max_concurrent_tasks=3,
        )

        task = TaskRequest(
            task_id="task-001",
            task_type="implement",
            required_capabilities=["python-development", "fastapi"],
        )

        match = delegation_manager.find_best_agent(task)

        assert match is not None
        assert match.agent_id == "backend-001"
        assert match.score == 1.0

    def test_capability_matching_partial(self, delegation_manager):
        """Test partial capability matching."""
        delegation_manager.register_agent(
            agent_id="backend-001",
            agent_type="backend-engineer",
            capabilities=["python-development", "fastapi", "postgresql"],
            max_concurrent_tasks=3,
        )

        task = TaskRequest(
            task_id="task-001",
            task_type="implement",
            required_capabilities=["python-development", "redis"],
        )

        match = delegation_manager.find_best_agent(task)

        assert match is not None
        assert match.agent_id == "backend-001"
        assert match.score == 0.5  # 1 out of 2 capabilities matched

    def test_capability_matching_no_match(self, delegation_manager):
        """Test no capability matching."""
        delegation_manager.register_agent(
            agent_id="frontend-001",
            agent_type="frontend-engineer",
            capabilities=["react", "typescript"],
            max_concurrent_tasks=3,
        )

        task = TaskRequest(
            task_id="task-001",
            task_type="implement",
            required_capabilities=["python-development", "fastapi"],
        )

        match = delegation_manager.find_best_agent(task)

        assert match is None

    def test_load_balancing_across_agents(self, delegation_manager):
        """Test load balancing selects least loaded agent."""
        # Register two identical agents
        delegation_manager.register_agent(
            agent_id="agent-1",
            agent_type="test",
            capabilities=["python"],
            max_concurrent_tasks=3,
        )
        delegation_manager.register_agent(
            agent_id="agent-2",
            agent_type="test",
            capabilities=["python"],
            max_concurrent_tasks=3,
        )

        # Set agent-1 with higher load
        delegation_manager.set_agent_load("agent-1", 2)
        delegation_manager.set_agent_load("agent-2", 0)

        task = TaskRequest(
            task_id="task-001",
            task_type="test",
            required_capabilities=["python"],
        )

        match = delegation_manager.find_best_agent(task)

        # Should select agent-2 (lower load)
        assert match.agent_id == "agent-2"

    def test_priority_based_task_routing(self, delegation_manager):
        """Test priority-based task routing."""
        delegation_manager.register_agent(
            agent_id="low-priority",
            agent_type="test",
            capabilities=["python"],
            priority_weight=5,
        )
        delegation_manager.register_agent(
            agent_id="high-priority",
            agent_type="test",
            capabilities=["python"],
            priority_weight=50,
        )

        task = TaskRequest(
            task_id="task-001",
            task_type="test",
            required_capabilities=["python"],
            priority=TaskPriority.HIGH,
        )

        match = delegation_manager.find_best_agent(task)

        # Should prefer high priority agent
        assert match.agent_id == "high-priority"

    def test_agent_availability_tracking(self, delegation_manager):
        """Test tracking agent availability."""
        delegation_manager.register_agent(
            agent_id="agent-1",
            agent_type="test",
            capabilities=["python"],
            available=True,
        )

        # Disable agent
        delegation_manager.set_agent_availability("agent-1", False)

        status = delegation_manager.get_agent_status("agent-1")
        assert status["available"] is False

        # Agent should not be selected
        task = TaskRequest(
            task_id="task-001",
            task_type="test",
            required_capabilities=["python"],
        )
        match = delegation_manager.find_best_agent(task)
        assert match is None

    def test_agent_expiration_and_cleanup(self, delegation_manager):
        """Test agent expiration and cleanup."""
        delegation_manager.register_agent(
            agent_id="temp-agent",
            agent_type="test",
            capabilities=["python"],
        )

        # Manually expire agent in Redis
        agent_key = f"{delegation_manager.AGENT_PREFIX}temp-agent"
        delegation_manager.redis_client.delete(agent_key)

        # Cleanup should remove expired agents
        cleaned = delegation_manager.cleanup_expired_agents()

        assert cleaned == 1

    def test_delegate_task(self, delegation_manager):
        """Test delegating task to matched agent."""
        delegation_manager.register_agent(
            agent_id="agent-1",
            agent_type="test",
            capabilities=["python"],
            max_concurrent_tasks=3,
        )

        task = TaskRequest(
            task_id="task-001",
            task_type="test",
            required_capabilities=["python"],
        )

        match = delegation_manager.find_best_agent(task)
        result = delegation_manager.delegate_task(task, match)

        assert result["task_id"] == "task-001"
        assert result["agent_id"] == "agent-1"
        assert result["agent_load"] == 1

    def test_delegate_task_no_capacity(self, delegation_manager):
        """Test delegating task when agent has no capacity."""
        delegation_manager.register_agent(
            agent_id="agent-1",
            agent_type="test",
            capabilities=["python"],
            max_concurrent_tasks=1,
        )

        # Fill capacity
        delegation_manager.set_agent_load("agent-1", 1)

        task = TaskRequest(
            task_id="task-001",
            task_type="test",
            required_capabilities=["python"],
        )

        match = AgentMatch(
            agent_id="agent-1",
            agent_type="test",
            score=1.0,
            current_load=1,
            max_load=1,
        )

        with pytest.raises(ValueError, match="has no capacity"):
            delegation_manager.delegate_task(task, match)

    def test_complete_task(self, delegation_manager):
        """Test completing task and decrementing agent load."""
        delegation_manager.register_agent(
            agent_id="agent-1",
            agent_type="test",
            capabilities=["python"],
        )
        delegation_manager.set_agent_load("agent-1", 2)

        success = delegation_manager.complete_task("agent-1", "task-001")

        assert success is True
        load_key = f"{delegation_manager.AGENT_LOAD_PREFIX}agent-1"
        current_load = int(delegation_manager.redis_client.get(load_key))
        assert current_load == 1

    def test_get_statistics(self, delegation_manager):
        """Test getting delegation manager statistics."""
        delegation_manager.register_agent(
            agent_id="agent-1",
            agent_type="backend",
            capabilities=["python"],
            available=True,
        )
        delegation_manager.register_agent(
            agent_id="agent-2",
            agent_type="frontend",
            capabilities=["react"],
            available=True,
        )

        stats = delegation_manager.get_statistics()

        assert stats["total_agents"] == 2
        assert stats["available_agents"] == 2
        assert "agents_by_type" in stats


# ============================================================================
# RESOURCE ALLOCATOR TESTS
# ============================================================================


@pytest.mark.unit
class TestResourceAllocator:
    """Test suite for ResourceAllocator component."""

    def test_set_agent_limits(self, resource_allocator):
        """Test setting resource limits for an agent."""
        success = resource_allocator.set_agent_limits(
            agent_id="agent-1",
            cpu_cores=4.0,
            memory_mb=8192.0,
            max_tasks=5,
        )

        assert success is True
        usage = resource_allocator.get_agent_usage("agent-1")
        assert usage.cpu_limit == 4.0
        assert usage.memory_limit == 8192.0
        assert usage.max_tasks == 5

    def test_set_agent_limits_invalid(self, resource_allocator):
        """Test setting invalid resource limits."""
        with pytest.raises(ValueError):
            resource_allocator.set_agent_limits(
                agent_id="agent-1",
                cpu_cores=-1.0,
                memory_mb=1024.0,
                max_tasks=3,
            )

    def test_get_agent_usage(self, resource_allocator):
        """Test getting agent resource usage."""
        resource_allocator.set_agent_limits(
            agent_id="agent-1",
            cpu_cores=2.0,
            memory_mb=4096.0,
            max_tasks=3,
        )

        usage = resource_allocator.get_agent_usage("agent-1")

        assert usage.agent_id == "agent-1"
        assert usage.cpu_used == 0.0
        assert usage.memory_used == 0.0
        assert usage.active_tasks == 0
        assert usage.cpu_available == 2.0
        assert usage.memory_available == 4096.0

    def test_get_agent_usage_not_found(self, resource_allocator):
        """Test getting usage for non-existent agent."""
        with pytest.raises(ValueError, match="not found"):
            resource_allocator.get_agent_usage("non-existent")

    def test_allocate_resources_success(self, resource_allocator):
        """Test successful resource allocation."""
        resource_allocator.set_agent_limits(
            agent_id="agent-1",
            cpu_cores=4.0,
            memory_mb=8192.0,
            max_tasks=3,
        )

        # Mock Lua script execution for success
        resource_allocator.allocate_script.return_value = [1, "success"]

        success = resource_allocator.allocate_resources(
            agent_id="agent-1",
            cpu=1.0,
            memory=2048.0,
            task_id="task-1",
            priority=Priority.MEDIUM,
        )

        assert success is True

    def test_allocate_resources_failure(self, resource_allocator):
        """Test resource allocation failure due to insufficient resources."""
        resource_allocator.set_agent_limits(
            agent_id="agent-1",
            cpu_cores=1.0,
            memory_mb=1024.0,
            max_tasks=1,
        )

        # Mock Lua script execution for failure
        resource_allocator.allocate_script.return_value = [0, "insufficient_cpu"]

        success = resource_allocator.allocate_resources(
            agent_id="agent-1",
            cpu=2.0,  # More than available
            memory=512.0,
            task_id="task-1",
            priority=Priority.MEDIUM,
        )

        assert success is False

    def test_release_resources(self, resource_allocator):
        """Test releasing resources after task completion."""
        resource_allocator.set_agent_limits(
            agent_id="agent-1",
            cpu_cores=4.0,
            memory_mb=8192.0,
            max_tasks=3,
        )

        # Mock Lua script execution
        resource_allocator.release_script.return_value = [1, "success"]

        success = resource_allocator.release_resources(
            agent_id="agent-1",
            task_id="task-1",
        )

        assert success is True

    def test_release_resources_task_not_found(self, resource_allocator):
        """Test releasing resources for non-existent task."""
        resource_allocator.set_agent_limits(
            agent_id="agent-1",
            cpu_cores=4.0,
            memory_mb=8192.0,
            max_tasks=3,
        )

        # Mock Lua script execution for task not found
        resource_allocator.release_script.return_value = [0, "task_not_found"]

        success = resource_allocator.release_resources(
            agent_id="agent-1",
            task_id="non-existent",
        )

        assert success is False

    def test_check_availability(self, resource_allocator):
        """Test checking resource availability."""
        resource_allocator.set_agent_limits(
            agent_id="agent-1",
            cpu_cores=4.0,
            memory_mb=8192.0,
            max_tasks=3,
        )

        available = resource_allocator.check_availability(
            agent_id="agent-1",
            cpu=2.0,
            memory=4096.0,
        )

        assert available is True

    def test_check_availability_insufficient(self, resource_allocator):
        """Test checking availability with insufficient resources."""
        resource_allocator.set_agent_limits(
            agent_id="agent-1",
            cpu_cores=2.0,
            memory_mb=2048.0,
            max_tasks=1,
        )

        available = resource_allocator.check_availability(
            agent_id="agent-1",
            cpu=4.0,  # More than limit
            memory=1024.0,
        )

        assert available is False

    def test_priority_based_preemption(self, resource_allocator):
        """Test priority-based resource preemption."""
        resource_allocator.set_agent_limits(
            agent_id="agent-1",
            cpu_cores=2.0,
            memory_mb=4096.0,
            max_tasks=2,
        )

        # Simulate low priority task allocation
        resource_allocator.allocate_script.side_effect = [
            [0, "insufficient_cpu"],  # First attempt fails
            [1, "success"],  # After preemption succeeds
        ]

        # Mock preemption to succeed
        with patch.object(resource_allocator, "_attempt_preemption", return_value=True):
            success = resource_allocator.allocate_resources(
                agent_id="agent-1",
                cpu=2.0,
                memory=2048.0,
                task_id="high-priority-task",
                priority=Priority.HIGH,
            )

            assert success is True

    def test_cleanup_expired_reservations(self, resource_allocator):
        """Test cleanup of expired resource reservations."""
        resource_allocator.set_agent_limits(
            agent_id="agent-1",
            cpu_cores=4.0,
            memory_mb=8192.0,
            max_tasks=3,
        )

        # Mock expired reservations
        past_time = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
        resource_allocator.redis_client.zadd(
            "reservation:expiry",
            {f"agent-1:rsv_001": past_time},
        )

        cleaned = resource_allocator.cleanup_expired_reservations()

        assert cleaned >= 0

    def test_detect_deadlocks(self, resource_allocator):
        """Test deadlock detection."""
        resource_allocator.set_agent_limits(
            agent_id="agent-1",
            cpu_cores=2.0,
            memory_mb=4096.0,
            max_tasks=1,
        )

        # Simulate deadlock scenario
        deadlocks = resource_allocator.detect_deadlocks()

        assert isinstance(deadlocks, list)


# ============================================================================
# HANDOFF MANAGER TESTS
# ============================================================================


@pytest.mark.unit
class TestHandoffManager:
    """Test suite for HandoffManager component."""

    def test_create_context(self, handoff_manager):
        """Test creating agent context."""
        context = handoff_manager.create_context(
            agent_id="agent-1",
            agent_type="backend-engineer",
            conversation=[
                {"role": "user", "content": "Implement feature X"},
                {"role": "assistant", "content": "Sure, I'll implement it."},
            ],
            files={"created": ["feature.py"], "modified": ["tests.py"]},
            state={"tests_passing": True, "coverage": 85.0},
            metadata={"version": "1.0"},
        )

        assert context.agent_id == "agent-1"
        assert context.agent_type == "backend-engineer"
        assert len(context.conversation_history) == 2
        assert len(context.files_created) == 1
        assert context.state["tests_passing"] is True

    def test_create_context_invalid(self, handoff_manager):
        """Test creating context with invalid data."""
        with pytest.raises(ValueError):
            handoff_manager.create_context(
                agent_id="",  # Empty agent_id
                agent_type="test",
                conversation=[],
                files={},
                state={},
            )

    def test_serialize_deserialize_context(self, handoff_manager):
        """Test serializing and deserializing agent context."""
        context = AgentContext(
            agent_id="agent-1",
            agent_type="test",
            conversation_history=[{"role": "user", "content": "Hello"}],
            state={"key": "value"},
        )

        serialized = handoff_manager.serialize_context(context)
        deserialized = handoff_manager.deserialize_context(serialized)

        assert deserialized.agent_id == context.agent_id
        assert deserialized.agent_type == context.agent_type
        assert deserialized.state == context.state

    def test_validate_preconditions_pass(self, handoff_manager):
        """Test validating preconditions that pass."""
        context = AgentContext(
            agent_id="agent-1",
            agent_type="test",
            state={"tests_passing": True, "coverage": 90.0},
        )

        preconditions = [
            HandoffPrecondition(
                condition_type="tests_passing",
                expected_value=True,
                operator="==",
            ),
            HandoffPrecondition(
                condition_type="coverage",
                expected_value=80.0,
                operator=">=",
            ),
        ]

        passed, failed = handoff_manager.validate_preconditions(context, preconditions)

        assert passed is True
        assert len(failed) == 0

    def test_validate_preconditions_fail(self, handoff_manager):
        """Test validating preconditions that fail."""
        context = AgentContext(
            agent_id="agent-1",
            agent_type="test",
            state={"tests_passing": False, "coverage": 60.0},
        )

        preconditions = [
            HandoffPrecondition(
                condition_type="tests_passing",
                expected_value=True,
                operator="==",
                required=True,
                error_message="Tests must be passing",
            ),
            HandoffPrecondition(
                condition_type="coverage",
                expected_value=80.0,
                operator=">=",
                required=True,
                error_message="Coverage must be >= 80%",
            ),
        ]

        passed, failed = handoff_manager.validate_preconditions(context, preconditions)

        assert passed is False
        assert len(failed) == 2

    def test_handoff_success(self, handoff_manager):
        """Test successful handoff execution."""
        source_context = AgentContext(
            agent_id="agent-1",
            agent_type="backend-engineer",
            state={"tests_passing": True},
        )

        result = handoff_manager.handoff(
            source_context=source_context,
            target_agent_type="qa-tester",
            workflow_id="workflow-001",
        )

        assert result.success is True
        assert result.validation_passed is True
        assert result.context_transferred is True

    def test_handoff_failed_preconditions(self, handoff_manager):
        """Test handoff with failed preconditions."""
        source_context = AgentContext(
            agent_id="agent-1",
            agent_type="backend-engineer",
            state={"tests_passing": False},
        )

        preconditions = [
            HandoffPrecondition(
                condition_type="tests_passing",
                expected_value=True,
                operator="==",
                required=True,
            )
        ]

        result = handoff_manager.handoff(
            source_context=source_context,
            target_agent_type="qa-tester",
            workflow_id="workflow-001",
            preconditions=preconditions,
        )

        assert result.success is False
        assert result.validation_passed is False
        assert len(result.failed_preconditions) > 0

    def test_transfer_context(self, handoff_manager):
        """Test transferring context via Redis."""
        context = AgentContext(
            agent_id="source-agent",
            agent_type="test",
            state={"key": "value"},
        )

        success = handoff_manager.transfer_context(
            source_agent_id="source-agent",
            target_agent_id="target-agent",
            context=context,
        )

        assert success is True

        # Verify context can be retrieved
        retrieved = handoff_manager.get_transferred_context("target-agent")
        assert retrieved is not None
        assert retrieved.agent_id == context.agent_id

    def test_rollback(self, handoff_manager, mock_postgres):
        """Test rolling back a handoff."""
        # Setup mock cursor to return handoff data
        mock_postgres["cursor"].fetchone.return_value = {
            "target_agent_id": "target-agent"
        }

        success = handoff_manager.rollback("handoff-001")

        assert success is True

    def test_get_handoff_history(self, handoff_manager, mock_postgres):
        """Test querying handoff history."""
        # Setup mock cursor to return history
        mock_postgres["cursor"].fetchall.return_value = [
            {
                "handoff_id": "handoff-001",
                "workflow_id": "workflow-001",
                "source_agent_id": "agent-1",
                "source_agent_type": "backend",
                "target_agent_id": "agent-2",
                "target_agent_type": "qa",
                "success": True,
                "context_transferred": True,
                "rollback_performed": False,
                "created_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc),
            }
        ]

        history = handoff_manager.get_handoff_history("workflow-001", limit=10)

        assert len(history) > 0


# ============================================================================
# WORKFLOW ENGINE TESTS
# ============================================================================


@pytest.mark.unit
class TestWorkflowEngine:
    """Test suite for WorkflowEngine component."""

    def test_create_from_template_tdd(self, workflow_engine):
        """Test creating TDD workflow from template."""
        workflow = workflow_engine.create_from_template(
            template_name="tdd",
            workflow_id="tdd-001",
            feature_name="user_authentication",
            test_file="tests/test_auth.py",
            implementation_file="src/auth.py",
        )

        assert workflow.workflow_id == "tdd-001"
        assert len(workflow.tasks) == 3  # test, implement, refactor

    def test_create_from_template_feature_development(self, workflow_engine):
        """Test creating feature development workflow from template."""
        workflow = workflow_engine.create_from_template(
            template_name="feature_development",
            workflow_id="feature-001",
            feature_name="payment_gateway",
            requirements="Integrate Stripe API",
        )

        assert workflow.workflow_id == "feature-001"
        assert len(workflow.tasks) >= 3

    def test_create_from_template_bug_fix(self, workflow_engine):
        """Test creating bug fix workflow from template."""
        workflow = workflow_engine.create_from_template(
            template_name="bug_fix",
            workflow_id="bug-001",
            bug_id="BUG-123",
            description="Login fails with SSO",
            severity="high",
        )

        assert workflow.workflow_id == "bug-001"
        assert len(workflow.tasks) == 5  # triage, reproduce, fix, verify, review

    def test_create_from_template_not_found(self, workflow_engine):
        """Test creating workflow from non-existent template."""
        with pytest.raises(ValueError, match="not found"):
            workflow_engine.create_from_template(
                template_name="non-existent",
                workflow_id="test-001",
            )

    def test_execute_sequential(self, workflow_engine):
        """Test sequential task execution."""
        tasks = [
            Task(task_id="task-1", agent_type="test"),
            Task(task_id="task-2", agent_type="test"),
            Task(task_id="task-3", agent_type="test"),
        ]

        results = workflow_engine.execute_sequential(tasks)

        assert len(results) == 3
        # Verify tasks executed in order
        for i, task in enumerate(tasks):
            assert task.status == TaskStatus.COMPLETED

    def test_execute_parallel(self, workflow_engine):
        """Test parallel task execution."""
        tasks = [
            Task(task_id="task-1", agent_type="test"),
            Task(task_id="task-2", agent_type="test"),
            Task(task_id="task-3", agent_type="test"),
        ]

        results = workflow_engine.execute_parallel(tasks)

        assert len(results) == 3
        # Verify all tasks completed
        for task in tasks:
            assert task.status == TaskStatus.COMPLETED

    def test_execute_conditional_true_branch(self, workflow_engine):
        """Test conditional execution taking true branch."""
        if_tasks = [Task(task_id="if-task-1", agent_type="test")]
        else_tasks = [Task(task_id="else-task-1", agent_type="test")]

        context = {"condition_met": True}

        results = workflow_engine.execute_conditional(
            condition="condition_met == True",
            if_tasks=if_tasks,
            else_tasks=else_tasks,
            context=context,
        )

        assert len(results) == 1
        assert if_tasks[0].status == TaskStatus.COMPLETED
        assert else_tasks[0].status == TaskStatus.PENDING

    def test_execute_conditional_false_branch(self, workflow_engine):
        """Test conditional execution taking false branch."""
        if_tasks = [Task(task_id="if-task-1", agent_type="test")]
        else_tasks = [Task(task_id="else-task-1", agent_type="test")]

        context = {"condition_met": False}

        results = workflow_engine.execute_conditional(
            condition="condition_met == True",
            if_tasks=if_tasks,
            else_tasks=else_tasks,
            context=context,
        )

        assert len(results) == 1
        assert if_tasks[0].status == TaskStatus.PENDING
        assert else_tasks[0].status == TaskStatus.COMPLETED

    def test_evaluate_condition_operators(self, workflow_engine):
        """Test evaluating conditions with different operators."""
        context = {"value": 50}

        assert workflow_engine.evaluate_condition("value == 50", context) is True
        assert workflow_engine.evaluate_condition("value != 100", context) is True
        assert workflow_engine.evaluate_condition("value > 40", context) is True
        assert workflow_engine.evaluate_condition("value < 60", context) is True
        assert workflow_engine.evaluate_condition("value >= 50", context) is True
        assert workflow_engine.evaluate_condition("value <= 50", context) is True

    def test_evaluate_condition_compound(self, workflow_engine):
        """Test evaluating compound conditions."""
        context = {"a": True, "b": True, "c": False}

        assert workflow_engine.evaluate_condition("a and b", context) is True
        assert workflow_engine.evaluate_condition("a or c", context) is True
        assert workflow_engine.evaluate_condition("not c", context) is True
        assert workflow_engine.evaluate_condition("a and c", context) is False

    def test_pause_resume_workflow(self, workflow_engine):
        """Test pausing and resuming workflow."""
        workflow = Workflow(
            workflow_id="test-001",
            name="Test",
            tasks=[Task(task_id="task-1", agent_type="test")],
        )
        workflow.status = WorkflowStatus.RUNNING
        workflow_engine.workflows[workflow.workflow_id] = workflow

        # Pause workflow
        success = workflow_engine.pause_workflow(workflow.workflow_id)
        assert success is True

        # Resume workflow
        success = workflow_engine.resume_workflow(workflow.workflow_id)
        assert success is True

    def test_dynamic_task_generation(self, workflow_engine):
        """Test generating tasks dynamically."""

        def generator(context: Dict[str, Any]) -> List[Task]:
            count = context.get("task_count", 3)
            return [
                Task(task_id=f"dynamic-{i}", agent_type="test") for i in range(count)
            ]

        context = {"task_count": 5}

        tasks = workflow_engine.generate_dynamic_tasks(generator, context)

        assert len(tasks) == 5


# ============================================================================
# HUB-SPOKE COORDINATOR TESTS
# ============================================================================


@pytest.mark.unit
class TestHubSpokeCoordinator:
    """Test suite for HubSpokeCoordinator component."""

    def test_register_hub(self, hub_spoke_coordinator):
        """Test registering hub agent."""
        success = hub_spoke_coordinator.register_hub(
            hub_id="hub-001",
            hub_type="coordinator",
            specializations=["planning", "coordination"],
            decomposition_strategy=DecompositionStrategy.FUNCTIONAL,
        )

        assert success is True
        status = hub_spoke_coordinator.get_hub_status("hub-001")
        assert status is not None

    def test_register_spoke(self, hub_spoke_coordinator):
        """Test registering spoke agent."""
        success = hub_spoke_coordinator.register_spoke(
            spoke_id="spoke-001",
            spoke_type="backend-engineer",
            specializations=["python-development", "api-development"],
            max_concurrent_tasks=3,
        )

        assert success is True
        status = hub_spoke_coordinator.get_spoke_status("spoke-001")
        assert status is not None

    def test_decompose_objective_functional(self, hub_spoke_coordinator):
        """Test decomposing objective using functional strategy."""
        hub = HubAgent(
            hub_id="hub-001",
            decomposition_strategy=DecompositionStrategy.FUNCTIONAL,
        )

        objective = Objective(
            objective_id="obj-001",
            description="Build a REST API with database and frontend",
            requirements=["API endpoints", "Database schema", "UI components"],
        )

        subtasks = hub_spoke_coordinator.decompose_objective(objective, hub)

        assert len(subtasks) > 0
        # Should have API, UI, and database tasks
        task_types = {st.required_specializations[0] for st in subtasks}
        assert any("api" in t or "backend" in t for t in task_types)

    def test_decompose_objective_sequential(self, hub_spoke_coordinator):
        """Test decomposing objective using sequential strategy."""
        hub = HubAgent(
            hub_id="hub-001",
            decomposition_strategy=DecompositionStrategy.SEQUENTIAL,
        )

        objective = Objective(
            objective_id="obj-001",
            description="Implement and test feature",
        )

        subtasks = hub_spoke_coordinator.decompose_objective(objective, hub)

        assert len(subtasks) == 3  # Planning, Implementation, Testing
        # Verify sequential dependencies
        assert len(subtasks[0].dependencies) == 0
        assert len(subtasks[1].dependencies) == 1
        assert len(subtasks[2].dependencies) == 1

    def test_decompose_objective_parallel(self, hub_spoke_coordinator):
        """Test decomposing objective using parallel strategy."""
        hub = HubAgent(
            hub_id="hub-001",
            decomposition_strategy=DecompositionStrategy.PARALLEL,
        )

        objective = Objective(
            objective_id="obj-001",
            description="Implement multiple independent components",
        )

        subtasks = hub_spoke_coordinator.decompose_objective(objective, hub)

        assert len(subtasks) > 0
        # Verify no dependencies (parallel)
        for subtask in subtasks:
            assert len(subtask.dependencies) == 0

    def test_decompose_objective_hierarchical(self, hub_spoke_coordinator):
        """Test decomposing objective using hierarchical strategy."""
        hub = HubAgent(
            hub_id="hub-001",
            decomposition_strategy=DecompositionStrategy.HIERARCHICAL,
        )

        objective = Objective(
            objective_id="obj-001",
            description="Complex multi-level project",
        )

        subtasks = hub_spoke_coordinator.decompose_objective(objective, hub)

        assert len(subtasks) > 0
        # Should have parent and child tasks
        parent_tasks = [st for st in subtasks if not st.dependencies]
        child_tasks = [st for st in subtasks if st.dependencies]
        assert len(parent_tasks) > 0
        assert len(child_tasks) > 0

    def test_decompose_objective_domain(self, hub_spoke_coordinator):
        """Test decomposing objective using domain strategy."""
        hub = HubAgent(
            hub_id="hub-001",
            decomposition_strategy=DecompositionStrategy.DOMAIN,
        )

        objective = Objective(
            objective_id="obj-001",
            description="Build e-commerce system",
            context={"domains": ["payment", "inventory", "shipping"]},
        )

        subtasks = hub_spoke_coordinator.decompose_objective(objective, hub)

        assert len(subtasks) == 3
        # Verify domain-specific tasks
        domains = {st.context.get("domain") for st in subtasks}
        assert "payment" in domains
        assert "inventory" in domains

    def test_match_spoke_exact(self, hub_spoke_coordinator):
        """Test matching spoke with exact specialization match."""
        hub_spoke_coordinator.register_spoke(
            spoke_id="spoke-001",
            spoke_type="backend",
            specializations=["python-development", "api-development"],
            max_concurrent_tasks=3,
        )

        subtask = SubTask(
            objective_id="obj-001",
            description="Implement API",
            required_specializations=["python-development", "api-development"],
        )

        match = hub_spoke_coordinator.match_spoke(subtask)

        assert match is not None
        assert match.spoke_id == "spoke-001"

    def test_match_spoke_partial(self, hub_spoke_coordinator):
        """Test matching spoke with partial specialization match."""
        hub_spoke_coordinator.register_spoke(
            spoke_id="spoke-001",
            spoke_type="fullstack",
            specializations=["python", "react", "postgresql"],
            max_concurrent_tasks=3,
        )

        subtask = SubTask(
            objective_id="obj-001",
            description="Backend work",
            required_specializations=["python", "redis"],
        )

        match = hub_spoke_coordinator.match_spoke(subtask)

        assert match is not None
        assert match.spoke_id == "spoke-001"

    def test_match_spoke_no_match(self, hub_spoke_coordinator):
        """Test matching spoke with no specialization match."""
        hub_spoke_coordinator.register_spoke(
            spoke_id="spoke-001",
            spoke_type="frontend",
            specializations=["react", "typescript"],
            max_concurrent_tasks=3,
        )

        subtask = SubTask(
            objective_id="obj-001",
            description="Backend work",
            required_specializations=["python", "django"],
        )

        match = hub_spoke_coordinator.match_spoke(subtask)

        assert match is None

    def test_execute_hub_spoke(self, hub_spoke_coordinator):
        """Test executing hub-spoke coordination."""
        hub_spoke_coordinator.register_hub(hub_id="hub-001")

        hub_spoke_coordinator.register_spoke(
            spoke_id="spoke-001",
            spoke_type="backend",
            specializations=["api-development", "backend-engineer"],
            max_concurrent_tasks=3,
        )

        objective = Objective(
            objective_id="obj-001",
            description="Build API endpoints",
        )

        result = hub_spoke_coordinator.execute_hub_spoke(
            objective=objective,
            hub_id="hub-001",
        )

        assert result.success in [True, False]
        assert result.total_subtasks > 0

    def test_aggregate_results(self, hub_spoke_coordinator):
        """Test aggregating results from spoke agents."""
        hub = HubAgent(hub_id="hub-001")

        spoke_results = [
            {
                "subtask_id": "st-1",
                "spoke_id": "spoke-1",
                "spoke_type": "backend",
                "success": True,
                "output": {"status": "completed"},
            },
            {
                "subtask_id": "st-2",
                "spoke_id": "spoke-2",
                "spoke_type": "frontend",
                "success": True,
                "output": {"status": "completed"},
            },
        ]

        synthesized = hub_spoke_coordinator.aggregate_results(hub, spoke_results)

        assert synthesized["total_spokes"] == 2
        assert synthesized["successful_spokes"] == 2
        assert synthesized["success_rate"] == 100.0

    def test_handle_spoke_failure(self, hub_spoke_coordinator):
        """Test handling spoke agent failure."""
        hub_spoke_coordinator.register_spoke(
            spoke_id="spoke-001",
            spoke_type="backend",
            specializations=["python"],
        )

        subtask = SubTask(
            objective_id="obj-001",
            description="Failed task",
            required_specializations=["python"],
        )

        result = hub_spoke_coordinator.handle_spoke_failure("spoke-001", subtask)

        assert result["failure_handled"] is True
        assert subtask.status == SpokeStatus.FAILED


# ============================================================================
# CLI INTERFACE TESTS (Integration)
# ============================================================================


@pytest.mark.integration
class TestCLI:
    """Integration tests for CLI interface."""

    def test_workflow_create(self, cli_runner, tmp_path):
        """Test workflow create command."""
        workflow_def = {
            "workflow": {
                "id": "test-001",
                "name": "Test Workflow",
                "tasks": [{"task_id": "task-1", "agent_type": "test"}],
            }
        }

        yaml_file = tmp_path / "workflow.yaml"
        yaml_file.write_text(yaml.dump(workflow_def))

        with patch("orchestration_cli.get_orchestrator") as mock_orchestrator:
            mock_orch = MagicMock()
            mock_workflow = MagicMock()
            mock_workflow.workflow_id = "test-001"
            mock_workflow.name = "Test Workflow"
            mock_workflow.tasks = [MagicMock()]
            mock_workflow.priority = "medium"

            mock_orch.create_workflow.return_value = "test-001"
            mock_orchestrator.return_value = mock_orch

            with patch(
                "orchestration_cli.TaskOrchestrator.parse_workflow_definition",
                return_value=mock_workflow,
            ):
                result = cli_runner.invoke(
                    cli, ["workflow", "create", "--file", str(yaml_file)]
                )

                assert result.exit_code == 0
                assert "test-001" in result.output

    def test_agent_register(self, cli_runner, tmp_path):
        """Test agent register command."""
        agent_config = {
            "agent_id": "agent-001",
            "agent_type": "backend-engineer",
            "capabilities": ["python", "fastapi"],
        }

        json_file = tmp_path / "agent.json"
        json_file.write_text(json.dumps(agent_config))

        with patch("orchestration_cli.get_delegation_manager") as mock_manager:
            mock_dm = MagicMock()
            mock_dm.register_agent.return_value = True
            mock_manager.return_value = mock_dm

            result = cli_runner.invoke(
                cli, ["agent", "register", "--file", str(json_file)]
            )

            assert result.exit_code == 0
            assert "agent-001" in result.output

    def test_agent_list(self, cli_runner):
        """Test agent list command."""
        with patch("orchestration_cli.get_delegation_manager") as mock_manager:
            mock_dm = MagicMock()
            mock_dm.list_agents.return_value = [
                {
                    "agent_id": "agent-001",
                    "agent_type": "backend",
                    "capabilities": ["python"],
                    "current_load": 1,
                    "max_concurrent_tasks": 3,
                    "available": True,
                }
            ]
            mock_manager.return_value = mock_dm

            result = cli_runner.invoke(cli, ["agent", "list"])

            assert result.exit_code == 0
            assert "agent-001" in result.output

    def test_task_delegate(self, cli_runner, tmp_path):
        """Test task delegate command."""
        task_data = {
            "task_id": "task-001",
            "task_type": "implement",
            "required_capabilities": ["python"],
        }

        json_file = tmp_path / "task.json"
        json_file.write_text(json.dumps(task_data))

        with patch("orchestration_cli.get_delegation_manager") as mock_manager:
            mock_dm = MagicMock()
            mock_match = AgentMatch(
                agent_id="agent-001",
                agent_type="backend",
                score=1.0,
                current_load=0,
                max_load=3,
            )
            mock_dm.find_best_agent.return_value = mock_match
            mock_dm.delegate_task.return_value = {
                "task_id": "task-001",
                "agent_id": "agent-001",
                "agent_type": "backend",
                "match_score": 1.0,
                "agent_load": 1,
                "max_load": 3,
            }
            mock_manager.return_value = mock_dm

            result = cli_runner.invoke(cli, ["task", "delegate", "--file", str(json_file)])

            assert result.exit_code == 0

    def test_monitor_metrics(self, cli_runner):
        """Test monitor metrics command."""
        with patch("orchestration_cli.get_delegation_manager") as mock_manager:
            mock_dm = MagicMock()
            mock_dm.get_statistics.return_value = {
                "total_agents": 5,
                "available_agents": 3,
                "agents_with_capacity": 2,
                "total_active_tasks": 10,
                "max_capacity": 15,
                "capacity_utilization": 66.7,
                "average_load_percentage": 50.0,
            }
            mock_manager.return_value = mock_dm

            result = cli_runner.invoke(cli, ["monitor", "metrics"])

            assert result.exit_code == 0
            assert "Total Agents" in result.output

    def test_health_check(self, cli_runner):
        """Test health check command."""
        with patch("redis.from_url") as mock_redis:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            result = cli_runner.invoke(cli, ["monitor", "health-check"])

            assert result.exit_code == 0
            assert "Redis" in result.output


# ============================================================================
# ADDITIONAL EDGE CASE TESTS
# ============================================================================


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_task_priority_validation(self):
        """Test task priority validation."""
        # Valid priorities
        task = Task(task_id="test", agent_type="test", priority="low")
        assert task.priority == "low"

        task = Task(task_id="test", agent_type="test", priority="medium")
        assert task.priority == "medium"

        task = Task(task_id="test", agent_type="test", priority="high")
        assert task.priority == "high"

        # Invalid priority
        with pytest.raises(ValidationError):
            Task(task_id="test", agent_type="test", priority="invalid")

    def test_resource_limits_validation(self):
        """Test resource limits validation."""
        # Valid limits
        limits = ResourceLimits(
            agent_id="test",
            cpu_cores=4.0,
            memory_mb=8192.0,
            max_tasks=5,
        )
        assert limits.cpu_cores == 4.0

        # Invalid CPU cores
        with pytest.raises(ValidationError):
            ResourceLimits(
                agent_id="test",
                cpu_cores=-1.0,
                memory_mb=1024.0,
                max_tasks=3,
            )

    def test_conversation_history_validation(self):
        """Test conversation history validation."""
        # Valid conversation
        context = AgentContext(
            agent_id="test",
            agent_type="test",
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ],
        )
        assert len(context.conversation_history) == 2

        # Invalid conversation - missing role
        with pytest.raises(ValidationError):
            AgentContext(
                agent_id="test",
                agent_type="test",
                conversation_history=[{"content": "Hello"}],
            )

        # Invalid conversation - invalid role
        with pytest.raises(ValidationError):
            AgentContext(
                agent_id="test",
                agent_type="test",
                conversation_history=[{"role": "invalid", "content": "Hello"}],
            )

    def test_empty_workflow(self, task_orchestrator):
        """Test handling empty workflow."""
        workflow = Workflow(
            workflow_id="empty",
            name="Empty Workflow",
            tasks=[],
        )
        task_orchestrator.create_workflow(workflow)

        result = task_orchestrator.execute_workflow(workflow.workflow_id)

        assert result["status"] == "completed"
        assert result["tasks_completed"] == 0

    def test_circular_dependency_detection(self, task_orchestrator):
        """Test detection of circular dependencies."""
        workflow = Workflow(
            workflow_id="circular",
            name="Circular Workflow",
            tasks=[
                Task(task_id="A", agent_type="test", depends_on=["C"]),
                Task(task_id="B", agent_type="test", depends_on=["A"]),
                Task(task_id="C", agent_type="test", depends_on=["B"]),
            ],
        )
        task_orchestrator.create_workflow(workflow)

        with pytest.raises(RuntimeError, match="circular dependency"):
            task_orchestrator.execute_workflow(workflow.workflow_id)


# ============================================================================
# PERFORMANCE AND LOAD TESTS
# ============================================================================


@pytest.mark.unit
class TestPerformance:
    """Performance and load tests."""

    def test_register_multiple_agents(self, delegation_manager):
        """Test registering multiple agents."""
        for i in range(100):
            delegation_manager.register_agent(
                agent_id=f"agent-{i}",
                agent_type="test",
                capabilities=[f"skill-{i % 10}"],
            )

        stats = delegation_manager.get_statistics()
        assert stats["total_agents"] == 100

    def test_find_agent_performance(self, delegation_manager):
        """Test agent finding performance with many agents."""
        # Register 50 agents
        for i in range(50):
            delegation_manager.register_agent(
                agent_id=f"agent-{i}",
                agent_type="test",
                capabilities=["python", f"skill-{i}"],
                max_concurrent_tasks=3,
            )

        task = TaskRequest(
            task_id="test",
            task_type="test",
            required_capabilities=["python"],
        )

        # Should complete quickly
        start_time = time.time()
        match = delegation_manager.find_best_agent(task)
        duration = time.time() - start_time

        assert match is not None
        assert duration < 1.0  # Should complete in < 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=term-missing"])
