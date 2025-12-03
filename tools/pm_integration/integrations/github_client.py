"""
GitHub Project Management Integration Client.

Comprehensive GitHub integration using PyGithub (REST API v3) and GraphQL
(API v4) for advanced Project Management operations including GitHub Projects
v2, issue management, PR linking, and repository operations.

Key Features:
    - Issue operations (create, update, label, assign, close)
    - GitHub Projects v2 integration via GraphQL API
    - Pull request linking and automation
    - Label and milestone management
    - Repository and organization operations
    - Webhook configuration
    - GitHub Actions integration
    - Rate limiting awareness
    - GitHub Enterprise support

Example:
    >>> client = GitHubPMClient(
    ...     token="ghp_token",
    ...     org="my-org",
    ...     repo="my-repo"
    ... )
    >>> issue = client.create_issue(
    ...     title="Bug: Login fails",
    ...     body="User cannot login...",
    ...     labels=["bug", "high-priority"]
    ... )
    >>> project_item = client.add_issue_to_project(
    ...     project_number=1,
    ...     issue_number=issue.number
    ... )

Author: devCrew_s1
Version: 1.0.0
Protocol: P-ISSUE-TRIAGE, P-FEATURE-DEV
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import requests
from github import Github, GithubException
from github.Issue import Issue
from github.Label import Label
from github.Milestone import Milestone
from github.ProjectCard import ProjectCard
from github.ProjectColumn import ProjectColumn
from github.PullRequest import PullRequest
from github.Repository import Repository
from pydantic import BaseModel, Field, field_validator

# Configure module logger
logger = logging.getLogger(__name__)


class GitHubIssueState(str, Enum):
    """GitHub issue states."""

    OPEN = "open"
    CLOSED = "closed"
    ALL = "all"


class GitHubPRState(str, Enum):
    """GitHub pull request states."""

    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    ALL = "all"


class GitHubProjectCardType(str, Enum):
    """GitHub project card content types."""

    ISSUE = "Issue"
    PULL_REQUEST = "PullRequest"
    NOTE = "Note"


class GitHubWebhookEvent(str, Enum):
    """GitHub webhook event types."""

    ISSUES = "issues"
    PULL_REQUEST = "pull_request"
    PUSH = "push"
    RELEASE = "release"
    WORKFLOW_RUN = "workflow_run"
    PROJECT_CARD = "project_card"


class GitHubClientException(Exception):
    """Base exception for GitHub client errors."""

    pass


class RateLimitException(GitHubClientException):
    """Raised when rate limit is exceeded."""

    pass


class ProjectNotFoundException(GitHubClientException):
    """Raised when project is not found."""

    pass


class IssueConfig(BaseModel):
    """Configuration for creating GitHub issues."""

    title: str = Field(..., min_length=1, max_length=256)
    body: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)
    milestone: Optional[int] = None
    project_number: Optional[int] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate issue title."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class ProjectV2Config(BaseModel):
    """Configuration for GitHub Projects v2."""

    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    owner_login: str = Field(..., min_length=1)
    owner_type: str = Field(default="ORGANIZATION")  # ORGANIZATION or USER

    @field_validator("owner_type")
    @classmethod
    def validate_owner_type(cls, v: str) -> str:
        """Validate owner type."""
        if v not in ["ORGANIZATION", "USER"]:
            raise ValueError("owner_type must be ORGANIZATION or USER")
        return v


class WebhookConfig(BaseModel):
    """Configuration for GitHub webhooks."""

    url: str = Field(..., pattern=r"^https?://.*")
    events: List[GitHubWebhookEvent]
    secret: Optional[str] = None
    active: bool = True
    content_type: str = "json"

    @field_validator("events")
    @classmethod
    def validate_events(
        cls, v: List[GitHubWebhookEvent]
    ) -> List[GitHubWebhookEvent]:
        """Validate webhook events."""
        if not v:
            raise ValueError("At least one event must be specified")
        return v


class GitHubPMClient:
    """
    GitHub Project Management Client.

    Provides comprehensive GitHub integration for project management operations
    using PyGithub for REST API and GraphQL for advanced features like
    Projects v2.

    Attributes:
        token: GitHub personal access token
        base_url: GitHub API base URL (for Enterprise)
        org: Default organization name
        repo: Default repository name
        client: PyGithub client instance
        graphql_url: GraphQL API endpoint
        rate_limit_threshold: Minimum remaining requests before warning
    """

    def __init__(
        self,
        token: str,
        org: Optional[str] = None,
        repo: Optional[str] = None,
        base_url: str = "https://api.github.com",
        graphql_url: Optional[str] = None,
        rate_limit_threshold: int = 100,
    ):
        """
        Initialize GitHub PM client.

        Args:
            token: GitHub personal access token
            org: Default organization name
            repo: Default repository name
            base_url: GitHub API base URL (for Enterprise)
            graphql_url: GraphQL API endpoint (defaults to base_url/graphql)
            rate_limit_threshold: Minimum remaining requests before warning

        Raises:
            GitHubClientException: If authentication fails
        """
        self.token = token
        self.base_url = base_url
        self.org = org
        self.repo = repo
        self.rate_limit_threshold = rate_limit_threshold

        # Initialize PyGithub client
        try:
            if base_url == "https://api.github.com":
                self.client = Github(token)
            else:
                # GitHub Enterprise
                self.client = Github(base_url=base_url, login_or_token=token)

            # Test authentication
            self.client.get_user().login
            logger.info("Successfully authenticated with GitHub API")

        except GithubException as e:
            logger.error(f"GitHub authentication failed: {e}")
            raise GitHubClientException(f"Authentication failed: {e}")

        # GraphQL setup
        self.graphql_url = graphql_url or f"{base_url}/graphql"
        self.graphql_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # Cache for repository objects
        self._repo_cache: Dict[str, Repository] = {}

    def _get_repository(
        self, org: Optional[str] = None, repo: Optional[str] = None
    ) -> Repository:
        """
        Get repository object with caching.

        Args:
            org: Organization name (uses default if not provided)
            repo: Repository name (uses default if not provided)

        Returns:
            Repository object

        Raises:
            GitHubClientException: If repository not found
        """
        org = org or self.org
        repo = repo or self.repo

        if not org or not repo:
            raise GitHubClientException(
                "Organization and repository must be specified"
            )

        cache_key = f"{org}/{repo}"
        if cache_key in self._repo_cache:
            return self._repo_cache[cache_key]

        try:
            repository = self.client.get_repo(cache_key)
            self._repo_cache[cache_key] = repository
            return repository
        except GithubException as e:
            logger.error(f"Repository {cache_key} not found: {e}")
            raise GitHubClientException(f"Repository not found: {e}")

    def _check_rate_limit(self) -> Tuple[int, int, datetime]:
        """
        Check current rate limit status.

        Returns:
            Tuple of (remaining, limit, reset_time)

        Raises:
            RateLimitException: If rate limit threshold exceeded
        """
        rate_limit = self.client.get_rate_limit()
        core = rate_limit.core

        remaining = core.remaining
        limit = core.limit
        reset_time = core.reset

        if remaining < self.rate_limit_threshold:
            logger.warning(
                f"Rate limit low: {remaining}/{limit} "
                f"(resets at {reset_time})"
            )

        if remaining == 0:
            raise RateLimitException(
                f"Rate limit exceeded. Resets at {reset_time}"
            )

        return remaining, limit, reset_time

    # ========================================================================
    # Issue Operations
    # ========================================================================

    def create_issue(
        self,
        title: str,
        body: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None,
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Issue:
        """
        Create a new GitHub issue.

        Args:
            title: Issue title
            body: Issue description (markdown supported)
            labels: List of label names
            assignees: List of GitHub usernames to assign
            milestone: Milestone number
            org: Organization name
            repo: Repository name

        Returns:
            Created issue object

        Raises:
            GitHubClientException: If issue creation fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)

            # Prepare issue parameters
            issue_params: Dict[str, Any] = {"title": title}

            if body:
                issue_params["body"] = body

            if labels:
                issue_params["labels"] = labels

            if assignees:
                issue_params["assignees"] = assignees

            if milestone:
                milestone_obj = repository.get_milestone(milestone)
                issue_params["milestone"] = milestone_obj

            issue = repository.create_issue(**issue_params)
            logger.info(
                f"Created issue #{issue.number}: {title} "
                f"in {repository.full_name}"
            )
            return issue

        except GithubException as e:
            logger.error(f"Failed to create issue: {e}")
            raise GitHubClientException(f"Issue creation failed: {e}")

    def update_issue(
        self,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[GitHubIssueState] = None,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None,
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Issue:
        """
        Update an existing GitHub issue.

        Args:
            issue_number: Issue number
            title: New issue title
            body: New issue description
            state: New issue state (open/closed)
            labels: New list of label names
            assignees: New list of assignees
            milestone: New milestone number
            org: Organization name
            repo: Repository name

        Returns:
            Updated issue object

        Raises:
            GitHubClientException: If update fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)
            issue = repository.get_issue(issue_number)

            # Update fields
            if title:
                issue.edit(title=title)

            if body is not None:
                issue.edit(body=body)

            if state:
                issue.edit(state=state.value)

            if labels is not None:
                issue.set_labels(*labels)

            if assignees is not None:
                issue.edit(assignees=assignees)

            if milestone is not None:
                milestone_obj = repository.get_milestone(milestone)
                issue.edit(milestone=milestone_obj)

            logger.info(
                f"Updated issue #{issue_number} in {repository.full_name}"
            )
            return issue

        except GithubException as e:
            logger.error(f"Failed to update issue #{issue_number}: {e}")
            raise GitHubClientException(f"Issue update failed: {e}")

    def close_issue(
        self,
        issue_number: int,
        comment: Optional[str] = None,
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Issue:
        """
        Close a GitHub issue.

        Args:
            issue_number: Issue number
            comment: Optional closing comment
            org: Organization name
            repo: Repository name

        Returns:
            Closed issue object

        Raises:
            GitHubClientException: If close fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)
            issue = repository.get_issue(issue_number)

            if comment:
                issue.create_comment(comment)

            issue.edit(state="closed")
            logger.info(
                f"Closed issue #{issue_number} in {repository.full_name}"
            )
            return issue

        except GithubException as e:
            logger.error(f"Failed to close issue #{issue_number}: {e}")
            raise GitHubClientException(f"Issue close failed: {e}")

    def add_issue_labels(
        self,
        issue_number: int,
        labels: List[str],
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Issue:
        """
        Add labels to an issue.

        Args:
            issue_number: Issue number
            labels: List of label names to add
            org: Organization name
            repo: Repository name

        Returns:
            Updated issue object

        Raises:
            GitHubClientException: If operation fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)
            issue = repository.get_issue(issue_number)

            issue.add_to_labels(*labels)
            logger.info(
                f"Added labels {labels} to issue #{issue_number}"
            )
            return issue

        except GithubException as e:
            logger.error(f"Failed to add labels: {e}")
            raise GitHubClientException(f"Label addition failed: {e}")

    def search_issues(
        self,
        query: str,
        state: GitHubIssueState = GitHubIssueState.OPEN,
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> List[Issue]:
        """
        Search for issues using GitHub's search API.

        Args:
            query: Search query string
            state: Issue state filter
            labels: Filter by labels
            assignee: Filter by assignee
            org: Organization name
            repo: Repository name

        Returns:
            List of matching issues

        Raises:
            GitHubClientException: If search fails
        """
        try:
            self._check_rate_limit()

            # Build search query
            search_terms = [query]

            if org and repo:
                search_terms.append(f"repo:{org}/{repo}")
            elif org:
                search_terms.append(f"org:{org}")

            if state != GitHubIssueState.ALL:
                search_terms.append(f"state:{state.value}")

            if labels:
                for label in labels:
                    search_terms.append(f'label:"{label}"')

            if assignee:
                search_terms.append(f"assignee:{assignee}")

            search_query = " ".join(search_terms)
            logger.info(f"Searching issues: {search_query}")

            issues = self.client.search_issues(search_query)
            return list(issues)

        except GithubException as e:
            logger.error(f"Issue search failed: {e}")
            raise GitHubClientException(f"Search failed: {e}")

    # ========================================================================
    # Label Management
    # ========================================================================

    def create_label(
        self,
        name: str,
        color: str,
        description: str = "",
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Label:
        """
        Create a new label in the repository.

        Args:
            name: Label name
            color: Hex color code (without #)
            description: Label description
            org: Organization name
            repo: Repository name

        Returns:
            Created label object

        Raises:
            GitHubClientException: If creation fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)

            # Remove # if present
            color = color.lstrip("#")

            label = repository.create_label(
                name=name, color=color, description=description
            )
            logger.info(f"Created label '{name}' in {repository.full_name}")
            return label

        except GithubException as e:
            logger.error(f"Failed to create label '{name}': {e}")
            raise GitHubClientException(f"Label creation failed: {e}")

    def get_labels(
        self, org: Optional[str] = None, repo: Optional[str] = None
    ) -> List[Label]:
        """
        Get all labels in the repository.

        Args:
            org: Organization name
            repo: Repository name

        Returns:
            List of label objects

        Raises:
            GitHubClientException: If operation fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)
            return list(repository.get_labels())

        except GithubException as e:
            logger.error(f"Failed to get labels: {e}")
            raise GitHubClientException(f"Get labels failed: {e}")

    # ========================================================================
    # Milestone Management
    # ========================================================================

    def create_milestone(
        self,
        title: str,
        description: Optional[str] = None,
        due_on: Optional[datetime] = None,
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Milestone:
        """
        Create a new milestone.

        Args:
            title: Milestone title
            description: Milestone description
            due_on: Due date
            org: Organization name
            repo: Repository name

        Returns:
            Created milestone object

        Raises:
            GitHubClientException: If creation fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)

            milestone = repository.create_milestone(
                title=title, description=description or "", due_on=due_on
            )
            logger.info(
                f"Created milestone '{title}' in {repository.full_name}"
            )
            return milestone

        except GithubException as e:
            logger.error(f"Failed to create milestone: {e}")
            raise GitHubClientException(f"Milestone creation failed: {e}")

    # ========================================================================
    # Pull Request Operations
    # ========================================================================

    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None,
        draft: bool = False,
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> PullRequest:
        """
        Create a new pull request.

        Args:
            title: PR title
            head: Name of branch with changes
            base: Name of branch to merge into
            body: PR description
            draft: Create as draft PR
            org: Organization name
            repo: Repository name

        Returns:
            Created pull request object

        Raises:
            GitHubClientException: If creation fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)

            pr = repository.create_pull(
                title=title, body=body or "", head=head, base=base, draft=draft
            )
            logger.info(
                f"Created PR #{pr.number}: {title} in {repository.full_name}"
            )
            return pr

        except GithubException as e:
            logger.error(f"Failed to create PR: {e}")
            raise GitHubClientException(f"PR creation failed: {e}")

    def link_pr_to_issue(
        self,
        pr_number: int,
        issue_number: int,
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> bool:
        """
        Link a pull request to an issue using keywords.

        Args:
            pr_number: Pull request number
            issue_number: Issue number to link
            org: Organization name
            repo: Repository name

        Returns:
            True if successful

        Raises:
            GitHubClientException: If operation fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)
            pr = repository.get_pull(pr_number)

            # Add closing keyword to PR body
            current_body = pr.body or ""
            link_text = f"\n\nCloses #{issue_number}"

            if f"#{issue_number}" not in current_body:
                pr.edit(body=current_body + link_text)
                logger.info(f"Linked PR #{pr_number} to issue #{issue_number}")

            return True

        except GithubException as e:
            logger.error(f"Failed to link PR to issue: {e}")
            raise GitHubClientException(f"PR linking failed: {e}")

    # ========================================================================
    # GitHub Projects (Classic) - REST API
    # ========================================================================

    def get_project_columns(
        self, project_id: int
    ) -> List[ProjectColumn]:
        """
        Get columns in a project (classic).

        Args:
            project_id: Project ID

        Returns:
            List of project column objects

        Raises:
            GitHubClientException: If operation fails
        """
        try:
            self._check_rate_limit()
            project = self.client.get_project(project_id)
            return list(project.get_columns())

        except GithubException as e:
            logger.error(f"Failed to get project columns: {e}")
            raise GitHubClientException(f"Get columns failed: {e}")

    def add_issue_to_classic_project(
        self,
        project_id: int,
        column_id: int,
        issue: Issue,
    ) -> ProjectCard:
        """
        Add an issue to a classic project board.

        Args:
            project_id: Project ID
            column_id: Column ID
            issue: Issue object

        Returns:
            Created project card

        Raises:
            GitHubClientException: If operation fails
        """
        try:
            self._check_rate_limit()
            project = self.client.get_project(project_id)
            column = project.get_column(column_id)

            card = column.create_card(
                content_id=issue.id, content_type="Issue"
            )
            logger.info(f"Added issue #{issue.number} to project {project_id}")
            return card

        except GithubException as e:
            logger.error(f"Failed to add issue to project: {e}")
            raise GitHubClientException(f"Add to project failed: {e}")

    # ========================================================================
    # GitHub Projects v2 - GraphQL API
    # ========================================================================

    def _execute_graphql(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Query response data

        Raises:
            GitHubClientException: If query fails
        """
        try:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables

            response = requests.post(
                self.graphql_url,
                headers=self.graphql_headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()

            if "errors" in data:
                error_msg = "; ".join(
                    [err.get("message", str(err)) for err in data["errors"]]
                )
                raise GitHubClientException(f"GraphQL error: {error_msg}")

            return data.get("data", {})

        except requests.exceptions.RequestException as e:
            logger.error(f"GraphQL request failed: {e}")
            raise GitHubClientException(f"GraphQL request failed: {e}")

    def get_organization_projects_v2(
        self, org: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get Projects v2 for an organization.

        Args:
            org: Organization login
            limit: Maximum number of projects to return

        Returns:
            List of project data dictionaries

        Raises:
            GitHubClientException: If query fails
        """
        org = org or self.org
        if not org:
            raise GitHubClientException("Organization must be specified")

        query = """
        query($org: String!, $limit: Int!) {
          organization(login: $org) {
            projectsV2(first: $limit) {
              nodes {
                id
                number
                title
                shortDescription
                url
                closed
                createdAt
                updatedAt
              }
            }
          }
        }
        """

        variables = {"org": org, "limit": limit}
        data = self._execute_graphql(query, variables)

        projects = (
            data.get("organization", {}).get("projectsV2", {}).get("nodes", [])
        )
        logger.info(f"Retrieved {len(projects)} projects for org {org}")
        return projects

    def add_issue_to_project_v2(
        self,
        project_id: str,
        issue_id: str,
    ) -> Dict[str, Any]:
        """
        Add an issue to a Projects v2 board.

        Args:
            project_id: Project node ID (from GraphQL)
            issue_id: Issue node ID (from GraphQL)

        Returns:
            Created project item data

        Raises:
            GitHubClientException: If operation fails
        """
        mutation = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {
            projectId: $projectId
            contentId: $contentId
          }) {
            item {
              id
              content {
                ... on Issue {
                  number
                  title
                }
              }
            }
          }
        }
        """

        variables = {"projectId": project_id, "contentId": issue_id}
        data = self._execute_graphql(mutation, variables)

        item = data.get("addProjectV2ItemById", {}).get("item", {})
        logger.info(f"Added issue to project v2: {project_id}")
        return item

    def update_project_v2_item_field(
        self,
        project_id: str,
        item_id: str,
        field_id: str,
        value: Any,
    ) -> Dict[str, Any]:
        """
        Update a field value for a Projects v2 item.

        Args:
            project_id: Project node ID
            item_id: Project item ID
            field_id: Field ID to update
            value: New field value

        Returns:
            Updated project item data

        Raises:
            GitHubClientException: If operation fails
        """
        mutation = """
        mutation(
          $projectId: ID!
          $itemId: ID!
          $fieldId: ID!
          $value: String!
        ) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId
            itemId: $itemId
            fieldId: $fieldId
            value: {
              text: $value
            }
          }) {
            projectV2Item {
              id
            }
          }
        }
        """

        variables = {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "value": str(value),
        }
        data = self._execute_graphql(mutation, variables)

        item = (
            data.get("updateProjectV2ItemFieldValue", {})
            .get("projectV2Item", {})
        )
        logger.info(f"Updated project v2 item field: {item_id}")
        return item

    def get_issue_node_id(
        self,
        issue_number: int,
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> str:
        """
        Get the GraphQL node ID for an issue.

        Args:
            issue_number: Issue number
            org: Organization name
            repo: Repository name

        Returns:
            Issue node ID

        Raises:
            GitHubClientException: If issue not found
        """
        try:
            repository = self._get_repository(org, repo)
            issue = repository.get_issue(issue_number)
            return issue.node_id

        except GithubException as e:
            logger.error(f"Failed to get issue node ID: {e}")
            raise GitHubClientException(f"Get node ID failed: {e}")

    # ========================================================================
    # Webhook Management
    # ========================================================================

    def create_webhook(
        self,
        config: WebhookConfig,
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a repository webhook.

        Args:
            config: Webhook configuration
            org: Organization name
            repo: Repository name

        Returns:
            Created webhook data

        Raises:
            GitHubClientException: If creation fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)

            webhook_config = {
                "url": config.url,
                "content_type": config.content_type,
            }

            if config.secret:
                webhook_config["secret"] = config.secret

            hook = repository.create_hook(
                name="web",
                config=webhook_config,
                events=[e.value for e in config.events],
                active=config.active,
            )

            logger.info(
                f"Created webhook for {repository.full_name}: {config.url}"
            )
            return {
                "id": hook.id,
                "url": hook.url,
                "events": hook.events,
                "active": hook.active,
            }

        except GithubException as e:
            logger.error(f"Failed to create webhook: {e}")
            raise GitHubClientException(f"Webhook creation failed: {e}")

    # ========================================================================
    # GitHub Actions Integration
    # ========================================================================

    def trigger_workflow(
        self,
        workflow_id: str,
        ref: str = "main",
        inputs: Optional[Dict[str, Any]] = None,
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> bool:
        """
        Trigger a GitHub Actions workflow.

        Args:
            workflow_id: Workflow file name or ID
            ref: Git reference (branch/tag)
            inputs: Workflow inputs
            org: Organization name
            repo: Repository name

        Returns:
            True if triggered successfully

        Raises:
            GitHubClientException: If trigger fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)

            workflow = repository.get_workflow(workflow_id)
            result = workflow.create_dispatch(ref=ref, inputs=inputs or {})

            logger.info(
                f"Triggered workflow {workflow_id} on {ref} "
                f"in {repository.full_name}"
            )
            return result

        except GithubException as e:
            logger.error(f"Failed to trigger workflow: {e}")
            raise GitHubClientException(f"Workflow trigger failed: {e}")

    def get_workflow_runs(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        branch: Optional[str] = None,
        org: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get workflow runs for a repository.

        Args:
            workflow_id: Filter by workflow ID
            status: Filter by status (completed, in_progress, etc.)
            branch: Filter by branch
            org: Organization name
            repo: Repository name

        Returns:
            List of workflow run data

        Raises:
            GitHubClientException: If query fails
        """
        try:
            self._check_rate_limit()
            repository = self._get_repository(org, repo)

            if workflow_id:
                workflow = repository.get_workflow(workflow_id)
                runs = workflow.get_runs(
                    status=status,
                    branch=branch,
                )
            else:
                runs = repository.get_workflow_runs(
                    status=status,
                    branch=branch,
                )

            return [
                {
                    "id": run.id,
                    "name": run.name,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "head_branch": run.head_branch,
                    "created_at": run.created_at.isoformat(),
                    "updated_at": run.updated_at.isoformat(),
                    "html_url": run.html_url,
                }
                for run in runs
            ]

        except GithubException as e:
            logger.error(f"Failed to get workflow runs: {e}")
            raise GitHubClientException(f"Get workflow runs failed: {e}")

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_repository_info(
        self, org: Optional[str] = None, repo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get repository information.

        Args:
            org: Organization name
            repo: Repository name

        Returns:
            Repository information dictionary

        Raises:
            GitHubClientException: If repository not found
        """
        try:
            repository = self._get_repository(org, repo)

            return {
                "name": repository.name,
                "full_name": repository.full_name,
                "description": repository.description,
                "url": repository.html_url,
                "private": repository.private,
                "default_branch": repository.default_branch,
                "open_issues": repository.open_issues_count,
                "stargazers": repository.stargazers_count,
                "forks": repository.forks_count,
                "created_at": repository.created_at.isoformat(),
                "updated_at": repository.updated_at.isoformat(),
            }

        except GithubException as e:
            logger.error(f"Failed to get repository info: {e}")
            raise GitHubClientException(f"Get repository info failed: {e}")

    def get_authenticated_user(self) -> Dict[str, Any]:
        """
        Get authenticated user information.

        Returns:
            User information dictionary

        Raises:
            GitHubClientException: If operation fails
        """
        try:
            user = self.client.get_user()
            return {
                "login": user.login,
                "name": user.name,
                "email": user.email,
                "company": user.company,
                "location": user.location,
                "bio": user.bio,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "following": user.following,
            }

        except GithubException as e:
            logger.error(f"Failed to get user info: {e}")
            raise GitHubClientException(f"Get user info failed: {e}")
