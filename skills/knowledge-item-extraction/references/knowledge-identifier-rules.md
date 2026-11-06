---
id: FR-IDENTIFIERS
purpose: 'Stable identifier rules for knowledge entries: minting once, frozen ids,
  naming and tombstones for merged or retired entries'
slug: knowledge-identifier-rules
created: '2026-11-04T14:38:43Z'
updated: '2026-11-04T18:55:41Z'
---

# Knowledge identifier rules

Use these rules whenever you create, merge, retire or cite entries in a knowledge base, whether it is a published graph or a set of Markdown and CSV files under version control. The identifier is the key everything else hangs on; once anyone cites it, changing it breaks every reference silently.

## What every identifier must do

An identifier is fit for use only when it has all four properties:

1. Globally unique: no two entries share it, across all systems and across time.
2. Persistent: it stays valid indefinitely, independent of where the entry is stored or how its wording changes.
3. Interoperable: it works with a standard resolution mechanism (HTTP, DOI resolution, or a plain-text search in a file-based store).
4. Resolvable: a person or program can go from the identifier to the entry and its metadata. In a file-based store this means one search for the identifier at the start of an entry header finds exactly one entry.

Local keys such as database row numbers or a bare running count work inside one store but collide when two stores are merged, forcing costly reconciliation. Give every entry, every schema element (classes, properties) and every controlled-vocabulary term a stable identifier, and qualify it with a namespace whenever it leaves its home store.

## Identifier shape

Build each identifier as two parts:

```
identifier = <namespace pattern> + <local id>
```

The namespace pattern (a base address or a prefix) says which store owns the entry; the local id picks the entry within it. The split lets a resolver route by pattern and lets you write compact forms `<prefix>:<local id>`.

Choose one of two layouts and record the choice:

| Layout | Pattern | Use when | Condition |
|---|---|---|---|
| Type-specific | one pattern per entry kind: the base address followed by a kind segment such as `source`, `item` or `concept` | you want the entry kind visible in the id for debugging and inspection (the default) | one prefix per kind when integrating |
| Type-agnostic | one pattern for all kinds: the base address followed by a single segment such as `id` | integration simplicity matters more, or the kind is clear from context | local ids must be unique across all kinds |

## Choosing the local id by entry kind

Reuse before you mint. Pick the first option that applies:

1. Sources (papers, reports, standards). Key each source on the strongest external persistent identifier available, in this order: DOI, then arXiv id, then RFC or Internet-Draft name with its revision number (for example `draft-name-08`), then a stable URL plus the retrieval date. You may also assign a short local source id (`S-0042`) for use inside entry bodies, but keep the external identifier in the source record: it is what makes the citation checkable.
2. Unpublished or internal documents. Use a content hash (SHA-256 of the file) as the local id, written as `sha256-<hex>`, and store the checksum with the record. If the content changes, the hash changes, so a silent edit cannot hide behind an old id.
3. Terms from a canonical vocabulary or catalog (control codes, technique ids, standard concept codes). If the owner publishes official identifiers, reuse them directly, so that any other system using the same ids aligns automatically. If no official identifier exists, mint one in your own namespace from the canonical code and add a "see also" link to the authoritative definition.
4. Derived entries (claims, findings, knowledge items extracted from sources). Use your own namespace plus a generated id:
   - a random UUID (version 4) when you need uniqueness and no coordination, and reproducibility does not matter;
   - a name-based UUID (version 5) when the same input must always give the same id, for example a namespace UUID plus the source identifier and a section or claim reference. Re-extracting the same claim from the same source then yields the same id, so ingestion is idempotent and creates no duplicates. Feed it a stable string (the source id plus a cryptographic digest of the normalized claim text), never a per-process hash that changes between runs.
   - in a file-based store seeded with an existing numbering, the next free number in the scheme instead (see the minting rules).

Store the local id as an explicit field on the entry as well as in its address, so it survives export to formats that drop the address.

## Minting rules

Rule 1. Inherited ids are frozen. If the seed inventory already numbers its entries (for example `A-01` to `L-38` across domains), those ids are the canonical local ids from day one. Never renumber, re-sort or tidy them, and never change an id because the entry's wording changed. Downstream documents (drafts, registries, cross-references) cite entries by bare id.

Rule 2. One step mints; everything else is provisional.
- New entries take the next free number in their domain (`A-33`, `G-63`).
- Only the consolidation (deduplication) step may mint canonical ids. Extraction steps emit provisional ids of the form `TMP-<source_slug>-<n>`, numbered deterministically, so that re-running an extraction on the same source yields the same provisional ids.
- This stops two parallel extraction runs from both allocating the same next number.
- When entries are exchanged with another store, prefix the local id with a namespace on export (`<NS>:A-07`); inside the home store the bare id stays the primary key.

Rule 3. Ids are never reused or deleted. A merged or retired entry becomes a tombstone, following the obsoletion pattern of the OBO Foundry: keep the obsolete identifier, mark it deprecated, point to the replacement ("term replaced by", IAO:0100001) and record the reason for obsolescence (IAO:0000231). Concretely:
- Keep the entry's inventory row with `status=merged` (or `deprecated`), `merged_into=<survivor>` (or `superseded_by=<replacement>`) and a `reason`.
- Replace the entry body with one line, for example: `**G-41. (merged into G-17 on <date>: same proposition, same scope; see the merge log)**`.
- Rewrite every cross-reference elsewhere to point at the survivor, so the tombstone is reachable only from the merge log and from the survivor's `Merged from:` line.
- A tombstone never points at another tombstone. When a survivor is itself merged later, repoint all earlier tombstones to the new survivor, so there are no redirect chains.

Rule 4. Titles are handles, ids are keys. Titles may be edited for clarity at any time; matching, cross-referencing and change tracking key on the id alone. Keep a `title` column in the inventory so that a first deduplication pass over headers can run without opening entry bodies.

Rule 5. Auxiliary registries get ids too. Contested points (`CP-01`, ...) and evidence gaps (`GAP-01`, ...) live in their own registry file with their own sequences, so an entry can say `Contested: CP-03` and a written paragraph can cite the registry directly. These ids follow Rules 1 to 3 as well.

## Resolution when ids are served over HTTP

If the store is published, every identifier should resolve ("follow your nose"): requesting it returns information about the entry, which links to related entries, so the graph can be explored without prior knowledge of the whole schema.

- A schema identifier (class or property) returns its informal definition (label, comment, usage examples) and its formal definition (axioms, domain and range, cardinality).
- A data identifier returns the known facts with that identifier as subject, subject to access-control policy.
- Serve one identifier to all audiences by content negotiation on the `Accept` header: `text/turtle` or `application/rdf+xml` gets RDF, `application/ld+json` gets JSON-LD, anything else gets HTML documentation.
- Answer the abstract identifier with HTTP 303 See Other, redirecting to the representation (`<id>.ttl`, `<id>.jsonld`, `<id>.html`), so the resource and its documents stay distinct and no second identifier is needed.

## Checklist

- [ ] Every entry, schema element and vocabulary term has an id with the four properties.
- [ ] The namespace layout (type-specific or type-agnostic) is recorded; under type-agnostic, local ids are unique across kinds.
- [ ] External persistent ids were reused before anything was minted; sources follow the DOI, arXiv, draft-with-revision, URL-plus-date order.
- [ ] Inherited ids are unchanged; no id changed with a wording change.
- [ ] Only the consolidation step minted canonical ids; extraction output carries deterministic provisional ids.
- [ ] No id was reused or deleted; each merged or retired entry is a tombstone with status, target and reason, and no tombstone points at a tombstone.
- [ ] Cross-references point at survivors, and they key on ids, not titles.
- [ ] One search per id finds exactly one entry.
