"""
Audit Reporter for generating compliance reports.

Supports PDF, HTML, and CSV report formats.
Part of devCrew_s1 TOOL-SEC-011 compliance management platform.
"""

import csv
import io
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .compliance_manager import ComplianceScore, ComplianceFramework, ComplianceStatus


class ReportFormat(Enum):
    """Supported report formats."""

    PDF = "pdf"
    HTML = "html"
    CSV = "csv"
    JSON = "json"


@dataclass
class ReportSection:
    """A section within a compliance report."""

    title: str
    content: str
    data: Optional[Dict[str, Any]] = None


class AuditReporter:
    """
    Generates compliance audit reports in multiple formats.

    Supports PDF, HTML, CSV, and JSON output formats with
    customizable templates and sections.
    """

    def __init__(self, organization_name: str = "Organization"):
        self.organization_name = organization_name
        self._report_templates: Dict[str, str] = {}

    def generate_report(
        self,
        scores: Dict[ComplianceFramework, ComplianceScore],
        format_type: ReportFormat,
        output_path: Optional[Path] = None,
        include_details: bool = True,
    ) -> str:
        """
        Generate compliance report.

        Args:
            scores: Compliance scores by framework
            format_type: Output format
            output_path: Optional path to save report
            include_details: Include detailed control results

        Returns:
            Report content as string
        """
        if format_type == ReportFormat.HTML:
            content = self._generate_html_report(scores, include_details)
        elif format_type == ReportFormat.CSV:
            content = self._generate_csv_report(scores)
        elif format_type == ReportFormat.JSON:
            content = self._generate_json_report(scores, include_details)
        elif format_type == ReportFormat.PDF:
            content = self._generate_pdf_placeholder(scores, include_details)
        else:
            content = self._generate_json_report(scores, include_details)

        if output_path:
            output_path.write_text(content)

        return content

    def _generate_html_report(
        self, scores: Dict[ComplianceFramework, ComplianceScore], include_details: bool
    ) -> str:
        """Generate HTML format report."""
        timestamp = datetime.utcnow().isoformat()

        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            f"<title>Compliance Report - {self.organization_name}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1 { color: #333; }",
            "h2 { color: #555; border-bottom: 1px solid #ddd; padding-bottom: 10px; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }",
            "th { background-color: #4CAF50; color: white; }",
            "tr:nth-child(even) { background-color: #f2f2f2; }",
            ".compliant { color: green; font-weight: bold; }",
            ".non-compliant { color: red; font-weight: bold; }",
            ".partial { color: orange; font-weight: bold; }",
            ".score-high { background-color: #d4edda; }",
            ".score-medium { background-color: #fff3cd; }",
            ".score-low { background-color: #f8d7da; }",
            ".summary-box { background: #f9f9f9; padding: 20px; border-radius: 8px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>Compliance Audit Report</h1>",
            f"<p><strong>Organization:</strong> {self.organization_name}</p>",
            f"<p><strong>Generated:</strong> {timestamp}</p>",
            "<hr>",
        ]

        html_parts.append("<h2>Executive Summary</h2>")
        html_parts.append("<div class='summary-box'>")
        html_parts.append("<table>")
        html_parts.append("<tr><th>Framework</th><th>Score</th><th>Status</th>")
        html_parts.append("<th>Passed</th><th>Failed</th></tr>")

        for framework, score in scores.items():
            status_class = self._get_status_class(score.status)
            score_class = self._get_score_class(score.score)
            html_parts.append(
                f"<tr class='{score_class}'>"
                f"<td>{framework.value.upper()}</td>"
                f"<td>{score.score:.1f}%</td>"
                f"<td class='{status_class}'>{score.status.value}</td>"
                f"<td>{score.passed_controls}</td>"
                f"<td>{score.failed_controls}</td>"
                "</tr>"
            )

        html_parts.append("</table>")
        html_parts.append("</div>")

        if include_details:
            html_parts.append("<h2>Detailed Results</h2>")
            for framework, score in scores.items():
                html_parts.append(f"<h3>{framework.value.upper()}</h3>")
                controls = score.details.get("controls", [])
                if controls:
                    html_parts.append("<table>")
                    html_parts.append(
                        "<tr><th>Control ID</th><th>Name</th>"
                        "<th>Category</th><th>Status</th></tr>"
                    )
                    for control in controls:
                        status = "PASS" if control["passed"] else "FAIL"
                        status_class = "compliant" if control["passed"] else "non-compliant"
                        html_parts.append(
                            f"<tr>"
                            f"<td>{control['control_id']}</td>"
                            f"<td>{control['name']}</td>"
                            f"<td>{control['category']}</td>"
                            f"<td class='{status_class}'>{status}</td>"
                            "</tr>"
                        )
                    html_parts.append("</table>")

        html_parts.extend([
            "<hr>",
            "<footer>",
            "<p><em>Generated by devCrew_s1 Compliance Management Platform</em></p>",
            "</footer>",
            "</body>",
            "</html>",
        ])

        return "\n".join(html_parts)

    def _generate_csv_report(
        self, scores: Dict[ComplianceFramework, ComplianceScore]
    ) -> str:
        """Generate CSV format report."""
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Framework", "Score", "Status", "Total Controls",
            "Passed", "Failed", "Not Applicable", "Assessed At"
        ])

        for framework, score in scores.items():
            writer.writerow([
                framework.value,
                f"{score.score:.2f}",
                score.status.value,
                score.total_controls,
                score.passed_controls,
                score.failed_controls,
                score.not_applicable,
                score.assessed_at.isoformat(),
            ])

        writer.writerow([])
        writer.writerow(["Control Details"])
        writer.writerow([
            "Framework", "Control ID", "Name", "Category", "Passed", "Violations"
        ])

        for framework, score in scores.items():
            for control in score.details.get("controls", []):
                violations = "; ".join(
                    v.get("message", "") for v in control.get("violations", [])
                )
                writer.writerow([
                    framework.value,
                    control["control_id"],
                    control["name"],
                    control["category"],
                    "Yes" if control["passed"] else "No",
                    violations,
                ])

        return output.getvalue()

    def _generate_json_report(
        self, scores: Dict[ComplianceFramework, ComplianceScore], include_details: bool
    ) -> str:
        """Generate JSON format report."""
        report = {
            "report_metadata": {
                "organization": self.organization_name,
                "generated_at": datetime.utcnow().isoformat(),
                "generator": "devCrew_s1 Compliance Management Platform",
            },
            "summary": {
                "frameworks_assessed": len(scores),
                "overall_status": self._calculate_overall_status(scores),
            },
            "framework_scores": {},
        }

        for framework, score in scores.items():
            score_dict = score.to_dict()
            if not include_details:
                score_dict.pop("details", None)
            report["framework_scores"][framework.value] = score_dict

        return json.dumps(report, indent=2)

    def _generate_pdf_placeholder(
        self, scores: Dict[ComplianceFramework, ComplianceScore], include_details: bool
    ) -> str:
        """
        Generate PDF placeholder content.

        Note: Full PDF generation requires reportlab or similar library.
        This returns a text representation that can be converted to PDF.
        """
        lines = [
            "=" * 60,
            "COMPLIANCE AUDIT REPORT",
            "=" * 60,
            "",
            f"Organization: {self.organization_name}",
            f"Generated: {datetime.utcnow().isoformat()}",
            "",
            "-" * 60,
            "EXECUTIVE SUMMARY",
            "-" * 60,
            "",
        ]

        for framework, score in scores.items():
            lines.append(f"Framework: {framework.value.upper()}")
            lines.append(f"  Score: {score.score:.1f}%")
            lines.append(f"  Status: {score.status.value}")
            lines.append(f"  Controls: {score.passed_controls}/{score.total_controls} passed")
            lines.append("")

        if include_details:
            lines.append("-" * 60)
            lines.append("DETAILED RESULTS")
            lines.append("-" * 60)
            lines.append("")

            for framework, score in scores.items():
                lines.append(f"[{framework.value.upper()}]")
                for control in score.details.get("controls", []):
                    status = "PASS" if control["passed"] else "FAIL"
                    lines.append(f"  {control['control_id']}: {status}")
                    if not control["passed"]:
                        for v in control.get("violations", []):
                            lines.append(f"    - {v.get('message', '')}")
                lines.append("")

        lines.extend([
            "=" * 60,
            "Generated by devCrew_s1 Compliance Management Platform",
            "=" * 60,
        ])

        return "\n".join(lines)

    def _get_status_class(self, status: ComplianceStatus) -> str:
        """Get CSS class for status."""
        return {
            ComplianceStatus.COMPLIANT: "compliant",
            ComplianceStatus.NON_COMPLIANT: "non-compliant",
            ComplianceStatus.PARTIAL: "partial",
            ComplianceStatus.NOT_ASSESSED: "partial",
        }.get(status, "")

    def _get_score_class(self, score: float) -> str:
        """Get CSS class for score."""
        if score >= 80:
            return "score-high"
        elif score >= 50:
            return "score-medium"
        return "score-low"

    def _calculate_overall_status(
        self, scores: Dict[ComplianceFramework, ComplianceScore]
    ) -> str:
        """Calculate overall compliance status."""
        if not scores:
            return "not_assessed"

        all_compliant = all(
            s.status == ComplianceStatus.COMPLIANT for s in scores.values()
        )
        any_non_compliant = any(
            s.status == ComplianceStatus.NON_COMPLIANT for s in scores.values()
        )

        if all_compliant:
            return "compliant"
        elif any_non_compliant:
            return "non_compliant"
        return "partial"

    def generate_executive_summary(
        self, scores: Dict[ComplianceFramework, ComplianceScore]
    ) -> str:
        """Generate executive summary text."""
        total_frameworks = len(scores)
        compliant_count = sum(
            1 for s in scores.values() if s.status == ComplianceStatus.COMPLIANT
        )
        avg_score = (
            sum(s.score for s in scores.values()) / total_frameworks
            if total_frameworks > 0 else 0
        )

        return (
            f"Assessment of {total_frameworks} compliance frameworks completed. "
            f"{compliant_count} frameworks fully compliant. "
            f"Average compliance score: {avg_score:.1f}%."
        )

    def generate_recommendations(
        self, scores: Dict[ComplianceFramework, ComplianceScore]
    ) -> List[str]:
        """Generate recommendations based on assessment results."""
        recommendations: List[str] = []

        for framework, score in scores.items():
            if score.status != ComplianceStatus.COMPLIANT:
                for control in score.details.get("controls", []):
                    if not control["passed"]:
                        for violation in control.get("violations", []):
                            recommendations.append(
                                f"[{framework.value.upper()}] {violation.get('message', '')}"
                            )

        return recommendations[:10]  # Top 10 recommendations
