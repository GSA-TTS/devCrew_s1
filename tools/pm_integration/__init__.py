"""
Project Management Integration Platform

Unified interface for managing issues, sprints, and projects across Jira,
Linear, and GitHub Projects with bidirectional synchronization.

Protocol Coverage:
- P-ISSUE-TRIAGE: Automated GitHub issue classification and labeling
- P-FEATURE-DEV: Cross-platform feature tracking and release planning
"""

__version__ = "1.0.0"
__author__ = "DevCrew Team"

from .integrations.jira_client import JiraClient
from .integrations.linear_client import LinearClient
from .integrations.github_client import GitHubPMClient
from .sync.sync_engine import SyncEngine
from .classifier.issue_classifier import IssueClassifier
from .analytics.sprint_analytics import SprintAnalytics

__all__ = [
    "JiraClient",
    "LinearClient",
    "GitHubPMClient",
    "SyncEngine",
    "IssueClassifier",
    "SprintAnalytics",
]
