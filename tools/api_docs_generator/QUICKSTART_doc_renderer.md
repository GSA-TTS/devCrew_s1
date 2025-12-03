# DocRenderer Quick Start Guide

5-minute guide to get started with the DocRenderer module.

## Installation

No installation needed! Uses Python standard library only.

## Basic Usage

### 1. Import and Initialize

```python
from doc_renderer import DocRenderer

renderer = DocRenderer()
```

### 2. Create OpenAPI Spec

```python
spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "My API",
        "version": "1.0.0",
        "description": "My awesome API"
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
```

### 3. Generate Documentation

#### Option A: Swagger UI
```python
html = renderer.render_swagger_ui(spec, title="My API Docs")
with open("docs.html", "w") as f:
    f.write(html)
```

#### Option B: Redoc
```python
html = renderer.render_redoc(spec, title="My API Docs")
with open("docs.html", "w") as f:
    f.write(html)
```

#### Option C: Complete Static Site
```python
renderer.render_static_site(spec, "docs/", title="My API")
# Creates: docs/index.html, docs/swagger.html, docs/redoc.html
```

## Common Tasks

### Use Dark Theme
```python
html = renderer.render_swagger_ui(spec, theme="dark")
```

### Add Custom CSS
```python
custom_css = ".swagger-ui .topbar { background: #ff5722; }"
html = renderer.render_swagger_ui(spec, custom_css=custom_css)
```

### Load Spec from File
```python
import json
with open("openapi.json") as f:
    spec = json.load(f)
html = renderer.render_swagger_ui(spec)
```

## Complete Example

```python
from pathlib import Path
from doc_renderer import DocRenderer

# Initialize
renderer = DocRenderer()

# Your API spec
spec = {
    "openapi": "3.0.0",
    "info": {
        "title": "User API",
        "version": "1.0.0"
    },
    "paths": {
        "/users": {
            "get": {
                "summary": "Get users",
                "responses": {
                    "200": {"description": "Success"}
                }
            },
            "post": {
                "summary": "Create user",
                "responses": {
                    "201": {"description": "Created"}
                }
            }
        }
    }
}

# Generate both light and dark versions
Path("swagger_light.html").write_text(
    renderer.render_swagger_ui(spec, title="User API", theme="light")
)

Path("swagger_dark.html").write_text(
    renderer.render_swagger_ui(spec, title="User API", theme="dark")
)

# Generate complete static site
renderer.render_static_site(spec, "docs/", title="User API Documentation")

print("✅ Documentation generated!")
print("  - swagger_light.html")
print("  - swagger_dark.html")
print("  - docs/ (complete site)")
```

## View Documentation

### Option 1: Open in Browser
```bash
open docs.html
# or
xdg-open docs.html  # Linux
```

### Option 2: Local Server
```bash
python3 -m http.server 8000
# Then visit: http://localhost:8000/docs.html
```

## Testing

Run the test suite to verify everything works:

```bash
cd tools/api_docs_generator
python3 test_doc_renderer_basic.py
```

Expected output:
```
✓ Swagger UI rendering test passed
✓ Redoc rendering test passed
✓ Static site generation test passed
✓ Theme support test passed
✓ Custom CSS test passed

✅ All tests passed!
```

## Examples

Run the example script to see all features:

```bash
cd tools/api_docs_generator
python3 example_usage.py
```

This generates:
- `swagger_light.html` - Swagger UI (light theme)
- `swagger_dark.html` - Swagger UI (dark theme)
- `redoc_light.html` - Redoc (light theme)
- `redoc_dark.html` - Redoc (dark theme)
- `swagger_custom.html` - Custom themed
- `static_site/` - Complete static site

## Next Steps

- Read [README_doc_renderer.md](README_doc_renderer.md) for full documentation
- Check [DOC_RENDERER_SUMMARY.md](DOC_RENDERER_SUMMARY.md) for implementation details
- Explore [example_usage.py](example_usage.py) for advanced patterns

## Troubleshooting

### Import Error
```python
# If you get import errors, add to path:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### Spec Not Showing
Validate your OpenAPI spec at: https://editor.swagger.io/

### Custom CSS Not Working
Add `!important` to CSS rules:
```python
custom_css = ".swagger-ui .topbar { background: red !important; }"
```

## Support

For more help, see:
- Full documentation: [README_doc_renderer.md](README_doc_renderer.md)
- Test examples: [test_doc_renderer_basic.py](test_doc_renderer_basic.py)
- Usage examples: [example_usage.py](example_usage.py)
