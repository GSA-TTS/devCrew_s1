"""
Jira Client - Comprehensive Jira REST API integration for PM Platform.

Production-ready client for Jira Cloud and Server with full support for:
- Issue CRUD operations with custom fields
- JQL query execution with pagination
- Sprint management (Agile/Software API)
- Project and board operations
- Workflow transitions and comments
- Attachment handling
- Bulk operations with rate limiting

Features:
    - Multiple authentication methods (Basic, OAuth, API token)
    - Automatic retry with exponential backoff
    - Rate limiting handling
    - Custom field schema discovery
    - Story points and sprint operations
    - Issue linking and subtask creation
    - Comprehensive error handling
    - Type-safe Pydantic models

Example:
    >>> from jira_client import JiraClient, JiraAuthConfig, AuthType
    >>> config = JiraAuthConfig(
    ...     url="https://company.atlassian.net",
    ...     auth_type=AuthType.API_TOKEN,
    ...     username="user@company.com",
    ...     api_token="xxx"
    ... )
    >>> client = JiraClient(config)
    >>> issue = client.create_issue(
    ...     project="PROJ",
    ...     summary="Bug in login",
    ...     issue_type="Bug",
    ...     description="Login fails with SSO"
    ... )
"""

import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from jira import JIRA
from jira.exceptions import JIRAError
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AuthType(str, Enum):
    """Supported Jira authentication types."""

    BASIC = "basic"
    API_TOKEN = "api_token"
    OAUTH = "oauth"
    PAT = "personal_access_token"


class IssueType(str, Enum):
    """Common Jira issue types."""

    BUG = "Bug"
    STORY = "Story"
    TASK = "Task"
    EPIC = "Epic"
    SUBTASK = "Sub-task"
    IMPROVEMENT = "Improvement"
    NEW_FEATURE = "New Feature"


class IssuePriority(str, Enum):
    """Standard Jira issue priorities."""

    BLOCKER = "Blocker"
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOWEST = "Lowest"
    HIGHEST = "Highest"


class IssueStatus(str, Enum):
    """Common Jira issue statuses."""

    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    CLOSED = "Closed"
    BLOCKED = "Blocked"
    READY_FOR_TEST = "Ready for Test"


class SprintState(str, Enum):
    """Jira sprint states."""

    FUTURE = "future"
    ACTIVE = "active"
    CLOSED = "closed"


class JiraAuthConfig(BaseModel):
    """Jira authentication configuration."""

    url: str = Field(..., description="Jira instance URL")
    auth_type: AuthType = Field(
        default=AuthType.API_TOKEN, description="Authentication method"
    )
    username: Optional[str] = Field(None, description="Username or email")
    password: Optional[str] = Field(None, description="Password (Basic auth)")
    api_token: Optional[str] = Field(None, description="API token")
    access_token: Optional[str] = Field(None, description="OAuth access token")
    access_token_secret: Optional[str] = Field(
        None, description="OAuth access token secret"
    )
    consumer_key: Optional[str] = Field(None, description="OAuth consumer key")
    key_cert: Optional[str] = Field(None, description="OAuth key certificate")
    verify_ssl: bool = Field(default=True, description="Verify SSL")
    timeout: int = Field(default=60, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")

    @validator("url")
    def validate_url(cls, v: str) -> str:
        """Ensure URL doesn't end with slash."""
        return v.rstrip("/")


class JiraIssue(BaseModel):
    """Jira issue model."""

    key: str = Field(..., description="Issue key (e.g., PROJ-123)")
    id: str = Field(..., description="Internal issue ID")
    summary: str = Field(..., description="Issue summary")
    description: Optional[str] = Field(None, description="Issue description")
    issue_type: str = Field(..., description="Issue type")
    status: str = Field(..., description="Current status")
    priority: Optional[str] = Field(None, description="Issue priority")
    assignee: Optional[str] = Field(None, description="Assignee username")
    reporter: Optional[str] = Field(None, description="Reporter username")
    created: datetime = Field(..., description="Creation timestamp")
    updated: datetime = Field(..., description="Last update timestamp")
    resolved: Optional[datetime] = Field(None, description="Resolution date")
    story_points: Optional[float] = Field(None, description="Story points")
    sprint: Optional[str] = Field(None, description="Current sprint name")
    epic_key: Optional[str] = Field(None, description="Parent epic key")
    labels: List[str] = Field(default_factory=list, description="Issue labels")
    components: List[str] = Field(default_factory=list, description="Components")
    custom_fields: Dict[str, Any] = Field(
        default_factory=dict, description="Custom field values"
    )

    class Config:
        """Pydantic model configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class JiraSprint(BaseModel):
    """Jira sprint model."""

    id: int = Field(..., description="Sprint ID")
    name: str = Field(..., description="Sprint name")
    state: SprintState = Field(..., description="Sprint state")
    board_id: int = Field(..., description="Board ID")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    complete_date: Optional[datetime] = Field(None, description="Complete date")
    goal: Optional[str] = Field(None, description="Sprint goal")

    class Config:
        """Pydantic model configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class JiraClientError(Exception):
    """Base exception for Jira client errors."""

    pass


class JiraAuthError(JiraClientError):
    """Authentication-related errors."""

    pass


class JiraNotFoundError(JiraClientError):
    """Resource not found errors."""

    pass


class JiraPermissionError(JiraClientError):
    """Permission-related errors."""

    pass


class JiraRateLimitError(JiraClientError):
    """Rate limit exceeded errors."""

    pass


class JiraValidationError(JiraClientError):
    """Validation errors."""

    pass


class JiraClient:
    """
    Comprehensive Jira API client with full CRUD operations.

    Provides a production-ready interface to Jira REST API with support for
    issues, sprints, projects, boards, and custom fields.

    Attributes:
        config: Authentication and connection configuration
        jira: Underlying JIRA client instance
    """

    def __init__(
        self,
        config: Optional[JiraAuthConfig] = None,
        server: Optional[str] = None,
        username: Optional[str] = None,
        api_token: Optional[str] = None,
        default_project: Optional[str] = None,
    ) -> None:
        """
        Initialize Jira client with authentication.

        Supports both new config-based and legacy parameter-based init.

        Args:
            config: JiraAuthConfig object (new style)
            server: Jira server URL (legacy, for backward compatibility)
            username: Username/email (legacy)
            api_token: API token (legacy)
            default_project: Default project key

        Raises:
            JiraAuthError: If authentication fails
        """
        # Support legacy initialization for backward compatibility
        if config is None and server and username and api_token:
            config = JiraAuthConfig(
                url=server,
                auth_type=AuthType.API_TOKEN,
                username=username,
                api_token=api_token,
            )
        elif config is None:
            raise JiraAuthError("Must provide either config or server/username/token")

        self.config = config
        self.server = config.url
        self.username = config.username
        self.default_project = default_project
        self._jira: Optional[JIRA] = None
        self._custom_field_cache: Dict[str, str] = {}
        self._connect()

    def _connect(self) -> None:
        """
        Establish connection to Jira instance.

        Raises:
            JiraAuthError: If connection fails
        """
        try:
            auth_params: Dict[str, Any] = {
                "server": self.config.url,
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries,
            }

            # Configure authentication
            if self.config.auth_type == AuthType.API_TOKEN:
                if not self.config.username or not self.config.api_token:
                    raise JiraAuthError(
                        "Username and API token required for API token auth"
                    )
                auth_params["basic_auth"] = (
                    self.config.username,
                    self.config.api_token,
                )

            elif self.config.auth_type == AuthType.BASIC:
                if not self.config.username or not self.config.password:
                    raise JiraAuthError("Username and password required for basic auth")
                auth_params["basic_auth"] = (self.config.username, self.config.password)

            elif self.config.auth_type == AuthType.OAUTH:
                if not all(
                    [
                        self.config.access_token,
                        self.config.access_token_secret,
                        self.config.consumer_key,
                        self.config.key_cert,
                    ]
                ):
                    raise JiraAuthError(
                        "OAuth requires access token, secret, consumer key, "
                        "and key cert"
                    )
                auth_params["oauth"] = {
                    "access_token": self.config.access_token,
                    "access_token_secret": self.config.access_token_secret,
                    "consumer_key": self.config.consumer_key,
                    "key_cert": self.config.key_cert,
                }

            elif self.config.auth_type == AuthType.PAT:
                if not self.config.api_token:
                    raise JiraAuthError("API token required for PAT authentication")
                auth_params["token_auth"] = self.config.api_token

            # SSL verification
            if not self.config.verify_ssl:
                auth_params["options"] = {"verify": False}

            self._jira = JIRA(**auth_params)
            # Test connection
            self._jira.myself()
            logger.info("Successfully connected to Jira instance: %s", self.config.url)

        except JIRAError as e:
            raise JiraAuthError(f"Failed to connect to Jira: {e}") from e
        except Exception as e:
            raise JiraAuthError(f"Unexpected error connecting to Jira: {e}") from e

    @property
    def jira(self) -> JIRA:
        """Get JIRA client instance."""
        if self._jira is None:
            raise JiraClientError("Not connected to Jira")
        return self._jira

    @property
    def client(self) -> JIRA:
        """Get JIRA client instance (legacy property name)."""
        return self.jira

    def _handle_jira_error(self, error: JIRAError) -> None:
        """
        Convert JIRA errors to custom exceptions.

        Args:
            error: JIRA error to handle

        Raises:
            Appropriate JiraClientError subclass
        """
        status_code = getattr(error, "status_code", None)
        if status_code == 401:
            raise JiraAuthError(f"Authentication failed: {error}")
        elif status_code == 403:
            raise JiraPermissionError(f"Permission denied: {error}")
        elif status_code == 404:
            raise JiraNotFoundError(f"Resource not found: {error}")
        elif status_code == 429:
            raise JiraRateLimitError(f"Rate limit exceeded: {error}")
        elif status_code in (400, 422):
            raise JiraValidationError(f"Validation error: {error}")
        else:
            raise JiraClientError(f"Jira API error: {error}")

    def _retry_with_backoff(self, func: callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with exponential backoff retry.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                return func(*args, **kwargs)
            except JiraRateLimitError as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    wait_time = (2**attempt) * 5
                    logger.warning(
                        "Rate limit hit, waiting %s seconds (attempt %s/%s)",
                        wait_time,
                        attempt + 1,
                        self.config.max_retries,
                    )
                    time.sleep(wait_time)
            except JIRAError as e:
                self._handle_jira_error(e)

        if last_exception:
            raise last_exception
        raise JiraClientError("Retry logic failed unexpectedly")

    def get_custom_fields(self) -> Dict[str, str]:
        """
        Get custom field mapping (name -> field_id).

        Returns:
            Dictionary mapping field names to field IDs
        """
        if not self._custom_field_cache:
            self._load_custom_fields()
        return self._custom_field_cache

    def _get_custom_field_id(self, field_name: str) -> Optional[str]:
        """
        Get custom field ID by name.

        Args:
            field_name: Custom field name

        Returns:
            Custom field ID (e.g., customfield_10001) or None
        """
        if not self._custom_field_cache:
            self._load_custom_fields()

        return self._custom_field_cache.get(field_name.lower())

    def _load_custom_fields(self) -> None:
        """Load and cache custom field mappings."""
        try:
            fields = self.jira.fields()
            for field in fields:
                if field.get("custom"):
                    name = field["name"].lower()
                    field_id = field["id"]
                    self._custom_field_cache[name] = field_id
                    logger.debug("Cached custom field: %s -> %s", name, field_id)
            logger.info("Loaded %s custom fields", len(self._custom_field_cache))
        except JIRAError as e:
            logger.warning("Failed to load custom fields: %s", e)

    def _parse_issue(self, jira_issue: Any) -> JiraIssue:
        """
        Parse JIRA issue object to JiraIssue model.

        Args:
            jira_issue: JIRA issue object

        Returns:
            Parsed JiraIssue model
        """
        fields = jira_issue.fields

        # Parse timestamps
        created = datetime.fromisoformat(fields.created.replace("Z", "+00:00"))
        updated = datetime.fromisoformat(fields.updated.replace("Z", "+00:00"))
        resolved = None
        if fields.resolutiondate:
            resolved = datetime.fromisoformat(
                fields.resolutiondate.replace("Z", "+00:00")
            )

        # Extract story points
        story_points = None
        story_points_field = self._get_custom_field_id("story points")
        if story_points_field:
            story_points = getattr(fields, story_points_field, None)

        # Extract sprint
        sprint_name = None
        sprint_field = self._get_custom_field_id("sprint")
        if sprint_field:
            sprint_data = getattr(fields, sprint_field, None)
            if sprint_data and isinstance(sprint_data, list) and sprint_data:
                sprint_name = sprint_data[0].name

        # Extract epic
        epic_key = None
        epic_field = self._get_custom_field_id("epic link")
        if epic_field:
            epic_key = getattr(fields, epic_field, None)

        return JiraIssue(
            key=jira_issue.key,
            id=jira_issue.id,
            summary=fields.summary,
            description=fields.description or "",
            issue_type=fields.issuetype.name,
            status=fields.status.name,
            priority=fields.priority.name if fields.priority else None,
            assignee=fields.assignee.name if fields.assignee else None,
            reporter=fields.reporter.name if fields.reporter else None,
            created=created,
            updated=updated,
            resolved=resolved,
            story_points=story_points,
            sprint=sprint_name,
            epic_key=epic_key,
            labels=fields.labels or [],
            components=[c.name for c in (fields.components or [])],
            custom_fields={},
        )

    def _format_issue(self, issue: Any) -> Dict[str, Any]:
        """
        Format Jira issue object to dictionary (legacy method).

        Args:
            issue: JIRA issue object

        Returns:
            Formatted issue dictionary
        """
        jira_issue = self._parse_issue(issue)
        return {
            "key": jira_issue.key,
            "id": jira_issue.id,
            "summary": jira_issue.summary,
            "description": jira_issue.description,
            "status": jira_issue.status,
            "type": jira_issue.issue_type,
            "priority": jira_issue.priority,
            "assignee": jira_issue.assignee,
            "reporter": jira_issue.reporter,
            "created": jira_issue.created.isoformat(),
            "updated": jira_issue.updated.isoformat(),
            "labels": jira_issue.labels,
            "url": f"{self.server}/browse/{jira_issue.key}",
            "project": issue.fields.project.key,
        }

    # Issue CRUD Operations

    def create_issue(
        self,
        project: Optional[str] = None,
        summary: str = "",
        issue_type: str = "Task",
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        story_points: Optional[float] = None,
        epic_key: Optional[str] = None,
        parent_key: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> Optional[Union[JiraIssue, Dict[str, Any]]]:
        """
        Create a new Jira issue.

        Args:
            project: Project key (uses default if not provided)
            summary: Issue summary/title
            issue_type: Issue type (Task, Bug, Story, etc.)
            description: Issue description
            priority: Priority level
            assignee: Assignee username
            labels: List of labels
            components: List of component names
            story_points: Story point estimate
            epic_key: Parent epic key
            parent_key: Parent issue key (for subtasks)
            custom_fields: Custom field values (name -> value)

        Returns:
            Created JiraIssue or dict (legacy), None if creation fails

        Raises:
            JiraValidationError: If validation fails
            JiraClientError: If creation fails
        """
        project_key = project or self.default_project
        if not project_key:
            logger.error("No project specified")
            return None

        try:
            fields: Dict[str, Any] = {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": issue_type},
            }

            if description:
                fields["description"] = description
            if priority:
                fields["priority"] = {"name": priority}
            if assignee:
                fields["assignee"] = {"name": assignee}
            if labels:
                fields["labels"] = labels
            if components:
                fields["components"] = [{"name": c} for c in components]
            if parent_key:
                fields["parent"] = {"key": parent_key}

            # Handle story points
            if story_points is not None:
                sp_field = self._get_custom_field_id("story points")
                if sp_field:
                    fields[sp_field] = story_points

            # Handle epic link
            if epic_key:
                epic_field = self._get_custom_field_id("epic link")
                if epic_field:
                    fields[epic_field] = epic_key

            # Add custom fields
            if custom_fields:
                cf_mapping = self.get_custom_fields()
                for name, value in custom_fields.items():
                    if name in cf_mapping:
                        fields[cf_mapping[name]] = value
                    elif name.lower() in cf_mapping:
                        fields[cf_mapping[name.lower()]] = value
                    else:
                        logger.warning("Unknown custom field: %s", name)

            issue = self._retry_with_backoff(self.jira.create_issue, fields=fields)
            logger.info("Created issue: %s", issue.key)
            return self._format_issue(issue)

        except JIRAError as e:
            logger.error("Failed to create issue: %s", e)
            return None

    def get_issue(
        self, issue_key: str, expand: Optional[List[str]] = None
    ) -> Optional[Union[JiraIssue, Dict[str, Any]]]:
        """
        Get issue by key.

        Args:
            issue_key: Issue key (e.g., PROJ-123)
            expand: Additional fields to expand (changelog, renderedFields)

        Returns:
            JiraIssue object or dict (legacy), None if not found

        Raises:
            JiraNotFoundError: If issue not found
        """
        try:
            expand_str = ",".join(expand) if expand else None
            issue = self._retry_with_backoff(
                self.jira.issue, issue_key, expand=expand_str
            )
            return self._format_issue(issue)
        except JIRAError as e:
            logger.error("Failed to get issue %s: %s", issue_key, e)
            return None

    def update_issue(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        story_points: Optional[float] = None,
        status: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update existing issue.

        Args:
            issue_key: Issue key to update
            summary: New summary
            description: New description
            priority: New priority
            assignee: New assignee
            labels: New labels (replaces existing)
            story_points: New story points
            status: New status (triggers transition)
            custom_fields: Custom field updates

        Returns:
            True if update successful

        Raises:
            JiraNotFoundError: If issue not found
            JiraValidationError: If validation fails
        """
        try:
            issue = self.jira.issue(issue_key)
            fields: Dict[str, Any] = {}

            if summary is not None:
                fields["summary"] = summary
            if description is not None:
                fields["description"] = description
            if priority is not None:
                fields["priority"] = {"name": priority}
            if assignee is not None:
                fields["assignee"] = {"name": assignee}
            if labels is not None:
                fields["labels"] = labels

            # Handle story points
            if story_points is not None:
                sp_field = self._get_custom_field_id("story points")
                if sp_field:
                    fields[sp_field] = story_points

            # Update custom fields
            if custom_fields:
                cf_mapping = self.get_custom_fields()
                for name, value in custom_fields.items():
                    if name in cf_mapping:
                        fields[cf_mapping[name]] = value
                    elif name.lower() in cf_mapping:
                        fields[cf_mapping[name.lower()]] = value

            if fields:
                self._retry_with_backoff(issue.update, fields=fields)

            # Handle status transition separately
            if status:
                self._transition_issue(issue, status)

            logger.info("Updated issue: %s", issue_key)
            return True

        except JIRAError as e:
            logger.error("Failed to update issue %s: %s", issue_key, e)
            return False

    def delete_issue(self, issue_key: str) -> bool:
        """
        Delete issue.

        Args:
            issue_key: Issue key to delete

        Returns:
            True if deletion successful

        Raises:
            JiraNotFoundError: If issue not found
            JiraPermissionError: If no permission to delete
        """
        try:
            issue = self.jira.issue(issue_key)
            self._retry_with_backoff(issue.delete)
            logger.info("Deleted issue: %s", issue_key)
            return True
        except JIRAError as e:
            logger.error("Failed to delete issue %s: %s", issue_key, e)
            return False

    def _transition_issue(self, issue: Any, status: str) -> bool:
        """
        Transition issue to new status.

        Args:
            issue: JIRA issue object
            status: Target status name

        Returns:
            True if transition successful
        """
        try:
            transitions = self.jira.transitions(issue)
            for transition in transitions:
                if transition["name"].lower() == status.lower():
                    self.jira.transition_issue(issue, transition["id"])
                    logger.info("Transitioned %s to %s", issue.key, status)
                    return True

            logger.warning("Status '%s' not available for %s", status, issue.key)
            return False

        except JIRAError as e:
            logger.error("Failed to transition %s: %s", issue.key, e)
            return False

    def transition_issue(
        self,
        issue_key: str,
        transition_name: str,
        comment: Optional[str] = None,
        fields: Optional[Dict[str, Any]] = None,
    ) -> Optional[Union[JiraIssue, Dict[str, Any]]]:
        """
        Transition issue to new status.

        Args:
            issue_key: Issue key
            transition_name: Transition name (e.g., "In Progress", "Done")
            comment: Optional comment to add
            fields: Additional fields to set during transition

        Returns:
            Updated JiraIssue or None

        Raises:
            JiraNotFoundError: If issue not found
            JiraValidationError: If transition invalid
        """
        try:
            issue = self.jira.issue(issue_key)
            success = self._transition_issue(issue, transition_name)

            # Add comment if provided
            if comment and success:
                self.add_comment(issue_key, comment)

            if success:
                return self.get_issue(issue_key)
            return None

        except JIRAError as e:
            logger.error("Failed to transition issue: %s", e)
            return None

    # JQL and Search Operations

    def search_issues(
        self,
        jql: str,
        max_results: int = 100,
        start_at: int = 0,
        fields: Optional[List[str]] = None,
        expand: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search issues using JQL.

        Args:
            jql: JQL query string
            max_results: Maximum results to return per page
            start_at: Starting index for pagination
            fields: Specific fields to retrieve
            expand: Fields to expand

        Returns:
            List of issue dictionaries

        Raises:
            JiraValidationError: If JQL is invalid
        """
        try:
            expand_str = ",".join(expand) if expand else None
            issues = self._retry_with_backoff(
                self.jira.search_issues,
                jql,
                startAt=start_at,
                maxResults=max_results,
                fields=fields,
                expand=expand_str,
            )

            result = [self._format_issue(issue) for issue in issues]
            logger.info("Found %s issues", len(result))
            return result

        except JIRAError as e:
            logger.error("Failed to search issues: %s", e)
            return []

    def search_all_issues(
        self, jql: str, batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search all issues matching JQL with automatic pagination.

        Args:
            jql: JQL query string
            batch_size: Results per page

        Returns:
            List of all matching issues

        Raises:
            JiraValidationError: If JQL is invalid
        """
        all_issues: List[Dict[str, Any]] = []
        start_at = 0

        while True:
            issues = self.search_issues(
                jql=jql, max_results=batch_size, start_at=start_at
            )
            all_issues.extend(issues)

            if len(issues) < batch_size:
                break

            start_at += len(issues)

        logger.info("Retrieved all %s issues matching JQL", len(all_issues))
        return all_issues

    # Comment Operations

    def add_comment(self, issue_key: str, comment: str) -> bool:
        """
        Add comment to issue.

        Args:
            issue_key: Issue key
            comment: Comment text

        Returns:
            True if comment added successfully

        Raises:
            JiraNotFoundError: If issue not found
        """
        try:
            self._retry_with_backoff(self.jira.add_comment, issue_key, comment)
            logger.info("Added comment to %s", issue_key)
            return True
        except JIRAError as e:
            logger.error("Failed to add comment: %s", e)
            return False

    def get_comments(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get all comments for issue.

        Args:
            issue_key: Issue key

        Returns:
            List of comment dictionaries

        Raises:
            JiraNotFoundError: If issue not found
        """
        try:
            comments = self._retry_with_backoff(self.jira.comments, issue_key)
            return [
                {
                    "id": c.id,
                    "author": c.author.name,
                    "body": c.body,
                    "created": c.created,
                    "updated": c.updated,
                }
                for c in comments
            ]
        except JIRAError as e:
            logger.error("Failed to get comments: %s", e)
            return []

    # Sprint Operations

    def get_sprint(self, sprint_id: int) -> Optional[Dict[str, Any]]:
        """
        Get sprint by ID.

        Args:
            sprint_id: Sprint ID

        Returns:
            Sprint dictionary or None

        Raises:
            JiraNotFoundError: If sprint not found
        """
        try:
            sprint = self._retry_with_backoff(self.jira.sprint, sprint_id)
            return self._format_sprint(sprint)
        except JIRAError as e:
            logger.error("Failed to get sprint: %s", e)
            return None

    def _format_sprint(self, sprint: Any) -> Dict[str, Any]:
        """
        Format Jira sprint object to dictionary.

        Args:
            sprint: JIRA sprint object

        Returns:
            Formatted sprint dictionary
        """
        return {
            "id": sprint.id,
            "name": sprint.name,
            "state": sprint.state,
            "start_date": getattr(sprint, "startDate", None),
            "end_date": getattr(sprint, "endDate", None),
            "goal": getattr(sprint, "goal", ""),
            "board_id": sprint.originBoardId,
        }

    def get_sprints(
        self, board_id: int, state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get sprints for a board.

        Args:
            board_id: Board ID
            state: Sprint state (active, future, closed) or None for all

        Returns:
            List of sprint dictionaries
        """
        try:
            sprints = self._retry_with_backoff(self.jira.sprints, board_id, state=state)
            return [self._format_sprint(sprint) for sprint in sprints]
        except JIRAError as e:
            logger.error("Failed to get sprints: %s", e)
            return []

    def get_sprint_issues(self, sprint_id: int) -> List[Dict[str, Any]]:
        """
        Get all issues in a sprint.

        Args:
            sprint_id: Sprint ID

        Returns:
            List of issue dictionaries
        """
        jql = f"sprint = {sprint_id}"
        return self.search_all_issues(jql)

    def create_sprint(
        self,
        board_id: int,
        name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        goal: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new sprint.

        Args:
            board_id: Board ID
            name: Sprint name
            start_date: Sprint start date
            end_date: Sprint end date
            goal: Sprint goal

        Returns:
            Sprint data dictionary or None if creation fails

        Raises:
            JiraValidationError: If validation fails
        """
        try:
            sprint_data: Dict[str, Any] = {
                "name": name,
                "originBoardId": board_id,
            }

            if start_date:
                sprint_data["startDate"] = start_date.isoformat()
            if end_date:
                sprint_data["endDate"] = end_date.isoformat()
            if goal:
                sprint_data["goal"] = goal

            sprint = self._retry_with_backoff(self.jira.create_sprint, **sprint_data)
            logger.info("Created sprint: %s", name)
            return self._format_sprint(sprint)

        except JIRAError as e:
            logger.error("Failed to create sprint: %s", e)
            return None

    def start_sprint(
        self,
        sprint_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Start a sprint.

        Args:
            sprint_id: Sprint ID
            start_date: Sprint start date (default: now)
            end_date: Sprint end date (required for starting)

        Returns:
            Updated sprint dictionary

        Raises:
            JiraValidationError: If sprint can't be started
        """
        try:
            update_data: Dict[str, Any] = {"state": "active"}

            if start_date:
                update_data["startDate"] = start_date.isoformat()
            else:
                update_data["startDate"] = datetime.now().isoformat()

            if end_date:
                update_data["endDate"] = end_date.isoformat()

            sprint = self._retry_with_backoff(
                self.jira.update_sprint, sprint_id, **update_data
            )
            logger.info("Started sprint: %s", sprint_id)
            return self._format_sprint(sprint)

        except JIRAError as e:
            logger.error("Failed to start sprint: %s", e)
            return None

    def close_sprint(self, sprint_id: int) -> Optional[Dict[str, Any]]:
        """
        Close a sprint.

        Args:
            sprint_id: Sprint ID

        Returns:
            Updated sprint dictionary

        Raises:
            JiraValidationError: If sprint can't be closed
        """
        try:
            sprint = self._retry_with_backoff(
                self.jira.update_sprint, sprint_id, state="closed"
            )
            logger.info("Closed sprint: %s", sprint_id)
            return self._format_sprint(sprint)

        except JIRAError as e:
            logger.error("Failed to close sprint: %s", e)
            return None

    def add_issues_to_sprint(self, sprint_id: int, issue_keys: List[str]) -> bool:
        """
        Add issues to sprint.

        Args:
            sprint_id: Sprint ID
            issue_keys: List of issue keys to add

        Returns:
            True if all issues added successfully

        Raises:
            JiraNotFoundError: If sprint or issues not found
        """
        try:
            self._retry_with_backoff(
                self.jira.add_issues_to_sprint, sprint_id, issue_keys
            )
            logger.info("Added %s issues to sprint %s", len(issue_keys), sprint_id)
            return True
        except JIRAError as e:
            logger.error("Failed to add issues to sprint: %s", e)
            return False

    # Attachment Operations

    def add_attachment(
        self, issue_key: str, file_path: str, filename: Optional[str] = None
    ) -> bool:
        """
        Upload attachment to issue.

        Args:
            issue_key: Issue key
            file_path: Path to file to upload
            filename: Optional filename override

        Returns:
            True if attachment added successfully

        Raises:
            JiraNotFoundError: If issue not found
            FileNotFoundError: If file doesn't exist
        """
        try:
            with open(file_path, "rb") as f:
                self._retry_with_backoff(
                    self.jira.add_attachment, issue_key, attachment=f, filename=filename
                )
            logger.info("Added attachment to %s", issue_key)
            return True
        except FileNotFoundError:
            logger.error("File not found: %s", file_path)
            return False
        except JIRAError as e:
            logger.error("Failed to add attachment: %s", e)
            return False

    # Link Operations

    def link_issues(
        self,
        from_issue: str,
        to_issue: str,
        link_type: str = "Relates",
        comment: Optional[str] = None,
    ) -> bool:
        """
        Link two issues.

        Args:
            from_issue: Source issue key
            to_issue: Target issue key
            link_type: Link type (Relates, Blocks, Duplicates, etc.)
            comment: Optional comment

        Returns:
            True if issues linked successfully

        Raises:
            JiraNotFoundError: If issues not found
            JiraValidationError: If link type invalid
        """
        try:
            self._retry_with_backoff(
                self.jira.create_issue_link,
                type=link_type,
                inwardIssue=from_issue,
                outwardIssue=to_issue,
                comment={"body": comment} if comment else None,
            )
            logger.info("Linked %s to %s (%s)", from_issue, to_issue, link_type)
            return True
        except JIRAError as e:
            logger.error("Failed to link issues: %s", e)
            return False

    # Bulk Operations

    def bulk_update_issues(
        self, issue_keys: List[str], fields: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Bulk update multiple issues.

        Args:
            issue_keys: List of issue keys to update
            fields: Fields to update (same for all issues)

        Returns:
            List of successfully updated issues

        Raises:
            JiraClientError: If bulk update fails
        """
        updated_issues: List[Dict[str, Any]] = []

        for issue_key in issue_keys:
            try:
                issue = self.jira.issue(issue_key)
                self._retry_with_backoff(issue.update, fields=fields)
                updated = self.get_issue(issue_key)
                if updated:
                    updated_issues.append(updated)
            except JIRAError as e:
                logger.error("Failed to update %s: %s", issue_key, e)
                continue

        logger.info("Bulk updated %s/%s issues", len(updated_issues), len(issue_keys))
        return updated_issues

    # Project and Board Operations

    def get_project(self, project_key: str) -> Optional[Dict[str, Any]]:
        """
        Get project details.

        Args:
            project_key: Project key

        Returns:
            Project data dictionary or None if not found
        """
        try:
            project = self._retry_with_backoff(self.jira.project, project_key)
            return {
                "key": project.key,
                "name": project.name,
                "id": project.id,
                "lead": project.lead.displayName if project.lead else None,
                "description": getattr(project, "description", ""),
                "url": f"{self.server}/browse/{project.key}",
            }
        except JIRAError as e:
            logger.error("Failed to get project %s: %s", project_key, e)
            return None

    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get all accessible projects.

        Returns:
            List of project dictionaries
        """
        try:
            projects = self._retry_with_backoff(self.jira.projects)
            return [
                {
                    "key": p.key,
                    "name": p.name,
                    "id": p.id,
                    "lead": p.lead.name if hasattr(p, "lead") else None,
                }
                for p in projects
            ]
        except JIRAError as e:
            logger.error("Failed to get projects: %s", e)
            return []

    def get_boards(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get boards for a project.

        Args:
            project_key: Project key (uses default if not provided)

        Returns:
            List of board dictionaries
        """
        project = project_key or self.default_project
        try:
            boards = self._retry_with_backoff(self.jira.boards, projectKeyOrID=project)
            return [
                {
                    "id": board.id,
                    "name": board.name,
                    "type": board.type,
                }
                for board in boards
            ]
        except JIRAError as e:
            logger.error("Failed to get boards: %s", e)
            return []

    def get_transitions(self, issue_key: str) -> List[Dict[str, str]]:
        """
        Get available transitions for an issue.

        Args:
            issue_key: Issue key

        Returns:
            List of transition dictionaries
        """
        try:
            issue = self.jira.issue(issue_key)
            transitions = self._retry_with_backoff(self.jira.transitions, issue)
            return [{"id": t["id"], "name": t["name"]} for t in transitions]
        except JIRAError as e:
            logger.error("Failed to get transitions: %s", e)
            return []

    def close(self) -> None:
        """Close Jira client connection."""
        if self._jira:
            self._jira.close()
            self._jira = None
            logger.info("Closed Jira connection")
