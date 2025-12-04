"""Accessibility auditor module for WCAG compliance checking.

This module provides comprehensive accessibility auditing capabilities
for the UX Research & Design Feedback Platform (TOOL-UX-001).
"""

from tools.ux_research.auditor.accessibility_auditor import (
    AccessibilityAuditor, AuditResult, KeyboardIssue, ScreenReaderIssue,
    Violation)

__all__ = [
    "AccessibilityAuditor",
    "AuditResult",
    "Violation",
    "KeyboardIssue",
    "ScreenReaderIssue",
]
