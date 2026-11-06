# Working Memory

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Working memory constitutes the task family of maintaining the bounded, task-scoped state that governs a single reasoning episode: the goal, the constraints, the plan, the open subtasks, the intermediate results, the recent observations, and the pending decisions. This guide provides AI agents with a structured protocol for treating that state as a versioned object owned by deterministic software rather than as text accumulating in a transcript. It separates working memory from the context window, which is a transport carrying a serialized projection of state into each model call, and from long-term memory, which receives only items promoted through a separate governed write. It specifies a declared schema with a capacity bound, an admission gate that binds provenance and freshness to every item, turn-level maintenance that refreshes expired observations and detects absent progress, an eviction and compaction policy protected by a preservation manifest, a token budget for serialization, and a recovery procedure that reconciles external effects before any action resumes. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that state survives context boundaries, tool failures, and process restarts rather than being silently reconstructed from a transcript.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Working memory**: The bounded, task-scoped, provenance-bearing state that governs one reasoning episode and is discarded when that episode closes. It holds the goal, constraints, plan, open subtasks, open variables, admitted evidence, error state, budgets, and pending decisions. It is not the transcript, the context window, the user profile, the knowledge base, or the durable history.

**Working state object**: The single canonical representation of working memory: a typed, versioned record with a declared schema, a declared capacity bound, a declared eviction policy, and a declared persistence location. Software owns it; models propose changes to it.

**Context window**: The token sequence accepted by one model call. It is a transport, not a store. Its capacity is address space; it holds whatever was serialized into it for that call and retains nothing afterward.

**Decision view**: The serialized projection of the working state rendered into the context window for one model call. A decision view is derived output, regenerated every turn from the canonical object, and never the authority for any field.

**Protected atom**: A state element that must survive every eviction, compaction, and truncation without loss: the goal, the success criteria, the standing and safety constraints, the current plan step, the latest value of every open variable, the unresolved error state, the outstanding approvals, and the side-effect ledger.

**Open variable**: A named quantity the task must resolve, carrying identity, declared type, current value or an explicit unknown marker, provenance, observation time, expiry, confidence, and supersession lineage.

**Provenance**: The verifiable path from a state value back to the event that produced it: the tool call identifier, the request and result hashes, the source identity, and the extraction that derived the field.

**Freshness**: The declared interval during which an observation may be treated as current, expressed as an observation timestamp and an expiry timestamp. A value used past its expiry is a staleness event, not a judgement call.

**Supersession**: The replacement of one variable version by a newer authoritative version of the same variable. The superseded value leaves the decision view immediately and survives only as lineage outside it.

**Contradiction**: Two authoritative current sources disagreeing about the same variable. A contradiction is not a supersession and must remain visible in the decision view as an unresolved conflict.

**Admission gate**: The deterministic pipeline every candidate item passes before entering the working state: protocol and size validation, trust and sensitivity classification, sanitization, injection scanning, field extraction, schema validation, and provenance binding.

**Reducer**: The deterministic function that applies a proposed update to one state field, defining merge semantics, conflict behaviour, and null handling. Every writable field has exactly one reducer.

**Capacity bound**: The declared maximum size of the active projection, expressed jointly as an item count per field class and a token budget for serialization. A bound stated only in prose is not a bound.

**Eviction**: The removal of an item from the active projection under a declared priority order, with the item either externalized to a referenced artifact or discarded outright.

**Compaction**: The lossy reduction of the active projection under measured capacity pressure, performed from the canonical state object and its source references rather than from the transcript, and validated against a preservation manifest before use.

**Promotion**: The governed write of a working-memory item into an episodic or semantic long-term store. Promotion is a separate workflow with its own admission criteria, not a side effect of task completion.

**Checkpoint**: A durable, versioned snapshot of the working state written at a semantic boundary, sufficient to resume the task without reconstructing anything from hidden reasoning.

**Side-effect ledger**: The record of every external effect the task has proposed, committed, or left ambiguous, keyed by an idempotency key that the effect's own boundary also honours.

**Action fingerprint**: A stable hash over the normalized action name, arguments, and target, used to detect exact repetition and oscillation across a rolling window.

**No-progress iteration**: An iteration that changed no protected atom: no variable verified, no artifact completed, no question resolved, no criterion satisfied, no uncertainty reduced, and no impossibility confirmed. Additional generated prose is not progress.

**Handoff record**: The bounded state package transferred between agents or across a context boundary, carrying the state version, the schema version, and the exact next decision, and requiring explicit acknowledgement by the receiver.

**Long-term memory**: The durable stores holding episodes, semantic facts, procedures, and user preferences across tasks. Working memory may reference them and hold a task-local interpretation of them, but never mutates their canonical records.

### 1.2 The Two Boundaries

Two boundaries govern this task family, and conflating either one produces agents that lose state at every context edge or that silently pollute durable stores with scratch material. Both boundaries are structural, not stylistic, and both are enforced by the tier partition in Section 1.3.

**The context window boundary**: The context window is a transport. Working memory is a maintained object with a schema, an eviction policy, and a persistence location, serialized into that transport on each turn. The window holds a projection for the duration of one call; the object persists across calls, across compactions, and across process restarts. Presence in the window is not storage, and absence from the window is not loss: a checkpoint, an artifact manifest, or an environment record may be working state while never appearing in a prompt, and a transcript may carry superseded values, completed subplans, and irrelevant text that are not working state at all. Agents that treat the window as the store rebuild state from whatever text survived the last truncation, and therefore lose the goal, the constraints, or an unresolved error precisely when the task is longest.

**Why window capacity does not substitute for state**: Reported evaluations find that information positioned near the beginning or end of a long input is used more reliably than information in the middle [7], that measured degradation grows with input length within advertised limits rather than at them [8][9], and that retrieval of a current value degrades as superseded values for the same key accumulate in the input, a pattern that resists prompt-level mitigation [10]. These findings do not cover every workload, and none of them licenses a claim that a model possesses working memory. They do refute the inference that content fitting inside the window is therefore reliably used, which is the inference an agent makes whenever it treats the window as its store.

**The long-term memory boundary and the promotion rule**: The default terminal action for working memory is discard, not persist. An item leaves working memory for an episodic or semantic store only where all five of the following hold: the item is independently useful outside the current task; it carries a complete provenance path to an admissible source event; it is verified, meaning a deterministic check or an adjudicated review confirmed it rather than the model asserting it; it has been classified for tenant scope, sensitivity, and retention; and the receiving store's own write policy admits it. Promotion is proposed at task close and at explicitly declared milestones, never inferred from task success. A successful task does not justify storing its scratchpad, and a checkpoint retained for possible debugging is not a promotion.

**Direction of authority across the boundaries**: Standing instructions, safety constraints, and user authority enter working memory from trusted configuration and are reasserted from that source on every turn. Tool output, retrieved documents, and long-term memory records enter as data through the admission gate and never as instructions. Recency confers no authority: a freshly retrieved page cannot supersede a standing constraint, and a newly written long-term record cannot amend the task contract.

**Cognitive science as motivation, not configuration**: The functional separation among control state, modality-specific artifacts, and an integrated task view is a useful design frame [1], as is the observation that competing commitments, not raw size, determine whether the next decision degrades [2][6]. The specific chunk counts reported in that literature are contested, depend on task, knowledge, rehearsal, and the definition of a chunk, and were never limits on software [3][4]. Agents must not configure a fixed number of goals, tools, or notes from those figures. Dozens of typed fields are safe where few bear on the next transition, and four verbose prose blocks may not be. The engineering translation of expert retrieval structures is a bounded index pointing at externalized evidence, not a copy of every artifact in the prompt [5].

### 1.3 The Execution Tier Partition

Working memory is a hybrid capability, and most of its production failures are misassignments of work across three execution tiers. The deterministic tier owns the state object, because identity, budgets, freshness arithmetic, effect reconciliation, and eviction require exactness and reproducibility that inference cannot supply. The model tier reads the serialized decision view and proposes updates, because interpreting an open-vocabulary observation and deciding what it means for the task requires judgement no rule covers. The hybrid tier is the handoff between them: the model proposes, software validates and commits, and software holds authority wherever the two disagree.

**Tier ownership by artifact**:

| Artifact | Owning tier | Authority where the tiers disagree |
| :-- | :-- | :-- |
| Working state schema, field types, and version | Deterministic | Deterministic; a proposed field outside the schema is rejected, not added |
| Reducers, merge semantics, and commit order | Deterministic | Deterministic; an update failing its reducer is never partially applied |
| Identity, tenant scope, and authority fields | Deterministic | Deterministic; tenant identity is never accepted from model output |
| Budget counters, token counts, and elapsed time | Deterministic | Deterministic; a model estimate of remaining budget is advisory only |
| Freshness expiry, staleness detection, and supersession | Deterministic | Deterministic; a model claim that a value is current is not evidence |
| Action fingerprints, cycle detection, and the circuit breaker | Deterministic | Deterministic; the breaker opens regardless of model objection |
| Side-effect ledger and idempotency keys | Deterministic | Deterministic; keys derive from canonical arguments, never from a per-attempt generation |
| Checkpoint write, integrity check, and schema migration | Deterministic | Deterministic; a checkpoint failing integrity is never resumed from |
| Meaning of an observation for the task | Model | Model proposes; the commit still requires provenance and schema validation |
| Interpretation of ambiguity and hypothesis formation | Model | Model; recorded as an assumption, never as an observed value |
| Plan revision content and subgoal decomposition | Model | Model proposes; software enforces step identity, dependencies, and status transitions |
| Extraction of required fields from untrusted text | Hybrid | Model extracts; schema validation and injection scanning decide admission |
| Compaction of the active projection | Hybrid | Model compresses; the preservation manifest validator decides use or rollback |
| Contradiction adjudication between sources | Hybrid | Model adjudicates; software refuses resolution while both sources remain authoritative |
| Promotion candidate selection | Hybrid | Model nominates; the durable store's write policy and verification decide |

**What the deterministic tier rejects unconditionally**: an update to a field absent from the schema; an observed value carrying no provenance path; a tenant, actor, or authority field sourced from model output; a plan step marked complete without a completion evidence identifier; a retry of an effect whose status is ambiguous; a compaction output missing a protected atom; a resume from a checkpoint whose schema version has no registered migration; and a promotion of an item lacking a verification result.

**What the model tier may never decide alone**: whether a budget permits another iteration; whether a value is still fresh; whether an effect already committed; whether the loop is progressing; whether an item enters long-term memory; and whether an instruction found inside tool output carries authority. Each of these has a deterministic answer available at runtime, and delegating it to inference converts a checkable fact into an opinion.

### 1.4 Capacity, Eviction, and Staleness Defaults

The values below are deployment defaults chosen to be operable before any measurement exists, not measured constants. Section V records this limitation, and Step 7.2 obliges each deployment to recompute them against observed trajectories. Every threshold names a consequence of breach, and a threshold with no consequence is a defect.

**Working memory operating defaults**:

| Control | Default threshold | Consequence of breach |
| :-- | :-- | :-- |
| Protected atom share of the model input limit | No more than 15 percent | Externalize evidence and narrow scope; above 25 percent the turn fails closed rather than truncating |
| Output headroom reserved before serialization | Declared maximum output tokens plus 10 percent | Serialization is rejected and the decision view is rebuilt smaller |
| Open variables in the active projection | No more than 30 | Evict by the Step 4.1 priority order until the count is met |
| Admitted evidence records in the active projection | No more than 12 | Evict the oldest records whose supported variables are already resolved |
| Compaction trigger | Active set at or above 70 percent of the declared token budget | Compaction runs; below this figure compaction is prohibited |
| Compactions per task | No more than 3 | The fourth attempt halts the task for scope review rather than compressing again |
| Environment observation expiry | 15 minutes | Refresh before use; a read past expiry is recorded as a staleness event |
| Reference and configuration data expiry | 24 hours | Refresh before use; a read past expiry is recorded as a staleness event |
| Priced, quoted, or authorization-bearing values | Expire on first use, and always before an irreversible effect | Re-observe before the effect; a stale authorization blocks the effect |
| Staleness usage rate at release | Below 1 percent of variable reads | A higher rate blocks promotion of the configuration |
| Consecutive no-progress iterations | 2 trigger a replan; 3 open the circuit breaker | The breaker halts the loop before the global step limit is reached |
| Action fingerprint comparison window | Rolling window of the last 5 actions | A repeat inside the window prohibits identical retry |
| Oscillation detection | A two-state cycle observed twice | The breaker opens and the run escalates |
| Retry cap by error class | 3 for transient transport, 1 for application rejection, 0 for an ambiguous effect | An ambiguous effect is reconciled before any retry, never retried on a timer |
| Checkpoint interval | Every irreversible effect boundary and every 10 iterations | A missed boundary checkpoint blocks the effect from committing |
| Duplicate irreversible effects in the resume suite | Exactly 0 | Any occurrence blocks release of the configuration |

***

## II. Operational Framework: A Bounded and Recoverable Working State Across One Task Episode

The framework produces one governed working state object per task, together with the machinery that keeps it correct: a schema carrying a capacity bound, an admission gate, a turn-level maintenance loop, an eviction and promotion policy, a token-budgeted serializer, a recovery path, and an event record sufficient to evaluate all of it. Phases 1 and 2 establish the object and its boundary. Phases 3 through 5 repeat once per iteration. Phase 6 binds at every semantic boundary and at every failure. Phase 7 runs alongside the loop and completes before any configuration is released.

### Phase 1: Working State Declaration and Capacity Bounding

**Objective**: Commit a versioned schema, a numeric capacity bound, and a field ownership map before any task effort is spent, so that state correctness is enforced by validation rather than by drafting discipline.

**Owning tier**: Deterministic throughout; the model tier contributes nothing to this phase except a proposed field list that software accepts or rejects against the task contract.

#### Step 1.1: Declare the Working State Schema and Its Field Classes

**Required Actions**:

- Declare one canonical working state object per task, carrying a schema version, and refuse any state read or write that does not name that version.
- Populate the task contract class with the goal text, a goal hash, the success criteria, the output contract, the standing constraints, the safety constraints, the authority scope, and the termination conditions, and preserve every one of them losslessly.
- Populate the control class with the task, thread, and run identifiers, the iteration index, the phase, the status, the plan version, the current step identifier, the subgoal stack, the pending approvals, and the timestamp of last progress.
- Populate the uncertainty class with open questions, open variables, hypotheses, assumptions, and contradictions, giving every variable identity, type, value or an explicit unknown marker, provenance, observation time, expiry, confidence method, and supersession lineage.
- Populate the evidence, failure, resource, and governance classes, holding raw artifacts by reference and recording per effect an idempotency key, a compensation status, and whether human review is required.
- Enumerate the exclusions explicitly: durable user facts, cross-task preferences, reusable knowledge, historical episodes, source corpora, embeddings, procedures, complete tool catalogues, the transcript, every prior result, completed subplans, and unrestricted reasoning content.

**Working State Schema Template**:

```
STATE_SCHEMA_VERSION:
TASK_CONTRACT:      goal_text, goal_hash, success_criteria, output_contract,
                    standing_constraints, safety_constraints, authority_scope,
                    termination_conditions
CONTROL:            task_id, thread_id, run_id, iteration_index, phase, status,
                    plan_version, current_step_id, subgoal_stack,
                    pending_approvals, last_progress_at
UNCERTAINTY:        open_questions, open_variables[], hypotheses, assumptions,
                    contradictions[]
OPEN_VARIABLE:      variable_id, name, declared_type, value | UNKNOWN,
                    provenance_event_ids, observed_at, fresh_until, confidence,
                    confidence_method, supersedes_version_id, conflicts_with[]
EVIDENCE:           tool_call_id, request_hash, result_hash, source_id,
                    trust_class, sensitivity_class, observed_at, fresh_until,
                    sanitizer_version, extraction_version, supported_variable_ids,
                    raw_artifact_reference
FAILURE:            error_class, error_fingerprint, failed_step_id,
                    attempt_count, retryable, next_retry_at, backoff_policy,
                    prior_remedies, compensation_status, human_review_required
RESOURCE:           max_and_consumed for steps, input_tokens, output_tokens,
                    tool_calls, retries, wall_time_ms, cost, side_effects;
                    soft_warning_threshold, hard_stop_threshold
GOVERNANCE:         sensitivity_labels, allowed_tools, prohibited_effects,
                    confirmation_requirements, retention_class,
                    checkpoint_eligibility
EXCLUDED:           durable_facts, cross_task_preferences, corpora, embeddings,
                    transcript, completed_subplans, reasoning_content
```

**Required Outputs**:

- One versioned working state schema covering all seven field classes.
- An explicit exclusion list naming every category held outside the object.
- A per-field type declaration with null semantics stated for every optional field.

**Quality Checkpoints**:

- Every field carries a declared type and a null semantic; an untyped field blocks schema registration.
- The task contract fields are marked lossless and are excluded from every eviction and compaction rule.
- The exclusion list is non-empty and names at least the transcript, the durable stores, and reasoning content.
- No field in the schema duplicates a canonical record held in a long-term store; duplication is replaced by a reference plus a task-local interpretation.

***

#### Step 1.2: Bound Capacity and Fix the Protected Atom Set

**Required Actions**:

- Express the capacity bound jointly as a per-class item count and a serialization token budget, since either bound alone permits the other to grow without limit.
- Fix the protected atom set to the goal, the success criteria, the standing and safety constraints, the current plan step, the latest value of every open variable, the unresolved error state, the outstanding approvals, and the side-effect ledger.
- Measure the protected atom set in tokens using the target model's own tokenizer, and treat a character estimate as unmeasured.
- Set the compaction trigger, the eviction trigger, and the fail-closed threshold as separate figures, so that pressure produces graduated responses rather than a single cliff.
- Record the bound in the state object itself, so a resumed task inherits the bound rather than recomputing it from a prompt.

**Required Outputs**:

- A capacity bound record stating item counts per field class and a token budget for the decision view.
- A protected atom manifest listing each atom, its field path, and its measured token size.
- Three declared thresholds covering eviction, compaction, and fail-closed behaviour.

**Quality Checkpoints**:

- Protected atoms occupy no more than 15 percent of the model input limit; above 25 percent the task is re-scoped rather than compacted.
- Every capacity figure was produced by the target tokenizer rather than estimated from character counts.
- The bound is stored in the state object and is recoverable after a restart without consulting a prompt.
- Each of the three thresholds names a distinct action; identical actions for two thresholds indicate the graduation is absent.

***

#### Step 1.3: Assign Ownership, Reducers, and Write Authority

**Required Actions**:

- Assign exactly one owner to every writable field, naming the component permitted to write it and the reducer that applies the update.
- Define merge semantics per reducer, covering the concurrent-write case explicitly, since an additive default silently duplicates entries when a retry replays an update.
- Prohibit last-write-wins for goals, constraints, approvals, side effects, and contradictory evidence, and require a version check or an explicit conflict object for those fields.
- Declare which fields the model tier may propose values for and which it may never propose, following the partition in Section 1.3.
- Register a validation function per field that rejects an update lacking a required provenance path, a required evidence identifier, or a valid enumeration member.

**Required Outputs**:

- A field ownership map naming one writer and one reducer per writable field.
- A reducer specification covering merge semantics, concurrency behaviour, and null handling.
- A model-proposable field list and a prohibited field list, disjoint and jointly covering the schema.

**Quality Checkpoints**:

- Every writable field has exactly one owner; a field with two owners blocks schema registration.
- No reducer for a goal, constraint, approval, effect, or contradiction resolves by last-write-wins.
- Every reducer defines behaviour for a replayed identical update, so a retry does not duplicate an entry.
- The proposable and prohibited lists partition the schema with no field appearing in both and none omitted from both.

***

### Phase 2: Admission Control at the State Boundary

**Objective**: Ensure that nothing enters the working state without passing a deterministic gate that binds provenance, freshness, and trust, so that no downstream decision rests on a value whose origin cannot be resolved.

**Owning tier**: Hybrid; the model tier extracts required fields from open-vocabulary content and the deterministic tier decides admission, with the handoff occurring at schema validation, which the model tier cannot override.

#### Step 2.1: Route Every Candidate Item Through the Admission Pipeline

**Required Actions**:

- Treat every external result as untrusted data even where the tool itself is trusted, since transport attestation confers no authority on the text inside the result [26].
- Run the pipeline stages in fixed order and fail the item at the first stage it does not pass, recording the failing stage rather than a generic rejection.
- Decode and normalize the content, strip hidden markup, and scan for injection indicators before any extraction is attempted.
- Separate the reader from the actor for high-risk tasks: an unprivileged component reads untrusted content and emits a constrained structured proposal, and the privileged controller never reads the raw content directly.
- Truncate oversized content at a field or artifact boundary, never inside a structured record, a code block, a citation, or a numeric value.

**Admission Pipeline**:

```
CANDIDATE ITEM ARRIVES
  1. PROTOCOL CHECK      transport status, declared type, byte size within limit
  2. NORMALIZE           decode, canonicalize encoding, strip hidden markup
  3. CLASSIFY            trust_class, sensitivity_class, source identity
  4. INJECTION SCAN      indicator codes; instruction-bearing text marked DATA
  5. EXTRACT             required fields only, by declared extraction version
  6. SCHEMA VALIDATE     types, enumerations, ranges, required fields
  7. PROVENANCE BIND     tool_call_id, request_hash, result_hash, observed_at,
                         fresh_until, sanitizer_version, extraction_version
  8. COMPARE             against current value: NEW | SUPERSEDES | CONFLICTS |
                         DUPLICATE | STALE_ON_ARRIVAL
  9. ADMIT OR REJECT     admit within capacity bound, else evict first
FAIL AT ANY STAGE -> record stage, retain raw artifact by reference, do not admit
```

**Required Outputs**:

- An admission decision per candidate item naming the terminating stage.
- A quarantine set holding rejected content by reference with its failing stage recorded.
- An extracted field set carrying only the fields the pending decisions require.

**Quality Checkpoints**:

- No item entered the state without a recorded admission decision; an unrecorded entry is a boundary breach.
- Every rejection names the stage that failed rather than a generic failure code.
- Instruction-bearing text found in tool output is marked as data and never reaches the control channel.
- No truncation split a structured record, a code block, a citation, or a numeric value.

***

#### Step 2.2: Bind Provenance, Freshness, and Trust to Every Admitted Item

**Required Actions**:

- Attach to every admitted value the tool call identifier, the request and result hashes, the source identity, and the extraction version that produced it, so the value resolves back to an event.
- Set an observation time and an expiry on every observation, drawing the default expiry from the class table in Section 1.4 and overriding it only with a stated reason.
- Record trust class and sensitivity class separately, since a highly trusted source may still carry sensitive content and a low-trust source may carry none.
- Record the confidence method alongside any confidence figure, since a figure without a method cannot be compared across sources or recalibrated.
- Replace credentials, session tokens, keys, and unnecessary personal data with scoped handles at the moment of admission rather than at display time.

**Required Outputs**:

- A provenance record per admitted value resolving to a source event.
- A freshness record per observation carrying observation time, expiry, and the class that set the default.
- A sensitivity classification per item with secrets already replaced by handles.

**Quality Checkpoints**:

- Every observed value resolves to an admissible provenance path; a value without one is rejected rather than admitted with a warning.
- Every observation carries an expiry; an observation without one is treated as expired on arrival.
- No raw credential, session token, private key, or unnecessary personal identifier is present in any state field, artifact name, or log line.
- Confidence figures appear only alongside the method that produced them.

***

#### Step 2.3: Commit Through Reducers and Resolve Supersession or Conflict

**Required Actions**:

- Apply every admitted update through the field's registered reducer, and never write a field directly from a model response.
- Classify the relationship of the new value to the current value as new, superseding, conflicting, duplicate, or stale on arrival, and act on the classification rather than on arrival order.
- Remove a superseded value from the active projection immediately on supersession, retaining its lineage pointer outside the decision view.
- Materialize a contradiction as an explicit conflict object where two authoritative current sources disagree, and refuse to resolve it by preferring the more recent arrival.
- Reject the commit and record the rejection reason where validation fails, leaving the prior state version intact rather than partially applied.

**Required Outputs**:

- A committed state version with an incremented version number and a recorded predecessor.
- A supersession lineage record per replaced variable version.
- A conflict object per unresolved contradiction, visible in the decision view.

**Quality Checkpoints**:

- Exactly one current value exists per open variable in the active projection; a second concurrent value is a supersession defect.
- Every superseded value is absent from the decision view and present in lineage; presence in both is a defect.
- No contradiction was resolved by recency alone; unresolved conflicts remain visible.
- A failed validation left the prior state version unchanged; a partially applied update blocks the iteration.

***

### Phase 3: Turn-Level Maintenance and Progress Control

**Objective**: Refresh the working state at the start of every iteration and establish, before any action is chosen, that the loop is still advancing toward the declared goal.

**Owning tier**: Deterministic for reload, version checking, freshness arithmetic, budget accounting, and cycle detection; the model tier is invoked only after these guards pass, and its objection to a guard result carries no authority.

#### Step 3.1: Reload and Version-Check the State at Iteration Start

**Required Actions**:

- Reload the canonical state version at the start of every iteration rather than carrying a copy forward from the previous turn, since a carried copy diverges silently after any concurrent write.
- Confirm the lease or compare-and-set token before any write, and abandon the iteration where a fencing token is stale, even where the holder believes its lease valid.
- Restate the goal hash from trusted state and compare it with the hash the previous decision used, treating any difference as goal drift rather than as paraphrase.
- Recompute remaining budget across steps, input and output tokens, tool calls, retries, wall-clock time, and cost, and halt before the model call where any hard limit is exhausted.
- Apply both a step limit and a wall-clock limit, since a stalled tool consumes time without consuming steps.

**Required Outputs**:

- A loaded state version with a confirmed version identifier and a valid concurrency token.
- A goal retention verdict comparing the expected and observed goal hashes.
- A budget ledger snapshot naming remaining capacity in every bounded dimension.

**Quality Checkpoints**:

- The iteration operated on a freshly loaded canonical version; operating on a carried copy is a staleness defect.
- The goal hash used by the decision equals the trusted goal hash; a model paraphrase resembling the goal does not satisfy this check.
- Every bounded dimension carries a numeric remaining figure; an unbounded dimension halts the run.
- The run halted before the model call where any hard budget was exhausted, rather than after it.

***

#### Step 3.2: Refresh Expired Observations and Reassert Canonical Constraints

**Required Actions**:

- Compare every observation's expiry against the current time and mark expired entries before they reach the decision view, refreshing those the pending decision requires.
- Re-observe any priced, quoted, or authorization-bearing value before an irreversible effect regardless of its nominal expiry.
- Reassert standing constraints and safety constraints from trusted configuration on every iteration, and never carry forward the model's paraphrase of them from a prior turn.
- Drop completed steps, rejected hypotheses, expired results, duplicate instructions, and verbose success logs from the active projection, since competing content degrades the next decision even where token capacity remains [6][10].
- Record every read of a value past its expiry as a staleness event, including reads the task subsequently justified.

**Required Outputs**:

- A refresh record naming expired variables, refreshed variables, and variables left expired with a stated reason.
- A reasserted constraint set sourced from trusted configuration rather than from prior model output.
- A staleness event log covering every read past expiry.

**Quality Checkpoints**:

- No value past its expiry entered the decision view without either a refresh or a recorded staleness event.
- Every constraint in the decision view traces to trusted configuration; a constraint traceable only to a prior model turn is replaced.
- Completed steps and rejected hypotheses are absent from the active projection.
- The staleness usage rate remains below 1 percent of variable reads; a higher rate blocks release of the configuration.

***

#### Step 3.3: Detect Absent Progress, Repetition, and Oscillation

**Required Actions**:

- Define the expected progress signal before acting, requiring a change to task state: a verified variable, a completed artifact, a resolved question, a satisfied criterion, a reduced uncertainty, or a confirmed impossibility.
- Compute a state hash after each iteration and reset the consecutive no-progress counter only where a protected atom changed; otherwise increment it and record the action fingerprint.
- Compare the current fingerprint against a rolling window of the last 5 actions to detect exact repetition, and compare state hash sequences to detect two-state oscillation and repeated error classes.
- Open the circuit breaker on 3 consecutive no-progress iterations, on a two-state cycle observed twice, on an excessive compaction or replan count, or on repeated identical error fingerprints, rather than waiting for the global step limit.
- Separate legitimate repeated polling, where an observation or timestamp changes, from useless repetition, where neither the action nor the resulting state changes.

**Required Outputs**:

- A progress verdict per iteration naming the signal type and whether the change was material.
- A fingerprint sequence covering actions, states, and error classes across the detection window.
- A breaker decision record naming the detector, the window, and the triggering pattern.

**Quality Checkpoints**:

- Generated prose alone never counts as progress; an iteration producing only text increments the no-progress counter.
- The breaker opened before the global step limit in every detected cycle; opening at the limit is a detector failure.
- Repeated polling with changing observations is not classified as a loop.
- Every breaker decision names its detector and window, so precision and recall are computable against labelled trajectories.

***

### Phase 4: Eviction, Compaction, and Governed Promotion

**Objective**: Keep the active projection inside its capacity bound by removing material under a declared priority order, and move only verified, independently useful items into durable stores through a separate write.

**Owning tier**: Deterministic for the eviction order, the preservation manifest, and the promotion admission check; hybrid for compaction itself, where the model tier compresses and the manifest validator holds authority over whether the result is used or rolled back.

#### Step 4.1: Evict Under a Declared Priority Order

**Required Actions**:

- Evict in the declared order below and never by recency alone, since the newest item is frequently the least load-bearing.
- Externalize any evicted item that remains recoverable, storing a content hash and a manifest entry in typed state and the artifact itself in a task-scoped location.
- Discard outright only material that is reproducible from a retained reference or that carries no bearing on any pending decision.
- Refuse to evict any protected atom, and escalate to scope reduction where the capacity bound cannot be met without touching one.
- Delete expired artifacts on schedule rather than retaining them against possible future need, and keep secrets out of artifact names and manifest entries.

**Eviction Priority Order**:

| Order | Class evicted | Treatment |
| :-- | :-- | :-- |
| 1 | Verbose success logs and duplicate instructions | Discard; reproducible from the event record |
| 2 | Completed plan steps and their intermediate outputs | Externalize by reference; retain step identity and completion evidence identifier |
| 3 | Rejected hypotheses and abandoned branches | Externalize by reference; retain the rejection reason only |
| 4 | Expired observations whose variables are resolved | Discard the value; retain provenance and lineage |
| 5 | Superseded variable versions | Discard from the projection; retain lineage outside the decision view |
| 6 | Admitted evidence supporting only closed decisions | Externalize by reference; retain the supported variable link |
| 7 | Raw artifacts exceeding the per-item size limit | Externalize with a content hash and manifest entry |
| 8 | Prose interpretation notes | Rewrite to a bounded summary rather than appending |
| Never | Protected atoms | Not evictable; a bound unmeetable without them forces scope reduction |

**Required Outputs**:

- An eviction record naming each removed item, its class, its order position, and its treatment.
- An artifact manifest with a content hash per externalized item.
- A capacity verdict confirming the active projection is inside its item and token bounds.

**Quality Checkpoints**:

- No protected atom appears in any eviction record.
- Every externalized item resolves through its manifest entry; an unresolvable reference is treated as data loss.
- The active projection satisfies both the item count bound and the token budget after eviction.
- No artifact name, manifest entry, or eviction log line contains a secret or an unnecessary personal identifier.

***

#### Step 4.2: Compact From Canonical State Against a Preservation Manifest

**Required Actions**:

- Trigger compaction only where the active set reaches the declared pressure threshold and completed history materially crowds current decisions, and never to obtain a caching discount.
- Compact from the canonical state object and its source references rather than from the transcript, since a transcript-derived summary inherits every distortion already present in the transcript.
- Build a preservation manifest before compacting, listing the goal, the constraints, the unresolved questions, the current plan, the latest value per open variable, the unresolved errors, the approvals, and the side-effect ledger as lossless atoms.
- Validate the compacted state against the manifest before use, comparing decision-relevant answers taken before and after compaction, and roll back to the pre-compaction version on any protected atom loss.
- Refuse to summarize a summary, and refuse summarization as a control for secrets, which are redacted or omitted instead.

**Required Outputs**:

- A preservation manifest identifying every protected atom by field path.
- A compaction validation record comparing pre- and post-compaction answers to decision-relevant questions.
- Either a committed compacted state version or a recorded rollback to the prior version.

**Quality Checkpoints**:

- Every protected atom in the manifest is present and unaltered after compaction; any loss triggers rollback rather than a warning.
- Governance content held as standing instructions, memory entries, or tool output is preserved at the same rate as content held in system configuration, since compaction erases the former far more readily than the latter [24].
- The compacted state derives from canonical state and source references, not from the transcript alone.
- Compaction count for the task does not exceed 3; a fourth trigger halts the task for scope review.

***

#### Step 4.3: Promote to Long-Term Memory Through a Separate Governed Write

**Required Actions**:

- Default the end-of-task action to discard, and treat every promotion as an exception requiring an affirmative case.
- Nominate a promotion candidate only where the item is independently useful outside this task, carries a complete provenance path, and is verified by a deterministic check or an adjudicated review rather than by model assertion.
- Classify every candidate for user and tenant scope, sensitivity, and retention class before the receiving store is consulted.
- Submit the candidate to the durable store's own write policy, and treat that policy rather than the working-memory layer as the authority on admission.
- Record the promotion attempt, its outcome, and the discard of the remainder, so that the boundary between scratch state and durable record is auditable.

**Required Outputs**:

- A promotion candidate set with provenance, verification result, scope, sensitivity, and retention class per entry.
- A promotion decision record per candidate naming the deciding policy and its verdict.
- A discard record covering all working state and artifacts not promoted.

**Quality Checkpoints**:

- No item was promoted on the strength of task success alone; success is not a verification result.
- Every promoted item carries a verification result produced outside the model that proposed it.
- Every promoted item carries a scope, sensitivity, and retention classification; an unclassified item is refused.
- Working state and artifacts not promoted are discarded under the retention policy rather than retained for possible debugging.

***

### Phase 5: Serialization Into the Context Window

**Objective**: Render the working state into a decision view that fits a declared token budget, places load-bearing content where it is reliably used, and fails closed rather than truncating a protected atom.

**Owning tier**: Deterministic; software allocates the budget, renders the view, and runs the preflight check, and the model tier receives the result as input without any authority over what was included.

#### Step 5.1: Allocate the Input Token Budget Across Reserved Regions

**Required Actions**:

- Allocate the input budget before each model call by region, reserving non-negotiable space before any discretionary content is considered.
- Count tokens with the target model's own tokenizer and enforce a hard preflight limit, treating a character-based estimate as unmeasured.
- Reserve output headroom equal to the declared maximum output tokens plus 10 percent, and reject the serialization where the remaining input space cannot hold the reserved regions.
- Keep content verbatim where exact wording, numbers, code, legal language, user authorization, or tool protocol matters, and use a referenced extract where only named fields matter.
- Hold a stable prefix stable where the provider rewards it, but never retain a stale value in the view for the sake of a cache hit.

**Decision View Budget Allocation**:

| Region | Allocation | Rule on overflow |
| :-- | :-- | :-- |
| System and safety instructions | Reserved, non-negotiable | Overflow halts the turn; never trimmed |
| Goal, success criteria, output contract | Reserved, non-negotiable | Overflow halts the turn; never summarized |
| Standing constraints and authority scope | Reserved, non-negotiable | Overflow halts the turn; reasserted verbatim each turn |
| Current plan step and subgoal stack | Reserved | Trim the stack depth, never the current step |
| Latest value per open variable | Reserved | Evict resolved variables before trimming any unresolved one |
| Unresolved errors and outstanding approvals | Reserved | Overflow halts the turn; error state is never dropped |
| Required tool schemas | Reserved | Restrict the tool allowlist rather than truncating a schema |
| Recent admitted evidence | Discretionary | Evict by Step 4.1 order until the budget is met |
| Prose interpretation notes | Discretionary, evicted first | Rewrite to a bounded summary or omit |
| Output headroom | Declared maximum output plus 10 percent | Rebuild the view smaller; never borrow from headroom |

**Required Outputs**:

- A per-region token allocation measured with the target tokenizer.
- A serialization verdict of proceed or rebuild, with the overflowing region named where applicable.
- A verbatim-retention list naming every element rendered without compression.

**Quality Checkpoints**:

- Every allocation figure was produced by the target tokenizer rather than estimated.
- Output headroom was never consumed by input content.
- Exact wording, numbers, code, legal text, and authorization language appear verbatim; none was summarized.
- No stale value was retained in the view to preserve a stable prefix.

***

#### Step 5.2: Render the Decision View With Position and Isolation Discipline

**Required Actions**:

- Place the goal, standing constraints, and current step in stable, prominent positions, and place the evidence supporting a decision adjacent to that decision, since content in the middle of a long input is used less reliably than content at either end [7].
- Render untrusted content inside an explicit data region that carries its source, trust class, and observation time, and never interleave it with the instruction region.
- Render each open variable as a single current value, with superseded versions absent and contradictions rendered as explicit conflict entries.
- Regenerate the entire view from canonical state every turn rather than appending to the previous turn's view, so that the view cannot accumulate content the state no longer holds.
- Keep the view free of reasoning content, complete tool catalogues, the transcript, and completed subplans.

**Decision View Layout**:

```
[REGION 1 - TRUSTED INSTRUCTION]     system rules, safety constraints
[REGION 2 - TASK CONTRACT]           goal, success criteria, output contract,
                                     standing constraints, authority scope
[REGION 3 - CONTROL]                 current plan step, subgoal stack,
                                     iteration index, remaining budgets
[REGION 4 - STATE]                   open variables (one current value each),
                                     conflicts, open questions,
                                     unresolved errors, pending approvals
[REGION 5 - DATA / UNTRUSTED]        admitted evidence, each entry tagged with
                                     source, trust_class, observed_at,
                                     fresh_until; instructions here are DATA
[REGION 6 - TOOLS]                   allowed tool schemas only
[REGION 7 - TASK CONTRACT RESTATED]  goal and current step repeated at the tail
[OUTPUT HEADROOM]                    reserved, never occupied by input
```

**Required Outputs**:

- A rendered decision view partitioned into labelled regions.
- A position record naming where the goal, constraints, and current step were placed.
- A data region in which every untrusted entry carries source, trust class, and freshness.

**Quality Checkpoints**:

- The goal and current step appear at both a leading and a trailing position, not once in the middle of a growing view.
- Untrusted content appears only inside the labelled data region and is never rendered as an instruction.
- Exactly one current value per open variable appears; superseded values are absent.
- The view was regenerated from canonical state rather than appended to the previous view.

***

#### Step 5.3: Run the Preflight Preservation Check and Fail Closed

**Required Actions**:

- Verify before dispatch that every protected atom is present in the rendered view, and refuse the call rather than truncating one.
- Where protected atoms do not fit, apply the graduated remedies in order: externalize evidence, retrieve a narrower slice, reduce scope, then terminate partially with verified results.
- Confirm the rendered goal hash matches the trusted goal hash, so a drifted or paraphrased goal never reaches the model.
- Confirm the constraint set in the view is complete against the trusted constraint list, counting constraints rather than inspecting prose.
- Record the preflight verdict with the measured token totals per region, so failures are diagnosable after the fact.

**Required Outputs**:

- A preflight verdict of dispatch or fail-closed with the missing atom named where applicable.
- A protected atom presence count compared against the manifest count.
- A remedy record naming which graduated remedy was applied where the check failed.

**Quality Checkpoints**:

- The call was dispatched only where 100 percent of protected atoms were present; a missing atom fails the call rather than degrading it.
- The rendered goal hash equals the trusted goal hash.
- The constraint count in the view equals the trusted constraint count.
- Every fail-closed event names the applied remedy rather than resolving by retrying the same serialization.

***

### Phase 6: Durability, Recovery, and Handoff

**Objective**: Persist enough state at semantic boundaries that the task resumes on another process or another agent without repeating a consequential effect or reconstructing anything from reasoning content.

**Owning tier**: Deterministic; checkpoint writes, integrity checks, schema migration, effect reconciliation, and handoff acknowledgement are all software operations, and no model output determines whether a resume is safe.

#### Step 6.1: Checkpoint at Semantic Boundaries

**Required Actions**:

- Use a process-local state object only for short, read-only, low-cost work that can be safely restarted, and require durable checkpointing wherever the task outlives one request, calls paid or rate-limited tools, waits for a human, modifies an external system, needs handoff, or holds expensive intermediate work.
- Checkpoint after plan commitment, before and after every irreversible effect, after admitting a material result, before a human wait, after compaction, and at the declared iteration interval.
- Write the minimum checkpoint contents in full, and never rely on reconstructing any field from hidden reasoning.
- Key every checkpoint by tenant, thread, and checkpoint version, encrypt sensitive fields, and set an expiry at write time rather than deferring retention to a later cleanup.
- Record the artifact manifest hash and the side-effect ledger hash inside the checkpoint, so integrity covers referenced state and not only inline fields.

**Checkpoint Record Template**:

```
CHECKPOINT_ID:
CHECKPOINT_SEQUENCE:
CHECKPOINT_REASON:      PLAN_COMMIT | PRE_EFFECT | POST_EFFECT |
                        MATERIAL_RESULT | PRE_HUMAN_WAIT | POST_COMPACTION |
                        INTERVAL
STATE_SCHEMA_VERSION:
STATE_VERSION:
STATE_HASH:
TASK_CONTRACT:          goal, success criteria, constraints, authority scope
PLAN:                   plan_version, step_ids, statuses, dependencies
OPEN_VARIABLES:         value, provenance, observed_at, fresh_until per variable
UNRESOLVED_ERRORS:      error_class, fingerprint, attempt_count, remedy history
BUDGETS:                limits and consumed per dimension
APPROVALS:              outstanding and granted
SIDE_EFFECT_LEDGER_HASH:
ARTIFACT_MANIFEST_HASH:
POLICY_VERSION:
NEXT_ALLOWED_TRANSITION:
TENANT_KEY:
ENCRYPTION_KEY_ID:
EXPIRES_AT:
REASONING_CONTENT:      PROHIBITED
```

**Required Outputs**:

- A durable checkpoint per semantic boundary, keyed by tenant, thread, and version.
- An artifact manifest and side-effect ledger with hashes recorded in the checkpoint.
- A retention record naming the expiry set at write time.

**Quality Checkpoints**:

- Every irreversible effect is bracketed by a checkpoint before and after; a missing pre-effect checkpoint blocks the effect.
- No checkpoint field contains reasoning content or a raw secret.
- Every checkpoint carries a schema version and a policy version, so a later resume can detect an incompatible runtime.
- Every checkpoint carries an expiry; an unexpiring checkpoint is a retention defect.

***

#### Step 6.2: Resume Only After Reconciliation

**Required Actions**:

- Load the checkpoint, verify its integrity against the recorded hashes, validate its schema and policy versions, and apply a registered migration where versions differ rather than resuming across an unmigrated gap.
- Authenticate the tenant and the resuming actor before any state is read into a decision view, and refuse a resume whose authority scope no longer holds.
- Reconcile every in-flight effect by querying the effect's own boundary with the recorded idempotency key or operation identifier, and never retry an ambiguous effect on a timer.
- Refresh expired observations and recheck outstanding approvals before selecting the next action, since the external environment need not match the snapshot.
- Treat successful deserialization as insufficient evidence of safety, and evaluate a resume readiness verdict against the reconciliation results [20].

**Required Outputs**:

- A resume record naming integrity, authentication, authorization, and migration results.
- An effect reconciliation result per in-flight effect drawn from the effect's own boundary.
- A refreshed variable set with the expired entries that were re-observed named.

**Quality Checkpoints**:

- No action was selected before every in-flight effect carried a reconciled status.
- Duplicate irreversible effects across the resume test suite number exactly 0; any occurrence blocks release.
- Every resume validated schema and policy versions; a version gap without a registered migration halts the resume.
- Expired observations were refreshed before the first post-resume decision rather than after it.

***

#### Step 6.3: Transfer State Under an Acknowledged Handoff Contract

**Required Actions**:

- Default to isolated working memory per agent and task, and share only a minimal coordination object carrying the common goal, the decomposition, assignment identifiers, dependency state, artifact references, and handoff summaries.
- Withhold every agent's private notes and reasoning content from the shared object, since exposing them increases distraction, leakage, and correlated error.
- Partition ownership so one agent owns one subgoal or variable namespace while a coordinator owns the global plan and the terminal decision, and require a reducer, a version check, or an explicit conflict object wherever two writers can reach one field.
- Include in every handoff the goal and success criteria, standing constraints, current plan and step, verified outputs, open variables with freshness, evidence references, errors and attempted remedies, effects already committed, remaining budgets, required approvals, and the exact next decision.
- Require the receiver to acknowledge the state version and schema version and to reject an incompatible schema or an authority scope it does not hold.

**Required Outputs**:

- A handoff record carrying all eleven required content classes and both version identifiers.
- A receiver acknowledgement naming the accepted state version and the authority verdict.
- An ownership map showing one writer per shared field for the duration of the handoff.

**Quality Checkpoints**:

- No handoff omitted a required content class; an omission is recorded as handoff loss rather than silently accepted.
- The receiver acknowledged the state version before acting; an unacknowledged handoff blocks the receiver's first action.
- No shared field is writable by two agents without a reducer or a version check.
- Handoff loss is measured by replaying the receiver's first decisions against a full-state reference rather than assumed to be zero.

***

### Phase 7: Instrumentation and Evaluation

**Objective**: Emit an event record from which every working memory property can be recomputed, and establish through interruption, interference, and adversarial trials that the state machinery holds under conditions the clean path never exercises.

**Owning tier**: Deterministic for event emission, metric computation, replay, and fault injection; the model tier appears only as the system under test, and its self-report is never an input to a metric.

#### Step 7.1: Emit the Working State Event Record

**Required Actions**:

- Emit append-only typed events alongside a versioned current projection, so that both the state at a point in time and the path that produced it are reconstructable.
- Attach identity, lineage, version, and handling fields to every event, including tenant, task, thread, run, trace, actor, model and runtime versions, state schema version, and the state versions before and after.
- Record the domain fields per event class named in the inventory below, so that goal retention, staleness, supersession, loop detection, compaction loss, and resume correctness are computable rather than inferred.
- Store hashes and redacted previews in place of raw values, redact before writing rather than at display, and follow open telemetry conventions for shared attributes while retaining state-specific fields the conventions do not define [29][30].
- Exclude reasoning content from every event, and treat its presence as a disclosure breach that halts release of the log.

**Event Field Inventory**:

| Event class | Required domain fields |
| :-- | :-- |
| Iteration | Iteration index, phase and status before and after, expected and observed goal hash, goal retained verdict, constraint count and satisfied count, current step, working set tokens, protected atom tokens, evidence tokens, state hash before and after, progress signal type, meaningful progress verdict, consecutive no-progress count, action fingerprint, cycle period detected, guard result, latency |
| Variable write | Variable identifier, declared type, operation, value hash before and after, redacted preview, source event identifiers, observed time, expiry, freshness status at write, confidence and method, superseded version, conflicting versions, writer, reducer, validation result, rejection reason |
| Tool admission | Tool call identifier, request hash, idempotency key hash, side-effect class, timeout, attempt index, response status, raw artifact reference and hash, source identity, trust and sensitivity classes, sanitizer and extraction versions, injection scan result and indicator codes, schema validation result, admission decision, admitted fields and tokens, truncation applied, rejection reason |
| Compaction and truncation | Trigger reason, method, input and output tokens, source artifact references, preservation manifest identifier, protected atom count and preserved count, per-class preservation verdicts, numeric exact match rate, entity retention rate, validator version, validation result, loss-detected fields, rollback state version, boundary type for raw truncation |
| Budget and loop | Limits and consumed values per dimension, soft and hard limit crossings, projected completion cost, detector identifier and version, window size, state hash sequence, action and error fingerprint sequences, no-progress threshold, loop type, breaker action |
| Checkpoint and resume | Checkpoint identifier and sequence, reason, state version and hash, artifact manifest hash, side-effect ledger hash, storage backend, encryption key identifier, expiry, write result, resume identifier, authentication and authorization results, integrity results, migration identifiers, expired and refreshed variables, in-flight effect identifiers, effect reconciliation results, first action expected and observed, state equivalence result |
| Termination and discard | Termination type, reason code, success criteria total and verified, verified output references, unresolved variables and errors, effects committed and reconciled, steps to completion, tokens, cost, latency, discard reason, retention policy, deletion result, derivative identifiers checked, promotion candidate identifier |

**Required Outputs**:

- An append-only event log covering all seven event classes with complete identity fields.
- A versioned current-state projection reconstructable from the log.
- A redaction record naming which fields were replaced by hashes or previews.

**Quality Checkpoints**:

- Every event carries its identity, lineage, and version fields; a missing parent identifier makes trajectory reconstruction impossible and fails the checkpoint.
- No event contains reasoning content, a raw secret, or an unnecessary personal identifier.
- A sampled trajectory is reconstructable end to end from events alone, without consulting a transcript.
- Constraint adherence is recorded per constraint identifier with a pass, fail, not-applicable, or unknown verdict, so rates use eligible decisions as the denominator.

***

#### Step 7.2: Compute the State Quality Metric Set

**Required Actions**:

- Compute goal retention as iterations using the correct trusted goal hash divided by eligible iterations, and never from a similarity judgement over paraphrases.
- Compute state correctness as latest-value accuracy, staleness usage rate, unsupported-variable rate, contradiction visibility, error-state retention, and plan-staleness detection rate.
- Compute loop metrics as no-progress rate over all iterations, loop rate over tasks with a detected cycle, and breaker precision and recall against labelled trajectories.
- Compute recovery metrics as resume correctness, duplicate-effect rate, lost-effect rate, state-equivalence rate, time to resume, and refresh correctness.
- Compute economics as tokens and cost per successful task rather than per call, since a smaller decision view that increases retries raises total cost, and slice every metric by horizon length, view size, compaction count, handoff count, and model version.

**Required Outputs**:

- A state-correctness metric block covering all six correctness measures.
- A control metric block covering goal retention, no-progress rate, loop rate, and breaker precision and recall.
- A recovery metric block covering resume correctness and effect duplication.
- An economics block reporting cost and tokens per successful task with slices.

**Quality Checkpoints**:

- Task success is never reported without at least 1 state-correctness metric and 1 economics metric alongside it.
- Goal retention derives from hash comparison rather than from a similarity score.
- Every metric is sliced rather than pooled; a single pooled figure fails the checkpoint.
- Every default threshold in Section 1.4 has been recomputed against observed trajectories before the configuration is promoted.

***

#### Step 7.3: Run Interruption, Interference, and Adversarial Trials

**Required Actions**:

- Interrupt execution before and after every transition class, restart on a different worker, and compare final state and external effects against an uninterrupted reference run, requiring exactly-once business outcomes even where execution is at least once.
- Test compaction in the loop rather than by summary similarity: freeze a pre-compaction state, ask decision-relevant questions before and after, continue the trajectory, and compare actions, constraint adherence, and final outcome, including cumulative loss across repeated compactions [25].
- Run position and length trials with the goal, the constraints, and the evidence placed at the beginning, middle, and end across increasing view sizes, and pair retrieval probes with contradictory updates, multi-source evidence, nested plans, tool failures, and stale values [32].
- Inject adversarial instructions through every tool path, including document content, filenames, page text, message bodies, code comments, and retrieved notes, and measure injection detection, unauthorized state writes, unauthorized tool calls, secret exposure, and task success under attack [33].
- Run ablations against no explicit state, transcript-only state, prose scratchpad, typed state, compaction disabled, durable checkpoints disabled, and the loop breaker disabled, and adopt a mechanism only where it improves a predeclared objective.

**Required Outputs**:

- An interruption matrix covering every transition class with reference-run comparisons.
- A compaction trajectory report covering answer preservation and downstream success retention.
- A position and length report across the tested view sizes.
- An adversarial report and an ablation table with per-mechanism verdicts.

**Quality Checkpoints**:

- Unauthorized state writes and unauthorized effects in the adversarial suite number exactly 0; any occurrence blocks release.
- Duplicate irreversible effects in the interruption suite number exactly 0.
- Compaction was evaluated by downstream trajectory outcome, not by summary similarity alone.
- Every retained mechanism improved a predeclared quality, safety, recovery, or cost objective in ablation; a mechanism improving none is removed.

***

## III. Implementation Guidance for AI Agents

AI agents maintaining working memory must follow systematic protocols ensuring that state is owned by software, admitted under a gate, bounded by measurement, and recoverable without reconstruction. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **State Custodian**: Owns the working state object, its schema version, its reducers, and its commit order. It is the only writer, and it rejects any update failing validation rather than applying it partially.
2. **Admission Agent**: Runs the deterministic admission pipeline over every candidate item, covering protocol checks, normalization, trust and sensitivity classification, injection scanning, schema validation, and provenance binding. It never interprets content.
3. **Untrusted Reader**: Reads raw external content and emits a constrained structured proposal. It holds no tool authority, no write authority, and no visibility of credentials, so instructions embedded in the content it reads cannot reach the control channel.
4. **Executor**: Selects and performs one action per iteration under authority, budget, and side-effect checks. It may not change the schema, extend a budget, or admit an unvalidated result.
5. **Budget and Loop Guard**: Counts tokens with the target tokenizer, tracks steps, cost, and wall-clock time, computes action and state fingerprints, and opens the circuit breaker. Its verdicts are final.
6. **Serializer**: Allocates the input budget, renders the decision view, and runs the preflight preservation check. It fails the turn closed rather than truncating a protected atom.
7. **Recovery Agent**: Writes checkpoints, verifies integrity and schema versions, reconciles in-flight effects on resume, and validates handoff acknowledgements before a receiver acts.

**State Authority Boundary**: The model tier proposes and the deterministic tier commits. This is a hard constraint applying to every component.

- Accept model output only as a proposal expressed against the declared schema, and discard any proposed field the schema does not carry.
- Never accept a tenant, actor, authority, budget, freshness, or effect-status value from model output, since each has a deterministic source available at runtime.
- Never treat a model assertion that a step is complete, a value is current, or an effect succeeded as evidence; require a completion evidence identifier, an expiry comparison, or a reconciliation result.
- Record decisions, evidence references, and observable transitions rather than reasoning content, and treat reasoning content found in state or logs as a disclosure breach.

**Workflow Execution Pattern**:

```
STATE: Iteration_State_Refresh
INPUTS:
  1. Canonical state version and concurrency token
  2. Trusted task contract and constraint list
  3. Budget ledger and fingerprint history
ACTIONS:
  1. Reload canonical state and confirm the fencing token
  2. Compare trusted goal hash against the hash used last decision
  3. Expire and refresh observations past fresh_until
  4. Recompute remaining budget across all bounded dimensions
  5. Evict to the capacity bound, then serialize the decision view
VALIDATION:
  - state_version_loaded == canonical_version
  - goal_hash_observed == goal_hash_expected
  - protected_atoms_present == protected_atom_manifest_count
  - stale_reads_without_event == 0
  - output_headroom_reserved == TRUE
  - reasoning_content_persisted == FALSE
TRANSITIONS:
  IF all_validations_pass THEN next_state = Action_Selection
  IF protected_atoms_present < manifest_count THEN next_state = Fail_Closed_Remedy
  IF hard_budget_exhausted THEN next_state = Terminate_Partial
  IF no_progress_count >= 3 OR cycle_detected THEN next_state = Breaker_Open
  ELSE next_state = State_Error_Handling
```

**Two-Phase Action Pattern**: Emit the proposed state update and the intended action without committing either; validate both against the schema, the provenance requirement, the authority scope, and the side-effect ledger while nothing is committed; commit only after validation passes, writing the state transition and the effect record in the same operation.

**Approval Gate**: Human authorization is required before committing any effect whose reconciliation status is ambiguous, before any irreversible effect resting on a value past its expiry, before promoting any item in the highest sensitivity class into a durable store, before relaxing the protected atom set, and before any single iteration projected to consume more than 25 percent of the remaining budget. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the task contract, plan, budgets, and effect ledger in durable state, since the task may outlive many context windows.
- Regenerate the decision view from canonical state every turn rather than appending to the previous view.
- Write a handoff record at every context boundary naming state version, schema version, remaining budgets, open variables, unresolved errors, and the exact next decision.
- Count the state machinery's own token consumption toward overhead rather than treating serialization as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Schema and Bound Integrity (After Phase 1)**

- **Automated Check**: Every field carries a type, a null semantic, one owner, and one reducer; the protected atom manifest is measured with the target tokenizer; the exclusion list is non-empty.
- **Agent Action on Pass**: Register the schema version and open the task.
- **Agent Action on Failure**: Halt before any task effort; an unregistered schema admits nothing.
- **Human Review Trigger**: Protected atoms exceeding 25 percent of the model input limit, which forces scope reduction rather than compaction.

**Checkpoint 2: Admission Integrity (After Phase 2)**

- **Automated Check**: Every admitted value carries a provenance path, an expiry, a trust class, and a sensitivity class; every rejection names its failing stage; no secret appears in any state field.
- **Agent Action on Pass**: Proceed to the iteration loop.
- **Agent Action on Failure**: Quarantine the affected items by reference and re-run admission for those items only.
- **Human Review Trigger**: More than 5 percent of candidate items failing the injection scan in one task.

**Checkpoint 3: Iteration Guard Integrity (After Phase 3)**

- **Automated Check**: Goal hash matches; all bounded dimensions carry remaining figures; staleness events recorded for every read past expiry; fingerprint window populated.
- **Agent Action on Pass**: Proceed to eviction and serialization.
- **Agent Action on Failure**: Halt the iteration and re-run the refresh; a failed guard is never bypassed for one turn.
- **Human Review Trigger**: A goal hash mismatch, or a staleness usage rate above 1 percent of reads.

**Checkpoint 4: Capacity and Preservation Integrity (After Phase 4)**

- **Automated Check**: No protected atom appears in an eviction record; every externalized item resolves through its manifest; compaction validation passed or rolled back; compaction count is at most 3.
- **Agent Action on Pass**: Proceed to serialization.
- **Agent Action on Failure**: Roll back to the pre-compaction state version and apply the graduated remedies in order.
- **Human Review Trigger**: A second compaction rollback in one task, or any protected atom loss detected after commit.

**Checkpoint 5: Serialization Integrity (After Phase 5)**

- **Automated Check**: 100 percent of protected atoms present in the rendered view; output headroom reserved; exactly one current value per open variable; untrusted content confined to the data region.
- **Agent Action on Pass**: Dispatch the model call.
- **Agent Action on Failure**: Fail the call closed and apply the named remedy; never dispatch a degraded view.
- **Human Review Trigger**: Two consecutive fail-closed events on the same task.

**Checkpoint 6: Recovery Integrity (After Phase 6)**

- **Automated Check**: Every irreversible effect bracketed by checkpoints; every in-flight effect reconciled before action selection; schema and policy versions validated; no reasoning content or raw secret in any checkpoint.
- **Agent Action on Pass**: Permit the resume or the handoff to proceed.
- **Agent Action on Failure**: Block the resume and report the unreconciled effects by identifier.
- **Human Review Trigger**: Any ambiguous irreversible effect, or any resume across a schema version lacking a registered migration.

**Checkpoint 7: Evaluation Integrity (After Phase 7)**

- **Automated Check**: All 7 event classes present with complete identity fields; duplicate irreversible effects at 0; unauthorized state writes at 0; every Section 1.4 default recomputed against observed trajectories.
- **Agent Action on Pass**: Release the metric report and permit promotion of the configuration.
- **Agent Action on Failure**: Withhold the report and name the missing evidence; no configuration is promoted on clean-path results alone.
- **Human Review Trigger**: Any disclosure breach, any non-zero duplicate effect, or any unauthorized state write.

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

**Error Type 1: State Loss at a Context or Process Boundary**

- **Symptoms**: The goal, a constraint, an unresolved error, or an approval is absent after a compaction, a truncation, a handoff, or a restart; the agent restates the task in altered terms; a previously closed subtask is reopened.
- **Diagnostic Steps**: Compare the current state hash against the last checkpoint hash, compare the protected atom count against the manifest count, and determine whether the loss originated in eviction, compaction, truncation, or a handoff omission.
- **Resolution Protocol**: Option A, restore from the last checkpoint preceding the loss and replay admitted results through the same reducers. Option B, reassert the task contract and constraints from trusted configuration and rebuild the view. Option C, where the loss is in a handoff, return the state to the sender and re-issue the handoff with the missing content classes. Option D, where no checkpoint precedes the loss, terminate partially with the verified results held.
- **Escalation Trigger**: A second state loss on the same task escalates regardless of remaining budget; loss of a safety constraint escalates immediately and is never resolved by continuing.

**Error Type 2: Stale or Superseded Value Treated as Current**

- **Symptoms**: A decision cites a quote, permission, search result, or environment observation past its expiry; two versions of one variable are visible; an effect is proposed against a value that has since changed.
- **Diagnostic Steps**: Resolve the cited value to its variable version, compare its observation time and expiry against the decision time, and check whether the supersession lineage shows a newer version that failed to leave the projection.
- **Resolution Protocol**: Option A, re-observe the value and re-run the decision. Option B, remove the superseded version from the projection and repair the reducer that failed to evict it. Option C, where two authoritative sources genuinely disagree, materialize a conflict object and block the dependent decision until it is adjudicated.
- **Escalation Trigger**: A stale value underlying an irreversible or authorization-bearing action escalates immediately; this class is never resolved by instructing the model to prefer recent values.

**Error Type 3: Unsupported or Injected State Commit**

- **Symptoms**: A decisive variable resolves to no source event; a committed value contradicts the tool result it cites; the agent follows an instruction that originated inside retrieved content; a tool call targets a destination outside the task's authority scope.
- **Diagnostic Steps**: Trace every decisive claim to an admissible provenance path, replay the admission record for the item, and check whether the injection scan and schema validation ran at the declared versions.
- **Resolution Protocol**: Option A, reject the commit, quarantine the source item by reference, and re-run admission with the current sanitizer and extraction versions. Option B, route the source through an unprivileged reader that emits only a constrained structured proposal, keeping the privileged controller away from the raw content. Option C, restrict the tool allowlist and destination set for the remainder of the task. Option D, where the proposed action does not match the original task intent, block the action and escalate with the intent comparison attached.
- **Escalation Trigger**: Any unauthorized state write or unauthorized effect escalates immediately and halts the task; additional sampling never resolves this class.

**Error Type 4: Protected Atom Loss Under Compaction or Truncation**

- **Symptoms**: A post-compaction view answers decision-relevant questions differently from the pre-compaction view; a constraint carried as a standing instruction or a memory entry disappears while system-level rules survive; a numeric value loses precision.
- **Diagnostic Steps**: Compare the post-compaction state against the preservation manifest field by field, and segment preservation rates by the channel the content occupied, since governance content held outside system configuration is lost at markedly higher rates [24].
- **Resolution Protocol**: Option A, roll back to the pre-compaction state version and pin the lost class outside the compaction path entirely. Option B, externalize evidence and retrieve a narrower slice so compaction is unnecessary. Option C, reduce declared scope so the protected set fits the bound. Option D, terminate partially with the verified results rather than compacting a fourth time.
- **Escalation Trigger**: A second rollback on one task escalates; loss of a safety constraint or an approval blocks release of the configuration and is never resolved by retrying compaction.

**Error Type 5: Non-Terminating Loop and Reflection Thrash**

- **Symptoms**: Identical action fingerprints recur inside the rolling window; the state hash alternates between two values; the same error fingerprint repeats; reflection restates the same explanation without producing a new action.
- **Diagnostic Steps**: Classify the pattern as exact repetition, two-state oscillation, repeated error class, or semantically equivalent retry, and separate it from legitimate polling in which an observation or timestamp genuinely changes.
- **Resolution Protocol**: Option A, prohibit identical retry and require a different action or a different evidence source. Option B, replan the affected branch only, preserving the goal and constraints and recording why the prior route became stale. Option C, cap reflection to a declared step budget and treat a reflection producing no state change as consumed budget. Option D, open the circuit breaker and terminate partially with the verified results.
- **Escalation Trigger**: 3 consecutive no-progress iterations, or a two-state cycle observed twice, opens the breaker and escalates; the global step limit is never the primary termination mechanism [14][15].

**Error Type 6: Duplicate or Ambiguous Irreversible Effect**

- **Symptoms**: An effect appears twice in the downstream system after a restart; an effect's status is unknown after a timeout; a replanned attempt reissues a semantically equivalent call carrying a fresh identifier.
- **Diagnostic Steps**: Query the effect's own boundary using the recorded idempotency key or operation identifier, compare the side-effect ledger against the downstream record, and determine whether the key was derived from canonical arguments or generated per attempt.
- **Resolution Protocol**: Option A, reconcile against the effect boundary and record the true status before any further action. Option B, derive the idempotency key from canonicalized arguments and pass it through to the effect boundary so the downstream system deduplicates as well. Option C, apply the declared compensation for an effect that committed and should not have. Option D, where the effect cannot be reconciled or compensated, halt and escalate with the ledger attached.
- **Escalation Trigger**: Any unreconciled irreversible effect escalates immediately; retrying an ambiguous effect on a timer is prohibited without exception.

**Troubleshooting Decision Tree**:

```
WORKING STATE CHECK FAILS
├─ CONTENT LOSS
│   ├─ Protected atom missing from view → Fail closed; apply graduated remedy
│   ├─ Atom lost after compaction → Roll back; pin the class out of compaction
│   ├─ Atom lost after handoff → Return state; re-issue with missing classes
│   └─ No checkpoint precedes the loss → Terminate partially with verified results
├─ VALIDITY DEFECT
│   ├─ Value past expiry → Re-observe; block dependent irreversible action
│   ├─ Superseded version still visible → Evict it; repair the reducer
│   ├─ Two authoritative sources disagree → Materialize conflict; block decision
│   └─ Value has no provenance path → Reject commit; quarantine the source
├─ BOUNDARY DEFECT
│   ├─ Instruction found in tool output → Mark as data; re-run admission
│   ├─ Action outside authority scope → Block; ESCALATE with intent comparison
│   ├─ Tenant or authority field from model output → Reject; reload from trusted state
│   └─ Reasoning content in state or log → HALT release; purge and re-instrument
├─ PROGRESS DEFECT
│   ├─ Fingerprint repeats in window → Prohibit identical retry; change evidence
│   ├─ Two-state cycle seen twice → Open breaker; ESCALATE
│   ├─ Reflection changes no action → Charge to budget; replan or stop
│   └─ Hard budget exhausted → Terminate partially with verified results
└─ EFFECT DEFECT
    ├─ Effect status ambiguous → Reconcile at the effect boundary before acting
    ├─ Duplicate effect observed → Apply compensation; repair key derivation
    ├─ Pre-effect checkpoint missing → Block the effect; checkpoint first
    └─ Effect unreconcilable → HALT; ESCALATE with the side-effect ledger
```

### D. Performance Metrics and Continuous Learning

**State Correctness Metrics**:

- **Goal retention rate**: Iterations whose decision used the correct trusted goal hash, over eligible iterations (target: 100 percent; any shortfall is a defect rather than a degradation).
- **Latest-value accuracy**: Decisions citing the current version of a variable, over decisions citing that variable (target: at least 99 percent).
- **Staleness usage rate**: Reads of a value past its expiry, over all variable reads (target: below 1 percent; a higher rate blocks release).
- **Unsupported-variable rate**: Decisive variables lacking an admissible provenance path, over decisive variables (target: 0 percent).
- **Contradiction visibility**: Detected conflicts rendered in the decision view, over detected conflicts (target: 100 percent).
- **Error-state retention**: Unresolved errors surviving a compaction or handoff, over unresolved errors present before it (target: 100 percent).

**Control and Recovery Metrics**:

- **No-progress rate**: Iterations changing no protected atom, over all iterations (target: no more than 15 percent; above 30 percent indicates the progress signal is misdefined).
- **Loop rate**: Tasks with a detected cycle, over all tasks (target: no more than 2 percent).
- **Breaker precision and recall**: Breaker openings that were genuine loops, and genuine loops the breaker caught, against labelled trajectories (target: at least 90 percent recall at no worse than 80 percent precision).
- **Resume correctness**: Resumes whose final state and external effects match an uninterrupted reference run, over resumes tested (target: at least 99 percent).
- **Duplicate-effect rate**: Irreversible effects observed twice downstream, over irreversible effects (target: exactly 0).
- **Compaction answer preservation**: Decision-relevant questions answered identically before and after compaction, over questions asked (target: at least 95 percent, with cumulative loss reported across the maximum expected compaction count).
- **Handoff loss**: Receiver first decisions diverging from a full-state reference, over handoffs tested (target: no more than 5 percent).

**Economics Metrics**:

- **Cost per successful task**: Total tokens, tool calls, and monetary cost over accepted successes, reported rather than cost per call, since a smaller view that raises retries raises total cost.
- **State overhead share**: Tokens spent on serialization, compaction, and checkpointing over total task tokens (target: no more than 20 percent; above 35 percent triggers a bound review).
- **Recovery cost**: Time and tokens from interruption to first correct post-resume action (target: below the cost of restarting the task from zero).

**Size Sweep Discipline**: Run the same task set at multiple active-state budgets and record success, constraint adherence, latest-value accuracy, no-progress rate, tokens, tool calls, compactions, retries, cost, and latency at each. Select the smallest budget on the quality plateau, then re-test under longer horizons and adversarial interference before adopting it. Reopen the sweep whenever the model, prompt, tool mix, schema, or task distribution changes.

**Learning and Adaptation Mechanisms**:

- **Threshold recalibration**: Recompute every Section 1.4 default per task class against observed trajectories; the stated values are deployment defaults, not constants.
- **Reducer hardening**: Where one field repeatedly produces conflicts or duplicate entries, change its reducer rather than instructing the model to write it more carefully.
- **Schema evolution under migration**: Version every schema change and register a migration before deploying it, since checkpoints written under the prior version must remain resumable.
- **Ablation before adoption**: Add compaction, durable checkpointing, plan state, or a loop breaker only where an ablation shows it improves a predeclared objective for the workload at hand.

**Human-in-the-Loop Boundaries**: Relaxation of the protected atom set, promotion of an item in the highest sensitivity class, authorization of an irreversible effect resting on an expired or unreconciled value, and release of a configuration whose adversarial suite is incomplete are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the representation and lifecycle of task state rather than the content of any particular task. Its phases hold wherever an agent performs multiple dependent steps, admits observations from outside itself, and may be interrupted before the task completes.

### 4.1 Cross-Domain Application Patterns

**Software engineering and repository automation**: The working state carries the change objective, the acceptance tests, the files under edit, the failing test identifiers, and the build and lint results, while diffs and logs are externalized with content hashes. Freshness is short because the repository changes underneath the agent, so a file read more than one edit ago is re-observed before a dependent change. The side-effect ledger covers commits, branch operations, and any deployment trigger, and the pre-effect checkpoint binds before each. Compaction risk concentrates in the failing-test set, which is a protected atom because losing it converts a targeted repair into an undirected rewrite.

**Regulated clinical and safety-critical operations**: Constraints dominate the protected atom set, since the standing prohibitions and the authority scope are the reason the agent is permitted to act at all. Every observation carries a short expiry and a source identity, and no recommendation is emitted from a value whose provenance does not resolve to an authoritative record. The event log is a deliverable rather than a diagnostic aid, and the promotion rule is strict: nothing enters a durable store without an adjudicated verification and an explicit retention class.

**Financial transaction processing**: Reversibility varies within one task, since a quote is reversible while a transfer is not, so thresholds bind per action class rather than per task. Priced and authorization-bearing values expire on first use and are always re-observed before an effect. The idempotency key is derived from canonicalized arguments and passed through to the payment boundary, so a replanned or replayed attempt deduplicates downstream rather than relying on the agent's own memory of what it did.

**Field logistics and operations**: The environment supplies frequent external signals, so expiries are short and refresh is cheap, and the dominant risk is a stale observation rather than a lost constraint. Partial termination is a normal outcome: an adequate allocation delivered on time outranks a better allocation delivered late, so the framework's partial-completion path carries most of the operational value. Working state is partitioned by assignment so that concurrent workers own disjoint variable namespaces.

**Research synthesis and evidence work**: Open variables are claims awaiting sources, and contradiction visibility is the principal correctness property, since two authoritative sources disagreeing is a finding rather than a defect to be smoothed away. Evidence is externalized aggressively and referenced by hash, keeping the active projection to claim identity, current support status, and open questions. Long horizons make compaction likely, so the preservation manifest protects the claim set and the unresolved questions above all else.

### 4.2 Scale, Risk, and Recovery Adaptation

- **Short read-only tasks**: Use a process-local state object with a declared schema and a capacity bound, omit durable checkpointing, and retain the admission gate and the loop guard. State machinery overhead above 20 percent of task cost indicates the bound is set too tight for the workload.
- **Effectful tasks of any length**: Require durable checkpointing, a side-effect ledger, idempotency keys derived from canonical arguments, and reconciliation before every resume, regardless of how short the task appears, since a single irreversible effect makes restart unsafe.
- **Long-horizon autonomous runs**: Expect several context boundaries and at least one compaction, so budget the protected atom set conservatively, externalize evidence early, write handoff records at every boundary, and re-run the contract check after each so drift is detected rather than inherited [14].
- **Multi-agent deployments**: Partition variable namespaces by owner, share only the coordination object, prohibit last-write-wins on goals, approvals, effects, and contradictions, and require fencing tokens for exclusive effects so a worker holding a stale lease cannot commit.
- **High-sensitivity workloads**: Separate the untrusted reader from the privileged controller, replace secrets with scoped handles at admission, encrypt checkpoints, qualify every state key by tenant, and shorten retention so that scratch state and its derivatives expire on a schedule rather than on request.

***

## V. Limitations and Considerations

**The numeric thresholds here are deployment defaults, not measured constants**: Every figure in Section 1.4, and every target in Section III.D, was chosen to be operable on first deployment rather than derived from a measurement of the reader's workload. Presenting them as evidence would misrepresent them, and adopting them permanently would encode one deployment's guesses as another's requirements. The mitigation is Step 7.2, which obliges each deployment to recompute every default against observed trajectories before the configuration is promoted, and the size sweep in Section III.D, which locates the smallest budget on the quality plateau for the workload at hand.

**State machinery costs tokens, latency, and engineering effort**: Serialization, compaction, checkpointing, and event emission consume resources the task itself does not, and on short, reversible, single-step work the machinery costs more than it saves. The mitigation is the scale adaptation in Section 4.2, which permits a process-local object without durable checkpointing for short read-only work, together with the state overhead metric that triggers a bound review above 35 percent of task cost.

**Deterministic ownership does not make state correct**: Software can validate a schema, a provenance path, and an expiry without establishing that the value is true or that the extraction preserved its meaning. A well-formed state object can carry a confidently wrong number admitted from a correctly attested source. The mitigation is the separation of validation from verification in Step 4.3, which requires a deterministic check or an adjudicated review outside the proposing model before any item is promoted, and the unsupported-variable metric, which measures provenance rather than truth and is reported as such.

**Compaction loss cannot be fully prevented, only bounded and detected**: A lossy reduction performed without knowing what the task will need next will sometimes discard something that later matters, and preservation rates differ sharply by the channel content occupies, with governance content held as standing instructions, memory entries, or tool output lost far more readily than content held in system configuration [24]. The mitigation is the preservation manifest and the rollback rule in Step 4.2, the trajectory-grounded validation in Step 7.3 [25], and the hard cap of 3 compactions per task, above which the task is re-scoped rather than compressed again.

**Recovery guarantees stop at the effect boundary**: A durable state store can guarantee that the agent's own steps are replayed at most once, but the moment an effect reaches a third-party system that guarantee degrades to at-least-once delivery with retry until acknowledgement, and a replanned attempt may reissue a semantically equivalent call carrying a fresh identifier. The mitigation is deriving idempotency keys from canonicalized arguments and passing them through to the effect's own boundary, together with the reconciliation requirement in Step 6.2 and the prohibition on retrying an ambiguous effect [20].

**Cognitive science motivates the design but does not specify it**: The bounded-attention framing, the separation of control state from artifacts, and the emphasis on interference over raw size are useful design intuitions, but the chunk counts frequently quoted from that literature depend on task, knowledge, rehearsal, and the definition of a chunk, and were never claims about software [2][3][4]. The mitigation is Section 1.2, which admits the literature as motivation only, refuses its numbers as configuration values, and requires every capacity figure to be measured with the target tokenizer instead.

**Instrumentation rich enough to evaluate state is rich enough to leak it**: An event log carrying variable previews, source identities, artifact references, and effect destinations concentrates exactly the material an incident would expose. The mitigation is the admission-time replacement of secrets with scoped handles in Step 2.2, redaction before writing rather than at display, tenant-qualified keys, encryption of checkpoints, and the retention and deletion testing required in Step 4.3, which must cover checkpoints, artifact stores, trace backends, replay corpora, and backups.

**Evidence for long-context behaviour is workload-specific**: The reported degradation with input length and position, and the reported growth of superseded-value retrieval errors, were measured on particular tasks and model families and do not establish a general law [7][8][9][10]. The mitigation is Step 7.3, which requires each deployment to run its own position and length trials against its own realistic trajectories rather than inheriting a published curve, and to pair retrieval probes with contradictory updates and tool failures so that the result reflects the workload it will govern.

***

## VI. Conclusion and Summary

Working memory is a state-ownership discipline before it is a prompting technique. Its correctness comes from a small number of structural commitments: a declared schema that software owns, a gate that nothing enters without provenance and freshness, a bound that is measured rather than asserted, a serializer that fails closed rather than truncating what matters, and a recovery path that reconciles the world before it acts on it. An agent that holds those commitments keeps its goal across every context boundary; an agent that treats the window as its store rebuilds itself from whatever text survived the last truncation, and does so precisely when the task has run longest and the stakes are highest.

A team introducing working memory should build the smallest recoverable object first and add machinery only as the workload demands it. Declare the schema, the exclusions, and the protected atom set. Add token counting with the real tokenizer, hard budgets, and tool timeouts. Add action and state fingerprints with a no-progress threshold and a circuit breaker. Add durable checkpointing and a side-effect ledger the moment the task becomes effectful or resumable. Add compaction last, under measured pressure, behind a preservation manifest and a rollback. At every stage, discard by default and promote only what a separate governed write admits.

**Key Success Factors**:

- **Software owns the state**: The model proposes updates against a declared schema and the deterministic tier commits them, holding authority over identity, budgets, freshness, effects, and every other question with a checkable answer.
- **Nothing enters without provenance and freshness**: Every admitted value resolves to a source event and carries an expiry, so a decisive claim can always be traced and a stale one is detected rather than debated.
- **The bound is measured, not asserted**: Capacity is expressed as item counts and a token budget produced by the target tokenizer, with graduated eviction, compaction, and fail-closed thresholds that each name a distinct action.
- **Protected atoms are never traded**: The goal, constraints, current step, latest values, unresolved errors, approvals, and effect ledger survive every eviction, compaction, and truncation, and a turn that cannot carry them fails closed.
- **Progress is a state change, not more text**: An iteration that verifies nothing, resolves nothing, and completes nothing increments the no-progress counter, and the breaker opens well before the global step limit.
- **Discard is the default and promotion is a separate write**: Working memory expires at task close, and only verified, independently useful, classified items reach a durable store through that store's own admission policy.

By following this guide, AI agents can maintain a task state that survives context boundaries, tool failures, and process restarts, act on values whose currency is established rather than assumed, and close a task by discarding its scratch state rather than by quietly promoting it into memory that outlives the reason it existed.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. Two exceptions are noted in place: entries 23 and 24 were retrieved during this conversion rather than taken from the prose source, and the identity of entry 10 was confirmed independently during that research.

**Corpus pointers**:

- `Working Memory Patterns for AI Agents: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the working-state field classes, the representation choices, the capacity and interference policy, the control-loop discipline, the durability and replay treatment, the multi-agent and concurrency boundaries, the failure-mode taxonomy, the security and retention rules, the metadata field inventory, the evaluation and gating discipline, and the staged operational workflow. It carries inline citations to primary literature on working memory, long-context behaviour, plan and loop structure, state persistence, injection defence, and evaluation; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — companion guidance on the memory taxonomy and the relationship among memory classes, applicable to the exclusion list in Step 1.1 and the boundaries in Section 1.2.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — companion guidance on durable episode capture, applicable as the receiving store for the promotion rule in Step 4.3.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on consolidating task output into durable stores, applicable to the promotion admission criteria in Step 4.3.
- `advanced_task_guides/memory-management/guide_AttentionBasedMemoryRetrieval.md` — companion guidance on salience and admission into a bounded context, applicable to the interference control in Step 3.2 and the serialization discipline in Phase 5.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — owns the operation contract for a single durable read and write, including gate ordering, idempotency, and terminal states; applicable to the checkpoint writes in Step 6.1 and the separate governed write in Step 4.3.
- `advanced_task_guides/memory-management/guide_HierarchicalMemory.md` — owns tier declaration, promotion and demotion thresholds, and the prompt-budget precedence order across tiers; applicable to the region allocation in Step 5.1, where this guide fixes only the working state's own share.
- `advanced_task_guides/memory-management/guide_DistributedMemoryArchitecture.md` — owns the consistency contract and the session guarantees that make a read after another writer's commit predictable; applicable to the shared coordination object and the single-writer ownership rule in Step 6.3.
- `advanced_task_guides/memory-management/guide_GenerativeAgentMemory.md` — owns the durable, versioned plan artifact and the observation stream it is revised against. Transient status, current subgoal, and intermediate results remain working state under this guide and are not appended to that stream.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on control loops, checkpoint horizons, and budget ledgers, applicable to the progress control in Step 3.3.
- `advanced_task_guides/planning/guide_PlanTodoRecitation.md` — companion guidance on holding and restating plan state across a long run, applicable to the plan fields in Step 1.1 and the reassertion discipline in Step 3.2.
- `advanced_task_guides/planning/guide_PlanExecuteDecoupling.md` — companion guidance on separating plan revision from execution, applicable to the replan triggers in Phase 3.
- `advanced_task_guides/planning/guide_TaskManagementOrchestration.md` — companion guidance on multi-agent task assignment and coordination, applicable to the handoff contract in Step 6.3.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design and instrumentation, applicable to the event record in Step 7.1.
- `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guidance on monitoring under constraint, applicable to the guard and detector design in Step 3.3.
- `advanced_task_guides/design-architecture/guide_SchemaFlexibilityandEvolution.md` — companion guidance on schema versioning and migration, applicable to the checkpoint migration requirement in Step 6.2.
- `advanced_task_guides/policy-risk/guide_InformationDependencyDisclosureRiskAnalysis.md` — companion guidance on disclosure exposure, applicable to the sensitivity classification in Step 2.2 and the instrumentation limitation in Section V.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, III, IV, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Working memory in cognitive science, admitted as motivation rather than as specification*

1. Baddeley, *The episodic buffer* — https://pubmed.ncbi.nlm.nih.gov/11058819/
2. Cowan, *The magical number 4* — https://pubmed.ncbi.nlm.nih.gov/11515286/
3. Miller, *The Magical Number Seven* — https://labs.la.utexas.edu/gilden/files/2016/04/MagicNumberSeven-Miller1956.pdf
4. Cowan, *Cowan's retrospective* — https://pmc.ncbi.nlm.nih.gov/articles/PMC4486516/
5. Ericsson and Kintsch — https://pubmed.ncbi.nlm.nih.gov/7740089/
6. Oberauer, *Working Memory and Attention* — https://pmc.ncbi.nlm.nih.gov/articles/PMC6688548/

*Context length, position, and interference effects*

7. Liu and colleagues, *Lost in the Middle* — https://arxiv.org/abs/2307.03172
8. *Context Length Alone Hurts* — https://arxiv.org/html/2510.05381v1
9. Chroma, *Context Rot* — https://www.trychroma.com/research/context-rot
10. *PI-LLM* — https://arxiv.org/html/2506.08184v3

*Loop structure, plan state, and long-horizon behaviour*

11. *ReAct* — https://arxiv.org/abs/2210.03629
12. *Plan-and-Act* — https://arxiv.org/html/2503.09572v3
13. LangChain, *Deep Agents benchmark* — https://www.langchain.com/blog/how-we-benchmark-deep-agents
14. *HORIZON* — https://arxiv.org/html/2604.11978v1
15. *Uncovering Infinite Agentic Loops* — https://arxiv.org/html/2607.01641v1

*State persistence, recovery, and concurrency*

16. *LangGraph persistence* — https://docs.langchain.com/oss/python/langgraph/persistence
17. *LangGraph Graph API* — https://docs.langchain.com/oss/python/langgraph/graph-api
18. *LangGraph time travel* — https://docs.langchain.com/oss/python/langgraph/use-time-travel
19. *AgentRewind* — https://arxiv.org/abs/2608.14380
20. *Safe to Resume?* — https://arxiv.org/html/2608.29381v1
21. PostgreSQL, *explicit locking* — https://www.postgresql.org/docs/current/explicit-locking.html
22. Temporal, *retry policies* — https://docs.temporal.io/encyclopedia/retry-policies
23. Temporal, *activities* — https://docs.temporal.io/activity-definition

*Compaction integrity, security, and instrumentation*

24. *Governance Decay: How Context Compaction Silently Erases Safety Constraints in Long-Horizon LLM Agents* — https://arxiv.org/abs/2606.22528
25. *Slipstream: Trajectory-Grounded Compaction Validation for Long-Horizon Agents* — https://arxiv.org/abs/2605.08580
26. OWASP, *LLM Prompt Injection Prevention Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
27. OpenAI, *safety best practices* — https://platform.openai.com/docs/guides/safety-best-practices
28. OpenAI, *prompt caching* — https://openai.com/index/api-prompt-caching/
29. OpenTelemetry, *generative-AI semantic conventions* — https://opentelemetry.io/docs/specs/semconv/gen-ai/
30. OpenTelemetry, *agent observability* — https://opentelemetry.io/blog/2025/ai-agent-observability/

*Evaluation harnesses and benchmarks*

31. *AgentBoard* — https://arxiv.org/abs/2401.13178
32. *LongMemEval* — https://arxiv.org/abs/2410.10813
33. *InjecAgent* — https://arxiv.org/abs/2403.02691

