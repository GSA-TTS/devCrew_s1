"""Stated-date parsing for ``page_dates.py`` (part 1).

``parse_stated_date`` turns the text of a stated date into ``YYYY-MM-DD`` (or
``YYYY-MM``). It reads ISO dates, year-first dates with slashes or dots, and
dates with a month name ("March 4, 2025", "4 March 2025", "March 2025").
"""

from __future__ import annotations

import re
from typing import Optional

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}  # fmt: skip
_ISO = re.compile(r"^(\d{4})-(\d{2})(?:-(\d{2}))?(?:[T ].*)?$")
_SLASH = re.compile(r"^(\d{4})[/.](\d{1,2})(?:[/.](\d{1,2}))?$")
_MDY = re.compile(r"^([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b")
_DMY = re.compile(r"^(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b")
_MY = re.compile(r"^([A-Za-z]{3,9})\.?,?\s+(\d{4})\b")


def parse_stated_date(value: str) -> str:
    """Return ``YYYY-MM-DD`` (or ``YYYY-MM``) for a stated date, else ''.

    A bare year is not a date basis, so it returns ''.
    """
    text = " ".join(str(value or "").split())
    if not text:
        return ""
    match = _ISO.match(text)
    if match:
        return _fmt(match.group(1), match.group(2), match.group(3))
    match = _SLASH.match(text)
    if match:
        return _fmt(match.group(1), match.group(2).zfill(2), match.group(3))
    for pattern, order in ((_MDY, "mdy"), (_DMY, "dmy"), (_MY, "my")):
        match = pattern.match(text)
        if not match:
            continue
        if order == "mdy":
            mon, day, year = match.group(1), match.group(2), match.group(3)
        elif order == "dmy":
            day, mon, year = match.group(1), match.group(2), match.group(3)
        else:
            mon, day, year = match.group(1), None, match.group(2)
        month = _MONTHS.get(mon.lower()[:3])
        if month:
            return _fmt(year, f"{month:02d}", day.zfill(2) if day else None)
    return ""


def _fmt(year: str, month: str, day: Optional[str]) -> str:
    """Format validated date parts; '' when a part is out of range."""
    if not 1 <= int(month) <= 12:
        return ""
    if day is None:
        return f"{year}-{month}"
    if not 1 <= int(day) <= 31:
        return ""
    return f"{year}-{month}-{int(day):02d}"
