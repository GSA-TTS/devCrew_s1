# Troubleshooting Guide

Common issues and solutions for the Threat Intelligence Platform.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Feed Ingestion Problems](#feed-ingestion-problems)
- [Performance Issues](#performance-issues)
- [Storage Issues](#storage-issues)
- [API Issues](#api-issues)
- [Integration Issues](#integration-issues)
- [Debug Mode](#debug-mode)

## Installation Issues

### Python Package Installation Fails

**Symptom**: pip install fails with compilation errors

**Solutions**:

```bash
# Install build dependencies
# Ubuntu/Debian
sudo apt-get install python3-dev build-essential libssl-dev libffi-dev

# RHEL/CentOS
sudo yum install python3-devel gcc gcc-c++ openssl-devel libffi-devel

# macOS
xcode-select --install

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Retry installation
pip install -r requirements.txt
```

### Import Errors

**Symptom**: `ModuleNotFoundError` or `ImportError`

**Solutions**:

```bash
# Verify virtual environment is activated
which python  # Should show venv path

# Reinstall specific package
pip install --force-reinstall stix2 taxii2-client

# Check installed packages
pip list | grep -E "stix2|taxii2|elasticsearch"

# Test imports
python -c "import stix2, taxii2client, elasticsearch; print('Success')"
```

### Permission Denied Errors

**Symptom**: Cannot write to log directory or data directory

**Solutions**:

```bash
# Create directories with correct permissions
sudo mkdir -p /var/log/threat-intel
sudo chown -R $USER:$USER /var/log/threat-intel
chmod 755 /var/log/threat-intel

# Or use user-local directories
# Edit threat-config.yaml
logging:
  file: "$HOME/.threat-intel/platform.log"
```

## Feed Ingestion Problems

### Feed Connection Timeout

**Symptom**: `ConnectionTimeout` or `ConnectTimeout` errors

**Diagnosis**:

```bash
# Test network connectivity
curl -I https://cisa.gov/taxii2/

# Check DNS resolution
nslookup cisa.gov

# Test with increased timeout
python -m cli.threat_cli test-feed \
  --feed cisa-ais \
  --timeout 300 \
  --verbose
```

**Solutions**:

```yaml
# Increase timeout in config
feeds:
  stix_taxii:
    - name: "CISA AIS"
      connection_timeout: 300
      read_timeout: 600
```

### Authentication Failures

**Symptom**: `401 Unauthorized` or `403 Forbidden` errors

**Diagnosis**:

```bash
# Verify credentials
python -m cli.threat_cli verify-credentials

# Test API key
curl -H "Authorization: Bearer $CISA_API_KEY" \
  https://cisa.gov/taxii2/

# Enable debug logging
export LOG_LEVEL=DEBUG
python -m cli.threat_cli ingest --feed cisa-ais
```

**Solutions**:

```bash
# Regenerate API key
# Visit feed provider website and regenerate

# Update .env file
echo "CISA_API_KEY=new-key-here" >> .env

# Reload configuration
python -m cli.threat_cli reload-config

# Test again
python -m cli.threat_cli test-feed --feed cisa-ais
```

### SSL Certificate Errors

**Symptom**: `SSLError` or certificate verification failed

**Solutions**:

```yaml
# Option 1: Update CA certificates
# Ubuntu/Debian
sudo apt-get install ca-certificates
sudo update-ca-certificates

# Option 2: Provide custom CA bundle
feeds:
  stix_taxii:
    - name: "Custom Feed"
      verify_ssl: true
      ca_bundle: "/path/to/ca-bundle.crt"

# Option 3: Disable SSL verification (NOT RECOMMENDED for production)
feeds:
  stix_taxii:
    - name: "Internal Feed"
      verify_ssl: false
```

### Rate Limiting

**Symptom**: `429 Too Many Requests` errors

**Solutions**:

```yaml
# Configure rate limiting
feeds:
  stix_taxii:
    - name: "NVD"
      rate_limit: 5  # requests per 30 seconds
      retry_on_rate_limit: true
      retry_delay: 60
      max_retries: 3

# Use exponential backoff
feeds:
  stix_taxii:
    - name: "External Feed"
      retry:
        strategy: "exponential"
        base_delay: 30
        max_delay: 300
```

### No Data Retrieved

**Symptom**: Feed ingests successfully but no indicators stored

**Diagnosis**:

```bash
# Check feed data
python -m cli.threat_cli ingest \
  --feed cisa-ais \
  --dry-run \
  --verbose

# Verify filters
python -m cli.threat_cli config-check \
  --show-filters

# Check storage
python -m cli.threat_cli stats
```

**Solutions**:

```yaml
# Review and adjust filters
feeds:
  stix_taxii:
    - name: "Feed"
      filter:
        confidence_min: 50  # Was 90, now lower
        types: []  # Empty = accept all types
```

## Performance Issues

### Slow Ingestion

**Symptom**: Feed ingestion takes hours

**Diagnosis**:

```bash
# Enable profiling
python -m cProfile -o ingestion.prof \
  -m cli.threat_cli ingest --feed cisa-ais

# Analyze profile
python -m pstats ingestion.prof
# In pstats shell:
# sort cumulative
# stats 20

# Check resource usage
top -p $(pgrep -f threat_cli)
```

**Solutions**:

```yaml
# Increase batch size
feeds:
  stix_taxii:
    - name: "Feed"
      batch_size: 5000  # Was 1000
      parallel_processing: true
      max_workers: 4

# Enable caching
cache:
  enabled: true
  backend: "redis"
  redis:
    host: "localhost"
    port: 6379
    ttl: 3600
```

```bash
# Use bulk operations
python -m cli.threat_cli ingest \
  --batch-mode \
  --batch-size 5000
```

### High Memory Usage

**Symptom**: Process using excessive RAM

**Solutions**:

```python
# Process in chunks
def process_large_feed(feed_data):
    chunk_size = 1000
    for i in range(0, len(feed_data), chunk_size):
        chunk = feed_data[i:i+chunk_size]
        process_chunk(chunk)
        # Force garbage collection
        import gc
        gc.collect()
```

```yaml
# Limit concurrent operations
processing:
  max_workers: 2  # Reduce from 4
  chunk_size: 500  # Reduce from 1000
```

### Slow Queries

**Symptom**: Elasticsearch queries timeout

**Solutions**:

```bash
# Optimize Elasticsearch
# Increase heap size in /etc/elasticsearch/jvm.options
-Xms8g
-Xmx8g

# Adjust refresh interval
curl -X PUT "localhost:9200/threat-intel-*/_settings" -H 'Content-Type: application/json' -d'
{
  "index": {
    "refresh_interval": "30s"
  }
}
'

# Add indices
curl -X PUT "localhost:9200/threat-intel-*/_settings" -H 'Content-Type: application/json' -d'
{
  "index": {
    "number_of_replicas": 0
  }
}
'
```

## Storage Issues

### Elasticsearch Connection Failed

**Symptom**: Cannot connect to Elasticsearch

**Diagnosis**:

```bash
# Check if Elasticsearch is running
curl -X GET "localhost:9200/"

# Check logs
sudo journalctl -u elasticsearch -f

# Test connection from Python
python -c "from elasticsearch import Elasticsearch; es = Elasticsearch(['localhost:9200']); print(es.info())"
```

**Solutions**:

```bash
# Start Elasticsearch
sudo systemctl start elasticsearch

# Check configuration
cat /etc/elasticsearch/elasticsearch.yml

# Verify network binding
# In elasticsearch.yml:
network.host: 0.0.0.0
http.port: 9200
```

### Disk Space Full

**Symptom**: `No space left on device`

**Solutions**:

```bash
# Check disk usage
df -h

# Check Elasticsearch indices size
curl -X GET "localhost:9200/_cat/indices?v&h=index,store.size"

# Delete old indices
curl -X DELETE "localhost:9200/threat-intel-2023-*"

# Configure retention
python -m cli.threat_cli cleanup \
  --retention-days 365 \
  --archive-path /backup/threat-intel
```

```yaml
# Auto-cleanup configuration
storage:
  elasticsearch:
    retention_days: 365
    auto_cleanup: true
    cleanup_schedule: "0 2 * * *"  # Daily at 2 AM
```

### Redis Connection Issues

**Symptom**: Cannot connect to Redis cache

**Solutions**:

```bash
# Check Redis status
redis-cli ping

# Start Redis
sudo systemctl start redis

# Test connection
redis-cli -h localhost -p 6379 ping

# Disable caching if not needed
# In threat-config.yaml:
cache:
  enabled: false
```

## API Issues

### API Not Responding

**Symptom**: API endpoints return timeout

**Diagnosis**:

```bash
# Check if API server is running
ps aux | grep threat_cli

# Check listening ports
netstat -tlnp | grep 8080

# Test API endpoint
curl -X GET http://localhost:8080/api/v1/health
```

**Solutions**:

```bash
# Start API server
python -m cli.threat_cli serve \
  --host 0.0.0.0 \
  --port 8080 \
  --workers 4

# Check logs
tail -f /var/log/threat-intel/api.log

# Restart service
sudo systemctl restart threat-intel-api
```

### API Authentication Failures

**Symptom**: `401 Unauthorized` on API calls

**Solutions**:

```bash
# Generate new API key
python -m cli.threat_cli api-key create \
  --name "client-1" \
  --output api_key.txt

# Test with API key
curl -X GET http://localhost:8080/api/v1/iocs \
  -H "Authorization: Bearer $(cat api_key.txt)"

# Verify API key
python -m cli.threat_cli api-key verify $(cat api_key.txt)
```

## Integration Issues

### SIEM Integration Not Working

**Symptom**: No data appearing in SIEM

**Diagnosis**:

```bash
# Test SIEM connectivity
python -m cli.threat_cli siem-test --target splunk --verbose

# Check SIEM logs
# Splunk
index=_internal sourcetype=splunkd "HEC" | stats count by status

# Send test event
python -c "
from integrations.siem.splunk import SplunkIntegration
splunk = SplunkIntegration('https://splunk:8088', 'token')
splunk.send_event({'test': 'data'})
"
```

**Solutions**:

```bash
# Verify HEC token
curl -k https://splunk.example.com:8088/services/collector \
  -H "Authorization: Splunk YOUR-TOKEN" \
  -d '{"event":"test"}'

# Check index exists
# In Splunk: | eventcount summarize=false index=threat_intelligence

# Enable debug logging
export LOG_LEVEL=DEBUG
python -m cli.threat_cli siem-forward --target splunk
```

### VEX Generation Fails

**Symptom**: VEX document generation errors

**Solutions**:

```bash
# Validate input data
python -m cli.threat_cli validate-vulnerabilities vuln_list.json

# Generate with verbose output
python -m cli.threat_cli vex \
  --product "myapp:2.1.0" \
  --vulnerabilities vuln_list.json \
  --format openvex \
  --verbose \
  --output vex.json

# Validate generated VEX
python -m cli.threat_cli validate-vex vex.json --format openvex
```

## Debug Mode

### Enable Debug Logging

```bash
# Environment variable
export LOG_LEVEL=DEBUG

# Command line
python -m cli.threat_cli ingest --log-level DEBUG

# Configuration file
# threat-config.yaml
logging:
  level: "DEBUG"
  file: "/var/log/threat-intel/debug.log"
```

### Verbose Output

```bash
# Add --verbose flag to any command
python -m cli.threat_cli ingest --verbose
python -m cli.threat_cli correlate --assets assets.json --verbose
python -m cli.threat_cli ioc extract --verbose
```

### Debug Python Code

```python
# Add debugging breakpoint
import pdb; pdb.set_trace()

# Or use ipdb for better interface
import ipdb; ipdb.set_trace()

# Enable verbose logging in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Capture Network Traffic

```bash
# For debugging feed issues
tcpdump -i any -w feed_traffic.pcap host cisa.gov

# Analyze with Wireshark or tcpdump
tcpdump -r feed_traffic.pcap -A
```

## Common Error Messages

### "STIX object validation failed"

**Cause**: Invalid STIX object structure

**Solution**:
```bash
# Enable validation in debug mode
python -m cli.threat_cli ingest \
  --feed cisa-ais \
  --validate-stix \
  --log-invalid \
  --verbose
```

### "CVE not found in NVD"

**Cause**: CVE doesn't exist or NVD not synced

**Solution**:
```bash
# Force NVD sync
python -m cli.threat_cli sync-nvd --force

# Check CVE existence
curl "https://services.nvd.nist.gov/rest/json/cves/2.0/CVE-2024-1234"
```

### "Correlation timeout"

**Cause**: Large asset inventory or slow storage

**Solution**:
```yaml
# Increase timeout
correlation:
  timeout: 600  # 10 minutes
  batch_size: 100  # Process in smaller batches
```

### "Enrichment service rate limit"

**Cause**: Too many enrichment requests

**Solution**:
```python
# Add delay between requests
from ioc.enrichers.virustotal import VirusTotalEnricher
vt = VirusTotalEnricher(
    api_key="key",
    rate_limit=4,  # 4 requests per minute
    delay_between_requests=15  # seconds
)
```

## Getting Help

### Collect Debug Information

```bash
# Generate debug report
python -m cli.threat_cli debug-report \
  --output debug_report.zip

# Includes:
# - System information
# - Configuration (sanitized)
# - Recent logs
# - Error traces
# - Metrics
```

### Check System Status

```bash
# Comprehensive status check
python -m cli.threat_cli status --detailed

# Output:
# ✓ Python version: 3.11.x
# ✓ Elasticsearch: Connected (8.11.0)
# ✓ Redis: Connected
# ✓ Feed health: 5/6 feeds OK
# ✗ SIEM integration: Connection failed
# ✓ Disk space: 45% used
# ✓ Memory: 2.1GB / 8GB
```

### Test Configuration

```bash
# Validate configuration file
python -m cli.threat_cli validate-config threat-config.yaml

# Test all integrations
python -m cli.threat_cli test-all
```

## Performance Tuning

### Optimize Elasticsearch

```bash
# Increase JVM heap
# /etc/elasticsearch/jvm.options
-Xms8g
-Xmx8g

# Optimize index settings
curl -X PUT "localhost:9200/threat-intel-*/_settings" -H 'Content-Type: application/json' -d'
{
  "index": {
    "refresh_interval": "30s",
    "number_of_replicas": 0,
    "translog.durability": "async",
    "translog.sync_interval": "30s"
  }
}
'
```

### Optimize Redis

```bash
# /etc/redis/redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
save ""
```

### Optimize Python

```python
# Use connection pooling
from elasticsearch import Elasticsearch
es = Elasticsearch(
    ['localhost:9200'],
    max_retries=3,
    retry_on_timeout=True,
    maxsize=25  # Connection pool size
)

# Enable bulk operations
from elasticsearch.helpers import bulk
bulk(es, actions, chunk_size=1000)
```

## Support Resources

- **Documentation**: `/docs/`
- **GitHub Issues**: Create issue with debug report
- **Logs**: `/var/log/threat-intel/`
- **Configuration**: `threat-config.yaml`

## Preventive Measures

1. **Regular Monitoring**
   ```bash
   # Set up monitoring
   python -m cli.threat_cli monitor --daemon
   ```

2. **Health Checks**
   ```bash
   # Add to cron
   0 */6 * * * /path/to/threat_cli status --alert-on-failure
   ```

3. **Log Rotation**
   ```bash
   # /etc/logrotate.d/threat-intel
   /var/log/threat-intel/*.log {
       daily
       rotate 30
       compress
       delaycompress
       notifempty
       create 0640 threat-intel threat-intel
   }
   ```

4. **Backup Configuration**
   ```bash
   # Backup script
   tar -czf threat-intel-backup-$(date +%Y%m%d).tar.gz \
     threat-config.yaml \
     .env \
     /var/lib/threat-intel/
   ```

## Next Steps

After resolving issues:

- Review [Installation Guide](installation.md) for setup verification
- Check [Feed Configuration](feed_configuration.md) for optimal settings
- Consult [Performance Guide](../README.md#performance) for tuning tips
