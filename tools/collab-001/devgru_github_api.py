#!/usr/bin/env python3
"""GitHub Python API wrapper using PyGithub.

This module provides high-level API for protocol integration
(GH-1, P-FEATURE-DEV, P-TDD) using PyGithub library.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

from github import Auth, Github, GithubException, RateLimitExceededException
from github.Issue import Issue
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Workflow import Workflow
from github.WorkflowRun import WorkflowRun

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format=(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"message": "%(message)s"}'
    ),
)
logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Exception raised for GitHub API errors."""

    pass


def get_github_client() -> Github:
    """Initialize and return GitHub client.

    Returns:
        Github: Authenticated GitHub client

    Raises:
        GitHubAPIError: If authentication token is not found
    """
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubAPIError(
            "GitHub token not found. Set GH_TOKEN or GITHUB_TOKEN environment variable."
        )

    auth = Auth.Token(token)
    client = Github(auth=auth)

    logger.info("GitHub client initialized successfully")
    return client


class IssueManager:
    """Manager class for GitHub issue operations."""

    def __init__(self, repo: Repository):
        """Initialize IssueManager.

        Args:
            repo: GitHub Repository object
        """
        self.repo = repo
        logger.info(f"IssueManager initialized for repo: {repo.full_name}")

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[int] = None,
    ) -> Issue:
        """Create a new issue.

        Args:
            title: Issue title
            body: Issue description
            labels: List of label names
            assignees: List of usernames to assign
            milestone: Milestone number

        Returns:
            Issue: Created issue object

        Raises:
            GitHubAPIError: If issue creation fails
        """
        try:
            logger.info(f"Creating issue: {title}")

            kwargs: Dict[str, Any] = {
                "title": title,
                "body": body,
            }

            if labels:
                kwargs["labels"] = labels

            if assignees:
                kwargs["assignees"] = assignees

            if milestone:
                kwargs["milestone"] = self.repo.get_milestone(milestone)

            issue = self.repo.create_issue(**kwargs)
            logger.info(f"Issue created successfully: #{issue.number}")
            return issue

        except GithubException as e:
            raise GitHubAPIError(f"Failed to create issue: {e.status} - {e.data}")

    def create_issue_with_retry(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        max_retries: int = 3,
    ) -> Issue:
        """Create issue with automatic retry on rate limit or server errors.

        Args:
            title: Issue title
            body: Issue description
            labels: List of label names
            assignees: List of usernames
            max_retries: Maximum retry attempts

        Returns:
            Issue: Created issue object

        Raises:
            GitHubAPIError: If creation fails after all retries
        """
        last_exception = None
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Creating issue (attempt {attempt + 1}/{max_retries}): {title}"
                )

                kwargs: Dict[str, Any] = {
                    "title": title,
                    "body": body,
                }

                if labels:
                    kwargs["labels"] = labels

                if assignees:
                    kwargs["assignees"] = assignees

                issue = self.repo.create_issue(**kwargs)
                logger.info(f"Issue created successfully: #{issue.number}")
                return issue

            except RateLimitExceededException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    reset_time = self.repo._requester.rate_limiting_resettime
                    wait_time = max(reset_time - time.time(), 0) + 10
                    logger.warning(f"Rate limit exceeded. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise GitHubAPIError(f"Rate limit exceeded: {e}")
            except GithubException as e:
                last_exception = e
                if e.status in [502, 503, 504] and attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        f"Server error {e.status}. Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    raise GitHubAPIError(
                        f"Failed to create issue: {e.status} - {e.data}"
                    )

        raise GitHubAPIError(f"Max retries exceeded. Last error: {last_exception}")

    def get_issue(self, issue_number: int) -> Issue:
        """Get issue by number.

        Args:
            issue_number: Issue number

        Returns:
            Issue: Issue object

        Raises:
            GitHubAPIError: If issue not found
        """
        try:
            logger.info(f"Fetching issue #{issue_number}")
            return self.repo.get_issue(issue_number)
        except GithubException as e:
            raise GitHubAPIError(f"Failed to get issue: {e.status} - {e.data}")

    def update_labels(
        self,
        issue_number: int,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None,
    ) -> None:
        """Update issue labels.

        Args:
            issue_number: Issue number
            add_labels: Labels to add
            remove_labels: Labels to remove

        Raises:
            GitHubAPIError: If update fails
        """
        try:
            issue = self.get_issue(issue_number)

            if add_labels:
                for label in add_labels:
                    issue.add_to_labels(label)
                logger.info(f"Added labels {add_labels} to issue #{issue_number}")

            if remove_labels:
                for label in remove_labels:
                    issue.remove_from_labels(label)
                logger.info(
                    f"Removed labels {remove_labels} from issue #{issue_number}"
                )

        except GithubException as e:
            raise GitHubAPIError(f"Failed to update labels: {e.status} - {e.data}")

    def add_comment(self, issue_number: int, comment: str) -> None:
        """Add comment to issue.

        Args:
            issue_number: Issue number
            comment: Comment text (supports markdown)

        Raises:
            GitHubAPIError: If comment creation fails
        """
        try:
            issue = self.get_issue(issue_number)
            issue.create_comment(comment)
            logger.info(f"Added comment to issue #{issue_number}")
        except GithubException as e:
            raise GitHubAPIError(f"Failed to add comment: {e.status} - {e.data}")

    def close_issue(self, issue_number: int, comment: Optional[str] = None) -> None:
        """Close an issue.

        Args:
            issue_number: Issue number
            comment: Optional closing comment

        Raises:
            GitHubAPIError: If close fails
        """
        try:
            issue = self.get_issue(issue_number)

            if comment:
                issue.create_comment(comment)

            issue.edit(state="closed")
            logger.info(f"Closed issue #{issue_number}")

        except GithubException as e:
            raise GitHubAPIError(f"Failed to close issue: {e.status} - {e.data}")

    def search_issues(
        self,
        state: str = "open",
        labels: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        milestone: Optional[str] = None,
    ) -> List[Issue]:
        """Search issues with filters.

        Args:
            state: Issue state ('open', 'closed', 'all')
            labels: Filter by labels
            assignee: Filter by assignee
            milestone: Filter by milestone

        Returns:
            List[Issue]: List of matching issues

        Raises:
            GitHubAPIError: If search fails
        """
        try:
            kwargs: Dict[str, Any] = {"state": state}

            if labels:
                kwargs["labels"] = labels

            if assignee:
                kwargs["assignee"] = assignee

            if milestone:
                kwargs["milestone"] = milestone

            issues = self.repo.get_issues(**kwargs)
            return list(issues)

        except GithubException as e:
            raise GitHubAPIError(f"Failed to search issues: {e.status} - {e.data}")


class PRManager:
    """Manager class for GitHub pull request operations."""

    def __init__(self, repo: Repository):
        """Initialize PRManager.

        Args:
            repo: GitHub Repository object
        """
        self.repo = repo
        logger.info(f"PRManager initialized for repo: {repo.full_name}")

    def create_pr(
        self,
        title: str,
        body: str,
        base: str,
        head: str,
        reviewers: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        draft: bool = False,
    ) -> PullRequest:
        """Create a pull request.

        Args:
            title: PR title
            body: PR description
            base: Base branch
            head: Head branch
            reviewers: List of reviewer usernames
            labels: List of labels
            draft: Create as draft PR

        Returns:
            PullRequest: Created PR object

        Raises:
            GitHubAPIError: If PR creation fails
        """
        try:
            logger.info(f"Creating PR: {title}")

            pr = self.repo.create_pull(
                title=title,
                body=body,
                base=base,
                head=head,
                draft=draft,
            )

            if reviewers:
                pr.create_review_request(reviewers=reviewers)
                logger.info(f"Requested reviews from: {reviewers}")

            if labels:
                pr.add_to_labels(*labels)
                logger.info(f"Added labels: {labels}")

            logger.info(f"PR created successfully: #{pr.number}")
            return pr

        except GithubException as e:
            raise GitHubAPIError(f"Failed to create PR: {e.status} - {e.data}")

    def merge_pr(
        self,
        pr_number: int,
        merge_method: str = "merge",
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
        delete_branch: bool = False,
    ) -> bool:
        """Merge a pull request.

        Args:
            pr_number: PR number
            merge_method: Merge method ('merge', 'squash', 'rebase')
            commit_title: Custom commit title
            commit_message: Custom commit message
            delete_branch: Delete head branch after merge

        Returns:
            bool: True if merged successfully

        Raises:
            GitHubAPIError: If merge fails or PR not mergeable
        """
        try:
            pr = self.repo.get_pull(pr_number)

            if not pr.mergeable:
                raise GitHubAPIError(f"PR #{pr_number} is not mergeable")

            logger.info(f"Merging PR #{pr_number} with method: {merge_method}")

            pr.merge(
                merge_method=merge_method,
                commit_title=commit_title,
                commit_message=commit_message,
            )

            if delete_branch:
                # Delete head branch reference
                ref = f"heads/{pr.head.ref}"
                self.repo.get_git_ref(ref).delete()
                logger.info(f"Deleted head branch: {pr.head.ref}")

            logger.info(f"PR #{pr_number} merged successfully")
            return True

        except GithubException as e:
            raise GitHubAPIError(f"Failed to merge PR: {e.status} - {e.data}")

    def create_review(
        self,
        pr_number: int,
        body: str,
        event: str = "COMMENT",
    ) -> None:
        """Create a review on PR.

        Args:
            pr_number: PR number
            body: Review comment
            event: Review event ('APPROVE', 'REQUEST_CHANGES', 'COMMENT')

        Raises:
            GitHubAPIError: If review creation fails
        """
        try:
            pr = self.repo.get_pull(pr_number)
            pr.create_review(body=body, event=event)
            logger.info(f"Created {event} review on PR #{pr_number}")

        except GithubException as e:
            raise GitHubAPIError(f"Failed to create review: {e.status} - {e.data}")

    def get_reviews(self, pr_number: int) -> List[Any]:
        """Get all reviews for a PR.

        Args:
            pr_number: PR number

        Returns:
            List of review objects

        Raises:
            GitHubAPIError: If fetching reviews fails
        """
        try:
            pr = self.repo.get_pull(pr_number)
            return list(pr.get_reviews())

        except GithubException as e:
            raise GitHubAPIError(f"Failed to get reviews: {e.status} - {e.data}")

    def add_comment(self, pr_number: int, comment: str) -> None:
        """Add comment to PR.

        Args:
            pr_number: PR number
            comment: Comment text

        Raises:
            GitHubAPIError: If comment creation fails
        """
        try:
            pr = self.repo.get_pull(pr_number)
            pr.create_issue_comment(comment)
            logger.info(f"Added comment to PR #{pr_number}")

        except GithubException as e:
            raise GitHubAPIError(f"Failed to add comment: {e.status} - {e.data}")


class WorkflowManager:
    """Manager class for GitHub Actions workflow operations."""

    def __init__(self, repo: Repository):
        """Initialize WorkflowManager.

        Args:
            repo: GitHub Repository object
        """
        self.repo = repo
        logger.info(f"WorkflowManager initialized for repo: {repo.full_name}")

    def trigger_workflow(
        self,
        workflow_name: str,
        ref: str,
        inputs: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Trigger a workflow dispatch event.

        Args:
            workflow_name: Workflow file name (e.g., 'deploy.yml')
            ref: Git ref to run on (branch, tag)
            inputs: Workflow input parameters

        Returns:
            bool: True if triggered successfully

        Raises:
            GitHubAPIError: If trigger fails
        """
        try:
            workflow = self.repo.get_workflow(workflow_name)

            logger.info(f"Triggering workflow: {workflow_name} on ref: {ref}")

            workflow.create_dispatch(ref=ref, inputs=inputs or {})

            logger.info(f"Workflow {workflow_name} triggered successfully")
            return True

        except GithubException as e:
            raise GitHubAPIError(f"Failed to trigger workflow: {e.status} - {e.data}")

    def get_workflow_runs(
        self,
        workflow_name: str,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[WorkflowRun]:
        """Get workflow runs.

        Args:
            workflow_name: Workflow file name
            status: Filter by status ('queued', 'in_progress', 'completed')
            limit: Maximum number of runs to return

        Returns:
            List of workflow run objects

        Raises:
            GitHubAPIError: If fetching runs fails
        """
        try:
            workflow = self.repo.get_workflow(workflow_name)

            kwargs: Dict[str, Any] = {}
            if status:
                kwargs["status"] = status

            runs = workflow.get_runs(**kwargs)
            return list(runs[:limit])

        except GithubException as e:
            raise GitHubAPIError(f"Failed to get workflow runs: {e.status} - {e.data}")

    def get_artifacts(self, run_id: int) -> List[Any]:
        """Get artifacts for a workflow run.

        Args:
            run_id: Workflow run ID

        Returns:
            List of artifact objects

        Raises:
            GitHubAPIError: If fetching artifacts fails
        """
        try:
            # Get workflow run from repository
            runs = self.repo.get_workflow_runs()
            run = None
            for r in runs:
                if r.id == run_id:
                    run = r
                    break

            if not run:
                raise GitHubAPIError(f"Workflow run {run_id} not found")

            return list(run.get_artifacts())

        except GithubException as e:
            raise GitHubAPIError(f"Failed to get artifacts: {e.status} - {e.data}")

    def list_workflows(self) -> List[Workflow]:
        """List all workflows in repository.

        Returns:
            List of workflow objects

        Raises:
            GitHubAPIError: If listing fails
        """
        try:
            workflows = self.repo.get_workflows()
            return list(workflows)

        except GithubException as e:
            raise GitHubAPIError(f"Failed to list workflows: {e.status} - {e.data}")


def batch_create_issues(
    repo: Repository,
    issues_data: List[Dict[str, Any]],
) -> List[Issue]:
    """Batch create multiple issues.

    Args:
        repo: GitHub Repository object
        issues_data: List of dicts with issue parameters

    Returns:
        List of created Issue objects

    Raises:
        GitHubAPIError: If batch creation fails
    """
    issue_manager = IssueManager(repo)
    created_issues = []

    for issue_data in issues_data:
        try:
            issue = issue_manager.create_issue(**issue_data)
            created_issues.append(issue)
        except GitHubAPIError as e:
            logger.error(f"Failed to create issue: {e}")
            # Continue with remaining issues

    logger.info(f"Batch created {len(created_issues)}/{len(issues_data)} issues")
    return created_issues
