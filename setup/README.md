# DevGRU Multi-OS Prerequisites Setup Script

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/devCrew_s1)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20WSL2-lightgrey.svg)](#supported-operating-systems)
[![Shell](https://img.shields.io/badge/shell-bash-orange.svg)](setup_devgru.sh)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](#prerequisites)

> **Automated, multi-OS development environment setup for DevGRU projects**
> Created for GitHub Issue #67 - Multi-OS Prerequisites Setup Script

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation Profiles](#installation-profiles)
- [Platform Support](#platform-support)
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Command-Line Options](#command-line-options)
- [Directory Structure](#directory-structure)
- [Logging and State Management](#logging-and-state-management)
- [Error Handling and Rollback](#error-handling-and-rollback)
- [Post-Installation Steps](#post-installation-steps)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Contributing](#contributing)
- [Version History](#version-history)
- [Support](#support)

## Overview

The `setup_devgru.sh` script provides **automated, intelligent, and robust installation** of development prerequisites for the DevGRU project across multiple operating systems. It eliminates the tedium of manual setup by detecting your system configuration and installing the appropriate packages, databases, and tools needed for development.

### Key Capabilities

- **Multi-OS Support**: Automatically detects and adapts to macOS (Intel/Apple Silicon), Linux (Ubuntu, Debian, RHEL, CentOS, Fedora), and Windows WSL2
- **Profile-Based Installation**: Choose from 7 pre-configured profiles tailored to different development scenarios
- **Intelligent Package Management**: Uses native package managers (Homebrew, apt, yum/dnf) for optimal compatibility
- **Safety First**: Dry-run mode, comprehensive logging, and automatic rollback on failures
- **State Tracking**: JSON-based tracking of all installed packages for easy auditing and management

### What Makes This Different

Unlike manual installation instructions or simple shell scripts, this setup script provides:

1. **Idempotency**: Safe to run multiple times without duplicating installations
2. **Comprehensive Error Handling**: Catches errors, provides clear messages, and offers rollback
3. **Detailed Logging**: Every operation is logged with timestamps for debugging and audit trails
4. **Flexible Profiles**: From minimal CI/CD environments to full-stack development setups
5. **Cloud-Ready**: Built-in support for AWS, Azure, and GCP development workflows

## Features

### Core Features

- **Multi-OS Detection**: Automatically identifies OS type, version, and architecture
- **7 Installation Profiles**: Minimal, Standard, Full, Security, Cloud-AWS, Cloud-Azure, Cloud-GCP
- **Dry-Run Mode**: Preview installations without making any system changes
- **Rollback Capability**: Automatic rollback on failures with manual override options
- **Comprehensive Logging**: Timestamped logs with INFO, SUCCESS, WARNING, ERROR, and DEBUG levels
- **State Tracking**: JSON-based installation state for monitoring and auditing
- **Error Recovery**: Robust error detection with clear, actionable error messages
- **Package Manager Updates**: Automatically updates package managers before installations
- **Skip Options**: Granular control with `--skip-databases` and `--skip-tools` flags
- **Verbose Mode**: Detailed debug output for troubleshooting complex issues

### Advanced Features

- **Intelligent Package Detection**: Checks if packages are already installed to avoid redundant operations
- **Architecture Awareness**: Handles x86_64 and ARM64 architectures seamlessly
- **WSL2 Detection**: Identifies and adapts to Windows Subsystem for Linux environments
- **Signal Handling**: Graceful handling of interrupts (SIGINT, SIGTERM)
- **Modular Design**: Organized into focused functions for maintainability
- **JSON Configuration**: Uses validated prerequisites from `/tmp/issue67_work/prerequisites_validated.json`

## Quick Start

### 1. Install Prerequisites

The script requires three tools: `jq`, `curl`, and `git`. Install them using your system's package manager:

**macOS**:
```bash
brew install jq curl git
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y jq curl git
```

**RHEL/CentOS/Fedora**:
```bash
sudo yum install -y jq curl git
```

### 2. Run Setup Script

```bash
# Navigate to setup directory
cd /Users/tamnguyen/Documents/GitHub/devCrew_s1/setup

# Make script executable (if needed)
chmod +x setup_devgru.sh

# Run with default profile (standard)
./setup_devgru.sh
```

### 3. Verify Installation

```bash
# Check Python version
python3 --version

# List installed packages
pip list

# Verify core packages
python3 -c "import pandas, requests, pydantic, celery, playwright; print('Installation successful!')"
```

See [QUICK_START.md](QUICK_START.md) for more quick reference information.

## Installation Profiles

The script offers 7 pre-configured profiles tailored to different development scenarios. Each profile builds upon the previous one, adding more packages and tools.

### Profile Comparison Table

| Profile | Python | Core Packages | Optional Packages | Databases | External Tools | Cloud SDKs | Use Case |
|---------|--------|---------------|-------------------|-----------|----------------|------------|----------|
| **minimal** | 3.10+ | 5 | 0 | 0 | 0 | 0 | Lightweight dev/CI |
| **standard** | 3.10+ | 5 | 15 | 0 | 0 | 0 | General development |
| **full** | 3.10+ | 5 | 15 | 3 | 5 | 0 | Complete stack |
| **security** | 3.10+ | 5 | 15+ | 0 | 0 | 0 | Security auditing |
| **cloud-aws** | 3.10+ | 5 | 15 | 0 | 0 | AWS | AWS development |
| **cloud-azure** | 3.10+ | 5 | 15 | 0 | 0 | Azure | Azure development |
| **cloud-gcp** | 3.10+ | 5 | 15 | 0 | 0 | GCP | GCP development |

### 1. Minimal Profile

**Command**: `./setup_devgru.sh --profile minimal`

Installs **Python 3.10+** and **5 core packages**:
- `pandas` (>=2.0) - Data manipulation and analysis
- `requests` (>=2.31) - HTTP library
- `pydantic` (>=2.5) - Data validation using Python type hints
- `celery` (>=5.3.4) - Distributed task queue
- `playwright` (>=1.40) - Browser automation

**Use Case**: Lightweight development environments, CI/CD pipelines, containerized applications

**Installation Time**: ~3-5 minutes
**Disk Space**: ~500 MB

### 2. Standard Profile (Default)

**Command**: `./setup_devgru.sh --profile standard` or `./setup_devgru.sh`

Includes **Minimal** + **15 optional packages**:

**Web Development**:
- `fastapi` (>=0.104) - Modern web framework
- `beautifulsoup4` (>=4.12) - HTML/XML parsing
- `scrapy` (>=2.11) - Web scraping framework

**Data Science**:
- `numpy` (>=1.24) - Numerical computing
- `sentence-transformers` (>=2.2) - Sentence embeddings
- `chromadb` (>=0.4) - Vector database

**DevOps & Infrastructure**:
- `docker` (>=7.0) - Docker SDK
- `kubernetes` (>=1.27) - Kubernetes client
- `terraform` - Infrastructure as Code (via external tool)

**Testing & Quality**:
- `pytest` (>=7.4) - Testing framework
- `safety` (>=3.0) - Dependency vulnerability scanning
- `bandit` (>=1.7.5) - Security linter
- `checkov` (>=3.1) - Infrastructure security scanning

**AI & NLP**:
- `langchain` (>=0.1) - LLM application framework
- `spacy` (>=3.7) - Natural language processing

**Database**:
- `sqlalchemy` (>=2.0) - SQL toolkit and ORM

**Use Case**: Full-featured local development, most common development scenarios

**Installation Time**: ~10-15 minutes
**Disk Space**: ~2 GB

### 3. Full Profile

**Command**: `./setup_devgru.sh --profile full`

Includes **Standard** + **databases** + **external tools**:

**Databases**:
- **Redis** (7.2+) - In-memory data store
- **PostgreSQL** (15.0+) - Relational database
- **Neo4j** (5.15+) - Graph database (manual installation required)

**External Tools**:
- **Docker** (24.0+) - Container platform (manual installation required)
- **Terraform** (1.6+) - Infrastructure as Code
- **Trivy** (0.48+) - Security scanner
- **Node.js** (18+) - JavaScript runtime
- **Airflow** (2.7+) - Workflow orchestration (installed via pip in venv)

**Use Case**: Complete development stack with infrastructure, data engineering, full-stack applications

**Installation Time**: ~20-30 minutes
**Disk Space**: ~5 GB

### 4. Security Profile

**Command**: `./setup_devgru.sh --profile security`

Includes **Standard** + **enhanced security tools**:

**Security Scanning**:
- `safety` - Checks Python dependencies for known security vulnerabilities
- `bandit` - Python security linter for identifying common security issues
- `checkov` - Static code analysis for infrastructure-as-code

**Use Case**: Security auditing, compliance checking, vulnerability assessments, security-focused development

**Recommended Workflow**:
```bash
./setup_devgru.sh --profile security
safety check                    # Scan dependencies
bandit -r . -ll                # Scan Python code for security issues
checkov --directory .          # Scan IaC files
```

**Installation Time**: ~10-15 minutes
**Disk Space**: ~2.5 GB

### 5. Cloud-AWS Profile

**Command**: `./setup_devgru.sh --profile cloud-aws`

Includes **Standard** + **AWS SDK**:

**AWS Packages**:
- `boto3` (>=1.34) - AWS SDK for Python
- **AWS CLI** - Command-line interface for AWS

**Post-Installation Configuration**:
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Default region, Output format
```

**Use Case**: AWS cloud development, Lambda functions, S3 management, EC2 automation, AWS infrastructure management

**Installation Time**: ~10-15 minutes
**Disk Space**: ~2.5 GB

### 6. Cloud-Azure Profile

**Command**: `./setup_devgru.sh --profile cloud-azure`

Includes **Standard** + **Azure SDK**:

**Azure Packages**:
- `azure-mgmt-resource` (>=23.0) - Azure Resource Management
- `azure-storage-blob` (>=12.0) - Azure Blob Storage
- `azure-mgmt-costmanagement` (>=4.0) - Azure Cost Management
- **Azure CLI** - Command-line interface for Azure

**Post-Installation Configuration**:
```bash
az login
az account set --subscription "your-subscription-id"
```

**Use Case**: Azure cloud development, Azure Functions, Blob storage management, Azure DevOps

**Installation Time**: ~10-15 minutes
**Disk Space**: ~2.5 GB

### 7. Cloud-GCP Profile

**Command**: `./setup_devgru.sh --profile cloud-gcp`

Includes **Standard** + **GCP SDK**:

**GCP Packages**:
- `google-cloud-storage` (>=2.14) - Google Cloud Storage
- `google-cloud-billing` (>=1.12) - Google Cloud Billing
- `google-cloud-resource-manager` (>=1.11) - Google Cloud Resource Manager
- **gcloud CLI** - Command-line interface for GCP (manual installation required)

**Post-Installation Configuration**:
```bash
gcloud auth login
gcloud config set project your-project-id
gcloud config set compute/region us-central1
```

**Use Case**: Google Cloud Platform development, Cloud Functions, Cloud Storage, GCP infrastructure management

**Installation Time**: ~10-15 minutes
**Disk Space**: ~2.5 GB

## Platform Support

### Supported Operating Systems

| Operating System | Version | Architecture | Package Manager | Status | Tested |
|-----------------|---------|--------------|-----------------|--------|--------|
| **macOS** | 10.15+ (Catalina+) | x86_64 (Intel) | Homebrew | Fully Supported | Yes |
| **macOS** | 11.0+ (Big Sur+) | arm64 (Apple Silicon) | Homebrew | Fully Supported | Yes |
| **Ubuntu** | 20.04 LTS (Focal) | x86_64, arm64 | apt | Fully Supported | Partial |
| **Ubuntu** | 22.04 LTS (Jammy) | x86_64, arm64 | apt | Fully Supported | Partial |
| **Ubuntu** | 24.04 LTS (Noble) | x86_64, arm64 | apt | Fully Supported | No |
| **Debian** | 10 (Buster) | x86_64 | apt | Fully Supported | No |
| **Debian** | 11 (Bullseye) | x86_64, arm64 | apt | Fully Supported | No |
| **Debian** | 12 (Bookworm) | x86_64, arm64 | apt | Fully Supported | No |
| **RHEL** | 8.x | x86_64 | yum/dnf | Fully Supported | No |
| **RHEL** | 9.x | x86_64, arm64 | dnf | Fully Supported | No |
| **CentOS** | 8 Stream | x86_64 | dnf | Fully Supported | No |
| **Fedora** | 35+ | x86_64, arm64 | dnf | Fully Supported | No |
| **Windows WSL2** | Ubuntu 20.04+ | x86_64 | apt | Fully Supported | No |

### Architecture Support

- **x86_64** (Intel/AMD 64-bit): Fully supported across all platforms
- **arm64** (ARM 64-bit): Fully supported on macOS (Apple Silicon) and modern Linux distributions
- **aarch64**: Alias for arm64, fully supported

### Package Manager Requirements

The script automatically detects and uses the appropriate package manager for your system:

- **macOS**: Homebrew (`brew`) - Must be installed before running script
- **Ubuntu/Debian**: APT (`apt-get`) - Pre-installed on most systems
- **RHEL/CentOS/Fedora**: YUM/DNF (`yum` or `dnf`) - Pre-installed on most systems

## Prerequisites

Before running the setup script, ensure the following tools are installed on your system:

### Required Tools

1. **jq** (JSON processor)
   - Used for parsing the prerequisites JSON configuration file
   - Installation: See [Quick Start](#quick-start) section

2. **curl** (Data transfer tool)
   - Used for downloading packages and cloud SDKs
   - Installation: See [Quick Start](#quick-start) section

3. **git** (Version control)
   - Used for repository management
   - Installation: See [Quick Start](#quick-start) section

### Required Files

1. **prerequisites_validated.json**
   - Location: `/tmp/issue67_work/prerequisites_validated.json`
   - Contains validated package specifications
   - Automatically created by prerequisite validation process
   - Contains: Core packages, optional packages, databases, cloud SDKs, external tools

### Optional (But Recommended)

- **Python 3.10+**: If not installed, the script will install it
- **pip**: Python package installer (installed automatically with Python)
- **Package Manager**: Homebrew (macOS), apt (Ubuntu/Debian), yum/dnf (RHEL/CentOS/Fedora)

### System Requirements

- **Disk Space**: 500 MB - 5 GB (depending on profile)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Internet Connection**: Required for downloading packages
- **Permissions**: Standard user permissions (sudo will be requested when needed)

## Usage

### Basic Usage

```bash
# Install with default (standard) profile
./setup_devgru.sh

# Install with specific profile
./setup_devgru.sh --profile full

# Install AWS cloud profile
./setup_devgru.sh --profile cloud-aws

# Show help message
./setup_devgru.sh --help
```

### Advanced Usage

```bash
# Dry-run to preview installations without making changes
./setup_devgru.sh --profile full --dry-run

# Verbose output for debugging
./setup_devgru.sh --profile standard --verbose

# Skip database installations
./setup_devgru.sh --profile full --skip-databases

# Skip external tools
./setup_devgru.sh --profile full --skip-tools

# Combine multiple options
./setup_devgru.sh --profile cloud-aws --skip-databases --verbose --dry-run
```

### Profile Selection Examples

```bash
# Minimal setup for CI/CD
./setup_devgru.sh --profile minimal

# Standard development environment (default)
./setup_devgru.sh --profile standard

# Complete stack with databases and tools
./setup_devgru.sh --profile full

# Security-focused environment
./setup_devgru.sh --profile security

# AWS development
./setup_devgru.sh --profile cloud-aws

# Azure development
./setup_devgru.sh --profile cloud-azure

# GCP development
./setup_devgru.sh --profile cloud-gcp
```

## Command-Line Options

### Available Options

| Option | Argument | Description | Default |
|--------|----------|-------------|---------|
| `--profile` | PROFILE | Installation profile to use | `standard` |
| `--dry-run` | None | Show what would be installed without making changes | `false` |
| `--verbose` | None | Enable detailed debug output | `false` |
| `--skip-databases` | None | Skip database installations | `false` |
| `--skip-tools` | None | Skip external tools installation | `false` |
| `--help`, `-h` | None | Display help message and exit | N/A |

### Profile Values

Valid profile values:
- `minimal` - Python 3.10+ + 5 core packages
- `standard` - Minimal + 15 optional packages (default)
- `full` - Standard + databases + external tools
- `security` - Standard + security tools
- `cloud-aws` - Standard + AWS SDK
- `cloud-azure` - Standard + Azure SDK
- `cloud-gcp` - Standard + GCP SDK

### Option Combinations

```bash
# Test full installation without making changes
./setup_devgru.sh --profile full --dry-run --verbose

# Install standard profile without databases (lightweight)
./setup_devgru.sh --profile standard --skip-databases

# Install AWS profile without tools, with verbose output
./setup_devgru.sh --profile cloud-aws --skip-tools --verbose

# Show help
./setup_devgru.sh --help
```

## Directory Structure

```
setup/
├── setup_devgru.sh                    # Main setup script (executable)
├── README.md                          # This file - comprehensive documentation
├── QUICK_START.md                     # Quick reference guide
├── VERIFICATION.md                    # Verification checklist
├── logs/                              # Installation logs (auto-created)
│   ├── setup_20251120_094530.log      # Timestamped installation log
│   └── installation_report_20251120_094530.txt  # Installation report
├── .state/                            # Installation state (auto-created)
│   └── installation_state.json        # JSON state file
├── modules/                           # Modular installation scripts
│   ├── python_setup.sh                # Python installation module
│   ├── core_packages.sh               # Core packages module
│   ├── optional_packages.sh           # Optional packages module
│   ├── databases.sh                   # Database installation module
│   ├── external_tools.sh              # External tools module
│   ├── cloud_sdks.sh                  # Cloud SDK installation module
│   ├── test_python_setup.sh           # Python setup testing
│   └── README.md                      # Modules documentation
└── requirements/                      # Requirements files by profile
    ├── requirements-core.txt          # Core packages
    ├── requirements-optional.txt      # Optional packages
    ├── requirements-cloud-aws.txt     # AWS packages
    ├── requirements-cloud-azure.txt   # Azure packages
    └── requirements-cloud-gcp.txt     # GCP packages
```

### File Descriptions

- **setup_devgru.sh**: Main executable script that orchestrates the entire installation process
- **README.md**: Comprehensive documentation (this file)
- **QUICK_START.md**: Quick reference guide for common operations
- **VERIFICATION.md**: Pre-deployment and post-installation verification checklists
- **logs/**: Automatically created directory containing timestamped logs and reports
- **.state/**: Automatically created directory containing JSON state files
- **modules/**: Modular bash scripts for specific installation tasks
- **requirements/**: Pip requirements files for different profiles

## Logging and State Management

### Log Files

All installations are logged to timestamped files in the `logs/` directory. The directory is automatically created on first run.

**Log File Naming**:
- Installation logs: `logs/setup_YYYYMMDD_HHMMSS.log`
- Installation reports: `logs/installation_report_YYYYMMDD_HHMMSS.txt`

**Log Entry Levels**:
```
[INFO]    - General information messages
[SUCCESS] - Successful operations (green)
[WARNING] - Non-critical issues (yellow)
[ERROR]   - Critical errors (red)
[DEBUG]   - Detailed debugging information (magenta, only with --verbose)
```

**Example Log Entries**:
```
[INFO] Profile: standard
[SUCCESS] OS Type: macos
[WARNING] Skipping database installations
[ERROR] Package installation failed: invalid-package
[DEBUG] Executing: brew install python@3.10
```

### Viewing Logs

```bash
# View latest installation log
cat logs/setup_*.log | tail -100

# View only errors and warnings
cat logs/setup_*.log | grep -E "WARNING|ERROR"

# Follow log in real-time (different terminal)
tail -f logs/setup_*.log

# View installation report
cat logs/installation_report_*.txt
```

### Installation State

The script maintains a JSON state file tracking all installation details:

**State File Location**: `.state/installation_state.json`

**State File Structure**:
```json
{
  "timestamp": "2025-11-20T14:45:30Z",
  "profile": "standard",
  "os_type": "macos",
  "os_version": "26.1",
  "arch": "arm64",
  "installed_packages": [
    "pandas",
    "requests",
    "pydantic",
    "celery",
    "playwright",
    "fastapi"
  ],
  "failed_packages": []
}
```

**Querying State File**:
```bash
# View entire state
cat .state/installation_state.json | jq .

# View installed packages
cat .state/installation_state.json | jq -r '.installed_packages[]'

# View failed packages
cat .state/installation_state.json | jq -r '.failed_packages[]'

# Check installation profile
cat .state/installation_state.json | jq -r '.profile'

# View OS information
cat .state/installation_state.json | jq -r '.os_type, .os_version, .arch'
```

## Error Handling and Rollback

The script includes comprehensive error handling and automatic rollback capabilities to ensure system integrity.

### Error Detection

The script uses strict error handling (`set -euo pipefail`) to catch errors immediately:

- **Set -e**: Exit immediately if a command exits with non-zero status
- **Set -u**: Treat unset variables as errors
- **Set -o pipefail**: Return value of pipeline is the status of the last command to exit with non-zero status

### Automatic Rollback

When errors occur during installation:

1. **Error Detection**: Script catches the error and logs details
2. **Rollback Prompt**: Asks if you want to rollback changes
3. **Reverse Execution**: Uninstalls packages in reverse order of installation
4. **State Preservation**: Saves state even after failures for analysis

**Rollback Process**:
```
[ERROR] Package installation failed: some-package
[WARNING] Executing rollback procedures...
[INFO] Rollback: pip uninstall -y some-package
[INFO] Rollback: brew uninstall python@3.10
[SUCCESS] Rollback completed
```

### Manual Rollback

If automatic rollback fails or you need to rollback later:

```bash
# View installed packages from state file
cat .state/installation_state.json | jq -r '.installed_packages[]'

# Uninstall Python packages
pip uninstall -y package_name

# Uninstall multiple Python packages
pip uninstall -y $(cat .state/installation_state.json | jq -r '.installed_packages[]')

# Uninstall system packages (macOS)
brew uninstall package_name

# Uninstall system packages (Ubuntu/Debian)
sudo apt-get remove -y package_name

# Uninstall system packages (RHEL/CentOS/Fedora)
sudo yum remove -y package_name
```

### Signal Handling

The script handles interrupt signals gracefully:

- **SIGINT** (Ctrl+C): Cleanup and rollback
- **SIGTERM**: Graceful shutdown
- **EXIT**: Always saves state before exiting

```bash
# Press Ctrl+C during installation
^C
[WARNING] Setup interrupted by user
[WARNING] Executing rollback procedures...
```

## Post-Installation Steps

After successful installation, follow these steps to complete your development environment setup:

### 1. Verify Installation

```bash
# Check Python version
python3 --version  # Should show Python 3.10 or higher

# Verify pip is available
python3 -m pip --version

# List installed packages
pip list

# Verify core packages
python3 -c "import pandas, requests, pydantic, celery, playwright; print('Core packages OK')"

# Verify optional packages (standard profile)
python3 -c "import fastapi, sqlalchemy, pytest, langchain; print('Optional packages OK')"

# Check installation report
cat logs/installation_report_*.txt
```

### 2. Configure Cloud Providers

If you installed a cloud profile, configure your cloud provider credentials:

**AWS Configuration**:
```bash
aws configure
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: us-east-1
# Default output format: json

# Verify AWS configuration
aws sts get-caller-identity
aws s3 ls
```

**Azure Configuration**:
```bash
az login
# Opens browser for authentication

# List subscriptions
az account list --output table

# Set default subscription
az account set --subscription "your-subscription-id"

# Verify Azure configuration
az account show
az group list
```

**GCP Configuration**:
```bash
gcloud auth login
# Opens browser for authentication

# Set project
gcloud config set project your-project-id

# Set region
gcloud config set compute/region us-central1

# Verify GCP configuration
gcloud config list
gcloud projects list
```

### 3. Start Database Services

If you installed the full profile, start database services:

**Redis**:
```bash
# macOS
brew services start redis
brew services list | grep redis

# Linux (Ubuntu/Debian)
sudo systemctl start redis
sudo systemctl enable redis
sudo systemctl status redis

# Test Redis connection
redis-cli ping  # Should return PONG
```

**PostgreSQL**:
```bash
# macOS
brew services start postgresql@15
brew services list | grep postgresql

# Linux (Ubuntu/Debian)
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo systemctl status postgresql

# Test PostgreSQL connection
psql --version
psql -U postgres -c "SELECT version();"
```

**Neo4j** (Requires Docker):
```bash
# Start Neo4j using Docker
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15

# Verify Neo4j is running
docker ps | grep neo4j

# Access Neo4j browser
open http://localhost:7474
```

### 4. Create Virtual Environments

Create isolated Python environments for different projects:

```bash
# Create project-specific virtual environment
python3 -m venv myproject_venv

# Activate virtual environment
source myproject_venv/bin/activate  # macOS/Linux
myproject_venv\Scripts\activate     # Windows

# Verify virtual environment
which python3  # Should point to venv
pip list       # Should show only pip and setuptools

# Install project-specific dependencies
pip install -r requirements.txt

# Deactivate virtual environment
deactivate
```

### 5. Configure Development Tools

Set up additional development tools and configurations:

```bash
# Configure Git (if not already done)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set up SSH keys for GitHub
ssh-keygen -t ed25519 -C "your.email@example.com"
cat ~/.ssh/id_ed25519.pub  # Add to GitHub

# Configure Docker (if installed)
docker version
docker ps

# Test Playwright browsers (if installed)
playwright install  # Installs browser binaries
playwright install-deps  # Installs system dependencies
```

### 6. Review Installation Report

```bash
# View installation report
cat logs/installation_report_*.txt

# Check for failed packages
cat .state/installation_state.json | jq -r '.failed_packages[]'

# Verify installed packages count
cat .state/installation_state.json | jq '.installed_packages | length'
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Script won't run - Permission denied

**Symptoms**:
```
bash: ./setup_devgru.sh: Permission denied
```

**Solution**:
```bash
chmod +x setup_devgru.sh
./setup_devgru.sh
```

#### Issue: Missing prerequisites (jq, curl, git)

**Symptoms**:
```
[ERROR] Missing required tools: jq curl
```

**Solution**:
```bash
# macOS
brew install jq curl git

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y jq curl git

# RHEL/CentOS/Fedora
sudo yum install -y jq curl git
```

#### Issue: Prerequisites file not found

**Symptoms**:
```
[ERROR] Prerequisites file not found: /tmp/issue67_work/prerequisites_validated.json
```

**Solution**:
Ensure the prerequisites validation process has been completed. The file should be created automatically during issue #67 setup.

#### Issue: Package installation fails

**Symptoms**:
```
[ERROR] Package installation failed: package-name
```

**Solution**:
1. Check internet connectivity: `ping google.com`
2. Update package manager:
   ```bash
   brew update              # macOS
   sudo apt-get update      # Ubuntu/Debian
   sudo yum update          # RHEL/CentOS
   ```
3. Check logs for specific error: `cat logs/setup_*.log | grep ERROR`
4. Try installing package manually to identify issue:
   ```bash
   pip install package-name --verbose
   ```

#### Issue: Python version conflict

**Symptoms**:
```
[ERROR] Python 3.10+ required, found Python 3.8
```

**Solution**: Use pyenv to manage multiple Python versions:
```bash
# Install pyenv
brew install pyenv  # macOS
curl https://pyenv.run | bash  # Linux

# Install Python 3.10
pyenv install 3.10.12

# Set global Python version
pyenv global 3.10.12

# Verify
python3 --version
```

#### Issue: Database connection fails

**Symptoms**:
```
Could not connect to Redis at 127.0.0.1:6379
```

**Solution**:
1. Ensure database service is running:
   ```bash
   # macOS
   brew services list
   brew services start redis

   # Linux
   sudo systemctl status redis
   sudo systemctl start redis
   ```
2. Check port is not in use: `lsof -i :6379`
3. Verify firewall rules
4. Review database logs:
   ```bash
   # macOS
   brew services list | grep redis
   tail -f /usr/local/var/log/redis.log

   # Linux
   sudo journalctl -u redis -f
   ```

#### Issue: Cloud SDK authentication fails

**Symptoms**:
```
[ERROR] Unable to authenticate with AWS
```

**Solution**:
```bash
# AWS
aws configure  # Re-enter credentials
aws sts get-caller-identity  # Verify

# Azure
az login  # Re-authenticate
az account show  # Verify

# GCP
gcloud auth login  # Re-authenticate
gcloud projects list  # Verify
```

#### Issue: Homebrew not found (macOS)

**Symptoms**:
```
[ERROR] Unsupported package manager: brew
```

**Solution**: Install Homebrew:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### Issue: Dry-run shows errors

**Symptoms**: Dry-run mode reveals potential issues

**Solution**: Address issues before actual installation:
```bash
# Run dry-run with verbose mode
./setup_devgru.sh --profile full --dry-run --verbose > test_output.txt

# Review output
cat test_output.txt | grep -E "WARNING|ERROR"

# Fix identified issues, then run actual installation
./setup_devgru.sh --profile full
```

#### Issue: Disk space insufficient

**Symptoms**:
```
[ERROR] No space left on device
```

**Solution**:
1. Check available disk space: `df -h`
2. Clean package manager cache:
   ```bash
   brew cleanup  # macOS
   sudo apt-get clean  # Ubuntu/Debian
   sudo yum clean all  # RHEL/CentOS
   ```
3. Remove unused Python packages: `pip list --outdated`
4. Use a smaller profile: `--profile minimal`

### Getting Additional Help

If you encounter issues not covered here:

1. **Check Logs**: Review detailed logs in `logs/setup_*.log`
2. **Verbose Mode**: Run with `--verbose` flag for detailed output
3. **Dry-Run**: Test with `--dry-run` to identify issues before installation
4. **State File**: Check `.state/installation_state.json` for installation details
5. **GitHub Issues**: Report bugs at repository issues page
6. **Community**: Ask questions in project discussions

## Examples

### Example 1: Basic Development Setup

Set up a standard development environment:

```bash
# Install standard profile (default)
./setup_devgru.sh

# Verify installation
python3 --version
pip list | grep -E "pandas|requests|fastapi"

# Create virtual environment for project
python3 -m venv project_venv
source project_venv/bin/activate

# Install project-specific dependencies
pip install -r requirements.txt
```

### Example 2: Security Auditing Environment

Set up an environment focused on security scanning:

```bash
# Install security profile
./setup_devgru.sh --profile security

# Run security checks
safety check
safety check --json > security_report.json

bandit -r . -ll
bandit -r . -f json -o bandit_report.json

checkov --directory .
checkov --directory . --output json > checkov_report.json

# Review reports
cat security_report.json | jq .
```

### Example 3: AWS Cloud Development

Set up an environment for AWS development:

```bash
# Install AWS profile
./setup_devgru.sh --profile cloud-aws

# Configure AWS credentials
aws configure

# Verify AWS CLI
aws sts get-caller-identity
aws s3 ls

# Example AWS operations
aws ec2 describe-instances --region us-east-1
aws s3 mb s3://my-bucket-name
aws lambda list-functions

# Python script using boto3
python3 << EOF
import boto3
s3 = boto3.client('s3')
buckets = s3.list_buckets()
print(f"Found {len(buckets['Buckets'])} buckets")
EOF
```

### Example 4: Full Stack with Custom Options

Install full stack without databases, with verbose output:

```bash
# Install full profile, skip databases, verbose output
./setup_devgru.sh --profile full --skip-databases --verbose

# Review installation report
cat logs/installation_report_*.txt

# Check installed packages
cat .state/installation_state.json | jq '.installed_packages'

# Verify external tools
docker --version
terraform --version
node --version
trivy --version
```

### Example 5: Testing Before Production

Test installation thoroughly before deploying to production:

```bash
# Test installation without making changes
./setup_devgru.sh --profile full --dry-run --verbose > test_output.txt

# Review what would be installed
cat test_output.txt
cat test_output.txt | grep -E "Would install|Would execute"

# Check for potential issues
cat test_output.txt | grep -E "WARNING|ERROR"

# If everything looks good, proceed with actual installation
./setup_devgru.sh --profile full

# Verify installation
python3 -m pytest --version
docker --version
redis-cli ping
```

### Example 6: Azure Development Environment

Set up Azure development environment:

```bash
# Install Azure profile
./setup_devgru.sh --profile cloud-azure

# Authenticate with Azure
az login

# Set default subscription
az account set --subscription "your-subscription-id"

# Verify Azure CLI
az account show
az group list --output table

# Example Azure operations
az group create --name myResourceGroup --location eastus
az storage account list
az vm list --output table

# Python script using Azure SDK
python3 << EOF
from azure.mgmt.resource import ResourceManagementClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
subscription_id = "your-subscription-id"
client = ResourceManagementClient(credential, subscription_id)

groups = list(client.resource_groups.list())
print(f"Found {len(groups)} resource groups")
EOF
```

### Example 7: Multi-Profile Installation

Install different profiles for different use cases:

```bash
# Install minimal profile for CI/CD container
./setup_devgru.sh --profile minimal

# Later, upgrade to standard profile
./setup_devgru.sh --profile standard

# Add security tools
./setup_devgru.sh --profile security

# Add cloud capabilities
./setup_devgru.sh --profile cloud-aws
```

## Best Practices

### 1. Always Use Dry-Run First

Test installations before making actual changes:

```bash
# Preview what will be installed
./setup_devgru.sh --profile full --dry-run

# Review output, then proceed
./setup_devgru.sh --profile full
```

### 2. Review Logs Regularly

Check logs for warnings or errors:

```bash
# View recent logs
cat logs/setup_*.log | tail -100

# Check for issues
cat logs/setup_*.log | grep -E "WARNING|ERROR"

# Monitor specific package installation
cat logs/setup_*.log | grep "package-name"
```

### 3. Use Virtual Environments

Always create isolated Python environments for projects:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

### 4. Keep Packages Updated

Regularly update packages to get security fixes and new features:

```bash
# Update package manager
brew update && brew upgrade              # macOS
sudo apt-get update && sudo apt-get upgrade  # Ubuntu/Debian
sudo yum update                          # RHEL/CentOS

# Update Python packages
pip list --outdated
pip install --upgrade package_name

# Update all packages (use with caution)
pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U
```

### 5. Regular Security Audits

Use security tools to scan for vulnerabilities:

```bash
# Install security profile if not already installed
./setup_devgru.sh --profile security

# Scan dependencies for vulnerabilities
safety check

# Scan Python code for security issues
bandit -r . -ll

# Scan infrastructure-as-code
checkov --directory .
```

### 6. Backup Before Major Changes

Create backups before running major installations:

```bash
# Backup current pip packages
pip freeze > backup_requirements.txt

# Backup state file
cp .state/installation_state.json .state/installation_state_backup.json

# Backup environment
cp -r venv venv_backup
```

### 7. Use Version Control

Track changes to configuration files:

```bash
# Initialize git repository (if not already done)
git init

# Add important files
git add requirements*.txt
git add .state/installation_state.json
git add logs/installation_report_*.txt

# Commit changes
git commit -m "Update development environment"
```

### 8. Document Custom Configurations

Keep notes about your specific setup:

```bash
# Create notes file
cat > SETUP_NOTES.md << EOF
# Development Environment Setup

## Date: $(date)
## Profile: standard

## Custom Configurations:
- Python 3.10.12
- Custom packages: package1, package2
- Cloud provider: AWS

## Environment Variables:
- AWS_REGION=us-east-1
- DATABASE_URL=postgresql://localhost/mydb

## Notes:
- Installed additional tools: X, Y, Z
- Custom configurations in ~/.bashrc
EOF
```

## Contributing

Contributions to the setup script are welcome! Here's how you can help:

### How to Contribute

1. **Test Changes**: Always test with `--dry-run` mode first
2. **Multi-OS Testing**: Ensure compatibility across all supported operating systems
3. **Documentation**: Update documentation for new features
4. **Code Quality**: Follow bash best practices and run shellcheck
5. **Error Handling**: Add proper error handling for new functions

### Testing Checklist

```bash
# Test syntax
bash -n setup_devgru.sh

# Test all profiles
for profile in minimal standard full security cloud-aws cloud-azure cloud-gcp; do
    ./setup_devgru.sh --profile $profile --dry-run
done

# Test error handling
./setup_devgru.sh --profile invalid  # Should show error

# Test help
./setup_devgru.sh --help

# Run shellcheck (install first: brew install shellcheck)
shellcheck setup_devgru.sh
```

### Code Style Guidelines

- Use consistent indentation (4 spaces)
- Add comments for complex logic
- Use descriptive variable names
- Follow bash best practices
- Add error checking for all operations
- Use shellcheck to validate code quality

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and test thoroughly
4. Commit with descriptive messages: `git commit -m "Add: Feature description"`
5. Push to your fork: `git push origin feature/my-feature`
6. Create a Pull Request

## Version History

### v1.0.0 (2025-11-20)

**Initial Release** - GitHub Issue #67

**Features**:
- Multi-OS support (macOS, Linux, WSL2)
- 7 installation profiles (minimal, standard, full, security, cloud-aws, cloud-azure, cloud-gcp)
- Automatic OS and architecture detection
- Dry-run mode for testing
- Rollback capability on failures
- Comprehensive logging with multiple log levels
- JSON-based state tracking
- Error handling with signal handlers
- Modular design for maintainability
- Skip options for databases and tools
- Verbose mode for debugging
- Help system with usage examples

**Supported Platforms**:
- macOS 10.15+ (Intel and Apple Silicon)
- Ubuntu 20.04+ LTS
- Debian 10+
- RHEL 8+
- CentOS 8+
- Fedora 35+
- Windows WSL2 (Ubuntu)

**Package Support**:
- Python 3.10+
- 5 core packages (pandas, requests, pydantic, celery, playwright)
- 15 optional packages (fastapi, sqlalchemy, pytest, langchain, etc.)
- 3 databases (Redis, PostgreSQL, Neo4j)
- 5 external tools (Docker, Terraform, Trivy, Node.js, Airflow)
- 3 cloud SDKs (AWS, Azure, GCP)

## Support

### Getting Help

For issues, questions, or contributions:

- **GitHub Issues**: Report bugs and request features at repository issues page
- **Documentation**:
  - Main documentation: [README.md](README.md) (this file)
  - Quick start: [QUICK_START.md](QUICK_START.md)
  - Verification: [VERIFICATION.md](VERIFICATION.md)
  - Modules: [modules/README.md](modules/README.md)
- **Logs**: Check `logs/setup_*.log` for detailed error information
- **State**: Review `.state/installation_state.json` for installation details

### Reporting Issues

When reporting issues, please include:

1. **Operating System**: OS type, version, and architecture
2. **Profile Used**: Which profile you were installing
3. **Command Used**: Exact command with all options
4. **Error Message**: Full error message from console
5. **Log File**: Relevant portions of `logs/setup_*.log`
6. **State File**: Content of `.state/installation_state.json`

**Example Issue Report**:
```
Title: Package installation fails on Ubuntu 22.04

Environment:
- OS: Ubuntu 22.04 LTS (x86_64)
- Profile: standard
- Command: ./setup_devgru.sh --profile standard --verbose

Error:
[ERROR] Package installation failed: playwright

Logs:
[See attached log file]

State:
{
  "profile": "standard",
  "failed_packages": ["playwright"]
}
```

### Community

- **Discussions**: Join project discussions for questions and ideas
- **Pull Requests**: Submit improvements and bug fixes
- **Documentation**: Help improve documentation for other users

## License

This script is part of the devCrew_s1 project. See the main repository for license information.

## Acknowledgments

- Created for GitHub Issue #67 - Multi-OS Prerequisites Setup Script
- devCrew_s1 team
- Contributors and testers

---

**Last Updated**: 2025-11-20
**Version**: 1.0.0
**Author**: devCrew_s1
**Issue**: GitHub Issue #67
