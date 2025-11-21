"""
ADR Manager - Architecture Decision Record Management
Issue #40: TOOL-ARCH-001

Provides CRUD operations for Architecture Decision Records with:
- Create, update, supersede, amend ADRs
- Template-based ADR creation
- GitHub issue linking
- ADR versioning and history
- Index generation
"""

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import frontmatter
import yaml
from jinja2 import Environment, FileSystemLoader


@dataclass
class ADR:
    """Architecture Decision Record data structure."""

    number: int
    title: str
    status: str  # proposed, accepted, rejected, superseded, deprecated, amended
    date: str
    deciders: List[str]
    context: str
    decision: str
    consequences: str
    technical_story: Optional[str] = None
    decision_drivers: Optional[List[str]] = None
    considered_options: Optional[List[str]] = None
    supersedes: Optional[List[int]] = None
    superseded_by: Optional[int] = None
    amended_by: Optional[List[int]] = None
    related_adrs: Optional[List[int]] = None
    compliance: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        """Convert ADR to dictionary."""
        return {
            "number": self.number,
            "title": self.title,
            "status": self.status,
            "date": self.date,
            "deciders": self.deciders,
            "context": self.context,
            "decision": self.decision,
            "consequences": self.consequences,
            "technical_story": self.technical_story,
            "decision_drivers": self.decision_drivers,
            "considered_options": self.considered_options,
            "supersedes": self.supersedes,
            "superseded_by": self.superseded_by,
            "amended_by": self.amended_by,
            "related_adrs": self.related_adrs,
            "compliance": self.compliance,
            "tags": self.tags,
        }


class ADRManager:
    """Manages Architecture Decision Records."""

    def __init__(self, adr_dir: str = "docs/adr", template_dir: Optional[str] = None):
        """
        Initialize ADR Manager.

        Args:
            adr_dir: Directory to store ADRs
            template_dir: Directory containing ADR templates
        """
        self.adr_dir = Path(adr_dir)
        self.adr_dir.mkdir(parents=True, exist_ok=True)

        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # Use default template directory
            script_dir = Path(__file__).parent
            self.template_dir = script_dir / "templates"

        self.template_env = Environment(
            loader=FileSystemLoader(str(self.template_dir))
            if self.template_dir.exists()
            else None
        )

    def get_next_adr_number(self) -> int:
        """Get the next available ADR number."""
        adr_files = list(self.adr_dir.glob("ADR-*.md"))
        if not adr_files:
            return 1

        numbers = []
        for f in adr_files:
            match = re.match(r"ADR-(\d+)\.md", f.name)
            if match:
                numbers.append(int(match.group(1)))

        return max(numbers) + 1 if numbers else 1

    def create(
        self,
        title: str,
        context: str,
        decision: str,
        consequences: str,
        status: str = "proposed",
        deciders: Optional[List[str]] = None,
        technical_story: Optional[str] = None,
        decision_drivers: Optional[List[str]] = None,
        considered_options: Optional[List[str]] = None,
        compliance: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        template: str = "default",
        supersedes: Optional[List[int]] = None,
    ) -> ADR:
        """
        Create a new ADR.

        Args:
            title: ADR title
            context: Context and problem statement
            decision: The decision made
            consequences: Consequences of the decision
            status: ADR status (default: proposed)
            deciders: List of decision makers
            technical_story: Link to GitHub issue/story
            decision_drivers: Factors driving the decision
            considered_options: Alternative options considered
            compliance: Compliance requirements
            tags: Tags for categorization
            template: Template name to use

        Returns:
            Created ADR object
        """
        number = self.get_next_adr_number()
        date = datetime.now().strftime("%Y-%m-%d")

        if deciders is None:
            deciders = ["Architecture Team"]

        adr = ADR(
            number=number,
            title=title,
            status=status,
            date=date,
            deciders=deciders,
            context=context,
            decision=decision,
            consequences=consequences,
            technical_story=technical_story,
            decision_drivers=decision_drivers,
            considered_options=considered_options,
            compliance=compliance,
            tags=tags,
            supersedes=supersedes,
        )

        # Write ADR to file
        self._write_adr(adr, template)
        return adr

    def _write_adr(self, adr: ADR, template: str = "default") -> None:
        """Write ADR to markdown file."""
        filename = f"ADR-{adr.number:03d}.md"
        filepath = self.adr_dir / filename

        # Try to use template if available
        try:
            if self.template_env:
                template_obj = self.template_env.get_template(f"{template}.md.j2")
                content = template_obj.render(adr=adr)
            else:
                content = self._generate_default_content(adr)
        except Exception:
            content = self._generate_default_content(adr)

        filepath.write_text(content)

    def _generate_default_content(self, adr: ADR) -> str:
        """Generate default ADR content without template."""
        content = f"""# ADR-{adr.number:03d}: {adr.title}

**Status**: {adr.status}
**Date**: {adr.date}
**Deciders**: {', '.join(adr.deciders)}
"""

        if adr.technical_story:
            content += f"**Technical Story**: {adr.technical_story}  \n"

        content += "\n## Context and Problem Statement\n\n"
        content += f"{adr.context}\n\n"

        if adr.decision_drivers:
            content += "## Decision Drivers\n\n"
            for driver in adr.decision_drivers:
                content += f"- {driver}\n"
            content += "\n"

        if adr.considered_options:
            content += "## Considered Options\n\n"
            for i, option in enumerate(adr.considered_options, 1):
                content += f"{i}. {option}\n"
            content += "\n"

        content += "## Decision Outcome\n\n"
        content += f"{adr.decision}\n\n"

        content += "## Consequences\n\n"
        content += f"{adr.consequences}\n\n"

        if adr.compliance:
            content += "## Compliance\n\n"
            for comp in adr.compliance:
                content += f"- {comp}\n"
            content += "\n"

        # Links section
        content += "## Links\n\n"
        if adr.supersedes:
            supersedes_list = ", ".join(
                [f"[ADR-{n:03d}](ADR-{n:03d}.md)" for n in adr.supersedes]
            )
            content += f"- Supersedes: {supersedes_list}\n"
        else:
            content += "- Supersedes: None\n"

        if adr.superseded_by:
            content += (
                f"- Superseded by: [ADR-{adr.superseded_by:03d}]"
                f"(ADR-{adr.superseded_by:03d}.md)\n"
            )

        if adr.amended_by:
            amended_list = ", ".join(
                [f"[ADR-{n:03d}](ADR-{n:03d}.md)" for n in adr.amended_by]
            )
            content += f"- Amended by: {amended_list}\n"

        if adr.related_adrs:
            related_list = ", ".join(
                [f"[ADR-{n:03d}](ADR-{n:03d}.md)" for n in adr.related_adrs]
            )
            content += f"- Related: {related_list}\n"

        if adr.tags:
            content += f"\n## Tags\n\n{', '.join(adr.tags)}\n"

        return content

    def read(self, number: int) -> Optional[ADR]:
        """
        Read an ADR by number.

        Args:
            number: ADR number

        Returns:
            ADR object or None if not found
        """
        filename = f"ADR-{number:03d}.md"
        filepath = self.adr_dir / filename

        if not filepath.exists():
            return None

        try:
            post = frontmatter.load(filepath)
            content = post.content

            # Parse ADR content
            adr_data = self._parse_adr_content(content, number)
            return ADR(**adr_data)
        except Exception:
            return None

    def _parse_adr_content(self, content: str, number: int) -> Dict:
        """Parse ADR markdown content."""
        lines = content.split("\n")
        adr_data = {"number": number}

        # Parse header
        title_match = re.search(r"^#\s+ADR-\d+:\s+(.+)$", lines[0])
        if title_match:
            adr_data["title"] = title_match.group(1)

        # Parse metadata
        for line in lines[1:10]:
            if line.startswith("**Status**:"):
                adr_data["status"] = line.split(":", 1)[1].strip()
            elif line.startswith("**Date**:"):
                adr_data["date"] = line.split(":", 1)[1].strip()
            elif line.startswith("**Deciders**:"):
                deciders = line.split(":", 1)[1].strip()
                adr_data["deciders"] = [d.strip() for d in deciders.split(",")]
            elif line.startswith("**Technical Story**:"):
                adr_data["technical_story"] = line.split(":", 1)[1].strip()

        # Extract sections
        adr_data["context"] = self._extract_section(
            content, "Context and Problem Statement"
        )
        adr_data["decision"] = self._extract_section(content, "Decision Outcome")
        adr_data["consequences"] = self._extract_section(content, "Consequences")

        return adr_data

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract content from a markdown section."""
        pattern = rf"##\s+{section_name}\s*\n+(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def supersede(
        self, adr_number: int, new_title: str, new_context: str, new_decision: str
    ) -> ADR:
        """
        Supersede an existing ADR with a new one.

        Args:
            adr_number: Number of ADR to supersede
            new_title: Title for new ADR
            new_context: Context for new ADR
            new_decision: Decision for new ADR

        Returns:
            New ADR that supersedes the old one
        """
        # Read old ADR
        old_adr = self.read(adr_number)
        if not old_adr:
            raise ValueError(f"ADR-{adr_number:03d} not found")

        # Create new ADR
        new_adr = self.create(
            title=new_title,
            context=new_context,
            decision=new_decision,
            consequences=f"Supersedes ADR-{adr_number:03d}",
            status="accepted",
            supersedes=[adr_number],
        )

        # Update old ADR status
        old_adr.status = "superseded"
        old_adr.superseded_by = new_adr.number
        self._write_adr(old_adr)

        return new_adr

    def amend(self, adr_number: int, amendments: str, reason: str) -> ADR:
        """
        Amend an existing ADR.

        Args:
            adr_number: Number of ADR to amend
            amendments: Amendment content
            reason: Reason for amendment

        Returns:
            New ADR containing the amendment
        """
        old_adr = self.read(adr_number)
        if not old_adr:
            raise ValueError(f"ADR-{adr_number:03d} not found")

        # Create amendment ADR
        amendment_adr = self.create(
            title=f"Amendment to {old_adr.title}",
            context=reason,
            decision=amendments,
            consequences=f"Amends ADR-{adr_number:03d}",
            status="accepted",
        )

        # Update original ADR
        if old_adr.amended_by:
            old_adr.amended_by.append(amendment_adr.number)
        else:
            old_adr.amended_by = [amendment_adr.number]

        self._write_adr(old_adr)

        return amendment_adr

    def list_adrs(self, status_filter: Optional[str] = None) -> List[ADR]:
        """
        List all ADRs, optionally filtered by status.

        Args:
            status_filter: Filter by status (proposed, accepted, etc.)

        Returns:
            List of ADR objects
        """
        adr_files = sorted(self.adr_dir.glob("ADR-*.md"))
        adrs = []

        for filepath in adr_files:
            match = re.match(r"ADR-(\d+)\.md", filepath.name)
            if match:
                number = int(match.group(1))
                adr = self.read(number)
                if adr:
                    if status_filter is None or adr.status == status_filter:
                        adrs.append(adr)

        return adrs

    def generate_index(self, output_file: Optional[str] = None) -> str:
        """
        Generate an index of all ADRs.

        Args:
            output_file: Optional file path to write index

        Returns:
            Index content as markdown string
        """
        adrs = self.list_adrs()

        content = "# Architecture Decision Records\n\n"
        content += f"Total ADRs: {len(adrs)}\n\n"

        # Group by status
        status_groups = {}
        for adr in adrs:
            if adr.status not in status_groups:
                status_groups[adr.status] = []
            status_groups[adr.status].append(adr)

        # Write grouped ADRs
        for status in ["accepted", "proposed", "superseded", "deprecated", "rejected"]:
            if status in status_groups:
                content += f"\n## {status.title()}\n\n"
                for adr in status_groups[status]:
                    content += (
                        f"- [ADR-{adr.number:03d}](ADR-{adr.number:03d}.md): "
                        f"{adr.title} ({adr.date})\n"
                    )

        if output_file:
            Path(output_file).write_text(content)

        return content

    def search(self, query: str, field: Optional[str] = None) -> List[ADR]:
        """
        Search ADRs by content.

        Args:
            query: Search query
            field: Specific field to search (title, context, decision, etc.)

        Returns:
            List of matching ADRs
        """
        adrs = self.list_adrs()
        results = []

        query_lower = query.lower()

        for adr in adrs:
            if field:
                field_value = getattr(adr, field, "")
                if field_value and query_lower in str(field_value).lower():
                    results.append(adr)
            else:
                # Search all text fields
                searchable = f"{adr.title} {adr.context} {adr.decision} {adr.consequences}".lower()
                if query_lower in searchable:
                    results.append(adr)

        return results
