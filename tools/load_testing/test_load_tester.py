"""
Issue #37: Comprehensive Tests for Load Testing Platform
Tests for k6 runner, performance analyzer, and report generator.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from k6_runner import K6Options, K6Result, K6Runner
from perf_analyzer import (
    Bottleneck,
    BottleneckType,
    CapacityRecommendation,
    PerformanceAnalyzer,
    PerformanceMetrics,
    SLAValidation,
    TestType,
)
from report_generator import ReportGenerator


class TestK6Runner:
    """Tests for K6Runner class."""

    def test_k6_runner_initialization(self):
        """Test K6Runner initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = K6Runner(
                k6_binary="k6", default_output_dir=Path(tmpdir)
            )
            assert runner.k6_binary == "k6"
            assert runner.default_output_dir == Path(tmpdir)

    def test_build_command_basic(self):
        """Test basic k6 command building."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = K6Runner(default_output_dir=Path(tmpdir))
            options = K6Options(vus=10, duration="30s")
            output_file = Path(tmpdir) / "output.json"
            script = Path(tmpdir) / "test.js"
            script.touch()

            cmd = runner._build_command(script, options, output_file)

            assert "k6" in cmd
            assert "run" in cmd
            assert "--vus" in cmd
            assert "10" in cmd
            assert "--duration" in cmd
            assert "30s" in cmd
            assert str(script) in cmd

    def test_build_command_with_thresholds(self):
        """Test k6 command with thresholds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = K6Runner(default_output_dir=Path(tmpdir))
            options = K6Options(
                vus=10,
                duration="30s",
                thresholds={
                    "http_req_duration": ["p(95)<500"],
                    "http_req_failed": ["rate<0.01"],
                },
            )
            output_file = Path(tmpdir) / "output.json"
            script = Path(tmpdir) / "test.js"
            script.touch()

            cmd = runner._build_command(script, options, output_file)

            assert "--threshold" in cmd

    def test_parse_duration(self):
        """Test duration parsing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = K6Runner(default_output_dir=Path(tmpdir))

            assert runner._calculate_timeout(K6Options(duration="30s")) == 90
            assert runner._calculate_timeout(K6Options(duration="2m")) == 180
            assert runner._calculate_timeout(K6Options(duration="1h")) == 3660

    def test_calculate_percentiles(self):
        """Test percentile calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = K6Runner(default_output_dir=Path(tmpdir))
            values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

            percentiles = runner._calculate_percentiles(sorted(values))

            assert "p50" in percentiles
            assert "p90" in percentiles
            assert "p95" in percentiles
            assert "p99" in percentiles
            assert percentiles["p50"] == 50

    @patch("subprocess.run")
    def test_run_with_mocked_k6(self, mock_run):
        """Test k6 execution with mocked subprocess."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = K6Runner(default_output_dir=Path(tmpdir))
            script = Path(tmpdir) / "test.js"
            script.write_text("export default function() {}")

            # Mock k6 version check
            version_result = Mock()
            version_result.returncode = 0
            version_result.stdout = "k6 v0.47.0"
            version_result.stderr = ""

            # Mock k6 run
            run_result = Mock()
            run_result.returncode = 0
            run_result.stdout = "Test completed"
            run_result.stderr = ""

            mock_run.side_effect = [version_result, run_result]

            # Create mock output file
            output_file = Path(tmpdir) / "results.json"
            output_file.write_text(
                json.dumps(
                    {
                        "type": "Point",
                        "metric": "http_req_duration",
                        "data": {"value": 150.5},
                    }
                )
            )

            options = K6Options(vus=5, duration="10s")
            result = runner.run(script, options, output_file)

            assert isinstance(result, K6Result)
            assert result.exit_code == 0

    def test_validate_thresholds(self):
        """Test threshold validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = K6Runner(default_output_dir=Path(tmpdir))

            result = K6Result(
                success=True,
                exit_code=0,
                metrics={"http_req_duration": [100, 200, 300, 400, 500]},
                thresholds={"http_req_duration_p95": True},
                raw_output="",
                summary={
                    "http_req_duration": {
                        "p95": 450,
                        "avg": 300,
                    }
                },
            )

            validations = runner.validate_thresholds(
                result, custom_thresholds={"http_req_duration": 500}
            )

            assert isinstance(validations, dict)
            assert "http_req_duration_p95" in validations


class TestPerformanceAnalyzer:
    """Tests for PerformanceAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        metrics = {
            "http_req_duration": [100, 200, 300, 400, 500],
            "http_req_failed": [0, 0, 0, 0, 1],
        }

        analyzer = PerformanceAnalyzer(
            metrics=metrics, test_duration=60.0, test_type=TestType.LOAD
        )

        assert analyzer.raw_metrics == metrics
        assert analyzer.test_duration == 60.0
        assert analyzer.test_type == TestType.LOAD
        assert analyzer.aggregated_metrics is not None

    def test_aggregate_metrics(self):
        """Test metric aggregation."""
        metrics = {
            "http_req_duration": [100.0, 200.0, 300.0, 400.0, 500.0],
            "http_req_failed": [0, 0, 0, 0, 0],
        }

        analyzer = PerformanceAnalyzer(
            metrics=metrics, test_duration=60.0, test_type=TestType.LOAD
        )

        assert analyzer.aggregated_metrics is not None
        assert analyzer.aggregated_metrics.total_requests == 5
        assert analyzer.aggregated_metrics.avg_response_time == 300.0
        assert analyzer.aggregated_metrics.error_rate == 0.0

    def test_identify_bottlenecks_high_latency(self):
        """Test bottleneck identification for high latency."""
        metrics = {
            "http_req_duration": [800.0, 900.0, 950.0, 1000.0, 1100.0],
            "http_req_failed": [0, 0, 0, 0, 0],
        }

        analyzer = PerformanceAnalyzer(
            metrics=metrics, test_duration=60.0, test_type=TestType.LOAD
        )

        bottlenecks = analyzer.identify_bottlenecks(
            latency_threshold_ms=500, error_rate_threshold=1.0
        )

        assert len(bottlenecks) > 0
        assert any(
            b.type == BottleneckType.HIGH_LATENCY for b in bottlenecks
        )

    def test_identify_bottlenecks_high_error_rate(self):
        """Test bottleneck identification for high error rate."""
        metrics = {
            "http_req_duration": [100.0, 200.0, 300.0, 400.0, 500.0],
            "http_req_failed": [1, 1, 1, 0, 0],  # 60% error rate
        }

        analyzer = PerformanceAnalyzer(
            metrics=metrics, test_duration=60.0, test_type=TestType.LOAD
        )

        bottlenecks = analyzer.identify_bottlenecks(
            latency_threshold_ms=500, error_rate_threshold=1.0
        )

        assert len(bottlenecks) > 0
        assert any(
            b.type == BottleneckType.HIGH_ERROR_RATE for b in bottlenecks
        )

    def test_recommend_capacity(self):
        """Test capacity recommendation."""
        metrics = {
            "http_req_duration": [100.0, 200.0, 300.0, 400.0, 500.0],
            "http_req_failed": [0, 0, 0, 0, 0],
        }

        analyzer = PerformanceAnalyzer(
            metrics=metrics, test_duration=60.0, test_type=TestType.LOAD
        )

        capacity = analyzer.recommend_capacity(
            target_latency_ms=500, target_error_rate=1.0, safety_margin=0.2
        )

        assert isinstance(capacity, CapacityRecommendation)
        assert capacity.max_sustainable_load > 0
        assert capacity.recommended_max_load > 0
        assert capacity.recommended_max_load < capacity.max_sustainable_load

    def test_validate_sla(self):
        """Test SLA validation."""
        metrics = {
            "http_req_duration": [100.0, 200.0, 300.0, 400.0, 500.0],
            "http_req_failed": [0, 0, 0, 0, 0],
        }

        analyzer = PerformanceAnalyzer(
            metrics=metrics, test_duration=60.0, test_type=TestType.LOAD
        )

        sla_definitions = [
            {
                "name": "Response Time SLA",
                "metric": "p95_response_time",
                "threshold": 500,
                "operator": "less_than",
            },
            {
                "name": "Error Rate SLA",
                "metric": "error_rate",
                "threshold": 1.0,
                "operator": "less_than",
            },
        ]

        validations = analyzer.validate_sla(sla_definitions)

        assert len(validations) == 2
        assert all(isinstance(v, SLAValidation) for v in validations)

    def test_compare_with_baseline(self):
        """Test baseline comparison."""
        metrics = {
            "http_req_duration": [200.0, 300.0, 400.0, 500.0, 600.0],
            "http_req_failed": [0, 0, 0, 0, 0],
        }

        analyzer = PerformanceAnalyzer(
            metrics=metrics, test_duration=60.0, test_type=TestType.LOAD
        )

        baseline_metrics = PerformanceMetrics(
            avg_response_time=300.0,
            min_response_time=100.0,
            max_response_time=500.0,
            p50_response_time=300.0,
            p90_response_time=450.0,
            p95_response_time=480.0,
            p99_response_time=500.0,
            std_response_time=50.0,
            total_requests=5,
            requests_per_second=0.083,
            data_received_bytes=1000,
            data_sent_bytes=500,
            total_errors=0,
            error_rate=0.0,
            status_code_distribution={200: 5},
            connections_active=1,
            connections_waiting=0,
            connection_duration_avg=10.0,
            test_duration_seconds=60.0,
        )

        comparison = analyzer.compare_with_baseline(baseline_metrics)

        assert isinstance(comparison, dict)
        assert "has_regression" in comparison
        assert "regressions" in comparison
        assert "improvements" in comparison
        assert "summary" in comparison


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    def test_report_generator_initialization(self):
        """Test report generator initialization."""
        generator = ReportGenerator()
        assert generator.env is not None

    def test_generate_html_report(self):
        """Test HTML report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ReportGenerator()

            metrics = PerformanceMetrics(
                avg_response_time=250.0,
                min_response_time=100.0,
                max_response_time=500.0,
                p50_response_time=250.0,
                p90_response_time=400.0,
                p95_response_time=450.0,
                p99_response_time=490.0,
                std_response_time=50.0,
                total_requests=100,
                requests_per_second=10.0,
                data_received_bytes=10000,
                data_sent_bytes=5000,
                total_errors=2,
                error_rate=2.0,
                status_code_distribution={200: 98, 500: 2},
                connections_active=10,
                connections_waiting=0,
                connection_duration_avg=5.0,
                test_duration_seconds=10.0,
            )

            bottlenecks = [
                Bottleneck(
                    type=BottleneckType.HIGH_LATENCY,
                    severity="medium",
                    description="P95 response time exceeds threshold",
                    metric_value=450.0,
                    threshold_value=400.0,
                    recommendation="Optimize database queries",
                )
            ]

            capacity = CapacityRecommendation(
                max_sustainable_load=150,
                recommended_max_load=120,
                safety_margin=0.2,
                limiting_factor="latency",
                confidence_level="medium",
                notes=["System performing within acceptable limits"],
            )

            sla_validations = [
                SLAValidation(
                    passed=True,
                    sla_name="Response Time",
                    metric_name="p95_response_time",
                    expected_value=500.0,
                    actual_value=450.0,
                    deviation_percentage=-10.0,
                    notes="SLA passed",
                )
            ]

            output_file = Path(tmpdir) / "report.html"
            result_file = generator.generate_html_report(
                metrics=metrics,
                bottlenecks=bottlenecks,
                capacity=capacity,
                sla_validations=sla_validations,
                test_type=TestType.LOAD,
                test_name="Test Report",
                output_file=output_file,
                include_charts=False,  # Skip charts for faster test
            )

            assert result_file.exists()
            content = result_file.read_text()
            assert "Test Report" in content
            assert "Performance Metrics" in content
            assert "250.00" in content  # avg response time

    def test_format_bytes(self):
        """Test byte formatting."""
        assert "1.00 KB" in ReportGenerator._format_bytes(1024)
        assert "1.00 MB" in ReportGenerator._format_bytes(1024 * 1024)
        assert "1.00 GB" in ReportGenerator._format_bytes(1024 * 1024 * 1024)

    def test_format_percentage(self):
        """Test percentage formatting."""
        assert "10.5%" == ReportGenerator._format_percentage(10.5)
        assert "0.1%" == ReportGenerator._format_percentage(0.123)

    def test_severity_color(self):
        """Test severity color mapping."""
        assert ReportGenerator._severity_color("low") == "#28a745"
        assert ReportGenerator._severity_color("medium") == "#ffc107"
        assert ReportGenerator._severity_color("high") == "#fd7e14"
        assert ReportGenerator._severity_color("critical") == "#dc3545"


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_workflow_mock(self):
        """Test complete workflow with mocked k6 execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test script
            script = Path(tmpdir) / "test.js"
            script.write_text("export default function() {}")

            # Create mock k6 output
            output_file = Path(tmpdir) / "results.json"
            with output_file.open("w") as f:
                for i in range(10):
                    f.write(
                        json.dumps(
                            {
                                "type": "Point",
                                "metric": "http_req_duration",
                                "data": {"value": 100 + i * 10},
                            }
                        )
                        + "\n"
                    )
                    f.write(
                        json.dumps(
                            {
                                "type": "Point",
                                "metric": "http_req_failed",
                                "data": {"value": 0},
                            }
                        )
                        + "\n"
                    )

            # Analyze results
            metrics = {
                "http_req_duration": [100.0 + i * 10 for i in range(10)],
                "http_req_failed": [0] * 10,
            }

            analyzer = PerformanceAnalyzer(
                metrics=metrics, test_duration=60.0, test_type=TestType.LOAD
            )

            assert analyzer.aggregated_metrics is not None
            assert analyzer.aggregated_metrics.total_requests == 10

            # Generate report
            generator = ReportGenerator()
            report_file = Path(tmpdir) / "report.html"

            if analyzer.aggregated_metrics:
                result = generator.generate_html_report(
                    metrics=analyzer.aggregated_metrics,
                    bottlenecks=[],
                    capacity=CapacityRecommendation(
                        max_sustainable_load=100,
                        recommended_max_load=80,
                        safety_margin=0.2,
                        limiting_factor="none",
                        confidence_level="high",
                        notes=[],
                    ),
                    sla_validations=[],
                    test_type=TestType.LOAD,
                    test_name="Integration Test",
                    output_file=report_file,
                    include_charts=False,
                )

                assert result.exists()


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
