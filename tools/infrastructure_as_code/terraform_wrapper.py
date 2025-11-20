"""
Terraform CLI wrapper for executing terraform commands.

This module provides a comprehensive wrapper around the Terraform CLI,
enabling programmatic execution of terraform operations with proper
error handling, output parsing, and workspace management.
"""

import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class TerraformError(Exception):
    """Base exception for Terraform operations."""
    pass


class TerraformCommandError(TerraformError):
    """Exception raised when a Terraform command fails."""
    pass


class TerraformParseError(TerraformError):
    """Exception raised when parsing Terraform output fails."""
    pass


@dataclass
class TerraformOutput:
    """Container for Terraform command output."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    duration: float


class TerraformWrapper:
    """
    Wrapper class for Terraform CLI operations.

    Provides methods for executing terraform commands with retry logic,
    output parsing, and comprehensive error handling.
    """

    def __init__(
        self,
        working_dir: str,
        terraform_bin: str = "terraform",
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize Terraform wrapper.

        Args:
            working_dir: Directory containing Terraform configurations
            terraform_bin: Path to terraform binary
            max_retries: Maximum number of retries for transient failures
            retry_delay: Delay between retries in seconds
        """
        self.working_dir = Path(working_dir)
        self.terraform_bin = terraform_bin
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        if not self.working_dir.exists():
            raise TerraformError(f"Working directory does not exist: {working_dir}")

        self._verify_terraform_installed()

    def _verify_terraform_installed(self) -> None:
        """Verify that Terraform is installed and accessible."""
        try:
            result = self._execute_command(["version"], check_return_code=False)
            if result.return_code != 0:
                raise TerraformError(
                    f"Terraform not found or not executable: {self.terraform_bin}"
                )
            logger.info(f"Terraform version: {result.stdout.strip()}")
        except FileNotFoundError:
            raise TerraformError(
                f"Terraform binary not found: {self.terraform_bin}"
            )

    def _execute_command(
        self,
        args: List[str],
        check_return_code: bool = True,
        retry_on_failure: bool = False
    ) -> TerraformOutput:
        """
        Execute a terraform command with optional retry logic.

        Args:
            args: Command arguments (e.g., ['init', '-upgrade'])
            check_return_code: Raise exception on non-zero return code
            retry_on_failure: Enable retry logic for transient failures

        Returns:
            TerraformOutput with command results

        Raises:
            TerraformCommandError: If command fails and check_return_code is True
        """
        cmd = [self.terraform_bin] + args
        attempt = 0

        while attempt < (self.max_retries if retry_on_failure else 1):
            attempt += 1
            start_time = time.time()

            try:
                logger.info(f"Executing: {' '.join(cmd)} (attempt {attempt})")

                process = subprocess.Popen(
                    cmd,
                    cwd=str(self.working_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout, stderr = process.communicate()
                duration = time.time() - start_time

                output = TerraformOutput(
                    success=process.returncode == 0,
                    stdout=stdout,
                    stderr=stderr,
                    return_code=process.returncode,
                    duration=duration
                )

                if not output.success and check_return_code:
                    if retry_on_failure and attempt < self.max_retries:
                        logger.warning(
                            f"Command failed (attempt {attempt}/{self.max_retries}), "
                            f"retrying in {self.retry_delay}s..."
                        )
                        time.sleep(self.retry_delay)
                        continue

                    raise TerraformCommandError(
                        f"Terraform command failed: {' '.join(cmd)}\n"
                        f"Return code: {process.returncode}\n"
                        f"STDOUT: {stdout}\n"
                        f"STDERR: {stderr}"
                    )

                logger.info(f"Command completed in {duration:.2f}s")
                return output

            except subprocess.SubprocessError as e:
                if retry_on_failure and attempt < self.max_retries:
                    logger.warning(f"Subprocess error, retrying: {e}")
                    time.sleep(self.retry_delay)
                    continue
                raise TerraformError(f"Failed to execute terraform: {e}")

        raise TerraformError(f"Max retries ({self.max_retries}) exceeded")

    def init(
        self,
        upgrade: bool = False,
        backend_config: Optional[Dict[str, str]] = None,
        reconfigure: bool = False
    ) -> TerraformOutput:
        """
        Execute terraform init.

        Args:
            upgrade: Upgrade modules and plugins
            backend_config: Backend configuration parameters
            reconfigure: Reconfigure backend ignoring saved configuration

        Returns:
            TerraformOutput with init results
        """
        args = ["init"]

        if upgrade:
            args.append("-upgrade")

        if reconfigure:
            args.append("-reconfigure")

        if backend_config:
            for key, value in backend_config.items():
                args.extend(["-backend-config", f"{key}={value}"])

        return self._execute_command(args, retry_on_failure=True)

    def plan(
        self,
        var_file: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        out: Optional[str] = None,
        destroy: bool = False
    ) -> TerraformOutput:
        """
        Execute terraform plan.

        Args:
            var_file: Path to variable file
            variables: Variables to pass to terraform
            out: Save plan to file
            destroy: Create a destroy plan

        Returns:
            TerraformOutput with plan results
        """
        args = ["plan"]

        if var_file:
            args.extend(["-var-file", var_file])

        if variables:
            for key, value in variables.items():
                args.extend(["-var", f"{key}={value}"])

        if out:
            args.extend(["-out", out])

        if destroy:
            args.append("-destroy")

        return self._execute_command(args)

    def plan_json(
        self,
        var_file: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute terraform plan and return JSON output.

        Args:
            var_file: Path to variable file
            variables: Variables to pass to terraform

        Returns:
            Parsed JSON plan output

        Raises:
            TerraformParseError: If JSON parsing fails
        """
        plan_file = str(self.working_dir / "tfplan")

        # Generate plan file
        self.plan(var_file=var_file, variables=variables, out=plan_file)

        # Show plan in JSON format
        args = ["show", "-json", plan_file]
        result = self._execute_command(args)

        try:
            plan_data = json.loads(result.stdout)
            return plan_data
        except json.JSONDecodeError as e:
            raise TerraformParseError(f"Failed to parse plan JSON: {e}")

    def apply(
        self,
        var_file: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        plan_file: Optional[str] = None,
        auto_approve: bool = False
    ) -> TerraformOutput:
        """
        Execute terraform apply.

        Args:
            var_file: Path to variable file
            variables: Variables to pass to terraform
            plan_file: Apply a saved plan file
            auto_approve: Skip interactive approval

        Returns:
            TerraformOutput with apply results
        """
        args = ["apply"]

        if plan_file:
            args.append(plan_file)
        else:
            if var_file:
                args.extend(["-var-file", var_file])

            if variables:
                for key, value in variables.items():
                    args.extend(["-var", f"{key}={value}"])

            if auto_approve:
                args.append("-auto-approve")

        return self._execute_command(args, retry_on_failure=True)

    def destroy(
        self,
        var_file: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        auto_approve: bool = False
    ) -> TerraformOutput:
        """
        Execute terraform destroy.

        Args:
            var_file: Path to variable file
            variables: Variables to pass to terraform
            auto_approve: Skip interactive approval

        Returns:
            TerraformOutput with destroy results
        """
        args = ["destroy"]

        if var_file:
            args.extend(["-var-file", var_file])

        if variables:
            for key, value in variables.items():
                args.extend(["-var", f"{key}={value}"])

        if auto_approve:
            args.append("-auto-approve")

        return self._execute_command(args)

    def output(self, name: Optional[str] = None, json_format: bool = True) -> Any:
        """
        Get terraform output values.

        Args:
            name: Specific output name (None for all outputs)
            json_format: Return as JSON (True) or raw string (False)

        Returns:
            Output value(s) as dict or string
        """
        args = ["output"]

        if json_format:
            args.append("-json")

        if name:
            args.append(name)

        result = self._execute_command(args, check_return_code=False)

        if result.return_code != 0:
            logger.warning(f"No outputs found: {result.stderr}")
            return {} if json_format else ""

        if json_format:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                raise TerraformParseError(f"Failed to parse output JSON: {e}")

        return result.stdout.strip()

    def workspace_list(self) -> List[str]:
        """
        List all workspaces.

        Returns:
            List of workspace names
        """
        result = self._execute_command(["workspace", "list"])

        workspaces = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line:
                # Remove asterisk from current workspace
                workspace = line.lstrip("* ").strip()
                if workspace:
                    workspaces.append(workspace)

        return workspaces

    def workspace_select(self, name: str) -> TerraformOutput:
        """
        Select a workspace.

        Args:
            name: Workspace name

        Returns:
            TerraformOutput with select results
        """
        return self._execute_command(["workspace", "select", name])

    def workspace_new(self, name: str) -> TerraformOutput:
        """
        Create a new workspace.

        Args:
            name: Workspace name

        Returns:
            TerraformOutput with new workspace results
        """
        return self._execute_command(["workspace", "new", name])

    def workspace_delete(self, name: str, force: bool = False) -> TerraformOutput:
        """
        Delete a workspace.

        Args:
            name: Workspace name
            force: Force deletion

        Returns:
            TerraformOutput with delete results
        """
        args = ["workspace", "delete"]
        if force:
            args.append("-force")
        args.append(name)

        return self._execute_command(args)

    def state_list(self) -> List[str]:
        """
        List resources in terraform state.

        Returns:
            List of resource addresses
        """
        result = self._execute_command(["state", "list"])

        resources = []
        for line in result.stdout.split("\n"):
            line = line.strip()
            if line:
                resources.append(line)

        return resources

    def state_show(self, address: str) -> str:
        """
        Show a resource in the state.

        Args:
            address: Resource address

        Returns:
            Resource details as string
        """
        result = self._execute_command(["state", "show", address])
        return result.stdout

    def state_pull(self) -> Dict[str, Any]:
        """
        Pull and parse the current state.

        Returns:
            State as parsed JSON

        Raises:
            TerraformParseError: If state parsing fails
        """
        result = self._execute_command(["state", "pull"])

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise TerraformParseError(f"Failed to parse state JSON: {e}")

    def validate(self) -> TerraformOutput:
        """
        Validate terraform configuration.

        Returns:
            TerraformOutput with validation results
        """
        return self._execute_command(["validate", "-json"])

    def fmt(self, check: bool = False, recursive: bool = True) -> TerraformOutput:
        """
        Format terraform configuration files.

        Args:
            check: Check if files are formatted (don't modify)
            recursive: Process subdirectories

        Returns:
            TerraformOutput with format results
        """
        args = ["fmt"]

        if check:
            args.append("-check")

        if recursive:
            args.append("-recursive")

        return self._execute_command(args, check_return_code=False)
