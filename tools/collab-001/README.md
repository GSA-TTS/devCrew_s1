# TOOL-COLLAB-001: GitHub Integration & Workflow Automation

High-level Python API and CLI wrapper for GitHub integration supporting devCrew agent protocols (GH-1, P-TDD, P-FEATURE-DEV).

## Overview

This tool provides two interfaces for GitHub operations:
1. **CLI Wrapper** (`devgru_github_cli.py`) - Wraps GitHub CLI (`gh`) commands with retry logic and error handling
2. **Python API** (`devgru_github_api.py`) - High-level PyGithub-based API for protocol integration

## Features

- Issue management (create, read, update, close, label)
- Pull request operations (create, review, merge, comment)
- GitHub Actions workflow triggering and monitoring
- Automatic retry with exponential backoff
- Rate limit handling
- Structured JSON logging
- Type-safe API with full type hints
- 90%+ test coverage

## Installation

### Prerequisites

- Python 3.8 or higher
- GitHub CLI (`gh`) version 2.40+ installed
- GitHub Personal Access Token with appropriate permissions

### Install GitHub CLI

```bash
# macOS
brew install gh

# Linux (Debian/Ubuntu)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh

# Verify installation
gh --version
```

### Install Python Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install individual packages
pip install PyGithub>=2.1.0 PyYAML>=6.0 requests>=2.31.0
```

### Authentication

Set up GitHub authentication token:

```bash
# Set environment variable (recommended)
export GH_TOKEN="ghp_YourPersonalAccessToken"

# Or use GitHub CLI authentication
gh auth login
```

#### Creating a Personal Access Token

1. Navigate to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Configure token:
   - **Scopes**: `repo`, `workflow`, `read:org`, `admin:repo_hook`
   - **Expiration**: 90 days (recommended)
4. Copy token and store securely

## Usage

### CLI Wrapper Examples

```python
#!/usr/bin/env python3
from devgru_github_cli import (
    create_issue,
    read_issue,
    update_issue,
    close_issue,
    create_pr,
    merge_pr,
    trigger_workflow,
)

# Create an issue
issue = create_issue(
    title="Bug: Login fails on mobile",
    body="## Description\nLogin button unresponsive on iOS Safari.",
    labels=["bug", "priority:high"],
    assignees=["developer1"],
)
print(f"Created issue #{issue['number']}")

# Read issue details
issue_data = read_issue(123)
print(f"Issue state: {issue_data['state']}")

# Update issue labels
updated_issue = update_issue(
    issue_number=123,
    add_labels=["verified"],
    remove_labels=["needs-triage"],
)

# Close issue
closed_issue = close_issue(
    issue_number=123,
    comment="Fixed in PR #456",
)

# Create pull request
pr = create_pr(
    title="Feature: Add user authentication",
    body="Implements OAuth 2.0 login",
    base="main",
    head="feature/auth",
    reviewers=["reviewer1", "reviewer2"],
    labels=["feature", "needs-review"],
)
print(f"Created PR #{pr['number']}")

# Merge PR with squash
merged_pr = merge_pr(
    pr_number=456,
    merge_method="squash",
    delete_branch=True,
)

# Trigger workflow
workflow_result = trigger_workflow(
    workflow_name="deploy.yml",
    ref="main",
    inputs={"environment": "production", "version": "v1.2.3"},
)
```

### Python API Examples

```python
#!/usr/bin/env python3
from devgru_github_api import (
    get_github_client,
    IssueManager,
    PRManager,
    WorkflowManager,
)

# Initialize GitHub client
client = get_github_client()
repo = client.get_repo("owner/repo")

# Issue Management
issue_manager = IssueManager(repo)

# Create issue with retry on rate limit
issue = issue_manager.create_issue_with_retry(
    title="Feature: Add dark mode",
    body="Implement dark mode theme",
    labels=["enhancement", "ui"],
    assignees=["developer1"],
)

# Search issues
open_bugs = issue_manager.search_issues(
    state="open",
    labels=["bug"],
)

# Update labels
issue_manager.update_labels(
    issue_number=123,
    add_labels=["verified"],
    remove_labels=["needs-triage"],
)

# Add comment
issue_manager.add_comment(
    issue_number=123,
    comment="Implementation plan: docs/development/issue_123/plan.md",
)

# Close issue
issue_manager.close_issue(
    issue_number=123,
    comment="Completed in PR #456",
)

# Pull Request Management
pr_manager = PRManager(repo)

# Create PR
pr = pr_manager.create_pr(
    title="Feature: User authentication",
    body="## Summary\nImplements OAuth 2.0\n\n## Changes\n- OAuth client\n- JWT tokens",
    base="main",
    head="feature/auth",
    reviewers=["reviewer1"],
    labels=["feature"],
)

# Review PR
pr_manager.create_review(
    pr_number=456,
    body="LGTM! Code quality looks good.",
    event="APPROVE",
)

# Merge PR
pr_manager.merge_pr(
    pr_number=456,
    merge_method="squash",
    delete_branch=True,
)

# Workflow Management
workflow_manager = WorkflowManager(repo)

# Trigger workflow
workflow_manager.trigger_workflow(
    workflow_name="deploy.yml",
    ref="main",
    inputs={"environment": "production", "version": "v1.2.3"},
)

# Get workflow runs
runs = workflow_manager.get_workflow_runs(
    workflow_name="deploy.yml",
    status="completed",
    limit=10,
)

# Get artifacts
artifacts = workflow_manager.get_artifacts(run_id=123456)
```

## Protocol Integration Examples

### GH-1: GitHub Issue Triage Protocol

```python
#!/usr/bin/env python3
"""GH-1 Protocol: Issue-driven development workflow."""

import subprocess
from devgru_github_cli import read_issue, create_issue
from devgru_github_api import get_github_client, IssueManager

def gh1_protocol(issue_number: int, parent_branch: str = "main"):
    """Execute GH-1 protocol for issue triage."""
    # Step 1: Create issue branch
    branch_name = f"issue_{issue_number}"
    subprocess.run(["git", "checkout", parent_branch], check=True)
    subprocess.run(["git", "pull", "origin", parent_branch], check=True)
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)
    subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)

    # Step 2: Read issue details
    issue_data = read_issue(issue_number)
    print(f"Issue: {issue_data['title']}")
    print(f"Labels: {issue_data['labels']}")

    # Step 3: Post comment on issue
    client = get_github_client()
    repo = client.get_repo("owner/repo")
    issue_manager = IssueManager(repo)

    issue_manager.add_comment(
        issue_number=issue_number,
        comment=f"Branch `{branch_name}` created for implementation.",
    )

    # Step 4: Update issue label
    issue_manager.update_labels(
        issue_number=issue_number,
        add_labels=["in-progress"],
    )

    print(f"GH-1 protocol completed for issue #{issue_number}")

# Execute
gh1_protocol(issue_number=123, parent_branch="main")
```

### P-TDD: Test-Driven Development Protocol

```python
#!/usr/bin/env python3
"""P-TDD Protocol: Test coverage reporting on PR."""

import subprocess
from devgru_github_api import get_github_client, PRManager

def p_tdd_protocol(pr_number: int):
    """Post test coverage report on PR."""
    # Step 1: Run tests with coverage
    result = subprocess.run(
        ["pytest", "--cov=.", "--cov-report=term-missing"],
        capture_output=True,
        text=True,
    )

    # Step 2: Parse coverage percentage
    coverage_line = [line for line in result.stdout.split("\n") if "TOTAL" in line][0]
    coverage_pct = coverage_line.split()[-1]

    # Step 3: Post comment on PR
    client = get_github_client()
    repo = client.get_repo("owner/repo")
    pr_manager = PRManager(repo)

    comment = f"""## Test Coverage Report

**Coverage**: {coverage_pct}

```
{result.stdout}
```

{'✅ Coverage meets threshold (>80%)' if float(coverage_pct.rstrip('%')) > 80 else '❌ Coverage below threshold'}
"""

    pr_manager.add_comment(pr_number=pr_number, comment=comment)
    print(f"Posted coverage report on PR #{pr_number}")

# Execute
p_tdd_protocol(pr_number=456)
```

### P-FEATURE-DEV: Feature Development Lifecycle

```python
#!/usr/bin/env python3
"""P-FEATURE-DEV Protocol: Complete feature development workflow."""

import subprocess
from devgru_github_cli import create_pr, merge_pr
from devgru_github_api import get_github_client, IssueManager, PRManager

def p_feature_dev_protocol(issue_number: int, feature_branch: str):
    """Execute complete feature development workflow."""
    client = get_github_client()
    repo = client.get_repo("owner/repo")

    # Step 1: Create PR from feature branch
    pr = create_pr(
        title=f"Feature: Implement issue #{issue_number}",
        body=f"Fixes #{issue_number}\n\n## Summary\n[Description]\n\n## Changes\n- [Change 1]",
        base="main",
        head=feature_branch,
        reviewers=["tech-lead"],
        labels=["feature", "needs-review"],
    )
    pr_number = pr["number"]
    print(f"Created PR #{pr_number}")

    # Step 2: Wait for approval (manual step)
    input("Press Enter after PR is approved...")

    # Step 3: Run quality checks
    subprocess.run(["pytest", "--cov=.", "--cov-report=term"], check=True)
    subprocess.run(["black", "."], check=True)
    subprocess.run(["flake8", "."], check=True)

    # Step 4: Merge PR
    merged = merge_pr(
        pr_number=pr_number,
        merge_method="squash",
        delete_branch=True,
    )

    # Step 5: Close linked issue
    issue_manager = IssueManager(repo)
    issue_manager.close_issue(
        issue_number=issue_number,
        comment=f"Completed in PR #{pr_number}",
    )

    print(f"Feature development completed: Issue #{issue_number}, PR #{pr_number}")

# Execute
p_feature_dev_protocol(issue_number=123, feature_branch="feature/user-auth")
```

## Configuration

Edit `github_config.yml` to customize:

- Default labels and reviewers
- Branch protection rules
- Rate limiting policies
- Retry configuration
- Workflow settings
- Protocol-specific settings (GH-1, P-TDD, etc.)

See `github_config.yml` for full configuration options.

## Error Handling

All functions include comprehensive error handling:

```python
from devgru_github_cli import GHCLIError
from devgru_github_api import GitHubAPIError

try:
    issue = create_issue(title="Test", body="Body")
except GHCLIError as e:
    print(f"CLI error: {e}")

try:
    client = get_github_client()
except GitHubAPIError as e:
    print(f"API error: {e}")
```

### Retry Logic

Automatic retry with exponential backoff for:
- Transient server errors (502, 503, 504)
- Rate limit exceeded (waits for reset)
- Network timeouts

Default configuration: 3 retries with exponential backoff (1s, 2s, 4s).

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_github_cli.py -v

# Run integration tests (requires GH_TOKEN)
pytest tests/test_integration.py -v -m integration
```

### Test Coverage

Current coverage: 90%+

```bash
# Generate coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Code Quality

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Linting and Formatting

```bash
# Format code
black .
isort .

# Lint code
flake8 .
pylint devgru_github_cli.py devgru_github_api.py

# Type checking
mypy devgru_github_cli.py --ignore-missing-imports
mypy devgru_github_api.py --ignore-missing-imports

# Security scanning
bandit -r . -ll
```

## API Reference

### CLI Wrapper (`devgru_github_cli.py`)

#### Issue Operations
- `create_issue(title, body, labels, assignees, milestone)` - Create issue
- `read_issue(issue_number)` - Read issue details
- `update_issue(issue_number, ...)` - Update issue
- `close_issue(issue_number, comment)` - Close issue

#### PR Operations
- `create_pr(title, body, base, head, reviewers, labels, draft)` - Create PR
- `merge_pr(pr_number, merge_method, delete_branch)` - Merge PR

#### Workflow Operations
- `trigger_workflow(workflow_name, ref, inputs)` - Trigger workflow

#### Authentication
- `get_auth_token()` - Get GitHub token from environment

### Python API (`devgru_github_api.py`)

#### Client Initialization
- `get_github_client()` - Initialize GitHub client

#### IssueManager
- `create_issue(title, body, labels, assignees)` - Create issue
- `create_issue_with_retry(...)` - Create with retry logic
- `get_issue(issue_number)` - Get issue
- `update_labels(issue_number, add_labels, remove_labels)` - Update labels
- `add_comment(issue_number, comment)` - Add comment
- `close_issue(issue_number, comment)` - Close issue
- `search_issues(state, labels, assignee)` - Search issues

#### PRManager
- `create_pr(title, body, base, head, reviewers, labels, draft)` - Create PR
- `merge_pr(pr_number, merge_method, delete_branch)` - Merge PR
- `create_review(pr_number, body, event)` - Create review
- `get_reviews(pr_number)` - Get reviews
- `add_comment(pr_number, comment)` - Add comment

#### WorkflowManager
- `trigger_workflow(workflow_name, ref, inputs)` - Trigger workflow
- `get_workflow_runs(workflow_name, status, limit)` - Get runs
- `get_artifacts(run_id)` - Get artifacts
- `list_workflows()` - List workflows

#### Batch Operations
- `batch_create_issues(repo, issues_data)` - Batch create issues

## Security

- Never hardcode tokens in code
- Use environment variables for authentication
- Enable secret scanning in repository
- Rotate tokens every 90 days
- Use minimum required token permissions
- Sanitize logs to prevent token exposure

## Troubleshooting

### Authentication Failed

```bash
# Check token
echo $GH_TOKEN

# Re-authenticate
gh auth login

# Verify permissions
gh api user
```

### Rate Limit Exceeded

```bash
# Check rate limit
gh api rate_limit

# Wait for reset or use authenticated requests (higher limit)
```

### Command Timeout

Increase timeout in configuration or retry manually.

### JSON Parse Error

Check GitHub CLI version (`gh --version`) and update if needed.

## Contributing

1. Fork repository
2. Create feature branch
3. Write tests (TDD approach)
4. Implement feature
5. Run pre-commit checks
6. Submit pull request

## License

This tool is part of the devCrew project. See main repository for license information.

## Support

For issues and questions:
- Create GitHub issue with `tool:collab-001` label
- Include error logs and reproduction steps
- Reference protocol (GH-1, P-TDD, etc.) if applicable

## Version History

- **1.0.0** (2025-11-19) - Initial release
  - CLI wrapper with retry logic
  - PyGithub API with protocol integration
  - 90%+ test coverage
  - Comprehensive documentation
