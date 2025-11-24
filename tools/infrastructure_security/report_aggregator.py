"""
Report Aggregator for Infrastructure Security Scanner Platform.

Aggregates results from multiple security scanners (Trivy, Checkov, tfsec,
Terrascan, OPA) into unified reports with SARIF generation, GitHub integration,
trend analysis, and multi-format output (HTML, PDF, Markdown, JSON).

This module implements:
- Multi-scanner result aggregation with deduplication
- SARIF 2.1.0 report generation for GitHub Code Scanning
- Severity prioritization and ranking
- Historical trend analysis
- HTML/PDF/Markdown report generation
- GitHub API integration for SARIF upload
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    """Supported output report formats."""

    SARIF = "sarif"
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"


class SeverityLevel(str, Enum):
    """Severity levels for security findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    UNKNOWN = "unknown"

    def to_sarif_level(self) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            "critical": "error",
            "high": "error",
            "medium": "warning",
            "low": "note",
            "info": "note",
            "unknown": "none",
        }
        return mapping.get(self.value, "none")

    def get_priority(self) -> int:
        """Get numeric priority for sorting (higher is more severe)."""
        priority_map = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "info": 1,
            "unknown": 0,
        }
        return priority_map.get(self.value, 0)


class TrendDirection(str, Enum):
    """Trend direction for comparison analysis."""

    IMPROVING = "improving"
    WORSENING = "worsening"
    STABLE = "stable"
    UNKNOWN = "unknown"


class SARIFLocation(BaseModel):
    """SARIF location information."""

    uri: str
    start_line: Optional[int] = None
    start_column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class SARIFMessage(BaseModel):
    """SARIF message object."""

    text: str
    markdown: Optional[str] = None

    class Config:
        """Pydantic config."""

        use_enum_values = True


class SARIFResult(BaseModel):
    """SARIF result representing a single finding."""

    ruleId: str
    message: SARIFMessage
    level: str = "warning"
    locations: List[Dict[str, Any]] = Field(default_factory=list)
    properties: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic config."""

        use_enum_values = True
        populate_by_name = True


class SARIFTool(BaseModel):
    """SARIF tool information."""

    driver: Dict[str, Any]

    class Config:
        """Pydantic config."""

        use_enum_values = True


class SARIFInvocation(BaseModel):
    """SARIF invocation information."""

    executionSuccessful: bool = True
    endTimeUtc: str

    class Config:
        """Pydantic config."""

        use_enum_values = True
        populate_by_name = True


class SARIFRun(BaseModel):
    """SARIF run containing tool and results."""

    tool: SARIFTool
    results: List[SARIFResult] = Field(default_factory=list)
    invocations: List[SARIFInvocation] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        use_enum_values = True


class SARIFReport(BaseModel):
    """SARIF 2.1.0 format report."""

    version: str = "2.1.0"
    schema_: str = Field(
        default=(
            "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/"
            "master/Schemata/sarif-schema-2.1.0.json"
        ),
        alias="$schema",
    )
    runs: List[SARIFRun] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        use_enum_values = True
        populate_by_name = True


class SecurityFinding(BaseModel):
    """Unified security finding from any scanner."""

    id: str
    title: str
    description: str
    severity: SeverityLevel
    scanner: str
    rule_id: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    end_line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    remediation: Optional[str] = None
    references: List[str] = Field(default_factory=list)
    cwe_ids: List[str] = Field(default_factory=list)
    cvss_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("severity", mode="before")
    @classmethod
    def validate_severity(cls, v: Any) -> SeverityLevel:
        """Validate and convert severity."""
        if isinstance(v, SeverityLevel):
            return v
        if isinstance(v, str):
            try:
                return SeverityLevel(v.lower())
            except ValueError:
                return SeverityLevel.UNKNOWN
        return SeverityLevel.UNKNOWN

    def get_hash(self) -> str:
        """Generate unique hash for deduplication."""
        components = [
            self.rule_id,
            self.file_path or "",
            str(self.line_number or ""),
            self.title,
        ]
        hash_string = "|".join(components)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    class Config:
        """Pydantic config."""

        use_enum_values = False


class FindingSummary(BaseModel):
    """Statistical summary of findings."""

    total_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    by_severity: Dict[str, int] = Field(default_factory=dict)
    by_scanner: Dict[str, int] = Field(default_factory=dict)
    by_rule: Dict[str, int] = Field(default_factory=dict)
    unique_files_affected: int = 0

    class Config:
        """Pydantic config."""

        use_enum_values = True


class TrendData(BaseModel):
    """Trend analysis comparing scans over time."""

    previous_scan_date: Optional[datetime] = None
    current_scan_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    new_findings: int = 0
    fixed_findings: int = 0
    unchanged_findings: int = 0
    trend_direction: TrendDirection = TrendDirection.UNKNOWN
    severity_trend: Dict[str, int] = Field(default_factory=dict)
    scanner_trend: Dict[str, Dict[str, int]] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        use_enum_values = True


class AggregatedReport(BaseModel):
    """Aggregated report combining all scanner results."""

    findings: List[SecurityFinding] = Field(default_factory=list)
    summary: FindingSummary = Field(default_factory=FindingSummary)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    scan_stats: Dict[str, Any] = Field(default_factory=dict)
    trend_data: Optional[TrendData] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        """Pydantic config."""

        use_enum_values = True


class ReportGenerationError(Exception):
    """Error during report generation."""

    pass


class SARIFGenerationError(Exception):
    """Error during SARIF generation."""

    pass


class GitHubUploadError(Exception):
    """Error during GitHub SARIF upload."""

    pass


@dataclass
class ReportConfig:
    """Configuration for report generation."""

    include_code_snippets: bool = True
    include_remediation: bool = True
    max_findings_per_file: Optional[int] = None
    severity_threshold: SeverityLevel = SeverityLevel.INFO
    template_dir: Optional[Path] = None
    output_dir: Path = field(default_factory=lambda: Path("./reports"))
    github_token: Optional[str] = None
    github_api_url: str = "https://api.github.com"


class ReportAggregator:
    """
    Aggregates security findings from multiple scanners into unified reports.

    Supports SARIF generation, GitHub integration, trend analysis, and multiple
    output formats (HTML, PDF, Markdown, JSON).
    """

    DEFAULT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Scan Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1400px;
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
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .summary-card h3 {
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
        }
        .summary-card .number {
            font-size: 36px;
            font-weight: bold;
            margin: 0;
        }
        .critical { color: #dc2626; }
        .high { color: #ea580c; }
        .medium { color: #ca8a04; }
        .low { color: #16a34a; }
        .info { color: #0284c7; }
        .finding {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            border-left: 4px solid #ccc;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .finding.critical { border-left-color: #dc2626; }
        .finding.high { border-left-color: #ea580c; }
        .finding.medium { border-left-color: #ca8a04; }
        .finding.low { border-left-color: #16a34a; }
        .finding.info { border-left-color: #0284c7; }
        .finding-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }
        .finding-title {
            font-size: 18px;
            font-weight: bold;
            margin: 0;
        }
        .severity-badge {
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .severity-badge.critical {
            background-color: #fee;
            color: #dc2626;
        }
        .severity-badge.high {
            background-color: #ffedd5;
            color: #ea580c;
        }
        .severity-badge.medium {
            background-color: #fef3c7;
            color: #ca8a04;
        }
        .severity-badge.low {
            background-color: #dcfce7;
            color: #16a34a;
        }
        .severity-badge.info {
            background-color: #dbeafe;
            color: #0284c7;
        }
        .finding-meta {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
        }
        .finding-description {
            margin: 15px 0;
            line-height: 1.6;
        }
        .code-snippet {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            margin: 15px 0;
        }
        .remediation {
            background: #f0fdf4;
            border-left: 3px solid #16a34a;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .references {
            margin-top: 15px;
        }
        .references a {
            color: #0284c7;
            text-decoration: none;
            display: block;
            margin: 5px 0;
        }
        .references a:hover {
            text-decoration: underline;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Security Scan Report</h1>
        <p>Generated: {{ report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC') }}</p>
        {% if report.metadata.get('scan_target') %}
        <p>Target: {{ report.metadata['scan_target'] }}</p>
        {% endif %}
    </div>

    <div class="summary">
        <div class="summary-card">
            <h3>Total Findings</h3>
            <p class="number">{{ report.summary.total_count }}</p>
        </div>
        <div class="summary-card">
            <h3>Critical</h3>
            <p class="number critical">{{ report.summary.critical_count }}</p>
        </div>
        <div class="summary-card">
            <h3>High</h3>
            <p class="number high">{{ report.summary.high_count }}</p>
        </div>
        <div class="summary-card">
            <h3>Medium</h3>
            <p class="number medium">{{ report.summary.medium_count }}</p>
        </div>
        <div class="summary-card">
            <h3>Low</h3>
            <p class="number low">{{ report.summary.low_count }}</p>
        </div>
        <div class="summary-card">
            <h3>Info</h3>
            <p class="number info">{{ report.summary.info_count }}</p>
        </div>
    </div>

    <h2>Findings by Scanner</h2>
    <div class="summary">
        {% for scanner, count in report.summary.by_scanner.items() %}
        <div class="summary-card">
            <h3>{{ scanner }}</h3>
            <p class="number">{{ count }}</p>
        </div>
        {% endfor %}
    </div>

    <h2>Detailed Findings</h2>
    {% for finding in report.findings %}
    <div class="finding {{ finding.severity.value }}">
        <div class="finding-header">
            <h3 class="finding-title">{{ finding.title }}</h3>
            <span class="severity-badge {{ finding.severity.value }}">
                {{ finding.severity.value }}
            </span>
        </div>
        <div class="finding-meta">
            <strong>Scanner:</strong> {{ finding.scanner }} |
            <strong>Rule:</strong> {{ finding.rule_id }}
            {% if finding.file_path %}
            | <strong>File:</strong> {{ finding.file_path }}
            {% if finding.line_number %}:{{ finding.line_number }}{% endif %}
            {% endif %}
        </div>
        <div class="finding-description">
            {{ finding.description }}
        </div>
        {% if finding.code_snippet %}
        <pre class="code-snippet">{{ finding.code_snippet }}</pre>
        {% endif %}
        {% if finding.remediation %}
        <div class="remediation">
            <strong>Remediation:</strong><br>
            {{ finding.remediation }}
        </div>
        {% endif %}
        {% if finding.references %}
        <div class="references">
            <strong>References:</strong>
            {% for ref in finding.references %}
            <a href="{{ ref }}" target="_blank">{{ ref }}</a>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    {% endfor %}

    <div class="footer">
        <p>
            Generated by Infrastructure Security Scanner Platform v1.0.0
        </p>
    </div>
</body>
</html>
    """

    def __init__(self, config: Optional[ReportConfig] = None):
        """
        Initialize the Report Aggregator.

        Args:
            config: Report generation configuration
        """
        self.config = config or ReportConfig()
        self.logger = logging.getLogger(__name__)

        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        if self.config.template_dir:
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.config.template_dir)),
                autoescape=True,
            )
        else:
            self.jinja_env = Environment(autoescape=True)

    def aggregate(
        self,
        results: List[Dict[str, Any]],
        previous_report: Optional[AggregatedReport] = None,
    ) -> AggregatedReport:
        """
        Aggregate results from multiple security scanners.

        Args:
            results: List of scanner result dictionaries
            previous_report: Previous scan report for trend analysis

        Returns:
            AggregatedReport containing unified findings

        Raises:
            ReportGenerationError: If aggregation fails
        """
        try:
            self.logger.info(f"Aggregating results from {len(results)} scanners")

            all_findings: List[SecurityFinding] = []

            for result in results:
                scanner_findings = self._extract_findings(result)
                all_findings.extend(scanner_findings)

            self.logger.info(
                f"Extracted {len(all_findings)} findings before deduplication"
            )

            deduplicated_findings = self.deduplicate_findings(all_findings)

            self.logger.info(
                f"Deduplicated to {len(deduplicated_findings)} unique findings"
            )

            filtered_findings = [
                f
                for f in deduplicated_findings
                if f.severity.get_priority()
                >= self.config.severity_threshold.get_priority()
            ]

            prioritized_findings = self.prioritize_findings(filtered_findings)

            summary = self.calculate_summary(prioritized_findings)

            trend_data = None
            if previous_report:
                trend_data = self.compare_scans(
                    AggregatedReport(findings=prioritized_findings, summary=summary),
                    previous_report,
                )

            scan_stats = {
                "total_scanners": len(results),
                "total_findings_raw": len(all_findings),
                "findings_after_deduplication": len(deduplicated_findings),
                "findings_after_filtering": len(filtered_findings),
                "severity_threshold": self.config.severity_threshold.value,
            }

            report = AggregatedReport(
                findings=prioritized_findings,
                summary=summary,
                metadata={
                    "aggregator_version": "1.0.0",
                    "config": {
                        "severity_threshold": self.config.severity_threshold.value,
                        "include_code_snippets": self.config.include_code_snippets,
                    },
                },
                scan_stats=scan_stats,
                trend_data=trend_data,
            )

            self.logger.info(f"Aggregation complete: {summary.total_count} findings")
            return report

        except Exception as e:
            raise ReportGenerationError(
                f"Failed to aggregate scan results: {str(e)}"
            ) from e

    def _extract_findings(self, result: Dict[str, Any]) -> List[SecurityFinding]:
        """
        Extract findings from a single scanner result.

        Args:
            result: Scanner result dictionary

        Returns:
            List of SecurityFinding objects
        """
        findings: List[SecurityFinding] = []
        scanner = result.get("scanner", "unknown")

        raw_findings = result.get("findings", [])
        if isinstance(raw_findings, dict):
            raw_findings = [raw_findings]

        for item in raw_findings:
            try:
                finding = SecurityFinding(
                    id=item.get("id", self._generate_finding_id(item)),
                    title=item.get("title", item.get("name", "Untitled Finding")),
                    description=item.get(
                        "description", item.get("message", "No description")
                    ),
                    severity=self._normalize_severity(item.get("severity")),
                    scanner=scanner,
                    rule_id=item.get("rule_id", item.get("check_id", "unknown")),
                    file_path=item.get("file_path", item.get("file")),
                    line_number=item.get("line_number", item.get("line")),
                    end_line_number=item.get("end_line_number"),
                    code_snippet=(
                        item.get("code_snippet")
                        if self.config.include_code_snippets
                        else None
                    ),
                    remediation=(
                        item.get("remediation")
                        if self.config.include_remediation
                        else None
                    ),
                    references=item.get("references", []),
                    cwe_ids=item.get("cwe_ids", []),
                    cvss_score=item.get("cvss_score"),
                    metadata=item.get("metadata", {}),
                )
                findings.append(finding)
            except Exception as e:
                self.logger.warning(f"Failed to parse finding: {e}, item: {item}")
                continue

        return findings

    def _generate_finding_id(self, item: Dict[str, Any]) -> str:
        """Generate unique ID for a finding."""
        components = [
            str(item.get("rule_id", "")),
            str(item.get("file_path", "")),
            str(item.get("line_number", "")),
        ]
        hash_str = "|".join(components)
        return hashlib.sha256(hash_str.encode()).hexdigest()[:16]

    def _normalize_severity(self, severity: Any) -> SeverityLevel:
        """Normalize severity from various scanner formats."""
        if isinstance(severity, SeverityLevel):
            return severity

        if severity is None:
            return SeverityLevel.UNKNOWN

        severity_str = str(severity).lower().strip()

        severity_mapping = {
            "critical": SeverityLevel.CRITICAL,
            "crit": SeverityLevel.CRITICAL,
            "high": SeverityLevel.HIGH,
            "medium": SeverityLevel.MEDIUM,
            "med": SeverityLevel.MEDIUM,
            "moderate": SeverityLevel.MEDIUM,
            "low": SeverityLevel.LOW,
            "info": SeverityLevel.INFO,
            "informational": SeverityLevel.INFO,
            "note": SeverityLevel.INFO,
            "warning": SeverityLevel.MEDIUM,
            "error": SeverityLevel.HIGH,
        }

        return severity_mapping.get(severity_str, SeverityLevel.UNKNOWN)

    def deduplicate_findings(
        self, findings: List[SecurityFinding]
    ) -> List[SecurityFinding]:
        """
        Remove duplicate findings based on hash.

        Args:
            findings: List of findings to deduplicate

        Returns:
            List of unique findings
        """
        seen_hashes: Set[str] = set()
        unique_findings: List[SecurityFinding] = []

        for finding in findings:
            finding_hash = finding.get_hash()
            if finding_hash not in seen_hashes:
                seen_hashes.add(finding_hash)
                unique_findings.append(finding)
            else:
                self.logger.debug(
                    f"Duplicate finding filtered: {finding.title} "
                    f"in {finding.file_path}"
                )

        return unique_findings

    def prioritize_findings(
        self, findings: List[SecurityFinding]
    ) -> List[SecurityFinding]:
        """
        Sort findings by severity and other criteria.

        Args:
            findings: List of findings to prioritize

        Returns:
            Sorted list of findings
        """
        return sorted(
            findings,
            key=lambda f: (
                -f.severity.get_priority(),
                f.cvss_score or 0.0,
                f.file_path or "",
                f.line_number or 0,
            ),
            reverse=False,
        )

    def calculate_summary(self, findings: List[SecurityFinding]) -> FindingSummary:
        """
        Calculate statistics for findings.

        Args:
            findings: List of findings

        Returns:
            FindingSummary with statistics
        """
        summary = FindingSummary()
        summary.total_count = len(findings)

        by_severity: Dict[str, int] = {}
        by_scanner: Dict[str, int] = {}
        by_rule: Dict[str, int] = {}
        unique_files: Set[str] = set()

        for finding in findings:
            severity = finding.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

            by_scanner[finding.scanner] = by_scanner.get(finding.scanner, 0) + 1

            by_rule[finding.rule_id] = by_rule.get(finding.rule_id, 0) + 1

            if finding.file_path:
                unique_files.add(finding.file_path)

        summary.critical_count = by_severity.get(SeverityLevel.CRITICAL.value, 0)
        summary.high_count = by_severity.get(SeverityLevel.HIGH.value, 0)
        summary.medium_count = by_severity.get(SeverityLevel.MEDIUM.value, 0)
        summary.low_count = by_severity.get(SeverityLevel.LOW.value, 0)
        summary.info_count = by_severity.get(SeverityLevel.INFO.value, 0)
        summary.by_severity = by_severity
        summary.by_scanner = by_scanner
        summary.by_rule = by_rule
        summary.unique_files_affected = len(unique_files)

        return summary

    def compare_scans(
        self, current: AggregatedReport, previous: AggregatedReport
    ) -> TrendData:
        """
        Compare current scan with previous scan for trend analysis.

        Args:
            current: Current scan report
            previous: Previous scan report

        Returns:
            TrendData with comparison results
        """
        current_hashes = {f.get_hash() for f in current.findings}
        previous_hashes = {f.get_hash() for f in previous.findings}

        new_findings_hashes = current_hashes - previous_hashes
        fixed_findings_hashes = previous_hashes - current_hashes
        unchanged_findings_hashes = current_hashes & previous_hashes

        new_count = len(new_findings_hashes)
        fixed_count = len(fixed_findings_hashes)
        unchanged_count = len(unchanged_findings_hashes)

        if new_count > fixed_count:
            direction = TrendDirection.WORSENING
        elif fixed_count > new_count:
            direction = TrendDirection.IMPROVING
        elif new_count == 0 and fixed_count == 0:
            direction = TrendDirection.STABLE
        else:
            direction = TrendDirection.STABLE

        severity_trend: Dict[str, int] = {}
        for severity in SeverityLevel:
            current_count = getattr(current.summary, f"{severity.value}_count", 0)
            previous_count = getattr(previous.summary, f"{severity.value}_count", 0)
            severity_trend[severity.value] = current_count - previous_count

        scanner_trend: Dict[str, Dict[str, int]] = {}
        all_scanners = set(current.summary.by_scanner.keys()) | set(
            previous.summary.by_scanner.keys()
        )
        for scanner in all_scanners:
            current_count = current.summary.by_scanner.get(scanner, 0)
            previous_count = previous.summary.by_scanner.get(scanner, 0)
            scanner_trend[scanner] = {
                "current": current_count,
                "previous": previous_count,
                "delta": current_count - previous_count,
            }

        return TrendData(
            previous_scan_date=previous.generated_at,
            current_scan_date=current.generated_at,
            new_findings=new_count,
            fixed_findings=fixed_count,
            unchanged_findings=unchanged_count,
            trend_direction=direction,
            severity_trend=severity_trend,
            scanner_trend=scanner_trend,
        )

    def generate_sarif(
        self, findings: List[SecurityFinding], tool_name: str = "infrastructure-scanner"
    ) -> SARIFReport:
        """
        Generate SARIF 2.1.0 format report.

        Args:
            findings: List of security findings
            tool_name: Name of the tool for SARIF metadata

        Returns:
            SARIFReport object

        Raises:
            SARIFGenerationError: If SARIF generation fails
        """
        try:
            self.logger.info(f"Generating SARIF report for {len(findings)} findings")

            rules = self._generate_sarif_rules(findings)

            tool = SARIFTool(
                driver={
                    "name": tool_name,
                    "version": "1.0.0",
                    "informationUri": "https://github.com/devCrew_s1/infrastructure",
                    "rules": rules,
                }
            )

            results = [self._convert_to_sarif_result(f) for f in findings]

            invocation = SARIFInvocation(
                executionSuccessful=True,
                endTimeUtc=datetime.now(timezone.utc).isoformat(),
            )

            run = SARIFRun(
                tool=tool,
                results=results,
                invocations=[invocation],
            )

            sarif_report = SARIFReport(runs=[run])

            self.logger.info("SARIF report generated successfully")
            return sarif_report

        except Exception as e:
            raise SARIFGenerationError(
                f"Failed to generate SARIF report: {str(e)}"
            ) from e

    def _generate_sarif_rules(
        self, findings: List[SecurityFinding]
    ) -> List[Dict[str, Any]]:
        """Generate SARIF rules from findings."""
        rules_map: Dict[str, Dict[str, Any]] = {}

        for finding in findings:
            if finding.rule_id not in rules_map:
                rules_map[finding.rule_id] = {
                    "id": finding.rule_id,
                    "name": finding.title,
                    "shortDescription": {"text": finding.title},
                    "fullDescription": {"text": finding.description},
                    "help": {
                        "text": finding.remediation or "No remediation available",
                        "markdown": finding.remediation or "No remediation available",
                    },
                    "defaultConfiguration": {
                        "level": finding.severity.to_sarif_level()
                    },
                    "properties": {
                        "tags": ["security", finding.scanner],
                        "security-severity": str(
                            finding.cvss_score or finding.severity.get_priority()
                        ),
                    },
                }

        return list(rules_map.values())

    def _convert_to_sarif_result(self, finding: SecurityFinding) -> SARIFResult:
        """
        Convert a SecurityFinding to SARIF result format.

        Args:
            finding: Security finding to convert

        Returns:
            SARIFResult object
        """
        message = SARIFMessage(
            text=finding.description,
            markdown=f"**{finding.title}**\n\n{finding.description}",
        )

        locations: List[Dict[str, Any]] = []
        if finding.file_path:
            region: Dict[str, Any] = {}

            if finding.line_number:
                region["startLine"] = finding.line_number
                if finding.end_line_number:
                    region["endLine"] = finding.end_line_number

            if finding.code_snippet:
                region["snippet"] = {"text": finding.code_snippet}

            location: Dict[str, Any] = {
                "physicalLocation": {
                    "artifactLocation": {"uri": finding.file_path},
                    "region": region,
                }
            }

            locations.append(location)

        properties: Dict[str, Any] = {
            "scanner": finding.scanner,
            "severity": finding.severity.value,
        }
        if finding.cwe_ids:
            properties["cwe_ids"] = finding.cwe_ids
        if finding.cvss_score:
            properties["cvss_score"] = finding.cvss_score
        if finding.references:
            properties["references"] = finding.references

        return SARIFResult(
            ruleId=finding.rule_id,
            message=message,
            level=finding.severity.to_sarif_level(),
            locations=locations,
            properties=properties,
        )

    def generate_html(
        self, report: AggregatedReport, template_name: Optional[str] = None
    ) -> str:
        """
        Generate HTML report.

        Args:
            report: Aggregated report
            template_name: Optional custom template name

        Returns:
            HTML string

        Raises:
            ReportGenerationError: If HTML generation fails
        """
        try:
            self.logger.info("Generating HTML report")

            if template_name and self.config.template_dir:
                template = self.jinja_env.get_template(template_name)
            else:
                template = Template(self.DEFAULT_HTML_TEMPLATE)

            html_content = template.render(report=report)

            self.logger.info("HTML report generated successfully")
            return html_content

        except Exception as e:
            raise ReportGenerationError(
                f"Failed to generate HTML report: {str(e)}"
            ) from e

    def generate_json(self, report: AggregatedReport) -> str:
        """
        Generate JSON report.

        Args:
            report: Aggregated report

        Returns:
            JSON string

        Raises:
            ReportGenerationError: If JSON generation fails
        """
        try:
            self.logger.info("Generating JSON report")

            report_dict = json.loads(report.model_dump_json())

            json_content = json.dumps(report_dict, indent=2, default=str)

            self.logger.info("JSON report generated successfully")
            return json_content

        except Exception as e:
            raise ReportGenerationError(
                f"Failed to generate JSON report: {str(e)}"
            ) from e

    def generate_markdown(self, report: AggregatedReport) -> str:
        """
        Generate Markdown summary report.

        Args:
            report: Aggregated report

        Returns:
            Markdown string

        Raises:
            ReportGenerationError: If Markdown generation fails
        """
        try:
            self.logger.info("Generating Markdown report")

            lines = [
                "# Security Scan Report",
                "",
                (
                    f"**Generated:** "
                    f"{report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                ),
                "",
                "## Summary",
                "",
                f"- **Total Findings:** {report.summary.total_count}",
                f"- **Critical:** {report.summary.critical_count}",
                f"- **High:** {report.summary.high_count}",
                f"- **Medium:** {report.summary.medium_count}",
                f"- **Low:** {report.summary.low_count}",
                f"- **Info:** {report.summary.info_count}",
                f"- **Files Affected:** {report.summary.unique_files_affected}",
                "",
            ]

            if report.trend_data:
                lines.extend(
                    [
                        "## Trend Analysis",
                        "",
                        (
                            f"- **Direction:** "
                            f"{report.trend_data.trend_direction.value.title()}"
                        ),
                        f"- **New Findings:** {report.trend_data.new_findings}",
                        f"- **Fixed Findings:** {report.trend_data.fixed_findings}",
                        f"- **Unchanged:** {report.trend_data.unchanged_findings}",
                        "",
                    ]
                )

            lines.extend(["## Findings by Scanner", ""])
            for scanner, count in sorted(
                report.summary.by_scanner.items(), key=lambda x: x[1], reverse=True
            ):
                lines.append(f"- **{scanner}:** {count}")

            lines.extend(["", "## Findings by Severity", ""])
            for severity, count in sorted(
                report.summary.by_severity.items(),
                key=lambda x: SeverityLevel(x[0]).get_priority(),
                reverse=True,
            ):
                lines.append(f"- **{severity.title()}:** {count}")

            lines.extend(["", "## Top Findings", ""])

            top_findings = report.findings[: min(20, len(report.findings))]
            for i, finding in enumerate(top_findings, 1):
                lines.extend(
                    [
                        f"### {i}. {finding.title}",
                        "",
                        f"**Severity:** {finding.severity.value.upper()}  ",
                        f"**Scanner:** {finding.scanner}  ",
                        f"**Rule ID:** {finding.rule_id}  ",
                    ]
                )

                if finding.file_path:
                    location = finding.file_path
                    if finding.line_number:
                        location += f":{finding.line_number}"
                    lines.append(f"**Location:** `{location}`  ")

                lines.extend(["", finding.description, ""])

                if finding.remediation:
                    lines.extend(
                        [
                            "**Remediation:**",
                            "",
                            finding.remediation,
                            "",
                        ]
                    )

                if finding.references:
                    lines.append("**References:**")
                    for ref in finding.references:
                        lines.append(f"- {ref}")
                    lines.append("")

                lines.append("---")
                lines.append("")

            markdown_content = "\n".join(lines)

            self.logger.info("Markdown report generated successfully")
            return markdown_content

        except Exception as e:
            raise ReportGenerationError(
                f"Failed to generate Markdown report: {str(e)}"
            ) from e

    def upload_to_github(
        self, sarif: SARIFReport, repo: str, ref: str, commit_sha: str
    ) -> bool:
        """
        Upload SARIF report to GitHub Code Scanning.

        Args:
            sarif: SARIF report to upload
            repo: Repository in format 'owner/repo'
            ref: Git reference (branch/tag)
            commit_sha: Commit SHA for the scan

        Returns:
            True if upload successful

        Raises:
            GitHubUploadError: If upload fails
        """
        try:
            self.logger.info(f"Uploading SARIF to GitHub for {repo}@{ref}")

            if not self.config.github_token:
                raise GitHubUploadError("GitHub token not configured")

            sarif_json = sarif.model_dump_json(by_alias=True)

            url = f"{self.config.github_api_url}/repos/{repo}/" f"code-scanning/sarifs"

            headers = {
                "Authorization": f"token {self.config.github_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
            }

            payload = {
                "commit_sha": commit_sha,
                "ref": ref,
                "sarif": sarif_json,
                "tool_name": "infrastructure-security-scanner",
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code == 202:
                self.logger.info(
                    f"SARIF uploaded successfully: {response.json().get('id')}"
                )
                return True
            else:
                raise GitHubUploadError(
                    f"GitHub API returned {response.status_code}: " f"{response.text}"
                )

        except requests.exceptions.RequestException as e:
            raise GitHubUploadError(
                f"Failed to upload SARIF to GitHub: {str(e)}"
            ) from e

    def save_report(
        self,
        report: AggregatedReport,
        format_type: ReportFormat,
        filename: Optional[str] = None,
    ) -> Path:
        """
        Save report to file in specified format.

        Args:
            report: Report to save
            format_type: Output format
            filename: Optional custom filename

        Returns:
            Path to saved report file

        Raises:
            ReportGenerationError: If save fails
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"security_report_{timestamp}.{format_type.value}"

            output_path = self.config.output_dir / filename

            if format_type == ReportFormat.SARIF:
                sarif = self.generate_sarif(report.findings)
                content = sarif.model_dump_json(by_alias=True, indent=2)
            elif format_type == ReportFormat.JSON:
                content = self.generate_json(report)
            elif format_type == ReportFormat.HTML:
                content = self.generate_html(report)
            elif format_type == ReportFormat.MARKDOWN:
                content = self.generate_markdown(report)
            elif format_type == ReportFormat.PDF:
                raise NotImplementedError("PDF generation requires additional setup")
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            output_path.write_text(content, encoding="utf-8")

            self.logger.info(f"Report saved to {output_path}")
            return output_path

        except Exception as e:
            raise ReportGenerationError(f"Failed to save report: {str(e)}") from e


def main() -> None:
    """Run example usage of ReportAggregator."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    config = ReportConfig(
        output_dir=Path("./security_reports"),
        severity_threshold=SeverityLevel.LOW,
    )

    aggregator = ReportAggregator(config)

    example_results = [
        {
            "scanner": "trivy",
            "findings": [
                {
                    "id": "CVE-2023-1234",
                    "title": "SQL Injection Vulnerability",
                    "description": "SQL injection found in login endpoint",
                    "severity": "high",
                    "rule_id": "TRIVY-SQL-001",
                    "file_path": "app/auth.py",
                    "line_number": 42,
                    "remediation": "Use parameterized queries",
                    "references": ["https://cve.mitre.org/CVE-2023-1234"],
                    "cvss_score": 8.5,
                }
            ],
        },
        {
            "scanner": "checkov",
            "findings": [
                {
                    "title": "S3 Bucket Not Encrypted",
                    "description": "S3 bucket lacks encryption at rest",
                    "severity": "medium",
                    "rule_id": "CKV_AWS_19",
                    "file_path": "terraform/s3.tf",
                    "line_number": 15,
                    "remediation": "Enable S3 bucket encryption",
                }
            ],
        },
    ]

    report = aggregator.aggregate(example_results)

    aggregator.save_report(report, ReportFormat.HTML)
    aggregator.save_report(report, ReportFormat.JSON)
    aggregator.save_report(report, ReportFormat.MARKDOWN)
    aggregator.save_report(report, ReportFormat.SARIF)

    print(f"Generated reports in {config.output_dir}")
    print(f"Total findings: {report.summary.total_count}")
    print(f"Critical: {report.summary.critical_count}")
    print(f"High: {report.summary.high_count}")


if __name__ == "__main__":
    main()
