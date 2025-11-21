"""
Compliance Manager for multiple regulatory frameworks.

Supports GDPR, HIPAA, FedRAMP, SOC2, ISO 27001, and NIST 800-53.
Part of devCrew_s1 TOOL-SEC-011 compliance management platform.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .policy_engine import PolicyEngine, PolicyDecision


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""

    GDPR = "gdpr"
    HIPAA = "hipaa"
    FEDRAMP = "fedramp"
    SOC2 = "soc2"
    ISO_27001 = "iso_27001"
    NIST_800_53 = "nist_800_53"


class ComplianceStatus(Enum):
    """Compliance assessment status."""

    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_ASSESSED = "not_assessed"


@dataclass
class ComplianceScore:
    """Compliance score for a framework."""

    framework: ComplianceFramework
    score: float  # 0-100
    total_controls: int
    passed_controls: int
    failed_controls: int
    not_applicable: int
    status: ComplianceStatus
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "framework": self.framework.value,
            "score": self.score,
            "total_controls": self.total_controls,
            "passed_controls": self.passed_controls,
            "failed_controls": self.failed_controls,
            "not_applicable": self.not_applicable,
            "status": self.status.value,
            "assessed_at": self.assessed_at.isoformat(),
            "details": self.details,
        }


@dataclass
class FrameworkControl:
    """A control within a compliance framework."""

    control_id: str
    name: str
    description: str
    category: str
    required_rules: List[str]
    severity: str = "medium"


class ComplianceManager:
    """
    Manages compliance assessments across multiple frameworks.

    Provides unified interface for evaluating compliance against
    GDPR, HIPAA, FedRAMP, SOC2, ISO 27001, and NIST 800-53.
    """

    def __init__(self, policy_engine: Optional[PolicyEngine] = None):
        self.policy_engine = policy_engine or PolicyEngine()
        self._frameworks = self._initialize_frameworks()
        self._assessment_history: List[ComplianceScore] = []

    def _initialize_frameworks(self) -> Dict[ComplianceFramework, List[FrameworkControl]]:
        """Initialize framework control definitions."""
        return {
            ComplianceFramework.GDPR: [
                FrameworkControl(
                    "GDPR-5.1", "Lawfulness of Processing",
                    "Personal data shall be processed lawfully",
                    "Data Processing", ["consent_management"]
                ),
                FrameworkControl(
                    "GDPR-5.2", "Data Minimization",
                    "Personal data shall be adequate, relevant and limited",
                    "Data Processing", ["data_minimization"]
                ),
                FrameworkControl(
                    "GDPR-32", "Security of Processing",
                    "Implement appropriate technical measures",
                    "Security", ["data_encryption", "access_control"]
                ),
                FrameworkControl(
                    "GDPR-33", "Breach Notification",
                    "Notify supervisory authority of breaches",
                    "Incident Response", ["breach_notification"]
                ),
                FrameworkControl(
                    "GDPR-30", "Records of Processing",
                    "Maintain records of processing activities",
                    "Documentation", ["audit_logging"]
                ),
            ],
            ComplianceFramework.HIPAA: [
                FrameworkControl(
                    "164.312(a)", "Access Control",
                    "Implement access controls for ePHI",
                    "Technical Safeguards", ["access_control", "authentication"]
                ),
                FrameworkControl(
                    "164.312(b)", "Audit Controls",
                    "Implement audit controls",
                    "Technical Safeguards", ["audit_logging"]
                ),
                FrameworkControl(
                    "164.312(e)", "Transmission Security",
                    "Protect ePHI during transmission",
                    "Technical Safeguards", ["data_encryption"]
                ),
                FrameworkControl(
                    "164.308(a)(6)", "Security Incident Procedures",
                    "Implement policies for security incidents",
                    "Administrative Safeguards", ["breach_notification"]
                ),
                FrameworkControl(
                    "164.310(d)", "Device and Media Controls",
                    "Implement policies for device handling",
                    "Physical Safeguards", ["data_retention"]
                ),
            ],
            ComplianceFramework.FEDRAMP: [
                FrameworkControl(
                    "AC-2", "Account Management",
                    "Manage system accounts",
                    "Access Control", ["access_control", "authentication"]
                ),
                FrameworkControl(
                    "AU-2", "Audit Events",
                    "Audit system events",
                    "Audit and Accountability", ["audit_logging"]
                ),
                FrameworkControl(
                    "SC-8", "Transmission Confidentiality",
                    "Protect transmitted information",
                    "System and Communications", ["data_encryption"]
                ),
                FrameworkControl(
                    "SC-28", "Protection of Information at Rest",
                    "Protect information at rest",
                    "System and Communications", ["data_encryption"]
                ),
                FrameworkControl(
                    "IR-6", "Incident Reporting",
                    "Report security incidents",
                    "Incident Response", ["breach_notification"]
                ),
                FrameworkControl(
                    "RA-5", "Vulnerability Scanning",
                    "Scan for vulnerabilities",
                    "Risk Assessment", ["vulnerability_management"]
                ),
            ],
            ComplianceFramework.SOC2: [
                FrameworkControl(
                    "CC6.1", "Logical Access Security",
                    "Implement logical access security",
                    "Common Criteria", ["access_control", "authentication"]
                ),
                FrameworkControl(
                    "CC6.7", "Data Transmission Protection",
                    "Protect data during transmission",
                    "Common Criteria", ["data_encryption"]
                ),
                FrameworkControl(
                    "CC7.2", "System Monitoring",
                    "Monitor system components",
                    "Common Criteria", ["audit_logging"]
                ),
                FrameworkControl(
                    "CC7.3", "Security Incident Detection",
                    "Detect security incidents",
                    "Common Criteria", ["breach_notification"]
                ),
                FrameworkControl(
                    "CC7.4", "Incident Response",
                    "Respond to security incidents",
                    "Common Criteria", ["breach_notification"]
                ),
            ],
            ComplianceFramework.ISO_27001: [
                FrameworkControl(
                    "A.9.1", "Access Control Policy",
                    "Establish access control policy",
                    "Access Control", ["access_control"]
                ),
                FrameworkControl(
                    "A.9.4", "System Access Control",
                    "Prevent unauthorized system access",
                    "Access Control", ["authentication"]
                ),
                FrameworkControl(
                    "A.10.1", "Cryptographic Controls",
                    "Use cryptographic controls",
                    "Cryptography", ["data_encryption"]
                ),
                FrameworkControl(
                    "A.12.4", "Logging and Monitoring",
                    "Record and monitor events",
                    "Operations Security", ["audit_logging"]
                ),
                FrameworkControl(
                    "A.13.1", "Network Security Management",
                    "Manage network security",
                    "Communications Security", ["network_security"]
                ),
                FrameworkControl(
                    "A.16.1", "Incident Management",
                    "Manage security incidents",
                    "Incident Management", ["breach_notification"]
                ),
            ],
            ComplianceFramework.NIST_800_53: [
                FrameworkControl(
                    "AC-1", "Access Control Policy",
                    "Develop access control policy",
                    "Access Control", ["access_control"]
                ),
                FrameworkControl(
                    "AC-2", "Account Management",
                    "Manage system accounts",
                    "Access Control", ["access_control", "authentication"]
                ),
                FrameworkControl(
                    "AU-2", "Event Logging",
                    "Log security events",
                    "Audit and Accountability", ["audit_logging"]
                ),
                FrameworkControl(
                    "SC-8", "Transmission Confidentiality",
                    "Protect transmitted data",
                    "System and Communications", ["data_encryption"]
                ),
                FrameworkControl(
                    "SC-13", "Cryptographic Protection",
                    "Implement cryptographic protection",
                    "System and Communications", ["data_encryption"]
                ),
                FrameworkControl(
                    "IR-6", "Incident Reporting",
                    "Report security incidents",
                    "Incident Response", ["breach_notification"]
                ),
                FrameworkControl(
                    "RA-5", "Vulnerability Monitoring",
                    "Monitor for vulnerabilities",
                    "Risk Assessment", ["vulnerability_management"]
                ),
            ],
        }

    def assess_compliance(
        self, framework: ComplianceFramework, input_data: Dict[str, Any]
    ) -> ComplianceScore:
        """
        Assess compliance against a specific framework.

        Args:
            framework: Framework to assess against
            input_data: System/application data to evaluate

        Returns:
            ComplianceScore with assessment results
        """
        controls = self._frameworks.get(framework, [])
        if not controls:
            return ComplianceScore(
                framework=framework,
                score=0.0,
                total_controls=0,
                passed_controls=0,
                failed_controls=0,
                not_applicable=0,
                status=ComplianceStatus.NOT_ASSESSED,
            )

        passed = 0
        failed = 0
        details: Dict[str, Any] = {"controls": []}

        for control in controls:
            result = self.policy_engine.evaluate_with_rules(
                control.required_rules, input_data
            )
            control_passed = result.decision == PolicyDecision.ALLOW

            if control_passed:
                passed += 1
            else:
                failed += 1

            details["controls"].append({
                "control_id": control.control_id,
                "name": control.name,
                "category": control.category,
                "passed": control_passed,
                "violations": result.violations,
            })

        total = len(controls)
        score = (passed / total * 100) if total > 0 else 0.0

        if score >= 100:
            status = ComplianceStatus.COMPLIANT
        elif score >= 70:
            status = ComplianceStatus.PARTIAL
        else:
            status = ComplianceStatus.NON_COMPLIANT

        compliance_score = ComplianceScore(
            framework=framework,
            score=round(score, 2),
            total_controls=total,
            passed_controls=passed,
            failed_controls=failed,
            not_applicable=0,
            status=status,
            details=details,
        )

        self._assessment_history.append(compliance_score)
        return compliance_score

    def assess_all_frameworks(
        self, input_data: Dict[str, Any]
    ) -> Dict[ComplianceFramework, ComplianceScore]:
        """Assess compliance against all supported frameworks."""
        results = {}
        for framework in ComplianceFramework:
            results[framework] = self.assess_compliance(framework, input_data)
        return results

    def get_framework_controls(
        self, framework: ComplianceFramework
    ) -> List[FrameworkControl]:
        """Get controls for a specific framework."""
        return self._frameworks.get(framework, [])

    def get_assessment_history(self) -> List[ComplianceScore]:
        """Get history of all assessments."""
        return self._assessment_history.copy()

    def get_supported_frameworks(self) -> List[ComplianceFramework]:
        """Get list of supported frameworks."""
        return list(ComplianceFramework)

    def get_overall_compliance_status(
        self, scores: Dict[ComplianceFramework, ComplianceScore]
    ) -> ComplianceStatus:
        """Calculate overall compliance status from multiple framework scores."""
        if not scores:
            return ComplianceStatus.NOT_ASSESSED

        all_compliant = all(
            s.status == ComplianceStatus.COMPLIANT for s in scores.values()
        )
        any_non_compliant = any(
            s.status == ComplianceStatus.NON_COMPLIANT for s in scores.values()
        )

        if all_compliant:
            return ComplianceStatus.COMPLIANT
        elif any_non_compliant:
            return ComplianceStatus.NON_COMPLIANT
        else:
            return ComplianceStatus.PARTIAL

    def export_assessment(
        self, score: ComplianceScore, format_type: str = "dict"
    ) -> Any:
        """Export assessment in specified format."""
        if format_type == "dict":
            return score.to_dict()
        return score.to_dict()
