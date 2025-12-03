#!/usr/bin/env python3
"""
Software Composition Analysis (SCA) Scanner CLI

Comprehensive command-line interface for vulnerability scanning,
SBOM generation, license compliance checking, and supply chain
security analysis.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .dependency_scanner import DependencyScanner, Ecosystem
from .license_checker import LicenseChecker
from .remediation_advisor import RemediationAdvisor
from .sbom_generator import SBOMGenerator
from .supply_chain_analyzer import SupplyChainAnalyzer
from .vulnerability_matcher import VulnerabilityMatcher

# Initialize Rich console
console = Console()

# Logging configuration
logger = logging.getLogger(__name__)


class CLIError(Exception):
    """Base exception for CLI errors."""

    pass


class ConfigurationError(CLIError):
    """Configuration file error."""

    pass


class ValidationError(CLIError):
    """Input validation error."""

    pass


# Severity color mappings
SEVERITY_COLORS = {
    "CRITICAL": "red",
    "HIGH": "bright_red",
    "MEDIUM": "yellow",
    "LOW": "blue",
    "NONE": "dim",
}


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging output.

    Args:
        verbose: Enable debug logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


def load_config(config_path: Optional[Path]) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        ConfigurationError: If config file is invalid
    """
    if not config_path:
        return {}

    if not config_path.exists():
        msg = f"Configuration file not found: {config_path}"
        raise ConfigurationError(msg)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if not isinstance(config, dict):
                raise ConfigurationError("Invalid configuration format")
            return config
    except yaml.YAMLError as e:
        err_msg = f"Failed to parse configuration: {e}"
        raise ConfigurationError(err_msg) from e


def validate_inputs(
    manifest: Optional[Path], path: Optional[Path]
) -> tuple[Optional[Path], Optional[Path]]:
    """
    Validate and normalize input paths.

    Args:
        manifest: Manifest file path
        path: Directory path

    Returns:
        Tuple of (manifest, path)

    Raises:
        ValidationError: If inputs are invalid
    """
    if not manifest and not path:
        raise ValidationError("Either --manifest or --path must be specified")

    if manifest and not manifest.exists():
        raise ValidationError(f"Manifest file not found: {manifest}")

    if path and not path.exists():
        raise ValidationError(f"Directory not found: {path}")

    if path and not path.is_dir():
        raise ValidationError(f"Path is not a directory: {path}")

    return manifest, path


def get_severity_level(severity: str) -> int:
    """Map severity to numeric level for comparison."""
    levels = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
    return levels.get(severity.upper(), 0)


def format_table(
    data: List[Dict[str, Any]], columns: List[Any], title: str = ""
) -> None:
    """
    Display data as a Rich table.

    Args:
        data: List of dictionaries to display
        columns: Column names to display
        title: Table title
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    for col in columns:
        table.add_column(col.upper())

    for row in data:
        values = []
        for col in columns:
            value = str(row.get(col, ""))
            if col == "severity" and value in SEVERITY_COLORS:
                values.append(f"[{SEVERITY_COLORS[value]}]{value}[/]")
            else:
                values.append(value)
        table.add_row(*values)

    console.print(table)


def export_sarif(vulnerabilities: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Export vulnerabilities to SARIF format.

    Args:
        vulnerabilities: List of vulnerability findings
        output_path: Output file path
    """
    sarif: Dict[str, Any] = {
        "$schema": (
            "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/"
            "master/Schemata/sarif-schema-2.1.0.json"
        ),
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "SCA Scanner",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/devCrew_s1",
                    }
                },
                "results": [],
            }
        ],
    }

    for vuln in vulnerabilities:
        result = {
            "ruleId": vuln.get("cve", "UNKNOWN"),
            "level": vuln.get("severity", "warning").lower(),
            "message": {"text": vuln.get("description", "No description available")},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": vuln.get("manifest_file", "unknown")
                        }
                    }
                }
            ],
            "properties": {
                "package": vuln.get("package", "unknown"),
                "version": vuln.get("version", "unknown"),
                "cvss_score": vuln.get("cvss_score"),
            },
        }
        runs_list = sarif["runs"]
        if isinstance(runs_list, list) and len(runs_list) > 0:
            results = runs_list[0].get("results", [])
            if isinstance(results, list):
                results.append(result)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sarif, f, indent=2)

    console.print(f"[green]SARIF report exported to {output_path}[/green]")


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose debug logging")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Software Composition Analysis (SCA) Scanner CLI."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


@cli.command()
@click.option(
    "--manifest",
    type=click.Path(exists=True, path_type=Path),
    help="Manifest file to scan",
)
@click.option(
    "--path",
    type=click.Path(exists=True, path_type=Path),
    help="Directory to scan recursively",
)
@click.option(
    "--ecosystem",
    type=click.Choice(
        ["python", "nodejs", "java", "go", "ruby", "rust"],
        case_sensitive=False,
    ),
    help="Ecosystem filter",
)
@click.option(
    "--severity",
    type=click.Choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"], case_sensitive=False),
    default="LOW",
    help="Minimum severity level",
)
@click.option(
    "--fail-on-severity",
    type=click.Choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"], case_sensitive=False),
    help="Fail if vulnerabilities found at this level",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Output file (JSON)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "sarif", "table"], case_sensitive=False),
    default="table",
    help="Output format",
)
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    help="Cache directory for vulnerability data",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Config file (sca-config.yaml)",
)
@click.pass_context
def scan(
    ctx: click.Context,
    manifest: Optional[Path],
    path: Optional[Path],
    ecosystem: Optional[str],
    severity: str,
    fail_on_severity: Optional[str],
    output: Optional[Path],
    output_format: str,
    cache_dir: Optional[Path],
    config: Optional[Path],
) -> None:
    """
    Scan dependencies for vulnerabilities.

    Examples:
        sca_cli.py scan --manifest requirements.txt
        sca_cli.py scan --path . --ecosystem python
        sca_cli.py scan --path . --fail-on-severity HIGH
    """
    try:
        # Validate inputs
        manifest, path = validate_inputs(manifest, path)

        # Load configuration
        cfg = load_config(config)
        if cache_dir:
            cfg["cache_dir"] = str(cache_dir)

        # Initialize scanners
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing scanners...", total=None)

            # DependencyScanner requires scan_path
            scan_target = manifest if manifest else path
            dep_scanner = DependencyScanner(scan_path=str(scan_target))
            vuln_matcher = VulnerabilityMatcher(config=cfg)

            # Scan dependencies
            progress.update(task, description="Scanning dependencies...")
            dependencies = dep_scanner.scan()

            if not dependencies:
                console.print("[yellow]No dependencies found[/yellow]")
                sys.exit(0)

            # Filter by ecosystem if specified
            if ecosystem:
                ecosystem_enum = Ecosystem(ecosystem.lower())
                dependencies = [
                    d for d in dependencies if d.ecosystem == ecosystem_enum
                ]

            console.print(f"[green]Found {len(dependencies)} dependencies[/green]")

            # Match vulnerabilities
            progress.update(task, description="Matching vulnerabilities...")

            # Convert dependencies to format expected by vulnerability matcher
            deps_for_vuln = [
                {
                    "package": dep.name,
                    "version": dep.version,
                    "ecosystem": dep.ecosystem.value,
                }
                for dep in dependencies
            ]

            vulns_list = vuln_matcher.find_vulnerabilities(deps_for_vuln)

            # Map vulnerabilities back to dependencies and filter
            vulnerabilities = []
            for vuln in vulns_list:
                vuln_severity = vuln.get("severity", "UNKNOWN")
                if get_severity_level(vuln_severity) >= get_severity_level(severity):
                    # Find matching dependency
                    pkg_name = vuln.get("package")
                    dep_match = next(
                        (d for d in dependencies if d.name == pkg_name), None
                    )
                    vuln_data = {
                        "package": pkg_name,
                        "version": vuln.get("version"),
                        "ecosystem": vuln.get("ecosystem"),
                        "manifest_file": (
                            dep_match.manifest_file if dep_match else "unknown"
                        ),
                        "cve": vuln.get("id", "UNKNOWN"),
                        "severity": vuln_severity,
                        "cvss_score": vuln.get("cvss_score"),
                        "description": vuln.get("description", "")[:100],
                        "is_direct": (dep_match.is_direct if dep_match else True),
                    }
                    vulnerabilities.append(vuln_data)

        # Filter by ignored vulnerabilities from config
        ignored_cves = cfg.get("ignored_vulnerabilities", [])
        if ignored_cves:
            vulnerabilities = [
                v for v in vulnerabilities if v["cve"] not in ignored_cves
            ]

        # Summary
        summary: Dict[str, Any] = {
            "total_dependencies": len(dependencies),
            "total_vulnerabilities": len(vulnerabilities),
            "by_severity": {},
        }

        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = sum(1 for v in vulnerabilities if v["severity"] == sev)
            by_sev = summary["by_severity"]
            if isinstance(by_sev, dict):
                by_sev[sev] = count

        # Display results
        if output_format == "table" and vulnerabilities:
            format_table(
                vulnerabilities,
                [
                    "package",
                    "version",
                    "cve",
                    "severity",
                    "cvss_score",
                ],
                title="Vulnerability Scan Results",
            )

        # Print summary
        console.print("\n[bold]Summary:[/bold]")
        total_deps = summary["total_dependencies"]
        console.print(f"  Total Dependencies: {total_deps}")
        total_vulns = summary["total_vulnerabilities"]
        console.print(f"  Total Vulnerabilities: {total_vulns}")
        for sev, count in summary["by_severity"].items():
            color = SEVERITY_COLORS.get(sev, "white")
            if count > 0:
                console.print(f"  [{color}]{sev}: {count}[/{color}]")

        # Export results
        if output:
            if output_format == "sarif":
                export_sarif(vulnerabilities, output)
            else:
                result = {
                    "scan_timestamp": datetime.utcnow().isoformat(),
                    "summary": summary,
                    "vulnerabilities": vulnerabilities,
                }
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                msg = f"Results exported to {output}"
                console.print(f"[green]{msg}[/green]")

        # Check fail condition
        if fail_on_severity and vulnerabilities:
            fail_level = get_severity_level(fail_on_severity)
            has_failure = any(
                get_severity_level(v["severity"]) >= fail_level for v in vulnerabilities
            )
            if has_failure:
                fail_msg = (
                    f"FAIL: Vulnerabilities found at {fail_on_severity} "
                    f"or higher severity"
                )
                console.print(f"\n[red]{fail_msg}[/red]")
                sys.exit(1)

        if vulnerabilities:
            console.print(
                "\n[yellow]Vulnerabilities detected. " "Review and remediate.[/yellow]"
            )
        else:
            console.print("\n[green]No vulnerabilities detected![/green]")

    except (ValidationError, ConfigurationError) as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        logger.exception("Unexpected error during scan")
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)


@cli.command()
@click.option(
    "--manifest",
    type=click.Path(exists=True, path_type=Path),
    help="Manifest file",
)
@click.option(
    "--path",
    type=click.Path(exists=True, path_type=Path),
    help="Directory to scan",
)
@click.option(
    "--format",
    "sbom_format",
    type=click.Choice(["spdx", "cyclonedx"], case_sensitive=False),
    default="spdx",
    help="SBOM format",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output file",
)
@click.option(
    "--sign/--no-sign",
    default=False,
    help="Sign SBOM (default: no)",
)
@click.option(
    "--include-dev",
    is_flag=True,
    help="Include dev dependencies",
)
@click.pass_context
def sbom(
    ctx: click.Context,
    manifest: Optional[Path],
    path: Optional[Path],
    sbom_format: str,
    output: Path,
    sign: bool,
    include_dev: bool,
) -> None:
    """
    Generate Software Bill of Materials (SBOM).

    Examples:
        sca_cli.py sbom --manifest requirements.txt --output sbom.json
        sca_cli.py sbom --path . --format cyclonedx --output sbom.xml
    """
    try:
        # Validate inputs
        manifest, path = validate_inputs(manifest, path)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating SBOM...", total=None)

            # Scan dependencies
            scan_target = manifest if manifest else path
            dep_scanner = DependencyScanner(scan_path=str(scan_target))
            dependencies = dep_scanner.scan()

            if not dependencies:
                console.print("[yellow]No dependencies found[/yellow]")
                sys.exit(0)

            # Convert to dict format
            deps_data = [dep.to_dict() for dep in dependencies]

            # Generate SBOM
            progress.update(task, description="Creating SBOM document...")
            sbom_generator = SBOMGenerator()

            metadata = {
                "name": "SCA-Scanner-SBOM",
                "version": "1.0.0",
                "description": "Software Bill of Materials",
                "created": datetime.utcnow().isoformat(),
                "include_dev": include_dev,
            }

            sbom_doc = sbom_generator.generate(
                dependencies=deps_data,
                metadata=metadata,
                format=sbom_format,
            )

            # Write output
            with open(output, "w", encoding="utf-8") as f:
                if isinstance(sbom_doc, str):
                    f.write(sbom_doc)
                else:
                    json.dump(sbom_doc, f, indent=2)

        console.print(f"[green]SBOM generated successfully: {output}[/green]")
        console.print(f"  Format: {sbom_format.upper()}")
        console.print(f"  Dependencies: {len(dependencies)}")

        if sign:
            console.print("[yellow]Note: SBOM signing not yet implemented[/yellow]")

    except (ValidationError, ConfigurationError) as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        logger.exception("Unexpected error during SBOM generation")
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)


@cli.command()
@click.option(
    "--manifest",
    type=click.Path(exists=True, path_type=Path),
    help="Manifest file",
)
@click.option(
    "--path",
    type=click.Path(exists=True, path_type=Path),
    help="Directory to scan",
)
@click.option(
    "--policy",
    type=click.Path(exists=True, path_type=Path),
    help="License policy file (license-policy.yaml)",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Output file (CSV or JSON)",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["csv", "json", "table"], case_sensitive=False),
    default="table",
    help="Output format",
)
@click.option(
    "--fail-on-violation",
    is_flag=True,
    help="Exit 1 if policy violations found",
)
@click.pass_context
def licenses(
    ctx: click.Context,
    manifest: Optional[Path],
    path: Optional[Path],
    policy: Optional[Path],
    output: Optional[Path],
    output_format: str,
    fail_on_violation: bool,
) -> None:
    """
    Check license compliance.

    Examples:
        sca_cli.py licenses --manifest requirements.txt
        sca_cli.py licenses --path . --policy license-policy.yaml
        sca_cli.py licenses --path . --fail-on-violation
    """
    try:
        # Validate inputs
        manifest, path = validate_inputs(manifest, path)

        # Load policy
        policy_config = {}
        if policy:
            policy_config = load_config(policy)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Checking licenses...", total=None)

            # Scan dependencies
            scan_target = manifest if manifest else path
            dep_scanner = DependencyScanner(scan_path=str(scan_target))
            dependencies = dep_scanner.scan()

            if not dependencies:
                console.print("[yellow]No dependencies found[/yellow]")
                sys.exit(0)

            # Check licenses
            license_checker = LicenseChecker()

            # Convert dependencies to format expected by license checker
            deps_info = [
                {
                    "name": dep.name,
                    "version": dep.version,
                    "ecosystem": dep.ecosystem.value,
                }
                for dep in dependencies
            ]

            license_results = license_checker.check_licenses(deps_info, policy_config)

        # Analyze results
        violations = [r for r in license_results if r.policy_violation]
        total_licenses = len(license_results)

        # Display results
        if output_format == "table":
            table_data = [
                {
                    "package": r.package,
                    "version": r.version,
                    "license": r.license or "UNKNOWN",
                    "spdx_id": r.spdx_id or "N/A",
                    "policy": r.policy_status.value,
                    "copyleft": "Yes" if r.is_copyleft else "No",
                }
                for r in license_results
            ]
            format_table(
                table_data,
                ["package", "version", "license", "policy", "copyleft"],
                title="License Compliance Report",
            )

        # Print summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Total Packages: {total_licenses}")
        console.print(f"  Policy Violations: {len(violations)}")

        if violations:
            console.print("\n[bold red]Policy Violations:[/bold red]")
            for v in violations:
                console.print(
                    f"  - {v.package}@{v.version}: " f"{v.license} ({v.recommendation})"
                )

        # Export results
        if output:
            if output_format == "csv":
                import csv

                with open(output, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=[
                            "package",
                            "version",
                            "license",
                            "spdx_id",
                            "policy_status",
                            "copyleft",
                        ],
                    )
                    writer.writeheader()
                    for r in license_results:
                        writer.writerow(
                            {
                                "package": r.package,
                                "version": r.version,
                                "license": r.license or "UNKNOWN",
                                "spdx_id": r.spdx_id or "",
                                "policy_status": r.policy_status.value,
                                "copyleft": r.is_copyleft,
                            }
                        )
            else:
                # JSON output
                output_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "summary": {
                        "total_packages": total_licenses,
                        "violations": len(violations),
                    },
                    "licenses": [
                        {
                            "package": r.package,
                            "version": r.version,
                            "license": r.license,
                            "spdx_id": r.spdx_id,
                            "policy_status": r.policy_status.value,
                            "is_copyleft": r.is_copyleft,
                            "policy_violation": r.policy_violation,
                        }
                        for r in license_results
                    ],
                }
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, indent=2)

            console.print(f"[green]Results exported to {output}[/green]")

        # Check fail condition
        if fail_on_violation and violations:
            console.print("\n[red]FAIL: License policy violations detected[/red]")
            sys.exit(1)

        if violations:
            msg = "License violations detected. Review required."
            console.print(f"\n[yellow]{msg}[/yellow]")
        else:
            console.print("\n[green]All licenses comply with policy![/green]")

    except (ValidationError, ConfigurationError) as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        logger.exception("Unexpected error during license check")
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)


@cli.command()
@click.option(
    "--cve",
    required=True,
    help="CVE identifier (e.g., CVE-2023-12345)",
)
@click.option(
    "--status",
    type=click.Choice(
        ["fixed", "not_affected", "under_investigation"],
        case_sensitive=False,
    ),
    required=True,
    help="VEX status",
)
@click.option(
    "--product",
    required=True,
    help="Product PURL (e.g., pkg:pypi/package@1.0.0)",
)
@click.option(
    "--justification",
    required=True,
    help="Justification text",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output file (JSON)",
)
@click.pass_context
def vex(
    ctx: click.Context,
    cve: str,
    status: str,
    product: str,
    justification: str,
    output: Path,
) -> None:
    """
    Generate Vulnerability Exploitability eXchange (VEX) document.

    Examples:
        sca_cli.py vex --cve CVE-2023-12345 --status not_affected \\
            --product pkg:pypi/requests@2.28.0 \\
            --justification "Vulnerable code path not used" \\
            --output vex.json
    """
    try:
        # Validate CVE format
        if not cve.upper().startswith("CVE-"):
            raise ValidationError("CVE must start with 'CVE-' (e.g., CVE-2023-12345)")

        # Create VEX document
        vex_doc = {
            "@context": "https://openvex.dev/ns",
            "@id": f"https://openvex.dev/docs/{cve.lower()}",
            "author": "SCA Scanner",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1",
            "statements": [
                {
                    "vulnerability": cve.upper(),
                    "products": [product],
                    "status": status,
                    "justification": justification,
                }
            ],
        }

        # Write VEX document
        with open(output, "w", encoding="utf-8") as f:
            json.dump(vex_doc, f, indent=2)

        console.print(f"[green]VEX document generated: {output}[/green]")
        console.print(f"  CVE: {cve.upper()}")
        console.print(f"  Status: {status}")
        console.print(f"  Product: {product}")

    except ValidationError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        logger.exception("Unexpected error during VEX generation")
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)


@cli.command()
@click.option(
    "--manifest",
    type=click.Path(exists=True, path_type=Path),
    help="Manifest file",
)
@click.option(
    "--path",
    type=click.Path(exists=True, path_type=Path),
    help="Directory to scan",
)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default=Path("sca-reports"),
    help="Output directory for reports",
)
@click.option(
    "--format",
    "formats",
    default="json,html",
    help="Report formats (comma-separated: html,json,sarif,pdf)",
)
@click.option(
    "--include-all",
    is_flag=True,
    help="Include vuln, sbom, license, and supply-chain analysis",
)
@click.option(
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Config file (sca-config.yaml)",
)
@click.pass_context
def report(
    ctx: click.Context,
    manifest: Optional[Path],
    path: Optional[Path],
    output_dir: Path,
    formats: str,
    include_all: bool,
    config: Optional[Path],
) -> None:
    """
    Generate comprehensive security report.

    Examples:
        sca_cli.py report --manifest requirements.txt --include-all
        sca_cli.py report --path . --format html,json,sarif
    """
    try:
        # Validate inputs
        manifest, path = validate_inputs(manifest, path)

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Parse formats
        format_list = [f.strip().lower() for f in formats.split(",")]
        supported = {"html", "json", "sarif", "pdf"}
        invalid = set(format_list) - supported
        if invalid:
            invalid_str = ", ".join(invalid)
            raise ValidationError(f"Unsupported formats: {invalid_str}")

        # Load configuration
        cfg = load_config(config)

        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Scan dependencies
            task = progress.add_task("Scanning dependencies...", total=None)
            scan_target = manifest if manifest else path
            dep_scanner = DependencyScanner(scan_path=str(scan_target))
            dependencies = dep_scanner.scan()

            if not dependencies:
                console.print("[yellow]No dependencies found[/yellow]")
                sys.exit(0)

            report_data: Dict[str, Any] = {
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "scan_target": str(manifest or path),
                    "total_dependencies": len(dependencies),
                },
                "dependencies": [dep.to_dict() for dep in dependencies],
            }

            # Vulnerability scan
            if include_all:
                progress.update(task, description="Scanning vulnerabilities...")
                vuln_matcher = VulnerabilityMatcher(config=cfg)

                # Convert dependencies for vuln matcher
                deps_for_vuln = [
                    {
                        "package": dep.name,
                        "version": dep.version,
                        "ecosystem": dep.ecosystem.value,
                    }
                    for dep in dependencies
                ]

                vulnerabilities = vuln_matcher.find_vulnerabilities(deps_for_vuln)

                report_data["vulnerabilities"] = vulnerabilities

                # Get remediation advice
                progress.update(task, description="Generating remediation...")
                remediation_advisor = RemediationAdvisor()
                remediations = []

                for dep in dependencies:
                    dep_vulns = [
                        v for v in vulnerabilities if v.get("package") == dep.name
                    ]
                    if dep_vulns:
                        for vuln in dep_vulns:
                            remediation_dict = remediation_advisor.get_remediation(
                                vulnerability=vuln,
                                dependency={
                                    "name": dep.name,
                                    "version": dep.version,
                                    "is_direct": dep.is_direct,
                                },
                                ecosystem=dep.ecosystem.value,
                            )
                            if remediation_dict:
                                remediations.append(remediation_dict)

                report_data["remediations"] = remediations

                # License check
                progress.update(task, description="Checking licenses...")
                license_checker = LicenseChecker()
                deps_info = [
                    {
                        "name": dep.name,
                        "version": dep.version,
                        "ecosystem": dep.ecosystem.value,
                    }
                    for dep in dependencies
                ]
                license_results = license_checker.check_licenses(
                    deps_info, cfg.get("policy", {})
                )
                report_data["licenses"] = [
                    {
                        "package": r.package,
                        "version": r.version,
                        "license": r.license,
                        "policy_status": r.policy_status.value,
                        "is_copyleft": r.is_copyleft,
                    }
                    for r in license_results
                ]

                # Supply chain analysis
                progress.update(task, description="Analyzing supply chain...")
                supply_chain = SupplyChainAnalyzer()
                sc_deps = [
                    {
                        "name": dep.name,
                        "version": dep.version,
                        "ecosystem": dep.ecosystem.value,
                    }
                    for dep in dependencies
                ]
                sc_results = supply_chain.analyze(sc_deps)
                report_data["supply_chain"] = sc_results

        # Generate reports in requested formats
        console.print("\n[bold]Generating reports:[/bold]")

        if "json" in format_list:
            json_path = output_dir / f"sca-report-{timestamp}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)
            console.print(f"  [green]JSON: {json_path}[/green]")

        if "sarif" in format_list and "vulnerabilities" in report_data:
            sarif_path = output_dir / f"sca-report-{timestamp}.sarif"
            export_sarif(report_data["vulnerabilities"], sarif_path)

        if "html" in format_list:
            html_path = output_dir / f"sca-report-{timestamp}.html"
            generate_html_report(report_data, html_path)
            console.print(f"  [green]HTML: {html_path}[/green]")

        if "pdf" in format_list:
            console.print("  [yellow]PDF generation not yet implemented[/yellow]")

        console.print(f"\n[green]Reports generated in {output_dir}[/green]")

    except (ValidationError, ConfigurationError) as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        logger.exception("Unexpected error during report generation")
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(2)


def generate_html_report(data: Dict[str, Any], output_path: Path) -> None:
    """
    Generate HTML report.

    Args:
        data: Report data
        output_path: Output file path
    """
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>SCA Security Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #ddd; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .critical {{ color: red; font-weight: bold; }}
        .high {{ color: orange; font-weight: bold; }}
        .medium {{ color: #f0ad4e; }}
        .low {{ color: blue; }}
        .summary {{ background: #f9f9f9; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>Software Composition Analysis Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Scan Date:</strong> {timestamp}</p>
        <p><strong>Target:</strong> {target}</p>
        <p><strong>Total Dependencies:</strong> {total_deps}</p>
        {vuln_summary}
    </div>

    {vulnerabilities_section}
    {licenses_section}
    {supply_chain_section}
</body>
</html>
"""

    metadata = data.get("metadata", {})
    vulnerabilities = data.get("vulnerabilities", [])
    licenses = data.get("licenses", [])

    # Vulnerability summary
    vuln_summary = ""
    if vulnerabilities:
        severity_counts: Dict[str, int] = {}
        for v in vulnerabilities:
            sev = v.get("severity", "UNKNOWN")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        vuln_summary = "<p><strong>Vulnerabilities:</strong></p><ul>"
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = severity_counts.get(sev, 0)
            if count > 0:
                vuln_summary += f'<li class="{sev.lower()}">{sev}: {count}</li>'
        vuln_summary += "</ul>"

    # Vulnerabilities section
    vuln_section = ""
    if vulnerabilities:
        vuln_section = "<h2>Vulnerabilities</h2><table>"
        vuln_section += (
            "<tr><th>Package</th><th>Version</th><th>CVE</th>"
            "<th>Severity</th><th>CVSS</th></tr>"
        )
        for v in vulnerabilities:
            sev_class = v.get("severity", "").lower()
            vuln_section += (
                f"<tr><td>{v.get('package', '')}</td>"
                f"<td>{v.get('version', '')}</td>"
                f"<td>{v.get('id', '')}</td>"
                f'<td class="{sev_class}">{v.get("severity", "")}</td>'
                f"<td>{v.get('cvss_score', 'N/A')}</td></tr>"
            )
        vuln_section += "</table>"

    # Licenses section
    license_section = ""
    if licenses:
        license_section = "<h2>Licenses</h2><table>"
        license_section += (
            "<tr><th>Package</th><th>Version</th>"
            "<th>License</th><th>Policy</th></tr>"
        )
        for lic in licenses:
            license_section += (
                f"<tr><td>{lic.get('package', '')}</td>"
                f"<td>{lic.get('version', '')}</td>"
                f"<td>{lic.get('license', 'UNKNOWN')}</td>"
                f"<td>{lic.get('policy_status', 'unknown')}</td></tr>"
            )
        license_section += "</table>"

    # Supply chain section
    sc_section = ""
    if "supply_chain" in data:
        sc_section = "<h2>Supply Chain Analysis</h2>"
        sc_section += "<p>Supply chain analysis completed.</p>"

    html_content = html_template.format(
        timestamp=metadata.get("timestamp", "Unknown"),
        target=metadata.get("scan_target", "Unknown"),
        total_deps=metadata.get("total_dependencies", 0),
        vuln_summary=vuln_summary,
        vulnerabilities_section=vuln_section,
        licenses_section=license_section,
        supply_chain_section=sc_section,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)


if __name__ == "__main__":
    cli(obj={})  # pylint: disable=no-value-for-parameter
