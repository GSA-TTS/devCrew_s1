"""
Example Generator Module.

Generates code examples (cURL, Python, JavaScript) from OpenAPI specifications
for API documentation.
"""

import json
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


class ExampleGenerator:
    """Generate code examples from OpenAPI specifications."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize example generator.

        Args:
            base_url: Base URL for API endpoints
                (e.g., https://api.example.com)
        """
        self.base_url = base_url or "https://api.example.com"
        logger.info("example_generator_initialized", base_url=self.base_url)

    def generate_curl(
        self,
        endpoint: str,
        method: str,
        spec: Dict[str, Any],
        auth: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Generate cURL command for an API endpoint.

        Args:
            endpoint: API endpoint path (e.g., /users/{id})
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            spec: OpenAPI operation specification
            auth: Authentication configuration
                (e.g., {"type": "bearer", "token": "TOKEN"})

        Returns:
            Formatted cURL command string
        """
        logger.debug(
            "generating_curl",
            endpoint=endpoint,
            method=method,
            has_auth=auth is not None,
        )

        method = method.upper()
        url = self._build_url(endpoint, spec)

        # Build cURL command parts
        parts = [f"curl -X {method} {url}"]

        # Add headers
        headers = self._extract_headers(spec, auth)
        for header_name, header_value in headers.items():
            parts.append(f'  -H "{header_name}: {header_value}"')

        # Add request body for POST/PUT/PATCH
        if method in ["POST", "PUT", "PATCH"]:
            body = self._generate_request_body(spec)
            if body:
                # Escape single quotes and format as JSON
                body_json = json.dumps(body, indent=2)
                parts.append(f"  -d '{body_json}'")

        # Add query parameters for GET
        if method == "GET":
            query_params = self._extract_query_params(spec)
            if query_params:
                query_string = "&".join(f"{k}={v}" for k, v in query_params.items())
                # Update URL with query string
                parts[0] = f"curl -X {method} {url}?{query_string}"

        result = " \\\n".join(parts)
        logger.debug("curl_generated", length=len(result))
        return result

    def generate_python(
        self,
        endpoint: str,
        method: str,
        spec: Dict[str, Any],
        auth: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Generate Python requests code for an API endpoint.

        Args:
            endpoint: API endpoint path (e.g., /users/{id})
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            spec: OpenAPI operation specification
            auth: Authentication configuration

        Returns:
            Formatted Python code string
        """
        logger.debug(
            "generating_python",
            endpoint=endpoint,
            method=method,
            has_auth=auth is not None,
        )

        method = method.lower()
        url = self._build_url(endpoint, spec)

        # Build Python code
        lines = ["import requests", "", "# API request"]

        # Build headers dict
        headers = self._extract_headers(spec, auth)
        if headers:
            headers_str = self._format_python_dict(headers, indent=4)
            lines.append(f"headers = {headers_str}")
            lines.append("")

        # Build request parameters
        request_params = [f'    "{url}"']

        if headers:
            request_params.append("    headers=headers")

        # Add request body for POST/PUT/PATCH
        if method in ["post", "put", "patch"]:
            body = self._generate_request_body(spec)
            if body:
                body_str = self._format_python_dict(body, indent=4)
                lines.append(f"data = {body_str}")
                lines.append("")
                request_params.append("    json=data")

        # Add query parameters for GET
        if method == "get":
            query_params = self._extract_query_params(spec)
            if query_params:
                params_str = self._format_python_dict(query_params, indent=4)
                lines.append(f"params = {params_str}")
                lines.append("")
                request_params.append("    params=params")

        # Build the request call
        request_call = f"response = requests.{method}(\n"
        request_call += ",\n".join(request_params)
        request_call += "\n)"
        lines.append(request_call)

        # Add response handling
        lines.extend(
            [
                "",
                "# Check response",
                "if response.status_code == 200:",
                "    print(response.json())",
                "else:",
                '    print(f"Error: {response.status_code}")',
                "    print(response.text)",
            ]
        )

        result = "\n".join(lines)
        logger.debug("python_generated", lines=len(lines))
        return result

    def generate_javascript(
        self,
        endpoint: str,
        method: str,
        spec: Dict[str, Any],
        auth: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Generate JavaScript fetch code for an API endpoint.

        Args:
            endpoint: API endpoint path (e.g., /users/{id})
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            spec: OpenAPI operation specification
            auth: Authentication configuration

        Returns:
            Formatted JavaScript code string
        """
        logger.debug(
            "generating_javascript",
            endpoint=endpoint,
            method=method,
            has_auth=auth is not None,
        )

        method = method.upper()
        url = self._build_url(endpoint, spec)

        # Build JavaScript code
        lines = ["// API request using fetch", ""]

        # Build options object
        options: Dict[str, Any] = {"method": method}

        # Add headers
        headers = self._extract_headers(spec, auth)
        if headers:
            options["headers"] = headers

        # Add request body for POST/PUT/PATCH
        if method in ["POST", "PUT", "PATCH"]:
            body = self._generate_request_body(spec)
            if body:
                options["body"] = "JSON.stringify(requestData)"
                body_str = json.dumps(body, indent=2)
                lines.append(f"const requestData = {body_str};")
                lines.append("")

        # Format options object
        options_str = json.dumps(options, indent=2)
        # Replace body placeholder
        if method in ["POST", "PUT", "PATCH"] and "body" in options:
            options_str = options_str.replace(
                '"JSON.stringify(requestData)"', "JSON.stringify(requestData)"
            )

        lines.append(f'const url = "{url}";')

        # Add query parameters for GET
        if method == "GET":
            query_params = self._extract_query_params(spec)
            if query_params:
                params_str = json.dumps(query_params, indent=2)
                lines.append(f"const params = {params_str};")
                lines.append(
                    "const queryString = " "new URLSearchParams(params).toString();"
                )
                lines.append("const fullUrl = `${url}?${queryString}`;")
                lines.append("")
                url_var = "fullUrl"
            else:
                url_var = "url"
        else:
            url_var = "url"

        lines.append("")
        lines.append(f"const options = {options_str};")
        lines.append("")

        # Add fetch call with error handling
        lines.extend(
            [
                f"fetch({url_var}, options)",
                "  .then(response => {",
                "    if (!response.ok) {",
                "      throw new Error(`HTTP error! status: " "${response.status}`);",
                "    }",
                "    return response.json();",
                "  })",
                "  .then(data => {",
                "    console.log('Success:', data);",
                "  })",
                "  .catch(error => {",
                "    console.error('Error:', error);",
                "  });",
            ]
        )

        result = "\n".join(lines)
        logger.debug("javascript_generated", lines=len(lines))
        return result

    def generate_all_examples(
        self, spec: Dict[str, Any], auth: Optional[Dict[str, str]] = None
    ) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Generate examples for all endpoints in OpenAPI spec.

        Args:
            spec: Complete OpenAPI specification
            auth: Authentication configuration

        Returns:
            Nested dictionary: {path: {method: {curl: ..., python: ...,
            javascript: ...}}}
        """
        logger.info("generating_all_examples", has_auth=auth is not None)

        examples: Dict[str, Dict[str, Dict[str, str]]] = {}
        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            examples[path] = {}

            for method in ["get", "post", "put", "patch", "delete"]:
                if method in path_item:
                    operation_spec = path_item[method]
                    try:
                        examples[path][method] = {
                            "curl": self.generate_curl(
                                path, method, operation_spec, auth
                            ),
                            "python": self.generate_python(
                                path, method, operation_spec, auth
                            ),
                            "javascript": self.generate_javascript(
                                path, method, operation_spec, auth
                            ),
                        }
                        logger.debug("examples_generated", path=path, method=method)
                    except Exception as exc:
                        logger.error(
                            "example_generation_failed",
                            path=path,
                            method=method,
                            error=str(exc),
                        )
                        error_msg = f"Error generating example: {exc}"
                        examples[path][method] = {
                            "curl": f"# {error_msg}",
                            "python": f"# {error_msg}",
                            "javascript": f"// {error_msg}",
                        }

        total_ops = sum(len(methods) for methods in examples.values())
        logger.info(
            "all_examples_generated",
            total_paths=len(examples),
            total_operations=total_ops,
        )
        return examples

    def _build_url(self, endpoint: str, spec: Dict[str, Any]) -> str:
        """
        Build full URL with path parameters replaced.

        Args:
            endpoint: API endpoint path
            spec: Operation specification

        Returns:
            Full URL with example parameter values
        """
        url = f"{self.base_url}{endpoint}"

        # Replace path parameters with example values
        parameters = spec.get("parameters", [])
        for param in parameters:
            if param.get("in") == "path":
                param_name = param.get("name")
                example_value = self._get_example_value(param)
                url = url.replace(f"{{{param_name}}}", str(example_value))

        return url

    def _extract_headers(
        self, spec: Dict[str, Any], auth: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Extract headers from operation spec and add authentication.

        Args:
            spec: Operation specification
            auth: Authentication configuration

        Returns:
            Dictionary of header names to values
        """
        headers = {}

        # Add content type for operations with request body
        if "requestBody" in spec:
            content = spec["requestBody"].get("content", {})
            if "application/json" in content:
                headers["Content-Type"] = "application/json"

        # Add authentication header
        if auth:
            auth_type = auth.get("type", "").lower()
            if auth_type == "bearer":
                token = auth.get("token", "TOKEN")
                headers["Authorization"] = f"Bearer {token}"
            elif auth_type == "apikey":
                key_name = auth.get("name", "X-API-Key")
                key_value = auth.get("value", "API_KEY")
                headers[key_name] = key_value
            elif auth_type == "basic":
                credentials = auth.get("credentials", "username:password")
                headers["Authorization"] = f"Basic {credentials}"

        # Extract headers from parameters
        parameters = spec.get("parameters", [])
        for param in parameters:
            if param.get("in") == "header":
                param_name = param.get("name")
                example_value = self._get_example_value(param)
                headers[param_name] = str(example_value)

        return headers

    def _extract_query_params(self, spec: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract query parameters from operation spec.

        Args:
            spec: Operation specification

        Returns:
            Dictionary of query parameter names to example values
        """
        params = {}
        parameters = spec.get("parameters", [])

        for param in parameters:
            if param.get("in") == "query":
                param_name = param.get("name")
                example_value = self._get_example_value(param)
                params[param_name] = str(example_value)

        return params

    def _generate_request_body(self, spec: Dict[str, Any]) -> Optional[Dict]:
        """
        Generate example request body from operation spec.

        Args:
            spec: Operation specification

        Returns:
            Example request body as dictionary, or None
        """
        if "requestBody" not in spec:
            return None

        request_body = spec["requestBody"]
        content = request_body.get("content", {})

        # Try to get JSON schema
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
            return self._generate_example_from_schema(schema)

        return None

    def _generate_example_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate example data from JSON schema.

        Args:
            schema: JSON schema object

        Returns:
            Example data matching the schema
        """
        # Check for explicit example
        if "example" in schema:
            return schema["example"]

        schema_type = schema.get("type")

        if schema_type == "object":
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            example = {}

            for prop_name, prop_schema in properties.items():
                # Only include required properties by default
                if prop_name in required or len(required) == 0:  # type: ignore
                    example[prop_name] = self._generate_value_from_schema(prop_schema)

            return example

        elif schema_type == "array":
            items_schema = schema.get("items", {})
            return {"items": [self._generate_value_from_schema(items_schema)]}

        else:
            value = self._generate_value_from_schema(schema)
            return {"value": value} if not isinstance(value, dict) else value

    def _generate_value_from_schema(self, schema: Dict[str, Any]) -> Any:
        """
        Generate example value from schema.

        Args:
            schema: JSON schema for a value

        Returns:
            Example value matching the schema
        """
        # Check for explicit example
        if "example" in schema:
            return schema["example"]

        # Check for enum
        if "enum" in schema:
            return schema["enum"][0]

        schema_type = schema.get("type", "string")
        schema_format = schema.get("format")

        # Generate value based on type and format
        if schema_type == "string":
            if schema_format == "email":
                return "user@example.com"
            elif schema_format == "date":
                return "2024-01-01"
            elif schema_format == "date-time":
                return "2024-01-01T00:00:00Z"
            elif schema_format == "uuid":
                return "550e8400-e29b-41d4-a716-446655440000"
            else:
                return "string"

        elif schema_type == "integer":
            return 1

        elif schema_type == "number":
            return 1.0

        elif schema_type == "boolean":
            return True

        elif schema_type == "array":
            items_schema = schema.get("items", {})
            return [self._generate_value_from_schema(items_schema)]

        elif schema_type == "object":
            return self._generate_example_from_schema(schema)

        return None

    def _get_example_value(self, param: Dict[str, Any]) -> Any:
        """
        Get example value for a parameter.

        Args:
            param: Parameter specification

        Returns:
            Example value
        """
        # Check for explicit example
        if "example" in param:
            return param["example"]

        # Generate from schema
        if "schema" in param:
            return self._generate_value_from_schema(param["schema"])

        # Default based on name
        param_name = param.get("name", "")
        if "id" in param_name.lower():
            return "123"
        elif "name" in param_name.lower():
            return "example"
        elif "email" in param_name.lower():
            return "user@example.com"
        else:
            return "value"

    def _format_python_dict(self, data: Dict[str, Any], indent: int = 0) -> str:
        """
        Format dictionary as Python dict literal.

        Args:
            data: Dictionary to format
            indent: Indentation level in spaces

        Returns:
            Formatted Python dict string
        """
        if not data:
            return "{}"

        items = []

        for key, value in data.items():
            if isinstance(value, str):
                items.append(f'    "{key}": "{value}"')
            else:
                items.append(f'    "{key}": {json.dumps(value)}')

        return "{\n" + ",\n".join(items) + "\n}"

    def set_base_url(self, base_url: str) -> None:
        """
        Update base URL for generated examples.

        Args:
            base_url: New base URL
        """
        self.base_url = base_url
        logger.info("base_url_updated", base_url=base_url)

    def generate_examples_for_operation(
        self,
        path: str,
        method: str,
        operation_spec: Dict[str, Any],
        auth: Optional[Dict[str, str]] = None,
        languages: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Generate examples for a single operation in specified languages.

        Args:
            path: API endpoint path
            method: HTTP method
            operation_spec: OpenAPI operation specification
            auth: Authentication configuration
            languages: List of languages to generate (curl, python, javascript)

        Returns:
            Dictionary mapping language to example code
        """
        if languages is None:
            languages = ["curl", "python", "javascript"]

        examples = {}

        if "curl" in languages:
            examples["curl"] = self.generate_curl(path, method, operation_spec, auth)

        if "python" in languages:
            examples["python"] = self.generate_python(
                path, method, operation_spec, auth
            )

        if "javascript" in languages:
            examples["javascript"] = self.generate_javascript(
                path, method, operation_spec, auth
            )

        logger.info(
            "operation_examples_generated",
            path=path,
            method=method,
            languages=languages,
        )

        return examples
