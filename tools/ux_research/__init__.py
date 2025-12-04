"""
UX Research & Design Feedback Platform (TOOL-UX-001).

A comprehensive user experience validation and accessibility auditing tool
for the devCrew_s1 enterprise tooling suite.

This platform provides:
- WCAG 2.1 Level A/AA/AAA compliance checking
- Nielsen's 10 usability heuristics evaluation
- User feedback collection and sentiment analysis
- Analytics integration (Google Analytics, Hotjar)
- Automated remediation guidance
- Comprehensive reporting and monitoring

Protocol Coverage:
- P-DESIGN-REVIEW: Design system validation
- P-FRONTEND-DEV: Frontend UX validation
"""

from tools.ux_research.analytics.analytics_integrator import (
    AnalyticsData, AnalyticsIntegrator, ConversionAnalysis, Event, FunnelStep,
    HotjarData, JourneyAnalysis, JourneyStep)
from tools.ux_research.analyzer.sentiment_analyzer import (Sentiment,
                                                           SentimentAnalyzer,
                                                           Topic)
from tools.ux_research.auditor.accessibility_auditor import (
    AccessibilityAuditor, AuditResult, AuditSummary, KeyboardIssue,
    ScreenReaderIssue, Violation)
from tools.ux_research.collector.feedback_collector import (ClickEvent,
                                                            FeedbackCollector,
                                                            HeatmapData,
                                                            HoverEvent,
                                                            NPSScore,
                                                            ScrollEvent,
                                                            SupportTicket,
                                                            SurveyResponse)
from tools.ux_research.remediation.guide_generator import (CodeExample,
                                                           RemediationGuide,
                                                           RemediationStep,
                                                           Severity)
from tools.ux_research.remediation.guide_generator import \
    Violation as RemediationViolation
from tools.ux_research.remediation.guide_generator import WCAGLevel
from tools.ux_research.validator.usability_validator import (
    FormIssue, HeuristicEvaluation, HeuristicResult, MobileIssue,
    ReadabilityScore, UsabilityValidator)

__version__ = "1.0.0"
__author__ = "devCrew_s1"
__tool_id__ = "TOOL-UX-001"

__all__ = [
    # Accessibility Auditor
    "AccessibilityAuditor",
    "AuditResult",
    "AuditSummary",
    "Violation",
    "KeyboardIssue",
    "ScreenReaderIssue",
    # Feedback Collector
    "FeedbackCollector",
    "SurveyResponse",
    "HeatmapData",
    "SupportTicket",
    "NPSScore",
    "ClickEvent",
    "ScrollEvent",
    "HoverEvent",
    # Usability Validator
    "UsabilityValidator",
    "HeuristicEvaluation",
    "HeuristicResult",
    "FormIssue",
    "MobileIssue",
    "ReadabilityScore",
    # Analytics Integrator
    "AnalyticsIntegrator",
    "AnalyticsData",
    "HotjarData",
    "Event",
    "JourneyAnalysis",
    "JourneyStep",
    "ConversionAnalysis",
    "FunnelStep",
    # Sentiment Analyzer
    "SentimentAnalyzer",
    "Sentiment",
    "Topic",
    # Remediation Guide
    "RemediationGuide",
    "RemediationStep",
    "CodeExample",
    "RemediationViolation",
    "Severity",
    "WCAGLevel",
    # Metadata
    "__version__",
    "__author__",
    "__tool_id__",
]
