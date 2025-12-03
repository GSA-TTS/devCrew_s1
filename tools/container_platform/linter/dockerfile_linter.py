"""
Dockerfile Linter with hadolint integration and custom rule validation.

Provides comprehensive Dockerfile validation including:
- hadolint integration for best practices
- Custom organizational rules
- Security anti-pattern detection
- Build optimization suggestions
- Multi-stage build validation
- OCI annotation compliance
"""

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class LintSeverity(Enum):
    """Severity levels for lint findings."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    STYLE = "style"


class RuleCategory(Enum):
    """Categories for lint rules."""

    BEST_PRACTICE = "best_practice"
    SECURITY = "security"
    OPTIMIZATION = "optimization"
    MAINTAINABILITY = "maintainability"
    COMPLIANCE = "compliance"


@dataclass
class LintRule:
    """Represents a linting rule."""

    rule_id: str
    description: str
    severity: LintSeverity
    category: RuleCategory
    fix_suggestion: Optional[str] = None
    documentation_url: Optional[str] = None


@dataclass
class LintFinding:
    """Represents a linting finding."""

    rule_id: str
    description: str
    severity: LintSeverity
    category: RuleCategory
    line_number: Optional[int] = None
    line_content: Optional[str] = None
    fix_suggestion: Optional[str] = None
    documentation_url: Optional[str] = None
    source: str = "custom"  # 'hadolint' or 'custom'

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            "rule_id": self.rule_id,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category.value,
            "line_number": self.line_number,
            "line_content": self.line_content,
            "fix_suggestion": self.fix_suggestion,
            "documentation_url": self.documentation_url,
            "source": self.source,
        }

    def to_sarif(self) -> Dict[str, Any]:
        """Convert to SARIF result format."""
        result: Dict[str, Any] = {
            "ruleId": self.rule_id,
            "level": self._severity_to_sarif_level(),
            "message": {"text": self.description},
        }

        if self.line_number:
            result["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": "Dockerfile"},
                        "region": {
                            "startLine": self.line_number,
                            "snippet": {"text": self.line_content or ""},
                        },
                    }
                }
            ]

        if self.fix_suggestion:
            result["fixes"] = [{"description": {"text": self.fix_suggestion}}]

        return result

    def _severity_to_sarif_level(self) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            LintSeverity.ERROR: "error",
            LintSeverity.WARNING: "warning",
            LintSeverity.INFO: "note",
            LintSeverity.STYLE: "note",
        }
        return mapping.get(self.severity, "warning")


@dataclass
class LintResult:
    """Results from Dockerfile linting."""

    dockerfile_path: str
    findings: List[LintFinding] = field(default_factory=list)
    total_lines: int = 0
    stages: List[str] = field(default_factory=list)
    base_images: List[str] = field(default_factory=list)
    has_healthcheck: bool = False
    has_user: bool = False
    has_labels: bool = False
    hadolint_available: bool = False
    scan_duration: float = 0.0

    @property
    def error_count(self) -> int:
        """Count of error-level findings."""
        return sum(1 for f in self.findings if f.severity == LintSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-level findings."""
        return sum(1 for f in self.findings if f.severity == LintSeverity.WARNING)

    @property
    def info_count(self) -> int:
        """Count of info-level findings."""
        return sum(1 for f in self.findings if f.severity == LintSeverity.INFO)

    @property
    def style_count(self) -> int:
        """Count of style-level findings."""
        return sum(1 for f in self.findings if f.severity == LintSeverity.STYLE)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "dockerfile_path": self.dockerfile_path,
            "summary": {
                "total_findings": len(self.findings),
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
                "style": self.style_count,
                "total_lines": self.total_lines,
                "stages": len(self.stages),
                "has_healthcheck": self.has_healthcheck,
                "has_user": self.has_user,
                "has_labels": self.has_labels,
                "hadolint_available": self.hadolint_available,
                "scan_duration": self.scan_duration,
            },
            "findings": [f.to_dict() for f in self.findings],
            "stages": self.stages,
            "base_images": self.base_images,
        }


class DockerfileLinter:
    """
    Comprehensive Dockerfile linter with hadolint integration.

    Features:
    - hadolint integration for industry best practices
    - Custom organizational rules
    - Security anti-pattern detection
    - Build optimization suggestions
    - Multi-stage build validation
    - OCI annotation compliance
    - Auto-fix suggestions
    """

    # Hardcoded secrets patterns
    SECRET_PATTERNS = [
        (
            r"(?i)(password|passwd|pwd)\s*=\s*['\"][\w!@#$%^&*()]+['\"]",
            "Hardcoded password",
        ),
        (
            r"(?i)(api[_-]?key|apikey)\s*=\s*['\"][\w-]+['\"]",
            "Hardcoded API key",
        ),
        (
            r"(?i)(secret|token)\s*=\s*['\"][\w-]+['\"]",
            "Hardcoded secret/token",
        ),
        (
            r"(?i)(aws|amazon).*(?:key|secret|token)",
            "AWS credentials",
        ),
        (r"(?i)private[_-]?key", "Private key reference"),
    ]

    # Known vulnerable base images
    VULNERABLE_IMAGES = {
        "ubuntu:latest": "Use specific version tags",
        "debian:latest": "Use specific version tags",
        "alpine:latest": "Use specific version tags",
        "node:latest": "Use specific version tags",
        "python:latest": "Use specific version tags",
    }

    # Required OCI labels for compliance
    REQUIRED_OCI_LABELS = {
        "org.opencontainers.image.title",
        "org.opencontainers.image.version",
        "org.opencontainers.image.created",
        "org.opencontainers.image.description",
        "org.opencontainers.image.authors",
    }

    def __init__(
        self,
        hadolint_path: Optional[str] = None,
        custom_rules: Optional[List[LintRule]] = None,
        strict_mode: bool = False,
    ):
        """
        Initialize Dockerfile linter.

        Args:
            hadolint_path: Path to hadolint binary (auto-detected)
            custom_rules: Additional custom rules to apply
            strict_mode: Enable strict validation (warnings become errors)
        """
        self.hadolint_path = hadolint_path or self._find_hadolint()
        self.custom_rules = custom_rules or []
        self.strict_mode = strict_mode
        self.hadolint_available = self.hadolint_path is not None

    def _find_hadolint(self) -> Optional[str]:
        """Find hadolint binary in PATH."""
        return shutil.which("hadolint")

    def lint_file(self, dockerfile_path: str) -> LintResult:
        """
        Lint a Dockerfile.

        Args:
            dockerfile_path: Path to Dockerfile

        Returns:
            LintResult with findings and metadata

        Raises:
            FileNotFoundError: If Dockerfile does not exist
        """
        import time

        start_time = time.time()

        path = Path(dockerfile_path)
        if not path.exists():
            raise FileNotFoundError(f"Dockerfile not found: {dockerfile_path}")

        result = LintResult(
            dockerfile_path=str(path.absolute()),
            hadolint_available=self.hadolint_available,
        )

        # Read Dockerfile content
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        result.total_lines = len(lines)

        # Extract metadata
        result.stages = self._extract_stages(content)
        result.base_images = self._extract_base_images(content)
        result.has_healthcheck = "HEALTHCHECK" in content
        user_pattern = r"^USER\s+\w+"
        result.has_user = bool(re.search(user_pattern, content, re.MULTILINE))
        result.has_labels = "LABEL" in content

        # Run hadolint if available
        if self.hadolint_available:
            hadolint_findings = self._run_hadolint(dockerfile_path)
            result.findings.extend(hadolint_findings)

        # Run custom checks
        custom_findings = self._run_custom_checks(content, lines)
        result.findings.extend(custom_findings)

        # Apply strict mode
        if self.strict_mode:
            for finding in result.findings:
                if finding.severity == LintSeverity.WARNING:
                    finding.severity = LintSeverity.ERROR

        # Sort findings by severity and line number
        result.findings.sort(
            key=lambda f: (
                self._severity_order(f.severity),
                f.line_number or 0,
            )
        )

        result.scan_duration = time.time() - start_time
        return result

    def _run_hadolint(self, dockerfile_path: str) -> List[LintFinding]:
        """Run hadolint and parse results."""
        if not self.hadolint_path:
            return []

        try:
            result = subprocess.run(
                [self.hadolint_path, "--format", "json", dockerfile_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # hadolint returns non-zero on findings, which is expected
            if result.stdout:
                return self._parse_hadolint_output(result.stdout)

            return []

        except subprocess.TimeoutExpired:
            return [
                LintFinding(
                    rule_id="LINT-TIMEOUT",
                    description="hadolint execution timed out",
                    severity=LintSeverity.WARNING,
                    category=RuleCategory.BEST_PRACTICE,
                    source="hadolint",
                )
            ]
        except Exception as e:
            return [
                LintFinding(
                    rule_id="LINT-ERROR",
                    description=f"hadolint execution failed: {str(e)}",
                    severity=LintSeverity.WARNING,
                    category=RuleCategory.BEST_PRACTICE,
                    source="hadolint",
                )
            ]

    def _parse_hadolint_output(self, output: str) -> List[LintFinding]:
        """Parse hadolint JSON output."""
        findings = []

        try:
            data = json.loads(output)
            for item in data:
                level = item.get("level", "info")
                severity = self._map_hadolint_severity(level)
                code = item.get("code", "")
                category = self._map_hadolint_category(code)

                # hadolint may include column
                finding = LintFinding(
                    rule_id=item.get("code", "DL-UNKNOWN"),
                    description=item.get("message", "Unknown issue"),
                    severity=severity,
                    category=category,
                    line_number=item.get("line"),
                    line_content=item.get("column"),
                    source="hadolint",
                )
                findings.append(finding)

        except json.JSONDecodeError:
            findings.append(
                LintFinding(
                    rule_id="LINT-PARSE-ERROR",
                    description="Failed to parse hadolint output",
                    severity=LintSeverity.WARNING,
                    category=RuleCategory.BEST_PRACTICE,
                    source="hadolint",
                )
            )

        return findings

    def _map_hadolint_severity(self, level: str) -> LintSeverity:
        """Map hadolint severity to LintSeverity."""
        mapping = {
            "error": LintSeverity.ERROR,
            "warning": LintSeverity.WARNING,
            "info": LintSeverity.INFO,
            "style": LintSeverity.STYLE,
        }
        return mapping.get(level.lower(), LintSeverity.INFO)

    def _map_hadolint_category(self, code: str) -> RuleCategory:
        """Map hadolint rule code to category."""
        # DL3xxx = Dockerfile best practices
        # DL4xxx = Security
        # DL6xxx = Build optimization
        if code.startswith("DL4"):
            return RuleCategory.SECURITY
        if code.startswith("DL6"):
            return RuleCategory.OPTIMIZATION
        return RuleCategory.BEST_PRACTICE

    def _run_custom_checks(self, content: str, lines: List[str]) -> List[LintFinding]:
        """Run custom organizational checks."""
        findings = []

        # Security checks
        findings.extend(self._check_root_user(content, lines))
        findings.extend(self._check_hardcoded_secrets(content, lines))
        findings.extend(self._check_vulnerable_images(content, lines))

        # Build optimization checks
        findings.extend(self._check_layer_optimization(content, lines))
        findings.extend(self._check_cache_optimization(content, lines))

        # Compliance checks
        findings.extend(self._check_oci_labels(content, lines))
        findings.extend(self._check_healthcheck(content, lines))

        # Best practice checks
        findings.extend(self._check_multistage_usage(content, lines))
        findings.extend(self._check_workdir_usage(content, lines))

        return findings

    def _check_root_user(self, content: str, lines: List[str]) -> List[LintFinding]:
        """Check for running as root user."""
        findings = []

        user_match = re.search(r"^USER\s+(.+)$", content, re.MULTILINE)

        if not user_match:
            findings.append(
                LintFinding(
                    rule_id="CUSTOM-SEC-001",
                    description=("No USER instruction found - container runs as root"),
                    severity=LintSeverity.ERROR,
                    category=RuleCategory.SECURITY,
                    fix_suggestion="Add USER before CMD/ENTRYPOINT",
                )
            )
        elif user_match.group(1).strip() in ["root", "0"]:
            line_num = content[: user_match.start()].count("\n") + 1
            findings.append(
                LintFinding(
                    rule_id="CUSTOM-SEC-002",
                    description="Explicitly running as root user",
                    severity=LintSeverity.ERROR,
                    category=RuleCategory.SECURITY,
                    line_number=line_num,
                    line_content=(
                        lines[line_num - 1] if line_num <= len(lines) else None
                    ),
                    fix_suggestion="Use a non-root user for security",
                )
            )

        return findings

    def _check_hardcoded_secrets(
        self, content: str, lines: List[str]
    ) -> List[LintFinding]:
        """Check for hardcoded secrets."""
        findings = []

        for pattern, description in self.SECRET_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[: match.start()].count("\n") + 1
                findings.append(
                    LintFinding(
                        rule_id="CUSTOM-SEC-003",
                        description=(f"Potential {description.lower()} detected"),
                        severity=LintSeverity.ERROR,
                        category=RuleCategory.SECURITY,
                        line_number=line_num,
                        line_content=(
                            lines[line_num - 1] if line_num <= len(lines) else None
                        ),
                        fix_suggestion=("Use build args or environment variables"),
                    )
                )

        return findings

    def _check_vulnerable_images(
        self, content: str, lines: List[str]
    ) -> List[LintFinding]:
        """Check for vulnerable or latest-tagged base images."""
        findings = []

        for image, suggestion in self.VULNERABLE_IMAGES.items():
            pattern = rf"FROM\s+{re.escape(image)}"
            for match in re.finditer(pattern, content, re.IGNORECASE):
                line_num = content[: match.start()].count("\n") + 1
                findings.append(
                    LintFinding(
                        rule_id="CUSTOM-SEC-004",
                        description=(f"Using '{image}' - not pinned to version"),
                        severity=LintSeverity.WARNING,
                        category=RuleCategory.SECURITY,
                        line_number=line_num,
                        line_content=(
                            lines[line_num - 1] if line_num <= len(lines) else None
                        ),
                        fix_suggestion=suggestion,
                    )
                )

        return findings

    def _check_layer_optimization(
        self, content: str, lines: List[str]
    ) -> List[LintFinding]:
        """Check for layer optimization opportunities."""
        findings = []

        # Check for multiple RUN commands that could be combined
        run_commands = list(re.finditer(r"^RUN\s+", content, re.MULTILINE))
        if len(run_commands) > 5:
            findings.append(
                LintFinding(
                    rule_id="CUSTOM-OPT-001",
                    description=(
                        f"Found {len(run_commands)} RUN commands - "
                        "consider combining"
                    ),
                    severity=LintSeverity.INFO,
                    category=RuleCategory.OPTIMIZATION,
                    fix_suggestion=(
                        "Combine related RUN commands with && to reduce " "layers"
                    ),
                )
            )

        # Check for apt-get without --no-install-recommends
        apt_pattern = r"apt-get\s+install(?!\s+--no-install-recommends)"
        for match in re.finditer(apt_pattern, content):
            line_num = content[: match.start()].count("\n") + 1
            findings.append(
                LintFinding(
                    rule_id="CUSTOM-OPT-002",
                    description=("apt-get install without --no-install-recommends"),
                    severity=LintSeverity.WARNING,
                    category=RuleCategory.OPTIMIZATION,
                    line_number=line_num,
                    line_content=(
                        lines[line_num - 1] if line_num <= len(lines) else None
                    ),
                    fix_suggestion=("Add --no-install-recommends to reduce image size"),
                )
            )

        return findings

    def _check_cache_optimization(
        self, content: str, lines: List[str]
    ) -> List[LintFinding]:
        """Check for build cache optimization."""
        findings = []

        # Check COPY ordering for package files
        package_files = [
            "package.json",
            "requirements.txt",
            "Gemfile",
            "go.mod",
        ]
        for pkg_file in package_files:
            if pkg_file in content:
                # Check if package file is copied before all files
                copy_all_pattern = r"COPY\s+\.\s+\."
                copy_pkg_pattern = rf"COPY\s+.*{re.escape(pkg_file)}"

                copy_all_matches = list(re.finditer(copy_all_pattern, content))
                copy_pkg_matches = list(re.finditer(copy_pkg_pattern, content))

                if copy_all_matches and copy_pkg_matches:
                    first_copy_all = copy_all_matches[0].start()
                    first_copy_pkg = copy_pkg_matches[0].start()

                    if first_copy_all < first_copy_pkg:
                        line_num = content[:first_copy_all].count("\n") + 1
                        findings.append(
                            LintFinding(
                                rule_id="CUSTOM-OPT-003",
                                description=(
                                    f"Copy {pkg_file} before other files "
                                    "for better caching"
                                ),
                                severity=LintSeverity.INFO,
                                category=RuleCategory.OPTIMIZATION,
                                line_number=line_num,
                                fix_suggestion=(
                                    f"COPY {pkg_file} before COPY . . to "
                                    "leverage build cache"
                                ),
                            )
                        )

        return findings

    def _check_oci_labels(self, content: str, lines: List[str]) -> List[LintFinding]:
        """Check for required OCI labels."""
        findings = []

        # Extract all labels
        labels = set()
        for match in re.finditer(r"LABEL\s+([\w.]+)=", content):
            labels.add(match.group(1))

        # Check for missing required labels
        missing_labels = self.REQUIRED_OCI_LABELS - labels
        if missing_labels:
            missing_str = ", ".join(sorted(missing_labels))
            findings.append(
                LintFinding(
                    rule_id="CUSTOM-COMP-001",
                    description=f"Missing required OCI labels: {missing_str}",
                    severity=LintSeverity.WARNING,
                    category=RuleCategory.COMPLIANCE,
                    fix_suggestion=(
                        "Add OCI-compliant labels for better image metadata"
                    ),
                    documentation_url=(
                        "https://github.com/opencontainers/"
                        "image-spec/blob/main/annotations.md"
                    ),
                )
            )

        return findings

    def _check_healthcheck(self, content: str, lines: List[str]) -> List[LintFinding]:
        """Check for HEALTHCHECK instruction."""
        findings = []

        if "HEALTHCHECK" not in content:
            findings.append(
                LintFinding(
                    rule_id="CUSTOM-BEST-001",
                    description="No HEALTHCHECK instruction defined",
                    severity=LintSeverity.INFO,
                    category=RuleCategory.BEST_PRACTICE,
                    fix_suggestion=(
                        "Add HEALTHCHECK to enable container health monitoring"
                    ),
                )
            )

        return findings

    def _check_multistage_usage(
        self, content: str, lines: List[str]
    ) -> List[LintFinding]:
        """Check multi-stage build usage."""
        findings = []

        from_statements = re.findall(r"^FROM\s+", content, re.MULTILINE)

        # If only one FROM and file is large, suggest multi-stage
        if len(from_statements) == 1 and len(lines) > 30:
            findings.append(
                LintFinding(
                    rule_id="CUSTOM-OPT-004",
                    description=("Consider multi-stage builds to reduce image size"),
                    severity=LintSeverity.INFO,
                    category=RuleCategory.OPTIMIZATION,
                    fix_suggestion=(
                        "Use builder stage for compilation, " "final stage for runtime"
                    ),
                )
            )

        return findings

    def _check_workdir_usage(self, content: str, lines: List[str]) -> List[LintFinding]:
        """Check WORKDIR usage."""
        findings = []

        if "WORKDIR" not in content:
            # Check for cd commands in RUN
            if re.search(r"RUN.*cd\s+", content):
                findings.append(
                    LintFinding(
                        rule_id="CUSTOM-BEST-002",
                        description="Using 'cd' instead of WORKDIR",
                        severity=LintSeverity.WARNING,
                        category=RuleCategory.BEST_PRACTICE,
                        fix_suggestion=("Use WORKDIR instead of cd for clarity"),
                    )
                )

        return findings

    def _extract_stages(self, content: str) -> List[str]:
        """Extract multi-stage build stage names."""
        stages = []
        pattern = r"FROM\s+.*?\s+AS\s+(\w+)"
        for match in re.finditer(pattern, content, re.IGNORECASE):
            stages.append(match.group(1))
        return stages

    def _extract_base_images(self, content: str) -> List[str]:
        """Extract base images from FROM instructions."""
        images = []
        for match in re.finditer(r"FROM\s+([\w:/.@-]+)", content):
            images.append(match.group(1))
        return images

    def _severity_order(self, severity: LintSeverity) -> int:
        """Get sorting order for severity."""
        order = {
            LintSeverity.ERROR: 0,
            LintSeverity.WARNING: 1,
            LintSeverity.INFO: 2,
            LintSeverity.STYLE: 3,
        }
        return order.get(severity, 99)

    def generate_report(self, result: LintResult, format: str = "text") -> str:
        """
        Generate formatted report.

        Args:
            result: LintResult to format
            format: Output format ('text', 'json', 'sarif')

        Returns:
            Formatted report string
        """
        if format == "json":
            return json.dumps(result.to_dict(), indent=2)
        elif format == "sarif":
            return self._generate_sarif_report(result)
        else:
            return self._generate_text_report(result)

    def _generate_text_report(self, result: LintResult) -> str:
        """Generate human-readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"Dockerfile Lint Report: {result.dockerfile_path}")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        lines.append("Summary:")
        lines.append(f"  Total Findings: {len(result.findings)}")
        lines.append(f"  Errors:         {result.error_count}")
        lines.append(f"  Warnings:       {result.warning_count}")
        lines.append(f"  Info:           {result.info_count}")
        lines.append(f"  Style:          {result.style_count}")
        lines.append(f"  Total Lines:    {result.total_lines}")
        lines.append(f"  Build Stages:   {len(result.stages)}")
        healthcheck_str = "Yes" if result.has_healthcheck else "No"
        lines.append(f"  Healthcheck:    {healthcheck_str}")
        user_str = "Yes" if result.has_user else "No"
        lines.append(f"  Non-root User:  {user_str}")
        labels_str = "Yes" if result.has_labels else "No"
        lines.append(f"  Has Labels:     {labels_str}")
        lines.append(f"  Scan Duration:  {result.scan_duration:.2f}s")
        lines.append("")

        # Base Images
        if result.base_images:
            lines.append("Base Images:")
            for img in result.base_images:
                lines.append(f"  - {img}")
            lines.append("")

        # Stages
        if result.stages:
            lines.append("Build Stages:")
            for stage in result.stages:
                lines.append(f"  - {stage}")
            lines.append("")

        # Findings by severity
        if result.findings:
            severities = [
                LintSeverity.ERROR,
                LintSeverity.WARNING,
                LintSeverity.INFO,
                LintSeverity.STYLE,
            ]
            for severity in severities:
                findings = [f for f in result.findings if f.severity == severity]
                if findings:
                    sev_label = f"{severity.value.upper()}S ({len(findings)}):"
                    lines.append(sev_label)
                    lines.append("-" * 80)

                    for finding in findings:
                        desc = f"[{finding.rule_id}] {finding.description}"
                        lines.append(desc)
                        if finding.line_number:
                            lines.append(f"  Line: {finding.line_number}")
                        if finding.line_content:
                            code = f"  Code: {finding.line_content.strip()}"
                            lines.append(code)
                        if finding.fix_suggestion:
                            fix = f"  Fix:  {finding.fix_suggestion}"
                            lines.append(fix)
                        if finding.documentation_url:
                            docs = f"  Docs: {finding.documentation_url}"
                            lines.append(docs)
                        lines.append(f"  Source: {finding.source}")
                        lines.append("")

        else:
            lines.append("No findings - Dockerfile looks good!")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def _generate_sarif_report(self, result: LintResult) -> str:
        """Generate SARIF 2.1.0 format report."""
        schema_url = (
            "https://raw.githubusercontent.com/oasis-tcs/"
            "sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
        )
        info_uri = "https://github.com/devops/container-platform"

        sarif = {
            "$schema": schema_url,
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "DockerfileLinter",
                            "version": "1.0.0",
                            "informationUri": info_uri,
                            "rules": self._get_sarif_rules(result),
                        }
                    },
                    "results": [f.to_sarif() for f in result.findings],
                    "properties": {
                        "total_lines": result.total_lines,
                        "stages": result.stages,
                        "base_images": result.base_images,
                        "has_healthcheck": result.has_healthcheck,
                        "has_user": result.has_user,
                        "scan_duration": result.scan_duration,
                    },
                }
            ],
        }
        return json.dumps(sarif, indent=2)

    def _get_sarif_rules(self, result: LintResult) -> List[Dict[str, Any]]:
        """Get unique rules for SARIF report."""
        rules = {}
        for finding in result.findings:
            if finding.rule_id not in rules:
                rules[finding.rule_id] = {
                    "id": finding.rule_id,
                    "shortDescription": {"text": finding.description},
                    "fullDescription": {"text": finding.description},
                    "defaultConfiguration": {
                        "level": finding._severity_to_sarif_level()
                    },
                    "properties": {"category": finding.category.value},
                }
        return list(rules.values())

    def check_hadolint_installed(self) -> Tuple[bool, Optional[str]]:
        """
        Check if hadolint is installed.

        Returns:
            Tuple of (is_installed, version_string)
        """
        if not self.hadolint_path:
            return False, None

        try:
            result = subprocess.run(
                [self.hadolint_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, version
        except Exception:
            pass

        return False, None

    def get_installation_instructions(self) -> str:
        """Get hadolint installation instructions."""
        return """
hadolint Installation Instructions:

macOS:
  brew install hadolint

Linux:
  wget -O /usr/local/bin/hadolint \\
    https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
  chmod +x /usr/local/bin/hadolint

Windows:
  scoop install hadolint

Docker:
  docker run --rm -i hadolint/hadolint < Dockerfile

For more information: https://github.com/hadolint/hadolint
"""
