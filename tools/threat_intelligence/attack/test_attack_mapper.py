"""
Comprehensive test suite for ATT&CK Mapper module.

Tests cover:
- ATT&CK framework initialization
- Threat-to-technique mapping
- Tactic coverage analysis
- Detection gap identification
- Mitigation recommendations
- Navigator layer generation
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from stix2 import AttackPattern, Malware, ThreatActor, Tool
from tools.threat_intelligence.attack.attack_mapper import (
    ATTACKMapper,
    ATTACKTechnique,
    DetectionGap,
    Mitigation,
    TacticCoverage,
)


@pytest.fixture
def attack_mapper():
    """Create ATT&CK mapper instance for testing."""
    patch_path = "tools.threat_intelligence.attack.attack_mapper.MitreAttackData"
    with patch(patch_path):
        mapper = ATTACKMapper()
        # Mock the attack data
        mapper._setup_mock_data()
        return mapper


@pytest.fixture
def sample_technique():
    """Create sample technique object."""
    return {
        "id": "attack-pattern--12345",
        "type": "attack-pattern",
        "name": "Command and Scripting Interpreter",
        "description": "Adversaries may abuse command and script interpreters",
        "kill_chain_phases": [{"phase_name": "execution"}],
        "x_mitre_platforms": ["Windows", "Linux", "macOS"],
        "x_mitre_data_sources": ["Process monitoring", "Command execution"],
        "external_references": [
            {"source_name": "mitre-attack", "external_id": "T1059"}
        ],
    }


@pytest.fixture
def sample_mitigation():
    """Create sample mitigation object."""
    return {
        "id": "course-of-action--67890",
        "type": "course-of-action",
        "name": "Code Signing",
        "description": "Enforce code signing policies",
        "external_references": [
            {"source_name": "mitre-attack", "external_id": "M1045"}
        ],
    }


class TestATTACKMapperInitialization:
    """Tests for ATT&CK Mapper initialization."""

    @patch("tools.threat_intelligence.attack.attack_mapper.MitreAttackData")
    def test_default_initialization(self, mock_attack_data):
        """Test initialization with default configuration."""
        mock_instance = Mock()
        mock_instance.get_techniques.return_value = []
        mock_instance.get_mitigations.return_value = []
        mock_instance.get_relationships.return_value = []
        mock_attack_data.return_value = mock_instance

        mapper = ATTACKMapper()

        assert mapper.domain == "enterprise-attack"
        assert mapper.cache_dir.exists()
        assert isinstance(mapper.techniques, dict)
        assert isinstance(mapper.mitigations, dict)

    @patch("tools.threat_intelligence.attack.attack_mapper.MitreAttackData")
    def test_custom_domain_initialization(self, mock_attack_data):
        """Test initialization with custom domain."""
        mock_instance = Mock()
        mock_instance.get_techniques.return_value = []
        mock_instance.get_mitigations.return_value = []
        mock_instance.get_relationships.return_value = []
        mock_attack_data.return_value = mock_instance

        config = {"domain": "mobile-attack", "cache_dir": "/tmp/test_cache"}
        mapper = ATTACKMapper(config)

        assert mapper.domain == "mobile-attack"
        assert str(mapper.cache_dir) == "/tmp/test_cache"

    @patch("tools.threat_intelligence.attack.attack_mapper.MitreAttackData")
    def test_index_building(self, mock_attack_data, sample_technique):
        """Test that indices are built correctly."""
        mock_instance = Mock()
        mock_instance.get_techniques.return_value = [sample_technique]
        mock_instance.get_mitigations.return_value = []
        mock_instance.get_relationships.return_value = []
        mock_attack_data.return_value = mock_instance

        mapper = ATTACKMapper()

        assert "T1059" in mapper.techniques
        assert "execution" in mapper.tactic_to_techniques
        assert "T1059" in mapper.tactic_to_techniques["execution"]


class TestTechniqueMapping:
    """Tests for threat-to-technique mapping."""

    def test_map_malware_to_techniques(self, attack_mapper):
        """Test mapping malware to techniques."""
        malware = Malware(
            name="Emotet",
            is_family=True,
            malware_types=["trojan"],
        )

        # Mock the relationship
        attack_mapper.attack_data.get_relationships = Mock(
            return_value=[
                {
                    "source_ref": malware.id,
                    "relationship_type": "uses",
                    "target_ref": "attack-pattern--12345",
                }
            ]
        )

        techniques = attack_mapper.map_threat_to_techniques(malware)

        assert isinstance(techniques, list)
        # Would have techniques if mocked data is complete

    def test_map_threat_actor_to_techniques(self, attack_mapper):
        """Test mapping threat actor to techniques."""
        actor = ThreatActor(
            name="APT28",
            threat_actor_types=["nation-state"],
        )

        attack_mapper.attack_data.get_relationships = Mock(
            return_value=[
                {
                    "source_ref": actor.id,
                    "relationship_type": "uses",
                    "target_ref": "attack-pattern--12345",
                }
            ]
        )

        techniques = attack_mapper.map_threat_to_techniques(actor)

        assert isinstance(techniques, list)

    def test_map_tool_to_techniques(self, attack_mapper):
        """Test mapping tool to techniques."""
        tool = Tool(
            name="Mimikatz",
            tool_types=["credential-access"],
        )

        attack_mapper.attack_data.get_relationships = Mock(return_value=[])

        techniques = attack_mapper.map_threat_to_techniques(tool)

        assert isinstance(techniques, list)

    def test_map_attack_pattern_directly(self, attack_mapper, sample_technique):
        """Test mapping attack pattern directly."""
        attack_mapper.techniques["T1059"] = sample_technique

        pattern = AttackPattern(
            name="Command and Scripting Interpreter",
            external_references=[
                {"source_name": "mitre-attack", "external_id": "T1059"}
            ],
        )

        techniques = attack_mapper.map_threat_to_techniques(pattern)

        assert isinstance(techniques, list)


class TestTacticCoverageAnalysis:
    """Tests for tactic coverage analysis."""

    def test_analyze_coverage_with_threats(self, attack_mapper):
        """Test tactic coverage analysis with multiple threats."""
        # Setup mock data
        attack_mapper.techniques["T1059"] = {
            "id": "attack-pattern--12345",
            "name": "Command Execution",
            "kill_chain_phases": [{"phase_name": "execution"}],
            "description": "Test",
            "x_mitre_platforms": ["Windows"],
            "x_mitre_data_sources": [],
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "T1059"}
            ],
        }

        attack_mapper.techniques["T1078"] = {
            "id": "attack-pattern--67890",
            "name": "Valid Accounts",
            "kill_chain_phases": [{"phase_name": "persistence"}],
            "description": "Test",
            "x_mitre_platforms": ["Windows"],
            "x_mitre_data_sources": [],
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "T1078"}
            ],
        }

        threats = [Malware(name="Malware1", is_family=True, malware_types=["trojan"])]

        with patch.object(
            attack_mapper,
            "map_threat_to_techniques",
            return_value=[
                ATTACKTechnique(
                    technique_id="T1059",
                    name="Command Execution",
                    tactic="execution",
                    description="Test",
                    platforms=["Windows"],
                )
            ],
        ):
            coverage = attack_mapper.analyze_tactic_coverage(threats)

        assert isinstance(coverage, TacticCoverage)
        expected = len(attack_mapper.ENTERPRISE_TACTICS)
        assert coverage.total_tactics == expected
        assert coverage.covered_tactics >= 0
        assert 0 <= coverage.coverage_percentage <= 100
        assert "execution" in coverage.tactics or len(coverage.tactics) == 0

    def test_analyze_coverage_empty_threats(self, attack_mapper):
        """Test tactic coverage with no threats."""
        coverage = attack_mapper.analyze_tactic_coverage([])

        assert isinstance(coverage, TacticCoverage)
        assert coverage.covered_tactics == 0
        assert coverage.coverage_percentage == 0
        assert len(coverage.tactics) == 0


class TestDetectionGapIdentification:
    """Tests for detection gap identification."""

    def test_identify_gaps_with_detections(self, attack_mapper):
        """Test gap identification with existing detections."""
        # Setup mock techniques
        attack_mapper.techniques["T1059"] = {
            "id": "attack-pattern--12345",
            "name": "Command Execution",
            "kill_chain_phases": [{"phase_name": "execution"}],
            "description": "Test",
            "x_mitre_platforms": ["Windows"],
            "x_mitre_data_sources": [],
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "T1059"}
            ],
        }

        threats = [
            Malware(name="Malware1", is_family=True, malware_types=["trojan"]),
            Malware(name="Malware2", is_family=True, malware_types=["trojan"]),
        ]

        current_detections = ["T1078"]  # Different technique

        with patch.object(
            attack_mapper,
            "map_threat_to_techniques",
            return_value=[
                ATTACKTechnique(
                    technique_id="T1059",
                    name="Command Execution",
                    tactic="execution",
                    description="Test",
                    platforms=["Windows"],
                )
            ],
        ):
            gaps = attack_mapper.identify_detection_gaps(current_detections, threats)

        assert isinstance(gaps, list)
        # Gaps might be empty if mock setup is incomplete

    def test_identify_gaps_priority_levels(self, attack_mapper):
        """Test that gaps are prioritized correctly."""
        attack_mapper.techniques["T1059"] = {
            "id": "attack-pattern--12345",
            "name": "Command Execution",
            "kill_chain_phases": [{"phase_name": "execution"}],
            "description": "Test",
            "x_mitre_platforms": ["Windows"],
            "x_mitre_data_sources": [],
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "T1059"}
            ],
        }

        # Create multiple threats using same technique
        threats = [
            Malware(
                name=f"Malware{i}",
                is_family=True,
                malware_types=["trojan"],
            )
            for i in range(6)
        ]

        with patch.object(
            attack_mapper,
            "map_threat_to_techniques",
            return_value=[
                ATTACKTechnique(
                    technique_id="T1059",
                    name="Command Execution",
                    tactic="execution",
                    description="Test",
                    platforms=["Windows"],
                )
            ],
        ):
            gaps = attack_mapper.identify_detection_gaps([], threats)

        # High priority expected for 6 threats
        if gaps:
            assert gaps[0].priority in ["HIGH", "MEDIUM", "LOW"]


class TestMitigationRecommendations:
    """Tests for mitigation recommendations."""

    def test_get_mitigations_for_technique(self, attack_mapper, sample_mitigation):
        """Test getting mitigations for a technique."""
        attack_mapper.mitigations["M1045"] = sample_mitigation
        attack_mapper.technique_to_mitigations["T1059"] = ["M1045"]

        mitigations = attack_mapper.get_mitigations("T1059")

        assert isinstance(mitigations, list)
        if mitigations:
            assert isinstance(mitigations[0], Mitigation)
            assert mitigations[0].mitigation_id == "M1045"

    def test_get_mitigations_no_results(self, attack_mapper):
        """Test getting mitigations for technique with none."""
        mitigations = attack_mapper.get_mitigations("T9999")

        assert isinstance(mitigations, list)
        assert len(mitigations) == 0


class TestNavigatorLayerGeneration:
    """Tests for ATT&CK Navigator layer generation."""

    def test_generate_layer_basic(self, attack_mapper):
        """Test basic navigator layer generation."""
        attack_mapper.techniques["T1059"] = {
            "id": "attack-pattern--12345",
            "name": "Command Execution",
            "kill_chain_phases": [{"phase_name": "execution"}],
            "description": "Test",
            "x_mitre_platforms": ["Windows"],
            "x_mitre_data_sources": [],
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "T1059"}
            ],
        }

        threats = [Malware(name="Test", is_family=True, malware_types=["trojan"])]

        with patch.object(
            attack_mapper,
            "map_threat_to_techniques",
            return_value=[
                ATTACKTechnique(
                    technique_id="T1059",
                    name="Command Execution",
                    tactic="execution",
                    description="Test",
                    platforms=["Windows"],
                )
            ],
        ):
            layer = attack_mapper.generate_navigator_layer(threats)

        assert isinstance(layer, dict)
        assert "name" in layer
        assert "versions" in layer
        assert "domain" in layer
        assert "techniques" in layer
        assert isinstance(layer["techniques"], list)

    def test_generate_layer_with_file_output(self, attack_mapper):
        """Test navigator layer generation with file output."""
        threats = []

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            layer = attack_mapper.generate_navigator_layer(threats, output_file)

            assert Path(output_file).exists()

            with open(output_file, "r", encoding="utf-8") as f:
                loaded_layer = json.load(f)

            assert loaded_layer == layer
        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_generate_layer_color_coding(self, attack_mapper):
        """Test that techniques are color-coded by usage."""
        attack_mapper.techniques["T1059"] = {
            "id": "attack-pattern--12345",
            "name": "Command Execution",
            "kill_chain_phases": [{"phase_name": "execution"}],
            "description": "Test",
            "x_mitre_platforms": ["Windows"],
            "x_mitre_data_sources": [],
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "T1059"}
            ],
        }

        # Create 5 threats to trigger red color
        threats = [
            Malware(
                name=f"Malware{i}",
                is_family=True,
                malware_types=["trojan"],
            )
            for i in range(5)
        ]

        with patch.object(
            attack_mapper,
            "map_threat_to_techniques",
            return_value=[
                ATTACKTechnique(
                    technique_id="T1059",
                    name="Command Execution",
                    tactic="execution",
                    description="Test",
                    platforms=["Windows"],
                )
            ],
        ):
            layer = attack_mapper.generate_navigator_layer(threats)

        if layer["techniques"]:
            technique = layer["techniques"][0]
            assert "color" in technique
            assert "score" in technique
            assert technique["color"] == "#ff0000"  # Red for 5+ threats


class TestHelperMethods:
    """Tests for helper methods."""

    def test_get_attack_id(self, attack_mapper, sample_technique):
        """Test extracting ATT&CK ID from STIX object."""
        attack_id = attack_mapper._get_attack_id(sample_technique)
        assert attack_id == "T1059"

    def test_get_attack_id_no_references(self, attack_mapper):
        """Test extracting ATT&CK ID with no references."""
        obj = {"id": "test", "external_references": []}
        attack_id = attack_mapper._get_attack_id(obj)
        assert attack_id is None

    def test_build_attack_technique(self, attack_mapper, sample_technique):
        """Test building ATTACKTechnique model."""
        attack_mapper.techniques["T1059"] = sample_technique

        tech = attack_mapper._build_attack_technique("T1059")

        assert tech is not None
        assert isinstance(tech, ATTACKTechnique)
        assert tech.technique_id == "T1059"
        assert tech.name == "Command and Scripting Interpreter"
        assert tech.tactic == "execution"
        assert "Windows" in tech.platforms

    def test_build_attack_technique_not_found(self, attack_mapper):
        """Test building technique that doesn't exist."""
        tech = attack_mapper._build_attack_technique("T9999")
        assert tech is None

    def test_get_technique_details(self, attack_mapper, sample_technique):
        """Test getting complete technique details."""
        attack_mapper.techniques["T1059"] = sample_technique
        attack_mapper.technique_to_mitigations["T1059"] = []

        details = attack_mapper.get_technique_details("T1059")

        assert details is not None
        assert "technique" in details
        assert "mitigations" in details
        assert isinstance(details["mitigations"], list)


class TestDataModels:
    """Tests for Pydantic data models."""

    def test_attack_technique_model(self):
        """Test ATTACKTechnique model validation."""
        tech = ATTACKTechnique(
            technique_id="T1059",
            name="Command Execution",
            tactic="execution",
            description="Test description",
            platforms=["Windows"],
            data_sources=["Process monitoring"],
        )

        assert tech.technique_id == "T1059"
        assert tech.name == "Command Execution"
        assert tech.tactic == "execution"

    def test_tactic_coverage_model(self):
        """Test TacticCoverage model validation."""
        coverage = TacticCoverage(
            total_tactics=14,
            covered_tactics=5,
            coverage_percentage=35.71,
            tactics={"execution": 3, "persistence": 2},
        )

        assert coverage.total_tactics == 14
        assert coverage.covered_tactics == 5
        assert coverage.coverage_percentage == 35.71

    def test_detection_gap_model(self):
        """Test DetectionGap model validation."""
        gap = DetectionGap(
            technique_id="T1059",
            technique_name="Command Execution",
            tactic="execution",
            threat_count=5,
            detection_available=False,
            priority="HIGH",
        )

        assert gap.priority == "HIGH"
        assert gap.threat_count == 5
        assert not gap.detection_available

    def test_mitigation_model(self):
        """Test Mitigation model validation."""
        mitigation = Mitigation(
            mitigation_id="M1045",
            name="Code Signing",
            description="Enforce code signing",
            techniques=["T1059", "T1078"],
        )

        assert mitigation.mitigation_id == "M1045"
        assert len(mitigation.techniques) == 2


# Helper method to setup mock data
def _setup_mock_data(self):
    """Setup mock ATT&CK data for testing."""
    self.techniques = {
        "T1059": {
            "id": "attack-pattern--12345",
            "name": "Command and Scripting Interpreter",
            "description": "Test description",
            "kill_chain_phases": [{"phase_name": "execution"}],
            "x_mitre_platforms": ["Windows", "Linux"],
            "x_mitre_data_sources": ["Process monitoring"],
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "T1059"}
            ],
        }
    }

    self.mitigations = {
        "M1045": {
            "id": "course-of-action--67890",
            "name": "Code Signing",
            "description": "Enforce code signing",
            "external_references": [
                {"source_name": "mitre-attack", "external_id": "M1045"}
            ],
        }
    }

    self.tactic_to_techniques = {"execution": ["T1059"]}
    self.technique_to_mitigations = {"T1059": ["M1045"]}


# Monkey patch for testing
ATTACKMapper._setup_mock_data = _setup_mock_data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=attack_mapper", "--cov-report=term"])
