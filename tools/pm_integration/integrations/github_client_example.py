"""
GitHub PM Client Usage Examples.

Demonstrates comprehensive usage of GitHubPMClient for project management
operations including issue tracking, Projects v2, and GitHub Actions.

Author: devCrew_s1
Version: 1.0.0
"""

import os
from datetime import datetime, timedelta

from github_client import (
    GitHubClientException,
    GitHubIssueState,
    GitHubPMClient,
    GitHubWebhookEvent,
    IssueConfig,
    WebhookConfig,
)


def example_basic_issue_operations():
    """Example: Basic issue operations."""
    print("=== Basic Issue Operations ===\n")

    # Initialize client
    client = GitHubPMClient(
        token=os.getenv("GITHUB_TOKEN"),
        org="my-org",
        repo="my-repo",
    )

    # Create an issue
    issue = client.create_issue(
        title="Bug: Login page timeout",
        body="""
## Description
Users are experiencing timeout errors on the login page.

## Steps to Reproduce
1. Navigate to /login
2. Enter credentials
3. Click submit
4. Timeout after 30 seconds

## Expected Behavior
Login should complete within 5 seconds
        """,
        labels=["bug", "high-priority", "authentication"],
        assignees=["developer1", "qa-lead"],
    )

    print(f"Created issue #{issue.number}: {issue.title}")
    print(f"URL: {issue.html_url}\n")

    # Update the issue
    updated = client.update_issue(
        issue_number=issue.number,
        labels=["bug", "high-priority", "authentication", "in-progress"],
    )
    print(f"Updated issue #{updated.number} with new labels\n")

    # Add a comment (using PyGithub directly)
    issue.create_comment("Starting investigation...")

    # Search for related issues
    related = client.search_issues(
        query="timeout login",
        state=GitHubIssueState.OPEN,
        labels=["bug"],
    )
    print(f"Found {len(related)} related issues\n")


def example_label_management():
    """Example: Label and milestone management."""
    print("=== Label Management ===\n")

    client = GitHubPMClient(
        token=os.getenv("GITHUB_TOKEN"),
        org="my-org",
        repo="my-repo",
    )

    # Create standard labels
    labels = [
        ("bug", "d73a4a", "Something isn't working"),
        ("enhancement", "a2eeef", "New feature or request"),
        ("documentation", "0075ca", "Improvements or additions to docs"),
        ("high-priority", "ff0000", "Needs immediate attention"),
    ]

    for name, color, description in labels:
        try:
            label = client.create_label(name, color, description)
            print(f"Created label: {label.name}")
        except GitHubClientException as e:
            print(f"Label {name} already exists or error: {e}")

    # Create a milestone
    milestone = client.create_milestone(
        title="Q1 2025 Release",
        description="Features and fixes for Q1 2025",
        due_on=datetime.now() + timedelta(days=90),
    )
    print(f"\nCreated milestone: {milestone.title}")
    print(f"Due: {milestone.due_on}\n")


def example_projects_v2_integration():
    """Example: GitHub Projects v2 integration using GraphQL."""
    print("=== GitHub Projects v2 Integration ===\n")

    client = GitHubPMClient(
        token=os.getenv("GITHUB_TOKEN"),
        org="my-org",
        repo="my-repo",
    )

    # Get organization projects
    projects = client.get_organization_projects_v2(org="my-org", limit=10)

    print(f"Found {len(projects)} projects:")
    for project in projects:
        print(f"  - {project['title']} (#{project['number']})")
        print(f"    URL: {project['url']}")

    if projects:
        # Create an issue and add it to a project
        issue = client.create_issue(
            title="Implement user dashboard",
            body="Create a dashboard for user analytics",
            labels=["enhancement", "frontend"],
        )

        # Get the issue node ID for GraphQL
        issue_node_id = client.get_issue_node_id(issue.number)
        project_id = projects[0]["id"]

        # Add issue to project
        item = client.add_issue_to_project_v2(
            project_id=project_id,
            issue_id=issue_node_id,
        )

        print(f"\nAdded issue #{issue.number} to project")
        print(f"Project item ID: {item['id']}\n")


def example_pull_request_workflow():
    """Example: Pull request creation and linking."""
    print("=== Pull Request Workflow ===\n")

    client = GitHubPMClient(
        token=os.getenv("GITHUB_TOKEN"),
        org="my-org",
        repo="my-repo",
    )

    # Create an issue
    issue = client.create_issue(
        title="Fix: Memory leak in background worker",
        body="Background worker accumulates memory over time",
        labels=["bug", "performance"],
    )
    print(f"Created issue #{issue.number}")

    # Create a pull request that fixes the issue
    pr = client.create_pull_request(
        title=f"Fix memory leak in background worker (#{issue.number})",
        head="fix/memory-leak",
        base="main",
        body=f"""
## Changes
- Fixed memory leak by properly cleaning up event listeners
- Added resource disposal in worker shutdown

## Testing
- Ran worker for 24 hours without memory growth
- Added unit tests for cleanup logic

Fixes #{issue.number}
        """,
        draft=False,
    )

    print(f"Created PR #{pr.number}: {pr.title}")
    print(f"URL: {pr.html_url}")

    # Link PR to issue explicitly
    client.link_pr_to_issue(pr.number, issue.number)
    print(f"Linked PR #{pr.number} to issue #{issue.number}\n")


def example_webhook_setup():
    """Example: Configure webhooks for automation."""
    print("=== Webhook Configuration ===\n")

    client = GitHubPMClient(
        token=os.getenv("GITHUB_TOKEN"),
        org="my-org",
        repo="my-repo",
    )

    # Create a webhook for issue tracking
    webhook_config = WebhookConfig(
        url="https://automation.example.com/github/webhook",
        events=[
            GitHubWebhookEvent.ISSUES,
            GitHubWebhookEvent.PULL_REQUEST,
            GitHubWebhookEvent.PROJECT_CARD,
        ],
        secret=os.getenv("WEBHOOK_SECRET"),
        active=True,
        content_type="json",
    )

    webhook = client.create_webhook(webhook_config)
    print(f"Created webhook: {webhook['url']}")
    print(f"Events: {webhook['events']}")
    print(f"Active: {webhook['active']}\n")


def example_github_actions_integration():
    """Example: GitHub Actions workflow integration."""
    print("=== GitHub Actions Integration ===\n")

    client = GitHubPMClient(
        token=os.getenv("GITHUB_TOKEN"),
        org="my-org",
        repo="my-repo",
    )

    # Trigger a deployment workflow
    triggered = client.trigger_workflow(
        workflow_id="deploy.yml",
        ref="main",
        inputs={
            "environment": "staging",
            "version": "v1.2.3",
        },
    )

    if triggered:
        print("Deployment workflow triggered successfully")

    # Get recent workflow runs
    runs = client.get_workflow_runs(
        workflow_id="deploy.yml",
        status="completed",
        branch="main",
    )

    print(f"\nRecent workflow runs ({len(runs)}):")
    for run in runs[:5]:  # Show last 5
        print(f"  - {run['name']}")
        print(f"    Status: {run['status']}")
        print(f"    Conclusion: {run['conclusion']}")
        print(f"    Branch: {run['head_branch']}")
        print(f"    URL: {run['html_url']}\n")


def example_issue_classification_automation():
    """Example: Automated issue classification for P-ISSUE-TRIAGE."""
    print("=== Automated Issue Classification ===\n")

    client = GitHubPMClient(
        token=os.getenv("GITHUB_TOKEN"),
        org="my-org",
        repo="my-repo",
    )

    # Get all open unlabeled issues
    unlabeled_issues = client.search_issues(
        query="is:open label:none",
        state=GitHubIssueState.OPEN,
    )

    print(f"Found {len(unlabeled_issues)} unlabeled issues")

    for issue in unlabeled_issues:
        print(f"\nProcessing issue #{issue.number}: {issue.title}")

        # Simple classification based on title/body
        title_lower = issue.title.lower()
        body_lower = (issue.body or "").lower()

        labels_to_add = []

        # Classify by type
        if any(word in title_lower for word in ["bug", "error", "fail"]):
            labels_to_add.append("bug")
        elif any(word in title_lower for word in ["feature", "add", "implement"]):
            labels_to_add.append("enhancement")
        elif any(word in title_lower for word in ["doc", "readme", "guide"]):
            labels_to_add.append("documentation")

        # Classify by priority
        if any(word in body_lower for word in ["critical", "urgent", "blocking"]):
            labels_to_add.append("high-priority")
        elif any(word in body_lower for word in ["nice to have", "minor"]):
            labels_to_add.append("low-priority")

        # Classify by component
        if "auth" in body_lower or "login" in body_lower:
            labels_to_add.append("authentication")
        if "api" in body_lower:
            labels_to_add.append("api")
        if "ui" in body_lower or "frontend" in body_lower:
            labels_to_add.append("frontend")

        if labels_to_add:
            client.add_issue_labels(issue.number, labels_to_add)
            print(f"  Added labels: {', '.join(labels_to_add)}")
        else:
            print("  No labels assigned")


def example_enterprise_setup():
    """Example: GitHub Enterprise configuration."""
    print("=== GitHub Enterprise Setup ===\n")

    # Configure for GitHub Enterprise Server
    client = GitHubPMClient(
        token=os.getenv("GHE_TOKEN"),
        org="enterprise-org",
        repo="enterprise-repo",
        base_url="https://github.enterprise.com/api/v3",
        graphql_url="https://github.enterprise.com/api/graphql",
    )

    # Test authentication
    user = client.get_authenticated_user()
    print(f"Authenticated as: {user['login']}")
    print(f"Enterprise user: {user['name']}")

    # Get repository info
    repo_info = client.get_repository_info()
    print(f"\nRepository: {repo_info['full_name']}")
    print(f"URL: {repo_info['url']}")
    print(f"Open issues: {repo_info['open_issues']}\n")


def example_rate_limit_handling():
    """Example: Rate limit awareness and handling."""
    print("=== Rate Limit Handling ===\n")

    client = GitHubPMClient(
        token=os.getenv("GITHUB_TOKEN"),
        org="my-org",
        repo="my-repo",
        rate_limit_threshold=100,  # Warn when below 100 requests
    )

    try:
        # Check rate limit before bulk operations
        remaining, limit, reset_time = client._check_rate_limit()
        print(f"Rate limit: {remaining}/{limit}")
        print(f"Resets at: {reset_time}")

        # Perform operations
        issues = client.search_issues(
            query="is:open",
            state=GitHubIssueState.OPEN,
        )
        print(f"\nFound {len(issues)} open issues")

        # Check rate limit again
        remaining, limit, reset_time = client._check_rate_limit()
        print(f"After search: {remaining}/{limit} remaining\n")

    except GitHubClientException as e:
        print(f"Error: {e}")
        print("Rate limit may be exceeded. Wait until reset time.")


if __name__ == "__main__":
    print("GitHub PM Client Examples\n")
    print("=" * 60)

    # Run examples (uncomment as needed)
    example_basic_issue_operations()
    # example_label_management()
    # example_projects_v2_integration()
    # example_pull_request_workflow()
    # example_webhook_setup()
    # example_github_actions_integration()
    # example_issue_classification_automation()
    # example_enterprise_setup()
    # example_rate_limit_handling()

    print("=" * 60)
    print("\nExamples completed!")
