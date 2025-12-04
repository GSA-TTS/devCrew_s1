"""
UX Research & Design Feedback Platform CLI.

This module provides a comprehensive command-line interface for UX research,
accessibility auditing, usability validation, and feedback analysis.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

console = Console()


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary containing configuration

    Raises:
        click.ClickException: If config file cannot be loaded
    """
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise click.ClickException(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise click.ClickException(f"Invalid YAML in config file: {e}")


def save_output(
    data: Dict[str, Any], output_path: Optional[str], format_type: str = "json"
) -> None:
    """
    Save output data to file.

    Args:
        data: Data to save
        output_path: Output file path
        format_type: Output format (json, yaml, html)
    """
    if not output_path:
        return

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if format_type == "json":
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
    elif format_type == "yaml":
        with open(output_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
    elif format_type == "html":
        from jinja2 import Template

        template = Template(HTML_REPORT_TEMPLATE)
        html_content = template.render(data=data)
        with open(output_file, "w") as f:
            f.write(html_content)

    console.print(f"[green]Output saved to: {output_file}[/green]")


def display_results_table(
    results: list, title: str, columns: list, severity_col: Optional[str] = None
) -> None:
    """
    Display results in a formatted table.

    Args:
        results: List of result dictionaries
        title: Table title
        columns: Column names to display
        severity_col: Column name for severity-based coloring
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    for col in columns:
        table.add_column(col)

    severity_colors = {
        "critical": "red",
        "serious": "orange1",
        "moderate": "yellow",
        "minor": "blue",
        "info": "green",
    }

    for result in results:
        row = []
        for col in columns:
            value = str(result.get(col.lower().replace(" ", "_"), ""))
            if severity_col and col == severity_col:
                color = severity_colors.get(value.lower(), "white")
                value = f"[{color}]{value}[/{color}]"
            row.append(value)
        table.add_row(*row)

    console.print(table)


@click.group()
@click.option(
    "--config",
    default="ux-audit-config.yaml",
    help="Configuration file path",
    type=click.Path(exists=True),
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
@click.option("--quiet", is_flag=True, help="Suppress non-essential output")
@click.pass_context
def cli(ctx: click.Context, config: str, verbose: bool, quiet: bool) -> None:
    """
    UX Research & Design Feedback Platform CLI.

    Comprehensive toolset for accessibility auditing, usability validation,
    user feedback analysis, and UX research automation.
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    if not quiet:
        console.print(
            Panel.fit(
                "[bold cyan]UX Research & Design Feedback Platform[/bold cyan]",
                border_style="cyan",
            )
        )


@cli.command()
@click.option("--url", required=True, help="URL to audit")
@click.option(
    "--wcag-level",
    default="AA",
    type=click.Choice(["A", "AA", "AAA"]),
    help="WCAG compliance level",
)
@click.option(
    "--browsers",
    multiple=True,
    default=["chromium"],
    help="Browsers to test (chromium, firefox, webkit)",
)
@click.option(
    "--viewports",
    multiple=True,
    default=["desktop"],
    help="Viewports to test (mobile, tablet, desktop)",
)
@click.option("--output", help="Output file path")
@click.option(
    "--format",
    type=click.Choice(["json", "html", "pdf"]),
    default="json",
    help="Output format",
)
@click.option("--dry-run", is_flag=True, help="Simulate without execution")
@click.pass_context
def audit(
    ctx: click.Context,
    url: str,
    wcag_level: str,
    browsers: tuple,
    viewports: tuple,
    output: Optional[str],
    format: str,
    dry_run: bool,
) -> None:
    """
    Run accessibility audit on a web page.

    Performs WCAG 2.1 compliance checking using axe-core and Playwright
    across multiple browsers and viewports.

    Example:
        ux-tool audit --url https://example.com --wcag-level AA
        --output report.json
    """
    if dry_run:
        console.print("[yellow]DRY RUN MODE - No audit will be executed[/yellow]")
        console.print(f"URL: {url}")
        console.print(f"WCAG Level: {wcag_level}")
        console.print(f"Browsers: {', '.join(browsers)}")
        console.print(f"Viewports: {', '.join(viewports)}")
        return

    try:
        # Import here to avoid issues if module doesn't exist yet
        from tools.ux_research.auditor.accessibility_auditor import \
            AccessibilityAuditor

        config = ctx.obj["config"]
        auditor = AccessibilityAuditor(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Auditing {url} for WCAG {wcag_level}...", total=None
            )

            results = auditor.audit_url(
                url=url,
                wcag_level=wcag_level,
                browsers=list(browsers),
                viewports=list(viewports),
            )

            progress.update(task, completed=True)

        # Display summary
        if not ctx.obj["quiet"]:
            console.print("\n[bold]Audit Summary[/bold]")
            console.print(f"Total violations: {results.get('total_violations', 0)}")
            console.print(
                f"Critical: {results.get('critical_count', 0)} | "
                f"Serious: {results.get('serious_count', 0)} | "
                f"Moderate: {results.get('moderate_count', 0)} | "
                f"Minor: {results.get('minor_count', 0)}"
            )

            # Display top violations
            if results.get("violations"):
                display_results_table(
                    results["violations"][:10],
                    "Top 10 Violations",
                    ["ID", "Description", "Severity", "Count"],
                    severity_col="Severity",
                )

        # Save output
        save_output(results, output, format)

        # Exit with error code if critical violations found
        if results.get("critical_count", 0) > 0:
            sys.exit(1)

    except ImportError:
        console.print(
            "[red]Error: Accessibility auditor module not found. "
            "Please ensure it's implemented.[/red]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Audit failed: {e}[/red]")
        if ctx.obj["verbose"]:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option("--source", required=True, help="Feedback source file or URL")
@click.option(
    "--analyze",
    multiple=True,
    default=["sentiment"],
    help="Analysis types (sentiment, topics, nps)",
)
@click.option("--output", help="Output file path")
@click.option("--format", type=click.Choice(["json", "html", "yaml"]), default="json")
@click.option("--min-confidence", default=0.7, help="Minimum confidence score")
@click.pass_context
def feedback(
    ctx: click.Context,
    source: str,
    analyze: tuple,
    output: Optional[str],
    format: str,
    min_confidence: float,
) -> None:
    """
    Analyze user feedback from various sources.

    Collects and analyzes user feedback from surveys, support tickets,
    session recordings, and heatmaps with NLP-based sentiment analysis.

    Example:
        ux-tool feedback --source surveys.csv --analyze sentiment
        --analyze topics
    """
    try:
        from tools.ux_research.analyzer.sentiment_analyzer import \
            SentimentAnalyzer
        from tools.ux_research.collector.feedback_collector import \
            FeedbackCollector

        config = ctx.obj["config"]
        collector = FeedbackCollector(config)
        analyzer = SentimentAnalyzer(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Collect feedback
            task = progress.add_task("Collecting feedback...", total=None)
            feedback_data = collector.collect_from_source(source)
            progress.update(task, completed=True)

            # Analyze feedback
            results = {}
            for analysis_type in analyze:
                task = progress.add_task(
                    f"Running {analysis_type} analysis...", total=None
                )
                if analysis_type == "sentiment":
                    results["sentiment"] = analyzer.analyze_sentiment(
                        feedback_data, min_confidence=min_confidence
                    )
                elif analysis_type == "topics":
                    results["topics"] = analyzer.extract_topics(feedback_data)
                elif analysis_type == "nps":
                    results["nps"] = collector.calculate_nps(feedback_data)
                progress.update(task, completed=True)

        # Display results
        if not ctx.obj["quiet"]:
            console.print("\n[bold]Feedback Analysis Results[/bold]")

            if "sentiment" in results:
                console.print("\n[cyan]Sentiment Distribution:[/cyan]")
                sentiment = results["sentiment"]
                console.print(
                    f"Positive: {sentiment.get('positive_count', 0)} "
                    f"({sentiment.get('positive_pct', 0):.1f}%)"
                )
                console.print(
                    f"Neutral: {sentiment.get('neutral_count', 0)} "
                    f"({sentiment.get('neutral_pct', 0):.1f}%)"
                )
                console.print(
                    f"Negative: {sentiment.get('negative_count', 0)} "
                    f"({sentiment.get('negative_pct', 0):.1f}%)"
                )

            if "topics" in results:
                console.print("\n[cyan]Top Topics:[/cyan]")
                for topic in results["topics"][:5]:
                    console.print(f"  - {topic['name']}: {topic['count']} mentions")

            if "nps" in results:
                nps_score = results["nps"].get("score", 0)
                color = (
                    "green" if nps_score > 50 else "yellow" if nps_score > 0 else "red"
                )
                console.print(
                    f"\n[cyan]NPS Score:[/cyan] [{color}]{nps_score:.1f}[/{color}]"
                )

        save_output(results, output, format)

    except ImportError:
        console.print(
            "[red]Error: Feedback analysis modules not found. "
            "Please ensure they're implemented.[/red]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Feedback analysis failed: {e}[/red]")
        if ctx.obj["verbose"]:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option("--url", required=True, help="URL to evaluate")
@click.option(
    "--checklist", default="heuristics-checklist.yaml", help="Heuristics checklist file"
)
@click.option(
    "--heuristics", multiple=True, help="Specific heuristics to evaluate (default: all)"
)
@click.option("--output", help="Output file path")
@click.option("--format", type=click.Choice(["json", "html"]), default="json")
@click.pass_context
def heuristics(
    ctx: click.Context,
    url: str,
    checklist: str,
    heuristics: tuple,
    output: Optional[str],
    format: str,
) -> None:
    """
    Evaluate usability using Nielsen's 10 heuristics.

    Performs automated and semi-automated usability validation based on
    Jakob Nielsen's 10 usability heuristics.

    Example:
        ux-tool heuristics --url https://example.com
        --checklist custom-checklist.yaml
    """
    try:
        from tools.ux_research.validator.usability_validator import \
            UsabilityValidator

        config = ctx.obj["config"]
        validator = UsabilityValidator(config)

        # Load checklist
        with open(checklist, "r") as f:
            checklist_data = yaml.safe_load(f)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Evaluating {url} against heuristics...", total=None
            )

            results = validator.evaluate_heuristics(
                url=url,
                checklist=checklist_data,
                heuristics=list(heuristics) if heuristics else None,
            )

            progress.update(task, completed=True)

        # Display results
        if not ctx.obj["quiet"]:
            console.print("\n[bold]Heuristic Evaluation Results[/bold]")

            tree = Tree("Nielsen's 10 Usability Heuristics")

            for heuristic in results.get("heuristics", []):
                name = heuristic["name"]
                passed = heuristic.get("passed", 0)
                failed = heuristic.get("failed", 0)
                total = passed + failed
                score = (passed / total * 100) if total > 0 else 0

                color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
                branch = tree.add(
                    f"[{color}]{name}: {score:.1f}% ({passed}/{total})[/{color}]"
                )

                # Add failed checks
                for check in heuristic.get("failed_checks", []):
                    branch.add(f"[red]✗[/red] {check}")

            console.print(tree)

            # Overall score
            overall_score = results.get("overall_score", 0)
            color = (
                "green"
                if overall_score >= 80
                else "yellow" if overall_score >= 60 else "red"
            )
            console.print(
                f"\n[bold]Overall Score:[/bold] "
                f"[{color}]{overall_score:.1f}%[/{color}]"
            )

        save_output(results, output, format)

    except ImportError:
        console.print(
            "[red]Error: Usability validator module not found. "
            "Please ensure it's implemented.[/red]"
        )
        sys.exit(1)
    except FileNotFoundError:
        console.print(f"[red]Checklist file not found: {checklist}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Heuristic evaluation failed: {e}[/red]")
        if ctx.obj["verbose"]:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--platform",
    required=True,
    type=click.Choice(["google_analytics", "hotjar", "mixpanel"]),
    help="Analytics platform",
)
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--end-date", help="End date (YYYY-MM-DD)")
@click.option(
    "--metrics",
    multiple=True,
    default=["bounce_rate", "conversion_rate"],
    help="Metrics to analyze",
)
@click.option("--output", help="Output file path")
@click.option("--format", type=click.Choice(["json", "yaml"]), default="json")
@click.pass_context
def analyze(
    ctx: click.Context,
    platform: str,
    start_date: Optional[str],
    end_date: Optional[str],
    metrics: tuple,
    output: Optional[str],
    format: str,
) -> None:
    """
    Analyze user behavior from analytics platforms.

    Integrates with Google Analytics, Hotjar, and other analytics platforms
    to extract UX insights and user behavior patterns.

    Example:
        ux-tool analyze --platform google_analytics
        --start-date 2025-01-01 --end-date 2025-01-31
    """
    try:
        from tools.ux_research.analytics.analytics_integrator import \
            AnalyticsIntegrator

        config = ctx.obj["config"]
        integrator = AnalyticsIntegrator(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Fetching data from {platform}...", total=None)

            results = integrator.analyze_platform(
                platform=platform,
                start_date=start_date,
                end_date=end_date,
                metrics=list(metrics),
            )

            progress.update(task, completed=True)

        # Display results
        if not ctx.obj["quiet"]:
            console.print(f"\n[bold]{platform.title()} Analytics[/bold]")
            console.print(f"Period: {start_date} to {end_date}\n")

            metrics_table = Table(
                title="Key Metrics", show_header=True, header_style="bold cyan"
            )
            metrics_table.add_column("Metric")
            metrics_table.add_column("Value")
            metrics_table.add_column("Change")

            for metric_name, metric_data in results.get("metrics", {}).items():
                value = metric_data.get("value", "N/A")
                change = metric_data.get("change", 0)
                change_color = (
                    "green" if change > 0 else "red" if change < 0 else "yellow"
                )
                change_str = f"[{change_color}]{change:+.1f}%[/{change_color}]"

                metrics_table.add_row(metric_name, str(value), change_str)

            console.print(metrics_table)

        save_output(results, output, format)

    except ImportError:
        console.print(
            "[red]Error: Analytics integrator module not found. "
            "Please ensure it's implemented.[/red]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Analytics analysis failed: {e}[/red]")
        if ctx.obj["verbose"]:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--type",
    "report_type",
    required=True,
    type=click.Choice(["accessibility", "usability", "feedback", "comprehensive"]),
    help="Report type",
)
@click.option("--data-dir", help="Directory containing analysis data")
@click.option("--output", required=True, help="Output file path")
@click.option(
    "--format", type=click.Choice(["html", "pdf", "markdown"]), default="html"
)
@click.option("--template", help="Custom report template file")
@click.pass_context
def report(
    ctx: click.Context,
    report_type: str,
    data_dir: Optional[str],
    output: str,
    format: str,
    template: Optional[str],
) -> None:
    """
    Generate comprehensive UX reports.

    Aggregates data from multiple sources and generates formatted reports
    with visualizations, recommendations, and remediation guidance.

    Example:
        ux-tool report --type comprehensive --data-dir ./results
        --output report.html
    """
    try:
        from jinja2 import Environment, FileSystemLoader, Template

        console.print(f"[cyan]Generating {report_type} report...[/cyan]")

        # Collect data
        report_data = {
            "type": report_type,
            "generated_at": str(Path.cwd()),
            "sections": [],
        }

        if data_dir:
            data_path = Path(data_dir)
            if data_path.exists():
                # Load all JSON files from data directory
                for json_file in data_path.glob("*.json"):
                    with open(json_file, "r") as f:
                        section_data = json.load(f)
                        report_data["sections"].append(
                            {"name": json_file.stem, "data": section_data}
                        )

        # Generate report
        if template:
            env = Environment(loader=FileSystemLoader("."))
            template_obj = env.get_template(template)
        else:
            template_obj = Template(get_default_template(report_type, format))

        content = template_obj.render(**report_data)

        # Save report
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)

        console.print(f"[green]Report generated: {output_path}[/green]")

        # Generate PDF if requested
        if format == "pdf":
            try:
                from weasyprint import HTML

                pdf_path = output_path.with_suffix(".pdf")
                HTML(string=content).write_pdf(pdf_path)
                console.print(f"[green]PDF generated: {pdf_path}[/green]")
            except ImportError:
                console.print(
                    "[yellow]Warning: WeasyPrint not installed. "
                    "PDF generation skipped.[/yellow]"
                )

    except Exception as e:
        console.print(f"[red]Report generation failed: {e}[/red]")
        if ctx.obj["verbose"]:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option("--url", required=True, help="URL to monitor")
@click.option("--interval", default=3600, help="Monitoring interval in seconds")
@click.option("--threshold-critical", default=5, help="Critical violations threshold")
@click.option("--threshold-serious", default=10, help="Serious violations threshold")
@click.option("--alert-email", help="Email address for alerts")
@click.option("--webhook", help="Webhook URL for alerts")
@click.option("--max-runs", help="Maximum number of monitoring runs")
@click.pass_context
def monitor(
    ctx: click.Context,
    url: str,
    interval: int,
    threshold_critical: int,
    threshold_serious: int,
    alert_email: Optional[str],
    webhook: Optional[str],
    max_runs: Optional[int],
) -> None:
    """
    Continuous monitoring and alerting for UX metrics.

    Monitors accessibility, performance, and usability metrics continuously
    and sends alerts when thresholds are exceeded.

    Example:
        ux-tool monitor --url https://example.com --interval 3600
        --alert-email admin@example.com
    """
    import time

    try:
        from tools.ux_research.auditor.accessibility_auditor import \
            AccessibilityAuditor

        config = ctx.obj["config"]
        auditor = AccessibilityAuditor(config)

        console.print(f"[cyan]Starting continuous monitoring of {url}[/cyan]")
        console.print(f"Interval: {interval} seconds")
        console.print(
            f"Thresholds - Critical: {threshold_critical}, "
            f"Serious: {threshold_serious}"
        )

        run_count = 0
        while True:
            run_count += 1

            if max_runs and run_count > int(max_runs):
                console.print("[yellow]Maximum runs reached. Stopping.[/yellow]")
                break

            console.print(f"\n[bold]Run #{run_count}[/bold]")

            # Run audit
            results = auditor.audit_url(url=url, wcag_level="AA")

            critical_count = results.get("critical_count", 0)
            serious_count = results.get("serious_count", 0)

            # Check thresholds
            alert_triggered = False
            if critical_count >= threshold_critical:
                console.print(
                    f"[red]ALERT: Critical violations ({critical_count}) "
                    f"exceeded threshold ({threshold_critical})[/red]"
                )
                alert_triggered = True

            if serious_count >= threshold_serious:
                console.print(
                    f"[orange1]WARNING: Serious violations ({serious_count}) "
                    f"exceeded threshold ({threshold_serious})[/orange1]"
                )
                alert_triggered = True

            # Send alerts
            if alert_triggered:
                if alert_email:
                    console.print(f"[cyan]Sending alert to {alert_email}[/cyan]")
                    # Email sending logic would go here

                if webhook:
                    console.print(f"[cyan]Sending webhook to {webhook}[/cyan]")
                    # Webhook logic would go here

            # Display current status
            console.print(
                f"Status: Critical={critical_count}, "
                f"Serious={serious_count}, "
                f"Moderate={results.get('moderate_count', 0)}, "
                f"Minor={results.get('minor_count', 0)}"
            )

            if not max_runs or run_count < int(max_runs):
                console.print(
                    f"[dim]Next run in {interval} seconds... "
                    f"(Press Ctrl+C to stop)[/dim]"
                )
                time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped by user[/yellow]")
    except ImportError:
        console.print(
            "[red]Error: Accessibility auditor module not found. "
            "Please ensure it's implemented.[/red]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Monitoring failed: {e}[/red]")
        if ctx.obj["verbose"]:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--action",
    type=click.Choice(["show", "set", "validate", "init"]),
    required=True,
    help="Configuration action",
)
@click.option("--key", help="Configuration key (for 'set' action)")
@click.option("--value", help="Configuration value (for 'set' action)")
@click.option("--config-file", help="Configuration file path")
@click.pass_context
def config(
    ctx: click.Context,
    action: str,
    key: Optional[str],
    value: Optional[str],
    config_file: Optional[str],
) -> None:
    """
    Manage UX tool configuration.

    View, update, and validate configuration settings for the UX platform.

    Example:
        ux-tool config --action show
        ux-tool config --action set --key audit.wcag_level --value AAA
        ux-tool config --action init
    """
    config_path = config_file or ctx.obj["config"].get(
        "config_file", "ux-audit-config.yaml"
    )

    try:
        if action == "show":
            # Display current configuration
            if config_file:
                with open(config_file, "r") as f:
                    config_data = yaml.safe_load(f)
            else:
                config_data = ctx.obj["config"]

            syntax = Syntax(
                yaml.dump(config_data, default_flow_style=False),
                "yaml",
                theme="monokai",
                line_numbers=True,
            )
            console.print(Panel(syntax, title="Current Configuration"))

        elif action == "set":
            if not key or not value:
                console.print(
                    "[red]Error: --key and --value required for 'set' action[/red]"
                )
                sys.exit(1)

            # Load existing config
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)

            # Set value (handle nested keys with dot notation)
            keys = key.split(".")
            current = config_data
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = value

            # Save updated config
            with open(config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)

            console.print(f"[green]Configuration updated: {key} = {value}[/green]")

        elif action == "validate":
            # Validate configuration
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f)

            errors = []

            # Check required fields
            required_sections = ["audit", "feedback", "analytics"]
            for section in required_sections:
                if section not in config_data:
                    errors.append(f"Missing required section: {section}")

            if errors:
                console.print("[red]Configuration validation failed:[/red]")
                for error in errors:
                    console.print(f"  - {error}")
                sys.exit(1)
            else:
                console.print("[green]Configuration is valid[/green]")

        elif action == "init":
            # Initialize new configuration file
            default_config = get_default_config()

            if Path(config_path).exists():
                console.print(f"[yellow]Warning: {config_path} already exists[/yellow]")
                if not click.confirm("Overwrite?"):
                    return

            with open(config_path, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False)

            console.print(f"[green]Configuration initialized: {config_path}[/green]")

    except Exception as e:
        console.print(f"[red]Configuration management failed: {e}[/red]")
        if ctx.obj["verbose"]:
            console.print_exception()
        sys.exit(1)


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration structure.

    Returns:
        Dictionary containing default configuration
    """
    return {
        "audit": {
            "wcag_level": "AA",
            "browsers": ["chromium", "firefox"],
            "viewports": {
                "mobile": [375, 667],
                "tablet": [768, 1024],
                "desktop": [1920, 1080],
            },
            "timeout": 30000,
            "screenshot": True,
        },
        "feedback": {
            "sources": {"surveys": "surveys.csv", "hotjar_site_id": None},
            "min_confidence": 0.7,
            "language": "en",
        },
        "analytics": {
            "google_analytics": {"property_id": None},
            "hotjar": {"site_id": None},
        },
        "monitoring": {"interval": 3600, "thresholds": {"critical": 5, "serious": 10}},
    }


def get_default_template(report_type: str, format: str) -> str:
    """
    Get default report template.

    Args:
        report_type: Type of report
        format: Output format

    Returns:
        Template string
    """
    if format == "html":
        return HTML_REPORT_TEMPLATE
    elif format == "markdown":
        return MARKDOWN_REPORT_TEMPLATE
    else:
        return "{{ data | tojson }}"


HTML_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UX Research Report - {{ type|title }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        h1 { margin: 0 0 10px 0; }
        .meta { opacity: 0.9; font-size: 14px; }
        .section {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .severity-critical { color: #d32f2f; font-weight: bold; }
        .severity-serious { color: #f57c00; font-weight: bold; }
        .severity-moderate { color: #fbc02d; font-weight: bold; }
        .severity-minor { color: #1976d2; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #667eea;
            color: white;
        }
        tr:hover { background-color: #f5f5f5; }
    </style>
</head>
<body>
    <div class="header">
        <h1>UX Research Report</h1>
        <div class="meta">
            Report Type: {{ type|title }}<br>
            Generated: {{ generated_at }}
        </div>
    </div>

    {% for section in sections %}
    <div class="section">
        <h2>{{ section.name|title }}</h2>
        <pre>{{ section.data|tojson(indent=2) }}</pre>
    </div>
    {% endfor %}
</body>
</html>
"""

MARKDOWN_REPORT_TEMPLATE = """
# UX Research Report

**Type:** {{ type|title }}
**Generated:** {{ generated_at }}

---

{% for section in sections %}
## {{ section.name|title }}

```json
{{ section.data|tojson(indent=2) }}
```

{% endfor %}
"""


if __name__ == "__main__":
    cli(obj={})
