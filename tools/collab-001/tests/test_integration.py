#!/usr/bin/env python3
"""Integration tests for GitHub integration tool.

These tests require actual GitHub access and should be run with
appropriate credentials. Mark as integration tests to skip in CI.
"""

import os
from typing import Any, Dict

import pytest

from devgru_github_api import (IssueManager, PRManager, WorkflowManager,
                               get_github_client)
from devgru_github_cli import (create_issue, get_auth_token, read_issue,
                               trigger_workflow)


@pytest.mark.integration
class TestGitHubCLIIntegration:
    """Integration tests for GitHub CLI wrapper."""

    @pytest.fixture(autouse=True)
    def skip_if_no_token(self) -> None:
        """Skip tests if GH_TOKEN is not set."""
        if not os.getenv("GH_TOKEN"):
            pytest.skip("GH_TOKEN environment variable not set")

    def test_authentication(self) -> None:
        """Test GitHub authentication."""
        token = get_auth_token()
        assert token is not None
        assert token.startswith("ghp_") or token.startswith("gho_")

    @pytest.mark.skip(reason="Creates real issues - run manually only")
    def test_create_and_close_issue(self) -> None:
        """Test creating and closing an issue (manual test only)."""
        # Create issue
        issue = create_issue(
            title="[TEST] Integration test issue",
            body="This is a test issue created by integration tests. Please ignore and close.",
            labels=["test"],
        )

        assert issue["number"] > 0
        assert issue["title"] == "[TEST] Integration test issue"

        # Read issue
        read_result = read_issue(issue["number"])
        assert read_result["number"] == issue["number"]

        # Note: Cleanup should be done manually to avoid polluting repository


@pytest.mark.integration
class TestGitHubAPIIntegration:
    """Integration tests for GitHub Python API."""

    @pytest.fixture(autouse=True)
    def skip_if_no_token(self) -> None:
        """Skip tests if GH_TOKEN is not set."""
        if not os.getenv("GH_TOKEN"):
            pytest.skip("GH_TOKEN environment variable not set")

    @pytest.fixture
    def github_client(self) -> Any:
        """Get GitHub client."""
        return get_github_client()

    @pytest.fixture
    def test_repo(self, github_client: Any) -> Any:
        """Get test repository (configure as needed)."""
        # Update with actual test repository
        repo_name = os.getenv("GITHUB_TEST_REPO", "owner/repo")
        return github_client.get_repo(repo_name)

    def test_client_initialization(self, github_client: Any) -> None:
        """Test GitHub client initialization."""
        user = github_client.get_user()
        assert user.login is not None

    def test_repository_access(self, test_repo: Any) -> None:
        """Test repository access."""
        assert test_repo.full_name is not None
        assert test_repo.default_branch in ["main", "master"]

    @pytest.mark.skip(reason="Creates real issues - run manually only")
    def test_issue_manager_workflow(self, test_repo: Any) -> None:
        """Test complete issue management workflow (manual test only)."""
        issue_manager = IssueManager(test_repo)

        # Create issue
        issue = issue_manager.create_issue(
            title="[TEST] API integration test",
            body="Test issue created via PyGithub API",
            labels=["test"],
        )

        assert issue.number > 0

        # Update labels
        issue_manager.update_labels(
            issue_number=issue.number,
            add_labels=["verified"],
        )

        # Add comment
        issue_manager.add_comment(
            issue_number=issue.number,
            comment="Test comment from integration test",
        )

        # Note: Cleanup should be done manually

    def test_workflow_listing(self, test_repo: Any) -> None:
        """Test listing workflows."""
        workflow_manager = WorkflowManager(test_repo)
        workflows = workflow_manager.list_workflows()

        assert isinstance(workflows, list)
        # May be empty if no workflows configured

    @pytest.mark.skip(reason="Triggers real workflows - run manually only")
    def test_workflow_trigger(self, test_repo: Any) -> None:
        """Test triggering workflow (manual test only)."""
        workflow_manager = WorkflowManager(test_repo)

        # Note: Requires workflow_dispatch configured workflow
        result = workflow_manager.trigger_workflow(
            workflow_name="test.yml",
            ref="main",
            inputs={"test": "true"},
        )

        # Workflow should be triggered successfully
        assert result is True


@pytest.mark.integration
class TestProtocolIntegration:
    """Integration tests for protocol workflows (GH-1, P-TDD, etc)."""

    @pytest.fixture(autouse=True)
    def skip_if_no_token(self) -> None:
        """Skip tests if GH_TOKEN is not set."""
        if not os.getenv("GH_TOKEN"):
            pytest.skip("GH_TOKEN environment variable not set")

    @pytest.mark.skip(reason="End-to-end test - run manually only")
    def test_gh1_protocol_simulation(self) -> None:
        """Test GH-1 protocol workflow simulation."""
        # This would test the complete GH-1 protocol:
        # 1. Create issue branch
        # 2. Read issue details
        # 3. Create implementation plan
        # 4. Post comment on issue

        # Implementation would go here for manual testing
        pass

    @pytest.mark.skip(reason="End-to-end test - run manually only")
    def test_p_tdd_protocol_simulation(self) -> None:
        """Test P-TDD protocol workflow simulation."""
        # This would test the TDD workflow:
        # 1. Create PR
        # 2. Post test coverage report
        # 3. Check status checks
        # 4. Merge on approval

        # Implementation would go here for manual testing
        pass


@pytest.mark.integration
class TestRateLimitHandling:
    """Integration tests for rate limit handling."""

    @pytest.fixture(autouse=True)
    def skip_if_no_token(self) -> None:
        """Skip tests if GH_TOKEN is not set."""
        if not os.getenv("GH_TOKEN"):
            pytest.skip("GH_TOKEN environment variable not set")

    def test_rate_limit_check(self) -> None:
        """Test checking rate limit status."""
        client = get_github_client()
        rate_limit = client.get_rate_limit()

        assert rate_limit.core.limit > 0
        assert rate_limit.core.remaining >= 0
        assert rate_limit.search.limit > 0

    def test_rate_limit_monitoring(self) -> None:
        """Test rate limit monitoring during operations."""
        client = get_github_client()
        initial_limit = client.get_rate_limit()

        # Perform some operations
        user = client.get_user()
        _ = user.login

        final_limit = client.get_rate_limit()

        # Remaining should have decreased
        assert final_limit.core.remaining <= initial_limit.core.remaining
