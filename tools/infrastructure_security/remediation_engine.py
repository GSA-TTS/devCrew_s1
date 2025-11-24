"""
Remediation Engine for Infrastructure Security Scanner Platform.

Provides automated fix generation, pull request creation, and remediation
playbooks for common security issues found in infrastructure as code,
containers, and cloud configurations. Supports auto-fixing hardcoded
secrets, open ports, weak encryption, and compliance drift detection.
"""

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field, validator


class RemediationError(Exception):
    """Base exception for remediation engine errors."""

    pass


class AutoFixError(RemediationError):
    """Exception raised when automated fix application fails."""

    pass


class PRCreationError(RemediationError):
    """Exception raised when pull request creation fails."""

    pass


class RemediationType(str, Enum):
    """Type of remediation action."""

    AUTO_FIX = "auto_fix"
    MANUAL = "manual"
    PLAYBOOK = "playbook"


class RemediationStatus(str, Enum):
    """Status of remediation action."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPLIED = "applied"
    FAILED = "failed"


class RemediationConfig(BaseModel):
    """Configuration for remediation engine."""

    auto_apply: bool = Field(default=False, description="Automatically apply fixes")
    create_pr: bool = Field(default=True, description="Create pull requests for fixes")
    dry_run: bool = Field(
        default=True, description="Perform dry run without applying changes"
    )
    backup_enabled: bool = Field(
        default=True, description="Create backups before applying changes"
    )
    backup_dir: Path = Field(
        default=Path(".remediation_backups"),
        description="Directory for backups",
    )
    github_token: Optional[str] = Field(
        default=None, description="GitHub API token for PR creation"
    )
    max_auto_fixes: int = Field(
        default=10, description="Maximum number of auto fixes per run"
    )
    pr_branch_prefix: str = Field(
        default="security-fix", description="Prefix for fix branches"
    )

    @validator("backup_dir")
    def validate_backup_dir(cls, v: Path) -> Path:
        """Ensure backup directory is absolute."""
        return v.resolve()


class CodeChange(BaseModel):
    """Represents a code modification to fix a security issue."""

    file_path: Path = Field(description="Path to file being modified")
    original_code: str = Field(description="Original code snippet")
    fixed_code: str = Field(description="Fixed code snippet")
    line_number: Optional[int] = Field(
        default=None, description="Line number of change"
    )
    description: str = Field(description="Description of the change")

    class Config:
        arbitrary_types_allowed = True


class RemediationAction(BaseModel):
    """Represents a remediation action for a security finding."""

    finding_id: str = Field(description="ID of the security finding")
    remediation_type: RemediationType = Field(description="Type of remediation")
    description: str = Field(description="Description of remediation")
    code_changes: List[CodeChange] = Field(
        default_factory=list, description="Code changes to apply"
    )
    commands: List[str] = Field(default_factory=list, description="Commands to execute")
    playbook_steps: List[str] = Field(
        default_factory=list, description="Manual remediation steps"
    )
    severity: str = Field(default="medium", description="Severity level")
    confidence: float = Field(default=0.8, description="Confidence in fix (0-1)")
    estimated_time: str = Field(
        default="5 minutes", description="Estimated time to apply"
    )
    references: List[str] = Field(
        default_factory=list, description="Reference documentation"
    )

    class Config:
        arbitrary_types_allowed = True


class AutoFixResult(BaseModel):
    """Result of an automated fix application."""

    action: RemediationAction = Field(description="Remediation action applied")
    status: RemediationStatus = Field(description="Status of the fix")
    changes_applied: int = Field(default=0, description="Number of changes applied")
    pr_url: Optional[str] = Field(
        default=None, description="URL of created pull request"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if failed"
    )
    backup_path: Optional[Path] = Field(
        default=None, description="Path to backup files"
    )
    applied_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of application"
    )

    class Config:
        arbitrary_types_allowed = True


class RemediationPlaybook(BaseModel):
    """Step-by-step remediation guide for manual fixes."""

    title: str = Field(description="Title of the playbook")
    finding_id: str = Field(description="ID of the security finding")
    severity: str = Field(description="Severity level")
    steps: List[str] = Field(description="Remediation steps")
    prerequisites: List[str] = Field(
        default_factory=list, description="Prerequisites for remediation"
    )
    verification: List[str] = Field(
        default_factory=list, description="Verification steps"
    )
    estimated_time: str = Field(description="Estimated remediation time")
    references: List[str] = Field(
        default_factory=list, description="Reference documentation"
    )
    code_examples: Dict[str, str] = Field(
        default_factory=dict, description="Code examples for remediation"
    )


@dataclass
class ComplianceDrift:
    """Represents a compliance drift between scans."""

    finding_id: str
    issue_type: str
    resource: str
    severity: str
    first_seen: datetime
    description: str
    remediation_action: Optional[RemediationAction] = None


class RemediationEngine:
    """
    Remediation engine for automated security fix generation and application.

    Provides automated fixes for common security issues including hardcoded
    secrets, open ports, weak encryption, and infrastructure
    misconfigurations. Supports creating pull requests with fixes and
    generating manual remediation playbooks.
    """

    def __init__(self, config: RemediationConfig) -> None:
        """
        Initialize the remediation engine.

        Args:
            config: Remediation engine configuration

        Raises:
            RemediationError: If initialization fails
        """
        self.config = config
        self._fix_count = 0
        self._applied_fixes: List[AutoFixResult] = []

        if config.backup_enabled:
            config.backup_dir.mkdir(parents=True, exist_ok=True)

        self._issue_patterns = self._load_issue_patterns()

    def _load_issue_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns for common security issues."""
        return {
            "hardcoded_secret": {
                "patterns": [
                    r'password\s*=\s*["\']([^"\']+)["\']',
                    r'api[_-]?key\s*=\s*["\']([^"\']+)["\']',
                    r'secret\s*=\s*["\']([^"\']+)["\']',
                    r'token\s*=\s*["\']([^"\']+)["\']',
                    r'aws_access_key_id\s*=\s*["\']([^"\']+)["\']',
                ],
                "severity": "critical",
                "remediation_type": RemediationType.AUTO_FIX,
            },
            "open_security_group": {
                "patterns": [
                    r'cidr_blocks\s*=\s*\["0\.0\.0\.0/0"\]',
                    r'source_address_prefix\s*=\s*["\*"]',
                    r'SourceAddressPrefix\s*=\s*["\*"]',
                ],
                "severity": "high",
                "remediation_type": RemediationType.AUTO_FIX,
            },
            "weak_encryption": {
                "patterns": [
                    r'algorithm\s*=\s*["\']MD5["\']',
                    r'algorithm\s*=\s*["\']SHA1["\']',
                    r"encryption\s*=\s*false",
                    r"ssl_enabled\s*=\s*false",
                ],
                "severity": "high",
                "remediation_type": RemediationType.AUTO_FIX,
            },
            "docker_root_user": {
                "patterns": [r"^FROM\s+\w+.*\n(?!USER\s+\w+)"],
                "severity": "medium",
                "remediation_type": RemediationType.AUTO_FIX,
            },
            "kubernetes_privileged": {
                "patterns": [r"privileged:\s*true"],
                "severity": "high",
                "remediation_type": RemediationType.AUTO_FIX,
            },
        }

    def generate_remediation(self, finding: Any) -> RemediationAction:
        """
        Generate remediation action for a security finding.

        Args:
            finding: Security finding object or dictionary

        Returns:
            RemediationAction with fix details

        Raises:
            RemediationError: If remediation generation fails
        """
        try:
            finding_dict = finding if isinstance(finding, dict) else finding.dict()
            issue_type = self._classify_issue(finding_dict)

            if issue_type == "hardcoded_secret":
                return self._fix_hardcoded_secret(finding_dict)
            elif issue_type == "open_security_group":
                return self._fix_open_security_group(finding_dict)
            elif issue_type == "weak_encryption":
                return self._fix_weak_encryption(finding_dict)
            elif issue_type.startswith("terraform_"):
                return self._fix_terraform_issue(finding_dict)
            elif issue_type.startswith("docker_"):
                return self._fix_dockerfile_issue(finding_dict)
            elif issue_type.startswith("kubernetes_"):
                return self._fix_kubernetes_issue(finding_dict)
            else:
                return self._generate_manual_remediation(finding_dict)

        except Exception as e:
            raise RemediationError(f"Failed to generate remediation: {str(e)}") from e

    def apply_auto_fix(self, action: RemediationAction) -> AutoFixResult:
        """
        Apply automated fix for a remediation action.

        Args:
            action: RemediationAction to apply

        Returns:
            AutoFixResult with application details

        Raises:
            AutoFixError: If fix application fails
        """
        if action.remediation_type != RemediationType.AUTO_FIX:
            raise AutoFixError(
                f"Action type {action.remediation_type} is not auto-fixable"
            )

        if self._fix_count >= self.config.max_auto_fixes:
            raise AutoFixError(
                f"Maximum auto-fixes limit ({self.config.max_auto_fixes}) " "reached"
            )

        result = AutoFixResult(action=action, status=RemediationStatus.PENDING)

        try:
            result.status = RemediationStatus.IN_PROGRESS

            backup_path = None
            if self.config.backup_enabled:
                backup_path = self._create_backup(action.code_changes)
                result.backup_path = backup_path

            if not self.config.dry_run:
                if self._apply_code_changes(action.code_changes):
                    result.changes_applied = len(action.code_changes)
                    result.status = RemediationStatus.APPLIED
                    self._fix_count += 1
                else:
                    result.status = RemediationStatus.FAILED
                    result.error_message = "Failed to apply code changes"
            else:
                result.changes_applied = len(action.code_changes)
                result.status = RemediationStatus.APPLIED

            self._applied_fixes.append(result)
            return result

        except Exception as e:
            result.status = RemediationStatus.FAILED
            result.error_message = str(e)
            raise AutoFixError(f"Failed to apply auto-fix: {str(e)}") from e

    def create_fix_pr(self, actions: List[RemediationAction], repo: str) -> str:
        """
        Create pull request with remediation fixes.

        Args:
            actions: List of remediation actions to include
            repo: Repository in format "owner/repo"

        Returns:
            URL of created pull request

        Raises:
            PRCreationError: If PR creation fails
        """
        if not self.config.github_token:
            raise PRCreationError("GitHub token not configured")

        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
            branch_name = f"{self.config.pr_branch_prefix}-{timestamp}"

            all_changes: List[CodeChange] = []
            for action in actions:
                all_changes.extend(action.code_changes)

            if self.config.backup_enabled:
                self._create_backup(all_changes)

            pr_url = self._create_github_pr(all_changes, repo, branch_name)

            return pr_url

        except Exception as e:
            raise PRCreationError(f"Failed to create pull request: {str(e)}") from e

    def generate_playbook(self, finding: Any) -> RemediationPlaybook:
        """
        Generate manual remediation playbook for a finding.

        Args:
            finding: Security finding object or dictionary

        Returns:
            RemediationPlaybook with step-by-step guide

        Raises:
            RemediationError: If playbook generation fails
        """
        try:
            finding_dict = finding if isinstance(finding, dict) else finding.dict()
            issue_type = self._classify_issue(finding_dict)

            playbook = RemediationPlaybook(
                title=f"Remediation Guide: {finding_dict.get('title', 'Security Issue')}",  # noqa: E501
                finding_id=finding_dict.get("id", "unknown"),
                severity=finding_dict.get("severity", "medium"),
                steps=[],
                estimated_time="15-30 minutes",
            )

            if issue_type == "hardcoded_secret":
                playbook.steps = self._get_secret_playbook_steps()
                playbook.prerequisites = [
                    "Access to secrets management system",
                    "Permissions to modify application configuration",
                ]
                playbook.verification = [
                    "Verify secret is stored in secrets manager",
                    "Test application with environment variable",
                    "Confirm no secrets in code repository",
                ]
            elif issue_type == "open_security_group":
                playbook.steps = self._get_security_group_playbook_steps()
                playbook.prerequisites = [
                    "AWS/Azure/GCP console access",
                    "Understanding of required network access",
                ]
                playbook.verification = [
                    "Verify security group rules are restricted",
                    "Test application connectivity",
                    "Run security scan to confirm fix",
                ]
            elif issue_type == "weak_encryption":
                playbook.steps = self._get_encryption_playbook_steps()
                playbook.prerequisites = [
                    "Understanding of encryption algorithms",
                    "Access to update encryption configuration",
                ]
                playbook.verification = [
                    "Verify strong encryption algorithm is used",
                    "Test encrypted data transmission",
                    "Run compliance scan to confirm",
                ]
            else:
                playbook.steps = self._get_generic_playbook_steps(finding_dict)

            playbook.references = self._get_references_for_issue(issue_type)
            playbook.code_examples = self._get_code_examples_for_issue(issue_type)

            return playbook

        except Exception as e:
            raise RemediationError(f"Failed to generate playbook: {str(e)}") from e

    def detect_compliance_drift(
        self, current_scan: Any, baseline: Any
    ) -> List[ComplianceDrift]:
        """
        Detect compliance drift between current scan and baseline.

        Args:
            current_scan: Current security scan results
            baseline: Baseline security scan results

        Returns:
            List of compliance drifts detected

        Raises:
            RemediationError: If drift detection fails
        """
        try:
            current_dict = (
                current_scan if isinstance(current_scan, dict) else current_scan.dict()
            )
            baseline_dict = baseline if isinstance(baseline, dict) else baseline.dict()

            current_findings = self._extract_findings(current_dict)
            baseline_findings = self._extract_findings(baseline_dict)

            baseline_ids = {f["id"] for f in baseline_findings}
            drifts: List[ComplianceDrift] = []

            for finding in current_findings:
                if finding["id"] not in baseline_ids:
                    drift = ComplianceDrift(
                        finding_id=finding["id"],
                        issue_type=finding.get("issue_type", "unknown"),
                        resource=finding.get("resource", "unknown"),
                        severity=finding.get("severity", "medium"),
                        first_seen=datetime.utcnow(),
                        description=finding.get(
                            "description", "New security issue detected"
                        ),
                    )

                    action = self.generate_remediation(finding)
                    drift.remediation_action = action

                    drifts.append(drift)

            return drifts

        except Exception as e:
            raise RemediationError(
                f"Failed to detect compliance drift: {str(e)}"
            ) from e

    def _classify_issue(self, finding: Dict[str, Any]) -> str:
        """Classify the type of security issue."""
        title = finding.get("title", "").lower()
        description = finding.get("description", "").lower()
        rule_id = finding.get("rule_id", "").lower()

        combined_text = f"{title} {description} {rule_id}"

        if any(
            kw in combined_text
            for kw in ["password", "secret", "api key", "token", "credential"]
        ):
            return "hardcoded_secret"
        elif any(
            kw in combined_text
            for kw in [
                "security group",
                "0.0.0.0",  # Pattern for insecure network rule detection
                "open port",
                "firewall",
            ]
        ):
            return "open_security_group"
        elif any(
            kw in combined_text for kw in ["encryption", "md5", "sha1", "ssl", "tls"]
        ):
            return "weak_encryption"
        elif "terraform" in combined_text or finding.get("file", "").endswith(".tf"):
            return "terraform_misconfiguration"
        elif "dockerfile" in combined_text or finding.get("file", "").endswith(
            "Dockerfile"
        ):
            return "docker_misconfiguration"
        elif "kubernetes" in combined_text or finding.get("file", "").endswith(
            (".yaml", ".yml")
        ):
            return "kubernetes_misconfiguration"
        else:
            return "unknown"

    def _fix_hardcoded_secret(self, finding: Dict[str, Any]) -> RemediationAction:
        """Generate fix for hardcoded secrets."""
        file_path = Path(finding.get("file", ""))
        line_number = finding.get("line", 1)

        secret_name = self._extract_secret_name(finding)
        env_var_name = secret_name.upper().replace("-", "_")

        code_change = CodeChange(
            file_path=file_path,
            original_code=finding.get("code_snippet", ""),
            fixed_code=f'{secret_name} = os.getenv("{env_var_name}")',
            line_number=line_number,
            description=f"Replace hardcoded {secret_name} with environment variable",  # noqa: E501
        )

        return RemediationAction(
            finding_id=finding.get("id", "unknown"),
            remediation_type=RemediationType.AUTO_FIX,
            description="Replace hardcoded secret with environment variable",
            code_changes=[code_change],
            commands=[
                f"export {env_var_name}=<your-secret-value>",
                "# Store secret in your secrets management system",
            ],
            severity="critical",
            confidence=0.9,
            references=[
                "https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password",  # noqa: E501
                "https://cwe.mitre.org/data/definitions/798.html",
            ],
        )

    def _fix_open_security_group(self, finding: Dict[str, Any]) -> RemediationAction:
        """Generate fix for open security groups."""
        file_path = Path(finding.get("file", ""))
        line_number = finding.get("line", 1)

        original = finding.get("code_snippet", "")

        if "terraform" in str(file_path).lower() or file_path.suffix == ".tf":
            fixed = original.replace(
                '["0.0.0.0/0"]',
                '["10.0.0.0/8"]  # Restrict to private network',  # noqa: E501
            )
        elif "azure" in original.lower():
            fixed = original.replace('"*"', '"10.0.0.0/8"  # Restrict to VNet range')
        else:
            fixed = original.replace(
                "0.0.0.0/0", "10.0.0.0/8  # Restrict to known networks"
            )

        code_change = CodeChange(
            file_path=file_path,
            original_code=original,
            fixed_code=fixed,
            line_number=line_number,
            description="Restrict security group to specific IP ranges",
        )

        return RemediationAction(
            finding_id=finding.get("id", "unknown"),
            remediation_type=RemediationType.AUTO_FIX,
            description="Restrict overly permissive security group rules",
            code_changes=[code_change],
            severity="high",
            confidence=0.85,
            playbook_steps=[
                "Identify required IP ranges for access",
                "Update security group rules to specific CIDR blocks",
                "Test application connectivity",
                "Remove 0.0.0.0/0 rule",
            ],
            references=[
                "https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html",  # noqa: E501
            ],
        )

    def _fix_weak_encryption(self, finding: Dict[str, Any]) -> RemediationAction:
        """Generate fix for weak encryption."""
        file_path = Path(finding.get("file", ""))
        line_number = finding.get("line", 1)

        original = finding.get("code_snippet", "")
        fixed = original

        fixed = re.sub(
            r'algorithm\s*=\s*["\']MD5["\']',
            'algorithm = "SHA256"',
            fixed,
        )
        fixed = re.sub(
            r'algorithm\s*=\s*["\']SHA1["\']',
            'algorithm = "SHA256"',
            fixed,
        )
        fixed = re.sub(r"encryption\s*=\s*false", "encryption = true", fixed)
        fixed = re.sub(r"ssl_enabled\s*=\s*false", "ssl_enabled = true", fixed)

        code_change = CodeChange(
            file_path=file_path,
            original_code=original,
            fixed_code=fixed,
            line_number=line_number,
            description="Upgrade to strong encryption algorithm",
        )

        return RemediationAction(
            finding_id=finding.get("id", "unknown"),
            remediation_type=RemediationType.AUTO_FIX,
            description="Replace weak encryption with strong algorithm",
            code_changes=[code_change],
            severity="high",
            confidence=0.9,
            references=[
                "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/09-Testing_for_Weak_Cryptography/04-Testing_for_Weak_Encryption",  # noqa: E501
            ],
        )

    def _fix_terraform_issue(self, finding: Dict[str, Any]) -> RemediationAction:
        """Generate fix for Terraform issues."""
        file_path = Path(finding.get("file", ""))
        issue_type = finding.get("issue_type", "")

        changes = []

        if "s3" in issue_type.lower() and "encryption" in issue_type.lower():
            original = finding.get("code_snippet", "")
            fixed = (
                original
                + '\n\n  server_side_encryption_configuration {\n    rule {\n      apply_server_side_encryption_by_default {\n        sse_algorithm = "AES256"\n      }\n    }\n  }'  # noqa: E501
            )

            changes.append(
                CodeChange(
                    file_path=file_path,
                    original_code=original,
                    fixed_code=fixed,
                    line_number=finding.get("line", 1),
                    description="Enable S3 bucket encryption",
                )
            )

        elif "logging" in issue_type.lower():
            original = finding.get("code_snippet", "")
            fixed = (
                original
                + '\n\n  logging {\n    target_bucket = aws_s3_bucket.log_bucket.id\n    target_prefix = "log/"\n  }'  # noqa: E501
            )

            changes.append(
                CodeChange(
                    file_path=file_path,
                    original_code=original,
                    fixed_code=fixed,
                    line_number=finding.get("line", 1),
                    description="Enable logging",
                )
            )

        return RemediationAction(
            finding_id=finding.get("id", "unknown"),
            remediation_type=RemediationType.AUTO_FIX,
            description="Fix Terraform security misconfiguration",
            code_changes=changes,
            severity=finding.get("severity", "medium"),
            confidence=0.8,
        )

    def _fix_dockerfile_issue(self, finding: Dict[str, Any]) -> RemediationAction:
        """Generate fix for Dockerfile issues."""
        file_path = Path(finding.get("file", ""))
        original = finding.get("code_snippet", "")

        fixed = original

        if "root" in finding.get("description", "").lower():
            if "USER" not in original:
                fixed = original + "\n\nRUN useradd -m appuser\nUSER appuser"

        elif "latest" in original.lower():
            fixed = re.sub(
                r"FROM\s+(\w+):latest",
                r"FROM \1:1.0.0  # Pin to specific version",
                original,
            )

        code_change = CodeChange(
            file_path=file_path,
            original_code=original,
            fixed_code=fixed,
            line_number=finding.get("line", 1),
            description="Fix Dockerfile security issue",
        )

        return RemediationAction(
            finding_id=finding.get("id", "unknown"),
            remediation_type=RemediationType.AUTO_FIX,
            description="Fix Dockerfile security configuration",
            code_changes=[code_change],
            severity=finding.get("severity", "medium"),
            confidence=0.85,
        )

    def _fix_kubernetes_issue(self, finding: Dict[str, Any]) -> RemediationAction:
        """Generate fix for Kubernetes issues."""
        file_path = Path(finding.get("file", ""))
        original = finding.get("code_snippet", "")

        fixed = original
        fixed = re.sub(r"privileged:\s*true", "privileged: false", fixed)
        fixed = re.sub(r"runAsNonRoot:\s*false", "runAsNonRoot: true", fixed)

        code_change = CodeChange(
            file_path=file_path,
            original_code=original,
            fixed_code=fixed,
            line_number=finding.get("line", 1),
            description="Fix Kubernetes security configuration",
        )

        return RemediationAction(
            finding_id=finding.get("id", "unknown"),
            remediation_type=RemediationType.AUTO_FIX,
            description="Fix Kubernetes security issue",
            code_changes=[code_change],
            severity=finding.get("severity", "high"),
            confidence=0.8,
        )

    def _generate_manual_remediation(
        self, finding: Dict[str, Any]
    ) -> RemediationAction:
        """Generate manual remediation action."""
        return RemediationAction(
            finding_id=finding.get("id", "unknown"),
            remediation_type=RemediationType.MANUAL,
            description=f"Manual remediation required for: {finding.get('title', 'unknown issue')}",  # noqa: E501
            playbook_steps=[
                "Review the security finding details",
                "Identify the root cause of the issue",
                "Implement appropriate security controls",
                "Verify the fix resolves the issue",
                "Document changes made",
            ],
            severity=finding.get("severity", "medium"),
            confidence=0.5,
        )

    def _apply_code_changes(self, changes: List[CodeChange]) -> bool:
        """
        Apply code changes to files.

        Args:
            changes: List of code changes to apply

        Returns:
            True if all changes applied successfully, False otherwise
        """
        try:
            for change in changes:
                if not change.file_path.exists():
                    continue

                content = change.file_path.read_text()

                if change.original_code in content:
                    new_content = content.replace(
                        change.original_code, change.fixed_code
                    )
                    change.file_path.write_text(new_content)
                else:
                    return False

            return True

        except Exception:
            return False

    def _create_backup(self, changes: List[CodeChange]) -> Path:
        """
        Create backup of files before applying changes.

        Args:
            changes: List of code changes

        Returns:
            Path to backup directory
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = self.config.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        for change in changes:
            if change.file_path.exists():
                relative_path = change.file_path.relative_to(change.file_path.anchor)
                backup_file = backup_path / relative_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(change.file_path, backup_file)

        return backup_path

    def _create_github_pr(
        self, changes: List[CodeChange], repo: str, branch: str
    ) -> str:
        """
        Create GitHub pull request with fixes.

        Args:
            changes: List of code changes
            repo: Repository in format "owner/repo"
            branch: Branch name for PR

        Returns:
            URL of created pull request

        Raises:
            PRCreationError: If PR creation fails
        """
        if not self.config.github_token:
            raise PRCreationError("GitHub token not configured")

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo_path = Path(tmpdir) / "repo"

                subprocess.run(
                    [
                        "git",
                        "clone",
                        f"https://github.com/{repo}.git",
                        str(repo_path),
                    ],
                    check=True,
                    capture_output=True,
                )

                subprocess.run(
                    ["git", "checkout", "-b", branch],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                )

                for change in changes:
                    target_file = repo_path / change.file_path.name
                    if target_file.exists():
                        content = target_file.read_text()
                        new_content = content.replace(
                            change.original_code, change.fixed_code
                        )
                        target_file.write_text(new_content)

                subprocess.run(
                    ["git", "add", "."],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                )

                commit_message = (
                    "Security fixes: Automated remediation\n\n"
                    f"Applied {len(changes)} security fixes"
                )
                subprocess.run(
                    ["git", "commit", "-m", commit_message],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                )

                subprocess.run(
                    ["git", "push", "origin", branch],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    env={
                        **os.environ,
                        "GIT_ASKPASS": "echo",
                        "GIT_USERNAME": "x-access-token",
                        "GIT_PASSWORD": self.config.github_token,
                    },
                )

            pr_data = {
                "title": "Security Fixes: Automated Remediation",
                "body": self._generate_pr_body(changes),
                "head": branch,
                "base": "main",
            }

            headers = {
                "Authorization": f"token {self.config.github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            response = requests.post(
                f"https://api.github.com/repos/{repo}/pulls",
                json=pr_data,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            pr_url = response.json()["html_url"]
            return pr_url

        except subprocess.CalledProcessError as e:
            raise PRCreationError(f"Git operation failed: {e.stderr.decode()}") from e
        except requests.RequestException as e:
            raise PRCreationError(f"GitHub API request failed: {str(e)}") from e

    def _generate_pr_body(self, changes: List[CodeChange]) -> str:
        """Generate pull request body describing changes."""
        body = "## Security Fixes\n\n"
        body += (
            "This PR contains automated security fixes generated by the "
            "Infrastructure Security Scanner.\n\n"
        )
        body += "### Changes Applied\n\n"

        for i, change in enumerate(changes, 1):
            body += f"{i}. **{change.file_path.name}**: {change.description}\n"

        body += "\n### Verification\n\n"
        body += "- [ ] Review all code changes\n"
        body += "- [ ] Run security scans to verify fixes\n"
        body += "- [ ] Test application functionality\n"
        body += "- [ ] Update documentation if needed\n"

        return body

    def _extract_secret_name(self, finding: Dict[str, Any]) -> str:
        """Extract secret name from finding."""
        code = finding.get("code_snippet", "")

        patterns = [
            r'(\w+)\s*=\s*["\']',
            r"export\s+(\w+)=",
            r"ENV\s+(\w+)\s",
        ]

        for pattern in patterns:
            match = re.search(pattern, code, re.IGNORECASE)
            if match:
                return match.group(1)

        return "secret"

    def _extract_findings(self, scan_results: Dict[str, Any]) -> List[Dict]:
        """Extract findings from scan results."""
        findings = []

        if "findings" in scan_results:
            findings = scan_results["findings"]
        elif "results" in scan_results:
            findings = scan_results["results"]
        elif "issues" in scan_results:
            findings = scan_results["issues"]

        if not isinstance(findings, list):
            findings = []

        for finding in findings:
            if "id" not in finding:
                finding["id"] = str(hash(str(finding)))

        return findings

    def _get_secret_playbook_steps(self) -> List[str]:
        """Get playbook steps for hardcoded secret remediation."""
        return [
            "Identify all locations where the secret is hardcoded",
            "Choose a secrets management solution (AWS Secrets Manager, "
            "HashiCorp Vault, etc.)",
            "Store the secret in the secrets management system",
            "Update application code to retrieve secret from environment "
            "variable or secrets manager",
            "Remove hardcoded secret from code",
            "Update deployment configuration to inject secret",
            "Rotate the exposed secret to a new value",
            "Update secrets manager with new value",
            "Verify application works with new secret retrieval method",
        ]

    def _get_security_group_playbook_steps(self) -> List[str]:
        """Get playbook steps for security group remediation."""
        return [
            "Identify legitimate sources that require access",
            "Document required ports and protocols",
            "Create specific CIDR blocks for allowed sources",
            "Update security group rules to use specific IP ranges",
            "Remove overly permissive 0.0.0.0/0 rules",
            "Test application connectivity from allowed sources",
            "Verify blocked access from unauthorized sources",
            "Document security group configuration",
        ]

    def _get_encryption_playbook_steps(self) -> List[str]:
        """Get playbook steps for encryption remediation."""
        return [
            "Identify current encryption algorithm in use",
            "Select appropriate strong encryption algorithm (AES-256, "
            "SHA-256, etc.)",
            "Update configuration to use strong encryption",
            "Plan migration for existing encrypted data if needed",
            "Update application code to use new encryption settings",
            "Test encryption/decryption with new algorithm",
            "Migrate existing data to new encryption if applicable",
            "Verify compliance with encryption requirements",
        ]

    def _get_generic_playbook_steps(self, finding: Dict[str, Any]) -> List[str]:
        """Get generic playbook steps for unknown issues."""
        return [
            f"Review finding: {finding.get('title', 'Unknown issue')}",
            "Analyze the security impact and risk",
            "Research best practices for remediation",
            "Develop remediation plan",
            "Implement security controls",
            "Test the remediation",
            "Verify the issue is resolved",
            "Document the changes made",
        ]

    def _get_references_for_issue(self, issue_type: str) -> List[str]:
        """Get reference documentation for issue type."""
        references = {
            "hardcoded_secret": [
                "https://owasp.org/www-community/vulnerabilities/Use_of_hard-coded_password",  # noqa: E501
                "https://cwe.mitre.org/data/definitions/798.html",
                "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html",  # noqa: E501
            ],
            "open_security_group": [
                "https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html",  # noqa: E501
                "https://cloud.google.com/vpc/docs/using-firewalls",
                "https://docs.microsoft.com/en-us/azure/virtual-network/network-security-groups-overview",  # noqa: E501
            ],
            "weak_encryption": [
                "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/09-Testing_for_Weak_Cryptography/04-Testing_for_Weak_Encryption",  # noqa: E501
                "https://csrc.nist.gov/projects/cryptographic-standards-and-guidelines",  # noqa: E501
            ],
        }
        return references.get(issue_type, [])

    def _get_code_examples_for_issue(self, issue_type: str) -> Dict[str, str]:
        """Get code examples for issue type."""
        examples = {
            "hardcoded_secret": {
                "before": 'api_key = "hardcoded-secret-12345"',
                "after": 'api_key = os.getenv("API_KEY")',
            },
            "open_security_group": {
                "before": 'cidr_blocks = ["0.0.0.0/0"]',
                "after": 'cidr_blocks = ["10.0.0.0/8"]  # Private network only',  # noqa: E501
            },
            "weak_encryption": {
                "before": 'algorithm = "MD5"',
                "after": 'algorithm = "SHA256"',
            },
        }
        return examples.get(issue_type, {})
