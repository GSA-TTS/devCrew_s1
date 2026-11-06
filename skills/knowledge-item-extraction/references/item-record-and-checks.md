---
created: "2026-11-04T20:36:39Z"
updated: "2026-11-04T20:39:41Z"
---

# Item record and citation checks

Field definitions for the Source register, the knowledge item block, the Item index and the Check results, the three citation checks, and the status rule.

## Source register columns

| Column | Content |
|---|---|
| Source ID | Short local id (S-01, S-02, ...) used inside item blocks. |
| Title | As printed on the source. |
| Authors | Authors of the intellectual content, as printed. |
| Stated date | Publication or version date as printed on the source; write n.a. if absent, never guess. |
| Identifier | The strongest external identifier in this order: DOI, arXiv id, RFC or Internet-Draft name with revision, stable URL. For an unpublished document, its content hash written sha256-hex, or its file name marked no-hash when no hash can be computed. |
| Retrieved from | Where the copy came from (user upload, a URL). |
| Retrieved on | Date the source was read. |
| Status qualifier | Copied from the source itself, for example RFC, Internet-Draft (individual), draft white paper, concept paper open for comment, trade press, vendor blog, internal report; not stated when the source gives none. |

## Knowledge item fields

| Field | Content |
|---|---|
| Identifier | Namespace prefix plus local id, unique in the set. |
| Title | Short concept-oriented phrase that works as a reusable handle, naming the idea, not the chapter or document. |
| Type | One term of the vocabulary named in Scope. Default vocabulary: Concept, Definition, Mechanism, Empirical Finding, Principle, Pattern, Example, Misconception, Guideline, Question, Policy Constraint. |
| Body | 2 to 6 sentences in the extractor's own words: the concept or claim with the minimal context, assumptions and implications needed to reuse it without reopening the source, framed so it can drive a decision or design. It asserts one headline proposition. |
| Relations | Typed links, each a relation type and a target item id: depends-on, refines, contradicts, example-of, implemented-by, is-a, part-of. none when no link is found. |
| Sources | One entry per supporting or challenging source (format below). |
| Tags | Domain tags, cognitive level (definition or application), and project context. |
| Source maturity | The weakest (least mature) status qualifier among the item's sources. |
| Status | One value of the status rule below. |
| Version | Counter, 1 at extraction. |
| Derived from, Extracted by, Extracted on, Verified by, Round | Provenance fields; Extracted by names the assistant and the procedure step that produced the item. |

### Sources entry

Each entry has five parts: Source ID, locator, quote, support, confidence.

- Locator: a position a reader can check. For a PDF, page number(s) and section heading. For converted Markdown without page markers, heading path plus paragraph ordinal, with page n.a. (no page markers); do not infer a page from the document's length. For a web page, its anchor or heading.
- Quote: a verbatim excerpt (typically 40 words or fewer) that a substring search can find in the source text. Ellipses are allowed only between complete clauses. A paraphrase is never presented as a quote. If the exact wording is unavailable (image-only page, blocked or paywalled text), write n.a. with the reason.
- Support: supports, partially-supports, contradicts or context-only; not judged when the quote is n.a.
- Confidence: high, medium or low, the extractor's own estimate. It never replaces the checks below.

## Item index columns

Identifier, Title, Type, Tags, Status, Source IDs: one row per item, so the set can be loaded as table rows.

## Check results columns

One row per Sources entry: Item, Source ID, Existence, Quote fidelity, Support, Status.

| Check | Catches | How | Values |
|---|---|---|---|
| Existence | Fabricated sources, corrupted metadata | Resolve the DOI or arXiv id at the publisher or arXiv; for a bare URL, open it and confirm it loads and its title matches. Record the resolution date and the page it resolved to. | Exact (the record matches), Minor (small metadata differences, named in the row), Major (the record names a different work), not found, supplied (a user-supplied file with no external identifier) |
| Quote fidelity | Misquotes, paraphrases given as quotes, quotes from the wrong document | Search the quote as a substring of that source's text after normalizing whitespace, ligatures and dashes. | found; locator corrected (found at another position: fix the locator and write the old one in the row); not found; n.a. (with the reason) |
| Support | Real source and real quote, wrong inference | Judge from the quote, its immediate context and the claim only. | supports, partially-supports, contradicts, context-only, not judged (quote n.a.) |

## Status rule

- unverified: the starting status, kept while any check has not run or no entry meets the machine-verified condition.
- quote-unverified: no Sources entry of the item has a quote that was found (each is n.a. or not found).
- machine-verified: at least one Sources entry has Existence Exact, Minor or supplied, Quote fidelity found or locator corrected, and Support supports.
- expert-verified: set only by a human reviewer, never by the assistant.
- deprecated: not assigned at extraction.

## Example item block

```text
Identifier: KI:WARD.handover-checklist-missed-doses
Title: Handover checklists reduce missed medication doses
Type: Empirical Finding
Body: On the two audited wards, missed medication doses fell after a structured
  handover checklist was introduced [during the 2023 ward audit]. The audit
  covered one quarter, so the effect over longer periods is untested. Wards
  with similar handover patterns could pilot the same checklist.
Relations: refines KI:WARD.structured-handover
Sources: S-01 | p. 4, Results > Medication safety | Missed doses fell on both
  wards in the quarter after the checklist was adopted. | supports | high
Tags: patient safety; application; ward quality project
Source maturity: internal report
Status: machine-verified
Version: 1
Derived from: none
Extracted by: assistant, step 5
Extracted on: 2026-11-04
Verified by: quote check, 2026-11-04
Round: 1
```
