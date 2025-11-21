"""
Regulatory Mapper for mapping policies to regulatory controls.

Provides compliance matrix generation and control mapping capabilities.
Part of devCrew_s1 TOOL-SEC-011 compliance management platform.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .compliance_manager import ComplianceFramework


@dataclass
class ControlMapping:
    """Mapping between a policy rule and regulatory controls."""

    rule_name: str
    frameworks: Dict[str, List[str]]  # framework -> list of control IDs
    description: str = ""
    evidence_requirements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_name": self.rule_name,
            "frameworks": self.frameworks,
            "description": self.description,
            "evidence_requirements": self.evidence_requirements,
        }


@dataclass
class ComplianceMatrixEntry:
    """Entry in the compliance matrix."""

    control_id: str
    framework: str
    control_name: str
    mapped_rules: List[str]
    status: str  # mapped, partial, unmapped
    coverage_percentage: float


@dataclass
class ComplianceMatrix:
    """Full compliance matrix across frameworks."""

    entries: List[ComplianceMatrixEntry]
    generated_at: datetime = field(default_factory=datetime.utcnow)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entries": [
                {
                    "control_id": e.control_id,
                    "framework": e.framework,
                    "control_name": e.control_name,
                    "mapped_rules": e.mapped_rules,
                    "status": e.status,
                    "coverage_percentage": e.coverage_percentage,
                }
                for e in self.entries
            ],
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary,
        }

    def filter_by_framework(self, framework: str) -> "ComplianceMatrix":
        """Filter matrix to specific framework."""
        filtered = [e for e in self.entries if e.framework == framework]
        return ComplianceMatrix(entries=filtered, summary=self.summary)


class RegulatoryMapper:
    """
    Maps policy rules to regulatory framework controls.

    Provides bidirectional mapping between technical policy rules
    and compliance framework requirements.
    """

    def __init__(self):
        self._mappings = self._initialize_mappings()
        self._control_catalog = self._initialize_control_catalog()

    def _initialize_mappings(self) -> Dict[str, ControlMapping]:
        """Initialize rule-to-control mappings."""
        return {
            "data_encryption": ControlMapping(
                rule_name="data_encryption",
                frameworks={
                    "gdpr": ["GDPR-32"],
                    "hipaa": ["164.312(e)"],
                    "fedramp": ["SC-8", "SC-28"],
                    "soc2": ["CC6.7"],
                    "iso_27001": ["A.10.1"],
                    "nist_800_53": ["SC-8", "SC-13"],
                },
                description="Encryption of data at rest and in transit",
                evidence_requirements=[
                    "Encryption configuration documentation",
                    "Certificate management records",
                    "Key rotation logs",
                ],
            ),
            "access_control": ControlMapping(
                rule_name="access_control",
                frameworks={
                    "gdpr": ["GDPR-32"],
                    "hipaa": ["164.312(a)"],
                    "fedramp": ["AC-2"],
                    "soc2": ["CC6.1"],
                    "iso_27001": ["A.9.1"],
                    "nist_800_53": ["AC-1", "AC-2"],
                },
                description="Access control policies and enforcement",
                evidence_requirements=[
                    "Access control policy documents",
                    "User access review records",
                    "Role-based access configurations",
                ],
            ),
            "audit_logging": ControlMapping(
                rule_name="audit_logging",
                frameworks={
                    "gdpr": ["GDPR-30"],
                    "hipaa": ["164.312(b)"],
                    "fedramp": ["AU-2"],
                    "soc2": ["CC7.2"],
                    "iso_27001": ["A.12.4"],
                    "nist_800_53": ["AU-2"],
                },
                description="Audit logging and monitoring",
                evidence_requirements=[
                    "Audit log configurations",
                    "Log retention policies",
                    "Log review procedures",
                ],
            ),
            "breach_notification": ControlMapping(
                rule_name="breach_notification",
                frameworks={
                    "gdpr": ["GDPR-33"],
                    "hipaa": ["164.308(a)(6)"],
                    "fedramp": ["IR-6"],
                    "soc2": ["CC7.3", "CC7.4"],
                    "iso_27001": ["A.16.1"],
                    "nist_800_53": ["IR-6"],
                },
                description="Security incident and breach notification",
                evidence_requirements=[
                    "Incident response plan",
                    "Notification procedures",
                    "Incident log records",
                ],
            ),
            "consent_management": ControlMapping(
                rule_name="consent_management",
                frameworks={
                    "gdpr": ["GDPR-5.1"],
                },
                description="User consent management for data processing",
                evidence_requirements=[
                    "Consent collection mechanisms",
                    "Consent records database",
                    "Consent withdrawal procedures",
                ],
            ),
            "data_minimization": ControlMapping(
                rule_name="data_minimization",
                frameworks={
                    "gdpr": ["GDPR-5.2"],
                },
                description="Collection of only necessary data",
                evidence_requirements=[
                    "Data inventory documentation",
                    "Purpose limitation policies",
                    "Data collection justifications",
                ],
            ),
            "authentication": ControlMapping(
                rule_name="authentication",
                frameworks={
                    "hipaa": ["164.312(a)"],
                    "fedramp": ["AC-2"],
                    "soc2": ["CC6.1"],
                    "iso_27001": ["A.9.4"],
                    "nist_800_53": ["AC-2"],
                },
                description="Authentication mechanisms including MFA",
                evidence_requirements=[
                    "Authentication policy",
                    "MFA implementation evidence",
                    "Password policy configurations",
                ],
            ),
            "data_retention": ControlMapping(
                rule_name="data_retention",
                frameworks={
                    "hipaa": ["164.310(d)"],
                },
                description="Data retention and disposal policies",
                evidence_requirements=[
                    "Retention schedule",
                    "Disposal procedures",
                    "Disposal verification records",
                ],
            ),
            "network_security": ControlMapping(
                rule_name="network_security",
                frameworks={
                    "iso_27001": ["A.13.1"],
                },
                description="Network security controls",
                evidence_requirements=[
                    "Network architecture diagrams",
                    "Firewall configurations",
                    "Network segmentation documentation",
                ],
            ),
            "vulnerability_management": ControlMapping(
                rule_name="vulnerability_management",
                frameworks={
                    "fedramp": ["RA-5"],
                    "nist_800_53": ["RA-5"],
                },
                description="Vulnerability scanning and management",
                evidence_requirements=[
                    "Vulnerability scan reports",
                    "Remediation tracking records",
                    "Scanning schedule documentation",
                ],
            ),
        }

    def _initialize_control_catalog(self) -> Dict[str, Dict[str, str]]:
        """Initialize control catalog with descriptions."""
        return {
            "gdpr": {
                "GDPR-5.1": "Lawfulness, fairness and transparency",
                "GDPR-5.2": "Purpose limitation and data minimization",
                "GDPR-30": "Records of processing activities",
                "GDPR-32": "Security of processing",
                "GDPR-33": "Notification of personal data breach",
            },
            "hipaa": {
                "164.312(a)": "Access Control (Technical Safeguards)",
                "164.312(b)": "Audit Controls (Technical Safeguards)",
                "164.312(e)": "Transmission Security (Technical Safeguards)",
                "164.308(a)(6)": "Security Incident Procedures",
                "164.310(d)": "Device and Media Controls",
            },
            "fedramp": {
                "AC-2": "Account Management",
                "AU-2": "Audit Events",
                "SC-8": "Transmission Confidentiality and Integrity",
                "SC-28": "Protection of Information at Rest",
                "IR-6": "Incident Reporting",
                "RA-5": "Vulnerability Scanning",
            },
            "soc2": {
                "CC6.1": "Logical and Physical Access Controls",
                "CC6.7": "Restriction and Protection of Information",
                "CC7.2": "System Monitoring",
                "CC7.3": "Detection of Unauthorized Activities",
                "CC7.4": "Response to Identified Incidents",
            },
            "iso_27001": {
                "A.9.1": "Access Control Policy",
                "A.9.4": "System and Application Access Control",
                "A.10.1": "Cryptographic Controls",
                "A.12.4": "Logging and Monitoring",
                "A.13.1": "Network Security Management",
                "A.16.1": "Management of Information Security Incidents",
            },
            "nist_800_53": {
                "AC-1": "Access Control Policy and Procedures",
                "AC-2": "Account Management",
                "AU-2": "Event Logging",
                "SC-8": "Transmission Confidentiality and Integrity",
                "SC-13": "Cryptographic Protection",
                "IR-6": "Incident Reporting",
                "RA-5": "Vulnerability Monitoring and Scanning",
            },
        }

    def get_mapping(self, rule_name: str) -> Optional[ControlMapping]:
        """Get mapping for a specific rule."""
        return self._mappings.get(rule_name)

    def get_rules_for_control(
        self, framework: str, control_id: str
    ) -> List[str]:
        """Get rules mapped to a specific control."""
        rules: List[str] = []
        for rule_name, mapping in self._mappings.items():
            framework_controls = mapping.frameworks.get(framework, [])
            if control_id in framework_controls:
                rules.append(rule_name)
        return rules

    def get_controls_for_rule(
        self, rule_name: str, framework: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Get controls mapped to a specific rule."""
        mapping = self._mappings.get(rule_name)
        if not mapping:
            return {}

        if framework:
            return {framework: mapping.frameworks.get(framework, [])}
        return mapping.frameworks

    def generate_compliance_matrix(
        self, frameworks: Optional[List[str]] = None
    ) -> ComplianceMatrix:
        """
        Generate compliance matrix for specified frameworks.

        Args:
            frameworks: List of framework names (None for all)

        Returns:
            ComplianceMatrix with all mappings
        """
        if frameworks is None:
            frameworks = list(self._control_catalog.keys())

        entries: List[ComplianceMatrixEntry] = []
        framework_stats: Dict[str, Dict[str, int]] = {}

        for framework in frameworks:
            controls = self._control_catalog.get(framework, {})
            mapped_count = 0
            total_count = len(controls)

            for control_id, control_name in controls.items():
                mapped_rules = self.get_rules_for_control(framework, control_id)

                if len(mapped_rules) > 0:
                    status = "mapped"
                    coverage = 100.0
                    mapped_count += 1
                else:
                    status = "unmapped"
                    coverage = 0.0

                entries.append(ComplianceMatrixEntry(
                    control_id=control_id,
                    framework=framework,
                    control_name=control_name,
                    mapped_rules=mapped_rules,
                    status=status,
                    coverage_percentage=coverage,
                ))

            framework_stats[framework] = {
                "total_controls": total_count,
                "mapped_controls": mapped_count,
                "coverage_percentage": (
                    mapped_count / total_count * 100 if total_count > 0 else 0
                ),
            }

        return ComplianceMatrix(
            entries=entries,
            summary={
                "frameworks": framework_stats,
                "total_rules": len(self._mappings),
            },
        )

    def get_evidence_requirements(
        self, framework: str, control_id: str
    ) -> List[str]:
        """Get evidence requirements for a control."""
        rules = self.get_rules_for_control(framework, control_id)
        requirements: Set[str] = set()

        for rule in rules:
            mapping = self._mappings.get(rule)
            if mapping:
                requirements.update(mapping.evidence_requirements)

        return list(requirements)

    def get_all_frameworks(self) -> List[str]:
        """Get list of all supported frameworks."""
        return list(self._control_catalog.keys())

    def get_framework_controls(self, framework: str) -> Dict[str, str]:
        """Get all controls for a framework."""
        return self._control_catalog.get(framework, {})

    def export_mapping(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Export mapping for a rule."""
        mapping = self._mappings.get(rule_name)
        return mapping.to_dict() if mapping else None

    def get_cross_framework_coverage(self, rule_name: str) -> Dict[str, int]:
        """Get count of controls covered by a rule per framework."""
        mapping = self._mappings.get(rule_name)
        if not mapping:
            return {}

        return {
            framework: len(controls)
            for framework, controls in mapping.frameworks.items()
        }
