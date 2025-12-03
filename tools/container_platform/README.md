# Container Platform Management

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-20.10+-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Comprehensive container platform management tool for the devCrew_s1 project**

Production-ready platform for managing the complete container lifecycle including building, scanning, optimizing, and deploying container images. Integrates with multiple registries, security scanners, and optimization tools.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Configuration](#configuration)
- [Modules](#modules)
- [Security Scanning](#security-scanning)
- [Image Optimization](#image-optimization)
- [Multi-Registry Support](#multi-registry-support)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Container Platform Management tool provides a unified interface for managing container operations across the entire lifecycle:

```
Build → Lint → Scan → Optimize → Push → Deploy → Monitor
```

### Key Capabilities

- **Build Engine**: Multi-platform builds with BuildKit support
- **Security Scanning**: Trivy and Grype integration with vulnerability management
- **Image Optimization**: Automated size reduction and efficiency analysis
- **Dockerfile Linting**: Best practices validation with hadolint
- **Registry Management**: Multi-registry support (Docker Hub, ECR, GCR, ACR, Harbor)
- **Container Lifecycle**: Complete container management operations
- **CLI & API**: Both command-line and programmatic interfaces

### Use Cases

1. **Local Development**: Build and test containers locally
2. **CI/CD Pipelines**: Automate container workflows
3. **Security Compliance**: Scan for vulnerabilities and enforce policies
4. **Image Optimization**: Reduce image sizes and improve efficiency
5. **Multi-Registry Sync**: Synchronize images across registries
6. **Production Deployment**: Manage container deployments

## Features

### Build Features

- ✅ Multi-platform builds (amd64, arm64, arm/v7)
- ✅ BuildKit backend with advanced caching
- ✅ Build argument and secret injection
- ✅ Multi-stage build optimization
- ✅ Build context validation
- ✅ Progress tracking and metrics
- ✅ Parallel build execution
- ✅ Cache management strategies

### Security Features

- ✅ Vulnerability scanning (Trivy, Grype)
- ✅ Misconfiguration detection
- ✅ Secret scanning in images
- ✅ License compliance checking
- ✅ SBOM generation (SPDX, CycloneDX)
- ✅ Severity threshold enforcement
- ✅ CVE ignore lists
- ✅ Result caching for performance

### Optimization Features

- ✅ Layer analysis with dive integration
- ✅ Base image recommendations
- ✅ Wasted space detection
- ✅ Multi-stage build suggestions
- ✅ Layer squashing
- ✅ Efficiency scoring
- ✅ Size reduction strategies
- ✅ Comparative analysis

### Registry Features

- ✅ Multiple registry support
- ✅ Image push/pull operations
- ✅ Cross-registry synchronization
- ✅ Image promotion workflows
- ✅ Tag management
- ✅ Manifest operations
- ✅ Image cleanup policies
- ✅ Authentication management

### Linting Features

- ✅ Hadolint integration
- ✅ Custom rule engine
- ✅ Security anti-patterns
- ✅ Best practice validation
- ✅ OCI label compliance
- ✅ Auto-fix suggestions
- ✅ SARIF report generation
- ✅ Configurable severity levels

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   CLI Interface                          │
│              (Click + Rich Terminal UI)                  │
└────────────────┬────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┬─────────────┬──────────┐
    │            │            │             │          │
┌───▼──────┐ ┌──▼────────┐ ┌▼──────────┐ ┌▼────────┐ │
│  Build   │ │  Scanner  │ │ Optimizer │ │ Linter  │ │
│  Engine  │ │           │ │           │ │         │ │
└───┬──────┘ └──┬────────┘ └┬──────────┘ └┬────────┘ │
    │           │            │             │          │
┌───▼───────────▼────────────▼─────────────▼──────────▼─┐
│              Container Manager                         │
│         (Docker SDK / BuildKit)                        │
└────────────────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┬─────────────┐
    │            │            │             │
┌───▼──────┐ ┌──▼────────┐ ┌▼──────────┐ ┌▼────────────┐
│ Docker   │ │ Registry  │ │  Trivy    │ │  Hadolint   │
│ Engine   │ │  APIs     │ │  /Grype   │ │  /Dive      │
└──────────┘ └───────────┘ └───────────┘ └─────────────┘
```

### Module Structure

```
container_platform/
├── builder/          # Build engine with BuildKit
├── scanner/          # Security scanning (Trivy/Grype)
├── optimizer/        # Image optimization with dive
├── linter/           # Dockerfile linting
├── registry/         # Multi-registry client
├── manager/          # Container lifecycle management
└── cli/              # Command-line interface
```

## Installation

### Prerequisites

**System Requirements:**
- Python 3.9 or higher
- Docker Engine 20.10+ or Docker Desktop
- 2GB RAM minimum (4GB recommended)
- 10GB disk space

**External Tools (Optional but Recommended):**
- [Trivy](https://aquasecurity.github.io/trivy/) - Security scanning
- [Grype](https://github.com/anchore/grype) - Alternative scanner
- [hadolint](https://github.com/hadolint/hadolint) - Dockerfile linting
- [dive](https://github.com/wagoodman/dive) - Image analysis

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/your-org/devCrew_s1.git
cd devCrew_s1/tools/container_platform

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -m cli.container_cli --version
```

### Platform-Specific Installation

#### macOS

```bash
# Install Docker Desktop
brew install --cask docker

# Install external tools
brew install hadolint dive trivy
brew tap anchore/grype && brew install grype

# Install Python dependencies
pip install -r requirements.txt
```

#### Linux (Ubuntu/Debian)

```bash
# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install hadolint
wget -O /usr/local/bin/hadolint \
  https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64
chmod +x /usr/local/bin/hadolint

# Install dive
wget https://github.com/wagoodman/dive/releases/download/v0.11.0/dive_0.11.0_linux_amd64.deb
sudo apt install ./dive_0.11.0_linux_amd64.deb

# Install Trivy
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | \
  sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# Install Grype
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

# Install Python dependencies
pip install -r requirements.txt
```

#### Windows

```powershell
# Install Docker Desktop
# Download from https://www.docker.com/products/docker-desktop

# Install scoop (package manager)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
irm get.scoop.sh | iex

# Install tools via scoop
scoop bucket add main
scoop install hadolint dive

# Install Trivy
# Download from https://github.com/aquasecurity/trivy/releases

# Install Python dependencies
pip install -r requirements.txt
```

### Development Installation

```bash
# Install with development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v --cov

# Run linters
black .
isort .
flake8
mypy . --ignore-missing-imports
```

### Docker Installation (Containerized)

```bash
# Build container platform image
docker build -t container-platform:latest .

# Run CLI in container
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  container-platform:latest --help

# Create alias for convenience
alias container-cli='docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/workspace -w /workspace container-platform:latest'
```

## Quick Start

### Basic Workflow

```bash
# 1. Build an image
container-cli build image ./my-app \
  --tag myapp:latest \
  --tag myapp:1.0.0

# 2. Lint the Dockerfile
container-cli lint ./my-app/Dockerfile

# 3. Scan for vulnerabilities
container-cli scan myapp:latest \
  --severity HIGH \
  --output scan-report.json

# 4. Optimize the image
container-cli optimize myapp:latest \
  --level balanced

# 5. Push to registry
container-cli push myapp:latest \
  --registry myregistry.com \
  --username myuser

# 6. List containers
container-cli list --type containers
```

### Example: Complete CI/CD Pipeline

```bash
#!/bin/bash
# ci-pipeline.sh

set -e

IMAGE_NAME="myapp"
IMAGE_TAG="v1.0.0"
REGISTRY="docker.io/myorg"

echo "==> Building image..."
container-cli build image . \
  --tag ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
  --tag ${REGISTRY}/${IMAGE_NAME}:latest \
  --platform linux/amd64 \
  --platform linux/arm64 \
  --build-arg VERSION=${IMAGE_TAG}

echo "==> Linting Dockerfile..."
container-cli lint Dockerfile --strict

echo "==> Scanning for vulnerabilities..."
container-cli scan ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
  --severity CRITICAL \
  --format json \
  --output scan-results.json

# Exit if critical vulnerabilities found
if [ $? -ne 0 ]; then
  echo "Critical vulnerabilities detected!"
  exit 1
fi

echo "==> Analyzing image..."
container-cli optimize ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
  --use-dive

echo "==> Pushing to registry..."
container-cli push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
container-cli push ${REGISTRY}/${IMAGE_NAME}:latest

echo "==> Pipeline complete!"
```

## CLI Reference

### Global Options

```
--config PATH      Configuration file path
--verbose, -v      Enable verbose logging
--json             Output in JSON format
--help             Show help message
```

### Build Commands

#### build image

Build a container image from Dockerfile.

```bash
container-cli build image CONTEXT [OPTIONS]
```

**Arguments:**
- `CONTEXT` - Build context directory (required)

**Options:**
- `--dockerfile, -f PATH` - Path to Dockerfile (default: CONTEXT/Dockerfile)
- `--tag, -t TAG` - Image tag(s), can be specified multiple times
- `--platform PLATFORM` - Target platform(s): linux/amd64, linux/arm64, linux/arm/v7
- `--build-arg KEY=VALUE` - Build arguments
- `--target STAGE` - Build target stage in multi-stage Dockerfile
- `--no-cache` - Disable build cache
- `--pull` - Always pull base images (default: true)
- `--backend BACKEND` - Build backend: docker, buildkit (default: buildkit)

**Examples:**

```bash
# Basic build
container-cli build image ./app --tag myapp:latest

# Multi-platform build with BuildKit
container-cli build image ./app \
  --tag myapp:latest \
  --platform linux/amd64 \
  --platform linux/arm64 \
  --backend buildkit

# Build with arguments
container-cli build image ./app \
  --tag myapp:1.0.0 \
  --build-arg VERSION=1.0.0 \
  --build-arg ENVIRONMENT=production \
  --target production

# No cache build
container-cli build image ./app \
  --tag myapp:latest \
  --no-cache \
  --pull
```

### Push/Pull Commands

#### push

Push image to container registry.

```bash
container-cli push IMAGE [OPTIONS]
```

**Arguments:**
- `IMAGE` - Image name with tag (e.g., myapp:latest)

**Options:**
- `--registry URL` - Registry URL
- `--username USER` - Registry username
- `--password PASS` - Registry password
- `--registry-type TYPE` - Registry type: dockerhub, ecr, gcr, acr, harbor, generic

**Examples:**

```bash
# Push to Docker Hub
container-cli push myapp:latest \
  --registry docker.io \
  --username myuser \
  --password $DOCKER_PASSWORD

# Push to AWS ECR
container-cli push myapp:latest \
  --registry 123456789.dkr.ecr.us-east-1.amazonaws.com \
  --registry-type ecr

# Push to Harbor
container-cli push myapp:latest \
  --registry harbor.company.com \
  --registry-type harbor \
  --username admin
```

#### pull

Pull image from container registry.

```bash
container-cli pull IMAGE [OPTIONS]
```

**Options:** Same as `push` command

**Examples:**

```bash
# Pull from Docker Hub
container-cli pull nginx:latest

# Pull from private registry
container-cli pull myregistry.com/myapp:latest \
  --username myuser \
  --password $PASSWORD
```

### Security Scanning

#### scan

Scan container image for security vulnerabilities.

```bash
container-cli scan IMAGE [OPTIONS]
```

**Arguments:**
- `IMAGE` - Image name to scan

**Options:**
- `--scanner TYPE` - Scanner to use: trivy, grype, both (default: trivy)
- `--severity LEVEL` - Minimum severity: CRITICAL, HIGH, MEDIUM, LOW (default: MEDIUM)
- `--output, -o FILE` - Output file path
- `--format FORMAT` - Output format: json, sarif, table (default: table)

**Examples:**

```bash
# Basic scan with Trivy
container-cli scan myapp:latest

# Scan with high severity threshold
container-cli scan myapp:latest \
  --severity HIGH \
  --scanner trivy

# Scan with both scanners
container-cli scan myapp:latest \
  --scanner both \
  --severity MEDIUM

# Generate SARIF report
container-cli scan myapp:latest \
  --format sarif \
  --output scan-results.sarif

# JSON output for automation
container-cli scan myapp:latest \
  --format json \
  --output scan.json
```

### Image Optimization

#### optimize

Analyze and optimize container image.

```bash
container-cli optimize IMAGE [OPTIONS]
```

**Arguments:**
- `IMAGE` - Image name to optimize

**Options:**
- `--output, -o NAME` - Output optimized image name
- `--level LEVEL` - Optimization level: conservative, balanced, aggressive (default: balanced)
- `--use-dive` - Use dive tool for deep analysis (default: true)

**Examples:**

```bash
# Analyze image
container-cli optimize myapp:latest

# Optimize with aggressive level
container-cli optimize myapp:latest \
  --level aggressive \
  --output myapp:optimized

# Conservative optimization
container-cli optimize myapp:latest \
  --level conservative \
  --use-dive
```

### Dockerfile Linting

#### lint

Lint Dockerfile for best practices and security issues.

```bash
container-cli lint DOCKERFILE [OPTIONS]
```

**Arguments:**
- `DOCKERFILE` - Path to Dockerfile

**Options:**
- `--strict` - Fail on warnings
- `--output, -o FILE` - Output file path

**Examples:**

```bash
# Basic lint
container-cli lint Dockerfile

# Strict mode (warnings as errors)
container-cli lint Dockerfile --strict

# Save results to file
container-cli lint Dockerfile \
  --output lint-results.json \
  --json
```

### Registry Synchronization

#### sync

Synchronize image between registries.

```bash
container-cli sync SOURCE_IMAGE TARGET_REGISTRY [OPTIONS]
```

**Arguments:**
- `SOURCE_IMAGE` - Source image name
- `TARGET_REGISTRY` - Target registry URL

**Options:**
- `--source-registry URL` - Source registry URL (default: docker.io)
- `--target-image NAME` - Target image name (defaults to source)
- `--source-username USER` - Source registry username
- `--source-password PASS` - Source registry password
- `--target-username USER` - Target registry username
- `--target-password PASS` - Target registry password

**Examples:**

```bash
# Sync from Docker Hub to private registry
container-cli sync nginx:latest myregistry.com \
  --target-username admin \
  --target-password $PASSWORD

# Sync with different name
container-cli sync myapp:v1.0 prodregistry.com \
  --target-image production/myapp:v1.0

# Cross-cloud sync (ECR to GCR)
container-cli sync 123.dkr.ecr.us-east-1.amazonaws.com/myapp:latest \
  gcr.io/myproject \
  --source-registry-type ecr \
  --target-registry-type gcr
```

### Resource Management

#### prune

Clean up unused containers and images.

```bash
container-cli prune [OPTIONS]
```

**Options:**
- `--containers` - Prune stopped containers
- `--images` - Prune unused images
- `--all` - Prune all unused resources
- `--force, -f` - Do not prompt for confirmation

**Examples:**

```bash
# Prune containers
container-cli prune --containers

# Prune images
container-cli prune --images

# Prune everything
container-cli prune --all --force
```

#### list

List containers or images.

```bash
container-cli list [OPTIONS]
```

**Options:**
- `--type TYPE` - Resource type: containers, images (default: containers)
- `--all, -a` - Show all (including stopped)
- `--filter FILTER` - Filter (key=value)

**Examples:**

```bash
# List running containers
container-cli list

# List all containers
container-cli list --all

# List images
container-cli list --type images

# Filter by label
container-cli list --filter label=env=production
```

#### logs

Stream container logs.

```bash
container-cli logs CONTAINER [OPTIONS]
```

**Arguments:**
- `CONTAINER` - Container ID or name

**Options:**
- `--follow, -f` - Follow log output
- `--tail N` - Number of lines to show from end
- `--timestamps, -t` - Show timestamps

**Examples:**

```bash
# View logs
container-cli logs my-container

# Follow logs
container-cli logs my-container --follow

# Last 100 lines with timestamps
container-cli logs my-container --tail 100 --timestamps
```

### Configuration Management

#### config set

Set configuration value.

```bash
container-cli config set KEY VALUE
```

**Examples:**

```bash
# Set registry URL
container-cli config set registry.url myregistry.com

# Set scanner preference
container-cli config set security.scanner trivy

# Set optimization level
container-cli config set optimization.level balanced
```

#### config get

Get configuration value.

```bash
container-cli config get KEY
```

**Examples:**

```bash
# Get registry URL
container-cli config get registry.url

# Get scanner type
container-cli config get security.scanner
```

#### config list

List all configuration.

```bash
container-cli config list
```

## Configuration

### Configuration File

The tool uses YAML configuration files. Default location: `~/.container-platform/config.yaml`

**Example configuration:**

```yaml
# Registry settings
registry:
  url: "docker.io"
  type: "dockerhub"
  username: "myuser"

# Build settings
build:
  backend: "buildkit"
  platforms:
    - "linux/amd64"
  cache:
    enabled: true

# Security scanning
security:
  scanner: "trivy"
  severity_threshold: "MEDIUM"
  scan_misconfig: true
  scan_secrets: true

# Optimization
optimization:
  use_dive: true
  level: "balanced"

# Linting
linting:
  use_hadolint: true
  strict_mode: false
```

See [container-config.yaml](./container-config.yaml) for complete example.

### Environment Variables

```bash
# Docker daemon URL
export DOCKER_HOST=unix:///var/run/docker.sock

# Registry credentials
export REGISTRY_USERNAME=myuser
export REGISTRY_PASSWORD=mypass

# AWS credentials (for ECR)
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# Google Cloud credentials (for GCR)
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# Azure credentials (for ACR)
export AZURE_SUBSCRIPTION_ID=your_subscription
```

## Modules

### Build Engine

The build engine provides comprehensive image building capabilities.

**Python API:**

```python
from builder.build_engine import BuildEngine, BuildContext, Platform

# Create build context
context = BuildContext(
    dockerfile_path=Path("Dockerfile"),
    context_path=Path("."),
    tags=["myapp:latest"],
    platforms=[Platform.AMD64, Platform.ARM64],
    build_args={"VERSION": "1.0.0"},
    no_cache=False,
    pull=True
)

# Initialize engine
engine = BuildEngine(backend=BuildBackend.BUILDKIT)

# Build image
image_id, metrics = engine.build(context)

print(f"Built image: {image_id}")
print(f"Duration: {metrics.duration_seconds}s")
print(f"Size: {metrics.image_size_bytes / 1024 / 1024}MB")
```

**Features:**

- Multi-platform builds
- BuildKit integration
- Build argument injection
- Secret management
- Cache optimization
- Progress tracking
- Parallel builds
- Build metrics

### Security Scanner

Comprehensive vulnerability scanning with Trivy and Grype.

**Python API:**

```python
from scanner.security_scanner import SecurityScanner, ScannerConfig, ScannerType

# Configure scanner
config = ScannerConfig(
    scanner_type=ScannerType.TRIVY,
    severity_threshold=SeverityLevel.MEDIUM,
    scan_misconfig=True,
    scan_secrets=True,
    enable_cache=True
)

# Create scanner
scanner = SecurityScanner(config)

# Scan image
result = scanner.scan_image("myapp:latest")

# Display results
print(f"Total vulnerabilities: {result.total_vulnerabilities}")
print(f"Critical: {result.critical_count}")
print(f"High: {result.high_count}")
print(f"Fixable: {result.fixable_count}")

# Get suggestions
for vuln in result.vulnerabilities:
    if vuln.severity == SeverityLevel.CRITICAL:
        print(f"CVE: {vuln.id}")
        print(f"Package: {vuln.package_name}")
        print(f"Fix: {vuln.fixed_version}")
```

**Supported Scanners:**

- **Trivy**: Comprehensive vulnerability scanner
- **Grype**: Fast vulnerability scanner
- **Both**: Aggregate results from both scanners

**Features:**

- CVE detection
- Misconfiguration scanning
- Secret detection
- License compliance
- SBOM generation
- Result caching
- Ignore lists
- Multiple output formats

### Image Optimizer

Analyze and optimize container images for size and efficiency.

**Python API:**

```python
from optimizer.image_optimizer import ImageOptimizer, OptimizationLevel

# Initialize optimizer
optimizer = ImageOptimizer()

# Analyze image
analysis = optimizer.analyze_image("myapp:latest", use_dive=True)

print(f"Total size: {analysis.total_size / 1024 / 1024}MB")
print(f"Wasted space: {analysis.wasted_space / 1024 / 1024}MB")
print(f"Efficiency: {analysis.efficiency_score}%")
print(f"Layers: {analysis.layer_count}")

# Get optimization suggestions
for suggestion in analysis.suggestions:
    print(f"[{suggestion.priority}] {suggestion.category}")
    print(f"  {suggestion.description}")
    print(f"  Potential savings: {suggestion.potential_savings / 1024 / 1024}MB")

# Apply optimizations
result = optimizer.optimize_image(
    "myapp:latest",
    level=OptimizationLevel.BALANCED,
    new_tag="myapp:optimized"
)

print(f"Original: {result.original_size / 1024 / 1024}MB")
print(f"Optimized: {result.optimized_size / 1024 / 1024}MB")
print(f"Saved: {result.percentage_saved}%")
```

**Features:**

- Layer analysis
- Dive integration
- Base image recommendations
- Wasted space detection
- Multi-stage build suggestions
- Layer squashing
- Efficiency scoring
- Comparative analysis

### Dockerfile Linter

Validate Dockerfiles for best practices and security.

**Python API:**

```python
from linter.dockerfile_linter import DockerfileLinter

# Initialize linter
linter = DockerfileLinter(strict_mode=False)

# Lint Dockerfile
result = linter.lint_file("Dockerfile")

print(f"Total lines: {result.total_lines}")
print(f"Errors: {result.error_count}")
print(f"Warnings: {result.warning_count}")
print(f"Has healthcheck: {result.has_healthcheck}")
print(f"Has non-root user: {result.has_user}")

# Display findings
for finding in result.findings:
    print(f"[{finding.severity.value}] {finding.rule_id}")
    print(f"  Line {finding.line_number}: {finding.description}")
    if finding.fix_suggestion:
        print(f"  Fix: {finding.fix_suggestion}")

# Generate report
json_report = linter.generate_report(result, format="json")
sarif_report = linter.generate_report(result, format="sarif")
```

**Features:**

- Hadolint integration
- Custom rule engine
- Security checks
- Best practice validation
- OCI label compliance
- Auto-fix suggestions
- SARIF output
- Configurable severity

### Registry Client

Multi-registry support for image management.

**Python API:**

```python
from registry.registry_client import RegistryClient, RegistryConfig, RegistryType

# Configure registry
config = RegistryConfig(
    registry_type=RegistryType.DOCKER_HUB,
    url="docker.io",
    username="myuser",
    password="mypassword"
)

# Create client
client = RegistryClient(config)

# Push image
image_info = client.push_image("myapp", "latest")
print(f"Pushed: {image_info.full_name}")
print(f"Digest: {image_info.digest}")

# Pull image
image_info = client.pull_image("nginx", "latest")

# List repositories
repos = client.list_repositories()
for repo in repos:
    print(f"Repository: {repo}")

# List tags
tags = client.list_tags("myapp")
for tag in tags:
    print(f"Tag: {tag}")

# Sync between registries
target_client = RegistryClient(target_config)
result = target_client.sync_image(
    source_registry=client,
    image_name="myapp",
    tag="latest"
)
```

**Supported Registries:**

- Docker Hub
- AWS ECR (Elastic Container Registry)
- Google GCR (Google Container Registry)
- Azure ACR (Azure Container Registry)
- Harbor (Private registry)
- Generic Docker Registry v2

**Features:**

- Authentication management
- Image push/pull
- Cross-registry sync
- Tag management
- Manifest operations
- Image cleanup
- Promotion workflows

### Container Manager

Complete container lifecycle management.

**Python API:**

```python
from manager.container_manager import (
    ContainerManager,
    ContainerConfig,
    PortMapping,
    ResourceLimits
)

# Initialize manager
manager = ContainerManager()

# Create container configuration
config = ContainerConfig(
    image="nginx:latest",
    name="my-nginx",
    ports=[PortMapping(container_port=80, host_port=8080)],
    resources=ResourceLimits(
        memory=536870912,  # 512MB
        cpu_shares=512
    ),
    environment={"ENV": "production"},
    restart_policy=RestartPolicy.UNLESS_STOPPED
)

# Create and start container
container_id = manager.create_container(config)
manager.start_container(container_id)

# Get container info
info = manager.get_container(container_id)
print(f"Container: {info.name}")
print(f"Status: {info.status}")
print(f"Image: {info.image}")

# Get statistics
stats = manager.get_container_stats(container_id)
print(f"CPU: {stats.cpu_percent}%")
print(f"Memory: {stats.memory_usage_mb}MB")

# Stream logs
for log_line in manager.stream_logs(container_id):
    print(log_line, end='')

# Stop and remove
manager.stop_container(container_id)
manager.remove_container(container_id)
```

**Features:**

- Container lifecycle operations
- Resource limits
- Health checks
- Network management
- Volume mounting
- Log streaming
- Statistics monitoring
- Container exec

## Security Scanning

### Vulnerability Detection

The security scanner integrates with industry-standard tools:

**Trivy Features:**
- OS package vulnerabilities
- Language-specific vulnerabilities (Python, Node.js, Go, etc.)
- Misconfiguration detection
- Secret scanning
- License scanning

**Grype Features:**
- Fast scanning
- Extensive CVE database
- Language-specific scanning
- SBOM support

### Scanning Workflow

```bash
# 1. Basic scan
container-cli scan myapp:latest

# 2. High severity only
container-cli scan myapp:latest --severity HIGH

# 3. Generate SBOM
container-cli scan myapp:latest --generate-sbom --format spdx-json

# 4. Custom ignore list
container-cli scan myapp:latest --ignore CVE-2023-12345

# 5. Save results
container-cli scan myapp:latest --output scan.json --format json
```

### Scan Result Interpretation

```
Scan Summary:
  Total Vulnerabilities: 15
  Critical: 2
  High: 5
  Medium: 6
  Low: 2
  Fixable: 12

Critical Vulnerabilities:
  CVE-2023-XXXXX - openssl (1.1.1 → 1.1.1q)
  CVE-2023-YYYYY - curl (7.74.0 → 7.81.0)
```

### SARIF Integration

```bash
# Generate SARIF report for GitHub Security
container-cli scan myapp:latest --format sarif --output results.sarif

# Upload to GitHub
gh api repos/owner/repo/code-scanning/sarifs \
  -F sarif=@results.sarif \
  -F commit_sha=$GITHUB_SHA \
  -F ref=$GITHUB_REF
```

## Image Optimization

### Optimization Strategies

The optimizer analyzes images and provides actionable recommendations:

1. **Base Image Optimization**
   - Switch from full to slim variants
   - Use Alpine Linux
   - Consider distroless images

2. **Layer Optimization**
   - Combine RUN commands
   - Remove package manager caches
   - Use .dockerignore

3. **Multi-stage Builds**
   - Separate build and runtime stages
   - Copy only necessary artifacts
   - Reduce final image size

4. **Dependency Management**
   - Use --no-install-recommends
   - Remove build dependencies
   - Pin versions

### Optimization Levels

```yaml
conservative:
  - Safe optimizations only
  - No structural changes
  - Minimal risk

balanced:
  - Common optimizations
  - Layer consolidation
  - Package cleanup

aggressive:
  - Maximum size reduction
  - Multi-stage conversion
  - Experimental features
```

### Analysis Report

```
Image Analysis: myapp:latest

Summary:
  Total Size:        850 MB
  Wasted Space:      120 MB
  Efficiency Score:  85.9%
  Layers:            42
  Potential Savings: 180 MB

Suggestions:
  [HIGH] Base Image
    Switch from python:3.11 to python:3.11-slim
    Potential Savings: 600 MB

  [HIGH] Layer Cleanup
    Layer abc123 has 45MB wasted space
    Add package cleanup: apt-get clean && rm -rf /var/lib/apt/lists/*

  [MEDIUM] Multi-stage Build
    Use multi-stage build to separate build tools from runtime
    Potential Savings: 150 MB

  [LOW] Layer Count
    Reduce layer count from 42 by combining RUN commands
    Potential Savings: 25 MB
```

## Multi-Registry Support

### Supported Registries

#### Docker Hub

```bash
# Configure
container-cli config set registry.url docker.io
container-cli config set registry.username myuser

# Push
container-cli push myapp:latest --registry-type dockerhub
```

#### AWS ECR

```bash
# Authenticate (AWS CLI required)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

# Push
container-cli push myapp:latest \
  --registry 123456789.dkr.ecr.us-east-1.amazonaws.com \
  --registry-type ecr
```

#### Google GCR

```bash
# Authenticate (gcloud CLI required)
gcloud auth configure-docker

# Push
container-cli push myapp:latest \
  --registry gcr.io/my-project \
  --registry-type gcr
```

#### Azure ACR

```bash
# Authenticate (Azure CLI required)
az acr login --name myregistry

# Push
container-cli push myapp:latest \
  --registry myregistry.azurecr.io \
  --registry-type acr
```

#### Harbor

```bash
# Push to Harbor
container-cli push myapp:latest \
  --registry harbor.company.com \
  --registry-type harbor \
  --username admin
```

### Image Promotion

```python
from registry.registry_client import ImagePromotionStage

# Promote from dev to staging
client.promote_image(
    image_name="myapp",
    current_stage=ImagePromotionStage.DEV,
    target_stage=ImagePromotionStage.STAGING,
    version="1.0.0"
)

# Promote to production (with validation)
if scan_result.critical_count == 0:
    client.promote_image(
        image_name="myapp",
        current_stage=ImagePromotionStage.STAGING,
        target_stage=ImagePromotionStage.PROD,
        version="1.0.0"
    )
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Container Build and Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Container Platform
        run: |
          pip install -r requirements.txt

      - name: Build Image
        run: |
          container-cli build image . \
            --tag myapp:${{ github.sha }} \
            --build-arg VERSION=${{ github.sha }}

      - name: Lint Dockerfile
        run: |
          container-cli lint Dockerfile --strict

      - name: Security Scan
        run: |
          container-cli scan myapp:${{ github.sha }} \
            --severity HIGH \
            --format sarif \
            --output results.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif

      - name: Optimize Image
        run: |
          container-cli optimize myapp:${{ github.sha }} \
            --level balanced

      - name: Push to Registry
        if: github.event_name == 'push'
        run: |
          container-cli push myapp:${{ github.sha }} \
            --registry ${{ secrets.REGISTRY_URL }} \
            --username ${{ secrets.REGISTRY_USERNAME }} \
            --password ${{ secrets.REGISTRY_PASSWORD }}
```

### GitLab CI

```yaml
stages:
  - build
  - scan
  - deploy

variables:
  IMAGE_NAME: myapp
  IMAGE_TAG: $CI_COMMIT_SHORT_SHA

build:
  stage: build
  script:
    - pip install -r requirements.txt
    - container-cli build image . --tag ${IMAGE_NAME}:${IMAGE_TAG}
  artifacts:
    paths:
      - scan-results.json

scan:
  stage: scan
  script:
    - container-cli scan ${IMAGE_NAME}:${IMAGE_TAG} \
        --severity HIGH \
        --format json \
        --output scan-results.json
  artifacts:
    reports:
      container_scanning: scan-results.json

deploy:
  stage: deploy
  script:
    - container-cli push ${IMAGE_NAME}:${IMAGE_TAG} \
        --registry ${CI_REGISTRY} \
        --username ${CI_REGISTRY_USER} \
        --password ${CI_REGISTRY_PASSWORD}
  only:
    - main
```

### Jenkins

```groovy
pipeline {
    agent any
    
    environment {
        IMAGE_NAME = 'myapp'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        REGISTRY = credentials('registry-credentials')
    }
    
    stages {
        stage('Build') {
            steps {
                sh """
                    container-cli build image . \
                        --tag ${IMAGE_NAME}:${IMAGE_TAG}
                """
            }
        }
        
        stage('Lint') {
            steps {
                sh """
                    container-cli lint Dockerfile --strict
                """
            }
        }
        
        stage('Security Scan') {
            steps {
                sh """
                    container-cli scan ${IMAGE_NAME}:${IMAGE_TAG} \
                        --severity HIGH \
                        --format json \
                        --output scan-results.json
                """
                archiveArtifacts 'scan-results.json'
            }
        }
        
        stage('Push') {
            when {
                branch 'main'
            }
            steps {
                sh """
                    container-cli push ${IMAGE_NAME}:${IMAGE_TAG} \
                        --registry ${REGISTRY_URL} \
                        --username ${REGISTRY_USR} \
                        --password ${REGISTRY_PSW}
                """
            }
        }
    }
}
```

## Troubleshooting

### Common Issues

#### Docker Connection Issues

**Problem:** Cannot connect to Docker daemon

```
Error: Connection refused
```

**Solution:**

```bash
# Check Docker is running
docker ps

# Check Docker socket
ls -l /var/run/docker.sock

# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Verify permissions
docker run hello-world
```

#### Build Failures

**Problem:** Build fails with "No space left on device"

**Solution:**

```bash
# Clean up Docker resources
container-cli prune --all --force

# Remove unused images
docker image prune -a

# Check disk space
df -h
```

#### Scanner Not Found

**Problem:** Trivy or Grype not found

```
Error: Scanner not available
```

**Solution:**

```bash
# Install Trivy
# macOS:
brew install trivy

# Linux:
sudo apt-get install trivy

# Install Grype
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh
```

#### Registry Authentication

**Problem:** Authentication failed

```
Error: 401 Unauthorized
```

**Solution:**

```bash
# Docker Hub
docker login

# ECR
aws ecr get-login-password | docker login --username AWS \
  --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

# GCR
gcloud auth configure-docker

# ACR
az acr login --name myregistry
```

#### BuildKit Issues

**Problem:** BuildKit not available

**Solution:**

```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Or use legacy builder
container-cli build image . --backend docker

# Check BuildKit support
docker buildx version
```

### Debug Mode

```bash
# Enable verbose logging
container-cli --verbose scan myapp:latest

# Enable debug logging
export LOG_LEVEL=DEBUG
container-cli scan myapp:latest

# Output to file
container-cli --verbose scan myapp:latest 2>&1 | tee debug.log
```

### Performance Issues

**Problem:** Scans or builds are slow

**Solution:**

```bash
# Enable caching
container-cli config set security.enable_cache true
container-cli config set build.cache.enabled true

# Use local cache
container-cli config set build.cache.from "type=local,src=/tmp/cache"

# Increase parallel builds
container-cli config set build.max_parallel_builds 8

# Skip database updates
container-cli scan myapp:latest --skip-db-update
```

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/devCrew_s1.git
cd devCrew_s1/tools/container_platform

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v --cov --cov-report=html
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_builder.py -v

# Run integration tests
pytest tests/integration/ -v --integration

# Run with markers
pytest -m "not slow" -v
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8 --max-line-length=88

# Type checking
mypy . --ignore-missing-imports

# Security checks
bandit -r . -x tests/

# Run all checks
pre-commit run --all-files
```

### Building Documentation

```bash
# Install documentation dependencies
pip install sphinx sphinx-rtd-theme

# Build HTML documentation
cd docs
make html

# View documentation
open _build/html/index.html
```

## API Reference

### Build Engine API

```python
class BuildEngine:
    """Container image build engine."""
    
    def __init__(
        self,
        backend: BuildBackend = BuildBackend.BUILDKIT,
        timeout: int = 600,
        max_parallel_builds: int = 4
    ) -> None:
        """Initialize build engine."""
        pass
    
    def build(
        self,
        context: BuildContext,
        progress_callback: Optional[Callable] = None
    ) -> Tuple[str, BuildMetrics]:
        """Build container image."""
        pass
    
    async def build_async(
        self,
        context: BuildContext,
        progress_callback: Optional[Callable] = None
    ) -> Tuple[str, BuildMetrics]:
        """Build image asynchronously."""
        pass
    
    async def build_batch(
        self,
        contexts: List[BuildContext],
        progress_callback: Optional[Callable] = None
    ) -> List[Tuple[str, BuildMetrics]]:
        """Build multiple images in parallel."""
        pass
```

### Security Scanner API

```python
class SecurityScanner:
    """Container security scanner."""
    
    def __init__(self, config: ScannerConfig) -> None:
        """Initialize scanner."""
        pass
    
    def scan_image(
        self,
        image: str,
        generate_sbom: bool = False,
        sbom_format: SBOMFormat = SBOMFormat.SPDX_JSON
    ) -> ScanResult:
        """Scan image for security issues."""
        pass
    
    def generate_sbom(
        self,
        image: str,
        format: SBOMFormat
    ) -> Dict[str, Any]:
        """Generate Software Bill of Materials."""
        pass
    
    def update_vulnerability_database(
        self,
        scanner: Optional[str] = None
    ) -> None:
        """Update vulnerability database."""
        pass
```

### Image Optimizer API

```python
class ImageOptimizer:
    """Container image optimizer."""
    
    def __init__(
        self,
        docker_client: Optional[DockerClient] = None
    ) -> None:
        """Initialize optimizer."""
        pass
    
    def analyze_image(
        self,
        image_name: str,
        use_dive: bool = True
    ) -> ImageAnalysis:
        """Analyze image for optimization opportunities."""
        pass
    
    def optimize_image(
        self,
        image_name: str,
        level: OptimizationLevel = OptimizationLevel.BALANCED,
        new_tag: Optional[str] = None
    ) -> OptimizationResult:
        """Apply optimizations to image."""
        pass
    
    def compare_images(
        self,
        image1: str,
        image2: str
    ) -> Dict[str, Any]:
        """Compare two images."""
        pass
```

## Examples

### Example 1: Complete Build Pipeline

```python
#!/usr/bin/env python3
"""Complete container build pipeline."""

from pathlib import Path
from builder.build_engine import BuildEngine, BuildContext, Platform
from scanner.security_scanner import SecurityScanner, ScannerConfig
from optimizer.image_optimizer import ImageOptimizer
from registry.registry_client import RegistryClient, RegistryConfig

def build_pipeline(app_path: Path, image_name: str, version: str):
    """Run complete build pipeline."""
    
    # 1. Build image
    print("Building image...")
    engine = BuildEngine()
    context = BuildContext(
        dockerfile_path=app_path / "Dockerfile",
        context_path=app_path,
        tags=[f"{image_name}:{version}", f"{image_name}:latest"],
        platforms=[Platform.AMD64, Platform.ARM64],
        build_args={"VERSION": version}
    )
    image_id, build_metrics = engine.build(context)
    print(f"Built: {image_id} in {build_metrics.duration_seconds}s")
    
    # 2. Security scan
    print("Scanning for vulnerabilities...")
    scanner = SecurityScanner(ScannerConfig())
    scan_result = scanner.scan_image(f"{image_name}:{version}")
    
    if scan_result.critical_count > 0:
        print(f"CRITICAL: Found {scan_result.critical_count} critical vulnerabilities!")
        return False
    
    print(f"Scan passed: {scan_result.total_vulnerabilities} total vulns")
    
    # 3. Optimize
    print("Analyzing optimization opportunities...")
    optimizer = ImageOptimizer()
    analysis = optimizer.analyze_image(f"{image_name}:{version}")
    
    print(f"Efficiency: {analysis.efficiency_score}%")
    print(f"Wasted space: {analysis.wasted_space / 1024 / 1024}MB")
    
    # 4. Push to registry
    print("Pushing to registry...")
    registry = RegistryClient(RegistryConfig(
        registry_type=RegistryType.DOCKER_HUB,
        url="docker.io",
        username="myuser"
    ))
    
    registry.push_image(image_name, version)
    print("Push complete!")
    
    return True

if __name__ == "__main__":
    success = build_pipeline(
        app_path=Path("./myapp"),
        image_name="myorg/myapp",
        version="1.0.0"
    )
    
    exit(0 if success else 1)
```

### Example 2: Multi-Registry Sync

```python
#!/usr/bin/env python3
"""Sync images across multiple registries."""

from registry.registry_client import (
    RegistryClient,
    RegistryConfig,
    RegistryType
)

def sync_registries():
    """Sync image from Docker Hub to private registries."""
    
    # Source registry (Docker Hub)
    source = RegistryClient(RegistryConfig(
        registry_type=RegistryType.DOCKER_HUB,
        url="docker.io",
        username="myuser"
    ))
    
    # Target registries
    targets = [
        RegistryClient(RegistryConfig(
            registry_type=RegistryType.HARBOR,
            url="harbor.company.com",
            username="admin"
        )),
        RegistryClient(RegistryConfig(
            registry_type=RegistryType.ECR,
            url="123.dkr.ecr.us-east-1.amazonaws.com",
            region="us-east-1"
        ))
    ]
    
    # Images to sync
    images = [
        ("myapp", "1.0.0"),
        ("myapp", "latest"),
    ]
    
    for image_name, tag in images:
        print(f"Syncing {image_name}:{tag}...")
        
        for target in targets:
            try:
                result = target.sync_image(
                    source_registry=source,
                    image_name=image_name,
                    tag=tag
                )
                print(f"  → {result.full_name}")
            except Exception as e:
                print(f"  ✗ Failed: {e}")
    
    print("Sync complete!")

if __name__ == "__main__":
    sync_registries()
```

### Example 3: Automated Optimization

```python
#!/usr/bin/env python3
"""Automated image optimization pipeline."""

from optimizer.image_optimizer import (
    ImageOptimizer,
    OptimizationLevel
)

def optimize_all_images(threshold: float = 90.0):
    """Optimize all images below efficiency threshold."""
    
    optimizer = ImageOptimizer()
    
    # Get all images
    images = optimizer.client.images.list()
    
    results = []
    for image in images:
        if not image.tags:
            continue
        
        image_name = image.tags[0]
        print(f"\nAnalyzing {image_name}...")
        
        # Analyze
        analysis = optimizer.analyze_image(image_name, use_dive=True)
        
        if analysis.efficiency_score < threshold:
            print(f"  Efficiency: {analysis.efficiency_score}% (below {threshold}%)")
            print(f"  Optimizing...")
            
            # Optimize
            result = optimizer.optimize_image(
                image_name,
                level=OptimizationLevel.BALANCED,
                new_tag=f"{image_name}-optimized"
            )
            
            if result.success:
                print(f"  ✓ Saved {result.percentage_saved:.1f}%")
                results.append({
                    "image": image_name,
                    "original_size": result.original_size,
                    "optimized_size": result.optimized_size,
                    "saved": result.percentage_saved
                })
            else:
                print(f"  ✗ Failed: {result.error_message}")
        else:
            print(f"  Efficiency: {analysis.efficiency_score}% (OK)")
    
    # Summary
    print("\n=== Optimization Summary ===")
    total_saved = sum(r["saved"] for r in results)
    print(f"Images optimized: {len(results)}")
    print(f"Average savings: {total_saved / len(results) if results else 0:.1f}%")

if __name__ == "__main__":
    optimize_all_images()
```

## Contributing

We welcome contributions to the Container Platform Management tool!

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `pytest tests/ -v`
5. **Run linters**: `pre-commit run --all-files`
6. **Commit your changes**: `git commit -m 'Add amazing feature'`
7. **Push to the branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Contribution Guidelines

- Follow PEP 8 style guide
- Write comprehensive tests (aim for 85%+ coverage)
- Add docstrings to all public methods
- Update documentation for new features
- Run pre-commit hooks before committing
- Write clear commit messages

### Development Workflow

```bash
# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install

# Make changes
# ...

# Run tests
pytest tests/ -v --cov

# Check code quality
black .
isort .
flake8
mypy . --ignore-missing-imports

# Commit
git add .
git commit -m "feat: add new feature"
git push
```

### Reporting Issues

When reporting issues, please include:

- Python version
- Docker version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages and logs

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Docker](https://www.docker.com/) - Container platform
- [BuildKit](https://github.com/moby/buildkit) - Modern build backend
- [Trivy](https://aquasecurity.github.io/trivy/) - Security scanner
- [Grype](https://github.com/anchore/grype) - Vulnerability scanner
- [hadolint](https://github.com/hadolint/hadolint) - Dockerfile linter
- [dive](https://github.com/wagoodman/dive) - Image analyzer
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal UI

## Support

For questions, issues, or contributions:

- **Issues**: [GitHub Issues](https://github.com/your-org/devCrew_s1/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/devCrew_s1/discussions)
- **Email**: dev-crew@company.com

---

**Project**: devCrew_s1 Container Platform Management  
**Version**: 1.0.0  
**Last Updated**: 2024-12-03  
**Author**: DevCrew Container Platform Team
