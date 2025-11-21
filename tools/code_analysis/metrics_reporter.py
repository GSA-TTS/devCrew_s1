"""
Metrics Reporter Module.

Generates reports in JSON, HTML, and text formats from code analysis results.
"""

import html
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional


class ReportFormat(Enum):
    """Supported report formats."""

    JSON = "json"
    HTML = "html"
    TEXT = "text"
    MARKDOWN = "markdown"


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    title: str = "Code Analysis Report"
    include_summary: bool = True
    include_details: bool = True
    include_suggestions: bool = True
    max_items_per_section: int = 50
    sort_by_severity: bool = True


class MetricsReporter:
    """Generates reports from code analysis results."""

    def __init__(self, config: Optional[ReportConfig] = None) -> None:
        """
        Initialize reporter with configuration.

        Args:
            config: Report configuration options
        """
        self.config = config or ReportConfig()

    def generate(
        self,
        data: Dict[str, Any],
        format: ReportFormat = ReportFormat.JSON,
        output_path: Optional[str | Path] = None,
    ) -> str:
        """
        Generate a report from analysis data.

        Args:
            data: Analysis data dictionary
            format: Output format
            output_path: Optional path to save the report

        Returns:
            The generated report as a string
        """
        generators = {
            ReportFormat.JSON: self._generate_json,
            ReportFormat.HTML: self._generate_html,
            ReportFormat.TEXT: self._generate_text,
            ReportFormat.MARKDOWN: self._generate_markdown,
        }

        report = generators[format](data)

        if output_path:
            Path(output_path).write_text(report, encoding="utf-8")

        return report

    def _generate_json(self, data: Dict[str, Any]) -> str:
        """Generate JSON report."""
        report_data = {
            "report_title": self.config.title,
            "generated_at": datetime.now().isoformat(),
            **data,
        }
        return json.dumps(report_data, indent=2, default=str)

    def _generate_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML report."""
        summary = data.get("summary", {})
        smells = data.get("smells", [])
        violations = data.get("violations", [])
        suggestions = data.get("suggestions", [])
        tech_debt = data.get("tech_debt", {})

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1'>",
            f"<title>{html.escape(self.config.title)}</title>",
            "<style>",
            self._get_css(),
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{html.escape(self.config.title)}</h1>",
            f"<p class='timestamp'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
        ]

        # Summary section
        if self.config.include_summary and summary:
            html_parts.append("<section class='summary'>")
            html_parts.append("<h2>Summary</h2>")
            html_parts.append("<div class='metrics-grid'>")
            for key, value in summary.items():
                display_key = key.replace("_", " ").title()
                html_parts.append(
                    f"<div class='metric-card'>"
                    f"<span class='metric-value'>{value}</span>"
                    f"<span class='metric-label'>{html.escape(display_key)}</span>"
                    f"</div>"
                )
            html_parts.append("</div>")
            html_parts.append("</section>")

        # Violations section
        if self.config.include_details and violations:
            html_parts.append("<section class='violations'>")
            html_parts.append("<h2>Complexity Violations</h2>")
            html_parts.append("<table>")
            html_parts.append(
                "<tr><th>Function</th><th>Type</th><th>Value</th>"
                "<th>Threshold</th><th>Line</th></tr>"
            )
            for v in violations[: self.config.max_items_per_section]:
                html_parts.append(
                    f"<tr class='severity-high'>"
                    f"<td>{html.escape(str(v.get('function', '')))}</td>"
                    f"<td>{html.escape(str(v.get('type', '')))}</td>"
                    f"<td>{v.get('value', '')}</td>"
                    f"<td>{v.get('threshold', '')}</td>"
                    f"<td>{v.get('lineno', '')}</td>"
                    f"</tr>"
                )
            html_parts.append("</table>")
            html_parts.append("</section>")

        # Code smells section
        if self.config.include_details and smells:
            html_parts.append("<section class='smells'>")
            html_parts.append("<h2>Code Smells</h2>")
            html_parts.append("<table>")
            html_parts.append(
                "<tr><th>Name</th><th>Severity</th><th>Location</th>"
                "<th>Description</th></tr>"
            )
            sorted_smells = smells
            if self.config.sort_by_severity:
                severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                sorted_smells = sorted(
                    smells,
                    key=lambda x: severity_order.get(x.get("severity", "low"), 4),
                )
            for s in sorted_smells[: self.config.max_items_per_section]:
                severity = s.get("severity", "low")
                html_parts.append(
                    f"<tr class='severity-{severity}'>"
                    f"<td>{html.escape(str(s.get('name', '')))}</td>"
                    f"<td><span class='badge badge-{severity}'>{severity}</span></td>"
                    f"<td>{html.escape(str(s.get('location', '')))}:"
                    f"{s.get('lineno', '')}</td>"
                    f"<td>{html.escape(str(s.get('description', '')))}</td>"
                    f"</tr>"
                )
            html_parts.append("</table>")
            html_parts.append("</section>")

        # Suggestions section
        if self.config.include_suggestions and suggestions:
            html_parts.append("<section class='suggestions'>")
            html_parts.append("<h2>Refactoring Suggestions</h2>")
            for s in suggestions[: self.config.max_items_per_section]:
                html_parts.append("<div class='suggestion-card'>")
                html_parts.append(
                    f"<h3>{html.escape(str(s.get('title', '')))}</h3>"
                )
                html_parts.append(
                    f"<p><strong>Location:</strong> "
                    f"{html.escape(str(s.get('location', '')))}"
                    f":{s.get('lineno', '')}</p>"
                )
                html_parts.append(
                    f"<p>{html.escape(str(s.get('description', '')))}</p>"
                )
                html_parts.append(
                    f"<p><strong>Impact:</strong> {s.get('impact', '')} | "
                    f"<strong>Effort:</strong> {s.get('effort', '')}</p>"
                )
                steps = s.get("steps", [])
                if steps:
                    html_parts.append("<ol>")
                    for step in steps:
                        html_parts.append(f"<li>{html.escape(step)}</li>")
                    html_parts.append("</ol>")
                html_parts.append("</div>")
            html_parts.append("</section>")

        # Tech debt section
        if tech_debt:
            debt_summary = tech_debt.get("summary", {})
            html_parts.append("<section class='tech-debt'>")
            html_parts.append("<h2>Technical Debt Summary</h2>")
            html_parts.append("<div class='metrics-grid'>")
            html_parts.append(
                f"<div class='metric-card'>"
                f"<span class='metric-value'>"
                f"{debt_summary.get('total_items', 0)}</span>"
                f"<span class='metric-label'>Total Items</span></div>"
            )
            html_parts.append(
                f"<div class='metric-card'>"
                f"<span class='metric-value'>"
                f"{debt_summary.get('total_estimated_hours', 0)}</span>"
                f"<span class='metric-label'>Estimated Hours</span></div>"
            )
            html_parts.append(
                f"<div class='metric-card critical'>"
                f"<span class='metric-value'>"
                f"{debt_summary.get('critical_count', 0)}</span>"
                f"<span class='metric-label'>Critical</span></div>"
            )
            html_parts.append("</div>")
            html_parts.append("</section>")

        html_parts.extend(["</body>", "</html>"])
        return "\n".join(html_parts)

    def _generate_text(self, data: Dict[str, Any]) -> str:
        """Generate plain text report."""
        lines = [
            "=" * 60,
            self.config.title.center(60),
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Summary
        summary = data.get("summary", {})
        if self.config.include_summary and summary:
            lines.append("SUMMARY")
            lines.append("-" * 40)
            for key, value in summary.items():
                display_key = key.replace("_", " ").title()
                lines.append(f"  {display_key}: {value}")
            lines.append("")

        # Violations
        violations = data.get("violations", [])
        if self.config.include_details and violations:
            lines.append("COMPLEXITY VIOLATIONS")
            lines.append("-" * 40)
            for v in violations[: self.config.max_items_per_section]:
                lines.append(
                    f"  [{v.get('type')}] {v.get('function')} "
                    f"(line {v.get('lineno')}): {v.get('value')} "
                    f"(threshold: {v.get('threshold')})"
                )
            lines.append("")

        # Code smells
        smells = data.get("smells", [])
        if self.config.include_details and smells:
            lines.append("CODE SMELLS")
            lines.append("-" * 40)
            for s in smells[: self.config.max_items_per_section]:
                lines.append(
                    f"  [{s.get('severity', '').upper()}] {s.get('name')} "
                    f"at {s.get('location')}:{s.get('lineno')}"
                )
                lines.append(f"    {s.get('description')}")
            lines.append("")

        # Suggestions
        suggestions = data.get("suggestions", [])
        if self.config.include_suggestions and suggestions:
            lines.append("REFACTORING SUGGESTIONS")
            lines.append("-" * 40)
            for i, s in enumerate(
                suggestions[: self.config.max_items_per_section], 1
            ):
                lines.append(f"  {i}. {s.get('title')}")
                lines.append(
                    f"     Location: {s.get('location')}:{s.get('lineno')}"
                )
                lines.append(f"     {s.get('description')}")
                lines.append(
                    f"     Impact: {s.get('impact')} | Effort: {s.get('effort')}"
                )
            lines.append("")

        # Tech debt
        tech_debt = data.get("tech_debt", {})
        if tech_debt:
            debt_summary = tech_debt.get("summary", {})
            lines.append("TECHNICAL DEBT")
            lines.append("-" * 40)
            lines.append(f"  Total Items: {debt_summary.get('total_items', 0)}")
            lines.append(
                f"  Estimated Hours: {debt_summary.get('total_estimated_hours', 0)}"
            )
            lines.append(f"  Critical: {debt_summary.get('critical_count', 0)}")
            lines.append(f"  High: {debt_summary.get('high_count', 0)}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def _generate_markdown(self, data: Dict[str, Any]) -> str:
        """Generate Markdown report."""
        lines = [
            f"# {self.config.title}",
            "",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
        ]

        # Summary
        summary = data.get("summary", {})
        if self.config.include_summary and summary:
            lines.append("## Summary")
            lines.append("")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            for key, value in summary.items():
                display_key = key.replace("_", " ").title()
                lines.append(f"| {display_key} | {value} |")
            lines.append("")

        # Violations
        violations = data.get("violations", [])
        if self.config.include_details and violations:
            lines.append("## Complexity Violations")
            lines.append("")
            lines.append("| Function | Type | Value | Threshold | Line |")
            lines.append("|----------|------|-------|-----------|------|")
            for v in violations[: self.config.max_items_per_section]:
                lines.append(
                    f"| {v.get('function', '')} | {v.get('type', '')} | "
                    f"{v.get('value', '')} | {v.get('threshold', '')} | "
                    f"{v.get('lineno', '')} |"
                )
            lines.append("")

        # Code smells
        smells = data.get("smells", [])
        if self.config.include_details and smells:
            lines.append("## Code Smells")
            lines.append("")
            for s in smells[: self.config.max_items_per_section]:
                severity = s.get("severity", "low").upper()
                lines.append(
                    f"### [{severity}] {s.get('name', '')} "
                    f"({s.get('location', '')}:{s.get('lineno', '')})"
                )
                lines.append("")
                lines.append(f"{s.get('description', '')}")
                if s.get("suggestion"):
                    lines.append("")
                    lines.append(f"**Suggestion:** {s.get('suggestion')}")
                lines.append("")

        # Suggestions
        suggestions = data.get("suggestions", [])
        if self.config.include_suggestions and suggestions:
            lines.append("## Refactoring Suggestions")
            lines.append("")
            for i, s in enumerate(
                suggestions[: self.config.max_items_per_section], 1
            ):
                lines.append(f"### {i}. {s.get('title', '')}")
                lines.append("")
                lines.append(
                    f"**Location:** `{s.get('location', '')}:{s.get('lineno', '')}`"
                )
                lines.append("")
                lines.append(s.get("description", ""))
                lines.append("")
                lines.append(
                    f"- **Impact:** {s.get('impact', '')}  "
                )
                lines.append(f"- **Effort:** {s.get('effort', '')}")
                steps = s.get("steps", [])
                if steps:
                    lines.append("")
                    lines.append("**Steps:**")
                    for step in steps:
                        lines.append(f"1. {step}")
                lines.append("")

        # Tech debt
        tech_debt = data.get("tech_debt", {})
        if tech_debt:
            debt_summary = tech_debt.get("summary", {})
            lines.append("## Technical Debt Summary")
            lines.append("")
            lines.append(f"- **Total Items:** {debt_summary.get('total_items', 0)}")
            lines.append(
                f"- **Estimated Hours:** "
                f"{debt_summary.get('total_estimated_hours', 0)}"
            )
            lines.append(f"- **Critical:** {debt_summary.get('critical_count', 0)}")
            lines.append(f"- **High Priority:** {debt_summary.get('high_count', 0)}")
            lines.append("")

        return "\n".join(lines)

    def _get_css(self) -> str:
        """Get CSS styles for HTML report."""
        return """
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: #f5f5f5;
}
h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
h2 { color: #555; margin-top: 30px; }
h3 { color: #666; }
.timestamp { color: #888; font-size: 0.9em; }
section { background: white; padding: 20px; margin: 20px 0; border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px; }
.metric-card { background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }
.metric-card.critical { background: #fee; }
.metric-value { display: block; font-size: 2em; font-weight: bold; color: #007bff; }
.metric-label { color: #666; font-size: 0.9em; }
table { width: 100%; border-collapse: collapse; margin: 10px 0; }
th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
th { background: #f8f9fa; font-weight: 600; }
.badge { padding: 3px 8px; border-radius: 12px; font-size: 0.8em; font-weight: 500; }
.badge-critical { background: #dc3545; color: white; }
.badge-high { background: #fd7e14; color: white; }
.badge-medium { background: #ffc107; color: #333; }
.badge-low { background: #28a745; color: white; }
.severity-critical { background: #fee; }
.severity-high { background: #fff3cd; }
.suggestion-card { background: #f8f9fa; padding: 15px; margin: 10px 0;
                   border-radius: 6px; border-left: 4px solid #007bff; }
.suggestion-card h3 { margin-top: 0; color: #007bff; }
ol { padding-left: 20px; }
pre { background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 6px;
      overflow-x: auto; }
"""

    def combine_results(
        self,
        complexity_result: Dict[str, Any],
        smell_result: Dict[str, Any],
        refactoring_result: Dict[str, Any],
        debt_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Combine results from different analyzers into a single report data.

        Args:
            complexity_result: Output from ComplexityAnalyzer
            smell_result: Output from CodeSmellDetector
            refactoring_result: Output from RefactoringAdvisor
            debt_result: Optional output from TechDebtTracker

        Returns:
            Combined data dictionary ready for report generation
        """
        return {
            "summary": {
                **complexity_result.get("summary", {}),
                "total_smells": smell_result.get("summary", {}).get("total", 0),
                "total_suggestions": refactoring_result.get("summary", {}).get(
                    "total", 0
                ),
            },
            "violations": complexity_result.get("violations", []),
            "smells": smell_result.get("smells", []),
            "duplicates": smell_result.get("duplicates", []),
            "suggestions": refactoring_result.get("suggestions", []),
            "tech_debt": debt_result or {},
            "files_analyzed": [
                complexity_result.get("filename"),
                smell_result.get("filename"),
            ],
        }
