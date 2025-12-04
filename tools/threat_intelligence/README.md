# Threat Intelligence Platform (TOOL-SEC-008)

A comprehensive threat data aggregation and analysis platform for security operations with STIX/TAXII integration, CVE tracking, MITRE ATT&CK mapping, VEX document generation, and IOC management.

## Features

### Core Capabilities

- **Feed Aggregation**: Ingest threat intelligence from multiple sources
  - STIX/TAXII 2.1 protocol support
  - CVE database integration (NVD, OSV, GitHub Advisory)
  - Custom feed parsers
  - Automatic updates every 15 minutes
  - Feed normalization and deduplication

- **Threat Correlation**: Match vulnerabilities to real threats
  - Asset inventory correlation
  - SBOM (Software Bill of Materials) analysis
  - Risk scoring algorithm
  - Attack surface analysis
  - Vulnerability prioritization

- **MITRE ATT&CK Mapping**: Map threats to adversary tactics
  - Technique and sub-technique mapping
  - Tactic coverage analysis
  - Detection gap identification
  - Mitigation recommendations
  - ATT&CK Navigator layer generation

- **VEX Document Generation**: Track vulnerability exploitability
  - OpenVEX format support
  - CSAF 2.0 format support
  - Exploitability assessment
  - Remediation tracking
  - VEX document chaining

- **IOC Management**: Extract and manage indicators of compromise
  - Automated IOC extraction from feeds
  - IP, domain, hash, URL enrichment
  - False positive filtering
  - IOC lifecycle management
  - Export to multiple formats (STIX, CSV, JSON)

- **Intelligence Enrichment**: Augment with OSINT data
  - Threat actor attribution
  - Campaign tracking
  - Geo-location analysis
  - TTP (Tactics, Techniques, Procedures) extraction
  - Confidence scoring

- **SIEM Integration**: Forward intelligence to security platforms
  - Splunk integration
  - Elastic Stack integration
  - QRadar integration
  - Syslog forwarding
  - REST API endpoints

## Installation

### System Requirements

- Python 3.10 or higher
- 8GB RAM minimum (16GB recommended)
- 20GB disk space for threat data
- Network access to threat intelligence feeds
- Optional: Elasticsearch 8.11+ for storage
- Optional: Redis for caching
- Optional: PostgreSQL for metadata storage

### Quick Install

```bash
# Clone the devCrew_s1 repository
git clone https://github.com/your-org/devCrew_s1.git
cd devCrew_s1/tools/threat_intelligence

# Install Python dependencies
pip install -r requirements.txt

# Copy and configure settings
cp threat-config.yaml.example threat-config.yaml
# Edit threat-config.yaml with your settings

# Initialize the database
python -m cli.threat_cli init

# Verify installation
python -m cli.threat_cli status
```

For detailed installation instructions, see [docs/installation.md](docs/installation.md).

## Quick Start

### 1. Configure Threat Feeds

Edit `threat-config.yaml` to add your threat intelligence feeds:

```yaml
feeds:
  stix_taxii:
    - name: "CISA AIS"
      url: "https://cisa.gov/taxii2/"
      collection_id: "your-collection-id"
      api_key: "your-api-key"
      update_interval: 900  # 15 minutes

  cve_sources:
    - name: "NVD"
      enabled: true
      api_key: "your-nvd-api-key"

    - name: "OSV"
      enabled: true
      ecosystems: ["PyPI", "npm", "Go", "Rust"]
```

See [docs/feed_configuration.md](docs/feed_configuration.md) for complete configuration options.

### 2. Ingest Threat Intelligence

```bash
# Ingest from all configured feeds
python -m cli.threat_cli ingest --all

# Ingest from specific feed
python -m cli.threat_cli ingest --feed cisa-ais

# Ingest CVE data for specific date range
python -m cli.threat_cli ingest --cve --start-date 2024-01-01 --end-date 2024-12-31

# Continuous ingestion mode
python -m cli.threat_cli ingest --daemon --interval 900
```

### 3. Correlate with Your Assets

```bash
# Correlate threats with asset inventory
python -m cli.threat_cli correlate \
  --assets assets.json \
  --output correlation_report.json

# Correlate with SBOM
python -m cli.threat_cli correlate \
  --sbom sbom.json \
  --format cyclonedx \
  --output sbom_threats.json

# Generate risk scores
python -m cli.threat_cli correlate \
  --assets assets.json \
  --risk-scoring \
  --output risk_report.pdf
```

### 4. Generate VEX Documents

```bash
# Generate OpenVEX document
python -m cli.threat_cli vex \
  --product "MyApp v2.1.0" \
  --vulnerabilities vuln_list.json \
  --format openvex \
  --output vex_document.json

# Generate CSAF 2.0 document
python -m cli.threat_cli vex \
  --product "MyApp v2.1.0" \
  --vulnerabilities vuln_list.json \
  --format csaf \
  --output csaf_advisory.json

# Mark vulnerabilities as not affected
python -m cli.threat_cli vex \
  --vex-id VEX-2024-001 \
  --status not_affected \
  --justification component_not_present \
  --output updated_vex.json
```

### 5. Map to MITRE ATT&CK

```bash
# Map threats to ATT&CK techniques
python -m cli.threat_cli attack-map \
  --threats threat_data.json \
  --output attack_mapping.json

# Generate ATT&CK Navigator layer
python -m cli.threat_cli attack-map \
  --threats threat_data.json \
  --navigator-layer \
  --output navigator_layer.json

# Identify detection gaps
python -m cli.threat_cli attack-map \
  --threats threat_data.json \
  --coverage-analysis \
  --detections current_detections.json \
  --output gap_analysis.json
```

### 6. Manage IOCs

```bash
# Extract IOCs from threat feeds
python -m cli.threat_cli ioc extract \
  --feed-data feed_dump.json \
  --output iocs.json

# Enrich IOCs with OSINT
python -m cli.threat_cli ioc enrich \
  --iocs iocs.json \
  --services virustotal,abuseipdb,shodan \
  --output enriched_iocs.json

# Export IOCs for SIEM
python -m cli.threat_cli ioc export \
  --format stix \
  --output ioc_feed.stix \
  --start-date 2024-12-01

# Filter false positives
python -m cli.threat_cli ioc filter \
  --iocs iocs.json \
  --whitelist whitelist.txt \
  --confidence-threshold 70 \
  --output filtered_iocs.json
```

### 7. Generate Reports

```bash
# Generate threat intelligence report
python -m cli.threat_cli report \
  --report-type intelligence \
  --start-date 2024-12-01 \
  --end-date 2024-12-31 \
  --format pdf \
  --output monthly_intel_report.pdf

# Generate vulnerability report
python -m cli.threat_cli report \
  --report-type vulnerability \
  --assets assets.json \
  --format html \
  --output vuln_report.html

# Generate ATT&CK coverage report
python -m cli.threat_cli report \
  --report-type attack-coverage \
  --format json \
  --output coverage_report.json
```

## Usage Examples

### Example 1: Daily Threat Intelligence Workflow

```bash
#!/bin/bash
# daily_threat_intel.sh

# 1. Ingest latest threat data
python -m cli.threat_cli ingest --all --verbose

# 2. Correlate with production assets
python -m cli.threat_cli correlate \
  --assets /opt/inventory/assets.json \
  --risk-scoring \
  --output /var/reports/daily_correlation.json

# 3. Export high-priority IOCs to SIEM
python -m cli.threat_cli ioc export \
  --format splunk \
  --priority high,critical \
  --output /var/siem/iocs.txt

# 4. Generate daily report
python -m cli.threat_cli report \
  --report-type daily-summary \
  --format pdf \
  --output /var/reports/threat_summary_$(date +%Y%m%d).pdf

# 5. Send alerts for critical threats
python -m cli.threat_cli alert \
  --severity critical \
  --email security-team@example.com
```

### Example 2: VEX Document for Software Release

```python
# generate_vex.py
from vex.vex_generator import VEXGenerator
from datetime import datetime

# Initialize VEX generator
vex_gen = VEXGenerator(format="openvex")

# Create VEX document for new release
vex_doc = vex_gen.create_document(
    product_id="pkg:npm/myapp@2.1.0",
    product_name="MyApp",
    version="2.1.0",
    vendor="ACME Corp",
    release_date=datetime.now()
)

# Add vulnerability assessments
vex_doc.add_vulnerability(
    cve_id="CVE-2024-1234",
    status="not_affected",
    justification="vulnerable_code_not_present",
    impact_statement="The vulnerable function is not included in our build"
)

vex_doc.add_vulnerability(
    cve_id="CVE-2024-5678",
    status="affected",
    action_statement="Patch available in version 2.1.1",
    action_statement_timestamp=datetime.now()
)

# Save VEX document
vex_doc.save("myapp_v2.1.0_vex.json")
print(f"VEX document generated: {vex_doc.document_id}")
```

### Example 3: Asset Risk Scoring

```python
# risk_scoring.py
from correlator.threat_correlator import ThreatCorrelator
import json

# Load asset inventory
with open('assets.json', 'r') as f:
    assets = json.load(f)

# Initialize correlator
correlator = ThreatCorrelator(
    threat_db="elasticsearch://localhost:9200",
    cache_enabled=True
)

# Calculate risk scores
for asset in assets:
    # Find relevant threats
    threats = correlator.find_threats_for_asset(
        asset_id=asset['id'],
        software_components=asset['software'],
        network_exposure=asset['exposure']
    )

    # Calculate risk score
    risk_score = correlator.calculate_risk_score(
        asset=asset,
        threats=threats,
        scoring_model="cvss_v3_with_context"
    )

    # Print high-risk assets
    if risk_score['total_score'] >= 8.0:
        print(f"HIGH RISK: {asset['name']}")
        print(f"  Score: {risk_score['total_score']}/10")
        print(f"  Critical Threats: {risk_score['critical_count']}")
        print(f"  Exploitable: {risk_score['exploitable_count']}")
        print()
```

### Example 4: ATT&CK Detection Gap Analysis

```python
# gap_analysis.py
from attack.attack_mapper import ATTACKMapper
import json

# Initialize ATT&CK mapper
mapper = ATTACKMapper(
    attack_version="v14.1",
    domain="enterprise-attack"
)

# Load current detections
with open('current_detections.json', 'r') as f:
    detections = json.load(f)

# Load recent threat intelligence
recent_threats = mapper.load_threats(
    start_date="2024-11-01",
    end_date="2024-12-01"
)

# Map threats to techniques
threat_techniques = mapper.map_threats_to_techniques(recent_threats)

# Identify detection gaps
gaps = mapper.find_detection_gaps(
    threat_techniques=threat_techniques,
    current_detections=detections
)

# Generate prioritized gap list
for gap in gaps.get_prioritized():
    print(f"GAP: {gap['technique_id']} - {gap['technique_name']}")
    print(f"  Tactic: {gap['tactic']}")
    print(f"  Threat Count: {gap['threat_count']}")
    print(f"  Priority: {gap['priority']}")
    print(f"  Recommendation: {gap['recommendation']}")
    print()

# Export as Navigator layer
navigator_layer = mapper.generate_navigator_layer(
    gaps=gaps,
    layer_name="Detection Gaps - December 2024"
)
navigator_layer.save("detection_gaps.json")
```

## API Usage

The platform provides a Python API for programmatic access:

```python
from feeds.aggregator import FeedAggregator
from correlator.threat_correlator import ThreatCorrelator
from vex.vex_generator import VEXGenerator
from attack.attack_mapper import ATTACKMapper
from ioc.ioc_manager import IOCManager

# Initialize components
aggregator = FeedAggregator(config_file="threat-config.yaml")
correlator = ThreatCorrelator()
vex_gen = VEXGenerator()
attack_mapper = ATTACKMapper()
ioc_manager = IOCManager()

# Ingest threats
threats = aggregator.ingest_all_feeds()
print(f"Ingested {len(threats)} threat indicators")

# Correlate with assets
assets = correlator.load_assets("assets.json")
correlations = correlator.correlate(threats, assets)
print(f"Found {len(correlations)} threat-asset correlations")

# Generate VEX document
vex_doc = vex_gen.create_for_product(
    product="myapp:2.1.0",
    vulnerabilities=correlations
)
vex_doc.save("vex_document.json")

# Map to ATT&CK
mappings = attack_mapper.map_threats(threats)
navigator = attack_mapper.generate_navigator_layer(mappings)
navigator.save("attack_layer.json")

# Extract and enrich IOCs
iocs = ioc_manager.extract_iocs(threats)
enriched = ioc_manager.enrich_iocs(iocs)
ioc_manager.export_iocs(enriched, format="stix", output="iocs.stix")
```

## Configuration

The platform uses YAML configuration files. Main configuration file: `threat-config.yaml`

```yaml
# Threat Intelligence Platform Configuration

# Feed Sources
feeds:
  stix_taxii:
    - name: "CISA AIS"
      url: "https://cisa.gov/taxii2/"
      collection_id: "collection-id"
      api_key: "${CISA_API_KEY}"
      poll_interval: 900

    - name: "MISP Feed"
      url: "https://misp.example.com/taxii2/"
      username: "${MISP_USER}"
      password: "${MISP_PASS}"
      verify_ssl: true

  cve_sources:
    - name: "NVD"
      enabled: true
      api_key: "${NVD_API_KEY}"
    - name: "OSV"
      enabled: true

# Storage Configuration
storage:
  backend: "elasticsearch"  # or "postgresql"
  elasticsearch:
    hosts: ["localhost:9200"]
    index_prefix: "threat-intel"
    retention_days: 365

  postgresql:
    host: "localhost"
    port: 5432
    database: "threat_intel"
    username: "${DB_USER}"
    password: "${DB_PASS}"

# Caching
cache:
  enabled: true
  backend: "redis"
  redis:
    host: "localhost"
    port: 6379
    ttl: 3600

# Correlation Settings
correlation:
  risk_scoring_model: "cvss_v3_with_context"
  threat_threshold: 5.0
  enable_sbom_analysis: true
  enable_asset_context: true

# MITRE ATT&CK
attack:
  version: "v14.1"
  domain: "enterprise-attack"
  auto_update: true

# IOC Management
ioc:
  enrichment_services:
    - name: "VirusTotal"
      api_key: "${VT_API_KEY}"
    - name: "AbuseIPDB"
      api_key: "${AIPDB_API_KEY}"

  false_positive_filtering: true
  confidence_threshold: 60

# SIEM Integration
siem:
  splunk:
    enabled: true
    hec_url: "https://splunk.example.com:8088"
    hec_token: "${SPLUNK_HEC_TOKEN}"

  elastic:
    enabled: false
    hosts: ["localhost:9200"]

# Reporting
reporting:
  output_dir: "/var/reports/threat-intel"
  formats: ["pdf", "html", "json"]
  schedule:
    daily: "06:00"
    weekly: "Mon 08:00"
    monthly: "1st 09:00"

# Logging
logging:
  level: "INFO"
  file: "/var/log/threat-intel/platform.log"
  max_size_mb: 100
  backup_count: 10
```

For detailed configuration options, see [docs/feed_configuration.md](docs/feed_configuration.md).

## Integration Examples

### Splunk Integration

```python
# splunk_integration.py
from integrations.siem.splunk import SplunkIntegration

# Initialize Splunk integration
splunk = SplunkIntegration(
    hec_url="https://splunk.example.com:8088",
    hec_token="your-hec-token"
)

# Send threat events
splunk.send_threats(
    threats=recent_threats,
    source="threat_intel_platform",
    sourcetype="stix:json"
)

# Send IOCs
splunk.send_iocs(
    iocs=ioc_list,
    index="threat_intelligence"
)

# Query for correlated events
events = splunk.query(
    search='index=security sourcetype=firewall | lookup ioc_list ip AS dest_ip',
    earliest_time="-24h"
)
```

### Elastic Stack Integration

```python
# elastic_integration.py
from integrations.siem.elastic import ElasticIntegration

# Initialize Elastic integration
elastic = ElasticIntegration(
    hosts=["localhost:9200"],
    api_key="your-api-key"
)

# Index threat data
elastic.index_threats(
    threats=threat_data,
    index="threat-intelligence-*"
)

# Create IOC watchlist
elastic.create_watchlist(
    name="malicious-ips",
    iocs=ip_iocs,
    type="ip"
)

# Query for matches
matches = elastic.search_ioc_matches(
    index="logs-*",
    timerange="now-24h"
)
```

### CI/CD Pipeline Integration

```yaml
# .github/workflows/security-scan.yml
name: Security Scan with Threat Intel

on: [push, pull_request]

jobs:
  threat-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Generate SBOM
        run: |
          pip install cyclonedx-bom
          cyclonedx-py -o sbom.json

      - name: Setup Threat Intel Platform
        run: |
          pip install -r tools/threat_intelligence/requirements.txt

      - name: Scan SBOM for Threats
        run: |
          python -m cli.threat_cli correlate \
            --sbom sbom.json \
            --format cyclonedx \
            --output threat_report.json \
            --fail-on-critical

      - name: Generate VEX Document
        if: always()
        run: |
          python -m cli.threat_cli vex \
            --product "${{ github.repository }}:${{ github.sha }}" \
            --sbom sbom.json \
            --format openvex \
            --output vex_document.json

      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: security-reports
          path: |
            threat_report.json
            vex_document.json
```

## Troubleshooting

### Common Issues

**Feed ingestion fails:**
```bash
# Check feed connectivity
python -m cli.threat_cli test-feed --feed cisa-ais

# Enable debug logging
python -m cli.threat_cli ingest --feed cisa-ais --log-level DEBUG

# Verify API credentials
python -m cli.threat_cli verify-credentials
```

**Performance issues:**
```bash
# Enable caching
# Edit threat-config.yaml: cache.enabled: true

# Optimize Elasticsearch
# Increase heap size, adjust refresh interval

# Use batch processing
python -m cli.threat_cli ingest --batch-size 1000
```

**VEX generation errors:**
```bash
# Validate input data
python -m cli.threat_cli validate-vulnerabilities vuln_list.json

# Check VEX schema
python -m cli.threat_cli validate-vex vex_document.json

# Use verbose mode
python -m cli.threat_cli vex --verbose
```

For detailed troubleshooting, see [docs/troubleshooting.md](docs/troubleshooting.md).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Threat Intelligence Platform                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Feed Sources │  │  STIX/TAXII  │  │ CVE Database │          │
│  │   (External) │  │    Feeds     │  │    (NVD)     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┴──────────────────┘                   │
│                            │                                      │
│                   ┌────────▼────────┐                            │
│                   │ Feed Aggregator │                            │
│                   └────────┬────────┘                            │
│                            │                                      │
│         ┌──────────────────┼──────────────────┐                 │
│         │                  │                   │                 │
│  ┌──────▼──────┐  ┌────────▼────────┐  ┌──────▼──────┐         │
│  │   Threat    │  │  Intelligence   │  │     IOC     │         │
│  │ Correlator  │  │   Enricher      │  │   Manager   │         │
│  └──────┬──────┘  └────────┬────────┘  └──────┬──────┘         │
│         │                  │                   │                 │
│         └──────────────────┼───────────────────┘                 │
│                            │                                      │
│         ┌──────────────────┼──────────────────┐                 │
│         │                  │                   │                 │
│  ┌──────▼──────┐  ┌────────▼────────┐  ┌──────▼──────┐         │
│  │   ATT&CK    │  │      VEX        │  │   Report    │         │
│  │   Mapper    │  │   Generator     │  │  Generator  │         │
│  └──────┬──────┘  └────────┬────────┘  └──────┬──────┘         │
│         │                  │                   │                 │
│         └──────────────────┴───────────────────┘                 │
│                            │                                      │
│                   ┌────────▼────────┐                            │
│                   │  SIEM / Output  │                            │
│                   └─────────────────┘                            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Performance

- **Ingestion Rate**: 10,000+ indicators per minute
- **Query Performance**: Sub-second queries on 10M+ indicators
- **Feed Update Interval**: 15 minutes (configurable)
- **Correlation Speed**: 1,000 assets per minute
- **Storage**: Efficient storage with Elasticsearch or PostgreSQL

## Security

- **Encrypted Storage**: All sensitive data encrypted at rest
- **API Authentication**: Token-based authentication for API access
- **Secure Communication**: TLS/SSL for all external connections
- **Access Control**: Role-based access control (RBAC)
- **Audit Logging**: Complete audit trail of all operations
- **Credential Management**: Environment variable support for secrets

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run integration tests
pytest tests/test_integration.py -v

# Run performance tests
pytest tests/test_performance.py -v

# Run specific module tests
pytest feeds/test_aggregator.py -v
```

## Contributing

1. Follow the devCrew_s1 development standards
2. Ensure all tests pass before submitting
3. Add tests for new features
4. Update documentation for changes
5. Run pre-commit hooks:
   ```bash
   pre-commit run --all-files
   ```

## License

Copyright (c) 2024 devCrew_s1. All rights reserved.

## Support

For issues, questions, or contributions, please use the GitHub issue tracker.

## Documentation

- [Installation Guide](docs/installation.md)
- [Feed Configuration](docs/feed_configuration.md)
- [Threat Correlation](docs/threat_correlation.md)
- [VEX Documentation](docs/vex_documentation.md)
- [ATT&CK Mapping](docs/attack_mapping.md)
- [SIEM Integration](docs/siem_integration.md)
- [IOC Management](docs/ioc_management.md)
- [Troubleshooting](docs/troubleshooting.md)

## Version

Current Version: 1.0.0

See [CHANGELOG.md](CHANGELOG.md) for version history.
