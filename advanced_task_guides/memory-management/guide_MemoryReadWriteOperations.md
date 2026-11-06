# Memory Read and Write Operations

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Memory read and write operations constitute the task family of admitting a record to a durable store and retrieving records from it under an explicit contract. They are the two primitives on which every memory type depends: an episode, a claim, a working-state entry, a tier promotion, and a consolidated summary all reach durable storage through one write path and reach a model through one read path. This guide provides AI agents with a structured protocol covering the operation contract, a five-gate write path, a bounded read path, atomicity across a canonical store and its derived indexes, the injection boundary that keeps retrieved content data rather than instruction, and the instrumentation that makes both paths measurable. It specifies what a rejected write becomes, what a read is permitted to return, what an agent is guaranteed to observe after its own write, and what happens when a write succeeds in one store and fails in another. It partitions the work across a deterministic tier that owns authorization, validation, identity, indexes, transaction boundaries, and result bounds, and a model tier that owns candidate extraction and relevance judgement within an already eligible set. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a store which accepts anything does not become a store which retrieves anything.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Memory operation**: One logical requested effect against a memory store, either a write that admits or changes a record or a read that returns a bounded set of records. An operation is the unit of authorization, idempotency, logging, and measurement.

**Canonical store**: The single authoritative system holding immutable record versions, current pointers, tombstones, provenance, and idempotency claims. Every other store is derived from it.

**Derivative**: Any store rebuildable from the canonical store, including lexical indexes, vector indexes, graph projections, summaries, and caches. A derivative is never authoritative and never the source of a consistency guarantee.

**Record version**: One immutable serialization of a memory record, addressed by a version identifier that never changes meaning. A change produces a new version rather than mutating an existing one.

**Current pointer**: The mutable reference naming which version of a logical record is current. Advancing a pointer is the only sanctioned form of update.

**Operation identifier**: The identity of one logical requested effect across every retry and transport attempt. Retries of one operation share it; distinct operations never do.

**Idempotency key**: A tenant-scoped client-supplied token binding one request to one committed effect. A repeat with the same key and an equivalent request returns the original result; the same key with a different request hash is a conflict, never a new write.

**Admission gate**: One of the five deterministic checks a candidate must clear before durable commit: authorization, schema validation, provenance completeness, duplicate detection, and the confidence floor.

**Provenance**: The record of where content came from, comprising a source identifier, a source class, a capture timestamp, and the extraction method that produced the candidate.

**Source class**: The categorical label distinguishing quoted source, direct observation, tool output, model inference, and approved procedure. Source class governs trust, never relevance.

**Eligibility**: The property of a record being permitted to reach a given caller for a given purpose at a given time, determined by tenant, principal, purpose, consent, sensitivity, validity interval, retention state, and tombstone state.

**Bounded result contract**: The declared maximum number of candidates a read may return, the token budget those candidates may occupy, and the provenance fields each returned record must carry.

**Consistency token**: An opaque marker returned by a commit and accepted by a read, allowing a caller to require that the read observes at least the state that commit produced.

**Derivative watermark**: The position in the canonical change sequence that a given derivative has applied. Comparing a watermark against a consistency token determines whether a derivative can satisfy a read.

**Tombstone**: A canonical record making a memory immediately ineligible for every read path, committed before any physical purge begins.

**Trust class**: The privilege level assigned to admitted content, determining where the content may appear in an assembled prompt and what it is permitted to influence.

**Terminal state**: A declared operation outcome that ends the operation: committed, rejected, quarantined, superseded, abstained, or degraded. An operation that ends in none of these is a defect.

### 1.2 Scope Boundary Against the Type-Specific Memory Guides

This guide owns the operation contract itself. It does not own any particular store, any particular memory type, or any policy that depends on what the record means.

**What this guide owns**: The shape of a write request and its response, the five admission gates and their ordering, the read contract and the bounded result it produces, identity and version semantics, transaction boundaries across a canonical store and its derivatives, the injection boundary applying to all admitted content, the terminal-state vocabulary, and the instrumentation that makes both paths measurable.

**What the type-specific guides own**: Episode boundaries and trajectory capture; claim modelling and identity resolution for semantic records; the residency and eviction rules of a bounded working state; placement and movement across storage tiers; the evidence thresholds that promote a raw episode into durable memory; the schema design of structured records and the chunking of unstructured ones; the salience model that scores what deserves context space. Those guides state policy in terms of what a record is; this guide states mechanism in terms of what an operation does.

**How the boundary is enforced in practice**: A type-specific guide supplies the predicate; this guide supplies the gate that evaluates it. Where a consolidation policy declares that an episode is promotable after 3 independent corroborations, this guide specifies where that predicate is evaluated (the admission gate), what happens when it fails (a typed rejection with a reason code), and how the decision is logged. No numeric threshold from a sibling guide is restated here, and no operation mechanism is delegated to a sibling guide.

**Composition rule**: An agent implementing any memory type loads that type's guide for policy and this guide for mechanism. Where the two appear to conflict, the operation mechanism holds, because a policy that cannot be evaluated inside a gate cannot be enforced at all.

### 1.3 The Execution-Tier Partition

Every unit of work in a memory operation belongs to exactly one tier. Assignment is not a stylistic preference; it determines what can be audited, what can be replayed, and what can be attacked.

**Deterministic tier**: Software, queries, schema validators, and policy engines own authorization evaluation, schema validation, identifier assignment, uniqueness and duplicate-constraint enforcement, index maintenance and watermark tracking, transaction boundaries, tombstone enforcement, retry classification, the bounded result contract, and telemetry emission. These require exactness, reproducibility, and auditability that model inference does not supply. A deterministic decision must produce the same outcome on replay of the same inputs; where it does not, the decision is a defect rather than a judgement.

**Model tier**: Model inference owns extraction of candidate records from unstructured input, query rewriting and decomposition, and relevance judgement within a candidate set that the deterministic tier has already filtered for eligibility. These require open-vocabulary understanding no deterministic rule covers. The model tier produces proposals and orderings; it never produces authority.

**Hybrid tier**: Candidate admission and result ranking are hybrid. The model proposes a candidate record or an ordering; deterministic validators normalize, authorize, deduplicate, check version preconditions, and commit. Retrieval is hybrid in the opposite direction: software retrieves an eligible set, and a model adjudicates relevance within it.

**Authority on disagreement**: The deterministic tier holds authority in every disagreement, without exception. Where a model proposes a record that fails schema validation, the record is rejected and the proposal is logged. Where a model ranks an ineligible record first, the record is absent from the set the model saw and the ranking is unaffected. Where a model asserts that a record should be retained past its retention class, the retention class governs.

**The prohibited delegations**: The model never decides eligibility and never decides authorization. It is never given a set from which it must exclude records it should not have seen, because a filter applied after retrieval has already leaked. It never selects a tenant, never widens a namespace, never overrides a tombstone, and never sets its own trust class. A deployment in which any of these decisions reaches the model tier has no enforceable memory policy, regardless of how the model behaves in testing.

### 1.4 The Ungated Write as the Origin of Memory Corruption

An ungated write is the single largest source of memory corruption, because a store that accepts anything eventually retrieves anything. Corruption entering through the write path is durable, is retrieved later as though it were established, and is retrieved most often by the read path that has the least context in which to detect it.

**Why the write path is the correct place to spend**: A defect admitted once is read many times. Rejecting a bad candidate costs one gate evaluation; retrieving it costs a gate evaluation on every read, a share of every context window it enters, and every downstream decision it influences. Read-side filtering cannot recover what write-side gating declined to prevent, because the read path does not know which of two contradictory records was the fabricated one.

**The four corruption classes an ungated write admits**: Unauthorized persistence, in which a principal writes into a scope it may not write; fabricated content, in which a model-inferred value enters the store labelled as observation; duplicate inflation, in which repeated copies of one occurrence masquerade as independent corroboration; and self-poisoning, in which an agent writes an inference, retrieves it later as evidence, and treats that retrieval as confirmation for a further write.

**Circular provenance is prohibited**: A record whose only supporting evidence is another record produced by the same agent in the same lineage does not count as corroborated. Corroboration requires at least 2 independent source identifiers whose lineages do not intersect. Occurrence count and independent source count are stored as separate fields precisely so that repetition cannot be read as agreement.

**The measurable consequence**: Where admission gating is absent or ineffective, write precision falls and every downstream retrieval metric degrades without naming its cause. Instrumenting the gate rejection rate, as specified in Phase 6, makes this failure visible before it becomes a retrieval quality investigation.

***

## II. Operational Framework: Gated Writes and Bounded Reads Over a Canonical Memory Store

The framework assumes a canonical store exists and is authoritative, and that at least one derivative may lag behind it. Phases 1 through 3 run in order for any deployment. Phase 4 governs every commit and every read once Phases 2 and 3 are live. Phase 5 applies to all content admitted in Phase 2 and all content returned in Phase 3. Phase 6 runs alongside the whole framework and completes before any configuration is promoted.

### Phase 1: Operation Contract Declaration

**Objective**: Fix identity, authorization, consistency, terminal states, and budgets before any record is written or read, so that every later decision is evaluated against a declared contract rather than against an implementation detail.

#### Step 1.1: Declare Identity, Idempotency, and Version Semantics

**Required Actions**:

- Define four identifier levels and their scopes: an operation identifier for one logical requested effect, an attempt identifier for one transport or worker attempt, a record identifier for the continuing logical memory, and a version identifier for one immutable serialization.
- Require a tenant-scoped idempotency key on every write request, and set a key retention window covering at least the maximum client retry window, the queue retention window, and the replay window, with 7 days as the deployment default.
- Declare the effective operation vocabulary as exactly four values: add, update, delete, and no-op, and define the condition under which each is the correct effective operation.
- Choose append semantics or versioned-current-projection semantics for every memory type, and prohibit in-place overwrite for all of them.
- Define the version precondition every mutation must carry, expressed as an expected parent version identifier, and require that a mismatch returns a conflict carrying the actual current version rather than committing.

**Required Outputs**:

- An identifier specification naming all 4 levels, their scopes, and their generation rules.
- An idempotency policy stating key scope, request-hash comparison rule, retention window, and conflict behaviour.
- An operation vocabulary of 4 effective operations with a decision rule per value.
- A per-memory-type semantics record naming append or versioned-current projection and the version precondition.

**Quality Checkpoints**:

- Every write request carries an idempotency key; a request without one is rejected before any gate runs.
- A repeat of one idempotency key with an equivalent request hash returns the original committed result and creates 0 additional versions.
- No memory type is configured for in-place overwrite, since overwrite destroys provenance, correction history, and point-in-time reconstruction.
- Every mutation path carries a version precondition; a path without one is a release blocker.

***

#### Step 1.2: Declare the Authorization and Consistency Envelope

**Required Actions**:

- Enumerate tenants, principals, purposes, namespaces, sensitivity classes, and retention classes, and bind each to explicit write grants and read grants.
- Evaluate authorization twice: once at write time to prevent unauthorized persistence, and once at read time because grants, purpose, consent, and sensitivity change after a record is written.
- Declare the supported consistency modes as exactly four: eventual, bounded-staleness with a numeric bound, read-your-writes through a supplied consistency token, and point-in-time snapshot.
- Set a freshness objective per derivative class, using p95 index lag no more than 5 seconds and p99 no more than 30 seconds as deployment defaults, and require that a bounded-staleness read whose watermark exceeds the requested bound fails rather than returns.
- Declare fail-closed behaviour for authorization, tombstone checks, and deletion propagation whenever the policy decision point is unavailable.

**Required Outputs**:

- An authorization matrix binding principals and purposes to write and read grants per namespace and sensitivity class.
- A consistency mode specification naming all 4 modes and the caller-facing parameter that selects each.
- A freshness objective per derivative class with p95 and p99 numeric bounds.
- A fail-closed list naming every check that denies rather than permits on dependency failure.

**Quality Checkpoints**:

- Authorization is evaluated at both write and read; a deployment evaluating it once is blocked from release.
- Every consistency mode has an implementation and a test; an advertised mode without a test is removed from the contract.
- Every derivative class carries a numeric freshness objective; a derivative without one cannot serve a bounded-staleness read.
- Policy-engine unavailability denies access on 100 percent of authorization, tombstone, and deletion checks.

***

#### Step 1.3: Declare Terminal States, Result Bounds, and Per-Operation Budgets

**Required Actions**:

- Declare the terminal-state vocabulary as exactly six values: committed, rejected, quarantined, superseded, abstained, and degraded, and require every operation to end in exactly one.
- Set the bounded result contract as numeric caps: no more than 200 candidates retrieved before eligibility filtering, no more than 50 surviving eligibility, no more than 20 entering rerank, and no more than 10 selected into an assembled context, with selection additionally capped by a token budget of no more than 40 percent of the available context window.
- Set the bounded retry contract as no more than 3 attempts for retryable transient failures within a total attempt age of 15 minutes, and 0 retries for schema, authorization, and request-hash conflict failures.
- Allocate a per-operation latency budget across authorization, validation, canonical commit, and response for writes, and across authorization, query planning, candidate retrieval, ranking, and assembly for reads, retaining at least 20 percent of the deadline as tail contingency.
- Set the confidence floor for durable admission at 0.60 calibrated confidence for ordinary records and 0.85 for records in the highest sensitivity or authority class.

**Required Outputs**:

- A terminal-state vocabulary of 6 values with a reason-code list attached to each.
- A bounded result contract stating all 4 numeric caps and the token budget share.
- A bounded retry contract stating attempt count, total age ceiling, and the non-retryable failure classes.
- A per-operation budget allocation for the write path and the read path with a stated contingency share.
- A confidence floor with 2 declared tiers.

**Quality Checkpoints**:

- Every operation terminates in exactly 1 of the 6 declared states; an operation ending outside the vocabulary halts and is escalated.
- Result contract caps are enforced by the retrieval service rather than by the caller; a caller-supplied limit above a cap is clamped and logged.
- No failure class is retried without a bound; an unbounded retry path is a release blocker.
- The confidence floor is a numeric comparison against a calibrated score, not a qualitative judgement.

***

### Phase 2: The Gated Write Path

**Objective**: Convert an untrusted observation into an authorized, canonical, versioned record by passing it through five deterministic gates, so that nothing reaches durable storage that the store cannot later account for.

#### Step 2.1: Capture the Source and Generate Candidates Without Granting Authority

**Required Actions**:

- Capture the source with an immutable source identifier, a content hash, a capture timestamp, and a source class drawn from the closed vocabulary of quoted source, direct observation, tool output, model inference, and approved procedure.
- Treat a successful tool response as establishing what the tool returned, not that the represented world fact is true, and record the distinction in the source class rather than in prose.
- Constrain the extraction model to the allowed memory types and require an explicit empty result to be expressible, so that the model is not forced to invent a candidate.
- Require every candidate to carry supporting spans into the captured source, a subject, a value, a modality, a negation marker, a temporal expression, and a stated confidence method.
- Record the extractor model identifier, prompt version, and schema revision with every candidate, so that a later regression can be attributed to the component that changed.
- Run candidate generation synchronously only where the next turn requires the record; otherwise enqueue it and return an accepted rather than committed status.

**Required Outputs**:

- A source capture record with identifier, content hash, capture timestamp, and source class.
- A candidate set with 0 or more entries, each carrying supporting spans and the 7 required content fields.
- An extractor provenance record naming model, prompt version, and schema revision.
- A synchronicity decision with a stated reason for any synchronous generation.

**Quality Checkpoints**:

- Every candidate traces to at least 1 supporting span in a captured source; a candidate without a span is rejected at Gate 3.
- The empty result is produced where no candidate exists, and empty results are logged rather than discarded.
- Source class is assigned by the deterministic tier from the capture channel, never by the extraction model.
- No response returns the word committed for a candidate that has only been enqueued.

***

#### Step 2.2: Normalize, Canonicalize, and Detect Duplicates in Two Passes

**Required Actions**:

- Normalize Unicode form, whitespace, locale, units, timestamps, identifiers, and entity aliases, and normalize casing only where the change is semantically safe.
- Preserve the original bytes or a protected reference to them, because canonicalization is lossy and forensic recovery depends on the original.
- Prohibit canonicalization from erasing negation, uncertainty, speaker attribution, temporal scope, or formatting that carries meaning.
- Produce a canonical serialization and a content hash whose scope includes tenant, memory type, subject, validity bucket, and schema version wherever meaning depends on them.
- Run the first duplicate pass as a deterministic unique constraint on the scoped content hash, rejecting exact duplicates as a no-op rather than as a failure.
- Run the second duplicate pass over lexical fingerprints or embeddings, and classify each near match as duplicate, corroboration, refinement, contradiction, or independent occurrence, never merging on similarity alone.
- Record cluster identifier, cluster version, similarity features, threshold version, and canonical member for every near-duplicate decision, so that any merge is reversible.
- Store occurrence count and independent source count as separate fields, so that repeated copies cannot be read as corroboration.

**Required Outputs**:

- A canonical serialization with a scoped content hash and a preserved original reference.
- An exact-duplicate verdict from the unique constraint.
- A near-duplicate classification from the closed vocabulary of 5 values, with features and thresholds recorded.
- A reversible cluster record with a named canonical member.

**Quality Checkpoints**:

- Negation, uncertainty, speaker, and temporal scope survive canonicalization in 100 percent of sampled records.
- Exact duplicates are rejected by a database constraint rather than by application logic, so a concurrent retry cannot bypass the check.
- Near-duplicate merge decisions achieve pair precision of at least 0.95 on a labelled sample of at least 200 pairs; below that threshold, automatic merging is disabled and near matches are recorded as independent occurrences.
- Occurrence count and independent source count are populated separately on every clustered record.

***

#### Step 2.3: Apply the Five Admission Gates and Bound the Rejection Path

**Required Actions**:

- Evaluate the five gates in this fixed order and stop at the first failure: authorization, schema validation, provenance completeness, duplicate detection, and the confidence floor.
- Evaluate the authorization gate against the principal, tenant, subject, namespace, purpose, and sensitivity class before any durable publication, and deny rather than quarantine where the principal has no write grant at all.
- Evaluate the schema gate over syntax, types, required fields, ranges, allowed relations, temporal interval validity, and referential integrity, rejecting on the first violation with the violated constraint named.
- Evaluate the provenance gate as a completeness check over 4 mandatory fields: source identifier, source class, capture timestamp, and extraction method, rejecting a candidate missing any one of them.
- Evaluate the confidence gate as a numeric comparison against the floor declared in Step 1.3, and require a deterministic override rule rather than a model judgement where a low-confidence record must nonetheless be retained.
- Assign every rejection a terminal state and a typed reason code, and route rejections to one of three outcomes: discard with a logged reason, quarantine with a payload reference and a named review owner, or return to the caller as a typed error the agent can act on.
- Bound the retry on a rejected write to 0 attempts for schema, authorization, provenance, and duplicate rejections, since re-submitting an unchanged request cannot change a deterministic verdict, and to at most 3 attempts within 15 minutes for transient dependency failures.
- Halt autonomous ingestion where the gate rejection rate exceeds 30 percent over 1,000 consecutive write attempts, and open an investigation where it falls below 2 percent, since a gate that rejects almost nothing is probably not evaluating.

**Admission Gate Specification**:

| Gate | Tier | Rejection is retryable | Rejected write becomes |
| :-- | :-- | :-- | :-- |
| Authorization | Deterministic | No | Denied and logged; quarantined only where policy requires forensic retention |
| Schema validation | Deterministic | No | Rejected with the violated constraint named |
| Provenance completeness | Deterministic | No | Rejected; returned to extraction with the missing field named |
| Duplicate detection | Deterministic | No | No-op referencing the existing record version |
| Confidence floor | Hybrid, deterministic comparison over a model-supplied score | No | Rejected, or quarantined for review where the memory type declares review |
| Transient dependency failure | Deterministic | Yes, at most 3 attempts within 15 minutes | Quarantined after the third attempt with an owner assigned |

**Required Outputs**:

- A gate evaluation record naming the gate reached, the verdict, and the reason code.
- A terminal state for every rejected candidate, drawn from rejected, quarantined, or no-op.
- A quarantine entry with payload reference, failure history, review owner, and replay authorization for every quarantined candidate.
- A rolling gate rejection rate computed over the last 1,000 write attempts.

**Quality Checkpoints**:

- Gates evaluate in the declared order, and no gate is skipped when an earlier gate passes.
- 100 percent of rejected candidates carry a typed reason code; an untyped rejection is a defect that blocks release.
- 0 rejected candidates are silently dropped; every rejection is either logged with its reason or quarantined with an owner.
- Deterministic rejections are retried 0 times; a retry of an unchanged deterministic rejection indicates a defective retry classifier.
- The rolling rejection rate stays within 2 percent to 30 percent; a breach in either direction halts autonomous ingestion pending review.

***

### Phase 3: The Bounded Read Path

**Objective**: Convert a scoped question into a bounded set of eligible records carrying provenance, so that a read returns evidence a caller can audit rather than an unbounded dump a caller must sift.

#### Step 3.1: Establish the Read Contract and Construct the Query

**Required Actions**:

- Authenticate the caller and bind tenant, principal, purpose, allowed namespaces, allowed memory types, requested valid time, maximum staleness, consistency mode, token budget, deadline, and cost budget before any candidate is retrieved.
- Preserve the original query verbatim alongside every rewrite, so that a retrieval failure can be attributed to the query or to the rewrite.
- Resolve relative time expressions, entity aliases, exact identifiers, and language against declared task state rather than against model recollection.
- Decompose a multi-part question into separate queries where one query would mix entities, time ranges, or predicates, and cap decomposition at 4 subqueries.
- Generate rewrites only where a measured recall gap justifies them, cap rewrite count at 3, and deduplicate rewrites before dispatch.
- Treat any generated hypothetical or answer-shaped text used for query expansion as a query artifact only, never as evidence, and exclude it from every returned result.
- Classify the query as exact-identifier, lexical, semantic, or structured, and route it to the routes that class requires rather than to every available route.

**Required Outputs**:

- A read contract record carrying all 11 bound parameters.
- An original query record plus at most 3 deduplicated rewrites and at most 4 subqueries.
- A query classification with the routes selected and the routes declined, each with a reason.
- A declared exclusion of expansion artifacts from the result set.

**Quality Checkpoints**:

- Every read carries a purpose and a consistency mode; a read missing either is rejected before retrieval.
- The original query is retained for 100 percent of reads that used a rewrite.
- Expansion artifacts appear in 0 returned results, since a generated hypothetical can carry fabricated detail.
- Route selection is deterministic given the query class; a route added without a measured recall gap is removed.

***

#### Step 3.2: Filter Eligibility and Authorization Before Ranking

**Required Actions**:

- Apply tenant, subject, purpose, consent, region, sensitivity, namespace, validity interval, retention state, trust class, quarantine state, and tombstone predicates before any semantic ranking runs.
- Search a physically scoped partition where the retrieval engine cannot guarantee filter correctness, and recheck every surviving candidate against the full predicate set immediately before release.
- Prohibit the pattern of retrieving globally and redacting afterwards, since a candidate that reached the ranking stage has already left its authorization boundary.
- Exclude any record whose eligibility cannot be established, rather than including it with a warning attached, and record the exclusion with its undetermined predicate.
- Recheck tombstone state at the final gateway on every serving path, including cache hits, so that a lagging derivative cannot leak a deleted record.
- Count candidates before and after eligibility filtering, and record both counts on the read event.

**Eligibility Predicate Ordering**:

| Predicate class | Evaluated against | Failure outcome |
| :-- | :-- | :-- |
| Tenant and namespace scope | Physical partition or index namespace | Candidate never retrieved |
| Principal and purpose grant | Policy decision point | Candidate excluded; read event records a policy exclusion |
| Consent, residency, sensitivity | Record labels plus policy version | Candidate excluded; existence not disclosed |
| Validity interval and retention | Record valid-time and retention class | Candidate excluded as expired or not yet valid |
| Trust class and quarantine state | Record trust label | Candidate excluded or demoted per the read contract |
| Tombstone state | Canonical tombstone table at the gateway | Candidate excluded; a leak is a severity-one incident |
| Undetermined eligibility | Any predicate returning unknown | Candidate excluded, never included with a warning |

**Required Outputs**:

- An eligible candidate set of no more than 50 records, each having passed all 7 predicate classes.
- A pre-filter and post-filter candidate count on the read event.
- An exclusion record naming the predicate that removed each excluded candidate.
- A gateway tombstone recheck result for every candidate on every serving path.

**Quality Checkpoints**:

- 100 percent of eligibility predicates are evaluated before the first ranking operation.
- 0 candidates reach the model tier that failed any eligibility predicate, since post-retrieval redaction is not containment.
- A record with an undetermined predicate is excluded in 100 percent of cases; inclusion with a warning is prohibited.
- Deleted-content leakage measured across all tested serving paths is 0; any non-zero value halts serving.

***

#### Step 3.3: Rank, Bound, and Return With Provenance Attached

**Required Actions**:

- Rank within the eligible set only, using rank-based fusion across routes rather than raw score averaging, since scores from different retrievers are not comparable.
- Apply reranking only where first-stage recall is adequate and precision is inadequate, bound the rerank input to at most 20 candidates, and record the reranker version and per-candidate output.
- Keep relevance, lexical match, semantic match, temporal fit, freshness, importance, source authority, confidence, and realized usefulness as separate recorded features, and permit a single scalar for sort order only.
- Apply diversity after relevance: cluster near duplicates, cap results per source, per episode, per entity, and per time window, and preserve contradictions rather than collapsing them.
- Select the final set against the token budget rather than against a fixed count alone, reserving capacity for system instructions, task state, conflicts, and the answer.
- Attach to every returned record its record identifier, version identifier, selected span, source reference, source class, valid time, transaction time, trust and sensitivity labels, freshness, deletion state, and conflict links.
- Surface unresolved conflicts together rather than allowing ranking to select one silently, and mark the conflict as unresolved rather than resolving it in the ranker.
- Abstain where no eligible record passes threshold, where a required authoritative source is missing, where staleness exceeds the requested bound, where a conflict cannot be resolved, or where the budget expires before minimum evidence is assembled.
- Return a typed degradation naming which routes failed and whether the remaining result satisfies the contract, rather than returning a silently partial result.

**Required Outputs**:

- A returned set of no more than 10 records within the declared token budget, ordered deterministically.
- A provenance block of 11 fields attached to every returned record.
- A conflict block listing unresolved conflicts with their competing version identifiers.
- An abstention or degradation record with a typed reason code where the read did not return a full result.

**Quality Checkpoints**:

- The returned set never exceeds the declared cap; an unbounded return is a contract violation that halts serving.
- 100 percent of returned records carry all 11 provenance fields; a record missing any field is withheld rather than returned bare.
- Ranking never removes a record for an eligibility reason, since eligibility was settled before ranking began.
- An empty eligible set produces an abstention with a reason code, never a widened scope or a relaxed predicate.
- Every degraded read names the failed routes; a degraded read presented as a normal read is a defect.

***

### Phase 4: Atomicity and Cross-Store Failure Handling

**Objective**: Make the operation pair atomic where it must be and explicitly eventual where it cannot be, so that a caller knows exactly what it will observe after its own write and what a partial success left behind.

#### Step 4.1: Commit Canonical State and the Derivative Outbox in One Transaction

**Required Actions**:

- Commit in one database transaction the idempotency claim, the immutable record version, the current-pointer or tombstone change, the lineage links, the audit decision, and one outbox event per required derivative.
- Acknowledge success only after that transaction commits, and never after a queue publish alone, since a queue publish that succeeds while the canonical write fails produces a searchable record with no authority behind it.
- Store the original response against the idempotency key inside the same transaction, so that a retry returns the original result rather than recomputing one.
- Treat the same idempotency key carrying a different request hash as a conflict returning the original result and a conflict marker, never as a new write.
- Prohibit dual writes to a database and a queue outside a transaction; where a required effect cannot join the transaction, model it as a saga step with a recorded compensation rather than as an untracked side effect.
- Require business-level uniqueness constraints on any externally visible effect, since transport-level idempotency guarantees delivery semantics and not business semantics.
- Target exactly-once business effect rather than exactly-once delivery, and state in the operation contract that at-least-once delivery with idempotent consumers is the achievable guarantee.

**Required Outputs**:

- A single-transaction commit record listing all 6 committed artifacts.
- A stored idempotency response keyed by the idempotency key with its request hash.
- A saga record for every effect that could not join the transaction, naming its compensation and its reversibility.
- A business uniqueness constraint per externally visible effect.

**Quality Checkpoints**:

- Canonical version, pointer change, idempotency claim, and outbox rows commit together in 1 transaction; a deployment splitting them is blocked from release.
- Acknowledgement follows canonical commit in 100 percent of write responses.
- Replaying an identical request before, during, and after response loss produces exactly 1 logical effect and a stable returned result.
- Orphaned derivative rate, meaning derivatives with no committed canonical version, is 0.

***

#### Step 4.2: Guarantee Read-Your-Writes and Bound Derivative Lag

**Required Actions**:

- Guarantee that a canonical key lookup observes a committed version immediately upon acknowledgement, with no lag, since the canonical store is the same store that acknowledged.
- State explicitly that a derivative-backed read carries no such guarantee, and that semantic search may not observe a committed version until the derivative watermark reaches the commit's consistency token.
- Satisfy a read-your-writes request by one of three deterministic mechanisms: merging committed but unindexed versions from canonical state into the result, querying canonical state by consistency token, or waiting on the derivative watermark up to a declared bound.
- Fail a bounded-staleness read whose derivative watermark exceeds the requested bound rather than returning a stale result labelled fresh.
- Publish derivatives from the committed outbox with per-key ordering by tenant and record identity, and never assert a global order the system does not maintain.
- Apply the highest observed version per key when events arrive out of order, retaining the superseded event for audit rather than applying it to the current projection.
- Append a late-arriving event with its real valid time rather than rewriting what was previously known, since a late arrival changes the record's history and not its past visibility.
- Acknowledge queue work only after both the derivative effect and the worker idempotency marker commit.

**Consistency Guarantee Matrix**:

| Read mode | Store consulted | Guarantee after the caller's own commit | Failure behaviour |
| :-- | :-- | :-- | :-- |
| Canonical key lookup | Canonical store | Immediate visibility | Fails closed; no derivative substitute |
| Read-your-writes | Canonical overlay plus derivative | Immediate visibility of the caller's own commit | Falls back to canonical-only result |
| Bounded staleness | Derivative with watermark check | Visibility once the watermark reaches the token | Fails the read rather than returning stale |
| Eventual | Derivative | No guarantee; lag is reported | Returns with a freshness label |
| Point-in-time snapshot | Canonical versions at a recorded watermark | Reproduces historical visibility | Falls back to canonical versions when an index cannot reproduce it |

**Boundary against distributed memory design**: The matrix above states what each mode guarantees to a caller and how the read behaves when the guarantee cannot be met. It does not cover how a consistency model is chosen, how replicas are placed, or how a session guarantee survives routing across failure domains. Those belong to `advanced_task_guides/memory-management/guide_DistributedMemoryArchitecture.md`, which carries the deeper treatment of consistency models, the four session guarantees including read-your-writes, replication topology, and the violation taxonomy that names a read-your-own-writes violation as a distinct failure event. This guide owns the per-operation commit and read contract within one canonical system; that guide owns the model under which the contract is offered across many. Where a deployment spans replicas or regions, the consistency mode is selected there and enforced here.

**Required Outputs**:

- A consistency token returned with every commit and accepted by every read.
- A derivative watermark per derivative store, updated on every applied event.
- A read-your-writes mechanism selection with a declared wait bound.
- A freshness label on every result served from a derivative.

**Quality Checkpoints**:

- A canonical key lookup observes the caller's own commit in 100 percent of tested cases.
- A bounded-staleness read outside its bound fails in 100 percent of tested cases and returns 0 stale results labelled fresh.
- Per-key ordering holds across delivery retries and duplicates; a global ordering claim appears nowhere in the contract.
- A late event never rewrites an earlier projection; it appends with its own valid time.

***

#### Step 4.3: Reconcile Partial Success and Contain Poison Operations

**Required Actions**:

- Classify a partial success by which store succeeded: a canonical commit with a failed derivative is a valid record with degraded retrieval, while a derivative write with no canonical commit is an orphan requiring immediate removal.
- Retry a failed derivative rather than rolling back a valid canonical commit, since the canonical record is authoritative and the derivative is rebuildable.
- Remove any searchable derivative whose canonical version does not exist, and run reconciliation on a schedule that bounds orphan lifetime to no more than 15 minutes.
- Classify every failure into one of six classes: retryable transient, retryable after a rate-limit interval, deterministic validation, authorization, conflict, and poison, and attach a distinct handling path to each.
- Apply bounded exponential backoff with jitter, preserve the next attempt time, and enforce both an attempt ceiling of 3 and a total attempt age ceiling of 15 minutes.
- Move an operation to quarantine after the attempt ceiling with a payload reference, failure history, named owner, and explicit replay authorization, and never drop it silently.
- Enforce bounded queues, per-tenant quotas, batch and concurrency limits, and circuit breakers, shedding optional enrichment before canonical writes when backpressure engages.
- Refuse to accept a write as committed when the canonical store is unavailable; accept an explicitly pending request onto a durable edge queue only where its authorization and retention risk are acceptable, and label it pending rather than committed.
- Commit a tombstone before any physical purge, publish high-priority invalidations to every derivative and cache, then purge content, vectors, lexical postings, summaries, projections, and permitted backups, and verify by probing every serving path.

**Required Outputs**:

- A failure classification record with 1 of 6 classes per failure.
- A reconciliation report naming orphaned derivatives, their age, and their removal.
- A quarantine entry with owner and replay authorization for every operation exceeding its attempt ceiling.
- A deletion lineage record naming every derivative target, its invalidation time, its purge status, and its verification method.

**Quality Checkpoints**:

- A failed derivative never triggers rollback of a valid canonical commit.
- Orphan lifetime does not exceed 15 minutes; a longer-lived orphan escalates as a data-integrity incident.
- 0 operations are dropped without a terminal state; every exhausted retry ends in quarantine with an owner.
- The store never reports committed for a write held on an edge queue; pending and committed are distinct terminal-facing states.
- Post-deletion probes across every serving path return 0 residual hits before the deletion is recorded as complete.

***

### Phase 5: The Injection and Trust Boundary

**Objective**: Establish that content admitted to memory is data for its whole lifetime, so that a record written today cannot act as an instruction when it is retrieved weeks later.

#### Step 5.1: Admit Content as Data and Assign a Trust Class

**Required Actions**:

- Assign every admitted record a trust class from a closed vocabulary at admission time, derived deterministically from the source class and the capture channel, never from the content itself.
- Prohibit content from setting or raising its own trust class, its own retention class, its own sensitivity label, or its own authority, since a record that can promote itself has no boundary at all.
- Detect and neutralize invisible control characters, active markup, embedded delimiters, and instruction-shaped passages at admission, and record the detection verdict as a field rather than acting on it as a permission.
- Preserve a protected original alongside any sanitized form, because sanitization destroys the evidence a later investigation needs.
- Cap the authority of any model-inferred record until it is corroborated by at least 2 independent source identifiers whose lineages do not intersect.
- Detect secrets, personal data, regulated categories, and cross-tenant identifiers before durable publication, and redact, tokenize, quarantine, or reject according to the declared policy.
- Propagate the source record's sensitivity and trust class to every derivative, since a summary of a sensitive record is a sensitive record unless policy proves otherwise.

**Required Outputs**:

- A trust class assignment per admitted record, with the deterministic rule that produced it.
- A detection verdict record naming what was found, what was neutralized, and where the protected original resides.
- An authority cap on every model-inferred record with its corroboration requirement.
- A sensitivity and label inheritance record for every derivative.

**Quality Checkpoints**:

- Trust class is assigned by the deterministic tier in 100 percent of admissions; a content-derived trust class is a release blocker.
- 0 records raise their own trust, retention, sensitivity, or authority.
- A protected original exists for every sanitized record; sanitization that destroys the original is a defect.
- Model-inferred records reach full authority only after 2 independent corroborating sources are recorded.

***

#### Step 5.2: Isolate Retrieved Content and Re-Authorize Every Downstream Effect

**Required Actions**:

- Place retrieved memory content into the model's input at the lowest available privilege, as delimited data in a user-role or tool-role position, and never in a system or developer position.
- Name the isolation mechanism explicitly in the deployment contract: a fixed delimiter convention, a distinct message role, and a standing instruction in the trusted prefix stating that delimited memory content is evidence and carries no authority.
- Keep stable trusted instructions, policy, and schemas ahead of any retrieved content in the assembled context, and append volatile memory deterministically after them.
- Retain the trust class label alongside the content in the assembled context, so that the reader can distinguish an approved procedure from a quoted third-party document.
- Re-authorize every tool call, credential use, permission change, and approval requirement against the calling principal's own grants after a read, and never against anything a retrieved record asserts.
- Treat detection failure as expected rather than exceptional: an instruction-shaped passage that evades detection must still be inert, because it sits in a data position with no authority attached.
- Prohibit memory content from altering system policy, tool allowlists, credentials, confirmation rules, retention, or its own labels, and enforce the prohibition in the tool-authorization layer rather than in a prompt instruction.
- Prohibit circular provenance at read time as well as at write time: a retrieval of the agent's own earlier inference does not satisfy a corroboration requirement for a new write.

**Isolation Boundary Rules**:

| Assembled context region | Permitted content | Authority |
| :-- | :-- | :-- |
| Trusted prefix | System policy, schemas, tool contracts, standing isolation instruction | Full; sets the rules |
| Task state | Current task parameters supplied by the calling system | Scoped to the task |
| Retrieved memory | Delimited records with trust class and provenance | None; evidence only |
| Tool output within the turn | Delimited results with source class | None; evidence only |
| Model output | Answer plus cited record identifiers | None until validated |

**Required Outputs**:

- A named isolation mechanism comprising a delimiter convention, a message-role placement rule, and a standing trusted instruction.
- An assembled context with retrieved content confined to the retrieved-memory region.
- A re-authorization record per tool call showing the grant it was evaluated against.
- A citation requirement binding the model to cite record identifiers where the task requires attribution.

**Quality Checkpoints**:

- Retrieved memory appears in a system or developer position in 0 assembled contexts.
- Every tool call following a read is authorized against the principal's grants; 0 tool calls are authorized by record content.
- Instruction-shaped content that evades detection produces 0 privilege changes in adversarial testing, since detection is a signal and not a control.
- 0 retrieved records alter policy, allowlists, credentials, confirmation rules, or their own labels.
- A corroboration claim resting on the agent's own prior inference is rejected in 100 percent of tested cases.

***

### Phase 6: Instrumentation of Both Paths

**Objective**: Emit an event record for every write attempt and every read request that makes each declared threshold computable, so that gate quality, result bounds, consistency, and containment are measured rather than assumed.

#### Step 6.1: Emit the Write-Path Event Record

**Required Actions**:

- Emit one event per write attempt and one per commit, carrying operation identifier, attempt identifier, tenant, pseudonymous principal, purpose, namespace, memory type, schema version, and policy version.
- Record the idempotency key hash, request hash, requested operation, effective operation, record identifier, committed version identifier, expected parent version, and actual parent version.
- Record the gate outcome per gate: gate reached, verdict, reason code, and the constraint or field that failed.
- Record provenance fields, source identifiers, source class, content hash, canonicalization version, valid-time interval, transaction time, sensitivity class, and retention class.
- Record duplicate decision fields, including cluster identifier, cluster version, similarity features, threshold version, decision value, and independent source count.
- Record commit fields, including commit sequence, canonical commit time, consistency token, outbox event identifiers, and acknowledgement time.
- Record extraction fields, including extractor model identifier, prompt version, candidate count, and the model-supplied confidence, and attach later adjudication labels covering usefulness, later use, correction within a window, and harm.
- Keep raw content, secrets, and unhashed identifiers out of general telemetry, substituting content references and keyed hashes.

**Required Outputs**:

- A write attempt event and a commit event per operation, with all required identity, gate, provenance, duplicate, and commit fields.
- A deferred adjudication record attaching usefulness and correction labels after the observation window closes.
- A redaction policy applied to 100 percent of telemetry fields carrying content.

**Quality Checkpoints**:

- 100 percent of write attempts emit an event, including rejections and no-ops; a missing event class blocks metric computation and halts promotion.
- Every event carries the operation identifier that links its attempts, so a retry is distinguishable from a distinct operation.
- 0 telemetry records carry raw content, secrets, or unhashed principal identifiers.
- Gate reason codes come from the closed vocabulary declared in Step 1.3.

***

#### Step 6.2: Emit the Read-Path Event Record

**Required Actions**:

- Emit one event per read request carrying read identifier, keyed query hash, query class, rewrite hashes, requested namespaces and memory types, consistency mode, consistency token, maximum staleness, deadline, and cost budget.
- Record candidate counts before and after eligibility filtering, the eligibility filter version, the routes used, retriever versions, index generations, and index watermarks.
- Record per candidate the record identifier, version identifier, route, rank within route, per-feature scores kept separately, validity status, tombstone check result, index staleness, and selected span.
- Record fusion and rerank fields, including fusion method and version, rank constant, fused rank, reranker model and revision, input count, ranks before and after, and rerank latency and cost.
- Record assembly fields, including token budget, selected and dropped candidate identifiers with drop reason codes, diversity cluster identifiers, source caps applied, conflict count, stale count, and each candidate's context position.
- Record abstention and degradation fields, including a reason code from the closed vocabulary and the failed route identifiers.
- Attach later outcome labels covering whether each returned record was used in the answer, cited, judged relevant, and whether the task succeeded.

**Required Outputs**:

- A read event per request with contract, filtering, route, and bound fields.
- A candidate record per returned and dropped candidate with per-feature scores and a drop reason.
- An assembly record with positions, conflicts, and budget consumption.
- A deferred outcome record attaching usefulness and citation-support labels.

**Quality Checkpoints**:

- 100 percent of reads emit an event, including abstentions and degraded reads.
- Per-feature scores are recorded separately; an event carrying only a fused scalar cannot support ablation and is a defect.
- Context position is recorded for every selected candidate, so position effects on evidence use are measurable.
- Every abstention carries a reason code from the closed vocabulary.

***

#### Step 6.3: Compute the Operation Metric Set and Gate Promotion

**Required Actions**:

- Compute write precision as adjudicated useful accepted writes over accepted writes, and write recall as adjudicated useful candidates accepted over all adjudicated useful candidates, reported by source, memory type, and sensitivity class.
- Compute the gate rejection rate per gate and in aggregate over a rolling window of 1,000 attempts, and alert on the 2 percent and 30 percent bounds.
- Compute duplicate pair precision and recall, false-merge severity, and duplicate rows per logical occurrence.
- Compute commit success, idempotency replay stability, outbox publication success, derivative application success, orphan rate, queue age, and index lag distributions at p50, p95, and p99.
- Compute retrieval recall and precision at the declared result bound, evidence coverage against version identifiers, context utilization, conflict surfacing rate, abstention precision, citation support, and deleted-content leakage.
- Compute latency and cost per successful operation rather than per API call, reporting p50, p95, and p99 rather than averages.
- Run replay regression on every change to a model, prompt, schema, policy, retriever, index generation, or gate threshold, using a frozen labelled operation corpus.
- Run chaos exercises that delay derivative publication, reorder and duplicate deliveries, pause one index, exhaust an embedding rate limit, corrupt a cache invalidation, fail the canonical store, and lose a response after commit.
- Block promotion of any configuration whose high-risk gates have not passed with stated confidence intervals, and whose rollback, replay, and deletion drills have not succeeded.

**Required Outputs**:

- A metric report covering write quality, duplicate quality, commit and consistency, retrieval quality, and cost and latency.
- A frozen labelled operation corpus with declared splits by principal, source, and time.
- A chaos exercise report naming each injected failure and the observed containment.
- A promotion decision record naming every gate and its measured value.

**Quality Checkpoints**:

- Every threshold declared in this guide has a computed metric behind it; a threshold without a metric is unenforceable and is removed or instrumented.
- Deleted-content leakage is 0 across all tested serving paths before any promotion.
- Replay regression runs on 100 percent of changes to the listed components; an unreplayed change blocks promotion.
- Reported latency and cost figures use p95 and p99; a report carrying only averages is rejected.

***

## III. Implementation Guidance for AI Agents

AI agents operating a memory data plane must follow systematic protocols ensuring that every write is gated, every read is bounded, every effect is idempotent, and every retrieved record remains data. The following guidance translates the operation pair into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Agent**: Owns the operation contract, the identifier specification, the consistency modes, the terminal-state vocabulary, and the numeric bounds. It alone may amend a bound, and every amendment is versioned and logged.
2. **Extraction Agent**: Proposes candidate records from unstructured input and proposes query rewrites. It operates entirely in the model tier, holds no authority, and its proposals are logged whether accepted or rejected.
3. **Admission Validator**: Evaluates the five gates in order, assigns identifiers, enforces uniqueness constraints, and returns a verdict with a typed reason code. It is deterministic and its verdicts must be reproducible on replay.
4. **Commit Coordinator**: Opens and closes the canonical transaction, writes the idempotency claim and the outbox rows, returns the consistency token, and acknowledges only after commit. It never acknowledges on a queue publish.
5. **Derivative Worker**: Consumes outbox events in per-key order, applies effects to lexical indexes, vector indexes, projections, summaries, and caches, advances watermarks, and acknowledges only after its idempotency marker commits.
6. **Retrieval Service**: Binds the read contract, applies eligibility predicates before ranking, enforces the result caps, attaches provenance, and issues abstentions. It alone may return a memory record to a caller.
7. **Instrumentation Agent**: Emits write-path and read-path events, enforces telemetry redaction, computes the metric set, and may withhold a promotion decision where an event class is missing.

**Trust Boundary**: Retrieved memory content is data at every point in this control plane. No component accepts an instruction, a permission, a label change, or a policy change originating in a memory record, and the tool-authorization layer enforces this independently of any prompt instruction.

**Workflow Execution Pattern**:

```
STATE: Write_Admission
INPUTS:
  1. Candidate record set from the Extraction Agent
  2. Operation contract and bounds from the Contract Agent
  3. Canonical current state for the target record identity
ACTIONS:
  1. Evaluate gate 1 authorization against principal, tenant, namespace, purpose
  2. Evaluate gate 2 schema over types, ranges, relations, temporal intervals
  3. Evaluate gate 3 provenance completeness over 4 mandatory fields
  4. Evaluate gate 4 duplicate detection, exact constraint then near-duplicate class
  5. Evaluate gate 5 confidence floor against the declared tier
  6. Assign identifiers and resolve the effective operation
VALIDATION:
  - gates_evaluated_in_declared_order == TRUE
  - rejection_reason_code IN closed_vocabulary
  - idempotency_key_present == TRUE
  - version_precondition_present == TRUE IF effective_operation IN {UPDATE, DELETE}
  - trust_class_source == DETERMINISTIC
TRANSITIONS:
  IF all_gates_pass THEN next_state = Canonical_Commit
  IF gate_failed AND failure_class == DETERMINISTIC
     THEN next_state = Typed_Rejection  (retry_budget = 0)
  IF gate_failed AND failure_class == TRANSIENT
     THEN next_state = Bounded_Retry    (max_attempts = 3, max_age_ms = 900000)
  IF retry_budget_exhausted THEN next_state = Quarantine_With_Owner
```

**Two-Phase Action Pattern**: Emit the intended effective operation with its gate verdicts, identifiers, and version precondition without committing it; confirm it against the validation block while no durable state has changed; commit it and record the operation event in the same transaction only after validation passes.

**Approval Gate**: Human authorization is required before any write into the highest sensitivity class, before any deletion whose lineage touches a backup or an export, before any relaxation of a gate threshold or a result bound, and before promoting a configuration whose gate rejection rate has moved by more than 10 percentage points against the prior release. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the operation contract, identifier specification, and bounds in durable state, since a memory data plane outlives any single context window.
- Carry the consistency token rather than the retrieved content across a context boundary, and re-read by token where the content is needed again.
- Bound the retrieval service's own context consumption against the declared token budget and count it toward the read's cost rather than treating it as free.
- Write a handoff record naming the pending operations, their terminal states, the outstanding derivative watermarks, and the open quarantine entries at every context boundary.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract Completeness (After Phase 1)**

- **Automated Check**: All 4 identifier levels defined; idempotency policy present with a retention window; all 4 consistency modes implemented and tested; all 6 terminal states defined with reason codes; all 4 result caps and both confidence tiers set.
- **Agent Action on Pass**: Proceed to write path implementation.
- **Agent Action on Failure**: Halt and return the missing contract element; no record is written against an incomplete contract.
- **Human Review Trigger**: Any memory type for which append or versioned-current semantics cannot be chosen, or any bound the deployment wishes to set outside the ranges in Step 1.3.

**Checkpoint 2: Gate Integrity (After Phase 2)**

- **Automated Check**: Gates evaluate in declared order on 100 percent of replayed corpus attempts; 100 percent of rejections carry a typed reason code; duplicate pair precision at least 0.95 on at least 200 labelled pairs; rolling rejection rate within 2 percent to 30 percent.
- **Agent Action on Pass**: Enable autonomous ingestion for the tested memory types only.
- **Agent Action on Failure**: Halt ingestion for the failing memory type and return the failing gate with its measured rate.
- **Human Review Trigger**: Rejection rate outside the 2 percent to 30 percent band, or pair precision below 0.95.

**Checkpoint 3: Read Bound Integrity (After Phase 3)**

- **Automated Check**: 0 candidates reach ranking having failed an eligibility predicate; result set within the declared cap on 100 percent of reads; all 11 provenance fields present on 100 percent of returned records; deleted-content leakage 0.
- **Agent Action on Pass**: Enable the read path for the tested query classes.
- **Agent Action on Failure**: Halt serving for the failing route and return the leaked or unbounded case.
- **Human Review Trigger**: Any deleted-content leak, or any read returning above the declared cap.

**Checkpoint 4: Atomicity and Consistency (After Phase 4)**

- **Automated Check**: Canonical version, pointer, idempotency claim, and outbox rows commit in 1 transaction; replay under response loss produces exactly 1 effect; orphan rate 0; bounded-staleness reads outside their bound fail on 100 percent of tested cases.
- **Agent Action on Pass**: Enable derivative publication and the read-your-writes mechanism.
- **Agent Action on Failure**: Halt commits and return the split-transaction path or the stale-result case.
- **Human Review Trigger**: Any acknowledged write with no committed canonical version, or any orphan surviving beyond 15 minutes.

**Checkpoint 5: Containment (After Phase 5)**

- **Automated Check**: 0 retrieved records placed in a system or developer position; 0 tool calls authorized by record content; 0 records raising their own trust, retention, sensitivity, or authority; adversarial suite produces 0 privilege changes.
- **Agent Action on Pass**: Enable autonomous tool use following reads.
- **Agent Action on Failure**: Suspend autonomous tool use following reads and return the escaped case with its record identifier.
- **Human Review Trigger**: Any privilege change traceable to memory content, regardless of whether detection flagged it.

**Checkpoint 6: Instrumentation Completeness (After Phase 6)**

- **Automated Check**: 100 percent of write attempts and read requests emit an event; every declared threshold has a computed metric; replay regression run on 100 percent of component changes; all chaos scenarios exercised.
- **Agent Action on Pass**: Release the metric report and permit promotion.
- **Agent Action on Failure**: Withhold the promotion decision and name the missing event class or uninstrumented threshold.
- **Human Review Trigger**: Any threshold without a metric, or any promotion requested on clean-condition results alone.

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

**Error Type 1: Ungated or Under-Gated Write**

- **Symptoms**: Gate rejection rate below 2 percent over a rolling window of 1,000 attempts; records present in the store lacking a source identifier or a source class; write precision falling while extraction quality is unchanged; contradictory records accumulating for one subject.
- **Diagnostic Steps**: Replay the frozen operation corpus and compare gate verdicts against labels; confirm each of the 5 gates is reached rather than short-circuited; check whether a gate is evaluating a field the extractor stopped populating.
- **Resolution Protocol**: Option A, restore the skipped gate and replay the affected window to identify admitted records that would now be rejected. Option B, quarantine the affected records rather than deleting them, since deletion destroys the evidence needed to size the corruption. Option C, where a gate cannot be restored without blocking legitimate traffic, tighten the confidence floor for the affected memory type and route its writes to review.
- **Escalation Trigger**: Any gate found to be unreachable in production halts autonomous ingestion immediately; this class is never resolved by retry, because retrying an ungated write admits it again.

**Error Type 2: Unbounded or Leaky Read**

- **Symptoms**: A read returning more than the declared cap; a deleted record surfacing on any serving path; a record returned without complete provenance; ranking observed to drop candidates for eligibility reasons.
- **Diagnostic Steps**: Compare the pre-filter and post-filter candidate counts on the read event; verify that the eligibility predicates ran before the first ranking operation; probe each serving path independently for the leaked record identifier.
- **Resolution Protocol**: Option A, move the failing predicate ahead of ranking and re-run the read regression. Option B, replace over-fetch-and-redact with a physically scoped partition search. Option C, where the retrieval engine cannot guarantee filter correctness, recheck every candidate against canonical state before release and accept the added latency.
- **Escalation Trigger**: Any deleted-content leak escalates as a severity-one incident and halts serving on the affected path; this class is never resolved by widening a cache invalidation window alone.

**Error Type 3: Partial Success Across Stores**

- **Symptoms**: A derivative carrying a record with no committed canonical version; an acknowledged write invisible to a canonical key lookup; index lag exceeding its p99 objective; outbox rows accumulating without publication.
- **Diagnostic Steps**: Reconcile derivative contents against canonical versions for the affected key range; verify that acknowledgement follows canonical commit rather than queue publish; inspect the derivative watermark against the commit sequence.
- **Resolution Protocol**: Option A, retry the failed derivative and leave the canonical commit intact, since the canonical record is authoritative. Option B, remove the orphaned derivative entry and record it as a data-integrity event. Option C, rebuild the derivative generation from a canonical snapshot, catch up its change stream, validate counts and deletions, then switch the alias atomically and retain the prior generation for rollback.
- **Escalation Trigger**: An orphan surviving beyond 15 minutes, or any acknowledged write with no canonical version, escalates immediately and blocks further commits on the affected path.

**Error Type 4: Idempotency and Duplicate Failure**

- **Symptoms**: Two versions committed for one idempotency key; duplicate rows per logical occurrence rising; independent source count rising in step with occurrence count; a retry returning a different result than the original attempt.
- **Diagnostic Steps**: Replay the same request before, during, and after simulated response loss; verify the uniqueness constraint is enforced by the database rather than by application logic; audit near-duplicate clusters against the labelled pair sample.
- **Resolution Protocol**: Option A, move the duplicate check into a database constraint so concurrent retries cannot both pass. Option B, widen the content hash scope to include the fields that distinguish meaning, where over-merging is observed. Option C, disable automatic near-duplicate merging and record near matches as independent occurrences until pair precision returns above 0.95.
- **Escalation Trigger**: Any false merge that destroyed a user correction escalates immediately and triggers restoration from version history; this class is never resolved by tuning a similarity threshold alone.

**Error Type 5: Instruction Escape From Retrieved Content**

- **Symptoms**: A tool call whose authorization traces to record content; a policy, allowlist, or confirmation rule changed after a read; a record whose trust class rose without a deterministic rule; corroboration satisfied by the agent's own earlier inference.
- **Diagnostic Steps**: Trace the tool call to the grant it was evaluated against; inspect the assembled context for retrieved content outside the retrieved-memory region; trace the corroborating source identifiers and test whether their lineages intersect.
- **Resolution Protocol**: Option A, move retrieved content into the data position and re-run the adversarial suite. Option B, enforce re-authorization in the tool layer rather than in a prompt instruction, since a prompt instruction is itself content. Option C, cap the authority of the affected memory type until independent corroboration is recorded.
- **Escalation Trigger**: Any privilege change traceable to memory content suspends autonomous tool use following reads; detection improvements alone never close this class, because detection failure must not grant authority.

**Error Type 6: Instrumentation Gap**

- **Symptoms**: A declared threshold with no computed metric; write attempts without events; reads emitting only a fused score; abstentions without reason codes.
- **Diagnostic Steps**: Enumerate every threshold in the operation contract and match each to an emitted field; compare event counts against store-side attempt counts for the same window.
- **Resolution Protocol**: Option A, instrument the missing field and replay the corpus to backfill the metric. Option B, remove the threshold from the contract where it cannot be instrumented, rather than leaving an unenforceable bound in place. Option C, block promotion and operate the affected path under human review until instrumentation lands.
- **Escalation Trigger**: A missing event class blocks promotion outright; this class is never resolved by estimating the metric from a sample.

**Troubleshooting Decision Tree**:

```
OPERATION FAILS ITS CONTRACT
├─ WRITE DEFECT
│   ├─ Gate skipped or unreachable → HALT ingestion; replay window; quarantine admitted records
│   ├─ Rejection without reason code → Reject the write; reissue with a code from the vocabulary
│   ├─ Two versions for one idempotency key → Move uniqueness into a database constraint
│   └─ False merge destroyed a correction → HALT merging; restore from version history
├─ READ DEFECT
│   ├─ Result above the declared cap → Clamp at the service; log the caller-supplied limit
│   ├─ Eligibility applied after ranking → Move predicates ahead of ranking; re-run regression
│   ├─ Undetermined eligibility included → Exclude the record; never attach a warning instead
│   └─ Deleted record surfaced → SEVERITY ONE; halt the path; probe every serving path
├─ CONSISTENCY DEFECT
│   ├─ Acknowledged write with no canonical version → HALT commits; fix acknowledgement order
│   ├─ Orphaned derivative → Remove entry; reconcile key range; bound orphan age to 15 minutes
│   ├─ Stale result served as fresh → Fail the bounded read instead of returning
│   └─ Out-of-order derivative event → Apply highest version; retain superseded event for audit
├─ CONTAINMENT DEFECT
│   ├─ Retrieved content in a system position → Move to the data region; re-run adversarial suite
│   ├─ Tool call authorized by record content → SUSPEND autonomous tool use; fix the tool layer
│   └─ Corroboration from own prior inference → Reject; require 2 non-intersecting lineages
└─ INSTRUMENTATION DEFECT
    ├─ Threshold without a metric → Instrument it, or remove the unenforceable bound
    └─ Missing event class → BLOCK promotion; operate under human review until instrumented
```

### D. Performance Metrics and Continuous Learning

**Write-Path Metrics**:

- **Write precision**: Adjudicated useful accepted writes over accepted writes (target: at least 0.85, reported per source and memory type).
- **Write recall**: Adjudicated useful candidates accepted over all adjudicated useful candidates (target: at least 0.75).
- **Gate rejection rate**: Rejections over attempts on a rolling 1,000-attempt window (target band: 2 percent to 30 percent; a breach in either direction halts autonomous ingestion).
- **Duplicate pair precision**: Correct merge decisions over merge decisions on a labelled sample of at least 200 pairs (target: at least 0.95; below it, automatic merging is disabled).
- **Provenance completeness**: Admitted records carrying all 4 mandatory provenance fields (target: 100 percent).
- **Silent-drop rate**: Operations ending outside the 6 terminal states (target: 0).

**Read-Path Metrics**:

- **Recall and precision at the declared bound**: Measured against version identifiers rather than text matches (targets set per query class against a measured baseline, never against an assumed one).
- **Result-bound conformance**: Reads returning within the declared cap (target: 100 percent).
- **Provenance attachment**: Returned records carrying all 11 provenance fields (target: 100 percent).
- **Abstention precision**: Abstentions correct under later adjudication (target: at least 0.90).
- **Context utilization**: Returned records used or cited in the answer, weighted by tokens (target: at least 0.50; a lower value indicates over-retrieval rather than a need for a larger result set).
- **Deleted-content leakage**: Deleted records surfacing on any serving path (target: 0).

**Consistency and Containment Metrics**:

- **Commit success and idempotency stability**: Replays under response loss producing exactly 1 effect and a stable result (target: 100 percent).
- **Derivative application success**: Outbox events applied within the freshness objective (target: at least 99.9 percent).
- **Index lag**: Time from canonical commit to derivative visibility (target: p95 no more than 5 seconds, p99 no more than 30 seconds).
- **Orphan rate and lifetime**: Derivatives without a canonical version (target: rate 0, lifetime no more than 15 minutes where any occurs).
- **Privilege changes traceable to memory content**: Measured under the adversarial suite (target: 0; a non-zero value suspends autonomous tool use).

**Learning and Adaptation Mechanisms**:

- **Calibrate the confidence floor against outcomes**: Recompute the floor per memory type from adjudicated usefulness rather than carrying the deployment default indefinitely.
- **Recalibrate gate thresholds per source**: A gate tuned on one source class misfires on another; hold thresholds per source class and per memory type.
- **Version every policy and threshold change**: Record the threshold version on every gate verdict, so a shift in rejection rate is attributable to a change rather than to traffic.
- **Adjudicate delayed usefulness**: Attach usefulness, later-use, correction, and harm labels after the observation window closes, and feed them back into write precision rather than relying on admission-time confidence.
- **Reopen the loop on component change**: Any change to the extraction model, prompt, schema, canonical store, embedding model, retriever, reranker, policy, cache, or threat model reopens Checkpoints 2 through 6.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the mechanics of admitting and retrieving a record rather than the meaning of any particular record. Its phases hold wherever an agent writes to a durable store, reads from it later, and must account for what it admitted.

### 4.1 Cross-Domain Application Patterns

**Clinical and healthcare support**: The confidence floor sits at the higher tier because an admitted error is retrieved during care. Provenance completeness is the binding gate: a record whose source is a model inference rather than a clinical system is admitted with capped authority and is never retrieved as an authoritative value. The read contract binds purpose explicitly, since a record eligible for treatment support is frequently ineligible for administrative or research purposes, and eligibility is evaluated per purpose rather than per principal. Deletion lineage extends to exports and evaluation fixtures, and the erasure verification probe is a compliance artifact rather than a diagnostic.

**Financial operations and reconciliation**: Idempotency dominates, because a duplicated write is a duplicated economic effect. Business uniqueness constraints sit on every externally visible effect independently of transport guarantees. Append semantics are mandatory for every record class, since a corrected balance and an original balance are both required for audit. The bounded-staleness mode is rarely acceptable: a read supporting a monetary decision uses canonical lookup or a consistency token, and a stale result is failed rather than labelled.

**Industrial and field operations**: Late arrival is normal rather than exceptional, because devices reconnect after outages. Late events append with their real valid time and never rewrite an earlier projection, so a reconstructed timeline distinguishes what was known from what was true. Per-key ordering by asset identity is the only ordering the system claims. Degraded reads are common and must be typed, so an operator can tell whether a missing route changed the answer.

**Legal and regulatory research**: Conflict surfacing outranks ranking quality. Contradictory records are returned together with their competing version identifiers rather than resolved by a scorer, because the disagreement is itself the finding. Source class separation between quoted source, direct observation, and model inference determines what may be cited, and the citation requirement binds the model to record identifiers rather than to paraphrase.

**Customer-facing conversational products**: Write volume is the dominant pressure and the ungated write is the dominant risk, because every turn is a candidate. The gate rejection rate band is the primary operational signal, and the confidence floor is calibrated per source rather than globally. The injection boundary carries the highest exposure here, since content arrives from the same channel that carries the request; retrieved content stays in the data region and every tool call is re-authorized against the end user's own grants.

**Software engineering agents**: Tool output is the dominant source class, and the distinction between what a tool returned and what is true governs admission. Read-your-writes is exercised constantly, because an agent writes a finding and queries it within the same task. The canonical overlay rather than the vector index serves those reads, and the derivative lag is tolerated because the overlay closes it.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small deployments**: One transactional store with immutable versions, tombstones, idempotency claims, an outbox table, and lexical search satisfies every phase. The five gates, the terminal states, and the bounded result contract are retained in full, since they cost little and prevent the corruption that is expensive to reverse. Dense retrieval, queues, rerankers, and caches are added only when a measured recall or throughput gap justifies the added failure surface.
- **High-volume deployments**: Retain every phase, add a durable queue or change-data-capture path with per-key ordering, operate immutable index generations behind an atomic alias, and run reconciliation continuously rather than on a schedule. Rebuild a generation from a canonical snapshot for any model, chunker, schema, or corpus change, and never mix incompatible embedding spaces in one score.
- **High-risk or regulated work**: Raise the confidence floor to the upper tier for every memory type, require human approval on the highest sensitivity class, treat the operation event log as a deliverable rather than a diagnostic, and prefer canonical reads over derivative reads wherever an audit could follow.
- **Strict latency budgets**: Shorten the read path by declining optional routes rather than by relaxing eligibility, since eligibility is the guarantee and route breadth is an optimization. Preserve exact lookup, authorization, tombstone checks, and minimum evidence under every degradation, and return a typed degradation naming what was skipped.
- **Multi-agent deployments**: Assign the admission validator and the retrieval service to components distinct from the agents that propose and consume records, so that no agent both proposes a write and admits it. Treat agreement among agents sharing a base model as correlated until independence is established, and require non-intersecting lineages for corroboration.

***

## V. Limitations and Considerations

**Every numeric bound here is a deployment default**: The rejection rate band of 2 percent to 30 percent, the confidence floors of 0.60 and 0.85, the result caps of 200, 50, 20, and 10, the retry ceiling of 3 attempts within 15 minutes, the pair precision target of 0.95, the index lag objectives of 5 and 30 seconds, and the token budget share of 40 percent were chosen to be operable on first deployment, not derived from a measured property of memory systems. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute thresholds per memory type and per source class against adjudicated outcomes, and to version every change so a shift in a metric is attributable.

**Exactly-once delivery is not achievable and is not the goal**: Distributed publication guarantees at-least-once delivery, and no configuration of a broker, a transactional producer, or an idempotent transport changes that. The consequence is that a system designed around an exactly-once delivery assumption will double-apply effects under retry. The mitigation is the exactly-once business-effect target in Step 4.1: idempotency claims inside the canonical transaction, business uniqueness constraints on externally visible effects, and idempotent consumers on every derivative worker.

**Gate rejection rate is a proxy, not a measure of correctness**: A rejection rate inside the declared band is consistent with a gate that rejects the wrong candidates, and a rate outside it is consistent with a genuine change in input quality. The consequence is that the band detects a malfunctioning gate but does not confirm a correct one. The mitigation is the frozen labelled corpus and the write precision and recall metrics, which measure gate decisions against adjudicated labels rather than against volume.

**Detection of instruction-shaped content is unreliable**: No classifier reliably separates instruction-shaped content from legitimate content that describes a procedure, and adversaries adapt to whatever detector is deployed. The consequence is that a system relying on detection as a control will eventually admit content it should have flagged. The mitigation is the isolation boundary in Step 5.2, under which detection failure grants no authority because retrieved content never occupies a privileged position and every tool call is re-authorized against the caller's own grants.

**Provenance completeness is a structural check, not a truth check**: A record can carry all 4 mandatory provenance fields and still assert something false, because the gate verifies that the origin is recorded rather than that the content is accurate. The consequence is that write precision depends on adjudication and cannot be inferred from gate pass rates. The mitigation is the deferred usefulness adjudication in Section III.D, which attaches outcome labels after an observation window and feeds them back into the confidence floor.

**Canonical reads and derivative reads offer different guarantees, and callers conflate them**: A caller that requests eventual consistency and then acts as though a result is current will act on stale evidence. The consequence is a class of correctness failures that looks like a retrieval quality problem. The mitigation is the freshness label on every derivative-served result and the requirement that a bounded-staleness read outside its bound fails rather than returns.

**Near-duplicate merging trades storage for evidence**: A merge that is wrong destroys an independent occurrence, a correction, or a contradiction, and storage reduction is an incentive to merge aggressively. The consequence is that a false merge is both more damaging and less visible than a duplicate. The mitigation is the reversibility requirement in Step 2.2, the separation of occurrence count from independent source count, and the pair precision floor of 0.95 below which automatic merging is disabled.

**Instrumentation carries its own exposure**: A log rich enough to compute every metric in Section III.D is rich enough to leak the content it describes. The consequence is that a telemetry pipeline becomes an unaudited copy of the memory store. The mitigation is the redaction requirement in Step 6.1: content references and keyed hashes in place of raw content, pseudonymous principal identifiers, and no secrets or unhashed identifiers in general telemetry.

**Operation correctness is not memory quality**: A deployment can satisfy every checkpoint here and still store a poorly chosen set of records, because this framework verifies that operations behave as declared and not that the declarations serve the task. The consequence is that no checkpoint substitutes for the type-specific policy the sibling guides carry, or for review of what the system was asked to remember.

***

## VI. Conclusion and Summary

A memory data plane is a pair of explicit protocols rather than a pair of convenience functions. The write protocol converts an untrusted observation into an authorized, versioned, canonical record by passing it through five deterministic gates, and it accounts for every candidate it declines. The read protocol converts a scoped question into a bounded set of eligible records carrying provenance, and it abstains rather than widening its scope when nothing qualifies. Everything else in a memory system, including consolidation, tiering, forgetting, and salience, is policy layered on top of these two primitives.

The gating asymmetry is the load-bearing idea. A defect admitted once is retrieved many times, and no read-side filter recovers what write-side gating declined to prevent, because the read path cannot tell which of two contradictory records was fabricated. Spending on the write path is therefore cheap and spending on the read path to compensate is not. The same asymmetry governs the injection boundary: a record that could act as an instruction when retrieved is a durable capability granted at write time, and the only reliable containment is structural, keeping retrieved content in a data position where detection failure grants no authority.

A team building this should start with one transactional store holding immutable versions, current pointers, tombstones, idempotency claims, provenance, and outbox rows, with lexical retrieval and complete instrumentation. Queues, change-data-capture, dense retrieval, rerankers, caches, and tiered paging each add a failure surface and should be added only when a measured gap justifies the cost. Frameworks and vector services supply plumbing; none supplies governance, and none supplies the operation contract.

**Key Success Factors**:

- **Gated admission**: Five deterministic gates in a fixed order, every rejection typed and accounted for, and a rejection rate monitored in both directions.
- **Bounded retrieval**: A declared cap enforced by the service, complete provenance on every returned record, and exclusion rather than warning for anything whose eligibility is undetermined.
- **Canonical authority**: One authoritative store, every other store rebuildable from it, and no acknowledgement that precedes a canonical commit.
- **Exactly-once effect, not exactly-once delivery**: Idempotency claims inside the transaction, business uniqueness on external effects, and idempotent consumers on every derivative.
- **Structural containment**: Retrieved content is data at every point, trust classes are assigned deterministically, and every downstream effect is re-authorized against the caller's own grants.
- **Instrumented thresholds**: Every declared bound has a computed metric behind it, and a bound that cannot be instrumented is removed rather than left unenforceable.

By following this guide, AI agents can admit records that a store can account for, retrieve evidence a reviewer can audit, and keep a memory system from becoming the mechanism by which yesterday's mistake instructs tomorrow's decision.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides that carry the type-specific policy this guide deliberately does not restate. The external references that follow are transcribed from the originating prose guide as it cited them, and were not independently re-verified in the course of this conversion; their titles and locations are reproduced rather than checked. Four areas were separately confirmed during conversion research and are marked in the list: the at-least-once delivery semantics of the transactional outbox pattern and the consequent need for consumer-side idempotency, the treatment of retrieved memory as lowest-privilege data as the current defence against memory poisoning, the eventual visibility of newly written vectors in production vector stores, and the prevailing two-stage retrieval shape of rank-based fusion over a bounded candidate set followed by reranking.

**Corpus pointers**:

- `Memory Reading and Writing Operations for AI Agents` — the originating prose guide from which this operational guide was derived. Source of the staged commit protocol, the canonical operation contract, the read-path stages, the consistency and deletion treatment, the failure taxonomy, the operation-event field inventory, the evaluation and budget guidance, and the end-to-end build sequence. Its external citations are transcribed in the list below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — the category overview covering the memory taxonomy and the selection of memory types; this guide supplies the operation primitives that overview assumes.
- `advanced_task_guides/memory-management/guide_StructuredMemory.md` — owns schema design and deterministic admission policy for structured records; this guide owns the gate that evaluates those schemas.
- `advanced_task_guides/memory-management/guide_UnstructuredMemory.md` — owns free-form record handling and verified deletion policy; this guide owns the deletion lineage mechanism in Step 4.3.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — owns episode boundaries and trajectory capture; this guide owns the capture and admission mechanism in Phase 2.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — owns bounded working state within one task episode; this guide owns the read contract that serves it.
- `advanced_task_guides/memory-management/guide_HierarchicalMemory.md` — owns placement and movement across storage tiers; this guide owns the atomicity of the writes that movement performs.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — owns evidence-gated promotion of raw episodes into durable memory; this guide owns the gate in which those promotion predicates are evaluated.
- `advanced_task_guides/memory-management/guide_AttentionBasedMemoryRetrieval.md` — owns salience calibration for admission into a bounded context; this guide owns the bounded result contract that salience operates within.
- `advanced_task_guides/memory-management/guide_LatentMemoryNetworks.md` — owns versioned latent representations over retained canonical evidence; this guide owns the derivative publication and generation-rebuild mechanism those representations depend on.
- `advanced_task_guides/memory-management/guide_DistributedMemoryArchitecture.md` — owns consistency model selection, the four session guarantees, replication topology, and the violation taxonomy across failure domains; this guide owns the per-operation commit and read contract within one canonical system. The two meet at Step 4.2 and the Consistency Guarantee Matrix: the mode is selected there and enforced here. Its naming convention is adopted in this guide, using read-your-writes for the guarantee and reserving read-your-own-writes violation for the failure event it defines.
- `advanced_task_guides/memory-management/guide_SemanticMemory.md` — owns claim modelling, identity resolution, and the scope and validity constraints under which a general fact is asserted; this guide owns the schema and provenance gates that evaluate those constraints at admission, and the validity-interval predicate that filters on them at read.
- `advanced_task_guides/memory-management/guide_TemporalKnowledgeGraphMemory.md` — owns bitemporal claim curation and the semantics of a point-in-time query; this guide owns the valid-time and transaction-time fields carried on every record version and the point-in-time snapshot read mode that reproduces historical visibility.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — owns retention policy, utility-based reduction, and the obligation rules that decide what must be removed and when; this guide owns the tombstone, invalidation, purge, and verification mechanism in Step 4.3 that carries those decisions out and proves they took effect.

**External references**:

*Operation contracts, transactions, and idempotency*

1. PostgreSQL, *Transaction Isolation* — https://www.postgresql.org/docs/current/transaction-iso.html
2. Debezium, *Outbox Event Router* — https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html
3. Apache Kafka, *Design: Message Delivery Semantics* — https://kafka.apache.org/documentation/#design_eos
4. Redis, *Distributed Locks with Redis* — https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/
5. Amazon Web Services, *Transactional Outbox Pattern* — https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html (retrieved during conversion research; confirms at-least-once delivery and the need for consumer-side idempotency)

*Memory operation surfaces and framework integrations*

6. Mem0, *Add Operations* — https://docs.mem0.ai/core-concepts/memory-operations/add
7. Mem0, *Update Operations* — https://docs.mem0.ai/core-concepts/memory-operations/update
8. Model Context Protocol, *Server Tools Specification* — https://modelcontextprotocol.io/specification/2026-07-28/server/tools
9. Model Context Protocol, *Server Resources Specification* — https://modelcontextprotocol.io/specification/2026-07-28/server/resources
10. LangGraph, *Persistence* — https://docs.langchain.com/oss/python/langgraph/persistence
11. LlamaIndex, *Agent Memory* — https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/
12. Letta, *Context Hierarchy* — https://docs.letta.com/v1-sdk/memory/context-hierarchy
13. Letta, *Memory Blocks* — https://docs.letta.com/v1-sdk/memory/memory-blocks/
14. Packer and colleagues, *MemGPT: Towards LLMs as Operating Systems* — https://arxiv.org/abs/2310.08560

*Retrieval, fusion, and context assembly*

15. Gao and colleagues, *Precise Zero-Shot Dense Retrieval without Relevance Labels* — https://arxiv.org/abs/2212.10496
16. Elasticsearch, *Reciprocal Rank Fusion* — https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
17. Liu and colleagues, *Lost in the Middle: How Language Models Use Long Contexts* — https://arxiv.org/abs/2307.03172
18. Li and colleagues, *Retrieval Augmented Generation or Long-Context LLMs? A Comprehensive Study and Hybrid Approach* — https://arxiv.org/abs/2407.16833

*Consistency, caching, and freshness*

19. Pinecone, *Understanding Data Freshness* — https://docs.pinecone.io/guides/data/understanding-data-freshness
20. OpenAI, *Prompt Caching* — https://platform.openai.com/docs/guides/prompt-caching
21. Anthropic, *Prompt Caching* — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

*Security, injection, and erasure*

22. OWASP, *LLM01: Prompt Injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
23. *Memory poisoning in agent systems* — https://arxiv.org/abs/2601.05504
24. *From Untrusted Input to Trusted Memory: A Systematic Study of Memory Poisoning Attacks in LLM Agents* — https://arxiv.org/html/2606.04329v1 (retrieved during conversion research)
25. Information Commissioner's Office, *Right to Erasure* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/

*Instrumentation and evaluation*

26. OpenTelemetry, *Semantic Conventions for Generative AI* — https://opentelemetry.io/docs/specs/semconv/gen-ai/
27. Wu and colleagues, *LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory* — https://arxiv.org/abs/2410.10813
28. *MemoryAgentBench* — https://arxiv.org/abs/2507.05257
