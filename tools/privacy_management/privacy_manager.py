"""Privacy Manager - Main Orchestrator and CLI for Privacy Management Platform."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from audit_logger import AuditEventType, AuditLogger
from compliance_validator import ComplianceFramework, ComplianceValidator
from consent_manager import ConsentManager, ConsentPurpose
from data_anonymizer import AnonymizationMethod, DataAnonymizer
from pii_detector import PIIDetector, PIIType


class PrivacyManager:
    """Main orchestrator for privacy management operations."""

    def __init__(
        self,
        audit_log_file: Optional[str] = None,
        anonymizer_salt: Optional[str] = None
    ):
        """
        Initialize Privacy Manager with all components.

        Args:
            audit_log_file: Path to audit log file.
            anonymizer_salt: Salt for anonymization operations.
        """
        self.pii_detector = PIIDetector()
        self.anonymizer = DataAnonymizer(salt=anonymizer_salt)
        self.consent_manager = ConsentManager()
        self.compliance_validator = ComplianceValidator(
            consent_manager=self.consent_manager
        )
        self.audit_logger = AuditLogger(log_file=audit_log_file)

    def scan_for_pii(
        self,
        data: Any,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Scan data for PII and log the operation.

        Args:
            data: Data to scan (text, dict, or DataFrame).
            user_id: User performing the scan.

        Returns:
            Scan results with matches and summary.
        """
        if isinstance(data, str):
            matches = self.pii_detector.scan_text(data)
        elif isinstance(data, dict):
            matches = self.pii_detector.scan_dict(data)
        else:
            try:
                matches = self.pii_detector.scan_dataframe(data)
            except (ImportError, AttributeError):
                matches = []

        self.audit_logger.log_event(
            event_type=AuditEventType.PII_DETECTION,
            action="PII scan performed",
            user_id=user_id,
            details={
                "matches_found": len(matches),
                "pii_types": list(set(m.pii_type.value for m in matches))
            }
        )

        return {
            "matches": [
                {
                    "type": m.pii_type.value,
                    "value": m.value,
                    "confidence": m.confidence,
                    "field": m.field
                }
                for m in matches
            ],
            "summary": self.pii_detector.get_summary(matches),
            "total_found": len(matches)
        }

    def anonymize_data(
        self,
        data: str,
        method: str = "masking",
        user_id: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """
        Detect and anonymize PII in data.

        Args:
            data: Text data to anonymize.
            method: Anonymization method name.
            user_id: User performing the operation.
            **kwargs: Additional method arguments.

        Returns:
            Anonymized data.
        """
        matches = self.pii_detector.scan_text(data)

        method_enum = AnonymizationMethod(method)
        result = self.anonymizer.anonymize_pii(data, matches, method_enum, **kwargs)

        self.audit_logger.log_event(
            event_type=AuditEventType.ANONYMIZATION,
            action=f"Data anonymized using {method}",
            user_id=user_id,
            details={
                "method": method,
                "pii_count": len(matches)
            }
        )

        return result

    def record_consent(
        self,
        user_id: str,
        purposes: List[str],
        opt_in: bool
    ) -> Dict[str, Any]:
        """
        Record user consent.

        Args:
            user_id: User identifier.
            purposes: List of purpose names.
            opt_in: Whether user opted in.

        Returns:
            Consent record details.
        """
        purpose_enums = [ConsentPurpose(p) for p in purposes]
        records = self.consent_manager.record_consent(user_id, purpose_enums, opt_in)

        self.audit_logger.log_event(
            event_type=AuditEventType.CONSENT_CHANGE,
            action="Consent recorded",
            user_id=user_id,
            details={
                "purposes": purposes,
                "opt_in": opt_in
            }
        )

        return {
            "user_id": user_id,
            "purposes": purposes,
            "opt_in": opt_in,
            "records_created": len(records)
        }

    def check_consent(self, user_id: str, purpose: str) -> bool:
        """
        Check if user has granted consent.

        Args:
            user_id: User identifier.
            purpose: Purpose to check.

        Returns:
            True if consent granted.
        """
        return self.consent_manager.check_consent(
            user_id, ConsentPurpose(purpose)
        )

    def validate_compliance(
        self,
        framework: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate compliance with a framework.

        Args:
            framework: Framework name (gdpr, ccpa).
            user_id: Optional user for user-specific checks.
            context: Additional context.

        Returns:
            Compliance report.
        """
        framework_enum = ComplianceFramework(framework)
        report = self.compliance_validator.generate_compliance_report(
            framework_enum, user_id, context
        )

        self.audit_logger.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            action=f"{framework.upper()} compliance check",
            user_id=user_id,
            details={
                "framework": framework,
                "score": report["score"]
            }
        )

        return report

    def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs.

        Args:
            user_id: Filter by user.
            event_type: Filter by event type.
            limit: Maximum results.

        Returns:
            List of audit events.
        """
        event_type_enum = AuditEventType(event_type) if event_type else None
        events = self.audit_logger.query_logs(
            user_id=user_id,
            event_type=event_type_enum,
            limit=limit
        )

        return [
            {
                "event_id": e.event_id,
                "event_type": e.event_type.value,
                "timestamp": e.timestamp,
                "user_id": e.user_id,
                "action": e.action,
                "resource": e.resource,
                "details": e.details
            }
            for e in events
        ]


# CLI Implementation
@click.group()
@click.option("--audit-log", default=None, help="Path to audit log file")
@click.pass_context
def cli(ctx: click.Context, audit_log: Optional[str]) -> None:
    """Privacy Management Platform CLI."""
    ctx.ensure_object(dict)
    ctx.obj["manager"] = PrivacyManager(audit_log_file=audit_log)


@cli.command("scan-pii")
@click.argument("text")
@click.option("--user", default=None, help="User ID")
@click.pass_context
def scan_pii_cmd(ctx: click.Context, text: str, user: Optional[str]) -> None:
    """Scan text for PII."""
    manager: PrivacyManager = ctx.obj["manager"]
    result = manager.scan_for_pii(text, user_id=user)
    click.echo(json.dumps(result, indent=2))


@cli.command("anonymize")
@click.argument("text")
@click.option("--method", default="masking", help="Anonymization method")
@click.option("--user", default=None, help="User ID")
@click.pass_context
def anonymize_cmd(
    ctx: click.Context,
    text: str,
    method: str,
    user: Optional[str]
) -> None:
    """Anonymize PII in text."""
    manager: PrivacyManager = ctx.obj["manager"]
    result = manager.anonymize_data(text, method=method, user_id=user)
    click.echo(result)


@cli.command("check-consent")
@click.argument("user_id")
@click.argument("purpose")
@click.pass_context
def check_consent_cmd(
    ctx: click.Context,
    user_id: str,
    purpose: str
) -> None:
    """Check if user has consent for a purpose."""
    manager: PrivacyManager = ctx.obj["manager"]
    result = manager.check_consent(user_id, purpose)
    click.echo(f"Consent granted: {result}")


@cli.command("validate-compliance")
@click.argument("framework")
@click.option("--user", default=None, help="User ID")
@click.pass_context
def validate_compliance_cmd(
    ctx: click.Context,
    framework: str,
    user: Optional[str]
) -> None:
    """Validate compliance with a framework."""
    manager: PrivacyManager = ctx.obj["manager"]
    result = manager.validate_compliance(framework, user_id=user)
    click.echo(json.dumps(result, indent=2))


@cli.command("audit-log")
@click.option("--user", default=None, help="Filter by user ID")
@click.option("--type", "event_type", default=None, help="Filter by event type")
@click.option("--limit", default=10, help="Maximum results")
@click.pass_context
def audit_log_cmd(
    ctx: click.Context,
    user: Optional[str],
    event_type: Optional[str],
    limit: int
) -> None:
    """View audit logs."""
    manager: PrivacyManager = ctx.obj["manager"]
    result = manager.get_audit_logs(
        user_id=user, event_type=event_type, limit=limit
    )
    click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    cli()
