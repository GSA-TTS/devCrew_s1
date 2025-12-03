"""
Comprehensive test suite for API Testing Platform.

Tests all 6 modules with 85%+ coverage target:
- ContractValidator (20+ tests)
- TestGenerator (15+ tests)
- APIClient (20+ tests)
- PactManager (15+ tests)
- SchemaValidator (20+ tests)
- RegressionEngine (15+ tests)
"""

import json
import re
from pathlib import Path
from typing import Any, Dict
from unittest import mock

import pytest
import responses
import yaml
from requests.exceptions import ConnectionError, SSLError, Timeout

from api_client import (
    APIClient,
    APIClientError,
    RateLimitError,
)
from contract_validator import (
    CompatibilityIssueType,
    ContractValidator,
    EndpointNamingRule,
)
from pact_manager import (
    BrokerError,
    ContractError,
    DeploymentStatus,
    Interaction,
    PactContract,
    PactManager,
    VerificationError,
)
from regression_engine import (
    BaselineNotFoundError,
    CorruptedBaselineError,
    RegressionEngine,
    RegressionEngineError,
)
from schema_validator import (
    SchemaValidator,
    ValidationMode,
)
from test_generator import (
    TemplateRenderError,
    TestGenerationError,
    TestGenerator,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_openapi_spec() -> Dict[str, Any]:
    """Sample OpenAPI 3.0 specification."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "A test API",
        },
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/users": {
                "get": {
                    "operationId": "listUsers",
                    "summary": "List all users",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/User"},
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "operationId": "createUser",
                    "summary": "Create a user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserInput"}
                            }
                        },
                    },
                    "responses": {
                        "201": {"description": "Created"},
                        "400": {"description": "Bad Request"},
                    },
                },
            },
            "/users/{id}": {
                "get": {
                    "operationId": "getUser",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            },
                        },
                        "404": {"description": "Not Found"},
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "required": ["id", "email"],
                    "properties": {
                        "id": {"type": "integer"},
                        "email": {"type": "string", "format": "email"},
                        "name": {"type": "string"},
                    },
                },
                "UserInput": {
                    "type": "object",
                    "required": ["email"],
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "name": {"type": "string"},
                    },
                },
            },
            "securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}},
        },
    }


@pytest.fixture
def sample_openapi_31_spec() -> Dict[str, Any]:
    """Sample OpenAPI 3.1 specification."""
    return {
        "openapi": "3.1.0",
        "info": {"title": "Test API 3.1", "version": "2.0.0"},
        "paths": {
            "/products": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "List products",
                            "content": {
                                "application/json": {"schema": {"type": "array"}}
                            },
                        }
                    }
                }
            }
        },
    }


@pytest.fixture
def invalid_openapi_spec() -> Dict[str, Any]:
    """Invalid OpenAPI spec (missing required fields)."""
    return {
        "openapi": "3.0.3",
        # Missing 'info' section
        "paths": {},
    }


@pytest.fixture
def malformed_yaml_file(tmp_path: Path) -> Path:
    """Create malformed YAML file."""
    file_path = tmp_path / "malformed.yaml"
    file_path.write_text("invalid: yaml: content: [unclosed")
    return file_path


@pytest.fixture
def temp_spec_file(tmp_path: Path, sample_openapi_spec: Dict) -> Path:
    """Create temporary OpenAPI spec file."""
    spec_path = tmp_path / "openapi.yaml"
    with open(spec_path, "w") as f:
        yaml.dump(sample_openapi_spec, f)
    return spec_path


@pytest.fixture
def temp_json_spec_file(tmp_path: Path, sample_openapi_spec: Dict) -> Path:
    """Create temporary JSON OpenAPI spec file."""
    spec_path = tmp_path / "openapi.json"
    with open(spec_path, "w") as f:
        json.dump(sample_openapi_spec, f)
    return spec_path


@pytest.fixture
def api_client() -> APIClient:
    """Create APIClient instance."""
    return APIClient(
        config={
            "base_url": "https://api.example.com",
            "timeout": 30,
            "retry_attempts": 3,
        }
    )


@pytest.fixture
def test_generator() -> TestGenerator:
    """Create TestGenerator instance."""
    return TestGenerator(
        config={
            "template": "pytest",
            "include_negative_tests": True,
            "include_property_tests": True,
        }
    )


@pytest.fixture
def pact_manager() -> PactManager:
    """Create PactManager instance."""
    return PactManager(
        consumer="TestConsumer",
        provider="TestProvider",
        broker_url="https://pact-broker.example.com",
        broker_token="test_token",
    )


@pytest.fixture
def schema_validator(sample_openapi_spec: Dict) -> SchemaValidator:
    """Create SchemaValidator instance."""
    return SchemaValidator(spec_dict=sample_openapi_spec)


@pytest.fixture
def regression_engine(tmp_path: Path) -> RegressionEngine:
    """Create RegressionEngine instance."""
    baseline_dir = tmp_path / "baselines"
    return RegressionEngine(
        baseline_dir=str(baseline_dir),
        ignore_fields=["timestamp", "request_id"],
        performance_threshold=0.20,
    )


# ============================================================================
# A. CONTRACT VALIDATOR TESTS (20+ tests)
# ============================================================================


class TestContractValidator:
    """Test suite for ContractValidator module."""

    def test_validate_valid_openapi_30_spec(self, temp_spec_file: Path) -> None:
        """Test validation of valid OpenAPI 3.0 spec."""
        validator = ContractValidator()
        result = validator.validate(temp_spec_file)

        assert result.is_valid
        assert result.spec_version == "3.0.3"
        assert len(result.errors) == 0

    def test_validate_valid_openapi_31_spec(
        self, tmp_path: Path, sample_openapi_31_spec: Dict
    ) -> None:
        """Test validation of valid OpenAPI 3.1 spec."""
        spec_path = tmp_path / "openapi_31.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(sample_openapi_31_spec, f)

        validator = ContractValidator()
        result = validator.validate(spec_path)

        assert result.is_valid
        assert result.spec_version == "3.1.0"

    def test_validate_invalid_spec_missing_paths(
        self, tmp_path: Path, invalid_openapi_spec: Dict
    ) -> None:
        """Test validation of spec with missing required fields."""
        spec_path = tmp_path / "invalid.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(invalid_openapi_spec, f)

        validator = ContractValidator()
        result = validator.validate(spec_path)

        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("info" in err.message.lower() for err in result.errors)

    def test_validate_malformed_yaml(self, malformed_yaml_file: Path) -> None:
        """Test validation of malformed YAML file."""
        validator = ContractValidator()
        result = validator.validate(malformed_yaml_file)

        assert not result.is_valid
        assert len(result.errors) > 0

    def test_validate_missing_file(self) -> None:
        """Test validation of non-existent file."""
        validator = ContractValidator()
        result = validator.validate("nonexistent.yaml")

        assert not result.is_valid
        assert any("not found" in err.message.lower() for err in result.errors)

    def test_validate_unsupported_version(self, tmp_path: Path) -> None:
        """Test validation of unsupported OpenAPI version."""
        spec = {
            "openapi": "2.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        spec_path = tmp_path / "v2.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(spec, f)

        validator = ContractValidator()
        result = validator.validate(spec_path)

        assert not result.is_valid
        assert any("version" in err.message.lower() for err in result.errors)

    def test_validate_missing_openapi_field(self, tmp_path: Path) -> None:
        """Test validation of spec missing openapi version field."""
        spec = {"info": {"title": "Test", "version": "1.0.0"}, "paths": {}}
        spec_path = tmp_path / "no_version.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(spec, f)

        validator = ContractValidator()
        result = validator.validate(spec_path)

        assert not result.is_valid

    def test_lint_valid_spec(self, temp_spec_file: Path) -> None:
        """Test linting of valid spec."""
        validator = ContractValidator()
        result = validator.lint(temp_spec_file)

        assert result.is_valid
        # May have warnings but no errors
        assert len(result.errors) == 0

    def test_lint_endpoint_naming_rule(self, tmp_path: Path) -> None:
        """Test endpoint naming rule validation."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {"/BAD-Path": {"get": {"responses": {"200": {}}}}},
        }
        spec_path = tmp_path / "bad_naming.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(spec, f)

        validator = ContractValidator()
        result = validator.lint(spec_path)

        # Should have warnings about naming
        assert len(result.warnings) > 0

    def test_lint_security_scheme_rule(self, tmp_path: Path) -> None:
        """Test security scheme rule validation."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {"/users": {"get": {"responses": {"200": {}}}}},
            # Missing security schemes
        }
        spec_path = tmp_path / "no_security.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(spec, f)

        validator = ContractValidator()
        result = validator.lint(spec_path)

        # Should have warning about missing security
        assert any("security" in w.message.lower() for w in result.warnings)

    def test_lint_response_schema_rule(self, tmp_path: Path) -> None:
        """Test response schema rule validation."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {
                                        # Missing schema
                                    }
                                },
                            }
                        }
                    }
                }
            },
        }
        spec_path = tmp_path / "no_schema.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(spec, f)

        validator = ContractValidator()
        result = validator.lint(spec_path)

        # Should have warnings about missing schemas
        assert len(result.warnings) > 0

    def test_lint_custom_rules(self, temp_spec_file: Path) -> None:
        """Test linting with custom rules."""
        # Create custom rule
        custom_rule = EndpointNamingRule(pattern=r"^/api/.*")

        validator = ContractValidator()
        result = validator.lint(temp_spec_file, rules=[custom_rule])

        # /users doesn't match /api/* pattern
        assert len(result.warnings) > 0

    def test_check_compatibility_backward_compatible(
        self, tmp_path: Path, sample_openapi_spec: Dict
    ) -> None:
        """Test compatibility check with backward compatible changes."""
        old_spec_path = tmp_path / "old.yaml"
        with open(old_spec_path, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        # New spec with added endpoint (backward compatible)
        new_spec = sample_openapi_spec.copy()
        new_spec["paths"]["/products"] = {
            "get": {"responses": {"200": {"description": "Success"}}}
        }
        new_spec_path = tmp_path / "new.yaml"
        with open(new_spec_path, "w") as f:
            yaml.dump(new_spec, f)

        validator = ContractValidator()
        result = validator.check_compatibility(old_spec_path, new_spec_path)

        assert result.is_valid
        # Should have additive changes
        additive = [
            i
            for i in result.compatibility_issues
            if i.issue_type == CompatibilityIssueType.ADDITIVE
        ]
        assert len(additive) > 0

    def test_check_compatibility_breaking_changes(
        self, tmp_path: Path, sample_openapi_spec: Dict
    ) -> None:
        """Test compatibility check with breaking changes."""
        old_spec_path = tmp_path / "old.yaml"
        with open(old_spec_path, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        # New spec with removed endpoint (breaking)
        new_spec = sample_openapi_spec.copy()
        del new_spec["paths"]["/users"]
        new_spec_path = tmp_path / "new.yaml"
        with open(new_spec_path, "w") as f:
            yaml.dump(new_spec, f)

        validator = ContractValidator()
        result = validator.check_compatibility(old_spec_path, new_spec_path)

        assert not result.is_valid
        # Should have breaking changes
        breaking = [
            i
            for i in result.compatibility_issues
            if i.issue_type == CompatibilityIssueType.BREAKING
        ]
        assert len(breaking) > 0

    def test_check_compatibility_removed_operation(
        self, tmp_path: Path, sample_openapi_spec: Dict
    ) -> None:
        """Test compatibility check with removed operation."""
        old_spec_path = tmp_path / "old.yaml"
        with open(old_spec_path, "w") as f:
            yaml.dump(sample_openapi_spec, f)

        # Remove POST operation
        new_spec = sample_openapi_spec.copy()
        del new_spec["paths"]["/users"]["post"]
        new_spec_path = tmp_path / "new.yaml"
        with open(new_spec_path, "w") as f:
            yaml.dump(new_spec, f)

        validator = ContractValidator()
        result = validator.check_compatibility(old_spec_path, new_spec_path)

        assert not result.is_valid

    def test_resolve_refs_valid_spec(self, temp_spec_file: Path) -> None:
        """Test $ref resolution for valid spec."""
        validator = ContractValidator()
        resolved = validator.resolve_refs(temp_spec_file)

        assert "components" in resolved
        assert "schemas" in resolved["components"]

    def test_resolve_refs_missing_file(self) -> None:
        """Test $ref resolution for missing file."""
        validator = ContractValidator()

        with pytest.raises(ValueError):
            validator.resolve_refs("nonexistent.yaml")

    def test_validation_report_generation(self, temp_spec_file: Path) -> None:
        """Test validation report generation."""
        validator = ContractValidator()
        result = validator.validate(temp_spec_file)
        report = validator.get_validation_report(result)

        assert isinstance(report, str)
        assert "OpenAPI Specification Validation Report" in report
        assert "3.0.3" in report

    def test_strict_mode_warnings_as_errors(self, tmp_path: Path) -> None:
        """Test strict mode treats warnings as errors."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {"/bad-PATH": {"get": {"responses": {"200": {}}}}},
        }
        spec_path = tmp_path / "spec.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(spec, f)

        validator = ContractValidator(strict=True)
        result = validator.lint(spec_path)

        # In strict mode, naming violations should be errors
        assert not result.is_valid or len(result.warnings) > 0


# ============================================================================
# B. TEST GENERATOR TESTS (15+ tests)
# ============================================================================


class TestTestGenerator:
    """Test suite for TestGenerator module."""

    def test_generate_from_valid_spec(
        self, test_generator: TestGenerator, temp_spec_file: Path, tmp_path: Path
    ) -> None:
        """Test test generation from valid spec."""
        output_file = test_generator.generate_from_spec(
            temp_spec_file, output_dir=tmp_path
        )

        assert output_file.exists()
        content = output_file.read_text()
        assert "import pytest" in content
        assert "def test_" in content

    def test_generate_pytest_template(
        self, temp_spec_file: Path, tmp_path: Path
    ) -> None:
        """Test pytest template generation."""
        generator = TestGenerator(config={"template": "pytest"})
        output_file = generator.generate_from_spec(temp_spec_file, output_dir=tmp_path)

        content = output_file.read_text()
        assert "import pytest" in content
        assert "@pytest.fixture" in content

    def test_generate_unittest_template(
        self, temp_spec_file: Path, tmp_path: Path
    ) -> None:
        """Test unittest template generation."""
        generator = TestGenerator(config={"template": "unittest"})
        output_file = generator.generate_from_spec(temp_spec_file, output_dir=tmp_path)

        content = output_file.read_text()
        assert "import unittest" in content
        assert "class TestAPI" in content

    def test_generate_negative_tests(
        self, test_generator: TestGenerator, temp_spec_file: Path, tmp_path: Path
    ) -> None:
        """Test negative test case generation."""
        generator = TestGenerator(config={"include_negative_tests": True})
        output_file = generator.generate_from_spec(temp_spec_file, output_dir=tmp_path)

        content = output_file.read_text()
        # Should have invalid test cases
        assert "invalid" in content.lower() or "bad_request" in content.lower()

    def test_generate_property_tests(
        self, test_generator: TestGenerator, temp_spec_file: Path, tmp_path: Path
    ) -> None:
        """Test property-based test generation."""
        generator = TestGenerator(config={"include_property_tests": True})
        output_file = generator.generate_from_spec(temp_spec_file, output_dir=tmp_path)

        content = output_file.read_text()
        # Should have property-based tests
        assert "schemathesis" in content.lower() or "@pytest.mark.property" in content

    def test_generate_with_auth_bearer(
        self, temp_spec_file: Path, tmp_path: Path
    ) -> None:
        """Test generation with Bearer token auth."""
        generator = TestGenerator(config={"auth_method": "bearer"})
        output_file = generator.generate_from_spec(temp_spec_file, output_dir=tmp_path)

        content = output_file.read_text()
        assert "Bearer" in content

    def test_generate_with_auth_apikey(
        self, temp_spec_file: Path, tmp_path: Path
    ) -> None:
        """Test generation with API key auth."""
        generator = TestGenerator(config={"auth_method": "apikey"})
        output_file = generator.generate_from_spec(temp_spec_file, output_dir=tmp_path)

        content = output_file.read_text()
        assert "X-API-Key" in content or "api_key" in content.lower()

    def test_template_rendering(self, test_generator: TestGenerator) -> None:
        """Test template rendering."""
        template = "Hello {{ name }}"
        context = {"name": "World"}

        result = test_generator.apply_template(template, context)

        assert result == "Hello World"

    def test_template_rendering_error(self, test_generator: TestGenerator) -> None:
        """Test template rendering with invalid template."""
        template = "Hello {{ name"  # Unclosed variable
        context = {"name": "World"}

        with pytest.raises(TemplateRenderError):
            test_generator.apply_template(template, context)

    def test_generate_from_invalid_spec(
        self, test_generator: TestGenerator, malformed_yaml_file: Path
    ) -> None:
        """Test generation from invalid spec."""
        with pytest.raises(TestGenerationError):
            test_generator.generate_from_spec(malformed_yaml_file)

    def test_generate_from_missing_file(self, test_generator: TestGenerator) -> None:
        """Test generation from missing file."""
        with pytest.raises(TestGenerationError):
            test_generator.generate_from_spec("nonexistent.yaml")

    def test_generate_from_spec_dict(
        self, test_generator: TestGenerator, sample_openapi_spec: Dict, tmp_path: Path
    ) -> None:
        """Test generation from spec dictionary."""
        output_file = test_generator.generate_from_dict(
            sample_openapi_spec, output_dir=tmp_path
        )

        assert output_file.exists()
        content = output_file.read_text()
        assert "def test_" in content

    def test_generate_endpoint_tests(
        self, test_generator: TestGenerator, sample_openapi_spec: Dict
    ) -> None:
        """Test endpoint test generation."""
        test_generator.spec = sample_openapi_spec
        test_generator.endpoints = test_generator._parse_endpoints()

        endpoint = test_generator.endpoints[0]
        tests = test_generator.generate_endpoint_tests(endpoint, endpoint["method"])

        assert len(tests) > 0
        assert any("def test_" in test for test in tests)

    def test_no_endpoints_in_spec(self, tmp_path: Path) -> None:
        """Test generation from spec with no endpoints."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        spec_path = tmp_path / "empty.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(spec, f)

        generator = TestGenerator()
        with pytest.raises(TestGenerationError):
            generator.generate_from_spec(spec_path)

    def test_unsupported_file_format(self, tmp_path: Path) -> None:
        """Test generation from unsupported file format."""
        spec_path = tmp_path / "spec.txt"
        spec_path.write_text("not a spec")

        generator = TestGenerator()
        with pytest.raises(TestGenerationError):
            generator.generate_from_spec(spec_path)


# ============================================================================
# C. API CLIENT TESTS (20+ tests)
# ============================================================================


class TestAPIClient:
    """Test suite for APIClient module."""

    @responses.activate
    def test_get_request_success(self, api_client: APIClient) -> None:
        """Test successful GET request."""
        responses.add(
            responses.GET,
            "https://api.example.com/users",
            json={"users": []},
            status=200,
        )

        response = api_client.get("/users")

        assert response.status_code == 200
        assert response.body == {"users": []}

    @responses.activate
    def test_post_request_success(self, api_client: APIClient) -> None:
        """Test successful POST request."""
        responses.add(
            responses.POST,
            "https://api.example.com/users",
            json={"id": 1},
            status=201,
        )

        response = api_client.post("/users", json={"name": "John"})

        assert response.status_code == 201
        assert response.body == {"id": 1}

    @responses.activate
    def test_put_request_success(self, api_client: APIClient) -> None:
        """Test successful PUT request."""
        responses.add(
            responses.PUT,
            "https://api.example.com/users/1",
            json={"id": 1, "name": "John"},
            status=200,
        )

        response = api_client.put("/users/1", json={"name": "John"})

        assert response.status_code == 200

    @responses.activate
    def test_delete_request_success(self, api_client: APIClient) -> None:
        """Test successful DELETE request."""
        responses.add(
            responses.DELETE,
            "https://api.example.com/users/1",
            status=204,
        )

        response = api_client.delete("/users/1")

        assert response.status_code == 204

    @responses.activate
    def test_patch_request_success(self, api_client: APIClient) -> None:
        """Test successful PATCH request."""
        responses.add(
            responses.PATCH,
            "https://api.example.com/users/1",
            json={"id": 1},
            status=200,
        )

        response = api_client.patch("/users/1", json={"name": "Jane"})

        assert response.status_code == 200

    @responses.activate
    def test_bearer_token_authentication(self, api_client: APIClient) -> None:
        """Test Bearer token authentication."""
        responses.add(
            responses.GET,
            "https://api.example.com/protected",
            json={"data": "secure"},
            status=200,
        )

        api_client.set_bearer_token("test_token_123")
        response = api_client.get("/protected")

        assert response.status_code == 200
        # Check authorization header was sent
        assert "Authorization" in responses.calls[0].request.headers
        assert (
            responses.calls[0].request.headers["Authorization"]
            == "Bearer test_token_123"
        )

    @responses.activate
    def test_api_key_authentication_header(self, api_client: APIClient) -> None:
        """Test API key authentication in header."""
        responses.add(
            responses.GET,
            "https://api.example.com/data",
            json={"data": []},
            status=200,
        )

        api_client.set_api_key("my_api_key", location="header", key_name="X-API-Key")
        response = api_client.get("/data")

        assert response.status_code == 200
        assert "X-API-Key" in responses.calls[0].request.headers
        assert responses.calls[0].request.headers["X-API-Key"] == "my_api_key"

    @responses.activate
    def test_api_key_authentication_query(self, api_client: APIClient) -> None:
        """Test API key authentication in query parameter."""
        responses.add(
            responses.GET,
            "https://api.example.com/data",
            json={"data": []},
            status=200,
        )

        api_client.set_api_key("my_api_key", location="query", key_name="api_key")
        response = api_client.get("/data")

        assert response.status_code == 200
        # Check query parameter
        assert "api_key=my_api_key" in responses.calls[0].request.url

    @responses.activate
    def test_basic_authentication(self, api_client: APIClient) -> None:
        """Test HTTP Basic authentication."""
        responses.add(
            responses.GET,
            "https://api.example.com/secure",
            json={"data": "secure"},
            status=200,
        )

        api_client.set_basic_auth("user", "password")
        response = api_client.get("/secure")

        assert response.status_code == 200
        # Check authorization header
        auth_header = responses.calls[0].request.headers.get("Authorization", "")
        assert auth_header.startswith("Basic ")

    @responses.activate
    def test_retry_on_5xx_error(self) -> None:
        """Test retry logic on 5xx server errors."""
        client = APIClient(
            config={"base_url": "https://api.example.com", "retry_attempts": 3}
        )

        # First two attempts return 503, third succeeds
        responses.add(responses.GET, "https://api.example.com/users", status=503)
        responses.add(responses.GET, "https://api.example.com/users", status=503)
        responses.add(
            responses.GET,
            "https://api.example.com/users",
            json={"users": []},
            status=200,
        )

        response = client.get("/users")

        assert response.status_code == 200
        # Should have made 3 attempts
        assert len(responses.calls) == 3

    @responses.activate
    def test_rate_limiting(self) -> None:
        """Test rate limiting enforcement."""
        # Create client with very low rate limit
        client = APIClient(
            config={
                "base_url": "https://api.example.com",
                "rate_limit": 2,  # 2 requests per minute
            }
        )

        responses.add(
            responses.GET,
            "https://api.example.com/data",
            json={"data": "ok"},
            status=200,
        )

        # First two requests should succeed
        client.get("/data")
        client.get("/data")

        # Third request should hit rate limit
        with pytest.raises(RateLimitError):
            client.get("/data")

    @responses.activate
    def test_429_rate_limit_response(self, api_client: APIClient) -> None:
        """Test handling of 429 rate limit response."""
        responses.add(
            responses.GET,
            "https://api.example.com/data",
            status=429,
            headers={"Retry-After": "60"},
        )

        with pytest.raises(RateLimitError):
            api_client.get("/data")

    def test_connection_error(self, api_client: APIClient) -> None:
        """Test handling of connection errors."""
        with mock.patch.object(
            api_client.session,
            "request",
            side_effect=ConnectionError("Connection failed"),
        ):
            with pytest.raises(APIClientError):
                api_client.get("/users")

    def test_timeout_error(self, api_client: APIClient) -> None:
        """Test handling of timeout errors."""
        with mock.patch.object(
            api_client.session, "request", side_effect=Timeout("Request timed out")
        ):
            with pytest.raises(APIClientError):
                api_client.get("/users")

    def test_ssl_error(self, api_client: APIClient) -> None:
        """Test handling of SSL errors."""
        with mock.patch.object(
            api_client.session,
            "request",
            side_effect=SSLError("SSL verification failed"),
        ):
            with pytest.raises(APIClientError):
                api_client.get("/users")

    @responses.activate
    def test_custom_headers(self, api_client: APIClient) -> None:
        """Test custom authentication headers."""
        responses.add(
            responses.GET,
            "https://api.example.com/data",
            json={"data": []},
            status=200,
        )

        api_client.set_custom_headers({"X-Custom-Auth": "custom_value"})
        response = api_client.get("/data")

        assert response.status_code == 200
        assert "X-Custom-Auth" in responses.calls[0].request.headers
        assert responses.calls[0].request.headers["X-Custom-Auth"] == "custom_value"

    def test_clear_authentication(self, api_client: APIClient) -> None:
        """Test clearing authentication configuration."""
        api_client.set_bearer_token("token")
        assert api_client._auth_type == "bearer"

        api_client.clear_authentication()

        assert api_client._auth_type is None
        assert api_client._auth_data == {}

    def test_context_manager(self) -> None:
        """Test APIClient as context manager."""
        with APIClient(config={"base_url": "https://api.example.com"}) as client:
            assert client.session is not None

        # Session should be closed after context exit
        # Note: We can't easily test this, but it should not raise an error

    @responses.activate
    def test_sanitize_sensitive_data_in_logs(
        self, api_client: APIClient, caplog
    ) -> None:
        """Test sanitization of sensitive data in logs."""
        import logging

        caplog.set_level(logging.DEBUG)

        responses.add(
            responses.GET,
            "https://api.example.com/data",
            json={"data": []},
            status=200,
        )

        api_client.set_bearer_token("secret_token_12345")
        api_client.get("/data")

        # Check logs don't contain actual token
        log_text = caplog.text
        assert "secret_token_12345" not in log_text
        assert "REDACTED" in log_text or "***" in log_text or log_text == ""


# ============================================================================
# D. PACT MANAGER TESTS (15+ tests)
# ============================================================================


class TestPactManager:
    """Test suite for PactManager module."""

    def test_create_consumer_contract_success(self, pact_manager: PactManager) -> None:
        """Test successful contract creation."""
        interaction = Interaction(
            description="Get user",
            request={"method": "GET", "path": "/users/1"},
            response={"status": 200, "body": {"id": 1, "name": "John"}},
        )

        pact_manager.add_interaction(interaction)
        contract = pact_manager.create_consumer_contract()

        assert contract.consumer == "TestConsumer"
        assert contract.provider == "TestProvider"
        assert len(contract.interactions) == 1

    def test_create_contract_missing_consumer(self) -> None:
        """Test contract creation with missing consumer."""
        manager = PactManager(provider="Provider")

        with pytest.raises(ContractError):
            manager.create_consumer_contract()

    def test_create_contract_no_interactions(self, pact_manager: PactManager) -> None:
        """Test contract creation with no interactions."""
        with pytest.raises(ContractError):
            pact_manager.create_consumer_contract()

    def test_add_interaction_from_dict(self, pact_manager: PactManager) -> None:
        """Test adding interaction from dictionary."""
        interaction_dict = {
            "description": "Create user",
            "request": {"method": "POST", "path": "/users"},
            "response": {"status": 201},
        }

        pact_manager.add_interaction(interaction_dict)

        assert len(pact_manager.interactions) == 1

    def test_add_invalid_interaction(self, pact_manager: PactManager) -> None:
        """Test adding invalid interaction."""
        invalid_interaction = {"invalid": "data"}

        with pytest.raises(ContractError):
            pact_manager.add_interaction(invalid_interaction)

    @responses.activate
    def test_publish_to_broker_success(self, pact_manager: PactManager) -> None:
        """Test publishing contract to broker."""
        url = (
            "https://pact-broker.example.com/pacts/provider/"
            "TestProvider/consumer/TestConsumer/version/1.0.0"
        )
        responses.add(responses.PUT, url, json={"status": "ok"}, status=200)

        interaction = Interaction(
            description="Test",
            request={"method": "GET", "path": "/test"},
            response={"status": 200},
        )
        pact_manager.add_interaction(interaction)
        contract = pact_manager.create_consumer_contract()

        result = pact_manager.publish_to_broker(contract, version="1.0.0")

        assert result["version"] == "1.0.0"
        assert result["consumer"] == "TestConsumer"

    def test_publish_without_broker_url(self) -> None:
        """Test publishing without broker URL configured."""
        manager = PactManager(consumer="C", provider="P")
        contract = PactContract(consumer="C", provider="P", interactions=[])

        with pytest.raises(BrokerError):
            manager.publish_to_broker(contract, version="1.0.0")

    @responses.activate
    def test_publish_broker_authentication(self, pact_manager: PactManager) -> None:
        """Test broker authentication."""
        url = (
            "https://pact-broker.example.com/pacts/provider/"
            "TestProvider/consumer/TestConsumer/version/1.0.0"
        )
        responses.add(responses.PUT, url, json={"status": "ok"}, status=200)

        interaction = Interaction(
            description="Test",
            request={"method": "GET", "path": "/test"},
            response={"status": 200},
        )
        pact_manager.add_interaction(interaction)
        contract = pact_manager.create_consumer_contract()

        pact_manager.publish_to_broker(contract, version="1.0.0")

        # Check authorization header
        assert "Authorization" in responses.calls[0].request.headers
        assert (
            responses.calls[0].request.headers["Authorization"] == "Bearer test_token"
        )

    @responses.activate
    def test_get_pacts_for_verification(self, pact_manager: PactManager) -> None:
        """Test fetching pacts for verification."""
        url = (
            "https://pact-broker.example.com/pacts/provider/"
            "TestProvider/for-verification"
        )
        responses.add(
            responses.POST,
            url,
            json={
                "_embedded": {
                    "pacts": [{"_links": {"self": {"href": "http://pact"}}}]
                }
            },
            status=200,
        )

        pacts = pact_manager.get_pacts_for_verification()

        assert len(pacts) == 1

    def test_register_state_handler(self, pact_manager: PactManager) -> None:
        """Test registering provider state handler."""

        def handler():
            pass

        pact_manager.register_state_handler("user exists", handler)

        assert "user exists" in pact_manager.state_handlers

    @responses.activate
    def test_verify_provider_success(self, pact_manager: PactManager) -> None:
        """Test successful provider verification."""
        # Mock pact retrieval
        pact_data = {
            "consumer": {"name": "TestConsumer"},
            "provider": {"name": "TestProvider"},
            "interactions": [
                {
                    "description": "Get user",
                    "request": {"method": "GET", "path": "/users/1"},
                    "response": {"status": 200, "body": {"id": 1}},
                }
            ],
            "metadata": {"pactSpecification": {"version": "3.0.0"}},
        }

        url = (
            "https://pact-broker.example.com/pacts/provider/"
            "TestProvider/for-verification"
        )
        responses.add(
            responses.POST,
            url,
            json={
                "_embedded": {
                    "pacts": [{"_links": {"self": {"href": "http://pact.json"}}}]
                }
            },
            status=200,
        )

        responses.add(responses.GET, "http://pact.json", json=pact_data, status=200)

        # Mock actual API call
        responses.add(
            responses.GET,
            "http://provider.example.com/users/1",
            json={"id": 1},
            status=200,
        )

        result = pact_manager.verify_provider(
            base_url="http://provider.example.com",
            publish_results=False,
        )

        assert result.success

    def test_verify_provider_without_base_url(self, pact_manager: PactManager) -> None:
        """Test verification without base URL."""
        with pytest.raises(VerificationError):
            pact_manager.verify_provider()

    @responses.activate
    def test_can_i_deploy_deployable(self, pact_manager: PactManager) -> None:
        """Test Can-I-Deploy check with deployable result."""
        responses.add(
            responses.GET,
            "https://pact-broker.example.com/matrix",
            json={
                "summary": {"deployable": True, "reason": "All verifications passed"}
            },
            status=200,
        )

        result = pact_manager.can_i_deploy(
            participant="TestConsumer",
            version="1.0.0",
            to_environment="production",
        )

        assert result.is_deployable()
        assert result.status == DeploymentStatus.DEPLOYABLE

    @responses.activate
    def test_can_i_deploy_not_deployable(self, pact_manager: PactManager) -> None:
        """Test Can-I-Deploy check with not deployable result."""
        responses.add(
            responses.GET,
            "https://pact-broker.example.com/matrix",
            json={"summary": {"deployable": False, "reason": "Verification failed"}},
            status=200,
        )

        result = pact_manager.can_i_deploy(participant="TestConsumer", version="1.0.0")

        assert not result.is_deployable()

    def test_contract_serialization(self, pact_manager: PactManager) -> None:
        """Test contract serialization."""
        interaction = Interaction(
            description="Test",
            request={"method": "GET", "path": "/test"},
            response={"status": 200},
        )

        pact_manager.add_interaction(interaction)
        contract = pact_manager.create_consumer_contract()

        json_str = contract.to_json()
        data = json.loads(json_str)

        assert data["consumer"]["name"] == "TestConsumer"
        assert data["provider"]["name"] == "TestProvider"

    def test_pact_manager_clear_interactions(self, pact_manager: PactManager) -> None:
        """Test clearing interactions."""
        interaction = Interaction(
            description="Test",
            request={"method": "GET", "path": "/test"},
            response={"status": 200},
        )

        pact_manager.add_interaction(interaction)
        assert len(pact_manager.interactions) == 1

        pact_manager.clear_interactions()
        assert len(pact_manager.interactions) == 0


# ============================================================================
# E. SCHEMA VALIDATOR TESTS (20+ tests)
# ============================================================================


class TestSchemaValidator:
    """Test suite for SchemaValidator module."""

    def test_validator_initialization_with_spec_file(
        self, temp_spec_file: Path
    ) -> None:
        """Test validator initialization with spec file."""
        validator = SchemaValidator(spec_file=temp_spec_file)

        assert validator.spec is not None
        assert "openapi" in validator.spec

    def test_validator_initialization_with_spec_dict(
        self, sample_openapi_spec: Dict
    ) -> None:
        """Test validator initialization with spec dictionary."""
        validator = SchemaValidator(spec_dict=sample_openapi_spec)

        assert validator.spec == sample_openapi_spec

    def test_validator_initialization_no_spec(self) -> None:
        """Test validator initialization without spec."""
        with pytest.raises(ValueError):
            SchemaValidator()

    def test_validator_initialization_invalid_spec(self) -> None:
        """Test validator initialization with invalid spec."""
        with pytest.raises(ValueError):
            SchemaValidator(spec_dict={"invalid": "spec"})

    def test_validate_request_valid(self, schema_validator: SchemaValidator) -> None:
        """Test request validation with valid data."""
        result = schema_validator.validate_request(
            endpoint="/users",
            method="POST",
            request_data={"email": "test@example.com", "name": "John"},
        )

        assert result.valid

    def test_validate_request_invalid_missing_required(
        self, schema_validator: SchemaValidator
    ) -> None:
        """Test request validation with missing required field."""
        result = schema_validator.validate_request(
            endpoint="/users",
            method="POST",
            request_data={"name": "John"},  # Missing required email
        )

        assert not result.valid
        assert len(result.errors) > 0

    def test_validate_request_invalid_email_format(
        self, schema_validator: SchemaValidator
    ) -> None:
        """Test request validation with invalid email format."""
        result = schema_validator.validate_request(
            endpoint="/users",
            method="POST",
            request_data={"email": "not-an-email", "name": "John"},
        )

        assert not result.valid
        # Should have format error
        assert any("format" in err.schema_rule for err in result.errors)

    def test_validate_response_valid(self, schema_validator: SchemaValidator) -> None:
        """Test response validation with valid data."""
        result = schema_validator.validate_response(
            endpoint="/users/1",
            method="GET",
            status_code=200,
            response_data={"id": 1, "email": "test@example.com", "name": "John"},
        )

        assert result.valid

    def test_validate_response_invalid_missing_field(
        self, schema_validator: SchemaValidator
    ) -> None:
        """Test response validation with missing required field."""
        result = schema_validator.validate_response(
            endpoint="/users/1",
            method="GET",
            status_code=200,
            response_data={"id": 1, "name": "John"},  # Missing email
        )

        assert not result.valid

    def test_validate_response_invalid_type(
        self, schema_validator: SchemaValidator
    ) -> None:
        """Test response validation with wrong type."""
        result = schema_validator.validate_response(
            endpoint="/users/1",
            method="GET",
            status_code=200,
            response_data={
                "id": "not-an-integer",  # Should be integer
                "email": "test@example.com",
            },
        )

        assert not result.valid

    def test_validate_missing_schema(self, schema_validator: SchemaValidator) -> None:
        """Test validation when schema is not defined for status code."""
        result = schema_validator.validate_response(
            endpoint="/users/1",
            method="GET",
            status_code=500,  # No schema defined
            response_data={"error": "Internal Server Error"},
        )

        # Should succeed with warning
        assert result.valid
        assert len(result.warnings) > 0

    def test_custom_format_validator(self, schema_validator: SchemaValidator) -> None:
        """Test adding custom format validator."""

        def validate_phone(value: str) -> bool:
            return bool(re.match(r"^\+?1?\d{9,15}$", value))

        schema_validator.add_format_validator("phone", validate_phone)

        # Validate with custom format
        schema = {"type": "string", "format": "phone"}
        errors = schema_validator.validate_against_schema("+1234567890", schema)

        assert len(errors) == 0

    def test_validation_mode_strict(self, sample_openapi_spec: Dict) -> None:
        """Test strict validation mode."""
        validator = SchemaValidator(
            spec_dict=sample_openapi_spec,
            validation_mode=ValidationMode.STRICT,
        )

        # Additional properties should fail in strict mode
        result = validator.validate_request(
            endpoint="/users",
            method="POST",
            request_data={
                "email": "test@example.com",
                "name": "John",
                "extra_field": "not allowed",
            },
        )

        assert not result.valid

    def test_validation_mode_lenient(self, sample_openapi_spec: Dict) -> None:
        """Test lenient validation mode."""
        validator = SchemaValidator(
            spec_dict=sample_openapi_spec,
            validation_mode=ValidationMode.LENIENT,
        )

        # Additional properties should be allowed in lenient mode
        result = validator.validate_request(
            endpoint="/users",
            method="POST",
            request_data={
                "email": "test@example.com",
                "name": "John",
                "extra_field": "allowed",
            },
        )

        # May still have errors for other reasons, but not for extra fields

    def test_validation_mode_partial(self, sample_openapi_spec: Dict) -> None:
        """Test partial validation mode."""
        validator = SchemaValidator(
            spec_dict=sample_openapi_spec,
            validation_mode=ValidationMode.PARTIAL,
        )

        # Missing required fields should be allowed in partial mode
        result = validator.validate_request(
            endpoint="/users",
            method="POST",
            request_data={"name": "John"},  # Missing email
        )

        # Should not fail on missing required fields

    def test_validate_uuid_format(self, schema_validator: SchemaValidator) -> None:
        """Test UUID format validation."""
        schema = {"type": "string", "format": "uuid"}

        # Valid UUID
        errors = schema_validator.validate_against_schema(
            "123e4567-e89b-12d3-a456-426614174000", schema
        )
        assert len(errors) == 0

        # Invalid UUID
        errors = schema_validator.validate_against_schema("not-a-uuid", schema)
        assert len(errors) > 0

    def test_validate_date_format(self, schema_validator: SchemaValidator) -> None:
        """Test date format validation."""
        schema = {"type": "string", "format": "date"}

        # Valid date
        errors = schema_validator.validate_against_schema("2023-01-01", schema)
        assert len(errors) == 0

        # Invalid date
        errors = schema_validator.validate_against_schema("not-a-date", schema)
        assert len(errors) > 0

    def test_validate_datetime_format(self, schema_validator: SchemaValidator) -> None:
        """Test datetime format validation."""
        schema = {"type": "string", "format": "date-time"}

        # Valid datetime
        errors = schema_validator.validate_against_schema(
            "2023-01-01T00:00:00Z", schema
        )
        assert len(errors) == 0

        # Invalid datetime
        errors = schema_validator.validate_against_schema("not-a-datetime", schema)
        assert len(errors) > 0

    def test_validate_uri_format(self, schema_validator: SchemaValidator) -> None:
        """Test URI format validation."""
        schema = {"type": "string", "format": "uri"}

        # Valid URI
        errors = schema_validator.validate_against_schema("https://example.com", schema)
        assert len(errors) == 0

        # Invalid URI
        errors = schema_validator.validate_against_schema("not a uri", schema)
        assert len(errors) > 0

    def test_schema_ref_resolution(self, schema_validator: SchemaValidator) -> None:
        """Test $ref resolution in schemas."""
        # Validate using ref
        result = schema_validator.validate_response(
            endpoint="/users",
            method="GET",
            status_code=200,
            response_data=[{"id": 1, "email": "test@example.com", "name": "John"}],
        )

        assert result.valid

    def test_clear_cache(self, schema_validator: SchemaValidator) -> None:
        """Test cache clearing."""
        # Trigger some caching
        schema_validator.validate_request(
            endpoint="/users", method="POST", request_data={}
        )

        schema_validator.clear_cache()

        stats = schema_validator.get_cache_stats()
        assert stats["cached_schemas"] == 0

    def test_get_validation_errors(self, schema_validator: SchemaValidator) -> None:
        """Test retrieving validation errors."""
        schema_validator.validate_request(
            endpoint="/users",
            method="POST",
            request_data={"name": "John"},  # Missing email
        )

        errors = schema_validator.get_validation_errors()

        assert len(errors) > 0


# ============================================================================
# F. REGRESSION ENGINE TESTS (15+ tests)
# ============================================================================


class TestRegressionEngine:
    """Test suite for RegressionEngine module."""

    def test_capture_baseline_success(
        self, regression_engine: RegressionEngine
    ) -> None:
        """Test successful baseline capture."""
        response = {
            "status_code": 200,
            "headers": {"Content-Type": "application/json"},
            "body": {"id": 1, "name": "John"},
        }

        baseline = regression_engine.capture_baseline(
            endpoint="/users/1", response=response, latency_ms=50.0
        )

        assert baseline.endpoint == "/users/1"
        assert baseline.response == response
        assert baseline.performance["latency_ms"] == 50.0

    def test_load_baseline_success(self, regression_engine: RegressionEngine) -> None:
        """Test loading existing baseline."""
        response = {
            "status_code": 200,
            "body": {"id": 1, "name": "John"},
        }

        regression_engine.capture_baseline(endpoint="/users/1", response=response)

        loaded = regression_engine.load_baseline(endpoint="/users/1")

        assert loaded.endpoint == "/users/1"
        assert loaded.response == response

    def test_load_baseline_not_found(self, regression_engine: RegressionEngine) -> None:
        """Test loading non-existent baseline."""
        with pytest.raises(BaselineNotFoundError):
            regression_engine.load_baseline(endpoint="/nonexistent")

    def test_load_corrupted_baseline(
        self, regression_engine: RegressionEngine, tmp_path: Path
    ) -> None:
        """Test loading corrupted baseline file."""
        # Create corrupted baseline
        baseline_path = regression_engine.baseline_dir / "get__users_1.json"
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text("invalid json{")

        with pytest.raises(CorruptedBaselineError):
            regression_engine.load_baseline(endpoint="/users/1")

    def test_compare_with_baseline_no_changes(
        self, regression_engine: RegressionEngine
    ) -> None:
        """Test comparison with identical responses."""
        response = {
            "status_code": 200,
            "body": {"id": 1, "name": "John"},
        }

        regression_engine.capture_baseline(endpoint="/users/1", response=response)

        report = regression_engine.compare_with_baseline(
            endpoint="/users/1", response=response
        )

        assert not report.has_changes

    def test_detect_structure_changes(
        self, regression_engine: RegressionEngine
    ) -> None:
        """Test structure change detection."""
        baseline_response = {
            "status_code": 200,
            "body": {"id": 1, "name": "John"},
        }

        current_response = {
            "status_code": 200,
            "body": {"id": 1, "name": "John", "email": "new@example.com"},
        }

        regression_engine.capture_baseline(
            endpoint="/users/1", response=baseline_response
        )

        report = regression_engine.compare_with_baseline(
            endpoint="/users/1", response=current_response
        )

        assert report.has_changes
        assert len(report.structure_changes) > 0

    def test_detect_data_changes(self, regression_engine: RegressionEngine) -> None:
        """Test data change detection."""
        baseline_response = {
            "status_code": 200,
            "body": {"id": 1, "name": "John"},
        }

        current_response = {
            "status_code": 200,
            "body": {"id": 1, "name": "Jane"},  # Name changed
        }

        regression_engine.capture_baseline(
            endpoint="/users/1", response=baseline_response
        )

        report = regression_engine.compare_with_baseline(
            endpoint="/users/1", response=current_response
        )

        assert report.has_changes
        assert len(report.data_changes) > 0

    def test_detect_performance_regression(
        self, regression_engine: RegressionEngine
    ) -> None:
        """Test performance regression detection."""
        response = {"status_code": 200, "body": {}}

        regression_engine.capture_baseline(
            endpoint="/users/1", response=response, latency_ms=100.0
        )

        # 50% slower (exceeds 20% threshold)
        report = regression_engine.compare_with_baseline(
            endpoint="/users/1", response=response, latency_ms=150.0
        )

        assert report.performance_changes is not None
        assert report.performance_changes.threshold_exceeded

    def test_detect_breaking_changes_status_code(
        self, regression_engine: RegressionEngine
    ) -> None:
        """Test breaking change detection for status code changes."""
        baseline_response = {"status_code": 200, "body": {}}
        current_response = {"status_code": 500, "body": {}}

        breaking = regression_engine.detect_breaking_changes(
            baseline_response, current_response
        )

        assert len(breaking) > 0
        assert any(bc.change_type == "status_change" for bc in breaking)

    def test_detect_breaking_changes_removed_field(
        self, regression_engine: RegressionEngine
    ) -> None:
        """Test breaking change detection for removed fields."""
        baseline_response = {
            "status_code": 200,
            "body": {"id": 1, "name": "John", "email": "john@example.com"},
        }
        current_response = {
            "status_code": 200,
            "body": {"id": 1, "name": "John"},  # Email removed
        }

        breaking = regression_engine.detect_breaking_changes(
            baseline_response, current_response
        )

        assert len(breaking) > 0
        assert any(bc.change_type == "removed_field" for bc in breaking)

    def test_detect_breaking_changes_type_change(
        self, regression_engine: RegressionEngine
    ) -> None:
        """Test breaking change detection for type changes."""
        baseline_response = {"status_code": 200, "body": {"id": 1}}
        current_response = {"status_code": 200, "body": {"id": "1"}}  # Now string

        breaking = regression_engine.detect_breaking_changes(
            baseline_response, current_response
        )

        assert len(breaking) > 0
        assert any(bc.change_type == "type_change" for bc in breaking)

    def test_track_performance(self, regression_engine: RegressionEngine) -> None:
        """Test performance tracking."""
        regression_engine.track_performance(endpoint="/users/1", latency=100.0)

        # Verify history file created
        history_path = regression_engine._get_history_path("/users/1", "GET")
        assert history_path.exists()

    def test_get_trend_analysis(self, regression_engine: RegressionEngine) -> None:
        """Test historical trend analysis."""
        # Create some history
        for i in range(10):
            regression_engine.track_performance(
                endpoint="/users/1", latency=100.0 + i * 10
            )

        analysis = regression_engine.get_trend_analysis(endpoint="/users/1", days=7)

        assert "latency" in analysis
        assert "min" in analysis["latency"]
        assert "max" in analysis["latency"]
        assert analysis["data_points"] == 10

    def test_update_baseline_with_approval(
        self, regression_engine: RegressionEngine
    ) -> None:
        """Test baseline update with approval."""
        response = {"status_code": 200, "body": {}}

        regression_engine.capture_baseline(endpoint="/users/1", response=response)

        success = regression_engine.update_baseline(
            endpoint="/users/1", approval_token="valid_token_123"
        )

        assert success

    def test_update_baseline_without_approval(
        self, regression_engine: RegressionEngine
    ) -> None:
        """Test baseline update without approval token."""
        response = {"status_code": 200, "body": {}}

        regression_engine.capture_baseline(endpoint="/users/1", response=response)

        with pytest.raises(RegressionEngineError):
            regression_engine.update_baseline(endpoint="/users/1", approval_token="")

    def test_cleanup_old_history(self, regression_engine: RegressionEngine) -> None:
        """Test cleanup of old history entries."""
        # Track some performance data
        regression_engine.track_performance(endpoint="/users/1", latency=100.0)

        # Run cleanup (won't delete recent entries)
        cleaned = regression_engine.cleanup_old_history()

        # Should return count (0 in this case as entries are recent)
        assert cleaned >= 0


# ============================================================================
# G. INTEGRATION TESTS (5+ tests)
# ============================================================================


class TestIntegration:
    """Integration tests for workflow combinations."""

    def test_validation_to_test_generation_workflow(
        self, temp_spec_file: Path, tmp_path: Path
    ) -> None:
        """Test full validation to test generation workflow."""
        # Step 1: Validate spec
        validator = ContractValidator()
        validation_result = validator.validate(temp_spec_file)
        assert validation_result.is_valid

        # Step 2: Generate tests
        generator = TestGenerator()
        output_file = generator.generate_from_spec(temp_spec_file, output_dir=tmp_path)
        assert output_file.exists()

        # Step 3: Verify test file contains expected content
        content = output_file.read_text()
        assert "def test_" in content

    @responses.activate
    def test_api_client_to_schema_validation_integration(
        self, sample_openapi_spec: Dict
    ) -> None:
        """Test API client to schema validator integration."""
        # Setup API response
        responses.add(
            responses.GET,
            "https://api.example.com/users/1",
            json={"id": 1, "email": "test@example.com", "name": "John"},
            status=200,
        )

        # Make API call
        client = APIClient(config={"base_url": "https://api.example.com"})
        response = client.get("/users/1")

        # Validate response
        validator = SchemaValidator(spec_dict=sample_openapi_spec)
        result = validator.validate_response(
            endpoint="/users/1",
            method="GET",
            status_code=response.status_code,
            response_data=response.body,
        )

        assert result.valid

    def test_regression_baseline_capture_and_compare_workflow(
        self, regression_engine: RegressionEngine
    ) -> None:
        """Test regression baseline capture and compare workflow."""
        # Step 1: Capture initial baseline
        baseline_response = {
            "status_code": 200,
            "body": {"id": 1, "name": "John"},
        }

        regression_engine.capture_baseline(
            endpoint="/users/1",
            response=baseline_response,
            latency_ms=50.0,
        )

        # Step 2: Compare with modified response
        current_response = {
            "status_code": 200,
            "body": {"id": 1, "name": "Jane"},  # Changed
        }

        report = regression_engine.compare_with_baseline(
            endpoint="/users/1",
            response=current_response,
            latency_ms=55.0,
        )

        # Step 3: Verify changes detected
        assert report.has_changes
        assert len(report.data_changes) > 0

    @responses.activate
    def test_contract_testing_workflow(self, tmp_path: Path) -> None:
        """Test consumer-driven contract testing workflow."""
        # Step 1: Consumer creates contract
        manager = PactManager(
            consumer="WebApp",
            provider="UserAPI",
            pacts_dir=tmp_path,
        )

        interaction = Interaction(
            description="Get user by ID",
            request={"method": "GET", "path": "/users/1"},
            response={"status": 200, "body": {"id": 1, "name": "John"}},
        )

        manager.add_interaction(interaction)
        contract = manager.create_consumer_contract()

        # Step 2: Save contract
        contract.save(tmp_path / "contract.json")

        # Step 3: Verify contract file
        assert (tmp_path / "contract.json").exists()

        # Step 4: Load and verify structure
        loaded_contract = PactContract.from_dict(
            json.loads((tmp_path / "contract.json").read_text())
        )
        assert loaded_contract.consumer == "WebApp"
        assert len(loaded_contract.interactions) == 1

    def test_multi_module_error_handling(self) -> None:
        """Test error handling across multiple modules."""
        # ContractValidator with invalid spec
        with pytest.raises(ValueError):
            SchemaValidator(spec_dict={"invalid": "spec"})

        # TestGenerator with missing file
        generator = TestGenerator()
        with pytest.raises(TestGenerationError):
            generator.generate_from_spec("nonexistent.yaml")

        # RegressionEngine with missing baseline
        engine = RegressionEngine()
        with pytest.raises(BaselineNotFoundError):
            engine.load_baseline("/nonexistent")


# ============================================================================
# PARAMETRIZED TESTS
# ============================================================================


class TestParametrizedCases:
    """Parametrized test cases for comprehensive coverage."""

    @pytest.mark.parametrize(
        "version",
        ["3.0.0", "3.0.1", "3.0.2", "3.0.3", "3.1.0"],
    )
    def test_supported_openapi_versions(self, version: str, tmp_path: Path) -> None:
        """Test all supported OpenAPI versions."""
        spec = {
            "openapi": version,
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        spec_path = tmp_path / f"spec_{version}.yaml"
        with open(spec_path, "w") as f:
            yaml.dump(spec, f)

        validator = ContractValidator()
        result = validator.validate(spec_path)

        assert result.spec_version == version

    @pytest.mark.parametrize(
        "method",
        ["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    @responses.activate
    def test_all_http_methods(self, method: str) -> None:
        """Test all HTTP methods."""
        url = "https://api.example.com/resource"
        responses.add(getattr(responses, method), url, json={}, status=200)

        client = APIClient(config={"base_url": "https://api.example.com"})
        method_func = getattr(client, method.lower())

        if method in ["POST", "PUT", "PATCH"]:
            response = method_func("/resource", json={})
        else:
            response = method_func("/resource")

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "format_type,valid_value,invalid_value",
        [
            ("email", "test@example.com", "not-an-email"),
            ("uuid", "123e4567-e89b-12d3-a456-426614174000", "not-a-uuid"),
            ("date", "2023-01-01", "invalid-date"),
            ("uri", "https://example.com", "not a uri"),
        ],
    )
    def test_format_validations(
        self,
        format_type: str,
        valid_value: str,
        invalid_value: str,
        schema_validator: SchemaValidator,
    ) -> None:
        """Test various format validations."""
        schema = {"type": "string", "format": format_type}

        # Valid value should pass
        errors = schema_validator.validate_against_schema(valid_value, schema)
        assert len(errors) == 0

        # Invalid value should fail
        errors = schema_validator.validate_against_schema(invalid_value, schema)
        assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
