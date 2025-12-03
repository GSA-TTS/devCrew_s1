"""
Basic tests for DocRenderer module.

Quick validation tests to ensure the module works correctly.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from doc_renderer import DocRenderer  # noqa: E402


def test_render_swagger_ui():
    """Test basic Swagger UI rendering."""
    renderer = DocRenderer()

    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test API Description",
        },
        "paths": {
            "/test": {
                "get": {
                    "summary": "Test endpoint",
                    "responses": {
                        "200": {
                            "description": "Success",
                        }
                    },
                }
            }
        },
    }

    html = renderer.render_swagger_ui(spec, title="Test API", theme="light")

    # Verify HTML structure
    assert "<!DOCTYPE html>" in html
    assert "<title>Test API</title>" in html
    assert "swagger-ui" in html
    assert "SwaggerUIBundle" in html
    assert spec["info"]["title"] in html

    # Verify spec is embedded
    assert "Test API" in html
    assert "Test endpoint" in html

    print("✓ Swagger UI rendering test passed")


def test_render_redoc():
    """Test basic Redoc rendering."""
    renderer = DocRenderer()

    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
        },
        "paths": {},
    }

    html = renderer.render_redoc(spec, title="Test API", theme="dark")

    # Verify HTML structure
    assert "<!DOCTYPE html>" in html
    assert "<title>Test API</title>" in html
    assert "redoc" in html.lower()
    assert "Redoc.init" in html

    print("✓ Redoc rendering test passed")


def test_render_static_site():
    """Test static site generation."""
    renderer = DocRenderer()

    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Test Description",
        },
        "paths": {},
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        renderer.render_static_site(spec, tmpdir, title="Test API")

        # Verify files exist
        output_path = Path(tmpdir)
        assert (output_path / "index.html").exists()
        assert (output_path / "swagger.html").exists()
        assert (output_path / "redoc.html").exists()
        assert (output_path / "openapi.json").exists()
        assert (output_path / "assets" / "common.css").exists()

        # Verify index.html content
        index_content = (output_path / "index.html").read_text()
        assert "Test API" in index_content
        assert "swagger.html" in index_content
        assert "redoc.html" in index_content

        # Verify spec file
        spec_content = (output_path / "openapi.json").read_text()
        loaded_spec = json.loads(spec_content)
        assert loaded_spec["info"]["title"] == "Test API"

        print("✓ Static site generation test passed")


def test_theme_support():
    """Test theme configuration."""
    renderer = DocRenderer()

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
    }

    # Test light theme
    light_html = renderer.render_swagger_ui(spec, theme="light")
    assert "#ffffff" in light_html or "white" in light_html.lower()

    # Test dark theme
    dark_html = renderer.render_swagger_ui(spec, theme="dark")
    assert "#1a1a1a" in dark_html or "dark" in dark_html.lower()

    print("✓ Theme support test passed")


def test_custom_css():
    """Test custom CSS injection."""
    renderer = DocRenderer()

    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test", "version": "1.0.0"},
        "paths": {},
    }

    custom_css = """
    .custom-class {
        color: red;
    }
    """

    html = renderer.render_swagger_ui(spec, custom_css=custom_css)
    assert "custom-class" in html
    assert "color: red" in html

    print("✓ Custom CSS test passed")


if __name__ == "__main__":
    test_render_swagger_ui()
    test_render_redoc()
    test_render_static_site()
    test_theme_support()
    test_custom_css()
    print("\n✅ All tests passed!")
