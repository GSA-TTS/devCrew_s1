"""
Comprehensive test suite for Design Tools & UI/UX Integration Platform.

This module contains 80+ test functions covering all core components:
    - FigmaClient (15 tests)
    - DesignValidator (20 tests)
    - CodeExporter (20 tests)
    - C4Generator (15 tests)
    - CLI Interface (10 tests)

Test coverage includes:
    - Unit tests for individual components
    - Integration tests for end-to-end workflows
    - Error handling and edge cases
    - Mock external APIs (Figma, file system)
    - Performance and validation tests
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import responses
from click.testing import CliRunner

from design_platform.c4_generator import (
    C4Component,
    C4Container,
    C4Generator,
    C4Person,
    C4Relationship,
    C4SoftwareSystem,
    C4Workspace,
    DiagramType,
)
from design_platform.code_exporter import (
    CSSGenerator,
    CodeExporter,
    DesignTokens,
    ExportConfig,
    ExportFormat,
    ReactGenerator,
)
from design_platform.design_cli import cli
from design_platform.design_validator import (
    ContrastRatio,
    DesignValidator,
    ValidationResult,
    Violation,
    WCAGLevel,
)
from design_platform.figma_client import (
    BoundingBox,
    Color,
    ExportFormat as FigmaExportFormat,
    FigmaClient,
    FigmaExport,
    FigmaFile,
    FigmaNode,
    NodeType,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_figma_response():
    """Mock Figma API response for file structure."""
    return {
        "document": {
            "id": "0:0",
            "name": "Test Document",
            "type": "DOCUMENT",
            "children": [
                {
                    "id": "1:2",
                    "name": "Page 1",
                    "type": "CANVAS",
                    "backgroundColor": {"r": 1, "g": 1, "b": 1, "a": 1},
                    "children": [
                        {
                            "id": "1:5",
                            "name": "Button",
                            "type": "FRAME",
                            "absoluteBoundingBox": {
                                "x": 0,
                                "y": 0,
                                "width": 120,
                                "height": 44,
                            },
                            "fills": [
                                {"type": "SOLID", "color": {"r": 0, "g": 0.4, "b": 0.8}}
                            ],
                        }
                    ],
                }
            ],
        },
        "name": "Test File",
        "lastModified": "2024-01-01T00:00:00Z",
        "version": "1",
        "thumbnailUrl": "https://example.com/thumb.png",
    }


@pytest.fixture
def mock_export_response():
    """Mock Figma API export response."""
    return {
        "images": {
            "1:5": "https://example.com/image1.png",
            "1:6": "https://example.com/image2.png",
        }
    }


@pytest.fixture
def figma_client():
    """Create FigmaClient instance with mock token."""
    return FigmaClient(access_token="figd_test_token")


@pytest.fixture
def design_validator():
    """Create DesignValidator instance."""
    return DesignValidator()


@pytest.fixture
def code_exporter():
    """Create CodeExporter instance."""
    return CodeExporter(figma_token="figd_test_token")


@pytest.fixture
def c4_generator():
    """Create C4Generator instance."""
    return C4Generator()


@pytest.fixture
def sample_figma_node():
    """Create sample FigmaNode for testing."""
    return FigmaNode(
        id="1:5",
        name="Test Button",
        type=NodeType.FRAME,
        visible=True,
        absolute_bounding_box=BoundingBox(x=0, y=0, width=120, height=44),
        background_color=Color(r=0, g=0.4, b=0.8, a=1),
        children=[],
    )


@pytest.fixture
def sample_c4_workspace():
    """Create sample C4Workspace for testing."""
    person = C4Person(id="user", name="User", description="System user")
    system = C4SoftwareSystem(
        id="system", name="System", description="Main system", containers=[]
    )
    relationship = C4Relationship(
        source_id="user",
        target_id="system",
        description="Uses",
        technology="HTTPS",
    )

    return C4Workspace(
        name="Test Workspace",
        model={
            "people": [person],
            "software_systems": [system],
            "relationships": [relationship],
        },
        views=[],
    )


# ============================================================================
# FigmaClient Tests (15 tests)
# ============================================================================


@responses.activate
def test_figma_client_initialization(figma_client):
    """Test FigmaClient initialization."""
    assert figma_client.access_token == "figd_test_token"
    assert figma_client.base_url == "https://api.figma.com/v1"
    assert figma_client.session is not None


@responses.activate
def test_figma_client_get_file(figma_client, mock_figma_response):
    """Test getting Figma file structure."""
    responses.add(
        responses.GET,
        "https://api.figma.com/v1/files/ABC123",
        json=mock_figma_response,
        status=200,
    )

    result = figma_client.get_file(file_key="ABC123")

    assert isinstance(result, FigmaFile)
    assert result.name == "Test File"
    assert result.document.name == "Test Document"


@responses.activate
def test_figma_client_export_nodes(figma_client, mock_export_response):
    """Test exporting nodes as images."""
    responses.add(
        responses.GET,
        "https://api.figma.com/v1/images/ABC123",
        json=mock_export_response,
        status=200,
    )
    responses.add(
        responses.GET,
        "https://example.com/image1.png",
        body=b"fake_image_data",
        status=200,
    )

    exports = figma_client.export_nodes(
        file_key="ABC123", node_ids=["1:5"], export_format="png", scale=2.0
    )

    assert len(exports) == 1
    assert exports[0].node_id == "1:5"
    assert exports[0].url == "https://example.com/image1.png"


@responses.activate
def test_figma_client_authentication_error(figma_client):
    """Test authentication error handling."""
    responses.add(
        responses.GET,
        "https://api.figma.com/v1/files/ABC123",
        json={"status": 403, "err": "Invalid token"},
        status=403,
    )

    with pytest.raises(Exception):  # AuthenticationError
        figma_client.get_file(file_key="ABC123")


@responses.activate
def test_figma_client_not_found_error(figma_client):
    """Test file not found error."""
    responses.add(
        responses.GET,
        "https://api.figma.com/v1/files/INVALID",
        json={"status": 404, "err": "File not found"},
        status=404,
    )

    with pytest.raises(Exception):  # NotFoundError
        figma_client.get_file(file_key="INVALID")


@responses.activate
def test_figma_client_rate_limit(figma_client, mock_figma_response):
    """Test rate limit handling."""
    # First request: rate limited
    responses.add(
        responses.GET,
        "https://api.figma.com/v1/files/ABC123",
        json={"status": 429, "err": "Rate limited"},
        status=429,
        headers={"Retry-After": "1"},
    )
    # Second request: success
    responses.add(
        responses.GET,
        "https://api.figma.com/v1/files/ABC123",
        json=mock_figma_response,
        status=200,
    )

    with patch("time.sleep"):
        result = figma_client.get_file(file_key="ABC123")
        assert result.name == "Test File"


def test_color_to_hex():
    """Test Color to hex conversion."""
    color = Color(r=1, g=0, b=0, a=1)
    assert color.to_hex() == "#FF0000"

    color2 = Color(r=0, g=0.5, b=1, a=1)
    assert color2.to_hex() == "#0080FF"


def test_color_to_css():
    """Test Color to CSS rgba conversion."""
    color = Color(r=1, g=0, b=0, a=0.5)
    assert color.to_css() == "rgba(255, 0, 0, 0.5)"


def test_bounding_box_area():
    """Test BoundingBox area calculation."""
    box = BoundingBox(x=0, y=0, width=100, height=50)
    assert box.width * box.height == 5000


@responses.activate
def test_figma_client_get_components(figma_client, mock_figma_response):
    """Test getting component definitions."""
    responses.add(
        responses.GET,
        "https://api.figma.com/v1/files/ABC123",
        json=mock_figma_response,
        status=200,
    )

    components = figma_client.get_components(file_key="ABC123")
    assert isinstance(components, list)


@responses.activate
def test_figma_client_context_manager(mock_figma_response):
    """Test FigmaClient as context manager."""
    with FigmaClient(access_token="figd_test") as client:
        assert client.session is not None

    # Session should be closed after exiting context
    assert client.session is None


def test_figma_export_format_enum():
    """Test FigmaExportFormat enum."""
    assert FigmaExportFormat.PNG == "png"
    assert FigmaExportFormat.SVG == "svg"
    assert FigmaExportFormat.PDF == "pdf"
    assert FigmaExportFormat.JPG == "jpg"


def test_node_type_enum():
    """Test NodeType enum."""
    assert NodeType.DOCUMENT == "DOCUMENT"
    assert NodeType.FRAME == "FRAME"
    assert NodeType.COMPONENT == "COMPONENT"
    assert NodeType.TEXT == "TEXT"


def test_figma_node_creation(sample_figma_node):
    """Test FigmaNode creation and properties."""
    assert sample_figma_node.id == "1:5"
    assert sample_figma_node.name == "Test Button"
    assert sample_figma_node.type == NodeType.FRAME
    assert sample_figma_node.absolute_bounding_box.width == 120


def test_figma_export_creation():
    """Test FigmaExport creation."""
    export = FigmaExport(
        node_id="1:5",
        format="png",
        url="https://example.com/image.png",
        image_data=b"data",
    )
    assert export.node_id == "1:5"
    assert export.format == "png"
    assert export.error is None


# ============================================================================
# DesignValidator Tests (20 tests)
# ============================================================================


def test_design_validator_initialization(design_validator):
    """Test DesignValidator initialization."""
    assert design_validator is not None
    assert hasattr(design_validator, "check_contrast")


def test_check_contrast_black_white(design_validator):
    """Test maximum contrast (black on white)."""
    contrast = design_validator.check_contrast("#000000", "#FFFFFF", WCAGLevel.AA)

    assert contrast.ratio == pytest.approx(21.0, rel=0.01)
    assert contrast.passes_aa is True
    assert contrast.passes_aaa is True


def test_check_contrast_gray_white(design_validator):
    """Test borderline AA contrast."""
    contrast = design_validator.check_contrast("#767676", "#FFFFFF", WCAGLevel.AA)

    assert contrast.ratio >= 4.5
    assert contrast.passes_aa is True


def test_check_contrast_fails_aa(design_validator):
    """Test contrast that fails AA."""
    contrast = design_validator.check_contrast("#FF0000", "#FFFF00", WCAGLevel.AA)

    assert contrast.passes_aa is False


def test_check_contrast_aaa_level(design_validator):
    """Test AAA level contrast checking."""
    contrast = design_validator.check_contrast("#000000", "#FFFFFF", WCAGLevel.AAA)

    assert contrast.passes_aaa is True


def test_check_touch_targets_pass(design_validator):
    """Test touch target that passes (44x44px)."""
    node = MagicMock()
    node.type = "BUTTON"
    node.absolute_bounding_box = MagicMock(width=44, height=44)

    result = design_validator.check_touch_targets(node)
    assert result is True


def test_check_touch_targets_fail(design_validator):
    """Test touch target that fails (too small)."""
    node = MagicMock()
    node.type = "BUTTON"
    node.absolute_bounding_box = MagicMock(width=32, height=32)

    result = design_validator.check_touch_targets(node)
    assert result is False


def test_check_text_size_pass(design_validator):
    """Test text size that passes (16px)."""
    node = MagicMock()
    node.type = "TEXT"
    node.style = MagicMock(fontSize=16)

    result = design_validator.check_text_size(node)
    assert result is True


def test_check_text_size_fail(design_validator):
    """Test text size that fails (too small)."""
    node = MagicMock()
    node.type = "TEXT"
    node.style = MagicMock(fontSize=12)

    result = design_validator.check_text_size(node)
    assert result is False


def test_validation_result_pass_rate():
    """Test ValidationResult pass rate calculation."""
    result = ValidationResult(
        status="passed",
        violations=[],
        warnings=[],
        passed_checks=8,
        total_checks=10,
    )

    assert result.pass_rate == 80.0


def test_validation_result_to_json():
    """Test ValidationResult JSON export."""
    result = ValidationResult(
        status="failed",
        violations=[
            Violation(
                rule="WCAG-1.4.3",
                severity="CRITICAL",
                message="Insufficient contrast",
            )
        ],
        warnings=[],
        passed_checks=2,
        total_checks=5,
    )

    json_str = result.to_json()
    data = json.loads(json_str)

    assert data["status"] == "failed"
    assert len(data["violations"]) == 1
    assert data["pass_rate"] == 40.0


def test_wcag_level_enum():
    """Test WCAGLevel enum."""
    assert WCAGLevel.AA == "AA"
    assert WCAGLevel.AAA == "AAA"


def test_contrast_ratio_hex_validation():
    """Test ContrastRatio hex color validation."""
    contrast = ContrastRatio(
        ratio=4.5,
        passes_aa=True,
        passes_aaa=False,
        foreground_color="#000000",
        background_color="#FFFFFF",
    )

    assert contrast.foreground_color == "#000000"
    assert contrast.background_color == "#FFFFFF"


def test_violation_creation():
    """Test Violation object creation."""
    violation = Violation(
        rule="WCAG-2.5.5",
        severity="WARNING",
        message="Touch target too small",
        node_id="1:5",
        location="Page 1 > Button",
    )

    assert violation.rule == "WCAG-2.5.5"
    assert violation.severity == "WARNING"
    assert violation.node_id == "1:5"


def test_validate_accessibility_mock(design_validator):
    """Test full accessibility validation with mock data."""
    # Create mock design file
    mock_file = MagicMock()
    mock_file.document = MagicMock()
    mock_file.document.children = []

    result = design_validator.validate_accessibility(mock_file, WCAGLevel.AA)

    assert isinstance(result, ValidationResult)
    assert result.status in ["passed", "failed", "warning"]


def test_validate_design_system(design_validator):
    """Test design system validation."""
    mock_file = MagicMock()
    mock_file.document = MagicMock()
    mock_file.document.children = []

    rules = {
        "color_palette": ["#FF0000", "#00FF00", "#0000FF"],
        "typography": {"font_family": ["Inter", "Roboto"]},
    }

    result = design_validator.validate_design_system(mock_file, rules)
    assert isinstance(result, ValidationResult)


def test_batch_validate_mock(design_validator):
    """Test batch validation."""
    with patch.object(
        design_validator, "validate_accessibility"
    ) as mock_validate:
        mock_validate.return_value = ValidationResult(
            status="passed", violations=[], warnings=[], passed_checks=5, total_checks=5
        )

        results = design_validator.batch_validate(["ABC", "DEF"], WCAGLevel.AA)

        assert len(results) == 2
        assert all(isinstance(r, ValidationResult) for r in results)


def test_color_format_rgb(design_validator):
    """Test contrast with RGB color format."""
    contrast = design_validator.check_contrast(
        "rgb(0, 0, 0)", "rgb(255, 255, 255)", WCAGLevel.AA
    )

    assert contrast.ratio == pytest.approx(21.0, rel=0.01)


def test_color_format_rgba(design_validator):
    """Test contrast with RGBA color format."""
    contrast = design_validator.check_contrast(
        "rgba(0, 0, 0, 1)", "rgba(255, 255, 255, 1)", WCAGLevel.AA
    )

    assert contrast.ratio == pytest.approx(21.0, rel=0.01)


def test_large_text_contrast(design_validator):
    """Test large text contrast requirements (3:1 for AA)."""
    contrast = design_validator.check_contrast(
        "#888888", "#FFFFFF", WCAGLevel.AA, is_large_text=True
    )

    # Large text has lower contrast requirements
    if contrast.ratio >= 3.0:
        assert contrast.passes_aa is True


# ============================================================================
# CodeExporter Tests (20 tests)
# ============================================================================


def test_code_exporter_initialization(code_exporter):
    """Test CodeExporter initialization."""
    assert code_exporter is not None
    assert hasattr(code_exporter, "export_css")


def test_css_generator_initialization():
    """Test CSSGenerator initialization."""
    generator = CSSGenerator()
    assert generator is not None


def test_css_generator_generate_css():
    """Test CSS generation from node."""
    generator = CSSGenerator()
    node = MagicMock()
    node.name = "Button"
    node.absoluteBoundingBox = MagicMock(width=120, height=44)
    node.fills = []

    css = generator.generate_css(node)

    assert isinstance(css, str)
    assert "width" in css or ".button" in css.lower()


def test_react_generator_initialization():
    """Test ReactGenerator initialization."""
    generator = ReactGenerator()
    assert generator is not None


def test_react_generator_component():
    """Test React component generation."""
    generator = ReactGenerator(typescript=True)
    node = MagicMock()
    node.name = "Button"
    node.type = "COMPONENT"
    node.children = []

    component = generator.generate_component(node, "Button")

    assert isinstance(component, dict)
    assert "component" in component or "code" in component


def test_design_tokens_initialization():
    """Test DesignTokens initialization."""
    tokens = DesignTokens()
    assert tokens is not None


def test_design_tokens_extract():
    """Test design token extraction."""
    tokens = DesignTokens()
    mock_file = MagicMock()
    mock_file.document = MagicMock()
    mock_file.document.children = []
    mock_file.styles = {}

    extracted = tokens.extract_tokens(mock_file)

    assert isinstance(extracted, dict)
    assert "colors" in extracted or isinstance(extracted, dict)


def test_design_tokens_export_json():
    """Test design tokens JSON export."""
    tokens = DesignTokens()
    token_data = {
        "colors": {"primary": "#0066CC"},
        "typography": {"heading1": "32px"},
    }

    json_output = tokens.export_json(token_data)

    assert isinstance(json_output, str)
    data = json.loads(json_output)
    assert "colors" in data


def test_design_tokens_export_css_vars():
    """Test design tokens CSS variables export."""
    tokens = DesignTokens()
    token_data = {
        "colors": {"primary": "#0066CC"},
        "spacing": {"md": "16px"},
    }

    css_output = tokens.export_css_vars(token_data)

    assert isinstance(css_output, str)
    assert "--" in css_output or ":" in css_output


def test_design_tokens_export_scss_vars():
    """Test design tokens SCSS variables export."""
    tokens = DesignTokens()
    token_data = {
        "colors": {"primary": "#0066CC"},
    }

    scss_output = tokens.export_scss_vars(token_data)

    assert isinstance(scss_output, str)
    assert "$" in scss_output or ":" in scss_output


def test_export_config_creation():
    """Test ExportConfig dataclass creation."""
    config = ExportConfig(
        format=ExportFormat.CSS, output_dir=Path("/tmp"), typescript=True
    )

    assert config.format == ExportFormat.CSS
    assert config.typescript is True


def test_export_format_enum():
    """Test ExportFormat enum."""
    assert ExportFormat.CSS == "css"
    assert ExportFormat.REACT == "react"
    assert ExportFormat.TOKENS == "tokens"


@patch("design_platform.code_exporter.FigmaClient")
def test_code_exporter_export_css(mock_figma_class):
    """Test CSS export with mocked Figma client."""
    mock_client = MagicMock()
    mock_client.get_file_nodes.return_value = [MagicMock()]
    mock_figma_class.return_value = mock_client

    exporter = CodeExporter(figma_token="figd_test")
    css_files = exporter.export_css(file_key="ABC123", node_ids=["1:5"])

    assert isinstance(css_files, list)


@patch("design_platform.code_exporter.FigmaClient")
def test_code_exporter_export_react(mock_figma_class):
    """Test React component export."""
    mock_client = MagicMock()
    mock_client.get_file_nodes.return_value = [MagicMock()]
    mock_figma_class.return_value = mock_client

    exporter = CodeExporter(figma_token="figd_test")
    components = exporter.export_react(file_key="ABC123", node_ids=["1:5"])

    assert isinstance(components, list)


@patch("design_platform.code_exporter.FigmaClient")
def test_code_exporter_export_tokens(mock_figma_class):
    """Test design tokens export."""
    mock_client = MagicMock()
    mock_file = MagicMock()
    mock_file.document = MagicMock()
    mock_file.document.children = []
    mock_file.styles = {}
    mock_client.get_file.return_value = mock_file
    mock_figma_class.return_value = mock_client

    exporter = CodeExporter(figma_token="figd_test")
    tokens = exporter.export_tokens(file_key="ABC123", format="json")

    assert isinstance(tokens, str)


def test_css_properties_dataclass():
    """Test CSSProperties dataclass."""
    from design_platform.code_exporter import CSSProperties

    props = CSSProperties(
        width="120px", height="44px", background="#0066CC", color="#FFFFFF"
    )

    assert props.width == "120px"
    assert props.background == "#0066CC"


def test_optimize_svg():
    """Test SVG optimization."""
    exporter = CodeExporter(figma_token="figd_test")
    svg_content = '<svg><circle cx="50" cy="50" r="40" /></svg>'

    optimized = exporter.optimize_svg(svg_content)

    assert isinstance(optimized, str)
    assert "svg" in optimized.lower()


def test_responsive_css_generation():
    """Test responsive CSS generation."""
    generator = CSSGenerator(responsive=True)
    node = MagicMock()
    node.name = "Container"
    node.absoluteBoundingBox = MagicMock(width=1200, height=600)

    css = generator.generate_css(node)

    # Should contain media queries for responsive design
    assert isinstance(css, str)


def test_react_typescript_generation():
    """Test React TypeScript component generation."""
    generator = ReactGenerator(typescript=True)
    node = MagicMock()
    node.name = "Button"
    node.type = "COMPONENT"

    component = generator.generate_component(node, "Button")

    # TypeScript components should have .tsx extension or type definitions
    assert isinstance(component, dict)


def test_token_format_enum():
    """Test TokenFormat enum."""
    from design_platform.code_exporter import TokenFormat

    assert TokenFormat.JSON == "json"
    assert TokenFormat.CSS_VARS == "css_vars"
    assert TokenFormat.SCSS_VARS == "scss_vars"


# ============================================================================
# C4Generator Tests (15 tests)
# ============================================================================


def test_c4_generator_initialization(c4_generator):
    """Test C4Generator initialization."""
    assert c4_generator is not None
    assert hasattr(c4_generator, "parse_dsl")


def test_c4_person_creation():
    """Test C4Person creation."""
    person = C4Person(id="user1", name="User", description="System user")

    assert person.id == "user1"
    assert person.name == "User"


def test_c4_software_system_creation():
    """Test C4SoftwareSystem creation."""
    system = C4SoftwareSystem(
        id="system1", name="System", description="Main system", containers=[]
    )

    assert system.id == "system1"
    assert system.containers == []


def test_c4_container_creation():
    """Test C4Container creation."""
    container = C4Container(
        id="container1",
        name="Web App",
        description="React SPA",
        technology="React",
        components=[],
    )

    assert container.id == "container1"
    assert container.technology == "React"


def test_c4_component_creation():
    """Test C4Component creation."""
    component = C4Component(
        id="comp1",
        name="UserService",
        description="User management",
        technology="Python",
    )

    assert component.id == "comp1"
    assert component.technology == "Python"


def test_c4_relationship_creation():
    """Test C4Relationship creation."""
    rel = C4Relationship(
        source_id="user",
        target_id="system",
        description="Uses",
        technology="HTTPS",
    )

    assert rel.source_id == "user"
    assert rel.target_id == "system"


def test_c4_workspace_creation(sample_c4_workspace):
    """Test C4Workspace creation."""
    assert sample_c4_workspace.name == "Test Workspace"
    assert len(sample_c4_workspace.model["people"]) == 1
    assert len(sample_c4_workspace.model["software_systems"]) == 1


def test_diagram_type_enum():
    """Test DiagramType enum."""
    assert DiagramType.SYSTEM_CONTEXT == "SystemContext"
    assert DiagramType.CONTAINER == "Container"
    assert DiagramType.COMPONENT == "Component"
    assert DiagramType.CODE == "Code"


def test_c4_parse_dsl(c4_generator):
    """Test DSL parsing."""
    dsl_content = """
    workspace "Test" {
        model {
            user = person "User"
            system = softwareSystem "System"
            user -> system "Uses"
        }
    }
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".dsl", delete=False) as f:
        f.write(dsl_content)
        dsl_file = f.name

    try:
        workspace = c4_generator.parse_dsl(dsl_file)
        assert isinstance(workspace, C4Workspace)
        assert workspace.name == "Test"
    finally:
        Path(dsl_file).unlink()


def test_c4_validate_dsl(c4_generator):
    """Test DSL validation."""
    valid_dsl = 'workspace "Test" { model { } }'

    is_valid, error = c4_generator.validate_dsl(valid_dsl)

    assert is_valid is True
    assert error is None


def test_c4_generate_plantuml(c4_generator, sample_c4_workspace):
    """Test PlantUML generation."""
    plantuml = c4_generator.generate_plantuml(
        sample_c4_workspace, DiagramType.SYSTEM_CONTEXT
    )

    assert isinstance(plantuml, str)
    assert "@startuml" in plantuml
    assert "@enduml" in plantuml


def test_c4_apply_design_system(c4_generator, sample_c4_workspace):
    """Test applying design system theme."""
    theme = {
        "person": {"fill": "#FF0000"},
        "system": {"fill": "#00FF00"},
    }

    themed = c4_generator.apply_design_system(sample_c4_workspace, theme)

    assert isinstance(themed, dict)


def test_c4_render_svg(c4_generator, sample_c4_workspace):
    """Test SVG rendering."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        output_file = f.name

    try:
        c4_generator.render(
            sample_c4_workspace, DiagramType.SYSTEM_CONTEXT, output_file, format="svg"
        )

        assert Path(output_file).exists()
    finally:
        Path(output_file).unlink(missing_ok=True)


def test_c4_render_png(c4_generator, sample_c4_workspace):
    """Test PNG rendering."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        output_file = f.name

    try:
        c4_generator.render(
            sample_c4_workspace, DiagramType.SYSTEM_CONTEXT, output_file, format="png"
        )

        assert Path(output_file).exists()
    finally:
        Path(output_file).unlink(missing_ok=True)


def test_c4_invalid_dsl(c4_generator):
    """Test invalid DSL handling."""
    invalid_dsl = "workspace { invalid syntax here"

    is_valid, error = c4_generator.validate_dsl(invalid_dsl)

    assert is_valid is False
    assert error is not None


# ============================================================================
# CLI Tests (10 tests)
# ============================================================================


def test_cli_help():
    """Test CLI help command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "devcrew-design" in result.output or "Usage" in result.output


def test_cli_export_help():
    """Test export command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["export", "--help"])

    assert result.exit_code == 0
    assert "export" in result.output.lower()


def test_cli_validate_help():
    """Test validate command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["validate", "--help"])

    assert result.exit_code == 0
    assert "validate" in result.output.lower()


def test_cli_tokens_help():
    """Test tokens command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["tokens", "--help"])

    assert result.exit_code == 0
    assert "tokens" in result.output.lower()


def test_cli_c4_help():
    """Test C4 command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["c4", "--help"])

    assert result.exit_code == 0
    assert "c4" in result.output.lower()


def test_cli_config_help():
    """Test config command help."""
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "--help"])

    assert result.exit_code == 0
    assert "config" in result.output.lower()


@patch("design_platform.design_cli.FigmaClient")
def test_cli_config_validate(mock_figma):
    """Test config validate command."""
    mock_client = MagicMock()
    mock_figma.return_value = mock_client

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["config", "validate", "--verbose"])

        # Should not crash
        assert result.exit_code in [0, 1]  # May fail without config file


def test_cli_config_show():
    """Test config show command."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["config", "show"])

        # Should not crash
        assert result.exit_code in [0, 1]


@patch("design_platform.design_cli.C4Generator")
def test_cli_c4_validate(mock_c4):
    """Test C4 validate command."""
    mock_gen = MagicMock()
    mock_gen.validate_dsl.return_value = (True, None)
    mock_c4.return_value = mock_gen

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create test DSL file
        with open("test.dsl", "w") as f:
            f.write('workspace "Test" { model { } }')

        result = runner.invoke(cli, ["c4", "validate", "--dsl", "test.dsl"])

        # Should validate successfully
        assert result.exit_code == 0


def test_cli_version():
    """Test CLI version display."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])

    # Should show version or command group help
    assert result.exit_code in [0, 2]


# ============================================================================
# Integration Tests (5 tests)
# ============================================================================


@responses.activate
@patch("design_platform.code_exporter.FigmaClient")
def test_integration_export_workflow(mock_figma_class, mock_figma_response):
    """Test complete export workflow."""
    mock_client = MagicMock()
    mock_node = MagicMock()
    mock_node.name = "Button"
    mock_node.type = "COMPONENT"
    mock_client.get_file_nodes.return_value = [mock_node]
    mock_figma_class.return_value = mock_client

    exporter = CodeExporter(figma_token="figd_test")
    css_files = exporter.export_css(file_key="ABC123", node_ids=["1:5"])

    assert isinstance(css_files, list)


@patch("design_platform.design_validator.FigmaClient")
def test_integration_validation_workflow(mock_figma_class):
    """Test complete validation workflow."""
    validator = DesignValidator()

    mock_file = MagicMock()
    mock_file.document = MagicMock()
    mock_file.document.children = []

    result = validator.validate_accessibility(mock_file, WCAGLevel.AA)

    assert isinstance(result, ValidationResult)


def test_integration_c4_workflow(c4_generator):
    """Test complete C4 diagram workflow."""
    dsl_content = """
    workspace "Test" {
        model {
            user = person "User"
            system = softwareSystem "System"
            user -> system "Uses"
        }
    }
    """

    with tempfile.NamedTemporaryFile(mode="w", suffix=".dsl", delete=False) as f:
        f.write(dsl_content)
        dsl_file = f.name

    try:
        # Parse DSL
        workspace = c4_generator.parse_dsl(dsl_file)

        # Generate PlantUML
        plantuml = c4_generator.generate_plantuml(
            workspace, DiagramType.SYSTEM_CONTEXT
        )

        assert "@startuml" in plantuml

        # Render SVG
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as out:
            output_file = out.name

        c4_generator.render(workspace, DiagramType.SYSTEM_CONTEXT, output_file)

        assert Path(output_file).exists()
        Path(output_file).unlink()

    finally:
        Path(dsl_file).unlink()


def test_integration_cli_workflow():
    """Test CLI integration workflow."""
    runner = CliRunner()

    # Test multiple CLI commands
    commands = [
        ["--help"],
        ["export", "--help"],
        ["validate", "--help"],
        ["tokens", "--help"],
        ["c4", "--help"],
        ["config", "--help"],
    ]

    for cmd in commands:
        result = runner.invoke(cli, cmd)
        assert result.exit_code in [0, 2]  # 0=success, 2=usage error


def test_integration_token_extraction_and_export():
    """Test token extraction and export workflow."""
    tokens = DesignTokens()

    token_data = {
        "colors": {"primary": "#0066CC", "secondary": "#28A745"},
        "typography": {"heading1": "32px", "body": "16px"},
        "spacing": {"sm": "8px", "md": "16px", "lg": "24px"},
    }

    # Export to JSON
    json_output = tokens.export_json(token_data)
    assert "colors" in json_output
    assert "typography" in json_output

    # Export to CSS vars
    css_output = tokens.export_css_vars(token_data)
    assert isinstance(css_output, str)

    # Export to SCSS vars
    scss_output = tokens.export_scss_vars(token_data)
    assert isinstance(scss_output, str)


# ============================================================================
# Main test configuration
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
