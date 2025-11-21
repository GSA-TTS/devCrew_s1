"""
Baseline Manager for tracking known secrets and false positives.

Supports .secrets.baseline JSON format with versioning.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .secret_scanner import ScanResult, SecretFinding


@dataclass
class BaselineEntry:
    """Entry in the baseline file."""

    hash_value: str
    pattern_name: str
    file_path: str
    line_number: int
    is_false_positive: bool = False
    reason: str = ""
    added_date: str = ""
    added_by: str = ""

    def __post_init__(self) -> None:
        """Set default date."""
        if not self.added_date:
            self.added_date = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hash": self.hash_value,
            "pattern_name": self.pattern_name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "is_false_positive": self.is_false_positive,
            "reason": self.reason,
            "added_date": self.added_date,
            "added_by": self.added_by,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaselineEntry":
        """Create from dictionary."""
        return cls(
            hash_value=data["hash"],
            pattern_name=data["pattern_name"],
            file_path=data["file_path"],
            line_number=data["line_number"],
            is_false_positive=data.get("is_false_positive", False),
            reason=data.get("reason", ""),
            added_date=data.get("added_date", ""),
            added_by=data.get("added_by", ""),
        )


@dataclass
class Baseline:
    """Secrets baseline configuration."""

    version: str = "1.0.0"
    generated_at: str = ""
    entries: List[BaselineEntry] = field(default_factory=list)
    plugins_used: List[str] = field(default_factory=list)
    filters_used: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Set defaults."""
        if not self.generated_at:
            self.generated_at = datetime.utcnow().isoformat()

    @property
    def entry_count(self) -> int:
        """Number of entries."""
        return len(self.entries)

    @property
    def false_positive_count(self) -> int:
        """Number of false positives."""
        return sum(1 for e in self.entries if e.is_false_positive)

    def get_hashes(self) -> Set[str]:
        """Get all hashes in baseline."""
        return {e.hash_value for e in self.entries}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "plugins_used": self.plugins_used,
            "filters_used": self.filters_used,
            "results": {
                e.file_path: [e.to_dict() for e in self.entries if e.file_path == e.file_path]
                for e in self.entries
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Baseline":
        """Create from dictionary."""
        entries = []
        results = data.get("results", {})
        for file_entries in results.values():
            if isinstance(file_entries, list):
                for entry_data in file_entries:
                    entries.append(BaselineEntry.from_dict(entry_data))

        return cls(
            version=data.get("version", "1.0.0"),
            generated_at=data.get("generated_at", ""),
            entries=entries,
            plugins_used=data.get("plugins_used", []),
            filters_used=data.get("filters_used", []),
        )


class BaselineManager:
    """Manages baseline files for secret scanning."""

    DEFAULT_FILENAME = ".secrets.baseline"

    def __init__(self, baseline_path: Optional[str | Path] = None) -> None:
        """Initialize baseline manager."""
        self.baseline_path = Path(baseline_path) if baseline_path else None
        self._baseline: Optional[Baseline] = None

    @property
    def baseline(self) -> Baseline:
        """Get or create baseline."""
        if self._baseline is None:
            self._baseline = Baseline()
        return self._baseline

    def load(self, path: Optional[str | Path] = None) -> Baseline:
        """Load baseline from file."""
        path = Path(path) if path else self.baseline_path
        if not path:
            raise ValueError("No baseline path specified")

        if not path.exists():
            self._baseline = Baseline()
            return self._baseline

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._baseline = Baseline.from_dict(data)
        self.baseline_path = path
        return self._baseline

    def save(self, path: Optional[str | Path] = None) -> None:
        """Save baseline to file."""
        path = Path(path) if path else self.baseline_path
        if not path:
            raise ValueError("No baseline path specified")

        self.baseline.generated_at = datetime.utcnow().isoformat()

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.baseline.to_dict(), f, indent=2)

        self.baseline_path = path

    def create_from_scan(self, scan_result: ScanResult) -> Baseline:
        """Create baseline from scan results."""
        entries = []
        for finding in scan_result.findings:
            entry = BaselineEntry(
                hash_value=finding.hash_value,
                pattern_name=finding.pattern_name,
                file_path=finding.file_path,
                line_number=finding.line_number,
            )
            entries.append(entry)

        self._baseline = Baseline(entries=entries)
        return self._baseline

    def update_from_scan(
        self, scan_result: ScanResult, keep_removed: bool = False
    ) -> Baseline:
        """Update baseline with new scan results."""
        existing_hashes = self.baseline.get_hashes()
        new_findings_hashes = {f.hash_value for f in scan_result.findings}

        # Add new findings
        for finding in scan_result.findings:
            if finding.hash_value not in existing_hashes:
                entry = BaselineEntry(
                    hash_value=finding.hash_value,
                    pattern_name=finding.pattern_name,
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                )
                self.baseline.entries.append(entry)

        # Remove entries not in scan (unless keeping removed)
        if not keep_removed:
            self.baseline.entries = [
                e for e in self.baseline.entries
                if e.hash_value in new_findings_hashes or e.is_false_positive
            ]

        return self.baseline

    def add_false_positive(
        self,
        hash_value: str,
        reason: str = "",
        added_by: str = "",
    ) -> bool:
        """Mark an entry as false positive."""
        for entry in self.baseline.entries:
            if entry.hash_value == hash_value:
                entry.is_false_positive = True
                entry.reason = reason
                entry.added_by = added_by
                return True

        return False

    def remove_false_positive(self, hash_value: str) -> bool:
        """Remove false positive marking."""
        for entry in self.baseline.entries:
            if entry.hash_value == hash_value:
                entry.is_false_positive = False
                entry.reason = ""
                return True

        return False

    def is_baselined(self, finding: SecretFinding) -> bool:
        """Check if a finding is in the baseline."""
        return finding.hash_value in self.baseline.get_hashes()

    def is_false_positive(self, finding: SecretFinding) -> bool:
        """Check if a finding is marked as false positive."""
        for entry in self.baseline.entries:
            if entry.hash_value == finding.hash_value:
                return entry.is_false_positive
        return False

    def filter_baselined(
        self,
        findings: List[SecretFinding],
        include_false_positives: bool = False,
    ) -> List[SecretFinding]:
        """Filter out baselined findings."""
        hashes = self.baseline.get_hashes()
        fp_hashes = {e.hash_value for e in self.baseline.entries if e.is_false_positive}

        filtered = []
        for finding in findings:
            if finding.hash_value in hashes:
                if include_false_positives and finding.hash_value in fp_hashes:
                    continue
                elif not include_false_positives:
                    continue
            filtered.append(finding)

        return filtered

    def get_new_findings(
        self, scan_result: ScanResult
    ) -> List[SecretFinding]:
        """Get findings not in baseline."""
        return self.filter_baselined(scan_result.findings)

    def get_removed_findings(
        self, scan_result: ScanResult
    ) -> List[BaselineEntry]:
        """Get baseline entries not found in scan."""
        scan_hashes = {f.hash_value for f in scan_result.findings}
        return [
            e for e in self.baseline.entries
            if e.hash_value not in scan_hashes and not e.is_false_positive
        ]

    def audit_baseline(self, scan_result: ScanResult) -> Dict[str, Any]:
        """Audit baseline against scan results."""
        new_findings = self.get_new_findings(scan_result)
        removed = self.get_removed_findings(scan_result)

        return {
            "total_in_baseline": self.baseline.entry_count,
            "false_positives": self.baseline.false_positive_count,
            "new_secrets_found": len(new_findings),
            "secrets_removed": len(removed),
            "new_findings": [f.to_dict() for f in new_findings],
            "removed_entries": [e.to_dict() for e in removed],
        }

    def generate_hash(
        self,
        pattern_name: str,
        file_path: str,
        matched_text: str,
    ) -> str:
        """Generate hash for a potential finding."""
        content = f"{pattern_name}:{file_path}:{matched_text}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def export_false_positives(self) -> List[Dict[str, Any]]:
        """Export all false positive entries."""
        return [
            e.to_dict() for e in self.baseline.entries
            if e.is_false_positive
        ]

    def import_false_positives(
        self, false_positives: List[Dict[str, Any]]
    ) -> int:
        """Import false positive entries."""
        count = 0
        existing_hashes = self.baseline.get_hashes()

        for fp in false_positives:
            entry = BaselineEntry.from_dict(fp)
            entry.is_false_positive = True

            if entry.hash_value not in existing_hashes:
                self.baseline.entries.append(entry)
                count += 1

        return count
