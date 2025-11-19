# **Tool Name**: GitHub Integration & Workflow Automation

**Tool ID**: `TOOL-COLLAB-001`
**Version**: 1.0.0
**Status**: Active
**Owner**: All Agents (Foundational Tool)
**Last Updated**: 2025-11-19

---

## **Part I: Tool Identity & Purpose**

### Tool Category
Collaboration / Version Control / Issue Management

### Tool Capability
Enables agents to interact with GitHub repositories for comprehensive workflow automation including issue management (create, read, update, label, close), pull request operations (create, review, merge, comment), GitHub Actions workflow triggering, release management, repository administration, code search, branch management, and team collaboration through comments, mentions, and project integration.

### Use Cases

**Use Case 1: Issue-Driven Development Workflow (GH-1 Protocol)**
- Automatically create issue branches from GitHub issues with standardized naming (`issue_{{number}}`)
- Read issue details via GitHub CLI to extract requirements and acceptance criteria
- Post implementation plans as issue comments with markdown formatting
- Update issue labels and status throughout development lifecycle
- Link commits and PRs to issues for complete traceability

**Use Case 2: Pull Request Management for Feature Development (P-FEATURE-DEV, P-TDD)**
- Create PRs from feature branches with auto-generated descriptions from commits
- Request reviews from designated code reviewers and architects
- Post automated code quality reports as PR comments (linting, security scans, test coverage)
- Manage merge strategies (squash, rebase, merge commit) based on branch protection rules
- Trigger CI/CD pipelines on PR creation and automatically merge on approval

**Use Case 3: Repository Maintenance Automation (GH-MAINTENANCE)**
- Identify and cleanup stale branches (inactive >30 days) via automated workflows
- Monitor repository health metrics (size, branch count, CI/CD performance)
- Manage dependency updates via Dependabot integration
- Cleanup merged branches and orphaned artifacts
- Generate repository maintenance reports with actionable recommendations

**Use Case 4: CI/CD Pipeline Integration via GitHub Actions**
- Trigger workflow_dispatch events for deployment pipelines with custom parameters
- Monitor workflow run status and retrieve logs for failed jobs
- Download build artifacts (test reports, coverage data, binaries) for validation
- Implement quality gates by blocking merges when CI checks fail
- Orchestrate multi-stage deployments with approval gates

**Use Case 5: Code Search and Security Analysis (P-SEC-VULN, P-DEVSECOPS)**
- Search codebase for security vulnerabilities (hardcoded secrets, SQL injection patterns)
- Identify deprecated API usage and technical debt markers
- Locate all usages of specific functions or libraries for impact analysis
- Generate security scan reports with file locations and remediation suggestions
- Track vulnerability remediation progress across issues and PRs

### Strategic Value

**Business Value**
- Accelerates development velocity by 40-60% through automated workflow orchestration
- Improves code quality with mandatory review processes and automated quality gates
- Ensures compliance with complete audit trails for all repository activities
- Reduces manual coordination overhead with structured issue-to-deployment workflows
- Enables rapid incident response with issue triage and hotfix branching automation

**Technical Value**
- Provides unified interface for all GitHub operations via CLI and REST API
- Supports event-driven automation through webhook integration
- Enables distributed team collaboration with asynchronous code review workflows
- Facilitates continuous integration with status check enforcement
- Maintains repository health through automated maintenance protocols

**Risk Mitigation**
- Prevents unauthorized deployments with branch protection rules and required reviews
- Detects security vulnerabilities early via automated scanning (Dependabot, CodeQL)
- Maintains disaster recovery capability with complete Git history and tagged releases
- Enforces coding standards through automated linting and quality gate protocols
- Provides rollback mechanisms via Git revert and release versioning

---

## **Part II: Functional Requirements**

### Core Capabilities

**1. Issue Management**
- **Requirement**: Create, read, update, close, and label issues with full metadata support including assignees, milestones, projects, and markdown-formatted descriptions; support issue templates and automated labeling based on content analysis
- **Acceptance Criteria**:
  - Creates issues with markdown formatting, code blocks, and file attachments
  - Assigns multiple assignees and labels atomically via single API call
  - Links related issues using keywords (closes #N, fixes #N, resolves #N)
  - Searches issues with filters (label:bug, assignee:@user, milestone:v1.0, state:open)
  - Automatically labels issues based on content patterns (bug keywords → bug label)
  - Posts comments with @mentions triggering notifications

**2. Pull Request Operations**
- **Requirement**: Create PRs from feature branches, request reviews from individuals and teams, manage review approval workflows, post inline code review comments with suggestions, merge with configurable strategies (merge commit, squash, rebase), and track review status
- **Acceptance Criteria**:
  - Creates PRs with auto-generated titles and descriptions from commit messages
  - Requests reviews from GitHub teams and individual users
  - Merges only when required status checks pass and approvals obtained
  - Posts inline comments on specific code lines with improvement suggestions
  - Supports draft PRs for work-in-progress features
  - Automatically closes linked issues on PR merge

**3. GitHub Actions Integration**
- **Requirement**: Trigger workflows via workflow_dispatch events with custom inputs, monitor workflow run status until completion, download build artifacts for validation, retrieve execution logs for debugging, and cancel long-running workflows
- **Acceptance Criteria**:
  - Triggers workflows with typed inputs (string, number, boolean, choice)
  - Polls workflow status with exponential backoff until success/failure
  - Downloads artifacts with automatic decompression (zip, tar.gz)
  - Retrieves job logs with error context highlighting
  - Cancels workflows exceeding timeout thresholds
  - Re-runs failed workflows with same parameters

**4. Release Management**
- **Requirement**: Create releases with semantic versioning (v1.2.3), upload release assets (binaries, documentation), generate automated changelogs from PR descriptions categorized by labels, manage pre-release and draft releases, and tag commits with release versions
- **Acceptance Criteria**:
  - Creates releases with Git tags following semver conventions
  - Generates changelogs categorized by PR labels (feature, bugfix, breaking-change)
  - Uploads multiple assets with SHA256 checksums for verification
  - Marks releases as draft (unpublished) or pre-release (beta, alpha)
  - Edits existing releases to update notes or assets
  - Deletes release assets without removing the release

**5. Code Search and Branch Management**
- **Requirement**: Search code across repositories with regex patterns, file type filters, and language constraints; create and manage branches with protection rules; retrieve file contents; and analyze repository structure
- **Acceptance Criteria**:
  - Searches codebase with regex patterns returning file paths and line numbers
  - Filters by language (Python, JavaScript, etc.) and file extensions
  - Returns code snippets with surrounding context (3 lines before/after)
  - Creates branches from specific commits or branch references
  - Applies branch protection rules (required reviews, status checks)
  - Lists all branches with last commit metadata

### Input/Output Specifications

**Input Requirements**
- **Input Format**: GitHub CLI commands (`gh` tool), REST API JSON payloads, Git commands for repository operations
- **Input Parameters**: Repository owner/name (string), issue/PR numbers (integer), commit SHAs (40-char hex), branch names (string), labels (array), workflow IDs (integer), file paths (string)
- **Input Constraints**: API rate limits (5,000 requests/hour authenticated), issue/PR titles ≤256 characters, descriptions ≤65,536 characters, file uploads ≤100 MB

**Output Requirements**
- **Output Format**: JSON (API responses), markdown (issue/PR bodies), plain text (logs, file contents), YAML (workflow files), binary (artifacts)
- **Output Schema**: Issue objects with {id, number, title, state, labels[], assignees[], milestone}, PR objects with {number, state, review_decision, mergeable}, workflow run objects with {id, status, conclusion, logs_url}
- **Output Artifacts**: Downloaded artifacts (zip, tar.gz), generated changelogs (markdown), issue exports (JSON, CSV), code search reports (JSON)

### Performance Requirements

**Throughput**
- 100 API requests per minute with rate limit management and automatic retry
- 50 concurrent PR reviews without performance degradation
- 1,000 issue searches per hour with caching optimization

**Latency**
- API response within 1 second (P95) for GET operations
- Webhook processing within 3 seconds for event handling
- Code search results within 15 seconds for repositories <100k files

**Scalability**
- Support 5,000+ issues per repository with pagination
- Handle 500+ open PRs with review tracking
- Manage 100+ concurrent workflow runs across multiple repositories

**Reliability**
- 99.95% API uptime (GitHub SLA for Enterprise Cloud)
- Automatic retry with exponential backoff for transient errors (5xx)
- Circuit breaker pattern for API failures (open after 5 consecutive failures)

### Integration Requirements

**API Integration**
- REST API v3 (stable, feature-complete) for CRUD operations
- GraphQL API v4 (advanced queries, batch operations) for complex data fetching
- GitHub CLI (`gh`) for command-line automation and scripting
- Git protocol for repository cloning, pushing, and pulling

**Authentication**
- Personal Access Tokens (PAT) with fine-grained permissions (repo, workflow, admin:org)
- GitHub Apps with installation tokens for automated workflows
- OAuth 2.0 flow for user authorization in web applications
- SSH keys for Git operations with SSH agent forwarding

**Data Exchange**
- JSON for API request/response bodies
- Git protocol for repository data transfer
- Webhooks for event notifications (push, pull_request, issues, release)
- HTTPS/TLS 1.3 for secure communication

**Event Handling**
- Webhook signatures validated with HMAC-SHA256
- Event types: push, pull_request, issues, release, workflow_run, check_suite
- Webhook retry on delivery failure (exponential backoff, max 3 attempts)
- Webhook payload size limit: 5 MB

---

## **Part III: Non-Functional Requirements**

### Security Requirements

**Authentication & Authorization**
- Personal Access Tokens with scoped permissions (repo, workflow, read:org, admin:repo_hook)
- Token rotation every 90 days for compliance with security policies
- GitHub Apps with fine-grained repository permissions (read, write, admin)
- OAuth 2.0 authorization with PKCE for web flows
- SSO enforcement for enterprise organizations with SAML/OIDC integration

**Data Encryption**
- TLS 1.3 for all API communication with certificate pinning
- SSH encryption (RSA 4096, Ed25519) for Git operations
- Webhook payload signature validation with shared secrets
- At-rest encryption for repository data (AES-256)

**Secret Management**
- NEVER log or expose tokens in code, logs, or error messages
- Store tokens in secret vaults (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault)
- Use GitHub Secrets for workflow environment variables
- Enable secret scanning (Dependabot, Gitleaks, TruffleHog) for automated detection
- Revoke compromised tokens immediately via API

**Audit Logging**
- GitHub Enterprise audit log for all API calls, authentications, and admin actions
- Security event logs for suspicious activities (unusual access patterns, privilege escalation)
- Compliance exports (JSON, CSV) for SOC 2, GDPR, HIPAA audits
- Webhook delivery logs with response codes and retry attempts

**Compliance**
- SOC 2 Type II certified (GitHub Enterprise Cloud)
- GDPR compliant with data residency options (EU, US, Australia)
- FedRAMP Moderate authorized (GitHub Enterprise Server for US government)
- HIPAA compliant configurations available for healthcare applications

### Operational Requirements

**Deployment Models**
- GitHub.com (SaaS) - Managed cloud service with 99.95% uptime SLA
- GitHub Enterprise Server (self-hosted) - On-premises deployment with full control
- GitHub Enterprise Cloud (managed SaaS) - Enterprise features with dedicated support
- GitHub AE (Azure-hosted) - Fully managed service in Azure cloud

**Platform Support**
- GitHub CLI (`gh`) for Linux (x64, ARM64), macOS (Intel, Apple Silicon), Windows (x64, ARM64)
- REST/GraphQL API accessible from any platform with HTTP client
- Git client required for repository operations (version 2.30+)
- Python PyGithub library for programmatic integration

**Resource Requirements**
- Minimal client-side resources (GitHub CLI <50 MB, PyGithub <5 MB)
- Network bandwidth: 1-10 Mbps for typical operations, 100+ Mbps for large repository cloning
- Disk space: Repository clone size + 2x for Git objects and working directory
- Memory: 512 MB minimum, 2 GB recommended for large repository operations

**Backup & Recovery**
- Repository data replicated across 3+ availability zones
- GitHub Enterprise Server supports backup utilities (GitHub Enterprise Backup Utilities)
- Disaster recovery with RTO <4 hours, RPO <1 hour
- Point-in-time recovery via Git reflog (local), GitHub API (remote)

### Observability Requirements

**Logging**
- API request/response logs with correlation IDs (X-GitHub-Request-Id)
- Rate limit headers tracked (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- Webhook delivery logs with timestamps and response codes
- GitHub Actions logs with job execution details and artifact metadata
- Error logs with stack traces for debugging (never log tokens)

**Metrics**
- API rate limit consumption percentage (alert at >80%)
- Webhook delivery success rate (alert if <95%)
- Workflow run duration and success rate
- Issue/PR velocity metrics (created, closed, merged per day)
- Repository health score (based on stale branches, open issues, PR age)

**Tracing**
- Distributed tracing for multi-API call operations (create PR → trigger workflow → post comment)
- Correlation IDs linking related API calls in sequence
- Workflow run tracing from trigger to completion
- Issue lifecycle tracing (creation → assignment → closure)

**Alerting**
- Rate limit warnings when >80% consumed (15-minute window)
- Webhook delivery failures when >5% error rate (1-hour window)
- Workflow failures with error context and logs URL
- Security alerts (Dependabot, CodeQL findings) with severity levels
- Repository health degradation (excessive stale branches, large file commits)

### Governance Requirements

**Licensing**
- GitHub Free: Public repositories unlimited, private repositories with limited features
- GitHub Pro ($4/user/month): Advanced code review, protected branches, 3,000 Actions minutes
- GitHub Team ($4/user/month): Team access controls, draft PRs, 3,000 Actions minutes
- GitHub Enterprise ($21/user/month): SAML SSO, audit logs, 50,000 Actions minutes, advanced security

**Vendor Lock-in Mitigation**
- Git repository data portable via standard Git protocol
- Issues/PRs exportable to JSON/CSV via API
- GitHub Actions workflows use YAML (portable to GitLab CI, Jenkins)
- Migration tools available for GitLab, Bitbucket, Azure DevOps

**Support**
- Community forums (GitHub Community) for free tier
- Standard support (24-hour response) for Team and Enterprise
- Premium support (1-hour response) for Enterprise Cloud with SLA
- GitHub Professional Services for migrations and custom integrations

**Deprecation Policy**
- 6-month notice for API deprecations with migration guides
- 12-month support window for deprecated endpoints
- Sunset headers (Sunset, Deprecation) in API responses
- Breaking changes versioned (API v3 → v4) with parallel support

---

## **Part IV: Integration Patterns**

### CLI Commands (GitHub CLI - `gh`)

**Installation**
```bash
# macOS via Homebrew
brew install gh

# Linux via package manager
sudo apt install gh        # Debian/Ubuntu
sudo dnf install gh        # Fedora
sudo yum install gh        # CentOS/RHEL

# Windows via Scoop
scoop install gh

# Verify installation
gh --version
```

**Authentication**
```bash
# Interactive login (browser-based OAuth)
gh auth login

# Login with token (CI/CD environments)
gh auth login --with-token < token.txt
echo $GH_TOKEN | gh auth login --with-token

# Check authentication status
gh auth status

# Logout
gh auth logout
```

**Issue Operations**
```bash
# Create issue
gh issue create --title "Bug: Login fails" --body "Description here" --label bug,priority:high --assignee @user

# List issues
gh issue list --state open --label bug --limit 50
gh issue list --assignee @me --json number,title,labels

# View issue details
gh issue view 123 --json title,body,labels,assignees,state

# Comment on issue
gh issue comment 123 --body "Implementation plan created: docs/development/issue_123/issue_123_plan.md"

# Close issue
gh issue close 123 --comment "Fixed in PR #456"

# Reopen issue
gh issue reopen 123

# Edit issue
gh issue edit 123 --add-label verified --remove-label needs-triage
```

**Pull Request Operations**
```bash
# Create PR
gh pr create --title "Feature: Add user authentication" --body "Implements OAuth 2.0 login" --base main --head feature/auth --reviewer @user1,@user2

# Create draft PR
gh pr create --title "WIP: Refactor API" --draft

# List PRs
gh pr list --state open --label needs-review
gh pr list --author @me --json number,title,reviewDecision

# View PR details
gh pr view 456 --json title,body,reviews,checks

# Checkout PR locally
gh pr checkout 456

# Review PR
gh pr review 456 --approve --body "LGTM! Code quality looks good."
gh pr review 456 --request-changes --body "Please fix linting errors."
gh pr review 456 --comment --body "Question about error handling."

# Merge PR
gh pr merge 456 --squash --delete-branch
gh pr merge 456 --merge --auto   # Auto-merge when checks pass
gh pr merge 456 --rebase

# Close PR without merging
gh pr close 456 --comment "Superseded by PR #789"

# Comment on PR
gh pr comment 456 --body "Test coverage report: 95% (↑3%)"
```

**Repository Operations**
```bash
# Clone repository
gh repo clone owner/repo

# Create repository
gh repo create my-new-repo --public --description "Project description"

# View repository details
gh repo view owner/repo --json name,description,stargazerCount

# Fork repository
gh repo fork owner/repo --clone

# Archive repository
gh repo archive owner/repo
```

**Workflow Operations**
```bash
# List workflows
gh workflow list

# View workflow details
gh workflow view deploy.yml

# Trigger workflow (workflow_dispatch)
gh workflow run deploy.yml --ref main --field environment=production --field version=v1.2.3

# List workflow runs
gh run list --workflow=deploy.yml --limit 10 --json status,conclusion,createdAt

# View run details
gh run view 987654321 --log --log-failed

# Download artifacts
gh run download 987654321 --name test-results

# Re-run workflow
gh run rerun 987654321

# Cancel workflow run
gh run cancel 987654321
```

**Release Operations**
```bash
# Create release
gh release create v1.2.3 --title "Release v1.2.3" --notes "Changelog here" dist/*.tar.gz dist/*.zip

# Create pre-release
gh release create v2.0.0-beta.1 --prerelease --notes "Beta release"

# List releases
gh release list --limit 10

# View release details
gh release view v1.2.3

# Download release assets
gh release download v1.2.3 --pattern '*.tar.gz'

# Delete release
gh release delete v1.2.3 --yes
```

**Code Search**
```bash
# Search code in repository
gh search code "function authenticate" --repo owner/repo --language python

# Search issues
gh search issues "is:open label:bug" --repo owner/repo --json number,title

# Search PRs
gh search prs "is:merged author:@user" --repo owner/repo --limit 50
```

### Python API (PyGithub)

**Installation and Setup**
```python
# Install PyGithub
pip install PyGithub

# Basic setup
from github import Github, Auth

# Authenticate with token
auth = Auth.Token("ghp_YourPersonalAccessToken")
g = Github(auth=auth)

# Get repository
repo = g.get_repo("owner/repo")
```

**Issue Operations**
```python
# Create issue
issue = repo.create_issue(
    title="Bug: Login fails on mobile",
    body="## Description\nLogin button unresponsive on iOS Safari.\n\n## Steps to Reproduce\n1. Navigate to /login\n2. Tap login button\n3. No response",
    labels=["bug", "mobile", "priority:high"],
    assignees=["username"]
)
print(f"Created issue #{issue.number}")

# Get issue
issue = repo.get_issue(number=123)
print(f"Issue: {issue.title} (State: {issue.state})")

# Comment on issue
issue.create_comment("Implementation plan created: `docs/development/issue_123/issue_123_plan.md`")

# Update issue labels
issue.add_to_labels("verified", "ready-for-review")
issue.remove_from_labels("needs-triage")

# Close issue
issue.edit(state="closed")
issue.create_comment("Fixed in PR #456")

# Search issues
issues = repo.get_issues(state="open", labels=["bug"], assignee="username")
for issue in issues:
    print(f"#{issue.number}: {issue.title}")
```

**Pull Request Operations**
```python
# Create PR
pr = repo.create_pull(
    title="Feature: Add user authentication",
    body="## Summary\nImplements OAuth 2.0 login with Google and GitHub providers.\n\n## Changes\n- Added OAuth client configuration\n- Implemented JWT token generation\n- Added user session management",
    base="main",
    head="feature/auth",
    draft=False
)
print(f"Created PR #{pr.number}")

# Request reviewers
pr.create_review_request(reviewers=["user1", "user2"])

# Get PR
pr = repo.get_pull(number=456)
print(f"PR: {pr.title} (State: {pr.state}, Mergeable: {pr.mergeable})")

# Comment on PR
pr.create_issue_comment("Test coverage report: 95% (↑3%)")

# Review PR
pr.create_review(
    body="LGTM! Code quality looks good.",
    event="APPROVE"  # Options: APPROVE, REQUEST_CHANGES, COMMENT
)

# Merge PR
pr.merge(
    merge_method="squash",  # Options: merge, squash, rebase
    commit_title=f"feat: {pr.title} (#{pr.number})",
    commit_message=pr.body
)
pr.delete_branch()  # Delete head branch after merge

# Get review status
reviews = pr.get_reviews()
for review in reviews:
    print(f"{review.user.login}: {review.state} - {review.body}")
```

**Workflow Operations**
```python
# Get workflows
workflows = repo.get_workflows()
for workflow in workflows:
    print(f"{workflow.name} (ID: {workflow.id}, State: {workflow.state})")

# Trigger workflow (workflow_dispatch)
workflow = repo.get_workflow("deploy.yml")
workflow.create_dispatch(
    ref="main",
    inputs={"environment": "production", "version": "v1.2.3"}
)

# Get workflow runs
runs = workflow.get_runs(status="completed")
for run in runs:
    print(f"Run {run.id}: {run.status} / {run.conclusion} (Created: {run.created_at})")

# Download artifacts
run = workflow.get_runs()[0]  # Latest run
artifacts = run.get_artifacts()
for artifact in artifacts:
    # Download artifact (returns ZIP bytes)
    url = artifact.archive_download_url
    # Use requests library to download
```

**Release Operations**
```python
# Create release
release = repo.create_git_release(
    tag="v1.2.3",
    name="Release v1.2.3",
    message="## Changelog\n\n### Features\n- User authentication\n- API rate limiting\n\n### Bug Fixes\n- Fixed login timeout issue",
    draft=False,
    prerelease=False
)

# Upload asset
with open("dist/app-v1.2.3.tar.gz", "rb") as f:
    release.upload_asset(
        path="dist/app-v1.2.3.tar.gz",
        label="Application Binary (Linux x64)",
        content_type="application/gzip"
    )

# Get releases
releases = repo.get_releases()
for release in releases:
    print(f"{release.tag_name}: {release.title} (Published: {release.published_at})")

# Get specific release
release = repo.get_release("v1.2.3")
print(f"Release: {release.title}\n{release.body}")
```

**Code Search**
```python
# Search code
results = g.search_code("function authenticate", repo=repo, language="python")
for file in results:
    print(f"Found in: {file.path} ({file.repository.full_name})")

# Get file contents
contents = repo.get_contents("src/auth.py", ref="main")
print(contents.decoded_content.decode("utf-8"))
```

### Error Handling

**Common Error Patterns**
```python
from github import GithubException, RateLimitExceededException
import time

def gh_operation_with_retry(operation, max_retries=3):
    """Execute GitHub operation with automatic retry on rate limit."""
    for attempt in range(max_retries):
        try:
            return operation()
        except RateLimitExceededException as e:
            if attempt < max_retries - 1:
                reset_time = g.get_rate_limit().core.reset
                sleep_time = (reset_time - datetime.now()).total_seconds() + 10
                print(f"Rate limit exceeded. Sleeping for {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                raise
        except GithubException as e:
            if e.status in [502, 503, 504] and attempt < max_retries - 1:
                # Retry on server errors
                sleep_time = 2 ** attempt  # Exponential backoff
                print(f"Server error {e.status}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                print(f"GitHub API error: {e.status} - {e.data}")
                raise

# Usage
issue = gh_operation_with_retry(lambda: repo.create_issue(title="Test", body="Body"))
```

**Rate Limit Handling**
```python
# Check rate limit before operations
rate_limit = g.get_rate_limit()
print(f"Core API: {rate_limit.core.remaining}/{rate_limit.core.limit}")
print(f"Search API: {rate_limit.search.remaining}/{rate_limit.search.limit}")

if rate_limit.core.remaining < 100:
    print(f"Rate limit low. Resets at: {rate_limit.core.reset}")
    # Wait or batch operations
```

---

## **Part V: Implementation Plan**

### Prerequisites

**Required Software**
- GitHub account with appropriate access permissions
- Personal Access Token (PAT) with required scopes
- GitHub CLI (`gh`) version 2.40+ installed
- Git client version 2.30+ installed
- Python 3.8+ (for PyGithub integration)

**Required Permissions**
- Repository access (read, write, or admin depending on operations)
- Workflow permissions (for GitHub Actions triggering)
- Organization membership (for team operations)

**Environment Setup**
- Network access to github.com (HTTPS 443, SSH 22)
- TLS/SSL certificates configured
- SSH keys configured for Git operations (optional)

### Installation Steps

**Step 1: Install GitHub CLI**
```bash
# macOS
brew install gh

# Linux (Debian/Ubuntu)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Verify installation
gh --version
```

**Step 2: Authenticate with GitHub**
```bash
# Interactive authentication (recommended)
gh auth login
# Select: GitHub.com → HTTPS → Authenticate with browser

# Or use token authentication
export GH_TOKEN="ghp_YourPersonalAccessToken"
echo $GH_TOKEN | gh auth login --with-token

# Verify authentication
gh auth status
```

**Step 3: Configure Git (if not already configured)**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Configure commit signing (optional)
git config --global user.signingkey YOUR_GPG_KEY_ID
git config --global commit.gpgsign true
```

**Step 4: Install PyGithub (for Python integration)**
```bash
# Using pip
pip install PyGithub

# Using requirements.txt
echo "PyGithub>=2.1.1" >> requirements.txt
pip install -r requirements.txt
```

### Configuration

**Personal Access Token Setup**
1. Navigate to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Configure token:
   - **Note**: `devCrew_s1 Automation Token`
   - **Expiration**: 90 days
   - **Scopes**:
     - `repo` (Full repository access)
     - `workflow` (GitHub Actions workflows)
     - `read:org` (Read organization data)
     - `admin:repo_hook` (Repository webhooks)
4. Click "Generate token" and copy immediately
5. Store token securely (never commit to repository)

**Environment Variables**
```bash
# Add to ~/.bashrc, ~/.zshrc, or ~/.profile
export GH_TOKEN="ghp_YourPersonalAccessToken"
export GITHUB_TOKEN="ghp_YourPersonalAccessToken"  # Alias for compatibility

# For Python scripts
export GITHUB_API_TOKEN="ghp_YourPersonalAccessToken"
```

**Repository Access Configuration**
```bash
# Clone repository with HTTPS
gh repo clone owner/repo

# Or with SSH (requires SSH key setup)
gh repo clone owner/repo -- --ssh

# Set default repository for gh commands
cd /path/to/repo
gh repo set-default owner/repo
```

### Testing

**Unit Tests (CLI Commands)**
```bash
# Test authentication
gh auth status

# Test issue operations
gh issue list --limit 1
gh issue view 1  # View issue #1

# Test PR operations
gh pr list --limit 1
gh pr view 1  # View PR #1 (if exists)

# Test workflow operations
gh workflow list
gh run list --limit 5

# Test search
gh search issues "is:open" --limit 5
```

**Integration Tests (Python)**
```python
#!/usr/bin/env python3
"""GitHub Integration Test Suite"""
import os
from github import Github, Auth

def test_github_integration():
    """Test GitHub API integration."""
    token = os.getenv("GH_TOKEN")
    assert token, "GH_TOKEN environment variable not set"

    # Authenticate
    auth = Auth.Token(token)
    g = Github(auth=auth)

    # Test API access
    user = g.get_user()
    print(f"Authenticated as: {user.login}")

    # Test repository access
    repo = g.get_repo("owner/repo")  # Replace with actual repo
    print(f"Repository: {repo.full_name} (Stars: {repo.stargazers_count})")

    # Test issue listing
    issues = repo.get_issues(state="open")
    print(f"Open issues: {issues.totalCount}")

    # Test rate limit
    rate_limit = g.get_rate_limit()
    print(f"API rate limit: {rate_limit.core.remaining}/{rate_limit.core.limit}")

    print("✅ All tests passed!")

if __name__ == "__main__":
    test_github_integration()
```

### Documentation

**Usage Examples**

*Example 1: GH-1 Protocol - Issue Branch Creation*
```bash
#!/bin/bash
# Create issue branch for GH-1 protocol

ISSUE_NUMBER=123
PARENT_BRANCH="main"
BRANCH_NAME="issue_${ISSUE_NUMBER}"

# Ensure clean state
git fetch origin
git checkout $PARENT_BRANCH
git pull origin $PARENT_BRANCH

# Create and push issue branch
git checkout -b $BRANCH_NAME
git push -u origin $BRANCH_NAME

# Read issue details
gh issue view $ISSUE_NUMBER --json title,body,labels

# Post comment on issue
gh issue comment $ISSUE_NUMBER --body "Branch \`$BRANCH_NAME\` created for implementation."

echo "✅ Issue branch created: $BRANCH_NAME"
```

*Example 2: P-FEATURE-DEV Protocol - PR Creation with Review*
```python
from github import Github, Auth
import os

def create_feature_pr(repo_name, feature_branch, title, body, reviewers):
    """Create PR for feature development with automated review requests."""
    auth = Auth.Token(os.getenv("GH_TOKEN"))
    g = Github(auth=auth)
    repo = g.get_repo(repo_name)

    # Create PR
    pr = repo.create_pull(
        title=title,
        body=body,
        base="main",
        head=feature_branch,
        draft=False
    )
    print(f"✅ Created PR #{pr.number}: {pr.title}")

    # Request reviewers
    pr.create_review_request(reviewers=reviewers)
    print(f"✅ Requested reviews from: {', '.join(reviewers)}")

    # Add labels
    pr.add_to_labels("feature", "needs-review")

    return pr

# Usage
pr = create_feature_pr(
    repo_name="owner/repo",
    feature_branch="feature/user-auth",
    title="Feature: Add user authentication",
    body="## Summary\nImplements OAuth 2.0 login.\n\n## Changes\n- Added OAuth client\n- Implemented JWT tokens",
    reviewers=["reviewer1", "reviewer2"]
)
```

**Troubleshooting**

*Issue: Authentication Failed*
```bash
# Check authentication status
gh auth status

# Re-authenticate
gh auth logout
gh auth login

# Verify token permissions
gh api user
```

*Issue: Rate Limit Exceeded*
```bash
# Check current rate limit
gh api rate_limit

# Wait for reset or use authenticated requests (higher limit)
```

*Issue: Permission Denied*
```bash
# Verify token scopes
gh auth status

# Generate new token with correct scopes
# Navigate to: Settings → Developer settings → Personal access tokens
```

---

## **Part VI: Protocol Integrations**

### Top 10 Protocol Integrations (by frequency)

**1. GH-1: GitHub Issue Triage Protocol**
- **Usage**: Issue-driven development workflow entry point
- **Integration Points**:
  - Create issue branches: `git checkout -b issue_{{number}}`
  - Read issue details: `gh issue view {{number}} --json title,body,labels`
  - Post implementation plans: `gh issue comment {{number}} --body "Plan: docs/development/issue_{{number}}/issue_{{number}}_plan.md"`
  - Update issue status: `gh issue edit {{number}} --add-label in-progress`
- **Example**: Automatically create branch and post plan for issue #123

**2. P-FEATURE-DEV: New Feature Development Lifecycle Protocol**
- **Usage**: End-to-end feature development from planning to deployment
- **Integration Points**:
  - Create feature branches from issues
  - Create PRs with automated descriptions
  - Trigger CI/CD pipelines on PR creation
  - Merge PRs on approval with branch cleanup
- **Example**: Create PR for feature branch, request reviews, merge on approval

**3. P-TDD: Test-Driven Development Protocol**
- **Usage**: Red-Green-Refactor cycle with automated quality gates
- **Integration Points**:
  - Post test coverage reports as PR comments
  - Block PR merge if tests fail (status checks)
  - Trigger test workflows on push
  - Update issue labels based on test results
- **Example**: Run tests on PR, post coverage report, block merge if <80% coverage

**4. GH-MAINTENANCE: GitHub Repository Maintenance Protocol**
- **Usage**: Automated repository health and cleanup
- **Integration Points**:
  - List stale branches: `gh api repos/{owner}/{repo}/branches --jq '.[] | select(.commit.commit.author.date < "2024-10-01") | .name'`
  - Delete merged branches: `gh pr list --state merged --json headRefName | jq -r '.[].headRefName' | xargs -n1 git push origin --delete`
  - Monitor workflow performance: `gh run list --limit 50 --json status,conclusion,duration`
  - Generate health reports with issue/PR metrics
- **Example**: Weekly cleanup of stale branches and performance analysis

**5. P-QGATE: Automated Quality Gate Protocol**
- **Usage**: Enforce quality standards before merging
- **Integration Points**:
  - Create required status checks on PRs
  - Post quality gate results as PR comments (linting, security, coverage)
  - Block merge if quality gates fail
  - Trigger quality validation workflows
- **Example**: Run linting, security scan, and tests; block merge if any fail

**6. P-DEVSECOPS: Integrated DevSecOps Pipeline Protocol**
- **Usage**: Security integration in CI/CD workflows
- **Integration Points**:
  - Trigger security scans via GitHub Actions
  - Create security issues from Dependabot alerts
  - Post security scan results as PR comments
  - Block deployment if critical vulnerabilities found
- **Example**: Run SAST, dependency scan, secret scan; create issues for findings

**7. P-CODE-REVIEW: Code Review Process Protocol**
- **Usage**: Structured code review workflow
- **Integration Points**:
  - Request reviews from designated reviewers
  - Post inline code review comments with suggestions
  - Track review approval status
  - Require approvals before merge (branch protection)
- **Example**: Request review from architect, post feedback, approve after fixes

**8. P-BUG-FIX: Bug Triage and Resolution Protocol**
- **Usage**: Bug tracking and resolution workflow
- **Integration Points**:
  - Create bug issues with severity labels
  - Create hotfix branches for critical bugs
  - Link PRs to bug issues with "Fixes #N"
  - Close bug issues automatically on PR merge
- **Example**: Create bug issue, create hotfix branch, create PR, merge and auto-close issue

**9. P-SEC-VULN: Automated Vulnerability Management Protocol**
- **Usage**: Security vulnerability tracking and remediation
- **Integration Points**:
  - Read Dependabot alerts via API
  - Create security issues for critical vulnerabilities
  - Track remediation progress with labels
  - Verify fixes with security scans
- **Example**: Read Dependabot alerts, create issues for CVSS >7.0, track remediation

**10. P-ROADMAP-SYNC: Roadmap Synchronization Protocol**
- **Usage**: Align development with product roadmap
- **Integration Points**:
  - Create milestone-based releases
  - Track feature completion via issue/PR metrics
  - Generate roadmap reports from GitHub Projects
  - Update roadmap status in issues/PRs
- **Example**: Create release milestones, assign issues, track progress, generate reports

### Example Workflow: Complete Feature Development

```bash
#!/bin/bash
# Complete feature development workflow integrating multiple protocols

ISSUE_NUMBER=123
FEATURE_NAME="user-authentication"
BRANCH_NAME="issue_${ISSUE_NUMBER}"

# Phase 1: GH-1 - Issue Triage
echo "📋 Phase 1: Issue Triage (GH-1)"
gh issue view $ISSUE_NUMBER
git checkout main
git pull origin main
git checkout -b $BRANCH_NAME
git push -u origin $BRANCH_NAME
gh issue comment $ISSUE_NUMBER --body "✅ Branch created: \`$BRANCH_NAME\`"

# Phase 2: P-TDD - Test-Driven Development
echo "🧪 Phase 2: TDD Implementation (P-TDD)"
# Write tests first (manual step)
# Implement feature (manual step)
pytest tests/ --cov=src --cov-report=html
gh issue comment $ISSUE_NUMBER --body "✅ Tests passing. Coverage: $(coverage report | tail -1 | awk '{print $4}')"

# Phase 3: P-CODE-REVIEW - Create PR and Request Review
echo "👀 Phase 3: Code Review (P-CODE-REVIEW)"
gh pr create \
  --title "Feature: Add $FEATURE_NAME" \
  --body "Fixes #${ISSUE_NUMBER}\n\n## Summary\nImplements user authentication with OAuth 2.0.\n\n## Changes\n- Added OAuth client\n- Implemented JWT tokens\n- Added user session management" \
  --base main \
  --reviewer architect,lead-dev

# Phase 4: P-QGATE - Quality Gates
echo "✅ Phase 4: Quality Gates (P-QGATE)"
gh workflow run quality-gate.yml --ref $BRANCH_NAME
sleep 10
gh run list --workflow=quality-gate.yml --branch=$BRANCH_NAME --limit 1 --json status,conclusion

# Phase 5: Merge PR (after approval)
echo "🚀 Phase 5: Merge and Deploy"
gh pr merge $ISSUE_NUMBER --squash --delete-branch
gh issue close $ISSUE_NUMBER --comment "✅ Deployed in release v1.2.3"

echo "✅ Feature development complete!"
```

---

## **Appendix: Quick Reference**

### Common Commands Cheat Sheet

```bash
# Issues
gh issue create --title "..." --body "..." --label bug,priority:high
gh issue list --state open --label bug
gh issue view 123
gh issue comment 123 --body "..."
gh issue close 123

# Pull Requests
gh pr create --title "..." --body "..." --base main --head feature/branch
gh pr list --state open
gh pr view 456
gh pr review 456 --approve
gh pr merge 456 --squash --delete-branch

# Workflows
gh workflow run deploy.yml --ref main
gh run list --workflow=deploy.yml
gh run view 987654321 --log
gh run download 987654321

# Releases
gh release create v1.2.3 --notes "..." dist/*
gh release list
gh release view v1.2.3

# Repository
gh repo clone owner/repo
gh repo view owner/repo
```

### Rate Limits

| Endpoint Type | Authenticated | Unauthenticated |
|---------------|--------------|-----------------|
| Core API | 5,000/hour | 60/hour |
| Search API | 30/minute | 10/minute |
| GraphQL API | 5,000 points/hour | N/A |

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | OK | Success |
| 201 | Created | Resource created |
| 204 | No Content | Success (no response body) |
| 401 | Unauthorized | Check authentication |
| 403 | Forbidden | Check permissions/rate limit |
| 404 | Not Found | Verify resource exists |
| 422 | Unprocessable Entity | Validation error |
| 500/502/503 | Server Error | Retry with backoff |

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-19
**Next Review**: 2026-02-19
