# Code as Action

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Code as action constitutes the task family of expressing an agent's intended action as a program that calls tools, rather than as one structured tool call per step. This guide provides AI agents with a structured protocol for deciding when a program is the correct action representation, scoping the callable namespace that defines the program's authority, constructing the program under per-operation idempotency and logging obligations, reviewing it in proportion to its blast radius, executing it under external bounds, and reconciling the partial effects a program that fails midway leaves behind. It specifies a representation gate that rejects the program form wherever a flat call sequence completes the task, a namespace partition in which the set of bound functions is the authority boundary rather than an ergonomic convenience, a construction contract requiring every effectful operation to carry its own idempotency key and its own ledger record, a review tier scaled to the count and reversibility of the effects a program can produce, and a reconciliation procedure that establishes what actually happened before any repair is attempted. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that the compositional gain of a program is not paid for in unattributable failures and duplicated effects.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Action representation**: The form in which an agent expresses one unit of intended action to the infrastructure that will carry it out. Two forms are in scope: a flat call, which names one capability and its arguments, and an action program, which names a sequence of operations with control flow between them. The representation is a design choice made per task, not a property of the agent.

**Action program**: A program the model emits as a single action, which calls bound capabilities, retains intermediate values in its own variables, branches, loops, handles typed errors, and returns one bounded structured result. It is one action to the orchestrator and many operations to the systems it touches. That asymmetry is the source of every benefit and every cost in this guide.

**Flat call sequence**: The baseline representation, in which each capability invocation is emitted separately, inspected separately, authorized separately, and observed separately before the next is proposed. It is the comparison against which every claim made for an action program is measured.

**Binding**: One language-native function inside the program's namespace that maps to exactly one immutable capability version and routes every invocation through the deterministic broker. A binding carries no credential, holds no client, and reaches no service directly.

**Binding namespace**: The complete set of bindings visible to one execution. The namespace is the authority boundary: a program can call anything in it and nothing outside it, so removing a function is a stronger control than instructing the model not to call it.

**Binding manifest**: The signed, frozen record mapping every alias in the namespace to a canonical capability identifier, a version, a schema digest, a side-effect class, and a broker route. It is fixed before execution and cannot be amended by the executing program.

**Call site**: One syntactic location in the program source at which a binding is invoked, identified stably so that a runtime observation can be attributed back to the source that produced it.

**Effect call site**: A call site whose binding carries a side-effect class other than read-only. The count of effect call sites, multiplied by the declared maximum iteration bound of any loop enclosing them, is the quantity the review tier and the approval gate are scaled against.

**Blast radius**: The maximum number and severity of externally visible effects one action can produce if it runs to completion. A flat call has a blast radius of one operation of one declared class. An action program's blast radius is declared before execution and enforced by the effect budget.

**Effect budget**: The declared numeric ceiling on effectful operations one execution may perform, enforced outside the interpreter by the broker, which denies the operation that would exceed it rather than trusting the program to stop.

**Operation ledger**: The append-only per-operation record written by the broker, not by the program, carrying one entry for every attempted operation with its call site, logical call identifier, idempotency key, canonical arguments hash, authorization decision, outcome class, and external operation identifier. It is the artifact that makes a mid-program failure attributable.

**Partial-effect set**: The set of effectful operations a terminated program actually completed, actually failed, or left in an unknown outcome. A program that performs three effectful operations and fails on the third leaves a partial-effect set of two completed, one unknown. Enumerating this set is mandatory before any repair, retry, or replacement program runs.

**Effect reconciliation**: The deterministic procedure that resolves every unknown outcome in the partial-effect set by querying the system of record, keyed by idempotency key or external operation identifier, and rewrites the ledger entry to a terminal outcome class. It is the only path out of an unknown outcome, and it is adopted from `advanced_task_guides/tool-use/guide_ToolUseAndFunctionCalling.md`.

**Side-effect class**: The declared category of consequence a successful invocation produces, drawn from the closed vocabulary defined in `advanced_task_guides/tool-use/guide_ToolUseAndFunctionCalling.md`. It governs whether a capability may be bound into a program namespace at all, and at which review tier.

**Idempotency key**: A caller-generated identifier bound to one logical call and presented on every attempt of that call, under which the executing service deduplicates repeated deliveries. The orchestrator generates it and binds it to the semantic operation, never to a source line or an attempt number, so that a repaired program reusing the same intent reuses the same key.

**Logical call and execution attempt**: One authorized operation, and one delivery of that operation to its service. A program that loops issues one logical call per iteration, and a repair that re-runs the loop must reuse the prior keys for iterations already completed.

**Unknown outcome**: The state in which the program, the runtime, or the broker lost the ability to establish whether an effect occurred. It is a distinct outcome class, never a transient error, and never a candidate for retry before reconciliation.

**Authority scope**: The complete set of capabilities, data classes, destinations, side-effect classes, and budgets an identity may exercise, as defined in `advanced_task_guides/tool-use/guide_AgentControlPlane.md`. A binding namespace is one narrow, task-scoped projection of an authority scope, never its full extent.

**Non-amplification invariant**: An agent never widens its own authority scope. Applied to this representation, the invariant states that an executing program never adds a binding, never loads a capability, and never reaches a service outside its frozen manifest. A namespace change requires terminating the execution and starting a new one.

**Runtime profile**: The named, versioned bundle specifying the language, image digest, isolation tier, writable paths, egress class, and resource limits under which the program runs, as defined in `advanced_task_guides/tool-use/guide_CodeExecution.md`. This guide selects a profile; it does not define one.

**Declared plan**: The structured statement of intended operations, in order, with their capabilities and their effect classes, emitted by the model before or alongside the source, against which the source is checked. A source that references an effect absent from the plan is denied rather than repaired.

**Static effect inventory**: The deterministic extraction from parsed source of every binding referenced, every effect call site, every loop bound enclosing one, every branch that guards one, and the maximum operation count the program can reach. It is derived by the deterministic tier from the syntax tree, not asserted by the model.

**Unrecognised effectful operation**: A referenced binding that does not resolve to an entry in the frozen manifest, or resolves to one whose side-effect class is absent from the declared plan. Its presence rejects the program; it is never run and never silently repaired.

**Plan-to-observation diff**: The comparison of the static effect inventory against the operation ledger after execution, reporting operations predicted but not observed, observed but not predicted, and observed above the predicted count. A non-empty unpredicted set is a control failure, not a modelling imprecision.

**Review tier**: The level of pre-execution scrutiny applied to one program, selected deterministically from its blast-radius class rather than from the model's confidence, and specifying who reads the source, what automated checks must pass, and which approval binding is required.

**Representation warrant**: The recorded determination that this task's structure justifies a program rather than a flat call sequence, carrying the estimated flat-call baseline, the expected gain, the dimension the gain is claimed in, and the review tier the resulting blast radius implies.

**Attribution record**: The terminal artifact naming, for a failed execution, the call site at which the failure occurred, the operations completed before it, the operations left unknown, the reconciliation outcome for each, and the residual state of every external system the program touched.

**Flat-call baseline**: The paired measurement of the same task, the same capabilities, the same model, the same budgets, and the same acceptance tests executed as a flat call sequence. Every efficiency claim in this guide is defined as a difference against it, and no claim is admissible without it.

### 1.2 What the Representation Buys and What It Costs

The program form is not a better way to call tools. It is a different action representation with a specific set of gains and a specific set of losses, and both are structural rather than incidental. An agent that adopts it without pricing the losses converts a turn-count saving into an audit failure.

**Gain one, control flow inside one action**: A loop, a conditional, a retryable read, a pagination walk, or a join executes inside the program rather than across model turns. Where a flat sequence spends one inference turn per operation, the program spends one inference turn for the whole composition. On the multi-tool benchmark most often cited for this representation, one evaluated proprietary model completed 74.4 percent of 82 human-curated instances in 5.5 average turns under the code representation against 52.4 percent in 7.6 turns under structured calls and 53.7 percent in 7.7 turns under text, across 17 evaluated models. That comparison carries a material caveat: the structured and text baselines were restricted to one capability per action, which advantages a representation permitting several, and the best open-source result in the same table fell below 20 percent.

**Gain two, composition without context transit**: Intermediate results stay in program variables instead of passing through the model's context. This is the largest measured effect and the one least dependent on model capability. One provider's reported evaluation of programmatic calling recorded average consumption falling from 43,588 to 27,297 tokens, a 37 percent reduction on complex research tasks, with internal knowledge-retrieval accuracy moving from 25.6 to 28.5 percent and a general agent benchmark from 46.5 to 51.2 percent. These are provider-reported results on that provider's workloads, not an independent or universal figure, and the reduction is realised only where intermediate payloads are large and genuinely reducible.

**Gain three, expressiveness for awkward operations**: Deduplication, aggregation, set difference, stable ordering, unit conversion, and reconciliation across two result sets are natural in a program and unnatural as a chain of flat calls whose intermediate state must be re-serialised into prose at every step. Where the operation is computable rather than judgeable, the program form removes a class of reasoning error rather than merely a class of turn.

**Cost one, the action is no longer individually inspectable**: A reviewer of a flat call reads one capability name and one argument object and decides. A reviewer of a program must read code and infer what it will do under inputs not yet observed. The unit of review has changed from a value to a behaviour, and the checks that suffice for a value do not suffice for a behaviour. A program 200 lines long with 6 effect call sites inside a loop bounded at 50 iterations presents a reviewer with 300 possible effects behind 6 syntactic locations.

**Cost two, failure attribution is harder**: A flat call that fails has one failure, one argument set, and one outcome. A program that fails at its third effectful operation has two completed effects, one uncertain effect, an interpreter traceback that names a source line rather than a business operation, and no default record of which of its operations reached which system. Without per-operation records emitted outside the program, the terminal state of a failed execution is unrecoverable by inspection.

**Cost three, blast radius is larger**: One action can now produce many effects. The consequence of an incorrect action scales with the effect count and with the reversibility of the worst effect in it. This is why the review tier in Phase 4 and the effect budget in Phase 5 are indexed on blast radius rather than applied uniformly, and why the default posture keeps irreversible operations out of programs entirely.

**The governing asymmetry**: The three gains are efficiency gains, measurable against a paired baseline and forfeitable without harm. The three costs are control losses, and a control loss is not offset by an efficiency gain. An agent therefore adopts the program form only where the gains are demonstrated and the losses are separately repaired by the mechanisms in Phases 3 through 5, never where the gains alone are argued.

### 1.3 The Representation Selection Gate

The gate runs before any source is generated, is bounded to 3 percent of the estimated task budget, and returns exactly one of program, flat calls, or clarification. It is deterministic: it consumes the estimated call graph and returns a verdict without model inference on the verdict itself.

**Admission conditions**: Return program only where at least one of the following holds and no exclusion condition applies. The task requires 3 or more related operations with computable data flow between them; a loop over a collection of 5 or more items would otherwise consume one turn per item; a pagination walk of 3 or more pages is bounded and read-only; intermediate payloads exceed 50 KB and reduce to under 10 percent of their size before the model needs them; or 3 or more independent read-only operations can be issued concurrently under a declared fan-out cap.

**Exclusion conditions**: Return flat calls where any of the following holds, regardless of admission signals. One or two operations complete the task; every intermediate result requires open-vocabulary model judgement before the next operation can be chosen; any operation in the composition carries an irreversible, financial, security-changing, or destructive side-effect class; the composition would conceal from the reviewer or the policy gate the exact destination, audience, amount, or data disclosed; capability outputs are unstructured or unstable enough that a program could misparse them without failing; or the deterministic tier cannot supply a scoped namespace, per-operation records, an effect budget, and a reconciliation path. The last is a hard stop: a program without those four controls is not a permitted representation at any blast radius.

**Clarification condition**: Return clarification where the intended target, scope, evidence standard, or acceptance criteria are ambiguous and the ambiguity would change the effect set. A program written against an ambiguous intent multiplies the ambiguity by its effect count.

**Selection Gate Decision Table**:

| Task shape observed | Worst side-effect class in the composition | Deterministic controls present | Gate verdict |
| :-- | :-- | :-- | :-- |
| 1 or 2 operations | Any | Any | Flat calls |
| 3 or more operations, computable data flow | Read-only | All four present | Program |
| Loop over 5 or more items | Read-only | All four present | Program |
| Intermediate payload 50 KB or larger, reducible below 10 percent | Read-only | All four present | Program |
| 3 or more operations | Reversible write | All four present | Program at review tier R1, effect budget declared |
| Any shape | Externally visible write | All four present | Program at review tier R2, named reviewer required |
| Any shape | Irreversible, financial, security, or destructive | Any | Flat calls; program form prohibited by default |
| Any shape | Any | One or more controls absent | Flat calls; record the missing control |
| Every intermediate needs semantic judgement | Any | Any | Flat calls |
| Target, scope, or acceptance criteria ambiguous | Any | Any | Clarification |

**Numeric gate rules**: Where the estimated flat-call baseline is 2 or fewer inference turns, the program form is refused regardless of other signals, because generation, screening, provisioning, and verification overhead exceeds the turns saved. Where the projected gain in the declared dimension is below 20 percent of the flat-call baseline, the program form is refused and the estimate is recorded for the next policy revision. Where a prior paired measurement for the same task class exists, it supersedes the estimate, and a task class whose last 10 paired measurements show under 20 percent gain is removed from program eligibility until re-measured.

### 1.4 Execution Tier Partition and the Authority Boundary

The method divides across three execution tiers, and the division is the principal control in this guide. The model tier writes the program. Everything that determines what the program is permitted to reach, what record it leaves, and what happens when it fails belongs to the deterministic tier. Assigning any deterministic item to the model tier reintroduces exactly the control losses named in Section 1.2.

**The deterministic tier owns five items without exception**: namespace scoping, per-operation logging, idempotency key assignment, effect reconciliation, approval gating, and blast-radius classification. Each is owned because it requires exactness, reproducibility, or auditability that inference cannot supply, and each fails silently when approximated. A namespace scoped by a prompt is not scoped. A log written by the program under audit is not evidence. An idempotency key chosen by the model is not a deduplication guarantee.

**The model tier owns one item**: writing the program, given a frozen namespace, a declared result contract, an effect budget, and a stated prohibition set. The model also proposes the declared plan and proposes repairs, both of which the deterministic tier verifies before either takes effect.

**Two invariants bind the model tier**. First, the model never widens its own namespace. A program that discovers it needs a capability outside its manifest terminates and returns a typed unavailability result; the orchestrator, outside the interpreter, decides whether a new namespace is warranted and starts a new execution if so. No running program loads, imports, or binds a capability, and this constraint holds independently of whether a given platform would technically permit it. One current hosted implementation enforces the same rule at the platform level, requiring deferred capabilities to be loaded before a program starts because a running program cannot invoke capability search. Second, a program containing an unrecognised effectful operation is rejected rather than run. Rejection is terminal for that source: the operation is not stripped, not commented out, and not repaired into an allowed form by the model, because a model that can repair its way past a rejection has, in effect, the authority the rejection was denying.

**Execution Tier Partition by Framework Phase**:

| Phase or artifact | Deterministic tier | Model tier | Authority on disagreement |
| :-- | :-- | :-- | :-- |
| Flat-call baseline estimate | Computes turn, token, and cost estimate from the call graph | Proposes the call graph | Deterministic; an unestimable graph returns clarification |
| Representation verdict | Applies the gate table and numeric rules | None | Deterministic; the verdict is not negotiable |
| Blast-radius classification | Assigns the class from declared side-effect classes | None | Deterministic; the class is read from contracts |
| Namespace composition | Computes the eligible set and freezes the manifest | Names the capabilities the task needs | Deterministic; a requested capability outside authority scope is omitted silently |
| Declared plan | Validates the plan against the manifest | Emits the plan | Deterministic; an unvalidatable plan blocks generation |
| Program source | Screens, parses, and derives the static effect inventory | Writes the source | Deterministic; rejection is terminal for that source |
| Idempotency keys | Generates and binds one key per semantic operation | None | Deterministic; a model-supplied key is discarded |
| Per-operation records | Emits every ledger entry from the broker | None | Deterministic; program-emitted records are evidence of intent only |
| Approval binding | Binds approval to the canonical operation hash | Presents the operation for review | Deterministic; a changed hash invalidates the approval |
| Effect budget enforcement | Denies the operation exceeding the budget | None | Deterministic; enforced outside the interpreter |
| Partial-effect enumeration | Reads the ledger and lists completed, failed, and unknown | None | Deterministic; the ledger is authoritative over the program's own return value |
| Effect reconciliation | Queries the system of record by key or operation identifier | None | Deterministic; an unreconciled unknown blocks repair |
| Failure attribution | Joins ledger entries to call sites | Diagnoses the cause from the attribution record | Hybrid; the model proposes the cause, the deterministic tier verifies the fix against the same inventory |
| Repair source | Re-screens the full source and revalidates every check | Proposes the patched source | Deterministic; a repair that broadens authority is rejected |
| Result verification | Runs independent oracles and the plan-to-observation diff | Interprets residual ambiguity | Hybrid; a failed deterministic check outranks any model assertion of success |
| Baseline measurement | Computes paired metrics over matched cohorts | None | Deterministic; unpaired figures are not reported |

**Handoff discipline**: Every tier boundary in the table is a handoff at which a typed artifact crosses, never a shared mutable state. The model receives a frozen manifest, a plan template, a result contract, and bounded diagnostics. The deterministic tier receives a plan and a source. Nothing else crosses, and in particular no credential, no policy source, no ledger handle, and no approval token is visible inside the runtime.

**What the deterministic tier rejects**: source that fails to parse; source referencing an alias absent from the manifest; source referencing an effect class absent from the declared plan; source containing dynamic evaluation, reflection, raw network access, subprocess creation, package installation, or credential access; source whose static effect inventory exceeds the effect budget; source whose maximum operation count cannot be bounded from the syntax tree; and any repair that adds a binding, raises a loop bound, changes an approved operation hash, or lowers an evidence requirement. Each rejection is recorded with its rule identifier and returned as a typed denial, not as a suggestion.

***

## II. Operational Framework: Reviewable Action Programs Under Scoped Namespaces and Reconciled Effects

The framework assumes the selection gate in Section 1.3 has returned program. It produces four artifacts per execution: a frozen binding manifest, a screened program with a static effect inventory, an operation ledger with one entry per attempted operation, and a terminal attribution record reconciling every effect the program produced. Phases 1 through 4 run once before execution. Phase 5 executes and may return to Phase 3 for a bounded repair. Phase 6 closes the run and feeds the measurement that governs future gate verdicts. The execution environment itself, including sandbox provisioning, isolation, egress denial, resource limits, output truncation, and infrastructure failure classification, is governed by `advanced_task_guides/tool-use/guide_CodeExecution.md` and is selected rather than specified here.

### Phase 1: Representation Selection and Action Contract

**Objective**: Establish that a program is the correct representation for this task, record the baseline it will be measured against, and fix the contract and blast-radius class before any capability is bound.

#### Step 1.1: Estimate the Flat-Call Baseline

**Required Actions**:

- Enumerate the operations the task requires as a flat call sequence, naming each capability, its side-effect class, and its dependence on prior results.
- Estimate inference turns, total tokens, wall-clock latency, and monetary cost for that sequence, using measured per-turn figures for the deployed model rather than nominal figures.
- Estimate the intermediate payload volume the flat sequence would place in model context, and the fraction of it the task's result actually requires.
- Retrieve any prior paired measurement for this task class and prefer it over the estimate where one exists.
- Record the dimension in which a gain is claimed, selecting exactly one of turns, tokens, latency, or cost as primary.

**Required Outputs**:

- A flat-call operation list with a side-effect class per entry.
- A baseline estimate record carrying turns, tokens, latency, cost, and intermediate payload bytes.
- A named primary gain dimension with its projected percentage improvement.

**Quality Checkpoints**:

- Every operation in the list carries a side-effect class drawn from the closed vocabulary; an unclassified capability halts the phase.
- The baseline is an estimate for this model and this catalogue, not a figure carried over from a published benchmark.
- Exactly one primary gain dimension is declared; a claim spanning several dimensions is not measurable against a paired cohort.

***

#### Step 1.2: Apply the Representation Gate

**Required Actions**:

- Evaluate every admission condition and every exclusion condition in Section 1.3 against the operation list, without model inference on the verdict.
- Halt and return flat calls where the worst side-effect class in the composition is irreversible, financial, security-changing, or destructive, unless a recorded exception exists for the exact capability version.
- Halt and return flat calls where any of the four mandatory controls is unavailable: a scoped namespace, per-operation records emitted outside the program, an enforced effect budget, and a reconciliation path to the system of record.
- Confirm the projected gain in the primary dimension reaches 20 percent of the baseline; refuse the program form below that and record the estimate.
- Return clarification rather than a verdict where target, scope, evidence standard, or acceptance criteria are ambiguous.

**Required Outputs**:

- A representation warrant carrying the verdict, the triggering admission condition, the projected gain, and the review tier implied by the blast-radius class.
- A refusal record naming the exclusion condition or missing control, where the verdict is flat calls.

**Quality Checkpoints**:

- The verdict is one of program, flat calls, or clarification; no fourth outcome exists.
- No warrant is issued where any of the four mandatory controls is absent, regardless of projected gain.
- Every refusal names a specific condition or a specific missing control, never a general judgement.

***

#### Step 1.3: Fix the Action Contract and Blast-Radius Class

**Required Actions**:

- State the intended result shape, the acceptance tests, the required evidence references, the prohibited effects, and the maximum authority the execution may exercise.
- Classify blast radius from the declared side-effect classes present in the composition, assigning R0 for read-only, R1 for reversible writes, R2 for externally visible writes, and R3 for irreversible, financial, security-changing, or destructive effects.
- Set the effect budget as an integer ceiling on effectful operations, computed as the planned effect call site count multiplied by the maximum enclosing loop bound, and never left unbounded.
- Set turn, token, latency, cost, operation, page, item, byte, and concurrency budgets, each with a numeric limit enforced outside the interpreter.
- Record the terminal outcome vocabulary the execution may return, comprising verified, partially verified, unverified, rejected, denied, and unknown.

**Required Outputs**:

- An action contract record with result shape, acceptance tests, evidence requirements, prohibited effects, and maximum authority.
- A blast-radius class assignment with the effect budget as an integer.
- A budget ledger naming every bounded dimension and its numeric limit.

**Quality Checkpoints**:

- The blast-radius class is derived from declared side-effect classes on capability contracts, never from a model assessment of risk.
- The effect budget is a finite integer; an unbounded effect count halts the phase before any capability is bound.
- Every budget dimension carries a numeric limit and a named enforcement point outside the runtime.

***

### Phase 2: Namespace Scoping and Binding Manifest Construction

**Objective**: Compose the exact set of callable functions the program may reach, so that the namespace rather than a prompt constitutes the authority boundary, and freeze it before generation.

#### Step 2.1: Compute the Policy-Eligible Capability Set

**Required Actions**:

- Resolve the calling principal, tenant, purpose code, and granted scope set from trusted session state, never from model output.
- Intersect the task's requested capabilities with the principal's authority scope, the current policy bundle, capability lifecycle state, and current health, producing the eligible set.
- Omit silently, without notifying the model, any requested capability the intersection excludes, so that the namespace does not disclose authority the principal lacks.
- Verify that every eligible capability version carries a declared output schema; exclude any whose output is prose only, since a program consuming prose can misparse it without failing.
- Verify each capability's opt-in to programmatic calling where the platform expresses one, and exclude any capability whose contract permits direct invocation only.

**Required Outputs**:

- An eligible capability set with canonical identifiers, versions, schema digests, and side-effect classes.
- An exclusion record naming each omitted capability and the reason, retained outside the model's context.

**Quality Checkpoints**:

- Every entry in the eligible set resolves to one immutable capability version, never to a floating alias.
- No entry lacks a declared output schema; a prose-only capability is excluded rather than wrapped.
- The exclusion record is never returned to the model, since disclosing denied capabilities invites attempts to reach them.

***

#### Step 2.2: Partition Read and Write Namespaces by Execution Stage

**Required Actions**:

- Separate the eligible set into stage namespaces, binding to each stage only what that stage's operations require.
- Bind read-only and effectful capabilities into different namespaces; never expose a write binding to a stage whose work is analysis.
- Cap each namespace at 15 bindings; where the task appears to need more, decompose it into further stages rather than widening one namespace.
- Terminate the runtime and provision a new one when moving between stages, so that a stage's bindings, variables, and handles do not survive into the next.
- Reject any binding whose authority depends on a model-supplied path, method, resource identifier, or destination, since such a binding is a namespace of unbounded size behind one function name.

**Namespace Stage Partition**:

| Stage | Bindings permitted | Side-effect classes permitted | Maximum bindings | Transition rule |
| :-- | :-- | :-- | :-- | :-- |
| Discovery | Catalogue metadata search returning identifiers and descriptions only | Read-only public | 3 | Terminates before any data stage begins |
| Analysis | Data reads, aggregation inputs, reference lookups | Read-only public, read-only private | 15 | Terminates and rebuilds before any effect stage |
| Preview | Dry-run and proposal-generation functions producing an authoritative preview without effect | Read-only private | 8 | Terminates before commit; preview hash carries forward |
| Commit | Exactly the approved effectful operations | Reversible write, externally visible write | 3 | Terminates on completion; no further stage follows |
| Prohibited in any stage | Policy introspection, credential access, raw transport, arbitrary destination fetch, dynamic binding | Any | 0 | Not applicable |

**Required Outputs**:

- A per-stage namespace definition listing bindings, side-effect classes, and binding count.
- A stage transition plan naming the runtime lifecycle action at each boundary.

**Quality Checkpoints**:

- No namespace contains both read-only and effectful bindings except the commit stage, whose read bindings are limited to postcondition checks.
- No namespace exceeds 15 bindings; a task requiring more is decomposed rather than granted a wider surface.
- No binding accepts a destination, path, or method as a model-supplied argument.

***

#### Step 2.3: Freeze and Sign the Binding Manifest

**Required Actions**:

- Emit a manifest mapping every alias in each stage namespace to its canonical capability identifier, version, input and output schema digests, description digest, side-effect class, and broker route.
- Sign the manifest and compute a manifest digest that every subsequent artifact of this execution references.
- Attach the manifest to the runtime through a channel the program cannot write, and expose to the model only the aliases, signatures, and concise descriptions, never the broker route or the manifest itself.
- Run a binding smoke test against simulators or non-sensitive health endpoints, confirming that every alias resolves, every schema validates, and no binding reaches a service without traversing the broker.
- Verify that no alias shadows a language builtin, a runtime-reserved name, another capability's alias, or a prior version of the same capability.

**Required Outputs**:

- A signed binding manifest with a digest, one entry per alias.
- A smoke-test record confirming resolution, schema validity, and broker traversal for 100 percent of aliases.
- A model-facing namespace description carrying aliases, typed signatures, and concise usage notes.

**Quality Checkpoints**:

- The manifest digest is referenced by the declared plan, the static effect inventory, every ledger entry, and the attribution record; an artifact carrying a different digest belongs to a different execution.
- Zero bindings hold a credential, a service client, or a transport handle; a single such binding voids the authority boundary.
- Zero alias collisions exist across the namespace, including against builtins and reserved names.

***

### Phase 3: Program Construction Under Idempotency and Logging Obligations

**Objective**: Produce source in which every effectful operation is individually identified, individually deduplicated, and individually recorded, so that a failure at any point leaves a determinable partial-effect set rather than an opaque one.

#### Step 3.1: Emit the Declared Plan Before the Source

**Required Actions**:

- Require the model to emit a structured plan naming, in order, each intended operation, its alias, its side-effect class, its enclosing loop bound where one exists, and the guard condition under which it executes.
- Validate every plan entry against the frozen manifest, rejecting the plan where an alias is unknown, a side-effect class contradicts the capability contract, or a loop bound is absent or unbounded.
- Compute the plan's maximum operation count as the sum over entries of the entry's enclosing loop bound, and reject the plan where that count exceeds the effect budget set in Step 1.3.
- Return the plan to the reviewer or the approval service at review tiers R2 and R3 before source generation, so that intent is reviewed while it is still cheap to change.
- Record the plan digest, which every later artifact of this execution carries.

**Required Outputs**:

- A validated declared plan with one entry per intended operation and a computed maximum operation count.
- A plan digest bound to the manifest digest.

**Quality Checkpoints**:

- Every plan entry resolves to a manifest alias; an unresolvable entry rejects the plan without generating source.
- The computed maximum operation count is finite and no greater than the effect budget.
- At tiers R2 and R3 the plan has been reviewed before any source exists; source generated ahead of plan review is discarded.

***

#### Step 3.2: Construct the Source Against the Idempotency and Logging Contract

**Required Actions**:

- Instruct the model to write minimal source using only manifest aliases and the declared language subset, with bounded loops, explicit pagination caps, deterministic ordering, typed error handling, and no retry of any effectful operation.
- Require each effectful operation to be issued exactly once per semantic intent in the source, at a distinct call site, so that one call site maps to one logical call and the mapping survives repair.
- Require the program to accept an orchestrator-supplied key set and pass the key belonging to each semantic operation to that operation, never generating, deriving, or reusing a key itself.
- Require the program to make partial failure visible: each effectful operation's outcome is captured, recorded in the returned result, and never swallowed by a broad exception handler or dropped from a concurrent group.
- Require the returned result to carry evidence references, comprising the logical call identifiers, external operation identifiers, item and page counts, and partial-completion markers, rather than a summary that discards them.

**Program Construction Contract**:

```
PROGRAM MUST:
  declare  every effectful call site in the plan, one site per semantic operation
  accept   an orchestrator key set, indexed by semantic operation identifier
  pass     the corresponding key on every effectful invocation
  capture  the typed outcome of every invocation into the result structure
  bound    every loop by a literal or a plan-declared constant
  return   a typed result envelope carrying evidence references

PROGRAM MUST NOT:
  generate  or derive an idempotency key
  retry     an effectful operation after any outcome, including timeout
  catch     an exception broadly enough to hide an operation's outcome
  emit      its own audit record in place of the broker's ledger entry
  import    any module, resolve any destination, or bind any capability
  suppress  cancellation or continue after a budget denial
```

**Required Outputs**:

- Program source referencing only manifest aliases, with one effect call site per semantic operation.
- A key set binding one orchestrator-generated idempotency key to each semantic operation in the plan.
- A result contract stating the structure the program returns, including its evidence reference fields.

**Quality Checkpoints**:

- The count of effect call sites in the source equals the count of effectful entries in the declared plan; any difference rejects the source.
- Zero idempotency keys originate inside the program; a key computed in source is treated as an unrecognised effectful operation.
- Zero effectful operations appear inside a retry construct, since a program-level retry issues a second attempt the broker cannot distinguish from a new intent.

***

#### Step 3.3: Attach Per-Operation Recording Outside the Program

**Required Actions**:

- Configure the broker to emit one ledger entry per attempted operation, before the operation is dispatched and again on its outcome, independently of whether the program returns.
- Bind each entry to the manifest digest, the plan digest, the source digest, the execution identifier, the attempt identifier, and the call site identifier, so that an entry attributes to a syntactic location.
- Record for each entry the logical call identifier, the idempotency key digest, the canonical arguments digest, the authorization decision, the outcome class, the external operation identifier where the service returns one, and the elapsed time.
- Prohibit the program from writing to the ledger, reading it, or observing its contents, so that a program cannot shape the record of its own behaviour.
- Verify before execution that the ledger is durable and that entries persist before a result is returned to the program, so that a crash between effect and return is reconcilable rather than lost.

**Operation Ledger Entry Fields**:

```
LEDGER_ENTRY:
  execution_id:            one logical execution of one source
  attempt_id:              one run of that source
  call_site_id:            syntactic location in the source
  manifest_digest:         frozen namespace this operation came from
  plan_digest:             declared plan this operation was predicted by
  logical_call_id:         one authorized operation, stable across attempts
  idempotency_key_digest:  deduplication identity, orchestrator-generated
  capability_id_version:   exact immutable capability version invoked
  side_effect_class:       declared class from the capability contract
  arguments_digest:        canonical argument hash, never raw arguments
  authorization_decision:  allow, deny, require-approval, allow-with-constraints
  approval_operation_hash: bound approval identity, or absent
  outcome_class:           success, partial, invalid, unauthorized, conflict,
                           rate-limited, unavailable, unknown, permanent-failure
  external_operation_id:   identifier returned by the system of record
  reconciliation_state:    not-required, pending, resolved-effected,
                           resolved-not-effected, unresolvable
  elapsed_ms:              dispatch to outcome duration
```

**Required Outputs**:

- A configured ledger writer emitting entries from the broker with all 16 fields populated.
- A durability confirmation showing that entries persist before results return to the program.
- A ledger access policy denying the program read and write access.

**Quality Checkpoints**:

- Ledger coverage is 100 percent of attempted operations; coverage below 100 percent makes failure attribution impossible and halts the execution before it starts.
- Every entry carries a call site identifier resolving to a location in the screened source.
- Zero ledger entries originate from inside the runtime; entries the program emits are retained as claims of intent and are never treated as evidence of effect.

***

### Phase 4: Pre-Execution Review Proportional to Blast Radius

**Objective**: Recover the inspectability a flat call has by default, by deriving what the program can do from its source and subjecting that derivation to scrutiny scaled to the effects it could produce.

#### Step 4.1: Derive the Static Effect Inventory

**Required Actions**:

- Parse the complete source and reject any source that fails to parse; never execute partially generated or streamed source.
- Extract from the syntax tree every referenced alias, every call site with its identifier, every loop and its bound, every branch guarding a call site, every exception handler and its scope, every concurrency construct and its fan-out cap, and every output operation.
- Compute the maximum reachable operation count per alias as the product of enclosing loop bounds, and the program's total maximum effect count as the sum over effect call sites.
- Flag any call site whose reachable count cannot be bounded from the syntax tree, and reject the source rather than assigning a default bound.
- Screen for the prohibited construct set: dynamic evaluation, reflection, attribute traversal, dynamic import, raw transport, subprocess creation, package installation, credential or environment access, policy introspection, binding mutation, and any handler that catches and suppresses cancellation or a budget denial.

**Required Outputs**:

- A static effect inventory listing aliases, call sites, guards, loop bounds, and maximum reachable operation counts.
- A screening verdict with a rule identifier for each rejection.

**Quality Checkpoints**:

- Every effect call site carries a finite maximum reachable count; one unbounded site rejects the source.
- The inventory is derived from the parsed source by the deterministic tier, never from a model description of the source.
- Zero prohibited constructs are present; presence of any one is a terminal rejection rather than a repair prompt.

***

#### Step 4.2: Reconcile the Inventory Against the Declared Plan

**Required Actions**:

- Compare the inventory's alias set against the plan's alias set, and reject the source where the inventory references an alias the plan did not declare.
- Compare per-alias maximum reachable counts against the plan's declared counts, and reject the source where the inventory exceeds the plan by any amount.
- Reject the source where the inventory's total maximum effect count exceeds the effect budget from Step 1.3, without offering the model an opportunity to justify the excess.
- Treat any referenced alias absent from the manifest, or any effect class absent from the plan, as an unrecognised effectful operation, and reject rather than strip, comment out, or repair it into an allowed form.
- Record the plan-to-inventory difference in full, including aliases declared but not referenced, which indicates the program does not implement its own plan.

**Required Outputs**:

- A plan-to-inventory difference report with three sets: declared and referenced, declared but absent, referenced but undeclared.
- A rejection record where the referenced-but-undeclared set is non-empty.

**Quality Checkpoints**:

- The referenced-but-undeclared set is empty; a single member rejects the source.
- No per-alias reachable count exceeds its declared count.
- A non-empty declared-but-absent set halts for reviewer attention rather than passing silently, since a plan the source does not implement is not a description of the source.

***

#### Step 4.3: Apply the Review Tier and Bind the Approval Gate

**Required Actions**:

- Select the review tier deterministically from the blast-radius class assigned in Step 1.3, never from model confidence, source length, or perceived simplicity.
- Apply the tier's automated checks in full, and halt where any check fails rather than proceeding with a recorded warning.
- Present the reviewer, at tiers requiring one, with the declared plan, the static effect inventory, the exact destinations and material arguments where they are statically determinable, the effect budget, and the source, in that order, so that intent is read before implementation.
- Bind any approval to the canonical operation hash covering the manifest digest, plan digest, source digest, capability versions, and canonical arguments where determinable, and invalidate the approval on any change to that hash.
- Refuse to treat approval of a program as approval of the operations it may generate; where an operation's arguments are computed at run time, the approval binds at the broker on the actual arguments, not in advance on the source.

**Review Tier by Blast-Radius Class**:

| Class | Effects the program can produce | Automated checks required | Human review required | Approval binding |
| :-- | :-- | :-- | :-- | :-- |
| R0 | Read-only only | Parse, screen, inventory, plan diff, budget | None | None |
| R1 | Reversible writes, total maximum effect count 10 or fewer | R0 checks plus per-alias count reconciliation and idempotency key coverage at 100 percent | None; sampled audit of 10 percent of executions | Automatic, bound to plan digest |
| R2 | Externally visible writes, or total maximum effect count 11 to 50 | R1 checks plus destination enumeration and preview generation where the service supports it | Named reviewer reads plan then source; source capped at 200 logical lines and 15 effect call sites | Reviewer approval bound to the operation hash |
| R3 | Irreversible, financial, security-changing, or destructive effects | R2 checks plus dry-run preview with authoritative target enumeration | Two named approvers, neither the requester | Prohibited by default; each exception is per capability version, time-boxed, and separately registered |
| Any class | Total maximum effect count above 50, or source above 200 logical lines | Not applicable | Not applicable | Decompose into stages; a program at this size is not reviewable within any tier's budget |

**Required Outputs**:

- A review record naming the tier, every automated check with its verdict, the reviewer identity where required, and the elapsed review time.
- An approval binding record carrying the operation hash and its component digests, where the tier requires approval.

**Quality Checkpoints**:

- The tier is derived from the blast-radius class; no execution runs at a tier below the one its class implies.
- No source exceeding 200 logical lines or 15 effect call sites proceeds at any tier; it is decomposed into staged executions instead.
- Every approval names an operation hash; an approval granted against a source digest alone is void once any argument is computed at run time.

***

### Phase 5: Bounded Execution and Partial-Effect Reconciliation

**Objective**: Run the program under externally enforced bounds, and on any terminal state other than clean completion, establish what actually happened to every external system before any further action is taken.

#### Step 5.1: Execute Under External Bounds With Per-Operation Mediation

**Required Actions**:

- Provision the runtime profile selected under `advanced_task_guides/tool-use/guide_CodeExecution.md`, attach the frozen manifest through a channel the program cannot write, and confirm that no credential, policy handle, or ledger handle is reachable from inside.
- Enforce every budget from Step 1.3 outside the interpreter, including the effect budget, and deny the operation that would exceed a budget rather than relying on the program to stop.
- Mediate every operation at the broker: revalidate the capability version against the manifest, validate arguments against the schema, evaluate policy against the calling principal, check the approval binding where one is required, reserve quota, present the idempotency key, dispatch, and normalise the outcome into the declared type or a typed error.
- Write the pre-dispatch ledger entry before dispatch and the outcome entry on completion, persisting both before any value returns to the program.
- Return to the program only the bounded typed result or an opaque handle, treating every returned string and field as untrusted data that is never evaluated, never used to select a destination, and never admitted as an instruction.

**Required Outputs**:

- An execution record carrying the terminal state, resource consumption, and budget utilisation per dimension.
- A complete operation ledger with one pre-dispatch and one outcome entry per attempted operation.
- The program's returned result envelope with its evidence references, retained as a claim rather than as evidence.

**Quality Checkpoints**:

- Every operation that reached a service has both a pre-dispatch and an outcome ledger entry; a pre-dispatch entry without an outcome entry is an unknown outcome by definition, never an absence of effect.
- Zero operations bypassed the broker; a service-side record with no corresponding ledger entry is a control failure and triggers security escalation.
- The effect budget was enforced by denial at the broker, not by the program's own arithmetic.

***

#### Step 5.2: Classify the Terminal State and Enumerate the Partial-Effect Set

**Required Actions**:

- Classify the terminal state from the ledger and the runtime, not from the program's return value, since a program can return a success envelope after an operation it did not observe.
- Enumerate the partial-effect set by reading the ledger: every effectful operation with a success outcome is completed, every one with a definite failure outcome is not effected, and every one with a pre-dispatch entry lacking a terminal outcome is unknown.
- Compare the partial-effect set against the static effect inventory, producing the plan-to-observation diff with three sets: predicted and observed, predicted and not observed, and observed but not predicted.
- Treat a non-empty observed-but-not-predicted set as a control failure, halt the run, and escalate under the security path rather than repairing the program.
- Record for every unknown operation its idempotency key digest, its external operation identifier where one was returned before the loss of contact, its canonical arguments digest, and its call site.

**Terminal State Classification and Required Next Action**:

| Terminal state | Partial-effect set condition | Required next action | Repair permitted |
| :-- | :-- | :-- | :-- |
| Clean completion | All operations terminal, none unknown | Proceed to verification | Not applicable |
| Program error before any effect | Empty | Repair within the attempt bound | Yes |
| Program error after one or more effects | Completed set non-empty, unknown set empty | Reconcile completed set, then repair with the same key set | Yes, keys reused |
| Timeout or cancellation | One or more unknown | Reconcile every unknown before any other action | Only after reconciliation resolves every unknown |
| Budget or effect-budget denial | Completed set non-empty by construction | Reconcile, then return a declared partial result | No; a denial is not a specification to route around |
| Policy denial at the broker | Denied operation not effected | Return typed denial to the orchestrator | No; the model never repairs past a denial |
| Observed operation absent from the inventory | Any | Halt and escalate under the security path | No |
| Infrastructure fault | One or more unknown | Reconcile every unknown, then re-provision | Yes, after reconciliation |

**Required Outputs**:

- A terminal state classification drawn from the closed vocabulary above.
- A partial-effect set listing completed, not-effected, and unknown operations with their keys and call sites.
- A plan-to-observation diff with its three sets populated.

**Quality Checkpoints**:

- The classification derives from the ledger; a program-reported success contradicted by the ledger is classified from the ledger and the contradiction is recorded.
- The unknown set is enumerated explicitly, including when it is empty, so that an absent enumeration is distinguishable from an empty one.
- The observed-but-not-predicted set is empty; a non-empty set halts the run regardless of whether the unpredicted operations succeeded.

***

#### Step 5.3: Reconcile Every Unknown Effect Before Any Further Action

**Required Actions**:

- Query the system of record for every unknown operation, keyed by idempotency key or external operation identifier, and never by re-issuing the operation to observe what happens.
- Rewrite each unknown ledger entry to a terminal reconciliation state: resolved-effected, resolved-not-effected, or unresolvable, and never leave an entry pending at run close.
- Retry reconciliation queries under a bounded schedule of at most 5 attempts across at most 10 minutes for an interactive task, and escalate to a named human role on the sixth attempt or at the deadline, whichever is reached first.
- Block every downstream action while any unknown remains: no repair, no replacement program, no fallback to flat calls, and no result return, since each of those risks a duplicate effect against an operation that already succeeded.
- Where reconciliation resolves an operation as effected, mark its semantic intent complete and exclude it from any subsequent program, reusing its idempotency key only if the identical intent must be re-presented.
- Where reconciliation returns unresolvable, escalate to a named human role with the full attribution record, and never resolve the ambiguity by re-attempting the operation.

**Reconciliation Procedure**:

```
FOR each operation in partial_effect_set WITH outcome_class == unknown:
  1. SELECT the reconciliation oracle for its capability:
       preferred:  system-of-record query by external_operation_id
       fallback:   system-of-record query by idempotency_key_digest
       last:       postcondition query on the target resource state
  2. IF no oracle exists for the capability
       THEN mark unresolvable AND escalate
       AND  record that this capability must not be bound into a program
            namespace again until an oracle exists
  3. EXECUTE the oracle query, bounded at 5 attempts over 10 minutes
  4. WRITE the resolved state to the ledger entry
  5. IF resolved-effected
       THEN mark the semantic operation complete
       AND  exclude it from every subsequent attempt of this task
  6. IF resolved-not-effected
       THEN return the operation to the unresolved work set
  7. IF unresolvable after the bound
       THEN escalate with the attribution record AND stop the task

GATE: no repair, replacement, fallback, or result return proceeds
      while any entry remains pending
```

**Required Outputs**:

- A reconciliation record with a terminal state for every unknown operation.
- An updated ledger in which zero entries remain in the pending reconciliation state.
- An attribution record naming the failing call site, the completed set, the reconciled set, and the residual external state.

**Quality Checkpoints**:

- Zero operations were re-issued to determine whether they had taken effect; re-issuing is the failure this procedure exists to prevent.
- Zero ledger entries remain pending at run close; a pending entry is an unreconciled effect and blocks the run from closing.
- Every capability bound into an effectful namespace has a named reconciliation oracle; one without an oracle is removed from program eligibility rather than executed and hoped for.

***

### Phase 6: Attribution, Verification, and Baseline Measurement

**Objective**: Attribute every failure to a call site, verify the result against evidence the program did not produce, and establish whether the representation earned its cost against the paired flat-call baseline.

#### Step 6.1: Attribute the Failure to a Call Site and Bound the Repair

**Required Actions**:

- Join the failing ledger entry to its call site identifier, and report the failure as a named operation at a named source location rather than as a runtime traceback line.
- Classify the failure into one of the representation-level classes: undeclared operation, budget denial, policy denial, schema mismatch on a bound result, unbounded reachable count, misparsed structured result, or unreconciled effect. Infrastructure and runtime failure classes are assigned under `advanced_task_guides/tool-use/guide_CodeExecution.md`.
- Return to the model only the bounded diagnostic set: the failing call site, the typed error class, a bounded message with untrusted content sanitised, the relevant schema, the remaining budgets, the completed operation set as immutable handles, and the reused key set.
- Permit a repair only where the failure class is repairable and the repair changes source without changing intent, authority, side-effect class, effect budget, or evidence requirements.
- Re-run the complete Phase 4 sequence on every repaired source, including parse, screen, inventory, plan diff, budget check, and approval revalidation, and invalidate any approval whose operation hash changed.

**Required Outputs**:

- An attribution record naming the failing call site, its capability version, its failure class, and its position in the partial-effect set.
- A bounded diagnostic package containing no credential, no policy source, no full traceback, and no unsanitised third-party content.
- A repair verdict permitting or refusing a further attempt, with the attempt count remaining.

**Quality Checkpoints**:

- Every failure resolves to exactly one call site; a failure that cannot be attributed to a call site indicates incomplete ledger coverage and escalates rather than repairing.
- No repair proceeds while any reconciliation entry is pending.
- Repair attempts are bounded at the initial execution plus 2 repairs for an interactive task, and at 5 total attempts for a durable read-only analytical task with explicit acceptance tests, after which the run terminates or falls back.

***

#### Step 6.2: Verify the Result Against Evidence the Program Did Not Produce

**Required Actions**:

- Validate the returned envelope against the declared result contract, and treat a valid envelope as a necessary condition rather than as evidence of correctness.
- Run the plan-to-observation diff as an acceptance check, requiring the observed-but-not-predicted set to be empty and the observed operation counts to fall within the predicted bounds.
- Verify every evidence reference in the returned envelope against the ledger, confirming that each named logical call identifier, external operation identifier, item count, and page count corresponds to a recorded entry.
- Recompute the result's key aggregates with an independent oracle as defined in `advanced_task_guides/tool-use/guide_CodeExecution.md`, and for every effectful operation query the authoritative postcondition by external operation identifier.
- Assign a terminal verification status from the closed vocabulary of verified, partially verified, unverified, rejected, denied, and unknown, naming every failed check.

**Required Outputs**:

- A verification record with one verdict per acceptance check and a terminal status.
- An evidence coverage figure stating the fraction of required evidence references that resolved against the ledger.
- A postcondition confirmation for every operation the run reports as completed.

**Quality Checkpoints**:

- Evidence coverage is 100 percent; a reference that does not resolve against the ledger rejects the result, because a fabricated evidence reference is indistinguishable from a fabricated result.
- No result reaches verified status on runtime success and schema validity alone; a well-formed wrong answer passes both.
- Every completed effectful operation carries an authoritative postcondition confirmation, not a program assertion that the operation succeeded.

***

#### Step 6.3: Measure Against the Paired Flat-Call Baseline

**Required Actions**:

- Execute the paired flat-call arm on the same task, capabilities, model, budgets, acceptance tests, and evidence requirements, and compare only matched successful tasks.
- Compute the primary gain dimension as a difference against the baseline, reporting negative values rather than suppressing them, and report verified completion rate for both arms alongside it.
- Compute the representation-specific control metrics: unpredicted operation rate, effect duplication rate, unknown-effect rate after reconciliation, ledger coverage, attribution rate, and false-success rate.
- Refuse to report an efficiency gain unless verified completion in the program arm is non-inferior to the baseline within 2 percentage points and evidence coverage is equal in both arms.
- Feed the measured gain back into the selection gate, and remove a task class from program eligibility where its last 10 paired measurements show under 20 percent gain in the declared dimension.

**Required Outputs**:

- A paired measurement record with both arms' verified completion, primary dimension figures, and evidence coverage.
- A control metric set with the six representation-specific metrics and their targets.
- A gate policy update recording the measured gain for this task class.

**Quality Checkpoints**:

- Every reported gain is paired; an unpaired figure is not reported at any confidence.
- No efficiency gain is reported where verified completion regressed by more than 2 percentage points or evidence coverage differs between arms, since fewer tokens carrying less evidence is a loss stated as a gain.
- Effect duplication rate and unknown-effect rate after reconciliation are both zero; a non-zero value in either blocks the configuration from promotion.

***

## III. Implementation Guidance for AI Agents

AI agents using code as an action representation must follow systematic protocols ensuring that the authority a program exercises is bounded by its namespace, that every effect it produces is individually recorded and individually deduplicated, and that a mid-program failure resolves to a determinate external state before any further action. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Gate Agent**: Estimates the flat-call baseline, applies the selection gate, and issues or refuses the representation warrant. It may refuse the program form and its refusal is not appealable by the model.
2. **Namespace Composer**: Computes the eligible capability set from the calling principal's authority scope, partitions it into stage namespaces, and signs the binding manifest. It alone determines what is callable, and it never discloses exclusions to the model.
3. **Program Author**: The model tier. Emits the declared plan and then the source, against a frozen manifest and a stated prohibition set. It writes nothing else and decides nothing else.
4. **Screening Agent**: Parses source, derives the static effect inventory, runs the plan diff, and issues a terminal accept or reject. A rejection is never returned to the Program Author as a repair prompt where the cause is an unrecognised effectful operation.
5. **Mediation Broker**: Receives every operation from the runtime, revalidates version, schema, policy, approval, and quota, presents the idempotency key, dispatches, normalises the outcome, and writes both ledger entries. It is the only path from the program to any external system.
6. **Reconciliation Agent**: Enumerates the partial-effect set, resolves every unknown against the system of record, and holds the gate that blocks repair, fallback, and result return while any entry is pending.
7. **Measurement Agent**: Runs the paired flat-call arm, computes the control metric set, and updates the gate policy for the task class.

**Authority Invariants**: Three statements hold for every execution and admit no exception. The Program Author never widens its own namespace, and a program needing a capability outside its manifest terminates and returns a typed unavailability result so that the orchestrator, outside the interpreter, may compose a new namespace and start a new execution. A program containing an unrecognised effectful operation is rejected rather than run, and the rejection is terminal for that source rather than a prompt to produce an allowed variant. The Mediation Broker's ledger, not the program's return value, is the authoritative record of what occurred.

**Workflow Execution Pattern**:

```
STATE: Pre_Execution_Review
INPUTS:
  1. Signed binding manifest with digest, from Phase 2
  2. Validated declared plan with digest, from Step 3.1
  3. Program source and orchestrator key set, from Step 3.2
  4. Blast-radius class and effect budget, from Step 1.3
ACTIONS:
  1. Parse source; reject on any parse failure
  2. Derive static effect inventory with per-site reachable counts
  3. Compute plan-to-inventory difference across three sets
  4. Select review tier from blast-radius class
  5. Bind approval to the canonical operation hash where the tier requires it
VALIDATION:
  - referenced_but_undeclared_aliases == 0
  - unbounded_effect_call_sites == 0
  - prohibited_constructs_present == FALSE
  - total_max_effect_count <= effect_budget
  - idempotency_key_coverage == 1.0 OVER effectful_call_sites
  - ledger_coverage_configured == 1.0
  - logical_source_lines <= 200 AND effect_call_sites <= 15
  - reviewer_approval_present == TRUE IF tier IN {R2, R3}
TRANSITIONS:
  IF all_validations_pass THEN next_state = Bounded_Execution
  IF referenced_but_undeclared_aliases > 0
     THEN next_state = Terminal_Rejection
  IF total_max_effect_count > effect_budget
     THEN next_state = Decompose_Into_Stages
  IF validation_failed FOR any other check
     THEN next_state = Bounded_Repair
```

**Two-Phase Action Pattern**: Emit the declared plan and have it validated against the manifest and the effect budget while no source exists; emit source and have it screened against that plan while no runtime is provisioned; provision and execute only after both pass. The cost of a defect rises by roughly an order of magnitude at each boundary, and the second boundary is the last at which a defect costs nothing external.

**Approval Gate**: Human authorisation is required before executing any program at blast-radius class R2 or R3; before any execution whose total maximum effect count exceeds 10; before any repair whose canonical operation hash differs from the approved hash; before any exception permitting an R3 capability into a program namespace, which requires two named approvers neither of whom is the requester; and before any reconciliation entry is closed as unresolvable. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the manifest, plan, key set, ledger, and budget ledger in durable state outside the model's context, since a repair may occur after a context boundary and the key set must survive it.
- Return to the model only aliases, signatures, concise descriptions, bounded diagnostics, and immutable handles; never the manifest, the ledger, the exclusion record, or the broker route.
- Write a handoff record at every context boundary naming the manifest digest, the plan digest, the completed operation set, the pending reconciliation set, and the remaining attempt count.
- Count generation, screening, provisioning, mediation, reconciliation, and verification cost toward the representation's overhead rather than treating any of it as free when computing the gain against the baseline.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Representation Warrant (After Phase 1)**

- **Automated Check**: The verdict is one of three values; all four mandatory controls are present; the projected gain reaches 20 percent of the baseline; the effect budget is a finite integer; every budget dimension carries a numeric limit.
- **Agent Action on Pass**: Proceed to namespace composition.
- **Agent Action on Failure**: Return flat calls and record the missing control or the failing threshold; no source is generated.
- **Human Review Trigger**: The worst side-effect class in the composition is irreversible, financial, security-changing, or destructive.

**Checkpoint 2: Namespace Integrity (After Phase 2)**

- **Automated Check**: Every alias resolves to one immutable capability version with a declared output schema; no namespace exceeds 15 bindings; read and effectful bindings are separated except in the commit stage; zero bindings hold a credential or transport handle; zero alias collisions exist.
- **Agent Action on Pass**: Freeze the manifest and proceed to plan emission.
- **Agent Action on Failure**: Halt; a defective namespace is the authority boundary failing, and no source is generated against it.
- **Human Review Trigger**: A task appearing to require more than 15 bindings in one stage, or any request to bind a capability whose destination is a model-supplied argument.

**Checkpoint 3: Plan and Source Conformance (After Phases 3 and 4)**

- **Automated Check**: Referenced-but-undeclared alias set is empty; every effect call site has a finite reachable count; total maximum effect count is within the effect budget; idempotency key coverage is 100 percent of effectful call sites; ledger coverage is configured at 100 percent; source is within 200 logical lines and 15 effect call sites; approval is bound where the tier requires it.
- **Agent Action on Pass**: Provision the runtime and execute.
- **Agent Action on Failure**: Reject the source terminally where an undeclared alias or a prohibited construct is present; otherwise return a bounded diagnostic and permit one repair within the attempt bound.
- **Human Review Trigger**: Any rejection for an undeclared effectful alias, and any second rejection of the same source digest lineage.

**Checkpoint 4: Effect Determinacy (After Phase 5)**

- **Automated Check**: Every pre-dispatch ledger entry has a terminal outcome or a resolved reconciliation state; zero entries remain pending; the observed-but-not-predicted set is empty; effect duplication count is zero.
- **Agent Action on Pass**: Proceed to verification.
- **Agent Action on Failure**: Block every downstream action, run the reconciliation procedure, and re-evaluate; where reconciliation returns unresolvable, escalate with the attribution record.
- **Human Review Trigger**: Any unresolvable reconciliation, any observed operation absent from the inventory, and any effect duplication.

**Checkpoint 5: Result Verification (After Step 6.2)**

- **Automated Check**: Evidence coverage is 100 percent against the ledger; every completed effectful operation carries an authoritative postcondition confirmation; independent oracles pass; the terminal status is drawn from the closed vocabulary.
- **Agent Action on Pass**: Release the result envelope with its status.
- **Agent Action on Failure**: Downgrade the status to partially verified, unverified, or rejected, and name every failed check rather than returning a qualified success.
- **Human Review Trigger**: An evidence reference that does not resolve against the ledger, which is treated as a fabrication signal rather than a formatting defect.

**Checkpoint 6: Baseline Justification (After Step 6.3)**

- **Automated Check**: Both arms ran on matched tasks; verified completion in the program arm is within 2 percentage points of the baseline; evidence coverage is equal in both arms; the six control metrics are computed; effect duplication rate and post-reconciliation unknown-effect rate are zero.
- **Agent Action on Pass**: Retain the task class in program eligibility and record the measured gain.
- **Agent Action on Failure**: Remove the task class from program eligibility until re-measured, and revert its tasks to flat calls.
- **Human Review Trigger**: A reported gain accompanied by a verified-completion regression, or any non-zero effect duplication rate.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
MANIFEST_DIGEST:
PLAN_DIGEST:
SOURCE_DIGEST:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Undeclared Effectful Operation in Generated Source**

- **Symptoms**: The static effect inventory references an alias absent from the declared plan, an alias absent from the manifest, or an effect class the plan did not carry; the referenced-but-undeclared set is non-empty.
- **Diagnostic Steps**: Confirm the alias against the manifest and the plan; determine whether the source names a capability the namespace never contained, which indicates the model is writing against a remembered catalogue rather than the supplied one, or names a manifest capability the plan omitted, which indicates a plan that does not describe the source.
- **Resolution Protocol**: Option A, reject the source terminally and require a new plan and a new source, since the defect is in the declaration rather than the syntax. Option B, where the alias is absent from the manifest entirely, return a typed unavailability result and let the orchestrator decide outside the interpreter whether a wider namespace is warranted. Option C, where the pattern recurs across sources, narrow the model-facing namespace description and restate the prohibition set, since an ambiguous description invites invention.
- **Escalation Trigger**: Two occurrences within one task escalate to a named human role. An occurrence naming a capability at side-effect class R3 escalates immediately and disables the task class pending review.

**Error Type 2: Unknown Effects After a Mid-Program Failure**

- **Symptoms**: One or more ledger entries carry a pre-dispatch record with no terminal outcome; the terminal state is timeout, cancellation, or infrastructure fault; the program's return value asserts a state the ledger does not support.
- **Diagnostic Steps**: Enumerate the partial-effect set from the ledger rather than from the return value; for each unknown, retrieve the idempotency key digest, the external operation identifier if one was returned, and the call site; confirm that a reconciliation oracle exists for each affected capability.
- **Resolution Protocol**: Option A, run the reconciliation procedure in Step 5.3 and resolve each unknown against the system of record. Option B, where an oracle is missing, escalate, and remove that capability from program eligibility until an oracle exists, since an unreconcilable effect cannot be safely composed. Option C, where reconciliation resolves everything as not effected, return the full operation set to the unresolved work and permit a bounded repair reusing the same key set.
- **Escalation Trigger**: Any unresolvable entry after 5 reconciliation attempts across 10 minutes escalates to a named human role with the attribution record and stops the task. Reconciliation is never abandoned in favour of a retry.

**Error Type 3: Effect Duplication Across Attempts**

- **Symptoms**: A system of record shows two effects for one semantic operation; two ledger entries carry different idempotency key digests for the same canonical arguments; a repaired program re-executed an operation the prior attempt completed.
- **Diagnostic Steps**: Compare key digests across attempts for the same semantic operation identifier; confirm whether the key set was regenerated at repair, whether the program derived a key itself, or whether a completed operation was not excluded from the replacement source.
- **Resolution Protocol**: Option A, apply the compensating operation where the capability declares one, and record it as a distinct ledger entry rather than as a correction of the original. Option B, where no compensation exists, escalate with the attribution record and treat the duplication as an incident rather than a defect. Option C, correct the orchestrator so that the key set is generated once per task and reused across every attempt, and add a regression case asserting key stability across repairs.
- **Escalation Trigger**: Any duplication at all escalates. The release target for effect duplication rate is zero, and a single occurrence blocks promotion of the configuration.

**Error Type 4: Wrong-But-Runs Result**

- **Symptoms**: The runtime exits cleanly, the envelope validates against the result contract, and independent verification fails; a field, unit, join, filter, snapshot, pagination termination, or exception default was wrong without producing an error.
- **Diagnostic Steps**: Run the plan-to-observation diff and check whether operation counts fell below their predicted range, which indicates an early loop exit; verify each evidence reference against the ledger; recompute the aggregate with the independent oracle and locate the first divergent intermediate.
- **Resolution Protocol**: Option A, tighten the result contract so the wrong shape fails validation rather than passing, and add the case as a regression assertion. Option B, where the capability's output is unstable enough that a program can misparse it silently, remove that capability from program eligibility and return the task to flat calls, where a model inspects each result. Option C, where the divergence is in aggregation rather than parsing, require the aggregate to be recomputed outside the program by the deterministic tier.
- **Escalation Trigger**: A false-success rate above 2 percent for a task class blocks that class from program eligibility until the contract is tightened and re-measured.

**Error Type 5: Namespace Widening Attempt**

- **Symptoms**: Source contains a dynamic import, a reflective lookup, an attribute traversal toward a transport client, a destination assembled from a computed string, or a call to a capability-search function from inside the runtime; a service-side record exists with no corresponding ledger entry.
- **Diagnostic Steps**: Identify the construct and the call site; determine whether it reached an external system by comparing service-side records against the ledger; establish whether the namespace description disclosed capabilities the manifest did not contain.
- **Resolution Protocol**: Option A, stop the execution and every child operation, revoke the runtime's capability token, and route to the security escalation path rather than returning the finding to the model for repair. Option B, where the attempt did not reach a service, record the rejection, reject the source terminally, and add the construct to the screening rule set with its own rule identifier. Option C, where a service-side record has no ledger entry, treat the mediation boundary as breached, disable the affected namespace, and preserve forensic evidence.
- **Escalation Trigger**: Any service-side effect with no ledger entry escalates immediately as a control failure. No repair loop is entered on a security signal at any attempt count.

**Error Type 6: Representation Oscillation**

- **Symptoms**: The task alternates between the program form and flat calls; a fallback to flat calls is followed by a return to a program; repair attempts produce a repeated normalised state hash without improving any named check.
- **Diagnostic Steps**: Hash normalised source, manifest digest, failure class, and acceptance results per attempt and compare across attempts; count mode switches per task; confirm whether completed idempotent operations were preserved across the switch.
- **Resolution Protocol**: Option A, permit exactly one mode switch per task and terminate on a second, since oscillation consumes budget without changing the failure. Option B, on a repeated state hash, stop the repair loop immediately rather than exhausting the attempt bound. Option C, where a task class oscillates across runs, remove it from program eligibility and record the pattern for the gate policy.
- **Escalation Trigger**: A second mode switch within one task, or two consecutive repairs that do not improve a named check, terminates the task and returns a declared partial result.

**Troubleshooting Decision Tree**:

```
ACTION PROGRAM FAILS
├─ SECURITY SIGNAL
│   ├─ Service effect with no ledger entry → HALT, revoke, forensic escalation
│   ├─ Dynamic import, reflection, or raw transport → Terminal reject, add rule
│   └─ Capability search from inside runtime → Terminate execution, no repair
├─ DECLARATION DEFECT
│   ├─ Alias referenced but not declared → Terminal reject, new plan required
│   ├─ Alias absent from manifest → Typed unavailability, orchestrator decides
│   └─ Reachable count above effect budget → Decompose into staged executions
├─ EFFECT DETERMINACY DEFECT
│   ├─ Pending reconciliation entry → Run reconciliation, block all downstream
│   ├─ No oracle for the capability → Escalate, remove from program eligibility
│   ├─ Unresolvable after 5 attempts → Escalate with attribution record, stop
│   └─ Duplicate effect observed → Compensate or escalate; promotion blocked
├─ CORRECTNESS DEFECT
│   ├─ Envelope invalid → Bounded repair within attempt limit
│   ├─ Evidence reference unresolved → Reject result, treat as fabrication
│   └─ Oracle disagrees with result → Tighten contract or revert to flat calls
└─ PROGRESS DEFECT
    ├─ Repeated normalised state hash → Stop repair loop immediately
    ├─ Attempt bound reached → One mode switch to flat calls, keys preserved
    └─ Second mode switch → Terminate, return declared partial result
```

### D. Performance Metrics and Continuous Learning

**Representation Control Metrics**: These measure whether the costs named in Section 1.2 are actually repaired, and they take precedence over every efficiency figure.

- **Ledger coverage**: Attempted operations carrying both a pre-dispatch and an outcome entry, over attempted operations (target: 100 percent; below 100 percent, failure attribution is impossible and the configuration is not deployable).
- **Attribution rate**: Failed executions whose failure resolves to exactly one call site, over failed executions (target: at least 98 percent; below 95 percent indicates ledger or call-site instrumentation gaps).
- **Unpredicted operation rate**: Observed operations absent from the static effect inventory, over observed operations (target: 0; any non-zero value is a control failure, not a modelling imprecision).
- **Effect duplication rate**: Semantic operations producing more than one authoritative effect, over semantic effectful operations executed (target: 0; a single occurrence blocks promotion).
- **Post-reconciliation unknown-effect rate**: Effectful operations still unresolved at run close, over effectful operations executed (target: 0).
- **Unresolvable reconciliation rate**: Unknown operations returning unresolvable, over unknown operations (target: no more than 1 percent; above 5 percent indicates missing oracles rather than transient loss).

**Review and Authority Metrics**:

- **Tier conformance**: Executions run at the tier their blast-radius class implies, over executions (target: 100 percent).
- **Namespace width**: Mean bindings per stage namespace (target: no more than 8; above 15 is prohibited by Step 2.2).
- **Widening attempt rate**: Sources rejected for a namespace-widening construct, over sources screened (target: below 1 percent; a rising rate indicates the model-facing namespace description is misleading).
- **Approval mutation rate**: Approved operation hashes invalidated by a later change, over approvals granted (target: no more than 10 percent; above 25 percent indicates approval is being sought before the plan is stable).
- **Review time per R2 execution**: Median reviewer minutes (target: no more than 15; above 15 indicates the source exceeds what the tier can actually inspect and must be decomposed).

**Efficiency Metrics, Reported Only in Paired Form**:

- **Primary dimension gain**: The declared dimension's difference against the paired flat-call arm over matched successful tasks (target: at least 20 percent; negative values are reported rather than clipped).
- **Verified completion delta**: Program-arm verified completion minus baseline verified completion (target: no worse than minus 2 percentage points; a larger regression voids any efficiency claim).
- **Intermediate context reduction**: Bytes of operation results not placed in model context, over bytes eligible to be (reported alongside evidence coverage, never alone).
- **False-success rate**: Executions with clean runtime status failing mandatory verification, over executions with clean runtime status (target: no more than 2 percent).
- **Repair convergence rate**: Repair loops reaching verified success within the attempt bound, over repair loops entered (target: at least 60 percent; below 40 percent indicates the representation is wrong for the task class).
- **Fallback rate and recovery**: Tasks switching once to flat calls, over tasks selecting the program form, and the fraction of those reaching verified success (target: fallback below 20 percent, recovery above 80 percent).

**Learning and Adaptation Mechanisms**:

- **Gate policy from measurement**: Update program eligibility per task class from the last 10 paired measurements, removing classes below 20 percent gain and re-admitting only after re-measurement.
- **Namespace narrowing from observation**: Where a binding is present in a manifest but referenced by under 5 percent of that class's programs, remove it from the namespace, since unused authority is cost without benefit.
- **Screening rule accretion**: Add a screening rule with its own identifier for every novel widening construct observed, and add a regression case to the private evaluation set.
- **Oracle coverage as a precondition**: Treat the absence of a reconciliation oracle as a blocking gap rather than an accepted risk, and track oracle coverage across effectful capabilities as a release metric.
- **Threshold recalibration**: Recompute every numeric bound here per deployment and per task class; the values stated are deployment defaults chosen to be operable on first use, not measured constants.

**Human-in-the-Loop Boundaries**: Widening a namespace, granting an exception permitting an R3 capability into a program namespace, closing a reconciliation entry as unresolvable, promoting a configuration with a non-zero effect duplication rate, and overriding a terminal rejection for an undeclared effectful operation are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how an action is represented and bounded rather than what the action does. Its phases hold wherever a task can be expressed either as a sequence of individually inspectable calls or as one program, and wherever some of those calls change external state.

### 4.1 Cross-Domain Application Patterns

**Financial operations**: The selection gate admits the analysis stage and refuses the settlement stage. Reconciling 4,000 transactions against a ledger extract is a read-only composition with large reducible intermediates, and the program form saves both turns and context. Issuing the resulting payments is not: each carries an irreversible side-effect class, so the commit stage returns to flat calls with per-payment approval. Where a reviewed exception permits a program to issue reversible holds, the effect budget is set to the exact expected count rather than to a headroom figure, and the reconciliation oracle is the payment processor's operation-identifier lookup rather than a balance query, since a balance cannot distinguish two effects from one.

**Clinical and health records**: Assembling a cohort across several record systems, deduplicating patients, and computing an aggregate is a read-only composition whose intermediates must not enter model context at all, which makes context reduction a privacy control rather than an efficiency one. Any operation writing to a record is externally visible at minimum and is kept direct. The namespace partition matters more here than elsewhere: a program that can read identifiers and also send messages is an exfiltration surface regardless of what its source says, so those bindings never share a stage.

**Industrial and logistics operations**: Effects vary in reversibility inside one task, since a provisional allocation is reversible while a dispatched shipment is not. Blast-radius class is therefore assigned per stage rather than per task, and the commit stage is decomposed so that no single program spans classes. The reconciliation oracle is usually a device or carrier status query with a real latency floor, so the reconciliation bound is set in the domain's terms rather than at the 10-minute default, and the default is recorded as overridden.

**Scientific and analytical research**: This is the strongest case for the representation. Compositions are read-only, intermediates are large and reducible, control flow is genuinely required, and the acceptance test is a recomputation rather than a judgement. Blast-radius class is R0 throughout, review is automated, and the effect budget is zero, which removes the entire partial-effect apparatus from the run. Where a task class is durably read-only, the attempt bound extends to 5 rather than 3, because a failed attempt costs computation and nothing external.

**Software engineering over a repository**: The composition spans reads, transformations, and writes to a working copy, where writes are reversible under version control and the reconciliation oracle is the repository state itself. This makes R1 the natural class and makes repair cheap. The distinction that matters is between the working copy, which is reversible, and any operation that publishes, deploys, or notifies, which is not and is kept out of the namespace entirely.

**Public-sector case handling**: Evidence requirements dominate. The value of the representation is not turn reduction but that the ledger and the plan-to-observation diff produce a machine-checkable account of exactly which records were touched, in which order, under whose authority. Here the operation ledger is a deliverable rather than a diagnostic aid, and evidence coverage below 100 percent rejects the result even where the substantive answer is correct.

### 4.2 Scale, Risk, and Reversibility Adaptation

- **Low-risk read-only work**: Set the effect budget to zero, run at tier R0, skip reconciliation entirely, and extend the attempt bound to 5. Overhead above 15 percent of the flat-call baseline indicates the gate should have refused the representation.
- **Mixed-reversibility work**: Decompose into stages by side-effect class and terminate the runtime between them. A single program spanning a read stage and a commit stage cannot be reviewed at one tier, because the tier its worst effect implies is disproportionate to the rest of it.
- **High-effect-count work**: Where the total maximum effect count exceeds 50, decompose rather than raise the budget. The reviewability ceiling of 200 logical lines and 15 effect call sites is what makes tier R2 meaningful; raising it converts review into a formality.
- **Irreversible work**: Keep it out of programs. Where an exception is genuinely required, bind it to one capability version, time-box the exception, require two named approvers, set the effect budget to the exact count, and confirm the reconciliation oracle before rather than after the first execution.
- **Large or unstable catalogues**: Compose the namespace from the policy-eligible set and cap it at 15 bindings per stage. Where selection among near-neighbour capabilities is itself hard, resolve it in a separate discovery stage that binds metadata only, and never inside the executing program.
- **Long-horizon or multi-context runs**: Persist the manifest, plan, key set, and ledger outside the model context, and write a handoff record at every boundary. The key set in particular must survive, since a regenerated key set is the direct cause of effect duplication.

***

## V. Limitations and Considerations

**The efficiency evidence is narrow and mostly provider-reported**: The token reduction figures this guide cites were measured by one provider on its own workloads, and the multi-tool benchmark most often cited compared representations on 82 instances with structured and text baselines restricted to one capability per action, which advantages the representation permitting several. No public benchmark evaluates the full apparatus described here, including the namespace boundary, the ledger, and reconciliation. The mitigation is Step 6.3, which admits no efficiency claim that is not paired against a flat-call arm on the deployment's own tasks, and Section III.D, which subordinates every efficiency metric to the control metrics.

**One transcribed figure could not be reconciled**: The prose source states that the best open-source result in the cited benchmark table was 15.9 percent; the retrieved paper reports 13.4 percent for the best open-source model under the code representation. This guide asserts only that the figure fell below 20 percent, which both readings support. The mitigation is to treat the specific value as unestablished and to rely on the qualitative finding, which is that open-source performance on that benchmark was far below the proprietary result and does not support a general claim for the representation.

**Review does not scale with program size**: The tier system assumes a reviewer can read 200 logical lines and hold 15 effect call sites in mind. That assumption degrades with reviewer fatigue, with unfamiliar languages, and with sources that are syntactically small but semantically dense. The mitigation is the hard decomposition rule in Step 4.3, which refuses any source above those bounds at every tier rather than permitting a longer review, and the review-time metric in Section III.D, which treats a median above 15 minutes as evidence that the bound is wrong for that deployment.

**Reconciliation depends on oracles that may not exist**: The entire partial-effect apparatus rests on being able to ask a system of record whether an operation took effect. Many capabilities do not return a durable operation identifier, do not deduplicate on a caller-supplied key, and expose no query that distinguishes one effect from two. The mitigation is to treat oracle absence as disqualifying: a capability without a reconciliation oracle is not bound into an effectful program namespace, and oracle coverage is tracked as a release metric rather than assumed.

**Static analysis bounds the possible, not the actual**: The static effect inventory establishes an upper bound on what a program can do, and the plan diff establishes that its declarations match its syntax. Neither proves what it will do with inputs not yet seen, and a program whose branch conditions depend on returned data can produce a very different operation set from run to run. The mitigation is that the inventory is a review aid and the ledger is the evidence, with the plan-to-observation diff run after execution as an acceptance check rather than before it as a proof.

**Every threshold here is a deployment default**: The 3-operation admission floor, the 20 percent gain threshold, the 15-binding namespace cap, the 200-line and 15-site review ceiling, the 50-effect decomposition trigger, the 5-attempt and 10-minute reconciliation bound, and the 2-repair attempt limit were chosen to be operable on first deployment. None is derived from a measured property of agent systems. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute them per task class against observed outcomes and to record the override where a domain constraint supersedes a default.

**The representation can conceal intent even when it is correct**: A program that is well formed, correctly scoped, and fully reconciled still presents a reviewer with behaviour rather than a value, and a reviewer approving behaviour approves a class of actions rather than one. This is irreducible: it is the cost the representation carries in exchange for composition. The mitigation is that approval binds at the broker on canonical arguments rather than in advance on source, so that an operation whose arguments were computed at run time is still approved on what it actually does.

**Control conformance is not correct purpose**: An execution can satisfy every checkpoint here, produce a determinate effect set, and still pursue an objective that should not have been pursued. The framework detects malformed and unattributable actions, not misdirected ones, and no checkpoint here substitutes for review of the objective itself.

***

## VI. Conclusion and Summary

Code as action is a representation decision before it is an engineering pattern. Expressing an action as a program buys control flow inside one action, composition without context transit, and expressiveness for computable operations, and it costs individual inspectability, easy failure attribution, and a small blast radius. The three gains are efficiencies and the three costs are control losses, and treating an efficiency as compensation for a control loss is the characteristic error of this pattern.

Three mechanisms repair the three costs, and none of them is optional. Pre-execution review scaled to blast radius restores inspectability by making the program's possible effects derivable from its syntax and by refusing any source too large to actually read. Per-operation records emitted by the broker rather than by the program restore attribution by binding every attempted operation to a call site. Orchestrator-generated idempotency keys plus a reconciliation procedure restore determinacy by ensuring that a program failing at its third effectful operation resolves to a known two-completed, one-resolved state rather than to an opaque one. A deployment that adopts the representation without all three has not moved the cost; it has hidden it.

The namespace is the authority boundary. What a program can reach is the set of functions bound into it, and no prompt, instruction, or declared plan narrows that set. Scoping the namespace per task and per stage, capping it, separating reads from effects, and refusing to let a running program widen it are therefore not hardening measures layered on top of the pattern; they are the pattern's authority model.

**Key Success Factors**:

- **Representation chosen against a baseline**: The program form is admitted only where a paired flat-call measurement shows a gain of at least 20 percent in one declared dimension at non-inferior verified completion.
- **Namespace as the authority boundary**: What is bound is what is reachable; namespaces are scoped per stage, capped at 15 bindings, separated by side-effect class, and never widened by a running program.
- **Every effect individually keyed and individually recorded**: One orchestrator-generated idempotency key per semantic operation, reused across repairs, and one broker-emitted ledger entry per attempted operation at 100 percent coverage.
- **Review proportional to blast radius**: The tier follows from the declared side-effect classes, the source is refused above 200 logical lines and 15 effect call sites, and approval binds to a canonical operation hash rather than to a source digest.
- **Determinate effects before any further action**: No repair, fallback, or result return proceeds while a reconciliation entry is pending, and no operation is ever re-issued to discover whether it already took effect.
- **Terminal rejection over silent repair**: An unrecognised effectful operation rejects the source rather than prompting a variant, because a model that can repair past a rejection holds the authority the rejection was denying.

By following this guide, AI agents can take the compositional and context advantages of expressing an action as a program while keeping every effect that program produces individually authorised, individually recorded, and individually reconcilable.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides that own adjacent layers. The external references that follow are transcribed from the originating prose guide as it cited them, using the labels that source carries rather than reconstructed publication titles. Three entries were independently retrieved during this conversion and are marked as verified; the remainder were not re-verified, and their labels and locations are reproduced rather than checked.

**Corpus pointers**:

- `Production Code as Action for AI Agents` — the originating prose guide from which this operational guide was derived. Source of the three-plane and five-contract model, the mode-selection conditions, the tool-binding and namespace design, the seven-phase workflow, the bounded discovery, repair, verification, approval, and fallback loops, the security and auditability material, the metric definitions, and the readiness checklist. Its execution-environment and canonical-contract material is owned by the sibling guides below and is referenced rather than restated here.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/tool-use/guide_ToolUseAndFunctionCalling.md` — the flat-call representation against which this guide's baseline is defined. Source of the terms side-effect class, idempotency key, logical call, execution attempt, outcome class, unknown outcome, and reconciliation, which this guide adopts rather than redefines.
- `advanced_task_guides/tool-use/guide_CodeExecution.md` — the execution environment this guide selects but does not specify. Owns sandbox provisioning, isolation, egress, resource limits, output truncation, independent oracles, reproducibility, and infrastructure failure classification.
- `advanced_task_guides/tool-use/guide_AgentControlPlane.md` — fleet-level authority and governance. Source of the terms authority scope, non-amplification invariant, policy gate, default-deny posture, budget ledger, quota, and execution grant, which this guide's namespace scoping projects to a single task.
- `advanced_task_guides/tool-use/guide_ToolRetrieval.md` — companion guidance on authorization-filtered capability retrieval, applicable to composing the eligible set in Step 2.1 and to the discovery stage in Step 2.2.
- `advanced_task_guides/tool-use/guide_ModelContextProtocol.md` — companion guidance on governed server integration under a pinned capability contract, applicable to the canonical descriptors from which bindings are compiled.
- `advanced_task_guides/tool-use/guide_AgentSkills.md` — companion guidance on governed capability libraries under progressive disclosure and bounded authority, applicable to staged namespace exposure.
- `advanced_task_guides/tool-use/guide_ComputerUse.md` — companion guidance on the interface-operation representation, which is the alternative where no programmatic capability exists.
- `advanced_task_guides/tool-use/guide_MCPToolGateway.md` — companion guidance on mediated multi-tenant tool access, and the specification of the broker through which every operation in this guide passes. It owns central credential custody, calling-principal propagation across the hop, tenant isolation, authority-keyed caching, dispatch under pinned definitions with drift enforcement, and a declared degraded-operation contract. The typed policy denial recorded as a terminal state in Step 5.2 is issued under that guide's enforcement, and the model never repairs past it.
- `advanced_task_guides/tool-use/guide_StructuredReflectionTool.md` — companion guidance on exposing self-assessment as a schema-constrained tool rather than leaving it implicit in prose, applicable to the bounded repair loop in Step 6.1. It owns the reflect-revise-reverify loop terminated by no-improvement and anti-oscillation rules, and the rule that a verdict alone never satisfies a deterministic gate; a reflection call is one way to draft a repair, never a way to authorise one.

**External references**: Entries marked verified were retrieved during this conversion and their figures confirmed against the retrieved page. All other entries are transcribed as the prose source carried them.

*Provider implementations of programmatic calling*

1. *Anthropic advanced tool use* — https://www.anthropic.com/engineering/advanced-tool-use (verified during conversion: average consumption 43,588 to 27,297 tokens, a 37 percent reduction on complex research tasks; internal knowledge retrieval 25.6 to 28.5 percent; GIA 46.5 to 51.2 percent)
2. *OpenAI Programmatic Tool Calling* — https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling (verified during conversion: capabilities opt in through an allowed-callers field taking direct, programmatic, or both; a running program cannot invoke capability search and deferred capabilities must be loaded before the program starts; the runtime is a fresh isolated V8 environment with no package installation, direct network, filesystem, subprocess, or persistent state)
3. *Claude code execution* — https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool

*Research lineage for programs as reasoning and as action*

4. *CodeAct paper* — https://arxiv.org/html/2402.01030v3 (verified during conversion: 82 human-curated M3ToolEval instances across 17 evaluated models; for one proprietary snapshot, 74.4 percent success and 5.5 average turns under the code representation against 52.4 percent and 7.6 turns under structured calls and 53.7 percent and 7.7 turns under text)
5. *PAL* — https://arxiv.org/abs/2211.10435
6. *Program of Thoughts* — https://arxiv.org/abs/2211.12588
7. *ViperGPT* — https://viper.cs.columbia.edu/

*Frameworks exposing capabilities as callable functions*

8. *TaskWeaver paper* — https://arxiv.org/html/2311.17541v3
9. *TaskWeaver overview* — https://microsoft.github.io/TaskWeaver/docs/overview/
10. *smolagents agent reference* — https://huggingface.co/docs/smolagents/en/reference/agents
11. *smolagents secure code execution* — https://huggingface.co/docs/smolagents/en/tutorials/secure_code_execution
12. *OpenAPI Generator* — https://openapi-generator.tech/
13. *Python asyncio tasks* — https://docs.python.org/3/library/asyncio-task.html

*Isolation boundaries referenced by the execution layer*

14. *WASI security model* — https://wasi.dev/security
15. *gVisor security model* — https://gvisor.dev/docs/architecture_guide/security/

*Risk framing and instrumentation conventions*

16. *OWASP Prompt Injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
17. *OWASP Excessive Agency* — https://genai.owasp.org/llmrisk/llm062025-excessive-agency/
18. *OpenTelemetry GenAI agent spans* — https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md

*Benchmarks cited for representation comparison and their stated limits*

19. *API-Bank* — https://arxiv.org/abs/2304.08244
20. *BFCL paper* — https://proceedings.mlr.press/v267/patil25a.html
21. *SWE-bench Verified* — https://www.swebench.com/verified.html
22. *DS-1000* — https://arxiv.org/abs/2211.11501
23. *BigCodeBench* — https://arxiv.org/abs/2406.15877
24. *ARCADE* — https://arxiv.org/abs/2212.09248
