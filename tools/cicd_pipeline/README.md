# CI/CD Pipeline Platform

**Issue #36 - TOOL-CICD-001**
**Priority:** HIGH (Phase 1 - Foundation)
**Protocol Coverage:** 26 protocols (31% coverage)

A comprehensive CI/CD pipeline platform built on GitHub Actions, providing workflow management, quality gates, deployment automation, and artifact handling.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Components](#components)
- [Workflow Templates](#workflow-templates)
- [Protocol Integration](#protocol-integration)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Features

### Core Capabilities

- **Pipeline Execution**: Trigger and monitor GitHub Actions workflows with custom parameters
- **Test Automation**: Run pytest, coverage analysis, and linting in CI
- **Deployment Management**: Deploy to dev/staging/production with approval gates
- **Artifact Handling**: Upload, download, and manage build artifacts
- **Quality Gates**: Enforce coverage ≥80%, security scans, code quality metrics
- **Status Monitoring**: Real-time workflow status tracking and reporting

### Technology Stack

- **GitHub Actions**: Native CI/CD platform
- **Python 3.11+**: Core implementation language
- **PyGithub**: GitHub API integration
- **pytest**: Testing framework with coverage
- **Bandit**: Security scanning
- **Radon**: Code complexity analysis

## Installation

### Prerequisites

- Python 3.11 or higher
- GitHub account with repository access
- GitHub Personal Access Token with `repo` and `workflow` scopes

### Setup

1. **Clone or download the Issue #36 files:**

```bash
# All files are prefixed with issue_36_
ls issue_36_*
```

2. **Install dependencies:**

```bash
pip install -r issue_36_requirements.txt
```

3. **Set up GitHub token:**

```bash
export GITHUB_TOKEN="your_github_personal_access_token"
```

4. **Configure the platform:**

```bash
# Edit issue_36_config.yaml with your repository details
vim issue_36_config.yaml
```

## Quick Start

### Basic Pipeline Usage

```python
from issue_36_pipeline_manager import PipelineManager

# Initialize pipeline manager
pipeline = PipelineManager(
    config_path="issue_36_config.yaml",
    token="your_github_token",  # or from GITHUB_TOKEN env
    repo_owner="your-org",
    repo_name="your-repo"
)

# Run quality gate workflow
result = pipeline.run_quality_gate(branch="main", wait=True)
print(f"Quality gate: {result['quality_passed']}")

# Deploy to staging
deployment = pipeline.deploy(
    environment="staging",
    version="v1.0.0",
    skip_quality_gate=False
)
print(f"Deployed: {deployment['run_url']}")

# Create release
release = pipeline.create_release(version="v1.0.0", branch="main")
print(f"Release: {release['run_url']}")
```

### Command-Line Usage

```bash
# Run quality gate
python -c "
from issue_36_pipeline_manager import PipelineManager
pm = PipelineManager(config_path='issue_36_config.yaml')
result = pm.run_quality_gate(branch='main', wait=True)
print(f'Quality passed: {result[\"quality_passed\"]}')
"

# Get pipeline status
python -c "
from issue_36_pipeline_manager import PipelineManager
pm = PipelineManager(config_path='issue_36_config.yaml')
status = pm.get_pipeline_status()
print(f'In progress: {status[\"in_progress\"]}, Success: {status[\"success\"]}')
"
```

## Components

### 1. Pipeline Manager (`issue_36_pipeline_manager.py`)

Main orchestration module coordinating all CI/CD operations.

**Key Methods:**
- `run_quality_gate()`: Execute quality gate workflow
- `run_tdd_workflow()`: Run TDD red-green-refactor workflow
- `deploy()`: Deploy to specified environment
- `create_release()`: Create GitHub release
- `get_pipeline_status()`: Get current pipeline status
- `validate_pipeline()`: Validate configuration

**Example:**

```python
from issue_36_pipeline_manager import PipelineManager

pipeline = PipelineManager(config_path="issue_36_config.yaml")

# Validate configuration
is_valid, issues = pipeline.validate_pipeline()
if not is_valid:
    print(f"Configuration issues: {issues}")

# Get status
status = pipeline.get_pipeline_status()
print(f"Total runs: {status['total_runs']}")
print(f"Success rate: {status['success']}/{status['completed']}")
```

### 2. GitHub Actions Wrapper (`issue_36_github_actions_wrapper.py`)

Clean interface to GitHub Actions API.

**Key Methods:**
- `list_workflows()`: List all workflows
- `trigger_workflow()`: Trigger workflow run
- `get_workflow_run()`: Get run details
- `wait_for_workflow_run()`: Poll until completion
- `cancel_workflow_run()`: Cancel running workflow
- `list_artifacts()`: List workflow artifacts
- `download_artifact()`: Download artifact

**Example:**

```python
from issue_36_github_actions_wrapper import GitHubActionsWrapper

github = GitHubActionsWrapper(
    token="your_token",
    repo_owner="your-org",
    repo_name="your-repo"
)

# List workflows
workflows = github.list_workflows()
for wf in workflows:
    print(f"{wf['name']}: {wf['state']}")

# Trigger workflow
github.trigger_workflow(
    workflow_id="quality_gate.yml",
    ref="main",
    inputs={"environment": "dev"}
)

# Wait for completion
conclusion, run_info = github.wait_for_workflow_run(
    run_id=12345,
    poll_interval=10,
    max_wait_time=1800
)
print(f"Workflow {conclusion}: {run_info['html_url']}")
```

### 3. Quality Gates (`issue_36_quality_gates.py`)

Validates code coverage, security scans, and code quality.

**Key Methods:**
- `validate_coverage()`: Check coverage against threshold
- `validate_security()`: Check security scan results
- `validate_code_quality()`: Check code quality metrics
- `validate_all()`: Run all validations
- `generate_report()`: Generate comprehensive report

**Example:**

```python
from issue_36_quality_gates import QualityGates
import yaml

with open("issue_36_config.yaml") as f:
    config = yaml.safe_load(f)

qg = QualityGates(config)

# Validate coverage
passed, coverage = qg.validate_coverage(
    "coverage.xml",
    fail_on_threshold=True
)
print(f"Coverage: {coverage.total_coverage:.2f}%")

# Validate security
passed, security = qg.validate_security(
    "security-report.json",
    fail_on_threshold=True
)
print(f"Security issues: H:{security.high_severity} M:{security.medium_severity}")

# Validate all
all_passed, report = qg.validate_all(
    coverage_path="coverage.xml",
    security_path="security.json",
    fail_fast=False
)
print(f"All gates passed: {all_passed}")
```

### 4. Artifact Manager (`issue_36_artifact_manager.py`)

Handles artifact upload, download, and lifecycle.

**Key Methods:**
- `list_artifacts()`: List available artifacts
- `download_artifact()`: Download single artifact
- `download_run_artifacts()`: Download all run artifacts
- `cleanup_artifacts()`: Clean up old artifacts
- `find_artifacts()`: Search artifacts by criteria
- `validate_artifacts()`: Validate expected artifacts exist

**Example:**

```python
from issue_36_artifact_manager import ArtifactManager
from issue_36_github_actions_wrapper import GitHubActionsWrapper

github = GitHubActionsWrapper(token="token", repo_owner="org", repo_name="repo")
artifacts = ArtifactManager(github, download_path="./artifacts")

# List artifacts
all_artifacts = artifacts.list_artifacts(run_id=12345)
for art in all_artifacts:
    print(f"{art['name']}: {art['size_mb']:.2f} MB")

# Download run artifacts
paths = artifacts.download_run_artifacts(
    run_id=12345,
    name_filter="coverage",
    extract=True
)
print(f"Downloaded to: {paths}")

# Validate expected artifacts
expected = ["coverage-reports", "test-results", "security-reports"]
all_present, missing = artifacts.validate_artifacts(12345, expected)
if not all_present:
    print(f"Missing artifacts: {missing}")
```

### 5. Deployment Manager (`issue_36_deployment_manager.py`)

Manages multi-environment deployments with approval gates.

**Key Methods:**
- `deploy()`: Deploy to environment
- `health_check()`: Perform health check
- `rollback()`: Rollback to previous version
- `validate_deployment()`: Validate deployment
- `approve_deployment()`: Approve pending deployment
- `plan_deployment()`: Generate deployment plan

**Example:**

```python
from issue_36_deployment_manager import DeploymentManager
from issue_36_github_actions_wrapper import GitHubActionsWrapper
import yaml

github = GitHubActionsWrapper(token="token", repo_owner="org", repo_name="repo")
with open("issue_36_config.yaml") as f:
    config = yaml.safe_load(f)

deployments = DeploymentManager(github, config)

# Plan deployment
plan = deployments.plan_deployment("production", "v1.0.0")
print(f"Deployment steps: {plan['steps']}")
print(f"Requires approval: {plan['requires_approval']}")

# Deploy to dev (no approval needed)
result = deployments.deploy(
    environment="dev",
    version="v1.0.0",
    skip_approval=True
)
print(f"Deployed: {result['run_url']}")

# Approve production deployment
deployments.approve_deployment("production", "devops-team")

# Deploy to production
result = deployments.deploy(
    environment="production",
    version="v1.0.0",
    skip_approval=False  # Will check for approval
)
```

## Workflow Templates

### 1. Quality Gate Workflow (`issue_36_workflow_quality_gate.yaml`)

Runs comprehensive quality checks on every push/PR.

**Features:**
- Test execution with pytest
- Coverage analysis (threshold: 80%)
- Security scanning (Bandit)
- Code quality checks (Flake8, Pylint, MyPy)
- Complexity analysis (Radon)
- Artifact upload (coverage, security, quality reports)

**Triggers:**
- Push to `main` or `develop`
- Pull requests
- Manual dispatch

**Usage:**
```bash
# Copy to .github/workflows/
cp issue_36_workflow_quality_gate.yaml .github/workflows/quality_gate.yml
git add .github/workflows/quality_gate.yml
git commit -m "Add quality gate workflow"
git push
```

### 2. TDD Workflow (`issue_36_workflow_tdd.yaml`)

Test-Driven Development workflow supporting red-green-refactor phases.

**Phases:**
- **Red**: Expects failing tests (validates TDD approach)
- **Green**: All tests must pass
- **Refactor**: Code quality checks while tests still pass
- **Full**: Execute all phases sequentially

**Usage:**
```bash
# Copy to .github/workflows/
cp issue_36_workflow_tdd.yaml .github/workflows/tdd.yml

# Trigger via GitHub UI or API
# Inputs: phase (red|green|refactor|full)
```

### 3. Deployment Workflow (`issue_36_workflow_deployment.yaml`)

Multi-environment deployment with approval gates and health checks.

**Environments:**
- **Dev**: Auto-deploy, no approval
- **Staging**: Requires approval, integration tests
- **Production**: Requires approval, health checks, rollback on failure

**Usage:**
```bash
# Copy to .github/workflows/
cp issue_36_workflow_deployment.yaml .github/workflows/deployment.yml

# Trigger deployment
python -c "
from issue_36_pipeline_manager import PipelineManager
pm = PipelineManager(config_path='issue_36_config.yaml')
pm.deploy(environment='staging', version='v1.0.0')
"
```

### 4. Release Workflow (`issue_36_workflow_release.yaml`)

Automated release creation with changelog generation.

**Features:**
- Version validation
- Quality gate enforcement
- Build artifact creation
- Changelog generation
- GitHub release creation
- Tag creation

**Usage:**
```bash
# Copy to .github/workflows/
cp issue_36_workflow_release.yaml .github/workflows/release.yml

# Create release
python -c "
from issue_36_pipeline_manager import PipelineManager
pm = PipelineManager(config_path='issue_36_config.yaml')
pm.create_release(version='v1.0.0', branch='main')
"
```

## Protocol Integration

This platform integrates with 26 protocols (31% coverage):

### Core Protocols

1. **P-TDD**: Test-Driven Development
   - Red-Green-Refactor workflow
   - Enforces test-first approach
   - Validates failing tests before implementation

2. **P-QGATE**: Quality Gate
   - Coverage threshold enforcement (≥80%)
   - Security vulnerability scanning
   - Code quality metrics validation

3. **P-DEVSECOPS**: DevSecOps
   - Security scanning in CI pipeline
   - Bandit for Python security analysis
   - Automated security reports

4. **P-DEPLOYMENT**: Deployment
   - Multi-environment support
   - Approval gates for production
   - Health check validation
   - Automatic rollback on failure

5. **P-RELEASE**: Release Management
   - Automated changelog generation
   - Version tagging
   - Artifact publishing
   - Release notes creation

### Additional Protocols (21 more)

See [Protocol Documentation](docs/protocols.md) for complete list.

## Usage Examples

### Example 1: Complete Quality Gate Check

```python
from issue_36_pipeline_manager import PipelineManager
from issue_36_quality_gates import QualityGates
import yaml

# Initialize
pipeline = PipelineManager(config_path="issue_36_config.yaml")

# Run quality gate workflow
qg_result = pipeline.run_quality_gate(branch="main", wait=True)

print(f"Run ID: {qg_result['run_id']}")
print(f"Status: {qg_result['status']}")
print(f"Quality Passed: {qg_result['quality_passed']}")
print(f"Artifacts: {qg_result['artifacts']}")

# Get detailed quality report
if qg_result['quality_report']:
    report = qg_result['quality_report']
    if 'gates' in report:
        print("\nQuality Gate Details:")
        if 'coverage' in report['gates']:
            cov = report['gates']['coverage']
            print(f"  Coverage: {cov['total_coverage']:.2f}% (threshold: {cov['threshold']}%)")
        if 'security' in report['gates']:
            sec = report['gates']['security']
            print(f"  Security: {sec['total_issues']} issues")
```

### Example 2: Staged Deployment Pipeline

```python
from issue_36_pipeline_manager import PipelineManager

pipeline = PipelineManager(config_path="issue_36_config.yaml")

version = "v1.2.0"

# Step 1: Deploy to dev
print(f"Deploying {version} to dev...")
dev_result = pipeline.deploy(
    environment="dev",
    version=version,
    skip_quality_gate=False  # Run quality checks first
)
print(f"✅ Dev deployment: {dev_result['run_url']}")

# Step 2: Deploy to staging (requires approval)
print(f"\nDeploying {version} to staging...")
try:
    staging_result = pipeline.deploy(
        environment="staging",
        version=version,
        skip_approval=False
    )
    print(f"✅ Staging deployment: {staging_result['run_url']}")
except Exception as e:
    print(f"⚠️ Approval required: {e}")

# Step 3: After approval, deploy to production
print(f"\nDeploying {version} to production...")
prod_result = pipeline.deploy(
    environment="production",
    version=version,
    skip_approval=False
)
print(f"✅ Production deployment: {prod_result['run_url']}")
```

### Example 3: Artifact Management

```python
from issue_36_artifact_manager import ArtifactManager
from issue_36_github_actions_wrapper import GitHubActionsWrapper

github = GitHubActionsWrapper(
    token="your_token",
    repo_owner="your-org",
    repo_name="your-repo"
)
artifacts = ArtifactManager(github, download_path="./artifacts")

# Find coverage artifacts from last week
coverage_artifacts = artifacts.find_artifacts(
    workflow_name="quality_gate.yml",
    branch="main",
    artifact_name="coverage"
)

print(f"Found {len(coverage_artifacts)} coverage artifacts")

# Download latest coverage report
if coverage_artifacts:
    latest = coverage_artifacts[0]
    path = artifacts.download_artifact(
        latest['id'],
        extract=True
    )
    print(f"Downloaded to: {path}")

# Get storage stats
stats = artifacts.get_storage_stats()
print(f"Total artifacts: {stats['total_artifacts']}")
print(f"Total size: {stats['total_size_mb']:.2f} MB")

# Cleanup old artifacts
old_artifacts = artifacts.cleanup_artifacts(
    older_than_days=90,
    dry_run=True
)
print(f"Would delete {len(old_artifacts)} old artifacts")
```

## Configuration

### Configuration File (`issue_36_config.yaml`)

```yaml
github:
  owner: "your-org"
  repo: "your-repo"
  token: "${GITHUB_TOKEN}"

quality_gates:
  coverage:
    minimum: 80.0
    target: 85.0
    enforcement: true

  security:
    max_high_severity: 0
    max_medium_severity: 5
    fail_on_high: true

  code_quality:
    max_complexity: 10
    max_duplication: 5.0

deployment:
  environments:
    dev:
      requires_approval: false
      auto_deploy: true
      health_check_url: "https://dev.example.com/health"

    staging:
      requires_approval: true
      approvers: ["devops-team"]
      health_check_url: "https://staging.example.com/health"

    production:
      requires_approval: true
      approvers: ["devops-team", "tech-leads"]
      health_check_url: "https://example.com/health"

  rollback_enabled: true
  health_check_timeout: 300

artifacts:
  retention_days: 90
  download_path: "./artifacts"

workflows:
  quality_gate: "quality_gate.yml"
  tdd: "tdd.yml"
  deployment: "deployment.yml"
  release: "release.yml"
```

### Environment Variables

```bash
# Required
export GITHUB_TOKEN="ghp_your_personal_access_token"

# Optional
export GITHUB_OWNER="your-org"
export GITHUB_REPO="your-repo"
```

## Testing

### Running Tests

```bash
# Run all tests
pytest issue_36_test_pipeline.py -v

# Run with coverage
pytest issue_36_test_pipeline.py --cov=. --cov-report=html --cov-report=term

# Run specific test class
pytest issue_36_test_pipeline.py::TestGitHubActionsWrapper -v

# Run specific test
pytest issue_36_test_pipeline.py::TestQualityGates::test_coverage_threshold_pass -v
```

### Test Coverage

Target: **85%+ coverage**

```bash
# Generate coverage report
pytest issue_36_test_pipeline.py \
  --cov=issue_36_pipeline_manager \
  --cov=issue_36_github_actions_wrapper \
  --cov=issue_36_quality_gates \
  --cov=issue_36_artifact_manager \
  --cov=issue_36_deployment_manager \
  --cov-report=html \
  --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Problem**: `Failed to authenticate with GitHub API`

**Solution**:
```bash
# Verify token is set
echo $GITHUB_TOKEN

# Check token scopes (needs repo, workflow)
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Regenerate token with correct scopes at:
# https://github.com/settings/tokens
```

#### 2. Workflow Not Found

**Problem**: `WorkflowNotFoundError: Workflow 'quality_gate.yml' not found`

**Solution**:
```bash
# List available workflows
python -c "
from issue_36_pipeline_manager import PipelineManager
pm = PipelineManager(config_path='issue_36_config.yaml')
workflows = pm.list_workflows()
for wf in workflows:
    print(f\"{wf['name']}: {wf['path']}\")
"

# Copy workflow templates to .github/workflows/
cp issue_36_workflow_*.yaml .github/workflows/
```

#### 3. Quality Gate Failures

**Problem**: Coverage below threshold

**Solution**:
```bash
# Run tests locally with coverage
pytest --cov=. --cov-report=term-missing

# Identify uncovered code
# Add tests for uncovered lines

# Adjust threshold temporarily (not recommended)
# Edit issue_36_config.yaml:
# quality_gates:
#   coverage:
#     minimum: 70.0  # Lower threshold
```

#### 4. Deployment Health Check Failures

**Problem**: Health check timeout

**Solution**:
```python
# Increase timeout in config
deployment:
  health_check_timeout: 600  # 10 minutes
  health_check_retries: 10

# Or skip health check for debugging
pipeline.deploy(
    environment="dev",
    version="v1.0.0",
    skip_health_check=True
)
```

## Best Practices

### 1. Quality Gates

- **Set realistic thresholds**: Start with 70% coverage, increase gradually
- **Fix security issues immediately**: Don't ignore high-severity findings
- **Review complexity regularly**: Refactor functions with complexity >10
- **Update thresholds in config**: Don't hardcode in workflows

### 2. Deployments

- **Always use quality gates**: Don't skip quality checks for production
- **Require approvals for production**: Multiple approvers recommended
- **Enable rollback**: Set `rollback_enabled: true`
- **Monitor health checks**: Configure appropriate timeouts
- **Test in staging first**: Validate before production deployment

### 3. Workflows

- **Use meaningful names**: Descriptive workflow and job names
- **Add comments**: Document complex workflow logic
- **Version control workflows**: Track changes in git
- **Test locally with `act`**: Validate before pushing

### 4. Artifacts

- **Clean up regularly**: Set appropriate retention periods
- **Use descriptive names**: Include version/date in artifact names
- **Validate artifacts**: Check expected artifacts exist
- **Monitor storage**: Track artifact storage usage

### 5. Security

- **Never commit tokens**: Use environment variables or secrets
- **Rotate tokens regularly**: Change tokens every 90 days
- **Use minimal scopes**: Only grant necessary permissions
- **Enable branch protection**: Require PR reviews and status checks
- **Scan dependencies**: Regularly update and scan dependencies

## Support

For issues, questions, or contributions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review [GitHub Issues](https://github.com/your-org/your-repo/issues)
3. Consult [Protocol Documentation](docs/protocols.md)

## License

[Your License Here]

## Credits

**Issue #36 - TOOL-CICD-001**
Implemented as part of devCrew_s1 project
All files prefixed with `issue_36_`
