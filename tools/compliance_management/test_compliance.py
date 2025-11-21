"""
Comprehensive tests for Compliance Management Platform.

Part of devCrew_s1 TOOL-SEC-011 compliance management platform.
"""

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from .policy_engine import (
    PolicyEngine,
    PolicyCache,
    PolicyResult,
    PolicyDecision,
)
from .compliance_manager import (
    ComplianceManager,
    ComplianceFramework,
    ComplianceStatus,
    ComplianceScore,
)
from .policy_validator import (
    PolicyValidator,
    ValidationResult,
    ValidationStatus,
    PolicyTest,
)
from .regulatory_mapper import (
    RegulatoryMapper,
    ControlMapping,
    ComplianceMatrix,
)
from .audit_reporter import AuditReporter, ReportFormat
from .violation_tracker import (
    ViolationTracker,
    Violation,
    ViolationSeverity,
    ViolationStatus,
)


class TestPolicyCache(unittest.TestCase):
    """Tests for PolicyCache."""

    def test_cache_put_and_get(self):
        cache = PolicyCache()
        cache.put("hash1", {"rule": "test"})
        result = cache.get("hash1")
        self.assertIsNotNone(result)
        self.assertEqual(result.compiled_rules, {"rule": "test"})

    def test_cache_miss(self):
        cache = PolicyCache()
        result = cache.get("nonexistent")
        self.assertIsNone(result)

    def test_cache_eviction(self):
        cache = PolicyCache(max_size=2)
        cache.put("hash1", {"rule": "1"})
        cache.put("hash2", {"rule": "2"})
        cache.put("hash3", {"rule": "3"})
        self.assertEqual(cache.size, 2)

    def test_cache_clear(self):
        cache = PolicyCache()
        cache.put("hash1", {"rule": "test"})
        cache.clear()
        self.assertEqual(cache.size, 0)

    def test_cache_ttl_expiry(self):
        cache = PolicyCache(ttl_seconds=0)
        cache.put("hash1", {"rule": "test"})
        import time
        time.sleep(0.1)
        result = cache.get("hash1")
        self.assertIsNone(result)


class TestPolicyEngine(unittest.TestCase):
    """Tests for PolicyEngine."""

    def setUp(self):
        self.engine = PolicyEngine()

    def test_compile_policy(self):
        policy = "package test\ndefault allow = false"
        result = self.engine.compile_policy(policy, "test")
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["package"], "test")

    def test_load_policy_from_string(self):
        policy = "package compliance\ndefault allow = false"
        self.engine.load_policy_from_string(policy, "test_policy")
        self.assertIn("test_policy", self.engine.get_loaded_policies())

    def test_evaluate_compliant(self):
        policy = "package test\ndefault allow = true"
        self.engine.load_policy_from_string(policy, "test")
        input_data = {
            "encryption_enabled": True,
            "access_controls": ["admin"],
            "audit_logging_enabled": True,
            "retention_policy": "90 days",
            "consent_obtained": True,
            "data_minimized": True,
            "breach_notification_process": True,
            "mfa_enabled": True,
            "firewall_enabled": True,
            "vulnerability_scanning": True,
        }
        result = self.engine.evaluate("test", input_data)
        self.assertEqual(result.decision, PolicyDecision.ALLOW)

    def test_evaluate_non_compliant(self):
        policy = "package test\ndefault allow = true"
        self.engine.load_policy_from_string(policy, "test")
        input_data = {"encryption_enabled": False}
        result = self.engine.evaluate("test", input_data)
        self.assertEqual(result.decision, PolicyDecision.DENY)
        self.assertTrue(len(result.violations) > 0)

    def test_evaluate_policy_not_found(self):
        result = self.engine.evaluate("nonexistent", {})
        self.assertEqual(result.decision, PolicyDecision.ERROR)

    def test_evaluate_with_rules(self):
        input_data = {"encryption_enabled": True}
        result = self.engine.evaluate_with_rules(["data_encryption"], input_data)
        self.assertEqual(result.decision, PolicyDecision.ALLOW)

    def test_get_available_rules(self):
        rules = self.engine.get_available_rules()
        self.assertIn("data_encryption", rules)
        self.assertIn("access_control", rules)

    def test_policy_result_to_dict(self):
        result = PolicyResult(
            decision=PolicyDecision.ALLOW,
            policy_name="test",
            violations=[],
        )
        d = result.to_dict()
        self.assertEqual(d["decision"], "allow")
        self.assertEqual(d["policy_name"], "test")


class TestComplianceManager(unittest.TestCase):
    """Tests for ComplianceManager."""

    def setUp(self):
        self.manager = ComplianceManager()
        self.compliant_data = {
            "encryption_enabled": True,
            "access_controls": ["admin", "user"],
            "audit_logging_enabled": True,
            "retention_policy": "90 days",
            "consent_obtained": True,
            "data_minimized": True,
            "breach_notification_process": True,
            "mfa_enabled": True,
            "firewall_enabled": True,
            "vulnerability_scanning": True,
        }

    def test_assess_gdpr(self):
        score = self.manager.assess_compliance(
            ComplianceFramework.GDPR, self.compliant_data
        )
        self.assertIsInstance(score, ComplianceScore)
        self.assertEqual(score.framework, ComplianceFramework.GDPR)
        self.assertEqual(score.score, 100.0)

    def test_assess_hipaa(self):
        score = self.manager.assess_compliance(
            ComplianceFramework.HIPAA, self.compliant_data
        )
        self.assertEqual(score.framework, ComplianceFramework.HIPAA)

    def test_assess_fedramp(self):
        score = self.manager.assess_compliance(
            ComplianceFramework.FEDRAMP, self.compliant_data
        )
        self.assertEqual(score.framework, ComplianceFramework.FEDRAMP)

    def test_assess_soc2(self):
        score = self.manager.assess_compliance(
            ComplianceFramework.SOC2, self.compliant_data
        )
        self.assertEqual(score.framework, ComplianceFramework.SOC2)

    def test_assess_iso_27001(self):
        score = self.manager.assess_compliance(
            ComplianceFramework.ISO_27001, self.compliant_data
        )
        self.assertEqual(score.framework, ComplianceFramework.ISO_27001)

    def test_assess_nist(self):
        score = self.manager.assess_compliance(
            ComplianceFramework.NIST_800_53, self.compliant_data
        )
        self.assertEqual(score.framework, ComplianceFramework.NIST_800_53)

    def test_assess_non_compliant(self):
        data = {"encryption_enabled": False}
        score = self.manager.assess_compliance(ComplianceFramework.GDPR, data)
        self.assertLess(score.score, 100)
        self.assertIn(score.status, [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIAL])

    def test_assess_all_frameworks(self):
        results = self.manager.assess_all_frameworks(self.compliant_data)
        self.assertEqual(len(results), len(ComplianceFramework))

    def test_get_framework_controls(self):
        controls = self.manager.get_framework_controls(ComplianceFramework.GDPR)
        self.assertTrue(len(controls) > 0)

    def test_get_supported_frameworks(self):
        frameworks = self.manager.get_supported_frameworks()
        self.assertEqual(len(frameworks), 6)

    def test_compliance_score_to_dict(self):
        score = self.manager.assess_compliance(
            ComplianceFramework.GDPR, self.compliant_data
        )
        d = score.to_dict()
        self.assertIn("framework", d)
        self.assertIn("score", d)
        self.assertIn("status", d)

    def test_assessment_history(self):
        self.manager.assess_compliance(ComplianceFramework.GDPR, self.compliant_data)
        history = self.manager.get_assessment_history()
        self.assertTrue(len(history) >= 1)


class TestPolicyValidator(unittest.TestCase):
    """Tests for PolicyValidator."""

    def setUp(self):
        self.validator = PolicyValidator()

    def test_validate_rego_valid(self):
        content = """package compliance

default allow = false

allow {
    input.valid == true
}
"""
        result = self.validator.validate_rego(content, "test")
        self.assertEqual(result.status, ValidationStatus.VALID)

    def test_validate_rego_missing_package(self):
        content = "default allow = false"
        result = self.validator.validate_rego(content, "test")
        self.assertEqual(result.status, ValidationStatus.INVALID)
        self.assertTrue(result.error_count > 0)

    def test_validate_rego_unbalanced_braces(self):
        content = "package test\nallow {"
        result = self.validator.validate_rego(content, "test")
        self.assertEqual(result.status, ValidationStatus.INVALID)

    def test_validate_yaml_valid(self):
        content = """
version: "1.0"
name: test-policy
rules:
  - name: rule1
    enabled: true
"""
        result = self.validator.validate_yaml(content, "test")
        self.assertIn(result.status, [ValidationStatus.VALID, ValidationStatus.WARNING])

    def test_validate_yaml_invalid_syntax(self):
        content = "invalid: yaml: content: ::"
        result = self.validator.validate_yaml(content, "test")
        self.assertEqual(result.status, ValidationStatus.INVALID)

    def test_validate_yaml_empty(self):
        result = self.validator.validate_yaml("", "test")
        self.assertEqual(result.status, ValidationStatus.WARNING)

    def test_validation_result_properties(self):
        result = ValidationResult(
            status=ValidationStatus.VALID,
            policy_name="test",
            policy_type="rego",
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.error_count, 0)

    def test_validate_file_not_found(self):
        result = self.validator.validate_file(Path("/nonexistent/file.rego"))
        self.assertEqual(result.status, ValidationStatus.INVALID)

    def test_run_tests(self):
        policy = "package test\ndefault allow = false"
        tests = [
            PolicyTest(
                name="test1",
                input_data={"valid": True},
                expected_decision="deny",
            )
        ]
        results = self.validator.run_tests(policy, tests)
        self.assertEqual(len(results), 1)

    def test_create_test_from_yaml(self):
        yaml_content = """
tests:
  - name: test1
    input:
      key: value
    expected: allow
"""
        tests = self.validator.create_test_from_yaml(yaml_content)
        self.assertEqual(len(tests), 1)
        self.assertEqual(tests[0].name, "test1")


class TestRegulatoryMapper(unittest.TestCase):
    """Tests for RegulatoryMapper."""

    def setUp(self):
        self.mapper = RegulatoryMapper()

    def test_get_mapping(self):
        mapping = self.mapper.get_mapping("data_encryption")
        self.assertIsNotNone(mapping)
        self.assertIn("gdpr", mapping.frameworks)

    def test_get_mapping_not_found(self):
        mapping = self.mapper.get_mapping("nonexistent_rule")
        self.assertIsNone(mapping)

    def test_get_rules_for_control(self):
        rules = self.mapper.get_rules_for_control("gdpr", "GDPR-32")
        self.assertIn("data_encryption", rules)

    def test_get_controls_for_rule(self):
        controls = self.mapper.get_controls_for_rule("data_encryption")
        self.assertIn("gdpr", controls)

    def test_get_controls_for_rule_filtered(self):
        controls = self.mapper.get_controls_for_rule("data_encryption", "gdpr")
        self.assertEqual(len(controls), 1)
        self.assertIn("gdpr", controls)

    def test_generate_compliance_matrix(self):
        matrix = self.mapper.generate_compliance_matrix()
        self.assertIsInstance(matrix, ComplianceMatrix)
        self.assertTrue(len(matrix.entries) > 0)

    def test_generate_compliance_matrix_filtered(self):
        matrix = self.mapper.generate_compliance_matrix(["gdpr"])
        for entry in matrix.entries:
            self.assertEqual(entry.framework, "gdpr")

    def test_filter_matrix_by_framework(self):
        matrix = self.mapper.generate_compliance_matrix()
        filtered = matrix.filter_by_framework("hipaa")
        for entry in filtered.entries:
            self.assertEqual(entry.framework, "hipaa")

    def test_get_evidence_requirements(self):
        requirements = self.mapper.get_evidence_requirements("gdpr", "GDPR-32")
        self.assertTrue(len(requirements) > 0)

    def test_get_all_frameworks(self):
        frameworks = self.mapper.get_all_frameworks()
        self.assertIn("gdpr", frameworks)
        self.assertIn("hipaa", frameworks)

    def test_get_framework_controls(self):
        controls = self.mapper.get_framework_controls("gdpr")
        self.assertIn("GDPR-32", controls)

    def test_export_mapping(self):
        exported = self.mapper.export_mapping("data_encryption")
        self.assertIsNotNone(exported)
        self.assertEqual(exported["rule_name"], "data_encryption")

    def test_cross_framework_coverage(self):
        coverage = self.mapper.get_cross_framework_coverage("data_encryption")
        self.assertTrue(len(coverage) > 0)


class TestAuditReporter(unittest.TestCase):
    """Tests for AuditReporter."""

    def setUp(self):
        self.reporter = AuditReporter(organization_name="Test Org")
        manager = ComplianceManager()
        self.scores = {
            ComplianceFramework.GDPR: manager.assess_compliance(
                ComplianceFramework.GDPR,
                {"encryption_enabled": True, "access_controls": ["admin"]},
            )
        }

    def test_generate_html_report(self):
        content = self.reporter.generate_report(self.scores, ReportFormat.HTML)
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("Test Org", content)

    def test_generate_csv_report(self):
        content = self.reporter.generate_report(self.scores, ReportFormat.CSV)
        self.assertIn("Framework", content)
        self.assertIn("Score", content)

    def test_generate_json_report(self):
        content = self.reporter.generate_report(self.scores, ReportFormat.JSON)
        data = json.loads(content)
        self.assertIn("report_metadata", data)
        self.assertIn("framework_scores", data)

    def test_generate_pdf_placeholder(self):
        content = self.reporter.generate_report(self.scores, ReportFormat.PDF)
        self.assertIn("COMPLIANCE AUDIT REPORT", content)

    def test_report_to_file(self):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            output_path = Path(f.name)
        try:
            self.reporter.generate_report(self.scores, ReportFormat.HTML, output_path)
            self.assertTrue(output_path.exists())
            content = output_path.read_text()
            self.assertIn("<!DOCTYPE html>", content)
        finally:
            output_path.unlink(missing_ok=True)

    def test_executive_summary(self):
        summary = self.reporter.generate_executive_summary(self.scores)
        self.assertIn("framework", summary.lower())

    def test_generate_recommendations(self):
        recommendations = self.reporter.generate_recommendations(self.scores)
        self.assertIsInstance(recommendations, list)


class TestViolationTracker(unittest.TestCase):
    """Tests for ViolationTracker."""

    def setUp(self):
        self.tracker = ViolationTracker()

    def test_create_violation(self):
        violation = self.tracker.create_violation(
            rule_name="data_encryption",
            framework="gdpr",
            control_id="GDPR-32",
            severity=ViolationSeverity.HIGH,
            description="Encryption not enabled",
            resource="database",
        )
        self.assertIsNotNone(violation.violation_id)
        self.assertEqual(violation.status, ViolationStatus.OPEN)

    def test_update_status(self):
        violation = self.tracker.create_violation(
            rule_name="test", framework="gdpr", control_id="GDPR-1",
            severity=ViolationSeverity.MEDIUM,
            description="Test violation", resource="test",
        )
        updated = self.tracker.update_status(
            violation.violation_id,
            ViolationStatus.ACKNOWLEDGED,
            "admin",
            "Reviewing",
        )
        self.assertEqual(updated.status, ViolationStatus.ACKNOWLEDGED)
        self.assertEqual(len(updated.history), 2)

    def test_assign_violation(self):
        violation = self.tracker.create_violation(
            rule_name="test", framework="gdpr", control_id="GDPR-1",
            severity=ViolationSeverity.LOW,
            description="Test", resource="test",
        )
        due = datetime.utcnow() + timedelta(days=7)
        updated = self.tracker.assign_violation(
            violation.violation_id, "user@test.com", due
        )
        self.assertEqual(updated.assigned_to, "user@test.com")
        self.assertIsNotNone(updated.due_date)

    def test_add_evidence(self):
        violation = self.tracker.create_violation(
            rule_name="test", framework="gdpr", control_id="GDPR-1",
            severity=ViolationSeverity.MEDIUM,
            description="Test", resource="test",
        )
        updated = self.tracker.add_evidence(violation.violation_id, "screenshot.png")
        self.assertIn("screenshot.png", updated.evidence)

    def test_get_violations_by_status(self):
        self.tracker.create_violation(
            rule_name="test", framework="gdpr", control_id="GDPR-1",
            severity=ViolationSeverity.HIGH,
            description="Test", resource="test",
        )
        open_violations = self.tracker.get_violations_by_status(ViolationStatus.OPEN)
        self.assertTrue(len(open_violations) >= 1)

    def test_get_violations_by_severity(self):
        self.tracker.create_violation(
            rule_name="test", framework="gdpr", control_id="GDPR-1",
            severity=ViolationSeverity.CRITICAL,
            description="Test", resource="test",
        )
        critical = self.tracker.get_violations_by_severity(ViolationSeverity.CRITICAL)
        self.assertTrue(len(critical) >= 1)

    def test_get_open_violations(self):
        self.tracker.create_violation(
            rule_name="test", framework="gdpr", control_id="GDPR-1",
            severity=ViolationSeverity.HIGH,
            description="Test", resource="test",
        )
        open_violations = self.tracker.get_open_violations()
        self.assertTrue(len(open_violations) >= 1)

    def test_calculate_risk_score(self):
        self.tracker.create_violation(
            rule_name="test", framework="gdpr", control_id="GDPR-1",
            severity=ViolationSeverity.CRITICAL,
            description="Test", resource="test",
        )
        score = self.tracker.calculate_risk_score()
        self.assertEqual(score, 100.0)

    def test_get_statistics(self):
        self.tracker.create_violation(
            rule_name="test", framework="gdpr", control_id="GDPR-1",
            severity=ViolationSeverity.HIGH,
            description="Test", resource="test",
        )
        stats = self.tracker.get_statistics()
        self.assertIn("total_violations", stats)
        self.assertIn("by_severity", stats)
        self.assertIn("by_framework", stats)

    def test_bulk_create_from_assessment(self):
        details = {
            "controls": [
                {
                    "control_id": "GDPR-32",
                    "name": "Security",
                    "passed": False,
                    "violations": [
                        {"rule": "data_encryption", "message": "Not enabled", "severity": "high"}
                    ],
                }
            ]
        }
        violations = self.tracker.bulk_create_from_assessment("gdpr", details)
        self.assertEqual(len(violations), 1)

    def test_export_violations(self):
        self.tracker.create_violation(
            rule_name="test", framework="gdpr", control_id="GDPR-1",
            severity=ViolationSeverity.HIGH,
            description="Test", resource="test",
        )
        exported = self.tracker.export_violations()
        self.assertTrue(len(exported) >= 1)
        self.assertIn("violation_id", exported[0])

    def test_delete_violation(self):
        violation = self.tracker.create_violation(
            rule_name="test", framework="gdpr", control_id="GDPR-1",
            severity=ViolationSeverity.LOW,
            description="Test", resource="test",
        )
        result = self.tracker.delete_violation(violation.violation_id)
        self.assertTrue(result)
        self.assertIsNone(self.tracker.get_violation(violation.violation_id))

    def test_clear_all(self):
        self.tracker.create_violation(
            rule_name="test", framework="gdpr", control_id="GDPR-1",
            severity=ViolationSeverity.LOW,
            description="Test", resource="test",
        )
        count = self.tracker.clear_all()
        self.assertTrue(count >= 1)
        self.assertEqual(len(self.tracker.get_all_violations()), 0)


class TestComplianceCLI(unittest.TestCase):
    """Tests for compliance CLI."""

    def test_parser_creation(self):
        from .compliance_cli import create_parser
        parser = create_parser()
        self.assertIsNotNone(parser)

    def test_list_rules(self):
        from .compliance_cli import main
        result = main(["list-rules"])
        self.assertEqual(result, 0)

    def test_list_frameworks(self):
        from .compliance_cli import main
        result = main(["list-frameworks"])
        self.assertEqual(result, 0)

    def test_no_command(self):
        from .compliance_cli import main
        result = main([])
        self.assertEqual(result, 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the compliance platform."""

    def test_full_compliance_workflow(self):
        """Test complete workflow: assess, track violations, generate report."""
        # Setup
        manager = ComplianceManager()
        tracker = ViolationTracker()
        reporter = AuditReporter(organization_name="Integration Test")

        # Assess compliance
        data = {
            "encryption_enabled": False,
            "access_controls": [],
            "audit_logging_enabled": True,
        }
        score = manager.assess_compliance(ComplianceFramework.GDPR, data)

        # Track violations
        violations = tracker.bulk_create_from_assessment("gdpr", score.details)

        # Generate report
        scores = {ComplianceFramework.GDPR: score}
        report = reporter.generate_report(scores, ReportFormat.JSON)

        # Verify
        self.assertLess(score.score, 100)
        self.assertTrue(len(violations) > 0)
        self.assertIn("framework_scores", report)

    def test_policy_validation_and_evaluation(self):
        """Test policy validation followed by evaluation."""
        validator = PolicyValidator()
        engine = PolicyEngine()

        policy = """package compliance

default allow = false

allow {
    input.encryption == true
}
"""
        # Validate
        result = validator.validate_rego(policy, "test")
        self.assertTrue(result.is_valid)

        # Load and evaluate
        engine.load_policy_from_string(policy, "test")
        eval_result = engine.evaluate("test", {"encryption": True})
        self.assertIsNotNone(eval_result)


if __name__ == "__main__":
    unittest.main()
