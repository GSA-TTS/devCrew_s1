"""
ContractValidator module for OpenAPI 3.0/3.1 specification validation.

This module provides comprehensive validation, linting, and compatibility
checking for OpenAPI specifications.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import yaml
from openapi_spec_validator import validate_spec
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError
from prance import ResolvingParser
from prance.util.url import ResolutionError

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    """Validation severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class CompatibilityIssueType(str, Enum):
    """Types of backward compatibility issues."""

    BREAKING = "breaking"
    DEPRECATED = "deprecated"
    ADDITIVE = "additive"


@dataclass
class ValidationError:
    """Represents a validation error with detailed context."""

    message: str
    path: str
    line: Optional[int] = None
    severity: Severity = Severity.ERROR
    rule: Optional[str] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message": self.message,
            "path": self.path,
            "line": self.line,
            "severity": self.severity.value,
            "rule": self.rule,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationWarning:
    """Represents a validation warning."""

    message: str
    path: str
    line: Optional[int] = None
    rule: Optional[str] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message": self.message,
            "path": self.path,
            "line": self.line,
            "rule": self.rule,
            "suggestion": self.suggestion,
        }


@dataclass
class CompatibilityIssue:
    """Represents a backward compatibility issue."""

    issue_type: CompatibilityIssueType
    path: str
    old_value: Any
    new_value: Any
    message: str
    severity: Severity = Severity.WARNING  # noqa: RUF009

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "issue_type": self.issue_type.value,
            "path": self.path,
            "old_value": str(self.old_value),
            "new_value": str(self.new_value),
            "message": self.message,
            "severity": self.severity.value,
        }


@dataclass
class ValidationResult:
    """Results of OpenAPI specification validation."""

    is_valid: bool
    spec_version: str
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationWarning] = field(default_factory=list)
    info: Dict[str, Any] = field(default_factory=dict)
    compatibility_issues: List[CompatibilityIssue] = field(
        default_factory=list
    )  # noqa: E501

    def add_error(
        self,
        message: str,
        path: str = "",
        line: Optional[int] = None,
        rule: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add a validation error."""
        self.errors.append(
            ValidationError(
                message=message,
                path=path,
                line=line,
                severity=Severity.ERROR,
                rule=rule,
                suggestion=suggestion,
            )
        )
        self.is_valid = False

    def add_warning(
        self,
        message: str,
        path: str = "",
        line: Optional[int] = None,
        rule: Optional[str] = None,
        suggestion: Optional[str] = None,
    ) -> None:
        """Add a validation warning."""
        self.warnings.append(
            ValidationWarning(
                message=message,
                path=path,
                line=line,
                rule=rule,
                suggestion=suggestion,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "is_valid": self.is_valid,
            "spec_version": self.spec_version,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "info": self.info,
            "compatibility_issues": [  # noqa: E501
                i.to_dict() for i in self.compatibility_issues
            ],
            "summary": {
                "total_errors": len(self.errors),
                "total_warnings": len(self.warnings),
                "total_compatibility_issues": len(
                    self.compatibility_issues
                ),  # noqa: E501
            },
        }


class LintRule:
    """Base class for linting rules."""

    def __init__(self, name: str, severity: Severity = Severity.WARNING):
        """Initialize linting rule."""
        self.name = name
        self.severity = severity

    def validate(self, spec: Dict[str, Any]) -> List[ValidationError]:
        """Validate specification against rule."""
        raise NotImplementedError


class EndpointNamingRule(LintRule):
    """Rule for endpoint naming conventions."""

    def __init__(
        self,
        pattern: str = r"^/[a-z0-9\-/{}]+$",
    ) -> None:
        """Initialize with naming pattern."""
        super().__init__("endpoint_naming", Severity.WARNING)
        self.pattern = re.compile(pattern)

    def validate(self, spec: Dict[str, Any]) -> List[ValidationError]:
        """Validate endpoint naming conventions."""
        errors = []
        paths = spec.get("paths", {})

        for path, _ in paths.items():
            if not self.pattern.match(path):
                errors.append(
                    ValidationError(
                        message=(
                            f"Endpoint path '{path}' does not follow "
                            "naming conventions"
                        ),
                        path=f"paths.{path}",
                        severity=self.severity,
                        rule=self.name,
                        suggestion=(
                            "Use lowercase letters, numbers, hyphens, and "
                            "path parameters"
                        ),
                    )
                )

        return errors


class SecuritySchemeRule(LintRule):
    """Rule for security scheme presence."""

    def __init__(self):
        """Initialize security scheme rule."""
        super().__init__("security_scheme", Severity.WARNING)

    def validate(self, spec: Dict[str, Any]) -> List[ValidationError]:
        """Validate security scheme presence."""
        errors = []

        if "components" not in spec or "securitySchemes" not in spec.get(
            "components", {}
        ):
            errors.append(
                ValidationError(
                    message="No security schemes defined",
                    path="components.securitySchemes",
                    severity=self.severity,
                    rule=self.name,
                    suggestion="Define at least one security scheme",
                )
            )

        return errors


class ResponseSchemaRule(LintRule):
    """Rule for response schema completeness."""

    def __init__(self):
        """Initialize response schema rule."""
        super().__init__("response_schema", Severity.WARNING)

    def validate(self, spec: Dict[str, Any]) -> List[ValidationError]:
        """Validate response schema completeness."""
        errors = []
        paths = spec.get("paths", {})

        for path_name, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if method.startswith("x-") or method in [
                    "parameters",
                    "servers",
                    "summary",
                    "description",
                ]:
                    continue

                if not isinstance(operation, dict):
                    continue

                responses = operation.get("responses", {})
                for status_code, response in responses.items():
                    if not isinstance(response, dict):
                        continue

                    if "content" not in response:
                        continue

                    content = response.get("content", {})
                    for media_type, media_obj in content.items():
                        if "schema" not in media_obj:
                            errors.append(
                                ValidationError(
                                    message=(
                                        f"Response {status_code} for "
                                        f"{method.upper()} {path_name} "
                                        f"missing schema for {media_type}"
                                    ),
                                    path=(
                                        f"paths.{path_name}.{method}."
                                        f"responses.{status_code}.content."
                                        f"{media_type}"
                                    ),
                                    severity=self.severity,
                                    rule=self.name,
                                    suggestion="Add schema definition",
                                )
                            )

        return errors


class ExampleDataRule(LintRule):
    """Rule for example data validation."""

    def __init__(self):
        """Initialize example data rule."""
        super().__init__("example_data", Severity.INFO)

    def validate(self, spec: Dict[str, Any]) -> List[ValidationError]:
        """Validate example data presence."""
        errors = []
        paths = spec.get("paths", {})
        skip_keys = ["parameters", "servers", "summary", "description"]

        for path_name, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if method.startswith("x-") or method in skip_keys:  # noqa: E501
                    continue

                if not isinstance(operation, dict):
                    continue

                responses = operation.get("responses", {})
                success_responses = [
                    code for code in responses.keys() if str(code).startswith("2")
                ]

                for status_code in success_responses:
                    response = responses[status_code]
                    if not isinstance(response, dict):
                        continue

                    content = response.get("content", {})
                    for media_type, media_obj in content.items():
                        no_example = "example" not in media_obj
                        no_examples = "examples" not in media_obj
                        if no_example and no_examples:
                            errors.append(
                                ValidationError(
                                    message=(
                                        f"Response {status_code} for "
                                        f"{method.upper()} {path_name} "
                                        f"missing example for {media_type}"
                                    ),
                                    path=(
                                        f"paths.{path_name}.{method}."
                                        f"responses.{status_code}.content."
                                        f"{media_type}"
                                    ),
                                    severity=self.severity,
                                    rule=self.name,
                                    suggestion="Add example or examples",
                                )
                            )

        return errors


class DeprecationWarningRule(LintRule):
    """Rule for deprecation warnings."""

    def __init__(self):
        """Initialize deprecation warning rule."""
        super().__init__("deprecation_warning", Severity.INFO)

    def validate(self, spec: Dict[str, Any]) -> List[ValidationError]:
        """Check for deprecated operations."""
        errors = []
        paths = spec.get("paths", {})

        for path_name, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if method.startswith("x-") or method in [
                    "parameters",
                    "servers",
                    "summary",
                    "description",
                ]:
                    continue

                if not isinstance(operation, dict):
                    continue

                if operation.get("deprecated", False):
                    errors.append(
                        ValidationError(
                            message=(
                                f"Operation {method.upper()} {path_name} "
                                "is deprecated"
                            ),
                            path=f"paths.{path_name}.{method}",
                            severity=self.severity,
                            rule=self.name,
                            suggestion="Consider migration plan",
                        )
                    )

        return errors


class ContractValidator:
    """
    OpenAPI 3.0/3.1 specification validator with linting and
    compatibility checking.
    """

    SUPPORTED_VERSIONS = ["3.0.0", "3.0.1", "3.0.2", "3.0.3", "3.1.0"]

    def __init__(self, strict: bool = False) -> None:
        """Initialize contract validator.

        Args:
            strict: If True, warnings are treated as errors
        """
        self.strict = strict
        self.default_rules: List[LintRule] = [
            EndpointNamingRule(),
            SecuritySchemeRule(),
            ResponseSchemaRule(),
            ExampleDataRule(),
            DeprecationWarningRule(),
        ]
        logger.info("ContractValidator initialized (strict=%s)", strict)

    def validate(self, spec_file: Union[str, Path]) -> ValidationResult:
        """Validate OpenAPI specification.

        Args:
            spec_file: Path to OpenAPI specification file (YAML or JSON)

        Returns:
            ValidationResult with detailed validation results
        """
        spec_path = Path(spec_file)
        logger.info("Validating specification: %s", spec_path)

        # Initialize result
        result = ValidationResult(is_valid=True, spec_version="unknown")

        # Check file exists
        if not spec_path.exists():
            result.add_error(
                message=f"Specification file not found: {spec_path}",
                path=str(spec_path),
            )
            return result

        # Load specification
        try:
            spec = self._load_spec(spec_path)
        except Exception as e:
            result.add_error(
                message=f"Failed to load specification: {str(e)}",
                path=str(spec_path),
            )
            return result

        # Check OpenAPI version
        openapi_version = spec.get("openapi", "")
        if not openapi_version:
            result.add_error(
                message="Missing 'openapi' version field",
                path="openapi",
                suggestion="Add 'openapi: 3.0.3' or 'openapi: 3.1.0'",
            )
            return result

        if openapi_version not in self.SUPPORTED_VERSIONS:
            result.add_error(
                message=(
                    f"Unsupported OpenAPI version: {openapi_version}. "
                    f"Supported: {', '.join(self.SUPPORTED_VERSIONS)}"
                ),
                path="openapi",
            )
            return result

        result.spec_version = openapi_version

        # Validate OpenAPI structure
        try:
            validate_spec(spec)  # type: ignore[arg-type]
            result.info["structure_valid"] = True
        except OpenAPIValidationError as e:
            result.add_error(
                message=str(e),
                path=self._extract_path_from_error(e),
                suggestion="Check OpenAPI 3.x specification",
            )
            result.info["structure_valid"] = False

        # Validate required fields
        self._validate_required_fields(spec, result)

        # Validate schema consistency
        self._validate_schema_consistency(spec, result)

        # Add metadata
        result.info.update(self._extract_spec_info(spec))

        logger.info(
            "Validation complete: %d errors, %d warnings",
            len(result.errors),
            len(result.warnings),
        )

        return result

    def lint(
        self,
        spec_file: Union[str, Path],
        rules: Optional[List[LintRule]] = None,
    ) -> ValidationResult:
        """Lint OpenAPI specification with custom rules.

        Args:
            spec_file: Path to OpenAPI specification file
            rules: Custom linting rules (uses defaults if None)

        Returns:
            ValidationResult with linting results
        """
        spec_path = Path(spec_file)
        logger.info("Linting specification: %s", spec_path)

        # First perform basic validation
        result = self.validate(spec_file)

        if not result.is_valid:
            logger.warning("Basic validation failed, skipping lint rules")
            return result

        # Load specification for linting
        spec = self._load_spec(spec_path)

        # Apply linting rules
        lint_rules = rules if rules is not None else self.default_rules

        for rule in lint_rules:
            try:
                rule_errors = rule.validate(spec)
                for error in rule_errors:
                    if error.severity == Severity.ERROR:
                        result.errors.append(error)
                        if self.strict:
                            result.is_valid = False
                    else:
                        result.warnings.append(
                            ValidationWarning(
                                message=error.message,
                                path=error.path,
                                line=error.line,
                                rule=error.rule,
                                suggestion=error.suggestion,
                            )
                        )
            except Exception as e:
                logger.error("Error applying rule %s: %s", rule.name, e)
                result.add_warning(
                    message=f"Failed to apply rule {rule.name}: {str(e)}",
                    path="",
                    rule=rule.name,
                )

        logger.info(
            "Linting complete: %d errors, %d warnings",
            len(result.errors),
            len(result.warnings),
        )

        return result

    def check_compatibility(
        self,
        old_spec: Union[str, Path],
        new_spec: Union[str, Path],
    ) -> ValidationResult:
        """Check backward compatibility between spec versions.

        Args:
            old_spec: Path to old OpenAPI specification
            new_spec: Path to new OpenAPI specification

        Returns:
            ValidationResult with compatibility issues
        """
        logger.info("Checking compatibility: %s -> %s", old_spec, new_spec)

        old_path = Path(old_spec)
        new_path = Path(new_spec)

        # Initialize result
        result = ValidationResult(is_valid=True, spec_version="comparison")

        # Load specifications
        try:
            old_data = self._load_spec(old_path)
            new_data = self._load_spec(new_path)
        except Exception as e:
            result.add_error(
                message=f"Failed to load specifications: {str(e)}",
                path="",
            )
            return result

        # Check paths
        self._check_paths_compatibility(old_data, new_data, result)

        # Check schemas
        self._check_schemas_compatibility(old_data, new_data, result)

        # Check security
        self._check_security_compatibility(old_data, new_data, result)

        # Determine overall compatibility
        breaking_changes = [
            issue
            for issue in result.compatibility_issues
            if issue.issue_type == CompatibilityIssueType.BREAKING
        ]

        if breaking_changes:
            result.is_valid = False
            result.add_error(
                message=(
                    f"Found {len(breaking_changes)} breaking changes "
                    "in new specification"
                ),
                path="",
            )

        logger.info(
            "Compatibility check complete: %d issues (%d breaking)",
            len(result.compatibility_issues),
            len(breaking_changes),
        )

        return result

    def resolve_refs(
        self,
        spec_file: Union[str, Path],
    ) -> Dict[str, Any]:
        """Resolve $ref references in specification.

        Args:
            spec_file: Path to OpenAPI specification file

        Returns:
            Resolved specification dictionary

        Raises:
            ValueError: If spec cannot be resolved
            ResolutionError: If circular references detected
        """
        spec_path = Path(spec_file)
        logger.info("Resolving $ref references: %s", spec_path)

        if not spec_path.exists():
            raise ValueError(f"Specification file not found: {spec_path}")

        try:
            parser = ResolvingParser(
                str(spec_path.absolute()),
                backend="openapi-spec-validator",
                strict=False,
            )
            resolved_spec = parser.specification
            logger.info("Successfully resolved all $ref references")
            return resolved_spec
        except ResolutionError as e:
            logger.error("Resolution error: %s", e)
            raise ResolutionError(f"Failed to resolve references: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error resolving refs: %s", e)
            raise ValueError(f"Failed to resolve references: {str(e)}")

    def get_validation_report(self, result: ValidationResult) -> str:
        """Generate detailed validation report.

        Args:
            result: ValidationResult to format

        Returns:
            Formatted validation report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("OpenAPI Specification Validation Report")
        lines.append("=" * 80)
        lines.append(f"Spec Version: {result.spec_version}")
        lines.append(f"Valid: {result.is_valid}")
        lines.append("")

        # Errors
        if result.errors:
            lines.append(f"ERRORS ({len(result.errors)}):")
            lines.append("-" * 80)
            for i, error in enumerate(result.errors, 1):
                severity_str = error.severity.value.upper()
                lines.append(f"{i}. [{severity_str}] {error.message}")
                if error.path:
                    lines.append(f"   Path: {error.path}")
                if error.line:
                    lines.append(f"   Line: {error.line}")
                if error.rule:
                    lines.append(f"   Rule: {error.rule}")
                if error.suggestion:
                    lines.append(f"   Suggestion: {error.suggestion}")
                lines.append("")

        # Warnings
        if result.warnings:
            lines.append(f"WARNINGS ({len(result.warnings)}):")
            lines.append("-" * 80)
            for i, warning in enumerate(result.warnings, 1):
                lines.append(f"{i}. {warning.message}")
                if warning.path:
                    lines.append(f"   Path: {warning.path}")
                if warning.line:
                    lines.append(f"   Line: {warning.line}")
                if warning.rule:
                    lines.append(f"   Rule: {warning.rule}")
                if warning.suggestion:
                    lines.append(f"   Suggestion: {warning.suggestion}")  # noqa: E501
                lines.append("")

        # Compatibility issues
        if result.compatibility_issues:  # noqa: E501
            compat_count = len(result.compatibility_issues)
            lines.append(f"COMPATIBILITY ISSUES ({compat_count}):")  # noqa: E501
            lines.append("-" * 80)
            for i, issue in enumerate(result.compatibility_issues, 1):
                lines.append(f"{i}. [{issue.issue_type.value.upper()}] {issue.message}")
                lines.append(f"   Path: {issue.path}")
                lines.append(f"   Old: {issue.old_value}")
                lines.append(f"   New: {issue.new_value}")
                lines.append("")

        # Info
        if result.info:
            lines.append("METADATA:")
            lines.append("-" * 80)
            for key, value in result.info.items():
                lines.append(f"{key}: {value}")

        lines.append("=" * 80)

        return "\n".join(lines)

    def _load_spec(self, spec_path: Path) -> Dict[str, Any]:
        """Load OpenAPI specification from file.

        Args:
            spec_path: Path to specification file

        Returns:
            Parsed specification dictionary

        Raises:
            ValueError: If file format is invalid
        """
        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Try YAML first
            if spec_path.suffix in [".yaml", ".yml"]:
                return yaml.safe_load(content)
            elif spec_path.suffix == ".json":
                return json.loads(content)
            else:
                # Try both
                try:
                    return yaml.safe_load(content)
                except yaml.YAMLError:
                    return json.loads(content)

        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid YAML/JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to load specification: {str(e)}")

    def _extract_path_from_error(self, error: Exception) -> str:
        """Extract JSON path from validation error.

        Args:
            error: Validation exception

        Returns:
            JSON path string
        """
        error_str = str(error)

        # Try to extract path from error message
        if "at" in error_str:
            parts = error_str.split("at")
            if len(parts) > 1:
                path = parts[-1].strip()
                return path.strip("'\"")

        return ""

    def _validate_required_fields(
        self,
        spec: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Validate required OpenAPI fields.

        Args:
            spec: OpenAPI specification dictionary
            result: ValidationResult to update
        """
        # Check info section
        if "info" not in spec:
            result.add_error(
                message="Missing required 'info' section",
                path="info",
                suggestion="Add info section with title and version",
            )
        else:
            info = spec["info"]
            if "title" not in info:
                result.add_error(
                    message="Missing required 'info.title'",
                    path="info.title",
                )
            if "version" not in info:
                result.add_error(
                    message="Missing required 'info.version'",
                    path="info.version",
                )

        # Check paths
        if "paths" not in spec or not spec["paths"]:
            result.add_error(
                message="Missing or empty 'paths' section",
                path="paths",
                suggestion="Define at least one API endpoint",
            )

    def _validate_schema_consistency(
        self,
        spec: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Validate schema consistency across specification.

        Args:
            spec: OpenAPI specification dictionary
            result: ValidationResult to update
        """
        # Collect all schema references
        schema_refs: Set[str] = set()
        defined_schemas: Set[str] = set()

        # Get defined schemas
        components = spec.get("components", {})
        schemas = components.get("schemas", {})
        defined_schemas = set(schemas.keys())

        # Find schema references in paths
        paths = spec.get("paths", {})
        for path_name, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if not isinstance(operation, dict):
                    continue

                # Check request body
                request_body = operation.get("requestBody", {})
                if isinstance(request_body, dict):
                    self._extract_schema_refs(request_body, schema_refs)

                # Check responses
                responses = operation.get("responses", {})
                for response in responses.values():
                    if isinstance(response, dict):
                        self._extract_schema_refs(response, schema_refs)

        # Check for undefined schema references
        for ref in schema_refs:
            if ref.startswith("#/components/schemas/"):
                schema_name = ref.split("/")[-1]
                if schema_name not in defined_schemas:
                    suggestion_msg = (  # noqa: E501
                        f"Define schema in components.schemas." f"{schema_name}"
                    )
                    result.add_error(
                        message=(
                            f"Undefined schema reference: {schema_name}"
                        ),  # noqa: E501
                        path=ref,
                        suggestion=suggestion_msg,
                    )

    def _extract_schema_refs(
        self,
        obj: Any,
        refs: Set[str],
    ) -> None:
        """Recursively extract schema references.

        Args:
            obj: Object to search
            refs: Set to add references to
        """
        if isinstance(obj, dict):
            if "$ref" in obj:
                refs.add(obj["$ref"])
            for value in obj.values():
                self._extract_schema_refs(value, refs)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_schema_refs(item, refs)

    def _extract_spec_info(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from specification.

        Args:
            spec: OpenAPI specification dictionary

        Returns:
            Metadata dictionary
        """
        info = spec.get("info", {})
        paths = spec.get("paths", {})

        endpoint_count = 0
        operations_count = 0

        http_methods = [
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "options",
            "head",
            "trace",
        ]

        for path_item in paths.values():
            if isinstance(path_item, dict):
                endpoint_count += 1
                for key in path_item.keys():
                    if key in http_methods:
                        operations_count += 1

        return {
            "title": info.get("title", "Unknown"),
            "version": info.get("version", "Unknown"),
            "description": info.get("description", ""),
            "endpoint_count": endpoint_count,
            "operations_count": operations_count,
            "has_servers": "servers" in spec,
            "has_security": (  # noqa: E501
                "security" in spec or "securitySchemes" in spec.get("components", {})
            ),
        }

    def _check_paths_compatibility(
        self,
        old_spec: Dict[str, Any],
        new_spec: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Check path compatibility between versions.

        Args:
            old_spec: Old specification
            new_spec: New specification
            result: ValidationResult to update
        """
        old_paths = old_spec.get("paths", {})
        new_paths = new_spec.get("paths", {})

        # Check for removed paths
        for path in old_paths:
            if path not in new_paths:
                result.compatibility_issues.append(
                    CompatibilityIssue(
                        issue_type=CompatibilityIssueType.BREAKING,
                        path=f"paths.{path}",
                        old_value="exists",
                        new_value="removed",
                        message=f"Path {path} was removed",
                        severity=Severity.ERROR,
                    )
                )

        # Check for removed operations
        for path in set(old_paths.keys()) & set(new_paths.keys()):
            old_methods = set(old_paths[path].keys())
            new_methods = set(new_paths[path].keys())

            for method in old_methods:
                if method in ["get", "post", "put", "patch", "delete"]:
                    if method not in new_methods:
                        msg = (  # noqa: E501
                            f"Operation {method.upper()} {path} " "was removed"
                        )
                        result.compatibility_issues.append(
                            CompatibilityIssue(
                                issue_type=CompatibilityIssueType.BREAKING,
                                path=f"paths.{path}.{method}",
                                old_value="exists",
                                new_value="removed",
                                message=msg,
                                severity=Severity.ERROR,
                            )
                        )

        # Check for new paths (additive change)
        for path in new_paths:
            if path not in old_paths:
                result.compatibility_issues.append(
                    CompatibilityIssue(
                        issue_type=CompatibilityIssueType.ADDITIVE,
                        path=f"paths.{path}",
                        old_value="none",
                        new_value="added",
                        message=f"New path {path} was added",
                        severity=Severity.INFO,
                    )
                )

    def _check_schemas_compatibility(
        self,
        old_spec: Dict[str, Any],
        new_spec: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Check schema compatibility between versions.

        Args:
            old_spec: Old specification
            new_spec: New specification
            result: ValidationResult to update
        """
        old_schemas = old_spec.get("components", {}).get("schemas", {})
        new_schemas = new_spec.get("components", {}).get("schemas", {})

        # Check for removed schemas
        for schema_name in old_schemas:
            if schema_name not in new_schemas:
                result.compatibility_issues.append(
                    CompatibilityIssue(
                        issue_type=CompatibilityIssueType.BREAKING,
                        path=f"components.schemas.{schema_name}",
                        old_value="exists",
                        new_value="removed",
                        message=f"Schema {schema_name} was removed",
                        severity=Severity.ERROR,
                    )
                )

        # Check for schema changes
        for schema_name in set(old_schemas.keys()) & set(new_schemas.keys()):
            old_schema = old_schemas[schema_name]
            new_schema = new_schemas[schema_name]

            self._check_schema_properties(
                schema_name,
                old_schema,
                new_schema,
                result,
            )

    def _check_schema_properties(
        self,
        schema_name: str,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Check schema property compatibility.

        Args:
            schema_name: Name of schema
            old_schema: Old schema definition
            new_schema: New schema definition
            result: ValidationResult to update
        """
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))

        # Check for new required fields (breaking change)
        newly_required = new_required - old_required
        if newly_required:
            result.compatibility_issues.append(
                CompatibilityIssue(
                    issue_type=CompatibilityIssueType.BREAKING,
                    path=f"components.schemas.{schema_name}.required",
                    old_value=list(old_required),
                    new_value=list(new_required),
                    message=(
                        f"Schema {schema_name} has new required fields: "
                        f"{', '.join(newly_required)}"
                    ),
                    severity=Severity.ERROR,
                )
            )

        # Check for removed properties
        old_props = set(old_schema.get("properties", {}).keys())
        new_props = set(new_schema.get("properties", {}).keys())

        removed_props = old_props - new_props
        if removed_props:
            result.compatibility_issues.append(
                CompatibilityIssue(
                    issue_type=CompatibilityIssueType.BREAKING,
                    path=f"components.schemas.{schema_name}.properties",
                    old_value=list(old_props),
                    new_value=list(new_props),
                    message=(
                        f"Schema {schema_name} has removed properties: "
                        f"{', '.join(removed_props)}"
                    ),
                    severity=Severity.ERROR,
                )
            )

    def _check_security_compatibility(
        self,
        old_spec: Dict[str, Any],
        new_spec: Dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Check security scheme compatibility.

        Args:
            old_spec: Old specification
            new_spec: New specification
            result: ValidationResult to update
        """
        old_components = old_spec.get("components", {})
        old_security = old_components.get("securitySchemes", {})
        new_components = new_spec.get("components", {})
        new_security = new_components.get("securitySchemes", {})

        # Check for removed security schemes
        for scheme_name in old_security:
            if scheme_name not in new_security:
                result.compatibility_issues.append(
                    CompatibilityIssue(
                        issue_type=CompatibilityIssueType.BREAKING,
                        path=f"components.securitySchemes.{scheme_name}",
                        old_value="exists",
                        new_value="removed",
                        message=f"Security scheme {scheme_name} was removed",
                        severity=Severity.ERROR,
                    )
                )
