# DevGRU Setup - Quick Start Guide

## Installation in 3 Steps

### Step 1: Install Prerequisites

```bash
# macOS
brew install jq curl git

# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y jq curl git

# RHEL/CentOS/Fedora
sudo yum install -y jq curl git
```

### Step 2: Run Setup Script

```bash
# Navigate to devgru_setup directory
cd /path/to/devCrew_s1/devgru_setup

# Make script executable (if needed)
chmod +x setup_devgru.sh

# Run with default profile (standard)
./setup_devgru.sh
```

### Step 3: Verify Installation

```bash
# Check Python version
python3 --version

# List installed packages
pip list | grep -E "pandas|requests|pydantic|celery|playwright"
```

## Profile Quick Reference

| Profile | Command | Packages | Use Case |
|---------|---------|----------|----------|
| **Minimal** | `--profile minimal` | 5 core packages | Lightweight dev/CI |
| **Standard** | `--profile standard` | 20 packages | General development |
| **Full** | `--profile full` | All + databases + tools | Complete stack |
| **Security** | `--profile security` | Standard + security tools | Security auditing |
| **AWS** | `--profile cloud-aws` | Standard + AWS SDK | AWS development |
| **Azure** | `--profile cloud-azure` | Standard + Azure SDK | Azure development |
| **GCP** | `--profile cloud-gcp` | Standard + GCP SDK | GCP development |

## Common Commands

```bash
# Test before installing
./setup_devgru.sh --profile full --dry-run

# Install with verbose output
./setup_devgru.sh --profile standard --verbose

# Install without databases
./setup_devgru.sh --profile full --skip-databases

# Install without external tools
./setup_devgru.sh --profile full --skip-tools

# Show help
./setup_devgru.sh --help
```

## What Gets Installed?

### Minimal Profile
- Python 3.10+
- pandas, requests, pydantic, celery, playwright

### Standard Profile (Default)
- Everything in Minimal +
- fastapi, sqlalchemy, pytest, langchain, spacy
- beautifulsoup4, scrapy, docker, kubernetes
- safety, bandit, checkov
- numpy, sentence-transformers, chromadb

### Full Profile
- Everything in Standard +
- Databases: Redis, PostgreSQL, Neo4j
- Tools: Docker, Terraform, Trivy, Node.js, Airflow

### Cloud Profiles
- Standard packages +
- Cloud-specific SDKs (boto3, azure-*, google-cloud-*)
- Cloud CLI tools (aws, az, gcloud)

## Troubleshooting

### Script won't run
```bash
chmod +x setup_devgru.sh
```

### Missing prerequisites
```bash
# Install jq, curl, git first (see Step 1)
```

### Installation fails
```bash
# Check logs
cat logs/setup_*.log | tail -50

# Try with verbose mode
./setup_devgru.sh --profile standard --verbose
```

### Want to rollback
The script will prompt for rollback on error. Or manually:
```bash
pip uninstall -y package_name
```

## File Locations

- **Script**: `./setup_devgru.sh`
- **Logs**: `./logs/setup_YYYYMMDD_HHMMSS.log`
- **Reports**: `./logs/installation_report_YYYYMMDD_HHMMSS.txt`
- **State**: `./.state/installation_state.json`

## Post-Installation

### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

### Configure Cloud Providers
```bash
# AWS
aws configure

# Azure
az login

# GCP
gcloud auth login
```

### Start Databases (Full Profile)
```bash
# macOS
brew services start redis
brew services start postgresql

# Linux
sudo systemctl start redis
sudo systemctl start postgresql
```

## Examples

### Example 1: Quick Standard Setup
```bash
./setup_devgru.sh
```

### Example 2: AWS Development
```bash
./setup_devgru.sh --profile cloud-aws
aws configure
```

### Example 3: Security Auditing
```bash
./setup_devgru.sh --profile security
safety check
bandit -r .
```

### Example 4: Testing First
```bash
./setup_devgru.sh --profile full --dry-run
# Review output, then:
./setup_devgru.sh --profile full
```

## Need More Help?

- Full documentation: `README.md`
- Help command: `./setup_devgru.sh --help`
- Logs: `cat logs/setup_*.log`
- GitHub Issues: Report problems at repository issues page
