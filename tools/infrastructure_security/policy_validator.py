"""
Policy Validator for Infrastructure Security Scanner Platform.

Implements OPA/Rego policy engine integration, custom policy enforcement,
CIS benchmark compliance checking, NIST/PCI-DSS framework mapping, and
policy-as-code governance with Terraform plan validation.

Part of devCrew_s1 Infrastructure Security Scanner Platform.
"""

import json
import logging
import subprocess
import tempfile
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


logger = logging.getLogger(__name__)


# ==================== Exceptions ====================


class PolicyValidationError(Exception):
    """Base exception for policy validation errors."""

    pass


class OPANotFoundError(PolicyValidationError):
    """OPA binary not found or not executable."""

    pass


class PolicyLoadError(PolicyValidationError):
    """Failed to load policy files."""

    pass


class InvalidRegoError(PolicyValidationError):
    """Invalid Rego policy syntax."""

    pass


class PolicyEvaluationError(PolicyValidationError):
    """Policy evaluation failed."""

    pass


# ==================== Enums ====================


class PolicyEngine(str, Enum):
    """Supported policy engines."""

    OPA = "opa"
    CHECKOV = "checkov"
    CUSTOM = "custom"


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""

    CIS_AWS = "cis_aws"
    CIS_AZURE = "cis_azure"
    CIS_GCP = "cis_gcp"
    NIST_800_53 = "nist_800_53"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"
    SOC2 = "soc2"


class Severity(str, Enum):
    """Violation severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ==================== Pydantic Models ====================


class PolicyConfig(BaseModel):
    """Policy validator configuration."""

    policy_path: str = Field(..., description="Path to policy files directory")
    engine: PolicyEngine = Field(
        default=PolicyEngine.OPA, description="Policy engine to use"
    )
    frameworks: List[ComplianceFramework] = Field(
        default_factory=list, description="Compliance frameworks to check"
    )
    fail_on_severity: Severity = Field(
        default=Severity.HIGH,
        description="Minimum severity to fail validation",
    )
    strict_mode: bool = Field(default=False, description="Fail on any violation")
    opa_binary: str = Field(default="opa", description="Path to OPA binary")
    checkov_binary: str = Field(default="checkov", description="Path to Checkov binary")
    timeout: int = Field(default=300, description="Policy evaluation timeout (seconds)")
    parallel_checks: bool = Field(default=True, description="Run checks in parallel")

    @validator("policy_path")
    def validate_policy_path(cls, v: str) -> str:
        """Validate policy path exists."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Policy path does not exist: {v}")
        return v


class PolicyViolation(BaseModel):
    """A single policy violation."""

    policy_id: str = Field(..., description="Policy identifier")
    title: str = Field(..., description="Violation title")
    severity: Severity = Field(..., description="Violation severity")
    description: str = Field(..., description="Detailed description")
    resource: str = Field(..., description="Affected resource")
    violated_rule: str = Field(..., description="Violated rule/check")
    remediation: str = Field(..., description="Remediation guidance")
    file_path: Optional[str] = Field(
        default=None, description="File containing violation"
    )
    line_number: Optional[int] = Field(
        default=None, description="Line number of violation"
    )
    framework: Optional[ComplianceFramework] = Field(
        default=None, description="Associated compliance framework"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_id": self.policy_id,
            "title": self.title,
            "severity": self.severity.value,
            "description": self.description,
            "resource": self.resource,
            "violated_rule": self.violated_rule,
            "remediation": self.remediation,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "framework": self.framework.value if self.framework else None,
            "metadata": self.metadata,
        }


class FrameworkResult(BaseModel):
    """Results for a specific compliance framework."""

    framework: ComplianceFramework = Field(..., description="Compliance framework")
    passed_checks: int = Field(default=0, description="Number of passed checks")
    failed_checks: int = Field(default=0, description="Number of failed checks")
    compliance_score: float = Field(default=0.0, description="Compliance score (0-100)")
    violations: List[PolicyViolation] = Field(
        default_factory=list, description="Framework violations"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "framework": self.framework.value,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "compliance_score": self.compliance_score,
            "violations": [v.to_dict() for v in self.violations],
        }


class PolicyResult(BaseModel):
    """Policy validation results."""

    violations: List[PolicyViolation] = Field(
        default_factory=list, description="All violations found"
    )
    passed_checks: int = Field(default=0, description="Number of passed checks")
    total_checks: int = Field(default=0, description="Total checks performed")
    compliance_score: float = Field(
        default=100.0, description="Overall compliance score (0-100)"
    )
    framework_results: Dict[str, FrameworkResult] = Field(
        default_factory=dict, description="Per-framework results"
    )
    evaluation_time: float = Field(default=0.0, description="Evaluation time (seconds)")
    engine: PolicyEngine = Field(default=PolicyEngine.OPA, description="Engine used")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @property
    def failed_checks(self) -> int:
        """Number of failed checks."""
        return len(self.violations)

    @property
    def critical_violations(self) -> List[PolicyViolation]:
        """Get critical violations."""
        return [v for v in self.violations if v.severity == Severity.CRITICAL]

    @property
    def high_violations(self) -> List[PolicyViolation]:
        """Get high severity violations."""
        return [v for v in self.violations if v.severity == Severity.HIGH]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "violations": [v.to_dict() for v in self.violations],
            "passed_checks": self.passed_checks,
            "total_checks": self.total_checks,
            "failed_checks": self.failed_checks,
            "compliance_score": self.compliance_score,
            "framework_results": {
                k: v.to_dict() for k, v in self.framework_results.items()
            },
            "evaluation_time": self.evaluation_time,
            "engine": self.engine.value,
            "metadata": self.metadata,
        }


class RegoPolicy(BaseModel):
    """OPA Rego policy definition."""

    package: str = Field(..., description="Rego package name")
    rules: List[str] = Field(default_factory=list, description="Policy rules")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Policy metadata"
    )
    content: str = Field(..., description="Full Rego policy content")
    file_path: Optional[str] = Field(default=None, description="Source file path")

    @validator("package")
    def validate_package(cls, v: str) -> str:
        """Validate package name format."""
        if not v or not v.replace(".", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid Rego package name: {v}")
        return v


# ==================== Policy Validator ====================


class PolicyValidator:
    """
    Policy validator with OPA/Rego engine integration.

    Provides comprehensive policy validation including OPA policy evaluation,
    Checkov custom policy enforcement, CIS benchmark compliance checking,
    and NIST/PCI-DSS framework mapping for infrastructure security.
    """

    def __init__(self, config: PolicyConfig) -> None:
        """
        Initialize policy validator.

        Args:
            config: Policy validator configuration

        Raises:
            OPANotFoundError: If OPA binary not found when using OPA engine
            PolicyLoadError: If policy files cannot be loaded
        """
        self.config = config
        self.policy_path = Path(config.policy_path)
        self.opa_binary = config.opa_binary
        self.checkov_binary = config.checkov_binary

        # Verify engine availability
        if config.engine == PolicyEngine.OPA:
            if not self.check_opa_installed():
                raise OPANotFoundError(f"OPA binary not found: {self.opa_binary}")

        # Load policies
        self._policies: Dict[str, RegoPolicy] = {}
        self._compliance_rules: Dict[ComplianceFramework, List[Dict[str, Any]]] = {}

        if config.engine == PolicyEngine.OPA:
            self._load_rego_policies(str(self.policy_path))

        self._load_compliance_mappings()

        logger.info(f"PolicyValidator initialized with {len(self._policies)} policies")

    def check_opa_installed(self) -> bool:
        """
        Verify OPA availability.

        Returns:
            True if OPA is installed and accessible
        """
        try:
            result = subprocess.run(  # nosec B603
                [self.opa_binary, "version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                logger.info(f"OPA version: {result.stdout.strip()}")
                return True
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def validate_opa(
        self, resources: Dict[str, Any], policy_package: str
    ) -> PolicyResult:
        """
        Validate resources with OPA/Rego policies.

        Args:
            resources: Resources to validate
            policy_package: OPA package to evaluate

        Returns:
            PolicyResult with validation results

        Raises:
            PolicyEvaluationError: If evaluation fails
        """
        start_time = time.time()

        try:
            # Run OPA evaluation
            opa_output = self._run_opa_eval(resources, policy_package)

            # Parse results
            violations = self._parse_opa_output(opa_output)

            # Create result
            result = PolicyResult(
                violations=violations,
                passed_checks=opa_output.get("passed_checks", 0),
                total_checks=len(violations) + opa_output.get("passed_checks", 0),
                engine=PolicyEngine.OPA,
                evaluation_time=time.time() - start_time,
                metadata={
                    "policy_package": policy_package,
                    "opa_version": self._get_opa_version(),
                },
            )

            # Calculate compliance score
            result.compliance_score = self._calculate_compliance_score(result)

            return result

        except Exception as e:
            raise PolicyEvaluationError(f"OPA evaluation failed: {e}") from e

    def validate_terraform_plan(
        self, plan_file: str, policy_package: str
    ) -> PolicyResult:
        """
        Validate Terraform plan with policies.

        Args:
            plan_file: Path to Terraform plan JSON file
            policy_package: OPA package to evaluate

        Returns:
            PolicyResult with validation results

        Raises:
            PolicyLoadError: If plan file cannot be loaded
            PolicyEvaluationError: If validation fails
        """
        plan_path = Path(plan_file)
        if not plan_path.exists():
            raise PolicyLoadError(f"Terraform plan not found: {plan_file}")

        try:
            with open(plan_path, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
        except json.JSONDecodeError as e:
            raise PolicyLoadError(f"Invalid JSON in plan file: {e}") from e

        # Extract resources from plan
        resources = self._extract_terraform_resources(plan_data)

        # Validate with OPA
        result = self.validate_opa(
            {"terraform_plan": plan_data, "resources": resources},
            policy_package,
        )

        result.metadata["terraform_plan"] = plan_file
        result.metadata["resource_count"] = len(resources)

        return result

    def validate_checkov_custom(self, path: str, policies: List[str]) -> PolicyResult:
        """
        Validate with Checkov custom policies.

        Args:
            path: Path to scan (directory or file)
            policies: List of custom policy paths

        Returns:
            PolicyResult with validation results

        Raises:
            PolicyEvaluationError: If Checkov execution fails
        """
        start_time = time.time()

        if not Path(path).exists():
            raise PolicyLoadError(f"Scan path does not exist: {path}")

        try:
            # Build Checkov command
            cmd = [
                self.checkov_binary,
                "-d" if Path(path).is_dir() else "-f",
                path,
                "--output",
                "json",
                "--quiet",
            ]

            # Add custom checks
            for policy in policies:
                cmd.extend(["--external-checks-dir", policy])

            # Execute Checkov
            result = subprocess.run(  # nosec B603
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                check=False,
            )

            # Parse Checkov output
            violations = self._parse_checkov_output(result.stdout)

            # Create result
            policy_result = PolicyResult(
                violations=violations,
                total_checks=len(violations),
                engine=PolicyEngine.CHECKOV,
                evaluation_time=time.time() - start_time,
                metadata={"scan_path": path, "custom_policies": policies},
            )

            policy_result.compliance_score = self._calculate_compliance_score(
                policy_result
            )

            return policy_result

        except subprocess.TimeoutExpired as e:
            raise PolicyEvaluationError(
                f"Checkov execution timed out after {self.config.timeout}s"
            ) from e
        except Exception as e:
            raise PolicyEvaluationError(f"Checkov execution failed: {e}") from e

    def evaluate_compliance(
        self, resources: Dict[str, Any], framework: ComplianceFramework
    ) -> PolicyResult:
        """
        Evaluate compliance against specific framework.

        Args:
            resources: Resources to evaluate
            framework: Compliance framework to check

        Returns:
            PolicyResult with compliance evaluation

        Raises:
            PolicyEvaluationError: If evaluation fails
        """
        start_time = time.time()

        if framework not in self._compliance_rules:
            raise PolicyValidationError(
                f"No rules loaded for framework: {framework.value}"
            )

        violations: List[PolicyViolation] = []
        passed_checks = 0
        rules = self._compliance_rules[framework]

        # Evaluate each compliance rule
        for rule in rules:
            rule_violations = self._evaluate_compliance_rule(resources, rule, framework)
            if rule_violations:
                violations.extend(rule_violations)
            else:
                passed_checks += 1

        # Create framework result
        framework_result = FrameworkResult(
            framework=framework,
            passed_checks=passed_checks,
            failed_checks=len(violations),
            compliance_score=0.0,
            violations=violations,
        )

        # Calculate framework score
        total = passed_checks + len(violations)
        if total > 0:
            framework_result.compliance_score = (passed_checks / total) * 100

        # Create overall result
        result = PolicyResult(
            violations=violations,
            passed_checks=passed_checks,
            total_checks=total,
            framework_results={framework.value: framework_result},
            engine=PolicyEngine.CUSTOM,
            evaluation_time=time.time() - start_time,
            metadata={"framework": framework.value},
        )

        result.compliance_score = framework_result.compliance_score

        return result

    def _run_opa_eval(
        self, input_data: Dict[str, Any], policy_package: str
    ) -> Dict[str, Any]:
        """
        Execute OPA eval command.

        Args:
            input_data: Input data for policy evaluation
            policy_package: OPA package name

        Returns:
            Parsed OPA output

        Raises:
            PolicyEvaluationError: If OPA execution fails
        """
        # Create temporary file for input
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(input_data, f)
            input_file = f.name

        try:
            # Build OPA command
            cmd = [
                self.opa_binary,
                "eval",
                "-d",
                str(self.policy_path),
                "-i",
                input_file,
                "--format",
                "json",
                f"data.{policy_package}",
            ]

            # Execute OPA
            result = subprocess.run(  # nosec B603
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout,
                check=False,
            )

            if result.returncode != 0:
                raise PolicyEvaluationError(f"OPA eval failed: {result.stderr}")

            # Parse output
            output = json.loads(result.stdout)
            return (
                output.get("result", [{}])[0]
                .get("expressions", [{}])[0]
                .get("value", {})
            )

        except subprocess.TimeoutExpired as e:
            raise PolicyEvaluationError(
                f"OPA eval timed out after {self.config.timeout}s"
            ) from e
        except json.JSONDecodeError as e:
            raise PolicyEvaluationError(f"Failed to parse OPA output: {e}") from e
        finally:
            # Clean up temp file
            Path(input_file).unlink(missing_ok=True)

    def _load_rego_policies(self, policy_path: str) -> None:
        """
        Load Rego policy files.

        Args:
            policy_path: Path to policy directory

        Raises:
            PolicyLoadError: If policies cannot be loaded
        """
        policy_dir = Path(policy_path)
        if not policy_dir.exists():
            raise PolicyLoadError(f"Policy directory not found: {policy_path}")

        rego_files = list(policy_dir.glob("**/*.rego"))

        for rego_file in rego_files:
            try:
                content = rego_file.read_text(encoding="utf-8")

                # Extract package name
                package = self._extract_package_name(content)
                if not package:
                    logger.warning(f"No package declaration in {rego_file}, skipping")
                    continue

                # Extract rules
                rules = self._extract_rego_rules(content)

                # Extract metadata
                metadata = self._extract_rego_metadata(content)

                policy = RegoPolicy(
                    package=package,
                    rules=rules,
                    metadata=metadata,
                    content=content,
                    file_path=str(rego_file),
                )

                self._policies[package] = policy
                logger.debug(f"Loaded policy: {package} from {rego_file}")

            except Exception as e:
                logger.error(f"Failed to load policy {rego_file}: {e}")
                raise PolicyLoadError(f"Error loading {rego_file}: {e}") from e

    def _parse_opa_output(self, output: Dict[str, Any]) -> List[PolicyViolation]:
        """
        Parse OPA evaluation output.

        Args:
            output: OPA eval output

        Returns:
            List of policy violations
        """
        violations: List[PolicyViolation] = []

        # Handle different OPA output formats
        deny_results = output.get("deny", [])
        if not isinstance(deny_results, list):
            deny_results = [deny_results]

        violations_data = output.get("violations", [])
        if not isinstance(violations_data, list):
            violations_data = [violations_data]

        # Parse deny results
        for deny in deny_results:
            if isinstance(deny, dict):
                violation = self._parse_opa_violation(deny)
                if violation:
                    violations.append(violation)
            elif isinstance(deny, str):
                violations.append(
                    PolicyViolation(
                        policy_id="opa_deny",
                        title="Policy Violation",
                        severity=Severity.HIGH,
                        description=deny,
                        resource="unknown",
                        violated_rule="deny",
                        remediation="Review policy violation",
                    )
                )

        # Parse structured violations
        for viol_data in violations_data:
            if isinstance(viol_data, dict):
                violation = self._parse_opa_violation(viol_data)
                if violation:
                    violations.append(violation)

        return violations

    def _parse_opa_violation(self, data: Dict[str, Any]) -> Optional[PolicyViolation]:
        """Parse a single OPA violation."""
        if not data:
            return None

        # Map severity
        severity_str = data.get("severity", "medium").lower()
        severity_map = {
            "critical": Severity.CRITICAL,
            "high": Severity.HIGH,
            "medium": Severity.MEDIUM,
            "low": Severity.LOW,
            "info": Severity.INFO,
        }
        severity = severity_map.get(severity_str, Severity.MEDIUM)

        return PolicyViolation(
            policy_id=data.get("policy_id", "opa_policy"),
            title=data.get("title", "Policy Violation"),
            severity=severity,
            description=data.get("description", data.get("msg", "")),
            resource=data.get("resource", "unknown"),
            violated_rule=data.get("rule", data.get("check", "unknown")),
            remediation=data.get("remediation", "Review and fix the violation"),
            file_path=data.get("file"),
            line_number=data.get("line"),
            metadata=data.get("metadata", {}),
        )

    def _calculate_compliance_score(self, result: PolicyResult) -> float:
        """
        Calculate overall compliance score.

        Args:
            result: Policy result to score

        Returns:
            Compliance score (0-100)
        """
        if result.total_checks == 0:
            return 100.0

        # Base score on passed checks
        base_score = (result.passed_checks / result.total_checks) * 100

        # Apply severity penalties
        critical_penalty = len(result.critical_violations) * 10
        high_penalty = len(result.high_violations) * 5

        score = base_score - critical_penalty - high_penalty
        return max(0.0, min(100.0, score))

    def _extract_package_name(self, content: str) -> Optional[str]:
        """Extract package name from Rego content."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("package "):
                return line[8:].strip()
        return None

    def _extract_rego_rules(self, content: str) -> List[str]:
        """Extract rule names from Rego content."""
        rules: List[str] = []
        for line in content.split("\n"):
            line = line.strip()
            # Match rule definitions: rule_name { or rule_name[x] {
            if "{" in line and not line.startswith("#"):
                parts = line.split("{")[0].strip().split()
                if parts and not parts[0] in [
                    "package",
                    "import",
                    "default",
                ]:
                    rule_name = parts[0].split("[")[0]
                    if rule_name and not rule_name.startswith("_"):
                        rules.append(rule_name)
        return list(set(rules))

    def _extract_rego_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata comments from Rego content."""
        metadata: Dict[str, Any] = {}
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# METADATA"):
                parts = line[11:].strip().split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip()
                    metadata[key] = value
        return metadata

    def _parse_checkov_output(self, output: str) -> List[PolicyViolation]:
        """Parse Checkov JSON output."""
        violations: List[PolicyViolation] = []

        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            logger.error("Failed to parse Checkov output")
            return violations

        # Checkov output format
        for result in data.get("results", {}).get("failed_checks", []):
            severity = self._map_checkov_severity(result.get("severity", "MEDIUM"))

            violation = PolicyViolation(
                policy_id=result.get("check_id", "checkov_check"),
                title=result.get("check_name", "Checkov Check Failed"),
                severity=severity,
                description=result.get("description", ""),
                resource=result.get("resource", "unknown"),
                violated_rule=result.get("check_class", "unknown"),
                remediation=result.get("guideline", "Review Checkov documentation"),
                file_path=result.get("file_path"),
                line_number=(
                    result.get("file_line_range", [0])[0]
                    if result.get("file_line_range")
                    else None
                ),
            )
            violations.append(violation)

        return violations

    def _map_checkov_severity(self, severity: str) -> Severity:
        """Map Checkov severity to internal severity."""
        severity_map = {
            "CRITICAL": Severity.CRITICAL,
            "HIGH": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
            "INFO": Severity.INFO,
        }
        return severity_map.get(severity.upper(), Severity.MEDIUM)

    def _extract_terraform_resources(
        self, plan_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract resources from Terraform plan."""
        resources: List[Dict[str, Any]] = []

        # Handle Terraform 0.12+ plan format
        resource_changes = plan_data.get("resource_changes", [])

        for change in resource_changes:
            resource = {
                "address": change.get("address", ""),
                "type": change.get("type", ""),
                "name": change.get("name", ""),
                "change": change.get("change", {}),
                "values": change.get("change", {}).get("after", {}),
            }
            resources.append(resource)

        return resources

    def _load_compliance_mappings(self) -> None:
        """Load compliance framework mappings."""
        # CIS AWS Benchmark rules
        self._compliance_rules[ComplianceFramework.CIS_AWS] = [
            {
                "id": "cis_aws_1.1",
                "title": "Avoid root account usage",
                "check": "root_account_usage",
                "severity": Severity.CRITICAL,
            },
            {
                "id": "cis_aws_2.1",
                "title": "Ensure CloudTrail is enabled",
                "check": "cloudtrail_enabled",
                "severity": Severity.HIGH,
            },
            {
                "id": "cis_aws_2.3",
                "title": "Ensure S3 bucket logging is enabled",
                "check": "s3_bucket_logging",
                "severity": Severity.MEDIUM,
            },
            {
                "id": "cis_aws_4.1",
                "title": "Ensure no security groups allow ingress 0.0.0.0/0",
                "check": "security_group_open_ingress",
                "severity": Severity.HIGH,
            },
        ]

        # NIST 800-53 controls
        self._compliance_rules[ComplianceFramework.NIST_800_53] = [
            {
                "id": "nist_ac_2",
                "title": "Account Management",
                "check": "account_management",
                "severity": Severity.HIGH,
            },
            {
                "id": "nist_au_2",
                "title": "Audit Events",
                "check": "audit_logging",
                "severity": Severity.HIGH,
            },
            {
                "id": "nist_sc_7",
                "title": "Boundary Protection",
                "check": "network_boundaries",
                "severity": Severity.HIGH,
            },
        ]

        # PCI-DSS requirements
        self._compliance_rules[ComplianceFramework.PCI_DSS] = [
            {
                "id": "pci_2.2.2",
                "title": "Enable only necessary services",
                "check": "necessary_services_only",
                "severity": Severity.HIGH,
            },
            {
                "id": "pci_8.2.1",
                "title": "Strong authentication",
                "check": "strong_authentication",
                "severity": Severity.CRITICAL,
            },
            {
                "id": "pci_10.1",
                "title": "Audit trails",
                "check": "audit_trails",
                "severity": Severity.HIGH,
            },
        ]

        # CIS Azure Benchmark
        self._compliance_rules[ComplianceFramework.CIS_AZURE] = [
            {
                "id": "cis_azure_1.1",
                "title": "Restrict access to Azure AD",
                "check": "azure_ad_access",
                "severity": Severity.HIGH,
            },
            {
                "id": "cis_azure_2.1",
                "title": "Enable Azure Security Center",
                "check": "security_center_enabled",
                "severity": Severity.HIGH,
            },
        ]

        # CIS GCP Benchmark
        self._compliance_rules[ComplianceFramework.CIS_GCP] = [
            {
                "id": "cis_gcp_1.1",
                "title": "Ensure Cloud Audit Logging",
                "check": "cloud_audit_logging",
                "severity": Severity.HIGH,
            },
            {
                "id": "cis_gcp_3.1",
                "title": "Ensure VPC Flow Logs",
                "check": "vpc_flow_logs",
                "severity": Severity.MEDIUM,
            },
        ]

    def _evaluate_compliance_rule(
        self,
        resources: Dict[str, Any],
        rule: Dict[str, Any],
        framework: ComplianceFramework,
    ) -> List[PolicyViolation]:
        """
        Evaluate a single compliance rule.

        Args:
            resources: Resources to check
            rule: Rule definition
            framework: Compliance framework

        Returns:
            List of violations (empty if passed)
        """
        check_name = rule["check"]
        violations: List[PolicyViolation] = []

        # Implement specific checks based on rule
        if check_name == "root_account_usage":
            violations.extend(self._check_root_account(resources, rule))
        elif check_name == "cloudtrail_enabled":
            violations.extend(self._check_cloudtrail(resources, rule))
        elif check_name == "s3_bucket_logging":
            violations.extend(self._check_s3_logging(resources, rule))
        elif check_name == "security_group_open_ingress":
            violations.extend(self._check_security_groups(resources, rule))
        # Add more checks as needed

        # Tag violations with framework
        for violation in violations:
            violation.framework = framework

        return violations

    def _check_root_account(
        self, resources: Dict[str, Any], rule: Dict[str, Any]
    ) -> List[PolicyViolation]:
        """Check for root account usage."""
        violations: List[PolicyViolation] = []

        # Example check logic
        iam_users = resources.get("iam_users", [])
        for user in iam_users:
            if user.get("name") == "root" and user.get("last_used"):
                violations.append(
                    PolicyViolation(
                        policy_id=rule["id"],
                        title=rule["title"],
                        severity=rule["severity"],
                        description="Root account has been used recently",
                        resource=f"IAM User: {user.get('arn', 'unknown')}",
                        violated_rule=rule["check"],
                        remediation="Avoid using root account",
                    )
                )

        return violations

    def _check_cloudtrail(
        self, resources: Dict[str, Any], rule: Dict[str, Any]
    ) -> List[PolicyViolation]:
        """Check CloudTrail configuration."""
        violations: List[PolicyViolation] = []

        cloudtrails = resources.get("cloudtrails", [])
        if not cloudtrails:
            violations.append(
                PolicyViolation(
                    policy_id=rule["id"],
                    title=rule["title"],
                    severity=rule["severity"],
                    description="No CloudTrail trails configured",
                    resource="CloudTrail",
                    violated_rule=rule["check"],
                    remediation="Enable CloudTrail in all regions",
                )
            )

        return violations

    def _check_s3_logging(
        self, resources: Dict[str, Any], rule: Dict[str, Any]
    ) -> List[PolicyViolation]:
        """Check S3 bucket logging."""
        violations: List[PolicyViolation] = []

        s3_buckets = resources.get("s3_buckets", [])
        for bucket in s3_buckets:
            if not bucket.get("logging_enabled"):
                violations.append(
                    PolicyViolation(
                        policy_id=rule["id"],
                        title=rule["title"],
                        severity=rule["severity"],
                        description="S3 bucket logging not enabled",
                        resource=f"S3 Bucket: {bucket.get('name', 'unknown')}",
                        violated_rule=rule["check"],
                        remediation="Enable server access logging for S3 bucket",
                    )
                )

        return violations

    def _check_security_groups(
        self, resources: Dict[str, Any], rule: Dict[str, Any]
    ) -> List[PolicyViolation]:
        """Check security group rules."""
        violations: List[PolicyViolation] = []

        security_groups = resources.get("security_groups", [])
        for sg in security_groups:
            for ingress_rule in sg.get("ingress_rules", []):
                if ingress_rule.get("cidr") == "0.0.0.0/0":
                    violations.append(
                        PolicyViolation(
                            policy_id=rule["id"],
                            title=rule["title"],
                            severity=rule["severity"],
                            description="Security group allows ingress from 0.0.0.0/0",
                            resource=f"Security Group: {sg.get('id', 'unknown')}",
                            violated_rule=rule["check"],
                            remediation="Restrict ingress to specific IP ranges",
                            metadata={
                                "port": ingress_rule.get("port"),
                                "protocol": ingress_rule.get("protocol"),
                            },
                        )
                    )

        return violations

    def _get_opa_version(self) -> str:
        """Get OPA version."""
        try:
            result = subprocess.run(  # nosec B603
                [self.opa_binary, "version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return "unknown"
