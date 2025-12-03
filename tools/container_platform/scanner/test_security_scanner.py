"""
Test suite for Security Scanner module.

This module tests the SecurityScanner functionality including vulnerability
scanning, SBOM generation, and result caching.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from security_scanner import (
    InvalidImageNameError,
    LicenseFinding,
    Misconfiguration,
    MisconfigType,
    SBOMFormat,
    ScannerConfig,
    ScannerNotFoundError,
    ScannerType,
    ScanResult,
    SecretFinding,
    SecurityScanner,
    SeverityLevel,
    Vulnerability,
)


class TestSeverityLevel:
    """Test SeverityLevel enum."""

    def test_from_string_valid(self):
        """Test valid severity string conversion."""
        assert SeverityLevel.from_string("CRITICAL") == SeverityLevel.CRITICAL
        assert SeverityLevel.from_string("high") == SeverityLevel.HIGH
        assert SeverityLevel.from_string("Medium") == SeverityLevel.MEDIUM

    def test_from_string_invalid(self):
        """Test invalid severity string conversion."""
        assert SeverityLevel.from_string("invalid") == SeverityLevel.UNKNOWN


class TestVulnerability:
    """Test Vulnerability model."""

    def test_is_fixable(self):
        """Test fixable vulnerability detection."""
        vuln_fixed = Vulnerability(
            id="CVE-2023-0001",
            severity=SeverityLevel.HIGH,
            package_name="openssl",
            installed_version="1.0.0",
            fixed_version="1.1.0",
            scanner="trivy",
        )
        assert vuln_fixed.is_fixable() is True

        vuln_unfixed = Vulnerability(
            id="CVE-2023-0002",
            severity=SeverityLevel.HIGH,
            package_name="openssl",
            installed_version="1.0.0",
            fixed_version=None,
            scanner="trivy",
        )
        assert vuln_unfixed.is_fixable() is False

    def test_meets_threshold(self):
        """Test vulnerability severity threshold check."""
        vuln = Vulnerability(
            id="CVE-2023-0001",
            severity=SeverityLevel.HIGH,
            package_name="openssl",
            installed_version="1.0.0",
            scanner="trivy",
        )

        assert vuln.meets_threshold(SeverityLevel.LOW) is True
        assert vuln.meets_threshold(SeverityLevel.HIGH) is True
        assert vuln.meets_threshold(SeverityLevel.CRITICAL) is False


class TestScanResult:
    """Test ScanResult model."""

    def test_vulnerability_counts(self):
        """Test vulnerability count properties."""
        result = ScanResult(
            image="nginx:latest",
            vulnerabilities=[
                Vulnerability(
                    id="CVE-2023-0001",
                    severity=SeverityLevel.CRITICAL,
                    package_name="pkg1",
                    installed_version="1.0",
                    scanner="trivy",
                ),
                Vulnerability(
                    id="CVE-2023-0002",
                    severity=SeverityLevel.HIGH,
                    package_name="pkg2",
                    installed_version="1.0",
                    scanner="trivy",
                ),
                Vulnerability(
                    id="CVE-2023-0003",
                    severity=SeverityLevel.HIGH,
                    package_name="pkg3",
                    installed_version="1.0",
                    fixed_version="1.1",
                    scanner="trivy",
                ),
            ],
        )

        assert result.total_vulnerabilities == 3
        assert result.critical_count == 1
        assert result.high_count == 2
        assert result.fixable_count == 1

    def test_get_summary(self):
        """Test summary generation."""
        result = ScanResult(
            image="nginx:latest",
            vulnerabilities=[
                Vulnerability(
                    id="CVE-2023-0001",
                    severity=SeverityLevel.CRITICAL,
                    package_name="pkg1",
                    installed_version="1.0",
                    scanner="trivy",
                )
            ],
            secrets=[
                SecretFinding(
                    type="api-key",
                    file_path="/app/config.py",
                    match="***REDACTED***",
                )
            ],
        )

        summary = result.get_summary()
        assert summary["vulnerabilities"]["total"] == 1
        assert summary["vulnerabilities"]["critical"] == 1
        assert summary["secrets"] == 1

    def test_has_critical_findings(self):
        """Test critical finding detection."""
        result_with_critical = ScanResult(
            image="nginx:latest",
            vulnerabilities=[
                Vulnerability(
                    id="CVE-2023-0001",
                    severity=SeverityLevel.CRITICAL,
                    package_name="pkg1",
                    installed_version="1.0",
                    scanner="trivy",
                )
            ],
        )
        assert result_with_critical.has_critical_findings() is True

        result_without_critical = ScanResult(
            image="nginx:latest",
            vulnerabilities=[
                Vulnerability(
                    id="CVE-2023-0001",
                    severity=SeverityLevel.LOW,
                    package_name="pkg1",
                    installed_version="1.0",
                    scanner="trivy",
                )
            ],
        )
        assert result_without_critical.has_critical_findings() is False


class TestSecurityScanner:
    """Test SecurityScanner functionality."""

    @patch("security_scanner.shutil.which")
    def test_init_no_scanners(self, mock_which):
        """Test initialization with no scanners available."""
        mock_which.return_value = None

        with pytest.raises(ScannerNotFoundError):
            SecurityScanner()

    @patch("security_scanner.shutil.which")
    def test_init_with_trivy(self, mock_which):
        """Test initialization with Trivy available."""
        mock_which.side_effect = lambda x: "/usr/bin/trivy" if x == "trivy" else None

        with patch.object(SecurityScanner, "_get_scanner_version", return_value="0.50"):
            scanner = SecurityScanner()
            assert "trivy" in scanner.scanners_available

    def test_validate_image_name_empty(self):
        """Test image name validation with empty name."""
        with patch("security_scanner.shutil.which", return_value="/usr/bin/trivy"):
            with patch.object(
                SecurityScanner, "_get_scanner_version", return_value="0.50"
            ):
                scanner = SecurityScanner()

                with pytest.raises(InvalidImageNameError):
                    scanner._validate_image_name("")

    def test_validate_image_name_invalid_chars(self):
        """Test image name validation with invalid characters."""
        with patch("security_scanner.shutil.which", return_value="/usr/bin/trivy"):
            with patch.object(
                SecurityScanner, "_get_scanner_version", return_value="0.50"
            ):
                scanner = SecurityScanner()

                with pytest.raises(InvalidImageNameError):
                    scanner._validate_image_name("nginx:latest | rm -rf /")

    def test_get_cache_key(self):
        """Test cache key generation."""
        with patch("security_scanner.shutil.which", return_value="/usr/bin/trivy"):
            with patch.object(
                SecurityScanner, "_get_scanner_version", return_value="0.50"
            ):
                scanner = SecurityScanner()

                key1 = scanner._get_cache_key("nginx:latest")
                key2 = scanner._get_cache_key("nginx:latest")
                key3 = scanner._get_cache_key("ubuntu:20.04")

                assert key1 == key2  # Same image should generate same key
                assert key1 != key3  # Different images generate different keys

    def test_get_severity_list(self):
        """Test severity list generation."""
        with patch("security_scanner.shutil.which", return_value="/usr/bin/trivy"):
            with patch.object(
                SecurityScanner, "_get_scanner_version", return_value="0.50"
            ):
                config = ScannerConfig(severity_threshold=SeverityLevel.HIGH)
                scanner = SecurityScanner(config)

                severities = scanner._get_severity_list()
                assert "CRITICAL" in severities
                assert "HIGH" in severities
                assert "MEDIUM" not in severities
                assert "LOW" not in severities

    def test_aggregate_vulnerabilities(self):
        """Test vulnerability aggregation and deduplication."""
        with patch("security_scanner.shutil.which", return_value="/usr/bin/trivy"):
            with patch.object(
                SecurityScanner, "_get_scanner_version", return_value="0.50"
            ):
                scanner = SecurityScanner()

                vuln1 = Vulnerability(
                    id="CVE-2023-0001",
                    severity=SeverityLevel.HIGH,
                    package_name="openssl",
                    installed_version="1.0.0",
                    scanner="trivy",
                )

                vuln2 = Vulnerability(
                    id="CVE-2023-0001",
                    severity=SeverityLevel.HIGH,
                    package_name="openssl",
                    installed_version="1.0.0",
                    fixed_version="1.1.0",
                    scanner="grype",
                )

                result = scanner._aggregate_vulnerabilities([[vuln1], [vuln2]])

                assert len(result) == 1  # Should be deduplicated
                assert result[0].fixed_version == "1.1.0"  # Should merge info

    @patch("security_scanner.subprocess.run")
    @patch("security_scanner.shutil.which")
    def test_scan_image_trivy(self, mock_which, mock_run):
        """Test scanning with Trivy."""
        mock_which.return_value = "/usr/bin/trivy"

        # Mock Trivy output
        trivy_output = {
            "Results": [
                {
                    "Target": "nginx:latest",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2023-0001",
                            "Severity": "HIGH",
                            "PkgName": "openssl",
                            "InstalledVersion": "1.0.0",
                            "FixedVersion": "1.1.0",
                            "Title": "Test vulnerability",
                            "Description": "Test description",
                        }
                    ],
                }
            ]
        }

        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps(trivy_output), stderr=""
        )

        with patch.object(
            SecurityScanner, "_get_scanner_version", return_value="0.50"
        ):
            config = ScannerConfig(enable_cache=False)
            scanner = SecurityScanner(config)
            result = scanner.scan_image("nginx:latest")

            assert result.image == "nginx:latest"
            assert result.total_vulnerabilities == 1
            assert result.vulnerabilities[0].id == "CVE-2023-0001"

    def test_cache_operations(self):
        """Test cache save and retrieve."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            with patch("security_scanner.shutil.which", return_value="/usr/bin/trivy"):
                with patch.object(
                    SecurityScanner, "_get_scanner_version", return_value="0.50"
                ):
                    config = ScannerConfig(
                        enable_cache=True, cache_dir=cache_dir, cache_ttl=3600
                    )
                    scanner = SecurityScanner(config)

                    result = ScanResult(
                        image="nginx:latest",
                        vulnerabilities=[
                            Vulnerability(
                                id="CVE-2023-0001",
                                severity=SeverityLevel.HIGH,
                                package_name="pkg",
                                installed_version="1.0",
                                scanner="trivy",
                            )
                        ],
                    )

                    scanner._save_to_cache(result)

                    cached = scanner._get_cached_result("nginx:latest")
                    assert cached is not None
                    assert cached.image == "nginx:latest"
                    assert cached.total_vulnerabilities == 1

    def test_clear_cache(self):
        """Test cache clearing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)

            # Create dummy cache files
            (cache_dir / "cache1.json").write_text('{"test": 1}')
            (cache_dir / "cache2.json").write_text('{"test": 2}')

            with patch("security_scanner.shutil.which", return_value="/usr/bin/trivy"):
                with patch.object(
                    SecurityScanner, "_get_scanner_version", return_value="0.50"
                ):
                    config = ScannerConfig(enable_cache=True, cache_dir=cache_dir)
                    scanner = SecurityScanner(config)

                    count = scanner.clear_cache()
                    assert count == 2
                    assert len(list(cache_dir.glob("*.json"))) == 0


class TestScannerIntegration:
    """Integration tests (require actual scanners installed)."""

    @pytest.mark.skipif(
        not SecurityScanner.check_scanner_installed("trivy"),
        reason="Trivy not installed",
    )
    def test_trivy_version(self):
        """Test getting Trivy version."""
        scanner = SecurityScanner()
        version = scanner._get_scanner_version("trivy")
        assert version != "unknown"

    @pytest.mark.skipif(
        not SecurityScanner.check_scanner_installed("grype"),
        reason="Grype not installed",
    )
    def test_grype_version(self):
        """Test getting Grype version."""
        config = ScannerConfig(scanner_type=ScannerType.GRYPE)
        scanner = SecurityScanner(config)
        version = scanner._get_scanner_version("grype")
        assert version != "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
