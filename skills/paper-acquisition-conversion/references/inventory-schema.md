---
created: "2026-11-04T19:34:28Z"
updated: "2026-11-04T19:40:49Z"
---

# Inventory schema, lifecycle, rejection codes and corpus layout

## Corpus layout

Keep five areas apart in the delivered corpus:

- sources: the byte-exact originals, split into a pdf, an html and a txt folder.
- papers: the verified, screened Markdown files; the only folder a downstream reader may read.
- quarantine: originals of sources flagged by the injection screen, with the excision log.
- logs: per candidate, a download log, a convert log, a verify log and a screen log, each named with the `cand_id`.
- the inventory CSV, one row per candidate, selected or not.

## File naming

- Papers: `<firstauthor-surname>_<year>_<slug>` with the `.pdf` or `.md` extension.
- Standards: `<ORG>.<doc-id>[.<rev>]` with the original extension, for example `IETF.draft-ietf-oauth-v2-1-12.txt`, `NIST.SP.800-63-4.pdf`.
- The Markdown file keeps the source's basename.

## Columns

| Column | Meaning |
|---|---|
| `cand_id` | `C001`, `C002`, ...; stable key used in log file names |
| `source_type` | `arxiv`, `doi-journal`, `ietf-draft`, `ietf-rfc`, `nist`, `owasp`, `csa`, `cosai`, `openid`, `other-grey` |
| `primary_id` | arXiv ID with version (`2401.01234v2`), DOI, `draft-...-NN`, `RFC9999`, or NIST document id with its stage |
| `secondary_ids` | semicolon-separated: DOI, OpenAlex work id, Semantic Scholar CorpusId, base arXiv ID |
| `title`, `first_author`, `first_author_affiliation` | as printed on the document; for standards, the publisher or working group goes in `first_author` |
| `year`, `date_published` | ISO date of the exact version or revision downloaded |
| `venue_or_publisher` | named venue, `preprint (arXiv)`, or the publisher (IETF, NIST, OWASP, ...) |
| `doc_status` | `published`, `preprint`, `S-RFC`, `S-WGdraft`, `S-indivDraft`, `S-NISTfinal`, `S-NISTdraft`, `S-community`, `S-vendor` |
| `pages` | number of entries in the Docling JSON `pages` map, set at conversion and blank until then; for TXT and HTML the page count only if the document prints one, else `n/a` |
| `search_hit_source` | where the candidate came from: `arxiv-api`, `openalex`, `s2`, `datatracker`, `csrc`, `manual` |
| `retrieval_url`, `retrieval_method`, `download_date`, `sha256` | provenance of the byte-exact file |
| `local_source_path`, `local_md_path` | relative to the corpus root |
| `conversion_tool` | `docling-<version>`, `html-docling-<version>`, or `txt-normalize-v1` |
| `conversion_status` | `ok`, `ok-with-warnings`, `failed` |
| `conversion_checks` | compact result string, for example `pages=18/18 words=0.97 heads=9/9 refs=42/42 order=3/3 formulas=warn` |
| `injection_screen_status` | `clean`, `flagged`, `not-screened` |
| `injection_screen_notes` | what was found, where, and by which check; empty only when `clean` |
| `status` | current lifecycle state (below) |
| `rejection_reason` | a code from the list below, else empty |
| `notes` | free text |

## Lifecycle of `status`

`candidate` then `downloaded` or `unavailable`; then `converted` or `conversion-failed`; then `verified` or `verify-failed`; then `screened-clean` or `flagged`; then `selected` or `rejected`.

A row is never deleted. A superseded version gets `R10-superseded` and the newer version gets a new row.

At close-out, a flagged row whose payload was excised keeps `status=flagged`, `injection_screen_status=flagged` and an empty `rejection_reason`: it is not selected, and the user decides on it. A flagged row whose payload cannot be isolated becomes `rejected` with `R9-injection-quarantined`.

## Rejection codes (`rejection_reason`)

| Code | When |
|---|---|
| `R6-duplicate` | the row duplicates another; the note points to the surviving `cand_id` |
| `R7-no-oa-copy` | no lawful open-access file exists |
| `R8-conversion-failed` | conversion still fails its hard checks after each applicable alternative (`--enrich-formula`, `--force-ocr`, the arXiv HTML rendering) has been tried once; an alternative that does not exist for the source counts as tried |
| `R9-injection-quarantined` | an injection payload cannot be cleanly excised |
| `R10-superseded` | a newer version, revision or final edition exists |
| `R11-access-gated` | login or form wall; record the URL |
| `R12-license-blocks-use` | the licence does not allow the intended use |

## Counts for the close-out

Recompute from the inventory alone, in the style of PRISMA 2020 record tracking: identified, deduplicated (duplicates removed), unavailable, converted, verified, flagged, selected, and rejected by reason code.
