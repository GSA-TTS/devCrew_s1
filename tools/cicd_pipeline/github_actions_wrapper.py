"""
GitHub Actions API Wrapper
Issue #36 - TOOL-CICD-001

Provides a clean interface to GitHub Actions API for workflow management,
artifact handling, and job log retrieval.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
from github import Github, GithubException
from github.Repository import Repository
from github.Workflow import Workflow
from github.WorkflowRun import WorkflowRun

logger = logging.getLogger(__name__)


class GitHubActionsError(Exception):
    """Base exception for GitHub Actions operations."""

    pass


class WorkflowNotFoundError(GitHubActionsError):
    """Raised when workflow is not found."""

    pass


class WorkflowRunError(GitHubActionsError):
    """Raised when workflow run fails."""

    pass


class GitHubActionsWrapper:
    """
    Wrapper for GitHub Actions API operations.

    Provides methods for workflow management, artifact operations,
    and job log retrieval with error handling and retry logic.
    """

    def __init__(
        self,
        token: str,
        repo_owner: str,
        repo_name: str,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize GitHub Actions wrapper.

        Args:
            token: GitHub personal access token
            repo_owner: Repository owner/organization
            repo_name: Repository name
            timeout: API request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.timeout = timeout
        self.max_retries = max_retries

        # Initialize GitHub API client
        self.github = Github(token, timeout=timeout)
        self.repo: Repository = self.github.get_repo(f"{repo_owner}/{repo_name}")

        logger.info(
            f"Initialized GitHub Actions wrapper for {repo_owner}/{repo_name}"
        )

    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List all workflows in the repository.

        Returns:
            List of workflow dictionaries with id, name, path, state

        Raises:
            GitHubActionsError: If API call fails
        """
        try:
            workflows = self.repo.get_workflows()
            return [
                {
                    "id": wf.id,
                    "name": wf.name,
                    "path": wf.path,
                    "state": wf.state,
                    "created_at": wf.created_at,
                    "updated_at": wf.updated_at,
                }
                for wf in workflows
            ]
        except GithubException as e:
            logger.error(f"Failed to list workflows: {e}")
            raise GitHubActionsError(f"Failed to list workflows: {e}")

    def get_workflow(self, workflow_id: str) -> Workflow:
        """
        Get workflow by ID or filename.

        Args:
            workflow_id: Workflow ID or filename (e.g., 'main.yml')

        Returns:
            Workflow object

        Raises:
            WorkflowNotFoundError: If workflow not found
        """
        try:
            if workflow_id.isdigit():
                return self.repo.get_workflow(int(workflow_id))
            else:
                # Search by filename
                workflows = self.repo.get_workflows()
                for wf in workflows:
                    if wf.path.endswith(workflow_id):
                        return wf
                raise WorkflowNotFoundError(f"Workflow '{workflow_id}' not found")
        except GithubException as e:
            logger.error(f"Failed to get workflow: {e}")
            raise WorkflowNotFoundError(f"Workflow '{workflow_id}' not found: {e}")

    def trigger_workflow(
        self,
        workflow_id: str,
        ref: str = "main",
        inputs: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Trigger a workflow run.

        Args:
            workflow_id: Workflow ID or filename
            ref: Git reference (branch, tag, or commit SHA)
            inputs: Workflow input parameters

        Returns:
            True if workflow was triggered successfully

        Raises:
            WorkflowRunError: If workflow trigger fails
        """
        try:
            workflow = self.get_workflow(workflow_id)
            result = workflow.create_dispatch(ref=ref, inputs=inputs or {})

            if result:
                logger.info(f"Triggered workflow '{workflow_id}' on ref '{ref}'")
                return True
            else:
                raise WorkflowRunError(f"Failed to trigger workflow '{workflow_id}'")

        except GithubException as e:
            logger.error(f"Failed to trigger workflow: {e}")
            raise WorkflowRunError(f"Failed to trigger workflow: {e}")

    def list_workflow_runs(
        self,
        workflow_id: Optional[str] = None,
        branch: Optional[str] = None,
        event: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        List workflow runs with optional filters.

        Args:
            workflow_id: Filter by workflow ID or filename
            branch: Filter by branch name
            event: Filter by event type (push, pull_request, etc.)
            status: Filter by status (queued, in_progress, completed)
            limit: Maximum number of runs to return

        Returns:
            List of workflow run dictionaries
        """
        try:
            if workflow_id:
                workflow = self.get_workflow(workflow_id)
                runs = workflow.get_runs(
                    branch=branch, event=event, status=status
                )[:limit]
            else:
                runs = self.repo.get_workflow_runs(
                    branch=branch, event=event, status=status
                )[:limit]

            return [self._workflow_run_to_dict(run) for run in runs]

        except GithubException as e:
            logger.error(f"Failed to list workflow runs: {e}")
            raise GitHubActionsError(f"Failed to list workflow runs: {e}")

    def get_workflow_run(self, run_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a workflow run.

        Args:
            run_id: Workflow run ID

        Returns:
            Workflow run dictionary with status, jobs, artifacts

        Raises:
            GitHubActionsError: If run not found
        """
        try:
            run = self.repo.get_workflow_run(run_id)
            return self._workflow_run_to_dict(run)

        except GithubException as e:
            logger.error(f"Failed to get workflow run: {e}")
            raise GitHubActionsError(f"Failed to get workflow run: {e}")

    def cancel_workflow_run(self, run_id: int) -> bool:
        """
        Cancel a running workflow.

        Args:
            run_id: Workflow run ID

        Returns:
            True if cancellation was successful

        Raises:
            WorkflowRunError: If cancellation fails
        """
        try:
            run = self.repo.get_workflow_run(run_id)
            result = run.cancel()

            if result:
                logger.info(f"Cancelled workflow run {run_id}")
                return True
            else:
                raise WorkflowRunError(f"Failed to cancel workflow run {run_id}")

        except GithubException as e:
            logger.error(f"Failed to cancel workflow run: {e}")
            raise WorkflowRunError(f"Failed to cancel workflow run: {e}")

    def wait_for_workflow_run(
        self,
        run_id: int,
        poll_interval: int = 10,
        max_wait_time: int = 1800,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Wait for workflow run to complete.

        Args:
            run_id: Workflow run ID
            poll_interval: Polling interval in seconds
            max_wait_time: Maximum wait time in seconds

        Returns:
            Tuple of (conclusion, run_info)
            conclusion: success, failure, cancelled, skipped, timed_out

        Raises:
            WorkflowRunError: If timeout or API error
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                raise WorkflowRunError(
                    f"Timeout waiting for workflow run {run_id} "
                    f"after {max_wait_time}s"
                )

            run_info = self.get_workflow_run(run_id)

            if run_info["status"] == "completed":
                conclusion = run_info["conclusion"]
                logger.info(
                    f"Workflow run {run_id} completed with "
                    f"conclusion: {conclusion}"
                )
                return conclusion, run_info

            logger.debug(
                f"Workflow run {run_id} status: {run_info['status']}, "
                f"elapsed: {elapsed:.0f}s"
            )
            time.sleep(poll_interval)

    def get_workflow_run_logs(self, run_id: int) -> str:
        """
        Download workflow run logs.

        Args:
            run_id: Workflow run ID

        Returns:
            Log content as string

        Raises:
            GitHubActionsError: If log retrieval fails
        """
        try:
            run = self.repo.get_workflow_run(run_id)
            # Get log URL
            log_url = run.logs_url

            # Download logs
            headers = {"Authorization": f"token {self.token}"}
            response = requests.get(log_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            logger.info(f"Retrieved logs for workflow run {run_id}")
            return response.text

        except (GithubException, requests.RequestException) as e:
            logger.error(f"Failed to get workflow run logs: {e}")
            raise GitHubActionsError(f"Failed to get workflow run logs: {e}")

    def list_artifacts(
        self, run_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List artifacts for a workflow run or repository.

        Args:
            run_id: Workflow run ID (None for all repository artifacts)

        Returns:
            List of artifact dictionaries

        Raises:
            GitHubActionsError: If listing fails
        """
        try:
            if run_id:
                run = self.repo.get_workflow_run(run_id)
                artifacts = run.get_artifacts()
            else:
                artifacts = self.repo.get_artifacts()

            return [
                {
                    "id": art.id,
                    "name": art.name,
                    "size_in_bytes": art.size_in_bytes,
                    "created_at": art.created_at,
                    "expired": art.expired,
                    "expires_at": art.expires_at,
                    "archive_download_url": art.archive_download_url,
                }
                for art in artifacts
            ]

        except GithubException as e:
            logger.error(f"Failed to list artifacts: {e}")
            raise GitHubActionsError(f"Failed to list artifacts: {e}")

    def download_artifact(
        self, artifact_id: int, destination: str
    ) -> str:
        """
        Download an artifact.

        Args:
            artifact_id: Artifact ID
            destination: Destination file path

        Returns:
            Path to downloaded file

        Raises:
            GitHubActionsError: If download fails
        """
        try:
            artifact = self.repo.get_artifact(artifact_id)

            # Download artifact
            headers = {"Authorization": f"token {self.token}"}
            response = requests.get(
                artifact.archive_download_url,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()

            # Write to file
            with open(destination, "wb") as f:
                f.write(response.content)

            logger.info(
                f"Downloaded artifact {artifact.name} to {destination}"
            )
            return destination

        except (GithubException, requests.RequestException) as e:
            logger.error(f"Failed to download artifact: {e}")
            raise GitHubActionsError(f"Failed to download artifact: {e}")

    def _workflow_run_to_dict(self, run: WorkflowRun) -> Dict[str, Any]:
        """
        Convert WorkflowRun object to dictionary.

        Args:
            run: WorkflowRun object

        Returns:
            Dictionary with run information
        """
        return {
            "id": run.id,
            "name": run.name,
            "head_branch": run.head_branch,
            "head_sha": run.head_sha,
            "status": run.status,
            "conclusion": run.conclusion,
            "workflow_id": run.workflow_id,
            "event": run.event,
            "created_at": run.created_at,
            "updated_at": run.updated_at,
            "html_url": run.html_url,
            "jobs_url": run.jobs_url,
            "logs_url": run.logs_url,
            "artifacts_url": run.artifacts_url,
        }

    def get_latest_run(
        self, workflow_id: str, branch: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest run for a workflow.

        Args:
            workflow_id: Workflow ID or filename
            branch: Optional branch filter

        Returns:
            Latest workflow run dictionary or None if no runs

        Raises:
            GitHubActionsError: If API call fails
        """
        runs = self.list_workflow_runs(
            workflow_id=workflow_id, branch=branch, limit=1
        )
        return runs[0] if runs else None

    def rerun_workflow(self, run_id: int) -> bool:
        """
        Rerun a failed workflow.

        Args:
            run_id: Workflow run ID

        Returns:
            True if rerun was triggered

        Raises:
            WorkflowRunError: If rerun fails
        """
        try:
            run = self.repo.get_workflow_run(run_id)
            result = run.rerun()

            if result:
                logger.info(f"Rerunning workflow run {run_id}")
                return True
            else:
                raise WorkflowRunError(f"Failed to rerun workflow run {run_id}")

        except GithubException as e:
            logger.error(f"Failed to rerun workflow: {e}")
            raise WorkflowRunError(f"Failed to rerun workflow: {e}")
