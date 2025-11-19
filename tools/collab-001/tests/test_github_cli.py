#!/usr/bin/env python3
"""Unit tests for GitHub CLI wrapper functions.

This module contains tests for the devgru_github_cli module, testing
CLI command wrappers with mocked subprocess calls.
"""

import json
import subprocess
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from devgru_github_cli import (GHCLIError, close_issue, create_issue,
                               create_pr, get_issue, merge_pr, read_issue,
                               trigger_workflow, update_issue)


class TestIssueOperations:
    """Test suite for GitHub issue operations."""

    @patch("devgru_github_cli.subprocess.run")
    def test_create_issue_success(self, mock_run: MagicMock) -> None:
        """Test successful issue creation."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "issue", "create"],
            returncode=0,
            stdout='{"number": 123, "title": "Test Issue"}',
            stderr="",
        )

        result = create_issue(
            title="Test Issue",
            body="Test body",
            labels=["bug", "priority:high"],
            assignees=["user1"],
        )

        assert result["number"] == 123
        assert result["title"] == "Test Issue"
        mock_run.assert_called_once()

    @patch("devgru_github_cli.subprocess.run")
    def test_create_issue_with_retry(self, mock_run: MagicMock) -> None:
        """Test issue creation with retry on transient error."""
        # First two calls fail with 502, third succeeds
        mock_run.side_effect = [
            subprocess.CompletedProcess(
                args=["gh"], returncode=1, stdout="", stderr="502 Bad Gateway"
            ),
            subprocess.CompletedProcess(
                args=["gh"], returncode=1, stdout="", stderr="503 Service Unavailable"
            ),
            subprocess.CompletedProcess(
                args=["gh"],
                returncode=0,
                stdout='{"number": 123, "title": "Test"}',
                stderr="",
            ),
        ]

        result = create_issue(title="Test", body="Body")
        assert result["number"] == 123
        assert mock_run.call_count == 3

    @patch("devgru_github_cli.subprocess.run")
    def test_create_issue_permanent_failure(self, mock_run: MagicMock) -> None:
        """Test issue creation fails after max retries."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh"], returncode=1, stdout="", stderr="Authentication failed"
        )

        with pytest.raises(GHCLIError) as exc_info:
            create_issue(title="Test", body="Body")

        assert "Authentication failed" in str(exc_info.value)
        assert mock_run.call_count == 3

    @patch("devgru_github_cli.subprocess.run")
    def test_read_issue_success(self, mock_run: MagicMock) -> None:
        """Test successful issue reading."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "issue", "view"],
            returncode=0,
            stdout='{"number": 123, "title": "Test", "state": "open", "labels": ["bug"]}',
            stderr="",
        )

        result = read_issue(123)
        assert result["number"] == 123
        assert result["state"] == "open"
        assert "bug" in result["labels"]

    @patch("devgru_github_cli.subprocess.run")
    def test_update_issue_labels(self, mock_run: MagicMock) -> None:
        """Test updating issue labels."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "issue", "edit"],
            returncode=0,
            stdout='{"number": 123, "labels": ["bug", "verified"]}',
            stderr="",
        )

        result = update_issue(
            issue_number=123, add_labels=["verified"], remove_labels=["needs-triage"]
        )
        assert "verified" in result["labels"]

    @patch("devgru_github_cli.subprocess.run")
    def test_close_issue_with_comment(self, mock_run: MagicMock) -> None:
        """Test closing issue with comment."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "issue", "close"],
            returncode=0,
            stdout='{"number": 123, "state": "closed"}',
            stderr="",
        )

        result = close_issue(issue_number=123, comment="Fixed in PR #456")
        assert result["state"] == "closed"


class TestPROperations:
    """Test suite for GitHub pull request operations."""

    @patch("devgru_github_cli.subprocess.run")
    def test_create_pr_success(self, mock_run: MagicMock) -> None:
        """Test successful PR creation."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "pr", "create"],
            returncode=0,
            stdout='{"number": 456, "title": "Feature PR"}',
            stderr="",
        )

        result = create_pr(
            title="Feature PR",
            body="PR body",
            base="main",
            head="feature/branch",
            reviewers=["reviewer1"],
        )

        assert result["number"] == 456
        assert result["title"] == "Feature PR"

    @patch("devgru_github_cli.subprocess.run")
    def test_create_pr_draft(self, mock_run: MagicMock) -> None:
        """Test creating draft PR."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "pr", "create"],
            returncode=0,
            stdout='{"number": 456, "draft": true}',
            stderr="",
        )

        result = create_pr(
            title="WIP: Feature",
            body="Work in progress",
            base="main",
            head="feature/wip",
            draft=True,
        )

        assert result["draft"] is True

    @patch("devgru_github_cli.subprocess.run")
    def test_merge_pr_squash(self, mock_run: MagicMock) -> None:
        """Test merging PR with squash strategy."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "pr", "merge"],
            returncode=0,
            stdout='{"number": 456, "merged": true}',
            stderr="",
        )

        result = merge_pr(pr_number=456, merge_method="squash", delete_branch=True)
        assert result["merged"] is True


class TestWorkflowOperations:
    """Test suite for GitHub Actions workflow operations."""

    @patch("devgru_github_cli.subprocess.run")
    def test_trigger_workflow_success(self, mock_run: MagicMock) -> None:
        """Test successful workflow triggering."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "workflow", "run"],
            returncode=0,
            stdout='{"id": 123456, "status": "queued"}',
            stderr="",
        )

        result = trigger_workflow(
            workflow_name="deploy.yml",
            ref="main",
            inputs={"environment": "production", "version": "v1.2.3"},
        )

        assert result["status"] == "queued"

    @patch("devgru_github_cli.subprocess.run")
    def test_trigger_workflow_with_invalid_inputs(self, mock_run: MagicMock) -> None:
        """Test workflow trigger with invalid inputs."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh"],
            returncode=1,
            stdout="",
            stderr="Invalid workflow inputs",
        )

        with pytest.raises(GHCLIError):
            trigger_workflow(
                workflow_name="deploy.yml", ref="main", inputs={"invalid": "value"}
            )


class TestErrorHandling:
    """Test suite for error handling and retry logic."""

    @patch("devgru_github_cli.subprocess.run")
    @patch("devgru_github_cli.time.sleep")
    def test_exponential_backoff(
        self, mock_sleep: MagicMock, mock_run: MagicMock
    ) -> None:
        """Test exponential backoff on retries."""
        mock_run.side_effect = [
            subprocess.CompletedProcess(
                args=["gh"], returncode=1, stdout="", stderr="502 Bad Gateway"
            ),
            subprocess.CompletedProcess(
                args=["gh"], returncode=1, stdout="", stderr="503 Service Unavailable"
            ),
            subprocess.CompletedProcess(
                args=["gh"],
                returncode=0,
                stdout='{"number": 123}',
                stderr="",
            ),
        ]

        result = create_issue(title="Test", body="Body")
        assert result["number"] == 123

        # Check exponential backoff: 2^0=1, 2^1=2
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @patch("devgru_github_cli.subprocess.run")
    def test_json_parse_error(self, mock_run: MagicMock) -> None:
        """Test handling of invalid JSON responses."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh"], returncode=0, stdout="Invalid JSON", stderr=""
        )

        with pytest.raises(GHCLIError) as exc_info:
            create_issue(title="Test", body="Body")

        assert "JSON parsing failed" in str(exc_info.value)


class TestAuthenticationManagement:
    """Test suite for GitHub authentication."""

    @patch("devgru_github_cli.subprocess.run")
    @patch("devgru_github_cli.os.getenv")
    def test_authentication_token_from_env(
        self, mock_getenv: MagicMock, mock_run: MagicMock
    ) -> None:
        """Test authentication using environment variable."""
        mock_getenv.return_value = "ghp_testtoken123"
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh"], returncode=0, stdout='{"login": "testuser"}', stderr=""
        )

        # Token should be loaded from environment
        from devgru_github_cli import get_auth_token

        token = get_auth_token()
        assert token == "ghp_testtoken123"

    @patch("devgru_github_cli.subprocess.run")
    @patch("devgru_github_cli.os.getenv")
    def test_authentication_missing_token(
        self, mock_getenv: MagicMock, mock_run: MagicMock
    ) -> None:
        """Test error when authentication token is missing."""
        mock_getenv.return_value = None

        from devgru_github_cli import get_auth_token

        with pytest.raises(GHCLIError) as exc_info:
            get_auth_token()

        assert "GH_TOKEN" in str(exc_info.value)
