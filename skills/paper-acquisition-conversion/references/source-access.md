---
created: "2026-11-04T19:34:28Z"
updated: "2026-11-04T19:40:49Z"
---

# Where to get each source type, and the limits to respect

All downloads: one connection, sequential, a user-agent naming the project and, where the user gave one, a contact email; retry a failed request at most 3 times, 5 seconds apart. Fetch only lawful open copies: publisher, repository or arXiv. Never use shadow libraries or paywalled copies, and never create accounts.

| Source | Metadata | File | Rate and terms |
|---|---|---|---|
| arXiv | the arXiv API on the export host export.arxiv.org, query by id list: title, authors, `published`, `updated`, `journal-ref`, `doi`, version | the PDF from export.arxiv.org with the version pinned (`<id>v<n>`); optional cross-check: the HTML rendering of the same version on arxiv.org | at most 1 request every 3 seconds, one connection, counted across all machines you control; use the export host; never bulk-crawl; link back to arXiv for the full text |
| DOI-only paper | Unpaywall API (api.unpaywall.org) record for the DOI (needs an email parameter), field `best_oa_location.url_for_pdf`; OpenAlex API (api.openalex.org) work record, `best_oa_location.pdf_url`; Semantic Scholar Graph API (api.semanticscholar.org) paper record by DOI with fields `openAccessPdf,externalIds`, field `openAccessPdf.url` | the resolved open-access PDF only (publisher, repository or arXiv) | Unpaywall up to 100,000 calls a day with an email; OpenAlex polite pool with a `mailto` parameter, up to 100 requests a second and 100,000 credits a day; Semantic Scholar unauthenticated pool is shared, so stay at 1 request a second or less and honour `Retry-After`; CORE needs an API key, so skip it unless one is configured |
| IETF Internet-Draft | the document JSON record on datatracker.ietf.org for the draft name: `rev`, expiry, and any `rfc` or `replaced_by` value | the `.txt` from two hosts: the IETF draft archive on ietf.org (all revisions are kept) and datatracker.ietf.org; the htmlized datatracker page and the XML exist but are not conversion inputs | no published limit; stay at 1 request a second or less; fetch the `.txt` from both hosts and compare SHA-256 |
| RFC | the document JSON record on datatracker.ietf.org for `rfc<n>` | the `.txt` from the RFC Editor site, rfc-editor.org (also offered as `.html` and `.pdf`); one host, so no two-host hash comparison | at 1 request a second or less, as for drafts |
| NIST | the publication page on the CSRC site (csrc.nist.gov), final or initial public draft stage | resolve the DOI `10.6028/NIST.<SERIES>.<id>` (with `.ipd` or `.2pd` for draft stages) through doi.org to the PDF on nvlpubs.nist.gov | public domain (US Government); record the DOI and the stage |
| OWASP GenAI | the resource page on genai.owasp.org | the Download PDF linked from the resource page | CC BY-SA 4.0; record the printed version string |
| CoSAI | the resource page on coalitionforsecureai.org | the direct PDF link | record the date shown in the file's URL path |
| CSA | the artifact page on cloudsecurityalliance.org | login-gated: do not download | set `status=unavailable`, `rejection_reason=R11-access-gated`, and note whether a mirror of the same version exists; treat a mirror as the same document only after matching title, version and page count |

## Deduplication before download

Build the dedup key in this order and merge rows that share any of them:

1. normalized DOI (lowercase, resolver prefix removed);
2. base arXiv ID (version suffix `vN` removed);
3. IETF draft base name (revision suffix `-NN` removed);
4. fallback: normalized title (lowercase alphanumerics, first 80 characters) plus first-author surname plus year.

Resolve arXiv and DOI pairs with one OpenAlex lookup, by DOI or by arXiv id; it returns `ids`, `open_access`, `best_oa_location` and `locations` in one call. Keep the version with the named venue (published over preprint).
