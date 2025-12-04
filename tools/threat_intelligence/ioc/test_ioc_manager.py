"""Tests for IOC Manager module."""

import json
from datetime import datetime, timedelta

import pytest
from ioc_manager import (
    IOC,
    EnrichedIOC,
    GeoLocation,
    IOCLifecycle,
    IOCManager,
)


class TestIOC:
    """Test IOC model."""

    def test_ioc_creation(self):
        """Test creating IOC."""
        now = datetime.utcnow()
        ioc = IOC(
            ioc_type="ip",
            value="192.168.1.1",
            confidence=80,
            first_seen=now,
            last_seen=now,
            tags=["malware"],
        )

        assert ioc.ioc_type == "ip"
        assert ioc.value == "192.168.1.1"
        assert ioc.confidence == 80

    def test_ioc_type_validation(self):
        """Test IOC type validation."""
        now = datetime.utcnow()

        # Valid type
        ioc = IOC(
            ioc_type="domain",
            value="example.com",
            confidence=70,
            first_seen=now,
            last_seen=now,
        )
        assert ioc.ioc_type == "domain"

        # Invalid type should raise error
        with pytest.raises(ValueError):
            IOC(
                ioc_type="invalid",
                value="test",
                confidence=50,
                first_seen=now,
                last_seen=now,
            )

    def test_confidence_validation(self):
        """Test confidence score validation."""
        now = datetime.utcnow()

        # Valid confidence
        ioc = IOC(
            ioc_type="ip",
            value="1.1.1.1",
            confidence=50,
            first_seen=now,
            last_seen=now,
        )
        assert ioc.confidence == 50

        # Out of range should raise error
        with pytest.raises(ValueError):
            IOC(
                ioc_type="ip",
                value="1.1.1.1",
                confidence=150,
                first_seen=now,
                last_seen=now,
            )


class TestIOCManager:
    """Test IOC Manager."""

    @pytest.fixture
    def manager(self):
        """Create IOC manager instance."""
        config = {
            "api_keys": {"virustotal": "test_key", "abuseipdb": "test_key"},
            "whitelist": ["google.com", "microsoft.com"],
            "max_calls_per_minute": 4,
        }
        return IOCManager(config)

    def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager is not None
        assert "google.com" in manager.whitelist
        assert "virustotal" in manager.rate_limits

    def test_extract_iocs_from_stix(self, manager):
        """Test IOC extraction from STIX data."""
        stix_data = [
            {
                "type": "indicator",
                "pattern": "[ipv4-addr:value = '192.0.2.1']",
                "labels": ["malicious-activity"],
                "created_by_ref": "identity--test",
            },
            {
                "type": "indicator",
                "pattern": "[domain-name:value = 'malicious.example.com']",
                "labels": ["phishing"],
                "created_by_ref": "identity--test",
            },
        ]

        iocs = manager.extract_iocs(stix_data)

        assert len(iocs) >= 2
        types = [ioc.ioc_type for ioc in iocs]
        assert "ip" in types
        assert "domain" in types

    def test_extract_iocs_from_text(self, manager):
        """Test IOC extraction from text."""
        text_data = [
            {
                "description": (
                    "Malicious IP 198.51.100.1 and domain evil.example.com "
                    "were observed. "
                    "Hash: 5d41402abc4b2a76b9719d911017c592"
                )
            }
        ]

        iocs = manager.extract_iocs(text_data)

        assert len(iocs) > 0
        types = {ioc.ioc_type for ioc in iocs}
        assert "ip" in types or "domain" in types or "hash" in types

    def test_is_valid_ip(self, manager):
        """Test IP validation."""
        # Valid public IP
        assert manager._is_valid_ip("8.8.8.8")

        # Private IPs should be invalid
        assert not manager._is_valid_ip("192.168.1.1")
        assert not manager._is_valid_ip("10.0.0.1")
        assert not manager._is_valid_ip("172.16.0.1")

        # Loopback should be invalid
        assert not manager._is_valid_ip("127.0.0.1")

        # Invalid format
        assert not manager._is_valid_ip("999.999.999.999")

    def test_is_valid_domain(self, manager):
        """Test domain validation."""
        # Valid domains
        assert manager._is_valid_domain("example.com")
        assert manager._is_valid_domain("sub.example.com")

        # Invalid domains
        assert not manager._is_valid_domain("example.com")  # In excluded list
        assert not manager._is_valid_domain("localhost")
        assert not manager._is_valid_domain("nodot")

    def test_detect_hash_type(self, manager):
        """Test hash type detection."""
        # MD5
        md5_hash = "5d41402abc4b2a76b9719d911017c592"
        assert manager._detect_hash_type(md5_hash) == "md5"

        # SHA1
        sha1_hash = "356a192b7913b04c54574d18c28d46e6395428ab"
        assert manager._detect_hash_type(sha1_hash) == "sha1"

        # SHA256
        sha256_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert manager._detect_hash_type(sha256_hash) == "sha256"

    def test_deduplicate_iocs(self, manager):
        """Test IOC deduplication."""
        now = datetime.utcnow()

        iocs = [
            IOC(
                ioc_type="ip",
                value="8.8.8.8",
                confidence=70,
                first_seen=now,
                last_seen=now,
                tags=["tag1"],
            ),
            IOC(
                ioc_type="ip",
                value="8.8.8.8",
                confidence=80,
                first_seen=now,
                last_seen=now + timedelta(hours=1),
                tags=["tag2"],
            ),
            IOC(
                ioc_type="domain",
                value="test.com",
                confidence=60,
                first_seen=now,
                last_seen=now,
                tags=["tag3"],
            ),
        ]

        unique = manager._deduplicate_iocs(iocs)

        # Should have 2 unique IOCs (one IP, one domain)
        assert len(unique) == 2

        # Check that tags are merged for duplicates
        ip_ioc = next(ioc for ioc in unique if ioc.ioc_type == "ip")
        assert "tag1" in ip_ioc.tags
        assert "tag2" in ip_ioc.tags
        assert ip_ioc.confidence == 80  # Should take max confidence

    def test_enrich_ioc_caching(self, manager):
        """Test IOC enrichment caching."""
        now = datetime.utcnow()
        ioc = IOC(
            ioc_type="ip",
            value="8.8.8.8",
            confidence=70,
            first_seen=now,
            last_seen=now,
        )

        # First enrichment
        enriched1 = manager.enrich_ioc(ioc, services=[])
        assert isinstance(enriched1, EnrichedIOC)

        # Second enrichment should use cache
        enriched2 = manager.enrich_ioc(ioc, services=[])
        assert enriched1.enriched_at == enriched2.enriched_at

    def test_rate_limiting(self, manager):
        """Test rate limiting."""
        # First 4 calls should succeed
        for _ in range(4):
            assert manager._check_rate_limit("virustotal")
            manager._increment_rate_limit("virustotal")

        # 5th call should fail
        assert not manager._check_rate_limit("virustotal")

    def test_filter_false_positives(self, manager):
        """Test false positive filtering."""
        now = datetime.utcnow()

        iocs = [
            IOC(
                ioc_type="domain",
                value="google.com",
                confidence=70,
                first_seen=now,
                last_seen=now,
            ),
            IOC(
                ioc_type="domain",
                value="malicious.com",
                confidence=80,
                first_seen=now,
                last_seen=now,
            ),
            IOC(
                ioc_type="ip",
                value="8.8.8.8",
                confidence=20,
                first_seen=now,
                last_seen=now,
            ),
        ]

        filtered = manager.filter_false_positives(iocs)

        # google.com should be filtered (in whitelist)
        domains = [ioc.value for ioc in filtered if ioc.ioc_type == "domain"]
        assert "google.com" not in domains

        # Low confidence should be filtered
        assert not any(ioc.confidence < 30 for ioc in filtered)

    def test_manage_lifecycle(self, manager):
        """Test IOC lifecycle management."""
        now = datetime.utcnow()

        # New IOC
        new_ioc = IOC(
            ioc_type="ip",
            value="8.8.8.8",
            confidence=70,
            first_seen=now,
            last_seen=now,
        )

        lifecycle = manager.manage_lifecycle(new_ioc)
        assert lifecycle.status == "new"
        assert lifecycle.times_seen == 1

        # Old IOC
        old_ioc = IOC(
            ioc_type="ip",
            value="1.1.1.1",
            confidence=70,
            first_seen=now - timedelta(days=100),
            last_seen=now - timedelta(days=95),
        )

        lifecycle = manager.manage_lifecycle(old_ioc)
        assert lifecycle.status == "expired"

    def test_export_json(self, manager):
        """Test JSON export."""
        now = datetime.utcnow()
        iocs = [
            IOC(
                ioc_type="ip",
                value="8.8.8.8",
                confidence=70,
                first_seen=now,
                last_seen=now,
                tags=["test"],
            )
        ]

        json_output = manager.export_iocs(iocs, format="json")
        data = json.loads(json_output)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["ioc_type"] == "ip"
        assert data[0]["value"] == "8.8.8.8"

    def test_export_csv(self, manager):
        """Test CSV export."""
        now = datetime.utcnow()
        iocs = [
            IOC(
                ioc_type="domain",
                value="test.com",
                confidence=80,
                first_seen=now,
                last_seen=now,
                tags=["tag1", "tag2"],
            )
        ]

        csv_output = manager.export_iocs(iocs, format="csv")
        lines = csv_output.split("\n")

        assert len(lines) >= 2  # Header + data
        assert "type,value,confidence" in lines[0]
        assert "domain,test.com,80" in lines[1]

    def test_export_stix(self, manager):
        """Test STIX export."""
        now = datetime.utcnow()
        iocs = [
            IOC(
                ioc_type="ip",
                value="8.8.8.8",
                confidence=70,
                first_seen=now,
                last_seen=now,
                tags=["malware"],
            )
        ]

        stix_output = manager.export_iocs(iocs, format="stix")
        data = json.loads(stix_output)

        assert data["type"] == "bundle"
        assert len(data["objects"]) == 1
        assert data["objects"][0]["type"] == "indicator"
        assert "ipv4-addr:value" in data["objects"][0]["pattern"]

    def test_export_misp(self, manager):
        """Test MISP export."""
        now = datetime.utcnow()
        iocs = [
            IOC(
                ioc_type="domain",
                value="malicious.com",
                confidence=85,
                first_seen=now,
                last_seen=now,
                tags=["apt"],
            )
        ]

        misp_output = manager.export_iocs(iocs, format="misp")
        data = json.loads(misp_output)

        assert "Event" in data
        assert "Attribute" in data["Event"]
        assert len(data["Event"]["Attribute"]) == 1
        assert data["Event"]["Attribute"][0]["type"] == "domain"

    def test_create_stix_pattern(self, manager):
        """Test STIX pattern creation."""
        now = datetime.utcnow()

        # IP pattern
        ip_ioc = IOC(
            ioc_type="ip",
            value="8.8.8.8",
            confidence=70,
            first_seen=now,
            last_seen=now,
        )
        pattern = manager._create_stix_pattern(ip_ioc)
        assert "[ipv4-addr:value = '8.8.8.8']" == pattern

        # Domain pattern
        domain_ioc = IOC(
            ioc_type="domain",
            value="test.com",
            confidence=70,
            first_seen=now,
            last_seen=now,
        )
        pattern = manager._create_stix_pattern(domain_ioc)
        assert "[domain-name:value = 'test.com']" == pattern

        # Hash pattern
        hash_ioc = IOC(
            ioc_type="hash",
            value="5d41402abc4b2a76b9719d911017c592",
            confidence=70,
            first_seen=now,
            last_seen=now,
            context={"hash_type": "md5"},
        )
        pattern = manager._create_stix_pattern(hash_ioc)
        assert "file:hashes.MD5" in pattern

    def test_invalid_export_format(self, manager):
        """Test invalid export format."""
        now = datetime.utcnow()
        iocs = [
            IOC(
                ioc_type="ip",
                value="8.8.8.8",
                confidence=70,
                first_seen=now,
                last_seen=now,
            )
        ]

        with pytest.raises(ValueError):
            manager.export_iocs(iocs, format="invalid")


class TestEnrichedIOC:
    """Test EnrichedIOC model."""

    def test_enriched_ioc_creation(self):
        """Test creating enriched IOC."""
        now = datetime.utcnow()
        ioc = IOC(
            ioc_type="ip",
            value="8.8.8.8",
            confidence=70,
            first_seen=now,
            last_seen=now,
        )

        enriched = EnrichedIOC(
            ioc=ioc,
            reputation_score=85,
            malicious_votes=2,
            benign_votes=50,
            enrichment_sources=["virustotal"],
        )

        assert enriched.reputation_score == 85
        assert enriched.malicious_votes == 2
        assert "virustotal" in enriched.enrichment_sources


class TestGeoLocation:
    """Test GeoLocation model."""

    def test_geolocation_creation(self):
        """Test creating geolocation."""
        geo = GeoLocation(
            country="United States",
            country_code="US",
            city="New York",
            latitude=40.7128,
            longitude=-74.0060,
            asn="AS15169",
            isp="Google LLC",
        )

        assert geo.country == "United States"
        assert geo.country_code == "US"
        assert geo.latitude == 40.7128


class TestIOCLifecycle:
    """Test IOCLifecycle model."""

    def test_lifecycle_creation(self):
        """Test creating lifecycle."""
        now = datetime.utcnow()
        ioc = IOC(
            ioc_type="ip",
            value="8.8.8.8",
            confidence=70,
            first_seen=now,
            last_seen=now,
        )

        lifecycle = IOCLifecycle(
            ioc=ioc,
            status="active",
            created_at=now,
            updated_at=now,
            times_seen=5,
        )

        assert lifecycle.status == "active"
        assert lifecycle.times_seen == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
