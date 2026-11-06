---
created: "2026-11-04T19:58:28Z"
updated: "2026-11-04T19:58:28Z"
---

# Scope, asset inventory and flow map: fields and categories

## Scope

- Boundaries: physical, logical and organizational. Mark every trust boundary, the point where security policy changes between components, and classify each as internal or external, upstream or downstream, or cross-domain.
- Stakeholder record: role and responsibilities, authority level, information access requirements, constraints and dependencies, trust level within the system.
- Stakeholder mapping aids, when the roster is large: a power-interest grid (influence and engagement need), a knowledge chart (expertise and information requirements), a value network (tangible and intangible exchanges).
- Lifecycle stages to map each data type through: creation or capture; storage and access; usage and processing; archiving and retention; disposal or deletion. Note which stakeholders touch the data at each stage, and the retention and disposal rules.
- Scope statement: what the analysis includes and excludes.

## Asset inventory

- Asset record: identifier and name, type and format, storage location(s), owner and custodian, creation date and source, current lifecycle stage, dependencies on other assets.
- Classification levels: Public (no harm from disclosure; meant for public use), Internal (internal use only), Confidential (high protection; limited authorized access), Restricted (highest risk; special access controls). An organization with no policy of its own can start with Public, Internal and Confidential.
- Classification dimensions to weigh: sensitivity (privacy or confidentiality impact), criticality (business continuity impact), regulatory impact, integrity requirements, availability requirements. Record the reason for each classification.
- Granularity: fine-grained detail (individual records, column-level data) supports precise analysis and targeted controls but costs storage and complexity; coarse aggregation (monthly totals, department totals) is simpler but loses detail. Record each granularity decision with its reason (analytical need, privacy need, performance, storage, regulation).
- Provenance fields, where provenance matters: source, generation date and time, creator identity, legal rights (licence, copyright, use restrictions), privacy constraints, data type and collection method, intended use, lineage (transformation history).

## Flow map

- Upstream source types: primary (the original creator: a transactional system, a device, user input), secondary (an aggregator or processor that supplies transformed data), external (a third-party provider, a public dataset, a partner).
- Downstream consumer types: direct, derived (uses transformed or aggregated versions), reporting and analytics, external (partners, regulators, the public).
- Access patterns: read-only; read-write with modification rights; transformation and derivation; deletion or archival authority.
- Dependency types: sequential, parallel (several sources feed one consumer), conditional (flow depends on a rule or event), cyclical (feedback loop). Characteristics: coupling strength, failure impact, change propagation, bottlenecks.
- Data flow diagram notation, when a diagram is drawn: circles for processes, rectangles for external entities, parallel lines for data stores, arrows for flows labelled with the data they carry.
- Lineage levels: table level (dataset to dataset), column level (field transformations; needed for precise impact analysis), cross-system (end to end across platforms).

## Example rows (format only)

A transit agency shares ridership data with a university.

| ID | Asset | Owner | Class | Reason |
|---|---|---|---|---|
| A-03 | Smart-card trip records (card number, tap time, stop) | Fare systems manager | Confidential | Trip sequences reveal home and work locations |

| From | To | Assets | Access | Crosses boundary |
|---|---|---|---|---|
| Fare database | University research server | A-03 | Read-only extract | Yes: external |
