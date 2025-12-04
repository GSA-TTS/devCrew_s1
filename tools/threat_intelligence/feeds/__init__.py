"""
Feed Aggregator Module for Threat Intelligence Platform.

This module provides STIX/TAXII feed ingestion, CVE database synchronization,
and custom feed parsing capabilities for the devCrew_s1 threat intelligence platform.
"""

from tools.threat_intelligence.feeds.aggregator import (
    CVE,
    FeedAggregator,
    STIXObject,
    ThreatIndicator,
)

__all__ = [
    "FeedAggregator",
    "STIXObject",
    "CVE",
    "ThreatIndicator",
]
