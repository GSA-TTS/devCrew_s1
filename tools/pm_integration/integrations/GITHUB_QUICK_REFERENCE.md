# GitHub PM Client - Quick Reference

## Installation
```bash
pip install PyGithub>=2.0.0 requests>=2.31.0 pydantic>=2.0.0
```

## Quick Start
```python
from github_client import GitHubPMClient

client = GitHubPMClient(token="ghp_...", org="my-org", repo="my-repo")
issue = client.create_issue(title="Bug", labels=["bug"])
```

## All Methods (27)

### Issue Operations
```python
create_issue(title, body, labels, assignees, milestone)
update_issue(issue_number, title, body, state, labels, assignees)
close_issue(issue_number, comment)
add_issue_labels(issue_number, labels)
search_issues(query, state, labels, assignee)
```

### Projects v2 (GraphQL)
```python
get_organization_projects_v2(org, limit)
add_issue_to_project_v2(project_id, issue_id)
update_project_v2_item_field(project_id, item_id, field_id, value)
get_issue_node_id(issue_number)
```

### Pull Requests
```python
create_pull_request(title, head, base, body, draft)
link_pr_to_issue(pr_number, issue_number)
```

### Labels & Milestones
```python
create_label(name, color, description)
get_labels()
create_milestone(title, description, due_on)
```

### Classic Projects
```python
get_project_columns(project_id)
add_issue_to_classic_project(project_id, column_id, issue)
```

### Webhooks
```python
create_webhook(config)
```

### GitHub Actions
```python
trigger_workflow(workflow_id, ref, inputs)
get_workflow_runs(workflow_id, status, branch)
```

### Utilities
```python
get_repository_info()
get_authenticated_user()
_check_rate_limit()
```

## Configuration Models

### IssueConfig
```python
IssueConfig(
    title="...",
    body="...",
    labels=["bug", "high-priority"],
    assignees=["user1"],
    milestone=1
)
```

### WebhookConfig
```python
WebhookConfig(
    url="https://...",
    events=[GitHubWebhookEvent.ISSUES, GitHubWebhookEvent.PULL_REQUEST],
    secret="...",
    active=True
)
```

## Enums

### States
- `GitHubIssueState`: OPEN, CLOSED, ALL
- `GitHubPRState`: OPEN, CLOSED, MERGED, ALL

### Events
- `GitHubWebhookEvent`: ISSUES, PULL_REQUEST, PUSH, RELEASE, WORKFLOW_RUN, PROJECT_CARD

## Exceptions
- `GitHubClientException` - Base exception
- `RateLimitException` - Rate limit exceeded
- `ProjectNotFoundException` - Project not found

## Common Patterns

### Create & Label Issue
```python
issue = client.create_issue(title="Bug", body="Description")
client.add_issue_labels(issue.number, ["bug", "high-priority"])
```

### Search & Update
```python
issues = client.search_issues(query="is:open", labels=["bug"])
for issue in issues:
    client.update_issue(issue.number, labels=["bug", "triaged"])
```

### Add to Project v2
```python
projects = client.get_organization_projects_v2(org="my-org")
node_id = client.get_issue_node_id(issue_number=42)
client.add_issue_to_project_v2(projects[0]["id"], node_id)
```

### Create PR & Link
```python
pr = client.create_pull_request(title="Fix", head="fix", base="main")
client.link_pr_to_issue(pr.number, issue.number)
```

### Trigger Workflow
```python
client.trigger_workflow(
    workflow_id="deploy.yml",
    ref="main",
    inputs={"env": "prod"}
)
```

## Rate Limits
- **Authenticated**: 5,000 requests/hour
- **Check**: `client._check_rate_limit()`
- **Threshold**: Configure in constructor

## GitHub Enterprise
```python
client = GitHubPMClient(
    token="...",
    base_url="https://github.enterprise.com/api/v3",
    graphql_url="https://github.enterprise.com/api/graphql"
)
```

## Files
- **Implementation**: `github_client.py` (1,292 lines)
- **Examples**: `github_client_example.py` (395 lines)
- **Documentation**: `GITHUB_CLIENT_README.md` (717 lines)
- **Summary**: `GITHUB_IMPLEMENTATION_SUMMARY.md`

---
**Version**: 1.0.0 | **Author**: devCrew_s1 | **Protocols**: P-ISSUE-TRIAGE, P-FEATURE-DEV
