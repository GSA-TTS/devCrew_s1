"""
Workflow Engine - Advanced workflow execution with conditional logic.

Provides complex workflow patterns including sequential execution,
parallel execution, conditional branching, dynamic task generation,
and reusable workflow templates for common development patterns
(TDD, feature development, bug fixing).
"""

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import redis
from prefect import flow, get_run_logger
from prefect import task as prefect_task
from prefect.task_runners import ConcurrentTaskRunner
from pydantic import BaseModel, Field, field_validator

from task_orchestrator import (Task, TaskOrchestrator, TaskStatus, Workflow,
                               WorkflowStatus)


class ExecutionMode(str, Enum):
    """Task execution mode."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    DYNAMIC = "dynamic"


class ConditionalOperator(str, Enum):
    """Operators for conditional expressions."""

    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    AND = "and"
    OR = "or"
    NOT = "not"


class ConditionalBranch(BaseModel):
    """Model for conditional workflow branching."""

    condition_expr: str = Field(..., description="Condition expression to evaluate")
    if_tasks: List[Task] = Field(
        default_factory=list,
        description="Tasks to execute if condition is true",
    )
    else_tasks: List[Task] = Field(
        default_factory=list,
        description="Tasks to execute if condition is false",
    )
    context_variable: Optional[str] = Field(
        default=None,
        description="Context variable to evaluate condition against",
    )

    @field_validator("condition_expr")
    @classmethod
    def validate_condition_expr(cls, v: str) -> str:
        """Validate condition expression syntax."""
        if not v or not v.strip():
            raise ValueError("Condition expression cannot be empty")
        return v.strip()


class WorkflowTemplate(ABC):
    """
    Abstract base class for workflow templates.

    Templates provide reusable workflow patterns for common
    development scenarios.
    """

    def __init__(self, workflow_id: str, name: str):
        """
        Initialize workflow template.

        Args:
            workflow_id: Unique identifier for the workflow
            name: Human-readable workflow name
        """
        self.workflow_id = workflow_id
        self.name = name

    @abstractmethod
    def create_workflow(self, **params: Any) -> Workflow:
        """
        Create a workflow instance from the template.

        Args:
            **params: Template-specific parameters

        Returns:
            Configured Workflow instance
        """
        pass

    def _create_task(
        self,
        task_id: str,
        agent_type: str,
        input_data: Dict[str, Any],
        depends_on: Optional[List[str]] = None,
        timeout: int = 600,
    ) -> Task:
        """
        Helper method to create a task.

        Args:
            task_id: Task identifier
            agent_type: Type of agent to execute the task
            input_data: Input data for the task
            depends_on: Task dependencies
            timeout: Task timeout in seconds

        Returns:
            Configured Task instance
        """
        return Task(
            task_id=task_id,
            agent_type=agent_type,
            input_data=input_data,
            depends_on=depends_on or [],
            timeout=timeout,
        )


class TDDWorkflow(WorkflowTemplate):
    """
    Test-Driven Development workflow template.

    Implements the classic TDD cycle: Red → Green → Refactor
    """

    def create_workflow(self, **params: Any) -> Workflow:
        """
        Create TDD workflow.

        Args:
            **params: Template parameters
                - feature_name: Name of the feature being developed
                - test_file: Path to test file
                - implementation_file: Path to implementation file
                - requirements: Feature requirements

        Returns:
            TDD workflow instance
        """
        feature_name = params.get("feature_name", "feature")
        test_file = params.get("test_file", "tests/test_feature.py")
        impl_file = params.get("implementation_file", "src/feature.py")
        requirements = params.get("requirements", "")

        # Phase 1: Red - Write failing tests
        test_task = self._create_task(
            task_id=f"{self.workflow_id}_test",
            agent_type="QA-Tester",
            input_data={
                "action": "write_tests",
                "feature_name": feature_name,
                "test_file": test_file,
                "requirements": requirements,
                "test_type": "unit",
            },
            timeout=900,
        )

        # Phase 2: Green - Implement feature to pass tests
        implement_task = self._create_task(
            task_id=f"{self.workflow_id}_implement",
            agent_type="Backend-Engineer",
            input_data={
                "action": "implement_feature",
                "feature_name": feature_name,
                "implementation_file": impl_file,
                "test_file": test_file,
                "requirements": requirements,
            },
            depends_on=[test_task.task_id],
            timeout=1800,
        )

        # Phase 3: Refactor - Improve code quality
        refactor_task = self._create_task(
            task_id=f"{self.workflow_id}_refactor",
            agent_type="Code-Reviewer",
            input_data={
                "action": "refactor_code",
                "feature_name": feature_name,
                "files": [impl_file, test_file],
                "focus": ["code_quality", "readability", "performance"],
            },
            depends_on=[implement_task.task_id],
            timeout=900,
        )

        workflow = Workflow(
            workflow_id=self.workflow_id,
            name=self.name,
            priority="high",
            tasks=[test_task, implement_task, refactor_task],
        )

        return workflow


class FeatureDevelopmentWorkflow(WorkflowTemplate):
    """
    Full feature development workflow template.

    Implements end-to-end feature development with design, implementation,
    testing, and review phases.
    """

    def create_workflow(self, **params: Any) -> Workflow:
        """
        Create feature development workflow.

        Args:
            **params: Template parameters
                - feature_name: Name of the feature
                - requirements: Feature requirements
                - design_needed: Whether design phase is needed
                - review_required: Whether code review is required

        Returns:
            Feature development workflow instance
        """
        feature_name = params.get("feature_name", "new_feature")
        requirements = params.get("requirements", "")
        design_needed = params.get("design_needed", True)
        review_required = params.get("review_required", True)

        tasks = []

        # Phase 1: Design (optional)
        if design_needed:
            design_task = self._create_task(
                task_id=f"{self.workflow_id}_design",
                agent_type="Architect",
                input_data={
                    "action": "design_feature",
                    "feature_name": feature_name,
                    "requirements": requirements,
                    "output_format": "technical_spec",
                },
                timeout=1200,
            )
            tasks.append(design_task)

        # Phase 2: Implementation
        prev_deps = [tasks[-1].task_id] if tasks else []
        implement_task = self._create_task(
            task_id=f"{self.workflow_id}_implement",
            agent_type="Backend-Engineer",
            input_data={
                "action": "implement_feature",
                "feature_name": feature_name,
                "requirements": requirements,
            },
            depends_on=prev_deps,
            timeout=2400,
        )
        tasks.append(implement_task)

        # Phase 3: Testing
        test_task = self._create_task(
            task_id=f"{self.workflow_id}_test",
            agent_type="QA-Tester",
            input_data={
                "action": "test_feature",
                "feature_name": feature_name,
                "test_types": ["unit", "integration", "e2e"],
            },
            depends_on=[implement_task.task_id],
            timeout=1800,
        )
        tasks.append(test_task)

        # Phase 4: Code Review (optional)
        if review_required:
            review_task = self._create_task(
                task_id=f"{self.workflow_id}_review",
                agent_type="Code-Reviewer",
                input_data={
                    "action": "review_code",
                    "feature_name": feature_name,
                    "review_focus": [
                        "code_quality",
                        "security",
                        "performance",
                        "maintainability",
                    ],
                },
                depends_on=[test_task.task_id],
                timeout=900,
            )
            tasks.append(review_task)

        # Phase 5: Documentation
        prev_deps = [tasks[-1].task_id]
        doc_task = self._create_task(
            task_id=f"{self.workflow_id}_document",
            agent_type="Tech-Writer",
            input_data={
                "action": "document_feature",
                "feature_name": feature_name,
                "documentation_types": ["api_docs", "user_guide"],
            },
            depends_on=prev_deps,
            timeout=600,
        )
        tasks.append(doc_task)

        workflow = Workflow(
            workflow_id=self.workflow_id,
            name=self.name,
            priority="medium",
            tasks=tasks,
        )

        return workflow


class BugFixWorkflow(WorkflowTemplate):
    """
    Bug fix workflow template.

    Implements systematic bug fixing: Triage → Reproduce → Fix → Test → Review
    """

    def create_workflow(self, **params: Any) -> Workflow:
        """
        Create bug fix workflow.

        Args:
            **params: Template parameters
                - bug_id: Bug identifier
                - description: Bug description
                - severity: Bug severity (low/medium/high/critical)
                - affected_files: Files affected by the bug

        Returns:
            Bug fix workflow instance
        """
        bug_id = params.get("bug_id", "BUG-001")
        description = params.get("description", "")
        severity = params.get("severity", "medium")
        affected_files = params.get("affected_files", [])

        # Phase 1: Triage and analysis
        triage_task = self._create_task(
            task_id=f"{self.workflow_id}_triage",
            agent_type="QA-Tester",
            input_data={
                "action": "triage_bug",
                "bug_id": bug_id,
                "description": description,
                "severity": severity,
            },
            timeout=600,
        )

        # Phase 2: Reproduce bug
        reproduce_task = self._create_task(
            task_id=f"{self.workflow_id}_reproduce",
            agent_type="QA-Tester",
            input_data={
                "action": "reproduce_bug",
                "bug_id": bug_id,
                "description": description,
                "affected_files": affected_files,
            },
            depends_on=[triage_task.task_id],
            timeout=900,
        )

        # Phase 3: Fix implementation
        fix_task = self._create_task(
            task_id=f"{self.workflow_id}_fix",
            agent_type="Backend-Engineer",
            input_data={
                "action": "fix_bug",
                "bug_id": bug_id,
                "description": description,
                "affected_files": affected_files,
            },
            depends_on=[reproduce_task.task_id],
            timeout=1800,
        )

        # Phase 4: Verification testing
        verify_task = self._create_task(
            task_id=f"{self.workflow_id}_verify",
            agent_type="QA-Tester",
            input_data={
                "action": "verify_fix",
                "bug_id": bug_id,
                "test_types": ["regression", "unit"],
            },
            depends_on=[fix_task.task_id],
            timeout=900,
        )

        # Phase 5: Code review
        review_task = self._create_task(
            task_id=f"{self.workflow_id}_review",
            agent_type="Code-Reviewer",
            input_data={
                "action": "review_bug_fix",
                "bug_id": bug_id,
                "severity": severity,
                "review_focus": [
                    "correctness",
                    "side_effects",
                    "test_coverage",
                ],
            },
            depends_on=[verify_task.task_id],
            timeout=600,
        )

        workflow = Workflow(
            workflow_id=self.workflow_id,
            name=self.name,
            priority="high" if severity in ["high", "critical"] else "medium",
            tasks=[
                triage_task,
                reproduce_task,
                fix_task,
                verify_task,
                review_task,
            ],
        )

        return workflow


class WorkflowEngine:
    """
    Advanced workflow execution engine.

    Provides complex workflow patterns including sequential execution,
    parallel execution, conditional branching, dynamic task generation,
    and workflow state management with Redis.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        task_orchestrator: Optional[TaskOrchestrator] = None,
    ):
        """
        Initialize workflow engine.

        Args:
            redis_url: Redis connection URL for state storage
            task_orchestrator: TaskOrchestrator instance for task execution
        """
        self.redis_url = redis_url
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.orchestrator = task_orchestrator or TaskOrchestrator(redis_url)
        self.workflows: Dict[str, Workflow] = {}
        self.templates: Dict[str, WorkflowTemplate] = {
            "tdd": TDDWorkflow,
            "feature_development": FeatureDevelopmentWorkflow,
            "bug_fix": BugFixWorkflow,
        }

    def register_template(self, template_name: str, template_class: type) -> None:
        """
        Register a custom workflow template.

        Args:
            template_name: Name to register the template under
            template_class: WorkflowTemplate subclass
        """
        if not issubclass(template_class, WorkflowTemplate):
            raise ValueError("Template class must inherit from WorkflowTemplate")
        self.templates[template_name] = template_class

    def create_from_template(
        self, template_name: str, workflow_id: str, **params: Any
    ) -> Workflow:
        """
        Create a workflow from a template.

        Args:
            template_name: Name of the template to use
            workflow_id: Unique identifier for the workflow
            **params: Template-specific parameters

        Returns:
            Created workflow instance

        Raises:
            ValueError: If template not found
        """
        if template_name not in self.templates:
            raise ValueError(
                f"Template '{template_name}' not found. "
                f"Available templates: {list(self.templates.keys())}"
            )

        template_class = self.templates[template_name]
        template_name_display = params.get("name", f"{template_name}_workflow")
        template = template_class(workflow_id, template_name_display)
        workflow = template.create_workflow(**params)

        # Register workflow
        self.workflows[workflow_id] = workflow
        self._save_workflow_state(workflow)

        return workflow

    @flow(name="execute_sequential_tasks", task_runner=ConcurrentTaskRunner())
    def execute_sequential(
        self, tasks: List[Task], context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute tasks sequentially (one after another).

        Args:
            tasks: List of tasks to execute
            context: Execution context for passing data between tasks

        Returns:
            List of task results in execution order

        Raises:
            ValueError: If tasks list is empty
            RuntimeError: If task execution fails
        """
        if not tasks:
            raise ValueError("Tasks list cannot be empty")

        logger = get_run_logger()
        logger.info(f"Executing {len(tasks)} tasks sequentially")

        results = []
        execution_context = context or {}

        for idx, task in enumerate(tasks):
            logger.info(f"Executing task {idx + 1}/{len(tasks)}: {task.task_id}")

            try:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now(timezone.utc)

                # Pass previous results as context
                task.input_data["context"] = execution_context
                task.input_data["previous_results"] = results

                # Execute task
                result = self._execute_single_task(task)
                results.append(result)

                # Update execution context
                execution_context[task.task_id] = result

                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc)
                task.output = result

                logger.info(f"Task {task.task_id} completed successfully")

            except Exception as e:
                logger.error(f"Task {task.task_id} failed: {str(e)}")
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now(timezone.utc)
                raise RuntimeError(
                    f"Sequential execution failed at task " f"{task.task_id}: {str(e)}"
                ) from e

        return results

    @flow(name="execute_parallel_tasks", task_runner=ConcurrentTaskRunner())
    def execute_parallel(
        self, tasks: List[Task], context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute tasks in parallel (all simultaneously).

        Args:
            tasks: List of tasks to execute
            context: Execution context shared across tasks

        Returns:
            List of task results (order may vary)

        Raises:
            ValueError: If tasks list is empty
            RuntimeError: If any task execution fails
        """
        if not tasks:
            raise ValueError("Tasks list cannot be empty")

        logger = get_run_logger()
        logger.info(f"Executing {len(tasks)} tasks in parallel")

        execution_context = context or {}

        # Create Prefect tasks for parallel execution
        @prefect_task
        def execute_task_wrapper(task: Task) -> Dict[str, Any]:
            """Wrapper for parallel task execution."""
            try:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now(timezone.utc)

                # Add shared context
                task.input_data["context"] = execution_context

                # Execute task
                result = self._execute_single_task(task)

                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now(timezone.utc)
                task.output = result

                return result

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now(timezone.utc)
                raise

        # Submit all tasks for parallel execution
        futures = []
        for task in tasks:
            future = execute_task_wrapper.submit(task)
            futures.append(future)

        # Wait for all tasks to complete
        results = []
        for idx, future in enumerate(futures):
            try:
                result = future.result()
                results.append(result)
                logger.info(f"Parallel task {idx + 1} completed")
            except Exception as e:
                logger.error(f"Parallel task {idx + 1} failed: {str(e)}")
                raise RuntimeError(f"Parallel execution failed: {str(e)}") from e

        return results

    @flow(
        name="execute_conditional_tasks",
        task_runner=ConcurrentTaskRunner(),
    )
    def execute_conditional(
        self,
        condition: Union[str, ConditionalBranch],
        if_tasks: Optional[List[Task]] = None,
        else_tasks: Optional[List[Task]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute tasks based on conditional logic (if-then-else).

        Args:
            condition: Condition expression or ConditionalBranch model
            if_tasks: Tasks to execute if condition is true
            else_tasks: Tasks to execute if condition is false
            context: Execution context for condition evaluation

        Returns:
            Results from executed branch

        Raises:
            ValueError: If condition is invalid or tasks are missing
        """
        logger = get_run_logger()
        execution_context = context or {}

        # Parse condition
        if isinstance(condition, ConditionalBranch):
            condition_expr = condition.condition_expr
            if_tasks = if_tasks or condition.if_tasks
            else_tasks = else_tasks or condition.else_tasks
        elif isinstance(condition, str):
            condition_expr = condition
        else:
            raise ValueError(
                "Condition must be a string expression or ConditionalBranch"
            )

        if not if_tasks and not else_tasks:
            raise ValueError("At least one of if_tasks or else_tasks required")

        # Evaluate condition
        logger.info(f"Evaluating condition: {condition_expr}")
        condition_result = self.evaluate_condition(condition_expr, execution_context)
        logger.info(f"Condition evaluated to: {condition_result}")

        # Execute appropriate branch
        if condition_result:
            if if_tasks:
                logger.info(f"Executing {len(if_tasks)} tasks (IF branch)")
                return self.execute_sequential(if_tasks, execution_context)
            else:
                logger.info("No IF tasks defined, returning empty results")
                return []
        else:
            if else_tasks:
                logger.info(f"Executing {len(else_tasks)} tasks (ELSE branch)")
                return self.execute_sequential(else_tasks, execution_context)
            else:
                logger.info("No ELSE tasks defined, returning empty results")
                return []

    def evaluate_condition(self, condition_expr: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate a conditional expression.

        Supports operators: ==, !=, >, <, >=, <=, contains, in, and, or, not

        Args:
            condition_expr: Condition expression to evaluate
            context: Context containing variables for evaluation

        Returns:
            Boolean result of condition evaluation

        Raises:
            ValueError: If expression is invalid
            RuntimeError: If evaluation fails
        """
        if not condition_expr or not condition_expr.strip():
            raise ValueError("Condition expression cannot be empty")

        try:
            # Handle compound conditions (and, or)
            if " and " in condition_expr.lower():
                parts = re.split(r"\s+and\s+", condition_expr, flags=re.IGNORECASE)
                return all(
                    self.evaluate_condition(part.strip(), context) for part in parts
                )

            if " or " in condition_expr.lower():
                parts = re.split(r"\s+or\s+", condition_expr, flags=re.IGNORECASE)
                return any(
                    self.evaluate_condition(part.strip(), context) for part in parts
                )

            # Handle negation
            if condition_expr.strip().lower().startswith("not "):
                inner_expr = condition_expr.strip()[4:].strip()
                return not self.evaluate_condition(inner_expr, context)

            # Handle comparison operators
            operators = [
                (">=", lambda a, b: a >= b),
                ("<=", lambda a, b: a <= b),
                ("==", lambda a, b: a == b),
                ("!=", lambda a, b: a != b),
                (">", lambda a, b: a > b),
                ("<", lambda a, b: a < b),
            ]

            for op, func in operators:
                if op in condition_expr:
                    left, right = condition_expr.split(op, 1)
                    left_val = self._resolve_value(left.strip(), context)
                    right_val = self._resolve_value(right.strip(), context)
                    return func(left_val, right_val)

            # Handle 'contains' operator
            if " contains " in condition_expr.lower():
                parts = re.split(r"\s+contains\s+", condition_expr, flags=re.IGNORECASE)
                if len(parts) != 2:
                    raise ValueError("Invalid 'contains' expression")
                left_val = self._resolve_value(parts[0].strip(), context)
                right_val = self._resolve_value(parts[1].strip(), context)
                return right_val in str(left_val)

            # Handle 'in' operator
            if " in " in condition_expr.lower():
                parts = re.split(r"\s+in\s+", condition_expr, flags=re.IGNORECASE)
                if len(parts) != 2:
                    raise ValueError("Invalid 'in' expression")
                left_val = self._resolve_value(parts[0].strip(), context)
                right_val = self._resolve_value(parts[1].strip(), context)

                # Handle list/set membership
                if isinstance(right_val, (list, set, tuple)):
                    return left_val in right_val
                return left_val in str(right_val)

            # Handle boolean literals
            if condition_expr.strip().lower() == "true":
                return True
            if condition_expr.strip().lower() == "false":
                return False

            # Handle variable evaluation (treat as truthy check)
            value = self._resolve_value(condition_expr.strip(), context)
            return bool(value)

        except Exception as e:
            raise RuntimeError(
                f"Failed to evaluate condition '{condition_expr}': {str(e)}"
            ) from e

    def _resolve_value(self, expr: str, context: Dict[str, Any]) -> Any:
        """
        Resolve a value from expression or context.

        Args:
            expr: Expression to resolve
            context: Context for variable lookup

        Returns:
            Resolved value
        """
        # Remove quotes if present
        if (expr.startswith('"') and expr.endswith('"')) or (
            expr.startswith("'") and expr.endswith("'")
        ):
            return expr[1:-1]

        # Try to parse as number
        try:
            if "." in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass

        # Try to parse as boolean
        if expr.lower() == "true":
            return True
        if expr.lower() == "false":
            return False

        # Try to parse as None
        if expr.lower() == "none":
            return None

        # Try to parse as list
        if expr.startswith("[") and expr.endswith("]"):
            try:
                return json.loads(expr)
            except json.JSONDecodeError:
                pass

        # Resolve from context (support nested access with dot notation)
        if "." in expr:
            parts = expr.split(".")
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value

        # Simple context lookup
        return context.get(expr, expr)

    def generate_dynamic_tasks(
        self,
        generator_func: Callable[[Dict[str, Any]], List[Task]],
        context: Dict[str, Any],
    ) -> List[Task]:
        """
        Generate tasks dynamically based on runtime data.

        Args:
            generator_func: Function that generates tasks from context
            context: Execution context for task generation

        Returns:
            List of dynamically generated tasks

        Raises:
            ValueError: If generator function is invalid
            RuntimeError: If task generation fails
        """
        if not callable(generator_func):
            raise ValueError("Generator must be a callable function")

        try:
            tasks = generator_func(context)

            if not isinstance(tasks, list):
                raise ValueError("Generator must return a list of tasks")

            if not all(isinstance(t, Task) for t in tasks):
                raise ValueError("Generator must return Task instances")

            return tasks

        except Exception as e:
            raise RuntimeError(f"Failed to generate dynamic tasks: {str(e)}") from e

    def pause_workflow(self, workflow_id: str) -> bool:
        """
        Pause a running workflow.

        Args:
            workflow_id: Workflow ID to pause

        Returns:
            True if paused successfully

        Raises:
            ValueError: If workflow not found
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if workflow.status != WorkflowStatus.RUNNING:
            return False

        # Save current state to Redis
        state = {
            "workflow_id": workflow_id,
            "status": "paused",
            "paused_at": datetime.now(timezone.utc).isoformat(),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "status": t.status.value,
                    "output": t.output,
                }
                for t in workflow.tasks
            ],
        }

        self.redis_client.set(
            f"workflow:paused:{workflow_id}",
            json.dumps(state),
            ex=86400,  # 24 hour expiry
        )

        return True

    def resume_workflow(self, workflow_id: str) -> bool:
        """
        Resume a paused workflow.

        Args:
            workflow_id: Workflow ID to resume

        Returns:
            True if resumed successfully

        Raises:
            ValueError: If workflow not found or not paused
        """
        # Retrieve paused state from Redis
        state_key = f"workflow:paused:{workflow_id}"
        state_data = self.redis_client.get(state_key)

        if not state_data:
            raise ValueError(f"No paused state found for workflow {workflow_id}")

        state = json.loads(state_data)

        if state.get("status") != "paused":
            return False

        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Restore task states
        task_states = {t["task_id"]: t for t in state.get("tasks", [])}
        for task in workflow.tasks:
            if task.task_id in task_states:
                saved_state = task_states[task.task_id]
                task.status = TaskStatus(saved_state["status"])
                if saved_state.get("output"):
                    task.output = saved_state["output"]

        # Delete paused state
        self.redis_client.delete(state_key)

        return True

    def get_workflow_state(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get current state of a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow state information

        Raises:
            ValueError: If workflow not found
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            # Check if it's a paused workflow
            state_key = f"workflow:paused:{workflow_id}"
            state_data = self.redis_client.get(state_key)
            if state_data:
                return json.loads(state_data)
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
                    "output": t.output,
                    "error": t.error,
                }
                for t in workflow.tasks
            ],
        }

    def _execute_single_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a single task (delegates to orchestrator).

        Args:
            task: Task to execute

        Returns:
            Task execution result
        """
        # In production, this would delegate to the TaskOrchestrator
        # which routes to appropriate agents via DelegationManager
        return self.orchestrator._execute_task(task, {})

    def _save_workflow_state(self, workflow: Workflow) -> None:
        """
        Save workflow state to Redis.

        Args:
            workflow: Workflow to save
        """
        state = {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "priority": workflow.priority,
            "started_at": (
                workflow.started_at.isoformat() if workflow.started_at else None
            ),
            "completed_at": (
                workflow.completed_at.isoformat() if workflow.completed_at else None
            ),
            "tasks_completed": workflow.tasks_completed,
            "tasks_failed": workflow.tasks_failed,
        }

        self.redis_client.set(
            f"workflow:state:{workflow.workflow_id}",
            json.dumps(state),
            ex=86400,  # 24 hour expiry
        )

    def _load_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Load workflow state from Redis.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow state or None if not found
        """
        state_data = self.redis_client.get(f"workflow:state:{workflow_id}")
        if state_data:
            return json.loads(state_data)
        return None
