"""
Threat Intelligence Platform (TOOL-SEC-008).

A comprehensive threat data aggregation and analysis solution with STIX/TAXII
integration, CVE tracking, MITRE ATT&CK mapping, VEX document generation,
and IOC management.

This platform provides:
- STIX/TAXII 2.1 feed ingestion
- CVE database synchronization (NVD, OSV, GitHub Advisory)
- Threat correlation with asset risk scoring
- MITRE ATT&CK technique mapping and detection gap analysis
- VEX document generation (OpenVEX and CSAF 2.0)
- IOC extraction, enrichment, and management
- Intelligence enrichment with OSINT and threat actor attribution
- Comprehensive CLI interface

Example:
    Basic usage with CLI:

    $ threat-intel ingest --feed taxii --url https://cti-taxii.mitre.org/taxii/
    $ threat-intel correlate --vulnerabilities vulns.json --threats threats.json
    $ threat-intel attack --threats threats.json --output navigator.json
    $ threat-intel vex --cve CVE-2024-1234 --product myapp --status not_affected
    $ threat-intel ioc --extract --input threats.json --output iocs.json
    $ threat-intel report --input threats.json --format html

    Python API usage:

    >>> from tools.threat_intelligence import FeedAggregator, ThreatCorrelator
    >>> aggregator = FeedAggregator()
    >>> threats = aggregator.ingest_taxii_feed(
    ...     "https://cti-taxii.mitre.org/taxii/",
    ...     "enterprise-attack"
    ... )
    >>> correlator = ThreatCorrelator()
    >>> correlations = correlator.correlate_vulnerabilities(cves, threats)
    >>> for corr in correlations:
    ...     print(f"{corr.cve_id}: Risk {corr.risk_score}")
"""

from tools.threat_intelligence.attack.attack_mapper import (
    ATTACKMapper,
    ATTACKTechnique,
    DetectionGap,
    TacticCoverage,
)
from tools.threat_intelligence.cli.threat_cli import cli
from tools.threat_intelligence.correlator.threat_correlator import (
    CVE,
    Asset,
    AssetRisk,
    SBOMThreatAnalysis,
    ThreatCorrelation,
    ThreatCorrelator,
    ThreatIndicator,
)
from tools.threat_intelligence.enricher.intelligence_enricher import (
    Campaign,
    EnrichedThreat,
    IntelligenceEnricher,
    ThreatActorAttribution,
)
from tools.threat_intelligence.feeds.aggregator import (
    CustomFeed,
    FeedAggregator,
    STIXObject,
)
from tools.threat_intelligence.ioc.ioc_manager import (
    IOC,
    EnrichedIOC,
    IOCManager,
)
from tools.threat_intelligence.vex.vex_generator import (
    ExploitabilityAssessment,
    VEXGenerator,
)

__version__ = "1.0.0"
__author__ = "devCrew_s1"

__all__ = [
    # Version info
    "__version__",
    "__author__",
    # CLI
    "cli",
    # Feed Aggregator
    "FeedAggregator",
    "STIXObject",
    "CustomFeed",
    # Threat Correlator
    "ThreatCorrelator",
    "ThreatCorrelation",
    "ThreatIndicator",
    "Asset",
    "AssetRisk",
    "CVE",
    "SBOMThreatAnalysis",
    # ATT&CK Mapper
    "ATTACKMapper",
    "ATTACKTechnique",
    "TacticCoverage",
    "DetectionGap",
    # VEX Generator
    "VEXGenerator",
    "ExploitabilityAssessment",
    # IOC Manager
    "IOCManager",
    "IOC",
    "EnrichedIOC",
    # Intelligence Enricher
    "IntelligenceEnricher",
    "EnrichedThreat",
    "ThreatActorAttribution",
    "Campaign",
]


def get_version() -> str:
    """
    Get the current version of the Threat Intelligence Platform.

    Returns:
        str: Version string in semantic versioning format (e.g., "1.0.0").
    """
    return __version__


def get_all_components() -> dict:
    """
    Get all available components in the platform.

    Returns:
        dict: Dictionary mapping component names to their classes.

    Example:
        >>> from tools.threat_intelligence import get_all_components
        >>> components = get_all_components()
        >>> aggregator = components['FeedAggregator']()
        >>> threats = aggregator.ingest_taxii_feed(url, collection)
    """
    return {
        "FeedAggregator": FeedAggregator,
        "ThreatCorrelator": ThreatCorrelator,
        "ATTACKMapper": ATTACKMapper,
        "VEXGenerator": VEXGenerator,
        "IOCManager": IOCManager,
        "IntelligenceEnricher": IntelligenceEnricher,
    }
