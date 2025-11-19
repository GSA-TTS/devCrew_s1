#!/usr/bin/env python3
"""Unit tests for GitHub Python API wrapper.

This module contains tests for the devgru_github_api module, testing
PyGithub-based high-level API with mocked GitHub objects.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest
from github import GithubException, RateLimitExceededException

from devgru_github_api import (GitHubAPIError, IssueManager, PRManager,
                               WorkflowManager, batch_create_issues,
                               get_github_client)


class TestGitHubClient:
    """Test suite for GitHub client initialization."""

    @patch("devgru_github_api.Github")
    @patch("devgru_github_api.Auth.Token")
    @patch("devgru_github_api.os.getenv")
    def test_client_initialization(
        self, mock_getenv: MagicMock, mock_auth: MagicMock, mock_github: MagicMock
    ) -> None:
        """Test GitHub client initialization with token."""
        mock_getenv.return_value = "ghp_testtoken123"
        mock_github_instance = MagicMock()
        mock_github.return_value = mock_github_instance

        client = get_github_client()

        assert client is not None
        mock_auth.assert_called_once_with("ghp_testtoken123")

    @patch("devgru_github_api.os.getenv")
    def test_client_missing_token(self, mock_getenv: MagicMock) -> None:
        """Test error when token is missing."""
        mock_getenv.return_value = None

        with pytest.raises(GitHubAPIError) as exc_info:
            get_github_client()

        assert "GH_TOKEN" in str(exc_info.value)


class TestIssueManager:
    """Test suite for IssueManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_repo = MagicMock()
        self.issue_manager = IssueManager(self.mock_repo)

    def test_create_issue_with_labels(self) -> None:
        """Test creating issue with labels and assignees."""
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        self.mock_repo.create_issue.return_value = mock_issue

        result = self.issue_manager.create_issue(
            title="Test Issue",
            body="Test body",
            labels=["bug", "priority:high"],
            assignees=["user1"],
        )

        assert result.number == 123
        self.mock_repo.create_issue.assert_called_once_with(
            title="Test Issue",
            body="Test body",
            labels=["bug", "priority:high"],
            assignees=["user1"],
        )

    def test_get_issue_by_number(self) -> None:
        """Test retrieving issue by number."""
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.state = "open"
        self.mock_repo.get_issue.return_value = mock_issue

        result = self.issue_manager.get_issue(123)

        assert result.number == 123
        assert result.state == "open"

    def test_update_issue_labels(self) -> None:
        """Test updating issue labels."""
        mock_issue = MagicMock()
        mock_issue.number = 123
        self.mock_repo.get_issue.return_value = mock_issue

        self.issue_manager.update_labels(
            issue_number=123,
            add_labels=["verified"],
            remove_labels=["needs-triage"],
        )

        mock_issue.add_to_labels.assert_called_once_with("verified")
        mock_issue.remove_from_labels.assert_called_once_with("needs-triage")

    def test_close_issue_with_comment(self) -> None:
        """Test closing issue with comment."""
        mock_issue = MagicMock()
        self.mock_repo.get_issue.return_value = mock_issue

        self.issue_manager.close_issue(issue_number=123, comment="Fixed in PR #456")

        mock_issue.edit.assert_called_once_with(state="closed")
        mock_issue.create_comment.assert_called_once_with("Fixed in PR #456")

    def test_search_issues_by_label(self) -> None:
        """Test searching issues by label."""
        mock_issues = [MagicMock(number=1), MagicMock(number=2)]
        self.mock_repo.get_issues.return_value = mock_issues

        results = self.issue_manager.search_issues(
            state="open",
            labels=["bug"],
        )

        assert len(results) == 2
        self.mock_repo.get_issues.assert_called_once_with(
            state="open",
            labels=["bug"],
        )

    def test_link_issue_to_pr(self) -> None:
        """Test linking issue to PR using keywords."""
        mock_issue = MagicMock()
        self.mock_repo.get_issue.return_value = mock_issue

        self.issue_manager.add_comment(
            issue_number=123,
            comment="Fixes #123",
        )

        mock_issue.create_comment.assert_called_once_with("Fixes #123")


class TestPRManager:
    """Test suite for PRManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_repo = MagicMock()
        self.pr_manager = PRManager(self.mock_repo)

    def test_create_pr_with_reviewers(self) -> None:
        """Test creating PR with review requests."""
        mock_pr = MagicMock()
        mock_pr.number = 456
        mock_pr.title = "Feature PR"
        self.mock_repo.create_pull.return_value = mock_pr

        result = self.pr_manager.create_pr(
            title="Feature PR",
            body="PR description",
            base="main",
            head="feature/branch",
            reviewers=["reviewer1", "reviewer2"],
        )

        assert result.number == 456
        mock_pr.create_review_request.assert_called_once_with(
            reviewers=["reviewer1", "reviewer2"]
        )

    def test_create_draft_pr(self) -> None:
        """Test creating draft PR."""
        mock_pr = MagicMock()
        mock_pr.draft = True
        self.mock_repo.create_pull.return_value = mock_pr

        result = self.pr_manager.create_pr(
            title="WIP: Feature",
            body="Work in progress",
            base="main",
            head="feature/wip",
            draft=True,
        )

        assert result.draft is True

    def test_merge_pr_with_squash(self) -> None:
        """Test merging PR with squash strategy."""
        mock_pr = MagicMock()
        mock_pr.mergeable = True
        self.mock_repo.get_pull.return_value = mock_pr

        result = self.pr_manager.merge_pr(
            pr_number=456,
            merge_method="squash",
            delete_branch=True,
        )

        mock_pr.merge.assert_called_once()
        assert result is True

    def test_merge_pr_not_mergeable(self) -> None:
        """Test error when PR is not mergeable."""
        mock_pr = MagicMock()
        mock_pr.mergeable = False
        mock_pr.number = 456
        self.mock_repo.get_pull.return_value = mock_pr

        with pytest.raises(GitHubAPIError) as exc_info:
            self.pr_manager.merge_pr(pr_number=456)

        assert "not mergeable" in str(exc_info.value)

    def test_request_review_changes(self) -> None:
        """Test requesting changes on PR."""
        mock_pr = MagicMock()
        self.mock_repo.get_pull.return_value = mock_pr

        self.pr_manager.create_review(
            pr_number=456,
            body="Please fix linting errors",
            event="REQUEST_CHANGES",
        )

        mock_pr.create_review.assert_called_once_with(
            body="Please fix linting errors",
            event="REQUEST_CHANGES",
        )

    def test_approve_pr(self) -> None:
        """Test approving PR."""
        mock_pr = MagicMock()
        self.mock_repo.get_pull.return_value = mock_pr

        self.pr_manager.create_review(
            pr_number=456,
            body="LGTM!",
            event="APPROVE",
        )

        mock_pr.create_review.assert_called_once_with(
            body="LGTM!",
            event="APPROVE",
        )

    def test_get_pr_reviews(self) -> None:
        """Test getting PR reviews."""
        mock_pr = MagicMock()
        mock_reviews = [
            MagicMock(state="APPROVED", user=MagicMock(login="user1")),
            MagicMock(state="CHANGES_REQUESTED", user=MagicMock(login="user2")),
        ]
        mock_pr.get_reviews.return_value = mock_reviews
        self.mock_repo.get_pull.return_value = mock_pr

        reviews = self.pr_manager.get_reviews(pr_number=456)

        assert len(reviews) == 2
        assert reviews[0].state == "APPROVED"


class TestWorkflowManager:
    """Test suite for WorkflowManager class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_repo = MagicMock()
        self.workflow_manager = WorkflowManager(self.mock_repo)

    def test_trigger_workflow(self) -> None:
        """Test triggering workflow with inputs."""
        mock_workflow = MagicMock()
        self.mock_repo.get_workflow.return_value = mock_workflow

        result = self.workflow_manager.trigger_workflow(
            workflow_name="deploy.yml",
            ref="main",
            inputs={"environment": "production", "version": "v1.2.3"},
        )

        mock_workflow.create_dispatch.assert_called_once_with(
            ref="main",
            inputs={"environment": "production", "version": "v1.2.3"},
        )
        assert result is True

    def test_get_workflow_runs(self) -> None:
        """Test getting workflow runs."""
        mock_workflow = MagicMock()
        mock_runs = [MagicMock(id=123, status="completed", conclusion="success")]
        mock_workflow.get_runs.return_value = mock_runs
        self.mock_repo.get_workflow.return_value = mock_workflow

        runs = self.workflow_manager.get_workflow_runs(workflow_name="deploy.yml")

        assert len(runs) == 1
        assert runs[0].status == "completed"

    def test_download_artifacts(self) -> None:
        """Test downloading workflow artifacts."""
        mock_run = MagicMock()
        mock_run.id = 123
        mock_artifact = MagicMock()
        mock_artifact.name = "test-results"
        mock_artifact.archive_download_url = "http://example.com/artifact"
        mock_run.get_artifacts.return_value = [mock_artifact]

        # Mock get_workflow_runs to return an iterable of runs
        self.mock_repo.get_workflow_runs.return_value = iter([mock_run])

        artifacts = self.workflow_manager.get_artifacts(run_id=123)

        assert len(artifacts) == 1
        assert artifacts[0].name == "test-results"


class TestBatchOperations:
    """Test suite for batch operations."""

    @patch("devgru_github_api.IssueManager")
    def test_batch_create_issues(self, mock_issue_manager_class: MagicMock) -> None:
        """Test batch creating issues."""
        mock_repo = MagicMock()
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager

        mock_issues = [MagicMock(number=i) for i in range(1, 6)]
        mock_issue_manager.create_issue.side_effect = mock_issues

        issues_data = [
            {"title": f"Issue {i}", "body": f"Body {i}", "labels": ["bug"]}
            for i in range(1, 6)
        ]

        results = batch_create_issues(mock_repo, issues_data)

        assert len(results) == 5
        assert mock_issue_manager.create_issue.call_count == 5


class TestErrorHandlingAndRetry:
    """Test suite for error handling and retry logic."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.mock_repo = MagicMock()
        self.issue_manager = IssueManager(self.mock_repo)

    @patch("devgru_github_api.time.sleep")
    @patch("devgru_github_api.time.time")
    def test_retry_on_rate_limit(
        self, mock_time: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Test retry logic on rate limit exceeded."""
        mock_issue = MagicMock()
        mock_issue.number = 123

        # Mock time for rate limit calculation
        mock_time.return_value = 1000
        self.mock_repo._requester.rate_limiting_resettime = 1100

        # First call raises RateLimitExceededException, second succeeds
        self.mock_repo.create_issue.side_effect = [
            RateLimitExceededException(
                status=403, data={"message": "Rate limit exceeded"}
            ),
            mock_issue,
        ]

        result = self.issue_manager.create_issue_with_retry(
            title="Test",
            body="Body",
        )

        assert result.number == 123
        assert self.mock_repo.create_issue.call_count == 2
        mock_sleep.assert_called_once()

    @patch("devgru_github_api.time.sleep")
    def test_retry_on_server_error(self, mock_sleep: MagicMock) -> None:
        """Test retry on server errors (502, 503, 504)."""
        mock_issue = MagicMock()
        mock_issue.number = 123

        self.mock_repo.create_issue.side_effect = [
            GithubException(status=502, data={"message": "Bad Gateway"}),
            GithubException(status=503, data={"message": "Service Unavailable"}),
            mock_issue,
        ]

        result = self.issue_manager.create_issue_with_retry(
            title="Test",
            body="Body",
        )

        assert result.number == 123
        assert self.mock_repo.create_issue.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("devgru_github_api.time.sleep")
    def test_max_retries_exceeded(self, mock_sleep: MagicMock) -> None:
        """Test failure after max retries."""
        # Permanent error (not 502/503/504)
        self.mock_repo.create_issue.side_effect = GithubException(
            status=500,
            data={"message": "Internal Server Error"},
        )

        with pytest.raises(GitHubAPIError):
            self.issue_manager.create_issue_with_retry(
                title="Test",
                body="Body",
                max_retries=3,
            )

        # Should fail on first attempt for non-retryable status code
        assert self.mock_repo.create_issue.call_count == 1
