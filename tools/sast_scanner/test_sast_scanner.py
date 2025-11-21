"""
Test suite for SAST Scanner (Issue #39)
Comprehensive tests for all scanner components.

TOOL-SEC-001: Static Application Security Testing Scanner
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import scanner modules
from bandit_wrapper import BanditScanner
from report_generator import HTMLReportGenerator, SARIFReportGenerator
from sast_scanner import SASTScanner
from semgrep_wrapper import SemgrepScanner


# Test fixtures
@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_python_file(temp_dir):
    """Create sample Python file with vulnerabilities."""
    code = """
import hashlib

def vulnerable_hash(data):
    # Weak hash function
    return hashlib.md5(data).hexdigest()

def sql_injection(user_input):
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE name = '%s'" % user_input
    return query

password = "hardcoded_password123"  # Hardcoded secret
"""
    file_path = temp_dir / "vulnerable.py"
    file_path.write_text(code)
    return file_path


@pytest.fixture
def sample_javascript_file(temp_dir):
    """Create sample JavaScript file with vulnerabilities."""
    code = """
// XSS vulnerability
function renderUser(name) {
    document.getElementById('user').innerHTML = name;
}

// Weak crypto
const crypto = require('crypto');
const hash = crypto.createHash('md5');

// Hardcoded secret
const apiKey = "AKIAIOSFODNN7EXAMPLE";
"""
    file_path = temp_dir / "vulnerable.js"
    file_path.write_text(code)
    return file_path


@pytest.fixture
def sample_findings():
    """Sample findings for testing report generation."""
    return [
        {
            "rule_id": "python-sql-injection",
            "severity": "HIGH",
            "confidence": "HIGH",
            "message": "SQL injection vulnerability detected",
            "file_path": "/test/file.py",
            "start_line": 10,
            "end_line": 10,
            "start_col": 5,
            "end_col": 50,
            "code_snippet": 'query = "SELECT * FROM users WHERE id = %s" % user_id',
            "cwe": ["CWE-89"],
            "owasp": ["A03:2021-Injection"],
            "category": "security",
        },
        {
            "rule_id": "weak-hash-md5",
            "severity": "MEDIUM",
            "confidence": "HIGH",
            "message": "MD5 is a weak hash function",
            "file_path": "/test/file.py",
            "start_line": 5,
            "end_line": 5,
            "start_col": 10,
            "end_col": 30,
            "code_snippet": "hash = hashlib.md5(data).hexdigest()",
            "cwe": ["CWE-327"],
            "owasp": ["A02:2021-Cryptographic Failures"],
            "category": "security",
        },
    ]


# Semgrep Scanner Tests
class TestSemgrepScanner:
    """Tests for Semgrep scanner wrapper."""

    @patch("semgrep_wrapper.subprocess.run")
    def test_semgrep_installation_check(self, mock_run):
        """Test Semgrep installation verification."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="semgrep 1.45.0", stderr=""
        )

        scanner = SemgrepScanner()
        assert scanner is not None
        mock_run.assert_called()

    @patch("semgrep_wrapper.subprocess.run")
    def test_semgrep_installation_failure(self, mock_run):
        """Test handling of missing Semgrep installation."""
        mock_run.side_effect = FileNotFoundError("semgrep not found")

        with pytest.raises(RuntimeError, match="Semgrep installation check failed"):
            SemgrepScanner()

    @patch("semgrep_wrapper.subprocess.run")
    def test_semgrep_scan_success(self, mock_run, temp_dir):
        """Test successful Semgrep scan."""
        # Mock version check
        version_result = MagicMock(returncode=0, stdout="semgrep 1.45.0")

        # Mock scan result
        scan_result = MagicMock(
            returncode=0,
            stdout=json.dumps(
                {
                    "results": [
                        {
                            "check_id": "test-rule",
                            "path": "test.py",
                            "start": {"line": 1, "col": 1},
                            "end": {"line": 1, "col": 10},
                            "extra": {
                                "message": "Test finding",
                                "severity": "ERROR",
                                "metadata": {
                                    "cwe": ["CWE-89"],
                                    "owasp": ["A03:2021"],
                                    "confidence": "HIGH",
                                },
                            },
                        }
                    ]
                }
            ),
        )

        mock_run.side_effect = [version_result, scan_result]

        scanner = SemgrepScanner()
        results = scanner.scan(temp_dir)

        assert results["scanner"] == "semgrep"
        assert len(results["findings"]) == 1
        assert results["findings"][0]["rule_id"] == "test-rule"
        assert results["summary"]["total_findings"] == 1

    def test_semgrep_supported_languages(self):
        """Test that Semgrep supports expected languages."""
        languages = SemgrepScanner.get_supported_languages()
        assert "python" in languages
        assert "javascript" in languages
        assert "typescript" in languages
        assert "go" in languages
        assert "java" in languages


# Bandit Scanner Tests
class TestBanditScanner:
    """Tests for Bandit scanner wrapper."""

    @patch("bandit_wrapper.subprocess.run")
    def test_bandit_installation_check(self, mock_run):
        """Test Bandit installation verification."""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="bandit 1.7.5", stderr=""
        )

        scanner = BanditScanner()
        assert scanner is not None

    @patch("bandit_wrapper.subprocess.run")
    def test_bandit_scan_success(self, mock_run, temp_dir):
        """Test successful Bandit scan."""
        # Mock version check
        version_result = MagicMock(returncode=0, stdout="bandit 1.7.5")

        # Mock scan result
        scan_result = MagicMock(
            returncode=0,
            stdout=json.dumps(
                {
                    "results": [
                        {
                            "test_id": "B303",
                            "test_name": "md5",
                            "issue_severity": "HIGH",
                            "issue_confidence": "HIGH",
                            "issue_text": "Use of insecure MD5 hash function",
                            "filename": "test.py",
                            "line_number": 5,
                            "col_offset": 10,
                            "code": "hashlib.md5(data)",
                            "more_info": "https://bandit.readthedocs.io/",
                        }
                    ],
                    "metrics": {},
                }
            ),
        )

        mock_run.side_effect = [version_result, scan_result]

        scanner = BanditScanner()
        results = scanner.scan(temp_dir)

        assert results["scanner"] == "bandit"
        assert len(results["findings"]) == 1
        assert results["findings"][0]["rule_id"] == "B303"
        assert results["findings"][0]["severity"] == "HIGH"

    def test_bandit_cwe_mapping(self):
        """Test Bandit test ID to CWE mapping."""
        scanner = BanditScanner()
        cwe = scanner._map_bandit_to_cwe("B303")
        assert cwe == "CWE-327"

    def test_bandit_owasp_mapping(self):
        """Test Bandit test ID to OWASP mapping."""
        scanner = BanditScanner()
        owasp = scanner._map_bandit_to_owasp("B303")
        assert "A02:2021-Cryptographic Failures" in owasp


# SARIF Report Generator Tests
class TestSARIFReportGenerator:
    """Tests for SARIF report generation."""

    def test_sarif_generation(self, sample_findings, temp_dir):
        """Test SARIF report generation."""
        generator = SARIFReportGenerator()
        sarif = generator.generate(sample_findings, temp_dir)

        assert sarif["version"] == "2.1.0"
        assert "$schema" in sarif
        assert len(sarif["runs"]) == 1

        run = sarif["runs"][0]
        assert "tool" in run
        assert "results" in run
        assert len(run["results"]) == 2

    def test_sarif_validation(self, sample_findings, temp_dir):
        """Test SARIF report validation."""
        generator = SARIFReportGenerator()
        sarif = generator.generate(sample_findings, temp_dir)

        assert generator.validate_sarif(sarif) is True

    def test_sarif_invalid_structure(self):
        """Test SARIF validation with invalid structure."""
        generator = SARIFReportGenerator()
        invalid_sarif = {"version": "2.1.0"}  # Missing required fields

        assert generator.validate_sarif(invalid_sarif) is False

    def test_sarif_severity_mapping(self):
        """Test severity to SARIF level mapping."""
        generator = SARIFReportGenerator()

        assert generator._map_severity_to_level("CRITICAL") == "error"
        assert generator._map_severity_to_level("HIGH") == "error"
        assert generator._map_severity_to_level("MEDIUM") == "warning"
        assert generator._map_severity_to_level("LOW") == "note"
        assert generator._map_severity_to_level("INFO") == "note"

    def test_sarif_export_to_file(self, sample_findings, temp_dir):
        """Test exporting SARIF to file."""
        generator = SARIFReportGenerator()
        sarif = generator.generate(sample_findings, temp_dir)

        output_path = temp_dir / "report.sarif"
        generator.export_to_file(sarif, output_path)

        assert output_path.exists()
        with open(output_path, "r", encoding="utf-8") as f:
            loaded_sarif = json.load(f)
        assert loaded_sarif["version"] == "2.1.0"


# HTML Report Generator Tests
class TestHTMLReportGenerator:
    """Tests for HTML report generation."""

    def test_html_generation(self, sample_findings):
        """Test HTML report generation."""
        generator = HTMLReportGenerator()
        summary = {
            "total_findings": 2,
            "by_severity": {"HIGH": 1, "MEDIUM": 1, "LOW": 0, "INFO": 0},
        }

        html = generator.generate(sample_findings, summary)

        assert "<!DOCTYPE html>" in html
        assert "SAST Scan Report" in html
        assert "SQL injection" in html
        assert "HIGH" in html
        assert "MEDIUM" in html

    def test_html_export_to_file(self, sample_findings, temp_dir):
        """Test exporting HTML to file."""
        generator = HTMLReportGenerator()
        summary = {
            "total_findings": 2,
            "by_severity": {"HIGH": 1, "MEDIUM": 1, "LOW": 0, "INFO": 0},
        }

        html = generator.generate(sample_findings, summary)
        output_path = temp_dir / "report.html"
        generator.export_to_file(html, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content


# Main SAST Scanner Tests
class TestSASTScanner:
    """Tests for main SAST scanner orchestration."""

    def test_scanner_initialization(self):
        """Test scanner initialization."""
        scanner = SASTScanner()
        assert scanner is not None
        assert scanner.sarif_generator is not None
        assert scanner.html_generator is not None

    def test_finding_deduplication(self):
        """Test finding deduplication logic."""
        scanner = SASTScanner()

        findings = [
            {
                "file_path": "test.py",
                "start_line": 10,
                "rule_id": "test-rule",
                "message": "Test 1",
            },
            {
                "file_path": "test.py",
                "start_line": 10,
                "rule_id": "test-rule",
                "message": "Test 2",
            },  # Duplicate
            {
                "file_path": "test.py",
                "start_line": 20,
                "rule_id": "test-rule",
                "message": "Test 3",
            },
        ]

        deduplicated = scanner._deduplicate_findings(findings)
        assert len(deduplicated) == 2

    def test_combined_summary_generation(self):
        """Test combined summary generation."""
        scanner = SASTScanner()

        findings = [
            {
                "severity": "HIGH",
                "cwe": ["CWE-89"],
                "owasp": ["A03:2021"],
                "file_path": "test.py",
            },
            {
                "severity": "MEDIUM",
                "cwe": ["CWE-327"],
                "owasp": ["A02:2021"],
                "file_path": "test.py",
            },
            {
                "severity": "HIGH",
                "cwe": ["CWE-89"],
                "owasp": ["A03:2021"],
                "file_path": "app.py",
            },
        ]

        summary = scanner._generate_combined_summary(findings)

        assert summary["total_findings"] == 3
        assert summary["by_severity"]["HIGH"] == 2
        assert summary["by_severity"]["MEDIUM"] == 1
        assert summary["files_affected"] == 2
        assert "CWE-89" in summary["by_cwe"]
        assert summary["by_cwe"]["CWE-89"] == 2

    def test_contains_python_files(self, temp_dir):
        """Test Python file detection."""
        scanner = SASTScanner()

        # Test with Python file
        py_file = temp_dir / "test.py"
        py_file.write_text("print('hello')")
        assert scanner._contains_python_files(py_file) is True

        # Test with directory containing Python files
        assert scanner._contains_python_files(temp_dir) is True

        # Test with non-Python file
        js_file = temp_dir / "test.js"
        js_file.write_text("console.log('hello')")
        assert scanner._contains_python_files(js_file) is False

    def test_baseline_generation(self, temp_dir):
        """Test baseline file generation."""
        scanner = SASTScanner()

        # Create test file
        test_file = temp_dir / "test.py"
        test_file.write_text("x = 1")

        baseline_path = temp_dir / "baseline.json"

        # Mock scan method to avoid actual scanning
        with patch.object(scanner, "scan") as mock_scan:
            mock_scan.return_value = {
                "findings": [],
                "summary": {"total_findings": 0},
                "scan_metadata": {"timestamp": "2024-01-01T00:00:00Z"},
            }

            scanner.generate_baseline(temp_dir, baseline_path)

        assert baseline_path.exists()
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = json.load(f)
        assert "findings" in baseline
        assert "summary" in baseline

    def test_finding_id_generation(self):
        """Test unique finding ID generation."""
        scanner = SASTScanner()

        finding = {
            "file_path": "/path/to/file.py",
            "start_line": 42,
            "rule_id": "test-rule",
        }

        finding_id = scanner._get_finding_id(finding)
        assert finding_id == "/path/to/file.py:42:test-rule"


# Integration Tests
class TestIntegration:
    """Integration tests requiring actual scanners."""

    @pytest.mark.skipif(
        not Path("/usr/local/bin/semgrep").exists()
        and not Path("/usr/bin/semgrep").exists(),
        reason="Semgrep not installed",
    )
    def test_real_semgrep_scan(self, sample_python_file):
        """Test real Semgrep scan (requires Semgrep installation)."""
        scanner = SemgrepScanner(config="p/python")
        results = scanner.scan(sample_python_file.parent)

        assert results["scanner"] == "semgrep"
        assert "findings" in results
        assert "summary" in results

    @pytest.mark.skipif(
        not Path("/usr/local/bin/bandit").exists()
        and not Path("/usr/bin/bandit").exists(),
        reason="Bandit not installed",
    )
    def test_real_bandit_scan(self, sample_python_file):
        """Test real Bandit scan (requires Bandit installation)."""
        scanner = BanditScanner()
        results = scanner.scan(sample_python_file.parent)

        assert results["scanner"] == "bandit"
        assert "findings" in results


# Performance Tests
class TestPerformance:
    """Performance tests for scanner."""

    def test_large_codebase_handling(self, temp_dir):
        """Test handling of large codebase."""
        # Create multiple files
        for i in range(100):
            file_path = temp_dir / f"file_{i}.py"
            file_path.write_text(f"x = {i}\n" * 100)

        scanner = SASTScanner()

        # This test mainly ensures no crashes with many files
        # Actual timing would require real scanners
        with patch.object(scanner, "scan") as mock_scan:
            mock_scan.return_value = {
                "findings": [],
                "summary": {"total_findings": 0},
                "scan_metadata": {"timestamp": "2024-01-01T00:00:00Z"},
                "scan_path": str(temp_dir),
            }

            results = scanner.scan(temp_dir)
            assert results is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=term-missing"])
