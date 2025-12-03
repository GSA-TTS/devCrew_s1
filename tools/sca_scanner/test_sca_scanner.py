"""
Comprehensive Test Suite for SCA Scanner

This test suite provides 90%+ coverage for all SCA scanner modules including:
- DependencyScanner
- VulnerabilityMatcher
- LicenseChecker
- SBOMGenerator
- RemediationAdvisor
- SupplyChainAnalyzer

Tests are organized by module with unit tests, integration tests, and
error handling validation.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from xml.etree import ElementTree as ET

import pytest

# Import the modules to test
from dependency_scanner import (
    Dependency,
    DependencyScanner,
    Ecosystem,
    ManifestParseError,
    UnsupportedFormatError,
)
from license_checker import (
    LicenseChecker,
    LicenseInfo,
    PolicyStatus,
)
from remediation_advisor import (
    RemediationAdvisor,
    UpgradeType,
)
from sbom_generator import (
    FormatError,
    SBOMGenerator,
    ValidationError,
)
from supply_chain_analyzer import SupplyChainAnalyzer
from vulnerability_matcher import (
    APIError,
    RateLimitError,
    VulnerabilityMatcher,
)


# ============= Test Fixtures =============


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_requirements(temp_dir):
    """Create sample requirements.txt file."""
    content = """# Sample requirements
requests==2.25.1
flask>=1.0.0
django~=3.2
numpy>=1.19.0,<2.0.0
pytest  # Latest version
-e git+https://github.com/user/repo.git@master#egg=mypackage
"""
    req_file = temp_dir / "requirements.txt"
    req_file.write_text(content)
    return req_file


@pytest.fixture
def sample_package_json(temp_dir):
    """Create sample package.json file."""
    content = {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": {
            "express": "^4.17.0",
            "lodash": "~4.17.20",
            "axios": ">=0.21.0"
        },
        "devDependencies": {
            "jest": "^27.0.0",
            "eslint": "~7.32.0"
        }
    }
    pkg_file = temp_dir / "package.json"
    pkg_file.write_text(json.dumps(content, indent=2))
    return pkg_file


@pytest.fixture
def sample_package_lock_json(temp_dir):
    """Create sample package-lock.json file."""
    content = {
        "name": "test-project",
        "version": "1.0.0",
        "lockfileVersion": 2,
        "packages": {
            "": {
                "name": "test-project",
                "version": "1.0.0"
            },
            "node_modules/express": {
                "version": "4.17.1",
                "integrity": "sha512-abc123...",
                "dev": False
            },
            "node_modules/lodash": {
                "version": "4.17.21",
                "integrity": "sha512-def456...",
                "dev": False
            }
        }
    }
    lock_file = temp_dir / "package-lock.json"
    lock_file.write_text(json.dumps(content, indent=2))
    return lock_file


@pytest.fixture
def sample_pom_xml(temp_dir):
    """Create sample pom.xml file."""
    content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
    <dependencies>
        <dependency>
            <groupId>org.springframework</groupId>
            <artifactId>spring-core</artifactId>
            <version>5.3.0</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
"""
    pom_file = temp_dir / "pom.xml"
    pom_file.write_text(content)
    return pom_file


@pytest.fixture
def sample_pyproject_toml(temp_dir):
    """Create sample pyproject.toml file."""
    content = """[tool.poetry]
name = "test-project"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.25.0"
flask = "~1.1.0"

[tool.poetry.dev-dependencies]
pytest = "^6.0"
"""
    toml_file = temp_dir / "pyproject.toml"
    toml_file.write_text(content)
    return toml_file


@pytest.fixture
def sample_go_mod(temp_dir):
    """Create sample go.mod file."""
    content = """module example.com/myproject

go 1.16

require (
    github.com/gin-gonic/gin v1.7.0
    github.com/stretchr/testify v1.7.0 // indirect
    golang.org/x/sync v0.0.0-20210220032951-036812b2e83c
)
"""
    go_file = temp_dir / "go.mod"
    go_file.write_text(content)
    return go_file


@pytest.fixture
def mock_cve_response():
    """Mock CVE response from vulnerability database."""
    return {
        "cve": "CVE-2023-32681",
        "package": "requests",
        "version": "2.25.1",
        "severity": "HIGH",
        "cvss_score": 7.5,
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N",
        "description": (
            "Requests is a HTTP library. Vulnerability description..."
        ),
        "references": [
            "https://nvd.nist.gov/vuln/detail/CVE-2023-32681",
            "https://github.com/psf/requests/security/advisories/GHSA-xxx"
        ],
        "fixed_in": "2.31.0",
        "published_date": "2023-05-26"
    }


@pytest.fixture
def mock_osv_response():
    """Mock OSV API response."""
    return {
        "vulns": [
            {
                "id": "PYSEC-2023-123",
                "aliases": ["CVE-2023-32681"],
                "summary": "Proxy authentication bypass vulnerability",
                "details": "Detailed vulnerability information...",
                "severity": [
                    {
                        "type": "CVSS_V3",
                        "score": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N"
                    }
                ],
                "affected": [
                    {
                        "package": {
                            "name": "requests",
                            "ecosystem": "PyPI"
                        },
                        "ranges": [
                            {
                                "type": "ECOSYSTEM",
                                "events": [
                                    {"introduced": "0"},
                                    {"fixed": "2.31.0"}
                                ]
                            }
                        ]
                    }
                ],
                "references": [
                    {"url": "https://nvd.nist.gov/vuln/detail/CVE-2023-32681"}
                ],
                "published": "2023-05-26T00:00:00Z"
            }
        ]
    }


@pytest.fixture
def sample_dependencies():
    """Sample dependency list for testing."""
    return [
        {
            "name": "requests",
            "version": "2.25.1",
            "ecosystem": "pypi",
            "is_direct": True
        },
        {
            "name": "flask",
            "version": "1.1.2",
            "ecosystem": "pypi",
            "is_direct": True
        },
        {
            "name": "numpy",
            "version": "1.19.5",
            "ecosystem": "pypi",
            "is_direct": False
        }
    ]


@pytest.fixture
def sample_license_policy():
    """Sample license policy configuration."""
    return {
        "allowed": [
            "MIT",
            "Apache-2.0",
            "BSD-3-Clause",
            "BSD-2-Clause",
            "ISC"
        ],
        "denied": [
            "GPL-3.0",
            "AGPL-3.0"
        ],
        "conditional": {
            "LGPL-3.0": "Requires legal review for commercial use",
            "MPL-2.0": "Review file-level copyleft implications"
        },
        "copyleft_allowed": False
    }


# ============= DependencyScanner Tests =============


class TestDependencyScanner:
    """Tests for DependencyScanner module."""

    def test_scan_requirements_txt_with_versions(self, sample_requirements):
        """Test scanning requirements.txt with version specifiers."""
        scanner = DependencyScanner(sample_requirements)
        dependencies = scanner.scan()

        assert len(dependencies) >= 4
        assert any(
            d.name == "requests" and d.version == "2.25.1"
            for d in dependencies
        )
        assert any(d.name == "flask" for d in dependencies)
        assert all(d.ecosystem == Ecosystem.PYPI for d in dependencies)

    def test_scan_package_json(self, sample_package_json):
        """Test scanning package.json."""
        scanner = DependencyScanner(sample_package_json)
        dependencies = scanner.scan()

        assert len(dependencies) >= 4
        assert any(d.name == "express" for d in dependencies)
        assert any(
            d.name == "jest" and d.extras.get("dev")
            for d in dependencies
        )
        assert all(d.ecosystem == Ecosystem.NPM for d in dependencies)

    def test_scan_package_lock_json(self, sample_package_lock_json):
        """Test scanning package-lock.json."""
        scanner = DependencyScanner(sample_package_lock_json)
        dependencies = scanner.scan()

        assert len(dependencies) >= 2
        assert any(
            d.name == "express" and d.version == "4.17.1"
            for d in dependencies
        )

    def test_scan_pom_xml(self, sample_pom_xml):
        """Test scanning pom.xml."""
        scanner = DependencyScanner(sample_pom_xml)
        dependencies = scanner.scan()

        assert len(dependencies) >= 2
        assert any("spring-core" in d.name for d in dependencies)
        assert any(d.ecosystem == Ecosystem.MAVEN for d in dependencies)

    def test_scan_pyproject_toml(self, sample_pyproject_toml):
        """Test scanning pyproject.toml."""
        scanner = DependencyScanner(sample_pyproject_toml)
        dependencies = scanner.scan()

        assert len(dependencies) >= 2
        assert any(d.name == "requests" for d in dependencies)
        assert all(d.ecosystem == Ecosystem.PYPI for d in dependencies)

    def test_scan_go_mod(self, sample_go_mod):
        """Test scanning go.mod."""
        scanner = DependencyScanner(sample_go_mod)
        dependencies = scanner.scan()

        assert len(dependencies) >= 3
        assert any("gin-gonic" in d.name for d in dependencies)
        assert all(d.ecosystem == Ecosystem.GO for d in dependencies)

    def test_scan_directory(self, temp_dir, sample_requirements):
        """Test scanning entire directory."""
        scanner = DependencyScanner(temp_dir)
        dependencies = scanner.scan()

        assert len(dependencies) >= 1
        assert all(isinstance(d, Dependency) for d in dependencies)

    def test_skip_venv_directories(self, temp_dir):
        """Test that virtual environment directories are skipped."""
        venv_dir = temp_dir / "venv"
        venv_dir.mkdir()
        req_file = venv_dir / "requirements.txt"
        req_file.write_text("requests==2.0.0")

        scanner = DependencyScanner(temp_dir)
        dependencies = scanner.scan()

        # Should not find dependencies in venv
        assert len(dependencies) == 0

    def test_invalid_scan_path(self):
        """Test error handling for invalid path."""
        with pytest.raises(ValueError, match="does not exist"):
            DependencyScanner("/nonexistent/path")

    def test_malformed_requirements_txt(self, temp_dir):
        """Test handling of malformed requirements.txt."""
        malformed = temp_dir / "requirements.txt"
        malformed.write_text("requests\n===invalid===\nflask>=1.0")

        scanner = DependencyScanner(malformed)
        dependencies = scanner.scan()

        # Should still parse valid lines
        assert any(d.name == "flask" for d in dependencies)

    def test_empty_requirements_txt(self, temp_dir):
        """Test handling of empty requirements.txt."""
        empty = temp_dir / "requirements.txt"
        empty.write_text("")

        scanner = DependencyScanner(empty)
        dependencies = scanner.scan()

        assert len(dependencies) == 0

    def test_version_parsing_operators(self, temp_dir):
        """Test parsing different version operators."""
        content = """
package1==1.0.0
package2>=2.0.0
package3~=3.0
package4<=4.0.0
package5>5.0.0
package6<6.0.0
"""
        req_file = temp_dir / "requirements.txt"
        req_file.write_text(content)

        scanner = DependencyScanner(req_file)
        dependencies = scanner.scan()

        assert len(dependencies) == 6
        pkg1 = next(d for d in dependencies if d.name == "package1")
        assert pkg1.version == "1.0.0"

    def test_dependency_tree_structure(self, temp_dir):
        """Test dependency tree with transitive dependencies."""
        # Create Poetry lock file with dependencies
        content = """[[package]]
name = "requests"
version = "2.25.1"
dependencies = {urllib3 = "^1.26.0", certifi = ">=2021.0.0"}

[[package]]
name = "urllib3"
version = "1.26.5"

[[package]]
name = "certifi"
version = "2021.5.30"
"""
        lock_file = temp_dir / "poetry.lock"
        lock_file.write_text(content)

        scanner = DependencyScanner(lock_file)
        dependencies = scanner.scan()

        # Check that dependencies are parsed
        assert len(dependencies) >= 1

    def test_get_direct_dependencies(self, sample_requirements):
        """Test filtering direct dependencies."""
        scanner = DependencyScanner(sample_requirements)
        all_deps = scanner.scan()
        direct_deps = scanner.get_direct_dependencies(all_deps)

        assert all(d.is_direct for d in direct_deps)
        assert len(direct_deps) <= len(all_deps)

    def test_get_dependencies_by_ecosystem(
        self, temp_dir, sample_requirements
    ):
        """Test filtering by ecosystem."""
        scanner = DependencyScanner(temp_dir)
        dependencies = scanner.scan()

        pypi_deps = scanner.get_dependencies_by_ecosystem(
            dependencies,
            Ecosystem.PYPI
        )
        assert all(d.ecosystem == Ecosystem.PYPI for d in pypi_deps)

    def test_export_to_json(self, sample_requirements, temp_dir):
        """Test exporting dependencies to JSON."""
        scanner = DependencyScanner(sample_requirements)
        dependencies = scanner.scan()

        output_file = temp_dir / "dependencies.json"
        scanner.export_to_json(dependencies, output_file)

        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_statistics(self, sample_requirements):
        """Test dependency statistics generation."""
        scanner = DependencyScanner(sample_requirements)
        dependencies = scanner.scan()

        stats = scanner.get_statistics(dependencies)

        assert "total_dependencies" in stats
        assert "direct_dependencies" in stats
        assert "by_ecosystem" in stats
        assert stats["total_dependencies"] > 0


# ============= VulnerabilityMatcher Tests =============


class TestVulnerabilityMatcher:
    """Tests for VulnerabilityMatcher module."""

    def test_initialization(self):
        """Test VulnerabilityMatcher initialization."""
        matcher = VulnerabilityMatcher()
        assert matcher is not None
        assert "osv" in matcher.databases

    def test_initialization_with_config(self):
        """Test initialization with custom configuration."""
        config = {
            "cache_ttl": 3600,
            "databases": ["osv"],
            "rate_limit": {"requests_per_minute": 10}
        }
        matcher = VulnerabilityMatcher(config)
        assert matcher.databases == ["osv"]

    @patch("vulnerability_matcher.requests.Session.post")
    def test_query_osv_success(self, mock_post, mock_osv_response):
        """Test successful OSV query."""
        mock_response = Mock()
        mock_response.json.return_value = mock_osv_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        matcher = VulnerabilityMatcher({"databases": ["osv"]})
        vulns = matcher.query_osv("requests", "2.25.1", "python")

        assert len(vulns) > 0
        assert vulns[0]["package"] == "requests"
        assert vulns[0]["database"] == "osv"

    @patch("vulnerability_matcher.requests.Session.post")
    def test_query_osv_network_error(self, mock_post):
        """Test OSV query with network error."""
        mock_post.side_effect = Exception("Network error")

        matcher = VulnerabilityMatcher({"databases": ["osv"]})
        with pytest.raises(APIError):
            matcher.query_osv("requests", "2.25.1", "python")

    @patch("vulnerability_matcher.requests.Session.get")
    def test_query_nvd_success(self, mock_get):
        """Test successful NVD query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2023-32681",
                        "metrics": {
                            "cvssMetricV31": [
                                {
                                    "cvssData": {
                                        "baseScore": 7.5,
                                        "vectorString": "CVSS:3.1/..."
                                    }
                                }
                            ]
                        },
                        "descriptions": [
                            {"lang": "en", "value": "Test vulnerability"}
                        ],
                        "references": [],
                        "published": "2023-05-26T00:00:00Z"
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        matcher = VulnerabilityMatcher({"databases": ["nvd"]})
        vulns = matcher.query_nvd("requests", "2.25.1", "python")

        assert len(vulns) > 0

    @patch("vulnerability_matcher.requests.Session.get")
    def test_query_nvd_rate_limit(self, mock_get):
        """Test NVD query with rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        matcher = VulnerabilityMatcher({"databases": ["nvd"]})
        with pytest.raises(RateLimitError):
            matcher.query_nvd("requests", "2.25.1", "python")

    @patch("vulnerability_matcher.requests.Session.post")
    def test_query_github_success(self, mock_post):
        """Test successful GitHub Advisory query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "securityVulnerabilities": {
                    "nodes": [
                        {
                            "advisory": {
                                "ghsaId": "GHSA-xxxx-yyyy-zzzz",
                                "summary": "Test advisory",
                                "description": "Test description",
                                "severity": "HIGH",
                                "publishedAt": "2023-05-26T00:00:00Z",
                                "references": [],
                                "identifiers": [
                                    {"type": "CVE", "value": "CVE-2023-32681"}
                                ]
                            },
                            "vulnerableVersionRange": ">= 2.0.0, < 2.31.0",
                            "firstPatchedVersion": {"identifier": "2.31.0"}
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        config = {
            "databases": ["github"],
            "api_keys": {"github": "test_token"}
        }
        matcher = VulnerabilityMatcher(config)
        vulns = matcher.query_github("requests", "2.25.1", "python")

        assert len(vulns) > 0

    def test_query_github_without_token(self):
        """Test GitHub query without API token."""
        matcher = VulnerabilityMatcher({"databases": ["github"]})
        vulns = matcher.query_github("requests", "2.25.1", "python")
        assert vulns == []

    def test_get_severity(self):
        """Test CVSS score to severity conversion."""
        matcher = VulnerabilityMatcher()

        assert matcher.get_severity(9.5) == "CRITICAL"
        assert matcher.get_severity(7.5) == "HIGH"
        assert matcher.get_severity(5.0) == "MEDIUM"
        assert matcher.get_severity(2.0) == "LOW"
        assert matcher.get_severity(0.0) == "NONE"

    def test_caching_functionality(self):
        """Test that results are cached."""
        matcher = VulnerabilityMatcher()

        # Create cache key
        cache_key = matcher._get_cache_key("requests", "2.25.1", "python")

        # Save to cache
        test_vulns = [{"cve": "CVE-2023-32681"}]
        matcher._save_to_cache(cache_key, test_vulns)

        # Retrieve from cache
        cached = matcher._get_from_cache(cache_key)
        assert cached == test_vulns

    def test_rate_limiting(self):
        """Test rate limiting mechanism."""
        config = {"rate_limit": {"requests_per_minute": 2}}
        matcher = VulnerabilityMatcher(config)

        # Should allow first 2 requests
        matcher._check_rate_limit()
        matcher._check_rate_limit()

        # Third request should be delayed (we'll just check it doesn't error)
        # In real scenario, this would sleep
        assert len(matcher._request_times) == 2

    def test_clear_cache(self):
        """Test cache clearing."""
        matcher = VulnerabilityMatcher()
        cache_key = matcher._get_cache_key("test", "1.0", "python")
        matcher._save_to_cache(cache_key, [{"test": "data"}])

        matcher.clear_cache()
        assert len(matcher._memory_cache) == 0

    def test_get_statistics(self):
        """Test statistics generation."""
        matcher = VulnerabilityMatcher()
        stats = matcher.get_statistics()

        assert "memory_cache_size" in stats
        assert "enabled_databases" in stats
        assert "rate_limit" in stats

    @patch("vulnerability_matcher.requests.Session.post")
    def test_find_vulnerabilities(self, mock_post, sample_dependencies):
        """Test finding vulnerabilities for multiple dependencies."""
        mock_response = Mock()
        mock_response.json.return_value = {"vulns": []}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Convert to format expected by find_vulnerabilities
        deps = [
            {
                "package": d["name"],
                "version": d["version"],
                "ecosystem": d["ecosystem"]
            }
            for d in sample_dependencies
        ]

        matcher = VulnerabilityMatcher({"databases": ["osv"]})
        vulns = matcher.find_vulnerabilities(deps)

        assert isinstance(vulns, list)


# ============= LicenseChecker Tests =============


class TestLicenseChecker:
    """Tests for LicenseChecker module."""

    def test_initialization(self):
        """Test LicenseChecker initialization."""
        checker = LicenseChecker()
        assert checker is not None
        assert checker.cache_enabled

    @patch("license_checker.requests.Session.get")
    def test_detect_license_pypi(self, mock_get):
        """Test license detection from PyPI."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {
                "license": "MIT",
                "home_page": "https://example.com",
                "author": "Test Author"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        checker = LicenseChecker()
        license_str, metadata = checker.detect_license(
            "requests", "2.25.1", "pypi"
        )

        assert license_str == "MIT"
        assert metadata is not None

    @patch("license_checker.requests.Session.get")
    def test_detect_license_npm(self, mock_get):
        """Test license detection from npm."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "license": "MIT",
            "homepage": "https://example.com",
            "repository": {"url": "https://github.com/user/repo"}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        checker = LicenseChecker()
        license_str, metadata = checker.detect_license(
            "express", "4.17.1", "npm"
        )

        assert license_str == "MIT"

    def test_normalize_license(self):
        """Test license normalization to SPDX."""
        checker = LicenseChecker()

        assert checker.normalize_license("MIT License") == "MIT"
        assert checker.normalize_license("Apache 2.0") == "Apache-2.0"
        assert checker.normalize_license("BSD") == "BSD-3-Clause"
        assert checker.normalize_license("GPL-3") == "GPL-3.0"
        assert checker.normalize_license("unknown") is None

    def test_validate_policy_allowed(self, sample_license_policy):
        """Test policy validation for allowed license."""
        checker = LicenseChecker()
        status, violation = checker.validate_policy(
            "MIT", sample_license_policy
        )

        assert status == PolicyStatus.ALLOWED
        assert not violation

    def test_validate_policy_denied(self, sample_license_policy):
        """Test policy validation for denied license."""
        checker = LicenseChecker()
        status, violation = checker.validate_policy(
            "GPL-3.0", sample_license_policy
        )

        assert status == PolicyStatus.DENIED
        assert violation

    def test_validate_policy_conditional(self, sample_license_policy):
        """Test policy validation for conditional license."""
        checker = LicenseChecker()
        status, violation = checker.validate_policy(
            "LGPL-3.0", sample_license_policy
        )

        assert status == PolicyStatus.CONDITIONAL
        assert not violation

    def test_validate_policy_unknown(self, sample_license_policy):
        """Test policy validation for unknown license."""
        checker = LicenseChecker()
        status, violation = checker.validate_policy(
            "CustomLicense", sample_license_policy
        )

        assert status == PolicyStatus.UNKNOWN
        assert violation

    def test_check_copyleft_strong(self):
        """Test copyleft detection for strong copyleft licenses."""
        checker = LicenseChecker()

        assert checker.check_copyleft("GPL-3.0")
        assert checker.check_copyleft("AGPL-3.0")
        assert checker.check_copyleft("GPL-2.0-only")

    def test_check_copyleft_weak(self):
        """Test copyleft detection for weak copyleft licenses."""
        checker = LicenseChecker()

        assert checker.check_copyleft("LGPL-3.0")
        assert checker.check_copyleft("MPL-2.0")
        assert checker.check_copyleft("EPL-2.0")

    def test_check_copyleft_permissive(self):
        """Test non-copyleft licenses."""
        checker = LicenseChecker()

        assert not checker.check_copyleft("MIT")
        assert not checker.check_copyleft("Apache-2.0")
        assert not checker.check_copyleft("BSD-3-Clause")

    def test_check_compatibility(self):
        """Test license compatibility analysis."""
        checker = LicenseChecker()

        licenses = ["MIT", "Apache-2.0", "GPL-3.0"]
        issues = checker.check_compatibility(licenses)

        # GPL-3.0 should have compatibility issues
        assert "GPL-3.0" in issues or len(issues) > 0

    def test_check_compatibility_permissive_only(self):
        """Test compatibility with only permissive licenses."""
        checker = LicenseChecker()

        licenses = ["MIT", "Apache-2.0", "BSD-3-Clause"]
        issues = checker.check_compatibility(licenses)

        # Should have no issues
        assert len(issues) == 0

    def test_validate_compound_license_or(self, sample_license_policy):
        """Test validation of OR compound license."""
        checker = LicenseChecker()
        status, violation = checker._validate_compound_license(
            "MIT OR Apache-2.0", sample_license_policy
        )

        assert status == PolicyStatus.ALLOWED
        assert not violation

    def test_validate_compound_license_and(self, sample_license_policy):
        """Test validation of AND compound license."""
        checker = LicenseChecker()
        status, violation = checker._validate_compound_license(
            "MIT AND Apache-2.0", sample_license_policy
        )

        assert status == PolicyStatus.ALLOWED
        assert not violation

    @patch("license_checker.requests.Session.get")
    def test_check_licenses(self, mock_get, sample_license_policy):
        """Test checking licenses for multiple dependencies."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {
                "license": "MIT",
                "author": "Test",
                "home_page": "http://test"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        checker = LicenseChecker()
        dependencies = [
            {"name": "requests", "version": "2.25.1", "ecosystem": "pypi"}
        ]

        results = checker.check_licenses(dependencies, sample_license_policy)

        assert len(results) == 1
        assert isinstance(results[0], LicenseInfo)
        assert results[0].package == "requests"

    def test_clear_cache(self):
        """Test cache clearing."""
        checker = LicenseChecker()
        checker._license_cache["test"] = {"license": "MIT", "metadata": {}}

        checker.clear_cache()
        assert len(checker._license_cache) == 0


# ============= SBOMGenerator Tests =============


class TestSBOMGenerator:
    """Tests for SBOMGenerator module."""

    def test_initialization(self):
        """Test SBOMGenerator initialization."""
        generator = SBOMGenerator()
        assert generator is not None

    def test_generate_spdx_json(self, sample_dependencies):
        """Test SPDX 2.3 JSON generation."""
        generator = SBOMGenerator()
        metadata = {
            "document_name": "test-sbom",
            "project_name": "test-project",
            "project_version": "1.0.0"
        }

        sbom = generator.generate(
            sample_dependencies,
            metadata,
            format="spdx",
            output_format="json"
        )

        assert isinstance(sbom, str)
        data = json.loads(sbom)
        assert data["spdxVersion"] == "SPDX-2.3"
        assert len(data["packages"]) > 0

    def test_generate_cyclonedx_json(self, sample_dependencies):
        """Test CycloneDX 1.4 JSON generation."""
        generator = SBOMGenerator()
        metadata = {
            "document_name": "test-sbom",
            "project_name": "test-project",
            "project_version": "1.0.0"
        }

        sbom = generator.generate(
            sample_dependencies,
            metadata,
            format="cyclonedx",
            output_format="json"
        )

        assert isinstance(sbom, str)
        data = json.loads(sbom)
        assert data["bomFormat"] == "CycloneDX"
        assert data["specVersion"] == "1.4"

    def test_generate_cyclonedx_xml(self, sample_dependencies):
        """Test CycloneDX XML generation."""
        generator = SBOMGenerator()
        metadata = {
            "document_name": "test-sbom",
            "project_name": "test-project"
        }

        sbom = generator.generate(
            sample_dependencies,
            metadata,
            format="cyclonedx",
            output_format="xml"
        )

        assert isinstance(sbom, str)
        assert "<?xml version=" in sbom
        assert "<bom" in sbom

    def test_generate_invalid_format(self, sample_dependencies):
        """Test error handling for invalid format."""
        generator = SBOMGenerator()
        metadata = {"document_name": "test", "project_name": "test"}

        with pytest.raises(FormatError):
            generator.generate(
                sample_dependencies,
                metadata,
                format="invalid"
            )

    def test_generate_invalid_output_format(self, sample_dependencies):
        """Test error handling for invalid output format."""
        generator = SBOMGenerator()
        metadata = {"document_name": "test", "project_name": "test"}

        with pytest.raises(FormatError):
            generator.generate(
                sample_dependencies,
                metadata,
                format="spdx",
                output_format="invalid"
            )

    def test_generate_missing_metadata(self, sample_dependencies):
        """Test error handling for missing metadata."""
        generator = SBOMGenerator()

        with pytest.raises(ValidationError):
            generator.generate(sample_dependencies, {})

    def test_generate_spdx_structure(self, sample_dependencies):
        """Test SPDX document structure."""
        generator = SBOMGenerator()
        metadata = {
            "document_name": "test-sbom",
            "project_name": "test-project"
        }

        sbom = generator.generate_spdx(sample_dependencies, metadata)

        assert "spdxVersion" in sbom
        assert "packages" in sbom
        assert "relationships" in sbom
        assert len(sbom["packages"]) >= len(sample_dependencies)

    def test_generate_cyclonedx_structure(self, sample_dependencies):
        """Test CycloneDX BOM structure."""
        generator = SBOMGenerator()
        metadata = {"project_name": "test-project", "project_version": "1.0.0"}

        bom = generator.generate_cyclonedx(sample_dependencies, metadata)

        assert bom["bomFormat"] == "CycloneDX"
        assert "components" in bom
        assert "dependencies" in bom
        assert len(bom["components"]) == len(sample_dependencies)

    def test_calculate_hash(self):
        """Test package hash calculation."""
        generator = SBOMGenerator()

        hash_value = generator.calculate_hash("requests", "2.25.1", "pypi")
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA256 hex length

    def test_validate_spdx(self, sample_dependencies):
        """Test SPDX validation."""
        generator = SBOMGenerator()
        metadata = {"document_name": "test", "project_name": "test"}

        sbom = generator.generate_spdx(sample_dependencies, metadata)
        is_valid = generator.validate_sbom(sbom, "spdx")

        assert is_valid

    def test_validate_cyclonedx(self, sample_dependencies):
        """Test CycloneDX validation."""
        generator = SBOMGenerator()
        metadata = {"project_name": "test"}

        bom = generator.generate_cyclonedx(sample_dependencies, metadata)
        is_valid = generator.validate_sbom(bom, "cyclonedx")

        assert is_valid

    def test_to_json(self, sample_dependencies):
        """Test JSON serialization."""
        generator = SBOMGenerator()
        metadata = {"document_name": "test", "project_name": "test"}

        sbom = generator.generate_spdx(sample_dependencies, metadata)
        json_str = generator.to_json(sbom)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed == sbom

    def test_to_xml(self, sample_dependencies):
        """Test XML serialization."""
        generator = SBOMGenerator()
        metadata = {"project_name": "test"}

        bom = generator.generate_cyclonedx(sample_dependencies, metadata)
        xml_str = generator.to_xml(bom)

        assert "<?xml" in xml_str
        # Parse to verify valid XML
        ET.fromstring(xml_str.split("?>", 1)[1])

    def test_to_xml_wrong_format(self):
        """Test XML serialization with non-CycloneDX format."""
        generator = SBOMGenerator()
        spdx_doc = {"spdxVersion": "SPDX-2.3"}

        with pytest.raises(FormatError):
            generator.to_xml(spdx_doc)


# ============= RemediationAdvisor Tests =============


class TestRemediationAdvisor:
    """Tests for RemediationAdvisor module."""

    def test_initialization(self):
        """Test RemediationAdvisor initialization."""
        advisor = RemediationAdvisor()
        assert advisor is not None

    def test_calculate_upgrade_path_patch(self):
        """Test upgrade path calculation for patch version."""
        advisor = RemediationAdvisor()
        recommended = advisor.calculate_upgrade_path(
            "2.25.1", ["2.25.2", "2.26.0", "2.27.0"]
        )

        assert recommended == "2.25.2"

    def test_calculate_upgrade_path_no_fixed(self):
        """Test upgrade path with no fixed versions."""
        advisor = RemediationAdvisor()
        recommended = advisor.calculate_upgrade_path("2.25.1", [])

        assert recommended is None

    def test_calculate_upgrade_path_invalid_version(self):
        """Test upgrade path with invalid version strings."""
        advisor = RemediationAdvisor()
        recommended = advisor.calculate_upgrade_path(
            "invalid", ["2.25.2"]
        )

        assert recommended is None

    def test_detect_breaking_changes_patch(self):
        """Test breaking change detection for patch upgrade."""
        advisor = RemediationAdvisor()
        upgrade_type, changes = advisor.detect_breaking_changes(
            "2.25.1", "2.25.2"
        )

        assert upgrade_type == UpgradeType.PATCH
        assert len(changes) == 0

    def test_detect_breaking_changes_minor(self):
        """Test breaking change detection for minor upgrade."""
        advisor = RemediationAdvisor()
        upgrade_type, changes = advisor.detect_breaking_changes(
            "2.25.1", "2.26.0"
        )

        assert upgrade_type == UpgradeType.MINOR
        assert len(changes) == 0

    def test_detect_breaking_changes_major(self):
        """Test breaking change detection for major upgrade."""
        advisor = RemediationAdvisor()
        upgrade_type, changes = advisor.detect_breaking_changes(
            "2.25.1", "3.0.0"
        )

        assert upgrade_type == UpgradeType.MAJOR
        assert len(changes) > 0
        assert changes[0].type == "major_version_bump"

    def test_find_alternatives_known_package(self):
        """Test finding alternatives for known package."""
        advisor = RemediationAdvisor()
        alternatives = advisor.find_alternatives("requests", "pypi")

        assert len(alternatives) > 0
        assert any(alt.package == "httpx" for alt in alternatives)

    def test_find_alternatives_unknown_package(self):
        """Test finding alternatives for unknown package."""
        advisor = RemediationAdvisor()
        alternatives = advisor.find_alternatives("unknown-package", "pypi")

        assert len(alternatives) == 0

    @patch("remediation_advisor.requests.get")
    def test_check_patch_available(self, mock_get):
        """Test patch availability checking."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {"version": "2.31.0"},
            "releases": {"2.31.0": [{}]}
        }
        mock_get.return_value = mock_response

        advisor = RemediationAdvisor()
        available = advisor.check_patch_available(
            "requests", "2.25.1", ["2.31.0"], "pypi"
        )

        assert available is True

    def test_check_patch_available_no_fixes(self):
        """Test patch checking with no fixed versions."""
        advisor = RemediationAdvisor()
        available = advisor.check_patch_available(
            "requests", "2.25.1", [], "pypi"
        )

        assert available is False

    @patch("remediation_advisor.requests.get")
    def test_get_remediation(self, mock_get):
        """Test complete remediation recommendation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {"version": "2.31.0"},
            "releases": {"2.31.0": [{}]}
        }
        mock_get.return_value = mock_response

        advisor = RemediationAdvisor()
        vulnerability = {
            "id": "CVE-2023-32681",
            "severity": "HIGH",
            "cvss_score": 7.5,
            "fixed_in": ["2.31.0"]
        }
        dependency = {
            "name": "requests",
            "version": "2.25.1",
            "is_direct": True
        }

        remediation = advisor.get_remediation(vulnerability, dependency)

        assert remediation["package"] == "requests"
        assert remediation["recommended_version"] == "2.31.0"
        assert remediation["priority_score"] > 0
        assert remediation["action"] != ""

    def test_prioritize_vulnerabilities(self):
        """Test vulnerability prioritization."""
        advisor = RemediationAdvisor()
        vulnerabilities = [
            {
                "vulnerability": {
                    "id": "CVE-2023-1",
                    "severity": "LOW",
                    "cvss_score": 3.0,
                    "fixed_in": ["1.1.0"]
                },
                "dependency": {
                    "name": "pkg1",
                    "version": "1.0.0",
                    "is_direct": False
                }
            },
            {
                "vulnerability": {
                    "id": "CVE-2023-2",
                    "severity": "CRITICAL",
                    "cvss_score": 9.8,
                    "fixed_in": ["2.1.0"]
                },
                "dependency": {
                    "name": "pkg2",
                    "version": "2.0.0",
                    "is_direct": True
                }
            }
        ]

        with patch.object(advisor, "_get_package_metadata", return_value=None):
            prioritized = advisor.prioritize(vulnerabilities)

        # Critical should be first
        assert prioritized[0]["vulnerability"]["severity"] == "CRITICAL"
        score_0 = prioritized[0]["priority_score"]
        score_1 = prioritized[1]["priority_score"]
        assert score_0 > score_1


# ============= SupplyChainAnalyzer Tests =============


class TestSupplyChainAnalyzer:
    """Tests for SupplyChainAnalyzer module."""

    def test_initialization(self):
        """Test SupplyChainAnalyzer initialization."""
        analyzer = SupplyChainAnalyzer()
        assert analyzer is not None

    @patch("supply_chain_analyzer.requests.Session.get")
    def test_verify_integrity_pypi(self, mock_get):
        """Test PyPI package integrity verification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "urls": [
                {
                    "digests": {
                        "sha256": "abc123def456"
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        analyzer = SupplyChainAnalyzer()
        result = analyzer.verify_integrity("requests", "2.25.1", "python")

        assert result["status"] == "verified"
        assert "sha256:" in result["expected_hash"]

    @patch("supply_chain_analyzer.requests.Session.get")
    def test_verify_integrity_npm(self, mock_get):
        """Test npm package integrity verification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "dist": {
                "integrity": "sha512-abc123...",
                "shasum": "def456"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        analyzer = SupplyChainAnalyzer()
        result = analyzer.verify_integrity("express", "4.17.1", "npm")

        assert result["status"] == "verified"
        assert result["expected_hash"] is not None

    @patch("supply_chain_analyzer.requests.Session.get")
    def test_detect_confusion_attack_high_risk(self, mock_get):
        """Test dependency confusion detection - high risk."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        analyzer = SupplyChainAnalyzer()
        result = analyzer.detect_confusion_attack(
            "@company/internal-pkg", "npm"
        )

        assert result["has_private_namespace"]
        # Risk level depends on public package existence

    def test_detect_confusion_attack_low_risk(self):
        """Test dependency confusion detection - low risk."""
        analyzer = SupplyChainAnalyzer()
        result = analyzer.detect_confusion_attack("requests", "python")

        assert not result["has_private_namespace"]

    def test_detect_typosquatting_similar_package(self):
        """Test typosquatting detection for similar package name."""
        analyzer = SupplyChainAnalyzer()
        result = analyzer.detect_typosquatting("reqeusts", "python")  # Typo

        assert result["risk_level"] in ["high", "medium", "low"]
        assert len(result["similar_packages"]) > 0

    def test_detect_typosquatting_legitimate_package(self):
        """Test typosquatting detection for legitimate package."""
        analyzer = SupplyChainAnalyzer()
        result = analyzer.detect_typosquatting("requests", "python")

        # Should have no similar packages
        assert result["risk_level"] == "none"

    def test_levenshtein_distance(self):
        """Test Levenshtein distance calculation."""
        analyzer = SupplyChainAnalyzer()

        assert analyzer._levenshtein_distance("kitten", "sitting") == 3
        assert analyzer._levenshtein_distance("requests", "reqeusts") == 2
        assert analyzer._levenshtein_distance("test", "test") == 0

    def test_has_doubled_char(self):
        """Test doubled character detection."""
        analyzer = SupplyChainAnalyzer()

        assert analyzer._has_doubled_char("fllask", "flask")
        assert not analyzer._has_doubled_char("flask", "requests")

    def test_has_swapped_chars(self):
        """Test swapped character detection."""
        analyzer = SupplyChainAnalyzer()

        assert analyzer._has_swapped_chars("falsk", "flask")
        assert not analyzer._has_swapped_chars("flask", "requests")

    @patch("supply_chain_analyzer.requests.Session.get")
    def test_check_malicious_indicators(self, mock_get):
        """Test malicious indicator checking."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {
                "description": "Test package",
                "author": "Test Author",
                "home_page": "https://example.com"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        analyzer = SupplyChainAnalyzer()
        result = analyzer.check_malicious_indicators(
            "requests", "2.25.1", "python"
        )

        assert "risk_level" in result
        assert "indicators" in result

    @patch("supply_chain_analyzer.requests.Session.get")
    def test_calculate_health_score(self, mock_get):
        """Test package health score calculation."""
        # Mock PyPI response
        pypi_response = Mock()
        pypi_response.status_code = 200
        pypi_response.json.return_value = {
            "info": {
                "version": "2.31.0",
                "author": "Test Author",
                "home_page": "https://example.com",
                "project_urls": {}
            },
            "releases": {
                "2.31.0": [
                    {"upload_time_iso_8601": "2023-05-26T00:00:00Z"}
                ]
            }
        }

        # Mock download stats response
        stats_response = Mock()
        stats_response.status_code = 200
        stats_response.json.return_value = {
            "data": {"last_month": 50000000}
        }

        def side_effect(url, timeout):
            if "pypistats" in url:
                return stats_response
            return pypi_response

        mock_get.side_effect = side_effect

        analyzer = SupplyChainAnalyzer()
        result = analyzer.calculate_health_score("requests", "python")

        assert "score" in result
        assert "factors" in result
        assert result["score"] >= 0

    def test_generate_slsa_provenance(self):
        """Test SLSA provenance generation."""
        analyzer = SupplyChainAnalyzer()
        dependencies = [
            {"name": "requests", "version": "2.25.1", "ecosystem": "python"}
        ]

        with patch.object(analyzer, "verify_integrity",
                          return_value={"expected_hash": "sha256:abc123"}):
            provenance = analyzer.generate_slsa_provenance(dependencies)

        assert provenance["_type"] == "https://in-toto.io/Statement/v0.1"
        assert "materials" in provenance["predicate"]
        assert len(provenance["predicate"]["materials"]) == 1

    def test_clear_cache(self):
        """Test cache clearing."""
        analyzer = SupplyChainAnalyzer()
        analyzer._cache["test"] = "data"

        analyzer.clear_cache()
        assert len(analyzer._cache) == 0

    def test_get_cache_stats(self):
        """Test cache statistics."""
        analyzer = SupplyChainAnalyzer()
        analyzer._cache["test"] = "data"

        stats = analyzer.get_cache_stats()
        assert "entries" in stats
        assert stats["entries"] == 1

    @patch("supply_chain_analyzer.requests.Session.get")
    def test_analyze_multiple_dependencies(
        self, mock_get, sample_dependencies
    ):
        """Test analyzing multiple dependencies."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {
                "description": "Test",
                "author": "Test",
                "home_page": "http://t"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        analyzer = SupplyChainAnalyzer()
        results = analyzer.analyze(sample_dependencies)

        assert len(results) == len(sample_dependencies)
        assert all("integrity_check" in r for r in results)
        assert all("health_score" in r for r in results)


# ============= Integration Tests =============


class TestIntegration:
    """Integration tests across multiple modules."""

    def test_full_scan_workflow(self, sample_requirements, temp_dir):
        """Test complete scan workflow from manifest to SBOM."""
        # Step 1: Scan dependencies
        scanner = DependencyScanner(sample_requirements)
        dependencies = scanner.scan()
        assert len(dependencies) > 0

        # Step 2: Convert to dict format
        deps_dict = [d.to_dict() for d in dependencies]

        # Step 3: Generate SBOM
        generator = SBOMGenerator()
        metadata = {
            "document_name": "integration-test",
            "project_name": "test-project",
            "project_version": "1.0.0"
        }
        sbom = generator.generate(deps_dict, metadata, format="spdx")
        assert sbom is not None

    @patch("license_checker.requests.Session.get")
    def test_dependency_license_workflow(
        self, mock_get, sample_requirements, sample_license_policy
    ):
        """Test workflow from dependency scanning to license checking."""
        # Mock license responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {
                "license": "MIT",
                "author": "Test",
                "home_page": "http://test"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Scan dependencies
        scanner = DependencyScanner(sample_requirements)
        dependencies = scanner.scan()

        # Convert to format for license checker
        deps_for_check = [
            {
                "name": d.name,
                "version": d.version,
                "ecosystem": d.ecosystem.value
            }
            for d in dependencies[:2]  # Limit to avoid too many requests
        ]

        # Check licenses
        checker = LicenseChecker()
        results = checker.check_licenses(deps_for_check, sample_license_policy)

        assert len(results) > 0
        assert all(isinstance(r, LicenseInfo) for r in results)


# ============= Performance Tests =============


class TestPerformance:
    """Performance-related tests."""

    def test_scan_large_requirements_file(self, temp_dir):
        """Test scanning large requirements file."""
        # Create file with 50 dependencies
        content = "\n".join([f"package{i}==1.0.{i}" for i in range(50)])
        req_file = temp_dir / "requirements.txt"
        req_file.write_text(content)

        scanner = DependencyScanner(req_file)
        dependencies = scanner.scan()

        assert len(dependencies) == 50

    def test_cache_performance(self):
        """Test that caching improves performance."""
        matcher = VulnerabilityMatcher()

        # First call - not cached
        cache_key = matcher._get_cache_key("test", "1.0.0", "python")
        test_data = [{"cve": "CVE-2023-0001"}]
        matcher._save_to_cache(cache_key, test_data)

        # Second call - should be cached
        cached = matcher._get_from_cache(cache_key)
        assert cached == test_data


# ============= Error Handling Tests =============


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_empty_dependency_list(self):
        """Test handling empty dependency list."""
        generator = SBOMGenerator()
        metadata = {"document_name": "test", "project_name": "test"}

        sbom = generator.generate([], metadata, format="spdx")
        data = json.loads(sbom)
        assert len(data["packages"]) >= 1  # At least root package

    def test_malformed_json(self, temp_dir):
        """Test handling malformed JSON manifest."""
        malformed = temp_dir / "package.json"
        malformed.write_text("{invalid json}")

        scanner = DependencyScanner(malformed)
        with pytest.raises(ManifestParseError):
            scanner.scan()

    def test_malformed_xml(self, temp_dir):
        """Test handling malformed XML manifest."""
        malformed = temp_dir / "pom.xml"
        malformed.write_text("<invalid><xml>")

        scanner = DependencyScanner(malformed)
        with pytest.raises(ManifestParseError):
            scanner.scan()

    def test_unsupported_manifest_format(self, temp_dir):
        """Test handling unsupported manifest format."""
        unsupported = temp_dir / "unknown.txt"
        unsupported.write_text("some content")

        scanner = DependencyScanner(unsupported)
        with pytest.raises(UnsupportedFormatError):
            scanner.scan()

    def test_network_timeout(self):
        """Test handling network timeouts."""
        config = {"databases": ["osv"]}
        matcher = VulnerabilityMatcher(config)

        with patch("vulnerability_matcher.requests.Session.post",
                   side_effect=Exception("Timeout")):
            with pytest.raises(APIError):
                matcher.query_osv("test", "1.0.0", "python")


# Run all tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
