"""
Issue #37: k6 Test Runner Module
Executes k6 load tests with configurable parameters and captures results.
"""

import json
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog

logger = structlog.get_logger()


@dataclass
class K6Options:
    """Configuration options for k6 test execution."""

    vus: int = 1  # Virtual users
    duration: str = "30s"  # Test duration (e.g., "5m", "1h")
    iterations: Optional[int] = None  # Total iterations instead of duration
    stages: Optional[List[Dict[str, Any]]] = None  # Load stages
    thresholds: Optional[Dict[str, List[str]]] = None  # Performance thresholds
    http2: bool = True  # Enable HTTP/2
    insecure_skip_tls_verify: bool = False  # Skip TLS verification
    no_connection_reuse: bool = False  # Disable connection reuse
    rps: Optional[int] = None  # Requests per second limit
    max_redirects: int = 10  # Maximum redirects to follow
    batch: Optional[int] = None  # Batch requests
    batch_per_host: Optional[int] = None  # Batch per host
    tags: Dict[str, str] = field(default_factory=dict)  # Custom tags
    env_vars: Dict[str, str] = field(default_factory=dict)  # Environment vars
    output_format: str = "json"  # Output format (json, influxdb, etc.)


@dataclass
class K6Result:
    """Results from k6 test execution."""

    success: bool
    exit_code: int
    metrics: Dict[str, Any]
    thresholds: Dict[str, bool]
    raw_output: str
    summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class K6Runner:
    """Execute k6 load tests and capture results."""

    def __init__(
        self,
        k6_binary: str = "k6",
        default_output_dir: Optional[Path] = None,
    ):
        """
        Initialize k6 runner.

        Args:
            k6_binary: Path to k6 binary (default: "k6" in PATH)
            default_output_dir: Default directory for output files
        """
        self.k6_binary = k6_binary
        self.default_output_dir = (
            default_output_dir or Path.cwd() / "k6_results"
        )
        self.default_output_dir.mkdir(parents=True, exist_ok=True)
        self._verify_k6_installation()

    def _verify_k6_installation(self) -> None:
        """Verify k6 is installed and accessible."""
        try:
            result = subprocess.run(
                [self.k6_binary, "version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(f"k6 not accessible: {result.stderr}")
            logger.info("k6_verified", version=result.stdout.strip())
        except FileNotFoundError as exc:
            raise RuntimeError(
                "k6 not found. Install from https://k6.io/docs/get-started/"
                "installation/"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("k6 version check timed out") from exc

    def run(
        self,
        script: Union[str, Path],
        options: Optional[K6Options] = None,
        output_file: Optional[Path] = None,
    ) -> K6Result:
        """
        Execute k6 test script.

        Args:
            script: Path to k6 JavaScript test script
            options: K6Options configuration
            output_file: Path to save JSON results

        Returns:
            K6Result with test results and metrics
        """
        script_path = Path(script)
        if not script_path.exists():
            raise FileNotFoundError(f"k6 script not found: {script_path}")

        options = options or K6Options()
        output_file = output_file or (
            self.default_output_dir / f"{script_path.stem}_results.json"
        )

        cmd = self._build_command(script_path, options, output_file)

        logger.info(
            "executing_k6_test",
            script=str(script_path),
            vus=options.vus,
            duration=options.duration,
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._calculate_timeout(options),
                check=False,
            )

            return self._parse_result(result, output_file)

        except subprocess.TimeoutExpired as exc:
            logger.error("k6_test_timeout", timeout=exc.timeout)
            return K6Result(
                success=False,
                exit_code=-1,
                metrics={},
                thresholds={},
                raw_output="",
                error=f"Test execution timed out after {exc.timeout}s",
            )
        except Exception as exc:
            logger.error("k6_execution_error", error=str(exc))
            return K6Result(
                success=False,
                exit_code=-1,
                metrics={},
                thresholds={},
                raw_output="",
                error=str(exc),
            )

    def _build_command(
        self,
        script: Path,
        options: K6Options,
        output_file: Path,
    ) -> List[str]:
        """Build k6 command with all options."""
        cmd = [self.k6_binary, "run"]

        # Output configuration
        cmd.extend(["--out", f"json={output_file}"])

        # VUs and duration
        if options.iterations:
            cmd.extend(["--iterations", str(options.iterations)])
        else:
            cmd.extend(["--vus", str(options.vus)])
            cmd.extend(["--duration", options.duration])

        # Stages for ramping load
        if options.stages:
            stages_file = self._create_stages_config(options.stages)
            cmd.extend(["--stage", self._format_stages(options.stages)])

        # Thresholds
        if options.thresholds:
            for metric, conditions in options.thresholds.items():
                for condition in conditions:
                    cmd.extend(["--threshold", f"{metric}={condition}"])

        # HTTP/2 and TLS
        if not options.http2:
            cmd.append("--no-http2")
        if options.insecure_skip_tls_verify:
            cmd.append("--insecure-skip-tls-verify")

        # Connection settings
        if options.no_connection_reuse:
            cmd.append("--no-connection-reuse")
        if options.rps:
            cmd.extend(["--rps", str(options.rps)])

        # Batch settings
        if options.batch:
            cmd.extend(["--batch", str(options.batch)])
        if options.batch_per_host:
            cmd.extend(["--batch-per-host", str(options.batch_per_host)])

        # Tags
        for key, value in options.tags.items():
            cmd.extend(["--tag", f"{key}={value}"])

        # Environment variables
        for key, value in options.env_vars.items():
            cmd.extend(["-e", f"{key}={value}"])

        # Script path (must be last)
        cmd.append(str(script))

        return cmd

    def _format_stages(self, stages: List[Dict[str, Any]]) -> str:
        """Format stages for k6 command line."""
        stage_strs = []
        for stage in stages:
            duration = stage.get("duration", "30s")
            target = stage.get("target", 1)
            stage_strs.append(f"{duration}:{target}")
        return ",".join(stage_strs)

    def _create_stages_config(self, stages: List[Dict[str, Any]]) -> Path:
        """Create temporary config file for complex stage configurations."""
        config = {"stages": stages}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(config, f)
            return Path(f.name)

    def _calculate_timeout(self, options: K6Options) -> int:
        """Calculate appropriate timeout based on test duration."""
        if options.iterations:
            # Estimate 1 second per iteration + 60s buffer
            return options.iterations + 60

        # Parse duration string
        duration_str = options.duration
        multipliers = {"s": 1, "m": 60, "h": 3600}

        for suffix, mult in multipliers.items():
            if duration_str.endswith(suffix):
                value = int(duration_str[:-1])
                return value * mult + 60  # Add 60s buffer

        # Default timeout
        return 300  # 5 minutes

    def _parse_result(
        self,
        result: subprocess.CompletedProcess,
        output_file: Path,
    ) -> K6Result:
        """Parse k6 execution results."""
        success = result.returncode == 0
        raw_output = result.stdout + result.stderr

        metrics = {}
        thresholds = {}
        summary = None

        # Parse JSON output file
        if output_file.exists():
            try:
                metrics, thresholds, summary = self._parse_json_output(
                    output_file
                )
            except Exception as exc:
                logger.error(
                    "failed_to_parse_results", file=str(output_file), error=str(exc)
                )

        return K6Result(
            success=success,
            exit_code=result.returncode,
            metrics=metrics,
            thresholds=thresholds,
            raw_output=raw_output,
            summary=summary,
            error=result.stderr if not success else None,
        )

    def _parse_json_output(
        self, output_file: Path
    ) -> tuple[Dict[str, Any], Dict[str, bool], Dict[str, Any]]:
        """Parse k6 JSON output file."""
        metrics: Dict[str, List[float]] = {}
        thresholds: Dict[str, bool] = {}
        summary_data: Dict[str, Any] = {}

        with output_file.open() as f:
            for line in f:
                try:
                    data = json.loads(line.strip())

                    # Collect metric data points
                    if data.get("type") == "Point":
                        metric_name = data.get("metric")
                        value = data.get("data", {}).get("value")
                        if metric_name and value is not None:
                            if metric_name not in metrics:
                                metrics[metric_name] = []
                            metrics[metric_name].append(value)

                    # Collect threshold results
                    elif data.get("type") == "Metric" and "thresholds" in data:
                        metric_name = data.get("name")
                        for threshold in data.get("thresholds", {}).values():
                            thresholds[f"{metric_name}"] = threshold.get(
                                "ok", False
                            )

                except json.JSONDecodeError:
                    continue

        # Calculate summary statistics
        summary_data = self._calculate_summary(metrics)

        return metrics, thresholds, summary_data

    def _calculate_summary(
        self, metrics: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Calculate summary statistics from metrics."""
        summary = {}

        for metric_name, values in metrics.items():
            if not values:
                continue

            summary[metric_name] = {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values),
            }

            # Calculate percentiles for timing metrics
            if "duration" in metric_name or "time" in metric_name:
                sorted_values = sorted(values)
                summary[metric_name].update(
                    self._calculate_percentiles(sorted_values)
                )

        return summary

    def _calculate_percentiles(
        self, sorted_values: List[float]
    ) -> Dict[str, float]:
        """Calculate percentile values."""
        n = len(sorted_values)
        if n == 0:
            return {}

        percentiles = {}
        for p in [50, 90, 95, 99]:
            idx = int((p / 100.0) * n)
            if idx >= n:
                idx = n - 1
            percentiles[f"p{p}"] = sorted_values[idx]

        return percentiles

    def validate_thresholds(
        self,
        result: K6Result,
        custom_thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, bool]:
        """
        Validate test results against thresholds.

        Args:
            result: K6Result from test execution
            custom_thresholds: Additional custom thresholds to validate

        Returns:
            Dictionary of threshold validations
        """
        validations = {}

        # Built-in k6 thresholds
        validations.update(result.thresholds)

        # Custom threshold validation
        if custom_thresholds and result.summary:
            for metric, threshold_value in custom_thresholds.items():
                if metric in result.summary:
                    actual_value = result.summary[metric].get("p95", 0)
                    validations[f"custom_{metric}_p95"] = (
                        actual_value <= threshold_value
                    )

        return validations
