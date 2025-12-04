"""
Remediation guide generator for WCAG violations.

Generates fix recommendations with code examples, prioritization,
and automated issue creation.
"""

from .guide_generator import (CodeExample, RemediationGuide, RemediationStep,
                              Severity, Violation, WCAGLevel)

__all__ = [
    "CodeExample",
    "RemediationGuide",
    "RemediationStep",
    "Severity",
    "Violation",
    "WCAGLevel",
]
