# Memory Forgetting Policy

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Memory forgetting policy constitutes the task family of governing how a persistent agent memory system reduces a record's authority, accessibility, detail, recoverability, or influence, and of proving that the reduction actually happened. This guide provides AI agents with a structured protocol separating two paths that are routinely confused: utility forgetting, which drops low-value records to control cost and retrieval noise and whose failure costs recall, and obligation erasure, which removes records because a subject, a contract, or a regulation requires it and whose failure is a compliance breach. It specifies retention class declaration at write time, decay and expiry arithmetic, bounded eviction, invalidation and supersession, and an erasure path treating deletion as a provenance-graph traversal rather than a row delete, because one statement reaches vector index entries, cached retrieval results, consolidated summaries, episode logs, and downstream derived records. It fixes an execution tier partition granting sole delete authority to deterministic software, a residual-match tolerance of zero, a numeric erasure completion bound with a stated escalation, and a recovery path for over-deletion. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a claim of forgetting is backed by evidence rather than by an accepted API response.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Forgetting**: The governed reduction of a memory record's authority, accessibility, detail, recoverability, or influence, executed under a policy stating why, what, when, how completely, under whose authority, with which exceptions, and by what evidence the result is accepted. Forgetting is not a synonym for cache eviction, storage reclamation, summarization, or a single row delete.

**Utility forgetting**: Reduction applied because a record's expected contribution to future task success no longer justifies its retrieval, storage, and context cost. Its trigger is measured value, its verification standard is a task-quality comparison, and its failure mode is lost recall.

**Obligation erasure**: Removal applied because a data subject, a contract, a regulator, a statute, or an approved incident response requires that the content cease to exist across the system. Its trigger is an authority, its verification standard is a zero-residual proof across every serving path, and its failure mode is a compliance breach.

**Retention class**: The single mandatory label assigned to every record at write time, fixing which path may act on it. The five classes are protected evidence, mandatory deletion, default decay, justified operational retention, and archival retention.

**Purpose binding**: The declared processing purpose attached to a record at write time, together with its lawful basis and jurisdiction. Duration is derived from purpose; a new use does not silently extend the original purpose.

**Canonical record**: The authoritative stored form of a memory, addressed by a stable memory identifier and a subject identifier.

**Derived artifact**: Any downstream object produced from a canonical record, including normalized events, extracted claims, text chunks, embeddings, index entries, graph nodes and edges, consolidated summaries, reflections, profile fields, cached retrieval results, prompt fragments, trace spans, evaluation examples, replicas, snapshots, and vendor-held copies.

**Provenance graph**: The directed structure linking every derived artifact to its parent artifacts, its storage system, its namespace, its region, its transform type and version, and its available deletion primitive. It is written at creation time and cannot be reconstructed reliably after the fact.

**Provenance traversal**: The enumeration, from one or more root artifacts, of every reachable derived artifact that must also be acted on. Deletion in an agent memory system is a traversal, not a row delete.

**Lineage coverage**: The proportion of expected artifact classes and discovered derived artifacts for which the orchestrator holds a resolvable target and an executable deletion action. The mandatory-deletion class requires 100 percent.

**Tombstone**: A minimal non-content record asserting that a deletion identity is prohibited from reappearing. It blocks delayed outbox events, replayed logs, stale replica syncs, restored backups, and future reimports. It stores keyed pseudonyms and hashes, never the deleted payload.

**Resurrection**: The reappearance of deleted content through a stale replica, a restored backup, a replayed event, a re-import, or a re-extraction that runs without consulting the tombstone registry.

**Soft delete**: A reversible transition marking a record non-serving while retaining the payload. It is a quarantine and a propagation barrier, never a discharge of an erasure obligation.

**Hard delete**: Removal of the canonical payload from its active substrate. A hard delete in one store proves nothing about derived artifacts, replicas, backups, vendor copies, or model weights.

**Cascading deletion**: The execution of a deletion action against every target enumerated by the provenance traversal, with per-target acknowledgment and per-target verification.

**Crypto-shredding**: Logical erasure achieved by destroying every usable copy of the key that makes ciphertext intelligible. It is valid only where the data was encrypted before storage and where every target, wrapping, derivation, backup, and escrow key copy can be sanitized.

**Residual match**: Any retrieval, read, traversal, reconstruction, or generation that returns erased content, or a distinguishing fragment of it, from any serving path after erasure was reported complete. The tolerance is zero.

**Supersession**: The replacement of a record's authority by a later, contradicting record, recorded as a correction relationship so that the obsolete fact cannot be reinstated from a replica, a summary, or a future import.

**Staleness budget**: The maximum age at which a record of a given relation type may be used directly, together with the age at which revalidation becomes mandatory and the authoritative source permitted to perform it.

**False forgetting**: The removal or suppression of a record that a later adjudication finds should have been retained. It is the principal cost of utility forgetting and the principal reason the eviction path carries a reversibility window.

**Completion attestation**: The evidence record issued at the end of an erasure case, stating scope, policy version, target counts by substrate, exceptions, verification results, residual risks, approver, and next review. It survives the deletion it describes and contains none of the deleted content.

### 1.2 The Two Paths and Why They Are Never Merged

Forgetting for utility and erasure for obligation share mechanisms and share nothing else. They are triggered differently, verified differently, and fail differently. A single policy treating them as one thing will either delete lawful evidence to save storage or satisfy an erasure request with a retrieval filter.

**Divergent triggers**: Utility forgetting is triggered by a measured decline in expected contribution, by a storage or context budget, or by a scheduled expiry with no external authority behind it. Obligation erasure is triggered by an authority: a validated subject request, a consent withdrawal, an expired lawful basis, a contractual deletion clause, a prohibited-content finding, or an approved incident containment order.

**Divergent verification standards**: Utility forgetting is accepted when a replayed task stream shows that retrieval precision and task success did not degrade beyond the declared gate. Obligation erasure is accepted only when every enumerated target returns a residual match count of exactly 0 across every serving path, and no aggregate quality measure substitutes for that count.

**Divergent failure consequences**: A utility mistake costs recall and is recoverable within the reversibility window. An obligation mistake is a compliance failure, is frequently undetectable from inside the system, and is not repaired by restoring the record.

**The prohibited substitution**: A utility policy must never be recorded as satisfying an erasure obligation. An expiry that happens to drop a record does not discharge an erasure request against that record; the request is discharged only by the obligation path, with its own traversal, tombstone, verification, and attestation. Where a scheduled utility expiry and an open erasure case target the same record, the obligation path takes precedence and the utility job marks the record as claimed rather than deleting it silently.

**The reverse substitution is also prohibited**: An obligation erasure must not be counted as evidence that the utility policy is working. Erasure volume is driven by requests and incidents, not by value, and reporting it inside eviction metrics conceals whether the decay parameters are calibrated.

**Retention Class Decision Table**:

| Retention class | Permitted path | Trigger | Terminal state |
| :-- | :-- | :-- | :-- |
| Protected evidence | Neither, while authority is active | Legal hold, statutory duty, safety incident evidence, attestation record | Isolated from serving; released only by a named release authority |
| Mandatory deletion | Obligation erasure only | Validated request, consent withdrawal, purpose end, prohibited content, confirmed poison | Hard delete plus cascade plus tombstone plus attestation |
| Default decay | Utility forgetting only | Confidence below threshold, staleness budget exceeded, eviction cohort selection | Soft delete, then hard delete after the reversibility window |
| Justified operational retention | Utility forgetting after review only | Fixed review date reached with no renewed justification | Reclassified to decay or archival at review |
| Archival retention | Neither, until schedule expiry | Records schedule end date | Reclassified to mandatory deletion at schedule end |

**Write-time enforcement**: A write carrying no retention class, no purpose identifier, no expiry or review time, and no lineage root is rejected at the storage boundary. Unclassified records are the largest single source of unbounded retention, because no scheduler owns them and no traversal reaches them.

### 1.3 Scope Boundary and the Bounded Referral

This guide operates at the agent layer: the stores, indexes, caches, queues, schedulers, orchestrators, and verification harnesses an agent reaches at runtime through tool calls, queries, APIs, and scripts. Three adjacent concerns sit outside that boundary and are handled by referral rather than by instruction.

**Weight-level unlearning is out of scope**: Where erased content entered a training corpus, an adapter, or a fine-tuning example set, removal from external stores does not remove residue held in model parameters. Editing, retraining, distilling, or unlearning at the weight level is a model-owner activity below the agent layer, and no instruction in this guide directs an agent to attempt it. The agent-layer obligations are bounded and executable: detect whether the content entered a dataset, an adapter, or a deployed checkpoint; remove it from all future dataset versions immediately; run the exposure probes in Step 5.1 against the deployed model; and where those probes return a non-zero residual, open a model-owner escalation carrying a named owner, the probe evidence, and a deadline. The completion attestation then states the parametric residual as an open risk rather than reporting the case closed. Behavioural refusal by a model is never accepted as proof of removal.

**Physical media sanitization is out of scope**: Confirming that bytes were physically reclaimed from a storage device is a platform and infrastructure activity. The agent layer records the earliest lawful deletion date, the known reclamation schedule, and whether reclamation is knowable at all, and reports logical deletion honestly rather than promising physical destruction the platform cannot evidence.

**Capacity-driven tier placement is out of scope**: Promotion and demotion between memory tiers under a capacity constraint is a placement decision, not a forgetting decision. A record demoted to a colder tier remains fully retained and fully answerable to a rights request. Placement enters this guide only where a tier's deletion primitive differs from the primitive available in the tier above it.

**Consolidation and compression are adjacent, not equivalent**: Replacing detail with a shorter derivative reduces exposure but is not a deletion guarantee, because the source, the prompt, the trace, and any vendor copy may persist, and because a summary can preserve the exact fact an erasure request targets. Summaries are treated here as derived artifacts subject to traversal, never as a forgetting mechanism.

### 1.4 Execution Tier Partition

Every unit of work in this method belongs to exactly one execution tier, and the partition is a control rather than a convenience. The tier owning an action determines who may perform it, what evidence it produces, and which component prevails in a disagreement.

**Deterministic tier**: Software, scheduled jobs, queries, schema validators, orchestrators, and APIs own everything requiring exactness, reproducibility, auditability, or scale. This tier evaluates expiry, computes decay arithmetic, selects and executes eviction cohorts, performs the provenance traversal, issues deletion calls to every substrate, writes tombstones, runs residual verification, and writes the audit record. It holds sole delete authority. No delete, no tombstone, and no attestation is ever issued by a model.

**Model tier**: LLM calls own work requiring open-vocabulary judgement no deterministic rule covers. This tier may propose that a record has lost value and supply a rationale; may classify free text for candidate sensitive spans a pattern matcher would miss; may identify semantically equivalent records during a subject-scoped search where exact identifier matching has already failed; may draft the human-readable case summary; and may propose a supersession relationship between two contradicting records. The model tier never decides that an erasure is complete, never selects a final eviction cohort without a deterministic filter, and never authorises a deletion against a record located by similarity alone.

**Hybrid tier**: Work in which the model proposes and software verifies, or software retrieves and the model adjudicates. Every hybrid step names its handoff and its authority holder.

**Tier Assignment and Authority Table**:

| Work unit | Owning tier | Handoff | Authority on disagreement |
| :-- | :-- | :-- | :-- |
| Retention class assignment at write time | Hybrid | Model proposes a class from content; validator enforces schema and policy registry | Deterministic; an unmapped proposal is rejected, never defaulted |
| Expiry evaluation and decay arithmetic | Deterministic | None | Deterministic |
| Eviction candidate proposal | Model | Model emits candidates with rationale codes | Deterministic filter removes any candidate under hold, class conflict, or protected evidence |
| Eviction execution | Deterministic | None | Deterministic |
| Staleness and contradiction detection | Hybrid | Deterministic detects age and field conflict; model adjudicates semantic contradiction | Deterministic; an unadjudicated conflict marks both records non-authoritative |
| Subject-scoped semantic search for unmatched records | Model | Model returns candidate identifiers; orchestrator verifies each against subject linkage | Deterministic; a candidate with no verifiable subject link is escalated, never deleted |
| Provenance traversal and target enumeration | Deterministic | None | Deterministic |
| Tombstone writing and anti-resurrection checks | Deterministic | None | Deterministic |
| Residual-match verification | Deterministic | Model generates paraphrase probe sets; the harness executes and scores them | Deterministic; a model assertion of absence is not a result |
| Completion attestation and audit record | Deterministic | None | Deterministic |
| Over-deletion adjudication | Hybrid | Model assesses whether a restored record was needed; an approver confirms | Human approver above the declared false-forget rate threshold |

**Cost of a tier violation**: A model-issued delete cannot be reproduced, cannot be bounded, and cannot be audited, because the same prompt may produce a different cohort on the next run. Every deletion in this method is therefore executed by a deterministic worker against an explicit target list, and a model's contribution survives only as a recorded proposal beside the deterministic decision that accepted or rejected it.

***

## II. Operational Framework: Governed Reduction of Memory Under Utility and Obligation Policy

The framework runs two paths over shared machinery. Phase 1 is common and mandatory: no record enters the system without a retention class, a purpose, and a lineage root. Phases 2 and 3 carry the utility path. Phases 4 and 5 carry the obligation path, and Phase 5 also verifies the terminal hard deletes issued by the utility path. Phase 6 recovers from over-deletion and recalibrates. A record may traverse both paths in its lifetime, but never in the same job run and never under the same acceptance criteria.

### Phase 1: Retention Class Declaration and Policy Binding

**Objective**: Bind every record at write time to a retention class, a declared purpose, an expiry or review time, and a resolvable lineage root, so that both later paths have a target they can reach and a rule they can apply.

#### Step 1.1: Assign a Retention Class and Purpose at Write Time

**Required Actions**:

- Reject any write lacking a retention class, a processing purpose identifier, a lawful basis where the content is subject-linked, a jurisdiction, and either an expiry time or a review time.
- Assign exactly 1 of the 5 retention classes named in Section 1.2; treat a multi-class proposal as a classification failure and route it to review.
- Derive the retention duration from the declared purpose, never from storage convenience or from a default carried over from a neighbouring record.
- Record the classifier type and, where a model proposed the class, the proposal confidence and the deterministic rule that accepted it.
- Route any record whose model-proposed class confidence falls below 0.80 to a deterministic rule set, and where no rule matches, to the most restrictive candidate class pending human review within 5 business days.

**Required Outputs**:

- A classification record per write, carrying class, purpose identifier, lawful basis, jurisdiction, sensitivity class, retention start time, review time, and expiry time.
- A rejection log naming every write refused at the storage boundary and the missing field.
- A review queue of low-confidence and unmapped classifications with per-item age.

**Quality Checkpoints**:

- 100 percent of accepted writes carry exactly 1 retention class; any write carrying 0 or more than 1 is rejected rather than defaulted.
- Every record in the mandatory-deletion class carries a deletion trigger naming the event or schedule that fires it.
- No review-queue item exceeds 5 business days of age; items above that bound escalate to the policy owner.

***

#### Step 1.2: Record the Lineage Root and Derivation Contract

**Required Actions**:

- Emit a provenance record at every write and at every transform, naming the artifact identifier, its parent artifact identifiers, its subject identifiers, its tenant, its transform type and version, its storage system, its namespace, its region, its key reference where encrypted, and its available deletion primitive.
- Preserve the complete parent set, or a durable manifest of parents, for every many-to-one artifact such as a consolidated summary or a batch embedding.
- Map every dataset, adapter, and deployed checkpoint that consumed subject-linked records back to the subjects it consumed, at the granularity of dataset version.
- Register every substrate that holds a copy, including replicas, snapshots, backups, caches, observability stores, and vendor systems, and record for each whether per-item deletion is available.
- Emit synthetic canary records through every transform path on a schedule no longer than 7 days, and confirm the canary is reachable from its root through every expected derivative.

**Required Outputs**:

- A provenance graph in which every derived artifact resolves to at least 1 parent and 1 deletion primitive.
- A substrate register naming per-substrate deletion capability, lock behaviour, and reclamation knowledge.
- A canary traversal report per transform path with discovered and expected derivative counts.

**Quality Checkpoints**:

- Every artifact class named in the substrate register is reachable from a canary root; an unreachable class is a blocked-risk item, not a passing result.
- Lineage coverage for records in the mandatory-deletion class is 100 percent; any value below 100 percent blocks that domain from serving subject-linked memory.
- No transform emits a derivative without a parent link; an orphan derivative halts the transform until the link is restored.

***

#### Step 1.3: Bind the Policy Registry Version and the Expiry Schedule

**Required Actions**:

- Bind every record to a versioned policy registry entry naming its decay parameters, its staleness budget, its retention duration, and its permitted terminal operations.
- Encode legal holds and approved exceptions as scoped, expiring states carrying a basis, an owner, a start time, a review date, a release authority, and an exact scope expression.
- Suspend every expiry and eviction job for records inside an active hold scope, and record the suspension against the hold rather than silently skipping the record.
- Schedule expiry evaluation at a cadence no coarser than 24 hours for the mandatory-deletion and default-decay classes, and no coarser than 30 days for review-based classes.
- Recompute the original schedule on hold release rather than granting a fresh full retention period.

**Required Outputs**:

- A policy binding record per retention class naming registry version, decay parameters, staleness budget, and permitted operations.
- A hold register with scope expressions, owners, review dates, and suspended job counts.
- An expiry schedule with per-class cadence and a queue-lag measurement.

**Quality Checkpoints**:

- Every active hold carries an owner and a review date; an ownerless or open-ended hold is closed or escalated within 10 business days.
- Expiry queue lag stays at or below 24 hours; lag above 72 hours on the oldest due item escalates to the system owner.
- No record is bound to a policy registry version that has been superseded for more than 30 days without re-evaluation.

***

### Phase 2: Utility Decay and Bounded Eviction

**Objective**: Reduce the serving corpus to the records that still earn their retrieval, storage, and context cost, at a bounded rate and with a reversibility window that makes a mistake recoverable.

#### Step 2.1: Compute Decay and Separate Access From Confirmation

**Required Actions**:

- Store per record the initial authority score, the decay half-life in ordinary time units, the last confirmation time, the last access time, and the reinforcement rule that applies.
- Apply fixed-duration expiry where validity ends at a known boundary such as a one-time code, a temporary grant, a reservation, or a transient tool result, and apply smooth decay where expected utility falls gradually.
- Compute decay deterministically from stored parameters; a model is never asked to estimate a record's current authority score.
- Separate the access counter from the confirmation counter, and permit only an authoritative outcome to reset the confirmation clock, because retrieval frequency can be produced by poison, popularity bias, or a repeated error.
- Cap access-based reinforcement so that automated retrieval alone cannot extend a record's authority beyond 2 consecutive decay half-lives without an authoritative confirmation.

**Required Outputs**:

- A decay state record per record carrying authority score, half-life, last confirmation, last access, and reinforcement count.
- A per-class parameter set naming half-life defaults and reinforcement caps.
- An anomaly list of records whose access reinforcement reached the cap without confirmation.

**Quality Checkpoints**:

- Authority scores are reproducible: recomputing a score from stored parameters at a fixed evaluation time yields the same value on every run.
- No record's authority is refreshed by retrieval alone beyond 2 half-lives; records reaching the cap are routed to revalidation, not to reinforcement.
- Every decay parameter in use resolves to a policy registry version; an unbound parameter halts the decay job for that class.

***

#### Step 2.2: Select the Eviction Cohort Under a Bounded Rate

**Required Actions**:

- Propose eviction candidates from records whose authority score has fallen below the class threshold, whose staleness budget has expired without revalidation, or whose review date passed without renewed justification.
- Permit the model tier to add candidates it judges to have lost value, each carrying a rationale code, and require every model proposal to pass the deterministic filter before it enters the cohort.
- Remove from the cohort every record under an active hold, every record in the protected-evidence class, every record with an open erasure case, and every record whose retention class does not permit the utility path.
- Cap the cohort at 5 percent of the serving corpus per scheduled window as a deployment default; a cohort between 5 and 10 percent requires a named approver, and a cohort above 10 percent halts the job.
- Rank the cohort so that the lowest-authority, most-duplicated, and most-superseded records are evicted first, and retain at least 1 representative of each distinct claim that no successor record covers.

**Required Outputs**:

- A ranked eviction cohort with per-record authority score, rationale code, and proposing tier.
- A filter rejection list naming every candidate removed and the rule that removed it.
- A cohort size record expressed as an absolute count and as a percentage of the serving corpus.

**Quality Checkpoints**:

- 0 records in the protected-evidence class and 0 records under an active hold appear in the cohort; a single such record halts the job and voids the cohort.
- Every model-proposed candidate carries a deterministic acceptance decision; unfiltered model proposals never reach execution.
- Cohort size is at or below 5 percent of the serving corpus, or carries a recorded approver identity.

***

#### Step 2.3: Execute Eviction and Measure the Retrieval Effect

**Required Actions**:

- Execute eviction as a soft delete that marks the record non-serving, writes the eviction identity, and starts the reversibility window; hold the payload for 30 days as a deployment default before the terminal hard delete.
- Invalidate the vector index entry, the lexical index entry, the retrieval result cache, the semantic cache, and any materialised view referencing the record in the same transaction boundary as the soft delete.
- Increment the index generation, or schedule a rebuild and atomic swap, wherever the index engine retains deleted entries in its graph rather than removing them, so that recall degradation and residual reconstructability are bounded.
- Replay a held-out task stream against the pre-eviction and post-eviction corpora and compare task success, retrieval precision, contradiction rate, stale-fact use, latency, and storage.
- Revert the cohort where post-eviction task success falls by more than 1 percentage point, or where retrieval precision fails to improve by at least 3 percentage points against the declared gate.

**Required Outputs**:

- An eviction execution record per record naming soft-delete time, invalidation targets confirmed, index generation before and after, and hard-delete due time.
- A replay comparison report carrying the 6 measured dimensions before and after eviction.
- A revert decision record naming the gate that failed, where the cohort was reverted.

**Quality Checkpoints**:

- Every evicted record shows a confirmed absence from all index and cache paths within 15 minutes of the soft delete; an unconfirmed path blocks the terminal hard delete.
- Post-eviction task success is within 1 percentage point of the pre-eviction baseline; a larger drop reverts the cohort automatically.
- The reversibility window is enforced: no utility-path hard delete executes before 30 days have elapsed, except where an obligation-path case has claimed the record.

***

### Phase 3: Invalidation and Supersession

**Objective**: Strip authority from records that have become false or superseded, so that the system stops answering from them without losing the history a correction depends on.

#### Step 3.1: Detect Staleness and Contradiction

**Required Actions**:

- Assign a staleness budget per relation type, naming the maximum age for direct use, the age at which revalidation becomes mandatory, the source permitted to revalidate, and the action taken when revalidation fails.
- Detect deterministically every record whose age exceeds its budget, and every pair of records that conflict on a typed field for the same subject and relation.
- Route untyped and free-text conflicts to the model tier for adjudication, supplying both records, their timestamps, and their provenance, and requiring a verdict of contradiction, refinement, or independence.
- Mark both records non-authoritative where the model returns no confident verdict, rather than allowing the more recent or the more fluent record to win by default.
- Record the detection outcome with prior state, new state, decay policy identifier, last verified time, and revalidation due time.

**Required Outputs**:

- A staleness budget table per relation type with the 4 declared parameters.
- A conflict inventory naming record pairs, conflict type, adjudication verdict, and adjudicating tier.
- A state transition log for every record moved to unverified, disputed, or stale.

**Quality Checkpoints**:

- Every relation type in the serving corpus carries a staleness budget; an unbudgeted relation type defaults to the most restrictive budget in its class until one is declared.
- 0 conflict pairs remain unadjudicated for more than 7 days; older pairs move both records to non-authoritative automatically.
- Every state transition names the rule or the adjudication that produced it; unattributed transitions are reverted.

***

#### Step 3.2: Apply Supersession and Write the Correction Tombstone

**Required Actions**:

- Record a correction relationship pointing from the superseded record to its authoritative replacement, so the obsolete fact cannot be reinstated from a replica, a summary, or a future import.
- Remove or quarantine the inaccurate serving record, then regenerate or invalidate every derived artifact that absorbed its content, including consolidated summaries, profile fields, and cached results.
- Write a correction tombstone containing the deletion identity, the scope, the effective generation, and a pointer to the replacement, and containing no part of the obsolete payload.
- Retain the superseded record only where a records schedule, a hold, or an audit duty justifies it, and mark it barred from current-state answers while permitting historical queries that declare their intent.
- Propagate the supersession to every replica and every downstream consumer, requiring a per-replica acknowledgement rather than a single global success flag.

**Required Outputs**:

- A supersession record per correction naming predecessor, successor, effective time, and propagation status.
- A correction tombstone per superseded record carrying replacement pointer and retention basis.
- A derived-artifact regeneration list naming every summary, profile field, and cache entry rebuilt or invalidated.

**Quality Checkpoints**:

- 100 percent of replicas acknowledge the supersession before the correction is reported complete; a missing acknowledgement leaves the case open.
- No correction tombstone contains payload content, direct identifiers, or a reversible hash of either.
- Every derived artifact reachable from the superseded record is regenerated or invalidated; a reachable artifact left stale is a supersession failure, not a deferred task.

***

#### Step 3.3: Enforce Non-Serving States Across Every Read Path

**Required Actions**:

- Enumerate every read path that can surface a record, including direct identifier reads, vector search, lexical search, metadata filters, graph traversal, historical APIs, prompt assembly, agent tools, exports, replicas, and restore environments.
- Enforce the non-serving state at the storage or retrieval boundary rather than in prompt instructions, so that a model-generated query cannot override it.
- Test each path with a probe set containing exact, paraphrased, misspelled, translated, and indirect formulations of the suppressed content.
- Fail closed where a read path cannot evaluate the non-serving state, blocking the path rather than serving the record with a warning.
- Record the enforcement result per path with path identifier, probe set version, expected result, and observed result.

**Required Outputs**:

- A read-path inventory with an enforcement mechanism named per path.
- A suppression probe report per path with pass or fail per probe class.
- A fail-closed register naming every path currently blocked and its owner.

**Quality Checkpoints**:

- Every enumerated read path enforces the non-serving state deterministically; a path relying on prompt instruction alone is recorded as unenforced and blocked.
- Suppression probes return 0 disclosures of non-serving content across all 5 probe classes; any disclosure halts serving for that path.
- No read path is exempted from enforcement without a recorded approval carrying an expiry date.

***

### Phase 4: Obligation Erasure and Provenance Traversal

**Objective**: Remove content the system is obliged to erase from every artifact it reached, under a bounded completion time, with anti-resurrection guarantees that survive a stale replica sync and a backup restore.

#### Step 4.1: Validate Intake, Authority, and Scope

**Required Actions**:

- Record every erasure trigger with a request identifier, a type, a receipt time, a channel, a claimed subject scope, a jurisdiction, the controller or processor role, and the case owner.
- Verify the requester's identity through a recorded verification method, and store a restricted verification receipt rather than the identity documents themselves.
- Determine scope deterministically from subject linkage first; invoke the model tier for a subject-scoped semantic search only where exact matching has already failed, and verify every returned candidate against a subject link before it enters the target set.
- Evaluate exceptions and preservation duties before any deletion executes, naming for each retained item the basis, the scope, the approver, and the review outcome.
- Set the internal completion due time at or before the statutory due time, using a deployment default of 30 calendar days from validated intake, and record the extension basis where a statutory extension is invoked with notice.

**Required Outputs**:

- A case record carrying request identity, verification state, jurisdiction, role, scope decision, and both statutory and internal due times.
- A target subject set with per-record match method recorded as exact, linked, or semantic.
- An exception register naming every item retained against the request, with basis and approver.

**Quality Checkpoints**:

- 0 records enter the target set on semantic similarity alone; every semantically located candidate carries a verified subject link or is escalated.
- Every claimed exception names a specific basis and an approver; the label "compliance" alone is rejected as a basis.
- The internal due time is at or before the statutory due time in every case; a later internal due time halts intake.

***

#### Step 4.2: Traverse the Provenance Graph and Enumerate Targets

**Required Actions**:

- Snapshot the provenance graph at case start, and traverse from every root artifact to every reachable derived artifact, recording traversal depth, discovered node count, edge count, and cycle count.
- Enumerate as separate targets, at minimum: the canonical record; every text chunk; every embedding and its vector index entry; every lexical index entry; every graph node and edge; every consolidated summary and reflection that absorbed the content; every episode log entry that quotes it; every profile field derived from it; every cached retrieval result and semantic cache entry; every prompt fragment and trace span; every replica and snapshot; every backup copy; every dataset, adapter, and checkpoint that consumed it; and every vendor-held copy.
- Resolve each target to a substrate, a namespace, a region, a deletion primitive, a reversibility class, and an owner; where a substrate offers no per-item deletion, resolve the target to the enclosing generation, partition, snapshot, key domain, or index that must be rebuilt, expired, or destroyed.
- Compare the discovered node count against the expected artifact-class inventory from the substrate register, and treat any expected class with 0 discovered targets as an unresolved gap rather than as an absence.
- Halt the case and escalate where lineage coverage falls below 100 percent for a mandatory-deletion target set, because a traversal that cannot see an artifact cannot delete it.

**Required Outputs**:

- A traversal record carrying snapshot version, expected and discovered node counts, coverage ratio, depth, and unresolved node count.
- A target list with per-target substrate, namespace, region, deletion method, reversibility class, and owner.
- An unresolved gap list naming every expected artifact class without a resolvable target.

**Quality Checkpoints**:

- Lineage coverage is exactly 100 percent before execution begins; any lower value halts the case and opens an escalation.
- Every target names a deletion primitive; a target whose primitive is unknown is escalated, never assumed deletable.
- The traversal terminates: cycle count is recorded and every cycle is broken by visited-set tracking rather than by a depth cap that silently truncates the graph.

***

#### Step 4.3: Execute the Cascade and Write Anti-Resurrection Tombstones

**Required Actions**:

- Write the tombstone before the first delete executes, carrying the deletion identity token, the scope type and scope token, the creation time, the effective generation, and flags blocking reimport, replay, and replica resurrection; store keyed pseudonyms and hashes only, never the payload.
- Execute deletion against every enumerated target through an idempotent orchestrator with a per-target state machine, retries, a dead-letter queue, and a service-level timer, and record per target the requested, started, acknowledged, and verified times.
- Invalidate and, where the engine retains deleted entries, rebuild and atomically swap every affected index generation, because marking an entry deleted removes queryability without removing the stored representation.
- Require a per-replica acknowledgement and a read-after-delete probe from every region before any target is marked complete, and treat a global success flag issued before quorum as a failed verification.
- Classify every backup and immutable copy as immediately deletable, beyond use until scheduled overwrite, retention-locked until a stated date, or erasable through key destruction, and register a deletion replay that runs against any restore before the restored data is read by an application.
- Issue deletion calls to every vendor holding a copy, record the configured retention mode observed on the call, and treat an accepted API response as initiation rather than as completion.

**Required Outputs**:

- A tombstone record per deletion identity with scope, effective generation, and the 3 anti-resurrection flags.
- A per-target execution ledger with status, attempt count, acknowledgement times, and residual risk code.
- A copy disposition register naming, per backup and immutable copy, its class, its earliest lawful deletion date, and its replay requirement.

**Quality Checkpoints**:

- The tombstone exists and is queryable before the first delete; a cascade started without a tombstone is aborted and restarted.
- 100 percent of targets reach a terminal status of succeeded, excepted, or failed; a target in a generic success count without an individual terminal status voids the case.
- Every failed target sits in a visible dead-letter queue with an owner; a target that disappears from the ledger is a case failure requiring a full re-traversal.

***

### Phase 5: Verification, Attestation, and Audit

**Objective**: Prove that erasure completed by searching for what should no longer exist, and record evidence that survives the deletion it describes without reproducing the deleted content.

#### Step 5.1: Run Residual-Match Verification Across Every Serving Path

**Required Actions**:

- Derive a probe set from the erased content before deletion, storing only keyed hashes and distinguishing fragments needed for matching, and never retaining the payload for verification purposes.
- Query every read path enumerated in Step 3.3 with the probe set, in each of 5 formulation classes: exact, paraphrased, misspelled, translated, and indirect.
- Run a control-plane absence check and a serving-path query for every target, because a control-plane acknowledgement and a row-count change prove neither.
- Attempt reconstruction where the operation was partial: reconstruct from neighbouring fields after redaction; attempt decryption through active, cached, escrowed, and restored key paths after key destruction; restore a backup into an isolated environment and replay the deletion ledger before any read.
- Run extraction probes against the deployed model where the content entered a dataset, an adapter, or a checkpoint, at a stated attack budget of at least 200 prompts spanning the 5 formulation classes, and record the budget, the model version, the access level, and the detection threshold.
- Query a control set of neighbouring authorised records to detect false forgetting caused by an over-broad scope.

**Required Outputs**:

- A verification run record per path carrying test type, artifact class, region, probe set version, expected result, observed result, and evidence reference.
- A residual-match count per path and per formulation class.
- A false-forget probe result naming any authorised neighbouring record that became unreachable.

**Quality Checkpoints**:

- The residual-match count is exactly 0 on every path and in every formulation class; a count of 1 or more reopens the case and blocks attestation without exception.
- Every target carries both a control-plane result and a serving-path result; a target with only 1 of the 2 is unverified.
- The false-forget probe returns 0 unreachable authorised records; any unreachable record opens a Phase 6 recovery case.

***

#### Step 5.2: Reconcile Failed Targets and Bounded Exceptions

**Required Actions**:

- Retry every failed target on an exponential schedule bounded to 5 attempts, then move it to the dead-letter queue with a named owner and a resolution deadline.
- Classify every unresolved target as a retention-locked copy with a stated earliest deletion date, an unresponsive vendor, an immutable log entry, a parametric residual, or an unknown-substrate gap.
- Escalate any target unresolved at day 21 of the 30-day completion bound to the privacy owner and the system owner, so that a notice or an extension can be issued before the statutory due time passes.
- Report exceptions separately from successes rather than counting an excepted target as a completed one.
- Open a model-owner escalation for every parametric residual, carrying the probe evidence, the affected dataset and checkpoint identifiers, a named owner, and a deadline, and record that the agent layer cannot discharge it.

**Required Outputs**:

- A reconciliation record per unresolved target naming class, owner, deadline, and residual risk code.
- An escalation register with per-item age against the 21-day trigger.
- A separated count of targets succeeded, targets excepted, and targets failed.

**Quality Checkpoints**:

- No target is retried more than 5 times without entering the dead-letter queue; unbounded retry is a reconciliation failure.
- 0 excepted targets are counted inside the success total; a merged count voids the attestation.
- Every escalation older than the 21-day trigger has a recorded notice to the requester or a recorded extension basis.

***

#### Step 5.3: Issue the Completion Attestation or Declare a Bounded Failure

**Required Actions**:

- Issue completion only where every enumerated target succeeded or carries an approved exception, lineage coverage is 100 percent, the residual-match count is 0, backup disposition is stated truthfully, and the internal due time was met.
- State in the attestation the scope, the policy version, the request and completion times, target counts by substrate, successful and excepted targets, hold conflicts, backup disposition, vendor status, the verification suite and its results, residual risks, the approver, and the next review date.
- Declare a bounded failure rather than a completion where any condition is unmet, naming what remains, why it remains, until when, and who accepted the residual risk.
- Write the audit record to an append-only store using keyed pseudonyms, coarse reason codes, and evidence references, and exclude payloads, prompts, embeddings, free-text reasons, identity documents, and reversible hashes.
- Retain the tombstone at least as long as the longest replica and backup overwrite cycle plus 30 days, using a deployment default of 400 days, and record its retention basis and expiry.

**Required Outputs**:

- A completion attestation or a bounded-failure declaration carrying all 13 required fields.
- An append-only audit record with a completeness ratio over the mandatory field set.
- A tombstone retention record naming basis, expiry, and the overwrite cycle it is bounded by.

**Quality Checkpoints**:

- No attestation states that all data was deleted where a parametric, immutable, or unresponsive-vendor residual remains; such a statement is a reportable defect.
- Audit field completeness is 100 percent for mandatory-deletion cases; below 98 percent blocks release of the case.
- The audit record contains 0 instances of deleted content, direct identifiers, or reversible hashes, verified by an automated scan before the record is committed.

***

### Phase 6: Recovery From Over-Deletion and Policy Recalibration

**Objective**: Detect and repair removals that should not have happened, and adjust the parameters that produced them, so that the system converges toward the least-retentive policy that preserves required knowledge.

#### Step 6.1: Detect and Adjudicate False Forgetting

**Required Actions**:

- Sample completed evictions and completed erasures at a rate of at least 5 percent per evaluation window, and adjudicate whether each removal should have occurred.
- Detect operationally through failed retrievals, repeated user corrections, re-collection of the same fact, and task failures whose root cause resolves to an absent record.
- Compute the false-forget rate as adjudicated wrongful removals over adjudicated removals, reported separately for the utility path and the obligation path.
- Escalate to the policy owner where the utility-path false-forget rate exceeds 2 percent in a window, and suspend automated eviction where it exceeds 5 percent.
- Treat any obligation-path over-deletion as an incident regardless of rate, because the erased record cannot be recovered from the erasure path itself.

**Required Outputs**:

- An adjudication sample with per-item verdict, adjudicator, and reason code.
- A false-forget rate per path per evaluation window.
- An incident record for every obligation-path over-deletion.

**Quality Checkpoints**:

- The adjudication sample covers at least 5 percent of removals in the window; a smaller sample yields an unreported rate rather than a passing one.
- Utility-path false-forget rate stays at or below 2 percent; a higher rate escalates and a rate above 5 percent suspends automated eviction.
- Every obligation-path over-deletion carries an incident record naming the scope error that produced it.

***

#### Step 6.2: Restore From the Reversibility Window

**Required Actions**:

- Restore wrongly evicted records from the soft-delete quarantine within the 30-day reversibility window, reinstating the canonical record and regenerating its derived artifacts from the restored source.
- Consult the tombstone registry before every restore, and refuse any restore whose deletion identity carries an obligation-path tombstone, because that tombstone represents a duty rather than a convenience.
- Rebuild index generations after a restore and confirm the restored record is reachable from every read path it previously served.
- Record the restore with its cause, the gate that failed to prevent the removal, and the policy parameter implicated.
- Declare the loss irrecoverable where the window has expired, record what was lost and its consequence, and route the cause to Step 6.3 rather than restoring from an unauthorised copy.

**Required Outputs**:

- A restore record per recovered item naming source quarantine, restore time, regenerated artifacts, and reachability confirmation.
- A refusal log naming every restore blocked by an obligation-path tombstone.
- An irrecoverable-loss register with cause and consequence per entry.

**Quality Checkpoints**:

- 0 restores complete against a deletion identity carrying an obligation-path tombstone; a single such restore is a compliance incident.
- Every restored record is reachable from 100 percent of the read paths it previously served; a partial restore is reopened rather than closed.
- Every restore names the policy parameter implicated, so that recalibration has an input.

***

#### Step 6.3: Recalibrate Retention Parameters and Re-Release

**Required Actions**:

- Replay representative task streams under at least 3 candidate configurations: no forgetting, the current policy, and a more aggressive candidate.
- Measure task success, retrieval precision, contradiction rate, stale-fact use, latency, storage, and false-forget cost for each configuration, and include rare future-use queries that require old but valuable records.
- Select the least-retentive configuration that holds task success within 1 percentage point of the no-forgetting baseline and improves retrieval precision by at least 3 percentage points.
- Run the selected configuration in shadow mode for at least 2 evaluation windows, then canary it on low-risk tenants and memory types before general release.
- Recompute every threshold per memory type, per relation type, and per jurisdiction after a change to the workload, the retriever, the model, a substrate, a vendor, or an applicable obligation.

**Required Outputs**:

- A calibration comparison report covering at least 3 configurations across the 7 measured dimensions.
- A selected configuration record naming policy registry version and the gates it satisfied.
- A shadow and canary result set with per-window comparison against the incumbent.

**Quality Checkpoints**:

- The selected configuration satisfies both the task-success and the retrieval-precision gates; failing either returns the incumbent to service.
- No configuration is promoted on fewer than 2 consecutive passing evaluation windows.
- Recalibration follows every material change to workload, retriever, model, substrate, vendor, or obligation; a configuration older than 180 days without re-evaluation is flagged as stale.

***

## III. Implementation Guidance for AI Agents

AI agents operating a memory forgetting policy must follow systematic protocols ensuring that every removal is authorised, bounded, traversed, verified, and recorded. The following guidance translates the two-path framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Classification Gateway**: Enforces the write-time contract, rejecting any write without a retention class, a purpose, a jurisdiction, an expiry or review time, and a lineage root. It may accept a model-proposed class but never a model-supplied deletion decision.
2. **Lineage Service**: Emits provenance records at every write and transform, maintains the substrate register, and answers traversal queries. It owns the canary schedule and reports lineage coverage.
3. **Retention Scheduler**: Evaluates expiry, computes decay arithmetic, applies staleness budgets, and suspends jobs inside active hold scopes. It is deterministic and reproducible on replay.
4. **Eviction Proposer**: The model-tier component that proposes low-value candidates with rationale codes. It holds no delete authority and its output is a proposal record, never an action.
5. **Erasure Orchestrator**: Owns the obligation path. It snapshots lineage, checks holds, writes the tombstone, executes per-target deletion with retries and a dead-letter queue, and drives vendor and replica acknowledgement. It holds sole delete authority for the obligation path.
6. **Verification Harness**: Executes probe sets across every read path, runs reconstruction and extraction probes, and returns residual-match counts. A model may generate its probes; only the harness scores them.
7. **Attestation and Audit Agent**: Writes the append-only record, computes field completeness, issues the completion attestation or the bounded-failure declaration, and blocks release where a mandatory field or a verification result is missing.

**Delete Authority Rule**: Delete authority sits exclusively with the Retention Scheduler for the utility path and the Erasure Orchestrator for the obligation path. Every deletion executes against an explicit, persisted target list. A deletion issued from a model output, a free-text instruction, or an ad hoc query is refused at the storage boundary and logged as an authority violation.

**Workflow Execution Pattern**:

```
STATE: Obligation_Erasure_Cascade
INPUTS:
  1. Validated case record from Step 4.1
  2. Lineage snapshot and target list from Step 4.2
  3. Hold register and exception register
ACTIONS:
  1. Write tombstone with deletion identity, scope, effective generation
  2. Execute per-target deletion through idempotent workers
  3. Invalidate caches; rebuild and atomically swap affected index generations
  4. Collect per-replica acknowledgements and per-region read-after-delete probes
  5. Issue vendor deletion calls and record configured retention mode
VALIDATION:
  - lineage_coverage_ratio == 1.00
  - tombstone_written_before_first_delete == TRUE
  - targets_with_terminal_status == targets_expected
  - replica_acknowledgement_ratio == 1.00
  - residual_match_count == 0
  - hold_conflict_count == 0
TRANSITIONS:
  IF all_validations_pass THEN next_state = Attestation_Issue
  IF residual_match_count > 0 THEN next_state = Cascade_Reopen
  IF lineage_coverage_ratio < 1.00 THEN next_state = Coverage_Escalation
  IF elapsed_days >= 21 AND unresolved_targets > 0
     THEN next_state = Privacy_Owner_Escalation
  IF validation_failed THEN next_state = Erasure_Error_Handling
```

**Two-Phase Action Pattern**: Emit the enumerated target list, the tombstone content, and the projected substrate impact without executing any deletion; validate the list against holds, retention classes, and coverage while nothing is committed; execute only after validation passes, recording each target's terminal status in the same operation that performs it.

**Approval Gate**: Human authorisation is required before an eviction cohort exceeding 5 percent of the serving corpus, before any cohort at all where the utility-path false-forget rate exceeded 2 percent in the previous window, before releasing a legal hold, before accepting a crypto-shred as the sole deletion method for a target class, before issuing an attestation carrying a parametric or immutable residual, and before any deletion targeting the protected-evidence class. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the case record, target list, hold register, and execution ledger in durable state, because an erasure case routinely outlives a single context window and a partially executed cascade must be resumable.
- Process target lists in bounded batches with a persisted cursor, so that a restart resumes rather than re-enumerates.
- Write a handoff record at every context boundary naming case identity, coverage ratio, targets completed, targets outstanding, open escalations, and the internal due time.
- Never hold deleted payload content in working context after the probe hashes are derived; verification operates on hashes and fragments, not on retained copies.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Classification Integrity (After Phase 1)**

- **Automated Check**: 100 percent of accepted writes carry exactly 1 retention class, a purpose identifier, an expiry or review time, and a resolvable lineage root; canary traversal reaches every registered artifact class.
- **Agent Action on Pass**: Permit the domain to serve subject-linked memory.
- **Agent Action on Failure**: Block writes for the affected memory type until the contract is enforced; do not accept unclassified writes with a backfill promise.
- **Human Review Trigger**: Lineage coverage below 100 percent for any mandatory-deletion domain, or a review queue item older than 5 business days.

**Checkpoint 2: Eviction Safety (After Phase 2)**

- **Automated Check**: 0 protected-evidence and 0 held records in the cohort; cohort size at or below 5 percent of the serving corpus; every model proposal carries a deterministic acceptance decision; post-eviction task success within 1 percentage point of baseline.
- **Agent Action on Pass**: Start the 30-day reversibility window and schedule the terminal hard delete.
- **Agent Action on Failure**: Revert the cohort from quarantine and rebuild affected index generations.
- **Human Review Trigger**: Cohort size above 5 percent, or a retrieval-precision gain below 3 percentage points across 2 consecutive windows.

**Checkpoint 3: Suppression Enforcement (After Phase 3)**

- **Automated Check**: Every enumerated read path enforces the non-serving state at the storage or retrieval boundary; suppression probes return 0 disclosures across all 5 formulation classes; 100 percent of replicas acknowledge each supersession.
- **Agent Action on Pass**: Proceed with normal serving.
- **Agent Action on Failure**: Fail closed on the affected path and block it from serving until enforcement is restored.
- **Human Review Trigger**: Any path enforcing suppression only through prompt instruction, or any conflict pair unadjudicated beyond 7 days.

**Checkpoint 4: Traversal Completeness (After Phase 4)**

- **Automated Check**: Lineage coverage exactly 100 percent; tombstone written before the first delete; every target carries a named deletion primitive and a terminal status; per-replica acknowledgement ratio 1.00.
- **Agent Action on Pass**: Proceed to verification.
- **Agent Action on Failure**: Halt the cascade, restore the case to enumeration, and re-traverse from a fresh lineage snapshot.
- **Human Review Trigger**: Any unresolved artifact class, or any substrate offering no per-item deletion primitive within the case scope.

**Checkpoint 5: Zero-Residual Verification (After Phase 5)**

- **Automated Check**: Residual-match count exactly 0 on every read path and in every formulation class; both a control-plane and a serving-path result present per target; excepted targets reported separately from successes; audit field completeness at 100 percent for mandatory-deletion cases.
- **Agent Action on Pass**: Issue the completion attestation.
- **Agent Action on Failure**: Reopen the cascade; an attestation is never issued with a warning attached to a non-zero residual.
- **Human Review Trigger**: Any residual match, any parametric residual, or any target unresolved at day 21 of the completion bound.

**Checkpoint 6: Recovery and Calibration (After Phase 6)**

- **Automated Check**: Adjudication sample covers at least 5 percent of removals; utility-path false-forget rate at or below 2 percent; 0 restores executed against an obligation-path tombstone; the selected configuration passed 2 consecutive windows.
- **Agent Action on Pass**: Promote the configuration and update the policy registry version.
- **Agent Action on Failure**: Return the incumbent configuration to service and withhold promotion.
- **Human Review Trigger**: False-forget rate above 2 percent, any obligation-path over-deletion, or any irrecoverable-loss entry.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
PATH: UTILITY | OBLIGATION | BOTH
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Incomplete Traversal**

- **Symptoms**: Lineage coverage below 100 percent; an expected artifact class returns 0 discovered targets; a residual match surfaces from a summary, a cache, or an index that no target covered.
- **Diagnostic Steps**: Compare the discovered node set against the substrate register; replay a canary through the transform paths that produce the missing class; determine whether the gap is a missing provenance edge, an unregistered substrate, or a many-to-one artifact that discarded its parent set.
- **Resolution Protocol**: Option A, restore the missing edge at the transform and re-traverse from a fresh snapshot. Option B, where the parent set was discarded, resolve the target to the enclosing generation and rebuild that generation from sanitized inputs. Option C, where the substrate was unregistered, register it, enumerate its contents by subject, and treat every prior case touching that substrate as requiring re-verification.
- **Escalation Trigger**: A coverage gap unresolved after 2 re-traversals escalates to the system owner and blocks the affected domain from serving subject-linked memory.

**Error Type 2: Resurrection After Deletion**

- **Symptoms**: Erased content reappears after a replica sync, a backup restore, an event replay, a re-import, or a re-extraction; a residual-match probe that passed at attestation fails on a later audit.
- **Diagnostic Steps**: Identify the reintroduction path from the artifact's creation time and its producing service; confirm whether the tombstone existed at that time, whether the path consults the tombstone registry, and whether the effective generation was advanced.
- **Resolution Protocol**: Option A, add a mandatory tombstone check to the reintroduction path and fail closed where the registry is unreachable. Option B, advance the effective generation so that any artifact predating it is rejected on read. Option C, where the source is a restored backup, register a deletion replay that runs before any application read of restored data.
- **Escalation Trigger**: Any confirmed resurrection is an incident regardless of volume; a second resurrection through the same path suspends that path until the tombstone check is verified by probe.

**Error Type 3: Tier Authority Violation**

- **Symptoms**: A deletion executes with no persisted target list; a cohort differs between two runs of the same job on unchanged data; an audit entry names a model as the acting component; an erasure marked complete carries no verification record.
- **Diagnostic Steps**: Trace the deletion event to its actor identity and its target list reference; confirm whether the target list was persisted before execution; check whether the model output was consumed as an action rather than as a proposal.
- **Resolution Protocol**: Option A, revoke the delete credential from the offending component and re-route its output into the proposal queue. Option B, reconstruct the affected removals from the quarantine and the audit trail, then re-execute them through the authorised orchestrator. Option C, where reconstruction is impossible, record the loss in the irrecoverable-loss register and report it as an over-deletion incident.
- **Escalation Trigger**: A single model-issued delete halts automated forgetting across the affected domain until the authority boundary is re-verified.

**Error Type 4: Substrate Refuses Deletion**

- **Symptoms**: A retention-locked object rejects deletion; an append-only log cannot remove one entry; an index engine acknowledges deletion while the stored representation remains reconstructible; a vendor returns an acceptance but no completion evidence.
- **Diagnostic Steps**: Read the substrate register for the target's lock behaviour and reclamation knowledge; determine whether the block is a retention lock, an immutability guarantee, a compaction schedule, or an unimplemented deletion primitive.
- **Resolution Protocol**: Option A, where the data was encrypted before storage and key granularity matches deletion granularity, destroy every usable copy of the subject key and verify decryption failure across active, cached, escrowed, and restored key paths. Option B, rebuild the enclosing generation, partition, or index from sanitized inputs and atomically swap it, then retire the old artifact on its earliest lawful date. Option C, record the copy as beyond use with a restore block, a stated overwrite date, and a deletion replay, and disclose it in the attestation.
- **Escalation Trigger**: A target with no viable option after 5 orchestrator attempts enters the dead-letter queue with a named owner, and escalates to the privacy owner at day 21 of the completion bound.

**Error Type 5: Over-Deletion and Institutional Amnesia**

- **Symptoms**: Rising task failures traced to absent records; users repeating information the system previously held; retrieval returning fewer than the requested candidates; a false-forget rate above the declared threshold.
- **Diagnostic Steps**: Adjudicate a sample of recent removals; determine whether the cause is an over-aggressive decay half-life, an over-broad erasure scope, an access-reinforcement cap set too low, or a cohort ranking that removed the sole representative of a claim.
- **Resolution Protocol**: Option A, restore from quarantine within the reversibility window and lengthen the implicated half-life by the measured margin. Option B, tighten the cohort ranking so that at least 1 representative of each uncovered claim is retained. Option C, suspend automated eviction for the affected memory type and run in shadow mode until 2 consecutive windows pass the false-forget gate.
- **Escalation Trigger**: A false-forget rate above 5 percent suspends automated eviction; an obligation-path over-deletion is an incident on first occurrence and is never resolved by retry.

**Error Type 6: Path Confusion Between Utility and Obligation**

- **Symptoms**: An erasure case closed by pointing at a scheduled expiry; an eviction metric that moves with request volume; a retrieval filter recorded as satisfying a rights request; a hold overridden by a decay job.
- **Diagnostic Steps**: Inspect the case record for a traversal, a tombstone, and a verification result; check whether the retention class permitted the path that acted; confirm whether the hold register was consulted before the job ran.
- **Resolution Protocol**: Option A, reopen the case and run the full obligation path regardless of whether the record still exists, because the tombstone and the attestation are themselves required outputs. Option B, separate the metric series so that eviction volume and erasure volume are never aggregated. Option C, move hold evaluation into the scheduler's pre-filter so that no job can act on a held record.
- **Escalation Trigger**: Any erasure obligation recorded as discharged by a utility mechanism is reported to the privacy owner within 1 business day and re-executed through the obligation path.

**Troubleshooting Decision Tree**:

```
FORGETTING OPERATION FAILS ITS CHECKPOINT
├─ COVERAGE DEFECT
│   ├─ Expected artifact class has zero targets → Replay canary; restore transform edge
│   ├─ Many-to-one parent set discarded → Resolve to enclosing generation; rebuild
│   └─ Substrate unregistered → Register; re-verify every prior case touching it
├─ PERSISTENCE DEFECT
│   ├─ Content reappears after replica sync → Advance effective generation; enforce tombstone check
│   ├─ Content reappears after restore → Register deletion replay before application read
│   └─ Index acknowledges but retains representation → Rebuild generation; atomic swap
├─ AUTHORITY DEFECT
│   ├─ Delete issued without persisted target list → HALT domain; revoke credential
│   ├─ Cohort not reproducible across runs → Re-route model output to proposal queue
│   └─ Hold ignored by scheduler → Move hold evaluation into the pre-filter
├─ SCOPE DEFECT
│   ├─ Authorised neighbour unreachable → Restore from quarantine; narrow the scope
│   ├─ False-forget rate above threshold → Suspend eviction; lengthen half-life
│   └─ Semantic match with no subject link → Escalate; never delete on similarity alone
└─ PATH DEFECT
    ├─ Erasure closed by an expiry → Reopen; run traversal, tombstone, verification
    ├─ Filter recorded as erasure → Reopen; a suppression is not a removal
    └─ Parametric residual detected → Escalate to model owner; state residual in attestation
```

### D. Performance Metrics and Continuous Learning

**Completeness and Correctness Metrics**:

- **Deletion completeness**: Verified successful targets over expected targets, with exceptions reported separately (target: 100 percent for mandatory-deletion cases).
- **Lineage coverage**: Discovered targets and covered artifact classes over expected classes (target: 100 percent; any lower value blocks execution).
- **Post-deletion residual-match rate**: Probes returning erased content over probes executed, across all read paths and formulation classes (target: 0; there is no tolerated non-zero value).
- **Resurrection incidence**: Confirmed reappearances per 1,000 completed cases (target: 0; any occurrence is an incident).
- **Extraction-probe success rate**: Successful recoveries over attempts at the stated attack budget (target: 0 at a budget of at least 200 prompts; a non-zero result opens a model-owner escalation).

**Utility and Cost Metrics**:

- **Retrieval precision gain**: Improvement in retrieval precision after eviction against the pre-eviction baseline (target: at least 3 percentage points; below that the cohort is reverted).
- **Task success delta**: Change in task success after eviction (target: within 1 percentage point of the no-forgetting baseline).
- **False-forget rate**: Adjudicated wrongful removals over adjudicated removals, reported per path (target: at or below 2 percent on the utility path; 0 on the obligation path).
- **Stale-fact use rate**: Answers grounded in a record past its staleness budget (target: at or below 1 percent).
- **Net storage and serving saving**: Storage, index, and context savings less orchestration, rebuild, key management, verification, and audit cost (target: positive; a negative value means the policy is buying noise reduction at a cost the deployment has not justified).

**Governance and Timeliness Metrics**:

- **Completion latency**: Validated intake to attestation (target: at or below 30 calendar days; day 21 triggers escalation).
- **Statutory compliance rate**: Cases completed within the applicable statutory window (target: 100 percent, with every extension recorded and notified).
- **Hold correctness**: Held records acted on by any job (target: 0), and holds without an owner or a review date (target: 0).
- **Vendor acknowledgement latency**: Deletion call to vendor completion evidence (target: at or below 14 calendar days; unacknowledged at 21 days escalates).
- **Audit field completeness**: Mandatory fields present over mandatory fields required (target: 100 percent for mandatory-deletion cases; below 98 percent blocks release).

**Log-Pattern Failure Detection**: A rising unresolved-node count indicates a transform emitting orphan derivatives. A residual match confined to one region indicates an unacknowledged replica. A residual match confined to summaries indicates that consolidation ran without parent manifests. Cohorts that differ between identical runs indicate a model output consumed as an action. Erasure volume tracking eviction volume indicates the two paths have been merged in reporting. A false-forget rate rising while precision gain stays flat indicates a half-life shorter than the workload requires.

**Learning and Adaptation Mechanisms**:

- **Parameter memory**: Retain per memory type the decay half-life, staleness budget, cohort size, measured precision gain, and measured false-forget rate, so that calibration improves against observed history rather than against intuition.
- **Traversal template refinement**: Where a residual match is traced to an artifact class the traversal missed, add that class to the expected inventory permanently rather than patching the single case.
- **Probe set growth**: Add every formulation that produced a residual match to the standing probe set, so that the verification suite strengthens monotonically.
- **Threshold recalibration**: Recompute every threshold per memory type, relation type, and jurisdiction; the values stated in this guide are deployment defaults, not measured constants.

**Human-in-the-Loop Boundaries**: Release of a legal hold, acceptance of an attestation carrying a residual, approval of an eviction cohort above the declared rate, deletion touching the protected-evidence class, and the decision to declare a loss irrecoverable are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the authority and reachability of stored records rather than their subject matter. Its phases hold wherever an agent writes records that outlive a session, derives artifacts from them, and faces both a cost of keeping and a duty to remove.

### 4.1 Cross-Domain Application Patterns

**Clinical and care coordination**: The staleness budget dominates, because a medication instruction, an allergy record, and a contact preference change at different rates and carry different consequences for a stale answer. Retention classes lean toward protected evidence and archival retention, since records schedules frequently mandate preservation that outlives any product purpose. The utility path is restricted to derived convenience artifacts such as caches and consolidated summaries, and never touches the clinical record itself. Erasure cases are frequently partial: the serving copy is removed while a scheduled record is retained, and the attestation must state that division precisely rather than reporting a clean deletion.

**Financial services and regulated advice**: Preservation duties routinely override deletion for a bounded scope, so the hold register becomes the busiest component and hold release is the highest-risk automated action. Immutable and retention-locked storage is common, making crypto-shredding and generation rebuild the practical deletion primitives, and making the earliest-lawful-deletion date a first-class field. The audit record is a deliverable rather than a diagnostic aid, and audit field completeness below 100 percent blocks a case rather than degrading a metric.

**Consumer software and personalisation**: Utility forgetting carries the most value here, because inferred preferences accumulate quickly, contradict each other, and dilute retrieval. Decay half-lives are short, the eviction cohort runs frequently, and the reversibility window is the principal safety net. Erasure volume is driven by subject requests at scale, so the obligation path must be automated end to end with human review reserved for exceptions, and the traversal must reach personalisation profiles and recommendation caches that were derived from the erased records.

**Industrial operations and field robotics**: Observations are numerous, cheap, and rapidly obsolete, so access-based retention is tempting and dangerous: a sensor reading retrieved often may be retrieved because a fault repeats, not because it is valuable. The separation of access from authoritative confirmation matters most in this domain. Erasure obligations are rarer but concentrate in personnel and site-access records, and the substrate register must cover edge caches and locally stored worker state that a central traversal would otherwise miss.

**Public-sector case handling**: Records schedules, freedom-of-information duties, and archival mandates create the largest population of protected-evidence records, and the most frequent conflict between a rights request and a preservation duty. The exception register carries most of the reasoning, and every exception must name a specific basis and approver. Correction and supersession matter as much as deletion, because reinstating a corrected fact from a replica is itself a reportable error.

**Multi-tenant platforms and processors**: Deletion granularity must match key granularity and tenant boundaries, so a shared key that cannot erase one subject without erasing all is a design defect rather than an operational inconvenience. Processor obligations propagate to subprocessors, so the vendor register and its acknowledgement latency become gating measures. Cross-tenant derived artifacts, such as a shared index or an aggregate model input, require either per-tenant partitioning or a rebuild path declared before launch.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small deployments under 100,000 records**: Retain all 6 phases but collapse the eviction cohort to a monthly run, keep the reversibility window at 30 days, and accept manual adjudication of the 5 percent sample. Lineage remains mandatory: a small store still derives summaries, embeddings, and caches, and a traversal that was never built cannot be built during a case.
- **Large deployments above 10,000,000 records**: Batch the traversal with a persisted cursor, cap the cohort at 5 percent of the serving corpus per window regardless of absolute volume, and shard verification probe execution by region. Report residual-match counts per path rather than aggregated, because a single failing path is invisible in a global figure.
- **High-obligation domains**: Shorten the internal completion bound below the statutory bound by at least 7 days, require dual approval for hold release, and run the verification suite on a recurring audit schedule against closed cases rather than only at closure.
- **Low-latency serving paths**: Enforce non-serving states through the index and the storage boundary rather than through a post-retrieval filter, because a filter adds latency to every query and fails open under load. Where a path cannot afford the check, it must be excluded from serving subject-linked memory entirely.
- **Ephemeral or session-scoped agents**: Where no record outlives the session and no derived artifact is persisted, this framework reduces to Phase 1 classification and a session-termination purge. Where value of future recall is unproven and deletion cannot be guaranteed at the required risk level, the correct decision is no persistent memory at all.
- **Distributed and multi-region deployments**: Treat per-replica acknowledgement and per-region read-after-delete probes as mandatory rather than as a completeness refinement, and advance the effective generation on every deletion so that a straggler replica cannot reintroduce content that a global success flag already reported gone.

***

## V. Limitations and Considerations

**Deletion completeness is relative to a declared scope**: No finite test proves absolute absence, and a residual-match count of 0 means only that the declared probe set, at the stated budget, across the enumerated paths, found nothing. The mitigation is to state the attack budget, the probe classes, the access level, and the paths tested in every attestation, and to grow the standing probe set with every formulation that ever produced a match, so the claim strengthens with experience rather than being asserted once.

**Lineage cannot be reconstructed after the fact**: A provenance graph not written at creation time cannot be recovered by inspecting the artifacts it should have described, because a derived artifact rarely carries a reliable pointer to its parents. The mitigation is the write-time contract in Phase 1, which rejects unclassified and unlinked writes at the storage boundary, and the canary schedule that detects a missing edge within 7 days rather than during a case.

**Logical deletion is not physical reclamation**: Several substrates acknowledge a deletion while retaining the stored representation until a compaction, a rebuild, or a scheduled overwrite, and recent work has shown that soft-deleted embeddings can remain reconstructible from index storage. The mitigation is the generation rebuild and atomic swap in Step 4.3, together with an attestation that reports logical deletion honestly and names the earliest lawful physical deletion date rather than promising destruction the platform cannot evidence.

**Weight-level residue is outside this framework's reach**: Where erased content entered a training corpus, an adapter, or a deployed checkpoint, no agent-layer action removes it, and behavioural refusal is not evidence of removal. The mitigation is the bounded referral in Section 1.3: detect the exposure, remove the content from all future dataset versions, probe the deployed model, escalate a non-zero result to a named model owner with a deadline, and disclose the residual in the attestation rather than closing the case.

**Every threshold here is a deployment default**: The 30-day reversibility window, the 5 percent cohort cap, the 2 percent false-forget escalation, the 3 percentage-point precision gate, the 200-prompt attack budget, the 400-day tombstone retention, and the 30-day internal completion bound were selected to be operable on first deployment, not derived from a measured property of memory systems. The single exception is the residual-match tolerance of 0, which is a definitional requirement rather than a tuned parameter. The mitigation is the recalibration obligation in Step 6.3 and Section III.D, which requires each deployment to recompute its thresholds against observed outcomes per memory type and jurisdiction.

**Legal states are engineering approximations of legal advice**: Retention classes, hold semantics, exception bases, and completion bounds are modelled here so that software can act on them, but the applicable duties depend on jurisdiction, role, and sector, and change over time. The statutory response windows cited in the references are transcribed from the originating sources and were not re-verified as current law during this conversion. The mitigation is that counsel approves the records schedule, the exception list, and the release authority, and that the policy registry is versioned so that a legal change produces a re-evaluation rather than a silent drift.

**Utility forgetting can produce institutional amnesia that no metric catches quickly**: A record's value may become apparent only years after its removal, and a replayed task stream drawn from recent history will not contain the query that needed it. The mitigation is the inclusion of rare future-use queries in the calibration replay in Step 6.3, the requirement to retain at least 1 representative of each uncovered claim during cohort ranking, and the 30-day reversibility window that makes a recent mistake recoverable.

**Verification telemetry can itself become an exposure**: A log rich enough to prove that deletion happened is rich enough to reproduce what was deleted, and probe sets derived from erased content are a particular hazard. The mitigation is the audit contract in Step 5.3, which restricts the record to keyed pseudonyms, coarse reason codes, and evidence references, scans for payload content before commit, and permits probe storage only as hashes and non-reconstructive fragments.

**Structural conformance is not a discharged obligation**: A case can satisfy every checkpoint in this guide and still have erased the wrong records, or retained the right ones for the wrong reason. The framework detects malformed forgetting, not misdirected policy, and no checkpoint substitutes for human review of the retention schedule and the exception basis.

***

## VI. Conclusion and Summary

Memory forgetting policy is a governance discipline before it is a storage optimisation. Its two paths are not two settings of one dial. Utility forgetting answers the question of what still earns its place, is verified against task quality, and is recoverable within a declared window. Obligation erasure answers the question of what must cease to exist, is verified against a residual-match count of zero, and is not recoverable at all. A system that runs one path and reports it as both will eventually satisfy a rights request with a retrieval filter and discover the fact only when someone else finds the record.

The structural claim this guide rests on is that deletion in an agent memory system is a graph traversal. One statement reaches chunks, embeddings, index entries, graph edges, consolidated summaries, episode logs, profile fields, caches, prompts, traces, replicas, backups, datasets, and vendor copies, and a deletion endpoint holding only a canonical identifier reaches none of them. The traversal is only as good as the provenance written at creation time, which is why the write-time contract in Phase 1 is not preparatory work but the load-bearing control. The tombstone is what keeps the result stable once achieved, because a stale replica, a restored backup, or a replayed event will otherwise undo a completed cascade without anyone issuing a write.

A team introducing governed forgetting should build the minimum path for one bounded memory domain and prove it end to end before expanding. Enforce classification and lineage at the storage boundary, implement the reversible operations first, then implement the cascade with tombstones and per-target status, then the verification harness, and only then the attestation. Expand to a second domain after a case has been completed, verified at zero residual, and re-audited some weeks later without a resurrection.

**Key Success Factors**:

- **Two paths, never merged**: Utility forgetting and obligation erasure carry different triggers, verification standards, and consequences, and neither is ever recorded as discharging the other.
- **Classification and lineage at write time**: A record without a retention class, a purpose, an expiry, and a lineage root is refused, because nothing later in the method can reach it.
- **Deletion as traversal**: Every erasure enumerates every derived artifact, resolves each to a deletion primitive, and reaches 100 percent lineage coverage before a single delete executes.
- **Tombstones before deletes**: Anti-resurrection markers exist and are consulted by every reintroduction path, so a completed cascade stays completed across replicas, restores, and replays.
- **Zero residual, proven not asserted**: Completion requires a residual-match count of exactly 0 across every serving path and formulation class, produced by a harness rather than claimed by a model.
- **Sole delete authority in deterministic software**: Models propose and adjudicate; software filters, executes, verifies, and attests, and a model-issued delete halts the domain.
- **Honest attestation**: What remains, why it remains, until when, how it was tested, and who accepted the residual risk are stated plainly, and no residual is concealed behind a claim that all data was deleted.

By following this guide, AI agents can reduce what they hold to what still earns its place, remove what they are obliged to remove across every artifact it reached, and support a claim of forgetting with evidence a reviewer can audit rather than with an accepted API response.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. Three areas were confirmed by independent search during conversion and are marked as such: the statutory response windows under the European and Californian regimes, the retention of deleted entries by graph-based vector indexes until compaction or rebuild, and the state of weight-level unlearning verification, which supports the out-of-scope treatment in Section 1.3.

**Corpus pointers**:

- `Memory Forgetting Policies for AI Agents: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the reversibility taxonomy, the retention class families, the derived-data and lineage-first argument, the substrate-specific deletion limits, the crypto-shredding preconditions, the incident-containment use, the verification and attestation requirements, the logging field inventory, the release gates, and the end-to-end workflow. Its external citations are transcribed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — companion guidance on the overall memory lifecycle, applicable to the write-time contract in Phase 1.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on evidence-gated promotion of episodes into durable records, which it frames as a promotion pipeline rather than as a compression job; applicable to the consolidated summaries treated as derived artifacts in Step 4.2.
- `advanced_task_guides/memory-management/guide_SemanticMemory.md` — owns the claim store in which supersession closes a validity interval and produces a successor version rather than removing anything; applicable to the supersession and correction tombstones in Step 3.2, which this guide governs as a non-serving state.
- `advanced_task_guides/memory-management/guide_DistributedMemoryArchitecture.md` — owns replication, partitioning, and the consistency contract across failure domains; applicable to the enumeration of serving paths in Step 4.2 and the residual-match verification in Step 5.1, which must reach every replica and backup rather than one primary.
- `advanced_task_guides/memory-management/guide_HierarchicalMemory.md` — companion guidance on capacity-driven tier placement, which Section 1.3 excludes from the scope of forgetting.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — companion guidance on episode logs, which the provenance traversal in Step 4.2 must reach.
- `advanced_task_guides/memory-management/guide_StructuredMemory.md` — companion guidance on typed records and field-level conflict, applicable to the deterministic detection in Step 3.1.
- `advanced_task_guides/memory-management/guide_LatentMemoryNetworks.md` — companion guidance on representation-level storage, applicable to the embedding and index targets in Step 4.2.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the audit contract in Step 5.3.
- `advanced_task_guides/policy-risk/guide_InformationDependencyDisclosureRiskAnalysis.md` — companion guidance on disclosure exposure, applicable to the residual-match verification in Step 5.1.

**External references**:

*Retrieval quality, staleness, and the case for removal*

1. Xiong and colleagues, *How Memory Management Impacts LLM Agents* — https://arxiv.org/abs/2505.16067
2. *Memory-R1* — https://arxiv.org/html/2508.19828v2
3. *Human-Inspired Memory Architecture* — https://arxiv.org/html/2605.08538v1
4. *STALE: current-state adjudication benchmark* — https://arxiv.org/html/2605.06527v1

*Memory poisoning and containment*

5. *MemoryGraft* — https://arxiv.org/html/2512.16962v1
6. *Systematic memory-poisoning study* — https://arxiv.org/html/2606.04329v1

*Cognitive-science background on forgetting*

7. Wimber and colleagues, *Retrieval induces adaptive forgetting of competing memories via cortical pattern suppression* — https://pmc.ncbi.nlm.nih.gov/articles/PMC4394359/
8. Murayama and colleagues, *Forgetting as a consequence of retrieval: a meta-analytic review of retrieval-induced forgetting* — https://pubmed.ncbi.nlm.nih.gov/25180807/

*Data protection duties, response windows, and storage limitation*

9. European Union, *General Data Protection Regulation, consolidated text* — https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02016R0679-20160504
10. Information Commissioner's Office, *Right to erasure* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/ (response window independently confirmed during conversion)
11. Information Commissioner's Office, *Storage limitation* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-protection-principles/a-guide-to-the-data-protection-principles/storage-limitation/
12. California Attorney General, *California Consumer Privacy Act* — https://oag.ca.gov/privacy/ccpa (response window independently confirmed during conversion)
13. California Privacy Protection Agency, *CCPA regulations effective 2026* — https://cppa.ca.gov/regulations/pdf/ccpa_statute_eff_20260101.pdf

*Sectoral retention duties*

14. United States Department of Health and Human Services, *Does HIPAA require covered entities to keep medical records for any period of time* — https://www.hhs.gov/hipaa/for-professionals/faq/580/does-hipaa-require-covered-entities-to-keep-medical-records-for-any-period/index.html
15. United States Securities and Exchange Commission, *Electronic recordkeeping requirements for broker-dealers* — https://www.sec.gov/rules-regulations/2022/10/electronic-recordkeeping-requirements-broker-dealers-security-based-swap-dealers-major-security

*Substrate deletion limits and sanitization*

16. National Institute of Standards and Technology, *SP 800-88 Revision 2, Guidelines for Media Sanitization* — https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-88r2.pdf
17. Pinecone, *Delete records* — https://docs.pinecone.io/guides/manage-data/delete-data
18. Pinecone, *Data deletion in production* — https://docs.pinecone.io/guides/production/data-deletion
19. Apache Kafka, *Topic configuration* — https://kafka.apache.org/41/configuration/topic-configs/
20. Amazon Web Services, *Managing S3 Object Lock* — https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-managing.html
21. Amazon Web Services, *Working with delete markers* — https://docs.aws.amazon.com/AmazonS3/latest/userguide/ManagingDelMarkers.html
22. *Ghost Vectors: Soft-Deleted Embeddings Remain Reconstructible in HNSW Vector Databases* — https://arxiv.org/html/2606.18497v1 (retrieved during conversion; supports the index rebuild requirement in Step 4.3 and the limitation on logical deletion in Section V)

*Vendor retention configuration*

23. OpenAI, *Data controls in the API* — https://developers.openai.com/api/docs/guides/your-data
24. Anthropic, *Zero data retention* — https://docs.anthropic.com/en/docs/build-with-claude/zero-data-retention

*Model-level residue and verification, referenced as out of scope*

25. European Data Protection Board, *Opinion 28/2024 on AI models and personal data* — https://www.edpb.europa.eu/system/files/2024-12/edpb_opinion_202428_ai-models_en.pdf
26. *Towards Reliable Forgetting: A Survey on Machine Unlearning Verification* — https://arxiv.org/html/2506.15115v3 (independently confirmed during conversion)
27. *Data Extraction after Exact Unlearning* — https://arxiv.org/abs/2505.24379

