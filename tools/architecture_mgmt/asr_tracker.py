"""
ASR Tracker - Architecture Significant Requirements Extraction & Tracking
Issue #40: TOOL-ARCH-001

Provides ASR management capabilities:
- Extract ASRs from GitHub issues
- Map ASRs to ADRs
- Track ASR implementation status
- Generate traceability matrix
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from github import Github


@dataclass
class ASR:
    """Architecture Significant Requirement."""

    id: str
    title: str
    description: str
    category: str  # performance, security, scalability, reliability, etc.
    priority: str  # HIGH, MEDIUM, LOW
    source: str  # GitHub issue, requirement doc, etc.
    status: str  # identified, analyzed, addressed, verified
    related_adrs: List[int] = field(default_factory=list)
    rationale: Optional[str] = None
    constraints: Optional[List[str]] = None
    quality_attributes: Optional[List[str]] = None
    created_date: Optional[str] = None
    updated_date: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert ASR to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "source": self.source,
            "status": self.status,
            "related_adrs": self.related_adrs,
            "rationale": self.rationale,
            "constraints": self.constraints,
            "quality_attributes": self.quality_attributes,
            "created_date": self.created_date,
            "updated_date": self.updated_date,
        }


class ASRExtractor:
    """Extracts Architecture Significant Requirements from various sources."""

    # Keywords that indicate architectural significance
    ARCH_KEYWORDS = [
        "performance",
        "scalability",
        "security",
        "reliability",
        "availability",
        "maintainability",
        "testability",
        "deployability",
        "architecture",
        "quality attribute",
        "non-functional",
        "throughput",
        "latency",
        "response time",
        "concurrent",
        "distributed",
        "fault tolerance",
        "disaster recovery",
        "compliance",
        "audit",
        "monitoring",
        "logging",
    ]

    # Category mappings
    CATEGORY_KEYWORDS = {
        "performance": ["performance", "latency", "throughput", "response time", "speed"],
        "security": ["security", "authentication", "authorization", "encryption", "audit"],
        "scalability": ["scalability", "scale", "concurrent", "distributed", "load"],
        "reliability": ["reliability", "availability", "fault tolerance", "disaster recovery"],
        "maintainability": ["maintainability", "testability", "deployability", "modularity"],
        "compliance": ["compliance", "regulation", "standard", "policy"],
        "observability": ["monitoring", "logging", "metrics", "tracing", "alerting"],
    }

    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize ASR extractor.

        Args:
            github_token: GitHub personal access token
        """
        self.github_token = github_token
        self.github = Github(github_token) if github_token else None

    def extract_from_github_issue(self, repo_name: str, issue_number: int) -> Optional[ASR]:
        """
        Extract ASR from GitHub issue.

        Args:
            repo_name: Repository name (owner/repo)
            issue_number: Issue number

        Returns:
            ASR object or None if not architecturally significant
        """
        if not self.github:
            raise ValueError("GitHub token required for issue extraction")

        try:
            repo = self.github.get_repo(repo_name)
            issue = repo.get_issue(issue_number)

            # Check if issue is architecturally significant
            if not self._is_architecturally_significant(issue.title, issue.body or ""):
                return None

            # Extract ASR details
            category = self._categorize_requirement(issue.title, issue.body or "")
            priority = self._extract_priority(issue.labels)

            asr = ASR(
                id=f"ASR-{issue_number:03d}",
                title=issue.title,
                description=issue.body or "",
                category=category,
                priority=priority,
                source=f"GitHub Issue #{issue_number}",
                status="identified",
                created_date=issue.created_at.strftime("%Y-%m-%d"),
                updated_date=issue.updated_at.strftime("%Y-%m-%d"),
            )

            # Extract quality attributes
            asr.quality_attributes = self._extract_quality_attributes(
                issue.title, issue.body or ""
            )

            # Extract constraints
            asr.constraints = self._extract_constraints(issue.body or "")

            return asr

        except Exception as e:
            print(f"Error extracting ASR from issue: {e}")
            return None

    def _is_architecturally_significant(self, title: str, body: str) -> bool:
        """
        Determine if requirement is architecturally significant.

        Args:
            title: Issue title
            body: Issue body

        Returns:
            True if architecturally significant
        """
        text = f"{title} {body}".lower()

        # Check for architecture keywords
        for keyword in self.ARCH_KEYWORDS:
            if keyword in text:
                return True

        # Check for specific patterns
        patterns = [
            r"must\s+handle\s+\d+",  # Performance requirements
            r"shall\s+support",  # Formal requirements
            r"security\s+requirement",
            r"quality\s+attribute",
            r"non-functional",
        ]

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def _categorize_requirement(self, title: str, body: str) -> str:
        """
        Categorize requirement based on content.

        Args:
            title: Requirement title
            body: Requirement body

        Returns:
            Category name
        """
        text = f"{title} {body}".lower()

        # Count keyword matches for each category
        category_scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                category_scores[category] = score

        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)  # type: ignore

        return "general"

    def _extract_priority(self, labels) -> str:
        """
        Extract priority from issue labels.

        Args:
            labels: GitHub issue labels

        Returns:
            Priority level (HIGH, MEDIUM, LOW)
        """
        label_names = [label.name.lower() for label in labels]

        if any(p in label_names for p in ["critical", "high", "p0", "p1"]):
            return "HIGH"
        elif any(p in label_names for p in ["medium", "p2"]):
            return "MEDIUM"
        else:
            return "LOW"

    def _extract_quality_attributes(self, title: str, body: str) -> List[str]:
        """
        Extract quality attributes from text.

        Args:
            title: Requirement title
            body: Requirement body

        Returns:
            List of quality attributes
        """
        text = f"{title} {body}".lower()
        attributes = []

        quality_attrs = {
            "performance",
            "security",
            "scalability",
            "reliability",
            "availability",
            "maintainability",
            "testability",
            "usability",
            "portability",
        }

        for attr in quality_attrs:
            if attr in text:
                attributes.append(attr)

        return attributes

    def _extract_constraints(self, body: str) -> List[str]:
        """
        Extract constraints from requirement body.

        Args:
            body: Requirement body

        Returns:
            List of constraints
        """
        constraints = []

        # Look for constraint patterns
        patterns = [
            r"must\s+not\s+(.+?)(?:\.|$)",
            r"cannot\s+(.+?)(?:\.|$)",
            r"limited\s+to\s+(.+?)(?:\.|$)",
            r"constraint:\s*(.+?)(?:\.|$)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            constraints.extend(matches)

        return constraints[:5]  # Limit to 5 constraints

    def extract_from_text(
        self,
        text: str,
        title: str,
        source: str = "Manual",
        asr_id: Optional[str] = None,
    ) -> Optional[ASR]:
        """
        Extract ASR from free text.

        Args:
            text: Requirement text
            title: Requirement title
            source: Source of requirement
            asr_id: Optional ASR ID

        Returns:
            ASR object or None
        """
        if not self._is_architecturally_significant(title, text):
            return None

        category = self._categorize_requirement(title, text)

        # Generate ID if not provided
        if not asr_id:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            asr_id = f"ASR-{timestamp}"

        asr = ASR(
            id=asr_id,
            title=title,
            description=text,
            category=category,
            priority="MEDIUM",
            source=source,
            status="identified",
            created_date=datetime.now().strftime("%Y-%m-%d"),
        )

        asr.quality_attributes = self._extract_quality_attributes(title, text)
        asr.constraints = self._extract_constraints(text)

        return asr


class ASRTracker:
    """Tracks and manages ASRs."""

    def __init__(self, asr_dir: str = "docs/asr"):
        """
        Initialize ASR tracker.

        Args:
            asr_dir: Directory to store ASR files
        """
        self.asr_dir = Path(asr_dir)
        self.asr_dir.mkdir(parents=True, exist_ok=True)

    def save_asr(self, asr: ASR) -> None:
        """
        Save ASR to file.

        Args:
            asr: ASR object to save
        """
        filename = f"{asr.id}.md"
        filepath = self.asr_dir / filename

        content = self._generate_asr_content(asr)
        filepath.write_text(content)

        # Also save as YAML for easier processing
        yaml_file = self.asr_dir / f"{asr.id}.yml"
        with open(yaml_file, "w") as f:
            yaml.dump(asr.to_dict(), f, default_flow_style=False)

    def _generate_asr_content(self, asr: ASR) -> str:
        """Generate markdown content for ASR."""
        lines = [f"# {asr.id}: {asr.title}\n"]
        lines.append(f"**Category**: {asr.category}\n")
        lines.append(f"**Priority**: {asr.priority}\n")
        lines.append(f"**Status**: {asr.status}\n")
        lines.append(f"**Source**: {asr.source}\n")

        if asr.created_date:
            lines.append(f"**Created**: {asr.created_date}\n")
        if asr.updated_date:
            lines.append(f"**Updated**: {asr.updated_date}\n")

        lines.append("\n## Description\n\n")
        lines.append(f"{asr.description}\n\n")

        if asr.quality_attributes:
            lines.append("## Quality Attributes\n\n")
            for attr in asr.quality_attributes:
                lines.append(f"- {attr}\n")
            lines.append("\n")

        if asr.constraints:
            lines.append("## Constraints\n\n")
            for constraint in asr.constraints:
                lines.append(f"- {constraint}\n")
            lines.append("\n")

        if asr.rationale:
            lines.append("## Rationale\n\n")
            lines.append(f"{asr.rationale}\n\n")

        if asr.related_adrs:
            lines.append("## Related ADRs\n\n")
            for adr_num in asr.related_adrs:
                lines.append(f"- [ADR-{adr_num:03d}](../adr/ADR-{adr_num:03d}.md)\n")
            lines.append("\n")

        return "".join(lines)

    def load_asr(self, asr_id: str) -> Optional[ASR]:
        """
        Load ASR from file.

        Args:
            asr_id: ASR ID

        Returns:
            ASR object or None
        """
        yaml_file = self.asr_dir / f"{asr_id}.yml"

        if not yaml_file.exists():
            return None

        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)
            return ASR(**data)
        except Exception:
            return None

    def list_asrs(
        self, category: Optional[str] = None, status: Optional[str] = None
    ) -> List[ASR]:
        """
        List all ASRs with optional filters.

        Args:
            category: Filter by category
            status: Filter by status

        Returns:
            List of ASR objects
        """
        asrs = []

        for yaml_file in self.asr_dir.glob("ASR-*.yml"):
            asr = self.load_asr(yaml_file.stem)
            if asr:
                if category and asr.category != category:
                    continue
                if status and asr.status != status:
                    continue
                asrs.append(asr)

        return sorted(asrs, key=lambda x: x.id)

    def link_asr_to_adr(self, asr_id: str, adr_number: int) -> bool:
        """
        Link ASR to an ADR.

        Args:
            asr_id: ASR ID
            adr_number: ADR number

        Returns:
            True if successful
        """
        asr = self.load_asr(asr_id)
        if not asr:
            return False

        if adr_number not in asr.related_adrs:
            asr.related_adrs.append(adr_number)
            asr.updated_date = datetime.now().strftime("%Y-%m-%d")
            self.save_asr(asr)

        return True

    def update_status(self, asr_id: str, new_status: str) -> bool:
        """
        Update ASR status.

        Args:
            asr_id: ASR ID
            new_status: New status

        Returns:
            True if successful
        """
        asr = self.load_asr(asr_id)
        if not asr:
            return False

        asr.status = new_status
        asr.updated_date = datetime.now().strftime("%Y-%m-%d")
        self.save_asr(asr)

        return True

    def generate_traceability_matrix(self, output_file: Optional[str] = None) -> str:
        """
        Generate ASR-to-ADR traceability matrix.

        Args:
            output_file: Optional output file path

        Returns:
            Traceability matrix as markdown string
        """
        asrs = self.list_asrs()

        lines = ["# ASR-to-ADR Traceability Matrix\n\n"]
        lines.append("| ASR ID | Title | Category | Priority | Related ADRs | Status |\n")
        lines.append("|--------|-------|----------|----------|--------------|--------|\n")

        for asr in asrs:
            adr_links = ", ".join(
                [f"[ADR-{n:03d}](../adr/ADR-{n:03d}.md)" for n in asr.related_adrs]
            ) if asr.related_adrs else "None"

            lines.append(
                f"| {asr.id} | {asr.title} | {asr.category} | "
                f"{asr.priority} | {adr_links} | {asr.status} |\n"
            )

        content = "".join(lines)

        if output_file:
            Path(output_file).write_text(content)

        return content

    def generate_summary_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate ASR summary report.

        Args:
            output_file: Optional output file path

        Returns:
            Summary report as markdown string
        """
        asrs = self.list_asrs()

        lines = ["# ASR Summary Report\n\n"]
        lines.append(f"**Total ASRs**: {len(asrs)}\n\n")

        # Group by category
        categories = {}
        for asr in asrs:
            if asr.category not in categories:
                categories[asr.category] = []
            categories[asr.category].append(asr)

        lines.append("## By Category\n\n")
        for category, cat_asrs in sorted(categories.items()):
            lines.append(f"- **{category}**: {len(cat_asrs)}\n")

        # Group by status
        statuses = {}
        for asr in asrs:
            if asr.status not in statuses:
                statuses[asr.status] = []
            statuses[asr.status].append(asr)

        lines.append("\n## By Status\n\n")
        for status, status_asrs in sorted(statuses.items()):
            lines.append(f"- **{status}**: {len(status_asrs)}\n")

        # Group by priority
        priorities = {}
        for asr in asrs:
            if asr.priority not in priorities:
                priorities[asr.priority] = []
            priorities[asr.priority].append(asr)

        lines.append("\n## By Priority\n\n")
        for priority in ["HIGH", "MEDIUM", "LOW"]:
            if priority in priorities:
                lines.append(f"- **{priority}**: {len(priorities[priority])}\n")

        # Coverage analysis
        linked_asrs = [asr for asr in asrs if asr.related_adrs]
        coverage = (len(linked_asrs) / len(asrs) * 100) if asrs else 0

        lines.append(f"\n## ADR Coverage\n\n")
        lines.append(f"- **ASRs with ADRs**: {len(linked_asrs)}/{len(asrs)}\n")
        lines.append(f"- **Coverage**: {coverage:.1f}%\n")

        content = "".join(lines)

        if output_file:
            Path(output_file).write_text(content)

        return content
