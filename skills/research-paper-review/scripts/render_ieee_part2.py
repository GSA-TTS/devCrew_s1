"""Register fields from the ``<meta>`` tags of a saved web page.

Part 2 of ``render_ieee.py``, which imports its names. ``meta_from_html`` reads the
``citation_*`` (Highwire) and Dublin Core tags of an HTML text and returns the CSV
columns it can fill; it opens no file and makes no request.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any, Optional

META_FIELDS = ["authors", "title", "container", "source_date", "publisher"]


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag != "meta":
            return
        amap = {k.lower(): (v or "").strip() for k, v in attrs}
        name = amap.get("name") or amap.get("property") or ""
        content = amap.get("content", "")
        if name and content:
            self.tags.append((name.casefold(), content))


def _normalize_date(value: str) -> str:
    m = re.match(r"^(\d{4})[/.](\d{1,2})(?:[/.](\d{1,2}))?$", value.strip())
    if m:
        parts = [m.group(1), m.group(2).zfill(2)]
        if m.group(3):
            parts.append(m.group(3).zfill(2))
        return "-".join(parts)
    return value.strip()


def meta_from_html(text: str) -> dict[str, Any]:
    """Register fields from ``citation_*`` and Dublin Core ``<meta>`` tags."""
    parser = _MetaParser()
    parser.feed(text)
    parser.close()

    def values(*names: str) -> list[str]:
        return [c for n, c in parser.tags if n in names]

    def first(*names: str) -> str:
        found = values(*names)
        return found[0] if found else ""

    fields: dict[str, str] = {}
    authors = values("citation_author") or values(
        "dc.creator", "dcterms.creator", "dc.contributor"
    )
    if authors:
        fields["authors"] = "; ".join(authors)
    title = first("citation_title", "dc.title", "dcterms.title")
    if title:
        fields["title"] = title
    container = first(
        "citation_journal_title", "citation_conference_title",
        "citation_inbook_title", "citation_series_title", "dc.source",
    )  # fmt: skip
    if container:
        fields["container"] = container
    date = first(
        "citation_publication_date", "citation_date", "citation_online_date",
        "dc.date", "dcterms.issued", "dcterms.date",
    )  # fmt: skip
    if date:
        fields["source_date"] = _normalize_date(date)
    publisher = first(
        "citation_publisher", "dc.publisher", "dcterms.publisher",
        "citation_technical_report_institution",
    )  # fmt: skip
    if publisher:
        fields["publisher"] = publisher
    arxiv = first("citation_arxiv_id")
    report = first("citation_technical_report_number")
    if arxiv:
        fields["report_no"] = f"arXiv:{arxiv}"
    elif report:
        fields["report_no"] = report
    if first("citation_conference_title"):
        fields["ref_type"] = "conference"
    elif first("citation_journal_title"):
        fields["ref_type"] = "article"
    elif arxiv:
        fields["ref_type"] = "preprint"
    elif first("citation_technical_report_institution"):
        fields["ref_type"] = "report"
    return fields
