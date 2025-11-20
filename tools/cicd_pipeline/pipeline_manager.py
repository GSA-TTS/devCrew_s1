"""
CI/CD Pipeline Manager
Issue #36 - TOOL-CICD-001

Main orchestration module for CI/CD pipeline operations.
Integrates GitHub Actions, quality gates, artifacts, and deployments.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from issue_36_artifact_manager import ArtifactManager
from issue_36_deployment_manager import DeploymentManager
from issue_36_github_actions_wrapper import (
    GitHubActionsWrapper,
    WorkflowRunError,
)
from issue_36_quality_gates import QualityGates

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Base exception for pipeline operations."""

    pass


class PipelineManager:
    """
    Main orchestrator for CI/CD pipeline operations.

    Provides high-level interface for triggering workflows,
    managing deployments, validating quality gates, and handling artifacts.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
    ):
        """
        Initialize pipeline manager.

        Args:
            config_path: Path to configuration YAML file
            token: GitHub personal access token (or from GITHUB_TOKEN env)
            repo_owner: Repository owner (or from config)
            repo_name: Repository name (or from config)
        """
        # Load configuration
        if config_path:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self._default_config()

        # Get GitHub credentials
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise PipelineError(
                "GitHub token required. Set GITHUB_TOKEN environment "
                "variable or pass token parameter."
            )

        # Get repository info
        github_config = self.config.get("github", {})
        self.repo_owner = repo_owner or github_config.get("owner")
        self.repo_name = repo_name or github_config.get("repo")

        if not self.repo_owner or not self.repo_name:
            raise PipelineError(
                "Repository owner and name required. Provide in config "
                "or as parameters."
            )

        # Initialize components
        self.github = GitHubActionsWrapper(
            token=self.token,
            repo_owner=self.repo_owner,
            repo_name=self.repo_name,
            timeout=github_config.get("timeout", 30),
            max_retries=github_config.get("max_retries", 3),
        )

        self.quality_gates = QualityGates(self.config)

        artifact_config = self.config.get("artifacts", {})
        self.artifacts = ArtifactManager(
            github_wrapper=self.github,
            download_path=artifact_config.get("download_path", "./artifacts"),
            retention_days=artifact_config.get("retention_days", 90),
        )

        self.deployments = DeploymentManager(
            github_wrapper=self.github,
            config=self.config,
        )

        logger.info(
            f"Initialized pipeline manager for {repo_owner}/{repo_name}"
        )

    def run_quality_gate(
        self,
        branch: str = "main",
        workflow_id: str = "quality_gate.yml",
        wait: bool = True,
    ) -> Dict[str, Any]:
        """
        Run quality gate workflow with coverage and security checks.

        Args:
            branch: Branch to run workflow on
            workflow_id: Quality gate workflow ID
            wait: Wait for workflow completion

        Returns:
            Workflow run result with quality gate status

        Raises:
            PipelineError: If quality gate fails
        """
        logger.info(f"Running quality gate on branch: {branch}")

        try:
            # Trigger workflow
            self.github.trigger_workflow(
                workflow_id=workflow_id,
                ref=branch,
            )

            # Get latest run
            import time
            time.sleep(5)  # Wait for run to appear
            latest_run = self.github.get_latest_run(workflow_id, branch=branch)

            if not latest_run:
                raise PipelineError("Failed to find quality gate workflow run")

            run_id = latest_run["id"]

            # Wait for completion if requested
            if wait:
                conclusion, run_info = self.github.wait_for_workflow_run(run_id)

                # Download and validate quality gate artifacts
                artifacts = self.artifacts.download_run_artifacts(
                    run_id,
                    name_filter="quality",
                )

                # Validate quality gates
                quality_passed, quality_report = self._validate_quality_artifacts(
                    artifacts
                )

                return {
                    "run_id": run_id,
                    "status": conclusion,
                    "quality_passed": quality_passed,
                    "quality_report": quality_report,
                    "run_url": run_info["html_url"],
                    "artifacts": artifacts,
                }
            else:
                return {
                    "run_id": run_id,
                    "status": "started",
                    "run_url": latest_run["html_url"],
                }

        except Exception as e:
            logger.error(f"Quality gate workflow failed: {e}")
            raise PipelineError(f"Quality gate workflow failed: {e}")

    def run_tdd_workflow(
        self,
        branch: str = "main",
        phase: str = "full",
        workflow_id: str = "tdd.yml",
    ) -> Dict[str, Any]:
        """
        Run TDD workflow (red-green-refactor).

        Args:
            branch: Branch to run workflow on
            phase: TDD phase (red, green, refactor, or full)
            workflow_id: TDD workflow ID

        Returns:
            Workflow run result

        Raises:
            PipelineError: If workflow fails
        """
        logger.info(f"Running TDD workflow - phase: {phase}")

        try:
            # Trigger workflow with phase input
            self.github.trigger_workflow(
                workflow_id=workflow_id,
                ref=branch,
                inputs={"phase": phase},
            )

            # Get latest run
            import time
            time.sleep(5)
            latest_run = self.github.get_latest_run(workflow_id, branch=branch)

            if not latest_run:
                raise PipelineError("Failed to find TDD workflow run")

            # Wait for completion
            conclusion, run_info = self.github.wait_for_workflow_run(
                latest_run["id"]
            )

            return {
                "run_id": latest_run["id"],
                "phase": phase,
                "status": conclusion,
                "run_url": run_info["html_url"],
            }

        except Exception as e:
            logger.error(f"TDD workflow failed: {e}")
            raise PipelineError(f"TDD workflow failed: {e}")

    def deploy(
        self,
        environment: str,
        version: str,
        skip_quality_gate: bool = False,
        skip_approval: bool = False,
    ) -> Dict[str, Any]:
        """
        Deploy to specified environment with quality gates.

        Args:
            environment: Target environment (dev, staging, production)
            version: Version/tag to deploy
            skip_quality_gate: Skip quality gate validation
            skip_approval: Skip approval gate

        Returns:
            Deployment result

        Raises:
            PipelineError: If deployment fails
        """
        logger.info(
            f"Starting deployment to {environment} (version: {version})"
        )

        # Run quality gate first unless skipped
        if not skip_quality_gate:
            logger.info("Running quality gate before deployment...")
            qg_result = self.run_quality_gate(branch=version, wait=True)

            if not qg_result.get("quality_passed", False):
                raise PipelineError(
                    "Quality gate failed. Deployment aborted. "
                    f"Report: {qg_result.get('quality_report')}"
                )

        # Execute deployment
        try:
            result = self.deployments.deploy(
                environment=environment,
                version=version,
                skip_approval=skip_approval,
            )

            logger.info(
                f"Successfully deployed {version} to {environment}"
            )

            return result

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise PipelineError(f"Deployment failed: {e}")

    def create_release(
        self,
        version: str,
        branch: str = "main",
        workflow_id: str = "release.yml",
    ) -> Dict[str, Any]:
        """
        Create release with automated workflow.

        Args:
            version: Release version (e.g., 'v1.0.0')
            branch: Branch to release from
            workflow_id: Release workflow ID

        Returns:
            Release result

        Raises:
            PipelineError: If release creation fails
        """
        logger.info(f"Creating release {version} from {branch}")

        try:
            # Trigger release workflow
            self.github.trigger_workflow(
                workflow_id=workflow_id,
                ref=branch,
                inputs={"version": version},
            )

            # Get latest run
            import time
            time.sleep(5)
            latest_run = self.github.get_latest_run(workflow_id, branch=branch)

            if not latest_run:
                raise PipelineError("Failed to find release workflow run")

            # Wait for completion
            conclusion, run_info = self.github.wait_for_workflow_run(
                latest_run["id"]
            )

            if conclusion != "success":
                raise PipelineError(
                    f"Release workflow failed with conclusion: {conclusion}"
                )

            return {
                "version": version,
                "status": conclusion,
                "run_id": latest_run["id"],
                "run_url": run_info["html_url"],
            }

        except Exception as e:
            logger.error(f"Release creation failed: {e}")
            raise PipelineError(f"Release creation failed: {e}")

    def get_pipeline_status(
        self, workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current pipeline status.

        Args:
            workflow_id: Filter by workflow ID (None for all)

        Returns:
            Dictionary with pipeline status
        """
        runs = self.github.list_workflow_runs(
            workflow_id=workflow_id,
            limit=10,
        )

        status = {
            "total_runs": len(runs),
            "in_progress": 0,
            "completed": 0,
            "success": 0,
            "failed": 0,
            "recent_runs": [],
        }

        for run in runs:
            if run["status"] == "in_progress":
                status["in_progress"] += 1
            elif run["status"] == "completed":
                status["completed"] += 1

                if run["conclusion"] == "success":
                    status["success"] += 1
                elif run["conclusion"] == "failure":
                    status["failed"] += 1

            status["recent_runs"].append(
                {
                    "id": run["id"],
                    "name": run["name"],
                    "status": run["status"],
                    "conclusion": run["conclusion"],
                    "created_at": run["created_at"],
                    "html_url": run["html_url"],
                }
            )

        return status

    def validate_pipeline(self) -> Tuple[bool, List[str]]:
        """
        Validate pipeline configuration and workflows.

        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []

        # Check workflows exist
        workflow_config = self.config.get("workflows", {})
        for workflow_name, workflow_file in workflow_config.items():
            if workflow_name in ["quality_gate", "tdd", "deployment", "release"]:
                try:
                    self.github.get_workflow(workflow_file)
                except Exception as e:
                    issues.append(
                        f"Workflow '{workflow_name}' ({workflow_file}) "
                        f"not found: {e}"
                    )

        # Validate quality gate thresholds
        qg_config = self.config.get("quality_gates", {})
        if not qg_config.get("coverage", {}).get("minimum"):
            issues.append("Coverage minimum threshold not configured")

        # Validate deployment environments
        env_config = self.config.get("deployment", {}).get("environments", {})
        for env in ["dev", "staging", "production"]:
            if env not in env_config:
                issues.append(f"Environment '{env}' not configured")

        is_valid = len(issues) == 0

        if is_valid:
            logger.info("Pipeline configuration is valid")
        else:
            logger.warning(f"Pipeline validation failed: {issues}")

        return is_valid, issues

    def _validate_quality_artifacts(
        self, artifact_paths: List[str]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate quality gate artifacts.

        Args:
            artifact_paths: List of downloaded artifact paths

        Returns:
            Tuple of (passed, report)
        """
        # Find quality reports in artifacts
        coverage_path = None
        security_path = None
        quality_path = None

        for path in artifact_paths:
            path_obj = Path(path)
            # Search for report files
            for file in path_obj.rglob("*"):
                if "coverage" in file.name and file.suffix in [".xml", ".json"]:
                    coverage_path = str(file)
                elif "security" in file.name and file.suffix == ".json":
                    security_path = str(file)
                elif "quality" in file.name and file.suffix == ".json":
                    quality_path = str(file)

        # Validate available reports
        try:
            passed, report = self.quality_gates.validate_all(
                coverage_path=coverage_path,
                security_path=security_path,
                quality_path=quality_path,
                fail_fast=False,
            )
            return passed, report
        except Exception as e:
            logger.warning(f"Quality gate validation error: {e}")
            return False, {"error": str(e)}

    def _default_config(self) -> Dict[str, Any]:
        """
        Generate default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            "github": {
                "timeout": 30,
                "max_retries": 3,
            },
            "workflows": {
                "quality_gate": "quality_gate.yml",
                "tdd": "tdd.yml",
                "deployment": "deployment.yml",
                "release": "release.yml",
                "default_branch": "main",
            },
            "quality_gates": {
                "coverage": {
                    "minimum": 80.0,
                    "enforcement": True,
                },
                "security": {
                    "max_high_severity": 0,
                    "fail_on_high": True,
                },
                "code_quality": {
                    "max_complexity": 10,
                },
            },
            "deployment": {
                "rollback_enabled": True,
                "health_check_timeout": 300,
                "environments": {
                    "dev": {
                        "requires_approval": False,
                        "auto_deploy": True,
                    },
                    "staging": {
                        "requires_approval": True,
                        "auto_deploy": False,
                    },
                    "production": {
                        "requires_approval": True,
                        "auto_deploy": False,
                    },
                },
            },
            "artifacts": {
                "retention_days": 90,
                "download_path": "./artifacts",
            },
        }

    def get_workflow_logs(self, run_id: int) -> str:
        """
        Get logs for a workflow run.

        Args:
            run_id: Workflow run ID

        Returns:
            Log content as string
        """
        return self.github.get_workflow_run_logs(run_id)

    def cancel_workflow(self, run_id: int) -> bool:
        """
        Cancel a running workflow.

        Args:
            run_id: Workflow run ID

        Returns:
            True if cancellation successful
        """
        return self.github.cancel_workflow_run(run_id)

    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List all available workflows.

        Returns:
            List of workflow dictionaries
        """
        return self.github.list_workflows()
