"""
Multi-Agent Orchestration Platform - CLI Interface.

Command-line interface for workflow management, agent coordination, task delegation,
and platform monitoring.

Issue #46: Multi-Agent Orchestration Platform - CLI Interface Component
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import redis
import yaml
from tabulate import tabulate

from delegation_manager import DelegationManager, TaskPriority, TaskRequest
from handoff_manager import HandoffManager
from resource_allocator import ResourceAllocator
# Import platform components
from task_orchestrator import TaskOrchestrator


# Configuration loading
def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or config file.

    Priority:
    1. Environment variables
    2. Config file at ~/.devcrew/config.yaml
    3. Default values

    Returns:
        Configuration dictionary
    """
    config = {
        "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
        "redis_db": int(os.getenv("REDIS_DB", "0")),
        "postgres_host": os.getenv("POSTGRES_HOST", "localhost"),
        "postgres_port": int(os.getenv("POSTGRES_PORT", "5432")),
        "postgres_db": os.getenv("POSTGRES_DB", "multi_agent_platform"),
        "postgres_user": os.getenv("POSTGRES_USER", "postgres"),
        "postgres_password": os.getenv("POSTGRES_PASSWORD", ""),
    }

    # Try loading from config file
    config_path = Path.home() / ".devcrew" / "config.yaml"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config.update(file_config)
        except Exception as e:
            click.echo(
                click.style(f"Warning: Failed to load config file: {e}", fg="yellow"),
                err=True,
            )

    return config


# Initialize platform components
def get_orchestrator(config: Dict[str, Any]) -> TaskOrchestrator:
    """Get TaskOrchestrator instance."""
    return TaskOrchestrator(redis_url=config["redis_url"])


def get_delegation_manager(config: Dict[str, Any]) -> DelegationManager:
    """Get DelegationManager instance."""
    return DelegationManager(
        redis_url=config["redis_url"],
        redis_db=config["redis_db"],
    )


def get_resource_allocator(config: Dict[str, Any]) -> ResourceAllocator:
    """Get ResourceAllocator instance."""
    return ResourceAllocator(redis_url=config["redis_url"])


def get_handoff_manager(config: Dict[str, Any]) -> HandoffManager:
    """Get HandoffManager instance."""
    redis_client = redis.from_url(
        config["redis_url"],
        db=config["redis_db"],
        decode_responses=True,
    )

    postgres_config = {
        "host": config["postgres_host"],
        "port": config["postgres_port"],
        "database": config["postgres_db"],
        "user": config["postgres_user"],
        "password": config["postgres_password"],
        "minconn": 1,
        "maxconn": 10,
    }

    return HandoffManager(
        redis_client=redis_client,
        postgres_config=postgres_config if config["postgres_password"] else None,
    )


# Output formatting utilities
def format_output(data: Any, output_format: str) -> str:
    """
    Format data for output.

    Args:
        data: Data to format
        output_format: Output format (json, yaml, table)

    Returns:
        Formatted string
    """
    if output_format == "json":
        return json.dumps(data, indent=2, default=str)
    elif output_format == "yaml":
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    else:
        return str(data)


def print_table(headers: List[str], rows: List[List[Any]]) -> None:
    """
    Print formatted table.

    Args:
        headers: Column headers
        rows: Table rows
    """
    click.echo(tabulate(rows, headers=headers, tablefmt="grid"))


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"


# Main CLI group
@click.group()
@click.version_option(version="1.0.0")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Multi-Agent Orchestration Platform CLI.

    Manage workflows, agents, tasks, and monitor platform health.
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config()


# Workflow commands group
@cli.group()
def workflow() -> None:
    """Manage workflows - create, start, monitor, and control execution."""
    pass


@workflow.command("create")
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to workflow definition file (YAML or JSON)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def workflow_create(ctx: click.Context, file_path: str, output: str) -> None:
    """Create a new workflow from definition file."""
    try:
        config = ctx.obj["config"]
        orchestrator = get_orchestrator(config)

        # Parse workflow definition
        workflow_obj = TaskOrchestrator.parse_workflow_definition(file_path)

        # Create workflow
        workflow_id = orchestrator.create_workflow(workflow_obj)

        if output == "table":
            click.echo(
                click.style("✓", fg="green")
                + f" Workflow created: {click.style(workflow_id, fg='cyan', bold=True)}"
            )
            click.echo(f"  Name: {workflow_obj.name}")
            click.echo(f"  Tasks: {len(workflow_obj.tasks)}")
            click.echo(f"  Priority: {workflow_obj.priority}")
        else:
            result = {
                "status": "success",
                "workflow_id": workflow_id,
                "name": workflow_obj.name,
                "tasks_count": len(workflow_obj.tasks),
            }
            click.echo(format_output(result, output))

    except FileNotFoundError as e:
        click.echo(click.style(f"Error: File not found - {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to create workflow - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


@workflow.command("start")
@click.option(
    "--workflow-id",
    "-w",
    required=True,
    help="Workflow ID to start",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def workflow_start(ctx: click.Context, workflow_id: str, output: str) -> None:
    """Start workflow execution."""
    try:
        config = ctx.obj["config"]
        orchestrator = get_orchestrator(config)

        if output == "table":
            click.echo(f"Starting workflow: {click.style(workflow_id, fg='cyan')}")
            with click.progressbar(length=100, label="Initializing workflow") as bar:
                # Execute workflow
                result = orchestrator.execute_workflow(workflow_id)
                bar.update(100)

            click.echo(
                click.style("\n✓", fg="green") + " Workflow started successfully"
            )
            click.echo(f"  Status: {result['status']}")
            click.echo(f"  Tasks completed: {result['tasks_completed']}")
            click.echo(f"  Tasks failed: {result['tasks_failed']}")

            if result.get("duration_seconds"):
                click.echo(f"  Duration: {format_duration(result['duration_seconds'])}")
        else:
            result = orchestrator.execute_workflow(workflow_id)
            click.echo(format_output(result, output))

    except ValueError as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to start workflow - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


@workflow.command("status")
@click.option(
    "--workflow-id",
    "-w",
    required=True,
    help="Workflow ID to check status",
)
@click.option(
    "--watch",
    is_flag=True,
    help="Watch workflow status in real-time",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def workflow_status(
    ctx: click.Context, workflow_id: str, watch: bool, output: str
) -> None:
    """Show workflow status and task details."""
    try:
        config = ctx.obj["config"]
        orchestrator = get_orchestrator(config)

        if watch:
            # Watch mode - update every 2 seconds
            try:
                while True:
                    click.clear()
                    status = orchestrator.get_workflow_status(workflow_id)
                    _display_workflow_status(status, output)

                    # Stop watching if workflow is complete
                    if status["status"] in ["completed", "failed", "cancelled"]:
                        break

                    time.sleep(2)
            except KeyboardInterrupt:
                click.echo("\nStopped watching workflow")
        else:
            # Single status check
            status = orchestrator.get_workflow_status(workflow_id)
            _display_workflow_status(status, output)

    except ValueError as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to get workflow status - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


def _display_workflow_status(status: Dict[str, Any], output: str) -> None:
    """
    Display workflow status in requested format.

    Args:
        status: Workflow status dictionary
        output: Output format (json, yaml, table)
    """
    if output == "table":
        workflow_id_styled = click.style(status["workflow_id"], fg="cyan", bold=True)
        click.echo(f"Workflow: {workflow_id_styled}")
        click.echo(f"Name: {status['name']}")

        # Status with color
        status_color = {
            "pending": "yellow",
            "running": "blue",
            "completed": "green",
            "failed": "red",
            "cancelled": "magenta",
        }
        status_styled = click.style(
            status["status"], fg=status_color.get(status["status"], "white")
        )
        click.echo(f"Status: {status_styled}")

        # Progress
        total_tasks = status["total_tasks"]
        completed = status["tasks_completed"]
        failed = status["tasks_failed"]
        click.echo(
            f"Progress: {completed}/{total_tasks} tasks completed"
            + (f" ({failed} failed)" if failed > 0 else "")
        )

        # Tasks table
        if status.get("tasks"):
            click.echo("\nTasks:")
            headers = ["Task ID", "Type", "Status", "Duration"]
            rows = []

            for task in status["tasks"]:
                task_status = task["status"]
                status_emoji = {
                    "pending": "⏳",
                    "running": "🔄",
                    "completed": "✅",
                    "failed": "❌",
                    "cancelled": "🚫",
                }

                # Calculate duration
                duration = ""
                if task.get("started_at"):
                    started = datetime.fromisoformat(task["started_at"])
                    if task.get("completed_at"):
                        completed_dt = datetime.fromisoformat(task["completed_at"])
                        duration = format_duration(
                            (completed_dt - started).total_seconds()
                        )
                    elif task_status == "running":
                        now = datetime.now(timezone.utc)
                        elapsed = (now - started).total_seconds()
                        duration = f"running for {format_duration(elapsed)}"

                rows.append(
                    [
                        f"{status_emoji.get(task_status, '')} {task['task_id']}",
                        task["agent_type"],
                        task_status,
                        duration,
                    ]
                )

            print_table(headers, rows)
    else:
        click.echo(format_output(status, output))


@workflow.command("cancel")
@click.option(
    "--workflow-id",
    "-w",
    required=True,
    help="Workflow ID to cancel",
)
@click.pass_context
def workflow_cancel(ctx: click.Context, workflow_id: str) -> None:
    """Cancel a running workflow."""
    try:
        config = ctx.obj["config"]
        orchestrator = get_orchestrator(config)

        # Confirm cancellation
        confirm_msg = f"Are you sure you want to cancel workflow {workflow_id}?"
        if not click.confirm(confirm_msg):
            click.echo("Cancelled")
            return

        success = orchestrator.cancel_workflow(workflow_id)

        if success:
            workflow_id_styled = click.style(workflow_id, fg="cyan")
            click.echo(
                click.style("✓", fg="green")
                + f" Workflow {workflow_id_styled} cancelled"
            )
        else:
            msg = f" Workflow {workflow_id} could not be cancelled " "(not running)"
            click.echo(click.style("✗", fg="red") + msg)
            sys.exit(1)

    except ValueError as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to cancel workflow - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


@workflow.command("list")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def workflow_list(ctx: click.Context, output: str) -> None:
    """List all workflows."""
    try:
        config = ctx.obj["config"]
        orchestrator = get_orchestrator(config)

        # Get all workflows
        workflows = orchestrator.workflows

        if output == "table":
            if not workflows:
                click.echo("No workflows found")
                return

            headers = ["Workflow ID", "Name", "Status", "Tasks", "Progress"]
            rows = []

            for workflow_id, workflow_obj in workflows.items():
                total = len(workflow_obj.tasks)
                completed = workflow_obj.tasks_completed
                progress = f"{completed}/{total}" if total > 0 else "0/0"

                rows.append(
                    [
                        workflow_id,
                        workflow_obj.name,
                        workflow_obj.status.value,
                        total,
                        progress,
                    ]
                )

            print_table(headers, rows)
        else:
            workflow_data = {
                wf_id: {
                    "workflow_id": wf_id,
                    "name": wf.name,
                    "status": wf.status.value,
                    "total_tasks": len(wf.tasks),
                    "tasks_completed": wf.tasks_completed,
                    "tasks_failed": wf.tasks_failed,
                }
                for wf_id, wf in workflows.items()
            }
            click.echo(format_output(workflow_data, output))

    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to list workflows - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


# Agent commands group
@cli.group()
def agent() -> None:
    """Manage agents - register, list, and control availability."""
    pass


@agent.command("register")
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to agent configuration file (JSON or YAML)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def agent_register(ctx: click.Context, file_path: str, output: str) -> None:
    """Register an agent from configuration file."""
    try:
        config = ctx.obj["config"]
        delegation_manager = get_delegation_manager(config)

        # Load agent configuration
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                agent_config = yaml.safe_load(f)
            else:
                agent_config = json.load(f)

        # Register agent
        success = delegation_manager.register_agent(
            agent_id=agent_config["agent_id"],
            agent_type=agent_config["agent_type"],
            capabilities=agent_config["capabilities"],
            max_concurrent_tasks=agent_config.get("max_concurrent_tasks", 3),
            priority_weight=agent_config.get("priority_weight", 10),
            available=agent_config.get("available", True),
        )

        if success:
            if output == "table":
                agent_id_styled = click.style(
                    agent_config["agent_id"], fg="cyan", bold=True
                )
                click.echo(
                    click.style("✓", fg="green")
                    + f" Agent registered: {agent_id_styled}"
                )
                click.echo(f"  Type: {agent_config['agent_type']}")
                caps_str = ", ".join(agent_config["capabilities"])
                click.echo(f"  Capabilities: {caps_str}")
            else:
                result = {
                    "status": "success",
                    "agent_id": agent_config["agent_id"],
                    "agent_type": agent_config["agent_type"],
                    "capabilities": agent_config["capabilities"],
                }
                click.echo(format_output(result, output))
        else:
            click.echo(click.style("✗ Agent registration failed", fg="red"), err=True)
            sys.exit(1)

    except FileNotFoundError as e:
        click.echo(click.style(f"Error: File not found - {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to register agent - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


@agent.command("list")
@click.option(
    "--filter",
    "-f",
    "filter_expr",
    help="Filter expression (e.g., 'type=backend-engineer')",
)
@click.option(
    "--available",
    is_flag=True,
    help="Show only available agents",
)
@click.option(
    "--capacity",
    is_flag=True,
    help="Show only agents with available capacity",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def agent_list(
    ctx: click.Context,
    filter_expr: Optional[str],
    available: bool,
    capacity: bool,
    output: str,
) -> None:
    """List registered agents with optional filters."""
    try:
        config = ctx.obj["config"]
        delegation_manager = get_delegation_manager(config)

        # Parse filter
        filter_type = None
        if filter_expr:
            if "=" in filter_expr:
                key, value = filter_expr.split("=", 1)
                if key == "type":
                    filter_type = value

        # List agents
        agents = delegation_manager.list_agents(
            filter_type=filter_type,
            available_only=available,
            has_capacity=capacity,
        )

        if output == "table":
            if not agents:
                click.echo("No agents found")
                return

            headers = ["Agent ID", "Type", "Capabilities", "Load", "Status"]
            rows = []

            for agent_data in agents:
                status_emoji = "✅" if agent_data["available"] else "❌"
                load_str = (
                    f"{agent_data['current_load']}/"
                    f"{agent_data['max_concurrent_tasks']}"
                )

                caps = agent_data["capabilities"][:3]
                caps_str = ", ".join(caps)
                if len(agent_data["capabilities"]) > 3:
                    caps_str += "..."

                avail_text = "Available" if agent_data["available"] else "Unavailable"

                rows.append(
                    [
                        agent_data["agent_id"],
                        agent_data["agent_type"],
                        caps_str,
                        load_str,
                        f"{status_emoji} {avail_text}",
                    ]
                )

            print_table(headers, rows)
            click.echo(f"\nTotal agents: {len(agents)}")
        else:
            click.echo(format_output(agents, output))

    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to list agents - {e}", fg="red"), err=True
        )
        sys.exit(1)


@agent.command("status")
@click.option(
    "--agent-id",
    "-a",
    required=True,
    help="Agent ID to check status",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def agent_status(ctx: click.Context, agent_id: str, output: str) -> None:
    """Show detailed agent status."""
    try:
        config = ctx.obj["config"]
        delegation_manager = get_delegation_manager(config)

        status = delegation_manager.get_agent_status(agent_id)

        if not status:
            click.echo(click.style(f"Error: Agent {agent_id} not found", fg="red"))
            sys.exit(1)

        if output == "table":
            agent_id_styled = click.style(status["agent_id"], fg="cyan", bold=True)
            click.echo(f"Agent: {agent_id_styled}")
            click.echo(f"Type: {status['agent_type']}")
            click.echo(f"Capabilities: {', '.join(status['capabilities'])}")

            avail_text = "Available" if status["available"] else "Unavailable"
            avail_color = "green" if status["available"] else "red"
            status_styled = click.style(avail_text, fg=avail_color)
            click.echo(f"Status: {status_styled}")

            load_info = (
                f"Load: {status['current_load']}/"
                f"{status['max_concurrent_tasks']} "
                f"({status['load_percentage']:.1f}%)"
            )
            click.echo(load_info)
            click.echo(f"Has Capacity: {'Yes' if status['has_capacity'] else 'No'}")
            click.echo(f"Priority Weight: {status['priority_weight']}")
            click.echo(f"TTL: {status['ttl_seconds']}s")
        else:
            click.echo(format_output(status, output))

    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to get agent status - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


@agent.command("disable")
@click.option(
    "--agent-id",
    "-a",
    required=True,
    help="Agent ID to disable",
)
@click.pass_context
def agent_disable(ctx: click.Context, agent_id: str) -> None:
    """Disable an agent."""
    try:
        config = ctx.obj["config"]
        delegation_manager = get_delegation_manager(config)

        success = delegation_manager.set_agent_availability(agent_id, False)

        if success:
            agent_id_styled = click.style(agent_id, fg="cyan")
            click.echo(
                click.style("✓", fg="green") + f" Agent {agent_id_styled} disabled"
            )
        else:
            click.echo(click.style(f"✗ Agent {agent_id} not found", fg="red"), err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to disable agent - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


@agent.command("enable")
@click.option(
    "--agent-id",
    "-a",
    required=True,
    help="Agent ID to enable",
)
@click.pass_context
def agent_enable(ctx: click.Context, agent_id: str) -> None:
    """Enable an agent."""
    try:
        config = ctx.obj["config"]
        delegation_manager = get_delegation_manager(config)

        success = delegation_manager.set_agent_availability(agent_id, True)

        if success:
            agent_id_styled = click.style(agent_id, fg="cyan")
            click.echo(
                click.style("✓", fg="green") + f" Agent {agent_id_styled} enabled"
            )
        else:
            click.echo(click.style(f"✗ Agent {agent_id} not found", fg="red"), err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to enable agent - {e}", fg="red"), err=True
        )
        sys.exit(1)


@agent.command("heartbeat")
@click.option(
    "--agent-id",
    "-a",
    required=True,
    help="Agent ID to send heartbeat",
)
@click.pass_context
def agent_heartbeat(ctx: click.Context, agent_id: str) -> None:
    """Send heartbeat for an agent to refresh TTL."""
    try:
        config = ctx.obj["config"]
        delegation_manager = get_delegation_manager(config)

        success = delegation_manager.heartbeat_agent(agent_id)

        if success:
            agent_id_styled = click.style(agent_id, fg="cyan")
            click.echo(
                click.style("✓", fg="green")
                + f" Heartbeat sent for agent {agent_id_styled}"
            )
        else:
            click.echo(click.style(f"✗ Agent {agent_id} not found", fg="red"), err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to send heartbeat - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


# Task commands group
@cli.group()
def task() -> None:
    """Manage tasks - delegate, monitor, and control execution."""
    pass


@task.command("delegate")
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to task request file (JSON or YAML)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def task_delegate(ctx: click.Context, file_path: str, output: str) -> None:
    """Delegate a task to the best available agent."""
    try:
        config = ctx.obj["config"]
        delegation_manager = get_delegation_manager(config)

        # Load task request
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                task_data = yaml.safe_load(f)
            else:
                task_data = json.load(f)

        # Create task request
        task_request = TaskRequest(
            task_id=task_data["task_id"],
            task_type=task_data["task_type"],
            required_capabilities=task_data["required_capabilities"],
            priority=TaskPriority(task_data.get("priority", "medium")),
            estimated_duration=task_data.get("estimated_duration", 600),
            context=task_data.get("context", {}),
            timeout=task_data.get("timeout", 3600),
        )

        # Find best agent
        agent_match = delegation_manager.find_best_agent(task_request)

        if not agent_match:
            click.echo(
                click.style("✗ No suitable agent found for task", fg="red"),
                err=True,
            )
            sys.exit(1)

        # Delegate task
        delegation_result = delegation_manager.delegate_task(task_request, agent_match)

        if output == "table":
            task_id_styled = click.style(task_request.task_id, fg="cyan", bold=True)
            click.echo(
                click.style("✓", fg="green") + f" Task delegated: {task_id_styled}"
            )
            click.echo(f"  Agent: {delegation_result['agent_id']}")
            click.echo(f"  Agent Type: {delegation_result['agent_type']}")
            click.echo(f"  Match Score: {delegation_result['match_score']:.3f}")
            load_info = (
                f"  Agent Load: {delegation_result['agent_load']}/"
                f"{delegation_result['max_load']}"
            )
            click.echo(load_info)
        else:
            click.echo(format_output(delegation_result, output))

    except FileNotFoundError as e:
        click.echo(click.style(f"Error: File not found - {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to delegate task - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


@task.command("complete")
@click.option(
    "--task-id",
    "-t",
    required=True,
    help="Task ID to mark as complete",
)
@click.option(
    "--agent-id",
    "-a",
    required=True,
    help="Agent ID that executed the task",
)
@click.pass_context
def task_complete(ctx: click.Context, task_id: str, agent_id: str) -> None:
    """Mark a task as completed and release resources."""
    try:
        config = ctx.obj["config"]
        delegation_manager = get_delegation_manager(config)

        success = delegation_manager.complete_task(agent_id, task_id)

        if success:
            task_id_styled = click.style(task_id, fg="cyan")
            click.echo(
                click.style("✓", fg="green")
                + f" Task {task_id_styled} marked as complete"
            )
        else:
            click.echo(click.style("✗ Task completion failed", fg="red"), err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to complete task - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


# Monitoring commands group
@cli.group()
def monitor() -> None:
    """Monitor platform health and performance metrics."""
    pass


@monitor.command("metrics")
@click.option(
    "--workflow-id",
    "-w",
    help="Workflow ID to get metrics (optional)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def metrics(ctx: click.Context, workflow_id: Optional[str], output: str) -> None:
    """Show platform or workflow metrics."""
    try:
        config = ctx.obj["config"]
        delegation_manager = get_delegation_manager(config)

        if workflow_id:
            # Get workflow-specific metrics
            orchestrator = get_orchestrator(config)
            status = orchestrator.get_workflow_status(workflow_id)

            if output == "table":
                workflow_id_styled = click.style(workflow_id, fg="cyan", bold=True)
                click.echo(f"Metrics for workflow: {workflow_id_styled}")
                click.echo(f"Status: {status['status']}")
                click.echo(f"Total Tasks: {status['total_tasks']}")
                click.echo(f"Completed: {status['tasks_completed']}")
                click.echo(f"Failed: {status['tasks_failed']}")

                if status.get("started_at"):
                    click.echo(f"Started: {status['started_at']}")
                if status.get("completed_at"):
                    click.echo(f"Completed: {status['completed_at']}")
            else:
                click.echo(format_output(status, output))
        else:
            # Get platform-wide metrics
            stats = delegation_manager.get_statistics()

            if output == "table":
                click.echo(click.style("Platform Metrics", fg="cyan", bold=True))
                click.echo(f"Total Agents: {stats['total_agents']}")
                click.echo(f"Available Agents: {stats['available_agents']}")
                click.echo(f"Agents with Capacity: {stats['agents_with_capacity']}")
                click.echo(f"Active Tasks: {stats['total_active_tasks']}")
                click.echo(f"Max Capacity: {stats['max_capacity']}")
                click.echo(
                    f"Capacity Utilization: {stats['capacity_utilization']:.1f}%"
                )
                click.echo(f"Average Load: {stats['average_load_percentage']:.1f}%")

                if stats.get("agents_by_type"):
                    click.echo("\nAgents by Type:")
                    for agent_type, count in stats["agents_by_type"].items():
                        click.echo(f"  {agent_type}: {count}")
            else:
                click.echo(format_output(stats, output))

    except ValueError as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(
            click.style(f"Error: Failed to get metrics - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


@monitor.command("health-check")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "yaml", "table"]),
    default="table",
    help="Output format",
)
@click.pass_context
def health_check(ctx: click.Context, output: str) -> None:
    """Check platform health status."""
    try:
        config = ctx.obj["config"]
        health = {"redis": False, "postgres": False, "platform": "unhealthy"}

        # Check Redis
        try:
            redis_client = redis.from_url(
                config["redis_url"],
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            redis_client.ping()
            health["redis"] = True
            redis_client.close()
        except Exception:
            pass

        # Check PostgreSQL (if configured)
        if config.get("postgres_password"):
            try:
                import psycopg2

                conn = psycopg2.connect(
                    host=config["postgres_host"],
                    port=config["postgres_port"],
                    database=config["postgres_db"],
                    user=config["postgres_user"],
                    password=config["postgres_password"],
                    connect_timeout=5,
                )
                conn.close()
                health["postgres"] = True
            except Exception:
                pass

        # Overall health
        if health["redis"]:
            health["platform"] = "healthy"

        if output == "table":
            click.echo(click.style("Platform Health Check", fg="cyan", bold=True))
            redis_status = "✓ Connected" if health["redis"] else "✗ Disconnected"
            redis_color = "green" if health["redis"] else "red"
            redis_styled = click.style(redis_status, fg=redis_color)
            click.echo(f"Redis: {redis_styled}")

            if config.get("postgres_password"):
                pg_status = "✓ Connected" if health["postgres"] else "✗ Disconnected"
                pg_color = "green" if health["postgres"] else "red"
                pg_styled = click.style(pg_status, fg=pg_color)
                click.echo(f"PostgreSQL: {pg_styled}")
            else:
                click.echo("PostgreSQL: Not configured")

            status_text = health["platform"].upper()
            status_color = "green" if health["platform"] == "healthy" else "red"
            status_styled = click.style(status_text, fg=status_color, bold=True)
            click.echo(f"\nOverall Status: {status_styled}")
        else:
            click.echo(format_output(health, output))

        # Exit with error code if unhealthy
        if health["platform"] != "healthy":
            sys.exit(1)

    except Exception as e:
        click.echo(
            click.style(f"Error: Health check failed - {e}", fg="red"),
            err=True,
        )
        sys.exit(1)


@monitor.command("dashboard")
@click.pass_context
def dashboard(ctx: click.Context) -> None:
    """Display the web dashboard URL for platform monitoring."""
    config = ctx.obj["config"]

    # Extract host and port from Redis URL for dashboard
    redis_url = config["redis_url"]
    if "://" in redis_url:
        host_part = redis_url.split("://")[1].split("/")[0]
        if ":" in host_part:
            host = host_part.split(":")[0]
        else:
            host = host_part
    else:
        host = "localhost"

    dashboard_url = f"http://{host}:8080/dashboard"

    title = "Multi-Agent Orchestration Platform Dashboard"
    click.echo(click.style(title, fg="cyan", bold=True))

    url_styled = click.style(dashboard_url, fg="blue", underline=True)
    click.echo(f"\nDashboard URL: {url_styled}")
    click.echo("\nNote: Ensure the dashboard service is running")
    click.echo("Start with: docker-compose up dashboard")


# Main entry point
def main() -> None:
    """Execute the main CLI entry point."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(
            click.style(f"\nUnexpected error: {e}", fg="red", bold=True),
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
