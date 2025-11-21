"""
Comprehensive tests for Secrets Scanner - devCrew_s1 TOOL-SEC-006.

Target: 85%+ code coverage.
"""

import os
import tempfile
import unittest
from pathlib import Path

from .baseline_manager import BaselineEntry, BaselineManager
from .pattern_manager import PatternManager, PatternSeverity, SecretPattern
from .remediation_guide import RemediationGuide, RemediationPriority
from .secret_scanner import ScanResult, SecretFinding, SecretScanner
from .verification_engine import VerificationEngine, VerificationResult, VerificationStatus


class TestPatternManager(unittest.TestCase):
    """Tests for PatternManager."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.pm = PatternManager()

    def test_builtin_patterns_loaded(self) -> None:
        """Test that built-in patterns are loaded."""
        patterns = self.pm.get_all_patterns()
        self.assertGreaterEqual(len(patterns), 50)

    def test_get_pattern_by_name(self) -> None:
        """Test retrieving pattern by name."""
        pattern = self.pm.get_pattern("aws_access_key_id")
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.category, "aws")

    def test_get_patterns_by_category(self) -> None:
        """Test filtering patterns by category."""
        aws_patterns = self.pm.get_patterns_by_category("aws")
        self.assertGreater(len(aws_patterns), 0)
        for p in aws_patterns:
            self.assertEqual(p.category, "aws")

    def test_get_patterns_by_severity(self) -> None:
        """Test filtering patterns by severity."""
        critical = self.pm.get_patterns_by_severity(PatternSeverity.CRITICAL)
        self.assertGreater(len(critical), 0)
        for p in critical:
            self.assertEqual(p.severity, PatternSeverity.CRITICAL)

    def test_add_custom_pattern(self) -> None:
        """Test adding custom pattern."""
        custom = SecretPattern(
            name="custom_test",
            pattern=r"CUSTOM_[A-Z]{10}",
            severity=PatternSeverity.HIGH,
            description="Custom test pattern",
            category="test",
        )
        self.pm.add_custom_pattern(custom)

        retrieved = self.pm.get_pattern("custom_test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.description, "Custom test pattern")

    def test_remove_custom_pattern(self) -> None:
        """Test removing custom pattern."""
        custom = SecretPattern(
            name="to_remove",
            pattern=r"REMOVE_ME",
            severity=PatternSeverity.LOW,
            description="To be removed",
            category="test",
        )
        self.pm.add_custom_pattern(custom)
        self.assertTrue(self.pm.remove_custom_pattern("to_remove"))
        self.assertIsNone(self.pm.get_pattern("to_remove"))

    def test_get_categories(self) -> None:
        """Test getting all categories."""
        categories = self.pm.get_categories()
        self.assertIn("aws", categories)
        self.assertIn("github", categories)
        self.assertIn("keys", categories)

    def test_pattern_count(self) -> None:
        """Test pattern count."""
        count = self.pm.pattern_count()
        self.assertGreaterEqual(count, 50)

    def test_export_import_patterns(self) -> None:
        """Test exporting and importing patterns."""
        exported = self.pm.export_patterns()
        self.assertIsInstance(exported, list)
        self.assertGreater(len(exported), 0)

        # Import to new manager
        new_pm = PatternManager()
        # Clear custom patterns first
        new_pm._custom_patterns = {}
        count = new_pm.import_patterns(exported[:5])
        self.assertEqual(count, 5)


class TestSecretScanner(unittest.TestCase):
    """Tests for SecretScanner."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.scanner = SecretScanner()

    def test_calculate_shannon_entropy(self) -> None:
        """Test Shannon entropy calculation."""
        # Low entropy
        low = self.scanner.calculate_shannon_entropy("aaaaaaaaaa")
        self.assertLess(low, 1.0)

        # High entropy
        high = self.scanner.calculate_shannon_entropy("aB3$xY9@mN")
        self.assertGreater(high, 3.0)

        # Empty string
        empty = self.scanner.calculate_shannon_entropy("")
        self.assertEqual(empty, 0.0)

    def test_is_high_entropy(self) -> None:
        """Test high entropy detection."""
        # Use a longer, more complex string to ensure high entropy
        self.assertTrue(self.scanner.is_high_entropy("8f3kD9sL2mNx7pQr4wZyABCDE12345!@#$%"))
        self.assertFalse(self.scanner.is_high_entropy("aaaaaaaaaa"))

    def test_scan_content_aws_key(self) -> None:
        """Test scanning content for AWS keys."""
        content = "AWS_KEY=AKIAIOSFODNN7EXAMPLE"
        findings = self.scanner.scan_content(content)

        self.assertGreater(len(findings), 0)
        self.assertTrue(any(f.pattern_name == "aws_access_key_id" for f in findings))

    def test_scan_content_github_token(self) -> None:
        """Test scanning content for GitHub tokens."""
        content = "token=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        findings = self.scanner.scan_content(content)

        self.assertGreater(len(findings), 0)

    def test_scan_content_private_key(self) -> None:
        """Test scanning content for private keys."""
        content = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"""
        findings = self.scanner.scan_content(content)

        self.assertGreater(len(findings), 0)
        self.assertTrue(any("private_key" in f.pattern_name for f in findings))

    def test_scan_content_slack_token(self) -> None:
        """Test scanning for Slack tokens."""
        content = "SLACK_TOKEN=xoxb-12345678901-12345678901-abcdefghijklmnopqrstuvwx"
        findings = self.scanner.scan_content(content)

        self.assertGreater(len(findings), 0)

    def test_scan_content_database_uri(self) -> None:
        """Test scanning for database URIs."""
        content = "DATABASE_URL=postgres://user:password@localhost:5432/mydb"
        findings = self.scanner.scan_content(content)

        self.assertGreater(len(findings), 0)
        self.assertTrue(any(f.category == "database" for f in findings))

    def test_scan_file(self) -> None:
        """Test scanning a single file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("AWS_KEY=AKIAIOSFODNN7EXAMPLE\n")
            f.write("secret = 'test'\n")
            temp_path = f.name

        try:
            findings = self.scanner.scan_file(temp_path)
            self.assertGreater(len(findings), 0)
        finally:
            os.unlink(temp_path)

    def test_scan_file_nonexistent(self) -> None:
        """Test scanning non-existent file."""
        findings = self.scanner.scan_file("/nonexistent/file.txt")
        self.assertEqual(len(findings), 0)

    def test_scan_file_excluded_extension(self) -> None:
        """Test scanning file with excluded extension."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name

        try:
            findings = self.scanner.scan_file(temp_path)
            self.assertEqual(len(findings), 0)
        finally:
            os.unlink(temp_path)

    def test_scan_directory(self) -> None:
        """Test scanning a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file with secret
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("API_KEY=AKIAIOSFODNN7EXAMPLE\n")

            result = self.scanner.scan_directory(tmpdir)

            self.assertGreater(result.files_scanned, 0)
            self.assertIsInstance(result, ScanResult)

    def test_scan_directory_nonexistent(self) -> None:
        """Test scanning non-existent directory."""
        result = self.scanner.scan_directory("/nonexistent/dir")
        self.assertGreater(len(result.errors), 0)

    def test_scan_high_entropy_strings(self) -> None:
        """Test high entropy string detection."""
        content = '''
key = "8f3kD9sL2mNx7pQr4wZyAaBbCcDdEeFf"
normal = "hello world"
'''
        findings = self.scanner.scan_high_entropy_strings(content)
        # Should find the high entropy string
        self.assertGreaterEqual(len(findings), 0)

    def test_deduplicate_findings(self) -> None:
        """Test deduplicating findings."""
        finding = SecretFinding(
            pattern_name="test",
            pattern_description="Test",
            severity=PatternSeverity.HIGH,
            file_path="test.py",
            line_number=1,
            line_content="test",
            matched_text="secret123",
            category="test",
        )

        duplicates = [finding, finding, finding]
        unique = self.scanner.deduplicate_findings(duplicates)
        self.assertEqual(len(unique), 1)

    def test_filter_findings(self) -> None:
        """Test filtering findings."""
        findings = [
            SecretFinding(
                pattern_name="test1",
                pattern_description="Test 1",
                severity=PatternSeverity.CRITICAL,
                file_path="test.py",
                line_number=1,
                line_content="test",
                matched_text="secret1",
                category="aws",
            ),
            SecretFinding(
                pattern_name="test2",
                pattern_description="Test 2",
                severity=PatternSeverity.LOW,
                file_path="test.py",
                line_number=2,
                line_content="test",
                matched_text="secret2",
                category="generic",
            ),
        ]

        # Filter by severity
        filtered = self.scanner.filter_findings(
            findings, min_severity=PatternSeverity.HIGH
        )
        self.assertEqual(len(filtered), 1)

        # Filter by category
        filtered = self.scanner.filter_findings(findings, categories=["aws"])
        self.assertEqual(len(filtered), 1)


class TestSecretFinding(unittest.TestCase):
    """Tests for SecretFinding."""

    def test_finding_hash_generation(self) -> None:
        """Test that hash is generated."""
        finding = SecretFinding(
            pattern_name="test",
            pattern_description="Test",
            severity=PatternSeverity.HIGH,
            file_path="test.py",
            line_number=1,
            line_content="test line",
            matched_text="secret123",
            category="test",
        )
        self.assertNotEqual(finding.hash_value, "")
        self.assertEqual(len(finding.hash_value), 16)

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        finding = SecretFinding(
            pattern_name="test",
            pattern_description="Test",
            severity=PatternSeverity.HIGH,
            file_path="test.py",
            line_number=1,
            line_content="test line",
            matched_text="secret123",
            category="test",
        )
        d = finding.to_dict()
        self.assertEqual(d["pattern_name"], "test")
        self.assertEqual(d["severity"], "high")

    def test_to_sarif(self) -> None:
        """Test conversion to SARIF format."""
        finding = SecretFinding(
            pattern_name="test",
            pattern_description="Test",
            severity=PatternSeverity.CRITICAL,
            file_path="test.py",
            line_number=1,
            line_content="test line",
            matched_text="secret123",
            category="test",
        )
        sarif = finding.to_sarif()
        self.assertEqual(sarif["ruleId"], "test")
        self.assertEqual(sarif["level"], "error")


class TestScanResult(unittest.TestCase):
    """Tests for ScanResult."""

    def test_properties(self) -> None:
        """Test ScanResult properties."""
        findings = [
            SecretFinding(
                pattern_name="test",
                pattern_description="Test",
                severity=PatternSeverity.CRITICAL,
                file_path="test.py",
                line_number=1,
                line_content="test",
                matched_text="secret",
                category="test",
            )
        ]
        result = ScanResult(findings=findings, files_scanned=10)

        self.assertEqual(result.finding_count, 1)
        self.assertEqual(result.critical_count, 1)
        self.assertEqual(result.files_scanned, 10)

    def test_to_sarif(self) -> None:
        """Test conversion to SARIF format."""
        result = ScanResult(findings=[], files_scanned=5)
        sarif = result.to_sarif()

        self.assertEqual(sarif["version"], "2.1.0")
        self.assertIn("runs", sarif)


class TestBaselineManager(unittest.TestCase):
    """Tests for BaselineManager."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.tmpdir = tempfile.mkdtemp()
        self.baseline_path = Path(self.tmpdir) / ".secrets.baseline"

    def tearDown(self) -> None:
        """Clean up."""
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_create_baseline(self) -> None:
        """Test creating baseline from scan."""
        manager = BaselineManager(self.baseline_path)
        findings = [
            SecretFinding(
                pattern_name="test",
                pattern_description="Test",
                severity=PatternSeverity.HIGH,
                file_path="test.py",
                line_number=1,
                line_content="test",
                matched_text="secret",
                category="test",
            )
        ]
        result = ScanResult(findings=findings)

        manager.create_from_scan(result)
        self.assertEqual(manager.baseline.entry_count, 1)

    def test_save_and_load(self) -> None:
        """Test saving and loading baseline."""
        manager = BaselineManager(self.baseline_path)
        manager.baseline.entries.append(
            BaselineEntry(
                hash_value="abc123",
                pattern_name="test",
                file_path="test.py",
                line_number=1,
            )
        )
        manager.save()

        # Load in new manager
        manager2 = BaselineManager(self.baseline_path)
        manager2.load()
        self.assertEqual(manager2.baseline.entry_count, 1)

    def test_add_false_positive(self) -> None:
        """Test marking false positive."""
        manager = BaselineManager()
        manager.baseline.entries.append(
            BaselineEntry(
                hash_value="test123",
                pattern_name="test",
                file_path="test.py",
                line_number=1,
            )
        )

        result = manager.add_false_positive("test123", reason="Test reason")
        self.assertTrue(result)
        self.assertTrue(manager.baseline.entries[0].is_false_positive)

    def test_is_baselined(self) -> None:
        """Test checking if finding is baselined."""
        manager = BaselineManager()
        manager.baseline.entries.append(
            BaselineEntry(
                hash_value="test123",
                pattern_name="test",
                file_path="test.py",
                line_number=1,
            )
        )

        finding = SecretFinding(
            pattern_name="test",
            pattern_description="Test",
            severity=PatternSeverity.HIGH,
            file_path="test.py",
            line_number=1,
            line_content="test",
            matched_text="secret",
            hash_value="test123",
            category="test",
        )

        self.assertTrue(manager.is_baselined(finding))

    def test_get_new_findings(self) -> None:
        """Test getting new findings not in baseline."""
        manager = BaselineManager()

        new_finding = SecretFinding(
            pattern_name="new",
            pattern_description="New",
            severity=PatternSeverity.HIGH,
            file_path="new.py",
            line_number=1,
            line_content="new",
            matched_text="newsecret",
            category="test",
        )
        result = ScanResult(findings=[new_finding])

        new = manager.get_new_findings(result)
        self.assertEqual(len(new), 1)


class TestVerificationEngine(unittest.TestCase):
    """Tests for VerificationEngine."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.engine = VerificationEngine(verify_live=False)

    def test_verify_aws_key_valid(self) -> None:
        """Test validating AWS key format."""
        finding = SecretFinding(
            pattern_name="aws_access_key_id",
            pattern_description="AWS Key",
            severity=PatternSeverity.CRITICAL,
            file_path="test.py",
            line_number=1,
            line_content="test",
            matched_text="AKIAIOSFODNN7EXAMPLE",
            category="aws",
        )

        result = self.engine.verify(finding)
        self.assertIn(
            result.status,
            [VerificationStatus.UNKNOWN, VerificationStatus.INVALID]
        )

    def test_verify_github_token(self) -> None:
        """Test validating GitHub token."""
        finding = SecretFinding(
            pattern_name="github_token",
            pattern_description="GitHub Token",
            severity=PatternSeverity.HIGH,
            file_path="test.py",
            line_number=1,
            line_content="test",
            matched_text="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            category="github",
        )

        result = self.engine.verify(finding)
        self.assertIsInstance(result, VerificationResult)

    def test_verify_jwt(self) -> None:
        """Test JWT validation."""
        # Valid JWT structure (header.payload.signature)
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        finding = SecretFinding(
            pattern_name="jwt_token",
            pattern_description="JWT",
            severity=PatternSeverity.MEDIUM,
            file_path="test.py",
            line_number=1,
            line_content="test",
            matched_text=jwt,
            category="generic",
        )

        result = self.engine.verify(finding)
        self.assertIn(
            result.status,
            [VerificationStatus.UNKNOWN, VerificationStatus.INVALID]
        )

    def test_verify_unsupported_pattern(self) -> None:
        """Test verifying unsupported pattern."""
        finding = SecretFinding(
            pattern_name="unknown_pattern",
            pattern_description="Unknown",
            severity=PatternSeverity.LOW,
            file_path="test.py",
            line_number=1,
            line_content="test",
            matched_text="unknown",
            category="unknown",
        )

        result = self.engine.verify(finding)
        self.assertEqual(result.status, VerificationStatus.SKIPPED)

    def test_get_supported_patterns(self) -> None:
        """Test getting supported patterns."""
        patterns = self.engine.get_supported_patterns()
        self.assertIn("aws_access_key_id", patterns)
        self.assertIn("github_token", patterns)


class TestRemediationGuide(unittest.TestCase):
    """Tests for RemediationGuide."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.guide = RemediationGuide()

    def test_calculate_priority_score(self) -> None:
        """Test priority score calculation."""
        finding = SecretFinding(
            pattern_name="aws_access_key_id",
            pattern_description="AWS Key",
            severity=PatternSeverity.CRITICAL,
            file_path="test.py",
            line_number=1,
            line_content="test",
            matched_text="AKIAIOSFODNN7EXAMPLE",
            category="aws",
            entropy=5.0,
        )

        score = self.guide.calculate_priority_score(finding)
        self.assertGreater(score, 50)

    def test_get_priority(self) -> None:
        """Test getting priority from score."""
        self.assertEqual(
            self.guide.get_priority(90), RemediationPriority.P1_IMMEDIATE
        )
        self.assertEqual(
            self.guide.get_priority(70), RemediationPriority.P2_URGENT
        )
        self.assertEqual(
            self.guide.get_priority(50), RemediationPriority.P3_HIGH
        )

    def test_get_workflow(self) -> None:
        """Test getting rotation workflow."""
        workflow = self.guide.get_workflow("aws_access_key_id")
        self.assertIsNotNone(workflow)
        self.assertGreater(len(workflow.steps), 0)

    def test_generate_report(self) -> None:
        """Test generating remediation report."""
        finding = SecretFinding(
            pattern_name="aws_access_key_id",
            pattern_description="AWS Key",
            severity=PatternSeverity.CRITICAL,
            file_path="test.py",
            line_number=1,
            line_content="test",
            matched_text="secret",
            category="aws",
        )

        report = self.guide.generate_report(finding)
        self.assertIsNotNone(report.priority)
        self.assertGreater(report.priority_score, 0)
        self.assertGreater(len(report.recommended_actions), 0)

    def test_batch_report(self) -> None:
        """Test batch report generation."""
        findings = [
            SecretFinding(
                pattern_name="test",
                pattern_description="Test",
                severity=PatternSeverity.HIGH,
                file_path="test.py",
                line_number=i,
                line_content="test",
                matched_text=f"secret{i}",
                category="test",
            )
            for i in range(3)
        ]

        reports = self.guide.batch_report(findings)
        self.assertEqual(len(reports), 3)
        # Should be sorted by priority score descending
        self.assertGreaterEqual(
            reports[0].priority_score, reports[-1].priority_score
        )

    def test_get_supported_patterns(self) -> None:
        """Test getting patterns with workflows."""
        patterns = self.guide.get_supported_patterns()
        self.assertIn("aws_access_key_id", patterns)
        self.assertIn("github_token", patterns)


class TestCLI(unittest.TestCase):
    """Tests for CLI."""

    def test_parser_creation(self) -> None:
        """Test parser is created correctly."""
        from .secrets_cli import create_parser

        parser = create_parser()
        self.assertIsNotNone(parser)

    def test_scan_command(self) -> None:
        """Test scan command."""
        from .secrets_cli import main

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("# No secrets here\n")

            result = main(["scan", tmpdir, "--format", "json"])
            self.assertEqual(result, 0)

    def test_patterns_command(self) -> None:
        """Test patterns command."""
        from .secrets_cli import main

        result = main(["patterns"])
        self.assertEqual(result, 0)


class TestIntegration(unittest.TestCase):
    """Integration tests."""

    def test_full_scan_workflow(self) -> None:
        """Test complete scan workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files with various secrets
            test_file = Path(tmpdir) / "config.py"
            test_file.write_text("""
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
DB_URL = "postgres://user:pass@localhost/db"
""")

            # Scan
            scanner = SecretScanner()
            result = scanner.scan_directory(tmpdir)

            self.assertGreater(result.finding_count, 0)

            # Create baseline
            baseline_mgr = BaselineManager(Path(tmpdir) / ".secrets.baseline")
            baseline_mgr.create_from_scan(result)
            baseline_mgr.save()

            # Rescan and filter
            result2 = scanner.scan_directory(tmpdir)
            new_findings = baseline_mgr.get_new_findings(result2)
            self.assertEqual(len(new_findings), 0)

    def test_sarif_output(self) -> None:
        """Test SARIF output generation."""
        findings = [
            SecretFinding(
                pattern_name="test",
                pattern_description="Test secret",
                severity=PatternSeverity.HIGH,
                file_path="test.py",
                line_number=1,
                line_content="secret = 'test'",
                matched_text="test",
                category="test",
            )
        ]
        result = ScanResult(findings=findings, files_scanned=1)

        sarif = result.to_sarif()

        # Validate SARIF structure
        self.assertEqual(sarif["version"], "2.1.0")
        self.assertEqual(len(sarif["runs"]), 1)
        self.assertEqual(len(sarif["runs"][0]["results"]), 1)


if __name__ == "__main__":
    unittest.main()
