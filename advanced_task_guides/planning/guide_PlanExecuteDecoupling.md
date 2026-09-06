# Plan-Execute Decoupling

**Status**: Beta testing

**Change logs**:

- [09/06/2026] - Initialization

***

## Executive Summary

Plan-Execute Decoupling is the task family of separating the decision about what work should occur from the observation and performance of that work. A planner emits a complete plan, a parameterised tool sequence, or a dependency graph before any tool runs. An executor then carries out that plan without asking the planner to reason again after every observation: independent work runs concurrently, dependent work waits until named outputs exist, and a joiner or controller decides whether to continue, repair, replan, escalate, or finish. This guide provides AI agents with a structured protocol for admitting a run, freezing a contract, generating and statically validating a typed plan, executing a ready frontier under immutable bindings, verifying results semantically, and replanning within declared bounds.

The pattern is a family rather than a single algorithm. One variant writes a blueprint of plan-and-evidence pairs in which each evidence placeholder names the output of a worker instruction, a worker binds those placeholders, and a solver combines the question, the plans, and the evidence into an answer. Another variant expresses the plan as a directed acyclic graph, streams tasks to a fetching unit that schedules each task as soon as its dependencies are satisfied, and terminates in a joiner that either returns the result or triggers a new plan. Both share the commitment that distinguishes the family: the plan is an explicit, versioned contract, tool observations do not silently rewrite it, and every change creates a visible new plan generation.

The pattern is not a licence to plan once and obey forever. Its useful commitment is narrower: plan enough work up front to remove unnecessary reasoning turns and expose dependencies, then re-enter planning only at declared checkpoints or when evidence invalidates the current graph. An implementation that replans after every tool response has returned to an interleaved agent and has lost the benefit; an implementation that never replans despite invalidated assumptions is an unsafe open-loop workflow. This guide states the loop, the entry and exit conditions, the failure policy, the observability schema, and the metric definitions required to keep an implementation between those two failure modes.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Plan-Execute Decoupling**: An operating pattern in which a planner emits a complete versioned plan before execution begins, an executor performs that plan without returning to the planner after each observation, and a controller re-enters planning only at declared checkpoints or on material invalidation. The separation is logical, not necessarily organisational: one model may act as both planner and final synthesiser, different models may fill those roles, or a human may approve a plan that software executes.

**Run contract**: The frozen record of the objective, accepted inputs, success criteria, hard constraints, preferences, risk class, deadlines, budgets, allowed tools and actors, approval requirements, side-effect policy, evidence standard, and terminal conditions. Planning has no stable target without this record, and a run admitted without it cannot be evaluated at exit.

**Plan intermediate representation**: The machine-checkable structure that records tasks as individually addressable operations. Every task carries a stable identifier, a purpose, a registered operation or executor, typed input expressions, an expected output type, dependencies, a completion validator, a timeout, a retry classification, a side-effect and idempotency policy, resource needs, and a risk level.

**Task**: One addressable unit of the plan. A sequence of tasks is sufficient when every step genuinely depends on the previous one; a directed acyclic graph is preferable when work can fan out and later join.

**Placeholder**: A typed reference to an output that does not yet exist. A conforming placeholder identifies the producing task and the specific output field rather than referring to a previous result in general terms. It is the operational form of the evidence variable used by the blueprint variant of the pattern.

**Binding**: The resolution of a placeholder from a validated, immutable task output, performed immediately before dispatch and accompanied by checks of type, freshness, provenance, sensitivity, and authorisation scope.

**Artifact**: An immutable stored output produced by a validated attempt, addressed by identifier and hash, and carrying provenance sufficient to reconstruct which task and which attempt produced it.

**Plan generation**: An immutable version of the remaining work. A replan creates a new generation linked to its predecessor and names the preserved, superseded, added, and invalidated tasks. Completed real-world effects are facts that replanning cannot erase.

**Ready frontier**: The set of tasks whose required predecessors hold their declared validated state, whose required placeholders are bound, whose time window is open, whose authorisation is current, whose resources and concurrency slots are available, and which have not been cancelled or superseded.

**Static validator**: The component that rejects malformed or unsafe plans before any tool runs, checking operation existence, type agreement, placeholder producers, acyclicity, constraint satisfaction, permission coverage, concurrency safety, budget plausibility, validator presence, and reachability of success.

**Postcondition validator**: The component that decides whether an apparent result is usable, checking transport success, output schema, semantic postconditions, evidence quality, freshness, policy compliance, and any external receipt. Only this component may move a task to a validated terminal state.

**Joiner or controller**: The component that decides, at a declared join or on invalidation, whether to continue, repair locally, create a new plan generation, escalate, or finish. It is the only component permitted to author or approve a new generation.

**Synthesizer**: The component that produces the requested result from validated artifacts with provenance rather than from an unexamined transcript.

**Side-effect class**: The classification of each action as read-only, reversible, compensable, approval-gated, or irreversible. This classification governs retry eligibility, speculation eligibility, approval requirements, and reconciliation duties.

**Uncertain side effect**: An attempt whose outcome in the external system is unknown, typically after a timeout. A timeout never proves that an external action did not occur.

**Speculative task**: A task dispatched before a gate has decided whether it is needed. Speculation is admissible only for read-only or safely cancellable work.

**Wasted work**: Cost or task time spent on outputs later invalidated, superseded, duplicated, or cancelled. It is the primary hidden cost of the pattern and is measured separately from model token cost.

**Critical path**: The longest chain of strictly dependent tasks in the accepted graph. It bounds the wall-clock benefit available from concurrency: a parallel executor can reduce elapsed time toward the critical path, but it cannot make a chain of strict dependencies parallel.

***

### 1.2 The Minimum Operating Model and the Contrast With Interleaved Reason-Act Loops

A reliable implementation needs more than a prose checklist. The minimum operating model consists of eight components with distinct authority. The planner proposes tasks, bindings, dependencies, and acceptance conditions. The static validator rejects malformed or unsafe plans before tools run. The scheduler computes which tasks are ready. The executor invokes only registered operations with bound inputs and current authorisation. The postcondition validator decides whether an apparent result is usable. The joiner or controller decides whether to continue, repair, replan, escalate, or finish. The synthesizer produces the requested result from validated artifacts. The recorder writes an append-only event log from which every one of these decisions can be reconstructed.

Two structural variants of the pattern are attested and both are executable. The blueprint variant asks the planner to write plan-and-evidence pairs before any tool runs, where each evidence placeholder names the output of a worker instruction and later instructions refer to earlier placeholders; a worker executes the instructions and binds the evidence, and a solver combines the original question, the plans, and the evidence into the answer. The name given to that approach reflects its central claim: the planning reasoning is not repeatedly conditioned on tool observations [8]. The graph variant expresses the plan as a directed acyclic graph, allows the planner to stream tasks, schedules a task as soon as its dependencies are satisfied, and terminates in a joiner that either returns the result or triggers another plan. The graph variant makes concurrency an architectural property rather than an accidental batch of calls [9][10].

A conceptual precursor asks a language model first to divide a problem into subtasks and then to execute those subtasks, responding to the missing-step errors seen in ordinary zero-shot chain-of-thought reasoning; an extended variant adds instructions intended to reduce calculation errors [11][12]. That precursor can remain entirely inside one model response. Plan-Execute Decoupling extends the same separation into an operational system with tools, typed outputs, dependencies, scheduling, validation, and failure recovery.

**Contrast with interleaved reason-act control**: The clearest contrast is the interleaved controller that alternates reasoning, action, and observation, allowing each live result to shape the next action [13]. That feedback makes the interleaved controller appropriate when the next step cannot be known until a page, environment, user, or tool responds. It also means observations and prior reasoning repeatedly enter the model context, which increases model invocations and lengthens prompts. Plan-Execute Decoupling trades some of that responsiveness for fewer planning calls, a smaller reasoning context, and concurrency.

Neither control style dominates. AI agents must select the interleaved controller when observations have high branching value, when actions reveal the state needed to choose the next action, or when a wrong early assumption would invalidate most later work. AI agents must select Plan-Execute Decoupling when the dependency structure is predictable, when most tool outputs fill known slots rather than redefine the objective, and when latency or cost benefits justify an explicit plan representation. A hybrid is appropriate when a stable outer graph contains a few reactive nodes: each such node runs a bounded interleaved loop and returns one validated output to the decoupled executor.

**Treatment of published efficiency results**: Reported figures for the blueprint variant include a fivefold token efficiency gain and a four-percentage-point accuracy improvement on a multi-hop question-answering benchmark, alongside evaluation across six public benchmarks and robustness tests under tool failure [8]. Reported figures for the graph variant include latency speedups of up to 3.7 times, cost reductions of up to 6.7 times, and accuracy improvements of up to approximately nine percent relative to an interleaved baseline, with different gains by task class [14]. Results expressed as maxima on selected benchmarks are evidence that the architecture can help, not production forecasts. Realised gains depend on graph width, critical-path length, tool latency, model pricing, cache behaviour, rate limits, retries, and the amount of replanning, so AI agents must treat every such figure as a hypothesis to be tested locally.

**Relation to neighbouring planning patterns**: Plan-Execute Decoupling states when planning and observation occur. It does not state how a valid plan is generated, how tasks survive workers and queues, or how an ambiguous objective becomes measurable. Eight neighbouring planning patterns belong to the same family and supply what this pattern leaves unstated. The following table records the division of responsibility.

**Neighbouring pattern relationships**:

| Pattern | Relation to Plan-Execute Decoupling | Condition favouring the neighbour |
| :-- | :-- | :-- |
| Meta-reasoning | Selects which reasoning method to use and how much computation to allocate; the decoupled joiner performs only a limited meta-level decision among continue, repair, and replan | The system must choose among decoupled planning, interleaved control, formal solving, simulation, retrieval, or human review |
| Hierarchical task network planning | Supplies domain-authored methods that refine compound tasks into permitted primitive networks and can generate the upfront graph the executor runs | Repeatable domain procedure and applicability conditions are central |
| Task management and orchestration | Governs task state, scheduling, assignment, retries, handoffs, compensation, and durable progress; supplies the runtime substrate a plan needs to survive workers, queues, and long waits | Multi-agent or side-effecting work requires durable runtime state |
| Intelligent goal decomposition | Turns a vague objective into measurable subgoals before tasks are formed; the decoupled planner must not silently repair an ambiguous objective by inventing goals | The objective is not yet measurable |
| Constraint satisfaction planning | Searches for assignments or schedules that satisfy hard and soft constraints; may be invoked as a planning component or as a graph task | Resource allocation, routing, timetabling, or combinatorial feasibility is difficult |
| Scenario-based planning | Develops contingent graphs and signposts across plausible futures; a signpost activates the corresponding branch or triggers a new generation | Deep uncertainty, not merely unknown tool values, drives the decision |
| World-model simulation planning | Predicts consequences of candidate actions before real execution; may score candidate plans or validate a dangerous task before dispatch | Actions are costly or irreversible and the environment can be modelled |
| Plan and todo recitation | Keeps the objective and work list salient in a long context; must not become the source of truth over the versioned graph | A human or executor needs the active frontier restated during long execution |

***

### 1.3 Selection Criteria: When to Use and When Not to Use the Pattern

**Admission conditions**: AI agents must adopt Plan-Execute Decoupling when at least six of the following eight conditions hold, and must record which conditions failed when adopting it on fewer.

1. The task requires several tool calls, model workers, data sources, or specialist agents.
2. Dependencies can be stated before execution, even where the actual values are unknown.
3. Several tasks are independent and tool latency is large enough for concurrency to matter.
4. Intermediate outputs mostly populate known fields rather than determine an entirely new strategy.
5. Tool interfaces and output schemas are stable and machine-checkable.
6. The work benefits from an auditable plan, explicit data lineage, predictable budgets, or human plan approval.
7. Repeatedly sending prior observations to a large model is a material token or monetary cost.
8. The system can detect stale assumptions, validate outputs, and replan safely.

Candidate task classes include multi-source research, document assembly, data-enrichment pipelines, report generation, test suites, batch interface operations, codebase analysis, compliance checks, and multi-agent work whose branches have clear inputs and joins [15]. The pattern is most attractive when total tool time greatly exceeds planning time and the graph has a wide ready frontier. Concurrency remains bounded by worker capacity, tool quotas, resource locks, and join delays, so a wide graph does not by itself guarantee a wall-clock benefit.

**Exclusion conditions**: AI agents must not adopt the pattern in the following situations, and must record the rejection reason in the run log.

- **Trivial control flow**: A single call, a short deterministic transformation, or a two-step chain whose ordinary application control flow is already clear. The plan parser, graph store, scheduler, and joiner would add more latency and failure surface than they remove.
- **Probe-driven work**: Each action is primarily an information-gathering probe that determines the next action. Interactive browsing, negotiation, diagnosis with unknown failure causes, rapidly changing environments, and exploratory conversations favour an interleaved controller or a short receding-horizon plan.
- **Unverifiable tool semantics**: Tool semantics are undocumented, outputs are unstructured, side effects cannot be reconciled, or the system lacks postcondition checks. A syntactically valid graph can still be semantically wrong.
- **Unsafe parallelism**: Tasks appear in the same layer but contend for a rate limit, modify the same record, rely on an undeclared assumption, expose sensitive data to different actors, or make incompatible side effects. Parallelism is a safety decision as well as a scheduling decision.
- **High discard probability**: Most branches of a large speculative graph are likely to be discarded after one early observation. Where more than 50% of planned tasks are expected to be discarded after the first gate, plan a short prefix, execute the high-information gate, and generate the next graph from its validated result.
- **Benchmark-driven adoption**: The pattern is selected from published maxima rather than from local measurement. Comparison against a direct call, a fixed workflow, and an interleaved agent on the adopting organisation's own tasks at matched quality and safety is a precondition for adoption.

**Planning horizon selection matrix**:

| Expected share of tasks whose definition an observation would change | Selected control style | Consequence of misselection |
| :-- | :-- | :-- |
| Below 30% | Full decoupling over a complete graph | None; this is the intended operating region |
| 30% to 60% | Receding-horizon decoupling with a prefix of at most 5 tasks per generation | A full graph in this region produces wasted work above the 15% budget and forces early replanning |
| Above 60% | Interleaved controller, with decoupled subgraphs only inside stable regions | A full graph in this region degrades into replanning after most observations and loses the token and latency benefit entirely |

***

## II. Operational Framework: Contracted Planning, Bound Execution, and Bounded Replanning

### Phase 1: Run Admission and Contract Freezing

**Objective**: Establish an evaluable target, a control-style decision, and a registered operation catalogue before any plan is generated, so that planning has a stable contract and the executor holds no capability the contract did not authorise.

#### Step 1.1: Freeze the Run Contract and Test Entry Conditions

**Required Actions**:

- Create the run identifier and the initial plan-generation identifier, and bind every subsequent record to both.
- Record the objective, accepted inputs, success tests, hard constraints, preferences, risk class, permissions, evidence requirements, deadlines, and the terminal conditions that end the run.
- Record numeric limits for planning calls, model tokens, tool calls, parallelism, monetary cost, retries per attempt, and plan generations per run.
- Classify every anticipated action as read-only, reversible, compensable, approval-gated, or irreversible, and attach the approval requirement to each class.
- Refuse admission where the objective, success criteria, required evidence, risk tier, authorised tools, budgets, or material constraints are not explicit enough to evaluate a plan, unless the plan may include an authorised observation or clarification task that obtains the missing element.

**Required Outputs**:

- A frozen run contract carrying all thirteen contract fields with no field left unset.
- A numeric budget record covering planning calls, tokens, tool calls, concurrency, money, retries, and generations.
- A side-effect classification for every anticipated action class.
- An admission verdict with its reason code.

**Quality Checkpoints**:

- Every contract field carries a value or an explicit authorised task that will obtain it; a run with an unset field and no obtaining task is refused.
- Every budget limit is a number rather than a qualitative bound, and each names the action taken at exhaustion.
- No action class is left unclassified for side effects; an unclassified action is treated as irreversible until classified.
- The success criteria are stated so that a terminal verdict can be computed without further human interpretation.

***

#### Step 1.2: Run the Suitability Gate and Select the Planning Horizon

**Required Actions**:

- Estimate whether the work has a predictable dependency structure, reusable tool contracts, and useful parallel width, expressing parallel width as the expected maximum ready-frontier size.
- Estimate the share of tasks whose definition an early observation would change, and apply the horizon selection matrix in Section 1.3.
- Select full decoupling, a receding-horizon graph of at most 5 tasks per generation, or an interleaved controller.
- Record the rejected alternatives with the reason each was rejected, so that the decision can be audited against outcome metrics.
- Compare the expected benefit against a direct call and a fixed workflow before accepting the additional machinery.

**Required Outputs**:

- A suitability decision record naming the selected control style.
- A parallel-width estimate and a critical-path length estimate for the anticipated graph.
- A rejected-alternatives list with reason codes.

**Quality Checkpoints**:

- The selected control style matches the horizon selection matrix, or a recorded justification states why it does not.
- Expected parallel width is at least 2 for full decoupling; a width of 1 indicates a strict chain for which the pattern supplies no concurrency benefit, and the decision is re-examined before planning.
- The rejected-alternatives list contains at least two entries, one of which is a simpler baseline.

***

#### Step 1.3: Normalise the Operation Catalogue

**Required Actions**:

- Assign every allowed tool, model worker, human task, and subworkflow a registered identifier and version.
- State for each registered operation the input schema, output schema, preconditions, required permissions, side effects, idempotency behaviour, expected latency and cost, timeout, retryable failure classes, and completion validator.
- Prohibit the planner from inventing executable operation names or free-form arguments, restricting it to identifiers present in the catalogue.
- Record the catalogue version so that plan validation can be replayed against the catalogue that was in force.

**Required Outputs**:

- A versioned operation catalogue with one entry per authorised operation.
- A per-operation validator reference for every entry.
- A catalogue version identifier bound to the run.

**Quality Checkpoints**:

- Every catalogue entry carries all eleven declared attributes; an entry missing a completion validator is not executable and is withheld from the planner.
- No operation is exposed to the planner without an explicit permission statement.
- Operations with irreversible side effects carry an approval requirement and a compensation policy, or they are withheld from the catalogue entirely.

***

### Phase 2: Plan Generation and Dependency Construction

**Objective**: Produce the smallest complete plan likely to satisfy the contract, expressed as typed tasks connected by explicit placeholders and a validated dependency structure.

#### Step 2.1: Generate the Candidate Plan

**Required Actions**:

- Instruct the planner to produce the smallest complete plan likely to satisfy the contract, rather than the most detailed plan it can produce.
- Require each task to state its operational purpose, registered executor, typed input expressions, declared output fields, dependencies, validator, risk class, and failure policy.
- Require the planner to distinguish facts already known from assumptions and from unresolved values, and to record each assumption as a separately addressable item.
- Generate at least two alternative plans, or submit the plan to an independent critic before execution, whenever the run contract carries a high risk class or any irreversible action.
- Reject any first generation exceeding 40 tasks without hierarchical decomposition, and require a two-level plan instead.

**Required Outputs**:

- A candidate plan in the plan intermediate representation with one entry per task.
- An assumption register separating known facts from assumptions and unresolved values.
- An alternatives record for high-risk runs, naming the plan selected and the basis of selection.

**Quality Checkpoints**:

- Every task names a registered operation from the catalogue version bound to the run; a task naming an unregistered operation invalidates the plan.
- Every task carries all eight declared attributes; a task missing a validator or a failure policy is rejected before graph derivation.
- Every assumption in the register is addressable, so that its later falsification can name the affected subgraph.
- The plan contains no task whose only justification is that it might prove useful; speculative tasks are marked as such and counted against the 10% speculative cost budget.

***

#### Step 2.2: Create Explicit Placeholders and Data Lineage

**Required Actions**:

- Replace every unknown value in the plan with a reference to a named producer output rather than an anticipated literal value.
- Require each downstream task to refer to a specific field of a specific producing task rather than to a previous result in general terms.
- Assign each placeholder a type, a required or optional status, a resolution rule, and a freshness window expressed in a time unit.
- Mark any task holding an unresolved required placeholder as blocked, and prohibit its dispatch until binding succeeds.
- Prohibit the planner from copying an anticipated value into task prose as a substitute for a placeholder.

**Required Outputs**:

- A placeholder inventory naming producer task, producer output field, consumer input field, type, status, resolution rule, and freshness window.
- A data lineage map connecting every consumed input to its producing task.

**Quality Checkpoints**:

- Every placeholder identifies both a producing task and an output field; a placeholder referring only to a preceding step blocks plan acceptance.
- Every required placeholder has exactly one producer; a required placeholder with two producers and no declared selection rule is rejected.
- No task input contains a literal value that the plan cannot trace to the contract inputs or to a producing task.
- A freshness window is declared for every placeholder, defaulting to 15 minutes for volatile external sources; a placeholder without a window inherits the strictest declared window in the run.

***

#### Step 2.3: Derive and Validate the Dependency Graph

**Required Actions**:

- Add an edge whenever a task consumes another task's output, requires its completion state, or must wait for its side effect.
- Declare fan-out, join, conditional branch, cancellation, and optional-task semantics explicitly for every branching and merging point.
- Reject accidental cycles, and represent intentional iteration through bounded new task occurrences or a declared controller loop rather than through a cyclic graph with no exit.
- Compute the predicted critical path, the maximum graph width, and the expected makespan under the declared concurrency limit.
- Assign concurrency groups so that tasks sharing a mutable resource, a rate limit, or a security scope cannot be scheduled together.

**Required Outputs**:

- A dependency graph with typed edges and declared branching semantics.
- A predicted critical path with its estimated duration.
- A concurrency group assignment covering every task with a side effect or a shared resource need.

**Quality Checkpoints**:

- The graph is acyclic; any cycle blocks acceptance and returns the plan to the planner with the cycle named.
- Every fan-in point declares its join semantics, including whether partial arrival is acceptable and at what count.
- Maximum graph width does not exceed the declared concurrency limit by more than a factor of 4; a wider graph is re-examined for scheduler starvation before acceptance.
- No two tasks writing the same resource share a concurrency group; a conflict blocks acceptance rather than being resolved at dispatch time.

***

### Phase 3: Static Validation, Approval, and Plan Freezing

**Objective**: Prove before any consequential execution that the plan is executable, permitted, safe to parallelise, budget-plausible, and capable of reaching the declared success condition, then commit it as an immutable generation.

#### Step 3.1: Run Static Plan Checks Before Execution

**Required Actions**:

- Confirm that every operation exists in the bound catalogue version and that argument and output types match the declared schemas.
- Confirm that every placeholder producer exists, that all required outputs are consumed correctly, and that no declared output is orphaned without a stated reason.
- Confirm acyclicity, hard-constraint satisfaction, permission coverage at both planning and execution scope, concurrency-group safety, and budget plausibility against the Phase 1 limits.
- Confirm that every task carries a validator and that every side-effecting task carries an approval, reconciliation, and compensation policy.
- Confirm that final success is reachable from the proposed outputs by tracing every top-level acceptance criterion to at least one producing task.
- Treat schema conformance as a representational check only, recording that strict structured output constrains shape rather than establishing factual correctness, authorisation, freshness, or feasibility.

**Required Outputs**:

- A static validation report with one verdict per check class.
- A defect list naming the task and the failing check for every rejection.
- A reachability trace connecting each acceptance criterion to its producing tasks.

**Quality Checkpoints**:

- All ten check classes return a verdict; an unrun check is treated as a failure.
- 100% of tasks reference registered operations; any violation rejects the plan without partial execution.
- Every top-level acceptance criterion traces to at least one producing task; an untraceable criterion rejects the plan.
- The validation report distinguishes planner defects from catalogue defects, so that error attribution metrics remain accurate.

***

#### Step 3.2: Obtain Approval for Consequential Work

**Required Actions**:

- Route the validated plan to human approval whenever it contains an irreversible action, an approval-gated action, or a single task whose projected cost exceeds 5% of the run budget.
- Present the approver with the objective, the affected external systems, the irreversible steps, the compensation policy, and the projected cost and latency.
- Record the approval as an explicit artifact bound to the graph hash, so that a later graph change invalidates the approval rather than inheriting it.
- Withhold dispatch of every approval-gated task until its approval artifact is bound.

**Required Outputs**:

- An approval artifact naming approver, scope, graph hash, and timestamp, or a recorded determination that no approval is required.
- An approval-gated task list with the binding status of each entry.

**Quality Checkpoints**:

- Every irreversible task carries an approval artifact bound to the current graph hash; an approval bound to a superseded hash is not valid for execution.
- No approval covers a task class broader than the one presented to the approver.
- The approval decision and its latency are recorded, since approval wait is a reported latency component.

***

#### Step 3.3: Freeze the Accepted Plan Generation

**Required Actions**:

- Store an immutable canonical representation of the accepted plan together with its graph hash.
- Record the assumption register, the planner and prompt versions, the predicted critical path, the expected cost and latency, the approval record, and the validation result.
- Permit execution to annotate runtime state, and prohibit it from mutating task definitions or edges in place.
- Store the plan outside conversational memory, and treat any restatement of the plan in a model context as a convenience copy rather than as the source of truth.

**Required Outputs**:

- A frozen plan generation with a stable identifier, a parent generation reference where applicable, and a graph hash.
- A provenance record naming planner version, prompt or policy version, and catalogue version.

**Quality Checkpoints**:

- The stored representation reproduces the graph hash on recomputation; a mismatch halts execution.
- No mutation path exists from an executor to a task definition or an edge; runtime state is written to separate records.
- The plan of record is retrievable without reference to any model context window.

***

### Phase 4: Frontier Scheduling and Bound Dispatch

**Objective**: Dispatch only work whose current validated bindings, authorisations, and resource conditions permit it, and convert declared graph parallelism into safe concurrent execution.

#### Step 4.1: Compute the Ready Frontier

**Required Actions**:

- Admit a task to the frontier only when every required predecessor holds its declared validated state, every required placeholder is bound, the time window is open, authorisation is current, resources and concurrency slots are available, and the task has not been cancelled or superseded.
- Prioritise ready tasks by critical-path impact, deadline slack, information value, risk, resource efficiency, and waiting age.
- Keep hard gates as gates, prohibiting the conversion of authorisation, resource locks, or side-effect safety into weighted preferences that a high priority score can override.
- Record the blocked set with a reason code for every blocked task, so that a stalled graph can be diagnosed without replay.

**Required Outputs**:

- A ready set for the current scheduling cycle.
- A blocked set with one reason code per entry.
- A priority ordering with its component scores.

**Quality Checkpoints**:

- Every task in the ready set satisfies all seven readiness conditions; a task admitted on six conditions is a scheduler defect that halts the cycle.
- Every blocked task carries exactly one primary reason code drawn from the declared code set.
- No hard gate appears as a weighted term in the priority function.
- An empty ready set with unfinished required tasks raises the blocked-graph condition rather than being interpreted as completion.

***

#### Step 4.2: Bind Inputs Immediately Before Dispatch

**Required Actions**:

- Resolve each placeholder from the producing artifact at dispatch time rather than at plan time, and verify type, freshness against the declared window, provenance, sensitivity class, and authorisation scope.
- Recheck the task preconditions against observed state rather than against the planner's projected state.
- Serialise the exact bound request, create an attempt identifier, and attach an idempotency key to every retriable side effect.
- Prohibit any worker from resolving a placeholder out of another worker's conversational memory, and require resolution from the artifact store.
- Prohibit silent coercion of a mismatched value, recording any coercion or repair as a separate event subject to its own threshold.

**Required Outputs**:

- A bound request record with the input hash and the attempt identifier.
- A binding verification record covering type, freshness, provenance, sensitivity, and authorisation.
- An idempotency key for every retriable side-effecting attempt.

**Quality Checkpoints**:

- 100% of dispatched inputs resolve from validated artifacts; a binding drawn from conversational memory is a security defect that halts the run.
- Every artifact consumed is within its declared freshness window; an artifact outside the window marks the placeholder stale and blocks the dependent task rather than proceeding.
- Silent coercion count is 0; any recorded coercion rate above 1% of bindings triggers a planner or schema review.
- Every side-effecting attempt carries an idempotency key before dispatch; a missing key blocks the dispatch.

***

#### Step 4.3: Dispatch Independent Ready Tasks Concurrently

**Required Actions**:

- Dispatch only tasks whose data, resource, security, and side-effect relationships permit concurrency, using the concurrency groups assigned in Step 2.3.
- Enforce global, per-tool, per-tenant, and per-resource concurrency limits, holding provider utilisation at or below 50% of the applicable rate quota by default.
- Apply backpressure when dispatch queue depth exceeds the declared concurrency limit by more than a factor of 2, rather than expanding the worker pool.
- Treat concurrency as an application policy, since a model response containing several tool calls does not establish that those calls are independent and does not transfer dependency or validation responsibility away from the controller.
- Cancel speculative tasks as soon as the gate they anticipated resolves against them.

**Required Outputs**:

- A dispatch record naming the selected tasks, the deferred tasks, and the concurrency slots consumed.
- A utilisation record per tool and per tenant for the scheduling cycle.

**Quality Checkpoints**:

- No two tasks in the same concurrency group are in flight simultaneously.
- Provider utilisation stays at or below the declared quota share; a breach triggers backpressure rather than retry amplification.
- Every dispatched batch derives from the readiness computation rather than from a model's grouping of calls in a single response.
- Speculative in-flight cost stays at or below 10% of run cost; a breach cancels the lowest-value speculative tasks first.

***

### Phase 5: Attempt Execution, Semantic Validation, and Local Repair

**Objective**: Convert each dispatched attempt into either an immutable validated artifact or a classified failure, and exhaust deterministic local recovery before any planning call is made.

#### Step 5.1: Execute Each Attempt Within Its Contract

**Required Actions**:

- Invoke only the bound operation with the bound inputs, observing the declared timeout and resource limits.
- Record the response or error without interpreting an arbitrary response as success.
- Permit a task to stream progress, and prohibit any component other than the postcondition validator from moving the task to a validated terminal state.
- Checkpoint immutable artifacts outside model context for long-running work, so that a crash preserves accepted results.
- Mark an attempt whose outcome is unknown after a timeout as an uncertain side effect rather than as a failure.

**Required Outputs**:

- An attempt record with dispatch, start, and finish timestamps and the raw status.
- A checkpointed artifact reference for every long-running task that produced partial output.
- A side-effect certainty classification for every attempt against a side-effecting operation.

**Quality Checkpoints**:

- No executor writes a validated state; transitions to validated originate only from the postcondition validator.
- Every attempt terminates in exactly one declared status class, with no attempt left in flight beyond its timeout plus a 60 second grace period.
- Every uncertain side effect is recorded as uncertain rather than as a failure, since the two classes carry different retry policies.

***

#### Step 5.2: Validate and Bind Each Result

**Required Actions**:

- Check transport success, output schema, semantic postconditions, evidence quality, freshness, policy compliance, and any external receipt before accepting a result.
- Classify the attempt as validated success, retryable failure, permanent failure, policy denial, cancelled, or uncertain side effect.
- Store an immutable artifact on validated success, bind its named fields to the consuming placeholders, and record the artifact hash.
- Recompute only the affected portion of the frontier after publication, so that newly unblocked work can begin without a full graph sweep.
- Treat schema conformity as necessary and insufficient, classifying a response that parses correctly but fails a semantic postcondition as a failure.

**Required Outputs**:

- A validation verdict per attempt with its classification code.
- An immutable artifact with hash and provenance for every validated success.
- An updated frontier limited to the tasks affected by the newly published outputs.

**Quality Checkpoints**:

- Every accepted result passed all seven validation checks; acceptance on transport success alone invalidates the artifact.
- Every artifact carries a hash and a producing attempt reference; an artifact without provenance cannot be bound.
- Frontier recomputation touches only successors of the published task; full recomputation on every publication is a performance defect at graph widths above 20 tasks.

***

#### Step 5.3: Handle Local Failure Before Global Replanning

**Required Actions**:

- Retry only when the failure is declared transient, the objective and preconditions remain valid, side effects are idempotent or reconciled, and attempt and budget limits remain, applying a default limit of 2 retries per attempt.
- Reconcile external state before retrying any uncertain side effect, by reading the target system rather than by re-issuing the action.
- Repair a malformed local input, or substitute a registered equivalent operation, where the surrounding graph remains sound.
- Prohibit escalation of a deterministic infrastructure retry to the planner, since a planning call cannot solve a transport failure the executor can handle.
- Escalate to Phase 6 only after local retry and local repair are exhausted or are inapplicable by classification.

**Required Outputs**:

- A local recovery record naming the failure class, the recovery action, and the outcome.
- A reconciliation record for every uncertain side effect, naming the external read performed.
- An escalation verdict where local recovery did not restore the task.

**Quality Checkpoints**:

- No retry is issued against an uncertain side effect before an external reconciliation read; a retry without reconciliation is a correctness defect.
- Retry count per attempt does not exceed 2; the third failure escalates rather than retrying.
- No planner invocation appears in the log for a failure classified as transient transport error.
- Local repair preserves task identity and graph structure; a repair that changes dependencies is a replan and belongs to Phase 6.

***

### Phase 6: Invalidation Detection and Bounded Replanning

**Objective**: Re-enter planning only on material invalidation, construct the next generation from observed state while preserving verified work, and bound the replanning loop so that it cannot consume the run.

#### Step 6.1: Trigger Replanning Only on Material Invalidation

**Required Actions**:

- Trigger replanning when a required output is unavailable or semantically unsuitable, an assumption proves false, a task or tool disappears, a hard constraint changes, an observed side effect diverges from its prediction, the graph becomes blocked, remaining work cannot meet budget or deadline, or the joiner concludes the objective is not yet satisfied.
- Refuse to treat a merely weak answer as a replanning trigger, and require the failing acceptance criterion to be named.
- Record the affected subgraph, the failure signature, and the detection source for every trigger.
- Prohibit replanning after an ordinary successful observation, since that restores the invocation and context overhead the pattern exists to remove.

**Required Outputs**:

- A replan trigger record naming the trigger class, the violated assumption or acceptance criterion, and the detection source.
- An affected subgraph specification listing invalidated tasks and preserved tasks.
- A failure signature suitable for repeated-failure detection.

**Quality Checkpoints**:

- Every replan is attributable to exactly one of the eight declared trigger classes; an unattributed replan is a controller defect.
- No replan is triggered by a successful, validated observation that satisfied its declared postconditions.
- The affected subgraph names both invalidated and preserved tasks; a trigger invalidating the entire graph without justification is reviewed before the new generation is created.

***

#### Step 6.2: Construct the Next Plan Generation From Observed State

**Required Actions**:

- Supply the replanner with the original contract, the validated artifacts, the completed and irreversible effects, the failed task and reason codes, the remaining budgets, the superseded graph, and the explicit scope of permitted change.
- Preserve every unaffected completed task, and replace the smallest invalid subgraph that restores validity.
- Create fresh task occurrences wherever inputs or semantics changed, rather than reusing an occurrence whose bindings no longer hold.
- Repeat static validation, approval where required, freezing, and frontier computation for the new generation.
- Record preserved, superseded, added, and invalidated tasks in the generation record.

**Required Outputs**:

- A new plan generation with a parent reference, a new graph hash, and a change classification per task.
- A preserved-work record naming the artifacts carried forward.
- A re-validation report for the new generation.

**Quality Checkpoints**:

- Completed irreversible effects appear in the new generation as facts rather than as work to repeat.
- The proportion of remaining tasks changed by the replan is at or below 40%; a larger change is treated as a full replan and requires renewed approval where the original plan required approval.
- The new generation passes the same ten static check classes as the first; a generation that skips validation is not executable.
- No artifact validated under a prior generation is discarded without a recorded invalidation reason.

***

#### Step 6.3: Protect the Replan Loop With Bounded Limits

**Required Actions**:

- Enforce limits on plan generations per run, changed tasks per replan, repeated graph signatures, repeated failure signatures, replanning token cost, elapsed time, and speculative fan-out.
- Halt identical retries when the same state and a materially equivalent plan recur without new evidence, using a default threshold of 2 equivalent signatures.
- Escalate to human takeover or a safe terminal state when the generation limit of 5 per run is reached without a validated path to success.
- Record replanning cost separately from execution cost, since a run may succeed on quality while failing on efficiency.

**Required Outputs**:

- A loop-protection record naming each limit, its current value, and its headroom.
- An escalation or safe-stop verdict where a limit is reached.

**Quality Checkpoints**:

- Every declared limit has a current measured value; an unmeasured limit provides no protection.
- Two materially equivalent plan signatures without new evidence stop the loop rather than producing a third generation.
- Generation count does not exceed 5 per run; the sixth trigger produces an escalation or a compensated failure rather than a new graph.
- Replanning cost stays at or below 20% of total run cost; a breach is reported as an efficiency defect even where the run succeeds.

***

### Phase 7: Join, Synthesis, Verification, and Closure

**Objective**: Convert validated artifacts into the contracted deliverable, verify it independently against every acceptance criterion, and close the run in an auditable terminal state with all side effects reconciled.

#### Step 7.1: Join and Synthesise From Validated Artifacts

**Required Actions**:

- Check coverage, contradiction, missing evidence, constraint satisfaction, and answerability of the top-level objective when all required branches reach their declared join state.
- Supply the synthesizer with the contract, the accepted plan, and the relevant validated artifacts with provenance, withholding raw logs and unexamined transcripts by default.
- Repair the output directly where synthesis reveals only a local presentational defect.
- Return control to the joiner and create a new plan generation where synthesis reveals missing work rather than a presentational defect.
- Record which artifacts entered synthesis, so that a later error can be traced to its source artifact.

**Required Outputs**:

- A join verdict naming required branches, arrived branches, and any missing or conflicting artifacts.
- A synthesised deliverable with an artifact lineage record.
- A defect classification distinguishing presentational repair from missing work.

**Quality Checkpoints**:

- Every required branch reached its declared join state, or the join semantics declared partial arrival acceptable at a stated count.
- Contradictions between artifacts are disclosed rather than silently resolved by the synthesizer.
- The synthesis input set contains only validated artifacts; inclusion of an unvalidated observation invalidates the deliverable.
- Every material claim in the deliverable traces to a named artifact.

***

#### Step 7.2: Run Final Independent Verification

**Required Actions**:

- Re-evaluate every top-level acceptance criterion, material factual claim, calculation, required approval, and consequential action against observed evidence.
- Use deterministic tests, primary sources, external state reads, or a differently configured reviewer where the risk class warrants independence.
- Treat a final model's expressed confidence as inadmissible in place of evidence.
- Record a per-criterion verdict rather than a single aggregate pass, so that partial completion can be reported accurately.

**Required Outputs**:

- A verification report with one verdict per acceptance criterion.
- An evidence reference for every material claim.
- A list of failed criteria, with the producing task identified for each.

**Quality Checkpoints**:

- 100% of top-level acceptance criteria are re-evaluated; an unevaluated criterion blocks a success verdict.
- Every material claim carries at least one evidence reference; a claim without evidence is removed or marked unsupported before delivery.
- Verification uses at least one source or method independent of the producing task for every high-risk criterion.
- No criterion is marked satisfied on the basis of a confidence statement alone.

***

#### Step 7.3: Close and Reconcile the Run

**Required Actions**:

- Assign an explicit terminal state and reason code from the declared set: verified success, verified partial completion, safe abstention, cancellation, compensated failure, budget exhaustion, or human takeover.
- Release reservations, cancel unnecessary speculative work, reconcile uncertain side effects against external systems, and record any uncompensated effect.
- Produce the deliverable together with a concise outcome record naming what was achieved, what was not, and what remains outstanding.
- Preserve the graph lineage, artifacts, validation results, costs, timing, failures, replans, and human decisions for the declared retention period.
- Refuse to interpret an empty ready frontier as success, since it may indicate completion, a failed prerequisite, a cycle, a missing binding, or deadlock.

**Required Outputs**:

- A terminal state record with its reason code.
- A reconciliation record covering every uncertain side effect and every uncompensated effect.
- A preserved run history containing the lineage, artifacts, and decisions.

**Quality Checkpoints**:

- Exactly one terminal state is assigned, drawn from the seven declared classes.
- Every uncertain side effect is reconciled or explicitly recorded as unreconciled with its exposure stated.
- The empty-frontier condition is diagnosed to one of five causes before any terminal state is assigned.
- The preserved history is sufficient to recompute every reported metric without access to a live model context.

***

## III. Implementation Guidance for AI Agents

AI agents implementing Plan-Execute Decoupling must treat the plan as durable system state rather than as conversational content, must separate the authority to propose work from the authority to execute it, and must make every state transition attributable to a named component. The following guidance translates the operational framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Agent**: Owns run admission, freezes the contract, classifies side effects, and holds the budget limits. Refuses admission when the contract is not evaluable, and owns Phase 1.
2. **Planner Agent**: Proposes tasks, bindings, dependencies, and acceptance conditions within the registered catalogue. Holds no execution authority, and owns Phase 2.
3. **Static Validator Agent**: Rejects malformed or unsafe plans before execution and owns Phase 3. Its pass verdict is a precondition for any dispatch.
4. **Scheduler Agent**: Computes the ready frontier, applies priority ordering, and enforces concurrency and quota limits. Owns Step 4.1 and Step 4.3 and cannot alter task definitions.
5. **Executor Worker**: Invokes exactly one bound operation per attempt under a timeout and records the raw outcome. Holds no authority to declare success, and owns Step 5.1.
6. **Postcondition Validator**: Applies the seven validation checks, classifies the attempt, and publishes artifacts. It is the sole author of validated terminal states, and owns Step 5.2.
7. **Joiner Controller**: Decides continue, repair, replan, escalate, or finish, and is the sole component permitted to create or approve a new plan generation. Owns Phase 6 and Step 7.1.
8. **Verifier Agent**: Re-evaluates acceptance criteria against evidence independently of the producing tasks, and owns Step 7.2.
9. **Recorder**: Writes the append-only event log and materialises the run, plan, task, attempt, artifact, binding, and resource views. Owns no decisions and blocks none.

**Workflow Execution Pattern**:

```
STATE: Phase_4_Frontier_Scheduling
ACTIONS:
  1. Compute ready set from validated predecessor states
  2. Verify placeholder bindings, freshness, and authorization
  3. Apply concurrency group and quota constraints
  4. Dispatch selected tasks with idempotency keys
VALIDATION:
  - all_readiness_conditions_met == TRUE
  - binding_source == VALIDATED_ARTIFACT_STORE
  - concurrency_group_conflict == FALSE
  - provider_utilization <= 0.50
TRANSITIONS:
  IF ready_set_non_empty AND validations_pass THEN next_state = Phase_5_Execution
  IF ready_set_empty AND required_tasks_incomplete THEN next_state = Phase_6_Invalidation
  IF ready_set_empty AND required_tasks_complete THEN next_state = Phase_7_Join
  ELSE next_state = Phase_4_Error_Handling
```

**Task State Machine**:

```
PLANNED    -> BLOCKED      (required placeholder unresolved)
BLOCKED    -> READY        (all seven readiness conditions satisfied)
READY      -> DISPATCHED   (inputs bound, idempotency key attached)
DISPATCHED -> OBSERVED     (executor recorded response or error)
OBSERVED   -> VALIDATED    (postcondition validator accepted, artifact published)
OBSERVED   -> RETRYABLE    (transient class, attempts remaining <= 2)
OBSERVED   -> UNCERTAIN    (side effect outcome unknown, reconciliation required)
OBSERVED   -> FAILED       (permanent, policy denial, or retries exhausted)
ANY        -> SUPERSEDED   (new plan generation invalidated this occurrence)
ANY        -> CANCELLED    (gate resolved against a speculative task)
```

**Two-Phase Action Pattern**:

1. **Plan**: Emit the typed task set, the placeholder inventory, and the dependency graph without invoking any operation.
2. **Validate**: Run all ten static check classes and obtain approval while the plan is still cheap to change and no external effect exists.
3. **Execute**: Dispatch only from the ready frontier, and only after the plan generation is frozen with a recomputable graph hash.

**Approval Gate**: Human authorisation is required before dispatch whenever the plan contains an irreversible action, an approval-gated action, or a single task whose projected cost exceeds 5% of the run budget. The approval binds to the graph hash, and any subsequent generation invalidates it and requires renewed authorisation for the affected tasks.

**Context Management Requirements**:

- Store the plan, the artifacts, and the bindings outside conversational memory, and treat any in-context restatement as a convenience copy that never overrides the versioned graph.
- Supply each worker only the bound inputs its task declares, rather than the accumulated observation history, since context accumulation is the cost the pattern exists to remove.
- Supply the synthesizer the contract, the accepted plan, and the relevant validated artifacts, and withhold raw logs by default.
- Checkpoint artifacts for any task whose expected duration exceeds 60 seconds, so that a crash preserves accepted work and graph state.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract Evaluability (After Phase 1)**

- **Automated Check**: All thirteen contract fields set or covered by an authorised obtaining task; all seven budget limits numeric; every anticipated action carries a side-effect class.
- **Agent Action on Pass**: Proceed to plan generation.
- **Agent Action on Failure**: Refuse admission and return the unset fields.
- **Human Review Trigger**: Any run whose risk class is high or which contains an irreversible action class.

**Checkpoint 2: Plan Well-Formedness (After Phase 2)**

- **Automated Check**: 100% of tasks reference registered operations; 100% of required placeholders name a producer task and field; graph is acyclic; concurrency groups assigned to all side-effecting tasks.
- **Agent Action on Pass**: Proceed to static validation.
- **Agent Action on Failure**: Return the defect list to the planner with the failing tasks named, without executing any task.
- **Human Review Trigger**: More than 20% of tasks fail well-formedness on the first generation.

**Checkpoint 3: Static Validation and Approval (After Phase 3)**

- **Automated Check**: All ten static check classes return pass; every acceptance criterion traces to a producing task; every irreversible task carries an approval bound to the current graph hash.
- **Agent Action on Pass**: Freeze the generation and begin scheduling.
- **Agent Action on Failure**: Halt before any dispatch, since a plan that fails static validation is never partially executed.
- **Human Review Trigger**: Any plan containing an irreversible action, or a projected cost exceeding the run budget.

**Checkpoint 4: Binding Integrity (Before Each Dispatch)**

- **Automated Check**: Binding source is the validated artifact store; artifact within its freshness window; exact type match; authorisation current; idempotency key present for side effects.
- **Agent Action on Pass**: Dispatch the attempt.
- **Agent Action on Failure**: Block the task, mark the placeholder stale or unauthorised, and route to local repair.
- **Human Review Trigger**: Any unauthorised binding attempt, which halts the run pending review.

**Checkpoint 5: Result Admissibility (After Each Attempt)**

- **Automated Check**: All seven validation checks pass; artifact carries hash and provenance; classification assigned from the six declared classes.
- **Agent Action on Pass**: Publish the artifact and recompute the affected frontier.
- **Agent Action on Failure**: Classify and route to local repair, then to invalidation handling where repair is exhausted.
- **Human Review Trigger**: Any uncertain side effect against an irreversible operation.

**Checkpoint 6: Replan Admissibility (Before Each New Generation)**

- **Automated Check**: Trigger attributable to one of eight classes; changed-task share at or below 40%; generation count below 5; no repeated equivalent signature.
- **Agent Action on Pass**: Create the new generation and re-run static validation.
- **Agent Action on Failure**: Escalate or terminate safely rather than generating another graph.
- **Human Review Trigger**: The fourth generation in a single run, ahead of the hard limit at five.

**Checkpoint 7: Release Verification (After Phase 7)**

- **Automated Check**: 100% of acceptance criteria re-evaluated; every material claim carries evidence; every uncertain side effect reconciled or recorded; exactly one terminal state assigned.
- **Agent Action on Pass**: Deliver the artifact and close the run.
- **Agent Action on Failure**: Assign verified partial completion or compensated failure rather than success, and report the failing criteria.
- **Human Review Trigger**: Any uncompensated irreversible effect, or any criterion that failed verification after passing task-level validation.

**Plan Acceptance Rubric**:

| Dimension | Weight | Pass anchor at 3 of 5 |
| :-- | :-- | :-- |
| Operation registration and type agreement | 25% | Every task names a registered operation with matching input and output types |
| Binding explicitness and lineage | 20% | Every required input resolves to a named producer field with a declared freshness window |
| Dependency and concurrency safety | 20% | Graph is acyclic, join semantics declared, no shared-resource conflict inside a concurrency group |
| Validator and failure policy coverage | 15% | Every task carries a validator, a retry class, and a side-effect policy |
| Success reachability | 12% | Every acceptance criterion traces to at least one producing task |
| Budget and latency plausibility | 8% | Predicted cost and critical path fall within the contract limits |

The aggregate pass threshold is 4.0 of 5.0 with no dimension below 3.0. A plan scoring below the aggregate threshold returns to the planner; a plan with any dimension below 3.0 is rejected regardless of its aggregate score.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
TRIGGER:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
FAIL_ACTION:
ESCALATION_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Planner Defects**

- **Symptoms**: Nonexistent tools, missing dependencies, cycles, type mismatches, impossible preconditions, unsafe concurrency, omitted success criteria, or hallucinated values presented as bindings.
- **Diagnostic Steps**: Run the ten static check classes and attribute each defect to the planner rather than to the catalogue or the executor; count defects per planned task.
- **Resolution Protocol**: Option A, return the named defects to the planner for a corrected generation without executing any task. Option B, tighten the structured plan schema so that the defect class becomes unrepresentable. Option C, substitute a domain-authored plan template where the same defect class recurs across runs.
- **Escalation Trigger**: Two corrected generations that still fail static validation escalate to human plan authoring; a planner defect rate above 10% of planned tasks triggers a planner or prompt review.

**Error Type 2: Binding Errors**

- **Symptoms**: A required output is missing, ambiguous, stale, wrongly typed, unauthorised for the consumer, or semantically invalid.
- **Diagnostic Steps**: Identify whether the producer failed, the freshness window expired, the authorisation scope changed, or the schema drifted; check whether any coercion was attempted.
- **Resolution Protocol**: Option A, repair the producer task and rebind. Option B, repair the binding expression where the producer output is valid but the reference is wrong. Option C, replace the smallest subgraph containing producer and consumer.
- **Escalation Trigger**: Any unauthorised binding halts the run immediately; a stale-binding rate above 1% of bindings triggers a freshness-window review. Coercion is never an admissible resolution.

**Error Type 3: Tool Failures**

- **Symptoms**: Rate limits, network timeouts, invalid requests, permission denials, unavailable capabilities, malformed responses, and uncertain side effects.
- **Diagnostic Steps**: Classify the cause before selecting a recovery policy, since these classes carry different policies; determine side-effect certainty before any retry.
- **Resolution Protocol**: Option A, bounded retry with backoff for declared transient classes. Option B, substitute a registered equivalent operation where the graph remains sound. Option C, reconcile external state by reading the target system, then decide retry or failure.
- **Escalation Trigger**: 2 retries exhausted escalates to local repair, and a third failure escalates to invalidation handling. An uncertain side effect against an irreversible operation escalates to human review without retry.

**Error Type 4: Stale-Plan Failures**

- **Symptoms**: Observed state invalidates one or more planning assumptions; a task precondition no longer holds; an observed side effect diverges from its prediction.
- **Diagnostic Steps**: Identify the falsified assumption in the assumption register and compute its descendant set; separate verified work from work that depended on the assumption.
- **Resolution Protocol**: Option A, invalidate only the affected descendants and replan that subgraph. Option B, insert an observation task that re-establishes the assumption before dependent work resumes. Option C, terminate with verified partial completion where the assumption is unrecoverable.
- **Escalation Trigger**: A falsified assumption invalidating more than 40% of remaining tasks requires renewed approval; the fifth generation terminates the run.

**Error Type 5: Join Failures**

- **Symptoms**: Incomplete fan-in, contradictory artifacts, duplicated evidence, incompatible units or versions, or a final objective still unsupported by the arrived artifacts.
- **Diagnostic Steps**: Identify which acceptance criterion failed and which producer can resolve it, rather than regenerating the entire answer.
- **Resolution Protocol**: Option A, dispatch a targeted producer task for the missing evidence. Option B, add a normalisation task where units or versions conflict. Option C, disclose the contradiction in the deliverable and mark the criterion as partially satisfied.
- **Escalation Trigger**: Two join attempts failing on the same criterion escalate to human adjudication; a contradiction on a hard constraint is never resolved by disclosure and halts delivery.

**Error Type 6: Parallel Execution Failures**

- **Symptoms**: Resource saturation, rate-limit amplification, conflicting writes, races over mutable state, and correlated provider outages.
- **Diagnostic Steps**: Compare active width against ready-frontier width and provider utilisation against quota; identify whether concurrency groups were assigned and honoured.
- **Resolution Protocol**: Option A, apply backpressure and reduce concurrency to the measured safe width. Option B, introduce per-resource locks and bulkhead limits for the conflicting group. Option C, fail the affected siblings partially while preserving every successful sibling.
- **Escalation Trigger**: Provider utilisation above 50% of quota for more than 2 consecutive scheduling cycles reduces concurrency automatically; a conflicting write to a shared resource halts the group and requires plan correction.

**Error Type 7: Speculation Failures**

- **Symptoms**: Branches executed before a gate decided whether they were needed; side effects produced by work later discarded.
- **Diagnostic Steps**: Measure wasted cost and task time attributable to speculation, and identify whether the speculative tasks were read-only and cancellable.
- **Resolution Protocol**: Option A, restrict speculation to read-only or safely cancellable tasks. Option B, defer speculation until the gate resolves where expected waste exceeds expected latency benefit. Option C, disable speculation for the task class entirely.
- **Escalation Trigger**: Speculative cost above 10% of run cost cancels the lowest-value speculative tasks; any speculative side effect against a non-cancellable operation halts speculation for the run.

**Error Type 8: Security and Trust-Boundary Failures**

- **Symptoms**: Untrusted tool output changes the plan, supplies executable instructions, or crosses an authorisation boundary; a worker resolves an input from another worker's conversational memory.
- **Diagnostic Steps**: Trace the provenance of the plan change and of every binding; confirm that only the controller authored the generation and that only registered tools executed.
- **Resolution Protocol**: Option A, treat retrieved content strictly as data and re-run the affected validation. Option B, revoke the affected authorisation scope and rebind from the artifact store. Option C, terminate the run and preserve the evidence where a boundary was crossed.
- **Escalation Trigger**: Any plan modification not authored by the controller halts the run immediately; this error class is never resolved by retry.

**Troubleshooting Decision Tree**:

```
RUN NOT PROGRESSING OR NOT SUCCEEDING
├─ NO READY TASK
│   ├─ Required tasks incomplete → Diagnose blocked-graph cause
│   │   ├─ Unresolved required placeholder → Repair producer or rebind
│   │   ├─ Cycle detected at runtime → HALT, static validation defect
│   │   ├─ Authorization expired → Re-authorize or escalate
│   │   └─ Resource lock never released → Release, then reschedule
│   └─ All required tasks validated → Proceed to join and synthesis
├─ TASK FAILING
│   ├─ Transient class, attempts <= 2 → Bounded retry with backoff
│   ├─ Uncertain side effect → Reconcile external state before any retry
│   ├─ Permanent or policy denial → Local repair or registered substitute
│   └─ Repair exhausted → Escalate to invalidation handling
├─ RESULT REJECTED BY VALIDATOR
│   ├─ Schema pass, semantics fail → Treat as failure, do not bind
│   ├─ Freshness expired → Mark stale, block dependents, replan subgraph
│   └─ Evidence quality below standard → Dispatch targeted producer task
├─ REPLAN LOOPING
│   ├─ Equivalent signature repeated → STOP identical retries, escalate
│   ├─ Generation count at limit → Terminate with compensated failure
│   └─ Changed-task share above 40% → Require renewed approval
└─ PARALLELISM NOT REALIZED
    ├─ Active width far below ready width → Inspect quotas, locks, scheduler
    ├─ Provider saturation → Apply backpressure, reduce concurrency
    └─ Hidden dependency detected → Correct concurrency groups in a new generation
```

**Prohibited Recovery Behaviours**:

- Coercing a mismatched or stale value merely to keep the graph moving.
- Retrying an uncertain side effect before reading the external system.
- Allowing tool output to rewrite the graph directly rather than triggering a controlled replanning decision.
- Treating strict structured output as semantic validation of truth, authorisation, freshness, or safety.
- Erasing superseded plans or failed attempts, which destroys the history that robustness metrics and incident diagnosis require.
- Improving wall-clock speed by weakening validation or by exceeding provider quotas.

### D. Observability, Metrics, and Robustness Analysis

**Logging architecture**: AI agents must write an append-only event log and materialise run, plan, task, attempt, artifact, binding, and resource views from it. Every event carries a schema version, an event identifier, an event type, a wall-clock timestamp, a monotonic sequence number, the run identifier, the plan-generation identifier, the task and attempt identifiers where applicable, the actor or worker identifier, trace and span identifiers, parent and causation identifiers, and the source-system version. Decisions and evidence references are preserved; hidden chain-of-thought is not stored.

**Event envelope template**:

```
SCHEMA_VERSION:
EVENT_ID:
EVENT_TYPE:
TIMESTAMP_WALL:
SEQUENCE_MONOTONIC:
RUN_ID:
PLAN_GENERATION_ID:
TASK_ID:
ATTEMPT_ID:
ACTOR_ID:
TRACE_ID:
SPAN_ID:
PARENT_ID:
CAUSATION_ID:
SOURCE_VERSION:
REASON_CODE:
EVIDENCE_REFS:
```

**Record inventory by level**:

- **Run level**: Objective and task class, input and dataset versions, risk tier, acceptance-test version, constraints, evidence standard, authorisation scope, allowed operations, suitability decision, chosen planning horizon, planner and executor and synthesizer and validator versions, prompt or policy versions, sampling settings, environment, deadlines, budgets, concurrency limits, experiment cohort, terminal status, terminal reason, final artifacts, and later adjudication.
- **Plan level**: Generation number, parent generation, creation trigger, planner request and structured response references, task and edge counts, graph hash, maximum width, predicted critical path, expected latency and tokens and cost, assumptions, candidate alternatives, chosen plan, static-validator version, validation findings, approval, created and preserved and superseded and invalidated tasks, and replan scope.
- **Task level**: Definition and occurrence identifiers, plan generation, registered operation and version, normalised purpose, input and output schema versions, dependency identifiers, placeholder references, readiness guards, critical-path rank, resource and capability needs, sensitivity class, permissions, timeout, retry policy, side-effect class, idempotency and compensation policy, validator, state, state version, and terminal reason.
- **Placeholder and binding level**: Placeholder identifier, consumer input field, producer task and output field, expected and observed type, required or optional status, artifact identifier and hash, provenance, creation and resolution times, freshness, authorisation check, validation result, and any coercion or repair. Silent coercion is prohibited, and any coercion is separately counted.
- **Scheduling level**: Ready set or a stable reference to it, blocked tasks with reasons, priority components, critical-path estimate, available capacity, tool and tenant quotas, resource locks, concurrency group, selected tasks, deferred tasks, cancellation choices, scheduler version, and decision latency. These fields reveal whether graph parallelism became real execution.
- **Attempt level**: Queued, dispatched, acknowledged, started, and finished times; queue, binding, tool, validation, and total latency; bound-input and output hashes; executor, model, and tool versions; token counts; model and tool call counts; monetary and infrastructure cost; retries hidden inside the tool where known; timeout; status code; error class; side-effect certainty; validator observations; artifact references; and postcondition verdict.
- **Repair and replan level**: Trigger, detection source, violated assumption or acceptance criterion, affected subgraph, failure signature, previous and new graph hashes, preserved work, invalidated and speculative work, completed side effects, compensation, planner latency and cost, human decision, remaining budgets, and recovery outcome.
- **Join and synthesis level**: Required and arrived branches, missing or conflicting artifacts, coverage by acceptance criterion, evidence-source independence, join verdict, synthesis inputs, final validation by criterion, corrections, artifact lineage, human rating, and later-discovered errors.

**Data minimisation rules**: Redact secrets before export, keep high-cardinality identifiers in traces rather than in metric labels, encrypt sensitive artifacts, restrict access, and set retention periods. Log concise reason codes, structured outcomes, and hashes or secure references instead of unrestricted prompts, private reasoning, personal data, or raw tool payloads. Sampling below 100% is permitted only for read-only attempts; every side-effecting attempt is logged in full.

**Efficacy metrics**:

- **End-to-end success rate**: Runs passing every top-level acceptance test divided by admitted runs. Plan-generation success, valid-plan rate, verified task success, safe-abstention, escalation, and uncompensated-failure rates are reported separately, so that a planner cannot appear successful when execution fails. Uncompensated failure target: at or below 0.5%, above which the failure policy is revised.
- **First-plan yield**: Successful runs completed without a new generation divided by runs that began execution. Target: at or above 60%; a lower value indicates planning defects or excessive environment volatility and triggers a plan-validity review.
- **Replan rate**: Runs with at least one replan divided by executed runs, supplemented by generations per run, tasks changed per replan, replan recovery yield, and replan cost. A low rate may indicate excellent planning or a controller that fails to adapt, so stale-plan failures are inspected whenever the rate falls below 5%.
- **Plan validity**: Share of first plans with registered tools, complete bindings, acyclic dependencies, valid schemas, satisfiable hard constraints, safe concurrency, and reachable success, with each defect class tracked per planned task. Target: at or above 90%, below which the planner or its schema is revised.
- **Execution adherence**: Completed task occurrences whose operation, inputs, and dependencies match the accepted generation divided by completed task occurrences, counting authorised replans as changes rather than violations. Target: at or above 99%; any shortfall is investigated as a control-plane defect.

**Execution and efficiency metrics**:

- **Binding reliability**: Placeholder resolution success at or above 98%, type mismatch rate at or below 1%, stale-binding rate at or below 1%, unauthorised-binding rate at 0, semantic validation failure tracked per producer, and time from producer validation to dependent readiness. These metrics test the mechanism that makes placeholder-based plans usable, and a breach of the unauthorised-binding target halts the run.
- **Parallelism realised**: Tasks executed concurrently divided by tasks eligible to run concurrently, reported with maximum and average ready-frontier width, maximum and average active width, critical-path duration, total task work, scheduler delay, resource saturation, and join wait. Target: at or above 60%; high graph width with low active width indicates scheduler, quota, resource, or hidden-dependency problems.
- **Critical-path efficiency**: Observed makespan compared with the duration implied by the executed critical path after accounting for unavoidable external waits. A ratio above 2.0 triggers a scheduling review.
- **Latency decomposition**: Planning, static validation, approval, queue, binding, execution, join, replanning, synthesis, and final-validation time reported separately, with end-to-end median and tail latency, time to first useful artifact, and speedup at matched success and quality. A concurrency benefit claimed alongside reduced quality or omitted checks is not admissible.
- **Cost and token efficiency**: Planner, replanner, executor-model, synthesizer, validator, and tool costs reported separately, with input and output tokens, model calls, tool calls, cache hits, cost per admitted run, and cost per verified success. Failed, cancelled, and speculative tasks are counted, since excluding them overstates efficiency.
- **Wasted-work rate**: Cost or task time spent on outputs later invalidated, superseded, duplicated, or cancelled divided by total cost or task time, segmented by planner defect, stale assumption, speculation, late failure, and cancellation. Target: at or below 15%. The pattern can lower model tokens while increasing unnecessary tool work, so both dimensions are reported together.

**Recovery and robustness metrics**:

- **Failure recovery**: Retry rate, local-repair yield, replan recovery yield at or above 70%, time to recovery, preserved-work share, repeated-failure rate, uncertain-side-effect incidents, compensation success, and escalation timeliness, each attributed to planning, binding, execution, validation, environment, policy, or synthesis.
- **Quality and evidence robustness**: Acceptance by criterion, factual or test accuracy, evidence coverage, contradiction rate, source independence, later correction, and human rating. A run that completes cheaply while propagating one bad early artifact is recorded as a robustness failure regardless of its cost profile.
- **Run-to-run robustness**: Repeated runs over identical tasks with controlled model settings, tracking success variance, plan-graph variation, task-count variation, dependency-edge variation, cost and latency dispersion, output agreement, and worst-decile performance. The pattern may reduce runtime reasoning variance while planner nondeterminism still produces materially different graphs, so graph variation is reported separately from outcome variation.

**Perturbation test set**: Paraphrase the objective without changing its meaning; add irrelevant context; remove an optional source; slow, rate-limit, or fail one tool; return malformed or semantically wrong data; change task ordering; reduce concurrency; expire a credential; alter one assumption; inject an uncertain side effect; and force a join contradiction. A robust implementation preserves valid work, blocks unsafe descendants, creates a bounded repair or replan, and fails safely when recovery is impossible. Any perturbation producing a silently wrong deliverable rather than a safe failure is a release-blocking defect.

**Comparative evaluation design**: Measure the whole system against direct execution, a fixed workflow, an interleaved controller, sequential decoupling, and graph decoupling, holding tools, models, acceptance tests, and budgets constant where possible and evaluating both clean and fault-injected conditions. Report distributions, tail percentiles, confidence intervals, and results by task class, since a single mean or a best run is not sufficient evidence for adoption.

***

## IV. Domain-Agnostic Application Guidance

The framework generalises across any domain in which work decomposes into typed operations with statable dependencies and verifiable outputs. The three worked applications below span knowledge research, software change management, and regulated document preparation, and the substrate guidance that follows applies to all of them.

**Multi-source research and synthesis**: A research agent compares six programmes across eligibility, deadlines, benefits, evidence quality, and fit, under a contract requiring primary citations for every material claim. The pattern suits the work because each programme can be researched independently, all researchers share a stable output contract, and synthesis waits on a predictable join. The planner creates six read-only research tasks that fan out concurrently, each returning named fields for official source, programme version, eligibility, deadline, benefits, caveats, and unresolved questions. Their outputs bind into a normalisation task that reconciles units and dates and an evidence auditor that checks source authority and contradiction, both running in parallel once all six artifacts arrive, with a final synthesizer depending on both. When one source times out, the executor classifies a transient read failure and performs the bounded retry; the second attempt returns an archived copy whose date is stale, so semantic validation fails even though the response schema passes. The joiner creates a new generation that preserves the other five validated artifacts and replaces only the failed branch with an official-document search and a clarification field, repeating no successful research call. Reported metrics include fan-out width, critical-path time, source-validation failure, preserved work, replan cost, cost per accepted programme record, and latency saved against sequential and interleaved baselines.

**Software change with parallel analysis and gated execution**: A coding system upgrades a shared library across a repository under a contract permitting read and test operations automatically but requiring human approval before modifying release configuration. The planner creates independent tasks to inspect call sites, dependency metadata, tests, and migration notes, whose outputs bind into a change-design task producing a list of affected files and expected behaviour; edit tasks then fan out only across nonoverlapping files, followed by a join running formatting, unit tests, integration tests, and a security check. Static validation finds two proposed edit tasks targeting the same configuration file and rejects the graph before execution, which the planner corrects by merging them into one ordered task, recorded as a planner defect rather than a tool failure. After the corrected graph runs, unit tests pass but the integration task reports a schema mismatch caused by an undocumented interface change, and the postcondition validator blocks the release branch. The replanner receives the validated edits, the failing test artifact, the current repository state, and the remaining budget, preserves compatible edits, adds one adapter task and a targeted test, and supersedes only the affected descendants. The run then pauses at the approval task so that approval binds as an explicit artifact before configuration changes, and a timeout after the final publish call is treated as an uncertain side effect, so the executor reads the package registry before considering any retry. Reported metrics include first-plan validity, conflict detection before execution, preserved-work share, test recovery yield, approval wait, critical-path time, and duplicate-publish incidents.

**Evidence and compliance pipeline for a regulated submission**: A team prepares an application whose narrative sections depend on a common requirements register and verified organisational facts. The planner first creates two gate tasks that retrieve the current call and extract a versioned requirement register, with a human validating ambiguous eligibility language, and only then fans out into problem framing, technical approach, milestones, budget justification, team evidence, and risk analysis. Each drafting task consumes the same validated requirements artifact plus only the evidence relevant to its section; a citation verifier and a cross-section consistency checker run after the drafts arrive, and a constraint task checks word limits, required headings, budget totals, dates, and claim provenance, with final assembly depending on all three checks. When a budget assumption changes during execution, the controller marks budget-dependent placeholders stale, blocks the budget and milestone descendants, and creates a new generation that preserves unaffected narrative and team-evidence artifacts, reruns the allocation solver, updates the milestones affected by staffing, and repeats the cross-section and compliance checks rather than regenerating every section or concealing the change. The finished package includes the verified submission and an audit record linking each requirement to a section, each claim to evidence, each numerical value to its producing artifact, and each revision to its trigger. Reported metrics include requirement coverage, first-pass compliance, stale-binding detections, sections preserved per replan, citation-validation yield, human intervention, total cost, and verified completion before the deadline.

**Further domain families**: The same structure transfers to data-enrichment pipelines, where each record class is an independent fan-out branch joined by a reconciliation task; to batch interface operations, where idempotency keys and reconciliation dominate the failure policy; to codebase and corpus analysis, where read-only parallelism is wide and the join is a synthesis over independent findings; and to multi-agent service composition, where each specialist agent is a registered operation with a typed output contract rather than a conversational participant.

**Implementation substrate adaptation**: The pattern is substrate-independent, but each substrate class supplies a different fraction of the required machinery, and the remainder must be built.

- **Graph orchestration libraries**: Published planning examples in this class cover a sequential plan-and-execute agent with a replanning step, a blueprint agent with planner, worker, and solver roles, and a streamed directed acyclic graph with eager task scheduling and a joiner [16][20]. These are architectural starting points supplying state machines and scheduling; they do not supply production authorisation, idempotency, semantic validation, observability, or evaluation, all of which remain the implementer's responsibility.
- **Role-based crew frameworks**: Frameworks exposing planning as an optional capability typically send crew information to a planning role before each iteration and add the resulting plan to task descriptions [21]. That separates a planning role from task agents, but planning before every iteration is closer to repeated planning than to decoupling. To implement the pattern on such a substrate, persist a versioned plan, execute its unchanged ready frontier, and call the planner again only at a declared join or on invalidation.
- **Multi-agent conversation frameworks**: Task-decomposition guidance in this class typically asks a planner agent, used as a tool, to propose a feasible plan of three to five subtasks, revise a defective plan, or analyse an execution error [22]. Graph-flow facilities in the same frameworks represent sequential chains, parallel fan-outs, conditional branches, joins, and loops with exit conditions, making them a suitable execution substrate for an already accepted plan [23]. Graph syntax does not prove semantic independence or safe side effects, so static validation remains mandatory.
- **Function-calling and tool-use interfaces**: These supply the typed invocation boundary and nothing above it. A model emits calls, application code executes them, tool outputs return to the model, and the model may request more calls or answer; applications must handle zero, one, or multiple calls per response, and a response containing several calls does not relieve the application of dependency and validation responsibility [18]. Parallel tool use is an application policy that such interfaces commonly permit and allow to be disabled [19]. The pattern adds a persistent graph, explicit dependencies, immutable bindings, scheduling, plan versions, and bounded replanning around those primitives.
- **Predefined code paths**: For a simpler fixed problem, a deterministic workflow in which models and tools follow predefined code paths is preferable to an autonomous planner, and complexity should be added only where it demonstrably improves outcomes [24]. A mature system may use a language model to author or select a graph while deterministic code validates and executes it.

**Scale adaptation**:

- **Small scope** (fewer than 8 tasks): Retain the contract, the registered catalogue, explicit placeholders, static validation, and postcondition validation; collapse the scheduler to a simple readiness sweep; cap generations at 2.
- **Medium scope** (8 to 40 tasks): Apply the full framework with concurrency groups, priority ordering, and per-tool quotas; report parallelism realised and wasted work as standing metrics.
- **Large scope** (more than 40 tasks): Introduce hierarchical decomposition so that no single generation exceeds 40 tasks, add durable orchestration for task state and long waits, and treat scheduler decisions as first-class logged events subject to their own review.

***

## V. Limitations and Considerations

**Efficiency claims are conditional, not guaranteed**: Published gains for both structural variants are reported as maxima on selected benchmarks, and real gains depend on graph width, critical-path length, tool latency, model pricing, cache behaviour, rate limits, retries, and replanning volume. Adopting the pattern from published figures alone risks paying the machinery cost without receiving the benefit. Mitigation: require a local comparison against a direct call, a fixed workflow, and an interleaved controller at matched quality and safety before adoption, and report cost per verified success rather than planner token savings.

**Token savings can be offset by tool waste**: The pattern reduces observation-conditioned model calls, but a plan generated before observation can dispatch work that later proves unnecessary. Mitigation: measure wasted-work rate alongside token cost, cap speculative cost at 10% of run cost, and select the receding-horizon variant whenever more than 30% of tasks are expected to change on observation.

**Planner nondeterminism produces graph variance**: Reducing runtime reasoning does not reduce planning variance, and two runs of the same task may produce materially different graphs with different costs and failure profiles. Mitigation: measure plan-graph variation, task-count variation, and dependency-edge variation across repeated runs, and constrain the planner with a registered catalogue, a structured plan schema, and domain-authored templates where variance is material.

**Schema conformance is not semantic validation**: Strict structured output constrains the representation of a plan or a result; it does not establish factual correctness, feasibility, authorisation, freshness, or safety [17]. Mitigation: require postcondition validation on every result, and treat a schema-conforming response that fails a semantic check as a failure rather than a success.

**Concurrency is a safety decision**: Tasks appearing in the same graph layer may contend for a rate limit, modify the same record, rely on an undeclared assumption, expose sensitive data to different actors, or produce incompatible side effects. Mitigation: assign concurrency groups at plan time, enforce per-resource locks and quota shares at dispatch, and treat a conflicting write as a plan defect requiring a new generation rather than a runtime exception to absorb.

**Uncertain side effects cannot be resolved by retry**: A timeout never proves that an external action did not occur, and a retry issued without reconciliation can duplicate a consequential effect. Mitigation: classify side-effect certainty on every attempt, require an external state read before any retry of an uncertain effect, and attach idempotency keys to every retriable side-effecting dispatch.

**Untrusted content is a plan-integrity risk**: Retrieved tool output may attempt to change the plan, supply executable instructions, or cross an authorisation boundary. Mitigation: treat retrieved content strictly as data, permit only the controller to author or approve a generation, permit only registered operations to execute, and halt the run on any plan modification not attributable to the controller.

**Auditability depends on retained history**: Robustness metrics, incident diagnosis, and later adjudication all require superseded plans and failed attempts. Deleting them for storage economy destroys the evidence base. Mitigation: retain graph lineage, artifacts, validation results, and decisions for the declared retention period, applying redaction and encryption rather than deletion.

**Structural validity is not method quality**: A well-formed graph can encode a poor method, and every quality threshold in this guide detects malformation rather than unsoundness. Mitigation: pair structural validation with independent verification against evidence at Step 7.2, and treat verification failures that follow task-level validation passes as a signal that the acceptance criteria themselves require revision.

***

## VI. Conclusion and Summary

Plan-Execute Decoupling is a commitment about when reasoning occurs, not a claim that a first plan is correct. Its benefit comes from removing reasoning turns that add no information, exposing dependencies that permit concurrency, and making the plan an auditable artifact rather than a conversational by-product. Its risk comes from the same commitment: a plan formed before observation can be wrong, and a system that cannot detect that condition will execute confidently into an invalid state.

The framework in this guide manages that trade by fixing three boundaries. The plan is frozen as an immutable generation and is never mutated in place. Bindings resolve only from validated artifacts, immediately before dispatch, under freshness and authorisation checks. Planning is re-entered only on one of eight declared invalidation triggers, within a generation limit, a changed-task limit, and a repeated-signature limit. Every other decision in the loop is deterministic control-plane work that a planning call cannot improve.

**Minimum production-readiness standard**: An implementation is ready for production use when it begins from an instrumented baseline over a representative task corpus, measuring direct, fixed-workflow, and interleaved-agent success, quality, model calls, tokens, tool calls, latency, cost, retries, and failures, and introduces the pattern only where that baseline reveals repeated reasoning or unused parallelism. The first implementation supports a small registered operation catalogue, a typed graph, explicit placeholders, static validation, bounded ready-frontier execution, immutable artifacts, semantic postconditions, one safe local retry class, one explicit replan trigger, and human escalation. Streamed planning, speculation, learned scheduling, multi-agent execution, and automatic compensation are added only after the simpler system passes repeated and fault-injected evaluation. Before deployment, the implementation demonstrates that malformed plans cannot invoke unregistered operations, that unresolved placeholders cannot dispatch, that cycles and unsafe concurrency are rejected, that permissions are checked at both planning and execution time, that retries cannot duplicate protected side effects, that crashes preserve accepted artifacts and graph state, that replans retain completed effects, that repeated-state loops stop, and that every terminal status is auditable.

**Key Success Factors**:

- **Evaluable contract before planning**: A graph is useful only when its terminal state can be verified against criteria fixed before the first task was proposed.
- **Typed, versioned plan representation**: Tasks, dependencies, placeholders, outputs, validators, and failure policies are machine-checkable, and a plan edit is a new generation rather than an in-place change.
- **Explicit immutable binding**: Downstream inputs resolve only from validated producer artifacts with lineage, never from another worker's conversational memory and never through silent coercion.
- **Validation before consequence**: The whole graph is checked for unknown operations, cycles, unsafe concurrency, impossible bindings, missing approvals, and unreachable success before any consequential execution.
- **Bounded recovery ladder**: Retry, local repair, replan, compensation, escalation, and safe stop solve different failure classes, and each carries a numeric bound and a stated consequence at breach.
- **Measured adoption**: The pattern is compared with simpler baselines at matched quality and safety on full cost, tail latency, wasted work, and fault recovery, not on planner token savings alone.

The practical operating rule is compact: plan enough to expose reusable structure and parallel work, execute only what current validated bindings authorise, observe results without continuously reopening reasoning, and replan only when evidence changes what the remaining graph must do. Applied with the bounds specified here, the pattern preserves its efficiency advantage without turning an upfront plan into an unmonitored commitment.

***

## VII. References and Further Reading

This guide is derived from a single originating prose document and is intended to be read alongside the sibling guides in this corpus that cover neighbouring planning patterns. The external references listed below are transcribed from that originating prose guide and have not been independently re-verified during conversion; a reader relying on any figure or claim attributed to them should consult the cited source directly.

**Corpus pointers**:

1. `Plan–Execute Decoupling: An Operational Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the plan-bind-execute-verify-replan loop, the entry and exit conditions, the failure policy and robustness controls, the framework and interface implementation choices, the logging field inventory, and the metric definitions.

**Sibling guides covering adjacent patterns**:

2. `advanced_task_guides/planning/guide_MetaReasoning.md` — the pattern that selects among reasoning methods and allocates computation; sits above this pattern when a system must choose between decoupled planning, interleaved control, formal solving, simulation, retrieval, or human review.
3. `advanced_task_guides/planning/guide_HierarchicalTaskNetworkPlanning.md` — method-library planning that can generate the upfront graph this guide executes, supplying applicability conditions that a free-form planner lacks.
4. `advanced_task_guides/planning/guide_TaskManagementOrchestration.md` — the runtime substrate governing task state, scheduling, assignment, retries, handoffs, compensation, and durable progress, commonly required beneath a production implementation of this pattern.
5. `advanced_task_guides/planning/guide_WorldModelSimulationPlanning.md` — consequence prediction for costly or irreversible actions; may score candidate plans or validate a dangerous task before dispatch.
6. `advanced_task_guides/planning/guide_PlanTodoRecitation.md` — objective and work-list salience during long execution; complementary to this pattern, but never the source of truth over the versioned graph.
7. `advanced_task_guides/authoring/guide_guidewriting.md` — the house-style specification governing the structure, register, and conformance envelope of this document.

**External references transcribed from the originating prose guide**:

**Pattern definition and core idea**

8. ReWOO — https://arxiv.org/abs/2305.18323
9. LLMCompiler paper — https://arxiv.org/abs/2312.04511
10. LangGraph’s LLMCompiler implementation — https://langchain-ai.github.io/langgraph/tutorials/llm-compiler/LLMCompiler/

**Conceptual lineage and the interleaved reason-act contrast**

11. Plan-and-Solve paper — https://arxiv.org/abs/2305.04091
12. ACL publication — https://aclanthology.org/2023.acl-long.147/
13. ReAct — https://arxiv.org/abs/2210.03629
14. LLMCompiler — https://arxiv.org/pdf/2312.04511

**Selection and applicability**

15. LangChain planning agents — https://www.langchain.com/blog/planning-agents
16. LangGraph ReWOO tutorial — https://langchain-ai.github.io/langgraph/tutorials/rewoo/rewoo/

**Plan-bind-execute-verify-replan loop and typed invocation**

17. OpenAI Structured Outputs — https://developers.openai.com/api/docs/guides/structured-outputs
18. OpenAI function calling — https://developers.openai.com/api/docs/guides/function-calling
19. Anthropic tool-use guidance — https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use

**Framework and API implementation choices**

20. LangGraph plan-and-execute tutorial — https://langchain-ai.github.io/langgraph/tutorials/plan-and-execute/plan-and-execute/
21. CrewAI planning — https://docs.crewai.com/v1.15.17/en/concepts/planning
22. AutoGen task decomposition — https://microsoft.github.io/autogen/0.2/docs/topics/task_decomposition/
23. AutoGen GraphFlow — https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/graph-flow.html
24. Building Effective AI Agents — https://www.anthropic.com/engineering/building-effective-agents

