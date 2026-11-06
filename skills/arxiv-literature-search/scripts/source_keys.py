"""Source keys: `primary_id`, canonical URLs, and lineage groups.

`primary_id` is the key for every set, join, and dedup of sources: `doi:<lowercased
DOI>` for papers, `github:<owner>/<repo>` for repositories, else
`url:<canonical URL>`. A canonical URL keeps its locale segment (such as `en`,
`en-us` or `ja`); the key drops it, so locale copies merge. Versioned pages
(a `v1` or `1.0` segment) stay distinct documents. `lineage_groups` joins records that
reproduce one release (a locale copy, a print copy, a mirror) under the smallest
member key.

Usage (every result is one JSON object on standard output):

  source_keys.py canon URL
  source_keys.py key [--doi DOI] [--github REPO] [--url URL]
  source_keys.py lineage [--edge A,B ...] [--single ID ...]

`canon` prints `{"canonical_url": ...}`, `key` prints `{"primary_id": ...}`,
`lineage` prints `{"lineages": {id: lineage_id}}`. Reads nothing and writes
nothing; no network. Same input, same output.

Exit codes: 0 done; 1 no usable identifier or a bad edge; 2 usage error
(a diagnostic goes to standard error).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit

# Letters that NFKD does not decompose into base letter plus accent.
_TRANSLIT = str.maketrans(
    {
        "ø": "o",
        "Ø": "O",
        "æ": "ae",
        "Æ": "AE",
        "ß": "ss",
        "đ": "d",
        "Đ": "D",
        "ł": "l",
        "Ł": "L",
        "ı": "i",
        "œ": "oe",
        "Œ": "OE",
    }
)

_DOI_PREFIX_RE = re.compile(
    r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*|urn:doi:)", re.IGNORECASE
)
_TRACKING_RE = re.compile(
    r"^(?:utm_|mc_)|^(?:fbclid|gclid|msclkid|igshid|ref)$", re.IGNORECASE
)
# `mailto:a@b.c` has a scheme; `example.com:8443/p` has a port, not a scheme.
_OTHER_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:(?!\d)")
_GITHUB_RE = re.compile(
    r"^(?:https?://(?:www\.)?github\.com/)?"
    r"(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/"
    r"(?P<repo>[A-Za-z0-9._-]+?)(?:\.git)?(?:[/?#].*)?$"
)

# Two-letter language codes a documentation site puts in a path. The set is
# closed on purpose: a path segment such as `ai` or `us` is not a locale.
_LOCALE_LANGS = frozenset(
    "ar cs da de el en es fi fr he hi hu id it ja ko ms nb nl no pl pt ro ru "
    "sv th tr uk vi zh".split()
)
_LOCALE_SEGMENT_RE = re.compile(
    r"^(?P<lang>[a-z]{2})(?:[-_](?:[a-z]{2}|hans|hant))?$", re.IGNORECASE
)


def strip_accents(text: str) -> str:
    """Return text with diacritics removed (NFKD plus a small table)."""
    text = text.translate(_TRANSLIT)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_doi(doi: Optional[str]) -> str:
    """Return the lowercased DOI with any URL or `doi:` prefix removed."""
    if not doi:
        return ""
    text = str(doi).strip()
    text = _DOI_PREFIX_RE.sub("", text)
    text = text.strip().rstrip(".,;)")
    return text.lower()


def canonical_url(url: Optional[str]) -> str:
    """Return the canonical form of a URL.

    `https`, lowercased host, no fragment or credentials, tracking parameters
    removed, the trailing slash normalized, remaining query parameters sorted.
    The locale segment stays. A non-HTTP(S) URL is returned stripped and
    unchanged; an empty input returns an empty string.
    """
    text = (url or "").strip()
    if not text:
        return ""
    if text.startswith("//"):
        text = "https:" + text
    elif "://" not in text and not _OTHER_SCHEME_RE.match(text):
        text = "https://" + text
    parts = urlsplit(text)
    if parts.scheme.lower() not in ("http", "https"):
        return text
    host = (parts.hostname or "").lower()
    if not host:
        return ""
    try:
        port = parts.port
    except ValueError:
        port = None
    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    query = sorted(
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if not _TRACKING_RE.match(key)
    )
    netloc = host if port in (None, 80, 443) else f"{host}:{port}"
    out = f"https://{netloc}{path}"
    return out + ("?" + urlencode(query) if query else "")


def _is_locale_segment(segment: str) -> bool:
    """Return True for `en`, `en-us`, `pt_br`, `zh-hans`, and the like."""
    match = _LOCALE_SEGMENT_RE.match(segment)
    if match is None:
        return False
    return match.group("lang").lower() in _LOCALE_LANGS


def drop_locale(path: str) -> str:
    """Return a URL path without its locale segment.

    A locale segment is the first path segment (`en` in a path that starts
    with `en`) or the one after `hc` (`en-us` after a leading `hc`). Only
    segments whose language is in the closed set count, so a leading `ai`
    segment is untouched. The result keeps a leading
    slash and has no trailing one, except for the root.
    """
    segments = [seg for seg in path.split("/") if seg]
    if segments and _is_locale_segment(segments[0]):
        segments = segments[1:]
    elif len(segments) > 1 and segments[0] == "hc" and _is_locale_segment(segments[1]):
        segments = [segments[0]] + segments[2:]
    return "/" + "/".join(segments)


def url_key(url: Optional[str]) -> str:
    """Return the canonical URL with its locale segment removed.

    Locale and print copies of one document share this key. Returns an empty
    string for an empty or unusable URL.
    """
    canon = canonical_url(url)
    if not canon.startswith("https://"):
        return canon
    parts = urlsplit(canon)
    out = f"https://{parts.netloc}{drop_locale(parts.path)}"
    return out + (f"?{parts.query}" if parts.query else "")


def github_id(repo: Optional[str]) -> str:
    """Return `github:<owner>/<repo>` (lowercased) from a URL or `owner/repo`.

    Returns an empty string when the value does not name a repository.
    """
    match = _GITHUB_RE.match((repo or "").strip())
    if not match:
        return ""
    return f"github:{match.group('owner')}/{match.group('repo')}".lower()


def primary_id(
    doi: Optional[str] = None,
    github: Optional[str] = None,
    url: Optional[str] = None,
) -> str:
    """Build the `primary_id` key.

    Order: `doi:<lowercased DOI>`, then `github:<owner>/<repo>`, then
    `url:<canonical URL without its locale segment>`. Raises ValueError when
    no usable identifier is given.
    """
    doi_norm = normalize_doi(doi)
    if doi_norm:
        return f"doi:{doi_norm}"
    repo = github_id(github)
    if repo:
        return repo
    key = url_key(url)
    if key:
        return f"url:{key}"
    raise ValueError("primary_id needs a DOI, a repository, or a URL")


def lineage_id(members: Iterable[str]) -> str:
    """Return the lineage ID shared by records that reproduce one release.

    The lineage is named by its smallest member ID, so it is stable under
    reordering and needs no new code format.
    """
    items = sorted(m for m in members if m)
    if not items:
        raise ValueError("a lineage needs at least one member")
    return items[0]


def lineage_groups(
    edges: Iterable[Tuple[str, str]], singles: Iterable[str] = ()
) -> Dict[str, str]:
    """Map every ID in `edges` and `singles` to its lineage ID.

    Each edge says two records reproduce one release (a locale copy, a print
    copy, a vendor mirror of a standard); groups join transitively.
    """
    parent: Dict[str, str] = {}

    def find(item: str) -> str:
        parent.setdefault(item, item)
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for left, right in edges:
        root_l, root_r = find(left), find(right)
        if root_l != root_r:
            parent[root_r] = root_l
    for item in singles:
        find(item)
    groups: Dict[str, List[str]] = {}
    for item in list(parent):
        groups.setdefault(find(item), []).append(item)
    out: Dict[str, str] = {}
    for members in groups.values():
        lineage = lineage_id(members)
        for member in members:
            out[member] = lineage
    return out


def _parse_edge(text: str) -> Tuple[str, str]:
    """Split `A,B` into two non-empty IDs; ValueError otherwise."""
    parts = [part.strip() for part in text.split(",")]
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"an edge is two IDs joined by a comma: {text!r}")
    return parts[0], parts[1]


def _build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="source_keys.py", description="Source keys; JSON on standard output"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    canon = sub.add_parser("canon", help="canonicalize a URL")
    canon.add_argument("value", help="the URL")
    key = sub.add_parser("key", help="print the primary_id of a source")
    key.add_argument("value", nargs="?", default=None, help="a URL (as --url)")
    key.add_argument("--doi", default=None, help="a DOI, bare or as a link")
    key.add_argument("--github", default=None, help="owner/repo or a repository URL")
    key.add_argument("--url", default=None, help="a URL")
    lineage = sub.add_parser("lineage", help="group records that share a release")
    lineage.add_argument("--edge", action="append", default=[], help="A,B")
    lineage.add_argument("--single", action="append", default=[], help="an ID")
    return parser


def _emit(payload: Dict[str, object]) -> None:
    """Print one JSON object, the same for the same input."""
    print(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the CLI; return the exit code (0 done, 1 refused, 2 usage)."""
    args = _build_parser().parse_args(argv)
    try:
        if args.cmd == "canon":
            _emit({"canonical_url": canonical_url(args.value)})
        elif args.cmd == "key":
            url = args.url if args.url is not None else args.value
            _emit({"primary_id": primary_id(args.doi, args.github, url)})
        else:
            edges = [_parse_edge(text) for text in args.edge]
            singles = [text.strip() for text in args.single if text.strip()]
            _emit({"lineages": lineage_groups(edges, singles)})
    except ValueError as exc:
        print(f"source_keys.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
