"""
Feedback collection module for UX Research Platform.

This module provides functionality for collecting user feedback from various sources
including surveys, heatmaps, session recordings, and support tickets.
"""

from .feedback_collector import (ClickEvent, FeedbackCollector, HeatmapData,
                                 HoverEvent, NPSScore, ScrollEvent,
                                 SupportTicket, SurveyResponse)

__all__ = [
    "FeedbackCollector",
    "SurveyResponse",
    "HeatmapData",
    "NPSScore",
    "SupportTicket",
    "ClickEvent",
    "ScrollEvent",
    "HoverEvent",
]
