---
created: "2026-11-05T00:15:49Z"
updated: "2026-11-05T00:15:49Z"
---

# Venue catalog: how to enumerate, what to pin, how to check versions, default tier, citation form

One section per venue. Each gives the evidence it holds, the container to enumerate, the fields that pin a version, the newer-version check, the default tier and the citation form. The log value is what the search log's Venue column holds; the source type is what the inventory's Source type column holds. Web searches outside a venue are logged as `web`.

## IETF Datatracker

- Holds: Internet-Drafts (individual and working-group adopted), RFCs, BoF materials. Log value `ietf`; source type `rfc` or `internet-draft`.
- Enumerate: the Datatracker document-list API (JSON, no key). Filter by `group__acronym` with `type=draft` to list a working group's drafts (the list includes superseded individual drafts); `name__contains` matches the draft's filename, not its title; `title__icontains` matches titles; `limit=0` returns everything without paging. Each document also has a JSON metadata record (with `rev`, `time` and `replaced_by`) and a working-group documents page. The search page filters by document type, author or affiliation, working group, area, state and stream.
- Read a working group's list once; do not run keyword searches over a group that holds under 50 documents. A draft about agent authorization may be named after its protocol and never contain the topic word in its filename, so use group sweeps and title filters rather than filename tokens alone.
- Pace: Datatracker publishes no rate limit; stay at or below one request per second.
- Pin: draft name, revision number, `time` (last updated), status (active, expired, replaced-by), stream.
- Newer-version check: compare `rev` in the metadata record with the revision in the user's citation; check `replaced_by` and the expired state. Follow every `replaced_by` link and cite the successor (an individual draft is often replaced by a working-group draft, and group lists hold both). Drafts expire after six months but stay retrievable; an expired draft may be the only text for a concept, so keep it with status expired rather than dropping it.
- Default tier: RFC T1; working-group draft (`draft-ietf-*`) T2; individual draft (`draft-<author>-*`) T3.
- Cite as: RFCs by number; Internet-Drafts by name with revision, the words Work in Progress and the last-updated date, for example draft-ietf-wimse-arch-08 (Work in Progress, 2026-07-06).
- Topic seed for agent identity and authorization: working groups `wimse`, `oauth`, `spice`, `rats`, `scim`, `bmwg`; filename tokens `aiagent`, `agent`, `aip`, `daap`; title filter `agent`.

## NIST CSRC

- Holds: SP 800 and SP 1800 series, NIST IR, FIPS, drafts and finals. Log value `nist`; source type `nist-sp`.
- Enumerate: the CSRC publications search, with keyword, series, status (Final, Draft), sort and items-per-page parameters, plus topic and 800-53 control-family filters. A topic word that is not a CSRC topic (agent is not one) works poorly alone: combine the keyword with series and date filters and read the list.
- Pin: publication number, revision, status (ipd initial public draft, 2pd, fpd, final), date, DOI of the form 10.6028/NIST.SP.<number>.
- Newer-version check: look for a superseded-by banner on the publication page and read its status; a draft (ipd, 2pd, fpd) text differs from the final, and the search returns both, so a cited draft may since have been finalized.
- Default tier: Final T1; public draft T2.
- Cite as: number, revision, status and DOI.

## NIST NCCoE

- Holds: project descriptions, concept papers, practice guides (SP 1800). Log value `nist`; source type `nccoe`.
- Enumerate: no search API. Open the project page and read its documents list; concept papers are PDFs whose path carries the year and month. If the project page has moved, web search restricted with `site:nccoe.nist.gov` for the PDF.
- Pin: document title, the date in its path, project name.
- Newer-version check: compare the date on the project page with the user's citation.
- Default tier: practice guide (SP 1800, final) T1; concept paper or project description T2.
- Cite as: the pinned fields above.

## OWASP GenAI Security Project

- Holds: Top 10 lists, whitepapers and guides, cheat sheets, landscape reports. Log value `owasp`; source type `owasp`.
- Enumerate: the project's resources listing page, filtered by category and by initiative; it has no search box and no search API. Fetch the listing once, filter by initiative and date, and do not crawl. Titles on the listing are the canonical titles; use them verbatim.
- Pin: title, version string, publication date, PDF URL.
- Newer-version check: compare the version string or date on the listing with the user's citation.
- Default tier: versioned publication T2; landscape or vendor-listing report T3.
- Cite as: title verbatim with version or date.

## Cloud Security Alliance

- Holds: working-group research artifacts, Labs research notes, frameworks. Log value `csa`; source type `csa`.
- Enumerate: the research artifacts listing, with topic, industry, chapter and language filters; paginated, no keyword API. Labs research notes and frameworks sit on the CSA Labs site. Fetch each listing once; do not crawl. Listing titles are canonical; use them verbatim.
- Pin: title, publish date, working group, URL. Artifacts carry no version number, so the date is the pin.
- Newer-version check: compare the date on the listing with the user's citation.
- Default tier: working-group artifact T2; Labs research note or blog T3.
- Cite as: title verbatim with date.

## OpenID Foundation

- Holds: Final specifications, Implementer's Drafts, drafts, community-group papers. Log value `openid`; source type `openid`.
- Enumerate: the specifications page, organized by working group and maturity (Final Specifications, Active Drafts, Implementer's Drafts, Inactive, Errata, Obsolete); community groups are listed separately. Working groups relevant to identity and authorization: AB/Connect (OpenID Connect Core), AuthZEN (Authorization API), Shared Signals (CAEP and RISC), Federation. Enumerate the working group's page; there is no cross-specification search.
- Pin: specification name, status (Final, Implementer's Draft N, Draft NN), date.
- Newer-version check: compare the status and date on the working group's page with the user's citation.
- Default tier: Final T1; Implementer's Draft T2; draft or community-group paper T3.
- Cite as: name with status and date.

## CoSAI (Coalition for Secure AI)

- Holds: workstream papers. Log value `cosai`; source type `cosai`.
- Enumerate: the publications listing page has returned not-found while the PDFs stayed live in the site's uploads area. Web search with `site:coalitionforsecureai.org` plus the topic, open the PDF, and confirm version and date on its title page.
- Pin: title, version and date from the PDF, and the URL that actually served it.
- Newer-version check: compare the version on the PDF's title page with the user's citation.
- Default tier: versioned workstream publication T2.
- Cite as: title with version or date.

## Model Context Protocol (MCP) specification

- Holds: the protocol specification in dated versions, including the authorization section. Log value `mcp`; source type `mcp-spec`.
- Enumerate: the specification's versioning page. Versions are `YYYY-MM-DD` strings; each revision is Draft, Current or Final; each version has a deprecated-features registry; the authorization section sits under each version's basic section. Change history (SEPs and release notes) is in the project's public repository.
- Pin: version date string and section; whether the version is Current or Final.
- Newer-version check: read the versioning page; if the cited version is not Current, note which Current section supersedes the cited text. The authorization section changed materially across versions, so a claim about MCP authorization without a version date cannot be verified.
- Default tier: Current or Final version T2 (an industry specification, not a standards-body standard); Draft T3.
- Cite as: the `YYYY-MM-DD` version and the section.

## W3C

- Holds: recommendations such as DID Core and the Verifiable Credentials Data Model. Log value `w3c`; source type `w3c`.
- Enumerate: the W3C technical reports listing, which shows each document's status (Recommendation, Candidate Recommendation, Working Draft) and date.
- Pin: short name, status, date.
- Newer-version check: compare the status and date on the listing with the user's citation.
- Default tier: Recommendation T1; Candidate Recommendation or Working Draft T2.
- Cite as: the pinned fields above.

## Vendor research and documentation

- Holds: secrets-sprawl and identity-posture reports, hyperscaler agent-identity documentation, identity-provider vendor frameworks. Log value `web`; source type `vendor`.
- Enumerate: no listing. Web search restricted with `site:` to the vendor's domain, plus the report name and year.
- Pin: title, edition or year, publication date, URL, and the specific figure cited. A vendor figure is reproducible only with its report edition and publication date.
- Newer-version check: look for a later edition of the same report.
- Default tier: report that discloses its method and data T3; marketing page or unversioned document T4.
- Cite as: the pinned fields above.
