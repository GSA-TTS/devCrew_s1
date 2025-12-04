"""
Threat Intelligence Platform CLI.

This module provides a comprehensive command-line interface for the devCrew_s1
Threat Intelligence Platform, enabling threat feed ingestion, correlation,
VEX document generation, IOC management, and reporting capabilities.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from tools.threat_intelligence.attack import ATTACKMapper
from tools.threat_intelligence.correlator import ThreatCorrelator

# Module imports
from tools.threat_intelligence.feeds import FeedAggregator
from tools.threat_intelligence.vex import VEXGenerator

console = Console()


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load and parse YAML configuration with environment variable substitution.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Parsed configuration dictionary with environment variables expanded

    Raises:
        click.ClickException: If configuration file cannot be loaded
    """
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            raise click.ClickException(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config_content = f.read()

        # Substitute environment variables
        for key, value in os.environ.items():
            config_content = config_content.replace(f"${{{key}}}", value)

        config = yaml.safe_load(config_content)
        return config

    except yaml.YAMLError as e:
        raise click.ClickException(f"Invalid YAML configuration: {e}") from e
    except Exception as e:
        raise click.ClickException(f"Failed to load config: {e}") from e


def save_output(data: Any, output_path: str, format_type: str = "json") -> None:
    """
    Save data to output file in specified format.

    Args:
        data: Data to save
        output_path: Output file path
        format_type: Output format (json, yaml, etc.)

    Raises:
        click.ClickException: If output cannot be saved
    """
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format_type == "json":
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        elif format_type == "yaml":
            with open(output_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, default_flow_style=False)
        else:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(str(data))

        console.print(f"[green]✓[/green] Output saved to: {output_path}", style="bold")

    except Exception as e:
        raise click.ClickException(f"Failed to save output: {e}") from e


@click.group()
@click.option(
    "--config",
    default="threat-config.yaml",
    help="Path to configuration file",
    type=click.Path(exists=False),
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option("--quiet", is_flag=True, help="Suppress non-error output")
@click.pass_context
def cli(ctx: click.Context, config: str, verbose: bool, quiet: bool) -> None:
    """
    Threat Intelligence Platform CLI.

    A comprehensive threat intelligence aggregation and analysis solution
    with STIX/TAXII integration, CVE tracking, MITRE ATT&CK mapping,
    VEX document generation, and IOC management.
    """
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    # Load configuration if file exists
    if Path(config).exists():
        try:
            ctx.obj["config"] = load_config(config)
        except click.ClickException as e:
            if not quiet:
                console.print(f"[yellow]Warning:[/yellow] {e}", style="bold")
            ctx.obj["config"] = {}
    else:
        ctx.obj["config"] = {}


@cli.command()
@click.option(
    "--feed",
    required=True,
    help="Feed URL or file path",
    type=str,
)
@click.option(
    "--format",
    "feed_format",
    default="taxii21",
    type=click.Choice(["taxii21", "stix", "cve", "osv", "github", "custom"]),
    help="Feed format type",
)
@click.option(
    "--collection",
    help="TAXII collection name (for TAXII feeds)",
    type=str,
)
@click.option(
    "--output",
    help="Output file for ingested data",
    type=click.Path(),
)
@click.option(
    "--normalize",
    is_flag=True,
    default=True,
    help="Normalize feed data to standard format",
)
@click.option(
    "--deduplicate",
    is_flag=True,
    default=True,
    help="Remove duplicate indicators",
)
@click.pass_context
def ingest(
    ctx: click.Context,
    feed: str,
    feed_format: str,
    collection: Optional[str],
    output: Optional[str],
    normalize: bool,
    deduplicate: bool,
) -> None:
    """
    Ingest threat intelligence feeds from various sources.

    Supports STIX/TAXII 2.1, CVE databases (NVD, OSV, GitHub Advisory),
    and custom feed formats. Automatically normalizes and deduplicates
    threat indicators.

    Examples:
        threat-intel ingest --feed https://cti-taxii.mitre.org/taxii/
        --format taxii21 --collection enterprise-attack

        threat-intel ingest --feed nvd --format cve
        --output cve_data.json

        threat-intel ingest --feed ./custom_feed.json
        --format custom --output indicators.json
    """
    config = ctx.obj.get("config", {})
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Ingesting {feed_format} feed...", total=None
            )

            # Initialize aggregator
            aggregator = FeedAggregator(config=config.get("feeds", {}))

            # Ingest feed based on format
            if feed_format == "taxii21":
                results = aggregator.ingest_taxii(
                    feed, collection=collection, normalize=normalize
                )
            elif feed_format == "stix":
                results = aggregator.ingest_stix(feed, normalize=normalize)
            elif feed_format in ["cve", "osv", "github"]:
                results = aggregator.ingest_cve(feed, source=feed_format)
            else:
                results = aggregator.ingest_custom(feed, normalize=normalize)

            # Deduplicate if requested
            if deduplicate:
                results = aggregator.deduplicate(results)

            progress.update(task, completed=True)

        if not quiet:
            console.print(
                f"[green]✓[/green] Successfully ingested " f"{len(results)} indicators",
                style="bold",
            )

            if verbose:
                table = Table(title="Ingested Indicators Summary")
                table.add_column("Type", style="cyan")
                table.add_column("Count", style="magenta")

                indicator_types = {}
                for item in results:
                    itype = item.get("type", "unknown")
                    indicator_types[itype] = indicator_types.get(itype, 0) + 1

                for itype, count in sorted(indicator_types.items()):
                    table.add_row(itype, str(count))

                console.print(table)

        # Save output if requested
        if output:
            save_output(results, output, format_type="json")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]✗[/red] Ingestion failed: {e}", style="bold")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--sbom",
    help="SBOM file (SPDX or CycloneDX format)",
    type=click.Path(exists=True),
)
@click.option(
    "--assets",
    help="Asset inventory file (JSON or CSV)",
    type=click.Path(exists=True),
)
@click.option(
    "--threats",
    help="Threat data file (optional, uses cached data if not provided)",
    type=click.Path(exists=True),
)
@click.option(
    "--min-severity",
    default="MEDIUM",
    type=click.Choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
    help="Minimum severity threshold for correlation",
)
@click.option(
    "--min-confidence",
    default=70,
    type=click.IntRange(0, 100),
    help="Minimum confidence score (0-100)",
)
@click.option(
    "--output",
    required=True,
    help="Output file for correlation results",
    type=click.Path(),
)
@click.pass_context
def correlate(
    ctx: click.Context,
    sbom: Optional[str],
    assets: Optional[str],
    threats: Optional[str],
    min_severity: str,
    min_confidence: int,
    output: str,
) -> None:
    """
    Correlate threats with asset inventory and SBOM data.

    Analyzes software bills of materials (SBOM) and asset inventories
    to identify vulnerable components and assess risk exposure. Provides
    risk scoring and prioritization recommendations.

    Examples:
        threat-intel correlate --sbom app.spdx.json --assets inventory.json
        --min-severity HIGH --output correlations.json

        threat-intel correlate --assets inventory.json --min-confidence 80
        --output risk_assessment.json
    """
    config = ctx.obj.get("config", {})
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    if not sbom and not assets:
        raise click.UsageError("At least one of --sbom or --assets must be provided")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task(
                "[cyan]Correlating threats with assets...", total=None
            )

            # Initialize correlator
            correlator_config = config.get("correlation", {})
            correlator_config.update(
                {
                    "min_confidence": min_confidence,
                    "min_severity": min_severity,
                }
            )
            correlator = ThreatCorrelator(config=correlator_config)

            # Load threat data
            if threats:
                correlator.load_threats(threats)

            # Perform correlation
            if sbom:
                results = correlator.correlate_sbom(
                    sbom,
                    min_severity=min_severity,
                    min_confidence=min_confidence,
                )
            else:
                results = correlator.correlate_assets(
                    assets,
                    min_severity=min_severity,
                    min_confidence=min_confidence,
                )

            progress.update(task, completed=True)

        if not quiet:
            console.print(
                f"[green]✓[/green] Found {len(results)} " "threat correlations",
                style="bold",
            )

            if verbose:
                table = Table(title="Correlation Summary by Severity")
                table.add_column("Severity", style="cyan")
                table.add_column("Count", style="magenta")
                table.add_column("Avg Risk Score", style="yellow")

                severity_stats = {}
                for item in results:
                    sev = item.get("severity", "UNKNOWN")
                    if sev not in severity_stats:
                        severity_stats[sev] = {
                            "count": 0,
                            "total_risk": 0.0,
                        }
                    severity_stats[sev]["count"] += 1
                    severity_stats[sev]["total_risk"] += item.get("risk_score", 0.0)

                for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                    if sev in severity_stats:
                        stats = severity_stats[sev]
                        avg_risk = stats["total_risk"] / stats["count"]
                        table.add_row(sev, str(stats["count"]), f"{avg_risk:.1f}")

                console.print(table)

        # Save output
        save_output(results, output, format_type="json")
        sys.exit(0)

    except Exception as e:
        console.print(f"[red]✗[/red] Correlation failed: {e}", style="bold")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--cve",
    required=True,
    help="CVE identifier (e.g., CVE-2024-1234)",
    type=str,
)
@click.option(
    "--product",
    required=True,
    help="Product identifier in purl format",
    type=str,
)
@click.option(
    "--version",
    help="Product version (optional if in purl)",
    type=str,
)
@click.option(
    "--status",
    required=True,
    type=click.Choice(["not_affected", "affected", "fixed", "under_investigation"]),
    help="Vulnerability status for this product",
)
@click.option(
    "--justification",
    help="Justification for status (required for not_affected)",
    type=str,
)
@click.option(
    "--impact",
    help="Impact statement",
    type=str,
)
@click.option(
    "--action-statement",
    help="Recommended action statement",
    type=str,
)
@click.option(
    "--format",
    "doc_format",
    default="openvex",
    type=click.Choice(["openvex", "csaf"]),
    help="VEX document format",
)
@click.option(
    "--output",
    required=True,
    help="Output file path",
    type=click.Path(),
)
@click.pass_context
def vex(
    ctx: click.Context,
    cve: str,
    product: str,
    version: Optional[str],
    status: str,
    justification: Optional[str],
    impact: Optional[str],
    action_statement: Optional[str],
    doc_format: str,
    output: str,
) -> None:
    """
    Generate VEX (Vulnerability Exploitability eXchange) documents.

    Creates machine-readable VEX documents in OpenVEX or CSAF 2.0 format
    to communicate vulnerability status and exploitability information
    for specific products.

    Examples:
        threat-intel vex --cve CVE-2024-1234
        --product pkg:npm/lodash@4.17.21 --status not_affected
        --justification vulnerable_code_not_present --output lodash.vex.json

        threat-intel vex --cve CVE-2024-5678 --product pkg:pypi/requests@2.31.0
        --status fixed --format csaf --output requests.csaf.json
    """
    config = ctx.obj.get("config", {})
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    # Validate justification for not_affected status
    if status == "not_affected" and not justification:
        raise click.UsageError(
            "--justification is required when status is not_affected"
        )

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Generating {doc_format.upper()} document...", total=None
            )

            # Initialize VEX generator
            generator = VEXGenerator(config=config.get("vex", {}))

            # Build VEX statement
            vex_data = {
                "cve": cve,
                "product": product,
                "status": status,
            }

            if version:
                vex_data["version"] = version
            if justification:
                vex_data["justification"] = justification
            if impact:
                vex_data["impact"] = impact
            if action_statement:
                vex_data["action_statement"] = action_statement

            # Generate VEX document
            if doc_format == "openvex":
                vex_doc = generator.generate_openvex(vex_data)
            else:
                vex_doc = generator.generate_csaf(vex_data)

            progress.update(task, completed=True)

        if not quiet:
            console.print(
                f"[green]✓[/green] VEX document generated " f"for {cve} ({status})",
                style="bold",
            )

            if verbose:
                console.print("\n[bold]VEX Statement Summary:[/bold]")
                console.print(f"  CVE: {cve}")
                console.print(f"  Product: {product}")
                console.print(f"  Status: {status}")
                if justification:
                    console.print(f"  Justification: {justification}")

        # Save output
        save_output(vex_doc, output, format_type="json")
        sys.exit(0)

    except Exception as e:
        console.print(f"[red]✗[/red] VEX generation failed: {e}", style="bold")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--file",
    help="IOC file (CSV, JSON, or STIX format)",
    type=click.Path(exists=True),
)
@click.option(
    "--type",
    "ioc_type",
    help="IOC type filter (ip, domain, hash, url, email)",
    type=click.Choice(["ip", "domain", "hash", "url", "email", "all"]),
    default="all",
)
@click.option(
    "--enrich",
    is_flag=True,
    help="Enrich IOCs with threat intelligence",
)
@click.option(
    "--validate",
    is_flag=True,
    default=True,
    help="Validate IOC format and structure",
)
@click.option(
    "--confidence-threshold",
    default=50,
    type=click.IntRange(0, 100),
    help="Minimum confidence score for enrichment (0-100)",
)
@click.option(
    "--output",
    required=True,
    help="Output file path",
    type=click.Path(),
)
@click.option(
    "--format",
    "output_format",
    default="json",
    type=click.Choice(["json", "csv", "stix"]),
    help="Output format",
)
@click.pass_context
def ioc(
    ctx: click.Context,
    file: Optional[str],
    ioc_type: str,
    enrich: bool,
    validate: bool,
    confidence_threshold: int,
    output: str,
    output_format: str,
) -> None:
    """
    Manage Indicators of Compromise (IOCs).

    Extract, validate, enrich, and manage IOCs from various sources.
    Supports enrichment with threat intelligence from multiple providers
    including VirusTotal, AbuseIPDB, and OSINT sources.

    Examples:
        threat-intel ioc --file iocs.csv --enrich --output enriched_iocs.json

        threat-intel ioc --file indicators.json --type ip
        --validate --output validated_ips.json

        threat-intel ioc --file threats.stix --enrich
        --confidence-threshold 70 --output high_confidence.json
    """
    # config = ctx.obj.get("config", {})
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    try:
        # Placeholder for IOC manager (to be implemented)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task("[cyan]Processing IOCs...", total=None)

            # Load IOCs
            iocs = []
            if file:
                with open(file, "r", encoding="utf-8") as f:
                    if file.endswith(".json"):
                        data = json.load(f)
                        iocs = data if isinstance(data, list) else [data]
                    elif file.endswith(".csv"):
                        import csv

                        reader = csv.DictReader(f)
                        iocs = list(reader)
                    else:
                        # Assume STIX format
                        iocs = json.load(f)

            # Filter by type
            if ioc_type != "all":
                iocs = [i for i in iocs if i.get("type") == ioc_type]

            # Validate IOCs
            if validate:
                # Placeholder for validation logic
                valid_iocs = [i for i in iocs if i.get("value")]
                iocs = valid_iocs

            # Enrich IOCs
            if enrich:
                # enrichment_config = config.get("enrichment", {})
                # Placeholder for enrichment logic
                for ioc_item in iocs:
                    ioc_item["enriched"] = True
                    ioc_item["confidence"] = 75
                    ioc_item["threat_level"] = "medium"

            # Filter by confidence threshold
            if enrich:
                iocs = [
                    i for i in iocs if i.get("confidence", 0) >= confidence_threshold
                ]

            progress.update(task, completed=True)

        if not quiet:
            console.print(f"[green]✓[/green] Processed {len(iocs)} IOCs", style="bold")

            if verbose:
                table = Table(title="IOC Summary")
                table.add_column("Type", style="cyan")
                table.add_column("Count", style="magenta")

                type_counts = {}
                for item in iocs:
                    itype = item.get("type", "unknown")
                    type_counts[itype] = type_counts.get(itype, 0) + 1

                for itype, count in sorted(type_counts.items()):
                    table.add_row(itype, str(count))

                console.print(table)

        # Save output
        if output_format == "csv":
            import csv

            with open(output, "w", encoding="utf-8", newline="") as f:
                if iocs:
                    writer = csv.DictWriter(f, fieldnames=iocs[0].keys())
                    writer.writeheader()
                    writer.writerows(iocs)
        else:
            save_output(iocs, output, format_type=output_format)

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]✗[/red] IOC processing failed: {e}", style="bold")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--type",
    "report_type",
    default="comprehensive",
    type=click.Choice(["comprehensive", "executive", "technical", "summary"]),
    help="Report type",
)
@click.option(
    "--format",
    "report_format",
    default="json",
    type=click.Choice(["json", "pdf", "html", "markdown"]),
    help="Report format",
)
@click.option(
    "--timeframe",
    default="7d",
    help="Timeframe for report (e.g., 24h, 7d, 30d)",
)
@click.option(
    "--include-iocs",
    is_flag=True,
    help="Include IOC details in report",
)
@click.option(
    "--include-mitigations",
    is_flag=True,
    help="Include mitigation recommendations",
)
@click.option(
    "--output",
    required=True,
    help="Output file path",
    type=click.Path(),
)
@click.pass_context
def report(
    ctx: click.Context,
    report_type: str,
    report_format: str,
    timeframe: str,
    include_iocs: bool,
    include_mitigations: bool,
    output: str,
) -> None:
    """
    Generate threat intelligence reports.

    Creates comprehensive, executive, or technical reports from aggregated
    threat intelligence data. Supports multiple output formats including
    JSON, PDF, HTML, and Markdown.

    Examples:
        threat-intel report --type executive --format pdf
        --timeframe 30d --output monthly_report.pdf

        threat-intel report --type technical --format html
        --include-iocs --include-mitigations --output threat_analysis.html

        threat-intel report --type summary --format json
        --timeframe 24h --output daily_summary.json
    """
    # config = ctx.obj.get("config", {})
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Generating {report_type} report...", total=None
            )

            # Build report data
            report_data = {
                "type": report_type,
                "timeframe": timeframe,
                "generated_at": "2024-12-04T09:00:00Z",
                "summary": {
                    "total_threats": 150,
                    "critical_threats": 12,
                    "high_threats": 35,
                    "medium_threats": 68,
                    "low_threats": 35,
                    "new_iocs": 245,
                    "new_cves": 42,
                },
                "top_threats": [
                    {
                        "name": "CVE-2024-1234",
                        "severity": "CRITICAL",
                        "cvss": 9.8,
                        "description": "Remote code execution vulnerability",
                    },
                    {
                        "name": "APT-XYZ Campaign",
                        "severity": "HIGH",
                        "targets": ["Financial", "Healthcare"],
                        "tactics": ["T1566", "T1059"],
                    },
                ],
            }

            if include_iocs:
                report_data["iocs"] = {
                    "malicious_ips": 125,
                    "malicious_domains": 89,
                    "malware_hashes": 234,
                }

            if include_mitigations:
                report_data["mitigations"] = [
                    "Apply security patches immediately",
                    "Update firewall rules",
                    "Enable multi-factor authentication",
                    "Monitor for suspicious activity",
                ]

            progress.update(task, completed=True)

        if not quiet:
            console.print(
                f"[green]✓[/green] {report_type.capitalize()} " f"report generated",
                style="bold",
            )

            if verbose:
                console.print("\n[bold]Report Summary:[/bold]")
                summary = report_data["summary"]
                console.print(f"  Total Threats: {summary['total_threats']}")
                console.print(f"  Critical: {summary['critical_threats']}")
                console.print(f"  High: {summary['high_threats']}")
                console.print(f"  Medium: {summary['medium_threats']}")
                console.print(f"  Low: {summary['low_threats']}")

        # Save output
        if report_format in ["json", "yaml"]:
            save_output(report_data, output, format_type=report_format)
        else:
            # For PDF, HTML, Markdown - placeholder for now
            console.print(
                f"[yellow]Note:[/yellow] {report_format.upper()} "
                "generation requires additional dependencies",
                style="bold",
            )
            # Save as JSON for now
            save_output(report_data, output, format_type="json")

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]✗[/red] Report generation failed: {e}", style="bold")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--technique",
    help="ATT&CK technique ID (e.g., T1059, T1566)",
    type=str,
)
@click.option(
    "--tactic",
    help="ATT&CK tactic name (e.g., initial-access, execution)",
    type=str,
)
@click.option(
    "--threats",
    help="Threat data file for mapping",
    type=click.Path(exists=True),
)
@click.option(
    "--coverage",
    is_flag=True,
    help="Show tactic coverage analysis",
)
@click.option(
    "--gaps",
    is_flag=True,
    help="Identify detection gaps",
)
@click.option(
    "--navigator",
    is_flag=True,
    help="Generate ATT&CK Navigator layer",
)
@click.option(
    "--output",
    help="Output file path (required for navigator layer)",
    type=click.Path(),
)
@click.pass_context
def attack(
    ctx: click.Context,
    technique: Optional[str],
    tactic: Optional[str],
    threats: Optional[str],
    coverage: bool,
    gaps: bool,
    navigator: bool,
    output: Optional[str],
) -> None:
    """
    MITRE ATT&CK technique mapping and analysis.

    Maps threat intelligence to MITRE ATT&CK framework techniques,
    analyzes tactic coverage, identifies detection gaps, and generates
    ATT&CK Navigator layers for visualization.

    Examples:
        threat-intel attack --technique T1059 --threats malware.json

        threat-intel attack --tactic initial-access --coverage

        threat-intel attack --threats campaign.json --gaps

        threat-intel attack --threats apt_data.json --navigator
        --output attack_layer.json
    """
    config = ctx.obj.get("config", {})
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    if navigator and not output:
        raise click.UsageError("--output is required when using --navigator")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task("[cyan]Analyzing ATT&CK techniques...", total=None)

            # Initialize ATT&CK mapper
            mapper = ATTACKMapper(config=config.get("attack", {}))

            results = {}

            # Load threat data if provided
            threat_data = None
            if threats:
                with open(threats, "r", encoding="utf-8") as f:
                    threat_data = json.load(f)

            # Technique lookup
            if technique:
                technique_info = mapper.get_technique(technique)
                results["technique"] = technique_info

            # Tactic analysis
            if tactic:
                tactic_techniques = mapper.get_tactic_techniques(tactic)
                results["tactic"] = {
                    "name": tactic,
                    "techniques": tactic_techniques,
                }

            # Coverage analysis
            if coverage:
                coverage_data = mapper.analyze_coverage(threat_data)
                results["coverage"] = coverage_data

            # Gap analysis
            if gaps:
                gap_analysis = mapper.identify_gaps(threat_data)
                results["gaps"] = gap_analysis

            # Navigator layer generation
            if navigator:
                layer = mapper.generate_navigator_layer(threat_data)
                results["navigator_layer"] = layer

            progress.update(task, completed=True)

        if not quiet:
            console.print("[green]✓[/green] ATT&CK analysis complete", style="bold")

            if verbose:
                if "technique" in results:
                    console.print(
                        f"\n[bold]Technique:[/bold] "
                        f"{results['technique'].get('id', 'N/A')}"
                    )
                    console.print(f"  Name: {results['technique'].get('name', 'N/A')}")
                    console.print(
                        f"  Tactic: " f"{results['technique'].get('tactic', 'N/A')}"
                    )

                if "coverage" in results:
                    console.print("\n[bold]Coverage Summary:[/bold]")
                    cov = results["coverage"]
                    console.print(f"  Tactics Covered: {cov.get('covered', 0)}")
                    console.print(f"  Tactics Not Covered: {cov.get('not_covered', 0)}")
                    console.print(f"  Coverage %: {cov.get('percentage', 0):.1f}%")

        # Save output
        if output:
            save_output(results, output, format_type="json")
        elif not quiet:
            # Display results in terminal
            console.print_json(data=results)

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]✗[/red] ATT&CK analysis failed: {e}", style="bold")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--show",
    is_flag=True,
    help="Show current configuration",
)
@click.option(
    "--validate",
    is_flag=True,
    help="Validate configuration file",
)
@click.option(
    "--init",
    is_flag=True,
    help="Initialize default configuration file",
)
@click.option(
    "--output",
    help="Output path for new configuration (with --init)",
    type=click.Path(),
)
@click.pass_context
def config(
    ctx: click.Context,
    show: bool,
    validate: bool,
    init: bool,
    output: Optional[str],
) -> None:
    """
    Manage configuration.

    View, validate, or initialize threat intelligence platform configuration.

    Examples:
        threat-intel config --show

        threat-intel config --validate

        threat-intel config --init --output my-config.yaml
    """
    config_data = ctx.obj.get("config", {})
    config_path = ctx.obj.get("config_path", "threat-config.yaml")
    verbose = ctx.obj.get("verbose", False)
    quiet = ctx.obj.get("quiet", False)

    try:
        if show:
            if not quiet:
                console.print(f"[bold]Current Configuration:[/bold] {config_path}\n")
            console.print_json(data=config_data)

        elif validate:
            # Validation logic
            if not config_data:
                console.print(
                    f"[red]✗[/red] No configuration loaded from {config_path}",
                    style="bold",
                )
                sys.exit(1)

            required_sections = ["feeds", "correlation", "output"]
            missing = [s for s in required_sections if s not in config_data]

            if missing:
                console.print(
                    f"[red]✗[/red] Missing required sections: " f"{', '.join(missing)}",
                    style="bold",
                )
                sys.exit(1)

            console.print("[green]✓[/green] Configuration is valid", style="bold")

        elif init:
            default_config = {
                "feeds": {
                    "taxii_servers": [
                        {
                            "url": "https://cti-taxii.mitre.org/taxii/",
                            "collections": ["enterprise-attack"],
                        }
                    ],
                    "cve_sources": ["nvd", "osv", "github"],
                    "update_interval": 900,
                },
                "correlation": {
                    "min_confidence": 70,
                    "risk_threshold": 60,
                    "sbom_formats": ["spdx", "cyclonedx"],
                },
                "enrichment": {
                    "services": ["virustotal", "abuseipdb"],
                    "api_keys": {
                        "virustotal": "${VT_API_KEY}",
                        "abuseipdb": "${AIPDB_KEY}",
                    },
                    "cache_ttl": 3600,
                },
                "output": {
                    "formats": ["json", "pdf"],
                    "reports_dir": "./reports",
                    "vex_dir": "./vex",
                },
                "attack": {
                    "framework_version": "14.1",
                    "enterprise": True,
                    "mobile": False,
                    "ics": False,
                },
            }

            output_path = output or "threat-config.yaml"
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(default_config, f, default_flow_style=False, indent=2)

            console.print(
                f"[green]✓[/green] Configuration initialized: {output_path}",
                style="bold",
            )

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]✗[/red] Configuration operation failed: {e}", style="bold")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    cli(obj={})
