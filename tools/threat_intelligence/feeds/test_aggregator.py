"""
Comprehensive tests for Feed Aggregator.

Tests cover STIX/TAXII ingestion, CVE synchronization, custom feed parsing,
deduplication, and normalization.

Author: devCrew_s1
"""

import json
from datetime import datetime

import pytest
from unittest.mock import Mock, patch
import requests
from pydantic import ValidationError
from tools.threat_intelligence.feeds.aggregator import (
    CVE,
    FeedAggregator,
    STIXObject,
    ThreatIndicator,
)


class TestSTIXObject:
    """Test STIX Object model validation."""

    def test_valid_stix_object(self):
        """Test creating valid STIX object."""
        stix_obj = STIXObject(
            id="indicator--12345678-1234-1234-1234-123456789abc",
            type="indicator",
            spec_version="2.1",
            created=datetime.utcnow(),
            modified=datetime.utcnow(),
            pattern="[ipv4-addr:value = '192.168.1.1']",
            name="Malicious IP",
            confidence=85,
        )

        assert stix_obj.type == "indicator"
        assert stix_obj.spec_version == "2.1"
        assert stix_obj.confidence == 85

    def test_invalid_spec_version(self):
        """Test STIX object with invalid spec version."""
        with pytest.raises(ValidationError):
            STIXObject(
                id="indicator--test",
                type="indicator",
                spec_version="1.0",
                created=datetime.utcnow(),
                modified=datetime.utcnow(),
            )

    def test_confidence_bounds(self):
        """Test confidence value validation."""
        # Valid confidence
        stix_obj = STIXObject(
            id="indicator--test",
            type="indicator",
            created=datetime.utcnow(),
            modified=datetime.utcnow(),
            confidence=50,
        )
        assert stix_obj.confidence == 50

        # Invalid confidence (too high)
        with pytest.raises(ValidationError):
            STIXObject(
                id="indicator--test",
                type="indicator",
                created=datetime.utcnow(),
                modified=datetime.utcnow(),
                confidence=150,
            )


class TestCVE:
    """Test CVE model validation."""

    def test_valid_cve(self):
        """Test creating valid CVE object."""
        cve = CVE(
            cve_id="CVE-2024-1234",
            description="Test vulnerability",
            severity="HIGH",
            cvss_score=7.5,
            published_date=datetime.utcnow(),
            references=["https://example.com/advisory"],
            affected_products=["product:1.0"],
            cwe_ids=["CWE-79"],
        )

        assert cve.cve_id == "CVE-2024-1234"
        assert cve.severity == "HIGH"
        assert cve.cvss_score == 7.5

    def test_invalid_cve_id(self):
        """Test CVE with invalid ID format."""
        with pytest.raises(ValidationError):
            CVE(
                cve_id="INVALID-2024-1234",
                description="Test",
                severity="HIGH",
                cvss_score=7.5,
                published_date=datetime.utcnow(),
            )

    def test_severity_normalization(self):
        """Test severity value normalization to uppercase."""
        cve = CVE(
            cve_id="CVE-2024-1234",
            description="Test",
            severity="high",
            cvss_score=7.5,
            published_date=datetime.utcnow(),
        )

        assert cve.severity == "HIGH"

    def test_invalid_severity(self):
        """Test CVE with invalid severity."""
        with pytest.raises(ValidationError):
            CVE(
                cve_id="CVE-2024-1234",
                description="Test",
                severity="INVALID",
                cvss_score=7.5,
                published_date=datetime.utcnow(),
            )

    def test_cvss_score_bounds(self):
        """Test CVSS score validation."""
        # Valid score
        cve = CVE(
            cve_id="CVE-2024-1234",
            description="Test",
            severity="HIGH",
            cvss_score=7.5,
            published_date=datetime.utcnow(),
        )
        assert cve.cvss_score == 7.5

        # Invalid score (too high)
        with pytest.raises(ValidationError):
            CVE(
                cve_id="CVE-2024-1234",
                description="Test",
                severity="HIGH",
                cvss_score=11.0,
                published_date=datetime.utcnow(),
            )


class TestThreatIndicator:
    """Test Threat Indicator model validation."""

    def test_valid_threat_indicator(self):
        """Test creating valid threat indicator."""
        indicator = ThreatIndicator(
            indicator_type="IP",
            value="192.168.1.1",
            threat_type="malware",
            confidence=75,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            tags=["botnet", "c2"],
            source="custom_feed",
        )

        assert indicator.indicator_type == "IP"
        assert indicator.value == "192.168.1.1"
        assert indicator.confidence == 75

    def test_indicator_type_normalization(self):
        """Test indicator type normalization to uppercase."""
        indicator = ThreatIndicator(
            indicator_type="ip",
            value="192.168.1.1",
            threat_type="malware",
            confidence=75,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
        )

        assert indicator.indicator_type == "IP"

    def test_invalid_indicator_type(self):
        """Test threat indicator with invalid type."""
        with pytest.raises(ValidationError):
            ThreatIndicator(
                indicator_type="INVALID_TYPE",
                value="test",
                threat_type="malware",
                confidence=75,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
            )


class TestFeedAggregator:
    """Test Feed Aggregator functionality."""

    @pytest.fixture
    def aggregator(self, tmp_path):
        """Create Feed Aggregator instance with temp cache dir."""
        config = {"cache_dir": str(tmp_path), "timeout": 10, "max_retries": 2}
        return FeedAggregator(config)

    def test_initialization(self, aggregator, tmp_path):
        """Test aggregator initialization."""
        assert aggregator.cache_dir == tmp_path
        assert aggregator.timeout == 10
        assert aggregator.max_retries == 2
        assert aggregator.cache_dir.exists()

    def test_compute_hash(self, aggregator):
        """Test hash computation for deduplication."""
        data1 = {"key": "value", "number": 42}
        data2 = {"number": 42, "key": "value"}  # Same data, different order

        hash1 = aggregator._compute_hash(data1)
        hash2 = aggregator._compute_hash(data2)

        # Hashes should be equal (order-independent)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_make_request_success(self, aggregator):
        """Test successful HTTP request."""
        with patch.object(aggregator.session, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value = mock_response

            response = aggregator._make_request("https://example.com/feed")

            assert response.status_code == 200
            mock_get.assert_called_once()

    def test_make_request_retry(self, aggregator):
        """Test request retry on failure."""
        with patch.object(aggregator.session, "get") as mock_get:
            # First call fails, second succeeds
            mock_get.side_effect = [
                requests.RequestException("Network error"),
                Mock(status_code=200),
            ]

            response = aggregator._make_request("https://example.com/feed")

            assert response.status_code == 200
            assert mock_get.call_count == 2

    def test_make_request_max_retries(self, aggregator):
        """Test max retries exceeded."""
        with patch.object(aggregator.session, "get") as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")

            with pytest.raises(requests.RequestException):
                aggregator._make_request("https://example.com/feed")

            assert mock_get.call_count == 2  # max_retries

    def test_ingest_stix_feed(self, aggregator):
        """Test STIX feed ingestion."""
        stix_bundle = {
            "type": "bundle",
            "id": "bundle--a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
            "objects": [
                {
                    "type": "indicator",
                    "spec_version": "2.1",
                    "id": "indicator--a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d",
                    "created": "2024-01-01T00:00:00.000Z",
                    "modified": "2024-01-01T00:00:00.000Z",
                    "pattern": "[ipv4-addr:value = '192.168.1.1']",
                    "pattern_type": "stix",
                    "valid_from": "2024-01-01T00:00:00Z",
                    "name": "Malicious IP",
                    "labels": ["malicious-activity"],
                }
            ],
        }

        with patch.object(aggregator, "_make_request") as mock_request:
            mock_response = Mock()
            mock_response.json.return_value = stix_bundle
            mock_request.return_value = mock_response

            stix_objects = aggregator.ingest_stix_feed("https://example.com/stix")

            assert len(stix_objects) == 1
            assert stix_objects[0].type == "indicator"
            assert stix_objects[0].name == "Malicious IP"

    def test_ingest_stix_feed_invalid_json(self, aggregator):
        """Test STIX feed with invalid JSON."""
        with patch.object(aggregator, "_make_request") as mock_request:
            mock_response = Mock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_request.return_value = mock_response

            with pytest.raises(ValueError, match="Invalid JSON"):
                aggregator.ingest_stix_feed("https://example.com/stix")

    def test_ingest_taxii_feed(self, aggregator):
        """Test TAXII feed ingestion."""
        with patch("tools.threat_intelligence.feeds.aggregator.Server") as MockServer:
            # Mock TAXII server and collection
            mock_collection = Mock()
            mock_collection.id = "collection-123"
            mock_collection.get_objects.return_value = {
                "objects": [
                    {
                        "type": "indicator",
                        "spec_version": "2.1",
                        "id": "indicator--b1c2d3e4-f5a6-4b5c-8d9e-0f1a2b3c4d5e",
                        "created": "2024-01-01T00:00:00.000Z",
                        "modified": "2024-01-01T00:00:00.000Z",
                        "pattern": "[domain-name:value = 'evil.com']",
                        "pattern_type": "stix",
                        "valid_from": "2024-01-01T00:00:00Z",
                        "labels": ["malicious-activity"],
                    }
                ]
            }

            mock_server = Mock()
            mock_server.collections = [mock_collection]
            MockServer.return_value = mock_server

            stix_objects = aggregator.ingest_taxii_feed(
                "https://taxii.example.com", "collection-123"
            )

            assert len(stix_objects) == 1
            assert stix_objects[0].type == "indicator"

    def test_ingest_taxii_feed_collection_not_found(self, aggregator):
        """Test TAXII feed with non-existent collection."""
        with patch("tools.threat_intelligence.feeds.aggregator.Server") as MockServer:
            mock_collection = Mock()
            mock_collection.id = "different-collection"

            mock_server = Mock()
            mock_server.collections = [mock_collection]
            MockServer.return_value = mock_server

            with pytest.raises(ValueError, match="Collection.*not found"):
                aggregator.ingest_taxii_feed(
                    "https://taxii.example.com", "collection-123"
                )

    def test_sync_cve_database_nvd(self, aggregator):
        """Test CVE sync from NVD."""
        nvd_response = {
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-1234",
                        "descriptions": [{"lang": "en", "value": "Test vulnerability"}],
                        "metrics": {
                            "cvssMetricV31": [
                                {
                                    "cvssData": {"baseScore": 7.5},
                                    "baseSeverity": "HIGH",
                                }
                            ]
                        },
                        "published": "2024-01-01T00:00:00.000Z",
                        "references": [{"url": "https://example.com/advisory"}],
                        "configurations": [],
                        "weaknesses": [{"description": [{"value": "CWE-79"}]}],
                    }
                }
            ]
        }

        with patch.object(aggregator, "_make_request") as mock_request:
            mock_response = Mock()
            mock_response.json.return_value = nvd_response
            mock_request.return_value = mock_response

            cves = aggregator.sync_cve_database("nvd")

            assert len(cves) == 1
            assert cves[0].cve_id == "CVE-2024-1234"
            assert cves[0].severity == "HIGH"
            assert cves[0].cvss_score == 7.5

    def test_sync_cve_database_invalid_source(self, aggregator):
        """Test CVE sync with invalid source."""
        with pytest.raises(ValueError, match="Unsupported CVE source"):
            aggregator.sync_cve_database("invalid_source")

    def test_parse_custom_feed_json(self, aggregator, tmp_path):
        """Test parsing JSON format threat feed."""
        feed_data = [
            {
                "type": "IP",
                "value": "192.168.1.1",
                "threat_type": "malware",
                "confidence": 85,
                "first_seen": "2024-01-01T00:00:00",
                "last_seen": "2024-01-01T00:00:00",
                "tags": ["botnet"],
                "source": "test_feed",
            }
        ]

        feed_file = tmp_path / "feed.json"
        with open(feed_file, "w", encoding="utf-8") as f:
            json.dump(feed_data, f)

        indicators = aggregator.parse_custom_feed(str(feed_file), "json")

        assert len(indicators) == 1
        assert indicators[0].indicator_type == "IP"
        assert indicators[0].value == "192.168.1.1"
        assert indicators[0].confidence == 85

    def test_parse_custom_feed_csv(self, aggregator, tmp_path):
        """Test parsing CSV format threat feed."""
        csv_content = """type,value,threat_type,confidence,first_seen,last_seen,tags,source
IP,10.0.0.1,malware,90,2024-01-01T00:00:00,2024-01-01T00:00:00,"botnet,c2",test_csv
DOMAIN,evil.com,phishing,75,2024-01-01T00:00:00,2024-01-01T00:00:00,phishing,test_csv
"""

        feed_file = tmp_path / "feed.csv"
        with open(feed_file, "w", encoding="utf-8") as f:
            f.write(csv_content)

        indicators = aggregator.parse_custom_feed(str(feed_file), "csv")

        assert len(indicators) == 2
        assert indicators[0].indicator_type == "IP"
        assert indicators[0].value == "10.0.0.1"
        assert indicators[1].indicator_type == "DOMAIN"
        assert indicators[1].value == "evil.com"

    def test_parse_custom_feed_rss(self, aggregator, tmp_path):
        """Test parsing RSS format threat feed."""
        rss_content = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Threat Feed</title>
        <item>
            <title>192.168.1.1</title>
            <description>Malicious IP address</description>
            <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
        </item>
        <item>
            <title>evil.com</title>
            <description>Malicious domain</description>
            <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
        </item>
    </channel>
</rss>
"""

        feed_file = tmp_path / "feed.xml"
        with open(feed_file, "w", encoding="utf-8") as f:
            f.write(rss_content)

        indicators = aggregator.parse_custom_feed(str(feed_file), "rss")

        assert len(indicators) == 2
        assert indicators[0].indicator_type == "IP"
        assert indicators[1].indicator_type == "DOMAIN"

    def test_parse_custom_feed_file_not_found(self, aggregator):
        """Test parsing non-existent feed file."""
        with pytest.raises(FileNotFoundError):
            aggregator.parse_custom_feed("/nonexistent/feed.json", "json")

    def test_parse_custom_feed_unsupported_format(self, aggregator, tmp_path):
        """Test parsing unsupported feed format."""
        feed_file = tmp_path / "feed.txt"
        feed_file.touch()

        with pytest.raises(ValueError, match="Unsupported feed format"):
            aggregator.parse_custom_feed(str(feed_file), "txt")

    def test_deduplicate_indicators(self, aggregator):
        """Test indicator deduplication."""
        now = datetime.utcnow()

        indicators = [
            ThreatIndicator(
                indicator_type="IP",
                value="192.168.1.1",
                threat_type="malware",
                confidence=85,
                first_seen=now,
                last_seen=now,
            ),
            ThreatIndicator(
                indicator_type="IP",
                value="192.168.1.1",  # Duplicate
                threat_type="malware",
                confidence=90,
                first_seen=now,
                last_seen=now,
            ),
            ThreatIndicator(
                indicator_type="DOMAIN",
                value="evil.com",
                threat_type="phishing",
                confidence=75,
                first_seen=now,
                last_seen=now,
            ),
        ]

        unique_indicators = aggregator.deduplicate_indicators(indicators)

        assert len(unique_indicators) == 2
        # Should keep first occurrence of duplicate
        assert unique_indicators[0].value == "192.168.1.1"
        assert unique_indicators[1].value == "evil.com"

    def test_normalize_feed_data_stix(self, aggregator):
        """Test normalizing STIX format data."""
        raw_data = [
            {
                "type": "indicator",
                "spec_version": "2.1",
                "id": "indicator--c1d2e3f4-a5b6-4c5d-8e9f-0a1b2c3d4e5f",
                "created": "2024-01-01T00:00:00.000Z",
                "modified": "2024-01-01T00:00:00.000Z",
                "pattern": "[ipv4-addr:value = '192.168.1.1']",
                "pattern_type": "stix",
                "valid_from": "2024-01-01T00:00:00Z",
                "name": "Test Indicator",
            }
        ]

        stix_objects = aggregator.normalize_feed_data(raw_data, "stix")

        assert len(stix_objects) == 1
        assert stix_objects[0].type == "indicator"
        assert stix_objects[0].name == "Test Indicator"

    def test_normalize_feed_data_custom(self, aggregator):
        """Test normalizing custom format data."""
        raw_data = [
            {
                "name": "Malicious IP",
                "description": "Known malware C2",
                "pattern": "[ipv4-addr:value = '10.0.0.1']",
                "confidence": 90,
                "labels": ["malware", "c2"],
            }
        ]

        stix_objects = aggregator.normalize_feed_data(raw_data, "custom")

        assert len(stix_objects) == 1
        assert stix_objects[0].type == "indicator"
        assert stix_objects[0].name == "Malicious IP"
        assert "custom" in stix_objects[0].labels

    def test_normalize_feed_data_single_object(self, aggregator):
        """Test normalizing single object (not in array)."""
        raw_data = {
            "name": "Test Indicator",
            "description": "Test description",
            "confidence": 80,
        }

        stix_objects = aggregator.normalize_feed_data(raw_data, "custom")

        assert len(stix_objects) == 1
        assert stix_objects[0].name == "Test Indicator"


class TestIntegration:
    """Integration tests for feed aggregator."""

    @pytest.fixture
    def aggregator(self, tmp_path):
        """Create aggregator with test configuration."""
        config = {
            "cache_dir": str(tmp_path),
            "update_interval": 15,
            "timeout": 30,
            "max_retries": 3,
        }
        return FeedAggregator(config)

    def test_end_to_end_custom_feed_processing(self, aggregator, tmp_path):
        """Test complete workflow: parse, deduplicate, normalize."""
        # Create test feed
        feed_data = [
            {
                "type": "IP",
                "value": "192.168.1.1",
                "threat_type": "malware",
                "confidence": 85,
                "first_seen": "2024-01-01T00:00:00",
                "last_seen": "2024-01-01T00:00:00",
                "tags": ["botnet"],
            },
            {
                "type": "IP",
                "value": "192.168.1.1",  # Duplicate
                "threat_type": "malware",
                "confidence": 90,
                "first_seen": "2024-01-01T00:00:00",
                "last_seen": "2024-01-01T00:00:00",
                "tags": ["botnet"],
            },
            {
                "type": "DOMAIN",
                "value": "evil.com",
                "threat_type": "phishing",
                "confidence": 75,
                "first_seen": "2024-01-01T00:00:00",
                "last_seen": "2024-01-01T00:00:00",
                "tags": ["phishing"],
            },
        ]

        feed_file = tmp_path / "test_feed.json"
        with open(feed_file, "w", encoding="utf-8") as f:
            json.dump(feed_data, f)

        # Parse feed
        indicators = aggregator.parse_custom_feed(str(feed_file), "json")
        assert len(indicators) == 3

        # Deduplicate
        unique_indicators = aggregator.deduplicate_indicators(indicators)
        assert len(unique_indicators) == 2

        # Convert indicators to dict format for normalization
        indicator_dicts = [
            {
                "name": f"{ind.indicator_type}: {ind.value}",
                "description": ind.threat_type,
                "confidence": ind.confidence,
                "labels": ind.tags,
            }
            for ind in unique_indicators
        ]

        # Normalize to STIX
        stix_objects = aggregator.normalize_feed_data(indicator_dicts, "custom")
        assert len(stix_objects) == 2
        assert all(obj.type == "indicator" for obj in stix_objects)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=tools.threat_intelligence.feeds"])
