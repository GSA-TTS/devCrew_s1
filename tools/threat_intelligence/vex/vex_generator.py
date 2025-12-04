"""VEX (Vulnerability Exploitability eXchange) document generator.

This module provides functionality for generating VEX documents in OpenVEX
and CSAF 2.0 formats, assessing exploitability of vulnerabilities, tracking
remediation status, and validating VEX documents.

Supports:
- OpenVEX format (https://openvex.dev)
- CSAF 2.0 format (OASIS standard)
- Package URL (purl) format
- VEX document chaining
- Exploitability assessment
- Remediation tracking
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from packageurl import PackageURL
from pydantic import BaseModel, Field, validator


class VEXStatement(BaseModel):
    """VEX statement describing vulnerability status for a product.

    Attributes:
        vulnerability: CVE identifier (e.g., CVE-2024-1234)
        products: List of product identifiers in purl format
        status: Vulnerability status (not_affected, affected, fixed,
                under_investigation)
        justification: Reason for status (e.g., vulnerable_code_not_present)
        impact_statement: Optional impact description
        action_statement: Optional recommended action
        action_statement_timestamp: When action statement was issued
    """

    vulnerability: str = Field(..., description="CVE identifier")
    products: List[str] = Field(..., description="Product purls")
    status: str = Field(
        ...,
        description="Status: not_affected, affected, fixed, " "under_investigation",
    )
    justification: Optional[str] = Field(None, description="Justification for status")
    impact_statement: Optional[str] = Field(None, description="Impact description")
    action_statement: Optional[str] = Field(None, description="Recommended action")
    action_statement_timestamp: Optional[datetime] = Field(
        None, description="Action statement timestamp"
    )

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate VEX status value."""
        valid_statuses = {
            "not_affected",
            "affected",
            "fixed",
            "under_investigation",
        }
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v

    @validator("justification")
    def validate_justification(cls, v: Optional[str]) -> Optional[str]:
        """Validate justification value."""
        if v is None:
            return v
        valid_justifications = {
            "component_not_present",
            "vulnerable_code_not_present",
            "vulnerable_code_not_in_execute_path",
            "vulnerable_code_cannot_be_controlled_by_adversary",
            "inline_mitigations_already_exist",
        }
        if v not in valid_justifications:
            raise ValueError(f"Justification must be one of {valid_justifications}")
        return v

    @validator("products")
    def validate_products(cls, v: List[str]) -> List[str]:
        """Validate product purls."""
        for purl_str in v:
            try:
                PackageURL.from_string(purl_str)
            except ValueError as e:
                raise ValueError(f"Invalid purl '{purl_str}': {e}")
        return v


class OpenVEXDocument(BaseModel):
    """OpenVEX document format.

    Attributes:
        context: OpenVEX schema version URL
        id: Unique document identifier
        author: Document author/organization
        timestamp: Document creation timestamp
        version: Document version number
        statements: List of VEX statements
        last_updated: Last update timestamp
    """

    context: str = Field(
        default="https://openvex.dev/ns/v0.2.0",
        alias="@context",
        description="OpenVEX schema version",
    )
    id: str = Field(
        default_factory=lambda: f"https://example.com/vex/{uuid.uuid4()}",
        alias="@id",
        description="Unique document ID",
    )
    author: str = Field(default="devCrew_s1", description="Document author")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    version: int = Field(default=1, description="Document version")
    statements: List[VEXStatement] = Field(
        default_factory=list, description="VEX statements"
    )
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat() + "Z" if v else None}


class CSAFProduct(BaseModel):
    """CSAF product identification.

    Attributes:
        product_id: Unique product identifier
        name: Product name
        cpe: CPE identifier (optional)
        purl: Package URL (optional)
    """

    product_id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    cpe: Optional[str] = Field(None, description="CPE identifier")
    purl: Optional[str] = Field(None, description="Package URL")


class CSAFVulnerability(BaseModel):
    """CSAF vulnerability information.

    Attributes:
        cve: CVE identifier
        product_status: Product status categorization
        scores: CVSS scores
        remediations: Remediation information
        notes: Additional notes
    """

    cve: str = Field(..., description="CVE identifier")
    product_status: Dict[str, List[str]] = Field(
        default_factory=dict, description="Product status by category"
    )
    scores: List[Dict[str, Any]] = Field(
        default_factory=list, description="CVSS scores"
    )
    remediations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Remediation information"
    )
    notes: List[Dict[str, str]] = Field(
        default_factory=list, description="Additional notes"
    )


class CSAFDocument(BaseModel):
    """CSAF 2.0 VEX document format.

    Attributes:
        document: Document metadata
        product_tree: Product identification tree
        vulnerabilities: List of vulnerabilities
    """

    document: Dict[str, Any] = Field(..., description="Document metadata")
    product_tree: Dict[str, Any] = Field(..., description="Product tree")
    vulnerabilities: List[CSAFVulnerability] = Field(
        default_factory=list, description="Vulnerabilities"
    )


class ExploitabilityAssessment(BaseModel):
    """Exploitability assessment for a CVE.

    Attributes:
        cve_id: CVE identifier
        exploitable: Whether the CVE is exploitable
        exploit_available: Whether exploit code is available
        exploit_maturity: Exploit maturity level
        active_exploitation: Whether active exploitation is detected
        confidence: Confidence score (0.0-1.0)
        threat_intel_sources: Sources used for assessment
        assessment_date: When assessment was performed
    """

    cve_id: str = Field(..., description="CVE identifier")
    exploitable: bool = Field(..., description="Is exploitable")
    exploit_available: bool = Field(..., description="Exploit code available")
    exploit_maturity: str = Field(..., description="Exploit maturity level")
    active_exploitation: bool = Field(..., description="Active exploitation detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    threat_intel_sources: List[str] = Field(
        default_factory=list, description="Threat intel sources"
    )
    assessment_date: datetime = Field(
        default_factory=datetime.utcnow, description="Assessment date"
    )

    @validator("exploit_maturity")
    def validate_maturity(cls, v: str) -> str:
        """Validate exploit maturity value."""
        valid_maturities = {"unproven", "poc", "functional", "high"}
        if v not in valid_maturities:
            raise ValueError(f"Exploit maturity must be one of {valid_maturities}")
        return v


class RemediationStatus(BaseModel):
    """Remediation status tracking.

    Attributes:
        cve_id: CVE identifier
        status: Current remediation status
        patch_available: Whether patch is available
        patch_version: Version with fix
        workaround_available: Whether workaround exists
        workaround_description: Workaround details
        estimated_fix_date: Expected fix date
        actual_fix_date: Actual fix date
        remediation_notes: Additional notes
        last_updated: Last update timestamp
    """

    cve_id: str = Field(..., description="CVE identifier")
    status: str = Field(..., description="Remediation status")
    patch_available: bool = Field(..., description="Patch available")
    patch_version: Optional[str] = Field(None, description="Version with fix")
    workaround_available: bool = Field(..., description="Workaround available")
    workaround_description: Optional[str] = Field(
        None, description="Workaround details"
    )
    estimated_fix_date: Optional[datetime] = Field(
        None, description="Expected fix date"
    )
    actual_fix_date: Optional[datetime] = Field(None, description="Actual fix date")
    remediation_notes: List[str] = Field(
        default_factory=list, description="Additional notes"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last update"
    )

    @validator("status")
    def validate_status(cls, v: str) -> str:
        """Validate remediation status."""
        valid_statuses = {
            "identified",
            "analyzing",
            "patch_in_progress",
            "patch_available",
            "patched",
            "workaround_available",
            "accepted_risk",
            "false_positive",
        }
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class ValidationResult(BaseModel):
    """VEX document validation result.

    Attributes:
        valid: Whether document is valid
        errors: List of validation errors
        warnings: List of validation warnings
        format: Document format validated
    """

    valid: bool = Field(..., description="Document is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    format: str = Field(..., description="Document format")


class CVE(BaseModel):
    """CVE information for exploitability assessment.

    Attributes:
        id: CVE identifier
        cvss_score: CVSS base score
        cvss_vector: CVSS vector string
        description: CVE description
        references: List of references
        published_date: Publication date
    """

    id: str = Field(..., description="CVE identifier")
    cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="CVSS score")
    cvss_vector: Optional[str] = Field(None, description="CVSS vector")
    description: str = Field(..., description="CVE description")
    references: List[str] = Field(default_factory=list, description="References")
    published_date: Optional[datetime] = Field(None, description="Publication date")


class VEXGenerator:
    """VEX document generator.

    Generates VEX documents in OpenVEX and CSAF 2.0 formats, assesses
    exploitability, tracks remediation status, and validates VEX documents.

    Attributes:
        config: Configuration dictionary
        author: Default document author
        base_url: Base URL for document IDs
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize VEX generator.

        Args:
            config: Optional configuration dictionary with keys:
                - author: Document author (default: devCrew_s1)
                - base_url: Base URL for IDs (default: https://example.com)
                - organization: Organization name
        """
        self.config = config or {}
        self.author = self.config.get("author", "devCrew_s1")
        self.base_url = self.config.get("base_url", "https://example.com")
        self.organization = self.config.get("organization", "devCrew_s1")

    def generate_openvex(
        self,
        cve_id: str,
        product: str,
        status: str,
        justification: Optional[str] = None,
        impact_statement: Optional[str] = None,
        action_statement: Optional[str] = None,
    ) -> Dict:
        """Generate OpenVEX document.

        Args:
            cve_id: CVE identifier (e.g., CVE-2024-1234)
            product: Product identifier in purl format
            status: Vulnerability status (not_affected, affected, fixed,
                    under_investigation)
            justification: Optional justification for status
            impact_statement: Optional impact description
            action_statement: Optional recommended action

        Returns:
            OpenVEX document as dictionary

        Example:
            >>> generator = VEXGenerator()
            >>> doc = generator.generate_openvex(
            ...     cve_id="CVE-2024-1234",
            ...     product="pkg:pypi/requests@2.31.0",
            ...     status="not_affected",
            ...     justification="vulnerable_code_not_present"
            ... )
        """
        statement = VEXStatement(
            vulnerability=cve_id,
            products=[product],
            status=status,
            justification=justification,
            impact_statement=impact_statement,
            action_statement=action_statement,
            action_statement_timestamp=datetime.utcnow() if action_statement else None,
        )

        # Use populate_by_name=True to allow alias usage
        document = OpenVEXDocument.parse_obj(
            {
                "@id": f"{self.base_url}/vex/{uuid.uuid4()}",
                "@context": "https://openvex.dev/ns/v0.2.0",
                "author": self.author,
                "timestamp": datetime.utcnow(),
                "version": 1,
                "statements": [json.loads(statement.json())],
            }
        )

        return json.loads(document.json(by_alias=True))

    def generate_csaf(
        self,
        cve_id: str,
        product: str,
        status: str,
        remediation: Optional[Dict] = None,
    ) -> Dict:
        """Generate CSAF 2.0 VEX document.

        Args:
            cve_id: CVE identifier
            product: Product identifier in purl format
            status: Vulnerability status
            remediation: Optional remediation information with keys:
                - category: Remediation category (workaround, mitigation,
                            vendor_fix)
                - details: Remediation details
                - url: Remediation URL

        Returns:
            CSAF 2.0 document as dictionary

        Example:
            >>> generator = VEXGenerator()
            >>> doc = generator.generate_csaf(
            ...     cve_id="CVE-2024-1234",
            ...     product="pkg:pypi/requests@2.31.0",
            ...     status="fixed",
            ...     remediation={
            ...         "category": "vendor_fix",
            ...         "details": "Upgrade to version 2.31.1",
            ...         "url": "https://pypi.org/project/requests/2.31.1"
            ...     }
            ... )
        """
        # Parse product purl
        try:
            purl = PackageURL.from_string(product)
            product_name = (
                f"{purl.namespace}/{purl.name}" if purl.namespace else purl.name
            )
            product_version = purl.version or "unknown"
        except ValueError:
            product_name = product
            product_version = "unknown"

        # Map OpenVEX status to CSAF product_status
        status_map = {
            "not_affected": "known_not_affected",
            "affected": "known_affected",
            "fixed": "fixed",
            "under_investigation": "under_investigation",
        }
        csaf_status = status_map.get(status, "known_affected")

        # Create product tree
        product_tree = {
            "full_product_names": [
                {
                    "product_id": f"{product_name}-{product_version}",
                    "name": f"{product_name} {product_version}",
                    "product_identification_helper": {"purl": product},
                }
            ]
        }

        # Create vulnerability entry
        vulnerability: Dict[str, Any] = {
            "cve": cve_id,
            "product_status": {csaf_status: [f"{product_name}-{product_version}"]},
        }

        # Add remediation if provided
        if remediation:
            vulnerability["remediations"] = [
                {
                    "category": remediation.get("category", "workaround"),
                    "details": remediation.get("details", "See details"),
                    "product_ids": [f"{product_name}-{product_version}"],
                    "url": remediation.get("url"),
                }
            ]

        # Create CSAF document
        document = {
            "document": {
                "category": "csaf_vex",
                "csaf_version": "2.0",
                "title": f"VEX for {cve_id}",
                "publisher": {
                    "category": "vendor",
                    "name": self.organization,
                    "namespace": self.base_url,
                },
                "tracking": {
                    "id": str(uuid.uuid4()),
                    "status": "final",
                    "version": "1",
                    "revision_history": [
                        {
                            "number": "1",
                            "date": datetime.utcnow().isoformat() + "Z",
                            "summary": "Initial version",
                        }
                    ],
                    "initial_release_date": datetime.utcnow().isoformat() + "Z",
                    "current_release_date": datetime.utcnow().isoformat() + "Z",
                },
            },
            "product_tree": product_tree,
            "vulnerabilities": [vulnerability],
        }

        return document

    def assess_exploitability(
        self, cve: CVE, threat_intel: List[Any]
    ) -> ExploitabilityAssessment:
        """Assess if CVE is exploitable based on threat intelligence.

        Args:
            cve: CVE information
            threat_intel: List of STIX objects or threat intel data

        Returns:
            ExploitabilityAssessment with findings

        Example:
            >>> generator = VEXGenerator()
            >>> cve = CVE(
            ...     id="CVE-2024-1234",
            ...     cvss_score=9.8,
            ...     description="Remote code execution"
            ... )
            >>> assessment = generator.assess_exploitability(
            ...     cve, threat_intel_data
            ... )
        """
        # Initialize assessment
        exploitable = False
        exploit_available = False
        exploit_maturity = "unproven"
        active_exploitation = False
        confidence = 0.5
        sources = []

        # Analyze CVSS score
        if cve.cvss_score and cve.cvss_score >= 7.0:
            exploitable = True
            confidence += 0.1

        # Analyze threat intelligence
        for intel in threat_intel:
            # Check for exploit patterns
            if isinstance(intel, dict):
                intel_type = intel.get("type", "")
                if intel_type == "malware" or intel_type == "tool":
                    exploit_available = True
                    confidence += 0.15
                    sources.append(intel.get("id", "unknown"))

                    # Assess maturity
                    if "functional" in str(intel).lower():
                        exploit_maturity = "functional"
                    elif "poc" in str(intel).lower():
                        exploit_maturity = "poc"

                if intel_type == "indicator":
                    active_exploitation = True
                    confidence += 0.25
                    sources.append(intel.get("id", "unknown"))

        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)

        # Determine final maturity
        if active_exploitation:
            exploit_maturity = "high"
        elif exploit_available and exploit_maturity == "unproven":
            exploit_maturity = "poc"

        return ExploitabilityAssessment(
            cve_id=cve.id,
            exploitable=exploitable,
            exploit_available=exploit_available,
            exploit_maturity=exploit_maturity,
            active_exploitation=active_exploitation,
            confidence=confidence,
            threat_intel_sources=sources,
            assessment_date=datetime.utcnow(),
        )

    def track_remediation(
        self,
        cve_id: str,
        status: str,
        remediation_plan: Optional[Dict] = None,
    ) -> RemediationStatus:
        """Track remediation progress for a CVE.

        Args:
            cve_id: CVE identifier
            status: Remediation status
            remediation_plan: Optional remediation plan with keys:
                - patch_available: bool
                - patch_version: str
                - workaround_available: bool
                - workaround_description: str
                - estimated_fix_date: datetime
                - notes: List[str]

        Returns:
            RemediationStatus object

        Example:
            >>> generator = VEXGenerator()
            >>> status = generator.track_remediation(
            ...     cve_id="CVE-2024-1234",
            ...     status="patch_available",
            ...     remediation_plan={
            ...         "patch_available": True,
            ...         "patch_version": "2.31.1",
            ...         "notes": ["Patch tested successfully"]
            ...     }
            ... )
        """
        plan = remediation_plan or {}

        return RemediationStatus(
            cve_id=cve_id,
            status=status,
            patch_available=plan.get("patch_available", False),
            patch_version=plan.get("patch_version"),
            workaround_available=plan.get("workaround_available", False),
            workaround_description=plan.get("workaround_description"),
            estimated_fix_date=plan.get("estimated_fix_date"),
            actual_fix_date=plan.get("actual_fix_date"),
            remediation_notes=plan.get("notes", []),
            last_updated=datetime.utcnow(),
        )

    def validate_vex(
        self, vex_document: Dict, format: str = "openvex"
    ) -> ValidationResult:
        """Validate VEX document against schema.

        Args:
            vex_document: VEX document dictionary
            format: Document format (openvex or csaf)

        Returns:
            ValidationResult with validation details

        Example:
            >>> generator = VEXGenerator()
            >>> result = generator.validate_vex(
            ...     vex_document, format="openvex"
            ... )
            >>> if not result.valid:
            ...     print(result.errors)
        """
        errors = []
        warnings = []

        try:
            if format == "openvex":
                # Validate OpenVEX format
                if "@context" not in vex_document:
                    errors.append("Missing @context field")

                if "@id" not in vex_document:
                    errors.append("Missing @id field")

                if "author" not in vex_document:
                    errors.append("Missing author field")

                if "timestamp" not in vex_document:
                    errors.append("Missing timestamp field")

                if "version" not in vex_document:
                    errors.append("Missing version field")

                if "statements" not in vex_document:
                    errors.append("Missing statements field")
                else:
                    statements = vex_document.get("statements", [])
                    if not statements:
                        warnings.append("No statements in document")

                    for idx, stmt in enumerate(statements):
                        if "vulnerability" not in stmt:
                            errors.append(f"Statement {idx}: missing vulnerability")
                        if "products" not in stmt:
                            errors.append(f"Statement {idx}: missing products")
                        if "status" not in stmt:
                            errors.append(f"Statement {idx}: missing status")

                        # Validate purls
                        products = stmt.get("products", [])
                        for purl_str in products:
                            try:
                                PackageURL.from_string(purl_str)
                            except ValueError:
                                errors.append(
                                    f"Statement {idx}: invalid purl " f"'{purl_str}'"
                                )

            elif format == "csaf":
                # Validate CSAF format
                if "document" not in vex_document:
                    errors.append("Missing document field")
                else:
                    doc = vex_document["document"]
                    if "category" not in doc:
                        errors.append("Missing document.category")
                    if "csaf_version" not in doc:
                        errors.append("Missing document.csaf_version")
                    if "title" not in doc:
                        errors.append("Missing document.title")
                    if "publisher" not in doc:
                        errors.append("Missing document.publisher")
                    if "tracking" not in doc:
                        errors.append("Missing document.tracking")

                if "product_tree" not in vex_document:
                    errors.append("Missing product_tree field")

                if "vulnerabilities" not in vex_document:
                    errors.append("Missing vulnerabilities field")
                elif not vex_document.get("vulnerabilities"):
                    warnings.append("No vulnerabilities in document")

            else:
                errors.append(f"Unknown format: {format}")

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            format=format,
        )

    def generate_human_readable_summary(
        self, vex_document: Dict, format: str = "openvex"
    ) -> str:
        """Generate human-readable summary of VEX document.

        Args:
            vex_document: VEX document dictionary
            format: Document format (openvex or csaf)

        Returns:
            Human-readable summary string

        Example:
            >>> generator = VEXGenerator()
            >>> summary = generator.generate_human_readable_summary(doc)
            >>> print(summary)
        """
        lines = []
        lines.append("=" * 60)
        lines.append("VEX DOCUMENT SUMMARY")
        lines.append("=" * 60)

        if format == "openvex":
            lines.append("Format: OpenVEX")
            lines.append(f"Document ID: {vex_document.get('@id')}")
            lines.append(f"Author: {vex_document.get('author')}")
            lines.append(f"Version: {vex_document.get('version')}")
            lines.append(f"Timestamp: {vex_document.get('timestamp')}")
            lines.append("")
            lines.append("STATEMENTS:")
            lines.append("-" * 60)

            for idx, stmt in enumerate(vex_document.get("statements", []), 1):
                lines.append(f"\nStatement {idx}:")
                lines.append(f"  Vulnerability: {stmt.get('vulnerability')}")
                lines.append(f"  Status: {stmt.get('status')}")
                lines.append(f"  Products: {', '.join(stmt.get('products', []))}")
                if stmt.get("justification"):
                    lines.append(f"  Justification: {stmt.get('justification')}")
                if stmt.get("impact_statement"):
                    lines.append(f"  Impact: {stmt.get('impact_statement')}")
                if stmt.get("action_statement"):
                    lines.append(f"  Action: {stmt.get('action_statement')}")

        elif format == "csaf":
            doc = vex_document.get("document", {})
            tracking = doc.get("tracking", {})
            lines.append("Format: CSAF 2.0")
            lines.append(f"Title: {doc.get('title')}")
            lines.append(f"Publisher: {doc.get('publisher', {}).get('name')}")
            lines.append(f"Tracking ID: {tracking.get('id')}")
            lines.append(f"Version: {tracking.get('version')}")
            lines.append(f"Status: {tracking.get('status')}")
            lines.append("")
            lines.append("VULNERABILITIES:")
            lines.append("-" * 60)

            for idx, vuln in enumerate(vex_document.get("vulnerabilities", []), 1):
                lines.append(f"\nVulnerability {idx}:")
                lines.append(f"  CVE: {vuln.get('cve')}")
                product_status = vuln.get("product_status", {})
                for status_type, products in product_status.items():
                    lines.append(f"  {status_type}: {', '.join(products)}")

                remediations = vuln.get("remediations", [])
                if remediations:
                    lines.append("  Remediations:")
                    for rem in remediations:
                        lines.append(
                            f"    - {rem.get('category')}: " f"{rem.get('details')}"
                        )

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def chain_vex_documents(self, parent_doc: Dict, child_docs: List[Dict]) -> Dict:
        """Chain VEX documents together.

        Allows referencing other VEX documents for dependencies.

        Args:
            parent_doc: Parent OpenVEX document
            child_docs: List of child VEX documents to reference

        Returns:
            Updated parent document with references

        Example:
            >>> generator = VEXGenerator()
            >>> parent = generator.generate_openvex(...)
            >>> child = generator.generate_openvex(...)
            >>> chained = generator.chain_vex_documents(parent, [child])
        """
        # Add chained document references
        if "related_documents" not in parent_doc:
            parent_doc["related_documents"] = []

        for child_doc in child_docs:
            parent_doc["related_documents"].append(
                {
                    "id": child_doc.get("@id"),
                    "relationship": "dependency",
                }
            )

        # Update version and timestamp
        parent_doc["version"] = parent_doc.get("version", 1) + 1
        parent_doc["last_updated"] = datetime.utcnow().isoformat() + "Z"

        return parent_doc
