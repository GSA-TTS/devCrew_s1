# API Documentation Generator

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Automated documentation platform for generating comprehensive API documentation from source code and OpenAPI specifications.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Generate OpenAPI Specification](#generate-openapi-specification)
  - [Serve Documentation](#serve-documentation)
  - [Validate Specifications](#validate-specifications)
  - [Programmatic Usage](#programmatic-usage)
- [Configuration](#configuration)
- [Documentation Renderers](#documentation-renderers)
- [Code Example Generation](#code-example-generation)
- [Theming](#theming)
- [CI/CD Integration](#cicd-integration)
- [Architecture](#architecture)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features

### OpenAPI Specification Generation
- **FastAPI Auto-Generation**: Automatically extract OpenAPI 3.0/3.1 specs from FastAPI applications
- **Route Introspection**: Discover all API routes, methods, and parameters
- **Pydantic Model Mapping**: Convert Pydantic models to JSON Schema
- **Manual Overrides**: Add custom documentation, examples, and descriptions
- **Multi-Format Output**: Export as JSON or YAML

### Interactive Documentation
- **Swagger UI Integration**: CDN-hosted Swagger UI with zero configuration
- **Redoc Support**: Beautiful, responsive API documentation with Redoc
- **Static Site Generation**: Generate standalone HTML documentation sites
- **Theme Customization**: Light/dark themes with custom color schemes

### Code Example Generation
- **Multi-Language Support**: Generate examples in cURL, Python, and JavaScript
- **Authentication Injection**: Automatic auth header injection (Bearer, API Key, Basic)
- **Parameter Substitution**: Replace path/query parameters with example values
- **Request Body Examples**: Generate sample payloads from schemas

### Docstring Parsing
- **Google-Style Docstrings**: Parse Args, Returns, Raises, Examples sections
- **NumPy/Sphinx Support**: Compatible with multiple docstring formats
- **Type Hint Extraction**: Automatic type annotation extraction
- **Example Extraction**: Pull code examples from docstrings

### CLI Interface
- **Rich Terminal UI**: Beautiful, colorful CLI with progress indicators
- **Multiple Commands**: Generate, serve, and validate specifications
- **Development Server**: Built-in Uvicorn server for local documentation
- **Validation Tools**: Lint and validate OpenAPI specifications

## Installation

### Basic Installation

```bash
pip install -r requirements.txt
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/devCrew_s1.git
cd devCrew_s1/tools/api_docs_generator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov pytest-mock black isort flake8 mypy bandit
```

### System Requirements

- Python 3.10 or higher
- pip 21.0 or higher
- FastAPI 0.104.0 or higher (for FastAPI integration)

## Quick Start

### 1. Generate OpenAPI Specification from FastAPI

```python
# my_api.py
from fastapi import FastAPI, Query
from pydantic import BaseModel

app = FastAPI(
    title="My API",
    description="Example API for documentation",
    version="1.0.0",
)

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users", response_model=list[User])
def get_users(limit: int = Query(10, description="Number of users")):
    """
    Get list of users.

    Args:
        limit: Maximum number of users to return

    Returns:
        List of user objects
    """
    return []
```

### 2. Generate Documentation

```bash
# Generate OpenAPI spec
python -m apidocs_cli generate my_api:app --output openapi.yaml

# Serve documentation locally
python -m apidocs_cli serve openapi.yaml --port 8000

# Visit http://localhost:8000 in your browser
```

### 3. Programmatic Usage

```python
from spec_generator import SpecGenerator
from doc_renderer import DocRenderer

# Generate spec from FastAPI app
from my_api import app
generator = SpecGenerator.from_fastapi(app)

# Save spec
generator.save("openapi.yaml", format="yaml")

# Render Swagger UI
renderer = DocRenderer(generator.to_dict())
html = renderer.render_swagger_ui()

with open("docs.html", "w") as f:
    f.write(html)
```

## Usage

### Generate OpenAPI Specification

#### From FastAPI Application

```bash
# Basic generation
python -m apidocs_cli generate my_api:app --output openapi.yaml

# With specific OpenAPI version
python -m apidocs_cli generate my_api:app --output openapi.json --openapi-version 3.1.0

# With additional metadata
python -m apidocs_cli generate my_api:app \
    --output openapi.yaml \
    --title "My Custom API" \
    --version "2.0.0" \
    --description "Custom API description"
```

#### Programmatic Generation

```python
from spec_generator import SpecGenerator
from fastapi import FastAPI

app = FastAPI(title="My API", version="1.0.0")

# Generate from FastAPI app
generator = SpecGenerator.from_fastapi(app)

# Add custom examples
generator.add_example(
    path="/users",
    method="get",
    example_type="response",
    status_code="200",
    example={
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]
    },
)

# Add manual overrides
generator.add_override(
    path="/users",
    method="get",
    override_data={
        "summary": "Get all users with pagination",
        "description": "Retrieve a paginated list of all users in the system",
    },
)

# Export to multiple formats
generator.save("openapi.yaml", format="yaml")
generator.save("openapi.json", format="json")
```

### Serve Documentation

#### Local Development Server

```bash
# Basic server
python -m apidocs_cli serve openapi.yaml

# Custom port
python -m apidocs_cli serve openapi.yaml --port 3000

# Specific renderer
python -m apidocs_cli serve openapi.yaml --ui swagger  # or --ui redoc

# Auto-reload on file changes
python -m apidocs_cli serve openapi.yaml --reload
```

#### Static Site Generation

```bash
# Generate static HTML site
python -m apidocs_cli generate my_api:app --static-site ./docs

# Outputs:
#   docs/index.html       - Landing page
#   docs/swagger.html     - Swagger UI
#   docs/redoc.html       - Redoc
#   docs/openapi.json     - OpenAPI spec
```

#### Programmatic Rendering

```python
from doc_renderer import DocRenderer
from pathlib import Path
import yaml

# Load existing spec
with open("openapi.yaml") as f:
    spec = yaml.safe_load(f)

renderer = DocRenderer(spec)

# Render Swagger UI
swagger_html = renderer.render_swagger_ui()
Path("swagger.html").write_text(swagger_html)

# Render Redoc
redoc_html = renderer.render_redoc()
Path("redoc.html").write_text(redoc_html)

# Generate complete static site
renderer.render_static_site(
    output_dir=Path("./docs"),
    force=True,  # Overwrite existing files
)
```

### Validate Specifications

#### CLI Validation

```bash
# Validate OpenAPI spec
python -m apidocs_cli validate openapi.yaml

# Strict validation
python -m apidocs_cli validate openapi.yaml --strict

# Output format
python -m apidocs_cli validate openapi.yaml --format json
```

#### Programmatic Validation

```python
from spec_generator import SpecGenerator
import yaml

# Load and validate spec
with open("openapi.yaml") as f:
    spec = yaml.safe_load(f)

# Basic validation
try:
    renderer = DocRenderer(spec)
    print("✓ Specification is valid")
except InvalidSpecError as e:
    print(f"✗ Validation failed: {e}")
```

### Programmatic Usage

#### Advanced Spec Generation

```python
from spec_generator import SpecGenerator

# Create custom spec
generator = SpecGenerator(
    title="Advanced API",
    version="2.0.0",
    description="API with custom configuration",
    openapi_version="3.1.0",
)

# Add custom paths
generator.add_path(
    path="/users/{user_id}",
    method="get",
    summary="Get user by ID",
    description="Retrieve a specific user by their unique identifier",
    parameters=[
        {
            "name": "user_id",
            "in": "path",
            "required": True,
            "schema": {"type": "integer"},
            "description": "Unique user identifier",
        }
    ],
    responses={
        "200": {
            "description": "User found",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/User"}
                }
            },
        },
        "404": {
            "description": "User not found",
        },
    },
    tags=["users"],
)

# Add component schemas
generator.add_schema(
    name="User",
    schema={
        "type": "object",
        "required": ["id", "name", "email"],
        "properties": {
            "id": {"type": "integer", "description": "User ID"},
            "name": {"type": "string", "description": "User name"},
            "email": {"type": "string", "format": "email", "description": "User email"},
            "age": {"type": "integer", "minimum": 0, "maximum": 150},
        },
    },
)

# Add security schemes
generator.add_security_scheme(
    name="bearerAuth",
    scheme={
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT Bearer token authentication",
    },
)

# Export
spec_dict = generator.to_dict()
yaml_str = generator.to_yaml()
json_str = generator.to_json()
```

#### Docstring Parsing

```python
from code_parser import CodeParser

parser = CodeParser()

# Parse Google-style docstring
docstring = """
Get user by ID.

This function retrieves a user from the database
by their unique identifier.

Args:
    user_id (int): The unique identifier of the user
    include_deleted (bool): Whether to include soft-deleted users

Returns:
    User: The user object if found

Raises:
    UserNotFoundError: If no user exists with the given ID
    DatabaseError: If database connection fails

Examples:
    >>> get_user(123)
    User(id=123, name='Alice')

    >>> get_user(999)
    UserNotFoundError: User 999 not found
"""

parsed = parser.parse_docstring(docstring, style="google")

print(f"Summary: {parsed.summary}")
print(f"Parameters: {parsed.parameters}")
print(f"Returns: {parsed.returns}")
print(f"Raises: {parsed.raises}")
print(f"Examples: {parsed.examples}")
```

#### Code Example Generation

```python
from example_generator import ExampleGenerator

# Create generator
generator = ExampleGenerator(
    base_url="https://api.example.com",
    auth_type="bearer",
    auth_token="your-api-token",
)

# Define operation
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

# Generate examples
examples = generator.generate_all_examples(operation)

print("cURL:")
print(examples["curl"])
print("\nPython:")
print(examples["python"])
print("\nJavaScript:")
print(examples["javascript"])
```

## Configuration

### Environment Variables

```bash
# Base URL for API examples
export APIDOCS_BASE_URL="https://api.example.com"

# Authentication
export APIDOCS_AUTH_TYPE="bearer"  # bearer, apikey, basic
export APIDOCS_AUTH_TOKEN="your-token"

# Server configuration
export APIDOCS_HOST="0.0.0.0"
export APIDOCS_PORT="8000"

# Docstring style
export APIDOCS_DOCSTRING_STYLE="google"  # google, numpy, sphinx
```

### Configuration File

Create `apidocs.yaml` in your project root:

```yaml
# API metadata
api:
  title: "My API"
  version: "1.0.0"
  description: "Comprehensive API documentation"

# OpenAPI settings
openapi:
  version: "3.0.3"

# Example generation
examples:
  base_url: "https://api.example.com"
  auth:
    type: "bearer"
    token_env: "API_TOKEN"

# Documentation rendering
docs:
  theme: "dark"
  ui: "swagger"  # swagger or redoc

# Code parsing
parsing:
  docstring_style: "google"
  extract_examples: true
```

Load configuration:

```python
from spec_generator import SpecGenerator
import yaml

# Load config
with open("apidocs.yaml") as f:
    config = yaml.safe_load(f)

# Use config
generator = SpecGenerator(
    title=config["api"]["title"],
    version=config["api"]["version"],
    description=config["api"]["description"],
    openapi_version=config["openapi"]["version"],
)
```

## Documentation Renderers

### Swagger UI

Swagger UI provides interactive API documentation with try-it-out functionality.

```python
from doc_renderer import DocRenderer
from theme_config import ThemeConfig

renderer = DocRenderer(spec)

# Basic Swagger UI
html = renderer.render_swagger_ui()

# With custom theme
theme = ThemeConfig.get_builtin_theme("dark")
html = renderer.render_swagger_ui(theme=theme)

# With custom CDN
html = renderer.render_swagger_ui(
    cdn_url="https://custom-cdn.com/swagger-ui/"
)
```

### Redoc

Redoc provides beautiful, responsive documentation with excellent mobile support.

```python
from doc_renderer import DocRenderer

renderer = DocRenderer(spec)

# Basic Redoc
html = renderer.render_redoc()

# With custom theme
from theme_config import ThemeConfig
theme = ThemeConfig.get_builtin_theme("light")
html = renderer.render_redoc(theme=theme)

# With custom options
html = renderer.render_redoc(
    hide_download_button=False,
    expand_responses="all",
)
```

### Static Site

Generate a complete static documentation site.

```python
from doc_renderer import DocRenderer
from pathlib import Path

renderer = DocRenderer(spec)

# Generate static site
renderer.render_static_site(
    output_dir=Path("./docs"),
    force=True,  # Overwrite existing
)

# Files generated:
# - docs/index.html       (landing page with links)
# - docs/swagger.html     (Swagger UI)
# - docs/redoc.html       (Redoc)
# - docs/openapi.json     (OpenAPI spec)
```

## Code Example Generation

### Supported Languages

- **cURL**: Universal command-line HTTP client
- **Python**: Using `requests` library
- **JavaScript**: Using `fetch` API

### Authentication Types

```python
from example_generator import ExampleGenerator

# Bearer token
generator = ExampleGenerator(
    base_url="https://api.example.com",
    auth_type="bearer",
    auth_token="your-jwt-token",
)

# API key (header)
generator = ExampleGenerator(
    base_url="https://api.example.com",
    auth_type="apikey",
    auth_token="your-api-key",
)

# Basic authentication
generator = ExampleGenerator(
    base_url="https://api.example.com",
    auth_type="basic",
    auth_token="username:password",
)
```

### Custom Templates

```python
from example_generator import ExampleGenerator

generator = ExampleGenerator(base_url="https://api.example.com")

# Override default templates
generator.curl_template = """
curl -X {method} \\
  '{url}' \\
  {headers} \\
  {data}
"""

operation = {"method": "GET", "path": "/users"}
curl = generator.generate_curl(operation)
```

## Theming

### Built-in Themes

```python
from theme_config import ThemeConfig

# Light theme
light = ThemeConfig.get_builtin_theme("light")

# Dark theme
dark = ThemeConfig.get_builtin_theme("dark")
```

### Custom Themes

```python
from theme_config import ThemeConfig

custom_theme = ThemeConfig(
    name="custom",
    colors={
        "background": "#1a1a1a",
        "foreground": "#ffffff",
        "primary": "#00ff00",
        "secondary": "#ffff00",
        "border": "#333333",
        "link": "#00aaff",
        "code_background": "#2a2a2a",
        "code_text": "#e0e0e0",
        "success": "#00ff00",
        "error": "#ff0000",
        "warning": "#ffaa00",
    },
)

# Use with renderer
renderer = DocRenderer(spec)
html = renderer.render_swagger_ui(theme=custom_theme)
```

### Theme Colors

Available color keys:

- `background`: Main background color
- `foreground`: Main text color
- `primary`: Primary accent color
- `secondary`: Secondary accent color
- `border`: Border color
- `link`: Hyperlink color
- `code_background`: Code block background
- `code_text`: Code block text
- `success`: Success message color
- `error`: Error message color
- `warning`: Warning message color

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/docs.yml
name: Generate API Documentation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  docs:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r tools/api_docs_generator/requirements.txt

      - name: Generate documentation
        run: |
          cd tools/api_docs_generator
          python -m apidocs_cli generate ../../my_api:app --output openapi.yaml
          python -m apidocs_cli validate openapi.yaml

      - name: Generate static site
        run: |
          cd tools/api_docs_generator
          python -m apidocs_cli generate ../../my_api:app --static-site ./docs

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        if: github.ref == 'refs/heads/main'
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./tools/api_docs_generator/docs
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - docs
  - deploy

generate-docs:
  stage: docs
  image: python:3.10
  script:
    - pip install -r tools/api_docs_generator/requirements.txt
    - cd tools/api_docs_generator
    - python -m apidocs_cli generate ../../my_api:app --output openapi.yaml
    - python -m apidocs_cli validate openapi.yaml
    - python -m apidocs_cli generate ../../my_api:app --static-site ./docs
  artifacts:
    paths:
      - tools/api_docs_generator/docs

pages:
  stage: deploy
  dependencies:
    - generate-docs
  script:
    - mv tools/api_docs_generator/docs public
  artifacts:
    paths:
      - public
  only:
    - main
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: generate-openapi
        name: Generate OpenAPI spec
        entry: python -m apidocs_cli generate
        args: [my_api:app, --output, openapi.yaml]
        language: python
        pass_filenames: false

      - id: validate-openapi
        name: Validate OpenAPI spec
        entry: python -m apidocs_cli validate
        args: [openapi.yaml]
        language: python
        pass_filenames: false
```

## Architecture

### Module Structure

```
api_docs_generator/
├── __init__.py              # Module exports
├── spec_generator.py        # OpenAPI spec generation (893 lines)
├── doc_renderer.py          # HTML documentation rendering (892 lines)
├── theme_config.py          # Theme configuration (345 lines)
├── code_parser.py           # Docstring parsing (749 lines)
├── example_generator.py     # Code example generation (646 lines)
├── apidocs_cli.py           # CLI interface (950 lines)
├── test_api_docs.py         # Test suite (1,243 lines)
├── requirements.txt         # Dependencies
└── README.md                # This file
```

### Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI App                       │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              SpecGenerator                          │
│  - Route introspection                              │
│  - Pydantic model conversion                        │
│  - OpenAPI 3.0/3.1 generation                       │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│             OpenAPI Specification                   │
│                (JSON/YAML)                          │
└──────┬──────────────────────────────────────┬───────┘
       │                                      │
       ▼                                      ▼
┌──────────────────┐              ┌──────────────────┐
│  DocRenderer     │              │ ExampleGenerator │
│  - Swagger UI    │              │  - cURL          │
│  - Redoc         │              │  - Python        │
│  - Static site   │              │  - JavaScript    │
└──────────────────┘              └──────────────────┘
       │                                      │
       ▼                                      ▼
┌─────────────────────────────────────────────────────┐
│           Interactive Documentation                 │
│        (HTML + JavaScript + Examples)               │
└─────────────────────────────────────────────────────┘
```

### Data Flow

1. **FastAPI App** → `SpecGenerator.from_fastapi()` → **OpenAPI Spec**
2. **OpenAPI Spec** → `DocRenderer.render_swagger_ui()` → **Swagger UI HTML**
3. **OpenAPI Spec** → `DocRenderer.render_redoc()` → **Redoc HTML**
4. **OpenAPI Spec** → `ExampleGenerator.generate_all_examples()` → **Code Examples**
5. **Docstrings** → `CodeParser.parse_google_docstring()` → **Parsed Documentation**

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_api_docs.py -v

# Run specific test
pytest test_api_docs.py::TestSpecGenerator::test_from_fastapi_basic -v
```

### Test Coverage

Current test coverage: **85%+**

Coverage by module:
- `spec_generator.py`: 90%
- `doc_renderer.py`: 88%
- `code_parser.py`: 85%
- `example_generator.py`: 87%
- `apidocs_cli.py`: 82%

### Test Categories

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test complete workflows
3. **Performance Tests**: Test with large specifications
4. **CLI Tests**: Test command-line interface

## Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/devCrew_s1.git
cd devCrew_s1/tools/api_docs_generator

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Code Quality

```bash
# Format code
black .
isort .

# Lint code
flake8
pylint .

# Type checking
mypy . --ignore-missing-imports

# Security scanning
bandit -r .

# Run all checks
pre-commit run --all-files
```

### Testing Guidelines

- Write tests for all new features
- Maintain 85%+ test coverage
- Use descriptive test names
- Include docstrings in test functions
- Test edge cases and error conditions

## Troubleshooting

### Common Issues

#### FastAPI Import Error

```
ImportError: FastAPI is not installed
```

**Solution**: Install FastAPI
```bash
pip install fastapi>=0.104.0
```

#### Validation Errors

```
InvalidSpecError: Missing required field 'openapi'
```

**Solution**: Ensure your OpenAPI spec has all required fields:
```python
spec = {
    "openapi": "3.0.3",
    "info": {
        "title": "API Title",
        "version": "1.0.0",
    },
    "paths": {},
}
```

#### Server Won't Start

```
ServerError: Port 8000 is already in use
```

**Solution**: Use a different port
```bash
python -m apidocs_cli serve openapi.yaml --port 3000
```

### Debug Mode

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: https://github.com/yourusername/devCrew_s1/issues
- **Documentation**: https://github.com/yourusername/devCrew_s1/wiki
- **Email**: support@example.com

## Acknowledgments

- FastAPI team for excellent OpenAPI integration
- Swagger UI and Redoc for interactive documentation
- Python community for amazing tools and libraries

---

**Generated with devCrew_s1 API Documentation Generator v1.0.0**
