---
created: "2026-11-05T00:15:49Z"
updated: "2026-11-05T00:15:49Z"
---

# Credibility tiers for standards and grey literature

Assign one tier per inventory row. The venue catalog gives each venue's default tier; this table decides the tier of a document whose status does not match a default, and says how a citing text may use it.

| Tier | Qualifies | How a citing text may use it |
|---|---|---|
| T1 Ratified | RFCs; NIST Final publications; W3C Recommendations; OpenID Final specifications | Cite freely for normative statements (MUST, SHALL) and definitions |
| T2 Body-endorsed, in progress or non-standards-body | Working-group Internet-Drafts (`draft-ietf-*`); NIST public drafts; NCCoE concept papers; OpenID Implementer's Drafts; versioned OWASP, CSA and CoSAI publications; MCP Current or Final specification versions | Cite with status and version (Work in Progress, public draft, v1.0); acceptable as evidence of consensus direction, not of settled practice |
| T3 Individual or vendor-with-data | Individual Internet-Drafts; community-group papers; CSA Labs notes; vendor research reports that disclose method and sample | Cite as proposals or measurements with attribution (X et al. propose; vendor Y reports); never for normative claims |
| T4 Unversioned or marketing | Vendor product pages, blog restatements of standards, undated pages | Do not cite; use only as a pointer to a T1 to T3 primary source |

A text aiming for rigor draws most standards citations from T1 and T2 and labels every T3 citation's status (proposal, draft or vendor measurement) in the sentence that cites it.
