"""
Container Platform CLI - Comprehensive Command-Line Interface

Production-ready CLI for container platform management with beautiful
terminal output, progress tracking, and comprehensive error handling.

Features:
- Build container images with BuildKit support
- Push/pull images to/from registries
- Optimize images with dive integration
- Security scanning with Trivy/Grype
- Lint Dockerfiles with hadolint
- Synchronize images across registries
- Container lifecycle management
- Resource monitoring and statistics
- JSON output for automation
- Verbose logging support
- Configuration file support

Author: DevCrew Container Platform Team
License: MIT
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml
from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.tree import Tree

# Import container platform modules
try:
    from ..builder.build_engine import (
        BuildBackend,
        BuildContext,
        BuildEngine,
        BuildMetrics,
        BuildProgress,
        Platform,
    )
    from ..linter.dockerfile_linter import DockerfileLinter, LintSeverity
    from ..manager.container_manager import (
        ContainerConfig,
        ContainerManager,
        ContainerStatus,
        PortMapping,
        ResourceLimits,
    )
    from ..optimizer.image_optimizer import ImageOptimizer, OptimizationLevel
    from ..registry.registry_client import (
        ImagePromotionStage,
        RegistryClient,
        RegistryConfig,
        RegistryType,
    )
    from ..scanner.security_scanner import (
        ScannerConfig,
        ScannerType,
        SecurityScanner,
        SeverityLevel,
    )

    MODULES_AVAILABLE = True
except ImportError as e:
    MODULES_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Console for rich output
console = Console()

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_VALIDATION_ERROR = 3


# ============================================================================
# Configuration Management
# ============================================================================


class CLIConfig:
    """CLI configuration management."""

    def __init__(self, config_file: Optional[Path] = None):
        """Initialize CLI configuration."""
        self.config_file = (
            config_file or Path.home() / ".container-platform" / "config.yaml"
        )
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self.config = yaml.safe_load(f) or {}
                console.print(
                    f"[dim]Loaded configuration from {self.config_file}[/dim]"
                )
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to load config: {e}[/yellow]")

    def save(self) -> None:
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                yaml.safe_dump(self.config, f, default_flow_style=False)
            console.print(f"[green]Configuration saved to {self.config_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error: Failed to save config: {e}[/red]")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value


# Global configuration instance
cli_config = CLIConfig()


# ============================================================================
# Utility Functions
# ============================================================================


def setup_logging(verbose: bool = False) -> None:
    """Setup logging with rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def check_modules() -> None:
    """Check if required modules are available."""
    if not MODULES_AVAILABLE:
        console.print(
            Panel(
                f"[red]Error: Required modules not available[/red]\n\n{IMPORT_ERROR}",
                title="Import Error",
                border_style="red",
            )
        )
        sys.exit(EXIT_ERROR)


def format_size(bytes_size: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format duration to human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    return f"{hours:.1f}h"


def output_json(data: Any) -> None:
    """Output data as JSON."""
    console.print_json(json.dumps(data, default=str))


def output_table(
    title: str, columns: List[str], rows: List[List[Any]], json_output: bool = False
) -> None:
    """Output data as table or JSON."""
    if json_output:
        data = [dict(zip(columns, row)) for row in rows]
        output_json(data)
        return

    table = Table(title=title, show_header=True, header_style="bold magenta")
    for column in columns:
        table.add_column(column)
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    console.print(table)


# ============================================================================
# Main CLI Group
# ============================================================================


@click.group()
@click.option(
    "--config",
    type=click.Path(path_type=Path),
    help="Configuration file path",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.pass_context
def cli(
    ctx: click.Context, config: Optional[Path], verbose: bool, json_output: bool
) -> None:
    """Container Platform CLI - Comprehensive container management tool."""
    check_modules()
    setup_logging(verbose)

    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["json_output"] = json_output

    if config:
        global cli_config
        cli_config = CLIConfig(config)
        ctx.obj["config"] = cli_config


# ============================================================================
# Build Commands
# ============================================================================


@cli.group()
def build() -> None:
    """Build container images."""
    pass


@build.command("image")
@click.argument("context", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--dockerfile",
    "-f",
    type=click.Path(exists=True, path_type=Path),
    help="Path to Dockerfile (default: context/Dockerfile)",
)
@click.option("--tag", "-t", multiple=True, help="Image tag(s)")
@click.option(
    "--platform",
    multiple=True,
    type=click.Choice(["linux/amd64", "linux/arm64", "linux/arm/v7"]),
    default=["linux/amd64"],
    help="Target platform(s)",
)
@click.option("--build-arg", multiple=True, help="Build arguments (KEY=VALUE)")
@click.option("--target", help="Build target stage")
@click.option("--no-cache", is_flag=True, help="Disable build cache")
@click.option("--pull", is_flag=True, default=True, help="Always pull base images")
@click.option(
    "--backend",
    type=click.Choice(["docker", "buildkit"]),
    default="buildkit",
    help="Build backend",
)
@click.pass_context
def build_image(
    ctx: click.Context,
    context: Path,
    dockerfile: Optional[Path],
    tag: tuple,
    platform: tuple,
    build_arg: tuple,
    target: Optional[str],
    no_cache: bool,
    pull: bool,
    backend: str,
) -> None:
    """Build a container image from Dockerfile."""
    json_output = ctx.obj.get("json_output", False)

    try:
        # Resolve Dockerfile path
        if not dockerfile:
            dockerfile = context / "Dockerfile"

        if not dockerfile.exists():
            console.print(f"[red]Error: Dockerfile not found at {dockerfile}[/red]")
            sys.exit(EXIT_ERROR)

        # Parse build args
        build_args = {}
        for arg in build_arg:
            if "=" in arg:
                key, value = arg.split("=", 1)
                build_args[key] = value

        # Convert platforms
        platforms = [Platform(p) for p in platform]

        # Create build context
        build_context = BuildContext(
            dockerfile_path=dockerfile,
            context_path=context,
            tags=list(tag),
            platforms=platforms,
            build_args=build_args,
            target=target,
            no_cache=no_cache,
            pull=pull,
        )

        # Initialize build engine
        backend_enum = (
            BuildBackend.BUILDKIT if backend == "buildkit" else BuildBackend.DOCKER
        )
        engine = BuildEngine(backend=backend_enum)

        # Progress tracking
        if not json_output:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=console,
            )

            with progress:
                task = progress.add_task("[cyan]Building image...", total=100)

                def progress_callback(build_progress: BuildProgress) -> None:
                    progress.update(
                        task,
                        completed=build_progress.progress_percent,
                        description=f"[cyan]Step {build_progress.current_step}/"
                        f"{build_progress.total_steps}: {build_progress.status}",
                    )

                image_id, metrics = engine.build(build_context, progress_callback)
        else:
            image_id, metrics = engine.build(build_context)

        # Output results
        if json_output:
            output_json(
                {
                    "image_id": image_id,
                    "tags": list(tag),
                    "size": metrics.image_size_bytes,
                    "duration": metrics.duration_seconds,
                    "cache_hits": metrics.cache_hits,
                    "cache_misses": metrics.cache_misses,
                }
            )
        else:
            console.print(
                Panel(
                    f"[green]Image built successfully![/green]\n\n"
                    f"Image ID: [cyan]{image_id[:12]}[/cyan]\n"
                    f"Size: [yellow]{format_size(metrics.image_size_bytes)}[/yellow]\n"
                    f"Duration: [blue]{format_duration(metrics.duration_seconds)}[/blue]\n"
                    f"Cache hits: {metrics.cache_hits} / Misses: {metrics.cache_misses}\n"
                    f"Tags: {', '.join(tag) if tag else 'none'}",
                    title="Build Complete",
                    border_style="green",
                )
            )

        sys.exit(EXIT_SUCCESS)

    except Exception as e:
        if json_output:
            output_json({"error": str(e)})
        else:
            console.print(f"[red]Build failed: {e}[/red]")
        sys.exit(EXIT_ERROR)


# ============================================================================
# Push/Pull Commands
# ============================================================================


@cli.command("push")
@click.argument("image")
@click.option("--registry", help="Registry URL")
@click.option("--username", help="Registry username")
@click.option("--password", help="Registry password")
@click.option(
    "--registry-type",
    type=click.Choice(["dockerhub", "ecr", "gcr", "acr", "harbor", "generic"]),
    default="dockerhub",
)
@click.pass_context
def push_image(
    ctx: click.Context,
    image: str,
    registry: Optional[str],
    username: Optional[str],
    password: Optional[str],
    registry_type: str,
) -> None:
    """Push image to registry."""
    json_output = ctx.obj.get("json_output", False)

    try:
        # Parse image name
        parts = image.rsplit(":", 1)
        image_name = parts[0]
        tag = parts[1] if len(parts) > 1 else "latest"

        # Get registry from config or parameter
        if not registry:
            registry = cli_config.get("registry.url")
            if not registry:
                console.print("[red]Error: Registry URL not specified[/red]")
                sys.exit(EXIT_CONFIG_ERROR)

        # Create registry config
        registry_config = RegistryConfig(
            registry_type=RegistryType(registry_type),
            url=registry,
            username=username or cli_config.get("registry.username"),
            password=password or cli_config.get("registry.password"),
        )

        # Initialize registry client
        client = RegistryClient(registry_config)

        # Push image
        if not json_output:
            with console.status(f"[bold green]Pushing {image}..."):
                image_info = client.push_image(image_name, tag)
        else:
            image_info = client.push_image(image_name, tag)

        # Output results
        if json_output:
            output_json(
                {
                    "image": image_info.full_name,
                    "digest": image_info.digest,
                    "size": image_info.size,
                }
            )
        else:
            console.print(f"[green]Successfully pushed {image_info.full_name}[/green]")

        sys.exit(EXIT_SUCCESS)

    except Exception as e:
        if json_output:
            output_json({"error": str(e)})
        else:
            console.print(f"[red]Push failed: {e}[/red]")
        sys.exit(EXIT_ERROR)


@cli.command("pull")
@click.argument("image")
@click.option("--registry", help="Registry URL")
@click.option("--username", help="Registry username")
@click.option("--password", help="Registry password")
@click.option(
    "--registry-type",
    type=click.Choice(["dockerhub", "ecr", "gcr", "acr", "harbor", "generic"]),
    default="dockerhub",
)
@click.pass_context
def pull_image(
    ctx: click.Context,
    image: str,
    registry: Optional[str],
    username: Optional[str],
    password: Optional[str],
    registry_type: str,
) -> None:
    """Pull image from registry."""
    json_output = ctx.obj.get("json_output", False)

    try:
        # Parse image name
        parts = image.rsplit(":", 1)
        image_name = parts[0]
        tag = parts[1] if len(parts) > 1 else "latest"

        # Get registry from config or parameter
        if not registry:
            registry = cli_config.get("registry.url")

        # Create registry config
        registry_config = RegistryConfig(
            registry_type=RegistryType(registry_type),
            url=registry or "docker.io",
            username=username or cli_config.get("registry.username"),
            password=password or cli_config.get("registry.password"),
        )

        # Initialize registry client
        client = RegistryClient(registry_config)

        # Pull image
        if not json_output:
            with console.status(f"[bold green]Pulling {image}..."):
                image_info = client.pull_image(image_name, tag)
        else:
            image_info = client.pull_image(image_name, tag)

        # Output results
        if json_output:
            output_json(
                {
                    "image": image_info.full_name,
                    "digest": image_info.digest,
                    "size": image_info.size,
                }
            )
        else:
            console.print(f"[green]Successfully pulled {image_info.full_name}[/green]")

        sys.exit(EXIT_SUCCESS)

    except Exception as e:
        if json_output:
            output_json({"error": str(e)})
        else:
            console.print(f"[red]Pull failed: {e}[/red]")
        sys.exit(EXIT_ERROR)


# ============================================================================
# Optimize Command
# ============================================================================


@cli.command("optimize")
@click.argument("image")
@click.option("--output", "-o", help="Output optimized image name")
@click.option(
    "--level",
    type=click.Choice(["conservative", "balanced", "aggressive"]),
    default="balanced",
    help="Optimization level",
)
@click.option(
    "--use-dive", is_flag=True, default=True, help="Use dive tool for analysis"
)
@click.pass_context
def optimize_image(
    ctx: click.Context,
    image: str,
    output: Optional[str],
    level: str,
    use_dive: bool,
) -> None:
    """Analyze and optimize container image."""
    json_output = ctx.obj.get("json_output", False)

    try:
        # Initialize optimizer
        optimizer = ImageOptimizer()

        # Analyze image
        if not json_output:
            with console.status(f"[bold cyan]Analyzing {image}..."):
                analysis = optimizer.analyze_image(image, use_dive=use_dive)
        else:
            analysis = optimizer.analyze_image(image, use_dive=use_dive)

        # Output results
        if json_output:
            output_json(
                {
                    "image": analysis.image_name,
                    "total_size": analysis.total_size,
                    "wasted_space": analysis.wasted_space,
                    "efficiency_score": analysis.efficiency_score,
                    "potential_savings": analysis.potential_savings,
                    "suggestions": [
                        {
                            "category": s.category,
                            "priority": s.priority,
                            "description": s.description,
                            "potential_savings": s.potential_savings,
                        }
                        for s in analysis.suggestions
                    ],
                }
            )
        else:
            # Create summary table
            summary_table = Table(title="Image Analysis", show_header=False)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="yellow")

            summary_table.add_row("Image", analysis.image_name)
            summary_table.add_row("Total Size", format_size(analysis.total_size))
            summary_table.add_row("Wasted Space", format_size(analysis.wasted_space))
            summary_table.add_row(
                "Efficiency Score", f"{analysis.efficiency_score:.1f}%"
            )
            summary_table.add_row("Layers", str(analysis.layer_count))
            summary_table.add_row(
                "Potential Savings", format_size(analysis.potential_savings)
            )

            console.print(summary_table)

            # Display suggestions
            if analysis.suggestions:
                console.print("\n[bold]Optimization Suggestions:[/bold]")
                for i, suggestion in enumerate(analysis.suggestions, 1):
                    priority_color = {
                        "high": "red",
                        "medium": "yellow",
                        "low": "green",
                    }.get(suggestion.priority, "white")

                    console.print(
                        f"\n[{priority_color}]{i}. [{suggestion.priority.upper()}] "
                        f"{suggestion.category}[/{priority_color}]"
                    )
                    console.print(f"   {suggestion.description}")
                    console.print(
                        f"   Savings: {format_size(suggestion.potential_savings)}"
                    )
                    if suggestion.implementation:
                        console.print(f"   [dim]Fix: {suggestion.implementation}[/dim]")

        sys.exit(EXIT_SUCCESS)

    except Exception as e:
        if json_output:
            output_json({"error": str(e)})
        else:
            console.print(f"[red]Optimization failed: {e}[/red]")
        sys.exit(EXIT_ERROR)


# ============================================================================
# Scan Command
# ============================================================================


@cli.command("scan")
@click.argument("image")
@click.option(
    "--scanner",
    type=click.Choice(["trivy", "grype", "both"]),
    default="trivy",
    help="Scanner to use",
)
@click.option(
    "--severity",
    type=click.Choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"]),
    default="MEDIUM",
    help="Minimum severity threshold",
)
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "sarif", "table"]),
    default="table",
)
@click.pass_context
def scan_image(
    ctx: click.Context,
    image: str,
    scanner: str,
    severity: str,
    output: Optional[Path],
    output_format: str,
) -> None:
    """Scan image for security vulnerabilities."""
    json_output = ctx.obj.get("json_output", False) or output_format == "json"

    try:
        # Create scanner config
        config = ScannerConfig(
            scanner_type=ScannerType(scanner),
            severity_threshold=SeverityLevel(severity),
            scan_misconfig=True,
            scan_secrets=True,
        )

        # Initialize scanner
        scanner_obj = SecurityScanner(config)

        # Scan image
        if not json_output:
            with console.status(f"[bold cyan]Scanning {image}..."):
                result = scanner_obj.scan_image(image)
        else:
            result = scanner_obj.scan_image(image)

        # Output results
        if output_format == "json" or json_output:
            data = {
                "image": result.image_name,
                "scan_id": result.scan_id,
                "timestamp": result.timestamp.isoformat(),
                "vulnerabilities": {
                    "critical": result.critical_count,
                    "high": result.high_count,
                    "medium": result.medium_count,
                    "low": result.low_count,
                },
                "fixable": result.fixable_count,
                "total": result.total_count,
                "items": [
                    {
                        "id": v.id,
                        "severity": v.severity.value,
                        "package": v.package_name,
                        "version": v.installed_version,
                        "fixed_version": v.fixed_version,
                        "title": v.title,
                    }
                    for v in result.vulnerabilities
                ],
            }
            if output:
                output.write_text(json.dumps(data, indent=2, default=str))
                console.print(f"[green]Results saved to {output}[/green]")
            else:
                output_json(data)
        elif output_format == "sarif":
            # Save SARIF format
            if not output:
                output = Path(f"scan-{result.scan_id}.sarif")
            result.to_sarif_file(output)
            console.print(f"[green]SARIF report saved to {output}[/green]")
        else:
            # Display summary
            summary_table = Table(title="Scan Summary", show_header=False)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="yellow")

            summary_table.add_row("Image", result.image_name)
            summary_table.add_row("Scanner", result.scanner)
            summary_table.add_row("Total Vulnerabilities", str(result.total_count))
            summary_table.add_row("[red]Critical[/red]", str(result.critical_count))
            summary_table.add_row("[red]High[/red]", str(result.high_count))
            summary_table.add_row("[yellow]Medium[/yellow]", str(result.medium_count))
            summary_table.add_row("[green]Low[/green]", str(result.low_count))
            summary_table.add_row("Fixable", str(result.fixable_count))

            console.print(summary_table)

            # Display vulnerabilities
            if result.vulnerabilities:
                vuln_table = Table(title="Vulnerabilities", show_lines=True)
                vuln_table.add_column("ID", style="cyan")
                vuln_table.add_column("Severity")
                vuln_table.add_column("Package")
                vuln_table.add_column("Installed")
                vuln_table.add_column("Fixed")
                vuln_table.add_column("Title")

                for vuln in result.vulnerabilities[:20]:  # Limit to 20
                    severity_style = {
                        "CRITICAL": "bold red",
                        "HIGH": "red",
                        "MEDIUM": "yellow",
                        "LOW": "green",
                    }.get(vuln.severity.value, "white")

                    vuln_table.add_row(
                        vuln.id,
                        f"[{severity_style}]{vuln.severity.value}[/{severity_style}]",
                        vuln.package_name,
                        vuln.installed_version,
                        vuln.fixed_version or "N/A",
                        vuln.title[:50] + "..." if len(vuln.title) > 50 else vuln.title,
                    )

                console.print(vuln_table)

                if len(result.vulnerabilities) > 20:
                    console.print(
                        f"\n[dim]... and {len(result.vulnerabilities) - 20} more[/dim]"
                    )

        # Exit with error if critical vulnerabilities found
        if result.critical_count > 0:
            sys.exit(EXIT_VALIDATION_ERROR)

        sys.exit(EXIT_SUCCESS)

    except Exception as e:
        if json_output:
            output_json({"error": str(e)})
        else:
            console.print(f"[red]Scan failed: {e}[/red]")
        sys.exit(EXIT_ERROR)


# ============================================================================
# Lint Command
# ============================================================================


@cli.command("lint")
@click.argument("dockerfile", type=click.Path(exists=True, path_type=Path))
@click.option("--strict", is_flag=True, help="Fail on warnings")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output file")
@click.pass_context
def lint_dockerfile(
    ctx: click.Context,
    dockerfile: Path,
    strict: bool,
    output: Optional[Path],
) -> None:
    """Lint Dockerfile for best practices and security."""
    json_output = ctx.obj.get("json_output", False)

    try:
        # Initialize linter
        linter = DockerfileLinter()

        # Lint Dockerfile
        result = linter.lint_file(dockerfile)

        # Output results
        if json_output:
            data = result.to_dict()
            if output:
                output.write_text(json.dumps(data, indent=2))
                console.print(f"[green]Results saved to {output}[/green]")
            else:
                output_json(data)
        else:
            # Display summary
            summary_table = Table(title="Lint Summary", show_header=False)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="yellow")

            summary_table.add_row("Dockerfile", str(dockerfile))
            summary_table.add_row("Total Lines", str(result.total_lines))
            summary_table.add_row("Stages", str(len(result.stages)))
            summary_table.add_row("[red]Errors[/red]", str(result.error_count))
            summary_table.add_row(
                "[yellow]Warnings[/yellow]", str(result.warning_count)
            )
            summary_table.add_row("[blue]Info[/blue]", str(result.info_count))
            summary_table.add_row(
                "Has Healthcheck", "✓" if result.has_healthcheck else "✗"
            )
            summary_table.add_row("Has USER", "✓" if result.has_user else "✗")

            console.print(summary_table)

            # Display findings
            if result.findings:
                findings_table = Table(title="Findings", show_lines=True)
                findings_table.add_column("Line", style="cyan")
                findings_table.add_column("Severity")
                findings_table.add_column("Rule")
                findings_table.add_column("Description")

                for finding in result.findings:
                    severity_style = {
                        "error": "bold red",
                        "warning": "yellow",
                        "info": "blue",
                        "style": "green",
                    }.get(finding.severity.value, "white")

                    findings_table.add_row(
                        str(finding.line_number) if finding.line_number else "-",
                        f"[{severity_style}]{finding.severity.value.upper()}[/{severity_style}]",
                        finding.rule_id,
                        (
                            finding.description[:60] + "..."
                            if len(finding.description) > 60
                            else finding.description
                        ),
                    )

                console.print(findings_table)

        # Exit with error if errors found (or warnings in strict mode)
        if result.error_count > 0 or (strict and result.warning_count > 0):
            sys.exit(EXIT_VALIDATION_ERROR)

        sys.exit(EXIT_SUCCESS)

    except Exception as e:
        if json_output:
            output_json({"error": str(e)})
        else:
            console.print(f"[red]Lint failed: {e}[/red]")
        sys.exit(EXIT_ERROR)


# ============================================================================
# Sync Command
# ============================================================================


@cli.command("sync")
@click.argument("source_image")
@click.argument("target_registry")
@click.option("--source-registry", help="Source registry URL")
@click.option("--target-image", help="Target image name (defaults to source)")
@click.option("--source-username", help="Source registry username")
@click.option("--source-password", help="Source registry password")
@click.option("--target-username", help="Target registry username")
@click.option("--target-password", help="Target registry password")
@click.pass_context
def sync_image(
    ctx: click.Context,
    source_image: str,
    target_registry: str,
    source_registry: Optional[str],
    target_image: Optional[str],
    source_username: Optional[str],
    source_password: Optional[str],
    target_username: Optional[str],
    target_password: Optional[str],
) -> None:
    """Synchronize image between registries."""
    json_output = ctx.obj.get("json_output", False)

    try:
        # Parse source image
        parts = source_image.rsplit(":", 1)
        source_name = parts[0]
        source_tag = parts[1] if len(parts) > 1 else "latest"

        # Parse target image
        if target_image:
            target_parts = target_image.rsplit(":", 1)
            target_name = target_parts[0]
            target_tag = target_parts[1] if len(target_parts) > 1 else source_tag
        else:
            target_name = source_name
            target_tag = source_tag

        # Create source registry client
        source_config = RegistryConfig(
            registry_type=RegistryType.GENERIC,
            url=source_registry or "docker.io",
            username=source_username,
            password=source_password,
        )
        source_client = RegistryClient(source_config)

        # Create target registry client
        target_config = RegistryConfig(
            registry_type=RegistryType.GENERIC,
            url=target_registry,
            username=target_username,
            password=target_password,
        )
        target_client = RegistryClient(target_config)

        # Sync image
        if not json_output:
            with console.status(
                f"[bold cyan]Syncing {source_image} to {target_registry}..."
            ):
                result = target_client.sync_image(
                    source_client, source_name, source_tag, target_name, target_tag
                )
        else:
            result = target_client.sync_image(
                source_client, source_name, source_tag, target_name, target_tag
            )

        # Output results
        if json_output:
            output_json(
                {
                    "source": f"{source_name}:{source_tag}",
                    "target": result.full_name,
                    "digest": result.digest,
                    "size": result.size,
                }
            )
        else:
            console.print(f"[green]Successfully synced to {result.full_name}[/green]")

        sys.exit(EXIT_SUCCESS)

    except Exception as e:
        if json_output:
            output_json({"error": str(e)})
        else:
            console.print(f"[red]Sync failed: {e}[/red]")
        sys.exit(EXIT_ERROR)


# ============================================================================
# Prune Command
# ============================================================================


@cli.command("prune")
@click.option("--containers", is_flag=True, help="Prune containers")
@click.option("--images", is_flag=True, help="Prune images")
@click.option("--all", "prune_all", is_flag=True, help="Prune all unused resources")
@click.option("--force", "-f", is_flag=True, help="Do not prompt for confirmation")
@click.pass_context
def prune_resources(
    ctx: click.Context,
    containers: bool,
    images: bool,
    prune_all: bool,
    force: bool,
) -> None:
    """Clean up unused containers and images."""
    json_output = ctx.obj.get("json_output", False)

    try:
        # Prompt for confirmation unless --force
        if not force and not json_output:
            if not click.confirm(
                "This will remove unused resources. Continue?", default=False
            ):
                console.print("[yellow]Cancelled[/yellow]")
                sys.exit(EXIT_SUCCESS)

        # Initialize container manager
        manager = ContainerManager()
        results = {}

        # Prune containers
        if containers or prune_all:
            if not json_output:
                with console.status("[bold cyan]Pruning containers..."):
                    result = manager.prune_containers()
            else:
                result = manager.prune_containers()
            results["containers"] = result

        # Prune images (using Docker API)
        if images or prune_all:
            if not json_output:
                with console.status("[bold cyan]Pruning images..."):
                    result = manager.client.images.prune()
            else:
                result = manager.client.images.prune()
            results["images"] = result

        # Output results
        if json_output:
            output_json(results)
        else:
            if "containers" in results:
                deleted = results["containers"].get("ContainersDeleted") or []
                space = results["containers"].get("SpaceReclaimed", 0)
                console.print(
                    f"[green]Removed {len(deleted)} containers, "
                    f"reclaimed {format_size(space)}[/green]"
                )

            if "images" in results:
                deleted = results["images"].get("ImagesDeleted") or []
                space = results["images"].get("SpaceReclaimed", 0)
                console.print(
                    f"[green]Removed {len(deleted)} images, "
                    f"reclaimed {format_size(space)}[/green]"
                )

        sys.exit(EXIT_SUCCESS)

    except Exception as e:
        if json_output:
            output_json({"error": str(e)})
        else:
            console.print(f"[red]Prune failed: {e}[/red]")
        sys.exit(EXIT_ERROR)


# ============================================================================
# List Command
# ============================================================================


@cli.command("list")
@click.option(
    "--type",
    "resource_type",
    type=click.Choice(["containers", "images"]),
    default="containers",
    help="Resource type to list",
)
@click.option("--all", "-a", is_flag=True, help="Show all (including stopped)")
@click.option("--filter", "filters", multiple=True, help="Filter (key=value)")
@click.pass_context
def list_resources(
    ctx: click.Context,
    resource_type: str,
    all: bool,
    filters: tuple,
) -> None:
    """List containers or images."""
    json_output = ctx.obj.get("json_output", False)

    try:
        # Parse filters
        filter_dict = {}
        for f in filters:
            if "=" in f:
                key, value = f.split("=", 1)
                filter_dict[key] = value

        # Initialize container manager
        manager = ContainerManager()

        if resource_type == "containers":
            # List containers
            containers = manager.list_containers(all=all, filters=filter_dict)

            if json_output:
                output_json(
                    [
                        {
                            "id": c.short_id,
                            "name": c.name,
                            "image": c.image,
                            "status": c.status,
                            "created": c.created.isoformat(),
                        }
                        for c in containers
                    ]
                )
            else:
                rows = [
                    [
                        c.short_id,
                        c.name,
                        c.image,
                        c.status,
                        c.created.strftime("%Y-%m-%d %H:%M"),
                    ]
                    for c in containers
                ]
                output_table(
                    "Containers",
                    ["ID", "Name", "Image", "Status", "Created"],
                    rows,
                )

        else:  # images
            # List images
            images = manager.client.images.list(all=all)

            if json_output:
                output_json(
                    [
                        {
                            "id": img.short_id,
                            "tags": img.tags,
                            "size": img.attrs.get("Size", 0),
                            "created": img.attrs.get("Created", ""),
                        }
                        for img in images
                    ]
                )
            else:
                rows = [
                    [
                        img.short_id,
                        ", ".join(img.tags[:2]) if img.tags else "<none>",
                        format_size(img.attrs.get("Size", 0)),
                        img.attrs.get("Created", "")[:10],
                    ]
                    for img in images
                ]
                output_table(
                    "Images",
                    ["ID", "Tags", "Size", "Created"],
                    rows,
                )

        sys.exit(EXIT_SUCCESS)

    except Exception as e:
        if json_output:
            output_json({"error": str(e)})
        else:
            console.print(f"[red]List failed: {e}[/red]")
        sys.exit(EXIT_ERROR)


# ============================================================================
# Logs Command
# ============================================================================


@cli.command("logs")
@click.argument("container")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--tail", type=int, help="Number of lines to show from end")
@click.option("--timestamps", "-t", is_flag=True, help="Show timestamps")
@click.pass_context
def container_logs(
    ctx: click.Context,
    container: str,
    follow: bool,
    tail: Optional[int],
    timestamps: bool,
) -> None:
    """Stream container logs."""
    try:
        # Initialize container manager
        manager = ContainerManager()

        if follow:
            # Stream logs
            for line in manager.stream_logs(
                container, follow=True, timestamps=timestamps, tail=tail
            ):
                console.print(line, end="")
        else:
            # Get logs
            logs = manager.get_logs(container, timestamps=timestamps, tail=tail)
            console.print(logs)

        sys.exit(EXIT_SUCCESS)

    except Exception as e:
        console.print(f"[red]Failed to get logs: {e}[/red]")
        sys.exit(EXIT_ERROR)


# ============================================================================
# Config Commands
# ============================================================================


@cli.group()
def config() -> None:
    """Manage CLI configuration."""
    pass


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set configuration value."""
    cli_config.set(key, value)
    cli_config.save()
    console.print(f"[green]Set {key} = {value}[/green]")


@config.command("get")
@click.argument("key")
def config_get(key: str) -> None:
    """Get configuration value."""
    value = cli_config.get(key)
    if value is not None:
        console.print(f"{key} = {value}")
    else:
        console.print(f"[yellow]Key not found: {key}[/yellow]")


@config.command("list")
def config_list() -> None:
    """List all configuration."""
    if cli_config.config:
        console.print_json(json.dumps(cli_config.config, indent=2))
    else:
        console.print("[yellow]No configuration found[/yellow]")


# ============================================================================
# Main Entry Point
# ============================================================================


def main() -> None:
    """Main entry point for CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(EXIT_ERROR)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()
