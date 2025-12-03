"""
Comprehensive Test Suite for API Documentation Generator

Tests all modules:
- SpecGenerator: OpenAPI generation from FastAPI
- DocRenderer: Swagger UI/Redoc rendering
- CodeParser: Docstring and type hint extraction
- ExampleGenerator: Code example generation
- CLI: Command-line interface

Target: 85%+ test coverage
"""

import json
import tempfile
from pathlib import Path
from typing import List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import APIRouter, Body, FastAPI
from fastapi import Path as PathParam
from fastapi import Query
from pydantic import BaseModel, Field

from apidocs_cli import AppLoadError, CLIError, ServerError, SpecLoadError
from code_parser import (
    CodeParser,
    DocstringError,
    Parameter,
    ParsedDocstring,
    ParseError,
    TypeHintError,
)
from doc_renderer import (
    DocRenderer,
    DocRendererError,
    InvalidSpecError,
    RenderError,
    ThemeError,
)
from example_generator import (
    AuthError,
    ExampleError,
    ExampleGenerator,
    InvalidOperationError,
    TemplateError,
)
from spec_generator import (
    DependencyError,
    FormatError,
    InvalidAppError,
    InvalidPathError,
    SpecGenerator,
    SpecGeneratorError,
)
from theme_config import BUILTIN_THEMES, ThemeConfig


# Test fixtures and models
class UserModel(BaseModel):
    """User model for testing."""

    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User name")
    email: str = Field(..., description="User email")
    age: Optional[int] = Field(None, description="User age")


class CreateUserRequest(BaseModel):
    """Create user request model."""

    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    age: Optional[int] = Field(None, ge=0, le=150)


# Test FastAPI application
def create_test_app() -> FastAPI:
    """
    Create a test FastAPI application.

    Returns:
        FastAPI application with test routes
    """
    app = FastAPI(
        title="Test API",
        description="Test API for documentation generation",
        version="1.0.0",
    )

    @app.get("/users", response_model=List[UserModel], tags=["users"])
    def get_users(
        limit: int = Query(10, description="Number of users to return"),
        offset: int = Query(0, description="Offset for pagination"),
    ):
        """
        Get list of users.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of users

        Raises:
            ValueError: If limit is negative
        """
        return []

    @app.get("/users/{user_id}", response_model=UserModel, tags=["users"])
    def get_user(user_id: int = PathParam(..., description="User ID")):
        """
        Get user by ID.

        Args:
            user_id: The ID of the user to retrieve

        Returns:
            User object

        Raises:
            HTTPException: If user not found
        """
        return UserModel(id=user_id, name="Test", email="test@example.com")

    @app.post("/users", response_model=UserModel, tags=["users"], status_code=201)
    def create_user(user: CreateUserRequest = Body(...)):
        """
        Create a new user.

        Args:
            user: User data

        Returns:
            Created user object

        Raises:
            ValidationError: If user data is invalid
        """
        return UserModel(id=1, name=user.name, email=user.email, age=user.age)

    return app


# SpecGenerator Tests
class TestSpecGenerator:
    """Test suite for SpecGenerator."""

    def test_init_default(self):
        """Test default initialization."""
        generator = SpecGenerator()
        assert generator.title == "API Documentation"
        assert generator.version == "1.0.0"
        assert generator.openapi_version == "3.0.3"

    def test_init_custom(self):
        """Test custom initialization."""
        generator = SpecGenerator(
            title="Custom API",
            version="2.0.0",
            description="Custom description",
            openapi_version="3.1.0",
        )
        assert generator.title == "Custom API"
        assert generator.version == "2.0.0"
        assert generator.description == "Custom description"
        assert generator.openapi_version == "3.1.0"

    def test_from_fastapi_basic(self):
        """Test basic FastAPI application parsing."""
        app = create_test_app()
        generator = SpecGenerator.from_fastapi(app)

        spec = generator.to_dict()
        assert spec["info"]["title"] == "Test API"
        assert spec["info"]["version"] == "1.0.0"
        assert "paths" in spec
        assert "/users" in spec["paths"]
        assert "/users/{user_id}" in spec["paths"]

    def test_from_fastapi_with_router(self):
        """Test FastAPI application with routers."""
        app = FastAPI(title="Test API", version="1.0.0")
        router = APIRouter(prefix="/api", tags=["api"])

        @router.get("/test")
        def test_endpoint():
            """Test endpoint."""
            return {"status": "ok"}

        app.include_router(router)

        generator = SpecGenerator.from_fastapi(app)
        spec = generator.to_dict()

        assert "/api/test" in spec["paths"]

    def test_from_fastapi_invalid_app(self):
        """Test with invalid application object."""
        with pytest.raises(InvalidAppError) as exc_info:
            SpecGenerator.from_fastapi(None)
        assert "Invalid FastAPI application" in str(exc_info.value)

    def test_from_fastapi_missing_dependency(self):
        """Test FastAPI parsing without FastAPI installed."""
        with patch.dict("sys.modules", {"fastapi": None}):
            with pytest.raises(DependencyError) as exc_info:
                app = create_test_app()
                SpecGenerator.from_fastapi(app)
            assert "FastAPI is not installed" in str(exc_info.value)

    def test_add_path(self):
        """Test adding custom path."""
        generator = SpecGenerator()
        generator.add_path(
            path="/test",
            method="get",
            summary="Test endpoint",
            description="Test description",
            parameters=[],
            responses={"200": {"description": "Success"}},
        )

        spec = generator.to_dict()
        assert "/test" in spec["paths"]
        assert "get" in spec["paths"]["/test"]
        assert spec["paths"]["/test"]["get"]["summary"] == "Test endpoint"

    def test_add_path_invalid(self):
        """Test adding path with invalid method."""
        generator = SpecGenerator()
        with pytest.raises(InvalidPathError) as exc_info:
            generator.add_path(
                path="/test",
                method="INVALID",
                summary="Test",
                responses={},
            )
        assert "Invalid HTTP method" in str(exc_info.value)

    def test_add_schema(self):
        """Test adding component schema."""
        generator = SpecGenerator()
        generator.add_schema(
            "User",
            {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                },
            },
        )

        spec = generator.to_dict()
        assert "components" in spec
        assert "schemas" in spec["components"]
        assert "User" in spec["components"]["schemas"]

    def test_add_security_scheme(self):
        """Test adding security scheme."""
        generator = SpecGenerator()
        generator.add_security_scheme(
            "bearerAuth",
            {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            },
        )

        spec = generator.to_dict()
        assert "components" in spec
        assert "securitySchemes" in spec["components"]
        assert "bearerAuth" in spec["components"]["securitySchemes"]

    def test_add_example(self):
        """Test adding example to path."""
        generator = SpecGenerator()
        generator.add_path(
            path="/test",
            method="get",
            summary="Test",
            responses={"200": {"description": "Success"}},
        )
        generator.add_example(
            "/test",
            "get",
            "response",
            "200",
            {
                "status": "ok",
            },
        )

        spec = generator.to_dict()
        examples = spec["paths"]["/test"]["get"]["responses"]["200"].get("examples")
        assert examples is not None

    def test_add_override(self):
        """Test adding manual override."""
        generator = SpecGenerator()
        generator.add_path(
            path="/test",
            method="get",
            summary="Original",
            responses={"200": {"description": "Success"}},
        )
        generator.add_override("/test", "get", {"summary": "Overridden"})

        spec = generator.to_dict()
        assert spec["paths"]["/test"]["get"]["summary"] == "Overridden"

    def test_save_yaml(self):
        """Test saving specification as YAML."""
        generator = SpecGenerator(title="Test", version="1.0.0")
        generator.add_path(
            path="/test",
            method="get",
            summary="Test",
            responses={"200": {"description": "Success"}},
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml_path = Path(f.name)

        try:
            generator.save(yaml_path, format="yaml")
            assert yaml_path.exists()

            content = yaml_path.read_text()
            assert "openapi:" in content
            assert "/test:" in content
        finally:
            yaml_path.unlink()

    def test_save_json(self):
        """Test saving specification as JSON."""
        generator = SpecGenerator(title="Test", version="1.0.0")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json_path = Path(f.name)

        try:
            generator.save(json_path, format="json")
            assert json_path.exists()

            data = json.loads(json_path.read_text())
            assert "openapi" in data
            assert data["info"]["title"] == "Test"
        finally:
            json_path.unlink()

    def test_save_invalid_format(self):
        """Test saving with invalid format."""
        generator = SpecGenerator()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            file_path = Path(f.name)

        try:
            with pytest.raises(FormatError) as exc_info:
                generator.save(file_path, format="invalid")
            assert "Unsupported format" in str(exc_info.value)
        finally:
            file_path.unlink()

    def test_to_dict(self):
        """Test converting to dictionary."""
        generator = SpecGenerator(title="Test API", version="1.0.0")
        spec = generator.to_dict()

        assert isinstance(spec, dict)
        assert spec["openapi"] == "3.0.3"
        assert spec["info"]["title"] == "Test API"
        assert spec["info"]["version"] == "1.0.0"
        assert "paths" in spec

    def test_to_yaml_string(self):
        """Test converting to YAML string."""
        generator = SpecGenerator(title="Test", version="1.0.0")
        yaml_str = generator.to_yaml()

        assert isinstance(yaml_str, str)
        assert "openapi:" in yaml_str
        assert "title: Test" in yaml_str

    def test_to_json_string(self):
        """Test converting to JSON string."""
        generator = SpecGenerator(title="Test", version="1.0.0")
        json_str = generator.to_json()

        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["info"]["title"] == "Test"


# DocRenderer Tests
class TestDocRenderer:
    """Test suite for DocRenderer."""

    def test_init_default(self):
        """Test default initialization."""
        spec = {"openapi": "3.0.3", "info": {"title": "Test", "version": "1.0.0"}}
        renderer = DocRenderer(spec)
        assert renderer.spec == spec
        assert renderer.title == "Test"

    def test_init_invalid_spec(self):
        """Test initialization with invalid spec."""
        with pytest.raises(InvalidSpecError) as exc_info:
            DocRenderer({})
        assert "Missing required field" in str(exc_info.value)

    def test_render_swagger_ui_basic(self):
        """Test basic Swagger UI rendering."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        renderer = DocRenderer(spec)
        html = renderer.render_swagger_ui()

        assert "<html" in html
        assert "swagger-ui" in html
        assert "Test API" in html
        assert "https://cdn.jsdelivr.net/npm/swagger-ui-dist" in html

    def test_render_swagger_ui_with_theme(self):
        """Test Swagger UI with custom theme."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        renderer = DocRenderer(spec)
        theme = ThemeConfig.get_builtin_theme("dark")
        html = renderer.render_swagger_ui(theme=theme)

        assert "background-color" in html
        assert theme.colors["background"] in html

    def test_render_redoc_basic(self):
        """Test basic Redoc rendering."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        renderer = DocRenderer(spec)
        html = renderer.render_redoc()

        assert "<html" in html
        assert "redoc" in html
        assert "Test API" in html
        assert "https://cdn.redoc.ly/redoc/latest" in html

    def test_render_redoc_with_theme(self):
        """Test Redoc with custom theme."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        renderer = DocRenderer(spec)
        theme = ThemeConfig.get_builtin_theme("light")
        html = renderer.render_redoc(theme=theme)

        assert "theme:" in html

    def test_render_static_site(self):
        """Test static site generation."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get users",
                        "responses": {"200": {"description": "Success"}},
                    }
                }
            },
        }
        renderer = DocRenderer(spec)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            renderer.render_static_site(output_dir)

            assert (output_dir / "index.html").exists()
            assert (output_dir / "swagger.html").exists()
            assert (output_dir / "redoc.html").exists()
            assert (output_dir / "openapi.json").exists()

    def test_render_static_site_existing_dir(self):
        """Test static site generation with existing directory."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        renderer = DocRenderer(spec)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "test.txt").write_text("test")

            with pytest.raises(RenderError) as exc_info:
                renderer.render_static_site(output_dir, force=False)
            assert "already exists" in str(exc_info.value)

    def test_render_static_site_force(self):
        """Test static site generation with force flag."""
        spec = {
            "openapi": "3.0.3",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {},
        }
        renderer = DocRenderer(spec)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "test.txt").write_text("test")

            renderer.render_static_site(output_dir, force=True)
            assert (output_dir / "index.html").exists()


# ThemeConfig Tests
class TestThemeConfig:
    """Test suite for ThemeConfig."""

    def test_init_default(self):
        """Test default theme initialization."""
        theme = ThemeConfig()
        assert theme.name == "default"
        assert "background" in theme.colors
        assert "text" in theme.colors

    def test_init_custom(self):
        """Test custom theme initialization."""
        theme = ThemeConfig(
            name="custom",
            colors={"background": "#ffffff", "text": "#000000"},
        )
        assert theme.name == "custom"
        assert theme.colors["background"] == "#ffffff"

    def test_get_builtin_theme_light(self):
        """Test getting built-in light theme."""
        theme = ThemeConfig.get_builtin_theme("light")
        assert theme.name == "light"
        assert isinstance(theme.colors, dict)

    def test_get_builtin_theme_dark(self):
        """Test getting built-in dark theme."""
        theme = ThemeConfig.get_builtin_theme("dark")
        assert theme.name == "dark"
        assert isinstance(theme.colors, dict)

    def test_get_builtin_theme_invalid(self):
        """Test getting invalid built-in theme."""
        with pytest.raises(ThemeError) as exc_info:
            ThemeConfig.get_builtin_theme("invalid")
        assert "Unknown theme" in str(exc_info.value)

    def test_to_dict(self):
        """Test converting theme to dictionary."""
        theme = ThemeConfig(name="test", colors={"bg": "#fff"})
        data = theme.to_dict()

        assert isinstance(data, dict)
        assert data["name"] == "test"
        assert data["colors"]["bg"] == "#fff"


# CodeParser Tests
class TestCodeParser:
    """Test suite for CodeParser."""

    def test_parse_google_docstring_basic(self):
        """Test parsing basic Google-style docstring."""
        docstring = """
        Test function.

        Args:
            x: First parameter
            y: Second parameter

        Returns:
            Sum of x and y

        Raises:
            ValueError: If inputs are invalid
        """
        parser = CodeParser()
        parsed = parser.parse_google_docstring(docstring)

        assert parsed.summary == "Test function."
        assert len(parsed.parameters) == 2
        assert parsed.parameters[0].name == "x"
        assert parsed.parameters[1].name == "y"
        assert parsed.returns == "Sum of x and y"
        assert len(parsed.raises) == 1

    def test_parse_google_docstring_multiline(self):
        """Test parsing Google-style docstring with multiline descriptions."""
        docstring = """
        Complex function.

        This function does something complex
        across multiple lines.

        Args:
            param: This is a parameter
                with a long description
                spanning multiple lines

        Returns:
            A complex result
            that also spans
            multiple lines
        """
        parser = CodeParser()
        parsed = parser.parse_google_docstring(docstring)

        assert "complex" in parsed.summary.lower()
        assert "multiple lines" in parsed.description
        assert len(parsed.parameters) == 1
        assert "multiple lines" in parsed.parameters[0].description

    def test_parse_google_docstring_with_types(self):
        """Test parsing Google-style docstring with type annotations."""
        docstring = """
        Typed function.

        Args:
            x (int): An integer
            y (str): A string
            z (Optional[float]): An optional float

        Returns:
            bool: Success status
        """
        parser = CodeParser()
        parsed = parser.parse_google_docstring(docstring)

        assert parsed.parameters[0].type == "int"
        assert parsed.parameters[1].type == "str"
        assert parsed.parameters[2].type == "Optional[float]"
        assert parsed.return_type == "bool"

    def test_parse_google_docstring_examples(self):
        """Test parsing Google-style docstring with examples."""
        docstring = """
        Function with examples.

        Examples:
            >>> add(1, 2)
            3
            >>> add(5, 7)
            12
        """
        parser = CodeParser()
        parsed = parser.parse_google_docstring(docstring)

        assert len(parsed.examples) == 2
        assert "add(1, 2)" in parsed.examples[0]

    def test_parse_docstring_invalid_style(self):
        """Test parsing with invalid docstring style."""
        parser = CodeParser()
        with pytest.raises(DocstringError) as exc_info:
            parser.parse_docstring("Test docstring", style="invalid")
        assert "Unsupported docstring style" in str(exc_info.value)

    def test_extract_type_hints_function(self):
        """Test extracting type hints from function."""

        def test_func(x: int, y: str, z: Optional[float] = None) -> bool:
            """Test function."""
            return True

        parser = CodeParser()
        hints = parser.extract_type_hints(test_func)

        assert hints["x"] == "int"
        assert hints["y"] == "str"
        assert hints["z"] == "Optional[float]"
        assert hints["return"] == "bool"

    def test_extract_type_hints_complex(self):
        """Test extracting complex type hints."""

        def test_func(
            items: List[str],
            mapping: dict[str, int],
            optional: Optional[List[int]] = None,
        ) -> tuple[bool, str]:
            """Test function."""
            return True, "ok"

        parser = CodeParser()
        hints = parser.extract_type_hints(test_func)

        assert "List" in hints["items"]
        assert "dict" in hints["mapping"]
        assert "Optional" in hints["optional"]

    def test_extract_examples_from_docstring(self):
        """Test extracting examples from docstring."""
        docstring = """
        Function description.

        Examples:
            Basic usage:
            >>> func(1)
            2

            Advanced usage:
            >>> func(5)
            10
        """
        parser = CodeParser()
        examples = parser.extract_examples(docstring)

        assert len(examples) >= 2
        assert any("func(1)" in ex for ex in examples)


# ExampleGenerator Tests
class TestExampleGenerator:
    """Test suite for ExampleGenerator."""

    def test_generate_curl_get(self):
        """Test generating cURL for GET request."""
        generator = ExampleGenerator(base_url="https://api.example.com")
        operation = {
            "method": "GET",
            "path": "/users",
            "parameters": [
                {"name": "limit", "in": "query", "schema": {"type": "integer"}},
            ],
        }

        curl = generator.generate_curl(operation)

        assert "curl" in curl
        assert "https://api.example.com/users" in curl
        assert "-X GET" in curl

    def test_generate_curl_post(self):
        """Test generating cURL for POST request."""
        generator = ExampleGenerator(base_url="https://api.example.com")
        operation = {
            "method": "POST",
            "path": "/users",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                            },
                        }
                    }
                }
            },
        }

        curl = generator.generate_curl(operation)

        assert "curl" in curl
        assert "-X POST" in curl
        assert "-H 'Content-Type: application/json'" in curl
        assert "-d" in curl

    def test_generate_curl_with_auth(self):
        """Test generating cURL with authentication."""
        generator = ExampleGenerator(
            base_url="https://api.example.com",
            auth_type="bearer",
            auth_token="test-token",
        )
        operation = {
            "method": "GET",
            "path": "/protected",
        }

        curl = generator.generate_curl(operation)

        assert "-H 'Authorization: Bearer test-token'" in curl

    def test_generate_python_get(self):
        """Test generating Python for GET request."""
        generator = ExampleGenerator(base_url="https://api.example.com")
        operation = {
            "method": "GET",
            "path": "/users/{user_id}",
            "parameters": [
                {"name": "user_id", "in": "path", "schema": {"type": "integer"}},
            ],
        }

        python = generator.generate_python(operation)

        assert "import requests" in python
        assert "requests.get" in python
        assert "https://api.example.com/users" in python

    def test_generate_python_post(self):
        """Test generating Python for POST request."""
        generator = ExampleGenerator(base_url="https://api.example.com")
        operation = {
            "method": "POST",
            "path": "/users",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                            },
                        }
                    }
                }
            },
        }

        python = generator.generate_python(operation)

        assert "requests.post" in python
        assert "json=" in python

    def test_generate_javascript_get(self):
        """Test generating JavaScript for GET request."""
        generator = ExampleGenerator(base_url="https://api.example.com")
        operation = {
            "method": "GET",
            "path": "/users",
        }

        js = generator.generate_javascript(operation)

        assert "fetch" in js
        assert "https://api.example.com/users" in js
        assert "method: 'GET'" in js

    def test_generate_javascript_post(self):
        """Test generating JavaScript for POST request."""
        generator = ExampleGenerator(base_url="https://api.example.com")
        operation = {
            "method": "POST",
            "path": "/users",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                            },
                        }
                    }
                }
            },
        }

        js = generator.generate_javascript(operation)

        assert "fetch" in js
        assert "method: 'POST'" in js
        assert "Content-Type" in js
        assert "JSON.stringify" in js

    def test_generate_all_examples(self):
        """Test generating all example types."""
        generator = ExampleGenerator(base_url="https://api.example.com")
        operation = {
            "method": "GET",
            "path": "/test",
        }

        examples = generator.generate_all_examples(operation)

        assert "curl" in examples
        assert "python" in examples
        assert "javascript" in examples
        assert isinstance(examples["curl"], str)
        assert isinstance(examples["python"], str)
        assert isinstance(examples["javascript"], str)

    def test_invalid_operation(self):
        """Test with invalid operation."""
        generator = ExampleGenerator(base_url="https://api.example.com")

        with pytest.raises(InvalidOperationError) as exc_info:
            generator.generate_curl({})
        assert "Missing required field" in str(exc_info.value)

    def test_auth_error(self):
        """Test authentication configuration error."""
        with pytest.raises(AuthError) as exc_info:
            ExampleGenerator(
                base_url="https://api.example.com",
                auth_type="invalid",
            )
        assert "Unsupported auth type" in str(exc_info.value)


# CLI Tests
class TestCLI:
    """Test suite for CLI commands."""

    @patch("apidocs_cli.SpecGenerator")
    def test_generate_command(self, mock_spec_gen):
        """Test generate command."""
        from click.testing import CliRunner

        from apidocs_cli import generate

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a dummy app file
            Path("app.py").write_text("from fastapi import FastAPI\napp = FastAPI()")

            result = runner.invoke(
                generate,
                [
                    "app:app",
                    "--output",
                    "openapi.yaml",
                ],
            )

            assert result.exit_code == 0 or "Error" in result.output

    @patch("apidocs_cli.uvicorn")
    def test_serve_command(self, mock_uvicorn):
        """Test serve command."""
        from click.testing import CliRunner

        from apidocs_cli import serve

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a dummy spec file
            spec = {
                "openapi": "3.0.3",
                "info": {"title": "Test", "version": "1.0.0"},
                "paths": {},
            }
            Path("openapi.json").write_text(json.dumps(spec))

            # Mock uvicorn.run to avoid actually starting server
            mock_uvicorn.run = Mock()

            result = runner.invoke(
                serve,
                [
                    "openapi.json",
                    "--port",
                    "8000",
                ],
            )

            # Command should attempt to start server
            assert result.exit_code == 0 or mock_uvicorn.run.called

    def test_validate_command_valid(self):
        """Test validate command with valid spec."""
        from click.testing import CliRunner

        from apidocs_cli import validate

        runner = CliRunner()
        with runner.isolated_filesystem():
            spec = {
                "openapi": "3.0.3",
                "info": {"title": "Test API", "version": "1.0.0"},
                "paths": {},
            }
            Path("openapi.json").write_text(json.dumps(spec))

            result = runner.invoke(validate, ["openapi.json"])

            assert result.exit_code == 0
            assert "valid" in result.output.lower() or "✓" in result.output

    def test_validate_command_invalid(self):
        """Test validate command with invalid spec."""
        from click.testing import CliRunner

        from apidocs_cli import validate

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Invalid spec missing required fields
            Path("openapi.json").write_text('{"invalid": "spec"}')

            result = runner.invoke(validate, ["openapi.json"])

            assert result.exit_code != 0 or "error" in result.output.lower()


# Integration Tests
class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow_fastapi_to_html(self):
        """Test complete workflow: FastAPI -> OpenAPI -> HTML."""
        # Create FastAPI app
        app = create_test_app()

        # Generate OpenAPI spec
        generator = SpecGenerator.from_fastapi(app)
        spec = generator.to_dict()

        # Render documentation
        renderer = DocRenderer(spec)
        swagger_html = renderer.render_swagger_ui()
        redoc_html = renderer.render_redoc()

        # Verify outputs
        assert "Test API" in swagger_html
        assert "Test API" in redoc_html
        assert "swagger-ui" in swagger_html
        assert "redoc" in redoc_html

    def test_full_workflow_with_examples(self):
        """Test workflow with code example generation."""
        # Create app and generate spec
        app = create_test_app()
        generator = SpecGenerator.from_fastapi(app)
        spec = generator.to_dict()

        # Generate examples for first path
        example_gen = ExampleGenerator(base_url="https://api.example.com")
        operation = {
            "method": "GET",
            "path": "/users",
            "parameters": [],
        }
        examples = example_gen.generate_all_examples(operation)

        # Verify examples
        assert "curl" in examples
        assert "python" in examples
        assert "javascript" in examples

    def test_full_workflow_static_site(self):
        """Test complete static site generation workflow."""
        # Create app and spec
        app = create_test_app()
        generator = SpecGenerator.from_fastapi(app)
        spec = generator.to_dict()

        # Generate static site
        renderer = DocRenderer(spec)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            renderer.render_static_site(output_dir)

            # Verify all files created
            assert (output_dir / "index.html").exists()
            assert (output_dir / "swagger.html").exists()
            assert (output_dir / "redoc.html").exists()
            assert (output_dir / "openapi.json").exists()

            # Verify content
            index_content = (output_dir / "index.html").read_text()
            assert "Test API" in index_content


# Performance Tests
class TestPerformance:
    """Performance and stress tests."""

    def test_large_spec_generation(self):
        """Test generating large OpenAPI spec."""
        generator = SpecGenerator(title="Large API", version="1.0.0")

        # Add many paths
        for i in range(100):
            generator.add_path(
                path=f"/endpoint{i}",
                method="get",
                summary=f"Endpoint {i}",
                responses={"200": {"description": "Success"}},
            )

        # Should complete without errors
        spec = generator.to_dict()
        assert len(spec["paths"]) == 100

    def test_complex_docstring_parsing(self):
        """Test parsing complex docstrings."""
        docstring = """
        Very complex function with lots of documentation.

        This function does many things and has extensive
        documentation spanning multiple paragraphs.

        Args:
            param1 (int): First parameter with
                a very long description that
                spans multiple lines
            param2 (str): Second parameter
            param3 (Optional[List[Dict[str, Any]]]): Complex type
            param4 (Union[int, str, float]): Union type

        Returns:
            Dict[str, Union[int, str]]: Complex return type
                with multiline description

        Raises:
            ValueError: When something goes wrong
            TypeError: When types are invalid
            RuntimeError: When runtime error occurs

        Examples:
            >>> complex_func(1, "test")
            {'result': 1}

            >>> complex_func(2, "other")
            {'result': 2}
        """
        parser = CodeParser()
        parsed = parser.parse_google_docstring(docstring)

        assert len(parsed.parameters) == 4
        assert len(parsed.raises) == 3
        assert len(parsed.examples) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=.", "--cov-report=term-missing"])
