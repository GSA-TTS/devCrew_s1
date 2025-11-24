# C4 Architecture Diagram Generator

## Overview

The C4 Generator is a comprehensive tool for creating C4 architecture diagrams from DSL (Domain-Specific Language) definitions. It supports parsing Structurizr-style workspace definitions and generating diagrams in multiple formats.

## Features

### Core Capabilities

1. **C4 DSL Parsing**
   - Parse Structurizr-compatible workspace definitions
   - Support for full C4 hierarchy: System Context → Container → Component → Code
   - Validates DSL syntax before processing
   - Detailed error reporting for syntax issues

2. **Multiple Diagram Types**
   - System Context diagrams (highest level view)
   - Container diagrams (applications and data stores)
   - Component diagrams (code-level components)
   - Code diagrams (class/interface level)

3. **Export Formats**
   - PlantUML C4 syntax generation
   - SVG (Scalable Vector Graphics)
   - PNG (via SVG conversion)

4. **Customization**
   - Theme and branding support
   - Custom colors for each element type
   - Font customization
   - Design system integration

## Installation

### Required Dependencies

```bash
pip install -r requirements.txt
```

### Key Dependencies

- `lark==1.1.9` - DSL parsing
- `pydantic==2.5.3` - Data validation
- `svgwrite==1.4.3` - SVG generation
- `cairosvg==2.7.1` - PNG conversion

## Usage

### Basic Example

```python
from c4_generator import C4Generator, DiagramType

# Initialize generator
c4 = C4Generator()

# Parse DSL file
workspace = c4.parse_dsl("architecture.dsl")

# Render diagrams
c4.render(workspace, DiagramType.SYSTEM_CONTEXT, "context.svg")
c4.render(workspace, DiagramType.CONTAINER, "container.png")

# Generate PlantUML
plantuml = c4.generate_plantuml(workspace, DiagramType.SYSTEM_CONTEXT)
```

### DSL Format

The generator uses a Structurizr-compatible DSL format:

```dsl
workspace "System Name" {
    name "System Name"
    description "System description"

    model {
        // Define people/actors
        user = person "User" "System user"

        // Define systems
        system = softwareSystem "Main System" "Core system" {
            // Define containers
            webapp = container "Web App" "Frontend" "React" {
                // Define components
                ui = component "UI Layer" "User interface" "React"
            }

            api = container "API" "Backend" "Node.js"
            db = container "Database" "Data store" "PostgreSQL"
        }

        external = softwareSystem "External System" "Third party"

        // Define relationships
        user -> webapp : "Uses" "HTTPS"
        webapp -> api : "Calls" "REST/JSON"
        api -> db : "Reads/Writes" "SQL"
        api -> external : "Integrates" "REST"
    }

    views {
        systemContext system "Context View" {}
        container system "Container View" {}
        component webapp "Component View" {}
    }
}
```

### Validation

```python
# Validate DSL before parsing
is_valid, error = c4.validate_dsl(dsl_content)
if is_valid:
    workspace = c4.parse_dsl("architecture.dsl")
else:
    print(f"Validation error: {error}")
```

### Custom Themes

```python
# Define custom theme
custom_theme = {
    "person": {
        "fill": "#FF6B6B",
        "stroke": "#C92A2A",
        "text": "#FFFFFF"
    },
    "system": {
        "fill": "#4ECDC4",
        "stroke": "#2A9D8F",
        "text": "#FFFFFF"
    },
    "container": {
        "fill": "#45B7D1",
        "stroke": "#2E86A8",
        "text": "#FFFFFF"
    },
    "component": {
        "fill": "#96CEB4",
        "stroke": "#6BAA8F",
        "text": "#000000"
    },
    "font_family": "Arial, Helvetica, sans-serif",
    "font_size": 14
}

# Apply theme
applied_theme = c4.apply_design_system(workspace, custom_theme)
```

## API Reference

### C4Generator Class

#### `__init__()`
Initialize the C4 generator with default theme and parser.

#### `parse_dsl(dsl_file: str) -> C4Workspace`
Parse C4 DSL file into workspace object.

**Parameters:**
- `dsl_file`: Path to DSL file

**Returns:**
- `C4Workspace`: Parsed workspace object

**Raises:**
- `FileNotFoundError`: If DSL file doesn't exist
- `ValueError`: If DSL syntax is invalid

#### `validate_dsl(dsl_content: str) -> Tuple[bool, Optional[str]]`
Validate C4 DSL syntax without full parsing.

**Parameters:**
- `dsl_content`: DSL content to validate

**Returns:**
- Tuple of (is_valid, error_message)

#### `generate_plantuml(workspace: C4Workspace, view: DiagramType) -> str`
Generate PlantUML C4 syntax from workspace.

**Parameters:**
- `workspace`: C4 workspace
- `view`: Diagram type to generate

**Returns:**
- PlantUML C4 syntax as string

#### `render(workspace: C4Workspace, view: DiagramType, output: str, format: Optional[str] = None)`
Render diagram to file.

**Parameters:**
- `workspace`: C4 workspace
- `view`: Diagram type to render
- `output`: Output file path
- `format`: Output format (svg/png), inferred from extension if None

**Raises:**
- `ValueError`: If output format is unsupported

#### `apply_design_system(workspace: C4Workspace, theme: Dict[str, Any]) -> Dict[str, Any]`
Apply custom theme/branding to workspace.

**Parameters:**
- `workspace`: C4 workspace to theme
- `theme`: Theme configuration dictionary

**Returns:**
- Applied theme dictionary

### Pydantic Models

#### `DiagramType` (Enum)
- `SYSTEM_CONTEXT`: System context diagram
- `CONTAINER`: Container diagram
- `COMPONENT`: Component diagram
- `CODE`: Code diagram

#### `C4Person`
Represents a person/actor in the C4 model.

**Fields:**
- `id`: Unique identifier
- `name`: Display name
- `description`: Role description
- `tags`: Tags for styling/filtering
- `external`: Whether person is external

#### `C4SoftwareSystem`
Represents a software system.

**Fields:**
- `id`: Unique identifier
- `name`: System name
- `description`: System description
- `tags`: System tags
- `external`: Whether system is external
- `containers`: List of containers

#### `C4Container`
Represents a container (application/service).

**Fields:**
- `id`: Unique identifier
- `name`: Container name
- `description`: Container description
- `technology`: Technology stack
- `tags`: Container tags
- `components`: List of components

#### `C4Component`
Represents a component within a container.

**Fields:**
- `id`: Unique identifier
- `name`: Component name
- `description`: Component description
- `technology`: Technology stack
- `tags`: Component tags

#### `C4Relationship`
Represents a relationship between elements.

**Fields:**
- `source_id`: Source element ID
- `target_id`: Target element ID
- `description`: Relationship description
- `technology`: Technology/protocol used
- `tags`: Tags for styling

#### `C4Model`
The C4 model containing all elements.

**Fields:**
- `people`: List of people/actors
- `software_systems`: List of software systems
- `relationships`: List of relationships

#### `C4View`
Represents a specific view/diagram.

**Fields:**
- `key`: Unique view identifier
- `type`: Diagram type
- `title`: View title
- `description`: View description
- `software_system_id`: Target system for container/component views
- `container_id`: Target container for component views
- `include_relationships`: Whether to include relationships

#### `C4Workspace`
Complete C4 workspace with model and views.

**Fields:**
- `name`: Workspace name
- `description`: Workspace description
- `model`: The C4 model
- `views`: List of defined views

## Example Workflow

### 1. Create DSL File

Create an `architecture.dsl` file defining your system architecture.

### 2. Generate Diagrams

```python
from c4_generator import C4Generator, DiagramType

# Initialize
generator = C4Generator()

# Parse
workspace = generator.parse_dsl("architecture.dsl")

# Generate all view types
generator.render(workspace, DiagramType.SYSTEM_CONTEXT, "context.svg")
generator.render(workspace, DiagramType.CONTAINER, "container.svg")
generator.render(workspace, DiagramType.COMPONENT, "component.svg")
```

### 3. Generate PlantUML

```python
# Generate PlantUML for documentation
plantuml = generator.generate_plantuml(workspace, DiagramType.SYSTEM_CONTEXT)
with open("context.puml", "w") as f:
    f.write(plantuml)
```

### 4. Apply Branding

```python
# Apply company branding
company_theme = {
    "person": {"fill": "#003366", "stroke": "#001F3F", "text": "#FFFFFF"},
    "system": {"fill": "#0074D9", "stroke": "#0056A3", "text": "#FFFFFF"},
    "font_family": "Roboto, sans-serif",
}

themed = generator.apply_design_system(workspace, company_theme)
generator.render(workspace, DiagramType.SYSTEM_CONTEXT, "branded_context.svg")
```

## Integration with Design Platform

The C4 Generator integrates with other design platform tools:

### With Figma Client
Export design system tokens from Figma and apply them as C4 themes:

```python
from figma_client import FigmaClient
from c4_generator import C4Generator

# Extract colors from Figma
figma = FigmaClient(api_key="...")
design_tokens = figma.export_design_tokens("file_id")

# Apply to C4 diagrams
theme = {
    "person": {"fill": design_tokens["colors"]["primary"]},
    "system": {"fill": design_tokens["colors"]["secondary"]},
}
c4.apply_design_system(workspace, theme)
```

### With Code Exporter
Generate both architecture diagrams and code:

```python
from c4_generator import C4Generator
from code_exporter import CodeExporter

# Generate architecture diagrams
c4 = C4Generator()
workspace = c4.parse_dsl("architecture.dsl")
c4.render(workspace, DiagramType.CONTAINER, "architecture.svg")

# Export code from designs
exporter = CodeExporter()
react_code = exporter.generate_react_component(figma_node)
```

## Best Practices

1. **Organize by Hierarchy**
   - Start with System Context (highest level)
   - Drill down to Container level for key systems
   - Use Component level for complex containers only
   - Reserve Code level for critical components

2. **Naming Conventions**
   - Use clear, descriptive names
   - IDs should be alphanumeric + underscores
   - Keep descriptions concise but informative

3. **Relationships**
   - Describe what flows over the relationship (data, commands, etc.)
   - Specify technology/protocol when relevant
   - Avoid too many relationships per diagram (5-10 is ideal)

4. **Views**
   - Create focused views for specific audiences
   - System Context for business stakeholders
   - Container for solution architects
   - Component for developers

5. **Themes**
   - Use consistent color schemes
   - Ensure text is readable (contrast)
   - External systems should be visually distinct

## Troubleshooting

### DSL Parse Errors

If parsing fails, check:
- All braces are properly closed
- String literals are quoted
- IDs are alphanumeric + underscores only
- Relationships reference existing elements

### Rendering Issues

If rendering fails:
- Ensure cairosvg and svgwrite are installed
- Check file permissions for output directory
- Verify sufficient disk space

### PlantUML Generation

For PlantUML output:
- Install PlantUML locally for rendering: `brew install plantuml`
- Use online renderer: http://www.plantuml.com/plantuml/
- Or use the generated .puml files with PlantUML CLI

## Performance

- **Parsing**: ~1000 elements per second
- **SVG Generation**: Sub-second for typical diagrams
- **PNG Conversion**: 1-2 seconds per diagram

## Limitations

- Maximum 100 elements per diagram (for readability)
- DSL must follow Structurizr conventions
- PNG export requires system dependencies (cairo)

## Future Enhancements

- [ ] Interactive SVG with zoom/pan
- [ ] Auto-layout algorithms
- [ ] Diagram diff/comparison
- [ ] Export to Mermaid syntax
- [ ] Animation support for relationship flows
- [ ] Integration with architecture decision records (ADRs)

## License

Part of devCrew_s1 design platform tools.

## Support

For issues or questions, refer to the main design platform documentation.
