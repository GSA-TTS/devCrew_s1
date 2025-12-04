"""
ATT&CK Mapper module for MITRE ATT&CK framework integration.

This module provides functionality for:
- Mapping threats to MITRE ATT&CK techniques
- Analyzing tactic coverage
- Identifying detection gaps
- Generating mitigation recommendations
- Creating ATT&CK Navigator layers
"""

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from mitreattack.stix20 import MitreAttackData
from pydantic import BaseModel, Field
from stix2 import AttackPattern, Malware, ThreatActor, Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type alias for STIX objects
STIXObject = Any


class ATTACKTechnique(BaseModel):
    """Model for MITRE ATT&CK technique."""

    technique_id: str = Field(..., description="ATT&CK technique ID (e.g., T1059)")
    name: str = Field(..., description="Technique name")
    tactic: str = Field(..., description="Primary tactic name")
    description: str = Field(..., description="Technique description")
    platforms: List[str] = Field(default_factory=list, description="Affected platforms")
    data_sources: List[str] = Field(
        default_factory=list, description="Data sources for detection"
    )
    subtechniques: List[str] = Field(
        default_factory=list,
        description="List of sub-technique IDs",
    )
    url: str = Field(default="", description="ATT&CK URL")


class TacticCoverage(BaseModel):
    """Model for tactic coverage analysis."""

    total_tactics: int = Field(..., description="Total number of tactics")
    covered_tactics: int = Field(..., description="Number of covered tactics")
    coverage_percentage: float = Field(..., description="Coverage percentage")
    tactics: Dict[str, int] = Field(
        ..., description="Mapping of tactic to technique count"
    )
    uncovered_tactics: List[str] = Field(
        default_factory=list, description="List of uncovered tactics"
    )


class DetectionGap(BaseModel):
    """Model for detection gap."""

    technique_id: str = Field(..., description="ATT&CK technique ID")
    technique_name: str = Field(..., description="Technique name")
    tactic: str = Field(..., description="Associated tactic")
    threat_count: int = Field(..., description="Number of threats using this technique")
    detection_available: bool = Field(..., description="Whether detection is available")
    priority: str = Field(..., description="Priority level: HIGH, MEDIUM, LOW")
    threat_actors: List[str] = Field(
        default_factory=list, description="Associated threat actors"
    )


class Mitigation(BaseModel):
    """Model for mitigation recommendation."""

    mitigation_id: str = Field(..., description="ATT&CK mitigation ID")
    name: str = Field(..., description="Mitigation name")
    description: str = Field(..., description="Mitigation description")
    techniques: List[str] = Field(
        ...,
        description="List of technique IDs this mitigation addresses",
    )
    url: str = Field(default="", description="ATT&CK URL")


class ATTACKMapper:
    """
    MITRE ATT&CK framework mapper for threat intelligence.

    This class provides functionality to map threats to ATT&CK techniques,
    analyze coverage, identify gaps, and generate navigator layers.
    """

    # Enterprise ATT&CK tactics in kill chain order
    ENTERPRISE_TACTICS = [
        "reconnaissance",
        "resource-development",
        "initial-access",
        "execution",
        "persistence",
        "privilege-escalation",
        "defense-evasion",
        "credential-access",
        "discovery",
        "lateral-movement",
        "collection",
        "command-and-control",
        "exfiltration",
        "impact",
    ]

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize ATT&CK Mapper.

        Args:
            config: Optional configuration dictionary with keys:
                - domain: ATT&CK domain ('enterprise', 'mobile', 'ics')
                - version: ATT&CK version (default: latest)
                - cache_dir: Directory for caching ATT&CK data
        """
        self.config = config or {}
        self.domain = self.config.get("domain", "enterprise-attack")
        self.cache_dir = Path(
            self.config.get("cache_dir", "/tmp/attack_cache")  # nosec B108
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize MITRE ATT&CK data
        logger.info(f"Loading ATT&CK data for domain: {self.domain}")
        self.attack_data = MitreAttackData(self.domain)

        # Build technique and mitigation indices
        self._build_indices()

        logger.info(
            f"Loaded {len(self.techniques)} techniques and "
            f"{len(self.mitigations)} mitigations"
        )

    def _build_indices(self) -> None:
        """Build internal indices for fast lookups."""
        # Technique index: technique_id -> technique object
        self.techniques: Dict[str, Any] = {}
        # Tactic to techniques mapping
        self.tactic_to_techniques: Dict[str, List[str]] = defaultdict(list)
        # Mitigation index: mitigation_id -> mitigation object
        self.mitigations: Dict[str, Any] = {}
        # Technique to mitigations mapping
        self.technique_to_mitigations: Dict[str, List[str]] = defaultdict(list)

        # Index techniques
        for technique in self.attack_data.get_techniques():
            tech_id = self._get_attack_id(technique)
            if tech_id:
                self.techniques[tech_id] = technique

                # Map tactics to techniques
                kill_chain_phases = technique.get("kill_chain_phases", [])
                for phase in kill_chain_phases:
                    tactic = phase.get("phase_name", "")
                    if tactic:
                        self.tactic_to_techniques[tactic].append(tech_id)

        # Index mitigations
        for mitigation in self.attack_data.get_mitigations():
            mit_id = self._get_attack_id(mitigation)
            if mit_id:
                self.mitigations[mit_id] = mitigation

        # Build technique to mitigation relationships
        relationships = self.attack_data.get_relationships()
        for rel in relationships:
            if rel.get("relationship_type") == "mitigates":
                source_ref = rel.get("source_ref", "")
                target_ref = rel.get("target_ref", "")

                # Find mitigation and technique IDs
                mit_id = self._get_id_from_ref(source_ref)
                tech_id = self._get_id_from_ref(target_ref)

                if mit_id and tech_id:
                    self.technique_to_mitigations[tech_id].append(mit_id)

    def _get_attack_id(self, stix_obj: Any) -> Optional[str]:
        """
        Extract ATT&CK ID from STIX object.

        Args:
            stix_obj: STIX object

        Returns:
            ATT&CK ID (e.g., T1059) or None
        """
        external_refs = stix_obj.get("external_references", [])
        for ref in external_refs:
            if ref.get("source_name") in [
                "mitre-attack",
                "mitre-mobile-attack",
                "mitre-ics-attack",
            ]:
                return ref.get("external_id")
        return None

    def _get_id_from_ref(self, ref: str) -> Optional[str]:
        """
        Get ATT&CK ID from STIX reference.

        Args:
            ref: STIX reference string

        Returns:
            ATT&CK ID or None
        """
        # Try techniques
        for tech_id, tech in self.techniques.items():
            if tech.get("id") == ref:
                return tech_id

        # Try mitigations
        for mit_id, mit in self.mitigations.items():
            if mit.get("id") == ref:
                return mit_id

        return None

    def map_threat_to_techniques(self, threat: STIXObject) -> List[ATTACKTechnique]:
        """
        Map a threat (STIX object) to ATT&CK techniques.

        Args:
            threat: STIX threat object (Malware, ThreatActor, Tool, etc.)

        Returns:
            List of ATTACKTechnique objects
        """
        techniques = []

        # Handle different STIX object types
        if isinstance(threat, (Malware, ThreatActor, Tool)):  # noqa: E501
            # Get relationships to attack patterns
            technique_ids = self._get_techniques_from_stix(threat)

            for tech_id in technique_ids:
                if tech_id in self.techniques:
                    tech = self._build_attack_technique(tech_id)
                    if tech:
                        techniques.append(tech)

        elif isinstance(threat, AttackPattern):
            # Direct attack pattern mapping
            pattern_tech_id: Optional[str] = self._get_attack_id(threat)
            if pattern_tech_id and pattern_tech_id in self.techniques:
                tech = self._build_attack_technique(pattern_tech_id)
                if tech:
                    techniques.append(tech)

        logger.debug(f"Mapped {len(techniques)} techniques for threat")
        return techniques

    def _get_techniques_from_stix(self, stix_obj: STIXObject) -> List[str]:
        """
        Extract technique IDs from STIX object relationships.

        Args:
            stix_obj: STIX object

        Returns:
            List of technique IDs
        """
        technique_ids: List[str] = []

        # Get object ID
        obj_id = getattr(stix_obj, "id", None)
        if not obj_id:
            return technique_ids

        # Find relationships where this object uses attack patterns
        relationships = self.attack_data.get_relationships()
        for rel in relationships:
            if (
                rel.get("source_ref") == obj_id
                and rel.get("relationship_type") == "uses"
            ):
                target_ref = rel.get("target_ref", "")
                tech_id = self._get_id_from_ref(target_ref)
                if tech_id:
                    technique_ids.append(tech_id)

        return technique_ids

    def _build_attack_technique(self, technique_id: str) -> Optional[ATTACKTechnique]:
        """
        Build ATTACKTechnique model from technique ID.

        Args:
            technique_id: ATT&CK technique ID

        Returns:
            ATTACKTechnique object or None
        """
        if technique_id not in self.techniques:
            return None

        tech = self.techniques[technique_id]

        # Extract tactic (use first one if multiple)
        tactic = ""
        kill_chain_phases = tech.get("kill_chain_phases", [])
        if kill_chain_phases:
            tactic = kill_chain_phases[0].get("phase_name", "")

        # Extract platforms
        platforms = tech.get("x_mitre_platforms", [])

        # Extract data sources
        data_sources = []
        for ds in tech.get("x_mitre_data_sources", []):
            data_sources.append(ds)

        # Find subtechniques
        subtechniques = []
        for sub_id, sub_tech in self.techniques.items():
            starts_with = sub_id.startswith(f"{technique_id}.")
            if starts_with and sub_id != technique_id:
                subtechniques.append(sub_id)

        # Build URL
        url = f"https://attack.mitre.org/techniques/{technique_id}/"

        return ATTACKTechnique(
            technique_id=technique_id,
            name=tech.get("name", ""),
            tactic=tactic,
            description=tech.get("description", ""),
            platforms=platforms,
            data_sources=data_sources,
            subtechniques=subtechniques,
            url=url,
        )

    def analyze_tactic_coverage(self, threats: List[STIXObject]) -> TacticCoverage:
        """
        Analyze which tactics are covered by the given threats.

        Args:
            threats: List of STIX threat objects

        Returns:
            TacticCoverage object with analysis results
        """
        # Count techniques per tactic
        tactic_counts: Dict[str, int] = defaultdict(int)

        for threat in threats:
            techniques = self.map_threat_to_techniques(threat)
            for tech in techniques:
                if tech.tactic:
                    tactic_counts[tech.tactic] += 1

        # Identify uncovered tactics
        covered_tactics = set(tactic_counts.keys())
        all_tactics = set(self.ENTERPRISE_TACTICS)
        uncovered = list(all_tactics - covered_tactics)

        # Calculate coverage
        total_tactics = len(all_tactics)
        covered_count = len(covered_tactics)
        coverage_pct = (covered_count / total_tactics * 100) if total_tactics > 0 else 0

        return TacticCoverage(
            total_tactics=total_tactics,
            covered_tactics=covered_count,
            coverage_percentage=round(coverage_pct, 2),
            tactics=dict(tactic_counts),
            uncovered_tactics=sorted(uncovered),
        )

    def identify_detection_gaps(
        self,
        current_detections: List[str],
        threat_landscape: List[STIXObject],
    ) -> List[DetectionGap]:
        """
        Identify gaps in detection coverage.

        Args:
            current_detections: List of technique IDs with current detection
            threat_landscape: List of STIX threat objects in landscape

        Returns:
            List of DetectionGap objects sorted by priority
        """
        # Count threats per technique
        technique_threats: Dict[str, List[str]] = defaultdict(list)

        for threat in threat_landscape:
            threat_name = getattr(threat, "name", "Unknown")
            techniques = self.map_threat_to_techniques(threat)

            for tech in techniques:
                technique_threats[tech.technique_id].append(threat_name)

        # Build detection gaps
        gaps = []
        detection_set = set(current_detections)

        for tech_id, threat_names in technique_threats.items():
            if tech_id not in self.techniques:
                continue

            has_detection = tech_id in detection_set
            threat_count = len(set(threat_names))

            # Determine priority based on threat count and detection status
            if not has_detection:
                if threat_count >= 5:
                    priority = "HIGH"
                elif threat_count >= 2:
                    priority = "MEDIUM"
                else:
                    priority = "LOW"
            else:
                priority = "LOW"  # Already detected

            tech_obj: Optional[ATTACKTechnique]
            tech_obj = self._build_attack_technique(tech_id)
            if tech_obj:
                gap = DetectionGap(
                    technique_id=tech_id,
                    technique_name=tech_obj.name,
                    tactic=tech_obj.tactic,
                    threat_count=threat_count,
                    detection_available=has_detection,
                    priority=priority,
                    threat_actors=sorted(list(set(threat_names))),
                )
                gaps.append(gap)

        # Sort by priority (HIGH > MEDIUM > LOW) and threat count
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        gaps.sort(key=lambda x: (priority_order[x.priority], -x.threat_count))

        return gaps

    def get_mitigations(self, technique_id: str) -> List[Mitigation]:
        """
        Get mitigation recommendations for a technique.

        Args:
            technique_id: ATT&CK technique ID

        Returns:
            List of Mitigation objects
        """
        mitigations = []

        mitigation_ids = self.technique_to_mitigations.get(technique_id, [])

        for mit_id in mitigation_ids:
            if mit_id in self.mitigations:
                mit = self.mitigations[mit_id]

                # Find all techniques this mitigation addresses
                addressed_techniques = []
                items = self.technique_to_mitigations.items()
                for tech_id, mit_list in items:
                    if mit_id in mit_list:
                        addressed_techniques.append(tech_id)

                url = f"https://attack.mitre.org/mitigations/{mit_id}/"

                mitigation = Mitigation(
                    mitigation_id=mit_id,
                    name=mit.get("name", ""),
                    description=mit.get("description", ""),
                    techniques=addressed_techniques,
                    url=url,
                )
                mitigations.append(mitigation)

        return mitigations

    def generate_navigator_layer(
        self,
        threats: List[STIXObject],
        output_file: Optional[str] = None,
    ) -> Dict:
        """
        Generate ATT&CK Navigator layer JSON.

        Args:
            threats: List of STIX threat objects
            output_file: Optional path to save layer JSON

        Returns:
            Navigator layer dictionary
        """
        # Count technique usage
        technique_usage: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "threats": []}
        )

        for threat in threats:
            threat_name = getattr(threat, "name", "Unknown")
            techniques = self.map_threat_to_techniques(threat)

            for tech in techniques:
                technique_usage[tech.technique_id]["count"] += 1
                technique_usage[tech.technique_id]["threats"].append(threat_name)

        # Build navigator techniques
        nav_techniques = []
        for tech_id, usage in technique_usage.items():
            count = usage["count"]
            threat_list = list(set(usage["threats"]))

            # Color gradient based on usage
            if count >= 5:
                color = "#ff0000"  # Red
                score = 100
            elif count >= 3:
                color = "#ff6600"  # Orange
                score = 75
            elif count >= 2:
                color = "#ffcc00"  # Yellow
                score = 50
            else:
                color = "#99ccff"  # Light blue
                score = 25

            nav_techniques.append(
                {
                    "techniqueID": tech_id,
                    "score": score,
                    "color": color,
                    "comment": f"Used by: {', '.join(threat_list)}",
                    "enabled": True,
                    "metadata": [{"name": "threat_count", "value": str(count)}],
                }
            )

        # Build layer
        layer = {
            "name": "Threat Landscape",
            "versions": {"navigator": "4.8.2", "layer": "4.4"},
            "domain": self.domain,
            "description": (
                f"ATT&CK Navigator layer for {len(threats)} threats "
                f"covering {len(nav_techniques)} techniques"
            ),
            "techniques": nav_techniques,
            "gradient": {
                "colors": ["#ffffff", "#ff0000"],
                "minValue": 0,
                "maxValue": 100,
            },
            "legendItems": [
                {"label": "5+ threats", "color": "#ff0000"},
                {"label": "3-4 threats", "color": "#ff6600"},
                {"label": "2 threats", "color": "#ffcc00"},
                {"label": "1 threat", "color": "#99ccff"},
            ],
        }

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(layer, f, indent=2)

            logger.info(f"Saved navigator layer to {output_file}")

        return layer

    def get_technique_details(self, technique_id: str) -> Optional[Dict]:
        """
        Get detailed information about a technique.

        Args:
            technique_id: ATT&CK technique ID

        Returns:
            Dictionary with technique details or None
        """
        tech = self._build_attack_technique(technique_id)
        if not tech:
            return None

        mitigations = self.get_mitigations(technique_id)

        return {
            "technique": tech.dict(),
            "mitigations": [m.dict() for m in mitigations],
            "tactic_techniques": self.tactic_to_techniques.get(tech.tactic, []),
        }
