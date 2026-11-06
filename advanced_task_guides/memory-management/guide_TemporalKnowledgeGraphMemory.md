# Temporal Knowledge Graph Memory

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Temporal knowledge graph memory constitutes the task family of holding an agent's durable knowledge as a graph whose edges carry time, so that the system can state not only what it believes now but what was true at a represented instant, what it held on record at an earlier system instant, and which evidence moved it between those states. This guide provides AI agents with a structured protocol for declaring two independent time axes and holding them apart, extracting temporal references from natural language and bounding their uncertainty, admitting claim versions under interval validation, distinguishing a correction that revises what the system believed from a change that records that the world moved, invalidating rather than deleting superseded edges, reconstructing a point-in-time belief state, and auditing interval integrity with repair that never falsifies history. It partitions every phase across a deterministic tier owning interval arithmetic, bitemporal indexing, invalidation, reconstruction, consistency checking, and traversal, a model tier owning extraction and the resolution of relative or vague temporal reference, and a hybrid tier in which the model proposes a bounded timestamp and software accepts or rejects it. It quantifies every admission gate, overlap tolerance, and audit rate with a stated consequence for breach, and emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that history survives contact with new information.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Temporal knowledge graph memory**: A durable store in which each consequential claim is held as an immutable, attributable version carrying an explicit interval on each of two time axes, and in which superseded versions are closed rather than overwritten. A timestamped edge is not a temporal graph; a single timestamp cannot distinguish when a fact held from when the system learned it.

**Claim**: A proposition about the represented world, expressed as a subject, a predicate, and an object, and asserted by an identified source.

**Claim version**: One immutable record of a claim, carrying a valid interval, a transaction interval, provenance, confidence, status, and supersession links. Versions are appended; a version is never edited in place.

**Logical claim key**: The identity under which successive versions of the same claim are grouped, typically the tuple of tenant, subject, predicate, and object scope. Version history is meaningless without a stable key to group it under.

**Valid time**: The interval during which a proposition holds in the represented world. Valid time is asserted by the application or extracted from evidence, may be set to the past or the future, and may be revised. SQL:2011 calls this application time [1].

**Transaction time**: The interval during which a particular claim version was the system's record. Transaction time is assigned by the store at commit, is never set to a future instant, and is never edited once written. SQL:2011 calls this system time [1].

**Bitemporal record**: A claim version carrying both axes. A fact may become valid on 1 January, arrive on 10 January, and be revised on 20 January, and all three positions must remain independently recoverable [1].

**Decision time**: The instant at which an authorised actor decided that a claim should apply. Decision time becomes a third queryable axis only where the decision itself carries legal or operational meaning; otherwise it is recorded as provenance [2].

**Half-open interval**: An interval that includes its start instant and excludes its end instant. Adjacent versions then meet without overlapping, and a change at an exact instant belongs to the successor.

**Valid-end semantics**: A declared marker distinguishing an unbounded end, an unknown end, and a not-applicable end. A single null overloaded across all three destroys the distinction between an open claim and an unrecorded one.

**Temporal granularity and precision**: The resolution the evidence supports and the resolution the store holds. A source stating "in 2024" supports a year interval, not midnight on 1 January.

**Temporal uncertainty bounds**: A pair of offsets stating how far before and after a recorded instant the true instant may lie. A resolved timestamp without bounds is an assertion of exactness the evidence rarely supports.

**Edge invalidation**: Closing a claim version's transaction interval and linking it to its successor, so the version becomes ineligible for current reads while remaining retrievable under an earlier transaction perspective. Invalidation is not deletion.

**Correction**: A write recording that the system's prior record was wrong. It closes the erroneous version on the transaction axis and opens a replacement carrying the intended valid interval.

**Change**: A write recording that the world moved. It closes the incumbent claim on the valid axis at the instant of the transition and opens a successor from that instant.

**Point-in-time reconstruction**: Deriving the set of claim versions visible under a stated transaction instant and a stated valid instant, and rebuilding the graph projection restricted to that set.

**Co-validity**: The property that every edge and versioned endpoint on a traversal path shares a non-empty valid-interval intersection. A path whose edges were each true at some time but never simultaneously true is not a historical path.

**Temporal cardinality**: The number of concurrently valid values a relation admits for one subject and scope. A relation admitting exactly one is functional; overlap on a functional relation is an integrity violation.

**Commit sequence**: A monotonically increasing order key assigned at commit, independent of wall-clock time, used to order writes that share or invert physical timestamps [15].

**Currency and recency**: Currency means valid now; recency means asserted or observed recently. A newly ingested historical fact is recent and not current, and conflating the two is the most common source of a stale answer served as fresh.

### 1.2 The Two Axes and What an As-Of Query Means on Each

**Axis independence**: Valid time and transaction time are orthogonal. Neither constrains the other beyond the single rule that transaction time is never set ahead of the commit instant. A fact may be recorded late, corrected retroactively, or learned in an order different from the order in which the underlying events occurred. Conflating the axes corrupts every historical query, because the system then has one dimension in which to express two independent facts.

**What each axis answers alone**: A valid-time constraint selects versions whose valid interval contains the requested world instant, and answers what the system now believes was true then. A transaction-time constraint selects versions whose transaction interval contains the requested system instant, and answers what the system had on record then. Neither alone answers the audit question.

**The dual-axis query**: Binding both axes answers what the system believed at system instant X about what was true at world instant Y. An agent that can bind only the valid axis can answer what it believes now about any past moment, but cannot answer what it believed when it made a decision, which is the question an audit asks. Every deployment that records decisions must support the dual-axis form.

**Query Perspectives and the Axes They Bind**:

| Perspective | Valid-time binding | Transaction-time binding | Question answered |
| :-- | :-- | :-- | :-- |
| Current | Instant equals now | Latest committed snapshot | What the system believes holds now |
| Historical world | Instant or range equals Y | Latest committed snapshot | What the system now believes held at Y |
| As-of belief | Instant equals now | Snapshot as of X | What the system held on record at X about the present |
| Dual-axis audit | Instant or range equals Y | Snapshot as of X | What the system believed at X about validity at Y |
| Transaction history | Unconstrained | Full transaction range | Every recorded version and the order of revision |
| Valid history | Full valid range | Latest committed snapshot | The currently believed timeline of the claim |

**Default binding is mandatory and must be echoed**: Where a caller omits an axis, the read layer applies a documented default and returns the applied default in the answer metadata. A read that silently defaults without disclosure produces an answer whose temporal perspective cannot be reconstructed, and such an answer is unusable as evidence.

### 1.3 Correction Versus Change as Two Distinct Operations

**The distinction**: A change records that the world moved and that the prior record was right for its period. A correction records that the prior record was wrong and that no period existed in which it held. These are different operations with different write patterns, different audit meanings, and different downstream propagation, and they must not share a code path.

**The write rule**: A change writes on the valid axis. The incumbent's valid interval is closed at the transition instant, and a successor version opens at that instant. A correction writes only on the transaction axis. The erroneous version's transaction interval closes, a replacement opens carrying the intended valid interval, and the erroneous version's valid extent is never shortened.

**The failure produced by conflating them**: Processing a correction as a change fabricates a period during which the wrong value was true, which is a falsification of history that survives every subsequent audit. Processing a change as a correction erases the record that the earlier value was ever true and destroys the evidence of the transition, which removes the system's ability to explain why a decision taken under the earlier value was reasonable.

**Bitemporal Version Ledger for a Change and a Correction**:

```
LOGICAL CLAIM: employer(person_71)

CHANGE  (person moved from A to B on 2026-06-01; learned 2026-06-03T09:00Z)
  v1  value=A  valid=[2020-01-01, INF)          txn=[2020-01-05T11:00Z, 2026-06-03T09:00Z)
  v2  value=A  valid=[2020-01-01, 2026-06-01)   txn=[2026-06-03T09:00Z, INF)
  v3  value=B  valid=[2026-06-01, INF)          txn=[2026-06-03T09:00Z, INF)
  write_reason_code   = WORLD_CHANGE
  effective_change_at = 2026-06-01
  NOTE: v1 remains a true statement about the period it covered

CORRECTION  (value was never B; it was C throughout; learned 2026-06-10T14:00Z)
  v3  value=B  valid=[2026-06-01, INF)          txn=[2026-06-03T09:00Z, 2026-06-10T14:00Z)
  v4  value=C  valid=[2026-06-01, INF)          txn=[2026-06-10T14:00Z, INF)
  write_reason_code   = RECORD_CORRECTION
  effective_change_at = NULL
  NOTE: the valid interval of v3 is not shortened; v3 is withdrawn, not ended
```

**Required discriminating evidence**: A change requires evidence naming a transition instant in the represented world. A correction requires evidence that the earlier record misread its own source, or an authoritative restatement from the same source covering the same period. Where neither is present the case is unresolved, and an unresolved case is quarantined rather than settled by recency.

**Recency is not authority**: A newer statement may be a correction, a change, a scope difference, a duplicate, a corroboration, or an error, and the classifier must return which. A store resolving conflicts by preferring the latest write cannot represent corrections at all, because it expresses every revision as a movement of the world.

**Closing is not succeeding**: Closing an interval and asserting a successor are separate operations. Evidence that a relationship ended closes the incumbent without establishing what replaced it, and a new assertion conflicts with an incumbent only where the relation is functionally exclusive for that subject and scope.

### 1.4 Execution Tier Partition, Authority, and Scope Boundary

The method divides across three execution tiers. The partition is binding: a step assigned to the deterministic tier is never delegated to a model, and every model output entering a deterministic artifact passes through a gate able to reject it.

**Tier Ownership by Artifact and Operation**:

| Artifact or operation | Owning tier | Authority on disagreement |
| :-- | :-- | :-- |
| Interval arithmetic and Allen relation evaluation | Deterministic | Deterministic; a model-stated relation is advisory only |
| Bitemporal indexing and visibility filtering | Deterministic | Deterministic; no model output enters the visibility predicate |
| Edge invalidation, supersession linking, interval close | Deterministic | Deterministic; the model supplies a classification, never the write |
| Point-in-time reconstruction and answer replay | Deterministic | Deterministic; reconstruction is a query, never a generation |
| Overlap, gap, and dangling-endpoint consistency checks | Deterministic | Deterministic; violations halt and are not argued away |
| Traversal and co-validity intersection | Deterministic | Deterministic; an empty intersection prunes the path unconditionally |
| Calendar, time-zone, and duration arithmetic | Deterministic | Deterministic; computed in a time library against a pinned time-zone database |
| Commit ordering and clock-skew reconciliation | Deterministic | Deterministic; commit sequence outranks wall-clock comparison |
| Entity, relation, and time-expression extraction from text | Model | Model proposes; schema validation admits or rejects |
| Resolution of relative and vague temporal reference | Model | A declared deterministic anchor outranks a model-inferred one |
| Correction-versus-change classification | Hybrid | Deterministic constraints veto; unresolved cases route to review |
| Temporal cardinality and authority declaration per relation | Hybrid | An approved human declaration outranks any model proposal |
| Answer explanation and ambiguity reporting | Model | The model may explain an answer it is not permitted to compute |

**The uncertainty rule for model-resolved time**: Every timestamp a model resolves carries an explicit uncertainty pair and a granularity label. The model returns the source span, the candidate anchors, the selected anchor, the normalised value, the granularity, the bounds, a rationale code, and an abstention option. A deterministic gate rejects any assertion whose time cannot be bounded: an endpoint with no upper and no lower bound, a granularity finer than the cited evidence supports, or an anchor resolving to no recorded reference instant. Rejected assertions are preserved as unstructured source text rather than promoted with a manufactured timestamp.

**What the model tier may never decide alone**: whether two intervals overlap; whether a path is co-valid; which version is visible at a transaction instant; whether a functional-relation violation exists; whether a claim may be physically deleted; and whether a write is a correction or a change wherever the deterministic constraint set is decisive.

**Boundary against neighbouring memory guides**: Event records, their boundaries, their capture gating, and their outcome labelling belong to the episodic memory guide, and this guide consumes episodes as evidence for claim intervals rather than as substitutes for them. Ontology design, entity resolution, and the validity intervals attached to individual assertions belong to the companion semantic memory guide, whose store is current-state by default and is versioned bitemporally only where a point-in-time competency question justifies the cost; this guide owns the graph model that carries time on its edges and the query semantics over both axes. Read and write transaction mechanics, consolidation policy, distributed clock skew, and storage tiering belong to their respective companions, and this guide states only the temporal contracts those systems must honour. The distinctive subject here is the temporal graph model and the semantics of querying it.

**Justification gate for adopting the pattern**: A temporal graph is warranted only where relationship structure and changing truth interact. The decisive requirement is a historical graph question: which relationships coexisted, what path was valid at a stated time, or what the system believed then about another time. Where only current relationships matter, a plain graph suffices. Where history and constraints dominate but variable-length traversal does not, bitemporal relational tables are cheaper and more auditable [1][12][13][14]. Where evidence passages rather than normalised relationships are the product, timestamped documents in a filtered vector index suffice. Adopting a temporal graph without a historical graph question imposes extraction, invalidation, indexing, and version-bloat cost for no recoverable benefit.

***

## II. Operational Framework: Bitemporal Claim Curation and Point-in-Time Query

The framework assumes the justification gate in Section 1.4 has returned adopt. Phases 1 through 3 establish and populate the store, Phase 4 governs revision, Phase 5 governs reading, and Phase 6 runs continuously alongside the others and gates release. Phases 2 through 5 repeat for every ingestion and every read; Phase 1 repeats whenever a relation, schema, clock convention, or authority declaration changes.

### Phase 1: Temporal Schema and Axis Declaration

**Objective**: Fix the two axes, the interval conventions, the per-relation temporal contracts, and the deterministic oracle before any claim is written, so that later history is interpretable rather than merely stored.

#### Step 1.1: Declare the Axes and the Interval Conventions

**Required Actions**:

- Declare valid time and transaction time as separate stored intervals on every claim version, and prohibit any schema in which one column serves both.
- Adopt half-open intervals on both axes, including the start instant and excluding the end instant, so adjacent versions meet without overlapping.
- Define three distinct end markers per axis: unbounded end, unknown end, and not applicable, and prohibit a single null standing for more than one of them.
- Store every ordering instant in UTC, and retain alongside it the original local expression, the IANA zone identifier, the offset, the locale, the calendar, and the normalisation rule applied.
- Pin the time-zone database version, the calendar library version, and the normalisation rule version as fields on the record, and record a commit sequence or hybrid logical clock alongside wall time for write ordering [15].
- Declare which of the thirteen Allen interval relations the deployment must evaluate, and implement only those, retaining tests for inverse symmetry and composition [5].

**Required Outputs**:

- An axis declaration naming both intervals, their maintainers, and their editability rules.
- An interval convention record stating endpoint inclusivity, the three end markers, and the infinity sentinel.
- A clock and calendar record naming the ordering time scale, the pinned time-zone database version, and the ordering key.
- An implemented Allen relation subset with its inverse and composition test set.

**Quality Checkpoints**:

- Valid time and transaction time occupy separate stored columns or properties on 100 percent of claim versions; a shared column halts schema approval.
- Transaction-time end instants are never set ahead of the commit instant, and transaction-time values are never editable after commit.
- Daylight-saving fold, leap-day, and equal-timestamp cases pass the temporal conformance suite in every service that writes claims; a single failing service blocks ingestion.
- Every implemented Allen relation passes its inverse-symmetry test, since multi-hop reasoning depends on composition holding.

***

#### Step 1.2: Specify Per-Relation Temporal Contracts

**Required Actions**:

- Define for every relation its valid-time meaning, its transaction-time authority, its temporal cardinality, its supported granularity, its permitted uncertainty, its freshness budget, its retention class, and its authoritative source class.
- Mark each relation functional where exactly one value may be concurrently valid for one subject and scope, and multi-valued otherwise, and record the scope that qualifies the constraint.
- Record whether decision time is a queryable third axis for the relation or provenance only, defaulting to provenance unless the decision carries legal or operational meaning [2].
- Declare the permitted valid-time granularities per relation from the set second, minute, day, month, year, event-relative, and unknown, and reject finer promotion than the declared floor.
- Assign every relation a staleness budget in seconds and a revalidation interval in seconds, distinguishing both from the valid-time end.

**Required Outputs**:

- A relation contract register with one row per relation carrying all eight declared attributes.
- A functional-relation list naming each exclusive relation and its qualifying scope.
- A granularity floor table stating the finest admissible resolution per relation.
- A freshness policy table stating staleness budget and revalidation interval per relation.

**Quality Checkpoints**:

- Every relation admitted to the store appears in the contract register; an unregistered relation is refused at write time rather than defaulted.
- No universal one-value-at-a-time rule is applied across relations; cardinality is declared per relation and per scope.
- Every open-ended relation carries either a permanence class or a scheduled next-verification instant; an open interval with neither raises an overdue alert.
- Staleness budget is recorded as a separate field from valid-time end on 100 percent of relations, since a stale fact is not a false one.

***

#### Step 1.3: Select the Representation and Establish the Deterministic Oracle

**Required Actions**:

- Enumerate the competency questions the store must answer, separating current, historical-world, as-of-belief, dual-axis, range, and path questions, and record which representation each requires.
- Select the least complex representation that preserves every enumerated question, choosing interval versioning for point-in-time state, event records for domain actions and causal audit, and snapshots for fast reconstruction or release publication.
- Verify by test rather than by vendor claim whether the selected store maintains transaction time natively, versions node properties, and enforces interval constraints, and represent any unsupported history as fact edges or external bitemporal records [6][9][10][11].
- Implement a bitemporal relational oracle over the same evidence, independent of the graph implementation, to serve as the correctness reference for every point-in-time and dual-axis answer [1][12][13][14].
- Keep canonical claim versions independent of graph, lexical, vector, summary, and snapshot projections, and mark every projection rebuildable from canonical state.

**Required Outputs**:

- A competency question inventory tagged by required query perspective.
- A representation decision record naming the selected model and the questions that justify it.
- A verified capability matrix recording, per tested behaviour, whether the store supports it natively, by application code, or not at all.
- A deterministic oracle implementation with a documented evidence-loading procedure.

**Quality Checkpoints**:

- Every enumerated competency question is answerable by the selected representation; an unanswerable question either changes the representation or is removed from scope.
- No capability is recorded as supported on the basis of documentation alone; each carries a passing test identifier.
- The oracle reproduces the graph implementation's answers on the labelled corpus with at most 0 unexplained divergences before the graph is permitted to serve reads.
- Canonical versions carry no dependency on any projection; a projection rebuilt from scratch reproduces byte-equivalent derived state.

***

### Phase 2: Temporal Extraction and Bounded Time Resolution

**Objective**: Convert source text into candidate claim assertions whose temporal position is anchored, bounded, and traceable to a preserved source expression, so that no timestamp enters the store more precise than its evidence.

#### Step 2.1: Detect and Preserve Temporal Expressions

**Required Actions**:

- Preserve the source text and record every temporal expression as a span before any normalisation is attempted, retaining span offsets, expression type, modifier, tense, aspect, polarity, and modality [16].
- Classify each expression as date, time, duration, set, or event-anchored, and record whether it is explicit, relative, vague, or absent.
- Run a deterministic parser over explicit dates and arithmetic, a rule-based temporal tagger over well-covered relative expressions, and a model call only over the residual ambiguity [17].
- Record the reference timestamp, reference time zone, locale, and calendar against which relative expressions will be resolved, and treat an unrecorded reference as a hard extraction failure.
- Separate negation from invalidation at extraction time, treating a time-qualified negative claim as an assertion in its own right rather than as a signal to close another version.

**Required Outputs**:

- An expression inventory carrying span, type, modifier, tense, aspect, polarity, and modality per detected expression.
- A parser routing record naming which resolver handled each expression and why.
- A declared reference context carrying reference timestamp, zone, locale, and calendar.
- A negative-claim list separated from the contradiction queue.

**Quality Checkpoints**:

- Every candidate assertion carries at least one source span reference; an assertion with no span is refused promotion.
- Deterministic and rule-based resolvers handle every explicit date, and no explicit date is routed to the model tier.
- The reference context is recorded on 100 percent of documents carrying relative expressions; a missing reference context quarantines the document.
- Span detection F1 on the labelled corpus is at least 0.85; below that threshold extraction is not promoted to structured claims for the affected source class.

***

#### Step 2.2: Resolve Relative and Vague References with Explicit Bounds

**Required Actions**:

- Resolve each relative expression against the declared reference context and a declared disambiguation rule, recording which rule applied.
- Resolve event-anchored expressions only after the anchor event is linked and its own best-supported interval is established; leave the expression unresolved where the anchor is unlinked.
- Preserve vague terms as bounded ranges or unresolved constraints, and never convert a vague term to an exact instant.
- Emit for every resolved expression the granularity, the lower uncertainty offset, the upper uncertainty offset, the selected anchor, the rejected candidate anchors, a rationale code, and a confidence score.
- Return an explicit abstention rather than a guess wherever candidate anchors are equally supported or no reference resolves.
- Where no date is present, record which default applied from the set present-tense default, document-creation default, episode-time default, and unknown, rather than silently assuming one.

**Required Outputs**:

- A resolved temporal record per expression carrying value, granularity, both uncertainty offsets, anchor, and confidence.
- A rejected-candidate record naming alternatives considered and the reason each was not selected.
- An abstention log carrying the abstention reason per unresolved expression.
- A default-application record naming which absence default applied per assertion.

**Quality Checkpoints**:

- Every resolved value carries a granularity label and both uncertainty offsets; a value missing either is treated as unresolved.
- No vague expression resolves to a zero-width uncertainty range; a zero-width range on a vague expression is a resolver defect.
- Exact normalised-value accuracy on the labelled corpus is at least 0.90 for explicit expressions and at least 0.70 for relative expressions; a class falling below its threshold is routed entirely to abstention until recalibrated.
- Interval intersection over union for uncertain ranges is at least 0.60 on the labelled corpus; below that, the source class is preserved as text without structured promotion.

***

#### Step 2.3: Gate Candidate Assertions Before Admission

**Required Actions**:

- Reject any candidate whose valid-time endpoints carry no upper and no lower bound, whose granularity is finer than the relation's declared floor, or whose anchor resolves to no recorded reference instant.
- Reject any candidate whose uncertainty half-width exceeds the relation's declared granularity, or exceeds 25 percent of the relation's median observed claim duration, whichever is larger.
- Route to human review any candidate whose resolution confidence is below 0.75, whose relation is in the highest risk tier, or whose resolved interval extends more than 2 years before the earliest evidence date for that subject.
- Preserve rejected candidates as unstructured source text with their spans intact, and record the rejection reason code, so that a later resolver improvement can reprocess them.
- Record temporal modality per candidate from the set actual, planned, expected, hypothetical, counterfactual, and reported, and admit only actual and reported assertions to the accepted claim path.

**Required Outputs**:

- An admission verdict per candidate carrying accept, reject, or review with a reason code.
- A quarantine store holding rejected candidates with spans, resolver outputs, and reason codes.
- A review queue carrying candidates above the risk or below the confidence threshold.
- A modality-tagged candidate set with non-actual modalities held outside the accepted claim path.

**Quality Checkpoints**:

- No assertion enters the store with an unbounded resolved timestamp; the gate rejects unbounded time unconditionally.
- Every rejection carries a reason code drawn from a closed vocabulary; an uncoded rejection blocks the ingestion batch.
- Planned, expected, hypothetical, and counterfactual assertions appear in 0 current-view answers.
- Review queue depth stays below 5 percent of admitted candidates per source class; above that, the resolver for that class is recalibrated before ingestion resumes.

***

### Phase 3: Admission, Interval Validation, and Ordered Commit

**Objective**: Commit accepted assertions as immutable claim versions whose intervals satisfy the declared constraints and whose order is recoverable independently of wall-clock time.

#### Step 3.1: Validate Interval Well-Formedness and Overlap

**Required Actions**:

- Reject any interval whose start is not strictly before its end, whose endpoints carry incompatible granularities, or whose end marker is ambiguous between unbounded and unknown.
- Retrieve every incumbent version sharing the logical claim key, with a compatible object type and an overlapping valid interval, restricted to versions visible in the current transaction snapshot.
- Evaluate overlap on functional relations with a tolerance of exactly 0, since half-open intervals make adjacency non-overlapping and remove the boundary case that a tolerance would otherwise absorb.
- Route to reconciliation, rather than rejection, an overlap of at most 1000 milliseconds on a functional relation where both endpoints carry recorded clock uncertainty spanning the overlap; reject any overlap above that bound.
- Detect gaps between consecutive versions of a functional relation and classify each as a permitted unknown period, an extraction omission, or an integrity failure, recording the classification rather than closing the gap silently.
- Prohibit automatic trimming of an interval to make validation pass, and record an overlap resolution code on every reconciled case.

**Required Outputs**:

- A well-formedness verdict per candidate interval.
- An incumbent overlap set per candidate, restricted to the current transaction snapshot.
- A reconciliation queue holding clock-uncertainty overlaps within the 1000 millisecond bound.
- A gap classification record per detected gap on a functional relation.

**Quality Checkpoints**:

- No functional relation holds two concurrently valid versions for one subject and scope at any point in valid time; a detected overlap halts the write.
- No interval is silently trimmed; every boundary adjustment carries an overlap resolution code and an evidence reference.
- Gaps are classified rather than filled; an unclassified gap on a functional relation raises an integrity finding.
- Reconciliation queue depth stays below 0.5 percent of writes per relation; above that, clock configuration is investigated before ingestion resumes.

***

#### Step 3.2: Commit the Immutable Version and Assign Its Order

**Required Actions**:

- Write the claim version with its valid interval, its transaction start, its provenance chain, its confidence, its status, its granularity, its uncertainty offsets, and its original source expression, and never mutate a committed version thereafter.
- Assign the transaction start from the store's own clock at commit, never from a value supplied by the ingesting caller, and set the transaction end to the unbounded marker.
- Assign a commit sequence number or hybrid logical clock value at the same commit, so that writes sharing or inverting wall-clock timestamps remain orderable [15].
- Make the write idempotent on a deterministic content key, so that a retried ingestion produces 0 duplicate versions.
- Publish graph, lexical, vector, and summary projections asynchronously through a transactional outbox, keeping the canonical commit synchronous and minimal.
- Record the schema version, policy version, extractor version, prompt version, and time-zone database version on the committed record, so a later replay can pin every generation.

**Required Outputs**:

- A committed immutable claim version with both intervals populated.
- A commit ordering key recorded alongside the wall-clock transaction start.
- An outbox entry per derived projection requiring update.
- A generation pin record naming every version-bearing component active at commit.

**Quality Checkpoints**:

- 0 committed versions are edited in place; an in-place update of a temporal predicate is denied by the write layer rather than detected afterwards.
- Transaction start is store-assigned on 100 percent of versions; a caller-supplied transaction time is rejected.
- Crash replay of the write log reproduces byte-equivalent canonical state with no partially published projection.
- Every committed version carries a complete generation pin; a missing pin field blocks the commit.

***

#### Step 3.3: Admit Late and Out-of-Order Arrivals Without Reordering History

**Required Actions**:

- Insert a late-arriving fact with its historical valid interval and a current transaction start, so that the record shows both when the fact held and when the system learned it.
- Compute and record the lateness and the out-of-order offset in milliseconds for every arrival, measured between source assertion time and commit time.
- Recompute, after every late insertion, the affected current projections, the affected historical answers whose transaction perspective postdates the insertion, the affected contradiction set, and the affected summaries, embeddings, and materialised paths.
- Leave answers whose transaction perspective predates the insertion unchanged, since a later arrival must never alter what the system is recorded as having believed earlier.
- Order concurrent or skewed writes by commit sequence or causal clock rather than by wall-clock comparison, and mark as incomparable any pair whose uncertainty intervals overlap with no causal relation resolving them [18].

**Required Outputs**:

- A late-arrival record carrying lateness, out-of-order offset, and affected valid range.
- An affected-artifact inventory naming every claim, cache key, embedding, summary, and materialisation requiring recomputation.
- A replay record carrying start instant, completion instant, and the set of prior answers whose values changed.
- An incomparability record for event pairs that no clock resolves.

**Quality Checkpoints**:

- An as-of answer computed at a transaction instant preceding a late insertion returns identical results before and after that insertion; any change is a bitemporal correctness defect that halts serving.
- Every late arrival triggers propagation, and propagation completes within the relation's staleness budget; propagation lag above the budget raises an alert and marks affected current answers as unverified.
- Ordering is never repaired by sorting wall-clock timestamps alone; a wall-clock-only reordering is a release-blocking defect.
- Late-arrival rate and out-of-order rate are recorded per source; a source exceeding 10 percent out-of-order arrivals is reviewed for clock or pipeline defects.

***

### Phase 4: Invalidation, Correction, and Change Handling

**Objective**: Retire superseded claim versions by closing and linking them rather than by deleting them, and execute a correction and a change through separate, separately audited write paths.

#### Step 4.1: Classify the Relation Between Candidate and Incumbent

**Required Actions**:

- Classify every candidate against each overlapping incumbent into exactly one of eight categories: duplicate, corroboration, succession, scope difference, world change, record correction, unresolved contradiction, or independent multi-valued fact.
- Require, for a world change classification, evidence naming a transition instant in the represented world, and record that instant as the effective change instant.
- Require, for a record correction classification, evidence that the earlier record misread its source or an authoritative restatement covering the same period, and record the erroneous version identifier.
- Apply the relation's declared temporal cardinality before classification, since overlap on a multi-valued relation is ordinary and contradiction there requires incompatible values, an explicit negation, an authority rule, or a domain constraint.
- Emit the classification with a confidence score, the compared version identifiers, the overlap interval, the constraint identifier applied, and the classifier version.
- Route to human adjudication every case classified as correction with confidence below 0.85, every case in the highest risk tier, and every case classified as unresolved.

**Classification Outcomes and the Axis Each Writes**:

| Classification | Discriminating evidence | Axis written | Incumbent disposition |
| :-- | :-- | :-- | :-- |
| Duplicate | Same value, same interval, same source lineage | None | Retained; support count incremented |
| Corroboration | Same value, compatible interval, independent source | None | Retained; independent support recorded |
| Succession | Prior interval already closed; new value follows | Valid | Retained unchanged |
| Scope difference | Qualifying scope differs between the two claims | None | Retained; both remain valid |
| World change | Transition instant in the represented world | Valid | Valid interval closed at the transition instant |
| Record correction | Prior record misread its source or is restated | Transaction | Transaction interval closed; valid extent untouched |
| Unresolved contradiction | Incompatible values, no discriminating evidence | None | Retained; candidate quarantined |
| Independent multi-valued | Relation admits concurrent values | None | Retained; both remain valid |

**Required Outputs**:

- A classification record per candidate and incumbent pair with confidence, evidence references, and classifier version.
- An adjudication queue holding low-confidence corrections, high-risk cases, and unresolved contradictions.
- A quarantine set holding candidates whose classification did not resolve.

**Quality Checkpoints**:

- Every classification names exactly one category from the closed vocabulary; a multi-label or unlabelled outcome halts the write.
- No classification of world change is admitted without a recorded effective change instant.
- No classification of record correction is admitted without a named erroneous version identifier.
- Correction-versus-change classification accuracy on the adjudicated sample is at least 0.95; below 0.93, autonomous classification is suspended for the affected relation and every case routes to review.

***

#### Step 4.2: Execute a World Change on the Valid Axis

**Required Actions**:

- Close the incumbent's valid interval at the recorded effective change instant, writing a new version that carries the shortened valid interval and a fresh transaction start rather than editing the incumbent.
- Close the incumbent's transaction interval at the same commit instant, so the pre-change record remains retrievable under an earlier transaction perspective.
- Open the successor version from the effective change instant with an unbounded or evidence-supported valid end, and link it to the predecessor through a supersession reference.
- Record the write reason code as a world change, the effective change instant, the evidence identifiers, and the reason the transition was accepted.
- Recompute derived current projections, materialised paths, summaries, and embeddings that referenced the incumbent, and record propagation completion.

**Required Outputs**:

- A shortened predecessor version carrying the closed valid interval.
- A successor version opening at the effective change instant with a supersession link.
- A change event record carrying reason code, effective change instant, and evidence references.
- A propagation completion record naming every recomputed derivative.

**Quality Checkpoints**:

- The predecessor remains retrievable and remains a true statement about the period it covers; its removal from history is a defect.
- The predecessor's closed valid end equals the recorded effective change instant exactly; a boundary mismatch halts the write.
- Predecessor and successor intervals meet without overlapping under the half-open convention, with an overlap tolerance of 0.
- No world change is written where the effective change instant is absent, since without it the operation is indistinguishable from a correction.

***

#### Step 4.3: Execute a Correction on the Transaction Axis

**Required Actions**:

- Close the erroneous version's transaction interval at the commit instant, and leave its valid interval exactly as recorded.
- Write the corrected version carrying the intended historical valid interval and a transaction start at the commit instant, linked to the withdrawn version through a correction reference distinct from the supersession reference used for changes.
- Record the write reason code as a record correction, with a null effective change instant, the withdrawn version identifier, the adjudicator identity where review applied, and the evidence establishing the error.
- Replay every prior answer whose transaction perspective postdates the correction commit, and label each as changed or unchanged, leaving answers under earlier perspectives untouched.
- Preserve the withdrawn version in full for audit, and never shorten its valid interval as though the world had moved.

**Required Outputs**:

- A withdrawn version with a closed transaction interval and an unchanged valid interval.
- A corrected version carrying the intended valid interval and a correction reference.
- A correction event record carrying reason code, withdrawn version identifier, adjudicator, and evidence.
- A changed-answer audit listing prior answers whose values moved and the perspectives under which they moved.

**Quality Checkpoints**:

- The withdrawn version's valid interval is byte-identical before and after the correction; any change to it is a falsification of history and halts release.
- Correction references and supersession references are stored in separate fields, so an audit can count corrections independently of changes.
- Answers computed under a transaction perspective preceding the correction are reproducible after it with 100 percent fidelity.
- 0 corrections are executed through the change code path, verified by asserting that the change path rejects any input carrying a null effective change instant.

***

### Phase 5: Point-in-Time, Interval, and Path Query

**Objective**: Answer every read under an explicitly bound pair of temporal perspectives, returning the interval over which the answer holds and the version set that produced it.

#### Step 5.1: Bind Both Axes and Return the Perspective

**Required Actions**:

- Require every read to carry a valid-time mode and a transaction-time mode, and apply a documented default where one is omitted, echoing the applied default in the answer metadata.
- Implement the six perspectives named in Section 1.2 as typed query entry points, so that a caller selects a perspective rather than assembling predicates.
- Evaluate point-in-time predicates as containment within the half-open interval, and range predicates through the declared Allen relation subset rather than through vague overlap language [5].
- Combine claims in a temporal join only where their valid intervals overlap and their versions are visible under the same transaction snapshot, and return the intersection interval as the derived claim's validity.
- Filter by tenant, deletion status, transaction visibility, and valid interval before or during approximate vector search, and never retrieve globally in the expectation that a reranker will remove temporally ineligible items.
- Return with every answer the version identifiers used, the applied perspective, the answer's validity interval, and a currency label from the set current, stale, unverified, and historical.

**Required Outputs**:

- A typed query interface exposing one entry point per perspective.
- An answer record carrying used version identifiers, applied perspective, validity interval, and currency label.
- A derived-claim interval computed as the intersection of its inputs.

**Quality Checkpoints**:

- 100 percent of answers carry an explicit valid-time and transaction-time perspective; an answer without both is not released.
- Every temporal join returns an intersection interval; a join returning a bare value without its validity is a defect.
- Approximate search is never executed before eligibility filtering where the engine cannot guarantee post-filter recall.
- Currency labels distinguish current from stale and unverified on 100 percent of answers, since recency of assertion is not currency of truth.

***

#### Step 5.2: Enforce Co-Validity Across Every Traversal

**Required Actions**:

- Intersect the valid intervals of every traversed edge and every versioned endpoint as traversal proceeds, and prune the path immediately when the running intersection becomes empty.
- Apply the transaction-time visibility filter to every hop under the same snapshot, so a path never mixes versions from different belief states.
- Carry the surviving intersection forward as the valid interval of any fact inferred from the path, and reject an inference whose supporting intersection is empty.
- Prune temporally before expanding variable-length paths, rather than expanding first and filtering afterwards.
- Record per path the hop count, the edge identifiers, the per-edge valid intervals, the running intersection, the co-validity verdict, and the count of pruned branches.

**Required Outputs**:

- A co-valid path set with the surviving intersection interval per path.
- A pruning record naming the hop at which each rejected path failed.
- An inferred-claim set carrying the intersection interval as its validity.

**Quality Checkpoints**:

- 0 returned paths contain an edge pair whose valid intervals do not intersect; a single such path is a co-validity error and blocks release.
- Co-validity errors per thousand multi-hop answers stay at 0 on the labelled corpus; any non-zero rate suspends multi-hop serving for the affected relation.
- Temporal pruning precedes variable-length expansion in the executed query plan, verified by plan inspection rather than by assumption.
- Every inferred fact carries an intersection interval; an inferred fact presented without one is withdrawn.

***

#### Step 5.3: Reconstruct a Point-in-Time Belief State

**Required Actions**:

- Reconstruct a belief state by selecting the version set whose transaction intervals contain the requested system instant and whose valid intervals satisfy the requested world constraint, and project the graph over that set alone.
- Pin, for any answer that must be reproduced, the schema version, the policy version, the extractor and prompt versions, the classifier version, the graph generation, the lexical and vector index generations, and the time-zone database version alongside the dual-axis specification.
- Cache reconstruction results only under a key containing tenant, policy version, valid-time specification, transaction as-of instant, graph generation, and query plan hash, and invalidate the entry when a source interval within its dependency set changes.
- Branch counterfactual questions from an immutable reconstructed snapshot, label every generated alternative as hypothetical, and prohibit writing any counterfactual into accepted history.
- Avoid reconstructing from the beginning of history where a snapshot or materialised projection at an intermediate instant is available, and bound reconstruction latency by the density of versions rather than by total history length.

**Required Outputs**:

- A reconstructed version set with its transaction and valid constraints recorded.
- A generation pin bundle sufficient to reproduce the answer independently.
- A cache key specification naming every dimension the key must carry.
- A counterfactual branch record labelled hypothetical and held outside accepted history.

**Quality Checkpoints**:

- Dual-axis reproducibility on the audited answer sample is 100 percent; below 99.9 percent, release is blocked and the missing pin dimension is identified.
- 0 counterfactual branches appear in accepted history or in any current-view answer.
- Every cache entry carries all six key dimensions; an entry missing any dimension is evicted rather than served.
- Reconstruction latency at the ninety-fifth percentile stays within the declared budget for the query class; a breach triggers snapshot or index revision rather than relaxation of correctness.

***

### Phase 6: Consistency Audit, Repair, and Lifecycle Operation

**Objective**: Detect interval and history defects continuously, repair them without falsifying the record, and hold freshness, retention, and erasure as scheduled policy rather than as incidental behaviour.

#### Step 6.1: Run the Interval Integrity Audit

**Required Actions**:

- Run overlap detection on every functional relation after every import, migration, backfill, and classifier change, and on a scheduled sweep at an interval no longer than the shortest relation revalidation interval.
- Detect and count gap anomalies, dangling supersession references, correction references pointing at versions that were never withdrawn, versions whose transaction end precedes their transaction start, and edges valid outside the valid window of either endpoint version.
- Run metamorphic checks: shifting every timestamp by a constant duration preserves all interval relations; swapping a relation with its inverse transforms Allen labels consistently; adding an irrelevant later transaction leaves every earlier as-of answer unchanged; and splitting an interval into two adjacent equivalent versions leaves point-in-time results unchanged.
- Compare a sampled set of point-in-time and dual-axis answers against the deterministic relational oracle established in Step 1.3, and record every divergence with both answers attached.
- Report violations as a rate per million versions per relation, and separate detection from repair so that a defect is recorded before anything is written.

**Required Outputs**:

- An integrity finding record per violation carrying constraint identifier, violation type, violation interval, and affected version identifiers.
- A metamorphic test report with one verdict per invariant.
- An oracle divergence report listing each mismatch with both answers and the perspective applied.
- A violation rate report per relation, expressed per million versions.

**Quality Checkpoints**:

- Interval integrity violations stay at or below 50 per million versions per relation; above 200 per million, ingestion halts for that relation until the cause is identified.
- All four metamorphic invariants hold; a single failing invariant blocks release regardless of aggregate accuracy.
- Oracle divergence on the audited sample is 0; any unexplained divergence halts graph serving and routes reads to the oracle.
- Every finding is recorded before any repair is attempted, so that repair activity cannot conceal defect volume.

***

#### Step 6.2: Repair Violations Without Falsifying History

**Required Actions**:

- Repair through append-only operations: write a corrected version, close an erroneous one, or record an unresolved finding, and never mutate or delete a committed version to make a constraint pass.
- Select the repair operation from the same closed vocabulary the write path uses, so that a repair is auditable as a correction or as a change rather than as an unlabelled adjustment.
- Quarantine, rather than repair, any violation whose correct resolution depends on evidence the system does not hold, and expose quarantined subjects as unverified in every current-view answer.
- Roll back a failed repair through a recorded rollback operation that itself appends, and verify after rollback that every as-of answer preceding the repair remains reproducible.
- Recompute affected projections after every repair and record propagation completion, treating a repair as complete only when serving projections agree with canonical history or reads fall back to canonical history.

**Required Outputs**:

- A repair operation record carrying operation type, affected versions, evidence, and operator identity.
- A quarantine record per unrepairable violation with the missing evidence named.
- A rollback record per failed repair with a post-rollback reproducibility verdict.
- A propagation completion record per repaired claim.

**Quality Checkpoints**:

- 0 repairs delete or mutate a committed version; a destructive repair is denied by the write layer.
- Every repair carries a write reason code identical in vocabulary to ordinary writes, so repairs and ordinary revisions are counted together in the correction and change ledgers.
- Every as-of answer preceding a repair reproduces identically after it; a reproducibility failure reverts the repair and escalates.
- Quarantined subjects appear as unverified rather than as current in 100 percent of answers touching them.

***

#### Step 6.3: Operate Freshness, Retention, and Erasure

**Required Actions**:

- Schedule revalidation per relation at its declared interval, fetch or request fresh evidence, compare it against the current claim, and record the outcome as reaffirmed, changed, corrected, or unverified.
- Treat a failed revalidation as an absence of confirmation rather than as proof of falsity, and mark the claim unverified without closing its valid interval.
- Apply confidence decay to epistemic confidence and retrieval eligibility only, never to historical validity, and retain the original calibrated confidence alongside the decayed value with the decay function version recorded.
- Apply expiry only where the proposition's truth is inherently short-lived or a retention contract requires it, and on expiry close retrieval eligibility rather than fabricating a world-valid end.
- Assign every claim and its evidence a retention class, a legal basis, a purpose, a sensitivity class, a consent reference, a legal-hold flag, and an erasure deadline, and justify why each retained history class is necessary and proportionate [20].
- Execute erasure by writing a policy tombstone that makes affected versions immediately ineligible for every read, then traverse evidence, claim versions, supersession and correction links, node properties, named graphs, embeddings, lexical indexes, summaries, caches, evaluation sets, exports, replicas, and backups, recording lawful exceptions and scheduled backup expiry.

**Required Outputs**:

- A revalidation outcome record per scheduled check with prior and new verification status.
- A decay configuration record naming function version, inputs, and retained original confidence.
- A retention register carrying all seven policy attributes per claim class.
- A deletion record carrying tombstone identifier, target artifacts, deleted artifacts, exception artifacts, backup expiry, and verifier identity.

**Quality Checkpoints**:

- Open-ended claims overdue for verification by more than twice their staleness budget raise an alert and are labelled unverified rather than current; an overdue open interval served as current is a serving defect.
- Confidence decay never alters a valid interval; a decay operation touching valid time halts the scheduler.
- Every test erasure reaches 100 percent of derivative artifacts within the declared window; a single reachable copy after the window blocks release.
- No invalidated version is reported as erased while its content remains retrievable under any transaction perspective.

***

## III. Implementation Guidance for AI Agents

AI agents operating a temporal knowledge graph must follow systematic protocols ensuring that every write is append-only, every read declares its perspective, and every revision is attributable to a correction or to a change. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Schema Authority Agent**: Owns the axis declaration, the interval conventions, the relation contract register, and the granularity floors. It alone may amend a temporal contract, and every amendment is versioned and triggers a full integrity audit.
2. **Extraction Agent**: Detects temporal expressions, routes them to the deterministic, rule-based, or model resolver, and emits bounded candidate assertions. It never writes to canonical state and never selects a timestamp it cannot bound.
3. **Admission Agent**: Validates interval well-formedness, evaluates overlap against incumbents, and returns accept, reject, review, or reconcile. It holds authority over every model-proposed timestamp and may refuse promotion.
4. **Revision Agent**: Classifies candidate against incumbent and dispatches to exactly one of the change path or the correction path. It may not write directly; it selects the path and supplies the evidence.
5. **Query Agent**: Binds both axes, executes typed perspective queries, enforces co-validity during traversal, and attaches the perspective and validity interval to every answer. It never generates a temporal value it did not retrieve.
6. **Audit Agent**: Runs integrity sweeps, metamorphic checks, and oracle comparisons, and may halt ingestion or serving for a relation. Its halt authority is not overridable by any other component.
7. **Lifecycle Agent**: Runs revalidation, decay, expiry, retention, and erasure jobs, and owns the tombstone-first deletion sequence.

**Write-Path Separation**: The change path and the correction path are distinct code paths with distinct entry points, distinct reason codes, and distinct audit counters. The change path rejects any input carrying a null effective change instant. The correction path rejects any input attempting to modify a valid interval on the withdrawn version. Neither path may be reached by defaulting from the other.

**Workflow Execution Pattern**:

```
STATE: Revision_Dispatch
INPUTS:
  1. Accepted candidate assertion with bounded valid interval
  2. Incumbent version set overlapping on the logical claim key
  3. Relation contract with temporal cardinality and authority class
ACTIONS:
  1. Classify candidate against each incumbent into one closed-vocabulary label
  2. Verify discriminating evidence required by the assigned label
  3. Select exactly one write path: NONE, CHANGE_PATH, or CORRECTION_PATH
  4. Emit the write plan with reason code and affected version identifiers
VALIDATION:
  - classification_label IN closed_vocabulary
  - selected_write_path_count == 1
  - effective_change_at != NULL IF selected_write_path == CHANGE_PATH
  - withdrawn_version_id != NULL IF selected_write_path == CORRECTION_PATH
  - functional_overlap_after_write == 0
  - valid_interval_of_withdrawn_version_unmodified == TRUE
TRANSITIONS:
  IF all_validations_pass AND path == CHANGE_PATH THEN next_state = Close_Valid_Axis
  IF all_validations_pass AND path == CORRECTION_PATH THEN next_state = Close_Transaction_Axis
  IF classification == UNRESOLVED THEN next_state = Quarantine_And_Adjudicate
  IF validation_failed THEN next_state = Revision_Error_Handling
```

**Two-Phase Action Pattern**: Emit the write plan naming the path, the reason code, the affected versions, and the resulting interval geometry without committing it; validate the plan against the constraint set while no version has changed; commit only after validation passes, recording the classification and the write in the same transaction.

**Approval Gate**: Human authorisation is required before amending a relation's temporal cardinality or authority class, before executing a correction affecting more than 100 claim versions or any claim in the highest risk tier, before any physical deletion that is not driven by an approved erasure request, and before promoting a configuration whose oracle divergence has not been demonstrated at 0. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the relation contract register, the interval conventions, and the generation pin bundle in durable state, since ingestion and audit outlive any single context window.
- Process ingestion in bounded batches keyed by logical claim, so that overlap evaluation reads a small incumbent set rather than a whole relation.
- Summarise superseded evidence into content references once its claims are verified, retaining the references and discarding the bulk while preserving the source spans.
- Write a handoff record naming the contract version, the last committed commit sequence, the outstanding outbox depth, and the open adjudication queue at every context boundary.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Temporal Contract Integrity (After Phase 1)**

- **Automated Check**: Both axes stored separately on every version; half-open convention and three end markers implemented; every admitted relation present in the contract register with all eight attributes; the conformance suite passes in every writing service.
- **Agent Action on Pass**: Open ingestion for the registered relations.
- **Agent Action on Failure**: Halt before any write; an incomplete contract cannot be retrofitted onto history already stored under it.
- **Human Review Trigger**: Any relation whose temporal cardinality cannot be stated, or any deployment requiring decision time as a queryable third axis.

**Checkpoint 2: Extraction and Bounding Adequacy (After Phase 2)**

- **Automated Check**: Span F1 at least 0.85; explicit-value accuracy at least 0.90; relative-value accuracy at least 0.70; interval intersection over union at least 0.60; 0 admitted assertions carrying unbounded time.
- **Agent Action on Pass**: Release candidates to admission.
- **Agent Action on Failure**: Route the failing source class entirely to abstention and preserve its text unstructured until the resolver is recalibrated.
- **Human Review Trigger**: Review queue depth above 5 percent of admitted candidates for a source class, or any class whose accuracy falls by more than 5 percentage points between releases.

**Checkpoint 3: Admission and Ordering Validity (After Phase 3)**

- **Automated Check**: 0 functional-relation overlaps after commit; 0 caller-supplied transaction timestamps; every version carries a commit ordering key and a complete generation pin; crash replay reproduces canonical state.
- **Agent Action on Pass**: Publish derived projections through the outbox.
- **Agent Action on Failure**: Halt the batch, quarantine the offending versions, and re-run validation on the batch only.
- **Human Review Trigger**: Reconciliation queue depth above 0.5 percent of writes, or any source exceeding 10 percent out-of-order arrivals.

**Checkpoint 4: Revision Path Correctness (After Phase 4)**

- **Automated Check**: Exactly one classification label per pair; correction-versus-change accuracy at least 0.95 on the adjudicated sample; 0 withdrawn versions whose valid interval changed; 0 corrections routed through the change path.
- **Agent Action on Pass**: Proceed to propagation and projection update.
- **Agent Action on Failure**: Halt revision for the affected relation; an incorrect revision path is never committed with a warning attached.
- **Human Review Trigger**: Correction-versus-change accuracy below 0.93, or any correction affecting more than 100 versions.

**Checkpoint 5: Query Perspective and Co-Validity (After Phase 5)**

- **Automated Check**: 100 percent of answers carry both perspectives and a currency label; 0 co-validity errors on the labelled corpus; dual-axis reproducibility at 100 percent on the audited sample; temporal pruning precedes path expansion in the executed plan.
- **Agent Action on Pass**: Release answers to callers with their perspective metadata.
- **Agent Action on Failure**: Withhold the answer class and route reads to the deterministic oracle.
- **Human Review Trigger**: Dual-axis reproducibility below 99.9 percent, or any co-validity error in a released answer.

**Checkpoint 6: Integrity, Lifecycle, and Release (After Phase 6)**

- **Automated Check**: Integrity violations at or below 50 per million versions per relation; all four metamorphic invariants holding; 0 oracle divergences; every test erasure reaching all derivatives within the declared window.
- **Agent Action on Pass**: Permit promotion of the configuration and release of the metric report.
- **Agent Action on Failure**: Withhold promotion and name the failing invariant or the unreached derivative; a configuration is never promoted on aggregate accuracy alone.
- **Human Review Trigger**: Violations above 200 per million versions, any unexplained oracle divergence, or any erasure that did not complete.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Axis Conflation**

- **Symptoms**: A single timestamp column serves both axes; a historical query returns the same result regardless of the transaction perspective requested; a late-arriving fact appears in an as-of answer computed before it arrived.
- **Diagnostic Steps**: Inspect the stored schema for separate valid and transaction intervals; compute one as-of answer before and after a controlled late insertion and compare; confirm whether the transaction end is store-assigned or caller-supplied.
- **Resolution Protocol**: Option A, add the missing axis and backfill transaction intervals from the write log where one exists, marking backfilled intervals as reconstructed. Option B, where no write log exists, declare all existing history as a single opening transaction interval and record that pre-migration belief states are unrecoverable. Option C, run the graph read-only behind the deterministic oracle until the axis is restored.
- **Escalation Trigger**: Any deployment recording decisions escalates immediately, since without the second axis no decision can be justified after the fact. This class is never resolved by retry.

**Error Type 2: Correction Executed as a Change**

- **Symptoms**: A version exists whose valid interval was shortened without a recorded effective change instant; the history shows a period during which a value known to be wrong is presented as true; correction counters read 0 while revision volume is high.
- **Diagnostic Steps**: Query all versions whose valid interval was shortened and whose write reason code is not a world change; compare the correction and change counters against the adjudicated sample; inspect whether the change path accepts a null effective change instant.
- **Resolution Protocol**: Option A, restore the falsified interval by appending a correction that reinstates the original valid extent and withdrawing the fabricated version. Option B, where the original extent is unrecoverable, mark the affected logical claims as history-uncertain and exclude them from audit evidence. Option C, close the defect at source by adding the null-instant rejection to the change path before reprocessing.
- **Escalation Trigger**: Any falsified interval on a claim used in a regulated or audited decision escalates immediately; more than 5 falsified intervals in one relation halts revision for that relation.

**Error Type 3: Stale Fact Served as Current**

- **Symptoms**: An open-ended version far past its staleness budget is returned without a currency label; a contradiction was missed and both an old and a new value are current; a query omitted the valid-time filter entirely.
- **Diagnostic Steps**: Measure the age of every open-ended version against its relation's staleness budget; re-run contradiction detection over the affected logical claims; inspect the executed query plan for the presence of the eligibility filter.
- **Resolution Protocol**: Option A, label the affected claims unverified and re-run revalidation against the authoritative source. Option B, re-run the classifier over the affected claims and execute the missed change or correction through the appropriate path. Option C, block the current-view entry point for the affected relation until the eligibility filter is restored.
- **Escalation Trigger**: A stale-current-answer rate above 1 percent for a relation suspends current-view serving for that relation; three consecutive revalidation failures against the same source escalate to a source-availability review.

**Error Type 4: Co-Validity Violation in a Multi-Hop Answer**

- **Symptoms**: A returned path contains edges whose valid intervals do not intersect; an inferred fact carries no validity interval; path counts rise sharply when a temporal filter is added late in the plan.
- **Diagnostic Steps**: Recompute the running intersection hop by hop for each returned path; inspect the executed plan for the position of the temporal predicate relative to path expansion; verify that endpoint node versions are included in the intersection, not only edges.
- **Resolution Protocol**: Option A, move temporal pruning ahead of expansion and re-execute. Option B, include versioned endpoints in the intersection where only edges were considered. Option C, withdraw the affected answers, re-issue them under the corrected traversal, and label the withdrawn answers in the changed-answer audit.
- **Escalation Trigger**: Any co-validity error reaching a released answer suspends multi-hop serving for the affected relation; this class is never resolved by re-ranking or by post-filtering.

**Error Type 5: Interval Integrity Violation Under Load**

- **Symptoms**: Overlaps appear on functional relations after import or migration; gaps proliferate without classification; supersession links point at versions that do not exist.
- **Diagnostic Steps**: Compute violation rates per relation per million versions; correlate onset with import, migration, classifier, or clock configuration changes; verify whether database-level exclusion constraints are present or whether enforcement is application-only.
- **Resolution Protocol**: Option A, halt ingestion for the relation, repair through append-only corrections, and re-run the audit before resuming. Option B, move enforcement into the database where the store supports interval exclusion constraints. Option C, reduce ingestion concurrency for the relation so that overlap evaluation and commit occur in one transaction.
- **Escalation Trigger**: Violations above 200 per million versions halt ingestion for the relation; violations persisting after one repair pass escalate to a schema and concurrency review.

**Error Type 6: Version Proliferation and Query Degradation**

- **Symptoms**: Version amplification rises without a corresponding rise in distinct logical claims; current-view latency degrades while history grows; reconstruction scans the whole version set.
- **Diagnostic Steps**: Compute versions per logical claim and the history-to-current ratio per relation; inspect whether a partial index over open-ended versions exists; check whether repeated identical assertions are being written as new versions rather than counted as corroboration.
- **Resolution Protocol**: Option A, deduplicate logical claims without merging distinct provenance, counting repeats as corroboration. Option B, add a partial or filtered index over open-ended versions and range-aware indexes for overlap. Option C, archive cold history under a policy that preserves point-in-time service levels and erasure reachability.
- **Escalation Trigger**: Version amplification above 20 versions per logical claim, or a ninety-fifth percentile current-view latency breach persisting after one indexing pass, escalates to a representation review.

**Troubleshooting Decision Tree**:

```
TEMPORAL DEFECT DETECTED
├─ AXIS DEFECT
│   ├─ One column serves both axes → HALT writes; add the missing axis
│   ├─ Transaction time caller-supplied → Reject at write layer; reassign at commit
│   └─ As-of answer changed by a later arrival → HALT serving; audit visibility predicate
├─ REVISION DEFECT
│   ├─ Valid interval shortened, no change instant → Restore interval; withdraw fabrication
│   ├─ Withdrawn version's valid extent modified → HALT; correction path is defective
│   └─ Classification outside vocabulary → Reject write; re-classify or quarantine
├─ CURRENCY DEFECT
│   ├─ Open interval past staleness budget → Label unverified; schedule revalidation
│   ├─ Missing eligibility filter in plan → Block current view; restore filter
│   └─ Revalidation failed → Mark unverified, never mark false
├─ TRAVERSAL DEFECT
│   ├─ Empty intersection in a returned path → Withdraw answer; prune before expansion
│   └─ Inferred fact without interval → Withdraw the inference
├─ INTEGRITY DEFECT
│   ├─ Functional overlap above tolerance → HALT ingestion; repair append-only
│   ├─ Gap unclassified → Classify as unknown, omission, or failure
│   └─ Dangling supersession link → Repair link or quarantine the claim
└─ LIFECYCLE DEFECT
    ├─ Erasure incomplete after window → HALT release; traverse remaining derivatives
    └─ Invalidated version reported as erased → Correct the claim; content is still retrievable
```

### D. Performance Metrics and Continuous Learning

**Correctness Metrics**:

- **Point-in-time correctness**: Historical-world answers matching the deterministic oracle (target: 100 percent on the audited sample; any divergence halts graph serving).
- **Dual-axis reproducibility**: Audited answers reproducible under their original perspective and generation pins (target: 100 percent; below 99.9 percent blocks release).
- **Correction-versus-change accuracy**: Adjudicated revisions whose path matched the gold label (target: at least 0.95; below 0.93 suspends autonomous classification).
- **Invalidation precision and recall**: Superseded versions correctly closed and correctly left open (target: at least 0.95 precision and 0.90 recall per relation).
- **Co-validity error rate**: Released multi-hop answers containing a non-intersecting edge pair (target: 0; any occurrence suspends multi-hop serving).
- **Temporal normalisation accuracy**: Exact normalised-value accuracy by expression class (target: at least 0.90 explicit, at least 0.70 relative, reported separately because aggregate accuracy conceals divergent failure modes) [19].

**Operational Metrics**:

- **Stale-current-answer rate**: Current-view answers whose supporting claim was overdue for verification (target: at most 1 percent; above that, current-view serving is suspended).
- **Overdue open-interval count**: Open-ended versions past twice their staleness budget (target: 0 per relation at every audit).
- **Interval integrity violations**: Detected violations per million versions per relation (target: at most 50; above 200 halts ingestion).
- **Propagation lag**: Time from a late arrival or revision to completion of derivative recomputation (target: within the relation's staleness budget).
- **Version amplification**: Total historical versions divided by distinct logical claims (target: at most 20; above that triggers archival or deduplication review).
- **Query latency by class**: Ninety-fifth and ninety-ninth percentile latency reported separately for current point lookup, historical point lookup, range overlap, dual-axis query, temporal join, co-valid path, and correction replay, since these have materially different access patterns [7].

**Governance Metrics**:

- **Erasure completeness**: Test erasures reaching every derivative artifact within the declared window (target: 100 percent).
- **Abstention quality**: Extraction abstentions later adjudicated as correct refusals (target: at least 0.85).
- **Adjudication throughput**: Review queue drained within one revalidation interval (target: 100 percent of queued cases).

**Learning and Adaptation Mechanisms**:

- **Adjudicated corpus growth**: Add every adjudicated correction and change case to the labelled corpus, stratified by relation, source, language, time zone, ambiguity class, lateness, and risk tier, so that classifier evaluation is not dominated by easy cases.
- **Resolver comparison**: Retain the deterministic parser, the rule-based tagger, and the model resolver as disagreement partners, and treat disagreement rate by expression class as the primary recalibration signal rather than aggregate accuracy.
- **Threshold recalibration per relation**: Recompute overlap tolerances, uncertainty bounds, confidence gates, and staleness budgets per relation against observed outcomes, since a volatile functional relation and a stable multi-valued relation share no defensible threshold.
- **Generation-pinned replay**: Re-run the audited answer sample after every model, prompt, parser, schema, classifier, clock, database, or policy change, and reopen the labelling and calibration steps whenever any pinned generation moves.

**Human-in-the-Loop Boundaries**: Amendment of a relation's temporal cardinality or authority class, adjudication of an unresolved contradiction, approval of a correction affecting more than 100 versions or any highest-risk claim, authorisation of physical deletion outside an approved erasure request, and promotion of a configuration with an unexplained oracle divergence are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how changing claims are recorded and interrogated rather than what the claims are about. Its phases hold wherever facts change, evidence arrives out of order, records are sometimes wrong, and a later reviewer must be able to establish what the system held and when.

### 4.1 Cross-Domain Application Patterns

**Clinical and care records**: Valid time carries the period a diagnosis, medication, allergy, or care-team assignment applied to the patient, and transaction time carries when the record system held it. The correction path dominates, because transcription errors, misattributed results, and amended reports are routine, and shortening a diagnosis interval to absorb a transcription error would fabricate a period of untreated illness. Functional relations are narrow and carefully scoped, since a patient may hold many concurrent conditions but one primary care assignment. Dual-axis queries are the operative form for any review of a past clinical decision, because the question is what the clinician's record showed at the time, not what is now known.

**Financial and regulatory reporting**: Restatement is the defining operation, and the distinction between a restated figure and a changed underlying position is the distinction between a correction and a change. Decision time is often a genuine third axis here, because approval instants carry legal meaning independent of both the world and the ledger. Point-in-time reconstruction with full generation pinning is a deliverable rather than a diagnostic aid, since a regulator asks the system to reproduce a report exactly as issued. Erasure exceptions are common, and legal-hold flags must survive every retention job.

**Supply chain and logistics**: Valid time is short and dense, arrivals are frequently late, and clock skew across sites is ordinary rather than exceptional, so the commit sequence carries the ordering burden and wall-clock comparison is never authoritative. Co-validity dominates path queries, because a route, a carrier contract, and a customs authorisation must have been simultaneously valid for a shipment plan to have been legitimate. Version amplification is the principal cost driver, and archival policy must preserve point-in-time service levels for the audit window while discarding older detail.

**Workforce identity and entitlement governance**: The central question is which access a principal held at a stated instant, which is a co-valid path over role assignments, group memberships, and entitlement grants. Functional relations are strict, and an overlap on a single-value entitlement is a security finding rather than a data-quality finding. The as-of belief perspective matters as much as the historical-world perspective, because an access decision made under a stale directory record is a different failure from one made under a correct record.

**Conversational and long-horizon assistants**: Facts arrive as natural-language statements whose temporal reference is relative and vague, so the extraction and bounding phase carries most of the risk, and the abstention path is exercised heavily. Preferences and circumstances change frequently and are corrected often, so the two write paths must be distinguishable even when both are triggered by an ordinary utterance. Currency labelling is the user-visible control: the assistant that says a fact is unverified rather than asserting it as current is the one that remains trustworthy across sessions.

### 4.2 Scale, Risk, and Complexity Adaptation

- **Low-risk, low-volume deployments**: Collapse to a single bitemporal relational table with half-open range columns, exclusion constraints, immutable versions, scheduled revalidation, and a fixed typed query API. Retain both axes, both write paths, and the integrity audit; omit the graph projection until a historical graph question is demonstrated.
- **High-risk or regulated deployments**: Retain every phase, run the deterministic oracle continuously rather than on a sample, treat the event log as a deliverable, bind the approval gate before every correction, and require 100 percent dual-axis reproducibility before any answer is released as evidence.
- **High-volume, high-churn relations**: Shorten revalidation intervals, tighten version amplification budgets, partition cold history by transaction time only where erasure and point-in-time queries remain correct across partitions, and prefer event records with interval projections over dense interval versioning.
- **Distributed or multi-site ingestion**: Require a hybrid logical clock or equivalent order key on every write, mark event pairs incomparable where uncertainty intervals overlap and no causal relation resolves them, and never repair ordering by sorting wall-clock timestamps [15][18].
- **Strict latency budgets**: Maintain separate current and historical indexes, prune temporally before path expansion, and materialise snapshots at intervals bounded by the reconstruction latency target. Where latency forbids reconstruction, serve the current view only and refuse historical perspectives explicitly rather than approximating them.
- **Multi-tenant deployments**: Include tenant in every index prefix, every cache key, and every eligibility filter, and run integrity audits per tenant, since a cross-tenant overlap is a disclosure failure rather than a temporal one.

***

## V. Limitations and Considerations

**Bitemporality doubles the surface on which mistakes are made**: Two axes, two write paths, and interval geometry on both create defect classes that a single-timestamp store cannot exhibit, and those defects are silent until an audit asks a question the store answers wrongly with confidence. The mitigation is the deterministic relational oracle established in Step 1.3, compared continuously in Step 6.1, together with the metamorphic invariants that fail loudly on geometry errors rather than degrading quietly.

**The correction-versus-change classification is the highest-risk component**: It depends on evidence about the intent of a prior record, which is frequently absent from the source text, and a misclassification silently falsifies history in a way no aggregate accuracy figure will surface. The mitigation is the separate write paths with mutually exclusive required fields, the routing of low-confidence and high-risk cases to adjudication, and the suspension of autonomous classification below 0.93 accuracy on the adjudicated sample.

**Thresholds here are deployment defaults, not measured findings**: Every numeric bound stated in this guide, including the 1000 millisecond clock-uncertainty reconciliation window, the 0.75 resolution confidence gate, the 50 and 200 per million integrity violation rates, the 20-version amplification budget, and the 0.95 correction-versus-change target, was chosen to be operable on first deployment rather than derived from a measured property of temporal stores. The mitigation is the per-relation recalibration requirement in Section III.D, which obliges each deployment to recompute thresholds against its own observed outcomes and to record the recomputed values as the operative ones.

**Model-resolved time is systematically overconfident**: Language models produce syntactically valid timestamps for expressions the evidence does not determine, and a valid-looking timestamp passes every schema check. The mitigation is the bounding gate in Step 2.3, which refuses structured promotion to any assertion whose time cannot be bounded and preserves the source text instead, together with the requirement that vague expressions never resolve to a zero-width uncertainty range.

**History preservation increases privacy exposure**: Superseded names, addresses, affiliations, preferences, and inferred relationships remain queryable under earlier perspectives, and retaining them because audit is convenient is not a lawful basis. The mitigation is the retention register in Step 6.3, which requires a declared legal basis, purpose, sensitivity class, and erasure deadline per claim class, and the tombstone-first erasure sequence that makes affected versions ineligible before derivative traversal begins [20].

**Invalidation alone does not prevent a stale answer**: An open-ended version is current only where extraction, contradiction detection, expiry, and query filtering all work; a failure in any one of them serves a superseded fact as fresh, and the store will report no error. The mitigation is the currency labelling requirement in Step 5.1, the overdue open-interval alert in Step 6.3, and the stale-current-answer rate that suspends current-view serving above 1 percent.

**Vendor and benchmark figures are not transferable evidence**: Reported results for temporal memory platforms depend on prompts, evaluation categories, timestamp handling, search scope, interface versions, and reader models, and a published dispute over one such figure resulted in a substantial downward restatement by its own authors [23]. The mitigation is the independent verification obligation in Step 1.3: normalisation is tested by relation and language, invalidation is measured against a labelled contradiction set, node-property history is tested rather than assumed, and answers are compared against the deterministic oracle on the deployment's own evidence.

**Structural correctness is not usefulness**: A store can satisfy every interval constraint, pass every metamorphic invariant, and still answer no question anyone asks, at a cost that a plain graph or a filtered vector index would not have imposed. The mitigation is the justification gate in Section 1.4 and the competency question inventory in Step 1.3, which require a named historical graph question before the pattern is adopted and remove unanswerable questions from scope rather than expanding the representation to reach them.

***

## VI. Conclusion and Summary

Temporal knowledge graph memory is a discipline of controlled historical truth before it is a graph feature. Its value comes from a small number of commitments held without exception: two axes stored separately, intervals that are half-open and explicitly bounded, versions that are appended rather than edited, revisions that declare whether the world moved or the record was wrong, reads that declare the perspective they were taken under, and repairs that append rather than overwrite. A system holding those commitments can state what it believed, when that belief applied, why it changed, and which evidence supported every answer. A system relaxing any one of them will answer historical questions confidently and wrongly, and will not detect that it is doing so.

A team introducing this pattern should establish the simpler counterfactuals before building the graph. Implement timestamped documents with filtered retrieval, a plain current-state graph, and bitemporal relational tables over the same representative evidence, and measure task success, stale-answer rate, historical correctness, latency, storage, and cost on each. Adopt the temporal graph only where relational history cannot meet the traversal requirement and the measured gain exceeds the failure and operating cost the pattern imposes. Then fix the interval and clock conventions, build canonical append-only versions, label an adjudicated corpus containing world changes, prior errors, late facts, overlaps, gaps, open intervals, vague dates, and clock skew, and calibrate extraction and classification against it before any query surface is exposed. Add hybrid retrieval only after point-in-time correctness is demonstrated, and reopen the labelling and calibration steps after every model, parser, schema, clock, database, policy, or relation change.

**Key Success Factors**:

- **Two axes, never fused**: Valid time and transaction time occupy separate stored intervals with separate maintainers and separate editability rules, because one column cannot carry two independent facts.
- **Bounded time or no time**: Every admitted timestamp carries a granularity and an uncertainty pair, and an assertion whose time cannot be bounded is preserved as text rather than promoted with a manufactured precision.
- **Correction and change on separate paths**: A change closes the valid axis at a recorded transition instant; a correction closes the transaction axis and leaves the valid extent untouched; neither path is reachable by defaulting from the other.
- **Invalidate, never overwrite**: Superseded versions are closed and linked, remain retrievable under earlier perspectives, and are physically deleted only under an approved erasure, retention expiry, or lawful purge.
- **Declared perspective on every answer**: Each read binds both axes, returns the interval over which its answer holds, labels currency, and names the version set that produced it.
- **Deterministic authority over interval work**: Interval arithmetic, visibility, co-validity, integrity checking, and reconstruction are computed by software and verified against an independent oracle, and no model output enters them unchecked.

By following this guide, AI agents can hold changing knowledge in a form that survives late evidence, retroactive correction, and audit, and can answer not only what they believe now but what they believed when a decision was made.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them, retaining the labels that source used where it supplied no formal title; they were not independently re-verified in the course of this conversion. The final group lists work surfaced by searches run during this conversion, which confirmed that the two-axis treatment, the half-open interval convention, and the invalidate-rather-than-delete rule remain current practice; those entries were located by search and not read in full.

**Corpus pointers**:

- `Temporal Knowledge Graph Memory for AI Agents: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the two-axis and decision-time treatment, the interval and clock conventions, the representation selection criteria, the conservative extraction and normalisation discipline, the invalidation and supersession rules, the correction-versus-change distinction, the dual-axis query treatment and co-validity requirement, the freshness and retention policy, the characteristic failure modes, the telemetry field inventory, the baseline comparison protocol, and the twelve-step operational sequence. Its inline citations supply the external references listed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — the category overview covering the two-axis memory taxonomy, which admits a temporal graph only where multi-hop and point-in-time queries dominate. It owns that selection decision; this guide owns the model and the query semantics that follow from it.
- `advanced_task_guides/memory-management/guide_SemanticMemory.md` — companion guidance on the semantic claim store, its ontology, entity resolution, and assertion-level validity intervals. It owns the store as such, current-state by default; this guide owns the graph form that carries time on its edges and the query semantics over both axes.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — owns the read and write transaction mechanics that the scope boundary in Section 1.4 defers to it, including gate ordering, idempotency, and terminal states; this guide states only the temporal contracts those operations must honour.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — companion guidance on event records, episode boundaries, capture admission, and outcome labelling. It owns episodes; this guide consumes them as evidence for claim intervals.
- `advanced_task_guides/memory-management/guide_StructuredMemory.md` — companion guidance on structured stores and schema-governed writes, applicable to the canonical version design in Step 3.2.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on consolidation policy, applicable to the projection and summary derivatives recomputed in Steps 3.3 and 4.2.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — companion guidance on decay and deletion, applicable to the confidence decay and erasure sequence in Step 6.3.
- `advanced_task_guides/memory-management/guide_DistributedMemoryArchitecture.md` — companion guidance on distributed clocks and causal ordering, applicable to the commit sequence and incomparability rules in Steps 3.2 and 3.3.
- `advanced_task_guides/knowledge-graphs/guide_KG_SchemaDesign.md` — companion guidance on graph schema construction, applicable to the relation contract register in Step 1.2.
- `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md` — companion guidance on provenance and evidence lineage, applicable to the provenance chain required on every claim version.
- `advanced_task_guides/knowledge-graphs/guide_KG_EntityResolutionDedup.md` — companion guidance on identity resolution, applicable to the logical claim key and the duplicate and corroboration classifications in Step 4.1.
- `advanced_task_guides/knowledge-graphs/guide_KG_ScalabilityArch.md` — companion guidance on graph scaling, applicable to the indexing, partitioning, and version amplification concerns in Phase 6.
- `advanced_task_guides/knowledge-graphs/guide_KG_QualityControl.md` — companion guidance on graph quality control, applicable to the integrity audit and repair steps in Phase 6.
- `advanced_task_guides/ontology/guide_ontology_CompetancyQuestions.md` — companion guidance on competency question capture, applicable to the question inventory in Step 1.3.
- `advanced_task_guides/design-architecture/guide_SchemaFlexibilityandEvolution.md` — companion guidance on schema versioning and migration, applicable to the contract amendment and generation pinning requirements.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design and instrumentation, applicable to the logging inventory underlying the metrics in Section III.D.
- `advanced_task_guides/research-analysis/guide_TemporalEvolutionAnalysisandForecasting.md` — companion guidance on temporal analysis over evolving data, applicable to the interval and range query classes in Phase 5.
- `advanced_task_guides/policy-risk/guide_InformationDependencyDisclosureRiskAnalysis.md` — companion guidance on disclosure and dependency risk, applicable to the retention register and erasure traversal in Step 6.3.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control loops and independence of verification signals, applicable to the tier authority rules in Section 1.4 and the promotion gates in Phase 6.

**External references**: The numbering below is the numbering used by the inline markers in Sections I through V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Bitemporal modelling, temporal standards, and interval semantics*

1. PostgreSQL wiki, *SQL:2011 temporal summary* — https://wiki.postgresql.org/wiki/SQL2011Temporal
2. *Nascimento and Eich record* — https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=737ad02dc5543ec98bca6758827fedfdf083b3db
3. W3C, *OWL-Time* — https://www.w3.org/TR/owl-time/
4. ISO, *ISO 8601 overview* — https://www.iso.org/iso-8601-date-and-time-format.html
5. *Allen interval algebra reference* — https://www.ics.uci.edu/~alspaugh/cls/shr/allen.html

*Representation and store selection for versioned claims*

6. *Graphiti issue on node-property history* — https://github.com/getzep/graphiti/issues/1166
7. *VLDB temporal subgraph management* — https://www.vldb.org/pvldb/vol19/p1170-wen.pdf
8. *AeonG paper* — https://arxiv.org/pdf/2304.12212v2/
9. Neo4j, *versioning guidance* — https://neo4j.com/docs/getting-started/data-modeling/versioning/
10. Memgraph, *data types* — https://memgraph.com/docs/fundamentals/data-types
11. *Graphiti repository* — https://github.com/getzep/graphiti
12. PostgreSQL, *range types* — https://www.postgresql.org/docs/current/rangetypes.html
13. MariaDB, *temporal tables* — https://mariadb.com/docs/server/reference/sql-structure/temporal-tables/system-versioned-tables
14. Microsoft, *SQL Server temporal tables* — https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal/overview?view=sql-server-ver17

*Clock ordering, temporal expression processing, and reasoning evaluation*

15. *HLC paper* — http://www.cse.buffalo.edu/tech-reports/2014-04.pdf
16. *TimeML 1.2.1* — https://timeml.github.io/site/publications/timeMLdocs/timeml_1.2.1.html
17. *HeidelTime repository* — https://github.com/HeidelTime/heideltime
18. Google, *Spanner TrueTime and external consistency* — https://docs.cloud.google.com/spanner-omni/true-time-external-consistency
19. *TimeBench* — https://arxiv.org/html/2311.17667v2

*Retention, erasure, and platform evidence*

20. ICO, *right-to-erasure guidance* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/
21. *Zep graph overview* — https://help.getzep.com/graph-overview
22. *Zep paper* — https://arxiv.org/html/2501.13956v1
23. *benchmark correction discussion* — https://github.com/getzep/zep-papers/issues/5

*Temporal query semantics, immutable stores, and event sourcing*

24. XTDB, *time model* — https://docs.xtdb.com/about/time-in-xtdb.html
25. Datomic, *database filters* — https://docs.datomic.com/reference/filters.html
26. Datomic, *history* — https://docs.datomic.com/client-tutorial/history.html
27. Snowflake, *Time Travel* — https://docs.snowflake.com/en/user-guide/data-time-travel
28. Fowler, *Event Sourcing* — https://martinfowler.com/eaaDev/EventSourcing.html
29. W3C, *RDF 1.2 Concepts* — https://www.w3.org/TR/rdf12-concepts/
30. *Temporal Regular Path Queries* — https://arxiv.org/pdf/2107.01241v2

*Temporal reasoning and question-answering benchmarks*

31. *TRAM* — https://arxiv.org/abs/2310.00835
32. *CronQuestions paper* — https://arxiv.org/abs/2106.01515
33. *TimeQuestions project* — https://exaqt.mpi-inf.mpg.de/
34. *TempQuestions* — https://dl.acm.org/doi/fullHtml/10.1145/3184558.3191536
35. *TIQ* — https://dl.acm.org/doi/pdf/10.1145/3589335.3651895
36. *TempTabQA* — https://arxiv.org/abs/2311.08002
37. *Test of Time* — https://arxiv.org/html/2406.09170v1
38. *TimE* — https://neurips.cc/virtual/2025/poster/121417
39. *TemporalBench* — https://arxiv.org/abs/2602.13272

*Located by search during this conversion and not read in full*

40. *Bitemporal modeling* — https://en.wikipedia.org/wiki/Bitemporal_modeling
41. *A Graph-Native Bitemporal Memory Store for Conversational AI Agents* — https://arxiv.org/abs/2607.26520
42. *Graph-based Agent Memory: Taxonomy, Techniques, and Applications* — https://arxiv.org/pdf/2602.05665
43. *Comprehensive insights into bitemporal databases: a PRISMA-guided systematic literature review* — https://link.springer.com/article/10.1007/s42488-026-00162-x
44. *ChronoQG: Towards a Temporally Expressive and Hop-Bounded Benchmark for Temporal Knowledge Graph Question Generation* — https://arxiv.org/html/2607.14770v1
