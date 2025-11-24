"""
Infrastructure Security Scanner CLI.

Comprehensive CLI interface for container vulnerability detection, IaC security
scanning, policy-as-code validation, and cloud configuration auditing. Supports
multiple output formats (JSON, SARIF, HTML, Markdown) and integrates with
CI/CD pipelines for automated security scanning.

Part of devCrew_s1 Infrastructure Security Scanner Platform.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from . import (
    CloudProvider,
    CloudScanner,
    ComplianceFramework,
    ContainerScanner,
    IaCFinding,
    IaCScanner,
    IaCType,
    PolicyEngine,
    PolicyValidator,
    RemediationEngine,
    ReportAggregator,
    SBOMFormat,
    ScanConfig,
    ScannerType,
)

console = Console()

# Exit codes for CI/CD integration
EXIT_SUCCESS = 0
EXIT_FINDINGS_FOUND = 1
EXIT_VALIDATION_FAILED = 2
EXIT_SCAN_ERROR = 3
EXIT_CONFIG_ERROR = 4


class CLIConfig:
    """CLI configuration manager."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize CLI configuration."""
        self.config_path = config_path or self._default_config_path()
        self.config = self._load_config()

    @staticmethod
    def _default_config_path() -> Path:
        """Get default configuration path."""
        config_dir = Path.home() / ".devcrew-security"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.yaml"

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return self._default_config()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config if config else self._default_config()
        except Exception as e:
            console.print(
                f"[yellow]Warning: Failed to load config: {e}[/yellow]"
            )
            return self._default_config()

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "scan": {
                "timeout": 600,
                "max_retries": 3,
                "parallel_scans": 4,
                "severity_threshold": "medium",
            },
            "report": {
                "default_format": "json",
                "output_dir": "./security-reports",
                "include_metadata": True,
            },
            "cloud": {
                "providers": ["aws", "azure", "gcp"],
                "regions": ["us-east-1", "us-west-2"],
            },
            "remediation": {
                "auto_fix": False,
                "create_pr": False,
                "git_branch_prefix": "security-fix/",
            },
            "opa": {
                "policy_path": "./policies",
                "data_path": "./policy-data",
            },
            "github": {
                "enable_code_scanning": True,
                "sarif_upload": True,
            },
        }

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.config, f, default_flow_style=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-notation key."""
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value


def load_config(ctx: click.Context) -> CLIConfig:
    """Load CLI configuration from context."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    return CLIConfig(config_path)


def handle_error(message: str, exit_code: int = EXIT_SCAN_ERROR) -> None:
    """Handle error with formatted output and exit."""
    console.print(f"[bold red]Error:[/bold red] {message}")
    sys.exit(exit_code)


def create_progress() -> Progress:
    """Create rich progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )


def format_severity(severity: str) -> str:
    """Format severity with color."""
    colors = {
        "critical": "bold red",
        "high": "red",
        "medium": "yellow",
        "low": "blue",
        "info": "dim",
    }
    color = colors.get(severity.lower(), "white")
    return f"[{color}]{severity.upper()}[/{color}]"


def display_findings_table(findings: List[Any], title: str) -> None:
    """Display findings in a rich table."""
    if not findings:
        console.print(f"[green]No findings in {title}[/green]")
        return

    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Severity", style="cyan", width=10)
    table.add_column("ID", style="yellow", width=20)
    table.add_column("Title", style="white", width=40)
    table.add_column("Resource", style="dim", width=30)

    for finding in findings[:50]:  # Limit to 50 for display
        severity = getattr(finding, "severity", "unknown")
        finding_id = getattr(finding, "id", getattr(finding, "rule_id", "N/A"))
        title = getattr(finding, "title", getattr(finding, "message", "N/A"))
        resource = getattr(
            finding, "resource", getattr(finding, "file_path", "N/A")
        )

        table.add_row(
            format_severity(severity),
            str(finding_id),
            str(title)[:40],
            str(resource)[:30],
        )

    console.print(table)

    if len(findings) > 50:
        console.print(
            f"[dim]... and {len(findings) - 50} more findings[/dim]"
        )


def save_output(
    data: Any,
    output_file: Optional[str],
    format_type: str,
    default_name: str,
) -> None:
    """Save output to file with proper formatting."""
    if not output_file:
        output_file = (
            f"{default_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            f".{format_type}"
        )

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            if format_type == "json":
                json.dump(data, f, indent=2, default=str)
            elif format_type in ("yaml", "yml"):
                yaml.safe_dump(data, f, default_flow_style=False)
            else:
                f.write(str(data))

        console.print(
            f"[green]Output saved to:[/green] {output_path.absolute()}"
        )
    except Exception as e:
        handle_error(f"Failed to save output: {e}", EXIT_SCAN_ERROR)


def check_fail_on_severity(
    findings: List[Any], fail_on: str, ctx: click.Context
) -> None:
    """Check if findings meet fail-on criteria and exit if needed."""
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    threshold = severity_order.get(fail_on.lower(), 0)

    critical_findings = [
        f
        for f in findings
        if severity_order.get(
            getattr(f, "severity", "").lower(), 0
        ) >= threshold
    ]

    if critical_findings:
        console.print(
            f"\n[red]Found {len(critical_findings)} findings "
            f"at or above {fail_on.upper()} severity[/red]"
        )
        ctx.exit(EXIT_FINDINGS_FOUND)


@click.group()
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, config: Optional[Path], verbose: bool) -> None:
    """
    DevCrew Infrastructure Security Scanner CLI.

    Comprehensive security scanning for containers, IaC, cloud infrastructure,
    and policy validation with automated remediation capabilities.
    """
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose

    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")


# ============================================================================
# SCAN COMMAND GROUP
# ============================================================================


@cli.group()
def scan() -> None:
    """Scan infrastructure components for security issues."""
    pass


@scan.command(name="container")
@click.argument("image", type=str)
@click.option(
    "--severity",
    type=click.Choice(["critical", "high", "medium", "low"], case_sensitive=False),
    default="medium",
    help="Minimum severity to report",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "sarif", "table"], case_sensitive=False),
    default="table",
    help="Output format",
)
@click.option("--output", "-o", type=str, help="Output file path")
@click.option(
    "--fail-on",
    type=click.Choice(["critical", "high", "medium", "low"], case_sensitive=False),
    help="Fail with exit code 1 if findings match severity",
)
@click.option("--sbom", is_flag=True, help="Generate SBOM along with scan")
@click.pass_context
def scan_container(
    ctx: click.Context,
    image: str,
    severity: str,
    output_format: str,
    output: Optional[str],
    fail_on: Optional[str],
    sbom: bool,
) -> None:
    """
    Scan Docker container image for vulnerabilities.

    Example:
        devcrew-security scan container nginx:latest --severity high
        devcrew-security scan container myapp:v1.0 --format json -o report.json
    """
    config = load_config(ctx)

    with create_progress() as progress:
        task = progress.add_task(f"[cyan]Scanning {image}...", total=100)

        try:
            scanner = ContainerScanner()
            scan_config = ScanConfig(
                image_name=image,
                severity_threshold=severity,
                timeout=config.get("scan.timeout", 600),
            )

            progress.update(task, advance=30)
            result = scanner.scan_image(scan_config)
            progress.update(task, advance=40)

            if sbom:
                progress.update(task, description="[cyan]Generating SBOM...")
                _ = scanner.generate_sbom(image, SBOMFormat.CYCLONEDX)
                progress.update(task, advance=20)

            progress.update(task, advance=10, completed=100)

        except Exception as e:
            handle_error(f"Container scan failed: {e}", EXIT_SCAN_ERROR)

    # Display results
    if output_format == "table":
        display_findings_table(result.vulnerabilities, f"Container Scan: {image}")
        console.print(
            f"\n[bold]Summary:[/bold] {len(result.vulnerabilities)} "
            f"vulnerabilities found"
        )
    else:
        output_data = result.to_dict() if hasattr(result, "to_dict") else result
        if output_format == "json":
            if output:
                save_output(output_data, output, "json", "container-scan")
            else:
                console.print_json(data=output_data)
        elif output_format == "sarif":
            # Convert to SARIF format
            aggregator = ReportAggregator()
            sarif = aggregator.to_sarif([output_data])
            save_output(sarif, output, "sarif", "container-scan")

    # Check fail-on criteria
    if fail_on:
        check_fail_on_severity(result.vulnerabilities, fail_on, ctx)


@scan.command(name="terraform")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--scanner",
    type=click.Choice(["checkov", "tfsec", "terrascan", "all"], case_sensitive=False),
    default="all",
    help="Scanner to use",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "sarif", "table"], case_sensitive=False),
    default="table",
    help="Output format",
)
@click.option("--output", "-o", type=str, help="Output file path")
@click.option(
    "--fail-on",
    type=click.Choice(["critical", "high", "medium", "low"], case_sensitive=False),
    help="Fail with exit code 1 if findings match severity",
)
@click.pass_context
def scan_terraform(
    ctx: click.Context,
    path: Path,
    scanner: str,
    output_format: str,
    output: Optional[str],
    fail_on: Optional[str],
) -> None:
    """
    Scan Terraform files for security issues.

    Example:
        devcrew-security scan terraform ./infrastructure --scanner tfsec
        devcrew-security scan terraform ./terraform --format json -o report.json
    """
    scanners_to_run = (
        [ScannerType.CHECKOV, ScannerType.TFSEC, ScannerType.TERRASCAN]
        if scanner == "all"
        else [ScannerType[scanner.upper()]]
    )

    all_findings: List[IaCFinding] = []

    with create_progress() as progress:
        task = progress.add_task(
            "[cyan]Scanning Terraform files...", total=len(scanners_to_run) * 100
        )

        try:
            iac_scanner = IaCScanner()

            for scanner_type in scanners_to_run:
                progress.update(
                    task, description=f"[cyan]Running {scanner_type.value}..."
                )

                findings = iac_scanner.scan(
                    iac_type=IaCType.TERRAFORM,
                    path=path,
                    scanner=scanner_type,
                )

                all_findings.extend(findings)
                progress.update(task, advance=100)

        except Exception as e:
            handle_error(f"Terraform scan failed: {e}", EXIT_SCAN_ERROR)

    # Display results
    if output_format == "table":
        display_findings_table(all_findings, f"Terraform Scan: {path}")
        console.print(
            f"\n[bold]Summary:[/bold] {len(all_findings)} findings from "
            f"{len(scanners_to_run)} scanner(s)"
        )
    else:
        output_data = [
            f.to_dict() if hasattr(f, "to_dict") else f for f in all_findings
        ]
        if output_format == "json":
            if output:
                save_output(output_data, output, "json", "terraform-scan")
            else:
                console.print_json(data=output_data)
        elif output_format == "sarif":
            aggregator = ReportAggregator()
            sarif = aggregator.to_sarif(output_data)
            save_output(sarif, output, "sarif", "terraform-scan")

    # Check fail-on criteria
    if fail_on:
        check_fail_on_severity(all_findings, fail_on, ctx)


@scan.command(name="cloudformation")
@click.argument("template", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "sarif", "table"], case_sensitive=False),
    default="table",
    help="Output format",
)
@click.option("--output", "-o", type=str, help="Output file path")
@click.option(
    "--fail-on",
    type=click.Choice(["critical", "high", "medium", "low"], case_sensitive=False),
    help="Fail with exit code 1 if findings match severity",
)
@click.pass_context
def scan_cloudformation(
    ctx: click.Context,
    template: Path,
    output_format: str,
    output: Optional[str],
    fail_on: Optional[str],
) -> None:
    """
    Scan CloudFormation template for security issues.

    Example:
        devcrew-security scan cloudformation template.yaml
        devcrew-security scan cloudformation stack.json --format json
    """
    with create_progress() as progress:
        task = progress.add_task(
            "[cyan]Scanning CloudFormation template...", total=100
        )

        try:
            scanner = IaCScanner()
            findings = scanner.scan(
                iac_type=IaCType.CLOUDFORMATION,
                path=template,
                scanner=ScannerType.CHECKOV,
            )
            progress.update(task, advance=100)

        except Exception as e:
            handle_error(f"CloudFormation scan failed: {e}", EXIT_SCAN_ERROR)

    # Display results
    if output_format == "table":
        display_findings_table(findings, f"CloudFormation: {template}")
        console.print(f"\n[bold]Summary:[/bold] {len(findings)} findings")
    else:
        output_data = [
            f.to_dict() if hasattr(f, "to_dict") else f for f in findings
        ]
        if output_format == "json":
            if output:
                save_output(output_data, output, "json", "cloudformation-scan")
            else:
                console.print_json(data=output_data)
        elif output_format == "sarif":
            aggregator = ReportAggregator()
            sarif = aggregator.to_sarif(output_data)
            save_output(sarif, output, "sarif", "cloudformation-scan")

    # Check fail-on criteria
    if fail_on:
        check_fail_on_severity(findings, fail_on, ctx)


@scan.command(name="kubernetes")
@click.argument("manifest", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "sarif", "table"], case_sensitive=False),
    default="table",
    help="Output format",
)
@click.option("--output", "-o", type=str, help="Output file path")
@click.option(
    "--fail-on",
    type=click.Choice(["critical", "high", "medium", "low"], case_sensitive=False),
    help="Fail with exit code 1 if findings match severity",
)
@click.pass_context
def scan_kubernetes(
    ctx: click.Context,
    manifest: Path,
    output_format: str,
    output: Optional[str],
    fail_on: Optional[str],
) -> None:
    """
    Scan Kubernetes manifest for security issues.

    Example:
        devcrew-security scan kubernetes deployment.yaml
        devcrew-security scan kubernetes manifests/ --format json
    """
    with create_progress() as progress:
        task = progress.add_task(
            "[cyan]Scanning Kubernetes manifest...", total=100
        )

        try:
            scanner = IaCScanner()
            findings = scanner.scan(
                iac_type=IaCType.KUBERNETES,
                path=manifest,
                scanner=ScannerType.CHECKOV,
            )
            progress.update(task, advance=100)

        except Exception as e:
            handle_error(f"Kubernetes scan failed: {e}", EXIT_SCAN_ERROR)

    # Display results
    if output_format == "table":
        display_findings_table(findings, f"Kubernetes: {manifest}")
        console.print(f"\n[bold]Summary:[/bold] {len(findings)} findings")
    else:
        output_data = [
            f.to_dict() if hasattr(f, "to_dict") else f for f in findings
        ]
        if output_format == "json":
            if output:
                save_output(output_data, output, "json", "kubernetes-scan")
            else:
                console.print_json(data=output_data)
        elif output_format == "sarif":
            aggregator = ReportAggregator()
            sarif = aggregator.to_sarif(output_data)
            save_output(sarif, output, "sarif", "kubernetes-scan")

    # Check fail-on criteria
    if fail_on:
        check_fail_on_severity(findings, fail_on, ctx)


@scan.command(name="cloud")
@click.argument(
    "provider",
    type=click.Choice(["aws", "azure", "gcp"], case_sensitive=False),
)
@click.option(
    "--service",
    type=str,
    multiple=True,
    help="Specific services to scan (can be repeated)",
)
@click.option("--region", type=str, multiple=True, help="Regions to scan")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "sarif", "table"], case_sensitive=False),
    default="table",
    help="Output format",
)
@click.option("--output", "-o", type=str, help="Output file path")
@click.option(
    "--fail-on",
    type=click.Choice(["critical", "high", "medium", "low"], case_sensitive=False),
    help="Fail with exit code 1 if findings match severity",
)
@click.pass_context
def scan_cloud(
    ctx: click.Context,
    provider: str,
    service: Tuple[str, ...],
    region: Tuple[str, ...],
    output_format: str,
    output: Optional[str],
    fail_on: Optional[str],
) -> None:
    """
    Scan live cloud infrastructure for security issues.

    Example:
        devcrew-security scan cloud aws --service s3 --region us-east-1
        devcrew-security scan cloud azure --format json -o azure-findings.json
    """
    config = load_config(ctx)
    provider_enum = CloudProvider[provider.upper()]

    regions_to_scan = list(region) if region else config.get("cloud.regions", [])
    services_to_scan = list(service) if service else []

    with create_progress() as progress:
        task = progress.add_task(
            f"[cyan]Scanning {provider.upper()} infrastructure...", total=100
        )

        try:
            scanner = CloudScanner()
            findings = scanner.scan_provider(
                provider=provider_enum,
                regions=regions_to_scan,
                services=services_to_scan,
            )
            progress.update(task, advance=100)

        except Exception as e:
            handle_error(f"Cloud scan failed: {e}", EXIT_SCAN_ERROR)

    # Display results
    if output_format == "table":
        display_findings_table(findings, f"Cloud Scan: {provider.upper()}")
        console.print(f"\n[bold]Summary:[/bold] {len(findings)} findings")
    else:
        output_data = [
            f.to_dict() if hasattr(f, "to_dict") else f for f in findings
        ]
        if output_format == "json":
            if output:
                save_output(output_data, output, "json", f"{provider}-cloud-scan")
            else:
                console.print_json(data=output_data)
        elif output_format == "sarif":
            aggregator = ReportAggregator()
            sarif = aggregator.to_sarif(output_data)
            save_output(sarif, output, "sarif", f"{provider}-cloud-scan")

    # Check fail-on criteria
    if fail_on:
        check_fail_on_severity(findings, fail_on, ctx)


# ============================================================================
# VALIDATE COMMAND GROUP
# ============================================================================


@cli.group()
def validate() -> None:
    """Validate configurations and policies."""
    pass


@validate.command(name="opa")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--data",
    type=click.Path(exists=True, path_type=Path),
    help="Path to data directory",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "table"], case_sensitive=False),
    default="table",
    help="Output format",
)
@click.option("--output", "-o", type=str, help="Output file path")
@click.pass_context
def validate_opa(
    ctx: click.Context,
    path: Path,
    data: Optional[Path],
    output_format: str,
    output: Optional[str],
) -> None:
    """
    Validate OPA (Rego) policies.

    Example:
        devcrew-security validate opa ./policies
        devcrew-security validate opa policy.rego --data ./data
    """
    config = load_config(ctx)
    data_path = data or Path(config.get("opa.data_path", "./policy-data"))

    with create_progress() as progress:
        task = progress.add_task("[cyan]Validating OPA policies...", total=100)

        try:
            validator = PolicyValidator()
            violations = validator.validate_policies(
                policy_path=path,
                engine=PolicyEngine.OPA,
                data_path=data_path,
            )
            progress.update(task, advance=100)

        except Exception as e:
            handle_error(f"OPA validation failed: {e}", EXIT_VALIDATION_FAILED)

    # Display results
    if not violations:
        console.print("[green]All OPA policies are valid![/green]")
        ctx.exit(EXIT_SUCCESS)

    if output_format == "table":
        table = Table(
            title="OPA Policy Violations", show_header=True, header_style="bold red"
        )
        table.add_column("Policy", style="yellow", width=30)
        table.add_column("Rule", style="cyan", width=20)
        table.add_column("Message", style="white", width=50)

        for violation in violations:
            table.add_row(
                getattr(violation, "policy", "N/A"),
                getattr(violation, "rule", "N/A"),
                getattr(violation, "message", "N/A"),
            )

        console.print(table)
        console.print(f"\n[red]{len(violations)} violations found[/red]")
    else:
        output_data = [
            v.to_dict() if hasattr(v, "to_dict") else v for v in violations
        ]
        if output:
            save_output(output_data, output, "json", "opa-validation")
        else:
            console.print_json(data=output_data)

    ctx.exit(EXIT_VALIDATION_FAILED)


@validate.command(name="terraform-plan")
@click.argument("plan_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "table"], case_sensitive=False),
    default="table",
    help="Output format",
)
@click.option("--output", "-o", type=str, help="Output file path")
@click.option(
    "--fail-on",
    type=click.Choice(["critical", "high", "medium", "low"], case_sensitive=False),
    help="Fail with exit code 1 if findings match severity",
)
@click.pass_context
def validate_terraform_plan(
    ctx: click.Context,
    plan_file: Path,
    output_format: str,
    output: Optional[str],
    fail_on: Optional[str],
) -> None:
    """
    Validate Terraform plan file for security issues.

    Example:
        devcrew-security validate terraform-plan tfplan.json
        devcrew-security validate terraform-plan plan.out --format json
    """
    with create_progress() as progress:
        task = progress.add_task("[cyan]Validating Terraform plan...", total=100)

        try:
            scanner = IaCScanner()
            findings = scanner.validate_plan(plan_file)
            progress.update(task, advance=100)

        except Exception as e:
            handle_error(
                f"Terraform plan validation failed: {e}", EXIT_VALIDATION_FAILED
            )

    # Display results
    if not findings:
        console.print("[green]Terraform plan is valid![/green]")
        ctx.exit(EXIT_SUCCESS)

    if output_format == "table":
        display_findings_table(findings, "Terraform Plan Validation")
        console.print(f"\n[bold]Summary:[/bold] {len(findings)} findings")
    else:
        output_data = [
            f.to_dict() if hasattr(f, "to_dict") else f for f in findings
        ]
        if output:
            save_output(output_data, output, "json", "terraform-plan-validation")
        else:
            console.print_json(data=output_data)

    # Check fail-on criteria
    if fail_on:
        check_fail_on_severity(findings, fail_on, ctx)


@validate.command(name="compliance")
@click.argument(
    "framework",
    type=click.Choice(
        ["cis", "nist", "pci-dss", "hipaa", "sox", "gdpr"], case_sensitive=False
    ),
)
@click.argument("scan_results", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "html", "markdown"], case_sensitive=False),
    default="json",
    help="Output format",
)
@click.option("--output", "-o", type=str, help="Output file path")
@click.pass_context
def validate_compliance(
    ctx: click.Context,
    framework: str,
    scan_results: Path,
    output_format: str,
    output: Optional[str],
) -> None:
    """
    Check compliance against security framework.

    Example:
        devcrew-security validate compliance cis scan-results.json
        devcrew-security validate compliance pci-dss results.json --format html
    """
    framework_enum = ComplianceFramework[framework.upper().replace("-", "_")]

    with create_progress() as progress:
        task = progress.add_task(
            f"[cyan]Checking {framework.upper()} compliance...", total=100
        )

        try:
            # Load scan results
            with open(scan_results, "r", encoding="utf-8") as f:
                results = json.load(f)

            validator = PolicyValidator()
            compliance_report = validator.check_compliance(
                framework=framework_enum, findings=results
            )
            progress.update(task, advance=100)

        except Exception as e:
            handle_error(f"Compliance check failed: {e}", EXIT_VALIDATION_FAILED)

    # Display results
    if output_format == "json":
        if output:
            save_output(compliance_report, output, "json", f"{framework}-compliance")
        else:
            console.print_json(data=compliance_report)
    elif output_format == "html":
        aggregator = ReportAggregator()
        html_report = aggregator.generate_html(compliance_report)
        save_output(html_report, output, "html", f"{framework}-compliance")
    elif output_format == "markdown":
        aggregator = ReportAggregator()
        md_report = aggregator.generate_markdown(compliance_report)
        save_output(md_report, output, "md", f"{framework}-compliance")

    # Check compliance status
    passed = compliance_report.get("passed", False)
    if not passed:
        console.print(f"\n[red]{framework.upper()} compliance check failed[/red]")
        ctx.exit(EXIT_VALIDATION_FAILED)
    else:
        console.print(f"\n[green]{framework.upper()} compliance check passed[/green]")


# ============================================================================
# SBOM COMMAND GROUP
# ============================================================================


@cli.group()
def sbom() -> None:
    """Software Bill of Materials (SBOM) operations."""
    pass


@sbom.command(name="generate")
@click.argument("image", type=str)
@click.option(
    "--format",
    "sbom_format",
    type=click.Choice(["cyclonedx", "spdx"], case_sensitive=False),
    default="cyclonedx",
    help="SBOM format",
)
@click.option("--output", "-o", type=str, help="Output file path")
@click.pass_context
def sbom_generate(
    ctx: click.Context,
    image: str,
    sbom_format: str,
    output: Optional[str],
) -> None:
    """
    Generate SBOM for container image.

    Example:
        devcrew-security sbom generate nginx:latest
        devcrew-security sbom generate myapp:v1.0 --format spdx -o sbom.json
    """
    format_enum = SBOMFormat[sbom_format.upper()]

    with create_progress() as progress:
        task = progress.add_task(f"[cyan]Generating SBOM for {image}...", total=100)

        try:
            scanner = ContainerScanner()
            sbom_data = scanner.generate_sbom(image, format_enum)
            progress.update(task, advance=100)

        except Exception as e:
            handle_error(f"SBOM generation failed: {e}", EXIT_SCAN_ERROR)

    # Save or display SBOM
    if output:
        save_output(sbom_data, output, "json", f"sbom-{image.replace(':', '-')}")
    else:
        console.print_json(data=sbom_data)

    console.print(f"\n[green]SBOM generated successfully in {sbom_format}[/green]")


@sbom.command(name="validate")
@click.argument("sbom_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "sbom_format",
    type=click.Choice(["cyclonedx", "spdx"], case_sensitive=False),
    required=True,
    help="SBOM format",
)
@click.pass_context
def sbom_validate(
    ctx: click.Context, sbom_file: Path, sbom_format: str
) -> None:
    """
    Validate SBOM file format.

    Example:
        devcrew-security sbom validate sbom.json --format cyclonedx
        devcrew-security sbom validate package-sbom.json --format spdx
    """
    with create_progress() as progress:
        task = progress.add_task("[cyan]Validating SBOM...", total=100)

        try:
            with open(sbom_file, "r", encoding="utf-8") as f:
                sbom_data = json.load(f)

            # Validate SBOM structure
            if sbom_format == "cyclonedx":
                required_fields = ["bomFormat", "specVersion", "components"]
            else:  # spdx
                required_fields = ["spdxVersion", "creationInfo", "packages"]

            missing_fields = [
                field for field in required_fields if field not in sbom_data
            ]

            progress.update(task, advance=100)

            if missing_fields:
                console.print(
                    f"[red]SBOM validation failed. Missing fields: "
                    f"{', '.join(missing_fields)}[/red]"
                )
                ctx.exit(EXIT_VALIDATION_FAILED)
            else:
                console.print("[green]SBOM is valid![/green]")

        except json.JSONDecodeError as e:
            handle_error(f"Invalid JSON in SBOM file: {e}", EXIT_VALIDATION_FAILED)
        except Exception as e:
            handle_error(f"SBOM validation failed: {e}", EXIT_VALIDATION_FAILED)


# ============================================================================
# REPORT COMMAND GROUP
# ============================================================================


@cli.group()
def report() -> None:
    """Generate and manage security reports."""
    pass


@report.command(name="aggregate")
@click.argument(
    "files",
    nargs=-1,
    required=True,
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "html", "markdown"], case_sensitive=False),
    default="json",
    help="Output format",
)
@click.option("--output", "-o", type=str, required=True, help="Output file path")
@click.option("--title", type=str, help="Report title")
@click.pass_context
def report_aggregate(
    ctx: click.Context,
    files: Tuple[Path, ...],
    output_format: str,
    output: str,
    title: Optional[str],
) -> None:
    """
    Aggregate multiple scan results into single report.

    Example:
        devcrew-security report aggregate scan1.json scan2.json -o combined.json
        devcrew-security report aggregate *.json --format html -o report.html
    """
    with create_progress() as progress:
        task = progress.add_task("[cyan]Aggregating reports...", total=len(files))

        try:
            all_findings = []
            for file_path in files:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_findings.extend(data)
                    else:
                        all_findings.append(data)
                progress.update(task, advance=1)

            aggregator = ReportAggregator()
            report_title = (
                title
                or f"Security Scan Report - {datetime.now().strftime('%Y-%m-%d')}"
            )

            if output_format == "json":
                aggregated = aggregator.aggregate(all_findings, title=report_title)
                save_output(aggregated, output, "json", "aggregated-report")
            elif output_format == "html":
                html_report = aggregator.generate_html(
                    all_findings, title=report_title
                )
                save_output(html_report, output, "html", "aggregated-report")
            elif output_format == "markdown":
                md_report = aggregator.generate_markdown(
                    all_findings, title=report_title
                )
                save_output(md_report, output, "md", "aggregated-report")

        except Exception as e:
            handle_error(f"Report aggregation failed: {e}", EXIT_SCAN_ERROR)

    console.print(
        f"\n[green]Aggregated {len(files)} reports with "
        f"{len(all_findings)} total findings[/green]"
    )


@report.command(name="sarif")
@click.argument("findings_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=str, required=True, help="SARIF output path")
@click.option("--tool-name", type=str, default="DevCrew Security Scanner")
@click.option("--tool-version", type=str, default="1.0.0")
@click.pass_context
def report_sarif(
    ctx: click.Context,
    findings_file: Path,
    output: str,
    tool_name: str,
    tool_version: str,
) -> None:
    """
    Generate SARIF report from findings.

    Example:
        devcrew-security report sarif findings.json -o results.sarif
        devcrew-security report sarif scan.json -o output.sarif --tool-name Custom
    """
    with create_progress() as progress:
        task = progress.add_task("[cyan]Generating SARIF report...", total=100)

        try:
            with open(findings_file, "r", encoding="utf-8") as f:
                findings = json.load(f)

            aggregator = ReportAggregator()
            sarif = aggregator.to_sarif(
                findings, tool_name=tool_name, tool_version=tool_version
            )

            progress.update(task, advance=100)
            save_output(sarif, output, "sarif", "sarif-report")

        except Exception as e:
            handle_error(f"SARIF generation failed: {e}", EXIT_SCAN_ERROR)

    console.print("[green]SARIF report generated successfully[/green]")


@report.command(name="html")
@click.argument("findings_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=str, required=True, help="HTML output path")
@click.option("--title", type=str, help="Report title")
@click.option("--template", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def report_html(
    ctx: click.Context,
    findings_file: Path,
    output: str,
    title: Optional[str],
    template: Optional[Path],
) -> None:
    """
    Generate HTML report from findings.

    Example:
        devcrew-security report html findings.json -o report.html
        devcrew-security report html scan.json -o output.html --title "My Report"
    """
    with create_progress() as progress:
        task = progress.add_task("[cyan]Generating HTML report...", total=100)

        try:
            with open(findings_file, "r", encoding="utf-8") as f:
                findings = json.load(f)

            aggregator = ReportAggregator()
            report_title = (
                title
                or f"Security Report - {datetime.now().strftime('%Y-%m-%d')}"
            )

            html = aggregator.generate_html(
                findings, title=report_title, template_path=template
            )

            progress.update(task, advance=100)
            save_output(html, output, "html", "html-report")

        except Exception as e:
            handle_error(f"HTML generation failed: {e}", EXIT_SCAN_ERROR)

    console.print("[green]HTML report generated successfully[/green]")


@report.command(name="upload-github")
@click.argument("sarif_file", type=click.Path(exists=True, path_type=Path))
@click.option("--repo", required=True, help="Repository (owner/name)")
@click.option("--ref", required=True, help="Git reference (branch/tag)")
@click.option("--commit", required=True, help="Commit SHA")
@click.option("--token", envvar="GITHUB_TOKEN", required=True, help="GitHub token")
@click.pass_context
def report_upload_github(
    ctx: click.Context,
    sarif_file: Path,
    repo: str,
    ref: str,
    commit: str,
    token: str,
) -> None:
    """
    Upload SARIF report to GitHub Code Scanning.

    Example:
        devcrew-security report upload-github results.sarif \\
            --repo owner/repo --ref refs/heads/main --commit abc123
    """
    import requests

    with create_progress() as progress:
        task = progress.add_task("[cyan]Uploading to GitHub...", total=100)

        try:
            with open(sarif_file, "r", encoding="utf-8") as f:
                sarif_content = f.read()

            # GitHub Code Scanning API
            url = f"https://api.github.com/repos/{repo}/code-scanning/sarifs"
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }

            payload = {
                "commit_sha": commit,
                "ref": ref,
                "sarif": sarif_content,
            }

            progress.update(task, advance=50)
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            progress.update(task, advance=50)

        except requests.exceptions.RequestException as e:
            handle_error(f"GitHub upload failed: {e}", EXIT_SCAN_ERROR)
        except Exception as e:
            handle_error(f"Upload failed: {e}", EXIT_SCAN_ERROR)

    console.print("[green]SARIF uploaded to GitHub Code Scanning[/green]")


# ============================================================================
# REMEDIATE COMMAND GROUP
# ============================================================================


@cli.group()
def remediate() -> None:
    """Remediate security findings."""
    pass


@remediate.command(name="auto")
@click.argument("findings_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--dry-run", is_flag=True, help="Show fixes without applying them"
)
@click.option(
    "--severity",
    type=click.Choice(["critical", "high", "medium", "low"], case_sensitive=False),
    multiple=True,
    default=["critical", "high"],
    help="Severities to fix",
)
@click.option("--output", "-o", type=str, help="Output remediation report")
@click.pass_context
def remediate_auto(
    ctx: click.Context,
    findings_file: Path,
    dry_run: bool,
    severity: Tuple[str, ...],
    output: Optional[str],
) -> None:
    """
    Automatically fix security findings.

    Example:
        devcrew-security remediate auto findings.json --dry-run
        devcrew-security remediate auto scan.json --severity critical
    """
    with create_progress() as progress:
        task = progress.add_task("[cyan]Processing fixes...", total=100)

        try:
            with open(findings_file, "r", encoding="utf-8") as f:
                findings = json.load(f)

            # Filter by severity
            filtered_findings = [
                f
                for f in findings
                if f.get("severity", "").lower() in [s.lower() for s in severity]
            ]

            progress.update(task, advance=30)

            engine = RemediationEngine()
            results = engine.auto_fix(filtered_findings, dry_run=dry_run)

            progress.update(task, advance=70)

        except Exception as e:
            handle_error(f"Auto-remediation failed: {e}", EXIT_SCAN_ERROR)

    # Display results
    table = Table(
        title="Remediation Results", show_header=True, header_style="bold cyan"
    )
    table.add_column("Finding ID", style="yellow", width=20)
    table.add_column("Status", style="white", width=15)
    table.add_column("Action", style="dim", width=40)

    for result in results:
        status = (
            "[green]Fixed[/green]"
            if result.get("success")
            else "[red]Failed[/red]"
        )
        table.add_row(
            result.get("finding_id", "N/A"),
            status,
            result.get("action", "N/A"),
        )

    console.print(table)

    if dry_run:
        console.print("\n[yellow]Dry run - no changes applied[/yellow]")

    if output:
        save_output(results, output, "json", "remediation-report")

    success_count = sum(1 for r in results if r.get("success"))
    console.print(
        f"\n[bold]Summary:[/bold] {success_count}/{len(results)} "
        f"findings remediated"
    )


@remediate.command(name="playbook")
@click.argument("finding_id", type=str)
@click.argument("findings_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=str, help="Output playbook file")
@click.pass_context
def remediate_playbook(
    ctx: click.Context,
    finding_id: str,
    findings_file: Path,
    output: Optional[str],
) -> None:
    """
    Generate remediation playbook for specific finding.

    Example:
        devcrew-security remediate playbook CVE-2023-1234 findings.json
        devcrew-security remediate playbook CKV_AWS_1 scan.json -o playbook.yaml
    """
    try:
        with open(findings_file, "r", encoding="utf-8") as f:
            findings = json.load(f)

        # Find specific finding
        finding = next(
            (f for f in findings if f.get("id") == finding_id), None
        )

        if not finding:
            handle_error(f"Finding {finding_id} not found", EXIT_SCAN_ERROR)

        engine = RemediationEngine()
        playbook = engine.generate_playbook(finding)

        if output:
            save_output(playbook, output, "yaml", "remediation-playbook")
        else:
            console.print_json(data=playbook)

        console.print(
            f"\n[green]Playbook generated for {finding_id}[/green]"
        )

    except Exception as e:
        handle_error(f"Playbook generation failed: {e}", EXIT_SCAN_ERROR)


@remediate.command(name="pr")
@click.argument("findings_file", type=click.Path(exists=True, path_type=Path))
@click.option("--repo", required=True, help="Repository path")
@click.option(
    "--branch", help="Branch name (auto-generated if not provided)"
)
@click.option("--title", help="PR title")
@click.option(
    "--severity",
    type=click.Choice(["critical", "high", "medium", "low"], case_sensitive=False),
    multiple=True,
    default=["critical", "high"],
    help="Severities to fix",
)
@click.pass_context
def remediate_pr(
    ctx: click.Context,
    findings_file: Path,
    repo: str,
    branch: Optional[str],
    title: Optional[str],
    severity: Tuple[str, ...],
) -> None:
    """
    Create pull request with security fixes.

    Example:
        devcrew-security remediate pr findings.json --repo ./my-project
        devcrew-security remediate pr scan.json --repo . --severity critical
    """
    config = load_config(ctx)

    try:
        with open(findings_file, "r", encoding="utf-8") as f:
            findings = json.load(f)

        # Filter by severity
        filtered_findings = [
            f
            for f in findings
            if f.get("severity", "").lower() in [s.lower() for s in severity]
        ]

        branch_name = branch or (
            f"{config.get('remediation.git_branch_prefix', 'security-fix/')}"
            f"{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        )

        pr_title = title or (
            f"Security fixes for {len(filtered_findings)} findings"
        )

        with create_progress() as progress:
            task = progress.add_task("[cyan]Creating PR...", total=100)

            engine = RemediationEngine()

            # Create fixes
            progress.update(task, advance=30)
            results = engine.auto_fix(filtered_findings, dry_run=False)

            # Create branch and commit
            progress.update(task, advance=30)
            pr_url = engine.create_pull_request(
                repo_path=repo,
                branch=branch_name,
                title=pr_title,
                findings=filtered_findings,
                fixes=results,
            )

            progress.update(task, advance=40)

        console.print(f"[green]Pull request created:[/green] {pr_url}")

    except Exception as e:
        handle_error(f"PR creation failed: {e}", EXIT_SCAN_ERROR)


# ============================================================================
# CONFIG COMMAND GROUP
# ============================================================================


@cli.group()
def config() -> None:
    """Manage CLI configuration."""
    pass


@config.command(name="show")
@click.option("--key", type=str, help="Show specific configuration key")
@click.pass_context
def config_show(ctx: click.Context, key: Optional[str]) -> None:
    """
    Display current configuration.

    Example:
        devcrew-security config show
        devcrew-security config show --key scan.timeout
    """
    cli_config = load_config(ctx)

    if key:
        value = cli_config.get(key)
        if value is None:
            console.print(f"[yellow]Key '{key}' not found[/yellow]")
        else:
            console.print(f"[cyan]{key}:[/cyan] {value}")
    else:
        console.print(
            Panel(
                yaml.dump(cli_config.config, default_flow_style=False),
                title="DevCrew Security Configuration",
                border_style="cyan",
            )
        )

    console.print(
        f"\n[dim]Config file: {cli_config.config_path.absolute()}[/dim]"
    )


@config.command(name="set")
@click.argument("key", type=str)
@click.argument("value", type=str)
@click.pass_context
def config_set(ctx: click.Context, key: str, value: str) -> None:
    """
    Set configuration value.

    Example:
        devcrew-security config set scan.timeout 900
        devcrew-security config set report.default_format sarif
    """
    cli_config = load_config(ctx)

    # Try to convert value to appropriate type
    try:
        if value.lower() == "true":
            typed_value = True
        elif value.lower() == "false":
            typed_value = False
        elif value.isdigit():
            typed_value = int(value)
        else:
            typed_value = value
    except (ValueError, AttributeError):
        typed_value = value

    cli_config.set(key, typed_value)
    cli_config.save()

    console.print(f"[green]Configuration updated:[/green] {key} = {typed_value}")


@config.command(name="validate")
@click.pass_context
def config_validate(ctx: click.Context) -> None:
    """
    Validate configuration file.

    Example:
        devcrew-security config validate
    """
    cli_config = load_config(ctx)

    with create_progress() as progress:
        task = progress.add_task("[cyan]Validating configuration...", total=100)

        errors = []

        # Validate scan configuration
        timeout = cli_config.get("scan.timeout")
        if timeout and (not isinstance(timeout, int) or timeout < 0):
            errors.append("scan.timeout must be a positive integer")

        # Validate report configuration
        report_format = cli_config.get("report.default_format")
        if report_format and report_format not in ["json", "sarif", "html", "markdown"]:
            errors.append(
                "report.default_format must be json, sarif, html, or markdown"
            )

        progress.update(task, advance=50)

        # Validate cloud configuration
        providers = cli_config.get("cloud.providers")
        if providers:
            valid_providers = ["aws", "azure", "gcp"]
            invalid = [p for p in providers if p not in valid_providers]
            if invalid:
                errors.append(
                    f"Invalid cloud providers: {', '.join(invalid)}"
                )

        progress.update(task, advance=50)

    if errors:
        console.print("[red]Configuration validation failed:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        ctx.exit(EXIT_CONFIG_ERROR)
    else:
        console.print("[green]Configuration is valid![/green]")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main() -> None:
    """Main entry point for CLI."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        if os.getenv("DEBUG"):
            raise
        sys.exit(EXIT_SCAN_ERROR)


if __name__ == "__main__":
    main()
