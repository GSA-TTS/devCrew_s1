"""
OpenAPI Specification Generator

Generates and manipulates OpenAPI 3.0/3.1 specifications from FastAPI
applications with support for custom examples, manual overrides, and
Pydantic model conversion.
"""

import copy
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from fastapi import FastAPI
    from fastapi.openapi.utils import get_openapi

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from pydantic import BaseModel
    from pydantic.json_schema import model_json_schema

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


logger = logging.getLogger(__name__)


class SpecGeneratorError(Exception):
    """Base exception for spec generation errors."""

    pass


class InvalidAppError(SpecGeneratorError):
    """Invalid or missing FastAPI application."""

    pass


class InvalidPathError(SpecGeneratorError):
    """Invalid path or method in specification."""

    pass


class FormatError(SpecGeneratorError):
    """Unsupported output format."""

    pass


class DependencyError(SpecGeneratorError):
    """Required dependency not available."""

    pass


class SpecGenerator:
    """
    OpenAPI Specification Generator for FastAPI applications.

    Provides comprehensive OpenAPI 3.0/3.1 specification generation with
    support for FastAPI route introspection, Pydantic model conversion,
    custom examples, and manual override merging.

    Attributes:
        spec: The OpenAPI specification dictionary
        openapi_version: OpenAPI specification version (3.0.x or 3.1.x)
    """

    SUPPORTED_FORMATS = {"json", "yaml"}
    OPENAPI_VERSIONS = {"3.0.0", "3.0.1", "3.0.2", "3.0.3", "3.1.0"}

    def __init__(self, openapi_version: str = "3.1.0"):
        """
        Initialize SpecGenerator.

        Args:
            openapi_version: OpenAPI specification version to use

        Raises:
            ValueError: If openapi_version is not supported
        """
        if openapi_version not in self.OPENAPI_VERSIONS:
            raise ValueError(
                f"Unsupported OpenAPI version: {openapi_version}. "
                f"Supported: {', '.join(sorted(self.OPENAPI_VERSIONS))}"
            )

        self.spec: Dict[str, Any] = {}
        self.openapi_version = openapi_version
        logger.info(
            "SpecGenerator initialized with OpenAPI %s",
            openapi_version,
        )

    def from_fastapi(
        self,
        app: "FastAPI",
        title: Optional[str] = None,
        version: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> "SpecGenerator":
        """
        Extract OpenAPI specification from FastAPI application.

        Uses FastAPI's built-in OpenAPI generation with customization
        support. This method leverages FastAPI's automatic route
        introspection and Pydantic model conversion to generate
        comprehensive specifications.

        Args:
            app: FastAPI application instance
            title: API title (overrides app.title)
            version: API version (overrides app.version)
            description: API description (overrides app.description)
            **kwargs: Additional OpenAPI specification fields

        Returns:
            Self for method chaining

        Raises:
            DependencyError: If FastAPI is not available
            InvalidAppError: If app is not a valid FastAPI instance
            SpecGeneratorError: If spec generation fails

        Example:
            >>> from fastapi import FastAPI
            >>> app = FastAPI()
            >>> generator = SpecGenerator()
            >>> generator.from_fastapi(
            ...     app,
            ...     title="My API",
            ...     version="1.0.0",
            ...     description="API documentation"
            ... )
        """
        if not FASTAPI_AVAILABLE:
            raise DependencyError(
                "FastAPI is not installed. Install with: pip install fastapi"
            )

        if not isinstance(app, FastAPI):
            raise InvalidAppError(
                f"Expected FastAPI instance, got {type(app).__name__}"
            )

        try:
            # Use FastAPI's built-in OpenAPI generation
            self.spec = get_openapi(
                title=title or app.title,
                version=version or app.version,
                description=description or app.description,
                routes=app.routes,
                tags=app.openapi_tags,
                servers=app.servers,
                terms_of_service=app.terms_of_service,
                contact=app.contact,
                license_info=app.license_info,
                openapi_version=self.openapi_version,
                **kwargs,
            )

            # Apply any custom OpenAPI modifications from the app
            if hasattr(app, "openapi_schema") and app.openapi_schema:
                self.spec = self._deep_merge(self.spec, app.openapi_schema)

            logger.info(
                "Generated OpenAPI spec from FastAPI app: %s paths found",
                len(self.spec.get("paths", {})),
            )

        except Exception as e:
            logger.error("Failed to generate OpenAPI spec: %s", str(e))
            raise SpecGeneratorError(f"Spec generation failed: {e}") from e

        return self

    def from_dict(self, spec: Dict[str, Any]) -> "SpecGenerator":
        """
        Load specification from dictionary.

        Args:
            spec: OpenAPI specification dictionary

        Returns:
            Self for method chaining

        Raises:
            ValueError: If spec is invalid

        Example:
            >>> spec = {
            ...     "openapi": "3.1.0",
            ...     "info": {"title": "API", "version": "1.0.0"},
            ...     "paths": {}
            ... }
            >>> generator = SpecGenerator()
            >>> generator.from_dict(spec)
        """
        if not isinstance(spec, dict):
            raise ValueError(f"Expected dict, got {type(spec).__name__}")

        if "openapi" not in spec:
            raise ValueError("Spec missing required 'openapi' field")

        if "info" not in spec:
            raise ValueError("Spec missing required 'info' field")

        self.spec = copy.deepcopy(spec)
        self.openapi_version = spec["openapi"]

        logger.info(
            "Loaded OpenAPI spec from dict: %s paths",
            len(self.spec.get("paths", {})),
        )

        return self

    def add_example(
        self,
        path: str,
        method: str,
        name: str,
        value: Dict[str, Any],
        location: str = "request",
        media_type: str = "application/json",
    ) -> "SpecGenerator":
        """
        Add custom example to specific endpoint.

        Examples are added to the OpenAPI specification in the appropriate
        location based on the OpenAPI version (3.0 vs 3.1 format
        differences).

        Args:
            path: API path (e.g., "/users/{id}")
            method: HTTP method (e.g., "get", "post")
            name: Example name/identifier
            value: Example value dictionary
            location: "request" or "response" or response code (e.g., "200")
            media_type: Media type for the example (default: application/json)

        Returns:
            Self for method chaining

        Raises:
            InvalidPathError: If path or method doesn't exist
            ValueError: If location is invalid

        Example:
            >>> generator.add_example(
            ...     "/users/{id}",
            ...     "get",
            ...     "success",
            ...     {"id": 1, "name": "John"},
            ...     location="200"
            ... )
        """
        method = method.lower()

        # Validate path and method exist
        if "paths" not in self.spec:
            raise InvalidPathError("Spec has no paths defined")

        if path not in self.spec["paths"]:
            raise InvalidPathError(f"Path not found: {path}")

        if method not in self.spec["paths"][path]:
            msg = f"Method not found: {method} for path {path}"
            raise InvalidPathError(msg)

        operation = self.spec["paths"][path][method]

        # Determine where to add the example
        if location == "request":
            self._add_request_example(operation, name, value, media_type)
        elif location == "response" or location.isdigit():
            response_code = "200" if location == "response" else location
            self._add_response_example(
                operation, response_code, name, value, media_type
            )
        else:
            raise ValueError(
                f"Invalid location: {location}. Use 'request', 'response', "
                "or response code (e.g., '200')"
            )

        logger.info(
            "Added example '%s' to %s %s (%s)",
            name,
            method.upper(),
            path,
            location,
        )

        return self

    def _add_request_example(
        self,
        operation: Dict[str, Any],
        name: str,
        value: Dict[str, Any],
        media_type: str,
    ) -> None:
        """Add example to request body."""
        if "requestBody" not in operation:
            operation["requestBody"] = {"content": {}}

        if "content" not in operation["requestBody"]:
            operation["requestBody"]["content"] = {}

        if media_type not in operation["requestBody"]["content"]:
            operation["requestBody"]["content"][media_type] = {"schema": {}}

        content = operation["requestBody"]["content"][media_type]

        # OpenAPI 3.0/3.1 format
        if "examples" not in content:
            content["examples"] = {}

        content["examples"][name] = {"value": value}

    def _add_response_example(
        self,
        operation: Dict[str, Any],
        response_code: str,
        name: str,
        value: Dict[str, Any],
        media_type: str,
    ) -> None:
        """Add example to response."""
        if "responses" not in operation:
            operation["responses"] = {}

        if response_code not in operation["responses"]:
            operation["responses"][response_code] = {
                "description": "",
                "content": {},
            }

        response = operation["responses"][response_code]

        if "content" not in response:
            response["content"] = {}

        if media_type not in response["content"]:
            response["content"][media_type] = {"schema": {}}

        content = response["content"][media_type]

        # OpenAPI 3.0/3.1 format
        if "examples" not in content:
            content["examples"] = {}

        content["examples"][name] = {"value": value}

    def add_override(self, path: str, data: Dict[str, Any]) -> "SpecGenerator":
        """
        Merge manual override data into specification.

        Uses deep merge strategy to combine override data with existing
        specification. Arrays are replaced, not merged. Useful for
        adding custom metadata, security schemes, or modifying generated
        content.

        Args:
            path: JSON pointer-style path (e.g., "/paths/~1users/get")
                  or dot notation (e.g., "paths./users.get")
            data: Override data to merge

        Returns:
            Self for method chaining

        Raises:
            ValueError: If path format is invalid

        Example:
            >>> generator.add_override(
            ...     "paths./users.get",
            ...     {"security": [{"bearer": []}]}
            ... )
            >>> generator.add_override(
            ...     "/components/securitySchemes",
            ...     {"bearer": {"type": "http", "scheme": "bearer"}},
            ... )
        """
        if not path:
            raise ValueError("Path cannot be empty")

        # Convert JSON pointer to dot notation if needed
        if path.startswith("/"):
            path = self._json_pointer_to_path(path)

        # Navigate to the target location
        parts = path.split(".")
        target = self.spec

        for i, part in enumerate(parts[:-1]):
            if part not in target:
                target[part] = {}
            target = target[part]

        # Merge the data at the final location
        final_key = parts[-1]
        if final_key in target and isinstance(target[final_key], dict):
            target[final_key] = self._deep_merge(target[final_key], data)
        else:
            target[final_key] = copy.deepcopy(data)

        logger.info("Applied override at path: %s", path)

        return self

    def _json_pointer_to_path(self, pointer: str) -> str:
        """
        Convert JSON pointer to dot notation path.

        Args:
            pointer: JSON pointer (e.g., "/paths/~1users/get")

        Returns:
            Dot notation path (e.g., "paths./users.get")
        """
        # Remove leading slash
        pointer = pointer.lstrip("/")

        # Replace escaped characters
        pointer = pointer.replace("~1", "/").replace("~0", "~")

        # Convert to dot notation
        return pointer.replace("/", ".")

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = copy.deepcopy(base)

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)

        return result

    def pydantic_to_schema(
        self, model: type["BaseModel"], **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Convert Pydantic model to JSON Schema.

        Args:
            model: Pydantic model class
            **kwargs: Additional arguments for schema generation

        Returns:
            JSON Schema dictionary

        Raises:
            DependencyError: If Pydantic is not available
            TypeError: If model is not a Pydantic model

        Example:
            >>> from pydantic import BaseModel
            >>> class User(BaseModel):
            ...     id: int
            ...     name: str
            >>> schema = generator.pydantic_to_schema(User)
        """
        if not PYDANTIC_AVAILABLE:
            msg = "Pydantic is not installed. Install with: pip install pydantic"
            raise DependencyError(msg)

        if not (isinstance(model, type) and issubclass(model, BaseModel)):
            msg = (
                f"Expected Pydantic BaseModel subclass, got " f"{type(model).__name__}"
            )
            raise TypeError(msg)

        try:
            schema = model_json_schema(model, **kwargs)
            logger.debug(
                "Converted Pydantic model %s to JSON Schema",
                model.__name__,
            )
            return schema
        except Exception as e:
            logger.error(
                "Failed to convert Pydantic model %s: %s",
                model.__name__,
                str(e),
            )
            raise

    def add_security_scheme(
        self, name: str, scheme_type: str, **kwargs: Any
    ) -> "SpecGenerator":
        """
        Add security scheme to specification.

        Args:
            name: Security scheme name
            scheme_type: Type (e.g., "http", "apiKey", "oauth2")
            **kwargs: Additional scheme parameters

        Returns:
            Self for method chaining

        Example:
            >>> generator.add_security_scheme(
            ...     "bearer",
            ...     "http",
            ...     scheme="bearer",
            ...     bearerFormat="JWT"
            ... )
        """
        if "components" not in self.spec:
            self.spec["components"] = {}

        if "securitySchemes" not in self.spec["components"]:
            self.spec["components"]["securitySchemes"] = {}

        scheme = {"type": scheme_type, **kwargs}
        self.spec["components"]["securitySchemes"][name] = scheme

        logger.info("Added security scheme: %s (%s)", name, scheme_type)

        return self

    def add_server(
        self, url: str, description: Optional[str] = None, **kwargs: Any
    ) -> "SpecGenerator":
        """
        Add server to specification.

        Args:
            url: Server URL
            description: Server description
            **kwargs: Additional server parameters

        Returns:
            Self for method chaining

        Example:
            >>> generator.add_server(
            ...     "https://api.example.com/v1",
            ...     "Production server"
            ... )
        """
        if "servers" not in self.spec:
            self.spec["servers"] = []

        server: Dict[str, Any] = {"url": url}
        if description:
            server["description"] = description

        server.update(kwargs)
        self.spec["servers"].append(server)

        logger.info("Added server: %s", url)

        return self

    def add_tag(
        self,
        name: str,
        description: Optional[str] = None,
        external_docs: Optional[Dict[str, str]] = None,
    ) -> "SpecGenerator":
        """
        Add tag to specification.

        Args:
            name: Tag name
            description: Tag description
            external_docs: External documentation link

        Returns:
            Self for method chaining

        Example:
            >>> generator.add_tag(
            ...     "users",
            ...     "User management endpoints",
            ...     {"url": "https://docs.example.com/users"}
            ... )
        """
        if "tags" not in self.spec:
            self.spec["tags"] = []

        tag: Dict[str, Any] = {"name": name}
        if description:
            tag["description"] = description
        if external_docs:
            tag["externalDocs"] = external_docs

        self.spec["tags"].append(tag)

        logger.info("Added tag: %s", name)

        return self

    def validate(self) -> List[str]:
        """
        Validate OpenAPI specification.

        Performs basic validation of required fields and structure.
        For comprehensive validation, use external tools like
        openapi-spec-validator.

        Returns:
            List of validation errors (empty if valid)

        Example:
            >>> errors = generator.validate()
            >>> if errors:
            ...     print("Validation errors:", errors)
        """
        errors = []

        # Check required root fields
        if "openapi" not in self.spec:
            errors.append("Missing required field: openapi")

        if "info" not in self.spec:
            errors.append("Missing required field: info")
        elif isinstance(self.spec["info"], dict):
            if "title" not in self.spec["info"]:
                errors.append("Missing required field: info.title")
            if "version" not in self.spec["info"]:
                errors.append("Missing required field: info.version")

        if "paths" not in self.spec:
            errors.append("Missing required field: paths")

        # Validate OpenAPI version format
        if "openapi" in self.spec:
            version = self.spec["openapi"]
            if not isinstance(version, str) or not version.startswith("3."):
                errors.append(f"Invalid OpenAPI version: {version}")

        # Validate paths structure
        if "paths" in self.spec and isinstance(self.spec["paths"], dict):
            for path, path_item in self.spec["paths"].items():
                if not isinstance(path_item, dict):
                    errors.append(f"Invalid path item at {path}")
                    continue

                # Check for valid HTTP methods
                valid_methods = {
                    "get",
                    "put",
                    "post",
                    "delete",
                    "options",
                    "head",
                    "patch",
                    "trace",
                }
                for key in path_item:
                    if key in valid_methods:
                        operation = path_item[key]
                        if not isinstance(operation, dict):
                            errors.append(f"Invalid operation at {path}.{key}")
                        elif "responses" not in operation:
                            errors.append(f"Missing responses at {path}.{key}")

        if errors:
            logger.warning(
                "Specification validation found %d errors",
                len(errors),
            )
        else:
            logger.info("Specification validation passed")

        return errors

    def save(
        self, filepath: Union[str, Path], format: str = "json", indent: int = 2
    ) -> Path:
        """
        Save specification to file.

        Args:
            filepath: Output file path
            format: Output format ("json" or "yaml")
            indent: Indentation spaces for JSON output

        Returns:
            Path to saved file

        Raises:
            FormatError: If format is not supported
            SpecGeneratorError: If save operation fails

        Example:
            >>> generator.save("openapi.json", format="json")
            >>> generator.save("openapi.yaml", format="yaml")
        """
        format = format.lower()

        if format not in self.SUPPORTED_FORMATS:
            raise FormatError(
                f"Unsupported format: {format}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        if format == "yaml" and not YAML_AVAILABLE:
            raise DependencyError(
                "PyYAML is not installed. Install with: pip install pyyaml"
            )

        filepath = Path(filepath)

        try:
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)

            if format == "json":
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(self.spec, f, indent=indent, ensure_ascii=False)
            elif format == "yaml":
                with open(filepath, "w", encoding="utf-8") as f:
                    yaml.dump(
                        self.spec,
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False,
                    )

            logger.info("Saved OpenAPI spec to %s (%s)", filepath, format)
            return filepath

        except Exception as e:
            logger.error("Failed to save spec to %s: %s", filepath, str(e))
            raise SpecGeneratorError(f"Failed to save spec: {e}") from e

    def to_dict(self) -> Dict[str, Any]:
        """
        Get specification as dictionary.

        Returns:
            Deep copy of the specification dictionary

        Example:
            >>> spec_dict = generator.to_dict()
            >>> print(spec_dict["info"]["title"])
        """
        return copy.deepcopy(self.spec)

    def to_json(self, indent: int = 2) -> str:
        """
        Get specification as JSON string.

        Args:
            indent: Indentation spaces

        Returns:
            JSON string representation

        Example:
            >>> json_str = generator.to_json(indent=2)
            >>> print(json_str)
        """
        return json.dumps(self.spec, indent=indent, ensure_ascii=False)

    def to_yaml(self) -> str:
        """
        Get specification as YAML string.

        Returns:
            YAML string representation

        Raises:
            DependencyError: If PyYAML is not available

        Example:
            >>> yaml_str = generator.to_yaml()
            >>> print(yaml_str)
        """
        if not YAML_AVAILABLE:
            raise DependencyError(
                "PyYAML is not installed. Install with: pip install pyyaml"
            )

        return yaml.dump(
            self.spec,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    def get_paths(self) -> List[str]:
        """
        Get list of all API paths.

        Returns:
            List of path strings

        Example:
            >>> paths = generator.get_paths()
            >>> print(paths)
            ['/users', '/users/{id}', '/posts']
        """
        return list(self.spec.get("paths", {}).keys())

    def get_operations(self) -> List[Dict[str, str]]:
        """
        Get list of all operations (path + method combinations).

        Returns:
            List of dicts with 'path' and 'method' keys

        Example:
            >>> operations = generator.get_operations()
            >>> for op in operations:
            ...     print(f"{op['method'].upper()} {op['path']}")
        """
        operations = []

        for path, path_item in self.spec.get("paths", {}).items():
            valid_methods = {
                "get",
                "put",
                "post",
                "delete",
                "options",
                "head",
                "patch",
                "trace",
            }

            for method in valid_methods:
                if method in path_item:
                    operations.append({"path": path, "method": method})

        return operations

    def clear(self) -> "SpecGenerator":
        """
        Clear the specification.

        Returns:
            Self for method chaining

        Example:
            >>> generator.clear()
        """
        self.spec = {}
        logger.info("Cleared specification")
        return self

    def __repr__(self) -> str:
        """String representation."""
        paths_count = len(self.spec.get("paths", {}))
        title = self.spec.get("info", {}).get("title", "Unknown")
        version = self.spec.get("info", {}).get("version", "Unknown")

        return (
            f"SpecGenerator(title='{title}', version='{version}', "
            f"paths={paths_count}, openapi='{self.openapi_version}')"
        )
