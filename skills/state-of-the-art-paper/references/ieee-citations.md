---
created: "2026-11-05T00:33:53Z"
updated: "2026-11-05T00:48:47Z"
---

# IEEE numeric citations in Markdown

## In the text

- Final form: [n]; several: [3], [7] or [3]-[5]. Numbers follow first appearance in the body; the abstract is excluded.
- While drafting, write the evidence map's Ref key in brackets instead, one key per cited document. Final assembly replaces the keys with numbers in first-appearance order and emits the list. Assembly is the only step that touches numbering, so a section edit never renumbers by hand.

## Reference list entries

One entry per line, numbered; the key is dropped at assembly. Patterns by source type:

```
[1] Organization, "Title," series and number, Mon. Year. [Online]. Available: URL
[2] A. Author et al., "Title," Internet-Draft draft-name-version, IETF, work in progress, Mon. Year. [Online]. Available: URL
[3] A. Author and B. Author, "Title," Year, arXiv:NNNN.NNNNN [cs.XX], preprint.
[4] Consortium name, "Title," Non-Standards Track Work Product, Mon. Day, Year. [Online]. Available: URL
[5] Vendor Inc., "Documentation page title," n.d. [Online]. Available: URL. Accessed: Mon. Day, Year.
```

An individual-submission Internet-Draft takes the pattern of entry 2 plus the words individual submission. A paywalled primary cited through a secondary source takes the secondary's entry plus a note that the primary text was not consulted.

## Optional PDF path

Only when the user asks for a PDF: keep the keys as pandoc citations (@ and the ref key, in brackets), keep a BibTeX file (techreport entries for RFCs and Internet-Drafts with the note Work in Progress, misc entries for web pages with urldate), use the IEEE style file of the Citation Style Language project, and run pandoc with --citeproc, --csl pointing at that style file, and --bibliography. Put a refs div where the list should go. Without --csl, pandoc defaults to Chicago author-date, so --csl is required for IEEE numbering.
