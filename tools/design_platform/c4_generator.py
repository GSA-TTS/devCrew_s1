"""
C4 Architecture Diagram Generator.

Provides comprehensive C4 model diagram generation supporting:
- C4 DSL parsing (Structurizr workspace format)
- Multiple diagram types (System Context, Container, Component, Code)
- PlantUML C4 syntax generation
- SVG and PNG export capabilities
- Theme and branding customization
- DSL validation and error reporting

The generator supports the full C4 model hierarchy:
    System Context -> Container -> Component -> Code

Usage:
    >>> c4 = C4Generator()
    >>> workspace = c4.parse_dsl("architecture.dsl")
    >>> c4.render(workspace, DiagramType.SYSTEM_CONTEXT, "context.svg")
    >>> c4.render(workspace, DiagramType.CONTAINER, "container.png")
"""

import re
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cairosvg
import svgwrite
from lark import Lark, Token, Transformer
from pydantic import BaseModel, Field, field_validator


class DiagramType(str, Enum):
    """C4 diagram types following the C4 model hierarchy."""

    SYSTEM_CONTEXT = "SystemContext"
    CONTAINER = "Container"
    COMPONENT = "Component"
    CODE = "Code"


class C4Person(BaseModel):
    """Represents a person/actor in the C4 model."""

    id: str = Field(..., description="Unique identifier for the person")
    name: str = Field(..., description="Display name of the person")
    description: str = Field(default="", description="Description of the person's role")
    tags: List[str] = Field(
        default_factory=list, description="Tags for styling/filtering"
    )
    external: bool = Field(
        default=False, description="Whether person is external to system"
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate that ID contains only alphanumeric and underscores."""
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(f"Invalid ID '{v}': must start with letter/underscore")
        return v


class C4Relationship(BaseModel):
    """Represents a relationship between C4 elements."""

    source_id: str = Field(..., description="Source element ID")
    target_id: str = Field(..., description="Target element ID")
    description: str = Field(..., description="Relationship description")
    technology: Optional[str] = Field(
        default=None, description="Technology/protocol used"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for styling")


class C4Component(BaseModel):
    """Represents a component within a container."""

    id: str = Field(..., description="Unique component identifier")
    name: str = Field(..., description="Component name")
    description: str = Field(default="", description="Component description")
    technology: Optional[str] = Field(default=None, description="Technology stack")
    tags: List[str] = Field(default_factory=list, description="Component tags")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate component ID format."""
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(f"Invalid component ID '{v}': use alphanumeric/underscore")
        return v


class C4Container(BaseModel):
    """Represents a container (application/service) in the C4 model."""

    id: str = Field(..., description="Unique container identifier")
    name: str = Field(..., description="Container name")
    description: str = Field(default="", description="Container description")
    technology: Optional[str] = Field(default=None, description="Technology stack")
    tags: List[str] = Field(default_factory=list, description="Container tags")
    components: List[C4Component] = Field(
        default_factory=list, description="Components within container"
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate container ID format."""
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(f"Invalid container ID '{v}': use alphanumeric/underscore")
        return v


class C4SoftwareSystem(BaseModel):
    """Represents a software system in the C4 model."""

    id: str = Field(..., description="Unique system identifier")
    name: str = Field(..., description="System name")
    description: str = Field(default="", description="System description")
    tags: List[str] = Field(default_factory=list, description="System tags")
    external: bool = Field(default=False, description="Whether system is external")
    containers: List[C4Container] = Field(
        default_factory=list, description="Containers in system"
    )

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate system ID format."""
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", v):
            raise ValueError(f"Invalid system ID '{v}': use alphanumeric/underscore")
        return v


class C4Model(BaseModel):
    """The C4 model containing all elements and relationships."""

    people: List[C4Person] = Field(
        default_factory=list, description="People/actors in the system"
    )
    software_systems: List[C4SoftwareSystem] = Field(
        default_factory=list, description="Software systems"
    )
    relationships: List[C4Relationship] = Field(
        default_factory=list, description="Relationships between elements"
    )

    def get_element_by_id(self, element_id: str) -> Optional[Any]:
        """Find element by ID across all collections."""
        # Check people
        for person in self.people:
            if person.id == element_id:
                return person

        # Check systems
        for system in self.software_systems:
            if system.id == element_id:
                return system

            # Check containers
            for container in system.containers:
                if container.id == element_id:
                    return container

                # Check components
                for component in container.components:
                    if component.id == element_id:
                        return component

        return None


class C4View(BaseModel):
    """Represents a specific view/diagram in the workspace."""

    key: str = Field(..., description="Unique view identifier")
    type: DiagramType = Field(..., description="Type of C4 diagram")
    title: str = Field(..., description="View title")
    description: str = Field(default="", description="View description")
    software_system_id: Optional[str] = Field(
        default=None, description="Target system for container/component views"
    )
    container_id: Optional[str] = Field(
        default=None, description="Target container for component views"
    )
    include_relationships: bool = Field(
        default=True, description="Whether to include relationships"
    )


class C4Diagram(BaseModel):
    """Processed diagram ready for rendering."""

    type: DiagramType = Field(..., description="Diagram type")
    title: str = Field(..., description="Diagram title")
    elements: List[Dict[str, Any]] = Field(
        default_factory=list, description="Elements to render"
    )
    relationships: List[C4Relationship] = Field(
        default_factory=list, description="Relationships to render"
    )
    layout: Dict[str, Any] = Field(
        default_factory=dict, description="Layout configuration"
    )


class C4Workspace(BaseModel):
    """Complete C4 workspace with model and views."""

    name: str = Field(..., description="Workspace name")
    description: str = Field(default="", description="Workspace description")
    model: C4Model = Field(..., description="The C4 model")
    views: List[C4View] = Field(default_factory=list, description="Defined views")


class C4DSLTransformer(Transformer):
    """Lark transformer to convert parse tree to C4 workspace objects."""

    def __init__(self) -> None:
        """Initialize the transformer."""
        super().__init__()
        self._workspace_name = ""
        self._workspace_desc = ""
        self.people: List[C4Person] = []
        self.systems: List[C4SoftwareSystem] = []
        self.relationships: List[C4Relationship] = []
        self.views: List[C4View] = []
        self.current_system: Optional[C4SoftwareSystem] = None
        self.current_container: Optional[C4Container] = None

    def workspace(self, items: List[Any]) -> C4Workspace:
        """Process workspace definition."""
        for item in items:
            if isinstance(item, dict) and "workspace_name" in item:
                self._workspace_name = item["workspace_name"]
            elif isinstance(item, dict) and "workspace_desc" in item:
                self._workspace_desc = item["workspace_desc"]

        model = C4Model(
            people=self.people,
            software_systems=self.systems,
            relationships=self.relationships,
        )

        return C4Workspace(
            name=self._workspace_name,
            description=self._workspace_desc,
            model=model,
            views=self.views,
        )

    def workspace_name(self, items: List[Token]) -> Dict[str, str]:
        """Extract workspace name."""
        return {"workspace_name": str(items[0]).strip('"')}

    def workspace_description(self, items: List[Token]) -> Dict[str, str]:
        """Extract workspace description."""
        return {"workspace_desc": str(items[0]).strip('"')}

    def person(self, items: List[Any]) -> None:
        """Process person definition."""
        person_id = str(items[0])
        name = str(items[1]).strip('"')
        desc = str(items[2]).strip('"') if len(items) > 2 else ""

        self.people.append(C4Person(id=person_id, name=name, description=desc))

    def software_system(self, items: List[Any]) -> None:
        """Process software system definition."""
        system_id = str(items[0])
        name = str(items[1]).strip('"')
        desc = str(items[2]).strip('"') if len(items) > 2 else ""

        self.current_system = C4SoftwareSystem(
            id=system_id, name=name, description=desc
        )
        self.systems.append(self.current_system)

    def container(self, items: List[Any]) -> None:
        """Process container definition."""
        if not self.current_system:
            return

        container_id = str(items[0])
        name = str(items[1]).strip('"')
        desc = str(items[2]).strip('"') if len(items) > 2 else ""
        tech = str(items[3]).strip('"') if len(items) > 3 else None

        self.current_container = C4Container(
            id=container_id, name=name, description=desc, technology=tech
        )
        self.current_system.containers.append(self.current_container)

    def component(self, items: List[Any]) -> None:
        """Process component definition."""
        if not self.current_container:
            return

        component_id = str(items[0])
        name = str(items[1]).strip('"')
        desc = str(items[2]).strip('"') if len(items) > 2 else ""
        tech = str(items[3]).strip('"') if len(items) > 3 else None

        self.current_container.components.append(
            C4Component(id=component_id, name=name, description=desc, technology=tech)
        )

    def relationship(self, items: List[Any]) -> None:
        """Process relationship definition."""
        source = str(items[0])
        target = str(items[1])
        desc = str(items[2]).strip('"')
        tech = str(items[3]).strip('"') if len(items) > 3 else None

        self.relationships.append(
            C4Relationship(
                source_id=source,
                target_id=target,
                description=desc,
                technology=tech,
            )
        )

    def system_context_view(self, items: List[Any]) -> None:
        """Process system context view definition."""
        key = str(items[0])
        system_id = str(items[1]) if len(items) > 1 else None
        title = str(items[2]).strip('"') if len(items) > 2 else key

        self.views.append(
            C4View(
                key=key,
                type=DiagramType.SYSTEM_CONTEXT,
                title=title,
                software_system_id=system_id,
            )
        )

    def container_view(self, items: List[Any]) -> None:
        """Process container view definition."""
        key = str(items[0])
        system_id = str(items[1]) if len(items) > 1 else None
        title = str(items[2]).strip('"') if len(items) > 2 else key

        self.views.append(
            C4View(
                key=key,
                type=DiagramType.CONTAINER,
                title=title,
                software_system_id=system_id,
            )
        )

    def component_view(self, items: List[Any]) -> None:
        """Process component view definition."""
        key = str(items[0])
        container_id = str(items[1]) if len(items) > 1 else None
        title = str(items[2]).strip('"') if len(items) > 2 else key

        self.views.append(
            C4View(
                key=key,
                type=DiagramType.COMPONENT,
                title=title,
                container_id=container_id,
            )
        )


class C4Generator:
    """
    C4 Architecture Diagram Generator.

    Generates C4 model diagrams from DSL definitions, supporting multiple
    output formats and customization options.

    Example:
        >>> generator = C4Generator()
        >>> workspace = generator.parse_dsl("architecture.dsl")
        >>> generator.render(workspace, DiagramType.SYSTEM_CONTEXT, "out.svg")
    """

    # C4 DSL Grammar
    C4_GRAMMAR = r"""
        start: workspace

        workspace: "workspace" STRING "{" workspace_body "}"

        workspace_body: (workspace_item)*

        workspace_item: workspace_name
                     | workspace_description
                     | model_block
                     | views_block

        workspace_name: "name" STRING
        workspace_description: "description" STRING

        model_block: "model" "{" (model_item)* "}"

        model_item: person
                 | software_system
                 | relationship

        person: IDENTIFIER "=" "person" STRING STRING?

        software_system: IDENTIFIER "=" "softwareSystem" STRING STRING? "{"
                        (system_item)* "}"

        system_item: container | relationship

        container: IDENTIFIER "=" "container" STRING STRING? STRING? "{"
                  (container_item)* "}"

        container_item: component | relationship

        component: IDENTIFIER "=" "component" STRING STRING? STRING?

        relationship: IDENTIFIER "->" IDENTIFIER ":" STRING STRING?

        views_block: "views" "{" (view_item)* "}"

        view_item: system_context_view
                | container_view
                | component_view

        system_context_view: "systemContext" IDENTIFIER STRING? "{" "}"

        container_view: "container" IDENTIFIER STRING? "{" "}"

        component_view: "component" IDENTIFIER STRING? "{" "}"

        STRING: /"[^"]*"/
        IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/

        %import common.WS
        %ignore WS
        %ignore /\/\/.*/
        %ignore /\/\*(.|\n)*?\*\//
    """

    def __init__(self) -> None:
        """Initialize the C4 generator with parser and default theme."""
        self.parser = Lark(
            self.C4_GRAMMAR, parser="lalr", transformer=C4DSLTransformer()
        )

        self.default_theme = {
            "person": {"fill": "#08427B", "stroke": "#073B6F", "text": "#FFF"},
            "system": {"fill": "#1168BD", "stroke": "#0B4884", "text": "#FFF"},
            "external_system": {
                "fill": "#999999",
                "stroke": "#6B6B6B",
                "text": "#FFF",
            },
            "container": {
                "fill": "#438DD5",
                "stroke": "#2E6295",
                "text": "#FFF",
            },
            "component": {
                "fill": "#85BBF0",
                "stroke": "#5D82A8",
                "text": "#000",
            },
            "relationship": {"stroke": "#707070", "text": "#707070"},
            "font_family": "Arial, Helvetica, sans-serif",
            "font_size": 14,
        }

    def validate_dsl(self, dsl_content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate C4 DSL syntax without full parsing.

        Args:
            dsl_content: DSL content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            self.parser.parse(dsl_content)
            return True, None
        except Exception as e:
            return False, str(e)

    def parse_dsl(self, dsl_file: str) -> C4Workspace:
        """
        Parse C4 DSL file into workspace object.

        Args:
            dsl_file: Path to DSL file

        Returns:
            Parsed C4Workspace object

        Raises:
            FileNotFoundError: If DSL file doesn't exist
            ValueError: If DSL syntax is invalid
        """
        dsl_path = Path(dsl_file)

        if not dsl_path.exists():
            raise FileNotFoundError(f"DSL file not found: {dsl_file}")

        dsl_content = dsl_path.read_text(encoding="utf-8")

        is_valid, error = self.validate_dsl(dsl_content)
        if not is_valid:
            raise ValueError(f"Invalid DSL syntax: {error}")

        try:
            workspace = self.parser.parse(dsl_content)
            return workspace
        except Exception as e:
            raise ValueError(f"Failed to parse DSL: {e}") from e

    def _build_diagram(self, workspace: C4Workspace, view: C4View) -> C4Diagram:
        """
        Build diagram data structure from workspace and view.

        Args:
            workspace: C4 workspace
            view: View definition

        Returns:
            C4Diagram ready for rendering
        """
        elements: List[Dict[str, Any]] = []
        relationships: List[C4Relationship] = []

        if view.type == DiagramType.SYSTEM_CONTEXT:
            # Include people and systems
            for person in workspace.model.people:
                elements.append(
                    {
                        "type": "person",
                        "id": person.id,
                        "name": person.name,
                        "description": person.description,
                    }
                )

            for system in workspace.model.software_systems:
                elements.append(
                    {
                        "type": "system",
                        "id": system.id,
                        "name": system.name,
                        "description": system.description,
                        "external": system.external,
                    }
                )

            relationships = workspace.model.relationships

        elif view.type == DiagramType.CONTAINER:
            # Find target system
            target_system = None
            for system in workspace.model.software_systems:
                if system.id == view.software_system_id:
                    target_system = system
                    break

            if target_system:
                # Include containers
                for container in target_system.containers:
                    elements.append(
                        {
                            "type": "container",
                            "id": container.id,
                            "name": container.name,
                            "description": container.description,
                            "technology": container.technology,
                        }
                    )

                # Include relevant people and external systems
                for person in workspace.model.people:
                    elements.append(
                        {
                            "type": "person",
                            "id": person.id,
                            "name": person.name,
                            "description": person.description,
                        }
                    )

                relationships = workspace.model.relationships

        elif view.type == DiagramType.COMPONENT:
            # Find target container
            target_container = None
            for system in workspace.model.software_systems:
                for container in system.containers:
                    if container.id == view.container_id:
                        target_container = container
                        break

            if target_container:
                # Include components
                for component in target_container.components:
                    elements.append(
                        {
                            "type": "component",
                            "id": component.id,
                            "name": component.name,
                            "description": component.description,
                            "technology": component.technology,
                        }
                    )

                relationships = workspace.model.relationships

        return C4Diagram(
            type=view.type,
            title=view.title,
            elements=elements,
            relationships=relationships,
            layout={},
        )

    def generate_plantuml(self, workspace: C4Workspace, view: DiagramType) -> str:
        """
        Generate PlantUML C4 syntax from workspace.

        Args:
            workspace: C4 workspace
            view: Diagram type to generate

        Returns:
            PlantUML C4 syntax as string
        """
        lines = ["@startuml"]
        lines.append(
            "!include https://raw.githubusercontent.com/"
            "plantuml-stdlib/C4-PlantUML/master/C4_Context.puml"
        )

        if view in [DiagramType.CONTAINER, DiagramType.COMPONENT]:
            lines.append(
                "!include https://raw.githubusercontent.com/"
                "plantuml-stdlib/C4-PlantUML/master/C4_Container.puml"
            )

        if view == DiagramType.COMPONENT:
            lines.append(
                "!include https://raw.githubusercontent.com/"
                "plantuml-stdlib/C4-PlantUML/master/C4_Component.puml"
            )

        lines.append("")
        lines.append(f"title {workspace.name}")
        lines.append("")

        # Add people
        for person in workspace.model.people:
            lines.append(
                f'Person({person.id}, "{person.name}", ' f'"{person.description}")'
            )

        lines.append("")

        # Add systems
        for system in workspace.model.software_systems:
            if system.external:
                lines.append(
                    f'System_Ext({system.id}, "{system.name}", '
                    f'"{system.description}")'
                )
            else:
                lines.append(
                    f'System({system.id}, "{system.name}", ' f'"{system.description}")'
                )

            # Add containers if container/component view
            if view in [DiagramType.CONTAINER, DiagramType.COMPONENT]:
                for container in system.containers:
                    tech = container.technology or ""
                    lines.append(
                        f'Container({container.id}, "{container.name}", '
                        f'"{tech}", "{container.description}")'
                    )

                    # Add components if component view
                    if view == DiagramType.COMPONENT:
                        for component in container.components:
                            comp_tech = component.technology or ""
                            lines.append(
                                f"Component({component.id}, "
                                f'"{component.name}", "{comp_tech}", '
                                f'"{component.description}")'
                            )

        lines.append("")

        # Add relationships
        for rel in workspace.model.relationships:
            tech = f', "{rel.technology}"' if rel.technology else ""
            lines.append(
                f"Rel({rel.source_id}, {rel.target_id}, " f'"{rel.description}"{tech})'
            )

        lines.append("")
        lines.append("@enduml")

        return "\n".join(lines)

    def apply_design_system(
        self, workspace: C4Workspace, theme: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply custom theme/branding to workspace.

        Args:
            workspace: C4 workspace to theme
            theme: Theme configuration dictionary

        Returns:
            Applied theme dictionary
        """
        # Merge with default theme
        applied_theme = {**self.default_theme, **theme}

        # Return theme for use in rendering
        return applied_theme

    def _render_svg(self, diagram: C4Diagram, output: str) -> None:
        """
        Render diagram to SVG file.

        Args:
            diagram: Diagram to render
            output: Output SVG file path
        """
        dwg = svgwrite.Drawing(output, size=("1200px", "800px"))

        # Add title
        dwg.add(
            dwg.text(
                diagram.title,
                insert=(600, 40),
                text_anchor="middle",
                font_size=24,
                font_family=self.default_theme["font_family"],
            )
        )

        # Simple layout: vertical stack
        y_offset = 100
        x_base = 100

        # Render elements
        for i, element in enumerate(diagram.elements):
            x = x_base + (i % 3) * 350
            y = y_offset + (i // 3) * 200

            # Determine colors based on type
            colors: Dict[str, Any]
            if element["type"] == "person":
                colors = self.default_theme["person"]  # type: ignore
            elif element["type"] == "system":
                if element.get("external", False):
                    colors = self.default_theme["external_system"]  # type: ignore  # noqa: E501
                else:
                    colors = self.default_theme["system"]  # type: ignore
            elif element["type"] == "container":
                colors = self.default_theme["container"]  # type: ignore
            else:  # component
                colors = self.default_theme["component"]  # type: ignore

            # Draw box
            dwg.add(
                dwg.rect(
                    insert=(x, y),
                    size=(300, 150),
                    fill=colors["fill"],
                    stroke=colors["stroke"],
                    stroke_width=2,
                    rx=5,
                )
            )

            # Add name
            dwg.add(
                dwg.text(
                    element["name"],
                    insert=(x + 150, y + 40),
                    text_anchor="middle",
                    font_size=16,
                    font_weight="bold",
                    fill=colors["text"],
                    font_family=self.default_theme["font_family"],
                )
            )

            # Add description (wrapped)
            desc = element.get("description", "")
            if desc:
                words = desc.split()
                lines_desc = []
                current_line = []
                for word in words:
                    current_line.append(word)
                    if len(" ".join(current_line)) > 35:
                        lines_desc.append(" ".join(current_line[:-1]))
                        current_line = [word]
                if current_line:
                    lines_desc.append(" ".join(current_line))

                for j, line in enumerate(lines_desc[:3]):
                    dwg.add(
                        dwg.text(
                            line,
                            insert=(x + 150, y + 70 + j * 20),
                            text_anchor="middle",
                            font_size=12,
                            fill=colors["text"],
                            font_family=self.default_theme["font_family"],
                        )
                    )

            # Add technology if present
            tech = element.get("technology")
            if tech:
                dwg.add(
                    dwg.text(
                        f"[{tech}]",
                        insert=(x + 150, y + 135),
                        text_anchor="middle",
                        font_size=10,
                        fill=colors["text"],
                        font_family=self.default_theme["font_family"],
                    )
                )

        dwg.save()

    def _render_png(self, diagram: C4Diagram, output: str) -> None:
        """
        Render diagram to PNG file via SVG conversion.

        Args:
            diagram: Diagram to render
            output: Output PNG file path
        """
        # Create temporary SVG file
        with tempfile.NamedTemporaryFile(
            suffix=".svg", delete=False, mode="w"
        ) as tmp_svg:
            tmp_svg_path = tmp_svg.name

        try:
            # Render to SVG first
            self._render_svg(diagram, tmp_svg_path)

            # Convert SVG to PNG
            cairosvg.svg2png(url=tmp_svg_path, write_to=output)

        finally:
            # Clean up temporary SVG
            Path(tmp_svg_path).unlink(missing_ok=True)

    def render(
        self,
        workspace: C4Workspace,
        view: DiagramType,
        output: str,
        format: Optional[str] = None,
    ) -> None:
        """
        Render diagram to file.

        Args:
            workspace: C4 workspace
            view: Diagram type to render
            output: Output file path
            format: Output format (svg/png), inferred from extension if None

        Raises:
            ValueError: If output format is unsupported
        """
        # Infer format from extension if not provided
        if format is None:
            ext = Path(output).suffix.lower()
            if ext in [".svg", ".png"]:
                format = ext[1:]
            else:
                raise ValueError(f"Cannot infer format from extension: {ext}")

        # Find matching view
        target_view = None
        for v in workspace.views:
            if v.type == view:
                target_view = v
                break

        if not target_view:
            # Create default view
            target_view = C4View(
                key=f"default_{view.value}",
                type=view,
                title=f"{workspace.name} - {view.value}",
            )

        # Build diagram
        diagram = self._build_diagram(workspace, target_view)

        # Render based on format
        if format == "svg":
            self._render_svg(diagram, output)
        elif format == "png":
            self._render_png(diagram, output)
        else:
            raise ValueError(f"Unsupported output format: {format}")
