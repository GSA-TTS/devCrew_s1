# Threat Correlator Quick Start Guide

## Installation

```bash
pip install pydantic>=2.0.0
```

## Basic Usage

```python
from threat_intelligence.correlator import ThreatCorrelator, CVE, STIXObject

# Initialize
correlator = ThreatCorrelator()

# Correlate vulnerabilities with threats
correlations = correlator.correlate_vulnerabilities(cves, stix_threats)

# Analyze asset risk
risk_assessments = correlator.analyze_asset_risk(assets, threat_indicators)

# Analyze SBOM
sbom_analysis = correlator.analyze_sbom(sbom_document, threat_data)

# Predict exploit likelihood
likelihood = correlator.predict_exploit_likelihood(cve, threat_intelligence)
```

## Data Models

### Create a CVE
```python
cve = CVE(
    cve_id="CVE-2024-1234",
    cvss_score=9.8,
    exploit_available=True,
    epss_score=0.85
)
```

### Create an Asset
```python
asset = Asset(
    asset_id="asset-001",
    name="Production Server",
    type="server",
    ip_addresses=["10.0.1.100"],
    software=[{"name": "nginx", "version": "1.18.0"}],
    criticality="CRITICAL"
)
```

### Create a Threat Indicator
```python
threat = ThreatIndicator(
    indicator_id="threat-001",
    type="cve",
    value="CVE-2024-1234",
    threat_type="exploit",
    confidence=0.9,
    severity="CRITICAL",
    first_seen="2024-01-01T00:00:00Z",
    last_seen="2024-01-15T00:00:00Z"
)
```

## Configuration

```python
config = {
    "cache_enabled": True,              # Enable caching
    "cache_ttl": 3600,                  # Cache TTL (seconds)
    "min_correlation_score": 0.5,       # Min correlation threshold
    "exploit_weight": 0.3,              # Exploit weight
    "active_exploitation_weight": 0.5   # Active exploitation weight
}

correlator = ThreatCorrelator(config)
```

## Examples

Run the example script:
```bash
cd tools/threat_intelligence/correlator
python3 example.py
```

## Testing

```bash
# Run all tests
pytest tools/threat_intelligence/correlator/test_correlator.py -v

# With coverage
pytest tools/threat_intelligence/correlator/test_correlator.py -v --cov
```

## API Quick Reference

| Method | Returns | Description |
|--------|---------|-------------|
| `correlate_vulnerabilities(cves, threats)` | List[ThreatCorrelation] | Match CVEs to threats |
| `analyze_asset_risk(assets, threats)` | List[AssetRisk] | Calculate asset risk |
| `analyze_sbom(sbom, threats)` | SBOMThreatAnalysis | Analyze SBOM threats |
| `calculate_risk_score(asset, threats)` | float (0-100) | Calculate risk score |
| `predict_exploit_likelihood(cve, intel)` | float (0-1) | Predict exploitation |
| `clear_cache()` | None | Clear all caches |
| `get_cache_stats()` | Dict | Get cache statistics |

## Risk Score Formula

```
Risk = Criticality × Likelihood × Exploitability × 10
Range: 0-100

Criticality: Asset importance (1-10)
  - LOW: 2.5, MEDIUM: 5.0, HIGH: 7.5, CRITICAL: 10.0

Likelihood: Threat presence (0-1)
  - Based on threat count and severity

Exploitability: Average threat confidence (0-1)
```

## SBOM Support

- **SPDX 2.3**: Fully supported
- **CycloneDX 1.4**: Fully supported

## For More Information

- Complete documentation: `README.md`
- Implementation details: `IMPLEMENTATION_SUMMARY.md`
- Working examples: `example.py`
- Test suite: `test_correlator.py`
