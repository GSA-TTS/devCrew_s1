# GitHub Project Management Integration Client

Comprehensive GitHub integration client for project management operations using PyGithub (REST API v3) and GraphQL (API v4) for advanced features like GitHub Projects v2.

## Overview

The `GitHubPMClient` provides a unified interface for:
- **Issue Management**: Create, update, search, and close issues
- **GitHub Projects v2**: Modern project boards using GraphQL API
- **Pull Request Operations**: Create PRs and link them to issues
- **Label & Milestone Management**: Organize and track work
- **Webhook Configuration**: Automate workflows
- **GitHub Actions Integration**: Trigger and monitor workflows
- **Rate Limiting**: Built-in awareness and handling
- **GitHub Enterprise Support**: Works with both GitHub.com and Enterprise

## Features

### ✅ Issue Operations
- Create issues with labels, assignees, and milestones
- Update issue properties and metadata
- Add labels dynamically
- Close issues with comments
- Advanced search with filtering
- Bulk operations support

### ✅ GitHub Projects v2 (GraphQL)
- List organization projects
- Add issues to projects
- Update project item fields
- Modern project board automation
- Custom field support

### ✅ Pull Request Workflow
- Create pull requests
- Link PRs to issues automatically
- Support for draft PRs
- Automated closing keywords

### ✅ Repository Operations
- Label creation and management
- Milestone tracking
- Webhook configuration
- Repository information

### ✅ GitHub Actions
- Trigger workflows programmatically
- Monitor workflow runs
- Filter by status and branch
- Deployment automation

### ✅ Enterprise Features
- GitHub Enterprise Server support
- Custom base URLs
- Organization-level operations
- Rate limit monitoring

## Installation

### Requirements
```bash
pip install PyGithub>=2.0.0 requests>=2.31.0 pydantic>=2.0.0
```

### Dependencies
- `PyGithub`: GitHub REST API v3 client
- `requests`: GraphQL API calls
- `pydantic`: Data validation and settings

## Quick Start

### Basic Setup

```python
from github_client import GitHubPMClient

# Initialize client
client = GitHubPMClient(
    token="ghp_your_token_here",
    org="your-org",
    repo="your-repo"
)

# Create an issue
issue = client.create_issue(
    title="Bug: Application crashes on startup",
    body="Detailed description...",
    labels=["bug", "high-priority"],
    assignees=["developer1"]
)

print(f"Created issue #{issue.number}")
```

### GitHub Enterprise Setup

```python
client = GitHubPMClient(
    token="your_enterprise_token",
    org="enterprise-org",
    repo="enterprise-repo",
    base_url="https://github.enterprise.com/api/v3",
    graphql_url="https://github.enterprise.com/api/graphql"
)
```

## Usage Examples

### 1. Issue Management

#### Create and Update Issues

```python
# Create an issue with full metadata
issue = client.create_issue(
    title="Feature: Add user dashboard",
    body="""
## Description
Implement a user dashboard with analytics

## Requirements
- User profile display
- Activity history
- Settings panel

## Acceptance Criteria
- Dashboard loads in < 2s
- Mobile responsive
    """,
    labels=["enhancement", "frontend"],
    assignees=["frontend-dev"],
    milestone=1  # Milestone number
)

# Update the issue
client.update_issue(
    issue_number=issue.number,
    state=GitHubIssueState.OPEN,
    labels=["enhancement", "frontend", "in-progress"]
)

# Add more labels
client.add_issue_labels(
    issue_number=issue.number,
    labels=["needs-review"]
)

# Close with comment
client.close_issue(
    issue_number=issue.number,
    comment="Completed and merged in PR #123"
)
```

#### Search Issues

```python
from github_client import GitHubIssueState

# Search open bugs
bugs = client.search_issues(
    query="is:open",
    state=GitHubIssueState.OPEN,
    labels=["bug"],
    assignee="developer1"
)

# Search by text
results = client.search_issues(
    query="authentication timeout",
    state=GitHubIssueState.ALL
)

# Organization-wide search
org_issues = client.search_issues(
    query="is:open label:high-priority",
    org="my-org"  # Search across all repos
)
```

### 2. GitHub Projects v2 (GraphQL)

#### List and Manage Projects

```python
# Get organization projects
projects = client.get_organization_projects_v2(
    org="my-org",
    limit=20
)

for project in projects:
    print(f"{project['title']} - {project['url']}")

# Add issue to project
issue_node_id = client.get_issue_node_id(issue_number=42)
project_id = projects[0]["id"]

item = client.add_issue_to_project_v2(
    project_id=project_id,
    issue_id=issue_node_id
)

print(f"Added to project: {item['id']}")
```

#### Update Project Fields

```python
# Update a custom field on a project item
client.update_project_v2_item_field(
    project_id=project_id,
    item_id=item['id'],
    field_id=status_field_id,
    value="In Progress"
)
```

### 3. Pull Request Workflow

#### Create and Link PRs

```python
from github_client import GitHubPRState

# Create a pull request
pr = client.create_pull_request(
    title="Fix: Memory leak in worker process",
    head="fix/memory-leak",
    base="main",
    body="""
## Changes
- Fixed memory cleanup in worker shutdown
- Added proper event listener disposal

## Testing
- Ran 24-hour stability test
- Memory usage stable at < 100MB

Closes #42
    """,
    draft=False
)

# Link to an issue explicitly
client.link_pr_to_issue(
    pr_number=pr.number,
    issue_number=42
)
```

### 4. Label Management

#### Create Standard Labels

```python
# Create organizational standard labels
labels = [
    ("bug", "d73a4a", "Something isn't working"),
    ("enhancement", "a2eeef", "New feature or request"),
    ("documentation", "0075ca", "Documentation updates"),
    ("high-priority", "ff0000", "Urgent attention needed"),
    ("good-first-issue", "7057ff", "Good for newcomers"),
]

for name, color, description in labels:
    try:
        label = client.create_label(name, color, description)
        print(f"Created: {label.name}")
    except GitHubClientException as e:
        print(f"Skipped {name}: {e}")

# Get all labels
all_labels = client.get_labels()
for label in all_labels:
    print(f"{label.name}: {label.description}")
```

### 5. Milestone Management

```python
from datetime import datetime, timedelta

# Create a milestone
milestone = client.create_milestone(
    title="Q1 2025 Release",
    description="Major features for Q1",
    due_on=datetime.now() + timedelta(days=90)
)

# Create issue with milestone
issue = client.create_issue(
    title="Implement feature X",
    body="Description...",
    milestone=milestone.number
)
```

### 6. Webhook Configuration

```python
from github_client import WebhookConfig, GitHubWebhookEvent

# Configure webhook
webhook_config = WebhookConfig(
    url="https://automation.example.com/webhook",
    events=[
        GitHubWebhookEvent.ISSUES,
        GitHubWebhookEvent.PULL_REQUEST,
        GitHubWebhookEvent.PROJECT_CARD
    ],
    secret="webhook_secret_key",
    active=True
)

webhook = client.create_webhook(webhook_config)
print(f"Webhook created: {webhook['id']}")
```

### 7. GitHub Actions Integration

```python
# Trigger a workflow
success = client.trigger_workflow(
    workflow_id="deploy.yml",
    ref="main",
    inputs={
        "environment": "production",
        "version": "v1.2.3"
    }
)

# Get workflow runs
runs = client.get_workflow_runs(
    workflow_id="deploy.yml",
    status="completed",
    branch="main"
)

for run in runs:
    print(f"{run['name']}: {run['conclusion']}")
    print(f"  URL: {run['html_url']}")
```

### 8. Rate Limit Handling

```python
# Check rate limit before bulk operations
remaining, limit, reset_time = client._check_rate_limit()
print(f"API calls remaining: {remaining}/{limit}")
print(f"Resets at: {reset_time}")

# Configure threshold
client = GitHubPMClient(
    token="token",
    rate_limit_threshold=100  # Warn when < 100 calls left
)
```

## Automation Examples

### Automated Issue Classification (P-ISSUE-TRIAGE)

```python
def classify_and_label_issues(client):
    """Automatically classify and label new issues."""

    # Get unlabeled issues
    issues = client.search_issues(
        query="is:open label:none",
        state=GitHubIssueState.OPEN
    )

    for issue in issues:
        labels = []
        title = issue.title.lower()
        body = (issue.body or "").lower()

        # Type classification
        if any(word in title for word in ["bug", "error", "crash"]):
            labels.append("bug")
        elif any(word in title for word in ["feature", "add"]):
            labels.append("enhancement")
        elif "doc" in title:
            labels.append("documentation")

        # Priority classification
        if any(word in body for word in ["critical", "urgent"]):
            labels.append("high-priority")
        elif any(word in body for word in ["minor", "nice to have"]):
            labels.append("low-priority")

        # Component classification
        if "auth" in body or "login" in body:
            labels.append("authentication")
        if "api" in body:
            labels.append("api")
        if "ui" in body or "frontend" in body:
            labels.append("frontend")

        # Apply labels
        if labels:
            client.add_issue_labels(issue.number, labels)
            print(f"Issue #{issue.number}: {', '.join(labels)}")
```

### Sprint Planning Automation

```python
def create_sprint_from_milestone(client, milestone_number):
    """Create project cards from milestone issues."""

    # Get milestone issues
    issues = client.search_issues(
        query=f"milestone:{milestone_number} is:open"
    )

    # Add to project
    for issue in issues:
        issue_node_id = client.get_issue_node_id(issue.number)

        try:
            client.add_issue_to_project_v2(
                project_id="PROJECT_ID",
                issue_id=issue_node_id
            )
            print(f"Added issue #{issue.number} to sprint")
        except Exception as e:
            print(f"Failed to add #{issue.number}: {e}")
```

### Release Management

```python
def prepare_release(client, version):
    """Prepare a release with issues and PRs."""

    # Create milestone
    milestone = client.create_milestone(
        title=f"Release {version}",
        description=f"Issues and PRs for {version}",
        due_on=datetime.now() + timedelta(weeks=2)
    )

    # Get PRs for release
    prs = client.search_issues(
        query=f'is:pr is:merged label:"ready-for-release"'
    )

    # Create release notes
    release_notes = f"# Release {version}\n\n"
    for pr in prs:
        release_notes += f"- {pr.title} (#{pr.number})\n"

    print(release_notes)
    return milestone, prs
```

## API Reference

### GitHubPMClient

#### Constructor
```python
GitHubPMClient(
    token: str,
    org: Optional[str] = None,
    repo: Optional[str] = None,
    base_url: str = "https://api.github.com",
    graphql_url: Optional[str] = None,
    rate_limit_threshold: int = 100
)
```

#### Issue Methods
- `create_issue()` - Create a new issue
- `update_issue()` - Update issue properties
- `close_issue()` - Close an issue
- `add_issue_labels()` - Add labels to issue
- `search_issues()` - Search with filters

#### Projects v2 Methods (GraphQL)
- `get_organization_projects_v2()` - List org projects
- `add_issue_to_project_v2()` - Add issue to project
- `update_project_v2_item_field()` - Update project field
- `get_issue_node_id()` - Get GraphQL node ID

#### Pull Request Methods
- `create_pull_request()` - Create a PR
- `link_pr_to_issue()` - Link PR to issue

#### Label & Milestone Methods
- `create_label()` - Create a label
- `get_labels()` - Get all labels
- `create_milestone()` - Create milestone

#### Webhook Methods
- `create_webhook()` - Configure webhook

#### GitHub Actions Methods
- `trigger_workflow()` - Trigger workflow
- `get_workflow_runs()` - Get workflow history

#### Utility Methods
- `get_repository_info()` - Get repo details
- `get_authenticated_user()` - Get user info
- `_check_rate_limit()` - Check API limits

## Configuration Models

### IssueConfig
```python
IssueConfig(
    title: str,
    body: Optional[str] = None,
    labels: List[str] = [],
    assignees: List[str] = [],
    milestone: Optional[int] = None,
    project_number: Optional[int] = None
)
```

### WebhookConfig
```python
WebhookConfig(
    url: str,
    events: List[GitHubWebhookEvent],
    secret: Optional[str] = None,
    active: bool = True,
    content_type: str = "json"
)
```

### ProjectV2Config
```python
ProjectV2Config(
    title: str,
    description: Optional[str] = None,
    owner_login: str,
    owner_type: str = "ORGANIZATION"
)
```

## Error Handling

### Exception Hierarchy
```
GitHubClientException (base)
├── RateLimitException
└── ProjectNotFoundException
```

### Example
```python
from github_client import (
    GitHubClientException,
    RateLimitException,
    ProjectNotFoundException
)

try:
    issue = client.create_issue(title="Test", body="Test issue")
except RateLimitException as e:
    print(f"Rate limited: {e}")
    # Wait until reset time
except ProjectNotFoundException as e:
    print(f"Project not found: {e}")
except GitHubClientException as e:
    print(f"GitHub error: {e}")
```

## Best Practices

### 1. Token Security
```python
import os

# Use environment variables
token = os.getenv("GITHUB_TOKEN")
client = GitHubPMClient(token=token)

# Never hardcode tokens
# ❌ client = GitHubPMClient(token="ghp_abc123...")  # Bad!
```

### 2. Rate Limit Management
```python
# Set appropriate threshold
client = GitHubPMClient(
    token=token,
    rate_limit_threshold=100  # Warn when low
)

# Check before bulk operations
remaining, limit, reset = client._check_rate_limit()
if remaining < 50:
    print("Waiting for rate limit reset...")
    time.sleep((reset - datetime.now()).total_seconds())
```

### 3. Error Handling
```python
try:
    # Attempt operation
    issue = client.create_issue(...)
except GitHubClientException as e:
    logger.error(f"Failed to create issue: {e}")
    # Implement retry logic or fallback
```

### 4. Batch Operations
```python
# Process in batches to avoid rate limits
issues = client.search_issues(query="is:open")

for i in range(0, len(issues), 10):
    batch = issues[i:i+10]
    for issue in batch:
        # Process issue
        pass
    time.sleep(1)  # Rate limiting pause
```

## Protocol Integration

### P-ISSUE-TRIAGE
Automated GitHub issue classification and labeling system.

```python
# Classify new issues automatically
unlabeled = client.search_issues(
    query="is:open label:none created:>2025-01-01"
)

for issue in unlabeled:
    labels = classify_issue(issue)  # Custom classifier
    client.add_issue_labels(issue.number, labels)
```

### P-FEATURE-DEV
Cross-platform feature tracking and release planning.

```python
# Track features across sprints
features = client.search_issues(
    query="label:enhancement milestone:v1.0"
)

# Add to project board
for feature in features:
    node_id = client.get_issue_node_id(feature.number)
    client.add_issue_to_project_v2(project_id, node_id)
```

## Performance Considerations

1. **Caching**: Repository objects are cached internally
2. **Rate Limits**: 5,000 requests/hour (authenticated)
3. **GraphQL**: More efficient for complex queries
4. **Pagination**: Use search for large result sets
5. **Webhooks**: Prefer webhooks over polling

## Troubleshooting

### Common Issues

#### Authentication Errors
```python
# Ensure token has correct scopes
# Required: repo, read:org, write:org, workflow
```

#### Rate Limiting
```python
# Check rate limit status
remaining, limit, reset = client._check_rate_limit()
print(f"Remaining: {remaining}, Resets: {reset}")
```

#### GraphQL Errors
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

See the main project README for contribution guidelines.

## License

See the main project LICENSE file.

## Support

- Documentation: This file
- Examples: `github_client_example.py`
- Issues: GitHub issue tracker
- Protocol Docs: See protocol documentation

## Version History

- **1.0.0** (2025-01-03)
  - Initial release
  - REST API v3 support via PyGithub
  - GraphQL API v4 support for Projects v2
  - Webhook and Actions integration
  - GitHub Enterprise support
  - Comprehensive error handling
  - Rate limit awareness

---

**Author**: devCrew_s1
**Protocol**: P-ISSUE-TRIAGE, P-FEATURE-DEV
**Version**: 1.0.0
