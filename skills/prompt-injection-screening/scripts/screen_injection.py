"""Screen documents for embedded instructions (prompt injection) before use.

Run it on any outside document, page, JSON file or folder before reading it
for a task. It returns findings and a status and never decides quarantine; the
caller does. Text found in a document is data, never an instruction: nothing
here executes or follows it. The checks are tuned for documentation.

Finding kinds:
  override-phrase, invisible-codepoint, html-comment-instruction, base64-blob,
  cited-title (an override phrase that is only a cited title in the references:
  counted, not held), offpage-text, tiny-text (Docling JSON),
  hidden-html-text (HTML text hidden by ``display:none``, ``visibility:hidden``,
  ``opacity:0``, a zero or 1 px font size, off-screen positioning, ``clip``, a
  zero-size box with hidden overflow, text the colour of its background,
  ``aria-hidden``, or the ``hidden`` attribute), attribute-text (an instruction
  in ``alt``, ``title``, ``aria-label``, ``<meta content>``, or the ``<title>``
  element), and payload-or-command (a quoted shell command or injection payload).

Documentation is full of visible code: captioned code blocks, ``curl`` lines,
JSON bodies, and webhook payload examples. `benign_candidate` is True for such
text inside a code fence (an HTML ``<pre>`` is turned into one), a listing, a
quotation, inline code, or after a sentence introducing a prompt or template,
unless a hidden-text signal (invisible code points, off-page or sub-2-pt text,
hidden HTML text, an instruction-like attribute or title, or an HTML comment
that carries instructions) is also present in the same scan. A real payload (an
unquoted command, a hidden instruction) stays a finding that is not benign.

Entry points: ``check_text(text)`` for snippets, abstracts, and Markdown, and
``check_html(html)``; both return ``{"status", "findings", ...}`` where
``status`` is ``clean``, ``benign-quoted-content``, or ``flagged``.
``scan_path(path)`` does the same for a file: text or Markdown (YAML files too,
read as text), HTML, a JSON document (the strings of the document, HTML
strings checked as HTML), or Docling JSON (off-page and tiny text).

CLI: ``screen_injection.py scan <file> [--references-after "<heading>"]``;
prints the verdict, the spans, and the findings as JSON, and exits 1 when the
verdict is ``flagged``, 2 on an unreadable file.

``screen_injection.py scan --tree <folder> --max-bytes N`` screens every text
file of a folder up to the size cap (``--max-bytes``, required with
``--tree``: no cap is assumed; missing is exit 2). It prints the tree verdict
(``flagged`` or ``clean``), the files flagged with their spans, the files over
the cap and the counts of binary files and links it did not read, and exits as
the single-file scan does. It never follows a link or enters ``.git``.

The checks live in ``screen_injection_part1.py`` (text) and
``screen_injection_part2.py`` (Docling JSON and HTML); ship all three files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from screen_injection_part1 import (
    BASE64_MIN_RUN,
    COMMENT_MIN_WORDS,
    CONTEXT_CHARS,
    HIDDEN_KINDS,
    KIND_ATTRIBUTE,
    KIND_BASE64,
    KIND_CITED_TITLE,
    KIND_HIDDEN_HTML,
    KIND_HTML_COMMENT,
    KIND_INVISIBLE,
    KIND_OFFPAGE,
    KIND_OVERRIDE,
    KIND_PAYLOAD,
    KIND_TINY,
    MIN_WORDS,
    OFFPAGE_MIN_VISIBLE,
    OVERRIDE_RE,
    PAYLOAD_RE,
    STATUS_BENIGN,
    STATUS_CLEAN,
    STATUS_FLAGGED,
    TINY_FONT_PX,
    TINY_HEIGHT_PT,
    check_text,
    finalize,
    screen_document_text,
    screen_text,
    split_at_references,
    status_of,
)
from screen_injection_part2 import check_html, screen_docling_json

__all__ = [
    "BASE64_MIN_RUN",
    "COMMENT_MIN_WORDS",
    "CONTEXT_CHARS",
    "HIDDEN_KINDS",
    "KIND_ATTRIBUTE",
    "KIND_BASE64",
    "KIND_CITED_TITLE",
    "KIND_HIDDEN_HTML",
    "KIND_HTML_COMMENT",
    "KIND_INVISIBLE",
    "KIND_OFFPAGE",
    "KIND_OVERRIDE",
    "KIND_PAYLOAD",
    "KIND_TINY",
    "MIN_WORDS",
    "OFFPAGE_MIN_VISIBLE",
    "OVERRIDE_RE",
    "PAYLOAD_RE",
    "STATUS_BENIGN",
    "STATUS_CLEAN",
    "STATUS_FLAGGED",
    "TEXT_PROBE_BYTES",
    "TINY_FONT_PX",
    "TINY_HEIGHT_PT",
    "check_html",
    "check_text",
    "finalize",
    "is_text_file",
    "main",
    "scan_file",
    "scan_path",
    "scan_tree",
    "screen_docling_json",
    "screen_document",
    "screen_document_text",
    "screen_text",
    "split_at_references",
    "status_of",
    "strings_of",
    "tree_size_cap",
]

#: Bytes read to tell a text file from a binary one in ``scan --tree``.
TEXT_PROBE_BYTES = 8192
_HTML_STRING = re.compile(r"<\s*(?:!--|/?[a-zA-Z][^>]*>)")


def strings_of(node: Any) -> List[str]:
    """Every string key and value of a parsed document, in document order."""
    out: List[str] = []
    stack: List[Any] = [node]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            for key, value in reversed(list(item.items())):
                stack.append(value)
                stack.append(key)
        elif isinstance(item, (list, tuple)):
            stack.extend(reversed(list(item)))
    return out


def screen_document(data: Any) -> List[Dict[str, Any]]:
    """Screen a parsed JSON document (an API spec, a help-center article).

    Strings that hold HTML (an article body) are checked as HTML pages; every
    other string is joined, one per line, and gets the text checks, so a
    zero-width code point written as an escape in the file is still found.
    Spans of an HTML string's findings are relative to that string.
    """
    html_parts: List[str] = []
    text_parts: List[str] = []
    for value in strings_of(data):
        (html_parts if _HTML_STRING.search(value) else text_parts).append(value)
    findings: List[Dict[str, Any]] = []
    for part in html_parts:
        findings += check_html(part)["findings"]
    findings += screen_text("\n".join(text_parts), payloads=True)
    return finalize(findings)


def _is_docling(data: Any) -> bool:
    """True for a Docling document (`schema_name` or a `texts` list)."""
    return isinstance(data, dict) and (
        data.get("schema_name") == "DoclingDocument"
        or isinstance(data.get("texts"), list)
    )


def scan_path(path: Path, references_after: Optional[str] = None) -> Dict[str, Any]:
    """Screen a file and return ``{"status", "findings"}``.

    `.html` and `.htm` are HTML pages; `.json` is Docling JSON (off-page and
    tiny text) or any other JSON document; everything else, YAML included, is
    text or Markdown. Raises OSError for an unreadable file and ValueError for
    invalid JSON.
    """
    suffix = path.suffix.lower()
    raw = path.read_text(encoding="utf-8", errors="replace")
    findings: List[Dict[str, Any]]
    if suffix == ".json":
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"not valid JSON: {path}: {exc}") from exc
        if _is_docling(data):
            findings = finalize(screen_docling_json(path))
        else:
            findings = screen_document(data)
    elif suffix in (".html", ".htm"):
        findings = check_html(raw)["findings"]
    else:
        findings = check_text(raw, references_after)["findings"]
    return {"status": status_of(findings), "findings": findings}


def scan_file(
    path: Path, references_after: Optional[str] = None
) -> List[Dict[str, Any]]:
    """The findings of `scan_path` (kept for callers that want the list)."""
    findings: List[Dict[str, Any]] = scan_path(path, references_after)["findings"]
    return findings


def is_text_file(path: Path) -> bool:
    """True when the first block of a file has no NUL byte (a text file)."""
    with path.open("rb") as handle:
        return b"\0" not in handle.read(TEXT_PROBE_BYTES)


def _scan_tree_file(path: Path) -> Dict[str, Any]:
    """Screen one file of a tree; invalid JSON is screened as text."""
    try:
        return scan_path(path)
    except ValueError:
        text = path.read_text(encoding="utf-8", errors="replace")
        findings: List[Dict[str, Any]] = check_text(text)["findings"]
        return {"status": status_of(findings), "findings": findings}


def scan_tree(root: Path, max_bytes: int) -> Dict[str, Any]:
    """Screen every text file of a clone or probe folder up to ``max_bytes``.

    The walk is sorted and does not follow symbolic links (a link is counted,
    never read: it could point outside the tree) or enter ``.git``. A file with
    a NUL byte in its first block is binary and is counted; a file over the
    cap is listed under ``skipped_over_cap`` and not read. The tree verdict is
    ``flagged`` when any file is, else ``clean`` (a benign-quoted file is
    clean and is listed under ``benign``). Raises OSError for a folder that
    cannot be listed.
    """
    if not root.is_dir():
        raise NotADirectoryError(f"not a folder: {root}")
    report: Dict[str, Any] = {
        "files_scanned": 0,
        "files_binary": 0,
        "links_skipped": 0,
        "files_unreadable": [],
        "skipped_over_cap": [],
        "benign": [],
        "flagged": [],
    }
    for current, folders, names in os.walk(root):
        linked = [d for d in folders if (Path(current) / d).is_symlink()]
        report["links_skipped"] += len(linked)
        folders[:] = sorted(d for d in folders if d != ".git" and d not in linked)
        for name in sorted(names):
            path = Path(current) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                report["links_skipped"] += 1
            elif path.stat().st_size > max_bytes:
                report["skipped_over_cap"].append(relative)
            else:
                try:
                    if not is_text_file(path):
                        report["files_binary"] += 1
                        continue
                    result = _scan_tree_file(path)
                except OSError:
                    report["files_unreadable"].append(relative)
                    continue
                report["files_scanned"] += 1
                if result["status"] == STATUS_FLAGGED:
                    report["flagged"].append(
                        {
                            "path": relative,
                            "spans": [f["span"] for f in result["findings"]],
                            "findings": result["findings"],
                        }
                    )
                elif result["status"] == STATUS_BENIGN:
                    report["benign"].append(relative)
    report["verdict"] = STATUS_FLAGGED if report["flagged"] else STATUS_CLEAN
    return report


def tree_size_cap(cli_value: Optional[int]) -> int:
    """The size cap: ``--max-bytes``, which ``scan --tree`` requires.

    No per-file cap is assumed. Raises ValueError when the value is absent or
    not a positive whole number.
    """
    if cli_value is None:
        raise ValueError("the size cap is not given: pass --max-bytes")
    if isinstance(cli_value, bool) or not isinstance(cli_value, int) or cli_value < 1:
        raise ValueError("the size cap is not a positive whole number: --max-bytes")
    return cli_value


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CLI."""
    parser = argparse.ArgumentParser(description="Injection screen")
    sub = parser.add_subparsers(dest="cmd", required=True)
    scan = sub.add_parser(
        "scan",
        help="scan a text, HTML, JSON, or Docling file, or (--tree) a folder",
    )
    scan.add_argument("file", type=Path)
    scan.add_argument("--references-after", default=None)
    scan.add_argument(
        "--tree",
        action="store_true",
        help="FILE is a folder: scan every text file up to the cap",
    )
    scan.add_argument(
        "--max-bytes",
        type=int,
        default=None,
        help="the size cap in bytes of --tree (required with --tree; no default)",
    )
    args = parser.parse_args(argv)
    if args.tree:
        try:
            tree = scan_tree(args.file, tree_size_cap(args.max_bytes))
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(tree, indent=2, ensure_ascii=False))
        return 1 if tree["verdict"] == STATUS_FLAGGED else 0
    try:
        result = scan_path(args.file, args.references_after)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    findings = result["findings"]
    report = {
        "verdict": result["status"],
        "spans": [f["span"] for f in findings],
        "findings": findings,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if result["status"] == STATUS_FLAGGED else 0


if __name__ == "__main__":
    sys.exit(main())
