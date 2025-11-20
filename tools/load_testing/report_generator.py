"""
Issue #37: Report Generator Module
Generates HTML and PDF reports from load test results.
"""

import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
import structlog
from jinja2 import Environment, FileSystemLoader, Template

from issue_37_perf_analyzer import (
    Bottleneck,
    CapacityRecommendation,
    PerformanceMetrics,
    SLAValidation,
    TestType,
)

matplotlib.use("Agg")  # Use non-interactive backend

logger = structlog.get_logger()


class ReportGenerator:
    """Generate HTML and PDF reports from load test results."""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize report generator.

        Args:
            template_dir: Directory containing Jinja2 templates
        """
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self.env = self._setup_jinja_env()

    def _setup_jinja_env(self) -> Environment:
        """Setup Jinja2 environment with custom filters."""
        if self.template_dir.exists():
            env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True,
            )
        else:
            # Use string templates if directory doesn't exist
            env = Environment(autoescape=True)

        # Add custom filters
        env.filters["format_number"] = self._format_number
        env.filters["format_percentage"] = self._format_percentage
        env.filters["format_bytes"] = self._format_bytes
        env.filters["severity_color"] = self._severity_color

        return env

    def generate_html_report(
        self,
        metrics: PerformanceMetrics,
        bottlenecks: List[Bottleneck],
        capacity: CapacityRecommendation,
        sla_validations: List[SLAValidation],
        test_type: TestType,
        test_name: str,
        output_file: Path,
        include_charts: bool = True,
    ) -> Path:
        """
        Generate HTML report.

        Args:
            metrics: Performance metrics
            bottlenecks: Identified bottlenecks
            capacity: Capacity recommendation
            sla_validations: SLA validation results
            test_type: Type of load test
            test_name: Name of the test
            output_file: Output file path
            include_charts: Whether to include charts

        Returns:
            Path to generated report
        """
        logger.info("generating_html_report", output=str(output_file))

        # Generate charts
        charts = {}
        if include_charts:
            charts = self._generate_charts(metrics)

        # Prepare template data
        template_data = {
            "test_name": test_name,
            "test_type": test_type.value,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metrics": metrics,
            "bottlenecks": bottlenecks,
            "capacity": capacity,
            "sla_validations": sla_validations,
            "sla_passed": all(v.passed for v in sla_validations),
            "charts": charts,
            "summary": self._generate_summary(metrics, bottlenecks),
        }

        # Render template
        html_content = self._render_html_template(template_data)

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html_content)

        logger.info("html_report_generated", path=str(output_file))
        return output_file

    def _render_html_template(self, data: Dict[str, Any]) -> str:
        """Render HTML template with data."""
        # Use inline template since we don't have template files
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ test_name }} - Load Test Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
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
        .header h1 { margin: 0 0 10px 0; }
        .header .meta { opacity: 0.9; font-size: 14px; }
        .section {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .section h2 {
            margin-top: 0;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .metric-card .label {
            font-size: 12px;
            text-transform: uppercase;
            color: #666;
            font-weight: 600;
        }
        .metric-card .value {
            font-size: 28px;
            font-weight: bold;
            color: #333;
            margin: 5px 0;
        }
        .metric-card .unit {
            font-size: 14px;
            color: #666;
        }
        .bottleneck {
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        .bottleneck.critical { border-color: #dc3545; background: #f8d7da; }
        .bottleneck.high { border-color: #fd7e14; background: #fff3cd; }
        .bottleneck.medium { border-color: #ffc107; background: #fff9e6; }
        .bottleneck.low { border-color: #28a745; background: #d4edda; }
        .bottleneck-header {
            font-weight: bold;
            margin-bottom: 8px;
        }
        .bottleneck-desc {
            margin: 5px 0;
            color: #555;
        }
        .bottleneck-rec {
            margin-top: 8px;
            padding: 8px;
            background: rgba(255,255,255,0.7);
            border-radius: 4px;
            font-size: 14px;
        }
        .sla-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .sla-table th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }
        .sla-table td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }
        .sla-table tr:hover {
            background: #f8f9fa;
        }
        .status-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-pass {
            background: #d4edda;
            color: #155724;
        }
        .status-fail {
            background: #f8d7da;
            color: #721c24;
        }
        .chart-container {
            margin: 20px 0;
            text-align: center;
        }
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .summary-box {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .capacity-recommendation {
            background: #e7f3ff;
            border-left: 4px solid #2196f3;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .capacity-recommendation h3 {
            margin-top: 0;
            color: #1976d2;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ test_name }}</h1>
        <div class="meta">
            <strong>Test Type:</strong> {{ test_type | upper }} |
            <strong>Generated:</strong> {{ generated_at }}
        </div>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        <div class="summary-box">
            {{ summary }}
        </div>
    </div>

    <div class="section">
        <h2>Performance Metrics</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="label">Average Response Time</div>
                <div class="value">{{ "%.2f"|format(metrics.avg_response_time) }}</div>
                <div class="unit">milliseconds</div>
            </div>
            <div class="metric-card">
                <div class="label">P95 Response Time</div>
                <div class="value">{{ "%.2f"|format(metrics.p95_response_time) }}</div>
                <div class="unit">milliseconds</div>
            </div>
            <div class="metric-card">
                <div class="label">P99 Response Time</div>
                <div class="value">{{ "%.2f"|format(metrics.p99_response_time) }}</div>
                <div class="unit">milliseconds</div>
            </div>
            <div class="metric-card">
                <div class="label">Throughput</div>
                <div class="value">{{ "%.2f"|format(metrics.requests_per_second) }}</div>
                <div class="unit">requests/second</div>
            </div>
            <div class="metric-card">
                <div class="label">Total Requests</div>
                <div class="value">{{ "{:,}".format(metrics.total_requests) }}</div>
                <div class="unit">requests</div>
            </div>
            <div class="metric-card">
                <div class="label">Error Rate</div>
                <div class="value">{{ "%.2f"|format(metrics.error_rate) }}</div>
                <div class="unit">percent</div>
            </div>
        </div>
    </div>

    {% if charts %}
    <div class="section">
        <h2>Performance Charts</h2>
        {% for chart_name, chart_data in charts.items() %}
        <div class="chart-container">
            <h3>{{ chart_name | replace('_', ' ') | title }}</h3>
            <img src="data:image/png;base64,{{ chart_data }}" alt="{{ chart_name }}">
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if bottlenecks %}
    <div class="section">
        <h2>Performance Bottlenecks</h2>
        {% for bottleneck in bottlenecks %}
        <div class="bottleneck {{ bottleneck.severity }}">
            <div class="bottleneck-header">
                [{{ bottleneck.severity | upper }}] {{ bottleneck.type.value | replace('_', ' ') | title }}
            </div>
            <div class="bottleneck-desc">{{ bottleneck.description }}</div>
            <div class="bottleneck-rec">
                <strong>Recommendation:</strong> {{ bottleneck.recommendation }}
            </div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="section">
        <h2>Capacity Recommendations</h2>
        <div class="capacity-recommendation">
            <h3>Capacity Planning Analysis</h3>
            <p><strong>Maximum Sustainable Load:</strong> {{ capacity.max_sustainable_load }} virtual users</p>
            <p><strong>Recommended Maximum Load:</strong> {{ capacity.recommended_max_load }} virtual users
               ({{ "%.0f"|format(capacity.safety_margin * 100) }}% safety margin)</p>
            <p><strong>Limiting Factor:</strong> {{ capacity.limiting_factor | replace('_', ' ') | title }}</p>
            <p><strong>Confidence Level:</strong> {{ capacity.confidence_level | upper }}</p>
            {% if capacity.notes %}
            <p><strong>Notes:</strong></p>
            <ul>
                {% for note in capacity.notes %}
                <li>{{ note }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
    </div>

    {% if sla_validations %}
    <div class="section">
        <h2>SLA Validation Results</h2>
        {% if sla_passed %}
        <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <strong style="color: #155724;">✓ All SLAs Passed</strong>
        </div>
        {% else %}
        <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <strong style="color: #721c24;">✗ Some SLAs Failed</strong>
        </div>
        {% endif %}
        <table class="sla-table">
            <thead>
                <tr>
                    <th>SLA Name</th>
                    <th>Metric</th>
                    <th>Expected</th>
                    <th>Actual</th>
                    <th>Deviation</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {% for sla in sla_validations %}
                <tr>
                    <td>{{ sla.sla_name }}</td>
                    <td>{{ sla.metric_name }}</td>
                    <td>{{ "%.2f"|format(sla.expected_value) }}</td>
                    <td>{{ "%.2f"|format(sla.actual_value) }}</td>
                    <td>{{ "%.1f"|format(sla.deviation_percentage) }}%</td>
                    <td>
                        <span class="status-badge {% if sla.passed %}status-pass{% else %}status-fail{% endif %}">
                            {% if sla.passed %}PASS{% else %}FAIL{% endif %}
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endif %}

    <div class="footer">
        Generated by devCrew_s1 Load Testing Platform | Issue #37
    </div>
</body>
</html>
        """

        template = Template(template_str)
        return template.render(**data)

    def _generate_charts(self, metrics: PerformanceMetrics) -> Dict[str, str]:
        """Generate charts and return as base64-encoded images."""
        charts = {}

        try:
            # Response time percentiles chart
            charts["response_time_percentiles"] = self._create_percentile_chart(
                metrics
            )

            # Throughput chart
            charts["throughput_summary"] = self._create_throughput_chart(metrics)

        except Exception as exc:
            logger.error("chart_generation_failed", error=str(exc))

        return charts

    def _create_percentile_chart(self, metrics: PerformanceMetrics) -> str:
        """Create response time percentile chart."""
        fig, ax = plt.subplots(figsize=(10, 6))

        percentiles = ["P50", "P90", "P95", "P99"]
        values = [
            metrics.p50_response_time,
            metrics.p90_response_time,
            metrics.p95_response_time,
            metrics.p99_response_time,
        ]

        bars = ax.bar(percentiles, values, color=["#4CAF50", "#FFC107", "#FF9800", "#F44336"])
        ax.set_ylabel("Response Time (ms)")
        ax.set_title("Response Time Percentiles")
        ax.grid(axis="y", alpha=0.3)

        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.1f}ms",
                ha="center",
                va="bottom",
            )

        return self._fig_to_base64(fig)

    def _create_throughput_chart(self, metrics: PerformanceMetrics) -> str:
        """Create throughput summary chart."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Requests summary
        labels = ["Successful", "Failed"]
        sizes = [
            metrics.total_requests - metrics.total_errors,
            metrics.total_errors,
        ]
        colors = ["#4CAF50", "#F44336"]
        ax1.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
        ax1.set_title("Request Success Rate")

        # Data transfer
        data_labels = ["Sent", "Received"]
        data_values = [
            metrics.data_sent_bytes / (1024 * 1024),  # Convert to MB
            metrics.data_received_bytes / (1024 * 1024),
        ]
        bars = ax2.bar(data_labels, data_values, color=["#2196F3", "#9C27B0"])
        ax2.set_ylabel("Data Transfer (MB)")
        ax2.set_title("Network Traffic")

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.2f} MB",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _fig_to_base64(self, fig: plt.Figure) -> str:
        """Convert matplotlib figure to base64-encoded string."""
        buffer = BytesIO()
        fig.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        return image_base64

    def _generate_summary(
        self, metrics: PerformanceMetrics, bottlenecks: List[Bottleneck]
    ) -> str:
        """Generate executive summary text."""
        summary_parts = []

        # Overall assessment
        if metrics.error_rate < 1.0 and metrics.p95_response_time < 500:
            summary_parts.append(
                "✓ <strong>System performed well</strong> under the tested load with "
                "acceptable response times and low error rates."
            )
        elif metrics.error_rate >= 5.0:
            summary_parts.append(
                "✗ <strong>High error rate detected</strong> - system is experiencing "
                "significant failures under load."
            )
        elif metrics.p95_response_time >= 1000:
            summary_parts.append(
                "✗ <strong>High latency detected</strong> - response times exceed "
                "acceptable thresholds."
            )
        else:
            summary_parts.append(
                "⚠ <strong>System under stress</strong> - performance degradation "
                "observed under the tested load."
            )

        # Key metrics
        summary_parts.append(
            f"<p><strong>Key Metrics:</strong> Processed "
            f"<strong>{metrics.total_requests:,}</strong> requests at "
            f"<strong>{metrics.requests_per_second:.1f} RPS</strong> with "
            f"<strong>{metrics.error_rate:.2f}%</strong> error rate.</p>"
        )

        # Bottlenecks
        if bottlenecks:
            critical_count = sum(1 for b in bottlenecks if b.severity == "critical")
            if critical_count > 0:
                summary_parts.append(
                    f"<p>⚠ <strong>{critical_count} critical bottleneck(s)</strong> "
                    "identified requiring immediate attention.</p>"
                )
            else:
                summary_parts.append(
                    f"<p><strong>{len(bottlenecks)} bottleneck(s)</strong> "
                    "identified for optimization.</p>"
                )

        return "\n".join(summary_parts)

    @staticmethod
    def _format_number(value: float) -> str:
        """Format number with commas."""
        return f"{value:,.2f}"

    @staticmethod
    def _format_percentage(value: float) -> str:
        """Format as percentage."""
        return f"{value:.1f}%"

    @staticmethod
    def _format_bytes(value: int) -> str:
        """Format bytes to human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if value < 1024.0:
                return f"{value:.2f} {unit}"
            value /= 1024.0
        return f"{value:.2f} TB"

    @staticmethod
    def _severity_color(severity: str) -> str:
        """Get color for severity level."""
        colors = {
            "low": "#28a745",
            "medium": "#ffc107",
            "high": "#fd7e14",
            "critical": "#dc3545",
        }
        return colors.get(severity.lower(), "#6c757d")
