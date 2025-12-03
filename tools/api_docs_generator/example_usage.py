"""
Example Usage of DocRenderer

Demonstrates how to use the DocRenderer module to generate API documentation.
"""

import json
import sys
from pathlib import Path

# Add to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from doc_renderer import DocRenderer  # noqa: E402


def create_sample_spec():
    """Create a sample OpenAPI specification."""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Sample API",
            "version": "1.0.0",
            "description": "A sample API for demonstration purposes",
            "contact": {
                "name": "API Support",
                "email": "support@example.com",
            },
        },
        "servers": [
            {
                "url": "https://api.example.com/v1",
                "description": "Production server",
            }
        ],
        "paths": {
            "/users": {
                "get": {
                    "summary": "List all users",
                    "description": "Returns a list of all users",
                    "operationId": "listUsers",
                    "tags": ["users"],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/User"
                                        },
                                    }
                                }
                            },
                        }
                    },
                },
                "post": {
                    "summary": "Create a new user",
                    "description": "Creates a new user",
                    "operationId": "createUser",
                    "tags": ["users"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/UserInput"
                                }
                            }
                        },
                    },
                    "responses": {
                        "201": {
                            "description": "User created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/User"
                                    }
                                }
                            },
                        }
                    },
                },
            },
            "/users/{userId}": {
                "get": {
                    "summary": "Get user by ID",
                    "description": "Returns a single user",
                    "operationId": "getUserById",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "userId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "User ID",
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/User"
                                    }
                                }
                            },
                        },
                        "404": {"description": "User not found"},
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "User ID",
                        },
                        "name": {
                            "type": "string",
                            "description": "User name",
                        },
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "User email",
                        },
                        "created_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "Creation timestamp",
                        },
                    },
                    "required": ["id", "name", "email"],
                },
                "UserInput": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "User name",
                        },
                        "email": {
                            "type": "string",
                            "format": "email",
                            "description": "User email",
                        },
                    },
                    "required": ["name", "email"],
                },
            }
        },
    }


def example_swagger_ui():
    """Generate Swagger UI documentation."""
    print("Generating Swagger UI documentation...")

    renderer = DocRenderer()
    spec = create_sample_spec()

    # Generate light theme
    html = renderer.render_swagger_ui(
        spec, title="Sample API - Swagger UI", theme="light"
    )

    output_file = Path("swagger_light.html")
    output_file.write_text(html)
    print(f"✓ Generated: {output_file.absolute()}")

    # Generate dark theme
    html_dark = renderer.render_swagger_ui(
        spec, title="Sample API - Swagger UI", theme="dark"
    )

    output_file_dark = Path("swagger_dark.html")
    output_file_dark.write_text(html_dark)
    print(f"✓ Generated: {output_file_dark.absolute()}")


def example_redoc():
    """Generate Redoc documentation."""
    print("\nGenerating Redoc documentation...")

    renderer = DocRenderer()
    spec = create_sample_spec()

    # Generate light theme
    html = renderer.render_redoc(
        spec, title="Sample API - Redoc", theme="light"
    )

    output_file = Path("redoc_light.html")
    output_file.write_text(html)
    print(f"✓ Generated: {output_file.absolute()}")

    # Generate dark theme
    html_dark = renderer.render_redoc(
        spec, title="Sample API - Redoc", theme="dark"
    )

    output_file_dark = Path("redoc_dark.html")
    output_file_dark.write_text(html_dark)
    print(f"✓ Generated: {output_file_dark.absolute()}")


def example_static_site():
    """Generate complete static site."""
    print("\nGenerating static site...")

    renderer = DocRenderer()
    spec = create_sample_spec()

    output_dir = Path("static_site")
    renderer.render_static_site(
        spec, str(output_dir), title="Sample API Documentation", theme="light"
    )

    print(f"✓ Generated static site in: {output_dir.absolute()}")
    print(f"  - index.html (landing page)")
    print(f"  - swagger.html (Swagger UI)")
    print(f"  - redoc.html (Redoc)")
    print(f"  - openapi.json (spec)")
    print(f"  - assets/common.css")


def example_custom_theme():
    """Generate documentation with custom CSS."""
    print("\nGenerating documentation with custom theme...")

    renderer = DocRenderer()
    spec = create_sample_spec()

    # Custom CSS to change primary color
    custom_css = """
    /* Custom brand colors */
    .swagger-ui .info .title {
        color: #e91e63 !important;
    }

    .swagger-ui .btn.execute {
        background-color: #e91e63 !important;
        border-color: #e91e63 !important;
    }

    .swagger-ui .opblock-tag {
        color: #e91e63 !important;
    }
    """

    html = renderer.render_swagger_ui(
        spec,
        title="Sample API - Custom Theme",
        theme="light",
        custom_css=custom_css,
    )

    output_file = Path("swagger_custom.html")
    output_file.write_text(html)
    print(f"✓ Generated: {output_file.absolute()}")


if __name__ == "__main__":
    print("DocRenderer Example Usage")
    print("=" * 50)

    example_swagger_ui()
    example_redoc()
    example_static_site()
    example_custom_theme()

    print("\n" + "=" * 50)
    print("✅ All examples generated successfully!")
    print("\nOpen the generated HTML files in your browser to view them.")
