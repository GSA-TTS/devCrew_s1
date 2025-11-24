#!/usr/bin/env python3
"""
Demo script for C4 Generator.

Shows how to use the C4Generator to parse DSL and generate diagrams.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from c4_generator import C4Generator, DiagramType


def main():
    """Demonstrate C4 generator functionality."""
    print("=== C4 Architecture Diagram Generator Demo ===\n")

    # Initialize generator
    generator = C4Generator()
    print("✓ C4Generator initialized")

    # DSL file path
    dsl_file = Path(__file__).parent / "example_architecture.dsl"
    print(f"✓ DSL file: {dsl_file}")

    # Validate DSL
    print("\n--- Validating DSL ---")
    dsl_content = dsl_file.read_text()
    is_valid, error = generator.validate_dsl(dsl_content)

    if is_valid:
        print("✓ DSL syntax is valid")
    else:
        print(f"✗ DSL validation error: {error}")
        return 1

    # Parse DSL
    print("\n--- Parsing DSL ---")
    try:
        workspace = generator.parse_dsl(str(dsl_file))
        print(f"✓ Workspace parsed: {workspace.name}")
        print(f"  - Description: {workspace.description}")
        print(f"  - People: {len(workspace.model.people)}")
        print(f"  - Systems: {len(workspace.model.software_systems)}")
        print(f"  - Relationships: {len(workspace.model.relationships)}")
        print(f"  - Views: {len(workspace.views)}")
    except Exception as e:
        print(f"✗ Parse error: {e}")
        return 1

    # Show workspace details
    print("\n--- Workspace Details ---")
    for person in workspace.model.people:
        print(f"Person: {person.name} ({person.id})")

    for system in workspace.model.software_systems:
        print(f"System: {system.name} ({system.id})")
        for container in system.containers:
            print(f"  Container: {container.name} ({container.id})")
            print(f"    Technology: {container.technology}")
            for component in container.components:
                print(f"    Component: {component.name} ({component.id})")

    # Generate PlantUML for each view type
    print("\n--- Generating PlantUML ---")
    for view_type in [
        DiagramType.SYSTEM_CONTEXT,
        DiagramType.CONTAINER,
        DiagramType.COMPONENT,
    ]:
        try:
            plantuml = generator.generate_plantuml(workspace, view_type)
            output_file = (
                Path(__file__).parent / f"{view_type.value.lower()}.puml"
            )
            output_file.write_text(plantuml)
            print(f"✓ Generated {view_type.value}: {output_file}")
            print(f"  Lines: {len(plantuml.splitlines())}")
        except Exception as e:
            print(f"✗ Error generating {view_type.value}: {e}")

    # Apply custom theme
    print("\n--- Applying Custom Theme ---")
    custom_theme = {
        "person": {"fill": "#FF6B6B", "stroke": "#C92A2A", "text": "#FFF"},
        "system": {"fill": "#4ECDC4", "stroke": "#2A9D8F", "text": "#FFF"},
    }
    applied_theme = generator.apply_design_system(workspace, custom_theme)
    print(f"✓ Theme applied with {len(applied_theme)} style definitions")

    # Show rendering capabilities
    print("\n--- Rendering Capabilities ---")
    print("Supported output formats:")
    print("  - SVG (Scalable Vector Graphics)")
    print("  - PNG (via SVG conversion)")
    print("\nTo render diagrams, install required dependencies:")
    print("  pip install cairosvg svgwrite")
    print("\nExample rendering commands:")
    print("  generator.render(workspace, DiagramType.SYSTEM_CONTEXT, 'context.svg')")  # noqa: E501
    print("  generator.render(workspace, DiagramType.CONTAINER, 'container.png')")  # noqa: E501

    print("\n=== Demo Complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
