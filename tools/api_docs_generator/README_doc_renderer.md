# DocRenderer Module

Complete documentation renderer for OpenAPI specifications, supporting Swagger UI and Redoc with customizable themes and static site generation.

## Features

- **Swagger UI Rendering**: Generate interactive API documentation with try-it-out functionality
- **Redoc Rendering**: Create clean, three-panel API documentation
- **Static Site Generation**: Build complete documentation sites with multiple pages
- **Theme Support**: Built-in light and dark themes with custom CSS support
- **CDN-Based**: Uses hosted UI libraries (no local bundling required)
- **Production-Ready**: Complete HTML templates with error handling

## Installation

No additional dependencies required beyond Python standard library.

```bash
# The module uses only standard library imports
import json
from pathlib import Path
from typing import Any, Dict, Optional
```

## Quick Start

### Basic Usage

```python
from doc_renderer import DocRenderer

# Create renderer instance
renderer = DocRenderer()

# Your OpenAPI specification
spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "My API",
        "version": "1.0.0"
    },
    "paths": {}
}

# Generate Swagger UI
html = renderer.render_swagger_ui(spec, title="My API Docs")
with open("docs.html", "w") as f:
    f.write(html)
```

## API Reference

### DocRenderer Class

Main class for rendering OpenAPI documentation.

#### Methods

##### `__init__()`

Initialize the DocRenderer with default theme configuration.

```python
renderer = DocRenderer()
```

##### `render_swagger_ui(spec, title, theme, custom_css)`

Render OpenAPI specification as Swagger UI HTML.

**Parameters:**
- `spec` (Dict[str, Any]): OpenAPI specification dictionary
- `title` (str, optional): HTML page title (default: "API Documentation")
- `theme` (str, optional): Theme name - "light" or "dark" (default: "light")
- `custom_css` (str, optional): Custom CSS to inject (default: None)

**Returns:**
- str: Complete HTML document

**Example:**
```python
html = renderer.render_swagger_ui(
    spec,
    title="My API",
    theme="dark",
    custom_css=".custom { color: red; }"
)
```

##### `render_redoc(spec, title, theme, custom_css)`

Render OpenAPI specification as Redoc HTML.

**Parameters:**
- `spec` (Dict[str, Any]): OpenAPI specification dictionary
- `title` (str, optional): HTML page title (default: "API Documentation")
- `theme` (str, optional): Theme name - "light" or "dark" (default: "light")
- `custom_css` (str, optional): Custom CSS to inject (default: None)

**Returns:**
- str: Complete HTML document

**Example:**
```python
html = renderer.render_redoc(
    spec,
    title="My API",
    theme="light"
)
```

##### `render_static_site(spec, output_dir, title, theme)`

Generate a complete static documentation site.

Creates multiple pages:
- `index.html`: Landing page with navigation
- `swagger.html`: Swagger UI documentation
- `redoc.html`: Redoc documentation
- `openapi.json`: OpenAPI specification file
- `assets/common.css`: Common styles

**Parameters:**
- `spec` (Dict[str, Any]): OpenAPI specification dictionary
- `output_dir` (str): Output directory path
- `title` (str, optional): Documentation title (default: "API Documentation")
- `theme` (str, optional): Theme name - "light" or "dark" (default: "light")

**Example:**
```python
renderer.render_static_site(
    spec,
    "docs/",
    title="My API Docs",
    theme="dark"
)
```

### ThemeConfig Class

Theme configuration manager for documentation renderers.

#### Methods

##### `get_swagger_theme(theme)`

Get Swagger UI theme colors.

**Parameters:**
- `theme` (str): Theme name ("light" or "dark")

**Returns:**
- Dict[str, str]: Dictionary of color values

**Example:**
```python
from theme_config import ThemeConfig

config = ThemeConfig()
colors = config.get_swagger_theme("dark")
print(colors["primary"])  # '#5ca3ff'
```

##### `get_redoc_theme(theme)`

Get Redoc theme colors with Redoc-specific extensions.

**Parameters:**
- `theme` (str): Theme name ("light" or "dark")

**Returns:**
- Dict[str, str]: Dictionary of color values including Redoc-specific keys

##### `add_custom_theme(name, colors)`

Add a custom theme configuration.

**Parameters:**
- `name` (str): Theme name
- `colors` (Dict[str, str]): Color values (must include required keys)

**Required color keys:**
- `background`
- `text`
- `secondary`
- `primary`
- `border`
- `card_bg`

**Example:**
```python
config = ThemeConfig()
custom_colors = {
    "background": "#fafafa",
    "text": "#222222",
    "secondary": "#555555",
    "primary": "#3498db",
    "border": "#dddddd",
    "card_bg": "#ffffff",
}
config.add_custom_theme("custom", custom_colors)
```

##### `list_themes()`

List available theme names.

**Returns:**
- list: List of theme names

## Usage Examples

### Example 1: Generate Swagger UI (Light Theme)

```python
from doc_renderer import DocRenderer

renderer = DocRenderer()

spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "User API",
        "version": "1.0.0",
        "description": "API for managing users"
    },
    "paths": {
        "/users": {
            "get": {
                "summary": "List users",
                "responses": {
                    "200": {"description": "Success"}
                }
            }
        }
    }
}

html = renderer.render_swagger_ui(spec, title="User API")
Path("swagger.html").write_text(html)
```

### Example 2: Generate Redoc (Dark Theme)

```python
from doc_renderer import DocRenderer

renderer = DocRenderer()

# Load spec from file
with open("openapi.json") as f:
    spec = json.load(f)

html = renderer.render_redoc(spec, title="My API", theme="dark")
Path("redoc.html").write_text(html)
```

### Example 3: Generate Complete Static Site

```python
from doc_renderer import DocRenderer

renderer = DocRenderer()

spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "Product API",
        "version": "2.0.0"
    },
    "paths": {}
}

# Creates docs/ with multiple HTML pages
renderer.render_static_site(
    spec,
    "docs/",
    title="Product API Documentation",
    theme="light"
)
```

### Example 4: Custom CSS Styling

```python
from doc_renderer import DocRenderer

renderer = DocRenderer()

custom_css = """
.swagger-ui .topbar {
    background-color: #1976d2;
}

.swagger-ui .info .title {
    color: #1976d2;
}

.swagger-ui .btn.execute {
    background-color: #1976d2;
    border-color: #1976d2;
}
"""

html = renderer.render_swagger_ui(
    spec,
    title="Branded API Docs",
    theme="light",
    custom_css=custom_css
)
```

### Example 5: Custom Theme Configuration

```python
from doc_renderer import DocRenderer

renderer = DocRenderer()

# Add custom theme
renderer.theme_config.add_custom_theme("ocean", {
    "background": "#e8f4f8",
    "text": "#0d3b4e",
    "secondary": "#4a7a8c",
    "primary": "#0077be",
    "primary_dark": "#005a8f",
    "border": "#b8d4e0",
    "card_bg": "#ffffff",
    "hover_bg": "#d6ebf2",
    "topbar_bg": "#0077be",
    "table_header_bg": "#f0f8fb",
    "code_bg": "#f0f8fb",
    "success": "#28a745",
    "warning": "#ffc107",
    "error": "#dc3545",
    "method_get": "#0077be",
    "method_post": "#28a745",
    "method_put": "#ffc107",
    "method_delete": "#dc3545",
    "method_patch": "#17a2b8",
})

# Use custom theme
html = renderer.render_swagger_ui(spec, theme="ocean")
```

## Theme System

### Built-in Themes

#### Light Theme
- Clean white background
- Blue primary color (#4990e2)
- High contrast for readability
- Professional appearance

#### Dark Theme
- Dark gray background (#1a1a1a)
- Blue accent color (#5ca3ff)
- Reduced eye strain
- Modern appearance

### Theme Color Keys

All themes support the following color keys:

**Base Colors:**
- `background`: Main background color
- `text`: Primary text color
- `secondary`: Secondary text color
- `primary`: Primary brand color
- `primary_dark`: Darker primary color (hover states)
- `border`: Border color

**UI Elements:**
- `card_bg`: Card/panel background
- `hover_bg`: Hover state background
- `topbar_bg`: Top bar background
- `table_header_bg`: Table header background
- `code_bg`: Code block background

**Status Colors:**
- `success`: Success state color (green)
- `warning`: Warning state color (yellow)
- `error`: Error state color (red)

**HTTP Method Colors:**
- `method_get`: GET requests (blue)
- `method_post`: POST requests (green)
- `method_put`: PUT requests (orange)
- `method_delete`: DELETE requests (red)
- `method_patch`: PATCH requests (cyan)

## CDN Resources

### Swagger UI
- Version: 5.x (latest)
- CDN: `https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/`
- Files used:
  - `swagger-ui.css`: Styles
  - `swagger-ui-bundle.js`: Core functionality
  - `swagger-ui-standalone-preset.js`: Standalone preset
  - `favicon-*.png`: Favicons

### Redoc
- Version: latest
- CDN: `https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js`
- Single standalone bundle includes all functionality

## Generated HTML Structure

### Swagger UI HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Meta tags, title, CDN CSS -->
    <style>/* Custom theme CSS */</style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="CDN/swagger-ui-bundle.js"></script>
    <script src="CDN/swagger-ui-standalone-preset.js"></script>
    <script>
        // Initialize SwaggerUIBundle with embedded spec
    </script>
</body>
</html>
```

### Redoc HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Meta tags, title -->
    <style>/* Custom theme CSS */</style>
</head>
<body>
    <div id="redoc"></div>
    <script src="CDN/redoc.standalone.js"></script>
    <script>
        // Initialize Redoc with embedded spec
    </script>
</body>
</html>
```

### Static Site Structure

```
output_dir/
├── index.html           # Landing page
├── swagger.html         # Swagger UI page
├── redoc.html          # Redoc page
├── openapi.json        # OpenAPI spec
└── assets/
    └── common.css      # Common styles
```

## Error Handling

All rendering methods include error handling:

```javascript
try {
    // Initialize documentation
} catch (error) {
    // Display user-friendly error message
    console.error("Error:", error);
    document.getElementById('container').innerHTML =
        '<div class="error">' +
        '<h2>Error Loading Documentation</h2>' +
        '<p>' + error.message + '</p>' +
        '</div>';
}
```

## Browser Compatibility

Generated HTML works in all modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

## Security Considerations

1. **Spec Escaping**: OpenAPI specs are properly escaped for safe JavaScript embedding
2. **XSS Prevention**: HTML special characters are escaped
3. **CDN Integrity**: Uses well-known, trusted CDN providers
4. **No External Dependencies**: No npm packages or local dependencies required

## Performance

- **Lightweight**: HTML files are typically 10-50 KB (depending on spec size)
- **Fast Loading**: CDN resources are cached by browsers
- **No Build Step**: Generate documentation instantly
- **Lazy Loading**: UI libraries load asynchronously

## Testing

Run the included test suite:

```bash
python3 test_doc_renderer_basic.py
```

Tests cover:
- Swagger UI rendering
- Redoc rendering
- Static site generation
- Theme support
- Custom CSS injection

## Common Issues and Solutions

### Issue: Spec not displaying

**Solution:** Ensure your OpenAPI spec is valid JSON. Validate at https://editor.swagger.io/

### Issue: Custom CSS not applying

**Solution:** Use `!important` for CSS rules that override default styles

### Issue: CORS errors in browser

**Solution:** Serve HTML files from a web server, not directly from filesystem

### Issue: Dark theme not working

**Solution:** Verify theme parameter is exactly "dark" (lowercase)

## Advanced Usage

### Loading Spec from URL

```python
import requests

# Fetch spec from remote URL
response = requests.get("https://api.example.com/openapi.json")
spec = response.json()

renderer = DocRenderer()
html = renderer.render_swagger_ui(spec)
```

### Batch Processing Multiple Specs

```python
from pathlib import Path
from doc_renderer import DocRenderer

renderer = DocRenderer()

specs_dir = Path("specs/")
output_dir = Path("docs/")

for spec_file in specs_dir.glob("*.json"):
    with open(spec_file) as f:
        spec = json.load(f)

    output_name = spec_file.stem
    renderer.render_static_site(
        spec,
        str(output_dir / output_name),
        title=spec["info"]["title"]
    )
```

### Integration with FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from doc_renderer import DocRenderer

app = FastAPI()

@app.get("/docs/swagger", response_class=HTMLResponse)
def get_swagger_docs():
    spec = app.openapi()
    renderer = DocRenderer()
    return renderer.render_swagger_ui(spec, title="My API")

@app.get("/docs/redoc", response_class=HTMLResponse)
def get_redoc_docs():
    spec = app.openapi()
    renderer = DocRenderer()
    return renderer.render_redoc(spec, title="My API")
```

## License

This module is part of the API Documentation Generator platform.

## Support

For issues and questions, please refer to the main project documentation.
