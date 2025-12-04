# SIEM Integration Guide

Guide for integrating the Threat Intelligence Platform with Security Information and Event Management (SIEM) systems.

## Table of Contents

- [Overview](#overview)
- [Splunk Integration](#splunk-integration)
- [Elastic Stack Integration](#elastic-stack-integration)
- [QRadar Integration](#qradar-integration)
- [Syslog Forwarding](#syslog-forwarding)
- [API Integration](#api-integration)

## Overview

SIEM integration enables real-time correlation of threat intelligence with security events, providing contextualized alerts and improved detection capabilities.

### Integration Methods

- **Push**: Platform sends threat data to SIEM
- **Pull**: SIEM queries platform API
- **Hybrid**: Combination of push and pull

### Data Types Sent to SIEM

- Indicators of Compromise (IOCs)
- Threat intelligence context
- Vulnerability information
- ATT&CK technique mappings
- Risk scores and correlations

## Splunk Integration

### Setup

#### 1. Configure HTTP Event Collector (HEC)

```yaml
# threat-config.yaml
siem:
  splunk:
    enabled: true
    hec_url: "https://splunk.example.com:8088"
    hec_token: "${SPLUNK_HEC_TOKEN}"
    index: "threat_intelligence"
    sourcetype: "stix:json"
    verify_ssl: true
```

#### 2. Send Threat Data

```bash
# Send all threat intelligence
python -m cli.threat_cli siem-export \
  --target splunk \
  --config-file threat-config.yaml

# Send specific IOCs
python -m cli.threat_cli ioc export \
  --format splunk \
  --output splunk_iocs.txt

# Continuous forwarding
python -m cli.threat_cli siem-forward \
  --target splunk \
  --daemon \
  --interval 300
```

### Python API

```python
from integrations.siem.splunk import SplunkIntegration
import json

# Initialize Splunk integration
splunk = SplunkIntegration(
    hec_url="https://splunk.example.com:8088",
    hec_token="your-hec-token",
    index="threat_intelligence",
    verify_ssl=True
)

# Send threat events
with open('threats.json') as f:
    threats = json.load(f)

response = splunk.send_threats(
    threats=threats,
    source="threat_intel_platform",
    sourcetype="stix:json"
)

print(f"Sent {response['events_sent']} events to Splunk")

# Send IOCs
iocs = [
    {
        "type": "domain",
        "value": "malicious.example.com",
        "confidence": 85,
        "tags": ["malware", "c2"]
    }
]

splunk.send_iocs(
    iocs=iocs,
    index="threat_intelligence"
)

# Query Splunk for correlated events
events = splunk.query(
    search='index=security sourcetype=firewall | lookup threat_intel_iocs ip AS dest_ip OUTPUT threat_confidence',
    earliest_time="-24h",
    latest_time="now"
)

for event in events:
    print(f"Matched event: {event}")
```

### Splunk Lookups

#### Create IOC Lookup

```python
# Export IOCs as CSV lookup
from ioc.ioc_manager import IOCManager

ioc_manager = IOCManager()
iocs = ioc_manager.export_iocs(
    format="csv",
    output="threat_intel_iocs.csv"
)

# Upload to Splunk
splunk.upload_lookup(
    lookup_name="threat_intel_iocs",
    lookup_file="threat_intel_iocs.csv"
)
```

Lookup file format:
```csv
ioc_type,ioc_value,confidence,first_seen,last_seen,tags
domain,malicious.example.com,85,2024-12-01,2024-12-04,malware;c2
ip,192.0.2.100,90,2024-12-02,2024-12-04,apt29;phishing
hash,d41d8cd98f00b204e9800998ecf8427e,95,2024-12-03,2024-12-04,ransomware
```

#### Use Lookup in Splunk

```spl
# Enrich firewall logs with threat intelligence
index=security sourcetype=firewall
| lookup threat_intel_iocs ioc_value AS dest_ip OUTPUT confidence, tags
| where confidence > 70
| table _time, src_ip, dest_ip, confidence, tags
```

### Splunk Searches

#### Detect Threat Intelligence Matches

```spl
index=security
| lookup threat_intel_iocs ioc_value AS dest_ip OUTPUT confidence, tags AS threat_tags
| where isnotnull(confidence) AND confidence > 70
| eval severity=case(
    confidence >= 90, "critical",
    confidence >= 70, "high",
    confidence >= 50, "medium",
    1=1, "low"
  )
| table _time, src_ip, dest_ip, confidence, threat_tags, severity
| sort -confidence
```

#### Correlate with ATT&CK

```spl
index=threat_intelligence sourcetype="stix:json"
| spath output=technique_id path=attack_pattern.external_references{}.external_id
| where like(technique_id, "T%")
| table _time, technique_id, name, description
| join type=left technique_id
    [search index=security sourcetype=windows:security
    | eval technique_id="T1059.001"
    | table _time, host, user, technique_id]
| where isnotnull(host)
| table _time, host, user, technique_id, name
```

### Splunk Alerts

```xml
<!-- savedsearches.conf -->
[Threat Intelligence Match - Critical]
search = index=security \
| lookup threat_intel_iocs ioc_value AS dest_ip OUTPUT confidence, tags \
| where confidence >= 90
cron_schedule = */5 * * * *
enableSched = 1
action.email = 1
action.email.to = security-team@example.com
action.email.subject = Critical Threat Intelligence Match
action.email.message = Critical threat detected. Review immediately.
alert.severity = 5
alert.track = 1
```

### Splunk Dashboard

```xml
<!-- threat_intelligence_dashboard.xml -->
<dashboard>
  <label>Threat Intelligence Dashboard</label>
  <row>
    <panel>
      <title>IOC Matches (Last 24h)</title>
      <single>
        <search>
          <query>
            index=security earliest=-24h
            | lookup threat_intel_iocs ioc_value AS dest_ip
            | where isnotnull(confidence)
            | stats count
          </query>
        </search>
        <option name="drilldown">all</option>
      </single>
    </panel>
    <panel>
      <title>Top Threat Sources</title>
      <chart>
        <search>
          <query>
            index=security earliest=-24h
            | lookup threat_intel_iocs ioc_value AS dest_ip OUTPUT tags
            | where isnotnull(tags)
            | stats count by tags
            | sort -count limit=10
          </query>
        </search>
        <option name="charting.chart">pie</option>
      </chart>
    </panel>
  </row>
</dashboard>
```

## Elastic Stack Integration

### Setup

#### 1. Configure Elasticsearch

```yaml
# threat-config.yaml
siem:
  elastic:
    enabled: true
    hosts: ["https://elasticsearch.example.com:9200"]
    api_key: "${ELASTIC_API_KEY}"
    # or username/password
    username: "${ELASTIC_USER}"
    password: "${ELASTIC_PASS}"
    index_prefix: "threat-intel"
    verify_certs: true
```

#### 2. Create Index Template

```bash
# Create threat intelligence index template
python -m cli.threat_cli siem-setup \
  --target elastic \
  --create-templates
```

### Python API

```python
from integrations.siem.elastic import ElasticIntegration

# Initialize Elastic integration
elastic = ElasticIntegration(
    hosts=["https://elasticsearch.example.com:9200"],
    api_key="your-api-key",
    verify_certs=True
)

# Index threat data
with open('threats.json') as f:
    threats = json.load(f)

response = elastic.index_threats(
    threats=threats,
    index="threat-intelligence-*"
)

print(f"Indexed {response['indexed_count']} documents")

# Create IOC watchlist
iocs = [
    {"type": "ip", "value": "192.0.2.100", "confidence": 90},
    {"type": "domain", "value": "malicious.example.com", "confidence": 85}
]

elastic.create_watchlist(
    name="malicious-ips",
    iocs=iocs,
    type="ip"
)

# Search for IOC matches
matches = elastic.search_ioc_matches(
    index="logs-*",
    timerange="now-24h"
)

for match in matches:
    print(f"Match: {match['_source']}")
```

### Elasticsearch Queries

#### Find IOC Matches

```json
POST /logs-*/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "@timestamp": {
              "gte": "now-24h"
            }
          }
        }
      ],
      "filter": [
        {
          "terms": {
            "destination.ip": {
              "index": "threat-intel-iocs",
              "id": "malicious-ips",
              "path": "ip"
            }
          }
        }
      ]
    }
  }
}
```

### Kibana Integration

#### Create Detection Rule

```python
# Create detection rule in Kibana
rule = {
    "name": "Threat Intelligence IOC Match",
    "description": "Alert on communication with known malicious IPs",
    "risk_score": 75,
    "severity": "high",
    "type": "query",
    "query": """
        destination.ip:* and threat.indicator.ip:*
    """,
    "threat": [
        {
            "framework": "MITRE ATT&CK",
            "tactic": {
                "id": "TA0011",
                "name": "Command and Control"
            },
            "technique": [
                {
                    "id": "T1071",
                    "name": "Application Layer Protocol"
                }
            ]
        }
    ],
    "actions": [
        {
            "group": "default",
            "id": "email-action",
            "action_type_id": ".email",
            "params": {
                "to": ["security-team@example.com"],
                "subject": "Threat Intelligence Match Detected"
            }
        }
    ]
}

elastic.create_detection_rule(rule)
```

#### Create Dashboard

```python
# Create Kibana dashboard
dashboard = elastic.create_dashboard(
    title="Threat Intelligence Overview",
    visualizations=[
        {
            "type": "metric",
            "title": "IOC Matches (24h)",
            "query": "threat.indicator.ip:* OR threat.indicator.domain:*"
        },
        {
            "type": "bar",
            "title": "Top Threat Types",
            "field": "threat.indicator.type"
        },
        {
            "type": "line",
            "title": "Threat Activity Timeline",
            "field": "@timestamp"
        }
    ]
)
```

### ECS Mapping

Elastic Common Schema mapping:

```python
# Map threat data to ECS
ecs_document = {
    "@timestamp": "2024-12-04T10:30:00.000Z",
    "event": {
        "kind": "enrichment",
        "category": ["threat"],
        "type": ["indicator"],
        "dataset": "threat.indicator"
    },
    "threat": {
        "indicator": {
            "type": "domain-name",
            "domain": "malicious.example.com",
            "confidence": 85,
            "first_seen": "2024-12-01T00:00:00.000Z",
            "last_seen": "2024-12-04T10:30:00.000Z",
            "tags": ["malware", "c2"]
        },
        "framework": "MITRE ATT&CK",
        "tactic": {
            "id": "TA0011",
            "name": "Command and Control"
        },
        "technique": {
            "id": "T1071.001",
            "name": "Application Layer Protocol: Web Protocols"
        }
    }
}
```

## QRadar Integration

### Setup

```yaml
# threat-config.yaml
siem:
  qradar:
    enabled: true
    host: "qradar.example.com"
    api_token: "${QRADAR_API_TOKEN}"
    reference_set: "ThreatIntelIOCs"
    verify_ssl: true
```

### Python API

```python
from integrations.siem.qradar import QRadarIntegration

# Initialize QRadar integration
qradar = QRadarIntegration(
    host="qradar.example.com",
    api_token="your-api-token",
    verify_ssl=True
)

# Create reference set for IOCs
qradar.create_reference_set(
    name="ThreatIntelIOCs",
    element_type="IP",
    timeout_type="LAST_SEEN",
    timeout="30 days"
)

# Add IOCs to reference set
iocs = ["192.0.2.100", "192.0.2.101", "192.0.2.102"]
qradar.add_to_reference_set(
    name="ThreatIntelIOCs",
    values=iocs
)

# Create custom rule
rule = qradar.create_rule(
    name="Threat Intelligence Match",
    enabled=True,
    rule_type="COMMON",
    tests=[
        {
            "test": "when any of destinationip in reference set 'ThreatIntelIOCs'"
        }
    ],
    responses=[
        {
            "type": "OFFENSE",
            "offense_name": "Communication with Known Malicious IP"
        }
    ]
)

# Query for offenses
offenses = qradar.get_offenses(
    filter="categories contains 'Threat Intelligence'"
)
```

### QRadar AQL Queries

```sql
-- Find events matching IOCs
SELECT
    sourceip,
    destinationip,
    eventcount,
    QIDNAME(qid) as "Event Name"
FROM events
WHERE
    destinationip IN (
        SELECT element
        FROM REFERENCESET('ThreatIntelIOCs')
    )
LAST 24 HOURS
```

## Syslog Forwarding

### Setup

```yaml
# threat-config.yaml
siem:
  syslog:
    enabled: true
    host: "syslog.example.com"
    port: 514
    protocol: "tcp"  # or "udp"
    facility: "local0"
    severity: "info"
    format: "rfc5424"  # or "rfc3164"
```

### Python API

```python
from integrations.siem.syslog import SyslogIntegration

# Initialize syslog integration
syslog = SyslogIntegration(
    host="syslog.example.com",
    port=514,
    protocol="tcp",
    facility="local0"
)

# Send threat event
syslog.send_event(
    severity="warning",
    message="Threat detected: IOC match",
    structured_data={
        "ioc_type": "ip",
        "ioc_value": "192.0.2.100",
        "confidence": 90,
        "tags": ["malware", "c2"]
    }
)

# Forward all new threats
syslog.forward_threats(
    threats=new_threats,
    batch_size=100
)
```

### Syslog Message Format

RFC 5424 format:
```
<134>1 2024-12-04T10:30:00.000Z threat-intel-platform - - [threat ioc_type="ip" ioc_value="192.0.2.100" confidence="90"] IOC match detected
```

## API Integration

### REST API

The platform provides a REST API for SIEMs to pull threat intelligence.

#### Endpoints

```bash
# Get all IOCs
GET /api/v1/iocs
  ?type=ip,domain
  &confidence_min=70
  &last_updated=2024-12-01

# Get specific IOC
GET /api/v1/iocs/{ioc_id}

# Get threats
GET /api/v1/threats
  ?start_date=2024-12-01
  &end_date=2024-12-04
  &severity=high,critical

# Get ATT&CK mappings
GET /api/v1/attack/mappings
  ?technique_id=T1566.001

# Get VEX documents
GET /api/v1/vex
  ?product=myapp:2.1.0
```

#### Python Client

```python
from api_client import ThreatIntelClient

# Initialize client
client = ThreatIntelClient(
    base_url="https://threat-intel.example.com",
    api_key="your-api-key"
)

# Get IOCs
iocs = client.get_iocs(
    ioc_type=["ip", "domain"],
    confidence_min=70,
    last_updated="2024-12-01"
)

# Get threats
threats = client.get_threats(
    start_date="2024-12-01",
    end_date="2024-12-04",
    severity=["high", "critical"]
)

# Get ATT&CK mappings
mappings = client.get_attack_mappings(
    technique_id="T1566.001"
)
```

### TAXII Server

The platform can act as a TAXII server for SIEM systems to pull threat intelligence.

```bash
# Start TAXII server
python -m cli.threat_cli taxii-server \
  --host 0.0.0.0 \
  --port 8080 \
  --collections threat-intel,iocs,attack-patterns
```

TAXII client configuration for SIEM:

```python
from taxii2client.v21 import Server

# Connect to TAXII server
server = Server(
    "https://threat-intel.example.com/taxii2/",
    user="siem-client",
    password="secure-password"
)

# Get collections
for collection in server.collections:
    print(f"Collection: {collection.title}")

    # Get objects
    objects = collection.get_objects()
    for obj in objects["objects"]:
        print(f"  {obj['type']}: {obj['id']}")
```

## Best Practices

### 1. Data Volume Management

```python
# Send only high-confidence IOCs
iocs_filtered = [
    ioc for ioc in iocs
    if ioc['confidence'] >= 70
]

# Batch updates
siem.send_batch(
    data=iocs_filtered,
    batch_size=1000,
    delay_between_batches=1
)
```

### 2. Deduplication

```python
# Remove duplicates before sending
unique_iocs = siem.deduplicate(
    iocs=iocs,
    key_fields=['type', 'value'],
    keep='newest'
)
```

### 3. Rate Limiting

```python
# Respect SIEM rate limits
siem = SplunkIntegration(
    hec_url=hec_url,
    hec_token=hec_token,
    rate_limit=100,  # events per second
    rate_limit_burst=500
)
```

### 4. Error Handling

```python
try:
    response = siem.send_threats(threats)
except SIEMConnectionError as e:
    # Retry with backoff
    time.sleep(60)
    response = siem.send_threats(threats)
except SIEMAuthError as e:
    # Alert on auth failure
    alert_security_team(f"SIEM auth failed: {e}")
```

### 5. Monitoring

```python
# Monitor integration health
metrics = siem.get_metrics()
print(f"Events sent: {metrics['events_sent']}")
print(f"Errors: {metrics['errors']}")
print(f"Last success: {metrics['last_success']}")

# Alert on issues
if metrics['error_rate'] > 0.1:  # 10% error rate
    alert_ops_team("High SIEM error rate")
```

## Troubleshooting

### Connection Issues

```bash
# Test SIEM connectivity
python -m cli.threat_cli siem-test \
  --target splunk \
  --verbose

# Check network connectivity
curl -X POST https://splunk.example.com:8088/services/collector \
  -H "Authorization: Splunk YOUR-HEC-TOKEN" \
  -d '{"event": "test"}'
```

### Authentication Issues

```bash
# Verify credentials
python -m cli.threat_cli siem-verify \
  --target elastic \
  --config threat-config.yaml
```

### Data Not Appearing

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check index/index pattern
siem.verify_index("threat-intelligence-*")

# Verify data format
siem.validate_event(sample_event)
```

## Next Steps

- Manage [IOCs](ioc_management.md)
- Review [Troubleshooting](troubleshooting.md)
- Configure [Feed Sources](feed_configuration.md)
