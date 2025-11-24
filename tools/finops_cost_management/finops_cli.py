"""
FinOps & Cost Management CLI.

Comprehensive command-line interface for cloud cost management, analysis,
optimization, and budgeting. Provides intuitive commands for multi-cloud
cost tracking, anomaly detection, optimization recommendations, forecasting,
and Kubernetes cost attribution.

Features:
- Multi-cloud cost aggregation and analysis
- Anomaly detection with ML-based algorithms
- Cost optimization recommendations
- Budget management and alerting
- Kubernetes cost attribution via Kubecost
- Cost forecasting with Prophet
- Export capabilities (JSON, CSV, Excel, charts)

Protocol Coverage:
- P-CLOUD-VALIDATION: Validate cloud configurations
- P-FINOPS-COST-MONITOR: Cost monitoring and tracking
- P-OBSERVABILITY: Metrics export and visualization
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .anomaly_detector import AnomalyConfig, AnomalyDetector
from .budget_manager import (Budget, BudgetConfig, BudgetManager, BudgetPeriod,
                             BudgetStatus)
from .cost_aggregator import CloudProvider, CostAggregator
from .cost_forecaster import CostForecaster, ForecastConfig
from .cost_optimizer import CostOptimizer, OptimizerConfig
from .k8s_cost_analyzer import K8sCostAnalyzer, KubecostConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rich console for output
console = Console()


# Global context for CLI
class FinOpsContext:
    """Global context for FinOps CLI."""

    def __init__(self) -> None:
        """Initialize context."""
        self.aggregator: Optional[CostAggregator] = None
        self.anomaly_detector: Optional[AnomalyDetector] = None
        self.optimizer: Optional[CostOptimizer] = None
        self.forecaster: Optional[CostForecaster] = None
        self.k8s_analyzer: Optional[K8sCostAnalyzer] = None
        self.budget_manager: Optional[BudgetManager] = None


pass_context = click.make_pass_decorator(FinOpsContext, ensure=True)


@click.group()
@click.option("--debug", is_flag=True, default=False, help="Enable debug logging")
@click.version_option(version="1.0.0")
@pass_context
def cli(ctx: FinOpsContext, debug: bool) -> None:
    """
    FinOps & Cost Management Platform.

    Comprehensive cloud cost monitoring, optimization, and budgeting tool
    supporting AWS, Azure, and Google Cloud Platform.
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize components
    try:
        ctx.aggregator = CostAggregator()
        ctx.anomaly_detector = AnomalyDetector(ctx.aggregator)
        ctx.optimizer = CostOptimizer(ctx.aggregator)
        ctx.forecaster = CostForecaster(ctx.aggregator)
        ctx.budget_manager = BudgetManager(ctx.aggregator)
    except Exception as e:
        console.print(f"[red]Failed to initialize FinOps components: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--provider",
    type=click.Choice(["aws", "azure", "gcp", "all"], case_sensitive=False),
    default="all",
    help="Cloud provider to query",
)
@click.option(
    "--period",
    type=click.Choice(["today", "week", "month", "quarter", "year", "custom"]),
    default="month",
    help="Time period for costs",
)
@click.option(
    "--start-date", type=str, help="Start date for custom period (YYYY-MM-DD)"
)
@click.option("--end-date", type=str, help="End date for custom period (YYYY-MM-DD)")
@click.option(
    "--group-by",
    type=click.Choice(["provider", "service", "region", "tag"]),
    default="service",
    help="Grouping dimension",
)
@click.option("--tag-key", type=str, help="Tag key for tag-based grouping")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.option("--output", type=click.Path(), help="Output file path")
@pass_context
def cost(
    ctx: FinOpsContext,
    provider: str,
    period: str,
    start_date: Optional[str],
    end_date: Optional[str],
    group_by: str,
    tag_key: Optional[str],
    output_format: str,
    output: Optional[str],
) -> None:
    """View multi-cloud costs with grouping and filtering."""
    try:
        # Calculate date range
        start_dt, end_dt = _parse_period(period, start_date, end_date)

        # Parse provider filter
        providers = None
        if provider != "all":
            providers = [CloudProvider(provider.lower())]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Fetching cost data...", total=None)

            # Get costs
            costs = ctx.aggregator.get_costs(
                start_date=start_dt.date().isoformat(),
                end_date=end_dt.date().isoformat(),
                providers=providers,
            )

        if not costs:
            console.print(
                "[yellow]No cost data found for the specified period[/yellow]"
            )  # noqa: E501
            return

        # Group costs
        if group_by == "tag" and tag_key:
            grouped = _group_costs_by_tag(costs, tag_key)
        elif group_by == "provider":
            grouped = _group_costs_by_provider(costs)
        elif group_by == "service":
            grouped = _group_costs_by_service(costs)
        elif group_by == "region":
            grouped = _group_costs_by_region(costs)
        else:
            grouped = _group_costs_by_service(costs)

        # Format output
        if output_format == "table":
            _display_cost_table(grouped, start_dt, end_dt, group_by)
        elif output_format == "json":
            data = _format_costs_json(grouped, start_dt, end_dt)
            if output:
                Path(output).write_text(json.dumps(data, indent=2, default=str))
                console.print(f"[green]Costs saved to {output}[/green]")
            else:
                console.print_json(data=data)
        elif output_format == "csv":
            csv_data = _format_costs_csv(grouped)
            if output:
                Path(output).write_text(csv_data)
                console.print(f"[green]Costs saved to {output}[/green]")
            else:
                console.print(csv_data)

    except Exception as e:
        console.print(f"[red]Error fetching costs: {e}[/red]")
        if ctx.aggregator:
            logger.exception("Cost fetch failed")
        sys.exit(1)


@cli.command()
@click.option(
    "--provider",
    type=click.Choice(["aws", "azure", "gcp", "all"], case_sensitive=False),
    default="all",
    help="Cloud provider to analyze",
)
@click.option("--days", type=int, default=30, help="Number of days to analyze")
@click.option(
    "--sensitivity",
    type=float,
    default=0.05,
    help="Anomaly detection sensitivity (0.0-1.0)",
)
@click.option(
    "--min-cost", type=float, default=10.0, help="Minimum cost threshold for anomalies"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@pass_context
def anomalies(
    ctx: FinOpsContext,
    provider: str,
    days: int,
    sensitivity: float,
    min_cost: float,
    output_format: str,
) -> None:
    """Detect cost anomalies using ML-based analysis."""
    try:
        # Configure anomaly detection
        config = AnomalyConfig(
            contamination=sensitivity,
            min_cost_threshold=min_cost,
        )
        ctx.anomaly_detector.config = config

        # Parse provider
        providers = None
        if provider != "all":
            providers = [CloudProvider(provider.lower())]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Detecting anomalies...", total=None)

            # Detect anomalies
            anomalies_found = ctx.anomaly_detector.detect_anomalies(
                days=days,
                providers=providers,
            )

        if not anomalies_found:
            console.print(
                "[green]No cost anomalies detected in the specified period[/green]"
            )
            return

        # Format output
        if output_format == "table":
            _display_anomalies_table(anomalies_found)
        else:
            data = [a.model_dump(mode="json") for a in anomalies_found]
            console.print_json(data=data)

        # Summary
        total_impact = sum(a.cost_impact for a in anomalies_found)
        console.print(
            f"\n[yellow]Found {len(anomalies_found)} anomalies "
            f"with total impact: ${total_impact:,.2f}[/yellow]"
        )

    except Exception as e:
        console.print(f"[red]Error detecting anomalies: {e}[/red]")
        logger.exception("Anomaly detection failed")
        sys.exit(1)


@cli.command()
@click.option(
    "--provider",
    type=click.Choice(["aws", "azure", "gcp", "all"], case_sensitive=False),
    default="all",
    help="Cloud provider to optimize",
)
@click.option(
    "--category",
    type=click.Choice(["compute", "storage", "network", "database", "all"]),
    default="all",
    help="Resource category to optimize",
)
@click.option(
    "--min-savings", type=float, default=10.0, help="Minimum monthly savings threshold"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@pass_context
def optimize(
    ctx: FinOpsContext,
    provider: str,
    category: str,
    min_savings: float,
    output_format: str,
) -> None:
    """Get cost optimization recommendations."""
    try:
        # Configure optimizer
        config = OptimizerConfig(
            min_savings_threshold=min_savings,
            analysis_period_days=30,
        )
        ctx.optimizer.config = config

        # Parse provider
        providers = None
        if provider != "all":
            providers = [CloudProvider(provider.lower())]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Analyzing optimization opportunities...", total=None)

            # Get recommendations
            recommendations = ctx.optimizer.get_recommendations(
                providers=providers,
                categories=[category] if category != "all" else None,
            )

        if not recommendations:
            console.print("[green]No optimization opportunities found[/green]")
            return

        # Format output
        if output_format == "table":
            _display_recommendations_table(recommendations)
        else:
            data = [r.model_dump(mode="json") for r in recommendations]
            console.print_json(data=data)

        # Summary
        total_savings = sum(r.estimated_monthly_savings for r in recommendations)
        console.print(
            f"\n[green]Found {len(recommendations)} optimization opportunities "
            f"with potential savings: ${total_savings:,.2f}/month[/green]"
        )

    except Exception as e:
        console.print(f"[red]Error generating recommendations: {e}[/red]")
        logger.exception("Optimization failed")
        sys.exit(1)


@cli.command()
@click.option(
    "--provider",
    type=click.Choice(["aws", "azure", "gcp", "all"], case_sensitive=False),
    default="all",
    help="Cloud provider to forecast",
)
@click.option("--days", type=int, default=30, help="Number of days to forecast")
@click.option(
    "--model",
    type=click.Choice(["prophet", "linear", "auto"]),
    default="auto",
    help="Forecasting model",
)
@click.option(
    "--confidence", type=float, default=0.95, help="Confidence interval (0.0-1.0)"
)
@click.option("--output", type=click.Path(), help="Output chart file (PNG)")
@pass_context
def forecast(
    ctx: FinOpsContext,
    provider: str,
    days: int,
    model: str,
    confidence: float,
    output: Optional[str],
) -> None:
    """Forecast future costs using time-series analysis."""
    try:
        # Configure forecaster
        config = ForecastConfig(
            forecast_days=days,
            model_type=model,
            confidence_interval=confidence,
        )
        ctx.forecaster.config = config

        # Parse provider
        providers = None
        if provider != "all":
            providers = [CloudProvider(provider.lower())]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Generating forecast...", total=None)

            # Generate forecast
            forecast_result = ctx.forecaster.forecast_costs(
                providers=providers,
            )

        # Display results
        _display_forecast_summary(forecast_result)

        # Generate chart if requested
        if output:
            ctx.forecaster.plot_forecast(forecast_result, output)
            console.print(f"\n[green]Forecast chart saved to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error generating forecast: {e}[/red]")
        logger.exception("Forecast failed")
        sys.exit(1)


@cli.group()
def budget() -> None:
    """Manage budgets and alerts."""
    pass


@budget.command("create")
@click.option("--name", required=True, help="Budget name")
@click.option("--amount", type=float, required=True, help="Budget amount")
@click.option(
    "--period",
    type=click.Choice(["daily", "weekly", "monthly", "quarterly", "yearly"]),
    default="monthly",
    help="Budget period",
)
@click.option(
    "--threshold",
    "thresholds",
    multiple=True,
    type=float,
    help="Alert thresholds (can specify multiple)",
)
@click.option(
    "--channel",
    "channels",
    multiple=True,
    type=str,
    help="Notification channels (e.g., email:user@example.com)",
)
@pass_context
def budget_create(
    ctx: FinOpsContext,
    name: str,
    amount: float,
    period: str,
    thresholds: tuple,
    channels: tuple,
) -> None:
    """Create a new budget."""
    try:
        # Parse thresholds
        alert_thresholds = list(thresholds) if thresholds else [0.8, 0.9, 1.0]

        # Create config
        config = BudgetConfig(
            name=name,
            amount=amount,
            period=BudgetPeriod(period),
            alert_thresholds=alert_thresholds,
            notification_channels=list(channels),
        )

        # Create budget
        budget_obj = ctx.budget_manager.create_budget(config)

        console.print(
            Panel(
                f"[green]Budget '{name}' created successfully![/green]\n\n"
                f"ID: {budget_obj.id}\n"
                f"Amount: ${amount:,.2f}\n"
                f"Period: {period}\n"
                f"Thresholds: {', '.join(f'{t:.0%}' for t in alert_thresholds)}",
                title="Budget Created",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]Error creating budget: {e}[/red]")
        sys.exit(1)


@budget.command("list")
@click.option(
    "--status",
    type=click.Choice(["on_track", "at_risk", "over_budget", "approaching_limit"]),
    help="Filter by status",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@pass_context
def budget_list(ctx: FinOpsContext, status: Optional[str], output_format: str) -> None:
    """List all budgets."""
    try:
        # Parse status filter
        status_filter = BudgetStatus(status) if status else None

        # Get budgets
        budgets = ctx.budget_manager.list_budgets(status=status_filter)

        if not budgets:
            console.print("[yellow]No budgets found[/yellow]")
            return

        # Format output
        if output_format == "table":
            _display_budgets_table(budgets)
        else:
            data = [b.model_dump(mode="json") for b in budgets]
            console.print_json(data=data)

    except Exception as e:
        console.print(f"[red]Error listing budgets: {e}[/red]")
        sys.exit(1)


@budget.command("check")
@pass_context
def budget_check(ctx: FinOpsContext) -> None:
    """Check budgets and send alerts."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Checking budgets...", total=None)

            # Check budgets
            alerts = ctx.budget_manager.check_budgets()

        if not alerts:
            console.print("[green]All budgets are within limits[/green]")
            return

        # Send alerts
        for alert in alerts:
            ctx.budget_manager.send_alert(alert)

        # Display alerts
        _display_alerts_table(alerts)

        console.print(f"\n[yellow]Generated {len(alerts)} budget alerts[/yellow]")

    except Exception as e:
        console.print(f"[red]Error checking budgets: {e}[/red]")
        sys.exit(1)


@budget.command("summary")
@pass_context
def budget_summary(ctx: FinOpsContext) -> None:
    """Show budget summary."""
    try:
        summary = ctx.budget_manager.get_budget_summary()

        # Display summary
        table = Table(title="Budget Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green", justify="right")

        table.add_row("Total Budgets", str(summary["total_budgets"]))
        table.add_row("Total Allocated", f"${summary['total_allocated']:,.2f}")
        table.add_row("Total Spent", f"${summary['total_spent']:,.2f}")
        table.add_row("Total Remaining", f"${summary['total_remaining']:,.2f}")
        table.add_row("Utilization", f"{summary['utilization_percentage']:.1f}%")

        if summary.get("at_risk_count", 0) > 0:
            table.add_row("At Risk", str(summary["at_risk_count"]), style="yellow")

        if summary.get("over_budget_count", 0) > 0:
            table.add_row("Over Budget", str(summary["over_budget_count"]), style="red")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting budget summary: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--cluster", help="Cluster name")
@click.option(
    "--kubecost-url", default="http://localhost:9090", help="Kubecost API URL"
)
@click.option(
    "--group-by",
    type=click.Choice(["namespace", "pod", "label"]),
    default="namespace",
    help="Grouping dimension",
)
@click.option("--label-key", type=str, help="Label key for label-based grouping")
@click.option(
    "--period",
    type=click.Choice(["today", "week", "month"]),
    default="week",
    help="Time period",
)
@click.option("--idle", is_flag=True, help="Show idle resources")
@click.option("--threshold", type=float, default=0.2, help="Idle resource threshold")
@pass_context
def k8s(
    ctx: FinOpsContext,
    cluster: Optional[str],
    kubecost_url: str,
    group_by: str,
    label_key: Optional[str],
    period: str,
    idle: bool,
    threshold: float,
) -> None:
    """Analyze Kubernetes costs with Kubecost."""
    try:
        # Configure K8s analyzer
        config = KubecostConfig(
            kubecost_url=kubecost_url,
            cluster_name=cluster or "default",
        )
        ctx.k8s_analyzer = K8sCostAnalyzer(config)

        # Calculate date range
        start_dt, end_dt = _parse_period(period, None, None)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            if idle:
                # Show idle resources
                progress.add_task("Identifying idle resources...", total=None)
                idle_resources = ctx.k8s_analyzer.identify_idle_resources(
                    threshold=threshold,
                    start_date=start_dt.isoformat(),
                    end_date=end_dt.isoformat(),
                )
                _display_idle_resources_table(idle_resources)

            elif group_by == "label" and label_key:
                # Show costs by label
                progress.add_task("Fetching costs by label...", total=None)
                costs = ctx.k8s_analyzer.get_costs_by_label(
                    label_key,
                    start_dt.isoformat(),
                    end_dt.isoformat(),
                )
                _display_label_costs_table(costs, label_key)

            else:
                # Show costs by namespace/pod
                progress.add_task("Fetching costs...", total=None)
                costs = ctx.k8s_analyzer.get_namespace_costs(
                    start_dt.isoformat(),
                    end_dt.isoformat(),
                    aggregation=group_by,
                )
                _display_k8s_costs_table(costs, group_by)

    except Exception as e:
        console.print(f"[red]Error analyzing Kubernetes costs: {e}[/red]")
        logger.exception("K8s analysis failed")
        sys.exit(1)


@cli.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "csv", "excel"]),
    required=True,
    help="Export format",
)
@click.option("--output", type=click.Path(), required=True, help="Output file path")
@click.option(
    "--provider",
    type=click.Choice(["aws", "azure", "gcp", "all"], case_sensitive=False),
    default="all",
    help="Cloud provider",
)
@click.option("--days", type=int, default=30, help="Number of days to export")
@pass_context
def export(
    ctx: FinOpsContext, output_format: str, output: str, provider: str, days: int
) -> None:
    """Export cost data to file."""
    try:
        # Calculate date range
        end_dt = datetime.utcnow()
        start_dt = end_dt - timedelta(days=days)

        # Parse provider
        providers = None
        if provider != "all":
            providers = [CloudProvider(provider.lower())]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task("Exporting cost data...", total=None)

            # Get costs
            costs = ctx.aggregator.get_costs(
                start_date=start_dt.date().isoformat(),
                end_date=end_dt.date().isoformat(),
                providers=providers,
            )

        if not costs:
            console.print("[yellow]No cost data to export[/yellow]")
            return

        # Export based on format
        if output_format == "json":
            data = [c.model_dump(mode="json") for c in costs]
            Path(output).write_text(json.dumps(data, indent=2, default=str))

        elif output_format == "csv":
            import csv

            with open(output, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "date",
                        "provider",
                        "service",
                        "region",
                        "cost",
                        "currency",
                        "usage_type",
                    ],
                )
                writer.writeheader()
                for cost in costs:
                    writer.writerow(
                        {
                            "date": cost.date.isoformat(),
                            "provider": cost.provider.value,
                            "service": cost.service,
                            "region": cost.region,
                            "cost": cost.cost,
                            "currency": cost.currency,
                            "usage_type": cost.usage_type,
                        }
                    )

        elif output_format == "excel":
            import pandas as pd

            df = pd.DataFrame(
                [
                    {
                        "Date": c.date,
                        "Provider": c.provider.value,
                        "Service": c.service,
                        "Region": c.region,
                        "Cost": c.cost,
                        "Currency": c.currency,
                        "Usage Type": c.usage_type,
                    }
                    for c in costs
                ]
            )
            df.to_excel(output, index=False, engine="openpyxl")

        console.print(f"[green]Exported {len(costs)} cost records to {output}[/green]")

    except Exception as e:
        console.print(f"[red]Error exporting data: {e}[/red]")
        sys.exit(1)


# Helper functions for formatting and display


def _parse_period(
    period: str, start_date: Optional[str], end_date: Optional[str]
) -> tuple[datetime, datetime]:
    """Parse time period into start and end dates."""
    now = datetime.utcnow()

    if period == "custom":
        if not start_date or not end_date:
            raise ValueError("Start and end dates required for custom period")
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    elif period == "today":
        start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = now
    elif period == "week":
        start_dt = now - timedelta(days=7)
        end_dt = now
    elif period == "month":
        start_dt = now - timedelta(days=30)
        end_dt = now
    elif period == "quarter":
        start_dt = now - timedelta(days=90)
        end_dt = now
    elif period == "year":
        start_dt = now - timedelta(days=365)
        end_dt = now
    else:
        raise ValueError(f"Invalid period: {period}")

    return start_dt, end_dt


def _group_costs_by_provider(costs: List[Any]) -> Dict[str, float]:
    """Group costs by provider."""
    grouped: Dict[str, float] = {}
    for cost in costs:
        key = cost.provider.value
        grouped[key] = grouped.get(key, 0.0) + cost.cost
    return grouped


def _group_costs_by_service(costs: List[Any]) -> Dict[str, float]:
    """Group costs by service."""
    grouped: Dict[str, float] = {}
    for cost in costs:
        key = cost.service
        grouped[key] = grouped.get(key, 0.0) + cost.cost
    return grouped


def _group_costs_by_region(costs: List[Any]) -> Dict[str, float]:
    """Group costs by region."""
    grouped: Dict[str, float] = {}
    for cost in costs:
        key = cost.region
        grouped[key] = grouped.get(key, 0.0) + cost.cost
    return grouped


def _group_costs_by_tag(costs: List[Any], tag_key: str) -> Dict[str, float]:
    """Group costs by tag value."""
    grouped: Dict[str, float] = {}
    for cost in costs:
        value = cost.tags.get(tag_key, "untagged")
        grouped[value] = grouped.get(value, 0.0) + cost.cost
    return grouped


def _display_cost_table(
    grouped: Dict[str, float], start_dt: datetime, end_dt: datetime, group_by: str
) -> None:
    """Display costs in a table."""
    table = Table(
        title=f"Costs from {start_dt.date()} to {end_dt.date()}", show_header=True
    )
    table.add_column(group_by.capitalize(), style="cyan")
    table.add_column("Cost", style="green", justify="right")
    table.add_column("Percentage", style="yellow", justify="right")

    total = sum(grouped.values())
    sorted_items = sorted(grouped.items(), key=lambda x: x[1], reverse=True)

    for key, cost in sorted_items:
        percentage = (cost / total * 100) if total > 0 else 0
        table.add_row(key, f"${cost:,.2f}", f"{percentage:.1f}%")

    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]${total:,.2f}[/bold]",
        "[bold]100.0%[/bold]",
        style="bold",
    )

    console.print(table)


def _format_costs_json(
    grouped: Dict[str, float], start_dt: datetime, end_dt: datetime
) -> Dict[str, Any]:
    """Format costs as JSON."""
    return {
        "period": {
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
        },
        "total_cost": sum(grouped.values()),
        "breakdown": grouped,
    }


def _format_costs_csv(grouped: Dict[str, float]) -> str:
    """Format costs as CSV."""
    lines = ["Category,Cost"]
    for key, cost in sorted(grouped.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"{key},{cost:.2f}")
    return "\n".join(lines)


def _display_anomalies_table(anomalies: List[Any]) -> None:
    """Display anomalies in a table."""
    table = Table(title="Cost Anomalies", show_header=True)
    table.add_column("Date", style="cyan")
    table.add_column("Provider", style="blue")
    table.add_column("Service", style="magenta")
    table.add_column("Cost", style="red", justify="right")
    table.add_column("Expected", style="green", justify="right")
    table.add_column("Impact", style="yellow", justify="right")
    table.add_column("Severity", style="red")

    for anomaly in sorted(anomalies, key=lambda a: a.cost_impact, reverse=True):
        table.add_row(
            anomaly.date.strftime("%Y-%m-%d"),
            anomaly.provider.value,
            anomaly.service,
            f"${anomaly.actual_cost:,.2f}",
            f"${anomaly.expected_cost:,.2f}",
            f"${anomaly.cost_impact:,.2f}",
            anomaly.severity.value.upper(),
        )

    console.print(table)


def _display_recommendations_table(recommendations: List[Any]) -> None:
    """Display recommendations in a table."""
    table = Table(title="Optimization Recommendations", show_header=True)
    table.add_column("Provider", style="cyan")
    table.add_column("Resource", style="blue")
    table.add_column("Category", style="magenta")
    table.add_column("Savings/Month", style="green", justify="right")
    table.add_column("Priority", style="yellow")

    for rec in sorted(
        recommendations, key=lambda r: r.estimated_monthly_savings, reverse=True
    ):
        table.add_row(
            rec.provider.value,
            rec.resource_id[:40],
            rec.category,
            f"${rec.estimated_monthly_savings:,.2f}",
            rec.priority.value.upper(),
        )

    console.print(table)


def _display_forecast_summary(forecast: Any) -> None:
    """Display forecast summary."""
    panel = Panel(
        f"[cyan]Forecast Model:[/cyan] {forecast.model_type}\n"
        f"[cyan]Confidence:[/cyan] {forecast.confidence_interval:.0%}\n"
        f"[cyan]Historical Cost:[/cyan] ${forecast.historical_total:,.2f}\n"
        f"[cyan]Forecasted Cost:[/cyan] ${forecast.forecasted_total:,.2f}\n"
        f"[cyan]Lower Bound:[/cyan] ${forecast.lower_bound_total:,.2f}\n"
        f"[cyan]Upper Bound:[/cyan] ${forecast.upper_bound_total:,.2f}\n"
        f"[cyan]Growth Rate:[/cyan] {forecast.growth_rate:.1%}",
        title="Cost Forecast",
        border_style="blue",
    )
    console.print(panel)


def _display_budgets_table(budgets: List[Budget]) -> None:
    """Display budgets in a table."""
    table = Table(title="Budgets", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Amount", style="green", justify="right")
    table.add_column("Spent", style="yellow", justify="right")
    table.add_column("Remaining", style="blue", justify="right")
    table.add_column("Usage", style="magenta", justify="right")
    table.add_column("Status", style="red")

    for budget in budgets:
        usage_pct = budget.get_percentage_used()
        remaining = budget.get_remaining_budget()

        # Color status
        status_colors = {
            BudgetStatus.ON_TRACK: "green",
            BudgetStatus.APPROACHING_LIMIT: "yellow",
            BudgetStatus.AT_RISK: "yellow",
            BudgetStatus.OVER_BUDGET: "red",
        }
        status_color = status_colors.get(budget.status, "white")

        table.add_row(
            budget.config.name,
            f"${budget.config.amount:,.2f}",
            f"${budget.current_spend:,.2f}",
            f"${remaining:,.2f}",
            f"{usage_pct:.1f}%",
            f"[{status_color}]{budget.status.value}[/{status_color}]",
        )

    console.print(table)


def _display_alerts_table(alerts: List[Any]) -> None:
    """Display alerts in a table."""
    table = Table(title="Budget Alerts", show_header=True)
    table.add_column("Budget", style="cyan")
    table.add_column("Threshold", style="yellow", justify="right")
    table.add_column("Current", style="red", justify="right")
    table.add_column("Status", style="magenta")
    table.add_column("Message", style="white")

    for alert in alerts:
        table.add_row(
            alert.budget_name,
            f"{alert.threshold:.0%}",
            f"${alert.current_spend:,.2f}",
            alert.status.value,
            alert.message[:60],
        )

    console.print(table)


def _display_k8s_costs_table(costs: List[Any], group_by: str) -> None:
    """Display Kubernetes costs in a table."""
    table = Table(title=f"Kubernetes Costs by {group_by}", show_header=True)
    table.add_column("Namespace", style="cyan")

    if group_by == "pod":
        table.add_column("Pod", style="blue")

    table.add_column("CPU", style="green", justify="right")
    table.add_column("Memory", style="yellow", justify="right")
    table.add_column("Storage", style="magenta", justify="right")
    table.add_column("Network", style="blue", justify="right")
    table.add_column("Total", style="red", justify="right")

    for cost in sorted(costs, key=lambda c: c.total_cost, reverse=True):
        row = [cost.namespace]
        if group_by == "pod":
            row.append(cost.pod or "N/A")
        row.extend(
            [
                f"${cost.cpu_cost:,.2f}",
                f"${cost.memory_cost:,.2f}",
                f"${cost.storage_cost:,.2f}",
                f"${cost.network_cost:,.2f}",
                f"${cost.total_cost:,.2f}",
            ]
        )
        table.add_row(*row)

    console.print(table)


def _display_idle_resources_table(resources: List[Any]) -> None:
    """Display idle resources in a table."""
    table = Table(title="Idle Resources", show_header=True)
    table.add_column("Namespace", style="cyan")
    table.add_column("Pod", style="blue")
    table.add_column("Type", style="magenta")
    table.add_column("Utilization", style="yellow", justify="right")
    table.add_column("Waste Cost", style="red", justify="right")
    table.add_column("Recommendation", style="green")

    for resource in resources:
        table.add_row(
            resource.namespace,
            resource.pod,
            resource.resource_type,
            f"{resource.utilization:.1f}%",
            f"${resource.waste_cost:,.2f}",
            resource.recommendation[:60],
        )

    console.print(table)


def _display_label_costs_table(costs: Dict[str, float], label_key: str) -> None:
    """Display costs by label in a table."""
    table = Table(title=f"Costs by Label: {label_key}", show_header=True)
    table.add_column("Label Value", style="cyan")
    table.add_column("Cost", style="green", justify="right")
    table.add_column("Percentage", style="yellow", justify="right")

    total = sum(costs.values())
    for value, cost in sorted(costs.items(), key=lambda x: x[1], reverse=True):
        pct = (cost / total * 100) if total > 0 else 0
        table.add_row(value, f"${cost:,.2f}", f"{pct:.1f}%")

    console.print(table)


if __name__ == "__main__":
    cli()
