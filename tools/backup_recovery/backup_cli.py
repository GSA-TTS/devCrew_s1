"""
Comprehensive CLI for Backup & Recovery Management Platform.

This module provides a command-line interface for managing backups, restores,
disaster recovery drills, and compliance reporting. Built with Click for an
intuitive user experience with rich output formatting.

Protocol Integration:
- P-SYSTEM-BACKUP: System backup operations
- P-BACKUP-VALIDATION: Backup validation and integrity checks
- P-RES-DR-DRILL: Disaster recovery drill execution
- P-OPS-RESILIENCE: Operational resilience management
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.tree import Tree

# Import local modules (will be created alongside)
try:
    from backup_manager import BackupManager
    from dr_drill import ComplianceReporter, DRDrill, DrillConfig
    from recovery_manager import RecoveryManager
    from scheduler import BackupScheduler
    from storage_adapter import StorageAdapter
    from validator import BackupValidator
except ImportError:
    # Graceful handling if modules not yet available
    BackupManager = None
    RecoveryManager = None
    BackupValidator = None
    DRDrill = None
    ComplianceReporter = None
    BackupScheduler = None
    StorageAdapter = None

console = Console()
logger = logging.getLogger(__name__)


class Config:
    """Global CLI configuration."""

    def __init__(self) -> None:
        """Initialize CLI configuration."""
        self.verbose = False
        self.debug = False
        self.json_output = False
        self.config_file: Optional[Path] = None
        self.backend: Optional[str] = None
        self.password_file: Optional[str] = None


pass_config = click.make_pass_decorator(Config, ensure=True)


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    """Setup logging configuration.

    Args:
        verbose: Enable verbose output
        debug: Enable debug output
    """
    level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def handle_error(message: str, exit_code: int = 1) -> None:
    """Handle and display error message.

    Args:
        message: Error message to display
        exit_code: Exit code (default: 1)
    """
    console.print(f"[red bold]Error:[/red bold] {message}")
    sys.exit(exit_code)


def format_size(bytes_size: int) -> str:
    """Format byte size to human-readable format.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def confirm_action(message: str, default: bool = False) -> bool:
    """Prompt user for confirmation.

    Args:
        message: Confirmation message
        default: Default response

    Returns:
        True if confirmed
    """
    return click.confirm(message, default=default)


@click.group()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug output",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output results in JSON format",
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@pass_config
def cli(
    config: Config,
    verbose: bool,
    debug: bool,
    json_output: bool,
    config_path: Optional[Path],
) -> None:
    """Backup & Recovery Management CLI.

    Comprehensive backup management with support for S3, Azure, GCS, and local
    storage. Includes disaster recovery drills, compliance reporting, and
    automated scheduling.
    """
    config.verbose = verbose
    config.debug = debug
    config.json_output = json_output
    config.config_file = config_path
    setup_logging(verbose, debug)


@cli.command()
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI (s3://bucket/path, azure://container, gs://bucket, /local/path)",  # noqa: E501
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@click.option(
    "--encryption",
    "-e",
    default="AES256",
    help="Encryption algorithm (default: AES256)",
)
@pass_config
def init(
    config: Config,
    backend: str,
    password_file: Optional[str],
    encryption: str,
) -> None:
    """Initialize backup repository.

    Creates a new backup repository at the specified backend location with
    encryption enabled. Supports S3, Azure, GCS, and local backends.

    Examples:
        backup-cli init -b s3://my-bucket/backups -p ~/.restic-pw
        backup-cli init -b /mnt/backup -p ~/.restic-pw
    """
    if not BackupManager:
        handle_error("BackupManager module not available")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing repository...", total=None)

            manager = BackupManager(backend, password_file, encryption=encryption)
            result = manager.init_repository()

            progress.update(task, completed=True)

        if config.json_output:
            console.print_json(data=result)
        else:
            console.print(
                Panel(
                    f"[green]Repository initialized successfully![/green]\n\n"
                    f"Backend: {backend}\n"
                    f"Encryption: {encryption}\n"
                    f"Repository ID: {result.get('repository_id', 'N/A')}",
                    title="Initialization Complete",
                    border_style="green",
                )
            )

    except Exception as e:
        handle_error(f"Failed to initialize repository: {e}")


@cli.command()
@click.option(
    "--source",
    "-s",
    required=True,
    multiple=True,
    help="Source path(s) to backup (can specify multiple)",
)
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI",
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@click.option(
    "--tags",
    "-t",
    multiple=True,
    help="Tags to apply to backup (can specify multiple)",
)
@click.option(
    "--exclude",
    "-x",
    multiple=True,
    help="Patterns to exclude from backup",
)
@click.option(
    "--exclude-file",
    type=click.Path(exists=True),
    help="File containing exclude patterns",
)
@pass_config
def create(
    config: Config,
    source: tuple,
    backend: str,
    password_file: Optional[str],
    tags: tuple,
    exclude: tuple,
    exclude_file: Optional[str],
) -> None:
    """Create new backup snapshot.

    Creates a new backup snapshot from specified source paths. Supports
    multiple sources, tags for organization, and exclusion patterns.

    Examples:
        backup-cli create -s /data -b s3://bucket/backups -t daily
        backup-cli create -s /app -s /config -b azure://container -x "*.tmp"
    """
    if not BackupManager:
        handle_error("BackupManager module not available")

    try:
        manager = BackupManager(backend, password_file)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Creating backup...", total=100)

            result = manager.create_backup(
                sources=list(source),
                tags=list(tags),
                exclude=list(exclude),
                exclude_file=exclude_file,
                progress_callback=lambda pct: progress.update(task, completed=pct),
            )

            progress.update(task, completed=100)

        if config.json_output:
            console.print_json(data=result)
        else:
            console.print(
                Panel(
                    f"[green]Backup created successfully![/green]\n\n"
                    f"Snapshot ID: {result.get('snapshot_id', 'N/A')}\n"
                    f"Files: {result.get('files_new', 0):,} new, "
                    f"{result.get('files_changed', 0):,} changed\n"
                    f"Data Added: {format_size(result.get('data_added', 0))}\n"
                    f"Total Size: {format_size(result.get('total_size', 0))}\n"
                    f"Duration: {result.get('duration', 0):.2f}s",
                    title="Backup Complete",
                    border_style="green",
                )
            )

    except Exception as e:
        handle_error(f"Failed to create backup: {e}")


@cli.command("list")
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI",
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@click.option(
    "--filter",
    "-f",
    help="Filter snapshots by tag or path",
)
@click.option(
    "--days",
    "-d",
    type=int,
    default=30,
    help="Show snapshots from last N days (default: 30)",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    help="Limit number of results",
)
@pass_config
def list_snapshots(
    config: Config,
    backend: str,
    password_file: Optional[str],
    filter: Optional[str],
    days: int,
    limit: Optional[int],
) -> None:
    """List backup snapshots.

    Lists all backup snapshots in the repository with details including
    creation time, size, and tags.

    Examples:
        backup-cli list -b s3://bucket/backups
        backup-cli list -b s3://bucket/backups -f daily -d 7
    """
    if not BackupManager:
        handle_error("BackupManager module not available")

    try:
        manager = BackupManager(backend, password_file)
        snapshots = manager.list_snapshots(tag=filter, days=days, limit=limit)

        if config.json_output:
            console.print_json(data=snapshots)
        else:
            if not snapshots:
                console.print("[yellow]No snapshots found[/yellow]")
                return

            table = Table(title=f"Backup Snapshots ({len(snapshots)} total)")
            table.add_column("Snapshot ID", style="cyan")
            table.add_column("Date", style="magenta")
            table.add_column("Hostname", style="green")
            table.add_column("Paths", style="blue")
            table.add_column("Size", style="yellow", justify="right")
            table.add_column("Tags", style="white")

            for snapshot in snapshots:
                table.add_row(
                    snapshot.get("short_id", "N/A"),
                    snapshot.get("time", "N/A"),
                    snapshot.get("hostname", "N/A"),
                    "\n".join(snapshot.get("paths", [])),
                    format_size(snapshot.get("size", 0)),
                    ", ".join(snapshot.get("tags", [])),
                )

            console.print(table)

    except Exception as e:
        handle_error(f"Failed to list snapshots: {e}")


@cli.command()
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI",
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@click.option(
    "--snapshot",
    "-s",
    default="latest",
    help="Snapshot ID to restore (default: latest)",
)
@click.option(
    "--target",
    "-t",
    required=True,
    type=click.Path(),
    help="Target directory for restore",
)
@click.option(
    "--include",
    "-i",
    multiple=True,
    help="Include only matching paths",
)
@click.option(
    "--exclude",
    "-x",
    multiple=True,
    help="Exclude matching paths",
)
@click.option(
    "--verify",
    is_flag=True,
    help="Verify restored files",
)
@pass_config
def restore(
    config: Config,
    backend: str,
    password_file: Optional[str],
    snapshot: str,
    target: str,
    include: tuple,
    exclude: tuple,
    verify: bool,
) -> None:
    """Restore from backup snapshot.

    Restores files from a backup snapshot to the specified target directory.
    Supports selective restore with include/exclude patterns.

    Examples:
        backup-cli restore -b s3://bucket/backups -s latest -t /restore
        backup-cli restore -b s3://bucket/backups -s abc123 -t /restore -i "*.txt"
    """
    if not RecoveryManager:
        handle_error("RecoveryManager module not available")

    # Confirm if target exists and has files
    target_path = Path(target)
    if target_path.exists() and any(target_path.iterdir()):
        if not confirm_action(
            f"Target directory {target} is not empty. Continue?",
            default=False,
        ):
            console.print("[yellow]Restore cancelled[/yellow]")
            return

    try:
        manager = RecoveryManager(backend, password_file)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Restoring files...", total=100)

            result = manager.restore_snapshot(
                snapshot_id=snapshot,
                target_path=target,
                include=list(include),
                exclude=list(exclude),
                verify=verify,
                progress_callback=lambda pct: progress.update(task, completed=pct),
            )

            progress.update(task, completed=100)

        if config.json_output:
            console.print_json(data=result)
        else:
            status = (
                "[green]✓ Verified[/green]" if verify and result.get("verified") else ""
            )
            console.print(
                Panel(
                    f"[green]Restore completed successfully![/green] {status}\n\n"
                    f"Snapshot ID: {result.get('snapshot_id', 'N/A')}\n"
                    f"Files Restored: {result.get('files_restored', 0):,}\n"
                    f"Total Size: {format_size(result.get('total_size', 0))}\n"
                    f"Duration: {result.get('duration', 0):.2f}s",
                    title="Restore Complete",
                    border_style="green",
                )
            )

    except Exception as e:
        handle_error(f"Failed to restore backup: {e}")


@cli.command()
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI",
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@click.option(
    "--snapshot",
    "-s",
    help="Specific snapshot ID to validate (default: all)",
)
@click.option(
    "--full-check",
    is_flag=True,
    help="Perform full data integrity check",
)
@click.option(
    "--read-data",
    is_flag=True,
    help="Read and verify all data blobs",
)
@pass_config
def validate(
    config: Config,
    backend: str,
    password_file: Optional[str],
    snapshot: Optional[str],
    full_check: bool,
    read_data: bool,
) -> None:
    """Validate backup integrity.

    Validates the integrity of backup snapshots and repository data.
    Can perform quick checks or comprehensive data verification.

    Examples:
        backup-cli validate -b s3://bucket/backups
        backup-cli validate -b s3://bucket/backups --full-check
    """
    if not BackupValidator:
        handle_error("BackupValidator module not available")

    try:
        validator = BackupValidator(backend, password_file)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Validating backup...", total=None)

            result = validator.validate_snapshot(
                snapshot_id=snapshot,
                full_check=full_check,
                read_data=read_data,
            )

            progress.update(task, completed=True)

        if config.json_output:
            console.print_json(data=result)
        else:
            status_color = "green" if result.get("valid") else "red"
            status_text = "VALID" if result.get("valid") else "INVALID"

            details = f"[{status_color}]Status: {status_text}[/{status_color}]\n\n"
            if result.get("errors"):
                details += "[red]Errors:[/red]\n"
                for error in result["errors"]:
                    details += f"  • {error}\n"
            if result.get("warnings"):
                details += "[yellow]Warnings:[/yellow]\n"
                for warning in result["warnings"]:
                    details += f"  • {warning}\n"

            console.print(
                Panel(
                    details,
                    title="Validation Results",
                    border_style=status_color,
                )
            )

    except Exception as e:
        handle_error(f"Failed to validate backup: {e}")


@cli.command()
@click.option(
    "--source",
    "-s",
    required=True,
    multiple=True,
    help="Source path(s) to backup",
)
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI",
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@click.option(
    "--cron",
    "-c",
    required=True,
    help="Cron expression for schedule (e.g., '0 2 * * *')",
)
@click.option(
    "--retention-policy",
    "-r",
    help="Retention policy (e.g., 'keep-daily:7,keep-weekly:4')",
)
@click.option(
    "--tags",
    "-t",
    multiple=True,
    help="Tags to apply to backups",
)
@click.option(
    "--name",
    "-n",
    help="Friendly name for scheduled job",
)
@pass_config
def schedule(
    config: Config,
    source: tuple,
    backend: str,
    password_file: Optional[str],
    cron: str,
    retention_policy: Optional[str],
    tags: tuple,
    name: Optional[str],
) -> None:
    """Schedule automated backups.

    Creates a scheduled backup job using cron expressions. Supports
    retention policies for automated backup cleanup.

    Examples:
        backup-cli schedule -s /data -b s3://bucket/backups -c "0 2 * * *"
        backup-cli schedule -s /app -b s3://bucket -c "0 */6 * * *" -r "keep-daily:7"
    """
    if not BackupScheduler:
        handle_error("BackupScheduler module not available")

    try:
        scheduler = BackupScheduler()

        job_config = {
            "sources": list(source),
            "backend": backend,
            "password_file": password_file,
            "tags": list(tags),
            "retention_policy": retention_policy,
            "name": name or f"Backup {','.join(source)}",
        }

        job_id = scheduler.add_job(
            cron_expression=cron,
            job_config=job_config,
        )

        if config.json_output:
            console.print_json(data={"job_id": job_id, "config": job_config})
        else:
            console.print(
                Panel(
                    f"[green]Backup scheduled successfully![/green]\n\n"
                    f"Job ID: {job_id}\n"
                    f"Schedule: {cron}\n"
                    f"Sources: {', '.join(source)}\n"
                    f"Next Run: {scheduler.get_next_run_time(job_id)}",
                    title="Schedule Created",
                    border_style="green",
                )
            )

    except Exception as e:
        handle_error(f"Failed to schedule backup: {e}")


@cli.command()
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI",
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@click.option(
    "--frequency",
    "-f",
    default="quarterly",
    type=click.Choice(["weekly", "monthly", "quarterly", "annually"]),
    help="Drill frequency (default: quarterly)",
)
@click.option(
    "--notification",
    "-n",
    multiple=True,
    default=["email"],
    help="Notification channels",
)
@click.option(
    "--compliance-framework",
    "-c",
    default="SOC2",
    type=click.Choice(["SOC2", "HIPAA", "GDPR", "ISO27001", "NIST"]),
    help="Compliance framework (default: SOC2)",
)
@pass_config
def schedule_drill(
    config: Config,
    backend: str,
    password_file: Optional[str],
    frequency: str,
    notification: tuple,
    compliance_framework: str,
) -> None:
    """Schedule disaster recovery drills.

    Schedules automated disaster recovery drills for compliance validation
    and operational resilience testing.

    Examples:
        backup-cli schedule-drill -b s3://bucket/backups -f quarterly
        backup-cli schedule-drill -b s3://bucket -f monthly -c HIPAA
    """
    if not DRDrill:
        handle_error("DRDrill module not available")

    # Convert frequency to cron
    cron_map = {
        "weekly": "0 2 * * 0",  # Sunday 2 AM
        "monthly": "0 2 1 * *",  # 1st of month 2 AM
        "quarterly": "0 2 1 */3 *",  # 1st of every 3 months 2 AM
        "annually": "0 2 1 1 *",  # January 1st 2 AM
    }
    cron = cron_map.get(frequency)

    try:
        drill = DRDrill(backend, password_file)

        drill_config = DrillConfig(
            name=f"Scheduled {frequency.capitalize()} DR Drill",
            description=f"Automated {frequency} disaster recovery drill",
            compliance_framework=compliance_framework,
            notification_channels=list(notification),
        )

        schedule_id = drill.schedule_drill(drill_config, cron)

        if config.json_output:
            console.print_json(
                data={"schedule_id": schedule_id, "frequency": frequency, "cron": cron}
            )
        else:
            console.print(
                Panel(
                    f"[green]DR Drill scheduled successfully![/green]\n\n"
                    f"Schedule ID: {schedule_id}\n"
                    f"Frequency: {frequency.capitalize()}\n"
                    f"Framework: {compliance_framework}\n"
                    f"Cron: {cron}",
                    title="Drill Scheduled",
                    border_style="green",
                )
            )

    except Exception as e:
        handle_error(f"Failed to schedule drill: {e}")


@cli.command()
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI",
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@click.option(
    "--days",
    "-d",
    type=int,
    default=7,
    help="Check status for last N days (default: 7)",
)
@pass_config
def status(
    config: Config,
    backend: str,
    password_file: Optional[str],
    days: int,
) -> None:
    """Check backup status and health.

    Displays backup status, recent activity, and repository health metrics.

    Examples:
        backup-cli status -b s3://bucket/backups
        backup-cli status -b s3://bucket/backups -d 30
    """
    if not BackupManager:
        handle_error("BackupManager module not available")

    try:
        manager = BackupManager(backend, password_file)
        status_data = manager.get_status(days=days)

        if config.json_output:
            console.print_json(data=status_data)
        else:
            # Repository info
            repo_tree = Tree("[bold cyan]Repository Status[/bold cyan]")
            repo_tree.add(f"Backend: {backend}")
            repo_tree.add(f"Total Snapshots: {status_data.get('snapshot_count', 0)}")
            repo_tree.add(
                f"Total Size: {format_size(status_data.get('total_size', 0))}"
            )
            repo_tree.add(
                f"Last Backup: {status_data.get('last_backup_time', 'Never')}"
            )

            # Recent activity
            activity_tree = Tree("[bold magenta]Recent Activity[/bold magenta]")
            for activity in status_data.get("recent_activity", [])[:5]:
                activity_tree.add(
                    f"{activity.get('time', 'N/A')}: {activity.get('action', 'N/A')}"
                )

            # Health status
            health = status_data.get("health", {})
            health_color = "green" if health.get("status") == "healthy" else "yellow"
            health_tree = Tree(
                f"[bold {health_color}]Health: "
                f"{health.get('status', 'unknown').upper()}[/bold {health_color}]"
            )
            if health.get("issues"):
                for issue in health["issues"]:
                    health_tree.add(f"[yellow]⚠ {issue}[/yellow]")

            console.print(repo_tree)
            console.print("\n")
            console.print(activity_tree)
            console.print("\n")
            console.print(health_tree)

    except Exception as e:
        handle_error(f"Failed to get status: {e}")


@cli.command()
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI",
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@click.option(
    "--config-file",
    "-c",
    type=click.Path(exists=True),
    help="Path to drill configuration YAML",
)
@click.option(
    "--name",
    "-n",
    help="Drill name",
)
@click.option(
    "--compliance-framework",
    "-f",
    default="SOC2",
    type=click.Choice(["SOC2", "HIPAA", "GDPR", "ISO27001", "NIST"]),
    help="Compliance framework (default: SOC2)",
)
@pass_config
def drill(
    config: Config,
    backend: str,
    password_file: Optional[str],
    config_file: Optional[str],
    name: Optional[str],
    compliance_framework: str,
) -> None:
    """Execute disaster recovery drill.

    Executes a disaster recovery drill with validation and compliance
    reporting. Can use configuration file or inline parameters.

    Examples:
        backup-cli drill -b s3://bucket/backups -n "Q1 2024 Drill"
        backup-cli drill -b s3://bucket/backups -c drill_config.yaml
    """
    if not DRDrill or not ComplianceReporter:
        handle_error("DRDrill or ComplianceReporter module not available")

    try:
        drill_mgr = DRDrill(backend, password_file)

        # Load configuration from file or create default
        if config_file:
            import yaml

            with open(config_file) as f:
                drill_config_data = yaml.safe_load(f)
                drill_config = DrillConfig(**drill_config_data)
        else:
            drill_config = DrillConfig(
                name=name or f"DR Drill {datetime.now().strftime('%Y-%m-%d')}",
                description="Manual disaster recovery drill execution",
                compliance_framework=compliance_framework,
            )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Executing drill...", total=None)

            drill_report = drill_mgr.execute_drill(drill_config)

            progress.update(task, completed=True)

        # Generate compliance report
        reporter = ComplianceReporter()
        compliance_report = reporter.generate_report(
            drill_report, compliance_framework, "markdown"
        )

        if config.json_output:
            console.print_json(data=drill_report.dict())
        else:
            status_color = (
                "green"
                if drill_report.status == "SUCCESS"
                else "red" if drill_report.status == "FAILED" else "yellow"
            )

            console.print(
                Panel(
                    f"[{status_color}]Status: {drill_report.status}[/{status_color}]\n\n"  # noqa: E501
                    f"Recovery Time: {drill_report.recovery_time_minutes:.2f} minutes\n"
                    f"RTO Compliant: {'✓' if drill_report.rto_compliant else '✗'}\n"
                    f"RPO Compliant: {'✓' if drill_report.rpo_compliant else '✗'}\n\n"
                    f"Compliance Report: {compliance_report.get('report_file', 'N/A')}",
                    title=f"DR Drill Complete - {drill_report.drill_name}",
                    border_style=status_color,
                )
            )

            # Display validation results
            if drill_report.validation_results:
                table = Table(title="Validation Results")
                table.add_column("Check", style="cyan")
                table.add_column("Result", style="white")

                for check, result in drill_report.validation_results.items():
                    result_text = (
                        "[green]✓ PASS[/green]" if result else "[red]✗ FAIL[/red]"
                    )
                    table.add_row(check, result_text)

                console.print("\n")
                console.print(table)

    except Exception as e:
        handle_error(f"Failed to execute drill: {e}")


@cli.command()
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI",
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@pass_config
def stats(
    config: Config,
    backend: str,
    password_file: Optional[str],
) -> None:
    """Show repository statistics.

    Displays detailed statistics about the backup repository including
    size, snapshot count, and storage efficiency.

    Examples:
        backup-cli stats -b s3://bucket/backups
    """
    if not BackupManager:
        handle_error("BackupManager module not available")

    try:
        manager = BackupManager(backend, password_file)
        stats_data = manager.get_stats()

        if config.json_output:
            console.print_json(data=stats_data)
        else:
            table = Table(title="Repository Statistics")
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="magenta")

            table.add_row("Total Size", format_size(stats_data.get("total_size", 0)))
            table.add_row("Total Snapshots", str(stats_data.get("snapshot_count", 0)))
            table.add_row("Total Files", f"{stats_data.get('total_files', 0):,}")
            table.add_row("Total Blobs", f"{stats_data.get('total_blobs', 0):,}")
            table.add_row(
                "Compression Ratio",
                f"{stats_data.get('compression_ratio', 0):.2f}x",
            )
            table.add_row(
                "Deduplication Ratio",
                f"{stats_data.get('dedup_ratio', 0):.2f}x",
            )
            table.add_row("Last Check", stats_data.get("last_check", "Never"))

            console.print(table)

    except Exception as e:
        handle_error(f"Failed to get statistics: {e}")


@cli.command()
@pass_config
def jobs(config: Config) -> None:
    """List scheduled backup jobs.

    Displays all scheduled backup jobs with their configuration and
    next run times.

    Examples:
        backup-cli jobs
    """
    if not BackupScheduler:
        handle_error("BackupScheduler module not available")

    try:
        scheduler = BackupScheduler()
        jobs_list = scheduler.list_jobs()

        if config.json_output:
            console.print_json(data=jobs_list)
        else:
            if not jobs_list:
                console.print("[yellow]No scheduled jobs found[/yellow]")
                return

            table = Table(title=f"Scheduled Jobs ({len(jobs_list)} total)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Schedule", style="green")
            table.add_column("Next Run", style="yellow")
            table.add_column("Status", style="white")

            for job in jobs_list:
                table.add_row(
                    job.get("id", "N/A")[:8],
                    job.get("name", "N/A"),
                    job.get("cron", "N/A"),
                    job.get("next_run", "N/A"),
                    job.get("status", "enabled"),
                )

            console.print(table)

    except Exception as e:
        handle_error(f"Failed to list jobs: {e}")


@cli.command()
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI",
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@click.option(
    "--retention-policy",
    "-r",
    required=True,
    help="Retention policy (e.g., 'keep-daily:7,keep-weekly:4,keep-monthly:12')",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
@pass_config
def prune(
    config: Config,
    backend: str,
    password_file: Optional[str],
    retention_policy: str,
    dry_run: bool,
) -> None:
    """Apply retention policy and prune old snapshots.

    Removes old snapshots according to the specified retention policy.
    Use --dry-run to preview deletions before applying.

    Examples:
        backup-cli prune -b s3://bucket -r "keep-daily:7,keep-weekly:4" --dry-run
        backup-cli prune -b s3://bucket -r "keep-daily:7,keep-monthly:12"
    """
    if not BackupManager:
        handle_error("BackupManager module not available")

    try:
        manager = BackupManager(backend, password_file)

        # Parse retention policy
        policy_parts = retention_policy.split(",")
        policy_dict = {}
        for part in policy_parts:
            key, value = part.split(":")
            policy_dict[key.strip()] = int(value.strip())

        if dry_run:
            console.print("[yellow]DRY RUN - No snapshots will be deleted[/yellow]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Pruning snapshots...", total=None)

            result = manager.prune_snapshots(policy_dict, dry_run=dry_run)

            progress.update(task, completed=True)

        if config.json_output:
            console.print_json(data=result)
        else:
            console.print(
                Panel(
                    f"[green]Prune completed![/green]\n\n"
                    f"Snapshots Removed: {result.get('removed_snapshots', 0)}\n"
                    f"Space Freed: {format_size(result.get('space_freed', 0))}\n"
                    f"Snapshots Kept: {result.get('kept_snapshots', 0)}",
                    title="Prune Results" + (" (DRY RUN)" if dry_run else ""),
                    border_style="green",
                )
            )

    except Exception as e:
        handle_error(f"Failed to prune snapshots: {e}")


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    required=True,
    help="Output file path",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["yaml", "json"]),
    default="yaml",
    help="Output format (default: yaml)",
)
@pass_config
def export_config(config: Config, output: str, format: str) -> None:
    """Export configuration to file.

    Exports the current configuration to a file for backup or sharing.

    Examples:
        backup-cli export-config -o backup_config.yaml
        backup-cli export-config -o backup_config.json -f json
    """
    try:
        # Collect configuration
        config_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "backend": config.backend,
            "password_file": config.password_file,
        }

        output_path = Path(output)

        if format == "yaml":
            import yaml

            with open(output_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)
        else:
            with open(output_path, "w") as f:
                json.dump(config_data, f, indent=2)

        console.print(f"[green]Configuration exported to {output_path}[/green]")

    except Exception as e:
        handle_error(f"Failed to export configuration: {e}")


@cli.command()
@click.option(
    "--backend",
    "-b",
    required=True,
    help="Backup backend URI",
)
@click.option(
    "--password-file",
    "-p",
    type=click.Path(exists=True),
    help="Path to restic password file",
)
@click.option(
    "--snapshot",
    "-s",
    default="latest",
    help="Snapshot ID to browse (default: latest)",
)
@click.option(
    "--path",
    type=str,
    default="/",
    help="Path within snapshot to browse",
)
@pass_config
def browse(
    config: Config,
    backend: str,
    password_file: Optional[str],
    snapshot: str,
    path: str,
) -> None:
    """Browse files in a snapshot.

    Interactively browse and explore files within a backup snapshot.

    Examples:
        backup-cli browse -b s3://bucket/backups
        backup-cli browse -b s3://bucket/backups -s abc123 -path /data
    """
    if not RecoveryManager:
        handle_error("RecoveryManager module not available")

    try:
        manager = RecoveryManager(backend, password_file)
        files = manager.browse_snapshot(snapshot, path)

        if config.json_output:
            console.print_json(data=files)
        else:
            tree = Tree(f"[bold cyan]Snapshot: {snapshot}[/bold cyan] - {path}")

            for file_info in files:
                file_type = file_info.get("type", "file")
                name = file_info.get("name", "")
                size = format_size(file_info.get("size", 0))

                if file_type == "dir":
                    tree.add(f"📁 {name}/")
                else:
                    tree.add(f"📄 {name} ({size})")

            console.print(tree)

    except Exception as e:
        handle_error(f"Failed to browse snapshot: {e}")


if __name__ == "__main__":
    cli()
