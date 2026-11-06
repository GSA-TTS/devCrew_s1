---
created: "2026-11-04T19:34:28Z"
updated: "2026-11-04T19:40:49Z"
---

# Conversion commands and the verification checks V1 to V11

## Converters

Use IBM Docling for PDF and HTML, and the deterministic `txt-normalize-v1` steps for plain-text IETF documents. Do not bring in Marker, MinerU or GROBID unless a verification failure is traced to Docling itself: mixed converters give inconsistent heading and reference formatting across one corpus.

PDF to Markdown (papers, NIST, OWASP, CoSAI):

```
docling <name>.pdf --to md --to json --image-export-mode placeholder --output <markdown-folder>
```

- The JSON output is required, not optional: it carries the per-item page provenance (`texts[].prov[].page_no`, `bbox`), the page map (`pages[n].size`) and the reference text (`texts[].text` in file order) that the checks use.
- `--image-export-mode placeholder` keeps the Markdown small (no embedded images); figures are not extraction targets.
- Add `--enrich-formula` for math-heavy papers; without it Docling drops formulas rather than inventing them.
- Keep the default OCR (it only triggers on image-only pages). Use `--force-ocr` only when a check finds a missing text layer.
- The `--force-ocr` run, written to a separate cache folder, is the rendered-view reference: what a human reader sees.
- Save the converter's output as the convert log.

HTML to Markdown (genuine HTML reports and arXiv HTML renderings only; never the htmlized datatracker page, which is a single preformatted block):

```
docling <name>.html --from html --to md --to json --output <markdown-folder>
```

Plain-text Internet-Drafts and RFCs (`txt-normalize-v1`; Docling has no `.txt` input). Apply the same steps to every document:

1. Remove form feeds and the page-break header and footer pairs: a line matching `^.*\[Page \d+\]\s*$` and the following line matching `^(Internet-Draft|RFC \d+)\s+.+\s+\w+ \d{4}\s*$`.
2. Re-join paragraphs split by a page break: a line ending without terminal punctuation followed by a non-indented line.
3. Promote numbered section titles (`^\d+(\.\d+)*\.?\s+\S`) to `#` levels by depth; promote Abstract, Status of This Memo, Table of Contents, Security Considerations, IANA Considerations, References and Authors' Addresses to `##`.
4. Wrap indented ASCII-art, code and JSON blocks in triple-backtick fences; leave prose unwrapped.
5. Prepend a metadata block: draft name (or RFC number), revision and expiry (drafts only; `n/a` for an RFC), date, state, source URL or URLs, SHA-256 of the `.txt`, and for a draft the sentence: Work in progress, cite as draft-...-NN (Month YYYY).

## Checks

Write the results to the verify log and the compact string to `conversion_checks`. A hard failure makes the row `verify-failed`; re-convert it (with `--enrich-formula`, `--force-ocr`, or the arXiv HTML rendering as alternate input) before it may proceed; try each applicable alternative once, count one that does not exist for the source (no arXiv HTML rendering of that version) as tried, and if a hard failure remains the row is `R8-conversion-failed`. A soft failure makes `conversion_status=ok-with-warnings`, visible in the row.

| # | Check | How | Hard fail if |
|---|---|---|---|
| V1 | Page count | entries in the Docling JSON `pages` map against the distinct `prov[].page_no` values across `texts[]`; write the map count to `pages` | a page in the map has no text provenance (missing text layer: re-run with `--force-ocr`); `pages` disagrees with the map |
| V2 | Text-volume ratio | words in the Markdown divided by words in the JSON `texts[].text` concatenated (serializer loss); if outside the band, run `--force-ocr` and divide Markdown words by OCR Markdown words (rendered view); for TXT, Markdown words divided by `.txt` words after header and footer removal | serializer ratio below 0.95 or above 1.05; OCR ratio below 0.85 or above 1.15 for papers; below 0.95 or above 1.05 for TXT |
| V3 | Section skeleton | expected headings present as `#` or `##` (Abstract, Introduction, ..., Conclusion or Discussion, References; for drafts the Table of Contents entries); heading count within 1 of the table of contents or reference-text count | Abstract, Introduction or References missing, or more than 2 headings missing |
| V4 | Reference list | count of numbered entries under References in the Markdown against the same count in the reference text; first and last entry present verbatim | counts differ by more than 1, or the last entry is truncated |
| V5 | Reading order | take 3 paragraphs of the reference text (JSON `texts[]` in provenance order, or the `--force-ocr` Markdown) at about 25, 50 and 75 percent of the file; each must appear contiguously in the Markdown (at least 90 percent of its words in order) | any of the 3 fails (typical two-column merge defect) |
| V6 | Tables | Markdown tables against "Table N" captions in the reference text | soft when tables are missing; hard only if the contribution is tabular (for example a comparison matrix the reader needs) |
| V7 | Formulas | count of `$...$` or LaTeX spans against equation numbers `(n)` in the reference text | soft unless the source is math-central |
| V8 | Garble | share of U+FFFD characters, isolated single-character lines, mojibake bigrams, and words with no vowels above 5 percent | more than 1 percent of tokens affected: re-run with `--force-ocr` |
| V9 | Running headers and footers | identical lines repeated 3 or more times (an arXiv stamp appearing once is normal) | soft: note it so the reader can ignore them |
| V10 | HTML-specific | Markdown heading count against `<h1>` to `<h3>` count; no `<script>` or `<style>` text present; visible-text word ratio 0.9 to 1.1 | ratio outside the range |
| V11 | TXT-specific | for a draft, the two-host SHA-256 values match (`n/a` for an RFC, which has one host); table of contents entry count equals promoted heading count | mismatch |

A row becomes `verified` only after V1 to V11 pass (the checks that do not apply to its format are recorded as `n/a`).
