# Intelligent Goal Decomposition

**Status**: Beta testing

**Change logs**:

- [09/06/2026] - Initialization

***

## Executive Summary

Intelligent Goal Decomposition is the controlled conversion of a vague, broad, ambiguous, or long-horizon objective into a hierarchy of measurable, actionable subgoals whose joint satisfaction is intended to establish the parent goal. The method produces more than a checklist. A sound decomposition makes the intended outcome explicit, defines evidence of success at every node, separates facts from assumptions, distinguishes hard constraints from negotiable preferences, exposes dependencies and interfaces across branches, assigns accountable ownership, and stops refining at the point where leaves are ready for planning or execution.

This guide provides AI agents with a seven-phase operational framework covering objective capture, goal-contract normalization, ambiguity gating, admission and budgeting, lens selection, multi-candidate generation, node-contract drafting, local and sibling validation, dependency and feasibility analysis, bounded refinement, adversarial challenge, version freezing, semantics-preserving handoff, and evidence-driven reopening. It specifies the properties that make a decomposition sound, the record types that make it auditable, the metric families that make it measurable, and the escalation paths that prevent an unvalidated hierarchy from reaching execution.

The word "intelligent" in the pattern name does not mean that a generative model's first hierarchy is trusted. It means the system uses context, stakeholder intent, retrieved evidence, domain knowledge, dependency analysis, independent critique, deterministic checks where they exist, and feedback from downstream execution to propose and improve a decomposition. Generated hierarchies are candidates requiring validation, never conclusions carried by rhetorical confidence. Without validation, bounds, and feedback, decomposition merely converts one vague objective into many confident-sounding ones.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Intelligent Goal Decomposition (IGD)**: The objective-structuring pattern defined by this guide. IGD answers three questions: which outcomes must become true, how each will be recognized, and what relationships exist among them. It is an input to planning and orchestration, not a substitute for either.

**Goal**: A desired state or outcome, expressed as a condition that either holds or does not hold at a stated time. A goal names a subject, a desired state, and a scope [10].

**Subgoal**: A necessary or deliberately selected intermediate outcome that contributes to its parent goal. A subgoal is a goal at a lower level of the hierarchy and carries the same structural obligations as its parent.

**Task**: Work to be performed. A task is an activity, not a state. The distinction is load-bearing: reducing a median support response time from eight hours to four hours by a named date without lowering quality is a goal; measuring the current queue and removing the largest routing delay are candidate subgoals; querying a ticket warehouse is a task.

**Goal contract**: The normalized statement of an objective, holding the desired end state, beneficiaries, scope inclusions and exclusions, target measures, decision horizon, required artifacts, prohibited outcomes, authority boundary, declared assumptions, hard constraints, and negotiable preferences. The goal contract is the artifact the decomposition refines; the verbatim original request is preserved separately from it.

**Node contract**: The metadata record attached to a single goal node, comprising the outcome statement, rationale, parent link, scope, measure, baseline, target, evidence specification, deadline or checkpoint, owner or executor class, effort estimate, required inputs, produced outputs, assumptions, constraints, risks, disaggregated confidence, and classification as required, conditional, optional, or guardrail.

**Goal tree**: The decomposition hierarchy, in which every node has exactly one parent for explanatory lineage. The tree explains contribution. It does not describe execution order.

**Dependency edge**: A typed, directed relationship between nodes that may cross branches, classified as precedence, data, resource, approval, mutual exclusion, or conditional trigger. Once dependency edges are added to a goal tree, the operational representation is a directed graph rather than a tree.

**Outcome criterion**: An acceptance condition proving that the desired state exists, such as a median response time at or below four hours sustained for four consecutive weeks.

**Guardrail criterion**: An acceptance condition proving that the method did not create an unacceptable trade-off, such as a satisfaction measure declining by no more than one percentage point. Guardrails are first-class acceptance criteria and are never traded away as preferences.

**Operational readiness**: The property that terminates refinement on a branch. A leaf is operationally ready when a planner or executor can identify the next action or invoke a known method, its inputs and outputs are clear, its completion can be verified from named evidence, its residual uncertainty falls within the receiving system's tolerance, and further decomposition would not materially reduce risk or ambiguity.

**Decomposition lens**: The organizing principle selected before children are proposed, drawn from outcome, capability, lifecycle, risk, stakeholder, and system lenses. The lens governs how siblings are named and partitioned.

**Decomposition budget**: The declared guardrail bounding maximum depth, maximum children per node, maximum refinement rounds, token spend, wall-clock time, and the review threshold above which human authorization is required. The budget is a limit, not a target to consume.

**Coverage loop**: The bounded iteration in which sibling sets are refined, locally revalidated, and rechecked against parent criteria until no material uncovered criterion remains or the refinement budget is exhausted.

**Tree version**: An immutable, content-hashed snapshot of an approved hierarchy together with its schema version, model and prompt versions, assumption set, evidence references, validator results, and approver identity. Later changes create a new version with a stated reason and lineage; they never rewrite an existing version.

**Exit category**: The declared terminal classification of a decomposition run, drawn from approved hierarchy, direct execution, template substitution, infeasible, clarification required, safe refusal, cancelled, and budget exhausted.

**Downstream consumer**: The planner, scheduler, workflow engine, orchestrator, or human team that receives the approved hierarchy [25][26]. IGD is not complete until a named downstream consumer has accepted the handoff.

### 1.2 Scope of the Pattern and Its Boundaries

IGD is an objective-structuring pattern that may use model judgment where formal domain knowledge is incomplete. It hands a validated hierarchy to a downstream consumer; it does not by itself guarantee an executable action sequence. Its leaves are outcomes, and the conversion of outcomes into tasks occurs only at the handoff boundary. AI agents must hold four boundary distinctions explicitly, because conflating them produces hierarchies that look rigorous and behave poorly.

**IGD and hierarchical task network planning**: Hierarchical task network planning recursively replaces compound tasks with task networks by applying explicit domain methods carrying applicability conditions, ordering constraints, and domain-defined semantics, until only primitive executable tasks remain. That authored domain knowledge makes the method efficient and predictable, and expensive to build [14]. IGD instead proposes a hierarchy for a novel or vaguely stated objective where no validated method library exists, and its leaves may remain outcomes rather than executable operators. AI agents must use IGD to discover and clarify structure, and use hierarchical task network planning where approved reusable procedures already define how abstract work may be refined. An IGD result is a candidate input to method authoring, never an authored method merely because both representations are hierarchical. A related distinction separates goal decomposition, which gives nodes explicit state semantics, from task decomposition, which names units of work; representations combining both in one partially ordered structure must label which nodes carry state semantics [15][16].

**IGD and task management and orchestration**: IGD decides which outcomes should exist and how they relate. Task management and orchestration manages the lifecycle of work already admitted into execution, covering registration, eligibility, scheduling, assignment, state transitions, retries, handoffs, cancellation, compensation, and closure. The orchestrator receives approved leaves, task definitions, dependencies, success evidence, and lineage from IGD, and then remains the runtime source of truth. A goal tree is not a work queue, and marking a subgoal complete is not sufficient unless its completion evidence passes the declared criterion.

**IGD and meta-reasoning**: IGD is one reasoning strategy among several. Meta-reasoning monitors reasoning and selects whether to decompose, retrieve evidence, apply a method library, invoke a constraint solver, simulate, verify, ask a person, or stop. The control layer can cost more than it saves on simple objectives, so the gate deciding whether IGD is warranted must itself be cheap. A meta-reasoning gate determines whether decomposition is justified, how much depth is warranted, and whether a stalled decomposition should change method.

**IGD and adjacent planning patterns**: Constraint-satisfaction planning finds assignments or schedules satisfying hard and soft constraints, and should be invoked after or during decomposition whenever feasibility depends on capacity, timing, routing, or exclusivity, rather than asking prose generation to solve combinatorial problems. Plan and execute decoupling separates upfront plan generation from tool execution; an IGD hierarchy can seed such a plan, but a static plan is fragile when observations change. Scenario planning tests a hierarchy against several plausible futures, and world-model simulation estimates the consequences of candidate actions; both challenge assumptions and neither defines the goal hierarchy. Plan and todo recitation keeps the current plan salient inside limited context and is not an authoritative goal registry. These patterns are complementary controls, not interchangeable labels.

### 1.3 Properties of a Sound Decomposition

This subsection is normative. Every acceptance decision in Section II refers back to it.

**Node anatomy**: A strong goal node states an outcome rather than an activity. It names the subject and desired state, the relevant scope, a measure or observable predicate, a target or acceptance threshold, a time horizon where relevant, the constraints that must remain true, the evidence required for verification, an accountable owner or capable executor class, and the assumptions on which feasibility depends. Specificity mnemonics such as the specific, measurable, achievable, relevant, and time-related checklist serve as prompts for completeness, and were framed by their originator as guidance rather than as a requirement that every goal satisfy every word mechanically [17]. AI agents must treat such mnemonics as a completeness prompt, not as a scoring rubric.

**Two kinds of success criteria**: Outcome criteria prove that the desired state exists. Guardrail criteria prove that the method did not create an unacceptable trade-off. Both must name evidence that is available, credible, and discoverable at the time the criterion will be evaluated. A criterion whose evidence does not yet exist creates an information subgoal rather than a passing node. Objective-and-key-result formulations that describe activities rather than outcomes conceal required resources and delay the discovery that an objective will be missed [18].

**The six sibling tests**: The children of any node must satisfy all six of the following tests. Failure of any test rewrites or removes the offending child.

1. **Necessary contribution**: Each child must explain how satisfying it materially advances or safeguards the parent. Ornamental work and unmotivated branches are removed unless explicitly classified as optional.

2. **Collective coverage**: Taken together, the required children must cover the parent's success criteria, its constraints, and its major failure modes. Coverage is semantic, not numerical. Five vague children are not superior to three sufficient ones.

3. **Limited overlap**: Children must not claim the same outcome or the same evidence without a declared shared interface. Undeclared overlap creates duplicated work and ambiguous accountability. Cross-cutting concerns such as safety or data quality legitimately touch several branches and must be modelled as shared constraints, reusable services, or explicit cross-links rather than forced into disjoint boxes.

4. **Measurability and falsifiability**: A neutral reviewer must be able to determine pass, fail, blocked, or not-yet-observed from named evidence. An abstract improvement statement fails this test; a statement raising a held-out score from a stated baseline to a stated threshold with no critical safety regressions passes it.

5. **Feasibility and controllability**: The responsible actor must hold a plausible means, the authority, the inputs, the resources, and the time to influence the result. Outcomes outside that actor's control are labelled as assumptions or dependencies, never assigned as though the actor controlled them.

6. **Operational readiness**: A leaf is sufficiently decomposed when it satisfies the readiness definition in Section 1.1. Readiness is judged against the receiving system's tolerance, not against an abstract standard of detail.

**Asymmetric depth**: Branches must not be forced to a common depth. Decomposition depth is a control variable, not a quality score. High-risk, novel, or weakly specified branches may require several levels, while a familiar and reversible branch may remain a single level deep. The stopping rule is marginal: refinement halts when another level is unlikely to improve measurability, feasibility, assignment, dependency detection, or risk control by enough to justify its cost. Excessive detail creates management overhead without reducing risk [19].

**Hierarchy is not order**: Parent-child structure explains contribution. Dependency edges explain execution eligibility. Two children of one parent may run in parallel, and a child in one branch may depend on evidence produced in another. Cycles must be rejected unless they represent an intentional, observable, bounded feedback loop with a declared trigger, progress measure, maximum iteration count, and exit condition.

**Canonical structure of a validated decomposition**:

```
ROOT GOAL  [normalized goal contract, tree version v3, hash 7f21c9]
  OUTCOME CRITERIA: C1  C2  C3        GUARDRAIL CRITERIA: G1  G2
│
├── NODE 1  [REQUIRED]    COVERS: C1, G1       DEPTH 1
│   ├── NODE 1.1  [REQUIRED]     COVERS: C1    LEAF: OPERATIONAL
│   └── NODE 1.2  [GUARDRAIL]    COVERS: G1    LEAF: OPERATIONAL
├── NODE 2  [REQUIRED]    COVERS: C2           DEPTH 1
│   ├── NODE 2.1  [REQUIRED]     COVERS: C2    LEAF: NEEDS REFINEMENT
│   └── NODE 2.2  [CONDITIONAL]  COVERS: C2    LEAF: OPERATIONAL
├── NODE 3  [REQUIRED]    COVERS: C3, G2       LEAF: OPERATIONAL
└── NODE 4  [OPTIONAL]    COVERS: NONE         FLAGGED FOR REMOVAL

DEPENDENCY EDGES  [CROSS-BRANCH; NOT PART OF THE HIERARCHY]
  E01  NODE 2.1 <-- DATA -------- NODE 1.1     JOIN: ALL
  E02  NODE 3   <-- APPROVAL ---- EXTERNAL     JOIN: ALL   ASSUMPTION A4
  E03  NODE 2.2 <-- CONDITIONAL - NODE 2.1     JOIN: NAMED CONDITION
  E04  NODE 1.2 <-- PRECEDENCE -- NODE 1.1     JOIN: THRESHOLD 2 OF 3

UNCOVERED CRITERIA: NONE          CYCLE CHECK: PASS
ORPHAN NODES: NONE                MAX DEPTH: 2   BRANCHING FACTOR: 2.0
```

### 1.4 Applicability: Selection and Exclusion Criteria

**Conditions favouring IGD**: AI agents should apply IGD when a requested outcome is ambiguous enough that different competent actors would pursue materially different meanings; when several workstreams or specialties must contribute; when success depends on hidden prerequisites, approvals, evidence, or resources; when the horizon is long enough for checkpoints to matter; when a shared definition of completion is missing; when downstream planning is blocked by unclear scope; or when failure is costly enough that an explicit completeness and feasibility review is warranted. Typical settings include research programmes, product launches, migrations, investigations, policy and grant work, organizational change, and agent systems that must hand work across tools or roles. Under-decomposition in these settings leaves blockers hidden until execution, where they are most expensive to resolve.

**Three intensities**: A lightweight decomposition applies when the objective is moderately complex but low risk, and consists of restating the outcome, identifying between three and seven measurable children, noting dependencies, and proceeding. A full decomposition applies when the objective is high consequence, cross-functional, expensive, hard to reverse, or likely to be judged against formal acceptance criteria. A hybrid decomposition applies when some branches have established methods and others are novel: stable branches route into a method library or fixed workflow, novel branches route into IGD or research, and tightly constrained allocation questions route into a constraint solver.

**Conditions excluding IGD**: AI agents must not apply IGD when the objective is already concrete, atomic, and directly executable; when a short deterministic sequence is obvious and cheap; when decomposition overhead would exceed the cost of performing and checking the work; or when a strict latency budget leaves no room for deliberation. A simple retrieval, transformation, calculation, or single reversible tool call requires only an acceptance check.

**Template precedence**: AI agents must not generate a fresh hierarchy when a validated fixed template, standard operating procedure, or authored method domain already covers the case. The existing method is instantiated and validated instead. Decomposing anew introduces unapproved variation and discards institutional knowledge.

**Authority boundary**: AI agents must not proceed autonomously when the objective is materially ambiguous and the missing choice expresses stakeholder values, legal authority, safety tolerance, budget ownership, or an irreversible trade-off. The correct output is a focused clarification request or an escalation, not an invented preference. Informal decomposition must never serve as the sole control for safety-critical actions requiring formal verification, licensed judgment, or explicit human authorization.

**Stability precondition**: AI agents must not decompose rapidly changing requirements into a large static tree. The decision horizon is stabilized first, assumptions and invalidation triggers are attached, or a rolling-wave approach is adopted. Decomposition must never be used merely to make work appear rigorous: if no downstream decision, assignment, check, or risk control changes because a branch exists, that branch is overhead and is removed.

***

## II. Operational Framework: Bounded Decomposition From Objective Capture to Validated Handoff

The framework proceeds through seven sequential phases. Phases 4 and 5 form a bounded loop with Phase 3, and Phase 7 may return control to Phase 5 when downstream evidence falsifies the hierarchy. All loops carry declared iteration limits.

**Entry conditions**: AI agents must begin a full decomposition run only when all seven of the following are established: an identified requester or accountable sponsor; an objective worth structuring; a known risk class; a bounded time, token, and iteration budget; a channel for clarification or escalation; a named downstream consumer; and a declared authority model stating which constraints are hard, which preferences are negotiable, and which actions require approval. Where fewer than seven entry conditions hold, the run produces a bounded clarification artifact naming the missing conditions and terminates with exit category clarification required, rather than a speculative goal tree.

### Phase 1: Objective Capture and Goal Contract Formation

**Objective**: Preserve the original request without distortion, convert it into an explicit and inspectable goal contract, and resolve or escalate ambiguity before any hierarchy is proposed.

#### Step 1.1: Capture the Objective Without Silent Improvement

**Required Actions**:

- Record the original request verbatim, preserving wording, punctuation, and any internal inconsistency.
- Capture the request source, timestamp, surrounding context, stated deadline, explicit constraints, supplied evidence, and requester identity or role.
- Mint an immutable run identifier and bind every later artifact of the run to it.
- Store the verbatim input in a field distinct from every later interpretation, so that no restatement can overwrite it.
- Compute and store a content hash of the verbatim input and of the supplied context.

**Required Outputs**:

- An immutable run identifier.
- A verbatim objective record with source, timestamp, requester, and context.
- Content hashes for the input and context.
- An inventory of supplied evidence artifacts with references.

**Quality Checkpoints**:

- The verbatim record is byte-identical to the request as received.
- The verbatim record occupies a field that no later phase writes to.
- Every supplied evidence artifact carries a resolvable reference.
- The run identifier appears on all artifacts produced by this run.

***

#### Step 1.2: Normalize the Objective Into a Goal Contract

**Required Actions**:

- Write a candidate goal statement naming the desired end state, the beneficiaries, the scope inclusions, and the scope exclusions.
- State target measures with baselines, units, and thresholds, and state the deadline or decision horizon.
- Enumerate required artifacts, prohibited outcomes, and the authority boundary defining which actions the executing system may take without approval.
- Separate facts from assumptions, and separate hard constraints from negotiable preferences, placing each into its own labelled list.
- Convert an exploratory objective into a learning outcome that reduces uncertainty enough to decide, rather than asserting a performance outcome that is not yet controllable.
- Attach an invalidation trigger to every assumption, stating the observation that would falsify it.

**Required Outputs**:

- A goal contract with end state, beneficiaries, scope boundaries, measures, targets, horizon, artifacts, prohibitions, and authority boundary.
- A labelled assumption list with an invalidation trigger per assumption.
- A hard-constraint list and a separate preference list.
- A declared objective class of performance or learning.

**Quality Checkpoints**:

- Every target measure carries a baseline, a unit, and a threshold; a measure missing any of the three is returned to clarification.
- No item appears in both the hard-constraint list and the preference list.
- Every assumption carries exactly one invalidation trigger.
- The authority boundary names at least one action class requiring approval, or explicitly records that no approval class applies.
- The goal contract states an end state, not an activity.

***

#### Step 1.3: Run the Ambiguity and Contradiction Gate

**Required Actions**:

- Inspect every undefined term, unstated baseline, missing target, conflicting constraint, uncertain owner, unavailable input, and value-laden choice in the goal contract.
- Apply the structural test for each finding: determine whether two reasonable interpretations would yield materially different child goals.
- Continue under a documented assumption where no structural difference arises.
- Select the least risky interpretation, label it explicitly, and continue where the difference is low consequence and reversible.
- Pause and issue the smallest clarification that would change the structure where the finding affects scope, safety, legality, money, public commitments, irreversible actions, or evaluation.
- Detect logically contradictory constraints, return the minimal conflicting set with the available relaxation choices, and refuse to decompose an impossible contract.
- Present between two and four materially different interpretations when requesting clarification, stating for each how the hierarchy would change.

**Required Outputs**:

- An ambiguity register with one row per finding, its class, its structural impact, and its disposition.
- A documented assumption set for findings resolved without clarification.
- A clarification request listing questions ranked by structural impact, where clarification is required.
- A minimal conflicting constraint set with relaxation options, where contradiction is detected.

**Quality Checkpoints**:

- Every ambiguity register row carries a disposition of assumed, resolved, escalated, or blocking.
- No finding classified as value-laden, irreversible, or safety-relevant carries a disposition of assumed.
- The clarification request contains no more than five questions; a request exceeding five questions indicates the goal contract is under-specified and returns to Step 1.2.
- Every presented interpretation states a distinct structural consequence for the hierarchy.
- No decomposition proceeds while a blocking contradiction remains open.

***

### Phase 2: Admission, Budgeting, and Lens Selection

**Objective**: Decide whether decomposition is the correct method, bound the cost of the decomposition before it begins, and select the organizing principle that will govern sibling generation.

#### Step 2.1: Apply the Complexity and Routing Gate

**Required Actions**:

- Score the objective on seven complexity signals: number of distinct outcomes, number of domains, number of actors, number of known dependencies, number of hard constraints, number of material unknowns, and number of irreversible decisions.
- Route to direct execution where a single actor can complete and verify the request within a bounded sequence of no more than five actions, and record exit category direct execution.
- Search the template and method library for a validated match, instantiate the matched method, and record exit category template substitution where a match is found.
- Route to a constraint solver any subproblem whose difficulty is combinatorial assignment, scheduling, routing, or exclusivity rather than semantic structuring.
- Admit the objective to full decomposition only where none of the preceding routes applies.
- Record the routing decision with its triggering signal values.

**Required Outputs**:

- A complexity signal vector with seven scored dimensions.
- A routing decision naming the selected route and its rationale.
- A template search record listing candidate templates and match verdicts.

**Quality Checkpoints**:

- The routing gate consumes no more than 5 percent of the run's total token budget; exceeding this indicates the gate is itself performing decomposition and it is truncated.
- The template library was searched before a fresh hierarchy was authorized.
- Objectives scoring 2 or fewer on all seven complexity signals are routed to direct execution rather than admitted.
- Every routing decision names the signal values that triggered it.

***

#### Step 2.2: Set the Decomposition Budget

**Required Actions**:

- Set a maximum depth, defaulting to 3 levels below the root for lightweight runs and 5 levels for full runs.
- Set a maximum children per node, defaulting to 7, above which the sibling set is treated as a symptom of a missing intermediate layer.
- Set a maximum refinement round count, defaulting to 3 for lightweight runs and 6 for full runs.
- Set token, monetary, and wall-clock ceilings, and set the no-progress limit at 2 consecutive rounds without a resolved defect.
- Set the human review threshold, naming the risk tier, financial exposure, or irreversibility class above which approval is mandatory before handoff.
- Record every budget value in the run record before the first candidate is generated.

**Required Outputs**:

- A decomposition budget record with depth, breadth, round, token, cost, time, and no-progress limits.
- A declared human review threshold with its triggering condition.

**Quality Checkpoints**:

- Every budget dimension carries a numeric value; an unset dimension halts the run.
- The human review threshold names a categorical or numeric trigger, not a judgment call.
- Budget values were written before generation began, not fitted afterwards.
- The no-progress limit is set at or below the refinement round limit.

***

#### Step 2.3: Select the Decomposition Lens

**Required Actions**:

- Select one primary lens before proposing any children, using the selection table below.
- Adopt the outcome lens as the backbone unless a stated condition selects otherwise.
- Apply the remaining lenses as omission tests against the sibling set produced by the primary lens, rather than as parallel partitions.
- Label every child with the lens that produced it where more than one lens contributes to a sibling set.
- Reject any sibling set mixing lenses without labels.

**Lens selection matrix**:

| Lens | Question it asks | Select as primary when | Characteristic failure |
| :-- | :-- | :-- | :-- |
| **Outcome** | Which observable states jointly establish the parent | Default for all objectives with declared acceptance criteria | Misses capabilities that no single outcome names |
| **Capability** | Which capabilities must exist before outcomes are reachable | The objective depends on absent skills, tools, or infrastructure | Produces activity nodes rather than state nodes |
| **Lifecycle** | Which phase outcomes must be achieved in sequence | The objective follows an established staged process | Encodes calendar order as if it were contribution |
| **Risk** | Which safeguards and mitigations must hold | Risk tier is high or the objective is irreversible | Produces guardrails without outcome coverage |
| **Stakeholder** | Which beneficiary or accountable group needs a distinct result | Multiple parties hold non-substitutable acceptance criteria | Mirrors the organization chart rather than the outcome |
| **System** | Which components or interfaces must change | The objective maps onto a known component boundary | Fragments a single outcome across components |

**Required Outputs**:

- A declared primary lens with its selection rationale.
- A secondary lens list used for omission testing.
- A lens label attached to every child in mixed sibling sets.

**Quality Checkpoints**:

- Exactly one primary lens is declared per parent node.
- At least 2 secondary lenses were applied as omission tests; fewer than 2 returns the sibling set for re-testing.
- No sibling set contains an unlabelled mixture of lenses, such as one child named for a team beside one named for a lifecycle phase.
- The selected lens produces children that are states rather than activities, or the lens selection is revisited.

***

### Phase 3: Candidate Generation and Node Contract Drafting

**Objective**: Produce genuinely distinct candidate hierarchies where uncertainty warrants them, and express every proposed child as a complete, inspectable node contract.

#### Step 3.1: Generate Competing Candidate Hierarchies

**Required Actions**:

- Generate between 2 and 3 candidate hierarchies whenever the objective admits competing structures, and exactly 1 where the structure is dictated by a validated template or by an unambiguous acceptance criterion set.
- Construct candidates from materially different lenses, such as an outcome-first candidate against a risk-first candidate, rather than paraphrasing one list.
- Decompose sequentially where earlier subproblem results inform later ones, making solved subproblems available to subsequent generation rather than solving all children independently.
- Delegate a subgoal to a specialized generator or a symbolic routine where that subgoal is of a kind such a routine handles reliably.
- Apply bounded branching with lookahead and backtracking where an early structural choice is consequential, capping explored branches at 3 per decision point.
- Retain every rejected candidate with its identifier, generation method, seed, and node and edge counts.

**Required Outputs**:

- Between 1 and 3 candidate hierarchies, each with a distinct generating lens recorded.
- A candidate register listing generation method, seed, node count, and edge count per candidate.
- A retained record of discarded structures with rejection reasons pending selection.

**Quality Checkpoints**:

- Candidates differ in at least 40 percent of their required child outcomes when measured by semantic alignment; candidates below this threshold are treated as one candidate and regenerated.
- No candidate exceeds the maximum breadth or depth set in Step 2.2.
- Search expansion is bounded at 3 branches per decision point; exceeding this halts expansion and records a budget event.
- Every candidate records the lens that generated it.

***

#### Step 3.2: Write Each Child as a Node Contract

**Required Actions**:

- State for every child the outcome, the rationale linking it to the parent, the parent identifier, the scope, the measure, the target, the evidence specification, the deadline or checkpoint, the owner or executor class, the estimated effort, the required inputs, the produced outputs, the assumptions, the hard constraints, the risks, and the confidence.
- Assign a stable node identifier and a version to every node.
- Classify every child as required, conditional, optional, or guardrail.
- Record which parent acceptance criteria and guardrails the child covers, by criterion identifier.
- Reject verbs naming activity rather than state, including analyze, support, review, and work on, unless the produced output and acceptance evidence render the result testable.
- Convert every outcome expressed as an activity into a state statement naming what will be true when the activity has succeeded.

**Required Outputs**:

- A node contract per child, populated across all sixteen fields.
- A criterion coverage mapping from child identifiers to parent criterion identifiers.
- A node identifier and version assignment for every node in every candidate.

**Quality Checkpoints**:

- 100 percent of required children carry a measure, a target, and a named evidence specification; a required child missing any of the three is rewritten before validation.
- Every child names at least one parent criterion it covers, or is reclassified as optional and flagged for removal.
- No required child's outcome statement is an activity verb without a defined resulting state.
- Node identifiers are unique across the candidate and stable across versions.
- Every conditional child names the condition that activates it.

***

### Phase 4: Local and Collective Validation

**Objective**: Test every child in isolation, record uncertainty at criterion granularity, and then test the sibling set as a whole against the parent contract until coverage closes or the budget is exhausted [17][18].

#### Step 4.1: Validate Each Child Locally

**Required Actions**:

- Test each child against all six sibling tests defined in Section 1.3.
- Apply the four adversarial questions to each child: whether it could be marked complete without advancing the parent; whether the parent could fail even if the child succeeds; whether no observer could determine that the child succeeded; and whether another child already owns the same result.
- Rewrite or remove any child for which an adversarial question exposes a defect.
- Reclassify as an assumption or dependency any child whose outcome the named owner cannot control.
- Verify that each child's evidence specification names evidence that is available, credible, and discoverable at the checkpoint where it will be evaluated.
- Create an information subgoal wherever a child's evidence does not yet exist.

**Required Outputs**:

- A per-child validation record with a verdict against each of the six tests.
- An adversarial question record with four answers per child.
- A defect list with the disposition of rewrite, remove, reclassify, or accept.
- Information subgoals created for missing evidence.

**Quality Checkpoints**:

- Every required child passes all six sibling tests; a child failing any test does not enter sibling validation.
- All four adversarial questions were answered for 100 percent of required children.
- No child assigns an uncontrollable outcome to a named owner.
- Every evidence specification names a source, an access path, and an evaluation time.

***

#### Step 4.2: Record Disaggregated Confidence

**Required Actions**:

- Record separate confidence values for interpretation correctness, necessity, coverage contribution, feasibility, measurability, dependency accuracy, and evidence availability.
- Record the elicitation method for each confidence value and whether the value is calibrated against observed outcomes.
- Store validator and reviewer judgments in fields distinct from generator self-ratings.
- Route to external evidence gathering or human review any node whose impact is high and whose confidence on any dimension falls below the review threshold.
- Prohibit aggregation that averages a near-zero safety or feasibility confidence against high confidence on other dimensions.

**Required Outputs**:

- A seven-dimension confidence vector per node with elicitation method and calibration status.
- A separated record of generator self-ratings, validator results, and human reviewer judgments.
- A review queue of high-impact low-confidence nodes.

**Quality Checkpoints**:

- No node carries a single scalar confidence in place of the seven-dimension vector.
- Confidence below 0.5 on feasibility, dependency accuracy, or evidence availability for a high-impact node routes that node to review; proceeding without review is a defect.
- Generator self-ratings are never written into validator result fields.
- No aggregate confidence figure conceals a dimension scoring below 0.3.

***

#### Step 4.3: Validate Siblings as a Set and Close the Coverage Loop

**Required Actions**:

- Trace every parent success criterion and every guardrail to at least one child or to a retained parent-level check.
- Construct counterexamples by assuming every child passes and then describing how the parent could still fail.
- Convert every credible counterexample into a candidate missing child, constraint, dependency, or validation step.
- Search the sibling set for duplicated scope, incompatible targets, conflicting assumptions, missing stakeholders, omitted integration work, and unsupported handoffs.
- Declare a shared interface wherever legitimate overlap exists, naming the shared outcome, the owning node, and the consuming nodes.
- Rerun local validation and then parent coverage after each refinement, continuing the loop until no material uncovered criterion remains or the refinement budget from Step 2.2 is reached.
- Interpret collective exhaustiveness relative to the declared scope, assumptions, and risk tolerance, not over every conceivable activity.

**Required Outputs**:

- A criterion traceability matrix mapping every parent criterion and guardrail to covering nodes.
- A counterexample register with disposition per counterexample.
- An overlap register naming declared shared interfaces.
- A coverage loop record listing rounds executed, defects resolved per round, and the terminating condition.

**Quality Checkpoints**:

- 100 percent of root outcome criteria and guardrails trace to at least one required leaf or retained parent-level check; any uncovered criterion blocks progression to Phase 5.
- At least 3 counterexamples were attempted per parent node with 3 or more required children; fewer than 3 returns the set for further challenge.
- Every retained overlap carries a declared shared interface; undeclared overlap is a defect.
- The coverage loop terminated on closure or on a recorded budget limit, never on an unrecorded stop.
- No sibling set contains two children with incompatible targets on the same measure.

***

### Phase 5: Dependency Mapping, Feasibility, and Bounded Refinement

**Objective**: Convert the validated hierarchy into a dependency graph, establish that the graph is executable under real constraints, and refine only the nodes whose defects justify the cost.

#### Step 5.1: Map Dependencies and Interfaces

**Required Actions**:

- Identify for each child its prerequisites, data inputs, produced artifacts, required approvals, resource needs, temporal windows, and the conditions that can invalidate it.
- Classify every edge as precedence, data, resource, approval, mutual exclusion, or conditional trigger.
- Declare explicit join semantics on every inbound edge set, selecting all predecessors, any one predecessor, a numeric threshold, or a named condition.
- Run a cycle check and a topological sort over the resulting graph.
- Repair an accidental cycle by changing scope, separating an outcome from its verification, or defining an intermediate artifact.
- Represent an intentional loop with a trigger condition, a maximum iteration count, a progress test, and a named stop reason.
- Detect orphan nodes with neither inbound nor outbound edges and neither a parent criterion nor an independent acceptance test.
- Defer critical-path analysis until durations and dependencies are credible, and label the longest dependent sequence only where duration estimates carry a stated confidence.

**Required Outputs**:

- A typed dependency edge set with source, destination, type, required predecessor state, condition, and join semantics.
- A cycle check result and a topological ordering, or a named set of intentional bounded loops.
- An orphan node list with dispositions.
- A critical-path classification where duration estimates support it, or an explicit statement that duration data is insufficient.

**Quality Checkpoints**:

- Zero unintentional cycles remain; any remaining cycle blocks handoff.
- Every intentional loop declares a trigger, a progress measure, a maximum iteration count, and an exit condition; a loop missing any of the four is converted to an acyclic sequence or rejected.
- 100 percent of edges carry a declared type and join semantics.
- Every orphan node is removed, connected, or justified by an independent acceptance test.
- No dependency is recorded in prose alone; all dependencies exist as typed, versioned edges.

***

#### Step 5.2: Check Feasibility, Constraints, and Risk

**Required Actions**:

- Verify for each candidate tree that the required tools, skills, permissions, budgets, time, data, and environments exist.
- Confirm that hard constraints remain untouched and that only declared preferences are scored or traded.
- Check whether success criteria conflict, whether any child's output can invalidate a sibling, and whether all dependencies can be satisfied before their deadlines.
- Pass explicit models of difficult assignment or scheduling questions to a constraint solver rather than resolving them by narrative reasoning.
- Classify any detected infeasibility precisely using the classification table below.
- Return the smallest useful explanation, the supporting evidence, and the available remediation choices for every infeasibility finding.
- Relax only declared preferences; never weaken a target, safety guardrail, approval requirement, or legal constraint without an authorized decision.

**Infeasibility classification**:

| Class | Diagnostic signature | Permitted remediation |
| :-- | :-- | :-- |
| **Logically contradictory** | Two or more constraints cannot hold simultaneously under any assignment | Return the minimal conflicting set and request prioritization |
| **Resource-infeasible** | Required budget, staffing, or capacity exceeds the declared ceiling | Narrow scope, add resources, or stage delivery |
| **Temporally infeasible** | The dependency-respecting earliest finish exceeds the deadline | Extend the date, reduce scope, or parallelize with declared risk |
| **Unauthorized** | A required action falls outside the declared authority boundary | Obtain permission or escalate; never proceed by inference |
| **Unverifiable** | No available evidence can establish a required criterion | Create an information subgoal or redefine the criterion |
| **Outside known capabilities** | No available actor or tool can produce the required outcome | Acquire the capability, substitute an approach, or narrow scope |
| **Uncertain, information missing** | Feasibility cannot be determined from available information | Create a diagnostic subgoal and re-evaluate at a checkpoint |

**Required Outputs**:

- A feasibility verdict per candidate tree with supporting evidence.
- An infeasibility register with class, evidence, certainty, and remediation options per finding.
- A constraint-versus-preference audit confirming that no hard constraint was scored or traded.
- Solver invocation records for combinatorial subproblems.

**Quality Checkpoints**:

- Every infeasibility finding carries exactly one class from the table and at least 1 remediation option.
- Zero hard constraints appear in any scored trade-off; a hard constraint entering a trade-off halts the run.
- Every infeasibility finding is labelled certain or uncertain, and uncertain findings name the information that would resolve them.
- Combinatorial subproblems were routed to a solver rather than resolved by generation; a narrative resolution of a scheduling or assignment problem is a defect.

***

#### Step 5.3: Refine Only the Nodes That Need It

**Required Actions**:

- Select a leaf for re-decomposition only where it remains ambiguous, contains several independently verifiable outcomes, hides internal dependencies, cannot be assigned, cannot be estimated, lacks a completion test, exceeds the executor's capability, or carries risk above the declared leaf threshold.
- Order refinement by risk and by blocking impact, selecting the highest-risk or most-blocking leaf first rather than the longest-worded one.
- Create children for the selected leaf, validate them locally, revalidate the sibling set, update the dependency graph, and rerun feasibility.
- Separate the planning act from the execution act, producing a subtask plan before carrying any step out, so that missing-step errors surface during planning.
- Continue refinement until every required leaf is operationally ready, rejected, or explicitly delegated to a planner with an appropriate formalism.
- Stop the loop when all leaves pass; when no refinement reduces uncertainty; when the same tree shape or defect recurs; when the depth or iteration budget is reached; or when human input becomes necessary.
- Record the selected leaf, defect category, old and new depth, children introduced, criteria improved, and whether the change resolved the cited defect for each refinement event.

**Required Outputs**:

- A refinement queue ordered by risk and blocking impact.
- A refinement event record per round with defect category and resolution verdict.
- An updated hierarchy with asymmetric depth reflecting risk rather than uniformity.
- A declared loop termination reason.

**Quality Checkpoints**:

- No leaf is refined that already satisfies operational readiness; unnecessary refinement is a budget defect.
- The refinement loop terminated on one of the five named stop conditions, recorded explicitly.
- Depth varies across branches where risk varies; uniform depth across branches of differing risk is a defect requiring justification.
- At least 60 percent of refinement events resolved their cited defect without introducing a new material defect; below this threshold the generation approach is changed rather than repeated.
- No refinement round exceeded the no-progress limit of 2 consecutive rounds without a resolved defect.

***

### Phase 6: Adversarial Challenge, Selection, and Version Freeze

**Objective**: Subject the surviving hierarchy to independent critique under stress, select among candidates on stated grounds, and freeze the selection as an immutable, attributable version.

#### Step 6.1: Challenge the Whole Hierarchy

**Required Actions**:

- Run an independent critique, performed by an agent or reviewer that did not generate the hierarchy, wherever the risk tier justifies the cost.
- Test at least six scenarios: one normal, one missing-input, one dependency failure, one deadline or resource stress, one changed-assumption, and one adversarial interpretation.
- Ask for each scenario whether the hierarchy still preserves the original objective, whether every failure becomes visible, whether guardrails survive, and whether escalation occurs before any unsafe action.
- Apply simulation where the system is consequential or dynamic and a world model is available.
- Withhold generator confidence values from the independent semantic reviewer, so that review is not anchored on self-assessment.
- Require human sign-off where the decomposition sets policy or commits resources beyond delegated authority.

**Required Outputs**:

- A scenario test record with one row per scenario and four verdicts per row.
- An independent critique report separated from generator artifacts.
- A simulation result set where simulation was applied.
- A human sign-off record where the review threshold was triggered.

**Quality Checkpoints**:

- At least 6 scenarios were tested for full decompositions; fewer than 6 blocks selection.
- The independent reviewer received no generator confidence values.
- Every scenario in which a failure would remain invisible produced a corrective node, constraint, or monitor.
- Guardrail criteria survive all 6 scenarios; a guardrail defeated by any scenario returns the hierarchy to Phase 5.
- Human sign-off is present wherever the Step 2.2 threshold was triggered.

***

#### Step 6.2: Select and Freeze the Goal-Tree Version

**Required Actions**:

- Score each candidate on semantic coverage, measurability, feasibility, absence of unnecessary overlap, dependency clarity, risk control, and complexity appropriateness.
- Select the candidate with the best combination across those seven dimensions and record the reason each alternative was rejected.
- Freeze the selected version with a content hash, a schema version, model and prompt versions, the assumption set, evidence references, validator results, and approver identity where approval was required.
- Retain all rejected candidates with their scores and rejection reasons rather than discarding them.
- Establish that later changes create a new version with a stated reason and a lineage link, and that no existing version is rewritten.

**Required Outputs**:

- A candidate scorecard across seven selection dimensions.
- A frozen tree version with content hash, schema version, model and prompt versions, assumptions, evidence references, and validator results.
- A retained rejected-candidate archive with rejection rationale.
- A lineage record linking this version to any predecessor.

**Quality Checkpoints**:

- All 7 selection dimensions were scored for every candidate; an unscored dimension blocks selection.
- The frozen version's content hash reproduces from its stored contents.
- Every rejected candidate carries a stated rejection reason; discarding a candidate without a reason is a provenance defect.
- No prior version was modified during the freeze; history is append-only.
- Approver identity is recorded wherever approval was required.

***

### Phase 7: Handoff, Closure, and Evidence-Driven Reopening

**Objective**: Transfer the frozen hierarchy to the downstream consumer without semantic loss, close the run under a declared exit category, and reopen the smallest affected subtree when downstream evidence contradicts the hierarchy.

#### Step 7.1: Hand Off Without Losing Semantics

**Required Actions**:

- Transfer the original objective, the normalized goal contract, the selected hierarchy, node metadata, dependency edges, hard constraints, assumptions, acceptance evidence, unresolved risks, and required approvals to the downstream consumer.
- Translate leaf outcomes into tasks only at this boundary, and never earlier.
- Preserve a link from every generated task to the goal criterion it serves and to the tree version it derives from.
- Confirm that the receiving orchestrator or planner acknowledges acceptance, and record any leaf it rejects as unexecutable.
- Recognize that runtime tooling tracks state, retries, monitoring, and dynamic branching, and that such tooling orchestrates a decomposition without validating its semantics.
- Record the downstream consumer's identity and version alongside the handoff.

**Required Outputs**:

- A handoff package containing all ten transferred elements.
- A task-to-criterion linkage table with tree version references.
- A downstream acceptance record with any rejected leaves listed.

**Quality Checkpoints**:

- 100 percent of handed-off tasks link to a named leaf and a tree version; an unlinked task is rejected at the boundary.
- Every hard constraint and guardrail present in the goal contract appears in the handoff package.
- No leaf outcome was converted into a task before this step.
- The downstream consumer's acceptance or rejection is recorded for every leaf.

***

#### Step 7.2: Close the Run Under a Declared Exit Category

**Required Actions**:

- Assign exactly one exit category from the table below, and record the evidence supporting it.
- Verify for the approved-hierarchy exit that the hierarchy is versioned, acyclic or explicitly loop-bounded, that required leaves are measurable and feasible under declared assumptions, that every parent criterion is covered, and that the hierarchy is ready for planning or orchestration.
- Record for every non-approval exit the reason, the evidence, and the next action available to the requester.
- Emit the best validated partial tree where the exit is budget exhaustion, marked as partial and not approved.
- Close the run record with end timestamps, total tokens, total cost, event count, and final exit category.

**Exit categories**:

| Exit category | Precondition | Artifact returned |
| :-- | :-- | :-- |
| **Approved hierarchy** | All Phase 6 checkpoints pass and handoff is accepted | Frozen tree version plus handoff package |
| **Direct execution** | Routing gate found the objective atomic and cheap | Acceptance check result |
| **Template substitution** | A validated method or workflow matched the objective | Instantiated method with validation record |
| **Infeasible** | An infeasibility class is established with evidence | Infeasibility register with remediation options |
| **Clarification required** | A structural ambiguity affects scope, safety, money, or evaluation | Ranked clarification request with interpretations |
| **Safe refusal** | The objective requires unauthorized or unsafe action | Refusal record naming the violated boundary |
| **Cancelled** | The requester withdrew the objective | Partial artifacts with cancellation timestamp |
| **Budget exhausted** | A declared budget limit was reached before closure | Best validated partial tree marked partial |

**Required Outputs**:

- A single declared exit category with supporting evidence.
- A closed run record with timing, cost, and event totals.
- The artifact corresponding to the declared exit category.

**Quality Checkpoints**:

- Exactly 1 exit category is assigned; multiple or absent categories are a closure defect.
- No partial tree is emitted without a partial marker.
- Clarification, infeasibility, template routing, direct execution, and safe refusal are recorded as distinct categories and never merged into a single failure count.
- The run record's end timestamp, token total, and cost total are populated.

***

#### Step 7.3: Reopen the Smallest Affected Subtree on Downstream Evidence

**Required Actions**:

- Monitor downstream signals for an unexecutable leaf discovered during planning, a missing dependency discovered during orchestration, an assumption falsified during execution, or an evaluation showing that successful children did not achieve the parent.
- Reopen only the affected node and its minimal sufficient subtree, preserving completed valid work elsewhere.
- Create a new tree version with a stated reason and a lineage link to the prior version rather than editing the prior version.
- Rerun ancestor coverage checks and dependency checks after repair, and hand off only the delta rather than the whole hierarchy.
- Detect oscillation by comparing defect signatures and tree signatures across reopenings, and escalate rather than rewording the hierarchy again when the same defect and signature recur without new evidence.
- Attach a reviewed cause to every downstream failure attributed to decomposition, drawn from missing subgoal, redundant subgoal, wrong dependency, unmeasurable criterion, infeasible target, stale assumption, scope drift, incorrect handoff, or execution failure unrelated to decomposition.

**Required Outputs**:

- A reopening record naming the trigger signal, the affected node, and the repaired subtree scope.
- A new tree version with lineage and reason.
- A delta handoff package for the downstream consumer.
- A cause attribution record per attributed downstream failure.

**Quality Checkpoints**:

- The repaired subtree is the smallest subtree containing the defect; repairing the full hierarchy for a leaf defect is a scope defect.
- No prior tree version was overwritten during repair.
- Oscillation halts after 2 reopenings with an identical defect signature and no new evidence, escalating to human review.
- Every attributed downstream failure carries exactly one reviewed cause from the nine-value list.
- Ancestor coverage and dependency checks were rerun after repair, not assumed unchanged.

***

## III. Implementation Guidance for AI Agents

AI agents executing Intelligent Goal Decomposition must operate under an explicit control plane, emit provenance at every state transition, and treat generated hierarchies as candidates subject to independent validation. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Orchestrator Agent**: Owns the run identifier, holds the decomposition budget, enforces phase transitions, and assigns the exit category. Never generates goal nodes itself, so that budget enforcement remains independent of generation.
2. **Intake Agent**: Executes Phase 1. Captures the verbatim objective, builds the goal contract, and operates the ambiguity gate. Holds the authority to halt a run for clarification without orchestrator approval.
3. **Routing Agent**: Executes Phase 2. Scores complexity, searches the template library, and selects the route. Requires read access to the validated method and template library.
4. **Generator Agent**: Executes Phase 3 and the child-creation portion of Step 5.3. Produces candidate hierarchies and node contracts. Its confidence outputs are recorded but never treated as validation.
5. **Structural Validator**: Executes deterministic checks on required fields, identifier uniqueness, graph cycles, budget limits, join semantics, and traceability completeness. Produces pass or fail verdicts without semantic judgment.
6. **Semantic Reviewer Agent**: Executes Phase 4 sibling validation and Phase 6 critique. Operates without visibility into generator confidence values, so that review is independent rather than confirmatory.
7. **Feasibility Agent**: Executes Step 5.2. Holds connections to capability registries, resource models, and constraint solvers. Classifies infeasibility and never relaxes hard constraints.
8. **Handoff Agent**: Executes Phase 7. Builds the handoff package, records downstream acceptance, and monitors for reopening triggers.

**Separation of duties requirement**: The Generator Agent and the Semantic Reviewer Agent must not share a context window, a confidence store, or a prompt lineage. Where a single model instance performs both functions, the review pass must receive the hierarchy without generation rationale or confidence values attached. A review conducted with generator confidence in context is recorded as self-approval and does not satisfy Phase 6.

**Workflow Execution Pattern**:

```
STATE: PHASE_4_VALIDATION
ENTRY GUARD:
  - goal_contract_frozen == TRUE
  - candidate_count BETWEEN 1 AND 3
  - decomposition_budget_declared == TRUE
ACTIONS:
  1. FOR EACH required child: RUN six_sibling_tests
  2. FOR EACH required child: RUN four_adversarial_questions
  3. FOR EACH node: EMIT confidence_vector WITH 7 DIMENSIONS
  4. TRACE every parent criterion TO covering node
  5. GENERATE counterexamples (MINIMUM 3 PER PARENT WITH >=3 CHILDREN)
  6. REFINE sibling set; RERUN steps 1 THROUGH 5
VALIDATION:
  - uncovered_root_criteria == 0
  - required_children_failing_any_sibling_test == 0
  - nodes_with_scalar_confidence == 0
  - undeclared_overlap_count == 0
  - coverage_rounds <= refinement_round_limit
TRANSITIONS:
  IF all_validations_pass THEN next_state = PHASE_5_DEPENDENCY_MAPPING
  ELIF coverage_rounds >= refinement_round_limit THEN
       next_state = EXIT_BUDGET_EXHAUSTED
  ELIF blocking_ambiguity_detected THEN next_state = PHASE_1_AMBIGUITY_GATE
  ELSE next_state = PHASE_4_VALIDATION
```

**Three-Stage Action Pattern**:

1. **Propose**: Emit the candidate hierarchy and node contracts without committing to a selection, and without generating any downstream task.
2. **Validate**: Run structural validation and independent semantic review while the hierarchy is still cheap to restructure, before dependency mapping and feasibility work is invested.
3. **Commit**: Freeze the version, hand off, and only then permit task generation. Task generation before commitment is a protocol violation, because it converts unvalidated outcomes into executable work.

**Approval gate**: Human authorization is mandatory before handoff wherever the decomposition sets policy, commits resources beyond the delegated authority declared in the goal contract, alters a safety guardrail, or carries a risk tier at or above the threshold declared in Step 2.2. The orchestrator must block the transition from Phase 6 to Phase 7 until the approval record is present. An approval that arrives after handoff does not satisfy this gate.

**Context Management Requirements**:

- Hold the goal contract and the criterion traceability matrix in working context for the whole run; page candidate node contracts in and out by branch.
- Validate one sibling set per working pass rather than the whole hierarchy, so that context consumption scales with branching factor rather than with tree size.
- Persist every node contract, edge, and event to durable storage as it is produced, so that a context exhaustion event loses no validated work.
- Write a handoff record naming completed phases, pending phases, the frozen goal contract, and the current tree version wherever a run exceeds the context available for a single pass.
- Never rely on context recall for the verbatim objective; re-read it from its immutable field at Phase 6 and Phase 7 to detect scope drift.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract Integrity (After Phase 1)**

- **Automated Check**: Verbatim record hash matches the received input; every target measure carries a baseline, unit, and threshold; every assumption carries an invalidation trigger; no term appears in both the constraint and preference lists.
- **Agent Action on Pass**: Proceed to the routing gate.
- **Agent Action on Failure**: Return the specific contract defect and re-run Step 1.2 for the affected fields only.
- **Human Review Trigger**: Any ambiguity classified as value-laden, irreversible, safety-relevant, or legally consequential.

**Checkpoint 2: Admission and Budget (After Phase 2)**

- **Automated Check**: Exactly one route selected; template library searched; all seven budget dimensions carry numeric values; human review threshold declared.
- **Agent Action on Pass**: Proceed to candidate generation.
- **Agent Action on Failure**: Halt; a run without a declared budget cannot be bounded and must not generate.
- **Human Review Trigger**: Complexity signals indicate full decomposition while the declared budget permits fewer than 2 refinement rounds.

**Checkpoint 3: Node Contract Completeness (After Phase 3)**

- **Automated Check**: 100 percent of required children carry measure, target, and evidence specification; every child maps to at least one parent criterion; node identifiers unique; no required child's outcome is an unqualified activity verb.
- **Agent Action on Pass**: Proceed to validation.
- **Agent Action on Failure**: Return the list of incomplete node contracts; regenerate those nodes only.
- **Human Review Trigger**: More than 30 percent of generated children fail the activity-versus-outcome test, indicating a lens selection defect.

**Checkpoint 4: Coverage Closure (After Phase 4)**

- **Automated Check**: Zero uncovered root criteria or guardrails; zero required children failing a sibling test; zero scalar confidence values; zero undeclared overlaps; counterexample minimum satisfied.
- **Agent Action on Pass**: Proceed to dependency mapping.
- **Agent Action on Failure**: Return to the coverage loop for uncovered criteria only, respecting the round limit.
- **Human Review Trigger**: A root criterion remains uncovered after the refinement round limit is reached.

**Checkpoint 5: Graph and Feasibility Integrity (After Phase 5)**

- **Automated Check**: Zero unintentional cycles; every loop bounded with four declared elements; 100 percent of edges typed with join semantics; zero orphan nodes without justification; zero hard constraints in scored trade-offs.
- **Agent Action on Pass**: Proceed to adversarial challenge.
- **Agent Action on Failure**: Halt; a cyclic or unbounded graph must not reach review.
- **Human Review Trigger**: Any infeasibility classified as unauthorized, or any temporal infeasibility against a committed external deadline.

**Checkpoint 6: Independent Review Sufficiency (After Phase 6)**

- **Automated Check**: At least 6 scenarios tested; reviewer received no generator confidence; all 7 selection dimensions scored; frozen hash reproduces; approver identity present where required.
- **Agent Action on Pass**: Proceed to handoff.
- **Agent Action on Failure**: Return the hierarchy to Phase 5 for the branches implicated by failed scenarios.
- **Human Review Trigger**: Any scenario in which a guardrail is defeated, or in which an unsafe action would occur before escalation.

**Checkpoint 7: Handoff and Closure (After Phase 7)**

- **Automated Check**: 100 percent of tasks linked to a leaf and tree version; every guardrail present in the package; downstream acceptance recorded per leaf; exactly one exit category assigned.
- **Agent Action on Pass**: Close the run and begin downstream monitoring.
- **Agent Action on Failure**: Halt handoff; return unlinked tasks and missing guardrails.
- **Human Review Trigger**: The downstream consumer rejects more than 20 percent of handed-off leaves as unexecutable, indicating a readiness-standard mismatch.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
RUN_ID:
TREE_VERSION:
PHASE_BOUNDARY:
AUTOMATED_CHECKS_RUN:
MEASURED_VALUES:
PASS_CONDITION:
VERDICT:
FAIL_ACTION_TAKEN:
HUMAN_REVIEW_TRIGGERED:
RESPONSIBLE_AGENT:
TIMESTAMP:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Resolvable Ambiguity Mistaken for Preference Ambiguity**

- **Symptoms**: The run halts for clarification on a question that retrieval, measurement, or inspection could answer; clarification volume exceeds five questions per run.
- **Diagnostic Steps**: Classify each open question as resolvable by evidence or as an expression of stakeholder value. Test whether any accessible source, measurement, or inspection would settle it.
- **Resolution Protocol**: Option A, convert the resolvable question into an information subgoal and continue decomposition under a labelled assumption. Option B, batch the genuinely value-laden questions into a single ranked clarification request. Option C, where the requester is unavailable, decompose only to the next stable decision point and mark deeper branches as pending clarification.
- **Escalation Trigger**: More than 2 clarification rounds on the same objective without a structural change to the goal contract.

**Error Type 2: Objective Is Infeasible**

- **Symptoms**: Feasibility checks fail on capability, resource, time, authority, or verifiability for a required branch.
- **Diagnostic Steps**: Assign the precise infeasibility class from the Step 5.2 table. Determine whether the finding is certain or uncertain, and name the evidence supporting it.
- **Resolution Protocol**: Option A, narrow scope or stage delivery. Option B, extend time or add resources with sponsor approval. Option C, obtain the missing permission through the declared escalation path. Option D, adjust a declared soft threshold with the sponsor's authorization. Option E, convert a performance goal into a learning goal that reduces uncertainty enough to decide. Under no option is a hard safety, legal, approval, or guardrail constraint offered as tradeable.
- **Escalation Trigger**: Any infeasibility classified as unauthorized escalates immediately without retry. Any other class escalates after 2 remediation attempts fail.

**Error Type 3: Objective Is Internally Contradictory**

- **Symptoms**: Two or more constraints cannot hold simultaneously; sibling targets conflict on the same measure; a guardrail and an outcome criterion are mutually exclusive.
- **Diagnostic Steps**: Compute the minimal conflicting constraint set rather than reporting the full constraint list. Confirm the conflict is logical rather than merely tight.
- **Resolution Protocol**: Option A, return the minimal set to the accountable party and request prioritization or redefinition. Option B, where one member of the conflicting set is a preference, relax the preference and record the decision. Option C, halt with exit category infeasible. Splitting contradictory requirements into separate branches and permitting both to proceed is prohibited; decomposition does not cure inconsistency.
- **Escalation Trigger**: Immediate escalation on detection; this error class is never resolved by retry or rewording.

**Error Type 4: Domain Knowledge Is Insufficient**

- **Symptoms**: Generated children are plausible but unsupported; confidence on evidence availability falls below 0.5 across a branch; no reviewer can judge measurability.
- **Diagnostic Steps**: Identify the depth at which support ends. Distinguish absent knowledge from absent evidence access.
- **Resolution Protocol**: Option A, mark the branch exploratory and require evidence-producing subgoals before further refinement. Option B, cap the branch depth at 1 level below the last supported node, since each unsupported level compounds error. Option C, route the branch to a domain expert or a retrieval process before continuing.
- **Escalation Trigger**: Speculative depth exceeding 2 levels below the last evidence-supported node.

**Error Type 5: Environment Changes Faster Than the Hierarchy**

- **Symptoms**: Assumptions are falsified during decomposition; the same branch is reopened more than twice; deadlines move during the run.
- **Diagnostic Steps**: Measure the interval between assumption invalidations against the decomposition duration. Identify which decision horizon remains stable.
- **Resolution Protocol**: Option A, decompose only to the next stable decision point, attach invalidation triggers, execute or observe, and re-enter decomposition from the observed state. Option B, convert deep branches into a rolling-wave structure with a scheduled re-entry checkpoint. Option C, reduce the decision horizon in the goal contract and reissue.
- **Escalation Trigger**: 3 or more assumption invalidations within a single run.

**Error Type 6: Decomposition Thrashing**

- **Symptoms**: Refinement events per run rise while resolved defects per event fall; the same tree signature and defect signature recur; node count grows while criterion coverage stays constant.
- **Diagnostic Steps**: Compare tree signatures and defect signatures across rounds. Compute refinement yield as defects resolved divided by refinement events.
- **Resolution Protocol**: Option A, change the decomposition lens and regenerate the affected sibling set. Option B, escalate to human review with the recurring defect named. Option C, accept the current hierarchy as partial, mark the unresolved branch, and hand off the remainder.
- **Escalation Trigger**: Refinement yield below 0.4 across 3 consecutive rounds, or 2 consecutive rounds with no resolved defect.

**Error Type 7: Self-Certification of Feasibility or Safety**

- **Symptoms**: A feasibility or safety verdict traces only to generator output; validator fields contain generator self-ratings; no external evidence or deterministic check supports a high-risk node.
- **Diagnostic Steps**: Trace every feasibility and safety verdict to its producing agent. Confirm that the semantic reviewer operated without generator confidence in context.
- **Resolution Protocol**: Option A, rerun the verdict through a deterministic check, a capability registry, or a constraint solver. Option B, obtain independent semantic review with generator artifacts withheld. Option C, escalate to a domain expert or a simulation proportional to the risk tier.
- **Escalation Trigger**: Any high-risk node whose feasibility or safety verdict has no source other than the generator halts handoff without retry.

**Troubleshooting Decision Tree**:

```
DECOMPOSITION RUN FAILS A CHECKPOINT
├─ CONTRACT DEFECT
│   ├─ Measure without baseline or threshold -> Return to goal contract
│   ├─ Constraint also listed as preference -> Reclassify, then re-gate
│   └─ Assumption without invalidation trigger -> Attach trigger or drop
├─ COVERAGE DEFECT
│   ├─ Root criterion uncovered -> Add child or retain parent-level check
│   ├─ Counterexample survives -> Convert to missing child or constraint
│   └─ Undeclared overlap -> Declare shared interface or merge nodes
├─ GRAPH DEFECT
│   ├─ Unintentional cycle -> Split outcome from verification, or
│   │                        introduce intermediate artifact
│   ├─ Loop without bound -> Add trigger, progress test, cap, exit reason
│   └─ Orphan node -> Connect, remove, or justify by acceptance test
├─ FEASIBILITY DEFECT
│   ├─ Class = UNAUTHORIZED -> HALT, escalate, no retry
│   ├─ Class = LOGICALLY CONTRADICTORY -> HALT, return minimal conflict set
│   └─ Other classes -> Offer remediation options, cap at 2 attempts
├─ REFINEMENT DEFECT
│   ├─ Yield below 0.4 over 3 rounds -> Change lens or escalate
│   └─ Same defect signature twice -> Escalate, do not reword
└─ PROVENANCE DEFECT
    ├─ Generator confidence in reviewer context -> Rerun review isolated
    ├─ Prior tree version overwritten -> HALT, restore from hash chain
    └─ Task without leaf linkage -> Reject at handoff boundary
```

**Prohibited Recovery Behaviours**: AI agents must never resolve an error by silently relaxing a deadline, target, budget, permission, or guardrail; by splitting contradictory requirements into parallel branches; by deepening a speculative branch to manufacture the appearance of rigour; by overwriting a prior tree version; or by retrying a generation that has already failed twice with the same defect signature.

### D. Provenance, Metrics, and Continuous Learning

AI agents must treat decomposition as an event-sourced, traceable decision process. Provenance models expressed in terms of entities, activities, and agents support derivation, attribution, versioning, and reproducibility, and map onto goal-tree versions, source artifacts, decomposition activities, model services, and human approvers [27]. Distributed trace conventions supply the transport model: one trace identifier connects the run, parent and child span identifiers encode hierarchy, attributes hold metadata, events represent meaningful instants, links connect causally related work across traces, and start and end timestamps support latency measurement [28].

**Run record template**:

```
RUN_RECORD
  RUN_ID:                        EXPERIMENT_OR_COHORT_ID:
  PARENT_RUN_ID (IF REPAIR):     TRACE_ID:
  ORIGINAL_OBJECTIVE_VERBATIM:   INPUT_HASH:
  NORMALIZED_OBJECTIVE:          CONTEXT_HASH:
  REQUESTER:                     ACCOUNTABLE_OWNER:
  TASK_CLASS:                    RISK_TIER:
  DECISION_HORIZON:              LOCALE:
  SOURCE_REFERENCES:             PRIVACY_CLASSIFICATION:
  HARD_CONSTRAINTS:              PREFERENCES:
  ACCEPTANCE_TEST_VERSION:       ALLOWED_TOOLS_AND_AUTHORITIES:
  MODEL_ID:                      MODEL_PROVIDER:
  DECODING_SETTINGS:             RANDOM_SEED:
  SYSTEM_PROMPT_VERSION:         DECOMPOSITION_PROMPT_VERSION:
  POLICY_VERSION:                VALIDATOR_VERSION:
  TOKEN_BUDGET:                  MONETARY_BUDGET:
  ITERATION_LIMIT:               DEPTH_LIMIT:
  START_TIMESTAMP:               END_TIMESTAMP:
  FINAL_EXIT_CATEGORY:
REPRODUCIBILITY_ENVIRONMENT
  CODE_OR_SERVICE_VERSION:       DEPENDENCY_VERSIONS:
  RETRIEVAL_INDEX_VERSION:       DATA_CUTOFF:
  FEATURE_FLAGS:                 TEMPLATE_OR_METHOD_DOMAIN_VERSION:
  DOWNSTREAM_CONSUMER_VERSION:
```

Sensitive content must be stored by protected reference or salted hash rather than copied into general telemetry. Secrets, personal data, and privileged material never enter the run record in plaintext.

**Goal-node record template**:

```
GOAL_NODE_RECORD
  NODE_ID:                       TREE_VERSION:
  PARENT_ID:                     DEPTH:          SIBLING_ORDER:
  NODE_TYPE:                     STATUS:
  OUTCOME_STATEMENT:             RATIONALE:
  SCOPE_INCLUSIONS:              SCOPE_EXCLUSIONS:
  CLASSIFICATION:                [REQUIRED | CONDITIONAL | OPTIONAL | GUARDRAIL]
  MEASURE:        BASELINE:      TARGET:         UNIT:
  DEADLINE_OR_CHECKPOINT:
  OUTCOME_EVIDENCE_SPEC:         GUARDRAIL_EVIDENCE_SPEC:
  OWNER_OR_EXECUTOR_CLASS:
  EXPECTED_INPUTS:               EXPECTED_OUTPUTS:
  RESOURCE_ESTIMATE:             EFFORT_ESTIMATE:
  ASSUMPTIONS:                   CONSTRAINTS:        RISKS:
  COVERS_PARENT_CRITERIA:        [CRITERION IDS]
  EVIDENCE_REFERENCES:
CONFIDENCE_VECTOR (DISAGGREGATED)
  INTERPRETATION:   NECESSITY:      COVERAGE:       MEASURABILITY:
  FEASIBILITY:      DEPENDENCY:     EVIDENCE_AVAILABILITY:
  ELICITATION_METHOD:              CALIBRATED: [TRUE | FALSE]
JUDGMENT_SEPARATION
  GENERATOR_SELF_RATING:
  STRUCTURAL_VALIDATOR_RESULT:
  SEMANTIC_REVIEWER_RESULT:
  HUMAN_REVIEWER_RESULT:
```

Recording which parent acceptance criteria each node covers is what makes coverage measurable rather than subjective. A self-reported probability is a feature to be evaluated, never an assurance.

**Edge and graph record template**:

```
EDGE_RECORD
  EDGE_ID:            SOURCE_NODE_ID:        DESTINATION_NODE_ID:
  EDGE_TYPE:          [PRECEDENCE | DATA | RESOURCE | APPROVAL |
                       MUTUAL_EXCLUSION | CONDITIONAL_TRIGGER]
  REQUIRED_PREDECESSOR_STATE_OR_ARTIFACT:
  CONDITION:          JOIN_SEMANTICS: [ALL | ANY | THRESHOLD n | NAMED]
  DISCOVERY_METHOD:   CONFIDENCE:     VALIDATOR_RESULT:
  VERSION_INTRODUCED:
LOOP_CONTRACT (CONDITIONAL AND ITERATIVE EDGES ONLY)
  TRIGGER:            MAX_ITERATIONS:  PROGRESS_MEASURE:  EXIT_CONDITION:
GRAPH_RECORD
  TREE_VERSION:       GRAPH_HASH:
  CYCLE_CHECK_RESULT: TOPOLOGICAL_SORT_RESULT:
  DISCONNECTED_NODES: CRITICAL_OR_NEAR_CRITICAL_CLASSIFICATION:
  NODE_COUNT:  EDGE_COUNT:  MAX_DEPTH:  MEAN_DEPTH:  BRANCHING_FACTOR:
```

**Event record template**:

```
EVENT_RECORD
  EVENT_ID:           TRACE_ID:        SPAN_ID:      PARENT_SPAN_ID:
  TIMESTAMP:          ACTOR:           EVENT_TYPE:
  EVENT_TYPE VALUES:  INTERPRETATION | CLARIFICATION | GENERATION |
                      MERGE | SPLIT | DELETION | REWRITE | REPARENT |
                      DEPENDENCY_DISCOVERY | CONSTRAINT_FAILURE |
                      FEASIBILITY_CHECK | VALIDATOR_DECISION |
                      HUMAN_REVIEW | APPROVAL | REJECTION | HANDOFF |
                      REOPEN | CLOSURE
  INPUT_NODE_VERSIONS:            OUTPUT_NODE_VERSIONS:
  TRIGGER:            REASON_CODE:    EVIDENCE:
  BEFORE_HASH:        AFTER_HASH:
  LATENCY_MS:         TOKEN_COST:     MONETARY_COST:      OUTCOME:
CLARIFICATION_EVENT_EXTENSION
  QUESTION:           WHY_IT_MATTERED:      ALTERNATIVES_PRESENTED:
  RESPONSE:           RESPONDER_AUTHORITY:  WAIT_TIME:  NODES_CHANGED:
REFINEMENT_EVENT_EXTENSION
  SELECTED_LEAF:      DEFECT_CATEGORY:      OLD_DEPTH:  NEW_DEPTH:
  CHILDREN_INTRODUCED:  CRITERIA_IMPROVED:  DEFECT_RESOLVED: [TRUE | FALSE]
CANDIDATE_COMPARISON_EXTENSION
  CANDIDATE_ID:       GENERATION_METHOD:    SEED:
  NODE_COUNT:         EDGE_COUNT:           VALIDATION_RESULTS:
  REVIEWER_SCORES:    SELECTED: [TRUE | FALSE]     SELECTION_RATIONALE:
```

Discarded structures must be retained, not only the winner. Rejected candidates reveal instability and recurring failure modes that a winners-only log conceals.

**Downstream linkage record template**:

```
DOWNSTREAM_LINKAGE_RECORD
  TASK_ID:            SOURCE_LEAF_NODE_ID:      TREE_VERSION:
  PLANNER_VERDICT:    [ACCEPTED | REJECTED]     REJECTION_REASON:
  TASK_STATUS:        ACTUAL_INPUTS:            ACTUAL_OUTPUTS:
  COMPLETION_EVIDENCE:                          FAILURE_REASON:
  RETRY_COUNT:        REPLAN_COUNT:             HUMAN_INTERVENTIONS:
  COST:               DURATION:
  VERIFIED_TOP_LEVEL_RESULT:
ATTRIBUTION
  DECOMPOSITION_ATTRIBUTED: [TRUE | FALSE]
  REVIEWED_CAUSE:     [MISSING_SUBGOAL | REDUNDANT_SUBGOAL |
                       WRONG_DEPENDENCY | UNMEASURABLE_CRITERION |
                       INFEASIBLE_TARGET | STALE_ASSUMPTION |
                       SCOPE_DRIFT | INCORRECT_HANDOFF |
                       EXECUTION_FAILURE_UNRELATED_TO_DECOMPOSITION]
  REVIEWER:           REVIEW_TIMESTAMP:
```

Attribution must be explicit and reviewable. Correlation between a deep tree and a failed run does not establish that the tree caused the failure.

**Retention and audit practice**: Maintain histories and audit logs, document system processes and outcomes, record external inputs and configurations, define acceptable performance limits, compare pre-deployment behaviour against production behaviour, and assess variance using confidence intervals, bootstrapping, and stress tests. These practices support operational debugging and defensible evaluation alike [29].

**Metric families and calculation**: No single metric establishes decomposition quality. AI agents must report a scorecard segmented by objective class, risk tier, model and prompt version, domain, and tree depth, and must pair averages with distributions and worst-tail behaviour.

- **Admission rate**: Admitted objectives divided by objectives presented to the routing gate. Target: report as a descriptor, with a deviation of more than 20 percentage points from the historical baseline triggering gate review.
- **Valid-decomposition rate**: Runs exiting with an approved tree divided by admitted runs. Target: at least 0.80 for full runs, with lower values triggering a review of the goal contract stage. Clarification-required, infeasible, template-routed, direct-execution, budget-exhausted, and safe-refusal exits are counted separately and never merged into failures, since merging punishes correct routing.
- **Measurability rate**: Required goal nodes with complete, verifiable outcome criteria and named evidence divided by all required nodes. Target: 1.00. The same rate is reported for guardrails. A manual audit of at least 10 percent of nodes is required, because a syntactically present metric can still be meaningless or gameable.
- **Criterion coverage**: The weighted share of root acceptance criteria and guardrails traced to at least one valid leaf or retained parent check. Target: 1.00 at freeze. Weights are applied only where stakeholders have approved them.
- **Counterexample escape rate**: The share of review scenarios in which all children could pass while the parent still fails. Target: at most 0.05; above this the sibling validation step is rerun with additional counterexamples.
- **Missing-subgoal incidence**: Downstream failures attributed to omitted goals divided by executed runs. Target: at most 0.10; above this the coverage loop's termination rule is tightened.
- **Redundancy rate**: Duplicated required outcomes identified by reviewers or semantic comparison divided by required nodes. Target: at most 0.10.
- **Useful-leaf ratio**: Leaves executed or explicitly retained as necessary controls divided by all generated leaves. Target: at least 0.75; below this the decomposition is over-generating.
- **Structural descriptors**: Node count, leaf count, maximum and mean depth, branching-factor distribution, and edge count are tracked as descriptors, never as quality targets. A growing tree with unchanged criterion coverage is a warning of over-decomposition and triggers lens review.
- **First-pass validation rate**: Candidate trees passing all required checks without refinement divided by first candidates. Target: at least 0.50.
- **Subgoal validation pass rate**: Passing node validations divided by node validations attempted. Target: at least 0.85.
- **Constraint-violation detection rate**: Violations caught during decomposition divided by all violations found during decomposition or later review. Target: at least 0.90; below this the feasibility stage is strengthened.
- **Human-review disagreement rate**: The frequency with which reviewers reject or materially change automated judgments. Target: at most 0.20; above this the automated validators are recalibrated rather than the reviewers overruled.
- **Re-decomposition frequency**: Refinement events per admitted run, reported alongside the percentage of nodes refined and depth added per event.
- **Refinement yield**: Events resolving the cited defect without introducing a new material defect divided by refinement events. Target: at least 0.60; below 0.40 across 3 rounds triggers the thrashing protocol in Section III.C.
- **Clarification rate and yield**: Runs asking at least one material question divided by admitted runs, and clarifications changing the goal contract, tree, or feasibility decision divided by clarifications asked. Target yield: at least 0.60. High frequency with low yield signals thrashing; very low frequency combined with high downstream omission signals superficial validation.
- **Dependency precision**: Confirmed necessary edges divided by sampled proposed edges. Target: at least 0.85.
- **Dependency recall**: Known necessary edges captured before execution divided by all necessary edges found before or during execution. Target: at least 0.80.
- **Graph defect rates**: Cycle rate, orphan-node rate, late-dependency discovery rate, and time blocked by missing dependencies. Target for cycle rate at freeze: 0.00. Critical-path accuracy is reported only where durations and completion data are reliable [23].
- **Efficiency**: Decomposition latency, model calls, tokens, monetary cost, human-review time, and total events per approved tree, each normalized by required leaf, by covered root criterion, and by successful downstream run. The full method is compared against a direct or lightweight baseline so that added structure demonstrably earns its cost.
- **End-to-end goal attainment**: Runs whose root outcome and guardrail criteria are verified divided by executed runs, joined to the originating tree version. Leaf success rate, schedule variance, replan frequency, human-intervention rate, and total cost are reported alongside it.
- **Decomposition-attributable success**: Estimated through controlled comparisons, paired replay, ablations, or reviewed failure attribution. Attribution by assumption is prohibited.
- **Calibration**: For each confidence dimension, predicted probabilities are compared with observed validation or execution outcomes using calibration plots, Brier score, or expected calibration error. Overconfidence on failed high-risk nodes is reported separately. A model producing stable high confidence while missing dependencies is not robust regardless of its aggregate score.

**Robustness and variance evaluation**: AI agents must evaluate IGD as a stochastic system rather than a deterministic function.

- Build a representative corpus containing simple, complex, ambiguous, contradictory, infeasible, dynamic, adversarial, and high-risk objectives, with at least 5 cases per class.
- Define for each case the hidden or reviewer-approved acceptance criteria, the known constraints, and the expected escalation behaviour.
- Run at least 5 repeated trials with controlled seeds and identical versions, then repeat under perturbation: benign paraphrases, reordered context, distractors, missing information, conflicting evidence, tool failures, changed deadlines, constrained budgets, and alternative model or prompt versions.
- Measure outcome consistency rather than identical wording. Align nodes by semantic goal and compare root-criterion coverage, required-leaf sets, dependency edges, feasibility verdicts, escalation decisions, and downstream success.
- Report the proportion of runs passing all quality gates, mean and worst-case coverage, variance in node count and depth, semantic agreement among required leaves, dependency-edge agreement, clarification-decision consistency, feasibility-decision consistency, cost variance, and the quality gap between clean and stressed conditions. A clean-to-stressed coverage gap exceeding 0.15 blocks promotion.
- Treat exact tree identity as a possible indicator of template reuse rather than of quality; structural diversity is acceptable where alternative trees are equally sound.

**Two mandatory review modes**: A structural validator checks required fields, identifiers, graph cycles, budget limits, and traceability. An independent semantic reviewer checks intent preservation, coverage, overlap, feasibility, and evidence quality without seeing generator confidence. Critical domains add a domain expert and scenario simulation. Repeated trials and independent review reduce correlated self-approval; they do not create a formal safety guarantee, and must never be described as one.

**Promotion and version comparison**: Compare versions with paired cases and preserved evaluation sets. Promote a new prompt, model, policy, or template only where it maintains hard-constraint safety, improves targeted quality, and causes no unacceptable regression in tail latency, cost, clarification behaviour, or downstream success. Record confidence intervals and sample sizes with every comparison. Investigate any improvement that disappears under paraphrase or under a different seed before promoting.

**Learning and adaptation mechanisms**:

- **Template promotion**: Where a validated structure recurs across at least 5 runs with a valid-decomposition rate at or above 0.90, promote it deliberately into governed workflow or method-library knowledge rather than leaving it as undocumented prompt convention.
- **Defect-driven checklist growth**: Where the same defect category appears in more than 20 percent of runs, add its detection to the structural validator rather than relying on generator discipline.
- **Attribution review cadence**: Review downstream failure attributions on a fixed cadence, since attribution drift silently reassigns execution failures to decomposition and inflates apparent decomposition defect rates.
- **Budget recalibration**: Recompute default depth, breadth, and round limits when the useful-leaf ratio or the refinement yield shifts by more than 0.10 from its established baseline.

***

## IV. Domain-Agnostic Application Guidance

The framework is designed for generalisability across domains. Its phases depend on the structure of the objective, not on the subject matter, and the four scenarios below demonstrate transfer across dissimilar sectors.

**Research and evidence programmes**: For an objective such as producing a credible report on whether a proposed intervention improves a review process, the ambiguity gate identifies the meaning of credibility, the review setting, the efficiency baseline, the comparison group, the evidence standard, and the deadline as unresolved. After clarification the normalized contract commits to delivering, by a named date, an evidence-backed comparison of the current and proposed approaches across time, cost, consistency, and decision quality, with stated limitations and reproducible sources. An outcome-first decomposition yields required children for evaluation definition, evidence corpus, comparative analysis, risk and limitation analysis, and reproducible report, each with a measurable artifact and an acceptance test. Dependency mapping shows that comparative analysis depends on both agreed metric definitions and extracted evidence, that drafting can proceed section by section, and that final conclusions depend on contradiction resolution. Where evidence cannot support causal claims, the agent does not manufacture them: it changes the conclusion target to a bounded assessment of available evidence and records the limitation. Final tasks enter orchestration with citations and data artifacts linked to the leaf goals requiring them.

**Product and service launches**: For an objective such as launching a new capability within a quarter, the goal contract adds the customer segment, the jurisdictions, the success metrics, the compliance and security guardrails, the rollout deadline, and the rollback authority. Candidate hierarchies are generated by customer outcome and by launch lifecycle, and the selected hierarchy covers product readiness, regulatory approval, operational readiness, controlled rollout, adoption, and post-launch verification. Dependency mapping reveals that production rollout depends on compliance approval, tested rollback, support readiness, and monitoring. Adoption remains an outcome rather than an activity, with implementation tasks generated only at handoff. A stress scenario in which a critical external provider is unavailable triggers the fallback criterion before launch rather than during it. Where the deadline conflicts with a mandatory review, the agent declares temporal infeasibility and asks the sponsor to change scope or date; it does not weaken the approval requirement.

**System and model quality improvement**: For an objective as underspecified as improving an assistant, the phrase is not safely decomposable until the stakeholder selects target users, behaviours, baselines, and acceptable trade-offs. The normalized contract becomes an increase in factual-answer accuracy on an approved benchmark from a stated baseline to a stated target while holding severe safety violations below a threshold and keeping median cost and latency within budget. Candidate children address measurement validity, data quality, retrieval, model or prompt behaviour, safety controls, and independent evaluation. A weak first decomposition containing an architecture-optimization child fails the measurability and necessary-contribution tests; validation rewrites it as a hypothesis-driven branch whose success is an accepted improvement on a held-out set, and marks the branch optional until evidence supports it. Repeated decompositions are then compared for stable coverage of factuality, safety, latency, cost, and generalization, and a new tree or intervention is promoted only where paired evaluation shows improvement without guardrail regression.

**Individual and team capability development**: For an objective such as becoming proficient in a technical discipline, a performance target is premature where the learner has no measured baseline. The first subgoal is therefore diagnostic: demonstrate current capability on a representative task. Later children define foundational knowledge, implementation practice, evaluation skill, and a portfolio artifact, each specified as an observable demonstration rather than as course attendance. Review checkpoints permit the hierarchy to adapt to evidence about what the learner already knows. This scenario illustrates the general rule that learning goals and performance goals must not be conflated on complex, novel work, because a performance target imposed before a baseline exists converts an unknown into a false commitment [10].

**Scale adaptation**:

- **Lightweight scope**: Retain Phase 1, the routing gate, one candidate, local and sibling validation, and dependency mapping. Collapse Phase 6 to a single-scenario check and cap depth at 3 levels. Retain all record types at reduced field density, since provenance is what makes a lightweight run auditable later.
- **Full scope**: Apply all seven phases as specified, generate 2 to 3 candidates, run all 6 challenge scenarios, and require independent semantic review with generator artifacts withheld.
- **Programme scope**: Where an objective spans multiple independent sponsors or budget owners, decompose one level into sponsor-aligned subgoals, freeze that level, and run a separate full decomposition per subgoal with its own run identifier and a lineage link to the parent run. A single run must not span authority boundaries, because the authority model in the goal contract cannot then be stated coherently.

***

## V. Limitations and Considerations

**Structural validity does not establish semantic correctness**: A hierarchy can satisfy every automated check in Section III.B and still misrepresent the objective. The validators detect malformation, not misunderstanding. Mitigation requires independent semantic review conducted without generator artifacts, plus adversarial scenario testing proportional to the risk tier, and neither substitutes for the accountable sponsor's judgment.

**Coverage is judged, not proved**: Collective exhaustiveness is asserted relative to declared scope, assumptions, and risk tolerance. No procedure in this guide proves that a sibling set is exhaustive over reality. Mitigation is the counterexample discipline in Step 4.3, the minimum of three counterexamples per branching parent, and explicit recording of the scope relative to which exhaustiveness is claimed.

**Generated hierarchies inherit generator weaknesses**: Systematic evaluation of language models on planning tasks finds material shortfalls in plan generation [11], and a fluent hierarchy is not evidence of a sound one. Mitigation is multi-candidate generation, deterministic structural validation, external evidence for feasibility claims, and the prohibition on self-certification in Section III.C.

**Confidence is diagnostic, not evidential**: Disaggregated confidence vectors improve visibility into which dimension is weak, but self-reported probabilities remain features to be evaluated. Mitigation is calibration measurement against observed outcomes, separate reporting of overconfidence on failed high-risk nodes, and the prohibition on averaging a near-zero safety confidence into an aggregate.

**Decomposition overhead can exceed its benefit**: Every phase consumes tokens, latency, and human attention. On simple objectives the control layer costs more than it saves. Mitigation is the cheap routing gate in Step 2.1, its 5 percent budget cap, and the useful-leaf ratio metric that detects over-generation after the fact.

**Provenance creates exposure**: Comprehensive logging of objectives, evidence, and stakeholder clarifications can capture secrets, personal data, and privileged material. Mitigation is storage by protected reference or salted hash, declared privacy classification on every run, retention limits, and minimization of sensitive fields while retaining the provenance needed for accountability.

**Attribution is contestable**: Joining downstream outcomes to a tree version enables analysis but invites false causal inference. A deep tree correlated with a failed run does not establish causation. Mitigation is reviewed cause attribution against a fixed nine-value list, controlled comparison or paired replay for effect estimates, and a periodic attribution review to detect drift.

**Human authority cannot be automated away**: Choices expressing stakeholder values, legal authority, safety tolerance, budget ownership, or irreversibility remain outside the agent's remit. Mitigation is the declared authority boundary in the goal contract, the mandatory approval gate before handoff, and the safe-refusal exit category. An agent that invents a stakeholder preference has failed regardless of the quality of the resulting hierarchy.

**Robustness evaluation is bounded by the corpus**: Repeated trials and perturbation testing measure stability over the cases the corpus contains. They do not generalize to case classes absent from it, and they do not constitute a formal safety guarantee. Mitigation is explicit corpus composition reporting, a minimum of 5 cases per objective class, and a stated clean-to-stressed quality gap alongside every promotion decision.

***

## VI. Conclusion and Summary

Intelligent Goal Decomposition creates value by reducing ambiguity before execution rather than after it. The governing principle is short: clarify what success means, propose alternative outcome structures where the structure is genuinely uncertain, validate every node and the whole set, expose dependencies and constraints as typed relationships, refine only until leaves are operational, then hand off while preserving lineage, and reopen the smallest affected subtree when reality contradicts the hierarchy.

The framework's discipline lies in what it refuses to do. It refuses to overwrite the original request with a polished restatement. It refuses to decompose an impossible contract. It refuses to treat a fluent list as a validated hierarchy. It refuses to let a generator certify its own feasibility and safety verdicts. It refuses to relax a deadline, target, budget, permission, or guardrail without an authorized decision. It refuses to rewrite history when replanning. Each refusal converts an invisible failure into a visible one, which is the whole of the method's contribution.

**Production readiness standard**: An IGD capability is ready for controlled production only when it has a documented admission gate; a versioned goal and edge schema; explicit outcome and guardrail criteria; bounded generation, critique, and refinement loops; deterministic structural validation; independent semantic review proportional to risk; distinct clarification, infeasibility, and safe-refusal paths; a lossless handoff to planning and orchestration; append-only provenance; downstream outcome linkage; repeated-run and perturbation evaluation; privacy and retention controls; and named human authority for consequential decisions. A capability missing any one of these fourteen elements operates in evaluation, not in production.

**Key Success Factors**:

- **Preserved original intent**: The verbatim request is immutable, every interpretation is versioned, and scope drift stays visible and auditable.
- **Outcomes and evidence before tasks**: What must become true is settled, with named evidence, before how to act is decided; task generation occurs only at the handoff boundary [24].
- **Paired criteria**: Every branch carries both outcome criteria and guardrail criteria, because optimization without protected constraints invites goal displacement.
- **Two-level validation**: Children are validated individually and as a set, since local quality never establishes parent coverage, and counterexamples are the instrument that finds the gap.
- **Typed dependencies**: Hierarchy explains contribution and dependency edges explain execution eligibility; no approval, data contract, or precedence relation survives only in prose.
- **Asymmetric bounded refinement**: The riskiest and least operational branches are decomposed deeply, clear branches stay shallow, and every loop carries depth, breadth, iteration, time, token, and no-progress limits with a named escalation path.
- **Independent verification**: Feasibility and safety verdicts come from external evidence, deterministic checks, independent review, simulation, or formal methods proportional to risk, never from generator self-assessment.
- **Lineage to outcome**: Every executed task links to its source leaf and tree version, so that decomposition quality can be separated from execution quality when results arrive.

By following this framework, AI agents can convert ambiguous, long-horizon objectives into validated goal hierarchies that downstream planners and orchestrators can execute, that reviewers can audit, and that reopen cleanly when evidence overturns an assumption.

***

## VII. References and Further Reading

This guide is derived from a single originating prose document and from companion operational guides in this documentation corpus. The external references listed below are transcribed from the originating prose guide as that guide cited them; they were carried across during conversion and have not been independently re-verified against their sources. Entries 1 through 9 are pointers within this documentation corpus, and entries 10 through 29 are the external references.

**Originating document**:

1. `Intelligent Goal Decomposition: A Practical Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the soundness properties in Section 1.3, the sixteen-step workflow restructured as the seven phases of Section II, the difficult-case handling restructured as the error taxonomy in Section III.C, the run, goal-node, edge and graph, event, and downstream-linkage record types in Section III.D, the metric definitions and robustness protocol in Section III.D, the practical scenarios in Section IV, and the production readiness standard in Section VI.

**Companion guides, for adjacent and downstream methods**:

2. `advanced_task_guides/planning/guide_HierarchicalTaskNetworkPlanning.md` — the method-library planning pattern distinguished from IGD in Section 1.2; the correct destination for branches where approved reusable procedures already define refinement.
3. `advanced_task_guides/planning/guide_TaskManagementOrchestration.md` — the runtime lifecycle pattern that receives the handoff package produced in Step 7.1 and becomes the source of truth for admitted work.
4. `advanced_task_guides/planning/guide_MetaReasoning.md` — the control layer that decides whether decomposition is warranted, how much depth is justified, and when a stalled decomposition should change method.
5. `advanced_task_guides/planning/guide_WorldModelSimulationPlanning.md` — the simulation method invoked in Step 6.1 for consequential or dynamic systems.
6. `advanced_task_guides/planning/guide_PlanTodoRecitation.md` — the context-salience pattern distinguished in Section 1.2 from an authoritative goal registry.
7. `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance for the provenance and observability requirements specified in Section III.D.
8. `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guidance for the monitoring and invalidation triggers attached to assumptions in Step 1.2 and Step 7.3.
9. `advanced_task_guides/authoring/guide_guidewriting.md` — the house-style specification governing the structure, register, and conformance envelope of this document.

**External references, transcribed from the originating prose guide and grouped by the source section in which each is cited**:

*Purpose and core idea*:

10. Locke and Latham — https://www-2.rotman.utoronto.ca/facbios/file/09%20-%20Locke%20&%20Latham%202002%20AP.pdf
11. PlanBench — https://arxiv.org/abs/2206.10498
12. Encyclopaedia Britannica — https://www.britannica.com/science/means-ends-analysis
13. Sutton, Precup, and Singh — https://people.cs.umass.edu/~barto/courses/cs687/Sutton-Precup-Singh-AIJ99.pdf

*What IGD is—and is not*:

14. Georgievski and Aiello — https://arxiv.org/abs/1403.7426
15. Shivashankar and colleagues — https://www.cs.umd.edu/~nau/papers/shivashankar2011hierarchical.pdf
16. Alford and colleagues — https://www.ijcai.org/Proceedings/16/Papers/429.pdf

*Properties of a sound decomposition*:

17. Doran, “There’s a S.M.A.R.T. Way to Write Management’s Goals and Objectives” — https://consultwithcatalyst.com/wp-content/uploads/2018/01/SMART-Goals.pdf
18. Google re:Work — https://rework.withgoogle.com/intl/en/guides/set-goals-with-okrs
19. U.S. Department of Energy Work Breakdown Structure Handbook — https://www.energy.gov/projectmanagement/articles/department-energy-work-breakdown-structure-handbook

*Operational workflow*:

20. Least-to-Most Prompting — https://arxiv.org/abs/2205.10625
21. Decomposed Prompting — https://arxiv.org/abs/2210.02406
22. Yao and colleagues — https://arxiv.org/abs/2305.10601
23. Critical Path Method overview — https://en.wikipedia.org/wiki/Critical_path_method
24. Wang and colleagues — https://arxiv.org/abs/2305.04091
25. Prefect documentation — https://docs.prefect.io/
26. LangChain and LangGraph overview — https://python.langchain.com/

*Logging and metadata strategy*:

27. W3C PROV Overview — https://www.w3.org/TR/prov-overview/
28. OpenTelemetry tracing concepts — https://opentelemetry.io/docs/concepts/signals/traces/
29. NIST AI RMF Measure playbook — https://airc.nist.gov/AI_RMF_Knowledge_Base/Playbook/Measure

