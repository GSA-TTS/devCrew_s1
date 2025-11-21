"""Compliance Validation Module for Privacy Management Platform."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from consent_manager import ConsentManager, ConsentPurpose


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"


class RequirementStatus(Enum):
    """Status of a compliance requirement."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class ComplianceRequirement:
    """Represents a compliance requirement."""
    id: str
    name: str
    description: str
    framework: ComplianceFramework
    check_function: Optional[Callable[..., bool]] = None


@dataclass
class ComplianceResult:
    """Result of a compliance check."""
    requirement_id: str
    requirement_name: str
    status: RequirementStatus
    details: str
    timestamp: datetime


class ComplianceValidator:
    """Validates compliance with privacy regulations."""

    # GDPR Requirements
    GDPR_REQUIREMENTS = [
        ComplianceRequirement(
            id="GDPR-1",
            name="Lawful Basis",
            description="Processing must have a lawful basis (consent, contract, etc.)",
            framework=ComplianceFramework.GDPR
        ),
        ComplianceRequirement(
            id="GDPR-2",
            name="Consent Records",
            description="Consent must be documented with timestamp and purpose",
            framework=ComplianceFramework.GDPR
        ),
        ComplianceRequirement(
            id="GDPR-3",
            name="Right to Erasure",
            description="Users can request deletion of their data",
            framework=ComplianceFramework.GDPR
        ),
        ComplianceRequirement(
            id="GDPR-4",
            name="Data Portability",
            description="Users can export their data in machine-readable format",
            framework=ComplianceFramework.GDPR
        ),
        ComplianceRequirement(
            id="GDPR-5",
            name="Data Minimization",
            description="Only collect data necessary for the stated purpose",
            framework=ComplianceFramework.GDPR
        ),
        ComplianceRequirement(
            id="GDPR-6",
            name="Breach Notification",
            description="Data breaches must be reported within 72 hours",
            framework=ComplianceFramework.GDPR
        ),
    ]

    # CCPA Requirements
    CCPA_REQUIREMENTS = [
        ComplianceRequirement(
            id="CCPA-1",
            name="Right to Know",
            description="Consumers can request info about data collected",
            framework=ComplianceFramework.CCPA
        ),
        ComplianceRequirement(
            id="CCPA-2",
            name="Right to Delete",
            description="Consumers can request deletion of their data",
            framework=ComplianceFramework.CCPA
        ),
        ComplianceRequirement(
            id="CCPA-3",
            name="Right to Opt-Out",
            description="Consumers can opt-out of sale of personal info",
            framework=ComplianceFramework.CCPA
        ),
        ComplianceRequirement(
            id="CCPA-4",
            name="Non-Discrimination",
            description="Cannot discriminate against users who exercise rights",
            framework=ComplianceFramework.CCPA
        ),
        ComplianceRequirement(
            id="CCPA-5",
            name="Privacy Notice",
            description="Must provide notice at collection",
            framework=ComplianceFramework.CCPA
        ),
    ]

    def __init__(self, consent_manager: Optional[ConsentManager] = None):
        """
        Initialize Compliance Validator.

        Args:
            consent_manager: Optional consent manager for consent checks.
        """
        self.consent_manager = consent_manager
        self._compliance_state: Dict[str, bool] = {}

    def set_compliance_state(self, requirement_id: str, compliant: bool) -> None:
        """
        Set compliance state for a requirement.

        Args:
            requirement_id: Requirement ID.
            compliant: Whether compliant.
        """
        self._compliance_state[requirement_id] = compliant

    def check_gdpr_compliance(
        self,
        user_id: Optional[str] = None,
        data_context: Optional[Dict[str, Any]] = None
    ) -> List[ComplianceResult]:
        """
        Check GDPR compliance.

        Args:
            user_id: Optional user ID for user-specific checks.
            data_context: Additional context for checks.

        Returns:
            List of compliance results.
        """
        results = []
        timestamp = datetime.now()

        for req in self.GDPR_REQUIREMENTS:
            # Check if state is manually set
            if req.id in self._compliance_state:
                status = (
                    RequirementStatus.COMPLIANT
                    if self._compliance_state[req.id]
                    else RequirementStatus.NON_COMPLIANT
                )
                details = "Status set via compliance state"
            else:
                # Default checks
                status, details = self._evaluate_gdpr_requirement(
                    req, user_id, data_context
                )

            results.append(ComplianceResult(
                requirement_id=req.id,
                requirement_name=req.name,
                status=status,
                details=details,
                timestamp=timestamp
            ))

        return results

    def _evaluate_gdpr_requirement(
        self,
        requirement: ComplianceRequirement,
        user_id: Optional[str],
        data_context: Optional[Dict[str, Any]]
    ) -> tuple:
        """Evaluate a GDPR requirement."""
        context = data_context or {}

        if requirement.id == "GDPR-2" and self.consent_manager and user_id:
            # Check consent records
            history = self.consent_manager.get_consent_history(user_id=user_id)
            if history:
                return (
                    RequirementStatus.COMPLIANT,
                    f"Found {len(history)} consent records"
                )
            return (
                RequirementStatus.NON_COMPLIANT,
                "No consent records found"
            )

        if requirement.id == "GDPR-3":
            # Check if deletion capability exists
            has_deletion = context.get("has_deletion_capability", False)
            if has_deletion:
                return RequirementStatus.COMPLIANT, "Deletion capability available"
            return RequirementStatus.PARTIAL, "Deletion capability not verified"

        if requirement.id == "GDPR-4":
            # Check if export capability exists
            has_export = context.get("has_export_capability", False)
            if has_export:
                return RequirementStatus.COMPLIANT, "Export capability available"
            return RequirementStatus.PARTIAL, "Export capability not verified"

        return RequirementStatus.PARTIAL, "Requires manual verification"

    def check_ccpa_compliance(
        self,
        user_id: Optional[str] = None,
        data_context: Optional[Dict[str, Any]] = None
    ) -> List[ComplianceResult]:
        """
        Check CCPA compliance.

        Args:
            user_id: Optional user ID for user-specific checks.
            data_context: Additional context for checks.

        Returns:
            List of compliance results.
        """
        results = []
        timestamp = datetime.now()

        for req in self.CCPA_REQUIREMENTS:
            if req.id in self._compliance_state:
                status = (
                    RequirementStatus.COMPLIANT
                    if self._compliance_state[req.id]
                    else RequirementStatus.NON_COMPLIANT
                )
                details = "Status set via compliance state"
            else:
                status, details = self._evaluate_ccpa_requirement(
                    req, user_id, data_context
                )

            results.append(ComplianceResult(
                requirement_id=req.id,
                requirement_name=req.name,
                status=status,
                details=details,
                timestamp=timestamp
            ))

        return results

    def _evaluate_ccpa_requirement(
        self,
        requirement: ComplianceRequirement,
        user_id: Optional[str],
        data_context: Optional[Dict[str, Any]]
    ) -> tuple:
        """Evaluate a CCPA requirement."""
        context = data_context or {}

        if requirement.id == "CCPA-3" and self.consent_manager and user_id:
            # Check opt-out capability
            has_third_party = self.consent_manager.check_consent(
                user_id, ConsentPurpose.THIRD_PARTY_SHARING
            )
            if not has_third_party:
                return (
                    RequirementStatus.COMPLIANT,
                    "User has opted out of third-party sharing"
                )
            return RequirementStatus.PARTIAL, "User has not opted out"

        if requirement.id == "CCPA-5":
            has_notice = context.get("has_privacy_notice", False)
            if has_notice:
                return RequirementStatus.COMPLIANT, "Privacy notice available"
            return RequirementStatus.NON_COMPLIANT, "Privacy notice not found"

        return RequirementStatus.PARTIAL, "Requires manual verification"

    def calculate_compliance_score(
        self,
        results: List[ComplianceResult]
    ) -> float:
        """
        Calculate compliance score as percentage.

        Args:
            results: List of compliance results.

        Returns:
            Compliance score (0-100).
        """
        if not results:
            return 0.0

        compliant_count = sum(
            1 for r in results if r.status == RequirementStatus.COMPLIANT
        )
        partial_count = sum(
            1 for r in results if r.status == RequirementStatus.PARTIAL
        )
        applicable_count = sum(
            1 for r in results if r.status != RequirementStatus.NOT_APPLICABLE
        )

        if applicable_count == 0:
            return 100.0

        # Full compliance = 1 point, partial = 0.5 points
        score = (compliant_count + partial_count * 0.5) / applicable_count * 100
        return round(score, 2)

    def generate_compliance_report(
        self,
        framework: ComplianceFramework,
        user_id: Optional[str] = None,
        data_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a compliance report.

        Args:
            framework: Compliance framework to check.
            user_id: Optional user ID.
            data_context: Additional context.

        Returns:
            Compliance report dictionary.
        """
        if framework == ComplianceFramework.GDPR:
            results = self.check_gdpr_compliance(user_id, data_context)
        elif framework == ComplianceFramework.CCPA:
            results = self.check_ccpa_compliance(user_id, data_context)
        else:
            results = []

        score = self.calculate_compliance_score(results)

        return {
            "framework": framework.value,
            "score": score,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "requirements": [
                {
                    "id": r.requirement_id,
                    "name": r.requirement_name,
                    "status": r.status.value,
                    "details": r.details
                }
                for r in results
            ],
            "summary": {
                "total": len(results),
                "compliant": sum(
                    1 for r in results if r.status == RequirementStatus.COMPLIANT
                ),
                "non_compliant": sum(
                    1 for r in results if r.status == RequirementStatus.NON_COMPLIANT
                ),
                "partial": sum(
                    1 for r in results if r.status == RequirementStatus.PARTIAL
                )
            }
        }
