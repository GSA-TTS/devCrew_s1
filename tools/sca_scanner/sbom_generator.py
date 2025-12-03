"""
Software Bill of Materials (SBOM) Generator

Generates SBOM documents in SPDX 2.3 and CycloneDX 1.4 formats with validation,
hash generation, and dependency relationship tracking.
"""

import hashlib
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET  # nosec B405 # Only used for SBOM generation

try:
    import jsonschema

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

try:
    from packageurl import PackageURL

    PURL_AVAILABLE = True
except ImportError:
    PURL_AVAILABLE = False


logger = logging.getLogger(__name__)


class SBOMGeneratorError(Exception):
    """Base exception for SBOM generation errors."""

    pass


class ValidationError(SBOMGeneratorError):
    """SBOM validation failed."""

    pass


class FormatError(SBOMGeneratorError):
    """Unsupported format or serialization error."""

    pass


class SBOMGenerator:
    """
    SBOM Generator supporting SPDX 2.3 and CycloneDX 1.4 formats.

    Generates Software Bill of Materials documents with package hashes,
    license information, dependency relationships, and schema validation.
    """

    SUPPORTED_FORMATS = {"spdx", "cyclonedx"}
    SUPPORTED_OUTPUTS = {"json", "xml"}

    # SPDX 2.3 License list (common subset)
    SPDX_LICENSES = {
        "MIT",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "GPL-2.0",
        "GPL-3.0",
        "LGPL-2.1",
        "LGPL-3.0",
        "AGPL-3.0",
        "MPL-2.0",
        "ISC",
        "Unlicense",
        "CC0-1.0",
        "EPL-2.0",
        "PSF-2.0",
    }

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize SBOM Generator.

        Args:
            cache_dir: Directory for caching package metadata
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "sca_scanner"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._hash_cache: Dict[str, str] = {}
        logger.info("SBOMGenerator initialized with cache at %s", self.cache_dir)

    def generate(
        self,
        dependencies: List[Dict[str, Any]],
        metadata: Dict[str, Any],
        format: str = "spdx",
        output_format: str = "json",
    ) -> str:
        """
        Generate SBOM in specified format.

        Args:
            dependencies: List of dependency dictionaries with keys:
                         name, version, ecosystem, licenses,
                         dependencies
            metadata: SBOM metadata (document_name, project_name,
                     etc.)
            format: SBOM format ('spdx' or 'cyclonedx')
            output_format: Output serialization ('json' or 'xml')

        Returns:
            Serialized SBOM document

        Raises:
            FormatError: If format is not supported
            ValidationError: If generated SBOM is invalid
        """
        format = format.lower()
        output_format = output_format.lower()

        if format not in self.SUPPORTED_FORMATS:
            raise FormatError(
                f"Unsupported format: {format}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        if output_format not in self.SUPPORTED_OUTPUTS:
            supported = ", ".join(self.SUPPORTED_OUTPUTS)
            raise FormatError(
                f"Unsupported output format: {output_format}. "
                f"Supported: {supported}"
            )

        logger.info(
            "Generating %s SBOM for %d dependencies", format.upper(), len(dependencies)
        )

        # Validate metadata
        self._validate_metadata(metadata)

        # Generate SBOM structure
        if format == "spdx":
            sbom = self.generate_spdx(dependencies, metadata)
        else:  # cyclonedx
            sbom = self.generate_cyclonedx(dependencies, metadata)

        # Validate against schema
        if JSONSCHEMA_AVAILABLE:
            self.validate_sbom(sbom, format)
        else:
            logger.warning("jsonschema not available, skipping validation")

        # Serialize output
        if output_format == "json":
            return self.to_json(sbom)
        else:  # xml
            if format != "cyclonedx":
                raise FormatError("XML output only supported for CycloneDX format")
            return self.to_xml(sbom)

    def generate_spdx(
        self, dependencies: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate SPDX 2.3 format SBOM.

        Args:
            dependencies: List of dependency dictionaries
            metadata: SBOM metadata

        Returns:
            SPDX document structure
        """
        created = metadata.get("created") or self._get_timestamp()
        document_name = metadata.get("document_name", "sbom-document")
        document_namespace = metadata.get(
            "document_namespace", f"https://example.com/sboms/{uuid.uuid4()}"
        )
        creator = metadata.get("creator", "DevCrew SCA Scanner")

        spdx_doc = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": document_name,
            "documentNamespace": document_namespace,
            "creationInfo": {
                "created": created,
                "creators": [f"Tool: {creator}"],
                "licenseListVersion": "3.21",
            },
            "packages": [],
            "relationships": [],
        }

        # Add root package
        project_name = metadata.get("project_name", "unknown-project")
        project_version = metadata.get("project_version", "0.0.0")

        root_package = {
            "SPDXID": "SPDXRef-Package-ROOT",
            "name": project_name,
            "versionInfo": project_version,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION",
        }
        spdx_doc["packages"].append(root_package)

        # Add dependency packages
        package_refs = {"ROOT": "SPDXRef-Package-ROOT"}

        for dep in dependencies:
            pkg_spdxid = self._generate_spdx_package(dep, spdx_doc)
            pkg_key = f"{dep['name']}-{dep.get('version', 'unknown')}"
            package_refs[pkg_key] = pkg_spdxid

            # Add DESCRIBES relationship for direct dependencies
            if dep.get("is_direct", True):
                spdx_doc["relationships"].append(
                    {
                        "spdxElementId": "SPDXRef-DOCUMENT",
                        "relationshipType": "DESCRIBES",
                        "relatedSpdxElement": pkg_spdxid,
                    }
                )

            # Add dependency relationships
            for sub_dep in dep.get("dependencies", []):
                sub_key = f"{sub_dep}-{dep.get('version', 'unknown')}"
                if sub_key in package_refs:
                    spdx_doc["relationships"].append(
                        {
                            "spdxElementId": pkg_spdxid,
                            "relationshipType": "DEPENDS_ON",
                            "relatedSpdxElement": package_refs[sub_key],
                        }
                    )

        logger.info(
            "Generated SPDX 2.3 SBOM with %d packages", len(spdx_doc["packages"])
        )
        return spdx_doc

    def generate_cyclonedx(
        self, dependencies: List[Dict[str, Any]], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate CycloneDX 1.4 format SBOM.

        Args:
            dependencies: List of dependency dictionaries
            metadata: SBOM metadata

        Returns:
            CycloneDX BOM structure
        """
        created = metadata.get("created") or self._get_timestamp()
        project_name = metadata.get("project_name", "unknown-project")
        project_version = metadata.get("project_version", "0.0.0")

        bom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": created,
                "tools": [
                    {"vendor": "DevCrew", "name": "SCA Scanner", "version": "1.0.0"}
                ],
                "component": {
                    "type": "application",
                    "bom-ref": f"pkg:generic/{project_name}@{project_version}",
                    "name": project_name,
                    "version": project_version,
                },
            },
            "components": [],
            "dependencies": [],
        }

        # Add root dependency
        root_bom_ref = f"pkg:generic/{project_name}@{project_version}"
        root_deps = []

        # Add dependency components
        components: List[Dict[str, Any]] = []
        deps: List[Dict[str, Any]] = []

        for dep in dependencies:
            component = self._generate_cyclonedx_component(dep)
            components.append(component)

            # Track direct dependencies of root
            if dep.get("is_direct", True):
                root_deps.append(component["bom-ref"])

            # Add dependency relationships
            dep_entry: Dict[str, Any] = {"ref": component["bom-ref"], "dependsOn": []}

            for sub_dep in dep.get("dependencies", []):
                ecosystem = dep.get("ecosystem", "generic")
                sub_version = dep.get("version", "unknown")
                sub_bom_ref = self._generate_purl(sub_dep, sub_version, ecosystem)
                dep_entry["dependsOn"].append(sub_bom_ref)

            if dep_entry["dependsOn"]:
                deps.append(dep_entry)

        # Add root dependencies
        if root_deps:
            deps.insert(0, {"ref": root_bom_ref, "dependsOn": root_deps})

        bom["components"] = components
        bom["dependencies"] = deps

        logger.info("Generated CycloneDX 1.4 BOM with %d components", len(components))
        return bom

    def calculate_hash(
        self, package: str, version: str, ecosystem: str = "pypi"
    ) -> Optional[str]:
        """
        Calculate SHA256 hash for a package.

        Args:
            package: Package name
            version: Package version
            ecosystem: Package ecosystem (pypi, npm, etc.)

        Returns:
            SHA256 hash or None if unavailable
        """
        cache_key = f"{ecosystem}:{package}:{version}"

        # Check cache
        if cache_key in self._hash_cache:
            return self._hash_cache[cache_key]

        # Try to download and hash package
        try:
            package_hash = self._download_and_hash(package, version, ecosystem)
            if package_hash:
                self._hash_cache[cache_key] = package_hash
                return package_hash
        except Exception as e:
            logger.warning(
                "Failed to calculate hash for %s@%s: %s", package, version, str(e)
            )

        return None

    def validate_sbom(self, sbom: Dict[str, Any], format: str) -> bool:
        """
        Validate SBOM against schema.

        Args:
            sbom: SBOM document structure
            format: SBOM format ('spdx' or 'cyclonedx')

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        if not JSONSCHEMA_AVAILABLE:
            logger.warning("jsonschema not available, skipping validation")
            return True

        try:
            if format == "spdx":
                self._validate_spdx(sbom)
            elif format == "cyclonedx":
                self._validate_cyclonedx(sbom)
            else:
                raise ValidationError(f"Unknown format: {format}")

            logger.info("SBOM validation passed for format: %s", format)
            return True

        except jsonschema.ValidationError as e:
            raise ValidationError(f"SBOM validation failed: {e.message}") from e

    def to_json(self, sbom: Dict[str, Any]) -> str:
        """
        Serialize SBOM to JSON.

        Args:
            sbom: SBOM document structure

        Returns:
            JSON string
        """
        return json.dumps(sbom, indent=2, ensure_ascii=False)

    def to_xml(self, sbom: Dict[str, Any]) -> str:
        """
        Serialize CycloneDX SBOM to XML.

        Args:
            sbom: CycloneDX BOM structure

        Returns:
            XML string

        Raises:
            FormatError: If SBOM is not CycloneDX format
        """
        if sbom.get("bomFormat") != "CycloneDX":
            raise FormatError("XML serialization only supported for CycloneDX format")

        return self._cyclonedx_to_xml(sbom)

    def sign_sbom(self, sbom_path: Path, key_path: Path) -> Path:
        """
        Sign SBOM document (stub implementation).

        Args:
            sbom_path: Path to SBOM file
            key_path: Path to signing key

        Returns:
            Path to signed SBOM or signature file

        Note:
            This is a stub for future implementation using GPG or cosign
        """
        logger.warning("SBOM signing not yet implemented")
        # TODO: Implement GPG or cosign signing
        # - Load private key from key_path
        # - Sign SBOM document
        # - Create detached signature or envelope
        # - Return signature file path
        return sbom_path

    # Private helper methods

    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """Validate required metadata fields."""
        required = ["document_name", "project_name"]
        missing = [field for field in required if field not in metadata]

        if missing:
            raise ValidationError(
                f"Missing required metadata fields: {', '.join(missing)}"
            )

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _generate_spdx_package(
        self, dep: Dict[str, Any], spdx_doc: Dict[str, Any]
    ) -> str:
        """
        Generate SPDX package entry and add to document.

        Args:
            dep: Dependency dictionary
            spdx_doc: SPDX document to add package to

        Returns:
            SPDX package ID
        """
        name = dep["name"]
        version = dep.get("version", "unknown")
        ecosystem = dep.get("ecosystem", "generic")

        # Generate unique SPDXID
        safe_name = re.sub(r"[^a-zA-Z0-9.-]", "-", name)
        safe_version = re.sub(r"[^a-zA-Z0-9.-]", "-", version)
        spdxid = f"SPDXRef-Package-{safe_name}-{safe_version}"

        # Get licenses
        licenses = dep.get("licenses", [])
        license_concluded = "NOASSERTION"
        if licenses:
            license_concluded = self._normalize_spdx_license(licenses[0])

        # Create package entry
        download_loc = self._get_download_location(name, version, ecosystem)
        package = {
            "SPDXID": spdxid,
            "name": name,
            "versionInfo": version,
            "downloadLocation": download_loc,
            "filesAnalyzed": False,
            "licenseConcluded": license_concluded,
            "licenseDeclared": license_concluded,
            "copyrightText": "NOASSERTION",
            "externalRefs": [],
        }

        # Add package hash
        package_hash = self.calculate_hash(name, version, ecosystem)
        if package_hash:
            package["checksums"] = [
                {"algorithm": "SHA256", "checksumValue": package_hash}
            ]

        # Add PURL as external reference
        if PURL_AVAILABLE:
            purl = self._generate_purl(name, version, ecosystem)
            package["externalRefs"].append(
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": purl,
                }
            )

        spdx_doc["packages"].append(package)
        return spdxid

    def _generate_cyclonedx_component(self, dep: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate CycloneDX component entry.

        Args:
            dep: Dependency dictionary

        Returns:
            CycloneDX component structure
        """
        name = dep["name"]
        version = dep.get("version", "unknown")
        ecosystem = dep.get("ecosystem", "generic")

        # Generate PURL
        purl = self._generate_purl(name, version, ecosystem)

        component = {
            "type": "library",
            "bom-ref": purl,
            "name": name,
            "version": version,
            "purl": purl,
        }

        # Add licenses
        licenses = dep.get("licenses", [])
        if licenses:
            component["licenses"] = []
            for lic in licenses:
                spdx_id = self._normalize_spdx_license(lic)
                if spdx_id in self.SPDX_LICENSES:
                    component["licenses"].append({"license": {"id": spdx_id}})
                else:
                    component["licenses"].append({"license": {"name": lic}})

        # Add hash
        package_hash = self.calculate_hash(name, version, ecosystem)
        if package_hash:
            component["hashes"] = [{"alg": "SHA-256", "content": package_hash}]

        # Add description if available
        if "description" in dep:
            component["description"] = dep["description"]

        return component

    def _generate_purl(self, name: str, version: str, ecosystem: str) -> str:
        """
        Generate Package URL (PURL).

        Args:
            name: Package name
            version: Package version
            ecosystem: Package ecosystem

        Returns:
            PURL string
        """
        if PURL_AVAILABLE:
            try:
                purl = PackageURL(
                    type=self._ecosystem_to_purl_type(ecosystem),
                    name=name,
                    version=version,
                )
                return purl.to_string()
            except Exception as e:
                logger.warning("Failed to generate PURL: %s", str(e))

        # Fallback to manual construction
        purl_type = self._ecosystem_to_purl_type(ecosystem)
        return f"pkg:{purl_type}/{name}@{version}"

    def _ecosystem_to_purl_type(self, ecosystem: str) -> str:
        """Map ecosystem to PURL type."""
        mapping = {
            "pypi": "pypi",
            "npm": "npm",
            "maven": "maven",
            "gem": "gem",
            "cargo": "cargo",
            "go": "golang",
            "nuget": "nuget",
        }
        return mapping.get(ecosystem.lower(), "generic")

    def _normalize_spdx_license(self, license: str) -> str:
        """Normalize license identifier to SPDX format."""
        # Simple normalization
        normalized = license.strip().upper()

        # Common mappings
        mappings = {
            "BSD": "BSD-3-Clause",
            "APACHE": "Apache-2.0",
            "APACHE-2": "Apache-2.0",
            "GPL": "GPL-3.0",
            "GPL-2": "GPL-2.0-only",
            "GPL-3": "GPL-3.0-only",
            "LGPL": "LGPL-3.0",
            "LGPL-2": "LGPL-2.1-only",
            "LGPL-3": "LGPL-3.0-only",
            "MPL": "MPL-2.0",
        }

        for key, value in mappings.items():
            if normalized.startswith(key):
                return value

        # Check if already SPDX format
        if license in self.SPDX_LICENSES:
            return license

        return "NOASSERTION"

    def _get_download_location(self, name: str, version: str, ecosystem: str) -> str:
        """Get package download location."""
        ecosystem = ecosystem.lower()

        if ecosystem == "pypi":
            return f"https://pypi.org/project/{name}/{version}/"
        elif ecosystem == "npm":
            return f"https://www.npmjs.com/package/{name}/v/{version}"
        elif ecosystem == "maven":
            parts = name.split(":", 1) if ":" in name else ("", name)
            group, artifact = parts
            return f"https://repo1.maven.org/maven2/" f"{group}/{artifact}/{version}/"
        elif ecosystem == "gem":
            return f"https://rubygems.org/gems/{name}/versions/{version}"
        elif ecosystem == "cargo":
            return f"https://crates.io/crates/{name}/{version}"

        return "NOASSERTION"

    def _download_and_hash(
        self, package: str, version: str, ecosystem: str
    ) -> Optional[str]:
        """
        Download package and calculate hash (stub implementation).

        Args:
            package: Package name
            version: Package version
            ecosystem: Package ecosystem

        Returns:
            SHA256 hash or None
        """
        # TODO: Implement actual package download and hashing
        # For now, return a deterministic hash based on package info
        # In production, this should:
        # 1. Download package from registry
        # 2. Calculate actual SHA256 hash
        # 3. Cache result

        data = f"{ecosystem}:{package}:{version}".encode()
        return hashlib.sha256(data).hexdigest()

    def _validate_spdx(self, sbom: Dict[str, Any]) -> None:
        """Validate SPDX document structure."""
        required_fields = [
            "spdxVersion",
            "dataLicense",
            "SPDXID",
            "name",
            "documentNamespace",
            "creationInfo",
        ]

        for field in required_fields:
            if field not in sbom:
                raise ValidationError(f"Missing required SPDX field: {field}")

        if sbom["spdxVersion"] != "SPDX-2.3":
            version = sbom["spdxVersion"]
            raise ValidationError(f"Invalid SPDX version: {version}, expected SPDX-2.3")

        if not isinstance(sbom.get("packages", []), list):
            raise ValidationError("SPDX packages must be a list")

        if not isinstance(sbom.get("relationships", []), list):
            raise ValidationError("SPDX relationships must be a list")

    def _validate_cyclonedx(self, sbom: Dict[str, Any]) -> None:
        """Validate CycloneDX BOM structure."""
        required_fields = ["bomFormat", "specVersion", "version"]

        for field in required_fields:
            if field not in sbom:
                raise ValidationError(f"Missing required CycloneDX field: {field}")

        if sbom["bomFormat"] != "CycloneDX":
            raise ValidationError(
                f"Invalid BOM format: {sbom['bomFormat']}, expected CycloneDX"
            )

        if sbom["specVersion"] != "1.4":
            raise ValidationError(
                f"Invalid spec version: {sbom['specVersion']}, expected 1.4"
            )

        if not isinstance(sbom.get("components", []), list):
            raise ValidationError("CycloneDX components must be a list")

    def _cyclonedx_to_xml(self, bom: Dict[str, Any]) -> str:
        """
        Convert CycloneDX BOM to XML format.

        Args:
            bom: CycloneDX BOM structure

        Returns:
            XML string
        """
        ns = "http://cyclonedx.org/schema/bom/1.4"
        ET.register_namespace("", ns)

        root = ET.Element(
            "bom",
            attrib={
                "xmlns": ns,
                "serialNumber": bom.get("serialNumber", ""),
                "version": str(bom.get("version", 1)),
            },
        )

        # Metadata
        if "metadata" in bom:
            metadata = ET.SubElement(root, "metadata")
            if "timestamp" in bom["metadata"]:
                timestamp = ET.SubElement(metadata, "timestamp")
                timestamp.text = bom["metadata"]["timestamp"]

            # Tools
            if "tools" in bom["metadata"]:
                tools = ET.SubElement(metadata, "tools")
                for tool in bom["metadata"]["tools"]:
                    tool_elem = ET.SubElement(tools, "tool")
                    if "vendor" in tool:
                        vendor = ET.SubElement(tool_elem, "vendor")
                        vendor.text = tool["vendor"]
                    if "name" in tool:
                        name = ET.SubElement(tool_elem, "name")
                        name.text = tool["name"]
                    if "version" in tool:
                        version = ET.SubElement(tool_elem, "version")
                        version.text = tool["version"]

            # Component (root)
            if "component" in bom["metadata"]:
                self._add_component_xml(metadata, bom["metadata"]["component"])

        # Components
        if "components" in bom:
            components = ET.SubElement(root, "components")
            for component in bom["components"]:
                self._add_component_xml(components, component)

        # Dependencies
        if "dependencies" in bom:
            dependencies = ET.SubElement(root, "dependencies")
            for dep in bom["dependencies"]:
                dep_elem = ET.SubElement(dependencies, "dependency", ref=dep["ref"])
                for depends_on in dep.get("dependsOn", []):
                    ET.SubElement(dep_elem, "dependency", ref=depends_on)

        # Convert to string with XML declaration
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        xml_str = ET.tostring(root, encoding="unicode", method="xml")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    def _add_component_xml(self, parent: ET.Element, component: Dict[str, Any]) -> None:
        """Add component to XML tree."""
        comp_elem = ET.SubElement(
            parent, "component", type=component.get("type", "library")
        )

        if "bom-ref" in component:
            comp_elem.set("bom-ref", component["bom-ref"])

        if "name" in component:
            name = ET.SubElement(comp_elem, "name")
            name.text = component["name"]

        if "version" in component:
            version = ET.SubElement(comp_elem, "version")
            version.text = component["version"]

        if "description" in component:
            desc = ET.SubElement(comp_elem, "description")
            desc.text = component["description"]

        if "purl" in component:
            purl = ET.SubElement(comp_elem, "purl")
            purl.text = component["purl"]

        # Licenses
        if "licenses" in component:
            licenses = ET.SubElement(comp_elem, "licenses")
            for lic in component["licenses"]:
                lic_elem = ET.SubElement(licenses, "license")
                if "license" in lic:
                    if "id" in lic["license"]:
                        lic_id = ET.SubElement(lic_elem, "id")
                        lic_id.text = lic["license"]["id"]
                    elif "name" in lic["license"]:
                        lic_name = ET.SubElement(lic_elem, "name")
                        lic_name.text = lic["license"]["name"]

        # Hashes
        if "hashes" in component:
            hashes = ET.SubElement(comp_elem, "hashes")
            for hash_item in component["hashes"]:
                hash_elem = ET.SubElement(hashes, "hash", alg=hash_item["alg"])
                hash_elem.text = hash_item["content"]
