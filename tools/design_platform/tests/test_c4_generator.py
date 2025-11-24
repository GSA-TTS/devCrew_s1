"""
Unit tests for C4 Generator.

Tests all major functionality including:
- DSL parsing and validation
- Model creation
- PlantUML generation
- Theme application
- Diagram rendering
"""

import tempfile
from pathlib import Path

import pytest

from c4_generator import (
    C4Component,
    C4Container,
    C4Diagram,
    C4Generator,
    C4Model,
    C4Person,
    C4Relationship,
    C4SoftwareSystem,
    C4View,
    C4Workspace,
    DiagramType,
)


class TestC4Models:
    """Test Pydantic models for C4 elements."""

    def test_c4_person_creation(self):
        """Test creating a C4 person."""
        person = C4Person(
            id="user",
            name="End User",
            description="System user",
            tags=["external"],
            external=True,
        )

        assert person.id == "user"
        assert person.name == "End User"
        assert person.description == "System user"
        assert person.external is True
        assert "external" in person.tags

    def test_c4_person_id_validation(self):
        """Test that invalid IDs are rejected."""
        with pytest.raises(ValueError, match="Invalid ID"):
            C4Person(id="123invalid", name="User", description="")

        with pytest.raises(ValueError, match="Invalid ID"):
            C4Person(id="user-name", name="User", description="")

    def test_c4_component_creation(self):
        """Test creating a C4 component."""
        component = C4Component(
            id="auth_component",
            name="Authentication",
            description="Handles auth",
            technology="JWT",
            tags=["security"],
        )

        assert component.id == "auth_component"
        assert component.name == "Authentication"
        assert component.technology == "JWT"

    def test_c4_container_creation(self):
        """Test creating a C4 container with components."""
        component = C4Component(
            id="controller", name="Controller", description="API controller"
        )

        container = C4Container(
            id="api",
            name="API Server",
            description="Backend API",
            technology="FastAPI",
            components=[component],
        )

        assert container.id == "api"
        assert len(container.components) == 1
        assert container.components[0].id == "controller"

    def test_c4_software_system_creation(self):
        """Test creating a C4 software system."""
        container = C4Container(id="web", name="Web App", description="Frontend")

        system = C4SoftwareSystem(
            id="ecommerce",
            name="E-Commerce",
            description="Main system",
            containers=[container],
            external=False,
        )

        assert system.id == "ecommerce"
        assert len(system.containers) == 1
        assert system.external is False

    def test_c4_relationship_creation(self):
        """Test creating relationships."""
        rel = C4Relationship(
            source_id="user",
            target_id="webapp",
            description="Uses",
            technology="HTTPS",
            tags=["async"],
        )

        assert rel.source_id == "user"
        assert rel.target_id == "webapp"
        assert rel.technology == "HTTPS"

    def test_c4_model_get_element(self):
        """Test finding elements by ID."""
        person = C4Person(id="user", name="User", description="")
        system = C4SoftwareSystem(id="sys", name="System", description="")

        model = C4Model(people=[person], software_systems=[system])

        assert model.get_element_by_id("user") == person
        assert model.get_element_by_id("sys") == system
        assert model.get_element_by_id("nonexistent") is None


class TestC4Generator:
    """Test C4Generator functionality."""

    @pytest.fixture
    def generator(self):
        """Create a C4Generator instance."""
        return C4Generator()

    @pytest.fixture
    def sample_dsl(self):
        """Provide sample DSL content."""
        return '''
workspace "Test System" {
    name "Test System"
    description "A test system"

    model {
        user = person "User" "End user"

        system = softwareSystem "Main System" "Core system" {
            webapp = container "Web App" "Frontend" "React"
        }

        user -> webapp : "Uses" "HTTPS"
    }

    views {
        systemContext system "Context View" {}
    }
}
        '''

    def test_generator_initialization(self, generator):
        """Test that generator initializes with default theme."""
        assert generator is not None
        assert "person" in generator.default_theme
        assert "system" in generator.default_theme
        assert "container" in generator.default_theme
        assert "component" in generator.default_theme

    def test_validate_dsl_valid(self, generator, sample_dsl):
        """Test DSL validation with valid input."""
        is_valid, error = generator.validate_dsl(sample_dsl)
        assert is_valid is True
        assert error is None

    def test_validate_dsl_invalid(self, generator):
        """Test DSL validation with invalid input."""
        invalid_dsl = "workspace { invalid syntax"
        is_valid, error = generator.validate_dsl(invalid_dsl)
        assert is_valid is False
        assert error is not None

    def test_parse_dsl_file(self, generator, sample_dsl):
        """Test parsing DSL from file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".dsl", delete=False
        ) as f:
            f.write(sample_dsl)
            temp_path = f.name

        try:
            workspace = generator.parse_dsl(temp_path)

            assert isinstance(workspace, C4Workspace)
            assert workspace.name == "Test System"
            assert workspace.description == "A test system"
            assert len(workspace.model.people) == 1
            assert len(workspace.model.software_systems) == 1
            assert len(workspace.model.relationships) == 1
            assert len(workspace.views) == 1

        finally:
            Path(temp_path).unlink()

    def test_parse_dsl_file_not_found(self, generator):
        """Test parsing non-existent file."""
        with pytest.raises(FileNotFoundError):
            generator.parse_dsl("/nonexistent/file.dsl")

    def test_generate_plantuml_system_context(self, generator, sample_dsl):
        """Test PlantUML generation for system context."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".dsl", delete=False
        ) as f:
            f.write(sample_dsl)
            temp_path = f.name

        try:
            workspace = generator.parse_dsl(temp_path)
            plantuml = generator.generate_plantuml(
                workspace, DiagramType.SYSTEM_CONTEXT
            )

            assert "@startuml" in plantuml
            assert "@enduml" in plantuml
            assert "Person(user" in plantuml
            assert "System(system" in plantuml
            assert "Rel(" in plantuml

        finally:
            Path(temp_path).unlink()

    def test_generate_plantuml_container(self, generator, sample_dsl):
        """Test PlantUML generation for container view."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".dsl", delete=False
        ) as f:
            f.write(sample_dsl)
            temp_path = f.name

        try:
            workspace = generator.parse_dsl(temp_path)
            plantuml = generator.generate_plantuml(
                workspace, DiagramType.CONTAINER
            )

            assert "@startuml" in plantuml
            assert "C4_Container.puml" in plantuml
            assert "Container(webapp" in plantuml

        finally:
            Path(temp_path).unlink()

    def test_apply_design_system(self, generator):
        """Test applying custom theme."""
        workspace = C4Workspace(
            name="Test",
            description="Test workspace",
            model=C4Model(),
            views=[],
        )

        custom_theme = {
            "person": {"fill": "#FF0000", "stroke": "#CC0000", "text": "#FFF"},
            "system": {"fill": "#00FF00", "stroke": "#00CC00", "text": "#000"},
        }

        applied_theme = generator.apply_design_system(workspace, custom_theme)

        # Should merge with defaults
        assert applied_theme["person"]["fill"] == "#FF0000"
        assert applied_theme["system"]["fill"] == "#00FF00"
        # Defaults should still be present
        assert "container" in applied_theme
        assert "component" in applied_theme

    def test_build_diagram_system_context(self, generator, sample_dsl):
        """Test building system context diagram."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".dsl", delete=False
        ) as f:
            f.write(sample_dsl)
            temp_path = f.name

        try:
            workspace = generator.parse_dsl(temp_path)
            view = workspace.views[0]

            diagram = generator._build_diagram(workspace, view)

            assert isinstance(diagram, C4Diagram)
            assert diagram.type == DiagramType.SYSTEM_CONTEXT
            assert len(diagram.elements) > 0
            assert len(diagram.relationships) > 0

        finally:
            Path(temp_path).unlink()


class TestDiagramType:
    """Test DiagramType enum."""

    def test_diagram_types(self):
        """Test that all diagram types are defined."""
        assert DiagramType.SYSTEM_CONTEXT == "SystemContext"
        assert DiagramType.CONTAINER == "Container"
        assert DiagramType.COMPONENT == "Component"
        assert DiagramType.CODE == "Code"


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow(self):
        """Test complete workflow from DSL to PlantUML."""
        dsl_content = '''
workspace "E-Commerce" {
    name "E-Commerce Platform"
    description "Online retail system"

    model {
        customer = person "Customer" "Buys products"
        admin = person "Admin" "Manages system"

        ecommerce = softwareSystem "E-Commerce System" "Main platform" {
            webapp = container "Web App" "Frontend" "React" {
                catalog = component "Catalog" "Product display" "React"
                cart = component "Cart" "Shopping cart" "Redux"
            }

            api = container "API" "Backend" "FastAPI"
            db = container "Database" "Data store" "PostgreSQL"
        }

        payment = softwareSystem "Payment Gateway" "External payment"

        customer -> webapp : "Uses" "HTTPS"
        admin -> webapp : "Manages" "HTTPS"
        webapp -> api : "Calls" "REST"
        api -> db : "Reads/Writes" "SQL"
        api -> payment : "Processes payment" "HTTPS"

        catalog -> api : "Fetches products" "REST"
        cart -> api : "Creates order" "REST"
    }

    views {
        systemContext ecommerce "System Context" {}
        container ecommerce "Container View" {}
        component webapp "Component View" {}
    }
}
        '''

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".dsl", delete=False
        ) as f:
            f.write(dsl_content)
            temp_path = f.name

        try:
            generator = C4Generator()

            # Validate
            is_valid, error = generator.validate_dsl(dsl_content)
            assert is_valid, f"DSL validation failed: {error}"

            # Parse
            workspace = generator.parse_dsl(temp_path)
            assert workspace.name == "E-Commerce Platform"
            assert len(workspace.model.people) == 2
            assert len(workspace.model.software_systems) == 2
            assert len(workspace.views) == 3

            # Generate PlantUML for all view types
            for view_type in [
                DiagramType.SYSTEM_CONTEXT,
                DiagramType.CONTAINER,
                DiagramType.COMPONENT,
            ]:
                plantuml = generator.generate_plantuml(workspace, view_type)
                assert "@startuml" in plantuml
                assert "@enduml" in plantuml
                assert len(plantuml.splitlines()) > 10

            # Apply theme
            custom_theme = {"person": {"fill": "#123456"}}
            themed = generator.apply_design_system(workspace, custom_theme)
            assert themed["person"]["fill"] == "#123456"

        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
