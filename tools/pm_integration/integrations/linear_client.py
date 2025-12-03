"""
Linear integration client for project management operations.

Provides comprehensive API access to Linear for issues, cycles, and projects
with field mapping and error handling.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


logger = logging.getLogger(__name__)


class LinearClient:
    """
    Client for Linear API operations.

    Handles authentication, issue management, cycle operations,
    and team management for Linear integration.
    """

    def __init__(self, api_key: str, default_team_id: Optional[str] = None):
        """
        Initialize Linear client.

        Args:
            api_key: Linear API key
            default_team_id: Default team ID for operations

        Raises:
            Exception: If connection fails
        """
        self.api_key = api_key
        self.default_team_id = default_team_id

        # Setup GraphQL client
        transport = RequestsHTTPTransport(
            url="https://api.linear.app/graphql",
            headers={"Authorization": api_key},
            retries=3,
        )

        self.client = Client(
            transport=transport, fetch_schema_from_transport=True
        )

        logger.info("Connected to Linear API")

        # Cache for teams and labels
        self._teams: Optional[List[Dict[str, Any]]] = None
        self._labels: Optional[Dict[str, List[Dict[str, Any]]]] = None

    def get_teams(self) -> List[Dict[str, Any]]:
        """
        Get all teams.

        Returns:
            List of team dictionaries
        """
        if self._teams is None:
            query = gql(
                """
                query {
                    teams {
                        nodes {
                            id
                            name
                            key
                        }
                    }
                }
                """
            )

            try:
                result = self.client.execute(query)
                self._teams = result.get("teams", {}).get("nodes", [])
                logger.info(f"Loaded {len(self._teams)} teams")
            except Exception as e:
                logger.error(f"Failed to load teams: {e}")
                self._teams = []

        return self._teams

    def get_team_labels(self, team_id: str) -> List[Dict[str, Any]]:
        """
        Get labels for a team.

        Args:
            team_id: Team ID

        Returns:
            List of label dictionaries
        """
        if self._labels is None:
            self._labels = {}

        if team_id not in self._labels:
            query = gql(
                """
                query($teamId: String!) {
                    team(id: $teamId) {
                        labels {
                            nodes {
                                id
                                name
                                color
                            }
                        }
                    }
                }
                """
            )

            try:
                result = self.client.execute(
                    query, variable_values={"teamId": team_id}
                )
                labels = (
                    result.get("team", {})
                    .get("labels", {})
                    .get("nodes", [])
                )
                self._labels[team_id] = labels
                logger.info(f"Loaded {len(labels)} labels for team")
            except Exception as e:
                logger.error(f"Failed to load labels: {e}")
                self._labels[team_id] = []

        return self._labels[team_id]

    def create_issue(
        self,
        team_id: Optional[str] = None,
        title: str = "",
        description: str = "",
        priority: int = 0,
        state_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        estimate: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new Linear issue.

        Args:
            team_id: Team ID (uses default if not provided)
            title: Issue title
            description: Issue description
            priority: Priority (0=None, 1=Urgent, 2=High, 3=Medium, 4=Low)
            state_id: Workflow state ID
            assignee_id: Assignee user ID
            label_ids: List of label IDs
            estimate: Story points estimate

        Returns:
            Issue data dictionary or None if creation fails
        """
        team = team_id or self.default_team_id
        if not team:
            logger.error("No team specified")
            return None

        mutation = gql(
            """
            mutation($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    success
                    issue {
                        id
                        identifier
                        title
                        description
                        priority
                        url
                        state {
                            id
                            name
                        }
                        assignee {
                            id
                            name
                        }
                        team {
                            id
                            key
                        }
                        createdAt
                        updatedAt
                    }
                }
            }
            """
        )

        input_data: Dict[str, Any] = {
            "teamId": team,
            "title": title,
            "description": description,
            "priority": priority,
        }

        if state_id:
            input_data["stateId"] = state_id

        if assignee_id:
            input_data["assigneeId"] = assignee_id

        if label_ids:
            input_data["labelIds"] = label_ids

        if estimate is not None:
            input_data["estimate"] = estimate

        try:
            result = self.client.execute(
                mutation, variable_values={"input": input_data}
            )
            issue_data = result.get("issueCreate", {})

            if issue_data.get("success"):
                issue = issue_data.get("issue", {})
                logger.info(f"Created issue: {issue.get('identifier')}")
                return self._format_issue(issue)
            else:
                logger.error("Issue creation failed")
                return None

        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return None

    def get_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """
        Get issue by ID.

        Args:
            issue_id: Issue ID

        Returns:
            Issue data dictionary or None if not found
        """
        query = gql(
            """
            query($id: String!) {
                issue(id: $id) {
                    id
                    identifier
                    title
                    description
                    priority
                    url
                    estimate
                    state {
                        id
                        name
                    }
                    assignee {
                        id
                        name
                    }
                    team {
                        id
                        key
                    }
                    labels {
                        nodes {
                            id
                            name
                        }
                    }
                    createdAt
                    updatedAt
                }
            }
            """
        )

        try:
            result = self.client.execute(
                query, variable_values={"id": issue_id}
            )
            issue = result.get("issue")
            return self._format_issue(issue) if issue else None

        except Exception as e:
            logger.error(f"Failed to get issue {issue_id}: {e}")
            return None

    def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[int] = None,
        state_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        estimate: Optional[int] = None,
    ) -> bool:
        """
        Update an existing issue.

        Args:
            issue_id: Issue ID
            title: New title
            description: New description
            priority: New priority
            state_id: New state ID
            assignee_id: New assignee ID
            label_ids: New label IDs
            estimate: New estimate

        Returns:
            True if update successful
        """
        mutation = gql(
            """
            mutation($id: String!, $input: IssueUpdateInput!) {
                issueUpdate(id: $id, input: $input) {
                    success
                }
            }
            """
        )

        input_data: Dict[str, Any] = {}

        if title is not None:
            input_data["title"] = title

        if description is not None:
            input_data["description"] = description

        if priority is not None:
            input_data["priority"] = priority

        if state_id is not None:
            input_data["stateId"] = state_id

        if assignee_id is not None:
            input_data["assigneeId"] = assignee_id

        if label_ids is not None:
            input_data["labelIds"] = label_ids

        if estimate is not None:
            input_data["estimate"] = estimate

        if not input_data:
            logger.warning("No fields to update")
            return False

        try:
            result = self.client.execute(
                mutation,
                variable_values={"id": issue_id, "input": input_data},
            )
            success = result.get("issueUpdate", {}).get("success", False)

            if success:
                logger.info(f"Updated issue: {issue_id}")
                return True
            else:
                logger.error("Issue update failed")
                return False

        except Exception as e:
            logger.error(f"Failed to update issue {issue_id}: {e}")
            return False

    def search_issues(
        self,
        team_id: Optional[str] = None,
        state_name: Optional[str] = None,
        assignee_id: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Search issues with filters.

        Args:
            team_id: Filter by team
            state_name: Filter by state name
            assignee_id: Filter by assignee
            label_ids: Filter by labels
            limit: Maximum results

        Returns:
            List of issue dictionaries
        """
        query = gql(
            """
            query($filter: IssueFilter, $first: Int) {
                issues(filter: $filter, first: $first) {
                    nodes {
                        id
                        identifier
                        title
                        description
                        priority
                        url
                        estimate
                        state {
                            id
                            name
                        }
                        assignee {
                            id
                            name
                        }
                        team {
                            id
                            key
                        }
                        labels {
                            nodes {
                                id
                                name
                            }
                        }
                        createdAt
                        updatedAt
                    }
                }
            }
            """
        )

        filter_data: Dict[str, Any] = {}

        if team_id:
            filter_data["team"] = {"id": {"eq": team_id}}

        if state_name:
            filter_data["state"] = {"name": {"eq": state_name}}

        if assignee_id:
            filter_data["assignee"] = {"id": {"eq": assignee_id}}

        if label_ids:
            filter_data["labels"] = {
                "some": {"id": {"in": label_ids}}
            }

        try:
            result = self.client.execute(
                query,
                variable_values={"filter": filter_data, "first": limit},
            )
            issues = result.get("issues", {}).get("nodes", [])
            return [self._format_issue(issue) for issue in issues]

        except Exception as e:
            logger.error(f"Failed to search issues: {e}")
            return []

    def get_cycles(
        self, team_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get cycles for a team.

        Args:
            team_id: Team ID (uses default if not provided)

        Returns:
            List of cycle dictionaries
        """
        team = team_id or self.default_team_id
        if not team:
            logger.error("No team specified")
            return []

        query = gql(
            """
            query($teamId: String!) {
                team(id: $teamId) {
                    cycles {
                        nodes {
                            id
                            number
                            name
                            startsAt
                            endsAt
                            completedAt
                        }
                    }
                }
            }
            """
        )

        try:
            result = self.client.execute(
                query, variable_values={"teamId": team}
            )
            cycles = (
                result.get("team", {}).get("cycles", {}).get("nodes", [])
            )
            return cycles

        except Exception as e:
            logger.error(f"Failed to get cycles: {e}")
            return []

    def get_cycle_issues(
        self, cycle_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get issues in a cycle.

        Args:
            cycle_id: Cycle ID

        Returns:
            List of issue dictionaries
        """
        query = gql(
            """
            query($cycleId: String!) {
                cycle(id: $cycleId) {
                    issues {
                        nodes {
                            id
                            identifier
                            title
                            description
                            priority
                            url
                            estimate
                            state {
                                id
                                name
                            }
                            assignee {
                                id
                                name
                            }
                            team {
                                id
                                key
                            }
                            createdAt
                            updatedAt
                        }
                    }
                }
            }
            """
        )

        try:
            result = self.client.execute(
                query, variable_values={"cycleId": cycle_id}
            )
            issues = (
                result.get("cycle", {}).get("issues", {}).get("nodes", [])
            )
            return [self._format_issue(issue) for issue in issues]

        except Exception as e:
            logger.error(f"Failed to get cycle issues: {e}")
            return []

    def get_workflow_states(
        self, team_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get workflow states for a team.

        Args:
            team_id: Team ID (uses default if not provided)

        Returns:
            List of workflow state dictionaries
        """
        team = team_id or self.default_team_id
        if not team:
            logger.error("No team specified")
            return []

        query = gql(
            """
            query($teamId: String!) {
                team(id: $teamId) {
                    states {
                        nodes {
                            id
                            name
                            type
                            position
                        }
                    }
                }
            }
            """
        )

        try:
            result = self.client.execute(
                query, variable_values={"teamId": team}
            )
            states = (
                result.get("team", {}).get("states", {}).get("nodes", [])
            )
            return states

        except Exception as e:
            logger.error(f"Failed to get workflow states: {e}")
            return []

    def add_comment(self, issue_id: str, body: str) -> bool:
        """
        Add a comment to an issue.

        Args:
            issue_id: Issue ID
            body: Comment text

        Returns:
            True if comment added successfully
        """
        mutation = gql(
            """
            mutation($input: CommentCreateInput!) {
                commentCreate(input: $input) {
                    success
                }
            }
            """
        )

        try:
            result = self.client.execute(
                mutation,
                variable_values={
                    "input": {"issueId": issue_id, "body": body}
                },
            )
            success = result.get("commentCreate", {}).get(
                "success", False
            )

            if success:
                logger.info(f"Added comment to issue {issue_id}")
                return True
            else:
                logger.error("Comment creation failed")
                return False

        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            return False

    def _format_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format Linear issue to standard dictionary.

        Args:
            issue: Raw issue data

        Returns:
            Formatted issue dictionary
        """
        state = issue.get("state", {})
        assignee = issue.get("assignee")
        team = issue.get("team", {})
        labels = issue.get("labels", {}).get("nodes", [])

        return {
            "id": issue.get("id"),
            "identifier": issue.get("identifier"),
            "title": issue.get("title"),
            "description": issue.get("description", ""),
            "priority": issue.get("priority", 0),
            "estimate": issue.get("estimate"),
            "state": state.get("name"),
            "state_id": state.get("id"),
            "assignee": assignee.get("name") if assignee else None,
            "assignee_id": assignee.get("id") if assignee else None,
            "team_key": team.get("key"),
            "team_id": team.get("id"),
            "labels": [label.get("name") for label in labels],
            "url": issue.get("url"),
            "created": issue.get("createdAt"),
            "updated": issue.get("updatedAt"),
        }
