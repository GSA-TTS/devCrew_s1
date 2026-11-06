# Structured Agent Memory

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Structured agent memory constitutes the task family of holding durable agent knowledge in an explicit schema: typed fields, records, tables, keyed documents, or declared graph nodes and edges. It is defined against unstructured memory by three properties: it is queryable by exact predicate, joinable across records, and validatable against a schema before the write is admitted. Its retrieval is a query, not a similarity search, and its correctness is checkable mechanically rather than by inspection. This guide provides AI agents with a structured protocol covering schema design and evolution, extraction and write admission under validation, indexing and query construction, consistency and referential integrity, and retention, migration, and deletion. It assigns schema validation, constraint enforcement, referential integrity, transactional write, scope injection, and query execution to a deterministic tier that holds final authority, and confines the model tier to extraction from unstructured input, schema proposal during design, and disambiguation of genuinely ambiguous values. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a schema-valid record is treated as a candidate rather than as evidence that its values are true.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Structured memory**: Durable agent memory held in an explicit schema, where every stored value occupies a declared field with a declared datatype, comparison semantics, normalization rule, and validity domain. A structured memory is retrieved by evaluating a predicate over its fields, not by measuring similarity to a query.

**Unstructured memory**: Durable agent memory held as text, transcript, or opaque payload, retrieved by similarity, keyword match, or full re-reading. Its correctness is judged by an interpreter, whether human or model, rather than by a validator.

**Record**: One logical unit of structured memory, identified by a stable logical key and materialised as an ordered sequence of immutable versions. A record is the unit of identity, authorization, rectification, and deletion.

**Schema**: The versioned contract that declares which fields a record family carries, which are required, what each field's datatype and domain are, how values are normalized, and which constraints hold across fields. A schema is a deterministic artifact; it is never inferred at read time.

**Schema version**: The identity of the contract used to interpret a record's fields. It is independent of record version: many revisions of one record may share one schema version, and one unchanged record may be transformed across schema versions during migration.

**Record version**: The immutable identity of one revision of one logical record, carrying its own creation time, author, parent version, and supersession pointer.

**Candidate record**: A model-proposed record that has passed shape constraints but has not yet been admitted by the validation gate. A candidate is never readable by a consumer and never participates in a query.

**Admission**: The deterministic decision that promotes a candidate record into structured memory, or rejects, quarantines, or routes it for clarification. Admission is the boundary at which model authority ends.

**Context**: The set of declared dimensions under which a record is eligible to be considered, including tenant, subject, user, session, task, project, role, locale, device, environment, purpose, jurisdiction, residency, audience, and validity time. Context is an eligibility and authorization boundary, not a ranking feature.

**Applicability**: The deterministic test of whether a record's declared context matches the request context. Applicability precedes relevance and cannot be overridden by a high similarity score.

**Provenance**: The recorded origin of a value, comprising source type, source identifier and version, evidence span offsets, capture method, source authority class, and assertion mode.

**Assertion mode**: A closed vocabulary labelling how a value came to be held: directly stated, observed, imported, inferred, corrected, re-extracted, or human verified.

**Canonicalization**: The deterministic transformation of a raw value into its stored representation under a declared normalization rule and normalization version, preserving the original where the transformation could be disputed.

**Bitemporal validity**: The pair of time intervals a record carries. Valid time states when the value holds in the represented world; transaction time states when the memory system treated the version as current.

**Idempotent write**: A write whose replay under the same operation key produces one logical effect and returns the same effective result, regardless of how many times the request is delivered.

**Expand-contract migration**: The schema evolution pattern that adds the new representation, dual-writes, backfills in bounded batches, compares dual reads, cuts readers over, and only then removes the old representation.

**Tombstone**: The durable marker recording that a record was deleted, carrying the deletion authority and target inventory while holding no field content.

### 1.2 The Selection Rule Between Structured and Unstructured Memory

The distinction is not stylistic. Structured and unstructured memory differ in what can be asked of them, in what a wrong value costs, and in what machinery can detect that a value is wrong. Placing a memory in the wrong one is a design defect with a specific remedy, not a matter of preference.

**Selection rule**: A memory belongs in structured memory only where all four conditions hold. Where any condition fails, the memory belongs in unstructured memory, with a structured projection added later if and when the failing condition is satisfied.

1. **Decision dependence**: At least one named consumer decision requires an exact predicate, a join, an aggregate, a constraint, a field-level authorization, or a point-in-time answer over the field. A field that supports no such operation earns no schema.
2. **Declarable semantics**: The field admits a canonical datatype, a comparison rule, a normalization rule, and a bounded value domain that can be written down before the first record is stored.
3. **Mechanical checkability**: A wrong value is detectable by a constraint, a referential check, a cross-field rule, or a comparison against an adjudicated gold value, without requiring a human or a model to reinterpret prose.
4. **Declarable scope**: The field's tenant, subject, purpose, audience, and validity semantics can be stated, so that eligibility is decidable rather than negotiated.

**Structured and Unstructured Memory Selection**:

| Property | Structured memory | Unstructured memory |
| :-- | :-- | :-- |
| Retrieval operation | Exact predicate query, join, aggregate, point-in-time read | Similarity search, keyword match, full re-read |
| Admission test | Deterministic schema and constraint validation before write | Provenance capture only; content is not validated |
| Correctness check | Mechanical, against constraints and adjudicated gold values | Interpretive, by a human or model reader |
| Unit of rectification | One field of one record version | The whole document or transcript |
| Unit of authorization | Field and row, enforced at query time | Document, enforced at retrieval time |
| Cost of a wrong value | Propagates into joins, aggregates, and derived answers | Confined to the readers who interpret that text |
| Cost profile | High write cost, low and predictable read cost | Low write cost, high and variable read cost |
| Failure signature | Schema-conformant falsehood carrying unearned authority | Ambiguity surviving unresolved into the answer |

**Consequence of admission to structured memory in error**: Nuance present in the source is destroyed at write time and is not recoverable from the record. The coerced value then carries the authority that schema validity confers, becomes joinable and aggregable, and propagates into every derived answer that touches it. Detection thresholds are: unknown-enum resolution above 15 percent of populated values for the field, abstention above 30 percent of extraction attempts, or per-field precision below the field's harm-tier gate, each measured over a rolling window of 200 attempts. Breach of any threshold triggers demotion. Demotion removes the field from automatic persistence, writes a tombstone in the structured store pointing at the preserved source evidence, and returns the information to unstructured memory. Demotion never deletes the evidence and never rewrites the history of records already admitted.

**Consequence of retention in unstructured memory in error**: Exact queries under-return silently, because a similarity search that misses a record returns a shorter list rather than an error. The field cannot be rectified, erased, or authorized independently of the document containing it, so a correction or erasure obligation cannot be discharged at field granularity. Aggregates require a model to reinterpret prose on every read, which is neither reproducible nor auditable. Detection is a consumer decision that repeatedly requires an exact predicate the store cannot evaluate, observed at least 3 times across distinct requests. The remedy is promotion by extraction against preserved source evidence, marked with assertion mode re-extracted, subjected to the same admission gate as a first write. Promotion is never performed by asking a model to recall the value from memory rather than from evidence.

### 1.3 Execution Tier Partition and the Locus of Authority

Structured memory is the strongest case in the memory family for the deterministic tier holding most authority, because every property that distinguishes it from unstructured memory is a property a deterministic component enforces. The partition below is binding on every phase of Section II.

**Execution Tier Partition for Structured Memory**:

| Work item | Owning tier | Authority on disagreement |
| :-- | :-- | :-- |
| Schema validation and strict type checking | Deterministic | Validator; no override exists |
| Constraint, uniqueness, and range enforcement | Deterministic | Store; a violation is never bypassed |
| Referential integrity across records | Deterministic | Store |
| Canonicalization and unit conversion | Deterministic | Normalizer, at a pinned normalization version |
| Transactional write, versioning, and idempotency | Deterministic | Store |
| Scope and authorization predicate injection | Deterministic | Policy decision point; fails closed |
| Query execution, planning, and cost bounding | Deterministic | Query engine |
| Retention, decay, migration, and deletion execution | Deterministic | Orchestrator |
| Extraction of candidate records from unstructured input | Model | Model proposes only |
| Schema proposal during design | Model | Human schema owner ratifies |
| Disambiguation of a genuinely ambiguous value | Model | Model proposes; validator admits or rejects |
| Clarification question selection and phrasing | Model | Model, within deterministic attempt limits |
| Duplicate and correction adjudication | Hybrid | Deterministic canonical key first; model only on residual |
| Natural-language query generation | Hybrid | Abstract syntax tree validator and scope injector |
| Field confidence scoring | Hybrid | Deterministic calibrator maps raw score to decision |

**The proposal-admission rule**: The model proposes a record and the schema validator admits or rejects it. No model output is a write. A candidate that fails validation is not made valid by the model asserting that it is correct, and a candidate that passes validation is not thereby true. Shape control and truth are separate properties, and one 2026 evaluation of structured-output reliability separates syntax, structure, and semantics precisely because structural controls do not eliminate semantic error [1].

**The bounded retry rule**: A validation failure is never resolved by asking the model to try again without a bound. Each candidate record admits at most 2 re-extraction attempts after the first, for 3 attempts in total. An identical retry after the same error class is prohibited on the second occurrence; the second attempt must change the prompt, the evidence window, the schema view, or the model, and the change must be recorded. After 3 attempts the candidate is abstained, quarantined, or routed to human review according to the field's harm tier, and it is never persisted with a warning attached.

**The halting rule**: Rejection is a signal about the extractor, not only about the record. Where schema conformance after repair falls below 98 percent over a rolling window of 500 candidates, or where the rejection rate for any single field exceeds 20 percent of attempts over a rolling window of 200 attempts, automatic persistence halts for that extractor version or that field respectively, and the run reverts to the previous extractor generation. Where the overall candidate rejection rate exceeds 35 percent over a rolling window of 500 candidates, ingestion halts entirely for that extractor version pending review.

**What the model tier is never permitted to decide alone**: tenant, subject identity, legal basis, sensitivity class, audience scope, retention class, authorization outcome, record identity, schema version, or whether a constraint applies. These are supplied by trusted execution context or by the policy decision point and are injected outside the model's output surface. A model that emits any of these fields has its emission discarded rather than merged.

### 1.4 Context as a Deterministic Eligibility Function

Context is evaluated before relevance, and the evaluation is deterministic. For a request context and a record context, eligibility is a policy decision over identity, scope, purpose, time, and authority. A missing mandatory tenant or subject predicate fails closed and returns no rows; it never degrades to an unfiltered scan. A high similarity score cannot repair ineligibility, and post-hoc redaction of an ineligible result is not equivalent to never retrieving it, because counts, timing, ranking behaviour, and embedding proximity leak across scopes even where field values do not.

**Ordering of the eligibility pipeline**: authorization and hard isolation first, contextual applicability second, validity and freshness third, relevance and utility last. Each stage is deterministic except the last. A deployment that reverses any pair of these stages has a leakage defect regardless of its measured precision.

**Operator declaration per dimension**: Each context dimension declares its match operator before any record is written. Tenant matches exactly. Project may permit declared ancestors under a stated inheritance lattice. Audience scope requires set inclusion. Validity time requires interval containment against a stated time axis, and every query declares whether it refers to world validity or system knowledge.

**The null policy**: Null means not supplied or unknown under a named policy. Null never means all, never means false, and never means user confirmed. A global default is represented by a deliberate scope value, so that a global record is distinguishable from a record whose scope was never populated.

**The inheritance rule**: A session-scoped value may override a project or user default for the duration of that session, and must not rewrite the broader record. A project value may inherit a user default only where purpose and audience remain compatible. Tenant-wide storage never implies tenant-wide visibility; authorization is evaluated separately in every case.

***

## II. Operational Framework: Schema-Governed Memory Records Under Deterministic Admission

The framework produces a governed record product: a versioned schema, an admission gate, a typed query surface, a migration path, and a deletion path, each carrying its own measured gate. Phases 1 through 6 run in order on first construction. Phases 2 through 4 then run continuously in operation, and Phases 5 and 6 run on change and on obligation respectively. Every phase is assignable to a tier under Section 1.3, and every step that mixes tiers names the handoff explicitly.

### Phase 1: Decision Scoping and Schema Design

**Objective**: Establish which decisions justify typed records, declare the context and authority model those records answer to, and commit a minimum schema before any value is extracted.

#### Step 1.1: Establish the Decision Inventory and Simpler Baselines

**Required Actions**:

- Enumerate every consumer decision the structured store is intended to support, recording for each the exact predicate, join, aggregate, constraint, or point-in-time question it requires.
- Assign each decision a harm tier of high, medium, or low, defined by the consequence of acting on a wrong value.
- Name the memory owner, schema owner, data steward, security owner, evaluation owner, migration owner, and deletion operator, each as a single accountable role.
- Run four baselines on the same decision set: no durable memory, bounded long context, unstructured retrieval, and raw episode replay, holding model, authorization, source data, and output budget constant.
- Apply the four-condition selection rule in Section 1.2 to every candidate field, recording the failing condition for each rejection.

**Required Outputs**:

- A decision inventory with one row per decision, its required operation, its harm tier, and its consuming component.
- A named owner assignment covering all 7 roles.
- A baseline comparison record reporting task success, latency, and total cost for each of the 4 baselines.
- A candidate field list partitioned into admitted, deferred, and rejected, with the governing selection condition recorded per entry.

**Quality Checkpoints**:

- Every admitted field traces to at least 1 decision in the inventory.
- Every one of the 7 owner roles resolves to a named accountable role rather than to a team.
- At least 1 exact query, constraint, aggregation, field-level rectification, or latency requirement is documented that no baseline satisfies.
- No field is admitted whose only justification is that a model can emit it in a valid shape.

***

#### Step 1.2: Define the Context and Authority Model

**Required Actions**:

- Declare the dimension set the deployment uses, drawn from tenant, subject, user, session, task, project, role, locale, language, device, environment, purpose, jurisdiction, residency, audience, and the two time axes.
- Specify the match operator, inheritance behaviour, wildcard behaviour, and missing-value behaviour for each declared dimension.
- Mark which dimensions are security critical and bind those exclusively from authenticated execution context, excluding them from the model output surface.
- Write the null policy and the global-default representation, and state the fail-closed behaviour for each mandatory dimension.
- Construct at least 1 denial test per security-critical dimension, in which a request carrying a mismatched value must return zero rows.

**Required Outputs**:

- A context dimension specification carrying operator, inheritance, wildcard, and null semantics per dimension.
- A binding record mapping each security-critical dimension to its authenticated source.
- A denial test suite with at least 1 case per security-critical dimension.

**Quality Checkpoints**:

- Every declared dimension carries a match operator; no dimension is left to caller convention.
- No security-critical dimension is populated from model output anywhere in the pipeline.
- Every denial test returns zero rows and zero counts, and exposes no timing difference attributable to the excluded population.
- The null policy distinguishes not supplied, not applicable, withheld, redacted, not asked, and intentionally empty as separate states.

***

#### Step 1.3: Specify the Canonical Record Schema

**Required Actions**:

- Declare identity fields: a stable logical identifier, an immutable version identifier, a parent version pointer, a supersession pointer, and a separately stated natural uniqueness key.
- Declare the typed value contract per field, comprising canonical datatype, allowed range or enum domain, normalization rule, comparison semantics, and display rule, with money stored as decimal plus currency code and physical quantities stored as decimal plus canonical unit and original unit.
- Declare provenance fields covering source type, source identifier and version, evidence span offsets, capture method, source authority class, assertion mode, and evidence hash.
- Declare validity fields covering valid time interval and precision, transaction time interval, last verified time, next verification time, volatility class, and expiry.
- Declare governance fields covering purpose, audience scope, jurisdiction, residency, sensitivity class, personal-data categories, legal basis, consent reference, retention class, access policy reference, key or tokenization reference, legal hold, and deletion state.
- Declare the extension policy for any bounded document field: size cap, namespace rule, permitted datatypes, sensitivity ceiling, query eligibility, and retention treatment.
- Separate the extraction contract from the storage contract, so that identity, tenancy, authorization, and governance fields exist only in the storage contract.

**Required Outputs**:

- A versioned schema document carrying identity, value, provenance, validity, and governance sections.
- A required-versus-optional determination in which the required core is limited to identity, tenancy, type, schema version, status, source, context, transaction time, and governance.
- An extension policy statement with numeric size and cardinality caps.
- A separate extraction contract carrying only the fields a model is permitted to propose.

**Quality Checkpoints**:

- Schema version and record version are declared as independent fields with independent lifecycles.
- Every enum is declared open, with a stable code, an explicit unrecognised state, and a rule prohibiting coercion of an unfamiliar value into the nearest known one.
- No field carries a default that would be indistinguishable from evidence once stored.
- The extraction contract contains zero identity, tenancy, authorization, or governance fields.
- Every declared field maps to at least 1 decision, constraint, policy, query, or evaluation slice.

***

### Phase 2: Extraction and Write Admission Under Validation

**Objective**: Convert unstructured input into candidate records under model authority, then admit or reject each candidate under deterministic authority, so that no unvalidated value reaches a consumer.

#### Step 2.1: Constrain Generation and Ground Every Field

**Required Actions**:

- Emit candidate records through a provider-native structured output facility, a tool-definition schema, or grammar-constrained decoding, rather than through a prompt instructing the model to return valid syntax.
- Set the core schema to reject unknown properties, and permit a nullable union only where null carries a defined meaning declared in Step 1.2.
- Require for every populated field a value, an evidence span, an evidence source identifier, an assertion mode, and a raw field confidence, and require a normalization note where the canonical value differs from the source text.
- Permit per-field abstention with a reason drawn from a closed vocabulary covering missing evidence, ambiguous reference, conflicting evidence, unsupported unit, unknown enum, and policy blocked.
- Inject tenancy, subject identity, authorization, legal basis, sensitivity, retention, and record identity from trusted execution context after generation, discarding any model emission of those fields.
- Route the raw field confidence through a deterministic calibrator fitted on adjudicated examples segmented by field, source class, language, and model version, and use only the calibrated score in any decision.

**Required Outputs**:

- A candidate record set conforming to the extraction contract, with one evidence span per populated field.
- An abstention record listing each unpopulated required field with its reason code.
- A calibrated confidence value per populated field, carrying its calibration version.

**Quality Checkpoints**:

- Shape conformance before repair is at least 98 percent of completed generations; below 95 percent the extractor version is rolled back rather than repaired in place.
- Every populated field carries evidence span offsets that resolve inside the cited source version.
- Zero candidate records carry a model-emitted tenancy, authorization, identity, or governance field.
- No raw model self-reported confidence is used directly in an admission, routing, or ranking decision.
- The extractor abstains rather than populating a required business field solely to satisfy the output schema.

***

#### Step 2.2: Execute the Layered Validation Gate

**Required Actions**:

- Run the seven validation layers in order and halt the candidate at the first failing layer, recording the layer, the rule identifier, and the reason code.
- Disable type coercion for every field in the high harm tier, and emit an explicit coercion code and warning wherever coercion is permitted for a low-harm import.
- Verify that each evidence span entails the extracted value, and reject the candidate where entailment fails rather than lowering its confidence.
- Enforce the bounded retry rule from Section 1.3: at most 2 re-extraction attempts after the first, with the second attempt required to change prompt, evidence window, schema view, or model.
- Apply the halting rule from Section 1.3 to the rolling rejection windows and stop automatic persistence when any threshold is breached.
- Emit every constraint violation as telemetry with a routing decision of reject, quarantine, retry after migration, or human review.

**Validation Layer Sequence and Owning Tier**:

| Layer | Check performed | Owning tier | Failure disposition |
| :-- | :-- | :-- | :-- |
| 1 | Parse and schema conformance | Deterministic | Reject; count toward shape-conformance metric |
| 2 | Strict type validation with coercion disabled | Deterministic | Reject for high harm; warn and code for low harm |
| 3 | Canonicalization at a pinned normalization version | Deterministic | Reject on unparseable unit, currency, or instant |
| 4 | Evidence entailment and span offset resolution | Hybrid | Reject; model may propose a corrected span once |
| 5 | Cross-field and business rule evaluation | Deterministic | Reject or quarantine by rule severity |
| 6 | Scope applicability and authorization of proposed value | Deterministic | Reject; fail closed on policy unavailability |
| 7 | Comparison against current records for duplicate, correction, exception, or contradiction | Hybrid | Route to Step 3.2 rather than admitting |

**Required Outputs**:

- An admission decision per candidate drawn from accept, reject, quarantine, clarify, or review.
- A validation event per candidate carrying layer results, rule identifiers, and reason codes.
- A quarantine set holding candidates that failed a recoverable layer, with their failing layer recorded.

**Quality Checkpoints**:

- No candidate reaches the data plane without an accept decision from layer 7.
- Zero rejected payloads are stored in an extension or overflow field under any circumstance.
- Every high-harm field records zero silent coercions across the evaluation corpus.
- Retry counts never exceed 3 attempts per candidate, and no identical retry follows the same error class.
- The rolling rejection windows are evaluated on every admission, not sampled.

***

#### Step 2.3: Operate Progressive Slot Filling Under Bounded Clarification

**Required Actions**:

- Represent a multi-turn form as a versioned slot state, holding per slot the state, candidate value, evidence, validation result, attempt count, and last question issued.
- Restrict slot states to the closed vocabulary of unasked, asked, provided, validated, conflicted, declined, not applicable, and expired.
- Ask a clarification only where the missing slot changes the next decision, the value cannot be obtained from an authorized source, and the expected value of asking exceeds the interruption cost.
- Bound clarification at 2 attempts per slot and 3 clarification turns per task, and stop on decline, on ambiguity surviving the attempt limit, or on the task becoming completable by abstention.
- Issue one focused clarification at a time for high-impact ambiguity, and group compatible low-risk slots only where user burden is the binding constraint.
- Permit a safe default for execution where the schema declares one, and prohibit persisting that default as a subject attribute.

**Required Outputs**:

- A versioned slot state record per active form, with an attempt count per slot.
- A clarification log carrying question identifier, attempt number, slot, and resolution.
- A separation record distinguishing values persisted to memory from defaults used for execution only.

**Quality Checkpoints**:

- Slot state is persisted and versioned rather than held as an implicit conversational assumption.
- Clarification attempts per slot never exceed 2, and clarification turns per task never exceed 3.
- Zero workflow defaults are persisted as subject attributes across the evaluation corpus.
- Unnecessary-question rate, measured as clarifications whose answer did not change the resulting decision, is at or below 10 percent.

***

### Phase 3: Consistency, Conflict, and Referential Integrity

**Objective**: Commit admitted candidates as immutable versions under transactional guarantees, and resolve duplicates, corrections, and contradictions without erasing evidence.

#### Step 3.1: Commit Versioned, Idempotent Writes

**Required Actions**:

- Compute an operation key over the request and a natural key over the logical attribute, and derive both deterministically outside the model.
- Append an immutable record version and atomically advance the current projection in one transaction, so that history is never overwritten.
- Reject a write whose parent version identifier is stale, returning a typed conflict rather than merging or last-write-wins.
- Replay every write path under simulated response loss before, during, and after commit, and confirm that one logical request produces exactly one logical effect.
- Record the schema version, normalization version, extractor version, policy version, and migration identifier on every version, so that any later divergence is attributable.
- Enforce persisted invariants in the store itself through range and enum checks, foreign keys, unique constraints on the natural key, and interval-overlap exclusion, rather than only in application code.

**Required Outputs**:

- An immutable version chain per logical record, with parent and supersession pointers resolved.
- A current projection per logical record, advanced only within the committing transaction.
- An idempotency test record covering replay before, during, and after commit.

**Quality Checkpoints**:

- Replay of at least 50 duplicate submissions per write path yields exactly 1 logical effect in 100 percent of cases.
- Every stale-parent write returns a typed conflict; zero stale-parent writes are silently merged.
- Zero record versions are mutated in place after commit.
- Every persisted invariant declared in Step 1.3 is enforced by a store-level constraint, not by application code alone.
- Every version carries all 5 attribution versions; a version missing any one is rejected at commit.

***

#### Step 3.2: Resolve Duplicates, Corrections, and Contradictions

**Required Actions**:

- Canonicalize before comparing, so that duplicate detection operates on normalized values rather than on raw text.
- Match on the declared natural key first, and route only the residual population, where the natural key does not decide, to model adjudication.
- Classify each residual pair as duplicate, correction, scope exception, or contradiction, and apply the class-specific disposition rather than a single merge rule.
- Resolve context before resolving value, so that a global default and a session exception can coexist rather than competing for one current slot.
- Apply the deterministic precedence ladder in order: current explicit instruction, authenticated correction, authoritative system of record, scope specificity, validity time, then source authority.
- Treat a denial that a statement was ever made as a rectification request routed to Step 6.2, never as a further low-confidence observation.
- Preserve conflict state as linked records rather than resolving it by deletion, and escalate an unresolved conflict on any high-harm field.

**Required Outputs**:

- A resolution decision per residual pair, carrying its class and the precedence rung that decided it.
- A conflict link set connecting records held in unresolved disagreement.
- An escalation queue holding unresolved high-harm conflicts with their evidence attached.

**Quality Checkpoints**:

- Duplicate pair precision is at least 0.98 and recall at least 0.90 on the labelled corpus; below either bound automatic merging is disabled for the affected record family.
- The precedence ladder is applied in the declared order in 100 percent of resolutions, and any deviation is recorded as a defect.
- Zero corrections overwrite the superseded version; every correction creates a new version linked to its parent.
- Every high-harm contradiction that the ladder does not resolve is escalated rather than defaulted.
- Model adjudication is invoked only on the residual population, never in place of the natural key.

***

#### Step 3.3: Enforce Referential and Temporal Integrity Continuously

**Required Actions**:

- Declare every cross-record reference as a governed foreign key, and prohibit a reference to a record version that has been tombstoned or placed under a deletion hold.
- Enforce interval order and prohibit overlapping valid-time intervals for the same natural key, using an exclusion constraint or equivalent store-level mechanism.
- Distinguish the two time axes on every write, so that a late-arriving fact is recorded with an earlier valid time and a current transaction time rather than backdating the version.
- Scan the store periodically for records that have become invalid under current business rules, and mark them rather than deleting or rewriting them.
- Verify after every scan that no scope predicate is absent from any repository path, cache key, index definition, or export.
- Treat a schema-conformant value that fails a referential or temporal check as a fault signal about the extractor or the migration, not as an isolated data error.

**Required Outputs**:

- A referential integrity report listing dangling references, tombstone violations, and interval overlaps, each with its affected record identifiers.
- A rule-drift register listing records invalid under current rules with the rule that invalidates them.
- A scope coverage report confirming mandatory predicates on every repository path, cache key, index, and export.

**Quality Checkpoints**:

- Dangling references and tombstone violations are both exactly 0; either being non-zero halts serving for the affected record family.
- Overlapping valid-time intervals for one natural key are exactly 0.
- A record invalidated by a later rule change retains its original version history; zero historical writes are retroactively deleted.
- Scope predicate coverage is 100 percent of repository paths, cache keys, indexes, and exports.
- Every integrity failure is emitted as telemetry with a routing decision; zero failures are caught and suppressed.

***

### Phase 4: Indexing and Query Construction

**Objective**: Expose structured memory through a typed query surface whose scope predicates cannot be removed, whose cost is bounded, and whose semantic retrieval operates only inside an already eligible population.

#### Step 4.1: Expose Typed Query Contracts With Injected Scope

**Required Actions**:

- Publish an application query contract with an allowlist of queryable fields and an allowlist of operators covering equality, set membership, range, existence, containment, validity at an instant, and change since an instant.
- Bind tenant, subject, purpose, and authorization from trusted execution context and inject them as non-removable predicates, never accepting them as model-supplied arguments.
- Return declared projections rather than complete records, applying column and attribute authorization after row eligibility and before context assembly.
- Require every temporal query to declare whether its time reference is world validity or system knowledge, and reject a query that declares neither.
- Serve current values by keyed lookup, filters and aggregates by predicate query, and historical questions by point-in-time query over versions, and count independent logical records or sources in aggregates rather than immutable versions.
- Tokenize or mask sensitive values in projections unless the exact value is required for the declared purpose.

**Required Outputs**:

- A published query contract listing allowlisted fields, operators, and projections per consumer role.
- An injected predicate specification naming every mandatory scope predicate and its authenticated source.
- A projection catalogue mapping each consumer purpose to its minimum field set.

**Quality Checkpoints**:

- Zero queries execute without every mandatory scope predicate present in the executed plan, verified on the plan rather than on the request.
- Zero mandatory predicates are removable, overridable, or supplied by model output.
- Unauthorized field projection is exactly 0 across the evaluation corpus.
- Every temporal query declares its time axis; queries omitting it are rejected rather than defaulted.
- Aggregates count logical records or sources; zero aggregates count record versions as independent observations.

***

#### Step 4.2: Design Indexes and Bound Query Cost

**Required Actions**:

- Index the mandatory scope predicates first, so that isolation filtering is the cheapest operation rather than the most expensive.
- Add composite indexes matching the declared query contract's operator combinations, and reject a query shape for which no supporting index exists rather than permitting an unbounded scan.
- Cap every query with a row limit, a timeout, and an estimated-cost ceiling evaluated before execution, and reject rather than truncate when a cap is exceeded.
- Execute all read paths under read-only credentials with schema visibility restricted to the allowlisted view.
- Treat any natural-language-to-structured-query generator as untrusted: generate against a restricted schema view, parse the resulting abstract syntax tree, inject non-removable scope predicates after parsing, allowlist columns and functions, estimate cost, cap rows and time, execute in a sandbox, and validate result types before return.
- Prefer reviewed query templates or the typed application interface for any consequential operation, and prohibit generated queries on high-harm fields.

**Required Outputs**:

- An index inventory mapping each supported query shape to its supporting index.
- A cost bounding policy stating the row cap, timeout, and estimated-cost ceiling per consumer class.
- A generated-query pipeline specification listing each of the 8 guardrails and its enforcement point.

**Quality Checkpoints**:

- Every supported query shape resolves to a supporting index; unsupported shapes are rejected rather than executed.
- Zero read paths execute under credentials holding write privilege.
- Zero generated queries execute without abstract syntax tree parsing and post-parse scope injection.
- Zero generated queries are permitted on high-harm fields or on consequential write paths.
- Query rejection on cost breach is 100 percent; zero results are silently truncated.

***

#### Step 4.3: Add Semantic Retrieval Only Within the Eligible Population

**Required Actions**:

- Add semantic retrieval only where a measured paraphrase-recall gap against the typed interface has been demonstrated, and record the gap that justifies it.
- Apply hard eligibility filters before candidate generation, so that ineligible vectors never enter the candidate set, and treat this ordering as a security invariant rather than a recall optimisation.
- Benchmark achieved recall across selectivity bands on the actual index and workload, since approximate indexes differ in how filters interact with candidate generation, and record the recall curve per band.
- Rerank the eligible candidate set using both typed features and semantic score, and cap the reranked population at a declared bound.
- Prohibit widening any scope predicate to improve recall, and record any recall shortfall as an unmet gate rather than resolving it by relaxing eligibility.
- Embed only the fields or source spans the measured gap requires, and inherit the strongest applicable sensitivity classification onto every embedding.

**Required Outputs**:

- A justification record naming the measured recall gap that semantic retrieval addresses.
- A recall curve per selectivity band on the production index and workload.
- A reranking specification listing typed features, semantic score, and the population cap.

**Quality Checkpoints**:

- Hard eligibility filtering precedes candidate generation on 100 percent of hybrid query paths.
- Cross-context leakage measured on the hybrid path is exactly 0; any non-zero result halts release of the hybrid path.
- Recall is measured per selectivity band rather than reported as a single figure.
- Zero scope predicates are widened, relaxed, or made optional to reach a recall target.
- Every embedded field carries the sensitivity classification of its strongest constituent source.

***

### Phase 5: Schema Evolution and Migration

**Objective**: Change a live schema without breaking readers, fabricating evidence, or losing the ability to roll back, and re-extract only where a new field cannot be derived from what is stored.

#### Step 5.1: Classify the Change and Register the Contract

**Required Actions**:

- Classify the change as additive, rename, enum expansion, type change, split, merge, or removal, and derive the migration plan from the class rather than from the size of the diff.
- Register the new schema version and its compatibility mode with the schema registry before any code that emits it is deployed.
- Assess whether the change is breaking for security even where it is additive for shape, since a newly optional sensitive field changes the authorization surface.
- Determine for each new field whether it is losslessly derivable from stored structured data, and mark the non-derivable fields for re-extraction in Step 5.3.
- Declare the rollback deadline and the contract deadline before the migration begins, and record the named approver for each.
- Prohibit field identifier reuse in any durable event contract, and prohibit removal of a field from a durable contract before every reader has migrated.

**Required Outputs**:

- A change classification record naming the class and the resulting migration plan.
- A registered schema version with a declared compatibility mode.
- A derivability determination per new field, partitioned into derivable and requiring re-extraction.
- A declared rollback deadline and contract deadline with named approvers.

**Quality Checkpoints**:

- Every schema version is registered before the first emitting deployment; zero versions are introduced by runtime schema creation.
- Every additive change carries a security assessment, not only a compatibility assessment.
- Zero field identifiers are reused in any durable event contract.
- The rollback deadline is at least 7 days after planned cutover, and the contract deadline is later than the rollback deadline.

***

#### Step 5.2: Execute Expand, Backfill, and Dual-Read Comparison

**Required Actions**:

- Expand first: add nullable columns or optional document properties, indexes, and policy definitions, and deploy readers that understand both representations before any writer emits the new one.
- Dual-write the old and new representations only where a deterministic mapping exists, and never dual-write indefinitely.
- Backfill in bounded, idempotent, resumable batches of at most 5,000 records, with each statement targeted to complete within 5 seconds on the production workload, and record lineage per batch.
- Compare dual reads on a sample of at least 1,000 logical records per record family, comparing by logical record and context rather than by row count alone.
- Verify constraint parity, index parity, authorization parity, point-in-time answers, and latency between the two representations before any reader is cut over.
- Halt the migration and hold at the current stage on any comparison breach, rather than proceeding with a recorded discrepancy.

**Required Outputs**:

- An expanded schema with both representations readable and the new representation nullable.
- A backfill ledger recording batch identifier, records attempted, succeeded, failed, and quarantined.
- A dual-read comparison report covering value agreement, constraint deltas, index parity, authorization parity, and point-in-time agreement.

**Quality Checkpoints**:

- Dual-read mismatch is at or below 0.1 percent of sampled logical records, and exactly 0 on high-harm fields; either breach halts cutover.
- Backfill batches are idempotent, so that a replayed batch produces no additional effect.
- Constraint violation counts after backfill do not exceed counts before backfill for any rule.
- Authorization parity is exact: zero records become visible to a principal under the new representation that were invisible under the old.
- Comparison is performed by logical record and context; row-count agreement alone never satisfies this checkpoint.

***

#### Step 5.3: Cut Over, Contract, and Re-Extract Where Derivation Fails

**Required Actions**:

- Cut readers over behind a versioned flag, in a staged rollout reaching full traffic only after each stage holds without a comparison breach.
- Stop the old write path only after the rollback deadline has passed with no breach recorded.
- Remove deprecated fields only after every reader, export, cache, backup restoration path, and deletion workflow has migrated, verified by enumeration rather than by assumption.
- Re-extract non-derivable fields against preserved source evidence using the new extractor and schema, marking every result with assertion mode re-extracted rather than as an original observation.
- Compare re-extracted values against prior values and route consequential disagreement to human review rather than accepting the newer value by default.
- Leave a field unknown where source evidence was not lawfully retained, and never backfill a value that no evidence supports.

**Required Outputs**:

- A staged cutover record with per-stage traffic share and comparison result.
- A reader enumeration confirming migration of every reader, export, cache, backup path, and deletion workflow.
- A re-extraction report listing agreements, disagreements, and unresolved unknowns per field.

**Quality Checkpoints**:

- Zero fields are removed while any enumerated consumer still reads them.
- Every re-extracted value carries assertion mode re-extracted; zero re-extracted values are recorded as directly stated or observed.
- Consequential re-extraction disagreements are routed to review at 100 percent; zero are auto-accepted.
- Zero values are backfilled without supporting evidence, and unknown is recorded in preference to an inferred value.
- Rollback is exercised at least once against a restored backup before the contract deadline.

***

### Phase 6: Retention, Rectification, and Deletion

**Objective**: Bind every record to a retention and verification lifecycle, discharge correction and erasure obligations across all derivatives, and gate release on measured evidence rather than on schema validity.

#### Step 6.1: Bind Retention, Volatility, and Decay

**Required Actions**:

- Assign every field a volatility class and a verification interval derived from that class, so that a confirmed stable preference and a rapidly changing role state are not refreshed on the same schedule.
- Reduce eligibility or calibrated confidence for unverified attributes as their verification interval elapses, without rewriting the stored value or its history.
- Surface staleness to consumers as an explicit field rather than inferring currency from schema validity, and require a fresh confirmation before any high-harm decision depends on a stale value.
- Prohibit retrieval frequency from counting as verification, so that a frequently read stale field does not acquire apparent currency.
- Enforce retention class expiry as a deterministic scheduled operation, and distinguish an expiry deadline from a claim that the underlying fact ceased to hold.
- Attempt refresh from an authoritative source before decaying a field, and record the refresh attempt whether or not it succeeded.

**Required Outputs**:

- A volatility and verification interval assignment per field.
- A decay policy statement with its version, naming the eligibility and confidence effect per elapsed interval.
- A staleness indicator exposed on every returned record alongside its validity and confidence.

**Quality Checkpoints**:

- Every field carries a volatility class; zero fields inherit a single global refresh interval.
- Zero decay operations rewrite a stored value or delete a prior version.
- Retrieval events never update last-verified time.
- Stale-result rate on high-harm decisions is at or below 2 percent; above that, the affected fields require confirmation before use.
- Every decayed field records a refresh attempt identifier and outcome.

***

#### Step 6.2: Execute Rectification and Erasure Across Derivatives

**Required Actions**:

- Treat a rectification as a new record version carrying the requester, the authoritative evidence, and a reason code, never as an in-place edit of the prior version.
- Enumerate every derivative of the corrected or erased field, including current projections, embeddings, caches, exports, aggregates, evaluation datasets, and backups, and invalidate each by enumeration rather than by expiry.
- Apply the strongest constituent classification to every derivative unless a documented transformation demonstrates that the derivative carries less exposure.
- Write a tombstone on erasure carrying the deletion authority, the target inventory, and the verification method, and stop serving the target immediately on tombstone write rather than at purge time.
- Verify purge across every target with a recorded verification method and time, and record residual risk explicitly where a backup class cannot be purged within its cycle.
- Preserve only the audit data the governing obligation permits, and record the legal basis for any retention that survives an erasure request.

**Required Outputs**:

- A rectification record per correction, carrying before and after version identifiers and the derivative inventory.
- A tombstone per erasure, carrying authority, target inventory, and verification method.
- A purge verification report with per-target status, verification method, and residual risk.

**Quality Checkpoints**:

- Zero rectifications overwrite the prior version; every correction produces a new version linked to its parent.
- Derivative invalidation covers 100 percent of enumerated targets; a target discovered after the fact is a defect, not an exception.
- Tombstoned records stop serving immediately, verified by a read attempt returning zero rows.
- Rectification propagation to all serving paths completes within its declared objective; breaches are recorded with the exceeded interval.
- Residual risk is stated explicitly for every target that cannot be purged within its backup cycle.

***

#### Step 6.3: Instrument, Evaluate, and Gate Release

**Required Actions**:

- Emit append-only operation events alongside immutable record versions, holding content-bearing evidence in a restricted store and general telemetry as hashes, categories, and references.
- Record on every event the identity, trace, context, governance, timing, cost, and outcome fields required to compute the metric set, and exclude subject and record identifiers from metric label dimensions.
- Evaluate structure and content separately: report shape conformance before and after repair, and report per-field precision, recall, and their harmonic mean against a frozen adjudicated corpus.
- Build the corpus with representative sampling across field, scope, source authority, language, locale, and harm tier, including missing evidence, unknown enums, unit ambiguity, negation, corrections, session exceptions, multilingual paraphrases, cross-tenant attempts, and stale values, and hold an untouched temporal test partition.
- Set per-field gates by harm tier rather than by a single average, and declare every gate before results are observed.
- Run load, soak, and adversarial evaluation replaying writes, queries, contradictions, decay, refresh, migrations, retries, and deletions at production scale, injecting schema-valid false values and instruction-bearing strings.
- Shadow the pipeline without changing production memory, then canary immutable schema, extractor, prompt, validator, policy, and index generations to a bounded authorized cohort.

**Release Gates by Harm Tier**:

| Gate | High harm | Medium harm | Low harm |
| :-- | :-- | :-- | :-- |
| Per-field precision | at least 0.98 | at least 0.95 | at least 0.90 |
| Per-field recall | at least 0.90 | at least 0.85 | at least 0.75 |
| Expected calibration error | at most 0.05 | at most 0.10 | at most 0.15 |
| Silent coercion count | 0 | 0 | reported with codes |
| Cross-context leakage | 0 | 0 | 0 |
| Unauthorized field projection | 0 | 0 | 0 |
| Idempotent single effect under replay | 100 percent | 100 percent | 100 percent |
| Human review coverage | 100 percent of writes | sampled at 10 percent | sampled at 2 percent |

**Required Outputs**:

- A frozen adjudicated corpus with declared development, calibration, and untouched temporal partitions.
- A metric report covering extraction, validation, integrity, retrieval, migration, latency, and cost, with confidence intervals and minimum sample sizes for rare fields.
- A release decision record naming every gate, its declared threshold, its measured value, and its verdict.

**Quality Checkpoints**:

- Every gate was declared before its result was observed; a gate adjusted after measurement invalidates the release decision.
- Cross-context leakage, unauthorized field projection, and stale-parent silent merge are each exactly 0 in the tested population; any non-zero value blocks release.
- Rare fields carry a stated minimum sample size and confidence interval rather than a point estimate.
- Downstream task success or measured risk improves against the unstructured and long-context baselines from Step 1.1; where it does not, the schema is simplified or the information is returned to unstructured memory.
- Zero subject or record identifiers appear as metric label dimensions.

***

## III. Implementation Guidance for AI Agents

AI agents operating structured memory must follow systematic protocols ensuring that every stored value was admitted by a deterministic gate, carries its evidence and its scope, and can be queried, corrected, migrated, and deleted without reinterpretation. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Schema Owner Agent**: Holds the versioned schema, the extraction contract, and the compatibility mode. It alone registers a schema version, and every registration is versioned and approved. It never writes record data.
2. **Extraction Agent**: Emits candidate records through a constrained output facility against the extraction contract only. It may propose values, evidence spans, assertion modes, and abstentions, and may not emit identity, tenancy, authorization, or governance fields.
3. **Validation Agent**: Runs the seven-layer gate in order, holds the bounded retry counter, and issues the admission decision. Its verdict is final and is not appealable by any model output.
4. **Persistence Agent**: Computes operation and natural keys, commits immutable versions, advances current projections transactionally, and returns typed conflicts. It never resolves a conflict by merging.
5. **Query Agent**: Publishes the typed contract, injects mandatory scope predicates from authenticated context, bounds cost, and applies projection authorization. It rejects any query lacking a supporting index or a declared time axis.
6. **Migration Agent**: Executes expand, backfill, dual-read comparison, cutover, and contract, and holds the rollback deadline. It halts on any comparison breach rather than proceeding with a discrepancy.
7. **Governance Agent**: Owns retention, decay, rectification, erasure, tombstones, and purge verification, and may veto release where a derivative inventory is incomplete.

**Authority Rule**: Where the model tier and the deterministic tier disagree, the deterministic tier prevails without exception. A validator rejection is not overturned by a model assertion, a policy denial is not overturned by a relevance score, and a constraint violation is not stored in an alternate field. The model proposes; the schema validator admits or rejects.

**Workflow Execution Pattern**:

```
STATE: Candidate_Admission
INPUTS:
  1. Candidate record set from the Extraction Agent
  2. Registered schema version and normalization version
  3. Authenticated context bindings for scope and governance fields
ACTIONS:
  1. Run validation layers 1 through 7 in order, halting at first failure
  2. Inject scope and governance fields from authenticated context
  3. Evaluate rolling rejection windows against the halting thresholds
  4. Issue exactly one admission decision per candidate
VALIDATION:
  - model_emitted_governance_field_count == 0
  - evidence_span_resolves_in_cited_source == TRUE
  - retry_attempts_for_candidate <= 3
  - identical_retry_after_same_error_class == FALSE
  - field_rejection_rate_200 <= 0.20
  - candidate_rejection_rate_500 <= 0.35
  - shape_conformance_after_repair_500 >= 0.98
TRANSITIONS:
  IF decision == ACCEPT THEN next_state = Versioned_Commit
  IF decision IN {REJECT, QUARANTINE} THEN next_state = Rejection_Telemetry
  IF decision == CLARIFY THEN next_state = Bounded_Slot_Clarification
  IF decision == REVIEW THEN next_state = Await_Human_Adjudication
  IF halting_threshold_breached THEN next_state = Ingestion_Halt_And_Rollback
```

**Two-Phase Action Pattern**: Emit the candidate record with its evidence, proposed scope, and calibrated confidence without committing it; validate it against the layer sequence while no storage effect exists; commit only after layer 7 accepts, writing the record version and the admission event in the same transaction.

**Approval Gate**: Human authorisation is required before registering a schema version that adds or widens a sensitive field, before removing any field from a durable contract, before cutting over any migration whose dual-read mismatch exceeds 0 on a high-harm field, before enabling automatic persistence for a field in the high harm tier, and before any purge whose verification method cannot confirm removal from a backup class. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the schema, the context binding table, and the retry counters in durable state, since ingestion outlives any single context window.
- Return projections rather than whole records into model context, so that the assembled context carries the minimum field set for the declared purpose.
- Pass evidence by reference and hash rather than by inlining raw source payloads into working context.
- Write a handoff record at every context boundary naming the schema version, the pending candidate set, the retry counters, and the open clarification slots.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Schema Justification (After Phase 1)**

- **Automated Check**: Every admitted field traces to at least 1 inventory decision; all 7 owner roles are named; all 4 baselines have recorded results; every security-critical dimension has a passing denial test.
- **Agent Action on Pass**: Proceed to extraction implementation.
- **Agent Action on Failure**: Halt and return the unjustified fields; no extraction is implemented against an unjustified schema.
- **Human Review Trigger**: Any field admitted in the high harm tier, or any decision no baseline satisfies that also lacks a stated exact-query requirement.

**Checkpoint 2: Admission Integrity (After Phase 2)**

- **Automated Check**: Shape conformance after repair is at or above 98 percent; zero model-emitted governance fields; every populated field has a resolving evidence span; retry counts are at or below 3 with no identical retry after the same error class.
- **Agent Action on Pass**: Proceed to persistence.
- **Agent Action on Failure**: Quarantine the affected candidates and evaluate the rolling rejection windows before any further ingestion.
- **Human Review Trigger**: Field rejection rate above 20 percent over 200 attempts, or candidate rejection rate above 35 percent over 500 candidates.

**Checkpoint 3: Persistence Consistency (After Phase 3)**

- **Automated Check**: Replay of at least 50 duplicate submissions yields exactly 1 effect; zero in-place version mutations; dangling references, tombstone violations, and interval overlaps are each 0; every version carries all 5 attribution versions.
- **Agent Action on Pass**: Proceed to query surface exposure.
- **Agent Action on Failure**: Halt serving for the affected record family; an integrity defect is never served with a warning.
- **Human Review Trigger**: Any duplicate merge performed by model adjudication that a later audit reverses, or duplicate pair precision below 0.98.

**Checkpoint 4: Query Safety (After Phase 4)**

- **Automated Check**: Every executed plan carries all mandatory scope predicates; zero read paths hold write privilege; unauthorized field projection is 0; cross-context leakage on the hybrid path is 0.
- **Agent Action on Pass**: Release the query surface to its declared consumer roles.
- **Agent Action on Failure**: Withdraw the query surface; a leakage defect is never mitigated by post-hoc redaction.
- **Human Review Trigger**: Any generated-query path proposed for a high-harm field, or any recall shortfall proposed to be closed by widening a scope predicate.

**Checkpoint 5: Migration Equivalence (After Phase 5)**

- **Automated Check**: Dual-read mismatch is at or below 0.1 percent overall and 0 on high-harm fields; constraint counts after backfill do not exceed counts before; authorization parity is exact; rollback was exercised against a restored backup.
- **Agent Action on Pass**: Proceed to staged cutover.
- **Agent Action on Failure**: Hold at the current stage; a migration is never advanced with a recorded discrepancy.
- **Human Review Trigger**: Any consequential re-extraction disagreement, or any field proposed for removal while a reader remains enumerated.

**Checkpoint 6: Release Readiness (After Phase 6)**

- **Automated Check**: Every harm-tier gate in Phase 6 is met with its declared threshold and a stated confidence interval; leakage, unauthorized projection, and stale-parent silent merge are each 0; derivative invalidation covers 100 percent of enumerated targets.
- **Agent Action on Pass**: Release the configuration and record the gate table as the release evidence.
- **Agent Action on Failure**: Withhold release and name the failing gate with its measured value; no configuration is released on aggregate averages alone.
- **Human Review Trigger**: Any gate adjusted after its result was observed, or any purge target whose verification method cannot confirm removal.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
OWNING_TIER:
VALIDATION_CRITERIA:
MEASURED_VALUE:
SAMPLE_SIZE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Schema-Conformant Falsehood**

- **Symptoms**: A value passes every type, range, and constraint check and is later contradicted by an authoritative source; per-field precision falls while shape conformance stays near 100 percent.
- **Diagnostic Steps**: Confirm the evidence span resolves inside the cited source version and entails the value; segment precision by field, source class, language, and model version to locate the failing segment rather than treating the whole extractor as degraded.
- **Resolution Protocol**: Option A, tighten the evidence entailment layer so that an unentailed value is rejected rather than accepted at lower confidence. Option B, move the field to confirmation-required persistence, so that a human or an authoritative system admits it. Option C, demote the field to unstructured memory under the Section 1.2 demotion rule and preserve the evidence.
- **Escalation Trigger**: Per-field precision below the harm-tier gate over a rolling window of 200 attempts halts automatic persistence for that field; this class is never resolved by re-prompting the same extractor.

**Error Type 2: Cross-Context Leakage**

- **Symptoms**: A record eligible in one scope appears in a result, count, aggregate, cache entry, embedding neighbourhood, or export belonging to another; a denial test returns a non-zero count or a distinguishable latency.
- **Diagnostic Steps**: Enumerate every path that reads the record family, including repository methods, cache keys, index definitions, vector filters, exports, and migration readers, and locate the path from which the mandatory predicate is absent.
- **Resolution Protocol**: Option A, move predicate injection to the repository boundary so that no caller path can omit it. Option B, replace post-hoc redaction with pre-filtering on the vector path, since post-hoc redaction leaks counts, timing, and ranking. Option C, withdraw the affected query surface until the enumeration is complete.
- **Escalation Trigger**: Any non-zero leakage measurement halts serving for the affected record family immediately; this class is never accepted with a compensating control.

**Error Type 3: Silent Coercion and Default Pollution**

- **Symptoms**: Boolean, date, money, unit, identifier, or enum fields hold plausible values that no source states; a currency, timezone, or unit appears uniformly across records regardless of source locale.
- **Diagnostic Steps**: Compare stored canonical values against preserved originals across the corpus, and count values whose provenance is an application default rather than an evidence span.
- **Resolution Protocol**: Option A, disable coercion for the field and reject rather than convert. Option B, move the default out of canonical memory and into the execution path, so that it is used but never persisted. Option C, re-extract the affected records against preserved evidence and mark them re-extracted.
- **Escalation Trigger**: Any non-zero silent coercion count on a high-harm field halts persistence for that field; more than 3 affected fields in one record family triggers schema review rather than field-by-field repair.

**Error Type 4: Bounded Retry Exhaustion and Extractor Degradation**

- **Symptoms**: The same candidate fails the same validation layer repeatedly; rejection rates climb after a model, prompt, or schema change; abstention rises without a corresponding rise in evidence scarcity.
- **Diagnostic Steps**: Segment rejection by layer, field, and extractor version, and determine whether the change coincides with a model version, prompt version, schema version, or source distribution shift.
- **Resolution Protocol**: Option A, roll back to the previous extractor generation and re-run the frozen corpus to confirm recovery. Option B, narrow the extraction contract to the fields that still meet their gates and defer the rest. Option C, route the affected field to human-confirmed persistence until a replacement extractor passes its gates.
- **Escalation Trigger**: 3 attempts per candidate is an absolute bound; candidate rejection above 35 percent over 500 candidates halts ingestion for the extractor version; the loop is never continued on the expectation that a further identical attempt will succeed.

**Error Type 5: Migration Divergence**

- **Symptoms**: Old and new readers return different answers for the same logical record and context; constraint violation counts rise after backfill; a point-in-time query answers differently across representations.
- **Diagnostic Steps**: Compare by logical record and context rather than by row count, and partition mismatches by change class to determine whether the mapping, the backfill, or the reader is at fault.
- **Resolution Protocol**: Option A, hold at the current migration stage and repair the mapping before advancing. Option B, roll back to the pre-cutover representation, which remains available until the rollback deadline. Option C, re-extract the affected fields against preserved evidence where no deterministic mapping exists.
- **Escalation Trigger**: Any mismatch on a high-harm field halts cutover; overall mismatch above 0.1 percent of sampled logical records halts cutover; divergence is never resolved by widening the comparison tolerance.

**Error Type 6: Contradictory Current State**

- **Symptoms**: Global defaults, session exceptions, corrections, and stale imports compete for one current slot; the same query returns different current values across adjacent requests; conflict links accumulate without resolution.
- **Diagnostic Steps**: Verify that scope and validity time are represented explicitly rather than collapsed, and replay the precedence ladder to determine which rung failed to decide.
- **Resolution Protocol**: Option A, represent the session exception and the global default as separate scoped records rather than as competing versions. Option B, apply the precedence ladder in declared order and record the deciding rung. Option C, escalate with both records and their evidence attached.
- **Escalation Trigger**: Any unresolved contradiction on a high-harm field escalates immediately; contradiction is never resolved by discarding the older record, since the older record may be the correctly scoped one.

**Troubleshooting Decision Tree**:

```
STRUCTURED MEMORY DEFECT DETECTED
├─ ADMISSION DEFECT
│   ├─ Shape valid, value false → Tighten entailment; demote field if gate still fails
│   ├─ Governance field model-emitted → Discard emission; rebind from authenticated context
│   └─ Retry count at bound → Abstain, quarantine, or route to review; never retry identically
├─ ISOLATION DEFECT
│   ├─ Predicate absent from a read path → Move injection to repository boundary
│   ├─ Post-hoc redaction in use → Replace with pre-filter; redaction leaks counts and timing
│   └─ Denial test non-zero → HALT serving for the record family
├─ VALUE FIDELITY DEFECT
│   ├─ Silent coercion present → Disable coercion; reject rather than convert
│   ├─ Default stored as evidence → Move default to execution path; re-extract affected records
│   └─ Unit or currency uniform across locales → Restore unit-bearing type; preserve original
├─ INTEGRITY DEFECT
│   ├─ Stale-parent write merged → HALT; return typed conflict instead
│   ├─ Interval overlap present → Restore exclusion constraint; split the intervals
│   └─ Dangling reference or tombstone violation → HALT serving; repair by enumeration
├─ EVOLUTION DEFECT
│   ├─ Dual-read mismatch on high-harm field → HALT cutover; repair mapping
│   ├─ Field removed with reader remaining → Roll back removal; complete enumeration
│   └─ Backfill without evidence → Revert to unknown; never infer a backfilled value
└─ LIFECYCLE DEFECT
    ├─ Derivative missed on erasure → HALT release; complete derivative inventory
    ├─ Retrieval treated as verification → Restore last-verified semantics; re-apply decay
    └─ Tombstone still serving → HALT; stop serving at tombstone write, not at purge
```

### D. Performance Metrics and Continuous Learning

**Extraction and Admission Metrics**:

- **Shape conformance**: Conforming candidates over completed generations, reported before and after repair (target: at least 98 percent after repair; below 95 percent rolls back the extractor version).
- **Per-field precision and recall**: Correct populated values over populated values, and over gold-present values, reported per field and harm tier rather than as one average (targets: the Phase 6 gate table).
- **Abstention quality**: Coverage, accepted-case risk, false abstention, and unsafe completion where evidence is absent (target: false abstention at or below 10 percent at the declared coverage).
- **Calibration error**: Expected calibration error and Brier score per field and source class (target: at most 0.05 for high harm; above 0.15 suspends automatic acceptance for the segment).
- **Hallucinated field rate**: Populated fields whose evidence span does not entail the value (target: 0 for high harm; at most 1 percent for low harm).

**Integrity and Retrieval Metrics**:

- **Idempotent single effect**: Logical effects over replayed identical requests (target: exactly 1 effect in 100 percent of replays).
- **Constraint violation escape**: Records violating a declared constraint that reached a consumer (target: 0).
- **Duplicate pair precision and recall**: Merge decisions judged correct on the labelled corpus (targets: at least 0.98 precision and 0.90 recall).
- **Typed filter precision and recall**: Returned records satisfying the declared predicate, and eligible records returned (targets: 1.00 precision; recall at least 0.95 within the eligible population).
- **Cross-context leakage**: Records returned outside their eligible scope (target: exactly 0; any non-zero value blocks release).
- **Stale retrieval rate**: Returned records past their verification interval on a high-harm decision (target: at most 2 percent).

**Lifecycle and Cost Metrics**:

- **Migration completeness and agreement**: Records migrated over records affected, and dual-read agreement by logical record (targets: 100 percent completeness; mismatch at or below 0.1 percent and 0 on high-harm fields).
- **Rectification propagation latency**: Time from correction commit to invalidation of the last enumerated derivative (target: within the declared objective; breaches recorded with the exceeded interval).
- **Deletion completeness**: Verified purged targets over enumerated targets (target: 100 percent, with residual risk stated for any exception).
- **Cost per correct policy-compliant memory-assisted task**: Total cost including extraction, retries, validation, storage, indexes, policy calls, migrations, human review, telemetry, and deletion, over accepted correct outcomes (target: below the unstructured and long-context baselines at matched quality).
- **Latency distribution**: Reported at the 50th, 95th, and 99th percentiles per stage rather than as a single mean.

**Learning and Adaptation Mechanisms**:

- **Adjudicated sampling**: Continuously sample accepted, rejected, and abstained candidates, oversampling rare fields, multilingual inputs, corrections, and unit conversions, and feed adjudicated labels back into the calibrator.
- **Enum and null observatory**: Monitor unknown-enum frequency, null reason distribution, and extension field growth, and revise controlled vocabularies deliberately rather than by letting an unrecognised bucket absorb new reality.
- **Schema pressure signals**: Treat a rising unknown-enum rate, a rising abstention rate, or a rising extension payload as evidence that the schema no longer fits the domain, and open Phase 5 rather than widening tolerances.
- **Threshold recalibration**: Recompute every threshold per field and harm tier against observed outcomes; the values stated here are deployment defaults, not measured constants.
- **Loop reopening**: Return to Phase 1 whenever decisions, schemas, models, prompts, sources, policies, jurisdictions, storage engines, query engines, or traffic distributions change materially.

**Human-in-the-Loop Boundaries**: Registration of a schema version adding or widening a sensitive field, removal of a field from a durable contract, admission of a high-harm field to automatic persistence, acceptance of a consequential re-extraction disagreement, adjustment of a release gate, and confirmation of a purge whose verification method is incomplete are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the admission, query, evolution, and disposal of typed records rather than the content of any particular record. Its phases hold wherever a decision requires an exact predicate over a value, that value can be given declared semantics, and a wrong value is mechanically detectable.

### 4.1 Cross-Domain Application Patterns

**Clinical and care coordination**: Structured records hold allergy, medication, dosage, unit, and care-plan constraint fields; unstructured memory holds the narrative in which those values were stated. The harm tier is high almost throughout, so per-field precision gates bind at the top of the table and confirmation-required persistence is the default rather than the exception. Unit-bearing types are mandatory, since a dosage stored without its unit is not a partially correct record but an actively dangerous one. Bitemporal validity carries real weight: a clinician needs both what is true of the patient now and what the record said on the date a decision was taken. Rectification propagation must reach derived alerts and decision-support caches, not only the primary row.

**Financial services and regulated lending**: Eligibility facts, declared income, jurisdiction, consent references, and legal basis are the typed core, and every one of them is a governance field bound from an authenticated system of record rather than proposed by a model. Point-in-time query is the dominant read pattern, because the reviewable question is what the system believed at decision time rather than what it believes now. Generated queries are prohibited on the decisioning path entirely; the typed contract and reviewed templates carry all consequential reads. The event log is a supervisory deliverable rather than a diagnostic convenience.

**Industrial operations and field service**: Asset configuration, calibration state, firmware version, environment scope, and device capability form the typed core, and the environment and device dimensions do most of the eligibility work. Volatility classes diverge sharply: an asset serial number is effectively permanent while a calibration state expires within a shift, so a single refresh interval would be simultaneously wasteful and unsafe. A workaround learned against a retired interface version must carry that version in its scope, so that it expires with the interface rather than persisting as a timeless preference.

**Public administration and benefits eligibility**: Jurisdiction, residency, purpose, and legal basis are load-bearing rather than decorative, and the audience dimension is often narrower than the query dimension, since an official may be permitted to know that a record exists without being permitted to see its value. Erasure and rectification obligations are enforceable, so the derivative inventory and the purge verification report are compliance artifacts. Open enums matter unusually much here, because statutory categories change on a legislative rather than an engineering timetable, and coercing a new category into the nearest existing one misclassifies a person.

**Commerce and travel personalisation**: The harm tier is mostly low, so recall gates loosen and sampled human review replaces full coverage. The distinguishing pressure is scope discipline rather than precision: a stated preference for one trip and a durable default must remain separate records rather than competing for one current slot, and a session exception must not silently rewrite a global default. The unstructured companion carries the phrasing and the nuance; the structured record carries only the fields a booking, pricing, or filtering operation evaluates exactly.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small-scope deployments**: One transactional store, an application-level schema validator, constrained model output, deterministic normalization, a frozen labelled corpus of at least 200 records per high-harm field, and structured logs are sufficient. Collapse the schema registry into the migration tool's version history, and run Phase 6 evaluation as a scheduled batch rather than as a service. Do not collapse the validation gate, the versioning discipline, or the scope injection, since these carry the guarantees that distinguish structured memory from an unvalidated table.
- **Large-scope deployments**: Add a schema registry with enforced compatibility policy, a migration runner, background backfill and re-extraction workers, an external policy decision point, field-level encryption or tokenization, immutable audit events, deletion orchestration, and an evaluation service. Partition rolling rejection windows per tenant as well as globally, so that one tenant's source distribution shift does not hide behind an aggregate.
- **High-harm records**: Require confirmation-required persistence, full human review coverage on writes, precision gates at the top of the Phase 6 table, prohibition of generated queries, and zero tolerance on dual-read mismatch during migration. Prefer leaving a field unknown to admitting an unverified value.
- **Low-harm records**: Permit coded coercion with a warning, sampled review at 2 percent, and looser recall gates. Retain unchanged the three invariants that never scale down: zero cross-context leakage, zero unauthorized field projection, and one logical effect per logical request.
- **Strict latency budgets**: Keep the interactive write path to authenticated context binding, extraction only where the next turn requires it, strict validation, canonical lookup, and commit. Move non-urgent extraction, embedding, re-extraction, backfill, and drift scanning to batch. Shorten the validated field set rather than removing validation layers, since removing a layer removes a guarantee while narrowing the field set only narrows scope.
- **Multi-tenant deployments**: Make tenant an exact-match mandatory predicate at the repository boundary, include it in keys, indexes, cache keys, encryption context, and logs, and run the denial test suite per tenant class on every release rather than once at design time.

***

## V. Limitations and Considerations

**Schema design is the standing bottleneck**: Typing forces a commitment to categories, units, and boundaries before the domain has necessarily stabilised, and a premature commitment is expensive to reverse because it propagates into indexes, policies, queries, and consumer code. The mitigation is the four-condition selection rule in Section 1.2, which admits a field only where a decision, declarable semantics, mechanical checkability, and declarable scope all exist, together with the demotion path that returns a failing field to unstructured memory without destroying its evidence.

**Structural validity does not establish truth**: Constrained decoding and schema validation guarantee shape, and a schema-conformant falsehood passes every layer that checks shape. Reported figures for structural control are correspondingly high while content agreement lags, and one evaluation of a structured-extraction method reports 99.5 percent schema accuracy alongside 94.0 percent content similarity in its own setting [2]. The mitigation is the evidence entailment layer, per-field precision gates set by harm tier, and the explicit separation in the Phase 6 report between shape conformance and value correctness.

**Structure raises aggregation risk even as it improves control**: Normalized attributes are easier to classify, minimize, encrypt, correct, and delete, and they are equally easier to join, score, and infer from. A field that is individually innocuous can become identifying in combination. The mitigation is field-level classification, projection minimization at read time, the ordering that applies authorization before relevance, and the requirement that every derivative inherit the strongest constituent classification.

**Generated queries remain unreliable on enterprise semantics**: Natural-language-to-query generation can produce executable output that binds the wrong field, omits a scope or time predicate, misreads null semantics, or selects sensitive columns. Enterprise benchmarks show a wide gap between syntactic success and semantic correctness, and one benchmark of 9,128 question-and-query pairs across 812 tables and 19 domains reports severe difficulty for advanced systems [3]; independent 2026 reporting places frontier-model accuracy on enterprise-grade query benchmarks far below their accuracy on earlier academic ones. The mitigation is the eight-guardrail pipeline in Step 4.2, the prohibition of generated queries on high-harm fields, and the preference for reviewed templates or the typed interface on any consequential read.

**Thresholds here are deployment defaults, not measured constants**: The precision, recall, calibration, rejection-window, batch-size, and mismatch bounds stated throughout were chosen to be operable on first deployment rather than derived from a property of structured memory systems in general. The 98 percent shape-conformance floor, the 20 percent field rejection and 35 percent candidate rejection halting thresholds, the 3-attempt retry bound, the 5,000-record backfill batch, the 0.1 percent dual-read mismatch bound, and the harm-tier gate table are all defaults of this kind. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute every threshold per field and harm tier against its own adjudicated outcomes.

**Maintenance cost is systematically underestimated**: Structured memory moves work out of every read and into extraction, validation, indexing, migration, review, and disposal, and that work is easy to omit from an evaluation that measures only answer quality. A 2026 survey of memory systems for autonomous agents reports that benchmarks are frequently underscaled, that metrics can misalign with semantic utility, and that system-level and maintenance costs are commonly overlooked [4]. The mitigation is the cost metric in Section III.D, which requires cost per correct, policy-compliant, memory-assisted task to include extraction, retries, validation, storage, indexes, policy calls, migrations, human review, telemetry, and deletion.

**Evaluation corpora age faster than schemas**: A frozen adjudicated corpus becomes unrepresentative as sources, languages, locales, and category distributions shift, and gates measured against a stale corpus give false assurance. The mitigation is the untouched temporal test partition required in Step 6.3 together with the enum and null observatory in Section III.D, which surfaces distribution drift as a schema pressure signal rather than as an unexplained metric decline.

**Conformance to this framework is not fitness for purpose**: A deployment can satisfy every checkpoint here and still hold a schema that answers the wrong questions, since the framework detects malformed records rather than misdirected modelling. The mitigation is the decision inventory and baseline comparison in Step 1.1, which requires a demonstrated advantage over unstructured, long-context, episodic, and no-memory baselines before typing is adopted, and which is repeated whenever the loop is reopened.

***

## VI. Conclusion and Summary

Structured agent memory is a governance discipline before it is a storage choice. Its value comes from making identity, scope, type, provenance, time, confidence, sensitivity, and version explicit enough that an agent can retrieve and update the right attribute by predicate rather than by rereading a narrative, and can prove afterwards what it held and when. Its danger comes from compressing ambiguity into an authoritative-looking field and then reusing that field outside the context in which it was learned.

The partition of authority is what makes the discipline executable. Schema validation, constraint enforcement, referential integrity, transactional write, scope injection, and query execution are deterministic and belong to software; extraction from unstructured input, schema proposal, and disambiguation of genuinely ambiguous values are open-vocabulary and belong to a model. The model proposes a record and the validator admits or rejects it. A rejection is never overturned by re-asking without a bound, and a validation pass is never mistaken for a truth claim.

A team adopting structured memory should start narrow: the few fields that support measured decisions, one transactional store, strict validation, evidence-backed extraction, typed queries with injected scope, and complete telemetry. Schema registries, constrained decoding facilities, vector search, external policy engines, and sophisticated migrations should be added only where each closes a demonstrated gap. Raw episodes should keep what happened, unstructured memory should keep unresolved nuance, and long context should carry bounded one-off interpretation.

**Key Success Factors**:

- **Selection before schema**: A field earns typing only where a decision needs an exact operation, its semantics can be declared, a wrong value is mechanically detectable, and its scope can be stated; everything else stays unstructured until those conditions hold.
- **Deterministic admission**: Every stored value passed a validator that a model cannot override, and no candidate reaches a consumer with a warning attached in place of a pass.
- **Bounded model authority**: The model proposes records and never decides identity, tenancy, authorization, legal basis, sensitivity, or whether a constraint applies, and its retries are capped at 3 attempts with no identical repeat after the same error class.
- **Scope before relevance**: Authorization and hard isolation precede applicability, validity, and ranking on every read path, and cross-context leakage is held at exactly zero rather than mitigated after the fact.
- **History preserved**: Corrections append versions, decay reduces eligibility without rewriting values, and erasure writes a tombstone with an enumerated derivative inventory rather than an in-place delete.
- **Measured gates declared in advance**: Precision, recall, calibration, leakage, idempotency, and migration agreement are gated per harm tier against a frozen adjudicated corpus, and a gate adjusted after its result was observed invalidates the release.

By following this guide, AI agents can hold durable knowledge in a form that is queryable by exact predicate, correctable at field granularity, migratable without loss, and disposable on obligation, so that a record earns production trust only when its shape, value, context, authority, lifecycle, and deletion path are all testable.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. Two exceptions are noted at their entries: the memory-systems survey at entry 4 and the constrained-decoding position at entry 1 were independently corroborated during conversion research, and current reporting on enterprise query-generation accuracy cited in Section V was retrieved during that research rather than taken from the prose source.

**Corpus pointers**:

- `Contextual Structured Memory for AI Agents: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the eligibility-function treatment of context, the canonical record field inventory, the layered validation sequence, the progressive slot-filling model, the typed query and hybrid retrieval discipline, the expand-contract migration procedure, the field-level governance model, the characteristic failure modes, the telemetry field inventory, and the evaluation program. Its external citations are transcribed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — companion guidance on the broad memory taxonomy and the placement of typed records within it, applicable to the selection rule in Section 1.2.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — companion guidance on event boundaries and raw trajectories, which hold the source evidence that Step 5.3 re-extracts against.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on promoting and compacting memory across representations, applicable to the promotion path in Section 1.2 and the decay policy in Step 6.1.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — companion guidance on bounded in-context state, applicable to the projection and context management requirements in Step 4.1 and Section III.A.
- `advanced_task_guides/memory-management/guide_AttentionBasedMemoryRetrieval.md` — companion guidance on salience scoring, the admission threshold, and bounded placement into a prompt, applicable to the semantic retrieval constraints in Step 4.3, where this guide fixes only the eligible population that scoring may range over.
- `advanced_task_guides/memory-management/guide_UnstructuredMemory.md` — the representation this guide is defined against by the selection rule in Section 1.2. It owns free-form bodies retrieved by approximate similarity under a governed metadata envelope; this guide owns content that is queryable by exact predicate, joinable, and validatable against a schema before admission.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — owns the operation contract for a single read and a single write, including gate ordering, idempotency, and terminal states, applicable to the versioned idempotent commit in Step 3.1.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — owns retention policy and the separation of utility forgetting from obligation erasure, including the coverage proof an erasure case requires; applicable to the retention binding in Step 6.1 and the erasure cascade in Step 6.2.
- `advanced_task_guides/knowledge-graphs/guide_KG_SchemaDesign.md` — companion guidance on schema construction and evolution where relation semantics and traversal are required, which lie outside the record layer this guide governs.
- `advanced_task_guides/knowledge-graphs/guide_KG_EntityResolutionDedup.md` — companion guidance on identity resolution, applicable to the residual adjudication population in Step 3.2.
- `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md` — companion guidance on provenance modelling, applicable to the provenance fields in Step 1.3.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design and instrumentation, applicable to the logging requirements in Step 6.3.
- `advanced_task_guides/policy-risk/guide_InformationDependencyDisclosureRiskAnalysis.md` — companion guidance on disclosure risk, applicable to the aggregation risk limitation in Section V and the audience scope rules in Section 1.4.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control loops and escalation, applicable to the retry bounds and halting rules in Section 1.3.

**External references**: The numbering below is the numbering used by the inline markers in Sections I and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Structured output, extraction, and abstention*

1. *Structured-output reliability study* — https://arxiv.org/abs/2606.09395. The position that structural controls do not eliminate semantic error was independently corroborated during conversion research.
2. *SLOT* — https://arxiv.org/abs/2505.04016
3. *BEAVER* — https://arxiv.org/abs/2409.02038
4. *Anatomy of Agentic Memory* — https://arxiv.org/abs/2602.19320. Confirmed to exist during conversion research.
5. Association for Computational Linguistics, *Survey of abstention in large language models* — https://aclanthology.org/2025.tacl-1.26/

*Schema definition and validation*

6. JSON Schema, *Specification* — https://json-schema.org/specification
7. Pydantic, *Strict mode* — https://pydantic.dev/docs/validation/latest/concepts/strict_mode/
8. Zod, *TypeScript-first schema validation* — https://zod.dev/
9. Protocol Buffers, *Language guide* — https://protobuf.dev/programming-guides/proto3/
10. Apache Avro, *Specification* — https://avro.apache.org/docs/current/specification/
11. Confluent, *Schema evolution and compatibility* — https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html

*Storage, constraints, and migration*

12. PostgreSQL, *JSON types* — https://www.postgresql.org/docs/current/datatype-json.html
13. PostgreSQL, *Constraints* — https://www.postgresql.org/docs/current/ddl-constraints.html
14. PostgreSQL, *Row security policies* — https://www.postgresql.org/docs/current/ddl-rowsecurity.html
15. Alembic, *Autogenerating migrations* — https://alembic.sqlalchemy.org/en/latest/autogenerate.html
16. Flyway, *Versioned migrations* — https://documentation.red-gate.com/fd/versioned-migrations-273973333.html

*Constrained generation and tool contracts*

17. OpenAI, *Structured Outputs* — https://developers.openai.com/api/docs/guides/structured-outputs
18. Anthropic, *Defining tools* — https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
19. Outlines, *Structured generation* — https://dottxt-ai.github.io/outlines/latest/reference/generation/structured_generation_explanation/
20. llama.cpp, *Grammars* — https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md
21. XGrammar — https://xgrammar.mlc.ai/

*Retrieval and metadata filtering*

22. pgvector — https://github.com/pgvector/pgvector
23. Pinecone, *Filter by metadata* — https://docs.pinecone.io/guides/search/filter-by-metadata
24. Qdrant, *Filtering* — https://qdrant.tech/documentation/concepts/filtering/

*Memory stores and context surfaces*

25. LangGraph, *Stores* — https://docs.langchain.com/oss/python/langgraph/stores
26. Letta, *Memory blocks* — https://docs.letta.com/v1-sdk/memory/memory-blocks/
27. Mem0, *Metadata filtering* — https://docs.mem0.ai/open-source/features/metadata-filtering
28. LlamaIndex, *Metadata filtering* — https://developers.llamaindex.ai/typescript/framework/modules/rag/query_engines/metadata_filtering/
29. Model Context Protocol, *Resources* — https://modelcontextprotocol.io/specification/2026-07-28/server/resources
30. OpenAI, *Context personalization pattern* — https://developers.openai.com/cookbook/examples/agents_sdk/context_personalization

*Authorization, governance, and telemetry*

31. Open Policy Agent, *Documentation* — https://openpolicyagent.org/docs
32. Cedar, *Authorization* — https://docs.cedarpolicy.com/auth/authorization.html
33. Information Commissioner's Office, *Data minimisation* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/data-minimisation/
34. Information Commissioner's Office, *Purpose limitation* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/purpose-limitation/
35. Information Commissioner's Office, *Right to rectification* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-rectification/
36. Information Commissioner's Office, *Right to erasure* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/
37. OpenTelemetry, *Generative AI semantic conventions* — https://opentelemetry.io/docs/specs/semconv/gen-ai/
