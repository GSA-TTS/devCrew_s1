"""Find secrets in text by token shape, before any of it is quoted.

Usage: ``find_secrets.py FILE [FILE ...]``; ``-`` reads standard input.

Scope: reads the files it is given (nothing else, nothing written, no network)
and reports where a secret sits (rule, line, character span), never the secret
itself. Warn the user, and quote nothing from a file that holds a hit.

Output: one JSON object on standard output, ``{"files": [{"path", "hits"}],
"found": N}``, the same for the same input. Diagnostics go to standard error.

Exit codes: 0 scanned (hits or none); 1 a file could not be read; 2 usage error.
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

_EDGE = r"(?<![A-Za-z0-9])"
# (rule, needles of which one must occur in the text in any case, regex)
SHAPES: Tuple[Tuple[str, Tuple[str, ...], str], ...] = (
    ("huggingface-token", ("hf_",), _EDGE + r"hf_[A-Za-z0-9]{20,}"),
    ("anthropic-key", ("sk-ant-",), _EDGE + r"sk-ant-[A-Za-z0-9_-]{16,}"),
    ("openai-key", ("sk-",), _EDGE + r"sk-(?!ant-)[A-Za-z0-9_-]{20,}"),
    ("xai-key", ("xai-",), _EDGE + r"xai-[A-Za-z0-9]{20,}"),
    ("github-token", ("gh",), _EDGE + r"gh[pousr]_[A-Za-z0-9]{30,}"),
    ("github-fine-grained", ("github_pat_",), _EDGE + r"github_pat_[A-Za-z0-9_]{20,}"),
    (
        "aws-access-key",
        ("AKIA", "ASIA", "ABIA", "ACCA"),
        _EDGE + r"(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}(?![A-Za-z0-9])",
    ),
    ("gcp-api-key", ("AIza",), _EDGE + r"AIza[0-9A-Za-z_-]{35}"),
    (
        "private-key-block",
        ("-----BEGIN",),
        r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----",
    ),
    ("slack-token", ("xox",), _EDGE + r"xox[abposr]-[A-Za-z0-9-]{10,}"),
    ("stripe-key", ("_live_",), _EDGE + r"[sr]k_live_[A-Za-z0-9]{24,}"),
    (
        "aws-secret-key",
        ("secret",),
        r"(?i:(?:aws[_-]?)?secret[_-]?access[_-]?key|aws[_-]?secret[_-]?key)"
        r"[\"']?\s*(?:=>|[:=])\s*[\"']?[A-Za-z0-9/+]{40,}",
    ),
    (
        "azure-account-key",
        ("accountkey",),
        r"(?i:accountkey)\s*=\s*[A-Za-z0-9+/]{40,}={0,2}",
    ),
)
_COMPILED = [(rule, needles, re.compile(rx)) for rule, needles, rx in SHAPES]
RULES = tuple(rule for rule, _, _ in SHAPES)


@dataclass(frozen=True)
class SecretHit:
    """Where one secret sits: its rule, character span and 1-based line."""

    rule: str
    start: int
    end: int
    line: int


def find_secrets(text: str) -> List[SecretHit]:
    """The secrets in ``text``, in order of position; the values stay unread."""
    starts = [0] + [m.end() for m in re.finditer("\n", text)]
    lowered = text.lower()
    found = set()
    for rule, needles, pattern in _COMPILED:
        if not any(needle.lower() in lowered for needle in needles):
            continue
        for match in pattern.finditer(text):
            line = bisect.bisect_right(starts, match.start())
            found.add(SecretHit(rule, match.start(), match.end(), line))
    return sorted(found, key=lambda h: (h.start, h.rule))


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8", errors="replace")


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Scan the named files and print the JSON result."""
    parser = argparse.ArgumentParser(
        description="Report where secrets sit in files, never their values."
    )
    parser.add_argument("files", nargs="+", metavar="FILE", help="file, or - for stdin")
    args = parser.parse_args(argv)
    results = []
    for path in args.files:
        try:
            text = _read(path)
        except OSError as exc:
            print(f"find_secrets: cannot read {path}: {exc.strerror}", file=sys.stderr)
            return 1
        hits = [asdict(hit) for hit in find_secrets(text)]
        results.append({"path": path, "hits": hits})
    found = sum(len(item["hits"]) for item in results)
    print(json.dumps({"files": results, "found": found}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
