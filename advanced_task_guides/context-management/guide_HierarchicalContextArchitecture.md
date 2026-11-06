# Hierarchical Context Architecture

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Hierarchical context architecture constitutes the task family of stratifying an assembled context package into layers that differ in permanence and scope, and of governing what moves between those layers. This guide provides AI agents with a structured protocol for three declared layers: a system layer carrying content that changes at most once in 500 calls and applies across every principal, a session layer carrying task-scoped content that changes between once in 5 and once in 500 calls, and a step layer carrying content rebuilt on every call. It specifies an assignment rule placing every unit in exactly one layer under the more volatile of its two classifications, the two named consequences of misassignment, a serialization discipline that holds unchanged prefixes byte-identical, a per-layer budget with a one-directional borrowing rule, a coherence check that resolves cross-layer conflict by unit type rather than by layer distance, and promotion and demotion triggers separated by hysteresis. It specifies the execution-tier partition that makes the method reliable: deterministic software owns assignment enforcement, ordering, budget bounds, coherence checking, and movement execution, while model inference owns only the proposal that content has become durable enough to promote or stale enough to demote. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that stratification lowers carried cost and staleness rather than merely renaming the budget.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Hierarchical context architecture**: The stratification of the content assembled for a model call into named layers ordered by permanence and scope, together with the policy that decides which layer a unit occupies and when it moves. It answers three operational questions: which layer owns this content, what does keeping it there cost on every call, and what happens when two layers assert different values for the same thing.

**Context layer**: A named stratum of the assembled context package, defined by a declared permanence band and a declared scope class rather than by subject matter. A layer declaration fixes the permanence band as a change period in calls, the scope class as the set of calls over which the layer's serialization is identical, a maximum token share, a floor, an admissible trust-class set, a within-layer eviction order, and a within-layer serialization order.

**Permanence**: The measured rate at which a unit's serialized bytes change, expressed as a change period P in calls between successive changes. Permanence is measured, never asserted; a unit described as stable that changes every third call is volatile.

**Scope**: The set of calls over which a unit's serialized bytes are identical, expressed as one of four classes: global across the deployment, tenant or project, session or task, and step. Scope is a property of the addressee set, not of importance.

**Layer index**: The ordinal position of a layer in the stratification, counting from the most stable. Layer 0 is the system layer, layer 1 the session layer, layer 2 the step layer. A lower index means longer permanence and broader scope.

**System layer (layer 0)**: The stratum holding content with a measured change period of at least 500 calls and a scope class of tenant or broader: controlling instructions, standing policy and safety constraints, tool contracts, role definition, and verified facts that hold across every task in the deployment.

**Session layer (layer 1)**: The stratum holding content with a measured change period between 5 and 500 calls and a scope class of session or task: the objective, acceptance criteria, the plan, resolved decisions, task-scoped facts, the working state projection, and the evidence set selected for the current task.

**Step layer (layer 2)**: The stratum holding content with a measured change period below 5 calls: the current request, the latest observation, the immediate tool result, the current plan step, and any per-call derived value. Step-layer content is rebuilt on every call by construction.

**Layer assignment**: The recorded fact that a unit belongs to exactly one layer, carrying the measured permanence class, the declared scope class, the trust class, the assignment rule that produced it, and the assignment version.

**Volatility-dominant rule**: The assignment rule stating that a unit's layer index is the greater of its permanence index and its scope index. A unit stable in time but narrow in scope cannot occupy a broadly shared layer; a unit broad in scope but changing every call cannot occupy a stable layer.

**Over-stabilisation**: The misassignment placing a unit in a layer more stable than its measured permanence. Its consequence is that the unit goes stale and is carried at full token cost on every subsequent call without re-derivation, so the staleness is invisible to the assembler.

**Under-stabilisation**: The misassignment placing a unit in a layer more volatile than its measured permanence. Its consequence is that the unit is rebuilt on every step, loses continuity across calls, and, where it is serialized ahead of a stable unit, invalidates the unchanged prefix behind it.

**Assembly order**: The fixed sequence in which layers are serialized, from lowest layer index to highest. Order is a control rather than a formatting preference, and the term is adopted unchanged from the context management guidance in this category.

**Prefix boundary**: The declared byte position separating the portion of the serialized package expected to be identical across a set of calls from the portion expected to differ. A prefix boundary sits only at a layer edge, never inside a layer.

**Byte identity**: The property that a layer's serialization produces the same bytes on two calls. It is verified by comparing a hash of the layer's serialized form, not by inspecting its source.

**Layer generation**: An immutable build of a layer's content, identified by a generation number and a content hash, published by moving the layer's serving alias from generation n to generation n plus one. A generation cutover is the only sanctioned way a stable layer changes.

**Claim key**: The canonical identifier of the thing a unit asserts, independent of the wording that asserts it. Two units carrying the same claim key assert about the same subject and are therefore comparable across layers.

**Cross-layer conflict**: The condition in which two units in different layers carry the same claim key and different value hashes. It is detected deterministically before serialization, never inferred from model output.

**Unit type**: The declared kind of a unit, determining how a conflict involving it resolves. Constraint-type units are policy, standing instructions, safety limits, and authority grants. Fact-type units are observations, values, and state.

**Layer budget**: The maximum token share of the input budget a layer may occupy, together with a floor below which the layer is never reduced. The term composes with, and does not replace, the purpose partitions declared in the context management guidance.

**Borrowing**: The single-call reallocation of measured unused headroom from a more stable layer to a more volatile one. Borrowing never changes a declared bound and never runs in the opposite direction.

**Promotion**: Movement of a unit to a lower layer index. Promotion changes carrying cost and stability; it never changes authority, trust class, or authorisation. The term is adopted from the hierarchical memory guidance and carries the same movement semantics.

**Demotion**: Movement of a unit to a higher layer index, preserving at least one durable reference to the unit outside the window.

**Hysteresis**: The deliberate gap between the score required to enter a layer and the score required to remain in it, together with a minimum residence and a post-movement cooldown. The term and its purpose are adopted from the hierarchical memory guidance.

**Thrashing**: The condition in which units repeatedly cross the same layer boundary in both directions inside the movement window, so that generation cutovers consume the saving that stratification was adopted to produce.

**Reason code**: A normalised categorical label recorded with every assignment, movement, conflict, borrow, and invalidation event, drawn from a closed vocabulary so that layer policy is analysable without reading prose logs.

### 1.2 Two Orthogonal Axes and the Boundaries Against Sibling Methods

**The axis this guide owns**: Content assembled for a model call can be partitioned along more than one axis, and the axes are independent. The context management guidance in this category partitions the budget by purpose, giving instructions, tool definitions, working state, retrieved evidence, tool results, and conversation history each a bounded share. This guide partitions the same budget by permanence and scope. The two are orthogonal: a retrieved-evidence unit may be a standing reference document that changes once a year or a passage fetched for the current step, and those two belong in different layers while sharing one purpose partition.

**How the two axes compose**: Every unit carries exactly one purpose partition and exactly one layer, and the pair forms a cell. Accounting runs on both axes at once, and the binding constraint is the tighter of the two: a unit is admitted only where its purpose partition has room and its layer has room. Where the two disagree, the assembler rejects the unit and records both bounds, because silently satisfying one axis while breaching the other reintroduces exactly the uncontrolled growth that partitioning exists to prevent. Neither axis is a refinement of the other, and neither may be derived from the other.

**The boundary against storage tiering**: The hierarchical memory guidance in the memory-management category owns tiered storage: capacity and latency bounds per tier, admission and initial placement, promotion and demotion triggers, eviction under a proven durability guarantee, thrash detection, and coherence across tiers. That guidance answers where a record lives and what it costs to reach. This guide answers a different question: given that a record is reachable, which stratum of the assembled window it occupies, for how many calls, and across which set of calls its bytes are identical. A record may sit in warm remote storage and be serialized into the system layer on every call; another may sit in fast local storage and never be serialized at all. Storage tier and context layer are independent properties of the same record, and this guide does not re-derive storage policy. Where the two guides share a term, the storage definition governs the store and this guide's definition governs the window.

**The boundary against provider caching**: Layer ordering has a direct economic consequence, because provider prompt caches reuse computation only for byte-identical prefixes. This guide carries the agent-layer discipline that makes a cache hit possible: a fixed layer order, a deterministic within-layer order, and byte-identity verification above the prefix boundary. Cache key scoping, breakpoint placement economics, lifetime selection, and savings measurement are owned by the KV-cache-aware prompt-construction guidance in this category, with supporting material in the umbrella and hierarchical memory guidance, and are referenced here rather than restated.

**Model-side instruction priority is defence in depth**: Providers document a priority order among message roles, so that platform and developer content outranks user and tool content. That behaviour reduces risk and does not enforce this architecture. Layer precedence here is resolved deterministically before serialization; a model is never asked which layer wins, and a unit does not acquire system-layer authority by being placed in a system-layer position.

### 1.3 The Layer Contract and the Assignment Rule

A layer is a contract before it is a region of a prompt. Three layers are the default stratification, and a fourth is warranted only where a tenant boundary genuinely separates two populations of stable content, since each added layer adds a boundary to account for, a generation to version, and a conflict surface to check.

**Layer contract defaults**: The bands and shares below are deployment defaults for a general tool-using agent, recalibrated per task class against the measurements taken in Phase 1.

| Layer | Permanence band, calls between changes | Scope class | Maximum share of input budget | Floor | Admissible trust classes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Layer 0, system | At least 500 | Global, tenant, or project | 25 percent | Controlling instructions and tool contracts, never reduced | Trusted configuration only |
| Layer 1, session | 5 to 499 | Session or task | 45 percent | Objective, acceptance criteria, and open obligations | Trusted configuration, authenticated principal, system of record |
| Layer 2, step | Fewer than 5 | Step | 30 percent, with a floor that binds first | Current request and latest unresolved error | All classes, each carrying its provenance label |

**The volatility-dominant rule**: Every unit carries a permanence index derived from its measured change period and a scope index derived from its declared addressee set. Permanence index 0 covers a change period of at least 500 calls, index 1 covers 5 to 499, index 2 covers fewer than 5. Scope index 0 covers global, tenant, and project scope, index 1 covers session and task scope, index 2 covers step scope. The assigned layer index is the greater of the two. The rule has one motivation on each side: a unit that is stable but narrow would break the shared prefix for every principal that does not carry it, and a unit that is broad but volatile would invalidate the prefix for every principal that does.

**The cost of over-stabilisation**: A unit placed in a layer more stable than its measured permanence is re-derived only at that layer's generation cutover. Staleness exposure equals 1 minus the ratio of the unit's true change period to the layer's cutover interval. A unit whose value changes every 10 calls, placed in a layer with a 200-call cutover interval, is carrying an outdated value on 95 percent of calls, at its full token cost on every one of them, with no signal that anything is wrong. Over-stabilisation is therefore not a performance defect but a correctness defect wearing an efficiency costume, and it is the reason permanence is measured rather than declared.

**The cost of under-stabilisation**: A unit placed in a layer more volatile than its measured permanence is rebuilt on every call and loses continuity, because nothing guarantees that the rebuild reproduces the previous value. Where such a unit is serialized ahead of otherwise-stable content, it also invalidates every byte behind it, converting a reusable prefix into a recomputed one. Any unit with a measured change period of at least 50 calls found in layer 2 is flagged as under-stabilised and enters the promotion evaluation in Phase 6.

**Exactly one layer**: A unit appears in exactly one layer per call. Duplication across layers is prohibited without exception, because a duplicated unit is charged twice, updated once, and becomes the most common source of the cross-layer conflicts that Phase 5 exists to catch. Where two layers legitimately need the same content, the more stable layer carries the content and the more volatile layer carries a reference to it.

**A stratification that buys nothing**: Where the system layer serializes to fewer than 512 tokens, no provider prefix reuse is available to capture, since documented minimum cacheable prefix lengths run from 512 to 4,096 tokens depending on the model. Where the system layer is that small, stratification is still justified by staleness containment and conflict detection, but the prefix-stability argument must not be claimed, and the layer count should be reduced to two.

### 1.4 The Execution-Tier Partition

Reliability in a layered architecture comes from putting the measurement, the enforcement, and the movement in software, and confining model inference to the judgements no rule covers. This partition binds every phase of Section II.

**Deterministic tier**: Software, schema validators, and hash comparisons own layer assignment enforcement against the volatility-dominant rule; change-period measurement and its windows; scope-class validation; serialization order within and across layers; byte-identity hashing above the prefix boundary; layer budget accounting and bound enforcement; borrow accounting and its caps; claim-key extraction and cross-layer comparison; conflict detection; promotion and demotion execution; residence, cooldown, and hysteresis timers; generation cutover; thrash detection; and every metric denominator. Each of these requires exactness, reproducibility, and auditability that model inference cannot supply, and each is expressible as a counter, a comparison, or a transaction.

**Model tier**: LLM calls own the proposal that a unit has become durable enough to promote, expressed as a judgement that the content is a standing fact rather than a passing observation; the proposal that a unit has gone stale enough to demote; the normalisation of two differently worded natural-language statements to one claim key where deterministic key matching fails; and the drafting of the condensed form a unit takes when it is promoted into a more stable layer. Each requires open-vocabulary judgement over natural-language content that no deterministic rule covers.

**Hybrid tier**: Promotion is hybrid: the model proposes durability, and the assignment accountant verifies the measured change period, the scope class, the trust class, and the target layer's remaining headroom before the movement is scheduled. Semantic conflict detection is hybrid: the model proposes that two prose statements assert about the same subject, and the deterministic precedence policy decides which wins. Initial assignment of a newly created unit is hybrid: the model estimates a permanence class where no history exists, and the deterministic tier re-measures after 100 calls and reassigns without consulting the model again.

**Authority when the tiers disagree**: The deterministic tier holds authority in every hybrid step. Three rules make this concrete and are never relaxed. A model proposal never overrides a layer budget bound, and a proposal that would breach one is rejected rather than deferred. Layer assignment is validated deterministically against the measured change period and the declared scope before it is honoured, so a model's belief that content is stable does not make it stable. A model proposal never moves a unit across a trust-class boundary, so retrieved text and tool output never become system-layer instructions on a model's recommendation.

**Tier ownership by artifact**:

| Artifact | Owning tier | Authority where the tiers disagree |
| :-- | :-- | :-- |
| Change-period measurement and permanence class | Deterministic | Deterministic; a stated permanence is evidence of nothing |
| Layer assignment record and its validation | Deterministic | Deterministic; an invalid assignment is rejected regardless of relevance |
| Assembly order and prefix boundary placement | Deterministic | Deterministic; ordering is policy, not preference |
| Layer budget ledger, bounds, and borrow events | Deterministic | Deterministic; the bound binds absolutely |
| Claim-key comparison and conflict detection | Deterministic | Deterministic; a conflict is surfaced, never silently reconciled |
| Movement execution, timers, and generation cutover | Deterministic | Deterministic; the movement runs or does not run on measured state |
| Durability proposal for promotion | Model | Model proposes; every precondition is checked before scheduling |
| Staleness proposal for demotion | Model | Model proposes; a measured freshness expiry alone is sufficient without it |
| Condensed form of a promoted unit | Model | Model drafts; a preservation check may reject the draft |
| Claim-key normalisation across differing wordings | Hybrid | Model proposes equivalence; deterministic policy decides precedence |
| Initial assignment where no history exists | Hybrid | Model estimates; deterministic re-measurement overrides at 100 calls |

***

## II. Operational Framework: Stratified Context Assembly Under Declared Permanence and Scope

The framework runs as an outer configuration loop and an inner assembly loop. Phase 1 executes once per deployment and again whenever a layer contract changes. Phases 2 through 5 execute on every model call. Phase 6 executes on a declared movement window and is the only sanctioned way a stable layer's content changes.

### Phase 1: Layer Declaration and Permanence Measurement

**Objective**: Fix the layer set, its permanence and scope criteria, and its budget bounds from measured behaviour, so that assignment in Phase 2 is a lookup rather than a judgement.

#### Step 1.1: Declare the Layer Set With Permanence and Scope Criteria

**Required Actions**:

- Declare 2 to 4 layers, defaulting to the 3 in Section 1.3, and record for each a permanence band expressed as a change period in calls and a scope class drawn from the 4 declared classes.
- Justify any fourth layer by naming the two populations of stable content a tenant boundary separates; reject a fourth layer whose only justification is subject matter, since subject matter is the purpose axis.
- Declare for each layer the admissible trust classes, and prohibit tool output, retrieved text, and model-generated inference from entering layer 0 under any relevance argument.
- Declare the within-layer serialization order as a deterministic function of stable unit identifiers, never insertion order and never map iteration order.
- Declare the within-layer eviction order naming which units leave first when the layer exceeds its maximum.
- Record the layer contract under a version identifier, since every downstream measurement is meaningless without the contract it was taken against.

**Required Outputs**:

- A layer contract record carrying, per layer, a permanence band, a scope class, a trust-class allowlist, a serialization order, and an eviction order.
- A layer count between 2 and 4 with a written justification for any count above 3.
- A contract version identifier bound to every subsequent measurement and log event.

**Quality Checkpoints**:

- Every layer carries a numeric permanence band with no gap and no overlap against its neighbours; overlapping bands make assignment non-deterministic and halt the declaration.
- Every layer's trust-class allowlist is stated; a layer admitting all trust classes below layer 2 is a declaration defect.
- The within-layer serialization order is reproducible across processes; an order that depends on runtime iteration halts the declaration.

***

#### Step 1.2: Measure the Change Period and Scope Class of Every Content Class

**Required Actions**:

- Instrument the assembler to hash every candidate unit's serialized form on every call, and record the call index at which each hash changes.
- Compute the change period per unit as the median number of calls between successive hash changes over a window of at least 200 calls, and record the count of observations behind it.
- Treat a unit with fewer than 20 observed calls as unmeasured, and assign it provisionally under the hybrid rule in Section 1.4 rather than reporting a change period from a sample too small to support one.
- Determine the scope class from the addressee set rather than from intent, by testing whether the unit's serialized bytes are identical across principals, across sessions of one principal, and across calls of one session.
- Record the token cost of each unit at the target model's tokenizer, after serialization, since layer budgets are enforced in tokens and character-derived estimates vary by more than a factor of 3 across languages.
- Flag every unit whose measured change period contradicts its current placement by at least one band.

**Required Outputs**:

- A per-unit measurement record carrying change period, observation count, scope class, token cost, and current placement.
- A contradiction list naming every unit whose measured band differs from its placed band.
- A per-layer aggregate stating total tokens, unit count, and the layer's observed byte-identity rate.

**Quality Checkpoints**:

- Every unit carries either a change period backed by at least 20 observations or an explicit unmeasured marker; an unmarked estimate is treated as a measurement defect.
- Scope class is derived from a byte comparison across principals and sessions, not from a description of the unit's purpose.
- Token counts come from the target model's tokenizer after serialization; an estimate derived from character count halts the measurement.

***

#### Step 1.3: Bind the Layer Budgets and Declare the Protected Floor

**Required Actions**:

- Compute the usable input budget as total window capacity minus the output reserve minus operational headroom, adopting the reserve and headroom rules from the context management guidance rather than restating them.
- Allocate a maximum share to each layer, defaulting to 25, 45, and 30 percent for layers 0, 1, and 2, and require the three maxima to sum to no more than 100 percent of the usable input budget.
- Declare a floor per layer naming the units that are never reduced, and place the current request and the unresolved error state in the layer 2 floor so that the call always carries what it is about.
- Record, for every layer, the cell matrix against the purpose partitions declared in the context management guidance, so that a unit is admitted only where both its cell bounds hold.
- Set the borrow cap at no more than 50 percent of a lending layer's measured unused headroom and no more than 10 percent of the usable input budget on any one call.
- Set the layer 0 maximum from measured content rather than aspiration, and reduce the layer count to 2 where layer 0 serializes below 512 tokens.

**Required Outputs**:

- A layer budget record carrying a maximum, a floor, and a current occupancy per layer.
- A cell matrix binding each layer against each purpose partition with the tighter bound marked.
- A borrow policy record stating the direction, the two caps, and the reason code emitted per borrow event.

**Quality Checkpoints**:

- Layer maxima sum to no more than 100 percent of the usable input budget; a sum above 100 percent halts the deployment, since it guarantees an overflow that no eviction order can resolve.
- Every layer floor is expressed as a named unit set, not as a token count alone, so that enforcement can identify what it must not remove.
- The borrow policy permits movement only from a lower layer index to a higher one; a policy admitting the reverse direction is rejected at declaration.

***

### Phase 2: Content Assignment and Deterministic Validation

**Objective**: Place every candidate unit in exactly one layer by rule, validate the placement against measured behaviour, and attach the metadata that later phases compare across layers.

#### Step 2.1: Assign Every Unit to Exactly One Layer Under the Volatility-Dominant Rule

**Required Actions**:

- Compute the permanence index from the measured change period and the scope index from the tested addressee set, and assign the layer index as the greater of the two.
- Reject any assignment that places a unit in a layer whose trust-class allowlist excludes the unit's provenance label, regardless of the unit's measured permanence.
- Assign a unit with fewer than 20 observed calls to the layer its model-estimated permanence indicates, mark the assignment provisional, and schedule re-measurement at 100 calls.
- Resolve a unit that legitimately belongs to two layers by placing the content in the lower layer index and a reference in the higher one, never by duplicating the content.
- Record for every assignment the two indices, the rule applied, the contract version, and a reason code from the closed vocabulary.
- Emit an assignment refusal, not a default placement, for any unit whose scope class cannot be determined by byte comparison.

**Required Outputs**:

- A layer assignment table carrying one row per unit with both indices, the resulting layer, the trust class, and the reason code.
- A provisional set naming every unit assigned on an estimate with its re-measurement call index.
- A refusal list naming every unit that could not be assigned and the missing property in each case.

**Quality Checkpoints**:

- Every admitted unit appears in exactly 1 layer; a unit appearing in 2 layers halts assembly, because duplication defeats the accounting on both axes.
- No unit sits in a layer whose trust-class allowlist excludes it; a single violation of this rule at layer 0 is a security event, not a placement defect.
- Every provisional assignment carries a scheduled re-measurement; an unscheduled provisional assignment becomes permanent by neglect and is rejected.

***

#### Step 2.2: Validate Every Assignment Against Measured Behaviour

**Required Actions**:

- Compare each unit's placed band against its measured change period at every measurement window, and classify a mismatch as over-stabilisation where the measured period is shorter than the band and under-stabilisation where it is longer.
- Compute staleness exposure for every over-stabilised unit as 1 minus the ratio of its measured change period to its layer's cutover interval, and rank the misassignment list by that figure multiplied by the unit's token cost.
- Compute rebuild cost for every under-stabilised unit as its token cost multiplied by the calls per movement window, plus the bytes of otherwise-stable content serialized behind it.
- Route every mismatch to Phase 6 rather than correcting it inside the assembly loop, so that a stable layer never changes outside a declared generation cutover.
- Suspend from layer 0 immediately, without waiting for a cutover, any unit whose staleness exposure exceeds 0.5 and whose unit type is fact rather than constraint.
- Record the validation verdict per unit with its measured inputs, so that a later audit separates a rule failure from a measurement failure.

**Required Outputs**:

- A misassignment list ranked by staleness exposure multiplied by token cost.
- A rebuild cost record per under-stabilised unit naming the tokens re-derived per window and the stable bytes invalidated.
- A suspension record naming every fact-type unit removed from layer 0 outside a cutover, with its exposure figure.

**Quality Checkpoints**:

- Every misassignment carries a numeric cost, not a label; an unquantified misassignment cannot be prioritised and is treated as unvalidated.
- No correction to a stable layer is applied inside the assembly loop except a suspension, which removes content and never adds it.
- Assignment validation covers 100 percent of admitted units at every window; partial validation is reported as a coverage figure and never as a pass.

***

#### Step 2.3: Bind a Claim Key, a Trust Class, and a Freshness Interval to Every Assigned Unit

**Required Actions**:

- Derive a claim key for every unit naming the subject it asserts about, using a canonical identifier where the unit is structured and a normalised key where it is prose.
- Attach the trust class from the unit's provenance, adopting the class vocabulary from the context management guidance rather than defining a parallel one.
- Attach a freshness interval to every fact-type unit, expressed as an observation timestamp and an expiry, and treat use past expiry as a staleness event rather than a judgement call.
- Declare the unit type as constraint or fact, since Phase 5 resolves conflicts by type and an untyped unit cannot be adjudicated.
- Bind a stable unit identifier that survives promotion and demotion, so that a movement does not appear in the logs as a deletion followed by an unrelated creation.
- Refer prose units whose claim key cannot be derived deterministically to the model tier for normalisation, and record the model identifier and prompt version with the proposed key.

**Required Outputs**:

- A unit metadata record carrying claim key, trust class, unit type, freshness interval, and stable identifier.
- A normalisation record for every model-proposed claim key naming the model identifier, the prompt version, and the two wordings judged equivalent.
- An untyped list naming units that carry no declared unit type.

**Quality Checkpoints**:

- Every unit carries a claim key and a unit type; an untyped unit is excluded from layer 0 and layer 1 until typed.
- Every fact-type unit carries an expiry; a fact without an expiry cannot be shown to be current and is treated as expired at the next window.
- Model-proposed claim keys are recorded with their provenance; an unattributed normalisation is rejected, because a later conflict cannot otherwise be traced to the equivalence that produced it.

***

### Phase 3: Ordering and Prefix Stability

**Objective**: Serialize the layers in a fixed order that leaves unchanged content byte-identical across calls, and attribute every departure from that identity to a named unit.

#### Step 3.1: Serialize in Non-Decreasing Layer Order Under a Deterministic Within-Layer Order

**Required Actions**:

- Serialize layers in ascending layer index, and enforce the ordering invariant that for any two units at positions i and j with i before j, the layer index of the first is no greater than the layer index of the second.
- Order units within a layer by the deterministic function declared in Step 1.1, and reject a serialization whose within-layer order differs between two calls with identical content.
- Exclude from every layer below the step layer any value derived from the current call: timestamps, request identifiers, counters, elapsed durations, randomised orderings, and rendered relative dates.
- Place per-call values that a stable instruction refers to in the step layer and refer to them from the stable layer by name, so that the instruction text stays constant while its operand varies.
- Serialize tool contracts before standing instructions where the provider's own prefix hierarchy places tool definitions first, since a layer order that contradicts the provider's render order forfeits reuse for the whole prefix.
- Emit the serialized package together with a per-layer byte offset record naming where each layer begins and ends.

**Required Outputs**:

- A serialized context package with layers in non-decreasing index order.
- A per-layer offset record giving the start byte, end byte, token count, and content hash of each layer.
- An exclusion record naming every per-call value removed from a layer below the step layer and the step-layer position it moved to.

**Quality Checkpoints**:

- The ordering invariant holds for 100 percent of serialized units; a single inversion halts the call, because one volatile unit ahead of the stable layers invalidates all of them.
- Two calls with identical layer content produce identical within-layer order; a difference indicates a non-deterministic order and halts serialization.
- No layer below the step layer contains a value derived from the current call; a single such value converts a stable layer into a volatile one at full stable-layer cost.

***

#### Step 3.2: Place the Prefix Boundary and Verify Byte Identity Above It

**Required Actions**:

- Place the prefix boundary at the end of the highest-index layer whose content is expected to be identical across the current call set, and never inside a layer.
- Declare at most 4 boundaries in one package, since providers document a maximum of 4 cache breakpoints per request and additional boundaries buy nothing.
- Compute a hash of each layer's serialized bytes on every call, and compare it against the hash recorded for the layer's current generation.
- Treat a layer 0 hash change outside a declared generation cutover as an invalidation event, record it with a reason code, and do not suppress it by re-baselining the hash.
- Track the layer 0 byte-identity rate over a rolling window of 200 calls, target at least 99 percent, and halt promotion of any new configuration where the rate falls below 95 percent.
- Defer cache key scoping, lifetime selection, and savings computation to the prompt-caching treatment in the context management and hierarchical memory guidance rather than deciding them here, and never share a prefix across authorization scopes on the strength of a byte match alone.

**Required Outputs**:

- A boundary placement record naming each boundary's layer edge and the call set over which identity is expected.
- A per-call layer hash record with a comparison verdict against the current generation.
- A rolling byte-identity rate per layer over the declared window.

**Quality Checkpoints**:

- Every boundary sits at a layer edge; a boundary inside a layer splits a unit set that moves together and is rejected.
- Boundary count does not exceed 4; a package declaring more is rejected at serialization.
- Layer 0 byte identity holds on at least 99 percent of calls in the window; below 95 percent, configuration promotion halts and Step 3.3 runs before any further call is optimised.

***

#### Step 3.3: Attribute Every Unplanned Invalidation to a Named Unit

**Required Actions**:

- Diff the current layer serialization against the generation's recorded serialization at unit granularity, and name the first unit whose bytes changed.
- Classify each invalidation as a legitimate generation cutover, an under-stabilised unit resident in a stable layer, a non-deterministic serializer, or a per-call value that escaped the Step 3.1 exclusion.
- Rank attributed units by invalidations per 200 calls multiplied by the stable bytes serialized behind them, since a small unit early in the package costs more than a large one late.
- Route units invalidating at least 5 times per 200 calls to the demotion evaluation in Phase 6, and route non-deterministic serializers to the error handling in Section III.C rather than to Phase 6.
- Record an invalidation ledger per layer carrying counts, causes, and the bytes forfeited, so that the cost of instability is a measured figure rather than an inference.
- Re-run attribution after any correction and confirm the invalidation count fell, rather than assuming the correction worked.

**Required Outputs**:

- An invalidation ledger per layer naming counts, first-changed units, causes, and forfeited bytes.
- A demotion referral list naming units invalidating at least 5 times per 200 calls.
- A post-correction attribution record showing the before and after invalidation counts.

**Quality Checkpoints**:

- Every invalidation event names a first-changed unit; an unattributed invalidation is a measurement gap and blocks the byte-identity claim for that window.
- No correction is recorded as effective without a post-correction count; an assumed fix is treated as unfixed.
- Non-deterministic serialization is escalated rather than demoted, since demoting a unit does not repair an order that varies between processes.

***

### Phase 4: Layer Budget Enforcement and Overflow Policy

**Objective**: Hold every layer inside its declared bound at serialization, resolve overflow within the layer before any cross-layer relief, and permit borrowing only in the one direction that cannot grow the permanent carry.

#### Step 4.1: Account Every Layer Against Its Bound and Its Cell

**Required Actions**:

- Count tokens per layer with the target model's tokenizer after serialization, and record occupancy against both the layer maximum and the cell bound formed with each purpose partition.
- Admit a unit only where both its layer has room and its purpose partition has room, and record the tighter of the two as the binding bound in the admission event.
- Compute unused headroom per layer as the maximum minus current occupancy, and hold it as an accounted quantity rather than an inference drawn at the moment of pressure.
- Report a per-call ledger naming, per layer, the maximum, the floor, the occupancy, the headroom, and the count of units admitted and excluded.
- Refuse to issue a call whose total assembly exceeds the usable input budget after Phases 4.2 and 4.3 have run, and return an overflow verdict carrying the ledger.
- Prohibit truncation from the front, the middle, or the end of a serialized package, since truncation removes content the accounting cannot name and silently deletes whichever layer happens to sit at the cut.

**Required Outputs**:

- A per-call layer ledger with maximum, floor, occupancy, headroom, and admitted and excluded counts.
- A binding-bound record per admission event naming which of the two axes constrained the decision.
- An overflow verdict where the package cannot be brought inside the budget, carrying the full ledger.

**Quality Checkpoints**:

- Occupancy is computed after serialization with the target tokenizer; a pre-serialization estimate is not accounting and halts enforcement.
- Every admission names its binding bound; an admission that satisfies one axis without checking the other is an accounting defect.
- No package is truncated to fit; a call that cannot be assembled inside the budget is not issued.

***

#### Step 4.2: Run the Within-Layer Eviction Order Before Any Borrowing

**Required Actions**:

- Trigger the eviction order of the layer that exceeded its maximum, and of that layer only, since a cross-layer eviction is how a growing tool result silently removes a standing constraint.
- Evict in the declared order, externalizing each evicted unit to a durable store and replacing it with a reference where the unit remains reachable, and discarding it with a reason code where it does not.
- Halt eviction at the layer's floor, and never evict a floor unit under capacity pressure; where the floor alone exceeds the layer maximum, the layer contract is wrong and the deployment halts rather than the call.
- Treat a layer 0 overflow that survives its eviction order as a configuration defect rather than a runtime condition: demote the lowest-authority layer 0 units to layer 1 as references at the next cutover, and halt the current call.
- Record every eviction with the unit identifier, the layer, the reason code, and whether a durable reference replaced it.
- Re-count the layer after eviction and confirm it sits below its maximum before proceeding, rather than assuming the order was sufficient.

**Required Outputs**:

- An eviction record per event naming unit, layer, order position, reason code, and replacement reference.
- A post-eviction occupancy figure per layer with a below-maximum verdict.
- A configuration defect report where a layer 0 overflow survived its eviction order.

**Quality Checkpoints**:

- Eviction is confined to the overflowing layer; a single cross-layer eviction is treated as a policy violation and halts the call.
- No floor unit is evicted under capacity pressure; a floor breach halts the deployment for contract repair rather than proceeding with a warning.
- Every evicted unit that remains reachable is replaced by a reference; an eviction that leaves no trace is indistinguishable from a loss.

***

#### Step 4.3: Apply the One-Directional Borrow Rule Under Its Two Caps

**Required Actions**:

- Permit a layer to borrow only from the measured unused headroom of a layer with a lower index, and refuse every request in the opposite direction without exception.
- Cap a single borrow at 50 percent of the lending layer's unused headroom and at 10 percent of the usable input budget, and reject a request exceeding either cap rather than partially satisfying it.
- Bind every borrow to the current call, and never write a borrowed allowance back into a declared bound, since a bound revised by pressure is not a bound.
- Refuse a borrow that would take the lending layer below its floor, even where the arithmetic on unused headroom alone permits it.
- Record every borrow event with the lending layer, the borrowing layer, the token quantity, both cap computations, and a reason code.
- Track the borrow rate over a rolling window of 200 calls, and where borrowing occurs on more than 20 percent of calls, return to Step 1.3 and re-derive the bounds rather than continuing to borrow.

**Required Outputs**:

- A borrow event record per occurrence with both cap computations and a reason code.
- A rolling borrow rate per layer pair over the declared window.
- A bound re-derivation referral where the borrow rate exceeds 20 percent.

**Quality Checkpoints**:

- Borrowing runs only from a lower layer index to a higher one; a reverse borrow is refused, because permanently enlarging a stable layer to relieve a transient pressure grows the carry on every future call.
- No borrow reduces a lending layer below its floor, and no borrow persists past the call that used it.
- A borrow rate above 20 percent over 200 calls triggers re-derivation of the bounds; repeated borrowing is evidence that the declared partition is wrong, not that the rule is working.

***

### Phase 5: Cross-Layer Coherence and Conflict Resolution

**Objective**: Detect every case in which two layers assert different values for the same subject, resolve it by a declared rule before serialization, and halt rather than serialize an unresolved contradiction.

#### Step 5.1: Compare Claim Keys Across Layers Before Every Call

**Required Actions**:

- Group all admitted units by claim key across every layer, and mark any key held by units in 2 or more layers as a candidate conflict.
- Compare value hashes within each candidate group, and record a cross-layer conflict where the hashes differ and a redundancy where they match.
- Treat a redundancy as a duplication defect under Step 2.1, retain the copy in the lower layer index, and replace the higher-layer copy with a reference.
- Refer prose units whose claim keys did not match deterministically to the model tier for equivalence assessment, bounded to the units already admitted rather than to the full corpus.
- Bound the comparison cost to no more than 2 percent of assembly latency, and where the bound is exceeded, reduce the comparison to constraint-type units and units above a declared token size rather than skipping it entirely.
- Run the comparison on 100 percent of admitted units at every assembly, since a conflict detected on a sample is a conflict serialized on the remainder.

**Required Outputs**:

- A claim-key group record naming every key held in 2 or more layers with its member units and value hashes.
- A conflict list separating hash-differing conflicts from hash-matching redundancies.
- A comparison cost figure per assembly against the 2 percent latency bound.

**Quality Checkpoints**:

- Coverage of the claim-key comparison is 100 percent of admitted units, or the reduced scope is recorded explicitly with the units it omitted.
- Every redundancy is collapsed to a single copy plus references before serialization; a package carrying the same value in 2 layers is charged twice for one assertion.
- Model-proposed equivalences are labelled as such in the conflict record, so that a false conflict traced later resolves to the equivalence rather than to the content.

***

#### Step 5.2: Resolve by Unit Type Rather Than by Layer Distance

**Required Actions**:

- Resolve a conflict between two constraint-type units in favour of the lower layer index, so that a volatile layer may narrow a standing constraint but never widen or repeal it.
- Resolve a conflict between two fact-type units in favour of the unit with the later observation timestamp, which is normally the higher layer index, and remove the superseded copy from the package rather than leaving it outranked.
- Apply intersection semantics where the conflicting field is a permission, a data scope, or a tool allowlist, so that a narrower layer restricts and never expands.
- Apply deny-overrides semantics where any conflicting unit expresses a prohibition, regardless of which layer carries it.
- Resolve a conflict between a constraint-type unit and a fact-type unit carrying the same claim key by rejecting the pairing, since a value and a rule about that value are different claims and must carry different keys.
- Record every resolution with the winning unit, the losing units, the operator applied, and a reason code, so that a later audit can replay the decision.

**Cross-layer resolution operators**:

| Conflicting field kind | Operator | Winner | Rationale |
| :-- | :-- | :-- | :-- |
| Standing instruction or policy | Lower layer index wins | Layer 0 over layer 1 over layer 2 | Authority is declared upward; recency never repeals a standing constraint |
| Permission, data scope, or tool allowlist | Set intersection | The narrower of the two | A descendant scope may restrict and never expand |
| Prohibition of any kind | Deny overrides | The prohibiting unit | A single applicable deny binds regardless of layer |
| Observation, measurement, or state value | Later observation timestamp wins | Normally the higher layer index | A fresh observation supersedes a stale copy, which is then removed |
| Numeric bound on cost, latency, or retries | Stricter bound wins | The tighter of the two | Two bounds on one resource compose to the tighter |
| Two constraints of equal layer and authority | Conflict required | No automatic winner | Assembly halts and a named owner decides |

**Required Outputs**:

- A resolution record per conflict naming winner, losers, operator, and reason code.
- A supersession record naming every stale fact-type unit removed from the package and the layer it was removed from.
- An unresolved set naming conflicts that no operator settled.

**Quality Checkpoints**:

- No conflict resolves by layer distance alone; a resolution recorded without an operator is treated as unresolved.
- Every superseded fact-type unit is removed from the serialized package, not merely ranked below the winner, since both copies otherwise remain visible to the model.
- Permission and prohibition conflicts resolve by intersection or deny-overrides in 100 percent of cases; a permission widened by a higher layer index is a security event.

***

#### Step 5.3: Halt on Unresolved Conflict and Repair the Assignment

**Required Actions**:

- Halt assembly where the unresolved set is non-empty and the conflict involves a constraint-type unit, and return a conflict verdict naming the claim key, the layers, and the candidate values.
- Serialize with an explicit disclosure marker, rather than halting, where the unresolved conflict involves only fact-type units of equal timestamp and the task class is declared low risk, and record the disclosure.
- Route every unresolved conflict to an assignment repair rather than to a per-call workaround, since a claim key held in 2 layers with different values is evidence of the duplication prohibited in Step 2.1.
- Escalate to a named owner where the same claim key produces an unresolved conflict on 3 consecutive assemblies, and never resolve a repeated conflict by retrying the same comparison.
- Track conflicts per 1,000 assemblies, target no more than 5, and trigger a full layer-assignment audit above that rate.
- Record the repair applied and re-measure the conflict rate for the affected claim key over the following 200 calls.

**Required Outputs**:

- A conflict verdict per halt naming claim key, layers, candidate values, and unit types.
- An escalation record for every claim key conflicting on 3 consecutive assemblies.
- A conflict rate per 1,000 assemblies with the audit trigger state.

**Quality Checkpoints**:

- No constraint-type conflict is serialized; a package carrying two live constraints on one subject is not issued.
- Every unresolved conflict produces an assignment repair referral, not only a per-call decision, so that the same conflict does not recur under a new reason code.
- A conflict rate above 5 per 1,000 assemblies opens an audit; a rate that is falling without an audit is treated as unexplained rather than as improvement.

***

### Phase 6: Promotion, Demotion, and Generation Cutover

**Objective**: Move content between layers only on measured evidence and only at declared cutovers, so that a stable layer stays stable and the movement itself does not consume the saving stratification produced.

#### Step 6.1: Evaluate the Promotion Trigger Under Separated Thresholds

**Required Actions**:

- Admit a unit to promotion evaluation only where 4 deterministic preconditions hold: a measured change period of at least 200 calls, a reference rate of at least 60 percent over the last 100 calls, a scope class no narrower than the target layer's scope class, and a trust class inside the target layer's allowlist.
- Request a model durability judgement only after all 4 preconditions hold, and treat the judgement as one weighted component of a promotion score rather than as a decision.
- Refuse a promotion whose token cost exceeds the target layer's remaining headroom, and never resolve the shortfall by borrowing, since borrowing is bound to a single call and a promotion is not.
- Refuse a promotion that would move a unit from a lower trust class into a layer whose allowlist excludes it, regardless of the model's judgement and regardless of the unit's reference rate.
- Draft the promoted unit's condensed form through the model tier where the raw unit exceeds 2 percent of the target layer's maximum, and validate the draft against a preservation check naming the assertions that must survive.
- Batch approved promotions into the next scheduled cutover rather than applying them individually, since each application costs one full prefix invalidation.

**Required Outputs**:

- A promotion candidate record per unit carrying all 4 precondition values and the reference rate that produced them.
- A promotion score per candidate naming the deterministic components and the weighted model contribution separately.
- A batched promotion set scheduled against a named cutover.

**Quality Checkpoints**:

- No promotion proceeds on a model judgement alone; a promotion record without all 4 precondition values is rejected.
- No promotion crosses a trust-class boundary; a retrieved or tool-produced unit never enters layer 0 through this path.
- Every condensed form passes its preservation check before scheduling; a failed check returns the unit to its current layer rather than promoting the raw form.

***

#### Step 6.2: Evaluate the Demotion Trigger With Hysteresis

**Required Actions**:

- Trigger demotion evaluation on any one of 4 conditions: a measured change period below 200 calls sustained across 2 consecutive windows, a reference rate below 10 percent over the last 200 calls, a scope class that has narrowed since assignment, or a passed freshness expiry.
- Separate the demotion threshold from the promotion threshold so that the reference rate required to remain in a layer, 10 percent, sits strictly below the rate required to enter it, 60 percent.
- Enforce a minimum residence of 200 calls in the current layer and a cooldown of 100 calls after any movement, and permit at most 1 movement per unit per movement window.
- Demote a passed-expiry fact-type unit without a model proposal, since a measured expiry is sufficient evidence and a model opinion adds latency without adding information.
- Preserve a durable reference to every demoted unit before the movement, adopting the externalization contract from the context write guidance rather than defining a parallel one.
- Suspend from layer 0 immediately, outside the cutover schedule, any fact-type unit whose staleness exposure exceeds 0.5, since carrying a known-stale fact costs more than one early invalidation.

**Required Outputs**:

- A demotion candidate record naming which of the 4 conditions fired and the measured value behind it.
- A hysteresis state record per unit carrying residence, cooldown, and movements in the current window.
- A durable reference record for every demoted unit.

**Quality Checkpoints**:

- The demotion threshold sits strictly below the promotion threshold for every layer pair; equal thresholds produce oscillation and are rejected at declaration.
- No unit moves twice inside one movement window; a second movement is deferred rather than executed with a warning.
- Every demoted unit retains a durable reference; a demotion that leaves no reference is a deletion and is not permitted under this phase.

***

#### Step 6.3: Publish a Layer Generation Atomically and Detect Thrashing

**Required Actions**:

- Build the new layer content as an immutable generation, compute its content hash, and publish it by moving the layer's serving alias from generation n to generation n plus one in one operation.
- Schedule at most 1 cutover per layer per 200 calls, since each cutover invalidates the prefix once by design and a higher rate converts a stable layer into a volatile one.
- Verify after cutover that the layer's serialized hash equals the new generation's recorded hash, and roll the alias back to generation n where it does not.
- Compute a thrash signature per unit as the count of boundary crossings in both directions inside a 500-call window, and flag any unit crossing the same boundary in both directions at least 2 times.
- Apply a graduated correction to a thrashing unit: first widen the hysteresis gap for its class, then extend its minimum residence, then pin it to the layer indicated by its measured change period and stop evaluating it.
- Compare the movement cost against the saving, expressed as tokens forfeited to cutover invalidation against tokens saved by the new placement, and reverse any batch whose net saving over 500 calls is not positive.

**Required Outputs**:

- A generation record per layer carrying the generation number, content hash, cutover call index, and the movement set applied.
- A thrash signature per unit over the declared window with the correction stage applied.
- A movement cost-benefit record per batch stating forfeited and saved tokens over 500 calls.

**Quality Checkpoints**:

- Cutover is atomic at the alias; a package assembled from two generations of one layer is not issued.
- No layer exceeds 1 cutover per 200 calls; a layer needing more frequent cutover is misdeclared and returns to Step 1.1.
- Every promotion batch demonstrates a positive net token saving over 500 calls; a batch that does not is reversed rather than retained on the expectation of a future benefit.

***

## III. Implementation Guidance for AI Agents

AI agents operating a layered context architecture must follow systematic protocols ensuring that layer assignment is measured rather than asserted, that ordering is enforced rather than conventional, and that every movement between layers is scheduled, attributable, and reversible. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Layer Contract Agent**: Owns the layer set, the permanence bands, the scope classes, the trust-class allowlists, the budgets, and the contract version. It alone may amend a layer contract, and every amendment produces a new version bound to subsequent measurements.
2. **Permanence Meter**: Hashes every candidate unit's serialization on every call, maintains the change-period and reference-rate windows, and derives scope class by byte comparison across principals and sessions. It never assigns a layer and never proposes a movement.
3. **Assignment Validator**: Applies the volatility-dominant rule, enforces trust-class allowlists, rejects duplicate placements, and produces the misassignment list with staleness exposure and rebuild cost. It rejects assignments; it does not correct stable layers.
4. **Assembler**: Serializes layers in index order, enforces the ordering invariant, counts tokens against both axes, runs within-layer eviction, applies the borrow rule, places the prefix boundary, and holds the budget veto. Its refusal is final for the call.
5. **Coherence Checker**: Groups admitted units by claim key, detects cross-layer conflicts, applies the resolution operators, removes superseded copies, and halts assembly on an unresolved constraint conflict.
6. **Movement Scheduler**: Evaluates promotion and demotion triggers, enforces residence and cooldown timers, batches approved movements, performs generation cutover, computes thrash signatures, and reverses batches whose net saving is not positive.
7. **Durability Proposer**: The model-tier component. Proposes that a unit has become durable or stale, normalises claim keys across differing wordings, and drafts condensed forms for promoted units. It holds no authority over any bound, any assignment, or any trust class.

**Component authority rule**: The Durability Proposer proposes and every other component verifies. Where the Proposer and any deterministic component disagree, the deterministic component prevails and the disagreement is recorded with the model identifier, the prompt version, and the proposal that was refused, so that a later audit separates a policy failure from a proposal failure.

**Workflow Execution Pattern**:

```
STATE: Assembly_Serialization
INPUTS:
  1. Layer contract record and version from Phase 1
  2. Layer assignment table with claim keys and unit types from Phase 2
  3. Candidate unit set for the current call with tokenized sizes
ACTIONS:
  1. Order units by layer index, then by the declared within-layer order
  2. Count tokens per layer and per purpose cell against both bounds
  3. Run within-layer eviction where a layer exceeds its maximum
  4. Apply the one-directional borrow rule under both caps
  5. Group by claim key and resolve cross-layer conflicts by operator
  6. Emit the package, the layer offset record, and the layer hashes
VALIDATION:
  - ordering_invariant_violations == 0
  - duplicate_claim_key_with_differing_hash_unresolved == 0
  - layer_occupancy <= layer_maximum FOR ALL layers
  - floor_units_evicted == 0
  - borrow_direction_valid == TRUE
  - per_call_values_below_step_layer == 0
  - boundary_count <= 4
TRANSITIONS:
  IF all_validations_pass THEN next_state = Issue_Call
  IF unresolved_constraint_conflict THEN next_state = Halt_With_Conflict_Verdict
  IF layer_occupancy_exceeds_maximum_after_eviction
     THEN next_state = Overflow_Verdict_And_Configuration_Review
  IF ordering_invariant_violated THEN next_state = Serialization_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended layer assignment, ordering, and movement set with their measured inputs and bound computations without serializing anything; confirm them against the validation block while no tokens are committed; serialize only after validation passes, recording the assignment and movement events in the same operation.

**Approval Gate**: Human authorisation is required before any amendment to a layer 0 trust-class allowlist, before any promotion of content whose trust class is not trusted configuration, before any increase of the layer 0 maximum above 25 percent of the usable input budget, and before any cutover replacing more than 30 percent of layer 0 tokens in one generation. Agents halt at these gates rather than proceeding with a recorded warning, because each of the four changes what every future call carries at system-layer authority.

**Context Management Requirements**:

- Hold the layer contract, the assignment table, the measurement windows, and the generation records in durable state, since the architecture outlives any single context window and none of it may be read back from the window as authority.
- Charge the assembler's own accounting output to the step layer and count it against the budget, rather than treating instrumentation as free.
- Write a handoff record at every context boundary naming the contract version, the current generation per layer, the open movement batch, and the pending conflict set, adopting the handoff contract from the context management guidance rather than defining a parallel one.
- Re-measure permanence after any context boundary rather than inheriting a change period computed against a different assembly, since a boundary changes what the window carries and therefore what changes between calls.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract Integrity (After Phase 1)**

- **Automated Check**: Layer count is between 2 and 4; permanence bands are contiguous and non-overlapping; every layer carries a trust-class allowlist, a floor expressed as a named unit set, and a deterministic within-layer order; layer maxima sum to no more than 100 percent of the usable input budget.
- **Agent Action on Pass**: Proceed to measurement and assignment.
- **Agent Action on Failure**: Halt the deployment and return the specific contract defect; no assembly runs against an incoherent contract.
- **Human Review Trigger**: A layer count above 3, or a layer 0 maximum above 25 percent of the usable input budget.

**Checkpoint 2: Assignment Validity (After Phase 2)**

- **Automated Check**: Every admitted unit sits in exactly 1 layer; no unit violates its layer's trust-class allowlist; every unit carries a claim key, a unit type, and, where fact-type, a freshness expiry; every provisional assignment carries a scheduled re-measurement.
- **Agent Action on Pass**: Proceed to serialization.
- **Agent Action on Failure**: Reject the offending units and assemble without them, recording each rejection with a reason code.
- **Human Review Trigger**: Any trust-class violation at layer 0, or more than 10 percent of admitted units carrying provisional assignments.

**Checkpoint 3: Ordering and Stability (After Phase 3)**

- **Automated Check**: Zero ordering-invariant violations; zero per-call values in layers below the step layer; boundary count no greater than 4; layer 0 byte-identity rate at least 99 percent over the last 200 calls; every invalidation names a first-changed unit.
- **Agent Action on Pass**: Proceed to budget enforcement.
- **Agent Action on Failure**: Halt the call on an ordering violation; record and attribute the invalidation on a byte-identity shortfall without halting.
- **Human Review Trigger**: Byte-identity rate below 95 percent over 200 calls, or a non-deterministic serializer confirmed across 2 processes.

**Checkpoint 4: Budget Compliance (After Phase 4)**

- **Automated Check**: Every layer sits at or below its maximum after eviction; zero floor units evicted; zero cross-layer evictions; every borrow runs from a lower layer index to a higher one and satisfies both caps; total assembly sits inside the usable input budget.
- **Agent Action on Pass**: Proceed to coherence checking.
- **Agent Action on Failure**: Return the overflow verdict with the per-layer ledger; the call is not issued and the package is never truncated to fit.
- **Human Review Trigger**: A layer 0 overflow surviving its eviction order, or a borrow rate above 20 percent over 200 calls.

**Checkpoint 5: Coherence (After Phase 5)**

- **Automated Check**: Claim-key comparison covered 100 percent of admitted units or recorded its reduced scope; zero unresolved constraint-type conflicts; zero superseded fact-type units remaining in the package; every resolution names an operator.
- **Agent Action on Pass**: Issue the call.
- **Agent Action on Failure**: Halt on an unresolved constraint conflict; serialize with a disclosure marker only where the conflict is fact-type, timestamps are equal, and the task class is declared low risk.
- **Human Review Trigger**: The same claim key unresolved on 3 consecutive assemblies, or a conflict rate above 5 per 1,000 assemblies.

**Checkpoint 6: Movement Validity (After Phase 6)**

- **Automated Check**: Every promotion carries all 4 precondition values; no promotion crosses a trust-class boundary; demotion thresholds sit strictly below promotion thresholds; no unit moved twice in one window; cutover count no greater than 1 per layer per 200 calls; every batch shows a positive net token saving over 500 calls.
- **Agent Action on Pass**: Publish the generation and release the movement record.
- **Agent Action on Failure**: Withhold the cutover, roll the alias back to the prior generation, and return the failing preconditions.
- **Human Review Trigger**: A cutover replacing more than 30 percent of layer 0 tokens, or any unit reaching the third correction stage of the thrash ladder.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
CONTRACT_VERSION:
LAYER_SCOPE:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Silent Staleness in a Stable Layer**

- **Symptoms**: Outputs cite a value that a durable store superseded; a layer 0 unit's measured change period falls below its band; staleness exposure above 0.5 with no invalidation events recorded for the unit.
- **Diagnostic Steps**: Compare the layer 0 copy's value hash against the canonical record in the durable store; recompute the unit's change period from the hash log rather than from its declaration; determine whether the unit is fact-type or constraint-type, since only fact-type units may be suspended outside a cutover.
- **Resolution Protocol**: Option A, suspend the fact-type unit from layer 0 immediately and serve it from layer 1 as a reference resolved per call. Option B, shorten the layer's cutover interval only where the change period is above 200 calls, since a shorter interval below that threshold makes the layer volatile. Option C, split the unit into a stable instruction and a volatile operand, keeping the instruction in layer 0 and moving the operand to layer 2.
- **Escalation Trigger**: A stale layer 0 value that reached an output escalates immediately with the affected call identifiers; this class is never resolved by waiting for the next scheduled cutover.

**Error Type 2: Prefix Churn From an Under-Stabilised Unit**

- **Symptoms**: Layer 0 byte identity below 95 percent; invalidation events attributed to the same unit on most calls; forfeited bytes rising while layer content is nominally unchanged.
- **Diagnostic Steps**: Diff the layer serialization at unit granularity and name the first changed unit; classify the cause as a per-call value, a non-deterministic order, or a genuinely volatile unit; confirm the classification across 2 processes to separate an order defect from a content defect.
- **Resolution Protocol**: Option A, move the offending unit to the step layer and refer to it by name from the stable layer. Option B, replace a runtime-derived within-layer order with a deterministic function of unit identifiers. Option C, remove the injected per-call value entirely where the stable instruction does not depend on it.
- **Escalation Trigger**: Byte identity below 95 percent after 2 correction attempts escalates for contract review; the layer is not left in place on the expectation that traffic patterns will change.

**Error Type 3: Cross-Layer Contradiction on One Claim Key**

- **Symptoms**: Two layers assert different values for one claim key; outputs alternate between the values across calls; a resolution record exists but the losing copy remains in the package.
- **Diagnostic Steps**: Confirm whether the pairing is a genuine conflict or a duplication that Step 2.1 should have prevented; check the unit types, since a constraint and a fact sharing one key is a keying defect rather than a conflict; verify that supersession removed the losing copy rather than ranking it.
- **Resolution Protocol**: Option A, collapse the duplication by keeping the content in the lower layer index and a reference in the higher one. Option B, re-key the pairing where a constraint and a fact share one claim key. Option C, escalate to the named owner where both units are constraint-type at equal authority, which the operator table declares unresolvable automatically.
- **Escalation Trigger**: The same claim key unresolved on 3 consecutive assemblies escalates to the owner; repeating the comparison against unchanged inputs is prohibited.

**Error Type 4: Layer Overflow That Eviction Cannot Resolve**

- **Symptoms**: A layer exceeds its maximum after its eviction order completes; the floor alone approaches or exceeds the maximum; borrow requests are refused for reaching a cap on consecutive calls.
- **Diagnostic Steps**: Compare the layer's floor token count against its maximum; determine whether growth came from admitted units or from a purpose partition whose cell bound is looser than the layer bound; check whether the overflow is at layer 0, which is a configuration defect rather than a runtime condition.
- **Resolution Protocol**: Option A, demote the lowest-authority units of an overflowing layer 0 to layer 1 as references at the next cutover, and halt the current call. Option B, re-derive the layer maxima from measured occupancy under Step 1.3 where the borrow rate exceeded 20 percent. Option C, reduce the layer count to 2 where layer 0 no longer justifies a separate stratum.
- **Escalation Trigger**: A floor exceeding its layer maximum halts the deployment for contract repair; this condition is never resolved by evicting a floor unit.

**Error Type 5: Layer Thrashing Across a Boundary**

- **Symptoms**: Units crossing the same boundary in both directions inside a 500-call window; cutover frequency approaching 1 per 200 calls; movement cost consuming the placement saving.
- **Diagnostic Steps**: Compute the thrash signature per unit and per boundary; check whether the promotion and demotion thresholds are separated; check whether residence and cooldown timers are enforced or merely declared.
- **Resolution Protocol**: Option A, widen the hysteresis gap for the affected class. Option B, extend the minimum residence beyond 200 calls for units in that class. Option C, pin the unit to the layer its measured change period indicates and stop evaluating it for movement.
- **Escalation Trigger**: A unit reaching the third correction stage escalates for contract review, because a unit that must be pinned indicates that the permanence bands do not match the workload.

**Error Type 6: Trust-Class Escalation Through Promotion**

- **Symptoms**: A layer 0 unit whose provenance is retrieved text, tool output, or model inference; a promotion record whose trust-class precondition is absent; instruction-shaped content appearing in a layer that admits only trusted configuration.
- **Diagnostic Steps**: Trace the unit's provenance label to its source; check the promotion record for all 4 preconditions; determine whether the model tier proposed the promotion and whether the Assignment Validator refused it.
- **Resolution Protocol**: Option A, remove the unit from layer 0 immediately and re-admit it only through the trusted configuration path. Option B, quarantine every output produced while it was resident and re-run the affected calls. Option C, tighten the allowlist enforcement so that the trust-class check precedes rather than follows the promotion score.
- **Escalation Trigger**: Any trust-class violation at layer 0 escalates immediately as a security event; this class is never resolved by retry and never by a compensating relevance argument.

**Troubleshooting Decision Tree**:

```
ASSEMBLY OR MOVEMENT FAILS VALIDATION
├─ STABILITY DEFECT
│   ├─ Per-call value below step layer → Move value to step layer; refer by name
│   ├─ Within-layer order varies across processes → Replace with identifier-ordered function
│   └─ Byte identity below 95 percent after 2 fixes → ESCALATE for contract review
├─ ASSIGNMENT DEFECT
│   ├─ Unit in 2 layers → Keep content in lower index; reference in higher
│   ├─ Trust class excluded by allowlist → HALT; security event at layer 0
│   └─ Measured band contradicts placement → Refer to Phase 6; never patch in the loop
├─ BUDGET DEFECT
│   ├─ Layer over maximum → Run that layer's eviction order only
│   ├─ Floor breached or floor exceeds maximum → HALT deployment; repair contract
│   └─ Borrow refused on consecutive calls → Re-derive bounds at Step 1.3
├─ COHERENCE DEFECT
│   ├─ Constraint conflict unresolved → HALT; do not issue the call
│   ├─ Fact conflict with equal timestamps → Disclose or escalate by risk class
│   └─ Constraint and fact share one key → Re-key; this is not a conflict
└─ MOVEMENT DEFECT
    ├─ Promotion without all 4 preconditions → Refuse; return the missing values
    ├─ Thrash signature at or above 2 crossings → Widen hysteresis, then extend residence, then pin
    └─ Batch net saving not positive → Reverse the batch at the next cutover
```

### D. Performance Metrics and Continuous Learning

Every figure below carries its numerator, denominator, window, layer, and contract version. A rate reported without its window is not interpretable, since every quantity here is defined over a call count.

**Stratification Quality Metrics**:

- **Layer fit rate**: Units whose measured change period falls inside their placed layer's band, divided by admitted units (target: at least 95 percent; below 90 percent opens an assignment audit).
- **Weighted staleness exposure**: The sum over layer 0 fact-type units of staleness exposure multiplied by token cost, divided by layer 0 tokens (target: no more than 0.05; above 0.15 suspends the affected units).
- **Provisional assignment share**: Units placed on a model estimate rather than a measurement, divided by admitted units (target: no more than 10 percent after 200 calls of operation).
- **Stable carry ratio**: Layer 0 tokens divided by usable input budget (target: at or below the declared 25 percent maximum; a ratio rising with a flat layer 0 unit count indicates unit growth rather than accretion and is diagnosed separately).

**Stability and Cost Metrics**:

- **Layer 0 byte-identity rate**: Calls whose layer 0 hash matched the current generation, divided by calls in the window (target: at least 99 percent; below 95 percent halts configuration promotion).
- **Unplanned invalidations**: Invalidation events not attributable to a scheduled cutover, per 200 calls (target: no more than 2; each carries a named first-changed unit or it is a measurement gap).
- **Forfeited byte ratio**: Stable bytes recomputed because of an unplanned invalidation, divided by stable bytes serialized (target: no more than 5 percent).
- **Borrow rate**: Calls containing at least 1 borrow event, divided by calls (target: no more than 20 percent; above it, the bounds are re-derived rather than the borrows continued).
- **Cutover frequency**: Generation cutovers per layer per 200 calls (target: no more than 1; a higher figure means the layer is misdeclared).

**Coherence and Movement Metrics**:

- **Conflict rate**: Cross-layer conflicts detected, per 1,000 assemblies (target: no more than 5; above it, a layer-assignment audit opens).
- **Unresolved conflict share**: Conflicts that no operator settled, divided by conflicts detected (target: no more than 2 percent; every unresolved constraint conflict halts its call regardless of the share).
- **Supersession completeness**: Superseded fact-type units removed from the package, divided by superseded units detected (target: 100 percent; a shortfall means both values were serialized).
- **Promotion precision**: Promotions whose promoted unit was referenced in at least 60 percent of the following 200 calls, divided by completed promotions (target: at least 80 percent). The definition is adopted from the hierarchical memory guidance with the reference window restated in calls.
- **Demotion regret**: Demotions followed by a qualifying re-admission inside the following 200 calls, divided by completed demotions (target: no more than 10 percent).
- **Thrash rate**: Units crossing one boundary in both directions inside a 500-call window, divided by units evaluated for movement (target: no more than 2 percent).
- **Net movement saving**: Tokens saved by new placements minus tokens forfeited to cutover invalidation, over 500 calls (target: positive; a non-positive figure reverses the batch).

**Log-Pattern Failure Detection**: Rising layer 0 tokens at a flat unit count indicates unit growth; rising layer 0 tokens at a rising unit count indicates accretion, and the two have different remedies. Invalidations concentrated on one unit indicate an under-stabilised unit; invalidations spread evenly across units indicate a non-deterministic serializer. Conflicts concentrated on one claim key indicate a duplication; conflicts spread across keys indicate a keying convention that is too coarse. A borrow rate rising while occupancy is flat indicates that a purpose-partition cell, not the layer, is binding. Promotion precision falling while the promotion threshold is unchanged indicates a workload shift and returns the bands to Step 1.1.

**Learning and Adaptation Mechanisms**:

- **Band recalibration**: Recompute the permanence bands from the observed distribution of change periods whenever the layer fit rate falls below 90 percent, rather than reassigning units into bands that do not fit the workload.
- **Threshold versioning**: Version every promotion and demotion threshold, and evaluate a revision against calls that did not produce it, so that the evidence is not the same data that motivated the change.
- **Refused-proposal review**: Retain every model proposal the deterministic tier refused, with the precondition that failed, so that a systematically wrong proposer is detected as a proposer defect rather than absorbed as noise.
- **Default recalibration**: Treat every numeric value in this guide as a deployment default and recompute it per task class against measured behaviour; the values are operable on first deployment and are not constants.

**Human-in-the-Loop Boundaries**: Amendment of a layer 0 trust-class allowlist, promotion of content whose trust class is not trusted configuration, an increase of the layer 0 maximum, a cutover replacing more than 30 percent of layer 0 tokens, and resolution of a conflict between two constraint-type units of equal authority are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how assembled content is stratified by permanence and scope, not what that content is about. Its phases hold wherever an agent issues repeated calls that share some content and differ in the rest, and wherever carrying stale content has a cost.

### 4.1 Cross-Domain Application Patterns

**Software engineering agents**: Layer 0 carries the language and build conventions, the repository-wide prohibitions, and the tool contracts, all of which change on the order of once per release. Layer 1 carries the issue objective, the acceptance tests, the files opened for the task, and the decisions already taken. Layer 2 carries the current diff, the latest test output, and the current instruction. Directory-scoped instruction files are a natural layer 1 source rather than a layer 0 source, because their applicability is bounded to a subtree and their content changes with the code beside them; treating them as layer 0 content is the characteristic over-stabilisation of this domain, and it produces a system layer that changes whenever any subdirectory does.

**Clinical decision support**: Layer 0 carries the escalation policy, the scope-of-practice limits, and the documentation obligations, which change on a governance cycle measured in months. Layer 1 carries the patient context assembled for the encounter, whose scope is one session and never broader. Layer 2 carries the current question and the latest retrieved result. The demotion trigger that matters most here is the freshness expiry, because a measurement carried past its validity is the domain's dominant failure and it is a measured condition rather than a judgement.

**Financial advisory and regulated recommendation**: Layer 0 carries the suitability rules, the disclosure obligations, and the prohibited-recommendation list, and its trust-class allowlist admits only trusted configuration, since a retrieved market commentary acquiring system-layer authority is the domain's principal risk. Layer 1 carries the client mandate and the constraints of the current engagement. Conflicts here resolve overwhelmingly by deny-overrides and intersection, and the resolution record is a compliance artifact rather than a diagnostic aid.

**Industrial operations and field maintenance**: Layer 0 carries the safety interlocks and the procedure library, whose stability is high and whose scope is the whole fleet. Layer 1 carries the asset under service and its history. Layer 2 carries the current sensor reading, which changes on every call by construction. The characteristic error is placing a fleet-wide but frequently revised procedure in layer 0, where a revision invalidates the prefix for every agent in the fleet at once, and the remedy is a scheduled cutover rather than an immediate edit.

**Education and tutoring**: Layer 0 carries the pedagogical policy and the assessment rules. Layer 1 carries the learner model, which is genuinely session-scoped and genuinely narrow, and which is the domain's most common over-stabilisation candidate because it feels durable. A learner model in layer 0 is both stale and shared across learners, which the scope index alone forbids; the volatility-dominant rule catches this case on the scope axis even where the permanence axis would have permitted it.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small deployments and short runs**: Collapse to 2 layers, a stable layer and a step layer, and retain the assignment rule, the ordering invariant, and the coherence check. A run of fewer than 200 calls cannot measure a change period at the declared window, so every assignment is provisional and the promotion path stays closed until the window fills.
- **Large multi-tenant deployments**: Split layer 0 into a platform stratum and a tenant stratum, since the two have different scope classes and a shared prefix across tenants is only available above the tenant boundary. Never share a prefix across authorization scopes on the strength of a byte match, and scope every cache key by tenant regardless of content identity.
- **High-risk and irreversible work**: Tighten the layer 0 trust-class allowlist to trusted configuration only, bind the approval gate before every cutover rather than only above the 30 percent threshold, and treat any unresolved conflict as a halt regardless of unit type. Prefer halting to serializing a disclosed contradiction where an action follows the call.
- **Strict latency budgets**: Reduce the coherence comparison to constraint-type units and units above a declared token size rather than skipping it, and record the reduced scope explicitly. Do not remove the ordering invariant to save time, since an inversion costs more in recomputed prefix than the check costs to run.
- **Long-horizon autonomous runs**: Persist the contract, the assignment table, the measurement windows, and the generation records outside the window, re-measure permanence after every context boundary, and treat the movement window as a property of the run rather than of the session, so that a boundary does not reset the hysteresis timers and restart thrashing.

***

## V. Limitations and Considerations

**Thresholds here are deployment defaults, not measured findings**: The permanence bands of 500 and 5 calls, the 25, 45, and 30 percent layer shares, the 60 percent promotion and 10 percent demotion reference rates, the 200-call residence, the 100-call cooldown, and the 500-call thrash window were chosen to be operable on first deployment and internally consistent, not derived from a measured property of agent workloads. Their consequence is that a deployment adopting them unchanged may stratify against the wrong boundaries and report a healthy layer fit rate for a bad architecture. The mitigation is the band recalibration mechanism in Section III.D, which recomputes the bands from the observed distribution of change periods whenever the layer fit rate falls below 90 percent.

**Permanence measurement is reflexive**: The change period of a unit is measured inside an architecture that already decides how often that unit is rebuilt, so a unit placed in the step layer is rebuilt every call and will measure as volatile whether or not its underlying value changed. Its consequence is that under-stabilisation can be self-confirming and can persist through several measurement windows. The mitigation is to hash the unit's source value in the durable store rather than its serialized form when computing change period for units under promotion evaluation, so that the measurement is taken against the value rather than against the rebuild.

**Byte identity is necessary but not sufficient for prefix reuse**: A layer that hashes identically across calls may still fail to produce provider cache reuse, because breakpoint placement, minimum cacheable length, lookback limits, cache lifetime, and parameters unrelated to content all bear on the outcome, and providers change these over time. Its consequence is that a deployment can satisfy every stability metric here and observe no cost saving. The mitigation is to treat byte identity as the agent-layer obligation and to measure the saving from provider-reported cache-read and cache-write token telemetry under the prompt-caching treatment in the hierarchical memory guidance, never to infer a saving from a stability figure.

**Claim-key extraction is imperfect over prose**: Deterministic keys work for structured units and fail for natural-language assertions, where the model tier proposes equivalences that may join two claims that are not the same or miss two that are. Its consequence is a mix of false conflicts, which halt calls that should have proceeded, and missed conflicts, which serialize contradictions the check was built to catch. The mitigation is the provenance labelling in Step 2.3, which records the model identifier and both wordings with every proposed equivalence, so that a halt traced later resolves to the equivalence rather than to the content, and the periodic refused-proposal review in Section III.D.

**The scope test needs traffic the deployment may not have**: Scope class is derived by comparing a unit's bytes across principals and across sessions, which requires more than one principal and more than one session to be observable. Its consequence is that a single-tenant deployment or a new deployment cannot distinguish global scope from tenant scope by measurement and must rely on a declaration. The mitigation is to treat an untestable scope class as the narrower of the candidates, which places the unit in a higher layer index and costs stability rather than correctness.

**Layering is itself a cost**: Each layer adds a boundary to account for, a generation to version, a conflict surface to check, and a movement policy to tune, and a three-layer architecture over content that has one permanence class buys nothing and pays for the machinery. Its consequence is a system whose overhead exceeds the staleness and stability it saves. The mitigation is the two explicit reductions in Section 1.3 and Section 4.2: reduce to two layers where layer 0 serializes below 512 tokens, and reduce to two layers where the measured change periods do not separate into distinct bands.

**Structural conformance is not sound stratification**: An architecture can satisfy every checkpoint here while carrying a system layer full of instructions that are stable, correct, and wrong for the task. The framework detects misplacement, staleness, contradiction, and churn; it does not detect a well-ordered layer 0 that says the wrong thing. No checkpoint in this guide substitutes for review of what the stable layer actually asserts.

***

## VI. Conclusion and Summary

Hierarchical context architecture is an accounting discipline before it is a prompt-construction technique. Its value comes from committing, in advance and in measurable terms, to which stratum each piece of content occupies, how long it may sit there without re-derivation, and what happens when two strata disagree. A deployment that makes those commitments explicitly will find its stale content, its churning units, and its duplicated claims by measurement; a deployment that leaves them implicit will carry all three at full token cost on every call and will discover them only through an output that cited a value nothing in the system still believed.

A team introducing this architecture should measure before stratifying. Instrument the assembler to hash every candidate unit and collect 200 calls of change-period and scope data against the current unstructured assembly, then derive the bands from that distribution rather than adopting the defaults. Declare two layers first, enforce the ordering invariant and the coherence check, and add a third layer only where the measured change periods separate into distinct bands. Open the promotion path last, after the movement window has enough history to separate a durable unit from a briefly popular one, since a promotion policy running against a short history produces exactly the thrashing that the hysteresis rules exist to prevent.

**Key Success Factors**:

- **Measured permanence**: Layer assignment follows an observed change period and a tested addressee set, never a description of what content is for.
- **Exactly one layer per unit**: Content sits in one stratum and is referenced from the others, so that duplication cannot be charged twice, updated once, and contradicted later.
- **Ordering as policy**: Layers serialize in a fixed index order under a deterministic within-layer order, and no per-call value ever sits ahead of stable content.
- **Type-based conflict resolution**: A constraint conflict resolves toward the stable layer and a fact conflict toward the fresh observation, and the losing copy leaves the package rather than merely losing.
- **One-directional relief**: A volatile layer may borrow a stable layer's unused headroom for one call; a stable layer never borrows, because a bound revised under pressure grows the carry on every call that follows.
- **Scheduled movement under hysteresis**: Promotion and demotion run at declared cutovers with separated thresholds, minimum residence, and cooldown, so that the movement does not consume the saving.

By following this guide, AI agents can stratify an assembled context so that stable content stays stable and cheap, volatile content stays current, and every disagreement between the two is detected and settled before a call is issued rather than after an output has already relied on it.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. The one exception is marked as verified: the provider documentation supplying the breakpoint limit, the minimum cacheable prefix lengths, and the prefix render order was retrieved during conversion, and the figures quoted in Section 1.3 and Step 3.2 come from that retrieval.

**Corpus pointers**:

- `Hierarchical Context Architecture: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the scope taxonomy, the separation of authority from scope and relevance, the staged resolution ordering, the field-specific composition operators, the stable-prefix and cache-boundary discipline, the directory-scoped instruction hazards, and the failure-mode inventory. Its material on hierarchical retrieval, recursive summarisation, ontology-backed traversal, and orchestrator-worker delegation is owned by sibling guides and was not restated here.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the umbrella guidance for this category. Source of the purpose-partition axis that composes with the permanence and scope axis here, and of the trust-class vocabulary, the admission gate, the output reserve and headroom rules, the assembly-order framing, and the handoff record, all adopted rather than redefined.
- `advanced_task_guides/memory-management/guide_HierarchicalMemory.md` — the storage-tiering counterpart. Owner of capacity and latency bounds per tier, admission and initial placement, eviction under a durability guarantee, and cross-tier coherence. Source of the promotion, demotion, hysteresis, thrashing, and generation terminology adopted here, and of the prompt-cache serialization constraint referenced in Step 3.2.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — companion guidance on admission across heterogeneous partitions, applicable to the candidate filtering that precedes assignment in Phase 2.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — companion guidance on externalization, supplying the durable reference contract required of every demoted unit in Step 6.2.
- `advanced_task_guides/context-management/guide_ContextFailurePrevention.md` — companion guidance on context failure modes, applicable to the staleness and contradiction consequences quantified in Section 1.3 and detected in Phase 5.
- `advanced_task_guides/context-management/guide_ContextLifecycle.md` — companion guidance on staged lifecycle and boundary crossings, applicable to the re-measurement obligation after a context boundary in Section III.A.
- `advanced_task_guides/context-management/guide_SlidingWindowContext.md` — companion guidance on windowed retention, applicable to the prefix-stability consequences of a moving conversation region in Phase 3.
- `advanced_task_guides/context-management/guide_ContextMemoryBlocks.md` — companion guidance on structured resident blocks, applicable to the composition of the system layer in Step 1.1.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — companion guidance on delegation into separate contexts, applicable where a layer set is constructed for a sub-context rather than inherited.
- `advanced_task_guides/context-management/guide_KVCacheAwarePromptConstruction.md` — the owner of cache key scoping, breakpoint placement economics, cache lifetime selection, invalidation causes, and savings measurement. This guide owns only the agent-layer prerequisite of a fixed layer order and verified byte identity above the prefix boundary; the deferrals stated in Section 1.3, Step 3.2, and Section V resolve to that guide, and its precedence deference in the other direction is stated in its own pointers.

**External references**: The entries below are transcribed from the originating prose guide except where marked as verified during conversion. Each is annotated with the material of this guide it bears on.

*Instruction priority and layered precedence*

1. OpenAI, *OpenAI instruction hierarchy* — https://openai.com/index/the-instruction-hierarchy/ (bears on the model-side defence-in-depth statement in Section 1.2).
2. OpenAI, *OpenAI Model Spec, December 2025* — https://model-spec.openai.com/2025-12-18.html (bears on the role-priority background in Section 1.2).
3. MDN, *MDN cascade specificity* — https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascade/Specificity (bears on the staged resolution pattern behind the operator table in Step 5.2).
4. Microsoft, *Microsoft inherited permissions guidance* — https://learn.microsoft.com/en-us/troubleshoot/windows-server/windows-security/inherited-permissions-not-automatically-update (bears on the requirement in Step 2.2 to re-measure rather than assume that a parent change propagated).

*Layered instruction sources and scope*

5. Anthropic, *Anthropic project memory* — https://docs.anthropic.com/en/docs/claude-code/memory (bears on the directory-scoped instruction pattern discussed in Section 4.1).
6. *AGENTS.md convention* — https://agents.md/ (bears on the nearest-file scoping pattern discussed in Section 4.1).
7. Anthropic, *Anthropic Claude Code subagents* — https://docs.anthropic.com/en/docs/claude-code/sub-agents (bears on layer sets constructed for a sub-context rather than inherited).

*Prefix stability and prompt caching*

8. OpenAI, *OpenAI prompt caching* — https://developers.openai.com/api/docs/guides/prompt-caching (bears on the static-content-first ordering discipline in Step 3.1).
9. Anthropic, *Anthropic prompt caching* — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching (bears on the cascade in which a change to an earlier layer invalidates later ones).
10. Anthropic, *Prompt caching* — https://platform.claude.com/docs/en/build-with-claude/prompt-caching (verified during conversion; source of the maximum of 4 cache breakpoints per request, the minimum cacheable prefix lengths of 512 to 4,096 tokens by model, and the tools then system then messages render order quoted in Section 1.3 and Step 3.2).

*Tiered and virtual context*

11. *MemGPT paper* — https://arxiv.org/abs/2310.08560 (bears on the virtual-context framing separated in Section 1.2 from the storage-tiering method owned by the hierarchical memory guidance).

*Context engineering principle*

12. Anthropic, *Effective context engineering for AI agents* — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (bears on the smallest-high-signal-set objective underlying the layer budgets in Step 1.3).
