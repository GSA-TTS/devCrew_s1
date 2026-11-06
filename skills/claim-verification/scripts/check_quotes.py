"""Check that quotes are verbatim in a source and that claims rest on them.

Usage::

    check_quotes.py SOURCE --claims CLAIMS.json
    check_quotes.py SOURCE --quote TEXT [--statement TEXT] [--artifact TEXT ...]

``SOURCE`` is the text file the quotes were taken from; ``-`` reads standard
input. ``CLAIMS.json`` is a list of objects ``{"id", "quote", "statement",
"artifacts"}``; only ``quote`` is required. Per claim the script checks that

* the quote has at least 25 characters and occurs verbatim in the source, after
  whitespace and end-of-line hyphenation are normalized, and starts and ends on
  a word boundary;
* each artifact (an endpoint, field, price or limit copied from the source)
  occurs verbatim in the source;
* every checkable token of the statement is in the quote or the artifacts:
  backticked strings, URLs, ``METHOD /path`` endpoints, prices, percentages,
  numbers with a unit or a rate, and numbers after a limit word. Numbers are
  compared after normalization (separators, ``%``, dashes, currency codes,
  spelled-out small numbers and unit synonyms), so ``1,000 requests per
  minute`` supports ``1000 requests/min`` and ``60 seconds`` supports ``60s``.
  A token of another value (``120`` against ``60``) is named as a conflict.

Scope: reads the files it is given (nothing else, nothing written, no network).

Output: one JSON object on standard output, ``{"source", "claims": [{"id",
"ok", "failures"}], "failed": N}``, the same for the same input. Diagnostics
go to standard error.

Exit codes: 0 every claim passes; 1 a claim fails; 2 usage error or unreadable
input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit

MIN_QUOTE_CHARS = 25  # a quote has at least 25 characters


# --------------------------------------------------------------------------
# Text normalization and the numeric-claim rule
# --------------------------------------------------------------------------
def normalize(text: str, keep_hyphen: bool = False) -> str:
    """Collapse whitespace and join end-of-line hyphenation.

    With ``keep_hyphen`` the hyphen of a broken compound is kept (``state-`` +
    ``of-the-art`` stays ``state-of-the-art``). Soft hyphens are removed.
    """
    text = text.replace("\xad", "")
    joiner = "-" if keep_hyphen else ""
    text = re.sub(r"(?<=\w)-[ \t]*\r?\n[ \t]*(?=\w)", joiner, text)
    return " ".join(text.split())


def quote_regex(quote: str) -> "re.Pattern[str]":
    """Compile a pattern matching the quote through whitespace and line breaks.

    Whitespace runs match any whitespace; between two word characters (and
    after a hyphen) a hyphen at the end of a line may intervene, so both
    ``recov-\\nery`` and ``state-\\nof-the-art`` match their unbroken forms.
    """
    text = normalize(quote, keep_hyphen=True)
    brk = r"(?:-[ \t]*\r?\n[ \t]*)?"
    parts: List[str] = []
    for idx, char in enumerate(text):
        if char == " ":
            parts.append(r"\s+")
            continue
        parts.append(re.escape(char))
        if char == "-":
            parts.append(r"(?:[ \t]*\r?\n[ \t]*)?")
        elif idx + 1 < len(text) and text[idx + 1] != " ":
            if char.isalnum() and text[idx + 1].isalnum():
                parts.append(brk)
    return re.compile("".join(parts))


def quote_in_source(quote: str, source_text: str) -> bool:
    """Return True if the quote or artifact occurs verbatim in the source text.

    A quote that starts or ends with a word character must start and end on a
    word boundary, so ``the recovery step`` is not a quote of ``recovery steps``.
    """
    flat = normalize(quote)
    if not flat:
        return False
    source_text = source_text.replace("\xad", "")
    pattern = quote_regex(quote).pattern
    if flat[0].isalnum():
        pattern = r"(?<!\w)" + pattern
    if flat[-1].isalnum():
        pattern = pattern + r"(?!\w)"
    return re.search(pattern, source_text) is not None


def token_in_text(token: str, raw: str) -> bool:
    """Return True if a code, path, or endpoint token occurs verbatim in the text.

    The token must not run on into a longer path or name: a path is not found
    in the same path with one more segment after it.
    """
    flat = normalize(token)
    if not flat:
        return False
    pattern = r"(?<![\w/.-])" + quote_regex(token).pattern + r"(?![\w/-]|\.\w)"
    return re.search(pattern, raw.replace("\xad", "")) is not None


def canonical_url(url: str) -> str:
    """Return a URL with scheme, host case, fragment and trailing slash settled.

    Two URLs that differ only in scheme, host case, fragment or a trailing
    slash agree. Query parameters are sorted. A non-HTTP(S) string is returned stripped.
    """
    text = url.strip()
    parts = urlsplit(text)
    host = (parts.hostname or "").lower()
    if parts.scheme.lower() not in ("http", "https") or not host:
        return text
    try:
        port = parts.port
    except ValueError:
        port = None
    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    netloc = host if port in (None, 80, 443) else f"{host}:{port}"
    query = sorted(parse_qsl(parts.query, keep_blank_values=True))
    return f"https://{netloc}{path}" + ("?" + urlencode(query) if query else "")


_NUMBER_WORDS = {
    word: str(num)
    for num, word in enumerate(
        "one two three four five six seven eight nine ten eleven twelve "
        "thirteen fourteen fifteen sixteen seventeen eighteen nineteen "
        "twenty".split(),
        start=1,
    )
}
_UNIT_SYNONYMS = {
    "s": "sec",
    "sec": "sec",
    "secs": "sec",
    "second": "sec",
    "seconds": "sec",
    "min": "min",
    "mins": "min",
    "minute": "min",
    "minutes": "min",
    "h": "hr",
    "hr": "hr",
    "hrs": "hr",
    "hour": "hr",
    "hours": "hr",
    "d": "day",
    "day": "day",
    "days": "day",
    "week": "week",
    "weeks": "week",
    "wk": "week",
    "mo": "month",
    "month": "month",
    "months": "month",
    "yr": "year",
    "yrs": "year",
    "year": "year",
    "years": "year",
    "ms": "ms",
    "millisecond": "ms",
    "milliseconds": "ms",
    "byte": "byte",
    "bytes": "byte",
    "kb": "kb",
    "kilobyte": "kb",
    "kilobytes": "kb",
    "mb": "mb",
    "megabyte": "mb",
    "megabytes": "mb",
    "gb": "gb",
    "gigabyte": "gb",
    "gigabytes": "gb",
    "tb": "tb",
    "terabyte": "tb",
    "terabytes": "tb",
}
_COUNT_NOUNS = (
    "request call item member contact product order email webhook key seat "
    "user page character word row record subscriber site domain campaign "
    "recipient attempt retry message file image attachment event field tag "
    "list customer donor student leader sponsor donation invoice"
).split()
_RATE_UNITS = (
    "second|sec|minute|min|hour|hr|day|week|month|mo|year|yr|user|seat|"
    "member|site|request|message|email"
)
_METHODS = "|".join("GET POST PUT PATCH DELETE HEAD OPTIONS TRACE".split())
_NUM = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
_RANGE = rf"{_NUM}(?:\s?(?:-|–|—|to|through)\s?{_NUM})?"
_RATE = rf"(?:\s?(?:per|/)[\s-]?(?:{_RATE_UNITS})s?\b)?"
_UNIT_WORDS = "|".join(
    sorted(
        [w for w in _UNIT_SYNONYMS if len(w) > 1]
        + [n + "s" for n in _COUNT_NOUNS]
        + [n + "es" for n in _COUNT_NOUNS]
        + ["retries", "business days?", "business day"]
        + _COUNT_NOUNS,
        key=len,
        reverse=True,
    )
)
_ATTACHED = r"(?:s|h|d)"
NUMBER_UNIT_RE = re.compile(
    rf"(?<![\w./$€£-])(?P<n>{_RANGE})"
    rf"(?:\s?(?P<u>{_UNIT_WORDS})\b|(?P<a>{_ATTACHED})\b){_RATE}",
    re.IGNORECASE,
)
MONEY_RE = re.compile(
    rf"(?:US\$|[$€£])\s?{_NUM}(?:\s?(?:k|m|million|billion)\b)?{_RATE}"
    rf"|(?<![\w.]){_NUM}\s?(?:USD|EUR|GBP|dollars?|euros?|pounds?)\b{_RATE}",
    re.IGNORECASE,
)
PERCENT_RE = re.compile(rf"(?<![\w.]){_NUM}\s?(?:%|percent\b|per cent\b)")
LIMIT_RE = re.compile(
    r"\b(?:limit|maximum|max|minimum|at most|at least|up to|no more than|"
    r"no fewer than|capped at)(?:\s+of)?\s+(?P<n>" + _NUM + r")(?![\d\w-])",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^\s)>\]`\"']+")
ENDPOINT_TEXT_RE = re.compile(rf"\b(?:{_METHODS})\s+/[^\s`)\]]+")
BACKTICK_RE = re.compile(r"`([^`\n]+)`")
MARKER_RE = re.compile(
    r"\[(?:S-\d{4}[^\]]*|ORG [^\]]+|RQ-[SPO]-\d{2,3}[^\]]*|\d{1,3}(?:,[^\]]*)?)\]"
)


class Token(NamedTuple):
    """One checkable claim in a line: its kind, raw text, and canonical form."""

    kind: str  # code | url | endpoint | money | percent | number
    text: str
    canon: str


def canon_text(text: str) -> str:
    """Return text with numbers, currencies, percents, and units normalized.

    Thousands separators go, ``50 percent`` becomes ``50%``, ``10 to 20`` and
    ``10-20`` agree, currency codes become symbols, spelled-out small numbers
    become digits, and unit synonyms collapse (``60 seconds`` is ``60 sec``,
    ``requests per minute`` is ``request/min``).
    """
    out = text.lower().replace("\xad", "")
    out = re.sub("[\N{HYPHEN}-\N{HORIZONTAL BAR}\N{MINUS SIGN}]", "-", out)
    out = out.replace("\xa0", " ").replace("\N{NARROW NO-BREAK SPACE}", "")
    out = out.replace("\N{THIN SPACE}", " ")
    out = re.sub(r"\b(" + "|".join(_NUMBER_WORDS) + r")\b", _word_to_digit, out)
    out = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", out)
    out = re.sub(r"(?<=\d)\.0+(?!\d)", "", out)
    for words, symbol in (
        (r"usd|us\$|dollars?", "$"),
        (r"eur|euros?", "€"),
        (r"gbp|pounds?", "£"),
    ):
        out = re.sub(rf"({_NUM})\s?(?:{words})(?!\w)", symbol + r"\1", out)
        out = re.sub(rf"(?<!\w)(?:{words})\s?({_NUM})", symbol + r"\1", out)
    out = re.sub(r"([$€£])\s+(\d)", r"\1\2", out)
    out = re.sub(r"(\d)\s?(?:%|percent\b|per cent\b|pct\b)", r"\1%", out)
    out = re.sub(r"(\d)\s?(?:-|to|through)\s?(\d)", r"\1-\2", out)
    out = re.sub(r"(\d)\s?(business days?)\b", r"\1 business-day", out)
    out = re.sub(rf"(\d)\s?({_UNIT_WORDS})\b", _unit_sub, out)
    out = re.sub(r"(\d)(s|h|d)\b", lambda m: m.group(1) + " " + _unit(m.group(2)), out)
    out = re.sub(
        rf"\s?(?:per|/)[\s-]?({_RATE_UNITS})s?\b",
        lambda m: "/" + _unit(m.group(1)),
        out,
    )
    return " ".join(out.split())


def _word_to_digit(match: "re.Match[str]") -> str:
    """Return the digit string for a spelled-out number."""
    return _NUMBER_WORDS[match.group(1)]


def _unit(word: str) -> str:
    """Return the canonical form of a unit word (singular, abbreviated)."""
    low = word.lower()
    if low in _UNIT_SYNONYMS:
        return _UNIT_SYNONYMS[low]
    if low == "retries":
        return "retry"
    if low.endswith("ies"):
        return low[:-3] + "y"
    for suffix in ("es", "s"):
        if low.endswith(suffix) and low[: -len(suffix)] in _COUNT_NOUNS:
            return low[: -len(suffix)]
    return low


def _unit_sub(match: "re.Match[str]") -> str:
    """Rewrite ``<digit> <unit words>`` with the canonical unit."""
    return match.group(1) + " " + _unit(match.group(2))


def claim_tokens(text: str) -> List[Token]:
    """Return the checkable tokens of a statement.

    Citation markers are ignored. A token is a backticked string, a URL, an
    ``METHOD /path`` endpoint, a price, a percentage, a number with a unit
    (or a rate), or a number after a limit word (``at most 25``). Dates,
    identifiers such as ``T07`` or ``RQ-S-03``, list numbers, and bare
    counts are not tokens.
    """
    clean = MARKER_RE.sub(" ", text)
    clean = re.sub(r"\]\([^)]*\)", "]", clean)
    spans: List[Tuple[int, int]] = []
    found: List[Tuple[int, Token]] = []

    def free(start: int, end: int) -> bool:
        return all(end <= a or start >= b for a, b in spans)

    def add(kind: str, start: int, end: int, raw: str, canon: str) -> None:
        if free(start, end) and canon:
            spans.append((start, end))
            found.append((start, Token(kind, raw.strip(), canon)))

    for match in BACKTICK_RE.finditer(clean):
        inner = match.group(1).strip()
        add("code", match.start(), match.end(), inner, inner)
    for match in URL_RE.finditer(clean):
        url = match.group(0).rstrip(".,;:")
        add("url", match.start(), match.start() + len(url), url, url)
    for match in ENDPOINT_TEXT_RE.finditer(clean):
        raw = match.group(0).rstrip(".,;:")
        add("endpoint", match.start(), match.start() + len(raw), raw, raw)
    for match in MONEY_RE.finditer(clean):
        add("money", match.start(), match.end(), match.group(0), canon_text(match[0]))
    for match in PERCENT_RE.finditer(clean):
        add("percent", match.start(), match.end(), match.group(0), canon_text(match[0]))
    for match in NUMBER_UNIT_RE.finditer(clean):
        add("number", match.start(), match.end(), match.group(0), canon_text(match[0]))
    for match in LIMIT_RE.finditer(clean):
        add(
            "number",
            match.start("n"),
            match.end("n"),
            match.group("n"),
            canon_text(match.group("n")),
        )
    found.sort(key=lambda pair: pair[0])
    seen: Set[Tuple[str, str]] = set()
    tokens: List[Token] = []
    for _, token in found:
        key = (token.kind, token.canon)
        if key not in seen:
            seen.add(key)
            tokens.append(token)
    return tokens


def url_forms(text: str) -> Set[str]:
    """Return the canonical forms of every URL in the text."""
    return {canonical_url(u.rstrip(".,;:")) for u in URL_RE.findall(text)}


def token_supported(token: Token, raw: str, canon: str) -> bool:
    """Return True when the evidence text supports the token.

    ``raw`` is the evidence text (quotes and artifacts joined) and ``canon`` is
    ``canon_text(raw)``. Code, endpoint, and URL tokens must appear verbatim
    (a URL may differ by scheme, host case, fragment, or trailing slash);
    numeric tokens are compared after normalization.
    """
    if token.kind in ("code", "endpoint"):
        return token_in_text(token.text, raw)
    if token.kind == "url":
        return token.text in raw or canonical_url(token.text) in url_forms(raw)
    pattern = r"(?<![\d.])" + re.escape(token.canon) + r"(?![\d])"
    return re.search(pattern, canon) is not None


def token_conflicts(token: Token, canon: str) -> List[str]:
    """Return values the evidence gives for the same unit as a numeric token.

    A token such as ``60 request/min`` conflicts with evidence that says
    ``120 request/min``; the list is empty for other kinds or when the
    evidence has no number with that unit.
    """
    if token.kind not in ("money", "percent", "number"):
        return []
    match = re.match(r"^([$€£]?)(\d[\d.]*(?:-\d[\d.]*)?)(.*)$", token.canon)
    if not match or not (match.group(1) or match.group(3).strip()):
        return []
    prefix, value, tail = match.groups()
    pattern = (
        r"(?<![\d.])"
        + re.escape(prefix)
        + r"(\d[\d.]*(?:-\d[\d.]*)?)"
        + re.escape(tail)
        + r"(?![\w%])"
    )
    return sorted({v for v in re.findall(pattern, canon) if v != value})


def evidence_text(quotes: Iterable[str]) -> Tuple[str, str]:
    """Return (raw, canonical) evidence text from quotes and artifacts."""
    raw = "\n".join(normalize(q, keep_hyphen=True) for q in quotes if q)
    return raw, canon_text(raw)


# --------------------------------------------------------------------------
# The check of one claim and the command line
# --------------------------------------------------------------------------
def check_claim(claim: Dict[str, Any], source_text: str) -> List[str]:
    """Return the failures of one claim; an empty list means it passes."""
    quote = claim.get("quote")
    if not isinstance(quote, str):
        return ["quote: must be a string"]
    failures = _quote_failures(quote, source_text)
    artifacts = claim.get("artifacts") or []
    if not isinstance(artifacts, list):
        return failures + ["artifacts: must be a list"]
    good: List[str] = []
    for item in artifacts:
        problem = _artifact_failure(item, source_text)
        if problem:
            failures.append(problem)
        else:
            good.append(item)
    statement = claim.get("statement")
    if statement is None:
        return failures
    if not isinstance(statement, str):
        return failures + ["statement: must be a string"]
    return failures + _statement_failures(statement, [quote] + good)


def _quote_failures(quote: str, source_text: str) -> List[str]:
    """Return the failures of a quote's length and of its verbatim match."""
    flat = normalize(quote)
    if len(flat) < MIN_QUOTE_CHARS:
        return [f"quote: has {len(flat)} characters; the minimum is {MIN_QUOTE_CHARS}"]
    if not quote_in_source(quote, source_text):
        return [f"quote: does not occur verbatim in the source: {flat[:60]!r}"]
    return []


def _artifact_failure(item: Any, source_text: str) -> str:
    """Return the failure of one artifact, or an empty string when it passes."""
    if not isinstance(item, str) or not item.strip():
        return f"artifacts: entry {item!r} must be a string"
    if not quote_in_source(item, source_text):
        return f"artifacts: {item!r} does not occur verbatim in the source"
    return ""


def _statement_failures(statement: str, evidence: List[str]) -> List[str]:
    """Return one failure per statement token the evidence does not support."""
    raw, canon = evidence_text(evidence)
    failures: List[str] = []
    for token in claim_tokens(statement):
        if token_supported(token, raw, canon):
            continue
        message = (
            f"statement: {token.kind} {token.text!r} is in neither the quote "
            "nor the artifacts (numbers are compared after normalization)"
        )
        other = token_conflicts(token, canon)
        if other:
            message += "; the evidence gives " + ", ".join(other)
        failures.append(message)
    return failures


def _load_claims(args: argparse.Namespace) -> List[Dict[str, Any]]:
    """Return the claims named by ``--claims`` or by the single-claim flags."""
    if args.claims:
        data = json.loads(_read(args.claims))
        if not isinstance(data, list) or not all(isinstance(c, dict) for c in data):
            raise ValueError("claims file must hold a list of objects")
        return data
    if args.quote is None:
        raise ValueError("give --claims FILE or --quote TEXT")
    return [
        {"quote": args.quote, "statement": args.statement, "artifacts": args.artifact}
    ]


def _read(path: str) -> str:
    """Return a file's text; ``-`` is standard input."""
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8", errors="replace")


def build_parser() -> argparse.ArgumentParser:
    """The command-line parser."""
    parser = argparse.ArgumentParser(
        description="Check that quotes are verbatim in a source file and that "
        "every number, URL, endpoint and code token of a statement is in its quote."
    )
    parser.add_argument("source", help="the source text file, or - for stdin")
    parser.add_argument("--claims", metavar="FILE", help="JSON list of claims")
    parser.add_argument("--quote", help="one quote to check")
    parser.add_argument("--statement", help="the statement resting on the quote")
    parser.add_argument(
        "--artifact", action="append", default=[], help="one artifact; repeatable"
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Check the claims against the source and print the JSON result."""
    args = build_parser().parse_args(argv)
    if args.claims == "-" and args.source == "-":
        print("check_quotes: only one input can be standard input", file=sys.stderr)
        return 2
    try:
        source_text = _read(args.source)
        claims = _load_claims(args)
    except (OSError, ValueError) as exc:
        print(f"check_quotes: {exc}", file=sys.stderr)
        return 2
    results: List[Dict[str, Any]] = []
    for number, claim in enumerate(claims, start=1):
        failures = check_claim(claim, source_text)
        label = str(claim.get("id", number))
        results.append({"id": label, "ok": not failures, "failures": failures})
    failed = sum(1 for item in results if not item["ok"])
    print(
        json.dumps(
            {"source": args.source, "claims": results, "failed": failed},
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    for item in results:
        for failure in item["failures"]:
            print(f"check_quotes: claim {item['id']}: {failure}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
