# Threat Correlator Module

## Overview

The Threat Correlator module provides comprehensive vulnerability-to-threat matching and risk scoring capabilities for the Threat Intelligence Platform. It correlates CVE vulnerabilities with STIX threat intelligence, analyzes asset risk, processes SBOMs, and predicts exploit likelihood.

## Features

- **Vulnerability-to-Threat Matching**: Correlate CVE vulnerabilities with active STIX threat intelligence
- **Asset Risk Analysis**: Calculate risk scores for assets based on inventory and threat data
- **SBOM Analysis**: Analyze Software Bill of Materials (SPDX and CycloneDX formats) for threats
- **Risk Scoring Algorithm**: Calculate risk using Criticality × Likelihood × Exploitability
- **Exploit Prediction**: Predict likelihood of exploitation using EPSS, CVSS, and threat intelligence
- **Attack Surface Analysis**: Identify vulnerable components and exposure windows
- **Caching**: Built-in correlation and risk caching for performance optimization

## Installation

The module requires the following dependencies:

```bash
pip install pydantic>=2.0.0
```

## Quick Start

### Basic Correlation

```python
from threat_intelligence.correlator import ThreatCorrelator, CVE, STIXObject

# Initialize correlator
correlator = ThreatCorrelator({
    "cache_enabled": True,
    "cache_ttl": 3600,
    "min_correlation_score": 0.5
})

# Create CVE vulnerabilities
cves = [
    CVE(
        cve_id="CVE-2024-1234",
        cvss_score=9.8,
        exploit_available=True,
        epss_score=0.85
    )
]

# Create STIX threat objects
threats = [
    STIXObject(
        id="indicator--123",
        type="indicator",
        created="2024-01-01T00:00:00Z",
        modified="2024-01-01T00:00:00Z",
        labels=["exploit", "active-exploitation"],
        external_references=[
            {"source_name": "cve", "external_id": "CVE-2024-1234"}
        ]
    )
]

# Correlate vulnerabilities with threats
correlations = correlator.correlate_vulnerabilities(cves, threats)

for correlation in correlations:
    print(f"CVE: {correlation.cve_id}")
    print(f"Score: {correlation.correlation_score:.2f}")
    print(f"Active Exploitation: {correlation.active_exploitation}")
    print(f"Threat Actors: {correlation.threat_actors}")
```

### Asset Risk Analysis

```python
from threat_intelligence.correlator import Asset, ThreatIndicator

# Define assets
assets = [
    Asset(
        asset_id="asset-001",
        name="Production Server",
        type="server",
        ip_addresses=["10.0.1.100"],
        software=[
            {"name": "nginx", "version": "1.18.0"},
            {"name": "openssl", "version": "1.1.1"}
        ],
        criticality="CRITICAL"
    )
]

# Define threat indicators
threats = [
    ThreatIndicator(
        indicator_id="threat-001",
        type="cve",
        value="CVE-2024-1234",
        threat_type="exploit",
        confidence=0.9,
        severity="CRITICAL",
        first_seen="2024-01-01T00:00:00Z",
        last_seen="2024-01-15T00:00:00Z",
        tags=["remote-code-execution"]
    )
]

# Analyze asset risk
risk_assessments = correlator.analyze_asset_risk(assets, threats)

for risk in risk_assessments:
    print(f"Asset: {risk.asset_id}")
    print(f"Risk Score: {risk.risk_score:.1f}/100")
    print(f"Threats: {risk.threat_count} ({risk.critical_threats} critical)")
    print(f"Recommendations: {risk.recommendations}")
```

### SBOM Threat Analysis

```python
# SPDX format SBOM
sbom = {
    "spdxVersion": "SPDX-2.3",
    "SPDXID": "SPDXRef-DOCUMENT",
    "packages": [
        {
            "name": "log4j",
            "versionInfo": "2.14.1",
            "SPDXID": "SPDXRef-Package-log4j"
        },
        {
            "name": "spring-boot",
            "versionInfo": "2.5.0",
            "SPDXID": "SPDXRef-Package-spring"
        }
    ]
}

# Analyze SBOM for threats
analysis = correlator.analyze_sbom(sbom, threats)

print(f"Total Components: {analysis.total_components}")
print(f"Vulnerable: {analysis.vulnerable_components}")
print(f"Threat Exposure: {analysis.threat_exposure:.1f}/100")
print(f"Critical Vulnerabilities: {len(analysis.critical_vulns)}")
```

### Exploit Likelihood Prediction

```python
# Predict exploitation likelihood
likelihood = correlator.predict_exploit_likelihood(cves[0], threats)

print(f"Exploit Likelihood: {likelihood:.2%}")
```

## Risk Scoring Algorithm

The risk score is calculated using the formula:

```
Risk = Criticality × Likelihood × Exploitability × 10
```

Where:
- **Criticality**: Asset importance (1-10) based on criticality level
  - LOW: 2.5
  - MEDIUM: 5.0
  - HIGH: 7.5
  - CRITICAL: 10.0
- **Likelihood**: Threat presence (0-1) based on threat count and severity
- **Exploitability**: Average threat confidence (0-1)

The final score ranges from 0-100.

## Exploit Prediction Factors

The exploit likelihood prediction considers:

1. **EPSS Score**: Exploit Prediction Scoring System score (0-1)
2. **CVSS Score**: Common Vulnerability Scoring System (normalized to 0-1)
3. **Exploit Availability**: Known public exploits
4. **Active Exploitation**: Evidence from threat intelligence
5. **Vulnerability Age**: Time since disclosure (older = higher likelihood)

## Configuration Options

```python
config = {
    "cache_enabled": True,              # Enable correlation caching
    "cache_ttl": 3600,                  # Cache TTL in seconds
    "min_correlation_score": 0.5,      # Minimum correlation threshold
    "exploit_weight": 0.3,              # Exploit availability weight
    "active_exploitation_weight": 0.5   # Active exploitation weight
}

correlator = ThreatCorrelator(config)
```

## Data Models

### Asset
- `asset_id`: Unique identifier
- `name`: Asset name
- `type`: server, workstation, network_device, container, vm
- `ip_addresses`: List of IP addresses
- `software`: List of installed software (name, version)
- `criticality`: LOW, MEDIUM, HIGH, CRITICAL

### CVE
- `cve_id`: CVE identifier (e.g., CVE-2024-1234)
- `cvss_score`: CVSS base score (0-10)
- `cvss_vector`: CVSS vector string
- `exploit_available`: Known exploit availability
- `epss_score`: EPSS score (0-1)
- `published_date`: Publication date (ISO format)

### ThreatIndicator
- `indicator_id`: Unique identifier
- `type`: ip, domain, hash, cve, pattern
- `value`: Indicator value
- `threat_type`: malware, exploit, apt
- `confidence`: Confidence score (0-1)
- `severity`: LOW, MEDIUM, HIGH, CRITICAL
- `first_seen`: First seen timestamp
- `last_seen`: Last seen timestamp

### ThreatCorrelation
- `cve_id`: CVE identifier
- `threat_indicators`: Related threat indicator IDs
- `correlation_score`: Confidence score (0-1)
- `active_exploitation`: Evidence of active exploitation
- `exploit_available`: Public exploit availability
- `threat_actors`: Associated threat actors
- `campaigns`: Related threat campaigns
- `techniques`: MITRE ATT&CK techniques

### AssetRisk
- `asset_id`: Asset identifier
- `risk_score`: Calculated risk (0-100)
- `threat_count`: Total threats
- `critical_threats`: Critical severity threats
- `vulnerable_software`: List of vulnerable components
- `recommendations`: Mitigation recommendations
- `exposure_window`: Days since first vulnerability

### SBOMThreatAnalysis
- `total_components`: Total SBOM components
- `vulnerable_components`: Vulnerable component count
- `threat_exposure`: Overall exposure score (0-100)
- `critical_vulns`: Critical vulnerabilities
- `high_vulns`: High severity vulnerabilities
- `affected_components`: Components with vulnerabilities
- `recommendations`: Remediation recommendations

## SBOM Format Support

The module supports both major SBOM formats:

### SPDX 2.3
```json
{
  "spdxVersion": "SPDX-2.3",
  "SPDXID": "SPDXRef-DOCUMENT",
  "packages": [
    {
      "name": "package-name",
      "versionInfo": "1.0.0"
    }
  ]
}
```

### CycloneDX 1.4
```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "components": [
    {
      "name": "package-name",
      "version": "1.0.0",
      "purl": "pkg:npm/package-name@1.0.0"
    }
  ]
}
```

## Caching

The correlator includes built-in caching for performance:

```python
# Get cache statistics
stats = correlator.get_cache_stats()
print(f"Correlation cache: {stats['correlation_cache_size']} entries")
print(f"Risk cache: {stats['risk_cache_size']} entries")

# Clear caches
correlator.clear_cache()
```

## Performance Considerations

- **Caching**: Enable caching for repeated correlations
- **Batch Processing**: Process multiple assets/CVEs in single calls
- **Filtering**: Use `min_correlation_score` to filter low-confidence matches
- **Cache TTL**: Adjust TTL based on threat intelligence update frequency

## Testing

Run the test suite:

```bash
pytest tools/threat_intelligence/correlator/test_correlator.py -v
```

Test coverage:
- 36 test cases
- Model validation tests
- Correlation algorithm tests
- Risk scoring tests
- SBOM analysis tests
- Edge case handling
- Integration scenarios

## API Reference

### ThreatCorrelator

#### `__init__(config: Optional[Dict] = None)`
Initialize the correlator with optional configuration.

#### `correlate_vulnerabilities(vulnerabilities: List[CVE], threats: List[STIXObject]) -> List[ThreatCorrelation]`
Match vulnerabilities to active threats.

#### `analyze_asset_risk(asset_inventory: List[Asset], threat_data: List[ThreatIndicator]) -> List[AssetRisk]`
Calculate risk score for each asset.

#### `analyze_sbom(sbom: Dict, threat_data: List[ThreatIndicator]) -> SBOMThreatAnalysis`
Analyze SBOM for threats (supports SPDX and CycloneDX).

#### `calculate_risk_score(asset: Asset, threats: List[ThreatIndicator]) -> float`
Calculate risk score (0-100) for an asset.

#### `predict_exploit_likelihood(cve: CVE, threat_intelligence: List[STIXObject]) -> float`
Predict likelihood of exploitation (0-1).

#### `clear_cache() -> None`
Clear all caches.

#### `get_cache_stats() -> Dict[str, int]`
Get cache statistics.

## Examples

See `test_correlator.py` for comprehensive usage examples including:
- Basic correlation
- Asset risk analysis
- SBOM vulnerability assessment
- Exploit prediction
- Complete threat assessment workflows

## Integration

The Threat Correlator integrates with other threat intelligence platform components:

- **Feed Aggregator**: Consumes STIX/TAXII feeds for correlation
- **ATT&CK Mapper**: Extracts and maps MITRE ATT&CK techniques
- **VEX Generator**: Provides vulnerability data for VEX documents
- **IOC Manager**: Correlates IOCs with asset inventory
- **Intelligence Enricher**: Uses enriched threat data for better correlation

## Future Enhancements

- CPE/PURL-based vulnerability matching
- Machine learning-based exploit prediction
- Real-time threat correlation streaming
- Advanced attack path analysis
- Threat actor attribution scoring
- Campaign correlation tracking

## License

Part of the devCrew_s1 Threat Intelligence Platform.

## Support

For issues or questions, refer to the main project documentation.
