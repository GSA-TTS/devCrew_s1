"""
Security Scanner Module for Container Platform Management.

This module provides comprehensive container security scanning with
multi-scanner support (Trivy and Grype), vulnerability analysis, SBOM
generation, and result caching for improved performance.

Features:
    - Dual scanner support (Trivy and Grype)
    - CVE detection with NVD and vendor advisories
    - SBOM generation in SPDX and CycloneDX formats
    - Severity filtering and threshold enforcement
    - Misconfiguration detection
    - License compliance scanning
    - Result caching with TTL
    - Ignore list for false positives
    - Incremental scanning support

Author: DevCrew Container Platform Team
License: MIT
Protocol Coverage: TOOL-CONTAINER-PLATFORM (Issue #58)
"""

import hashlib
import json
import logging
import shutil
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class SecurityScanError(Exception):
    """Base exception for security scanning errors."""

    pass


class ScannerNotFoundError(SecurityScanError):
    """Raised when required scanner is not installed."""

    pass


class ImageNotFoundError(SecurityScanError):
    """Raised when Docker image cannot be found."""

    pass


class ScanTimeoutError(SecurityScanError):
    """Raised when scan operation times out."""

    pass


class InvalidImageNameError(SecurityScanError):
    """Raised when image name format is invalid."""

    pass


class CacheError(SecurityScanError):
    """Raised when cache operations fail."""

    pass


# ============================================================================
# Enums
# ============================================================================


class ScannerType(str, Enum):
    """Supported vulnerability scanners."""

    TRIVY = "trivy"
    GRYPE = "grype"
    BOTH = "both"  # Run both scanners and aggregate results


class SeverityLevel(str, Enum):
    """Vulnerability severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NEGLIGIBLE = "NEGLIGIBLE"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_string(cls, value: str) -> "SeverityLevel":
        """Convert string to SeverityLevel, handling variations."""
        value_upper = value.upper()
        try:
            return cls(value_upper)
        except ValueError:
            logger.warning(f"Unknown severity level: {value}, using UNKNOWN")
            return cls.UNKNOWN


class SBOMFormat(str, Enum):
    """SBOM output formats."""

    SPDX = "spdx"
    SPDX_JSON = "spdx-json"
    CYCLONEDX = "cyclonedx"
    CYCLONEDX_JSON = "cyclonedx-json"


class MisconfigType(str, Enum):
    """Misconfiguration types."""

    DOCKERFILE = "dockerfile"
    KUBERNETES = "kubernetes"
    SECRETS = "secrets"
    LICENSE = "license"


# ============================================================================
# Pydantic Models
# ============================================================================


class ScannerConfig(BaseModel):
    """Scanner configuration."""

    scanner_type: ScannerType = Field(
        default=ScannerType.TRIVY, description="Scanner to use"
    )
    severity_threshold: SeverityLevel = Field(
        default=SeverityLevel.MEDIUM, description="Minimum severity to report"
    )
    timeout: int = Field(
        default=600, ge=30, le=3600, description="Scan timeout in seconds"
    )
    ignore_unfixed: bool = Field(
        default=False, description="Ignore vulnerabilities without fixes"
    )
    skip_db_update: bool = Field(
        default=False, description="Skip vulnerability database update"
    )
    enable_cache: bool = Field(default=True, description="Enable result caching")
    cache_ttl: int = Field(default=3600, ge=60, description="Cache TTL in seconds")
    cache_dir: Optional[Path] = Field(default=None, description="Cache directory path")
    output_dir: Optional[Path] = Field(
        default=None, description="Output directory for reports"
    )
    ignore_list: List[str] = Field(
        default_factory=list, description="CVE IDs to ignore"
    )
    scan_misconfig: bool = Field(default=True, description="Scan for misconfigurations")
    scan_secrets: bool = Field(default=True, description="Scan for secrets")
    scan_licenses: bool = Field(
        default=False, description="Scan for license compliance"
    )


class Vulnerability(BaseModel):
    """Vulnerability information."""

    id: str = Field(..., description="CVE or vulnerability ID")
    severity: SeverityLevel = Field(..., description="Vulnerability severity")
    title: str = Field(default="", description="Vulnerability title")
    description: str = Field(default="", description="Detailed description")
    package_name: str = Field(..., description="Affected package")
    installed_version: str = Field(..., description="Installed version")
    fixed_version: Optional[str] = Field(default=None, description="Version with fix")
    cvss_score: Optional[float] = Field(
        default=None, ge=0.0, le=10.0, description="CVSS score"
    )
    cvss_vector: Optional[str] = Field(default=None, description="CVSS vector string")
    cwe_ids: List[str] = Field(default_factory=list, description="CWE identifiers")
    published_date: Optional[datetime] = Field(
        default=None, description="Publication date"
    )
    references: List[str] = Field(default_factory=list, description="Reference URLs")
    scanner: str = Field(..., description="Scanner that found this")

    def is_fixable(self) -> bool:
        """Check if vulnerability has a fix available."""
        return self.fixed_version is not None

    def meets_threshold(self, threshold: SeverityLevel) -> bool:
        """Check if vulnerability meets severity threshold."""
        severity_order = {
            SeverityLevel.CRITICAL: 5,
            SeverityLevel.HIGH: 4,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.LOW: 2,
            SeverityLevel.NEGLIGIBLE: 1,
            SeverityLevel.UNKNOWN: 0,
        }
        vuln_level = severity_order[self.severity]
        threshold_level = severity_order[threshold]
        return vuln_level >= threshold_level


class Misconfiguration(BaseModel):
    """Misconfiguration finding."""

    id: str = Field(..., description="Check ID")
    type: MisconfigType = Field(..., description="Misconfiguration type")
    severity: SeverityLevel = Field(..., description="Finding severity")
    title: str = Field(..., description="Finding title")
    description: str = Field(..., description="Detailed description")
    file_path: str = Field(..., description="File with misconfiguration")
    line_number: Optional[int] = Field(
        default=None, description="Line number if applicable"
    )
    remediation: str = Field(default="", description="How to fix")
    references: List[str] = Field(default_factory=list, description="Reference URLs")


class SecretFinding(BaseModel):
    """Secret detection finding."""

    type: str = Field(..., description="Secret type")
    file_path: str = Field(..., description="File containing secret")
    line_number: Optional[int] = Field(default=None, description="Line number")
    match: str = Field(..., description="Matched pattern (redacted)")
    severity: SeverityLevel = Field(
        default=SeverityLevel.CRITICAL, description="Finding severity"
    )


class LicenseFinding(BaseModel):
    """License compliance finding."""

    package_name: str = Field(..., description="Package name")
    package_version: str = Field(..., description="Package version")
    license_name: str = Field(..., description="License name")
    license_type: str = Field(..., description="License type category")
    compliant: bool = Field(..., description="Whether license is compliant")
    risk_level: str = Field(..., description="Risk level (low/medium/high)")


class ScanResult(BaseModel):
    """Comprehensive scan result."""

    image: str = Field(..., description="Scanned image")
    scan_time: datetime = Field(
        default_factory=datetime.utcnow, description="Scan timestamp"
    )
    scanner_version: Dict[str, str] = Field(
        default_factory=dict, description="Scanner versions used"
    )
    vulnerabilities: List[Vulnerability] = Field(
        default_factory=list, description="Found vulnerabilities"
    )
    misconfigurations: List[Misconfiguration] = Field(
        default_factory=list, description="Found misconfigurations"
    )
    secrets: List[SecretFinding] = Field(
        default_factory=list, description="Found secrets"
    )
    licenses: List[LicenseFinding] = Field(
        default_factory=list, description="License findings"
    )
    sbom: Optional[Dict[str, Any]] = Field(default=None, description="Generated SBOM")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @property
    def total_vulnerabilities(self) -> int:
        """Total vulnerability count."""
        return len(self.vulnerabilities)

    @property
    def critical_count(self) -> int:
        """Critical vulnerability count."""
        return sum(
            1 for v in self.vulnerabilities if v.severity == SeverityLevel.CRITICAL
        )

    @property
    def high_count(self) -> int:
        """High vulnerability count."""
        return sum(1 for v in self.vulnerabilities if v.severity == SeverityLevel.HIGH)

    @property
    def medium_count(self) -> int:
        """Medium vulnerability count."""
        return sum(
            1 for v in self.vulnerabilities if v.severity == SeverityLevel.MEDIUM
        )

    @property
    def low_count(self) -> int:
        """Low vulnerability count."""
        return sum(1 for v in self.vulnerabilities if v.severity == SeverityLevel.LOW)

    @property
    def fixable_count(self) -> int:
        """Count of fixable vulnerabilities."""
        return sum(1 for v in self.vulnerabilities if v.is_fixable())

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive scan summary."""
        return {
            "image": self.image,
            "scan_time": self.scan_time.isoformat(),
            "vulnerabilities": {
                "total": self.total_vulnerabilities,
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "fixable": self.fixable_count,
            },
            "misconfigurations": len(self.misconfigurations),
            "secrets": len(self.secrets),
            "licenses": {
                "total": len(self.licenses),
                "non_compliant": sum(1 for lic in self.licenses if not lic.compliant),
            },
        }

    def has_critical_findings(self) -> bool:
        """Check if result contains critical findings."""
        has_critical_vuln = self.critical_count > 0
        has_critical_secret = len(self.secrets) > 0
        has_critical_misconfig = any(
            m.severity == SeverityLevel.CRITICAL for m in self.misconfigurations
        )
        return has_critical_vuln or has_critical_secret or has_critical_misconfig


# ============================================================================
# Security Scanner
# ============================================================================


class SecurityScanner:
    """
    Comprehensive container security scanner.

    Supports multiple scanners (Trivy, Grype) for vulnerability detection,
    misconfiguration scanning, secret detection, and SBOM generation.

    Attributes:
        config: Scanner configuration
        cache_dir: Cache directory path
        scanners_available: Set of available scanners
    """

    def __init__(self, config: Optional[ScannerConfig] = None):
        """
        Initialize security scanner.

        Args:
            config: Scanner configuration. Uses defaults if None.

        Raises:
            ScannerNotFoundError: If no scanners are available
        """
        self.config = config or ScannerConfig()
        self.cache_dir = self._setup_cache_dir()
        self.scanners_available = self._check_scanners()

        if not self.scanners_available:
            raise ScannerNotFoundError(
                "No security scanners found. Install Trivy or Grype:\n"
                "  Trivy: https://aquasecurity.github.io/trivy/\n"
                "  Grype: https://github.com/anchore/grype"
            )

        logger.info(
            f"SecurityScanner initialized with: {', '.join(self.scanners_available)}"
        )

    def _setup_cache_dir(self) -> Path:
        """
        Setup cache directory.

        Returns:
            Path to cache directory
        """
        if self.config.cache_dir:
            cache_dir = self.config.cache_dir
        else:
            cache_dir = Path.home() / ".container-scanner-cache"

        if self.config.enable_cache:
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache directory: {cache_dir}")

        return cache_dir

    def _check_scanners(self) -> Set[str]:
        """
        Check which scanners are available.

        Returns:
            Set of available scanner names
        """
        available = set()

        if shutil.which("trivy"):
            available.add("trivy")
            logger.debug("Trivy scanner available")

        if shutil.which("grype"):
            available.add("grype")
            logger.debug("Grype scanner available")

        return available

    @staticmethod
    def check_scanner_installed(scanner: str) -> bool:
        """
        Check if specific scanner is installed.

        Args:
            scanner: Scanner name (trivy or grype)

        Returns:
            True if scanner is available
        """
        return shutil.which(scanner) is not None

    def _get_scanner_version(self, scanner: str) -> str:
        """
        Get scanner version.

        Args:
            scanner: Scanner name

        Returns:
            Version string or "unknown"
        """
        try:
            if scanner == "trivy":
                result = subprocess.run(
                    ["trivy", "--version"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10,
                )
                for line in result.stdout.split("\n"):
                    if "Version:" in line:
                        return line.split("Version:")[1].strip()

            elif scanner == "grype":
                result = subprocess.run(
                    ["grype", "version"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10,
                )
                # Parse "Version: X.Y.Z" from output
                for line in result.stdout.split("\n"):
                    if "Version:" in line:
                        return line.split("Version:")[1].strip()

            return "unknown"

        except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Could not get {scanner} version: {e}")
            return "unknown"

    def _validate_image_name(self, image: str) -> None:
        """
        Validate Docker image name format.

        Args:
            image: Image name to validate

        Raises:
            InvalidImageNameError: If image name is invalid
        """
        if not image or len(image.strip()) == 0:
            raise InvalidImageNameError("Image name cannot be empty")

        invalid_chars = [" ", "\n", "\t", "\r", "|", "&", ";"]
        if any(char in image for char in invalid_chars):
            raise InvalidImageNameError(
                f"Image name contains invalid characters: {image}"
            )

    def _get_cache_key(self, image: str) -> str:
        """
        Generate cache key for image.

        Args:
            image: Image name

        Returns:
            Cache key (hex digest)
        """
        # Include config in cache key to invalidate on config changes
        config_str = json.dumps(
            {
                "image": image,
                "scanner": self.config.scanner_type.value,
                "threshold": self.config.severity_threshold.value,
                "ignore_unfixed": self.config.ignore_unfixed,
            },
            sort_keys=True,
        )
        return hashlib.sha256(config_str.encode()).hexdigest()

    def _get_cached_result(self, image: str) -> Optional[ScanResult]:
        """
        Get cached scan result if available and not expired.

        Args:
            image: Image name

        Returns:
            Cached result or None
        """
        if not self.config.enable_cache:
            return None

        cache_key = self._get_cache_key(image)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            if not cache_file.exists():
                return None

            # Check if cache is expired
            cache_age = datetime.now() - datetime.fromtimestamp(
                cache_file.stat().st_mtime
            )
            if cache_age.total_seconds() > self.config.cache_ttl:
                logger.debug(f"Cache expired for {image}")
                cache_file.unlink()
                return None

            # Load cached result
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            result = ScanResult(**data)
            logger.info(f"Using cached result for {image}")
            return result

        except (OSError, json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to load cache: {e}")
            return None

    def _save_to_cache(self, result: ScanResult) -> None:
        """
        Save scan result to cache.

        Args:
            result: Scan result to cache
        """
        if not self.config.enable_cache:
            return

        cache_key = self._get_cache_key(result.image)
        cache_file = self.cache_dir / f"{cache_key}.json"

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(
                    result.model_dump(mode="json"),
                    f,
                    indent=2,
                    default=str,
                )
            logger.debug(f"Saved result to cache: {cache_file}")

        except OSError as e:
            logger.warning(f"Failed to save cache: {e}")

    def _run_trivy_scan(self, image: str) -> Dict[str, Any]:
        """
        Run Trivy vulnerability scan.

        Args:
            image: Image name

        Returns:
            Trivy JSON output

        Raises:
            ScanTimeoutError: If scan times out
            SecurityScanError: For other scan failures
        """
        cmd = [
            "trivy",
            "image",
            "--format",
            "json",
            "--timeout",
            f"{self.config.timeout}s",
        ]

        # Severity filtering
        severities = self._get_severity_list()
        if severities:
            cmd.extend(["--severity", ",".join(severities)])

        # Additional flags
        if self.config.ignore_unfixed:
            cmd.append("--ignore-unfixed")

        if self.config.skip_db_update:
            cmd.append("--skip-db-update")

        if self.config.scan_misconfig:
            cmd.extend(["--scanners", "vuln,config"])
        else:
            cmd.extend(["--scanners", "vuln"])

        if self.config.scan_secrets:
            cmd.extend(["--scanners", "vuln,secret"])

        if self.config.scan_licenses:
            cmd.extend(["--scanners", "vuln,license"])

        cmd.append(image)

        logger.info(f"Running Trivy scan: {image}")
        logger.debug(f"Trivy command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.timeout,
            )

            if result.returncode != 0:
                error_msg = result.stderr.lower()
                if "not found" in error_msg or "manifest unknown" in error_msg:
                    raise ImageNotFoundError(f"Image not found: {image}")
                else:
                    raise SecurityScanError(f"Trivy scan failed: {result.stderr}")

            output = json.loads(result.stdout) if result.stdout else {"Results": []}
            return output

        except subprocess.TimeoutExpired as e:
            raise ScanTimeoutError(
                f"Trivy scan timed out after {self.config.timeout}s"
            ) from e
        except json.JSONDecodeError as e:
            raise SecurityScanError(f"Invalid Trivy JSON output: {e}") from e

    def _run_grype_scan(self, image: str) -> Dict[str, Any]:
        """
        Run Grype vulnerability scan.

        Args:
            image: Image name

        Returns:
            Grype JSON output

        Raises:
            ScanTimeoutError: If scan times out
            SecurityScanError: For other scan failures
        """
        cmd = [
            "grype",
            image,
            "-o",
            "json",
        ]

        logger.info(f"Running Grype scan: {image}")
        logger.debug(f"Grype command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.timeout,
            )

            # Grype returns 1 if vulns found
            if result.returncode not in [0, 1]:
                error_msg = result.stderr.lower()
                if "not found" in error_msg or "failed to load" in error_msg:
                    raise ImageNotFoundError(f"Image not found: {image}")
                else:
                    raise SecurityScanError(f"Grype scan failed: {result.stderr}")

            output = json.loads(result.stdout) if result.stdout else {"matches": []}
            return output

        except subprocess.TimeoutExpired as e:
            raise ScanTimeoutError(
                f"Grype scan timed out after {self.config.timeout}s"
            ) from e
        except json.JSONDecodeError as e:
            raise SecurityScanError(f"Invalid Grype JSON output: {e}") from e

    def _parse_trivy_results(
        self, output: Dict[str, Any], image: str
    ) -> Tuple[List[Vulnerability], List[Misconfiguration], List[SecretFinding]]:
        """
        Parse Trivy scan output.

        Args:
            output: Trivy JSON output
            image: Image name

        Returns:
            Tuple of (vulnerabilities, misconfigurations, secrets)
        """
        vulnerabilities: List[Vulnerability] = []
        misconfigs: List[Misconfiguration] = []
        secrets: List[SecretFinding] = []

        results = output.get("Results", [])

        for result in results:
            target = result.get("Target", "")

            # Parse vulnerabilities
            for vuln_data in result.get("Vulnerabilities", []):
                try:
                    vuln_id = vuln_data.get("VulnerabilityID", "UNKNOWN")

                    # Skip if in ignore list
                    if vuln_id in self.config.ignore_list:
                        logger.debug(f"Ignoring {vuln_id} (in ignore list)")
                        continue

                    severity = SeverityLevel.from_string(
                        vuln_data.get("Severity", "UNKNOWN")
                    )

                    # Parse published date
                    published_date = None
                    if "PublishedDate" in vuln_data:
                        try:
                            pub_date_str = vuln_data["PublishedDate"]
                            pub_date_iso = pub_date_str.replace("Z", "+00:00")
                            published_date = datetime.fromisoformat(pub_date_iso)
                        except (ValueError, AttributeError):
                            pass

                    # Parse CVSS
                    cvss_score = None
                    cvss_vector = None
                    if "CVSS" in vuln_data and vuln_data["CVSS"]:
                        for vendor in ["nvd", "redhat", "vendor"]:
                            if vendor in vuln_data["CVSS"]:
                                cvss_data = vuln_data["CVSS"][vendor]
                                if "V3Score" in cvss_data:
                                    cvss_score = float(cvss_data["V3Score"])
                                    cvss_vector = cvss_data.get("V3Vector")
                                    break

                    vuln = Vulnerability(
                        id=vuln_id,
                        severity=severity,
                        title=vuln_data.get("Title", ""),
                        description=vuln_data.get("Description", ""),
                        package_name=vuln_data.get("PkgName", "unknown"),
                        installed_version=vuln_data.get("InstalledVersion", ""),
                        fixed_version=vuln_data.get("FixedVersion"),
                        cvss_score=cvss_score,
                        cvss_vector=cvss_vector,
                        cwe_ids=vuln_data.get("CweIDs", []),
                        published_date=published_date,
                        references=vuln_data.get("References", []),
                        scanner="trivy",
                    )

                    vulnerabilities.append(vuln)

                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse vulnerability: {e}")
                    continue

            # Parse misconfigurations
            for misconfig_data in result.get("Misconfigurations", []):
                try:
                    severity = SeverityLevel.from_string(
                        misconfig_data.get("Severity", "UNKNOWN")
                    )

                    # Determine misconfiguration type
                    misconfig_type = MisconfigType.DOCKERFILE
                    if "kubernetes" in target.lower():
                        misconfig_type = MisconfigType.KUBERNETES

                    cause_meta = misconfig_data.get("CauseMetadata", {})
                    line_num = cause_meta.get("StartLine")

                    misconfig = Misconfiguration(
                        id=misconfig_data.get("ID", "UNKNOWN"),
                        type=misconfig_type,
                        severity=severity,
                        title=misconfig_data.get("Title", ""),
                        description=misconfig_data.get("Description", ""),
                        file_path=target,
                        line_number=line_num,
                        remediation=misconfig_data.get("Resolution", ""),
                        references=misconfig_data.get("References", []),
                    )

                    misconfigs.append(misconfig)

                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse misconfiguration: {e}")
                    continue

            # Parse secrets
            for secret_data in result.get("Secrets", []):
                try:
                    secret_type = secret_data.get("Category", "generic-secret")
                    secret = SecretFinding(
                        type=secret_type,
                        file_path=target,
                        line_number=secret_data.get("StartLine"),
                        match=secret_data.get("Match", "***REDACTED***"),
                        severity=SeverityLevel.CRITICAL,
                    )

                    secrets.append(secret)

                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse secret: {e}")
                    continue

        return vulnerabilities, misconfigs, secrets

    def _parse_grype_results(
        self, output: Dict[str, Any], image: str
    ) -> List[Vulnerability]:
        """
        Parse Grype scan output.

        Args:
            output: Grype JSON output
            image: Image name

        Returns:
            List of vulnerabilities
        """
        vulnerabilities: List[Vulnerability] = []
        matches = output.get("matches", [])

        for match in matches:
            try:
                vuln_data = match.get("vulnerability", {})
                vuln_id = vuln_data.get("id", "UNKNOWN")

                # Skip if in ignore list
                if vuln_id in self.config.ignore_list:
                    continue

                severity = SeverityLevel.from_string(
                    vuln_data.get("severity", "UNKNOWN")
                )

                artifact = match.get("artifact", {})
                package_name = artifact.get("name", "unknown")
                installed_version = artifact.get("version", "")

                # Parse fix info
                fixed_version = None
                fix_info = match.get("vulnerability", {}).get("fix", {})
                if fix_info and fix_info.get("state") == "fixed":
                    versions = fix_info.get("versions", [])
                    if versions:
                        fixed_version = versions[0]

                # Parse CVSS
                cvss_score = None
                cvss_vector = None
                cvss_list = vuln_data.get("cvss", [])
                if cvss_list:
                    cvss_data = cvss_list[0]
                    if "metrics" in cvss_data:
                        cvss_score = cvss_data["metrics"].get("baseScore")
                    if "vector" in cvss_data:
                        cvss_vector = cvss_data["vector"]

                vuln = Vulnerability(
                    id=vuln_id,
                    severity=severity,
                    title=vuln_data.get("description", "")[:100],
                    description=vuln_data.get("description", ""),
                    package_name=package_name,
                    installed_version=installed_version,
                    fixed_version=fixed_version,
                    cvss_score=cvss_score,
                    cvss_vector=cvss_vector,
                    cwe_ids=[],
                    published_date=None,
                    references=vuln_data.get("urls", []),
                    scanner="grype",
                )

                vulnerabilities.append(vuln)

            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse Grype vulnerability: {e}")
                continue

        return vulnerabilities

    def _get_severity_list(self) -> List[str]:
        """
        Get list of severity levels at or above threshold.

        Returns:
            List of severity strings
        """
        severity_order = [
            SeverityLevel.CRITICAL,
            SeverityLevel.HIGH,
            SeverityLevel.MEDIUM,
            SeverityLevel.LOW,
            SeverityLevel.NEGLIGIBLE,
        ]

        threshold_idx = severity_order.index(self.config.severity_threshold)
        return [s.value for s in severity_order[: threshold_idx + 1]]

    def _aggregate_vulnerabilities(
        self, vuln_lists: List[List[Vulnerability]]
    ) -> List[Vulnerability]:
        """
        Aggregate and deduplicate vulnerabilities from multiple scanners.

        Args:
            vuln_lists: List of vulnerability lists

        Returns:
            Deduplicated vulnerability list
        """
        seen: Dict[str, Vulnerability] = {}

        for vuln_list in vuln_lists:
            for vuln in vuln_list:
                key = f"{vuln.id}:{vuln.package_name}:" f"{vuln.installed_version}"

                if key not in seen:
                    seen[key] = vuln
                else:
                    # Merge information from multiple scanners
                    existing = seen[key]
                    if vuln.cvss_score and not existing.cvss_score:
                        existing.cvss_score = vuln.cvss_score
                    if vuln.fixed_version and not existing.fixed_version:
                        existing.fixed_version = vuln.fixed_version
                    # Combine references
                    combined_refs = existing.references + vuln.references
                    existing.references = list(set(combined_refs))

        return list(seen.values())

    def scan_image(
        self,
        image: str,
        generate_sbom: bool = False,
        sbom_format: SBOMFormat = SBOMFormat.SPDX_JSON,
    ) -> ScanResult:
        """
        Scan Docker image for security issues.

        Args:
            image: Docker image name (e.g., "nginx:latest")
            generate_sbom: Whether to generate SBOM
            sbom_format: SBOM format to use

        Returns:
            Comprehensive scan results

        Raises:
            InvalidImageNameError: If image name is invalid
            ImageNotFoundError: If image cannot be found
            ScanTimeoutError: If scan times out
            SecurityScanError: For other scan failures

        Example:
            >>> scanner = SecurityScanner()
            >>> result = scanner.scan_image("nginx:latest")
            >>> print(result.get_summary())
        """
        self._validate_image_name(image)

        # Check cache first
        cached_result = self._get_cached_result(image)
        if cached_result:
            return cached_result

        vulnerabilities: List[Vulnerability] = []
        misconfigs: List[Misconfiguration] = []
        secrets: List[SecretFinding] = []
        scanner_versions: Dict[str, str] = {}

        # Run scans based on configuration
        if self.config.scanner_type == ScannerType.TRIVY:
            if "trivy" not in self.scanners_available:
                raise ScannerNotFoundError("Trivy not available")

            trivy_output = self._run_trivy_scan(image)
            trivy_vulns, trivy_misconfigs, trivy_secrets = self._parse_trivy_results(
                trivy_output, image
            )
            vulnerabilities.extend(trivy_vulns)
            misconfigs.extend(trivy_misconfigs)
            secrets.extend(trivy_secrets)
            scanner_versions["trivy"] = self._get_scanner_version("trivy")

        elif self.config.scanner_type == ScannerType.GRYPE:
            if "grype" not in self.scanners_available:
                raise ScannerNotFoundError("Grype not available")

            grype_output = self._run_grype_scan(image)
            grype_vulns = self._parse_grype_results(grype_output, image)
            vulnerabilities.extend(grype_vulns)
            scanner_versions["grype"] = self._get_scanner_version("grype")

        elif self.config.scanner_type == ScannerType.BOTH:
            all_vulns = []

            if "trivy" in self.scanners_available:
                trivy_output = self._run_trivy_scan(image)
                trivy_vulns, trivy_misconfigs, trivy_secrets = (
                    self._parse_trivy_results(trivy_output, image)
                )
                all_vulns.append(trivy_vulns)
                misconfigs.extend(trivy_misconfigs)
                secrets.extend(trivy_secrets)
                scanner_versions["trivy"] = self._get_scanner_version("trivy")

            if "grype" in self.scanners_available:
                grype_output = self._run_grype_scan(image)
                grype_vulns = self._parse_grype_results(grype_output, image)
                all_vulns.append(grype_vulns)
                scanner_versions["grype"] = self._get_scanner_version("grype")

            # Aggregate and deduplicate
            vulnerabilities = self._aggregate_vulnerabilities(all_vulns)

        # Generate SBOM if requested
        sbom_data = None
        if generate_sbom and "trivy" in self.scanners_available:
            sbom_data = self.generate_sbom(image, sbom_format)

        # Create result
        result = ScanResult(
            image=image,
            scanner_version=scanner_versions,
            vulnerabilities=vulnerabilities,
            misconfigurations=misconfigs,
            secrets=secrets,
            sbom=sbom_data,
            metadata={
                "config": {
                    "scanner": self.config.scanner_type.value,
                    "threshold": self.config.severity_threshold.value,
                    "ignore_unfixed": self.config.ignore_unfixed,
                },
            },
        )

        # Cache result
        self._save_to_cache(result)

        # Save to output directory if configured
        if self.config.output_dir:
            self._save_result_to_file(result)

        logger.info(
            f"Scan complete: {result.total_vulnerabilities} "
            f"vulnerabilities, {len(misconfigs)} misconfigurations, "
            f"{len(secrets)} secrets"
        )

        return result

    def generate_sbom(self, image: str, format: SBOMFormat) -> Dict[str, Any]:
        """
        Generate Software Bill of Materials.

        Args:
            image: Image name
            format: SBOM format

        Returns:
            SBOM as dictionary

        Raises:
            ScannerNotFoundError: If Trivy not available
            SecurityScanError: If SBOM generation fails
        """
        if "trivy" not in self.scanners_available:
            raise ScannerNotFoundError("Trivy required for SBOM generation")

        cmd = [
            "trivy",
            "image",
            "--format",
            format.value,
            image,
        ]

        logger.info(f"Generating SBOM for {image} in {format.value} format")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=self.config.timeout,
            )

            return json.loads(result.stdout) if result.stdout else {}

        except subprocess.TimeoutExpired as e:
            raise ScanTimeoutError("SBOM generation timed out") from e
        except subprocess.SubprocessError as e:
            raise SecurityScanError(f"SBOM generation failed: {e}") from e
        except json.JSONDecodeError as e:
            raise SecurityScanError(f"Invalid SBOM JSON: {e}") from e

    def update_vulnerability_database(self, scanner: Optional[str] = None) -> None:
        """
        Update vulnerability database for scanner(s).

        Args:
            scanner: Specific scanner to update, or None for all
        """
        scanners_to_update = []

        if scanner:
            if scanner in self.scanners_available:
                scanners_to_update.append(scanner)
            else:
                logger.warning(f"Scanner {scanner} not available")
                return
        else:
            scanners_to_update = list(self.scanners_available)

        for scanner_name in scanners_to_update:
            try:
                if scanner_name == "trivy":
                    logger.info("Updating Trivy database...")
                    subprocess.run(
                        ["trivy", "image", "--download-db-only"],
                        check=True,
                        timeout=300,
                        capture_output=True,
                    )
                    logger.info("Trivy database updated")

                elif scanner_name == "grype":
                    logger.info("Updating Grype database...")
                    subprocess.run(
                        ["grype", "db", "update"],
                        check=True,
                        timeout=300,
                        capture_output=True,
                    )
                    logger.info("Grype database updated")

            except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
                logger.error(f"Failed to update {scanner_name} database: {e}")

    def clear_cache(self) -> int:
        """
        Clear all cached scan results.

        Returns:
            Number of cache files removed
        """
        if not self.config.enable_cache or not self.cache_dir.exists():
            return 0

        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")

        logger.info(f"Cleared {count} cache files")
        return count

    def _save_result_to_file(self, result: ScanResult) -> None:
        """
        Save scan result to output directory.

        Args:
            result: Scan result to save
        """
        if not self.config.output_dir:
            return

        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize image name for filename
        safe_name = result.image.replace("/", "_").replace(":", "_")
        timestamp = result.scan_time.strftime("%Y%m%d_%H%M%S")
        filename = f"scan_{safe_name}_{timestamp}.json"

        output_path = self.config.output_dir / filename

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    result.model_dump(mode="json"),
                    f,
                    indent=2,
                    default=str,
                )
            logger.info(f"Scan result saved to: {output_path}")

        except OSError as e:
            logger.error(f"Failed to save result to file: {e}")
