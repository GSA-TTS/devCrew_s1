# Context Lifecycle Management

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Context lifecycle management constitutes the task family of governing a context across time: the ordered stages a run's context passes through from declaration to teardown, the conditions that permit each transition, and the artifacts each stage must produce before the next may begin. This guide provides AI agents with a structured protocol for six declared stages, an initialisation discipline that separates what is established once per run from what is rebuilt on every call, a turn-level mutation contract distinguishing what is appended from what is replaced and what is explicitly invalidated, a boundary-crossing procedure requiring a handoff record and a deterministic reconstruction test before the outgoing window may be discarded, and a teardown procedure requiring verified persistence before any live element is released. It fixes the execution tier partition so that stage transitions, prefix stability, handoff verification, invalidation bookkeeping, and persistence checks remain deterministic while relevance judgement and summary drafting remain with the model. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that a run outliving any single context window loses no binding state at the point where the window is rebuilt.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Context lifecycle**: The ordered sequence of stages a run's context passes through from the moment its contract is declared until its final element is persisted or released, together with the conditions governing each transition between stages. The lifecycle is the time dimension of context management: it owns sequence and transition, not the individual operations performed within a stage.

**Run**: One bounded unit of work with a single objective, a single authority scope, and a single terminal state. A run may span many context windows, many processes, and many agents; its identity is stable across all of them.

**Turn**: One model call within a run, together with the assembly that preceded it and the state commit that followed it. A turn is the smallest unit at which content is appended, replaced, or invalidated.

**Context window**: The token sequence accepted by one model call. It is a transport, not a store. This definition is adopted unchanged from the working-memory and context-management guidance and is load-bearing throughout.

**Durable store**: Any location outside the window that survives the call: a checkpoint, a file, an artifact store, a relational or vector index, a graph, an episodic or semantic memory store, or an event log.

**Lifecycle stage**: A named condition of the context, carrying a declared entry condition, a declared artifact it must produce, and a declared terminating condition. A stage without all three is a narrative label, not a stage.

**Stage transition**: The move from one stage to the next, permitted only where the outgoing stage's artifact exists, validates, and satisfies the incoming stage's entry condition. Transitions are recorded events, never inferred from elapsed time or from apparent progress.

**Epoch**: One continuous span of a run served by a single stable prefix. An epoch begins at initialisation or reinitialisation and ends when the prefix changes or the window is discarded. A run comprises one or more epochs sharing a run identifier and linked by epoch lineage.

**Initialisation record**: The once-per-epoch artifact naming the resolved identity, the pinned policy and prompt versions, the tool manifest and its serialization order, the model and tokenizer identifiers, the partitioned budget, the durable store handles, and the prefix hash.

**Stable prefix**: The leading region of the assembled context package whose bytes do not change for the duration of an epoch: policy and instructions, tool definitions in a fixed order, and static reference material. Its stability is the agent-layer surrogate for physical prefix reuse.

**Volatile suffix**: The trailing region rebuilt on every turn from canonical state: the working-state projection, admitted evidence, recent turn pairs, and the current request.

**Turn delta**: The recorded difference one turn makes to the context, expressed as three disjoint sets: appended units, replaced units, and invalidated units. A turn without a recorded delta is an accounting defect.

**Invalidation**: The explicit removal of a unit from eligibility, executed at the turn in which its invalidating condition is detected, carrying a reason code and a tombstone in the lifecycle ledger. Content leaving the window through eviction, truncation, or compaction is not invalidated, because the unit remains authoritative in canonical state and re-enters at the next assembly.

**Supersession**: The replacement of one unit by a newer authoritative version of the same unit. The superseded version leaves the working set immediately and survives only as lineage in a durable store. The term is adopted unchanged from the working-memory guidance.

**Context boundary**: Any point at which the window is discarded and reconstructed: a compaction, a session end, a sub-agent dispatch, a model or provider switch, or a process restart. The term is adopted unchanged from the context-management guidance.

**Boundary trigger**: The deterministic condition that declares a boundary before one is forced: a measured budget threshold, a projected overflow within the next turn, a policy or tool-schema change invalidating the prefix, a scheduled suspension, or an authority change.

**Handoff record**: The bounded state package written at every context boundary, carrying the contract version, the protected set, the durable-store references, the open questions, the remaining budget, and the exact next decision, and requiring explicit acknowledgement by the receiver. The term and its content classes are adopted from the working-memory guidance and extended here with lifecycle fields.

**Reconstruction test**: The deterministic check that a handoff record alone is sufficient to rebuild working state, performed by constructing a candidate state in a process with no access to the outgoing window and comparing it field by field against the canonical state at the boundary. A boundary crossing is not permitted until this test passes.

**Protected atom**: A content element that must survive every eviction, compaction, truncation, and boundary crossing without loss: the task objective, the success criteria, the standing and safety constraints, the current plan step, the latest value of every open variable, the unresolved error state, the outstanding approvals, and the side-effect ledger. The membership list is adopted unchanged from the working-memory guidance.

**Lifecycle ledger**: The append-only record of every stage transition, initialisation, turn delta, invalidation, boundary crossing, and teardown action, keyed by run, epoch, and turn, and carrying a reason code drawn from a closed vocabulary.

**Teardown**: The terminal stage in which every live element is classified as persist, discard, or erase; every persist target is verified as durably readable; and only then is any discard executed.

**Persistence manifest**: The teardown artifact listing each element to be persisted with its destination store, its identifier, its content hash, its retention expiry, and its verification verdict.

**Freshness**: The declared interval during which an observation may be treated as current, expressed as an observation timestamp and an expiry timestamp. Use past expiry is a staleness event, not a judgement call.

**Trust class**: The provenance-derived label attached to every unit naming the authority of its source. Trust class determines which region a unit may occupy and whether it may instruct; it is never inferred from position in the window.

**Reason code**: A normalised categorical label recorded with every transition, invalidation, boundary, and teardown action, drawn from a closed vocabulary so that lifecycle behaviour is analysable without reading prose logs.

### 1.2 What This Guide Owns and What It Defers

**The time dimension**: This guide owns the sequence a context passes through over a run's lifetime and the transitions between its stages. The pattern siblings in this category own the individual operations available at any moment: writing content out of the window, selecting content into it, compressing what remains, and isolating work into separate windows. The category umbrella owns the choice among those four families under a partitioned budget at a single point in time. None of them owns when the context is established, what changes at each turn, what happens at the point where the window is rebuilt, or what must be true before a completed run releases its state. Those questions are ordered in time, and the answers are transitions rather than operations.

**Why the sequence is a separate concern**: A system can perform every operation correctly and still lose the run. Compaction executed at the right threshold with a valid preservation manifest still destroys a run whose handoff omitted the side-effect ledger, because the reconstructed agent repeats a committed effect. A correct selection policy still produces a run that cannot resume, because the durable references for evicted content were never written. The operations are judged against the current call; the lifecycle is judged against the run.

**What this guide does not restate**: The internal procedure of eviction, ranking, summarisation, delegation, and budget partitioning is deferred to the siblings named in Section VII. Where a stage requires one of those operations, this guide names the operation, states the condition under which the stage invokes it, and states what the stage requires of its output; it does not specify how the operation is performed.

**The agent-layer boundary and two re-scoped mechanisms**: Two mechanisms discussed in the originating prose sit below the agent layer and are not executable through any runtime tool, API, or script. The first is the serving-side key-value cache that physically produces prefix reuse; its block allocation, fragmentation, and eviction are owned by the model server, and no application agent can read or direct them. The executable form carried here is prefix stability discipline: a fixed assembly order, a prefix frozen and hashed for the duration of an epoch, an epoch version incremented on any prefix change, and provider-reported cache-read and cache-write token counts as the only observable evidence of reuse. The second is provider-managed conversation state and server-side compaction, whose retained items are opaque to the application and carry the provider's retention semantics rather than the application's. The executable form carried here is an application-owned handoff record subjected to a deterministic reconstruction test, with any provider continuation token treated as a latency and cost optimisation that is never the run's record. Retention behaviour differs by object type and by account configuration on at least one major provider, so agents must read the current controls for the endpoint in use rather than assuming one retention rule applies across a provider's surface [1][2][6].

**Provider mechanisms are stage participants, not stage owners**: Server-side compaction, tool-result clearing, connection-resumption handles, and provider context caching each participate in one or more transitions [3][4][5][9]. Each is admissible where its retention, inspection, deletion, and availability behaviour satisfies the run's contract. None of them discharges the obligation to write a handoff record, to verify reconstruction, or to verify persistence before discard, because none of them is inspectable by the application that must answer for the run. Published harness engineering supports the same separation: summarising the window in place proved insufficient for very long runs, and the reported remedy was a full context reset in which the window is cleared entirely and a fresh agent rebuilds from a structured handoff artifact carrying the prior state and the next steps [14][26]. That is the transition this guide specifies, with the addition of a deterministic gate on the discard.

### 1.3 The Six Lifecycle Stages and Their Transition Conditions

A run's context occupies exactly one stage at any moment. Every transition is recorded in the lifecycle ledger with its trigger, its evidence, and a reason code. A transition attempted without its entry condition is refused, and the refusal is itself a ledger event; silent stage drift is the failure this table exists to prevent.

**Lifecycle stage contract**:

| Stage | Entry condition | Artifact produced | Terminating condition |
| :-- | :-- | :-- | :-- |
| Declared | A task contract and a context contract exist, both validated, with terminal states enumerated | Lifecycle stage contract naming stages, triggers, terminal states, and retention classes | Initialisation begins under a resolved identity |
| Initialised | Stage contract validates; identity, policy version, tool manifest, model, and tokenizer all resolve | Initialisation record and a frozen, hashed stable prefix bound to an epoch identifier | The first volatile suffix is assembled against the frozen prefix |
| Active | Prefix hash matches the initialisation record; budget ledger is open; canonical state object is loadable | Per-turn context packages and one recorded turn delta per turn | A boundary trigger fires, or a declared terminal condition is reached |
| Crossing | A boundary trigger fired and was recorded; the outgoing window is still intact | Handoff record and a reconstruction verdict | The reconstruction test passes and the outgoing window is discarded |
| Reinitialised | A passing reconstruction verdict and a receiver acknowledgement of the state and schema versions | New initialisation record carrying epoch lineage to the prior epoch | The first post-boundary turn is assembled, returning the run to Active |
| Terminated | A declared terminal condition reached, or teardown ordered by an authority | Persistence manifest with a verification verdict per target, and a teardown record | Every persist target verifies and every discard target is released |

**Stage rules that bind every deployment**: A run enters Active only through Initialised or Reinitialised, never directly. A run leaves Active only through Crossing or Terminated, never by exhausting a window. Crossing never terminates by timeout: an expired boundary budget escalates rather than discarding an unverified window. Terminated is the only stage permitted to release state, and it may release nothing before its verification verdicts are complete.

**Suspension is a sub-state of Active, not a stage**: A run awaiting a human decision, an external event, or a scheduled resume remains Active with a suspension marker, a resume deadline, and a mandatory checkpoint written before the wait begins. Where the suspension exceeds the declared window-retention interval or crosses a process restart, the run transitions to Crossing and rebuilds through a handoff rather than assuming the window survived. Treating a resumed transport connection as evidence that business state is current is the specific error this rule prevents [5].

**Terminal states**: A run terminates as completed, cancelled, failed-recoverable, failed-terminal, expired, or teardown-incomplete. Teardown-incomplete is a real terminal state, not a failure to reach one: it records that persistence verification did not complete, that no discard was executed, and that an owner holds the remainder. A run that cannot verify persistence must terminate here rather than discarding on an assumption.

### 1.4 Execution Tier Partition

Context lifecycle management is a hybrid capability, and its production failures concentrate at two misassignments: allowing a model to decide that a boundary crossing is safe, and allowing a model to decide that a unit is no longer needed. The deterministic tier owns stage transitions and their conditions, assembly order and prefix stability, handoff record construction and verification, invalidation bookkeeping, and teardown persistence checks, because each requires exactness, reproducibility, and auditability that inference cannot supply. The model tier owns judging what remains relevant across a boundary and drafting the summary fields of the handoff record, because deciding what an open-vocabulary body of work means for the next epoch is covered by no rule. The hybrid tier is the handoff between them, and software holds authority wherever the two disagree.

**The binding rule**: A boundary crossing is not permitted until the deterministic reconstruction test passes. A model assertion that the handoff is sufficient is an input to drafting, never a verdict. The outgoing window is the only remaining copy of anything the handoff omitted, so discarding it on an unverified judgement converts a recoverable omission into permanent loss.

**Tier ownership by artifact**:

| Artifact | Owning tier | Authority where the tiers disagree |
| :-- | :-- | :-- |
| Stage identity, transition conditions, and the lifecycle ledger | Deterministic | Deterministic; a transition without its entry condition is refused regardless of model objection |
| Initialisation record, pinned versions, and prefix hash | Deterministic | Deterministic; a prefix whose hash differs from the record ends the epoch, it does not continue it |
| Assembly order and the prefix and suffix split | Deterministic | Deterministic; ordering is policy, not a model preference |
| Turn delta classification and the append, replace, and invalidate sets | Deterministic | Deterministic; a unit is invalidated by a recorded condition, never by absence from an assembly |
| Supersession lineage, tombstones, and invalidation reason codes | Deterministic | Deterministic; a model claim that a value is current is not evidence |
| Boundary trigger evaluation and projected-overflow arithmetic | Deterministic | Deterministic; a model estimate of remaining budget is advisory only |
| Handoff record schema, required content classes, and version fields | Deterministic | Deterministic; a handoff missing a required class is rejected, not accepted with a note |
| Reconstruction test execution and its pass or fail verdict | Deterministic | Deterministic; the verdict gates the discard absolutely |
| Persistence manifest, read-back verification, and discard release | Deterministic | Deterministic; an unverified target is never discarded |
| Relevance of accumulated work to the next epoch | Model | Model proposes the carry-forward set; the reconstruction test still binds |
| Summary and narrative fields of the handoff record | Model | Model drafts; deterministic protected-atom and reference checks decide use |
| Interpretation of an observation as superseding an earlier one | Model | Model proposes; the supersession is committed only against a schema-validated identity |
| Selection of the carry-forward evidence set at a boundary | Hybrid | Model nominates; the budget bound and the reconstruction test decide |
| Classification of a live element as persist, discard, or erase | Hybrid | Model nominates promotion candidates; the receiving store's write policy and retention class decide |

**What the deterministic tier rejects unconditionally**: a stage transition whose entry condition is unmet; an assembly whose prefix hash differs from the epoch's initialisation record without an epoch increment; a turn that commits state without recording a delta; an invalidation without a reason code from the closed vocabulary; a handoff record missing a required content class or either version field; a discard of an outgoing window before a passing reconstruction verdict; a persist target released before read-back verification; and a teardown that discards while any verification verdict is outstanding.

**What the model tier may never decide alone**: whether a boundary has been reached; whether a handoff is sufficient; whether a unit is still fresh; whether an effect already committed; whether a superseded value may remain; whether the run may terminate; and whether an element has been persisted. Each has a deterministic answer available at runtime, and delegating it to inference converts a checkable fact into an opinion.

### 1.5 Lifecycle Operating Defaults

The values below are deployment defaults chosen to be operable before any measurement exists, not measured constants. Section V records this limitation, and Step 6.3 obliges each deployment to recompute them against observed runs. Every threshold names a consequence of breach, and a threshold with no consequence is a defect.

**Lifecycle operating defaults**:

| Control | Default threshold | Consequence of breach |
| :-- | :-- | :-- |
| Boundary trigger on measured occupancy | Assembled input at or above 70 percent of the input budget | Boundary declared and Crossing entered; at or above 85 percent the turn fails closed rather than assembling |
| Boundary trigger on projected overflow | Projected next-turn growth, taken as the 95th percentile turn delta over the last 10 turns, would exceed the remaining budget | Boundary declared this turn rather than next; a forced boundary is recorded as a lead-time defect |
| Prefix share of the input budget | No more than 25 percent | Externalize static reference material behind references; above 35 percent initialisation fails closed |
| Prefix rebuilds per run | No more than 2 | A third rebuild halts the run for contract review rather than opening another epoch |
| Epochs per run | No more than 6 | The seventh boundary escalates for scope review; the run is not silently continued |
| Handoff record size | No more than 5 percent of the input budget | Move content behind durable references until the bound is met; a handoff that cannot meet it escalates |
| Protected atoms preserved across a boundary | Exactly 100 percent, verified by hash over the normalised protected set | Any shortfall fails the reconstruction test and blocks the discard |
| Unresolved durable references in a handoff | Exactly 0 | Any occurrence fails the reconstruction test and blocks the discard |
| Handoff amendments per boundary | No more than 2 | A third failing verdict escalates to a named owner; the window is retained meanwhile |
| Invalidation latency | Removed from the next assembled package, within 1 turn of detection | A unit surviving 2 assemblies after its invalidating condition is recorded as a staleness event |
| Turns with an unrecorded delta | Exactly 0 | Any occurrence blocks release of the configuration |
| Duplicate irreversible effects across a boundary | Exactly 0 | Any occurrence blocks release and triggers reconciliation review |
| Persist targets verified before any discard | Exactly 100 percent | Any shortfall terminates the run as teardown-incomplete rather than discarding |
| Persistence verification attempts per target | 3 attempts, 30 seconds each | Exhaustion terminates the run as teardown-incomplete with the target named |
| Checkpoint interval within Active | Every irreversible effect boundary and every 10 turns | A missed effect-boundary checkpoint blocks the effect from committing |

***

## II. Operational Framework: A Staged Context Lifecycle With Verified Boundary Crossings

The framework produces one governed lifecycle per run: a stage contract with transition conditions, an initialisation record binding a frozen prefix to an epoch, a per-turn mutation contract, an invalidation discipline with explicit tombstones, a boundary procedure gated on a deterministic reconstruction test, and a teardown gated on verified persistence. Phase 1 produces the Declared stage. Phase 2 produces the Initialised stage. Phases 3 and 4 repeat once per turn throughout the Active stage. Phase 5 produces the Crossing and Reinitialised stages and returns the run to Active. Phase 6 produces the Terminated stage and closes the run.

### Phase 1: Lifecycle Declaration and Stage Contract

**Objective**: Fix the stage set, the transition conditions, the terminal states, and the ledger schema before any context is allocated, so that stage membership is checkable rather than inferred.

**Owning tier**: Deterministic; the stage contract, the transition conditions, and the ledger schema are software artifacts, and no model output determines whether a stage has been entered.

#### Step 1.1: Declare the Stage Set and Its Transition Conditions

**Required Actions**:

- Adopt the six stages in Section 1.3 or declare a superset, and record for each stage its entry condition, the artifact it must produce, and its terminating condition.
- State each transition as a predicate over observable values: a hash comparison, a count, a token measurement, a version match, or a verification verdict, never a qualitative judgement.
- Name the single component authorised to record each transition, and prohibit any other component from writing a stage change.
- Declare the closed reason-code vocabulary covering transition, invalidation, boundary, and teardown events, and reject any event carrying a code outside it.
- Declare the refusal behaviour for a transition attempted without its entry condition, and record the refusal as a ledger event rather than discarding it.

**Required Outputs**:

- A stage contract with entry condition, produced artifact, and terminating condition populated for every stage.
- A transition predicate per transition, each evaluable from observable values alone.
- A closed reason-code vocabulary with a named owner.

**Quality Checkpoints**:

- Every stage carries all three contract elements; a stage missing one is rejected before the run opens.
- Every transition predicate evaluates without model inference; a predicate requiring judgement is rewritten or escalated.
- The Active stage is reachable only from Initialised and Reinitialised, and exitable only to Crossing and Terminated.

***

#### Step 1.2: Establish Run Identity, Epoch Lineage, and the Lifecycle Ledger

**Required Actions**:

- Assign a run identifier stable across every window, process, and agent participating in the run, and derive epoch identifiers from it so lineage is reconstructable from an identifier alone.
- Declare the ledger schema carrying run, epoch, turn, stage, transition, trigger, evidence reference, reason code, actor, and timestamp for every event.
- Make the ledger append-only, and require that a correction is expressed as a superseding event rather than as an edit to an existing one.
- Bind tenant scope, authority scope, and retention class to the run identifier at creation, and prohibit any later component from sourcing those fields from model output.
- Record content references and hashes in the ledger rather than payloads, and prohibit reasoning content, raw secrets, and full prompts from every ledger field.

**Required Outputs**:

- A run identifier with derived epoch identifiers and a stated lineage rule.
- A ledger schema with all ten event fields declared and an append-only guarantee.
- A binding record naming tenant scope, authority scope, and retention class.

**Quality Checkpoints**:

- Epoch lineage reconstructs from identifiers alone, without consulting any window.
- No ledger field admits reasoning content, a raw secret, or a full prompt payload.
- Tenant and authority scope are sourced from trusted configuration; a value from model output is rejected.

***

#### Step 1.3: Declare Terminal States and the Teardown Obligation

**Required Actions**:

- Enumerate the terminal states the run may reach, including teardown-incomplete, and state the observable condition that selects each.
- Classify every state class the run will create as persist, discard, or erase in advance, and name for each persist class its destination store, its retention expiry, and its verification method.
- State the discard gate: no element of any class is released before every persist target in the run's manifest carries a passing verification verdict.
- Declare the ownership of each erase class, its propagation targets, and the evidence that closes it, so that a deletion obligation is not discovered at teardown [7][8].
- Set the retention expiry at declaration time for every persist class rather than deferring retention to a later cleanup process.

**Required Outputs**:

- A terminal state list with a selecting condition per state.
- A state class inventory with a persist, discard, or erase disposition and a destination for every persist class.
- A discard gate statement and a retention expiry per persist class.

**Quality Checkpoints**:

- Every state class the run creates appears in the inventory with a disposition; an unclassified class blocks the run from opening.
- Every persist class carries a destination, an expiry, and a verification method.
- Teardown-incomplete is present as a terminal state with its own selecting condition.

***

### Phase 2: Initialisation and Stable Prefix Construction

**Objective**: Establish once per epoch everything that does not change within it, freeze it in a fixed order, and hash it, so that per-turn assembly rebuilds only the volatile suffix.

**Owning tier**: Deterministic; version pinning, serialization order, hashing, and budget partitioning are software operations, and a prefix is frozen by comparison against a recorded hash rather than by intention.

#### Step 2.1: Establish the Once-Per-Epoch Initialisation Record

**Required Actions**:

- Resolve identity, tenant scope, and authority outside the model, and fail closed where any of the three is unresolved rather than proceeding with a default.
- Pin the policy release, instruction version, tool manifest and its serialization order, model identifier, tokenizer identifier, schema version, and retention class, and record each version in the initialisation record.
- Compute the input budget and its partitions once per epoch, subtracting the output reserve and operational headroom before partitioning, and open the budget ledger against those figures.
- Open handles to every durable store the epoch will read or write, and verify each is reachable and writable before the first turn rather than at first use.
- Record which elements are established once per epoch and which are rebuilt per turn, so that the cost of a turn is attributable and a per-turn rebuild of a per-epoch element is detectable.

**Initialisation Record Template**:

```
RUN_ID:
EPOCH_ID:
EPOCH_PARENT:            null for the first epoch, else the prior EPOCH_ID
IDENTITY:                tenant, principal, authority scope
PINNED_VERSIONS:         policy, instructions, tool manifest, schema, retention class
MODEL:                   model identifier and tokenizer identifier
BUDGET:                  window capacity, output reserve, headroom, per-partition maxima
DURABLE_STORES:          handle, reachability verdict, writability verdict per store
PREFIX_HASH:             hash over the serialized stable prefix
PREFIX_TOKENS:           tokenizer-exact count
PER_EPOCH_ELEMENTS:      enumerated
PER_TURN_ELEMENTS:       enumerated
CREATED_AT:
EXPIRES_AT:
REASONING_CONTENT:       PROHIBITED
```

**Required Outputs**:

- An initialisation record with every field populated and no unresolved version.
- A budget ledger opened against the epoch's partition maxima.
- A durable store readiness verdict per store.

**Quality Checkpoints**:

- Every behaviour-affecting version is pinned; an unpinned version halts initialisation rather than defaulting.
- Identity, tenant scope, and authority all resolve before any content is assembled; an unresolved value fails closed.
- Every durable store the epoch will use was verified reachable and writable before the first turn.

***

#### Step 2.2: Construct the Stable Prefix in a Fixed Order

**Required Actions**:

- Place content in descending order of stability: policy and standing instructions first, then tool definitions in a fixed declared order, then static reference material, then the volatile suffix.
- Exclude from the prefix every element that changes within the epoch: timestamps, turn counters, budget figures, working-state projections, retrieved evidence, and the current request.
- Serialize the prefix with canonical field ordering, a declared encoding, and stable key ordering, so that a semantically identical prefix is byte-identical across turns.
- Hash the serialized prefix, record the hash and its tokenizer-exact token count in the initialisation record, and compare the hash before every subsequent assembly.
- Treat any required change to prefix content, tool set, tool order, or pinned version as the end of the epoch, increment the epoch, and write a new initialisation record rather than mutating the prefix in place.

**Required Outputs**:

- A serialized stable prefix in the declared order with a recorded hash and token count.
- An exclusion list naming the volatile elements kept out of the prefix.
- An epoch increment rule naming every change class that ends an epoch.

**Quality Checkpoints**:

- The prefix hash is identical across every turn of the epoch; a differing hash without an epoch increment is an assembly defect and halts the turn.
- No prefix element carries a timestamp, a counter, or any per-turn value.
- The prefix occupies no more than 25 percent of the input budget; above 35 percent initialisation fails closed and static material is externalized.

***

#### Step 2.3: Validate Initialisation and Fail Closed

**Required Actions**:

- Verify that the pinned schema version has a registered reader, that the policy signature validates, and that every declared tool resolves in the manifest.
- Recount the assembled prefix with the target model's tokenizer after serialization, and reject a count estimated from character length, whose token ratio varies by more than a factor of 3 across languages and modalities.
- Confirm that the output reserve and operational headroom were subtracted before partitioning and that no partition borrows against either.
- Confirm the clock, the retention expiry, and the tenant isolation of every store handle, and refuse to open the epoch where any check fails.
- Write the initialisation record and the stage transition into the ledger before the first assembly, so that a crash between initialisation and the first turn is recoverable.

**Required Outputs**:

- An initialisation validation verdict per check with a pass or fail result.
- A tokenizer-exact prefix token count recorded in the initialisation record.
- A ledger entry recording the transition into the Initialised stage.

**Quality Checkpoints**:

- Every validation check returned a verdict; an unrun check is treated as a failure, not as an absence of evidence.
- No epoch opened with an unresolved policy signature, an unregistered schema version, or an unreachable store.
- The transition into Initialised was recorded before the first turn assembled.

***

### Phase 3: Per-Turn Assembly and Mutation

**Objective**: Rebuild the volatile suffix from canonical state on every turn and record the exact difference the turn makes, so that accumulation across turns is accounted rather than incidental.

**Owning tier**: Deterministic for assembly, delta classification, and budget accounting; the model tier proposes state changes and the deterministic tier commits them.

#### Step 3.1: Rebuild the Volatile Suffix From Canonical State

**Required Actions**:

- Regenerate the volatile suffix on every turn from the canonical state object and its durable references, and never by editing the previous turn's serialized package.
- Verify the prefix hash against the initialisation record before appending the suffix, and halt the turn where it differs without a recorded epoch increment.
- Render only the latest value of every open variable, the current plan step, and the unresolved error state, so that superseded values are absent by construction rather than by later removal.
- Replace inline content above the declared size cap with a durable reference plus a precise excerpt, and record the reference identifier and content hash in the turn's assembly record.
- Recount the assembled package with the target model's tokenizer after serialization and before the call, and refuse to issue a call whose total exceeds the input budget.

**Required Outputs**:

- One assembled context package per turn with a recorded prefix hash and a tokenizer-exact total count.
- An assembly record naming every unit admitted, its partition, its trust class, and its source reference.
- A refusal verdict where the package exceeded the budget, carrying the per-partition ledger.

**Quality Checkpoints**:

- The suffix was regenerated from canonical state; a package derived by editing the prior serialization is rejected.
- No superseded value appears in the package, because the renderer emits latest values only.
- Every unit above the size cap appears as a reference and an excerpt, never as an inline payload.

***

#### Step 3.2: Classify Every Turn-Level Change as Append, Replace, or Invalidate

**Required Actions**:

- Classify every change the turn makes into exactly one of three disjoint sets, and record the counts and identifiers of all three in the turn delta.
- Append only content that is genuinely new and durable within the epoch: the incoming request, the model's committed output, new tool-result references, and new ledger events.
- Replace every projection whose latest value is the only correct rendering: open variable values, plan step statuses, budget figures, freshness tables, and the error state, so that a replaced unit does not appear twice.
- Invalidate on a detected condition, never on absence: supersession by an authoritative newer version, freshness expiry, source revocation, resolution of an open question, consumption of a single-use instruction, or completion of a tool-call pair whose result has been externalized.
- Refuse to commit a turn that records no delta, since an unrecorded delta makes accumulation unattributable and boundary projection unreliable.

**Turn mutation contract**:

| Change class | What it covers | Where the previous version goes | Recorded evidence |
| :-- | :-- | :-- | :-- |
| Append | Incoming request, committed model output, new tool-result reference, new ledger event | Retained; appended content is additive within the epoch | Unit identifier, partition, trust class, token cost |
| Replace | Open variable values, plan step status, budget figures, freshness table, error state | Removed from the next assembly; retained as lineage in the durable store | Prior version identifier, new version identifier, reducer name |
| Invalidate | Superseded units, expired observations, revoked sources, resolved questions, consumed single-use instructions, externalized tool-call pairs | Tombstoned; ineligible for any future assembly until a new authoritative version appears | Reason code, detecting condition, tombstone identifier, detection turn |

**Required Outputs**:

- One turn delta per turn carrying the append, replace, and invalidate sets with identifiers.
- A tombstone per invalidated unit carrying its reason code and detecting condition.
- A lineage entry per replaced unit naming both versions and the reducer that applied the change.

**Quality Checkpoints**:

- The three sets are disjoint; a unit appearing in two sets halts the commit for reclassification.
- Every invalidation names a detecting condition; an invalidation justified only by the unit not appearing in the next package is rejected.
- Every turn recorded a delta; the count of turns with an unrecorded delta is exactly 0.

***

#### Step 3.3: Update the Budget Ledger and Project the Next Turn

**Required Actions**:

- Post the turn's token cost to the budget ledger by partition, distinguishing prefix tokens, suffix tokens, and provider-reported cache-read and cache-write tokens where the provider reports them.
- Compute the turn delta size in tokens and maintain a rolling distribution over the last 10 turns, so that growth is measured rather than assumed linear.
- Project the next turn's assembled size as the current size plus the 95th percentile turn delta, and evaluate the boundary triggers in Section 1.5 against that projection.
- Record the occupancy ratio and the projection in the ledger every turn, so that a forced boundary is distinguishable from a declared one during review.
- Checkpoint at every irreversible effect boundary and at the declared turn interval, and block an effect whose pre-effect checkpoint is missing.

**Required Outputs**:

- A per-partition budget ledger entry per turn including cache-read and cache-write counts where reported.
- A rolling turn-delta distribution over the last 10 turns with a recorded 95th percentile.
- A boundary trigger evaluation per turn with a fired or not-fired verdict.

**Quality Checkpoints**:

- Token counts derive from the target model's tokenizer after serialization, never from character-length estimation.
- The projection uses measured turn deltas rather than an assumed growth rate.
- Every irreversible effect is bracketed by a checkpoint before and after; a missing pre-effect checkpoint blocks the effect.

***

### Phase 4: Invalidation and Supersession Within a Run

**Objective**: Remove eligibility from every unit whose invalidating condition has been detected, explicitly and with a recorded reason, so that correctness never depends on a unit happening to fall out of a window.

**Owning tier**: Deterministic; expiry arithmetic, supersession identity, revocation propagation, and tombstone bookkeeping are software operations, and a model claim that a unit is current is not evidence.

#### Step 4.1: Detect Invalidating Conditions Deterministically

**Required Actions**:

- Evaluate freshness on every read against the unit's declared expiry rather than a global interval, since an authorization grant, a computed figure, a reference document, and a historical record carry different validity periods.
- Detect supersession by unit identity and authority, admitting a newer version only where it names the same identity and carries authority at least equal to the version it replaces.
- Subscribe to revocation events for consent withdrawal, permission change, source deletion, policy change, and tool-schema change, and treat each as an invalidating condition on every unit derived from the revoked source.
- Detect dependency invalidation where a prefix element, a schema, a policy, or a parent summary changes, and mark every descendant derived from the changed parent.
- Distinguish contradiction from supersession: two authoritative current sources disagreeing about one identity produce a visible unresolved conflict, never a silent replacement.

**Required Outputs**:

- A freshness verdict per unit read, naming its observation time and expiry.
- A supersession record per replacement naming both version identifiers and the authority comparison.
- A revocation and dependency invalidation set naming every affected descendant.

**Quality Checkpoints**:

- Every unit carries a declared expiry; a unit with no expiry rule is refused admission rather than treated as permanent.
- No supersession was committed where the incoming version carried lower authority than the version it replaces.
- Contradictions remain visible as unresolved conflicts; a contradiction silently resolved into a replacement is a defect.

***

#### Step 4.2: Execute Explicit Invalidation With a Reason Code and a Tombstone

**Required Actions**:

- Write a tombstone at the turn the invalidating condition is detected, carrying the unit identifier, the reason code, the detecting condition, the detection turn, and the identifier of any superseding version.
- Make the tombstone the filter: the renderer consults tombstones before assembly, so an invalidated unit cannot re-enter through retrieval, replay, cache, or a restored checkpoint.
- Prohibit invalidation by omission, and record as a defect any case where a unit ceased to appear in assemblies without a corresponding tombstone.
- Distinguish the three terminal dispositions of an invalidated unit: ineligible but retained as lineage, externalized behind a reference, or erased under a declared retention obligation, and record which applies.
- Bound invalidation latency to 1 turn from detection to absence from the next assembled package, and record a staleness event where a unit survives 2 assemblies after detection.

**Required Outputs**:

- A tombstone per invalidated unit with all five required fields.
- A disposition record naming which of the three terminal dispositions applies to each invalidated unit.
- An invalidation latency measurement per unit, in turns from detection to absence.

**Quality Checkpoints**:

- Every unit absent from an assembly that was present in the prior one traces to either a tombstone or a recorded eviction with a reference; an untraceable absence is a defect.
- No invalidated unit re-entered an assembly through retrieval, replay, cache, or checkpoint restore.
- Invalidation latency is 1 turn or less for every unit; 2 or more is recorded as a staleness event.

***

#### Step 4.3: Propagate Invalidation to Derived Artifacts and the Prefix

**Required Actions**:

- Enumerate the descendants of every invalidated unit: summaries, extracted claims, index entries, embeddings, cached prompt segments, checkpoints, and handoff records already written.
- Invalidate or rebuild each descendant rather than leaving it serving, since a summary outlives the source it summarised and a cache entry outlives the permission that authorised it.
- Treat a cache hit as an economic outcome and never as a freshness or authorization decision, and scope cache keys by tenant, authorization scope, model identifier, prompt version, tool-schema version, and policy version so that a change to any of them misses rather than serves [9].
- Where the invalidating condition touches a prefix element, end the epoch and reinitialise under Phase 2 rather than mutating the frozen prefix, and record the epoch increment with its reason code.
- Where the invalidating condition is a revocation arising from a compromised or hostile source, invalidate the source's full descendant set, rebuild the affected indexes, and review the actions taken since the source was admitted [10][11].

**Required Outputs**:

- A descendant set per invalidated unit naming every derived artifact.
- A propagation verdict per descendant recording invalidation, rebuild, or an approved exception.
- An epoch increment record where a prefix element was affected.

**Quality Checkpoints**:

- Every descendant class named in the inventory received a propagation verdict; an unvisited class blocks the invalidation from closing.
- No cache key omits tenant, authorization scope, or policy version; a hit never bypasses an authorization or freshness check.
- A prefix-affecting invalidation produced an epoch increment; a mutated frozen prefix is a defect regardless of the change's size.

***

### Phase 5: Boundary Crossing With Handoff and Reconstruction Verification

**Objective**: Cross every context boundary through a handoff record whose sufficiency has been verified deterministically, so that the outgoing window is discarded only after the incoming state has been proven reconstructable.

**Owning tier**: Hybrid; the model tier judges what remains relevant and drafts the summary fields, the deterministic tier constructs the record, runs the reconstruction test, and holds the discard gate absolutely.

#### Step 5.1: Declare the Boundary Before It Is Forced

**Required Actions**:

- Evaluate the boundary triggers every turn against measured occupancy and projected next-turn growth, and declare the boundary at the first firing rather than at the hard limit.
- Classify the boundary, since the class determines what survives it and what must be rebuilt, and record the class in the ledger with the trigger that fired.
- Record whether the boundary was declared or forced, treating a forced boundary as a lead-time defect requiring threshold recalibration rather than as normal operation.
- Freeze admission of new work at the moment of declaration, completing the current tool-call pair and refusing new ones, so that the state being captured is not moving while it is captured.
- Write a pre-boundary checkpoint before any handoff drafting begins, so that a failure during the crossing returns to a known state rather than to a partially dismantled one.

**Boundary classes and what survives them**:

| Boundary class | Trigger | What survives without action | What must be rebuilt from the handoff |
| :-- | :-- | :-- | :-- |
| Occupancy compaction | Assembled input at or above the declared threshold | Durable stores, canonical state, run identity | The entire volatile suffix and any evicted evidence set |
| Session end or process restart | Termination of the serving process or session | Durable stores only | Prefix, suffix, budget ledger position, in-flight effect status |
| Sub-agent dispatch | Delegation of a bounded subtask | Parent's own context, unchanged | The child's entire context, scoped to the delegated subtask |
| Model or provider switch | Change of model, tokenizer, or provider | Durable stores and canonical state | Prefix, token accounting, and any provider-held continuation state |
| Prefix invalidation | Change to policy, instructions, tool set, or tool order | Durable stores and canonical state | The prefix and every cached segment derived from it |
| Suspension beyond retention | Wait exceeding the declared window-retention interval | Durable stores only | Prefix, suffix, and the freshness state of every observation |

**Required Outputs**:

- A boundary declaration naming the class, the firing trigger, and whether it was declared or forced.
- An admission freeze marker with the completion status of every in-flight tool-call pair.
- A pre-boundary checkpoint written before drafting begins.

**Quality Checkpoints**:

- The boundary was declared before the hard limit; a forced boundary is recorded and triggers threshold recalibration.
- No new work was admitted after the declaration; a tool call issued during a crossing is a defect.
- The pre-boundary checkpoint exists and validates before any content is removed.

***

#### Step 5.2: Construct the Handoff Record

**Required Actions**:

- Populate every required content class of the handoff record from canonical state, never from the transcript, since the transcript carries superseded values and abandoned work that the canonical state has already resolved.
- Include durable references for every unit evicted or externalized during the epoch, so that content absent from the handoff remains retrievable rather than lost.
- State the exact next decision as an action identifier the receiver can execute, rather than as a description of what remains to be done.
- Have the model draft only the summary and rationale fields, and bound them to the declared size, since a summary is the one field no deterministic rule can produce.
- Record the remaining budget by partition, the epoch lineage, the prefix version, and the invalidation ledger digest, so the receiver inherits the accounting rather than restarting it.

**Handoff Record Template**:

```
HANDOFF_ID:
RUN_ID:
OUTGOING_EPOCH_ID:
BOUNDARY_CLASS:          OCCUPANCY | SESSION_END | SUBAGENT_DISPATCH |
                         PROVIDER_SWITCH | PREFIX_INVALIDATION | SUSPENSION
STATE_SCHEMA_VERSION:
STATE_VERSION:
PROTECTED_SET_HASH:
ACTIVE_GOAL:             objective and success criteria
BINDING_CONSTRAINTS:     standing, safety, and authority constraints
PLAN:                    plan version, step identifiers, statuses, dependencies
COMPLETED_WORK:          verified outputs with artifact references
OPEN_WORK:               unresolved subtasks, open questions, blocked items
OPEN_VARIABLES:          value, provenance, observed_at, fresh_until per variable
EVIDENCE_REFERENCES:     durable references for every evicted or externalized unit
ERROR_STATE:             unresolved errors, fingerprints, attempted remedies
SIDE_EFFECT_LEDGER:      committed, pending, and ambiguous effects with idempotency keys
APPROVALS:               granted and outstanding
REMAINING_BUDGET:        per partition, in tokens, and per non-token dimension
INVALIDATION_DIGEST:     tombstone set hash and count
PREFIX_VERSION:
EPOCH_LINEAGE:           ordered ancestor epoch identifiers
NEXT_DECISION:           executable action identifier, not a description
SUMMARY:                 model-drafted, size-bounded, non-authoritative
REASONING_CONTENT:       PROHIBITED
```

**Required Outputs**:

- A handoff record with every required content class populated and both version fields present.
- A durable reference set covering every unit evicted or externalized during the epoch.
- A size measurement confirming the record fits within its declared share of the input budget.

**Quality Checkpoints**:

- Every required content class is populated; an omission is recorded as handoff loss and blocks the crossing rather than being accepted with a note.
- Every content class was populated from canonical state; a field derived from the transcript is rejected.
- The record carries no reasoning content and no raw secret, and its summary field is marked non-authoritative.

***

#### Step 5.3: Run the Reconstruction Test and Gate the Discard

**Required Actions**:

- Build a candidate working state from the handoff record alone, in a process with no access to the outgoing window, so that the test measures the record rather than the residual context.
- Compare the candidate against the canonical state at the boundary on the five checks below, and treat any failure as a failure of the whole test.
- Amend the handoff and re-test where the verdict fails, up to the declared amendment limit, and escalate rather than proceeding once the limit is reached.
- Retain the outgoing window until a passing verdict is recorded, and release it only in the same operation that records the verdict and the transition into Reinitialised.
- Require the receiver to acknowledge the state version and the schema version, and to refuse an incompatible schema or an authority scope it does not hold.

**Reconstruction Test**:

```
CHECK 1  PROTECTED ATOMS
         Hash over the normalised protected set of the candidate state
         equals the hash recorded at the boundary.
         PASS CONDITION: exact match, 100 percent of atoms present.

CHECK 2  REFERENCE RESOLUTION
         Every durable reference in the handoff resolves and its content
         hash matches the hash recorded at write time.
         PASS CONDITION: unresolved references == 0, hash mismatches == 0.

CHECK 3  NEXT DECISION EQUIVALENCE
         The action selector, run against the candidate state, returns the
         action identifier named in NEXT_DECISION.
         PASS CONDITION: identifiers equal.

CHECK 4  EFFECT RECONCILIATION
         Every entry in the side-effect ledger carries a status and an
         idempotency key, and every ambiguous effect carries a
         reconciliation entry queried from the effect's own boundary.
         PASS CONDITION: ambiguous effects without reconciliation == 0.

CHECK 5  BUDGET AND VERSION CONTINUITY
         Committed budget counters in the candidate equal the recorded
         remaining budget, and schema and policy versions either match or
         have a registered migration.
         PASS CONDITION: counter difference == 0, unmigrated version gaps == 0.

VERDICT  PASS only where all five checks pass.
         On FAIL: retain the outgoing window, amend, re-test.
         After 2 failed amendments: escalate to a named owner.
         The outgoing window is never discarded on a FAIL verdict.
```

**Required Outputs**:

- A reconstruction verdict carrying a pass or fail result for each of the five checks.
- A receiver acknowledgement naming the accepted state version, schema version, and authority verdict.
- A ledger entry recording the discard of the outgoing window and the transition into Reinitialised.

**Quality Checkpoints**:

- No outgoing window was discarded before a passing verdict; the count of unverified discards is exactly 0.
- Protected atom preservation across the boundary is 100 percent, verified by hash rather than asserted.
- Duplicate irreversible effects across boundaries number exactly 0; any occurrence blocks release of the configuration.

***

### Phase 6: Teardown, Persistence Verification, and Lifecycle Evaluation

**Objective**: Close the run by persisting what must outlive it, verifying that persistence before releasing anything, and emitting the evidence that lets the next deployment recalibrate its thresholds.

**Owning tier**: Deterministic for classification enforcement, read-back verification, discard release, and metric computation; the model tier nominates promotion candidates and drafts closing summaries only.

#### Step 6.1: Classify Every Live Element as Persist, Discard, or Erase

**Required Actions**:

- Enumerate every live element at termination: canonical state, checkpoints, artifacts, evidence sets, tombstones, handoff records, ledger entries, caches, provider-held conversation state, and scratch files.
- Assign each element exactly one disposition from the inventory declared in Step 1.3, and refuse to close where any element carries no disposition.
- Default to discard rather than persist, and require for a promotion that the item is useful outside this run, carries a complete provenance path, has been verified rather than asserted, has been classified for tenant scope and sensitivity, and is admitted by the receiving store's write policy.
- Route every erase element through the declared propagation set, covering primary stores, indexes, summaries, embeddings, caches, checkpoints, archives, replicas, and any provider-held copy, and record the completion evidence rather than the erased payload [7][8].
- Set the retention expiry on every persisted element at write time, and reject a persist target whose expiry is unset.

**Required Outputs**:

- A live element inventory with exactly one disposition per element.
- A promotion record per persisted item naming the five admission conditions and their verdicts.
- An erasure propagation record naming every target and its completion evidence.

**Quality Checkpoints**:

- Every live element carries a disposition; an unclassified element blocks teardown from proceeding.
- No item was promoted on task success alone; each carries all five admission verdicts.
- Every persisted element carries a retention expiry set at write time.

***

#### Step 6.2: Verify Persistence Before Any Discard

**Required Actions**:

- Read back every persist target from its destination store by identifier, and compare its content hash against the hash recorded at write time.
- Confirm that the target is retrievable by the identifier the run will publish, since a value written under one key and referenced under another is functionally lost.
- Retry a failing verification up to the declared attempt limit with a bounded timeout per attempt, and terminate the run as teardown-incomplete rather than discarding once the limit is exhausted.
- Release discard targets only after every persist target carries a passing verdict, and execute the release in one recorded operation so a partial teardown is detectable.
- Revoke credentials, close store handles, expire leases, remove serving aliases, and delete scratch files as part of the same recorded release, so no capability outlives the run that held it.

**Required Outputs**:

- A persistence manifest with a read-back verdict, content hash comparison, and retrievability verdict per target.
- A discard release record naming every element released and the verdict set that authorised it.
- A capability closure record naming every credential, handle, lease, and alias revoked.

**Quality Checkpoints**:

- The proportion of persist targets verified before any discard is exactly 100 percent; a shortfall terminates the run as teardown-incomplete.
- Every verified target is retrievable by its published identifier, not merely present in its store.
- No credential, handle, lease, or serving alias survives the run; a surviving capability is a defect.

***

#### Step 6.3: Emit the Lifecycle Record and Compute the Stage Metric Set

**Required Actions**:

- Emit one root trace per run with child spans for initialisation, each turn assembly, each invalidation, each boundary crossing, and teardown, and adopt the current generative-AI semantic conventions for identifiers where they cover the field, adding namespaced application attributes only for lifecycle fields the conventions do not yet carry [12][13].
- Default to metadata-only telemetry, keeping prompts, evidence payloads, and tool arguments in a separately authorized store with shorter retention and audited access.
- Compute the stage metric set with an explicit numerator, denominator, sample count, time window, and version cohort for every ratio, since a percentage without its denominator supports no decision.
- Recompute every threshold in Section 1.5 against observed runs at each release, and record the recomputed value beside the default it replaced.
- Run interruption trials that kill the process at each stage boundary, verify that the run resumes without a duplicate irreversible effect, and block release where any trial produces one.

**Required Outputs**:

- A lifecycle event record per run covering every stage transition and boundary crossing.
- A stage metric report with denominators and cohorts stated for every ratio.
- An interruption trial result set covering every stage boundary.

**Quality Checkpoints**:

- Every ratio carries its numerator, denominator, sample count, window, and cohort; a bare percentage is rejected.
- No telemetry field carries a prompt payload, an evidence payload, or reasoning content.
- Duplicate irreversible effects across the interruption trial suite number exactly 0; any occurrence blocks release.

***

## III. Implementation Guidance for AI Agents

AI agents operating a context lifecycle must follow systematic protocols ensuring that every stage transition is recorded, every boundary crossing is verified before the outgoing window is released, and every terminal state is reached through a checked teardown rather than through exhaustion. The following guidance translates the staged lifecycle into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Lifecycle Controller**: Owns the stage contract, evaluates every transition predicate, and writes every stage change to the ledger. It alone may record a stage transition, and it refuses a transition whose entry condition is unmet regardless of any other component's request.
2. **Initialiser**: Resolves identity, pins versions, partitions the budget, opens store handles, serializes and hashes the prefix, and writes the initialisation record. It fails closed rather than defaulting an unresolved version.
3. **Assembler**: Rebuilds the volatile suffix each turn from canonical state, verifies the prefix hash, counts tokens with the target tokenizer, and holds the budget veto. A model preference never exceeds a partition bound.
4. **Mutation Recorder**: Classifies each turn's changes into the append, replace, and invalidate sets, writes tombstones and supersession lineage, and refuses to commit a turn with no recorded delta.
5. **Boundary Agent**: Evaluates boundary triggers, declares the boundary and its class, freezes admission, constructs the handoff record, and requests the reconstruction test. It never discards a window.
6. **Reconstruction Verifier**: Runs the five-check reconstruction test in a process isolated from the outgoing window and issues the only verdict that releases that window. It may veto a crossing and cannot be overridden by any other component.
7. **Teardown Agent**: Classifies live elements, verifies persistence by read-back, releases discard targets in one recorded operation, and terminates the run as teardown-incomplete where verification does not complete.

**The discard gate**: Only the Reconstruction Verifier's passing verdict releases an outgoing window, and only the Teardown Agent's complete verification verdict set releases a discard target. No other component may release either, and neither release is ever performed on a model assertion, an elapsed timer, or an operator's assumption that the state was captured.

**Workflow Execution Pattern**:

```
STATE: Boundary_Crossing
INPUTS:
  1. Boundary declaration with class and firing trigger from Step 5.1
  2. Canonical state object at the boundary
  3. Durable reference set for evicted and externalized units
  4. Pre-boundary checkpoint identifier
ACTIONS:
  1. Freeze admission and complete in-flight tool-call pairs
  2. Populate every handoff content class from canonical state
  3. Request one model-drafted summary field, size-bounded
  4. Build a candidate state from the handoff in an isolated process
  5. Run the five reconstruction checks against the boundary state
VALIDATION:
  - required_content_classes_populated == TRUE
  - protected_atom_hash_match == TRUE
  - unresolved_references == 0
  - next_decision_identifier_match == TRUE
  - ambiguous_effects_without_reconciliation == 0
  - unmigrated_version_gaps == 0
  - reasoning_content_persisted == FALSE
TRANSITIONS:
  IF all_validations_pass
     THEN discard_outgoing_window AND next_state = Reinitialised
  IF validation_failed AND amendments_used < 2
     THEN next_state = Handoff_Amendment
  IF validation_failed AND amendments_used >= 2
     THEN next_state = Boundary_Escalation
  THE OUTGOING WINDOW IS RETAINED IN BOTH FAILURE PATHS
```

**Two-Phase Action Pattern**: Emit the intended stage transition with its trigger, its evidence references, and its artifact identifiers without executing it; confirm it against the validation block while the outgoing state is still intact; commit it only after validation passes, recording the transition in the same operation that performs it.

**Approval Gate**: Human authorisation is required before discarding an outgoing window whose reconstruction test failed twice, before executing an erasure whose propagation set includes a target the run cannot verify, before opening a seventh epoch within one run, and before terminating a run whose persistence verification covered less than 100 percent of persist targets. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the stage contract, the ledger, the canonical state, and the budget position in durable stores, since the lifecycle by definition outlives any single window.
- Count the lifecycle machinery's own token and latency cost against the run's budget rather than treating it as free, since handoff drafting and reconstruction testing consume real resources.
- Draft one handoff per boundary and one summary field per handoff, rather than regenerating summaries across turns, so that summarisation cost scales with boundaries rather than with turns.
- Never read a value back from the window as authority; the canonical state and the ledger are the record, and the window is a rendering regenerated on every call.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Stage Contract Integrity (After Phase 1)**

- **Automated Check**: Every stage carries an entry condition, a produced artifact, and a terminating condition; every transition predicate evaluates from observable values; the reason-code vocabulary is closed; every state class carries a disposition.
- **Agent Action on Pass**: Proceed to initialisation.
- **Agent Action on Failure**: Halt and return the incomplete contract element; no context is allocated against an incomplete contract.
- **Human Review Trigger**: A transition condition that cannot be stated as an evaluable predicate, or a state class whose retention obligation is unresolved.

**Checkpoint 2: Initialisation Validity (After Phase 2)**

- **Automated Check**: Every behaviour-affecting version is pinned; identity, tenant, and authority resolve; the prefix hash and tokenizer-exact count are recorded; the prefix occupies no more than 25 percent of the input budget; every store handle verified reachable and writable.
- **Agent Action on Pass**: Assemble the first turn against the frozen prefix.
- **Agent Action on Failure**: Fail closed; an epoch never opens on an unresolved identity, policy, or store.
- **Human Review Trigger**: Prefix share above 35 percent of the input budget, or a schema version with no registered reader.

**Checkpoint 3: Turn Accounting Integrity (After Phase 3, every turn)**

- **Automated Check**: Prefix hash matches the initialisation record; the append, replace, and invalidate sets are disjoint and recorded; token counts derive from the target tokenizer; the boundary trigger evaluation returned a verdict.
- **Agent Action on Pass**: Issue the call and commit the turn.
- **Agent Action on Failure**: Halt the turn and rebuild the suffix; a turn is never issued with an unmatched prefix hash or an unrecorded delta.
- **Human Review Trigger**: More than 5 percent of turns in a run failing this checkpoint.

**Checkpoint 4: Invalidation Completeness (After Phase 4, every invalidation)**

- **Automated Check**: Every tombstone carries all five fields; every descendant class received a propagation verdict; invalidation latency is 1 turn or less; no invalidated unit re-entered an assembly.
- **Agent Action on Pass**: Continue the Active stage.
- **Agent Action on Failure**: Block the next assembly until propagation completes; a partially propagated invalidation never serves.
- **Human Review Trigger**: Any re-entry of an invalidated unit, or any revocation whose descendant set cannot be enumerated.

**Checkpoint 5: Boundary Crossing Validity (After Phase 5, every boundary)**

- **Automated Check**: All five reconstruction checks pass; the receiver acknowledged both version fields; the outgoing window was retained until the verdict; duplicate irreversible effects across the boundary number 0.
- **Agent Action on Pass**: Discard the outgoing window and transition to Reinitialised in one recorded operation.
- **Agent Action on Failure**: Retain the outgoing window, amend the handoff, and re-test; an invalid crossing is never executed with a warning attached.
- **Human Review Trigger**: A second failed amendment, or a boundary the run was forced into rather than declaring.

**Checkpoint 6: Teardown Completeness (After Phase 6)**

- **Automated Check**: Every live element carries a disposition; 100 percent of persist targets verified by read-back and retrievable by published identifier; every erase target carries completion evidence; no capability survives the run.
- **Agent Action on Pass**: Close the run in its declared terminal state and release the lifecycle record.
- **Agent Action on Failure**: Terminate as teardown-incomplete, execute no discard, and name the unverified targets and their owner.
- **Human Review Trigger**: Any teardown-incomplete termination, or any erase target the run cannot verify.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
STAGE_BOUNDARY:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Forced Boundary**

- **Symptoms**: The window overflowed before a boundary was declared; a provider rejected the call for length; the crossing began after the outgoing content had already been truncated.
- **Diagnostic Steps**: Compare the occupancy trace against the declared trigger threshold, and determine whether the projection under-estimated growth, the threshold was set too high, or a single turn delta exceeded the rolling distribution by more than a factor of 2.
- **Resolution Protocol**: Option A, lower the occupancy trigger by 10 percentage points and re-measure over the next 20 runs. Option B, switch the projection from the 95th to the 99th percentile turn delta for the task class. Option C, cap the single-turn delta by externalizing tool results above a smaller size cap, so no one turn can jump the threshold.
- **Escalation Trigger**: More than 1 forced boundary per 20 runs in a task class escalates for threshold recalibration; a forced boundary that truncated content before capture escalates immediately, since the handoff cannot then be built from a complete state.

**Error Type 2: Handoff Insufficiency**

- **Symptoms**: The reconstruction test fails; the receiver requests information the record does not carry; the post-boundary agent repeats work or asks a question the run already answered.
- **Diagnostic Steps**: Identify which of the five checks failed and which content class was implicated, and determine whether the field was absent, populated from the transcript, or populated from a reference that no longer resolves.
- **Resolution Protocol**: Option A, populate the missing class from canonical state and re-test. Option B, where a reference no longer resolves, re-externalize the content and update the reference before re-testing. Option C, where the summary field is carrying load the structured fields should carry, move the content into structured fields and re-draft the summary as non-authoritative.
- **Escalation Trigger**: A third failing verdict after 2 amendments escalates to a named owner with the outgoing window retained; the crossing is never completed by relaxing a check.

**Error Type 3: Invalidation by Omission**

- **Symptoms**: A superseded or expired value influenced a decision; a unit disappeared from assemblies with no tombstone; a revoked source's content reappeared after a checkpoint restore.
- **Diagnostic Steps**: Trace the unit from its last appearance to its detecting condition, and determine whether a tombstone was never written, was written after the unit had already served, or was written but not consulted by the renderer.
- **Resolution Protocol**: Option A, write the missing tombstone, propagate to descendants, and rebuild the affected indexes. Option B, move the tombstone check ahead of retrieval in the assembly order, so an invalidated unit cannot be selected in the first place. Option C, where the omission arose from a restore, apply the full tombstone set as part of restore rather than after it.
- **Escalation Trigger**: Any invalidated unit that influenced an irreversible action escalates immediately; this class is never resolved by re-running the assembly.

**Error Type 4: Prefix Instability**

- **Symptoms**: Cache-read tokens fall toward zero across an epoch; the prefix hash differs between consecutive turns with no recorded epoch increment; per-turn cost rises with no change in task content.
- **Diagnostic Steps**: Diff consecutive serialized prefixes byte by byte and locate the varying element, checking first for injected timestamps, counters, non-deterministic key ordering, and tool sets assembled from an unordered collection.
- **Resolution Protocol**: Option A, move the varying element into the volatile suffix and re-freeze the prefix. Option B, fix the serialization to canonical key ordering so semantically identical prefixes are byte-identical. Option C, where the change is genuinely required, end the epoch and reinitialise rather than allowing the prefix to drift.
- **Escalation Trigger**: A third prefix rebuild within one run halts the run for contract review; drift that continues after two corrections escalates to the initialisation owner.

**Error Type 5: Teardown Without Verified Persistence**

- **Symptoms**: A durable output cannot be retrieved after the run closed; a reference published by the run resolves to nothing; a store reports the object under a different key than the one published.
- **Diagnostic Steps**: Compare the persistence manifest against the destination stores by identifier and hash, and determine whether the write failed, the verification was skipped, or the published identifier differs from the write key.
- **Resolution Protocol**: Option A, re-execute the write from the retained pre-teardown checkpoint and verify by read-back. Option B, where the checkpoint is also gone, reconstruct from the ledger and the durable reference set and record the reconstruction as a partial recovery. Option C, where neither is available, record the loss, its scope, and its cause rather than reporting the run as complete.
- **Escalation Trigger**: Any discard executed before a complete verification verdict set escalates immediately and blocks release of the configuration; this class is never resolved by retrying the discard.

**Error Type 6: Stage Drift**

- **Symptoms**: A component acts as though the run is in a stage it never entered; a transition appears in the ledger with no trigger; two components disagree about the current stage.
- **Diagnostic Steps**: Replay the ledger from the run's opening and identify the first event whose entry condition was unmet, then determine whether the transition was recorded by an unauthorised component or inferred from elapsed time.
- **Resolution Protocol**: Option A, roll the run back to the last stage whose entry condition validates and re-enter forward through recorded transitions. Option B, restrict transition-writing to the Lifecycle Controller and reject events from every other source. Option C, where the drift originated in a resumed process, require a stage acknowledgement at resume before any action is selected.
- **Escalation Trigger**: Any transition recorded by a component other than the Lifecycle Controller escalates for architecture review; a run whose current stage cannot be established halts rather than guessing.

**Troubleshooting Decision Tree**:

```
LIFECYCLE CHECKPOINT DETECTS A PROBLEM
├─ TRANSITION DEFECT
│   ├─ Entry condition unmet → Refuse transition; record refusal event
│   ├─ Transition written by another component → HALT; restrict to controller
│   └─ Current stage indeterminate → HALT; re-establish from ledger replay
├─ INITIALISATION DEFECT
│   ├─ Unpinned behaviour-affecting version → Fail closed; do not default
│   ├─ Prefix hash drifts within an epoch → Locate varying element; move to suffix
│   └─ Prefix above 35 percent of budget → Externalize static material; re-init
├─ TURN DEFECT
│   ├─ Delta unrecorded → Refuse commit; reclassify and re-record
│   ├─ Unit in two delta sets → HALT; reclassify into exactly one
│   └─ Superseded value rendered → Rebuild suffix from canonical state
├─ INVALIDATION DEFECT
│   ├─ Absence with no tombstone → Write tombstone; propagate to descendants
│   ├─ Invalidated unit re-entered → Move tombstone check ahead of retrieval
│   └─ Descendant set unenumerable → ESCALATE; do not close the invalidation
├─ BOUNDARY DEFECT
│   ├─ Reconstruction check fails → Retain window; amend handoff; re-test
│   ├─ Two amendments exhausted → ESCALATE; window stays retained
│   └─ Boundary forced not declared → Recalibrate threshold; record defect
└─ TEARDOWN DEFECT
    ├─ Persist target unverified → Terminate as teardown-incomplete
    ├─ Discard executed before verdict → HALT release; record loss scope
    └─ Erase target unverifiable → ESCALATE to the retention owner
```

### D. Performance Metrics and Continuous Learning

**Stage and Transition Metrics**:

- **Transition legality**: Recorded transitions whose entry condition validated, over recorded transitions (target: 100 percent; any shortfall blocks release).
- **Declared boundary share**: Boundaries declared before the hard limit, over all boundaries (target: at least 95 percent; below 90 percent triggers threshold recalibration).
- **Boundary lead time**: Turns between the boundary declaration and the projected overflow point (target: at least 1 turn; a median below 1 indicates the trigger is set too high).
- **Epochs per run**: Median and 95th percentile epoch count (target: median no more than 3, 95th percentile no more than 6; above indicates the prefix or the scope is wrong).

**Continuity and Integrity Metrics**:

- **Protected atom preservation**: Boundaries where all protected atoms matched by hash, over all boundaries (target: 100 percent; any shortfall is a zero-tolerance failure).
- **Handoff sufficiency**: Boundaries passing the reconstruction test on the first attempt, over all boundaries (target: at least 90 percent; below 75 percent indicates the record schema is missing a content class).
- **Post-boundary rework**: Turns after a crossing that repeated work completed before it, over the first 5 post-boundary turns (target: no more than 10 percent).
- **Duplicate irreversible effects**: Effects executed more than once across a boundary or a resume, over retried effects (target: exactly 0; any occurrence blocks release).
- **Invalidation latency**: Turns from detecting an invalidating condition to absence from the assembled package, reported at the 95th percentile (target: no more than 1 turn).
- **Staleness usage rate**: Reads that used content past its expiry, over reads requiring freshness (target: below 1 percent; a higher rate blocks promotion of the configuration).

**Cost and Efficiency Metrics**:

- **Prefix stability rate**: Turns whose prefix hash matched the epoch record, over turns in the epoch (target: at least 95 percent; below 90 percent indicates injected volatility).
- **Cache-read share**: Provider-reported cache-read tokens over total input tokens, where the provider reports them (target: rising within an epoch; a falling trend indicates prefix drift rather than a provider fault).
- **Lifecycle overhead**: Tokens and latency consumed by handoff drafting, reconstruction testing, and teardown verification, over total run cost (target: no more than 15 percent; above 25 percent triggers policy review).
- **Teardown completeness**: Persist targets verified before discard, over persist targets declared (target: 100 percent; any shortfall terminates the run as teardown-incomplete).

**Log-Pattern Failure Detection**: Cache-read tokens falling across an epoch indicates prefix drift, not provider variance. A rising post-boundary rework rate with a stable handoff schema indicates the model tier is nominating a carry-forward set that omits open work. Growing epoch counts with stable task complexity indicates the occupancy trigger is set too low. Invalidation latency rising after an index change indicates the tombstone filter is applied after retrieval rather than before it. Teardown-incomplete terminations concentrated in one store indicate a write-key and publish-key mismatch rather than a store fault.

**Learning and Adaptation Mechanisms**:

- **Threshold recomputation**: Recompute every default in Section 1.5 per task class against observed runs at each release, and record the recomputed value beside the default it replaced.
- **Handoff schema evolution**: Where a content class is repeatedly implicated in reconstruction failures, add the missing field to the schema rather than relying on drafting discipline to supply it.
- **Boundary policy versioning**: Version any trigger threshold changed from observed history and evaluate it on subsequent runs, so evaluation is not contaminated by the history that produced the change.
- **Interruption trial rotation**: Rotate the stage boundary at which interruption trials kill the process, so no boundary is left untested across successive releases.

**Human-in-the-Loop Boundaries**: Discarding a window whose reconstruction test failed twice, executing an erasure with an unverifiable target, opening a seventh epoch within one run, and closing a run whose persistence verification is incomplete are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the sequence and transitions of a context over time rather than the content of any particular context. Its stages hold wherever a run outlives a single model call, accumulates state across turns, and produces something that must survive its own termination.

### 4.1 Cross-Domain Application Patterns

**Clinical documentation and regulated record-keeping**: The lifecycle contract is a compliance artifact before it is an engineering one, because retention class, erasure obligation, and audit depth are declared per state class at Phase 1 rather than discovered at teardown. Boundaries are frequent because source records are long, so the handoff record carries the patient or case identity, the standing clinical constraints, and the reference set rather than the record text. Teardown is the binding stage: the persistence manifest is the evidence that a documented conclusion reached its system of record, and a teardown-incomplete termination is reported rather than retried silently.

**Software engineering and long-running build work**: Runs span hours and many boundaries, and the dominant risk is a post-boundary agent repeating a committed effect such as a merge, a deployment, or a release tag. The side-effect ledger is therefore the most load-bearing handoff field, and Check 4 of the reconstruction test carries most of the protective weight. The stable prefix holds the tool manifest and the repository conventions, and a tool-set change ends the epoch rather than mutating the prefix, since tool definitions participate in prefix reuse and reordering them destroys it.

**Financial operations and settlement workflows**: Reversibility varies sharply within one run, so checkpoint density is keyed to effect boundaries rather than to a turn interval, and every priced or authorization-bearing value expires on first use and again before any irreversible effect. Invalidation is the dominant stage: a revoked authorization, a superseded rate, or a withdrawn approval must leave eligibility within one turn, and the tombstone filter runs ahead of retrieval so a stale figure cannot be selected.

**Field service, logistics, and industrial operations**: Suspensions are long and connectivity is intermittent, so the run frequently crosses the window-retention interval and must rebuild from a handoff rather than assuming the window survived. Freshness intervals are short for environment observations and long for reference material, and the boundary class table drives what is re-observed rather than merely re-rendered. A resumed transport connection is never treated as evidence that a dispatched action completed.

**Customer-facing support and account servicing**: Runs are short but numerous, so lifecycle overhead dominates unless initialisation is genuinely once-per-epoch and the prefix is genuinely stable across the account's turns. Teardown is where promotion is decided, and the default is discard: a resolved ticket does not justify persisting its scratch reasoning, and a durable preference is written only where it passes all five promotion conditions.

### 4.2 Scale, Risk, and Duration Adaptation

- **Short single-window runs**: Collapse Phases 5 and the Crossing stage entirely, retain the stage contract, initialisation, turn delta recording, and teardown. Lifecycle overhead above 5 percent of run cost indicates the machinery exceeds the run it governs.
- **Long multi-epoch runs**: Retain every phase, tighten the boundary lead time to at least 2 turns, and write a checkpoint at every effect boundary. Persist the ledger and canonical state outside the serving process so a process restart is a boundary rather than a loss.
- **High-risk or irreversible work**: Require an external reconciliation query against every effect boundary before Check 4 passes, bind the approval gate before any discard following a failed reconstruction, and prefer terminating as teardown-incomplete over discarding on partial verification.
- **Multi-agent deployments**: Treat every sub-agent dispatch as a boundary of its own class, scope the child's handoff to the delegated subtask rather than forwarding the parent transcript, and require the child's terminal handoff to pass the same reconstruction test before its window is released.
- **Strict latency budgets**: Reduce handoff drafting cost by narrowing the summary field rather than by skipping structured content classes, since the structured fields are what the reconstruction test reads. Where latency forbids a full crossing, suspend the run and resume from a checkpoint instead of crossing without verification.

***

## V. Limitations and Considerations

**Thresholds here are defaults, not constants**: Every numeric bound in Section 1.5 was chosen to be operable on first deployment, not derived from a measured property of any model or workload. The consequence is that a deployment adopting them unchanged will over-trigger boundaries in some task classes and under-trigger in others. The mitigation is the recomputation requirement in Step 6.3, obliging each deployment to recompute every threshold per task class against observed runs and to record the recomputed value beside the default it replaced.

**The reconstruction test verifies sufficiency, not correctness**: The five checks establish that a handoff carries enough state to rebuild working state, not that the state itself is right. A run pursuing a wrong objective will cross every boundary cleanly and terminate with a verified persistence manifest. The mitigation is to treat the test as a continuity gate only, and to retain the separate quality review of the objective and the outputs that no lifecycle checkpoint substitutes for.

**Verification consumes the budget it protects**: Handoff drafting, isolated reconstruction, and read-back verification cost tokens, latency, and storage operations that the task itself does not. On short runs this overhead can exceed the loss it prevents. The mitigation is the scale adaptation in Section 4.2, which collapses the crossing machinery for single-window runs, together with the overhead metric that triggers policy review above 25 percent.

**Model-tier relevance judgement is the weakest link in a crossing**: The one judgement no rule covers is what accumulated work still matters, and a model making it shares the blind spots that produced the work. The consequence is that an omitted open subtask passes every deterministic check, because a check cannot know that something is missing from a set it never saw. The mitigation is the post-boundary rework metric, which detects the omission after the fact, and the requirement that open work be carried as a structured content class rather than folded into the summary field.

**Provider-managed state is opaque to the verifier**: Where a provider holds conversation state or performs server-side compaction, the application cannot inspect what was retained, cannot verify it against a preservation manifest, and cannot guarantee its retention or deletion behaviour matches the run's contract [1][3][6]. The mitigation is to treat provider-held state as an optimisation that never discharges the handoff obligation, and to keep the application-owned handoff record and reconstruction verdict as the run's only continuity evidence.

**Erasure cannot be promised beyond what propagation can verify**: A teardown obligation reaching indexes, summaries, caches, archives, replicas, and third-party processors is only as complete as the descendant enumeration behind it, and content already represented in a trained artifact may not be reachable at all [7][8]. The mitigation is to record residual copy classes and their scheduled overwrite dates explicitly rather than reporting an erasure as complete, and to escalate any target the run cannot verify to a named retention owner.

**Prefix stability is measured indirectly**: The agent layer cannot observe the serving-side cache and must infer reuse from provider-reported cache-read and cache-write token counts, which not every provider reports and which no provider guarantees. The consequence is that a prefix can be byte-stable and still produce no measurable reuse for reasons the application cannot see. The mitigation is to treat the prefix hash match as the controllable target and the cache-read share as corroborating evidence rather than as the acceptance criterion.

***

## VI. Conclusion and Summary

Context lifecycle management is a sequencing discipline before it is a context technique. Its value comes from a small number of transitions made explicit: when a context is established and what is frozen at that moment, what each turn adds and what each turn removes, when a window is declared finished rather than discovered full, what must be provably reconstructable before the old window is released, and what must be provably persisted before a completed run lets anything go. A system that records those transitions can be audited and recovered; a system that leaves them implicit loses state at exactly the point where the run is longest and the loss is least visible.

A team introducing this framework should instrument before building. Record stage transitions, turn deltas, and boundary events against the existing behaviour first, so that measured occupancy curves and turn-delta distributions replace guessed thresholds. Then add the handoff record and the reconstruction test, since the boundary is where the loss actually occurs and where a deterministic gate pays for itself soonest. Add explicit invalidation next, because a tombstone filter ahead of retrieval removes a whole class of stale-value failures that no amount of ranking corrects. Add teardown verification last, and treat teardown-incomplete as a reportable outcome rather than a defect to be hidden. Provider mechanisms for compaction, caching, conversation state, and session resumption are useful at every one of these stages, and none of them is a substitute for the application's own record of what happened.

**Key Success Factors**:

- **Stages with stated transitions**: Every stage carries an entry condition, a produced artifact, and a terminating condition, so stage membership is checkable and drift is detectable rather than inferred.
- **Initialise once, assemble per turn**: What does not change within an epoch is established once, ordered by descending stability, frozen, and hashed; a needless reorder ends the epoch and forfeits the reuse it was ordered to obtain.
- **Explicit invalidation**: A unit loses eligibility when its condition is detected and a tombstone is written, never by falling out of a window, because the window is a rendering and its contents prove nothing about what remains authoritative.
- **Verified boundary crossings**: A handoff record carries the goal, the binding constraints, the completed and open work, the durable references for evicted content, and the remaining budget, and the outgoing window is discarded only after the reconstruction test passes.
- **Verified teardown**: Every persist target is read back and matched by hash before any discard is executed, and a run that cannot verify persistence terminates as teardown-incomplete rather than releasing on an assumption.
- **Deterministic gates on irreversible steps**: Discarding a window and releasing state are both irreversible, and neither is ever performed on a model judgement, an elapsed timer, or an operator's confidence that the state was captured.

By following this guide, AI agents can operate runs that outlive any single context window, cross every boundary with proven continuity, and terminate through a checked teardown that a reviewer can audit rather than through exhaustion or silent loss.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source and carries the time dimension of the context-management category: the stage sequence over a run's lifetime and the transitions between stages. The corpus pointers below identify that source and the sibling guides that own the individual operations invoked within a stage. The external references that follow are transcribed from the originating prose guide as it cited them and were not independently re-verified during conversion, except for the single entry explicitly marked as verified, whose title and location were retrieved during this conversion's research.

**Corpus pointers**:

- `Context Management Lifecycle Guide` — the originating prose guide from which this operational guide was derived. Source of the lifecycle invariants, the state and serialization contract, the initialisation and session scaffold procedure, the per-turn transaction discipline, the checkpoint content inventory, the compaction and window-handoff procedure, the freshness and invalidation taxonomy, the garbage-collection and archive rules, the erasure and retention obligations, the versioning and change-management rules, the lifecycle event field inventory, the metric definitions with their denominators, the failure-mode catalogue, and the production readiness checklist. Its depth on durable workflow engines, branch and merge semantics, memory tier promotion, and memory-poisoning defence is deferred here to the sibling guides named below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the category umbrella. Source of the context boundary definition, the handoff record definition, the context contract and partitioned budget vocabulary, the trust class taxonomy, and the operation-selection ladder this guide invokes but does not restate.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — the source of the handoff and reconstruction discipline adopted here, together with the protected atom set, the checkpoint contents, the supersession and freshness vocabulary, and the resume-only-after-reconciliation rule. Its terminology is adopted unchanged rather than re-coined.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — the sibling carrying the internal procedure for externalizing content behind durable references, invoked by the eviction and handoff steps in Phases 3 and 5.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — the sibling carrying the internal procedure for admission and ranking, invoked by the per-turn assembly step in Phase 3.
- `advanced_task_guides/context-management/guide_ContextCompression.md` — the sibling carrying the internal procedure for lossy reduction under a preservation manifest, invoked at the occupancy boundary class in Phase 5.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — the sibling carrying the internal procedure for delegating into separate contexts, invoked at the sub-agent dispatch boundary class in Phase 5.
- `advanced_task_guides/context-management/guide_ContextFailurePrevention.md` — companion guidance on the failure classes this lifecycle's checkpoints are designed to detect, applicable to Section III.C.
- `advanced_task_guides/context-management/guide_FilesystemAsContext.md` — companion guidance on filesystem-backed durable stores, applicable to the durable reference set in Steps 5.2 and 6.2.
- `advanced_task_guides/context-management/guide_HierarchicalContextArchitecture.md` — companion guidance on tiered context organisation, applicable to the prefix and suffix split in Phase 2.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — the memory-category umbrella. Source of the canonical record, derived artifact, and retrieval eligibility vocabulary used in Phase 4.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — companion guidance on decay, expiry, tombstones, and verified deletion, applicable to the invalidation and erasure steps in Phases 4 and 6.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on gated promotion into durable stores, applicable to the promotion conditions in Step 6.1.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the lifecycle ledger in Step 1.2 and the event record in Step 6.3.
- `advanced_task_guides/design-architecture/guide_SchemaFlexibilityandEvolution.md` — companion guidance on schema versioning and migration, applicable to the version continuity check in Step 5.3.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control loops and declared exit conditions, applicable to the terminal states in Step 1.3.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, II, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Provider-managed conversation state, compaction, and session continuity*

1. OpenAI conversation state — https://developers.openai.com/api/docs/guides/conversation-state
2. OpenAI data controls — https://developers.openai.com/api/docs/guides/your-data
3. OpenAI compaction guide — https://developers.openai.com/api/docs/guides/compaction
4. Anthropic context-engineering cookbook — https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools
5. Gemini Live session management — https://ai.google.dev/gemini-api/docs/live-api/session-management
6. OpenAI migration guidance — https://developers.openai.com/api/docs/guides/migrate-to-responses

*Retention, erasure, and data protection*

7. ICO right to erasure guidance — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/
8. EDPB Opinion 28/2024 — https://www.edpb.europa.eu/system/files/2024-12/edpb_opinion_202428_ai-models_en.pdf

*Cache lifetime, invalidation, and hostile durable content*

9. Gemini context caching — https://ai.google.dev/gemini-api/docs/generate-content/caching
10. AgentPoison, NeurIPS 2024 — https://neurips.cc/virtual/2024/poster/94715
11. PoisonedRAG — https://arxiv.org/abs/2402.07867

*Lifecycle instrumentation*

12. OpenTelemetry GenAI agent spans — https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md
13. OpenTelemetry GenAI attribute registry — https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/

*Context construction and long-horizon agent harnesses*

14. Anthropic context engineering — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
15. Anthropic memory tool — https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
26. Anthropic, *Harness design for long-running application development* — https://anthropic.com/engineering/harness-design-long-running-apps (verified during conversion)

*Checkpointing, replay, and durable execution*

16. LlamaIndex workflow checkpointing — https://developers.llamaindex.ai/python/examples/workflow/checkpointing_workflows/
17. LlamaIndex memory documentation — https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/memory/
18. LangGraph checkpointers — https://docs.langchain.com/oss/python/langgraph/checkpointers
19. LangGraph time travel — https://docs.langchain.com/oss/python/langgraph/use-time-travel
20. Temporal event-history documentation — https://docs.temporal.io/encyclopedia/event-history/event-history-python
21. Temporal workflow versioning — https://docs.temporal.io/develop/python/workflows/versioning
22. Temporal on idempotency — https://temporal.io/blog/idempotency-and-durable-execution

*Durable memory tiers and promotion*

23. Letta memory documentation — https://docs.letta.com/configuration/memory
24. Mem0 paper — https://arxiv.org/abs/2504.19413
25. Zep paper — https://arxiv.org/abs/2501.13956
