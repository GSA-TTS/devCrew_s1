"""
Test Generator for API Testing Platform

Auto-generates pytest test cases from OpenAPI specifications with support for:
- Property-based testing using Schemathesis
- Boundary value testing
- Negative test cases
- Parametrized tests
- Custom Jinja2 templates
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml
from jinja2 import Environment, FileSystemLoader, Template
from jinja2 import TemplateError as Jinja2TemplateError

logger = logging.getLogger(__name__)


class TestGenerationError(Exception):
    """Raised when test generation fails."""

    pass


class TemplateRenderError(Exception):
    """Raised when template rendering fails."""

    pass


class TestGenerator:
    """
    Auto-generates pytest test cases from OpenAPI specifications.

    Supports multiple test generation strategies including
    property-based testing, boundary value analysis, negative testing,
    and schema validation.
    """

    # Default pytest template
    DEFAULT_PYTEST_TEMPLATE = '''"""
Auto-generated API tests for {{ spec_title }}
Generated from OpenAPI specification version {{ spec_version }}
"""

import pytest
from typing import Dict, Any

{% if has_auth %}
@pytest.fixture
def auth_headers():
    """Provide authentication headers for API requests."""
    {% if auth_method == "bearer" %}
    return {"Authorization": "Bearer YOUR_TOKEN_HERE"}
    {% elif auth_method == "apikey" %}
    return {"X-API-Key": "YOUR_API_KEY_HERE"}
    {% elif auth_method == "basic" %}
    import base64
    credentials = base64.b64encode(b"user:pass").decode("utf-8")
    return {"Authorization": f"Basic {credentials}"}
    {% else %}
    return {}
    {% endif %}
{% endif %}

{% for test in tests %}
{{ test }}

{% endfor %}
'''

    # Default unittest template
    DEFAULT_UNITTEST_TEMPLATE = '''"""
Auto-generated API tests for {{ spec_title }}
Generated from OpenAPI specification version {{ spec_version }}
"""

import unittest
from typing import Dict, Any

class TestAPI(unittest.TestCase):
    """Auto-generated test suite for API."""

    def setUp(self):
        """Set up test fixtures."""
        {% if has_auth %}
        {% if auth_method == "bearer" %}
        self.auth_headers = {"Authorization": "Bearer YOUR_TOKEN_HERE"}
        {% elif auth_method == "apikey" %}
        self.auth_headers = {"X-API-Key": "YOUR_API_KEY_HERE"}
        {% elif auth_method == "basic" %}
        import base64
        credentials = base64.b64encode(b"user:pass").decode("utf-8")
        self.auth_headers = {"Authorization": f"Basic {credentials}"}
        {% else %}
        self.auth_headers = {}
        {% endif %}
        {% endif %}

    {% for test in tests %}
    {{ test }}

    {% endfor %}

if __name__ == "__main__":
    unittest.main()
'''

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize the TestGenerator.

        Args:
            config: Configuration dictionary with generation options
            template_dir: Directory containing custom Jinja2 templates

        Configuration options:
            - template: Template type ("pytest" or "unittest")
            - include_negative_tests: Generate negative test cases
            - include_property_tests: Generate property-based tests
            - auth_method: Authentication method
              ("bearer", "apikey", "basic", "oauth2")
            - output_dir: Output directory for generated tests
        """
        self.config = config or {}
        self.template_dir = template_dir

        # Set defaults
        self.template_type = self.config.get("template", "pytest")
        self.include_negative_tests = self.config.get("include_negative_tests", True)
        self.include_property_tests = self.config.get("include_property_tests", True)
        self.auth_method = self.config.get("auth_method", "bearer")
        self.output_dir = Path(self.config.get("output_dir", "tests/generated"))

        # Setup Jinja2 environment
        if template_dir and template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self.jinja_env = Environment(
                trim_blocks=True,
                lstrip_blocks=True,
            )

        self.spec: Dict[str, Any] = {}
        self.endpoints: List[Dict[str, Any]] = []

    def _load_spec(self, spec_file: Union[str, Path]) -> Dict[str, Any]:
        """
        Load OpenAPI specification from file.

        Args:
            spec_file: Path to OpenAPI spec (YAML or JSON)

        Returns:
            Parsed specification dictionary

        Raises:
            TestGenerationError: If spec cannot be loaded
        """
        spec_path = Path(spec_file)
        if not spec_path.exists():
            raise TestGenerationError(f"Spec file not found: {spec_file}")

        try:
            with open(spec_path, "r", encoding="utf-8") as f:
                if spec_path.suffix in [".yaml", ".yml"]:
                    return yaml.safe_load(f)
                elif spec_path.suffix == ".json":
                    return json.load(f)
                else:
                    raise TestGenerationError(
                        f"Unsupported file format: " f"{spec_path.suffix}"
                    )
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise TestGenerationError(f"Failed to parse spec file: {e}") from e
        except Exception as e:
            raise TestGenerationError(f"Error loading spec file: {e}") from e

    def _parse_endpoints(self) -> List[Dict[str, Any]]:
        """
        Parse endpoints from OpenAPI specification.

        Returns:
            List of endpoint dictionaries with path, method, and metadata
        """
        endpoints = []
        paths = self.spec.get("paths", {})

        for path, path_item in paths.items():
            # Handle path-level parameters and servers
            path_params = path_item.get("parameters", [])

            methods = ["get", "post", "put", "delete", "patch", "options", "head"]
            for method in methods:
                if method in path_item:
                    operation = path_item[method]
                    default_op_id = f"{method}_{path.replace('/', '_').strip('_')}"
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "operation_id": operation.get(
                            "operationId",
                            default_op_id,
                        ),
                        "summary": operation.get("summary", ""),
                        "description": operation.get("description", ""),
                        "parameters": (path_params + operation.get("parameters", [])),
                        "request_body": operation.get("requestBody"),
                        "responses": operation.get("responses", {}),
                        "security": operation.get("security", []),
                        "tags": operation.get("tags", []),
                    }
                    endpoints.append(endpoint)

        return endpoints

    def _extract_schema(self, ref_or_schema: Union[str, Dict]) -> Dict[str, Any]:
        """
        Extract schema from $ref or return schema directly.

        Args:
            ref_or_schema: Schema object or reference string

        Returns:
            Resolved schema dictionary
        """
        if isinstance(ref_or_schema, dict):
            if "$ref" in ref_or_schema:
                ref = ref_or_schema["$ref"]
                # Parse reference like #/components/schemas/User
                parts = ref.split("/")
                schema = self.spec
                for part in parts[1:]:  # Skip the '#'
                    schema = schema.get(part, {})
                return schema
            return ref_or_schema
        return {}

    def _get_example_value(self, schema: Dict[str, Any]) -> Any:
        """
        Generate example value based on schema type.

        Args:
            schema: JSON schema dictionary

        Returns:
            Example value matching the schema
        """
        if "example" in schema:
            return schema["example"]

        schema_type = schema.get("type", "string")
        schema_format = schema.get("format", "")

        if schema_type == "string":
            if schema_format == "email":
                return "test@example.com"
            elif schema_format == "uuid":
                return "123e4567-e89b-12d3-a456-426614174000"
            elif schema_format == "date":
                return "2023-01-01"
            elif schema_format == "date-time":
                return "2023-01-01T00:00:00Z"
            elif schema_format == "uri":
                return "https://example.com"
            elif "enum" in schema:
                return schema["enum"][0]
            else:
                return "test_string"
        elif schema_type == "integer":
            return schema.get("default", 123)
        elif schema_type == "number":
            return schema.get("default", 123.45)
        elif schema_type == "boolean":
            return schema.get("default", True)
        elif schema_type == "array":
            items = schema.get("items", {})
            return [self._get_example_value(items)]
        elif schema_type == "object":
            if "properties" in schema:
                return {
                    key: self._get_example_value(prop)
                    for key, prop in schema["properties"].items()
                }
            return {}
        else:
            return None

    def _get_boundary_values(self, schema: Dict[str, Any]) -> List[Any]:
        """
        Generate boundary test values based on schema constraints.

        Args:
            schema: JSON schema dictionary

        Returns:
            List of boundary values for testing
        """
        boundary_values: List[Any] = []
        schema_type = schema.get("type", "string")

        if schema_type == "string":
            min_length = schema.get("minLength", 0)
            max_length = schema.get("maxLength")

            # Empty string (if allowed)
            if min_length == 0:
                boundary_values.append("")

            # Minimum length
            if min_length > 0:
                boundary_values.append("x" * min_length)

            # Maximum length
            if max_length:
                boundary_values.append("x" * max_length)

        elif schema_type in ["integer", "number"]:
            minimum = schema.get("minimum")
            maximum = schema.get("maximum")
            exclusive_min = schema.get("exclusiveMinimum")
            exclusive_max = schema.get("exclusiveMaximum")

            if minimum is not None:
                boundary_values.append(minimum)
            if maximum is not None:
                boundary_values.append(maximum)
            if exclusive_min is not None:
                boundary_values.append(exclusive_min + 1)
            if exclusive_max is not None:
                boundary_values.append(exclusive_max - 1)

        elif schema_type == "array":
            min_items = schema.get("minItems", 0)
            max_items = schema.get("maxItems")

            # Empty array (if allowed)
            if min_items == 0:
                boundary_values.append([])

            # Minimum items
            if min_items > 0:
                items = schema.get("items", {})
                boundary_values.append(
                    [self._get_example_value(items) for _ in range(min_items)]
                )

            # Maximum items
            if max_items:
                items = schema.get("items", {})
                boundary_values.append(
                    [self._get_example_value(items) for _ in range(max_items)]
                )

        return boundary_values

    def _get_invalid_values(self, schema: Dict[str, Any]) -> List[Tuple[Any, str]]:
        """
        Generate invalid test values for negative testing.

        Args:
            schema: JSON schema dictionary

        Returns:
            List of tuples (invalid_value, reason)
        """
        invalid_values: List[Tuple[Any, str]] = []
        schema_type = schema.get("type", "string")

        if schema_type == "string":
            # Type violations
            invalid_values.append((123, "number instead of string"))
            invalid_values.append((True, "boolean instead of string"))
            invalid_values.append(([], "array instead of string"))

            # Length violations
            min_length = schema.get("minLength")
            max_length = schema.get("maxLength")

            if min_length and min_length > 0:
                invalid_values.append(("x" * (min_length - 1), "below minimum length"))

            if max_length:
                invalid_values.append(("x" * (max_length + 1), "above maximum length"))

            # Format violations
            schema_format = schema.get("format")
            if schema_format == "email":
                invalid_values.append(("not-an-email", "invalid email format"))
            elif schema_format == "uuid":
                invalid_values.append(("not-a-uuid", "invalid UUID format"))
            elif schema_format == "uri":
                invalid_values.append(("not a uri", "invalid URI format"))

        elif schema_type in ["integer", "number"]:
            # Type violations
            invalid_values.append(("string", "string instead of number"))
            invalid_values.append((True, "boolean instead of number"))

            # Range violations
            minimum = schema.get("minimum")
            maximum = schema.get("maximum")

            if minimum is not None:
                invalid_values.append((minimum - 1, "below minimum"))

            if maximum is not None:
                invalid_values.append((maximum + 1, "above maximum"))

        elif schema_type == "boolean":
            invalid_values.append(("true", "string instead of boolean"))
            invalid_values.append((1, "number instead of boolean"))

        elif schema_type == "array":
            # Type violations
            invalid_values.append(("string", "string instead of array"))
            invalid_values.append((123, "number instead of array"))

            # Length violations
            min_items = schema.get("minItems")
            max_items = schema.get("maxItems")

            if min_items and min_items > 0:
                empty_list: List[Any] = []
                invalid_values.append((empty_list, "below minimum items"))

            if max_items:
                items = schema.get("items", {})
                too_many: List[Any] = [
                    self._get_example_value(items) for _ in range(max_items + 1)
                ]
                invalid_values.append((too_many, "above maximum items"))

        # Null value if not nullable
        if not schema.get("nullable", False):
            invalid_values.append((None, "null value not allowed"))

        return invalid_values

    def _generate_function_name(self, endpoint: Dict[str, Any], test_type: str) -> str:
        """
        Generate test function name.

        Args:
            endpoint: Endpoint dictionary
            test_type: Type of test (success, error, boundary, etc)

        Returns:
            Valid Python function name
        """
        method = endpoint["method"].lower()
        path = endpoint["path"].replace("/", "_")
        path = path.replace("{", "").replace("}", "").strip("_")
        operation_id = endpoint.get("operation_id", f"{method}_{path}")

        # Sanitize operation_id
        operation_id = operation_id.replace("-", "_").replace(".", "_")

        return f"test_{operation_id}_{test_type}"

    def generate_endpoint_tests(
        self, endpoint: Dict[str, Any], method: str
    ) -> List[str]:
        """
        Generate test cases for a specific endpoint and HTTP method.

        Args:
            endpoint: Endpoint dictionary from OpenAPI spec
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)

        Returns:
            List of generated test function strings
        """
        tests = []

        # Success test (2xx responses)
        success_test = self._generate_success_test(endpoint)
        if success_test:
            tests.append(success_test)

        # Error tests (4xx, 5xx responses)
        error_tests = self._generate_error_tests(endpoint)
        tests.extend(error_tests)

        # Negative tests
        if self.include_negative_tests:
            negative_tests = self.generate_negative_tests(endpoint)
            tests.extend(negative_tests)

        # Property-based tests
        if self.include_property_tests:
            property_tests = self.generate_property_tests(endpoint)
            tests.extend(property_tests)

        return tests

    def _generate_success_test(self, endpoint: Dict[str, Any]) -> Optional[str]:
        """Generate success case test (2xx response)."""
        path = endpoint["path"]
        method = endpoint["method"]
        responses = endpoint.get("responses", {})

        # Find first success response
        success_status = None
        for status in ["200", "201", "204"]:
            if status in responses:
                success_status = status
                break

        if not success_status:
            return None

        # Generate path with example parameters
        test_path = path
        params = {}
        for param in endpoint.get("parameters", []):
            param_name = param.get("name")
            param_in = param.get("in")
            param_schema = param.get("schema", {})

            example_value = self._get_example_value(param_schema)

            if param_in == "path":
                test_path = test_path.replace(f"{{{param_name}}}", str(example_value))
            elif param_in == "query":
                params[param_name] = example_value

        # Generate request body if needed
        request_body = ""
        if method in ["POST", "PUT", "PATCH"] and endpoint.get("request_body"):
            content = endpoint["request_body"].get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                resolved_schema = self._extract_schema(schema)
                example_data = self._get_example_value(resolved_schema)
                json_str = json.dumps(example_data, indent=8)
                request_body = f"    json_data = {json_str}\n"

        func_name = self._generate_function_name(endpoint, "success")

        if self.template_type == "pytest":
            auth_param = ", auth_headers" if endpoint.get("security") else ""
            test_code = f'''def {func_name}(api_client{auth_param}):
    """Test {method} {path} with valid input."""
{request_body}    response = api_client.{method.lower()}(
        "{test_path}"'''

            if params:
                test_code += f""",
        params={params}"""

            if request_body:
                test_code += """,
        json=json_data"""

            if endpoint.get("security"):
                test_code += """,
        headers=auth_headers"""

            test_code += f"""
    )
    assert response.status_code == {success_status}"""

            # Add schema validation if response has a schema
            response_spec = responses.get(success_status, {})
            content = response_spec.get("content", {})
            if "application/json" in content:
                test_code += """
    assert response.json()  # Verify JSON response"""

        else:  # unittest
            test_code = f'''def {func_name}(self):
        """Test {method} {path} with valid input."""
{request_body}        response = self.client.{method.lower()}(
            "{test_path}"'''

            if params:
                test_code += f""",
            params={params}"""

            if request_body:
                test_code += """,
            json=json_data"""

            if endpoint.get("security"):
                test_code += """,
            headers=self.auth_headers"""

            test_code += f"""
        )
        self.assertEqual(response.status_code, {success_status})"""

            response_spec = responses.get(success_status, {})
            content = response_spec.get("content", {})
            if "application/json" in content:
                test_code += """
        # Verify JSON response
        self.assertTrue(response.json())"""

        return test_code

    def _generate_error_tests(self, endpoint: Dict[str, Any]) -> List[str]:
        """Generate error case tests (4xx, 5xx responses)."""
        tests = []
        responses = endpoint.get("responses", {})

        for status_code, response_spec in responses.items():
            if status_code.startswith("4") or status_code.startswith("5"):
                test = self._generate_error_test(endpoint, status_code, response_spec)
                if test:
                    tests.append(test)

        return tests

    def _generate_error_test(
        self,
        endpoint: Dict[str, Any],
        status_code: str,
        response_spec: Dict[str, Any],
    ) -> Optional[str]:
        """Generate a single error test case."""
        path = endpoint["path"]
        method = endpoint["method"]

        # Generate descriptive test name
        error_type = "not_found" if status_code == "404" else "error"
        if status_code == "401":
            error_type = "unauthorized"
        elif status_code == "403":
            error_type = "forbidden"
        elif status_code == "400":
            error_type = "bad_request"

        func_name = self._generate_function_name(endpoint, error_type)

        # For 404, use non-existent ID
        test_path = path
        if status_code == "404":
            test_path = test_path.replace("{id}", "99999")
            test_path = test_path.replace(
                "{uuid}", "00000000-0000-0000-0000-000000000000"
            )
        else:
            # Use example values
            for param in endpoint.get("parameters", []):
                if param.get("in") == "path":
                    param_name = param.get("name")
                    param_schema = param.get("schema", {})
                    example = self._get_example_value(param_schema)
                    test_path = test_path.replace(f"{{{param_name}}}", str(example))

        if self.template_type == "pytest":
            test_code = f'''def {func_name}(api_client):
    """Test {method} {path} returns {status_code}."""
    response = api_client.{method.lower()}("{test_path}")
    assert response.status_code == {status_code}'''
        else:
            test_code = f'''def {func_name}(self):
        """Test {method} {path} returns {status_code}."""
        response = self.client.{method.lower()}("{test_path}")
        self.assertEqual(response.status_code, {status_code})'''

        return test_code

    def generate_negative_tests(self, endpoint: Dict[str, Any]) -> List[str]:
        """
        Generate negative test cases with invalid inputs.

        Args:
            endpoint: Endpoint dictionary

        Returns:
            List of negative test function strings
        """
        tests: List[str] = []
        method = endpoint["method"]

        # Only generate for methods that accept input
        if method not in ["POST", "PUT", "PATCH"]:
            return tests

        request_body = endpoint.get("request_body")
        if not request_body:
            return tests

        content = request_body.get("content", {})
        if "application/json" not in content:
            return tests

        schema = content["application/json"].get("schema", {})
        resolved_schema = self._extract_schema(schema)

        # Generate tests for invalid request bodies
        invalid_values = self._get_invalid_values(resolved_schema)

        # Limit to 3 negative tests
        for invalid_value, reason in invalid_values[:3]:
            sanitized_reason = f"invalid_{reason.replace(' ', '_')}"
            func_name = self._generate_function_name(endpoint, sanitized_reason)

            if self.template_type == "pytest":
                test_code = f'''def {func_name}(api_client):
    """Test {method} {endpoint["path"]} with {reason}."""
    invalid_data = {json.dumps(invalid_value)}
    response = api_client.{method.lower()}(
        "{endpoint["path"]}",
        json=invalid_data
    )
    # Bad request or validation error
    assert response.status_code in [400, 422]'''
            else:
                test_code = f'''def {func_name}(self):
        """Test {method} {endpoint["path"]} with {reason}."""
        invalid_data = {json.dumps(invalid_value)}
        response = self.client.{method.lower()}(
            "{endpoint["path"]}",
            json=invalid_data
        )
        self.assertIn(response.status_code, [400, 422])'''

            tests.append(test_code)

        return tests

    def generate_schema_tests(self, schema: Dict[str, Any]) -> List[str]:
        """
        Generate schema-based validation tests.

        Args:
            schema: JSON schema dictionary

        Returns:
            List of schema test function strings
        """
        tests: List[str] = []

        # Generate boundary value tests
        boundary_values = self._get_boundary_values(schema)

        for idx, value in enumerate(boundary_values):
            func_name = f"test_schema_boundary_value_{idx}"

            if self.template_type == "pytest":
                test_code = f'''def {func_name}():
    """Test schema with boundary value."""
    test_value = {json.dumps(value)}
    # Add validation logic here
    assert test_value is not None'''
            else:
                test_code = f'''def {func_name}(self):
        """Test schema with boundary value."""
        test_value = {json.dumps(value)}
        # Add validation logic here
        self.assertIsNotNone(test_value)'''

            tests.append(test_code)

        return tests

    def generate_property_tests(self, endpoint: Dict[str, Any]) -> List[str]:
        """
        Generate property-based tests using Schemathesis.

        Args:
            endpoint: Endpoint dictionary

        Returns:
            List of property-based test function strings
        """
        tests = []

        path = endpoint["path"]
        method = endpoint["method"].lower()

        func_name = self._generate_function_name(endpoint, "property_based")

        # Generate Schemathesis-based test
        test_code = f'''@pytest.mark.property
def {func_name}(api_client):
    """Property-based test for {method.upper()} {path}."""
    # This test uses Schemathesis for automatic property-based testing
    # Schemathesis will generate various inputs based on the OpenAPI spec
    import schemathesis

    schema = schemathesis.from_uri("openapi.yaml")

    @schema.parametrize(endpoint="{path}", method="{method.upper()}")
    def test_api(case):
        response = case.call()
        case.validate_response(response)

    test_api()'''

        tests.append(test_code)

        return tests

    def apply_template(
        self, template: Union[str, Template], context: Dict[str, Any]
    ) -> str:
        """
        Apply Jinja2 template with context.

        Args:
            template: Template string or Jinja2 Template object
            context: Template context variables

        Returns:
            Rendered template string

        Raises:
            TemplateRenderError: If template rendering fails
        """
        try:
            if isinstance(template, str):
                jinja_template = self.jinja_env.from_string(template)
            else:
                jinja_template = template

            return jinja_template.render(**context)
        except Jinja2TemplateError as e:
            raise TemplateRenderError(f"Template rendering failed: {e}") from e
        except Exception as e:
            raise TemplateRenderError(
                f"Unexpected error during template rendering: {e}"
            ) from e

    def generate_from_spec(
        self, spec_file: Union[str, Path], output_dir: Optional[Path] = None
    ) -> Path:
        """
        Generate pytest test cases from OpenAPI specification.

        Args:
            spec_file: Path to OpenAPI specification file (YAML or JSON)
            output_dir: Output directory for generated tests (optional)

        Returns:
            Path to generated test file

        Raises:
            TestGenerationError: If generation fails
        """
        # Load specification
        logger.info(f"Loading OpenAPI spec from {spec_file}")
        self.spec = self._load_spec(spec_file)

        # Parse endpoints
        logger.info("Parsing endpoints from specification")
        self.endpoints = self._parse_endpoints()

        if not self.endpoints:
            raise TestGenerationError("No endpoints found in specification")

        logger.info(f"Found {len(self.endpoints)} endpoints")

        # Generate tests for each endpoint
        all_tests = []
        for endpoint in self.endpoints:
            logger.debug(
                f"Generating tests for {endpoint['method']} {endpoint['path']}"
            )
            tests = self.generate_endpoint_tests(endpoint, endpoint["method"])
            all_tests.extend(tests)

        logger.info(f"Generated {len(all_tests)} test cases")

        # Prepare template context
        spec_info = self.spec.get("info", {})
        context = {
            "spec_title": spec_info.get("title", "API"),
            "spec_version": spec_info.get("version", "1.0.0"),
            "tests": all_tests,
            "has_auth": any(ep.get("security") for ep in self.endpoints),
            "auth_method": self.auth_method,
        }

        # Select template
        template_str: Union[str, Template]
        if self.template_type == "pytest":
            template_str = self.DEFAULT_PYTEST_TEMPLATE
        elif self.template_type == "unittest":
            template_str = self.DEFAULT_UNITTEST_TEMPLATE
        else:
            # Try to load custom template
            try:
                template_str = self.jinja_env.get_template(f"{self.template_type}.j2")
            except Exception as e:
                raise TestGenerationError(
                    f"Failed to load template " f"{self.template_type}: {e}"
                ) from e

        # Render template
        logger.info("Rendering test file from template")
        rendered = self.apply_template(template_str, context)

        # Write to file
        output_dir = output_dir or self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        spec_name = Path(spec_file).stem
        output_file = output_dir / f"test_{spec_name}_generated.py"

        logger.info(f"Writing generated tests to {output_file}")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(rendered)
        except IOError as e:
            raise TestGenerationError(f"Failed to write test file: {e}") from e

        logger.info(f"Successfully generated {output_file}")
        return output_file

    def generate_from_dict(
        self, spec_dict: Dict[str, Any], output_dir: Optional[Path] = None
    ) -> Path:
        """
        Generate tests from OpenAPI specification dictionary.

        Args:
            spec_dict: OpenAPI specification as dictionary
            output_dir: Output directory for generated tests

        Returns:
            Path to generated test file
        """
        # Set spec directly
        self.spec = spec_dict

        # Parse endpoints
        self.endpoints = self._parse_endpoints()

        if not self.endpoints:
            raise TestGenerationError("No endpoints found in specification")

        # Generate tests
        all_tests = []
        for endpoint in self.endpoints:
            tests = self.generate_endpoint_tests(endpoint, endpoint["method"])
            all_tests.extend(tests)

        # Prepare context
        spec_info = self.spec.get("info", {})
        context = {
            "spec_title": spec_info.get("title", "API"),
            "spec_version": spec_info.get("version", "1.0.0"),
            "tests": all_tests,
            "has_auth": any(ep.get("security") for ep in self.endpoints),
            "auth_method": self.auth_method,
        }

        # Render template
        if self.template_type == "pytest":
            template = self.DEFAULT_PYTEST_TEMPLATE
        else:
            template = self.DEFAULT_UNITTEST_TEMPLATE

        rendered = self.apply_template(template, context)

        # Write file
        output_dir = output_dir or self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / "test_api_generated.py"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered)

        return output_file


__all__ = ["TestGenerator", "TestGenerationError", "TemplateRenderError"]
