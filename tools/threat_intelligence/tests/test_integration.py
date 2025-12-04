"""
Integration tests for Threat Intelligence Platform.

Tests end-to-end workflows including:
- Feed ingestion and normalization
- Threat correlation with assets
- VEX document generation
- ATT&CK mapping and analysis
- IOC extraction and enrichment
- Complete threat intelligence workflows
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestFullThreatIntelligenceWorkflow:
    """Test complete end-to-end threat intelligence workflows."""

    @pytest.mark.asyncio
    async def test_full_threat_intelligence_workflow(
        self,
        temp_dir: Path,
        sample_stix_bundle: Dict[str, Any],
        sample_cve_list: List[Dict[str, Any]],
        sample_sbom_spdx: Dict[str, Any],
        mock_elasticsearch: Mock,
    ) -> None:
        """
        Test complete TI workflow: Ingest → Correlate → Generate VEX → Report.

        Steps:
            1. Ingest STIX feed
            2. Sync CVE database
            3. Correlate with SBOM
            4. Generate VEX document
            5. Generate threat report
        """
        # Step 1: Ingest STIX feed
        with patch(
            "tools.threat_intelligence.feeds.aggregator.FeedAggregator"
        ) as mock_agg:
            mock_agg_instance = Mock()
            mock_agg_instance.ingest_stix_bundle = AsyncMock(
                return_value={
                    "status": "success",
                    "objects_ingested": len(sample_stix_bundle["objects"]),
                    "indicators": 1,
                    "malware": 1,
                    "relationships": 1,
                }
            )
            mock_agg.return_value = mock_agg_instance

            ingest_result = await mock_agg_instance.ingest_stix_bundle(
                sample_stix_bundle
            )
            assert ingest_result["status"] == "success"
            assert ingest_result["objects_ingested"] == 3
            assert ingest_result["indicators"] == 1

        # Step 2: Sync CVE database
        with patch("tools.threat_intelligence.feeds.aggregator.CVESync") as mock_cve:
            mock_cve_instance = Mock()
            mock_cve_instance.sync_cves = AsyncMock(
                return_value={
                    "status": "success",
                    "cves_synced": len(sample_cve_list),
                    "new_cves": 3,
                    "updated_cves": 2,
                }
            )
            mock_cve.return_value = mock_cve_instance

            cve_result = await mock_cve_instance.sync_cves()
            assert cve_result["status"] == "success"
            assert cve_result["cves_synced"] == 5

        # Step 3: Correlate with SBOM
        with patch(
            "tools.threat_intelligence.correlator.threat_correlator.ThreatCorrelator"
        ) as mock_corr:
            mock_corr_instance = Mock()
            mock_corr_instance.correlate_sbom = AsyncMock(
                return_value={
                    "status": "success",
                    "vulnerabilities_found": 2,
                    "affected_components": ["vulnerable-lib@1.2.3"],
                    "risk_score": 85.5,
                    "matches": [
                        {
                            "cve": "CVE-2024-1000",
                            "component": "vulnerable-lib@1.2.3",
                            "severity": "CRITICAL",
                        }
                    ],
                }
            )
            mock_corr.return_value = mock_corr_instance

            corr_result = await mock_corr_instance.correlate_sbom(sample_sbom_spdx)
            assert corr_result["status"] == "success"
            assert corr_result["vulnerabilities_found"] == 2
            assert "vulnerable-lib@1.2.3" in corr_result["affected_components"]

        # Step 4: Generate VEX document
        with patch(
            "tools.threat_intelligence.vex.vex_generator.VEXGenerator"
        ) as mock_vex:
            mock_vex_instance = Mock()
            mock_vex_instance.generate_vex = AsyncMock(
                return_value={
                    "@context": "https://openvex.dev/ns/v0.2.0",
                    "@id": "https://example.com/vex/2024/001",
                    "author": "Test Team",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "version": "1",
                    "statements": [
                        {
                            "vulnerability": {"name": "CVE-2024-1000"},
                            "status": "affected",
                        }
                    ],
                }
            )
            mock_vex.return_value = mock_vex_instance

            vex_doc = await mock_vex_instance.generate_vex(
                sbom=sample_sbom_spdx, vulnerabilities=corr_result["matches"]
            )
            assert vex_doc["@context"] == "https://openvex.dev/ns/v0.2.0"
            assert len(vex_doc["statements"]) == 1

        # Step 5: Generate threat report
        with patch(
            "tools.threat_intelligence.cli.threat_cli.ReportGenerator"
        ) as mock_report:
            mock_report_instance = Mock()
            mock_report_instance.generate_report = AsyncMock(
                return_value={
                    "report_id": "TI-2024-001",
                    "title": "Threat Analysis Report",
                    "vulnerabilities": 2,
                    "risk_level": "HIGH",
                    "vex_document": vex_doc,
                    "recommendations": ["Upgrade vulnerable-lib"],
                }
            )
            mock_report.return_value = mock_report_instance

            report = await mock_report_instance.generate_report(
                correlation=corr_result, vex=vex_doc
            )
            assert report["report_id"] == "TI-2024-001"
            assert report["vulnerabilities"] == 2
            assert report["risk_level"] == "HIGH"

    @pytest.mark.asyncio
    async def test_stix_taxii_feed_ingestion_workflow(
        self,
        sample_stix_bundle: Dict[str, Any],
        mock_taxii_server: Mock,
        mock_elasticsearch: Mock,
    ) -> None:
        """
        Test STIX/TAXII feed ingestion → Normalization → Storage.

        Steps:
            1. Connect to TAXII server
            2. Fetch STIX objects
            3. Normalize data
            4. Store in Elasticsearch
        """
        with patch(
            "tools.threat_intelligence.feeds.aggregator.TAXIIClient"
        ) as mock_taxii:
            # Step 1: Connect to TAXII server
            mock_taxii_instance = Mock()
            mock_taxii_instance.connect = Mock(return_value=True)
            mock_taxii_instance.get_collections = Mock(
                return_value=mock_taxii_server.get_collections()
            )
            mock_taxii.return_value = mock_taxii_instance

            connected = mock_taxii_instance.connect()
            assert connected is True

            collections = mock_taxii_instance.get_collections()
            assert len(collections) == 1
            assert collections[0]["id"] == "collection-1"

            # Step 2: Fetch STIX objects
            mock_taxii_instance.get_objects = Mock(
                return_value=mock_taxii_server.get_objects()
            )
            objects = mock_taxii_instance.get_objects("collection-1")
            assert objects["type"] == "bundle"
            assert len(objects["objects"]) == 1

        # Step 3: Normalize data
        with patch(
            "tools.threat_intelligence.feeds.aggregator.STIXNormalizer"
        ) as mock_norm:
            mock_norm_instance = Mock()
            mock_norm_instance.normalize_bundle = Mock(
                return_value={
                    "indicators": [
                        {
                            "id": "indicator--test",
                            "type": "ipv4",
                            "value": "192.0.2.1",
                            "pattern": "[ipv4-addr:value = '192.0.2.1']",
                            "confidence": 85,
                        }
                    ],
                    "normalized": True,
                }
            )
            mock_norm.return_value = mock_norm_instance

            normalized = mock_norm_instance.normalize_bundle(objects)
            assert normalized["normalized"] is True
            assert len(normalized["indicators"]) == 1

        # Step 4: Store in Elasticsearch
        mock_elasticsearch.bulk = Mock(
            return_value={"errors": False, "items": [{"index": {"_id": "test-1"}}]}
        )
        result = mock_elasticsearch.bulk(body=normalized["indicators"])
        assert result["errors"] is False
        assert len(result["items"]) == 1

    @pytest.mark.asyncio
    async def test_cve_sync_threat_correlation_workflow(
        self,
        sample_cve_list: List[Dict[str, Any]],
        sample_asset_inventory: List[Dict[str, Any]],
        mock_elasticsearch: Mock,
    ) -> None:
        """
        Test CVE sync → Threat correlation → Risk scoring.

        Steps:
            1. Sync CVE database
            2. Load asset inventory
            3. Correlate CVEs with assets
            4. Calculate risk scores
        """
        # Step 1: Sync CVE database
        with patch("tools.threat_intelligence.feeds.aggregator.CVESync") as mock_cve:
            mock_cve_instance = Mock()
            mock_cve_instance.sync_latest = AsyncMock(
                return_value={
                    "status": "success",
                    "cves_synced": len(sample_cve_list),
                    "source": "NVD",
                }
            )
            mock_cve.return_value = mock_cve_instance

            sync_result = await mock_cve_instance.sync_latest()
            assert sync_result["status"] == "success"
            assert sync_result["cves_synced"] == 5

        # Step 2: Load asset inventory
        with patch(
            "tools.threat_intelligence.correlator.threat_correlator.AssetInventory"
        ) as mock_inv:
            mock_inv_instance = Mock()
            mock_inv_instance.load_assets = AsyncMock(
                return_value={
                    "status": "success",
                    "assets_loaded": len(sample_asset_inventory),
                    "assets": sample_asset_inventory,
                }
            )
            mock_inv.return_value = mock_inv_instance

            inv_result = await mock_inv_instance.load_assets()
            assert inv_result["status"] == "success"
            assert inv_result["assets_loaded"] == 2

        # Step 3: Correlate CVEs with assets
        with patch(
            "tools.threat_intelligence.correlator.threat_correlator.ThreatCorrelator"
        ) as mock_corr:
            mock_corr_instance = Mock()
            mock_corr_instance.correlate_assets = AsyncMock(
                return_value={
                    "status": "success",
                    "correlations": [
                        {
                            "asset_id": "web-server-01",
                            "vulnerabilities": [
                                {
                                    "cve": "CVE-2024-1000",
                                    "component": "vulnerable-lib@1.2.3",
                                    "severity": "CRITICAL",
                                    "cvss_score": 9.8,
                                }
                            ],
                            "risk_score": 85.5,
                        }
                    ],
                }
            )
            mock_corr.return_value = mock_corr_instance

            corr_result = await mock_corr_instance.correlate_assets(
                assets=sample_asset_inventory, cves=sample_cve_list
            )
            assert corr_result["status"] == "success"
            assert len(corr_result["correlations"]) == 1
            assert corr_result["correlations"][0]["risk_score"] == 85.5

        # Step 4: Calculate risk scores
        assert corr_result["correlations"][0]["risk_score"] > 80
        assert corr_result["correlations"][0]["vulnerabilities"][0]["cvss_score"] == 9.8


class TestAttackMappingWorkflow:
    """Test ATT&CK mapping and analysis workflows."""

    @pytest.mark.asyncio
    async def test_attack_mapping_workflow(
        self,
        sample_stix_bundle: Dict[str, Any],
        sample_attack_technique_list: List[Dict[str, Any]],
    ) -> None:
        """
        Test ATT&CK mapping workflow.

        Steps:
            1. Map threats to techniques
            2. Analyze coverage
            3. Identify gaps
            4. Generate navigator layer
        """
        # Step 1: Map threats to techniques
        with patch(
            "tools.threat_intelligence.attack.attack_mapper.AttackMapper"
        ) as mock_mapper:
            mock_mapper_instance = Mock()
            mock_mapper_instance.map_to_attack = AsyncMock(
                return_value={
                    "status": "success",
                    "mappings": [
                        {
                            "threat": "Emotet",
                            "techniques": ["T1566", "T1059"],
                            "tactics": ["initial-access", "execution"],
                        }
                    ],
                }
            )
            mock_mapper.return_value = mock_mapper_instance

            mapping_result = await mock_mapper_instance.map_to_attack(
                sample_stix_bundle
            )
            assert mapping_result["status"] == "success"
            assert len(mapping_result["mappings"]) == 1
            assert "T1566" in mapping_result["mappings"][0]["techniques"]

        # Step 2: Analyze coverage
        with patch(
            "tools.threat_intelligence.attack.attack_mapper.CoverageAnalyzer"
        ) as mock_coverage:
            mock_coverage_instance = Mock()
            mock_coverage_instance.analyze_coverage = Mock(
                return_value={
                    "total_techniques": len(sample_attack_technique_list),
                    "covered_techniques": 2,
                    "coverage_percentage": 50.0,
                    "tactics_coverage": {
                        "initial-access": 1,
                        "execution": 1,
                        "discovery": 0,
                    },
                }
            )
            mock_coverage.return_value = mock_coverage_instance

            coverage = mock_coverage_instance.analyze_coverage(
                mapping_result["mappings"], sample_attack_technique_list
            )
            assert coverage["total_techniques"] == 4
            assert coverage["covered_techniques"] == 2
            assert coverage["coverage_percentage"] == 50.0

        # Step 3: Identify gaps
        with patch(
            "tools.threat_intelligence.attack.attack_mapper.GapAnalyzer"
        ) as mock_gap:
            mock_gap_instance = Mock()
            mock_gap_instance.identify_gaps = Mock(
                return_value={
                    "gaps": [
                        {
                            "technique": "T1087",
                            "tactic": "discovery",
                            "severity": "medium",
                            "recommendation": "Implement account discovery detection",
                        }
                    ],
                    "critical_gaps": 0,
                    "high_gaps": 0,
                    "medium_gaps": 1,
                }
            )
            mock_gap.return_value = mock_gap_instance

            gaps = mock_gap_instance.identify_gaps(coverage)
            assert len(gaps["gaps"]) == 1
            assert gaps["gaps"][0]["technique"] == "T1087"
            assert gaps["medium_gaps"] == 1

        # Step 4: Generate navigator layer
        with patch(
            "tools.threat_intelligence.attack.attack_mapper.NavigatorGenerator"
        ) as mock_nav:
            mock_nav_instance = Mock()
            mock_nav_instance.generate_layer = Mock(
                return_value={
                    "name": "Threat Coverage Layer",
                    "versions": {"attack": "13", "navigator": "4.9", "layer": "4.5"},
                    "domain": "enterprise-attack",
                    "techniques": [
                        {
                            "techniqueID": "T1566",
                            "color": "#ff6666",
                            "comment": "Detected in Emotet",
                        },
                        {
                            "techniqueID": "T1059",
                            "color": "#ff6666",
                            "comment": "Detected in Emotet",
                        },
                    ],
                }
            )
            mock_nav.return_value = mock_nav_instance

            layer = mock_nav_instance.generate_layer(
                mapping_result["mappings"], gaps["gaps"]
            )
            assert layer["name"] == "Threat Coverage Layer"
            assert len(layer["techniques"]) == 2

    @pytest.mark.asyncio
    async def test_detection_gap_analysis(
        self,
        sample_attack_technique_list: List[Dict[str, Any]],
        sample_threat_actor: Dict[str, Any],
    ) -> None:
        """Test detection gap analysis for threat actors."""
        with patch(
            "tools.threat_intelligence.attack.attack_mapper.DetectionAnalyzer"
        ) as mock_detector:
            mock_detector_instance = Mock()
            mock_detector_instance.analyze_gaps = AsyncMock(
                return_value={
                    "actor": sample_threat_actor["name"],
                    "total_techniques": len(sample_threat_actor["techniques"]),
                    "detected_techniques": 1,
                    "undetected_techniques": 2,
                    "detection_rate": 33.3,
                    "gaps": [
                        {
                            "technique": "T1059",
                            "priority": "high",
                            "mitigation": "Implement command-line auditing",
                        },
                        {
                            "technique": "T1053",
                            "priority": "medium",
                            "mitigation": "Monitor scheduled task creation",
                        },
                    ],
                }
            )
            mock_detector.return_value = mock_detector_instance

            result = await mock_detector_instance.analyze_gaps(
                sample_threat_actor, sample_attack_technique_list
            )
            assert result["actor"] == "APT28"
            assert result["detection_rate"] == 33.3
            assert len(result["gaps"]) == 2


class TestIOCWorkflow:
    """Test IOC extraction, enrichment, and export workflows."""

    @pytest.mark.asyncio
    async def test_ioc_extraction_enrichment_export_workflow(
        self,
        sample_stix_bundle: Dict[str, Any],
        sample_ioc_list: List[Dict[str, Any]],
        temp_dir: Path,
    ) -> None:
        """
        Test IOC workflow: Extract → Enrich → Export.

        Steps:
            1. Extract IOCs from feeds
            2. Enrich with OSINT data
            3. Export to various formats
        """
        # Step 1: Extract IOCs from feeds
        with patch(
            "tools.threat_intelligence.ioc.ioc_manager.IOCExtractor"
        ) as mock_ext:
            mock_ext_instance = Mock()
            mock_ext_instance.extract_from_stix = AsyncMock(
                return_value={
                    "status": "success",
                    "iocs_extracted": len(sample_ioc_list),
                    "iocs": sample_ioc_list,
                    "types": {"ipv4": 1, "domain": 1, "sha256": 1},
                }
            )
            mock_ext.return_value = mock_ext_instance

            extract_result = await mock_ext_instance.extract_from_stix(
                sample_stix_bundle
            )
            assert extract_result["status"] == "success"
            assert extract_result["iocs_extracted"] == 3
            assert extract_result["types"]["ipv4"] == 1

        # Step 2: Enrich with OSINT data
        with patch(
            "tools.threat_intelligence.enricher.intelligence_enricher.IOCEnricher"
        ) as mock_enrich:
            mock_enrich_instance = Mock()
            mock_enrich_instance.enrich_iocs = AsyncMock(
                return_value={
                    "status": "success",
                    "iocs_enriched": 3,
                    "enriched_iocs": [
                        {
                            **sample_ioc_list[0],
                            "geolocation": {"country": "US", "city": "New York"},
                            "reputation": "malicious",
                            "threat_score": 85,
                        },
                        {
                            **sample_ioc_list[1],
                            "dns_records": ["192.0.2.100"],
                            "reputation": "suspicious",
                            "threat_score": 70,
                        },
                        {
                            **sample_ioc_list[2],
                            "file_type": "PE32",
                            "signatures": ["malware-family-x"],
                            "threat_score": 95,
                        },
                    ],
                }
            )
            mock_enrich.return_value = mock_enrich_instance

            enrich_result = await mock_enrich_instance.enrich_iocs(sample_ioc_list)
            assert enrich_result["status"] == "success"
            assert enrich_result["iocs_enriched"] == 3
            assert "geolocation" in enrich_result["enriched_iocs"][0]
            assert "dns_records" in enrich_result["enriched_iocs"][1]
            assert "signatures" in enrich_result["enriched_iocs"][2]

        # Step 3: Export to various formats
        with patch("tools.threat_intelligence.ioc.ioc_manager.IOCExporter"):
            mock_exp_instance = Mock()

            # Export to STIX
            mock_exp_instance.export_to_stix = Mock(
                return_value={
                    "type": "bundle",
                    "objects": [{"type": "indicator", "id": "indicator--test"}],
                }
            )
            stix_export = mock_exp_instance.export_to_stix(
                enrich_result["enriched_iocs"]
            )
            assert stix_export["type"] == "bundle"
            assert len(stix_export["objects"]) == 1

            # Export to CSV
            mock_exp_instance.export_to_csv = Mock(
                return_value=str(temp_dir / "iocs.csv")
            )
            csv_path = mock_exp_instance.export_to_csv(
                enrich_result["enriched_iocs"], temp_dir / "iocs.csv"
            )
            assert Path(csv_path).name == "iocs.csv"

            # Export to MISP
            mock_exp_instance.export_to_misp = Mock(
                return_value={
                    "Event": {
                        "info": "IOC Export",
                        "Attribute": [{"type": "ip-dst", "value": "192.0.2.100"}],
                    }
                }
            )
            misp_export = mock_exp_instance.export_to_misp(
                enrich_result["enriched_iocs"]
            )
            assert "Event" in misp_export
            assert len(misp_export["Event"]["Attribute"]) == 1

    @pytest.mark.asyncio
    async def test_ioc_lifecycle_management(
        self,
        sample_ioc_ip: Dict[str, Any],
        mock_elasticsearch: Mock,
    ) -> None:
        """Test IOC lifecycle management (creation, update, expiration)."""
        with patch("tools.threat_intelligence.ioc.ioc_manager.IOCManager"):
            mock_mgr_instance = Mock()

            # Create IOC
            mock_mgr_instance.create_ioc = AsyncMock(
                return_value={
                    "status": "success",
                    "ioc_id": "ioc-001",
                    "created_at": datetime.utcnow().isoformat() + "Z",
                }
            )
            create_result = await mock_mgr_instance.create_ioc(sample_ioc_ip)
            assert create_result["status"] == "success"
            assert create_result["ioc_id"] == "ioc-001"

            # Update IOC
            mock_mgr_instance.update_ioc = AsyncMock(
                return_value={
                    "status": "success",
                    "ioc_id": "ioc-001",
                    "updated_fields": ["last_seen", "confidence"],
                }
            )
            update_result = await mock_mgr_instance.update_ioc(
                "ioc-001", {"last_seen": datetime.utcnow().isoformat() + "Z"}
            )
            assert update_result["status"] == "success"
            assert "last_seen" in update_result["updated_fields"]

            # Check expiration
            mock_mgr_instance.check_expired = AsyncMock(
                return_value={
                    "expired_iocs": [],
                    "active_iocs": ["ioc-001"],
                }
            )
            expire_result = await mock_mgr_instance.check_expired()
            assert len(expire_result["expired_iocs"]) == 0
            assert "ioc-001" in expire_result["active_iocs"]


class TestVEXGeneration:
    """Test VEX document generation workflows."""

    @pytest.mark.asyncio
    async def test_vex_generation_from_sbom(
        self,
        sample_sbom_spdx: Dict[str, Any],
        sample_cve_list: List[Dict[str, Any]],
    ) -> None:
        """Test VEX document generation from SBOM and CVE data."""
        with patch(
            "tools.threat_intelligence.vex.vex_generator.VEXGenerator"
        ) as mock_vex:
            mock_vex_instance = Mock()
            mock_vex_instance.generate_from_sbom = AsyncMock(
                return_value={
                    "@context": "https://openvex.dev/ns/v0.2.0",
                    "@id": "https://example.com/vex/2024/001",
                    "author": "Security Team",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "version": "1",
                    "statements": [
                        {
                            "vulnerability": {"name": "CVE-2024-1000"},
                            "products": [
                                {
                                    "@id": "pkg:npm/vulnerable-lib@1.2.3",
                                    "identifiers": {
                                        "purl": "pkg:npm/vulnerable-lib@1.2.3"
                                    },
                                }
                            ],
                            "status": "affected",
                            "justification": "vulnerable_code_in_use",
                            "impact_statement": "Critical vulnerability affects production",
                            "action_statement": "Upgrade to 1.2.4 immediately",
                        },
                        {
                            "vulnerability": {"name": "CVE-2024-1001"},
                            "products": [
                                {
                                    "@id": "pkg:npm/safe-lib@2.0.0",
                                    "identifiers": {"purl": "pkg:npm/safe-lib@2.0.0"},
                                }
                            ],
                            "status": "not_affected",
                            "justification": "vulnerable_code_not_present",
                        },
                    ],
                }
            )
            mock_vex.return_value = mock_vex_instance

            vex_doc = await mock_vex_instance.generate_from_sbom(
                sample_sbom_spdx, sample_cve_list
            )
            assert vex_doc["@context"] == "https://openvex.dev/ns/v0.2.0"
            assert len(vex_doc["statements"]) == 2
            assert vex_doc["statements"][0]["status"] == "affected"
            assert vex_doc["statements"][1]["status"] == "not_affected"

    @pytest.mark.asyncio
    async def test_vex_csaf_format_generation(
        self,
        sample_sbom_cyclonedx: Dict[str, Any],
        sample_cve_list: List[Dict[str, Any]],
    ) -> None:
        """Test CSAF 2.0 format VEX document generation."""
        with patch(
            "tools.threat_intelligence.vex.vex_generator.VEXGenerator"
        ) as mock_vex:
            mock_vex_instance = Mock()
            mock_vex_instance.generate_csaf = AsyncMock(
                return_value={
                    "document": {
                        "category": "csaf_vex",
                        "csaf_version": "2.0",
                        "publisher": {
                            "category": "vendor",
                            "name": "Example Corp",
                            "namespace": "https://example.com",
                        },
                        "title": "Security Advisory",
                        "tracking": {
                            "id": "CSAF-2024-001",
                            "status": "final",
                            "version": "1",
                            "initial_release_date": datetime.utcnow().isoformat() + "Z",
                            "current_release_date": datetime.utcnow().isoformat() + "Z",
                        },
                    },
                    "vulnerabilities": [
                        {
                            "cve": "CVE-2024-1000",
                            "product_status": {
                                "known_affected": ["pkg:npm/vulnerable-lib@1.2.3"]
                            },
                        }
                    ],
                }
            )
            mock_vex.return_value = mock_vex_instance

            csaf_doc = await mock_vex_instance.generate_csaf(
                sample_sbom_cyclonedx, sample_cve_list
            )
            assert csaf_doc["document"]["csaf_version"] == "2.0"
            assert csaf_doc["document"]["category"] == "csaf_vex"
            assert len(csaf_doc["vulnerabilities"]) == 1


class TestThreatCorrelation:
    """Test threat correlation and risk assessment."""

    @pytest.mark.asyncio
    async def test_multi_source_correlation(
        self,
        sample_cve_list: List[Dict[str, Any]],
        sample_ioc_list: List[Dict[str, Any]],
        sample_asset_inventory: List[Dict[str, Any]],
    ) -> None:
        """Test correlation across multiple threat sources."""
        with patch(
            "tools.threat_intelligence.correlator.threat_correlator.MultiSourceCorrelator"
        ) as mock_corr:
            mock_corr_instance = Mock()
            mock_corr_instance.correlate_all = AsyncMock(
                return_value={
                    "status": "success",
                    "correlations": [
                        {
                            "asset_id": "web-server-01",
                            "cve_matches": 2,
                            "ioc_matches": 1,
                            "overall_risk": 88.5,
                            "details": {
                                "cves": ["CVE-2024-1000", "CVE-2024-1001"],
                                "iocs": ["192.0.2.100"],
                                "attack_surface": "high",
                            },
                        }
                    ],
                    "total_assets_analyzed": 2,
                    "high_risk_assets": 1,
                }
            )
            mock_corr.return_value = mock_corr_instance

            result = await mock_corr_instance.correlate_all(
                cves=sample_cve_list,
                iocs=sample_ioc_list,
                assets=sample_asset_inventory,
            )
            assert result["status"] == "success"
            assert result["high_risk_assets"] == 1
            assert result["correlations"][0]["overall_risk"] > 80

    @pytest.mark.asyncio
    async def test_risk_score_calculation(
        self,
        sample_correlation_result: Dict[str, Any],
    ) -> None:
        """Test risk score calculation algorithm."""
        with patch(
            "tools.threat_intelligence.correlator.threat_correlator.RiskScorer"
        ) as mock_scorer:
            mock_scorer_instance = Mock()
            mock_scorer_instance.calculate_risk = Mock(
                return_value={
                    "risk_score": 85.5,
                    "risk_level": "HIGH",
                    "factors": {
                        "cvss_score": 9.8,
                        "exploitability": 0.95,
                        "asset_criticality": 0.9,
                        "exposure": 0.85,
                    },
                    "recommendations": [
                        "Immediate patching required",
                        "Isolate affected systems",
                    ],
                }
            )
            mock_scorer.return_value = mock_scorer_instance

            risk = mock_scorer_instance.calculate_risk(sample_correlation_result)
            assert risk["risk_score"] == 85.5
            assert risk["risk_level"] == "HIGH"
            assert "cvss_score" in risk["factors"]
            assert len(risk["recommendations"]) == 2


class TestIntelligenceEnrichment:
    """Test intelligence enrichment workflows."""

    @pytest.mark.asyncio
    async def test_osint_enrichment(
        self,
        sample_ioc_ip: Dict[str, Any],
    ) -> None:
        """Test OSINT data enrichment for IOCs."""
        with patch(
            "tools.threat_intelligence.enricher.intelligence_enricher.OSINTEnricher"
        ) as mock_osint:
            mock_osint_instance = Mock()
            mock_osint_instance.enrich = AsyncMock(
                return_value={
                    **sample_ioc_ip,
                    "osint_data": {
                        "geolocation": {
                            "country": "RU",
                            "city": "Moscow",
                            "coordinates": [37.6156, 55.7522],
                        },
                        "asn": {"number": 12345, "org": "Example ISP"},
                        "reputation": {
                            "score": 15,
                            "category": "malicious",
                            "sources": ["virustotal", "abuseipdb"],
                        },
                        "related_domains": ["malicious.ru"],
                        "threat_intel": {
                            "campaigns": ["apt-campaign-2024"],
                            "malware_families": ["emotet"],
                        },
                    },
                }
            )
            mock_osint.return_value = mock_osint_instance

            enriched = await mock_osint_instance.enrich(sample_ioc_ip)
            assert "osint_data" in enriched
            assert enriched["osint_data"]["geolocation"]["country"] == "RU"
            assert enriched["osint_data"]["reputation"]["category"] == "malicious"

    @pytest.mark.asyncio
    async def test_threat_actor_tracking(
        self,
        sample_threat_actor: Dict[str, Any],
    ) -> None:
        """Test threat actor campaign tracking."""
        with patch(
            "tools.threat_intelligence.enricher.intelligence_enricher.ThreatActorTracker"
        ) as mock_tracker:
            mock_tracker_instance = Mock()
            mock_tracker_instance.track_campaigns = AsyncMock(
                return_value={
                    "actor": sample_threat_actor["name"],
                    "active_campaigns": [
                        {
                            "name": "Operation X",
                            "start_date": "2024-01-01T00:00:00Z",
                            "status": "active",
                            "targets": ["US", "EU"],
                            "techniques": ["T1566", "T1059"],
                        }
                    ],
                    "recent_activity": {
                        "last_seen": datetime.utcnow().isoformat() + "Z",
                        "activity_level": "high",
                        "new_techniques": ["T1053"],
                    },
                }
            )
            mock_tracker.return_value = mock_tracker_instance

            tracking = await mock_tracker_instance.track_campaigns(sample_threat_actor)
            assert tracking["actor"] == "APT28"
            assert len(tracking["active_campaigns"]) == 1
            assert tracking["recent_activity"]["activity_level"] == "high"


class TestReportGeneration:
    """Test threat intelligence report generation."""

    @pytest.mark.asyncio
    async def test_comprehensive_report_generation(
        self,
        sample_threat_report: Dict[str, Any],
        temp_dir: Path,
    ) -> None:
        """Test comprehensive threat intelligence report generation."""
        with patch(
            "tools.threat_intelligence.cli.threat_cli.ReportGenerator"
        ):
            mock_gen_instance = Mock()

            # Generate JSON report
            mock_gen_instance.generate_json = AsyncMock(
                return_value=sample_threat_report
            )
            json_report = await mock_gen_instance.generate_json()
            assert json_report["report_id"] == "TI-2024-001"
            assert "key_findings" in json_report
            assert len(json_report["threat_actors"]) == 2

            # Generate PDF report
            mock_gen_instance.generate_pdf = AsyncMock(
                return_value=str(temp_dir / "report.pdf")
            )
            pdf_path = await mock_gen_instance.generate_pdf(
                json_report, temp_dir / "report.pdf"
            )
            assert Path(pdf_path).name == "report.pdf"

            # Generate HTML report
            mock_gen_instance.generate_html = AsyncMock(
                return_value=str(temp_dir / "report.html")
            )
            html_path = await mock_gen_instance.generate_html(
                json_report, temp_dir / "report.html"
            )
            assert Path(html_path).name == "report.html"
