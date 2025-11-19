#!/usr/bin/env python3
"""GitHub CLI wrapper for devCrew agent operations.

This module provides wrapper functions around GitHub CLI (gh) commands
with automatic retry logic, error handling, and JSON parsing.
"""

import json
import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Optional

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format=(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"message": "%(message)s"}'
    ),
)
logger = logging.getLogger(__name__)


class GHCLIError(Exception):
    """Exception raised for GitHub CLI errors."""

    pass


def get_auth_token() -> str:
    """Get GitHub authentication token from environment.

    Returns:
        str: GitHub personal access token

    Raises:
        GHCLIError: If token is not found in environment
    """
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise GHCLIError(
            "GitHub token not found. Set GH_TOKEN or GITHUB_TOKEN environment variable."
        )
    return token


def _run_gh_command(
    args: List[str],
    max_retries: int = 3,
    parse_json: bool = True,
) -> Any:
    """Execute GitHub CLI command with retry logic.

    Args:
        args: Command arguments to pass to gh CLI
        max_retries: Maximum number of retry attempts (default: 3)
        parse_json: Whether to parse output as JSON (default: True)

    Returns:
        Parsed JSON response or raw stdout if parse_json=False

    Raises:
        GHCLIError: If command fails after all retries
    """
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Running gh command: {' '.join(args)} "
                f"(attempt {attempt + 1}/{max_retries})"
            )

            result = subprocess.run(
                ["gh"] + args,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                if not parse_json:
                    return result.stdout

                try:
                    return json.loads(result.stdout) if result.stdout.strip() else {}
                except json.JSONDecodeError as e:
                    raise GHCLIError(
                        f"JSON parsing failed: {e}. Output: {result.stdout}"
                    )

            # Check for transient errors (server errors)
            stderr = result.stderr.lower()
            if any(code in stderr for code in ["502", "503", "504"]):
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Transient error detected. Retrying in {wait_time}s... "
                        f"Error: {result.stderr}"
                    )
                    time.sleep(wait_time)
                    continue

            # Permanent error
            raise GHCLIError(f"GitHub CLI error: {result.stderr}")

        except subprocess.TimeoutExpired:
            if attempt < max_retries - 1:
                logger.warning("Command timeout. Retrying...")
                continue
            raise GHCLIError("GitHub CLI command timed out after all retries")
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Unexpected error: {e}. Retrying...")
                time.sleep(2**attempt)
                continue
            raise GHCLIError(f"Unexpected error: {e}")

    raise GHCLIError("Max retries exceeded")


def create_issue(
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    milestone: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a GitHub issue.

    Args:
        title: Issue title
        body: Issue description (supports markdown)
        labels: List of labels to apply
        assignees: List of usernames to assign
        milestone: Milestone name

    Returns:
        Dict containing issue details (number, title, etc.)

    Raises:
        GHCLIError: If issue creation fails
    """
    args = [
        "issue",
        "create",
        "--title",
        title,
        "--body",
        body,
        "--json",
        "number,title,state,labels,assignees",
    ]

    if labels:
        args.extend(["--label", ",".join(labels)])

    if assignees:
        args.extend(["--assignee", ",".join(assignees)])

    if milestone:
        args.extend(["--milestone", milestone])

    logger.info(f"Creating issue: {title}")
    return _run_gh_command(args)


def read_issue(issue_number: int) -> Dict[str, Any]:
    """Read issue details.

    Args:
        issue_number: Issue number to read

    Returns:
        Dict containing issue details

    Raises:
        GHCLIError: If issue cannot be read
    """
    args = [
        "issue",
        "view",
        str(issue_number),
        "--json",
        "number,title,body,state,labels,assignees,milestone,comments",
    ]

    logger.info(f"Reading issue #{issue_number}")
    return _run_gh_command(args)


def get_issue(issue_number: int) -> Dict[str, Any]:
    """Alias for read_issue for consistency.

    Args:
        issue_number: Issue number to get

    Returns:
        Dict containing issue details
    """
    return read_issue(issue_number)


def update_issue(
    issue_number: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    add_labels: Optional[List[str]] = None,
    remove_labels: Optional[List[str]] = None,
    add_assignees: Optional[List[str]] = None,
    remove_assignees: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Update an existing issue.

    Args:
        issue_number: Issue number to update
        title: New title (optional)
        body: New body (optional)
        add_labels: Labels to add
        remove_labels: Labels to remove
        add_assignees: Assignees to add
        remove_assignees: Assignees to remove

    Returns:
        Dict containing updated issue details

    Raises:
        GHCLIError: If update fails
    """
    args = ["issue", "edit", str(issue_number)]

    if title:
        args.extend(["--title", title])

    if body:
        args.extend(["--body", body])

    if add_labels:
        args.extend(["--add-label", ",".join(add_labels)])

    if remove_labels:
        args.extend(["--remove-label", ",".join(remove_labels)])

    if add_assignees:
        args.extend(["--add-assignee", ",".join(add_assignees)])

    if remove_assignees:
        args.extend(["--remove-assignee", ",".join(remove_assignees)])

    args.extend(["--json", "number,title,state,labels,assignees"])

    logger.info(f"Updating issue #{issue_number}")
    return _run_gh_command(args)


def close_issue(issue_number: int, comment: Optional[str] = None) -> Dict[str, Any]:
    """Close an issue.

    Args:
        issue_number: Issue number to close
        comment: Optional closing comment

    Returns:
        Dict containing closed issue details

    Raises:
        GHCLIError: If close fails
    """
    args = ["issue", "close", str(issue_number)]

    if comment:
        args.extend(["--comment", comment])

    args.extend(["--json", "number,title,state"])

    logger.info(f"Closing issue #{issue_number}")
    return _run_gh_command(args)


def create_pr(
    title: str,
    body: str,
    base: str,
    head: str,
    reviewers: Optional[List[str]] = None,
    labels: Optional[List[str]] = None,
    draft: bool = False,
) -> Dict[str, Any]:
    """Create a pull request.

    Args:
        title: PR title
        body: PR description
        base: Base branch (e.g., 'main')
        head: Head branch (feature branch)
        reviewers: List of reviewer usernames
        labels: List of labels to apply
        draft: Whether to create as draft PR

    Returns:
        Dict containing PR details

    Raises:
        GHCLIError: If PR creation fails
    """
    args = [
        "pr",
        "create",
        "--title",
        title,
        "--body",
        body,
        "--base",
        base,
        "--head",
        head,
        "--json",
        "number,title,state,draft,url",
    ]

    if reviewers:
        args.extend(["--reviewer", ",".join(reviewers)])

    if labels:
        args.extend(["--label", ",".join(labels)])

    if draft:
        args.append("--draft")

    logger.info(f"Creating PR: {title}")
    return _run_gh_command(args)


def merge_pr(
    pr_number: int,
    merge_method: str = "merge",
    delete_branch: bool = False,
    auto: bool = False,
) -> Dict[str, Any]:
    """Merge a pull request.

    Args:
        pr_number: PR number to merge
        merge_method: Merge method ('merge', 'squash', 'rebase')
        delete_branch: Whether to delete head branch after merge
        auto: Enable auto-merge when checks pass

    Returns:
        Dict containing merge result

    Raises:
        GHCLIError: If merge fails
    """
    args = ["pr", "merge", str(pr_number)]

    if merge_method == "squash":
        args.append("--squash")
    elif merge_method == "rebase":
        args.append("--rebase")
    elif merge_method == "merge":
        args.append("--merge")
    else:
        raise GHCLIError(f"Invalid merge method: {merge_method}")

    if delete_branch:
        args.append("--delete-branch")

    if auto:
        args.append("--auto")

    args.extend(["--json", "number,merged,state"])

    logger.info(f"Merging PR #{pr_number} with method: {merge_method}")
    return _run_gh_command(args)


def trigger_workflow(
    workflow_name: str,
    ref: str,
    inputs: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Trigger a GitHub Actions workflow.

    Args:
        workflow_name: Workflow file name (e.g., 'deploy.yml')
        ref: Git ref to run workflow on (branch, tag, commit)
        inputs: Workflow inputs as key-value pairs

    Returns:
        Dict containing workflow dispatch result

    Raises:
        GHCLIError: If workflow trigger fails
    """
    args = ["workflow", "run", workflow_name, "--ref", ref]

    if inputs:
        for key, value in inputs.items():
            args.extend(["--field", f"{key}={value}"])

    # Note: gh workflow run doesn't return JSON by default
    # We'll parse the success message
    _run_gh_command(args, parse_json=False)

    logger.info(f"Triggered workflow: {workflow_name} on ref: {ref}")

    # Return a simulated response
    return {"status": "queued", "workflow": workflow_name, "ref": ref}
