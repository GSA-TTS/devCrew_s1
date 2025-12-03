"""
Documentation Renderer

Renders OpenAPI specifications into interactive documentation using Swagger UI
and Redoc. Supports custom themes, static site generation, and both inline
and external spec loading.

Classes:
    DocRenderer: Main class for rendering documentation

Example:
    >>> from doc_renderer import DocRenderer
    >>> renderer = DocRenderer()
    >>> html = renderer.render_swagger_ui(spec, title="My API")
    >>> with open("index.html", "w") as f:
    ...     f.write(html)
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from theme_config import ThemeConfig
else:
    try:
        from .theme_config import ThemeConfig
    except ImportError:
        from theme_config import ThemeConfig


class DocRenderer:
    """
    Renders OpenAPI specifications into interactive HTML documentation.

    Supports both Swagger UI and Redoc rendering engines with customizable
    themes and layouts. Can generate standalone HTML files or complete
    static sites with multiple pages.

    Attributes:
        SWAGGER_CDN: CDN URL for Swagger UI distribution
        REDOC_CDN: CDN URL for Redoc standalone bundle
        theme_config: Theme configuration manager
    """

    SWAGGER_CDN = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/"
    REDOC_CDN = "https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"

    def __init__(self) -> None:
        """Initialize the DocRenderer with default theme configuration."""
        self.theme_config = ThemeConfig()

    def render_swagger_ui(
        self,
        spec: Dict[str, Any],
        title: str = "API Documentation",
        theme: str = "light",
        custom_css: Optional[str] = None,
    ) -> str:
        """
        Render OpenAPI specification as Swagger UI HTML.

        Generates a complete HTML page with Swagger UI embedded, including
        the OpenAPI spec inline as JSON. Supports light and dark themes
        with optional custom CSS overrides.

        Args:
            spec: OpenAPI specification dictionary
            title: HTML page title
            theme: Theme name ("light" or "dark")
            custom_css: Optional custom CSS to inject

        Returns:
            Complete HTML document as string

        Example:
            >>> renderer = DocRenderer()
            >>> spec = {"openapi": "3.0.0", "info": {...}}
            >>> html = renderer.render_swagger_ui(spec, theme="dark")
            >>> Path("docs.html").write_text(html)
        """
        # Escape spec for safe embedding in JavaScript
        spec_json = json.dumps(spec, indent=2)
        spec_escaped = spec_json.replace("</", "<\\/")

        # Get theme colors
        theme_colors = self.theme_config.get_swagger_theme(theme)

        # Build custom CSS
        css_rules = self._build_swagger_css(theme_colors)
        if custom_css:
            css_rules += f"\n{custom_css}"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{title} - Interactive API Documentation">
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" \
href="{self.SWAGGER_CDN}swagger-ui.css">
    <link rel="icon" type="image/png" \
href="{self.SWAGGER_CDN}favicon-32x32.png" sizes="32x32">
    <link rel="icon" type="image/png" \
href="{self.SWAGGER_CDN}favicon-16x16.png" sizes="16x16">
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}

        *,
        *:before,
        *:after {{
            box-sizing: inherit;
        }}

        body {{
            margin: 0;
            padding: 0;
            background: {theme_colors['background']};
        }}

        #swagger-ui {{
            max-width: 1460px;
            margin: 0 auto;
        }}

        {css_rules}

        .loading {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: sans-serif;
            color: {theme_colors['text']};
        }}

        .error {{
            color: #dc3545;
            padding: 20px;
            margin: 20px;
            border: 1px solid #dc3545;
            border-radius: 4px;
            background: #f8d7da;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui" class="loading">
        Loading documentation...
    </div>

    <script src="{self.SWAGGER_CDN}swagger-ui-bundle.js" \
charset="UTF-8"></script>
    <script src="{self.SWAGGER_CDN}swagger-ui-standalone-preset.js" \
charset="UTF-8"></script>
    <script>
        window.onload = function() {{
            try {{
                // Embedded OpenAPI specification
                const spec = {spec_escaped};

                // Initialize Swagger UI
                const ui = SwaggerUIBundle({{
                    spec: spec,
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout",
                    defaultModelsExpandDepth: 1,
                    defaultModelExpandDepth: 1,
                    docExpansion: "list",
                    filter: true,
                    showExtensions: true,
                    showCommonExtensions: true,
                    tryItOutEnabled: true,
                    persistAuthorization: true,
                    syntaxHighlight: {{
                        activate: true,
                        theme: "{theme}"
                    }}
                }});

                window.ui = ui;
            }} catch (error) {{
                console.error("Error initializing Swagger UI:", error);
                document.getElementById('swagger-ui').innerHTML =
                    '<div class="error">' +
                    '<h2>Error Loading Documentation</h2>' +
                    '<p>' + error.message + '</p>' +
                    '<p>Please check the console for more details.</p>' +
                    '</div>';
            }}
        }};
    </script>
</body>
</html>"""
        return html

    def render_redoc(
        self,
        spec: Dict[str, Any],
        title: str = "API Documentation",
        theme: str = "light",
        custom_css: Optional[str] = None,
    ) -> str:
        """
        Render OpenAPI specification as Redoc HTML.

        Generates a complete HTML page with Redoc embedded, including
        the OpenAPI spec inline as JSON. Supports light and dark themes
        with optional custom CSS overrides.

        Args:
            spec: OpenAPI specification dictionary
            title: HTML page title
            theme: Theme name ("light" or "dark")
            custom_css: Optional custom CSS to inject

        Returns:
            Complete HTML document as string

        Example:
            >>> renderer = DocRenderer()
            >>> spec = {"openapi": "3.0.0", "info": {...}}
            >>> html = renderer.render_redoc(spec, theme="dark")
            >>> Path("docs.html").write_text(html)
        """
        # Escape spec for safe embedding in JavaScript
        spec_json = json.dumps(spec, indent=2)
        spec_escaped = spec_json.replace("</", "<\\/")

        # Get theme colors
        theme_colors = self.theme_config.get_redoc_theme(theme)

        # Build theme options for Redoc
        theme_options = {
            "theme": {
                "colors": {
                    "primary": {
                        "main": theme_colors["primary"],
                    },
                    "success": {
                        "main": theme_colors["success"],
                    },
                    "warning": {
                        "main": theme_colors["warning"],
                    },
                    "error": {
                        "main": theme_colors["error"],
                    },
                    "text": {
                        "primary": theme_colors["text"],
                    },
                },
                "sidebar": {
                    "backgroundColor": theme_colors["sidebar_bg"],
                    "textColor": theme_colors["sidebar_text"],
                },
                "rightPanel": {
                    "backgroundColor": theme_colors["panel_bg"],
                },
            },
            "scrollYOffset": 0,
            "hideDownloadButton": False,
            "disableSearch": False,
            "expandResponses": "200,201",
            "requiredPropsFirst": True,
            "sortPropsAlphabetically": True,
            "showExtensions": True,
            "nativeScrollbars": False,
            "pathInMiddlePanel": False,
        }

        theme_options_json = json.dumps(theme_options, indent=2)

        # Build custom CSS
        css_rules = self._build_redoc_css(theme_colors)
        if custom_css:
            css_rules += f"\n{custom_css}"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{title} - Interactive API Documentation">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                         Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: {theme_colors['background']};
        }}

        {css_rules}

        .loading {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: sans-serif;
            color: {theme_colors['text']};
        }}

        .error {{
            color: #dc3545;
            padding: 20px;
            margin: 20px;
            border: 1px solid #dc3545;
            border-radius: 4px;
            background: #f8d7da;
        }}
    </style>
</head>
<body>
    <div id="redoc" class="loading">Loading documentation...</div>

    <script src="{self.REDOC_CDN}"></script>
    <script>
        (function() {{
            try {{
                // Embedded OpenAPI specification
                const spec = {spec_escaped};

                // Theme options
                const options = {theme_options_json};

                // Initialize Redoc
                Redoc.init(
                    spec,
                    options,
                    document.getElementById('redoc')
                );
            }} catch (error) {{
                console.error("Error initializing Redoc:", error);
                document.getElementById('redoc').innerHTML =
                    '<div class="error">' +
                    '<h2>Error Loading Documentation</h2>' +
                    '<p>' + error.message + '</p>' +
                    '<p>Please check the console for more details.</p>' +
                    '</div>';
            }}
        }})();
    </script>
</body>
</html>"""
        return html

    def render_static_site(
        self,
        spec: Dict[str, Any],
        output_dir: str,
        title: str = "API Documentation",
        theme: str = "light",
    ) -> None:
        """
        Generate a complete static documentation site.

        Creates a multi-page static site with:
        - index.html: Landing page with navigation
        - swagger.html: Swagger UI documentation
        - redoc.html: Redoc documentation
        - openapi.json: OpenAPI specification file

        Args:
            spec: OpenAPI specification dictionary
            output_dir: Output directory path
            title: Documentation title
            theme: Theme name ("light" or "dark")

        Raises:
            OSError: If unable to create output directory or write files

        Example:
            >>> renderer = DocRenderer()
            >>> spec = {"openapi": "3.0.0", "info": {...}}
            >>> renderer.render_static_site(spec, "docs/", theme="dark")
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Write OpenAPI spec as JSON file
        spec_file = output_path / "openapi.json"
        spec_file.write_text(json.dumps(spec, indent=2))

        # Generate Swagger UI page
        swagger_html = self.render_swagger_ui(spec, title, theme)
        (output_path / "swagger.html").write_text(swagger_html)

        # Generate Redoc page
        redoc_html = self.render_redoc(spec, title, theme)
        (output_path / "redoc.html").write_text(redoc_html)

        # Generate index/landing page
        index_html = self._render_index_page(spec, title, theme)
        (output_path / "index.html").write_text(index_html)

        # Generate assets
        self._generate_assets(output_path, theme)

    def _render_index_page(
        self,
        spec: Dict[str, Any],
        title: str,
        theme: str,
    ) -> str:
        """
        Render the index/landing page for the static site.

        Args:
            spec: OpenAPI specification dictionary
            title: Documentation title
            theme: Theme name

        Returns:
            Complete HTML document as string
        """
        info = spec.get("info", {})
        api_title = info.get("title", title)
        description = info.get("description", "")
        version = info.get("version", "1.0.0")

        theme_colors = self.theme_config.get_swagger_theme(theme)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{api_title} - API Documentation">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                         Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: {theme_colors['text']};
            background: {theme_colors['background']};
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        header {{
            text-align: center;
            margin-bottom: 60px;
            padding-bottom: 40px;
            border-bottom: 2px solid {theme_colors['border']};
        }}

        h1 {{
            font-size: 3rem;
            margin-bottom: 10px;
            color: {theme_colors['primary']};
        }}

        .version {{
            display: inline-block;
            padding: 4px 12px;
            background: {theme_colors['primary']};
            color: white;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
            margin-top: 10px;
        }}

        .description {{
            margin-top: 20px;
            font-size: 1.125rem;
            color: {theme_colors['secondary']};
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }}

        .docs-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }}

        .doc-card {{
            padding: 30px;
            border: 1px solid {theme_colors['border']};
            border-radius: 8px;
            background: {theme_colors['card_bg']};
            transition: transform 0.2s, box-shadow 0.2s;
            text-decoration: none;
            color: inherit;
            display: block;
        }}

        .doc-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            border-color: {theme_colors['primary']};
        }}

        .doc-card h2 {{
            color: {theme_colors['primary']};
            font-size: 1.5rem;
            margin-bottom: 15px;
        }}

        .doc-card p {{
            color: {theme_colors['secondary']};
            margin-bottom: 20px;
        }}

        .doc-card .btn {{
            display: inline-block;
            padding: 10px 20px;
            background: {theme_colors['primary']};
            color: white;
            border-radius: 4px;
            text-decoration: none;
            font-weight: 500;
            transition: background 0.2s;
        }}

        .doc-card .btn:hover {{
            background: {theme_colors['primary_dark']};
        }}

        .resources {{
            margin-top: 60px;
            padding: 30px;
            background: {theme_colors['card_bg']};
            border-radius: 8px;
            border: 1px solid {theme_colors['border']};
        }}

        .resources h2 {{
            color: {theme_colors['primary']};
            margin-bottom: 20px;
        }}

        .resources ul {{
            list-style: none;
            padding: 0;
        }}

        .resources li {{
            padding: 10px 0;
            border-bottom: 1px solid {theme_colors['border']};
        }}

        .resources li:last-child {{
            border-bottom: none;
        }}

        .resources a {{
            color: {theme_colors['primary']};
            text-decoration: none;
            font-weight: 500;
        }}

        .resources a:hover {{
            text-decoration: underline;
        }}

        footer {{
            margin-top: 60px;
            padding-top: 40px;
            border-top: 2px solid {theme_colors['border']};
            text-align: center;
            color: {theme_colors['secondary']};
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{api_title}</h1>
            <span class="version">v{version}</span>
            <p class="description">{description}</p>
        </header>

        <div class="docs-grid">
            <a href="swagger.html" class="doc-card">
                <h2>Swagger UI</h2>
                <p>
                    Interactive API documentation with a try-it-out
                    feature. Test endpoints directly from your browser
                    with automatic request formatting and response
                    validation.
                </p>
                <span class="btn">Open Swagger UI &rarr;</span>
            </a>

            <a href="redoc.html" class="doc-card">
                <h2>Redoc</h2>
                <p>
                    Clean, responsive API documentation with a
                    three-panel layout. Perfect for exploring API
                    structure, schemas, and examples with excellent
                    readability.
                </p>
                <span class="btn">Open Redoc &rarr;</span>
            </a>
        </div>

        <div class="resources">
            <h2>Resources</h2>
            <ul>
                <li>
                    <a href="openapi.json" download>
                        Download OpenAPI Specification (JSON)
                    </a>
                </li>
                <li>
                    <a href="openapi.json" target="_blank">
                        View OpenAPI Specification
                    </a>
                </li>
            </ul>
        </div>

        <footer>
            <p>Generated with API Documentation Generator</p>
        </footer>
    </div>
</body>
</html>"""
        return html

    def _build_swagger_css(self, theme_colors: Dict[str, str]) -> str:
        """
        Build custom CSS for Swagger UI theming.

        Args:
            theme_colors: Dictionary of theme color values

        Returns:
            CSS rules as string
        """
        return f"""
        /* Swagger UI Custom Theme */
        .swagger-ui .topbar {{
            background-color: {theme_colors['topbar_bg']};
            border-bottom: 1px solid {theme_colors['border']};
        }}

        .swagger-ui .info .title {{
            color: {theme_colors['primary']};
        }}

        .swagger-ui .scheme-container {{
            background: {theme_colors['card_bg']};
            border-color: {theme_colors['border']};
        }}

        .swagger-ui .opblock-tag {{
            border-bottom: 1px solid {theme_colors['border']};
        }}

        .swagger-ui .opblock-tag:hover {{
            background: {theme_colors['hover_bg']};
        }}

        .swagger-ui .opblock {{
            border-color: {theme_colors['border']};
            background: {theme_colors['card_bg']};
        }}

        .swagger-ui .opblock.opblock-get {{
            border-color: {theme_colors['method_get']};
        }}

        .swagger-ui .opblock.opblock-post {{
            border-color: {theme_colors['method_post']};
        }}

        .swagger-ui .opblock.opblock-put {{
            border-color: {theme_colors['method_put']};
        }}

        .swagger-ui .opblock.opblock-delete {{
            border-color: {theme_colors['method_delete']};
        }}

        .swagger-ui .opblock.opblock-patch {{
            border-color: {theme_colors['method_patch']};
        }}

        .swagger-ui .btn {{
            border-color: {theme_colors['border']};
        }}

        .swagger-ui .btn.execute {{
            background-color: {theme_colors['primary']};
            border-color: {theme_colors['primary']};
        }}

        .swagger-ui .btn.execute:hover {{
            background-color: {theme_colors['primary_dark']};
        }}

        .swagger-ui .response-col_status {{
            color: {theme_colors['success']};
        }}

        .swagger-ui .parameter__name {{
            color: {theme_colors['primary']};
        }}

        .swagger-ui .parameter__type {{
            color: {theme_colors['secondary']};
        }}

        .swagger-ui table {{
            border-color: {theme_colors['border']};
        }}

        .swagger-ui table thead tr {{
            background: {theme_colors['table_header_bg']};
        }}

        .swagger-ui .model-box {{
            background: {theme_colors['card_bg']};
            border-color: {theme_colors['border']};
        }}

        .swagger-ui .model-title {{
            color: {theme_colors['primary']};
        }}

        .swagger-ui .prop-type {{
            color: {theme_colors['secondary']};
        }}
        """

    def _build_redoc_css(self, theme_colors: Dict[str, str]) -> str:
        """
        Build custom CSS for Redoc theming.

        Args:
            theme_colors: Dictionary of theme color values

        Returns:
            CSS rules as string
        """
        return f"""
        /* Redoc Custom Theme */
        redoc {{
            color: {theme_colors['text']};
        }}

        .redoc-wrap {{
            background: {theme_colors['background']};
        }}

        .api-info {{
            background: {theme_colors['card_bg']};
            border-bottom: 1px solid {theme_colors['border']};
        }}

        .menu-content {{
            background: {theme_colors['sidebar_bg']};
            color: {theme_colors['sidebar_text']};
        }}

        .menu-content a {{
            color: {theme_colors['sidebar_text']};
        }}

        .menu-content a:hover {{
            background: {theme_colors['hover_bg']};
        }}

        .http-verb {{
            border-radius: 4px;
            padding: 2px 8px;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
        }}

        .http-verb.get {{
            background: {theme_colors['method_get']};
            color: white;
        }}

        .http-verb.post {{
            background: {theme_colors['method_post']};
            color: white;
        }}

        .http-verb.put {{
            background: {theme_colors['method_put']};
            color: white;
        }}

        .http-verb.delete {{
            background: {theme_colors['method_delete']};
            color: white;
        }}

        .http-verb.patch {{
            background: {theme_colors['method_patch']};
            color: white;
        }}
        """

    def _generate_assets(self, output_path: Path, theme: str) -> None:
        """
        Generate additional assets for the static site.

        Creates a simple CSS file for common styles and a basic favicon.

        Args:
            output_path: Output directory path
            theme: Theme name
        """
        # Create assets directory
        assets_dir = output_path / "assets"
        assets_dir.mkdir(exist_ok=True)

        # Generate common CSS
        theme_colors = self.theme_config.get_swagger_theme(theme)
        common_css = f"""
        /* Common Styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                         Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: {theme_colors['text']};
            background: {theme_colors['background']};
        }}

        a {{
            color: {theme_colors['primary']};
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        code {{
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            background: {theme_colors['code_bg']};
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }}

        pre {{
            background: {theme_colors['code_bg']};
            padding: 16px;
            border-radius: 4px;
            overflow-x: auto;
        }}

        pre code {{
            background: none;
            padding: 0;
        }}
        """

        (assets_dir / "common.css").write_text(common_css.strip())
