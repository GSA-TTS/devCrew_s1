"""Schema validation for configurations using JSON Schema and Pydantic."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union

import jsonschema
from pydantic import BaseModel, ValidationError


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)


class SchemaValidator:
    """Validator supporting JSON Schema, Pydantic models, and custom validators."""

    def __init__(self) -> None:
        """Initialize the schema validator."""
        self._custom_validators: Dict[str, Callable[[Any], ValidationResult]] = {}

    def validate_json_schema(
        self,
        config: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> ValidationResult:
        """Validate configuration against a JSON Schema.

        Args:
            config: Configuration dictionary to validate.
            schema: JSON Schema to validate against.

        Returns:
            ValidationResult with validation outcome.
        """
        result = ValidationResult(valid=True)
        validator = jsonschema.Draft7Validator(schema)

        for error in validator.iter_errors(config):
            path = ".".join(str(p) for p in error.absolute_path) or "root"
            result.add_error(f"{path}: {error.message}")

        return result

    def validate_json_schema_file(
        self,
        config: Dict[str, Any],
        schema_path: Union[str, Path],
    ) -> ValidationResult:
        """Validate configuration against a JSON Schema file.

        Args:
            config: Configuration dictionary to validate.
            schema_path: Path to JSON Schema file.

        Returns:
            ValidationResult with validation outcome.
        """
        import json

        path = Path(schema_path)
        if not path.exists():
            result = ValidationResult(valid=False)
            result.add_error(f"Schema file not found: {schema_path}")
            return result

        schema = json.loads(path.read_text(encoding="utf-8"))
        return self.validate_json_schema(config, schema)

    def validate_pydantic(
        self,
        config: Dict[str, Any],
        model: Type[BaseModel],
    ) -> ValidationResult:
        """Validate configuration against a Pydantic model.

        Args:
            config: Configuration dictionary to validate.
            model: Pydantic model class to validate against.

        Returns:
            ValidationResult with validation outcome.
        """
        result = ValidationResult(valid=True)

        try:
            model(**config)
        except ValidationError as e:
            for error in e.errors():
                loc = ".".join(str(loc) for loc in error["loc"])
                result.add_error(f"{loc}: {error['msg']}")

        return result

    def register_custom_validator(
        self,
        name: str,
        validator: Callable[[Any], ValidationResult],
    ) -> None:
        """Register a custom validator function.

        Args:
            name: Name to register the validator under.
            validator: Function that takes config and returns ValidationResult.
        """
        self._custom_validators[name] = validator

    def validate_custom(
        self,
        config: Dict[str, Any],
        validator_name: str,
    ) -> ValidationResult:
        """Run a registered custom validator.

        Args:
            config: Configuration dictionary to validate.
            validator_name: Name of the registered validator.

        Returns:
            ValidationResult with validation outcome.

        Raises:
            KeyError: If validator is not registered.
        """
        if validator_name not in self._custom_validators:
            raise KeyError(f"Custom validator not found: {validator_name}")
        return self._custom_validators[validator_name](config)

    def validate_all(
        self,
        config: Dict[str, Any],
        json_schema: Optional[Dict[str, Any]] = None,
        pydantic_model: Optional[Type[BaseModel]] = None,
        custom_validators: Optional[List[str]] = None,
    ) -> ValidationResult:
        """Run all specified validations.

        Args:
            config: Configuration dictionary to validate.
            json_schema: Optional JSON Schema.
            pydantic_model: Optional Pydantic model.
            custom_validators: List of custom validator names to run.

        Returns:
            Combined ValidationResult.
        """
        combined = ValidationResult(valid=True)

        if json_schema:
            result = self.validate_json_schema(config, json_schema)
            combined.errors.extend(result.errors)
            combined.warnings.extend(result.warnings)
            if not result.valid:
                combined.valid = False

        if pydantic_model:
            result = self.validate_pydantic(config, pydantic_model)
            combined.errors.extend(result.errors)
            combined.warnings.extend(result.warnings)
            if not result.valid:
                combined.valid = False

        for validator_name in custom_validators or []:
            result = self.validate_custom(config, validator_name)
            combined.errors.extend(result.errors)
            combined.warnings.extend(result.warnings)
            if not result.valid:
                combined.valid = False

        return combined


def create_required_fields_validator(
    required_fields: List[str],
) -> Callable[[Any], ValidationResult]:
    """Create a validator that checks for required fields.

    Args:
        required_fields: List of field paths that must exist.

    Returns:
        Validator function.
    """

    def validator(config: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult(valid=True)
        for field_path in required_fields:
            parts = field_path.split(".")
            current = config
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    result.add_error(f"Required field missing: {field_path}")
                    break
                current = current[part]
        return result

    return validator


def create_type_validator(
    field_types: Dict[str, type],
) -> Callable[[Any], ValidationResult]:
    """Create a validator that checks field types.

    Args:
        field_types: Mapping of field paths to expected types.

    Returns:
        Validator function.
    """

    def validator(config: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult(valid=True)
        for field_path, expected_type in field_types.items():
            parts = field_path.split(".")
            current = config
            for part in parts:
                if not isinstance(current, dict) or part not in current:
                    break
                current = current[part]
            else:
                if not isinstance(current, expected_type):
                    result.add_error(
                        f"{field_path}: expected {expected_type.__name__}, "
                        f"got {type(current).__name__}"
                    )
        return result

    return validator
