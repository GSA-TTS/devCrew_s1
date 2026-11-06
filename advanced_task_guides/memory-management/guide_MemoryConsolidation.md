# Memory Consolidation

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Memory consolidation constitutes the task family of converting accumulated raw episodes into fewer, more durable, higher-order memory records that later retrieval treats as established knowledge. This guide provides AI agents with a structured protocol for running that conversion as an evidence-gated promotion pipeline rather than as a compression job: grouping episodes by entity, task, and validity period; deduplicating without inflating support; detecting contradictions explicitly instead of averaging them away; generating candidate summaries and facts that carry their provenance forward; and admitting candidates to durable memory only through a gate that software closes rather than a model. It names the central hazard the pipeline exists to contain, which is error laundering: the conversion of many low-confidence and possibly wrong episodes into a small number of confident-looking records that no longer carry the uncertainty of their inputs and that are subsequently retrieved as fact. Four countermeasures are carried as first-class procedure: provenance preservation through every consolidation step, explicit contradiction detection, a confidence propagation rule capping a consolidated record at what its evidence supports, and a promotion gate with a verification requirement and a numeric threshold. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that durable memory grows in accuracy rather than only in volume.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Episode**: One immutable record of something that happened, carrying its content, its observation time, its source, its tenant and purpose scope, and an identifier that never changes. Episodes are written once and never edited; a correction is a new episode that references the one it corrects.

**Consolidation**: The scheduled, usually offline transformation of a snapshotted set of episodes into fewer, more durable records of a different epistemic status. Consolidation is not ordinary memory writing, not tier movement, and not deletion.

**Consolidated record**: A durable memory artifact produced by consolidation, such as a scoped summary, an atomic fact, a preference entry, a procedure, or an index generation. Every consolidated record is a versioned hypothesis derived from immutable evidence, not a truth created by repetition.

**Candidate**: A consolidated record that has been generated but not admitted to durable memory. Candidates are ineligible for general retrieval and carry no authority over agent behaviour.

**Promotion**: The transition of a candidate to a published version that general retrieval may return. Promotion is a decision, not a write; it is the point at which epistemic status changes.

**Promotion gate**: The set of mechanical checks and verification requirements that a candidate must satisfy before promotion. The gate is owned by software and is the only path from candidate to published.

**Provenance link**: A typed, immutable edge from one consolidated record version to one exact source version, naming the evidence span, the relation (`supports`, `contradicts`, `derived_from`, `validated_by`), and the run that created it. A link that points at a mutable identifier rather than a version is a broken link.

**Provenance family**: The set of episodes that trace to one original observation, including its copies, quotations, forwards, and model restatements. Members of one family are one piece of evidence regardless of how many times they appear.

**Support count**: The number of episodes in a group asserting the same content. Support count measures repetition.

**Independent support count**: The number of distinct provenance families asserting the same content. Independent support count measures corroboration. Support count and independent support count are recorded separately and are never conflated.

**Validity interval**: The half-open period during which a record's assertion is claimed to hold, expressed as a valid-from time and an optional valid-to time, kept distinct from the time the system learned it.

**Contradiction**: Two records sharing an entity and a predicate whose validity intervals overlap and whose values differ beyond the field's declared tolerance. A contradiction is a state to be detected and adjudicated, never a value to be averaged.

**Error laundering**: The failure mode in which consolidation strips the uncertainty, disagreement, and hedging present in its inputs and emits a record whose surface form asserts more than its evidence supports. Laundering is invisible after promotion because the retrieved record no longer displays what it discarded.

**Confidence ceiling**: The maximum confidence a consolidated record may carry, computed from its independent support count, its source authority, and the calibrated accuracy last observed for its artifact class. A record's stated confidence is the lesser of its proposed confidence and its ceiling.

**Generation depth**: The number of consolidation passes separating a record from a generation-zero episode. A summary of episodes has depth 1; a summary of summaries has depth 2.

**Consequence class**: The declared severity tier of the decisions a record may influence, drawn from low, moderate, and high. Consequence class sets the promotion threshold, the verification requirement, and whether human approval is mandatory.

**Frozen holdout**: An adjudicated evaluation corpus of source-grounded questions, exact identifiers, chronology probes, contradictions, rare events, and negative cases, split by provenance family and frozen before any threshold is tuned.

**Rollback**: Atomic restoration of the serving pointer to a prior published version, followed by cache invalidation and proof that the withdrawn version is no longer retrieved.

**Invalidation cascade**: The traversal of outgoing dependency edges from a corrected, retracted, or erased source through every record derived from it, tombstoning each from serving before re-derivation.

### 1.2 Error Laundering and Its Four Countermeasures

Consolidation is valuable because it reduces many uncertain records to few reusable ones. That same reduction is the mechanism of its principal failure. Twenty episodes, each individually hedged, individually low-confidence, and several of them wrong, become one fluent paragraph or one typed fact. The hedges do not survive summarisation, the disagreement is resolved by whichever value the generator found most salient, and the wrongness is no longer visible because the sources are no longer in view. From the moment of promotion, retrieval returns the laundered record and every downstream agent treats it as established. The laundering is not detectable by reading the output, because a laundered record and a well-supported record look identical.

Four countermeasures address this, and each is carried as procedure in the Operational Framework rather than as advice.

**Provenance preservation through every step**: Every consolidation step preserves the mapping from output to input. Grouping records which episodes entered which group, deduplication records which episodes collapsed into which survivor and why, and generation records which evidence span supports which assertion in the output. A consolidated record that cannot enumerate its sources at span granularity is not admissible, regardless of how good it looks. This is enforced in Step 4.2 as a completeness check with a numeric threshold, not as a best effort.

**Explicit contradiction detection**: Disagreement among episodes is found by deterministic comparison before any summary is written, and is adjudicated by a named procedure with a recorded verdict. Silent averaging, last-writer-wins, and majority-by-repetition are prohibited resolution strategies because each produces a confident record from conflicting evidence while destroying the record of the conflict. Where adjudication cannot resolve a contradiction, the candidate is blocked, not softened. This is Phase 3.

**Confidence propagation**: A consolidated record can never carry more confidence than its evidence supports. Confidence does not rise because content was restated, because the generator was fluent, or because the group was large. The propagation rule in Step 4.3 computes a ceiling from independent support count, source authority, and the calibrated accuracy last measured for the artifact class, and caps the record at that ceiling and at the maximum confidence of its inputs, whichever is lower.

**A promotion gate with verification and a numeric threshold**: Generation authority and publication authority are held by different components. The component that writes the candidate cannot publish it. Publication requires that mechanical checks pass, that the record clears a numeric threshold set by its consequence class, and that a verification requirement is satisfied against a frozen holdout rather than against the model's own assessment. This is Phase 5.

### 1.3 Scope: The Agent-Layer Surrogate for Systems Consolidation

The originating literature frames consolidation biologically. In that framing, new experience is initially held by a fast, high-plasticity system and is progressively reorganised into a slower, more integrated store, with offline replay revisiting experience and retrieval rendering a trace temporarily labile [1][3][5]. A second line of the same literature proposes the direct computational analogue: consolidating accumulated experience into model weights through fine-tuning, parameter-efficient fine-tuning, or knowledge editing [12][13].

Neither mechanism is executable at the AI Agent layer. Biological consolidation is not a procedure an agent can invoke, and weight modification is not an operation an agent performs at runtime through prompting, tool calls, or store operations. This guide therefore scopes to the external-memory surrogate, which is fully executable and which reproduces the architectural properties that make the biological account useful:

- **Fast store separated from durable store**: An append-only episode store accepts writes cheaply and without adjudication; a conservative consolidated store accepts records only through the promotion gate. Separation is what allows a wrong episode to be recorded without becoming a wrong belief.
- **Offline revision rather than write-time adjudication**: Consolidation runs on a schedule against a snapshot, not on the write path, so foreground latency is unaffected and evidence has time to settle.
- **Versioned reads rather than mutation on retrieval**: Retrieving a record never modifies it. New evidence produces a successor version and retains the predecessor, which preserves the audit trail the biological metaphor otherwise invites systems to discard.

Parametric promotion is treated here as a bounded referral case. Where a deployment does elect to move stable, high-reuse knowledge into weights, the agent layer's role is limited to producing the approved external artifact, its dataset lineage, its evaluation corpus, and its retirement plan, and to gating that artifact through the same promotion procedure specified below. The training or editing operation itself, its regression and forgetting behaviour, and its unlearning obligations sit below this guide's scope and must be governed by a separate specification. An agent must never treat a fine-tuned behaviour as a consolidated record it can inspect, cite, correct, or roll back by pointer switch, because it cannot.

### 1.4 The Execution Tier Partition

The partition of consolidation work across execution tiers is the principal thing separating an operational consolidation pipeline from a prose description of one. Assignment is not stylistic. Work that requires exactness, reproducibility, auditability, or scale belongs to the deterministic tier, because model inference supplies none of those properties. Work that requires open-vocabulary judgement belongs to the model tier, because no deterministic rule covers it. Work where one tier proposes and the other verifies belongs to the hybrid tier, and every hybrid assignment names which component holds authority when the two disagree.

The governing rule for this method is stated once and enforced throughout: **the model tier may propose a consolidated record but may never promote one**. The generator holds no write access to the published store, no ability to set a record's final confidence, and no vote in the promotion decision. Publication is a deterministic operation conditioned on checks that software evaluates.

**Execution Tier Assignment for Consolidation Work**

| Work unit | Owning tier | What the tier does | Authority on disagreement |
| :-- | :-- | :-- | :-- |
| Trigger evaluation and run scheduling | Deterministic | Evaluates watermarks, staleness targets, and capacity reserves; admits or defers runs | Deterministic; a model never schedules its own run |
| Eligibility, authorization, and purpose filtering | Deterministic | Applies tenant, consent, retention, and policy filters before any content is read | Deterministic; failure is a hard reject |
| Snapshot and manifest construction | Deterministic | Freezes source versions, computes the manifest hash, records inclusion and exclusion reasons | Deterministic |
| Grouping by entity, task, and validity period | Deterministic | Partitions episodes on typed keys and interval overlap | Deterministic |
| Exact and near-exact deduplication | Deterministic | Content hashing, normalized hashing, MinHash, and embedding-neighbour collapse within a partition | Deterministic |
| Provenance family assignment and support counting | Deterministic | Traces ancestry, assigns family identifiers, computes support and independent support counts | Deterministic; a model may not assert independence |
| Semantic clustering where exact match fails | Hybrid | Model proposes cluster membership; software validates each member against the partition keys | Deterministic; rejected members are removed and an over-rejected cluster is dissolved |
| Contradiction detection on typed fields | Deterministic | Compares entity, predicate, interval overlap, and value tolerance | Deterministic |
| Contradiction detection in free text | Hybrid | Model proposes contradiction pairs; software confirms both members exist in the snapshot | Deterministic on existence; model on the semantic claim |
| Contradiction adjudication | Model | Judges whether two assertions genuinely conflict, and which is scoped, superseded, or wrong | Model proposes a verdict; software enforces the blocking rule regardless of the verdict |
| Summary and abstraction generation | Model | Produces the consolidated content under a fixed output schema | Model only; software rejects schema violations without repair |
| Evidence span attribution | Hybrid | Model attaches spans; software verifies each span resolves to a snapshot member | Deterministic; an unresolvable span voids the assertion |
| Confidence proposal | Model | Emits a proposed confidence and its stated basis | Model proposes; software computes the ceiling and takes the minimum |
| Confidence ceiling computation | Deterministic | Applies the propagation rule to independent support, authority, and calibrated accuracy | Deterministic; the ceiling is never overridden |
| Promotion gate mechanical checks | Deterministic | Schema, provenance completeness, contradiction block, independence, ancestry, tenant isolation, threshold comparison | Deterministic; any failed hard check rejects |
| Holdout verification | Deterministic | Executes the frozen evaluation suite and compares scores against gate values | Deterministic |
| Human approval for high consequence | Hybrid | Software routes and blocks; a named human role decides | Human; software records the decision and the content hash approved |
| Publication and alias switch | Deterministic | Writes the immutable version, links lineage, switches the serving pointer atomically | Deterministic |
| Post-promotion audit sampling | Hybrid | Software samples and computes rates; a model or human adjudicates sampled records | Software on the rate; adjudicator on the individual record |
| Rollback and invalidation cascade | Deterministic | Restores the pointer, traverses dependencies, tombstones, verifies residual serves | Deterministic; a model never decides that a rollback is unnecessary |

Two consequences of this partition are load-bearing. First, every phase of the Operational Framework is assignable to a tier, and every step that mixes tiers names the handoff explicitly in its actions. Second, the deterministic tier's rejections are not advisory. A candidate failing a hard mechanical check is rejected without a model being consulted, because consulting a model about whether its own output should be published reintroduces exactly the self-approval the partition exists to prevent [24][25].

***

## II. Operational Framework: Evidence-Gated Promotion of Raw Episodes Into Durable Memory

The framework consumes a bounded set of immutable episodes and produces versioned consolidated records admitted to durable memory. Phases 1 through 5 run in sequence within one consolidation run. Phase 6 runs continuously against records already promoted and returns control to Phase 1 when it triggers a re-derivation. Each phase names the execution tier that owns its work, and each step that crosses tiers names the handoff.

### Phase 1: Consolidation Scheduling and Candidate Selection

**Objective**: Decide that a consolidation run is warranted, bound its scope, and freeze an immutable authorized snapshot of the episodes it will operate on, so that the run is reproducible and its blast radius is known before any content is read.

#### Step 1.1: Declare the Consolidation Contract and Artifact Classes

**Required Actions**:

- Name every artifact class the run may produce, and reject any run whose output class is undeclared.
- Assign each artifact class a consequence class from low, moderate, and high, based on the severity of the decisions the record may influence rather than on the effort of producing it.
- Record per class the minimum proof obligation, the owning validator, the human approver where one is required, the freshness target, the retention rule, and the rollback target.
- State the counterfactual for each class: the no-consolidation baseline of raw retrieval, and the simple deterministic baseline of exact deduplication plus fixed-scope summaries.
- Declare the break-even reuse count as total lifecycle cost divided by expected net saving per eligible use, and refuse to run a class whose denominator is zero or negative.

**Consolidation Artifact Classes and Proof Obligations**

| Artifact class | What the record asserts | Minimum proof obligation | Default consequence class |
| :-- | :-- | :-- | :-- |
| Deduplicated episode set | These episodes are copies of one another | Exact or near-exact match evidence per collapse, with reference counts preserved | Low |
| Scoped summary | This is what the grouped episodes said, within a declared scope | Answer preservation on holdout questions, zero unsupported critical claims, retained contradictions | Low |
| Atomic fact | This proposition holds for this entity over this interval | Authoritative source, or 2 or more independent provenance families, with no blocking contradiction | Moderate |
| Preference or profile record | This subject durably prefers this | Direct statement distinguished from inferred behaviour, consent and purpose scope, subject-inspectable | Moderate |
| Procedure or workflow record | These ordered steps achieve this outcome | Support across 3 or more distinct tasks, verified outcomes, negative examples, sandbox execution | High |
| Reflection or inferred relationship | This higher-order pattern explains these episodes | Sentence-level evidence links, counterexample search, expiry, an inferred label, holdout testing | High |
| Index generation | This derived view retrieves the same corpus | Document count parity, authorization filter correctness, shadow retrieval comparison | Low |

**Required Outputs**:

- A consolidation contract naming every permitted artifact class with its consequence class and proof obligation.
- A validator and approver assignment per class.
- A baseline declaration naming the no-consolidation and simple deterministic comparators.
- A break-even reuse figure per class with its cost and saving components itemised.

**Quality Checkpoints**:

- Every declared class carries a proof obligation, a validator, a freshness target, and a rollback target; a class missing any of the four is removed from the run.
- Consequence class is assigned before generation, not inferred afterwards from what the record turned out to say.
- No class is admitted whose expected lifetime saving is below its lifecycle cost.

***

#### Step 1.2: Configure Triggers, Batches, and Backpressure

**Required Actions**:

- Select the trigger type per class from event-driven, periodic, budget-pressure, and idle-window, and record the choice with its rationale.
- Set the settling window so that episodes younger than 24 hours are excluded from consolidation, allowing corrections and late-arriving evidence to land before the snapshot is taken.
- Set the staleness target as the maximum tolerable age of unconsolidated eligible evidence, defaulting to 7 days, and raise an alert rather than silently deferring when the oldest eligible item exceeds 4 times that target.
- Bound each work item to no more than 500 episodes or 400,000 input tokens, whichever binds first, and never allow a work item to span more than 1 tenant.
- Apply hysteresis to capacity admission: admit consolidation work only while foreground utilisation is at or below 60 percent, and halt admission when it rises above 75 percent, so the pipeline does not oscillate against serving traffic.
- Derive the idempotency key from the source snapshot identifier and the pipeline version, so that at-least-once delivery produces exactly 1 logical effect.
- Cap retries at 3 attempts with exponential backoff and jitter, and dead-letter any work item whose age exceeds 24 hours.

**Required Outputs**:

- A trigger configuration per artifact class with its watermarks and cadence.
- A batch policy stating episode, token, and tenant limits.
- A backpressure policy stating admission and halt watermarks, retry bounds, and dead-letter conditions.
- An idempotency key specification with its component fields.

**Quality Checkpoints**:

- Every trigger has both a start and a stop condition; a trigger without a stop condition is rejected because it cannot be prevented from competing with serving.
- Budget pressure never bypasses an evidence gate; a run admitted under pressure applies the same promotion thresholds as a scheduled run.
- Crash and restart of a worker mid-run produces no duplicate published version, verified by replaying the idempotency key.
- No work item spans more than 1 tenant in its sources, queues, temporary files, model batches, or caches.

***

#### Step 1.3: Select and Snapshot the Eligible Episode Set

**Required Actions**:

- Apply authorization, consent, purpose, and retention filters before any relevance selection, so that ineligible content is never read by the consolidator.
- Select candidate episodes by the declared partition keys of entity, task class, and validity period rather than by embedding similarity alone, since similarity selection admits content the partition would exclude.
- Include negative outcomes, rare events, and known counterevidence in the selection deliberately, because relevance ranking systematically omits them and their omission is a common cause of an over-confident summary.
- Scan every selected episode for instruction-like text, hidden Unicode, encoded payloads, provenance breaks, and cross-tenant references, and quarantine rather than sanitise anything that trips a detector [22][23].
- Freeze an immutable snapshot recording every source version identifier, the selection query hash, the inclusion reason per member, the exclusion reason per rejected candidate, and a manifest hash over the whole set.

**Required Outputs**:

- An authorized episode set with one eligibility verdict per candidate.
- A snapshot manifest with source version identifiers, selection query hash, and manifest hash.
- An inclusion and exclusion record with a reason code per decision.
- A quarantine set holding suspect episodes with their tripped detector named.

**Quality Checkpoints**:

- Authorization precedes relevance in the selection order; a pipeline that filters after ranking fails this checkpoint.
- The manifest hash reproduces exactly when the selection is replayed against the same source versions.
- Every selected episode resolves to an immutable version identifier; a reference to a mutable identifier blocks the run.
- Rare and negative cases present in the eligible population appear in the selection, and their absence is recorded as an explicit exclusion with a reason rather than passing unnoticed.
- No quarantined episode enters the snapshot, and quarantine is never resolved by the same component that generates candidates.

***

### Phase 2: Grouping and Deduplication

**Objective**: Partition the snapshot into groups that share a subject and a time window, and collapse the copies within each group without allowing repetition to be recorded as corroboration.

#### Step 2.1: Partition Episodes by Entity, Task, and Validity Period

**Required Actions**:

- Assign every episode a partition key composed of its resolved entity identifier, its task class, and the validity period bucket its assertion falls in.
- Resolve entity identifiers against the canonical identifier store rather than against surface strings, and route unresolvable references to a separate unresolved partition rather than guessing.
- Bucket validity periods so that two assertions land in the same bucket only where their intervals overlap; assertions about disjoint intervals are never grouped and therefore never contradict.
- Keep the transaction time at which the system learned each episode distinct from the valid time its assertion claims, since conflating them makes a corrected fact indistinguishable from a changed fact [26].
- Record group membership as an explicit list of episode version identifiers, so that grouping itself is auditable and reversible.

**Required Outputs**:

- A partition assignment per episode with its three key components named.
- A group inventory listing every group with its member episode versions and its interval bounds.
- An unresolved partition holding episodes whose entity could not be resolved, with the failing resolution step recorded.

**Quality Checkpoints**:

- Every episode in the snapshot appears in exactly 1 group or in the unresolved partition; an episode appearing in 2 groups is a partitioning defect that halts the phase.
- No group spans disjoint validity intervals, so interval overlap is a precondition of membership rather than a property discovered later.
- Entity resolution operates on canonical identifiers; string-similarity resolution is recorded as a proposal requiring confirmation, never as a resolved identity.
- Valid time and transaction time are separately populated on every member; a missing transaction time blocks the group from proceeding.

***

#### Step 2.2: Collapse Exact and Near-Exact Duplicates Without Inflating Support

**Required Actions**:

- Compute a content hash and a normalized content hash for every episode, and collapse byte-identical and canonically identical members to 1 survivor while preserving the reference count.
- Detect near-exact textual duplicates within a group by MinHash Jaccard similarity at or above 0.85, and near-exact semantic duplicates by embedding cosine similarity at or above 0.92, applying both only inside an existing partition so similarity never crosses an entity or interval boundary.
- Trace ancestry for every member and assign a provenance family identifier, so that quotations, forwards, and model restatements of one original resolve to 1 family.
- Increment support count for every member collapsed, and increment independent support count only where the member belongs to a provenance family not already represented in the group.
- Preserve the strongest available source, every distinct family link, every recorded disagreement, and a reversible merge record naming what was collapsed into what and by which rule.

**Duplicate Classes and Their Effect on Support**

| Duplicate class | Detection method | Owning tier | Support count effect | Independent support effect |
| :-- | :-- | :-- | :-- | :-- |
| Byte-identical | Content hash equality | Deterministic | Plus 1 | Plus 0 |
| Canonically identical | Normalized hash equality after whitespace, case, and encoding normalisation | Deterministic | Plus 1 | Plus 0 |
| Near-exact textual | MinHash Jaccard at or above 0.85 within a partition | Deterministic | Plus 1 | Plus 0 |
| Near-exact semantic | Embedding cosine at or above 0.92 within a partition | Deterministic | Plus 1 | Plus 0 |
| Restatement by a model | Provenance ancestry resolves to an existing family | Deterministic | Plus 1 | Plus 0 |
| Distinct observation of one event | Same event identifier, different observer, different family | Hybrid | Plus 1 | Plus 1 |
| Independent assertion | Different provenance family, no shared ancestor | Deterministic | Plus 1 | Plus 1 |

**Required Outputs**:

- A deduplicated group set with 1 survivor per duplicate cluster and its reference count preserved.
- A merge record per collapse naming the rule applied, the survivor, and every collapsed member.
- A support ledger per group carrying support count and independent support count as separate fields.
- A provenance family assignment per surviving member.

**Quality Checkpoints**:

- Support count and independent support count are stored in separate fields and are never summed, averaged, or substituted for one another.
- No collapse raises independent support count; a collapse that does is a defect in family assignment and blocks the group.
- Every merge is reversible from its merge record without consulting the original run.
- Rare failure episodes are never collapsed into a dominant success cluster; a proposed collapse crossing an outcome boundary is rejected and recorded.
- Near-exact detection runs inside partitions only; a similarity match crossing a partition boundary is discarded rather than promoted to a merge.

***

#### Step 2.3: Cluster Residual Episodes Semantically Under Deterministic Constraints

**Required Actions**:

- Pass only the residual members that exact and near-exact matching failed to group to the model tier, with the partition keys attached as constraints rather than as hints.
- Require the model tier to return proposed cluster membership as a typed structure naming each member episode version and the shared assertion it is claimed to express.
- Validate each proposed member deterministically against the partition keys, the interval overlap rule, and the tenant boundary, and remove any member failing validation.
- Dissolve any proposed cluster from which more than 20 percent of members were removed by validation, and return its members to the unclustered residual rather than accepting a weakened cluster.
- Record every proposal, every removal, and every dissolution, so that the model tier's clustering accuracy is measurable rather than assumed.

**Required Outputs**:

- A validated semantic cluster set with per-member validation verdicts.
- A rejection record naming every removed member and the constraint it failed.
- A dissolution record naming every cluster dissolved and its removal rate.
- A residual set of episodes that remain unclustered after the pass.

**Quality Checkpoints**:

- The model tier proposes membership and never writes it; every accepted member carries a deterministic validation verdict.
- No cluster survives with a validation removal rate above 20 percent.
- Semantic clustering is applied only to residuals; it never overrides an exact or near-exact grouping already established.
- Unclustered residuals are retained and reported rather than discarded, since a residual is unconsolidated evidence and not noise.

***

### Phase 3: Contradiction Detection and Resolution

**Objective**: Find every disagreement inside a group before any summary is written, adjudicate it through a named procedure with a recorded verdict, and block promotion where adjudication does not resolve it.

#### Step 3.1: Detect Contradictions Deterministically Within Each Group

**Required Actions**:

- Compare every pair of typed assertions within a group on entity, predicate, validity interval overlap, and value, and mark a contradiction where the entities and predicates match, the intervals overlap, and the values differ beyond the field's declared tolerance.
- Set the tolerance per field type before the run: exact equality for identifiers and categorical values, the field's declared precision for measured quantities, and 1 percent relative difference as the default for unlabelled numeric fields.
- Detect polarity conflicts, where one assertion negates another, as a distinct class from value conflicts, since the two carry different resolution options.
- Pass free-text assertions that carry no typed fields to the model tier for contradiction proposal, and confirm deterministically that both proposed members exist in the snapshot before recording the pair.
- Compute the group's contradiction rate as contradicted groups divided by total groups in the batch, and the batch's unresolved contradiction rate after adjudication.

**Contradiction Classes and Permitted Resolutions**

| Contradiction class | Deterministic signature | Permitted resolutions | Blocking by default |
| :-- | :-- | :-- | :-- |
| Value conflict | Same entity, same predicate, overlapping interval, differing value | Supersede by recency where an authority ordering exists; split the interval; block | Yes |
| Polarity conflict | One assertion negates the other over an overlapping interval | Scope narrowing where the negation applies to a subcase; block | Yes |
| Interval conflict | Same assertion with incompatible valid-from or valid-to bounds | Widen to the union where both sources are authoritative; split; block | Yes |
| Scope mismatch | Assertions differ because one is narrower than the other | Retain both with explicit scopes; never merge into one value | No |
| Authority conflict | Authoritative and non-authoritative sources disagree | Prefer the authoritative source and retain the dissent as counterevidence | No |
| Supersession | Later assertion invalidates an earlier one and both are authoritative | Close the earlier interval, open the later, retain both versions | No |
| Unexplained conflict | Conflict survives every resolution rule | Quarantine the group; escalate | Yes |

**Required Outputs**:

- A contradiction inventory listing every detected pair with its class and its signature.
- A tolerance specification per field type used in the comparison.
- A contradiction rate figure for the batch, computed before adjudication.
- A model-proposed contradiction set with existence confirmation per member.

**Quality Checkpoints**:

- Detection runs before generation; a pipeline that generates a summary and then looks for conflicts in it fails this checkpoint.
- Every detected contradiction carries a class drawn from the closed vocabulary above; an unclassified contradiction is treated as unexplained and blocks.
- Numeric comparison uses a declared tolerance rather than string equality, so a rounding difference is not recorded as a conflict and a material difference is not missed.
- Model-proposed contradictions are confirmed to reference real snapshot members; an unresolvable member voids the proposal.

***

#### Step 3.2: Adjudicate Contradictions With Explicit Outcomes

**Required Actions**:

- Route each detected contradiction to the model tier with both assertions, their sources, their authorities, their intervals, and the class assigned by detection.
- Require the adjudicator to return one verdict from the closed vocabulary of supersede, split interval, narrow scope, prefer authority, retain both, and unresolved, together with the evidence supporting the verdict.
- Prohibit averaging, last-writer-wins, majority-by-repetition, and silent omission as resolution outcomes, and reject any verdict whose stated basis is the frequency of one value rather than the authority or recency of its source.
- Retain the losing assertion as linked counterevidence on the surviving record rather than deleting it, so that the disagreement remains visible to any later audit.
- Enforce the blocking rule in software after the verdict is returned, since the adjudicator's verdict is a proposal and the blocking decision is not the adjudicator's to make.

**Adjudication Verdict Record**

```
CONTRADICTION_ID:
GROUP_ID:
CLASS:              VALUE | POLARITY | INTERVAL | SCOPE |
                    AUTHORITY | SUPERSESSION | UNEXPLAINED
ASSERTION_A_VERSION:
ASSERTION_B_VERSION:
FAMILY_A:
FAMILY_B:
AUTHORITY_A:
AUTHORITY_B:
INTERVAL_OVERLAP:
VERDICT:            SUPERSEDE | SPLIT_INTERVAL | NARROW_SCOPE |
                    PREFER_AUTHORITY | RETAIN_BOTH | UNRESOLVED
VERDICT_BASIS:      AUTHORITY | RECENCY | SCOPE | EXTERNAL_TEST
COUNTEREVIDENCE_RETAINED:
BLOCKING_DECISION:  SET_BY_SOFTWARE
ADJUDICATOR_ID:
ADJUDICATED_AT:
```

**Required Outputs**:

- An adjudication record per contradiction carrying the verdict, its basis, and the retained counterevidence.
- A counterevidence link set attached to every surviving assertion whose competitor was not deleted.
- A rejected-verdict record naming every verdict refused for citing frequency as its basis.

**Quality Checkpoints**:

- Every verdict is drawn from the closed vocabulary; a free-text verdict is rejected because it cannot be aggregated or audited.
- No verdict cites repetition count as its basis; frequency is never a resolution basis because duplicate copies were already collapsed in Step 2.2.
- The losing assertion is retained and linked on 100 percent of resolved contradictions; a deleted competitor is a laundering event and halts the group.
- The blocking decision is recorded as set by software, never by the adjudicator.

***

#### Step 3.3: Enforce the Contradiction Halt and Quarantine Rules

**Required Actions**:

- Block promotion of any candidate whose group carries an unresolved contradiction of a blocking class, regardless of how well the candidate scores on every other gate condition.
- Halt the entire consolidation run where the batch's unresolved contradiction rate exceeds 15 percent, since a rate that high indicates an upstream extraction, entity-resolution, or source defect rather than genuine disagreement among sources.
- Halt the run where the batch's contradiction rate exceeds 2 times the trailing median of the last 30 runs for the same artifact class, even when the absolute rate is below 15 percent, because a sudden rise is a change in the input population rather than in the world.
- Quarantine, rather than reject, any group whose contradiction is accompanied by an injection detector hit, a provenance break, a cross-tenant reference, or an unexplained outcome mismatch, and route the quarantine to a component distinct from the consolidator.
- Record every halt with its triggering rate, its comparison basis, and the batch identifier, so that halts are analysable rather than merely disruptive.

**Required Outputs**:

- A blocked-candidate list naming every candidate blocked by an unresolved contradiction.
- A halt record where a threshold was breached, carrying the rate, the threshold, and the comparison basis.
- A quarantine queue holding suspect groups with their tripped condition named.

**Quality Checkpoints**:

- A blocking contradiction overrides every other gate result; no aggregate score compensates for it.
- The 15 percent unresolved rate and the 2 times median rise are both evaluated on every run, and a breach of either halts.
- Quarantined groups are adjudicated by a component distinct from the one that generated their candidates.
- Halts are recorded with their evidence and are never cleared by re-running the same batch with the same configuration.

***

### Phase 4: Abstraction and Candidate Generation

**Objective**: Produce the consolidated content for each surviving group under a fixed output schema, attach a resolvable evidence span to every assertion it makes, and cap its stated confidence at what its evidence supports.

#### Step 4.1: Generate the Consolidated Candidate Under a Fixed Output Schema

**Required Actions**:

- Invoke the consolidator with a pinned model identifier, a versioned prompt, a fixed structured output schema, least-privilege tool permissions, no outbound network access, and no write access to the published store.
- Present source content inside explicit content delimiters and treat it as data, never as instruction, since a summarisation step is a well-documented laundering path for instructions embedded in untrusted sources [22][23].
- Require the output to carry, per assertion, the assertion text, its evidence span identifiers, its validity interval, its proposed confidence, and its stated uncertainty.
- Require the output to carry, per candidate, the retained contradictions, the counterevidence links, the categories deliberately omitted, and the generation depth.
- Reject a schema-invalid output outright rather than repairing it, because a repaired output no longer corresponds to what the generator asserted and its provenance becomes unverifiable.
- Write every output to the candidate store only, with state `candidate`, ineligible for general retrieval.

**Required Outputs**:

- A candidate record per group conforming to the declared output schema.
- A generation manifest naming the model identifier, prompt version, schema version, and snapshot manifest hash.
- A schema rejection record naming every output refused and the field that failed.

**Quality Checkpoints**:

- The consolidator holds no publication authority; a pipeline in which the generating component can write to the published store fails this checkpoint at design review, not at runtime.
- Every candidate is written with state `candidate` and is unreachable by general retrieval until Phase 5 completes.
- Schema-invalid outputs are rejected and counted; none is repaired into validity.
- Retained contradictions and omitted categories are populated on every candidate, since an empty omissions field on a compressive summary is itself a laundering signal.
- Source content never reaches the consolidator outside content delimiters.

***

#### Step 4.2: Preserve Provenance Through the Abstraction Step

**Required Actions**:

- Create one immutable provenance link per assertion per supporting source, naming the exact source version, the evidence span within it, the relation type, and the transformation run identifier.
- Verify deterministically that every declared evidence span resolves to a member of the frozen snapshot, and void any assertion whose span does not resolve.
- Link counterevidence with the relation `contradicts` rather than omitting it, so that a later reader can reconstruct what the candidate disagreed with as well as what supported it.
- Compute provenance completeness as the proportion of assertions in the candidate carrying at least 1 resolvable supporting link, and require 100 percent for every artifact class.
- Reject any link that points at a mutable identifier, crosses a tenant boundary, or closes a cycle in the lineage graph.

**Consolidated Record Provenance Block**

```
CANDIDATE_VERSION_ID:
ARTIFACT_CLASS:
GENERATION_DEPTH:
SNAPSHOT_MANIFEST_HASH:
ASSERTION_ID:
  TEXT:
  VALID_FROM:
  VALID_TO:
  SUPPORTING_LINKS:
    - SOURCE_VERSION_ID:
      EVIDENCE_SPAN_ID:
      PROVENANCE_FAMILY_ID:
      SOURCE_AUTHORITY:
      RELATION:            supports
  CONTRADICTING_LINKS:
    - SOURCE_VERSION_ID:
      EVIDENCE_SPAN_ID:
      PROVENANCE_FAMILY_ID:
      RELATION:            contradicts
  SUPPORT_COUNT:
  INDEPENDENT_SUPPORT_COUNT:
  SYNTHETIC_ANCESTRY_FRACTION:
  PROPOSED_CONFIDENCE:
  CONFIDENCE_CEILING:      SET_BY_SOFTWARE
  FINAL_CONFIDENCE:        SET_BY_SOFTWARE
OMITTED_CATEGORIES:
PROVENANCE_COMPLETENESS:
```

**Required Outputs**:

- A provenance link set covering every assertion in the candidate.
- A span resolution verdict per declared evidence span.
- A provenance completeness figure per candidate.
- A voided-assertion record naming every assertion removed for an unresolvable span.

**Quality Checkpoints**:

- Provenance completeness is 100 percent; a candidate below 100 percent is rejected rather than promoted with a caveat.
- Every link names a source version rather than a source identifier, so that a later edit to the source cannot silently change what the record claims to rest on.
- Counterevidence links are present wherever Phase 3 recorded a retained contradiction; their absence blocks the candidate.
- No link closes a cycle in the lineage graph and no link crosses a tenant boundary.
- The provenance block is stored with the candidate, not reconstructed later from logs, since a reconstructed lineage cannot be distinguished from an invented one.

***

#### Step 4.3: Apply the Confidence Propagation Rule

**Required Actions**:

- Treat the model's proposed confidence as an input to the computation, never as the record's confidence, since a model-stated confidence is generated by the same process that generated the content and carries no independent evidential weight.
- Compute the evidence ceiling from independent support count and source authority: 0.60 where independent support count is 1 and no source is authoritative; 0.75 where it is 2; 0.90 where it is 3 or more; and 0.95 where at least 1 source is authoritative and no blocking contradiction remains.
- Cap the ceiling further at the calibrated accuracy last measured for the artifact class in the most recent post-promotion audit, so that a class whose promoted records were 82 percent correct cannot emit a record claiming 0.90.
- Reduce the ceiling by 0.10 for each generation of depth beyond 1, and set the ceiling to 0 where synthetic ancestry fraction exceeds 0.50, because a record derived mostly from other derived records carries no independent evidence.
- Set the record's final confidence to the minimum of the proposed confidence, the evidence ceiling, and the highest confidence carried by any of its supporting inputs, and record all four values so that the binding constraint is visible.
- Prohibit any confidence value of 1.0 on a consolidated record, since certainty is not a property a derivation can create.

**Required Outputs**:

- A confidence computation record per assertion carrying the proposed value, the evidence ceiling, the input maximum, the final value, and the binding constraint.
- A calibrated accuracy figure per artifact class drawn from the most recent audit.
- A zero-ceiling record naming every assertion suppressed for excessive synthetic ancestry.

**Quality Checkpoints**:

- Final confidence never exceeds the maximum confidence of any supporting input; a consolidated record is never more certain than its evidence.
- Final confidence never exceeds the evidence ceiling, and the ceiling is computed by software from counted evidence rather than proposed by the generator.
- No consolidated record carries a confidence of 1.0.
- The binding constraint is recorded on every assertion, so that a record capped by calibration is distinguishable from one capped by thin evidence.
- Depth and synthetic ancestry penalties are applied before the minimum is taken, not after.

***

### Phase 5: The Promotion Gate

**Objective**: Admit a candidate to durable memory only where mechanical checks pass, a verification requirement is satisfied against evidence the candidate did not produce, and a numeric threshold set by consequence class is cleared.

#### Step 5.1: Run the Mechanical Admissibility Checks

**Required Actions**:

- Evaluate every hard check in software with no model in the path: schema conformance, provenance completeness at 100 percent, contradiction blocking status, independent support count, synthetic ancestry fraction, generation depth, tenant isolation, authorization re-check, and expiry presence.
- Re-run the authorization decision after transformation as well as before selection, because a set of individually permitted sources can yield an aggregate whose disclosure is not permitted.
- Compare the candidate's final confidence against the threshold for its consequence class, and reject rather than downgrade where it falls short.
- Treat every hard check as a veto: reject on the first failure without evaluating a weighted aggregate, since averaging permits a strong score on compression to offset a failure on provenance.
- Record the full check vector on every candidate, passing or failing, so that rejection reasons are analysable across runs.

**Promotion Gate Thresholds by Consequence Class**

| Gate condition | Low | Moderate | High |
| :-- | :-- | :-- | :-- |
| Provenance completeness | 100 percent | 100 percent | 100 percent |
| Independent support count | 1 or more | 2 or more, or 1 authoritative | 3 or more, or 1 authoritative plus 1 corroborating |
| Blocking contradiction present | Rejects | Rejects | Rejects |
| Final confidence at or above | 0.50 | 0.70 | 0.85 |
| Unsupported critical claim count | 0 | 0 | 0 |
| Answer preservation on holdout | 0.90 or above | 0.95 or above | 0.98 or above |
| Counterevidence retention | 0.90 or above | 1.00 | 1.00 |
| Rare-event retention | 0.80 or above | 0.90 or above | 1.00 |
| Synthetic ancestry fraction at or below | 0.50 | 0.35 | 0.20 |
| Generation depth at or below | 3 | 2 | 1 |
| Rollback test passed | Required | Required | Required |
| Human approval | Not required | Required on sample of 10 percent | Required on every record |

**Required Outputs**:

- A check vector per candidate carrying a verdict for every hard check.
- A rejection record naming the first failing check and its measured value.
- A re-authorization verdict computed on the candidate rather than on its sources.

**Quality Checkpoints**:

- No hard check is evaluated by a model, and no model output contributes to a gate verdict.
- Rejection occurs on the first hard failure; no weighted aggregate is computed across hard checks.
- Authorization is evaluated twice, on the source set and on the candidate, and both verdicts are recorded.
- Every rejection carries a measured value alongside its threshold, so that a near miss is distinguishable from a gross failure.

***

#### Step 5.2: Run the Verification Requirement Against a Frozen Holdout

**Required Actions**:

- Execute the frozen holdout suite for the candidate's artifact class, covering source-grounded questions, exact identifier recall, chronology probes, retained contradictions, rare and negative cases, schema-incongruent cases, deletion probes, and injection probes.
- Keep development and holdout provenance families disjoint, since a holdout sharing a family with the training or tuning set measures memorisation rather than preservation.
- Measure answer preservation as the proportion of holdout questions answerable from the consolidated record that were answerable from the source set, and treat any drop on a hard slice as a failure regardless of the aggregate.
- Compare the candidate against both declared baselines, raw retrieval and simple deterministic consolidation, and reject any candidate that does not exceed both on the class's primary metric.
- Verify rollback before publication rather than after, by exercising the pointer switch against a rehearsal target and confirming the withdrawn version is not served.

**Required Outputs**:

- A validation result record carrying per-slice scores and the suite version.
- A leakage check verdict confirming holdout and development families are disjoint.
- A baseline comparison record showing the candidate's margin over both comparators.
- A rollback rehearsal result with the residual serve count observed.

**Quality Checkpoints**:

- Every hard slice passes independently; a favourable aggregate never compensates for a failed slice, because the failed slice is usually the rare case the record was going to be trusted on.
- Holdout and development sets share no provenance family; a shared family voids the validation result.
- The candidate beats both baselines; a candidate that merely matches raw retrieval is rejected because it adds a governance burden with no measured benefit.
- The rollback rehearsal returns a residual serve count of 0 before publication is permitted.

***

#### Step 5.3: Issue the Promotion Decision and Publish a Reversible Version

**Required Actions**:

- Route every high-consequence candidate, and a sampled 10 percent of moderate-consequence candidates, to a qualified human approver with the supporting evidence, the counterevidence, the validator results, and the proposed scope attached.
- Require the approver to approve an immutable content hash rather than editable prose, so that what was reviewed and what is published are provably identical.
- Write the promotion decision with its prior state, next state, policy version, threshold version, decider type, decider identity, reason codes, and eligible scope.
- Publish by writing the immutable artifact version, its justification record, its lineage links, its expiry, and its active alias, then switching the serving pointer atomically and invalidating affected caches and index generations.
- Restrict initial exposure to a shadow phase against baseline traffic followed by a canary cohort, and expand scope only after the canary meets its predeclared release gate.

**Required Outputs**:

- A promotion decision record per candidate with its decider and reason codes.
- A published artifact version with an immutable content hash and an active alias.
- A justification record naming intended use, thresholds applied, supporting and opposing evidence, known omissions, expiry, and rollback target.
- A shadow and canary plan with its release gate and automatic rollback conditions.

**Quality Checkpoints**:

- No candidate reaches the published store without a promotion decision record; a published version with no decision record is treated as an incident.
- The approved content hash matches the published content hash exactly.
- Every published version carries an expiry and a named rollback target; a version without either is withdrawn.
- Serving state and audit state agree after publication, verified by querying the serving path for the withdrawn and the current version.
- Promotion is never granted by the component that generated the candidate, and never by relaxing a threshold to admit a specific record.

***

### Phase 6: Post-Promotion Audit, Rollback, and Economics

**Objective**: Detect laundered records after promotion, withdraw them through a rehearsed rollback with a full invalidation cascade, and retire artifact classes whose measured lifetime value is negative.

#### Step 6.1: Audit Promoted Records Against Their Sources

**Required Actions**:

- Sample promoted records for adjudication at the greater of 5 percent of the class's weekly promotions or 30 records per class per week, so that a low-volume class is still audited at a usable sample size.
- Adjudicate each sampled record against its own linked sources rather than against a model's recollection, and record whether every assertion is supported, partially supported, or unsupported.
- Compute per class the promotion precision as adjudicated-correct records over audited records, and the calibrated accuracy that Step 4.3 will consume as a confidence ceiling on the next run.
- Detect self-confirmation by tracing whether the record's supporting sources include a prior consolidated artifact, and flag any record whose independent external anchor count is 0.
- Monitor per class the correction rate within 30 days of promotion, the stale-serve rate against the freshness target, the answer-flip rate against the frozen holdout, and the tail-coverage delta across generations.
- Compare every class against a no-consolidation control on the same time-sliced tasks, so that measured lift is attributable to the artifact rather than to a coincident change elsewhere.

**Required Outputs**:

- An audit sample record per class with per-assertion support verdicts.
- A promotion precision and calibrated accuracy figure per class per audit window.
- A self-confirmation flag set naming records with no independent external anchor.
- A drift report covering correction rate, stale-serve rate, answer-flip rate, and tail-coverage delta.

**Quality Checkpoints**:

- Every audit window produces a calibrated accuracy figure, and the next run's confidence ceilings consume it; a run using a stale calibration figure older than 90 days is blocked.
- Adjudication is performed against linked sources; an adjudication that cannot open the sources is recorded as inconclusive rather than as correct.
- Records with 0 independent external anchors are flagged in every audit window, since they are the population in which laundering concentrates.
- The no-consolidation control is run on the same tasks in the same window, not inferred from a prior period.

***

#### Step 6.2: Execute Rollback and Invalidation Cascades

**Required Actions**:

- Roll back an individual record on any of the following triggers: contradiction by an authoritative source, a broken or unresolvable provenance link, a correction rate above 5 percent within 30 days of promotion, or an adjudicated support verdict of unsupported on any critical assertion.
- Suspend an entire artifact class where its audited promotion precision falls below 90 percent, and roll back every record promoted in that class since the last passing audit where precision falls below 80 percent.
- Execute rollback as an atomic pointer restoration followed by cache invalidation, index alias reversion, and a verification query proving the withdrawn version is no longer served.
- On source correction, retraction, consent withdrawal, or erasure, traverse outgoing dependency edges from the affected source and tombstone every derived record from serving immediately, before attempting any re-derivation.
- Continue the cascade through summaries, facts, procedures, prompts, index generations, evaluation corpora, datasets, caches, and exports, and record targets discovered, tombstoned, re-derived, and failed at each depth.
- Re-derive tombstoned records from the remaining eligible sources, and where re-derivation cannot reconstruct a record without the removed source, retire the record rather than publishing a weaker successor at the original confidence.

**Required Outputs**:

- A rollback record per withdrawn version with its trigger, pointer switch time, and residual serve count.
- A class suspension record where a precision threshold was breached.
- An invalidation cascade record with cascade depth and per-depth target counts.
- A re-derivation record naming the new version, the remaining eligible sources, and the semantic difference from its predecessor.

**Quality Checkpoints**:

- Residual serve count after rollback is 0, verified by query rather than assumed from the pointer switch.
- Tombstoning precedes re-derivation in every cascade; a pipeline that re-derives first continues serving the affected record during the gap and fails this checkpoint.
- Every cascade reports targets failed as well as targets completed, since a silently partial cascade leaves a stale copy that later reads as current.
- A re-derived record's confidence is recomputed from its new evidence rather than inherited from its predecessor.
- Rollback is rehearsed before first release of every artifact class and re-rehearsed after any change to the serving path.

***

#### Step 6.3: Recompute Consolidation Economics and Retire Negative Classes

**Required Actions**:

- Compute fully loaded consolidation cost per class, allocating model tokens, batch discounts, compute time, storage, index writes, human review minutes, retries, correction work, and rollback work to the runs and records that incurred them.
- Compute cost per useful artifact as fully loaded cost divided by records later adjudicated useful, and recompute break-even reuse using the observed selection rate rather than the expected one, since a record that exists but is rarely retrieved saves nothing.
- Include error externalities in net value as the expected frequency of harmful reuse multiplied by the expected harm, so that a cheap class producing occasional wrong answers is not scored as profitable.
- Compare measured net value against the no-consolidation and simple deterministic baselines declared in Step 1.1, and report per class rather than only in aggregate.
- Retire any class whose confidence-bounded net value remains negative across 2 consecutive audit windows, and record the retirement with its measured values rather than deferring the decision.
- Feed every rejection reason, halt, rollback, and human-review disagreement into the next policy version, and version the thresholds rather than editing them in place.

**Required Outputs**:

- A cost ledger per class with its allocated components.
- A net value figure per class with its confidence bounds and its externality term.
- A retirement record for every class withdrawn, naming its measured net value across both windows.
- A threshold policy version incorporating the window's findings.

**Quality Checkpoints**:

- Every cost component is allocated to a run and a record; unallocated cost is reported rather than absorbed, because absorbed cost makes every class look profitable.
- Break-even is recomputed on observed selection rate at each audit window.
- Net value carries an externality term; a class evaluated without one is reported as unevaluated.
- Retirement is executed on the measured criterion rather than deferred, and a retained negative-value class carries an explicit written exception with an expiry.
- Threshold changes are versioned, and no threshold is lowered in the same window in which it caused a rejection.

***

## III. Implementation Guidance for AI Agents

AI agents running a consolidation pipeline must follow systematic protocols ensuring that generation and publication authority remain separated, that every consolidated record remains traceable to the episodes it came from, and that no record carries more confidence than its evidence supports. The following guidance translates the pipeline above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Scheduler Component**: Evaluates triggers, watermarks, staleness targets, and capacity reserves; admits, defers, or halts runs. Deterministic. It owns the batch and backpressure policy and may refuse a run that would compete with serving.
2. **Selection Agent**: Applies authorization and purpose filters, partitions episodes, deduplicates, assigns provenance families, and freezes the snapshot manifest. Deterministic. It alone may declare two episodes independent.
3. **Consolidator Agent**: Generates candidate content under a pinned model, versioned prompt, and fixed output schema. Model tier. It holds no write access to the published store, no vote in the promotion decision, and no authority to set a record's final confidence.
4. **Adjudicator Agent**: Judges whether two assertions genuinely conflict and returns a verdict from the closed vocabulary. Model tier. Its verdict is a proposal; the blocking decision is made by software.
5. **Gatekeeper Component**: Runs the mechanical admissibility checks, computes confidence ceilings, executes the holdout suite, records the promotion decision, and performs the atomic publication. Deterministic. It is the only component that may change a record's state to published.
6. **Audit Agent**: Samples promoted records, adjudicates them against their linked sources, computes precision and calibration, and issues rollback and cascade instructions. Hybrid. It may withdraw a record and suspend a class without consulting the consolidator.

**Authority Separation Rule**: The component that proposes a consolidated record and the component that publishes it are never the same component, never share a prompt, and never share a model invocation. Where a deployment runs both on one model, they must run as separate invocations with separate schemas, and the Gatekeeper's checks must be executed outside model inference entirely. A pipeline in which a model is asked whether its own output should be published has no promotion gate, only a formality.

**Workflow Execution Pattern**:

```
STATE: Promotion_Gate_Evaluation
INPUTS:
  1. Candidate record with provenance block from Step 4.2
  2. Confidence computation record from Step 4.3
  3. Contradiction inventory and adjudication records from Phase 3
  4. Frozen holdout suite for the artifact class
ACTIONS:
  1. Evaluate every hard check in software, no model in path
  2. Re-run authorization on the candidate, not only on its sources
  3. Execute the holdout suite and compare per slice
  4. Compare final confidence against the consequence-class threshold
  5. Route to human approval where the class requires it
VALIDATION:
  - provenance_completeness == 1.00
  - blocking_contradiction_present == FALSE
  - independent_support_count >= class_minimum
  - final_confidence <= min(proposed, ceiling, input_max)
  - final_confidence >= class_threshold
  - every_holdout_hard_slice_passed == TRUE
  - synthetic_ancestry_fraction <= class_maximum
  - generation_depth <= class_maximum
  - rollback_rehearsal_residual_serves == 0
  - publishing_component != generating_component
TRANSITIONS:
  IF all_validations_pass AND human_approval_not_required
     THEN next_state = Publish_Immutable_Version
  IF all_validations_pass AND human_approval_required
     THEN next_state = Await_Human_Approval
  IF blocking_contradiction_present THEN next_state = Quarantine_Group
  IF any_hard_check_failed THEN next_state = Reject_With_Reason_Codes
```

**Two-Phase Action Pattern**: Emit the candidate with its provenance block, computed ceiling, and check vector without publishing it; confirm the check vector against the validation block while no serving state has changed; publish only after every hard check passes, writing the immutable version, the lineage links, and the promotion decision record in the same transaction.

**Approval Gate**: Human authorisation is required before publishing any high-consequence record, before publishing any record whose independent support count is 1 and whose sole source is not authoritative, before publishing any record whose generation depth exceeds 1 in a moderate or high class, and before resuming a run halted by an unresolved contradiction rate above 15 percent. Agents halt at these gates rather than publishing with a recorded warning, because a warning attached to a published record is not read at retrieval time.

**Context Management Requirements**:

- Hold the snapshot manifest, the provenance links, and the support ledger in durable state rather than in working context, since a consolidation run routinely exceeds a single context window.
- Process one group per model invocation so that a large batch never places unrelated groups in the same context, where cross-contamination between groups produces assertions supported by the wrong episodes.
- Checkpoint after selection, after generation, after validation, and after publication independently, and make each stage idempotent under at-least-once delivery.
- Write a handoff record at every context boundary naming the completed groups, the pending groups, the snapshot manifest hash, and the pipeline version.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Scope and Snapshot Integrity (After Phase 1)**

- **Automated Check**: Every declared artifact class carries a proof obligation, validator, freshness target, and rollback target; the manifest hash reproduces on replay; authorization precedes relevance in the selection order; no work item spans more than 1 tenant.
- **Agent Action on Pass**: Proceed to grouping and deduplication.
- **Agent Action on Failure**: Halt the run and return the incomplete class or the irreproducible manifest; no content is read against an unfrozen selection.
- **Human Review Trigger**: More than 10 percent of eligible episodes excluded by authorization filters, which usually indicates a scope or consent misconfiguration rather than a genuine restriction.

**Checkpoint 2: Grouping and Independence Integrity (After Phase 2)**

- **Automated Check**: Every episode sits in exactly 1 group or the unresolved partition; support count and independent support count are separately populated; no collapse raised independent support count; no semantic cluster survives a validation removal rate above 20 percent.
- **Agent Action on Pass**: Proceed to contradiction detection.
- **Agent Action on Failure**: Return the affected groups for re-partitioning; do not proceed with a group whose independence ledger is inconsistent.
- **Human Review Trigger**: More than 30 percent of the snapshot landing in the unresolved partition, which indicates an entity-resolution failure upstream.

**Checkpoint 3: Contradiction Handling Integrity (After Phase 3)**

- **Automated Check**: Every detected contradiction carries a class and a verdict from the closed vocabulary; no verdict cites frequency as its basis; counterevidence is retained on 100 percent of resolved contradictions; the batch's unresolved contradiction rate is at or below 15 percent and at or below 2 times the trailing 30-run median.
- **Agent Action on Pass**: Proceed to candidate generation.
- **Agent Action on Failure**: Halt the run, record the triggering rate, and quarantine the affected groups; do not re-run the same batch with the same configuration.
- **Human Review Trigger**: Any halt on either contradiction rate threshold, or any deleted competitor assertion detected in a resolved contradiction.

**Checkpoint 4: Provenance and Confidence Integrity (After Phase 4)**

- **Automated Check**: Provenance completeness is 100 percent on every candidate; every evidence span resolves to a snapshot member; no link points at a mutable identifier, crosses a tenant boundary, or closes a lineage cycle; final confidence is at or below the minimum of proposed, ceiling, and input maximum; no record carries confidence 1.0.
- **Agent Action on Pass**: Proceed to the promotion gate.
- **Agent Action on Failure**: Void the affected assertions and re-evaluate the candidate without them; reject the candidate where voiding leaves it below its class minimum.
- **Human Review Trigger**: More than 5 percent of assertions in a batch voided for unresolvable spans, which indicates a generation or schema defect rather than isolated error.

**Checkpoint 5: Promotion Gate Integrity (After Phase 5)**

- **Automated Check**: Every hard check evaluated in software; rejection on first hard failure with no weighted aggregate; every holdout hard slice passed; the candidate beats both baselines; rollback rehearsal residual serve count is 0; the approved content hash matches the published hash; the publishing component differs from the generating component.
- **Agent Action on Pass**: Publish the immutable version, switch the alias, and begin the shadow phase.
- **Agent Action on Failure**: Reject with reason codes and retain the candidate in the candidate store for analysis; never publish with a caveat attached.
- **Human Review Trigger**: Any published version lacking a promotion decision record, or any threshold change proposed in the same window in which it caused a rejection.

**Checkpoint 6: Post-Promotion Audit Integrity (After Phase 6)**

- **Automated Check**: The audit sample meets the greater of 5 percent or 30 records per class per week; calibrated accuracy is no older than 90 days; residual serve count after every rollback is 0; every cascade reports targets failed as well as completed; every class carries a net value figure with an externality term.
- **Agent Action on Pass**: Release the audit report and permit the next scheduled run.
- **Agent Action on Failure**: Block the next run for the affected class until the audit completes; a class cannot promote on a calibration figure it has not refreshed.
- **Human Review Trigger**: Promotion precision below 90 percent for any class, any partial cascade leaving a residual stale copy, or any class retained despite negative net value across 2 consecutive windows.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
RUN_ID:
ARTIFACT_CLASS:
VALIDATION_CRITERIA:
MEASURED_VALUE:
THRESHOLD:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
EVALUATED_BY:          SOFTWARE | MODEL | HUMAN
```

### C. Error Handling and Troubleshooting

**Error Type 1: Error Laundering in a Promoted Record**

- **Symptoms**: An audited record asserts more than its linked sources support; hedges, uncertainty, and minority positions present in the sources are absent from the record; the record's confidence exceeds the calibrated accuracy of its class; downstream corrections cluster on records from one artifact class.
- **Diagnostic Steps**: Open the record's provenance block and adjudicate each assertion against its own linked spans; compare the record's stated confidence against its evidence ceiling and identify the binding constraint; check whether counterevidence links exist for contradictions that Phase 3 recorded; determine whether the omissions field was populated at generation.
- **Resolution Protocol**: Option A, roll back the record and re-derive with the counterevidence links restored and the ceiling recomputed. Option B, narrow the record's scope to the subset its evidence supports and republish at the reduced scope and confidence. Option C, retire the record and revert the affected queries to raw retrieval. Option D, suspend the artifact class where audited precision has fallen below 90 percent.
- **Escalation Trigger**: Any laundered record in a high-consequence class escalates immediately and is never resolved by re-generation alone; 2 laundered records in one audit window for one class suspends that class pending a policy revision.

**Error Type 2: Provenance Break or Orphaned Record**

- **Symptoms**: An evidence span fails to resolve; a link points at a mutable identifier; a source version referenced by a published record no longer exists; provenance completeness computed at audit differs from the figure recorded at promotion.
- **Diagnostic Steps**: Determine whether the break originated in a source deletion, a snapshot expiry, a link written against an identifier rather than a version, or an incomplete cascade from an earlier invalidation.
- **Resolution Protocol**: Option A, restore the source version from immutable storage and re-verify the link. Option B, where the source was lawfully erased, tombstone the record and re-derive from remaining eligible sources at a recomputed confidence. Option C, where re-derivation cannot reconstruct the record, retire it rather than republishing a weaker successor at the original confidence.
- **Escalation Trigger**: Any orphaned record in the published store halts promotion for its class until the cascade that produced the orphan is identified; this class of error is never resolved by retry, because a retry re-publishes the same broken lineage.

**Error Type 3: Contradiction Storm**

- **Symptoms**: The batch's contradiction rate exceeds 15 percent unresolved or 2 times the trailing median; contradictions concentrate on one entity, one source, or one time window; adjudication verdicts cluster on unresolved.
- **Diagnostic Steps**: Determine whether the rise originates in a genuine change in the world, an entity-resolution failure merging two distinct subjects, an extraction schema change, a clock or timezone defect producing false interval overlap, or a poisoned source injecting conflicting assertions.
- **Resolution Protocol**: Option A, where entity resolution is the cause, re-partition with corrected identifiers and re-run detection. Option B, where a source is the cause, quarantine that source's episodes and re-run the batch without them, recording the exclusion. Option C, where the change is genuine, split the validity intervals and consolidate each period separately. Option D, where the cause cannot be established, hold the batch and escalate rather than lowering the threshold.
- **Escalation Trigger**: 2 consecutive halted batches for the same artifact class escalates to policy review; the threshold is never raised to clear a halt.

**Error Type 4: Repetition Mistaken for Corroboration**

- **Symptoms**: A record's support count greatly exceeds its independent support count; a fact's supporting sources trace to 1 provenance family; confidence rose across runs while the evidence set did not change; multiple agents agree while citing a common upstream artifact.
- **Diagnostic Steps**: Trace every supporting source to its provenance family and recount independent support; check whether any supporting source is itself a consolidated artifact; compute the independent external anchor count and the synthetic ancestry fraction.
- **Resolution Protocol**: Option A, recompute the confidence ceiling from the corrected independent support count and republish at the lower value. Option B, commission an independent verification against an authoritative source or a deterministic test before restoring the original confidence. Option C, mark the record provisional with a restricted audience until an external anchor is obtained. Option D, reject the record where its independent external anchor count is 0 and no anchor is obtainable.
- **Escalation Trigger**: Any record with independent external anchor count 0 in a moderate or high class escalates; additional agreeing sources from the same family never resolve this error [21].

**Error Type 5: Recursive Consolidation Drift**

- **Symptoms**: Generation depth rising across runs; tail coverage falling; rare events absent from later generations that were present in earlier ones; answer-flip rate rising against the frozen holdout; synthetic ancestry fraction climbing.
- **Diagnostic Steps**: Compare adjacent-generation preservation from depth g minus 1 to depth g against end-to-end preservation from depth 0 to depth g, and identify the generation at which a hard slice first failed.
- **Resolution Protocol**: Option A, stop recursive consolidation at the last passing generation and serve that version. Option B, rebuild the failing generation from leaves rather than from its parent summary. Option C, reduce the depth cap for the class and re-derive within it. Option D, retire the recursive class and serve raw retrieval for the queries it covered.
- **Escalation Trigger**: Any hard-slice failure at any generation stops further recursion for that class immediately; recursion is never continued on the expectation that the next generation will recover the tail [20].

**Error Type 6: Consolidation Backlog and Staleness Breach**

- **Symptoms**: Oldest eligible item age above 4 times the staleness target; queue depth rising while throughput is flat; runs repeatedly deferred by the capacity watermark; observed staleness exceeding the freshness target on published records.
- **Diagnostic Steps**: Determine whether the cause is capacity starvation from the foreground reserve, oversized work items, repeated dead-lettering, or a halted class blocking its own queue.
- **Resolution Protocol**: Option A, reduce work item size and raise parallelism within the existing capacity reserve. Option B, split the queue by artifact class so that a halted high-consequence class does not block a low-consequence one. Option C, extend the staleness target for classes whose freshness requirement was set tighter than the evidence changes. Option D, retire the class where the backlog reflects volume the break-even calculation never supported.
- **Escalation Trigger**: Oldest eligible item age above 10 times the staleness target escalates; backlog is never cleared by relaxing an evidence gate or by skipping validation on the oldest items.

**Troubleshooting Decision Tree**:

```
CONSOLIDATION DEFECT DETECTED
├─ EVIDENCE DEFECT
│   ├─ Assertion unsupported by its own links → Roll back; re-derive with ceiling recomputed
│   ├─ Span does not resolve to snapshot → Void assertion; reject if below class minimum
│   └─ Support high, independent support 1 → Recompute ceiling; require external anchor
├─ CONTRADICTION DEFECT
│   ├─ Unresolved blocking class → Block candidate; quarantine group
│   ├─ Unresolved rate above 15 percent → HALT run; diagnose cause; never raise threshold
│   └─ Verdict cites frequency as basis → Reject verdict; re-adjudicate on authority
├─ CONFIDENCE DEFECT
│   ├─ Final above evidence ceiling → HALT publication; recompute in software
│   ├─ Final above input maximum → Cap at input maximum; record binding constraint
│   └─ Calibration figure older than 90 days → Block run until audit refreshes it
├─ AUTHORITY DEFECT
│   ├─ Generator wrote to published store → HALT; treat as incident; re-separate components
│   ├─ Model verdict used as gate result → Reject verdict; re-evaluate check in software
│   └─ Human approval missing on high class → Withdraw version; route to approver
├─ LINEAGE DEFECT
│   ├─ Orphaned published record → Halt class promotion; identify failed cascade
│   ├─ Link to mutable identifier → Reject link; rewrite against source version
│   └─ Lineage cycle detected → Reject candidate; do not repair the cycle
└─ OPERATIONAL DEFECT
    ├─ Rollback residual serves above 0 → Re-invalidate caches; re-verify by query
    ├─ Cascade reports failed targets → Tombstone remains; escalate before re-derivation
    └─ Backlog above 10 times staleness target → Escalate; never skip validation
```

### D. Performance Metrics and Continuous Learning

**Promotion Quality Metrics**:

- **Promotion precision**: Audited promoted records adjudicated correct over records audited, reported per artifact class (target: at least 90 percent; below 90 percent suspends the class, below 80 percent rolls back the window).
- **Promotion recall**: Records that should have been promoted and were, measured against a labelled set built independently of accepted candidates (target: at least 70 percent; recall inferred from accepted candidates alone is not reported).
- **Provenance completeness**: Assertions in published records carrying at least 1 resolvable supporting link (target: 100 percent; any shortfall is an incident, not a metric miss).
- **Counterevidence retention**: Contradictions detected in Phase 3 that survive as links on the published record (target: 100 percent for moderate and high classes).
- **Confidence calibration gap**: Stated confidence minus observed correctness, segmented by artifact class and consequence class (target: no more than 10 percentage points per segment; a positive gap above 10 points is the direct measurement of error laundering).

**Preservation and Drift Metrics**:

- **Answer preservation**: Holdout questions answerable from the consolidated record that were answerable from the sources (target: at or above the class threshold in Step 5.1; a drop on any hard slice fails regardless of the aggregate).
- **Rare-event retention**: Rare and negative cases present in the sources that remain recoverable from the record (target: at or above the class threshold; this metric degrades first and is reported before compression ratio).
- **Answer-flip rate**: Holdout answers that changed between consecutive generations (target: no more than 2 percent per generation).
- **Tail-coverage delta**: Change in coverage of the least frequent 10 percent of source content across generations (target: no more than 5 percentage points lost per generation) [20].
- **Independent external anchor count**: Published records supported by at least 1 non-derived source (target: 100 percent for moderate and high classes).

**Operational and Economic Metrics**:

- **Observed staleness**: Age of the oldest unconsolidated eligible evidence against the staleness target (target: at or below 1 times the target; above 4 times alerts, above 10 times escalates).
- **Rollback success**: Rollbacks completing with residual serve count 0 (target: 100 percent).
- **Cascade completeness**: Invalidation cascades completing with 0 failed targets (target: 100 percent; a partial cascade is reported as a residual stale copy count, never as a success).
- **Consolidation overhead**: Fully loaded consolidation cost over serving cost (target: no more than 15 percent; above 25 percent triggers class-level economic review).
- **Cost per useful artifact**: Fully loaded cost divided by records later adjudicated useful (target: below the measured cost of serving the same queries from raw retrieval).

**Learning and Adaptation Mechanisms**:

- **Calibration feedback**: Each audit window's measured accuracy per class becomes the next run's confidence ceiling, so that a class producing over-confident records is automatically constrained rather than corrected by exhortation.
- **Threshold versioning**: Every threshold change is versioned with the evidence that motivated it, evaluated on subsequent rather than historical batches, and never applied retroactively to admit a previously rejected record.
- **Rejection analysis**: Rejection reason codes are aggregated per class per window, and a reason code accounting for more than 40 percent of rejections indicates an upstream defect to fix rather than a gate to loosen.
- **Holdout refresh**: The frozen holdout is extended, never edited, and a new frozen version is cut whenever the source distribution shifts materially; scores across holdout versions are never compared directly.

**Human-in-the-Loop Boundaries**: Approval of a high-consequence record, amendment of a promotion threshold, resumption of a run halted by a contradiction storm, retention of a class whose net value is negative across 2 windows, and any relaxation of the authority separation rule are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how accumulated evidence becomes durable belief, not what the evidence is about. Its phases hold wherever an agent accumulates episodes faster than it can retrieve them economically, and wherever a wrong durable record would be costlier than a wrong transient one.

### 4.1 Cross-Domain Application Patterns

**Customer service and support operations**: Episodes are conversation turns, ticket events, and resolution outcomes. Grouping is by customer identifier, issue class, and the period the account configuration held. The dominant laundering risk is a summary asserting a stable customer preference from a single frustrated exchange, so the preference class requires a direct statement rather than an inferred behaviour and carries an expiry. Contradiction detection is high-value because account state changes frequently and a superseded entitlement served as current produces an immediately visible error.

**Clinical and care documentation**: Episodes are encounter notes, results, and observations. Consequence class is high for anything influencing care, so independent support and human approval bind on every record. Validity intervals are the load-bearing field, since a finding true at one encounter is not a standing fact, and the interval conflict class is the most frequent contradiction. Raw evidence is retained rather than compressed away, because exact wording carries audit and dispute value that no summary preserves, and erasure obligations must reach every derivative.

**Software engineering agents**: Episodes are execution trajectories, test outcomes, and tool results. The valuable artifact class is the procedure record, whose proof obligation is support across 3 or more distinct tasks plus sandbox execution on unseen inputs. Failed trajectories are as informative as successful ones and must be selected deliberately, since collapsing rare failures into a dominant success pattern produces a runbook that works until it does not. Deterministic validators are unusually available here, which raises the achievable evidence ceiling.

**Financial and regulatory advisory**: Episodes are filings, communications, and market observations. Source authority dominates: an authoritative filing outranks any volume of secondary restatement, and the authority conflict class resolves in its favour while retaining the dissent. Records carry tight expiries because the domain changes faster than most refresh targets, and the break-even calculation frequently returns negative for volatile facts, which the framework handles by declining to consolidate them rather than by consolidating them badly.

**Field operations and logistics**: Episodes are sensor readings, dispatch events, and completion reports. Volume is high and individual episodes are cheap, so exact deduplication and index regeneration carry most of the value while semantic abstraction carries little. The staleness target is short and the settling window is correspondingly short, since a correction that arrives after the snapshot is a stale-serve rather than a late refinement.

**Scientific and technical research assistance**: Episodes are papers, extracted claims, and experiment records. Provenance at span granularity is the deliverable rather than an audit aid, because a claim without its source is unusable in this domain regardless of correctness. Contradictions are frequently genuine disagreement in the literature rather than error, so the retain-both verdict dominates and any pipeline that resolves disagreement into a single confident value is producing a wrong artifact even when its value happens to be right.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small corpora under 10,000 episodes**: Run exact deduplication and scoped summaries only, retain every source, and review promotions manually. The full gate is retained; only the artifact classes are reduced, because a small corpus does not make laundering less likely, only less frequent.
- **High-volume, low-consequence corpora**: Automate promotion for the low class, sample audit at the floor of 30 records per class per week, and reserve human review for the moderate sample and every high record. Prefer index regeneration and deduplication over abstraction, since they carry proof obligations software can discharge alone.
- **High-consequence or regulated deployments**: Retain every phase, require an authoritative source or 3 independent families, cap generation depth at 1, mandate human approval on every record, and treat the lineage graph and justification records as deliverables rather than as diagnostics.
- **Latency-sensitive serving paths**: Never place consolidation on the write path. Where a product contract requires immediate availability of a derived record, serve raw retrieval until the record clears the gate, rather than shortening the gate to meet the deadline.
- **Multi-tenant deployments**: Bind every work item, queue, temporary file, model batch, vector namespace, cache, and review queue to 1 tenant, and reject any lineage edge crossing a tenant boundary unless an explicit sharing policy authorises it. A cross-tenant edge is treated as an incident, not as a configuration error.

***

## V. Limitations and Considerations

**Error laundering is contained, not eliminated**: The four countermeasures reduce the rate at which unsupported records reach durable memory; none of them detects a record whose sources were themselves wrong in a mutually consistent way. A group of episodes that all report the same error will produce a well-provenanced, correctly ceilinged, contradiction-free record asserting that error. The mitigation is the post-promotion audit in Step 6.1, which adjudicates against sources rather than against the record, and the calibration feedback loop that lowers the class ceiling when audited accuracy falls; both detect the failure after promotion rather than preventing it, so consolidated records must remain correctable and revocable at all times.

**Thresholds are deployment defaults, not measured findings**: Every numeric bound stated in this guide, including the 15 percent contradiction halt, the 0.85 and 0.92 duplicate similarities, the confidence ceiling ladder, the 5 percent audit sample, and the 90 percent precision floor, was chosen to be operable on first deployment rather than derived from a measured property of consolidation systems. The mitigation is the threshold versioning requirement in Section III.D, which obliges each deployment to recompute its thresholds per artifact class against observed audit outcomes and to treat the values here as a starting configuration to be replaced.

**Contradiction detection is bounded by schema typing**: Deterministic detection finds conflicts only where assertions carry typed entities, predicates, and intervals. Free-text assertions are passed to the model tier, whose recall on subtle contradiction is unmeasured in most deployments, so a pipeline consolidating mostly unstructured content will under-detect conflict and over-promote. The mitigation is to require typed extraction before consolidation for any moderate or high class, and to treat free-text-only groups as low-consequence regardless of what their content appears to assert.

**Provenance completeness is checkable, provenance correctness is not**: Software can verify that every assertion carries a resolvable link to a snapshot member; it cannot verify that the linked span actually supports the assertion. A generator that attaches plausible but unsupporting spans produces a record with 100 percent completeness and no evidential basis. The mitigation is the audit sample in Step 6.1, which adjudicates span-to-assertion support directly, and the promotion precision floor that suspends a class where that adjudication fails.

**Consolidation frequently fails to pay back**: Many workloads have reuse distributions too thin to recover the generation, validation, review, storage, monitoring, correction, and retirement cost of a durable record. Consolidating anyway produces a governed artifact that saves nothing and creates a new source of authority to maintain. The mitigation is the break-even requirement in Step 1.1, the observed-selection-rate recomputation in Step 6.3, and the retirement rule that withdraws a class after 2 negative windows rather than waiting for a decision that is never taken.

**Below-agent-layer promotion is out of scope**: Consolidating experience into model weights through fine-tuning or knowledge editing is a real technique and is not covered here beyond the referral in Section 1.3. A deployment electing it loses the properties this framework depends on: a weight-encoded behaviour cannot be inspected, cited, rolled back by pointer switch, or removed by an invalidation cascade. The mitigation is to keep the approved external artifact and its dataset lineage canonical, to govern any parametric promotion under a separate specification, and never to represent a fine-tuned behaviour to an agent as a consolidated record it can audit.

**Holdout corpora age and leak**: A frozen holdout measures preservation against the questions it was built to ask. As the source distribution shifts, its slices stop covering the cases that matter, and near-duplicate leakage between development and holdout families silently inflates every score. The mitigation is the family-disjointness check in Step 5.2, the extend-never-edit rule in Section III.D, and the prohibition on comparing scores across holdout versions.

**Deletion propagation to derivatives is expensive and rarely complete**: Consolidated summaries, facts, profiles, embeddings, and exports can remain personal data, and an erasure obligation reaches all of them. Backups, provider-side batches, and downstream exports are frequently outside the cascade's reach. The mitigation is the verifiable derivative inventory maintained through the lineage links in Step 4.2, the cascade recording of failed targets in Step 6.2, and explicit disclosure of residual backup treatment rather than an unqualified claim of completion [17][18].

**Semantic clustering has no ground truth at run time**: The model tier's cluster proposals are validated against partition keys, which catches members that violate a typed constraint but not members that are semantically wrong within one partition. The mitigation is the 20 percent dissolution rule in Step 2.3, which discards a cluster whose validation removal rate suggests the proposal was unreliable, and the retention of unclustered residuals as evidence rather than noise.

***

## VI. Conclusion and Summary

Memory consolidation is a promotion discipline before it is a compression technique. Its value comes from a small number of explicit decisions: which episodes belong together, which of them are copies rather than corroboration, where they disagree, how much confidence their agreement can support, and whether the resulting record has earned the right to be retrieved as fact. A pipeline that makes those decisions explicitly and records them produces durable memory that improves with auditing. A pipeline that leaves them implicit produces confident-looking records whose errors are invisible precisely because consolidation removed the evidence that would have exposed them.

A team introducing consolidation should instrument the episode store and build the frozen holdout before building a consolidator. Start with exact deduplication and index regeneration, which carry proof obligations software can discharge alone, and measure whether they pay back. Add scoped summaries next, then atomic facts, and add procedures and reflections only after the audit loop has produced 2 windows of calibrated accuracy for the earlier classes. Keep the promotion gate in software from the first day, because retrofitting authority separation into a pipeline whose generator already writes to the published store requires rebuilding it.

**Key Success Factors**:

- **Provenance through every step**: Every consolidated record enumerates the episodes it came from at span granularity, and completeness below 100 percent rejects rather than caveats.
- **Contradiction before abstraction**: Disagreement is detected deterministically and adjudicated with a recorded verdict before any summary is written, and averaging, last-writer-wins, and majority-by-repetition are prohibited outcomes.
- **Confidence bounded by evidence**: A consolidated record never carries more confidence than its independent support, its source authority, its generation depth, and its class calibration allow, and never carries certainty at all.
- **Software closes the gate**: The model tier proposes and the deterministic tier promotes; a pipeline in which the generator can publish its own output has a formality rather than a gate.
- **Reversibility as an ordinary operation**: Every published version has an expiry, a rollback target, and a rehearsed cascade, and rollback is verified by query rather than assumed from a pointer switch.
- **Economics measured per class**: Consolidation is retained only where its audited net value, including error externalities, exceeds the no-consolidation baseline, and negative classes are retired rather than defended.

By following this guide, AI agents can convert accumulated experience into durable memory that carries its own evidence, discloses its own disagreements, and can be withdrawn as readily as it was published.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. The four entries marked as retrieved during conversion were located by the author of this guide during its research pass rather than transcribed, and entry 23 was found in both the prose source and that research pass.

**Corpus pointers**:

- `Memory Consolidation for AI Agents: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the promotion-pipeline framing, the candidate state machine, the artifact-class taxonomy and its proof obligations, the trigger and batching discipline, the evidence-over-frequency rule, the holdout and preservation metrics, the lineage and reversibility requirements, the self-confirmation and security material, and the fifteen-step end-to-end workflow that the six phases above reorganise.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — companion guidance on the surrounding memory architecture into which consolidated records are written and from which they are served.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — companion guidance on the episode store that supplies this pipeline's inputs, applicable to the immutability and identifier requirements in Phase 1.
- `advanced_task_guides/memory-management/guide_AttentionBasedMemoryRetrieval.md` — companion guidance on the retrieval path that consumes promoted records, applicable to the index-generation artifact class and the stale-serve metrics in Phase 6.
- `advanced_task_guides/memory-management/guide_SemanticMemory.md` — owns the destination store for promoted claims, including the ontology and relation registry, identity resolution, and the supersession state a published record carries. This pipeline ends at the promotion decision in Step 5.3; the governance of the record thereafter belongs to that guide.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — owns retention policy, the separation of utility forgetting from obligation erasure, and the coverage proof a reduction requires; applicable to the invalidation cascade in Step 6.2 and the retirement of negative classes in Step 6.3.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — owns the operation contract for a single durable write, including gate ordering and terminal states; applicable to the publication of a reversible version in Step 5.3 and to the derivative watermarks a rollback must reach.
- `advanced_task_guides/memory-management/guide_TemporalKnowledgeGraphMemory.md` — owns the semantics of the valid-time and transaction-time axes and of a point-in-time query; applicable to the validity-period partitioning in Step 2.1, which this guide treats as a grouping key rather than defining.
- `advanced_task_guides/memory-management/guide_GenerativeAgentMemory.md` — owns the reflection path, which is one specific promotion mechanism running inline against a live stream on a salience trigger. This guide owns the general promotion governance, the contradiction treatment across accumulated records, and the evidence gate that any such mechanism is measured against.
- `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md` — companion guidance on evidence tracking and lineage modelling, applicable to the provenance links in Step 4.2 and the invalidation cascade in Step 6.2.
- `advanced_task_guides/knowledge-graphs/guide_KG_EntityResolutionDedup.md` — companion guidance on entity resolution and deduplication, applicable to the partitioning and duplicate-collapse rules in Phase 2.
- `advanced_task_guides/knowledge-graphs/guide_KG_QualityControl.md` — companion guidance on quality control for derived knowledge, applicable to the holdout suite and audit sampling in Steps 5.2 and 6.1.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the run, candidate, decision, validation, and cascade records this pipeline emits.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on value-of-computation control, applicable to the break-even and retirement decisions in Steps 1.1 and 6.3.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, III, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Consolidation in biological memory systems*

1. Squire and colleagues, *Memory Consolidation* — https://pmc.ncbi.nlm.nih.gov/articles/PMC4526749/
2. Review of challenges to standard systems consolidation — https://pmc.ncbi.nlm.nih.gov/articles/PMC9720899/
3. McClelland, McNaughton, and O'Reilly, *Complementary Learning Systems* review — https://onlinelibrary.wiley.com/doi/full/10.1111/j.1551-6709.2011.01214.x
4. Tse and colleagues, *Schemas and Memory Consolidation*, Science — https://www.science.org/doi/10.1126/science.1135935
5. Review of waking and sleeping sharp-wave ripples — https://pmc.ncbi.nlm.nih.gov/articles/PMC4641767/
6. Reconsolidation review — https://pmc.ncbi.nlm.nih.gov/articles/PMC4588064/

*Summary faithfulness and evaluation*

7. G-Eval — https://arxiv.org/html/2305.14069v2
8. FineSurE — https://aclanthology.org/2024.acl-long.51.pdf

*Experience reuse and derived artifacts at the agent layer*

9. Park and colleagues, *Generative Agents* — https://arxiv.org/abs/2304.03442
10. ExpeL — https://arxiv.org/html/2308.10144v2
11. Voyager — https://arxiv.org/abs/2305.16291

*Parametric promotion, referred to in Section 1.3 and out of scope here*

12. Hugging Face PEFT — https://huggingface.co/docs/peft/en/index
13. MLflow Model Registry — https://mlflow.org/docs/latest/ml/model-registry/

*Scheduling, orchestration, and durable execution*

14. Apache Airflow documentation — https://airflow.apache.org/docs/apache-airflow/stable/index.html
15. Temporal failure and error handling — https://docs.temporal.io/encyclopedia/failures-and-error-handling
16. Celery tasks — https://docs.celeryq.dev/en/stable/userguide/tasks.html

*Lineage, versioning, and data protection*

17. ICO, *A Guide to the Data Protection Principles* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/
18. ICO, *Right to Erasure* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/
19. OpenLineage documentation — https://openlineage.io/docs/

*Synthetic drift and correlated evidence*

20. Shumailov and colleagues, *AI Models Collapse When Trained on Recursively Generated Data*, Nature — https://www.nature.com/articles/s41586-024-07566-y
21. *When Not to Write Memory: Governing False Promotion from Correlated Agent Traces* — https://arxiv.org/html/2607.02579 (retrieved during conversion)

*Security and governance of the consolidation boundary*

22. MemoryGraft — https://arxiv.org/html/2512.16962v1
23. *From Untrusted Input to Trusted Memory: A Systematic Study of Memory Poisoning Attacks in LLM Agents* — https://arxiv.org/html/2606.04329v1
24. NIST AI 100-2e2025, adversarial machine learning taxonomy — https://csrc.nist.gov/pubs/ai/100/2/e2025/final
25. *Governing Evolving Memory in LLM Agents: Risks, Mechanisms, and the Stability and Safety Governed Memory Framework* — https://arxiv.org/pdf/2603.11768 (retrieved during conversion)

*Temporal validity and staleness*

26. *Temporal Validity in Retrieval Memory: Eliminating Stale-Fact Errors for AI Agents over Evolving Knowledge* — https://arxiv.org/pdf/2606.26511 (retrieved during conversion)

*Additional sources carrying no inline marker*

27. Agent Workflow Memory — https://arxiv.org/abs/2409.07429
28. Sleep-time Compute — https://arxiv.org/abs/2504.13171
29. OpenAI Batch API — https://developers.openai.com/api/docs/guides/batch
30. Anthropic Message Batches — https://docs.anthropic.com/en/docs/build-with-claude/batch-processing
31. Amazon S3 Object Lock — https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html
32. Dagster column-level lineage documentation — https://docs.dagster.io/guides/build/assets/metadata-and-tags/column-level-lineage
33. OpenTelemetry generative AI semantic conventions — https://opentelemetry.io/docs/specs/semconv/gen-ai/
34. *Uncertainty Management in the Construction of Knowledge Graphs: a Survey* — https://arxiv.org/html/2405.16929v2 (retrieved during conversion)
