"""
Violation Tracker for tracking compliance violations.

Provides violation lifecycle management with severity levels.
Part of devCrew_s1 TOOL-SEC-011 compliance management platform.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ViolationSeverity(Enum):
    """Severity levels for violations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ViolationStatus(Enum):
    """Lifecycle status of a violation."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    REMEDIATED = "remediated"
    ACCEPTED_RISK = "accepted_risk"
    FALSE_POSITIVE = "false_positive"
    CLOSED = "closed"


@dataclass
class ViolationHistory:
    """Historical record of violation status change."""

    status: ViolationStatus
    changed_at: datetime
    changed_by: str
    comment: str = ""


@dataclass
class Violation:
    """A compliance violation record."""

    violation_id: str
    rule_name: str
    framework: str
    control_id: str
    severity: ViolationSeverity
    status: ViolationStatus
    description: str
    resource: str
    detected_at: datetime
    updated_at: datetime
    assigned_to: Optional[str] = None
    due_date: Optional[datetime] = None
    remediation_notes: str = ""
    evidence: List[str] = field(default_factory=list)
    history: List[ViolationHistory] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "violation_id": self.violation_id,
            "rule_name": self.rule_name,
            "framework": self.framework,
            "control_id": self.control_id,
            "severity": self.severity.value,
            "status": self.status.value,
            "description": self.description,
            "resource": self.resource,
            "detected_at": self.detected_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "assigned_to": self.assigned_to,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "remediation_notes": self.remediation_notes,
            "evidence": self.evidence,
            "history": [
                {
                    "status": h.status.value,
                    "changed_at": h.changed_at.isoformat(),
                    "changed_by": h.changed_by,
                    "comment": h.comment,
                }
                for h in self.history
            ],
            "metadata": self.metadata,
        }


class ViolationTracker:
    """
    Tracks and manages compliance violations throughout their lifecycle.

    Provides creation, updates, querying, and reporting capabilities
    for compliance violations.
    """

    def __init__(self):
        self._violations: Dict[str, Violation] = {}
        self._severity_weights = {
            ViolationSeverity.CRITICAL: 10,
            ViolationSeverity.HIGH: 7,
            ViolationSeverity.MEDIUM: 4,
            ViolationSeverity.LOW: 2,
            ViolationSeverity.INFO: 1,
        }

    def create_violation(
        self,
        rule_name: str,
        framework: str,
        control_id: str,
        severity: ViolationSeverity,
        description: str,
        resource: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Violation:
        """
        Create a new violation record.

        Args:
            rule_name: Name of the violated rule
            framework: Compliance framework
            control_id: Control identifier
            severity: Violation severity
            description: Description of violation
            resource: Affected resource
            metadata: Additional metadata

        Returns:
            Created Violation object
        """
        violation_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow()

        violation = Violation(
            violation_id=violation_id,
            rule_name=rule_name,
            framework=framework,
            control_id=control_id,
            severity=severity,
            status=ViolationStatus.OPEN,
            description=description,
            resource=resource,
            detected_at=now,
            updated_at=now,
            metadata=metadata or {},
        )

        violation.history.append(ViolationHistory(
            status=ViolationStatus.OPEN,
            changed_at=now,
            changed_by="system",
            comment="Violation detected",
        ))

        self._violations[violation_id] = violation
        return violation

    def update_status(
        self,
        violation_id: str,
        new_status: ViolationStatus,
        changed_by: str,
        comment: str = "",
    ) -> Optional[Violation]:
        """Update violation status with audit trail."""
        violation = self._violations.get(violation_id)
        if not violation:
            return None

        now = datetime.utcnow()
        violation.history.append(ViolationHistory(
            status=new_status,
            changed_at=now,
            changed_by=changed_by,
            comment=comment,
        ))

        violation.status = new_status
        violation.updated_at = now

        return violation

    def assign_violation(
        self,
        violation_id: str,
        assignee: str,
        due_date: Optional[datetime] = None,
    ) -> Optional[Violation]:
        """Assign violation to a team member."""
        violation = self._violations.get(violation_id)
        if not violation:
            return None

        violation.assigned_to = assignee
        violation.due_date = due_date
        violation.updated_at = datetime.utcnow()

        return violation

    def add_evidence(self, violation_id: str, evidence: str) -> Optional[Violation]:
        """Add evidence to a violation."""
        violation = self._violations.get(violation_id)
        if not violation:
            return None

        violation.evidence.append(evidence)
        violation.updated_at = datetime.utcnow()

        return violation

    def add_remediation_notes(
        self, violation_id: str, notes: str
    ) -> Optional[Violation]:
        """Add remediation notes to a violation."""
        violation = self._violations.get(violation_id)
        if not violation:
            return None

        violation.remediation_notes = notes
        violation.updated_at = datetime.utcnow()

        return violation

    def get_violation(self, violation_id: str) -> Optional[Violation]:
        """Get violation by ID."""
        return self._violations.get(violation_id)

    def get_all_violations(self) -> List[Violation]:
        """Get all violations."""
        return list(self._violations.values())

    def get_violations_by_status(self, status: ViolationStatus) -> List[Violation]:
        """Get violations filtered by status."""
        return [v for v in self._violations.values() if v.status == status]

    def get_violations_by_severity(
        self, severity: ViolationSeverity
    ) -> List[Violation]:
        """Get violations filtered by severity."""
        return [v for v in self._violations.values() if v.severity == severity]

    def get_violations_by_framework(self, framework: str) -> List[Violation]:
        """Get violations filtered by framework."""
        return [v for v in self._violations.values() if v.framework == framework]

    def get_open_violations(self) -> List[Violation]:
        """Get all open violations."""
        open_statuses = {
            ViolationStatus.OPEN,
            ViolationStatus.ACKNOWLEDGED,
            ViolationStatus.IN_PROGRESS,
        }
        return [v for v in self._violations.values() if v.status in open_statuses]

    def get_overdue_violations(self) -> List[Violation]:
        """Get violations past their due date."""
        now = datetime.utcnow()
        return [
            v for v in self._violations.values()
            if v.due_date and v.due_date < now
            and v.status not in {
                ViolationStatus.REMEDIATED,
                ViolationStatus.CLOSED,
                ViolationStatus.FALSE_POSITIVE,
            }
        ]

    def calculate_risk_score(self) -> float:
        """
        Calculate overall risk score based on open violations.

        Returns:
            Risk score (0-100)
        """
        open_violations = self.get_open_violations()
        if not open_violations:
            return 0.0

        total_weight = sum(
            self._severity_weights[v.severity] for v in open_violations
        )
        max_possible = len(open_violations) * self._severity_weights[ViolationSeverity.CRITICAL]

        return (total_weight / max_possible * 100) if max_possible > 0 else 0.0

    def get_statistics(self) -> Dict[str, Any]:
        """Get violation statistics."""
        all_violations = list(self._violations.values())

        by_status = {}
        for status in ViolationStatus:
            by_status[status.value] = sum(
                1 for v in all_violations if v.status == status
            )

        by_severity = {}
        for severity in ViolationSeverity:
            by_severity[severity.value] = sum(
                1 for v in all_violations if v.severity == severity
            )

        by_framework: Dict[str, int] = {}
        for v in all_violations:
            by_framework[v.framework] = by_framework.get(v.framework, 0) + 1

        return {
            "total_violations": len(all_violations),
            "open_violations": len(self.get_open_violations()),
            "overdue_violations": len(self.get_overdue_violations()),
            "risk_score": self.calculate_risk_score(),
            "by_status": by_status,
            "by_severity": by_severity,
            "by_framework": by_framework,
        }

    def bulk_create_from_assessment(
        self,
        framework: str,
        assessment_details: Dict[str, Any],
    ) -> List[Violation]:
        """Create violations from compliance assessment results."""
        violations: List[Violation] = []

        for control in assessment_details.get("controls", []):
            if not control.get("passed", True):
                for violation_data in control.get("violations", []):
                    severity_str = violation_data.get("severity", "medium")
                    severity = ViolationSeverity(severity_str)

                    violation = self.create_violation(
                        rule_name=violation_data.get("rule", "unknown"),
                        framework=framework,
                        control_id=control.get("control_id", "unknown"),
                        severity=severity,
                        description=violation_data.get("message", ""),
                        resource=control.get("name", "unknown"),
                    )
                    violations.append(violation)

        return violations

    def export_violations(
        self, violations: Optional[List[Violation]] = None
    ) -> List[Dict[str, Any]]:
        """Export violations to list of dictionaries."""
        if violations is None:
            violations = list(self._violations.values())
        return [v.to_dict() for v in violations]

    def delete_violation(self, violation_id: str) -> bool:
        """Delete a violation record."""
        if violation_id in self._violations:
            del self._violations[violation_id]
            return True
        return False

    def clear_all(self) -> int:
        """Clear all violations. Returns count deleted."""
        count = len(self._violations)
        self._violations.clear()
        return count
