"""Tests for VEX generator module.

Tests cover:
- OpenVEX document generation
- CSAF 2.0 document generation
- Exploitability assessment
- Remediation tracking
- VEX document validation
- VEX document chaining
- Human-readable summaries
"""

import json
from datetime import datetime, timedelta

import pytest
from tools.threat_intelligence.vex.vex_generator import (
    CVE,
    ExploitabilityAssessment,
    OpenVEXDocument,
    RemediationStatus,
    VEXGenerator,
    VEXStatement,
)


class TestVEXStatement:
    """Test VEXStatement model."""

    def test_valid_statement(self):
        """Test creating valid VEX statement."""
        stmt = VEXStatement(
            vulnerability="CVE-2024-1234",
            products=["pkg:pypi/requests@2.31.0"],
            status="not_affected",
            justification="vulnerable_code_not_present",
        )
        assert stmt.vulnerability == "CVE-2024-1234"
        assert stmt.status == "not_affected"
        assert len(stmt.products) == 1

    def test_invalid_status(self):
        """Test invalid status raises error."""
        with pytest.raises(ValueError, match="Status must be one of"):
            VEXStatement(
                vulnerability="CVE-2024-1234",
                products=["pkg:pypi/requests@2.31.0"],
                status="invalid_status",
            )

    def test_invalid_justification(self):
        """Test invalid justification raises error."""
        with pytest.raises(ValueError, match="Justification must be one of"):
            VEXStatement(
                vulnerability="CVE-2024-1234",
                products=["pkg:pypi/requests@2.31.0"],
                status="not_affected",
                justification="invalid_justification",
            )

    def test_invalid_purl(self):
        """Test invalid purl raises error."""
        with pytest.raises(ValueError, match="Invalid purl"):
            VEXStatement(
                vulnerability="CVE-2024-1234",
                products=["not-a-valid-purl"],
                status="affected",
            )

    def test_multiple_products(self):
        """Test statement with multiple products."""
        stmt = VEXStatement(
            vulnerability="CVE-2024-1234",
            products=[
                "pkg:pypi/requests@2.31.0",
                "pkg:npm/axios@1.6.0",
            ],
            status="affected",
        )
        assert len(stmt.products) == 2


class TestOpenVEXDocument:
    """Test OpenVEXDocument model."""

    def test_default_document(self):
        """Test creating document with defaults."""
        doc = OpenVEXDocument()
        assert doc.author == "devCrew_s1"
        assert doc.version == 1
        assert doc.context == "https://openvex.dev/ns/v0.2.0"
        assert len(doc.statements) == 0

    def test_document_with_statements(self):
        """Test document with statements."""
        stmt = VEXStatement(
            vulnerability="CVE-2024-1234",
            products=["pkg:pypi/requests@2.31.0"],
            status="fixed",
        )
        doc = OpenVEXDocument(statements=[stmt])
        assert len(doc.statements) == 1
        assert doc.statements[0].vulnerability == "CVE-2024-1234"

    def test_document_serialization(self):
        """Test document serializes correctly."""
        stmt = VEXStatement(
            vulnerability="CVE-2024-1234",
            products=["pkg:pypi/requests@2.31.0"],
            status="not_affected",
        )
        doc = OpenVEXDocument(statements=[stmt])
        json_data = json.loads(doc.json(by_alias=True))
        assert "@context" in json_data
        assert "@id" in json_data
        assert "statements" in json_data


class TestExploitabilityAssessment:
    """Test ExploitabilityAssessment model."""

    def test_valid_assessment(self):
        """Test creating valid assessment."""
        assessment = ExploitabilityAssessment(
            cve_id="CVE-2024-1234",
            exploitable=True,
            exploit_available=True,
            exploit_maturity="functional",
            active_exploitation=False,
            confidence=0.85,
        )
        assert assessment.cve_id == "CVE-2024-1234"
        assert assessment.exploitable is True
        assert assessment.confidence == 0.85

    def test_invalid_maturity(self):
        """Test invalid maturity raises error."""
        with pytest.raises(ValueError, match="Exploit maturity must be"):
            ExploitabilityAssessment(
                cve_id="CVE-2024-1234",
                exploitable=True,
                exploit_available=False,
                exploit_maturity="invalid",
                active_exploitation=False,
                confidence=0.5,
            )

    def test_confidence_bounds(self):
        """Test confidence is bounded 0-1."""
        with pytest.raises(ValueError):
            ExploitabilityAssessment(
                cve_id="CVE-2024-1234",
                exploitable=True,
                exploit_available=False,
                exploit_maturity="poc",
                active_exploitation=False,
                confidence=1.5,
            )


class TestRemediationStatus:
    """Test RemediationStatus model."""

    def test_valid_status(self):
        """Test creating valid remediation status."""
        status = RemediationStatus(
            cve_id="CVE-2024-1234",
            status="patch_available",
            patch_available=True,
            patch_version="2.31.1",
            workaround_available=False,
        )
        assert status.cve_id == "CVE-2024-1234"
        assert status.status == "patch_available"
        assert status.patch_version == "2.31.1"

    def test_invalid_status(self):
        """Test invalid status raises error."""
        with pytest.raises(ValueError, match="Status must be one of"):
            RemediationStatus(
                cve_id="CVE-2024-1234",
                status="invalid_status",
                patch_available=False,
                workaround_available=False,
            )

    def test_with_workaround(self):
        """Test status with workaround."""
        status = RemediationStatus(
            cve_id="CVE-2024-1234",
            status="workaround_available",
            patch_available=False,
            workaround_available=True,
            workaround_description="Disable affected feature",
        )
        assert status.workaround_available is True
        assert "Disable" in status.workaround_description


class TestVEXGenerator:
    """Test VEXGenerator class."""

    @pytest.fixture
    def generator(self) -> VEXGenerator:
        """Create VEX generator for testing."""
        return VEXGenerator(
            config={
                "author": "Test Author",
                "base_url": "https://test.example.com",
                "organization": "Test Org",
            }
        )

    def test_initialization(self, generator: VEXGenerator):
        """Test generator initialization."""
        assert generator.author == "Test Author"
        assert generator.base_url == "https://test.example.com"
        assert generator.organization == "Test Org"

    def test_default_initialization(self):
        """Test generator with default config."""
        gen = VEXGenerator()
        assert gen.author == "devCrew_s1"
        assert gen.base_url == "https://example.com"

    def test_generate_openvex_not_affected(self, generator: VEXGenerator):
        """Test generating OpenVEX document for not affected product."""
        doc = generator.generate_openvex(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/requests@2.31.0",
            status="not_affected",
            justification="vulnerable_code_not_present",
        )

        assert doc["@context"] == "https://openvex.dev/ns/v0.2.0"
        assert doc["author"] == "Test Author"
        assert len(doc["statements"]) == 1
        assert doc["statements"][0]["vulnerability"] == "CVE-2024-1234"
        assert doc["statements"][0]["status"] == "not_affected"
        assert doc["statements"][0]["justification"] == "vulnerable_code_not_present"

    def test_generate_openvex_affected(self, generator: VEXGenerator):
        """Test generating OpenVEX document for affected product."""
        doc = generator.generate_openvex(
            cve_id="CVE-2024-5678",
            product="pkg:npm/lodash@4.17.20",
            status="affected",
            impact_statement="Prototype pollution vulnerability",
            action_statement="Upgrade to version 4.17.21",
        )

        assert doc["statements"][0]["status"] == "affected"
        assert "Prototype" in doc["statements"][0]["impact_statement"]
        assert "Upgrade" in doc["statements"][0]["action_statement"]

    def test_generate_openvex_fixed(self, generator: VEXGenerator):
        """Test generating OpenVEX document for fixed vulnerability."""
        doc = generator.generate_openvex(
            cve_id="CVE-2024-9999",
            product="pkg:maven/org.apache.commons/commons-text@1.9",
            status="fixed",
        )

        assert doc["statements"][0]["status"] == "fixed"

    def test_generate_csaf_basic(self, generator: VEXGenerator):
        """Test generating basic CSAF document."""
        doc = generator.generate_csaf(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/requests@2.31.0",
            status="not_affected",
        )

        assert doc["document"]["category"] == "csaf_vex"
        assert doc["document"]["csaf_version"] == "2.0"
        assert doc["document"]["publisher"]["name"] == "Test Org"
        assert len(doc["vulnerabilities"]) == 1
        assert doc["vulnerabilities"][0]["cve"] == "CVE-2024-1234"

    def test_generate_csaf_with_remediation(self, generator: VEXGenerator):
        """Test generating CSAF document with remediation."""
        doc = generator.generate_csaf(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/requests@2.31.0",
            status="fixed",
            remediation={
                "category": "vendor_fix",
                "details": "Upgrade to version 2.31.1",
                "url": "https://pypi.org/project/requests/2.31.1",
            },
        )

        assert len(doc["vulnerabilities"][0]["remediations"]) == 1
        remediation = doc["vulnerabilities"][0]["remediations"][0]
        assert remediation["category"] == "vendor_fix"
        assert "Upgrade" in remediation["details"]
        assert remediation["url"] == "https://pypi.org/project/requests/2.31.1"

    def test_assess_exploitability_low_cvss(self, generator: VEXGenerator):
        """Test exploitability assessment with low CVSS."""
        cve = CVE(
            id="CVE-2024-1234",
            cvss_score=5.0,
            description="Low severity vulnerability",
        )
        assessment = generator.assess_exploitability(cve, [])

        assert assessment.cve_id == "CVE-2024-1234"
        assert assessment.exploitable is False
        assert assessment.exploit_available is False
        assert assessment.active_exploitation is False

    def test_assess_exploitability_high_cvss(self, generator: VEXGenerator):
        """Test exploitability assessment with high CVSS."""
        cve = CVE(
            id="CVE-2024-5678",
            cvss_score=9.8,
            description="Critical remote code execution",
        )
        assessment = generator.assess_exploitability(cve, [])

        assert assessment.exploitable is True
        assert assessment.confidence > 0.5

    def test_assess_exploitability_with_exploit(self, generator: VEXGenerator):
        """Test exploitability assessment with known exploit."""
        cve = CVE(
            id="CVE-2024-9999",
            cvss_score=8.5,
            description="SQL injection vulnerability",
        )
        threat_intel = [
            {
                "type": "tool",
                "id": "exploit-db-12345",
                "description": "Functional exploit available",
            }
        ]
        assessment = generator.assess_exploitability(cve, threat_intel)

        assert assessment.exploit_available is True
        assert assessment.exploit_maturity in ["poc", "functional"]
        assert len(assessment.threat_intel_sources) > 0

    def test_assess_exploitability_active_exploitation(self, generator: VEXGenerator):
        """Test exploitability assessment with active exploitation."""
        cve = CVE(
            id="CVE-2024-0000",
            cvss_score=9.0,
            description="Remote code execution under active attack",
        )
        threat_intel = [
            {
                "type": "indicator",
                "id": "indicator-1",
                "description": "IOC observed in the wild",
            }
        ]
        assessment = generator.assess_exploitability(cve, threat_intel)

        assert assessment.active_exploitation is True
        assert assessment.exploit_maturity == "high"
        assert assessment.confidence > 0.7

    def test_track_remediation_identified(self, generator: VEXGenerator):
        """Test tracking remediation in identified state."""
        status = generator.track_remediation(
            cve_id="CVE-2024-1234", status="identified"
        )

        assert status.cve_id == "CVE-2024-1234"
        assert status.status == "identified"
        assert status.patch_available is False
        assert status.workaround_available is False

    def test_track_remediation_with_patch(self, generator: VEXGenerator):
        """Test tracking remediation with patch available."""
        status = generator.track_remediation(
            cve_id="CVE-2024-1234",
            status="patch_available",
            remediation_plan={
                "patch_available": True,
                "patch_version": "2.31.1",
                "notes": ["Patch tested in dev environment"],
            },
        )

        assert status.status == "patch_available"
        assert status.patch_available is True
        assert status.patch_version == "2.31.1"
        assert len(status.remediation_notes) == 1

    def test_track_remediation_with_workaround(self, generator: VEXGenerator):
        """Test tracking remediation with workaround."""
        status = generator.track_remediation(
            cve_id="CVE-2024-5678",
            status="workaround_available",
            remediation_plan={
                "patch_available": False,
                "workaround_available": True,
                "workaround_description": "Disable affected module",
                "estimated_fix_date": datetime.utcnow() + timedelta(days=30),
            },
        )

        assert status.workaround_available is True
        assert "Disable" in status.workaround_description
        assert status.estimated_fix_date is not None

    def test_validate_vex_valid_openvex(self, generator: VEXGenerator):
        """Test validating valid OpenVEX document."""
        doc = generator.generate_openvex(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/requests@2.31.0",
            status="not_affected",
        )

        result = generator.validate_vex(doc, format="openvex")

        assert result.valid is True
        assert len(result.errors) == 0
        assert result.format == "openvex"

    def test_validate_vex_missing_fields(self, generator: VEXGenerator):
        """Test validating OpenVEX document with missing fields."""
        doc = {
            "@context": "https://openvex.dev/ns/v0.2.0",
            "statements": [],
        }

        result = generator.validate_vex(doc, format="openvex")

        assert result.valid is False
        assert len(result.errors) > 0
        assert any("@id" in error for error in result.errors)

    def test_validate_vex_invalid_statement(self, generator: VEXGenerator):
        """Test validating OpenVEX with invalid statement."""
        doc = {
            "@context": "https://openvex.dev/ns/v0.2.0",
            "@id": "test-id",
            "author": "Test",
            "timestamp": datetime.utcnow().isoformat(),
            "version": 1,
            "statements": [{"vulnerability": "CVE-2024-1234"}],
        }

        result = generator.validate_vex(doc, format="openvex")

        assert result.valid is False
        assert any("missing products" in error for error in result.errors)

    def test_validate_vex_invalid_purl(self, generator: VEXGenerator):
        """Test validating OpenVEX with invalid purl."""
        doc = {
            "@context": "https://openvex.dev/ns/v0.2.0",
            "@id": "test-id",
            "author": "Test",
            "timestamp": datetime.utcnow().isoformat(),
            "version": 1,
            "statements": [
                {
                    "vulnerability": "CVE-2024-1234",
                    "products": ["not-a-purl"],
                    "status": "affected",
                }
            ],
        }

        result = generator.validate_vex(doc, format="openvex")

        assert result.valid is False
        assert any("invalid purl" in error.lower() for error in result.errors)

    def test_validate_vex_valid_csaf(self, generator: VEXGenerator):
        """Test validating valid CSAF document."""
        doc = generator.generate_csaf(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/requests@2.31.0",
            status="fixed",
        )

        result = generator.validate_vex(doc, format="csaf")

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_vex_invalid_csaf(self, generator: VEXGenerator):
        """Test validating invalid CSAF document."""
        doc = {"document": {}}

        result = generator.validate_vex(doc, format="csaf")

        assert result.valid is False
        assert len(result.errors) > 0

    def test_generate_human_readable_summary_openvex(self, generator: VEXGenerator):
        """Test generating human-readable summary for OpenVEX."""
        doc = generator.generate_openvex(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/requests@2.31.0",
            status="not_affected",
            justification="vulnerable_code_not_present",
            impact_statement="No impact to our usage",
        )

        summary = generator.generate_human_readable_summary(doc, format="openvex")

        assert "VEX DOCUMENT SUMMARY" in summary
        assert "CVE-2024-1234" in summary
        assert "not_affected" in summary
        assert "vulnerable_code_not_present" in summary
        assert "No impact" in summary

    def test_generate_human_readable_summary_csaf(self, generator: VEXGenerator):
        """Test generating human-readable summary for CSAF."""
        doc = generator.generate_csaf(
            cve_id="CVE-2024-5678",
            product="pkg:npm/lodash@4.17.20",
            status="fixed",
            remediation={
                "category": "vendor_fix",
                "details": "Upgrade to 4.17.21",
            },
        )

        summary = generator.generate_human_readable_summary(doc, format="csaf")

        assert "VEX DOCUMENT SUMMARY" in summary
        assert "CSAF 2.0" in summary
        assert "CVE-2024-5678" in summary
        assert "vendor_fix" in summary

    def test_chain_vex_documents(self, generator: VEXGenerator):
        """Test chaining VEX documents."""
        parent = generator.generate_openvex(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/myapp@1.0.0",
            status="affected",
        )

        child1 = generator.generate_openvex(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/requests@2.31.0",
            status="not_affected",
        )

        child2 = generator.generate_openvex(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/urllib3@2.0.0",
            status="fixed",
        )

        chained = generator.chain_vex_documents(parent, [child1, child2])

        assert "related_documents" in chained
        assert len(chained["related_documents"]) == 2
        assert chained["version"] == 2
        assert "last_updated" in chained

    def test_chain_vex_documents_multiple_times(self, generator: VEXGenerator):
        """Test chaining VEX documents multiple times."""
        parent = generator.generate_openvex(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/myapp@1.0.0",
            status="affected",
        )

        child1 = generator.generate_openvex(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/dep1@1.0.0",
            status="fixed",
        )

        # First chain
        chained = generator.chain_vex_documents(parent, [child1])
        assert chained["version"] == 2

        # Second chain
        child2 = generator.generate_openvex(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/dep2@1.0.0",
            status="not_affected",
        )
        chained2 = generator.chain_vex_documents(chained, [child2])
        assert chained2["version"] == 3
        assert len(chained2["related_documents"]) == 2


class TestIntegration:
    """Integration tests for VEX generator."""

    def test_full_workflow_not_affected(self):
        """Test complete workflow for not affected vulnerability."""
        # Initialize generator
        generator = VEXGenerator(
            config={
                "author": "Security Team",
                "base_url": "https://security.example.com",
                "organization": "Example Corp",
            }
        )

        # Generate OpenVEX document
        doc = generator.generate_openvex(
            cve_id="CVE-2024-1234",
            product="pkg:pypi/requests@2.31.0",
            status="not_affected",
            justification="vulnerable_code_not_present",
            impact_statement="Our application does not use the affected code",
        )

        # Validate document
        result = generator.validate_vex(doc, format="openvex")
        assert result.valid is True

        # Generate summary
        summary = generator.generate_human_readable_summary(doc)
        assert "CVE-2024-1234" in summary

    def test_full_workflow_affected_with_remediation(self):
        """Test complete workflow for affected vulnerability."""
        generator = VEXGenerator()

        # Assess exploitability
        cve = CVE(
            id="CVE-2024-5678",
            cvss_score=8.5,
            description="SQL injection vulnerability",
        )
        threat_intel = [{"type": "tool", "id": "exploit-1", "description": "POC"}]
        assessment = generator.assess_exploitability(cve, threat_intel)
        assert assessment.exploitable is True

        # Track remediation
        remediation = generator.track_remediation(
            cve_id="CVE-2024-5678",
            status="patch_available",
            remediation_plan={
                "patch_available": True,
                "patch_version": "3.0.1",
                "notes": ["Patch deployed to staging"],
            },
        )
        assert remediation.patch_available is True

        # Generate CSAF document
        doc = generator.generate_csaf(
            cve_id="CVE-2024-5678",
            product="pkg:pypi/sqlalchemy@1.4.0",
            status="fixed",
            remediation={
                "category": "vendor_fix",
                "details": f"Upgrade to {remediation.patch_version}",
                "url": "https://pypi.org/project/sqlalchemy/3.0.1",
            },
        )

        # Validate
        result = generator.validate_vex(doc, format="csaf")
        assert result.valid is True

    def test_dependency_chain_workflow(self):
        """Test workflow with dependency chaining."""
        generator = VEXGenerator()

        # Create parent VEX for main application
        parent = generator.generate_openvex(
            cve_id="CVE-2024-9999",
            product="pkg:pypi/myapp@2.0.0",
            status="under_investigation",
        )

        # Create child VEX for direct dependency
        dep1 = generator.generate_openvex(
            cve_id="CVE-2024-9999",
            product="pkg:pypi/django@4.2.0",
            status="affected",
        )

        # Create child VEX for transitive dependency
        dep2 = generator.generate_openvex(
            cve_id="CVE-2024-9999",
            product="pkg:pypi/sqlparse@0.4.0",
            status="fixed",
        )

        # Chain documents
        chained = generator.chain_vex_documents(parent, [dep1, dep2])

        # Validate chained document
        result = generator.validate_vex(chained, format="openvex")
        assert result.valid is True
        assert len(chained["related_documents"]) == 2
        assert chained["version"] > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
