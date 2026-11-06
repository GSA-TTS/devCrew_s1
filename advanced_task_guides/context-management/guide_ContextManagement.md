# Context Management

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Context management constitutes the task family of deciding what occupies a model's context window at each call, under an accounted token budget, and of detecting when the window's contents have become the cause of a failure rather than the means of a solution. This guide provides AI agents with a governance procedure rather than a survey of techniques: it partitions the budget by purpose, bounds each partition, declares what is evicted when a partition overflows, and holds the assembler's budget veto above any model preference. It specifies a selection ladder across four operation families, writing state out of the window, selecting what returns, compressing what must stay, and isolating work into a separate context, each entered on an observable condition and charged with a stated cost. It names four distinct context failure modes, overflow, distraction, contradiction, and staleness, and gives each a detection signal and a distinct remedy, because a single remedy applied to all four repairs only the first. It requires utilization measurement, since a full window is not a used window, and it governs the lifecycle across context boundaries through an explicit handoff record. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures to ensure that window occupancy is a decision with evidence behind it rather than an accumulation.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Context management**: The controlled construction, ordering, bounding, mutation, and disposal of the information supplied to a model at each inference or action. It governs instructions, tool definitions, tool results, retrieved evidence, working state, conversation history, memory records, and policy constraints as one accounted resource, and it optimises the smallest set of high-signal units likely to produce the required behaviour rather than the largest set the window will accept [1].

**Context window**: The token sequence accepted by one model call. It is a transport, not a store. Its capacity is address space; it holds whatever was serialized into it for that call and retains nothing afterward. This definition is adopted unchanged from the working-memory guidance in the memory-management category and is load-bearing throughout this guide.

**Working set**: The bounded selection of content assembled for one model call, drawn from durable stores that outlive it. The working set is what occupies the window; it is never the system's record of anything.

**Durable store**: Any location outside the window that survives the call: a checkpoint, a file, an artifact store, a relational or vector index, a graph, an episodic or semantic memory store, or an event log. Every element of the working set must trace to a durable store or to a trusted configuration source.

**Context package**: The complete serialized input for one call, comprising every partition in declared assembly order together with the accounting record naming what was admitted, what was excluded, and why.

**Context contract**: The declaration, fixed before assembly, of the model and tokenizer in use, the total window capacity, the output reserve, the partition set with a numeric bound on each, the protected set, the eviction order per partition, the trust classes admissible into each partition, and the terminal states permitted when the budget cannot be satisfied.

**Context budget**: The usable input allowance, computed as total window capacity minus the output reserve and operational headroom. It is an accounted resource with a ledger, not an upper limit discovered on rejection.

**Partition**: A named region of the context budget reserved for one purpose, carrying a maximum token count, a minimum floor where the purpose is protected, an admission rule, and an eviction order. An unpartitioned budget is consumed by whatever grows fastest, which in tool-using agents is tool output.

**Output reserve**: Tokens withheld from the input budget for the model's response, its reasoning, and any tool-call serialization the response may carry. The reserve is subtracted first and is never borrowed against.

**Protected atom**: A content element that must survive every eviction, compaction, and truncation without loss: the task objective, the success criteria, the standing and safety constraints, the current plan step, the latest value of every open variable, the unresolved error state, the outstanding approvals, and the side-effect ledger. The term is adopted from the working-memory guidance and its membership list is unchanged.

**Admission gate**: The deterministic pipeline every candidate unit passes before entering a partition: size and protocol validation, trust and sensitivity classification, authorization filtering, sanitization, injection scanning, provenance binding, tokenizer-exact counting, and partition assignment. Relevance is judged only after admission, never in place of it.

**Assembly order**: The fixed sequence in which partitions are serialized into the window. Order is a control, not a formatting preference, because position affects whether admitted content is used.

**Eviction**: The removal of a unit from the working set under a declared priority order, with the unit either externalized to a durable store and replaced by a reference, or discarded outright with a recorded reason code.

**Compaction**: The lossy reduction of the working set under measured budget pressure, performed from durable state and source references rather than from the transcript, and validated against a preservation manifest before use.

**Write, select, compress, isolate**: The four operation families available when a partition is under pressure, defined respectively as saving content outside the window, pulling content into the window, retaining only the tokens the task requires, and splitting work across separate windows.

**Utilization**: The proportion of admitted units that a supported output claim, a tool call, or a state update actually cited or consumed. Utilization is measured per partition and per admission rule, and it is the only evidence that corrects an admission policy.

**Overflow**: The failure mode in which the window cannot hold what the task needs. Detected by budget arithmetic before the call, never by a provider error after it.

**Distraction**: The failure mode in which admitted but irrelevant content displaces attention from relevant content, so the model uses the wrong material or none of it while the correct material is present.

**Contradiction**: The failure mode in which the window holds mutually inconsistent content, both current and authoritative, and the model selects between them arbitrarily and without disclosure.

**Staleness**: The failure mode in which superseded content remains present and is treated as current, so an outdated value drives a decision that a fresh value would have changed.

**Supersession**: The replacement of one unit by a newer authoritative version of the same unit. The superseded version leaves the working set immediately and survives only as lineage in a durable store.

**Freshness**: The declared interval during which an observation may be treated as current, expressed as an observation timestamp and an expiry timestamp. Use past expiry is a staleness event, not a judgement call.

**Trust class**: The provenance-derived label attached to every unit naming the authority of its source, distinguishing trusted configuration, an authenticated principal, a system of record, an unauthenticated external document, a tool result, and a model-generated inference. Trust class determines which partition a unit may enter and whether it may instruct.

**Context boundary**: Any point at which the window is discarded and reconstructed: a compaction, a session end, a sub-agent dispatch, a model or provider switch, or a process restart.

**Handoff record**: The bounded state package written at every context boundary, carrying the contract version, the protected set, the durable-store references, the open questions, the remaining budget, and the exact next decision, and requiring explicit acknowledgement by the receiver.

**Marginal utility per token**: The estimated contribution of a candidate unit to task completion divided by the tokens it consumes. It is the admission criterion when a partition is contested, and it is estimated before the call and corrected by measured utilization afterward.

**Reason code**: A normalised categorical label recorded with every admission, exclusion, eviction, compaction, and isolation event, drawn from a closed vocabulary so that admission policy is analysable without reading prose logs.

### 1.2 The Window as Transport and the Agent-Layer Boundary

**The distinction that carries the method**: The context window is the working set assembled for one model call, drawn from durable stores that outlive it. It is not memory. Systems that treat it as memory lose state at every boundary, because the boundary discards exactly the thing they were using as the record. Presence in the window is not storage, and absence from the window is not loss: a checkpoint, an artifact manifest, or an index record may be authoritative state while never appearing in a prompt, and a transcript may carry superseded values, completed subplans, and abandoned reasoning that are state in no sense at all. Every guide in this category assumes this separation, and the failure modes in Phase 4 are consequences of violating it.

**What follows from it**: The window has no consistency guarantee, no retention, and no identity. No value may be read back from the window as authority, no budget counter may be maintained inside it, and no decision may depend on content persisting across a compaction unless that content also sits in a durable store. The durable store is the record; the window is a rendering of a selection from it, regenerated on every call.

**Capacity is not usability**: Advertised window size states how many tokens the interface accepts, not how many the model uses reliably. Reported evaluations find that information positioned near the beginning or end of a long input is used more reliably than information in the middle [2], and that measured degradation grows with input length within advertised limits rather than at them [3]. One 2026 evaluation retrieved during this conversion reports that frontier models acting as safety monitors miss a dangerous action 2 to 30 times more often when it appears after 800,000 tokens of benign activity than when it appears alone [4]. These findings do not cover every workload and do not license a fixed universal threshold. They do refute the inference that content fitting inside the window is therefore reliably used, which is the inference an agent makes whenever it fills the window because the window accepted the tokens.

**The agent-layer boundary**: Two mechanisms adjacent to this task family sit below the agent layer and are not executable here. The first is the serving-side key-value cache, whose block allocation, fragmentation, preemption, and eviction the model server owns and no application agent can read or direct [5]. The second is the attention computation that produces the position effects above, which no runtime tool exposes. This guide carries the agent-layer surrogates for both: prefix stability discipline with scoped cache keys and provider-reported cache-read and cache-write token accounting in place of physical cache control [6][7][8], and measured admission, ordering, and utilization policy in place of attention inspection. Both mechanisms are named here as background because misattributing an agent-layer failure to them wastes diagnosis. The agent-layer surrogates for the first are specified in depth by the cache-aware sibling guidance in this category, which stops at the same boundary; the second has no sibling that reaches below it.

**Prompt caching is an economic optimisation, not a store**: Cached content still enters the window, still occupies the budget, and still causes distraction, staleness, and contradiction. A cache hit never bypasses an authorization check, a freshness check, or an admission rule. Cache keys must carry tenant, authorization scope, model identifier, prompt version, tool-schema version, and policy version, and must invalidate on source deletion, permission change, policy change, tool change, and expiry.

### 1.3 The Context Budget as a Partitioned Resource

The budget is computed, partitioned, and enforced before any candidate is ranked. The usable input budget equals total window capacity minus the output reserve minus operational headroom for serialization overhead and provider variance. Agents must set the output reserve to at least the 95th percentile observed response length for the task class, and operational headroom to at least 3 percent of total capacity. Both are subtracted first, and neither is borrowed against under pressure.

The remainder is divided among named partitions. An unpartitioned budget is not a budget: whichever content class grows fastest consumes it, and in tool-using agents that class is tool output, which crowds out instructions and working state without any decision having been taken. Every partition carries a maximum, a floor where the purpose is protected, an admission rule naming which trust classes may enter, and an eviction order naming what leaves first when the maximum is reached.

**Default partition table**: The shares below are deployment defaults for a general tool-using agent, recalibrated per task class against measured utilization under Phase 5.

| Partition | Default share of input budget | Floor | Admission rule | Eviction order when full |
| :-- | :-- | :-- | :-- | :-- |
| Instructions and policy | 5 to 10 percent | Hard floor, never evicted | Trusted configuration only, never tool output or retrieved text | None; overflow here halts the call |
| Tool definitions | 5 to 15 percent | 1 tool | Trusted configuration, schema-validated | Narrow schemas, then drop tools unreachable from the current plan step |
| Working state | 10 to 20 percent | All protected atoms | Deterministic projection of the state object | Non-protected fields by ascending recency of change |
| Retrieved evidence | 25 to 40 percent | 0 | Authorization filter first, relevance rank second | Lowest marginal utility per token first |
| Tool results | 15 to 30 percent | 0 | Size-capped, schema-validated, externalized above the cap | Oldest result pairs first, each replaced by a reference |
| Conversation history | 10 to 25 percent | Last user turn | Deduplicated turn pairs | Compact oldest first, protected atoms lifted out beforehand |
| Output reserve | Subtracted before partitioning | Full reserve | Not applicable | Never reallocated |

**Enforcement rules**: Token counts are computed with the target model's tokenizer after serialization, never estimated from character counts, whose token ratio varies by more than a factor of 3 across languages and modalities. A partition exceeding 100 percent of its maximum triggers that partition's eviction order and nothing else; eviction never crosses partition lines, because a cross-partition eviction is how a growing tool result silently removes a standing constraint. Where total assembly still exceeds the input budget after every partition has run its eviction order, the call is not issued: the assembler returns an overflow verdict carrying the per-partition ledger, and Phase 3 selects an operation. Blind truncation from the front or the middle of a serialized package is prohibited without exception, because it removes content the accounting cannot name.

**Contested admission**: Where two candidates compete for the last tokens of a partition, admission uses marginal utility per token, combining evidential coverage, source authority, freshness, and diversity against token cost. Where the estimate cannot separate them by more than 10 percent, the assembler admits the more recent authoritative unit and records the tie with a reason code, so the utilization measurement in Phase 5 has a case to adjudicate.

### 1.4 Execution Tier Partition

Context management is a hybrid capability, and most of its production failures are misassignments of work across three execution tiers. The deterministic tier owns token accounting, partition enforcement, assembly order, eviction execution, and utilization measurement, because these require exactness, reproducibility, and auditability that inference cannot supply. The model tier owns relevance and salience judgement and summarisation, because deciding what an open-vocabulary unit means for a task is covered by no rule. The hybrid tier is the handoff between them: the model proposes a ranking or a summary, software validates it against the budget and the preservation manifest, and software holds authority wherever the two disagree. The assembler holds the budget veto. A model preference never exceeds a partition bound, and a model assertion that a unit is important is an input to ranking, never an exemption from accounting.

**Tier ownership by artifact**:

| Artifact | Owning tier | Authority where the tiers disagree |
| :-- | :-- | :-- |
| Token counts, budget ledger, and partition bounds | Deterministic | Deterministic; a model estimate of remaining budget is advisory only |
| Partition assignment and admission gate verdicts | Deterministic | Deterministic; an unauthorized unit is rejected regardless of relevance |
| Assembly order and placement of protected atoms | Deterministic | Deterministic; ordering is policy, not a model preference |
| Eviction execution and reason codes | Deterministic | Deterministic; the eviction runs regardless of model objection |
| Freshness expiry, supersession, and staleness detection | Deterministic | Deterministic; a model claim that a value is current is not evidence |
| Contradiction detection between structured units | Deterministic | Deterministic; conflicting current values are surfaced, never silently reconciled |
| Utilization measurement and citation binding | Deterministic | Deterministic; utilization is computed from citation identifiers, never asserted |
| Cache key scoping and invalidation | Deterministic | Deterministic; a hit never bypasses authorization or freshness |
| Relevance and salience ranking of admitted candidates | Model | Model proposes; the partition bound still binds absolutely |
| Summarisation and abstractive compaction | Model | Model drafts; the preservation manifest check may reject the draft |
| Contradiction adjudication between unstructured sources | Hybrid | Model proposes precedence; deterministic authority policy decides, and unresolved conflict is disclosed |
| Isolation scope for a sub-agent dispatch | Hybrid | Model proposes the decomposition; deterministic budget and permission scoping bind the child |

***

## II. Operational Framework: Governed Window Occupancy Under a Partitioned Token Budget

The framework produces one auditable decision per model call: which units occupy the window, in what order, at what token cost, and on what recorded grounds. Phases 1 and 2 run before every call. Phase 3 runs when a partition is under pressure. Phase 4 runs at every turn boundary and on every unexpected output. Phase 5 runs asynchronously over completed calls and feeds corrections back into Phase 2. Phase 6 runs at every context boundary. The framework does not restate the sibling techniques in this category; it decides which of them applies and holds the accounting that makes the decision reviewable.

### Phase 1: Context Contract and Budget Partitioning

**Objective**: Fix the context contract, compute the budget, and bound every partition before any candidate unit is considered, so that occupancy is allocated by declaration rather than by whichever content class grows fastest.

#### Step 1.1: Declare the Context Contract and Name the Durable Store Behind Every Partition

**Required Actions**:

- Record the model identifier, the tokenizer identifier, and the total window capacity for the call class, pinning all three per run so a provider change is detectable rather than silent.
- Enumerate the partitions the task class requires, and for each name the durable store from which its content is drawn and to which evicted content returns.
- Reject any partition whose content has no durable store behind it, since content that exists only in the window is lost at the first boundary.
- Classify each partition by the trust classes it admits, and mark the partitions that may carry instructions, which are the instruction partition and the policy partition only.
- Declare the terminal states available when the budget cannot be satisfied: reduced scope, isolation into a child context, escalation, or a declared abstention naming what could not be admitted.

**Required Outputs**:

- A context contract record naming model, tokenizer, capacity, and contract version.
- A partition inventory with a named durable store and an admitted trust class list per partition.
- A terminal state list covering every case in which assembly cannot succeed.

**Quality Checkpoints**:

- Every partition names exactly 1 durable store or trusted configuration source; a partition without one halts contract approval.
- No partition outside instructions and policy admits instruction-bearing content; a tool result or retrieved document carrying imperative text is data in every other partition.
- The contract distinguishes an abstention from a failure, so an unsatisfiable budget is reportable rather than concealed by truncation.

***

#### Step 1.2: Compute the Budget and Bound Every Partition

**Required Actions**:

- Subtract the output reserve, set at or above the 95th percentile observed response length for the task class, and subtract operational headroom of at least 3 percent of total capacity.
- Allocate the remaining budget across partitions as absolute token counts, not as percentages evaluated at serialization time, so the bound is checkable before content exists.
- Assign each partition a floor equal to the tokens its protected content requires, and verify that the sum of all floors does not exceed 60 percent of the input budget.
- Cap any single tool result at 5 percent of the input budget by default, externalizing the remainder to a durable store and admitting a reference and a manifest in its place.
- Record the allocation as a ledger the assembler reads at run time rather than as prose in a system prompt.

**Required Outputs**:

- A budget ledger with total capacity, output reserve, headroom, input budget, and a token maximum and floor per partition.
- A per-unit size cap for tool results and retrieved documents, with the externalization threshold stated in tokens.

**Quality Checkpoints**:

- Every partition carries a numeric maximum and a numeric floor; a partition bounded only in prose is treated as unbounded and halts assembly.
- The sum of partition maxima does not exceed the input budget; an over-allocated ledger is rejected before any call.
- The sum of floors does not exceed 60 percent of the input budget, above which no partition retains room to admit new evidence and the contract is re-scoped.

***

#### Step 1.3: Declare the Protected Set and the Per-Partition Eviction Order

**Required Actions**:

- Enumerate the protected atoms explicitly: objective, success criteria, standing and safety constraints, current plan step, latest value of every open variable, unresolved error state, outstanding approvals, and the side-effect ledger.
- Write a total eviction order within each partition, so that every eviction decision is deterministic and reproducible rather than resolved at run time by judgement.
- State for each eviction whether the unit is externalized and replaced by a reference or discarded, and assign the reason code recorded in either case.
- Declare the compaction trigger as a numeric occupancy threshold, defaulting to 80 percent of a partition's maximum, rather than waiting for the partition to overflow.
- Prohibit eviction of any protected atom under every operation, and route a protected atom that cannot fit to re-scoping rather than to removal.

**Required Outputs**:

- A protected set enumeration with a durable-store reference for each atom.
- A per-partition eviction order, complete and totally ordered, with a reason code per position.
- A numeric compaction trigger per partition expressed as a percentage of that partition's maximum.

**Quality Checkpoints**:

- The eviction order for each partition is total, so no two units can tie and force a run-time judgement.
- No protected atom appears anywhere in an eviction order; its presence there is a contract defect that halts approval.
- The compaction trigger fires below 100 percent occupancy, so compaction runs under pressure rather than after overflow.

***

### Phase 2: Assembly and Admission

**Objective**: Assemble the context package for one call so that every admitted unit passed an authorization and provenance gate, occupies a declared partition, and sits in a position chosen by policy rather than by arrival order.

#### Step 2.1: Filter Every Candidate Through the Admission Gate Before Any Ranking

**Required Actions**:

- Apply authorization, tenant, purpose, region, classification, and validity filters to the candidate pool before any relevance score is computed, since a highly relevant unauthorized unit is ineligible rather than merely low-priority [9].
- Assign each surviving candidate a trust class, and route every candidate outside trusted configuration into a data partition where it is structurally delimited and declared unable to alter instructions, permissions, or tool policy [10][11].
- Validate size, schema, and encoding, sanitize active content and hidden text, and scan for injected instructions, quarantining any candidate that fails rather than admitting it with a warning.
- Bind provenance to each candidate: source identifier, source version, content hash, observation timestamp, expiry timestamp, and the extraction that produced the unit.
- Count each candidate's tokens with the pinned tokenizer after serialization into its rendered form, not before, and attach the count to the candidate record.

**Required Outputs**:

- An eligible candidate pool with trust class, provenance, expiry, and exact token count per candidate.
- A quarantine record naming every rejected candidate and its rejection reason code.

**Quality Checkpoints**:

- Authorization filtering precedes ranking in every retrieval channel; a pipeline that ranks first and filters after is rejected at review.
- Every admitted candidate carries a complete provenance record and a non-null expiry; a candidate missing either is quarantined, not admitted.
- 100 percent of admitted units outside the instruction and policy partitions are structurally marked as data.

***

#### Step 2.2: Rank Admitted Candidates and Serialize in Declared Assembly Order

**Required Actions**:

- Rank within each partition independently, using the model tier for relevance and salience judgement and the deterministic tier for authority, freshness, and diversity, and combine them by the declared marginal-utility rule.
- Deduplicate near-identical units before ranking, since two renderings of one fact consume two allocations and raise the apparent evidence count without raising coverage.
- Serialize partitions in a fixed order that places instructions and policy first, working state and the current request next, evidence after them, and volatile turn content last, so that stable prefixes precede volatile ones and cache reuse is preserved.
- Place the units most likely to be needed at the boundaries of the evidence partition rather than in its interior, and record the position assigned to each unit for later utilization analysis.
- Assign every evidence unit a citation identifier bound to its source and exact span, so that use of the unit is measurable rather than inferred.

**Required Outputs**:

- A ranked, deduplicated admission list per partition with a position index per unit.
- A serialized context package in declared assembly order.
- A citation identifier map linking every evidence unit to its source and span.

**Quality Checkpoints**:

- Assembly order is identical across calls of the same task class; an order that varies with candidate arrival breaks both cache reuse and position analysis.
- No two admitted units in one partition share a content hash; duplicates are removed before serialization.
- Every evidence unit carries a citation identifier; an uncited unit cannot be scored in Phase 5 and is not admitted.

***

#### Step 2.3: Enforce the Budget at Serialization and Execute Eviction

**Required Actions**:

- Compare each partition's serialized token count against its maximum, and run that partition's declared eviction order until it fits, recording a reason code for every eviction.
- Externalize evicted units above the reference threshold to a durable store and admit a reference and a one-line manifest in place of the content, so recovery is exact rather than reconstructed.
- Verify pairing invariants before the call: every tool-call identifier has its matching result or an explicit cleared-result placeholder, and no orphaned result or dangling call remains.
- Refuse the call where any partition remains above its maximum after its eviction order is exhausted, returning an overflow verdict with the per-partition ledger rather than truncating.
- Emit the assembly record: partition occupancies, admitted unit identifiers, excluded unit identifiers with reasons, position indices, cache status, and the total input token count.

**Required Outputs**:

- A validated context package within every partition bound.
- An eviction log with a reason code and a durable-store reference per evicted unit.
- An assembly record sufficient to reconstruct exactly which context produced the response.

**Quality Checkpoints**:

- Every partition's serialized count is at or below its maximum at call time; a single breach blocks the call.
- 100 percent of tool-call identifiers are paired with a result or a declared placeholder; an unpaired identifier blocks the call.
- The assembly record reconstructs the exact package for 100 percent of calls; a run that cannot answer which context produced an answer is not releasable.

***

### Phase 3: Operation Selection Across the Four Families

**Objective**: Relieve budget pressure by selecting exactly one operation family per event, entered at the least costly rung whose observable condition holds, so that lossy and structural operations are used only where lossless ones cannot succeed.

#### Step 3.1: Read the Observable Condition and Enter the Ladder at the Least Costly Rung

**Required Actions**:

- Read the partition occupancy ledger and identify which partition crossed its compaction trigger, since the operation is selected for a partition, not for the window as a whole.
- Evaluate the ladder in order and select the first family whose observable condition holds, rather than selecting the family most familiar to the deployment.
- Record the cost the selected family carries, so that a later utilization review can compare the cost paid against the pressure relieved.
- Refuse to select a family whose condition does not hold, and escalate to re-scoping where no condition holds and the partition is still over its maximum.
- Reference the sibling guide covering the selected family for its internal procedure rather than reimplementing that procedure here.

**Operation family selection ladder**: The four families are defined as saving content outside the window, pulling content into the window, retaining only the tokens the task requires, and splitting work across separate windows [12].

| Family | Observable condition that indicates it | Cost it carries | Rung |
| :-- | :-- | :-- | :-- |
| Write | A unit exceeds the per-unit cap, or its content is not needed verbatim for the next decision, and it is exactly recoverable from a durable store | One retrieval round-trip if the content is needed again; the reference may never be followed, so the content is effectively absent | 1, lossless |
| Select | Required content is absent from the window while present in a durable store, or the coverage check reports an unaddressed subgoal | Retrieval latency and cost; low-precision selection admits distractors that cause the failure mode in Phase 4 | 2, lossless but additive |
| Compress | The partition is above its compaction trigger and no unit in it falls below the utility floor, so nothing can be evicted without losing needed material | Irreversible information loss, summary drift, and invalidation of every cached prefix downstream of the compacted region | 3, lossy |
| Isolate | A subtask's expected intermediate token volume exceeds 30 percent of the parent input budget and its result summarises to under 5 percent of that budget | Token multiplication across parallel windows, coordination overhead, and loss of anything the handoff record omits | 4, structural |

**Required Outputs**:

- A selected operation family with the partition it addresses and the condition that triggered it.
- A cost declaration naming the specific cost accepted for this event.

**Quality Checkpoints**:

- Exactly 1 family is selected per pressure event; two families applied together make the relief unattributable.
- The selected family sits at the lowest rung whose condition holds; selecting a higher rung with a lower rung available is a defect recorded for policy review.
- No compression runs while any unit in the partition remains below the utility floor, since eviction is lossless and compression is not.

***

#### Step 3.2: Execute the Selected Operation Under Its Preservation Manifest

**Required Actions**:

- Build a preservation manifest before any lossy operation, enumerating the protected atoms, the open variables and their current values, the unresolved questions, the standing constraints, the outstanding approvals, and the side-effect ledger entries that must survive intact.
- Perform compaction from the durable state object and its source references, never from the transcript, so that superseded and abandoned content is not carried into the summary as though it were current [13][14].
- Record for every summary the source unit identifiers, the covered interval, the summarising model and prompt version, the pre-compression and post-compression token counts, and a reference to the originals.
- Externalize rather than compress wherever exact wording, numeric values, identifiers, code, contractual language, or security policy is involved, since these classes do not survive abstraction.
- Scope every isolated child context explicitly: objective, allowed actions, input artifact references, budget, deadline, output schema, and data-handling restrictions, and never forward the parent transcript by default.

**Required Outputs**:

- A preservation manifest listing every element required to survive the operation.
- A compaction record or externalization record with source identifiers, token counts before and after, and a recovery path.
- A child context specification for every isolation event, carrying its own budget ledger.

**Quality Checkpoints**:

- 100 percent of preservation manifest elements are present in the post-operation working set; a single missing element rejects the operation and restores the prior state.
- No summary replaces content whose exact form is required; such content is externalized with a reference or retained verbatim.
- No child context receives the parent transcript; a dispatch carrying the full transcript is blocked and re-specified.

***

#### Step 3.3: Verify That Pressure Was Relieved and Record the Operation

**Required Actions**:

- Recompute partition occupancy after the operation and compare it against the trigger threshold that fired.
- Compare the post-operation working set against the preservation manifest element by element, and restore the prior state where any element is missing.
- Re-run the next model call and confirm that the task advanced, since an operation that relieves pressure while removing the material the task needed has traded one failure mode for another.
- Record the operation with its family, partition, tokens reclaimed, cost incurred, and verification verdict, keyed to the run and turn.
- Where the same partition triggers a third operation within 5 consecutive turns, stop selecting operations and escalate to a partition re-scoping under Phase 1.

**Required Outputs**:

- A post-operation occupancy ledger showing the partition below its trigger.
- A manifest verification verdict with per-element pass or fail.
- An operation record joinable to the utilization measurements in Phase 5.

**Quality Checkpoints**:

- The addressed partition sits below its compaction trigger after the operation; an operation that fails to clear the trigger is recorded as ineffective and escalates one rung.
- Manifest verification passes on 100 percent of elements before the working set is committed.
- No partition receives more than 2 operations within 5 consecutive turns; a third indicates the partition bound is wrong rather than the content.

***

### Phase 4: Context Failure Detection and Diagnosis

**Objective**: Determine whether the context is the cause of an observed failure and which of four distinct failure modes is present, so that a mode-specific remedy is applied instead of the single remedy that repairs only one of them.

#### Step 4.1: Run the Four-Signal Failure Sweep at Every Turn Boundary

**Required Actions**:

- Compute projected serialized tokens against the input budget and against every partition maximum before the call, so overflow is detected by arithmetic rather than by a provider rejection after the tokens have been paid for.
- Compute evidence utilization for the previous call as cited or consumed units divided by admitted units, and compare it against the coverage the assembly record claimed.
- Compare every admitted structured unit against every other on shared keyed fields, and flag any pair whose current authoritative values disagree.
- Evaluate expiry timestamps and supersession lineage for every admitted unit, and flag any unit past expiry or any superseded version present alongside its successor.
- Record all four signals on every turn regardless of whether a failure was observed, since a baseline is required to distinguish a degraded turn from a normal one.

**Required Outputs**:

- A per-turn signal record carrying projected occupancy, utilization ratio, contradiction pair count, and stale unit count.
- A rolling baseline of each signal over the last 20 turns of the same task class.

**Quality Checkpoints**:

- All 4 signals are computed on 100 percent of turns; a missing signal makes the diagnosis in Step 4.2 unavailable and is treated as an instrumentation defect.
- Overflow is detected before the call on 100 percent of occasions; a provider length rejection reaching the agent indicates the projection is not running.
- Every flagged contradiction pair and stale unit carries the identifiers of the units involved, not merely a count.

***

#### Step 4.2: Discriminate the Failure Mode Before Selecting a Remedy

**Required Actions**:

- Classify the observed failure into exactly one of four modes using the signal record, and refuse the classification "the context is too long" as a diagnosis, since that phrase names only the first mode and is routinely applied to all four [16].
- Confirm distraction by verifying that the needed unit was present and uncited, distinguishing it from a selection failure in which the needed unit was never admitted.
- Confirm contradiction by verifying that both conflicting units are unexpired and authoritative, distinguishing it from staleness, in which one is superseded and the conflict is only apparent.
- Confirm staleness by comparing the cited source version against the current canonical version in the durable store, since a plausible but outdated value produces confident wrong output with no other symptom.
- Record the mode with its evidence, and where two modes are present, remedy staleness and contradiction before distraction, because both inflate the admitted unit count that distraction is measured against.

**Context failure mode table**:

| Failure mode | What is wrong | Detection signal with threshold | Mode-specific remedy | Why the general remedy fails |
| :-- | :-- | :-- | :-- | :-- |
| Overflow | The window cannot hold what the task needs | Projected serialized tokens exceed the input budget, or any partition exceeds its maximum after its eviction order is exhausted | Enter the Phase 3 ladder at rung 1: externalize, then narrow selection, then compress, then isolate | Not applicable; this is the only mode the general remedy addresses |
| Distraction | Admitted but irrelevant content displaces attention from relevant content that is present | Evidence utilization below 40 percent while coverage exceeds 80 percent, or accuracy falling as admitted unit count rises with coverage flat | Reduce the admitted unit count, raise the admission threshold, tighten filters, and narrow tool definitions to those reachable from the current plan step | Compression retains the distractors in condensed form, so density rises while the distraction persists and becomes harder to detect |
| Contradiction | The window holds mutually inconsistent current content and the model selects between versions arbitrarily | 1 or more conflicting pairs among unexpired authoritative units on a shared keyed field | Surface the conflict explicitly with both sources and their authority ranks, apply the declared precedence policy, and escalate where precedence cannot resolve it | Compression selects one side silently and destroys the evidence that a conflict existed |
| Staleness | Superseded content remains present and is treated as current | 1 or more admitted units past expiry, or any superseded version present alongside its successor | Evict the superseded version immediately, re-select the current version, and invalidate every cache entry keyed to the old version | Compression blends stale and current values into one summary, after which the staleness is no longer detectable at all |

**Required Outputs**:

- A failure mode classification with the identifiers of the units that evidence it.
- A remedy assignment drawn from the mode-specific column, not from the general ladder.

**Quality Checkpoints**:

- Exactly 1 mode is assigned per diagnosis; a diagnosis naming no mode or two modes without an ordering halts remediation.
- No remedy is applied before the mode is recorded; applying compression to an undiagnosed failure is the defect this phase exists to prevent.
- Staleness and contradiction are remedied before distraction whenever more than 1 mode is present.

***

#### Step 4.3: Apply the Mode-Specific Remedy and Confirm Resolution

**Required Actions**:

- Execute the assigned remedy, and for staleness and contradiction execute it before the next model call rather than deferring it to the next assembly.
- Re-run the four-signal sweep after the remedy and confirm that the triggering signal returned within its threshold.
- Re-run the failed task step and confirm the output changed in the direction the diagnosis predicted, since a signal that clears without an output change indicates the diagnosis was wrong.
- Where the same mode recurs on the same task class 3 times within 20 turns, treat the recurrence as an admission policy defect and route it to Phase 5 rather than remedying it a fourth time.
- Log every diagnosis and remedy with a reason code, so that mode frequency by task class becomes a measurable property of the deployment.

**Required Outputs**:

- A remediation record with the mode, the remedy, the signal before and after, and the output change observed.
- A recurrence counter per mode per task class over a rolling 20-turn window.

**Quality Checkpoints**:

- The triggering signal is within threshold after remediation on at least 90 percent of events; below that rate the remedy assignment itself is reviewed.
- No mode is remedied more than 3 times for one task class within 20 turns without an admission policy revision being opened.
- Every remediation carries an observed output change or an explicit note that the diagnosis was not confirmed; an unconfirmed diagnosis is never counted as a resolution.

***

### Phase 5: Utilization Measurement and Admission Correction

**Objective**: Measure which admitted content the model actually used, attribute every non-used unit to the admission rule that admitted it, and correct that rule by evidence rather than by intuition, since a full window is not a used window.

#### Step 5.1: Measure Per-Unit Utilization From Bound Citation Identifiers

**Required Actions**:

- Join the response's cited identifiers, the tool calls it issued, and the state fields it updated against the citation identifier map produced in Step 2.2, marking each admitted unit as used or unused.
- Verify that each citation entails the claim attached to it, so that a citation emitted without support is not counted as utilization [18][19].
- Compute utilization per partition, per admission rule, per source, and per position index, since an aggregate figure conceals whether the problem is the rule, the source, or the placement.
- Record the token cost of unused units alongside their count, because 5 unused units of 200 tokens and 1 unused unit of 4,000 tokens are different policy problems.
- Report every utilization figure with its numerator, denominator, sample count, time window, and task stratum, and never as a bare percentage.

**Required Outputs**:

- A per-unit utilization record joined to the assembly record for each call.
- Utilization aggregates segmented by partition, admission rule, source, and position index.
- A wasted-token ledger giving the token cost of unused admissions per task class.

**Quality Checkpoints**:

- Utilization is computed from bound identifiers on 100 percent of calls; a deployment that cannot join responses to admitted units cannot correct its admission policy and is not releasable.
- Every reported figure carries its denominator and stratum; a bare percentage is rejected at review.
- Citation entailment is verified before a unit is counted as used, so unsupported citations do not inflate utilization.

***

#### Step 5.2: Attribute Non-Utilization to a Named Admission Rule

**Required Actions**:

- Trace every unused unit back to the admission rule, retrieval channel, filter, and rank position that admitted it, so the correction has a target.
- Separate the three causes of non-utilization: the unit was irrelevant and should not have been admitted, the unit was relevant but displaced by distraction, and the unit was relevant and used without being cited.
- Distinguish over-admission, in which utilization is low and coverage is complete, from under-admission, in which utilization is high and the coverage check reports unaddressed subgoals, because the corrections are opposite.
- Test position sensitivity by re-running a sample of at least 30 calls with the same admitted set in a different order, and attribute any change in utilization to placement rather than to admission.
- Escalate to the retrieval configuration owner where non-utilization concentrates in one channel, since a channel with utilization below 20 percent is a retrieval defect rather than an assembly defect.

**Required Outputs**:

- A non-utilization attribution table mapping unused units to admission rules with a cause label per unit.
- An over-admission and under-admission verdict per partition and task class.
- A position sensitivity measurement over a sample of at least 30 calls.

**Quality Checkpoints**:

- 100 percent of unused units are attributed to a named rule; an unattributable admission means the assembly record is incomplete.
- Over-admission and under-admission are never corrected in the same revision for the same partition, since simultaneous opposite corrections make the effect unmeasurable.
- Position sensitivity is measured before any admission rule is changed on the grounds of low utilization.

***

#### Step 5.3: Revise Admission Policy and Re-Measure Against a Frozen Baseline

**Required Actions**:

- Change exactly one admission parameter per revision: a threshold, a partition bound, a filter, a rank depth, or an assembly position.
- Re-run the frozen baseline set, which must include common queries, rare entities, exact identifiers, multi-hop questions, contradictory sources, missing-evidence cases, and long-history cases, and compare the candidate against the current configuration on identical inputs.
- Predeclare non-regression floors for task success, coverage, faithfulness, and citation correctness, and a maximum for input tokens per successful outcome, before the comparison is run.
- Accept the revision only where utilization rises by at least 5 percentage points, or input tokens per successful outcome fall by at least 10 percent, without breaching any non-regression floor.
- Version the admission policy, record the measurement that justified the change, and retain the prior version for rollback.

**Required Outputs**:

- A versioned admission policy with a single changed parameter and its justification.
- A paired comparison report against the frozen baseline with stratum-level results.
- A rollback record naming the prior policy version and the conditions that trigger reversion.

**Quality Checkpoints**:

- Exactly 1 parameter changed per revision; a multi-parameter change is rejected because its effect cannot be attributed.
- No revision is promoted that breaches a predeclared non-regression floor, regardless of its utilization gain.
- Every promoted revision carries a paired measurement on the frozen baseline; a revision justified by a single anecdotal improvement is not promoted.

***

### Phase 6: Lifecycle Across Context Boundaries

**Objective**: Carry the task across every point at which the window is discarded and rebuilt, so that continuity depends on a durable handoff record rather than on whichever text survived the boundary.

#### Step 6.1: Detect the Boundary Before It Is Forced

**Required Actions**:

- Monitor total occupancy against a boundary trigger set at 75 percent of the input budget by default, and open the boundary procedure at that trigger rather than at overflow.
- Treat every sub-agent dispatch, model switch, provider switch, session close, and process restart as a boundary requiring the same procedure as a compaction.
- Estimate the tokens the next 3 turns will add from the rolling average for the task class, and open the boundary early where the projection crosses the input budget.
- Confirm that every protected atom is currently persisted in a durable store, and persist any that is not before the boundary opens.
- Refuse to cross a boundary while an uncommitted side effect is outstanding, and either commit it, record it as ambiguous with its idempotency key, or abort it first.

**Required Outputs**:

- A boundary trigger record naming the trigger type and the occupancy at which it fired.
- A protected atom persistence verification with one verdict per atom.
- A side-effect reconciliation verdict covering every outstanding effect.

**Quality Checkpoints**:

- The boundary opens at or below 75 percent occupancy on at least 95 percent of occasions; a boundary forced by overflow is recorded as a detection failure.
- 100 percent of protected atoms are persisted before the boundary opens; a single unpersisted atom blocks the crossing.
- No boundary is crossed with an unreconciled side effect; the effect is committed, marked ambiguous with its key, or aborted.

***

#### Step 6.2: Write the Handoff Record and Externalize the Remainder

**Required Actions**:

- Write a handoff record carrying the contract version, the schema version, the protected set, the durable-store references for all externalized content, the open questions, the remaining budget across every dimension, and the exact next decision.
- Bound the handoff record to 10 percent of the receiving context's input budget by default, so the record itself does not consume the space it was written to free.
- Externalize every unit not carried in the handoff record to a durable store with a stable identifier, and record a manifest that lists what was externalized and where.
- Include in the handoff record what was deliberately dropped and why, since a receiver that cannot distinguish absent from never-existed will re-derive work already completed.
- Require explicit acknowledgement from the receiver, and treat an unacknowledged handoff as a failed crossing rather than a completed one.

**Handoff record template**:

```
CONTRACT_VERSION:
SCHEMA_VERSION:
BOUNDARY_TYPE:
OBJECTIVE:
SUCCESS_CRITERIA:
STANDING_CONSTRAINTS:
CURRENT_PLAN_STEP:
OPEN_VARIABLES_WITH_VALUES_AND_EXPIRY:
UNRESOLVED_ERROR_STATE:
OUTSTANDING_APPROVALS:
SIDE_EFFECT_LEDGER_REFERENCE:
EXTERNALIZED_ARTIFACT_MANIFEST:
DELIBERATELY_DROPPED_WITH_REASON:
OPEN_QUESTIONS:
REMAINING_BUDGET_BY_DIMENSION:
EXACT_NEXT_DECISION:
RECEIVER_ACKNOWLEDGEMENT:
```

**Required Outputs**:

- A handoff record conforming to the template and within its token bound.
- An externalization manifest with a stable identifier per externalized unit.
- A receiver acknowledgement or a recorded crossing failure.

**Quality Checkpoints**:

- The handoff record carries every protected atom and every field of the template; a missing field blocks the crossing.
- The record occupies no more than 10 percent of the receiving input budget; a larger record is compacted from durable state, never truncated.
- 100 percent of crossings carry an explicit acknowledgement; an unacknowledged crossing is retried or escalated, never assumed.

***

#### Step 6.3: Rehydrate After the Boundary and Verify Continuity

**Required Actions**:

- Rebuild the working set on the far side of the boundary from the durable stores and the handoff record, never from whatever transcript text survived.
- Re-run the full assembly procedure in Phase 2, including the admission gate, so that content carried across the boundary is re-authorized and re-checked for freshness rather than inherited as trusted.
- Verify continuity by comparing the objective, success criteria, standing constraints, and open variable values against the handoff record field by field.
- Re-run the four-signal sweep immediately after rehydration, since compaction is the operation most likely to introduce staleness and contradiction.
- Where continuity verification fails on any protected atom, halt the task and restore from the last verified checkpoint rather than proceeding on partial state.

**Required Outputs**:

- A rehydrated context package assembled through the full admission gate.
- A continuity verification report with one verdict per protected atom.
- A post-rehydration signal record covering all four failure modes.

**Quality Checkpoints**:

- 100 percent of protected atoms match the handoff record after rehydration; a single mismatch halts the task and triggers checkpoint restore.
- No unit crosses the boundary without passing the admission gate again; inherited authorization is a security defect, not an optimisation.
- The four-signal sweep runs before the first post-boundary model call on 100 percent of crossings.

***

## III. Implementation Guidance for AI Agents

AI agents managing context must follow systematic protocols ensuring that every token in the window was admitted by a rule, counted against a partition, and accounted for after the call. The following guidance translates the governance procedure above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Agent**: Owns the context contract, the partition inventory, and the budget ledger. It alone may amend a partition bound, and every amendment is versioned with the measurement that justified it.
2. **Admission Gate**: Applies authorization, tenant, classification, and validity filters, assigns trust classes, sanitizes and scans candidates, binds provenance, and counts tokens with the pinned tokenizer. It runs entirely in the deterministic tier and never consults a relevance score.
3. **Relevance Judge**: Ranks admitted candidates for relevance and salience and proposes what a summary must preserve. It operates in the model tier, sees only the eligible pool, and holds no authority over any bound.
4. **Context Assembler**: Holds the budget veto. It serializes partitions in declared order, executes eviction, enforces pairing invariants, refuses the call on an unsatisfiable budget, and emits the assembly record. A model preference never overrides it.
5. **Compaction Agent**: Builds the preservation manifest, drafts summaries from durable state rather than the transcript, and submits them for deterministic manifest verification. It may not commit a summary that the verification rejects.
6. **Failure Diagnostician**: Runs the four-signal sweep, classifies the failure mode, assigns the mode-specific remedy, and blocks any remedy applied before a mode is recorded.
7. **Utilization Auditor**: Joins responses to admitted units, computes utilization by partition and rule, attributes non-utilization, and proposes single-parameter admission revisions with paired baseline evidence.

**Authority Rule**: The Context Assembler holds the budget veto absolutely. Where the Relevance Judge ranks a unit as essential and the partition has no room, the unit is externalized and referenced or the task is re-scoped; the bound is never exceeded. Where the Compaction Agent's summary fails manifest verification, the prior state is restored; the summary is never committed with a warning attached.

**Workflow Execution Pattern**:

```
STATE: Phase_2_Assembly_And_Admission
ACTIONS:
  1. Apply authorization and validity filters to the candidate pool
  2. Assign trust class, bind provenance, count tokens per candidate
  3. Rank within each partition and assign citation identifiers
  4. Serialize partitions in declared assembly order
  5. Compare each partition against its maximum and run its eviction order
VALIDATION:
  - authorization_filter_precedes_ranking == TRUE
  - partition_tokens <= partition_maximum FOR ALL partitions
  - protected_atoms_present == TRUE
  - tool_call_result_pairs_matched == TRUE
  - citation_identifier_bound FOR ALL evidence_units
TRANSITIONS:
  IF all_validations_pass THEN next_state = Issue_Model_Call
  ELSE IF partition_over_maximum THEN next_state = Phase_3_Operation_Selection
  ELSE next_state = Phase_1_Contract_Rescoping
```

**Two-Phase Action Pattern**:

1. **Plan**: Compute the projected package and the per-partition ledger without issuing the call.
2. **Validate**: Confirm every partition bound, every pairing invariant, and the presence of every protected atom while the package is still cheap to revise.
3. **Execute**: Issue the call only after the ledger validates, and record the assembly record with the response.

**Approval Gate**: Human authorisation is required before any of the following, and none may be automated: amending a partition bound by more than 20 percent of its current value; promoting an admission policy revision whose paired baseline comparison covers fewer than 50 cases per stratum; compacting content classified above the deployment's declared sensitivity tier; dispatching more than 4 isolated child contexts from one parent turn; and relaxing the prohibition on blind truncation for any reason.

**Instrumentation Requirements**:

- Emit one span per assembly with partition occupancies, admitted and excluded identifiers, position indices, cache-read and cache-write token counts, and the total input token count, aligned to a general-purpose instrumentation convention rather than a bespoke schema [20].
- Default to metadata-only telemetry: record identifiers, hashes, token counts, and reason codes, and treat full prompts, retrieved content, and tool payloads as opt-in and access-controlled.
- Hold the budget ledger, the assembly record, and the handoff record in durable stores, since the loop outlives any single window.
- Count the context management machinery's own token consumption, including summarisation calls and relevance ranking calls, against the run's cost rather than treating it as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract Integrity (After Phase 1)**

- **Automated Check**: Every partition carries a numeric maximum, a numeric floor, a named durable store, and a total eviction order; the sum of maxima does not exceed the input budget; the sum of floors does not exceed 60 percent of it; no protected atom appears in any eviction order.
- **Agent Action on Pass**: Proceed to assembly.
- **Agent Action on Failure**: Halt and return the specific contract defect; no call is issued against an unbounded partition.
- **Human Review Trigger**: A protected atom that cannot fit within its partition floor, or a task class whose floors exceed 60 percent of the input budget.

**Checkpoint 2: Assembly Validity (After Phase 2)**

- **Automated Check**: Authorization filtering preceded ranking in every channel; every partition is at or below its maximum; every tool-call identifier is paired; every evidence unit carries a citation identifier; the assembly record reconstructs the package.
- **Agent Action on Pass**: Issue the model call.
- **Agent Action on Failure**: Block the call and route to operation selection or contract re-scoping; never truncate to proceed.
- **Human Review Trigger**: Any admitted unit whose authorization state cannot be determined, or any package that cannot be reconstructed from its record.

**Checkpoint 3: Operation Effectiveness (After Phase 3)**

- **Automated Check**: Exactly 1 family selected; the family sits at the lowest rung whose condition holds; 100 percent of preservation manifest elements survive; the addressed partition is below its trigger afterward.
- **Agent Action on Pass**: Commit the post-operation working set.
- **Agent Action on Failure**: Restore the prior state and escalate one rung; a partially applied compaction is never committed.
- **Human Review Trigger**: A third operation on the same partition within 5 turns, or any manifest element lost.

**Checkpoint 4: Diagnosis Validity (After Phase 4)**

- **Automated Check**: All 4 signals recorded; exactly 1 mode assigned with unit identifiers as evidence; the remedy drawn from that mode's column; staleness and contradiction remedied before distraction where multiple modes are present.
- **Agent Action on Pass**: Apply the remedy and re-sweep.
- **Agent Action on Failure**: Halt remediation; an undiagnosed failure is never remedied by compaction.
- **Human Review Trigger**: The same mode recurring 3 times for one task class within 20 turns, or a diagnosis whose remedy produced no output change.

**Checkpoint 5: Utilization Evidence (After Phase 5)**

- **Automated Check**: Utilization computed from bound identifiers on 100 percent of calls; every figure carries a denominator and stratum; 100 percent of unused units attributed to a named rule; exactly 1 parameter changed per revision.
- **Agent Action on Pass**: Promote the revision and version the policy.
- **Agent Action on Failure**: Withhold promotion and name the missing evidence; a revision justified by impression is not promoted.
- **Human Review Trigger**: Utilization below 20 percent in any retrieval channel, or a revision whose paired comparison is inconclusive.

**Checkpoint 6: Boundary Continuity (After Phase 6)**

- **Automated Check**: The boundary opened at or below 75 percent occupancy; all protected atoms persisted and matched after rehydration; the handoff record carries every template field within its token bound; the admission gate re-ran on every carried unit; the four-signal sweep ran before the first post-boundary call.
- **Agent Action on Pass**: Resume the task on the far side.
- **Agent Action on Failure**: Halt and restore from the last verified checkpoint; a partial rehydration is never continued.
- **Human Review Trigger**: Any protected atom mismatch, or a boundary forced by overflow rather than by the trigger.

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

**Error Type 1: Tool Output Crowding the Window**

- **Symptoms**: The tool result partition sits at its maximum on consecutive turns; instructions or working state are absent from the package despite being in the contract; a single result exceeds the per-unit cap; the agent repeats a tool call whose earlier result was evicted.
- **Diagnostic Steps**: Read the per-partition ledger for the last 10 turns and confirm whether the tool result partition breached its maximum or whether eviction crossed a partition line. Compare the largest single result against the per-unit cap and check whether externalization ran.
- **Resolution Protocol**: Option A, enforce the per-unit cap and externalize the result body, admitting a reference and a manifest. Option B, clear the oldest tool-use and result pairs above a token threshold, leaving an explicit placeholder so the absence is visible to the model [15]. Option C, move the tool's output through a filter that projects only the fields the plan step consumes. Option D, isolate the tool-heavy subtask into a child context whose result returns as a summary.
- **Escalation Trigger**: A partition breach caused by cross-partition eviction escalates immediately and is never resolved by retry, since it means the enforcement is wrong rather than the content. Three consecutive turns at the tool result maximum escalate to a partition re-scoping.

**Error Type 2: Compaction Loss and Summary Drift**

- **Symptoms**: A protected atom is absent after a boundary; a constraint the task previously honoured is violated; a user correction reappears as an open question; the post-compaction summary asserts a value the sources do not carry.
- **Diagnostic Steps**: Compare the post-operation working set against the preservation manifest element by element, and compare the summary's claims against the source unit identifiers it names. Determine whether the summary was drafted from the transcript rather than from durable state.
- **Resolution Protocol**: Option A, restore from the last verified checkpoint and re-run compaction from the state object and source references. Option B, replace the abstractive summary with extractive retention for the classes that do not survive abstraction, namely exact wording, numbers, identifiers, code, and policy. Option C, externalize instead of compacting and admit references. Option D, block the summarising configuration version and record the failure against it.
- **Escalation Trigger**: Any lost protected atom halts the task; this class is never resolved by regenerating the summary with the same inputs. Two manifest verification failures against one summarising version block that version from further use.

**Error Type 3: Distraction Misdiagnosed as Overflow**

- **Symptoms**: Compaction runs repeatedly and quality does not recover; utilization stays below 40 percent while coverage stays above 80 percent; the needed unit is demonstrably present and uncited; accuracy falls as admitted unit count rises with coverage flat.
- **Diagnostic Steps**: Confirm the needed unit was present in the package by identifier. Compare utilization before and after the last compaction. Count the admitted tool definitions and check whether any are unreachable from the current plan step.
- **Resolution Protocol**: Option A, raise the admission threshold and reduce admitted unit count rather than compressing, since compression retains the distractors in denser form. Option B, tighten the retrieval filters and reduce rank depth for the channel carrying the unused units. Option C, narrow tool definitions to those reachable from the current plan step. Option D, re-order the evidence partition so the highest-authority units sit at its boundaries and measure the change over at least 30 calls.
- **Escalation Trigger**: A second compaction applied to a partition already diagnosed with distraction escalates for policy review, since the remedy is being applied against the diagnosis. Utilization below 20 percent for one channel escalates to the retrieval configuration owner.

**Error Type 4: Cache-Induced Staleness and Scope Leakage**

- **Symptoms**: The response cites a source version that the durable store has superseded; a cached prefix survives a policy or permission change; content from one tenant or principal appears under another; cache-read tokens stay high after a deliberate prompt change.
- **Diagnostic Steps**: Recompute the cache key and confirm it carries tenant, authorization scope, model identifier, prompt version, tool-schema version, and policy version. Compare the cited source version against the current canonical version. Check whether invalidation ran on the last source deletion or permission change.
- **Resolution Protocol**: Option A, invalidate the affected keys, re-assemble, and record the incident. Option B, add the missing dimension to the cache key and re-key the namespace. Option C, disable prefix caching for the affected partition until the key scope is corrected. Option D, move volatile content behind the stable prefix so cache reuse and freshness stop competing.
- **Escalation Trigger**: Any cross-tenant or cross-principal cache hit is a zero-tolerance event, halts the deployment path, and is never resolved by retry. A stale citation reaching a user escalates to the data owner within the same run.

**Error Type 5: Isolation Fan-Out Cost Explosion and Handoff Loss**

- **Symptoms**: Total input tokens per successful outcome rise sharply while quality is flat; child contexts duplicate one another's retrievals; a child returns a result the parent cannot verify against any cited artifact; the parent re-derives work a child completed.
- **Diagnostic Steps**: Compare tokens per successful outcome against the single-context baseline for the same task class. Count duplicate retrievals across children by content hash. Check whether each child received a scoped handoff record or the parent transcript.
- **Resolution Protocol**: Option A, cap fan-out and merge children whose scopes overlap by more than 50 percent of their retrieval sets. Option B, deduplicate retrieval across children through a shared artifact store keyed by content hash. Option C, require every child result to cite artifacts the parent can verify, and reject uncited claims. Option D, collapse the isolation entirely where the subtask is tightly coupled to the parent, since isolation is not a way to evade a partition bound.
- **Escalation Trigger**: Tokens per successful outcome above 200 percent of the single-context baseline escalates for architecture review. A child result that cannot be verified against a cited artifact is never merged into the parent state.

**Troubleshooting Decision Tree**:

```
CONTEXT IS SUSPECTED AS THE CAUSE
├─ BUDGET DEFECT
│   ├─ Partition over maximum after eviction order → Enter operation ladder at rung 1
│   ├─ Eviction crossed a partition line → HALT; enforcement defect, not a content problem
│   └─ Blind truncation detected → HALT; restore and re-assemble from the ledger
├─ SELECTION DEFECT
│   ├─ Needed unit present and uncited → Distraction; reduce admissions, do not compress
│   ├─ Needed unit never admitted → Under-admission; widen filter or raise rank depth
│   └─ Channel utilization below 20 percent → Escalate to retrieval configuration owner
├─ CONSISTENCY DEFECT
│   ├─ Two current authoritative units disagree → Contradiction; surface both, apply precedence
│   ├─ Superseded version present with successor → Staleness; evict and re-select current
│   └─ Cited version behind canonical version → Invalidate cache keys; re-assemble
├─ COMPACTION DEFECT
│   ├─ Manifest element missing → Restore checkpoint; re-compact from durable state
│   ├─ Summary asserts unsourced claim → Block summarising version; use extractive retention
│   └─ Exact-form content abstracted → Externalize and reference instead
└─ ISOLATION DEFECT
    ├─ Fan-out cost above 200 percent of baseline → Escalate; cap fan-out
    ├─ Child result uncited → Reject the merge; require artifact citation
    └─ Parent transcript forwarded → Block dispatch; re-specify the child scope
```

### D. Performance Metrics and Continuous Learning

**Budget and Enforcement Metrics**:

- **Partition compliance**: Calls in which every partition sat at or below its maximum at issue time (target: 100 percent; any breach blocks release).
- **Pre-call overflow detection**: Overflow events detected by projection rather than by provider rejection (target: at least 99 percent).
- **Blind truncation events**: Packages truncated without an eviction record (target: 0; a single event is a release blocker).
- **Protected atom survival**: Boundaries after which every protected atom matched the handoff record (target: 100 percent).

**Utilization and Selection Metrics**:

- **Evidence utilization**: Admitted evidence units cited or consumed by a supported claim, tool call, or state update, divided by admitted evidence units (target: at least 60 percent per task class; below 40 percent triggers an admission review).
- **Wasted-token ratio**: Tokens of unused admitted units divided by input tokens (target: no more than 25 percent).
- **Coverage**: Subgoals or reference claims addressed by at least 1 admitted unit, divided by subgoals requiring evidence (target: at least 90 percent; falling coverage with rising utilization indicates over-tightened admission).
- **Citation precision**: Citations that entail their attached claim, divided by citations emitted (target: at least 95 percent).
- **Position sensitivity**: Change in utilization when the same admitted set is re-ordered, measured over at least 30 calls (target: reported per task class; a change above 10 percentage points makes assembly order a controlled parameter).

**Failure and Efficiency Metrics**:

- **Failure mode distribution**: Diagnosed events by mode, reported with counts and denominators per task class (target: reported, not optimised; a distribution that is 100 percent overflow indicates the other three signals are not instrumented).
- **Remedy effectiveness**: Remediations after which the triggering signal returned within threshold and the output changed as predicted (target: at least 90 percent).
- **Critical-fact retention**: Manifest elements present after compaction, divided by manifest elements (target: 100 percent).
- **Compaction ratio**: Pre-compaction tokens divided by post-compaction tokens, always reported paired with critical-fact retention (target: reported; a ratio without retention is not evidence).
- **Input tokens per successful outcome**: Total input tokens divided by accepted successes (target: below the pre-governance baseline at matched quality).
- **Cache hit rate and effective token savings**: Cache reads divided by eligible lookups, and eligible uncached input tokens minus billed cache-write and cache-read equivalents (target: reported with the price-book version).

**Learning and Adaptation Mechanisms**:

- **Evidence-bound policy change**: An admission rule changes only on a paired baseline comparison, never on a single observed failure.
- **Per-class recalibration**: Every threshold in this guide is recomputed per task class against observed utilization and failure distribution; the stated values are deployment defaults.
- **Failure corpus growth**: Every adjudicated context failure is added to the frozen baseline with its mode label, so that a later revision is tested against it.
- **Policy versioning**: Admission policies, partition ledgers, and summarising prompts carry versions, and every metric is joined to the version that produced it so drift is attributable.

**Human-in-the-Loop Boundaries**: Amending a partition bound by more than 20 percent, promoting an admission revision on thin evidence, compacting content above the declared sensitivity tier, exceeding the isolation fan-out cap, and relaxing the truncation prohibition are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the allocation of a bounded transport rather than the content that any particular domain places in it. Its phases hold wherever a model call draws on more content than it can hold, that content comes from stores of differing authority and freshness, and a wrong occupancy decision has a cost.

### 4.1 Cross-Domain Application Patterns

**Clinical decision support**: Partitions separate standing clinical policy, the active encounter, the patient record extract, and literature evidence, and the policy partition is never evicted. Staleness is the dominant failure mode because a superseded laboratory value or a discontinued medication reads as current, so expiry arithmetic runs on every admitted record and the supersession check precedes every call. Contradiction is disclosed rather than resolved: where two current sources disagree on an allergy or a dose, both appear with their authority ranks and the conflict is surfaced to the clinician. Compaction is restricted to narrative history; numeric values, identifiers, and orders are externalized and referenced rather than summarised.

**Legal and regulatory analysis**: The evidence partition carries clause-level units with exact spans and effective dates, and abstractive compression is prohibited across it because contractual and statutory language does not survive paraphrase. Distraction dominates, since a large corpus of superficially similar provisions crowds the correct one, so admission thresholds are tight and rank depth is shallow. The handoff record carries the full citation manifest, because a boundary that loses the span binding makes the analysis unverifiable rather than merely incomplete.

**Software engineering agents**: The tool result partition is the fastest-growing region and the one that most often invades others, so per-unit caps, externalization to the filesystem, and clearing of old tool-use and result pairs are the routine operations. Isolation is well suited here, since a build, a test run, or a dependency audit produces large intermediates the parent never needs and a short verdict it does. The protected set carries the failing test identity and the current diff scope, which are the atoms most often lost across a compaction and most expensive to re-derive.

**Industrial field operations**: Freshness intervals are short and measured in minutes, so the staleness signal fires often and the evidence partition is rebuilt rather than accumulated. The window carries the current asset state, the active procedure step, and the standing safety constraints, and everything else is referenced. Latency bounds are tight, so the operation ladder is entered at rung 1 by default and compaction is scheduled between tasks rather than mid-task.

**Financial research and reporting**: Contradiction is the dominant mode because multiple sources report the same figure under different definitions, restatement dates, and currencies, so the contradiction sweep compares keyed fields rather than free text and unresolved conflicts appear in the output. Utilization measurement matters most here, since the temptation is to admit every source that mentions the entity; the wasted-token ratio is the metric that disciplines it. Every figure carries its source version, and a cache hit never substitutes for a freshness check on a restated period.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small single-turn tasks**: Collapse the partition set to instructions, request, and evidence, retain the output reserve and the budget veto, and skip Phases 3 through 6. Where the projected package occupies less than 30 percent of the input budget on 95 percent of calls, the governance overhead exceeds its benefit and only the contract and the assembly record are retained.
- **Long-horizon autonomous runs**: Retain every phase, persist the budget ledger and protected set outside the window, write a handoff record at every boundary, and re-run the four-signal sweep after every rehydration, since staleness and contradiction accumulate across boundaries rather than within a turn.
- **High-risk or irreversible work**: Raise the evidence partition floor, prohibit abstractive compaction over any content bearing on an irreversible action, require a freshness check within the declared interval before every such action, and treat any unresolved contradiction as a blocking condition rather than a disclosure.
- **Strict latency budgets**: Shorten the evidence partition and lower rank depth rather than removing the admission gate, since removing the gate removes authorization while narrowing the partition only reduces coverage. Schedule compaction between turns and never in the critical path of an interactive response.
- **Multi-tenant deployments**: Scope every cache key, index filter, artifact store path, and telemetry export by tenant, and treat a cross-tenant admission or cache hit as a zero-tolerance event. Utilization aggregates are computed per tenant, since one tenant's corpus shape can mask another's admission defect.
- **Multi-agent deployments**: Give each agent its own contract and budget ledger, pass scoped handoff records rather than transcripts, deduplicate retrieval across children by content hash, and cap fan-out. Isolation multiplies token cost and must be justified by decomposability, not adopted to evade a partition bound [24].

***

## V. Limitations and Considerations

**The stated thresholds are deployment defaults, not measured constants**: Every numeric bound in this guide, including the partition shares, the 80 percent compaction trigger, the 75 percent boundary trigger, the 40 percent utilization floor, and the 60 percent floor ceiling, was chosen to be operable on first deployment rather than derived from a measured property of any model. Treating them as findings produces a system tuned to this document instead of to its own traffic. The mitigation is Phase 5 and the recalibration requirement in Section III.D, which oblige each deployment to recompute every threshold per task class against observed utilization and failure distribution.

**Utilization is a proxy, not a measure of use**: A unit can inform an answer without being cited, and a citation can be emitted without the unit having informed anything. Counting citations therefore both undercounts and overcounts real use, and an admission policy tuned only to citation counts will discard useful background and retain decorative sources. The mitigation is the entailment check in Step 5.1, which removes unsupported citations from the numerator, and the three-way cause separation in Step 5.2, which distinguishes uncited use from irrelevance before any rule is changed.

**Long-context findings do not transfer across models or tasks**: The position and length effects that motivate assembly order and admission discipline were measured on particular models, input constructions, and distractor densities, and their magnitude varies by model, task, and evidence placement. A deployment that imports a threshold from a published evaluation will mis-set it. The mitigation is the position sensitivity measurement in Step 5.2, run on the deployed model at production lengths, which turns assembly order into a locally measured parameter rather than an inherited one.

**Contradiction detection is only as good as the schema**: Deterministic contradiction detection compares keyed fields across structured units, and it finds nothing where the conflicting content is unstructured prose. Two documents that disagree in narrative form pass the sweep and reach the model, which resolves the conflict silently. The mitigation is the hybrid tier assignment in Section 1.4, which routes unstructured conflict to a model proposal adjudicated by a deterministic authority policy, and the requirement that unresolved conflict be disclosed in the output rather than settled inside it.

**Compaction is irreversible even when verified**: A preservation manifest confirms that named elements survived; it cannot confirm that nothing unnamed mattered. The elements a manifest omits are exactly the ones nobody anticipated needing, and they are gone. The mitigation is the ladder ordering in Phase 3, which exhausts lossless externalization before any lossy operation, together with the requirement that compaction run from durable state and source references so the originals remain recoverable even where the summary is poor.

**Governance machinery consumes the resource it governs**: Relevance ranking calls, summarisation calls, contradiction sweeps, and utilization joins cost tokens, latency, and engineering attention. On short, simple, or high-volume tasks the machinery can cost more than the occupancy errors it prevents. The mitigation is the scale adaptation in Section 4.2, which collapses the framework where projected occupancy stays below 30 percent, and the requirement in Section III.A that the machinery's own consumption be counted against the run rather than treated as free.

**Instrumentation rich enough to diagnose is rich enough to leak**: An assembly record detailed enough to reconstruct which context produced an answer contains the identifiers, spans, and often the content of sensitive material. The mitigation is the metadata-only default in Section III.A, which records identifiers, hashes, token counts, and reason codes while treating prompts, retrieved content, and tool payloads as opt-in and access-controlled, together with per-tenant scoping of every telemetry export.

**Conformance to this procedure is not adequacy of the content**: A package can satisfy every partition bound, pass every signal sweep, and carry perfectly attributed citations while the admitted evidence is wrong, the objective is misframed, or the durable store behind a partition is itself stale. The framework detects malformed occupancy, not misdirected purpose. No checkpoint here substitutes for review of the sources themselves or of the task the context was assembled to serve.

***

## VI. Conclusion and Summary

Context management is an accounting discipline before it is a technique. The window is a transport assembled for one call from durable stores that outlive it, and every failure this guide addresses follows from treating that transport as a store. A system that partitions its budget, bounds each partition, declares what leaves when a partition fills, and records what it admitted and why can answer the only question that matters after a bad answer: which context produced it. A system that lets whichever content class grows fastest consume the window cannot answer that question and cannot improve, because it has no unit of correction.

A team introducing this discipline should instrument before it optimises. Pin the tokenizer and record per-partition occupancy and an assembly record on every call, with no eviction policy at all, and observe where the budget actually goes; in tool-using agents it goes to tool output. Then declare bounds and eviction orders, and refuse the call rather than truncating. Then add the four-signal sweep, which is cheap and which immediately separates the three failure modes that the single remedy of summarisation makes worse from the one it repairs. Only after utilization is measurable should admission thresholds be tuned, and only one parameter at a time against a frozen baseline. The sibling guides in this category supply the internal procedure for each operation family; this guide supplies the decision about which one applies and the accounting that shows whether it worked.

**Key Success Factors**:

- **Transport, not store**: Every element in the window traces to a durable store, so a context boundary loses a rendering rather than the state.
- **Partitioned budget with the assembler's veto**: Each purpose carries a numeric bound and an eviction order, eviction never crosses partition lines, and a model preference never exceeds a bound.
- **Least costly rung first**: Lossless externalization is exhausted before lossy compression, and structural isolation is the last option rather than the reflexive one.
- **Four modes, four remedies**: Overflow, distraction, contradiction, and staleness are diagnosed separately, because one remedy applied to all four repairs only the first and conceals the other three.
- **Measured utilization**: Admission policy is corrected by evidence of what was actually used, not by the intuition that more evidence is safer.
- **Auditable assembly**: Every call carries a record sufficient to reconstruct exactly which context produced its answer, and a run that cannot do so is not releasable.

By following this guide, AI agents can decide what occupies the window at each step under an accounted budget, detect when the context has become the cause of a failure rather than the means of a solution, and carry a task across context boundaries without losing the state on which it depends.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source and serves as the umbrella entry for the context-management category. The corpus pointers below identify that source and the sibling guides that carry the internal procedure for individual operations, failure classes, and stores. The external references that follow are transcribed from the originating prose guide as it cited them and were not independently re-verified during conversion, except for the five entries explicitly marked as verified, whose titles and locations were retrieved during this conversion's research.

**Corpus pointers**:

- `Context Management and Processing Pipelines: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the context envelope, the trust and instruction hierarchy, the budget construction and reservation rules, the retrieval and selection decision guide, the compression and offloading discipline, the memory-type separation, the assembly ordering rules, the prompt-cache and serving-cache distinction, the stage telemetry field inventory, the metric definitions with their denominators, the failure-mode and bounded-fallback catalogue, and the production readiness checklist. Its per-technique depth on chunking, hybrid retrieval, reranking, graph retrieval, resource provisioning, and multi-agent sharing is deferred here to the sibling guides named below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — the source of the transport-not-store distinction, the protected atom set, the admission gate, the capacity bound and eviction vocabulary, and the handoff record. Its terminology is adopted here unchanged rather than re-coined.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — the memory-category umbrella. Source of the trust class, canonical record, derived artifact, and retrieval eligibility gate vocabulary used in Phases 2 and 6.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on lossy reduction under gated promotion, applicable to the compaction operation in Step 3.2.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — companion guidance on decay, expiry, and verified deletion, applicable to the eviction and staleness handling in Phases 2 and 4.
- `advanced_task_guides/memory-management/guide_HierarchicalMemory.md` — companion guidance on tiered stores, applicable to the durable stores named behind each partition in Step 1.1.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — the sibling carrying the internal procedure for the write family at rung 1 of the ladder in Step 3.1.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — the sibling carrying the internal procedure for the select family at rung 2 of the ladder in Step 3.1.
- `advanced_task_guides/context-management/guide_ContextCompression.md` — the sibling carrying the internal procedure for the compress family at rung 3 of the ladder in Step 3.1, including the preservation manifest and compression-loss testing referenced in Step 3.2.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — the sibling carrying the internal procedure for the isolate family at rung 4 of the ladder in Step 3.1, including the child scoping and fan-out limits referenced in Step 3.2 and Section 4.2.
- `advanced_task_guides/context-management/guide_ContextFailurePrevention.md` — the sibling carrying both prevention and detection in depth for the failure modes this guide diagnoses in Phase 4, and extending the four-mode taxonomy named in Phase 4 by exactly one mode, poisoning, without renaming the four. Phase 4 here carries the four-signal sweep and the mode-specific remedies at the level of the context contract; that guide carries the detection budget, the signal thresholds, and the containment procedure.
- `advanced_task_guides/context-management/guide_ContextLifecycle.md` — the sibling carrying the internal procedure for boundary detection, checkpointing, handoff, and rehydration across the boundaries Phase 6 governs at the level of the context contract.
- `advanced_task_guides/context-management/guide_HierarchicalContextArchitecture.md` — the sibling carrying scope, inheritance, and precedence across context layers, applicable to the permanence-and-scope organisation of the durable stores named behind each partition in Step 1.1.
- `advanced_task_guides/context-management/guide_ContextMemoryBlocks.md` — the sibling carrying the internal procedure for prompt-resident structured blocks, one class of durable store standing behind a partition in Step 1.1 and holding a reserved region under its budget arithmetic.
- `advanced_task_guides/context-management/guide_SlidingWindowContext.md` — the sibling carrying the internal procedure for recency-ordered eviction over a moving resident set, invoked by the per-partition eviction order declared in Step 1.3 and executed in Phase 2.
- `advanced_task_guides/context-management/guide_SemanticContextCompression.md` — the sibling carrying meaning-level reduction and its fidelity tests, applicable where the compress operation executed in Step 3.2 changes representation rather than removing units.
- `advanced_task_guides/context-management/guide_ContextStateMachines.md` — the sibling carrying explicit control states, guarded transitions, and state-determined composition, applicable to the workflow specified in Section III.A.
- `advanced_task_guides/context-management/guide_ContextStreamingProtocols.md` — the sibling carrying incremental delivery, event ordering, and reconnection, applicable to assembly in Phase 2 where candidates arrive as a stream rather than as a completed set.
- `advanced_task_guides/context-management/guide_FilesystemAsContext.md` — the sibling carrying file-backed durable stores, path contracts, and bounded reads, applicable to the externalization performed under Step 3.2.
- `advanced_task_guides/context-management/guide_ContextEditingAndToolResultClearing.md` — the sibling carrying the clearing contract, the persist-then-clear order, and the placeholder discipline behind Option B of Error Type 1 in Section III.C.
- `advanced_task_guides/context-management/guide_ContextEngineeringFrameworks.md` — the sibling carrying framework selection and the framework-boundary audit, applicable wherever the capabilities defined in Section I are supplied by a library rather than built directly.
- `advanced_task_guides/context-management/guide_KVCacheAwarePromptConstruction.md` — the sibling carrying the agent-layer surrogates named at the boundary in Section 1.2: prefix stability discipline, cache-family keys, invalidation causes, and cache-read and cache-write token accounting. The serving-side mechanism itself remains outside the agent layer in both guides.
- `advanced_task_guides/knowledge-retrieval/guide_AdvancedKnowledgeRetrieval.md` — companion guidance on retrieval configuration, applicable to the candidate pool construction preceding the admission gate in Step 2.1.
- `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md` — companion guidance on agent-driven retrieval loops, applicable to the under-admission correction in Step 5.2.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the assembly record and instrumentation requirements in Section III.A.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control loops and value-of-computation gating, applicable to the operation selection ladder in Phase 3.

**External references**: The numbering below is the numbering used by the inline markers in Sections I through IV. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Context engineering and window occupancy*

1. Anthropic, *Effective context engineering for AI agents* — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
2. Liu and colleagues, *Lost in the Middle* — https://arxiv.org/abs/2307.03172
3. Chroma, *Context Rot* — https://research.trychroma.com/context-rot
4. Martin and Roger, *Classifier Context Rot: Monitor Performance Degrades with Context Length* — https://arxiv.org/abs/2605.12366 (verified during conversion)
5. *PagedAttention* — https://arxiv.org/abs/2309.06180

*Prompt caching and prefix stability*

6. OpenAI, *Prompt caching* — https://platform.openai.com/docs/guides/prompt-caching
7. Anthropic, *Prompt caching* — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
8. Google, *Context caching* — https://ai.google.dev/gemini-api/docs/caching

*Admission, authorization, and untrusted content*

9. Pinecone, *Metadata filtering* — https://docs.pinecone.io/guides/search/filter-by-metadata
10. OWASP, *LLM01 Prompt Injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
11. Microsoft, *Input, context, and retrieval hygiene* — https://learn.microsoft.com/en-us/security/zero-trust/catalog-ai-defense-capabilities/input-context-retrieval-hygiene

*Operation families, compaction, and failure modes*

12. LangChain, *Context Engineering* — https://www.langchain.com/blog/context-engineering-for-agents (verified during conversion)
13. OpenAI, *Compaction* — https://developers.openai.com/api/docs/guides/compaction
14. Anthropic, *Context windows* — https://docs.anthropic.com/en/docs/build-with-claude/context-windows
15. Anthropic, *Context editing* — https://platform.claude.com/docs/en/build-with-claude/context-editing (verified during conversion)
16. Breunig, *How Long Contexts Fail* — https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html (verified during conversion)
17. *LongLLMLingua* — https://arxiv.org/abs/2310.06839

*Utilization, evaluation, and instrumentation*

18. RAGAS, *Faithfulness* — https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/
19. TruLens, *RAG Triad* — https://www.trulens.org/getting_started/core_concepts/rag_triad/
20. OpenTelemetry, *GenAI attribute registry* — https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
21. RAGAS, *Context precision* — https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/
22. RAGAS, *Context recall* — https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/
23. OpenAI, *Evaluation best practices* — https://developers.openai.com/api/docs/guides/evaluation-best-practices

*Isolation, durable stores, provenance, and data protection*

24. Anthropic, *Multi-agent research system* — https://www.anthropic.com/engineering/multi-agent-research-system
25. Packer and colleagues, *MemGPT* — https://arxiv.org/abs/2310.08560
26. LangChain, *Long-term memory* — https://docs.langchain.com/oss/python/langchain/long-term-memory
27. W3C, *PROV overview* — https://www.w3.org/TR/prov-overview/
28. *MCP resources specification* — https://modelcontextprotocol.io/specification/2026-07-28/server/resources
29. ICO, *How should we assess security and data minimisation in AI* — https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/guidance-on-ai-and-data-protection/how-should-we-assess-security-and-data-minimisation-in-ai/
