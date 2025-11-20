"""
Quality Gates Module
Issue #36 - TOOL-CICD-001

Validates code coverage, security scans, and code quality metrics
against configured thresholds.
"""

import json
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


@dataclass
class CoverageReport:
    """Coverage report data structure."""

    total_coverage: float
    line_coverage: float
    branch_coverage: float
    files_covered: int
    total_files: int
    lines_covered: int
    total_lines: int


@dataclass
class SecurityReport:
    """Security scan report data structure."""

    high_severity: int
    medium_severity: int
    low_severity: int
    total_issues: int
    findings: List[Dict[str, Any]]


@dataclass
class QualityReport:
    """Code quality report data structure."""

    complexity_score: float
    duplication_percentage: float
    violations: List[Dict[str, Any]]
    max_complexity: int
    average_complexity: float


class QualityGateError(Exception):
    """Base exception for quality gate failures."""

    pass


class CoverageThresholdError(QualityGateError):
    """Raised when coverage is below threshold."""

    pass


class SecurityThresholdError(QualityGateError):
    """Raised when security issues exceed threshold."""

    pass


class CodeQualityThresholdError(QualityGateError):
    """Raised when code quality is below threshold."""

    pass


class QualityGates:
    """
    Quality gate validation for CI/CD pipelines.

    Validates coverage, security, and code quality metrics against
    configured thresholds with detailed reporting.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize quality gates with configuration.

        Args:
            config: Configuration dictionary with thresholds
        """
        self.config = config
        self.quality_config = config.get("quality_gates", {})

        # Extract thresholds
        self.coverage_config = self.quality_config.get("coverage", {})
        self.security_config = self.quality_config.get("security", {})
        self.code_quality_config = self.quality_config.get("code_quality", {})

        logger.info("Initialized quality gates with configuration")

    def validate_coverage(
        self, report_path: str, fail_on_threshold: bool = True
    ) -> Tuple[bool, CoverageReport]:
        """
        Validate test coverage against thresholds.

        Args:
            report_path: Path to coverage report (XML or JSON)
            fail_on_threshold: Raise exception if below threshold

        Returns:
            Tuple of (passed, coverage_report)

        Raises:
            CoverageThresholdError: If coverage below threshold and fail_on_threshold
        """
        report_path_obj = Path(report_path)

        if not report_path_obj.exists():
            raise FileNotFoundError(f"Coverage report not found: {report_path}")

        # Parse coverage report based on format
        if report_path.endswith(".xml"):
            coverage = self._parse_coverage_xml(report_path)
        elif report_path.endswith(".json"):
            coverage = self._parse_coverage_json(report_path)
        else:
            raise ValueError(f"Unsupported coverage format: {report_path}")

        # Check threshold
        minimum_coverage = self.coverage_config.get("minimum", 80.0)
        passed = coverage.total_coverage >= minimum_coverage

        logger.info(
            f"Coverage: {coverage.total_coverage:.2f}% "
            f"(threshold: {minimum_coverage}%)"
        )

        if not passed and fail_on_threshold:
            raise CoverageThresholdError(
                f"Coverage {coverage.total_coverage:.2f}% is below "
                f"minimum threshold {minimum_coverage}%"
            )

        return passed, coverage

    def _parse_coverage_xml(self, report_path: str) -> CoverageReport:
        """
        Parse Cobertura XML coverage report.

        Args:
            report_path: Path to XML report

        Returns:
            CoverageReport object
        """
        tree = ET.parse(report_path)
        root = tree.getroot()

        # Parse coverage attributes
        line_rate = float(root.attrib.get("line-rate", 0))
        branch_rate = float(root.attrib.get("branch-rate", 0))

        # Calculate total coverage (weighted average)
        total_coverage = (line_rate * 0.7 + branch_rate * 0.3) * 100

        # Count files
        files = root.findall(".//class")
        files_covered = len(files)

        # Count lines
        lines = root.findall(".//line")
        lines_covered = sum(1 for line in lines if line.attrib.get("hits", "0") != "0")
        total_lines = len(lines)

        return CoverageReport(
            total_coverage=total_coverage,
            line_coverage=line_rate * 100,
            branch_coverage=branch_rate * 100,
            files_covered=files_covered,
            total_files=files_covered,
            lines_covered=lines_covered,
            total_lines=total_lines,
        )

    def _parse_coverage_json(self, report_path: str) -> CoverageReport:
        """
        Parse coverage.py JSON report.

        Args:
            report_path: Path to JSON report

        Returns:
            CoverageReport object
        """
        with open(report_path, "r") as f:
            data = json.load(f)

        totals = data.get("totals", {})
        total_coverage = totals.get("percent_covered", 0)

        files = data.get("files", {})
        files_covered = len([f for f in files.values() if f.get("summary", {}).get("percent_covered", 0) > 0])
        total_files = len(files)

        lines_covered = totals.get("covered_lines", 0)
        total_lines = totals.get("num_statements", 0)

        return CoverageReport(
            total_coverage=total_coverage,
            line_coverage=total_coverage,
            branch_coverage=totals.get("percent_covered_display", 0),
            files_covered=files_covered,
            total_files=total_files,
            lines_covered=lines_covered,
            total_lines=total_lines,
        )

    def validate_security(
        self, report_path: str, fail_on_threshold: bool = True
    ) -> Tuple[bool, SecurityReport]:
        """
        Validate security scan results against thresholds.

        Args:
            report_path: Path to security report (JSON)
            fail_on_threshold: Raise exception if exceeds threshold

        Returns:
            Tuple of (passed, security_report)

        Raises:
            SecurityThresholdError: If issues exceed threshold
        """
        if not Path(report_path).exists():
            raise FileNotFoundError(f"Security report not found: {report_path}")

        # Parse security report
        security = self._parse_security_report(report_path)

        # Check thresholds
        max_high = self.security_config.get("max_high_severity", 0)
        max_medium = self.security_config.get("max_medium_severity", 5)
        fail_on_high = self.security_config.get("fail_on_high", True)

        passed = True
        reasons = []

        if security.high_severity > max_high:
            passed = False
            reasons.append(
                f"{security.high_severity} high severity issues "
                f"(max: {max_high})"
            )

        if security.medium_severity > max_medium:
            passed = False
            reasons.append(
                f"{security.medium_severity} medium severity issues "
                f"(max: {max_medium})"
            )

        logger.info(
            f"Security scan: {security.total_issues} issues "
            f"(H:{security.high_severity} M:{security.medium_severity} "
            f"L:{security.low_severity})"
        )

        if not passed and fail_on_threshold:
            raise SecurityThresholdError(
                f"Security issues exceed threshold: {', '.join(reasons)}"
            )

        return passed, security

    def _parse_security_report(self, report_path: str) -> SecurityReport:
        """
        Parse Bandit/Semgrep JSON security report.

        Args:
            report_path: Path to JSON report

        Returns:
            SecurityReport object
        """
        with open(report_path, "r") as f:
            data = json.load(f)

        findings = []
        high_count = 0
        medium_count = 0
        low_count = 0

        # Handle Bandit format
        if "results" in data:
            for result in data["results"]:
                severity = result.get("issue_severity", "").upper()
                findings.append(
                    {
                        "severity": severity,
                        "confidence": result.get("issue_confidence", ""),
                        "message": result.get("issue_text", ""),
                        "file": result.get("filename", ""),
                        "line": result.get("line_number", 0),
                    }
                )

                if severity == "HIGH":
                    high_count += 1
                elif severity == "MEDIUM":
                    medium_count += 1
                else:
                    low_count += 1

        # Handle Semgrep format
        elif "results" in data and isinstance(data["results"], list):
            for result in data["results"]:
                severity = result.get("extra", {}).get("severity", "").upper()
                findings.append(
                    {
                        "severity": severity,
                        "message": result.get("extra", {}).get("message", ""),
                        "file": result.get("path", ""),
                        "line": result.get("start", {}).get("line", 0),
                    }
                )

                if "ERROR" in severity or "HIGH" in severity:
                    high_count += 1
                elif "WARNING" in severity or "MEDIUM" in severity:
                    medium_count += 1
                else:
                    low_count += 1

        return SecurityReport(
            high_severity=high_count,
            medium_severity=medium_count,
            low_severity=low_count,
            total_issues=len(findings),
            findings=findings,
        )

    def validate_code_quality(
        self, report_path: str, fail_on_threshold: bool = True
    ) -> Tuple[bool, QualityReport]:
        """
        Validate code quality metrics against thresholds.

        Args:
            report_path: Path to quality report (JSON)
            fail_on_threshold: Raise exception if below threshold

        Returns:
            Tuple of (passed, quality_report)

        Raises:
            CodeQualityThresholdError: If quality below threshold
        """
        if not Path(report_path).exists():
            raise FileNotFoundError(f"Quality report not found: {report_path}")

        # Parse quality report
        quality = self._parse_quality_report(report_path)

        # Check thresholds
        max_complexity = self.code_quality_config.get("max_complexity", 10)
        max_duplication = self.code_quality_config.get("max_duplication", 5.0)

        passed = True
        reasons = []

        if quality.max_complexity > max_complexity:
            passed = False
            reasons.append(
                f"Max complexity {quality.max_complexity} exceeds "
                f"threshold {max_complexity}"
            )

        if quality.duplication_percentage > max_duplication:
            passed = False
            reasons.append(
                f"Duplication {quality.duplication_percentage:.2f}% exceeds "
                f"threshold {max_duplication}%"
            )

        logger.info(
            f"Code quality: complexity={quality.average_complexity:.2f}, "
            f"duplication={quality.duplication_percentage:.2f}%"
        )

        if not passed and fail_on_threshold:
            raise CodeQualityThresholdError(
                f"Code quality below threshold: {', '.join(reasons)}"
            )

        return passed, quality

    def _parse_quality_report(self, report_path: str) -> QualityReport:
        """
        Parse code quality report (radon/pylint JSON).

        Args:
            report_path: Path to JSON report

        Returns:
            QualityReport object
        """
        with open(report_path, "r") as f:
            data = json.load(f)

        violations = []
        complexity_scores = []
        max_complexity = 0

        # Parse complexity data
        if "complexity" in data:
            for file_data in data["complexity"].values():
                for func in file_data:
                    complexity = func.get("complexity", 0)
                    complexity_scores.append(complexity)
                    max_complexity = max(max_complexity, complexity)

                    if complexity > 10:
                        violations.append(
                            {
                                "type": "complexity",
                                "file": func.get("file", ""),
                                "function": func.get("name", ""),
                                "value": complexity,
                            }
                        )

        average_complexity = (
            sum(complexity_scores) / len(complexity_scores)
            if complexity_scores
            else 0
        )

        # Parse duplication data
        duplication = data.get("duplication", {}).get("percentage", 0)

        return QualityReport(
            complexity_score=average_complexity,
            duplication_percentage=duplication,
            violations=violations,
            max_complexity=max_complexity,
            average_complexity=average_complexity,
        )

    def generate_report(
        self,
        coverage: Optional[CoverageReport] = None,
        security: Optional[SecurityReport] = None,
        quality: Optional[QualityReport] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive quality gate report.

        Args:
            coverage: Coverage report data
            security: Security report data
            quality: Quality report data
            output_path: Optional path to save report JSON

        Returns:
            Dictionary with complete report
        """
        report = {
            "timestamp": str(Path(__file__).stat().st_mtime),
            "passed": True,
            "gates": {},
        }

        # Add coverage
        if coverage:
            coverage_passed = coverage.total_coverage >= self.coverage_config.get(
                "minimum", 80.0
            )
            report["gates"]["coverage"] = {
                "passed": coverage_passed,
                "total_coverage": coverage.total_coverage,
                "line_coverage": coverage.line_coverage,
                "branch_coverage": coverage.branch_coverage,
                "threshold": self.coverage_config.get("minimum", 80.0),
            }
            report["passed"] = report["passed"] and coverage_passed

        # Add security
        if security:
            security_passed = security.high_severity <= self.security_config.get(
                "max_high_severity", 0
            )
            report["gates"]["security"] = {
                "passed": security_passed,
                "high_severity": security.high_severity,
                "medium_severity": security.medium_severity,
                "low_severity": security.low_severity,
                "total_issues": security.total_issues,
            }
            report["passed"] = report["passed"] and security_passed

        # Add quality
        if quality:
            quality_passed = (
                quality.max_complexity
                <= self.code_quality_config.get("max_complexity", 10)
            )
            report["gates"]["quality"] = {
                "passed": quality_passed,
                "average_complexity": quality.average_complexity,
                "max_complexity": quality.max_complexity,
                "duplication": quality.duplication_percentage,
            }
            report["passed"] = report["passed"] and quality_passed

        # Save to file if requested
        if output_path:
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Quality gate report saved to {output_path}")

        return report

    def validate_all(
        self,
        coverage_path: Optional[str] = None,
        security_path: Optional[str] = None,
        quality_path: Optional[str] = None,
        fail_fast: bool = False,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate all quality gates.

        Args:
            coverage_path: Path to coverage report
            security_path: Path to security report
            quality_path: Path to quality report
            fail_fast: Stop on first failure

        Returns:
            Tuple of (all_passed, detailed_report)

        Raises:
            QualityGateError: If any gate fails and fail_fast is True
        """
        coverage_report = None
        security_report = None
        quality_report = None
        all_passed = True

        # Validate coverage
        if coverage_path:
            try:
                passed, coverage_report = self.validate_coverage(
                    coverage_path, fail_on_threshold=fail_fast
                )
                all_passed = all_passed and passed
            except QualityGateError as e:
                if fail_fast:
                    raise
                logger.error(f"Coverage validation failed: {e}")
                all_passed = False

        # Validate security
        if security_path:
            try:
                passed, security_report = self.validate_security(
                    security_path, fail_on_threshold=fail_fast
                )
                all_passed = all_passed and passed
            except QualityGateError as e:
                if fail_fast:
                    raise
                logger.error(f"Security validation failed: {e}")
                all_passed = False

        # Validate quality
        if quality_path:
            try:
                passed, quality_report = self.validate_code_quality(
                    quality_path, fail_on_threshold=fail_fast
                )
                all_passed = all_passed and passed
            except QualityGateError as e:
                if fail_fast:
                    raise
                logger.error(f"Quality validation failed: {e}")
                all_passed = False

        # Generate comprehensive report
        report = self.generate_report(coverage_report, security_report, quality_report)

        return all_passed, report
