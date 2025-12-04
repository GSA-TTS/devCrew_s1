"""
Pytest configuration and shared fixtures for threat intelligence tests.

This module provides:
- Database fixtures for testing
- Mock data generators
- Shared test utilities
- Async testing support
- Performance benchmarking setup
"""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, List
from unittest.mock import Mock

import pytest
from elasticsearch import AsyncElasticsearch


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_elasticsearch(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mock Elasticsearch client."""
    mock_es = Mock(spec=AsyncElasticsearch)
    mock_es.search = Mock(return_value={"hits": {"hits": [], "total": {"value": 0}}})
    mock_es.index = Mock(return_value={"result": "created", "_id": "test-id"})
    mock_es.bulk = Mock(return_value={"errors": False, "items": []})
    mock_es.get = Mock(return_value={"_source": {}, "found": True, "_id": "test-id"})
    return mock_es


@pytest.fixture
def sample_stix_indicator() -> Dict[str, Any]:
    """Generate sample STIX indicator object."""
    return {
        "type": "indicator",
        "spec_version": "2.1",
        "id": "indicator--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
        "created": datetime.utcnow().isoformat() + "Z",
        "modified": datetime.utcnow().isoformat() + "Z",
        "name": "Malicious IP Address",
        "description": "IP address associated with malware C2",
        "indicator_types": ["malicious-activity"],
        "pattern": "[ipv4-addr:value = '192.0.2.1']",
        "pattern_type": "stix",
        "valid_from": datetime.utcnow().isoformat() + "Z",
        "labels": ["malicious-activity"],
        "confidence": 85,
    }


@pytest.fixture
def sample_stix_malware() -> Dict[str, Any]:
    """Generate sample STIX malware object."""
    return {
        "type": "malware",
        "spec_version": "2.1",
        "id": "malware--92a78b87-6b9e-4b36-9c8d-9c6a3c4a7e3f",
        "created": datetime.utcnow().isoformat() + "Z",
        "modified": datetime.utcnow().isoformat() + "Z",
        "name": "Emotet",
        "description": "Banking trojan and malware loader",
        "malware_types": ["trojan", "backdoor"],
        "is_family": True,
        "labels": ["malware"],
    }


@pytest.fixture
def sample_stix_bundle(
    sample_stix_indicator: Dict[str, Any], sample_stix_malware: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate sample STIX bundle with multiple objects."""
    return {
        "type": "bundle",
        "id": "bundle--44af6c39-c09b-49c5-9de2-394224b04982",
        "objects": [
            sample_stix_indicator,
            sample_stix_malware,
            {
                "type": "relationship",
                "spec_version": "2.1",
                "id": "relationship--44af6c39-c09b-49c5-9de2-394224b04982",
                "created": datetime.utcnow().isoformat() + "Z",
                "modified": datetime.utcnow().isoformat() + "Z",
                "relationship_type": "indicates",
                "source_ref": sample_stix_indicator["id"],
                "target_ref": sample_stix_malware["id"],
            },
        ],
    }


@pytest.fixture
def sample_cve_data() -> Dict[str, Any]:
    """Generate sample CVE data."""
    return {
        "cve_id": "CVE-2024-1234",
        "description": "Remote code execution vulnerability in Example Software",
        "published_date": "2024-01-15T00:00:00Z",
        "last_modified": "2024-01-20T00:00:00Z",
        "cvss_v3_score": 9.8,
        "cvss_v3_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        "severity": "CRITICAL",
        "cwe_ids": ["CWE-94"],
        "references": [
            {"url": "https://example.com/advisory", "source": "vendor"},
            {"url": "https://nvd.nist.gov/vuln/detail/CVE-2024-1234", "source": "NVD"},
        ],
        "affected_products": [
            {
                "vendor": "Example Corp",
                "product": "Example Software",
                "versions": ["1.0", "1.1", "1.2"],
            }
        ],
    }


@pytest.fixture
def sample_cve_list() -> List[Dict[str, Any]]:
    """Generate list of sample CVE records."""
    cves = []
    for i in range(5):
        cves.append(
            {
                "cve_id": f"CVE-2024-{1000 + i}",
                "description": f"Vulnerability {i} in test software",
                "published_date": (datetime.utcnow() - timedelta(days=i)).isoformat()
                + "Z",
                "cvss_v3_score": 7.5 + (i * 0.5),
                "severity": "HIGH" if i < 3 else "CRITICAL",
                "cwe_ids": [f"CWE-{79 + i}"],
                "affected_products": [
                    {
                        "vendor": "TestVendor",
                        "product": f"Product-{i}",
                        "versions": ["*"],
                    }
                ],
            }
        )
    return cves


@pytest.fixture
def sample_ioc_ip() -> Dict[str, Any]:
    """Generate sample IP IOC."""
    return {
        "type": "ipv4",
        "value": "192.0.2.100",
        "first_seen": datetime.utcnow().isoformat() + "Z",
        "last_seen": datetime.utcnow().isoformat() + "Z",
        "confidence": 90,
        "tags": ["malware", "c2"],
        "source": "threat-feed-1",
        "threat_types": ["malicious-activity"],
    }


@pytest.fixture
def sample_ioc_domain() -> Dict[str, Any]:
    """Generate sample domain IOC."""
    return {
        "type": "domain",
        "value": "malicious.example.com",
        "first_seen": datetime.utcnow().isoformat() + "Z",
        "last_seen": datetime.utcnow().isoformat() + "Z",
        "confidence": 85,
        "tags": ["phishing", "malware"],
        "source": "threat-feed-2",
        "threat_types": ["phishing"],
    }


@pytest.fixture
def sample_ioc_hash() -> Dict[str, Any]:
    """Generate sample file hash IOC."""
    return {
        "type": "sha256",
        "value": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "first_seen": datetime.utcnow().isoformat() + "Z",
        "last_seen": datetime.utcnow().isoformat() + "Z",
        "confidence": 95,
        "tags": ["malware", "ransomware"],
        "source": "threat-feed-3",
        "threat_types": ["malicious-activity"],
        "file_name": "malware.exe",
        "file_size": 102400,
    }


@pytest.fixture
def sample_ioc_list(
    sample_ioc_ip: Dict[str, Any],
    sample_ioc_domain: Dict[str, Any],
    sample_ioc_hash: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate list of IOCs."""
    return [sample_ioc_ip, sample_ioc_domain, sample_ioc_hash]


@pytest.fixture
def sample_sbom_spdx() -> Dict[str, Any]:
    """Generate sample SPDX SBOM."""
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "example-application",
        "documentNamespace": "https://example.com/spdx/example-app-1.0",
        "creationInfo": {
            "created": datetime.utcnow().isoformat() + "Z",
            "creators": ["Tool: example-scanner-1.0"],
        },
        "packages": [
            {
                "SPDXID": "SPDXRef-Package-1",
                "name": "vulnerable-lib",
                "versionInfo": "1.2.3",
                "supplier": "Organization: Example Corp",
                "downloadLocation": "https://example.com/vulnerable-lib-1.2.3.tar.gz",
                "filesAnalyzed": False,
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": "pkg:npm/vulnerable-lib@1.2.3",
                    }
                ],
            },
            {
                "SPDXID": "SPDXRef-Package-2",
                "name": "safe-lib",
                "versionInfo": "2.0.0",
                "supplier": "Organization: Example Corp",
                "downloadLocation": "https://example.com/safe-lib-2.0.0.tar.gz",
                "filesAnalyzed": False,
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": "pkg:npm/safe-lib@2.0.0",
                    }
                ],
            },
        ],
    }


@pytest.fixture
def sample_sbom_cyclonedx() -> Dict[str, Any]:
    """Generate sample CycloneDX SBOM."""
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
        "version": 1,
        "metadata": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tools": [{"name": "example-scanner", "version": "1.0.0"}],
            "component": {
                "type": "application",
                "name": "example-application",
                "version": "1.0.0",
            },
        },
        "components": [
            {
                "type": "library",
                "name": "vulnerable-lib",
                "version": "1.2.3",
                "purl": "pkg:npm/vulnerable-lib@1.2.3",
                "bom-ref": "pkg:npm/vulnerable-lib@1.2.3",
            },
            {
                "type": "library",
                "name": "safe-lib",
                "version": "2.0.0",
                "purl": "pkg:npm/safe-lib@2.0.0",
                "bom-ref": "pkg:npm/safe-lib@2.0.0",
            },
        ],
    }


@pytest.fixture
def sample_attack_technique() -> Dict[str, Any]:
    """Generate sample ATT&CK technique."""
    return {
        "id": "T1566",
        "name": "Phishing",
        "description": "Adversaries may send phishing messages to gain access",
        "tactics": ["initial-access"],
        "platforms": ["Linux", "macOS", "Windows"],
        "data_sources": [
            "Application Log: Application Log Content",
            "Network Traffic: Network Traffic Content",
        ],
        "detection": "Network and/or mail server analysis",
        "url": "https://attack.mitre.org/techniques/T1566",
    }


@pytest.fixture
def sample_attack_technique_list() -> List[Dict[str, Any]]:
    """Generate list of ATT&CK techniques."""
    return [
        {
            "id": "T1566",
            "name": "Phishing",
            "tactics": ["initial-access"],
            "platforms": ["Linux", "macOS", "Windows"],
        },
        {
            "id": "T1059",
            "name": "Command and Scripting Interpreter",
            "tactics": ["execution"],
            "platforms": ["Linux", "macOS", "Windows"],
        },
        {
            "id": "T1053",
            "name": "Scheduled Task/Job",
            "tactics": ["execution", "persistence", "privilege-escalation"],
            "platforms": ["Windows", "Linux", "macOS"],
        },
        {
            "id": "T1087",
            "name": "Account Discovery",
            "tactics": ["discovery"],
            "platforms": ["Linux", "macOS", "Windows", "Azure AD"],
        },
    ]


@pytest.fixture
def sample_threat_actor() -> Dict[str, Any]:
    """Generate sample threat actor data."""
    return {
        "id": "threat-actor--8e2e2d2b-17d4-4cbf-938f-98ee46b3cd3f",
        "name": "APT28",
        "aliases": ["Fancy Bear", "Sofacy", "Sednit"],
        "description": "Russian cyber espionage group",
        "first_seen": "2007-01-01T00:00:00Z",
        "sophistication": "advanced",
        "resource_level": "government",
        "primary_motivation": "organizational-gain",
        "goals": ["intelligence gathering", "geopolitical influence"],
        "targeted_countries": ["US", "EU", "NATO"],
        "targeted_sectors": ["government", "military", "defense"],
        "techniques": ["T1566", "T1059", "T1053"],
    }


@pytest.fixture
def sample_vex_document() -> Dict[str, Any]:
    """Generate sample VEX document."""
    return {
        "@context": "https://openvex.dev/ns/v0.2.0",
        "@id": "https://example.com/vex/2024/001",
        "author": "Example Security Team",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1",
        "statements": [
            {
                "vulnerability": {
                    "name": "CVE-2024-1234",
                    "description": "Remote code execution vulnerability",
                },
                "products": [
                    {
                        "@id": "pkg:npm/vulnerable-lib@1.2.3",
                        "identifiers": {"purl": "pkg:npm/vulnerable-lib@1.2.3"},
                    }
                ],
                "status": "affected",
                "justification": "vulnerable_code_in_use",
                "impact_statement": "This vulnerability affects our production systems",
                "action_statement": "Upgrade to version 1.2.4 or apply patch",
            },
            {
                "vulnerability": {
                    "name": "CVE-2024-5678",
                    "description": "SQL injection vulnerability",
                },
                "products": [
                    {
                        "@id": "pkg:npm/safe-lib@2.0.0",
                        "identifiers": {"purl": "pkg:npm/safe-lib@2.0.0"},
                    }
                ],
                "status": "not_affected",
                "justification": "vulnerable_code_not_in_execute_path",
                "impact_statement": "Code path not used in our application",
            },
        ],
    }


@pytest.fixture
def sample_threat_report() -> Dict[str, Any]:
    """Generate sample threat intelligence report."""
    return {
        "report_id": "TI-2024-001",
        "title": "Q1 2024 Threat Intelligence Summary",
        "created": datetime.utcnow().isoformat() + "Z",
        "author": "Threat Intelligence Team",
        "tlp": "AMBER",
        "summary": "Summary of threat landscape for Q1 2024",
        "key_findings": [
            "Increase in ransomware attacks",
            "New phishing campaigns targeting finance sector",
            "Emergence of new APT group",
        ],
        "threat_actors": ["APT28", "APT29"],
        "malware_families": ["Emotet", "TrickBot"],
        "attack_vectors": ["phishing", "supply-chain"],
        "affected_sectors": ["finance", "healthcare", "government"],
        "iocs": {
            "ip_addresses": ["192.0.2.100", "192.0.2.101"],
            "domains": ["malicious.example.com", "phishing.example.org"],
            "file_hashes": [
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            ],
        },
        "mitre_attack_techniques": ["T1566", "T1059", "T1053"],
        "recommendations": [
            "Implement email security controls",
            "Update vulnerable software",
            "Monitor for IOCs",
        ],
    }


@pytest.fixture
def mock_taxii_server(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mock TAXII server responses."""
    mock_server = Mock()
    mock_server.get_collections = Mock(
        return_value=[
            {
                "id": "collection-1",
                "title": "Malware Indicators",
                "can_read": True,
                "can_write": False,
            }
        ]
    )
    mock_server.get_objects = Mock(
        return_value={
            "type": "bundle",
            "objects": [
                {
                    "type": "indicator",
                    "id": "indicator--test",
                    "pattern": "[ipv4-addr:value = '192.0.2.1']",
                }
            ],
        }
    )
    return mock_server


@pytest.fixture
def sample_asset_inventory() -> List[Dict[str, Any]]:
    """Generate sample asset inventory."""
    return [
        {
            "asset_id": "web-server-01",
            "type": "server",
            "hostname": "web01.example.com",
            "ip_address": "10.0.1.10",
            "os": "Ubuntu 22.04",
            "services": [
                {"name": "nginx", "version": "1.18.0", "port": 80},
                {"name": "postgresql", "version": "14.5", "port": 5432},
            ],
            "software": [
                {"name": "vulnerable-lib", "version": "1.2.3"},
                {"name": "safe-lib", "version": "2.0.0"},
            ],
            "criticality": "high",
            "location": "datacenter-1",
        },
        {
            "asset_id": "db-server-01",
            "type": "server",
            "hostname": "db01.example.com",
            "ip_address": "10.0.1.20",
            "os": "Red Hat Enterprise Linux 8",
            "services": [
                {"name": "mysql", "version": "8.0.30", "port": 3306},
            ],
            "software": [
                {"name": "openssl", "version": "1.1.1k"},
            ],
            "criticality": "critical",
            "location": "datacenter-1",
        },
    ]


@pytest.fixture
def sample_correlation_result() -> Dict[str, Any]:
    """Generate sample threat correlation result."""
    return {
        "correlation_id": "corr-2024-001",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "asset_id": "web-server-01",
        "threats": [
            {
                "threat_id": "CVE-2024-1234",
                "type": "vulnerability",
                "severity": "CRITICAL",
                "cvss_score": 9.8,
                "affected_component": "vulnerable-lib@1.2.3",
                "exploitability": "high",
                "patch_available": True,
            }
        ],
        "risk_score": 85.5,
        "risk_level": "HIGH",
        "attack_surface": {
            "exposed_services": ["nginx:80", "postgresql:5432"],
            "vulnerable_components": ["vulnerable-lib@1.2.3"],
            "exploitable_paths": 3,
        },
        "recommendations": [
            "Upgrade vulnerable-lib to version 1.2.4",
            "Apply security patches for nginx",
            "Review firewall rules for exposed services",
        ],
    }


@pytest.fixture
def performance_test_data() -> Dict[str, Any]:
    """Generate performance test data."""
    return {
        "indicators": [
            {
                "type": "indicator",
                "id": f"indicator--{i:08d}-17d4-4cbf-938f-98ee46b3cd3f",
                "pattern": f"[ipv4-addr:value = '192.0.2.{i % 256}']",
            }
            for i in range(10000)
        ],
        "cves": [
            {
                "cve_id": f"CVE-2024-{10000 + i}",
                "cvss_v3_score": 5.0 + (i % 5),
                "severity": "MEDIUM",
            }
            for i in range(1000)
        ],
        "assets": [
            {
                "asset_id": f"asset-{i:06d}",
                "ip_address": f"10.0.{(i // 256) % 256}.{i % 256}",
            }
            for i in range(1000)
        ],
    }


@pytest.fixture
def config_file(temp_dir: Path) -> Path:
    """Create temporary configuration file."""
    config = {
        "elasticsearch": {
            "hosts": ["http://localhost:9200"],
            "index_prefix": "test-threat-intel",
        },
        "feeds": {
            "update_interval": 900,
            "enabled_feeds": ["test-feed"],
        },
        "correlation": {
            "risk_threshold": 70,
            "auto_remediate": False,
        },
        "performance": {
            "batch_size": 1000,
            "max_workers": 4,
        },
    }
    config_path = temp_dir / "threat-config.yaml"
    with open(config_path, "w") as f:
        import yaml

        yaml.safe_dump(config, f)
    return config_path


# Async fixtures
@pytest.fixture
async def async_mock_es() -> AsyncGenerator[Mock, None]:
    """Async Elasticsearch mock."""
    mock = Mock(spec=AsyncElasticsearch)
    mock.search = Mock(return_value={"hits": {"hits": [], "total": {"value": 0}}})
    yield mock
    # Cleanup if needed


# Performance testing helpers
@pytest.fixture
def benchmark_config() -> Dict[str, Any]:
    """Configuration for performance benchmarks."""
    return {
        "min_rounds": 5,
        "max_time": 10.0,
        "warmup": True,
        "warmup_iterations": 2,
    }
