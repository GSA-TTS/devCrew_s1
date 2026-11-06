"""IEEE reference entries from source rows: dates, authors, entry formats.

Part 1 of ``render_ieee.py``, which imports its names. Pure functions over a row (a
mapping of the CSV's columns to strings) with no file access.

Conventions. In ``authors`` the names are separated by ``;``. A person is
``Surname, Given Names`` (preferred when the order is ambiguous) or ``Given Names
Surname``; an organization is written as is, optionally with an ``org:`` prefix, and
is also recognized by common organization words and by CJK script (never turned into
initials). With no author, ``publisher`` stands for it. Dates are ISO (``YYYY``,
``YYYY-MM`` or ``YYYY-MM-DD``); a missing or other date is ``n.d.``. The access date
is ``retrieved``. Months use the IEEE abbreviations. For ``preprint`` the arXiv
number is read from ``report_no`` or from an arxiv.org URL; for ``webpage`` the
site name is ``container``, else ``publisher``.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from typing import Optional

Row = Mapping[str, str]
Date = tuple[int, Optional[int], Optional[int]]
# fmt: off
MONTHS = [
    "Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.",
    "Jul.", "Aug.", "Sept.", "Oct.", "Nov.", "Dec.",
]
_PARTICLES = {
    "van", "von", "de", "der", "den", "la", "le", "da", "di", "del", "bin", "al",
    "el", "du", "dos", "das", "ter", "ten",
}
# fmt: on
_ISO_DATE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?(?:[T ].*)?$")
_SUFFIXES = {"jr.", "jr", "sr.", "sr", "ii", "iii", "iv"}
_ORG_RE = re.compile(
    r"\b(?:ministry|bureau|department|office|organi[sz]ation|association|"
    r"institute|university|college|agency|commission|council|bank|authority|"
    r"administration|board|committee|foundation|corporation|company|inc|ltd|llc|"
    r"gmbh|group|center|centre|laborator(?:y|ies)|labs?|government|federation|"
    r"union|society|forum|network|international|authors|contributors|project|"
    r"team|community)\b",
    re.IGNORECASE,
)
_CJK_RE = re.compile("[぀-ヿ㐀-鿿가-힯]")


# --- dates ---------------------------------------------------------------------
def parse_date(value: str) -> Optional[Date]:
    """An ISO date as (year, month, day) with None for a missing part, else None."""
    found = _ISO_DATE.match((value or "").strip())
    if not found:
        return None
    month = int(found.group(2)) if found.group(2) else None
    day = int(found.group(3)) if found.group(3) else None
    if month is not None and not 1 <= month <= 12:
        return (int(found.group(1)), None, None)
    if day is not None and not 1 <= day <= 31:
        day = None
    return (int(found.group(1)), month, day)


def fmt_month_year(value: str) -> str:
    """``Mon. YYYY``, ``YYYY`` or ``n.d.``."""
    date = parse_date(value)
    if date is None:
        return "n.d."
    return f"{MONTHS[date[1] - 1]} {date[0]}" if date[1] else str(date[0])


def fmt_full_date(value: str) -> str:
    """``Mon. DD, YYYY``, ``Mon. YYYY``, ``YYYY`` or ``n.d.``."""
    date = parse_date(value)
    if date is not None and date[1] and date[2]:
        return f"{MONTHS[date[1] - 1]} {date[2]}, {date[0]}"
    return fmt_month_year(value)


def fmt_year(value: str) -> str:
    """``YYYY`` or ``n.d.``."""
    date = parse_date(value)
    return str(date[0]) if date else "n.d."


# --- authors -------------------------------------------------------------------
def _initials(given: str) -> str:
    out: list[str] = []
    for token in given.replace(".", ". ").split():
        if "-" in token:
            parts = [p for p in token.split("-") if p]
            out.append("-".join(f"{p[0].upper()}." for p in parts if p[0].isalpha()))
        elif token.isupper() and 2 <= len(token.rstrip(".")) <= 3 and token.isalpha():
            out += [f"{c}." for c in token]
        elif token[0].isalpha():
            out.append(f"{token[0].upper()}.")
    return " ".join(x for x in out if x)


def _comma_author(raw: str) -> str:
    surname, given = (p.strip() for p in raw.split(",", 1))
    return f"{_initials(given)} {surname}".strip() if given else raw


def _spaced_author(raw: str) -> str:
    tokens = raw.split()
    if len(tokens) == 1:
        return raw
    cut = len(tokens) - 1
    if tokens[cut].casefold() in _SUFFIXES and cut > 1:
        cut -= 1
    while cut > 1 and tokens[cut - 1].casefold() in _PARTICLES:
        cut -= 1
    return f"{_initials(' '.join(tokens[:cut]))} {' '.join(tokens[cut:])}".strip()


def format_author(name: str) -> str:
    """One author as ``I. I. Surname``; organizations and CJK names unchanged."""
    raw = name.strip()
    if raw.casefold().startswith("org:"):
        return raw[4:].strip()
    if not raw or _CJK_RE.search(raw) or _ORG_RE.search(raw):
        return raw
    return _comma_author(raw) if "," in raw else _spaced_author(raw)


def format_author_list(names: Sequence[str]) -> str:
    """IEEE author list: up to six names, then the first author and ``et al.``."""
    shown = [a for a in (format_author(n) for n in names) if a]
    if len(shown) > 6:
        return f"{shown[0]} et al."
    if len(shown) <= 2:
        return " and ".join(shown)
    return ", ".join(shown[:-1]) + f", and {shown[-1]}"


# --- entries -------------------------------------------------------------------
def _g(row: Row, key: str) -> str:
    return (row.get(key) or "").strip()


def _author_text(row: Row) -> str:
    names = [p.strip() for p in _g(row, "authors").split(";") if p.strip()]
    return format_author_list(names) if names else _g(row, "publisher")


def _end(items: Sequence[str]) -> str:
    text = ", ".join(i for i in items if i)
    return text if text.endswith(".") else text + "."


def _title(row: Row, end: str, quoted: bool = True) -> str:
    return f'"{_g(row, "title")}{end}"' if quoted else f"{_g(row, 'title')}{end}"


def arxiv_id(row: Row) -> str:
    """The arXiv number of a row (``report_no`` first, then the URL), else ``""``."""
    for field in ("report_no", "url"):
        found = re.search(
            r"(?:arXiv:\s*|arxiv\.org/(?:abs|pdf)/)(\d{4}\.\d{4,5})(v\d+)?",
            _g(row, field),
            re.IGNORECASE,
        )
        if found:
            return found.group(1)
    bare = re.fullmatch(r"(\d{4}\.\d{4,5})(v\d+)?", _g(row, "report_no"))
    return bare.group(1) if bare else ""


def _tail(row: Row, accessed: bool = False) -> str:
    url = _g(row, "url")
    online = f"[Online]. Available: {url}" if url else ""
    got = ""
    if accessed and parse_date(_g(row, "retrieved")):
        got = f"Accessed: {fmt_full_date(_g(row, 'retrieved'))}."
    return " ".join(p for p in (got, online) if p)


def _head(row: Row) -> str:
    author = _author_text(row)
    return f"{author}, " if author else ""


def _join(parts: Sequence[str]) -> str:
    return " ".join(p for p in parts if p)


def _entry_webpage(row: Row) -> str:
    site = _g(row, "container") or _g(row, "publisher")
    title = _title(row, "," if site else ".")
    return _join([_head(row) + title, f"{site}." if site else "", _tail(row, True)])


def _entry_dataset(row: Row) -> str:
    items = [_g(row, "publisher"), _g(row, "edition_or_version")]
    items.append(fmt_year(_g(row, "source_date")))
    return _join([_head(row) + _title(row, ","), _end(items), _tail(row, True)])


def _entry_report(row: Row) -> str:
    number = _g(row, "report_no")
    if number and not number.casefold().startswith(("rep", "no.")):
        number = f"Rep. no. {number}"
    items = [_g(row, "publisher"), number, fmt_month_year(_g(row, "source_date"))]
    return _join([_head(row) + _title(row, ","), _end(items), _tail(row)])


def _entry_article(row: Row) -> str:
    items = [_g(row, "container"), fmt_month_year(_g(row, "source_date"))]
    return _join([_head(row) + _title(row, ","), _end(items)])


def _entry_conference(row: Row) -> str:
    conf = _g(row, "container")
    if conf and not conf.casefold().startswith(("proc", "in ")):
        conf = f"in Proc. {conf}"
    items = [conf, fmt_year(_g(row, "source_date"))]
    return _join([_head(row) + _title(row, ","), _end(items)])


def _entry_preprint(row: Row) -> str:
    number = arxiv_id(row)
    items = [fmt_year(_g(row, "source_date")), f"arXiv:{number}" if number else ""]
    return _join(
        [_head(row) + _title(row, ","), _end(items), "" if number else _tail(row)]
    )


def _entry_standard(row: Row) -> str:
    items = [_author_text(row), _title(row, "", quoted=False), _g(row, "report_no")]
    items.append(fmt_full_date(_g(row, "source_date")))
    return _join([_end(items), _tail(row)])


ENTRY_FORMATS: dict[str, Callable[[Row], str]] = {
    "webpage": _entry_webpage,
    "dataset": _entry_dataset,
    "report": _entry_report,
    "article": _entry_article,
    "conference": _entry_conference,
    "preprint": _entry_preprint,
    "standard": _entry_standard,
}
_REQUIRED: dict[str, list[str]] = {
    "webpage": ["author_or_publisher", "title", "url", "retrieved"],
    "dataset": ["author_or_publisher", "title", "publisher", "url", "retrieved"],
    "report": ["author_or_publisher", "title", "publisher", "url"],
    "article": ["authors", "title", "container"],
    "conference": ["authors", "title", "container"],
    "preprint": ["authors", "title", "arxiv_or_url"],
    "standard": ["author_or_publisher", "title", "url"],
}


def format_entry(row: Row) -> str:
    """The IEEE entry text (without the ``[n]``) for one register row."""
    formatter = ENTRY_FORMATS.get(_g(row, "ref_type"))
    return formatter(row) if formatter is not None else ""


def missing_fields(row: Row) -> list[str]:
    """Required fields (by ``ref_type``) that the row leaves empty."""
    kind = _g(row, "ref_type")
    if kind not in _REQUIRED:
        return ["ref_type"]
    out: list[str] = []
    for field in _REQUIRED[kind]:
        if field == "author_or_publisher":
            ok = bool(_g(row, "authors") or _g(row, "publisher"))
        elif field == "arxiv_or_url":
            ok = bool(arxiv_id(row) or _g(row, "url"))
        else:
            ok = bool(_g(row, field))
        if not ok:
            out.append(field)
    return out
