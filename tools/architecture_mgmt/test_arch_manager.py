"""
Test Suite for Architecture Management & Documentation Platform
Issue #40: TOOL-ARCH-001

Comprehensive tests for:
- ADR Manager
- C4 Generator
- Fitness Functions
- ASR Tracker
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from adr_manager import ADR, ADRManager
from asr_tracker import ASR, ASRExtractor, ASRTracker
from c4_generator import C4Generator, C4Model
from fitness_functions import (
    ComplexityAnalyzer,
    FitnessResult,
    FitnessRule,
    FitnessTester,
    FitnessViolation,
    NamingAnalyzer,
)


# ============================================================================
# ADR Manager Tests
# ============================================================================


class TestADRManager:
    """Test ADR Manager functionality."""

    @pytest.fixture
    def temp_adr_dir(self):
        """Create temporary ADR directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def adr_manager(self, temp_adr_dir):
        """Create ADR manager instance."""
        return ADRManager(adr_dir=temp_adr_dir)

    def test_create_adr(self, adr_manager):
        """Test creating a new ADR."""
        adr = adr_manager.create(
            title="Use Microservices Architecture",
            context="Need scalable architecture",
            decision="Adopt microservices",
            consequences="Increased complexity but better scalability",
            status="accepted",
        )

        assert adr.number == 1
        assert adr.title == "Use Microservices Architecture"
        assert adr.status == "accepted"
        assert isinstance(adr.deciders, list)

        # Check file was created
        adr_file = Path(adr_manager.adr_dir) / "ADR-001.md"
        assert adr_file.exists()

    def test_get_next_adr_number(self, adr_manager):
        """Test getting next ADR number."""
        assert adr_manager.get_next_adr_number() == 1

        # Create an ADR
        adr_manager.create(
            title="Test ADR",
            context="Context",
            decision="Decision",
            consequences="Consequences",
        )

        assert adr_manager.get_next_adr_number() == 2

    def test_read_adr(self, adr_manager):
        """Test reading an ADR."""
        # Create ADR
        original = adr_manager.create(
            title="Test ADR",
            context="Test context",
            decision="Test decision",
            consequences="Test consequences",
        )

        # Read it back
        read_adr = adr_manager.read(original.number)

        assert read_adr is not None
        assert read_adr.number == original.number
        assert read_adr.title == original.title

    def test_supersede_adr(self, adr_manager):
        """Test superseding an ADR."""
        # Create original ADR
        original = adr_manager.create(
            title="Original Decision",
            context="Original context",
            decision="Original decision",
            consequences="Original consequences",
        )

        # Supersede it
        new_adr = adr_manager.supersede(
            adr_number=original.number,
            new_title="Updated Decision",
            new_context="Updated context",
            new_decision="Updated decision",
        )

        assert new_adr.number == 2
        assert new_adr.supersedes == [original.number]

        # Check original ADR was updated
        updated_original = adr_manager.read(original.number)
        assert updated_original.status == "superseded"
        assert updated_original.superseded_by == new_adr.number

    def test_list_adrs(self, adr_manager):
        """Test listing ADRs."""
        # Create multiple ADRs
        adr_manager.create(
            title="ADR 1",
            context="Context 1",
            decision="Decision 1",
            consequences="Consequences 1",
            status="accepted",
        )

        adr_manager.create(
            title="ADR 2",
            context="Context 2",
            decision="Decision 2",
            consequences="Consequences 2",
            status="proposed",
        )

        # List all
        all_adrs = adr_manager.list_adrs()
        assert len(all_adrs) == 2

        # Filter by status
        accepted = adr_manager.list_adrs(status_filter="accepted")
        assert len(accepted) == 1
        assert accepted[0].status == "accepted"

    def test_generate_index(self, adr_manager):
        """Test generating ADR index."""
        # Create some ADRs
        adr_manager.create(
            title="ADR 1",
            context="Context",
            decision="Decision",
            consequences="Consequences",
            status="accepted",
        )

        index = adr_manager.generate_index()

        assert "Architecture Decision Records" in index
        assert "ADR-001" in index
        assert "ADR 1" in index

    def test_search_adrs(self, adr_manager):
        """Test searching ADRs."""
        adr_manager.create(
            title="Use Microservices",
            context="Need scalability",
            decision="Adopt microservices",
            consequences="More complexity",
        )

        adr_manager.create(
            title="Use PostgreSQL",
            context="Need database",
            decision="Use PostgreSQL",
            consequences="SQL constraints",
        )

        # Search by keyword
        results = adr_manager.search("microservices")
        assert len(results) == 1
        assert "Microservices" in results[0].title


# ============================================================================
# C4 Generator Tests
# ============================================================================


class TestC4Generator:
    """Test C4 Generator functionality."""

    @pytest.fixture
    def c4_generator(self):
        """Create C4 generator instance."""
        return C4Generator()

    @pytest.fixture
    def sample_model(self):
        """Create sample C4 model."""
        model = C4Model(name="Test System", description="Test system")
        model.add_person("user", "User", "A user of the system")
        model.add_software_system("system", "System", "The main system")
        model.add_relationship("user", "system", "Uses", "HTTPS")
        return model

    def test_create_c4_model(self, sample_model):
        """Test creating a C4 model."""
        assert sample_model.name == "Test System"
        assert len(sample_model.people) == 1
        assert len(sample_model.software_systems) == 1
        assert len(sample_model.relationships) == 1

    def test_generate_context_diagram(self, c4_generator, sample_model):
        """Test generating context diagram."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = c4_generator.generate_from_model(
                sample_model, tmpdir, diagram_type="context", formats=["plantuml"]
            )

            assert "plantuml" in results
            assert len(results["plantuml"]) > 0

            # Check PlantUML file was created
            puml_file = Path(results["plantuml"][0])
            assert puml_file.exists()

            # Check content
            content = puml_file.read_text()
            assert "@startuml" in content
            assert "Person(user" in content
            assert "System(system" in content

    def test_parse_yaml_model(self, c4_generator):
        """Test parsing YAML model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = Path(tmpdir) / "model.yml"
            model_data = {
                "name": "Test System",
                "description": "A test system",
                "people": [
                    {"id": "user", "name": "User", "description": "System user"}
                ],
                "systems": [
                    {"id": "app", "name": "Application", "description": "Main app"}
                ],
                "relationships": [
                    {"source": "user", "target": "app", "description": "Uses"}
                ],
            }

            with open(yaml_file, "w") as f:
                yaml.dump(model_data, f)

            model = c4_generator.parse_yaml_model(str(yaml_file))

            assert model.name == "Test System"
            assert len(model.people) == 1
            assert len(model.software_systems) == 1


# ============================================================================
# Fitness Functions Tests
# ============================================================================


class TestFitnessFunctions:
    """Test fitness functions functionality."""

    @pytest.fixture
    def sample_python_file(self):
        """Create a sample Python file for testing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write("""
class TestService:
    def complex_function(self, x):
        if x > 0:
            if x > 10:
                if x > 20:
                    if x > 30:
                        if x > 40:
                            return "very high"
                        return "high"
                    return "medium"
                return "low"
            return "very low"
        return "negative"

class InvalidClassName:
    pass

def test_function():
    pass
""")
            yield f.name
        Path(f.name).unlink()

    def test_complexity_analyzer(self, sample_python_file):
        """Test complexity analysis."""
        analyzer = ComplexityAnalyzer()
        complexities = analyzer.get_cyclomatic_complexity(Path(sample_python_file))

        assert "complex_function" in complexities
        assert complexities["complex_function"] > 1

    def test_naming_analyzer(self, sample_python_file):
        """Test naming convention analysis."""
        analyzer = NamingAnalyzer()

        # Test class naming (should end with Service)
        violations = analyzer.check_class_naming(
            Path(sample_python_file), r"^[A-Z][a-zA-Z0-9]*Service$"
        )

        # InvalidClassName should violate the pattern
        assert "InvalidClassName" in violations

    def test_fitness_rule_creation(self):
        """Test creating fitness rules."""
        rule = FitnessRule(
            name="Test Rule",
            type="complexity",
            severity="ERROR",
            parameters={"threshold": 10},
        )

        assert rule.name == "Test Rule"
        assert rule.type == "complexity"
        assert rule.enabled is True

    def test_fitness_tester_with_rules(self, sample_python_file):
        """Test fitness tester with rules."""
        # Create rules file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False
        ) as f:
            rules = {
                "rules": [
                    {
                        "name": "Cyclomatic Complexity",
                        "type": "complexity",
                        "severity": "ERROR",
                        "parameters": {"threshold": 5, "metric": "cyclomatic"},
                    }
                ]
            }
            yaml.dump(rules, f)
            rules_file = f.name

        try:
            tester = FitnessTester(rules_file=rules_file)
            assert len(tester.rules) == 1

            # Test on directory containing our sample file
            test_dir = Path(sample_python_file).parent
            result = tester.test(str(test_dir))

            assert isinstance(result, FitnessResult)
            assert result.total_rules == 1

        finally:
            Path(rules_file).unlink()

    def test_fitness_result(self):
        """Test fitness result object."""
        result = FitnessResult(total_rules=10, passed_rules=7, failed_rules=3)

        assert result.total_rules == 10
        assert result.success_rate == 70.0
        assert result.violation_count == 0

        # Add violations
        result.violations.append(
            FitnessViolation(
                rule_name="Test Rule", severity="ERROR", message="Test violation"
            )
        )

        assert result.violation_count == 1

        error_violations = result.get_violations_by_severity("ERROR")
        assert len(error_violations) == 1


# ============================================================================
# ASR Tracker Tests
# ============================================================================


class TestASRTracker:
    """Test ASR Tracker functionality."""

    @pytest.fixture
    def temp_asr_dir(self):
        """Create temporary ASR directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def asr_tracker(self, temp_asr_dir):
        """Create ASR tracker instance."""
        return ASRTracker(asr_dir=temp_asr_dir)

    def test_save_and_load_asr(self, asr_tracker):
        """Test saving and loading ASR."""
        asr = ASR(
            id="ASR-001",
            title="Performance Requirement",
            description="System must handle 10K requests per second",
            category="performance",
            priority="HIGH",
            source="Manual",
            status="identified",
        )

        asr_tracker.save_asr(asr)

        # Load it back
        loaded = asr_tracker.load_asr("ASR-001")

        assert loaded is not None
        assert loaded.id == "ASR-001"
        assert loaded.title == "Performance Requirement"
        assert loaded.category == "performance"

    def test_list_asrs(self, asr_tracker):
        """Test listing ASRs."""
        # Create multiple ASRs
        asr1 = ASR(
            id="ASR-001",
            title="Performance",
            description="Performance requirement",
            category="performance",
            priority="HIGH",
            source="Manual",
            status="identified",
        )

        asr2 = ASR(
            id="ASR-002",
            title="Security",
            description="Security requirement",
            category="security",
            priority="MEDIUM",
            source="Manual",
            status="analyzed",
        )

        asr_tracker.save_asr(asr1)
        asr_tracker.save_asr(asr2)

        # List all
        all_asrs = asr_tracker.list_asrs()
        assert len(all_asrs) == 2

        # Filter by category
        perf_asrs = asr_tracker.list_asrs(category="performance")
        assert len(perf_asrs) == 1
        assert perf_asrs[0].category == "performance"

    def test_link_asr_to_adr(self, asr_tracker):
        """Test linking ASR to ADR."""
        asr = ASR(
            id="ASR-001",
            title="Test ASR",
            description="Test description",
            category="general",
            priority="MEDIUM",
            source="Manual",
            status="identified",
        )

        asr_tracker.save_asr(asr)

        # Link to ADR
        success = asr_tracker.link_asr_to_adr("ASR-001", 5)
        assert success is True

        # Verify link
        loaded = asr_tracker.load_asr("ASR-001")
        assert 5 in loaded.related_adrs

    def test_update_status(self, asr_tracker):
        """Test updating ASR status."""
        asr = ASR(
            id="ASR-001",
            title="Test",
            description="Description",
            category="general",
            priority="LOW",
            source="Manual",
            status="identified",
        )

        asr_tracker.save_asr(asr)

        # Update status
        success = asr_tracker.update_status("ASR-001", "addressed")
        assert success is True

        # Verify update
        loaded = asr_tracker.load_asr("ASR-001")
        assert loaded.status == "addressed"

    def test_generate_traceability_matrix(self, asr_tracker):
        """Test generating traceability matrix."""
        asr = ASR(
            id="ASR-001",
            title="Test ASR",
            description="Description",
            category="performance",
            priority="HIGH",
            source="Manual",
            status="identified",
            related_adrs=[1, 2],
        )

        asr_tracker.save_asr(asr)

        matrix = asr_tracker.generate_traceability_matrix()

        assert "Traceability Matrix" in matrix
        assert "ASR-001" in matrix
        assert "ADR-001" in matrix


class TestASRExtractor:
    """Test ASR Extractor functionality."""

    @pytest.fixture
    def extractor(self):
        """Create ASR extractor instance."""
        return ASRExtractor()

    def test_is_architecturally_significant(self, extractor):
        """Test identifying architecturally significant requirements."""
        # Should be significant
        assert extractor._is_architecturally_significant(
            "Performance Requirement", "System must handle 10K requests per second"
        )

        assert extractor._is_architecturally_significant(
            "Security Enhancement", "Implement authentication and authorization"
        )

        # Should not be significant
        assert not extractor._is_architecturally_significant(
            "Fix typo", "Fix typo in documentation"
        )

    def test_categorize_requirement(self, extractor):
        """Test categorizing requirements."""
        category = extractor._categorize_requirement(
            "Performance", "System must have low latency and high throughput"
        )
        assert category == "performance"

        category = extractor._categorize_requirement(
            "Security", "Implement encryption and authentication"
        )
        assert category == "security"

    def test_extract_quality_attributes(self, extractor):
        """Test extracting quality attributes."""
        attributes = extractor._extract_quality_attributes(
            "Performance and Security", "Must be scalable and secure"
        )

        assert "performance" in attributes
        assert "security" in attributes
        assert "scalability" in attributes

    def test_extract_from_text(self, extractor):
        """Test extracting ASR from text."""
        text = "The system must handle 10,000 concurrent users with response time under 200ms"
        title = "High Performance Requirement"

        asr = extractor.extract_from_text(text, title, source="Requirements Doc")

        assert asr is not None
        assert asr.title == title
        assert asr.category == "performance"
        assert "performance" in asr.quality_attributes


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for the entire platform."""

    def test_adr_to_asr_workflow(self):
        """Test complete workflow: Create ADR and link to ASR."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adr_dir = Path(tmpdir) / "adr"
            asr_dir = Path(tmpdir) / "asr"

            # Create ADR
            adr_manager = ADRManager(adr_dir=str(adr_dir))
            adr = adr_manager.create(
                title="Use Microservices",
                context="Need scalability",
                decision="Adopt microservices",
                consequences="Better scalability",
            )

            # Create ASR
            asr_tracker = ASRTracker(asr_dir=str(asr_dir))
            asr = ASR(
                id="ASR-001",
                title="Scalability Requirement",
                description="Must scale to 10K users",
                category="scalability",
                priority="HIGH",
                source="Manual",
                status="identified",
            )
            asr_tracker.save_asr(asr)

            # Link ASR to ADR
            asr_tracker.link_asr_to_adr("ASR-001", adr.number)

            # Verify link
            loaded_asr = asr_tracker.load_asr("ASR-001")
            assert adr.number in loaded_asr.related_adrs


# ============================================================================
# Main Test Runner
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
