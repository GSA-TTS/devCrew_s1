# Infrastructure as Code (IaC) Provisioning & Management Platform

**Issue #38 - TOOL-INFRA-001**

A comprehensive Infrastructure as Code platform that provides provisioning, validation, drift detection, and cost estimation capabilities across AWS, Azure, and GCP.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Multi-Cloud Examples](#multi-cloud-examples)
- [Protocol Integration](#protocol-integration)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

This IaC platform provides a unified interface for managing infrastructure across multiple cloud providers using Terraform. It integrates security validation, drift detection, and cost estimation to ensure safe and cost-effective infrastructure deployments.

### Key Capabilities

- **Provisioning**: Execute terraform init/plan/apply/destroy workflows
- **Multi-Cloud Support**: AWS, Azure, and GCP providers
- **Security Validation**: Pre-deployment scanning with Checkov and tfsec
- **State Management**: Remote state with locking (S3, Azure Blob, GCS)
- **Drift Detection**: Identify and remediate configuration drift
- **Cost Estimation**: Generate cost estimates before deployment

## Features

### 1. Terraform Wrapper (`terraform_wrapper.py`)

- Execute Terraform commands programmatically
- Parse JSON output for automation
- Handle state operations
- Retry logic for transient failures
- Workspace management

### 2. Multi-Cloud Providers (`cloud_providers.py`)

- Unified interface for AWS, Azure, and GCP
- Credential validation
- Provider-specific configurations
- Backend configuration generation

### 3. State Management (`state_manager.py`)

- Remote state operations (S3, Azure Blob, GCS)
- State locking mechanisms
- Backup and recovery
- State migration support

### 4. Security Validation (`validator.py`)

- Checkov integration for security scanning
- tfsec integration for additional checks
- Custom policy support
- Compliance framework checks
- Report generation (text, JSON, HTML)

### 5. Drift Detection (`drift_detector.py`)

- Compare state vs actual infrastructure
- Identify drifted resources
- Generate drift reports
- Remediation recommendations
- Auto-remediation (with approval)

### 6. Cost Estimation (`cost_estimator.py`)

- Estimate infrastructure costs
- Budget alerts
- Cost comparison (before/after)
- Multi-cloud pricing support

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IaC Manager (CLI)                        │
│                     iac_manager.py                          │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┬───────────┬────────────┐
        │           │           │           │            │
        ▼           ▼           ▼           ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐
│Terraform │ │  Cloud   │ │  State   │ │Validator│ │  Cost   │
│ Wrapper  │ │Providers │ │ Manager  │ │         │ │Estimator│
└──────────┘ └──────────┘ └──────────┘ └─────────┘ └─────────┘
      │            │            │            │            │
      ▼            ▼            ▼            ▼            ▼
┌──────────────────────────────────────────────────────────────┐
│                     Cloud Providers                          │
│              AWS  │  Azure  │  GCP                            │
└──────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

1. **Terraform** (>= 1.6.0)
   ```bash
   # macOS
   brew install terraform

   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/

   # Verify installation
   terraform version
   ```

2. **Python** (>= 3.8)
   ```bash
   python3 --version
   ```

3. **Cloud Provider CLI** (optional but recommended)
   ```bash
   # AWS CLI
   pip install awscli

   # Azure CLI
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

   # GCP CLI
   curl https://sdk.cloud.google.com | bash
   ```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Install Security Scanning Tools

```bash
# Checkov
pip install checkov

# tfsec (optional)
# macOS
brew install tfsec

# Linux
curl -s https://raw.githubusercontent.com/aquasecurity/tfsec/master/scripts/install_linux.sh | bash
```

## Quick Start

### 1. Configure Credentials

**AWS:**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"

# Or use AWS CLI
aws configure
```

**Azure:**
```bash
export AZURE_SUBSCRIPTION_ID="your-subscription-id"

# Or use Azure CLI
az login
```

**GCP:**
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Or use gcloud CLI
gcloud auth application-default login
```

### 2. Initialize Configuration

```bash
# Copy and customize the configuration file
cp config.yaml my_config.yaml

# Edit the configuration
vim my_config.yaml
```

### 3. Provision Infrastructure

```bash
# Validate configuration
python iac_manager.py -c my_config.yaml -d /path/to/terraform validate

# Estimate costs
python iac_manager.py -c my_config.yaml -d /path/to/terraform estimate-cost

# Provision infrastructure
python iac_manager.py -c my_config.yaml -d /path/to/terraform provision

# With auto-approval (USE WITH CAUTION)
python iac_manager.py -c my_config.yaml -d /path/to/terraform provision --auto-approve
```

## Usage

### Command-Line Interface

```bash
python iac_manager.py [OPTIONS] COMMAND

Options:
  -c, --config PATH       Configuration file path (default: config.yaml)
  -d, --directory PATH    Terraform working directory (default: .)

Commands:
  provision               Provision infrastructure
  validate                Validate Terraform configuration
  detect-drift            Detect configuration drift
  estimate-cost           Estimate infrastructure costs
  destroy                 Destroy infrastructure
```

### Provision Infrastructure

```bash
# Interactive mode (prompts for approval)
python iac_manager.py -d /path/to/terraform provision

# With variable file
python iac_manager.py -d /path/to/terraform provision --var-file=prod.tfvars

# Auto-approve (skip prompts)
python iac_manager.py -d /path/to/terraform provision --auto-approve
```

### Validate Configuration

```bash
# Text output
python iac_manager.py -d /path/to/terraform validate

# JSON output
python iac_manager.py -d /path/to/terraform validate --format json

# Save to file
python iac_manager.py -d /path/to/terraform validate --format html --output report.html
```

### Detect Drift

```bash
# Detect drift
python iac_manager.py -d /path/to/terraform detect-drift

# Auto-remediate drift (USE WITH CAUTION)
python iac_manager.py -d /path/to/terraform detect-drift --auto-remediate

# Save drift report
python iac_manager.py -d /path/to/terraform detect-drift --format json --output drift.json
```

### Estimate Costs

```bash
# Estimate costs
python iac_manager.py -d /path/to/terraform estimate-cost

# Generate HTML report
python iac_manager.py -d /path/to/terraform estimate-cost --format html --output costs.html
```

### Destroy Infrastructure

```bash
# Interactive mode (requires typing 'destroy' to confirm)
python iac_manager.py -d /path/to/terraform destroy

# Auto-approve (USE WITH EXTREME CAUTION)
python iac_manager.py -d /path/to/terraform destroy --auto-approve
```

## Multi-Cloud Examples

### AWS Example

```bash
# Use the provided AWS example
cd /path/to/devCrew_s1

# Initialize
python iac_manager.py -d . provision

# This will:
# 1. Create VPC with public/private subnets
# 2. Launch EC2 instance
# 3. Create S3 bucket with encryption
# 4. Configure security groups
```

See `example_aws.tf` for complete configuration.

### Azure Example

```bash
# Use the provided Azure example
cd /path/to/devCrew_s1

# Set Azure subscription
export AZURE_SUBSCRIPTION_ID="your-subscription-id"

# Initialize
python iac_manager.py -d . provision

# This will:
# 1. Create resource group and VNet
# 2. Launch Linux VM
# 3. Create storage account
# 4. Configure network security groups
```

See `example_azure.tf` for complete configuration.

### GCP Example

```bash
# Use the provided GCP example
cd /path/to/devCrew_s1

# Set GCP project
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Initialize
python iac_manager.py -d . provision

# This will:
# 1. Create VPC network with subnets
# 2. Launch compute instance
# 3. Create Cloud Storage bucket
# 4. Configure firewall rules
```

See `example_gcp.tf` for complete configuration.

## Protocol Integration

This platform integrates with 18 protocols:

### Core Protocols

1. **P-ARCH-INTEGRATION**: Architecture-driven infrastructure setup
2. **P-CLOUD-VALIDATION**: Cloud architecture validation
3. **CORE-CACHE-003**: Cache infrastructure provisioning
4. **P-DEPLOYMENT-VALIDATION**: Deployment environment validation
5. **P-DOCKER-CLEANUP**: Container infrastructure management

### Security Protocols

6. **P-SECURITY-SCAN**: Pre-deployment security scanning
7. **P-COMPLIANCE-CHECK**: Compliance framework validation
8. **P-VULNERABILITY-ASSESS**: Infrastructure vulnerability assessment

### Operations Protocols

9. **P-STATE-MGMT**: Remote state management
10. **P-DRIFT-DETECT**: Configuration drift detection
11. **P-COST-OPTIMIZE**: Cost optimization recommendations
12. **P-BACKUP-RESTORE**: State backup and recovery

### Integration Protocols

13. **P-MULTI-CLOUD**: Multi-cloud provider support
14. **P-CI-CD**: CI/CD pipeline integration
15. **P-MONITORING**: Infrastructure monitoring setup
16. **P-LOGGING**: Centralized logging configuration

### Governance Protocols

17. **P-POLICY-ENFORCE**: Policy enforcement
18. **P-AUDIT-TRAIL**: Audit trail generation

## Configuration

### Configuration File Structure

```yaml
# Terraform settings
terraform:
  binary: "terraform"
  working_dir: "."
  max_retries: 3
  retry_delay: 5

# Provider settings
provider:
  name: "aws"  # aws, azure, gcp
  region: "us-east-1"
  credentials: {}

# Backend configuration
backend:
  type: "s3"  # s3, azurerm, gcs, local
  bucket: "terraform-state-bucket"
  key: "terraform.tfstate"
  region: "us-east-1"
  encrypt: true
  dynamodb_table: "terraform-state-lock"

# Validation settings
validation:
  enable_checkov: true
  enable_tfsec: true
  severity_threshold: "MEDIUM"

# Cost estimation
cost_estimation:
  enabled: true
  budget_limit: 1000.0
```

### Environment Variables

```bash
# AWS
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"

# Azure
export AZURE_SUBSCRIPTION_ID="..."
export AZURE_TENANT_ID="..."
export AZURE_CLIENT_ID="..."
export AZURE_CLIENT_SECRET="..."

# GCP
export GOOGLE_CLOUD_PROJECT="..."
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

## Testing

### Run All Tests

```bash
# Run all tests
pytest test_iac.py -v

# Run with coverage
pytest test_iac.py -v --cov=. --cov-report=html

# Run specific test class
pytest test_iac.py::TestTerraformWrapper -v

# Run specific test
pytest test_iac.py::TestTerraformWrapper::test_init_success -v
```

### Test Coverage

The test suite includes:

- **Terraform Wrapper Tests**: Command execution, output parsing, error handling
- **Cloud Provider Tests**: AWS, Azure, GCP provider configurations
- **State Manager Tests**: S3, Azure Blob, GCS state operations
- **Validator Tests**: Security scanning, report generation
- **Drift Detector Tests**: Drift detection, remediation
- **Cost Estimator Tests**: Cost calculation, budget alerts

Target coverage: **80%+**

## Troubleshooting

### Common Issues

#### 1. Terraform Not Found

```bash
# Error: Terraform binary not found
# Solution: Install Terraform or specify path in config
terraform:
  binary: "/usr/local/bin/terraform"
```

#### 2. Authentication Errors

```bash
# AWS Error: Unable to locate credentials
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"

# Or use AWS CLI
aws configure

# Azure Error: No subscription found
az login

# GCP Error: Could not find default credentials
gcloud auth application-default login
```

#### 3. State Lock Errors

```bash
# Error: Error acquiring the state lock
# Solution: Force unlock (USE WITH CAUTION)
terraform force-unlock <lock-id>

# Or use state manager
python -c "
from state_manager import StateManager
manager = StateManager('s3', {'bucket': '...', 'key': '...', 'region': '...'})
manager.force_unlock()
"
```

#### 4. Checkov/tfsec Not Found

```bash
# Install Checkov
pip install checkov

# Install tfsec
brew install tfsec  # macOS
# or download from GitHub releases
```

#### 5. Cost Estimation Errors

```bash
# Error: No pricing data for resource type
# This is expected for resources without pricing data
# Cost estimates are approximate
```

### Debug Mode

```bash
# Enable verbose logging
export TF_LOG=DEBUG

# Run with Python debugging
python -m pdb iac_manager.py provision
```

## Best Practices

### 1. Security

- **Never commit credentials** to version control
- Use **environment variables** or **credential files**
- Enable **encryption** for remote state
- Use **state locking** to prevent concurrent modifications
- Run **security validation** before every deployment
- Restrict **firewall rules** to specific IP ranges

### 2. State Management

- Use **remote state** for team collaboration
- Enable **state versioning** for rollback capability
- **Backup state** before destructive operations
- Use **workspaces** for environment isolation

### 3. Cost Optimization

- Review **cost estimates** before provisioning
- Set **budget alerts** to avoid surprises
- Use **appropriate instance sizes** for workloads
- Enable **auto-scaling** where applicable
- Clean up **unused resources**

### 4. Drift Detection

- Run **drift detection** regularly (weekly/monthly)
- Investigate and **remediate drift** promptly
- Document **intentional manual changes**
- Use **auto-remediation** carefully

### 5. Validation

- Run **validation** on every configuration change
- Address **critical** and **high** severity issues
- Use **custom policies** for organization-specific requirements
- Integrate **validation** into CI/CD pipelines

### 6. Multi-Cloud

- Use **consistent naming** conventions across clouds
- Leverage **provider-specific features** appropriately
- Test **disaster recovery** across regions
- Monitor **cross-cloud connectivity**

## Example Workflow

### Complete Deployment Workflow

```bash
# 1. Initialize working directory
cd /path/to/terraform/config

# 2. Validate configuration
python iac_manager.py -c config.yaml validate

# 3. Estimate costs
python iac_manager.py -c config.yaml estimate-cost

# 4. Review and approve
# (Review validation and cost reports)

# 5. Provision infrastructure
python iac_manager.py -c config.yaml provision

# 6. Verify deployment
terraform output

# 7. Monitor for drift (run periodically)
python iac_manager.py -c config.yaml detect-drift

# 8. When done, destroy infrastructure
python iac_manager.py -c config.yaml destroy
```

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
name: IaC Deployment

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
      - name: Install Dependencies
        run: pip install -r requirements.txt
      - name: Validate
        run: python iac_manager.py validate --format json
      - name: Cost Estimate
        run: python iac_manager.py estimate-cost --format json

  deploy:
    needs: validate
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy
        run: python iac_manager.py provision --auto-approve
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

## Support and Contribution

### Getting Help

- Review this README and example configurations
- Check the troubleshooting section
- Run tests to verify functionality
- Review logs for detailed error messages

### Contributing

Contributions are welcome! Please:

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass

## License

This project is part of the devCrew_s1 repository.

## Credits

- **Tool ID**: TOOL-INFRA-001
- **Issue**: #38
- **Priority**: MEDIUM (Phase 2 - Core Capabilities)
- **Protocol Coverage**: 18 protocols (22% coverage)
