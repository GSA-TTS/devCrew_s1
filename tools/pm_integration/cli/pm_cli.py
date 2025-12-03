#!/usr/bin/env python3
"""
Project Management Integration Platform CLI.

Unified command-line interface for managing issues, sprints, and projects
across Jira, Linear, and GitHub Projects with bidirectional synchronization.

Commands:
    create      Create new issues across platforms
    update      Update existing issues
    sync        Synchronize issues between platforms
    sprint      Manage sprints and cycles
    report      Generate analytics reports
    triage      Classify and triage GitHub issues
    query       Search issues across platforms
    config      Manage configuration

Usage:
    pm-cli create --platform jira --title "Bug fix" --project PROJ
    pm-cli sync --source jira --target github --project PROJ
    pm-cli report --platform jira --sprint-id 123
    pm-cli triage --repo owner/repo --auto-label
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.syntax import Syntax
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analytics.sprint_analytics import SprintAnalytics
from classifier.issue_classifier import IssueClassifier
from integrations.github_client import GitHubPMClient
from integrations.jira_client import JiraClient
from integrations.linear_client import LinearClient
from sync.sync_engine import (
    FieldMapping,
    PlatformType,
    SyncConfiguration,
    SyncDirection,
    SyncEngine,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("pm-cli.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Rich console for formatted output
console = Console()


class ConfigManager:
    """Manage CLI configuration from YAML file."""

    DEFAULT_CONFIG_PATH = Path.home() / ".pm-cli" / "config.yaml"

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"Loaded config from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                self.config = {}
        else:
            logger.warning(f"Config file not found: {self.config_path}")

    def save(self) -> None:
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value


def get_jira_client(config: ConfigManager) -> Optional[JiraClient]:
    """
    Get configured Jira client.

    Args:
        config: Configuration manager

    Returns:
        JiraClient instance or None
    """
    jira_config = config.get("jira", {})
    if not jira_config.get("server"):
        console.print("[red]Jira not configured. Run 'pm-cli config' first.[/red]")
        return None

    try:
        return JiraClient(
            server=jira_config["server"],
            username=jira_config["username"],
            api_token=jira_config["api_token"],
            default_project=jira_config.get("default_project"),
        )
    except Exception as e:
        console.print(f"[red]Failed to connect to Jira: {e}[/red]")
        return None


def get_linear_client(config: ConfigManager) -> Optional[LinearClient]:
    """
    Get configured Linear client.

    Args:
        config: Configuration manager

    Returns:
        LinearClient instance or None
    """
    linear_config = config.get("linear", {})
    if not linear_config.get("api_key"):
        console.print("[red]Linear not configured. Run 'pm-cli config' first.[/red]")
        return None

    try:
        return LinearClient(
            api_key=linear_config["api_key"],
            default_team_id=linear_config.get("default_team_id"),
        )
    except Exception as e:
        console.print(f"[red]Failed to connect to Linear: {e}[/red]")
        return None


def get_github_client(
    config: ConfigManager,
) -> Optional[GitHubPMClient]:
    """
    Get configured GitHub client.

    Args:
        config: Configuration manager

    Returns:
        GitHubPMClient instance or None
    """
    github_config = config.get("github", {})
    if not github_config.get("token"):
        console.print("[red]GitHub not configured. Run 'pm-cli config' first.[/red]")
        return None

    try:
        return GitHubPMClient(
            token=github_config["token"],
            default_repo=github_config.get("default_repo"),
            default_project=github_config.get("default_project"),
        )
    except Exception as e:
        console.print(f"[red]Failed to connect to GitHub: {e}[/red]")
        return None


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.option("--json-output", is_flag=True, help="Output as JSON")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(
    ctx: click.Context,
    config: Optional[str],
    json_output: bool,
    verbose: bool,
) -> None:
    """Project Management Integration Platform CLI."""
    ctx.ensure_object(dict)

    # Load configuration
    config_path = Path(config) if config else None
    ctx.obj["config"] = ConfigManager(config_path)
    ctx.obj["json_output"] = json_output

    # Set logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["jira", "linear", "github"]),
    required=True,
    help="Target platform",
)
@click.option("--title", "-t", required=True, help="Issue title")
@click.option("--description", "-d", default="", help="Issue description")
@click.option("--project", help="Project/repository/team identifier")
@click.option("--type", "issue_type", default="Task", help="Issue type")
@click.option("--priority", default="Medium", help="Priority level")
@click.option("--labels", multiple=True, help="Labels (repeatable)")
@click.option("--assignee", help="Assignee username")
@click.pass_context
def create(
    ctx: click.Context,
    platform: str,
    title: str,
    description: str,
    project: Optional[str],
    issue_type: str,
    priority: str,
    labels: tuple,
    assignee: Optional[str],
) -> None:
    """Create a new issue on specified platform."""
    config_mgr = ctx.obj["config"]
    json_output = ctx.obj["json_output"]

    with console.status(f"[bold green]Creating issue on {platform}..."):
        result = None

        if platform == "jira":
            client = get_jira_client(config_mgr)
            if not client:
                sys.exit(1)

            result = client.create_issue(
                project=project,
                summary=title,
                description=description,
                issue_type=issue_type,
                priority=priority,
                labels=list(labels) if labels else None,
                assignee=assignee,
            )

        elif platform == "linear":
            client = get_linear_client(config_mgr)
            if not client:
                sys.exit(1)

            # Convert priority string to Linear priority number
            priority_map = {
                "urgent": 1,
                "high": 2,
                "medium": 3,
                "low": 4,
            }
            priority_num = priority_map.get(priority.lower(), 0)

            result = client.create_issue(
                team_id=project,
                title=title,
                description=description,
                priority=priority_num,
                assignee_id=assignee,
            )

        elif platform == "github":
            client = get_github_client(config_mgr)
            if not client:
                sys.exit(1)

            result = client.create_issue(
                repo=project,
                title=title,
                body=description,
                labels=list(labels) if labels else None,
                assignees=[assignee] if assignee else None,
            )

    if result:
        if json_output:
            console.print_json(data=result)
        else:
            console.print(
                Panel(
                    f"[green]✓[/green] Issue created successfully!\n\n"
                    f"[bold]ID:[/bold] {result.get('key') or result.get('identifier') or result.get('number')}\n"  # noqa: E501
                    f"[bold]Title:[/bold] {result.get('title') or result.get('summary')}\n"  # noqa: E501
                    f"[bold]URL:[/bold] {result.get('url')}",
                    title=f"{platform.capitalize()} Issue",
                    border_style="green",
                )
            )
    else:
        console.print("[red]✗ Failed to create issue[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["jira", "linear", "github"]),
    required=True,
    help="Platform",
)
@click.option("--issue-id", "-i", required=True, help="Issue ID/key/number")
@click.option("--title", help="New title")
@click.option("--description", help="New description")
@click.option("--status", help="New status")
@click.option("--assignee", help="New assignee")
@click.option("--labels", multiple=True, help="New labels (repeatable)")
@click.pass_context
def update(
    ctx: click.Context,
    platform: str,
    issue_id: str,
    title: Optional[str],
    description: Optional[str],
    status: Optional[str],
    assignee: Optional[str],
    labels: tuple,
) -> None:
    """Update an existing issue."""
    config_mgr = ctx.obj["config"]

    with console.status(f"[bold green]Updating issue on {platform}..."):
        success = False

        if platform == "jira":
            client = get_jira_client(config_mgr)
            if not client:
                sys.exit(1)

            success = client.update_issue(
                issue_key=issue_id,
                summary=title,
                description=description,
                status=status,
                assignee=assignee,
                labels=list(labels) if labels else None,
            )

        elif platform == "linear":
            client = get_linear_client(config_mgr)
            if not client:
                sys.exit(1)

            success = client.update_issue(
                issue_id=issue_id,
                title=title,
                description=description,
                assignee_id=assignee,
            )

        elif platform == "github":
            client = get_github_client(config_mgr)
            if not client:
                sys.exit(1)

            success = client.update_issue(
                issue_number=int(issue_id),
                title=title,
                body=description,
                state=status,
                assignees=[assignee] if assignee else None,
                labels=list(labels) if labels else None,
            )

    if success:
        console.print(f"[green]✓ Issue {issue_id} updated successfully[/green]")
    else:
        console.print(f"[red]✗ Failed to update issue {issue_id}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--source",
    "-s",
    type=click.Choice(["jira", "linear", "github"]),
    required=True,
    help="Source platform",
)
@click.option(
    "--target",
    "-t",
    type=click.Choice(["jira", "linear", "github"]),
    required=True,
    help="Target platform",
)
@click.option("--project", help="Project/repository/team identifier")
@click.option("--dry-run", is_flag=True, help="Show what would be synced")
@click.option(
    "--direction",
    type=click.Choice(["one-way", "bidirectional"]),
    default="one-way",
    help="Sync direction",
)
@click.option(
    "--conflict-resolution",
    type=click.Choice(["source", "target", "newest", "manual"]),
    default="newest",
    help="Conflict resolution strategy",
)
@click.pass_context
def sync(
    ctx: click.Context,
    source: str,
    target: str,
    project: Optional[str],
    dry_run: bool,
    direction: str,
    conflict_resolution: str,
) -> None:
    """Synchronize issues between platforms."""
    config_mgr = ctx.obj["config"]
    json_output = ctx.obj["json_output"]

    # Initialize clients
    clients = {}
    for platform in [source, target]:
        if platform == "jira":
            clients[platform] = get_jira_client(config_mgr)
        elif platform == "linear":
            clients[platform] = get_linear_client(config_mgr)
        elif platform == "github":
            clients[platform] = get_github_client(config_mgr)

        if not clients[platform]:
            sys.exit(1)

    # Create sync configuration
    sync_config = SyncConfiguration(
        source_platform=PlatformType(source.upper()),
        target_platform=PlatformType(target.upper()),
        direction=(
            SyncDirection.BIDIRECTIONAL
            if direction == "bidirectional"
            else SyncDirection.ONE_WAY
        ),
        conflict_resolution=conflict_resolution,
        field_mappings=_load_field_mappings(config_mgr),
    )

    # Initialize sync engine
    sync_engine = SyncEngine(
        source_client=clients[source],
        target_client=clients[target],
        config=sync_config,
    )

    # Perform sync
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(f"Syncing from {source} to {target}...", total=100)

        try:
            results = sync_engine.sync_project(project_id=project, dry_run=dry_run)
            progress.update(task, completed=100)

            if json_output:
                console.print_json(data=results)
            else:
                _display_sync_results(results, dry_run)

        except Exception as e:
            console.print(f"[red]✗ Sync failed: {e}[/red]")
            logger.exception("Sync error")
            sys.exit(1)


@cli.command()
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["jira", "linear"]),
    required=True,
    help="Platform",
)
@click.option("--action", type=click.Choice(["list", "create", "close"]))
@click.option("--name", help="Sprint/cycle name")
@click.option("--board-id", type=int, help="Board ID (Jira)")
@click.option("--team-id", help="Team ID (Linear)")
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD)")
@click.option("--goal", help="Sprint goal")
@click.pass_context
def sprint(
    ctx: click.Context,
    platform: str,
    action: str,
    name: Optional[str],
    board_id: Optional[int],
    team_id: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    goal: Optional[str],
) -> None:
    """Manage sprints and cycles."""
    config_mgr = ctx.obj["config"]
    json_output = ctx.obj["json_output"]

    if platform == "jira":
        client = get_jira_client(config_mgr)
        if not client:
            sys.exit(1)

        if action == "list":
            if not board_id:
                console.print("[red]--board-id required for list[/red]")
                sys.exit(1)

            sprints = client.get_sprints(board_id)
            if json_output:
                console.print_json(data=sprints)
            else:
                _display_sprints_table(sprints)

        elif action == "create":
            if not board_id or not name:
                console.print("[red]--board-id and --name required[/red]")
                sys.exit(1)

            start = datetime.fromisoformat(start_date) if start_date else None
            end = datetime.fromisoformat(end_date) if end_date else None

            sprint_data = client.create_sprint(
                board_id=board_id,
                name=name,
                start_date=start,
                end_date=end,
                goal=goal,
            )

            if sprint_data:
                console.print(f"[green]✓ Sprint '{name}' created[/green]")
            else:
                console.print("[red]✗ Failed to create sprint[/red]")
                sys.exit(1)

    elif platform == "linear":
        client = get_linear_client(config_mgr)
        if not client:
            sys.exit(1)

        if action == "list":
            cycles = client.get_cycles(team_id)
            if json_output:
                console.print_json(data=cycles)
            else:
                _display_cycles_table(cycles)


@cli.command()
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["jira", "linear"]),
    required=True,
    help="Platform",
)
@click.option("--sprint-id", help="Sprint/cycle ID")
@click.option("--output", "-o", help="Output file path")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "html"]),
    default="table",
    help="Output format",
)
@click.pass_context
def report(
    ctx: click.Context,
    platform: str,
    sprint_id: Optional[str],
    output: Optional[str],
    output_format: str,
) -> None:
    """Generate analytics reports."""
    config_mgr = ctx.obj["config"]

    if platform == "jira":
        client = get_jira_client(config_mgr)
    elif platform == "linear":
        client = get_linear_client(config_mgr)
    else:
        console.print(f"[red]Unsupported platform: {platform}[/red]")
        sys.exit(1)

    if not client:
        sys.exit(1)

    analytics = SprintAnalytics(client)

    with console.status("[bold green]Generating report..."):
        if sprint_id:
            report_data = analytics.generate_sprint_report(sprint_id)
        else:
            # Generate overall metrics
            report_data = analytics.generate_summary_report()

    if output_format == "json" or output:
        output_path = (
            output or f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )  # noqa: E501
        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)
        console.print(f"[green]✓ Report saved to {output_path}[/green]")
    else:
        _display_report(report_data)


@cli.command()
@click.option("--repo", "-r", required=True, help="Repository (owner/repo)")
@click.option("--auto-label", is_flag=True, help="Automatically apply labels")
@click.option(
    "--threshold",
    type=float,
    default=0.7,
    help="Confidence threshold for auto-labeling",
)
@click.option(
    "--limit", type=int, default=50, help="Number of issues to process"
)  # noqa: E501
@click.pass_context
def triage(
    ctx: click.Context,
    repo: str,
    auto_label: bool,
    threshold: float,
    limit: int,
) -> None:
    """Classify and triage GitHub issues."""
    config_mgr = ctx.obj["config"]
    json_output = ctx.obj["json_output"]

    client = get_github_client(config_mgr)
    if not client:
        sys.exit(1)

    classifier = IssueClassifier()

    with console.status("[bold green]Fetching issues..."):
        issues = client.search_issues(repo=repo, state="open", limit=limit)

    if not issues:
        console.print("[yellow]No issues found[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Classifying issues...", total=len(issues))

        classifications = []
        for issue in issues:
            classification = classifier.classify_issue(
                title=issue["title"],
                body=issue["body"],
                labels=issue["labels"],
            )
            classification["issue_number"] = issue["number"]
            classifications.append(classification)

            if auto_label:
                # Apply labels if confidence is high enough
                max_confidence = max(
                    classification.get("confidence", {}).get("types", {}).values(),
                    default=0,
                )
                if max_confidence >= threshold:
                    new_labels = issue["labels"] + classification["suggested_labels"]
                    client.label_issue(
                        issue_number=issue["number"],
                        labels=new_labels,
                        repo=repo,
                    )

            progress.advance(task)

    # Generate triage report
    triage_report = classifier.generate_triage_report(issues)

    if json_output:
        console.print_json(data=triage_report)
    else:
        _display_triage_report(triage_report)


@cli.command()
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["jira", "linear", "github"]),
    required=True,
    help="Platform to query",
)
@click.option("--query", "-q", help="Search query/JQL")
@click.option("--status", help="Filter by status")
@click.option("--assignee", help="Filter by assignee")
@click.option("--labels", multiple=True, help="Filter by labels")
@click.option("--limit", type=int, default=50, help="Result limit")
@click.pass_context
def query(
    ctx: click.Context,
    platform: str,
    query: Optional[str],
    status: Optional[str],
    assignee: Optional[str],
    labels: tuple,
    limit: int,
) -> None:
    """Search issues across platforms."""
    config_mgr = ctx.obj["config"]
    json_output = ctx.obj["json_output"]

    if platform == "jira":
        client = get_jira_client(config_mgr)
        if not client:
            sys.exit(1)

        # Build JQL query
        if not query:
            jql_parts = []
            if status:
                jql_parts.append(f"status = '{status}'")
            if assignee:
                jql_parts.append(f"assignee = '{assignee}'")
            if labels:
                label_filter = " OR ".join([f"labels = '{label}'" for label in labels])
                jql_parts.append(f"({label_filter})")

            query = (
                " AND ".join(jql_parts) if jql_parts else "ORDER BY created DESC"
            )  # noqa: E501

        issues = client.search_issues(jql=query, max_results=limit)

    elif platform == "linear":
        client = get_linear_client(config_mgr)
        if not client:
            sys.exit(1)

        issues = client.search_issues(
            state_name=status, assignee_id=assignee, limit=limit
        )

    elif platform == "github":
        client = get_github_client(config_mgr)
        if not client:
            sys.exit(1)

        issues = client.search_issues(
            state=status or "open",
            assignee=assignee,
            labels=list(labels) if labels else None,
            limit=limit,
        )

    if json_output:
        console.print_json(data=issues)
    else:
        _display_issues_table(issues, platform)


@cli.command()
@click.option(
    "--action",
    type=click.Choice(["show", "set", "init"]),
    default="show",
    help="Configuration action",
)
@click.option("--key", help="Configuration key")
@click.option("--value", help="Configuration value")
@click.pass_context
def config(
    ctx: click.Context,
    action: str,
    key: Optional[str],
    value: Optional[str],
) -> None:
    """Manage configuration."""
    config_mgr = ctx.obj["config"]

    if action == "show":
        if key:
            val = config_mgr.get(key)
            console.print(f"{key}: {val}")
        else:
            syntax = Syntax(
                yaml.dump(config_mgr.config, default_flow_style=False),
                "yaml",
                theme="monokai",
            )
            console.print(syntax)

    elif action == "set":
        if not key or value is None:
            console.print("[red]Both --key and --value required[/red]")
            sys.exit(1)

        config_mgr.set(key, value)
        config_mgr.save()
        console.print(f"[green]✓ Set {key} = {value}[/green]")

    elif action == "init":
        _interactive_config(config_mgr)


def _interactive_config(config_mgr: ConfigManager) -> None:
    """Interactive configuration setup."""
    console.print(
        Panel(
            "[bold]Project Management Integration Platform[/bold]\n"
            "Configuration Setup",
            border_style="blue",
        )
    )

    # Jira configuration
    console.print("\n[bold cyan]Jira Configuration[/bold cyan]")
    jira_server = click.prompt("Jira server URL", default="")
    if jira_server:
        jira_user = click.prompt("Username/email")
        jira_token = click.prompt("API token", hide_input=True)
        jira_project = click.prompt("Default project key", default="")

        config_mgr.config["jira"] = {
            "server": jira_server,
            "username": jira_user,
            "api_token": jira_token,
            "default_project": jira_project,
        }

    # Linear configuration
    console.print("\n[bold cyan]Linear Configuration[/bold cyan]")
    linear_key = click.prompt("Linear API key", default="")
    if linear_key:
        linear_team = click.prompt("Default team ID", default="")

        config_mgr.config["linear"] = {
            "api_key": linear_key,
            "default_team_id": linear_team,
        }

    # GitHub configuration
    console.print("\n[bold cyan]GitHub Configuration[/bold cyan]")
    github_token = click.prompt("GitHub personal access token", default="")
    if github_token:
        github_repo = click.prompt(
            "Default repository (owner/repo)", default=""
        )  # noqa: E501

        config_mgr.config["github"] = {
            "token": github_token,
            "default_repo": github_repo,
        }

    config_mgr.save()
    console.print("\n[green]✓ Configuration saved successfully[/green]")


def _load_field_mappings(
    config_mgr: ConfigManager,
) -> List[FieldMapping]:
    """Load field mappings from configuration."""
    mappings_file = config_mgr.get("field_mappings_file")
    if mappings_file and Path(mappings_file).exists():
        with open(mappings_file, "r") as f:
            mappings_data = yaml.safe_load(f)
            return [
                FieldMapping(**mapping)
                for mapping in mappings_data.get("mappings", [])  # noqa: E501
            ]
    return []


def _display_sync_results(results: Dict[str, Any], dry_run: bool) -> None:
    """Display sync results in formatted table."""
    table = Table(title="Sync Results" + (" (Dry Run)" if dry_run else ""))
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="magenta")

    table.add_row("Total Items", str(results.get("total", 0)))
    table.add_row("Created", str(results.get("created", 0)))
    table.add_row("Updated", str(results.get("updated", 0)))
    table.add_row("Skipped", str(results.get("skipped", 0)))
    table.add_row("Conflicts", str(results.get("conflicts", 0)))
    table.add_row("Errors", str(results.get("errors", 0)))

    console.print(table)


def _display_sprints_table(sprints: List[Dict[str, Any]]) -> None:
    """Display sprints in formatted table."""
    table = Table(title="Sprints")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("State", style="yellow")
    table.add_column("Start Date")
    table.add_column("End Date")

    for sprint in sprints:
        table.add_row(
            str(sprint.get("id")),
            sprint.get("name", ""),
            sprint.get("state", ""),
            (
                sprint.get("start_date", "")[:10] if sprint.get("start_date") else ""
            ),  # noqa: E501
            sprint.get("end_date", "")[:10] if sprint.get("end_date") else "",
        )

    console.print(table)


def _display_cycles_table(cycles: List[Dict[str, Any]]) -> None:
    """Display Linear cycles in formatted table."""
    table = Table(title="Cycles")
    table.add_column("ID", style="cyan")
    table.add_column("Number", style="green")
    table.add_column("Name", style="yellow")
    table.add_column("Start Date")
    table.add_column("End Date")

    for cycle in cycles:
        table.add_row(
            cycle.get("id", ""),
            str(cycle.get("number", "")),
            cycle.get("name", ""),
            cycle.get("startsAt", "")[:10] if cycle.get("startsAt") else "",
            cycle.get("endsAt", "")[:10] if cycle.get("endsAt") else "",
        )

    console.print(table)


def _display_report(report_data: Dict[str, Any]) -> None:
    """Display analytics report."""
    console.print(
        Panel(
            f"[bold]Sprint Analytics Report[/bold]\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            border_style="blue",
        )
    )

    # Metrics table
    table = Table(title="Key Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in report_data.items():
        if not isinstance(value, (dict, list)):
            table.add_row(str(key).replace("_", " ").title(), str(value))

    console.print(table)


def _display_triage_report(report: Dict[str, Any]) -> None:
    """Display issue triage report."""
    summary = report.get("summary", {})

    console.print(
        Panel(
            f"[bold]Issue Triage Report[/bold]\n"
            f"Total Issues: {summary.get('total_issues', 0)}",
            border_style="blue",
        )
    )

    # Types table
    if summary.get("types"):
        table = Table(title="Issue Types")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="magenta")

        for type_name, count in summary["types"].items():
            table.add_row(type_name, str(count))

        console.print(table)

    # Priorities table
    if summary.get("priorities"):
        table = Table(title="Priorities")
        table.add_column("Priority", style="cyan")
        table.add_column("Count", style="magenta")

        for priority, count in summary["priorities"].items():
            table.add_row(priority, str(count))

        console.print(table)

    # Recommendations
    if report.get("recommendations"):
        console.print("\n[bold yellow]Recommendations:[/bold yellow]")
        for rec in report["recommendations"]:
            console.print(f"  • {rec}")


def _display_issues_table(issues: List[Dict[str, Any]], platform: str) -> None:
    """Display issues in formatted table."""
    table = Table(title=f"{platform.capitalize()} Issues")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Assignee")

    for issue in issues:
        issue_id = (
            issue.get("key") or issue.get("identifier") or str(issue.get("number"))
        )
        title = issue.get("title") or issue.get("summary")
        status = issue.get("status") or issue.get("state")
        assignee = issue.get("assignee", "Unassigned")

        # Truncate title if too long
        if title and len(title) > 50:
            title = title[:47] + "..."

        table.add_row(issue_id, title, status, assignee)

    console.print(table)


if __name__ == "__main__":
    cli()
