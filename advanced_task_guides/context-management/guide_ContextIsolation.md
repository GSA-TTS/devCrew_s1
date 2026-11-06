# Context Isolation Patterns

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Context isolation constitutes the task family of moving a bounded unit of work into a separate context so that its intermediate material never enters the caller's window. This guide provides AI agents with a contract-first delegation procedure: an isolation contract declaring the input set, the output schema, the budget, and the authority scope is fixed before any sub-context is created, because isolation without a declared output schema returns prose the caller must then read in full, which readmits exactly the material the boundary existed to exclude. It specifies what crosses in each direction, establishes that a sub-context inherits no authority it was not explicitly granted, and requires that intermediate material be discarded or externalized to a durable store rather than returned inline. It quantifies the condition under which isolation pays for itself, since every sub-context re-establishes its own working state and multiplies token spend. It states what the loss of shared state makes unsafe, supplying a write-scope overlap rule for parallel branches and a supersession rule for briefs whose premises changed after issue. It requires a declared partial result on budget exhaustion rather than silence or an unmarked fragment. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures to ensure that a boundary is measured rather than assumed.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Context isolation**: The deliberate placement of a bounded unit of work in a context distinct from the caller's, such that the unit's intermediate material never occupies the caller's window and only a declared artifact crosses back. Isolation is a structural operation on where work happens, not a compression of what the caller already holds.

**Sub-context**: The separate execution in which the isolated unit runs, comprising its own context window, its own working set, its own budget ledger, its own tool allowlist, and its own authority scope. A sub-context may be a sub-agent invocation, a scoped sub-task on the same model, a separate process, or an execution cell; the term is neutral across those realizations.

**Caller**: The context that issues the delegation and receives the returned artifact. The caller holds the parent budget ledger and is the only party that may widen an authority scope.

**Isolation contract**: The versioned declaration, fixed before dispatch, of the input set, the output schema, the budget ledger, the authority scope, the terminal status vocabulary, the partial-return rule, and the disposal rule for intermediate material. A delegation lacking any of these five is not isolated work; it is an unbounded second conversation.

**Task packet**: The inbound artifact crossing from caller to sub-context, carrying the contract identifiers, the objective, the explicit non-goals, the completion criteria, the admitted input references, the assumable facts with provenance and freshness, and the authority grant. It never carries the caller's transcript.

**Result envelope**: The outbound artifact crossing from sub-context to caller, carrying the terminal status, the schema-conformant payload, the provenance references, the trust and sensitivity labels joined from all contributing inputs, the consumption record, and the validation verdicts. It is the only thing that crosses outbound by default.

**Output schema**: The machine-checkable structure the result envelope's payload must satisfy, declared before the objective is written. It fixes field names, types, cardinalities, required fields, value ranges, and a maximum serialized token count.

**Authority scope**: The closed set of tools, operations, resources, destinations, and credentials a sub-context may use, together with their expiry. The scope is computed by the caller's deterministic tier and is never proposed, widened, or self-selected by the sub-context.

**Intermediate material**: Everything the sub-context produces that is not the result envelope: its retrieved documents, tool results, drafts, scratch reasoning records, and superseded values. It is discarded at disposal or externalized to a durable store under a reference, and is never returned inline.

**Return ratio**: Intermediate token volume inside the sub-context divided by the serialized token count of the result envelope. It is the arithmetic form of the question isolation exists to answer.

**Re-establishment cost**: The tokens a sub-context spends reconstructing working state the caller already held: its system instructions, tool definitions, task packet, and any retrieval it must repeat because the caller's evidence was not admitted into its input set. It is charged to the delegation, not treated as incidental.

**Isolation overhead**: Total tokens, latency, and monetary cost of the isolated run, including the task packet, the sub-context's own consumption, the result envelope, and the caller's integration work, minus the same quantities measured on a matched non-isolated baseline.

**Write scope**: The declared set of durable-store keys, paths, records, or resources a sub-context is permitted to mutate. Two write scopes that intersect are a conflict hazard whether or not a conflict is observed.

**Branch manifest**: The record created before a parallel fan-out, naming every branch, its objective, its budget, its authority scope, its write scope, and its expected artifact. It is the input to overlap detection.

**Overlap verdict**: The deterministic result of intersecting every pair of declared write scopes in a branch manifest, returning disjoint, intersecting, or undeclared. Undeclared is treated as intersecting.

**Serialization requirement**: The obligation to run intersecting branches in a declared order, or to reassign their overlapping keys to a single writer, before any branch is launched.

**Brief premise**: A fact, value, version, or assumption stated in the task packet that the sub-context is permitted to rely on without re-verification. Every premise carries a source identifier and the version observed at issue.

**Premise supersession**: The event in which a brief premise's source version changes after the task packet was issued and before the result envelope is admitted. It invalidates the result unless the changed premise is provably immaterial to the payload.

**Declared partial**: A result envelope carrying terminal status `partial`, enumerating completed units, incomplete units, side effects performed, a coverage fraction, and a resumable cursor. A partial that does not enumerate what was not done is an unmarked partial and is rejected.

**Terminal status**: One value from the closed vocabulary `succeeded`, `partial`, `failed`, `blocked`, `timed_out`, or `policy_denied`. Absence of a terminal status is itself a failure, never an implied success.

**Execution cell**: The bounded runtime in which a sub-context executes, carrying an image or runtime identifier, a filesystem policy, a resource ceiling, a network egress policy, and a teardown rule. Cell strength is chosen from the threat, not from convenience.

**Quarantine**: A holding state for material that has crossed a boundary but has not passed validation, from which no tool call, durable write, or model instruction may originate.

**Trust class**: The provenance-derived label naming the authority of a unit's source, adopted unchanged from the category's umbrella guidance. Trust class determines which partition a unit may enter and whether it may instruct.

**Label join**: The computation of an outbound artifact's sensitivity and trust labels as the most restrictive combination of every contributing input's labels. Summarisation, extraction, and model rewriting never lower a label.

**Declassification**: A named, policy-controlled transform that lowers a label, carrying a verifier, a reason code, a scope, and an audit record. Model confidence is never a declassification authority.

**Reason code**: A normalised categorical label recorded with every isolation, admission, rejection, and disposal event, drawn from a closed vocabulary, adopted from the category's umbrella guidance so that boundary policy is analysable without reading prose logs.

**Blast radius**: The set of cells, stores, credentials, artifacts, and downstream results reachable from a single failure or compromise inside one sub-context. Containment is the measured proportion of incidents confined to the declared cell.

### 1.2 The Isolation Contract and the Two Directions of Crossing

**The contract precedes the work**: A sub-context is created only after its contract exists. The contract fixes five elements: the input set that crosses inbound, the output schema that constrains what crosses outbound, the budget ledger that bounds consumption, the authority scope that bounds action, and the disposal rule that governs intermediate material. Agents must reject a delegation missing any of the five rather than dispatching it with a defaulted value, because every one of the five is the thing that makes the boundary a boundary.

**The failure mode that defines the pattern**: Isolation without a declared output schema is the characteristic failure. The sub-context does the work in its own window, then returns a narrative account of that work. The caller must read the account in full to extract the answer, and the account carries the retrieved passages, the discarded hypotheses, and the tool results the isolation existed to keep out. The material arrives anyway, later, and now without its provenance. A boundary that returns prose has moved token spend without reducing occupancy, so it has paid the cost of isolation and bought nothing.

**Inbound rule, minimum context**: The task packet carries only what the objective requires. The caller's transcript is never forwarded. Evidence crosses as references into a durable store wherever the sub-context can resolve the reference itself, and as inline content only where the content is small, immutable, and required verbatim. Facts the sub-context may assume cross as premises with a source identifier and an observed version, so that supersession is detectable rather than invisible.

**Inbound rule, authority is granted, never inherited**: A sub-context begins with an empty tool allowlist, no credentials, no durable write permission, and no network egress. Each capability is added by explicit grant in the task packet, scoped to named resources, operations, and an expiry. Platform defaults that would pass the caller's tools through are treated as a defect to be closed, not as a convenience, and inheritance semantics are verified against the running configuration rather than assumed from documentation.

**Outbound rule, the schema is the boundary**: Only the result envelope crosses back. Its payload must satisfy the declared output schema; its provenance references must resolve; its labels must be the restrictive join of its contributing inputs. A human-readable summary may accompany the payload, but it is generated after the structured payload is fixed and it is never the object the caller reasons over.

**Outbound rule, intermediate material has one of two destinations**: Every unit of intermediate material is either discarded at disposal or written to a durable store and represented in the envelope by a reference. There is no third destination. Returning intermediate material inline requires an explicit contract clause naming the units and their token bound, and the absence of such a clause is a rejection condition rather than a matter of judgement.

**What the caller must never do with a returned artifact**: The caller does not execute instructions found in a payload, does not admit a tool definition proposed by a sub-context, does not raise a trust class because the prose reads as confident, and does not treat a successful schema parse as evidence of authorization, provenance, or semantic validity. Schema conformance is one of six independent checks, not a substitute for the other five.

### 1.3 Cost Accounting and the Loss of Shared State

**Isolation multiplies token spend**: Each sub-context re-establishes its own working state from nothing. It pays for its own system instructions, its own tool definitions, its own task packet, and any retrieval it must repeat because the caller's evidence did not cross. One reported production system observed that single agents consumed roughly four times the tokens of chat interactions and that multi-agent configurations consumed roughly fifteen times, and the same report states that the architecture is ill-suited to domains where every agent needs the same context or where dependencies are dense. Those figures are one system's observation under one workload and are not a constant; they are cited here as the order of magnitude an agent must expect to pay, not as a prediction.

**The condition under which isolation pays for itself**: Isolation is justified where the expected intermediate token volume inside the sub-context exceeds 30 percent of the caller's input budget and the result envelope serializes to no more than 5 percent of that budget. This threshold is adopted unchanged from the category's umbrella guidance so that the two guides name one condition. Expressed as a ratio, the delegation must carry an expected return ratio of at least 5 to 1. Agents must compute both quantities before dispatch: the intermediate volume from the expected count of retrievals, tool results, and drafts multiplied by their observed median sizes, and the envelope size from the declared output schema's maximum serialized token count.

**The converse, stated so that agents do not delegate cheap work**: Where the expected return ratio falls below 3 to 1, isolation is refused and the work is performed inline, because the returned artifact is then large enough that the caller absorbs most of the material anyway while having paid the full re-establishment cost. Where expected intermediate volume falls below 15 percent of the caller's input budget, isolation is refused regardless of ratio, because the absolute saving cannot repay the fixed cost of packet construction, dispatch, validation, and integration. Where re-establishment cost is estimated at 50 percent or more of expected intermediate volume, isolation is at best break-even and is refused unless a non-cost justification applies.

**Non-cost justifications that override the cost test**: Four conditions justify isolation even where the arithmetic does not. First, overflow: the work cannot fit in the caller's budget at all, so the alternative to isolation is failure rather than a cheaper run. Second, authority separation: the work must touch untrusted content, private data, or consequential effects in a combination the caller must not hold simultaneously. Third, tenant or principal separation: the work belongs to a different authorization domain and may not share a window with the caller's material. Fourth, failure containment: the work can hang, recurse, or exhaust a shared resource, and the caller must survive that. Each must be recorded by name, because a delegation justified by authority separation is measured against containment evidence rather than token savings.

**Parallel isolation has its own arithmetic**: Parallel speedup is sequential critical completion time divided by parallel completion time; parallel efficiency is speedup divided by the count of active branches. Agents must report both alongside the token and monetary multiplier, since a run that completes in a third of the time at fifteen times the cost is the right choice for some workloads and the wrong choice for most. The deployment default caps concurrency at 8 branches and requires parallel efficiency of at least 0.50 measured at 4 branches; efficiency below 0.50 triggers a reduction in branch count before any other tuning.

**Loss of shared state is the structural cost that is not measured in tokens**: An isolated worker sees the world as it was when its packet was issued. It cannot see what the caller learned afterwards, and two parallel workers cannot see each other at all. This is the property that makes isolation useful, because it is what prevents contamination and path dependence, and it is simultaneously the property that makes three specific things unsafe.

**Unsafe case one, parallel branches writing to one durable store**: Two branches whose declared write scopes intersect will produce concurrent versions of the same record with no mechanism between them to detect it. The detection rule is deterministic and runs before launch: intersect every pair of declared write scopes in the branch manifest, treating an undeclared write scope as intersecting everything. The serialization requirement follows: any intersecting pair is either run in a declared order with the later branch reading the earlier branch's committed result, or the overlapping keys are reassigned so that exactly one branch writes each key. Launching an intersecting pair in parallel is prohibited. Where a store must nonetheless accept concurrent writes, conflict detection and resolution are governed by the distributed-memory guidance in the memory-management category and are not re-derived here: this guide's obligation ends at declaring write scopes, detecting overlap, and serializing or partitioning before dispatch.

**Unsafe case two, work whose correctness depends on state that changed after the brief**: Every fact the task packet permits the sub-context to assume is a brief premise carrying a source identifier and the version observed at issue. At admission, the caller re-reads each premise's current version. Any premise whose version advanced between issue and admission is a supersession event, and the result envelope is quarantined rather than admitted. The caller then either shows that the changed premise is immaterial to the payload, by demonstrating that no returned field derives from it, or re-dispatches with a refreshed packet. Admitting a result whose premises have silently moved is the delegation equivalent of the staleness failure mode, and it is invisible without version stamps, which is why the stamps are mandatory rather than recommended.

**Unsafe case three, branch agreement mistaken for corroboration**: Parallel branches sharing a model, a prompt template, a retrieval corpus, or a premise set fail together. Independence, defined in the transactive-memory guidance as the property that a verifier shares neither model, prompt, retrieval corpus, provider, nor premise set with what it verifies, is the test that must pass before agreement between branches counts as evidence. Quorum and majority rules are admissible only across branches that pass the independence test; across dependent branches they convert a single error into a confident answer.

### 1.4 Execution Tier Partition

Context isolation is a hybrid capability whose production failures are almost entirely misassignments of work across three execution tiers. The deterministic tier owns the isolation contract, schema validation of the returned artifact, budget allocation and accounting per sub-context, authority scoping, provenance attachment, and conflict detection between parallel branches, because each requires exactness, reproducibility, and auditability that inference cannot supply. The model tier owns the work performed inside the sub-context and the proposal that a unit of work should be delegated at all, because deciding what a subtask means and whether it separates cleanly is covered by no rule. The hybrid tier is the handoff: the model proposes a decomposition, and the deterministic tier binds it with budgets, scopes, and schemas that the proposal may not exceed.

**Two rules that carry the partition**: A returned artifact failing schema validation is rejected, never parsed leniently. Recovering fields from a malformed payload by inference reintroduces the model tier at exactly the point the boundary exists to make deterministic, and it produces a caller that silently accepts whatever the sub-context happened to emit. A sub-context never widens its own authority scope. It may report that its scope was insufficient and terminate with status `blocked`; the caller's deterministic tier alone recomputes and reissues a scope, and it does so from policy rather than from the sub-context's request text.

**Tier ownership by artifact**:

| Artifact | Owning tier | Authority where the tiers disagree |
| :-- | :-- | :-- |
| Isolation contract, its version, and its five required elements | Deterministic | Deterministic; a delegation missing an element is refused before dispatch |
| Output schema declaration and validation of the returned payload | Deterministic | Deterministic; a failing artifact is rejected, never repaired by inference |
| Budget ledger per sub-context and its enforcement | Deterministic | Deterministic; a sub-context claim that more budget is warranted is advisory only |
| Authority scope computation, credential issue, and expiry | Deterministic | Deterministic; a sub-context never grants or widens its own scope |
| Task packet assembly and transcript exclusion | Deterministic | Deterministic; a dispatch carrying the caller's transcript is blocked |
| Provenance attachment and label join on outbound artifacts | Deterministic | Deterministic; labels are computed from inputs, never asserted by the payload |
| Write-scope overlap detection and the serialization decision | Deterministic | Deterministic; an intersecting pair is serialized regardless of model objection |
| Premise version stamping and supersession detection at admission | Deterministic | Deterministic; a model claim that a premise is unchanged is not evidence |
| Intermediate-material disposal and teardown verification | Deterministic | Deterministic; disposal runs on every terminal status including failure |
| The work performed inside the sub-context | Model | Model; the budget, scope, and schema still bind absolutely |
| Proposal that a unit of work should be isolated, and its decomposition | Model | Model proposes; the deterministic cost test in Section 1.3 may refuse it |
| Semantic adequacy of a schema-valid payload against the objective | Hybrid | Model judges adequacy; deterministic validation gates entry, and rejection outranks a positive judgement |
| Merge of conflicting claims returned by independent branches | Hybrid | Model proposes precedence; the declared reducer rule decides, and unresolved conflict is disclosed rather than smoothed |

***

## II. Operational Framework: Contracted Delegation Into Separate Contexts Under Declared Budget and Authority

The framework assumes a caller holding a governed context budget under the category's umbrella guidance, and a candidate unit of work proposed for delegation. Phases 1 through 5 execute once per delegation. Phase 6 runs only where more than one sub-context is dispatched from the same caller. Phase 7 runs on a schedule against accumulated delegation records and governs whether each boundary survives.

### Phase 1: Delegation Decision and Cost Justification

**Objective**: Determine whether a candidate unit of work should leave the caller's context at all, using a computed cost test and a named dimension inventory, so that isolation is a justified decision rather than a reflex.

#### Step 1.1: Compute the Cost Test Before Any Contract Is Drafted

**Required Actions**:

- Estimate expected intermediate token volume for the candidate unit as the expected count of retrievals, tool results, and drafts multiplied by their observed median serialized sizes for the task class.
- Estimate result envelope size from the output schema the delegation would declare, using the schema's maximum serialized token count rather than an expected value.
- Compute the return ratio as intermediate volume divided by envelope size, and compute intermediate volume as a percentage of the caller's input budget.
- Estimate re-establishment cost as the sum of the sub-context's system instructions, its tool definitions, its task packet, and any retrieval the sub-context must repeat because the caller's evidence will not cross.
- Apply the refusal rules in order and stop at the first that fires: refuse where return ratio is below 3 to 1; refuse where intermediate volume is below 15 percent of the caller's input budget; refuse where re-establishment cost is 50 percent or more of intermediate volume.
- Check the four non-cost justifications before accepting a refusal, and record by name any that applies, since a non-cost justification overrides all three refusal rules.

**Delegation cost test thresholds**:

| Measured quantity | Isolation admitted | Isolation refused | Consequence of breach |
| :-- | :-- | :-- | :-- |
| Return ratio, intermediate tokens to envelope tokens | 5 to 1 or greater | Below 3 to 1 | Work is performed inline; the delegation record states the measured ratio |
| Intermediate volume as share of caller input budget | Above 30 percent | Below 15 percent | Work is performed inline; the fixed dispatch cost cannot be repaid |
| Return ratio between 3 to 1 and 5 to 1 | Admitted only with a named non-cost justification | Refused without one | Dispatch is blocked pending a recorded justification |
| Re-establishment cost as share of intermediate volume | 50 percent or less | Above 50 percent | Refused; the sub-context spends more rebuilding than the caller saves |
| Parallel efficiency at 4 branches | 0.50 or greater | Below 0.50 | Branch count is reduced before any other tuning |

**Required Outputs**:

- A delegation cost record carrying intermediate volume, envelope size, return ratio, budget share, and re-establishment cost, each as a number.
- A verdict of admitted or refused, with the first firing refusal rule named where refused.
- A named non-cost justification where one is invoked, drawn from overflow, authority separation, tenant separation, or failure containment.

**Quality Checkpoints**:

- Every quantity in the cost record is a computed number; an estimate expressed as a qualitative judgement fails the step.
- Exactly 1 verdict is recorded per candidate unit, and a refused verdict carries the rule that fired.
- No delegation proceeds on a return ratio below 3 to 1 without a named non-cost justification recorded before dispatch.

***

#### Step 1.2: Name Every Isolation Dimension the Boundary Must Enforce

**Required Actions**:

- Enumerate the dimensions the boundary must actually enforce, selecting from context, task scope, session scope, tenant, trust domain, capability, execution, resource, and cache, and record why each selected dimension is required.
- State for every selected dimension the enforcement point that implements it, naming a component outside the model in every case.
- Reject the label isolated where no dimension is named, since a boundary without a named dimension cannot be tested and therefore cannot be verified.
- Record explicitly that context isolation alone is a cognitive boundary and not a security boundary wherever the sub-context would share credentials, processes, filesystems, stores, or tools with the caller.
- Verify the platform's actual inheritance semantics for tools, credentials, and filesystem access against the running configuration rather than against documentation, and record the observed result.

**Required Outputs**:

- A dimension inventory naming each required dimension, its justification, and its enforcement point.
- An inheritance verification record stating what the running configuration actually passes to a sub-context by default.

**Quality Checkpoints**:

- At least 1 dimension is named for every delegation; an unnamed boundary is rejected before contract drafting.
- Every named dimension has an enforcement point implemented outside the model.
- The inheritance verification record is derived from observation of the running configuration, not from a documented default.

***

#### Step 1.3: Record the No-Isolation Decision and Its Reason

**Required Actions**:

- Write a no-isolation record whenever the cost test refuses a candidate, naming the candidate, the firing rule, and the measured value.
- Name the alternative operation selected instead, drawn from writing state to a durable store, narrowing selection, or compressing the partition under pressure, and reference the sibling guidance for that operation rather than reimplementing it.
- State the condition that would change the verdict, expressed as the numeric value the failing quantity must reach.
- Retain no-isolation records in the same store as delegation records, so that the refusal rate and its distribution are measurable.

**Required Outputs**:

- A no-isolation record with the candidate, the firing rule, the measured value, and the selected alternative.
- A reversal condition stating the numeric threshold that would admit the candidate later.

**Quality Checkpoints**:

- Every refused candidate produces a record; a silent refusal leaves the refusal rate unmeasurable and fails the step.
- The selected alternative names one operation family, not a general intention to reduce context.
- The reversal condition carries a number, not a description of circumstances.

***

### Phase 2: Isolation Contract and Output Schema Declaration

**Objective**: Fix the five contract elements, with the output schema declared before the objective, so that what crosses back is bounded by structure rather than by the sub-context's discretion.

#### Step 2.1: Declare the Output Schema Before the Objective Is Written

**Required Actions**:

- Write the output schema first, naming every field the caller will consume, its type, its cardinality, whether it is required, its permitted value range or enumeration, and the maximum serialized token count for the payload as a whole.
- Include a required provenance field on every claim-bearing element, carrying a source identifier and a content hash, so that a claim without a traceable source cannot satisfy the schema.
- Include required fields for assumptions relied on, unresolved conflicts, missing evidence, and per-field uncertainty, so that a sub-context can express incompleteness inside the schema rather than in prose beside it.
- Cap any free-text field at a stated token count, and permit at most 1 such field, generated only after the structured payload is fixed.
- Derive the objective from the schema by stating what must be true for each required field to be populated, rather than writing an objective and then guessing what it will return.
- Prefer a constrained-decoding or strict schema-enforcement mechanism where the model interface exposes one, and treat prompt-shaped instruction to return a given structure as a best-effort mechanism that still requires validation on receipt.

**Required Outputs**:

- A versioned output schema with types, cardinalities, required fields, value constraints, and a maximum serialized token count.
- An objective derived from the schema, stating the completion criterion for each required field.
- A declaration of the enforcement mechanism in use, naming whether it constrains generation or only validates on receipt.

**Quality Checkpoints**:

- The schema exists before the objective; an objective drafted first is re-derived from the schema before dispatch.
- Every claim-bearing element carries a required provenance field, so an unsourced claim cannot validate.
- At most 1 free-text field is present and it carries a stated token cap; a schema whose payload is predominantly prose is rejected as an unisolated return.

***

#### Step 2.2: Bind the Budget Ledger and the Terminal Status Vocabulary

**Required Actions**:

- Allocate a budget ledger to the sub-context naming a numeric limit for input tokens, output tokens, tool calls, wall-clock seconds, monetary cost, and retry attempts, with no dimension left unbounded.
- Deduct the allocation from the caller's own ledger at dispatch rather than at return, so that concurrent dispatches cannot collectively overcommit the parent budget.
- Declare the terminal status vocabulary as the closed set `succeeded`, `partial`, `failed`, `blocked`, `timed_out`, `policy_denied`, and prohibit any status outside it.
- Declare the partial-return rule: which of the schema's required fields may be absent under status `partial`, what the coverage fraction measures, and whether the caller is permitted to use a partial at all for this task class.
- Set the sub-context's own deadline strictly below the caller's remaining deadline, and propagate a decreasing deadline to any further nesting, so that a child cannot outlive its parent.
- Cap nesting depth at 2 levels below the caller by default, and require an explicit contract clause for any deeper nesting, since retry and budget multiply with depth.

**Budget and status contract slots**:

| Contract slot | Required content | Default where the contract is silent | Consequence of absence |
| :-- | :-- | :-- | :-- |
| Input and output token limits | Numeric ceilings per dimension | Refuse dispatch | Unbounded consumption against the parent ledger |
| Tool-call and retry ceilings | Integer counts, retries at most 2 | Refuse dispatch | Retry amplification across nesting levels |
| Wall-clock deadline | Seconds, strictly below caller remainder | Refuse dispatch | A child outlives its parent and returns to a closed context |
| Terminal status vocabulary | The 6 closed values | The 6 closed values | An undeclared status is treated as `failed` |
| Partial-return permission | Permitted or prohibited for this task class | Prohibited | An unmarked partial is admitted as if complete |
| Coverage fraction definition | The unit counted and its denominator | Refuse partials | A coverage number that cannot be interpreted |
| Nesting depth | Integer, default 2 | 2 | Uncontrolled fan-out below the caller's visibility |

**Required Outputs**:

- A budget ledger with a numeric limit on every named dimension, deducted from the caller's ledger at dispatch.
- A declared terminal status vocabulary and a partial-return rule naming permitted absent fields and the coverage fraction definition.
- A deadline and nesting-depth declaration.

**Quality Checkpoints**:

- Every budget dimension carries a numeric limit; an unbounded dimension blocks dispatch.
- The sub-context deadline is strictly less than the caller's remaining deadline at dispatch time.
- The partial-return rule states explicitly whether partials are usable for this task class, so that usability is not decided after a partial arrives.

***

#### Step 2.3: Version the Contract and Declare the Disposal Rule

**Required Actions**:

- Assign a contract version and a boundary identifier, and require the sub-context to acknowledge both before performing work, treating a mismatch, an expiry, or an unknown version as a terminal precondition failure rather than as an invitation to proceed.
- Declare the disposal rule for intermediate material, naming for each class whether it is discarded at teardown or externalized to a named durable store under a reference.
- Prohibit inline return of intermediate material unless an explicit clause names the units and their token bound, and record the absence of such a clause as a rejection condition.
- Declare the caller's integration bound: the maximum tokens the admitted artifact may occupy in the caller's window, and the partition it will enter.
- Record the contract in durable storage with its identifiers, so that a delegation can be audited after both contexts are gone.

**Required Outputs**:

- A versioned contract record with boundary identifier, contract version, and an acknowledgement requirement.
- A disposal rule assigning every class of intermediate material to discard or to a named durable store.
- An integration bound naming the caller partition and its token ceiling for the admitted artifact.

**Quality Checkpoints**:

- The sub-context acknowledges the boundary identifier and contract version before any work; an unacknowledged dispatch is terminated.
- Every class of intermediate material has exactly 1 declared destination, and inline return appears only under a clause naming units and a bound.
- The integration bound is less than or equal to the caller partition's remaining capacity at admission time.

***

### Phase 3: Authority Scoping and Inbound Context Construction

**Objective**: Compute the sub-context's authority outside the model and assemble the smallest input set that satisfies the objective, so that the boundary constrains action as well as occupancy.

#### Step 3.1: Compute the Effective Authority Scope Outside the Model

**Required Actions**:

- Begin from an empty allowlist: no tools, no credentials, no durable write permission, and no network egress, and add each capability only by explicit grant.
- Scope every granted credential to the boundary identifier, the principal, the named resources, the permitted operations, a maximum record or byte count, and an expiry not exceeding the sub-context deadline.
- Issue opaque handles held by the execution runtime in preference to secrets that would appear in the sub-context's window, and never forward the caller's own bearer credential.
- Separate read from write and computation from external communication, granting a write capability only where the contract's output schema requires a side effect, and defaulting every delegation to read-only.
- Enforce the allowlist at dispatch, validating the tool identifier, its version or digest, the requested operation, the arguments, the principal, and the destination on every call, rather than relying on the absence of a tool from the prompt text.
- Record the computed scope in the contract record, so that a later audit can compare what was granted against what was used.

**Authority scope ladder by delegation class**:

| Delegation class | Tool grant | Credential grant | Egress | Write permission |
| :-- | :-- | :-- | :-- | :-- |
| Reasoning over admitted evidence only | None | None | None | None |
| Read-only retrieval from a governed store | Retrieval tools by identifier | Read-scoped, resource-bound, expiring | None beyond the named store | None |
| Untrusted-content interpretation | Parsing and extraction tools only | None | None | None; output is quarantined |
| Code or parser execution | Execution tools inside a cell | None | Default-deny with an allowlist | Cell-local ephemeral volume only |
| Proposal of a consequential action | Read tools plus a proposal emitter | Read-scoped only | None | None; the caller commits under its own authority |
| Commit of an approved action | The single committing tool | Audience-bound, single-purpose, expiring | The single named destination | The named records only, under an idempotency key |

**Required Outputs**:

- An authority scope record naming every granted tool, credential, destination, and write target, each with its bound and expiry.
- A dispatch-time enforcement configuration implementing the allowlist outside the model.

**Quality Checkpoints**:

- The scope was computed from policy by the caller's deterministic tier; a scope proposed in the sub-context's own text is never adopted.
- Every granted credential carries an expiry no later than the sub-context deadline and is bound to the boundary identifier.
- The delegation defaults to read-only; a write grant appears only where a required output field names a side effect.

***

#### Step 3.2: Assemble the Task Packet Under the Minimum-Context Rule

**Required Actions**:

- Include the contract identifiers, the objective derived in Step 2.1, the explicit non-goals, the completion criteria, the output schema, the budget ledger, the authority scope, and the deadline.
- Pass evidence as references into a durable store wherever the sub-context can resolve the reference under its own scope, and inline only where the content is small, immutable, and required verbatim.
- Record every fact the sub-context may assume as a brief premise carrying a source identifier and the version observed at issue, so that supersession is detectable at admission.
- Exclude the caller's transcript, its scratch reasoning, sibling results, unrelated principal data, reusable credentials, and any tool granted in anticipation of a need the objective does not state.
- Label every included unit with its trust class and sensitivity, and state the classification ceiling the sub-context may not exceed.
- Bound the packet: a task packet exceeding 25 percent of the sub-context's input budget indicates the work was not separable and returns to Step 1.1 for re-scoping.

**Required Outputs**:

- A task packet carrying identifiers, objective, non-goals, completion criteria, schema, budget, scope, deadline, and labelled input references.
- A premise list with a source identifier and observed version for every assumable fact.
- A packet size measurement expressed as a percentage of the sub-context input budget.

**Quality Checkpoints**:

- The packet contains no element of the caller's transcript; a transcript-bearing packet is blocked and re-specified.
- Every assumable fact carries a source identifier and an observed version; an unversioned premise fails the step.
- Packet size does not exceed 25 percent of the sub-context input budget; above that threshold the delegation returns to the cost test.

***

#### Step 3.3: Select the Execution Cell and Its Egress Policy

**Required Actions**:

- Select the cell strength from the threat rather than from convenience: no cell for reasoning over already-admitted trusted material with no tools; a process-level cell for read-only retrieval; an ephemeral sandboxed cell for code, parsers, browser automation, locally hosted tool servers, and any tool influenced by untrusted content.
- Configure the sandboxed cell with an immutable image or runtime identifier, a non-root identity, a read-only base filesystem, an empty ephemeral working volume, explicit read-only inputs, and an export-only output path.
- Deny egress by default and permit only named destinations, with byte caps and protocol limits, and exclude any metadata endpoint, container socket, credential agent, or caller home directory from the cell.
- Set resource ceilings for processor, memory, process count, file descriptors, disk, output bytes, and wall-clock time, and ensure a timeout terminates the process tree and revokes credentials rather than merely abandoning the wait.
- Treat every file, stream, and standard-output fragment produced inside the cell as untrusted until it passes outbound validation in Phase 5.
- Verify teardown: confirm that the cell is destroyed, its credentials revoked, and its residual artifacts removed after extraction, and record the verification.

**Required Outputs**:

- A cell specification naming strength, image or runtime identifier, filesystem policy, resource ceilings, and egress allowlist.
- A teardown verification record confirming destruction, revocation, and residue removal.

**Quality Checkpoints**:

- Cell strength matches the named threat; a delegation touching untrusted content and consequential tools never runs without an execution cell.
- Egress is default-deny with an explicit destination allowlist; an unrestricted egress configuration blocks dispatch.
- Teardown is verified by observation after every terminal status, including `failed` and `timed_out`, not only after success.

***

### Phase 4: Bounded Execution, Partial Return, and Disposal

**Objective**: Run the isolated unit inside its declared budget and authority ceiling, and terminate through a declared status that names what was and was not completed, so the caller never receives silence or an unmarked fragment.

#### Step 4.1: Execute Under the Budget Ledger and the Authority Ceiling

**Required Actions**:

- Acknowledge the boundary identifier and contract version, and terminate with status `blocked` on a mismatch, an expiry, an unknown version, or an objective the granted scope cannot satisfy.
- Maintain the budget ledger inside the execution runtime rather than inside the sub-context's window, and decrement it on every call, tool invocation, and elapsed interval.
- Halt at the first breached dimension: a sub-context that reaches any numeric ceiling stops work and proceeds to Step 4.2 rather than continuing on a remaining dimension.
- Treat every denied tool call as a terminal signal for that path, never as a prompt to attempt an equivalent operation through a different tool, and record the denial with its reason code.
- Report insufficient authority as status `blocked` carrying the specific capability required and the field it would have populated; never attempt to widen the scope, negotiate for it in prose, or synthesise the missing field.
- Route all untrusted content through the cell's parsing and extraction path, keep it labelled, and never allow it to select a tool, name a destination, or alter an argument bound by the caller.

**Required Outputs**:

- An acknowledgement record naming the boundary identifier and contract version confirmed at start.
- A consumption record showing final values against every budget dimension.
- A denial log listing every refused call with its reason code and the capability requested.

**Quality Checkpoints**:

- The ledger is maintained outside the sub-context's window; a budget figure read back from the window is not evidence and fails the step.
- Execution halts at the first breached dimension; continuing against a remaining dimension is a defect recorded for policy review.
- Zero instances occur of the sub-context proposing, requesting, or assuming an authority beyond its granted scope; any such instance terminates the delegation.

***

#### Step 4.2: Emit a Declared Partial on Budget Exhaustion or Fault

**Required Actions**:

- Emit a result envelope on every termination path, including budget exhaustion, timeout, tool fault, policy denial, and unrecoverable error; returning nothing is prohibited without exception.
- Set the terminal status from the closed vocabulary, and for status `partial` populate the completed unit list, the incomplete unit list, the coverage fraction against its declared denominator, the side effects already performed, and a resumable cursor identifying where work stopped.
- Populate every required schema field that the partial-return rule permits to be absent with an explicit absence marker rather than an empty value, so that absence is distinguishable from a computed empty result.
- Record which incomplete units were not attempted and which were attempted and failed, since the two carry different resumption costs.
- Attach the consumption record and the denial log to the envelope, so the caller can attribute the shortfall to budget, authority, or fault.
- Never reinterpret a timeout as success, never fill an unpopulated field by inference to satisfy the schema, and never substitute a plausible value for an unobtained one.

**Partial-return envelope requirements**:

| Envelope element | Required under `partial` | Required under `failed`, `blocked`, `timed_out`, `policy_denied` |
| :-- | :-- | :-- |
| Terminal status from the closed vocabulary | Yes | Yes |
| Completed unit list with provenance | Yes | Where any unit completed |
| Incomplete unit list, split into unattempted and failed | Yes | Yes |
| Coverage fraction against a declared denominator | Yes | Yes, reported as zero where nothing completed |
| Side-effect ledger with idempotency keys | Yes | Yes |
| Resumable cursor | Yes | Where resumption is possible |
| Consumption record and denial log | Yes | Yes |
| Explicit absence marker on each permitted-absent field | Yes | Yes |

**Required Outputs**:

- A result envelope on every termination path, carrying a terminal status from the closed vocabulary.
- A partial record with completed units, incomplete units split by cause, coverage fraction, side effects, and a resumable cursor where the status is `partial`.

**Quality Checkpoints**:

- 100 percent of terminations produce an envelope; a delegation that returns nothing is recorded as a boundary defect and its cell configuration is reviewed.
- Every partial enumerates what was not completed; a partial listing only completed work is an unmarked partial and is rejected at admission.
- No field is populated by inference to satisfy a required-field constraint; a synthesised value is a validation failure rather than a repair.

***

#### Step 4.3: Dispose of Intermediate Material Under the Declared Rule

**Required Actions**:

- Apply the disposal rule from Step 2.3 to every class of intermediate material, discarding each class or writing it to its named durable store under a reference, with no third destination permitted.
- Externalize rather than discard wherever the material would be expensive to regenerate, is required for audit, or supports a claim in the payload, and place its reference in the envelope's provenance fields.
- Bind every externalized artifact to the boundary identifier, the principal, the sensitivity label, and a retention period, so that the artifact inherits the boundary's constraints rather than escaping them.
- Confirm that no intermediate material appears inline in the envelope beyond an explicit clause naming units and a token bound, and reject the envelope where it does.
- Purge the sub-context's window, scratch volume, and any cell-local cache, and confirm that no residual artifact survives outside the declared durable store.
- Record a disposal receipt naming each class, its destination, its reference where externalized, and its byte or token volume.

**Required Outputs**:

- A disposal receipt naming every class of intermediate material and its destination.
- Durable-store references for every externalized class, bound to the boundary identifier and a retention period.

**Quality Checkpoints**:

- Every class of intermediate material appears exactly once in the disposal receipt; an unaccounted class blocks admission of the envelope.
- Zero intermediate units appear inline in the envelope absent an explicit clause; the presence of any is a contract violation.
- Purge is confirmed by observation of the cell after teardown, not inferred from the teardown command completing.

***

### Phase 5: Outbound Validation, Provenance, and Integration

**Objective**: Admit the returned artifact only after it passes deterministic validation and carries computed provenance and labels, so the caller's context gains a verified unit rather than an assertion.

#### Step 5.1: Validate the Returned Artifact Against the Declared Schema

**Required Actions**:

- Validate the payload against the contract's output schema version, checking field presence, types, cardinalities, enumerations, value ranges, and the maximum serialized token count.
- Reject on any failure and place the envelope in quarantine; do not parse leniently, do not extract fields from surrounding prose, and do not repair a malformed structure by inference.
- Permit at most 1 re-emission attempt against the identical contract, and only where the failure class is malformation rather than authorization denial, semantic inadequacy, or suspected compromise.
- Convert a second failure to terminal status `failed` for the delegation, and record the failure class so the schema or the enforcement mechanism can be revised rather than the retry repeated.
- Verify the terminal status is a member of the closed vocabulary, and treat an absent or unrecognised status as `failed` rather than as an implied success.
- Verify the boundary identifier, contract version, and lineage identifiers on the envelope match the dispatch record, rejecting an envelope whose lineage does not resolve.

**Required Outputs**:

- A validation verdict per envelope, naming pass or the first failing constraint.
- A quarantine record for every rejected envelope, carrying its failure class.
- A re-emission record where one attempt was made, naming the failure class that permitted it.

**Quality Checkpoints**:

- 100 percent of admitted payloads passed schema validation; a leniently parsed payload is a defect regardless of whether its content proved correct.
- At most 1 re-emission occurs per delegation, and never for an authorization denial or a suspected compromise.
- Every envelope's lineage identifiers resolve to a recorded dispatch; an unresolvable envelope is rejected without inspection of its payload.

***

#### Step 5.2: Run the Five Non-Schema Checks and Compute the Label Join

**Required Actions**:

- Run authorization: confirm the payload's referenced resources fall inside the authority scope actually granted, rejecting any claim resting on a resource the sub-context was never permitted to read.
- Run provenance: resolve every source identifier and content hash on every claim-bearing element, and mark any element whose reference does not resolve as unsupported rather than dropping it silently.
- Run premise supersession: re-read the current version of every brief premise and compare against the version stamped at issue, quarantining the envelope on any advance until materiality is shown or the delegation is reissued.
- Run label join: compute the artifact's sensitivity and trust labels as the most restrictive combination of every contributing input's labels, and record that summarisation and extraction inside the sub-context lowered nothing.
- Run destination and semantic bounds: confirm the payload names no destination outside the granted scope, contains no instruction directed at the caller, carries no proposed tool definition, and falls inside the declared value ranges for each field.
- Refuse declassification except through a named policy transform with a verifier, a reason code, a scope, and an audit record; a confident payload is never a declassification authority.

**Outbound check inventory**:

| Check | What it verifies | Failure action |
| :-- | :-- | :-- |
| Schema | Structure, types, cardinality, token cap | Reject to quarantine; at most 1 re-emission |
| Authorization | Every referenced resource sits inside the granted scope | Reject; review why the resource was reachable |
| Provenance | Every claim resolves to a source identifier and hash | Mark the element unsupported; never drop silently |
| Premise supersession | No brief premise advanced between issue and admission | Quarantine; show immateriality or reissue |
| Label join | Outbound labels equal the restrictive join of inputs | Raise the labels and re-evaluate destination policy |
| Destination and semantics | No external destination, instruction, or tool definition | Reject; record as a boundary-crossing attempt |

**Required Outputs**:

- A check record with a verdict for each of the six checks.
- A computed label set attached to the artifact, with the contributing inputs named.
- An unsupported-element list where any provenance reference failed to resolve.

**Quality Checkpoints**:

- All 6 checks run independently; a schema pass never substitutes for any of the other five.
- Labels are computed from contributing inputs rather than copied from the payload; a payload-asserted label is ignored.
- Zero declassifications occur outside a named policy transform with an audit record.

***

#### Step 5.3: Admit the Artifact Into the Caller's Working Set Under Its Integration Bound

**Required Actions**:

- Admit the artifact into the partition named in the contract's integration bound, subject to that partition's admission gate and remaining capacity under the category's umbrella budget rules.
- Externalize any admitted element exceeding the integration bound to a durable store and admit a reference, rather than allowing the artifact to consume the partition it was sized against.
- Attach the boundary identifier, the contract version, the sub-context lineage, and the computed labels to every admitted element, so downstream use carries the boundary's constraints forward.
- Reconcile the artifact against the caller's existing working set, surfacing contradictions rather than overwriting, and treating a returned value that conflicts with a current caller value as a contradiction to disclose.
- Record the delegation outcome: measured intermediate volume where the sub-context reported it, measured envelope size, achieved return ratio, consumption against each budget dimension, terminal status, and the check verdicts.
- Close the caller's ledger entry, releasing any allocated but unconsumed budget back to the parent ledger.

**Required Outputs**:

- An admitted artifact carrying boundary identifier, contract version, lineage, and computed labels.
- A delegation outcome record with measured volumes, achieved return ratio, consumption, status, and verdicts.
- A reconciliation record naming any contradiction between the artifact and the caller's existing working set.

**Quality Checkpoints**:

- Admitted tokens do not exceed the integration bound; an over-bound artifact is externalized and referenced instead.
- The achieved return ratio is recorded as a measured number and compared against the estimate from Step 1.1, so the estimator is correctable.
- No returned value silently overwrites a current caller value; every conflict is surfaced for adjudication.

***

### Phase 6: Parallel Branch Conflict Detection and Serialization

**Objective**: Detect, before launch, every hazard created by branches that cannot see each other, and either remove it by partitioning or contain it by serializing, so that parallel isolation does not trade contamination for corruption.

#### Step 6.1: Build the Branch Manifest and Compute the Overlap Verdict

**Required Actions**:

- Create a branch manifest before any branch is launched, naming for each branch its identifier, objective, output schema, budget, authority scope, write scope, and expected artifact.
- Declare each write scope as an explicit set of durable-store keys, paths, records, or resources, and treat an undeclared write scope as intersecting every other scope.
- Compute the overlap verdict by intersecting every pair of declared write scopes, returning disjoint, intersecting, or undeclared for each pair.
- Partition by independent question, source family, hypothesis, artifact, time range, or method, preferring a decomposition whose write scopes are disjoint by construction over one that requires later reconciliation.
- Assign a single writer per contested key wherever partitioning can eliminate an intersection, since eliminating the conflict is cheaper than detecting and resolving it.
- Record the independence properties of the branch set: whether branches share a model, a prompt template, a retrieval corpus, or a premise set, since agreement across dependent branches is not corroboration.

**Required Outputs**:

- A branch manifest with all seven fields populated for every branch.
- An overlap verdict for every branch pair, with intersecting keys enumerated where the verdict is intersecting.
- An independence record naming every shared model, prompt, corpus, or premise across the branch set.

**Quality Checkpoints**:

- Every branch declares a write scope; an undeclared scope is treated as intersecting and blocks parallel launch.
- The overlap verdict covers 100 percent of branch pairs; a partial computation is not a verdict.
- The independence record is populated before merge policy is chosen, because a dependent branch set forbids quorum rules.

***

#### Step 6.2: Launch Under Independent Budgets and Serialize Intersecting Branches

**Required Actions**:

- Serialize every intersecting pair: run them in a declared order in which the later branch reads the earlier branch's committed result, or reassign the overlapping keys so exactly one branch writes each.
- Refuse to launch an intersecting pair in parallel under any justification, including deadline pressure, since the resulting concurrent versions are undetectable from inside either branch.
- Allocate independent budgets, retry counts, rate allowances, and concurrency slots per branch, so that one branch cannot consume another's allocation.
- Cap total concurrency at 8 branches by default, and reduce the cap where measured parallel efficiency at 4 branches falls below 0.50.
- Accept status and metadata heartbeats from running branches, and never stream one branch's intermediate material into another, since doing so reintroduces the path dependence the fan-out was intended to remove.
- Retry only branches whose failure is classified transient, issuing a new branch identifier linked to the original and preserving the contract unchanged; never retry an authorization denial, a deterministic validation failure, or a suspected compromise without a reviewed contract change.
- Escalate a branch that fails 2 times to a bounded fallback: a narrower subtask, a different method inside the same boundary, or a declared coverage gap.

**Required Outputs**:

- A launch record naming which branches ran in parallel and which were serialized, with the serialization order.
- Per-branch budget allocations with independent retry and concurrency counters.
- A retry record linking every reissued branch to its predecessor with a transient-failure classification.

**Quality Checkpoints**:

- Zero intersecting pairs ran in parallel; a single instance is a boundary defect requiring reconciliation of the affected keys.
- Every branch holds an independent budget; a shared retry or rate allowance across branches fails the step.
- No branch is retried more than 2 times, and no retry occurs on an authorization denial or a suspected compromise.

***

#### Step 6.3: Merge Under a Declared Reducer Rule

**Required Actions**:

- Fix the reducer rule before fan-out, selecting per field class from deterministic union for independent facts, evidence-weighted adjudication for conflicting claims, quorum only across branches that pass the independence test, or a dedicated reducing sub-context holding no consequential tools.
- Prohibit last-writer-wins as a merge rule for any field the caller will act on, and where a store nonetheless resolves concurrency that way, name the loss explicitly and route the affected fields to a deterministic reducer instead.
- Admit only validated envelopes into the merge, since a reducer receiving an unvalidated payload is a new boundary crossing that has skipped Phase 5.
- Preserve provenance, labels, minority findings, and branch failures through the merge, computing the merged artifact's labels as the restrictive join across all contributing branches.
- Run a cross-branch consistency check, and where a contradiction is material, dispatch a fresh adjudication sub-context carrying only the competing claims and their evidence, never the branch identities or their prior standing.
- Report coverage honestly: name every branch that failed, timed out, or returned a partial, and state the resulting gap rather than presenting the merged artifact as complete.

**Required Outputs**:

- A declared reducer rule per field class, fixed before fan-out.
- A merged artifact carrying preserved provenance, joined labels, and retained minority findings.
- A coverage statement naming every failed, timed-out, and partial branch and the gap each leaves.

**Quality Checkpoints**:

- The reducer rule was declared before fan-out; a rule chosen after results arrive is selection on the outcome and fails the step.
- No quorum or majority rule is applied across branches sharing a model, prompt, corpus, or premise set.
- The merged artifact's labels equal the restrictive join across contributing branches; selecting the least restrictive label is a containment failure.

***

### Phase 7: Boundary Measurement and Retirement

**Objective**: Prove that each boundary contains what it claims and costs less than it saves, and retire boundaries that do neither, so that isolation remains a measured decision after deployment.

#### Step 7.1: Measure Isolation Overhead Against a Matched Baseline

**Required Actions**:

- Establish a matched non-isolated baseline for each delegation class, measuring quality, latency, tokens, and monetary cost on the same task instances.
- Compute token overhead as isolated-run tokens plus packet and envelope tokens plus caller integration tokens minus baseline tokens, and report it both as a difference and as a ratio to baseline.
- Decompose overhead into useful sub-context work, re-establishment cost, duplicated retrieval, crossing validation, and merge cost, since only the first is the work the delegation was for.
- Compute achieved return ratio per delegation and compare it against the estimate recorded in Step 1.1, reporting the estimator's error distribution rather than a single average.
- Report parallel speedup and parallel efficiency alongside the token and cost multiplier for every fan-out class.
- Segment every metric by delegation class, model, tool set, cell strength, and contract version, since aggregate stability conceals a regression confined to one segment.

**Required Outputs**:

- A matched-baseline comparison per delegation class with quality, latency, token, and cost figures.
- An overhead decomposition attributing each component of the difference.
- An estimator error distribution comparing predicted against achieved return ratios.

**Quality Checkpoints**:

- Overhead is computed against a matched baseline on the same task instances; a comparison against a different workload is not a measurement.
- Re-establishment cost is reported separately from useful sub-context work; an undivided total cannot justify a boundary.
- Metrics are reported by segment, not only in aggregate.

***

#### Step 7.2: Run Containment Probes Against the Boundary

**Required Actions**:

- Plant a unique canary in the caller's context that is absent from every admitted input set, and confirm it never appears in any sub-context, envelope, log, cache entry, or merged artifact.
- Probe contamination with paired clean and contaminated runs, measuring the proportion of outputs in which material the boundary should have excluded measurably changed the result.
- Probe authority containment by attempting, from inside a sub-context, each operation outside its granted scope, and confirm every attempt is denied at the enforcement point rather than declined by the model.
- Probe outbound validation by returning envelopes that are schema-valid but carry an unresolvable provenance reference, an out-of-scope resource, an embedded instruction, and a proposed tool definition, confirming each is rejected.
- Probe partial handling by forcing budget exhaustion mid-task and confirming an enumerating partial is produced and correctly refused where the contract prohibits partials.
- Vary the probes adaptively rather than replaying a fixed set, since a boundary tuned against a static probe set demonstrates only that it blocks those probes.
- Classify each success by the earliest enforcement point that failed, and add the probe to a permanent regression suite after the enforcement gap is closed.

**Required Outputs**:

- A probe result set with a pass or fail verdict per probe class and the earliest failing enforcement point for each failure.
- A contamination rate and a leakage rate with declared denominators.
- A regression suite entry for every probe that succeeded before remediation.

**Quality Checkpoints**:

- Successful canary appearances outside the boundary are 0; any occurrence blocks the boundary from release.
- Every authority probe is denied at an enforcement point outside the model; a refusal produced by the model alone does not count as containment.
- Probes are varied across runs; a fixed probe set that has passed unchanged for 3 consecutive cycles is refreshed.

***

#### Step 7.3: Retain, Strengthen, or Retire the Boundary

**Required Actions**:

- Compare each boundary's measured containment benefit against its measured overhead, using the contamination rate, leakage rate, blast-radius containment, and overhead decomposition from the preceding steps.
- Retire a boundary that shows no measured reduction in contamination, leakage, or blast radius together with a token, latency, or merge-error increase, and record the measured values that justified retirement.
- Strengthen a boundary whose probes revealed an enforcement gap, closing the gap at the enforcement point rather than adding the specific probe payload to a filter.
- Never retire a boundary justified by tenant separation, authority separation, or a regulatory constraint on the basis of overhead alone, since those boundaries are not measured against token savings.
- Assign every retained boundary an owner, a review date, a policy version, and a stated retirement criterion expressed as a numeric threshold.
- Re-run the full probe suite after any change to the model, prompt template, tool set, cell runtime, cache topology, output schema, or policy version.

**Required Outputs**:

- A retain, strengthen, or retire verdict per boundary, with the measured values that produced it.
- An ownership record per retained boundary with owner, review date, policy version, and numeric retirement criterion.

**Quality Checkpoints**:

- Every verdict cites measured values; a boundary retained on architectural intent alone fails the step.
- No boundary justified by tenant, authority, or regulatory separation is retired for overhead.
- The probe suite is re-run after every change in the named change classes, not only on a calendar schedule.

***

## III. Implementation Guidance for AI Agents

AI agents operating context isolation must follow systematic protocols ensuring that every boundary is contracted before it exists, enforced outside the model, and measured after use. The following guidance translates the delegation procedure into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Delegation Gate Agent**: Computes the cost test in Step 1.1 and returns admitted or refused with the firing rule. It may refuse a delegation the model tier proposed, and it owns the no-isolation record.
2. **Contract Agent**: Owns the isolation contract, the output schema, the budget ledger, and the disposal rule. It alone may amend a contract, and every amendment is versioned and re-acknowledged.
3. **Scope Authority**: Computes the effective authority scope from policy, issues bound credentials, and enforces the tool allowlist at dispatch. It never accepts a scope request expressed in a sub-context's text.
4. **Isolated Executor**: Performs the work inside one sub-context under one contract. It may not widen a scope, extend a budget, alter an output schema, or return intermediate material inline.
5. **Boundary Validator**: Runs the six outbound checks, computes the label join, and holds rejection authority. Its rejection is final and is never overridden by a judgement that the payload looked correct.
6. **Branch Coordinator**: Builds the branch manifest, computes the overlap verdict, enforces serialization, and applies the declared reducer rule. It holds no consequential tools.
7. **Instrumentation Agent**: Writes delegation and no-isolation records, computes overhead and containment metrics, and may withhold a boundary from release where evidence is missing.

**Boundary Disclosure Rule**: Delegation records carry decision metadata and never hidden reasoning content. Log boundary identifiers, contract versions, reason codes, consumption figures, check verdicts, label joins, provenance references, and content hashes. Do not persist a sub-context's private reasoning trace, raw untrusted payloads, credentials, or cross-principal content; a hash or a durable-store reference stands in every case. Where an admission cannot be justified without exposing withheld content, record it as unjustified and escalate.

**Workflow Execution Pattern**:

```
STATE: Outbound_Admission
INPUTS:
  1. Result envelope from the isolated executor
  2. Dispatch record with contract version and granted scope
  3. Premise list with versions stamped at issue
ACTIONS:
  1. Resolve lineage identifiers against the dispatch record
  2. Validate payload against the declared output schema version
  3. Run authorization, provenance, supersession, label join, destination checks
  4. Compute admitted token count against the integration bound
VALIDATION:
  - terminal_status IN closed_vocabulary
  - schema_valid == TRUE
  - lenient_parse_attempted == FALSE
  - out_of_scope_resource_count == 0
  - superseded_premise_count == 0
  - admitted_tokens <= integration_bound
  - inline_intermediate_units == 0
TRANSITIONS:
  IF all_validations_pass THEN next_state = Admit_And_Record_Outcome
  IF schema_valid == FALSE AND reemissions_used < 1
     THEN next_state = Request_Single_Reemission
  IF superseded_premise_count > 0 THEN next_state = Quarantine_Pending_Materiality
  IF out_of_scope_resource_count > 0 THEN next_state = Reject_And_Review_Scope
  ELSE next_state = Terminal_Failed
```

**Two-Phase Action Pattern**: Emit the contract, schema, budget, and scope as a dispatch plan without creating the sub-context; validate the plan against the cost test and the scope ladder while no tokens have been spent; create the sub-context only after the plan passes, recording the dispatch in the same operation that deducts the budget.

**Approval Gate**: Human authorisation is required before granting a write or egress capability to any sub-context that will process untrusted content, before any delegation projected to consume more than 40 percent of the caller's remaining budget, before any widening of an authority scope beyond a previously approved maximum, before permitting inline return of intermediate material, and before retiring a boundary justified by tenant, authority, or regulatory separation. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the contract, budget ledger, dispatch record, and premise versions in durable state, since a delegation routinely outlives the window that issued it.
- Deduct the sub-context allocation from the caller's ledger at dispatch, so concurrent delegations cannot collectively overcommit the parent budget.
- Write a handoff record at every context boundary the caller itself crosses while a delegation is outstanding, naming the open boundary identifiers and their expected artifacts.
- Count packet construction, validation, and integration tokens toward isolation overhead rather than treating them as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Delegation Justification (After Phase 1)**

- **Automated Check**: Return ratio, budget share, and re-establishment cost are computed numbers; a refused verdict names the firing rule; a ratio between 3 to 1 and 5 to 1 carries a named non-cost justification; at least 1 isolation dimension is named with an enforcement point outside the model.
- **Agent Action on Pass**: Proceed to contract drafting.
- **Agent Action on Failure**: Halt and return the missing quantity; no contract is drafted against an unjustified delegation.
- **Human Review Trigger**: A delegation projected above 40 percent of the caller's remaining budget, or a boundary whose only justification is regulatory.

**Checkpoint 2: Contract Completeness (After Phase 2)**

- **Automated Check**: All 5 contract elements present; output schema declared before the objective; every budget dimension numerically bounded; sub-context deadline strictly below the caller's remainder; partial-return permission stated explicitly; every intermediate class assigned exactly 1 disposal destination.
- **Agent Action on Pass**: Proceed to scoping.
- **Agent Action on Failure**: Halt; a contract missing an element is not dispatched with a defaulted value.
- **Human Review Trigger**: Any request to permit inline return of intermediate material.

**Checkpoint 3: Scope and Packet Integrity (After Phase 3)**

- **Automated Check**: Allowlist derived from an empty start; every credential bound and expiring at or before the deadline; zero transcript content in the packet; every premise version-stamped; packet size at or below 25 percent of the sub-context input budget; cell strength matches the named threat; egress default-deny.
- **Agent Action on Pass**: Dispatch and deduct the budget.
- **Agent Action on Failure**: Block dispatch and re-specify the failing element only.
- **Human Review Trigger**: Any write or egress grant to a sub-context that will process untrusted content.

**Checkpoint 4: Termination Integrity (After Phase 4)**

- **Automated Check**: An envelope exists for every termination; terminal status is a member of the closed vocabulary; a `partial` enumerates incomplete units split into unattempted and failed and carries a coverage fraction; the disposal receipt accounts for every intermediate class; teardown and purge verified by observation.
- **Agent Action on Pass**: Proceed to outbound validation.
- **Agent Action on Failure**: Record a boundary defect, quarantine the envelope, and review the cell configuration before any retry.
- **Human Review Trigger**: More than 10 percent of delegations in a class returning no envelope.

**Checkpoint 5: Admission Validity (After Phase 5)**

- **Automated Check**: All 6 outbound checks executed independently; zero lenient parses; at most 1 re-emission; zero superseded premises admitted without a materiality finding; labels computed from contributing inputs; admitted tokens within the integration bound.
- **Agent Action on Pass**: Admit the artifact and close the ledger entry.
- **Agent Action on Failure**: Quarantine; an artifact failing any check is never admitted with a warning attached.
- **Human Review Trigger**: Any admitted artifact requiring a declassification, or any envelope naming a resource outside the granted scope.

**Checkpoint 6: Parallel Safety (After Phase 6)**

- **Automated Check**: Every branch declares a write scope; the overlap verdict covers 100 percent of pairs; zero intersecting pairs launched in parallel; independent budgets per branch; reducer rule declared before fan-out; no quorum applied across dependent branches.
- **Agent Action on Pass**: Release the merged artifact with its coverage statement.
- **Agent Action on Failure**: Halt the merge, reconcile the affected keys, and report the coverage gap rather than a completed artifact.
- **Human Review Trigger**: Any intersecting pair that ran in parallel, or a merged artifact whose contributing branches share a model and were resolved by quorum.

**Checkpoint 7: Boundary Evidence (After Phase 7)**

- **Automated Check**: Matched baseline present; overhead decomposed into its 5 components; canary appearances outside the boundary equal 0; every authority probe denied at an enforcement point; every retained boundary carries an owner, a review date, and a numeric retirement criterion.
- **Agent Action on Pass**: Release the boundary for continued use.
- **Agent Action on Failure**: Withhold release and name the missing evidence; no boundary is released on architectural intent.
- **Human Review Trigger**: Any successful canary appearance, or a proposal to retire a boundary justified by tenant or authority separation.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
BOUNDARY_ID:
CONTRACT_VERSION:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Unstructured Return Defeating the Boundary**

- **Symptoms**: The envelope's payload is predominantly free text; the caller reads the whole return to extract an answer; admitted tokens approach the intermediate volume; the achieved return ratio falls below the estimate by more than 50 percent.
- **Diagnostic Steps**: Compare the declared schema against the returned payload field by field, and determine whether the schema permitted a large free-text field, whether the enforcement mechanism only validates on receipt, or whether the objective was written before the schema.
- **Resolution Protocol**: Option A, tighten the schema by removing or capping the free-text field and re-deriving the objective from it. Option B, move to a constrained-decoding mechanism where the interface exposes one, so structure is enforced during generation rather than checked afterwards. Option C, split the delegation so each sub-context returns a narrower typed artifact. Option D, refuse the delegation under the cost test, since a task whose result cannot be typed is not separable.
- **Escalation Trigger**: A second unstructured return under the same contract version halts the delegation class until the schema is revised; this class is never resolved by asking for a shorter summary.

**Error Type 2: Fluent but Under-Contextualised Result**

- **Symptoms**: The payload validates and reads as confident, but a downstream check finds it omitted a dependency, contradicted a caller-held constraint, or answered a narrower question than the objective.
- **Diagnostic Steps**: Identify the specific fact the sub-context lacked, and determine whether it was excluded from the input set, present as an unresolvable reference, or absent from the premise list.
- **Resolution Protocol**: Option A, add the single missing fact or reference to the packet and reissue under a new sub-context identifier. Option B, add a required schema field forcing the sub-context to state the dependency it relied on. Option C, add a required-fact fixture to the probe suite so the omission is detected before admission next time.
- **Escalation Trigger**: A third under-contextualised return in one delegation class returns the class to Step 1.1, since the work is not separable at the chosen granularity. Granting the caller's transcript is never a resolution.

**Error Type 3: Cross-Branch Write Corruption**

- **Symptoms**: A durable record holds a value no single branch produced; a branch's committed result disappears; reconciliation reports concurrent versions with no ordering between them.
- **Diagnostic Steps**: Recompute the overlap verdict from the branch manifest, identify the intersecting keys, and determine whether the pair was launched in parallel or whether a write scope was undeclared.
- **Resolution Protocol**: Option A, reassign the contested keys to a single writer and reissue the affected branches. Option B, serialize the intersecting pair in a declared order with the later branch reading the earlier committed result. Option C, route the contested field class to a deterministic reducer and remove it from branch write scopes entirely.
- **Escalation Trigger**: Any intersecting pair found to have run in parallel halts further fan-out in that class until write scopes are declared for every branch; conflict resolution semantics beyond detection and serialization are governed by the distributed-memory guidance and are not resolved here.

**Error Type 4: Premise Supersession Admitted Undetected**

- **Symptoms**: An admitted artifact rests on a value the caller has since replaced; two admitted artifacts from sequential delegations disagree about the same fact; a decision reverses when the same delegation is repeated.
- **Diagnostic Steps**: Compare every premise's stamped version against its version at admission, and determine whether the premise carried a version at issue at all.
- **Resolution Protocol**: Option A, quarantine the artifact and demonstrate that no returned field derives from the changed premise. Option B, reissue the delegation with a refreshed packet under a new identifier. Option C, shorten the delegation deadline so the window in which a premise can move is smaller than the observed change interval for that source.
- **Escalation Trigger**: Any premise found unversioned at issue blocks the contract version from further dispatch until version stamping is added; this class is never resolved by re-running the same brief.

**Error Type 5: Boundary Laundering and Authority Escape**

- **Symptoms**: An admitted payload names a destination, contains an instruction, or proposes a tool; a sub-context performs an operation outside its granted scope; content from a lower trust class appears in a higher-privilege action.
- **Diagnostic Steps**: Trace the crossing that admitted the content, identify the earliest enforcement point that should have denied it, and determine whether the enforcement was implemented outside the model or only stated in a prompt.
- **Resolution Protocol**: Option A, close the enforcement gap at the identified point, revoke the credentials reachable from the sub-context, and invalidate the artifacts and cache entries derived from it. Option B, replace free-text return with typed extraction so attacker-influenced text cannot populate an action parameter. Option C, remove the capability from the scope ladder for that delegation class, so the combination cannot recur.
- **Escalation Trigger**: Any successful escape halts the delegation class immediately, triggers credential revocation and downstream lineage tracing, and requires a regression probe before the class reopens. This class is never resolved by adding the specific payload to a filter.

**Error Type 6: Isolation Overhead Dominates**

- **Symptoms**: Token overhead exceeds the matched baseline by more than 6 times without a named non-cost justification; re-establishment cost exceeds useful sub-context work; parallel efficiency falls below 0.50; merge error rises while contamination is unchanged.
- **Diagnostic Steps**: Decompose overhead into useful work, re-establishment, duplicated retrieval, crossing validation, and merge cost, and locate the dominant component by segment.
- **Resolution Protocol**: Option A, reduce branch count and re-measure efficiency. Option B, shrink the packet and the schema so less crosses in each direction. Option C, reuse an immutable evidence manifest across branches so retrieval is not duplicated. Option D, retire the boundary under Step 7.3 where it shows no containment benefit.
- **Escalation Trigger**: Overhead above 6 times baseline for 2 consecutive measurement cycles escalates for policy review. A boundary justified by tenant, authority, or regulatory separation is never weakened to reduce overhead.

**Troubleshooting Decision Tree**:

```
DELEGATION FAILS A CHECKPOINT
├─ RETURN DEFECT
│   ├─ Payload is predominantly prose → Tighten schema; re-derive objective; no second summary request
│   ├─ Schema invalid → At most 1 re-emission; then terminal failed; never lenient parse
│   └─ No envelope returned → Record boundary defect; review cell teardown before any retry
├─ CONTEXT DEFECT
│   ├─ Missing dependency in a valid payload → Add the single fact; reissue; never grant the transcript
│   ├─ Premise version advanced → Quarantine; show immateriality or reissue with refreshed packet
│   └─ Premise unversioned at issue → HALT contract version; add version stamping
├─ PARALLEL DEFECT
│   ├─ Write scopes intersect → Serialize or reassign to one writer before launch
│   ├─ Undeclared write scope → Treat as intersecting; block parallel launch
│   └─ Quorum across dependent branches → Discard the quorum; adjudicate on evidence
├─ AUTHORITY DEFECT
│   ├─ Out-of-scope resource in payload → Reject; revoke credentials; trace lineage
│   ├─ Instruction or tool definition in payload → Reject; record crossing attempt; add probe
│   └─ Scope widened from inside → HALT class; scope is recomputed only from policy
└─ ECONOMIC DEFECT
    ├─ Overhead above 6x baseline → Reduce branches, shrink contract, or retire boundary
    └─ Return ratio below estimate by half → Correct the estimator; re-run the cost test
```

### D. Performance Metrics and Continuous Learning

**Containment Metrics**:

- **Contamination rate**: Outputs in which material the boundary should have excluded measurably changed the result, over evaluated outputs (target: no more than 2 percent; any harmful contamination blocks release).
- **Leakage rate**: Successful unauthorized source-to-sink disclosures over attempted probes (target: 0; a payload that reached an unauthorized model counts as a disclosure even where external transmission failed).
- **Blast-radius containment**: Injected failures confined to the declared cell over all injected failures (target: at least 95 percent, with maximum observed spread depth reported).
- **Boundary-violation counts**: Denied and successful violations counted separately by rule, since rising denials indicate attack or drift even where successes remain 0.

**Economic Metrics**:

- **Isolation token overhead**: Isolated total tokens over matched baseline tokens (target: no more than 6 times; above that requires a named non-cost justification).
- **Re-establishment share**: Re-establishment cost over total sub-context tokens (target: no more than 30 percent; above 50 percent refuses the delegation class).
- **Achieved return ratio**: Intermediate tokens over envelope tokens, measured per delegation (target: at least 5 to 1, matching the admission threshold).
- **Parallel efficiency**: Speedup over active branch count (target: at least 0.50 at 4 branches).

**Reliability Metrics**:

- **First-attempt contract success**: Envelopes passing all 6 outbound checks on first return over launched sub-contexts (target: at least 85 percent).
- **Unmarked partial rate**: Partials failing to enumerate incomplete units over all partials (target: 0).
- **Silent insufficiency rate**: Admitted artifacts later found under-contextualised by downstream review over admitted artifacts (target: no more than 5 percent).
- **Estimator error**: Absolute difference between predicted and achieved return ratio over predicted ratio (target: no more than 40 percent at the 90th percentile).

**Learning and Adaptation Mechanisms**:

- **Schema tightening from measured returns**: Where a delegation class repeatedly returns a payload dominated by one field, split or cap that field in the next schema version rather than instructing the sub-context to be briefer.
- **Scope narrowing from usage**: Compare granted scopes against used scopes per class, and remove capabilities unused across 20 consecutive delegations.
- **Estimator recalibration**: Refit the intermediate-volume and envelope-size estimators against achieved measurements per delegation class, since the cost test is only as good as its inputs.
- **Probe refresh**: Retire probes passing unchanged for 3 cycles and generate new ones from recent enforcement gaps, so the suite does not fossilise.
- **Threshold recalibration**: Recompute every numeric threshold per delegation class against observed outcomes; the values stated here are deployment defaults, not constants.

**Human-in-the-Loop Boundaries**: Widening an authority scope, permitting inline return of intermediate material, declassifying a labelled artifact, approving a write or egress grant to a sub-context handling untrusted content, and retiring a boundary justified by tenant, authority, or regulatory separation are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs where work happens and what crosses between contexts, not the content of any particular work. Its phases hold wherever a unit of work can be separated, budgeted, typed on return, and bounded in authority.

### 4.1 Cross-Domain Application Patterns

**Research and evidence synthesis**: Per-source extraction is the archetypal isolated unit: each source produces a large intermediate volume and a small typed set of claims, so return ratios of 20 to 1 are common and the cost test admits readily. Branches partition by source family, and their write scopes are disjoint by construction because each writes only its own claim set. The reducer holds no retrieval tools and receives validated claim envelopes rather than raw documents. Independence fails where every branch retrieves from one corpus, so quorum over agreeing claims is prohibited and adjudication runs on evidence weight instead.

**Software engineering and code modification**: The write scope is the file or module set, and the one-writer-per-scope rule removes conflicts before they exist rather than reconciling them afterwards. Isolated execution cells are mandatory because parsers, build tools, and dependency installers are attacker-influenced surfaces. The output schema names changed paths, test verdicts, and diagnostics rather than a narrative of the work. Premise supersession is frequent here, since a base revision moves during a long delegation, so version stamps are the base commit identifiers and admission compares against the current head.

**Regulated decision support**: Authority separation, not token savings, justifies the boundary, so the delegation is measured against containment evidence and the overhead test does not apply. Sub-contexts that read protected records hold no external destination, and sub-contexts that communicate externally hold no protected-record access. Every crossing is logged with its authorization decision, its label join, and its policy version, and the delegation record becomes a deliverable rather than a diagnostic aid. Partial returns are usually prohibited for this class, since an incomplete determination is not a usable determination.

**Multi-principal service operations**: The boundary is a hard authorization boundary rather than a cognitive one. Principal identity is derived server-side from authenticated execution context and injected into every store, index, cache, queue, and log lookup, never taken from a payload field or a filename. Caches are keyed by principal and authorization digest, and are disabled entirely where partitioning cannot be demonstrated. Cross-principal probes run against every path including asynchronous completions, retries, exports, and administrative tooling, because a boundary that holds on the request path and leaks on the export path has not held.

**Industrial and field operations**: Reversibility varies within one run, so authority scopes bind per action class: a provisional plan is reversible and may be produced under a broad read scope, while a dispatched instruction is not and requires a single-purpose committing capability under an idempotency key. Deadlines are short, so nesting depth is capped at 1 and partials are permitted with a coverage fraction, since most of a route delivered on time beats a complete plan delivered late.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk single-principal work**: Apply the cost test and the output schema, and omit the execution cell, the label join, and the containment probes. A boundary here is a token-economy decision, and overhead above 2 times baseline indicates the cost test should have refused it.
- **High-risk or irreversible work**: Retain every phase, mandate an execution cell, prohibit partials unless the contract names them usable, and bind the approval gate before any write or egress grant. Abstention through status `blocked` is preferred over an unverified completion.
- **Strict latency budgets**: Reduce nesting depth and branch count rather than removing outbound checks, since removing checks removes containment while reducing fan-out only reduces parallelism. Where latency forbids any delegation, the cost test refuses and the work runs inline under a declared no-isolation record.
- **Large parallel fan-outs**: Above 8 branches, declare write scopes at a coarser granularity so the overlap computation stays tractable, freeze a shared immutable evidence manifest to prevent duplicated retrieval, and report coverage gaps by branch rather than as an aggregate completeness claim.
- **Long-running autonomous operation**: Persist contracts, ledgers, and premise versions outside working context, write a handoff record whenever the caller crosses its own context boundary with a delegation outstanding, and re-run premise supersession at every handoff so drift is detected rather than inherited.

***

## V. Limitations and Considerations

**Isolation multiplies cost by construction**: Every sub-context rebuilds working state the caller already held, and reported production figures place multi-agent token consumption at roughly fifteen times chat interactions in one measured system. On tightly coupled work the boundary costs more than it saves and hides evidence the caller needed. The mitigation is the cost test in Step 1.1, with its three refusal rules and its requirement that a return ratio below 5 to 1 carry a named non-cost justification.

**A schema constrains structure, not adequacy**: A payload can satisfy every type, cardinality, and range constraint while answering a narrower question than the objective, omitting a dependency, or resting on a source the caller would have rejected. The mitigation is the five non-schema checks in Step 5.2 and the silent-insufficiency metric in Section III.D, which measures how often a validated artifact was later found inadequate and returns the delegation class to re-scoping at 5 percent.

**Schema enforcement varies by interface**: Some model interfaces constrain generation against a schema so that a non-conforming payload cannot be produced, while others accept a schema as an instruction and make a best effort, and the two are not interchangeable. Treating a best-effort interface as a guarantee produces a caller with no validation path. The mitigation is the enforcement-mechanism declaration required in Step 2.1 and the unconditional receipt-side validation in Step 5.1, which runs regardless of what the interface promised.

**Loss of shared state cannot be eliminated, only bounded**: A sub-context is blind to everything the caller learns after dispatch, and shortening deadlines narrows that window without closing it. The mitigation is premise version stamping with supersession detection at admission, which converts an invisible staleness failure into a detected quarantine event, together with the deadline-shortening remedy in Error Type 4.

**Write-scope declaration depends on foreknowledge**: The overlap verdict is only as good as the declared scopes, and a branch that discovers mid-run that it must write a key it did not declare defeats the pre-launch check. The mitigation is to treat an undeclared scope as intersecting, to deny writes outside the declared scope at the enforcement point rather than trusting the declaration, and to route contested field classes to a deterministic reducer so no branch writes them at all.

**Containment evidence is expensive and tends to be skipped**: Adaptive probing multiplies evaluation cost, and deployments under schedule pressure report clean-condition results. The mitigation is Checkpoint 7, which withholds release from any boundary lacking a matched baseline, a decomposed overhead figure, and a passing probe set, and the probe-refresh mechanism that retires probes passing unchanged for 3 cycles.

**Thresholds here are deployment defaults**: The 5 to 1 return ratio, the 30 percent and 15 percent budget shares, the 6 times overhead ceiling, the 8-branch concurrency cap, the 0.50 efficiency floor, the 25 percent packet bound, the depth cap of 2, and the retry ceiling of 2 were chosen to be operable on first deployment. None is derived from a universal property of agent systems. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute them per delegation class against observed outcomes.

**Structural containment is not correct delegation**: A boundary can satisfy every checkpoint here while separating the work along the wrong seam, producing sub-contexts that each succeed and a merged artifact that answers no useful question. The framework detects a malformed boundary, not a misconceived decomposition, and no checkpoint substitutes for review of whether the unit of work was the right unit.

***

## VI. Conclusion and Summary

Context isolation is a contract discipline before it is an architecture. A sub-context that receives a minimal typed brief, holds only granted authority, spends a bounded budget, and returns a schema-conformant artifact keeps its intermediate material out of the caller entirely. A sub-context given a vague objective and no output schema returns prose, and the caller absorbs the very material the boundary was created to exclude, having paid the full multiplier for the privilege. The difference between the two is not the quality of the delegation prompt; it is whether five declarations existed before the sub-context did.

A team introducing isolation should measure a single-context baseline first, then delegate exactly one unit whose return ratio is high and whose write scope is disjoint, then measure overhead against that baseline before adding a second. Parallelism, nesting, and adaptive decomposition come last, since each multiplies the cost of a boundary whose containment is not yet demonstrated.

**Key Success Factors**:

- **Schema before objective**: The output schema is written first, and the objective is derived from what each required field demands, so the return is bounded by structure rather than by discretion.
- **Granted, never inherited**: A sub-context starts with no tools, no credentials, no writes, and no egress, and never widens its own scope; the caller's deterministic tier computes authority from policy alone.
- **One destination for intermediate material**: Every unit is discarded or externalized under a reference, and inline return exists only under an explicit clause naming units and a bound.
- **A computed cost decision**: Return ratio, budget share, and re-establishment cost are numbers checked before dispatch, so cheap work stays inline and expensive work is justified by name.
- **Declared write scopes before launch**: Overlap is computed from the branch manifest and resolved by partitioning or serialization, since two blind branches cannot detect the conflict they create.
- **Declared termination**: Every path returns an envelope with a status from a closed vocabulary, and a partial enumerates what was not done rather than presenting a fragment as a result.

By following this guide, AI agents can move work out of a context without moving its cost back in, and can prove, from measured containment and measured overhead, that each boundary they hold is still worth holding.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them, using the short labels that source carried; they were not independently re-verified during this conversion except where an entry is marked as verified.

**Corpus pointers**:

- `Context Isolate Patterns: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the isolation objectives, costs, and invariants, the isolation dimensions, the task packet and result envelope, the boundary-definition loop, the fan-out and fan-in workflow, the quarantine, capability, and sandbox material, the metric definitions, and the failure-mode inventory.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification this guide was written against.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the category umbrella. Source of the context contract, partition, admission gate, trust class, protected atom, and reason code definitions, and of the isolation trigger thresholds adopted unchanged in Section 1.3.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — the write operation. Owns write eligibility, the write handle, durability receipt, supersession, and idempotency; this guide's disposal rule and envelope references defer to it.
- `advanced_task_guides/context-management/guide_ContextSelection.md` — the select operation. Owns eligibility, ranking, trust-tier admission, and the staged tool loadout; this guide governs whether an admitted set may cross a boundary.
- `advanced_task_guides/context-management/guide_ContextCompression.md` — the compress operation. Governs summarisation fidelity and preservation manifests, which apply to any compression performed at fan-in.
- `advanced_task_guides/context-management/guide_ContextLifecycle.md` — creation, checkpointing, and disposal of context, applicable to sub-context teardown in Step 4.3.
- `advanced_task_guides/context-management/guide_ContextFailurePrevention.md` — the failure-mode treatment this guide's supersession and contamination rules connect to.
- `advanced_task_guides/memory-management/guide_DistributedMemoryArchitecture.md` — the authority on concurrent writes, conflict detection, version comparison, and reconciliation. This guide's obligation ends at write-scope declaration, overlap detection, and serialization; resolution semantics are that guide's.
- `advanced_task_guides/memory-management/guide_TransactiveMemory.md` — the expertise directory and the independence definition adopted in Section 1.3, applicable to selecting which holder receives a delegation.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — source of the window-as-transport and protected-atom definitions inherited through the umbrella guide.
- `advanced_task_guides/planning/guide_TaskManagementOrchestration.md` — task decomposition, scheduling, and dependency ordering upstream of the delegation decision in Phase 1.
- `advanced_task_guides/planning/guide_PlanExecuteDecoupling.md` — planner and executor separation, applicable to the scope ladder rows separating proposal from commit.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — event schema design for the delegation and crossing records in Section III.A.

**External references**:

*Multi-agent isolation, subagent boundaries, and framework mapping*

1. Anthropic engineering — https://www.anthropic.com/engineering/multi-agent-research-system (token multipliers verified during conversion)
2. Claude Code subagent documentation — https://code.claude.com/docs/en/sub-agents
3. LangGraph subgraph documentation — https://docs.langchain.com/oss/python/langgraph/use-subgraphs
4. Structured outputs, Claude Platform Docs — https://platform.claude.com/docs/en/build-with-claude/structured-outputs (retrieved and verified during conversion)

*Untrusted content, injection containment, and flow control*

5. OWASP Agentic AI Threats and Mitigations — https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/
6. Simon Willison — https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
7. NIST CAISI — https://www.nist.gov/news-events/news/2025/01/technical-blog-strengthening-ai-agent-hijacking-evaluations
8. Microsoft Research — https://www.microsoft.com/en-us/research/publication/defending-against-indirect-prompt-injection-attacks-with-spotlighting/
9. "Design Patterns for Securing LLM Agents against Prompt Injections" — https://arxiv.org/html/2506.08837v1
10. CaMeL paper — https://arxiv.org/abs/2503.18813
11. CaMeL implementation — https://github.com/google-research/camel-prompt-injection
12. "Securing AI Agents with Information-Flow Control" — https://arxiv.org/pdf/2505.23643

*Capability scoping, identity, and tool-server isolation*

13. OWASP AI Agent Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
14. MCP Security Best Practices — https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
15. MCP Authorization Specification — https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
16. NSA, "Model Context Protocol Security" — https://www.nsa.gov/Portals/75/documents/Cybersecurity/CSI_MCP_SECURITY.pdf
17. ETDI paper — https://arxiv.org/abs/2506.01333
18. Invariant Labs — https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks

*Execution cells and failure containment*

19. gVisor security model — https://gvisor.dev/docs/architecture_guide/security/
20. Firecracker project — https://github.com/firecracker-microvm/firecracker
21. WASI security — https://wasi.dev/security
22. Microsoft Bulkhead Pattern — https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead
23. Microsoft Circuit Breaker Pattern — https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker

*Principal partitioning, caches, and observability*

24. OWASP Multi-Tenant Security Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Multi_Tenant_Security_Cheat_Sheet.html
25. OWASP Authorization Regression Testing Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Regression_Testing_Cheat_Sheet.html
26. Kubernetes multi-tenancy documentation — https://kubernetes.io/docs/concepts/security/multi-tenancy/
27. Pinecone multi-tenancy guidance — https://www.pinecone.io/learn/series/vector-databases-in-production-for-busy-engineers/vector-database-multi-tenancy/
28. NDSS, "I Know What You Asked" — https://www.ndss-symposium.org/ndss-paper/i-know-what-you-asked-prompt-leakage-via-kv-cache-sharing-in-multi-tenant-llm-serving/
29. "Auditing Prompt Caching in Language Model APIs" — https://arxiv.org/html/2502.07776v1
30. OpenTelemetry log redaction — https://opentelemetry.io/docs/languages/dotnet/logs/redaction/
