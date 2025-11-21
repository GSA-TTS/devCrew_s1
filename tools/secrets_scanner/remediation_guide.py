"""
Remediation Guide for secret rotation and handling.

Provides workflows and priority scoring for remediation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .pattern_manager import PatternSeverity
from .secret_scanner import SecretFinding


class RemediationPriority(Enum):
    """Priority level for remediation."""

    P1_IMMEDIATE = 1
    P2_URGENT = 2
    P3_HIGH = 3
    P4_MEDIUM = 4
    P5_LOW = 5


@dataclass
class RemediationStep:
    """A step in the remediation workflow."""

    order: int
    action: str
    description: str
    automated: bool = False
    command: Optional[str] = None
    documentation_url: Optional[str] = None


@dataclass
class RotationWorkflow:
    """Workflow for rotating a secret."""

    pattern_name: str
    service_name: str
    steps: List[RemediationStep] = field(default_factory=list)
    estimated_time: str = ""
    documentation_url: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_name": self.pattern_name,
            "service_name": self.service_name,
            "steps": [
                {
                    "order": s.order,
                    "action": s.action,
                    "description": s.description,
                    "automated": s.automated,
                    "command": s.command,
                    "documentation_url": s.documentation_url,
                }
                for s in self.steps
            ],
            "estimated_time": self.estimated_time,
            "documentation_url": self.documentation_url,
            "notes": self.notes,
        }


@dataclass
class RemediationReport:
    """Report for a finding's remediation."""

    finding: SecretFinding
    priority: RemediationPriority
    priority_score: int
    workflow: Optional[RotationWorkflow] = None
    impact_assessment: str = ""
    recommended_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "finding_hash": self.finding.hash_value,
            "pattern_name": self.finding.pattern_name,
            "file_path": self.finding.file_path,
            "priority": self.priority.name,
            "priority_score": self.priority_score,
            "workflow": self.workflow.to_dict() if self.workflow else None,
            "impact_assessment": self.impact_assessment,
            "recommended_actions": self.recommended_actions,
        }


class RemediationGuide:
    """Guide for remediating detected secrets."""

    def __init__(self) -> None:
        """Initialize with built-in workflows."""
        self._workflows: Dict[str, RotationWorkflow] = {}
        self._load_builtin_workflows()

    def _load_builtin_workflows(self) -> None:
        """Load built-in rotation workflows."""
        # AWS Rotation
        self._workflows["aws_access_key_id"] = RotationWorkflow(
            pattern_name="aws_access_key_id",
            service_name="AWS IAM",
            steps=[
                RemediationStep(
                    order=1,
                    action="Create new access key",
                    description="Generate a new access key pair in AWS IAM Console",
                    documentation_url="https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html",
                ),
                RemediationStep(
                    order=2,
                    action="Update applications",
                    description="Update all applications using the old key with the new credentials",
                ),
                RemediationStep(
                    order=3,
                    action="Test new credentials",
                    description="Verify all applications work with new credentials",
                ),
                RemediationStep(
                    order=4,
                    action="Deactivate old key",
                    description="Deactivate the exposed key in IAM Console",
                    automated=True,
                    command="aws iam update-access-key --access-key-id <KEY> --status Inactive",
                ),
                RemediationStep(
                    order=5,
                    action="Delete old key",
                    description="After confirming no issues, delete the old key",
                    automated=True,
                    command="aws iam delete-access-key --access-key-id <KEY>",
                ),
                RemediationStep(
                    order=6,
                    action="Audit CloudTrail",
                    description="Review CloudTrail logs for unauthorized use of the exposed key",
                ),
            ],
            estimated_time="30-60 minutes",
            documentation_url="https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html",
            notes="Consider using IAM roles instead of access keys where possible",
        )

        # GitHub Token Rotation
        self._workflows["github_token"] = RotationWorkflow(
            pattern_name="github_token",
            service_name="GitHub",
            steps=[
                RemediationStep(
                    order=1,
                    action="Revoke exposed token",
                    description="Immediately revoke the token in GitHub Settings > Developer Settings > Personal Access Tokens",
                    documentation_url="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/token-expiration-and-revocation",
                ),
                RemediationStep(
                    order=2,
                    action="Create new token",
                    description="Generate a new token with minimum required permissions",
                ),
                RemediationStep(
                    order=3,
                    action="Update applications",
                    description="Update all CI/CD pipelines and applications with new token",
                ),
                RemediationStep(
                    order=4,
                    action="Audit activity",
                    description="Review audit logs for unauthorized repository access",
                ),
            ],
            estimated_time="15-30 minutes",
            documentation_url="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens",
        )

        # Slack Token Rotation
        self._workflows["slack_token"] = RotationWorkflow(
            pattern_name="slack_token",
            service_name="Slack",
            steps=[
                RemediationStep(
                    order=1,
                    action="Revoke token",
                    description="Revoke the token in Slack App management",
                ),
                RemediationStep(
                    order=2,
                    action="Regenerate credentials",
                    description="Generate new OAuth tokens or bot tokens",
                ),
                RemediationStep(
                    order=3,
                    action="Update integrations",
                    description="Update all applications using Slack integration",
                ),
            ],
            estimated_time="15-30 minutes",
            documentation_url="https://api.slack.com/authentication/token-types",
        )

        # Stripe Key Rotation
        self._workflows["stripe_secret_key"] = RotationWorkflow(
            pattern_name="stripe_secret_key",
            service_name="Stripe",
            steps=[
                RemediationStep(
                    order=1,
                    action="Roll API keys",
                    description="Use Stripe Dashboard to roll secret keys",
                    documentation_url="https://stripe.com/docs/keys#rolling-keys",
                ),
                RemediationStep(
                    order=2,
                    action="Update applications",
                    description="Update all applications with new API keys",
                ),
                RemediationStep(
                    order=3,
                    action="Review transactions",
                    description="Audit recent transactions for unauthorized activity",
                ),
            ],
            estimated_time="20-40 minutes",
            documentation_url="https://stripe.com/docs/keys",
            notes="Stripe keys can be rolled without downtime using versioned keys",
        )

        # Private Key Rotation
        self._workflows["private_key_rsa"] = RotationWorkflow(
            pattern_name="private_key_rsa",
            service_name="General",
            steps=[
                RemediationStep(
                    order=1,
                    action="Generate new key pair",
                    description="Generate a new RSA key pair",
                    automated=True,
                    command="ssh-keygen -t rsa -b 4096 -f new_key",
                ),
                RemediationStep(
                    order=2,
                    action="Deploy public key",
                    description="Deploy the new public key to all authorized_keys files",
                ),
                RemediationStep(
                    order=3,
                    action="Update configurations",
                    description="Update all configurations to use the new private key",
                ),
                RemediationStep(
                    order=4,
                    action="Remove old key",
                    description="Remove the old public key from all systems",
                ),
                RemediationStep(
                    order=5,
                    action="Secure delete old key",
                    description="Securely delete the compromised private key",
                    automated=True,
                    command="shred -u old_key",
                ),
            ],
            estimated_time="30-60 minutes",
        )

        # Database Connection String
        self._workflows["postgres_uri"] = RotationWorkflow(
            pattern_name="postgres_uri",
            service_name="PostgreSQL",
            steps=[
                RemediationStep(
                    order=1,
                    action="Create new user/password",
                    description="Create new database credentials",
                ),
                RemediationStep(
                    order=2,
                    action="Update applications",
                    description="Update connection strings in all applications",
                ),
                RemediationStep(
                    order=3,
                    action="Test connections",
                    description="Verify applications can connect with new credentials",
                ),
                RemediationStep(
                    order=4,
                    action="Revoke old credentials",
                    description="Revoke or change password for exposed credentials",
                ),
                RemediationStep(
                    order=5,
                    action="Audit access logs",
                    description="Review database access logs for unauthorized queries",
                ),
            ],
            estimated_time="30-60 minutes",
            notes="Consider using managed secrets services like AWS Secrets Manager",
        )

    def calculate_priority_score(self, finding: SecretFinding) -> int:
        """
        Calculate priority score for remediation.

        Score is 0-100, higher = more urgent.
        """
        score = 0

        # Severity component (0-40)
        severity_scores = {
            PatternSeverity.CRITICAL: 40,
            PatternSeverity.HIGH: 30,
            PatternSeverity.MEDIUM: 20,
            PatternSeverity.LOW: 10,
        }
        score += severity_scores.get(finding.severity, 20)

        # Entropy component (0-20)
        if finding.entropy:
            if finding.entropy > 5.0:
                score += 20
            elif finding.entropy > 4.0:
                score += 15
            elif finding.entropy > 3.0:
                score += 10

        # Category component (0-20)
        high_risk_categories = {"aws", "payment", "keys", "database"}
        if finding.category in high_risk_categories:
            score += 20
        elif finding.category in {"github", "google", "slack"}:
            score += 15
        else:
            score += 10

        # Verification component (0-20)
        if finding.is_verified:
            score += 20

        return min(score, 100)

    def get_priority(self, score: int) -> RemediationPriority:
        """Get priority level from score."""
        if score >= 80:
            return RemediationPriority.P1_IMMEDIATE
        elif score >= 60:
            return RemediationPriority.P2_URGENT
        elif score >= 40:
            return RemediationPriority.P3_HIGH
        elif score >= 20:
            return RemediationPriority.P4_MEDIUM
        else:
            return RemediationPriority.P5_LOW

    def get_workflow(self, pattern_name: str) -> Optional[RotationWorkflow]:
        """Get rotation workflow for a pattern."""
        return self._workflows.get(pattern_name)

    def add_workflow(self, workflow: RotationWorkflow) -> None:
        """Add custom rotation workflow."""
        self._workflows[workflow.pattern_name] = workflow

    def generate_report(self, finding: SecretFinding) -> RemediationReport:
        """Generate remediation report for a finding."""
        score = self.calculate_priority_score(finding)
        priority = self.get_priority(score)
        workflow = self.get_workflow(finding.pattern_name)

        # Generate impact assessment
        impact = self._assess_impact(finding)

        # Generate recommended actions
        actions = self._get_recommended_actions(finding, priority)

        return RemediationReport(
            finding=finding,
            priority=priority,
            priority_score=score,
            workflow=workflow,
            impact_assessment=impact,
            recommended_actions=actions,
        )

    def _assess_impact(self, finding: SecretFinding) -> str:
        """Assess potential impact of exposed secret."""
        impacts = {
            "aws": "Exposed AWS credentials could allow unauthorized access to cloud resources, data exfiltration, and resource abuse.",
            "github": "Exposed GitHub tokens could allow unauthorized repository access, code modifications, and supply chain attacks.",
            "google": "Exposed Google API keys could allow unauthorized API usage and potential data access.",
            "slack": "Exposed Slack tokens could allow unauthorized messaging and data access in workspaces.",
            "payment": "Exposed payment credentials could allow unauthorized transactions and financial fraud.",
            "database": "Exposed database credentials could allow unauthorized data access, modification, or deletion.",
            "keys": "Exposed private keys could allow unauthorized system access and identity impersonation.",
        }

        return impacts.get(
            finding.category,
            "Exposed secret could potentially allow unauthorized access to protected resources.",
        )

    def _get_recommended_actions(
        self, finding: SecretFinding, priority: RemediationPriority
    ) -> List[str]:
        """Get recommended actions based on finding."""
        actions = []

        if priority in (RemediationPriority.P1_IMMEDIATE, RemediationPriority.P2_URGENT):
            actions.append("Immediately revoke or rotate the exposed credential")
            actions.append("Check audit logs for unauthorized access")
            actions.append("Notify security team")

        actions.append("Remove the secret from the codebase")
        actions.append("Use environment variables or secrets management service")
        actions.append("Add the file pattern to .gitignore if appropriate")
        actions.append("Update baseline after remediation")

        return actions

    def batch_report(
        self, findings: List[SecretFinding]
    ) -> List[RemediationReport]:
        """Generate reports for multiple findings."""
        reports = [self.generate_report(f) for f in findings]
        # Sort by priority score descending
        reports.sort(key=lambda r: r.priority_score, reverse=True)
        return reports

    def get_summary(
        self, reports: List[RemediationReport]
    ) -> Dict[str, Any]:
        """Get summary of remediation reports."""
        priority_counts = {p.name: 0 for p in RemediationPriority}
        for report in reports:
            priority_counts[report.priority.name] += 1

        return {
            "total_findings": len(reports),
            "priority_breakdown": priority_counts,
            "immediate_action_required": priority_counts.get("P1_IMMEDIATE", 0),
            "urgent_action_required": priority_counts.get("P2_URGENT", 0),
            "highest_priority_findings": [
                r.to_dict() for r in reports[:5]
            ],
        }

    def export_workflows(self) -> List[Dict[str, Any]]:
        """Export all workflows."""
        return [w.to_dict() for w in self._workflows.values()]

    def get_supported_patterns(self) -> List[str]:
        """Get patterns with defined workflows."""
        return list(self._workflows.keys())
