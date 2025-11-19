#!/usr/bin/env python3
"""GitHub Integration Tool (TOOL-COLLAB-001) for devCrew.

This package provides GitHub integration for devCrew agent protocols.
"""

__version__ = "1.0.0"
__author__ = "devCrew Team"

from devgru_github_api import (
    GitHubAPIError,
    IssueManager,
    PRManager,
    WorkflowManager,
    batch_create_issues,
    get_github_client,
)
from devgru_github_cli import (
    GHCLIError,
    close_issue,
    create_issue,
    create_pr,
    get_auth_token,
    merge_pr,
    read_issue,
    trigger_workflow,
    update_issue,
)

__all__ = [
    # CLI functions
    "create_issue",
    "read_issue",
    "update_issue",
    "close_issue",
    "create_pr",
    "merge_pr",
    "trigger_workflow",
    "get_auth_token",
    "GHCLIError",
    # API classes
    "get_github_client",
    "IssueManager",
    "PRManager",
    "WorkflowManager",
    "batch_create_issues",
    "GitHubAPIError",
]
