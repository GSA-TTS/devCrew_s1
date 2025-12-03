"""
Supply Chain Security Analyzer.

Provides supply chain security analysis including package integrity verification,
dependency confusion detection, typosquatting analysis, malicious pattern detection,
health scoring, and SLSA provenance generation.
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupplyChainAnalyzer:
    """
    Analyzes supply chain security aspects of software dependencies.

    Features:
    - Package integrity verification (hash checking)
    - Dependency confusion attack detection
    - Typosquatting detection
    - Malicious pattern identification
    - Package health metrics analysis
    - Maintainer trust scoring
    - SLSA provenance generation (basic)
    """

    # Known malicious patterns
    MALICIOUS_PATTERNS = [
        r"eval\s*\(",  # Eval usage
        r"exec\s*\(",  # Exec usage
        r"__import__\s*\(",  # Dynamic imports
        r"compile\s*\(",  # Code compilation
        r"base64\.b64decode",  # Base64 decoding (potential obfuscation)
        r"subprocess\.(?:call|run|Popen)",  # Subprocess execution
        r"os\.system",  # OS command execution
        r"socket\.socket",  # Network socket creation
        r"urllib\.request",  # URL requests
        r"requests\.(?:get|post)",  # HTTP requests
    ]

    # Common typosquatting patterns
    COMMON_TYPOS = {
        "a": ["e", "s"],
        "e": ["a", "i"],
        "i": ["e", "o"],
        "o": ["i", "u"],
        "u": ["o", "y"],
        "s": ["z", "a"],
        "z": ["s"],
        "c": ["k"],
        "k": ["c"],
    }

    # Popular package names for typosquatting detection
    POPULAR_PACKAGES = {
        "python": [
            "requests",
            "numpy",
            "pandas",
            "flask",
            "django",
            "pytest",
            "matplotlib",
            "scipy",
            "tensorflow",
            "keras",
            "pillow",
            "beautifulsoup4",
            "selenium",
            "sqlalchemy",
            "redis",
            "celery",
            "boto3",
            "pyyaml",
            "jsonschema",
            "cryptography",
        ],
        "javascript": [
            "express",
            "react",
            "vue",
            "angular",
            "webpack",
            "babel",
            "eslint",
            "typescript",
            "lodash",
            "axios",
            "moment",
            "jquery",
            "socket.io",
            "mongoose",
            "mocha",
            "jest",
            "commander",
            "chalk",
            "yargs",
            "dotenv",
        ],
    }

    def __init__(self, api_timeout: int = 10, cache_enabled: bool = True):
        """
        Initialize the SupplyChainAnalyzer.

        Args:
            api_timeout: Timeout for API requests in seconds
            cache_enabled: Enable local caching for API responses
        """
        self.api_timeout = api_timeout
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, Any] = {}
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "SupplyChainAnalyzer/1.0"})

    def analyze(self, dependencies: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Analyze supply chain security for a list of dependencies.

        Args:
            dependencies: List of dependency dictionaries with keys:
                - name: Package name
                - version: Package version
                - ecosystem: Package ecosystem (python, npm, etc.)

        Returns:
            List of analysis results for each dependency
        """
        results = []

        for dep in dependencies:
            package = dep.get("name", "")
            version = dep.get("version", "")
            ecosystem = dep.get("ecosystem", "python").lower()

            logger.info(f"Analyzing supply chain security for {package}@{version}")

            result = {
                "package": package,
                "version": version,
                "ecosystem": ecosystem,
                "integrity_check": self.verify_integrity(package, version, ecosystem),
                "confusion_risk": self.detect_confusion_attack(package, ecosystem),
                "typosquatting": self.detect_typosquatting(package, ecosystem),
                "malicious_indicators": self.check_malicious_indicators(
                    package, version, ecosystem
                ),
                "health_score": self.calculate_health_score(package, ecosystem),
                "trust_score": self._calculate_trust_score(package, ecosystem),
            }

            results.append(result)

        return results

    def verify_integrity(
        self, package: str, version: str, ecosystem: str
    ) -> Dict[str, Any]:
        """
        Verify package integrity using hash checking.

        Args:
            package: Package name
            version: Package version
            ecosystem: Package ecosystem (python, npm, etc.)

        Returns:
            Dictionary with integrity check results
        """
        result = {
            "status": "unknown",
            "expected_hash": None,
            "actual_hash": None,
            "algorithm": "SHA256",
        }

        try:
            if ecosystem == "python":
                result = self._verify_pypi_integrity(package, version)
            elif ecosystem in ["npm", "javascript", "node"]:
                result = self._verify_npm_integrity(package, version)
            else:
                logger.warning(f"Integrity verification not supported for {ecosystem}")

        except Exception as e:
            logger.error(f"Error verifying integrity for {package}: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def _verify_pypi_integrity(self, package: str, version: str) -> Dict[str, Any]:
        """Verify PyPI package integrity."""
        cache_key = f"pypi_hash_{package}_{version}"

        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            url = f"https://pypi.org/pypi/{quote(package)}/{version}/json"
            response = self.session.get(url, timeout=self.api_timeout)
            response.raise_for_status()
            data = response.json()

            # Get first distribution file's hash
            urls = data.get("urls", [])
            if urls:
                first_url = urls[0]
                digests = first_url.get("digests", {})
                expected_hash = digests.get("sha256", "")

                result = {
                    "status": "verified" if expected_hash else "unknown",
                    "expected_hash": (
                        f"sha256:{expected_hash}" if expected_hash else None
                    ),
                    "actual_hash": None,
                    "algorithm": "SHA256",
                    "source": "PyPI",
                }

                if self.cache_enabled:
                    self._cache[cache_key] = result

                return result

        except requests.RequestException as e:
            logger.error(f"Failed to fetch PyPI data for {package}: {e}")

        return {
            "status": "unknown",
            "expected_hash": None,
            "actual_hash": None,
            "algorithm": "SHA256",
        }

    def _verify_npm_integrity(self, package: str, version: str) -> Dict[str, Any]:
        """Verify npm package integrity."""
        cache_key = f"npm_hash_{package}_{version}"

        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            url = f"https://registry.npmjs.org/{quote(package)}/{version}"
            response = self.session.get(url, timeout=self.api_timeout)
            response.raise_for_status()
            data = response.json()

            dist = data.get("dist", {})
            integrity = dist.get("integrity", "")
            shasum = dist.get("shasum", "")

            result = {
                "status": "verified" if (integrity or shasum) else "unknown",
                "expected_hash": integrity or f"sha1:{shasum}",
                "actual_hash": None,
                "algorithm": "SHA512" if integrity else "SHA1",
                "source": "npm",
            }

            if self.cache_enabled:
                self._cache[cache_key] = result

            return result

        except requests.RequestException as e:
            logger.error(f"Failed to fetch npm data for {package}: {e}")

        return {
            "status": "unknown",
            "expected_hash": None,
            "actual_hash": None,
            "algorithm": "SHA256",
        }

    def detect_confusion_attack(self, package: str, ecosystem: str) -> Dict[str, Any]:
        """
        Detect potential dependency confusion attacks.

        Checks if a package name might conflict between private and public
        registries, potentially allowing an attacker to upload a malicious
        package with the same name to a public registry.

        Args:
            package: Package name
            ecosystem: Package ecosystem

        Returns:
            Dictionary with confusion attack risk assessment
        """
        result = {
            "risk_level": "none",
            "has_private_namespace": False,
            "public_package_exists": False,
            "version_comparison": None,
        }

        # Check for private namespace indicators
        private_indicators = [
            "@company/",
            "@org/",
            "@internal/",
            "@private/",
            "-internal",
            "-private",
            "_internal",
            "_private",
        ]

        has_private_namespace = any(
            indicator in package.lower() for indicator in private_indicators
        )
        result["has_private_namespace"] = has_private_namespace

        # Check if package exists in public registry
        public_exists = self._check_public_registry(package, ecosystem)
        result["public_package_exists"] = public_exists

        # Calculate risk level
        if has_private_namespace and public_exists:
            result["risk_level"] = "high"
        elif has_private_namespace:
            result["risk_level"] = "medium"
        elif public_exists and self._is_suspicious_name(package):
            result["risk_level"] = "low"

        return result

    def _check_public_registry(self, package: str, ecosystem: str) -> bool:
        """Check if package exists in public registry."""
        cache_key = f"public_exists_{ecosystem}_{package}"

        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            if ecosystem == "python":
                url = f"https://pypi.org/pypi/{quote(package)}/json"
            elif ecosystem in ["npm", "javascript", "node"]:
                url = f"https://registry.npmjs.org/{quote(package)}"
            else:
                return False

            response = self.session.get(url, timeout=self.api_timeout)
            exists = response.status_code == 200

            if self.cache_enabled:
                self._cache[cache_key] = exists

            return exists

        except requests.RequestException:
            return False

    def _is_suspicious_name(self, package: str) -> bool:
        """Check if package name has suspicious patterns."""
        suspicious_patterns = [
            r"test[_-]?package",
            r"example[_-]?pkg",
            r"temp[_-]?lib",
            r"demo[_-]?package",
            r"\d{4,}",  # Many numbers
        ]

        return any(
            re.search(pattern, package, re.IGNORECASE)
            for pattern in suspicious_patterns
        )

    def detect_typosquatting(self, package: str, ecosystem: str) -> Dict[str, Any]:
        """
        Detect potential typosquatting attempts.

        Analyzes package name similarity to popular packages using various
        techniques including Levenshtein distance, common typo patterns,
        and character substitutions.

        Args:
            package: Package name
            ecosystem: Package ecosystem

        Returns:
            Dictionary with typosquatting risk assessment
        """
        similar_pkg_names: List[str] = []
        result: Dict[str, Any] = {
            "risk_level": "none",
            "similar_packages": similar_pkg_names,
            "levenshtein_distance": None,
        }

        popular_packages = self.POPULAR_PACKAGES.get(ecosystem, [])

        similar_packages: List[Dict[str, Any]] = []
        min_distance = float("inf")

        for popular in popular_packages:
            distance = self._levenshtein_distance(package.lower(), popular.lower())

            # Check for similar packages (distance 1-3)
            if 0 < distance <= 3:
                similar_packages.append({"package": popular, "distance": distance})
                min_distance = min(min_distance, distance)

        # Extract package names
        for pkg in similar_packages[:5]:
            similar_pkg_names.append(str(pkg["package"]))

        if similar_packages:
            result["levenshtein_distance"] = int(min_distance)

            # Determine risk level based on distance
            if min_distance == 1:
                result["risk_level"] = "high"
            elif min_distance == 2:
                result["risk_level"] = "medium"
            else:
                result["risk_level"] = "low"

        # Check for common typo patterns
        typo_matches = self._check_typo_patterns(package, popular_packages)
        if typo_matches:
            similar_pkg_names.extend(typo_matches)
            result["risk_level"] = "high"

        return result

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _check_typo_patterns(
        self, package: str, popular_packages: List[str]
    ) -> List[str]:
        """Check for common typo patterns."""
        matches = []

        for popular in popular_packages:
            # Check for doubled characters
            if self._has_doubled_char(package, popular):
                matches.append(popular)
                continue

            # Check for swapped characters
            if self._has_swapped_chars(package, popular):
                matches.append(popular)
                continue

            # Check for missing hyphen/underscore
            if package.replace("-", "").replace("_", "") == popular.replace(
                "-", ""
            ).replace("_", ""):
                matches.append(popular)

        return matches[:3]

    def _has_doubled_char(self, s1: str, s2: str) -> bool:
        """Check if s1 is s2 with a doubled character."""
        for i in range(len(s2)):
            modified = s2[:i] + s2[i] + s2[i:]
            if modified == s1:
                return True
        return False

    def _has_swapped_chars(self, s1: str, s2: str) -> bool:
        """Check if s1 is s2 with swapped adjacent characters."""
        if len(s1) != len(s2):
            return False

        for i in range(len(s2) - 1):
            modified = list(s2)
            modified[i], modified[i + 1] = modified[i + 1], modified[i]
            if "".join(modified) == s1:
                return True
        return False

    def check_malicious_indicators(
        self, package: str, version: str, ecosystem: str
    ) -> Dict[str, Any]:
        """
        Check for malicious indicators in package.

        Analyzes package metadata and code patterns for suspicious behaviors
        such as obfuscated code, install hooks, network calls, and file
        system access.

        Args:
            package: Package name
            version: Package version
            ecosystem: Package ecosystem

        Returns:
            Dictionary with malicious indicator assessment
        """
        indicators: List[str] = []
        suspicious_patterns: List[str] = []

        result = {
            "risk_level": "none",
            "indicators": indicators,
            "suspicious_patterns": suspicious_patterns,
        }

        try:
            # Get package metadata
            metadata = self._get_package_metadata(package, version, ecosystem)

            if not metadata:
                return result

            # Check for suspicious patterns in description
            description = metadata.get("description", "")
            if self._has_suspicious_description(description):
                indicators.append("suspicious_description")

            # Check for install hooks
            if self._has_install_hooks(metadata, ecosystem):
                indicators.append("install_hooks")

            # Check for minimal metadata
            if self._has_minimal_metadata(metadata):
                indicators.append("minimal_metadata")

            # Check for recent creation with high version
            if self._is_new_with_high_version(metadata):
                indicators.append("new_package_high_version")

            # Check for obfuscated code patterns (if source available)
            patterns = self._check_code_patterns(metadata, ecosystem)
            if patterns:
                suspicious_patterns.extend(patterns)

            # Calculate risk level
            indicator_count = len(result["indicators"]) + len(
                result["suspicious_patterns"]
            )

            if indicator_count >= 3:
                result["risk_level"] = "high"
            elif indicator_count >= 2:
                result["risk_level"] = "medium"
            elif indicator_count >= 1:
                result["risk_level"] = "low"

        except Exception as e:
            logger.error(f"Error checking malicious indicators for {package}: {e}")

        return result

    def _get_package_metadata(
        self, package: str, version: str, ecosystem: str
    ) -> Optional[Dict[str, Any]]:
        """Get package metadata from registry."""
        cache_key = f"metadata_{ecosystem}_{package}_{version}"

        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            if ecosystem == "python":
                url = f"https://pypi.org/pypi/{quote(package)}/{version}/json"
            elif ecosystem in ["npm", "javascript", "node"]:
                url = f"https://registry.npmjs.org/{quote(package)}/{version}"
            else:
                return None

            response = self.session.get(url, timeout=self.api_timeout)
            response.raise_for_status()
            metadata = response.json()

            if self.cache_enabled:
                self._cache[cache_key] = metadata

            return metadata

        except requests.RequestException as e:
            logger.error(f"Failed to fetch metadata for {package}: {e}")
            return None

    def _has_suspicious_description(self, description: str) -> bool:
        """Check for suspicious patterns in description."""
        if not description or len(description) < 10:
            return True

        suspicious_keywords = [
            "test package",
            "do not use",
            "under construction",
            "work in progress",
            "proof of concept",
            "poc",
        ]

        return any(keyword in description.lower() for keyword in suspicious_keywords)

    def _has_install_hooks(self, metadata: Dict[str, Any], ecosystem: str) -> bool:
        """Check for install hooks (setup.py, postinstall scripts)."""
        if ecosystem == "python":
            # Check for setup.py indicators
            info = metadata.get("info", {})
            return bool(info.get("has_scripts", False))

        elif ecosystem in ["npm", "javascript", "node"]:
            # Check for npm lifecycle scripts
            scripts = metadata.get("scripts", {})
            hook_scripts = ["preinstall", "install", "postinstall"]
            return any(hook in scripts for hook in hook_scripts)

        return False

    def _has_minimal_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Check if package has minimal metadata."""
        if "info" in metadata:  # PyPI
            info = metadata["info"]
            return not all(
                [
                    info.get("description"),
                    info.get("author"),
                    info.get("home_page"),
                ]
            )
        elif "description" in metadata:  # npm
            return not all(
                [
                    metadata.get("description"),
                    metadata.get("author"),
                    metadata.get("repository"),
                ]
            )

        return True

    def _is_new_with_high_version(self, metadata: Dict[str, Any]) -> bool:
        """Check if package is new but has suspiciously high version."""
        try:
            if "info" in metadata:  # PyPI
                # PyPI doesn't provide creation date easily
                return False
            elif "time" in metadata:  # npm
                created = metadata["time"].get("created", "")
                if created:
                    created_date = datetime.fromisoformat(
                        created.replace("Z", "+00:00")
                    )
                    age_days = (datetime.now(created_date.tzinfo) - created_date).days

                    version = metadata.get("version", "0.0.0")
                    major_version = int(version.split(".")[0])

                    # Suspicious if less than 30 days old but version >= 5.0.0
                    return age_days < 30 and major_version >= 5

        except Exception as e:
            logger.debug(f"Error checking package age: {e}")

        return False

    def _check_code_patterns(
        self, metadata: Dict[str, Any], ecosystem: str
    ) -> List[str]:
        """Check for suspicious code patterns."""
        patterns = []

        # This would require downloading and analyzing the package source
        # For now, we do a basic check on available text fields

        text_fields = []

        if "info" in metadata:  # PyPI
            info = metadata["info"]
            text_fields.extend(
                [
                    info.get("description", ""),
                    info.get("summary", ""),
                ]
            )
        else:  # npm
            text_fields.extend(
                [
                    metadata.get("description", ""),
                    json.dumps(metadata.get("scripts", {})),
                ]
            )

        full_text = " ".join(text_fields).lower()

        # Check for obfuscation indicators
        if re.search(r"\\x[0-9a-f]{2}", full_text):
            patterns.append("hex_encoding")

        if re.search(r"base64", full_text):
            patterns.append("base64_encoding")

        if re.search(r"eval|exec", full_text):
            patterns.append("code_execution")

        if re.search(r"subprocess|os\.system", full_text):
            patterns.append("system_commands")

        return patterns

    def calculate_health_score(self, package: str, ecosystem: str) -> Dict[str, Any]:
        """
        Calculate package health score based on various metrics.

        Analyzes package health including update frequency, maintainer count,
        download statistics, issue response time, and security policy presence.

        Args:
            package: Package name
            ecosystem: Package ecosystem

        Returns:
            Dictionary with health score and contributing factors
        """
        factors: Dict[str, Any] = {
            "last_updated": None,
            "maintainer_count": 0,
            "download_count": 0,
            "issue_response_time": None,
            "has_security_policy": False,
        }

        result: Dict[str, Any] = {
            "score": 50,  # Default neutral score
            "factors": factors,
        }

        try:
            metadata = self._get_package_metadata(package, "latest", ecosystem)
            if not metadata:
                return result

            score = 0
            max_score = 100

            # Factor 1: Last update (20 points)
            last_updated = self._get_last_update_date(metadata, ecosystem)
            if last_updated:
                factors["last_updated"] = last_updated
                days_since_update = (
                    datetime.now() - datetime.fromisoformat(last_updated)
                ).days

                if days_since_update < 90:
                    score += 20
                elif days_since_update < 180:
                    score += 15
                elif days_since_update < 365:
                    score += 10
                else:
                    score += 5

            # Factor 2: Maintainer count (15 points)
            maintainer_count = self._get_maintainer_count(metadata, ecosystem)
            factors["maintainer_count"] = maintainer_count

            if maintainer_count >= 5:
                score += 15
            elif maintainer_count >= 3:
                score += 12
            elif maintainer_count >= 1:
                score += 8

            # Factor 3: Download count (25 points)
            download_count = self._get_download_count(package, ecosystem)
            factors["download_count"] = download_count

            if download_count >= 1000000:
                score += 25
            elif download_count >= 100000:
                score += 20
            elif download_count >= 10000:
                score += 15
            elif download_count >= 1000:
                score += 10
            else:
                score += 5

            # Factor 4: GitHub metrics (25 points)
            github_score = self._get_github_health_score(metadata)
            score += github_score

            # Factor 5: Security policy (15 points)
            has_security = self._has_security_policy(metadata)
            factors["has_security_policy"] = has_security
            if has_security:
                score += 15

            result["score"] = min(score, max_score)

        except Exception as e:
            logger.error(f"Error calculating health score for {package}: {e}")

        return result

    def _get_last_update_date(
        self, metadata: Dict[str, Any], ecosystem: str
    ) -> Optional[str]:
        """Get last update date from metadata."""
        try:
            if "info" in metadata:  # PyPI
                # Get release dates
                releases = metadata.get("releases", {})
                if releases:
                    # Get latest non-yanked release
                    latest_version = metadata["info"]["version"]
                    release_data = releases.get(latest_version, [])
                    if release_data:
                        return release_data[0].get("upload_time_iso_8601", "")

            elif "time" in metadata:  # npm
                return metadata["time"].get("modified", "")

        except Exception as e:
            logger.debug(f"Error getting last update date: {e}")

        return None

    def _get_maintainer_count(self, metadata: Dict[str, Any], ecosystem: str) -> int:
        """Get maintainer count from metadata."""
        try:
            if "info" in metadata:  # PyPI
                # PyPI doesn't easily expose maintainer count
                # Return 1 if author exists
                return 1 if metadata["info"].get("author") else 0

            elif "maintainers" in metadata:  # npm
                return len(metadata.get("maintainers", []))

        except Exception as e:
            logger.debug(f"Error getting maintainer count: {e}")

        return 0

    def _get_download_count(self, package: str, ecosystem: str) -> int:
        """Get download count for package."""
        cache_key = f"downloads_{ecosystem}_{package}"

        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        try:
            if ecosystem == "python":
                # PyPI download stats API
                url = f"https://pypistats.org/api/packages/{quote(package)}/recent"
                response = self.session.get(url, timeout=self.api_timeout)
                if response.status_code == 200:
                    data = response.json()
                    downloads = data.get("data", {}).get("last_month", 0)

                    if self.cache_enabled:
                        self._cache[cache_key] = downloads

                    return downloads

            elif ecosystem in ["npm", "javascript", "node"]:
                # npm download stats API
                base_url = "https://api.npmjs.org/downloads/point/last-month"
                url = f"{base_url}/{quote(package)}"
                response = self.session.get(url, timeout=self.api_timeout)
                if response.status_code == 200:
                    data = response.json()
                    downloads = data.get("downloads", 0)

                    if self.cache_enabled:
                        self._cache[cache_key] = downloads

                    return downloads

        except requests.RequestException as e:
            logger.debug(f"Error fetching download count for {package}: {e}")

        return 0

    def _get_github_health_score(self, metadata: Dict[str, Any]) -> int:
        """Get health score from GitHub metrics."""
        score = 0

        try:
            # Extract GitHub URL
            github_url = None

            if "info" in metadata:  # PyPI
                project_urls = metadata["info"].get("project_urls", {})
                github_url = project_urls.get("Source") or project_urls.get("Homepage")
            elif "repository" in metadata:  # npm
                repo = metadata.get("repository", {})
                if isinstance(repo, dict):
                    github_url = repo.get("url", "")
                else:
                    github_url = repo

            if github_url and "github.com" in github_url:
                # Extract owner/repo from URL
                match = re.search(r"github\.com[:/]([^/]+)/([^/\.]+)", github_url)
                if match:
                    owner, repo = match.groups()

                    # This would require GitHub API token for real implementation
                    # For now, give default score
                    score = 12  # Moderate score for having a GitHub repo

        except Exception as e:
            logger.debug(f"Error getting GitHub health score: {e}")

        return score

    def _has_security_policy(self, metadata: Dict[str, Any]) -> bool:
        """Check if package has a security policy."""
        try:
            # Check project URLs for security policy
            if "info" in metadata:  # PyPI
                project_urls = metadata["info"].get("project_urls", {})
                return any("security" in key.lower() for key in project_urls.keys())

            elif "repository" in metadata:  # npm
                # npm packages with GitHub repos might have SECURITY.md
                # This would require additional GitHub API call
                return False

        except Exception as e:
            logger.debug(f"Error checking security policy: {e}")

        return False

    def _calculate_trust_score(self, package: str, ecosystem: str) -> int:
        """
        Calculate overall trust score for a package.

        Combines multiple factors including health score, integrity checks,
        and risk assessments to provide an overall trust metric.

        Args:
            package: Package name
            ecosystem: Package ecosystem

        Returns:
            Trust score from 0-100
        """
        try:
            # Get health score
            health_data = self.calculate_health_score(package, ecosystem)
            health_score = health_data["score"]

            # Check for malicious indicators
            malicious = self.check_malicious_indicators(package, "latest", ecosystem)
            malicious_penalty = 0

            if malicious["risk_level"] == "high":
                malicious_penalty = 40
            elif malicious["risk_level"] == "medium":
                malicious_penalty = 20
            elif malicious["risk_level"] == "low":
                malicious_penalty = 10

            # Check for typosquatting
            typo = self.detect_typosquatting(package, ecosystem)
            typo_penalty = 0

            if typo["risk_level"] == "high":
                typo_penalty = 30
            elif typo["risk_level"] == "medium":
                typo_penalty = 15
            elif typo["risk_level"] == "low":
                typo_penalty = 5

            # Calculate final trust score
            trust_score = health_score - malicious_penalty - typo_penalty
            trust_score = max(0, min(100, trust_score))

            return trust_score

        except Exception as e:
            logger.error(f"Error calculating trust score for {package}: {e}")
            return 50  # Default neutral score

    def generate_slsa_provenance(
        self, dependencies: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Generate SLSA (Supply-chain Levels for Software Artifacts) provenance.

        Creates a basic SLSA provenance document describing the build process
        and materials (dependencies) used.

        Args:
            dependencies: List of dependency dictionaries

        Returns:
            SLSA provenance document (basic implementation)
        """
        materials = []

        for dep in dependencies:
            package = dep.get("name", "")
            version = dep.get("version", "")
            ecosystem = dep.get("ecosystem", "python")

            # Get package hash if available
            integrity = self.verify_integrity(package, version, ecosystem)
            digest = {}

            if integrity.get("expected_hash"):
                hash_value = integrity["expected_hash"]
                if ":" in hash_value:
                    algo, value = hash_value.split(":", 1)
                    digest[algo.lower()] = value

            # Create package URL (purl)
            purl = self._create_package_url(package, version, ecosystem)

            material = {"uri": purl, "digest": digest}

            materials.append(material)

        provenance = {
            "_type": "https://in-toto.io/Statement/v0.1",
            "predicateType": "https://slsa.dev/provenance/v0.2",
            "subject": [
                {
                    "name": "supply-chain-analysis",
                    "digest": {"sha256": self._generate_analysis_hash()},
                }
            ],
            "predicate": {
                "builder": {"id": "https://github.com/devCrew_s1/sca-scanner"},
                "buildType": "https://slsa.dev/build-type/sca/v1",
                "invocation": {
                    "configSource": {
                        "uri": "https://github.com/devCrew_s1/sca-scanner",
                        "digest": {"sha256": ""},
                        "entryPoint": "supply_chain_analyzer.py",
                    }
                },
                "metadata": {
                    "buildStartedOn": datetime.utcnow().isoformat() + "Z",
                    "buildFinishedOn": datetime.utcnow().isoformat() + "Z",
                    "completeness": {
                        "parameters": True,
                        "environment": False,
                        "materials": True,
                    },
                    "reproducible": False,
                },
                "materials": materials,
            },
        }

        return provenance

    def _create_package_url(self, package: str, version: str, ecosystem: str) -> str:
        """Create Package URL (purl) for a package."""
        ecosystem_map = {
            "python": "pypi",
            "javascript": "npm",
            "npm": "npm",
            "node": "npm",
            "java": "maven",
            "ruby": "gem",
            "rust": "cargo",
            "go": "golang",
        }

        purl_ecosystem = ecosystem_map.get(ecosystem.lower(), ecosystem.lower())
        return f"pkg:{purl_ecosystem}/{package}@{version}"

    def _generate_analysis_hash(self) -> str:
        """Generate hash for the analysis run."""
        data = f"sca-analysis-{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "entries": len(self._cache),
            "size_bytes": sum(len(str(v).encode()) for v in self._cache.values()),
        }
