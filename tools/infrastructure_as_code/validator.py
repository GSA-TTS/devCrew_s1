"""
Security and compliance validation for Terraform configurations.

This module integrates with Checkov and tfsec to scan Terraform
configurations for security issues, compliance violations, and
best practice violations.
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum


logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Severity levels for validation findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ValidationError(Exception):
    """Base exception for validation operations."""
    pass


@dataclass
class ValidationFinding:
    """Container for a single validation finding."""
    check_id: str
    check_name: str
    severity: SeverityLevel
    resource: str
    file_path: str
    line_range: tuple
    description: str
    remediation: Optional[str] = None


@dataclass
class ValidationReport:
    """Container for validation results."""
    passed: int
    failed: int
    skipped: int
    findings: List[ValidationFinding]
    summary: Dict[str, int]
    scan_duration: float


class TerraformValidator:
    """
    Validator for Terraform configurations.

    Integrates with security scanning tools to identify issues
    before deployment.
    """

    def __init__(
        self,
        working_dir: str,
        enable_checkov: bool = True,
        enable_tfsec: bool = True,
        custom_policies_dir: Optional[str] = None
    ):
        """
        Initialize validator.

        Args:
            working_dir: Directory containing Terraform configurations
            enable_checkov: Enable Checkov scanning
            enable_tfsec: Enable tfsec scanning
            custom_policies_dir: Directory containing custom policies
        """
        self.working_dir = Path(working_dir)
        self.enable_checkov = enable_checkov
        self.enable_tfsec = enable_tfsec
        self.custom_policies_dir = Path(custom_policies_dir) \
            if custom_policies_dir else None

        if not self.working_dir.exists():
            raise ValidationError(
                f"Working directory does not exist: {working_dir}"
            )

        self._check_tools()

    def _check_tools(self) -> None:
        """Check if validation tools are installed."""
        if self.enable_checkov:
            try:
                subprocess.run(
                    ["checkov", "--version"],
                    capture_output=True,
                    check=True
                )
                logger.info("Checkov is available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning(
                    "Checkov not found. Install with: pip install checkov"
                )
                self.enable_checkov = False

        if self.enable_tfsec:
            try:
                subprocess.run(
                    ["tfsec", "--version"],
                    capture_output=True,
                    check=True
                )
                logger.info("tfsec is available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning(
                    "tfsec not found. Install from: https://github.com/aquasecurity/tfsec"
                )
                self.enable_tfsec = False

    def validate(
        self,
        framework: Optional[str] = None,
        severity_threshold: SeverityLevel = SeverityLevel.MEDIUM
    ) -> ValidationReport:
        """
        Run validation checks on Terraform configurations.

        Args:
            framework: Compliance framework (e.g., 'cis-aws', 'pci-dss')
            severity_threshold: Minimum severity to report

        Returns:
            ValidationReport with findings

        Raises:
            ValidationError: If validation fails
        """
        import time

        start_time = time.time()
        all_findings = []

        if self.enable_checkov:
            checkov_findings = self._run_checkov(framework)
            all_findings.extend(checkov_findings)

        if self.enable_tfsec:
            tfsec_findings = self._run_tfsec()
            all_findings.extend(tfsec_findings)

        # Filter by severity threshold
        filtered_findings = self._filter_by_severity(
            all_findings,
            severity_threshold
        )

        # Generate summary
        summary = self._generate_summary(filtered_findings)

        duration = time.time() - start_time

        return ValidationReport(
            passed=summary.get("passed", 0),
            failed=len(filtered_findings),
            skipped=summary.get("skipped", 0),
            findings=filtered_findings,
            summary=summary,
            scan_duration=duration
        )

    def _run_checkov(self, framework: Optional[str] = None) -> List[ValidationFinding]:
        """
        Run Checkov security scanner.

        Args:
            framework: Compliance framework to check against

        Returns:
            List of ValidationFinding objects
        """
        logger.info("Running Checkov scan...")

        cmd = [
            "checkov",
            "--directory", str(self.working_dir),
            "--framework", "terraform",
            "--output", "json",
            "--quiet"
        ]

        if framework:
            cmd.extend(["--check", framework])

        if self.custom_policies_dir:
            cmd.extend(["--external-checks-dir", str(self.custom_policies_dir)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Checkov returns non-zero on findings, which is expected
            if result.stdout:
                return self._parse_checkov_output(result.stdout)
            else:
                logger.warning(f"Checkov produced no output: {result.stderr}")
                return []

        except subprocess.TimeoutExpired:
            logger.error("Checkov scan timed out")
            return []
        except Exception as e:
            logger.error(f"Checkov scan failed: {e}")
            return []

    def _parse_checkov_output(self, output: str) -> List[ValidationFinding]:
        """
        Parse Checkov JSON output.

        Args:
            output: Checkov JSON output

        Returns:
            List of ValidationFinding objects
        """
        findings = []

        try:
            data = json.loads(output)

            for result in data.get("results", {}).get("failed_checks", []):
                severity = self._map_checkov_severity(
                    result.get("check_class", "")
                )

                finding = ValidationFinding(
                    check_id=result.get("check_id", ""),
                    check_name=result.get("check_name", ""),
                    severity=severity,
                    resource=result.get("resource", ""),
                    file_path=result.get("file_path", ""),
                    line_range=(
                        result.get("file_line_range", [0, 0])[0],
                        result.get("file_line_range", [0, 0])[1]
                    ),
                    description=result.get("check_result", {}).get("result", ""),
                    remediation=result.get("guideline", "")
                )

                findings.append(finding)

            logger.info(f"Checkov found {len(findings)} issues")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Checkov output: {e}")

        return findings

    def _map_checkov_severity(self, check_class: str) -> SeverityLevel:
        """Map Checkov check class to severity level."""
        severity_map = {
            "CRITICAL": SeverityLevel.CRITICAL,
            "HIGH": SeverityLevel.HIGH,
            "MEDIUM": SeverityLevel.MEDIUM,
            "LOW": SeverityLevel.LOW,
        }

        # Extract severity from check class if present
        for key in severity_map:
            if key in check_class.upper():
                return severity_map[key]

        return SeverityLevel.MEDIUM

    def _run_tfsec(self) -> List[ValidationFinding]:
        """
        Run tfsec security scanner.

        Returns:
            List of ValidationFinding objects
        """
        logger.info("Running tfsec scan...")

        cmd = [
            "tfsec",
            str(self.working_dir),
            "--format", "json",
            "--no-color"
        ]

        if self.custom_policies_dir:
            cmd.extend(["--custom-check-dir", str(self.custom_policies_dir)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            # tfsec returns non-zero on findings
            if result.stdout:
                return self._parse_tfsec_output(result.stdout)
            else:
                logger.warning(f"tfsec produced no output: {result.stderr}")
                return []

        except subprocess.TimeoutExpired:
            logger.error("tfsec scan timed out")
            return []
        except Exception as e:
            logger.error(f"tfsec scan failed: {e}")
            return []

    def _parse_tfsec_output(self, output: str) -> List[ValidationFinding]:
        """
        Parse tfsec JSON output.

        Args:
            output: tfsec JSON output

        Returns:
            List of ValidationFinding objects
        """
        findings = []

        try:
            data = json.loads(output)

            for result in data.get("results", []):
                severity = self._map_tfsec_severity(result.get("severity", ""))

                finding = ValidationFinding(
                    check_id=result.get("rule_id", ""),
                    check_name=result.get("rule_description", ""),
                    severity=severity,
                    resource=result.get("resource", ""),
                    file_path=result.get("location", {}).get("filename", ""),
                    line_range=(
                        result.get("location", {}).get("start_line", 0),
                        result.get("location", {}).get("end_line", 0)
                    ),
                    description=result.get("description", ""),
                    remediation=result.get("links", [None])[0] if result.get("links") else None
                )

                findings.append(finding)

            logger.info(f"tfsec found {len(findings)} issues")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tfsec output: {e}")

        return findings

    def _map_tfsec_severity(self, severity: str) -> SeverityLevel:
        """Map tfsec severity to SeverityLevel."""
        severity_map = {
            "CRITICAL": SeverityLevel.CRITICAL,
            "HIGH": SeverityLevel.HIGH,
            "MEDIUM": SeverityLevel.MEDIUM,
            "LOW": SeverityLevel.LOW,
            "INFO": SeverityLevel.INFO,
        }

        return severity_map.get(severity.upper(), SeverityLevel.MEDIUM)

    def _filter_by_severity(
        self,
        findings: List[ValidationFinding],
        threshold: SeverityLevel
    ) -> List[ValidationFinding]:
        """
        Filter findings by severity threshold.

        Args:
            findings: All findings
            threshold: Minimum severity level

        Returns:
            Filtered findings
        """
        severity_order = [
            SeverityLevel.CRITICAL,
            SeverityLevel.HIGH,
            SeverityLevel.MEDIUM,
            SeverityLevel.LOW,
            SeverityLevel.INFO
        ]

        threshold_index = severity_order.index(threshold)

        return [
            f for f in findings
            if severity_order.index(f.severity) <= threshold_index
        ]

    def _generate_summary(
        self,
        findings: List[ValidationFinding]
    ) -> Dict[str, int]:
        """
        Generate summary statistics.

        Args:
            findings: Validation findings

        Returns:
            Summary dictionary
        """
        summary = {
            "total": len(findings),
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

        for finding in findings:
            summary[finding.severity.value.lower()] += 1

        return summary

    def generate_report(
        self,
        report: ValidationReport,
        output_format: str = "text",
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate validation report in specified format.

        Args:
            report: ValidationReport to format
            output_format: Report format (text, json, html)
            output_file: Optional file to write report to

        Returns:
            Formatted report as string
        """
        if output_format == "json":
            report_str = self._generate_json_report(report)
        elif output_format == "html":
            report_str = self._generate_html_report(report)
        else:
            report_str = self._generate_text_report(report)

        if output_file:
            Path(output_file).write_text(report_str)
            logger.info(f"Report written to: {output_file}")

        return report_str

    def _generate_text_report(self, report: ValidationReport) -> str:
        """Generate text format report."""
        lines = [
            "=" * 80,
            "Terraform Validation Report",
            "=" * 80,
            f"Scan Duration: {report.scan_duration:.2f}s",
            f"Total Checks: {report.passed + report.failed}",
            f"Passed: {report.passed}",
            f"Failed: {report.failed}",
            f"Skipped: {report.skipped}",
            "",
            "Severity Breakdown:",
            f"  Critical: {report.summary.get('critical', 0)}",
            f"  High:     {report.summary.get('high', 0)}",
            f"  Medium:   {report.summary.get('medium', 0)}",
            f"  Low:      {report.summary.get('low', 0)}",
            f"  Info:     {report.summary.get('info', 0)}",
            "",
            "=" * 80,
            "Findings:",
            "=" * 80,
        ]

        for i, finding in enumerate(report.findings, 1):
            lines.extend([
                f"\n{i}. [{finding.severity.value}] {finding.check_name}",
                f"   ID: {finding.check_id}",
                f"   Resource: {finding.resource}",
                f"   File: {finding.file_path}:{finding.line_range[0]}-{finding.line_range[1]}",
                f"   Description: {finding.description}",
            ])

            if finding.remediation:
                lines.append(f"   Remediation: {finding.remediation}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    def _generate_json_report(self, report: ValidationReport) -> str:
        """Generate JSON format report."""
        report_data = {
            "scan_duration": report.scan_duration,
            "summary": {
                "total": report.passed + report.failed,
                "passed": report.passed,
                "failed": report.failed,
                "skipped": report.skipped,
            },
            "severity_breakdown": report.summary,
            "findings": [
                {
                    "check_id": f.check_id,
                    "check_name": f.check_name,
                    "severity": f.severity.value,
                    "resource": f.resource,
                    "file_path": f.file_path,
                    "line_range": f.line_range,
                    "description": f.description,
                    "remediation": f.remediation,
                }
                for f in report.findings
            ]
        }

        return json.dumps(report_data, indent=2)

    def _generate_html_report(self, report: ValidationReport) -> str:
        """Generate HTML format report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Terraform Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f0f0f0; padding: 15px; margin: 20px 0; }}
        .finding {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; }}
        .critical {{ border-left: 5px solid #d32f2f; }}
        .high {{ border-left: 5px solid #f57c00; }}
        .medium {{ border-left: 5px solid #ffa000; }}
        .low {{ border-left: 5px solid #388e3c; }}
        .info {{ border-left: 5px solid #1976d2; }}
        .severity {{ font-weight: bold; padding: 2px 8px; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>Terraform Validation Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <p>Scan Duration: {report.scan_duration:.2f}s</p>
        <p>Total Checks: {report.passed + report.failed}</p>
        <p>Passed: {report.passed} | Failed: {report.failed} | Skipped: {report.skipped}</p>

        <h3>Severity Breakdown</h3>
        <ul>
            <li>Critical: {report.summary.get('critical', 0)}</li>
            <li>High: {report.summary.get('high', 0)}</li>
            <li>Medium: {report.summary.get('medium', 0)}</li>
            <li>Low: {report.summary.get('low', 0)}</li>
            <li>Info: {report.summary.get('info', 0)}</li>
        </ul>
    </div>

    <h2>Findings</h2>
"""

        for finding in report.findings:
            severity_class = finding.severity.value.lower()
            html += f"""
    <div class="finding {severity_class}">
        <span class="severity">[{finding.severity.value}]</span>
        <strong>{finding.check_name}</strong>
        <p><strong>ID:</strong> {finding.check_id}</p>
        <p><strong>Resource:</strong> {finding.resource}</p>
        <p><strong>File:</strong> {finding.file_path}:{finding.line_range[0]}-{finding.line_range[1]}</p>
        <p><strong>Description:</strong> {finding.description}</p>
"""
            if finding.remediation:
                html += f"        <p><strong>Remediation:</strong> {finding.remediation}</p>\n"

            html += "    </div>\n"

        html += """
</body>
</html>
"""

        return html
