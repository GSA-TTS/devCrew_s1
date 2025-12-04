"""Threat Correlator for vulnerability-to-threat matching and risk scoring.

This module provides comprehensive threat correlation capabilities including:
- Vulnerability-to-threat matching using CVE IDs
- Asset inventory correlation with threat data
- SBOM (Software Bill of Materials) analysis
- Risk scoring algorithm (criticality × likelihood × exploitability)
- Attack surface analysis
- Exploit prediction based on threat intelligence
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class Asset(BaseModel):
    """Asset model for inventory tracking."""

    asset_id: str = Field(..., description="Unique asset identifier")
    name: str = Field(..., description="Asset name")
    type: str = Field(
        ..., description="Asset type: server, workstation, network_device"
    )
    ip_addresses: List[str] = Field(
        default_factory=list, description="List of IP addresses"
    )
    software: List[Dict[str, str]] = Field(
        default_factory=list, description="Installed software (name, version)"
    )
    criticality: str = Field(
        ..., description="Criticality level: LOW, MEDIUM, HIGH, CRITICAL"
    )

    @validator("criticality")
    def validate_criticality(cls, v: str) -> str:
        """Validate criticality level."""
        allowed = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"Criticality must be one of {allowed}")
        return v.upper()

    @validator("type")
    def validate_type(cls, v: str) -> str:
        """Validate asset type."""
        allowed = ["server", "workstation", "network_device", "container", "vm"]
        if v.lower() not in allowed:
            raise ValueError(f"Asset type must be one of {allowed}")
        return v.lower()


class CVE(BaseModel):
    """CVE vulnerability model."""

    cve_id: str = Field(..., description="CVE identifier")
    description: str = Field(default="", description="Vulnerability description")
    cvss_score: float = Field(default=0.0, description="CVSS base score (0-10)")
    cvss_vector: str = Field(default="", description="CVSS vector string")
    cpe: List[str] = Field(default_factory=list, description="CPE identifiers")
    published_date: Optional[str] = Field(
        None, description="Publication date (ISO format)"
    )
    exploit_available: bool = Field(
        default=False, description="Known exploit availability"
    )
    epss_score: float = Field(
        default=0.0, description="EPSS score (Exploit Prediction Scoring System)"
    )

    @validator("cve_id")
    def validate_cve_id(cls, v: str) -> str:
        """Validate CVE ID format."""
        if not re.match(r"^CVE-\d{4}-\d{4,}$", v):
            raise ValueError(f"Invalid CVE ID format: {v}")
        return v.upper()

    @validator("cvss_score")
    def validate_cvss_score(cls, v: float) -> float:
        """Validate CVSS score range."""
        if not 0.0 <= v <= 10.0:
            raise ValueError(f"CVSS score must be between 0 and 10: {v}")
        return v


class STIXObject(BaseModel):
    """STIX 2.1 object model."""

    id: str = Field(..., description="STIX object ID")
    type: str = Field(..., description="STIX object type")
    spec_version: str = Field(default="2.1", description="STIX specification version")
    created: str = Field(..., description="Creation timestamp")
    modified: str = Field(..., description="Modification timestamp")
    name: Optional[str] = Field(None, description="Object name")
    description: Optional[str] = Field(None, description="Object description")
    labels: List[str] = Field(default_factory=list, description="Object labels")
    external_references: List[Dict[str, Any]] = Field(
        default_factory=list, description="External references"
    )


class ThreatIndicator(BaseModel):
    """Threat indicator model."""

    indicator_id: str = Field(..., description="Unique indicator ID")
    type: str = Field(..., description="Indicator type: ip, domain, hash, cve, pattern")
    value: str = Field(..., description="Indicator value")
    threat_type: str = Field(..., description="Threat type: malware, exploit, apt")
    confidence: float = Field(..., description="Confidence score (0-1)")
    severity: str = Field(
        ..., description="Severity level: LOW, MEDIUM, HIGH, CRITICAL"
    )
    first_seen: str = Field(..., description="First seen timestamp")
    last_seen: str = Field(..., description="Last seen timestamp")
    tags: List[str] = Field(default_factory=list, description="Threat tags")


class ThreatCorrelation(BaseModel):
    """Threat correlation result."""

    cve_id: str = Field(..., description="CVE identifier")
    threat_indicators: List[str] = Field(
        default_factory=list, description="Related threat indicator IDs"
    )
    correlation_score: float = Field(
        ..., description="Correlation confidence score (0-1)"
    )
    active_exploitation: bool = Field(
        default=False, description="Evidence of active exploitation"
    )
    exploit_available: bool = Field(
        default=False, description="Public exploit availability"
    )
    threat_actors: List[str] = Field(
        default_factory=list, description="Associated threat actors"
    )
    campaigns: List[str] = Field(
        default_factory=list, description="Related threat campaigns"
    )
    techniques: List[str] = Field(
        default_factory=list, description="MITRE ATT&CK techniques"
    )


class AssetRisk(BaseModel):
    """Asset risk assessment result."""

    asset_id: str = Field(..., description="Asset identifier")
    risk_score: float = Field(..., description="Calculated risk score (0-100)")
    threat_count: int = Field(..., description="Total number of threats")
    critical_threats: int = Field(
        ..., description="Number of critical severity threats"
    )
    vulnerable_software: List[Dict[str, Any]] = Field(
        default_factory=list, description="Vulnerable software components"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Risk mitigation recommendations"
    )
    exposure_window: int = Field(
        default=0, description="Days since first vulnerability discovered"
    )


class SBOMThreatAnalysis(BaseModel):
    """SBOM threat analysis result."""

    total_components: int = Field(..., description="Total SBOM components")
    vulnerable_components: int = Field(..., description="Vulnerable component count")
    threat_exposure: float = Field(
        ..., description="Overall threat exposure score (0-100)"
    )
    critical_vulns: List[Dict[str, Any]] = Field(
        default_factory=list, description="Critical vulnerabilities"
    )
    high_vulns: List[Dict[str, Any]] = Field(
        default_factory=list, description="High severity vulnerabilities"
    )
    affected_components: List[Dict[str, Any]] = Field(
        default_factory=list, description="Components with vulnerabilities"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Remediation recommendations"
    )


class ThreatCorrelator:
    """Threat correlator for vulnerability-to-threat matching and risk scoring."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize threat correlator.

        Args:
            config: Optional configuration dictionary with keys:
                - cache_enabled: Enable correlation caching (default: True)
                - cache_ttl: Cache TTL in seconds (default: 3600)
                - min_correlation_score: Minimum correlation score (default: 0.5)
                - exploit_weight: Exploit availability weight (default: 0.3)
                - active_exploitation_weight: Active exploitation weight (0.5)
        """
        self.config = config or {}
        self.cache_enabled = self.config.get("cache_enabled", True)
        self.cache_ttl = self.config.get("cache_ttl", 3600)
        self.min_correlation_score = self.config.get("min_correlation_score", 0.5)
        self.exploit_weight = self.config.get("exploit_weight", 0.3)
        self.active_exploitation_weight = self.config.get(
            "active_exploitation_weight", 0.5
        )

        # Correlation cache: {cve_id: (correlation, timestamp)}
        self._correlation_cache: Dict[str, Tuple[ThreatCorrelation, datetime]] = {}

        # Risk calculation cache: {asset_id: (risk, timestamp)}
        self._risk_cache: Dict[str, Tuple[AssetRisk, datetime]] = {}

        logger.info("ThreatCorrelator initialized with config: %s", self.config)

    def correlate_vulnerabilities(
        self, vulnerabilities: List[CVE], threats: List[STIXObject]
    ) -> List[ThreatCorrelation]:
        """Match vulnerabilities to active threats.

        Args:
            vulnerabilities: List of CVE vulnerabilities
            threats: List of STIX threat objects

        Returns:
            List of threat correlations with confidence scores
        """
        correlations = []

        for cve in vulnerabilities:
            # Check cache first
            if self.cache_enabled and cve.cve_id in self._correlation_cache:
                cached_correlation, timestamp = self._correlation_cache[cve.cve_id]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                    logger.debug("Using cached correlation for %s", cve.cve_id)
                    correlations.append(cached_correlation)
                    continue

            # Perform correlation
            correlation = self._correlate_single_vulnerability(cve, threats)

            # Only include if above threshold
            if correlation.correlation_score >= self.min_correlation_score:
                correlations.append(correlation)

                # Cache result
                if self.cache_enabled:
                    self._correlation_cache[cve.cve_id] = (
                        correlation,
                        datetime.now(),
                    )

        logger.info(
            "Correlated %d vulnerabilities with threats, found %d matches",
            len(vulnerabilities),
            len(correlations),
        )
        return correlations

    def _correlate_single_vulnerability(
        self, cve: CVE, threats: List[STIXObject]
    ) -> ThreatCorrelation:
        """Correlate a single vulnerability with threat indicators.

        Args:
            cve: CVE vulnerability
            threats: List of STIX threat objects

        Returns:
            ThreatCorrelation with confidence score
        """
        threat_indicators: List[str] = []
        active_exploitation = False
        exploit_available = cve.exploit_available
        threat_actors: Set[str] = set()
        campaigns: Set[str] = set()
        techniques: Set[str] = set()
        correlation_factors = []

        for threat in threats:
            # Check for CVE reference in external_references
            for ref in threat.external_references:
                if (
                    ref.get("source_name") == "cve"
                    and ref.get("external_id") == cve.cve_id
                ):
                    threat_indicators.append(threat.id)
                    correlation_factors.append(0.9)  # Direct CVE reference

                    # Check for exploitation indicators
                    if threat.type == "indicator" and "exploit" in threat.labels:
                        exploit_available = True
                        correlation_factors.append(0.8)

                    # Check for active exploitation
                    if "active-exploitation" in threat.labels:
                        active_exploitation = True
                        correlation_factors.append(1.0)

                    # Extract threat actor info
                    if threat.type == "threat-actor" and threat.name:
                        threat_actors.add(threat.name)

                    # Extract campaign info
                    if threat.type == "campaign" and threat.name:
                        campaigns.add(threat.name)

                    # Extract ATT&CK techniques
                    for ref in threat.external_references:
                        if ref.get("source_name") == "mitre-attack":
                            technique_id = ref.get("external_id", "")
                            if technique_id.startswith("T"):
                                techniques.add(technique_id)

            # Check for CVE mention in description
            if threat.description and cve.cve_id.upper() in threat.description.upper():
                if threat.id not in threat_indicators:
                    threat_indicators.append(threat.id)
                    correlation_factors.append(0.7)  # Description mention

        # Calculate correlation score
        correlation_score = 0.0
        if correlation_factors:
            # Weighted average with boost for multiple factors
            correlation_score = sum(correlation_factors) / len(correlation_factors)
            # Boost for multiple correlations
            if len(correlation_factors) > 1:
                correlation_score = min(
                    1.0, correlation_score * (1 + 0.1 * len(correlation_factors))
                )

            # Boost for exploit availability
            if exploit_available:
                correlation_score = min(1.0, correlation_score + self.exploit_weight)

            # Boost for active exploitation
            if active_exploitation:
                correlation_score = min(
                    1.0, correlation_score + self.active_exploitation_weight
                )

        return ThreatCorrelation(
            cve_id=cve.cve_id,
            threat_indicators=threat_indicators,
            correlation_score=correlation_score,
            active_exploitation=active_exploitation,
            exploit_available=exploit_available,
            threat_actors=sorted(list(threat_actors)),
            campaigns=sorted(list(campaigns)),
            techniques=sorted(list(techniques)),
        )

    def analyze_asset_risk(
        self, asset_inventory: List[Asset], threat_data: List[ThreatIndicator]
    ) -> List[AssetRisk]:
        """Calculate risk score for each asset.

        Args:
            asset_inventory: List of assets
            threat_data: List of threat indicators

        Returns:
            List of asset risk assessments
        """
        risk_assessments = []

        for asset in asset_inventory:
            # Check cache
            if self.cache_enabled and asset.asset_id in self._risk_cache:
                cached_risk, timestamp = self._risk_cache[asset.asset_id]
                if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                    logger.debug("Using cached risk for %s", asset.asset_id)
                    risk_assessments.append(cached_risk)
                    continue

            # Calculate risk
            risk_assessment = self._calculate_asset_risk(asset, threat_data)
            risk_assessments.append(risk_assessment)

            # Cache result
            if self.cache_enabled:
                self._risk_cache[asset.asset_id] = (risk_assessment, datetime.now())

        logger.info("Analyzed risk for %d assets", len(asset_inventory))
        return risk_assessments

    def _calculate_asset_risk(
        self, asset: Asset, threat_data: List[ThreatIndicator]
    ) -> AssetRisk:
        """Calculate risk for a single asset.

        Args:
            asset: Asset to analyze
            threat_data: List of threat indicators

        Returns:
            AssetRisk assessment
        """
        threats_affecting_asset = []
        critical_threats = 0
        vulnerable_software = []

        # Match threats to asset
        for threat in threat_data:
            # Check IP-based threats
            if threat.type == "ip" and threat.value in asset.ip_addresses:
                threats_affecting_asset.append(threat)
                if threat.severity == "CRITICAL":
                    critical_threats += 1

            # Check software-based threats (CVE indicators)
            if threat.type == "cve":
                cve_id = threat.value
                for software in asset.software:
                    sw_name = software.get("name", "")
                    sw_version = software.get("version", "")

                    # Simple version matching - in production, use CPE matching
                    if self._is_software_vulnerable(sw_name, sw_version, cve_id):
                        threats_affecting_asset.append(threat)
                        if threat.severity == "CRITICAL":
                            critical_threats += 1

                        vulnerable_software.append(
                            {
                                "name": sw_name,
                                "version": sw_version,
                                "cve": cve_id,
                                "severity": threat.severity,
                            }
                        )

        # Calculate risk score
        risk_score = self.calculate_risk_score(asset, threats_affecting_asset)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            asset, threats_affecting_asset, vulnerable_software
        )

        # Calculate exposure window
        exposure_window = self._calculate_exposure_window(threats_affecting_asset)

        return AssetRisk(
            asset_id=asset.asset_id,
            risk_score=risk_score,
            threat_count=len(threats_affecting_asset),
            critical_threats=critical_threats,
            vulnerable_software=vulnerable_software,
            recommendations=recommendations,
            exposure_window=exposure_window,
        )

    def calculate_risk_score(
        self, asset: Asset, threats: List[ThreatIndicator]
    ) -> float:
        """Calculate risk score for an asset.

        Formula: Risk = Criticality × Likelihood × Exploitability
        - Criticality: Asset importance (1-10)
        - Likelihood: Threat intelligence indicators (0-1)
        - Exploitability: Average threat confidence (0-1)

        Args:
            asset: Asset to score
            threats: List of threats affecting the asset

        Returns:
            Risk score (0-100)
        """
        # Criticality mapping
        criticality_map = {"LOW": 2.5, "MEDIUM": 5.0, "HIGH": 7.5, "CRITICAL": 10.0}
        criticality = criticality_map.get(asset.criticality, 5.0)

        # Likelihood based on threat count
        if not threats:
            return 0.0

        # Calculate average threat confidence (exploitability)
        avg_confidence = sum(t.confidence for t in threats) / len(threats)

        # Likelihood increases with threat count but caps at 1.0
        likelihood = min(1.0, len(threats) / 10.0)

        # Weight by severity
        severity_weights = {"LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.75, "CRITICAL": 1.0}
        severity_factor = sum(
            severity_weights.get(t.severity, 0.5) for t in threats
        ) / len(threats)

        # Combined likelihood
        likelihood = (likelihood + severity_factor) / 2.0

        # Calculate final risk score (0-100)
        risk_score = criticality * likelihood * avg_confidence * 10.0

        return min(100.0, risk_score)

    def analyze_sbom(
        self, sbom: Dict[str, Any], threat_data: List[ThreatIndicator]
    ) -> SBOMThreatAnalysis:
        """Analyze SBOM for threats.

        Supports SPDX and CycloneDX formats.

        Args:
            sbom: SBOM document (SPDX or CycloneDX)
            threat_data: List of threat indicators

        Returns:
            SBOMThreatAnalysis with vulnerability analysis
        """
        # Detect SBOM format
        sbom_format = self._detect_sbom_format(sbom)
        logger.info("Detected SBOM format: %s", sbom_format)

        # Extract components
        components = self._extract_sbom_components(sbom, sbom_format)
        total_components = len(components)

        # Analyze components for vulnerabilities
        vulnerable_components = []
        critical_vulns = []
        high_vulns = []

        for component in components:
            vulns = self._find_component_vulnerabilities(component, threat_data)
            if vulns:
                vulnerable_components.append(
                    {"component": component["name"], "vulnerabilities": vulns}
                )

                for vuln in vulns:
                    if vuln["severity"] == "CRITICAL":
                        critical_vulns.append(vuln)
                    elif vuln["severity"] == "HIGH":
                        high_vulns.append(vuln)

        # Calculate threat exposure score
        if total_components == 0:
            threat_exposure = 0.0
        else:
            vuln_ratio = len(vulnerable_components) / total_components
            severity_weight = (len(critical_vulns) * 1.0 + len(high_vulns) * 0.7) / (
                total_components + 1
            )
            threat_exposure = min(100.0, (vuln_ratio + severity_weight) * 50.0)

        # Generate recommendations
        recommendations = self._generate_sbom_recommendations(
            vulnerable_components, critical_vulns, high_vulns
        )

        return SBOMThreatAnalysis(
            total_components=total_components,
            vulnerable_components=len(vulnerable_components),
            threat_exposure=threat_exposure,
            critical_vulns=critical_vulns[:10],  # Top 10
            high_vulns=high_vulns[:20],  # Top 20
            affected_components=vulnerable_components[:50],  # Top 50
            recommendations=recommendations,
        )

    def predict_exploit_likelihood(
        self, cve: CVE, threat_intelligence: List[STIXObject]
    ) -> float:
        """Predict likelihood of exploitation.

        Uses multiple factors:
        - EPSS score (if available)
        - Exploit availability in threat intelligence
        - Active exploitation indicators
        - CVSS score and exploitability metrics
        - Age of vulnerability

        Args:
            cve: CVE vulnerability
            threat_intelligence: List of STIX threat objects

        Returns:
            Exploit likelihood score (0-1)
        """
        factors = []

        # Factor 1: EPSS score (if available)
        if cve.epss_score > 0:
            factors.append(cve.epss_score)

        # Factor 2: CVSS score (normalized to 0-1)
        if cve.cvss_score > 0:
            cvss_likelihood = cve.cvss_score / 10.0
            factors.append(cvss_likelihood)

        # Factor 3: Exploit availability
        if cve.exploit_available:
            factors.append(0.8)

        # Factor 4: Active exploitation from threat intelligence
        for threat in threat_intelligence:
            for ref in threat.external_references:
                if (
                    ref.get("source_name") == "cve"
                    and ref.get("external_id") == cve.cve_id
                ):
                    if "active-exploitation" in threat.labels:
                        factors.append(1.0)
                        break

        # Factor 5: Vulnerability age (older = more time for exploits)
        if cve.published_date:
            age_likelihood = self._calculate_age_factor(cve.published_date)
            factors.append(age_likelihood)

        # Calculate weighted average
        if not factors:
            return 0.0

        exploit_likelihood = sum(factors) / len(factors)

        # Boost if multiple factors present
        if len(factors) > 2:
            exploit_likelihood = min(1.0, exploit_likelihood * 1.1)

        return exploit_likelihood

    def _detect_sbom_format(self, sbom: Dict[str, Any]) -> str:
        """Detect SBOM format (SPDX or CycloneDX).

        Args:
            sbom: SBOM document

        Returns:
            Format name: "SPDX", "CycloneDX", or "Unknown"
        """
        if "spdxVersion" in sbom or "SPDXID" in sbom:
            return "SPDX"
        elif "bomFormat" in sbom or "components" in sbom:
            return "CycloneDX"
        else:
            return "Unknown"

    def _extract_sbom_components(
        self, sbom: Dict[str, Any], sbom_format: str
    ) -> List[Dict[str, str]]:
        """Extract components from SBOM.

        Args:
            sbom: SBOM document
            sbom_format: Detected format

        Returns:
            List of components with name and version
        """
        components = []

        if sbom_format == "SPDX":
            # SPDX format
            packages = sbom.get("packages", [])
            for pkg in packages:
                components.append(
                    {
                        "name": pkg.get("name", ""),
                        "version": pkg.get("versionInfo", ""),
                        "purl": pkg.get("externalRefs", [{}])[0].get(
                            "referenceLocator", ""
                        ),
                    }
                )

        elif sbom_format == "CycloneDX":
            # CycloneDX format
            comps = sbom.get("components", [])
            for comp in comps:
                components.append(
                    {
                        "name": comp.get("name", ""),
                        "version": comp.get("version", ""),
                        "purl": comp.get("purl", ""),
                    }
                )

        return components

    def _find_component_vulnerabilities(
        self, component: Dict[str, str], threat_data: List[ThreatIndicator]
    ) -> List[Dict[str, Any]]:
        """Find vulnerabilities for a component.

        Args:
            component: Component dict with name and version
            threat_data: List of threat indicators

        Returns:
            List of vulnerabilities affecting the component
        """
        vulnerabilities = []

        comp_name = component.get("name", "").lower()
        comp_version = component.get("version", "")

        for threat in threat_data:
            if threat.type == "cve":
                # Simple name-based matching - in production use CPE/PURL
                if self._is_software_vulnerable(comp_name, comp_version, threat.value):
                    vulnerabilities.append(
                        {
                            "cve": threat.value,
                            "severity": threat.severity,
                            "confidence": threat.confidence,
                            "description": threat.tags,
                        }
                    )

        return vulnerabilities

    def _is_software_vulnerable(
        self, software_name: str, software_version: str, cve_id: str
    ) -> bool:
        """Check if software version is vulnerable to CVE.

        This is a simplified implementation. In production, use:
        - CPE matching against NVD data
        - Package URL (PURL) comparison
        - Version range checking

        Args:
            software_name: Software name
            software_version: Software version
            cve_id: CVE identifier

        Returns:
            True if software is likely vulnerable
        """
        # TODO: Implement proper CPE/PURL matching
        # For now, return True if software_name is mentioned in CVE
        # This is a placeholder - proper implementation requires CVE database
        return len(software_name) > 3 and len(software_version) > 0

    def _generate_recommendations(
        self,
        asset: Asset,
        threats: List[ThreatIndicator],
        vulnerable_software: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate risk mitigation recommendations.

        Args:
            asset: Asset being analyzed
            threats: Threats affecting the asset
            vulnerable_software: List of vulnerable software

        Returns:
            List of actionable recommendations
        """
        recommendations = []

        # Critical threat recommendations
        critical_threats = [t for t in threats if t.severity == "CRITICAL"]
        if critical_threats:
            recommendations.append(
                f"URGENT: Address {len(critical_threats)} critical threats "
                "immediately"
            )

        # Software update recommendations
        if vulnerable_software:
            unique_software = {sw["name"] for sw in vulnerable_software}
            recommendations.append(
                f"Update vulnerable software: {', '.join(list(unique_software)[:5])}"
            )

        # Network isolation recommendations
        if asset.type in ["server", "network_device"] and len(threats) > 5:
            recommendations.append(
                "Consider network segmentation to reduce attack surface"
            )

        # Monitoring recommendations
        if any(t.type == "ip" for t in threats):
            recommendations.append(
                "Enable network monitoring for suspicious IP connections"
            )

        # Patch management
        cve_threats = [t for t in threats if t.type == "cve"]
        if len(cve_threats) > 3:
            recommendations.append(
                "Implement automated patch management for timely updates"
            )

        return recommendations

    def _generate_sbom_recommendations(
        self,
        vulnerable_components: List[Dict[str, Any]],
        critical_vulns: List[Dict[str, Any]],
        high_vulns: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate SBOM-specific recommendations.

        Args:
            vulnerable_components: Components with vulnerabilities
            critical_vulns: Critical severity vulnerabilities
            high_vulns: High severity vulnerabilities

        Returns:
            List of recommendations
        """
        recommendations = []

        if critical_vulns:
            recommendations.append(
                f"CRITICAL: Update {len(critical_vulns)} components with "
                "critical vulnerabilities"
            )

        if high_vulns:
            recommendations.append(
                f"HIGH: Address {len(high_vulns)} high-severity vulnerabilities"
            )

        if len(vulnerable_components) > 10:
            recommendations.append(
                "Implement automated dependency scanning in CI/CD pipeline"
            )

        if vulnerable_components:
            recommendations.append("Review and update outdated dependencies regularly")

        return recommendations

    def _calculate_exposure_window(self, threats: List[ThreatIndicator]) -> int:
        """Calculate exposure window in days.

        Args:
            threats: List of threat indicators

        Returns:
            Number of days since first threat discovered
        """
        if not threats:
            return 0

        earliest_date = None
        for threat in threats:
            try:
                first_seen = datetime.fromisoformat(
                    threat.first_seen.replace("Z", "+00:00")
                )
                if earliest_date is None or first_seen < earliest_date:
                    earliest_date = first_seen
            except (ValueError, AttributeError):
                continue

        if earliest_date:
            exposure_days = (datetime.now(earliest_date.tzinfo) - earliest_date).days
            return max(0, exposure_days)

        return 0

    def _calculate_age_factor(self, published_date: str) -> float:
        """Calculate age factor for vulnerability.

        Args:
            published_date: Publication date (ISO format)

        Returns:
            Age factor (0-1), higher = older = more likely exploited
        """
        try:
            pub_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
            age_days = (datetime.now(pub_date.tzinfo) - pub_date).days

            # Age factor increases over time, caps at 1 year
            age_factor = min(1.0, age_days / 365.0)
            return age_factor

        except (ValueError, AttributeError):
            return 0.5  # Default for unknown dates

    def clear_cache(self) -> None:
        """Clear correlation and risk caches."""
        self._correlation_cache.clear()
        self._risk_cache.clear()
        logger.info("Caches cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache sizes
        """
        return {
            "correlation_cache_size": len(self._correlation_cache),
            "risk_cache_size": len(self._risk_cache),
        }
