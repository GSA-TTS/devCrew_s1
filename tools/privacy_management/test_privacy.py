"""Comprehensive tests for Privacy Management Platform."""

import json
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from audit_logger import AuditEventType, AuditLogger
from compliance_validator import (
    ComplianceFramework,
    ComplianceValidator,
    RequirementStatus,
)
from consent_manager import ConsentManager, ConsentPurpose, ConsentStatus
from data_anonymizer import AnonymizationMethod, DataAnonymizer
from pii_detector import PIIDetector, PIIMatch, PIIType
from privacy_manager import PrivacyManager


# =============================================================================
# PII Detector Tests
# =============================================================================
class TestPIIDetector:
    """Tests for PII detection."""

    def test_detect_email(self) -> None:
        """Test email detection."""
        detector = PIIDetector()
        matches = detector.scan_text("Contact me at john.doe@example.com")
        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.EMAIL
        assert matches[0].value == "john.doe@example.com"
        assert matches[0].confidence >= 0.9

    def test_detect_phone(self) -> None:
        """Test phone number detection."""
        detector = PIIDetector()
        matches = detector.scan_text("Call me at 555-123-4567")
        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.PHONE
        assert "555" in matches[0].value

    def test_detect_ssn(self) -> None:
        """Test SSN detection."""
        detector = PIIDetector()
        matches = detector.scan_text("SSN: 123-45-6789")
        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.SSN

    def test_detect_credit_card(self) -> None:
        """Test credit card detection."""
        detector = PIIDetector()
        matches = detector.scan_text("Card: 4111-1111-1111-1111")
        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.CREDIT_CARD

    def test_detect_ip_address(self) -> None:
        """Test IP address detection."""
        detector = PIIDetector()
        matches = detector.scan_text("Server IP: 192.168.1.100")
        assert len(matches) == 1
        assert matches[0].pii_type == PIIType.IP_ADDRESS

    def test_detect_name(self) -> None:
        """Test name detection."""
        detector = PIIDetector()
        matches = detector.scan_text("Customer: John Smith")
        assert len(matches) >= 1
        name_matches = [m for m in matches if m.pii_type == PIIType.NAME]
        assert len(name_matches) == 1

    def test_detect_address(self) -> None:
        """Test address detection."""
        detector = PIIDetector()
        matches = detector.scan_text("Address: 123 Main Street")
        address_matches = [m for m in matches if m.pii_type == PIIType.ADDRESS]
        assert len(address_matches) == 1
        assert "123 Main Street" in address_matches[0].value

    def test_scan_dict(self) -> None:
        """Test dictionary scanning."""
        detector = PIIDetector()
        data = {
            "email": "test@example.com",
            "phone": "555-123-4567"
        }
        matches = detector.scan_dict(data)
        assert len(matches) == 2
        assert any(m.field == "email" for m in matches)

    def test_multiple_pii_in_text(self) -> None:
        """Test detecting multiple PII types."""
        detector = PIIDetector()
        text = "Email: user@test.com, Phone: 555-111-2222, SSN: 111-22-3333"
        matches = detector.scan_text(text)
        assert len(matches) == 3

    def test_get_summary(self) -> None:
        """Test summary generation."""
        detector = PIIDetector()
        matches = detector.scan_text("user@test.com and 555-111-2222")
        summary = detector.get_summary(matches)
        assert "email" in summary
        assert "phone" in summary


# =============================================================================
# Data Anonymizer Tests
# =============================================================================
class TestDataAnonymizer:
    """Tests for data anonymization."""

    def test_mask_default(self) -> None:
        """Test default masking."""
        anonymizer = DataAnonymizer()
        result = anonymizer.mask("1234567890")
        assert result == "******7890"

    def test_mask_start_visible(self) -> None:
        """Test masking with start visible."""
        anonymizer = DataAnonymizer()
        result = anonymizer.mask("1234567890", visible_position="start")
        assert result == "1234******"

    def test_hash_value(self) -> None:
        """Test hashing."""
        anonymizer = DataAnonymizer(salt="test_salt")
        result = anonymizer.hash_value("sensitive_data")
        assert len(result) == 64  # SHA-256 hex length
        # Same input should give same output
        assert anonymizer.hash_value("sensitive_data") == result

    def test_pseudonymize_consistent(self) -> None:
        """Test pseudonymization consistency."""
        anonymizer = DataAnonymizer()
        result1 = anonymizer.pseudonymize("john@example.com")
        result2 = anonymizer.pseudonymize("john@example.com")
        assert result1 == result2
        assert result1.startswith("PSEUDO_")

    def test_pseudonymize_different_values(self) -> None:
        """Test different values get different pseudonyms."""
        anonymizer = DataAnonymizer()
        result1 = anonymizer.pseudonymize("user1@example.com")
        result2 = anonymizer.pseudonymize("user2@example.com")
        assert result1 != result2

    def test_generalize_age_range(self) -> None:
        """Test age generalization."""
        anonymizer = DataAnonymizer()
        assert anonymizer.generalize(25, "age_range") == "18-29"
        assert anonymizer.generalize(45, "age_range") == "30-49"
        assert anonymizer.generalize(70, "age_range") == "65+"

    def test_generalize_zip(self) -> None:
        """Test zip code generalization."""
        anonymizer = DataAnonymizer()
        result = anonymizer.generalize("12345", "zip_prefix")
        assert result == "123XX"

    def test_suppress(self) -> None:
        """Test suppression."""
        anonymizer = DataAnonymizer()
        result = anonymizer.suppress("sensitive_value")
        assert result == "[SUPPRESSED]"

    def test_anonymize_pii_in_text(self) -> None:
        """Test anonymizing PII in text."""
        detector = PIIDetector()
        anonymizer = DataAnonymizer()
        text = "Email: test@example.com"
        matches = detector.scan_text(text)
        result = anonymizer.anonymize_pii(
            text, matches, AnonymizationMethod.MASKING
        )
        assert "test@example.com" not in result

    def test_anonymize_dict(self) -> None:
        """Test dictionary anonymization."""
        anonymizer = DataAnonymizer()
        data = {"ssn": "123-45-6789", "name": "John Doe"}
        config = {
            "ssn": AnonymizationMethod.MASKING,
            "name": AnonymizationMethod.PSEUDONYMIZATION
        }
        result = anonymizer.anonymize_dict(data, config)
        assert result["ssn"] != "123-45-6789"
        assert result["name"].startswith("PSEUDO_")


# =============================================================================
# Consent Manager Tests
# =============================================================================
class TestConsentManager:
    """Tests for consent management."""

    def test_record_consent(self) -> None:
        """Test recording consent."""
        manager = ConsentManager()
        records = manager.record_consent(
            "user123",
            [ConsentPurpose.MARKETING, ConsentPurpose.ANALYTICS],
            opt_in=True
        )
        assert len(records) == 2
        assert all(r.opt_in for r in records)

    def test_check_consent_granted(self) -> None:
        """Test checking granted consent."""
        manager = ConsentManager()
        manager.record_consent("user123", [ConsentPurpose.MARKETING], opt_in=True)
        assert manager.check_consent("user123", ConsentPurpose.MARKETING) is True

    def test_check_consent_denied(self) -> None:
        """Test checking denied consent."""
        manager = ConsentManager()
        manager.record_consent("user123", [ConsentPurpose.MARKETING], opt_in=False)
        assert manager.check_consent("user123", ConsentPurpose.MARKETING) is False

    def test_check_consent_not_recorded(self) -> None:
        """Test checking non-existent consent."""
        manager = ConsentManager()
        assert manager.check_consent("user123", ConsentPurpose.MARKETING) is False

    def test_revoke_consent(self) -> None:
        """Test revoking consent."""
        manager = ConsentManager()
        manager.record_consent("user123", [ConsentPurpose.MARKETING], opt_in=True)
        manager.revoke_consent("user123", [ConsentPurpose.MARKETING])
        assert manager.check_consent("user123", ConsentPurpose.MARKETING) is False

    def test_get_consent_history(self) -> None:
        """Test getting consent history."""
        manager = ConsentManager()
        manager.record_consent("user123", [ConsentPurpose.MARKETING], opt_in=True)
        manager.revoke_consent("user123", [ConsentPurpose.MARKETING])
        history = manager.get_consent_history(user_id="user123")
        assert len(history) == 2

    def test_export_consents(self) -> None:
        """Test exporting user consents."""
        manager = ConsentManager()
        manager.record_consent("user123", [ConsentPurpose.MARKETING], opt_in=True)
        export = manager.export_consents("user123")
        assert export["user_id"] == "user123"
        assert len(export["consents"]) == 1

    def test_delete_user_data(self) -> None:
        """Test deleting user data."""
        manager = ConsentManager()
        manager.record_consent("user123", [ConsentPurpose.MARKETING], opt_in=True)
        assert manager.delete_user_data("user123") is True
        assert manager.check_consent("user123", ConsentPurpose.MARKETING) is False


# =============================================================================
# Compliance Validator Tests
# =============================================================================
class TestComplianceValidator:
    """Tests for compliance validation."""

    def test_gdpr_compliance_check(self) -> None:
        """Test GDPR compliance check."""
        validator = ComplianceValidator()
        results = validator.check_gdpr_compliance()
        assert len(results) > 0
        assert all(r.requirement_id.startswith("GDPR") for r in results)

    def test_ccpa_compliance_check(self) -> None:
        """Test CCPA compliance check."""
        validator = ComplianceValidator()
        results = validator.check_ccpa_compliance()
        assert len(results) > 0
        assert all(r.requirement_id.startswith("CCPA") for r in results)

    def test_compliance_score_calculation(self) -> None:
        """Test compliance score calculation."""
        validator = ComplianceValidator()
        validator.set_compliance_state("GDPR-1", True)
        validator.set_compliance_state("GDPR-2", True)
        results = validator.check_gdpr_compliance()
        score = validator.calculate_compliance_score(results)
        assert 0 <= score <= 100

    def test_generate_compliance_report(self) -> None:
        """Test compliance report generation."""
        validator = ComplianceValidator()
        report = validator.generate_compliance_report(ComplianceFramework.GDPR)
        assert "framework" in report
        assert "score" in report
        assert "requirements" in report
        assert "summary" in report

    def test_set_compliance_state(self) -> None:
        """Test setting compliance state."""
        validator = ComplianceValidator()
        validator.set_compliance_state("GDPR-1", True)
        results = validator.check_gdpr_compliance()
        gdpr1 = next(r for r in results if r.requirement_id == "GDPR-1")
        assert gdpr1.status == RequirementStatus.COMPLIANT


# =============================================================================
# Audit Logger Tests
# =============================================================================
class TestAuditLogger:
    """Tests for audit logging."""

    def test_log_event(self) -> None:
        """Test logging an event."""
        logger = AuditLogger()
        event = logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            action="User accessed data",
            user_id="user123"
        )
        assert event.event_id.startswith("EVT-")
        assert event.user_id == "user123"

    def test_query_logs_by_user(self) -> None:
        """Test querying logs by user."""
        logger = AuditLogger()
        logger.log_event(AuditEventType.DATA_ACCESS, "Action 1", user_id="user1")
        logger.log_event(AuditEventType.DATA_ACCESS, "Action 2", user_id="user2")
        results = logger.query_logs(user_id="user1")
        assert len(results) == 1
        assert results[0].user_id == "user1"

    def test_query_logs_by_type(self) -> None:
        """Test querying logs by event type."""
        logger = AuditLogger()
        logger.log_event(AuditEventType.DATA_ACCESS, "Access")
        logger.log_event(AuditEventType.CONSENT_CHANGE, "Consent")
        results = logger.query_logs(event_type=AuditEventType.DATA_ACCESS)
        assert len(results) == 1

    def test_verify_integrity(self) -> None:
        """Test log integrity verification."""
        logger = AuditLogger()
        logger.log_event(AuditEventType.DATA_ACCESS, "Action 1")
        logger.log_event(AuditEventType.DATA_ACCESS, "Action 2")
        assert logger.verify_integrity() is True

    def test_file_persistence(self) -> None:
        """Test logging to file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False
        ) as f:
            log_file = f.name

        try:
            logger = AuditLogger(log_file=log_file)
            logger.log_event(AuditEventType.DATA_ACCESS, "Test action")

            # Create new logger and verify it loads existing logs
            logger2 = AuditLogger(log_file=log_file)
            assert logger2.get_event_count() == 1
        finally:
            if os.path.exists(log_file):
                os.remove(log_file)

    def test_export_logs_json(self) -> None:
        """Test exporting logs as JSON."""
        logger = AuditLogger()
        logger.log_event(AuditEventType.DATA_ACCESS, "Test")
        export = logger.export_logs(format="json")
        data = json.loads(export)
        assert len(data) == 1

    def test_get_events_by_type(self) -> None:
        """Test getting event counts by type."""
        logger = AuditLogger()
        logger.log_event(AuditEventType.DATA_ACCESS, "Access 1")
        logger.log_event(AuditEventType.DATA_ACCESS, "Access 2")
        logger.log_event(AuditEventType.CONSENT_CHANGE, "Consent")
        counts = logger.get_events_by_type()
        assert counts["data_access"] == 2
        assert counts["consent_change"] == 1


# =============================================================================
# Privacy Manager Integration Tests
# =============================================================================
class TestPrivacyManager:
    """Integration tests for Privacy Manager."""

    def test_scan_for_pii(self) -> None:
        """Test PII scanning through manager."""
        manager = PrivacyManager()
        result = manager.scan_for_pii("Contact: test@example.com, 555-123-4567")
        assert result["total_found"] == 2
        assert "email" in result["summary"]

    def test_anonymize_data(self) -> None:
        """Test data anonymization through manager."""
        manager = PrivacyManager()
        result = manager.anonymize_data(
            "Email: test@example.com",
            method="masking"
        )
        assert "test@example.com" not in result

    def test_consent_workflow(self) -> None:
        """Test consent workflow through manager."""
        manager = PrivacyManager()
        manager.record_consent("user123", ["marketing"], opt_in=True)
        assert manager.check_consent("user123", "marketing") is True

    def test_compliance_validation(self) -> None:
        """Test compliance validation through manager."""
        manager = PrivacyManager()
        result = manager.validate_compliance("gdpr")
        assert "score" in result
        assert "requirements" in result

    def test_audit_logging_integration(self) -> None:
        """Test that operations are logged."""
        manager = PrivacyManager()
        manager.scan_for_pii("test@example.com")
        manager.anonymize_data("test@example.com")
        logs = manager.get_audit_logs()
        assert len(logs) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
