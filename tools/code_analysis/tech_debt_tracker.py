"""
Technical Debt Tracker Module.

Tracks, categorizes, and prioritizes technical debt items
discovered during code analysis.
"""

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional


class DebtPriority(Enum):
    """Priority levels for technical debt."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class DebtCategory(Enum):
    """Categories of technical debt."""

    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    DEPENDENCY = "dependency"


@dataclass
class TechDebtItem:
    """Represents a technical debt item."""

    id: str
    title: str
    description: str
    category: DebtCategory
    priority: DebtPriority
    location: str
    lineno: int
    estimated_hours: float = 0.0
    created_at: str = ""
    tags: List[str] = field(default_factory=list)
    source: str = ""  # How it was discovered (manual, automated, etc.)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority.name,
            "priority_value": self.priority.value,
            "location": self.location,
            "lineno": self.lineno,
            "estimated_hours": self.estimated_hours,
            "created_at": self.created_at,
            "tags": self.tags,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TechDebtItem":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            title=data["title"],
            description=data["description"],
            category=DebtCategory(data["category"]),
            priority=DebtPriority[data["priority"]],
            location=data["location"],
            lineno=data["lineno"],
            estimated_hours=data.get("estimated_hours", 0.0),
            created_at=data.get("created_at", ""),
            tags=data.get("tags", []),
            source=data.get("source", ""),
        )


class TechDebtTracker:
    """Tracks and manages technical debt items."""

    # TODO/FIXME patterns with priority indicators
    TODO_PATTERNS = [
        (r"#\s*TODO[:\s](.+)$", DebtPriority.MEDIUM),
        (r"#\s*FIXME[:\s](.+)$", DebtPriority.HIGH),
        (r"#\s*HACK[:\s](.+)$", DebtPriority.HIGH),
        (r"#\s*XXX[:\s](.+)$", DebtPriority.MEDIUM),
        (r"#\s*BUG[:\s](.+)$", DebtPriority.CRITICAL),
        (r"#\s*OPTIMIZE[:\s](.+)$", DebtPriority.LOW),
        (r"#\s*REFACTOR[:\s](.+)$", DebtPriority.MEDIUM),
    ]

    def __init__(self, storage_path: Optional[str | Path] = None) -> None:
        """
        Initialize tracker.

        Args:
            storage_path: Optional path to store debt items persistently
        """
        self.items: List[TechDebtItem] = []
        self.storage_path = Path(storage_path) if storage_path else None
        if self.storage_path and self.storage_path.exists():
            self._load()

    def add_item(self, item: TechDebtItem) -> str:
        """
        Add a technical debt item.

        Args:
            item: The debt item to add

        Returns:
            The item's ID
        """
        self.items.append(item)
        self._save()
        return item.id

    def remove_item(self, item_id: str) -> bool:
        """
        Remove a technical debt item.

        Args:
            item_id: ID of item to remove

        Returns:
            True if removed, False if not found
        """
        for i, item in enumerate(self.items):
            if item.id == item_id:
                del self.items[i]
                self._save()
                return True
        return False

    def get_item(self, item_id: str) -> Optional[TechDebtItem]:
        """Get an item by ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def scan_file(self, filepath: str | Path) -> List[TechDebtItem]:
        """
        Scan a file for TODO/FIXME comments and create debt items.

        Args:
            filepath: Path to file to scan

        Returns:
            List of discovered debt items
        """
        filepath = Path(filepath)
        if not filepath.exists():
            return []

        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            return []

        discovered = []
        for lineno, line in enumerate(content.splitlines(), 1):
            for pattern, priority in self.TODO_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    comment_text = match.group(1).strip()
                    tag = pattern.split(r"\s*")[0].split("#")[-1].strip("\\")

                    item = TechDebtItem(
                        id="",
                        title=f"{tag}: {comment_text[:50]}...",
                        description=comment_text,
                        category=self._categorize_from_tag(tag),
                        priority=priority,
                        location=str(filepath),
                        lineno=lineno,
                        tags=[tag.lower()],
                        source="automated_scan",
                    )
                    discovered.append(item)
                    self.items.append(item)

        self._save()
        return discovered

    def scan_directory(
        self,
        directory: str | Path,
        extensions: Optional[List[str]] = None,
    ) -> List[TechDebtItem]:
        """
        Scan a directory recursively for debt items.

        Args:
            directory: Directory to scan
            extensions: File extensions to include (default: .py)

        Returns:
            List of all discovered debt items
        """
        directory = Path(directory)
        extensions = extensions or [".py"]
        discovered = []

        for ext in extensions:
            for filepath in directory.rglob(f"*{ext}"):
                discovered.extend(self.scan_file(filepath))

        return discovered

    def import_from_analysis(
        self,
        smells: List[Dict[str, Any]],
        complexity_violations: List[Dict[str, Any]],
    ) -> List[TechDebtItem]:
        """
        Import debt items from code analysis results.

        Args:
            smells: Code smells from CodeSmellDetector
            complexity_violations: Violations from ComplexityAnalyzer

        Returns:
            List of created debt items
        """
        created = []

        # Import code smells
        for smell in smells:
            priority = self._severity_to_priority(smell.get("severity", "medium"))
            item = TechDebtItem(
                id="",
                title=f"Code Smell: {smell['name']}",
                description=smell["description"],
                category=DebtCategory.CODE_QUALITY,
                priority=priority,
                location=smell["location"],
                lineno=smell["lineno"],
                estimated_hours=self._estimate_hours(smell["name"]),
                tags=[smell["name"], "code_smell"],
                source="code_smell_detector",
            )
            self.items.append(item)
            created.append(item)

        # Import complexity violations
        for violation in complexity_violations:
            item = TechDebtItem(
                id="",
                title=f"Complexity: {violation['type']}",
                description=(
                    f"{violation['function']} has {violation['type']} of "
                    f"{violation['value']} (threshold: {violation['threshold']})"
                ),
                category=DebtCategory.MAINTAINABILITY,
                priority=DebtPriority.HIGH,
                location=violation.get("file", "unknown"),
                lineno=violation["lineno"],
                estimated_hours=2.0,
                tags=[violation["type"], "complexity"],
                source="complexity_analyzer",
            )
            self.items.append(item)
            created.append(item)

        self._save()
        return created

    def get_prioritized(self) -> List[TechDebtItem]:
        """Get items sorted by priority (highest first)."""
        return sorted(self.items, key=lambda x: x.priority.value, reverse=True)

    def get_by_category(self, category: DebtCategory) -> List[TechDebtItem]:
        """Get items filtered by category."""
        return [item for item in self.items if item.category == category]

    def get_by_location(self, location_pattern: str) -> List[TechDebtItem]:
        """Get items filtered by location pattern."""
        return [
            item for item in self.items
            if location_pattern in item.location
        ]

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        by_priority = {p.name: 0 for p in DebtPriority}
        by_category = {c.value: 0 for c in DebtCategory}
        total_hours = 0.0

        for item in self.items:
            by_priority[item.priority.name] += 1
            by_category[item.category.value] += 1
            total_hours += item.estimated_hours

        return {
            "total_items": len(self.items),
            "by_priority": by_priority,
            "by_category": by_category,
            "total_estimated_hours": round(total_hours, 1),
            "critical_count": by_priority["CRITICAL"],
            "high_count": by_priority["HIGH"],
        }

    def to_dict(self) -> Dict[str, Any]:
        """Export all items as dictionary."""
        return {
            "items": [item.to_dict() for item in self.items],
            "summary": self.get_summary(),
        }

    def _categorize_from_tag(self, tag: str) -> DebtCategory:
        """Determine category from comment tag."""
        tag_lower = tag.lower()
        if tag_lower in ("bug", "fixme"):
            return DebtCategory.CODE_QUALITY
        if tag_lower == "optimize":
            return DebtCategory.PERFORMANCE
        if tag_lower == "refactor":
            return DebtCategory.MAINTAINABILITY
        if tag_lower == "hack":
            return DebtCategory.ARCHITECTURE
        return DebtCategory.CODE_QUALITY

    def _severity_to_priority(self, severity: str) -> DebtPriority:
        """Convert severity string to priority."""
        mapping = {
            "low": DebtPriority.LOW,
            "medium": DebtPriority.MEDIUM,
            "high": DebtPriority.HIGH,
            "critical": DebtPriority.CRITICAL,
        }
        return mapping.get(severity.lower(), DebtPriority.MEDIUM)

    def _estimate_hours(self, smell_name: str) -> float:
        """Estimate hours to fix based on smell type."""
        estimates = {
            "long_method": 2.0,
            "large_class": 4.0,
            "god_class": 8.0,
            "too_many_parameters": 1.0,
            "deep_nesting": 1.5,
            "feature_envy": 2.0,
            "too_many_methods": 3.0,
            "too_many_attributes": 2.0,
            "too_many_branches": 1.5,
            "too_many_returns": 1.0,
            "too_many_variables": 1.0,
        }
        return estimates.get(smell_name, 1.0)

    def _save(self) -> None:
        """Save items to storage if configured."""
        if self.storage_path:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)

    def _load(self) -> None:
        """Load items from storage."""
        if self.storage_path and self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    content = f.read().strip()
                    if not content:
                        return
                    data = json.loads(content)
                    self.items = [
                        TechDebtItem.from_dict(item)
                        for item in data.get("items", [])
                    ]
            except json.JSONDecodeError:
                # Handle invalid/empty JSON files
                pass
