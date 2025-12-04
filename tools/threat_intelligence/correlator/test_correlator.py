"""Test suite for Threat Correlator module."""

from datetime import datetime, timedelta
from typing import List

import pytest

from .threat_correlator import (
    CVE,
    Asset,
    STIXObject,
    ThreatCorrelator,
    ThreatIndicator,
)


class TestAssetModel:
    """Test Asset model validation."""

    def test_asset_valid(self):
        """Test valid asset creation."""
        asset = Asset(
            asset_id="asset-001",
            name="Web Server 01",
            type="server",
            ip_addresses=["192.168.1.100"],
            software=[{"name": "nginx", "version": "1.18.0"}],
            criticality="HIGH",
        )
        assert asset.asset_id == "asset-001"
        assert asset.criticality == "HIGH"
        assert asset.type == "server"

    def test_asset_criticality_validation(self):
        """Test criticality level validation."""
        with pytest.raises(ValueError):
            Asset(
                asset_id="asset-001",
                name="Test",
                type="server",
                criticality="INVALID",
            )

    def test_asset_type_validation(self):
        """Test asset type validation."""
        with pytest.raises(ValueError):
            Asset(
                asset_id="asset-001",
                name="Test",
                type="invalid_type",
                criticality="HIGH",
            )


class TestCVEModel:
    """Test CVE model validation."""

    def test_cve_valid(self):
        """Test valid CVE creation."""
        cve = CVE(
            cve_id="CVE-2024-1234",
            description="Remote code execution",
            cvss_score=9.8,
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            exploit_available=True,
            epss_score=0.85,
        )
        assert cve.cve_id == "CVE-2024-1234"
        assert cve.cvss_score == 9.8

    def test_cve_id_validation(self):
        """Test CVE ID format validation."""
        with pytest.raises(ValueError):
            CVE(cve_id="INVALID-2024-1234")

    def test_cvss_score_validation(self):
        """Test CVSS score range validation."""
        with pytest.raises(ValueError):
            CVE(cve_id="CVE-2024-1234", cvss_score=11.0)


class TestThreatCorrelator:
    """Test ThreatCorrelator functionality."""

    @pytest.fixture
    def correlator(self) -> ThreatCorrelator:
        """Create correlator instance."""
        config = {
            "cache_enabled": True,
            "cache_ttl": 3600,
            "min_correlation_score": 0.5,
        }
        return ThreatCorrelator(config)

    @pytest.fixture
    def sample_cves(self) -> List[CVE]:
        """Create sample CVEs."""
        return [
            CVE(
                cve_id="CVE-2024-1234",
                description="Remote code execution vulnerability",
                cvss_score=9.8,
                exploit_available=True,
                epss_score=0.85,
                published_date="2024-01-15T00:00:00Z",
            ),
            CVE(
                cve_id="CVE-2024-5678",
                description="SQL injection vulnerability",
                cvss_score=7.5,
                exploit_available=False,
                epss_score=0.15,
                published_date="2024-02-01T00:00:00Z",
            ),
        ]

    @pytest.fixture
    def sample_stix_objects(self) -> List[STIXObject]:
        """Create sample STIX objects."""
        now = datetime.now().isoformat()
        return [
            STIXObject(
                id="indicator--123",
                type="indicator",
                created=now,
                modified=now,
                name="CVE-2024-1234 Exploitation",
                description="Active exploitation of CVE-2024-1234",
                labels=["exploit", "active-exploitation"],
                external_references=[
                    {"source_name": "cve", "external_id": "CVE-2024-1234"}
                ],
            ),
            STIXObject(
                id="threat-actor--456",
                type="threat-actor",
                created=now,
                modified=now,
                name="APT28",
                description="Nation-state actor exploiting CVE-2024-1234",
                external_references=[
                    {"source_name": "cve", "external_id": "CVE-2024-1234"},
                    {"source_name": "mitre-attack", "external_id": "T1190"},
                ],
            ),
        ]

    @pytest.fixture
    def sample_threats(self) -> List[ThreatIndicator]:
        """Create sample threat indicators."""
        now = datetime.now().isoformat()
        return [
            ThreatIndicator(
                indicator_id="threat-001",
                type="cve",
                value="CVE-2024-1234",
                threat_type="exploit",
                confidence=0.9,
                severity="CRITICAL",
                first_seen=now,
                last_seen=now,
                tags=["remote-code-execution"],
            ),
            ThreatIndicator(
                indicator_id="threat-002",
                type="ip",
                value="192.168.1.100",
                threat_type="malware",
                confidence=0.7,
                severity="HIGH",
                first_seen=now,
                last_seen=now,
                tags=["botnet"],
            ),
        ]

    @pytest.fixture
    def sample_assets(self) -> List[Asset]:
        """Create sample assets."""
        return [
            Asset(
                asset_id="asset-001",
                name="Web Server 01",
                type="server",
                ip_addresses=["192.168.1.100"],
                software=[
                    {"name": "nginx", "version": "1.18.0"},
                    {"name": "openssl", "version": "1.1.1"},
                ],
                criticality="CRITICAL",
            ),
            Asset(
                asset_id="asset-002",
                name="Workstation 01",
                type="workstation",
                ip_addresses=["192.168.1.200"],
                software=[{"name": "chrome", "version": "120.0"}],
                criticality="MEDIUM",
            ),
        ]

    def test_initialization(self, correlator: ThreatCorrelator):
        """Test correlator initialization."""
        assert correlator.cache_enabled is True
        assert correlator.min_correlation_score == 0.5
        assert len(correlator._correlation_cache) == 0

    def test_correlate_vulnerabilities_with_direct_match(
        self,
        correlator: ThreatCorrelator,
        sample_cves: List[CVE],
        sample_stix_objects: List[STIXObject],
    ):
        """Test vulnerability correlation with direct CVE match."""
        correlations = correlator.correlate_vulnerabilities(
            sample_cves, sample_stix_objects
        )

        assert len(correlations) > 0
        cve_1234_corr = next(
            (c for c in correlations if c.cve_id == "CVE-2024-1234"), None
        )
        assert cve_1234_corr is not None
        assert cve_1234_corr.correlation_score >= 0.5
        assert cve_1234_corr.active_exploitation is True
        assert len(cve_1234_corr.threat_indicators) > 0

    def test_correlate_vulnerabilities_with_threat_actors(
        self,
        correlator: ThreatCorrelator,
        sample_cves: List[CVE],
        sample_stix_objects: List[STIXObject],
    ):
        """Test extraction of threat actors from correlations."""
        correlations = correlator.correlate_vulnerabilities(
            sample_cves, sample_stix_objects
        )

        cve_1234_corr = next(
            (c for c in correlations if c.cve_id == "CVE-2024-1234"), None
        )
        assert cve_1234_corr is not None
        assert "APT28" in cve_1234_corr.threat_actors

    def test_correlate_vulnerabilities_with_techniques(
        self,
        correlator: ThreatCorrelator,
        sample_cves: List[CVE],
        sample_stix_objects: List[STIXObject],
    ):
        """Test extraction of ATT&CK techniques."""
        correlations = correlator.correlate_vulnerabilities(
            sample_cves, sample_stix_objects
        )

        cve_1234_corr = next(
            (c for c in correlations if c.cve_id == "CVE-2024-1234"), None
        )
        assert cve_1234_corr is not None
        assert "T1190" in cve_1234_corr.techniques

    def test_correlate_vulnerabilities_caching(
        self,
        correlator: ThreatCorrelator,
        sample_cves: List[CVE],
        sample_stix_objects: List[STIXObject],
    ):
        """Test correlation result caching."""
        # First call
        correlations1 = correlator.correlate_vulnerabilities(
            sample_cves, sample_stix_objects
        )

        # Second call should use cache
        correlations2 = correlator.correlate_vulnerabilities(
            sample_cves, sample_stix_objects
        )

        assert len(correlations1) == len(correlations2)
        assert correlator.get_cache_stats()["correlation_cache_size"] > 0

    def test_analyze_asset_risk_with_threats(
        self,
        correlator: ThreatCorrelator,
        sample_assets: List[Asset],
        sample_threats: List[ThreatIndicator],
    ):
        """Test asset risk analysis with threats."""
        risk_assessments = correlator.analyze_asset_risk(sample_assets, sample_threats)

        assert len(risk_assessments) == len(sample_assets)

        # Web server should have higher risk (IP match + critical)
        web_server_risk = next(
            (r for r in risk_assessments if r.asset_id == "asset-001"), None
        )
        assert web_server_risk is not None
        assert web_server_risk.risk_score > 0
        assert web_server_risk.threat_count > 0

    def test_calculate_risk_score_critical_asset(
        self, correlator: ThreatCorrelator, sample_assets: List[Asset]
    ):
        """Test risk score calculation for critical asset."""
        critical_asset = sample_assets[0]  # CRITICAL asset
        threats = [
            ThreatIndicator(
                indicator_id="t1",
                type="cve",
                value="CVE-2024-1234",
                threat_type="exploit",
                confidence=0.9,
                severity="CRITICAL",
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
            )
        ]

        risk_score = correlator.calculate_risk_score(critical_asset, threats)
        assert 0 <= risk_score <= 100
        assert risk_score > 45  # Should be high for critical asset + threat

    def test_calculate_risk_score_no_threats(
        self, correlator: ThreatCorrelator, sample_assets: List[Asset]
    ):
        """Test risk score with no threats."""
        asset = sample_assets[0]
        risk_score = correlator.calculate_risk_score(asset, [])
        assert risk_score == 0.0

    def test_analyze_sbom_spdx_format(self, correlator: ThreatCorrelator):
        """Test SBOM analysis with SPDX format."""
        sbom = {
            "spdxVersion": "SPDX-2.3",
            "SPDXID": "SPDXRef-DOCUMENT",
            "packages": [
                {
                    "name": "openssl",
                    "versionInfo": "1.1.1",
                    "SPDXID": "SPDXRef-Package-openssl",
                },
                {
                    "name": "nginx",
                    "versionInfo": "1.18.0",
                    "SPDXID": "SPDXRef-Package-nginx",
                },
            ],
        }

        threats = [
            ThreatIndicator(
                indicator_id="t1",
                type="cve",
                value="CVE-2024-1234",
                threat_type="exploit",
                confidence=0.9,
                severity="CRITICAL",
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
            )
        ]

        analysis = correlator.analyze_sbom(sbom, threats)

        assert analysis.total_components == 2
        assert analysis.threat_exposure >= 0
        assert isinstance(analysis.recommendations, list)

    def test_analyze_sbom_cyclonedx_format(self, correlator: ThreatCorrelator):
        """Test SBOM analysis with CycloneDX format."""
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "components": [
                {"name": "openssl", "version": "1.1.1", "purl": "pkg:generic/openssl"},
                {"name": "nginx", "version": "1.18.0", "purl": "pkg:generic/nginx"},
            ],
        }

        threats = [
            ThreatIndicator(
                indicator_id="t1",
                type="cve",
                value="CVE-2024-1234",
                threat_type="exploit",
                confidence=0.8,
                severity="HIGH",
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
            )
        ]

        analysis = correlator.analyze_sbom(sbom, threats)

        assert analysis.total_components == 2
        assert analysis.threat_exposure >= 0
        assert len(analysis.recommendations) > 0

    def test_predict_exploit_likelihood_high_epss(
        self, correlator: ThreatCorrelator, sample_stix_objects: List[STIXObject]
    ):
        """Test exploit prediction with high EPSS score."""
        cve = CVE(
            cve_id="CVE-2024-1234",
            cvss_score=9.8,
            exploit_available=True,
            epss_score=0.95,  # Very high EPSS
        )

        likelihood = correlator.predict_exploit_likelihood(cve, sample_stix_objects)

        assert 0 <= likelihood <= 1
        assert likelihood > 0.8  # Should be high

    def test_predict_exploit_likelihood_active_exploitation(
        self, correlator: ThreatCorrelator, sample_stix_objects: List[STIXObject]
    ):
        """Test exploit prediction with active exploitation indicator."""
        cve = CVE(
            cve_id="CVE-2024-1234",
            cvss_score=9.8,
            exploit_available=True,
            epss_score=0.5,
        )

        likelihood = correlator.predict_exploit_likelihood(cve, sample_stix_objects)

        # Should be high due to active-exploitation label in STIX
        assert likelihood > 0.7

    def test_predict_exploit_likelihood_no_data(self, correlator: ThreatCorrelator):
        """Test exploit prediction with minimal data."""
        cve = CVE(cve_id="CVE-2024-9999", cvss_score=0.0)

        likelihood = correlator.predict_exploit_likelihood(cve, [])

        assert likelihood == 0.0

    def test_cache_clearing(
        self,
        correlator: ThreatCorrelator,
        sample_cves: List[CVE],
        sample_stix_objects: List[STIXObject],
    ):
        """Test cache clearing functionality."""
        # Populate cache
        correlator.correlate_vulnerabilities(sample_cves, sample_stix_objects)
        assert correlator.get_cache_stats()["correlation_cache_size"] > 0

        # Clear cache
        correlator.clear_cache()
        assert correlator.get_cache_stats()["correlation_cache_size"] == 0

    def test_exposure_window_calculation(self, correlator: ThreatCorrelator):
        """Test exposure window calculation."""
        # Threat from 30 days ago
        past_date = (datetime.now() - timedelta(days=30)).isoformat()
        threats = [
            ThreatIndicator(
                indicator_id="t1",
                type="cve",
                value="CVE-2024-1234",
                threat_type="exploit",
                confidence=0.9,
                severity="CRITICAL",
                first_seen=past_date,
                last_seen=datetime.now().isoformat(),
            )
        ]

        exposure = correlator._calculate_exposure_window(threats)
        assert 25 <= exposure <= 35  # Should be ~30 days

    def test_age_factor_calculation(self, correlator: ThreatCorrelator):
        """Test vulnerability age factor calculation."""
        # Recent vulnerability
        recent_date = (datetime.now() - timedelta(days=30)).isoformat()
        recent_factor = correlator._calculate_age_factor(recent_date)
        assert 0 <= recent_factor < 0.2

        # Old vulnerability
        old_date = (datetime.now() - timedelta(days=365)).isoformat()
        old_factor = correlator._calculate_age_factor(old_date)
        assert old_factor >= 0.9

    def test_sbom_format_detection_spdx(self, correlator: ThreatCorrelator):
        """Test SPDX format detection."""
        sbom = {"spdxVersion": "SPDX-2.3", "SPDXID": "SPDXRef-DOCUMENT"}
        fmt = correlator._detect_sbom_format(sbom)
        assert fmt == "SPDX"

    def test_sbom_format_detection_cyclonedx(self, correlator: ThreatCorrelator):
        """Test CycloneDX format detection."""
        sbom = {"bomFormat": "CycloneDX", "specVersion": "1.4"}
        fmt = correlator._detect_sbom_format(sbom)
        assert fmt == "CycloneDX"

    def test_sbom_format_detection_unknown(self, correlator: ThreatCorrelator):
        """Test unknown format detection."""
        sbom = {"unknown": "format"}
        fmt = correlator._detect_sbom_format(sbom)
        assert fmt == "Unknown"

    def test_recommendations_generation(
        self, correlator: ThreatCorrelator, sample_assets: List[Asset]
    ):
        """Test recommendation generation."""
        asset = sample_assets[0]
        threats = [
            ThreatIndicator(
                indicator_id=f"t{i}",
                type="cve",
                value=f"CVE-2024-{i}",
                threat_type="exploit",
                confidence=0.9,
                severity="CRITICAL",
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
            )
            for i in range(3)
        ]

        vulnerable_software = [
            {
                "name": "openssl",
                "version": "1.1.1",
                "cve": "CVE-2024-1",
                "severity": "CRITICAL",
            }
        ]

        recommendations = correlator._generate_recommendations(
            asset, threats, vulnerable_software
        )

        assert len(recommendations) > 0
        assert any("URGENT" in rec for rec in recommendations)

    def test_multiple_asset_risk_analysis(
        self,
        correlator: ThreatCorrelator,
        sample_assets: List[Asset],
        sample_threats: List[ThreatIndicator],
    ):
        """Test risk analysis for multiple assets."""
        risk_assessments = correlator.analyze_asset_risk(sample_assets, sample_threats)

        assert len(risk_assessments) == len(sample_assets)

        # All assessments should have valid structure
        for risk in risk_assessments:
            assert risk.asset_id in [a.asset_id for a in sample_assets]
            assert 0 <= risk.risk_score <= 100
            assert risk.threat_count >= 0
            assert isinstance(risk.recommendations, list)

    def test_correlation_score_boosting(
        self, correlator: ThreatCorrelator, sample_cves: List[CVE]
    ):
        """Test correlation score boosting with multiple factors."""
        now = datetime.now().isoformat()
        cve = sample_cves[0]  # CVE with exploit_available=True

        # Multiple STIX objects referencing same CVE
        stix_objects = [
            STIXObject(
                id=f"indicator--{i}",
                type="indicator",
                created=now,
                modified=now,
                labels=["exploit", "active-exploitation"],
                external_references=[{"source_name": "cve", "external_id": cve.cve_id}],
            )
            for i in range(3)
        ]

        correlation = correlator._correlate_single_vulnerability(cve, stix_objects)

        # Score should be boosted due to multiple factors
        assert correlation.correlation_score > 0.8
        assert correlation.active_exploitation is True


class TestThreatCorrelationEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_vulnerability_list(self):
        """Test correlation with empty vulnerability list."""
        correlator = ThreatCorrelator()
        correlations = correlator.correlate_vulnerabilities([], [])
        assert correlations == []

    def test_empty_threat_list(self):
        """Test correlation with empty threat list."""
        correlator = ThreatCorrelator()
        cves = [CVE(cve_id="CVE-2024-1234")]
        correlations = correlator.correlate_vulnerabilities(cves, [])
        assert len(correlations) == 0  # No correlations above threshold

    def test_asset_with_no_software(self):
        """Test asset risk with no software installed."""
        correlator = ThreatCorrelator()
        asset = Asset(
            asset_id="asset-001",
            name="Empty Server",
            type="server",
            software=[],
            criticality="LOW",
        )

        threats = [
            ThreatIndicator(
                indicator_id="t1",
                type="cve",
                value="CVE-2024-1234",
                threat_type="exploit",
                confidence=0.9,
                severity="CRITICAL",
                first_seen=datetime.now().isoformat(),
                last_seen=datetime.now().isoformat(),
            )
        ]

        risk_assessments = correlator.analyze_asset_risk([asset], threats)
        assert len(risk_assessments) == 1
        assert risk_assessments[0].risk_score >= 0

    def test_sbom_with_no_components(self):
        """Test SBOM analysis with no components."""
        correlator = ThreatCorrelator()
        sbom = {"spdxVersion": "SPDX-2.3", "packages": []}

        analysis = correlator.analyze_sbom(sbom, [])
        assert analysis.total_components == 0
        assert analysis.vulnerable_components == 0
        assert analysis.threat_exposure == 0.0

    def test_invalid_date_handling(self):
        """Test handling of invalid dates."""
        correlator = ThreatCorrelator()

        # Invalid date should return default factor
        factor = correlator._calculate_age_factor("invalid-date")
        assert factor == 0.5

    def test_cache_with_disabled_caching(self):
        """Test correlator with caching disabled."""
        correlator = ThreatCorrelator(config={"cache_enabled": False})
        cves = [CVE(cve_id="CVE-2024-1234", cvss_score=7.5)]
        now = datetime.now().isoformat()
        stix_objects = [
            STIXObject(
                id="indicator--1",
                type="indicator",
                created=now,
                modified=now,
                external_references=[
                    {"source_name": "cve", "external_id": "CVE-2024-1234"}
                ],
            )
        ]

        # Multiple calls should not cache
        correlator.correlate_vulnerabilities(cves, stix_objects)
        correlator.correlate_vulnerabilities(cves, stix_objects)

        assert correlator.get_cache_stats()["correlation_cache_size"] == 0


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_complete_threat_assessment_workflow(self):
        """Test complete workflow: correlate -> analyze -> assess."""
        correlator = ThreatCorrelator()

        # Step 1: Create test data
        cves = [
            CVE(
                cve_id="CVE-2024-1234",
                cvss_score=9.8,
                exploit_available=True,
                epss_score=0.9,
            ),
            CVE(
                cve_id="CVE-2024-5678",
                cvss_score=7.5,
                exploit_available=False,
                epss_score=0.2,
            ),
        ]

        now = datetime.now().isoformat()
        stix_objects = [
            STIXObject(
                id="indicator--1",
                type="indicator",
                created=now,
                modified=now,
                labels=["exploit", "active-exploitation"],
                external_references=[
                    {"source_name": "cve", "external_id": "CVE-2024-1234"}
                ],
            )
        ]

        assets = [
            Asset(
                asset_id="asset-001",
                name="Production Server",
                type="server",
                ip_addresses=["10.0.1.100"],
                software=[{"name": "apache", "version": "2.4.50"}],
                criticality="CRITICAL",
            )
        ]

        threats = [
            ThreatIndicator(
                indicator_id="t1",
                type="cve",
                value="CVE-2024-1234",
                threat_type="exploit",
                confidence=0.95,
                severity="CRITICAL",
                first_seen=now,
                last_seen=now,
            )
        ]

        # Step 2: Correlate vulnerabilities
        correlations = correlator.correlate_vulnerabilities(cves, stix_objects)
        assert len(correlations) > 0

        # Step 3: Analyze asset risk
        risk_assessments = correlator.analyze_asset_risk(assets, threats)
        assert len(risk_assessments) > 0
        assert risk_assessments[0].risk_score > 0

        # Step 4: Predict exploit likelihood
        likelihood = correlator.predict_exploit_likelihood(cves[0], stix_objects)
        assert likelihood > 0.7  # Should be high

    def test_sbom_vulnerability_assessment(self):
        """Test SBOM-based vulnerability assessment."""
        correlator = ThreatCorrelator()

        # Real-world style SBOM
        sbom = {
            "spdxVersion": "SPDX-2.3",
            "packages": [
                {"name": "log4j", "versionInfo": "2.14.1"},
                {"name": "spring-boot", "versionInfo": "2.5.0"},
                {"name": "jackson-databind", "versionInfo": "2.12.3"},
            ],
        }

        now = datetime.now().isoformat()
        threats = [
            ThreatIndicator(
                indicator_id=f"t{i}",
                type="cve",
                value=f"CVE-2024-{i}",
                threat_type="exploit",
                confidence=0.9,
                severity="CRITICAL" if i < 2 else "HIGH",
                first_seen=now,
                last_seen=now,
            )
            for i in range(5)
        ]

        analysis = correlator.analyze_sbom(sbom, threats)

        assert analysis.total_components == 3
        assert len(analysis.recommendations) > 0
        assert analysis.threat_exposure >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
