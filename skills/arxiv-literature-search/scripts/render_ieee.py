"""Render IEEE references for a Markdown document from a CSV of sources.

Usage (run from the working folder; every result is JSON on stdout, diagnostics on
stderr; no network call, nothing is installed):

- ``meta FILE``: the CSV columns that the ``<meta>`` tags of a saved HTML page fill.
- ``render FILE --sources CSV (--out FILE | --in-place)``: replace ``[S-nnnn]``
  citations (with an optional locator: ``[S-0001, p. 4]``) by IEEE numbers in order
  of first citation, collapse runs of three or more consecutive numbers (``[3]-[5]``)
  and append ``## References``. Nothing is written when there is an error.
- ``check FILE --sources CSV [--final]``: numbers resolve, entries are cited, every
  entry equals the entry re-derived from its CSV row (a hand-written or stale entry
  fails), the sources are citable and their required fields are present; ``--final``
  also fails on a citation that is not rendered yet.

The CSV is written by the agent, one row per source. Columns: ``source_id``
(``S-nnnn``), ``ref_type`` (webpage, dataset, report, article, conference, preprint
or standard), ``authors`` (names separated by ``;``), ``title``, ``container``,
``publisher``, ``edition_or_version``, ``report_no``, ``url``, ``source_date`` and
``retrieved`` (ISO dates), and the optional gate columns ``status`` (``screened-clean``
or ``extracted``), ``injection_screen_status`` (``clean``) and ``verify_result``
(blank, ``confirmed``, ``corrected`` or ``unverified``). A gate column that is in the
CSV is enforced; a gate column that is not in the CSV is read as passing.

Output files (``--out``, ``--in-place``) must lie inside the working folder; any
other target is refused (exit 2).

Exit codes: 0 ok; 1 a check failed or a citation could not be rendered; 2 usage
error or unreadable input.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional

from render_ieee_part1 import format_entry, missing_fields
from render_ieee_part2 import META_FIELDS, meta_from_html

EXIT_OK, EXIT_FINDING, EXIT_USAGE = 0, 1, 2
SOURCE_COLUMNS = [
    "source_id",
    "ref_type",
    "authors",
    "title",
    "container",
    "publisher",
    "edition_or_version",
    "report_no",
    "url",
    "source_date",
    "retrieved",
    "status",
    "injection_screen_status",
    "verify_result",
]
REQUIRED = ["source_id", "ref_type", "title"]
GATE_DEFAULTS = {"status": "screened-clean", "injection_screen_status": "clean"}
SOURCE_ID = re.compile(r"^S-\d{4}$")
OK_STATUS = ("screened-clean", "extracted")
VERIFY_RESULT = ("confirmed", "corrected", "unverified")
_CITE = r"\[[^\[\]\n]*?S-\d{4}[^\[\]\n]*?\]"
_GROUP_RE = re.compile(_CITE + r"(?:\s*,\s*" + _CITE + r")*")
_RANGE_RE = re.compile(_CITE + r"\s*[-–—]\s*" + _CITE)
_REF_HEADING_RE = re.compile(r"^## References[ \t]*$", re.MULTILINE)
_ANY_NUM_RE = re.compile(
    r"\[(\d{1,3})\]\s*[–-]\s*\[(\d{1,3})\]"
    r"|\[(\d{1,3})(?:,\s*([^\[\]\n]{1,40}))?\](?!\()"
)
_ENTRY_RE = re.compile(r"^\[(\d{1,3})\][ \t]+(.+?)[ \t]*$", re.MULTILINE)


class UsageError(ValueError):
    """Invalid arguments or unreadable input (exit code 2)."""


# --- the CSV -------------------------------------------------------------------
def load_sources(path: Path) -> dict[str, dict[str, str]]:
    """The CSV rows by id; a missing file, column or a repeated id is an error."""
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            header = [name.strip() for name in reader.fieldnames or []]
            raw = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise UsageError(f"cannot read {path.name}: {exc}") from exc
    absent = [col for col in REQUIRED if col not in header]
    if absent:
        raise UsageError(f"{path.name}: missing column {', '.join(absent)}")
    found: dict[str, dict[str, str]] = {}
    for record in raw:
        row = {col: "" for col in SOURCE_COLUMNS}
        for key, value in record.items():
            if isinstance(key, str) and isinstance(value, str):
                row[key.strip()] = value.strip()
        row.update({c: v for c, v in GATE_DEFAULTS.items() if c not in header})
        if not row["source_id"]:
            continue
        if row["source_id"] in found:
            raise UsageError(f"{row['source_id']}: repeated in {path.name}")
        found[row["source_id"]] = row
    return found


def citable(row: Mapping[str, str]) -> list[str]:
    """Reasons that a source may not be cited (empty when it may)."""
    reasons = []
    if row["status"] not in OK_STATUS:
        reasons.append(f"status is {row['status'] or 'blank'}, not screened-clean")
    if row["injection_screen_status"] != "clean":
        shown = row["injection_screen_status"] or "blank"
        reasons.append(f"injection_screen_status is {shown}, not clean")
    verify = row["verify_result"]
    if verify and verify not in VERIFY_RESULT:
        reasons.append(f"verify_result {verify!r} is not one of {VERIFY_RESULT}")
    return reasons


# --- render --------------------------------------------------------------------
def _split_front_matter(text: str) -> tuple[str, str]:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end >= 0:
            cut = text.find("\n", end + 1)
            cut = len(text) if cut < 0 else cut + 1
            return text[:cut], text[cut:]
    return "", text


def _segments(text: str) -> list[tuple[str, bool]]:
    """Chunks of ``(text, is_code_fence)``: fenced code is never cited."""
    out: list[tuple[str, bool]] = []
    buf: list[str] = []
    fenced = False
    for line in text.splitlines(keepends=True):
        if re.match(r"^\s*(```|~~~)", line):
            if fenced:
                out.append(("".join([*buf, line]), True))
                buf, fenced = [], False
            else:
                if buf:
                    out.append(("".join(buf), False))
                buf, fenced = [line], True
        else:
            buf.append(line)
    if buf:
        out.append(("".join(buf), fenced))
    return out


def _collapse(items: list[tuple[int, str]]) -> str:
    out: list[str] = []
    i = 0
    while i < len(items):
        number, locator = items[i]
        j = i
        while (
            not locator
            and j + 1 < len(items)
            and not items[j + 1][1]
            and items[j + 1][0] == items[j][0] + 1
        ):
            j += 1
        if j - i >= 2:
            out.append(f"[{items[i][0]}]–[{items[j][0]}]")
            i = j + 1
        else:
            out.append(f"[{number}, {locator}]" if locator else f"[{number}]")
            i += 1
    return ", ".join(out)


def _split_refs(body: str) -> tuple[str, Optional[str]]:
    heading = None
    for found in _REF_HEADING_RE.finditer(body):
        heading = found
    if heading is None:
        return body, None
    return body[: heading.start()], body[heading.end() :]


def _number_citations(
    body: str, sources: Mapping[str, Mapping[str, str]]
) -> tuple[str, dict[str, int], list[str], int]:
    numbers: dict[str, int] = {}
    errors: list[str] = []
    groups = [0]

    def sub_group(match: re.Match[str]) -> str:
        items: list[tuple[int, str]] = []
        for bracket in re.findall(_CITE, match.group(0)):
            tokens = [t.strip() for t in bracket[1:-1].split(",")]
            ids = [t for t in tokens if SOURCE_ID.match(t)]
            locator = ", ".join(t for t in tokens if t and not SOURCE_ID.match(t))
            if not ids:
                errors.append(f"malformed-citation: {bracket}")
                return match.group(0)
            if len(ids) > 1 and locator:
                errors.append(f"ambiguous-locator: {bracket}")
                return match.group(0)
            for ident in ids:
                if ident not in sources:
                    errors.append(f"unknown-source: {ident} is not in the CSV")
                    return match.group(0)
                numbers.setdefault(ident, len(numbers) + 1)
                items.append((numbers[ident], locator))
        groups[0] += 1
        return _collapse(items)

    pieces: list[str] = []
    for chunk, is_code in _segments(body):
        if not is_code:
            errors += [
                f"range-of-source-ids: {m.group(0)} (list each source)"
                for m in _RANGE_RE.finditer(chunk)
            ]
            chunk = _GROUP_RE.sub(sub_group, chunk)
        pieces.append(chunk)
    return "".join(pieces), numbers, errors, groups[0]


def render(text: str, sources: Mapping[str, Mapping[str, str]]) -> dict[str, Any]:
    """Replace ``[S-nnnn]`` citations with IEEE numbers and append the list."""
    front, body = _split_front_matter(text)
    numbered, numbers, errors, groups = _number_citations(_split_refs(body)[0], sources)
    refs: list[dict[str, Any]] = [
        {"n": n, "source_id": ident, "entry": format_entry(sources[ident])}
        for ident, n in sorted(numbers.items(), key=lambda item: item[1])
    ]
    for ref in refs:
        row = sources[ref["source_id"]]
        errors += [f"source-not-citable: {ref['source_id']}: {r}" for r in citable(row)]
        errors += [
            f"missing-field: {ref['source_id']}: {f}" for f in missing_fields(row)
        ]
    final = text
    if refs and not errors:
        lines = "\n\n".join(f"[{r['n']}] {r['entry']}" for r in refs)
        final = front + numbered.rstrip("\n") + "\n\n## References\n\n" + lines + "\n"
    return {"text": final, "citations": groups, "references": refs, "errors": errors}


# --- check ---------------------------------------------------------------------
def _norm(text: str) -> str:
    return " ".join(text.split())


def _cited_numbers(prose: str) -> tuple[list[int], set[int], list[str]]:
    failures: list[str] = []
    order: list[int] = []
    cited: set[int] = set()
    for found in _ANY_NUM_RE.finditer(prose):
        if found.group(1):
            low, high = int(found.group(1)), int(found.group(2))
            if high < low or high - low > 50:
                failures.append(f"bad-range: {found.group(0)}")
                continue
            numbers = list(range(low, high + 1))
        else:
            numbers = [int(found.group(3))]
        cited.update(numbers)
        order += [n for n in numbers if n not in order]
    return order, cited, failures


def _entry_findings(
    entries: Mapping[int, str], sources: Mapping[str, Mapping[str, str]]
) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    notes: list[str] = []
    by_text: dict[str, Mapping[str, str]] = {}
    for row in sources.values():
        by_text.setdefault(_norm(format_entry(row)), row)
    for number, entry in sorted(entries.items()):
        source = by_text.get(entry)
        if source is None:
            failures.append(
                f"entry-not-from-sources: [{number}] matches no row of the CSV"
            )
            continue
        where = f"[{number}] {source['source_id']}"
        failures += [f"source-not-citable: {where}: {r}" for r in citable(source)]
        failures += [f"missing-field: {where}: {f}" for f in missing_fields(source)]
        if source["verify_result"] == "unverified":
            notes.append(f"unverified-source: {where} has verify_result unverified")
    return failures, notes


def check(  # pylint: disable=too-many-locals
    text: str, sources: Mapping[str, Mapping[str, str]], final: bool = False
) -> dict[str, Any]:
    """Check citations and reference entries in a rendered (or draft) document."""
    body, refs_part = _split_refs(_split_front_matter(text)[1])
    prose = "".join(chunk for chunk, code in _segments(body) if not code)
    order, cited, failures = _cited_numbers(prose)
    entries: dict[int, str] = {}
    for found in _ENTRY_RE.finditer(refs_part or ""):
        number = int(found.group(1))
        if number in entries:
            failures.append(f"duplicate-entry-number: [{number}]")
        entries[number] = _norm(found.group(2))
    for number in sorted(cited - set(entries)):
        failures.append(f"unresolved-number: [{number}] has no entry")
    for number in sorted(set(entries) - cited):
        failures.append(f"uncited-entry: [{number}] is never cited")
    if entries and sorted(entries) != list(range(1, len(entries) + 1)):
        failures.append("entry-numbering: entries are not numbered 1..N in order")
    if order != list(range(1, len(order) + 1)):
        failures.append("number-order: numbers are not in order of first citation")
    more, notes = _entry_findings(entries, sources)
    failures += more
    drafts = sorted(set(re.findall(r"S-\d{4}", "".join(_GROUP_RE.findall(prose)))))
    if drafts:
        message = f"unrendered-citations: {', '.join(drafts)}"
        (failures if final else notes).append(message)
        for ident in drafts:
            if ident not in sources:
                failures.append(f"unknown-source: {ident} is not in the CSV")
    if refs_part is None and cited:
        failures.append("no-references-section: numbers cited but no ## References")
    return {
        "ok": not failures,
        "failures": failures,
        "notes": notes,
        "cited": sorted(cited),
    }


# --- the command line ----------------------------------------------------------
def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise UsageError(f"cannot read {path.name}: {exc}") from exc


def _write_inside(dest: Path, text: str) -> None:
    """Write ``text`` atomically; the target must lie inside the working folder."""
    base = Path.cwd().resolve()
    target = (dest if dest.is_absolute() else base / dest).resolve()
    if target != base and base not in target.parents:
        raise UsageError(f"{dest.name}: outside the working folder, not written")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=target.parent, prefix=".render-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temp, target)
    except OSError as exc:
        Path(temp).unlink(missing_ok=True)
        raise UsageError(f"cannot write {dest.name}: {exc}") from exc


def _show(result: Mapping[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def cmd_meta(args: argparse.Namespace) -> int:
    """Print the CSV columns that a saved page's ``<meta>`` tags fill."""
    fields = meta_from_html(_read_text(Path(args.file)))
    missing = [name for name in META_FIELDS if name not in fields]
    _show({"origin": "html-meta", "fields": fields, "missing": missing})
    return EXIT_OK


def cmd_render(args: argparse.Namespace) -> int:
    """Render a document's citations; nothing is written when there is an error."""
    if bool(args.out) == args.in_place:
        raise UsageError("give exactly one of --out FILE and --in-place")
    source = Path(args.file)
    result = render(_read_text(source), load_sources(Path(args.sources)))
    written = None
    if not result["errors"]:
        dest = source if args.in_place else Path(args.out)
        _write_inside(dest, result["text"])
        written = dest.name
    shown = {k: v for k, v in result.items() if k != "text"}
    _show({**shown, "ok": not result["errors"], "written": written})
    for error in result["errors"]:
        print(f"FAIL {error}", file=sys.stderr)
    return EXIT_FINDING if result["errors"] else EXIT_OK


def cmd_check(args: argparse.Namespace) -> int:
    """Check a document against the CSV."""
    result = check(
        _read_text(Path(args.file)), load_sources(Path(args.sources)), args.final
    )
    _show(result)
    for failure in result["failures"]:
        print(f"FAIL {failure}", file=sys.stderr)
    return EXIT_OK if result["ok"] else EXIT_FINDING


def build_parser() -> argparse.ArgumentParser:
    """The parser of ``render_ieee.py``."""
    parser = argparse.ArgumentParser(
        prog="render_ieee.py",
        description="Render IEEE references from a CSV of sources.",
        epilog="Exit codes: 0 ok; 1 a check failed; 2 usage or unreadable input",
    )
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="COMMAND")
    meta = sub.add_parser("meta", help="register fields from a saved HTML page")
    meta.add_argument("file")
    meta.set_defaults(func=cmd_meta)
    rend = sub.add_parser("render", help="number the citations")
    rend.add_argument("file")
    rend.add_argument("--sources", metavar="CSV", required=True)
    rend.add_argument("--out", metavar="FILE")
    rend.add_argument("--in-place", action="store_true")
    rend.set_defaults(func=cmd_render)
    chk = sub.add_parser("check", help="check a document")
    chk.add_argument("file")
    chk.add_argument("--sources", metavar="CSV", required=True)
    chk.add_argument("--final", action="store_true", help="unrendered fails")
    chk.set_defaults(func=cmd_check)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run one command; return its exit code."""
    try:
        args = build_parser().parse_args(argv)
        return int(args.func(args))
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
