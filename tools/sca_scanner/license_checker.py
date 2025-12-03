"""
License Checker Module

Detects and validates software licenses against policies, checks SPDX
compliance, identifies copyleft licenses, and provides compatibility analysis.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import requests
from license_expression import ExpressionError, get_spdx_licensing

# Configure logging
logger = logging.getLogger(__name__)


class PolicyStatus(Enum):
    """License policy compliance status."""

    ALLOWED = "allowed"
    DENIED = "denied"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"


class LicenseCategory(Enum):
    """License categories based on permissions and restrictions."""

    PERMISSIVE = "permissive"
    COPYLEFT_WEAK = "copyleft_weak"
    COPYLEFT_STRONG = "copyleft_strong"
    PROPRIETARY = "proprietary"
    PUBLIC_DOMAIN = "public_domain"
    UNKNOWN = "unknown"


@dataclass
class LicenseInfo:
    """Structured license information."""

    package: str
    version: str
    license: str
    spdx_id: Optional[str] = None
    is_osi_approved: bool = False
    is_copyleft: bool = False
    category: LicenseCategory = LicenseCategory.UNKNOWN
    policy_status: PolicyStatus = PolicyStatus.UNKNOWN
    policy_violation: bool = False
    recommendation: str = "No action needed"
    compatibility_issues: List[str] = field(default_factory=list)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)  # noqa: E501


class LicenseChecker:  # pylint: disable=too-many-instance-attributes
    """
    License compliance checker for software dependencies.

    Validates licenses against organizational policies, detects copyleft
    licenses, and analyzes license compatibility across dependencies.
    """

    # SPDX identifier mappings for common non-standard license names
    LICENSE_ALIASES = {
        "apache": "Apache-2.0",
        "apache 2": "Apache-2.0",
        "apache 2.0": "Apache-2.0",
        "apache license 2.0": "Apache-2.0",
        "apache software license": "Apache-2.0",
        "bsd": "BSD-3-Clause",
        "bsd license": "BSD-3-Clause",
        "new bsd": "BSD-3-Clause",
        "new bsd license": "BSD-3-Clause",
        "modified bsd": "BSD-3-Clause",
        "3-clause bsd": "BSD-3-Clause",
        "simplified bsd": "BSD-2-Clause",
        "2-clause bsd": "BSD-2-Clause",
        "gpl": "GPL-3.0",
        "gplv2": "GPL-2.0",
        "gplv3": "GPL-3.0",
        "gnu gpl": "GPL-3.0",
        "gnu general public license": "GPL-3.0",
        "lgpl": "LGPL-3.0",
        "lgplv2": "LGPL-2.1",
        "lgplv3": "LGPL-3.0",
        "agpl": "AGPL-3.0",
        "agplv3": "AGPL-3.0",
        "mit license": "MIT",
        "isc license": "ISC",
        "mpl": "MPL-2.0",
        "mozilla public license": "MPL-2.0",
        "eclipse public license": "EPL-2.0",
        "epl": "EPL-2.0",
        "cc0": "CC0-1.0",
        "public domain": "CC0-1.0",
        "unlicense": "Unlicense",
        "wtfpl": "WTFPL",
    }

    # OSI-approved licenses
    OSI_APPROVED = {
        "MIT",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "GPL-2.0",
        "GPL-3.0",
        "LGPL-2.1",
        "LGPL-3.0",
        "AGPL-3.0",
        "MPL-2.0",
        "EPL-2.0",
        "ISC",
        "CC0-1.0",
        "Unlicense",
        "WTFPL",
        "Python-2.0",
        "PSF-2.0",
        "Artistic-2.0",
        "Zlib",
        "CDDL-1.0",
        "CPL-1.0",
        "EPL-1.0",
    }

    # Copyleft licenses (strong and weak)
    COPYLEFT_STRONG = {
        "GPL-2.0",
        "GPL-2.0-only",
        "GPL-2.0-or-later",
        "GPL-3.0",
        "GPL-3.0-only",
        "GPL-3.0-or-later",
        "AGPL-3.0",
        "AGPL-3.0-only",
        "AGPL-3.0-or-later",
        "CC-BY-SA-4.0",
        "CC-BY-SA-3.0",
    }

    COPYLEFT_WEAK = {
        "LGPL-2.1",
        "LGPL-2.1-only",
        "LGPL-2.1-or-later",
        "LGPL-3.0",
        "LGPL-3.0-only",
        "LGPL-3.0-or-later",
        "MPL-2.0",
        "MPL-1.1",
        "EPL-2.0",
        "EPL-1.0",
        "CDDL-1.0",
        "CPL-1.0",
    }

    # License categories mapping
    LICENSE_CATEGORIES = {
        LicenseCategory.PERMISSIVE: {
            "MIT",
            "Apache-2.0",
            "BSD-2-Clause",
            "BSD-3-Clause",
            "ISC",
            "Zlib",
            "Python-2.0",
            "PSF-2.0",
            "Artistic-2.0",
        },
        LicenseCategory.PUBLIC_DOMAIN: {"CC0-1.0", "Unlicense", "WTFPL"},
    }

    def __init__(self, cache_enabled: bool = True, request_timeout: int = 10):
        """
        Initialize LicenseChecker.

        Args:
            cache_enabled: Enable local caching of license data
            request_timeout: HTTP request timeout in seconds
        """
        self.cache_enabled = cache_enabled
        self.request_timeout = request_timeout
        self._license_cache: Dict[str, Dict[str, Any]] = {}
        self._spdx_licensing = get_spdx_licensing()

        # HTTP session with connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "devCrew-SCA-Scanner/1.0",
                "Accept": "application/json",
            }
        )

    def check_licenses(
        self,
        dependencies: List[Dict[str, str]],
        policy: Dict[str, Any],
    ) -> List[LicenseInfo]:
        """
        Check licenses for all dependencies against policy.

        Args:
            dependencies: List of dependency dicts with 'name',
                         'version', 'ecosystem' keys
            policy: License policy configuration

        Returns:
            List of LicenseInfo objects with compliance status
        """
        results = []

        for dep in dependencies:
            package = dep.get("name", "")
            version = dep.get("version", "")
            ecosystem = dep.get("ecosystem", "pypi")

            try:
                license_info = self._check_package_license(
                    package, version, ecosystem, policy
                )
                results.append(license_info)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "Failed to check license for %s@%s: %s", package, version, e
                )
                # Create error result
                results.append(
                    LicenseInfo(
                        package=package,
                        version=version,
                        license="Unknown",
                        policy_violation=True,
                        recommendation=(f"Failed to retrieve license information: {e}"),
                    )
                )

        # Perform compatibility analysis across all licenses
        self._analyze_compatibility(results)

        return results

    def _check_package_license(
        self,
        package: str,
        version: str,
        ecosystem: str,
        policy: Dict[str, Any],
    ) -> LicenseInfo:
        """
        Check license for a single package.

        Args:
            package: Package name
            version: Package version
            ecosystem: Package ecosystem (pypi, npm, maven, etc.)
            policy: License policy configuration

        Returns:
            LicenseInfo object with license details and compliance status
        """
        # Detect license from package metadata
        raw_license, metadata = self.detect_license(package, version, ecosystem)

        # Normalize to SPDX identifier
        spdx_id = self.normalize_license(raw_license)

        # Determine license category
        category = self._categorize_license(spdx_id)

        # Check if copyleft
        is_copyleft = self.check_copyleft(spdx_id) if spdx_id else False

        # Check OSI approval
        is_osi_approved = spdx_id in self.OSI_APPROVED if spdx_id else False

        # Validate against policy
        policy_status, policy_violation = self.validate_policy(
            spdx_id or raw_license, policy
        )  # noqa: E501

        # Generate recommendation
        recommendation = self._generate_recommendation(
            policy_status, policy_violation, is_copyleft, category
        )

        return LicenseInfo(
            package=package,
            version=version,
            license=raw_license,
            spdx_id=spdx_id,
            is_osi_approved=is_osi_approved,
            is_copyleft=is_copyleft,
            category=category,
            policy_status=policy_status,
            policy_violation=policy_violation,
            recommendation=recommendation,
            raw_metadata=metadata,
        )

    def detect_license(
        self, package: str, version: str, ecosystem: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Detect license from package metadata.

        Args:
            package: Package name
            version: Package version
            ecosystem: Package ecosystem

        Returns:
            Tuple of (license_string, metadata_dict)
        """
        cache_key = f"{ecosystem}:{package}:{version}"

        # Check cache
        if self.cache_enabled and cache_key in self._license_cache:
            cached = self._license_cache[cache_key]
            return cached["license"], cached["metadata"]

        # Fetch from appropriate source
        ecosystem_lower = ecosystem.lower()

        if ecosystem_lower in ["pypi", "python", "pip"]:
            license_str, metadata = self._fetch_pypi_license(package, version)
        elif ecosystem_lower in ["npm", "node", "nodejs"]:
            license_str, metadata = self._fetch_npm_license(package, version)
        elif ecosystem_lower in ["maven", "java"]:
            license_str, metadata = self._fetch_maven_license(package, version)
        elif ecosystem_lower in ["cargo", "rust", "crates"]:
            license_str, metadata = self._fetch_cargo_license(package, version)
        elif ecosystem_lower in ["gem", "ruby", "rubygems"]:
            license_str, metadata = self._fetch_rubygems_license(package, version)
        elif ecosystem_lower in ["go", "golang"]:
            license_str, metadata = self._fetch_go_license(package, version)
        else:
            logger.warning("Unsupported ecosystem: %s", ecosystem)
            license_str, metadata = "Unknown", {}

        # Cache result
        if self.cache_enabled:
            self._license_cache[cache_key] = {
                "license": license_str,
                "metadata": metadata,
            }

        return license_str, metadata

    def normalize_license(self, license_text: str) -> Optional[str]:
        """
        Normalize license text to SPDX identifier.

        Args:
            license_text: Raw license string

        Returns:
            SPDX identifier or None if not recognized
        """
        if not license_text or license_text.lower() in [
            "unknown",
            "none",
            "n/a",
        ]:
            return None

        # Try direct SPDX validation
        try:
            parsed = self._spdx_licensing.parse(license_text)
            return str(parsed)
        except ExpressionError:
            pass

        # Try alias mapping
        normalized = license_text.lower().strip()
        if normalized in self.LICENSE_ALIASES:
            return self.LICENSE_ALIASES[normalized]

        # Try partial matching
        for alias, spdx_id in self.LICENSE_ALIASES.items():
            if alias in normalized or normalized in alias:
                return spdx_id

        # Extract SPDX-like identifiers from text
        spdx_pattern = r"\b([A-Z][A-Za-z0-9\-\.]+)\b"
        matches = re.findall(spdx_pattern, license_text)
        for match in matches:
            if match in self.OSI_APPROVED or match in self.COPYLEFT_STRONG:
                return match

        logger.warning("Could not normalize license: %s", license_text)
        return None

    def validate_policy(  # pylint: disable=too-many-return-statements
        self, license_id: str, policy: Dict[str, Any]
    ) -> Tuple[PolicyStatus, bool]:
        """
        Validate license against policy.

        Args:
            license_id: License identifier (SPDX or raw)
            policy: Policy configuration with allowed/denied lists

        Returns:
            Tuple of (PolicyStatus, violation_flag)
        """
        if not license_id or license_id.lower() in ["unknown", "none"]:
            return PolicyStatus.UNKNOWN, True

        allowed = policy.get("allowed", [])
        denied = policy.get("denied", [])
        conditional = policy.get("conditional", {})
        copyleft_allowed = policy.get("copyleft_allowed", False)

        # Check denied list first (highest priority)
        if license_id in denied:
            return PolicyStatus.DENIED, True

        # Check conditional licenses
        if license_id in conditional:
            return PolicyStatus.CONDITIONAL, False

        # Check allowed list
        if license_id in allowed:
            return PolicyStatus.ALLOWED, False

        # Check copyleft policy if not explicitly listed
        if not copyleft_allowed and self.check_copyleft(license_id):
            return PolicyStatus.DENIED, True

        # Handle dual/multi licensing (e.g., "MIT OR Apache-2.0")
        if " OR " in license_id or " AND " in license_id:
            return self._validate_compound_license(license_id, policy)

        # Default to unknown if not in policy
        return PolicyStatus.UNKNOWN, True

    def check_copyleft(self, license_id: str) -> bool:
        """
        Check if license is copyleft (strong or weak).

        Args:
            license_id: SPDX license identifier

        Returns:
            True if copyleft, False otherwise
        """
        if not license_id:
            return False

        # Normalize for comparison
        license_upper = license_id.upper()

        # Check strong copyleft
        if license_id in self.COPYLEFT_STRONG:
            return True

        # Check weak copyleft
        if license_id in self.COPYLEFT_WEAK:
            return True

        # Pattern matching for GPL/AGPL variants
        copyleft_patterns = [r"GPL", r"AGPL", r"CC-BY-SA"]
        for pattern in copyleft_patterns:
            if re.search(pattern, license_upper):
                return True

        return False

    def check_compatibility(self, licenses: List[str]) -> Dict[str, List[str]]:
        """
        Analyze license compatibility across multiple licenses.

        Args:
            licenses: List of SPDX license identifiers

        Returns:
            Dictionary of compatibility issues grouped by license
        """
        issues = {}

        # Remove duplicates and None values
        unique_licenses = set(filter(None, licenses))

        # Check for incompatible combinations
        has_strong_copyleft = any(
            lic in self.COPYLEFT_STRONG for lic in unique_licenses
        )
        has_permissive = any(
            lic in self.LICENSE_CATEGORIES.get(LicenseCategory.PERMISSIVE, set())
            for lic in unique_licenses
        )

        # Strong copyleft + proprietary/other copyleft can cause issues
        for lic in unique_licenses:
            license_issues = []

            if lic in self.COPYLEFT_STRONG:
                # GPL incompatible with different copyleft licenses
                other_copyleft = (self.COPYLEFT_STRONG | self.COPYLEFT_WEAK) - {lic}
                conflicting = unique_licenses & other_copyleft
                if conflicting:
                    license_issues.append(
                        f"Strong copyleft {lic} may conflict with: "
                        f"{', '.join(conflicting)}"
                    )

            elif lic in self.COPYLEFT_WEAK:
                # Weak copyleft with strong copyleft needs careful handling
                if has_strong_copyleft:
                    license_issues.append(
                        f"Weak copyleft {lic} combined with strong "
                        "copyleft licenses - verify compatibility"
                    )

            # Check for proprietary/custom licenses
            if lic not in (
                self.OSI_APPROVED | self.COPYLEFT_STRONG | self.COPYLEFT_WEAK
            ):
                if has_strong_copyleft or has_permissive:
                    license_issues.append(
                        f"Custom/proprietary license {lic} may have "
                        "compatibility issues"
                    )

            if license_issues:
                issues[lic] = license_issues

        return issues

    def _analyze_compatibility(self, results: List[LicenseInfo]) -> None:
        """
        Perform compatibility analysis and update results in-place.

        Args:
            results: List of LicenseInfo objects to analyze
        """
        # Extract all SPDX identifiers
        licenses = [r.spdx_id for r in results if r.spdx_id]

        if len(licenses) <= 1:
            return  # No compatibility issues with single license

        # Get compatibility issues
        compatibility_issues = self.check_compatibility(licenses)

        # Update results with compatibility information
        for result in results:
            if result.spdx_id and result.spdx_id in compatibility_issues:
                result.compatibility_issues = compatibility_issues[result.spdx_id]

                # Update recommendation if there are compatibility issues
                if result.compatibility_issues:
                    result.recommendation += (
                        " | Compatibility issues detected: "
                        + "; ".join(result.compatibility_issues)
                    )

    def _validate_compound_license(
        self, license_expr: str, policy: Dict[str, Any]
    ) -> Tuple[PolicyStatus, bool]:
        """
        Validate compound license expressions (OR/AND).

        Args:
            license_expr: Compound license expression
            policy: License policy

        Returns:
            Tuple of (PolicyStatus, violation_flag)
        """
        allowed = policy.get("allowed", [])

        try:
            # Parse with SPDX library
            parsed = self._spdx_licensing.parse(license_expr)

            # For OR expressions, check if any alternative is allowed
            if " OR " in str(parsed):
                alternatives = str(parsed).split(" OR ")
                for alt in alternatives:
                    alt = alt.strip()
                    if alt in allowed:
                        return PolicyStatus.ALLOWED, False

                # None of the alternatives are allowed
                return PolicyStatus.DENIED, True

            # For AND expressions, all must be allowed
            if " AND " in str(parsed):
                requirements = str(parsed).split(" AND ")
                for req in requirements:
                    req = req.strip()
                    if req not in allowed:
                        return PolicyStatus.DENIED, True

                return PolicyStatus.ALLOWED, False

        except ExpressionError:
            logger.warning("Failed to parse compound license: %s", license_expr)

        return PolicyStatus.UNKNOWN, True

    def _categorize_license(self, spdx_id: Optional[str]) -> LicenseCategory:
        """
        Categorize license by type.

        Args:
            spdx_id: SPDX license identifier

        Returns:
            LicenseCategory enum value
        """
        if not spdx_id:
            return LicenseCategory.UNKNOWN

        # Check each category
        for category, licenses in self.LICENSE_CATEGORIES.items():
            if spdx_id in licenses:
                return category

        # Check copyleft categories
        if spdx_id in self.COPYLEFT_STRONG:
            return LicenseCategory.COPYLEFT_STRONG
        if spdx_id in self.COPYLEFT_WEAK:
            return LicenseCategory.COPYLEFT_WEAK

        # Check for proprietary indicators
        if "proprietary" in spdx_id.lower():
            return LicenseCategory.PROPRIETARY

        return LicenseCategory.UNKNOWN

    def _generate_recommendation(
        self,
        policy_status: PolicyStatus,
        policy_violation: bool,
        is_copyleft: bool,
        category: LicenseCategory,
    ) -> str:
        """
        Generate remediation recommendation based on license status.

        Args:
            policy_status: Policy compliance status
            policy_violation: Whether there's a violation
            is_copyleft: Whether license is copyleft
            category: License category

        Returns:
            Human-readable recommendation string
        """
        if not policy_violation and policy_status == PolicyStatus.ALLOWED:
            return "No action needed"

        recommendations = []

        if policy_status == PolicyStatus.DENIED:
            recommendations.append(
                "License is explicitly denied by policy. "
                "Consider replacing with allowed alternative."
            )

        elif policy_status == PolicyStatus.CONDITIONAL:
            recommendations.append(
                "License has conditional approval. "
                "Review policy conditions before use."
            )

        elif policy_status == PolicyStatus.UNKNOWN:
            recommendations.append(
                "License not found in policy. "
                "Request policy review or choose alternative."
            )

        if is_copyleft and category == LicenseCategory.COPYLEFT_STRONG:
            recommendations.append(
                "Strong copyleft license detected. "
                "Ensure compliance with distribution requirements."
            )

        if not recommendations:
            recommendations.append("Review license terms and verify compliance.")

        return " ".join(recommendations)

    # Ecosystem-specific license fetchers

    def _fetch_pypi_license(
        self, package: str, version: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Fetch license from PyPI."""
        try:
            url = f"https://pypi.org/pypi/{package}/{version}/json"
            response = self.session.get(url, timeout=self.request_timeout)
            response.raise_for_status()

            data = response.json()
            info = data.get("info", {})

            license_str = info.get("license") or "Unknown"

            # Fallback to classifiers
            if license_str in ["Unknown", "", "UNKNOWN"]:
                classifiers = info.get("classifiers", [])
                for classifier in classifiers:
                    if classifier.startswith("License ::"):
                        license_str = classifier.split("::")[-1].strip()
                        break

            metadata = {
                "url": info.get("home_page"),
                "author": info.get("author"),
            }

            return license_str, metadata

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to fetch PyPI license for %s: %s", package, e)
            return "Unknown", {}

    def _fetch_npm_license(
        self, package: str, version: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Fetch license from npm registry."""
        try:
            url = f"https://registry.npmjs.org/{package}/{version}"
            response = self.session.get(url, timeout=self.request_timeout)
            response.raise_for_status()

            data = response.json()
            license_field = data.get("license", "Unknown")

            # Handle object format
            if isinstance(license_field, dict):
                license_str = license_field.get("type", "Unknown")
            else:
                license_str = str(license_field)

            metadata = {
                "url": data.get("homepage"),
                "repository": data.get("repository"),
            }

            return license_str, metadata

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to fetch npm license for %s: %s", package, e)
            return "Unknown", {}

    def _fetch_maven_license(
        self, package: str, version: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Fetch license from Maven Central."""
        try:
            # Maven coordinates: groupId:artifactId
            parts = package.split(":")
            if len(parts) != 2:
                return "Unknown", {}

            group_id, artifact_id = parts
            group_path = group_id.replace(".", "/")

            url = (
                f"https://repo1.maven.org/maven2/{group_path}/"
                f"{artifact_id}/{version}/{artifact_id}-{version}.pom"
            )

            response = self.session.get(url, timeout=self.request_timeout)
            response.raise_for_status()

            # Parse POM XML (simple extraction)
            pom_text = response.text
            license_match = re.search(
                r"<license>.*?<name>(.*?)</name>", pom_text, re.DOTALL
            )

            if license_match:
                license_str = license_match.group(1).strip()
            else:
                license_str = "Unknown"

            metadata = {"url": url}
            return license_str, metadata

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to fetch Maven license for %s: %s", package, e)
            return "Unknown", {}

    def _fetch_cargo_license(
        self, package: str, version: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Fetch license from crates.io."""
        try:
            url = f"https://crates.io/api/v1/crates/{package}/{version}"
            response = self.session.get(url, timeout=self.request_timeout)
            response.raise_for_status()

            data = response.json()
            version_data = data.get("version", {})
            license_str = version_data.get("license") or "Unknown"

            metadata = {
                "url": version_data.get("homepage"),
                "repository": version_data.get("repository"),
            }

            return license_str, metadata

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to fetch crates.io license for %s: %s", package, e)
            return "Unknown", {}

    def _fetch_rubygems_license(
        self, package: str, version: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Fetch license from RubyGems."""
        try:
            url = f"https://rubygems.org/api/v2/rubygems/{package}/versions/{version}.json"  # noqa: E501
            response = self.session.get(url, timeout=self.request_timeout)
            response.raise_for_status()

            data = response.json()
            licenses = data.get("licenses", [])

            if licenses:
                license_str = " OR ".join(licenses)
            else:
                license_str = "Unknown"

            metadata = {
                "url": data.get("homepage_uri"),
                "source": data.get("source_code_uri"),
            }

            return license_str, metadata

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to fetch RubyGems license for %s: %s", package, e)
            return "Unknown", {}

    def _fetch_go_license(
        self, package: str, version: str
    ) -> Tuple[str, Dict[str, Any]]:
        """Fetch license from pkg.go.dev."""
        try:
            # Go modules use full import paths
            url = f"https://api.pkg.go.dev/v1/module/{package}@{version}"
            response = self.session.get(url, timeout=self.request_timeout)
            response.raise_for_status()

            data = response.json()

            # Go packages typically store license in repository
            # This is a simplified approach
            license_str = data.get("License", "Unknown")

            metadata = {"url": data.get("URL")}

            return license_str, metadata

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to fetch Go license for %s: %s", package, e)
            return "Unknown", {}

    def clear_cache(self) -> None:
        """Clear the license cache."""
        self._license_cache.clear()
        logger.info("License cache cleared")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.session.close()
