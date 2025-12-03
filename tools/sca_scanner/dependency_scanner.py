"""
Dependency Scanner Module for Software Composition Analysis.

This module provides comprehensive dependency detection, parsing, and
analysis across multiple programming language ecosystems including Python,
Node.js, Java, Go, Ruby, and Rust.
"""

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore


class Ecosystem(str, Enum):
    """Supported package ecosystems."""

    PYPI = "pypi"
    NPM = "npm"
    MAVEN = "maven"
    GO = "go"
    RUBYGEMS = "rubygems"
    CARGO = "cargo"


class DependencyScannerError(Exception):
    """Base exception for DependencyScanner errors."""

    pass


class ManifestParseError(DependencyScannerError):
    """Exception raised when manifest file parsing fails."""

    pass


class UnsupportedFormatError(DependencyScannerError):
    """Exception raised for unsupported manifest formats."""

    pass


@dataclass
class Dependency:
    """
    Represents a software dependency with its metadata.

    Attributes:
        name: Package name
        version: Package version string
        ecosystem: Package ecosystem (pypi, npm, maven, etc.)
        manifest_file: Source manifest file path
        is_direct: True if direct dependency, False if transitive
        dependencies: List of nested dependencies
        raw_version: Original version specification (may include constraints)
        extras: Additional metadata specific to the ecosystem
    """

    name: str
    version: str
    ecosystem: Ecosystem
    manifest_file: str
    is_direct: bool = True
    dependencies: List["Dependency"] = field(default_factory=list)
    raw_version: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert dependency to dictionary representation.

        Returns:
            Dictionary containing all dependency information
        """
        return {
            "name": self.name,
            "version": self.version,
            "ecosystem": self.ecosystem.value,
            "manifest_file": self.manifest_file,
            "is_direct": self.is_direct,
            "dependencies": [dep.to_dict() for dep in self.dependencies],
            "raw_version": self.raw_version,
            "extras": self.extras,
        }


class DependencyScanner:
    """
    Multi-language dependency scanner for software composition analysis.

    Supports detection and parsing of dependency manifests for:
    - Python (requirements.txt, Pipfile.lock, poetry.lock,
      pyproject.toml)
    - Node.js (package.json, package-lock.json, yarn.lock,
      pnpm-lock.yaml)
    - Java (pom.xml, build.gradle)
    - Go (go.mod, go.sum)
    - Ruby (Gemfile.lock)
    - Rust (Cargo.lock)
    """

    # Manifest file patterns for each ecosystem
    MANIFEST_PATTERNS = {
        Ecosystem.PYPI: [
            "requirements.txt",
            "requirements/*.txt",
            "Pipfile.lock",
            "poetry.lock",
            "pyproject.toml",
        ],
        Ecosystem.NPM: [
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
        ],
        Ecosystem.MAVEN: ["pom.xml", "build.gradle", "build.gradle.kts"],
        Ecosystem.GO: ["go.mod", "go.sum"],
        Ecosystem.RUBYGEMS: ["Gemfile.lock"],
        Ecosystem.CARGO: ["Cargo.lock"],
    }

    def __init__(self, scan_path: Union[str, Path]):
        """
        Initialize the DependencyScanner.

        Args:
            scan_path: Path to file or directory to scan

        Raises:
            ValueError: If scan_path is invalid
        """
        self.scan_path = Path(scan_path)
        if not self.scan_path.exists():
            raise ValueError(f"Scan path does not exist: {scan_path}")

        self._manifest_cache: Dict[str, List[Dependency]] = {}

    def scan(self) -> List[Dependency]:
        """
        Scan for dependencies in the specified path.

        Returns:
            List of detected dependencies

        Raises:
            DependencyScannerError: If scanning fails
        """
        all_dependencies: List[Dependency] = []

        if self.scan_path.is_file():
            deps = self._scan_manifest_file(self.scan_path)
            all_dependencies.extend(deps)
        else:
            # Scan directory for all manifest files
            for ecosystem, patterns in self.MANIFEST_PATTERNS.items():
                for pattern in patterns:
                    for manifest_file in self.scan_path.rglob(pattern):
                        # Skip virtual environments and node_modules
                        if self._should_skip_path(manifest_file):
                            continue

                        try:
                            deps = self._scan_manifest_file(manifest_file)
                            all_dependencies.extend(deps)
                        except Exception as e:
                            # Log error but continue scanning
                            msg = f"Warning: Failed to parse {manifest_file}"
                            print(f"{msg}: {e}")

        return all_dependencies

    def _should_skip_path(self, path: Path) -> bool:
        """
        Check if path should be skipped during scanning.

        Args:
            path: Path to check

        Returns:
            True if path should be skipped
        """
        skip_dirs = {
            "venv",
            "virtualenv",
            ".venv",
            "env",
            "node_modules",
            ".git",
            "__pycache__",
            "target",
            "build",
            "dist",
            ".tox",
        }

        return any(skip_dir in path.parts for skip_dir in skip_dirs)

    def _scan_manifest_file(self, manifest_path: Path) -> List[Dependency]:
        """
        Scan a single manifest file for dependencies.

        Args:
            manifest_path: Path to manifest file

        Returns:
            List of dependencies from the manifest

        Raises:
            ManifestParseError: If parsing fails
            UnsupportedFormatError: If format is not supported
        """
        manifest_str = str(manifest_path)

        # Check cache first
        if manifest_str in self._manifest_cache:
            return self._manifest_cache[manifest_str]

        filename = manifest_path.name.lower()

        try:
            # Python manifests
            if filename == "requirements.txt" or filename.endswith(".txt"):
                deps = self._parse_requirements_txt(manifest_path)
            elif filename == "pipfile.lock":
                deps = self._parse_pipfile_lock(manifest_path)
            elif filename == "poetry.lock":
                deps = self._parse_poetry_lock(manifest_path)
            elif filename == "pyproject.toml":
                deps = self._parse_pyproject_toml(manifest_path)

            # Node.js manifests
            elif filename == "package.json":
                deps = self._parse_package_json(manifest_path)
            elif filename == "package-lock.json":
                deps = self._parse_package_lock_json(manifest_path)
            elif filename == "yarn.lock":
                deps = self._parse_yarn_lock(manifest_path)
            elif filename == "pnpm-lock.yaml":
                deps = self._parse_pnpm_lock(manifest_path)

            # Java manifests
            elif filename == "pom.xml":
                deps = self._parse_pom_xml(manifest_path)
            elif filename in ["build.gradle", "build.gradle.kts"]:
                deps = self._parse_gradle(manifest_path)

            # Go manifests
            elif filename == "go.mod":
                deps = self._parse_go_mod(manifest_path)
            elif filename == "go.sum":
                deps = self._parse_go_sum(manifest_path)

            # Ruby manifests
            elif filename == "gemfile.lock":
                deps = self._parse_gemfile_lock(manifest_path)

            # Rust manifests
            elif filename == "cargo.lock":
                deps = self._parse_cargo_lock(manifest_path)

            else:
                raise UnsupportedFormatError(f"Unsupported manifest format: {filename}")

            # Cache results
            self._manifest_cache[manifest_str] = deps
            return deps

        except (json.JSONDecodeError, ET.ParseError) as e:
            raise ManifestParseError(f"Failed to parse {manifest_path}: {e}") from e

    # ============= Python Parsers =============

    def _parse_requirements_txt(self, path: Path) -> List[Dependency]:
        """
        Parse requirements.txt file.

        Args:
            path: Path to requirements.txt

        Returns:
            List of dependencies
        """
        dependencies = []
        content = path.read_text(encoding="utf-8")

        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Skip editable installs and URLs
            if line.startswith("-e") or line.startswith("git+"):
                continue

            # Skip options
            if line.startswith("-"):
                continue

            try:
                name, version = self._parse_requirement_line(line)
                if name and version:
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            ecosystem=Ecosystem.PYPI,
                            manifest_file=str(path),
                            is_direct=True,
                            raw_version=(
                                line.split("==")[1].strip() if "==" in line else None
                            ),
                        )
                    )
            except Exception:
                # Skip malformed lines
                continue

        return dependencies

    def _parse_requirement_line(self, line: str) -> tuple[str, str]:
        """
        Parse a single requirement line.

        Args:
            line: Requirement line string

        Returns:
            Tuple of (package_name, version)
        """
        # Remove extras like package[extra]
        if "[" in line:
            line = line.split("[")[0]

        # Handle various version specifiers
        for operator in ["===", "==", ">=", "<=", "~=", ">", "<"]:
            if operator in line:
                parts = line.split(operator)
                name = parts[0].strip()
                version = parts[1].split(";")[0].split("#")[0].strip()
                # For non-exact matches, use the specified version
                if operator == "==":
                    return name, version
                else:
                    # Store the constraint but use the minimum version
                    return name, version

        # No version specified
        return line.strip(), "unknown"

    def _parse_pipfile_lock(self, path: Path) -> List[Dependency]:
        """
        Parse Pipfile.lock file.

        Args:
            path: Path to Pipfile.lock

        Returns:
            List of dependencies
        """
        content = json.loads(path.read_text(encoding="utf-8"))
        dependencies = []

        # Parse default dependencies
        for name, info in content.get("default", {}).items():
            version = info.get("version", "").lstrip("=")
            dependencies.append(
                Dependency(
                    name=name,
                    version=version,
                    ecosystem=Ecosystem.PYPI,
                    manifest_file=str(path),
                    is_direct=True,
                    extras={
                        "hashes": info.get("hashes", []),
                        "markers": info.get("markers"),
                    },
                )
            )

        # Parse dev dependencies
        for name, info in content.get("develop", {}).items():
            version = info.get("version", "").lstrip("=")
            dependencies.append(
                Dependency(
                    name=name,
                    version=version,
                    ecosystem=Ecosystem.PYPI,
                    manifest_file=str(path),
                    is_direct=True,
                    extras={
                        "dev": True,
                        "hashes": info.get("hashes", []),
                        "markers": info.get("markers"),
                    },
                )
            )

        return dependencies

    def _parse_poetry_lock(self, path: Path) -> List[Dependency]:
        """
        Parse poetry.lock file.

        Args:
            path: Path to poetry.lock

        Returns:
            List of dependencies
        """
        content = tomllib.loads(path.read_text(encoding="utf-8"))
        dependencies = []

        for package in content.get("package", []):
            name = package.get("name", "")
            version = package.get("version", "")

            # Parse sub-dependencies
            sub_deps = []
            for dep_name, dep_version in package.get("dependencies", {}).items():
                if isinstance(dep_version, str):
                    sub_deps.append(
                        Dependency(
                            name=dep_name,
                            version=dep_version.lstrip("^~>=<"),
                            ecosystem=Ecosystem.PYPI,
                            manifest_file=str(path),
                            is_direct=False,
                        )
                    )

            dependencies.append(
                Dependency(
                    name=name,
                    version=version,
                    ecosystem=Ecosystem.PYPI,
                    manifest_file=str(path),
                    is_direct=True,
                    dependencies=sub_deps,
                    extras={
                        "category": package.get("category"),
                        "optional": package.get("optional", False),
                    },
                )
            )

        return dependencies

    def _parse_pyproject_toml(self, path: Path) -> List[Dependency]:
        """
        Parse pyproject.toml file.

        Args:
            path: Path to pyproject.toml

        Returns:
            List of dependencies
        """
        content = tomllib.loads(path.read_text(encoding="utf-8"))
        dependencies = []

        # Poetry-style dependencies
        if "tool" in content and "poetry" in content["tool"]:
            poetry = content["tool"]["poetry"]
            for name, version_spec in poetry.get("dependencies", {}).items():
                if name == "python":
                    continue

                version = (
                    version_spec
                    if isinstance(version_spec, str)
                    else version_spec.get("version", "unknown")
                )
                dependencies.append(
                    Dependency(
                        name=name,
                        version=version.lstrip("^~>=<"),
                        ecosystem=Ecosystem.PYPI,
                        manifest_file=str(path),
                        is_direct=True,
                        raw_version=version,
                    )
                )

        # PEP 621 dependencies
        if "project" in content:
            project = content["project"]
            for dep_str in project.get("dependencies", []):
                name, version = self._parse_requirement_line(dep_str)
                if name:
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            ecosystem=Ecosystem.PYPI,
                            manifest_file=str(path),
                            is_direct=True,
                        )
                    )

        return dependencies

    # ============= Node.js Parsers =============

    def _parse_package_json(self, path: Path) -> List[Dependency]:
        """
        Parse package.json file.

        Args:
            path: Path to package.json

        Returns:
            List of dependencies
        """
        content = json.loads(path.read_text(encoding="utf-8"))
        dependencies = []

        # Parse dependencies
        for name, version in content.get("dependencies", {}).items():
            dependencies.append(
                Dependency(
                    name=name,
                    version=self._normalize_npm_version(version),
                    ecosystem=Ecosystem.NPM,
                    manifest_file=str(path),
                    is_direct=True,
                    raw_version=version,
                )
            )

        # Parse devDependencies
        for name, version in content.get("devDependencies", {}).items():
            dependencies.append(
                Dependency(
                    name=name,
                    version=self._normalize_npm_version(version),
                    ecosystem=Ecosystem.NPM,
                    manifest_file=str(path),
                    is_direct=True,
                    raw_version=version,
                    extras={"dev": True},
                )
            )

        return dependencies

    def _parse_package_lock_json(self, path: Path) -> List[Dependency]:
        """
        Parse package-lock.json file.

        Args:
            path: Path to package-lock.json

        Returns:
            List of dependencies
        """
        content = json.loads(path.read_text(encoding="utf-8"))
        dependencies = []

        # Handle both lockfile v1 and v2/v3 formats
        if "packages" in content:
            # Lockfile version 2/3
            for pkg_path, info in content["packages"].items():
                if not pkg_path:  # Skip root package
                    continue

                name = info.get("name", pkg_path.split("node_modules/")[-1])
                version = info.get("version", "")

                dependencies.append(
                    Dependency(
                        name=name,
                        version=version,
                        ecosystem=Ecosystem.NPM,
                        manifest_file=str(path),
                        is_direct=not pkg_path.count("node_modules") > 1,
                        extras={
                            "dev": info.get("dev", False),
                            "integrity": info.get("integrity"),
                        },
                    )
                )
        else:
            # Lockfile version 1
            for name, info in content.get("dependencies", {}).items():
                dependencies.extend(self._extract_npm_deps(name, info, str(path), True))

        return dependencies

    def _extract_npm_deps(
        self, name: str, info: Dict, manifest: str, is_direct: bool
    ) -> List[Dependency]:
        """
        Recursively extract npm dependencies.

        Args:
            name: Package name
            info: Package info dict
            manifest: Manifest file path
            is_direct: Whether this is a direct dependency

        Returns:
            List of dependencies including transitive ones
        """
        deps = []
        version = info.get("version", "")

        # Parse sub-dependencies
        sub_deps = []
        for sub_name, sub_info in info.get("dependencies", {}).items():
            sub_deps.extend(self._extract_npm_deps(sub_name, sub_info, manifest, False))

        deps.append(
            Dependency(
                name=name,
                version=version,
                ecosystem=Ecosystem.NPM,
                manifest_file=manifest,
                is_direct=is_direct,
                dependencies=sub_deps,
                extras={
                    "integrity": info.get("integrity"),
                    "resolved": info.get("resolved"),
                },
            )
        )

        return deps

    def _parse_yarn_lock(self, path: Path) -> List[Dependency]:
        """
        Parse yarn.lock file.

        Args:
            path: Path to yarn.lock

        Returns:
            List of dependencies
        """
        content = path.read_text(encoding="utf-8")
        dependencies = []

        # Yarn lock file has a specific format
        current_package = None
        current_version = None

        for line in content.splitlines():
            line = line.strip()

            # Package declaration line
            if line and not line.startswith(" ") and ":" in line:
                # Extract package name and version constraint
                match = re.match(r'"?([^@\s]+)@([^"]+)"?:', line)
                if match:
                    current_package = match.group(1)

            # Version line
            elif line.startswith("version") and current_package:
                match = re.match(r'version\s+"([^"]+)"', line)
                if match:
                    current_version = match.group(1)
                    dependencies.append(
                        Dependency(
                            name=current_package,
                            version=current_version,
                            ecosystem=Ecosystem.NPM,
                            manifest_file=str(path),
                            is_direct=True,
                        )
                    )
                    current_package = None
                    current_version = None

        return dependencies

    def _parse_pnpm_lock(self, path: Path) -> List[Dependency]:
        """
        Parse pnpm-lock.yaml file.

        Args:
            path: Path to pnpm-lock.yaml

        Returns:
            List of dependencies
        """
        # Basic YAML parsing for pnpm-lock.yaml
        # Note: This is a simplified parser. For production use,
        # consider PyYAML
        content = path.read_text(encoding="utf-8")
        dependencies = []

        in_packages_section = False
        current_package = None

        for line in content.splitlines():
            if "packages:" in line:
                in_packages_section = True
                continue

            if in_packages_section and line.startswith("  /"):
                # Package line like "  /package-name@1.0.0:"
                match = re.match(r"  /([^@]+)@([^:]+):", line)
                if match:
                    name = match.group(1)
                    version = match.group(2)
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            ecosystem=Ecosystem.NPM,
                            manifest_file=str(path),
                            is_direct=True,
                        )
                    )

        return dependencies

    def _normalize_npm_version(self, version: str) -> str:
        """
        Normalize npm version string.

        Args:
            version: Version string (may include ^, ~, >=, etc.)

        Returns:
            Normalized version string
        """
        # Remove common version prefixes
        version = re.sub(r"^[\^~>=<]+", "", version)
        # Handle version ranges
        if "-" in version and version.count(".") > 0:
            version = version.split("-")[0]
        return version.strip()

    # ============= Java Parsers =============

    def _parse_pom_xml(self, path: Path) -> List[Dependency]:
        """
        Parse pom.xml file.

        Args:
            path: Path to pom.xml

        Returns:
            List of dependencies
        """
        tree = ET.parse(path)
        root = tree.getroot()

        # Handle XML namespaces
        ns = {"m": "http://maven.apache.org/POM/4.0.0"}
        if root.tag.startswith("{"):
            ns_uri = root.tag.split("}")[0].strip("{")
            ns = {"m": ns_uri}

        dependencies = []

        # Find all dependency elements
        for dep in root.findall(".//m:dependency", ns) or root.findall(".//dependency"):
            group_id = (
                dep.find("m:groupId", ns)
                if dep.find("m:groupId", ns) is not None
                else dep.find("groupId")
            )
            artifact_id = (
                dep.find("m:artifactId", ns)
                if dep.find("m:artifactId", ns) is not None
                else dep.find("artifactId")
            )
            version = (
                dep.find("m:version", ns)
                if dep.find("m:version", ns) is not None
                else dep.find("version")
            )
            scope = (
                dep.find("m:scope", ns)
                if dep.find("m:scope", ns) is not None
                else dep.find("scope")
            )

            if group_id is not None and artifact_id is not None:
                name = f"{group_id.text}:{artifact_id.text}"
                version_text = version.text if version is not None else "unknown"
                # Strip Maven version range brackets
                version_str = version_text.strip("[]()") if version_text else "unknown"

                dependencies.append(
                    Dependency(
                        name=name,
                        version=version_str,
                        ecosystem=Ecosystem.MAVEN,
                        manifest_file=str(path),
                        is_direct=True,
                        extras={"scope": scope.text if scope is not None else None},
                    )
                )

        return dependencies

    def _parse_gradle(self, path: Path) -> List[Dependency]:
        """
        Parse build.gradle or build.gradle.kts file.

        Args:
            path: Path to gradle build file

        Returns:
            List of dependencies
        """
        content = path.read_text(encoding="utf-8")
        dependencies = []

        # Regex patterns for Gradle dependencies
        # Handles: implementation 'group:artifact:version'
        # or: implementation("group:artifact:version")
        patterns = [
            r"(?:implementation|api|compile|testImplementation)\s*"
            r"['\"]([^:'\"]+):([^:'\"]+):([^:'\"]+)['\"]",
            r"(?:implementation|api|compile|testImplementation)\s*\(\s*"
            r'["\']([^:"\']+):([^:"\']+):([^:"\']+)["\']\s*\)',
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                group_id, artifact_id, version = match.groups()
                dependencies.append(
                    Dependency(
                        name=f"{group_id}:{artifact_id}",
                        version=version,
                        ecosystem=Ecosystem.MAVEN,
                        manifest_file=str(path),
                        is_direct=True,
                    )
                )

        return dependencies

    # ============= Go Parsers =============

    def _parse_go_mod(self, path: Path) -> List[Dependency]:
        """
        Parse go.mod file.

        Args:
            path: Path to go.mod

        Returns:
            List of dependencies
        """
        content = path.read_text(encoding="utf-8")
        dependencies = []

        in_require_block = False

        for line in content.splitlines():
            line = line.strip()

            if line.startswith("require ("):
                in_require_block = True
                continue
            elif line == ")":
                in_require_block = False
                continue

            # Single line require
            if line.startswith("require "):
                line = line[8:].strip()

            if in_require_block or line:
                # Parse: module version [// indirect]
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0]
                    version = parts[1]
                    is_indirect = "// indirect" in line

                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            ecosystem=Ecosystem.GO,
                            manifest_file=str(path),
                            is_direct=not is_indirect,
                        )
                    )

        return dependencies

    def _parse_go_sum(self, path: Path) -> List[Dependency]:
        """
        Parse go.sum file.

        Args:
            path: Path to go.sum

        Returns:
            List of dependencies
        """
        content = path.read_text(encoding="utf-8")
        dependencies = []
        seen = set()

        for line in content.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                version = parts[1].split("/")[0]  # Remove /go.mod suffix

                # Deduplicate entries
                dep_key = f"{name}@{version}"
                if dep_key not in seen:
                    seen.add(dep_key)
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            ecosystem=Ecosystem.GO,
                            manifest_file=str(path),
                            is_direct=True,
                        )
                    )

        return dependencies

    # ============= Ruby Parsers =============

    def _parse_gemfile_lock(self, path: Path) -> List[Dependency]:
        """
        Parse Gemfile.lock file.

        Args:
            path: Path to Gemfile.lock

        Returns:
            List of dependencies
        """
        content = path.read_text(encoding="utf-8")
        dependencies = []

        in_specs_section = False
        current_indent = 0

        for line in content.splitlines():
            # Check for specs section
            if line.strip() == "specs:":
                in_specs_section = True
                continue

            # Exit specs section on non-indented line (except blank)
            if in_specs_section and line and not line.startswith(" "):
                in_specs_section = False

            if in_specs_section and line.strip():
                # Count leading spaces
                indent = len(line) - len(line.lstrip())

                # Parse gem line: "    name (version)"
                match = re.match(r"\s+([a-zA-Z0-9_-]+)\s+\(([^)]+)\)", line)
                if match:
                    name = match.group(1)
                    version = match.group(2)
                    dependencies.append(
                        Dependency(
                            name=name,
                            version=version,
                            ecosystem=Ecosystem.RUBYGEMS,
                            manifest_file=str(path),
                            is_direct=indent == 4,  # 4 spaces = direct
                        )
                    )

        return dependencies

    # ============= Rust Parsers =============

    def _parse_cargo_lock(self, path: Path) -> List[Dependency]:
        """
        Parse Cargo.lock file.

        Args:
            path: Path to Cargo.lock

        Returns:
            List of dependencies
        """
        content = tomllib.loads(path.read_text(encoding="utf-8"))
        dependencies = []

        for package in content.get("package", []):
            name = package.get("name", "")
            version = package.get("version", "")

            # Parse sub-dependencies
            sub_deps = []
            for dep in package.get("dependencies", []):
                # Dependencies are in format "name version (source)"
                dep_parts = dep.split()
                if len(dep_parts) >= 2:
                    dep_name = dep_parts[0]
                    dep_version = dep_parts[1]
                    sub_deps.append(
                        Dependency(
                            name=dep_name,
                            version=dep_version,
                            ecosystem=Ecosystem.CARGO,
                            manifest_file=str(path),
                            is_direct=False,
                        )
                    )

            dependencies.append(
                Dependency(
                    name=name,
                    version=version,
                    ecosystem=Ecosystem.CARGO,
                    manifest_file=str(path),
                    is_direct=True,
                    dependencies=sub_deps,
                    extras={"source": package.get("source")},
                )
            )

        return dependencies

    # ============= Utility Methods =============

    def get_direct_dependencies(
        self, dependencies: List[Dependency]
    ) -> List[Dependency]:
        """
        Filter to only direct dependencies.

        Args:
            dependencies: List of all dependencies

        Returns:
            List of direct dependencies only
        """
        return [dep for dep in dependencies if dep.is_direct]

    def get_dependencies_by_ecosystem(
        self, dependencies: List[Dependency], ecosystem: Ecosystem
    ) -> List[Dependency]:
        """
        Filter dependencies by ecosystem.

        Args:
            dependencies: List of all dependencies
            ecosystem: Target ecosystem

        Returns:
            List of dependencies in the specified ecosystem
        """
        return [dep for dep in dependencies if dep.ecosystem == ecosystem]

    def get_dependency_tree(self, dependencies: List[Dependency]) -> Dict[str, Any]:
        """
        Build a hierarchical dependency tree.

        Args:
            dependencies: List of dependencies

        Returns:
            Dictionary representing the dependency tree
        """
        tree: Dict[str, Any] = {}

        for dep in dependencies:
            if dep.is_direct:
                tree[dep.name] = {
                    "version": dep.version,
                    "ecosystem": dep.ecosystem.value,
                    "dependencies": self._build_subtree(dep.dependencies),
                }

        return tree

    def _build_subtree(self, dependencies: List[Dependency]) -> Dict[str, Any]:
        """
        Build subtree for transitive dependencies.

        Args:
            dependencies: List of sub-dependencies

        Returns:
            Dictionary representing the subtree
        """
        subtree: Dict[str, Any] = {}

        for dep in dependencies:
            subtree[dep.name] = {
                "version": dep.version,
                "ecosystem": dep.ecosystem.value,
                "dependencies": self._build_subtree(dep.dependencies),
            }

        return subtree

    def export_to_json(
        self, dependencies: List[Dependency], output_path: Union[str, Path]
    ) -> None:
        """
        Export dependencies to JSON file.

        Args:
            dependencies: List of dependencies to export
            output_path: Path to output JSON file
        """
        output_path = Path(output_path)
        data = [dep.to_dict() for dep in dependencies]

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_statistics(self, dependencies: List[Dependency]) -> Dict[str, Any]:
        """
        Generate statistics about scanned dependencies.

        Args:
            dependencies: List of dependencies

        Returns:
            Dictionary containing statistics
        """
        by_ecosystem: Dict[str, int] = {}
        by_manifest: Dict[str, int] = {}

        stats: Dict[str, Any] = {
            "total_dependencies": len(dependencies),
            "direct_dependencies": sum(1 for d in dependencies if d.is_direct),
            "transitive_dependencies": sum(1 for d in dependencies if not d.is_direct),
            "by_ecosystem": by_ecosystem,
            "by_manifest": by_manifest,
        }

        # Count by ecosystem
        for ecosystem in Ecosystem:
            count = sum(1 for d in dependencies if d.ecosystem == ecosystem)
            if count > 0:
                by_ecosystem[ecosystem.value] = count

        # Count by manifest file
        for dep in dependencies:
            by_manifest[dep.manifest_file] = by_manifest.get(dep.manifest_file, 0) + 1

        return stats
