# **Tool Name**: CI/CD Pipeline Platform

**Tool ID**: `TOOL-CICD-001`
**Version**: 1.0.0
**Status**: Active
**Owner**: DevOps Engineer, Backend Engineer, SRE
**Last Updated**: 2025-11-19

---

## **Part I: Tool Identity & Purpose**

### Tool Category
**CI/CD & DevOps Automation**

### Tool Capability
Enables autonomous agents to define, execute, and manage continuous integration and continuous deployment pipelines for automated building, testing, and deployment of applications. Provides infrastructure-as-code for CI/CD workflows with GitHub Actions as the primary platform, supporting parallel execution, quality gates, artifact management, and multi-environment deployments.

### Use Cases

**Use Case 1: Automated Testing Pipeline**
- **Scenario**: Execute comprehensive test suites on every code commit
- **Trigger**: Push to feature branch or pull request creation
- **Process**: Run unit tests → integration tests → E2E tests in parallel
- **Outcome**: Test reports, coverage metrics, pass/fail status
- **Integration**: P-TDD, P-QGATE protocols

**Use Case 2: Quality Gate Enforcement**
- **Scenario**: Enforce code quality standards before merge
- **Trigger**: Pull request opened or updated
- **Process**: Linting → type checking → security scan → test coverage validation
- **Outcome**: Quality gate pass/fail, automated PR comments
- **Integration**: P-QGATE, P-DEVSECOPS protocols

**Use Case 3: Multi-Environment Deployment**
- **Scenario**: Deploy application through dev → staging → production
- **Trigger**: Tag creation or manual workflow dispatch
- **Process**: Build artifacts → deploy to dev → automated tests → promote to staging → approval gate → production deployment
- **Outcome**: Versioned deployments with rollback capability
- **Integration**: P-DEPLOYMENT, P-RECOVERY protocols

**Use Case 4: Artifact Management**
- **Scenario**: Build, version, and publish release artifacts
- **Trigger**: Release tag or schedule
- **Process**: Build binaries → run tests → generate SBOM → publish to registry
- **Outcome**: Versioned artifacts in package registry
- **Integration**: P-FEATURE-DEV completion

**Use Case 5: Security and Compliance Scanning**
- **Scenario**: Automated security validation in pipeline
- **Trigger**: Every commit and pull request
- **Process**: SAST scan → dependency check → container scan → license compliance
- **Outcome**: Security reports, vulnerability alerts, compliance status
- **Integration**: P-DEVSECOPS, P-SEC-VULN protocols

### Strategic Value

**Business Value**
- Reduces deployment time from hours to minutes (10x improvement)
- Enables multiple daily deployments (continuous delivery)
- Accelerates feature delivery to customers (faster time-to-market)
- Reduces human error in release processes (99% error reduction)
- Provides audit trail for compliance and governance

**Technical Value**
- Infrastructure-as-code for reproducible workflows
- Parallel execution for faster feedback loops (<5 min builds)
- Matrix builds across platforms/versions/environments
- Integrated secret management with cloud providers
- Reusable workflow components and actions

**Risk Mitigation**
- Enforces quality gates before production (zero-defect policy)
- Enables quick rollback to previous versions (<5 min recovery)
- Detects breaking changes early (shift-left testing)
- Provides deployment audit trails (compliance ready)
- Automated security scanning (continuous security validation)

---

## **Part II: Functional Requirements**

### Core Capabilities

#### 1. Pipeline Execution
**Requirement**: Execute CI/CD workflows defined in YAML with complex job dependencies

**Acceptance Criteria**:
- Support for sequential and parallel job execution
- Job dependencies with conditional execution (if/else logic)
- Matrix builds (OS: [ubuntu, macos, windows], Python: [3.9, 3.10, 3.11])
- Workflow reuse and composition (reusable workflows)
- Timeout controls (job-level and step-level)

**Performance Targets**:
- Queue time: <10 seconds
- Job startup: <60 seconds
- Build completion: <5 minutes (typical)
- Test execution: <10 minutes (comprehensive suite)

#### 2. Test Automation
**Requirement**: Run automated tests with result aggregation and reporting

**Acceptance Criteria**:
- Support for multiple test frameworks (pytest, jest, selenium)
- Parallel test execution with sharding
- Test result parsing (JUnit XML, TAP)
- Code coverage collection and reporting
- Test artifact retention (screenshots, logs, videos)

**Performance Targets**:
- Unit tests: <2 minutes
- Integration tests: <5 minutes
- E2E tests: <10 minutes
- Test report generation: <30 seconds

#### 3. Deployment Management
**Requirement**: Orchestrate deployments to multiple environments with approval workflows

**Acceptance Criteria**:
- Environment-specific configurations (dev, staging, production)
- Deployment approval gates (manual or automated)
- Blue-green and canary deployment strategies
- Automatic rollback on failure detection
- Deployment status tracking and history

**Performance Targets**:
- Deployment execution: <5 minutes
- Health check validation: <2 minutes
- Rollback completion: <3 minutes

#### 4. Artifact Handling
**Requirement**: Build, version, store, and distribute build artifacts

**Acceptance Criteria**:
- Artifact upload/download between jobs
- Integration with package registries (npm, PyPI, Docker Hub)
- Artifact retention policies (90 days default)
- SBOM (Software Bill of Materials) generation
- Artifact signing and verification

**Performance Targets**:
- Artifact upload: <1 minute per 100 MB
- Artifact download: <30 seconds per 100 MB
- Registry publish: <2 minutes

#### 5. Workflow Orchestration
**Requirement**: Trigger and coordinate complex multi-workflow pipelines

**Acceptance Criteria**:
- Event-driven triggers (push, PR, schedule, webhook)
- Manual workflow dispatch with input parameters
- Workflow chaining (trigger downstream workflows)
- Branch and path filtering for selective execution
- Concurrency control (prevent parallel runs)

**Performance Targets**:
- Trigger latency: <5 seconds
- Workflow dispatch: <10 seconds
- Concurrent workflows: 20+ per repository

### Input/Output Specifications

#### Input Requirements

**Workflow Definition**:
```yaml
# Format: YAML (GitHub Actions syntax)
# Location: .github/workflows/*.yml
# Size limit: <10 MB per file
# Structure: name, on, jobs, env, defaults

Example:
name: CI Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
```

**Input Parameters**:
- Repository URL: `https://github.com/owner/repo`
- Git reference: Branch name, tag, or commit SHA
- Environment variables: Key-value pairs
- Secrets: Encrypted values (GitHub Secrets, Vault)
- Matrix configurations: Multi-dimensional build parameters

**Input Constraints**:
- Maximum 1000 jobs per workflow
- Maximum 72-hour runtime per job
- Maximum 256 jobs in matrix
- Maximum 10 reusable workflows per call

#### Output Requirements

**Build Outputs**:
- **Logs**: Structured logs with timestamps (JSON format available)
- **Artifacts**: Build binaries, Docker images, test reports, SBOM
- **Test Results**: JUnit XML, coverage reports (Cobertura, LCOV)
- **Status**: Success, failure, cancelled, skipped
- **Metrics**: Duration, resource usage, cost

**Output Schema**:
```json
{
  "workflow_run": {
    "id": 123456789,
    "status": "completed",
    "conclusion": "success",
    "created_at": "2025-11-19T10:00:00Z",
    "updated_at": "2025-11-19T10:05:00Z",
    "jobs": [
      {
        "id": 987654321,
        "name": "build",
        "status": "completed",
        "conclusion": "success",
        "steps": [...]
      }
    ],
    "artifacts": [
      {
        "name": "build-artifacts",
        "size_in_bytes": 1024000,
        "url": "https://api.github.com/repos/owner/repo/actions/artifacts/12345"
      }
    ]
  }
}
```

### Performance Requirements

**Throughput**:
- 1000+ concurrent workflows across organization
- 10,000+ workflow runs per repository per month
- 50+ parallel jobs per workflow run

**Latency**:
- Queue time: <10 seconds (99th percentile)
- Job startup: <60 seconds (cold start)
- Log streaming: <5 seconds delay
- Webhook delivery: <30 seconds

**Scalability**:
- Auto-scale runners based on queue depth
- Support 100+ self-hosted runners per organization
- Handle matrix builds with 256+ jobs

**Reliability**:
- Platform uptime: 99.9% (GitHub Actions SLA)
- Automatic retry on transient failures (3 attempts)
- Persistent job queue (no job loss)

### Integration Requirements

**Git Integration**:
- GitHub: Native integration (primary)
- GitLab: Via GitLab CI (alternative)
- Bitbucket: Via Bitbucket Pipelines (alternative)

**Cloud Providers**:
- AWS: OIDC authentication, ECS/Lambda deployment
- Azure: Service principal, AKS deployment
- GCP: Workload Identity, GKE deployment

**Notification Systems**:
- Slack: Workflow status notifications
- Email: Build failure alerts
- PagerDuty: Production deployment alerts
- GitHub: Commit status, PR comments

**API Integration**:
- REST API: GitHub API v3 for workflow management
- GraphQL: GitHub API v4 for complex queries
- Webhooks: Event-driven notifications
- CLI: `gh` GitHub CLI for automation

---

## **Part III: Non-Functional Requirements**

### Security Requirements

**Authentication & Authorization**:
- OAuth 2.0 for API access
- Personal Access Tokens (PAT) with scope control
- GitHub App authentication for organization-wide access
- OIDC for cloud provider federation (no long-lived credentials)
- RBAC: Repository permissions, environment protection rules

**Secret Management**:
- GitHub Secrets: Encrypted at rest (AES-256), masked in logs
- Environment secrets: Scope to specific environments
- Organization secrets: Shared across repositories
- Integration: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault
- Secret rotation: Automated with cloud provider integration

**Data Encryption**:
- At rest: AES-256 for secrets, artifacts, logs
- In transit: TLS 1.3 for API, webhook, log streaming
- Artifact signing: GPG, Sigstore/Cosign support

**Audit Logging**:
- All workflow executions logged with user attribution
- Configuration changes tracked (workflow edits, secret updates)
- Deployment history with approval chain
- API access logs with IP and user agent
- Retention: 90 days (audit logs), 400 days (GitHub Enterprise)

**Compliance**:
- SLSA Level 3: Provenance generation for builds
- SOC 2 Type II certified (GitHub)
- ISO 27001 certified
- GDPR compliant (data residency options)
- Audit-ready deployment trails

### Operational Requirements

**Deployment Models**:
- **SaaS (GitHub.com)**: Cloud-hosted, managed by GitHub
- **Self-Hosted Runners**: On-premise execution, cloud control plane
- **GitHub Enterprise Server**: Fully on-premise deployment
- **Hybrid**: Cloud workflows + self-hosted runners for sensitive workloads

**Platform Support**:
- **Linux**: Ubuntu 20.04/22.04, Debian, RHEL, Alpine (Docker)
- **Windows**: Server 2019/2022, Windows 10/11
- **macOS**: Monterey, Ventura, Sonoma
- **ARM64**: Linux ARM64 support (self-hosted)
- **GPU**: CUDA support for ML workloads (self-hosted)

**Resource Requirements**:
- **GitHub-hosted runners**: 2 vCPU, 7 GB RAM (Linux/Windows), 3 vCPU, 14 GB RAM (macOS)
- **Self-hosted runners**: 2+ vCPU, 8+ GB RAM (minimum), customizable
- **Storage**: 14 GB SSD (GitHub-hosted), 50+ GB (self-hosted recommended)
- **Network**: 1 Gbps (outbound for artifact downloads)

**Backup & Recovery**:
- Workflow definitions: Version-controlled in Git (no backup needed)
- Build history: Retained for 90 days (GitHub Actions)
- Artifacts: Configurable retention (default 90 days)
- Logs: Downloadable, exportable to external storage
- Disaster recovery: Multi-region redundancy (GitHub SaaS)

### Observability Requirements

**Logging**:
- **Structured logs**: JSON format with ISO 8601 timestamps
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Step-level granularity**: Individual command output
- **Retention**: 90 days (downloadable, exportable)
- **Search**: Full-text search in workflow logs (GitHub UI)

**Metrics**:
- **Success rate**: Workflow/job pass rate (%)
- **Duration**: P50/P95/P99 percentiles for workflows and jobs
- **Queue time**: Time from trigger to execution start
- **Runner utilization**: Active vs. idle runner time
- **Cost per run**: Billable minutes (GitHub Actions pricing)
- **Artifact size**: Total storage used per repository

**Tracing**:
- Workflow visualization: DAG view of job dependencies
- Job timeline: Gantt chart of parallel execution
- Step duration: Breakdown of time per step
- Distributed tracing: External tools (OpenTelemetry support via actions)

**Alerting**:
- **Failure notifications**: Email, Slack, Teams, PagerDuty
- **Long-running jobs**: Alert on timeout threshold
- **Runner health**: Self-hosted runner offline alerts
- **Quota warnings**: Usage approaching limits (billable minutes, storage)
- **Security alerts**: Secrets exposure, unauthorized access

### Governance Requirements

**Licensing**:
- **GitHub Actions (SaaS)**: Free tier (2,000 min/month), Team ($4/user/month), Enterprise
- **Self-hosted runners**: Free (no minute limits)
- **Alternative platforms**: Jenkins (open source), GitLab CI (open core), CircleCI (commercial)

**Vendor Lock-in Mitigation**:
- Workflow syntax: Portable to GitLab CI, CircleCI with adaptations
- Artifacts: Exportable to S3, Azure Blob, GCS
- Secrets: Migrate via API, Vault integration
- Self-hosted runners: Full control over execution environment

**Support**:
- **Community**: GitHub Community Forum, Stack Overflow
- **Enterprise support**: SLA-backed support (response time SLA)
- **Professional services**: Migration assistance, custom integrations
- **Documentation**: Comprehensive official docs, community guides

**Deprecation Policy**:
- **Breaking changes**: 12-month advance notice
- **Runner images**: LTS support for 18 months (Ubuntu LTS)
- **API versions**: Minimum 12-month support after deprecation announcement
- **Action versions**: Semantic versioning, major version support (v1, v2, v3)

---

## **Part IV: Integration Patterns**

### GitHub Actions Integration (Primary)

#### Workflow Syntax

**Basic Workflow Structure**:
```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
    paths-ignore: ['docs/**', '*.md']
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        type: choice
        options: [dev, staging, production]

env:
  PYTHON_VERSION: '3.11'

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  build:
    name: Build Application
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Save image
        run: docker save myapp:${{ github.sha }} | gzip > myapp.tar.gz

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: docker-image
          path: myapp.tar.gz
          retention-days: 30

  deploy:
    name: Deploy to Staging
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com

    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: docker-image

      - name: Deploy to staging
        run: |
          # Deployment logic here
          echo "Deploying to staging..."
```

#### Quality Gate Workflow

**P-QGATE Integration**:
```yaml
name: Quality Gate

on:
  pull_request:
    branches: [main, develop]

jobs:
  quality-gate:
    name: Quality Gate Validation
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for SonarQube

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install black isort flake8 pylint mypy bandit pytest pytest-cov

      - name: Code formatting check (Black)
        run: black --check .

      - name: Import sorting check (isort)
        run: isort --check-only .

      - name: Linting (Flake8)
        run: flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203

      - name: Static analysis (Pylint)
        run: pylint src/ --fail-under=8.0

      - name: Type checking (mypy)
        run: mypy src/ --ignore-missing-imports

      - name: Security scan (Bandit)
        run: bandit -r src/ -ll

      - name: Run tests with coverage
        run: pytest --cov=src --cov-report=xml --cov-report=term --cov-fail-under=80

      - name: SonarQube scan
        uses: sonarsource/sonarqube-scan-action@v2
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
          SONAR_HOST_URL: ${{ secrets.SONAR_HOST_URL }}

      - name: Quality Gate status
        uses: sonarsource/sonarqube-quality-gate-action@v1
        timeout-minutes: 5
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}

      - name: Comment PR with results
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const status = '${{ job.status }}';
            const body = status === 'success'
              ? '✅ Quality gate PASSED - All checks successful!'
              : '❌ Quality gate FAILED - Please fix issues before merging';
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

#### TDD Workflow

**P-TDD Integration**:
```yaml
name: TDD Workflow

on:
  push:
    branches: [feature/*, bugfix/*]

jobs:
  tdd-cycle:
    name: TDD Red-Green-Refactor
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: RED - Run tests (expect failures)
        id: red
        continue-on-error: true
        run: pytest -v --tb=short

      - name: Check for failing tests
        if: steps.red.outcome == 'success'
        run: |
          echo "Warning: All tests passing in RED phase - no new tests added?"
          exit 0

      - name: GREEN - Implement feature
        run: |
          # This step represents development
          # In practice, code changes are made locally
          echo "Implementing feature to make tests pass..."

      - name: Run tests again (expect success)
        run: pytest -v

      - name: REFACTOR - Code quality checks
        run: |
          black --check .
          pylint src/ --fail-under=8.0
          mypy src/ --ignore-missing-imports

      - name: Coverage check
        run: pytest --cov=src --cov-fail-under=80
```

#### Security Scanning Workflow

**P-DEVSECOPS Integration**:
```yaml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Monday

jobs:
  security:
    name: Security Analysis
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Dependency check (Safety)
        run: |
          pip install safety
          safety check --json --output safety-report.json

      - name: SAST scan (Bandit)
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json

      - name: Container scanning
        if: hashFiles('Dockerfile') != ''
        run: |
          docker build -t myapp:scan .
          trivy image --severity HIGH,CRITICAL myapp:scan

      - name: License compliance
        uses: fossas/fossa-action@v1
        with:
          api-key: ${{ secrets.FOSSA_API_KEY }}

      - name: Upload security reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            trivy-results.sarif
            safety-report.json
            bandit-report.json
```

### CLI Integration

#### GitHub CLI Commands

```bash
# List workflows
gh workflow list --repo owner/repo

# Trigger workflow with inputs
gh workflow run ci.yml \
  --ref main \
  --field environment=production \
  --field version=v1.2.3

# View workflow runs
gh run list --workflow=ci.yml --limit 10

# Watch live run
gh run watch 123456789

# View run details
gh run view 123456789 --log

# Re-run failed jobs
gh run rerun 123456789 --failed

# Download artifacts
gh run download 123456789 --name build-artifacts

# View workflow file
gh workflow view ci.yml --yaml

# Disable/Enable workflow
gh workflow disable ci.yml
gh workflow enable ci.yml
```

#### Local Testing with `act`

```bash
# Install act (Docker-based local runner)
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# List available actions
act -l

# Run default event (push)
act

# Run specific event
act pull_request

# Run specific job
act -j test

# Run with secrets
act -s GITHUB_TOKEN=ghp_xxx

# Run with custom workflow
act -W .github/workflows/ci.yml

# Dry run (show what would happen)
act -n

# Use specific platform
act --platform ubuntu-latest=catthehacker/ubuntu:act-latest
```

### Python API Integration

```python
"""
GitHub Actions API integration for workflow management
"""

import requests
from typing import Dict, List, Optional

class GitHubActionsClient:
    def __init__(self, token: str, repo_owner: str, repo_name: str):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def trigger_workflow(
        self,
        workflow_id: str,
        ref: str,
        inputs: Optional[Dict] = None
    ) -> Dict:
        """Trigger a workflow dispatch event"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/workflows/{workflow_id}/dispatches"
        payload = {
            "ref": ref,
            "inputs": inputs or {}
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return {"status": "triggered", "workflow": workflow_id, "ref": ref}

    def get_workflow_runs(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Get workflow runs with optional filtering"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs"
        params = {"per_page": limit}

        if workflow_id:
            params["workflow_id"] = workflow_id
        if status:
            params["status"] = status

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()["workflow_runs"]

    def get_run_status(self, run_id: int) -> Dict:
        """Get detailed status of a workflow run"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def download_artifacts(self, run_id: int, artifact_name: str, output_path: str) -> None:
        """Download artifacts from a workflow run"""
        # Get artifact ID
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/artifacts"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        artifacts = response.json()["artifacts"]
        artifact = next((a for a in artifacts if a["name"] == artifact_name), None)

        if not artifact:
            raise ValueError(f"Artifact '{artifact_name}' not found")

        # Download artifact
        download_url = artifact["archive_download_url"]
        response = requests.get(download_url, headers=self.headers)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(response.content)

    def rerun_failed_jobs(self, run_id: int) -> Dict:
        """Re-run only failed jobs in a workflow run"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/rerun-failed-jobs"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return {"status": "rerun_triggered", "run_id": run_id}

    def cancel_run(self, run_id: int) -> Dict:
        """Cancel a running workflow"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/cancel"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return {"status": "cancelled", "run_id": run_id}

# Usage example
if __name__ == "__main__":
    client = GitHubActionsClient(
        token="ghp_xxx",
        repo_owner="myorg",
        repo_name="myrepo"
    )

    # Trigger deployment workflow
    client.trigger_workflow(
        workflow_id="deploy.yml",
        ref="main",
        inputs={"environment": "production", "version": "v1.2.3"}
    )

    # Get recent runs
    runs = client.get_workflow_runs(status="completed", limit=5)
    for run in runs:
        print(f"{run['name']}: {run['conclusion']} ({run['created_at']})")
```

### Error Handling

**Common Error Scenarios**:

```yaml
# 1. Retry on failure
- name: Deploy with retry
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 5
    max_attempts: 3
    retry_on: error
    command: ./deploy.sh

# 2. Continue on error
- name: Optional step
  continue-on-error: true
  run: ./optional-task.sh

# 3. Conditional execution on failure
- name: Notify on failure
  if: failure()
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
      -d '{"text":"Pipeline failed!"}'

# 4. Always run cleanup
- name: Cleanup
  if: always()
  run: ./cleanup.sh

# 5. Timeout protection
- name: Long running task
  timeout-minutes: 30
  run: ./long-task.sh

# 6. Fallback on error
- name: Try primary method
  id: primary
  continue-on-error: true
  run: ./primary-deploy.sh

- name: Fallback method
  if: steps.primary.outcome == 'failure'
  run: ./fallback-deploy.sh
```

---

## **Part V: Implementation Plan**

### Prerequisites

**Required**:
- GitHub account with repository access
- GitHub Actions enabled (default for public repos)
- Repository with write permissions
- Basic YAML knowledge

**Optional**:
- Self-hosted runners (for private environments)
- Cloud provider accounts (AWS, Azure, GCP)
- Secret management tools (Vault, AWS Secrets Manager)
- Notification integrations (Slack, PagerDuty)

### Installation

#### Step 1: Create Workflow Directory
```bash
cd /path/to/repository
mkdir -p .github/workflows
```

#### Step 2: Create Basic CI Workflow
```bash
cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          echo "Running tests..."
          # Add your test commands here
EOF
```

#### Step 3: Commit and Push
```bash
git add .github/workflows/ci.yml
git commit -m "Add CI workflow"
git push origin main
```

#### Step 4: Verify Workflow
```bash
# View workflow in GitHub UI: Repository → Actions tab
# Or use CLI
gh workflow list
gh run list --workflow=ci.yml
```

### Configuration

#### Environment Setup

```yaml
# .github/workflows/production-deploy.yml
name: Production Deployment

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy'
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.example.com

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to production
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          VERSION: ${{ github.event.inputs.version }}
        run: |
          ./deploy.sh production $VERSION
```

**Configure Secrets**:
```bash
# Using GitHub CLI
gh secret set AWS_ACCESS_KEY_ID -b "AKIAXXXXX"
gh secret set AWS_SECRET_ACCESS_KEY -b "secret-value"

# Or via GitHub UI: Repository → Settings → Secrets and variables → Actions
```

**Environment Protection Rules**:
- Navigate to: Repository → Settings → Environments → New environment
- Configure:
  - Required reviewers (manual approval)
  - Wait timer (delay before deployment)
  - Deployment branches (restrict to specific branches)

#### Self-Hosted Runner Setup

```bash
# Download runner
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure runner
./config.sh --url https://github.com/owner/repo --token YOUR_TOKEN

# Run as service
sudo ./svc.sh install
sudo ./svc.sh start
```

### Testing

#### Local Testing with `act`

```bash
# Install act
brew install act  # macOS
# or curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Test push event
act push

# Test with specific workflow
act -W .github/workflows/ci.yml

# Test with secrets
echo "GITHUB_TOKEN=ghp_xxx" > .secrets
act --secret-file .secrets

# Dry run
act -n
```

#### Workflow Validation

```bash
# Validate YAML syntax
yamllint .github/workflows/*.yml

# Use actionlint for GitHub Actions-specific validation
brew install actionlint  # macOS
actionlint .github/workflows/*.yml

# Example actionlint output:
# .github/workflows/ci.yml:10:5: "runs-on" section is missing [syntax-check]
```

### Documentation

**Workflow README Example**:
```markdown
# CI/CD Workflows

## Available Workflows

### CI Pipeline (`ci.yml`)
- **Trigger**: Push to main/develop, Pull requests
- **Jobs**: Test, Lint, Build
- **Duration**: ~5 minutes

### Production Deployment (`deploy.yml`)
- **Trigger**: Manual (workflow_dispatch)
- **Jobs**: Deploy to production with approval
- **Duration**: ~10 minutes
- **Required Secrets**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

## Debugging Failed Workflows

1. View logs in GitHub Actions UI
2. Check job status: `gh run view RUN_ID --log`
3. Re-run failed jobs: `gh run rerun RUN_ID --failed`
4. Test locally with `act`

## Common Issues

### Issue: "Resource not accessible by integration"
**Solution**: Ensure workflow has correct permissions:
```yaml
permissions:
  contents: read
  pull-requests: write
```

### Issue: Timeout
**Solution**: Increase timeout or optimize workflow:
```yaml
timeout-minutes: 60
```
```

---

## **Part VI: Protocol Integrations**

### Key Protocol Integrations (10 of 26)

#### 1. P-TDD (Test-Driven Development)
**Integration Point**: Automated test execution in CI pipeline

**Workflow Example**:
```yaml
name: TDD Workflow
on: [push, pull_request]
jobs:
  tdd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run TDD cycle
        run: |
          pytest -v  # RED: Run tests (may fail)
          # GREEN: Implementation (in development)
          pytest -v  # Verify passing
          black . && pylint src/  # REFACTOR
```

#### 2. P-QGATE (Quality Gate)
**Integration Point**: Enforce quality standards before merge

**Workflow Example**:
```yaml
name: Quality Gate
on: pull_request
jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Quality checks
        run: |
          black --check .
          flake8 src/
          pylint src/ --fail-under=8.0
          pytest --cov=src --cov-fail-under=80
      - name: SonarQube scan
        uses: sonarsource/sonarqube-scan-action@v2
      - name: Block merge on failure
        if: failure()
        run: exit 1
```

#### 3. P-DEVSECOPS (Security Integration)
**Integration Point**: Automated security scanning

**Workflow Example**:
```yaml
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
      - name: Dependency check
        run: safety check
      - name: SAST scan
        run: bandit -r src/
```

#### 4. P-FEATURE-DEV (Feature Development)
**Integration Point**: Build and test new features

**Workflow Example**:
```yaml
name: Feature CI
on:
  push:
    branches: [feature/*]
jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build feature
        run: ./build.sh
      - name: Run feature tests
        run: pytest tests/features/
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
```

#### 5. P-DEPLOYMENT (Deployment Automation)
**Integration Point**: Multi-environment deployment

**Workflow Example**:
```yaml
name: Deploy
on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [dev, staging, production]
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: ./deploy.sh ${{ github.event.inputs.environment }}
```

#### 6. P-RECOVERY (Failure Recovery)
**Integration Point**: Automatic rollback on deployment failure

**Workflow Example**:
```yaml
name: Deploy with Rollback
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy
        id: deploy
        continue-on-error: true
        run: ./deploy.sh

      - name: Health check
        id: health
        if: steps.deploy.outcome == 'success'
        run: ./health-check.sh

      - name: Rollback on failure
        if: steps.deploy.outcome == 'failure' || steps.health.outcome == 'failure'
        run: ./rollback.sh
```

#### 7. P-BUG-FIX (Bug Fix Workflow)
**Integration Point**: Regression testing for bug fixes

**Workflow Example**:
```yaml
name: Bug Fix Validation
on:
  push:
    branches: [bugfix/*]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run regression tests
        run: pytest tests/regression/
      - name: Verify bug fix
        run: pytest tests/bugs/
```

#### 8. P-SEC-VULN (Vulnerability Management)
**Integration Point**: Continuous vulnerability scanning

**Workflow Example**:
```yaml
name: Vulnerability Scan
on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Dependency audit
        run: |
          pip install safety
          safety check --json > vuln-report.json
      - name: Create issue on critical vulns
        uses: actions/github-script@v7
        if: failure()
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Critical vulnerabilities detected',
              body: 'See vulnerability report in artifacts'
            });
```

#### 9. P-CODE-REVIEW (Automated Code Review)
**Integration Point**: Pre-review automated checks

**Workflow Example**:
```yaml
name: Automated Code Review
on: pull_request
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Code complexity check
        run: radon cc src/ --min B
      - name: Duplicate code detection
        run: pylint src/ --disable=all --enable=duplicate-code
      - name: Comment on PR
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: 'Automated review complete ✅'
            });
```

#### 10. P-RELEASE (Release Management)
**Integration Point**: Automated release creation and publishing

**Workflow Example**:
```yaml
name: Release
on:
  push:
    tags: ['v*']
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build release artifacts
        run: ./build-release.sh
      - name: Create GitHub release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
      - name: Publish to PyPI
        run: |
          pip install twine
          twine upload dist/*
```

### Complete Quality Gate Integration

**End-to-End Quality Gate Workflow**:
```yaml
name: Complete Quality Gate

on:
  pull_request:
    branches: [main, develop]

jobs:
  quality-gate:
    name: Quality Gate Validation
    runs-on: ubuntu-latest

    steps:
      # Checkout
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      # Setup
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install black isort flake8 pylint mypy bandit pytest pytest-cov safety

      # Code Quality Checks
      - name: Code formatting (Black)
        run: black --check .

      - name: Import sorting (isort)
        run: isort --check-only .

      - name: Linting (Flake8)
        run: flake8 src/ tests/ --max-line-length=88

      - name: Static analysis (Pylint)
        run: pylint src/ --fail-under=8.0

      - name: Type checking (mypy)
        run: mypy src/ --ignore-missing-imports

      # Security Checks
      - name: Security analysis (Bandit)
        run: bandit -r src/ -ll

      - name: Dependency vulnerabilities (Safety)
        run: safety check --json

      - name: Container scan (Trivy)
        if: hashFiles('Dockerfile') != ''
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'HIGH,CRITICAL'

      # Testing
      - name: Unit tests
        run: pytest tests/unit/ -v

      - name: Integration tests
        run: pytest tests/integration/ -v

      - name: Test coverage
        run: pytest --cov=src --cov-report=xml --cov-fail-under=80

      # Upload Results
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

      # Quality Gate Decision
      - name: Quality gate status
        if: success()
        run: echo "✅ Quality gate PASSED"

      - name: Post PR comment
        uses: actions/github-script@v7
        if: always()
        with:
          script: |
            const status = '${{ job.status }}';
            const conclusion = status === 'success' ? 'PASSED ✅' : 'FAILED ❌';
            const body = `## Quality Gate ${conclusion}\n\n` +
              `**Checks:** ${context.payload.pull_request.head.sha}\n` +
              `**Status:** ${status}\n\n` +
              `View details: ${context.payload.pull_request.html_url}/checks`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

---

## **Summary**

**Tool ID**: TOOL-CICD-001
**Primary Platform**: GitHub Actions
**Usage**: 26 of 83 protocols (31% - fourth highest priority)
**Core Capabilities**: Pipeline execution, test automation, deployment management, artifact handling, workflow orchestration

**Key Workflows Provided**:
1. Basic CI pipeline (build, test, lint)
2. Quality gate enforcement (P-QGATE)
3. TDD automation (P-TDD)
4. Security scanning (P-DEVSECOPS)
5. Multi-environment deployment (P-DEPLOYMENT)
6. Failure recovery (P-RECOVERY)
7. Release management (P-RELEASE)
8. Vulnerability management (P-SEC-VULN)

**Integration Points**: 10 key protocols with complete workflow examples
**Performance Targets**: <5min builds, <10min tests, 99.9% uptime
**Security**: OIDC, secret management, SLSA compliance, audit logging

---

**Document Control**:
- Version: 1.0.0
- Last Updated: 2025-11-19
- Status: Active
- Next Review: 2026-02-19
