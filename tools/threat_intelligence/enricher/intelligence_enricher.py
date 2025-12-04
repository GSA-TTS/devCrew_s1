"""Intelligence Enricher for Threat Intelligence Platform.

This module provides threat intelligence enrichment including OSINT
augmentation, threat actor attribution, campaign tracking, geolocation
analysis, and TTP extraction.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

import requests
from pydantic import BaseModel, Field


class GeoLocation(BaseModel):
    """Geolocation information."""

    ip_address: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    asn: Optional[str] = None
    isp: Optional[str] = None
    organization: Optional[str] = None


class TTP(BaseModel):
    """MITRE ATT&CK Tactic, Technique, and Procedure."""

    technique_id: str  # e.g., T1566.001
    technique_name: str
    tactic: str  # e.g., Initial Access
    description: Optional[str] = None
    confidence: int = Field(ge=0, le=100)
    data_sources: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)
    mitigations: List[str] = Field(default_factory=list)


class ThreatActorAttribution(BaseModel):
    """Threat actor attribution analysis."""

    actor_name: str
    aliases: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    ttps: List[str] = Field(default_factory=list)
    campaigns: List[str] = Field(default_factory=list)
    targets: List[str] = Field(default_factory=list)
    motivation: Optional[str] = None
    sophistication: Optional[str] = None  # low, medium, high, advanced
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    attribution_factors: Dict[str, Any] = Field(default_factory=dict)


class CampaignEvent(BaseModel):
    """Event in a threat campaign timeline."""

    event_id: str
    timestamp: datetime
    event_type: str  # reconnaissance, initial_access, execution, etc.
    description: str
    indicators: List[str] = Field(default_factory=list)
    affected_targets: List[str] = Field(default_factory=list)
    ttps: List[str] = Field(default_factory=list)


class Campaign(BaseModel):
    """Threat campaign tracking."""

    campaign_id: str
    name: str
    threat_actor: str
    start_date: datetime
    end_date: Optional[datetime] = None
    targets: List[str] = Field(default_factory=list)
    timeline: List[CampaignEvent] = Field(default_factory=list)
    objectives: List[str] = Field(default_factory=list)
    ttps: List[str] = Field(default_factory=list)
    indicators: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    impact: Optional[str] = None  # low, medium, high, critical


class OSINTData(BaseModel):
    """Open Source Intelligence data."""

    source: str
    source_type: str  # blog, twitter, github, pastebin, forum, etc.
    url: Optional[str] = None
    title: Optional[str] = None
    content: str
    published_date: Optional[datetime] = None
    author: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    relevance_score: float = Field(ge=0.0, le=1.0)
    extracted_indicators: List[str] = Field(default_factory=list)


class EnrichedThreat(BaseModel):
    """Enriched threat intelligence."""

    threat_id: str
    original_data: Dict[str, Any]
    osint_data: List[OSINTData] = Field(default_factory=list)
    threat_actor: Optional[ThreatActorAttribution] = None
    campaign: Optional[Campaign] = None
    ttps: List[TTP] = Field(default_factory=list)
    geolocations: List[GeoLocation] = Field(default_factory=list)
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
    enrichment_sources: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)


class IntelligenceEnricher:
    """Enriches threat intelligence with OSINT, attribution, and contextual data."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize intelligence enricher.

        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config or {}
        self.api_keys = self.config.get("api_keys", {})
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = self.config.get("cache_ttl_hours", 24)

        # Threat actor database (simplified for demonstration)
        self.threat_actors = self._load_threat_actor_db()

        # MITRE ATT&CK techniques (simplified mapping)
        self.attack_techniques = self._load_attack_techniques()

        # Campaign tracking
        self.campaigns: Dict[str, Campaign] = {}

    def _load_threat_actor_db(self) -> Dict[str, Dict[str, Any]]:
        """Load threat actor database."""
        # Simplified threat actor profiles
        return {
            "APT28": {
                "aliases": ["Fancy Bear", "Sofacy", "Strontium"],
                "ttps": [
                    "T1566.001",
                    "T1059.001",
                    "T1003",
                    "T1071.001",
                ],
                "targets": ["government", "military", "critical_infrastructure"],
                "motivation": "espionage",
                "sophistication": "advanced",
            },
            "APT29": {
                "aliases": ["Cozy Bear", "The Dukes"],
                "ttps": ["T1566.002", "T1547.001", "T1053.005", "T1071.001"],
                "targets": ["government", "think_tanks", "healthcare"],
                "motivation": "espionage",
                "sophistication": "advanced",
            },
            "Lazarus": {
                "aliases": ["Hidden Cobra", "ZINC", "Guardians of Peace"],
                "ttps": ["T1566.001", "T1105", "T1486", "T1490"],
                "targets": ["financial", "cryptocurrency", "government"],
                "motivation": "financial_gain",
                "sophistication": "advanced",
            },
            "FIN7": {
                "aliases": ["Carbanak Group"],
                "ttps": ["T1566.001", "T1059.003", "T1003.001", "T1041"],
                "targets": ["retail", "hospitality", "restaurant"],
                "motivation": "financial_gain",
                "sophistication": "high",
            },
        }

    def _load_attack_techniques(self) -> Dict[str, Dict[str, Any]]:
        """Load MITRE ATT&CK techniques."""
        # Simplified technique database
        return {
            "T1566.001": {
                "name": "Phishing: Spearphishing Attachment",
                "tactic": "Initial Access",
                "description": (
                    "Adversaries may send spearphishing emails with "
                    "malicious attachments"
                ),
                "platforms": ["Linux", "macOS", "Windows"],
                "data_sources": ["Email Gateway", "Email Content"],
            },
            "T1566.002": {
                "name": "Phishing: Spearphishing Link",
                "tactic": "Initial Access",
                "description": (
                    "Adversaries may send spearphishing emails with " "malicious links"
                ),
                "platforms": ["Linux", "macOS", "Windows"],
                "data_sources": ["Email Gateway", "Web Proxy"],
            },
            "T1059.001": {
                "name": "Command and Scripting Interpreter: PowerShell",
                "tactic": "Execution",
                "description": "Adversaries may abuse PowerShell commands",
                "platforms": ["Windows"],
                "data_sources": ["PowerShell Logs", "Process Monitoring"],
            },
            "T1003": {
                "name": "OS Credential Dumping",
                "tactic": "Credential Access",
                "description": "Adversaries may attempt to dump credentials",
                "platforms": ["Linux", "macOS", "Windows"],
                "data_sources": ["Process Monitoring", "API Monitoring"],
            },
            "T1071.001": {
                "name": "Application Layer Protocol: Web Protocols",
                "tactic": "Command and Control",
                "description": "Adversaries may use web protocols for C2",
                "platforms": ["Linux", "macOS", "Windows"],
                "data_sources": ["Network Traffic", "Web Proxy"],
            },
        }

    def augment_with_osint(self, threat: Dict[str, Any]) -> EnrichedThreat:
        """Augment threat data with OSINT sources.

        Args:
            threat: STIX object or threat data

        Returns:
            EnrichedThreat with OSINT data
        """
        threat_id = threat.get("id", hashlib.sha256(str(threat).encode()).hexdigest())

        # Check cache
        cache_key = f"osint:{threat_id}"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (datetime.utcnow() - cached_time).total_seconds() < (
                self.cache_ttl * 3600
            ):
                return cached_data

        enriched = EnrichedThreat(
            threat_id=threat_id,
            original_data=threat,
            confidence_score=0.5,
        )

        # Extract indicators from threat data
        indicators = self._extract_indicators(threat)

        # Search OSINT sources
        osint_data = []

        # Search Twitter/X (placeholder)
        twitter_data = self._search_twitter(indicators)
        osint_data.extend(twitter_data)

        # Search GitHub (placeholder)
        github_data = self._search_github(indicators)
        osint_data.extend(github_data)

        # Search security blogs (placeholder)
        blog_data = self._search_security_blogs(indicators)
        osint_data.extend(blog_data)

        # Search threat feeds (placeholder)
        feed_data = self._search_threat_feeds(indicators)
        osint_data.extend(feed_data)

        enriched.osint_data = osint_data
        enriched.enrichment_sources = [
            "twitter",
            "github",
            "security_blogs",
            "threat_feeds",
        ]

        # Calculate confidence based on OSINT findings
        if osint_data:
            avg_relevance = sum(d.relevance_score for d in osint_data) / len(osint_data)
            enriched.confidence_score = min(0.9, avg_relevance + 0.2)

        # Cache result
        self.cache[cache_key] = (datetime.utcnow(), enriched)

        return enriched

    def _extract_indicators(self, threat: Dict[str, Any]) -> List[str]:
        """Extract indicators from threat data."""
        indicators = []

        # Extract from STIX pattern
        if "pattern" in threat:
            pattern = threat["pattern"]
            # Simple extraction - in production, use proper STIX parsing
            import re

            values = re.findall(r"'([^']+)'", pattern)
            indicators.extend(values)

        # Extract from observables
        if "observables" in threat:
            for obs in threat["observables"]:
                if isinstance(obs, dict) and "value" in obs:
                    indicators.append(obs["value"])

        # Extract from description
        if "description" in threat:
            desc = threat["description"]
            # Extract IPs, domains, hashes (simplified)
            ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
            domain_pattern = r"\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b"
            indicators.extend(re.findall(ip_pattern, desc))
            indicators.extend(re.findall(domain_pattern, desc))

        return list(set(indicators))

    def _search_twitter(self, indicators: List[str]) -> List[OSINTData]:
        """Search Twitter/X for threat intelligence."""
        # Placeholder - in production, use Twitter API
        results = []

        # Simulate finding relevant tweets
        if indicators:
            sample_data = OSINTData(
                source="twitter",
                source_type="social_media",
                url=f"https://twitter.com/search?q={indicators[0]}",
                title="Security Alert",
                content=(f"Observed malicious activity related to " f"{indicators[0]}"),
                published_date=datetime.utcnow(),
                author="@security_researcher",
                tags=["threat_intel", "malware"],
                relevance_score=0.7,
                extracted_indicators=indicators[:3],
            )
            results.append(sample_data)

        return results

    def _search_github(self, indicators: List[str]) -> List[OSINTData]:
        """Search GitHub for threat intelligence."""
        # Placeholder - in production, use GitHub API
        results = []

        # Simulate finding relevant repos/issues
        if indicators:
            sample_data = OSINTData(
                source="github",
                source_type="code_repository",
                url=f"https://github.com/search?q={indicators[0]}",
                title="Malware Analysis Repository",
                content=(f"Analysis of malware campaign using " f"{indicators[0]}"),
                published_date=datetime.utcnow() - timedelta(days=2),
                author="security_analyst",
                tags=["malware", "analysis"],
                relevance_score=0.8,
                extracted_indicators=indicators[:2],
            )
            results.append(sample_data)

        return results

    def _search_security_blogs(self, indicators: List[str]) -> List[OSINTData]:
        """Search security blogs for threat intelligence."""
        # Placeholder - in production, use RSS feeds or blog APIs
        results = []

        if indicators:
            sample_data = OSINTData(
                source="security_blog",
                source_type="blog",
                url="https://blog.example.com/threat-analysis",
                title="Threat Campaign Analysis",
                content=(
                    f"In-depth analysis of recent campaign using " f"{indicators[0]}"
                ),
                published_date=datetime.utcnow() - timedelta(days=1),
                author="Security Research Team",
                tags=["apt", "campaign"],
                relevance_score=0.85,
                extracted_indicators=indicators[:5],
            )
            results.append(sample_data)

        return results

    def _search_threat_feeds(self, indicators: List[str]) -> List[OSINTData]:
        """Search public threat feeds."""
        # Placeholder - in production, query actual threat feeds
        results = []

        if indicators:
            sample_data = OSINTData(
                source="threat_feed",
                source_type="feed",
                url="https://threatfeed.example.com",
                title="IOC Alert",
                content=f"Malicious indicator detected: {indicators[0]}",
                published_date=datetime.utcnow(),
                author="ThreatFeed Service",
                tags=["ioc", "malicious"],
                relevance_score=0.9,
                extracted_indicators=indicators[:10],
            )
            results.append(sample_data)

        return results

    def attribute_threat_actor(
        self, indicators: List[str], ttps: List[str]
    ) -> ThreatActorAttribution:
        """Attribute threat to known actor based on indicators and TTPs.

        Args:
            indicators: List of IOCs
            ttps: List of TTP IDs (e.g., T1566.001)

        Returns:
            ThreatActorAttribution with confidence score
        """
        # Score each threat actor
        actor_scores: Dict[str, float] = {}

        for actor_name, actor_data in self.threat_actors.items():
            score = 0.0
            factors = {}

            # Score based on TTP overlap
            actor_ttps = set(actor_data["ttps"])
            provided_ttps = set(ttps)
            ttp_overlap = len(actor_ttps.intersection(provided_ttps))

            if ttp_overlap > 0:
                ttp_score = ttp_overlap / len(actor_ttps)
                score += ttp_score * 0.6  # 60% weight
                factors["ttp_match"] = f"{ttp_overlap}/{len(actor_ttps)} TTPs matched"

            # Score based on indicator patterns (simplified)
            # In production, this would analyze IOC characteristics
            if indicators:
                # Placeholder scoring
                indicator_score = 0.3
                score += indicator_score * 0.2  # 20% weight
                factors["indicator_match"] = f"{len(indicators)} indicators analyzed"

            # Score based on timing patterns (placeholder)
            timing_score = 0.1  # Default low score
            score += timing_score * 0.2  # 20% weight
            factors["temporal_correlation"] = "timeline analysis"

            actor_scores[actor_name] = score
            factors["total_score"] = str(score)

            # Store factors for top actor
            if not actor_scores or score > max(actor_scores.values()):
                top_factors = factors

        # Select actor with highest score
        if not actor_scores:
            return ThreatActorAttribution(
                actor_name="Unknown",
                confidence=0.0,
                attribution_factors={"reason": "insufficient_data"},
            )

        # Select actor with highest score
        top_actor = max(actor_scores, key=actor_scores.get)  # type: ignore
        confidence = actor_scores[top_actor]
        actor_data = self.threat_actors[top_actor]

        attribution = ThreatActorAttribution(
            actor_name=top_actor,
            aliases=actor_data["aliases"],
            confidence=round(confidence, 2),
            ttps=actor_data["ttps"],
            campaigns=self._get_actor_campaigns(top_actor),
            targets=actor_data["targets"],
            motivation=actor_data.get("motivation"),
            sophistication=actor_data.get("sophistication"),
            attribution_factors=top_factors,
        )

        return attribution

    def _get_actor_campaigns(self, actor_name: str) -> List[str]:
        """Get known campaigns for an actor."""
        campaigns = []
        for campaign_id, campaign in self.campaigns.items():
            if campaign.threat_actor == actor_name:
                campaigns.append(campaign.name)
        return campaigns

    def track_campaign(self, threats: List[Dict[str, Any]]) -> Campaign:
        """Track and correlate threats into campaigns.

        Args:
            threats: List of STIX objects or threat data

        Returns:
            Campaign object with timeline and correlation
        """
        # Extract common indicators and TTPs
        all_indicators: Set[str] = set()
        all_ttps: Set[str] = set()
        all_targets: Set[str] = set()
        events: List[CampaignEvent] = []

        for threat in threats:
            indicators = self._extract_indicators(threat)
            all_indicators.update(indicators)

            ttps = self._extract_ttps_from_threat(threat)
            all_ttps.update(ttps)

            targets = threat.get("targets", [])
            if isinstance(targets, list):
                all_targets.update(targets)

            # Create campaign event
            event = CampaignEvent(
                event_id=threat.get(
                    "id", hashlib.sha256(str(threat).encode()).hexdigest()
                ),
                timestamp=self._extract_timestamp(threat),
                event_type=self._classify_event_type(threat),
                description=threat.get("description", "Threat event"),
                indicators=indicators,
                affected_targets=targets if isinstance(targets, list) else [],
                ttps=ttps,
            )
            events.append(event)

        # Sort events by timestamp
        events.sort(key=lambda x: x.timestamp)

        # Attribute to threat actor
        attribution = self.attribute_threat_actor(list(all_indicators), list(all_ttps))

        # Calculate campaign confidence
        confidence = self._calculate_campaign_confidence(threats, attribution)

        # Generate campaign ID and name
        min_timestamp = min(e.timestamp for e in events)
        campaign_id = hashlib.sha256(
            f"{attribution.actor_name}:{min_timestamp}".encode()
        ).hexdigest()[:16]
        now = datetime.utcnow()
        campaign_name = f"{attribution.actor_name} Campaign " f"{now.strftime('%Y-%m')}"

        # Determine campaign objectives
        objectives = self._infer_objectives(threats, all_ttps)

        campaign = Campaign(
            campaign_id=campaign_id,
            name=campaign_name,
            threat_actor=attribution.actor_name,
            start_date=min(e.timestamp for e in events),
            end_date=max(e.timestamp for e in events) if len(events) > 1 else None,
            targets=list(all_targets),
            timeline=events,
            objectives=objectives,
            ttps=list(all_ttps),
            indicators=list(all_indicators),
            confidence=confidence,
            impact=self._assess_impact(threats),
        )

        # Store campaign
        self.campaigns[campaign_id] = campaign

        return campaign

    def _extract_ttps_from_threat(self, threat: Dict[str, Any]) -> List[str]:
        """Extract TTP IDs from threat data."""
        ttps = []

        # Check for direct TTP references
        if "ttps" in threat:
            ttps.extend(threat["ttps"])

        # Extract from kill chain phases
        if "kill_chain_phases" in threat:
            for phase in threat["kill_chain_phases"]:
                # Map kill chain phase to TTPs (simplified)
                phase_name = phase.get("phase_name", "")
                if "initial-access" in phase_name:
                    ttps.append("T1566.001")  # Phishing
                elif "execution" in phase_name:
                    ttps.append("T1059.001")  # PowerShell

        # Infer from description
        if "description" in threat:
            desc = threat["description"].lower()
            if "phishing" in desc:
                ttps.append("T1566.001")
            if "powershell" in desc:
                ttps.append("T1059.001")
            if "credential" in desc or "dump" in desc:
                ttps.append("T1003")

        return list(set(ttps))

    def _extract_timestamp(self, threat: Dict[str, Any]) -> datetime:
        """Extract timestamp from threat data."""
        # Try various timestamp fields
        for field in ["created", "modified", "first_seen", "timestamp"]:
            if field in threat:
                value = threat[field]
                if isinstance(value, datetime):
                    return value
                elif isinstance(value, str):
                    try:
                        return datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        pass

        return datetime.utcnow()

    def _classify_event_type(self, threat: Dict[str, Any]) -> str:
        """Classify event type based on threat data."""
        # Try to determine phase from kill chain
        if "kill_chain_phases" in threat:
            phases = threat["kill_chain_phases"]
            if phases:
                return phases[0].get("phase_name", "unknown")

        # Infer from TTPs
        ttps = self._extract_ttps_from_threat(threat)
        if any(ttp.startswith("T1566") for ttp in ttps):
            return "initial_access"
        elif any(ttp.startswith("T1059") for ttp in ttps):
            return "execution"
        elif any(ttp.startswith("T1003") for ttp in ttps):
            return "credential_access"

        return "unknown"

    def _calculate_campaign_confidence(
        self,
        threats: List[Dict[str, Any]],
        attribution: ThreatActorAttribution,
    ) -> float:
        """Calculate campaign tracking confidence."""
        if not threats:
            return 0.0

        # Base confidence from attribution
        confidence = attribution.confidence * 0.5

        # Increase confidence based on number of correlated events
        event_score = min(0.3, len(threats) * 0.05)
        confidence += event_score

        # Increase confidence if events are temporally close
        if len(threats) > 1:
            timestamps = [self._extract_timestamp(t) for t in threats]
            time_span = (max(timestamps) - min(timestamps)).days
            if time_span <= 30:  # Within 30 days
                confidence += 0.2

        return min(1.0, round(confidence, 2))

    def _infer_objectives(
        self, threats: List[Dict[str, Any]], ttps: Set[str]
    ) -> List[str]:
        """Infer campaign objectives from threats and TTPs."""
        objectives = set()

        # Analyze TTPs
        if any(ttp.startswith("T1486") for ttp in ttps):
            objectives.add("financial_gain")  # Ransomware
        if any(ttp.startswith("T1003") for ttp in ttps):
            objectives.add("credential_theft")  # Credential dumping
        if any(ttp.startswith("T1071") for ttp in ttps):
            objectives.add("persistent_access")  # C2

        # Analyze threat descriptions
        for threat in threats:
            desc = threat.get("description", "").lower()
            if "espionage" in desc or "intelligence" in desc:
                objectives.add("espionage")
            if "ransomware" in desc:
                objectives.add("financial_gain")
            if "destruction" in desc or "wiper" in desc:
                objectives.add("destruction")

        return list(objectives) if objectives else ["unknown"]

    def _assess_impact(self, threats: List[Dict[str, Any]]) -> str:
        """Assess campaign impact level."""
        # Simplified impact assessment
        if len(threats) >= 10:
            return "critical"
        elif len(threats) >= 5:
            return "high"
        elif len(threats) >= 2:
            return "medium"
        return "low"

    def analyze_geolocation(self, ip_addresses: List[str]) -> List[GeoLocation]:
        """Analyze IP geolocation using external services.

        Args:
            ip_addresses: List of IP addresses

        Returns:
            List of GeoLocation objects
        """
        geolocations = []

        for ip in ip_addresses:
            # Check cache
            cache_key = f"geo:{ip}"
            if cache_key in self.cache:
                cached_time, cached_data = self.cache[cache_key]
                if (datetime.utcnow() - cached_time).total_seconds() < (
                    self.cache_ttl * 3600
                ):
                    geolocations.append(cached_data)
                    continue

            # Use ipapi.co (free tier)
            geolocation = self._geolocate_ip(ip)
            if geolocation:
                geolocations.append(geolocation)
                self.cache[cache_key] = (datetime.utcnow(), geolocation)

        return geolocations

    def _geolocate_ip(self, ip: str) -> Optional[GeoLocation]:
        """Geolocate a single IP address."""
        try:
            # Try ipapi.co (free, no API key required)
            response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)

            if response.status_code == 200:
                data = response.json()

                if data.get("error"):
                    return None

                return GeoLocation(
                    ip_address=ip,
                    country=data.get("country_name"),
                    country_code=data.get("country_code"),
                    city=data.get("city"),
                    region=data.get("region"),
                    latitude=data.get("latitude"),
                    longitude=data.get("longitude"),
                    asn=data.get("asn"),
                    isp=data.get("org"),
                    organization=data.get("org"),
                )

        except Exception:
            pass

        # Fallback: return basic geolocation
        return GeoLocation(
            ip_address=ip,
            country="Unknown",
            country_code="XX",
        )

    def extract_ttps(self, threat: Dict[str, Any]) -> List[TTP]:
        """Extract TTPs from threat data.

        Args:
            threat: STIX object or threat data

        Returns:
            List of TTP objects with details
        """
        ttp_ids = self._extract_ttps_from_threat(threat)
        ttps = []

        for ttp_id in ttp_ids:
            if ttp_id in self.attack_techniques:
                technique = self.attack_techniques[ttp_id]
                ttp = TTP(
                    technique_id=ttp_id,
                    technique_name=technique["name"],
                    tactic=technique["tactic"],
                    description=technique["description"],
                    confidence=80,  # Default confidence
                    data_sources=technique.get("data_sources", []),
                    platforms=technique.get("platforms", []),
                    mitigations=[],
                )
                ttps.append(ttp)
            else:
                # Unknown TTP
                ttp = TTP(
                    technique_id=ttp_id,
                    technique_name=f"Unknown Technique {ttp_id}",
                    tactic="Unknown",
                    confidence=50,
                )
                ttps.append(ttp)

        return ttps

    def get_campaign_summary(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign summary for reporting.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Campaign summary dictionary
        """
        if campaign_id not in self.campaigns:
            return None

        campaign = self.campaigns[campaign_id]

        summary = {
            "campaign_id": campaign.campaign_id,
            "name": campaign.name,
            "threat_actor": campaign.threat_actor,
            "start_date": campaign.start_date.isoformat(),
            "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
            "duration_days": (
                (campaign.end_date - campaign.start_date).days
                if campaign.end_date
                else 0
            ),
            "targets": campaign.targets,
            "objectives": campaign.objectives,
            "ttps": campaign.ttps,
            "total_events": len(campaign.timeline),
            "total_indicators": len(campaign.indicators),
            "confidence": campaign.confidence,
            "impact": campaign.impact,
            "timeline": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "description": event.description,
                    "indicators_count": len(event.indicators),
                }
                for event in campaign.timeline
            ],
        }

        return summary

    def export_enrichment_report(
        self, enriched: EnrichedThreat, format: str = "json"  # noqa: A002
    ) -> str:
        """Export enrichment report.

        Args:
            enriched: EnrichedThreat object
            format: Export format (json, markdown)

        Returns:
            Formatted report as string
        """
        if format == "json":
            return json.dumps(enriched.dict(), indent=2, default=str)
        elif format == "markdown":
            return self._generate_markdown_report(enriched)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_markdown_report(self, enriched: EnrichedThreat) -> str:
        """Generate markdown report."""
        lines = [
            "# Threat Intelligence Enrichment Report",
            "",
            f"**Threat ID:** {enriched.threat_id}",
            f"**Enriched At:** {enriched.enriched_at.isoformat()}",
            f"**Confidence Score:** {enriched.confidence_score:.2%}",
            "",
            "## Threat Actor Attribution",
        ]

        if enriched.threat_actor:
            actor = enriched.threat_actor
            lines.extend(
                [
                    "",
                    f"**Actor:** {actor.actor_name}",
                    f"**Aliases:** {', '.join(actor.aliases)}",
                    f"**Confidence:** {actor.confidence:.2%}",
                    f"**Motivation:** {actor.motivation}",
                    f"**Sophistication:** {actor.sophistication}",
                    f"**Targets:** {', '.join(actor.targets)}",
                ]
            )

        if enriched.campaign:
            lines.extend(
                [
                    "",
                    "## Campaign Information",
                    "",
                    f"**Campaign:** {enriched.campaign.name}",
                    f"**Start Date:** " f"{enriched.campaign.start_date.isoformat()}",
                    f"**Events:** {len(enriched.campaign.timeline)}",
                    f"**Impact:** {enriched.campaign.impact}",
                ]
            )

        if enriched.ttps:
            lines.extend(["", f"## TTPs ({len(enriched.ttps)})", ""])
            for ttp in enriched.ttps:
                lines.append(f"- **{ttp.technique_id}** - {ttp.technique_name}")

        if enriched.osint_data:
            lines.extend(["", f"## OSINT Sources ({len(enriched.osint_data)})", ""])
            for osint in enriched.osint_data[:5]:  # Top 5
                pub_date = (
                    osint.published_date.isoformat() if osint.published_date else "N/A"
                )
                lines.extend(
                    [
                        f"### {osint.title}",
                        "",
                        f"**Source:** {osint.source}",
                        f"**Relevance:** {osint.relevance_score:.2%}",
                        f"**Published:** {pub_date}",
                        "",
                    ]
                )

        return "\n".join(lines)
