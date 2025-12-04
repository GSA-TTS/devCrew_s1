"""Tests for Intelligence Enricher module."""

import json
from datetime import datetime, timedelta

import pytest
from intelligence_enricher import (
    TTP,
    Campaign,
    CampaignEvent,
    EnrichedThreat,
    GeoLocation,
    IntelligenceEnricher,
    OSINTData,
    ThreatActorAttribution,
)


class TestTTP:
    """Test TTP model."""

    def test_ttp_creation(self):
        """Test creating TTP."""
        ttp = TTP(
            technique_id="T1566.001",
            technique_name="Phishing: Spearphishing Attachment",
            tactic="Initial Access",
            confidence=85,
            data_sources=["Email Gateway"],
            platforms=["Windows", "Linux"],
        )

        assert ttp.technique_id == "T1566.001"
        assert ttp.tactic == "Initial Access"
        assert ttp.confidence == 85
        assert "Windows" in ttp.platforms


class TestThreatActorAttribution:
    """Test ThreatActorAttribution model."""

    def test_attribution_creation(self):
        """Test creating attribution."""
        attribution = ThreatActorAttribution(
            actor_name="APT28",
            aliases=["Fancy Bear", "Sofacy"],
            confidence=0.85,
            ttps=["T1566.001", "T1059.001"],
            campaigns=["Campaign2024"],
            targets=["government"],
            motivation="espionage",
            sophistication="advanced",
        )

        assert attribution.actor_name == "APT28"
        assert "Fancy Bear" in attribution.aliases
        assert attribution.confidence == 0.85
        assert attribution.motivation == "espionage"


class TestCampaign:
    """Test Campaign model."""

    def test_campaign_creation(self):
        """Test creating campaign."""
        now = datetime.utcnow()

        event = CampaignEvent(
            event_id="event1",
            timestamp=now,
            event_type="initial_access",
            description="Phishing campaign",
            indicators=["evil.com"],
            affected_targets=["target1"],
            ttps=["T1566.001"],
        )

        campaign = Campaign(
            campaign_id="camp123",
            name="Test Campaign",
            threat_actor="APT28",
            start_date=now,
            targets=["government"],
            timeline=[event],
            objectives=["espionage"],
            ttps=["T1566.001"],
            indicators=["evil.com"],
            confidence=0.8,
            impact="high",
        )

        assert campaign.campaign_id == "camp123"
        assert campaign.threat_actor == "APT28"
        assert len(campaign.timeline) == 1
        assert campaign.confidence == 0.8


class TestOSINTData:
    """Test OSINTData model."""

    def test_osint_creation(self):
        """Test creating OSINT data."""
        now = datetime.utcnow()

        osint = OSINTData(
            source="twitter",
            source_type="social_media",
            url="https://twitter.com/test",
            title="Security Alert",
            content="Malicious activity detected",
            published_date=now,
            author="@security_researcher",
            tags=["malware"],
            relevance_score=0.8,
            extracted_indicators=["evil.com"],
        )

        assert osint.source == "twitter"
        assert osint.relevance_score == 0.8
        assert "evil.com" in osint.extracted_indicators


class TestIntelligenceEnricher:
    """Test Intelligence Enricher."""

    @pytest.fixture
    def enricher(self):
        """Create enricher instance."""
        config = {
            "api_keys": {"virustotal": "test_key"},
            "cache_ttl_hours": 24,
        }
        return IntelligenceEnricher(config)

    def test_enricher_initialization(self, enricher):
        """Test enricher initialization."""
        assert enricher is not None
        assert "APT28" in enricher.threat_actors
        assert "T1566.001" in enricher.attack_techniques

    def test_load_threat_actor_db(self, enricher):
        """Test threat actor database loading."""
        actors = enricher.threat_actors

        assert "APT28" in actors
        assert "APT29" in actors
        assert "Lazarus" in actors
        assert "FIN7" in actors

        # Check APT28 data
        apt28 = actors["APT28"]
        assert "Fancy Bear" in apt28["aliases"]
        assert "espionage" == apt28["motivation"]
        assert "advanced" == apt28["sophistication"]

    def test_load_attack_techniques(self, enricher):
        """Test MITRE ATT&CK techniques loading."""
        techniques = enricher.attack_techniques

        assert "T1566.001" in techniques
        assert "T1059.001" in techniques

        # Check T1566.001 data
        phishing = techniques["T1566.001"]
        assert phishing["tactic"] == "Initial Access"
        assert "Phishing" in phishing["name"]

    def test_extract_indicators_from_stix_pattern(self, enricher):
        """Test indicator extraction from STIX pattern."""
        threat = {
            "pattern": "[ipv4-addr:value = '192.0.2.1'] OR "
            "[domain-name:value = 'evil.com']"
        }

        indicators = enricher._extract_indicators(threat)

        assert len(indicators) > 0
        assert "192.0.2.1" in indicators or "evil.com" in indicators

    def test_extract_indicators_from_description(self, enricher):
        """Test indicator extraction from description."""
        threat = {
            "description": "Malicious activity from 198.51.100.1 and "
            "malware.example.com"
        }

        indicators = enricher._extract_indicators(threat)

        assert len(indicators) > 0
        # Should extract IP and/or domain
        assert any("198.51.100.1" in ind or "example.com" in ind for ind in indicators)

    def test_augment_with_osint(self, enricher):
        """Test OSINT augmentation."""
        threat = {
            "id": "indicator--test",
            "pattern": "[ipv4-addr:value = '8.8.8.8']",
            "description": "Test threat",
        }

        enriched = enricher.augment_with_osint(threat)

        assert isinstance(enriched, EnrichedThreat)
        assert enriched.threat_id == "indicator--test"
        assert enriched.confidence_score >= 0.0

    def test_augment_with_osint_caching(self, enricher):
        """Test OSINT caching."""
        threat = {
            "id": "indicator--cached",
            "pattern": "[ipv4-addr:value = '1.1.1.1']",
        }

        # First call
        enriched1 = enricher.augment_with_osint(threat)

        # Second call should use cache
        enriched2 = enricher.augment_with_osint(threat)

        assert enriched1.enriched_at == enriched2.enriched_at

    def test_attribute_threat_actor_apt28(self, enricher):
        """Test threat actor attribution for APT28."""
        indicators = ["192.0.2.1", "evil.com"]
        ttps = ["T1566.001", "T1059.001", "T1003"]

        attribution = enricher.attribute_threat_actor(indicators, ttps)

        assert isinstance(attribution, ThreatActorAttribution)
        # Should match APT28 based on TTPs
        assert attribution.actor_name in enricher.threat_actors
        assert attribution.confidence > 0.0

    def test_attribute_threat_actor_unknown(self, enricher):
        """Test attribution with no matching actor."""
        indicators = []
        ttps = []

        attribution = enricher.attribute_threat_actor(indicators, ttps)

        assert attribution.actor_name == "Unknown"
        assert attribution.confidence == 0.0

    def test_attribute_threat_actor_confidence_scoring(self, enricher):
        """Test attribution confidence scoring."""
        # High TTP overlap
        indicators = ["test.com"]
        ttps = ["T1566.001", "T1059.001", "T1003", "T1071.001"]

        attribution = enricher.attribute_threat_actor(indicators, ttps)

        # Should have reasonable confidence
        assert 0.0 <= attribution.confidence <= 1.0
        assert "ttp_match" in attribution.attribution_factors

    def test_extract_ttps_from_threat(self, enricher):
        """Test TTP extraction from threat data."""
        threat = {
            "ttps": ["T1566.001"],
            "description": "Phishing campaign using PowerShell",
        }

        ttps = enricher._extract_ttps_from_threat(threat)

        assert "T1566.001" in ttps
        # Should infer PowerShell TTP from description
        assert "T1059.001" in ttps

    def test_extract_ttps_from_kill_chain(self, enricher):
        """Test TTP extraction from kill chain phases."""
        threat = {
            "kill_chain_phases": [
                {"phase_name": "initial-access"},
                {"phase_name": "execution"},
            ]
        }

        ttps = enricher._extract_ttps_from_threat(threat)

        # Should infer TTPs from kill chain phases
        assert len(ttps) > 0

    def test_track_campaign_single_threat(self, enricher):
        """Test campaign tracking with single threat."""
        now = datetime.utcnow()

        threats = [
            {
                "id": "indicator--1",
                "pattern": "[ipv4-addr:value = '192.0.2.1']",
                "created": now.isoformat(),
                "targets": ["government"],
                "description": "Phishing campaign",
            }
        ]

        campaign = enricher.track_campaign(threats)

        assert isinstance(campaign, Campaign)
        assert (
            campaign.threat_actor in enricher.threat_actors
            or campaign.threat_actor == "Unknown"
        )  # noqa: E501
        assert len(campaign.timeline) == 1

    def test_track_campaign_multiple_threats(self, enricher):
        """Test campaign tracking with multiple threats."""
        now = datetime.utcnow()

        threats = [
            {
                "id": "indicator--1",
                "pattern": "[ipv4-addr:value = '192.0.2.1']",
                "created": now.isoformat(),
                "targets": ["government"],
                "ttps": ["T1566.001"],
            },
            {
                "id": "indicator--2",
                "pattern": "[domain-name:value = 'evil.com']",
                "created": (now + timedelta(hours=1)).isoformat(),
                "targets": ["government"],
                "ttps": ["T1566.001"],
            },
        ]

        campaign = enricher.track_campaign(threats)

        assert len(campaign.timeline) == 2
        assert len(campaign.indicators) > 0
        assert "government" in campaign.targets

    def test_track_campaign_timeline_ordering(self, enricher):
        """Test campaign timeline is ordered by timestamp."""
        now = datetime.utcnow()

        threats = [
            {
                "id": "indicator--2",
                "created": (now + timedelta(hours=2)).isoformat(),
                "description": "Second event",
            },
            {
                "id": "indicator--1",
                "created": now.isoformat(),
                "description": "First event",
            },
            {
                "id": "indicator--3",
                "created": (now + timedelta(hours=1)).isoformat(),
                "description": "Middle event",
            },
        ]

        campaign = enricher.track_campaign(threats)

        # Timeline should be sorted
        timestamps = [event.timestamp for event in campaign.timeline]
        assert timestamps == sorted(timestamps)

    def test_extract_timestamp(self, enricher):
        """Test timestamp extraction."""
        now = datetime.utcnow()

        # From created field
        threat1 = {"created": now.isoformat()}
        ts1 = enricher._extract_timestamp(threat1)
        assert isinstance(ts1, datetime)

        # From modified field
        threat2 = {"modified": now.isoformat()}
        ts2 = enricher._extract_timestamp(threat2)
        assert isinstance(ts2, datetime)

        # Default to now if no timestamp
        threat3 = {"description": "No timestamp"}
        ts3 = enricher._extract_timestamp(threat3)
        assert isinstance(ts3, datetime)

    def test_classify_event_type(self, enricher):
        """Test event type classification."""
        # From kill chain phases
        threat1 = {"kill_chain_phases": [{"phase_name": "initial-access"}]}
        event_type1 = enricher._classify_event_type(threat1)
        assert event_type1 == "initial-access"

        # From TTPs
        threat2 = {"ttps": ["T1566.001"]}
        event_type2 = enricher._classify_event_type(threat2)
        assert event_type2 == "initial_access"

        # Unknown
        threat3 = {"description": "Unknown activity"}
        event_type3 = enricher._classify_event_type(threat3)
        assert event_type3 == "unknown"

    def test_calculate_campaign_confidence(self, enricher):
        """Test campaign confidence calculation."""
        now = datetime.utcnow()

        # Single threat, low confidence attribution
        threats1 = [{"id": "1", "created": now.isoformat()}]
        attribution1 = ThreatActorAttribution(actor_name="Unknown", confidence=0.3)
        conf1 = enricher._calculate_campaign_confidence(threats1, attribution1)
        assert 0.0 <= conf1 <= 1.0

        # Multiple threats, high confidence attribution
        threats2 = [{"id": str(i), "created": now.isoformat()} for i in range(5)]
        attribution2 = ThreatActorAttribution(actor_name="APT28", confidence=0.9)
        conf2 = enricher._calculate_campaign_confidence(threats2, attribution2)
        assert conf2 > conf1  # Should have higher confidence

        # Temporally close threats
        threats3 = [
            {"id": "1", "created": now.isoformat()},
            {"id": "2", "created": (now + timedelta(days=1)).isoformat()},
        ]
        attribution3 = ThreatActorAttribution(actor_name="APT28", confidence=0.8)
        conf3 = enricher._calculate_campaign_confidence(threats3, attribution3)
        assert conf3 > 0.5  # Should have good confidence

    def test_infer_objectives(self, enricher):
        """Test campaign objective inference."""
        # Ransomware TTPs
        threats1 = []
        ttps1 = {"T1486"}  # Ransomware
        objectives1 = enricher._infer_objectives(threats1, ttps1)
        assert "financial_gain" in objectives1

        # Credential theft
        threats2 = []
        ttps2 = {"T1003"}  # Credential dumping
        objectives2 = enricher._infer_objectives(threats2, ttps2)
        assert "credential_theft" in objectives2

        # From description
        threats3 = [{"description": "Espionage campaign targeting government"}]
        ttps3 = set()
        objectives3 = enricher._infer_objectives(threats3, ttps3)
        assert "espionage" in objectives3

    def test_assess_impact(self, enricher):
        """Test impact assessment."""
        # Critical impact (many threats)
        threats1 = [{"id": str(i)} for i in range(15)]
        impact1 = enricher._assess_impact(threats1)
        assert impact1 == "critical"

        # High impact
        threats2 = [{"id": str(i)} for i in range(7)]
        impact2 = enricher._assess_impact(threats2)
        assert impact2 == "high"

        # Medium impact
        threats3 = [{"id": str(i)} for i in range(3)]
        impact3 = enricher._assess_impact(threats3)
        assert impact3 == "medium"

        # Low impact
        threats4 = [{"id": "1"}]
        impact4 = enricher._assess_impact(threats4)
        assert impact4 == "low"

    def test_analyze_geolocation(self, enricher):
        """Test geolocation analysis."""
        ip_addresses = ["8.8.8.8", "1.1.1.1"]

        geolocations = enricher.analyze_geolocation(ip_addresses)

        assert len(geolocations) == len(ip_addresses)
        for geo in geolocations:
            assert isinstance(geo, GeoLocation)
            assert geo.ip_address in ip_addresses

    def test_analyze_geolocation_caching(self, enricher):
        """Test geolocation caching."""
        ip_addresses = ["8.8.8.8"]

        # First call
        geo1 = enricher.analyze_geolocation(ip_addresses)

        # Second call should use cache
        geo2 = enricher.analyze_geolocation(ip_addresses)

        assert len(geo1) == len(geo2)

    def test_extract_ttps(self, enricher):
        """Test TTP extraction with details."""
        threat = {
            "ttps": ["T1566.001", "T1059.001"],
            "description": "Phishing with PowerShell",
        }

        ttps = enricher.extract_ttps(threat)

        assert len(ttps) >= 2
        assert all(isinstance(ttp, TTP) for ttp in ttps)

        # Check known TTP
        phishing_ttp = next((t for t in ttps if t.technique_id == "T1566.001"), None)
        assert phishing_ttp is not None
        assert phishing_ttp.tactic == "Initial Access"
        assert phishing_ttp.confidence == 80

    def test_extract_ttps_unknown(self, enricher):
        """Test TTP extraction with unknown technique."""
        threat = {"ttps": ["T9999.999"]}

        ttps = enricher.extract_ttps(threat)

        assert len(ttps) == 1
        assert ttps[0].technique_id == "T9999.999"
        assert ttps[0].technique_name == "Unknown Technique T9999.999"
        assert ttps[0].confidence == 50

    def test_get_campaign_summary(self, enricher):
        """Test campaign summary generation."""
        now = datetime.utcnow()

        # Create a campaign
        threats = [
            {
                "id": "indicator--1",
                "created": now.isoformat(),
                "targets": ["government"],
                "ttps": ["T1566.001"],
            }
        ]

        campaign = enricher.track_campaign(threats)

        # Get summary
        summary = enricher.get_campaign_summary(campaign.campaign_id)

        assert summary is not None
        assert summary["campaign_id"] == campaign.campaign_id
        assert summary["threat_actor"] == campaign.threat_actor
        assert "timeline" in summary
        assert summary["total_events"] == len(campaign.timeline)

    def test_get_campaign_summary_not_found(self, enricher):
        """Test campaign summary for non-existent campaign."""
        summary = enricher.get_campaign_summary("nonexistent")
        assert summary is None

    def test_export_enrichment_report_json(self, enricher):
        """Test JSON report export."""
        threat = {"id": "test", "description": "Test threat"}
        enriched = enricher.augment_with_osint(threat)

        report = enricher.export_enrichment_report(enriched, format="json")

        data = json.loads(report)
        assert data["threat_id"] == "test"
        assert "confidence_score" in data

    def test_export_enrichment_report_markdown(self, enricher):
        """Test Markdown report export."""
        threat = {"id": "test", "description": "Test threat"}
        enriched = enricher.augment_with_osint(threat)

        # Add attribution for richer report
        enriched.threat_actor = ThreatActorAttribution(
            actor_name="APT28",
            aliases=["Fancy Bear"],
            confidence=0.85,
            ttps=["T1566.001"],
            campaigns=["Test Campaign"],
            targets=["government"],
            motivation="espionage",
            sophistication="advanced",
        )

        report = enricher.export_enrichment_report(enriched, format="markdown")

        assert "# Threat Intelligence Enrichment Report" in report
        assert "APT28" in report
        assert "Confidence Score" in report

    def test_export_enrichment_report_invalid_format(self, enricher):
        """Test invalid report format."""
        threat = {"id": "test"}
        enriched = enricher.augment_with_osint(threat)

        with pytest.raises(ValueError):
            enricher.export_enrichment_report(enriched, format="invalid")


class TestEnrichedThreat:
    """Test EnrichedThreat model."""

    def test_enriched_threat_creation(self):
        """Test creating enriched threat."""
        enriched = EnrichedThreat(
            threat_id="threat-123",
            original_data={"type": "indicator"},
            confidence_score=0.75,
            enrichment_sources=["twitter", "github"],
        )

        assert enriched.threat_id == "threat-123"
        assert enriched.confidence_score == 0.75
        assert "twitter" in enriched.enrichment_sources


class TestGeoLocation:
    """Test GeoLocation model."""

    def test_geolocation_full(self):
        """Test geolocation with full data."""
        geo = GeoLocation(
            ip_address="8.8.8.8",
            country="United States",
            country_code="US",
            city="Mountain View",
            region="California",
            latitude=37.4056,
            longitude=-122.0775,
            asn="AS15169",
            isp="Google LLC",
            organization="Google LLC",
        )

        assert geo.ip_address == "8.8.8.8"
        assert geo.country_code == "US"
        assert geo.latitude is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
