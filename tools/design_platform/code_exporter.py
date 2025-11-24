"""
Design-to-Code Exporter for devCrew_s1 Design Platform.

Provides automated export of Figma designs to production-ready code including
CSS, React components, and design tokens. Supports responsive layouts, modern
CSS features, and TypeScript.

Main Components:
    - CodeExporter: Main orchestrator for all export operations
    - CSSGenerator: CSS generation from Figma nodes
    - ReactGenerator: React component scaffolding with TypeScript support
    - DesignTokens: Design token extraction and formatting

Supported Export Formats:
    - CSS (Flexbox, Grid, responsive breakpoints)
    - React (Functional components with hooks, TypeScript)
    - Design Tokens (JSON, CSS Variables, SCSS Variables)
    - SVG optimization

Usage:
    >>> exporter = CodeExporter()
    >>> css = exporter.export_css("ABC123", ["1:5"])
    >>> component = exporter.export_react("ABC123", ["1:6"])
    >>> tokens = exporter.export_tokens("ABC123", format="json")
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .figma_client import FigmaClient, FigmaFile, FigmaNode


class ExportFormat(Enum):
    """Supported export formats."""

    CSS = "css"
    REACT = "react"
    TOKENS = "tokens"
    SVG = "svg"


class TokenFormat(Enum):
    """Design token export formats."""

    JSON = "json"
    CSS_VARS = "css_vars"
    SCSS_VARS = "scss_vars"


class ComponentStyle(Enum):
    """React component styling approaches."""

    STYLED_COMPONENTS = "styled_components"
    CSS_MODULES = "css_modules"
    INLINE_STYLES = "inline_styles"


@dataclass
class ExportConfig:
    """Configuration for code export operations."""

    format: ExportFormat
    output_dir: Path
    typescript: bool = True
    component_style: ComponentStyle = ComponentStyle.CSS_MODULES
    responsive: bool = True
    breakpoints: Dict[str, int] = field(
        default_factory=lambda: {"mobile": 480, "tablet": 768, "desktop": 1024}
    )
    optimize_svg: bool = True
    include_comments: bool = True


@dataclass
class DesignToken:
    """Individual design token representation."""

    name: str
    value: Any
    category: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CSSProperties:
    """CSS properties extracted from Figma node."""

    display: Optional[str] = None
    position: Optional[str] = None
    width: Optional[str] = None
    height: Optional[str] = None
    top: Optional[str] = None
    left: Optional[str] = None
    right: Optional[str] = None
    bottom: Optional[str] = None
    flex_direction: Optional[str] = None
    justify_content: Optional[str] = None
    align_items: Optional[str] = None
    gap: Optional[str] = None
    padding: Optional[str] = None
    margin: Optional[str] = None
    background: Optional[str] = None
    color: Optional[str] = None
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_weight: Optional[str] = None
    line_height: Optional[str] = None
    letter_spacing: Optional[str] = None
    border: Optional[str] = None
    border_radius: Optional[str] = None
    box_shadow: Optional[str] = None
    opacity: Optional[float] = None
    transform: Optional[str] = None
    transition: Optional[str] = None


class CSSGenerator:
    """Generates CSS code from Figma design nodes."""

    def __init__(self, responsive: bool = True, include_comments: bool = True):
        """
        Initialize CSS generator.

        Args:
            responsive: Enable responsive breakpoint generation
            include_comments: Include descriptive comments in output
        """
        self.responsive = responsive
        self.include_comments = include_comments
        self.breakpoints = {"mobile": 480, "tablet": 768, "desktop": 1024}

    def generate_css(self, node: FigmaNode) -> str:
        """
        Convert Figma node to CSS code.

        Args:
            node: Figma design node to convert

        Returns:
            Generated CSS code as string
        """
        properties = self._extract_properties(node)
        class_name = self._sanitize_class_name(node.name)

        css_lines = []

        if self.include_comments:
            css_lines.append(f"/* {node.name} - Generated from Figma */")

        css_lines.append(f".{class_name} {{")

        # Add properties in logical order
        css_lines.extend(self._format_properties(properties))

        css_lines.append("}")

        # Add responsive variants if enabled
        if self.responsive and hasattr(node, "children"):
            css_lines.extend(self._generate_responsive_css(node, class_name))

        return "\n".join(css_lines)

    def _extract_properties(self, node: FigmaNode) -> CSSProperties:
        """
        Extract CSS properties from Figma node.

        Args:
            node: Figma node to extract from

        Returns:
            CSSProperties object with extracted values
        """
        props = CSSProperties()
        node_dict = node.model_dump(by_alias=True)

        # Layout properties
        if "layoutMode" in node_dict:
            if node_dict["layoutMode"] == "HORIZONTAL":
                props.display = "flex"
                props.flex_direction = "row"
            elif node_dict["layoutMode"] == "VERTICAL":
                props.display = "flex"
                props.flex_direction = "column"
            else:
                props.display = "block"

        # Positioning
        if "constraints" in node_dict:
            props.position = self._get_position_type(node)

        # Dimensions
        if node.absolute_bounding_box:
            bbox = node.absolute_bounding_box
            props.width = f"{bbox.width}px"
            props.height = f"{bbox.height}px"

        # Spacing
        if "itemSpacing" in node_dict:
            props.gap = f"{node_dict['itemSpacing']}px"

        if "padding" in node_dict:
            props.padding = self._format_spacing(node_dict["padding"])

        # Background
        if "fills" in node_dict and node_dict["fills"]:
            props.background = self._extract_fill(node_dict["fills"][0])

        # Typography
        if "style" in node_dict:
            style = node_dict["style"]
            if "fontFamily" in style:
                props.font_family = style["fontFamily"]
            if "fontSize" in style:
                props.font_size = f"{style['fontSize']}px"
            if "fontWeight" in style:
                props.font_weight = str(style["fontWeight"])
            if "lineHeightPx" in style:
                props.line_height = f"{style['lineHeightPx']}px"
            if "letterSpacing" in style:
                props.letter_spacing = f"{style['letterSpacing']}px"

        # Border
        if "strokes" in node_dict and node_dict["strokes"]:
            props.border = self._extract_border_from_dict(node_dict)

        if "cornerRadius" in node_dict:
            props.border_radius = f"{node_dict['cornerRadius']}px"

        # Effects
        if "effects" in node_dict and node_dict["effects"]:
            effects = node_dict["effects"]
            shadows = [e for e in effects if e.get("type") == "DROP_SHADOW"]
            if shadows:
                props.box_shadow = self._extract_shadow(shadows[0])

        if "opacity" in node_dict:
            props.opacity = node_dict["opacity"]

        return props

    def _format_properties(self, props: CSSProperties) -> List[str]:
        """
        Format CSS properties as string lines.

        Args:
            props: CSS properties to format

        Returns:
            List of formatted CSS property lines
        """
        lines = []
        prop_map = {
            "display": props.display,
            "position": props.position,
            "width": props.width,
            "height": props.height,
            "top": props.top,
            "left": props.left,
            "right": props.right,
            "bottom": props.bottom,
            "flex-direction": props.flex_direction,
            "justify-content": props.justify_content,
            "align-items": props.align_items,
            "gap": props.gap,
            "padding": props.padding,
            "margin": props.margin,
            "background": props.background,
            "color": props.color,
            "font-family": props.font_family,
            "font-size": props.font_size,
            "font-weight": props.font_weight,
            "line-height": props.line_height,
            "letter-spacing": props.letter_spacing,
            "border": props.border,
            "border-radius": props.border_radius,
            "box-shadow": props.box_shadow,
            "opacity": props.opacity,
            "transform": props.transform,
            "transition": props.transition,
        }

        for key, value in prop_map.items():
            if value is not None:
                if isinstance(value, float):
                    lines.append(f"  {key}: {value};")
                else:
                    lines.append(f"  {key}: {value};")

        return lines

    def _generate_responsive_css(self, node: FigmaNode, class_name: str) -> List[str]:
        """
        Generate responsive media query variants.

        Args:
            node: Figma node for responsive variants
            class_name: CSS class name

        Returns:
            List of media query CSS lines
        """
        lines = []

        for breakpoint_name, breakpoint_value in self.breakpoints.items():
            if self.include_comments:
                lines.append(f"\n/* {breakpoint_name.capitalize()} */")
            lines.append(f"@media (max-width: {breakpoint_value}px) {{")
            lines.append(f"  .{class_name} {{")
            lines.append("    /* Add responsive overrides */")
            lines.append("  }")
            lines.append("}")

        return lines

    def _extract_fill(self, fill: Dict[str, Any]) -> str:
        """
        Extract fill/background from Figma fill object.

        Args:
            fill: Figma fill object

        Returns:
            CSS background value
        """
        if fill.get("type") == "SOLID":
            color = fill.get("color", {})
            r = int(color.get("r", 0) * 255)
            g = int(color.get("g", 0) * 255)
            b = int(color.get("b", 0) * 255)
            a = color.get("a", 1)
            return f"rgba({r}, {g}, {b}, {a})"
        elif fill.get("type") == "GRADIENT_LINEAR":
            return self._extract_gradient(fill)
        return "transparent"

    def _extract_gradient(self, fill: Dict[str, Any]) -> str:
        """
        Extract linear gradient from Figma fill.

        Args:
            fill: Figma gradient fill object

        Returns:
            CSS linear-gradient value
        """
        stops = fill.get("gradientStops", [])
        if not stops:
            return "transparent"

        stop_strings = []
        for stop in stops:
            color = stop.get("color", {})
            r = int(color.get("r", 0) * 255)
            g = int(color.get("g", 0) * 255)
            b = int(color.get("b", 0) * 255)
            a = color.get("a", 1)
            position = stop.get("position", 0) * 100
            stop_strings.append(f"rgba({r}, {g}, {b}, {a}) {position}%")

        return f"linear-gradient(90deg, {', '.join(stop_strings)})"

    def _extract_border_from_dict(self, node_dict: Dict[str, Any]) -> str:
        """
        Extract border from Figma node dictionary.

        Args:
            node_dict: Figma node dictionary with strokes

        Returns:
            CSS border value
        """
        stroke = node_dict["strokes"][0]
        color = self._extract_fill(stroke)
        width = node_dict.get("strokeWeight", 1)
        return f"{width}px solid {color}"

    def _extract_shadow(self, effect: Dict[str, Any]) -> str:
        """
        Extract box shadow from Figma effect.

        Args:
            effect: Figma shadow effect object

        Returns:
            CSS box-shadow value
        """
        offset_x = effect.get("offset", {}).get("x", 0)
        offset_y = effect.get("offset", {}).get("y", 0)
        radius = effect.get("radius", 0)
        color = effect.get("color", {})
        r = int(color.get("r", 0) * 255)
        g = int(color.get("g", 0) * 255)
        b = int(color.get("b", 0) * 255)
        a = color.get("a", 1)

        return f"{offset_x}px {offset_y}px {radius}px rgba({r}, {g}, {b}, {a})"

    def _format_spacing(self, padding: Union[Dict, float, int]) -> str:
        """
        Format padding/margin spacing values.

        Args:
            padding: Padding value from Figma

        Returns:
            CSS spacing value
        """
        if isinstance(padding, (int, float)):
            return f"{padding}px"
        elif isinstance(padding, dict):
            top = padding.get("top", 0)
            right = padding.get("right", 0)
            bottom = padding.get("bottom", 0)
            left = padding.get("left", 0)
            return f"{top}px {right}px {bottom}px {left}px"
        return "0"

    def _get_position_type(self, node: FigmaNode) -> str:
        """
        Determine CSS position type from constraints.

        Args:
            node: Figma node with constraints

        Returns:
            CSS position value
        """
        if not hasattr(node, "constraints"):
            return "relative"

        constraints = node.constraints
        if constraints.get("horizontal") == "FIXED":
            return "absolute"
        return "relative"

    def _sanitize_class_name(self, name: str) -> str:
        """
        Sanitize Figma node name for CSS class.

        Args:
            name: Original node name

        Returns:
            Sanitized CSS class name
        """
        sanitized = re.sub(r"[^a-zA-Z0-9-_]", "-", name)
        sanitized = re.sub(r"-+", "-", sanitized)
        return sanitized.lower().strip("-")


class ReactGenerator:
    """Generates React components from Figma designs."""

    def __init__(
        self,
        typescript: bool = True,
        component_style: ComponentStyle = ComponentStyle.CSS_MODULES,
        include_comments: bool = True,
    ):
        """
        Initialize React generator.

        Args:
            typescript: Generate TypeScript components
            component_style: Styling approach to use
            include_comments: Include descriptive comments
        """
        self.typescript = typescript
        self.component_style = component_style
        self.include_comments = include_comments
        self.css_generator = CSSGenerator(include_comments=include_comments)

    def generate_component(
        self, node: FigmaNode, component_name: str
    ) -> Dict[str, str]:
        """
        Generate React component from Figma node.

        Args:
            node: Figma design node
            component_name: Name for React component

        Returns:
            Dictionary with component code and styles
        """
        props = self._extract_props(node)
        component_code = self._generate_component_code(node, component_name, props)
        styles = self._generate_styles(node, component_name)

        return {"component": component_code, "styles": styles}

    def _extract_props(self, node: FigmaNode) -> List[Dict[str, str]]:
        """
        Extract React props from Figma component variants.

        Args:
            node: Figma component node

        Returns:
            List of prop definitions
        """
        props = []

        # Check for Figma component properties
        if hasattr(node, "componentPropertyDefinitions"):
            for prop_name, prop_def in node.componentPropertyDefinitions.items():
                prop_type = self._map_figma_type_to_typescript(prop_def.get("type"))
                props.append(
                    {
                        "name": prop_name,
                        "type": prop_type,
                        "optional": prop_def.get("defaultValue") is not None,
                    }
                )

        # Default props for common patterns
        if hasattr(node, "children"):
            props.append({"name": "children", "type": "React.ReactNode"})

        props.extend(
            [
                {"name": "className", "type": "string", "optional": True},
                {"name": "style", "type": "React.CSSProperties", "optional": True},
            ]
        )

        return props

    def _generate_component_code(
        self, node: FigmaNode, component_name: str, props: List[Dict[str, str]]
    ) -> str:
        """
        Generate React component code.

        Args:
            node: Figma node
            component_name: Component name
            props: Component props

        Returns:
            React component code
        """
        lines = []
        ext = "tsx" if self.typescript else "jsx"

        # Imports
        lines.append("import React from 'react';")

        if self.component_style == ComponentStyle.CSS_MODULES:
            lines.append(f"import styles from './{component_name}.module.css';")
        elif self.component_style == ComponentStyle.STYLED_COMPONENTS:
            lines.append("import styled from 'styled-components';")

        lines.append("")

        # Type definitions for TypeScript
        if self.typescript and props:
            lines.append(f"interface {component_name}Props {{")
            for prop in props:
                optional = "?" if prop.get("optional") else ""
                lines.append(f"  {prop['name']}{optional}: {prop['type']};")
            lines.append("}")
            lines.append("")

        # Component function
        if self.include_comments:
            lines.append(f"/**\n * {component_name} component")
            lines.append(f" * Generated from Figma node: {node.name}\n */")

        props_param = f"{component_name}Props" if self.typescript else "props"
        lines.append(f"const {component_name}: React.FC<{props_param}> = (props) => {{")

        # Destructure props
        prop_names = [p["name"] for p in props]
        lines.append(f"  const {{ {', '.join(prop_names)} }} = props;")
        lines.append("")

        # Render JSX
        lines.append("  return (")
        lines.extend(self._generate_jsx(node, component_name))
        lines.append("  );")
        lines.append("};")
        lines.append("")

        # Export
        lines.append(f"export default {component_name};")

        return "\n".join(lines)

    def _generate_jsx(self, node: FigmaNode, component_name: str) -> List[str]:
        """
        Generate JSX markup for component.

        Args:
            node: Figma node
            component_name: Component name

        Returns:
            List of JSX lines
        """
        lines = []
        tag = self._get_html_tag(node)
        class_attr = self._get_class_attribute(component_name)
        node_dict = node.model_dump(by_alias=True)

        lines.append(f"    <{tag} {class_attr}>")

        # Add children
        if node.children:
            if node.type.value == "TEXT":
                text = node_dict.get("characters", "Text content")
                lines.append(f"      {{children || '{text}'}}")
            else:
                lines.append("      {children}")
        elif node.type.value == "TEXT":
            text = node_dict.get("characters", "Text content")
            lines.append(f"      {text}")

        lines.append(f"    </{tag}>")

        return lines

    def _generate_styles(self, node: FigmaNode, component_name: str) -> str:
        """
        Generate styles for component.

        Args:
            node: Figma node
            component_name: Component name

        Returns:
            Style code based on component_style setting
        """
        if self.component_style == ComponentStyle.CSS_MODULES:
            return self.css_generator.generate_css(node)
        elif self.component_style == ComponentStyle.STYLED_COMPONENTS:
            return self._generate_styled_component(node, component_name)
        return ""

    def _generate_styled_component(self, node: FigmaNode, component_name: str) -> str:
        """
        Generate styled-components code.

        Args:
            node: Figma node
            component_name: Component name

        Returns:
            Styled-components code
        """
        properties = self.css_generator._extract_properties(node)
        tag = self._get_html_tag(node)

        lines = [f"const Styled{component_name} = styled.{tag}`"]
        lines.extend(self.css_generator._format_properties(properties))
        lines.append("`;")

        return "\n".join(lines)

    def _get_html_tag(self, node: FigmaNode) -> str:
        """
        Determine appropriate HTML tag for node.

        Args:
            node: Figma node

        Returns:
            HTML tag name
        """
        node_type = node.type.value
        if node_type == "TEXT":
            return "span"
        elif node_type in ("FRAME", "COMPONENT"):
            return "div"
        elif node_type == "RECTANGLE":
            return "div"
        elif node_type == "VECTOR":
            return "svg"
        return "div"

    def _get_class_attribute(self, component_name: str) -> str:
        """
        Generate className attribute based on styling approach.

        Args:
            component_name: Component name

        Returns:
            className JSX attribute
        """
        if self.component_style == ComponentStyle.CSS_MODULES:
            sanitized = self.css_generator._sanitize_class_name(component_name)
            return f'className={{`${{styles.{sanitized}}} ${{className || ""}}`}}'
        return "className={className}"

    def _map_figma_type_to_typescript(self, figma_type: str) -> str:
        """
        Map Figma property types to TypeScript types.

        Args:
            figma_type: Figma property type

        Returns:
            TypeScript type string
        """
        type_map = {
            "BOOLEAN": "boolean",
            "TEXT": "string",
            "INSTANCE_SWAP": "React.ReactNode",
            "VARIANT": "string",
        }
        return type_map.get(figma_type, "any")


class DesignTokens:
    """Extracts and formats design tokens from Figma files."""

    def __init__(self, include_metadata: bool = True):
        """
        Initialize design token extractor.

        Args:
            include_metadata: Include metadata in token output
        """
        self.include_metadata = include_metadata
        self.tokens: Dict[str, List[DesignToken]] = {
            "colors": [],
            "typography": [],
            "spacing": [],
            "borders": [],
            "shadows": [],
            "radii": [],
        }

    def extract_tokens(self, design_file: FigmaFile) -> Dict[str, Any]:
        """
        Extract all design tokens from Figma file.

        Args:
            design_file: Figma file to extract tokens from

        Returns:
            Dictionary of categorized design tokens
        """
        self._extract_color_tokens(design_file)
        self._extract_typography_tokens(design_file)
        self._extract_spacing_tokens(design_file)
        self._extract_effect_tokens(design_file)

        return self._format_tokens()

    def _extract_color_tokens(self, design_file: FigmaFile) -> None:
        """
        Extract color tokens from Figma styles.

        Args:
            design_file: Figma file
        """
        if not hasattr(design_file, "styles"):
            return

        for style_id, style in design_file.styles.items():
            if style.get("styleType") == "FILL":
                name = style.get("name", f"color-{style_id}")
                color_value = self._extract_color_value(style)

                self.tokens["colors"].append(
                    DesignToken(
                        name=self._sanitize_token_name(name),
                        value=color_value,
                        category="colors",
                        description=style.get("description"),
                    )
                )

    def _extract_typography_tokens(self, design_file: FigmaFile) -> None:
        """
        Extract typography tokens from Figma text styles.

        Args:
            design_file: Figma file
        """
        if not hasattr(design_file, "styles"):
            return

        for style_id, style in design_file.styles.items():
            if style.get("styleType") == "TEXT":
                name = style.get("name", f"font-{style_id}")
                text_style = style.get("style", {})

                self.tokens["typography"].append(
                    DesignToken(
                        name=self._sanitize_token_name(name),
                        value={
                            "fontFamily": text_style.get("fontFamily"),
                            "fontSize": f"{text_style.get('fontSize', 16)}px",
                            "fontWeight": text_style.get("fontWeight", 400),
                            "lineHeight": f"{text_style.get('lineHeightPx')}px",
                            "letterSpacing": f"{text_style.get('letterSpacing', 0)}px",
                        },
                        category="typography",
                        description=style.get("description"),
                    )
                )

    def _extract_spacing_tokens(self, design_file: FigmaFile) -> None:
        """
        Extract spacing tokens from common patterns.

        Args:
            design_file: Figma file
        """
        # Common spacing scale
        spacing_scale = [0, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128]

        for i, value in enumerate(spacing_scale):
            self.tokens["spacing"].append(
                DesignToken(
                    name=f"spacing-{i}",
                    value=f"{value}px",
                    category="spacing",
                    description=f"Spacing value: {value}px",
                )
            )

    def _extract_effect_tokens(self, design_file: FigmaFile) -> None:
        """
        Extract shadow and effect tokens.

        Args:
            design_file: Figma file
        """
        if not hasattr(design_file, "styles"):
            return

        for style_id, style in design_file.styles.items():
            if style.get("styleType") == "EFFECT":
                name = style.get("name", f"effect-{style_id}")
                effect_value = self._extract_effect_value(style)

                category = "shadows" if "shadow" in name.lower() else "effects"
                if category in self.tokens:
                    self.tokens[category].append(
                        DesignToken(
                            name=self._sanitize_token_name(name),
                            value=effect_value,
                            category=category,
                            description=style.get("description"),
                        )
                    )

    def _format_tokens(self) -> Dict[str, Any]:
        """
        Format extracted tokens for output.

        Returns:
            Formatted token dictionary
        """
        formatted = {}

        for category, tokens in self.tokens.items():
            if tokens:
                formatted[category] = {
                    token.name: (
                        {
                            "value": token.value,
                            "description": token.description,
                        }
                        if self.include_metadata
                        else token.value
                    )
                    for token in tokens
                }

        return formatted

    def export_json(self, tokens: Dict[str, Any]) -> str:
        """
        Export tokens as JSON.

        Args:
            tokens: Token dictionary

        Returns:
            JSON string
        """
        return json.dumps(tokens, indent=2)

    def export_css_vars(self, tokens: Dict[str, Any]) -> str:
        """
        Export tokens as CSS custom properties.

        Args:
            tokens: Token dictionary

        Returns:
            CSS variables string
        """
        lines = [":root {"]

        for category, category_tokens in tokens.items():
            lines.append(f"  /* {category.capitalize()} */")
            for name, value in category_tokens.items():
                token_value = value if isinstance(value, str) else value.get("value")
                if isinstance(token_value, dict):
                    for prop, prop_value in token_value.items():
                        var_name = f"--{name}-{self._kebab_case(prop)}"
                        lines.append(f"  {var_name}: {prop_value};")
                else:
                    lines.append(f"  --{name}: {token_value};")
            lines.append("")

        lines.append("}")
        return "\n".join(lines)

    def export_scss_vars(self, tokens: Dict[str, Any]) -> str:
        """
        Export tokens as SCSS variables.

        Args:
            tokens: Token dictionary

        Returns:
            SCSS variables string
        """
        lines = []

        for category, category_tokens in tokens.items():
            lines.append(f"// {category.capitalize()}")
            for name, value in category_tokens.items():
                token_value = value if isinstance(value, str) else value.get("value")
                if isinstance(token_value, dict):
                    lines.append(f"${name}: (")
                    for prop, prop_value in token_value.items():
                        lines.append(f"  {self._kebab_case(prop)}: {prop_value},")
                    lines.append(");")
                else:
                    lines.append(f"${name}: {token_value};")
            lines.append("")

        return "\n".join(lines)

    def _extract_color_value(self, style: Dict[str, Any]) -> str:
        """
        Extract color value from style.

        Args:
            style: Figma style object

        Returns:
            Color value as hex or rgba
        """
        # Simplified extraction - would use actual Figma paint data
        return "#000000"

    def _extract_effect_value(self, style: Dict[str, Any]) -> str:
        """
        Extract effect value from style.

        Args:
            style: Figma style object

        Returns:
            Effect value string
        """
        # Simplified extraction
        return "0px 2px 4px rgba(0, 0, 0, 0.1)"

    def _sanitize_token_name(self, name: str) -> str:
        """
        Sanitize token name for output.

        Args:
            name: Original name

        Returns:
            Sanitized name
        """
        sanitized = re.sub(r"[^a-zA-Z0-9-_/]", "-", name)
        sanitized = re.sub(r"-+", "-", sanitized)
        return sanitized.lower().strip("-")

    def _kebab_case(self, text: str) -> str:
        """
        Convert text to kebab-case.

        Args:
            text: Input text

        Returns:
            Kebab-cased text
        """
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", text)
        return re.sub("([a-z0-9])([A-Z])", r"\1-\2", s1).lower()


class CodeExporter:
    """Main orchestrator for design-to-code export operations."""

    def __init__(
        self,
        figma_token: Optional[str] = None,
        export_config: Optional[ExportConfig] = None,
    ):
        """
        Initialize code exporter.

        Args:
            figma_token: Figma API access token
            export_config: Export configuration
        """
        self.figma_client = FigmaClient(access_token=figma_token or "")
        self.config = export_config or ExportConfig(
            format=ExportFormat.CSS, output_dir=Path("./output")
        )
        self.css_generator = CSSGenerator(
            responsive=self.config.responsive,
            include_comments=self.config.include_comments,
        )
        self.react_generator = ReactGenerator(
            typescript=self.config.typescript,
            component_style=self.config.component_style,
            include_comments=self.config.include_comments,
        )
        self.token_extractor = DesignTokens(include_metadata=True)

    def export_css(self, file_key: str, node_ids: List[str]) -> List[str]:
        """
        Export CSS for specified Figma nodes.

        Args:
            file_key: Figma file key
            node_ids: List of node IDs to export

        Returns:
            List of generated CSS strings
        """
        css_outputs = []
        nodes = self.figma_client.get_file_nodes(file_key, node_ids)

        for node_id in node_ids:
            if node_id in nodes:
                node = nodes[node_id]
                css = self.css_generator.generate_css(node)
                css_outputs.append(css)

                # Write to file if output directory configured
                if self.config.output_dir:
                    filename = f"{self._sanitize_filename(node.name)}.css"
                    self._write_output(filename, css)

        return css_outputs

    def export_react(self, file_key: str, node_ids: List[str]) -> List[Dict[str, str]]:
        """
        Export React components for specified Figma nodes.

        Args:
            file_key: Figma file key
            node_ids: List of node IDs to export

        Returns:
            List of dictionaries with component and style code
        """
        component_outputs = []
        nodes = self.figma_client.get_file_nodes(file_key, node_ids)

        for node_id in node_ids:
            if node_id in nodes:
                node = nodes[node_id]
                component_name = self._to_pascal_case(node.name)
                result = self.react_generator.generate_component(node, component_name)
                component_outputs.append(result)

                # Write to files if output directory configured
                if self.config.output_dir:
                    ext = "tsx" if self.config.typescript else "jsx"
                    self._write_output(f"{component_name}.{ext}", result["component"])
                    if result["styles"]:
                        if self.config.component_style == ComponentStyle.CSS_MODULES:
                            style_ext = "module.css"
                        else:
                            style_ext = "styles.ts"
                        self._write_output(
                            f"{component_name}.{style_ext}", result["styles"]
                        )

        return component_outputs

    def export_tokens(self, file_key: str, format: str = "json") -> str:
        """
        Export design tokens from Figma file.

        Args:
            file_key: Figma file key
            format: Output format (json, css_vars, scss_vars)

        Returns:
            Formatted design tokens string
        """
        design_file = self.figma_client.get_file(file_key)
        tokens = self.token_extractor.extract_tokens(design_file)

        if format == "json":
            output = self.token_extractor.export_json(tokens)
            filename = "design-tokens.json"
        elif format == "css_vars":
            output = self.token_extractor.export_css_vars(tokens)
            filename = "design-tokens.css"
        elif format == "scss_vars":
            output = self.token_extractor.export_scss_vars(tokens)
            filename = "design-tokens.scss"
        else:
            raise ValueError(f"Unsupported token format: {format}")

        # Write to file if output directory configured
        if self.config.output_dir:
            self._write_output(filename, output)

        return output

    def optimize_svg(self, svg_content: str) -> str:
        """
        Optimize SVG content for web use.

        Args:
            svg_content: Raw SVG content

        Returns:
            Optimized SVG content
        """
        if not self.config.optimize_svg:
            return svg_content

        # Remove comments
        svg_content = re.sub(r"<!--.*?-->", "", svg_content, flags=re.DOTALL)

        # Remove unnecessary whitespace
        svg_content = re.sub(r"\s+", " ", svg_content)

        # Remove default attributes
        svg_content = re.sub(r'\s+xmlns:xlink="[^"]*"', "", svg_content)

        # Round decimals to 2 places
        def round_decimals(match):
            return str(round(float(match.group(0)), 2))

        svg_content = re.sub(r"\d+\.\d{3,}", round_decimals, svg_content)

        return svg_content.strip()

    def _write_output(self, filename: str, content: str) -> None:
        """
        Write output to file.

        Args:
            filename: Output filename
            content: File content
        """
        output_path = self.config.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize filename from node name.

        Args:
            name: Original name

        Returns:
            Sanitized filename
        """
        sanitized = re.sub(r"[^a-zA-Z0-9-_]", "-", name)
        sanitized = re.sub(r"-+", "-", sanitized)
        return sanitized.lower().strip("-")

    def _to_pascal_case(self, text: str) -> str:
        """
        Convert text to PascalCase.

        Args:
            text: Input text

        Returns:
            PascalCase text
        """
        words = re.sub(r"[^a-zA-Z0-9]", " ", text).split()
        return "".join(word.capitalize() for word in words)
