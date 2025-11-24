"""
Container Scanner Component for Infrastructure Security Scanner Platform.

This module provides comprehensive Docker container security scanning using Trivy,
including CVE detection, vulnerability analysis, and SBOM generation.

Features:
    - CVE detection with NVD and vendor advisories
    - OS and library vulnerability analysis
    - SBOM generation in SPDX and CycloneDX formats
    - Severity filtering (CRITICAL, HIGH, MEDIUM, LOW)
    - Registry authentication support
    - Support for Docker daemon and containerd

Author: devCrew Infrastructure Security Team
License: MIT
"""

import json
import logging
import os
import shutil
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class ContainerScanError(Exception):
    """Base exception for container scanning errors."""

    pass


class TrivyNotFoundError(ContainerScanError):
    """Raised when Trivy is not installed or not found in PATH."""

    pass


class ImageNotFoundError(ContainerScanError):
    """Raised when Docker image cannot be found or pulled."""

    pass


class RegistryAuthError(ContainerScanError):
    """Raised when registry authentication fails."""

    pass


class ScanTimeoutError(ContainerScanError):
    """Raised when scan operation times out."""

    pass


class InvalidImageNameError(ContainerScanError):
    """Raised when image name format is invalid."""

    pass


# ============================================================================
# Enums
# ============================================================================


class SBOMFormat(str, Enum):
    """Supported SBOM formats."""

    SPDX = "spdx"
    SPDX_JSON = "spdx-json"
    CYCLONEDX = "cyclonedx"
    CYCLONEDX_JSON = "cyclonedx-json"


class SeverityLevel(str, Enum):
    """Vulnerability severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


# ============================================================================
# Pydantic Models
# ============================================================================


class RegistryAuth(BaseModel):
    """Registry authentication credentials."""

    username: str = Field(..., description="Registry username")
    password: str = Field(..., description="Registry password")
    registry_url: str = Field(
        default="https://index.docker.io/v1/", description="Registry URL"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Password cannot be empty")
        return v


class ScanConfig(BaseModel):
    """Configuration for container scanning."""

    severity_filter: List[SeverityLevel] = Field(
        default=[
            SeverityLevel.CRITICAL,
            SeverityLevel.HIGH,
            SeverityLevel.MEDIUM,
            SeverityLevel.LOW,
        ],
        description="Severity levels to include in results",
    )
    generate_sbom: bool = Field(default=False, description="Generate SBOM")
    sbom_format: SBOMFormat = Field(
        default=SBOMFormat.SPDX_JSON, description="SBOM format"
    )
    registry_auth: Optional[RegistryAuth] = Field(
        default=None, description="Registry authentication"
    )
    timeout: int = Field(default=600, ge=30, le=3600, description="Scan timeout")
    ignore_unfixed: bool = Field(
        default=False, description="Ignore vulnerabilities without fixes"
    )
    skip_db_update: bool = Field(
        default=False, description="Skip vulnerability database update"
    )
    offline_mode: bool = Field(default=False, description="Run in offline mode")
    output_dir: Optional[Path] = Field(
        default=None, description="Output directory for reports"
    )

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Optional[Path]) -> Optional[Path]:
        """Ensure output directory exists if specified."""
        if v is not None:
            v.mkdir(parents=True, exist_ok=True)
        return v


class Vulnerability(BaseModel):
    """Vulnerability information."""

    cve_id: str = Field(..., description="CVE identifier")
    severity: SeverityLevel = Field(..., description="Vulnerability severity")
    title: str = Field(..., description="Vulnerability title")
    description: str = Field(..., description="Detailed description")
    fixed_version: Optional[str] = Field(default=None, description="Version with fix")
    cvss_score: Optional[float] = Field(
        default=None, ge=0.0, le=10.0, description="CVSS score"
    )
    cwe_ids: List[str] = Field(default_factory=list, description="CWE identifiers")
    published_date: Optional[datetime] = Field(
        default=None, description="Publication date"
    )
    package_name: str = Field(..., description="Affected package name")
    installed_version: str = Field(..., description="Installed package version")
    references: List[str] = Field(default_factory=list, description="Reference URLs")

    @field_validator("cve_id")
    @classmethod
    def validate_cve_id(cls, v: str) -> str:
        """Validate CVE ID format."""
        if not v.startswith("CVE-") and not v.startswith("GHSA-"):
            logger.warning(f"Non-standard CVE ID format: {v}")
        return v


class VulnerabilityResult(BaseModel):
    """Container vulnerability scan results."""

    image: str = Field(..., description="Scanned image name")
    vulnerabilities: List[Vulnerability] = Field(
        default_factory=list, description="Found vulnerabilities"
    )
    total_count: int = Field(default=0, description="Total vulnerabilities")
    critical_count: int = Field(default=0, description="Critical vulnerabilities")
    high_count: int = Field(default=0, description="High vulnerabilities")
    medium_count: int = Field(default=0, description="Medium vulnerabilities")
    low_count: int = Field(default=0, description="Low vulnerabilities")
    unknown_count: int = Field(default=0, description="Unknown vulnerabilities")
    sbom: Optional[str] = Field(default=None, description="Generated SBOM")
    scan_time: datetime = Field(
        default_factory=datetime.utcnow, description="Scan timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    trivy_version: Optional[str] = Field(default=None, description="Trivy version used")

    def get_by_severity(self, severity: SeverityLevel) -> List[Vulnerability]:
        """Get vulnerabilities by severity level."""
        return [v for v in self.vulnerabilities if v.severity == severity]

    def has_critical(self) -> bool:
        """Check if result contains critical vulnerabilities."""
        return self.critical_count > 0

    def get_summary(self) -> Dict[str, int]:
        """Get vulnerability count summary."""
        return {
            "total": self.total_count,
            "critical": self.critical_count,
            "high": self.high_count,
            "medium": self.medium_count,
            "low": self.low_count,
            "unknown": self.unknown_count,
        }


# ============================================================================
# Container Scanner
# ============================================================================


class ContainerScanner:
    """
    Container security scanner using Trivy.

    Provides comprehensive vulnerability scanning for Docker images including
    CVE detection, SBOM generation, and severity-based filtering.

    Attributes:
        config: Scanner configuration
        trivy_path: Path to Trivy executable
    """

    def __init__(self, config: Optional[ScanConfig] = None):
        """
        Initialize container scanner.

        Args:
            config: Scanner configuration. If None, uses defaults.

        Raises:
            TrivyNotFoundError: If Trivy is not installed
        """
        self.config = config or ScanConfig()
        self.trivy_path = self._find_trivy()
        self.trivy_version = self._get_trivy_version()
        logger.info(f"Initialized ContainerScanner with Trivy {self.trivy_version}")

    def _find_trivy(self) -> str:
        """
        Find Trivy executable in system PATH.

        Returns:
            Path to Trivy executable

        Raises:
            TrivyNotFoundError: If Trivy is not found
        """
        trivy_path = shutil.which("trivy")
        if not trivy_path:
            raise TrivyNotFoundError(
                "Trivy not found in PATH. Install from: "
                "https://aquasecurity.github.io/trivy/"
            )
        return trivy_path

    def _get_trivy_version(self) -> str:
        """
        Get installed Trivy version.

        Returns:
            Trivy version string
        """
        try:
            result = subprocess.run(
                [self.trivy_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            # Extract version from output like "Version: 0.48.0"
            for line in result.stdout.split("\n"):
                if "Version:" in line:
                    return line.split("Version:")[1].strip()
            return "unknown"
        except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Could not determine Trivy version: {e}")
            return "unknown"

    @staticmethod
    def check_trivy_installed() -> bool:
        """
        Check if Trivy is installed and available.

        Returns:
            True if Trivy is available, False otherwise
        """
        return shutil.which("trivy") is not None

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

        # Check for invalid characters
        invalid_chars = [" ", "\n", "\t", "\r"]
        if any(char in image for char in invalid_chars):
            raise InvalidImageNameError(
                f"Image name contains invalid characters: {image}"
            )

    def _setup_registry_auth(self) -> Dict[str, str]:
        """
        Setup environment variables for registry authentication.

        Returns:
            Environment variables dictionary
        """
        env = os.environ.copy()

        if self.config.registry_auth:
            auth = self.config.registry_auth
            env["TRIVY_USERNAME"] = auth.username
            env["TRIVY_PASSWORD"] = auth.password

            # Set registry-specific auth if not default Docker Hub
            if auth.registry_url != "https://index.docker.io/v1/":
                env["TRIVY_REGISTRY"] = auth.registry_url

            logger.info(f"Registry authentication configured for {auth.registry_url}")

        return env

    def _build_trivy_args(
        self, image: str, additional_args: Optional[List[str]] = None
    ) -> List[str]:
        """
        Build Trivy command arguments.

        Args:
            image: Image name to scan
            additional_args: Additional arguments to append

        Returns:
            Complete argument list
        """
        args = [
            self.trivy_path,
            "image",
            "--format",
            "json",
            "--timeout",
            str(self.config.timeout),
        ]

        # Severity filtering
        if self.config.severity_filter:
            severities = ",".join([s.value for s in self.config.severity_filter])
            args.extend(["--severity", severities])

        # Ignore unfixed vulnerabilities
        if self.config.ignore_unfixed:
            args.append("--ignore-unfixed")

        # Skip database update
        if self.config.skip_db_update:
            args.append("--skip-db-update")

        # Offline mode
        if self.config.offline_mode:
            args.append("--offline-scan")

        # Add additional arguments
        if additional_args:
            args.extend(additional_args)

        # Image name must be last
        args.append(image)

        return args

    def _run_trivy_scan(
        self, image: str, args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute Trivy scan command.

        Args:
            image: Image name to scan
            args: Additional arguments

        Returns:
            Parsed JSON output from Trivy

        Raises:
            ImageNotFoundError: If image cannot be found
            RegistryAuthError: If authentication fails
            ScanTimeoutError: If scan times out
            ContainerScanError: For other scan failures
        """
        cmd_args = self._build_trivy_args(image, args)
        env = self._setup_registry_auth()

        logger.info(f"Scanning image: {image}")
        logger.debug(f"Trivy command: {' '.join(cmd_args)}")

        try:
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.timeout,
                env=env,
            )

            # Check for specific error conditions
            if result.returncode != 0:
                error_output = result.stderr.lower()

                if "manifest unknown" in error_output or "not found" in error_output:
                    raise ImageNotFoundError(
                        f"Image not found: {image}\n{result.stderr}"
                    )
                elif "unauthorized" in error_output or "authentication" in error_output:
                    raise RegistryAuthError(
                        f"Registry authentication failed: {result.stderr}"
                    )
                else:
                    raise ContainerScanError(
                        f"Trivy scan failed with code {result.returncode}: "
                        f"{result.stderr}"
                    )

            # Parse JSON output
            if not result.stdout or result.stdout.strip() == "":
                logger.warning("Trivy returned empty output")
                return {"Results": []}

            return json.loads(result.stdout)

        except subprocess.TimeoutExpired as e:
            raise ScanTimeoutError(
                f"Scan timed out after {self.config.timeout} seconds"
            ) from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Trivy output: {result.stdout[:200]}")
            raise ContainerScanError(f"Invalid JSON output from Trivy: {e}") from e

    def _parse_trivy_output(
        self, output: Dict[str, Any], image: str
    ) -> VulnerabilityResult:
        """
        Parse Trivy JSON output into VulnerabilityResult.

        Args:
            output: Trivy JSON output
            image: Image name

        Returns:
            Parsed vulnerability result
        """
        vulnerabilities: List[Vulnerability] = []
        counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "unknown": 0,
        }

        # Trivy output structure: {"Results": [{"Target": "", "Vulnerabilities": []}]}
        results = output.get("Results", [])

        for result in results:
            # Target field available but not currently used in parsing
            # target = result.get("Target", "unknown")
            vulns = result.get("Vulnerabilities", [])

            for vuln_data in vulns:
                try:
                    # Parse severity
                    severity_str = vuln_data.get("Severity", "UNKNOWN").upper()
                    try:
                        severity = SeverityLevel(severity_str)
                    except ValueError:
                        severity = SeverityLevel.UNKNOWN

                    # Parse published date
                    published_date = None
                    if "PublishedDate" in vuln_data:
                        try:
                            published_date = datetime.fromisoformat(
                                vuln_data["PublishedDate"].replace("Z", "+00:00")
                            )
                        except (ValueError, AttributeError):
                            pass

                    # Parse CVSS score
                    cvss_score = None
                    if "CVSS" in vuln_data and vuln_data["CVSS"]:
                        # Try to get score from various CVSS versions
                        for cvss_key in ["nvd", "redhat", "vendor"]:
                            if cvss_key in vuln_data["CVSS"]:
                                cvss_data = vuln_data["CVSS"][cvss_key]
                                if "V3Score" in cvss_data:
                                    cvss_score = float(cvss_data["V3Score"])
                                    break
                                elif "V2Score" in cvss_data:
                                    cvss_score = float(cvss_data["V2Score"])
                                    break

                    vulnerability = Vulnerability(
                        cve_id=vuln_data.get("VulnerabilityID", "UNKNOWN"),
                        severity=severity,
                        title=vuln_data.get("Title", "No title available"),
                        description=vuln_data.get(
                            "Description", "No description available"
                        ),
                        fixed_version=vuln_data.get("FixedVersion"),
                        cvss_score=cvss_score,
                        cwe_ids=vuln_data.get("CweIDs", []),
                        published_date=published_date,
                        package_name=vuln_data.get("PkgName", "unknown"),
                        installed_version=vuln_data.get("InstalledVersion", "unknown"),
                        references=vuln_data.get("References", []),
                    )

                    vulnerabilities.append(vulnerability)

                    # Update counts
                    if severity == SeverityLevel.CRITICAL:
                        counts["critical"] += 1
                    elif severity == SeverityLevel.HIGH:
                        counts["high"] += 1
                    elif severity == SeverityLevel.MEDIUM:
                        counts["medium"] += 1
                    elif severity == SeverityLevel.LOW:
                        counts["low"] += 1
                    else:
                        counts["unknown"] += 1

                except (KeyError, ValueError) as e:
                    logger.warning(
                        f"Failed to parse vulnerability: {e} - Data: {vuln_data}"
                    )
                    continue

        # Extract metadata
        metadata = {
            "trivy_version": self.trivy_version,
            "scan_config": {
                "severity_filter": [s.value for s in self.config.severity_filter],
                "ignore_unfixed": self.config.ignore_unfixed,
                "offline_mode": self.config.offline_mode,
            },
        }

        if "Metadata" in output:
            metadata["trivy_metadata"] = output["Metadata"]

        result = VulnerabilityResult(
            image=image,
            vulnerabilities=vulnerabilities,
            total_count=len(vulnerabilities),
            critical_count=counts["critical"],
            high_count=counts["high"],
            medium_count=counts["medium"],
            low_count=counts["low"],
            unknown_count=counts["unknown"],
            metadata=metadata,
            trivy_version=self.trivy_version,
        )

        return result

    def scan_image(self, image: str) -> VulnerabilityResult:
        """
        Scan Docker image for vulnerabilities.

        Args:
            image: Docker image name (e.g., "nginx:latest", "ubuntu:20.04")

        Returns:
            Vulnerability scan results

        Raises:
            InvalidImageNameError: If image name is invalid
            ImageNotFoundError: If image cannot be found
            RegistryAuthError: If authentication fails
            ScanTimeoutError: If scan times out
            ContainerScanError: For other scan failures

        Example:
            >>> scanner = ContainerScanner()
            >>> result = scanner.scan_image("nginx:latest")
            >>> print(f"Found {result.total_count} vulnerabilities")
            >>> print(f"Critical: {result.critical_count}")
        """
        self._validate_image_name(image)

        try:
            output = self._run_trivy_scan(image)
            result = self._parse_trivy_output(output, image)

            logger.info(
                f"Scan completed: {result.total_count} vulnerabilities found "
                f"(Critical: {result.critical_count}, High: {result.high_count})"
            )

            # Save results if output directory specified
            if self.config.output_dir:
                self._save_results(result)

            return result

        except (
            ImageNotFoundError,
            RegistryAuthError,
            ScanTimeoutError,
            InvalidImageNameError,
        ):
            raise
        except Exception as e:
            logger.error(f"Unexpected error during scan: {e}")
            raise ContainerScanError(f"Scan failed: {e}") from e

    def scan_image_file(self, image_file: Path) -> VulnerabilityResult:
        """
        Scan Docker image from tar file.

        Args:
            image_file: Path to image tar file

        Returns:
            Vulnerability scan results

        Raises:
            FileNotFoundError: If image file does not exist
            ContainerScanError: For scan failures

        Example:
            >>> scanner = ContainerScanner()
            >>> result = scanner.scan_image_file(Path("nginx.tar"))
            >>> print(f"Found {result.total_count} vulnerabilities")
        """
        if not image_file.exists():
            raise FileNotFoundError(f"Image file not found: {image_file}")

        if not image_file.is_file():
            raise ContainerScanError(f"Not a file: {image_file}")

        logger.info(f"Scanning image file: {image_file}")

        try:
            args = ["--input", str(image_file)]
            output = self._run_trivy_scan(str(image_file), args)
            result = self._parse_trivy_output(output, str(image_file))

            logger.info(f"File scan completed: {result.total_count} vulnerabilities")

            if self.config.output_dir:
                self._save_results(result)

            return result

        except Exception as e:
            logger.error(f"Failed to scan image file: {e}")
            raise ContainerScanError(f"File scan failed: {e}") from e

    def generate_sbom(self, image: str, format: SBOMFormat) -> str:
        """
        Generate Software Bill of Materials (SBOM) for image.

        Args:
            image: Docker image name
            format: SBOM format (SPDX or CycloneDX)

        Returns:
            SBOM content as string

        Raises:
            InvalidImageNameError: If image name is invalid
            ImageNotFoundError: If image cannot be found
            ContainerScanError: For generation failures

        Example:
            >>> scanner = ContainerScanner()
            >>> sbom = scanner.generate_sbom("nginx:latest", SBOMFormat.SPDX_JSON)
            >>> with open("sbom.json", "w") as f:
            ...     f.write(sbom)
        """
        self._validate_image_name(image)

        logger.info(f"Generating {format.value} SBOM for {image}")

        try:
            args = [
                self.trivy_path,
                "image",
                "--format",
                format.value,
                "--timeout",
                str(self.config.timeout),
            ]

            if self.config.skip_db_update:
                args.append("--skip-db-update")

            if self.config.offline_mode:
                args.append("--offline-scan")

            args.append(image)

            env = self._setup_registry_auth()

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.timeout,
                env=env,
            )

            if result.returncode != 0:
                raise ContainerScanError(f"SBOM generation failed: {result.stderr}")

            logger.info(f"SBOM generated successfully ({len(result.stdout)} bytes)")

            # Save SBOM if output directory specified
            if self.config.output_dir:
                self._save_sbom(image, format, result.stdout)

            return result.stdout

        except subprocess.TimeoutExpired as e:
            raise ScanTimeoutError(
                f"SBOM generation timed out after {self.config.timeout} seconds"
            ) from e
        except Exception as e:
            logger.error(f"SBOM generation failed: {e}")
            raise ContainerScanError(f"SBOM generation failed: {e}") from e

    def filter_by_severity(
        self, vulns: List[Vulnerability], levels: List[SeverityLevel]
    ) -> List[Vulnerability]:
        """
        Filter vulnerabilities by severity levels.

        Args:
            vulns: List of vulnerabilities
            levels: Severity levels to include

        Returns:
            Filtered vulnerability list

        Example:
            >>> scanner = ContainerScanner()
            >>> result = scanner.scan_image("nginx:latest")
            >>> critical_high = scanner.filter_by_severity(
            ...     result.vulnerabilities,
            ...     [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
            ... )
            >>> print(f"Found {len(critical_high)} critical/high vulnerabilities")
        """
        return [v for v in vulns if v.severity in levels]

    def get_unfixed_vulnerabilities(
        self, result: VulnerabilityResult
    ) -> List[Vulnerability]:
        """
        Get vulnerabilities without available fixes.

        Args:
            result: Vulnerability scan result

        Returns:
            List of unfixed vulnerabilities
        """
        return [v for v in result.vulnerabilities if v.fixed_version is None]

    def get_fixable_vulnerabilities(
        self, result: VulnerabilityResult
    ) -> List[Vulnerability]:
        """
        Get vulnerabilities with available fixes.

        Args:
            result: Vulnerability scan result

        Returns:
            List of fixable vulnerabilities
        """
        return [v for v in result.vulnerabilities if v.fixed_version is not None]

    def _save_results(self, result: VulnerabilityResult) -> None:
        """
        Save scan results to output directory.

        Args:
            result: Vulnerability scan result
        """
        if not self.config.output_dir:
            return

        # Sanitize image name for filename
        safe_name = result.image.replace("/", "_").replace(":", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON results
        json_file = self.config.output_dir / f"scan_{safe_name}_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2, default=str)

        logger.info(f"Results saved to {json_file}")

    def _save_sbom(self, image: str, format: SBOMFormat, sbom: str) -> None:
        """
        Save SBOM to output directory.

        Args:
            image: Image name
            format: SBOM format
            sbom: SBOM content
        """
        if not self.config.output_dir:
            return

        safe_name = image.replace("/", "_").replace(":", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        extension = "json" if "json" in format.value else "xml"
        sbom_file = (
            self.config.output_dir
            / f"sbom_{safe_name}_{format.value}_{timestamp}.{extension}"
        )

        with open(sbom_file, "w", encoding="utf-8") as f:
            f.write(sbom)

        logger.info(f"SBOM saved to {sbom_file}")


# ============================================================================
# Utility Functions
# ============================================================================


def scan_images_batch(
    images: List[str], config: Optional[ScanConfig] = None
) -> Dict[str, VulnerabilityResult]:
    """
    Scan multiple images in batch.

    Args:
        images: List of image names
        config: Scanner configuration

    Returns:
        Dictionary mapping image names to results

    Example:
        >>> images = ["nginx:latest", "ubuntu:20.04", "redis:alpine"]
        >>> results = scan_images_batch(images)
        >>> for image, result in results.items():
        ...     print(f"{image}: {result.critical_count} critical")
    """
    scanner = ContainerScanner(config)
    results = {}

    for image in images:
        try:
            logger.info(f"Scanning {image} ({images.index(image) + 1}/{len(images)})")
            results[image] = scanner.scan_image(image)
        except ContainerScanError as e:
            logger.error(f"Failed to scan {image}: {e}")
            continue

    return results


def compare_scans(
    result1: VulnerabilityResult, result2: VulnerabilityResult
) -> Tuple[List[Vulnerability], List[Vulnerability], List[Vulnerability]]:
    """
    Compare two scan results to find new, fixed, and persistent vulnerabilities.

    Args:
        result1: First scan result (older)
        result2: Second scan result (newer)

    Returns:
        Tuple of (new, fixed, persistent) vulnerabilities

    Example:
        >>> old_scan = scanner.scan_image("nginx:1.20")
        >>> new_scan = scanner.scan_image("nginx:1.21")
        >>> new, fixed, persistent = compare_scans(old_scan, new_scan)
        >>> print(f"New: {len(new)}, Fixed: {len(fixed)}, "
        ...       f"Persistent: {len(persistent)}")
    """
    # Create sets of CVE IDs
    cves1 = {v.cve_id for v in result1.vulnerabilities}
    cves2 = {v.cve_id for v in result2.vulnerabilities}

    # Find differences
    new_cves = cves2 - cves1
    fixed_cves = cves1 - cves2
    persistent_cves = cves1 & cves2

    # Get vulnerability objects
    new_vulns = [v for v in result2.vulnerabilities if v.cve_id in new_cves]
    fixed_vulns = [v for v in result1.vulnerabilities if v.cve_id in fixed_cves]
    persistent_vulns = [
        v for v in result2.vulnerabilities if v.cve_id in persistent_cves
    ]

    return new_vulns, fixed_vulns, persistent_vulns


def export_to_sarif(result: VulnerabilityResult, output_file: Path) -> None:
    """
    Export scan results to SARIF format.

    Args:
        result: Vulnerability scan result
        output_file: Output file path

    Example:
        >>> result = scanner.scan_image("nginx:latest")
        >>> export_to_sarif(result, Path("results.sarif"))
    """
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/"
        "master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Trivy",
                        "version": result.trivy_version or "unknown",
                        "informationUri": "https://aquasecurity.github.io/trivy/",
                    }
                },
                "results": [
                    {
                        "ruleId": vuln.cve_id,
                        "level": _severity_to_sarif_level(vuln.severity),
                        "message": {"text": vuln.description},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": result.image},
                                    "region": {
                                        "snippet": {
                                            "text": f"{vuln.package_name}@"
                                            f"{vuln.installed_version}"
                                        }
                                    },
                                }
                            }
                        ],
                        "properties": {
                            "severity": vuln.severity.value,
                            "cvss_score": vuln.cvss_score,
                            "fixed_version": vuln.fixed_version,
                        },
                    }
                    for vuln in result.vulnerabilities
                ],
            }
        ],
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sarif, f, indent=2)

    logger.info(f"SARIF report exported to {output_file}")


def _severity_to_sarif_level(severity: SeverityLevel) -> str:
    """Convert severity level to SARIF level."""
    mapping = {
        SeverityLevel.CRITICAL: "error",
        SeverityLevel.HIGH: "error",
        SeverityLevel.MEDIUM: "warning",
        SeverityLevel.LOW: "note",
        SeverityLevel.UNKNOWN: "none",
    }
    return mapping.get(severity, "none")


# ============================================================================
# CLI Interface (optional usage)
# ============================================================================


def main() -> None:
    """CLI entry point for container scanner."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python container_scanner.py <image_name>")
        print("Example: python container_scanner.py nginx:latest")
        sys.exit(1)

    image = sys.argv[1]

    try:
        scanner = ContainerScanner()
        result = scanner.scan_image(image)

        print(f"\n{'=' * 70}")
        print(f"Scan Results for: {result.image}")
        print(f"{'=' * 70}")
        print(f"Total Vulnerabilities: {result.total_count}")
        print(f"  Critical: {result.critical_count}")
        print(f"  High:     {result.high_count}")
        print(f"  Medium:   {result.medium_count}")
        print(f"  Low:      {result.low_count}")
        print(f"{'=' * 70}\n")

        if result.critical_count > 0:
            print("Critical Vulnerabilities:")
            for vuln in result.get_by_severity(SeverityLevel.CRITICAL):
                print(f"  - {vuln.cve_id}: {vuln.title}")
                print(f"    Package: {vuln.package_name} ({vuln.installed_version})")
                if vuln.fixed_version:
                    print(f"    Fixed in: {vuln.fixed_version}")
                print()

    except ContainerScanError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
