"""
Policy Validator for Rego and YAML policy syntax validation.

Provides comprehensive validation and testing framework for policies.
Part of devCrew_s1 TOOL-SEC-011 compliance management platform.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ValidationStatus(Enum):
    """Validation result status."""

    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


@dataclass
class ValidationIssue:
    """A single validation issue."""

    line: int
    column: int
    message: str
    severity: str  # error, warning, info
    rule: str


@dataclass
class ValidationResult:
    """Result of policy validation."""

    status: ValidationStatus
    policy_name: str
    policy_type: str  # rego, yaml
    issues: List[ValidationIssue] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "policy_name": self.policy_name,
            "policy_type": self.policy_type,
            "issues": [
                {
                    "line": i.line,
                    "column": i.column,
                    "message": i.message,
                    "severity": i.severity,
                    "rule": i.rule,
                }
                for i in self.issues
            ],
            "validated_at": self.validated_at.isoformat(),
            "metadata": self.metadata,
        }

    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return self.status == ValidationStatus.VALID

    @property
    def error_count(self) -> int:
        """Count of errors."""
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        """Count of warnings."""
        return sum(1 for i in self.issues if i.severity == "warning")


@dataclass
class PolicyTest:
    """A test case for policy validation."""

    name: str
    input_data: Dict[str, Any]
    expected_decision: str
    description: str = ""


@dataclass
class TestResult:
    """Result of a policy test execution."""

    test_name: str
    passed: bool
    expected: str
    actual: str
    duration_ms: float
    error_message: Optional[str] = None


class PolicyValidator:
    """
    Validates policy syntax and runs policy tests.

    Supports Rego and YAML policy formats with comprehensive
    syntax checking and test execution.
    """

    def __init__(self):
        self._rego_keywords = {
            "package", "import", "default", "as", "with", "not",
            "some", "every", "in", "if", "contains", "else",
        }
        self._yaml_schema_cache: Dict[str, Any] = {}

    def validate_rego(self, content: str, policy_name: str = "policy") -> ValidationResult:
        """
        Validate Rego policy syntax.

        Args:
            content: Rego policy content
            policy_name: Name of the policy

        Returns:
            ValidationResult with any issues found
        """
        issues: List[ValidationIssue] = []
        lines = content.split("\n")

        has_package = False
        brace_count = 0
        in_string = False

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            if not stripped or stripped.startswith("#"):
                continue

            if stripped.startswith("package "):
                has_package = True
                pkg_name = stripped[8:].strip()
                if not re.match(r"^[a-z][a-z0-9_.]*$", pkg_name):
                    issues.append(ValidationIssue(
                        line=line_num, column=9,
                        message=f"Invalid package name: {pkg_name}",
                        severity="error", rule="rego-package-name"
                    ))

            if stripped.startswith("import "):
                import_path = stripped[7:].strip()
                if not re.match(r"^(data|input|future)\.[a-z][a-z0-9_.]*", import_path):
                    if not import_path.startswith("rego."):
                        issues.append(ValidationIssue(
                            line=line_num, column=8,
                            message=f"Invalid import path: {import_path}",
                            severity="warning", rule="rego-import-path"
                        ))

            for char in stripped:
                if char == '"' and not in_string:
                    in_string = True
                elif char == '"' and in_string:
                    in_string = False
                elif char == "{" and not in_string:
                    brace_count += 1
                elif char == "}" and not in_string:
                    brace_count -= 1

            if ":=" in stripped:
                parts = stripped.split(":=")
                if len(parts) >= 2:
                    var_name = parts[0].strip()
                    if not re.match(r"^[a-z_][a-z0-9_]*$", var_name.split("[")[0]):
                        issues.append(ValidationIssue(
                            line=line_num, column=1,
                            message=f"Invalid variable name: {var_name}",
                            severity="warning", rule="rego-var-name"
                        ))

            if len(line) > 120:
                issues.append(ValidationIssue(
                    line=line_num, column=121,
                    message="Line exceeds 120 characters",
                    severity="warning", rule="line-length"
                ))

        if not has_package:
            issues.append(ValidationIssue(
                line=1, column=1,
                message="Missing package declaration",
                severity="error", rule="rego-package-required"
            ))

        if brace_count != 0:
            issues.append(ValidationIssue(
                line=len(lines), column=1,
                message=f"Unbalanced braces: {brace_count} unclosed",
                severity="error", rule="rego-brace-balance"
            ))

        has_errors = any(i.severity == "error" for i in issues)
        status = ValidationStatus.INVALID if has_errors else (
            ValidationStatus.WARNING if issues else ValidationStatus.VALID
        )

        return ValidationResult(
            status=status,
            policy_name=policy_name,
            policy_type="rego",
            issues=issues,
            metadata={"has_package": has_package, "line_count": len(lines)},
        )

    def validate_yaml(self, content: str, policy_name: str = "policy") -> ValidationResult:
        """
        Validate YAML policy syntax.

        Args:
            content: YAML policy content
            policy_name: Name of the policy

        Returns:
            ValidationResult with any issues found
        """
        issues: List[ValidationIssue] = []

        try:
            parsed = yaml.safe_load(content)
        except yaml.YAMLError as e:
            line = getattr(e, "problem_mark", None)
            line_num = line.line + 1 if line else 1
            col = line.column + 1 if line else 1
            issues.append(ValidationIssue(
                line=line_num, column=col,
                message=f"YAML syntax error: {str(e)}",
                severity="error", rule="yaml-syntax"
            ))
            return ValidationResult(
                status=ValidationStatus.INVALID,
                policy_name=policy_name,
                policy_type="yaml",
                issues=issues,
            )

        if parsed is None:
            issues.append(ValidationIssue(
                line=1, column=1,
                message="Empty YAML document",
                severity="warning", rule="yaml-empty"
            ))

        if isinstance(parsed, dict):
            self._validate_yaml_structure(parsed, issues)

        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            if len(line) > 120:
                issues.append(ValidationIssue(
                    line=line_num, column=121,
                    message="Line exceeds 120 characters",
                    severity="warning", rule="line-length"
                ))

            if line.rstrip() != line:
                issues.append(ValidationIssue(
                    line=line_num, column=len(line),
                    message="Trailing whitespace",
                    severity="warning", rule="trailing-whitespace"
                ))

        has_errors = any(i.severity == "error" for i in issues)
        status = ValidationStatus.INVALID if has_errors else (
            ValidationStatus.WARNING if issues else ValidationStatus.VALID
        )

        return ValidationResult(
            status=status,
            policy_name=policy_name,
            policy_type="yaml",
            issues=issues,
            metadata={"parsed": parsed is not None},
        )

    def _validate_yaml_structure(
        self, data: Dict[str, Any], issues: List[ValidationIssue]
    ) -> None:
        """Validate YAML policy structure."""
        expected_keys = {"version", "rules", "metadata", "name", "description"}
        for key in data.keys():
            if key not in expected_keys and not key.startswith("_"):
                issues.append(ValidationIssue(
                    line=1, column=1,
                    message=f"Unexpected top-level key: {key}",
                    severity="warning", rule="yaml-structure"
                ))

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate policy file based on extension."""
        if not file_path.exists():
            return ValidationResult(
                status=ValidationStatus.INVALID,
                policy_name=file_path.name,
                policy_type="unknown",
                issues=[ValidationIssue(
                    line=1, column=1,
                    message=f"File not found: {file_path}",
                    severity="error", rule="file-exists"
                )],
            )

        content = file_path.read_text()
        policy_name = file_path.stem

        if file_path.suffix in (".rego",):
            return self.validate_rego(content, policy_name)
        elif file_path.suffix in (".yaml", ".yml"):
            return self.validate_yaml(content, policy_name)
        else:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                policy_name=policy_name,
                policy_type="unknown",
                issues=[ValidationIssue(
                    line=1, column=1,
                    message=f"Unsupported file type: {file_path.suffix}",
                    severity="error", rule="file-type"
                )],
            )

    def run_tests(
        self, policy_content: str, tests: List[PolicyTest]
    ) -> List[TestResult]:
        """
        Run test cases against a policy.

        Args:
            policy_content: Policy content to test
            tests: List of test cases

        Returns:
            List of test results
        """
        from .policy_engine import PolicyEngine

        engine = PolicyEngine()
        engine.load_policy_from_string(policy_content, "test_policy")

        results: List[TestResult] = []

        for test in tests:
            import time
            start = time.time()

            try:
                result = engine.evaluate("test_policy", test.input_data)
                actual = result.decision.value
                passed = actual == test.expected_decision

                results.append(TestResult(
                    test_name=test.name,
                    passed=passed,
                    expected=test.expected_decision,
                    actual=actual,
                    duration_ms=(time.time() - start) * 1000,
                ))
            except Exception as e:
                results.append(TestResult(
                    test_name=test.name,
                    passed=False,
                    expected=test.expected_decision,
                    actual="error",
                    duration_ms=(time.time() - start) * 1000,
                    error_message=str(e),
                ))

        return results

    def create_test_from_yaml(self, yaml_content: str) -> List[PolicyTest]:
        """Parse test cases from YAML content."""
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError:
            return []

        tests: List[PolicyTest] = []
        test_cases = data.get("tests", []) if isinstance(data, dict) else []

        for tc in test_cases:
            if isinstance(tc, dict):
                tests.append(PolicyTest(
                    name=tc.get("name", "unnamed"),
                    input_data=tc.get("input", {}),
                    expected_decision=tc.get("expected", "allow"),
                    description=tc.get("description", ""),
                ))

        return tests
