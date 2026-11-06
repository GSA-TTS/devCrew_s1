"""Date basis of a web page or document, from the page's own stated dates.

``extract_date`` reads, in this order of kind, every date a page states about
itself and records each with its quote and locator:

* JSON-LD ``datePublished`` and ``dateModified``;
* Open Graph ``article:published_time`` and ``article:modified_time``;
* ``citation_*`` and Dublin Core ``<meta>`` tags, and ``itemprop`` dates;
* PDF metadata in the Docling JSON (the keys are a configuration entry,
  ``DOCLING_DATE_KEYS``, because the Docling JSON layout is not bundled);
* a help-center article JSON's ``edited_at``, ``updated_at``, and
  ``created_at``;
* visible "Published", "Last updated", "Revised", and "Version N released"
  lines.

The HTTP ``Last-Modified`` header, the retrieval time, and a copyright year are
never a date basis. ``date_basis`` takes these values: ``stated-published``,
``stated-revised``, ``version-release`` (a release or version line states the
date), ``change-notice`` (the source is a change notice and states a date),
``undated-official`` (no stated date on a document the caller marks official),
``none`` (no stated date), and ``pending`` (nothing readable yet, so the date
cannot be known).

  page_dates.py date FILE [--json] [--source-type TYPE] [--official]

The date-parsing helpers are in ``page_dates_part1.py``, beside this file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from page_dates_part1 import parse_stated_date

__all__ = ["date_finder", "extract_date", "main", "parse_stated_date"]

DOCLING_DATE_KEYS: Tuple[str, ...] = (
    "creation_date",
    "CreationDate",
    "created",
    "modification_date",
    "ModDate",
    "modified",
)
ARTICLE_REVISED_KEYS: Tuple[str, ...] = ("edited_at", "updated_at")
ARTICLE_PUBLISHED_KEYS: Tuple[str, ...] = ("created_at",)
PUBLISHED_META = (
    "article:published_time",
    "og:article:published_time",
    "citation_publication_date",
    "citation_date",
    "citation_online_date",
    "dc.date",
    "dc.date.issued",
    "dcterms.issued",
    "dcterms.created",
    "datepublished",
)
REVISED_META = (
    "article:modified_time",
    "og:article:modified_time",
    "og:updated_time",
    "dcterms.modified",
    "dc.date.modified",
    "datemodified",
)
CHANGE_NOTICE_TYPE = "change-notice"
#: A visible line longer than this is body text, not a date line.
MAX_LINE_CHARS = 160
#: Candidate kinds in order of preference.
_ORDER = {"stated-published": 0, "stated-revised": 1, "version-release": 2}
_BLOCK_TAGS = {
    "p", "div", "li", "br", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5",
    "h6", "section", "article", "header", "footer", "dd", "dt", "time", "span",
}  # fmt: skip
_SKIP_TEXT = {"script", "style", "noscript", "template", "head", "title"}
_PUBLISHED_LABEL = re.compile(
    r"^(first\s+published|originally\s+published|date\s+published|publication\s+date|"
    r"published(\s+on|\s+date)?|posted(\s+on)?|issued)\b[\s:.\-–—]*",
    re.IGNORECASE,
)
_REVISED_LABEL = re.compile(
    r"^(last\s+(updated|revised|modified|reviewed)(\s+on)?|updated(\s+on)?|"
    r"revised(\s+on)?|revision\s+date|date\s+modified|modified(\s+on)?)\b"
    r"[\s:.\-–—]*",
    re.IGNORECASE,
)
# "Version 2.3 released March 4, 2025", "Released on 2025-03-04", "Release date: ..."
_RELEASED_LABEL = re.compile(
    r"^(?:(?:api\s+)?version\s+v?[\w.\-]+[\s,;:–—-]*)?"
    r"released?(?:\s+date)?(?:\s+on)?\b[\s:.\-–—]*",
    re.IGNORECASE,
)
# "Version 3.1 (2025-03-04)", "Release 2.0 - March 2025", "v1.2.3: 2025-03-04"
_VERSION_LABEL = re.compile(
    r"^(?:(?:(?:api\s+)?version|release)\s+v?[\w.\-]+|v\d[\w.\-]*)\s*[(–—:,-]\s*",
    re.IGNORECASE,
)
_HTML_TAG = re.compile(
    r"<\s*/?\s*(?:!doctype|html|head|body|meta|script|p|div|span|article|section|main|"
    r"h[1-6]|li|ul|ol|br|table|tr|td|a|time)\b",
    re.IGNORECASE,
)


class _PageProbe(HTMLParser):
    """Collects meta tags, JSON-LD blocks, and visible text lines."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: List[Tuple[str, str, int]] = []
        self.jsonld: List[Tuple[str, int]] = []
        self.lines: List[Tuple[str, int]] = []
        self._buf: List[str] = []
        self._line_no = 1
        self._skip: List[str] = []
        # (line, text parts) of the JSON-LD script being read, else None
        self._ld: Optional[Tuple[int, List[str]]] = None

    def _flush(self) -> None:
        text = " ".join("".join(self._buf).split())
        if text:
            self.lines.append((text, self._line_no))
        self._buf = []
        self._line_no = self.getpos()[0]

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        amap = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            name = (
                (amap.get("name") or amap.get("property") or amap.get("itemprop") or "")
                .strip()
                .lower()
            )
            content = amap.get("content", "").strip()
            if name and content:
                self.meta.append((name, content, self.getpos()[0]))
        if tag == "script" and "ld+json" in amap.get("type", "").lower():
            self._ld = (self.getpos()[0], [])
        elif tag in _SKIP_TEXT:
            self._skip.append(tag)
        if tag in _BLOCK_TAGS and tag not in ("time", "span"):
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._ld is not None:
            line, parts = self._ld
            self._ld = None
            self.jsonld.append(("".join(parts), line))
        elif self._skip and self._skip[-1] == tag:
            self._skip.pop()
        if tag in _BLOCK_TAGS and tag not in ("time", "span"):
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._ld is not None:
            self._ld[1].append(data)
        elif not self._skip:
            if not self._buf:
                self._line_no = self.getpos()[0]
            self._buf.append(data)

    def close(self) -> None:
        super().close()
        self._flush()


def _walk_jsonld(node: Any, out: List[Tuple[str, str]]) -> None:
    """Collect (key, value) pairs of ``datePublished`` and ``dateModified``."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key in ("datePublished", "dateModified") and isinstance(value, str):
                out.append((key, value))
            else:
                _walk_jsonld(value, out)
    elif isinstance(node, list):
        for item in node:
            _walk_jsonld(item, out)


def _candidate(
    basis: str, raw: str, source: str, locator: str, quote: str = ""
) -> Optional[Dict[str, str]]:
    """Build one candidate dict, or None when the raw text is not a date."""
    date = parse_stated_date(raw)
    if not date:
        return None
    return {
        "date": date,
        "date_basis": basis,
        "source": source,
        "locator": locator,
        "quote": quote or raw.strip(),
    }


def _visible_candidate(text_line: str, line: int) -> Optional[Dict[str, str]]:
    """The date a visible line states about the page, if it is a date line."""
    for regex, basis in (
        (_PUBLISHED_LABEL, "stated-published"),
        (_REVISED_LABEL, "stated-revised"),
        (_RELEASED_LABEL, "version-release"),
        (_VERSION_LABEL, "version-release"),
    ):
        match = regex.match(text_line)
        if match:
            start = match.end()
            rest = text_line[start:].strip().rstrip(")].,;")
            return _candidate(basis, rest, "visible", f"line {line}", text_line)
    return None


def _from_html(text: str) -> List[Dict[str, str]]:
    """Return the stated-date candidates of an HTML page."""
    probe = _PageProbe()
    try:
        probe.feed(text)
        probe.close()
    except (AssertionError, ValueError):  # malformed markup: keep what parsed
        pass
    found: List[Optional[Dict[str, str]]] = []
    for block, line in probe.jsonld:
        try:
            data = json.loads(block)
        except ValueError:
            continue
        pairs: List[Tuple[str, str]] = []
        _walk_jsonld(data, pairs)
        for key, value in pairs:
            basis = "stated-published" if key == "datePublished" else "stated-revised"
            found.append(
                _candidate(basis, value, "json-ld", f"json-ld:{key}@line{line}")
            )
    for name, content, line in probe.meta:
        if name in PUBLISHED_META:
            found.append(
                _candidate(
                    "stated-published", content, "meta", f"meta:{name}@line{line}"
                )
            )
        elif name in REVISED_META:
            found.append(
                _candidate("stated-revised", content, "meta", f"meta:{name}@line{line}")
            )
    for text_line, line in probe.lines:
        if len(text_line) <= MAX_LINE_CHARS:
            found.append(_visible_candidate(text_line, line))
    return [c for c in found if c]


def _looks_like_html(text: str) -> bool:
    """True when the text carries HTML tags (otherwise it is Markdown or plain text)."""
    return _HTML_TAG.search(text) is not None


def _from_text(text: str) -> List[Dict[str, str]]:
    """Return the stated-date candidates of Markdown or plain text, line by line.

    Newlines separate lines here (unlike HTML, where they are only spacing). A
    line's leading heading, quote, and list marks and its bold marks are dropped
    before the date label is read.
    """
    found: List[Optional[Dict[str, str]]] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.replace("**", "").replace("__", "")
        line = re.sub(r"^[\s#>*+-]+", "", line).strip()
        if line and len(line) <= MAX_LINE_CHARS:
            found.append(_visible_candidate(line, number))
    return [c for c in found if c]


def _from_docling_json(
    doc: Dict[str, Any], keys: Sequence[str]
) -> List[Dict[str, str]]:
    """Return candidates from metadata mappings of a Docling JSON document."""
    found: List[Optional[Dict[str, str]]] = []
    holders: List[Tuple[str, Any]] = []
    for name in ("metadata", "origin", "properties", "meta"):
        if isinstance(doc.get(name), dict):
            holders.append((name, doc[name]))
    for name, holder in holders:
        for key in keys:
            value = holder.get(key)
            if not isinstance(value, str):
                continue
            raw = value[2:] if value.startswith("D:") else value
            if re.fullmatch(r"\d{8}.*", raw):
                raw = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
            basis = (
                "stated-revised"
                if re.search(r"mod|ModDate|update", key, re.IGNORECASE)
                else "stated-published"
            )
            found.append(_candidate(basis, raw, "pdf-metadata", f"{name}.{key}", value))
    return [c for c in found if c]


def _from_article_json(doc: Dict[str, Any]) -> List[Dict[str, str]]:
    """Return candidates from a help-center article JSON's own date fields.

    The article is `doc["article"]` or `doc` itself. `edited_at` and
    `updated_at` are revision dates and carry the article's currency, so
    `created_at` (the first publication) counts only when neither is present.
    """
    inner = doc.get("article")
    article: Dict[str, Any] = inner if isinstance(inner, dict) else doc
    prefix = "article." if article is not doc else ""

    def collect(keys: Sequence[str], basis: str) -> List[Dict[str, str]]:
        """Candidates for the given keys of the article."""
        out: List[Optional[Dict[str, str]]] = []
        for key in keys:
            value = article.get(key)
            if isinstance(value, str):
                out.append(_candidate(basis, value, "article-json", f"{prefix}{key}"))
        return [c for c in out if c]

    revised = collect(ARTICLE_REVISED_KEYS, "stated-revised")
    return revised or collect(ARTICLE_PUBLISHED_KEYS, "stated-published")


def _no_date(basis: str) -> Dict[str, Any]:
    """The result for a document that states no date."""
    return {
        "source_date": "",
        "date_basis": basis,
        "date_quote": "",
        "date_locator": "",
        "candidates": [],
    }


def extract_date(
    text: str,
    docling_keys: Sequence[str] = DOCLING_DATE_KEYS,
    *,
    source_type: str = "",
    official: bool = False,
) -> Dict[str, Any]:
    """Return the date basis of a page, article JSON, Docling JSON, or Markdown.

    The result has ``source_date``, ``date_basis`` (see the module docstring),
    ``date_quote``, ``date_locator``, and ``candidates`` (every stated date
    found, in order of preference: published, revised, version release).
    ``source_type="change-notice"`` makes a stated date a ``change-notice``
    basis. ``official=True`` marks a document that may be admitted undated:
    with no stated date its basis is ``undated-official`` rather than
    ``none``. Text with no content is ``pending``.
    """
    stripped = text.lstrip()
    if not stripped:
        return _no_date("pending")
    candidates: List[Dict[str, str]]
    doc: Any = None
    if stripped.startswith("{"):
        try:
            doc = json.loads(stripped)
        except ValueError:
            doc = None
    if isinstance(doc, dict):
        candidates = _from_docling_json(doc, docling_keys) + _from_article_json(doc)
    elif doc is not None:
        candidates = []
    elif _looks_like_html(text):
        candidates = _from_html(text)
    else:
        candidates = _from_text(text)
    ranked = sorted(candidates, key=lambda c: _ORDER[c["date_basis"]])
    if not ranked:
        return _no_date("undated-official" if official else "none")
    best = ranked[0]
    basis = CHANGE_NOTICE_TYPE if source_type == CHANGE_NOTICE_TYPE else None
    return {
        "source_date": best["date"],
        "date_basis": basis or best["date_basis"],
        "date_quote": best["quote"],
        "date_locator": best["locator"],
        "candidates": ranked,
    }


def _read_text(path: Optional[Path]) -> str:
    """Return a file's text ('' when it is absent or unreadable)."""
    if path is None:
        return ""
    try:
        return Path(path).read_bytes().decode("utf-8", errors="replace")
    except OSError:
        return ""


def date_finder(
    md_path: Optional[Path] = None,
    json_path: Optional[Path] = None,
    original: Optional[Path] = None,
    record: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """The date basis of a fetched document, from its saved files.

    It looks, in order, at the saved original when that is an HTML page or a
    JSON file, the Docling JSON (PDF metadata), and the converted Markdown
    (visible "Published" and "Last updated" lines), and returns the first
    stated date with its quote and locator. ``record`` supplies ``source_type``
    (a ``change-notice`` source gets that basis) and ``credibility_tier`` (a
    Tier 1 document with no stated date gets ``undated-official``). A document
    with none gets ``none``, and one with nothing readable yet gets
    ``pending``; ``Last-Modified`` and the ``retrieved`` stamp are never read.
    """
    hints = record or {}
    source_type = str(hints.get("source_type") or "")
    official = str(hints.get("credibility_tier") or "").strip() == "Tier 1"
    texts: List[str] = []
    page = _read_text(original)
    head = page[:4096]
    if re.search(r"<(!doctype html|html|head|meta)\b", head, re.IGNORECASE) or (
        page.lstrip().startswith("{")
    ):
        texts.append(page)
    texts.extend([_read_text(json_path), _read_text(md_path)])
    readable = [t for t in texts if t.strip()]
    for text in readable:
        found = extract_date(text, source_type=source_type, official=False)
        if found["date_basis"] not in ("none", "pending"):
            return {
                "source_date": str(found["source_date"]),
                "date_basis": str(found["date_basis"]),
                "date_quote": str(found["date_quote"]),
                "date_locator": str(found["date_locator"]),
            }
    if not readable:
        basis = "pending"
    else:
        basis = "undated-official" if official else "none"
    return {
        "source_date": "",
        "date_basis": basis,
        "date_quote": "",
        "date_locator": "",
    }


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    date = sub.add_parser("date", help="date basis of an HTML, JSON, or Docling file")
    date.add_argument("file")
    date.add_argument("--json", action="store_true")
    date.add_argument(
        "--source-type", default="", help="`change-notice` gives that date basis"
    )
    date.add_argument(
        "--official",
        action="store_true",
        help="a Tier 1 document: no stated date is `undated-official`",
    )
    args = parser.parse_args(argv)
    path = Path(args.file)
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        return 2
    result = extract_date(
        path.read_bytes().decode("utf-8", errors="replace"),
        source_type=args.source_type,
        official=args.official,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"{result['date_basis']}: {result['source_date'] or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
