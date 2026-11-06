---
created: "2026-11-04T20:35:59Z"
updated: "2026-11-04T20:35:59Z"
---

# Source credibility, freshness and corroboration

Use this file to fill the Tier and Lineages columns of the claim ledger and to decide which sources to read further.

## Credibility tiers

Assign the tier for the claim the source supports: one source can be strong for one claim and weak for another.

- A: controlling or system-of-record evidence: enacted law, official filings, signed standards, official datasets, court decisions, original experimental data, first-party versioned documentation.
- B: primary research or direct evidence with inspectable methods: peer-reviewed papers, preprints clearly labelled as preprints, audit reports, original surveys, transcripts, official engineering accounts.
- C: high-quality independent synthesis: scholarly reviews, established investigative reporting, expert technical analysis with transparent sourcing.
- D: discovery-only material: vendor marketing, unsourced explainers, aggregators, anonymous posts, low-transparency newsletters, tertiary summaries. Use it only to find other sources.
- E: prohibited or quarantined material: fabricated sites, content farms, malicious pages, unverifiable AI-generated text, copied content with missing provenance, sources whose use breaks the access rules. Do not use it.

## What to assess in each retained source

- Identity and accountability of the author, organization, publisher and domain.
- Directness: whether it observed, measured, authored or regulated the fact, or only repeated it.
- Method quality, sample, definitions, units, jurisdiction and limitations.
- Publication and last-update dates relative to the claim.
- Version, correction, retraction, supersession and archival status.
- Its own citations, and whether they support what it says.
- Incentives, conflicts, sponsorship, advocacy and commercial interest.
- Completeness, and whether important caveats were left out.
- Integrity signals: copied phrasing, template-heavy pages, fabricated biographies, nonexistent references, impossible dates.

Do not treat an AI-detector score as decisive. Judge low-quality or synthetic material by provenance, factual checks, citation integrity, authorship, publication process, copying across sources and comparison with primary records. Do not infer credibility from search rank, visual polish, domain familiarity, citation count or confident prose alone.

## Primary evidence and freshness

- Use primary evidence for numbers, dates, product capabilities, legal status, benchmark results, scientific findings and quotations whenever it is accessible. Use a secondary source to locate primary evidence, explain context or carry an attributed interpretation.
- If only secondary evidence is available, say so and lower confidence.
- Follow citations backward until the originating evidence is found or the trail breaks.
- For fast-moving claims, check the as-of date of the fact separately from the page's publication date, and prefer event time over article time when reporting what happened.
- Set a freshness window per claim class: an old theorem may be current while a recent product list may be stale. Query explicit dates for current products, prices, laws, officeholders, security incidents, benchmarks and market data.
- Label preprints, archived repositories, preview or beta features and self-reported benchmark numbers as such.
- Keep apart no newer evidence found and evidence that nothing changed.

## Corroboration rules (Lineages required)

- 1: one Tier A record may support a straightforward claim, unless the record is disputed, outdated or self-reported.
- 2: a material claim without a controlling record needs two independent sources.
- 2, one of them primary: a consequential, surprising, disputed or commercially self-reported claim needs at least one primary source plus one independent source.
- 3: a high-impact claim, where error could cause substantial harm, needs three independent lineages or a domain expert.

These do not count as separate lineages: syndicated copies, press-release rewrites, pages citing the same paper, mirrored datasets, cloned model outputs, or articles quoting one anonymous source. Several measurements from the same upstream dataset are one lineage for the dataset's validity, and separate only for genuinely independent analysis.

## Signs that sources depend on each other

- Identical unusual wording, numbers, ordering, typos, examples or timestamps.
- Shared hyperlinks, footnotes, dataset versions, press releases or unnamed experts.
- A publication order showing that later sources could only have copied an earlier one.
- Explicit according-to chains.
- Shared domain ownership, syndication notes, canonical tags or repository forks.

If independence cannot be established, count the sources as one lineage.
