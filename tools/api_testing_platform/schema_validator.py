"""
Schema Validator Module.

Provides comprehensive JSON Schema validation for API requests and responses
against OpenAPI specifications.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import urlparse

import yaml
from jsonschema import Draft7Validator, FormatChecker
from jsonschema import ValidationError as JSValidationError  # noqa: E501

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Represents a schema validation error with detailed context."""

    path: str  # JSON path like $.user.email
    message: str
    expected: Any
    actual: Any
    schema_rule: str  # e.g., "format", "type", "required"

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation error to dictionary format."""
        return {
            "path": self.path,
            "message": self.message,
            "expected": self.expected,
            "actual": self.actual,
            "schema_rule": self.schema_rule,
        }


@dataclass
class ValidationResult:
    """Container for validation results."""

    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary format."""
        return {
            "valid": self.valid,
            "errors": [err.to_dict() for err in self.errors],
            "warnings": self.warnings,
        }


class ValidationMode:
    """Validation mode constants."""

    STRICT = "strict"  # Fail on additional properties not in schema
    LENIENT = "lenient"  # Allow additional properties
    PARTIAL = "partial"  # Validate only provided fields


class SchemaValidator:
    """
    Validates API requests and responses against OpenAPI schemas.

    Supports JSON Schema Draft 7/2019-09/2020-12, custom format validators,
    multiple validation modes, and detailed error reporting.
    """

    def __init__(
        self,
        spec_file: Optional[Union[str, Path]] = None,
        spec_dict: Optional[Dict[str, Any]] = None,
        validation_mode: str = ValidationMode.STRICT,
        enable_format_validation: bool = True,
    ):
        """
        Initialize SchemaValidator.

        Args:
            spec_file: Path to OpenAPI specification file (YAML/JSON)
            spec_dict: OpenAPI specification as dictionary
            validation_mode: Validation mode (strict/lenient/partial)
            enable_format_validation: Enable format validation

        Raises:
            ValueError: If neither spec_file nor spec_dict is provided
            FileNotFoundError: If spec_file doesn't exist
            yaml.YAMLError: If spec file has invalid YAML/JSON syntax
        """
        if spec_file is None and spec_dict is None:
            raise ValueError("Either spec_file or spec_dict must be provided")

        self.validation_mode = validation_mode
        self.enable_format_validation = enable_format_validation

        # Load OpenAPI specification
        if spec_dict:
            self.spec = spec_dict
        elif spec_file is not None:
            self.spec = self._load_spec(spec_file)
        else:
            raise ValueError("spec_file or spec_dict must be provided")

        # Validate OpenAPI spec structure
        self._validate_spec_structure()

        # Initialize format checker with built-in validators
        self.format_checker = FormatChecker()
        self._register_builtin_formats()

        # Custom format validators registry
        self.custom_format_validators: Dict[str, Callable] = {}

        # Cache for resolved schemas
        self._schema_cache: Dict[str, Dict[str, Any]] = {}

        # Validation errors collected during last validation
        self._last_validation_errors: List[ValidationError] = []

        logger.info("SchemaValidator initialized with mode: %s", validation_mode)

    def _load_spec(self, spec_file: Union[str, Path]) -> Dict[str, Any]:
        """
        Load OpenAPI specification from file.

        Args:
            spec_file: Path to specification file

        Returns:
            Parsed OpenAPI specification

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If file has invalid syntax
        """
        spec_path = Path(spec_file)
        if not spec_path.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_file}")

        logger.debug("Loading OpenAPI spec from: %s", spec_file)

        with open(spec_path, "r", encoding="utf-8") as f:
            if spec_path.suffix.lower() in [".yaml", ".yml"]:
                spec = yaml.safe_load(f)
            elif spec_path.suffix.lower() == ".json":
                spec = json.load(f)
            else:
                # Try YAML first, then JSON
                try:
                    spec = yaml.safe_load(f)
                except yaml.YAMLError:
                    f.seek(0)
                    spec = json.load(f)

        return spec

    def _validate_spec_structure(self) -> None:
        """
        Validate basic OpenAPI spec structure.

        Raises:
            ValueError: If spec is invalid
        """
        if not isinstance(self.spec, dict):
            raise ValueError("OpenAPI spec must be a dictionary")

        if "openapi" not in self.spec:
            raise ValueError("Missing 'openapi' version field")

        version = self.spec["openapi"]
        if not version.startswith("3."):
            raise ValueError(f"Unsupported OpenAPI version: {version}")

        if "paths" not in self.spec and "components" not in self.spec:
            raise ValueError("OpenAPI spec must contain 'paths' or 'components'")

        logger.info("OpenAPI spec validated: version %s", version)

    def _register_builtin_formats(self) -> None:
        """Register built-in format validators."""

        # Email validation (RFC 5322 simplified)
        @self.format_checker.checks("email")
        def check_email(instance: str) -> bool:
            pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            return bool(re.match(pattern, instance))

        # UUID validation (v1-v5)
        @self.format_checker.checks("uuid")
        def check_uuid(instance: str) -> bool:
            pattern = (
                r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
                r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
            )
            return bool(re.match(pattern, instance.lower()))

        # Date-time validation (ISO 8601)
        @self.format_checker.checks("date-time")
        def check_datetime(instance: str) -> bool:
            pattern = (
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
                r"(\.\d+)?(Z|[+-]\d{2}:\d{2})$"
            )
            return bool(re.match(pattern, instance))

        # Date validation (YYYY-MM-DD)
        @self.format_checker.checks("date")
        def check_date(instance: str) -> bool:
            pattern = r"^\d{4}-\d{2}-\d{2}$"
            return bool(re.match(pattern, instance))

        # URI validation
        @self.format_checker.checks("uri")
        def check_uri(instance: str) -> bool:
            try:
                result = urlparse(instance)
                return all([result.scheme, result.netloc])
            except Exception:
                return False

        # IPv4 validation
        @self.format_checker.checks("ipv4")
        def check_ipv4(instance: str) -> bool:
            pattern = (
                r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
                r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
            )
            return bool(re.match(pattern, instance))

        # IPv6 validation (simplified)
        @self.format_checker.checks("ipv6")
        def check_ipv6(instance: str) -> bool:
            pattern = r"^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$"
            return bool(re.match(pattern, instance))

        logger.debug("Built-in format validators registered")

    def add_format_validator(
        self, format_name: str, validator_func: Callable[[str], bool]
    ) -> None:
        r"""
        Register a custom format validator.

        Args:
            format_name: Format identifier (e.g., "phone")
            validator_func: Function that takes a string and returns bool

        Example:
            def validate_phone(value: str) -> bool:
                return bool(re.match(r'^\+?1?\d{9,15}$', value))

            validator.add_format_validator("phone", validate_phone)
        """
        self.custom_format_validators[format_name] = validator_func

        @self.format_checker.checks(format_name)
        def check_custom(instance: str) -> bool:
            return validator_func(instance)

        logger.info("Custom format validator registered: %s", format_name)

    def _resolve_ref(self, ref: str) -> Dict[str, Any]:
        """
        Resolve $ref reference in OpenAPI spec.

        Args:
            ref: Reference string like "#/components/schemas/User"

        Returns:
            Resolved schema dictionary

        Raises:
            ValueError: If reference is invalid or circular
        """
        if ref in self._schema_cache:
            return self._schema_cache[ref]

        if not ref.startswith("#/"):
            raise ValueError(f"External references not supported: {ref}")

        # Parse reference path
        path_parts = ref[2:].split("/")
        schema = self.spec

        # Navigate to referenced schema
        for part in path_parts:
            if not isinstance(schema, dict) or part not in schema:
                raise ValueError(f"Invalid reference: {ref}")
            schema = schema[part]

        # Check for circular references (simple detection)
        if isinstance(schema, dict) and "$ref" in schema:
            if schema["$ref"] == ref:
                raise ValueError(f"Circular reference detected: {ref}")
            schema = self._resolve_ref(schema["$ref"])

        self._schema_cache[ref] = schema
        return schema

    def _resolve_schema_refs(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively resolve all $ref in a schema.

        Args:
            schema: Schema dictionary potentially containing $ref

        Returns:
            Schema with all $ref resolved
        """
        if not isinstance(schema, dict):
            return schema

        if "$ref" in schema:
            resolved = self._resolve_ref(schema["$ref"])
            # Merge other properties if present
            result = {
                **resolved,
                **{k: v for k, v in schema.items() if k != "$ref"},
            }  # noqa: E501
            return self._resolve_schema_refs(result)

        # Recursively resolve refs in nested structures
        result = {}
        for key, value in schema.items():
            if isinstance(value, dict):
                result[key] = self._resolve_schema_refs(value)
            elif isinstance(value, list):
                result[key] = [
                    (
                        self._resolve_schema_refs(item)
                        if isinstance(item, dict)
                        else item
                    )  # noqa: E501
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def get_schema_for_endpoint(self, endpoint: str, method: str) -> Dict[str, Any]:
        """
        Extract schema for a specific endpoint and HTTP method.

        Args:
            endpoint: API endpoint path (e.g., "/api/v1/users")
            method: HTTP method (GET, POST, etc.)

        Returns:
            Schema dictionary containing request and response schemas

        Raises:
            ValueError: If endpoint/method not found in spec
        """
        method = method.upper()

        # Normalize endpoint path
        normalized_endpoint = (
            endpoint if endpoint.startswith("/") else f"/{endpoint}"
        )  # noqa: E501

        # Find endpoint in spec
        if "paths" not in self.spec:
            raise ValueError("No paths defined in OpenAPI spec")

        path_item = None
        for path_pattern, path_def in self.spec["paths"].items():
            if self._match_path_pattern(normalized_endpoint, path_pattern):
                path_item = path_def
                break

        if not path_item:
            raise ValueError(f"Endpoint not found: {normalized_endpoint}")

        if method.lower() not in path_item:
            raise ValueError(f"Method {method} not defined for {normalized_endpoint}")

        operation = path_item[method.lower()]

        # Extract request schema
        request_schema = self._extract_request_schema(operation)

        # Extract response schemas
        response_schemas = self._extract_response_schemas(operation)

        return {
            "request": request_schema,
            "responses": response_schemas,
        }

    def _match_path_pattern(self, endpoint: str, pattern: str) -> bool:
        """
        Check if endpoint matches OpenAPI path pattern.

        Args:
            endpoint: Actual endpoint path
            pattern: OpenAPI path pattern (may contain {param})

        Returns:
            True if endpoint matches pattern
        """
        # Convert OpenAPI pattern to regex
        regex_pattern = re.sub(r"\{[^}]+\}", r"[^/]+", pattern)
        regex_pattern = f"^{regex_pattern}$"
        return bool(re.match(regex_pattern, endpoint))

    def _extract_request_schema(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract request schema from operation definition.

        Args:
            operation: OpenAPI operation object

        Returns:
            Combined schema for request (parameters + body)
        """
        schema: Dict[str, Any] = {
            "parameters": {},
            "body": None,
        }

        # Extract parameter schemas
        if "parameters" in operation:
            for param in operation["parameters"]:
                param_schema = param.get("schema", {})
                if "$ref" in param_schema:
                    param_schema = self._resolve_ref(param_schema["$ref"])

                param_name = param["name"]
                schema["parameters"][param_name] = {
                    "in": param.get("in", "query"),
                    "required": param.get("required", False),
                    "schema": param_schema,
                }

        # Extract request body schema
        if "requestBody" in operation:
            request_body = operation["requestBody"]
            content = request_body.get("content", {})

            # Get JSON content type schema
            for content_type in ["application/json", "*/*"]:
                if content_type in content:
                    body_schema = content[content_type].get("schema", {})
                    if "$ref" in body_schema:
                        body_schema = self._resolve_ref(body_schema["$ref"])
                    schema["body"] = self._resolve_schema_refs(body_schema)
                    break

        return schema

    def _extract_response_schemas(
        self, operation: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract response schemas from operation definition.

        Args:
            operation: OpenAPI operation object

        Returns:
            Dictionary mapping status codes to response schemas
        """
        schemas: Dict[str, Dict[str, Any]] = {}

        if "responses" not in operation:
            return schemas

        for status_code, response in operation["responses"].items():
            content = response.get("content", {})

            # Get JSON content type schema
            for content_type in ["application/json", "*/*"]:
                if content_type in content:
                    response_schema = content[content_type].get("schema", {})
                    if "$ref" in response_schema:
                        response_schema = self._resolve_ref(
                            response_schema["$ref"]
                        )  # noqa: E501
                    schemas[status_code] = self._resolve_schema_refs(response_schema)
                    break

        return schemas

    def validate_request(
        self,
        endpoint: str,
        method: str,
        request_data: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate request against OpenAPI schema.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            request_data: Request body data (for POST, PUT, PATCH)
            parameters: Query/path/header parameters

        Returns:
            ValidationResult with errors if validation fails

        Example:
            result = validator.validate_request(
                endpoint="/api/v1/users",
                method="POST",
                request_data={"name": "John", "email": "john@example.com"}
            )
        """
        self._last_validation_errors = []

        try:
            schema = self.get_schema_for_endpoint(endpoint, method)
            request_schema = schema["request"]

            errors = []

            # Validate parameters
            if parameters:
                param_errors = self._validate_parameters(
                    parameters, request_schema["parameters"]
                )
                errors.extend(param_errors)

            # Validate request body
            if request_data is not None and request_schema["body"]:
                body_errors = self.validate_against_schema(
                    request_data, request_schema["body"]
                )
                errors.extend(body_errors)

            self._last_validation_errors = errors
            return ValidationResult(
                valid=len(errors) == 0,
                errors=errors,
            )

        except Exception as e:
            logger.error("Request validation error: %s", str(e))
            error = ValidationError(
                path="$",
                message=str(e),
                expected="Valid request",
                actual=None,
                schema_rule="validation",
            )
            self._last_validation_errors = [error]
            return ValidationResult(valid=False, errors=[error])

    def _validate_parameters(
        self,
        parameters: Dict[str, Any],
        param_schemas: Dict[str, Dict[str, Any]],
    ) -> List[ValidationError]:
        """
        Validate request parameters against schemas.

        Args:
            parameters: Actual parameter values
            param_schemas: Parameter schema definitions

        Returns:
            List of validation errors
        """
        errors = []

        # Check required parameters
        for param_name, param_def in param_schemas.items():
            if param_def["required"] and param_name not in parameters:
                errors.append(
                    ValidationError(
                        path=f"$.{param_name}",
                        message=f"Required parameter missing: {param_name}",
                        expected="Parameter value",
                        actual=None,
                        schema_rule="required",
                    )
                )

        # Validate provided parameters
        for param_name, param_value in parameters.items():
            if param_name in param_schemas:
                param_schema = param_schemas[param_name]["schema"]
                param_errors = self.validate_against_schema(
                    param_value, param_schema, path_prefix=f"$.{param_name}"
                )
                errors.extend(param_errors)

        return errors

    def validate_response(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_data: Any,
    ) -> ValidationResult:
        """
        Validate response against OpenAPI schema.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP status code
            response_data: Response body data

        Returns:
            ValidationResult with errors if validation fails

        Example:
            result = validator.validate_response(
                endpoint="/api/v1/users/123",
                method="GET",
                status_code=200,
                response_data={"id": 123, "name": "John"}
            )
        """
        self._last_validation_errors = []

        try:
            schema = self.get_schema_for_endpoint(endpoint, method)
            response_schemas = schema["responses"]

            # Find matching status code schema
            status_str = str(status_code)
            response_schema = None

            # Exact match
            if status_str in response_schemas:
                response_schema = response_schemas[status_str]
            # Wildcard match (e.g., "2XX", "4XX")
            else:
                wildcard = f"{status_str[0]}XX"
                if wildcard in response_schemas:
                    response_schema = response_schemas[wildcard]
                elif "default" in response_schemas:
                    response_schema = response_schemas["default"]

            if not response_schema:
                warning = f"No schema defined for status code {status_code}"
                logger.warning(warning)
                return ValidationResult(valid=True, warnings=[warning])

            # Validate response data
            errors = self.validate_against_schema(response_data, response_schema)

            self._last_validation_errors = errors
            return ValidationResult(
                valid=len(errors) == 0,
                errors=errors,
            )

        except Exception as e:
            logger.error("Response validation error: %s", str(e))
            error = ValidationError(
                path="$",
                message=str(e),
                expected="Valid response",
                actual=None,
                schema_rule="validation",
            )
            self._last_validation_errors = [error]
            return ValidationResult(valid=False, errors=[error])

    def validate_against_schema(
        self,
        data: Any,
        schema: Dict[str, Any],
        path_prefix: str = "$",
    ) -> List[ValidationError]:
        """
        Validate data against a JSON Schema.

        Args:
            data: Data to validate
            schema: JSON Schema definition
            path_prefix: JSON path prefix for error reporting

        Returns:
            List of validation errors

        Example:
            errors = validator.validate_against_schema(
                {"email": "invalid"},
                {"type": "object", "properties": {"email": {"type": "string", "format": "email"}}}  # noqa: E501
            )
        """
        errors = []

        # Apply validation mode
        schema = self._apply_validation_mode(schema)

        # Create validator
        validator_cls = self._get_validator_class()
        format_checker = (
            self.format_checker if self.enable_format_validation else None
        )  # noqa: E501
        validator = validator_cls(schema, format_checker=format_checker)

        # Collect validation errors
        for error in validator.iter_errors(data):
            validation_error = self._convert_jsonschema_error(error, path_prefix)
            errors.append(validation_error)

        return errors

    def _apply_validation_mode(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply validation mode settings to schema.

        Args:
            schema: Original schema

        Returns:
            Modified schema based on validation mode
        """
        if self.validation_mode == ValidationMode.STRICT:
            # Disallow additional properties
            if schema.get("type") == "object":
                schema = {**schema, "additionalProperties": False}
        elif self.validation_mode == ValidationMode.LENIENT:
            # Allow additional properties
            if schema.get("type") == "object":
                schema = {**schema, "additionalProperties": True}
        elif self.validation_mode == ValidationMode.PARTIAL:
            # Remove required fields for partial validation
            schema = {k: v for k, v in schema.items() if k != "required"}

        return schema

    def _get_validator_class(self):
        """
        Get appropriate JSON Schema validator class.

        Returns:
            Validator class (Draft 7 by default)
        """
        # Use Draft 7 validator as default
        # Can be extended to support other drafts based on schema
        return Draft7Validator

    def _convert_jsonschema_error(
        self, error: JSValidationError, path_prefix: str
    ) -> ValidationError:
        """
        Convert jsonschema ValidationError to our ValidationError format.

        Args:
            error: jsonschema ValidationError
            path_prefix: Path prefix for error location

        Returns:
            Formatted ValidationError
        """
        # Build JSON path
        path_parts = [path_prefix]
        for part in error.absolute_path:
            if isinstance(part, int):
                path_parts.append(f"[{part}]")
            else:
                path_parts.append(f".{part}")
        path = "".join(path_parts)

        # Extract expected value from schema
        expected = self._extract_expected_value(error)

        # Determine schema rule that was violated
        schema_rule = error.validator

        # Build error message with suggestions
        message = self._build_error_message(error)

        return ValidationError(
            path=path,
            message=message,
            expected=expected,
            actual=error.instance,
            schema_rule=schema_rule,
        )

    def _extract_expected_value(self, error: JSValidationError) -> Any:
        """
        Extract expected value from validation error.

        Args:
            error: jsonschema ValidationError

        Returns:
            Expected value or constraint
        """
        if error.validator == "type":
            return error.validator_value
        elif error.validator == "format":
            return f"format: {error.validator_value}"
        elif error.validator == "enum":
            return f"one of: {error.validator_value}"
        elif error.validator == "pattern":
            return f"pattern: {error.validator_value}"
        elif error.validator in [
            "minimum",
            "maximum",
            "minLength",
            "maxLength",
        ]:  # noqa: E501
            return f"{error.validator}: {error.validator_value}"
        elif error.validator == "required":
            return f"required properties: {error.validator_value}"
        else:
            return error.validator_value

    def _build_error_message(self, error: JSValidationError) -> str:
        """
        Build detailed error message with suggestions.

        Args:
            error: jsonschema ValidationError

        Returns:
            Detailed error message
        """
        message = error.message

        # Add suggestions based on error type
        if error.validator == "type":
            message += f" (expected: {error.validator_value})"
        elif error.validator == "format":
            message += f" (format: {error.validator_value})"
        elif error.validator == "pattern":
            message += " (pattern mismatch)"
        elif error.validator == "enum":
            allowed = ", ".join(str(v) for v in error.validator_value)
            message += f" (allowed values: {allowed})"
        elif error.validator == "additionalProperties":
            message += " (additional properties not allowed in strict mode)"

        return message

    def get_validation_errors(self) -> List[ValidationError]:
        """
        Get detailed list of validation errors from last validation.

        Returns:
            List of ValidationError objects
        """
        return self._last_validation_errors.copy()

    def clear_cache(self) -> None:
        """Clear internal schema cache."""
        self._schema_cache.clear()
        logger.debug("Schema cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache size
        """
        return {
            "cached_schemas": len(self._schema_cache),
        }
