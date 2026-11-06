"""Docling JSON and HTML checks of the injection screen (part 2).

Holds ``screen_docling_json`` (off-page and tiny text) and ``check_html``
(hidden text, attribute text, comments, and the text checks on the visible
text), built on the text checks of part 1.
"""

# pylint: disable=too-many-locals  # check_html reports each signal it finds
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from screen_injection_part1 import (
    _COMMENT_CUE_RE,
    COMMENT_MIN_WORDS,
    CONTEXT_CHARS,
    KIND_ATTRIBUTE,
    KIND_HIDDEN_HTML,
    KIND_HTML_COMMENT,
    KIND_OFFPAGE,
    KIND_TINY,
    MIN_WORDS,
    OFFPAGE_MIN_VISIBLE,
    OVERRIDE_RE,
    PAYLOAD_RE,
    TINY_FONT_PX,
    TINY_HEIGHT_PT,
    _finding,
    finalize,
    screen_text,
    status_of,
)


def _page_sizes(doc: Dict[str, Any]) -> Dict[int, Tuple[float, float]]:
    """Map page number to (width, height) from a Docling `pages` field."""
    pages = doc.get("pages") or {}
    entries = pages.items() if isinstance(pages, dict) else enumerate(pages, start=1)
    sizes: Dict[int, Tuple[float, float]] = {}
    for key, page in entries:
        if not isinstance(page, dict):
            continue
        size = page.get("size") or {}
        try:
            number = int(str(page.get("page_no", key)))
            sizes[number] = (float(size["width"]), float(size["height"]))
        except (KeyError, TypeError, ValueError):
            continue
    return sizes


def _axis_visible(low: float, high: float, limit: float) -> float:
    """Fraction of the interval [low, high] that lies inside [0, limit]."""
    low, high = min(low, high), max(low, high)
    length = high - low
    if length <= 0:
        return 1.0 if 0 <= low <= limit else 0.0
    return max(0.0, min(high, limit) - max(low, 0.0)) / length


def screen_docling_json(path: Any) -> List[Dict[str, Any]]:
    """Flag Docling `texts[]` items off the page or under 2 pt high.

    An item is reported when it holds 8 or more words and its `prov[].bbox`
    (keys `l,t,r,b`) lies mostly outside `pages[n].size`, or its height is
    under 2 pt. Missing keys are tolerated. Raises ValueError on invalid JSON.
    """
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"not valid JSON: {path}: {exc}") from exc
    if not isinstance(doc, dict):
        return []
    sizes = _page_sizes(doc)
    findings: List[Dict[str, Any]] = []
    for index, item in enumerate(doc.get("texts") or []):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "")
        if len(text.split()) < MIN_WORDS:
            continue
        for prov in item.get("prov") or []:
            bbox = prov.get("bbox") if isinstance(prov, dict) else None
            if not isinstance(bbox, dict):
                continue
            try:
                left, right = float(bbox["l"]), float(bbox["r"])
                top, bottom = float(bbox["t"]), float(bbox["b"])
            except (KeyError, TypeError, ValueError):
                continue
            page = prov.get("page_no")
            where = (
                f"texts[{index}] page {page} bbox "
                f"({left:.1f},{top:.1f},{right:.1f},{bottom:.1f})"
            )
            snippet = re.sub(r"\s+", " ", text)[:120]
            if abs(top - bottom) < TINY_HEIGHT_PT:
                findings.append(
                    _finding(
                        KIND_TINY,
                        0,
                        len(text),
                        f"{where} height {abs(top - bottom):.2f}pt: {snippet}",
                    )
                )
            size = sizes.get(page) if isinstance(page, int) else None
            if size is None:
                continue
            visible = _axis_visible(left, right, size[0]) * _axis_visible(
                bottom, top, size[1]
            )
            if visible < OFFPAGE_MIN_VISIBLE:
                findings.append(
                    _finding(
                        KIND_OFFPAGE,
                        0,
                        len(text),
                        f"{where} page {size[0]:.0f}x{size[1]:.0f}: {snippet}",
                    )
                )
    return findings


# --------------------------------------------------------------------------
# HTML: hidden text, attribute text, and comments
# --------------------------------------------------------------------------

_VOID_TAGS = frozenset(
    "area base br col embed hr img input link meta param source track wbr".split()
)
_SKIP_TEXT = frozenset({"script", "style", "template", "head"})
_ATTR_TEXT = ("alt", "title", "aria-label")
_CODE_TAGS = frozenset({"code", "samp", "kbd", "tt"})
_NAMED_COLOURS = {
    "white": "#ffffff",
    "black": "#000000",
    "red": "#ff0000",
    "gray": "#808080",
    "grey": "#808080",
    "silver": "#c0c0c0",
}
_BIG_NEGATIVE = re.compile(r"^-\s*(\d{4,})(?:px|pt|em|rem|vw)?$")
_ZERO = re.compile(r"^0*\.?0+(?:px|pt|em|rem|%|ex|ch|vw|vh)?$")
_ZERO_OPACITY = re.compile(r"^0*\.?0+%?$")
_TINY_FONT = re.compile(r"^(\d*\.?\d+)(px|pt)$")
_CLIPPED = re.compile(
    r"rect\(\s*0(?:px)?[\s,]+0(?:px)?[\s,]+0(?:px)?[\s,]+0(?:px)?\s*\)|"
    r"inset\(\s*(?:50|100)%|circle\(\s*0"
)


def _norm_colour(value: str) -> Optional[str]:
    """A CSS colour as ``#rrggbb``; None for transparent, inherit, or unknown."""
    text = value.strip().lower().replace("!important", "").strip()
    if text in _NAMED_COLOURS:
        return _NAMED_COLOURS[text]
    match = re.fullmatch(r"#([0-9a-f]{3})", text)
    if match:
        return "#" + "".join(ch * 2 for ch in match.group(1))
    if re.fullmatch(r"#[0-9a-f]{6}", text):
        return text
    match = re.fullmatch(
        r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,[^)]*)?\)", text
    )
    if match:
        return "#" + "".join(f"{min(int(g), 255):02x}" for g in match.groups())
    return None


def _declarations(block: str) -> Dict[str, str]:
    """Parse ``a:b;c:d`` into a lowercase property map."""
    out: Dict[str, str] = {}
    for part in block.split(";"):
        name, _, value = part.partition(":")
        if name.strip() and value.strip():
            out[name.strip().lower()] = value.strip().lower()
    return out


def _tiny_font(size: str) -> bool:
    """True for a font size of 1 px or 1 pt or less (a zero size is `_ZERO`)."""
    match = _TINY_FONT.match(size)
    return match is not None and float(match.group(1)) <= TINY_FONT_PX


def _hiding_signals(decl: Dict[str, str]) -> List[str]:
    """The hidden-text signals one declaration map carries."""
    found: List[str] = []
    clean = {k: v.replace("!important", "").strip() for k, v in decl.items()}
    if clean.get("display") == "none":
        found.append("display-none")
    if clean.get("visibility") in ("hidden", "collapse"):
        found.append("visibility-hidden")
    if _ZERO_OPACITY.match(clean.get("opacity", "x")):
        found.append("opacity-zero")
    size = clean.get("font-size", "")
    if size and (_ZERO.match(size) or size in ("0px", "0pt")):
        found.append("zero-font-size")
    elif size and _tiny_font(size):
        found.append("tiny-font-size")
    for prop in ("left", "right", "top", "bottom", "text-indent", "margin-left"):
        if _BIG_NEGATIVE.match(clean.get(prop, "")):
            found.append("offscreen")
            break
    if any(_CLIPPED.search(clean.get(p, "")) for p in ("clip", "clip-path")):
        found.append("clipped")
    sizes = (clean.get("width", "x"), clean.get("height", "x"))
    if clean.get("overflow") == "hidden" and any(_ZERO.match(s) for s in sizes):
        found.append("zero-size-box")
    return found


def _selector_matches(selector: str, tag: str, attrs: Dict[str, str]) -> bool:
    """Match a simple selector: ``tag``, ``.class``, ``#id``, or ``tag.class``."""
    match = re.fullmatch(r"([a-z][a-z0-9]*)?(?:\.([\w-]+))?(?:#([\w-]+))?", selector)
    if not match or not any(match.groups()):
        return False
    want_tag, want_class, want_id = match.groups()
    classes = attrs.get("class", "").split()
    return (
        (want_tag is None or want_tag == tag)
        and (want_class is None or want_class in classes)
        and (want_id is None or want_id == attrs.get("id"))
    )


class _Mode:  # pylint: disable=too-few-public-methods
    """What the page parser is inside: a stylesheet, a code block, code, a quote."""

    def __init__(self) -> None:
        self.style = False
        self.pre: Optional[List[str]] = None  # raw text of the open <pre>
        self.code = 0  # open inline code elements
        self.quote = 0  # open blockquotes


class _Page(HTMLParser):
    """Collect visible text, hidden text, attribute text, and comments.

    Visible text keeps its quoting: a ``<pre>`` becomes a fenced block, inline
    code gets backticks, and a blockquote line starts with ``>``, so the text
    checks see documentation code as quoted.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: List[Dict[str, Any]] = []
        self.rules: List[Tuple[str, Dict[str, str]]] = []
        self.visible: List[str] = []
        self.hidden: List[Tuple[str, str]] = []  # (signal, text)
        self.attributes: List[Tuple[str, str]] = []  # (where, text)
        self.comments: List[str] = []
        self.mode = _Mode()

    # -- helpers
    def _top(self) -> Dict[str, Any]:
        return self.stack[-1] if self.stack else {"signals": [], "colour": None}

    def _open(self, tag: str, attrs: Dict[str, str]) -> None:
        parent = self._top()
        decl: Dict[str, str] = {}
        for selector, rule in self.rules:
            parts = [s.strip() for s in selector.split(",")]
            if any(_selector_matches(s, tag, attrs) for s in parts):
                decl.update(rule)
        decl.update(_declarations(attrs.get("style", "")))
        signals = list(parent["signals"]) + _hiding_signals(decl)
        if attrs.get("aria-hidden", "").lower() == "true":
            signals.append("aria-hidden")
        if "hidden" in attrs:
            signals.append("hidden-attribute")
        colour = _norm_colour(decl.get("color", "")) or parent["colour"]
        background = (
            _norm_colour(decl.get("background-color", ""))
            or _norm_colour(decl.get("background", ""))
            or parent.get("background")
        )
        if colour is not None and colour == background:
            signals.append("same-colour")
        elif colour == "#ffffff" and background is None and "color" in decl:
            signals.append("same-colour")
        self.stack.append(
            {
                "tag": tag,
                "signals": list(dict.fromkeys(signals)),
                "colour": colour,
                "background": background,
            }
        )

    def _close_pre(self) -> None:
        """End a `<pre>`: its text becomes one fenced block (unless already fenced)."""
        body = "".join(self.mode.pre or []).strip("\n")
        self.mode.pre = None
        if not body.strip():
            return
        if re.match(r"\s*(?:```|~~~)", body):
            self.visible.append(body)
        else:
            self.visible.append(f"```\n{body}\n```")

    def _quote(self, text: str) -> str:
        """Visible text with the quoting of the element it sits in."""
        if self.mode.code:
            return f"`{text}`"
        return f"> {text}" if self.mode.quote else text

    # -- parser hooks
    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        values = {k.lower(): (v or "") for k, v in attrs}
        if tag == "style":
            self.mode.style = True
        if tag == "meta" and values.get("content"):
            name = values.get("name") or values.get("property") or "meta"
            self.attributes.append((f"meta {name}", values["content"]))
        self._open(tag, values)
        if tag == "pre" and self.mode.pre is None:
            self.mode.pre = []
        elif tag in _CODE_TAGS:
            self.mode.code += 1
        elif tag == "blockquote":
            self.mode.quote += 1
        for key in _ATTR_TEXT:
            if values.get(key):
                self.attributes.append((f"{tag} {key}", values[key]))
        if tag in _VOID_TAGS:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self.mode.style = False
        if tag == "pre" and self.mode.pre is not None:
            self._close_pre()
        elif tag in _CODE_TAGS and self.mode.code:
            self.mode.code -= 1
        elif tag == "blockquote" and self.mode.quote:
            self.mode.quote -= 1
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if self.mode.style:
            for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", data):
                self.rules.append((selector.strip().lower(), _declarations(body)))
            return
        top = self._top()
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            if self.mode.pre is not None and not top["signals"]:
                self.mode.pre.append(data)
            return
        if top.get("tag") == "title":
            self.attributes.append(("title element", text))
        elif top.get("tag") in _SKIP_TEXT:
            return
        elif top["signals"]:
            self.hidden.append((",".join(top["signals"]), text))
        elif self.mode.pre is not None:
            self.mode.pre.append(data)
        else:
            self.visible.append(self._quote(text))

    def handle_comment(self, data: str) -> None:
        self.comments.append(data)


def _instruction_like(text: str) -> bool:
    """True when hidden or attribute text reads like an instruction."""
    words = len(text.split())
    if OVERRIDE_RE.search(text):
        return True
    if PAYLOAD_RE.search(text):
        return True
    return words >= MIN_WORDS and _COMMENT_CUE_RE.search(text) is not None


def check_html(html: str) -> Dict[str, Any]:
    """Screen an HTML document: hidden text, attribute text, comments, text.

    Hidden-text signals: ``display:none``, ``visibility:hidden``,
    ``opacity:0``, a zero or 1 px font size, off-screen positioning, ``clip``, a
    zero-size box with hidden overflow, text the colour of its background (a
    page background of white is assumed when none is set), ``aria-hidden``, and
    the ``hidden`` attribute; plus instruction-like ``alt``, ``title``,
    ``aria-label``, ``<meta content>``, and ``<title>`` text and HTML comments.
    The visible text then gets the text checks, with commands and payloads
    quoted in it (``<pre>``, inline code, a blockquote) benign unless one of
    those hidden-text signals is also present.
    """
    page = _Page()
    page.feed(html)
    page.close()
    findings: List[Dict[str, Any]] = []
    for signal, text in page.hidden:
        if not _instruction_like(text):
            continue
        snippet = text[: CONTEXT_CHARS * 2]
        item = _finding(KIND_HIDDEN_HTML, 0, len(text), f"{signal}: {snippet}")
        item["signal"] = signal
        findings.append(item)
    for where, text in page.attributes:
        if not _instruction_like(text):
            continue
        item = _finding(KIND_ATTRIBUTE, 0, len(text), f"{where}: {text[:160]}")
        item["signal"] = where
        findings.append(item)
    for body in page.comments:
        if len(body.split()) >= COMMENT_MIN_WORDS and (
            _COMMENT_CUE_RE.search(body) or OVERRIDE_RE.search(body)
        ):
            snippet = re.sub(r"\s+", " ", body).strip()[:160]
            findings.append(_finding(KIND_HTML_COMMENT, 0, len(body), snippet))
    visible = "\n".join(page.visible)
    for item in screen_text(visible, payloads=True):
        if item["kind"] != KIND_HTML_COMMENT:
            findings.append(item)
    findings = finalize(findings)
    return {
        "status": status_of(findings),
        "findings": findings,
        "visible_words": len(visible.split()),
        "hidden_words": sum(len(t.split()) for _, t in page.hidden),
    }
