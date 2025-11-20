"""
Configuration drift detection for Terraform-managed infrastructure.

This module compares Terraform state against actual cloud infrastructure
to identify configuration drift, generate reports, and provide
remediation recommendations.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum


logger = logging.getLogger(__name__)


class DriftType(Enum):
    """Types of configuration drift."""
    ADDED = "ADDED"  # Resource exists in cloud but not in state
    REMOVED = "REMOVED"  # Resource in state but not in cloud
    MODIFIED = "MODIFIED"  # Resource attributes changed
    NO_DRIFT = "NO_DRIFT"  # No drift detected


class DriftError(Exception):
    """Base exception for drift detection operations."""
    pass


@dataclass
class DriftedResource:
    """Container for a drifted resource."""
    resource_type: str
    resource_name: str
    resource_address: str
    drift_type: DriftType
    changes: Dict[str, Any]
    severity: str  # HIGH, MEDIUM, LOW


@dataclass
class DriftReport:
    """Container for drift detection results."""
    timestamp: str
    total_resources: int
    drifted_resources: int
    drift_details: List[DriftedResource]
    summary: Dict[str, int]


class DriftDetector:
    """
    Drift detector for Terraform-managed infrastructure.

    Compares Terraform state with actual cloud resources to identify
    configuration drift.
    """

    def __init__(self, terraform_wrapper, state_manager):
        """
        Initialize drift detector.

        Args:
            terraform_wrapper: TerraformWrapper instance
            state_manager: StateManager instance
        """
        self.terraform = terraform_wrapper
        self.state_manager = state_manager

    def detect_drift(self) -> DriftReport:
        """
        Detect configuration drift.

        Returns:
            DriftReport with drift details

        Raises:
            DriftError: If drift detection fails
        """
        logger.info("Starting drift detection...")

        try:
            # Generate a new plan to detect drift
            plan_output = self.terraform.plan(out="drift_plan")

            # Parse the plan to extract drift information
            plan_json = self.terraform.plan_json()

            # Analyze drift
            drift_details = self._analyze_plan_for_drift(plan_json)

            # Generate summary
            summary = self._generate_drift_summary(drift_details)

            timestamp = datetime.now().isoformat()

            report = DriftReport(
                timestamp=timestamp,
                total_resources=len(self._get_state_resources()),
                drifted_resources=len(drift_details),
                drift_details=drift_details,
                summary=summary
            )

            logger.info(
                f"Drift detection complete: {len(drift_details)} resources drifted"
            )

            return report

        except Exception as e:
            raise DriftError(f"Drift detection failed: {e}")

    def _get_state_resources(self) -> List[str]:
        """
        Get list of resources from Terraform state.

        Returns:
            List of resource addresses
        """
        try:
            return self.terraform.state_list()
        except Exception as e:
            logger.error(f"Failed to list state resources: {e}")
            return []

    def _analyze_plan_for_drift(
        self,
        plan_json: Dict[str, Any]
    ) -> List[DriftedResource]:
        """
        Analyze Terraform plan JSON for drift.

        Args:
            plan_json: Parsed Terraform plan JSON

        Returns:
            List of DriftedResource objects
        """
        drifted = []

        resource_changes = plan_json.get("resource_changes", [])

        for change in resource_changes:
            drift = self._analyze_resource_change(change)
            if drift:
                drifted.append(drift)

        # Also check for resource drift (in-place updates due to external changes)
        resource_drift = plan_json.get("resource_drift", [])
        for drift_info in resource_drift:
            drift = self._analyze_resource_drift(drift_info)
            if drift:
                drifted.append(drift)

        return drifted

    def _analyze_resource_change(
        self,
        change: Dict[str, Any]
    ) -> Optional[DriftedResource]:
        """
        Analyze a resource change for drift.

        Args:
            change: Resource change from plan

        Returns:
            DriftedResource if drift detected, None otherwise
        """
        resource_type = change.get("type", "")
        resource_name = change.get("name", "")
        resource_address = change.get("address", "")

        change_actions = change.get("change", {}).get("actions", [])

        # Skip if no change
        if change_actions == ["no-op"]:
            return None

        # Determine drift type
        if "create" in change_actions:
            drift_type = DriftType.ADDED
        elif "delete" in change_actions:
            drift_type = DriftType.REMOVED
        elif "update" in change_actions:
            drift_type = DriftType.MODIFIED
        else:
            return None

        # Extract changes
        before = change.get("change", {}).get("before", {})
        after = change.get("change", {}).get("after", {})

        changes = self._compute_changes(before, after)

        # Determine severity
        severity = self._assess_drift_severity(resource_type, changes)

        return DriftedResource(
            resource_type=resource_type,
            resource_name=resource_name,
            resource_address=resource_address,
            drift_type=drift_type,
            changes=changes,
            severity=severity
        )

    def _analyze_resource_drift(
        self,
        drift_info: Dict[str, Any]
    ) -> Optional[DriftedResource]:
        """
        Analyze resource drift information.

        Args:
            drift_info: Resource drift from plan

        Returns:
            DriftedResource if drift detected, None otherwise
        """
        resource_type = drift_info.get("type", "")
        resource_name = drift_info.get("name", "")
        resource_address = drift_info.get("address", "")

        change_actions = drift_info.get("change", {}).get("actions", [])

        # Resource drift indicates external changes
        if change_actions == ["no-op"]:
            return None

        before = drift_info.get("change", {}).get("before", {})
        after = drift_info.get("change", {}).get("after", {})

        changes = self._compute_changes(before, after)

        severity = self._assess_drift_severity(resource_type, changes)

        return DriftedResource(
            resource_type=resource_type,
            resource_name=resource_name,
            resource_address=resource_address,
            drift_type=DriftType.MODIFIED,
            changes=changes,
            severity=severity
        )

    def _compute_changes(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute differences between before and after states.

        Args:
            before: Before state
            after: After state

        Returns:
            Dictionary of changes
        """
        changes = {}

        # Handle None cases
        if before is None and after is None:
            return changes

        if before is None:
            return {"entire_resource": {"old": None, "new": after}}

        if after is None:
            return {"entire_resource": {"old": before, "new": None}}

        # Compare attributes
        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            old_value = before.get(key)
            new_value = after.get(key)

            if old_value != new_value:
                changes[key] = {
                    "old": old_value,
                    "new": new_value
                }

        return changes

    def _assess_drift_severity(
        self,
        resource_type: str,
        changes: Dict[str, Any]
    ) -> str:
        """
        Assess severity of drift.

        Args:
            resource_type: Type of resource
            changes: Changes detected

        Returns:
            Severity level (HIGH, MEDIUM, LOW)
        """
        # Critical resources
        critical_resources = [
            "aws_security_group",
            "aws_iam_role",
            "aws_iam_policy",
            "azurerm_network_security_group",
            "google_compute_firewall",
        ]

        # High-risk attributes
        high_risk_attributes = [
            "ingress",
            "egress",
            "policy",
            "security_rule",
            "allowed",
            "denied",
        ]

        if resource_type in critical_resources:
            return "HIGH"

        for attr in high_risk_attributes:
            if attr in changes:
                return "HIGH"

        # Check number of changes
        if len(changes) > 5:
            return "MEDIUM"

        return "LOW"

    def _generate_drift_summary(
        self,
        drift_details: List[DriftedResource]
    ) -> Dict[str, int]:
        """
        Generate drift summary statistics.

        Args:
            drift_details: List of drifted resources

        Returns:
            Summary dictionary
        """
        summary = {
            "total_drifted": len(drift_details),
            "added": 0,
            "removed": 0,
            "modified": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "low_severity": 0,
        }

        for drift in drift_details:
            if drift.drift_type == DriftType.ADDED:
                summary["added"] += 1
            elif drift.drift_type == DriftType.REMOVED:
                summary["removed"] += 1
            elif drift.drift_type == DriftType.MODIFIED:
                summary["modified"] += 1

            if drift.severity == "HIGH":
                summary["high_severity"] += 1
            elif drift.severity == "MEDIUM":
                summary["medium_severity"] += 1
            else:
                summary["low_severity"] += 1

        return summary

    def generate_drift_report(
        self,
        report: DriftReport,
        output_format: str = "text",
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate drift report in specified format.

        Args:
            report: DriftReport to format
            output_format: Report format (text, json, html)
            output_file: Optional file to write report to

        Returns:
            Formatted report as string
        """
        if output_format == "json":
            report_str = self._generate_json_report(report)
        elif output_format == "html":
            report_str = self._generate_html_report(report)
        else:
            report_str = self._generate_text_report(report)

        if output_file:
            Path(output_file).write_text(report_str)
            logger.info(f"Drift report written to: {output_file}")

        return report_str

    def _generate_text_report(self, report: DriftReport) -> str:
        """Generate text format drift report."""
        lines = [
            "=" * 80,
            "Terraform Drift Detection Report",
            "=" * 80,
            f"Timestamp: {report.timestamp}",
            f"Total Resources: {report.total_resources}",
            f"Drifted Resources: {report.drifted_resources}",
            "",
            "Summary:",
            f"  Added: {report.summary['added']}",
            f"  Removed: {report.summary['removed']}",
            f"  Modified: {report.summary['modified']}",
            "",
            "Severity Breakdown:",
            f"  High: {report.summary['high_severity']}",
            f"  Medium: {report.summary['medium_severity']}",
            f"  Low: {report.summary['low_severity']}",
            "",
            "=" * 80,
            "Drift Details:",
            "=" * 80,
        ]

        if not report.drift_details:
            lines.append("\nNo drift detected!")
        else:
            for i, drift in enumerate(report.drift_details, 1):
                lines.extend([
                    f"\n{i}. [{drift.severity}] {drift.resource_address}",
                    f"   Type: {drift.resource_type}",
                    f"   Drift: {drift.drift_type.value}",
                    "   Changes:",
                ])

                for attr, change in drift.changes.items():
                    lines.append(
                        f"     - {attr}: {change['old']} → {change['new']}"
                    )

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    def _generate_json_report(self, report: DriftReport) -> str:
        """Generate JSON format drift report."""
        report_data = {
            "timestamp": report.timestamp,
            "total_resources": report.total_resources,
            "drifted_resources": report.drifted_resources,
            "summary": report.summary,
            "drift_details": [
                {
                    "resource_type": d.resource_type,
                    "resource_name": d.resource_name,
                    "resource_address": d.resource_address,
                    "drift_type": d.drift_type.value,
                    "severity": d.severity,
                    "changes": d.changes,
                }
                for d in report.drift_details
            ]
        }

        return json.dumps(report_data, indent=2)

    def _generate_html_report(self, report: DriftReport) -> str:
        """Generate HTML format drift report."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Terraform Drift Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f0f0f0; padding: 15px; margin: 20px 0; }}
        .drift {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; }}
        .high {{ border-left: 5px solid #d32f2f; }}
        .medium {{ border-left: 5px solid #ffa000; }}
        .low {{ border-left: 5px solid #388e3c; }}
        .change {{ margin-left: 20px; font-family: monospace; }}
    </style>
</head>
<body>
    <h1>Terraform Drift Detection Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <p>Timestamp: {report.timestamp}</p>
        <p>Total Resources: {report.total_resources}</p>
        <p>Drifted Resources: {report.drifted_resources}</p>

        <h3>Drift Types</h3>
        <ul>
            <li>Added: {report.summary['added']}</li>
            <li>Removed: {report.summary['removed']}</li>
            <li>Modified: {report.summary['modified']}</li>
        </ul>

        <h3>Severity Breakdown</h3>
        <ul>
            <li>High: {report.summary['high_severity']}</li>
            <li>Medium: {report.summary['medium_severity']}</li>
            <li>Low: {report.summary['low_severity']}</li>
        </ul>
    </div>

    <h2>Drift Details</h2>
"""

        if not report.drift_details:
            html += "    <p>No drift detected!</p>\n"
        else:
            for drift in report.drift_details:
                severity_class = drift.severity.lower()
                html += f"""
    <div class="drift {severity_class}">
        <strong>[{drift.severity}] {drift.resource_address}</strong>
        <p>Type: {drift.resource_type}</p>
        <p>Drift: {drift.drift_type.value}</p>
        <p>Changes:</p>
"""
                for attr, change in drift.changes.items():
                    html += f'        <div class="change">{attr}: {change["old"]} → {change["new"]}</div>\n'

                html += "    </div>\n"

        html += """
</body>
</html>
"""

        return html

    def get_remediation_recommendations(
        self,
        report: DriftReport
    ) -> List[Dict[str, str]]:
        """
        Generate remediation recommendations for drifted resources.

        Args:
            report: DriftReport with drift details

        Returns:
            List of remediation recommendations
        """
        recommendations = []

        for drift in report.drift_details:
            if drift.drift_type == DriftType.ADDED:
                recommendations.append({
                    "resource": drift.resource_address,
                    "action": "import",
                    "command": f"terraform import {drift.resource_address} <resource-id>",
                    "description": "Import the manually created resource into Terraform state"
                })

            elif drift.drift_type == DriftType.REMOVED:
                recommendations.append({
                    "resource": drift.resource_address,
                    "action": "remove_from_state",
                    "command": f"terraform state rm {drift.resource_address}",
                    "description": "Remove the deleted resource from Terraform state"
                })

            elif drift.drift_type == DriftType.MODIFIED:
                recommendations.append({
                    "resource": drift.resource_address,
                    "action": "apply_changes",
                    "command": "terraform apply",
                    "description": f"Apply Terraform configuration to fix drift in {drift.resource_address}"
                })

        return recommendations

    def auto_remediate(
        self,
        report: DriftReport,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Automatically remediate drift (USE WITH CAUTION).

        Args:
            report: DriftReport with drift details
            auto_approve: Skip interactive approval

        Returns:
            Remediation results

        Raises:
            DriftError: If auto-remediation fails
        """
        if not auto_approve:
            logger.warning(
                "Auto-remediation requires manual approval. Set auto_approve=True"
            )
            return {"status": "skipped", "reason": "manual_approval_required"}

        logger.warning("Starting auto-remediation...")

        results = {
            "remediated": [],
            "failed": [],
            "skipped": []
        }

        for drift in report.drift_details:
            try:
                if drift.drift_type == DriftType.MODIFIED:
                    # Apply changes to fix drift
                    result = self.terraform.apply(auto_approve=True)
                    if result.success:
                        results["remediated"].append(drift.resource_address)
                    else:
                        results["failed"].append({
                            "resource": drift.resource_address,
                            "error": result.stderr
                        })

                else:
                    # Skip ADDED and REMOVED - require manual intervention
                    results["skipped"].append({
                        "resource": drift.resource_address,
                        "reason": f"Drift type {drift.drift_type.value} requires manual intervention"
                    })

            except Exception as e:
                logger.error(f"Failed to remediate {drift.resource_address}: {e}")
                results["failed"].append({
                    "resource": drift.resource_address,
                    "error": str(e)
                })

        return results
