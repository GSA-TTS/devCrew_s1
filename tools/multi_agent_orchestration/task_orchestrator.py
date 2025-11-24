"""
Task Orchestrator - Prefect-based workflow coordination.

Coordinates multi-agent workflows with dependency management, parallel execution,
and state transitions.
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import yaml
from prefect import flow, get_run_logger
from prefect.task_runners import ConcurrentTaskRunner
from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """Task definition for multi-agent workflows."""

    task_id: str = Field(..., description="Unique task identifier")
    agent_type: str = Field(..., description="Type of agent to execute task")
    agent_capabilities: List[str] = Field(
        default_factory=list, description="Required agent capabilities"
    )
    input_data: Dict[str, Any] = Field(
        default_factory=dict, description="Input data for task execution"
    )
    depends_on: List[str] = Field(
        default_factory=list, description="Task IDs this task depends on"
    )
    timeout: int = Field(default=600, description="Task timeout in seconds")
    retry: int = Field(default=3, description="Number of retries on failure")
    priority: str = Field(default="medium", description="Task priority")
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Current task status"
    )
    agent_id: Optional[str] = Field(
        default=None, description="ID of agent executing task"
    )
    started_at: Optional[datetime] = Field(default=None, description="Task start time")
    completed_at: Optional[datetime] = Field(
        default=None, description="Task completion time"
    )
    output: Optional[Dict[str, Any]] = Field(
        default=None, description="Task output data"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate task priority."""
        valid_priorities = {"low", "medium", "high"}
        if v not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")
        return v


class Workflow(BaseModel):
    """Workflow definition containing multiple tasks."""

    workflow_id: str = Field(..., description="Unique workflow identifier")
    name: str = Field(..., description="Workflow name")
    priority: str = Field(default="medium", description="Workflow priority")
    timeout: int = Field(default=3600, description="Workflow timeout in seconds")
    tasks: List[Task] = Field(
        default_factory=list, description="List of tasks in workflow"
    )
    status: WorkflowStatus = Field(
        default=WorkflowStatus.PENDING, description="Current workflow status"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Workflow start time"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Workflow completion time"
    )
    tasks_completed: int = Field(default=0, description="Number of tasks completed")
    tasks_failed: int = Field(default=0, description="Number of tasks failed")
    notification: Optional[Dict[str, List[str]]] = Field(
        default=None, description="Notification configuration"
    )

    def add_task(self, task: Task) -> None:
        """Add a task to the workflow."""
        self.tasks.append(task)

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_ready_tasks(self) -> List[Task]:
        """
        Get tasks that are ready to execute.

        A task is ready if:
        1. Status is PENDING
        2. All dependencies are completed
        """
        ready = []
        for task in self.tasks:
            if task.status != TaskStatus.PENDING:
                continue

            # Check if all dependencies are completed
            deps_completed = True
            for dep_id in task.depends_on:
                dep_task = self.get_task(dep_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    deps_completed = False
                    break

            if deps_completed:
                ready.append(task)

        return ready


class TaskOrchestrator:
    """
    Orchestrate multi-agent workflows using Prefect.

    Manages workflow execution, task scheduling, dependency resolution,
    and state transitions.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize the task orchestrator.

        Args:
            redis_url: Redis connection URL for state storage
        """
        self.redis_url = redis_url
        self.workflows: Dict[str, Workflow] = {}

    @staticmethod
    def parse_workflow_definition(file_path: str) -> Workflow:
        """
        Parse workflow definition from YAML or JSON file.

        Args:
            file_path: Path to workflow definition file

        Returns:
            Parsed Workflow object

        Raises:
            ValueError: If file format is invalid
        """
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                data = yaml.safe_load(f)
            elif file_path.endswith(".json"):
                data = json.load(f)
            else:
                raise ValueError("File must be YAML or JSON")

        # Extract workflow data
        workflow_data = data.get("workflow", {})

        # Build tasks
        tasks = []
        for task_data in workflow_data.get("tasks", []):
            task = Task(
                task_id=task_data["task_id"],
                agent_type=task_data["agent_type"],
                agent_capabilities=task_data.get("agent_capabilities", []),
                input_data=task_data.get("input", {}),
                depends_on=task_data.get("depends_on", []),
                timeout=task_data.get("timeout", 600),
                retry=task_data.get("retry", 3),
            )
            tasks.append(task)

        # Create workflow
        workflow = Workflow(
            workflow_id=workflow_data["id"],
            name=workflow_data["name"],
            priority=workflow_data.get("priority", "medium"),
            timeout=workflow_data.get("timeout", 3600),
            tasks=tasks,
            notification=workflow_data.get("notification"),
        )

        return workflow

    def create_workflow(self, workflow: Workflow) -> str:
        """
        Register a workflow for execution.

        Args:
            workflow: Workflow to register

        Returns:
            Workflow ID
        """
        self.workflows[workflow.workflow_id] = workflow
        return workflow.workflow_id

    @flow(
        name="multi_agent_workflow",
        task_runner=ConcurrentTaskRunner(),
    )
    def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Execute a workflow using Prefect.

        Args:
            workflow_id: ID of workflow to execute

        Returns:
            Workflow execution result
        """
        logger = get_run_logger()
        workflow = self.workflows.get(workflow_id)

        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        logger.info(f"Starting workflow: {workflow.name} ({workflow_id})")

        # Update workflow status
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now(timezone.utc)

        try:
            # Execute tasks based on dependencies
            task_results = {}
            completed_tasks = set()

            while len(completed_tasks) < len(workflow.tasks):
                # Get ready tasks
                ready_tasks = workflow.get_ready_tasks()

                if not ready_tasks:
                    # Check if there are still pending tasks
                    pending = [
                        t for t in workflow.tasks if t.status == TaskStatus.PENDING
                    ]
                    if pending:
                        raise RuntimeError(
                            "Workflow has pending tasks but none are ready "
                            "(possible circular dependency)"
                        )
                    break

                # Execute ready tasks
                for task in ready_tasks:
                    logger.info(f"Executing task: {task.task_id}")
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now(timezone.utc)

                    try:
                        # Execute task (placeholder - actual execution delegated)
                        result = self._execute_task(task, task_results)
                        task.output = result
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.now(timezone.utc)
                        workflow.tasks_completed += 1
                        completed_tasks.add(task.task_id)
                        task_results[task.task_id] = result
                        logger.info(f"Task {task.task_id} completed successfully")

                    except Exception as e:
                        logger.error(f"Task {task.task_id} failed: {str(e)}")
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                        task.completed_at = datetime.now(timezone.utc)
                        workflow.tasks_failed += 1
                        completed_tasks.add(task.task_id)

                        # Optionally stop workflow on task failure
                        raise

            # Workflow completed successfully
            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now(timezone.utc)

            duration = (
                (workflow.completed_at - workflow.started_at).total_seconds()
                if workflow.completed_at and workflow.started_at
                else 0
            )

            return {
                "workflow_id": workflow.workflow_id,
                "status": workflow.status.value,
                "started_at": (
                    workflow.started_at.isoformat() if workflow.started_at else None
                ),
                "completed_at": (
                    workflow.completed_at.isoformat() if workflow.completed_at else None
                ),
                "duration_seconds": duration,
                "tasks_completed": workflow.tasks_completed,
                "tasks_failed": workflow.tasks_failed,
            }

        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now(timezone.utc)
            raise

    def _execute_task(
        self, task: Task, previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single task.

        This is a placeholder for actual task execution which would be
        delegated to the DelegationManager and agents.

        Args:
            task: Task to execute
            previous_results: Results from previous tasks

        Returns:
            Task execution result
        """
        # Placeholder implementation
        # In real implementation, this would delegate to DelegationManager
        # which would route to appropriate agent based on capabilities

        return {
            "task_id": task.task_id,
            "status": "success",
            "message": f"Task {task.task_id} executed successfully",
            "agent_type": task.agent_type,
        }

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow status.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow status information
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "started_at": (
                workflow.started_at.isoformat() if workflow.started_at else None
            ),
            "completed_at": (
                workflow.completed_at.isoformat() if workflow.completed_at else None
            ),
            "tasks_completed": workflow.tasks_completed,
            "tasks_failed": workflow.tasks_failed,
            "total_tasks": len(workflow.tasks),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "agent_type": t.agent_type,
                    "status": t.status.value,
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                    "completed_at": (
                        t.completed_at.isoformat() if t.completed_at else None
                    ),
                }
                for t in workflow.tasks
            ],
        }

    def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel a running workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            True if cancelled successfully
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if workflow.status != WorkflowStatus.RUNNING:
            return False

        workflow.status = WorkflowStatus.CANCELLED
        workflow.completed_at = datetime.now(timezone.utc)

        # Cancel running tasks
        for task in workflow.tasks:
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now(timezone.utc)

        return True
