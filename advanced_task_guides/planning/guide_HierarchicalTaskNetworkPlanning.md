# Hierarchical Task Network Planning

**Status**: Beta testing

**Change logs**:

- [09/06/2026] - Initialization

***

## Executive Summary

Hierarchical Task Network planning, abbreviated HTN planning, is the task family of converting an abstract task into an executable plan by repeatedly replacing compound tasks with networks of simpler tasks until every remaining task is primitive. Unlike a checklist, an HTN model states not only what may be done but which decomposition methods are authorised, when each applies, how subtasks are ordered, and which constraints the finished plan must satisfy. This guide provides AI agents with a structured protocol for building an HTN domain model as an engineered artifact, searching that model to produce a validated primitive plan, executing the plan against verified evidence, and recovering through bounded backtracking, repair, and replanning. It specifies the design-time obligations preceding any run, the decomposition and execution loop, the taxonomy separating planning failure from execution failure, the append-only logging schema that makes runs auditable, and the metrics derived from those logs. It emphasises structured execution protocols, quality assurance checkpoints, and error handling procedures so that hierarchical planning remains disciplined procedural search rather than hierarchical prose.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Compound task**: Work described too abstractly for direct execution, such as preparing a compliant application or restoring a degraded service. It carries a stable identifier, parameters, invariants, and a completion condition, and is never executed; it is refined.

**Primitive task**: An action the executor can invoke directly. Primitive does not mean physically indivisible; it means atomic at the planner's chosen interface to a tool, person, solver, or controller.

**Operator**: The specification giving a primitive task operational semantics. Preconditions state what must hold immediately before invocation, effects state the modelled changes caused by successful execution, and annotations carry cost, duration, resources, permissions, timeout, retry policy, idempotency class, and expected outputs.

**Postcondition checker**: The evidence-producing test deciding whether an attempt actually succeeded. A returned call status is not evidence; a receipt, an accepted status, or an independent observation is evidence.

**Method**: A conditional recipe for refining one compound task, naming the task it refines, its applicability conditions, the subtasks it introduces, and the constraints among them. Several methods may refine the same task, and that multiplicity is the planner's principal source of controlled alternatives.

**Task network**: A set of task occurrences plus constraints that order tasks, bind variables, restrict resources, or require facts to hold before, during, or after parts of the network [6]. A network may be totally ordered, unordered, or partially ordered; a primitive partially ordered network still requires a valid linearisation respecting its constraints.

**Decomposition**: The replacement of one compound task occurrence with the subnetwork of an applicable method, preserving surrounding ordering and constraints. Refinement continues until an executable primitive plan exists or no permitted refinement works within declared bounds [5].

**Choice point**: The snapshot of task network, planning state, constraint store, budgets, and untried alternatives saved immediately before a method is applied. It is the unit of backtracking [7].

**Projected state**: The simulated state produced by applying modelled effects during planning [12]. **Observed state** is the state supported by environmental evidence. The two are stored separately, and divergence between them is a first-class signal.

**Domain model**: The versioned artifact holding task types, operators, methods, constraints, selection policy, and bounds. Planner quality is bounded by its coverage and correctness.

**Illustrative decomposition hierarchy**:

```
COMPOUND TASK: <top-level outcome>
├─ METHOD M1  [applicable when: <condition set A>]
│   ├─ COMPOUND SUBTASK: <capability 1>
│   │   ├─ METHOD M1a  [applicable when: primary evidence available]
│   │   │   ├─ PRIMITIVE: <retrieve primary evidence>  [operator + postcondition checker]
│   │   │   └─ PRIMITIVE: <record into register>       [idempotent]
│   │   └─ METHOD M1b  [applicable when: primary evidence absent]
│   │       └─ PRIMITIVE: <corroborate across independent sources>
│   ├─ COMPOUND SUBTASK: <capability 2>                [ordering: after capability 1]
│   └─ PRIMITIVE: <approval gate>                      [permission required; blocking]
└─ METHOD M2  [applicable when: <condition set B>; declared fallback]
    └─ PRIMITIVE: <escalate, naming the missing evidence>
```

### 1.2 Differentiation From Neighbouring Planning Patterns

**Classical goal-based planning**: A goal planner searches for any action sequence achieving a desired end condition; HTN searches only among sequences obtainable through authorised methods [9][10], which lets the hierarchy encode procedural requirements and meaningful intermediate activity. HTN completeness is therefore relative to the method library: a physically valid sequence is not an HTN solution when no allowed decomposition generates it.

**Plain sequential planning**: A flat step list is cheaper to inspect but carries no alternative methods, no recursive refinement, and no principled backtracking. It is preferable when the task is short, stable, and nearly deterministic.

**Goal decomposition**: Splitting a goal into subgoals is not HTN, which requires typed tasks, explicit methods, applicability conditions, and network constraints. Goal decomposition suits an agent needing a hierarchy before a validated model exists, and can propose candidate methods for later validation.

**Task management and orchestration**: Orchestration tracks assignments, dependencies, status, and handoffs after work is selected; HTN decides how abstract work may be refined. Production systems commonly need both.

**Constraint-satisfaction planning**: A solver assigns values or schedules under hard and soft constraints, and belongs inside an HTN method when a decomposition creates a scheduling, routing, or allocation subproblem.

**Plan and execute decoupling**: Planning before tool execution improves batching, but such a plan may be flat and need not originate in domain methods. HTN may supply it, or may interleave planning and acting when state is incomplete.

**Meta-reasoning and reflection**: Meta-reasoning selects among reasoning strategies, including whether to invoke HTN; reflection may diagnose a failed primitive or weak method but must never silently override HTN constraints.

**Scenario planning and world-model simulation**: These test a plan against uncertainty and surround HTN as robustness controls; they do not define the authorised hierarchy.

**Pattern selection matrix**:

| Pattern | Centre of gravity | Select when |
| :-- | :-- | :-- |
| **HTN planning** | Authorised decomposition of tasks | Acceptable procedure is part of the problem definition |
| **Goal-based planning** | Search over actions toward an end state | The end state is clear and procedure may emerge freely |
| **Sequential planning** | A fixed ordered step list | One stable procedure exists and failures resolve locally |
| **Goal decomposition** | Subgoal generation without typed methods | A hierarchy is needed before a validated model exists |
| **Orchestration** | Assignment, status, and handoff | Work is already selected and needs coordination |
| **Constraint satisfaction** | Feasible assignment under constraints | A subproblem is scheduling, routing, or allocation |
| **Meta-reasoning** | Strategy selection and monitoring | Several strategies compete for one request |

### 1.3 Selection Criteria and Exclusion Conditions

**Conditions favouring HTN planning**: The work spans several abstraction levels; experts can state repeatable ways to perform it; the procedure itself matters for safety, compliance, quality, or coordination; alternative procedures apply under different conditions; the same top-level task recurs so decompositions can be reused [16]; plans must remain interpretable to reviewers; or an agent must stay inside an auditable procedural envelope. HTN also suits multi-agent settings where compound tasks map onto roles [17].

**Conditions excluding HTN planning**: The task is short, linear, and representable by a validated checklist, where model and search machinery add failure modes without meaningful choice. The environment changes faster than decomposition and validation can run, so a reactive controller must own urgent response while HTN sets slower strategic intent [14]. No one can state reliable methods or applicability conditions, in which case fluent generated text is a proposal awaiting validation rather than domain knowledge [18]. Unrestricted recursion, unbounded task insertion, or elaborate partial ordering is contemplated without an understood termination argument. The desired output merely carries headings, which is not evidence that runtime search over alternative methods is needed.

**Hybrid construction**: Where only part of the problem carries stable procedural knowledge, HTN governs high-level compliance and handoffs, a goal-directed planner solves unfamiliar subgoals, a solver allocates resources, and a reactive controller performs low-level action. The boundary of a primitive task sits exactly at the interface to the specialised subsystem.

***

## II. Operational Framework: Bounded Decomposition Under a Versioned Domain Model

Phases 1 through 3 are design-time work performed once per domain version and reviewed like code. Phases 4 through 7 are runtime work performed once per run. No run may begin against a domain version that has not passed Phase 3.

### Phase 1: Planning Boundary and Abstraction Design

**Objective**: Fix what the system accepts, observes, and may invoke, and where abstraction stops, so decomposition operates inside a stated envelope rather than an implied one.

#### Step 1.1: Define the Planning Boundary

**Required Actions**:

- Enumerate accepted top-level task types, each with a stable identifier and a risk class.
- List the state variables the planner may trust, recording provenance and a freshness bound in time units.
- Inventory every invocable executor with the tool, agent, human role, or solver behind it and its required permission.
- Name the actions requiring human approval, recording whether approval is per run or per action.
- Define success, failure, cancellation, and escalation observably, and state the admission rule: a request enters planning only when its task type is accepted and the state needed to evaluate methods is present or retrievable by an authorised observation action.

**Required Outputs**:

- An accepted task-type register with risk classes, and an executor and permission inventory.
- A trusted state-variable inventory with provenance and freshness bounds.
- A written admission rule with four terminal-status definitions.

**Quality Checkpoints**:

- 100% of trusted state variables carry a freshness bound; a variable without one is reclassified as untrusted and cannot satisfy the admission rule.
- All 4 terminal statuses are decidable from evidence; a status decidable only by narrative judgement is rewritten before Phase 2.
- Every executor names its permission; an executor with an unstated permission is excluded from operator specification.

***

#### Step 1.2: Fix the Abstraction Levels

**Required Actions**:

- Start from outcomes meaningful to a domain expert rather than from available tools, refine into system capabilities, and stop at actions supported by stable executors.
- Record for each descent what it adds: a resolved ambiguity, a bound variable, or an operational constraint.
- Reject any level paraphrasing its parent without adding one of those three.
- Promote any nominally primitive action hiding alternatives, dependencies, or approvals into a compound task.

**Required Outputs**:

- A level map naming each abstraction level and its intended executor.
- A descent justification record with one entry per level transition.

**Quality Checkpoints**:

- Every descent adds at least 1 constraint or resolves at least 1 binding; a descent adding neither is collapsed into its parent.
- Level count falls within 2 to 6; above 6 triggers a redundant-abstraction review before the model proceeds.
- No primitive contains an alternative, approval, or internal dependency; any that does is promoted or delegated to a governed subsystem.

***

#### Step 1.3: Specify Primitive Operators and Compound Tasks

**Required Actions**:

- Record per primitive its input types, preconditions, expected effects, output contract, timeout, retry policy, idempotency class, estimated cost and duration, permissions, and compensation action where reversible.
- Define an evidence-producing postcondition checker per operator, naming the observation constituting proof of effect.
- Give each compound task an identifier, parameters, purpose, invariants, and a completion condition derived from an allowed method's subnetwork rather than from the task name.
- Classify every operator as reversible, compensable, or irreversible.

**Required Outputs**:

- An operator register with one complete entry per primitive, carrying the side-effect classification.
- A compound task register with parameters, invariants, and completion conditions.

**Quality Checkpoints**:

- 100% of operators carry a postcondition checker keyed to evidence rather than a call return; one without is marked non-executable and excluded from all plans.
- Every non-idempotent side-effecting operator carries a compensation action or an approval requirement; one carrying neither blocks approval in Phase 3.
- Cost and duration estimates cover at least 90% of operators, since prediction-accuracy metrics cannot be computed below that coverage.

***

### Phase 2: Method Library Authoring and Bounding

**Objective**: Author the authorised alternatives, separate hard constraints from preferences, and bound the search so refinement terminates by construction rather than by timeout.

#### Step 2.1: Author Alternative Methods for Each Compound Task

**Required Actions**:

- State per method its parent task, applicability conditions, introduced subtasks, ordering constraints, resource and policy constraints, predicted cost and risk, and justifying evidence.
- Author more than one method wherever the domain offers real alternatives, such as a primary-source method where authoritative evidence exists and a corroboration method where it does not.
- Add a declared fallback, safe-stop, or escalation method for every compound task whose failure has consequences beyond the run.
- Encode applicability conditions as evaluable expressions over the trusted state inventory, never as prose intentions, and remove methods producing identical behaviour under identical conditions.

**Required Outputs**:

- A method register with all fields populated per entry, and a method-to-task coverage map.
- A fallback and escalation inventory.

**Quality Checkpoints**:

- Every compound task has at least 1 method, and every consequential task at least 1 fallback or escalation method; a gap blocks Phase 3 approval.
- 100% of applicability conditions are evaluable against the trusted state inventory; one referencing an unavailable variable is rewritten or its method withdrawn.
- No 2 methods on the same parent share identical conditions and subnetworks; duplicates are merged before validation.
- Every method names its justifying evidence; one justified only by plausibility is marked a proposal and excluded from production selection.

***

#### Step 2.2: Separate Hard Constraints From Preferences and Fix the Selection Policy

**Required Actions**:

- Classify safety, permission, legal, resource-capacity, and required-ordering constraints as hard, and cost, speed, source preference, and style as scored preferences.
- Prohibit any aggregation rule in which a weighted preference offsets a hard violation.
- Declare the selection policy as deterministic first-applicable ordering or ranked search with backtracking, recording the consequence for method ordering.
- Specify ranking inputs where ranked search is used: predicted success, hard-risk screening, cost, duration, resource demand, historical reliability, and stated preference.
- Specify that an applicability result of unknown is never promoted to true for a safety-critical condition.

**Required Outputs**:

- A constraint classification separating hard constraints from scored preferences.
- A written selection policy with ranking inputs, tie-breaking rule, and unknown-condition handling.

**Quality Checkpoints**:

- 0 preference weights may change the outcome of a hard-constraint test; any such coupling halts Phase 2.
- Every constraint appears in exactly 1 classification; an unclassified constraint defaults to hard and is reviewed before release.
- The policy names a tie-breaking rule; without one it is completed before Phase 3, since unranked ties produce nondeterministic runs.
- Unknown results resolve to inapplicable for 100% of safety-critical conditions.

***

#### Step 2.3: Bound Recursion, Depth, and Resource Budgets

**Required Actions**:

- Give every recursive method a decreasing measure such as a shrinking unprocessed set, shorter remaining horizon, or lower unresolved-risk count.
- Set numeric caps on decomposition depth, generated task count, search nodes, planning time, tokens, and monetary cost.
- Set numeric caps on retry attempts per operator and replan generations per run.
- Record each cap's breach action, distinguishing safe termination from escalation, and document the termination argument separately, since a depth cap is a safety bound rather than a proof.

**Required Outputs**:

- A bounds table listing each cap, its numeric value, and its breach action.
- A termination argument for every recursive method.

**Quality Checkpoints**:

- 100% of recursive methods carry a decreasing measure; one without is withdrawn rather than capped.
- Every cap has a numeric value and a named breach action; a cap missing either blocks release.
- Retry limits are finite for 100% of operators, defaulting to at most 3 attempts where the domain states no value.
- Replan generations per run are capped, with 5 as the default ceiling above which the run escalates.

***

### Phase 3: Domain Validation and Versioned Release

**Objective**: Prove offline that the model is internally consistent and adequately covering, then release it under a version identifier making runs comparable.

#### Step 3.1: Validate the Domain Model Offline

**Required Actions**:

- Check that every referenced task, variable, and operator exists and that method parameters bind correctly.
- Check that ordering constraints are acyclic unless a loop is explicit and bounded, and that preconditions and effects are type-consistent with the state inventory.
- Confirm at least one applicable method across a representative set of expected states.
- Test unsatisfiable, adversarial, stale-state, missing-tool, and permission-denied cases, recording the terminal status of each.
- Run available plan validators, treating their verdicts as necessary but not sufficient because application-specific effects still require runtime verification.

**Required Outputs**:

- A static validation report covering reference integrity, binding, acyclicity, and type consistency.
- A coverage report over the representative state set, and a negative-case test record.

**Quality Checkpoints**:

- 0 dangling references remain; any dangling reference halts release.
- 0 unbounded cycles exist in the ordering constraints; a cycle without a decreasing measure halts release.
- At least 1 method applies for at least 95% of representative states; lower coverage returns the model to Step 2.1 for the uncovered contexts.
- Every negative case terminates in a defined status; any unhandled case blocks release.

***

#### Step 3.2: Version, Approve, and Register the Model

**Required Actions**:

- Assign version identifiers to the domain model, each method, operator, prompt, tool binding, and the policy set.
- Record the approval decision, approver role, and supporting validation evidence.
- Register the released version as the only version admissible for new runs, retaining prior versions for comparison rather than deleting them.
- State the comparability rule: results from different domain versions are not pooled unless the intervening change is recorded and assessed as behaviour-neutral.

**Required Outputs**:

- A version manifest covering model, methods, operators, prompts, tools, and policies.
- An approval record with attached evidence and a registered active version identifier.

**Quality Checkpoints**:

- 100% of methods, operators, prompts, and tool bindings carry a version identifier; an unversioned element blocks release because its runs cannot be compared or rolled back.
- The approval record names a human approver for every model above the lowest risk tier; an unapproved model is restricted to simulation.
- Exactly 1 domain version is registered as active for new runs at any time.

***

### Phase 4: Run Initialisation and Network Instantiation

**Objective**: Establish an auditable run context and a well-formed initial network, so the planner never repairs malformed input silently.

#### Step 4.1: Create the Run Context

**Required Actions**:

- Assign a run identifier and correlation identifiers for request, user, session, and parent workflow.
- Capture the top-level task and parameters, the initial state snapshot, and that snapshot's provenance and freshness.
- Record active domain, policy, planner, and model versions with any sampling settings affecting reproducibility.
- Record budgets for time, tokens, money, actions, and replans, plus risk class, required approvals, and allowed side effects.
- Apply the admission rule, rejecting or pausing the run where required data, permission, or a safe execution boundary is absent.

**Required Outputs**:

- A run record carrying identifiers, versions, budgets, risk class, and authorisation context.
- An annotated initial state snapshot and a reasoned admission decision.

**Quality Checkpoints**:

- Every state variable required by at least 1 candidate method is within its freshness bound or retrievable by an authorised observation action; otherwise the run pauses rather than planning on stale data.
- All 5 budget dimensions carry numeric values; a missing budget defaults to 0 and blocks admission rather than defaulting to unbounded.
- The run record names the active domain version; a run without one is rejected because its results are not comparable.

***

#### Step 4.2: Instantiate and Validate the Initial Task Network

**Required Actions**:

- Instantiate the top-level compound task with bound parameters.
- Attach initial ordering, deadline, resource, and policy constraints declared by the request or the policy set.
- Validate parameter types and task invariants against the compound task register.
- Halt before search where the initial network is malformed, returning the specific defect rather than attempting repair.

**Required Outputs**:

- An initial task network with its constraint store.
- A network validation verdict naming any defect found.

**Quality Checkpoints**:

- 100% of parameters bind to declared types; any unbound or mistyped parameter halts the run before search.
- All declared invariants hold in the initial state; a violated invariant halts the run as an admission defect.
- The initial constraint store holds 0 contradictory ordering or deadline constraints.

***

### Phase 5: Decomposition Search and Constraint Propagation

**Objective**: Reduce the network to primitive tasks through authorised methods while pruning invalid branches at the earliest point they can be detected.

#### Step 5.1: Evaluate the Termination Condition and Select the Next Task

**Required Actions**:

- Test the termination condition before every iteration: continue while unresolved compound tasks remain, validate executability when only primitives remain, and classify the network as blocked when neither a compound task nor an executable primitive remains and completion is false.
- Route a fully primitive network to whole-plan validation under plan-then-execute mode, or select an enabled primitive under interleaved mode.
- Select the earliest unresolved task in a totally ordered network, or a task whose predecessors are satisfied in a partially ordered network.
- Prefer a selection rule exposing likely failure early, such as most-constrained or highest-risk first, unless the planner's semantics require another order, and log the eligible set with the selection reason.

**Required Outputs**:

- A termination verdict for the current iteration.
- A selected task occurrence with its eligibility set and selection rationale.

**Quality Checkpoints**:

- The termination condition is evaluated before 100% of iterations; a skipped evaluation halts the loop as a control defect.
- The eligible set is logged for every selection; an unlogged selection cannot be audited and counts as a missing record in the Section III.D metrics.
- A blocked network enters failure handling within 1 iteration of detection rather than continuing to search.

***

#### Step 5.2: Enumerate, Rank, and Apply a Method

**Required Actions**:

- Retrieve every method whose head matches the selected task, bind parameters, and evaluate applicability against planning state and context.
- Record each candidate as applicable, inapplicable, unknown, or error, resolving unknown to inapplicable for safety-critical conditions.
- Rank applicable methods under the declared policy and preserve the ordered alternative set rather than discarding the losers.
- Constrain any model-proposed or model-ranked method to registered identifiers, validate bindings symbolically, and log the model, prompt, response, confidence, and validation verdict.
- Open a choice point saving network, state, constraint store, budgets, and remaining alternatives, then replace the selected task with a fresh subnetwork instance, preserving incoming and outgoing ordering constraints, creating lineage links, and incrementing depth.

**Required Outputs**:

- A candidate evaluation record with per-condition results and a retained ranked alternative set.
- A choice point identifier and the refined task network.

**Quality Checkpoints**:

- Every candidate carries an explicit applicability verdict; 0 candidates are silently omitted.
- 0 unregistered method identifiers enter the plan; a proposed identifier absent from the register is rejected rather than created on demand.
- A choice point exists for 100% of applied methods; a method applied without one cannot be backtracked and halts the run as a control defect.
- Depth after refinement stays within the Step 2.3 cap; a breach triggers the stated breach action rather than continued refinement.

***

#### Step 5.3: Propagate Constraints and Update Projected State

**Required Actions**:

- Verify types, bindings, ordering consistency, resource limits, temporal windows, permissions, method invariants, and any already-evaluable primitive preconditions.
- Reject the branch as soon as a hard violation appears rather than deferring detection to full decomposition.
- Apply modelled effects of fixed primitives to projected state in forward planning, and retain causal and ordering constraints instead in plan-space or partially ordered planning.
- Keep projected state in a store separate from observed state, and never write a projection into the observed record.
- Return control to the termination check and continue until the network is primitive and valid, a branch fails, a budget is reached, cancellation occurs, or external state invalidates an assumption.

**Required Outputs**:

- A constraint-check result for the refined network.
- An updated projected state store with separation from observed state preserved.

**Quality Checkpoints**:

- Constraints are checked after 100% of refinements; an unchecked refinement is rolled back and re-applied with checking enabled.
- Every hard violation detectable at planning time is detected there; a predictable violation first surfacing at execution is logged as a modelling defect.
- 0 projected facts appear in the observed state store; leakage invalidates the evidence trail and forces a restart from Step 4.1.

***

### Phase 6: Backtracking and Plan Validation

**Objective**: Recover from decomposition failure through explicit bounded backtracking, and prove the primitive plan valid before any consequential action.

#### Step 6.1: Backtrack Through Choice Points

**Required Actions**:

- Restore the most recent choice point holding an untried applicable method.
- Mark the failed branch with its failure category and violated constraint, and release its reservations and tentative state.
- Select the next alternative and resume at method application, moving backward through choice points until a branch succeeds or no alternatives remain.
- Append a restoration event to the log rather than removing the rejected branch from history.
- Apply memoisation only over the full signature of task, state, method, and constraint context, so a branch differing in context is not suppressed.

**Required Outputs**:

- A backtrack record naming the failed branch, its cause, the restored choice point, and the backtrack distance in hierarchy levels.
- A released-reservation record for the abandoned branch.

**Quality Checkpoints**:

- The event log is append-only across 100% of backtracks; 0 events are removed when planner state is restored.
- Every backtrack records a failure category and distance; a record missing either cannot support the backtracking metrics.
- 0 reservations remain held by an abandoned branch after restoration completes.
- Backtracking halts and escalates on reaching the search-node cap rather than continuing without bound.

***

#### Step 6.2: Classify and Resolve an Unresolvable Decomposition

**Required Actions**:

- Distinguish four causes where no method applies: incomplete state, missing domain coverage, genuine impossibility under the constraints, or exhaustion of a resource bound.
- Retrieve missing state only through an authorised observation action, treating the absence of such an action as escalation rather than impossibility.
- Select a resolution by cause: invoke a declared fallback, relax only soft preferences, request human input, delegate through a modelled primitive, or terminate safely.
- Never create an unregistered method to avoid failure, and never relax a hard constraint to obtain a plan.

**Required Outputs**:

- A failure classification naming one of the four causes and the selected resolution path.
- An escalation package naming the missing information or authority where escalation is chosen.

**Quality Checkpoints**:

- Every unresolvable decomposition carries exactly 1 classified cause; an unclassified failure escalates rather than retrying.
- 0 unregistered methods are introduced at runtime; any attempt halts the run and is reported as a domain gap.
- 0 hard constraints are relaxed to obtain a plan; an attempted relaxation is a safety defect halting the run.
- Escalations name the missing evidence or authority in 100% of cases, since one without that content cannot be actioned.

***

#### Step 6.3: Validate the Primitive Plan Before Consequential Execution

**Required Actions**:

- Confirm every operator in the plan exists in the released register at the active version.
- Confirm hard constraints are satisfied, dependencies form a valid schedule, and projected preconditions hold in sequence.
- Confirm remaining budgets cover projected cost and duration and that required approvals are present.
- Validate the selected schedule for a partial order, or require the executor to preserve the partial-order constraints explicitly.
- Record a plan version identifier and a validation verdict, treating an unvalidated generated plan as not a plan.

**Required Outputs**:

- A validated primitive plan with a plan version identifier.
- A validation report covering operator existence, constraints, schedule, budgets, and approvals.

**Quality Checkpoints**:

- Hard-constraint violations in the validated plan number exactly 0; any violation returns the run to Step 6.1 rather than proceeding.
- 100% of plan operators resolve to the active register; an unresolved operator halts execution.
- Projected cost and duration fall within remaining budgets; a projection exceeding budget triggers replanning or escalation rather than optimistic execution.
- Every required approval is recorded before the first consequential action; a missing action-scoped approval blocks that action alone.

***

### Phase 7: Monitored Execution, Recovery, and Closure

**Objective**: Execute primitives against fresh state, accept only evidence-backed effects, recover through the narrowest sufficient mechanism, and close with a complete lineage record.

#### Step 7.1: Execute One Enabled Primitive Task and Verify Its Effects

**Required Actions**:

- Recheck the operator's preconditions against fresh observed state immediately before invocation.
- Reserve required resources, generate an idempotency key for any retriable side effect, and enforce the declared timeout and retry limits.
- Capture tool requests and responses with sensitive values redacted or stored as secure references.
- Run the postcondition checker, classify the attempt as succeeded, failed, uncertain, or externally cancelled, update observed state only from evidence, and record divergence between predicted and observed effects.
- Mark a succeeded task complete, release its resources, enable successors whose dependencies now hold, and return to the termination check, verifying effect non-conflict and logging actual start and finish order wherever tasks run concurrently.

**Required Outputs**:

- An execution attempt record with identifiers, timings, costs, and status.
- A postcondition verification result with observed effects and any divergence entry.

**Quality Checkpoints**:

- Preconditions are rechecked against observed state before 100% of invocations; an invocation without a fresh recheck is a control defect.
- Every attempt is classified into exactly 1 of the 4 statuses; an unclassified attempt is treated as uncertain and blocks retry until reconciled.
- 0 observed-state updates originate from modelled effects rather than evidence.
- 0 secret or personal-data values appear in general telemetry; any occurrence triggers redaction at ingestion and a retention review.

***

#### Step 7.2: Select Repair, Backtracking, or Replanning

**Required Actions**:

- Apply the bounded retry policy first, and only for transient failures on idempotent operators whose preconditions still hold.
- Reconcile uncertain effects before any retry or conflicting branch selection, treating a timeout as evidence of nothing rather than evidence of no side effect.
- Select the narrowest sufficient mechanism from the matrix below, by observed condition rather than convenience.
- Increment a replan generation number, preserve completed tasks and irreversible effects, invalidate stale projections, rebuild only the affected remaining network, and reuse a prior decomposition only where its method conditions and versions still hold.
- Stop and escalate on reaching the replan cap, a repeated state signature, oscillating method choices, or a deadline, cost, or risk threshold.

**Recovery mechanism selection**:

| Condition observed | Mechanism | Bound before escalation |
| :-- | :-- | :-- |
| Transient failure, idempotent operator, precondition holds | Bounded retry | At most 3 attempts |
| Registered alternative primitive preserves method invariants | Local repair | 1 repair per task occurrence |
| Decomposition invalid, completed work harmless or compensable | Backtracking | Search-node cap from Step 2.3 |
| Observed state diverges from projection, or a tool is unavailable | Replanning | At most 5 replan generations |
| Action succeeded but must be semantically undone | Compensation | 1 compensation per irreversible effect |
| Safety or authorisation uncertain, or all methods exhausted | Escalation | Immediate; no retry |

**Required Outputs**:

- A recovery decision record naming the trigger, chosen mechanism, and bound applied.
- An updated plan generation naming preserved and invalidated task sets, with a compensation record per undone effect.

**Quality Checkpoints**:

- 0 retries occur against uncertain side effects before reconciliation completes.
- Replan generations per run stay at or below the Step 2.3 cap; exceeding it escalates rather than replanning again.
- Repeated state signatures across generations number at most 2 before oscillation protection halts the run.
- 100% of reused decompositions are checked against current method conditions and versions; an unchecked reuse is rejected.

***

#### Step 7.3: Close the Run and Emit the Lineage Record

**Required Actions**:

- Declare success only after every required primitive and the top-level completion condition are verified from evidence.
- Emit the final observed state, artifact references, constraint-validation result, costs, timing, deviations, and lineage from the top-level task through methods to executed primitives.
- Emit on non-success the terminal category, deepest resolved network, uncompensated effects, exhausted alternatives, and the information or authority required to continue.
- Retain the minimum content needed for audit and reproducibility, under access controls and retention periods matched to sensitivity.

**Required Outputs**:

- A terminal run record with status, reason, and final-state hash.
- A lineage record linking the top-level task to every executed primitive, and an uncompensated-effect list where any remains.

**Quality Checkpoints**:

- Success is declared only where 100% of required primitives are verified and the completion condition holds; a partially verified run closes as non-success.
- Every executed primitive traces to a generating method and plan version; one without lineage indicates an unmodelled action and triggers a domain review.
- Non-success records name the missing information or authority in 100% of cases, and uncompensated irreversible effects are enumerated rather than assumed absent.

***

## III. Implementation Guidance for AI Agents

AI agents operating an HTN planner must separate model authorship from runtime search, planning failure from execution failure, and projected state from observed state. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Domain Modelling Agent**: Owns Phases 1 through 3. Authors task types, operators, methods, constraints, and bounds, and refuses release when validation fails. Never executes a plan.
2. **Planner Agent**: Owns Phases 4 through 6. Selects tasks, enumerates and ranks methods, maintains choice points, and produces a validated primitive plan. Reads the domain model as read-only.
3. **Constraint Validator Agent**: Runs after every refinement and before every consequential action. Holds the hard-constraint set, and its rejection is not overridable by ranking scores.
4. **Execution Agent**: Owns Step 7.1. Invokes operators, enforces timeouts, retries, and idempotency, runs postcondition checkers, and writes observed state only from evidence.
5. **Recovery Agent**: Owns Step 7.2. Selects among retry, repair, backtracking, replanning, compensation, and escalation, and enforces the replan and oscillation bounds.
6. **Observability Agent**: Owns the append-only event stream and derived records. Never modifies planner state and never deletes an event.

**Workflow Execution Pattern**:

```
STATE: DECOMPOSITION_LOOP
INPUTS: task_network, planning_state, constraint_store, budgets, domain_version
ACTIONS:
  1. Evaluate termination condition
  2. Select next unresolved task under the declared selection rule
  3. Enumerate candidate methods, bind parameters, evaluate applicability
  4. Rank applicable methods and retain the ordered alternative set
  5. Open choice point, apply one method, increment depth
  6. Propagate constraints and update projected state
VALIDATION:
  - hard_constraint_violations == 0
  - decomposition_depth <= depth_cap
  - unknown_condition_promoted_to_true == FALSE
  - unregistered_method_identifiers == 0
  - budgets_remaining > 0
TRANSITIONS:
  IF network_is_primitive AND validations_pass THEN next_state = PLAN_VALIDATION
  IF hard_violation OR no_applicable_method       THEN next_state = BACKTRACK
  IF budgets_exhausted OR depth_cap_reached       THEN next_state = SAFE_TERMINATION
  ELSE next_state = DECOMPOSITION_LOOP
```

**Two-Phase Action Pattern**: Refine the network to primitive tasks without invoking any consequential operator; validate the whole plan while no side effect has occurred and the plan is still cheap to discard; then execute, rechecking preconditions against fresh observed state at each invocation.

**Approval Gate**: Human authorisation is required before the first irreversible action, before any action whose projected cost exceeds the run's approval threshold, and before any escalation relaxing a soft preference in the highest risk class. Approval is modelled as a primitive task or applicability condition, never as an informal pause inside executor code.

**Context Management Requirements**:

- Hold the domain model as an external addressable artifact and retrieve only the methods matching the selected task.
- Bound retained planning history to choice points still reachable for backtracking, referencing older history through the event log.
- Emit each decomposition event as it occurs rather than batching at run end, so context exhaustion leaves a complete partial record.
- Prefer short deliberation followed by observation over a large open-loop plan, since a long plan built on stale projections is invalidated as a whole [13].

### B. Quality Assurance Checkpoints

**Checkpoint 1: Boundary Integrity (After Phase 1)**

- **Automated Check**: Every accepted task type has a risk class; 100% of trusted variables carry freshness bounds; all 4 terminal statuses are evidence-decidable.
- **Agent Action on Pass**: Proceed to method authoring.
- **Agent Action on Failure**: Halt and return the specific boundary defect.
- **Human Review Trigger**: Any accepted task type whose success cannot be defined observably.

**Checkpoint 2: Method Coverage (After Phase 2)**

- **Automated Check**: Every compound task has a method; consequential tasks have a fallback; recursive methods have decreasing measures; all caps carry values and breach actions.
- **Agent Action on Pass**: Proceed to offline validation.
- **Agent Action on Failure**: Return to Step 2.1 for the uncovered tasks only.
- **Human Review Trigger**: Method coverage below 95% across the representative state set.

**Checkpoint 3: Release Readiness (After Phase 3)**

- **Automated Check**: 0 dangling references; 0 unbounded cycles; 100% version coverage; every negative case terminates in a defined status.
- **Agent Action on Pass**: Register the version as active for new runs.
- **Agent Action on Failure**: Halt release; the model stays restricted to simulation.
- **Human Review Trigger**: Any model above the lowest risk class, requiring named human approval regardless of automated results.

**Checkpoint 4: Search Integrity (During Phase 5, per refinement)**

- **Automated Check**: A choice point exists per applied method; hard violations equal 0; depth is within cap; 0 unregistered identifiers entered the plan.
- **Agent Action on Pass**: Continue the decomposition loop.
- **Agent Action on Failure**: Reject the branch and enter backtracking.
- **Human Review Trigger**: More than 3 consecutive branch rejections on one compound task, indicating a defective applicability test.

**Checkpoint 5: Pre-Execution Validity (After Phase 6)**

- **Automated Check**: All operators resolve at the active version; hard violations equal 0; the schedule is valid; budgets cover projections; approvals are present.
- **Agent Action on Pass**: Begin monitored execution.
- **Agent Action on Failure**: Halt before any consequential action and return to backtracking or escalation.
- **Human Review Trigger**: Any plan containing an irreversible action, or a projected cost within 10% of the run budget.

**Checkpoint 6: Execution Evidence (During Phase 7, per attempt)**

- **Automated Check**: Preconditions rechecked; attempt classified into exactly 1 of 4 statuses; postcondition evidence recorded; divergence logged.
- **Agent Action on Pass**: Enable successors and continue.
- **Agent Action on Failure**: Enter recovery selection with the failure classified.
- **Human Review Trigger**: Any uncertain effect on a non-idempotent operator, which may not be retried without human reconciliation.

**Checkpoint 7: Closure Completeness (After Phase 7)**

- **Automated Check**: Required primitives verified at 100%; lineage complete per executed primitive; uncompensated effects enumerated.
- **Agent Action on Pass**: Close the run as successful and emit the artifacts.
- **Agent Action on Failure**: Close as non-success with the terminal category and missing information named.
- **Human Review Trigger**: Any uncompensated irreversible effect at closure.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
AUTOMATED_CHECK:
MEASURED_VALUE:
PASS_CONDITION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
DOMAIN_MODEL_VERSION:
RESPONSIBLE_AGENT:
```

### C. Error Handling and Troubleshooting

Planning failure means the system cannot produce a permitted primitive network under its current knowledge, model, constraints, and budget. Execution failure means a selected primitive did not produce verified effects. The classifications stay separate because a domain gap is repaired by authoring while an execution failure is repaired by recovery.

**Error Type 1: No Applicable Method**

- **Symptoms**: Every candidate evaluates to inapplicable, unknown, or error for the selected compound task.
- **Diagnostic Steps**: Determine which of the four causes applies, inspecting the failed condition recorded per candidate rather than the aggregate verdict.
- **Resolution Protocol**: Option A, retrieve missing state through an authorised observation action. Option B, invoke a declared fallback or escalation method. Option C, relax only soft preferences and re-rank. Option D, terminate safely with the blocking constraint named.
- **Escalation Trigger**: Escalate immediately where no authorised observation action exists, and after at most 2 fallback attempts on one task occurrence.

**Error Type 2: Hard Constraint Violation During Refinement**

- **Symptoms**: Constraint propagation rejects the refined network on ordering, resource, temporal, or permission grounds.
- **Diagnostic Steps**: Identify whether the violation originates in the applied method, an inherited parent constraint, or a stale projection.
- **Resolution Protocol**: Option A, backtrack and select the next alternative. Option B, backtrack further where the parent method created the conflict. Option C, escalate where a permission or safety constraint admits no alternative.
- **Escalation Trigger**: Escalate on reaching the search-node cap or after 3 consecutive rejections on one compound task.

**Error Type 3: Unverified or Uncertain Execution Effect**

- **Symptoms**: The postcondition checker reports failure or cannot decide; a timeout occurred with no confirming evidence.
- **Diagnostic Steps**: Treat the timeout as evidence of nothing, query an independent checker, compare modelled with observed effects, and confirm the idempotency class.
- **Resolution Protocol**: Option A, retry under the same idempotency key where the operator is idempotent, the precondition holds, and the retry limit is intact. Option B, reconcile through independent observation before further action. Option C, compensate a confirmed unwanted effect. Option D, replan from observed state preserving the uncertain fact as unresolved.
- **Escalation Trigger**: Escalate after at most 3 attempts, and immediately for any uncertain effect on a non-idempotent operator.

**Error Type 4: Oscillation and Replan Exhaustion**

- **Symptoms**: Repeated state signatures across generations; alternating method choices without new evidence; replan count approaching its cap.
- **Diagnostic Steps**: Compare state signatures across generations and check whether new evidence entered observed state between replans.
- **Resolution Protocol**: Option A, suppress the alternating pair and select a third method where one exists. Option B, require new evidence before a further replan. Option C, escalate with the deepest resolved network and the oscillating pair named.
- **Escalation Trigger**: Escalate after 2 repeated state signatures or on reaching the replan cap, whichever comes first; this error is never resolved by further replanning alone.

**Error Type 5: Unvalidated Model-Proposed Decomposition**

- **Symptoms**: A proposed method references unregistered identifiers, bindings that do not type-check, or conditions not evaluable against trusted state.
- **Diagnostic Steps**: Match every proposed identifier against the register at the active version and attempt symbolic binding validation.
- **Resolution Protocol**: Option A, reject the proposal and continue with registered alternatives. Option B, route it to the Domain Modelling Agent as a candidate for authoring and approval. Option C, escalate where no registered alternative exists.
- **Escalation Trigger**: Any unregistered identifier halts its branch immediately; this error is never resolved by retrying generation.

**Troubleshooting Decision Tree**:

```
RUN CANNOT PROCEED
├─ PLANNING FAILURE
│   ├─ No applicable method → classify cause
│   │   ├─ State incomplete → authorised observation action, else escalate
│   │   ├─ Domain gap → declared fallback, else escalate; never invent a method
│   │   ├─ Genuinely impossible → terminate safely, naming the blocking constraint
│   │   └─ Budget exhausted → escalate with deepest resolved network
│   ├─ Hard constraint violated → BACKTRACK to nearest untried alternative
│   └─ Depth or node cap reached → HALT, report the termination measure
├─ EXECUTION FAILURE
│   ├─ Transient, idempotent, precondition holds → RETRY (limit 3), then escalate
│   ├─ Precondition no longer holds → REPLAN from observed state
│   ├─ Effect uncertain → reconcile first; never retry blind
│   └─ Effect irreversible and unwanted → COMPENSATE, else escalate
└─ CONTROL FAILURE
    ├─ Oscillating method choice → HALT after 2 repeated state signatures
    ├─ Replan generations exceeded → escalate, naming information needed
    └─ Unregistered identifier proposed → REJECT branch, route to authoring
```

**Invariant Failure Rules**:

- Never roll back the event log when backtracking; planner state returns to a choice point while the audit history appends a restoration event and retains every rejected branch.
- Never treat a tool timeout as evidence that no side effect occurred; reconcile uncertain effects before retrying or selecting a conflicting branch.
- Never allow a weighted preference to compensate for a hard violation, and never relax a hard constraint to obtain a plan.
- Never reuse a cached decomposition without rechecking method conditions and versions.
- Never let reflection or meta-reasoning modify the authorised hierarchy; proposed adaptations enter the same validation and approval process as any other domain change.

### D. Observability, Performance Metrics, and Continuous Learning

**Logging Architecture**: Maintain an append-only event stream plus materialised run, task, method-choice, plan-version, and execution-attempt records. Use wall-clock timestamps for cross-system correlation and monotonic durations for latency computation. Redact secrets and personal data at ingestion and store secure references rather than sensitive payloads.

**Event Record Template**:

```
EVENT_SCHEMA_VERSION:
EVENT_ID:
EVENT_TYPE:            [RUN_OPEN | DECOMPOSITION | SEARCH | PLAN_VALIDATION |
                        EXECUTION_ATTEMPT | REPAIR_REPLAN | RUN_CLOSE]
EVENT_TIMESTAMP_WALLCLOCK:
MONOTONIC_SEQUENCE_NUMBER:
RUN_ID:
PLAN_VERSION_ID:
ACTOR_OR_AGENT_ID:
CORRELATION_ID:
PARENT_EVENT_ID:
DOMAIN_VERSION / METHOD_VERSION / OPERATOR_VERSION / POLICY_VERSION:
PAYLOAD_REFERENCE:     [secure reference; secrets redacted at ingestion]
```

**Required Content by Event Type**:

- **Run level**: Top-level task and parameters, requester and risk class, initial-state hash, state provenance and freshness, domain, policy, planner and model versions, sampling settings, available tools, authorisation context, planning mode, budgets, terminal status and reason, final-state hash, output references.
- **Decomposition event**: Selected occurrence, task type, parent, depth, unresolved-network size before and after, eligible set, selection rule, candidate identifiers with per-condition results, ranking scores, chosen method and version, bindings, introduced subtasks, ordering and resource constraints, constraint-check result, projected cost and duration, choice-point identifier, and network and constraint-store hashes before and after.
- **Search event**: Node and parent identifiers, branch number, frontier size, expanded and generated node counts, memoisation hits, pruning reason, heuristic values, elapsed planning time, tokens and cost consumed, remaining budgets; for backtracks, the failed branch, failure category, violated constraint, restored choice point, discarded work, alternative selected, and backtrack distance.
- **Plan-validation event**: Plan version, primitive count, maximum and mean depth, ordering validation, precondition simulation result, resource, temporal, permission and approval validation, hard-violation count, soft-preference score, validator version, warnings, and verdict.
- **Execution attempt**: Task and operator identifiers, plan generation, attempt number, executor version, idempotency key reference, input hash, precondition observations, scheduled and actual start, finish and duration, timeout and retry status, resource consumption, token and monetary cost, response status, output hash, postcondition observations, predicted and observed effects, divergence classification, and error taxonomy entry.
- **Repair or replan event**: Trigger, detection source, affected tasks and assumptions, observed-state change, old and new plan identifiers, preserved and invalidated tasks, compensation actions, planning overhead, method changes, recovery outcome, and a causal category drawn from stale state, domain gap, tool failure, external event, constraint conflict, budget exhaustion, policy denial, or model error.
- **Closure**: Verified outcome, required versus completed primitives, uncompensated side effects, total planning and execution duration, tokens and cost, plan generations, failure counts, human interventions, approvals, and artifact lineage.

**Metric Families and Targets**:

| Metric | Definition | Target |
| :-- | :-- | :-- |
| **Plan-generation success rate** | Runs producing a valid primitive plan, over runs admitted | ≥90% |
| **End-to-end success rate** | Runs with verified execution and top-level completion | ≥80% |
| **First-pass plan validity** | First plans passing every hard check without repair | ≥85% |
| **Execution validity** | Attempts whose preconditions held and postconditions verified | ≥95% |
| **Method coverage** | Encountered task and state contexts with an applicable method | ≥95% |
| **Hard-constraint safety** | Plan versions with 0 hard violations | 100% |
| **Backtracking frequency** | Planned runs with at least 1 backtrack | ≤30% |
| **Replans per run** | Mean plan generations beyond the first | ≤1.0 |
| **Effect-divergence rate** | Successful calls whose observed effects differ from modelled | ≤5% |
| **Budget adherence** | Runs within time, token, money, action, and replan limits | ≥95% |
| **Human-intervention rate** | Runs needing clarification, extra approval, or recovery help | ≤15% |

**Metric Interpretation Rules**:

- Segment success rates by top-level task, domain version, risk class, and environment, so improvement is not an artifact of an easier workload, and read the gap between plan-generation and end-to-end success as isolating execution and environment weaknesses.
- Track decomposition efficiency as valid primitives per expanded node, planning time per primitive, and useful executed tasks over all generated occurrences; depth alone is not a quality measure, since excessive depth signals redundant abstraction while shallow networks may hide complexity inside opaque primitives.
- Report method utilisation and success rate with confidence intervals and a minimum support of 20 selections, comparing method versions rather than pooling incompatible definitions.
- Read backtracking concentrated in 1 method as a defective applicability test rather than healthy exploration, and count an execution-time hard violation predictable at planning time as a modelling defect.
- Examine the planning-to-execution resource ratio by task complexity, since 1 global target penalises difficult but appropriate planning.

**Learning and Adaptation Mechanisms**:

- **Perturbation suite**: Vary initial-state facts, missing data, tool latency, transient errors, method ordering, cost estimates, deadlines, and benign input wording, and add adversarial cases covering contradictory state, poisoned untrusted instructions, unavailable tools, permission denial, repeated timeouts with uncertain side effects, and cyclic decomposition proposals. Compare each perturbed run with a baseline on the same domain version and record whether the planner succeeded, failed safely, escalated correctly, or violated a hard constraint.
- **Robustness reporting**: Run repeated trials over identical task sets with controlled seeds, reporting success-rate confidence intervals, median and tail latency, cost variance, method-choice entropy, plan-edit distance, and outcome variance. Robustness means relevant perturbations cause no unacceptable degradation, not that the same plan repeats.
- **Paired replay evaluation**: Replay a representative corpus against old and new versions when a method or ranking policy changes, using simulation or read-only tools so no consequential side effect occurs. Promote a change only where it holds hard-constraint safety at 100% and improves the targeted metric without regressing tail cost, tail latency, or intervention rate by more than 10%.
- **Domain feedback loop**: Route every escalation classified as a domain gap into the method register as a candidate, subject to the full Phase 2 and Phase 3 validation path rather than direct insertion.

***

## IV. Domain-Agnostic Application Guidance

The framework is independent of subject matter. What changes between domains is the content of task types, operators, and methods, not the phase sequence, the choice-point discipline, or the evidence rules.

### Worked Application: Preparing a Grant Application

The top-level compound task is the preparation and quality assurance of a grant application. One method applies where the official call, applicant facts, and deadline are available, decomposing the task into establishing requirements, designing a response strategy, drafting sections, verifying claims and citations, running compliance review, and preparing submission, with drafting permitted to overlap across independent sections and compliance review ordered strictly after consolidation.

Establishing requirements decomposes into primitive retrieval of the current call, primitive extraction into a requirements register, and primitive human confirmation of ambiguous eligibility rules. Verifying claims selects an official-source method where a primary source exists and a corroboration method otherwise. Preparing submission stays blocked until required approvals and all hard compliance checks hold.

Where a cited source becomes unavailable during execution, the failed retrieval operator refreshes observed state. A local retry is permitted only where the operator is idempotent and the retry budget intact; otherwise the planner backtracks from the source-verification method to the corroboration method. Where the missing source is mandated by the funder, no alternative method applies, and the run escalates naming the exact missing evidence rather than fabricating support. The log then reconstructs why each section exists, which method generated it, which source supported each claim, which constraints were checked, where backtracking occurred, and whether the submission condition was verified.

### Worked Application: Service-Incident Response

The top-level compound task is the safe restoration of service. A triage method decomposes it into observing symptoms, classifying severity, preserving evidence, and selecting a containment method. Where state indicates a faulty deployment and rollback is authorised, one method introduces verification of the rollback target, obtaining approval where required, executing the rollback, and verifying service health. Where data corruption is possible, a different method prioritises write isolation and forensic preservation.

Where a health-check primitive fails after rollback, the planner does not conclude that the rollback failed. It records the uncertain observation, invokes an independent checker, and compares modelled with observed effects. Where service remains unhealthy, it replans from current state while preserving the irreversible fact that rollback occurred, and oscillation protection prevents repeated roll-forward and rollback branches without new evidence. The division of labour is explicit: HTN encodes accepted procedures and authorisation gates, reactive monitors detect fast state changes, constraint checks protect resource and safety limits, and reflection may summarise diagnostic evidence without authorising an unmodelled action.

### Cross-Domain Adaptation Patterns

**Research and analysis workflows**: Compound tasks map to investigative stages and primitives to retrieval, extraction, and verification. Postcondition checkers verify evidence provenance rather than call success, and method alternatives encode source-availability contingencies.

**Software delivery and operations**: Compound tasks map to change, release, and remediation procedures. Irreversible operators dominate, so compensation actions and approval gates carry most of the safety load, and replanning preserves completed irreversible facts.

**Manufacturing, logistics, and robotics**: Partial ordering earns its cost because independent physical operations run concurrently. Methods delegate scheduling and routing to a constraint solver, and low-level control is delegated to a reactive controller at the primitive boundary.

**Regulated business processes**: Hard constraints encode legal and permission requirements, method conditions encode jurisdictional variation, and the lineage record is the audit artifact retained under its sensitivity class.

**Education and training design**: Compound tasks map to instructional outcomes, alternative methods encode differing prerequisite states of the learner, and human approval is modelled at assessment boundaries rather than assumed.

**Multi-agent systems**: Compound tasks map onto roles while the network expresses ordering and synchronisation between them. Each agent's capability boundary determines where a task becomes primitive, and cross-agent handoffs are modelled as operators with explicit postcondition checkers.

### Scale Adaptation

- **Small scope**, under 10 compound tasks in a stable environment: Retain the design-time phases but permit deterministic first-applicable selection, a depth cap of 4, and plan-then-execute mode without interleaving.
- **Medium scope**, 10 to 50 compound tasks under moderate change: Use ranked selection with backtracking, a depth cap of 6 to 8, interleaved planning and acting, and the full metric set segmented by task type.
- **Large scope**, over 50 compound tasks with several executors in a volatile environment: Partition the method library by subdomain with separate version streams, delegate subproblems to specialised planners at modelled primitive boundaries, and enforce oscillation and replan caps at both run and subdomain level.
- **Any scope with irreversible actions**: Approval gates and compensation coverage are mandatory regardless of size, since the cost of an unmodelled irreversible action does not scale down with the model.

***

## V. Limitations and Considerations

**Completeness is relative to the method library**: An HTN planner cannot produce a plan its methods do not generate, so under-coverage presents as impossibility. Mitigate by measuring method coverage over a representative state set, distinguishing domain gaps from genuine impossibility in every escalation, and routing gap escalations back into authoring.

**Modelling cost is front-loaded and recurring**: A domain model requires authorship, validation, versioning, and maintenance as tools and policies change, which makes HTN uneconomic for short-lived or low-repetition tasks. Mitigate by applying the exclusion conditions in Section 1.3 before committing to the pattern.

**Brittleness under environmental divergence**: An encoded hierarchy can depart from reality faster than it is revalidated, producing plans that are internally valid and externally wrong. Mitigate by keeping projected state separate from observed state, rechecking preconditions before every invocation, and preferring short deliberation cycles over large open-loop plans.

**Computational difficulty of unrestricted variants**: Unbounded recursion, arbitrary task insertion, and elaborate partial ordering raise search cost sharply and make termination hard to establish [8][11]. Mitigate through decreasing measures, numeric caps with named breach actions, and a termination argument recorded independently of the caps.

**Generated decompositions are proposals, not knowledge**: A language model can produce fluent method-shaped text corresponding to no valid procedure, so unvalidated adoption converts a generation error into an executed action. Mitigate by constraining proposals to registered identifiers, validating bindings and conditions symbolically, and routing every proposal through the standard approval path.

**Observability carries privacy and retention exposure**: The lineage detail making runs auditable also concentrates sensitive content. Mitigate by redacting at ingestion, storing secure references instead of payloads, and setting access controls and retention by sensitivity class rather than uniformly.

**Metric gaming through partial measurement**: Optimising plan-generation rate alone can improve a dashboard while degrading verified execution, safety, cost, and variance. Mitigate by reporting plan-generation and end-to-end success separately, holding hard-constraint safety at 100% as a promotion gate, and requiring paired replay evaluation before promoting any change.

***

## VI. Conclusion and Summary

HTN planning is disciplined procedural search rather than hierarchical prose. Its value comes from combining abstraction with executable semantics, domain-approved alternatives, constraint-aware search, and evidence-based execution. Applied to the right problems it produces reusable, interpretable plans whose lineage explains why each action was taken; applied without reliable methods, current state, and bounded recovery it converts procedural confidence into systematic brittleness.

The framework's centre of gravity is the design-time work in Phases 1 through 3. No planner compensates at runtime for absent methods, unclassified constraints, unbounded recursion, or operators lacking evidence-producing checkers. The runtime phases add the machinery that keeps a valid model honest: explicit choice points, early constraint propagation, validation before consequential action, evidence-only state updates, and bounded recovery selected by failure cause.

**Minimal Production Readiness Standard**: An HTN system is admissible to controlled production only where it carries a versioned domain model; typed task and method schemas; observable primitive operators with postcondition checkers; hard-constraint and permission checks; bounded search, retries, and replanning; explicit backtracking and escalation; append-only lineage logs; offline coverage and perturbation tests; and separate metrics for planning validity, execution success, safety, cost, and robustness. Where any control is absent, the system is restricted to recommendation or simulation until it is supplied.

**Key Success Factors**:

- **Encoded expertise over improvised decomposition**: Methods represent defensible procedures with explicit applicability conditions, authored once and versioned, not plausible hierarchies regenerated on every run.
- **Observable primitives**: Every operator ends at a verifiable postcondition and a clear boundary to a tool, person, solver, or controller, and no meaningful alternative or approval hides inside a nominally primitive task.
- **Modelled failure paths**: Fallback, compensation, escalation, and safe-stop methods exist wherever the domain permits, so failure has an authorised route rather than an improvised one.
- **Evidence discipline**: Observed state is updated only from evidence, projections are never written into it, and divergence is logged rather than reconciled silently.
- **Bounded everything**: Recursion carries decreasing measures, and depth, nodes, time, cost, retries, and replans carry numeric caps with named breach actions.
- **Complete and immutable lineage**: Rejected branches are retained alongside the winning plan, because failure evidence is what improves applicability tests and measures robustness.

By following this framework, AI agents can convert abstract tasks into validated primitive plans, execute them against verified evidence, recover through the narrowest sufficient mechanism, and leave a lineage record supporting audit, comparison, and disciplined improvement of the domain model itself.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The external references listed below are transcribed from that originating prose guide and have not been independently re-verified during conversion; each title and address is reproduced as it stood in the source. Items 1 through 4 are corpus pointers, and items 5 through 18 are the external works cited by the prose source.

1. `Hierarchical Task Network Planning: An Operational Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the domain-model design rules, the planning and execution workflow, the failure policy, the logging schema, the metric definitions, the two worked applications, and the minimal production readiness standard.

**Companion guides**:

2. `advanced_task_guides/authoring/guide_guidewriting.md` — the house-style specification governing this document's archetype, step slot template, mandatory section names, and conformance envelope.
3. `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — sibling guide on telemetry design, relevant to the append-only event stream and event record schema in Section III.D.
4. `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — sibling guide on monitoring design under constraints, relevant to the constraint classification in Step 2.2 and the checkpoint architecture in Section III.B.

**External references — HTN formalism, complexity, and hierarchical domain languages**:

5. Georgievski and Aiello overview — https://arxiv.org/abs/1403.7426
6. Erol, Hendler, and Nau framework — https://www.cs.umd.edu/~nau/papers/erol1993toward.pdf
7. Erol, Hendler, and Nau — https://www.cs.umd.edu/~nau/papers/erol1994umcp.pdf
8. Erol, Hendler, and Nau — https://www.cs.umd.edu/~nau/papers/erol1996complexity.pdf
9. Georgievski and Aiello — https://pure.rug.nl/ws/files/83768215/HTN_planning_Overview_comparison_and_beyond.pdf
10. Höller and colleagues — https://gki.informatik.uni-freiburg.de/papers/hoeller-etal-hplan19.pdf
11. Structural Complexity Analysis of HTN Planning — https://arxiv.org/abs/2401.14174

**External references — planners, tooling, and applied systems**:

12. Nau and colleagues — https://arxiv.org/abs/1106.4869
13. GTPyhop — https://www.cs.umd.edu/~nau/papers/nau2021gtpyhop.pdf
14. Bansod and colleagues — https://www.cs.umd.edu/users/nau/papers/bansod2021integrating.pdf
15. Unified Planning — https://unified-planning.readthedocs.io/en/latest/problem_representation.html
16. Game AI Pro — https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter12_Exploring_HTN_Planners_through_Example.pdf
17. Chen and colleagues — https://arxiv.org/abs/2306.08359
18. GPT-HTN-Planner — https://github.com/DaemonIB/GPT-HTN-Planner

