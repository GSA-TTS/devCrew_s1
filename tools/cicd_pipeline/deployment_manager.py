"""
Deployment Manager Module
Issue #36 - TOOL-CICD-001

Manages multi-environment deployments with approval gates,
health checks, and rollback capabilities.
"""

import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import requests

from issue_36_github_actions_wrapper import GitHubActionsWrapper

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Deployment environment types."""

    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(Enum):
    """Deployment status states."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeploymentError(Exception):
    """Base exception for deployment operations."""

    pass


class HealthCheckError(DeploymentError):
    """Raised when health check fails."""

    pass


class ApprovalRequiredError(DeploymentError):
    """Raised when deployment requires approval."""

    pass


class DeploymentManager:
    """
    Manages deployments across multiple environments.

    Provides deployment orchestration with approval gates,
    health checks, and automatic rollback capabilities.
    """

    def __init__(
        self,
        github_wrapper: GitHubActionsWrapper,
        config: Dict[str, Any],
    ):
        """
        Initialize deployment manager.

        Args:
            github_wrapper: GitHubActionsWrapper instance
            config: Deployment configuration
        """
        self.github = github_wrapper
        self.config = config
        self.deployment_config = config.get("deployment", {})
        self.environments_config = self.deployment_config.get("environments", {})

        logger.info("Initialized deployment manager")

    def deploy(
        self,
        environment: str,
        version: str,
        workflow_id: str = "deployment.yml",
        skip_approval: bool = False,
        skip_health_check: bool = False,
    ) -> Dict[str, Any]:
        """
        Deploy to specified environment.

        Args:
            environment: Target environment (dev, staging, production)
            version: Version/tag to deploy
            workflow_id: Deployment workflow ID
            skip_approval: Skip approval gate (use with caution)
            skip_health_check: Skip health check validation

        Returns:
            Deployment result dictionary

        Raises:
            DeploymentError: If deployment fails
            ApprovalRequiredError: If approval is required
        """
        env_config = self.environments_config.get(environment, {})

        # Check if approval is required
        requires_approval = env_config.get("requires_approval", False)
        if requires_approval and not skip_approval:
            raise ApprovalRequiredError(
                f"Deployment to {environment} requires approval. "
                f"Approvers: {env_config.get('approvers', [])}"
            )

        logger.info(f"Starting deployment to {environment} (version: {version})")

        # Trigger deployment workflow
        inputs = {
            "environment": environment,
            "version": version,
        }

        try:
            # Trigger workflow
            self.github.trigger_workflow(
                workflow_id=workflow_id,
                ref="main",
                inputs=inputs,
            )

            # Wait for workflow to start
            time.sleep(5)

            # Get latest run
            latest_run = self.github.get_latest_run(workflow_id, branch="main")

            if not latest_run:
                raise DeploymentError("Failed to find deployment workflow run")

            run_id = latest_run["id"]

            # Wait for completion
            conclusion, run_info = self.github.wait_for_workflow_run(
                run_id,
                poll_interval=self.deployment_config.get("poll_interval", 10),
                max_wait_time=self.deployment_config.get("max_wait_time", 1800),
            )

            if conclusion != "success":
                raise DeploymentError(
                    f"Deployment workflow failed with conclusion: {conclusion}"
                )

            # Perform health check
            if not skip_health_check and env_config.get("health_check_url"):
                health_check_passed = self.health_check(
                    env_config["health_check_url"]
                )

                if not health_check_passed:
                    # Attempt rollback if enabled
                    if self.deployment_config.get("rollback_enabled", True):
                        logger.warning("Health check failed, initiating rollback")
                        self.rollback(environment, version)

                    raise HealthCheckError(
                        f"Health check failed for {environment}"
                    )

            logger.info(f"Successfully deployed to {environment}")

            return {
                "environment": environment,
                "version": version,
                "status": DeploymentStatus.SUCCESS.value,
                "run_id": run_id,
                "run_url": run_info["html_url"],
                "health_check": not skip_health_check,
            }

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise DeploymentError(f"Deployment failed: {e}")

    def health_check(
        self,
        url: str,
        timeout: int = 300,
        retry_interval: int = 10,
    ) -> bool:
        """
        Perform health check on deployed application.

        Args:
            url: Health check endpoint URL
            timeout: Maximum time to wait for healthy status
            retry_interval: Time between retries

        Returns:
            True if health check passed

        Raises:
            HealthCheckError: If health check fails
        """
        start_time = time.time()
        max_retries = self.deployment_config.get("health_check_retries", 5)
        retries = 0

        logger.info(f"Starting health check: {url}")

        while retries < max_retries:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise HealthCheckError(
                    f"Health check timeout after {timeout}s"
                )

            try:
                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    logger.info(f"Health check passed (attempt {retries + 1})")
                    return True

                logger.warning(
                    f"Health check returned {response.status_code} "
                    f"(attempt {retries + 1}/{max_retries})"
                )

            except requests.RequestException as e:
                logger.warning(
                    f"Health check request failed: {e} "
                    f"(attempt {retries + 1}/{max_retries})"
                )

            retries += 1
            if retries < max_retries:
                time.sleep(retry_interval)

        raise HealthCheckError(
            f"Health check failed after {max_retries} attempts"
        )

    def rollback(
        self,
        environment: str,
        from_version: str,
        to_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Rollback deployment to previous version.

        Args:
            environment: Target environment
            from_version: Current (failed) version
            to_version: Version to rollback to (None for previous)

        Returns:
            Rollback result dictionary

        Raises:
            DeploymentError: If rollback fails
        """
        logger.warning(
            f"Initiating rollback in {environment} from {from_version}"
        )

        # If no target version specified, determine previous version
        if to_version is None:
            # In real implementation, query deployment history
            # For now, use placeholder
            to_version = "previous"
            logger.warning(
                "No target version specified, using 'previous' placeholder"
            )

        try:
            # Trigger rollback deployment
            result = self.deploy(
                environment=environment,
                version=to_version,
                skip_approval=True,  # Rollbacks bypass approval
                skip_health_check=False,
            )

            result["status"] = DeploymentStatus.ROLLED_BACK.value
            result["rolled_back_from"] = from_version

            logger.info(
                f"Successfully rolled back {environment} from "
                f"{from_version} to {to_version}"
            )

            return result

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise DeploymentError(f"Rollback failed: {e}")

    def get_deployment_status(
        self, environment: str
    ) -> Dict[str, Any]:
        """
        Get current deployment status for environment.

        Args:
            environment: Target environment

        Returns:
            Dictionary with deployment status
        """
        # Get latest deployment workflow run for environment
        runs = self.github.list_workflow_runs(
            workflow_id="deployment.yml",
            status="completed",
            limit=10,
        )

        # Filter runs for this environment (would need to parse inputs in real impl)
        env_runs = [
            run for run in runs
            if run["conclusion"] == "success"
        ]

        if not env_runs:
            return {
                "environment": environment,
                "status": "unknown",
                "last_deployment": None,
            }

        latest = env_runs[0]

        return {
            "environment": environment,
            "status": "deployed",
            "last_deployment": {
                "version": "unknown",  # Would parse from workflow inputs
                "deployed_at": latest["created_at"],
                "run_id": latest["id"],
                "run_url": latest["html_url"],
            },
        }

    def validate_deployment(
        self,
        environment: str,
        checks: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Validate deployment with custom checks.

        Args:
            environment: Target environment
            checks: List of check types to perform

        Returns:
            Tuple of (passed, failed_checks)
        """
        env_config = self.environments_config.get(environment, {})
        failed_checks = []

        if checks is None:
            checks = ["health_check"]

        # Health check
        if "health_check" in checks and env_config.get("health_check_url"):
            try:
                self.health_check(env_config["health_check_url"])
            except HealthCheckError as e:
                failed_checks.append(f"health_check: {e}")

        # Custom validation logic can be added here

        passed = len(failed_checks) == 0

        if passed:
            logger.info(f"All deployment validations passed for {environment}")
        else:
            logger.warning(
                f"Deployment validation failed for {environment}: "
                f"{failed_checks}"
            )

        return passed, failed_checks

    def approve_deployment(
        self,
        environment: str,
        approver: str,
    ) -> bool:
        """
        Approve pending deployment.

        Args:
            environment: Target environment
            approver: Approver identifier

        Returns:
            True if approval was recorded

        Note:
            In real implementation, this would integrate with
            GitHub Environments approval workflow
        """
        env_config = self.environments_config.get(environment, {})
        required_approvers = env_config.get("approvers", [])

        if approver not in required_approvers:
            logger.warning(
                f"{approver} is not an authorized approver for {environment}"
            )
            return False

        logger.info(
            f"Deployment to {environment} approved by {approver}"
        )

        # In real implementation, this would:
        # 1. Record approval in database/state store
        # 2. Trigger deployment workflow if all approvals collected
        # 3. Send notifications

        return True

    def list_deployments(
        self,
        environment: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        List recent deployments.

        Args:
            environment: Filter by environment
            limit: Maximum number of deployments to return

        Returns:
            List of deployment records
        """
        runs = self.github.list_workflow_runs(
            workflow_id="deployment.yml",
            status="completed",
            limit=limit * 3,  # Get more to account for filtering
        )

        deployments = []
        for run in runs:
            # In real implementation, parse environment from workflow inputs
            deployment = {
                "run_id": run["id"],
                "environment": "unknown",  # Would parse from inputs
                "status": run["conclusion"],
                "created_at": run["created_at"],
                "html_url": run["html_url"],
            }

            # Filter by environment if specified
            if environment is None or deployment["environment"] == environment:
                deployments.append(deployment)

            if len(deployments) >= limit:
                break

        return deployments

    def get_environment_config(
        self, environment: str
    ) -> Dict[str, Any]:
        """
        Get configuration for specified environment.

        Args:
            environment: Target environment

        Returns:
            Environment configuration dictionary
        """
        return self.environments_config.get(environment, {})

    def plan_deployment(
        self,
        environment: str,
        version: str,
    ) -> Dict[str, Any]:
        """
        Generate deployment plan without executing.

        Args:
            environment: Target environment
            version: Version to deploy

        Returns:
            Dictionary with deployment plan details
        """
        env_config = self.get_environment_config(environment)

        plan = {
            "environment": environment,
            "version": version,
            "requires_approval": env_config.get("requires_approval", False),
            "approvers": env_config.get("approvers", []),
            "auto_deploy": env_config.get("auto_deploy", False),
            "health_check_enabled": bool(env_config.get("health_check_url")),
            "rollback_enabled": self.deployment_config.get("rollback_enabled", True),
            "steps": [
                "Trigger deployment workflow",
                "Wait for workflow completion",
            ],
        }

        if plan["requires_approval"]:
            plan["steps"].insert(0, "Obtain approval from required approvers")

        if plan["health_check_enabled"]:
            plan["steps"].append("Perform health check")

        if plan["rollback_enabled"]:
            plan["steps"].append("Rollback on failure (if enabled)")

        return plan
