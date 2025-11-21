"""
Compliance Management & Policy Enforcement Platform (TOOL-SEC-011)

A comprehensive compliance management platform supporting multiple regulatory
frameworks including GDPR, HIPAA, FedRAMP, SOC2, ISO 27001, and NIST 800-53.

Part of devCrew_s1 security tooling.
"""

from .policy_engine import PolicyEngine, PolicyResult, PolicyCache
from .compliance_manager import (
    ComplianceManager,
    ComplianceFramework,
    ComplianceStatus,
    ComplianceScore,
)
from .policy_validator import PolicyValidator, ValidationResult
from .regulatory_mapper import RegulatoryMapper, ControlMapping, ComplianceMatrix
from .audit_reporter import AuditReporter, ReportFormat
from .violation_tracker import (
    ViolationTracker,
    Violation,
    ViolationSeverity,
    ViolationStatus,
)

__version__ = "1.0.0"
__all__ = [
    "PolicyEngine",
    "PolicyResult",
    "PolicyCache",
    "ComplianceManager",
    "ComplianceFramework",
    "ComplianceStatus",
    "ComplianceScore",
    "PolicyValidator",
    "ValidationResult",
    "RegulatoryMapper",
    "ControlMapping",
    "ComplianceMatrix",
    "AuditReporter",
    "ReportFormat",
    "ViolationTracker",
    "Violation",
    "ViolationSeverity",
    "ViolationStatus",
]
