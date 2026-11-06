# Hierarchical Memory

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Hierarchical memory constitutes the task family of organising agent state and evidence across storage tiers that differ in capacity, latency, cost, and durability, and of moving records between those tiers under an explicit policy rather than by accident. This guide provides AI agents with a structured protocol for declaring four service tiers, assigning each a numeric capacity and latency bound, admitting records at a defensible initial placement, promoting and demoting them under separated thresholds, evicting derived copies only where a durable copy is proven to survive, detecting the thrashing that a mistuned hierarchy produces, and holding every tier coherent against one canonical version. It specifies the execution-tier partition that makes the method reliable: deterministic software owns capacity accounting, movement execution, durability verification, access counting, and thrash detection, while model inference owns only the relevance forecast that predicts near-term need. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that tiering demonstrably lowers cost or latency per successful task without losing, staling, or irrecoverably compacting the records it moves.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Hierarchical memory**: The governed placement of agent state and evidence across storage tiers with different capacity, latency, cost, durability, and retrieval properties, together with explicit policy-driven movement among those tiers. It answers five operational questions: what must remain resident, what may be fetched, what should be compacted, what can wait in an archive, and what must be deleted.

**Tier**: A storage layer defined by a service contract rather than by a product name. A tier declaration fixes capacity, maximum latency, durability class, consistency guarantee, eligibility rule, retention, and cost per unit stored. Two technologies belong to the same tier where their service contracts match, and one technology may serve two tiers where it is configured differently.

**Tier zero (resident core)**: The portion of the serialized model input that is present on nearly every call: controlling instructions, tool contracts, non-negotiable policy, the current request, a compact identity block, verified pinned facts, and pointers to active goals. Residency means presence in the serialized input, not permanent retention by the model.

**Tier one (active working set)**: Session-scoped or task-scoped state held in fast local storage and assembled into prompts on demand: conversation state, unresolved obligations, recent decisions, task-local facts, compact tool results, and the checkpoint needed to resume execution.

**Tier two (warm recall)**: Durable remote storage holding canonical records and their derived serving structures, reachable within the interactive latency budget. Warm means operationally available; it does not mean trusted or automatically eligible.

**Tier three (cold archive)**: Durable, high-latency storage holding retired transcripts, large artifacts, immutable source documents, retired checkpoints, and low-frequency evidence retained for audit, legal, replay, or rare recovery. Retrieval is an asynchronous job, not an interactive cache miss.

**Canonical record**: The single authoritative, immutably versioned representation of a memory, identified by a stable memory identifier and an immutable version identifier. Every tier copy is a derived representation carrying the canonical version it was built from.

**Derived copy**: Any representation built from a canonical record: a prompt fragment, a cache entry, a lexical document, an embedding, a summary node, a checkpoint, or an archive object. A derived copy is never independently edited.

**Placement**: The recorded fact that a specific memory version occupies a specific tier at a specific time, carrying capacity charge, residency timestamps, pin state, sensitivity class, retention class, and tombstone state.

**Admission**: The decision to accept a newly created or newly retrieved record into any tier at all, and the selection of its initial placement. Admission is separated from replacement so that a single access burst cannot displace established records.

**Promotion**: Movement of a record to a tier of lower latency or higher influence. Promotion changes availability; it never changes truth, authority, or authorisation.

**Demotion**: Movement of a record to a tier of higher latency or lower influence, preserving at least one durable copy.

**Eviction**: Removal of a derived copy from a tier without removing the canonical record. Eviction is legitimate only where a durable copy is proven to remain.

**Deletion**: Removal of a canonical record and every derivative under a tombstone. Deletion is a governed operation with an authorisation record; it is never a byproduct of capacity pressure.

**Hysteresis**: The deliberate gap between the score required to enter a tier and the score required to remain in it, together with a minimum residence time and a post-movement cooldown. Hysteresis exists to prevent oscillation.

**Thrashing**: The condition in which records repeatedly cross the same tier boundary in both directions inside the movement window, so that the system spends its budget on movement rather than on work.

**Relevance forecast**: A model-produced estimate that a record will be needed within a declared horizon. It is an input to a promotion score, never a placement decision on its own.

**Movement window**: The bounded interval over which movement counts, thrash rates, and promotion precision are computed. Every movement metric is meaningless without its stated window.

**Durability class**: The declared survival property of a tier, expressed as replica count, backup coverage, and recovery point objective. Durability class, not latency, determines whether a copy may be counted as the record's surviving copy.

**Promotion precision**: Completed promotions that were subsequently used within the declared horizon, divided by completed promotions.

**Demotion regret**: Completed demotions followed by a qualifying re-fetch or a demonstrated need inside the regret window, divided by completed demotions.

**Generation**: An immutable build of a derived structure such as a lexical index, a vector index, or a summary tree, published by moving a serving alias atomically from generation n to generation n plus one.

**Tombstone**: A committed marker making every version of a memory immediately ineligible for retrieval across all tiers, ahead of the physical removal that follows it.

### 1.2 The Tier Model and Its Agent-Layer Boundary

**The borrowed framing and where it stops**: Hierarchical memory is conventionally described by analogy to operating-system virtual memory, with the model context window standing in for resident pages and external storage standing in for backing store. The analogy is legitimate at the agent layer, because an agent genuinely controls what it loads into a prompt and what it leaves in a store, and one influential system adopted it explicitly as virtual context management rather than as an equivalence claim [1]. The analogy stops at the model boundary. A prompt is serialized evidence interpreted probabilistically, not byte-addressable memory: token position, instruction authority, and semantic interference all affect whether resident content is used, and models degrade measurably as input length grows and as relevant evidence moves away from the edges of the input [2].

**Agent-layer scope of this guide**: The executable policy here governs four things an agent can act on: what is serialized into the prompt, what is held in a fast session-local store, what is held in a warm remote store, and what is left in a cold archive. Page tables, fault handlers, attention matrices, hidden states, and key-value cache tensors sit outside that scope. Decoder key-value caching and its block-paging optimisations are serving-engine properties available to an operator of a self-hosted inference stack, not runtime levers for an agent, and they are named here only so they are not confused with tier policy. Provider prompt caching remains in scope, because prefix ordering and cache breakpoints are controllable through provider APIs and therefore constrain how tier zero is serialized.

**Prompt-cache serialization constraint**: Provider prompt caches reuse computation for identical prefixes and invalidate everything after the first changed byte, so stable policy and tool schemas must precede volatile core facts, working state, retrieved evidence, and user text in a deterministic order [3][4]. Cache lifetimes, minimum lengths, and write premiums vary by provider and change over time, so savings are computed from observed cache-read and cache-write token telemetry against a versioned price book rather than assumed. Prompt caching is an economic optimisation, never a durability guarantee, and a cache key is never shared across security scopes.

**Three distinct hit types**: A provider prompt-cache hit, a local cache hit, and a warm-tier retrieval hit have different keys, lifetimes, correctness properties, and security scopes. Reporting them under one hit-rate figure conceals which mechanism paid for the saving and which one crossed a scope boundary. Instrument the three separately.

**Cognitive type is independent of serving tier**: An episodic event, a semantic claim, a procedure, and a checkpoint may each occupy any tier over their life. Tier policy is a function of access cost, reuse, sensitivity, and durability requirement, not of what kind of memory a record is.

**Tier Service Contract Defaults**:

| Tier | Capacity bound | Latency bound | Durability class | Eligibility rule |
| :-- | :-- | :-- | :-- | :-- |
| Tier zero, resident core | No more than 25 percent of the model input limit and no more than 40 percent of the assembled prompt | 0 ms additional; already serialized | Not durable; rebuilt from tier one or two on every assembly | Verified, compact, broadly useful, safe to repeat |
| Tier one, active working set | Declared token and byte cap per session; default 2 times the tier zero token budget | p95 no more than 50 ms | At least 1 replica plus checkpoint; recovery point objective no more than 60 seconds | Task-scoped, unresolved, or needed to resume |
| Tier two, warm recall | Sized to the record count meeting the hit-rate target; index overhead counted separately | p95 no more than 300 ms; p99 no more than 800 ms | At least 2 replicas plus point-in-time recovery | Canonical, or reconstructable within the latency bound |
| Tier three, cold archive | Bounded by admitted bytes times retention times version count; forecast 12 months ahead | Restore no more than 12 hours; never on the interactive path | At least 2 replicas plus backup with tested restore | Retention, audit, legal, replay, or rare recovery |

**Budget precedence inside tier zero**: Reserve output and tool headroom first, then allocate the remainder in this fixed order: controlling instructions, current request and constraints, active core blocks, retrieved evidence, and scratch or recent history. Where the assembled package exceeds capacity, remove duplicate and re-fetchable material before summarising, and never silently truncate instructions, unresolved side effects, or the current request. The current request and controlling policy are protected; every other allocation is revocable.

### 1.3 The Execution-Tier Partition

Reliability in a memory hierarchy comes from putting the counting, the enforcement, and the movement in software, and confining model inference to the one judgement no rule covers. This partition binds every phase of Section II.

**Deterministic tier**: Software, queries, schema validators, and APIs own capacity accounting against every tier bound; access-frequency and recency counting; residency and cooldown timers; movement execution and its idempotency; durability verification before eviction; watermark enforcement; invalidation fan-out and generation cutover; tombstone propagation; thrash detection; and every metric denominator. These require exactness, reproducibility, and auditability that model inference cannot supply, and each is expressible as a counter, a comparison, or a transaction.

**Model tier**: LLM calls own the relevance forecast predicting whether a record will be needed inside the declared horizon; the classification of an incoming request into an access class; the generation of synopses and summary nodes during compaction; and the proposal of semantic duplicates for merging. These require open-vocabulary judgement over natural-language content that no deterministic rule covers.

**Hybrid tier**: Promotion is hybrid: the model forecast contributes one weighted component to a promotion score, and the placement accountant computes capacity, incumbent scores, and residency, then applies the threshold. Compaction is hybrid: the model writes the summary, and a deterministic answer-preservation gate over predeclared holdout questions accepts or rejects it. Model-directed paging is hybrid: the model may request a page-in, and an authorisation and budget check permits or refuses it.

**Authority when the tiers disagree**: The deterministic tier holds authority in every hybrid step. Three rules make this concrete and are never relaxed. A model forecast may raise a record's promotion score but never overrides a capacity bound, a residency minimum, a cooldown, a sensitivity constraint, or a pin policy. Eviction of the last durable copy of a record is never a model decision and never a capacity-pressure decision; it is reclassified as deletion and requires an authorisation record. A model-proposed edit to a resident core block is a proposed write subject to schema, provenance, conflict, poison, and capacity checks, exactly like any other write.

**Artifact ownership**: The deterministic tier owns the placement table, the capacity ledger, the movement log, the tombstone register, and the metric report. The model tier owns the forecast record, the query classification, and the draft summary. Where an artifact carries a model-produced field, that field is recorded with the model identifier, the prompt version, and the score it contributed, so a later audit separates a policy failure from a forecast failure.

### 1.4 The Entry Gate: When Tiering Is Warranted

Tiering is not free. Each added tier adds a copy to invalidate, a boundary to cross, and a failure mode to contain. Agents must run a gate, bounded to 2 percent of the direct-execution budget, returning tier, defer, or a named simpler design.

**Conditions favouring a hierarchy**: Open the hierarchy where the eligible corpus exceeds reliable prompt capacity; accesses are skewed enough that a working set exists, measured as the top 20 percent of records serving at least 60 percent of reads; warm and cold latency differ by a factor of 10 or more; reuse is high enough to amortise indexing or compaction across at least 5 future uses; or selective retention, erasure, or provenance is required by policy.

**Conditions favouring refusal**: Prefer a flat single-store design where the corpus fits one query path within the latency objective, where reuse is below 2 uses per record, or where added copies would create more synchronisation risk than the latency saving is worth. Prefer a long-context-only design where the bounded eligible corpus fits comfortably, exact order and wording matter, reuse is low, and position-perturbation tests pass. Neither substitutes for a hierarchy over indefinite histories, selective erasure across mixed principals, or workloads that repeatedly pay to send mostly irrelevant tokens.

**Numeric gate rules**: Adopt a hierarchy only where at least 2 tiers show materially different measured latency and at least 1 declared workload gate improves. Where projected movement and invalidation overhead exceeds 20 percent of the serving cost the flat baseline would incur, defer and record the estimate. Where no baseline measurement exists for the flat and long-context alternatives, the gate returns defer, because a hierarchy never compared to a simpler design cannot be shown to pay for itself.

***

## II. Operational Framework: Governed Placement and Movement Across Memory Tiers

The framework assumes the entry gate has returned tier. Phases 1 and 2 establish the hierarchy and admit records into it. Phases 3 through 5 form the steady-state loop: movement is evaluated, eviction reclaims capacity, and thrash detection corrects the policy that produced the movement. Phase 6 runs continuously alongside the loop and holds tiers coherent. Phase 7 closes the loop by measuring the hierarchy against the baselines the gate required, and returns control to Phase 1 whenever a gate is breached.

### Phase 1: Tier Declaration and Budget Assignment

**Objective**: Fix the number of tiers, their service contracts, and their numeric capacity and latency budgets from measured demand, so that every later movement decision is evaluated against a declared bound rather than an impression.

#### Step 1.1: Declare the Tier Service Contracts

**Required Actions**:

- Declare between 2 and 4 tiers, and for each record capacity, maximum latency at p95 and p99, durability class as replica count and recovery point objective, consistency guarantee, eligibility rule, retention class, and cost per unit stored.
- Reject any tier whose declared p95 latency is within a factor of 2 of an adjacent tier, since two tiers that perform alike add copies without adding service.
- Assign each tier a physical backend and record that the mapping is revisable, so tier identity survives a technology change.
- Declare overflow behaviour and dependency-outage behaviour per tier, naming what is refused, what is degraded, and what is served stale.
- Record the durability class that qualifies a copy as the record's surviving copy, and mark every tier that does not qualify.

**Required Outputs**:

- A tier register of 2 to 4 entries with all 8 contract fields populated.
- A backend mapping naming the technology serving each tier.
- An overflow and outage policy statement per tier.

**Quality Checkpoints**:

- Every tier carries a numeric capacity, a numeric p95 and p99 latency bound, and a durability class; a tier missing any of the three is not declared.
- Adjacent tiers differ in measured p95 latency by a factor of at least 2; tiers failing this are merged.
- At least 1 declared tier qualifies as a durable destination, without which no eviction is ever permitted.

***

#### Step 1.2: Assign Capacity and Latency Budgets From Measured Demand

**Required Actions**:

- Measure, per workload, calls per task, input and output tokens, concurrent sessions, new records per task, bytes per canonical record, index amplification, object size, read frequency, cold-fetch frequency, and monthly growth.
- Compute tier zero capacity as the model input limit minus reserved output, tool schemas, operational headroom, and a safety margin of at least 10 percent, then allocate the remainder across the 5 protected classes in the declared precedence order.
- Size tier two from the record count required to meet the target hit rate within the latency objective, adding metadata, cache overhead, lexical postings, vectors, replicas, and write amplification as separate line items.
- Size tier three as admitted bytes times retention times version count, plus lifecycle transitions, restore requests, temporary restored copies, backup, and erasure overhead.
- Set a low and high capacity watermark per tier, defaulting to 70 percent and 85 percent, and a forecast review trigger at 12 months to projected exhaustion.

**Required Outputs**:

- A demand measurement record with one row per workload and per measured quantity.
- A capacity ledger naming provisioned, reserved, pinned, and evictable bytes or tokens per tier.
- A watermark and forecast configuration per tier.

**Quality Checkpoints**:

- Every capacity figure derives from a measured distribution, not from a percentage chosen a priori; unmeasured tiers are provisioned at the measured tier's figure and marked provisional.
- Index, replica, and cache overhead are counted separately from content bytes; a tier sized on content bytes alone is re-sized before admission opens.
- Projected exhaustion is at least 12 months away at current growth, or a capacity review is opened before Phase 2 begins.

***

#### Step 1.3: Establish Canonical Records and Placement State

**Required Actions**:

- Assign every memory a stable identifier and an immutable version identifier, and require every tier copy to record the canonical version and generation it derives from.
- Create the placement table carrying tier, backend, storage class, capacity charge in bytes and tokens, creation, placement and last-access timestamps, minimum-residence expiry, cooldown expiry, pin state and owner, sensitivity class, retention class, and tombstone state.
- Create an outbox written in the same transaction as every canonical change, so derivative rebuild and invalidation are driven by committed facts rather than by best-effort notification.
- Forbid independent edits to any derived copy, and route every correction through a new canonical version.
- Test crash and retry points until one logical operation produces exactly one effect and every stale copy is enumerable by query.

**Required Outputs**:

- A canonical version store with current-version pointers.
- A placement table with all 14 fields populated for every placed record.
- An outbox with committed change events and a replay position.

**Quality Checkpoints**:

- Every derived copy resolves to exactly 1 canonical version; copies that do not are quarantined and rebuilt.
- A repeated movement operation with the same identifier produces no additional effect.
- Stale copies are enumerable by a single query at any moment; where they are not, movement remains disabled.

***

### Phase 2: Admission Control and Initial Placement

**Objective**: Decide which records enter the hierarchy at all and where they first land, so that a single access burst or one large artifact cannot displace established records.

#### Step 2.1: Score Admission Candidates With Decomposed Evidence

**Required Actions**:

- Compute the admission score from named components kept individually visible: recency, access frequency, current-task relevance, source authority, obligation state, predicted reuse, re-fetch cost, and sensitivity risk.
- Obtain the predicted-reuse component from a model forecast, and record it with the model identifier, prompt version, and horizon; cap its weight at 0.30 of the composite score.
- Apply hard rules ahead of the score: policy may forbid admission outright, a legal hold may require retention without residency, and a quarantine flag blocks admission regardless of score.
- Refuse admission to any record whose sensitivity class exceeds the target tier's declared handling, whose tenant scope differs from the tier's namespace, or whose provenance is absent.
- Reject as a single unit any candidate larger than 5 percent of the target tier's capacity, and route it to the next slower tier with a reference retained in the faster tier.

**Required Outputs**:

- An admission record per candidate carrying every score component and its weight.
- A hard-rule verdict per candidate, preceding and dominating the composite score.
- A refusal log naming rejected candidates and the rule that rejected each.

**Quality Checkpoints**:

- No single opaque importance score drives admission; every decision reproduces from its recorded components.
- The model-forecast component never exceeds 0.30 of the composite weight, and a decision that flips on the forecast alone is recorded as forecast-determined.
- Every refusal names a rule, not a threshold alone; unexplained refusals halt admission for review.

***

#### Step 2.2: Place Admitted Records and Open Probation

**Required Actions**:

- Place each admitted record at the slowest tier that satisfies its access-class latency requirement, not at the fastest tier with capacity available.
- Admit newly popular records to a probation segment sized at 10 percent of the target tier's capacity, and promote out of probation only after verified reuse exceeds the weakest incumbent.
- Charge the capacity ledger at placement time, and refuse placement that would carry the tier above its high watermark without first selecting an eviction victim under Phase 4.
- Admit to tier zero only records that are verified, compact, broadly useful across expected calls, safe to repeat, and expensive or risky to miss; treat every other tier-zero candidate as a pin request under Phase 3.
- Record for every placement the expected reuse horizon and the deletion path, so no record enters the hierarchy without a declared exit.

**Required Outputs**:

- A placement record per admitted candidate naming the tier, the reason, and the capacity charge.
- A probation segment inventory with entry time and reuse count per record.
- A per-record expected reuse horizon and deletion path.

**Quality Checkpoints**:

- Initial placement is the slowest satisfying tier for at least 90 percent of admissions; a lower rate indicates the placement rule is being bypassed and admission halts for review.
- The probation segment never exceeds 10 percent of tier capacity; overflow evicts the oldest probationary entry rather than an established record.
- Every placed record carries a reuse horizon and a deletion path; records lacking either are refused.

***

### Phase 3: Promotion and Demotion Under Separated Thresholds

**Objective**: Move records between tiers on numeric triggers whose entry and exit thresholds differ by a declared margin, so that availability tracks demand without oscillating.

#### Step 3.1: Evaluate the Promotion Trigger

**Required Actions**:

- Recompute the composite promotion score on a 0 to 1 scale at each evaluation, from the same named components used at admission, and normalise every component against its tier population rather than against a fixed constant.
- Require all 4 conditions before promoting: the composite score meets the target tier's entry threshold; at least 1 hard access signal is present, meaning 3 or more accesses inside the last 20 task-turns or a current-task relevance of 0.70 or above; the score exceeds the weakest incumbent by a margin of at least 0.15; and the minimum residence at the current tier has elapsed.
- Confirm capacity before movement: promote into free capacity where the target tier sits below its low watermark, and otherwise pair the promotion with an eviction victim selected under Phase 4.
- Apply hard blocks ahead of the score: quarantine state, sensitivity exceeding the target tier, unresolved provenance, or a policy prohibition each block promotion irrespective of score.
- Require independent evidence or a recorded review for any promotion into tier zero whose source trust class is untrusted, since resident text is repeatedly trusted and can influence tool selection.

**Promotion and Demotion Trigger Defaults**:

| Boundary | Promotion entry threshold | Demotion exit threshold | Minimum residence | Cooldown after demotion |
| :-- | :-- | :-- | :-- | :-- |
| Tier one to tier zero | Composite 0.80 and independent verification | Composite below 0.60, or 15 task-turns without access | 5 task-turns | 10 task-turns |
| Tier two to tier one | Composite 0.65 | Composite below 0.45, or 3 times median reuse interval without access | 20 task-turns | 40 task-turns |
| Tier three to tier two | Composite 0.50 and an explicit restore request | Composite below 0.30, or 90 days without access | 30 minutes | 60 minutes |
| Any tier to tier three | Not applicable; archival is a demotion | Retention class requires retention and reuse is below 1 access per 90 days | 24 hours | 48 hours |

**Required Outputs**:

- A promotion evaluation record per candidate carrying all 4 conditions and their measured values.
- A capacity verdict naming free capacity or the paired eviction victim.
- A hard-block log naming every promotion refused by rule rather than by score.

**Quality Checkpoints**:

- No promotion executes with any of the 4 conditions unmet; a promotion missing a condition is rejected and logged as a policy violation.
- The margin over the weakest incumbent is at least 0.15 in every displacing promotion; smaller margins are refused because they buy movement without buying service.
- Every tier-zero promotion from an untrusted source carries independent evidence or a recorded review; those lacking both are quarantined.

***

#### Step 3.2: Evaluate the Demotion Trigger With Hysteresis

**Required Actions**:

- Set every demotion exit threshold at least 0.20 below the corresponding promotion entry threshold on the 0 to 1 scale, and never evaluate promotion and demotion against a single shared threshold.
- Trigger demotion on any of: composite score below the exit threshold; inactivity beyond 3 times the tier's measured median reuse interval, floored at 15 task-turns for tier zero and tier one; supersession by a newer canonical version; completion of the obligation that justified residency; staleness beyond the record's declared validity; a raised sensitivity class; or capacity pressure above the high watermark.
- Enforce the minimum residence time before any demotion, so a record admitted moments earlier is not immediately displaced by the next arrival.
- Apply a cooldown of at least 2 times the minimum residence after every demotion, during which re-promotion requires an explicit pin or a hard trigger such as the current request naming the record by identifier.
- Expire pins on their declared review date rather than on inactivity, and record owner, reason, expiry, and capacity charge for every pin.

**Required Outputs**:

- A demotion evaluation record naming the trigger that fired and its measured value.
- A hysteresis configuration recording the entry threshold, exit threshold, gap, minimum residence, and cooldown per boundary.
- A pin register with owner, reason, expiry, charge, and review date per pin.

**Quality Checkpoints**:

- The gap between entry and exit thresholds is at least 0.20 at every boundary; a smaller gap is corrected before movement resumes.
- No record is demoted before its minimum residence has elapsed, and none is re-promoted inside its cooldown without a recorded hard trigger.
- Every pin carries an expiry and a review date; pins without either are released at the next evaluation.

***

#### Step 3.3: Execute at Most One Movement per Record per Window

**Required Actions**:

- Cap movement at 1 boundary crossing per record per movement window, defaulting to the shorter of 1 hour and 50 task-turns, and queue further crossings for the following window.
- Cap aggregate movement at 10 percent of a tier's capacity per window, and where demand exceeds the cap, execute the highest-margin movements first and defer the rest.
- Execute movement idempotently against the placement table, charging and crediting capacity in the same transaction, so a retried movement neither double-charges nor loses a placement.
- Perform movement asynchronously off the request path wherever the record is not required for the current turn, so promotion latency never enters the user-visible budget.
- Record for every executed movement the decision type, trigger, policy version, threshold version, all score components, capacity before and after, and the incumbent displaced.

**Required Outputs**:

- A movement log with one append-only entry per executed movement carrying all 7 recorded fields.
- A deferred-movement queue with the reason each entry was deferred.
- An updated capacity ledger reflecting every charge and credit.

**Quality Checkpoints**:

- No record crosses the same boundary more than once inside one movement window; a second crossing is refused and counted as a thrash event under Phase 5.
- Aggregate movement stays within 10 percent of tier capacity per window; breaches halt autonomous movement and open a capacity review.
- Every movement is reproducible from its log entry alone, without consulting mutable cache state.

***

### Phase 4: Eviction Under a Durability Guarantee

**Objective**: Reclaim capacity by removing derived copies while proving that every evicted record remains recoverable, so that eviction never becomes undeclared deletion.

#### Step 4.1: Verify the Surviving Durable Copy

**Required Actions**:

- Refuse any eviction until the placement table shows at least 1 copy of the same canonical version at a tier whose durability class meets or exceeds the record's declared retention class.
- Verify the surviving copy by content hash comparison against the canonical version, not by the existence of a placement row alone, since a row can outlive the object it names.
- Reclassify as deletion any eviction that would remove the last durable copy, halt it, and require an explicit deletion authorisation carrying requester, approver, and legal basis.
- Confirm the surviving copy is readable within its tier's declared restore bound before the faster copy is released, and record the verification timestamp and method.
- Record the recovery path for every evicted record: the surviving tier, the expected restore latency class, and the cost of the restore.

**Required Outputs**:

- A durability verification record per eviction carrying the surviving tier, the hash comparison result, and the verification method.
- A recovery path statement per evicted record.
- A reclassification log naming every eviction converted to a deletion request.

**Quality Checkpoints**:

- Zero evictions execute without a hash-verified surviving copy; a single unverified eviction halts the eviction worker.
- No eviction removes the last durable copy; such operations appear only in the reclassification log, never in the movement log.
- Every evicted record carries a recovery path naming a tier and a latency class.

***

#### Step 4.2: Select Victims and Reclaim Capacity

**Required Actions**:

- Begin eviction when a tier reaches its high watermark at 85 percent of capacity and stop at its low watermark at 70 percent, so eviction runs in bounded batches rather than continuously at the margin.
- Select victims by the tier's declared replacement policy, defaulting to a segmented recency policy guarded by a frequency-based admission filter, which resists scan pollution better than recency alone [6][7].
- Exclude from victim selection every pinned record, every record inside its minimum residence, and every record carrying an unresolved obligation or an active transaction.
- Replay recorded access traces against the candidate policies at the same capacity and compare each against an offline optimal bound, and adopt the simplest policy whose miss rate falls within the declared gap of that bound [8].
- Never serve stale authorisation or tombstoned content to avoid an eviction, and never extend a tier past its high watermark to postpone a victim decision.

**Required Outputs**:

- An eviction batch record naming the victims, the policy version, and the capacity reclaimed.
- A policy comparison record covering at least 3 candidate policies and the offline bound on the same trace.
- An exclusion list naming pinned, resident-minimum, and obligation-bearing records withheld from selection.

**Quality Checkpoints**:

- Eviction runs only between the high and low watermarks; continuous eviction at the boundary indicates the tier is under-provisioned and opens a capacity review.
- No pinned, minimum-residence, or obligation-bearing record appears in any eviction batch.
- The adopted policy's miss rate sits within the declared gap of the offline bound on the replayed trace; a wider gap returns the selection to comparison.

***

### Phase 5: Thrash Detection and Policy Correction

**Objective**: Detect the numeric signature of records oscillating across a tier boundary and correct the policy that produced it, before movement consumes the budget the hierarchy was built to save.

#### Step 5.1: Compute the Thrash Signature

**Required Actions**:

- Record a thrash event whenever one memory identifier crosses the same tier boundary in both directions inside that boundary's minimum residence window, using the movement log rather than mutable cache state as the evidence.
- Flag a record as thrashing when it accumulates 3 or more crossings of the same boundary inside one movement window, defaulting to the shorter of 1 hour and 50 task-turns.
- Compute the system thrash rate as thrashing records divided by records moved inside the window, and report the boundary and the window with every figure, since neither number means anything without both.
- Compute the movement overhead ratio as the cost of movement, including transfer bytes, re-embedding, re-serialization, and invalidation work, divided by total tier-serving cost for the same window.
- Confirm the diagnosis against the two lagging indicators: promotion precision below 50 percent together with demotion regret above 20 percent inside the same window distinguishes genuine thrashing from a legitimate shift in the working set.

**Thrash Signature Thresholds and Responses**:

| Measured signature | Numeric trigger | Response tier |
| :-- | :-- | :-- |
| Per-record oscillation | 3 or more crossings of one boundary in 1 movement window | Freeze that record for 1 window |
| System thrash rate | Above 5 percent of moved records in 1 window | Graduated correction, level 1 |
| System thrash rate, sustained | Above 5 percent across 2 consecutive windows | Graduated correction, level 2 |
| System thrash rate, severe | Above 15 percent in any window | Halt movement and escalate |
| Movement overhead ratio | Above 15 percent of tier-serving cost | Graduated correction, level 1 |
| Movement overhead ratio, severe | Above 25 percent of tier-serving cost | Halt movement and escalate |
| Confirming lagging pair | Promotion precision below 50 percent and demotion regret above 20 percent | Confirms thrashing rather than working-set shift |

**Required Outputs**:

- A thrash event log keyed by memory identifier, boundary, and window.
- A thrash rate and movement overhead figure per window, each carrying its boundary and window definition.
- A confirmation verdict distinguishing thrashing from a working-set shift.

**Quality Checkpoints**:

- Every thrash figure is reported with its boundary and its window; a figure lacking either is rejected as uninterpretable.
- The confirming lagging pair is computed before any correction is applied, so a genuine working-set shift is not suppressed as though it were oscillation.
- Thrash detection runs on the append-only movement log; a detector reading mutable cache rows is replaced, since evicted rows erase the evidence.

***

#### Step 5.2: Apply the Graduated Policy Correction

**Required Actions**:

- Apply level 1 on first breach: double the minimum residence time and widen the hysteresis gap by 0.10 at the affected boundary, and version the threshold change so the correction is attributable.
- Apply level 2 on a second consecutive breach: freeze movement across the affected boundary for 1 window and pin the highest-scoring incumbents up to the tier's low watermark, so the working set stabilises before movement resumes.
- Apply level 3 on a severe breach: halt autonomous movement entirely and escalate, because a thrash rate above 15 percent or a movement overhead above 25 percent indicates the faster tier is under-provisioned rather than mistuned, and threshold changes will not repair it.
- Correct admission alongside residency where thrashing concentrates in newly admitted records, by enlarging the probation segment or raising the admission threshold rather than by adjusting promotion alone.
- Never respond by slowing the movement scheduler while leaving contradictory thresholds in place, since that converts visible oscillation into invisible staleness.

**Required Outputs**:

- A correction record naming the level applied, the boundary affected, the parameters changed, and the threshold version issued.
- A post-correction measurement of thrash rate and movement overhead over the following window.
- An escalation record for every level 3 breach naming the under-provisioned tier and its capacity shortfall.

**Quality Checkpoints**:

- Every correction is versioned and attributable to a measured breach; unversioned threshold edits are reverted.
- The thrash rate falls below 5 percent within 2 windows of a level 1 or level 2 correction; where it does not, the response escalates to level 3 rather than repeating level 1.
- No correction consists solely of reducing movement frequency; corrections that do not change a threshold, a residency, or a capacity are rejected.

***

### Phase 6: Cross-Tier Coherence and Deletion Propagation

**Objective**: Hold every tier consistent with one canonical version, so that a record updated in one tier is never served stale from another and a deleted record survives nowhere.

#### Step 6.1: Version and Invalidate Derived Copies

**Required Actions**:

- Create a new canonical version for every change, and write the outbox event inside the same transaction, so no derivative rebuild depends on a notification that can be lost.
- Invalidate higher-tier copies before or atomically with making the new version current, so no faster tier serves an older version than a slower tier holds.
- Overlay committed records not yet indexed on read, so a principal reads their own writes without waiting for derivative rebuild.
- Meet declared invalidation propagation bounds: p95 no more than 5 seconds for tier zero and tier one copies, no more than 60 seconds for tier two indexes, and no more than 24 hours for archive catalogues.
- Store derivation lineage per derived copy, so one source correction invalidates every ancestor summary and every cached assembly built from it.

**Required Outputs**:

- An invalidation record per change naming cause, affected placements, affected cache keys, affected index generations, and completion state.
- A lineage graph linking every derived copy to its canonical sources.
- A propagation latency measurement per tier against its declared bound.

**Quality Checkpoints**:

- Zero stale copies are servable on tested online paths after propagation completes; a non-zero count halts serving from the affected tier.
- Every derived copy resolves to a lineage path terminating in canonical sources; copies with broken lineage are rebuilt rather than repaired.
- Propagation p95 meets the declared bound per tier; a breach opens an invalidation review before further movement.

***

#### Step 6.2: Publish Derived Generations Atomically

**Required Actions**:

- Build index and summary generation n plus 1 from a canonical snapshot, catch up the changes committed during the build, and validate record counts, deletions, retrieval quality, and placement before publication.
- Publish by moving a serving alias atomically from generation n to generation n plus 1, never by mutating a live generation in place.
- Retain generation n for a bounded rollback window, defaulting to 24 hours, and delete it on expiry rather than indefinitely.
- Refuse to mix embeddings produced by incompatible models in one score space, or summaries derived from different canonical versions in one node, without a recorded compatibility statement.
- Re-run the validation suite against the new generation before the alias moves, and abort publication on any regression beyond the declared gate.

**Required Outputs**:

- A generation record per build naming the snapshot, the catch-up range, and the validation results.
- An alias history showing every cutover and its rollback window.
- A compatibility statement per score space and per summary node.

**Quality Checkpoints**:

- No generation is mutated after publication; in-place edits to a live generation halt the publication pipeline.
- Every cutover is reversible inside the declared rollback window; cutovers without a retained predecessor are blocked.
- Validation runs on the new generation before the alias moves, never after.

***

#### Step 6.3: Propagate Tombstones Across Every Tier

**Required Actions**:

- Commit a tombstone that makes every version of the memory immediately ineligible for retrieval, ahead of the physical removal that follows.
- Fan out high-priority invalidations to prompt assemblies, application caches, lexical and vector indexes, summary nodes, checkpoints, archive objects and restores, exports, and backup schedules.
- Search every serving route after deletion, including negative caches, partial assemblies in flight, and retained generations, and record a residual stale-copy count per route.
- Handle backup residuals explicitly: keep deleted data beyond use until the scheduled purge, record the exception with its basis and its purge date, and never restore a backup without replaying tombstones against it.
- Complete valid erasure requests inside the applicable statutory period, notify recipients where required, and record every lawful exception rather than leaving the request silently incomplete [10].

**Required Outputs**:

- A deletion record naming requester, approver, legal basis, and every target with its tier, status, verification method, and scheduled purge.
- A residual stale-copy count per serving route after propagation.
- A backup residual register with purge dates and exception codes.

**Quality Checkpoints**:

- Deleted content is unreachable on 100 percent of tested online routes; any reachable copy halts the deletion as incomplete.
- Every backup restore replays tombstones before the restored data is served; restores that do not are quarantined.
- Every erasure request carries either a completion verification or a recorded lawful exception; silent incompletion is a release-blocking defect.

***

### Phase 7: Evaluation Against Declared Gates and Simpler Baselines

**Objective**: Prove that the hierarchy improves cost or latency per successful task against a flat store and a long-context alternative, so that added tiers are retained on evidence rather than on architecture preference.

#### Step 7.1: Measure Tier, Movement, and Compaction Quality

**Required Actions**:

- Define per-tier hit rate as requests satisfied within the tier's evidence and quality gate divided by eligible requests reaching that tier, and report conditional and cumulative rates separately.
- Pair every hit-rate figure with answer correctness, provenance completeness, and staleness, since a high resident-core hit rate is a defect where stale or poisoned blocks produce confident wrong answers.
- Measure p50, p95, and p99 for prompt assembly, warm exact lookup, lexical search, vector search, cold restore, movement, invalidation, and deletion, and compare each against its declared tier bound.
- Measure promotion precision after the declared horizon, demotion regret inside the regret window, false pin rate, movement rate, thrash rate, stale-hit rate, and tier occupancy, each reported with its window.
- Gate every compaction on answer preservation over holdout questions generated from source leaves before the summary was written, scoring exact identifiers, chronology, contradictions, minority cases, and uncertainty separately, and rejecting compression ratio as a substitute for that score.

**Required Outputs**:

- A tier metric report with one row per tier and per declared bound, carrying measured and target values.
- A movement metric report carrying promotion precision, demotion regret, thrash rate, and movement overhead with windows.
- A compaction quality report carrying per-slice answer preservation against the predeclared holdout set.

**Quality Checkpoints**:

- Every metric carries a denominator and a window; a metric lacking either is not reported.
- Compaction that reduces tokens while raising unsupported confident answers is rejected regardless of its compression ratio.
- Promotion precision is at least 60 percent and demotion regret no more than 15 percent; breaches return the thresholds to Phase 3 for revision.

***

#### Step 7.2: Compare Against Flat and Long-Context Baselines

**Required Actions**:

- Run 3 matched baselines on the same frozen corpus with model, task set, authorisation, and output budget held constant: bounded recent context with no durable memory, one flat canonical store with hybrid retrieval, and a long-context configuration using the full eligible history.
- Vary evidence position across the long-context runs, since retrieval accuracy degrades when relevant evidence sits away from the edges of the input [2].
- Measure end-to-end task success, evidence faithfulness, token use, billed cost, p95 and p99 latency, storage growth, deletion completeness, and attack success for every configuration including the hierarchy.
- Model economics per successful task rather than per request, amortising each promotion and each summary across the future successful tasks that actually consume it, and counting build cost, validation cost, and expected failure cost on the other side of the ledger.
- Retire any tier that does not improve at least 1 declared gate against the best baseline, and record the retirement rather than leaving the tier in place unused.

**Required Outputs**:

- A baseline comparison table covering 4 configurations and all 8 measured dimensions.
- A per-successful-task economic model with amortisation horizon stated.
- A tier retention or retirement decision per declared tier, each citing the gate it improved or failed.

**Quality Checkpoints**:

- All 4 configurations run on the same frozen corpus with the same model and budgets; a comparison across differing conditions is discarded.
- The hierarchy beats the best baseline on at least 1 declared gate without regressing any other beyond its stated tolerance; otherwise the design simplifies.
- Every retained tier cites a gate it improves; tiers citing none are retired at the next revision.

***

## III. Implementation Guidance for AI Agents

AI agents operating a memory hierarchy must follow systematic protocols ensuring that every placement is accounted, every movement is reproducible, every eviction is recoverable, and no model judgement overrides a capacity or durability bound. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Tier Registrar**: Owns the tier register, the service contracts, and the threshold versions. It alone may declare, merge, or retire a tier, and every change is versioned and dated.
2. **Placement Accountant**: Owns the capacity ledger, the placement table, the watermarks, and the residency and cooldown timers. It is deterministic, holds authority in every hybrid decision, and may veto any movement that breaches a bound.
3. **Relevance Forecaster**: Produces the predicted-reuse component and the access-class classification through model inference. It never executes a movement, never reads the capacity ledger as an input, and its output is capped at 0.30 of any composite score.
4. **Movement Executor**: Performs admissions, promotions, demotions, evictions, and archival transitions idempotently against the placement table, charging and crediting capacity in the same transaction. It may not change a threshold.
5. **Coherence Agent**: Owns invalidation fan-out, generation builds and cutovers, lineage, and tombstone propagation. It may block a cutover and may quarantine a tier whose stale-copy count is non-zero.
6. **Thrash Monitor**: Computes thrash events, thrash rate, and movement overhead from the append-only movement log, issues graduated corrections, and may freeze movement across a boundary without further authorisation.
7. **Evaluation Agent**: Runs the baseline comparisons, the compaction answer-preservation gates, and the metric reports, and may withhold promotion of a configuration whose advantage is unproven.

**Separation Requirements**: The component producing the relevance forecast is never the component enforcing capacity, and the component executing movement is never the component setting thresholds. Where one model serves several roles, the state and the authority of each role remain distinguishable, since a forecaster that can also enforce capacity will eventually justify its own forecasts.

**Workflow Execution Pattern**:

```
STATE: Movement_Evaluation
INPUTS:
  1. Placement row and capacity ledger entry for the candidate
  2. Access counters and residency timers from the deterministic tier
  3. Relevance forecast with model id, prompt version, and horizon
  4. Threshold set and policy version for the affected boundary
ACTIONS:
  1. Recompute composite score from named components
  2. Evaluate all four promotion conditions or any demotion trigger
  3. Verify capacity headroom or select a paired eviction victim
  4. Verify a hash-matched durable copy for any eviction
  5. Emit exactly one movement decision for the record
VALIDATION:
  - movement_decisions_for_record_in_window <= 1
  - forecast_weight_in_composite <= 0.30
  - minimum_residence_elapsed == TRUE
  - cooldown_expired == TRUE OR hard_trigger_present == TRUE
  - hysteresis_gap >= 0.20
  - durable_copy_hash_verified == TRUE IF decision == EVICT
  - tier_capacity_after <= high_watermark
TRANSITIONS:
  IF decision IN {ADMIT, PROMOTE, DEMOTE, ARCHIVE}
     THEN next_state = Execute_Movement_And_Charge_Capacity
  IF decision == EVICT AND durable_copy_hash_verified == TRUE
     THEN next_state = Execute_Eviction
  IF decision == EVICT AND durable_copy_hash_verified == FALSE
     THEN next_state = Reclassify_As_Deletion_Request
  IF thrash_rate_in_window > 0.05 THEN next_state = Graduated_Correction
  IF validation_failed THEN next_state = Movement_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended movement with its score components, its capacity effect, and its durability verdict without executing it; confirm it against the validation block while no capacity is charged and no copy is released; commit it only after validation passes, writing the movement log entry in the same transaction that charges the ledger.

**Approval Gate**: Human authorisation is required before any eviction that would leave fewer than 2 durable copies of a record carrying a retention or legal-hold class; before raising the tier zero budget above 40 percent of assembled prompt capacity; before any movement batch exceeding 10 percent of a tier's capacity in one window; before promoting into tier zero any record whose source trust class is untrusted; and before relaxing any hysteresis gap below 0.20. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the tier register, capacity ledger, placement table, and threshold versions in durable state, since the hierarchy outlives any single context window.
- Serialize tier zero deterministically with stable policy and tool schemas first, so a prompt-cache boundary is stable and a content change never invalidates more of the prefix than it must.
- Choose the reclamation mode deliberately: summarise where several records share repeatedly needed context and the answer-preservation gate passes, evict where the exact item is cheaply re-fetchable, offload where exact bytes must survive but need not sit in an interactive tier, and delete only where policy requires removal.
- Never describe summary creation as forgetting while source data remains, since the distinction determines whether an erasure obligation has been discharged.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Tier Contract Integrity (After Phase 1)**

- **Automated Check**: Every declared tier carries capacity, p95 and p99 latency, and durability class; adjacent tiers differ in measured p95 by a factor of at least 2; at least 1 tier qualifies as a durable destination; projected exhaustion is at least 12 months away.
- **Agent Action on Pass**: Open admission and proceed to initial placement.
- **Agent Action on Failure**: Halt before admission; an incomplete tier contract makes every later movement unverifiable.
- **Human Review Trigger**: No tier qualifies as a durable destination, or projected exhaustion is under 6 months.

**Checkpoint 2: Admission Discipline (After Phase 2)**

- **Automated Check**: Every admission reproduces from its recorded score components; the forecast weight is no more than 0.30; probation holds no more than 10 percent of tier capacity; at least 90 percent of placements are at the slowest satisfying tier.
- **Agent Action on Pass**: Proceed to movement evaluation.
- **Agent Action on Failure**: Suspend admission for the affected class and rebuild the refused candidates' records.
- **Human Review Trigger**: More than 20 percent of admissions determined by the model forecast alone.

**Checkpoint 3: Movement Validity (After Phase 3)**

- **Automated Check**: Every promotion satisfies all 4 conditions; every hysteresis gap is at least 0.20; no record crosses a boundary more than once per window; aggregate movement is within 10 percent of tier capacity.
- **Agent Action on Pass**: Proceed to eviction and capacity reclamation.
- **Agent Action on Failure**: Reject the offending movements, revert their capacity charges, and log a policy violation.
- **Human Review Trigger**: Any hysteresis gap edited below 0.20, or 3 consecutive windows with aggregate movement at the cap.

**Checkpoint 4: Durability Before Eviction (After Phase 4)**

- **Automated Check**: 100 percent of evictions carry a hash-verified surviving durable copy; zero evictions appear that would remove a last durable copy; no pinned or minimum-residence record appears in an eviction batch.
- **Agent Action on Pass**: Release the reclaimed capacity and continue serving.
- **Agent Action on Failure**: Halt the eviction worker immediately; this failure is never resolved by retry.
- **Human Review Trigger**: Any eviction reclassified as a deletion request, or any unverified eviction detected.

**Checkpoint 5: Movement Stability (After Phase 5)**

- **Automated Check**: Thrash rate no more than 5 percent and movement overhead no more than 15 percent for the window; every correction is versioned; the confirming lagging pair was computed before correction.
- **Agent Action on Pass**: Resume normal movement at the current thresholds.
- **Agent Action on Failure**: Apply the graduated correction at the level the signature indicates and re-measure over the next window.
- **Human Review Trigger**: Thrash rate above 15 percent, or movement overhead above 25 percent, in any window.

**Checkpoint 6: Coherence and Erasure (After Phase 6)**

- **Automated Check**: Zero servable stale copies on tested online routes; propagation p95 within the declared bound per tier; every cutover reversible inside the rollback window; deleted content unreachable on 100 percent of tested routes.
- **Agent Action on Pass**: Publish the generation and close the invalidation batch.
- **Agent Action on Failure**: Quarantine the affected tier from serving until the stale-copy count returns to zero.
- **Human Review Trigger**: Any reachable deleted content, or any backup restored without tombstone replay.

**Checkpoint 7: Baseline Justification (After Phase 7)**

- **Automated Check**: All 4 configurations ran on the same frozen corpus; the hierarchy improves at least 1 declared gate without regressing another beyond tolerance; promotion precision at least 60 percent and demotion regret no more than 15 percent.
- **Agent Action on Pass**: Retain the hierarchy and release the metric report.
- **Agent Action on Failure**: Retire the tiers citing no improved gate and simplify the design.
- **Human Review Trigger**: The hierarchy fails to beat the flat baseline on any declared gate, or compaction answer preservation falls below its declared slice thresholds.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
VALIDATION_CRITERIA:
MEASURED_VALUE:
MEASUREMENT_WINDOW:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Thrashing Across a Tier Boundary**

- **Symptoms**: The same memory identifier appears repeatedly in the movement log for one boundary; movement overhead rises while hit rate is flat; promotion precision falls below 50 percent while demotion regret rises above 20 percent.
- **Diagnostic Steps**: Recompute crossings per identifier per window from the append-only log; compare the entry and exit thresholds for the boundary; confirm the minimum residence and cooldown were enforced rather than merely configured; separate genuine working-set shift from oscillation using the confirming lagging pair.
- **Resolution Protocol**: Option A, double the minimum residence and widen the hysteresis gap by 0.10 at the affected boundary. Option B, freeze the boundary for 1 window and pin the highest-scoring incumbents to the low watermark. Option C, enlarge the probation segment or raise the admission threshold where thrashing concentrates in newly admitted records. Option D, provision the faster tier upward where the working set genuinely exceeds capacity.
- **Escalation Trigger**: A thrash rate above 15 percent or a movement overhead above 25 percent halts autonomous movement and escalates; this class is never resolved by slowing the scheduler while contradictory thresholds remain.

**Error Type 2: Eviction Without a Surviving Durable Copy**

- **Symptoms**: A record is unreachable at every tier after a capacity event; a placement row references an object that no longer exists; a restore returns a hash that does not match the canonical version.
- **Diagnostic Steps**: Replay the movement log for the record to locate the eviction and its durability verdict; verify whether the verification checked a hash or only the existence of a placement row; determine whether the surviving copy was itself evicted inside the same batch.
- **Resolution Protocol**: Option A, restore from backup and replay tombstones before serving. Option B, rebuild the record from its lineage sources where the derivation is reproducible. Option C, mark the record irrecoverable, record the loss with its window and cause, and notify the retention owner.
- **Escalation Trigger**: Any single unverified eviction halts the eviction worker and escalates immediately; this class is never resolved by retry, and eviction does not resume until hash verification is proven on a test batch.

**Error Type 3: Stale or Poisoned Resident Core Block**

- **Symptoms**: Confident answers contradict the current canonical version; a resident block carries no verification date; retrieval dominance concentrates on one record; instruction-like content appears in material admitted as data.
- **Diagnostic Steps**: Compare every resident block's canonical version against the current pointer; check validity, source, verification date, and expiry per block; trace the block's admission path and source trust class; test whether the block's influence survives removal of the suspected source.
- **Resolution Protocol**: Option A, refresh the block from its canonical version and re-run assembly. Option B, quarantine the block, demote it, and require independent evidence before re-promotion. Option C, separate the affected content from policy scope so it can no longer alter instruction authority. Option D, revoke the pin and reduce the tier zero budget until the source is verified.
- **Escalation Trigger**: Any promotion of untrusted content into tier zero without independent evidence, or any post-promotion behaviour anomaly, escalates and suspends autonomous tier zero admission for the affected class.

**Error Type 4: Capacity Exhaustion, Stampede, and Hot-Key Concentration**

- **Symptoms**: A tier sits continuously at its high watermark; concurrent misses trigger duplicate fetches or restorations; one principal, topic, or record consumes a disproportionate share of a tier or a shard; tail latency rises while median latency holds.
- **Diagnostic Steps**: Measure occupancy against watermarks over the window; count concurrent identical fetches per key; compute the share of tier capacity and retrieval volume held by the top key and the top principal; separate genuine growth from a single burst.
- **Resolution Protocol**: Option A, coalesce concurrent requests behind a bounded single-flight lease with jittered refresh, preserving authorisation per waiter. Option B, apply per-principal quotas, shard-aware routing, and replication for hot keys. Option C, raise the tier's provisioned capacity where the working set has genuinely grown. Option D, apply negative caching with a short time to live scoped by principal, policy, index generation, and query fingerprint, invalidated on write.
- **Escalation Trigger**: Occupancy above the high watermark for 3 consecutive windows, or a single key holding more than 10 percent of tier capacity, escalates for capacity and quota review. Stale authorisation and tombstoned content are never served to relieve a stampede.

**Error Type 5: Irrecoverable Compaction Drift**

- **Symptoms**: Answer preservation falls on identifier, chronology, or minority-case slices while compression ratio improves; a summary cites a descendant of itself; exceptions and uncertainty disappear across successive summary levels.
- **Diagnostic Steps**: Score the compacted hierarchy against holdout questions generated from immutable leaves before compaction; check lineage for cycles and for summaries admitted as sources; compare summary-only, leaf-only, and combined retrieval on the same questions.
- **Resolution Protocol**: Option A, enlarge the summary or split the node so the omitted material survives. Option B, retrieve leaves for the affected slice and verify high-impact answers against canonical sources. Option C, retain the richer record in warm storage and evict re-fetchable content instead of compacting. Option D, regenerate the affected branch from sources after a summariser model or prompt change.
- **Escalation Trigger**: Any circular lineage halts publication of the summary generation; any slice falling below its declared answer-preservation gate blocks the compaction and escalates rather than being averaged away against a passing slice.

**Error Type 6: Divergent Copies Across Tiers**

- **Symptoms**: Two tiers return different content for one memory identifier; a derived copy carries no canonical version; read-after-write consistency fails for the writing principal; a retired generation continues serving.
- **Diagnostic Steps**: Enumerate all copies by canonical version and compare against the current pointer; check whether the outbox event committed in the same transaction as the change; verify the alias points at the intended generation; search negative caches and in-flight assemblies.
- **Resolution Protocol**: Option A, rebuild the divergent copy from its canonical version and lineage. Option B, roll the serving alias back to the retained predecessor generation and re-run validation. Option C, quarantine the affected tier from serving until the stale-copy count returns to zero. Option D, overlay committed records not yet indexed so reads remain correct while rebuild proceeds.
- **Escalation Trigger**: A non-zero stale-copy count on a tested online route after propagation escalates and blocks further movement across that boundary; divergence is never resolved by editing a derived copy in place.

**Troubleshooting Decision Tree**:

```
TIER POLICY DETECTS A PROBLEM
├─ MOVEMENT DEFECT
│   ├─ Same boundary crossed both ways in residence window → Count thrash event; apply graduated correction
│   ├─ Thrash rate above 15 percent → HALT movement; escalate as capacity shortfall
│   └─ Promotion missing one of four conditions → Reject movement; log policy violation
├─ DURABILITY DEFECT
│   ├─ Eviction without hash-verified surviving copy → HALT eviction worker; escalate
│   ├─ Last durable copy targeted → Reclassify as deletion; require authorisation
│   └─ Restore hash mismatch → Rebuild from lineage or declare irrecoverable
├─ CAPACITY DEFECT
│   ├─ Occupancy above high watermark for three windows → Provision upward; open capacity review
│   ├─ Single key above 10 percent of tier → Apply quota, replication, shard-aware routing
│   └─ Duplicate concurrent fetches → Coalesce under bounded lease; never serve stale authorisation
├─ COHERENCE DEFECT
│   ├─ Stale copy servable after propagation → Quarantine tier from serving
│   ├─ Derived copy without canonical version → Rebuild; never repair in place
│   └─ Deleted content reachable on any route → HALT release; re-run tombstone fan-out
└─ CONTENT DEFECT
    ├─ Circular summary lineage → Block generation publication; regenerate from leaves
    ├─ Answer-preservation slice below gate → Reject compaction; retain richer record
    └─ Untrusted content promoted to resident core → Quarantine; suspend tier zero admission
```

### D. Performance Metrics and Continuous Learning

**Placement and Retrieval Metrics**:

- **Conditional tier hit rate**: Requests satisfied within a tier's evidence and quality gate over eligible requests reaching that tier (target: at least 70 percent at tier one, at least 85 percent cumulative across tiers zero to two).
- **Stale-hit rate**: Hits served from a copy whose canonical version is superseded (target: 0 percent on tested online routes; any non-zero value quarantines the tier).
- **Cold-path share**: Interactive requests reaching tier three (target: no more than 2 percent; a higher share indicates tier two is under-provisioned).
- **Tail latency conformance**: Proportion of tier probes within the declared p95 and p99 bounds (target: at least 95 percent per tier per window).

**Movement Quality Metrics**:

- **Promotion precision**: Promotions used within the declared horizon over completed promotions (target: at least 60 percent; below 50 percent with rising regret confirms thrashing).
- **Demotion regret**: Demotions followed by a qualifying re-fetch inside the regret window over completed demotions (target: no more than 15 percent).
- **Thrash rate**: Records crossing one boundary more than the configured count inside the movement window over records moved (target: no more than 5 percent; above 15 percent halts movement).
- **Movement overhead ratio**: Cost of movement over total tier-serving cost (target: no more than 15 percent; above 25 percent halts movement).
- **False pin rate**: Pins expiring unused or without a recorded review over pins created (target: no more than 10 percent).

**Integrity and Economic Metrics**:

- **Durability verification coverage**: Evictions carrying a hash-verified surviving copy over evictions executed (target: 100 percent, without exception).
- **Invalidation propagation p95**: Time from canonical change to derivative ineligibility, per tier (target: within each tier's declared bound).
- **Deletion completeness**: Tested serving routes returning no deleted content over routes tested (target: 100 percent).
- **Compaction answer preservation**: Holdout answers preserved, reported per slice for identifiers, chronology, contradictions, and minority cases (target: at least 90 percent per slice; a failing slice is never averaged against a passing one).
- **Cost per successful task**: Total tier cost over accepted successful tasks, amortising promotions and summaries across their reuse horizon (target: below the best simpler baseline at matched quality).

**Learning and Adaptation Mechanisms**:

- **Delayed label adjudication**: Attach usefulness labels to each movement after the declared horizon, so promotion precision and demotion regret are measured against outcomes rather than against intent.
- **Threshold recalibration**: Recompute entry thresholds, exit thresholds, residency, and cooldown per workload class against observed access distributions; the values in this guide are deployment defaults, not constants.
- **Forecaster calibration**: Compare the relevance forecast against realised use per class, and lower its weight below 0.30 in any class where its calibration gap exceeds 20 percentage points.
- **Trace replay**: Retain access traces long enough to replay candidate replacement policies against an offline bound whenever the workload, model, tokenizer, retriever, or storage class changes materially.
- **Reopening the loop**: Return to Phase 1 whenever the model, prompt order, provider cache behaviour, canonical schema, retriever, quantisation, storage class, traffic pattern, or threat model changes materially, since every tier bound was derived under the prior configuration.

**Human-in-the-Loop Boundaries**: Eviction leaving fewer than 2 durable copies of a retention-classed record, deletion authorisation, relaxation of a hysteresis gap below 0.20, promotion of untrusted content into the resident core, and retirement of a tier carrying a legal hold are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs where records live and what moves them, not what the records mean. Its phases hold wherever an agent's eligible corpus exceeds what it can hold resident, access is skewed, and storage layers differ measurably in cost or latency.

### 4.1 Cross-Domain Application Patterns

**Long-running conversational assistance**: The working set is small and turns over quickly, so tier one carries the unresolved obligations and the resumption checkpoint while tier two carries verified preferences and prior resolutions. Promotion is driven mainly by current-task relevance rather than by frequency, because a preference used once per month is worth resident space during the month it matters. The dominant failure is the stale resident block: a preference pinned during one engagement and never re-verified continues to shape answers after it has ceased to be true, so every pinned fact carries a verification date and an expiry, and tier zero is rebuilt from canonical versions on every assembly rather than carried forward.

**Software engineering over large repositories**: The corpus is large, highly skewed, and cheaply re-fetchable, which shifts the reclamation mode decisively toward eviction rather than summarisation. Tier zero carries the task contract, the interface contracts, and the current diff; tier one carries the files under active edit and the failing test output; tier two carries the symbol and dependency indexes. Because a file can be re-read exactly at low cost, summarising it is usually a loss, and the answer-preservation gate rejects most compaction of code. Thrashing appears when a build touches a wide file set once, which is why the admission filter and the probation segment matter more here than the replacement policy.

**Clinical and other regulated decision support**: Sensitivity is a placement constraint before it is an encryption question. A record permitted in an encrypted canonical store may not be permitted in a shared cache, a provider prompt cache, a cross-region archive, or a global index, so the eligibility rule in each tier contract carries the residency, consent, and purpose conditions, and admission refuses on them ahead of any score. Erasure obligations traverse every tier and every derivative, so the deletion path recorded at admission is a release requirement rather than a convenience. Cold retrieval is acceptable here because audit and replay tolerate delay, while the interactive path is held strictly to tier two.

**Industrial and field operations**: Connectivity is intermittent and the interactive latency budget is hard, so tier one is provisioned generously at the edge and tier two access is treated as optional rather than assured. Degradation is declared rather than hidden: a request served without warm recall reports lexical-only or cold-pending rather than presenting a partial result as complete. Movement runs opportunistically during connected windows, and the movement cap protects the connection budget rather than the storage budget.

**Legal discovery and archival research**: The corpus is dominated by tier three, reuse is rare, and exactness is non-negotiable. Summarisation is confined to a warm catalogue that carries identifiers, time ranges, sensitivity, retention, content hash, and object location, while bodies remain in the archive unsummarised, because a summary is never the only surviving representation of a contract, a chronology, or a numerical claim. Cold restore is planned and batched against a declared restore window, and a truthful pending outcome is preferred over an interactive call that blocks.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small corpora and low reuse**: Collapse to 2 tiers, a resident core and one durable store, retaining canonical versioning, invalidation, and the deletion path. Movement overhead above 10 percent at this scale indicates the entry gate should have refused the hierarchy.
- **High-risk or regulated work**: Retain every tier, raise the durability requirement to at least 2 verified copies before any eviction, bind the approval gate before every eviction of a retention-classed record, and treat the movement log and the deletion register as deliverables rather than diagnostics.
- **Strict interactive latency**: Shorten the cold path rather than removing tiers: keep a warm catalogue so discovery never reads cold bodies, prefetch from predictable workflows, and declare a pending outcome rather than blocking. Removing a tier removes recall; shortening its path preserves it.
- **Very large corpora**: Split tier two into a fast serving layer and a capacity layer with distinct contracts rather than over-provisioning one, and size the split from the measured reuse distribution rather than from the record count.
- **Multi-principal deployments**: Partition capacity, cache namespaces, and index namespaces by security scope, include the scope in every cache key, apply per-principal quotas so one principal cannot evict another's working set, and treat cross-scope reuse as a defect regardless of the cost saving it produces.

***

## V. Limitations and Considerations

**Thresholds here are deployment defaults, not measured constants**: Every numeric bound in this guide, including the 0.20 hysteresis gap, the 5 percent thrash rate, the 0.30 forecast weight cap, and the 70 and 85 percent watermarks, was chosen to be operable on first deployment rather than derived from a universal property of memory systems. The consequence is that a deployment inheriting them uncritically will mistune its hierarchy in one direction or the other. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute thresholds per workload class against observed access distributions before the defaults are treated as settled.

**Movement metrics depend entirely on their windows**: Promotion precision, demotion regret, thrash rate, and movement overhead change substantially with the horizon and window chosen, and a favourable window can conceal an unstable hierarchy. The consequence is that figures compared across differing windows are not comparable and can license the wrong correction. The mitigation is the reporting rule in Step 5.1 and Section III.D, which rejects any movement figure not carrying its boundary and its window.

**The relevance forecast is an estimate the system cannot verify in advance**: The model tier predicts near-term need without knowing the future access pattern, and its calibration drifts with model version, prompt, and workload. The consequence is that an uncapped forecast would systematically promote what the model finds salient rather than what the task will use. The mitigation is the 0.30 weight cap, the requirement that the deterministic tier hold authority in every hybrid decision, and the forecaster calibration rule that lowers the cap further in any class whose calibration gap exceeds 20 percentage points.

**Summarisation trades recoverability for capacity, irreversibly**: Compaction reduces tokens by discarding material that the answer-preservation gate did not think to test for, and repeated compaction compounds the loss while producing increasingly confident prose. The consequence is that a hierarchy relying on summarisation as its primary reclamation mode will lose exceptions, minority cases, and uncertainty without any visible error. The mitigation is the reclamation-mode rule in Section III.A, which prefers eviction where content is cheaply re-fetchable and offload where exact bytes must survive, together with the per-slice answer-preservation gate that blocks a compaction on any failing slice.

**The resident core is the highest-value attack surface**: Content promoted into tier zero is repeatedly trusted and can influence tool selection, so an attacker who can drive access frequency or supply plausible content can convert untrusted data into a high-authority instruction. The consequence is that a purely popularity-driven promotion policy is exploitable by construction. The mitigation is the hard block on untrusted-source promotion into tier zero without independent evidence or recorded review, the separation of data from policy scope, and the auditable, reversible treatment of every core edit.

**Erasure is never fully verifiable across backups**: Tombstone propagation covers online serving routes, but backups retain deleted content until their scheduled purge, and a restore can reintroduce it. The consequence is that a deletion reported as complete may be complete only on the paths that were tested. The mitigation is the explicit backup residual register with purge dates and exception codes, the requirement that every restore replay tombstones before serving, and the reporting of deletion completeness against tested routes rather than as an absolute claim.

**Structural conformance is not a justified hierarchy**: A deployment can satisfy every checkpoint in this guide and still operate tiers that no workload needs, paying synchronisation and movement cost for a latency saving it never measured. The consequence is a well-instrumented system that is more expensive than the flat store it replaced. The mitigation is Phase 7 and Checkpoint 7, which retire any tier that improves no declared gate against the flat and long-context baselines.

***

## VI. Conclusion and Summary

A production memory hierarchy is a controlled working-set machine, not a stack of databases. Its value comes from a small number of explicit, countable decisions: how many tiers exist and what each one guarantees, what is admitted and where it first lands, what numeric trigger moves a record up and what different trigger moves it down, what proves a record survives its eviction, and what signature says the whole arrangement is spending its budget on movement rather than on work. A system making those decisions explicitly and recording them can be tuned; a system leaving them implicit will oscillate, stale, or quietly lose records, and will have no evidence with which to diagnose any of the three.

The partition between execution tiers is what keeps such a system honest. Capacity accounting, movement execution, durability verification, access counting, and thrash detection belong to deterministic software because they demand exactness and auditability; the forecast of near-term need belongs to model inference because no rule covers it. The forecast informs a promotion score and never overrides a capacity bound, and the eviction of a last durable copy is never a model decision at all. A team introducing a hierarchy should begin with one canonical versioned store, a bounded resident core, one durable tier, simple replacement, and complete movement telemetry, and should add each further tier, index, cache, or summary layer only when it improves a declared gate against the simpler design it replaces.

**Key Success Factors**:

- **One canonical record, many rebuildable copies**: Every tier copy carries the canonical version it derives from, no derived copy is edited independently, and one source correction invalidates every ancestor built from it.
- **Separated entry and exit thresholds**: Promotion and demotion never share a threshold; the gap, the minimum residence, and the cooldown are what prevent oscillation, and a hierarchy without all three will thrash.
- **Durability proven before capacity is reclaimed**: No eviction executes without a hash-verified surviving copy at a qualifying durability class, and any operation that would remove the last durable copy is deletion under authorisation, not eviction under pressure.
- **Deterministic authority over model forecast**: Model judgement contributes a bounded, recorded component to a promotion score and never overrides a capacity, residency, sensitivity, or durability bound.
- **Thrashing measured, not assumed**: The thrash signature is computed from the append-only movement log with its boundary and window stated, and the response changes a threshold, a residency, or a capacity rather than merely slowing the scheduler.
- **Justified against a simpler design**: Every retained tier cites a declared gate it improves against a flat store and a long-context alternative measured on the same frozen corpus.

By following this guide, AI agents can hold a large and growing body of state across storage layers that differ in cost and latency, move records between them on triggers a reviewer can audit, and prove that the arrangement pays for itself without losing, staling, or irrecoverably compacting what it was built to keep.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. Entries marked as retrieved were located during this conversion's own research and are noted as such.

**Corpus pointers**:

- `Hierarchical Memory for AI Agents: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the four-tier service-property decomposition, the prompt-budget precedence order, the separation of admission from replacement, the hysteresis controls, the paging and compaction treatment, the cross-tier consistency protocol, the placement and movement field inventory, the failure-mode catalogue, and the baseline comparison requirement. It carries inline citations to primary literature and vendor documentation on virtual context management, cache admission and replacement, vector index trade-offs, prompt caching, archival lifecycle, erasure obligations, and long-context evaluation; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — companion guidance on the overall memory lifecycle, applicable to the record semantics that Phase 2 admits and Phase 6 versions.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — companion guidance on session-scoped state, applicable to the tier one contract in Step 1.1 and to the resumption checkpoint in Phase 2.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on summarisation and consolidation, applicable to the compaction answer-preservation gate in Step 7.1.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — companion guidance on event-structured records, whose cognitive type remains independent of the serving tier assigned in Phase 2.
- `advanced_task_guides/memory-management/guide_AttentionBasedMemoryRetrieval.md` — companion guidance on retrieval scoring, applicable to the relevance components entering the promotion score in Step 3.1.
- `advanced_task_guides/memory-management/guide_LatentMemoryNetworks.md` — companion guidance on retrieval embeddings, index generations, and bounded latent compression over evidence that still survives; it excludes weight-level and learned-module methods. Relevant to the vector-index trade-offs referenced in the tier two contract.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — owns retention policy, the separation of utility forgetting from obligation erasure, and the proof that a reduction occurred. Capacity-driven demotion and eviction under this guide are not forgetting, and a record that an obligation requires removed leaves the hierarchy by that guide's path rather than by tier policy.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — owns the operation contract for a single read and a single write, including gate ordering and terminal states; this guide owns where a record sits and when it moves, not the mechanics of the operation that reaches it.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the movement log and placement records in Phase 1 and Phase 3.
- `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guidance on monitoring under constraint, applicable to the thrash detection rules in Phase 5.
- `advanced_task_guides/design-architecture/guide_SchemaFlexibilityandEvolution.md` — companion guidance on schema evolution, applicable to the generation cutover protocol in Step 6.2.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control loops and value-of-computation gating, applicable to the entry gate in Section 1.4.

**External references**: The numbering below is the numbering used by the inline markers in Sections I and II. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Virtual context management and long-context behaviour*

1. Packer and colleagues, *MemGPT: Towards LLMs as Operating Systems* — https://arxiv.org/abs/2310.08560
2. Liu and colleagues, *Lost in the Middle: How Language Models Use Long Contexts* — https://arxiv.org/abs/2307.03172

*Prompt caching and serialization order*

3. OpenAI, *Prompt caching* — https://platform.openai.com/docs/guides/prompt-caching
4. Anthropic, *Prompt caching* — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
5. Google Cloud, *Vertex AI context caching overview* — https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview

*Cache admission, replacement, and offline bounds*

6. Einziger and colleagues, *TinyLFU: A Highly Efficient Cache Admission Policy* — https://arxiv.org/abs/1512.00727
7. Megiddo and Modha, *ARC: A Self-Tuning, Low Overhead Replacement Cache* — https://www.usenix.org/conference/fast-03/arc-self-tuning-low-overhead-replacement-cache
8. Belady, Nelson and Shedler, *An Anomaly in Space-Time Characteristics of Certain Programs Running in a Paging Machine* — https://dl.acm.org/doi/10.1145/321686.321687
9. Redis, *Key eviction policies* — https://redis.io/docs/latest/develop/reference/eviction/

*Erasure and retention obligations*

10. UK Information Commissioner's Office, *Right to erasure* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/

*Serving indexes and storage tiers*

11. Faiss project, *Faiss indexes* — https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
12. Microsoft, *DiskANN* — https://github.com/microsoft/DiskANN
13. Amazon Web Services, *S3 object lifecycle management* — https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
14. Amazon Web Services, *S3 Glacier two-step archive retrieval* — https://docs.aws.amazon.com/amazonglacier/latest/dev/downloading-an-archive-two-steps.html

*Hierarchical summarisation and tiered agent memory systems*

15. Sarthi and colleagues, *RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval* — https://arxiv.org/abs/2401.18059
16. *MemTree* — https://arxiv.org/abs/2410.14052
17. *H-MEM* — https://arxiv.org/html/2507.22925v1
18. *MemForest* — https://arxiv.org/html/2605.23986v1
19. *Mem0* — https://arxiv.org/abs/2504.19413

*Framework and protocol surfaces for tiered memory*

20. LangChain, *LangGraph persistence* — https://docs.langchain.com/oss/python/langgraph/persistence
21. Letta, *Context hierarchy* — https://docs.letta.com/v1-sdk/memory/context-hierarchy
22. Letta, *Memory blocks* — https://docs.letta.com/v1-sdk/memory/memory-blocks
23. LlamaIndex, *Agent memory* — https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/
24. Model Context Protocol, *Resources* — https://modelcontextprotocol.io/specification/2025-06-18/server/resources
25. OpenTelemetry, *GenAI semantic conventions* — https://opentelemetry.io/docs/specs/semconv/gen-ai/

*Serving-memory mechanisms named as out of agent-layer scope in Section 1.2*

26. Kwon and colleagues, *Efficient Memory Management for Large Language Model Serving with PagedAttention* — https://arxiv.org/abs/2309.06180
27. vLLM, *Automatic prefix caching* — https://docs.vllm.ai/en/latest/features/automatic_prefix_caching/

*Component benchmarks for long-horizon memory*

28. *LongMemEval* — https://arxiv.org/abs/2410.10813
29. *LoCoMo* — https://arxiv.org/abs/2402.17753
30. *MemoryAgentBench* — https://arxiv.org/abs/2507.05257

*Retrieved during this conversion*

31. Anthropic, *Prompt caching, Claude platform documentation* — https://platform.claude.com/docs/en/build-with-claude/prompt-caching (retrieved during conversion; confirms cache breakpoints, the fixed tools then system then messages prefix order, and the five-minute default lifetime with an extended one-hour option)
32. Maruf and colleagues, *TPP: Transparent Page Placement for CXL-Enabled Tiered-Memory* — https://symbioticlab.org/publications/files/tpp:asplos23/tpp-asplos23.pdf (retrieved during conversion; source of the general finding that hysteresis applied to promotion candidates substantially reduces promotion rate in tiered systems)

