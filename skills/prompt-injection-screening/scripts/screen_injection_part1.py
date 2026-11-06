"""Text checks of the injection screen (part 1 of ``screen_injection.py``).

Holds the constants, the patterns, ``screen_text``, ``screen_document_text``,
``status_of`` and ``check_text``. The checks return findings and a status and
never decide quarantine. Text found in a document is data, never an
instruction: nothing here executes or follows it.
"""

# pylint: disable=too-many-locals  # screen_text reports each signal it finds
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

CONTEXT_CHARS = 80
BASE64_MIN_RUN = 200
TINY_HEIGHT_PT = 2.0
MIN_WORDS = 8
OFFPAGE_MIN_VISIBLE = 0.5
COMMENT_MIN_WORDS = 4
TINY_FONT_PX = 1.0

KIND_OVERRIDE = "override-phrase"
KIND_INVISIBLE = "invisible-codepoint"
KIND_HTML_COMMENT = "html-comment-instruction"
KIND_BASE64 = "base64-blob"
KIND_CITED_TITLE = "cited-title"
KIND_OFFPAGE = "offpage-text"
KIND_TINY = "tiny-text"
KIND_HIDDEN_HTML = "hidden-html-text"
KIND_ATTRIBUTE = "attribute-text"
KIND_PAYLOAD = "payload-or-command"
HIDDEN_KINDS = frozenset(
    {
        KIND_INVISIBLE,
        KIND_OFFPAGE,
        KIND_TINY,
        KIND_HIDDEN_HTML,
        KIND_ATTRIBUTE,
        KIND_HTML_COMMENT,
    }
)
STATUS_CLEAN = "clean"
STATUS_FLAGGED = "flagged"
STATUS_BENIGN = "benign-quoted-content"

_OVERRIDE_SOURCES = [
    r"\b(?:ignore|disregard|forget|override|bypass)\s+(?:all\s+|any\s+|every\s+|"
    r"the\s+|your\s+|these\s+|those\s+)*(?:previous|prior|above|earlier|preceding|"
    r"foregoing|former)\s+(?:instructions?|prompts?|context|directions?|"
    r"messages?|rules?|guidelines?|text)\b",
    r"\b(?:ignore|disregard)\s+(?:everything|anything)\s+(?:above|before)\b",
    r"\b(?:ignore|disregard)\s+the\s+(?:above|following)\b",
    r"\bignore\s+any\s+(?:prior|previous)\b",
    r"\b(?:reveal|print|repeat|show|output|display|leak|disclose|expose|"
    r"exfiltrate)\s+(?:me\s+|us\s+)?(?:your|the)\s+(?:system|hidden|initial|"
    r"original|secret)\s+(?:prompt|instructions?|message)\b",
    r"\bwhat\s+(?:is|are)\s+your\s+(?:system|initial|original)\s+"
    r"(?:prompt|instructions?)\b",
    r"\byou\s+are\s+now\b",
    r"\bfrom\s+now\s+on,?\s+you\s+(?:are|will|must|should|shall)\b",
    r"\byour\s+(?:new\s+)?(?:task|role|persona|objective|instructions?)\s+"
    r"(?:is|are|will\s+be)\b",
    r"\bpretend\s+(?:to\s+be|that\s+you\s+are|you\s+are)\b",
    r"\bassume\s+the\s+role\s+of\b",
    r"\bact\s+as\s+(?:if\s+you\s+(?:are|were)|my)\b",
    r"\bas\s+an?\s+(?:ai(?:\s+language\s+model)?|llm|language\s+model|"
    r"assistant),?\s+you\s+"
    r"(?:must|should|will|shall)\b",
    r"\bdo\s+not\s+summari[sz]e\s+this\b",
    r"\brespond\s+only\s+with\b",
    r"\bgive\s+(?:this|the)\s+paper\s+a\s+(?:positive|favou?rable|high)\b",
    r"\b(?:positive|favou?rable)\s+review\s+only\b",
    r"\bdo\s+not\s+(?:mention|tell|reveal|disclose)\s+(?:this|that|it)\s+to\s+the\s+"
    r"(?:user|human|reader)\b",
    r"<\|(?:im_start|im_end|system|assistant|user)\|>",
    r"\[/?INST\]",
]
OVERRIDE_RE = re.compile("|".join(f"(?:{s})" for s in _OVERRIDE_SOURCES), re.I)

# Zero-width and direction-control code points, the byte-order mark, the
# Mongolian vowel separator, and the Unicode tag block (a plain-text
# checklist). Built from numbers so no invisible character sits in the source.
_INVISIBLE_RANGES = (
    (0x200B, 0x200F),
    (0x202A, 0x202E),
    (0x2060, 0x2064),
    (0x2066, 0x2069),
    (0xFEFF, 0xFEFF),
    (0x180E, 0x180E),
    (0xE0000, 0xE007F),
)
_INVISIBLE_RE = re.compile(
    "[" + "".join(f"{chr(low)}-{chr(high)}" for low, high in _INVISIBLE_RANGES) + "]+"
)
_BOM = chr(0xFEFF)
_LDQUO = chr(0x201C)
_RDQUO = chr(0x201D)
_BASE64_RE = re.compile(rf"[A-Za-z0-9+/]{{{BASE64_MIN_RUN},}}={{0,2}}")
_HTML_COMMENT_RE = re.compile(r"<!--(.*?)-->", re.S)
# Docling writes this exact comment where a picture was not exported. Only a
# body that equals it is exempt; any other wording keeps its finding.
_DOCLING_PLACEHOLDER_RE = re.compile(
    r"\s*\U0001f5bc️?❌\s*Image not available\.\s*Please use\s*"
    r"`PdfPipelineOptions\(generate_picture_images=True\)`\s*"
)
_COMMENT_CUE_RE = re.compile(
    r"\b(?:ignore|disregard|you\s+(?:must|should|are|will)|do\s+not|don'?t|"
    r"please|instruction|system\s+prompt|assistant|ai\s+(?:model|agent|reviewer)|"
    r"llm|language\s+model|reviewer|note\s+to|respond|output|always|never|"
    r"send|update|delete|execute|run\s+the|call\s+the)\b",
    re.I,
)
_INTRO_RE = re.compile(
    r"(?:prompts?|templates?)\s*(?:\(.*?\))?\s*"
    r"(?:is|are|was|were|reads?|looks?\s+like|as\s+follows?|below|shown|given|"
    r"used|follows?|:)|following\s+(?:prompt|template)|"
    r"(?:prompt|template)\s+(?:we|is|was)\s+use|\blisting\s+\d+|"
    r"\bfigure\s+\d+|\bwe\s+prompt\b|\bsystem\s+message\b",
    re.I,
)
_CITATION_LINE_RE = re.compile(
    r"(?:\b(?:19|20)\d{2}\b|\bdoi\b|\bpp\.|\bet\s+al\b|\bproc\.|"
    r"\bin:\s|\bvol\.|\bjournal\b|\bconference\b|\bieee\b|\bacm\b|\"|" + _LDQUO + ")",
    re.I,
)


def _context(text: str, start: int, end: int) -> str:
    """Return the surrounding text with whitespace collapsed."""
    lo = max(0, start - CONTEXT_CHARS)
    hi = min(len(text), end + CONTEXT_CHARS)
    return re.sub(r"\s+", " ", text[lo:hi]).strip()


def _finding(
    kind: str, start: int, end: int, context: str, benign: bool = False
) -> Dict[str, Any]:
    """Build a finding dict."""
    return {
        "kind": kind,
        "span": [start, end],
        "context": context,
        "benign_candidate": benign,
    }


def _line_bounds(text: str, pos: int) -> Tuple[int, int]:
    """Return the start and end offsets of the line holding `pos`."""
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return start, len(text) if end == -1 else end


def _inside_fence(text: str, pos: int) -> bool:
    """True if `pos` is inside a triple-backtick or triple-tilde fence."""
    fences = [m.start() for m in re.finditer(r"^[ \t]*(?:```|~~~)", text, re.M)]
    count = sum(1 for f in fences if f < pos)
    return count % 2 == 1


def _quoted_or_listing_line(text: str, pos: int) -> bool:
    """True if the line is a blockquote, indented listing, or quoted string."""
    start, end = _line_bounds(text, pos)
    line = text[start:end]
    if re.match(r"^\s*>", line) or re.match(r"^(?: {4}|\t)\S", line):
        return True
    before = text[start:pos]
    after = text[pos:end]
    ascii_quoted = before.count('"') % 2 == 1 and '"' in after
    curly_quoted = before.count(_LDQUO) > before.count(_RDQUO) and _RDQUO in after
    return ascii_quoted or curly_quoted


def _in_inline_code(text: str, pos: int) -> bool:
    """True if `pos` lies between a pair of single backticks on its line."""
    start, end = _line_bounds(text, pos)
    before, after = text[start:pos], text[pos:end]
    return before.count("`") % 2 == 1 and "`" in after


def _quoted(text: str, pos: int) -> bool:
    """True if `pos` is in a fence, a listing, a quotation, or inline code."""
    return (
        _inside_fence(text, pos)
        or _quoted_or_listing_line(text, pos)
        or _in_inline_code(text, pos)
    )


def _benign_visible(text: str, start: int) -> bool:
    """Heuristic for visible prompt text in a listing, figure, or introduced prompt."""
    if _quoted(text, start):
        return True
    first = max(0, start - 300)
    return _INTRO_RE.search(text[first:start]) is not None


def _is_cited_title(text: str, start: int, end: int) -> bool:
    """True if the line around a match looks like a bibliography entry."""
    lo, hi = _line_bounds(text, start)
    line = text[lo:hi]
    if len(line) > 500:
        return False
    looks_cited = _CITATION_LINE_RE.search(line) is not None
    return looks_cited and (end - start) < 0.8 * max(len(line), 1)


_PAYLOAD_SOURCES = [
    r"\b(?:curl|wget)\b[^\n|]{0,200}\|\s*(?:sudo\s+)?(?:ba|z|da)?sh\b",
    r"\brm\s+-[a-z]*r[a-z]*f?[a-z]*\s+(?:--no-preserve-root\s+)?/(?:\s|$|\*)",
    r"\bbase64\s+(?:-d|--decode)\b[^\n|]{0,100}\|\s*(?:ba|z)?sh\b",
    r"\b(?:nc|ncat|netcat)\b[^\n]{0,40}\s-e\s",
    r"\bbash\s+-i\s*>&\s*[/]dev[/]tcp[/]",
    r"\bpowershell(?:\.exe)?\b[^\n]{0,40}\s-(?:enc|encodedcommand)\b",
    r"<script\b[^>]*>",
    r"\bjavascript:",
    r"['\"]\s*or\s+['\"]?1['\"]?\s*=\s*['\"]?1\b",
    r";\s*drop\s+table\b",
    r"\$\([^)\n]{1,80}\)\s*;?\s*(?:curl|wget)\b",
    r"\bchmod\s+(?:-R\s+)?[0-7]*777\s+/(?:\s|$)",
]
PAYLOAD_RE = re.compile("|".join(f"(?:{s})" for s in _PAYLOAD_SOURCES), re.I)


def screen_text(
    text: str, in_references: bool = False, payloads: bool = False
) -> List[Dict[str, Any]]:
    """Run the text checks on `text` and return the findings.

    Spans are character offsets in `text`. With `in_references=True` an
    override phrase on a bibliography-like line is returned as `cited-title`.
    With `payloads=True` shell commands and injection payloads are reported as
    `payload-or-command`; they are benign when quoted (fence, listing,
    blockquote, inline code, or an introducing sentence). A base64 blob is
    benign only when it sits in a fence, a listing, a quotation, or inline code
    (a sample body or signature in documentation).
    """
    findings: List[Dict[str, Any]] = []
    if payloads:
        for match in PAYLOAD_RE.finditer(text):
            start, end = match.span()
            quoted = _benign_visible(text, start)
            findings.append(
                _finding(KIND_PAYLOAD, start, end, _context(text, start, end), quoted)
            )
    for match in OVERRIDE_RE.finditer(text):
        start, end = match.span()
        ctx = _context(text, start, end)
        if in_references and _is_cited_title(text, start, end):
            findings.append(_finding(KIND_CITED_TITLE, start, end, ctx, True))
        else:
            findings.append(
                _finding(KIND_OVERRIDE, start, end, ctx, _benign_visible(text, start))
            )
    for match in _INVISIBLE_RE.finditer(text):
        start, end = match.span()
        if start == 0 and end == 1 and text[0] == _BOM:
            continue  # a lone leading byte-order mark is an encoding artifact
        points = ", ".join(f"U+{ord(ch):04X}" for ch in match.group(0)[:12])
        ctx = f"codepoints {points} | {_context(text, start, end)}"
        findings.append(_finding(KIND_INVISIBLE, start, end, ctx))
    for match in _HTML_COMMENT_RE.finditer(text):
        body = match.group(1)
        if _DOCLING_PLACEHOLDER_RE.fullmatch(body):
            continue  # Docling's own picture placeholder, not page content
        if len(body.split()) >= COMMENT_MIN_WORDS and (
            _COMMENT_CUE_RE.search(body) or OVERRIDE_RE.search(body)
        ):
            start, end = match.span()
            findings.append(
                _finding(KIND_HTML_COMMENT, start, end, _context(text, start, end))
            )
    for match in _BASE64_RE.finditer(text):
        start, end = match.span()
        findings.append(
            _finding(
                KIND_BASE64,
                start,
                end,
                f"{end - start} base64 chars | {_context(text, start, start + 20)}",
                _quoted(text, start),
            )
        )
    findings.sort(key=lambda f: f["span"][0])
    return finalize(findings)


def finalize(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clear `benign_candidate` on every finding if a hidden-text signal exists.

    Cited titles stay benign (they are counted, not held).
    """
    if any(f["kind"] in HIDDEN_KINDS for f in findings):
        for finding in findings:
            if finding["kind"] != KIND_CITED_TITLE:
                finding["benign_candidate"] = False
    return findings


def split_at_references(text: str, heading: str) -> Tuple[str, str, int]:
    """Split `text` at the last line whose heading text equals `heading`.

    Returns (before, after, offset of `after`); `after` starts at the heading
    line. If the heading is absent, `after` is empty.
    """
    wanted = heading.strip().lower()
    offset = None
    pos = 0
    for line in text.splitlines(keepends=True):
        stripped = re.sub(r"^[#\s*_]+|[#\s*_:]+$", "", line.strip()).lower()
        if stripped == wanted:
            offset = pos
        pos += len(line)
    if offset is None:
        return text, "", len(text)
    return text[:offset], text[offset:], offset


def screen_document_text(
    text: str, references_after: Optional[str] = None, payloads: bool = True
) -> List[Dict[str, Any]]:
    """Screen converted text, treating the part after a references heading as such.

    Commands and payloads are checked by default (`payloads=True`): a quoted one
    in a documentation page is benign, an unquoted one is held.
    """
    if not references_after:
        return screen_text(text, payloads=payloads)
    before, after, offset = split_at_references(text, references_after)
    findings = screen_text(before, payloads=payloads)
    if after:
        for item in screen_text(after, in_references=True, payloads=payloads):
            item["span"] = [item["span"][0] + offset, item["span"][1] + offset]
            findings.append(item)
    findings.sort(key=lambda f: f["span"][0])
    return finalize(findings)


def status_of(findings: Sequence[Dict[str, Any]]) -> str:
    """The injection screen status a list of findings amounts to.

    ``flagged`` when any finding is neither benign nor a cited title;
    ``benign-quoted-content`` when findings exist and all are benign quotes;
    ``clean`` when there is nothing, or only cited titles.
    """
    real = [f for f in findings if f["kind"] != KIND_CITED_TITLE]
    if any(not f["benign_candidate"] for f in real):
        return STATUS_FLAGGED
    return STATUS_BENIGN if real else STATUS_CLEAN


def check_text(text: str, references_after: Optional[str] = None) -> Dict[str, Any]:
    """Screen a snippet, abstract, or Markdown text.

    Returns ``{"status", "findings"}``; ``status`` is ``clean``,
    ``benign-quoted-content`` (quoted commands, payloads, or prompt text with
    no hidden-text signal beside them), or ``flagged``.
    """
    findings = screen_document_text(text, references_after, payloads=True)
    return {"status": status_of(findings), "findings": findings}
