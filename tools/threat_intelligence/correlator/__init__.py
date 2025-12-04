"""Threat Correlator module for matching vulnerabilities with threats."""

from .threat_correlator import (
    CVE,
    Asset,
    AssetRisk,
    SBOMThreatAnalysis,
    STIXObject,
    ThreatCorrelation,
    ThreatCorrelator,
    ThreatIndicator,
)

__all__ = [
    "ThreatCorrelator",
    "Asset",
    "CVE",
    "STIXObject",
    "ThreatIndicator",
    "ThreatCorrelation",
    "AssetRisk",
    "SBOMThreatAnalysis",
]
