"""VEX (Vulnerability Exploitability eXchange) document generation.

This module provides functionality for generating VEX documents in OpenVEX
and CSAF 2.0 formats, assessing exploitability, and tracking remediation status.
"""

from tools.threat_intelligence.vex.vex_generator import (
    CSAFDocument,
    ExploitabilityAssessment,
    OpenVEXDocument,
    RemediationStatus,
    ValidationResult,
    VEXGenerator,
    VEXStatement,
)

__all__ = [
    "VEXGenerator",
    "OpenVEXDocument",
    "VEXStatement",
    "CSAFDocument",
    "ExploitabilityAssessment",
    "RemediationStatus",
    "ValidationResult",
]
