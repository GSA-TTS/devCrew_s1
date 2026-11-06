---
id: FR-PROVENANCE
purpose: Provenance metadata fields, item-to-source linking and a file-based provenance
  record with a completeness audit for knowledge items
slug: knowledge-provenance-records
created: '2026-11-04T14:38:43Z'
updated: '2026-11-04T18:55:46Z'
---

# Knowledge provenance records

Use this reference whenever you extract, record or revise a knowledge item (a claim, fact or finding) from source material. A claim is only as strong as its provenance: the sources, processes, agents, time and context that produced it. The W3C PROV recommendation (2013) defines provenance as information about the entities, activities and people involved in producing a piece of data, used to judge its quality, reliability or trustworthiness.

The record below uses the W3C PROV model in plain text: a source or item is an Entity, an extraction or curation step is an Activity, and the person or model that performed it is an Agent.

## 1. What to capture

### Per source (one row in the source register)

- Origin identifier: URL, DOI, file hash or dataset id.
- Acquisition: `retrieved_from` (where the copy was fetched) and `retrieved_on` (when), ingestion channel (download, upload, API) and original format.
- Authors of the intellectual content.
- Source quality: reliability or reputation, if known, and license or usage constraints.
- Maturity: flag drafts, non-standards-track documents, individual submissions and trade press, so the flag can travel with every claim that cites the source.

### Per knowledge item

- Supports: every source that supports the item, each with a locator (section, page, heading, or character span).
- Process: which extraction step or model produced the item, and its version.
- Agents: who or what created, verified or modified the item.
- Quality: confidence, a status flag (auto-extracted, human-verified, disputed, deprecated) and freshness (date of the last validation).

### Per workflow step

- The transformation (extraction, enrichment, merge, split), with what it used and what it generated.
- The round or batch it belongs to, so every item traces to the batch of sources that produced or changed it.

## 2. Linking items to sources

The link between items and sources is many-to-many: one source can support several items, and one item can rest on several sources. Large web-scale knowledge graphs average about three independent origins per fact, so expect more than one source per item.

- Record each link explicitly, one entry per supporting source. Never collapse several sources into a single unattributed claim.
- When a link needs its own detail (which span, what transformation, a local confidence for that link), attach it to the link entry, not to the item as a whole.
- Keep both directions answerable: from an item to all its sources, and from a source to every item that cites it (search the item records for the source id).
- No item exists without at least one source link, unless it is explicitly tagged `hypothetical` or `editorial`.
- Derive the item's overall confidence from the confidence of each link and the reliability of each supporting source; several independent, reliable sources justify higher confidence than one.
- Record support and challenge separately: a source that contradicts the item is listed as challenging evidence, not dropped.

## 3. The file-based provenance record

When items are kept as Markdown files with CSV indexes, and no graph database or shape validator is available, carry the same information in this fixed field set. Fill every field for every item. With less, nobody can drill down from a claim to its evidence.

| Field (item body / index column) | PROV relation | Content |
|---|---|---|
| `Sources:` | `wasDerivedFrom` (Entity from Entity) | One entry per supporting source: `source_id` from the source register, a locator, and a verbatim quote. Never present a paraphrase as a quote. |
| `Derived from:` | `wasDerivedFrom` | Upstream items this one was built from, such as seed-list ids or temporary candidate ids folded in. |
| `Extracted by:` / `extracted_by` | `wasAttributedTo` (Entity to Agent) and `wasGeneratedBy` (Entity to Activity) | `<agent or model>` and `<workflow step id>`: the step run is the Activity, the agent is the Agent. |
| `Extracted on:` / `extracted_on` | `generatedAtTime` | ISO 8601 date. |
| `Verified by:` / `verified_on` | `wasAttributedTo` (curation) | Empty until a verification pass confirms the quote against the local source text or a human reviews it. |
| `Supersedes:` / `Superseded by:` | `wasRevisionOf` / `wasInvalidatedBy` | Set when a later source retracts or replaces a claim. The old item is kept, marked `deprecated`, with a reason. |
| `Merged from:` | `alternateOf` plus derivation | Candidate or duplicate ids folded into this canonical item. |
| `round` | Activity grouping | Extraction round number. |

In PROV-DM (W3C, 2013), a revision is a resulting entity that is a revised version of an original, and an invalidation marks the start of an existing entity's destruction, cessation or expiry by an activity. The supersede fields stand in for these two relations.

### Keep three roles apart

Curated content has three distinct roles (Ciccarese et al., PAV ontology, 2013). Record each one in its own place:

1. Author: who wrote the intellectual content. Record this in the source register.
2. Creator: who produced this digital record. Record the extracting agent and step in `extracted_by`.
3. Curator: who selected or validated it. Record this in `verified_by`.

### Never edit a published claim silently

A published claim is immutable. Change it only by superseding or retracting it, so the original stays readable (the nanopublication discipline). When new evidence arrives, choose one of two paths:

- The claim still holds and gains evidence. Append the new source entry, bump the item's `last_changed` date and `round`, and record the change in the change log. Version history is the audit trail.
- The claim is wrong. Keep the item, set `status=deprecated`, fill `Superseded by:` with a one-line reason, and create the replacement item with `Supersedes:` pointing back. The deprecated item is the audit trail.

Do not overwrite an item's body in place.

## 4. Provenance completeness audit

Run this audit after every extraction or consolidation step. Report each failure with the item id and the rule it breaks. Fix each failure, or downgrade the item, before anything uses the items.

1. Every item has at least one `Sources:` entry whose `source_id` exists in the source register, and that source has a URL or a local file path.
2. Every quote in `Sources:` appears verbatim, after whitespace normalization, in the local text of that source when one exists. If no local text exists, the item's confidence may not exceed `medium`.
3. Every id in `Derived from:`, `Merged from:`, `Supersedes:` and `Superseded by:` resolves to an existing item.
4. `extracted_by`, `extracted_on` and `round` are non-empty for every item not carried over from a seed list.
5. Every source has its acquisition fields (`retrieved_from`, `retrieved_on`).
6. Every item citing a draft, non-standards-track, individual-submission or trade-press source carries that flag in `source_maturity`.
7. No workflow step or agent is orphaned: each `<workflow step id>` and agent named in `extracted_by` or `verified_by` is one that actually ran or exists.
8. Every item with no source link is tagged `hypothetical` or `editorial`. Any other such item fails rule 1.

Incomplete provenance leads to systematic errors and irreproducible results, so treat a failed audit as blocking, not cosmetic.

## 5. Using provenance downstream

- Any claim shown in an answer, report or view must let the reader trace it: claim, then item, then sources and locators, then the step and agent that produced it.
- Express risk tolerance as a filter over provenance, for example: use only items with confidence of at least X, backed by at least Y independent sources newer than Z months. Then state the filter you applied.
- Capture provenance as a side effect of each step, at the moment the step runs. Do not reconstruct it afterwards.
