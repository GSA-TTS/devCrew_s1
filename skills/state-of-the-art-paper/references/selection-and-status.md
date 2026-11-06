---
created: "2026-11-05T00:33:53Z"
updated: "2026-11-05T00:33:53Z"
---

# Item selection, tiers and status labels

## Scoring rubric (0 to 2 per criterion, total out of 12)

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| Load-bearing | Not needed for any research question | Supports a question | Answers a question, or is the only support for a sentence that must exist |
| Authority (tier) | T4 | T3 | T1 or T2 |
| Currency and status | Superseded, or undated with no corroboration | Dated within the window but draft or preprint | Dated within the window and final, or the most recent version of a living specification |
| Distinctness | Restates an item already selected | Adds a nuance | Only item establishing this fact |
| Evidence strength | Opinion or unattributed number | Attributed number, or normative SHOULD | Measurement with its population stated, or normative MUST in a final specification |
| Representation | Not related to a contested point | One side of a contested point already covered | Required to give a contested point its second side |

## Decision rule

- Select an item if it scores 8 or more, or if it is any side of a contested point the outline has chosen to report; every side of a reported contested point is then selected regardless of score.
- Every body subsection needs at least one T1 or T2 anchor.
- Keep no more than about 12 items per body subsection in the evidence map.
- Log every rejected item with a one-line reason.
- Numbers: at most one number per phenomenon per paragraph, unless the paper's point is that the numbers disagree; then cite all of them and say that they disagree.

## Tiers (how much weight a source can carry)

| Tier | Source types | May support |
|---|---|---|
| T1 | Published RFCs; final NIST SP or IR; OMB memoranda and regulations; peer-reviewed venue papers; released versions of an official protocol specification; CVE records | Any claim, including normative statements and numbers |
| T2 | Working-group-adopted Internet-Drafts; NIST or NCCoE drafts and concept papers; consortium consensus documents; official vendor product documentation; incident reports by the affected party or a named security firm; empirical industry reports with stated methodology | Descriptive and proposes or recommends claims; numbers with their population stated |
| T3 | Individual-submission Internet-Drafts; arXiv preprints with no venue; AI-assisted rapid research or draft white papers; bylined vendor or practitioner analyses; survey press releases whose methodology is n.a. | Claims attributed in the text (X argues; a vendor analysis holds); numbers only with the caveat self-reported or methodology not published |
| T4 | Unbylined or undated blog posts; press releases restating others; secondary summaries of paywalled sources; glossary pages with no date | Commentary only, attributed; never the sole support for a normative or numeric claim |

## Status (what the text must call the source)

The label appears in the sentence or its citation parenthetical the first time the source is used, and the marker appears in its reference entry.

| Status | Wording in text | Reference-list marker |
|---|---|---|
| Final standard or RFC | requires, specifies, MUST (quote the RFC 2119 keyword if used) | none |
| Working-group-adopted Internet-Draft | the draft proposes; name the draft string and version | Internet-Draft, work in progress, draft name and version, date |
| Individual-submission Internet-Draft | an individual submission proposes ... (not adopted by any working group) | as above, plus individual submission |
| Draft or open-for-comment document | (draft) or (open for comment) | Draft |
| Preprint | (preprint) | arXiv identifier and category, preprint |
| Non-standards-track consensus | consensus work product, not a standard, once; then by name | Non-Standards Track |
| Vendor documentation | the vendor as actor: Vendor documents that its product ... | vendor as corporate author |
| Undated page | give the accessed date; never invent a year | n.d., Online, Available, Accessed: date |
| Paywalled (for example ISO) | as summarized by the secondary source | cite the secondary; note that the primary text was not consulted |

Hedge by status, not by mood: final standard, requires; adopted draft, proposes; preprint, reports (preprint); survey press release, self-reports; vendor page, documents. Do not upgrade a SHOULD to a MUST or a proposes to a requires.

## Disagreements and numbers

- For normative disagreements between serious bodies, recency settles nothing: report both positions; do not pick the newer one as correct.
- For numbers from different populations or definitions, never average them and never present them as a single trend.
