# Feed Configuration Guide

Comprehensive guide for configuring threat intelligence feeds in the Threat Intelligence Platform.

## Table of Contents

- [Overview](#overview)
- [Feed Types](#feed-types)
- [STIX/TAXII Configuration](#stixtaxii-configuration)
- [CVE Sources](#cve-sources)
- [Custom Feed Formats](#custom-feed-formats)
- [Feed Authentication](#feed-authentication)
- [Update Intervals](#update-intervals)
- [Feed Filtering](#feed-filtering)
- [Best Practices](#best-practices)

## Overview

The Threat Intelligence Platform supports multiple feed types and formats. Feeds are configured in the `threat-config.yaml` file and can be managed through the CLI or API.

### Supported Feed Types

- **STIX/TAXII 2.1** - Industry-standard threat intelligence format
- **CVE Databases** - NVD, OSV, GitHub Advisory Database
- **MISP Feeds** - Malware Information Sharing Platform
- **Custom JSON/XML** - Custom threat feed formats
- **RSS/Atom Feeds** - Blog and advisory feeds
- **File-based Feeds** - Local or network file shares

## Feed Types

### STIX/TAXII Feeds

STIX (Structured Threat Information Expression) and TAXII (Trusted Automated Exchange of Intelligence Information) are the primary standards for threat intelligence sharing.

#### Basic Configuration

```yaml
feeds:
  stix_taxii:
    - name: "CISA AIS"
      url: "https://cisa.gov/taxii2/"
      collection_id: "xxx-xxx-xxx"
      api_key: "${CISA_API_KEY}"
      poll_interval: 900  # 15 minutes
      enabled: true

    - name: "MISP Feed"
      url: "https://misp.example.com/taxii2/"
      username: "${MISP_USER}"
      password: "${MISP_PASS}"
      verify_ssl: true
      poll_interval: 1800  # 30 minutes
      enabled: true
```

#### Advanced Configuration

```yaml
feeds:
  stix_taxii:
    - name: "Custom TAXII Server"
      url: "https://taxii.example.com/api/v2/"

      # Authentication
      auth_type: "jwt"  # or "basic", "api_key", "certificate"
      api_key: "${TAXII_API_KEY}"

      # Collection settings
      collection_id: "collection-uuid"
      collection_name: "threat-intelligence"

      # Polling configuration
      poll_interval: 900
      initial_poll_start: "2024-01-01T00:00:00Z"
      max_content_length: 10485760  # 10MB

      # Filtering
      filter:
        types: ["indicator", "malware", "threat-actor"]
        labels: ["malicious-activity"]
        confidence_min: 50

      # Processing options
      deduplication: true
      validation: true
      enrichment: true

      # Rate limiting
      rate_limit: 100  # requests per hour
      batch_size: 1000

      # Retry configuration
      retry_attempts: 3
      retry_delay: 60

      # SSL/TLS
      verify_ssl: true
      client_cert: "/path/to/client.crt"
      client_key: "/path/to/client.key"
      ca_bundle: "/path/to/ca-bundle.crt"

      # Proxy
      proxy: "http://proxy.example.com:8080"
      proxy_auth: "${PROXY_USER}:${PROXY_PASS}"

      enabled: true
```

## STIX/TAXII Configuration

### Popular TAXII Servers

#### CISA AIS (Automated Indicator Sharing)

```yaml
- name: "CISA AIS"
  url: "https://cisa.gov/taxii2/"
  collection_id: "your-collection-id"
  api_key: "${CISA_API_KEY}"
  poll_interval: 900
  filter:
    types: ["indicator", "malware"]
  enabled: true
```

**Registration**: https://www.cisa.gov/ais

#### Anomali ThreatStream

```yaml
- name: "Anomali ThreatStream"
  url: "https://api.threatstream.com/api/v1/taxii/"
  username: "${ANOMALI_USER}"
  api_key: "${ANOMALI_API_KEY}"
  collection_id: "your-collection"
  poll_interval: 1800
  enabled: true
```

#### AlienVault OTX

```yaml
- name: "AlienVault OTX"
  url: "https://otx.alienvault.com/taxii/"
  api_key: "${OTX_API_KEY}"
  collection_id: "xxx"
  poll_interval: 3600
  filter:
    types: ["indicator"]
    confidence_min: 70
  enabled: true
```

#### MISP

```yaml
- name: "MISP Threat Sharing"
  url: "https://misp.example.com/taxii2/"
  auth_type: "api_key"
  api_key: "${MISP_API_KEY}"
  verify_ssl: true
  poll_interval: 1800
  filter:
    tags: ["tlp:white", "tlp:green"]
    published_within_days: 30
  enabled: true
```

### Collection Discovery

```bash
# List available collections from a TAXII server
python -m cli.threat_cli discover-collections \
  --url https://cisa.gov/taxii2/ \
  --api-key $CISA_API_KEY

# Output:
# Available Collections:
# 1. collection-id-1: Indicators of Compromise
# 2. collection-id-2: Malware Analysis
# 3. collection-id-3: Threat Actors
```

### STIX Object Filtering

Filter specific STIX object types:

```yaml
filter:
  # STIX Domain Objects (SDO)
  types:
    - "indicator"           # Observable patterns
    - "malware"            # Malware details
    - "threat-actor"       # Threat actor profiles
    - "attack-pattern"     # ATT&CK techniques
    - "campaign"           # Attack campaigns
    - "course-of-action"   # Mitigations
    - "identity"           # Organizations/personas
    - "intrusion-set"      # Intrusion groups
    - "tool"               # Attack tools
    - "vulnerability"      # CVEs

  # STIX Relationship Objects (SRO)
  relationships:
    - "indicates"
    - "targets"
    - "uses"
    - "attributed-to"

  # Additional filters
  labels: ["malicious-activity", "attribution"]
  confidence_min: 60
  severity: ["high", "critical"]
  tlp: ["white", "green", "amber"]  # Traffic Light Protocol
```

## CVE Sources

### National Vulnerability Database (NVD)

```yaml
feeds:
  cve_sources:
    - name: "NVD"
      enabled: true
      url: "https://services.nvd.nist.gov/rest/json/cves/2.0"
      api_key: "${NVD_API_KEY}"

      # Update configuration
      update_interval: 3600  # 1 hour
      initial_sync_days: 365  # Full year on first run

      # Filtering
      filter:
        cvss_v3_min: 7.0  # High and Critical only
        status: ["Analyzed", "Modified"]
        cwe_ids: ["CWE-79", "CWE-89", "CWE-787"]  # Specific weakness types

      # Rate limiting (NVD has strict limits)
      requests_per_30_seconds: 5  # Without API key
      # requests_per_30_seconds: 50  # With API key

      # Storage
      cache_results: true
      cache_ttl: 86400  # 24 hours
```

**Get API Key**: https://nvd.nist.gov/developers/request-an-api-key

### OSV (Open Source Vulnerabilities)

```yaml
- name: "OSV"
  enabled: true
  url: "https://api.osv.dev/v1/"

  # Ecosystems to track
  ecosystems:
    - "PyPI"
    - "npm"
    - "Go"
    - "Rust"
    - "Maven"
    - "NuGet"
    - "Packagist"
    - "RubyGems"

  update_interval: 3600

  # Package-specific tracking
  tracked_packages:
    - ecosystem: "PyPI"
      packages: ["django", "flask", "requests"]
    - ecosystem: "npm"
      packages: ["express", "react", "vue"]
```

### GitHub Advisory Database

```yaml
- name: "GitHub Advisory"
  enabled: true
  url: "https://api.github.com/graphql"
  token: "${GITHUB_TOKEN}"

  ecosystems:
    - "pip"
    - "npm"
    - "composer"
    - "maven"
    - "nuget"
    - "rubygems"

  # Severity filtering
  severity: ["HIGH", "CRITICAL"]

  update_interval: 3600

  # GitHub-specific
  include_withdrawn: false
  published_since: "2024-01-01"
```

### CVE Search (Local Database)

```yaml
- name: "CVE-Search"
  enabled: true
  type: "local_database"

  # MongoDB connection (CVE-Search backend)
  mongodb:
    host: "localhost"
    port: 27017
    database: "cvedb"

  update_interval: 86400  # Daily

  # Sources to sync
  sources:
    - "nvd"
    - "redhat"
    - "debian"
    - "ubuntu"
```

### CVE Configuration Examples

#### Track Specific CVEs

```yaml
cve_sources:
  - name: "Critical CVE Tracking"
    type: "nvd"
    api_key: "${NVD_API_KEY}"

    # Track specific CVE IDs
    cve_ids:
      - "CVE-2024-1234"
      - "CVE-2024-5678"

    # Or track by keyword
    keywords:
      - "Apache"
      - "OpenSSL"
      - "Docker"

    alert_on_new: true
    notification_email: "security@example.com"
```

#### CVE with SBOM Correlation

```yaml
cve_sources:
  - name: "SBOM-Based CVE Tracking"
    type: "nvd"
    api_key: "${NVD_API_KEY}"

    # Automatically track CVEs for packages in SBOM
    sbom_file: "/path/to/sbom.json"
    sbom_format: "cyclonedx"

    # Re-scan SBOM for new CVEs
    sbom_rescan_interval: 3600

    # Alert on new matches
    alert_threshold: 7.0  # CVSS >= 7.0
```

## Custom Feed Formats

### JSON Feed

```yaml
feeds:
  custom_feeds:
    - name: "Custom JSON Feed"
      type: "json"
      url: "https://threat-intel.example.com/feed.json"

      # Authentication
      headers:
        Authorization: "Bearer ${CUSTOM_TOKEN}"
        X-API-Key: "${CUSTOM_API_KEY}"

      # Parsing configuration
      parser:
        root_path: "$.data.indicators"
        fields:
          indicator: "$.value"
          type: "$.type"
          confidence: "$.confidence"
          timestamp: "$.created_at"
          tags: "$.tags"

      # Transform to STIX
      stix_mapping:
        indicator_pattern: "indicator"
        pattern_type: "type"
        valid_from: "timestamp"
        labels: "tags"

      update_interval: 1800
      enabled: true
```

### XML Feed

```yaml
- name: "Custom XML Feed"
  type: "xml"
  url: "https://threat-intel.example.com/feed.xml"

  # XPath parsing
  parser:
    root_xpath: "//threat-feed/indicator"
    fields:
      indicator: "./value/text()"
      type: "./type/text()"
      confidence: "./confidence/text()"

  update_interval: 3600
  enabled: true
```

### CSV Feed

```yaml
- name: "CSV IOC Feed"
  type: "csv"
  url: "https://threat-intel.example.com/iocs.csv"

  # CSV configuration
  parser:
    delimiter: ","
    header_row: true
    columns:
      indicator: 0
      type: 1
      confidence: 2
      first_seen: 3
      last_seen: 4
      tags: 5

  update_interval: 3600
  enabled: true
```

### File-based Feed

```yaml
- name: "Network Share Feed"
  type: "file"
  path: "/mnt/threat-intel/feed.json"
  format: "json"

  # Watch for changes
  watch_mode: true

  # Or poll periodically
  poll_interval: 300

  enabled: true
```

### RSS/Atom Feed

```yaml
- name: "Security Blog Feed"
  type: "rss"
  url: "https://security-blog.example.com/feed.xml"

  # Content extraction
  extract_iocs: true
  extract_cves: true

  # Parse content with regex
  ioc_patterns:
    - pattern: '\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
      type: "ipv4-addr"
    - pattern: '\b[A-Fa-f0-9]{32}\b'
      type: "md5"
    - pattern: '\b[A-Fa-f0-9]{64}\b'
      type: "sha256"

  update_interval: 3600
  enabled: true
```

## Feed Authentication

### API Key Authentication

```yaml
auth_type: "api_key"
api_key: "${API_KEY}"

# Header-based
headers:
  X-API-Key: "${API_KEY}"

# Query parameter
auth_param: "api_key"
auth_value: "${API_KEY}"
```

### Basic Authentication

```yaml
auth_type: "basic"
username: "${USERNAME}"
password: "${PASSWORD}"
```

### Bearer Token

```yaml
auth_type: "bearer"
token: "${BEARER_TOKEN}"

# Or in headers
headers:
  Authorization: "Bearer ${BEARER_TOKEN}"
```

### OAuth 2.0

```yaml
auth_type: "oauth2"
oauth2:
  client_id: "${CLIENT_ID}"
  client_secret: "${CLIENT_SECRET}"
  token_url: "https://auth.example.com/oauth/token"
  grant_type: "client_credentials"
  scopes: ["read:threat-intel"]

  # Token caching
  cache_token: true
  token_refresh_before_expiry: 300  # 5 minutes
```

### Client Certificate

```yaml
auth_type: "certificate"
client_cert: "/path/to/client.crt"
client_key: "/path/to/client.key"
ca_bundle: "/path/to/ca-bundle.crt"
```

### JWT Authentication

```yaml
auth_type: "jwt"
jwt:
  secret: "${JWT_SECRET}"
  algorithm: "HS256"
  payload:
    iss: "threat-intel-platform"
    sub: "feed-ingestion"

  # Or use pre-generated token
  token: "${JWT_TOKEN}"
```

## Update Intervals

### Configuration Options

```yaml
feeds:
  stix_taxii:
    - name: "Real-time Feed"
      poll_interval: 300  # 5 minutes

    - name: "Hourly Feed"
      poll_interval: 3600  # 1 hour

    - name: "Daily Feed"
      poll_interval: 86400  # 24 hours

    - name: "On-demand Feed"
      poll_interval: 0  # Manual only
      auto_update: false
```

### Schedule-based Updates

```yaml
- name: "Scheduled Feed"
  schedule:
    type: "cron"
    expression: "0 */6 * * *"  # Every 6 hours
    timezone: "UTC"

- name: "Business Hours Feed"
  schedule:
    type: "cron"
    expression: "0 9-17 * * 1-5"  # 9 AM - 5 PM, Mon-Fri
    timezone: "America/New_York"
```

### Adaptive Polling

```yaml
- name: "Adaptive Feed"
  polling:
    mode: "adaptive"
    min_interval: 300   # 5 minutes
    max_interval: 3600  # 1 hour

    # Increase interval if no new data
    backoff_factor: 1.5

    # Reset to min_interval on new data
    reset_on_change: true
```

## Feed Filtering

### Content Filtering

```yaml
filter:
  # Type filtering
  types: ["indicator", "malware"]

  # Confidence threshold
  confidence_min: 60
  confidence_max: 100

  # Severity filtering
  severity: ["high", "critical"]

  # Date filtering
  created_after: "2024-01-01"
  modified_within_days: 30

  # Tag filtering
  include_tags: ["apt", "ransomware"]
  exclude_tags: ["false-positive", "test"]

  # Pattern filtering (regex)
  pattern_include:
    - ".*malware.*"
    - ".*apt[0-9]+.*"
  pattern_exclude:
    - ".*test.*"
    - ".*example.*"

  # Geographic filtering
  countries: ["CN", "RU", "KP", "IR"]

  # TLP filtering
  tlp: ["white", "green", "amber"]
```

### Deduplication

```yaml
deduplication:
  enabled: true

  # Dedup strategy
  strategy: "hash"  # or "fingerprint", "similarity"

  # Hash fields for comparison
  hash_fields:
    - "indicator"
    - "type"

  # Time window for deduplication
  window_hours: 24

  # Keep newest or oldest
  keep: "newest"  # or "oldest", "highest_confidence"
```

### Allowlist/Blocklist

```yaml
filtering:
  # Allowlist - only keep these
  allowlist:
    indicators:
      - "10.0.0.0/8"
      - "192.168.0.0/16"
    domains:
      - "*.example.com"

  # Blocklist - exclude these
  blocklist:
    indicators:
      - "127.0.0.1"
      - "0.0.0.0"
    domains:
      - "*.local"
      - "*.internal"
    hashes:
      - "d41d8cd98f00b204e9800998ecf8427e"  # Empty file MD5
```

## Best Practices

### Security

1. **Store Credentials Securely**
   ```yaml
   # Use environment variables
   api_key: "${API_KEY}"

   # Never commit credentials
   # Add to .gitignore: .env, threat-config.yaml
   ```

2. **Use TLS/SSL**
   ```yaml
   verify_ssl: true
   ca_bundle: "/etc/ssl/certs/ca-bundle.crt"
   ```

3. **Implement Rate Limiting**
   ```yaml
   rate_limit: 100  # per hour
   retry_on_rate_limit: true
   retry_delay: 300
   ```

### Performance

1. **Optimize Polling Intervals**
   - High-value feeds: 15-30 minutes
   - Standard feeds: 1-2 hours
   - Archive feeds: Daily

2. **Use Caching**
   ```yaml
   cache:
     enabled: true
     backend: "redis"
     ttl: 3600
   ```

3. **Batch Processing**
   ```yaml
   batch_size: 1000
   batch_timeout: 60
   parallel_feeds: 4
   ```

### Reliability

1. **Configure Retries**
   ```yaml
   retry:
     attempts: 3
     delay: 60
     backoff: "exponential"
     max_delay: 300
   ```

2. **Health Monitoring**
   ```bash
   # Monitor feed health
   python -m cli.threat_cli feed-health

   # Alert on failures
   python -m cli.threat_cli alert \
     --type feed-failure \
     --email ops@example.com
   ```

3. **Backup Feeds**
   ```yaml
   # Configure fallback feeds
   - name: "Primary Feed"
     url: "https://primary.example.com"
     fallback:
       - url: "https://backup.example.com"
       - url: "https://backup2.example.com"
   ```

### Data Quality

1. **Validate Data**
   ```yaml
   validation:
     enabled: true
     strict_mode: false  # Log warnings vs reject

     rules:
       - field: "indicator"
         required: true
         pattern: "^[a-zA-Z0-9.-]+$"
       - field: "confidence"
         range: [0, 100]
   ```

2. **Enrich Data**
   ```yaml
   enrichment:
     enabled: true
     services:
       - "virustotal"
       - "abuseipdb"
       - "shodan"
   ```

3. **Score Confidence**
   ```yaml
   confidence_scoring:
     enabled: true
     factors:
       - source_reputation: 0.4
       - age_decay: 0.2
       - validation_results: 0.4
   ```

### Maintenance

1. **Regular Feed Audits**
   ```bash
   # Review feed performance
   python -m cli.threat_cli feed-stats --days 30

   # Check for stale feeds
   python -m cli.threat_cli feed-health --check-stale
   ```

2. **Update Feed Configurations**
   ```bash
   # Test new configuration
   python -m cli.threat_cli test-config threat-config.yaml

   # Apply changes
   python -m cli.threat_cli reload-config
   ```

3. **Clean Up Old Data**
   ```yaml
   retention:
     enabled: true
     days: 365
     archive_before_delete: true
     archive_path: "/backup/threat-intel-archive"
   ```

## Testing Feed Configuration

```bash
# Test all feeds
python -m cli.threat_cli test-feeds

# Test specific feed
python -m cli.threat_cli test-feed --feed "CISA AIS"

# Validate configuration file
python -m cli.threat_cli validate-config threat-config.yaml

# Dry run ingestion
python -m cli.threat_cli ingest --dry-run --feed "CISA AIS"

# Check feed statistics
python -m cli.threat_cli feed-stats
```

## Example Configurations

See the [examples/](../examples/) directory for complete configuration examples:

- `threat-config-basic.yaml` - Minimal configuration
- `threat-config-enterprise.yaml` - Full-featured setup
- `threat-config-high-security.yaml` - Security-focused
- `threat-config-performance.yaml` - Performance-optimized

## Next Steps

- Configure [Threat Correlation](threat_correlation.md)
- Set up [SIEM Integration](siem_integration.md)
- Learn about [IOC Management](ioc_management.md)
