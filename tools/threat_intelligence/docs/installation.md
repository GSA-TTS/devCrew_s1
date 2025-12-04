# Installation Guide

Complete installation instructions for the Threat Intelligence Platform.

## Table of Contents

- [System Requirements](#system-requirements)
- [Python Environment Setup](#python-environment-setup)
- [Core Installation](#core-installation)
- [External Services Setup](#external-services-setup)
- [Configuration](#configuration)
- [Verification](#verification)
- [Docker Installation](#docker-installation)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 8GB
- Disk: 20GB free space
- Network: 10 Mbps

**Recommended:**
- CPU: 4+ cores
- RAM: 16GB+
- Disk: 100GB+ SSD
- Network: 100 Mbps

### Software Requirements

**Required:**
- Python 3.10 or higher
- pip or uv package manager
- Git

**Optional but Recommended:**
- Elasticsearch 8.11+ (for threat data storage)
- Redis 7.0+ (for caching)
- PostgreSQL 14+ (for metadata storage)
- Docker and Docker Compose (for containerized deployment)

### Operating System

Supported platforms:
- Linux (Ubuntu 20.04+, RHEL 8+, Debian 11+)
- macOS 11+ (Big Sur or later)
- Windows 10/11 with WSL2

## Python Environment Setup

### Using venv (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
.\venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Using conda

```bash
# Create conda environment
conda create -n threat-intel python=3.11

# Activate environment
conda activate threat-intel

# Install pip in conda environment
conda install pip
```

## Core Installation

### Clone Repository

```bash
# Clone devCrew_s1 repository
git clone https://github.com/your-org/devCrew_s1.git
cd devCrew_s1/tools/threat_intelligence
```

### Install Python Dependencies

```bash
# Standard installation
pip install -r requirements.txt

# Development installation (includes testing tools)
pip install -r requirements-dev.txt

# Using uv (faster)
uv pip install -r requirements.txt
```

### Verify Installation

```bash
# Check Python packages
pip list | grep -E "stix2|taxii2-client|elasticsearch"

# Test imports
python -c "import stix2; import taxii2client; print('Success!')"
```

## External Services Setup

### Elasticsearch (Recommended)

Elasticsearch is recommended for storing and querying threat intelligence data.

#### Docker Installation

```bash
# Pull Elasticsearch image
docker pull elasticsearch:8.11.0

# Run Elasticsearch
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms4g -Xmx4g" \
  elasticsearch:8.11.0

# Verify Elasticsearch is running
curl -X GET "localhost:9200/"
```

#### System Installation (Ubuntu/Debian)

```bash
# Import GPG key
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg

# Add repository
echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list

# Install Elasticsearch
sudo apt-get update && sudo apt-get install elasticsearch

# Start Elasticsearch
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch

# Verify
curl -X GET "localhost:9200/"
```

#### Configuration

Edit `/etc/elasticsearch/elasticsearch.yml`:

```yaml
cluster.name: threat-intel-cluster
node.name: threat-intel-node-1
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node

# Increase heap size for large datasets
# Edit /etc/elasticsearch/jvm.options
# -Xms4g
# -Xmx4g
```

### Redis (Optional - for Caching)

#### Docker Installation

```bash
# Pull Redis image
docker pull redis:7-alpine

# Run Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Verify Redis
redis-cli ping
```

#### System Installation (Ubuntu/Debian)

```bash
# Install Redis
sudo apt-get update
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify
redis-cli ping
```

### PostgreSQL (Optional - for Metadata)

#### Docker Installation

```bash
# Pull PostgreSQL image
docker pull postgres:15-alpine

# Run PostgreSQL
docker run -d \
  --name postgres \
  -p 5432:5432 \
  -e POSTGRES_DB=threat_intel \
  -e POSTGRES_USER=threat_user \
  -e POSTGRES_PASSWORD=secure_password \
  postgres:15-alpine

# Verify PostgreSQL
psql -h localhost -U threat_user -d threat_intel -c "SELECT version();"
```

#### System Installation (Ubuntu/Debian)

```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE threat_intel;
CREATE USER threat_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE threat_intel TO threat_user;
\q
EOF

# Verify
psql -h localhost -U threat_user -d threat_intel -c "SELECT version();"
```

## Configuration

### Create Configuration File

```bash
# Copy example configuration
cp threat-config.yaml.example threat-config.yaml

# Or create from scratch
cat > threat-config.yaml << 'EOF'
# Threat Intelligence Platform Configuration

feeds:
  stix_taxii:
    - name: "CISA AIS"
      url: "https://cisa.gov/taxii2/"
      collection_id: "your-collection-id"
      api_key: "${CISA_API_KEY}"
      poll_interval: 900

  cve_sources:
    - name: "NVD"
      enabled: true
      api_key: "${NVD_API_KEY}"

storage:
  backend: "elasticsearch"
  elasticsearch:
    hosts: ["localhost:9200"]
    index_prefix: "threat-intel"
    retention_days: 365

cache:
  enabled: true
  backend: "redis"
  redis:
    host: "localhost"
    port: 6379
    ttl: 3600

logging:
  level: "INFO"
  file: "/var/log/threat-intel/platform.log"
EOF
```

### Set Environment Variables

Create `.env` file:

```bash
cat > .env << 'EOF'
# API Keys
CISA_API_KEY=your-cisa-api-key
NVD_API_KEY=your-nvd-api-key
VT_API_KEY=your-virustotal-api-key
AIPDB_API_KEY=your-abuseipdb-api-key

# Database
DB_USER=threat_user
DB_PASS=secure_password

# SIEM Integration
SPLUNK_HEC_TOKEN=your-splunk-hec-token

# Optional
MISP_USER=your-misp-username
MISP_PASS=your-misp-password
EOF

# Load environment variables
export $(grep -v '^#' .env | xargs)
```

### Initialize Database

```bash
# Initialize the platform
python -m cli.threat_cli init

# This will:
# - Create necessary indices in Elasticsearch
# - Create tables in PostgreSQL (if configured)
# - Download MITRE ATT&CK data
# - Set up initial feed configurations
```

### Configure API Keys

#### NVD API Key (Required for CVE data)

1. Visit: https://nvd.nist.gov/developers/request-an-api-key
2. Request an API key
3. Add to `.env`: `NVD_API_KEY=your-key-here`

#### CISA AIS (Recommended)

1. Visit: https://www.cisa.gov/ais
2. Register for access
3. Obtain API key and collection ID
4. Add to `threat-config.yaml`

#### VirusTotal (Optional - for IOC enrichment)

1. Visit: https://www.virustotal.com/gui/join-us
2. Create account
3. Get API key from profile
4. Add to `.env`: `VT_API_KEY=your-key-here`

#### AbuseIPDB (Optional - for IP reputation)

1. Visit: https://www.abuseipdb.com/register
2. Create account
3. Get API key
4. Add to `.env`: `AIPDB_API_KEY=your-key-here`

## Verification

### Run System Check

```bash
# Check system status
python -m cli.threat_cli status

# Expected output:
# ✓ Python version: 3.11.x
# ✓ Elasticsearch: Connected (version 8.11.0)
# ✓ Redis: Connected
# ✓ PostgreSQL: Connected
# ✓ MITRE ATT&CK data: Downloaded
# ✓ Configuration: Valid
```

### Test Feed Connectivity

```bash
# Test all configured feeds
python -m cli.threat_cli test-feeds

# Test specific feed
python -m cli.threat_cli test-feed --feed cisa-ais

# Expected output:
# Testing CISA AIS feed...
# ✓ Connection successful
# ✓ Authentication successful
# ✓ Collection accessible
# ✓ Sample data retrieved
```

### Run Sample Ingestion

```bash
# Ingest small sample of data
python -m cli.threat_cli ingest --limit 100 --verbose

# Check ingestion results
python -m cli.threat_cli stats

# Expected output:
# Total indicators: 100
# STIX objects: 75
# CVEs: 25
# IOCs: 50
# Last update: 2024-12-04 10:30:00
```

### Verify Components

```bash
# Test each component
python -c "
from feeds.aggregator import FeedAggregator
from correlator.threat_correlator import ThreatCorrelator
from vex.vex_generator import VEXGenerator
from attack.attack_mapper import ATTACKMapper
from ioc.ioc_manager import IOCManager

print('All components imported successfully!')
"
```

## Docker Installation

For containerized deployment using Docker Compose.

### Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:8.11.0
    container_name: threat-intel-es
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms4g -Xmx4g"
    ports:
      - "9200:9200"
    volumes:
      - es-data:/usr/share/elasticsearch/data
    networks:
      - threat-intel

  redis:
    image: redis:7-alpine
    container_name: threat-intel-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - threat-intel

  postgres:
    image: postgres:15-alpine
    container_name: threat-intel-postgres
    environment:
      POSTGRES_DB: threat_intel
      POSTGRES_USER: threat_user
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - threat-intel

  threat-intel-platform:
    build: .
    container_name: threat-intel-platform
    depends_on:
      - elasticsearch
      - redis
      - postgres
    environment:
      - ELASTICSEARCH_HOSTS=elasticsearch:9200
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
    env_file:
      - .env
    volumes:
      - ./threat-config.yaml:/app/threat-config.yaml
      - ./data:/app/data
    networks:
      - threat-intel
    command: ["python", "-m", "cli.threat_cli", "ingest", "--daemon"]

volumes:
  es-data:
  redis-data:
  postgres-data:

networks:
  threat-intel:
    driver: bridge
```

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/data /var/log/threat-intel

# Initialize platform
RUN python -m cli.threat_cli init

EXPOSE 8080

CMD ["python", "-m", "cli.threat_cli", "serve"]
```

### Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f threat-intel-platform

# Check status
docker-compose ps

# Stop services
docker-compose down
```

## Post-Installation Tasks

### Set Up Scheduled Ingestion

#### Using Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add ingestion job (every 15 minutes)
*/15 * * * * cd /path/to/devCrew_s1/tools/threat_intelligence && /path/to/venv/bin/python -m cli.threat_cli ingest --all >> /var/log/threat-intel/cron.log 2>&1

# Add daily report
0 6 * * * cd /path/to/devCrew_s1/tools/threat_intelligence && /path/to/venv/bin/python -m cli.threat_cli report --report-type daily-summary >> /var/log/threat-intel/report.log 2>&1
```

#### Using systemd (Linux)

Create `/etc/systemd/system/threat-intel-ingestion.service`:

```ini
[Unit]
Description=Threat Intelligence Ingestion
After=network.target elasticsearch.service

[Service]
Type=simple
User=threat-intel
WorkingDirectory=/opt/devCrew_s1/tools/threat_intelligence
Environment="PATH=/opt/devCrew_s1/tools/threat_intelligence/venv/bin"
ExecStart=/opt/devCrew_s1/tools/threat_intelligence/venv/bin/python -m cli.threat_cli ingest --daemon --interval 900
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable threat-intel-ingestion
sudo systemctl start threat-intel-ingestion
sudo systemctl status threat-intel-ingestion
```

### Configure Log Rotation

Create `/etc/logrotate.d/threat-intel`:

```
/var/log/threat-intel/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 threat-intel threat-intel
    sharedscripts
    postrotate
        systemctl reload threat-intel-ingestion > /dev/null 2>&1 || true
    endscript
}
```

### Set Up Monitoring

```bash
# Add health check endpoint
curl http://localhost:8080/health

# Monitor ingestion metrics
python -m cli.threat_cli metrics --watch

# Set up alerts (example with email)
python -m cli.threat_cli alert \
  --type email \
  --recipient security-team@example.com \
  --severity high,critical
```

## Troubleshooting

### Common Installation Issues

#### Issue: pip install fails with compilation errors

```bash
# Install build dependencies
# Ubuntu/Debian
sudo apt-get install python3-dev build-essential

# RHEL/CentOS
sudo yum install python3-devel gcc gcc-c++

# macOS
xcode-select --install
```

#### Issue: Elasticsearch connection refused

```bash
# Check if Elasticsearch is running
curl -X GET "localhost:9200/"

# Check logs
docker logs elasticsearch
# or
sudo journalctl -u elasticsearch

# Verify configuration
cat threat-config.yaml | grep -A5 elasticsearch
```

#### Issue: Redis connection timeout

```bash
# Check Redis status
redis-cli ping

# Check Redis logs
docker logs redis
# or
sudo journalctl -u redis

# Test connection
redis-cli -h localhost -p 6379 ping
```

#### Issue: Import errors for stix2 or taxii2client

```bash
# Reinstall with force
pip install --force-reinstall stix2 taxii2-client

# Check installed versions
pip show stix2 taxii2-client
```

#### Issue: Permission denied errors

```bash
# Create directories with correct permissions
sudo mkdir -p /var/log/threat-intel
sudo chown -R $USER:$USER /var/log/threat-intel
chmod 755 /var/log/threat-intel
```

### Verify Installation Checklist

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] All Python packages installed
- [ ] Elasticsearch running and accessible
- [ ] Redis running (if caching enabled)
- [ ] PostgreSQL running (if configured)
- [ ] Configuration file created and valid
- [ ] Environment variables set
- [ ] API keys configured
- [ ] Database initialized
- [ ] Feed connectivity tested
- [ ] Sample ingestion successful
- [ ] Component imports working

### Get Help

If you encounter issues not covered here:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review logs: `/var/log/threat-intel/platform.log`
3. Enable debug logging: `--log-level DEBUG`
4. Check GitHub issues
5. Contact support team

## Next Steps

After successful installation:

1. Review [Feed Configuration Guide](feed_configuration.md)
2. Set up your threat intelligence feeds
3. Configure asset inventory
4. Run initial threat correlation
5. Set up SIEM integration
6. Schedule regular reports

## Upgrading

To upgrade to a newer version:

```bash
# Backup configuration
cp threat-config.yaml threat-config.yaml.backup

# Pull latest code
cd /path/to/devCrew_s1
git pull origin master

# Update dependencies
cd tools/threat_intelligence
pip install --upgrade -r requirements.txt

# Run database migrations (if any)
python -m cli.threat_cli migrate

# Restart services
sudo systemctl restart threat-intel-ingestion
```
