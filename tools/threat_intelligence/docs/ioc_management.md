# IOC Management Guide

Guide for extracting, enriching, and managing Indicators of Compromise (IOCs).

## Table of Contents

- [Overview](#overview)
- [IOC Extraction](#ioc-extraction)
- [Enrichment Services](#enrichment-services)
- [False Positive Filtering](#false-positive-filtering)
- [IOC Lifecycle](#ioc-lifecycle)
- [Export Formats](#export-formats)

## Overview

Indicators of Compromise (IOCs) are artifacts observed in networks or systems that indicate a potential security incident. The platform extracts, enriches, validates, and manages IOCs from threat intelligence feeds.

### Supported IOC Types

- **Network**: IP addresses, domains, URLs, email addresses
- **File**: MD5, SHA1, SHA256, SHA512, SSDEEP, file names
- **Registry**: Windows registry keys and values
- **Mutex**: Mutex names
- **Process**: Process names and command lines
- **Certificate**: SSL certificate hashes

## IOC Extraction

### CLI Usage

#### Extract from Feeds

```bash
# Extract IOCs from all feeds
python -m cli.threat_cli ioc extract \
  --output iocs.json

# Extract from specific feed data
python -m cli.threat_cli ioc extract \
  --feed-data feed_dump.json \
  --output iocs.json

# Extract specific IOC types
python -m cli.threat_cli ioc extract \
  --types ip,domain,hash \
  --output iocs.json

# Extract with minimum confidence
python -m cli.threat_cli ioc extract \
  --min-confidence 70 \
  --output iocs.json
```

#### Extract from Text

```bash
# Extract IOCs from text file
python -m cli.threat_cli ioc extract-text \
  --input report.txt \
  --output iocs.json

# Extract from multiple sources
python -m cli.threat_cli ioc extract-text \
  --input-dir ./reports/ \
  --recursive \
  --output iocs.json
```

### Python API

#### Basic Extraction

```python
from ioc.ioc_manager import IOCManager

# Initialize IOC manager
ioc_manager = IOCManager()

# Extract from threat data
with open('threats.json') as f:
    threat_data = json.load(f)

iocs = ioc_manager.extract_iocs(threat_data)

print(f"Extracted {len(iocs)} IOCs")
for ioc in iocs[:10]:  # Show first 10
    print(f"  {ioc['type']}: {ioc['value']} (confidence: {ioc['confidence']}%)")
```

#### Extract from STIX

```python
# Extract from STIX bundle
stix_bundle = {
    "type": "bundle",
    "objects": [
        {
            "type": "indicator",
            "pattern": "[ipv4-addr:value = '192.0.2.100']",
            "pattern_type": "stix",
            "valid_from": "2024-12-04T00:00:00Z"
        }
    ]
}

iocs = ioc_manager.extract_from_stix(stix_bundle)
```

#### Extract from Text

```python
# Extract from unstructured text
text = """
The malware connects to 192.0.2.100 and malicious.example.com.
File hash: d41d8cd98f00b204e9800998ecf8427e (MD5)
Email: attacker@evil.com
"""

iocs = ioc_manager.extract_from_text(text)

# Returns:
# [
#   {"type": "ipv4", "value": "192.0.2.100"},
#   {"type": "domain", "value": "malicious.example.com"},
#   {"type": "md5", "value": "d41d8cd98f00b204e9800998ecf8427e"},
#   {"type": "email", "value": "attacker@evil.com"}
# ]
```

#### Custom Extraction Patterns

```python
# Add custom extraction patterns
ioc_manager.add_pattern(
    name="custom_mutex",
    pattern=r"Global\\[A-Z0-9]{32}",
    ioc_type="mutex"
)

# Extract with custom patterns
iocs = ioc_manager.extract_from_text(
    text=malware_report,
    include_custom=True
)
```

## Enrichment Services

### Configuration

```yaml
# threat-config.yaml
ioc:
  enrichment_services:
    - name: "VirusTotal"
      api_key: "${VT_API_KEY}"
      rate_limit: 4  # requests per minute
      enabled: true

    - name: "AbuseIPDB"
      api_key: "${AIPDB_API_KEY}"
      rate_limit: 1000  # requests per day
      enabled: true

    - name: "Shodan"
      api_key: "${SHODAN_API_KEY}"
      enabled: true

    - name: "PassiveTotal"
      username: "${PT_USER}"
      api_key: "${PT_API_KEY}"
      enabled: false
```

### CLI Usage

```bash
# Enrich IOCs with all configured services
python -m cli.threat_cli ioc enrich \
  --iocs iocs.json \
  --output enriched_iocs.json

# Enrich with specific services
python -m cli.threat_cli ioc enrich \
  --iocs iocs.json \
  --services virustotal,abuseipdb \
  --output enriched_iocs.json

# Enrich specific IOC types
python -m cli.threat_cli ioc enrich \
  --iocs iocs.json \
  --types ip,domain \
  --output enriched_iocs.json
```

### Python API

#### VirusTotal Enrichment

```python
from ioc.enrichers.virustotal import VirusTotalEnricher

# Initialize enricher
vt_enricher = VirusTotalEnricher(api_key="your-api-key")

# Enrich IP address
ip_data = vt_enricher.enrich_ip("192.0.2.100")
print(f"Malicious: {ip_data['malicious_count']}/{ip_data['total_votes']}")
print(f"Country: {ip_data['country']}")
print(f"ASN: {ip_data['asn']}")

# Enrich domain
domain_data = vt_enricher.enrich_domain("malicious.example.com")
print(f"Reputation: {domain_data['reputation']}")
print(f"Last Analysis: {domain_data['last_analysis_date']}")

# Enrich file hash
hash_data = vt_enricher.enrich_hash("d41d8cd98f00b204e9800998ecf8427e")
print(f"Detections: {hash_data['positives']}/{hash_data['total']}")
print(f"File Type: {hash_data['file_type']}")
print(f"Names: {', '.join(hash_data['names'])}")
```

#### AbuseIPDB Enrichment

```python
from ioc.enrichers.abuseipdb import AbuseIPDBEnricher

# Initialize enricher
aipdb_enricher = AbuseIPDBEnricher(api_key="your-api-key")

# Enrich IP
ip_data = aipdb_enricher.enrich_ip("192.0.2.100")
print(f"Abuse Confidence: {ip_data['abuseConfidenceScore']}%")
print(f"Total Reports: {ip_data['totalReports']}")
print(f"Last Reported: {ip_data['lastReportedAt']}")
print(f"ISP: {ip_data['isp']}")
print(f"Usage Type: {ip_data['usageType']}")
```

#### Shodan Enrichment

```python
from ioc.enrichers.shodan import ShodanEnricher

# Initialize enricher
shodan_enricher = ShodanEnricher(api_key="your-api-key")

# Enrich IP
ip_data = shodan_enricher.enrich_ip("192.0.2.100")
print(f"Open Ports: {', '.join(map(str, ip_data['ports']))}")
print(f"Hostnames: {', '.join(ip_data['hostnames'])}")
print(f"Organization: {ip_data['org']}")
print(f"Services:")
for service in ip_data['services']:
    print(f"  - {service['port']}/{service['transport']}: {service['product']}")
```

#### Bulk Enrichment

```python
# Enrich multiple IOCs efficiently
iocs = [
    {"type": "ip", "value": "192.0.2.100"},
    {"type": "ip", "value": "192.0.2.101"},
    {"type": "domain", "value": "malicious.example.com"},
    {"type": "hash", "value": "d41d8cd98f00b204e9800998ecf8427e"}
]

enriched = ioc_manager.enrich_bulk(
    iocs=iocs,
    services=["virustotal", "abuseipdb", "shodan"],
    parallel=True,
    max_workers=5
)

for ioc in enriched:
    print(f"{ioc['type']}: {ioc['value']}")
    print(f"  Enrichment: {ioc['enrichment']}")
```

## False Positive Filtering

### Whitelist Configuration

```yaml
# threat-config.yaml
ioc:
  false_positive_filtering: true

  whitelist:
    # RFC 1918 private networks
    ip_ranges:
      - "10.0.0.0/8"
      - "172.16.0.0/12"
      - "192.168.0.0/16"
      - "127.0.0.0/8"

    # Internal domains
    domains:
      - "*.internal"
      - "*.local"
      - "*.corp.example.com"

    # Known benign hashes
    hashes:
      - "d41d8cd98f00b204e9800998ecf8427e"  # Empty file

    # Email domains
    email_domains:
      - "example.com"
      - "company.internal"

  # Confidence thresholds
  confidence_threshold: 60
  min_sources: 2  # Require at least 2 sources
```

### CLI Usage

```bash
# Filter IOCs
python -m cli.threat_cli ioc filter \
  --iocs iocs.json \
  --whitelist whitelist.txt \
  --output filtered_iocs.json

# Filter by confidence
python -m cli.threat_cli ioc filter \
  --iocs iocs.json \
  --confidence-threshold 70 \
  --output filtered_iocs.json

# Remove private IPs
python -m cli.threat_cli ioc filter \
  --iocs iocs.json \
  --remove-private \
  --output filtered_iocs.json
```

### Python API

```python
# Filter false positives
filtered_iocs = ioc_manager.filter_false_positives(
    iocs=iocs,
    whitelist_file="whitelist.txt",
    remove_private=True,
    confidence_threshold=70
)

# Custom filtering
def custom_filter(ioc):
    # Keep only high-confidence IOCs
    if ioc['confidence'] < 80:
        return False

    # Skip old IOCs
    age_days = (datetime.now() - ioc['first_seen']).days
    if age_days > 365:
        return False

    return True

filtered_iocs = [ioc for ioc in iocs if custom_filter(ioc)]
```

### Validation Rules

```python
# Add validation rules
ioc_manager.add_validation_rule(
    name="valid_ip",
    rule=lambda ioc: ipaddress.ip_address(ioc['value']).is_global,
    ioc_types=["ipv4", "ipv6"]
)

ioc_manager.add_validation_rule(
    name="valid_domain",
    rule=lambda ioc: len(ioc['value']) >= 4 and '.' in ioc['value'],
    ioc_types=["domain"]
)

# Validate IOCs
validated_iocs = ioc_manager.validate(iocs)
```

## IOC Lifecycle

### Aging and Expiration

```python
# Configure IOC aging
ioc_manager.configure_aging(
    default_ttl=90,  # days
    ttl_by_type={
        "ip": 30,
        "domain": 60,
        "hash": 365
    },
    confidence_decay=True,  # Reduce confidence over time
    decay_rate=0.1  # 10% per month
)

# Get active IOCs
active_iocs = ioc_manager.get_active_iocs(
    max_age_days=90
)

# Expire old IOCs
expired = ioc_manager.expire_iocs(
    max_age_days=365,
    archive=True,
    archive_path="/backup/expired_iocs"
)

print(f"Expired {len(expired)} IOCs")
```

### Status Tracking

```python
# IOC status values
# - active: Currently malicious
# - expired: Too old, confidence degraded
# - false_positive: Confirmed benign
# - investigating: Under analysis
# - whitelisted: Explicitly allowed

# Update IOC status
ioc_manager.update_status(
    ioc_id="ioc-12345",
    status="false_positive",
    reason="Confirmed as CDN IP",
    updated_by="analyst@example.com"
)

# Get IOCs by status
active = ioc_manager.get_by_status("active")
investigating = ioc_manager.get_by_status("investigating")
```

### Historical Tracking

```python
# Track IOC history
history = ioc_manager.get_history(
    ioc_value="192.0.2.100"
)

print(f"IOC: {history['ioc_value']}")
print(f"First Seen: {history['first_seen']}")
print(f"Last Seen: {history['last_seen']}")
print(f"Sightings: {history['sighting_count']}")
print(f"Sources: {', '.join(history['sources'])}")

# Timeline of changes
for event in history['timeline']:
    print(f"  {event['timestamp']}: {event['event_type']}")
    print(f"    {event['details']}")
```

### Deduplication

```python
# Deduplicate IOCs
unique_iocs = ioc_manager.deduplicate(
    iocs=iocs,
    strategy="merge",  # or "newest", "highest_confidence"
    merge_fields=["tags", "sources"]
)

# Merge duplicate IOCs
merged = ioc_manager.merge_duplicates(
    ioc_value="192.0.2.100",
    keep="highest_confidence",
    combine_metadata=True
)
```

## Export Formats

### STIX Format

```bash
# Export as STIX 2.1
python -m cli.threat_cli ioc export \
  --format stix \
  --output iocs.stix

# With relationships
python -m cli.threat_cli ioc export \
  --format stix \
  --include-relationships \
  --output iocs.stix
```

Python API:
```python
# Export to STIX
stix_bundle = ioc_manager.export_stix(
    iocs=iocs,
    include_relationships=True
)

with open('iocs.stix', 'w') as f:
    json.dump(stix_bundle, f, indent=2)
```

### CSV Format

```bash
# Export as CSV
python -m cli.threat_cli ioc export \
  --format csv \
  --output iocs.csv
```

CSV format:
```csv
type,value,confidence,first_seen,last_seen,tags,source
ip,192.0.2.100,90,2024-12-01,2024-12-04,"malware,c2",feed-001
domain,malicious.example.com,85,2024-12-02,2024-12-04,"phishing",feed-002
hash,d41d8cd98f00b204e9800998ecf8427e,95,2024-12-03,2024-12-04,"ransomware",feed-003
```

### JSON Format

```bash
# Export as JSON
python -m cli.threat_cli ioc export \
  --format json \
  --output iocs.json
```

JSON format:
```json
[
  {
    "id": "ioc-12345",
    "type": "ipv4",
    "value": "192.0.2.100",
    "confidence": 90,
    "first_seen": "2024-12-01T00:00:00Z",
    "last_seen": "2024-12-04T10:30:00Z",
    "tags": ["malware", "c2"],
    "source": "feed-001",
    "enrichment": {
      "country": "US",
      "asn": "AS15169",
      "reputation": "malicious"
    }
  }
]
```

### MISP Format

```bash
# Export for MISP
python -m cli.threat_cli ioc export \
  --format misp \
  --output iocs_misp.json
```

### OpenIOC Format

```bash
# Export as OpenIOC
python -m cli.threat_cli ioc export \
  --format openioc \
  --output iocs.xml
```

### Yara Rules

```bash
# Generate Yara rules from file IOCs
python -m cli.threat_cli ioc export \
  --format yara \
  --types hash \
  --output iocs.yar
```

Generated Yara rule:
```yara
rule ThreatIntel_Malware_Hashes {
    meta:
        description = "Malware file hashes from threat intelligence"
        generated = "2024-12-04"
        source = "threat_intel_platform"

    strings:
        $hash1 = "d41d8cd98f00b204e9800998ecf8427e" ascii
        $hash2 = "098f6bcd4621d373cade4e832627b4f6" ascii

    condition:
        any of them
}
```

### SIEM-Specific Formats

```bash
# Splunk format
python -m cli.threat_cli ioc export \
  --format splunk \
  --output splunk_iocs.txt

# Elastic format (ECS)
python -m cli.threat_cli ioc export \
  --format elastic \
  --output elastic_iocs.ndjson

# QRadar format
python -m cli.threat_cli ioc export \
  --format qradar \
  --output qradar_iocs.csv
```

## Advanced Features

### IOC Relationships

```python
# Define relationships between IOCs
ioc_manager.add_relationship(
    source_ioc="192.0.2.100",
    target_ioc="malicious.example.com",
    relationship_type="resolves_to",
    confidence=90
)

# Query relationships
related = ioc_manager.get_related_iocs(
    ioc_value="192.0.2.100",
    relationship_types=["resolves_to", "communicates_with"]
)

# Build IOC graph
graph = ioc_manager.build_ioc_graph(
    seed_ioc="192.0.2.100",
    max_depth=3
)
```

### IOC Scoring

```python
# Calculate composite score
score = ioc_manager.calculate_score(
    ioc=ioc,
    factors={
        'confidence': 0.3,
        'source_reputation': 0.2,
        'enrichment_data': 0.2,
        'age': 0.15,
        'sighting_frequency': 0.15
    }
)

print(f"IOC Score: {score['total_score']:.2f}/100")
print(f"  Confidence: {score['confidence_score']}")
print(f"  Reputation: {score['reputation_score']}")
print(f"  Freshness: {score['freshness_score']}")
```

### Automated IOC Management

```python
# Automated IOC pipeline
def ioc_pipeline():
    # 1. Extract from feeds
    iocs = ioc_manager.extract_from_feeds()

    # 2. Deduplicate
    iocs = ioc_manager.deduplicate(iocs)

    # 3. Filter false positives
    iocs = ioc_manager.filter_false_positives(iocs)

    # 4. Enrich
    iocs = ioc_manager.enrich_bulk(iocs)

    # 5. Score and prioritize
    iocs = ioc_manager.score_iocs(iocs)

    # 6. Export to SIEM
    ioc_manager.export_to_siem(iocs, target="splunk")

    # 7. Archive old IOCs
    ioc_manager.archive_old_iocs(max_age_days=90)

# Schedule pipeline
schedule.every(1).hours.do(ioc_pipeline)
```

## Best Practices

1. **Regular Cleanup**
   - Archive expired IOCs
   - Remove false positives
   - Deduplicate regularly

2. **Confidence Management**
   - Require minimum confidence
   - Implement confidence decay
   - Update based on feedback

3. **Enrichment Strategy**
   - Enrich high-priority IOCs first
   - Respect API rate limits
   - Cache enrichment data

4. **Export Optimization**
   - Export only active IOCs
   - Filter by date range
   - Batch large exports

5. **Documentation**
   - Document whitelist entries
   - Track status changes
   - Maintain audit trail

## Next Steps

- Review [Troubleshooting Guide](troubleshooting.md)
- Configure [SIEM Integration](siem_integration.md)
- Set up [Feed Sources](feed_configuration.md)
