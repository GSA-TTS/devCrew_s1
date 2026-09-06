# Constraint Satisfaction Planning

**Status**: Beta testing

**Change logs**:

- [09/06/2026] - Initialization

***

## Executive Summary

Constraint Satisfaction Planning is the task family of converting a planning subproblem into explicit decision variables, candidate value domains, and restrictions on which value combinations are permitted, then obtaining an assignment that satisfies every mandatory restriction and, where preferences exist, approximates or proves the best feasible assignment. It applies wherever feasibility is difficult to judge informally because scheduling, allocation, routing, configuration, temporal, capacity, permission, and compatibility rules interact. The mechanism is constraint propagation followed by guided search, with optimization layered on top of an established feasible region.

This guide provides AI agents with an operational protocol for admitting a decision problem, building a versioned constraint model before runtime, selecting a solving method matched to model structure, executing propagation and search under declared bounds, validating every candidate assignment against authoritative requirements through an independent checker, diagnosing infeasibility rather than concealing it, relaxing only under recorded authority, testing robustness before consequential handoff, and returning control to an orchestrator that continues to observe reality.

One architectural constraint governs the whole framework: a language model must not be trusted to perform constraint propagation, feasibility determination, or optimality proof by itself. Fluent output is not a feasibility certificate. The language model serves as an interface and model-authoring assistant; a solver establishes feasibility; an independent validator confirms the result against source requirements. This separation is preserved in every phase, checkpoint, and error path below.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Variable**: One decision whose value is not yet fixed. It can be a meeting start slot, an assigned actor identifier, a serving vehicle, an allocated machine, and a Boolean inclusion decision are variables. Facts already known, such as a room's capacity or an operator's clearance level, are input data rather than variables unless the system is explicitly deciding them.

**Domain**: The set or range of values a variable may take. Sound modelling begins from the tightest domain justified by authoritative data. A value removed without justification can delete the only solution; an unrealistically broad domain wastes search effort and permits semantically invalid outputs to enter the candidate space.

**Constraint**: A statement of which values or value combinations are allowed. A unary constraint restricts one variable. A binary constraint links two variables. A higher-arity or global constraint relates many variables at once, expressing reusable structure such as all-distinct assignment, cumulative resource use below capacity, or membership in a permitted compatibility tuple set. A global constraint is more than syntactic convenience, because a solver can frequently propagate it more effectively than an equivalent collection of pairwise tests [13][14].

**Hard constraint**: A restriction that is non-negotiable within the current planning contract. Safety limits, authorization rules, legal restrictions, physical capacity, required precedence, and non-overlap rules are typical. A candidate violating one hard constraint is not a solution.

**Soft constraint**: A preference whose violation is permitted at a declared cost, priority, or lexicographic level. Preferred working hours, travel minimisation, workload balance, and honoured requests are typical [15]. A mandatory rule is never encoded as a large finite penalty unless the accountable owner has explicitly authorized that relaxation, because every finite weight can in principle be outweighed.

**Objective**: A ranking over feasible assignments. It may minimise cost, delay, makespan, travel, imbalance, energy, or weighted soft violations, or maximise coverage, preference satisfaction, expected utility, or slack. Multi-objective problems require an explicit policy: lexicographic priority, weighted aggregation with stated units and approved weights, or enumeration of non-dominated alternatives for human choice.

**Constraint graph**: A diagnostic view in which variables are nodes and edges join variables sharing a binary constraint, with higher-arity constraints represented as a factor or hypergraph [16]. Dense regions indicate tightly coupled decisions, separators suggest decomposable subproblems, and symmetric regions warn that many assignments may be equivalent. The graph informs decomposition boundaries, propagation strength, variable ordering, and what context must travel between agents solving related pieces.

**Partial assignment**: A binding of only some variables. It is consistent when it violates no constraint whose relevant variables are sufficiently bound.

**Complete assignment**: A binding giving every required decision variable a value. It is feasible only when an independent final check confirms every hard constraint against authoritative inputs, because solver-internal consistency is necessary but not sufficient when source data may be stale, units may be wrong, or the model may have omitted a real requirement.

**Constraint propagation**: The removal of domain values that cannot participate in any solution under current information. Propagation detects local contradictions cheaply and focuses search on what remains possible.

**Search**: The systematic or stochastic exploration of assignments consistent with the propagated model. Systematic search can prove infeasibility; ordinary local search cannot.

**Optimization**: The retention of feasibility while improving an objective, typically by bounding remaining search against an incumbent.

**Incumbent**: The best complete assignment found so far. An incumbent becomes a result only after independent validation.

**Solve contract**: The declared statement of what the requester needs, selected from any feasible solution, a proven optimum, several diverse alternatives, an enumeration, a proof of infeasibility, or a best-known answer within a deadline. Different contracts carry different acceptance conditions and different failure semantics.

**Conflict set**: A subset of constraints that cannot all hold simultaneously in the model. An unsatisfiable core is a conflict set produced by the backend. A conflict set proves that its members are jointly unsatisfiable; it does not decide which member should change, and it is neither necessarily minimal nor necessarily unique.

**Relaxation**: An authorized, recorded change to constraint hardness, bounds, or penalties that enlarges the feasible region. Relaxation is a governed policy decision, never a solver tuning action.

**Independent validator**: A checker implemented separately from the model-building path that recomputes every hard constraint from authoritative inputs and the returned assignment, verifies domain membership and completeness, recalculates objective components, and emits violations by constraint identifier.

**Solve generation**: A monotonically incremented version marker covering the model, its data snapshot, and its parameters. Any accepted change to constraints, data, or authority creates a new generation rather than mutating the current one.

### 1.2 The Conceptual Model and Its Solving Machinery

Constraint reasoning is declarative. The model states what must hold rather than prescribing the exact procedure for finding it, and the solving machinery identifies impossible combinations in order to focus search on what remains possible [10]. The machinery divides into four layers, and AI agents must understand all four because the guarantees each layer provides differ.

**Propagation layer**: Node consistency removes values violating unary restrictions. Arc consistency, defined for a directed arc between two variables, requires that every remaining value of the first variable have at least one compatible supporting value in the second variable's domain. Because the definition is directional, revising one direction does not automatically revise the reverse; when a domain shrinks, neighbouring arcs may need reconsideration, so a work queue is maintained until no further revision is possible or a domain becomes empty. Path consistency asks the stronger question of whether a compatible assignment at the endpoints of a path can be extended through the intervening variables [16]. Stronger consistency exposes contradictions that weaker checks miss, at higher time and memory cost. Local consistency at any level detects many contradictions but never proves that a global solution exists.

**Look-ahead layer inside search**: Forward checking removes incompatible values from directly connected unassigned variables after each assignment and fails the branch immediately when a domain empties, without propagating all consequences among unassigned variables. Maintaining arc consistency applies a stronger consistency procedure after each assignment, pruning more search at higher cost per node [17]. Propagation strength is selected by measured total solve performance on representative instances, never by assuming that stronger propagation is always better.

**Search layer**: Systematic backtracking assigns a variable, tries a value, propagates consequences, and recurses; on inconsistency it restores the previous state and tries another value. Exhaustive backtracking is complete for a finite model when allowed to run without pruning errors or resource limits, but the space can grow exponentially, and plain backtracking can repeatedly rediscover the same failure. Ordering heuristics change exploration order without changing model meaning: minimum remaining values selects an unassigned variable with the smallest current domain so that likely failure appears early; a degree tie-breaker prefers the variable constraining the most other unassigned variables; least constraining value tries the value leaving the most options for neighbouring variables. Constraint weighting, conflict-directed backjumping, learned nogoods, restarts, and domain-specific branching may improve difficult instances. Local search begins from a complete, possibly inconsistent assignment and repairs it, with min-conflicts selecting a conflicted variable and assigning the value that minimises current violations [18]. Local search can scale well and adapt from a previous assignment, but ordinary forms are incomplete: failure to find a solution is not proof of infeasibility.

**Optimization layer**: Branch-and-bound uses an incumbent as a bound and prunes branches that cannot improve it. Soft constraints are represented through violation indicators and costs, and the encoding must preserve declared priority semantics rather than flattening a lexicographic policy into a scalar. Core-guided methods identify subsets of temporarily enforced soft constraints that cannot all hold and relax them systematically [19]. Under a deadline, the best independently validated feasible incumbent is retained and reported with its bound or optimality gap where the backend supplies one. An incumbent is never labelled optimal unless optimality was proven.

Two model-strengthening devices sit alongside these layers and carry a specific hazard. Symmetry breaking removes interchangeable solutions differing only by arbitrary labels, such as swapping two identical resources; an unsound breaker silently removes valid solutions. Implied constraints restate logical consequences in forms that strengthen propagation and must themselves be entailed by the original model. Both are hypotheses to validate against small exhaustive instances, never trusted requirements, and this applies with particular force to any strengthening constraint proposed by a language model [20].

**Terminal status semantics**: A solving run answers one of several different questions, and the answers are not interchangeable. Constraint backends commonly expose a status vocabulary distinguishing a feasible solution found, a proven optimum, proven infeasibility, an invalid model, and an unknown outcome in which a time, memory, or custom limit stopped the run before either a solution or a proof was obtained [12]. A stopped solver does not imply infeasibility, and a found solution does not imply optimality. AI agents must normalise backend statuses into an application status vocabulary and must never collapse distinct statuses into a single success or failure flag.

### 1.3 Relationship to Neighbouring Agent Patterns

Constraint Satisfaction Planning is defined by the question it answers: which values can be assigned to decision variables so that hard restrictions hold, and which feasible assignment best serves declared preferences. Neighbouring planning patterns answer different questions and frequently invoke constraint solving as a bounded subroutine.

**Goal decomposition** decides which outcomes and measurable subgoals should exist, converting a broad intent into coverage targets, response thresholds, readiness conditions, and retention requirements. It does not decide the exact assignment of resources to slots. Once decomposition produces explicit tasks and requirements, constraint solving allocates times, actors, and resources. The separation prevents a solver from optimizing a precisely stated version of the wrong objective.

**Hierarchical task network planning** decides which authorized procedural decomposition turns a compound task into executable primitive tasks, selecting a valid method. Constraint solving then schedules the selected primitive tasks and allocates scarce resources among them. A solver belongs inside a method when that method creates a difficult temporal or allocation subproblem; a constraint model is not the place to invent procedural domain knowledge that belongs in the method library.

**Task management and orchestration** governs the lifecycle after tasks exist: eligibility, assignment, lease, dispatch, retry, completion, compensation, and escalation. Constraint solving computes a proposed schedule or allocation from current capacity and deadlines; orchestration makes the proposal operational, rechecks real preconditions, observes execution, and triggers incremental re-solving when facts change. The solver's assignment is a proposal, never the authoritative record of execution.

**Meta-reasoning** selects and monitors reasoning strategies, deciding whether a case merits a dedicated solver, a cheaper heuristic, a clarification step, a simulation, or human review, and whether a solver budget should be increased or a run stopped when marginal improvement is small. Constraint solving performs the selected computation; it does not decide whether that computation is worth running.

**Plan and execution decoupling** produces an action sequence or dependency graph before execution. Constraint solving populates times, actors, routes, or resources within that graph. Both the plan and its assignment can become stale, so solver assumptions are revalidated immediately before consequential actions and control returns to planning when observed state diverges.

**Scenario planning** represents several plausible external futures and seeks strategies acceptable across them. A deterministic constraint model solves one declared instance; robust or stochastic extensions solve across scenarios, reserve slack, or optimize expected and worst-case performance. A single nominal solution is not robust merely because it is feasible under one forecast.

**World-model simulation** predicts how candidate actions change an environment and can supply travel times, durations, failure probabilities, and future resource states to a constraint model. The solver then enforces combinatorial restrictions over those estimates. Prediction error remains a separate risk: a mathematically valid schedule fails when the simulated durations were wrong.

**Plan and todo recitation** keeps a working plan salient in an agent's context and may prompt the agent to formulate, solve, validate, and hand off. It is not the constraint store and not solver state. The authoritative model, incumbent, validation result, and execution record must survive outside any conversational context window.

### 1.4 Applicability Boundaries

**Conditions favouring adoption**: Constraint Satisfaction Planning applies when decisions are discrete or discretizable, when many restrictions interact, and when a candidate solution can be checked mechanically. Representative fits include staff and meeting scheduling, task-to-actor allocation, room and equipment assignment, production sequencing, product configuration, deployment placement, fleet and vehicle routing, portfolio or bundle selection, examination timetabling, and multi-actor coordination under capacity, locality, permission, or safety rules [11].

**Conditions favouring a dedicated solver over informal reasoning**: interacting constraints numerous enough that informal reasoning is fragile; a missed hard constraint carrying material cost; feasibility that must be established repeatedly; alternatives that must be compared consistently; infeasibility that must be diagnosed; optimality or a bound that matters; or one model solved across many instances. A solver is especially valuable when a change in one assignment has nonlocal consequences, such as one task consuming an actor's capacity and thereby moving several downstream deadlines.

**Conditions favouring a hybrid**: natural language is needed to elicit or interpret requirements, but exact combinatorial reasoning is needed afterwards. A language model interviews the requester, normalises names, proposes candidate variables, maps free-text preferences to registered constraint templates, and explains a result. Deterministic code validates types and units, the solver establishes feasibility, and the rendered explanation carries constraint identifiers and evidence rather than unsupported rationale.

**Exclusion, trivial low-risk instances**: A small case with fewer than 5 interacting constraints, where direct reasoning followed by a simple checker is faster and equally reliable, does not warrant a production constraint service. The checker is retained regardless, because simplicity of reasoning does not excuse violating a hard requirement.

**Exclusion, primarily creative tasks**: Where success cannot be represented as checkable restrictions or objectives, a solver can enforce only the formalizable part, such as length, required elements, forbidden terms, or publication windows. It cannot determine whether an artifact is persuasive or a strategy is wise.

**Exclusion, undefined or contested requirements**: Where constraints are unstated, disputed, or changing faster than a model can be authorized and solved, clarification, decomposition, policy review, or an interactive configurator precedes modelling. A solver proves properties of the model it received, not of unstated stakeholder intent.

**Exclusion, strongly nonlinear continuous dynamics**: Forcing continuous dynamics into a crude finite discretisation merely to use familiar tooling produces convincing but unusable answers. Mixed-integer, nonlinear, control-theoretic, simulation, or domain-specific methods apply instead [21].

**Exclusion, hard real-time control loops**: Where the control deadline is shorter than predictable solver latency, policies or feasible envelopes are precomputed, a bounded heuristic runs at execution time, and constraint solving is reserved for slower supervisory replanning. A solver is also excluded wherever its result cannot be validated or where no safe response exists for an unknown terminal status.

***

## II. Operational Framework: Modelling, Solving, and Governing Constrained Assignments

### Phase 1: Problem Admission and Solve Contract Definition

**Objective**: Establish that the decision problem is admissible, fix the planning boundary and the contract the solving run must satisfy, and open an immutable run record before any model is constructed.

#### Step 1.1: Establish the Planning Boundary and Accountability

**Required Actions**:

- State exactly which decisions the solver may make and which facts arrive from authoritative systems, listing each decision class and each fact class separately.
- Identify the parent goal, the upstream planner supplying tasks and requirements, the downstream orchestrator that will execute the result, and the accountable requester.
- Enumerate permitted side effects, and confirm that the solving run returns assignments and evidence rather than executing consequential actions directly.
- Record the human approval points, the risk tier of the decision, and the authority under which any relaxation could later be considered.
- Reject the request when the boundary cannot be stated, when no accountable requester exists, or when the requested decision class falls outside the exclusions in Section 1.4.

**Required Outputs**:

- A planning boundary statement listing solver-controlled decision classes and system-supplied fact classes.
- A named accountability record covering requester, upstream planner, downstream orchestrator, and approvers.
- A risk tier assignment with the approval points it triggers.

**Quality Checkpoints**:

- Every decision class in the boundary statement is controllable by the requesting organisation; classes controlled by external parties are recorded as facts, not variables.
- The boundary statement contains 0 side effects that write to production systems during solving.
- Requests failing any admission condition are rejected before modelling begins, with the failing condition named.

***

#### Step 1.2: Declare the Outcome Contract and Resource Budgets

**Required Actions**:

- Select exactly one primary contract from any feasible solution, best solution within budget, proven optimum, enumeration of alternatives, proof of infeasibility, or extension of a partial assignment.
- Declare the acceptable terminal statuses, and state the handling policy for each, including the response to an unknown status.
- Set wall-clock, processor-time, and memory budgets, plus a target optimality gap expressed as a percentage of the best bound.
- Set token and monetary budgets for any language-model-assisted modelling, and set a bound on the number of clarification rounds.
- Define what happens when no incumbent is found within budget, naming the fallback, the escalation target, and the maximum escalation latency.

**Required Outputs**:

- A solve contract record naming one primary contract and its acceptance condition.
- A budget record covering time, memory, gap tolerance, token spend, and clarification rounds.
- A no-incumbent policy naming the fallback path and the escalation target.

**Quality Checkpoints**:

- Exactly 1 primary contract is declared; multiple simultaneous primary contracts are rejected as ambiguous and returned for clarification.
- Every declared budget carries a numeric bound; an unbounded budget is treated as an admission failure and the run does not open.
- The target optimality gap is stated numerically, with a default of 1.0% relative gap where the requester states none, and a run reaching the gap terminates rather than continuing to a proof.
- The unknown-status policy names a safe response; where no safe response exists, the request is refused under the Section 1.4 exclusion.

***

#### Step 1.3: Open the Solve Run and Freeze Run Metadata

**Required Actions**:

- Create a run identifier, a parent workflow identifier, correlation identifiers, and a monotonic event sequence counter.
- Capture the request text, the objective contract, the risk tier, the deadline, the data snapshot reference, the model and solver versions, the random seed, the compute budgets, the required approvals, and the allowed relaxation authority.
- Initialise the solve generation counter at 1, and bind every subsequent artifact to a generation number.
- Write the run record to append-only storage before any model construction begins.

**Required Outputs**:

- An open run record carrying identifiers, contract, budgets, versions, seed, and authority.
- An initialised solve generation counter bound to the run.

**Quality Checkpoints**:

- Run metadata is immutable for the life of the generation; any change to contract, budget, or authority increments the generation counter rather than overwriting fields.
- The random seed is recorded before the first solver invocation, so that repeated runs are reproducible to within the backend's declared nondeterminism.
- The run record is persisted outside any conversational context and survives a context reset with 100% of its fields intact.

***

### Phase 2: Model Construction From Authoritative Inputs

**Objective**: Convert the admitted request into a canonical input snapshot, a set of decision variables with sound domains, and a versioned constraint registry, so that every element of the model traces to an authoritative source.

#### Step 2.1: Canonicalise Inputs and Freeze the Authoritative Snapshot

**Required Actions**:

- Retrieve calendars, capacities, skills, permissions, topology, deadlines, costs, and prior commitments from systems of record.
- Assign every entity a stable identifier, type, unit, timezone, provenance reference, freshness timestamp, and version.
- Normalise intervals, boundary conventions, rounding, currency, capacity units, and calendar rules to one declared convention before construction.
- Reject ambiguous identifiers, duplicate identifiers, and mixed units, and stop rather than guessing a resolution.
- Where a required source is unavailable or stale beyond the declared freshness threshold, either retrieve it through an authorized step or solve an explicitly labelled scenario, and never present a scenario result as current reality.
- Convert the natural-language request into registered entities, marking every extracted item as confirmed, inferred, ambiguous, conflicting, or missing.

**Required Outputs**:

- A frozen input snapshot with a canonical hash and per-source provenance and freshness records.
- A normalisation record naming the unit, timezone, and boundary conventions applied.
- An extraction ledger classifying every requirement item by confidence class.

**Quality Checkpoints**:

- 100% of entities carry an identifier, a unit, and a freshness timestamp; entities missing any of the three are excluded from the model and reported.
- Input freshness is within the declared threshold, defaulting to 15 minutes for volatile availability data and 24 hours for structural data; breaching the threshold halts the run pending refresh or explicit scenario labelling.
- Every item marked ambiguous or conflicting that can change feasibility or policy is resolved by the owner or by a preauthorized conservative interpretation before Step 2.2; unresolved items above 0 in count halt progression.
- Deterministic schema and registry checks accept the extraction result; language-model output is never admitted to the model without passing those checks.

***

#### Step 2.2: Declare Decision Variables and Construct Sound Domains

**Required Actions**:

- Create one variable for each real controllable choice, recording its identifier, type, interpretation, nullable behaviour, and the business entity it controls.
- Eliminate duplicate variables representing the same decision unless an explicit equality constraint and a recorded reason exist.
- Construct each domain by intersecting technical type ranges with availability, eligibility, authorization, and known physical bounds.
- Record the source and reason for every domain value removal, so that no reduction is unexplained.
- Introduce an explicit unassigned or rejected value only where partial service is permitted, and mark it as visibly penalised rather than free.
- Apply sound unary restrictions and record initial and reduced domain sizes per variable.

**Required Outputs**:

- A variable registry with identifier, type, interpretation, and controlled entity per entry.
- A domain construction record with initial size, reduced size, and a justification per removed value class.
- A declared optionality policy naming which variables may take an unassigned value.

**Quality Checkpoints**:

- Every variable maps to exactly 1 controllable decision; variables representing known facts are reclassified as input data before solving.
- Every domain reduction carries a recorded source; unexplained reductions are reverted, because an unjustified removal can delete the only solution.
- Any variable whose domain exceeds 10,000 candidate values is flagged for reformulation or decomposition before search, since unbounded domains inflate search without improving the answer.
- Any variable with an empty domain after unary restriction routes directly to the diagnostic path in Phase 6 rather than to general search.

***

#### Step 2.3: Register Constraints as Versioned Objects

**Required Actions**:

- Create one registry entry per constraint carrying a stable identifier, a natural-language meaning, a formal template with bound parameters, a scope, a severity, an owner, a provenance reference, effective dates, and test cases.
- Classify each restriction as hard, soft, conditional, or advisory, and record the classification authority.
- For each soft constraint, record penalty, priority, unit, cap, and the approver of the trade-off.
- For each hard constraint that could ever be relaxed, define a separate relaxation policy naming the approver, and never permit the solver to demote it implicitly.
- Separate source requirements from derived implied constraints and from solver-only symmetry breakers by tagging each entry with its origin class.
- Validate types and referenced identifiers for every instantiated constraint, and retain both rules where two authoritative rules conflict rather than selecting one.

**Required Outputs**:

- A constraint registry with a complete metadata record per constraint.
- A hardness classification table listing each restriction with its severity, authority, and relaxation policy.
- A requirement-to-constraint coverage map linking each source requirement to at least one registry entry.

**Quality Checkpoints**:

- 100% of registry entries carry an identifier, an owner, a provenance reference, and an origin class; entries missing any field are not instantiated into the model.
- 0 safety, legal, permission, or physical restrictions are encoded as finite penalties; any such encoding is a blocking modelling defect.
- Every source requirement maps to at least 1 constraint in the coverage map; uncovered requirements above 0 in count halt progression to Phase 3.
- Conflicting authoritative rules are both retained and reported; selecting one on the basis of model fluency is prohibited.

**Constraint registry record template**:

```
CONSTRAINT_ID:
VERSION:
NATURAL_LANGUAGE_LABEL:
FORMAL_TEMPLATE:
BOUND_PARAMETERS:
SCOPE_VARIABLES:
HARDNESS:            HARD | SOFT | CONDITIONAL | ADVISORY
PRIORITY_OR_WEIGHT:
UNIT:
OWNER:
AUTHORITATIVE_SOURCE:
EFFECTIVE_FROM:
EFFECTIVE_TO:
ORIGIN_CLASS:        ORIGINAL | DERIVED | IMPLIED | SYMMETRY_BREAKING
RELAXATION_POLICY:
APPROVAL_REQUIRED:
TEST_CASE_REFERENCES:
```

***

### Phase 3: Objective Policy, Model Strengthening, and Pre-Runtime Assurance

**Objective**: Fix the ranking policy over feasible assignments, strengthen the model only with devices proven sound, and construct the independent validator, diagnostic path, and offline test corpus before any production solve is permitted.

#### Step 3.1: Define Objectives, Tie-Breaking, and Relaxation Authority

**Required Actions**:

- Specify each objective term with its direction, scaling, unit, and aggregation rule.
- Select one multi-objective policy from lexicographic priority, weighted aggregation, or enumeration of non-dominated alternatives, and record who approved it.
- Add deterministic tie-breakers where reproducibility matters, so that equal-objective assignments resolve identically across runs.
- Produce a plain-language objective summary that a reviewer can read to detect inverted signs, double counting, or hidden trade-offs before solve time.
- Test whether weights create unintended compensation between unrelated preferences and whether large coefficients introduce numeric or search problems.

**Required Outputs**:

- An objective specification with direction, scaling, unit, and aggregation per term.
- A declared multi-objective policy with named approver.
- A plain-language objective summary suitable for non-technical review.

**Quality Checkpoints**:

- Every weight is traceable to a stakeholder approval record; arbitrary weights are rejected, because weights encode policy.
- Lexicographic priorities, where declared, are preserved in the encoding and reported per level rather than collapsed into a single scalar.
- The largest objective coefficient does not exceed the smallest non-zero coefficient by a factor greater than 10,000 without a recorded numeric-stability review, since wider ranges risk coefficient dominance and precision loss.
- The plain-language summary is reviewed and accepted before solving; an unreviewed objective halts progression.

***

#### Step 3.2: Apply Global, Implied, and Symmetry-Breaking Constraints

**Required Actions**:

- Replace collections of weak pairwise constraints with an appropriate global constraint wherever the backend supports one that expresses the real structure.
- Verify the semantics of every global constraint against the requirement it is intended to encode before adopting it.
- Prove or exhaustively test every implied constraint and every symmetry breaker against small instances whose full solution set is enumerable.
- Tag each added device with its origin class so that later diagnosis can distinguish a business conflict from a modelling technique.
- Remove any strengthening device whose exhaustive test removes a legitimate solution, and record the removal.

**Required Outputs**:

- A model-strengthening record listing each global, implied, and symmetry-breaking device with its verification evidence.
- An exhaustive test result set for each device, naming the instance size tested and the solution counts before and after.

**Quality Checkpoints**:

- Every implied constraint and symmetry breaker is validated against at least 3 exhaustive small instances whose complete solution sets are enumerated; a device failing on any instance is removed.
- Solution counts on exhaustive instances are unchanged by implied constraints and reduced only by intended symmetry classes; an unexplained reduction is treated as an unsound device and reverted.
- 0 strengthening devices proposed by a language model enter the model without passing the same exhaustive test as any other device.
- Every strengthening device carries an origin class tag distinguishing it from an original requirement.

***

#### Step 3.3: Construct the Independent Validator, Diagnostic Path, and Offline Test Corpus

**Required Actions**:

- Implement the acceptance check on a separate path from the model-building code, so that a shared defect cannot pass both.
- Specify the validator to recompute every hard constraint from authoritative inputs and the returned assignment, verify domain membership, verify completeness, recalculate objective components, and emit violations by constraint identifier.
- Make selected constraints reifiable or assumption-controlled so that subsets can be enabled, disabled, or labelled for conflict isolation and controlled what-if analysis.
- Map backend core literals back to user-facing requirement identifiers wherever the backend supports unsatisfiable cores.
- Build an offline corpus containing known feasible instances, known infeasible instances, boundary values, duplicate identifiers, empty domains, zero capacity, conflicting calendars, daylight-saving transitions, missing data, dominated preferences, equivalent resources, and large stress instances.
- Mutate or remove one constraint at a time across the corpus to measure validator sensitivity, and compare results against hand-checked tiny instances and a simple baseline heuristic.
- Version the entire solving contract, recording model schema, data snapshot, constraint registry, objective, solver, parameters, validator, prompt, tool, and relaxation-policy versions.

**Required Outputs**:

- An independent validator specification with its check inventory and violation reporting format.
- A diagnostic model path exposing assumption controls and a core-literal to requirement-identifier mapping.
- An offline test corpus with expected outcomes per instance and a recorded validator sensitivity result.
- A solving contract version manifest covering all named components.

**Quality Checkpoints**:

- The validator recomputes 100% of hard constraints from authoritative inputs; a validator that reuses model-building code for any hard constraint is rejected as non-independent.
- Single-constraint mutation is detected by the validator in at least 95% of mutated instances; detection below that threshold blocks deployment until the validator is extended.
- The offline corpus contains at least 1 instance per fault class named in the actions list; missing fault classes block deployment.
- The version manifest is complete, because a performance change is uninterpretable when the workload or model changed invisibly.

***

### Phase 4: Solver and Method Selection

**Objective**: Choose the least complicated method that can satisfy the declared contract, matched to model structure rather than to familiarity, and configure its propagation, search, and bounding parameters with a recorded rationale.

#### Step 4.1: Characterise the Instance and Select a Method Class

**Required Actions**:

- Measure instance features including variable count by type, total domain-value count, constraint count by type and hardness, global constraint use, constraint graph density, connected component count, and objective term count.
- Determine whether the contract requires a proof, and eliminate incomplete methods where a proof of infeasibility or optimality is contractually required.
- Match the measured structure to a method class using the selection matrix below.
- Prefer a dedicated domain library where it directly represents the structure and its tested neighbourhood moves outperform a generic formulation.
- Adopt a portfolio or hybrid approach only where measurement shows that instance features route work effectively; otherwise reject it as operational complexity without reliable gain.

**Required Outputs**:

- An instance feature record with measured values for every named feature.
- A selected method class with a written rationale referencing the measured features.
- A statement of what the selected method's failure status can and cannot prove.

**Quality Checkpoints**:

- The selection rationale cites at least 3 measured instance features; a selection justified only by team familiarity is rejected.
- Incomplete methods are excluded wherever the contract requires proof of infeasibility or optimality; selecting one under such a contract is a blocking defect.
- The failure-status statement distinguishes proven infeasibility from search failure for the selected method, and this distinction is carried into the result payload.

**Solver and method selection matrix**:

| Method class | Selection condition | Provides proof | Principal risk |
| :-- | :-- | :-- | :-- |
| Custom backtracking with propagation | Small finite problems, teaching instances, highly specialised search, or full control over branching and explanation required | Yes, when exhaustive and correct | Easy to implement incorrectly; requires comparison against a mature solver before production use |
| Constraint-programming solver [23][24] | Discrete decisions with rich logical, scheduling, or global constraints where propagation can exploit combinatorial structure | Yes | Integer-oriented encodings; continuous quantities require discretisation review [12] |
| Mixed-integer linear programming | Variables and constraints naturally linear, strong relaxations valuable, mature optimization features required | Yes | Logical and scheduling structure may require large or weak linearisations |
| Boolean satisfiability solving | Problem is fundamentally Boolean or admits a high-quality Boolean encoding | Yes | Encoding size growth; arithmetic structure is lost |
| Satisfiability modulo theories | Satisfiability depends on theories such as integer or real arithmetic, arrays, bit-vectors, or uninterpreted functions | Yes, with core extraction and incremental assumption control [25] | Theory combination cost; optimization support varies by backend |
| Dedicated routing or scheduling library | Domain structure is directly represented and tested neighbourhood moves exist for it | Partial; depends on the library's search mode | Domain fit must be verified; generic constraints may be awkward to add |
| Local search including min-conflicts | Complete assignment is easy to construct, repair is meaningful, instances are large, and a fast feasible answer outranks a proof | No | Failure is not infeasibility; a systematic solver or an explicit not-proven status must accompany it |
| Portfolio or hybrid | Measurement shows instance features route work effectively across two or more of the above | Depends on constituent members | Operational complexity without reliable gain when routing is unmeasured |

***

#### Step 4.2: Configure Propagation, Search Strategy, and Bounds

**Required Actions**:

- Set the propagation level, choosing between unary and node-level checks, forward checking, arc consistency maintenance, and any stronger consistency the backend offers.
- Measure total solve performance at each candidate propagation level on representative instances rather than assuming stronger propagation is better.
- Set the variable ordering strategy, the value ordering strategy, restart policy, parallelism, and warm-start source.
- Set the enumeration or diversity policy where the contract requires multiple alternatives.
- Set time, node, conflict, memory, and optimality-gap limits, each as an explicit number.
- Record the random seed and every parameter, because heuristics and seeds change latency, the first solution found, and sometimes the returned solution under a time limit.

**Required Outputs**:

- A solver configuration record listing propagation level, ordering strategies, restart and parallelism settings, warm start, and every limit.
- A propagation benchmark record comparing candidate levels on representative instances.

**Quality Checkpoints**:

- The selected propagation level is supported by measurement on at least 5 representative instances; an unmeasured selection is provisional and is revisited after the first 20 production runs.
- Every limit carries a numeric value; an absent limit defaults to the Phase 1 budget, and a configuration with no effective limit is rejected.
- The random seed and thread count are recorded, because nondeterminism that is not recorded cannot be reproduced or compared.

***

#### Step 4.3: Record Selection Rationale and Status Semantics

**Required Actions**:

- Write the rationale connecting measured instance features, the contract, and the chosen method, parameters, and limits.
- Enumerate the backend statuses the selected configuration can return, and map each to a normalised application status.
- State for each normalised status what downstream action is permitted and what claim may be made to the requester.
- Declare the response to an unknown status, naming the fallback and the escalation target.

**Required Outputs**:

- A selection rationale record bound to the solve generation.
- A backend-to-application status mapping table with permitted downstream actions per status.

**Quality Checkpoints**:

- Every backend status the configuration can emit appears in the mapping; an unmapped status halts the run rather than defaulting to failure.
- No normalised status permits consequential execution without a passing independent validation event.
- The mapping never translates a resource-limit termination into an infeasibility claim.

**Normalised terminal status semantics**:

| Normalised status | Meaning | Permitted downstream action |
| :-- | :-- | :-- |
| VALIDATED_FEASIBLE | A complete assignment satisfied every hard constraint under independent validation, optimality not claimed | Handoff permitted with explicit non-optimal labelling |
| PROVEN_OPTIMAL | A validated assignment is optimal under the declared objective and model | Handoff permitted with optimality claim bound to the model version |
| PROVEN_INFEASIBLE | No assignment satisfies the hard constraints of this model generation | Diagnosis and escalation only; no assignment is returned |
| UNKNOWN_WITH_INCUMBENT | A limit terminated the run; a validated incumbent exists without a proof | Handoff permitted as best-known, with bound and gap reported where available |
| UNKNOWN_WITHOUT_INCUMBENT | A limit terminated the run before any incumbent or proof | Escalation only; never reported as no solution |
| MODEL_INVALID | The model failed backend validation | Modelling defect path; never reported as a business infeasibility |
| VALIDATION_FAILED | A solver-feasible assignment failed independent validation | Quarantine and defect investigation; execution blocked |
| CANCELLED | The run was terminated by the requester or by policy | No claim about feasibility is made |

***

### Phase 5: Propagation, Search, and Optimization Execution

**Objective**: Reduce domains before search, obtain a hard-feasible incumbent under declared bounds, validate every incumbent independently, and improve the objective only while the retained best solution remains validated.

#### Step 5.1: Preprocess and Propagate Before Search

**Required Actions**:

- Normalise units and time boundaries, remove exact duplicate constraints, and tighten bounds using the registered domain justifications.
- Run the backend's model validator, and treat an invalid-model status as a modelling defect rather than an infeasible business problem.
- Hash the canonical model and record counts of variables, domain values, constraints by type and hardness, graph density indicators, and objective terms.
- Enforce the selected consistency level, or permit the backend to run its own presolve and propagation, and record values removed, domains emptied, responsible constraints where available, and time spent.
- Skip ordinary search and enter the diagnostic path in Phase 6 whenever propagation empties a domain or proves a contradiction.

**Required Outputs**:

- A canonical model hash with a structural count record.
- A propagation record listing removed values, emptied domains, responsible constraints, and elapsed time.
- A model validation verdict from the backend.

**Quality Checkpoints**:

- The model hash is recorded before search begins, so that repeated identical solves can be detected and suppressed.
- An invalid-model verdict routes to the modelling defect path and never to an infeasibility report.
- Propagation that empties any domain terminates search entry within 1 step and transfers control to diagnosis, because searching an already-contradictory model consumes budget without producing information.
- Propagation time does not exceed 25% of the declared wall-clock budget at the strongest configured level; exceeding it triggers a fallback to the next weaker level with the fallback recorded.

***

#### Step 5.2: Run the Feasibility Loop and Validate Every Incumbent

**Required Actions**:

- Search first for a hard-feasible incumbent, unless the selected backend tightly integrates feasibility and optimization.
- At each branch, select a variable by the configured strategy, try a value, propagate consequences, and continue while all domains remain nonempty.
- On branch failure, record the conflict or reason, restore the prior search state, learn a nogood where the backend supports it, and try the next value.
- Continue until an incumbent appears, infeasibility is proven, or a resource limit fires.
- On each incumbent, serialize the complete assignment, the solver status, the objective components, the bound, the gap, and the assumptions, then run the independent validator before treating it as feasible.
- On a hard violation found by the validator, quarantine the result, classify the cause as model omission, encoding error, stale data, serialization error, or validator defect, and stop automatic execution.

**Required Outputs**:

- A search statistics record covering branches, failures, conflicts, propagations, backtracks, learned nogoods, and restarts.
- A serialized incumbent record with assignment hash, status, objective components, bound, gap, and assumptions.
- An independent validation verdict per incumbent with violations listed by constraint identifier.

**Quality Checkpoints**:

- 100% of incumbents are independently validated before being described as feasible; an unvalidated incumbent is never handed off.
- A solver-feasible assignment failing independent validation is treated as a critical defect even when execution was blocked, and the run does not continue on that model generation.
- The same model is never asked to explain away a discrepancy between solver output and validator output; discrepancies route to the defect path.
- Search statistics unavailable from the backend are recorded as unavailable rather than as zero, because a false zero corrupts later efficiency comparisons.

***

#### Step 5.3: Run the Optimization Loop and Return a Bounded Best-Known Answer

**Required Actions**:

- Preserve the first validated feasible assignment before any optimization step begins.
- Continue branch-and-bound, core-guided optimization, local improvement, or the backend-specific method while the objective improves and budget remains.
- Validate each material incumbent, record the improvement and its timestamp, and atomically replace the retained best solution only after validation passes.
- Stop when optimality is proven, the approved gap is reached, the deadline is reached, improvement stalls under the declared rule, cancellation occurs, or risk policy requires review.
- On deadline expiry with a validated incumbent, return it labelled feasible or best-known, with objective, bound, gap where available, and explicit non-optimal status.
- On deadline expiry without an incumbent and without a proof, return the unknown status and never translate a timeout into a claim that no solution exists.

**Required Outputs**:

- A retained best solution record with validation verdict, objective components, bound, and gap.
- An incumbent trajectory record listing each validated improvement with its time and objective delta.
- A terminal status assignment drawn from the normalised vocabulary.

**Quality Checkpoints**:

- The retained best solution is replaced only after the replacement passes independent validation; replacement on solver status alone is prohibited.
- Optimality is claimed only where the backend proved it; a gap greater than 0 accompanying an optimality claim is a reporting defect that blocks handoff.
- Improvement stall is measured against the declared rule, defaulting to termination when no validated improvement exceeding 0.5% of the current objective occurs within 20% of the remaining budget.
- A timeout with no incumbent produces the unknown status, not an infeasibility claim; any infeasibility claim without a proof is a blocking defect.

***

### Phase 6: Infeasibility Diagnosis and Authorized Relaxation

**Objective**: Convert an absence of solutions into an actionable, source-mapped conflict report, and enlarge the feasible region only through recorded, authorized relaxations under bounded re-solve loops.

#### Step 6.1: Isolate and Classify the Conflict

**Required Actions**:

- Confirm first that the model itself is valid and that the input snapshot is the intended one, so that a defect is not reported as a business conflict.
- Obtain an unsatisfiable core, conflict set, explanation, or deletion-based diagnosis from the backend where supported.
- Map technical literals back to registered constraint identifiers and to source requirements.
- Test whether the conflict persists when constraints outside the candidate set are disabled, and repeat isolation until the report is small enough to act on or the diagnostic budget is reached.
- Classify the conflict as a genuine impossible request, contradictory authoritative rules, bad or stale input, an empty or over-tight domain, an encoding defect, an unintended interaction, or a resource shortage.
- Preserve the original infeasible model, its hash, and its proof status without modification.

**Required Outputs**:

- A conflict package listing constraint identifiers, source requirements, and the isolation evidence.
- A conflict classification with a named suspected cause and a recommended owner.
- A preserved infeasible model reference bound to the solve generation.

**Quality Checkpoints**:

- At least 80% of conflict-set members map to named source requirements; below that threshold the package is extended before it reaches a decision owner, because unmapped solver literals are rarely actionable.
- The conflict package contains no more than 12 constraints, or records why further isolation was not possible within the diagnostic budget.
- The classification distinguishes a modelling defect from a business conflict; ambiguity between the two routes to the defect path first.
- The original infeasible model is retained unmodified; overwriting it is a blocking audit defect.

***

#### Step 6.2: Apply Controlled Relaxation Under Declared Authority

**Required Actions**:

- Generate relaxation candidates only from declared soft constraints and preapproved relaxation policies.
- Prefer relaxing lower-priority preferences, widening explicitly flexible bounds, introducing optional unassignment with a visible penalty, or requesting additional resources, in that order.
- Record for each candidate the changed constraint, the magnitude, the authority, the predicted consequence, and the affected stakeholders.
- Obtain the named approval before applying any relaxation that crosses a declared authority boundary.
- Refuse any candidate that removes a safety, legal, permission, or physical constraint in order to force feasibility.
- Correct the classification through governance where a preference was accidentally encoded as hard, rather than silently editing the model.

**Required Outputs**:

- A relaxation candidate set with magnitude, authority, predicted consequence, and stakeholder impact per candidate.
- An approval record naming the approver and the scope of the approved change.
- A rejection record for candidates refused on authority grounds.

**Quality Checkpoints**:

- 0 relaxations of safety, legal, permission, or physical constraints are applied; any such proposal is refused and logged as a governance event.
- Every applied relaxation carries a named approver; an unapproved relaxation is a blocking governance defect and invalidates the resulting assignment.
- Relaxation is attempted only after diagnosis; deleting constraints before a conflict set exists is prohibited.
- A conflict set is never treated as a decision about which rule should change, because it proves only joint unsatisfiability.

***

#### Step 6.3: Re-Solve Under Generation Control and Loop Bounds

**Required Actions**:

- Increment the model generation, preserve the prior infeasible model and its diagnostic package, and apply only the approved relaxation.
- Warm-start from a prior assignment only after validating that assignment against the new model.
- Return to preprocessing and propagation, and repeat the feasibility loop under the remaining budget.
- Detect repeated model hashes and identical failure signatures, and stop rather than repeating an identical attempt.
- Escalate or close the run as infeasible when no authorized relaxation yields feasibility within the loop bounds.

**Required Outputs**:

- A new model generation record referencing the prior generation and the applied relaxation.
- A re-solve outcome record with terminal status, elapsed budget, and validation verdict.
- An escalation package where no authorized relaxation restores feasibility.

**Quality Checkpoints**:

- Relaxation rounds do not exceed 3 per run by default; reaching the bound escalates rather than continuing, because further rounds indicate a policy problem rather than a search problem.
- Identical retries are suppressed when model hash, data version, parameters, and failure signature are unchanged; repeating an identical attempt is a budget defect.
- Oscillation between two model hashes across 2 consecutive generations triggers escalation rather than a third attempt.
- Every re-solve preserves the prior generation's model and diagnostic; overwriting history is prohibited.

***

### Phase 7: Robustness Testing, Handoff, and Execution Monitoring

**Objective**: Establish that the selected assignment survives plausible variation, transfer it to execution with expiring reservations and revalidated preconditions, and manage incremental re-solving as observed reality diverges from solver assumptions.

#### Step 7.1: Test Robustness Before Consequential Handoff

**Required Actions**:

- Perturb declared uncertain quantities, including durations, demand, availability, costs, and travel times, within plausible ranges drawn from the declared uncertainty model.
- Re-solve representative perturbed scenarios, or test whether the retained incumbent preserves slack against each perturbation.
- Record hard-feasibility survival, objective degradation, assignment churn, minimum slack, and the binding constraints under each scenario.
- Keep clean, stress, and adversarial cohorts distinct so that degradation is attributable.
- Where small plausible changes destroy feasibility, reserve slack, select a slightly worse but more stable assignment, prepare contingencies, or require human approval before handoff.

**Required Outputs**:

- A robustness result set with feasibility, objective, churn, and slack per perturbed scenario.
- A binding-constraint summary naming the restrictions that limit the assignment.
- A stability decision recording whether the nominal assignment, a slack-preserving alternative, or an escalation was selected.

**Quality Checkpoints**:

- The perturbation suite covers at least 5 distinct uncertainty dimensions declared in the input snapshot; fewer dimensions blocks the robustness claim.
- Hard-feasibility survival across the perturbation suite is at least 90% for consequential handoffs; below that threshold, handoff requires either a slack-preserving alternative or explicit human approval.
- No assignment is described as robust on the basis of feasibility under a single forecast.
- Objective degradation and churn are reported per scenario rather than averaged into a single figure that hides tail behaviour.

***

#### Step 7.2: Produce the Explanation Package and Hand Off to Orchestration

**Required Actions**:

- State the solver status, the assignment, the hard constraints checked, the soft constraints satisfied and violated, the objective components, the optimality claim or gap, the major binding constraints, the relaxations applied, the assumptions, the input freshness, the sensitivity results, and alternative assignments where requested.
- Express every explanation element using constraint identifiers and source-backed facts rather than narrative rationale.
- Create versioned tasks or reservations from the validated assignment, each carrying an expiration time and the state changes that invalidate it.
- Require the orchestrator to recheck permissions, availability, deadlines, and other volatile preconditions immediately before execution.
- Withhold private reasoning traces, and never imply that the solver considered values that were not in the model.

**Required Outputs**:

- An explanation package with every named element populated or explicitly marked unavailable.
- A set of versioned reservations or tasks with expiration times and invalidation triggers.
- An orchestrator acknowledgement record.

**Quality Checkpoints**:

- 100% of explanation claims reference a constraint identifier or an authoritative input; unsupported rationale is removed before release.
- Every reservation carries an expiration time, defaulting to 30 minutes for volatile resources and 24 hours for structural commitments, after which the reservation lapses rather than persisting silently.
- Handoff occurs only after a passing independent validation event; solver output is never passed directly to consequential tools.
- The orchestrator's precondition recheck is a required step; a handoff accepted without recheck is a governance defect.

***

#### Step 7.3: Monitor Execution, Trigger Incremental Re-Solving, and Close the Run

**Required Actions**:

- Compare observed state with solver assumptions whenever a task finishes, fails, or overruns, a resource disappears, a deadline moves, or a new requirement arrives.
- Preserve completed and irreversible decisions as fixed facts, release obsolete reservations, update only the affected facts where possible, and increment the solve generation.
- Return to input refresh or variable instantiation, and validate every reused assignment under the new model before adopting it.
- Penalise unnecessary changes to preserve stability, while never freezing a value that has become invalid under a new hard constraint.
- Bound the re-solving loop with limits on re-solve count, wall time, solver processor time, tokens used for reformulation, relaxation rounds, and assignment churn.
- Declare verified success only when the selected assignment passes independent validation and the handoff is acknowledged, then emit the final model generation, solution and validation hashes, terminal status and reason, objective and gap, relaxations, robustness results, costs, and lineage.
- For any non-success closure, identify whether the result is infeasible, unknown, invalid, cancelled, or escalated, and state the information, authority, or resource required next.

**Required Outputs**:

- A re-solve event record per trigger, with changed facts, fixed decisions, released reservations, churn, and validation verdict.
- A loop-bound record showing consumed and remaining limits.
- A closure record with terminal status, hashes, costs, and artifact lineage.

**Quality Checkpoints**:

- Completed or irreversible decisions are never rewritten by a re-solve; only remaining degrees of freedom are replanned.
- Re-solves do not exceed 5 per execution window by default; reaching the bound escalates rather than continuing, because rapid re-solving indicates unstable inputs rather than a search problem.
- Warm-started assignments are validated against the current model before reuse; reusing a stale assignment without validation is a blocking defect.
- Closure declares verified success only on a passing validation plus an acknowledged handoff; any other outcome is closed under its specific non-success status with the next required input named.

***

## III. Implementation Guidance for AI Agents

AI agents executing Constraint Satisfaction Planning must follow systematic protocols that separate language competence from combinatorial competence, bound every loop numerically, and route every candidate assignment through an independent validator before any consequential action. The following guidance translates the operational framework above into agent-executable instruction.

### A. Structured Execution Protocol

**The division of labour that must not be violated**: A language model must not be trusted to perform constraint propagation, feasibility determination, conflict isolation, or optimality proof by itself. This is an architectural constraint, not a preference. Fluent output describing a schedule as satisfying all constraints is not a feasibility certificate, and re-sampling several language-model answers does not substitute for an exact validator, because independently sampled answers can share the same omitted rule. Language models may extract candidate entities and constraints, select from registered constraint templates, draft a model in a declarative modelling language [22], propose heuristics, explain a conflict set in ordinary language, or translate a validated assignment into a readable summary. Typed deterministic code checks the draft, a solver executes it, and an independent validator checks the resulting solution against the source requirements [26]. Successful execution of generated solver code is never proof that the original natural-language request was modelled completely [27], and human approval remains required for policy interpretation and for consequential relaxation.

**Control Plane Components**:

1. **Admission Agent**: Owns Phase 1. Evaluates the request against the applicability boundaries in Section 1.4, fixes the planning boundary and solve contract, sets every budget, and opens the immutable run record. Refuses requests carrying no accountable requester, no numeric budget, or no safe response to an unknown status.
2. **Modelling Agent**: Owns Phases 2 and 3. Canonicalises inputs, declares variables and domains, populates the constraint registry, defines the objective policy, and applies only verified strengthening devices. Holds no authority to change constraint hardness.
3. **Method Selection Agent**: Owns Phase 4. Measures instance features, selects a method class against the selection matrix, configures propagation and search, and publishes the backend-to-application status mapping. Eliminates incomplete methods wherever the contract requires a proof.
4. **Solving Agent**: Owns Phase 5. Executes preprocessing, propagation, feasibility search, and optimization within declared limits, and serializes every incumbent with its statistics. Holds no authority to declare a result feasible.
5. **Validation Agent**: Owns the independent validator across all phases. Recomputes every hard constraint from authoritative inputs, verifies domain membership and completeness, recalculates objective components, and issues the only verdict that permits handoff. Implemented on a code path separate from the Modelling Agent.
6. **Diagnosis and Governance Agent**: Owns Phase 6. Isolates and classifies conflicts, maps cores to source requirements, proposes relaxation candidates within declared authority, and routes anything beyond that authority to a named human approver.
7. **Handoff and Monitoring Agent**: Owns Phase 7. Runs the perturbation suite, assembles the explanation package, creates expiring reservations, watches for divergence between observed state and solver assumptions, and triggers bounded incremental re-solving.

**Phase transition conditions**:

- Phase 1 to Phase 2 requires an accountable requester, exactly 1 declared primary contract, and numeric values for every budget.
- Phase 2 to Phase 3 requires 0 unresolved feasibility-affecting ambiguities, 0 uncovered source requirements in the coverage map, and 0 entities missing an identifier, unit, or freshness timestamp.
- Phase 3 to Phase 4 requires an independent validator that detects at least 95% of single-constraint mutations, an offline corpus covering every declared fault class, and a complete version manifest.
- Phase 4 to Phase 5 requires a selection rationale citing at least 3 measured features, numeric values for every solver limit, and a status mapping covering every emittable backend status.
- Phase 5 to Phase 6 occurs on proven infeasibility, on an emptied domain during propagation, or on a validation failure; it does not occur on a timeout, which routes to bounded best-known reporting instead.
- Phase 5 to Phase 7 requires a retained best solution carrying a passing independent validation verdict.
- Phase 6 to Phase 5 requires an approved relaxation, an incremented generation, and a model hash differing from every prior generation in the run.
- Phase 7 closure requires a passing validation verdict plus an orchestrator acknowledgement, or a named non-success status with its next required input.

**Approval gate**: Autonomous progression is permitted through model construction, method selection, solving, validation, diagnosis, and reporting. Human authorisation is required before any of the following: applying a relaxation that changes constraint hardness; applying a relaxation whose magnitude exceeds the preapproved bound recorded in the constraint registry; handing off an assignment whose hard-feasibility survival across the perturbation suite falls below 90%; handing off under a risk tier that names an approver; and closing a run as infeasible where the conflict maps to contradictory authoritative rules. Agents must not seek an alternative path around a gate by reclassifying a constraint, widening a domain with impossible values, or reinterpreting an ambiguous requirement in the direction that restores feasibility.

**Workflow Execution Pattern**:

```
STATE: Phase_5_Solving_Execution
PRECONDITIONS:
  - model_hash_recorded == TRUE
  - all_solver_limits_numeric == TRUE
  - status_mapping_complete == TRUE
ACTIONS:
  1. Run presolve and propagation at configured level
  2. Record removed values, emptied domains, elapsed time
  3. Search for hard-feasible incumbent under limits
  4. Serialize incumbent with status, objective, bound, gap
  5. Invoke independent validator on every incumbent
  6. Retain best validated incumbent atomically
VALIDATION:
  - emptied_domain_count == 0
  - validator_verdict == PASS for retained incumbent
  - optimality_claimed IMPLIES proof_present == TRUE
TRANSITIONS:
  IF emptied_domain_count > 0 THEN next_state = Phase_6_Diagnosis
  ELSE IF validator_verdict == FAIL THEN next_state = Defect_Quarantine
  ELSE IF terminal_status == PROVEN_INFEASIBLE THEN next_state = Phase_6_Diagnosis
  ELSE IF retained_incumbent_present == TRUE THEN next_state = Phase_7_Handoff
  ELSE next_state = Escalate_Unknown_Without_Incumbent
```

**Context management requirements**: The authoritative model, constraint registry, incumbent, validation verdict, diagnostic package, and execution record are persisted outside any conversational context and are never reconstructed from a transcript. Agents load one phase's working set at a time. Where the constraint registry exceeds the working context, agents load the coverage map and fetch individual registry entries by identifier rather than holding the full registry. Backtracking restores logical search state; it must never erase audit history.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Admission Integrity (After Phase 1)**

- **Automated Check**: Exactly 1 primary contract declared; every budget carries a numeric bound; accountable requester named; unknown-status response defined; risk tier assigned.
- **Agent Action on Pass**: Open the run record and proceed to model construction.
- **Agent Action on Failure**: Halt and return the specific admission defect without opening a run.
- **Human Review Trigger**: The requested decision class falls within any Section 1.4 exclusion, or no safe response exists for an unknown terminal status.

**Checkpoint 2: Model Integrity (After Phase 2)**

- **Automated Check**: 100% of entities carry identifier, unit, and freshness timestamp; 100% of registry entries carry identifier, owner, provenance, and origin class; 0 mandatory rules encoded as finite penalties; 0 uncovered source requirements; 0 variables with an empty domain.
- **Agent Action on Pass**: Proceed to objective policy and model strengthening.
- **Agent Action on Failure**: Return the failing entities or registry entries only, and re-run construction for those entries.
- **Human Review Trigger**: Two authoritative sources conflict and the declared source-of-authority policy does not resolve the conflict, or more than 10% of extracted requirements are marked ambiguous.

**Checkpoint 3: Assurance Readiness (After Phase 3)**

- **Automated Check**: Validator detects at least 95% of single-constraint mutations; every strengthening device passes at least 3 exhaustive small-instance tests; offline corpus covers every declared fault class; version manifest complete; objective summary reviewed.
- **Agent Action on Pass**: Proceed to method selection.
- **Agent Action on Failure**: Halt; a model may not be solved in production against an unproven validator.
- **Human Review Trigger**: A strengthening device reduces the solution count on an exhaustive instance and the reduction cannot be attributed to an intended symmetry class.

**Checkpoint 4: Configuration Soundness (After Phase 4)**

- **Automated Check**: Selection rationale cites at least 3 measured features; incomplete methods absent where a proof is contractually required; every limit numeric; status mapping covers every emittable backend status; seed and thread count recorded.
- **Agent Action on Pass**: Proceed to solving.
- **Agent Action on Failure**: Return to selection with the unmapped status or the missing limit named.
- **Human Review Trigger**: The measured instance exceeds the largest instance in the offline corpus by more than a factor of 5 in total domain-value count.

**Checkpoint 5: Result Validity (After Phase 5)**

- **Automated Check**: Retained incumbent carries a passing independent validation verdict; hard-violation count equals 0; optimality claim accompanied by a proof; terminal status drawn from the normalised vocabulary.
- **Agent Action on Pass**: Proceed to robustness testing.
- **Agent Action on Failure**: Quarantine the assignment, classify the discrepancy cause, and block execution.
- **Human Review Trigger**: Any solver-feasible assignment that fails independent validation, regardless of whether execution was blocked.

**Checkpoint 6: Governance of Change (After Phase 6)**

- **Automated Check**: 0 relaxations applied to safety, legal, permission, or physical constraints; every applied relaxation carries a named approver; relaxation rounds at or below 3; prior generations preserved unmodified.
- **Agent Action on Pass**: Proceed to re-solve or to closure as infeasible.
- **Agent Action on Failure**: Revert the unapproved change, invalidate any assignment derived from it, and escalate.
- **Human Review Trigger**: The conflict classification names contradictory authoritative rules, or relaxation rounds reach the bound without restoring feasibility.

**Checkpoint 7: Handoff Readiness (After Phase 7)**

- **Automated Check**: Hard-feasibility survival across the perturbation suite at or above 90%; every explanation claim references a constraint identifier or authoritative input; every reservation carries an expiration time and invalidation triggers; orchestrator acknowledgement recorded.
- **Agent Action on Pass**: Close the run as verified success and emit the closure record.
- **Agent Action on Failure**: Withhold handoff, select a slack-preserving alternative, or escalate for approval.
- **Human Review Trigger**: Survival below 90%, churn above 30% of assignments under any single perturbation, or a risk tier that names an approver.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
RUN_ID:
MODEL_GENERATION:
TRIGGER:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
FAIL_ACTION:
RESPONSIBLE_AGENT:
HUMAN_REVIEW_TRIGGERED:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Over-Constrained Problem**

- **Symptoms**: No assignment satisfies all current hard constraints; the backend returns proven infeasibility, or propagation empties a domain before search begins.
- **Diagnostic Steps**: Confirm model validity and snapshot identity first; obtain a conflict set or unsatisfiable core; map core literals to registered constraint identifiers; distinguish original requirements from derived and symmetry-breaking entries; test whether the conflict persists when unrelated constraints are disabled.
- **Resolution Protocol**: Option A, correct a misclassification through governance where a preference was accidentally encoded as hard. Option B, apply an authorized relaxation drawn from declared soft constraints or preapproved policies, preferring lower-priority preferences and explicitly flexible bounds. Option C, request additional resources where the conflict maps to a capacity shortage. Option D, report proven infeasibility and escalate where every constraint is genuinely hard.
- **Escalation Trigger**: 3 relaxation rounds without restoring feasibility, or any conflict whose members are all safety, legal, permission, or physical constraints. Random deletion of constraints is prohibited at every stage.

**Error Type 2: Under-Constrained Problem With a Missing Requirement**

- **Symptoms**: The model admits many arbitrary or operationally implausible assignments; reviewers reject a solver-feasible result as obviously unusable; a requirement appears in the request text but not in the coverage map.
- **Diagnostic Steps**: Re-run the requirement-to-constraint coverage map against the original request; run adversarial offline instances designed to exploit the suspected gap; request domain-owner review of the assignment; compare against post-execution monitoring records from prior runs.
- **Resolution Protocol**: Option A, register the missing requirement as a new versioned constraint, increment the generation, and re-solve. Option B, extend the independent validator with the missing check so that future omissions are detected rather than executed. Option C, tighten the affected domains where the omission is a domain-level rather than constraint-level gap.
- **Escalation Trigger**: 2 or more omitted-constraint incidents discovered after deployment against the same model version. Feasibility never reveals omissions, so no retry count applies; historical models are never rewritten, only superseded.

**Error Type 3: Ambiguous or Conflicting Requirements**

- **Symptoms**: Requirement text uses undefined qualifiers such as an unquantified urgency, an unmeasured notion of balance, or an unscoped overlap rule; two authoritative sources state incompatible rules; the extraction ledger contains items marked ambiguous or conflicting.
- **Diagnostic Steps**: Identify which ambiguous items can change feasibility or policy; apply the declared source-of-authority policy and effective dates to conflicting sources; determine whether a preauthorized conservative interpretation covers the item.
- **Resolution Protocol**: Option A, ask the accountable owner and record the answer as a registry entry. Option B, apply a preauthorized conservative interpretation and log which interpretation drove the assignment. Option C, solve labelled alternative interpretations and present them as distinct results rather than merging them. Option D, halt for human judgement where the source-of-authority policy does not resolve a conflict.
- **Escalation Trigger**: Any feasibility-affecting ambiguity unresolved after 2 clarification rounds, or any source conflict unresolved by the declared policy. Selecting the wording that a language model finds more plausible is prohibited; the rejected or superseded rule is retained in provenance.

**Error Type 4: Search Space Too Large for the Declared Budget**

- **Symptoms**: Repeated unknown terminal statuses without an incumbent; propagation consuming a disproportionate share of budget; node counts growing without objective improvement; tail latency far exceeding median latency.
- **Diagnostic Steps**: Measure domain sizes, constraint graph density, connected component count, and symmetry class sizes before altering any limit; compare propagation levels on representative instances; check for accidental symmetries introduced by interchangeable resources.
- **Resolution Protocol**: Option A, tighten domains from authoritative facts and remove impossible values. Option B, replace weak pairwise encodings with an appropriate verified global constraint. Option C, remove accidental symmetries with a verified breaker. Option D, decompose along weakly connected boundaries, preserving cross-subproblem constraints through shared variables, master decisions, or iterative coordination. Option E, supply a good starting incumbent or a better branching strategy. Option F, switch to a domain-specific solver or a local-search method with an explicit not-proven status. Only after these, adjust time and gap limits and retain the best feasible incumbent.
- **Escalation Trigger**: 2 consecutive budget increases without a validated incumbent. Raising a timeout before investigating domains, symmetry, propagation, decomposition, and modelling defects is prohibited, because more compute makes a poor model fail more slowly.

**Error Type 5: Validation Disagreement Between Solver and Validator**

- **Symptoms**: The backend reports a feasible or optimal assignment that the independent validator rejects; recomputed objective components differ from solver-reported components; domain membership fails for an assigned value.
- **Diagnostic Steps**: Classify the cause as model omission, encoding error, stale input data, serialization error, or validator defect; compare input hashes at model build time and at validation time; re-run the validator against a known-good archived instance to test the validator itself.
- **Resolution Protocol**: Option A, correct the encoding and increment the generation where the model misrepresents the requirement. Option B, refresh the snapshot and re-solve where input staleness explains the difference. Option C, correct the serialization path where the assignment was transcribed incorrectly. Option D, correct and re-verify the validator where the validator is at fault, then re-validate every incumbent produced since the defect was introduced.
- **Escalation Trigger**: Any single occurrence. This class does not resolve by retry; execution stays blocked until the cause is classified, and the model that produced the assignment is never asked to explain away the discrepancy.

**Error Type 6: Unstable Dynamic Problem and Re-Solve Oscillation**

- **Symptoms**: Repeated re-solves triggered by rapidly changing inputs; alternating model hashes across consecutive generations; assignment churn rising while objective quality stays flat; warm starts repeatedly failing validation.
- **Diagnostic Steps**: Compare the trigger causes across recent re-solves; measure the interval between input changes against median solve latency; check whether churn originates from external change or from solver nondeterminism and unstable objective weights.
- **Resolution Protocol**: Option A, fix executed and irreversible decisions and replan only the remaining degrees of freedom. Option B, add a stability term penalising unnecessary changes, while never freezing a value that has become invalid under a new hard constraint. Option C, batch input changes into a fixed re-solve cadence where the change interval is shorter than solve latency. Option D, escalate where inputs change faster than the model can be authorized and solved, since Section 1.4 excludes that regime.
- **Escalation Trigger**: 5 re-solves within one execution window, or 2 consecutive generations producing alternating model hashes.

**Troubleshooting Decision Tree**:

```
SOLVE RUN DOES NOT PRODUCE A VALIDATED ASSIGNMENT
├─ NO SOLUTION EXISTS FOR THIS MODEL
│   ├─ Proven infeasible → Isolate conflict set → Map to source requirements
│   │     ├─ Conflict is all-hard and authoritative → CLOSE INFEASIBLE, escalate
│   │     ├─ Preference encoded as hard → Reclassify via governance → Re-solve
│   │     └─ Capacity shortage → Request resources or authorized relaxation
│   └─ Empty domain before search → Identify removing constraint → Verify data freshness
│         ├─ Data stale → Refresh snapshot → Re-solve
│         └─ Domain over-tightened → Restore justified values → Re-solve
├─ RUN STOPPED WITHOUT A PROOF
│   ├─ Incumbent retained → Report best-known with bound and gap, never as optimal
│   └─ No incumbent → Investigate model before budget
│         ├─ Domains, symmetry, propagation, decomposition untested → Improve model
│         └─ Model already improved → Raise limits once, then ESCALATE
├─ ASSIGNMENT FOUND BUT REJECTED
│   ├─ Validator finds hard violation → Quarantine → Classify cause → HALT execution
│   ├─ Robustness survival below 90% → Slack alternative or human approval
│   └─ Explanation lacks constraint identifiers → Rebuild package before release
└─ REQUIREMENTS UNSTABLE OR UNCLEAR
    ├─ Ambiguity affects feasibility → Clarify, or solve labelled alternatives
    ├─ Sources conflict beyond policy → HALT for human judgement
    └─ Inputs change faster than solve latency → Batch or ESCALATE as out of scope
```

**Prohibited recovery actions**: Agents must not conclude that no solution exists from a local-search failure, a timeout, or an unknown status; must not broaden domains with impossible values to obtain feasibility; must not delete constraints blindly when a model is infeasible; must not warm-start from a historical assignment without validating it against the current model; must not let incremental re-solving rewrite completed or irreversible reality; must not hide solver nondeterminism; and must not hand solver output directly to consequential tools.

### D. Performance Metrics, Observability, and Robustness Analysis

**Logging architecture**: Observability uses an append-only event stream plus materialized run, model-generation, solve-attempt, incumbent, validation, diagnosis, relaxation, robustness-test, and handoff records. Every event carries a schema version, a globally unique event identifier, an event type, a wall-clock timestamp, a monotonic duration or sequence number, a run identifier, a model-generation identifier, a solve-attempt identifier, an actor or service identifier, a parent event identifier, correlation identifiers, an environment label, and a sensitivity classification. Backtracking restores logical state; it never erases audit history.

**Required log fields by level**:

- **Request and run level**: requester and tenant class, parent goal and task, risk tier, decision contract, required proof status, deadline, allowed statuses, time and memory budgets, token and monetary budgets for language-model-assisted modelling, relaxation authority, human approvers, experiment cohort, terminal status and reason.
- **Input level**: canonical input hash; dataset, calendar, topology, inventory, policy, and capability versions; provenance references; retrieval timestamps; freshness thresholds; units; timezones; entity counts; missing and defaulted fields; ambiguity resolutions; conflicting sources; redaction policy.
- **Model level**: schema and model-builder version, backend model hash, variable count by type, per-variable domain summary, initial and post-presolve domain sizes, total domain-value count where practical, constraint count by type and hardness, global constraint use, objective terms and scaling, graph density and component summaries, implied constraints, symmetry breakers, assumption literals, requirement-to-constraint coverage, model validation outcome.
- **Constraint level**: stable identifier, version, natural-language label, formal template and bound parameters, scope, hardness, priority or weight, unit, owner, authoritative source, effective dates, relaxation rule, approval requirement, and origin class.
- **Solver attempt level**: solver name and version, compute class, thread count, parameters, random seed, chosen strategy, branching and value heuristics, propagation level, presolve setting, restart policy, warm-start source, time, node, conflict, memory and solution limits, target gap, start and finish timestamps, processor and wall time, peak memory, backend terminal status, normalised application status.
- **Search level**: branches or nodes explored, failures, conflicts, propagations, domain reductions, backtracks, backjumps, learned nogoods, restarts, incumbent count, time to first feasible solution, objective improvements, best bound, gap trajectory, time of last improvement. Fields a backend does not expose are recorded as unavailable rather than as zero, and a custom solver emits sampled or aggregated events where per-node logging would distort performance.
- **Incumbent level**: sequence number, discovery time, assignment hash and secure artifact reference, completeness, solver-reported feasibility, independent validation verdict, hard-violation count, soft-violation count and weighted cost, objective components, best bound, gap, diversity from prior incumbents, and whether it became the retained or handed-off solution.
- **Validation level**: validator name and version, input and solution hashes, checks performed, constraint identifiers evaluated, hard and soft violations, domain-membership failures, missing assignments, recomputed objective, discrepancy from solver objective, source freshness at validation, verdict, evidence references.
- **Diagnosis level**: trigger, proof status, empty domains, conflict or core identifiers, whether the set is known minimal or merely sufficient, source constraints represented, diagnostic algorithm and budget, constraints toggled during isolation, repeated conflicts, suspected cause, recommended owner, and the preserved infeasible model hash.
- **Relaxation level**: proposed and approved constraint changes, previous and new hardness, bound or penalty change, authority, approver, rationale, affected stakeholders, expected and observed feasibility impact, objective impact, model generation, and whether the change is temporary.
- **Re-solve and repair level**: environmental trigger, changed facts, prior and new model hashes, fixed executed decisions, released reservations, warm start, assignment edit distance, retained decisions, invalidated tasks, additional solve cost, recovery latency, and validation outcome, with causes normalised across stale data, execution overrun, resource loss, new task, policy change, model defect, and external cancellation.
- **Robustness level**: baseline instance, perturbation identifier and rule, changed fields, seed, scenario probability where defensible, solve parameters, feasibility, objective, gap, solution churn, minimum slack, binding constraints, and degradation from baseline, with clean, stress, and adversarial cohorts kept distinct.
- **Handoff and closure level**: selected solution and validation identifiers, orchestrator acknowledgement, reservations created, expiration time, invalidation triggers, tasks generated, human decisions, final objective and proof status, total solve attempts and model generations, total solver and language-model resources, total relaxations, unresolved uncertainty, and artifact lineage.

**Solve-run log record template**:

```
RUN_ID:
MODEL_GENERATION:
SOLVE_ATTEMPT_ID:
EVENT_TYPE:
SCHEMA_VERSION:
TIMESTAMP:
MONOTONIC_SEQUENCE:
INPUT_HASH:
MODEL_HASH:
SOLVER_NAME_VERSION:
RANDOM_SEED:
THREAD_COUNT:
PROPAGATION_LEVEL:
LIMITS:               TIME | NODES | CONFLICTS | MEMORY | GAP
BACKEND_STATUS:
NORMALISED_STATUS:
INCUMBENT_HASH:
VALIDATION_VERDICT:
HARD_VIOLATION_COUNT:
OBJECTIVE_COMPONENTS:
BEST_BOUND:
GAP:
SENSITIVITY_CLASS:
```

**Outcome metrics**:

- **Admission-to-feasible success rate**: admitted runs producing at least 1 independently validated hard-feasible assignment, divided by admitted runs, segmented by problem family, size, risk tier, model version, and solver configuration (target: at or above 90% for workloads believed feasible).
- **Proof rate**: runs ending in proven optimality or proven infeasibility, divided by admitted runs, reported separately from success (target: reported, not optimized in isolation).
- **Hard-constraint violation rate**: validated returned solutions carrying at least 1 hard violation, divided by validated returned solutions (target: 0%). Any occurrence is a critical defect even when execution was blocked, and its cause is attributed to model omission, stale input, encoding, serialization, or validator mismatch.
- **Terminal status distribution**: the share of runs closing in each normalised status, reported in full rather than reduced to a success rate, because some workloads are legitimately infeasible.

**Efficiency metrics**:

- **Time to first validated feasible solution**: latency from solve start to the first passing validation verdict, reported at median and at the 95th percentile (target: within the declared deadline at the 95th percentile).
- **Total solve time**: latency to terminal status, reported with processor time, wall time, peak memory, nodes, conflicts, backtracks, and propagations, since equal latency on different hardware or search effort is not equivalent.
- **Search efficiency**: nodes or branches per validated incumbent, backtracks per node, values removed per propagation unit where available, time per incumbent improvement, and memory per instance. A lower node count that raises wall time through expensive propagation is not an improvement.
- **Re-solving performance**: re-solves per execution window, recovery success rate, trigger-to-valid-plan latency, share of prior decisions retained, assignment churn, and additional objective cost, separating necessary adaptation to external change from churn caused by unstable objectives or solver nondeterminism.

**Quality and governance metrics**:

- **Solution quality**: objective total and each component, normalised improvement over a simple baseline heuristic, best bound, optimality gap, and distribution across instances, compared only across compatible model and objective versions and reported per lexicographic level where priorities are lexicographic.
- **Relaxation frequency**: runs carrying any approved relaxation, divided by admitted runs, with rounds, magnitude, constraint class, approval latency, and feasibility gained (target: reviewed whenever above 20%, since relaxation concentrated in one requirement indicates unrealistic policy or systematic under-resourcing rather than solver success).
- **Infeasibility diagnostic yield**: proven-infeasible runs producing an actionable conflict package, divided by proven-infeasible runs, with time to first conflict, conflict-set size, repeated cores, share mapped to source requirements, human acceptance, and resolution after an approved change (target: at or above 80% mapped to source requirements).
- **Modelling quality**: requirement coverage, model-invalid rate, empty-domain rate before search, validator disagreement rate, omitted-constraint incidents found after deployment, and manual correction frequency, tracked by model-builder version and, where language-model assistance is used, by model, prompt, sampling settings, retrieved examples, and validation path (target: 0 omitted-constraint incidents per model version).

**Robustness analysis protocol**: Robustness is evaluated across repeated runs and perturbed instances. For identical inputs, agents report feasibility consistency, objective variance, latency variance, assignment variation, and worst-tail resource use across seeds and thread settings, because local-search and parallel-solver nondeterminism makes repeated trials essential. For perturbed inputs, agents report hard-feasibility survival rate, objective degradation, plan churn, minimum slack, and the gap between clean and stress cohorts. The perturbation suite varies demand, durations, availability, deadlines, capacities, costs, travel times, input ordering, benign paraphrases of the request, missing optional data, and solver seeds, and includes fault cases covering a stale calendar, a duplicate identifier, a timezone shift, an unavailable resource, a policy contradiction, a malformed generated constraint, a solver timeout, memory pressure, and validator disagreement. A robust system either preserves an acceptable validated result or fails safely with the correct status and escalation.

**Change evaluation and promotion rule**: Model, solver, prompt, heuristic, and weight changes are evaluated by paired comparison, running the old and new versions on the same frozen corpus and perturbation suite with consequential execution disabled. Promotion requires that zero-hard-violation behaviour is preserved, that the targeted improvement is measured, and that no unacceptable regression appears in tail latency, proof rate, solution quality, intervention rate, or robustness. A simple greedy or rule-based baseline is retained permanently, and a dedicated solver must justify its operational cost against that baseline at matched validity.

***

## IV. Domain-Agnostic Application Guidance

The framework is independent of subject matter. Variables, domains, hardness classification, propagation, bounded search, independent validation, diagnosis, authorized relaxation, robustness testing, and governed handoff apply wherever discrete decisions interact under checkable rules. The following adaptations show how the same phases instantiate in dissimilar sectors.

**Time and facility scheduling**: Variables represent each activity's start slot, its location, and its equipment configuration. Domains are drawn from participant availability, location calendars, permitted operating hours, and compatible equipment sets. Hard constraints require every required participant to be available, location capacity to cover attendance, sensitive activities to use approved locations, no participant or location to overlap, changeover time between incompatible configurations, and completion before a deadline. Soft constraints prefer compact calendars, favoured hours, minimal location changes, and fewer remote participants. Phase 2 freezes calendar and location data and normalises timezones and interval boundary conventions before construction, because a boundary convention error produces a convincing but unusable schedule. Propagation frequently removes every location value for one activity because attendance exceeds available capacity; that is an immediate diagnostic finding, not a reason to search longer. When no schedule exists, the conflict is typically narrow, such as a single approved secure location being unavailable during the only common availability window, and the authorized alternatives are moving the deadline, dividing attendance, obtaining approval for another location, or reclassifying one participant as optional with the activity owner's confirmation. Robustness testing shifts uncertain durations and changeover times, removes one location, and perturbs one participant's availability; a schedule with modest slack is frequently preferable to a nominal optimum that collapses after a small delay.

**Allocation of work across autonomous actors**: Variables identify the actor assigned to each task and, where relevant, its start time and compute tier. Domains include only actors holding the required capability, tool access, clearance, context capacity, and availability. Hard constraints preserve task dependencies, prevent an actor from exceeding concurrency or consumption budgets, keep confidential work inside authorized boundaries, require independent validation of high-risk outputs, and prohibit the same actor from both producing and independently approving a result. Soft constraints minimise latency and cost, preserve context locality, balance load, and prefer historically reliable actors per task class. The pattern boundaries in Section 1.3 matter acutely here: decomposition decides which outcomes and tasks exist, hierarchical method selection chooses approved procedures, constraint solving assigns actors and timing, orchestration issues leases and tracks attempts, and meta-reasoning decides whether the allocation warrants exact solving. Keeping these distinct prevents an allocation optimizer from inventing tasks or treating predicted capability as observed completion. A characteristic infeasibility arises when only one actor holds both the required clearance and the validation capability while independence is mandatory; lower cost is not an authorized relaxation of separation of duties, and the correct options are adding another cleared validator, changing scope, or escalating.

**Routing and physical logistics**: Variables assign each stop to a vehicle and to a sequence position or time. Hard constraints require every mandatory stop exactly once, keep loads within capacity, respect operator and customer time windows, preserve pickup-before-delivery ordering, and prohibit incompatible cargo combinations. Objectives may combine distance, lateness penalties, vehicle count, workload balance, and plan stability. A dedicated routing library is frequently preferable to a generic hand-built model because it supplies domain-specific route representations and tested neighbourhood moves. Language interpretation of delivery notes is useful, but addresses, demands, permissions, and time windows must pass schema and location validation before solving. During execution, completed stops and current vehicle positions become fixed facts; the remaining route is re-solved with a penalty on unnecessary reassignment, capacity and operating-hour constraints are revalidated, and churn is bounded. Scenario tests vary travel times and vehicle availability, and no plan is called robust merely because it is shortest under the original forecast.

**Configuration and selection problems**: Variables represent component choices, inclusion decisions, or tier selections. Domains come from catalogues filtered by compatibility, licensing, and regulatory eligibility. Hard constraints encode compatibility tuples, mutual exclusions, required companions, and budget or capacity ceilings. The dominant risk is an incomplete compatibility catalogue rather than search difficulty, so the coverage map and the independent validator carry more weight than solver configuration, and offline adversarial instances target catalogue gaps directly.

**Scale adaptation**:

- **Small scope** (fewer than 50 variables and fewer than 20 constraints): Retain the constraint registry, the independent validator, and the status vocabulary, but collapse the method selection phase to a recorded default and skip the propagation benchmark. Budgets remain numeric. The validator is never omitted, because a small model can still omit a requirement.
- **Medium scope** (50 to 5,000 variables): Apply the full framework as written. Propagation benchmarking, symmetry analysis, and the perturbation suite deliver their largest returns in this range.
- **Large scope** (above 5,000 variables or above 1,000,000 total domain values): Improve the model before raising budgets, following the Error Type 4 protocol. Decompose along weakly connected boundaries only where cross-subproblem constraints are preserved through shared variables, master decisions, or iterative coordination, since an unpreserved cross constraint produces subproblem-feasible but globally infeasible assignments. Report tail latency rather than mean latency, and retain the best validated feasible incumbent under every deadline.
- **Multi-agent distribution**: Where several agents solve related pieces, the constraint graph determines what context must travel between them. Shared variables and the constraints spanning subproblems are transmitted in full; local constraints are not. Each agent's result passes the same independent validation before composition, and the composed assignment is validated again against the global hard constraints.

***

## V. Limitations and Considerations

**Language models cannot substitute for constraint propagation**: A language model does not maintain domains, does not perform arc revision, and does not prove infeasibility or optimality, yet it produces fluent text asserting that an assignment satisfies every rule. The consequence is that unchecked model-authored assignments pass human review on plausibility while violating hard constraints. The mitigation is structural rather than procedural: a solver establishes feasibility, an independent validator on a separate code path confirms it against authoritative inputs, and no assignment reaches execution without a passing validation verdict. Re-sampling multiple answers does not mitigate this, because independently sampled answers can share the same omitted rule.

**Generated models are hypotheses, not requirements**: A language model can draft a constraint model, propose implied constraints, or suggest streamlining devices that materially reduce runtime. Successful execution of that generated model proves only that the encoding runs, not that it encodes the request completely or soundly. The mitigation is to test every generated device against exhaustive small instances, to maintain a requirement-to-constraint coverage record, and to check the returned assignment against source-level acceptance criteria rather than against the generated encoding.

**Solver feasibility is not requirement completeness**: A solver proves properties of the encoding it received. A model that omits a real requirement will return confident, feasible, and unusable answers, and no amount of solver quality detects the omission. The mitigation is the coverage map, domain-owner review, adversarial offline instances, post-execution monitoring, and treating any post-deployment omission incident as a validator extension rather than a one-off correction.

**Local search cannot prove infeasibility**: Ordinary local search returns no solution both when none exists and when the search failed. Reporting the former on evidence of the latter causes requesters to abandon feasible requests. The mitigation is to accompany incomplete methods with a systematic solver or with an explicit not-proven status, and to reserve the proven-infeasible status for backend proofs.

**Discretisation error**: Continuous quantities forced into a finite model acquire rounding, boundary, and interval-convention errors that the solver cannot detect because they are already in the data. The mitigation is to normalise units, timezones, boundary conventions, and rounding rules in one place during Phase 2, to record the convention applied, and to route strongly nonlinear continuous dynamics to methods designed for them rather than discretising them crudely.

**Unsound strengthening silently removes solutions**: An incorrect symmetry breaker or a non-entailed implied constraint removes valid assignments without producing any error, and the run reports infeasibility for a feasible problem. The mitigation is exhaustive small-instance testing of every strengthening device, origin-class tagging so that diagnosis can distinguish a modelling technique from a business rule, and removal of any device that changes the solution set of an exhaustive instance in an unintended way.

**Objective weights encode policy**: Arbitrary weights permit surprising compensation between unrelated preferences, so that a small gain on one dimension outweighs a substantial loss on another that stakeholders never agreed to trade. The mitigation is to require an approval record for every weight, to prefer lexicographic priority where the policy is genuinely a priority ordering, and to review the plain-language objective summary before solving rather than after.

**Nondeterminism obscures comparison**: Parallelism, restarts, and randomised heuristics mean that identical inputs can produce different assignments, different latencies, and different terminal statuses. Comparing a new configuration against an old one on single runs therefore produces conclusions that do not replicate. The mitigation is to record seeds, thread counts, and parameters, to report repeated-run variance alongside point estimates, and to promote changes only on paired evaluation across a frozen corpus.

**Decomposition can break global feasibility**: Splitting a large model into subproblems is often the only way to meet a deadline, but a cross-subproblem constraint that is not preserved yields locally feasible pieces that compose into an infeasible whole. The mitigation is to decompose only along weakly connected boundaries, to carry spanning constraints through shared variables, master decisions, or iterative coordination, and to validate the composed assignment against the global hard constraints.

**Upstream estimate error propagates silently**: Durations, travel times, demand, and failure probabilities supplied by simulation or forecasting enter the model as facts. A mathematically valid plan fails when those estimates were wrong, and the failure appears at execution rather than at solving. The mitigation is the perturbation suite, explicit slack reservation where survival falls below the declared threshold, and expiring reservations that force a precondition recheck before execution.

**Allocation decisions carry distributive consequences**: Assigning work, access, or resources among people or organisations distributes benefit and burden, and an objective that minimises cost can systematically disadvantage a group without any constraint being violated. The mitigation is to represent fairness requirements as explicit registered constraints or objective terms with named owners rather than leaving them implicit, to report per-group outcome distributions alongside the aggregate objective, and to route any relaxation affecting a protected requirement to human approval.

**Telemetry can leak sensitive material**: Constraint models frequently contain personal availability, clearance levels, health-related restrictions, and commercially sensitive capacity data, and detailed observability multiplies the places that data is stored. The mitigation is to log secure references, structured reason codes, and hashes rather than raw inputs, to classify every event by sensitivity, to exclude secrets and unnecessary personal data from general telemetry, and to withhold private reasoning traces from explanation packages.

**Operational cost may exceed the benefit**: A dedicated solver adds modelling effort, a validator, a registry, a diagnostic path, and an observability surface, all of which must be maintained. Deploying one because a library is available, rather than because it improves feasibility, quality, or reliability over a simpler checked baseline, converts a solved problem into a maintained system. The mitigation is the permanent baseline comparison in Section III.D and the exclusion rules in Section 1.4.

***

## VI. Conclusion and Summary

Constraint Satisfaction Planning earns its place in an agent architecture when correctness depends on finding a jointly feasible assignment among interacting choices, and when a candidate assignment can be checked mechanically. Its value comes from making the problem explicit: decisions become variables, possibilities become domains, requirements become registered constraints with owners and provenance, and preferences become an approved ranking policy that is visibly separate from what is mandatory.

The method's discipline is procedural rather than mathematical. Propagation runs before search so that contradictions surface cheaply. Search runs under numeric bounds so that budget exhaustion produces a labelled status rather than a silent failure. Every incumbent passes an independent validator before it is called feasible, and the best validated incumbent is retained so that a deadline yields a usable answer instead of an abandoned run. Infeasibility is diagnosed and mapped to source requirements rather than concealed by deleting constraints, and relaxation happens only under recorded authority that never reaches safety, legal, permission, or physical rules.

The architectural boundary is the part most easily lost in an agent system. A language model is an excellent interface to a constraint problem and a poor solver of one. It elicits requirements, normalises vocabulary, drafts encodings, and explains results; it does not maintain domains, prove infeasibility, or certify feasibility. Every phase in this guide preserves that separation, and every checkpoint enforces it.

**Key Success Factors**:

- **Explicit solve contract**: One declared contract, one set of numeric budgets, and a full status vocabulary that distinguishes feasible, optimal, infeasible, invalid, unknown, and cancelled outcomes.
- **Hardness discipline**: Mandatory rules stay hard, preferences carry approved priorities and provenance, and no safety, legal, permission, or physical rule is ever expressed as a finite penalty.
- **Sound domains and verified strengthening**: Domains are tightened only from authoritative facts with recorded justification, and every global, implied, and symmetry-breaking device is tested against exhaustive small instances before use.
- **Independent validation**: A validator on a separate code path recomputes every hard constraint from authoritative inputs, and no assignment reaches execution without its verdict.
- **Diagnose before relaxing**: Conflict sets, cores, empty-domain evidence, and controlled what-if analysis precede any change, and every applied relaxation names an approver.
- **Bounded loops and recorded nondeterminism**: Search, optimization, relaxation, and re-solving all carry numeric limits, and seeds, parameters, statistics, and repeated-run variance are logged so that comparisons replicate.
- **Governed handoff**: Solver output proposes control actions, expiring reservations force a precondition recheck, and execution systems remain authoritative over reality.

By following this framework, AI agents can convert informally stated planning problems into explicit, auditable constraint models, obtain assignments whose feasibility is proven rather than asserted, and hand those assignments to an orchestrator that continues to observe reality and returns control to planning when it changes.

***

## VII. References and Further Reading

This guide is a structural conversion of a single originating prose document. The external references listed below are transcribed from that originating prose guide, which cited them in support of the material converted here. They have not been independently re-verified during this conversion, and each title and location is reproduced as it appeared in the source.

**Originating document**:

1. `Constraint Satisfaction Planning: An Operational Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the variable, domain, and constraint model; the propagation, search, and optimization machinery; the solver and method selection rules; the pre-runtime model design rules; the end-to-end operational workflow; the over-constrained, ambiguous, and large-problem recovery procedures; the analysis of language-model reasoning versus a dedicated solver; the logging field inventory; and the metric definitions.

**Sibling guides in this corpus** (each is self-contained and may be loaded alongside this guide where the neighbouring pattern is in play):

2. `advanced_task_guides/planning/guide_HierarchicalTaskNetworkPlanning.md` — procedural decomposition of compound tasks into authorized primitive tasks, which supplies the tasks a constraint model schedules and allocates.
3. `advanced_task_guides/planning/guide_TaskManagementOrchestration.md` — the lifecycle governance that converts a validated assignment into leases, dispatches, retries, and escalations, and that triggers incremental re-solving.
4. `advanced_task_guides/planning/guide_MetaReasoning.md` — selection and monitoring of reasoning strategies, including whether a case warrants exact solving and how solver budgets should be adjusted.
5. `advanced_task_guides/planning/guide_WorldModelSimulationPlanning.md` — prediction of environmental response, which supplies duration, travel-time, and resource-state estimates consumed as facts by a constraint model.
6. `advanced_task_guides/planning/guide_PlanTodoRecitation.md` — maintenance of plan salience in an agent's working context, distinct from the authoritative constraint store and solver state.
7. `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — observability design practice relevant to the append-only event stream and log field inventory in Section III.D.
8. `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — analysis of constraints acting on monitoring design, relevant when the constraint model itself governs observability resources.
9. `advanced_task_guides/authoring/guide_guidewriting.md` — the house-style specification this guide conforms to, covering the archetype, the step slot template, and the conformance envelope.

**External references transcribed from the originating guide** (titles and locations reproduced as they appeared in that source, grouped by the section of the source in which each was cited):

*Purpose and core idea*

10. *Constraint Processing* — https://www.elsevier.com/books/constraint-processing/dechter/978-1-55860-890-0
11. *Handbook of Constraint Programming* — https://www.elsevier.com/books/handbook-of-constraint-programming/rossi/978-0-444-52726-4
12. Google CP-SAT documentation — https://developers.google.com/optimization/cp/cp_solver

*The conceptual model*

13. MiniZinc global-constraint library — https://docs.minizinc.dev/en/stable/lib-globals.html
14. Global Constraint Catalog — https://sofdem.github.io/gccat/
15. OR-Tools employee scheduling — https://developers.google.com/optimization/scheduling/employee_scheduling
16. Mackworth, “Consistency in Networks of Relations” — https://www.cs.ubc.ca/~mack/Publications/AI77.pdf

*Propagation, search, and optimization*

17. UMBC’s CSP lecture notes — https://courses.cs.umbc.edu/471/spring23/02/notes/06_constraints/06.pdf
18. Minton and colleagues, “Minimizing Conflicts” — https://jmvidal.cse.sc.edu/lib/minton92a.html
19. “Unsatisfiable Cores for Constraint Programming” — https://arxiv.org/pdf/1305.1690
20. Generating Streamlining Constraints with Large Language Models — https://arxiv.org/abs/2408.10268

*When not to use it*

21. Google constraint optimization guidance — https://developers.google.com/optimization/cp

*Solver and method selection*

22. MiniZinc Handbook — https://www.minizinc.org/doc-latest/en/
23. Choco — https://choco-solver.org/docs/modeling/constraints/
24. Gecode — https://www.gecode.dev/documentation.html
25. Programming Z3 — https://theory.stanford.edu/~nikolaj/programmingz3.html

*Language-model reasoning versus a dedicated solver*

26. Combining Constraint Programming Reasoning with Large Language Model Predictions — https://drops.dagstuhl.de/storage/00lipics/lipics-vol307-cp2024/LIPIcs.CP.2024.25/LIPIcs.CP.2024.25.pdf
27. CP-Bench — https://arxiv.org/html/2506.06052

