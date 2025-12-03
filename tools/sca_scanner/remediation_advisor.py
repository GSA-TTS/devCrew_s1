"""
Remediation Advisor Module for SCA Scanner

Provides upgrade recommendations, breaking change detection, and alternative
package suggestions for vulnerable dependencies.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import requests
from packaging import version
from packaging.version import parse as parse_version

logger = logging.getLogger(__name__)


class UpgradeType(Enum):
    """Types of version upgrades."""

    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"
    UNKNOWN = "unknown"


class Confidence(Enum):
    """Confidence levels for recommendations."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MigrationEffort(Enum):
    """Estimated effort for package migration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Alternative:
    """Alternative package suggestion."""

    package: str
    reason: str
    migration_effort: str
    ecosystem: Optional[str] = None
    latest_version: Optional[str] = None


@dataclass
class BreakingChange:
    """Details about a breaking change."""

    type: str
    description: str
    affected_apis: List[str] = field(default_factory=list)
    migration_guide: Optional[str] = None


@dataclass
class Remediation:
    """Complete remediation recommendation."""

    package: str
    current_version: str
    vulnerability: str
    severity: str
    recommended_version: Optional[str]
    upgrade_type: str
    breaking_changes: bool
    breaking_change_details: List[Dict[str, Any]]
    alternatives: List[Dict[str, Any]]
    priority_score: int
    action: str
    confidence: str
    patch_available: bool = False
    ecosystem: str = "pypi"
    cvss_score: Optional[float] = None
    exploitability: Optional[str] = None
    is_direct: bool = True


class RemediationAdvisor:
    """
    Provides remediation advice for vulnerable dependencies.

    This class analyzes vulnerabilities and provides recommendations
    including upgrade paths, breaking changes, and alternative packages.
    """

    def __init__(
        self,
        cache_enabled: bool = True,
        api_timeout: int = 10,
        custom_alternatives: Optional[Dict[str, List[Dict[str, str]]]] = None,
    ):
        """
        Initialize RemediationAdvisor.

        Args:
            cache_enabled: Enable local caching of package metadata
            api_timeout: Timeout for API requests in seconds
            custom_alternatives: Custom alternative package mappings
        """
        self.cache_enabled = cache_enabled
        self.api_timeout = api_timeout
        self.custom_alternatives = custom_alternatives or {}
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}
        self._changelog_cache: Dict[str, str] = {}

        # Known breaking change patterns by major version bumps
        self.breaking_patterns = {
            "python": [
                r"removed.*deprecated",
                r"breaking.*change",
                r"incompatible",
                r"no longer support",
                r"dropped support for",
            ]
        }

        # Known package alternatives
        self.alternative_packages = {
            "requests": [
                {
                    "package": "httpx",
                    "reason": "Modern async support, HTTP/2",
                    "migration_effort": "medium",
                },
                {
                    "package": "aiohttp",
                    "reason": "Async-first design",
                    "migration_effort": "high",
                },
            ],
            "urllib3": [
                {
                    "package": "httpx",
                    "reason": "Higher-level API, better security defaults",
                    "migration_effort": "medium",
                }
            ],
            "pyyaml": [
                {
                    "package": "ruamel.yaml",
                    "reason": "Better YAML 1.2 support, preserves comments",
                    "migration_effort": "low",
                }
            ],
            "cryptography": [
                {
                    "package": "pynacl",
                    "reason": "Simpler API for common use cases",
                    "migration_effort": "medium",
                }
            ],
        }

        # Update with custom alternatives
        if self.custom_alternatives:
            self.alternative_packages.update(self.custom_alternatives)

    def get_remediation(
        self,
        vulnerability: Dict[str, Any],
        dependency: Dict[str, Any],
        ecosystem: str = "pypi",
    ) -> Dict[str, Any]:
        """
        Get complete remediation recommendation for a vulnerability.

        Args:
            vulnerability: Vulnerability details including CVE, severity, CVSS
            dependency: Dependency details including name, version
            ecosystem: Package ecosystem (pypi, npm, maven, etc.)

        Returns:
            Complete remediation recommendation dictionary
        """
        package_name = dependency.get("name", "")
        current_version = dependency.get("version", "")
        vuln_id = vulnerability.get("id", "UNKNOWN")
        severity = vulnerability.get("severity", "UNKNOWN")
        cvss_score = vulnerability.get("cvss_score")
        exploitability = vulnerability.get("exploitability")
        is_direct = dependency.get("is_direct", True)

        logger.info(
            f"Generating remediation for {package_name}@{current_version} "
            f"({vuln_id})"
        )

        # Get fixed version from vulnerability data
        fixed_in = vulnerability.get("fixed_in", [])
        recommended_version = self._select_recommended_version(
            current_version, fixed_in
        )

        # Calculate upgrade path
        upgrade_type = UpgradeType.UNKNOWN.value
        if recommended_version:
            upgrade_type = self.detect_breaking_changes(
                current_version, recommended_version
            )[0].value

        # Check for breaking changes
        breaking_changes = False
        breaking_details = []
        if recommended_version:
            _, breaking_changes_list = self.detect_breaking_changes(
                current_version, recommended_version, package_name
            )
            breaking_changes = len(breaking_changes_list) > 0
            breaking_details = [
                {
                    "type": bc.type,
                    "description": bc.description,
                    "affected_apis": bc.affected_apis,
                    "migration_guide": bc.migration_guide,
                }
                for bc in breaking_changes_list
            ]

        # Check patch availability
        patch_available = self.check_patch_available(
            package_name, current_version, fixed_in, ecosystem
        )

        # Find alternatives
        alternatives_list = self.find_alternatives(package_name, ecosystem)
        alternatives = [
            {
                "package": alt.package,
                "reason": alt.reason,
                "migration_effort": alt.migration_effort,
                "latest_version": alt.latest_version,
            }
            for alt in alternatives_list
        ]

        # Build remediation object
        remediation = Remediation(
            package=package_name,
            current_version=current_version,
            vulnerability=vuln_id,
            severity=severity,
            recommended_version=recommended_version,
            upgrade_type=upgrade_type,
            breaking_changes=breaking_changes,
            breaking_change_details=breaking_details,
            alternatives=alternatives,
            priority_score=0,  # Will be calculated
            action="",  # Will be set based on recommendation
            confidence=Confidence.HIGH.value,
            patch_available=patch_available,
            ecosystem=ecosystem,
            cvss_score=cvss_score,
            exploitability=exploitability,
            is_direct=is_direct,
        )

        # Calculate priority score
        priority_score = self._calculate_priority_score(remediation)
        remediation.priority_score = priority_score

        # Generate action recommendation
        remediation.action = self._generate_action(remediation)

        # Set confidence level
        remediation.confidence = self._determine_confidence(remediation).value

        return self._remediation_to_dict(remediation)

    def calculate_upgrade_path(
        self, current: str, fixed_in: List[str]
    ) -> Optional[str]:
        """
        Calculate the best upgrade path from current version to fixed version.

        Args:
            current: Current version string
            fixed_in: List of versions that fix the vulnerability

        Returns:
            Recommended version to upgrade to, or None if no path found
        """
        if not fixed_in:
            return None

        try:
            current_ver = parse_version(current)
        except Exception as e:
            logger.warning(f"Failed to parse current version '{current}': {e}")
            return None

        # Parse and filter valid fixed versions
        valid_fixed = []
        for ver_str in fixed_in:
            try:
                ver = parse_version(ver_str)
                if ver > current_ver:
                    valid_fixed.append((ver_str, ver))
            except Exception as e:
                msg = f"Failed to parse fixed version '{ver_str}': {e}"
                logger.warning(msg)
                continue

        if not valid_fixed:
            return None

        # Sort by version (ascending)
        valid_fixed.sort(key=lambda x: x[1])

        # Prefer the smallest version bump that fixes the issue
        for ver_str, ver in valid_fixed:
            return ver_str

        return None

    def detect_breaking_changes(
        self,
        current: str,
        target: str,
        package_name: Optional[str] = None,
    ) -> Tuple[UpgradeType, List[BreakingChange]]:
        """
        Detect breaking changes between two versions using semver analysis.

        Args:
            current: Current version string
            target: Target version string
            package_name: Optional package name for changelog lookup

        Returns:
            Tuple of (upgrade_type, list of breaking changes)
        """
        breaking_changes: List[BreakingChange] = []

        try:
            current_ver = parse_version(current)
            target_ver = parse_version(target)
        except Exception as e:
            logger.warning(f"Failed to parse versions: {e}")
            return UpgradeType.UNKNOWN, breaking_changes

        # Determine upgrade type based on semver
        upgrade_type = self._classify_upgrade_type(current_ver, target_ver)

        # Major version bumps likely have breaking changes
        if upgrade_type == UpgradeType.MAJOR:
            breaking_changes.append(
                BreakingChange(
                    type="major_version_bump",
                    description=(
                        f"Major version upgrade from {current} to {target} "
                        "may contain breaking changes"
                    ),
                    affected_apis=[],
                    migration_guide=None,
                )
            )

            # Try to fetch and analyze changelog if package name provided
            if package_name:
                changelog_breaks = self._analyze_changelog(
                    package_name, current, target
                )
                breaking_changes.extend(changelog_breaks)

        return upgrade_type, breaking_changes

    def find_alternatives(
        self, package: str, ecosystem: str = "pypi"
    ) -> List[Alternative]:
        """
        Find alternative packages that could replace the vulnerable package.

        Args:
            package: Package name
            ecosystem: Package ecosystem

        Returns:
            List of alternative package suggestions
        """
        alternatives = []

        # Check known alternatives
        if package.lower() in self.alternative_packages:
            alt_data = self.alternative_packages[package.lower()]
            for alt in alt_data:
                pkg_name = alt["package"]
                latest_ver = self._get_latest_version(pkg_name, ecosystem)
                alternatives.append(
                    Alternative(
                        package=alt["package"],
                        reason=alt["reason"],
                        migration_effort=alt["migration_effort"],
                        ecosystem=ecosystem,
                        latest_version=latest_ver,
                    )
                )

        return alternatives

    def prioritize(
        self, vulnerabilities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize vulnerabilities by calculating priority scores.

        Args:
            vulnerabilities: List of vulnerability findings

        Returns:
            Sorted list of vulnerabilities by priority (highest first)
        """
        scored_vulns = []

        for vuln in vulnerabilities:
            dependency = vuln.get("dependency", {})
            vulnerability = vuln.get("vulnerability", {})

            remediation = self.get_remediation(vulnerability, dependency)
            scored_vulns.append(
                {
                    **vuln,
                    "priority_score": remediation["priority_score"],
                    "remediation": remediation,
                }
            )

        # Sort by priority score (descending)
        scored_vulns.sort(key=lambda x: x["priority_score"], reverse=True)

        return scored_vulns

    def check_patch_available(
        self,
        package: str,
        version: str,
        fixed_in: List[str],
        ecosystem: str = "pypi",
    ) -> bool:
        """
        Check if a patch is available for the vulnerability.

        Args:
            package: Package name
            version: Current version
            fixed_in: List of versions with fix
            ecosystem: Package ecosystem

        Returns:
            True if patch is available, False otherwise
        """
        if not fixed_in:
            return False

        try:
            current_ver = parse_version(version)

            for fixed_ver_str in fixed_in:
                try:
                    fixed_ver = parse_version(fixed_ver_str)
                    if fixed_ver > current_ver:
                        # Check if version exists
                        version_exists = self._version_exists(
                            package, fixed_ver_str, ecosystem
                        )
                        if version_exists:
                            return True
                except Exception:
                    continue

        except Exception as e:
            msg = f"Failed to check patch availability for {package}: {e}"
            logger.warning(msg)

        return False

    # Private helper methods

    def _select_recommended_version(
        self, current: str, fixed_in: List[str]
    ) -> Optional[str]:
        """Select the best recommended version to upgrade to."""
        return self.calculate_upgrade_path(current, fixed_in)

    def _calculate_priority_score(self, remediation: Remediation) -> int:
        """
        Calculate priority score based on multiple factors.

        Scoring factors:
        - CVSS score (40%)
        - Exploitability (30%)
        - Direct vs transitive (20%)
        - Patch availability (10%)
        """
        score = 0.0

        # CVSS score contribution (40%)
        if remediation.cvss_score is not None:
            cvss_normalized = min(remediation.cvss_score / 10.0, 1.0)
            score += cvss_normalized * 40.0
        else:
            # Use severity as fallback
            severity_scores = {
                "CRITICAL": 1.0,
                "HIGH": 0.8,
                "MEDIUM": 0.5,
                "LOW": 0.2,
            }
            sev_key = remediation.severity.upper()
            severity_score = severity_scores.get(sev_key, 0.5)
            score += severity_score * 40.0

        # Exploitability contribution (30%)
        if remediation.exploitability:
            exploit_scores = {
                "ACTIVE": 1.0,
                "POC": 0.8,
                "FUNCTIONAL": 0.8,
                "HIGH": 0.7,
                "MEDIUM": 0.5,
                "LOW": 0.3,
                "UNPROVEN": 0.1,
            }
            exploit_key = remediation.exploitability.upper()
            exploit_score = exploit_scores.get(exploit_key, 0.5)
            score += exploit_score * 30.0
        else:
            score += 0.5 * 30.0  # Default medium

        # Direct vs transitive contribution (20%)
        if remediation.is_direct:
            score += 20.0
        else:
            score += 10.0  # Transitive gets half weight

        # Patch availability contribution (10%)
        if remediation.patch_available:
            score += 10.0
        else:
            score += 0.0

        return int(min(score, 100))

    def _generate_action(self, remediation: Remediation) -> str:
        """Generate actionable recommendation text."""
        if not remediation.recommended_version:
            if remediation.alternatives:
                return (
                    f"No fix available. Consider migrating to "
                    f"{remediation.alternatives[0]['package']}"
                )
            return (
                "No fix available. Monitor for updates or "
                "consider alternative packages"
            )

        urgency = "immediately" if remediation.priority_score >= 80 else "soon"

        if remediation.breaking_changes:
            return (
                f"Upgrade to {remediation.recommended_version} {urgency}. "
                "Review breaking changes before upgrading"
            )

        return f"Upgrade to {remediation.recommended_version} {urgency}"

    def _determine_confidence(self, remediation: Remediation) -> Confidence:
        """Determine confidence level for the recommendation."""
        if not remediation.recommended_version:
            return Confidence.LOW

        if remediation.breaking_changes:
            return Confidence.MEDIUM

        upgrade_type = remediation.upgrade_type
        if upgrade_type == UpgradeType.PATCH.value:
            return Confidence.HIGH

        if upgrade_type == UpgradeType.MINOR.value:
            return Confidence.HIGH

        if upgrade_type == UpgradeType.MAJOR.value:
            return Confidence.MEDIUM

        return Confidence.MEDIUM

    def _classify_upgrade_type(
        self, current: version.Version, target: version.Version
    ) -> UpgradeType:
        """Classify the type of version upgrade."""
        # Handle pre-release and dev versions
        default_release = (0, 0, 0)
        current_release = (
            current.release if hasattr(current, "release") else default_release
        )
        target_release = (
            target.release if hasattr(target, "release") else default_release
        )

        # Ensure we have at least 3 components
        curr_len = len(current_release)
        current_parts = list(current_release) + [0] * (3 - curr_len)
        tgt_len = len(target_release)
        target_parts = list(target_release) + [0] * (3 - tgt_len)

        if current_parts[0] != target_parts[0]:
            return UpgradeType.MAJOR
        elif current_parts[1] != target_parts[1]:
            return UpgradeType.MINOR
        elif current_parts[2] != target_parts[2]:
            return UpgradeType.PATCH
        else:
            return UpgradeType.PATCH  # Default for any other differences

    def _analyze_changelog(
        self, package: str, current: str, target: str
    ) -> List[BreakingChange]:
        """Analyze package changelog for breaking changes."""
        breaking_changes: List[BreakingChange] = []

        # Try to fetch changelog from cache or API
        changelog = self._get_changelog(package)
        if not changelog:
            return breaking_changes

        # Look for breaking change patterns
        for pattern in self.breaking_patterns.get("python", []):
            flags = re.IGNORECASE | re.MULTILINE
            matches = re.finditer(pattern, changelog, flags)
            for match in matches:
                # Extract context around the match
                start = max(0, match.start() - 100)
                end = min(len(changelog), match.end() + 100)
                context = changelog[start:end].strip()

                breaking_changes.append(
                    BreakingChange(
                        type="changelog_indicator",
                        description=context,
                        affected_apis=[],
                        migration_guide=None,
                    )
                )

        return breaking_changes[:3]  # Limit to first 3 findings

    def _get_changelog(self, package: str) -> Optional[str]:
        """Fetch package changelog from cache or API."""
        if package in self._changelog_cache:
            return self._changelog_cache[package]

        # Try to fetch from PyPI
        try:
            metadata = self._get_package_metadata(package)
            if metadata and "info" in metadata:
                description = metadata["info"].get("description", "")
                # Cache it
                self._changelog_cache[package] = description
                return description
        except Exception as e:
            logger.debug(f"Failed to fetch changelog for {package}: {e}")

        return None

    def _get_package_metadata(
        self, package: str, ecosystem: str = "pypi"
    ) -> Optional[Dict[str, Any]]:
        """Fetch package metadata from registry."""
        cache_key = f"{ecosystem}:{package}"

        if self.cache_enabled and cache_key in self._metadata_cache:
            return self._metadata_cache[cache_key]

        if ecosystem == "pypi":
            url = f"https://pypi.org/pypi/{package}/json"
            try:
                response = requests.get(url, timeout=self.api_timeout)
                if response.status_code == 200:
                    metadata = response.json()
                    if self.cache_enabled:
                        self._metadata_cache[cache_key] = metadata
                    return metadata
            except Exception as e:
                logger.debug(f"Failed to fetch metadata for {package}: {e}")

        return None

    def _get_latest_version(
        self, package: str, ecosystem: str = "pypi"
    ) -> Optional[str]:
        """Get the latest version of a package."""
        metadata = self._get_package_metadata(package, ecosystem)
        if metadata and "info" in metadata:
            return metadata["info"].get("version")
        return None

    def _version_exists(
        self, package: str, version_str: str, ecosystem: str = "pypi"
    ) -> bool:
        """Check if a specific version exists in the registry."""
        metadata = self._get_package_metadata(package, ecosystem)
        if metadata and "releases" in metadata:
            return version_str in metadata["releases"]
        return False

    def _remediation_to_dict(self, remediation: Remediation) -> Dict[str, Any]:
        """Convert Remediation object to dictionary."""
        return {
            "package": remediation.package,
            "current_version": remediation.current_version,
            "vulnerability": remediation.vulnerability,
            "severity": remediation.severity,
            "recommended_version": remediation.recommended_version,
            "upgrade_type": remediation.upgrade_type,
            "breaking_changes": remediation.breaking_changes,
            "breaking_change_details": remediation.breaking_change_details,
            "alternatives": remediation.alternatives,
            "priority_score": remediation.priority_score,
            "action": remediation.action,
            "confidence": remediation.confidence,
            "patch_available": remediation.patch_available,
            "ecosystem": remediation.ecosystem,
        }
