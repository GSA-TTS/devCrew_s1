"""Analytics integration module for UX Research Platform.

This module provides integration with various analytics platforms including
Google Analytics, Hotjar, and Heap for comprehensive user behavior analysis.
"""

from tools.ux_research.analytics.analytics_integrator import (
    AnalyticsData, AnalyticsIntegrator, ConversionAnalysis, Event, HotjarData,
    JourneyAnalysis)

__all__ = [
    "AnalyticsIntegrator",
    "AnalyticsData",
    "HotjarData",
    "Event",
    "JourneyAnalysis",
    "ConversionAnalysis",
]
