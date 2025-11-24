"""
Infrastructure as Code Security Scanner.

This module provides comprehensive security scanning for Infrastructure as Code
files including Terraform, CloudFormation, Kubernetes manifests, and Helm charts.
It orchestrates multiple security scanners (Checkov, tfsec, Terrascan, Trivy) and
aggregates results with deduplication and framework mapping.

Example:
    >>> config = IaCConfig(
    ...     scanners=[ScannerType.CHECKOV, ScannerType.TFSEC],
    ...     frameworks=[ComplianceFramework.CIS_AWS],
    ...     include_passed=False
    ... )
    >>> scanner = IaCScanner(config)
    >>> result = scanner.scan_terraform("./terraform")
    >>> print(f"Found {result.failed_count} issues")
"""

import json
import logging
import shutil
import subprocess  # nosec B404  # Controlled input for security scanners
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field, validator


class IaCType(str, Enum):
    """Infrastructure as Code file types."""

    TERRAFORM = "terraform"
    CLOUDFORMATION = "cloudformation"
    KUBERNETES = "kubernetes"
    HELM = "helm"
    ARM_TEMPLATE = "arm_template"


class ScannerType(str, Enum):
    """Supported security scanners."""

    TRIVY = "trivy"
    CHECKOV = "checkov"
    TFSEC = "tfsec"
    TERRASCAN = "terrascan"


class SeverityLevel(str, Enum):
    """Security finding severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ComplianceFramework(str, Enum):
    """Compliance and security frameworks."""

    CIS_AWS = "CIS_AWS"
    CIS_AZURE = "CIS_AZURE"
    CIS_GCP = "CIS_GCP"
    NIST = "NIST"
    PCI_DSS = "PCI_DSS"
    HIPAA = "HIPAA"


class IaCConfig(BaseModel):
    """Configuration for IaC security scanning."""

    scanners: List[ScannerType] = Field(
        default=[ScannerType.CHECKOV, ScannerType.TFSEC],
        description="List of scanners to use",
    )
    frameworks: List[ComplianceFramework] = Field(
        default=[], description="Compliance frameworks to check against"
    )
    skip_checks: List[str] = Field(default=[], description="Check IDs to skip")
    include_passed: bool = Field(
        default=False, description="Include passed checks in results"
    )
    timeout: int = Field(default=300, description="Scanner timeout in seconds")
    enable_secret_detection: bool = Field(
        default=True, description="Enable secret detection in IaC files"
    )
    min_severity: SeverityLevel = Field(
        default=SeverityLevel.INFO, description="Minimum severity level to report"
    )

    @validator("timeout")
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is reasonable."""
        if v < 10 or v > 3600:
            raise ValueError("Timeout must be between 10 and 3600 seconds")
        return v


class IaCFinding(BaseModel):
    """Security finding from IaC scan."""

    check_id: str = Field(description="Unique check identifier")
    title: str = Field(description="Finding title")
    severity: SeverityLevel = Field(description="Severity level")
    description: str = Field(description="Detailed description")
    resource: str = Field(description="Affected resource")
    file_path: str = Field(description="File containing the issue")
    line_number: Optional[int] = Field(
        default=None, description="Line number of the issue"
    )
    scanner: ScannerType = Field(description="Scanner that found the issue")
    framework: List[ComplianceFramework] = Field(
        default=[], description="Related compliance frameworks"
    )
    remediation: Optional[str] = Field(default=None, description="Remediation guidance")
    guideline: Optional[str] = Field(
        default=None, description="Guideline or documentation URL"
    )
    code_block: Optional[str] = Field(
        default=None, description="Vulnerable code snippet"
    )

    def __hash__(self) -> int:
        """Hash for deduplication."""
        return hash((self.check_id, self.file_path, self.line_number))

    def __eq__(self, other: object) -> bool:
        """Equality for deduplication."""
        if not isinstance(other, IaCFinding):
            return False
        return (
            self.check_id == other.check_id
            and self.file_path == other.file_path
            and self.line_number == other.line_number
        )


class IaCResult(BaseModel):
    """Results from IaC security scan."""

    findings: List[IaCFinding] = Field(description="Security findings")
    total_count: int = Field(description="Total checks performed")
    failed_count: int = Field(description="Number of failed checks")
    passed_count: int = Field(description="Number of passed checks")
    scanner_results: Dict[str, int] = Field(
        default={}, description="Per-scanner finding counts"
    )
    scan_time: float = Field(description="Scan duration in seconds")
    iac_type: Optional[IaCType] = Field(default=None, description="Type of IaC scanned")
    scan_path: str = Field(description="Scanned path or file")


class IaCScanError(Exception):
    """Base exception for IaC scanning errors."""

    pass


class ScannerNotFoundError(IaCScanError):
    """Raised when required scanner is not installed."""

    pass


class InvalidIaCError(IaCScanError):
    """Raised when IaC file is invalid or malformed."""

    pass


class IaCScanner:
    """
    Multi-scanner IaC security analyzer.

    Orchestrates multiple security scanners to analyze Infrastructure as Code
    files for security vulnerabilities, misconfigurations, and compliance issues.
    Supports Terraform, CloudFormation, Kubernetes, Helm, and ARM templates.

    Attributes:
        config: Scanner configuration
        logger: Logger instance
    """

    SEVERITY_MAP = {
        "CRITICAL": SeverityLevel.CRITICAL,
        "HIGH": SeverityLevel.HIGH,
        "MEDIUM": SeverityLevel.MEDIUM,
        "LOW": SeverityLevel.LOW,
        "INFO": SeverityLevel.INFO,
        "UNKNOWN": SeverityLevel.INFO,
    }

    FRAMEWORK_KEYWORDS = {
        ComplianceFramework.CIS_AWS: ["cis", "aws"],
        ComplianceFramework.CIS_AZURE: ["cis", "azure"],
        ComplianceFramework.CIS_GCP: ["cis", "gcp", "google"],
        ComplianceFramework.NIST: ["nist"],
        ComplianceFramework.PCI_DSS: ["pci", "pci-dss"],
        ComplianceFramework.HIPAA: ["hipaa"],
    }

    def __init__(self, config: IaCConfig) -> None:
        """
        Initialize IaC scanner.

        Args:
            config: Scanner configuration

        Raises:
            ScannerNotFoundError: If required scanners are not installed
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        missing_scanners = []
        for scanner in config.scanners:
            if not self._is_scanner_installed(scanner):
                missing_scanners.append(scanner.value)

        if missing_scanners:
            raise ScannerNotFoundError(
                f"Required scanners not found: {', '.join(missing_scanners)}"
            )

    def _is_scanner_installed(self, scanner: ScannerType) -> bool:
        """
        Check if a scanner is installed.

        Args:
            scanner: Scanner to check

        Returns:
            True if scanner is installed
        """
        command_map = {
            ScannerType.CHECKOV: "checkov",
            ScannerType.TFSEC: "tfsec",
            ScannerType.TERRASCAN: "terrascan",
            ScannerType.TRIVY: "trivy",
        }
        return shutil.which(command_map[scanner]) is not None

    @staticmethod
    def check_scanners_installed() -> Dict[str, bool]:
        """
        Check availability of all supported scanners.

        Returns:
            Dictionary mapping scanner names to installation status
        """
        scanners = {
            "checkov": "checkov",
            "tfsec": "tfsec",
            "terrascan": "terrascan",
            "trivy": "trivy",
        }
        return {name: shutil.which(cmd) is not None for name, cmd in scanners.items()}

    def scan_terraform(self, path: str) -> IaCResult:
        """
        Scan Terraform files for security issues.

        Args:
            path: Path to Terraform files or directory

        Returns:
            Scan results with findings

        Raises:
            InvalidIaCError: If path is invalid or contains no Terraform files
            IaCScanError: If scanning fails
        """
        target_path = Path(path)
        if not target_path.exists():
            raise InvalidIaCError(f"Path does not exist: {path}")

        tf_files = list(target_path.rglob("*.tf")) if target_path.is_dir() else []
        if target_path.is_file() and target_path.suffix == ".tf":
            tf_files = [target_path]

        if not tf_files:
            raise InvalidIaCError(f"No Terraform files found in: {path}")

        self.logger.info(f"Scanning {len(tf_files)} Terraform files in {path}")
        return self._execute_scan(str(target_path), IaCType.TERRAFORM)

    def scan_cloudformation(self, template: str) -> IaCResult:
        """
        Scan CloudFormation template for security issues.

        Args:
            template: Path to CloudFormation template file

        Returns:
            Scan results with findings

        Raises:
            InvalidIaCError: If template is invalid
            IaCScanError: If scanning fails
        """
        template_path = Path(template)
        if not template_path.exists():
            raise InvalidIaCError(f"Template does not exist: {template}")

        if template_path.suffix not in [".json", ".yaml", ".yml", ".template"]:
            raise InvalidIaCError(
                f"Invalid CloudFormation template extension: {template_path.suffix}"
            )

        self.logger.info(f"Scanning CloudFormation template: {template}")
        return self._execute_scan(str(template_path), IaCType.CLOUDFORMATION)

    def scan_kubernetes(self, manifest: str) -> IaCResult:
        """
        Scan Kubernetes manifest for security issues.

        Args:
            manifest: Path to Kubernetes manifest file or directory

        Returns:
            Scan results with findings

        Raises:
            InvalidIaCError: If manifest is invalid
            IaCScanError: If scanning fails
        """
        manifest_path = Path(manifest)
        if not manifest_path.exists():
            raise InvalidIaCError(f"Manifest does not exist: {manifest}")

        self.logger.info(f"Scanning Kubernetes manifest: {manifest}")
        return self._execute_scan(str(manifest_path), IaCType.KUBERNETES)

    def _execute_scan(self, path: str, iac_type: IaCType) -> IaCResult:
        """
        Execute security scan with configured scanners.

        Args:
            path: Path to scan
            iac_type: Type of IaC being scanned

        Returns:
            Aggregated scan results
        """
        start_time = datetime.now()
        all_findings: List[List[IaCFinding]] = []

        for scanner in self.config.scanners:
            try:
                findings = self._run_scanner(scanner, path, iac_type)
                all_findings.append(findings)
                self.logger.info(f"{scanner.value} found {len(findings)} issues")
            except Exception as e:
                self.logger.error(f"Scanner {scanner.value} failed: {e}")
                continue

        scan_time = (datetime.now() - start_time).total_seconds()
        return self._aggregate_results(all_findings, scan_time, path, iac_type)

    def _run_scanner(
        self, scanner: ScannerType, path: str, iac_type: IaCType
    ) -> List[IaCFinding]:
        """
        Execute a specific scanner.

        Args:
            scanner: Scanner to run
            path: Path to scan
            iac_type: Type of IaC

        Returns:
            List of findings from the scanner
        """
        scanner_map = {
            ScannerType.CHECKOV: self._run_checkov,
            ScannerType.TFSEC: self._run_tfsec,
            ScannerType.TERRASCAN: self._run_terrascan,
            ScannerType.TRIVY: self._run_trivy_config,
        }

        if scanner in scanner_map:
            return scanner_map[scanner](path, iac_type)
        return []

    def _run_checkov(self, path: str, iac_type: IaCType) -> List[IaCFinding]:
        """
        Execute Checkov scanner.

        Args:
            path: Path to scan
            iac_type: Type of IaC

        Returns:
            List of findings
        """
        cmd = [
            "checkov",
            "-d" if Path(path).is_dir() else "-f",
            path,
            "--output",
            "json",
            "--quiet",
        ]

        if iac_type == IaCType.TERRAFORM:
            cmd.extend(["--framework", "terraform"])
        elif iac_type == IaCType.CLOUDFORMATION:
            cmd.extend(["--framework", "cloudformation"])
        elif iac_type == IaCType.KUBERNETES:
            cmd.extend(["--framework", "kubernetes"])

        if self.config.skip_checks:
            cmd.extend(["--skip-check", ",".join(self.config.skip_checks)])

        if self.config.frameworks:
            for framework in self.config.frameworks:
                if framework in [
                    ComplianceFramework.CIS_AWS,
                    ComplianceFramework.CIS_AZURE,
                    ComplianceFramework.CIS_GCP,
                ]:
                    cmd.extend(["--check", "CKV_*"])

        try:
            result = subprocess.run(  # nosec B603  # Controlled scanner commands
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                check=False,
            )

            if not result.stdout:
                return []

            data = json.loads(result.stdout)
            return self._parse_checkov_output(data)

        except subprocess.TimeoutExpired:
            raise IaCScanError(f"Checkov scan timed out after {self.config.timeout}s")
        except json.JSONDecodeError as e:
            raise IaCScanError(f"Failed to parse Checkov output: {e}")
        except Exception as e:
            raise IaCScanError(f"Checkov execution failed: {e}")

    def _parse_checkov_output(self, data: Dict[str, Any]) -> List[IaCFinding]:
        """
        Parse Checkov JSON output.

        Args:
            data: Checkov JSON output

        Returns:
            List of findings
        """
        findings: List[IaCFinding] = []

        for result in data.get("results", {}).get("failed_checks", []):
            severity = self._map_severity(result.get("check_class", "").upper())

            if not self._meets_severity_threshold(severity):
                continue

            frameworks = self._extract_frameworks(
                result.get("check_id", ""), result.get("guideline", "")
            )

            finding = IaCFinding(
                check_id=result.get("check_id", "UNKNOWN"),
                title=result.get("check_name", "Unknown check"),
                severity=severity,
                description=result.get("check_result", {}).get(
                    "result", "No description"
                ),
                resource=result.get("resource", "Unknown"),
                file_path=result.get("file_path", ""),
                line_number=self._safe_int(result.get("file_line_range", [0])[0]),
                scanner=ScannerType.CHECKOV,
                framework=frameworks,
                remediation=result.get("guideline", ""),
                guideline=result.get("guideline", ""),
                code_block=(
                    result.get("code_block", [[""]])[0][0]
                    if result.get("code_block")
                    else None
                ),
            )
            findings.append(finding)

        if self.config.include_passed:
            for result in data.get("results", {}).get("passed_checks", []):
                frameworks = self._extract_frameworks(
                    result.get("check_id", ""), result.get("guideline", "")
                )

                finding = IaCFinding(
                    check_id=result.get("check_id", "UNKNOWN"),
                    title=result.get("check_name", "Unknown check"),
                    severity=SeverityLevel.INFO,
                    description="Check passed",
                    resource=result.get("resource", "Unknown"),
                    file_path=result.get("file_path", ""),
                    line_number=self._safe_int(result.get("file_line_range", [0])[0]),
                    scanner=ScannerType.CHECKOV,
                    framework=frameworks,
                    guideline=result.get("guideline", ""),
                )
                findings.append(finding)

        return findings

    def _run_tfsec(self, path: str, iac_type: IaCType) -> List[IaCFinding]:
        """
        Execute tfsec scanner.

        Args:
            path: Path to scan
            iac_type: Type of IaC

        Returns:
            List of findings
        """
        if iac_type != IaCType.TERRAFORM:
            return []

        cmd = [
            "tfsec",
            path,
            "--format",
            "json",
            "--no-color",
        ]

        if self.config.skip_checks:
            for check in self.config.skip_checks:
                cmd.extend(["-e", check])

        try:
            result = subprocess.run(  # nosec B603  # Controlled scanner commands
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                check=False,
            )

            if not result.stdout:
                return []

            data = json.loads(result.stdout)
            return self._parse_tfsec_output(data)

        except subprocess.TimeoutExpired:
            raise IaCScanError(f"tfsec scan timed out after {self.config.timeout}s")
        except json.JSONDecodeError as e:
            raise IaCScanError(f"Failed to parse tfsec output: {e}")
        except Exception as e:
            raise IaCScanError(f"tfsec execution failed: {e}")

    def _parse_tfsec_output(self, data: Dict[str, Any]) -> List[IaCFinding]:
        """
        Parse tfsec JSON output.

        Args:
            data: tfsec JSON output

        Returns:
            List of findings
        """
        findings: List[IaCFinding] = []

        for result in data.get("results", []):
            severity = self._map_severity(result.get("severity", "UNKNOWN").upper())

            if not self._meets_severity_threshold(severity):
                continue

            frameworks = self._extract_frameworks(
                result.get("rule_id", ""),
                result.get("links", [""])[0] if result.get("links") else "",
            )

            finding = IaCFinding(
                check_id=result.get("rule_id", "UNKNOWN"),
                title=result.get("rule_description", "Unknown check"),
                severity=severity,
                description=result.get("description", "No description"),
                resource=result.get("resource", "Unknown"),
                file_path=result.get("location", {}).get("filename", ""),
                line_number=result.get("location", {}).get("start_line", 0),
                scanner=ScannerType.TFSEC,
                framework=frameworks,
                remediation=result.get("resolution", ""),
                guideline=result.get("links", [""])[0] if result.get("links") else None,
            )
            findings.append(finding)

        return findings

    def _run_terrascan(self, path: str, iac_type: IaCType) -> List[IaCFinding]:
        """
        Execute Terrascan scanner.

        Args:
            path: Path to scan
            iac_type: Type of IaC

        Returns:
            List of findings
        """
        iac_map = {
            IaCType.TERRAFORM: "terraform",
            IaCType.CLOUDFORMATION: "cloudformation",
            IaCType.KUBERNETES: "k8s",
            IaCType.HELM: "helm",
            IaCType.ARM_TEMPLATE: "arm",
        }

        if iac_type not in iac_map:
            return []

        cmd = [
            "terrascan",
            "scan",
            "-i",
            iac_map[iac_type],
            "-d" if Path(path).is_dir() else "-f",
            path,
            "-o",
            "json",
        ]

        if self.config.skip_checks:
            cmd.extend(["--skip-rules", ",".join(self.config.skip_checks)])

        try:
            result = subprocess.run(  # nosec B603  # Controlled scanner commands
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                check=False,
            )

            if not result.stdout:
                return []

            data = json.loads(result.stdout)
            return self._parse_terrascan_output(data)

        except subprocess.TimeoutExpired:
            raise IaCScanError(f"Terrascan timed out after {self.config.timeout}s")
        except json.JSONDecodeError as e:
            raise IaCScanError(f"Failed to parse Terrascan output: {e}")
        except Exception as e:
            raise IaCScanError(f"Terrascan execution failed: {e}")

    def _parse_terrascan_output(self, data: Dict[str, Any]) -> List[IaCFinding]:
        """
        Parse Terrascan JSON output.

        Args:
            data: Terrascan JSON output

        Returns:
            List of findings
        """
        findings: List[IaCFinding] = []

        for result in data.get("results", {}).get("violations", []):
            severity = self._map_severity(result.get("severity", "UNKNOWN").upper())

            if not self._meets_severity_threshold(severity):
                continue

            frameworks = self._extract_frameworks(
                result.get("rule_id", ""), result.get("rule_reference_id", "")
            )

            finding = IaCFinding(
                check_id=result.get("rule_id", "UNKNOWN"),
                title=result.get("rule_name", "Unknown check"),
                severity=severity,
                description=result.get("description", "No description"),
                resource=result.get("resource_name", "Unknown"),
                file_path=result.get("file", ""),
                line_number=result.get("line", 0),
                scanner=ScannerType.TERRASCAN,
                framework=frameworks,
                remediation=result.get("resolution", ""),
                guideline=result.get("rule_reference_id", ""),
            )
            findings.append(finding)

        return findings

    def _run_trivy_config(self, path: str, iac_type: IaCType) -> List[IaCFinding]:
        """
        Execute Trivy config scanner.

        Args:
            path: Path to scan
            iac_type: Type of IaC

        Returns:
            List of findings
        """
        cmd = [
            "trivy",
            "config",
            path,
            "--format",
            "json",
            "--quiet",
        ]

        if self.config.skip_checks:
            for check in self.config.skip_checks:
                cmd.extend(["--skip-policy-update", check])

        if self.config.enable_secret_detection:
            cmd.append("--security-checks")
            cmd.append("config,secret")

        try:
            result = subprocess.run(  # nosec B603  # Controlled scanner commands
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                check=False,
            )

            if not result.stdout:
                return []

            data = json.loads(result.stdout)
            return self._parse_trivy_output(data)

        except subprocess.TimeoutExpired:
            raise IaCScanError(f"Trivy scan timed out after {self.config.timeout}s")
        except json.JSONDecodeError as e:
            raise IaCScanError(f"Failed to parse Trivy output: {e}")
        except Exception as e:
            raise IaCScanError(f"Trivy execution failed: {e}")

    def _parse_trivy_output(self, data: Dict[str, Any]) -> List[IaCFinding]:
        """
        Parse Trivy JSON output.

        Args:
            data: Trivy JSON output

        Returns:
            List of findings
        """
        findings: List[IaCFinding] = []

        for result in data.get("Results", []):
            target = result.get("Target", "Unknown")

            for misconfiguration in result.get("Misconfigurations", []):
                severity = self._map_severity(
                    misconfiguration.get("Severity", "UNKNOWN").upper()
                )

                if not self._meets_severity_threshold(severity):
                    continue

                frameworks = self._extract_frameworks(
                    misconfiguration.get("ID", ""),
                    misconfiguration.get("PrimaryURL", ""),
                )

                finding = IaCFinding(
                    check_id=misconfiguration.get("ID", "UNKNOWN"),
                    title=misconfiguration.get("Title", "Unknown check"),
                    severity=severity,
                    description=misconfiguration.get("Description", "No description"),
                    resource=misconfiguration.get("CauseMetadata", {}).get(
                        "Resource", target
                    ),
                    file_path=target,
                    line_number=misconfiguration.get("CauseMetadata", {}).get(
                        "StartLine", 0
                    ),
                    scanner=ScannerType.TRIVY,
                    framework=frameworks,
                    remediation=misconfiguration.get("Resolution", ""),
                    guideline=misconfiguration.get("PrimaryURL", ""),
                )
                findings.append(finding)

            for secret in result.get("Secrets", []):
                finding = IaCFinding(
                    check_id=secret.get("RuleID", "SECRET"),
                    title=secret.get("Title", "Secret detected"),
                    severity=SeverityLevel.CRITICAL,
                    description=secret.get("Match", "Secret found in code"),
                    resource=target,
                    file_path=target,
                    line_number=secret.get("StartLine", 0),
                    scanner=ScannerType.TRIVY,
                    framework=[],
                    remediation="Remove secret from code and use secret management",
                )
                findings.append(finding)

        return findings

    def _aggregate_results(
        self,
        all_findings: List[List[IaCFinding]],
        scan_time: float,
        scan_path: str,
        iac_type: Optional[IaCType] = None,
    ) -> IaCResult:
        """
        Aggregate results from multiple scanners.

        Args:
            all_findings: List of finding lists from each scanner
            scan_time: Time taken to scan
            scan_path: Path that was scanned
            iac_type: Type of IaC scanned

        Returns:
            Aggregated scan results
        """
        flat_findings = [finding for findings in all_findings for finding in findings]

        deduplicated = self._deduplicate_findings(flat_findings)

        scanner_counts: Dict[str, int] = {}
        for findings in all_findings:
            if findings:
                scanner = findings[0].scanner.value
                scanner_counts[scanner] = len(findings)

        failed_findings = [f for f in deduplicated if f.severity != SeverityLevel.INFO]
        passed_findings = [f for f in deduplicated if f.severity == SeverityLevel.INFO]

        return IaCResult(
            findings=deduplicated,
            total_count=len(deduplicated),
            failed_count=len(failed_findings),
            passed_count=len(passed_findings),
            scanner_results=scanner_counts,
            scan_time=scan_time,
            iac_type=iac_type,
            scan_path=scan_path,
        )

    def _deduplicate_findings(self, findings: List[IaCFinding]) -> List[IaCFinding]:
        """
        Remove duplicate findings across scanners.

        Deduplication strategy:
        1. Same check_id, file_path, and line_number = duplicate
        2. Keep finding from scanner with highest priority
        3. Merge framework information

        Args:
            findings: List of findings to deduplicate

        Returns:
            Deduplicated findings
        """
        scanner_priority = {
            ScannerType.CHECKOV: 1,
            ScannerType.TRIVY: 2,
            ScannerType.TFSEC: 3,
            ScannerType.TERRASCAN: 4,
        }

        unique_map: Dict[Tuple[str, str, Optional[int]], IaCFinding] = {}

        for finding in findings:
            key = (finding.check_id, finding.file_path, finding.line_number)

            if key not in unique_map:
                unique_map[key] = finding
            else:
                existing = unique_map[key]
                if scanner_priority.get(finding.scanner, 99) < scanner_priority.get(
                    existing.scanner, 99
                ):
                    combined_frameworks = list(
                        set(existing.framework + finding.framework)
                    )
                    finding.framework = combined_frameworks
                    unique_map[key] = finding
                else:
                    combined_frameworks = list(
                        set(existing.framework + finding.framework)
                    )
                    existing.framework = combined_frameworks

        return sorted(
            list(unique_map.values()),
            key=lambda x: (
                list(SeverityLevel).index(x.severity),
                x.file_path,
                x.line_number or 0,
            ),
        )

    def _extract_frameworks(
        self, check_id: str, guideline: str
    ) -> List[ComplianceFramework]:
        """
        Extract compliance frameworks from check ID and guideline.

        Args:
            check_id: Check identifier
            guideline: Guideline or reference URL

        Returns:
            List of applicable compliance frameworks
        """
        frameworks: Set[ComplianceFramework] = set()
        combined_text = f"{check_id} {guideline}".lower()

        for framework, keywords in self.FRAMEWORK_KEYWORDS.items():
            if any(keyword in combined_text for keyword in keywords):
                frameworks.add(framework)

        return list(frameworks)

    def _map_severity(self, severity_str: str) -> SeverityLevel:
        """
        Map scanner severity string to SeverityLevel.

        Args:
            severity_str: Severity string from scanner

        Returns:
            Mapped severity level
        """
        normalized = severity_str.upper().strip()
        return self.SEVERITY_MAP.get(normalized, SeverityLevel.INFO)

    def _meets_severity_threshold(self, severity: SeverityLevel) -> bool:
        """
        Check if severity meets configured threshold.

        Args:
            severity: Severity level to check

        Returns:
            True if severity meets threshold
        """
        severity_order = [
            SeverityLevel.CRITICAL,
            SeverityLevel.HIGH,
            SeverityLevel.MEDIUM,
            SeverityLevel.LOW,
            SeverityLevel.INFO,
        ]

        try:
            severity_index = severity_order.index(severity)
            threshold_index = severity_order.index(self.config.min_severity)
            return severity_index <= threshold_index
        except ValueError:
            return True

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        """
        Safely convert value to int.

        Args:
            value: Value to convert

        Returns:
            Integer value or None
        """
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None


def main() -> None:
    """Demonstrate IaCScanner usage and check scanner availability."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("Checking scanner availability...")
    available = IaCScanner.check_scanners_installed()
    for scanner_name, installed in available.items():
        status = "✓" if installed else "✗"
        print(f"  {status} {scanner_name}")

    installed_scanners = [
        ScannerType(name) for name, installed in available.items() if installed
    ]

    if not installed_scanners:
        print("\nNo scanners installed. Please install at least one scanner:")
        print("  - pip install checkov")
        print("  - brew install tfsec (macOS)")
        print("  - brew install terrascan (macOS)")
        print("  - brew install trivy (macOS)")
        return

    config = IaCConfig(
        scanners=installed_scanners,
        frameworks=[ComplianceFramework.CIS_AWS, ComplianceFramework.NIST],
        include_passed=False,
        enable_secret_detection=True,
        min_severity=SeverityLevel.MEDIUM,
    )

    _ = IaCScanner(config)

    print(
        f"\nScanner initialized with: " f"{', '.join(s.value for s in config.scanners)}"
    )
    print("Ready to scan Infrastructure as Code files.")


if __name__ == "__main__":
    main()
