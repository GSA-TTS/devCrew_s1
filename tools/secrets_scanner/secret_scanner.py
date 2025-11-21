"""
Secret Scanner with pattern matching and entropy analysis.

Core scanning engine for detecting secrets in files and content.
"""

import hashlib
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .pattern_manager import PatternManager, PatternSeverity, SecretPattern


@dataclass
class SecretFinding:
    """Represents a detected secret."""

    pattern_name: str
    pattern_description: str
    severity: PatternSeverity
    file_path: str
    line_number: int
    line_content: str
    matched_text: str
    entropy: Optional[float] = None
    hash_value: str = ""
    category: str = ""
    is_verified: bool = False
    is_false_positive: bool = False

    def __post_init__(self) -> None:
        """Generate hash for the finding."""
        if not self.hash_value:
            content = f"{self.pattern_name}:{self.file_path}:{self.matched_text}"
            self.hash_value = hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
        return {
            "pattern_name": self.pattern_name,
            "pattern_description": self.pattern_description,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_content": self.line_content[:200],
            "matched_text": self._redact(self.matched_text),
            "entropy": self.entropy,
            "hash": self.hash_value,
            "category": self.category,
            "is_verified": self.is_verified,
            "is_false_positive": self.is_false_positive,
        }

    def _redact(self, text: str) -> str:
        """Redact secret value for safe display."""
        if len(text) <= 8:
            return "*" * len(text)
        return text[:4] + "*" * (len(text) - 8) + text[-4:]

    def to_sarif(self) -> Dict[str, Any]:
        """Convert to SARIF result format."""
        return {
            "ruleId": self.pattern_name,
            "level": self._severity_to_sarif_level(),
            "message": {"text": f"Potential {self.pattern_description} detected"},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": self.file_path},
                        "region": {
                            "startLine": self.line_number,
                            "snippet": {"text": self.line_content[:100]},
                        },
                    }
                }
            ],
            "fingerprints": {"secret_hash": self.hash_value},
            "properties": {
                "entropy": self.entropy,
                "category": self.category,
                "is_verified": self.is_verified,
            },
        }

    def _severity_to_sarif_level(self) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            PatternSeverity.CRITICAL: "error",
            PatternSeverity.HIGH: "error",
            PatternSeverity.MEDIUM: "warning",
            PatternSeverity.LOW: "note",
        }
        return mapping.get(self.severity, "warning")


@dataclass
class ScanResult:
    """Results of a secret scan."""

    findings: List[SecretFinding] = field(default_factory=list)
    files_scanned: int = 0
    scan_duration: float = 0.0
    scan_timestamp: str = ""
    errors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if not self.scan_timestamp:
            self.scan_timestamp = datetime.utcnow().isoformat()

    @property
    def finding_count(self) -> int:
        """Total number of findings."""
        return len(self.findings)

    @property
    def critical_count(self) -> int:
        """Number of critical findings."""
        return sum(1 for f in self.findings if f.severity == PatternSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        """Number of high severity findings."""
        return sum(1 for f in self.findings if f.severity == PatternSeverity.HIGH)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary": {
                "total_findings": self.finding_count,
                "critical": self.critical_count,
                "high": self.high_count,
                "files_scanned": self.files_scanned,
                "scan_duration": self.scan_duration,
                "timestamp": self.scan_timestamp,
            },
            "findings": [f.to_dict() for f in self.findings],
            "errors": self.errors,
        }

    def to_sarif(self) -> Dict[str, Any]:
        """Convert to SARIF format."""
        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "devCrew_s1 Secret Scanner",
                            "version": "1.0.0",
                            "informationUri": "https://github.com/devCrew_s1/secrets_scanner",
                            "rules": self._get_sarif_rules(),
                        }
                    },
                    "results": [f.to_sarif() for f in self.findings],
                    "invocations": [
                        {
                            "executionSuccessful": len(self.errors) == 0,
                            "endTimeUtc": self.scan_timestamp,
                        }
                    ],
                }
            ],
        }

    def _get_sarif_rules(self) -> List[Dict]:
        """Generate SARIF rules from findings."""
        rules = {}
        for f in self.findings:
            if f.pattern_name not in rules:
                rules[f.pattern_name] = {
                    "id": f.pattern_name,
                    "shortDescription": {"text": f.pattern_description},
                    "defaultConfiguration": {
                        "level": f._severity_to_sarif_level()
                    },
                    "properties": {"category": f.category},
                }
        return list(rules.values())


class SecretScanner:
    """Main secret scanning engine."""

    DEFAULT_EXCLUDED_EXTENSIONS: Set[str] = {
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
        ".zip", ".tar", ".gz", ".rar", ".7z",
        ".exe", ".dll", ".so", ".dylib",
        ".pyc", ".pyo", ".class", ".o",
        ".mp3", ".mp4", ".avi", ".mov",
        ".woff", ".woff2", ".ttf", ".eot",
    }

    DEFAULT_EXCLUDED_DIRS: Set[str] = {
        ".git", ".svn", ".hg",
        "node_modules", "__pycache__", ".venv", "venv",
        ".idea", ".vscode",
        "dist", "build", ".tox", ".eggs",
    }

    def __init__(
        self,
        pattern_manager: Optional[PatternManager] = None,
        excluded_extensions: Optional[Set[str]] = None,
        excluded_dirs: Optional[Set[str]] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        entropy_threshold: float = 4.5,
    ) -> None:
        """Initialize the scanner."""
        self.pattern_manager = pattern_manager or PatternManager()
        self.excluded_extensions = excluded_extensions or self.DEFAULT_EXCLUDED_EXTENSIONS
        self.excluded_dirs = excluded_dirs or self.DEFAULT_EXCLUDED_DIRS
        self.max_file_size = max_file_size
        self.entropy_threshold = entropy_threshold

    def calculate_shannon_entropy(self, data: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not data:
            return 0.0

        entropy = 0.0
        for char in set(data):
            p_x = data.count(char) / len(data)
            if p_x > 0:
                entropy -= p_x * math.log2(p_x)
        return entropy

    def is_high_entropy(self, text: str, threshold: Optional[float] = None) -> bool:
        """Check if text has high entropy indicating a potential secret."""
        threshold = threshold or self.entropy_threshold
        return self.calculate_shannon_entropy(text) >= threshold

    def scan_content(
        self,
        content: str,
        file_path: str = "<string>",
        patterns: Optional[List[SecretPattern]] = None,
    ) -> List[SecretFinding]:
        """Scan content string for secrets."""
        findings: List[SecretFinding] = []
        patterns = patterns or self.pattern_manager.get_all_patterns()
        lines = content.split("\n")

        for pattern in patterns:
            if pattern.compiled is None:
                continue

            for match in pattern.compiled.finditer(content):
                matched_text = match.group(0)
                line_num = content[:match.start()].count("\n") + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""

                # Calculate entropy
                entropy = self.calculate_shannon_entropy(matched_text)

                # Skip if pattern requires high entropy but match is low entropy
                if pattern.entropy_threshold and entropy < pattern.entropy_threshold:
                    continue

                finding = SecretFinding(
                    pattern_name=pattern.name,
                    pattern_description=pattern.description,
                    severity=pattern.severity,
                    file_path=file_path,
                    line_number=line_num,
                    line_content=line_content,
                    matched_text=matched_text,
                    entropy=entropy,
                    category=pattern.category,
                )
                findings.append(finding)

        return findings

    def scan_file(self, file_path: str | Path) -> List[SecretFinding]:
        """Scan a single file for secrets."""
        file_path = Path(file_path)

        if not file_path.exists():
            return []

        if not file_path.is_file():
            return []

        # Check exclusions
        if file_path.suffix.lower() in self.excluded_extensions:
            return []

        # Check file size
        try:
            if file_path.stat().st_size > self.max_file_size:
                return []
        except OSError:
            return []

        # Read and scan content
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            return self.scan_content(content, str(file_path))
        except (OSError, UnicodeDecodeError):
            return []

    def scan_directory(
        self,
        directory: str | Path,
        recursive: bool = True,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> ScanResult:
        """Scan a directory for secrets."""
        import time

        start_time = time.time()
        directory = Path(directory)
        result = ScanResult()

        if not directory.exists():
            result.errors.append(f"Directory not found: {directory}")
            return result

        if not directory.is_dir():
            result.errors.append(f"Not a directory: {directory}")
            return result

        # Compile include/exclude patterns
        include_compiled = None
        exclude_compiled = None
        if include_patterns:
            include_compiled = [re.compile(p) for p in include_patterns]
        if exclude_patterns:
            exclude_compiled = [re.compile(p) for p in exclude_patterns]

        # Walk directory
        if recursive:
            files = directory.rglob("*")
        else:
            files = directory.glob("*")

        for file_path in files:
            # Skip directories
            if file_path.is_dir():
                continue

            # Check if any parent is excluded
            if any(part in self.excluded_dirs for part in file_path.parts):
                continue

            # Check include patterns
            if include_compiled:
                if not any(p.search(str(file_path)) for p in include_compiled):
                    continue

            # Check exclude patterns
            if exclude_compiled:
                if any(p.search(str(file_path)) for p in exclude_compiled):
                    continue

            try:
                findings = self.scan_file(file_path)
                result.findings.extend(findings)
                result.files_scanned += 1
            except Exception as e:
                result.errors.append(f"Error scanning {file_path}: {e}")

        result.scan_duration = time.time() - start_time
        return result

    def scan_high_entropy_strings(
        self,
        content: str,
        file_path: str = "<string>",
        min_length: int = 20,
        max_length: int = 200,
    ) -> List[SecretFinding]:
        """Scan for high-entropy strings that might be secrets."""
        findings: List[SecretFinding] = []
        lines = content.split("\n")

        # Pattern to find potential secret strings
        string_pattern = re.compile(r'["\']([a-zA-Z0-9+/=_\-]{' + str(min_length) + ',' + str(max_length) + r'})["\']')

        for line_num, line in enumerate(lines, 1):
            for match in string_pattern.finditer(line):
                candidate = match.group(1)
                entropy = self.calculate_shannon_entropy(candidate)

                if entropy >= self.entropy_threshold:
                    finding = SecretFinding(
                        pattern_name="high_entropy_string",
                        pattern_description="High-entropy string (potential secret)",
                        severity=PatternSeverity.MEDIUM,
                        file_path=file_path,
                        line_number=line_num,
                        line_content=line,
                        matched_text=candidate,
                        entropy=entropy,
                        category="entropy",
                    )
                    findings.append(finding)

        return findings

    def deduplicate_findings(
        self, findings: List[SecretFinding]
    ) -> List[SecretFinding]:
        """Remove duplicate findings based on hash."""
        seen: Set[str] = set()
        unique: List[SecretFinding] = []

        for finding in findings:
            if finding.hash_value not in seen:
                seen.add(finding.hash_value)
                unique.append(finding)

        return unique

    def filter_findings(
        self,
        findings: List[SecretFinding],
        min_severity: Optional[PatternSeverity] = None,
        categories: Optional[List[str]] = None,
        exclude_false_positives: bool = True,
    ) -> List[SecretFinding]:
        """Filter findings by criteria."""
        severity_order = {
            PatternSeverity.LOW: 0,
            PatternSeverity.MEDIUM: 1,
            PatternSeverity.HIGH: 2,
            PatternSeverity.CRITICAL: 3,
        }

        filtered = findings

        if exclude_false_positives:
            filtered = [f for f in filtered if not f.is_false_positive]

        if min_severity:
            min_order = severity_order[min_severity]
            filtered = [f for f in filtered if severity_order[f.severity] >= min_order]

        if categories:
            filtered = [f for f in filtered if f.category in categories]

        return filtered
