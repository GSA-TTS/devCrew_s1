"""
Issue #37: Load Testing & Performance Benchmarking Platform
Main CLI and orchestration module for k6-based load testing.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
import structlog
import yaml

from k6_runner import K6Options, K6Result, K6Runner
from perf_analyzer import PerformanceAnalyzer, TestType
from report_generator import ReportGenerator

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class LoadTestOrchestrator:
    """Orchestrate load testing workflow from execution to reporting."""

    def __init__(
        self,
        output_dir: Path,
        k6_binary: str = "k6",
    ):
        """
        Initialize load test orchestrator.

        Args:
            output_dir: Directory for test results and reports
            k6_binary: Path to k6 binary
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.k6_runner = K6Runner(
            k6_binary=k6_binary, default_output_dir=self.output_dir
        )
        self.report_generator = ReportGenerator()

        logger.info("orchestrator_initialized", output_dir=str(self.output_dir))

    def run_load_test(
        self,
        script: Path,
        test_name: str,
        options: K6Options,
        test_type: TestType = TestType.LOAD,
        sla_config: Optional[Dict[str, Any]] = None,
        generate_report: bool = True,
    ) -> Dict[str, Any]:
        """
        Run complete load test workflow.

        Args:
            script: Path to k6 test script
            test_name: Name for the test run
            options: K6 test options
            test_type: Type of load test
            sla_config: SLA configuration for validation
            generate_report: Whether to generate HTML report

        Returns:
            Dictionary with test results and analysis
        """
        logger.info(
            "starting_load_test",
            test_name=test_name,
            script=str(script),
            test_type=test_type.value,
        )

        # Execute k6 test
        result_file = self.output_dir / f"{test_name}_raw.json"
        result = self.k6_runner.run(
            script=script, options=options, output_file=result_file
        )

        if not result.success:
            logger.error(
                "test_execution_failed",
                error=result.error,
                exit_code=result.exit_code,
            )
            return {
                "success": False,
                "error": result.error,
                "result": result,
            }

        # Analyze results
        analyzer = self._analyze_results(result, options, test_type)

        # Validate SLAs
        sla_validations = []
        if sla_config and "slas" in sla_config:
            sla_validations = analyzer.validate_sla(sla_config["slas"])

        # Identify bottlenecks
        bottlenecks = analyzer.identify_bottlenecks(
            latency_threshold_ms=sla_config.get("latency_threshold_ms", 500)
            if sla_config
            else 500,
            error_rate_threshold=sla_config.get("error_rate_threshold", 1.0)
            if sla_config
            else 1.0,
        )

        # Generate capacity recommendations
        capacity = analyzer.recommend_capacity(
            target_latency_ms=sla_config.get("target_latency_ms", 500)
            if sla_config
            else 500,
            target_error_rate=sla_config.get("target_error_rate", 1.0)
            if sla_config
            else 1.0,
        )

        # Save analysis results
        analysis_file = self.output_dir / f"{test_name}_analysis.json"
        self._save_analysis(
            analysis_file,
            analyzer,
            bottlenecks,
            capacity,
            sla_validations,
        )

        # Generate report
        report_file = None
        if generate_report and analyzer.aggregated_metrics:
            report_file = self.output_dir / f"{test_name}_report.html"
            self.report_generator.generate_html_report(
                metrics=analyzer.aggregated_metrics,
                bottlenecks=bottlenecks,
                capacity=capacity,
                sla_validations=sla_validations,
                test_type=test_type,
                test_name=test_name,
                output_file=report_file,
                include_charts=True,
            )

        logger.info(
            "load_test_completed",
            test_name=test_name,
            success=result.success,
            report=str(report_file) if report_file else None,
        )

        return {
            "success": True,
            "result": result,
            "analyzer": analyzer,
            "bottlenecks": bottlenecks,
            "capacity": capacity,
            "sla_validations": sla_validations,
            "files": {
                "raw_results": str(result_file),
                "analysis": str(analysis_file),
                "report": str(report_file) if report_file else None,
            },
        }

    def _analyze_results(
        self,
        result: K6Result,
        options: K6Options,
        test_type: TestType,
    ) -> PerformanceAnalyzer:
        """Analyze k6 test results."""
        test_duration = self._parse_duration(options.duration)
        return PerformanceAnalyzer(
            metrics=result.metrics,
            test_duration=test_duration,
            test_type=test_type,
        )

    def _parse_duration(self, duration_str: str) -> float:
        """Parse duration string to seconds."""
        multipliers = {"s": 1, "m": 60, "h": 3600}
        for suffix, mult in multipliers.items():
            if duration_str.endswith(suffix):
                return float(duration_str[:-1]) * mult
        return 30.0  # Default

    def _save_analysis(
        self,
        output_file: Path,
        analyzer: PerformanceAnalyzer,
        bottlenecks: List[Any],
        capacity: Any,
        sla_validations: List[Any],
    ) -> None:
        """Save analysis results to JSON file."""
        data = {
            "timestamp": structlog.processors.TimeStamper(fmt="iso")(),
            "metrics": (
                self._serialize_dataclass(analyzer.aggregated_metrics)
                if analyzer.aggregated_metrics
                else {}
            ),
            "bottlenecks": [self._serialize_dataclass(b) for b in bottlenecks],
            "capacity": self._serialize_dataclass(capacity),
            "sla_validations": [
                self._serialize_dataclass(v) for v in sla_validations
            ],
        }

        output_file.write_text(json.dumps(data, indent=2))
        logger.info("analysis_saved", path=str(output_file))

    def _serialize_dataclass(self, obj: Any) -> Dict[str, Any]:
        """Serialize dataclass to dictionary."""
        if hasattr(obj, "__dataclass_fields__"):
            result = {}
            for field_name in obj.__dataclass_fields__:
                value = getattr(obj, field_name)
                if hasattr(value, "__dataclass_fields__"):
                    result[field_name] = self._serialize_dataclass(value)
                elif isinstance(value, list):
                    result[field_name] = [
                        (
                            self._serialize_dataclass(item)
                            if hasattr(item, "__dataclass_fields__")
                            else str(item)
                        )
                        for item in value
                    ]
                elif hasattr(value, "value"):  # Enum
                    result[field_name] = value.value
                else:
                    result[field_name] = value
            return result
        return str(obj)


# CLI Implementation
@click.group()
@click.version_option(version="1.0.0")
def cli() -> None:
    """devCrew_s1 Load Testing & Performance Benchmarking Platform."""
    pass


@cli.command(name="run-test")
@click.option(
    "--script",
    "-s",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to k6 test script",
)
@click.option(
    "--name",
    "-n",
    type=str,
    required=True,
    help="Test name for identification",
)
@click.option(
    "--vus",
    "-v",
    type=int,
    default=10,
    help="Number of virtual users",
)
@click.option(
    "--duration",
    "-d",
    type=str,
    default="30s",
    help="Test duration (e.g., 30s, 5m, 1h)",
)
@click.option(
    "--test-type",
    "-t",
    type=click.Choice(["load", "stress", "spike", "soak", "baseline"]),
    default="load",
    help="Type of load test",
)
@click.option(
    "--sla-config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to SLA configuration YAML file",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("./load_test_results"),
    help="Output directory for results",
)
@click.option(
    "--no-report",
    is_flag=True,
    help="Skip HTML report generation",
)
@click.option(
    "--k6-binary",
    type=str,
    default="k6",
    help="Path to k6 binary",
)
def run_test(
    script: Path,
    name: str,
    vus: int,
    duration: str,
    test_type: str,
    sla_config: Optional[Path],
    output_dir: Path,
    no_report: bool,
    k6_binary: str,
) -> None:
    """Execute k6 load test with analysis and reporting."""
    try:
        # Load SLA config if provided
        sla_conf = None
        if sla_config:
            with sla_config.open() as f:
                sla_conf = yaml.safe_load(f)

        # Create orchestrator
        orchestrator = LoadTestOrchestrator(
            output_dir=output_dir, k6_binary=k6_binary
        )

        # Configure k6 options
        options = K6Options(
            vus=vus,
            duration=duration,
        )

        # Run test
        test_type_enum = TestType(test_type)
        results = orchestrator.run_load_test(
            script=script,
            test_name=name,
            options=options,
            test_type=test_type_enum,
            sla_config=sla_conf,
            generate_report=not no_report,
        )

        if results["success"]:
            click.echo(
                click.style("✓ Load test completed successfully", fg="green")
            )
            click.echo(f"\nResults saved to: {output_dir}")
            if results["files"]["report"]:
                click.echo(
                    f"HTML Report: {click.style(results['files']['report'], fg='cyan')}"
                )

            # Display summary
            analyzer = results["analyzer"]
            if analyzer.aggregated_metrics:
                metrics = analyzer.aggregated_metrics
                click.echo("\n=== Performance Summary ===")
                click.echo(f"Total Requests: {metrics.total_requests:,}")
                click.echo(f"Throughput: {metrics.requests_per_second:.2f} RPS")
                click.echo(
                    f"Avg Response Time: {metrics.avg_response_time:.2f}ms"
                )
                click.echo(
                    f"P95 Response Time: {metrics.p95_response_time:.2f}ms"
                )
                click.echo(f"Error Rate: {metrics.error_rate:.2f}%")

            # Display bottlenecks
            if results["bottlenecks"]:
                click.echo(
                    f"\n⚠ {len(results['bottlenecks'])} bottleneck(s) identified"
                )

            # Display SLA results
            if results["sla_validations"]:
                passed = sum(1 for v in results["sla_validations"] if v.passed)
                total = len(results["sla_validations"])
                if passed == total:
                    click.echo(
                        click.style(f"\n✓ All {total} SLAs passed", fg="green")
                    )
                else:
                    click.echo(
                        click.style(
                            f"\n✗ {total - passed}/{total} SLAs failed", fg="red"
                        )
                    )

            sys.exit(0)
        else:
            click.echo(
                click.style(f"✗ Load test failed: {results['error']}", fg="red")
            )
            sys.exit(1)

    except Exception as exc:
        logger.error("test_execution_error", error=str(exc))
        click.echo(click.style(f"Error: {exc}", fg="red"))
        sys.exit(1)


@cli.command(name="analyze")
@click.option(
    "--results",
    "-r",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to k6 results JSON file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    required=True,
    help="Output path for analysis report",
)
@click.option(
    "--test-duration",
    "-d",
    type=float,
    required=True,
    help="Test duration in seconds",
)
def analyze_results(results: Path, output: Path, test_duration: float) -> None:
    """Analyze existing k6 test results."""
    try:
        # Load results
        with results.open() as f:
            metrics = {}
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if data.get("type") == "Point":
                        metric_name = data.get("metric")
                        value = data.get("data", {}).get("value")
                        if metric_name and value is not None:
                            if metric_name not in metrics:
                                metrics[metric_name] = []
                            metrics[metric_name].append(value)
                except json.JSONDecodeError:
                    continue

        # Analyze
        analyzer = PerformanceAnalyzer(
            metrics=metrics,
            test_duration=test_duration,
            test_type=TestType.LOAD,
        )

        bottlenecks = analyzer.identify_bottlenecks()
        capacity = analyzer.recommend_capacity()

        # Generate report
        if analyzer.aggregated_metrics:
            report_gen = ReportGenerator()
            report_gen.generate_html_report(
                metrics=analyzer.aggregated_metrics,
                bottlenecks=bottlenecks,
                capacity=capacity,
                sla_validations=[],
                test_type=TestType.LOAD,
                test_name="Analysis",
                output_file=output,
            )

            click.echo(click.style("✓ Analysis completed", fg="green"))
            click.echo(f"Report saved to: {output}")
        else:
            click.echo(click.style("No metrics found in results file", fg="yellow"))

    except Exception as exc:
        logger.error("analysis_error", error=str(exc))
        click.echo(click.style(f"Error: {exc}", fg="red"))
        sys.exit(1)


@cli.command(name="validate-sla")
@click.option(
    "--results",
    "-r",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to analysis JSON file",
)
@click.option(
    "--sla-config",
    "-s",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to SLA configuration YAML file",
)
def validate_sla(results: Path, sla_config: Path) -> None:
    """Validate test results against SLA thresholds."""
    try:
        # Load analysis results
        with results.open() as f:
            analysis_data = json.load(f)

        # Load SLA config
        with sla_config.open() as f:
            sla_conf = yaml.safe_load(f)

        # Check SLAs (simplified version)
        click.echo("\n=== SLA Validation ===")
        all_passed = True

        for sla in sla_conf.get("slas", []):
            metric_name = sla["metric"]
            threshold = sla["threshold"]
            actual_value = analysis_data.get("metrics", {}).get(metric_name, 0)

            passed = actual_value <= threshold
            all_passed = all_passed and passed

            status = click.style("PASS", fg="green") if passed else click.style("FAIL", fg="red")
            click.echo(
                f"{sla['name']}: {status} "
                f"(Expected: {threshold}, Actual: {actual_value:.2f})"
            )

        sys.exit(0 if all_passed else 1)

    except Exception as exc:
        logger.error("sla_validation_error", error=str(exc))
        click.echo(click.style(f"Error: {exc}", fg="red"))
        sys.exit(1)


if __name__ == "__main__":
    cli()
