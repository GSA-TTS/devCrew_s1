# Scenario-Based Planning

**Status**: Beta testing

**Change logs**:

- [09/06/2026] - Initialization

***

## Executive Summary

Scenario-Based Planning is the task family of preparing a decision maker for several materially different futures instead of optimising a single plan against one forecast. It identifies the uncertainties that could change a decision, constructs a bounded set of plausible and internally consistent future states, tests candidate strategies against every state under common criteria, and assembles a plan from actions that are acceptable now plus options that activate when observable conditions change. This guide converts that method into an agent-executable procedure: a six-phase Operational Framework spanning seventeen steps, from opening a scenario run with a decision contract through closing the run and updating the strategy library.

The output of the method is not a most-likely future. It is a decision architecture containing a common core of no-regret actions, explicit hedges, preserved options, scenario-specific branches, signposts, trigger thresholds, and a replanning rule. This guide specifies the uncertainty-regime rule that governs which scenario method may be used, the scenario architecture and budget declaration that prevents scenario explosion, the strategy-by-scenario stress-testing matrix, the robustness and regret measures that replace probability-weighted scoring under deep uncertainty, the trigger and playbook design that makes contingencies executable, the six persistent record types that make a run reproducible, and the seven metric families that reveal whether the method is improving decisions. It emphasises structured execution protocols, quality assurance checkpoints, and error handling procedures so that AI agents can run the method autonomously while escalating the decisions that may not be automated.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Scenario-Based Planning (SBP)**: A planning method that constructs multiple internally consistent future states, evaluates candidate strategies in each, and produces a conditional portfolio rather than a single optimised plan. Abbreviated SBP throughout this guide.

**Scenario**: A decision-relevant account of how a future state could arise, specifying the assumptions it contains, the causal sequence that produces it, how actors respond, and what the state means for the focal decision [14]. A scenario is not a prediction and is never scored by whether it came true [13].

**Focal decision**: The specific choice the run exists to inform, stated so that alternatives are possible [16][17]. A focal decision names the decider, the object of the decision, the deadline, the horizon, and the authority under which it is made.

**Decision contract**: The record fixing the focal decision, objective hierarchy, hard constraints, minimum acceptable outcomes, risk tolerance, stakeholders, budget, evidence standard, irreversible actions, and exit conditions before any analysis begins [18].

**Driving uncertainty**: A factor whose different states imply different actions on the focal decision. Driving uncertainties are the material from which scenario axes are built.

**Predetermined element**: A trend or condition supported by evidence strong enough that it appears in every scenario unless a specific mechanism supports a break.

**Deep uncertainty**: The condition in which parties do not know, or do not agree on, the models, probabilities, or values governing a decision. Deep uncertainty forbids probability-weighted scoring as the primary decision rule.

**Scenario axis**: A high-impact uncertainty whose distinct states are used to separate one scenario from another.

**Strategy portfolio**: A combination of core actions, hedges, options, big bets, contingent actions, and exit or safe-state actions, selected together rather than as competing single plans.

**No-regret action**: An action producing acceptable value across nearly all relevant scenarios, such as improving observability, removing a single point of failure, or repairing a known control weakness.

**Hedge**: An action reducing downside if an adverse future occurs, carried at a known ongoing cost.

**Option**: An action preserving the right but not the obligation to act later, such as a pilot, a reserve contract, a modular interface, a trained backup team, or a pre-negotiated licence. Options carry costs, prerequisites, and expiry dates.

**Big bet**: An action producing high value in a narrow set of futures while creating exposure elsewhere. Big bets require explicit, recorded risk acceptance.

**Contingent action**: An action bound to a named trigger, owner, lead time, and branch playbook, held dormant until the trigger fires.

**Safe-state action**: An action limiting loss when no primary strategy remains acceptable, including exit, suspension, and degraded-mode operation.

**Robustness**: The property of remaining acceptable across a broad and relevant set of futures, failing gracefully, and adapting before losses become irreversible. Robustness is not optimality in any single future.

**Regret**: The shortfall of a strategy in a given scenario relative to the best available strategy in that same scenario. Reported as maximum regret and as percentile regret across the retained set.

**Vulnerability region**: A compact combination of uncertain conditions under which a strategy fails an acceptance threshold. Identified by scenario discovery or interpretable clustering over an evaluation ensemble [36].

**Signpost**: An observable indicator tied to an uncertainty or a causal transition, carrying a data source, a measurement method, and a check frequency.

**Trigger**: A rule that changes action when one or more signposts cross a threshold, carrying persistence requirements, a decision authority, a lead time, an activation window, and a fallback when data are unavailable.

**Branch**: A prepared, contingent course of action within the current plan, activated by a trigger.

**Sequel**: A prepared course of action following a different outcome of the current plan rather than a contingency inside it [35].

**Playbook**: The rehearsed procedure that executes a branch, specifying prerequisites, tasks, resources, communications, safety checks, handoffs, and success and abort conditions [37].

**Scenario envelope**: The union of conditions covered by the retained scenario set. Observations falling outside it return control to uncertainty framing rather than being forced into the nearest existing scenario.

**Replanning rule**: The stated condition under which the run returns to an earlier phase, distinguishing strategy repair from scenario-space rebuild from decision-contract revision.

**Scenario discovery**: The practice of searching an evaluation database for concise, interpretable combinations of conditions associated with strategy failure, in place of declaring one forecast correct.

### 1.2 What Scenario-Based Planning Is and Is Not

SBP combines four distinct activities that AI agents must not collapse into a single narrative exercise.

**Scenario construction** represents alternative external conditions and actor responses. Scenarios must differ on uncertainties capable of changing the decision, not on decorative detail.

**Strategy stress testing** applies identical acceptance criteria to every candidate strategy in every scenario, producing comparable evidence about strengths, weaknesses, binding constraints, and failure modes.

**Robust and adaptive choice** selects a portfolio of no-regret actions, hedges, options, and contingent moves rather than a brittle plan optimised for one future, and identifies the conditions under which each strategy fails [19].

**Monitoring and replanning** watches signposts, updates the scenario set and the evidence behind it, activates pre-authorised branches, and constructs a new plan when reality leaves the modelled envelope.

The method is defined as much by its exclusions as by its content.

**SBP is not forecasting**: A forecast estimates what is likely to happen, usually as a central estimate with an uncertainty interval. SBP asks what could happen that matters to the decision and what must be done if it does [15]. Forecasts inform scenarios, but a scenario set organised only around small variations in one forecast will miss structural change and adversarial response.

**SBP is not sensitivity analysis**: Sensitivity analysis varies inputs to observe output movement. A scenario additionally specifies a coherent joint state, a causal path, actor behaviour, and operational consequences. Sensitivity analysis is a component inside SBP for identifying influential assumptions; isolated high, medium, and low input values are not automatically coherent futures.

**SBP is not contingency planning alone**: Contingency planning converts selected disruptions into response procedures, recovery requirements, authorities, and resources. SBP discovers which disruptions and transitions deserve preparation; contingency planning makes the selected branches operational. Consequences and recovery needs must be established before response procedures are written [20].

**SBP is not simulation**: Simulation is an engine for generating or evaluating trajectories under a model. SBP supplies the decision frame, the uncertainty space, the strategies, the criteria, and the interpretation. Spreadsheet models, Monte Carlo ensembles, wargames, digital twins, learned world models, and multi-agent simulations support SBP, but no model validates assumptions it omits.

**Relation to neighbouring planning patterns**: SBP occupies one position in a family of planning and execution patterns, each of which answers a different control question. The neighbouring patterns that bound it are enumerated below, and AI agents must place SBP correctly rather than substituting a neighbour for it.

- **Meta-reasoning** decides whether scenario work is worth its cost, which scenario method to invoke, how broad the search should be, whether evidence is improving the decision, and when to stop. SBP is the selected object-level method; a meta-reasoner may switch from a qualitative set to a quantitative ensemble, commission a red team, or halt generation when marginal coverage falls below threshold.
- **Hierarchical task network planning** selects an authorised decomposition from a compound task down to executable primitives. SBP supplies environmental branches and contingent goals; hierarchical decomposition supplies the method for executing a chosen response. The same decomposition may be tested in several scenarios, and different decompositions may be attached to specific triggers.
- **Task management and orchestration** owns runtime task state, assignment, dispatch, retries, dependencies, timeouts, compensation, and escalation. SBP creates the portfolio and the trigger logic; orchestration executes the active branch and records actual outcomes. A scenario document is not a work queue, and a simulated completion is not an executed task.
- **Goal decomposition** determines which outcomes and measurable subgoals should exist. SBP then asks whether that goal system remains appropriate or attainable under different futures. Goal decomposition precedes scenario evaluation so that all futures are judged against the same authorised outcomes.
- **Constraint satisfaction planning** determines whether assignments, schedules, routes, configurations, or allocations satisfy explicit restrictions. SBP varies uncertain parameters or structural conditions across cases; a constraint solver checks feasibility inside each case. A plan feasible in the nominal scenario is not robust until it is feasible, acceptably repairable, or safely abandonable across the retained set.
- **Plan and execute decoupling** separates plan construction from action so commitments can be checked before tools change the world. SBP extends that separation from one plan to a conditional portfolio; a selected branch still requires pre-execution validation against current facts.
- **World-model simulation planning** predicts state transitions and outcomes for candidate actions. It is an evaluation mechanism inside SBP, not a replacement for scenario framing, evidence governance, or decision authority.
- **Plan and todo recitation** keeps the current objective, plan, and unfinished work salient in an agent's working context. It reminds an agent to evaluate every scenario and monitor every trigger, but recited text is never the authoritative scenario registry, evaluation store, or trigger state; those records persist outside the conversational context.

The practical composition runs in sequence: goal decomposition defines outcomes; meta-reasoning selects SBP and sets its budget; SBP produces a robust portfolio; hierarchical decomposition and constraint solving create feasible branch plans; plan and execute decoupling validates commitments; orchestration runs them; and monitoring returns changed conditions to SBP for replanning.

### 1.3 Choosing the Uncertainty Regime Before Choosing the Method

The scenario method must follow the quality of available knowledge, not the sophistication of available tooling. AI agents must classify the uncertainty regime during Phase 1 and record that classification in the run record before any generation method is invoked. Selecting a method whose evidentiary preconditions are unmet is a run-halting defect, not a stylistic preference.

**Uncertainty regime selection rule**:

| Regime condition | Method to select | Evidentiary precondition | Failure signature if misapplied |
| :-- | :-- | :-- | :-- |
| Structural forces, actor choices, institutional change, or discontinuity dominate; reliable probabilities unavailable | Qualitative exploratory scenarios, 3 to 4 strongly contrasting narratives | Evidence grounding and internal consistency in every scenario | Decorative variants that change prose without changing decisions |
| The question is how to reach or avoid a defined end state such as a safety target, regulatory deadline, or unacceptable loss | Normative or backcast scenarios | A defined and authorised end condition | A desired endpoint presented as a prediction |
| Branches, choices, outcomes, and conditional probabilities are few enough to enumerate, and information or action order matters | Decision trees | Defensible probabilities and utilities on every branch | Invented probabilities filling blank cells; incomplete branch sets |
| Uncertainty is primarily quantitative and a defensible computational model exists | Monte Carlo simulation | Justified input distributions and dependency structure | Thousands of runs of a wrong model presented as precision |
| Parties do not know or do not agree on models, probabilities, or values | Robust Decision Making with scenario discovery | A broad sampled uncertainty space and a declared outcome threshold | Probability weighting that conceals catastrophic tails |
| Adaptive opponents, partners, regulators, customers, or internal stakeholders can observe and react to the plan | Wargaming and red teaming | Declared roles, a move sequence, and a documented adjudication method | Static scenarios in which no actor responds to the plan |
| Actions alter a stateful environment and real trials would be slow, unsafe, or expensive | World-model or multi-agent simulation | Out-of-model tests, holdout cases, and real-world validation | Policies that score well by exploiting simulator error |
| The decision is consequential and no single regime dominates | Hybrid combining a small qualitative set, a quantitative ensemble, red teaming, and contingency planning | Each component addresses a named uncertainty or failure mode | The same assumptions repeated in several formats |

**Qualitative exploratory scenarios** apply where structural forces dominate and probabilities are unavailable. Three or four strongly contrasting, evidence-grounded, internally consistent narratives are sufficient for strategic use. Exploratory scenarios develop plausible outcomes forward from assumptions and are distinguished from normative scenarios, which assume a desired outcome and reason backward to possible pathways [21].

**Normative or backcast scenarios** start from the end condition, reason backward to necessary milestones and dependencies, then test whether the pathway remains feasible under alternative external conditions. AI agents must never present a normative endpoint as a probability-bearing prediction.

**Decision trees** expose decision points and support expected-value calculation where probabilities and utilities are defensible [22]. They become misleading when the branch set is incomplete, when outcomes are interdependent, or when precise probabilities are invented to fill blank cells.

**Monte Carlo simulation** requires specifying uncertain variables, their probability distributions, and an iteration count; sampling inputs repeatedly; running the model; and examining the distribution of outcomes [23]. Sample count repairs sampling error only. It does not repair a wrong model, an omitted dependency, or an unjustified distribution.

**Robust Decision Making with scenario discovery** applies under deep uncertainty. Rather than assigning false precision, the method samples a broad uncertainty space, evaluates strategies across it, and searches the resulting database for concise combinations of conditions associated with failure [24]. Interpretable vulnerability regions replace a single correct forecast as the analytical product.

**Wargaming and red teaming** add human or agent decisions, action, reaction, and counteraction, and a documented adjudication method. Wargaming applies across strategic, operational, and tactical levels, including planning and executive decision-making [25]. Red teams must challenge explicit and implicit assumptions and examine the problem from adversary, partner, and third-party perspectives rather than criticise wording [26].

**World-model or multi-agent simulation** provides a learned or constructed environment in which policies are evaluated before transfer to the real task [27]. Planning may use a model that predicts reward, value, and action-selection information without reconstructing every environmental detail [28]. Policies can exploit model error, so consequential conclusions require out-of-model tests, holdout cases, and real-world validation.

**Hybrid regimes** govern most consequential applications: a small qualitative set communicates structural futures, a quantitative ensemble tests ranges, red teams expose adaptive behaviour, and contingency planning makes selected branches executable. Each component must address a named uncertainty or failure mode; components repeating the same assumptions in a different format are removed from the budget.

### 1.4 Applicability Conditions and Exclusions

**Conditions favouring SBP**: SBP applies when several plausible external futures would require materially different choices, when the uncertainty cannot be resolved before a commitment is due, and when the cost of being wrong is significant. Strong fits include long-horizon strategy, technology and regulatory transitions, infrastructure and capacity investment, supply-chain design, security and continuity planning, safety planning, product or market entry, capability planning, environmental adaptation, and multi-agent systems whose participants may adapt or fail.

SBP additionally applies where decisions are partly irreversible but can be staged; where a modest investment preserves a valuable option; where actors may react strategically to the plan; where a single failure mode would defeat an otherwise attractive plan; where stakeholders disagree about assumptions; or where an organisation requires observable triggers rather than periodic improvisation. The characteristic product in these cases combines near-term no-regret actions with pathways, deferred actions, and signposts determining when additional measures are taken [29].

**Conditions favouring SBP in agent systems**: SBP applies to agent workloads where tool results, users, other agents, policies, or environments may change state faster than a fixed long plan can tolerate. It is most valuable before high-impact actions, across long-running workflows, and wherever a model can cheaply test multiple futures before acting. Branching search over reasoning paths is a related mechanism, but its task-level branches are typically shorter and narrower than strategic scenarios and do not substitute for scenario framing [30].

**Exclusion 1, trivial or determinate tasks**: Full SBP must not be invoked for a simple lookup, a deterministic transformation, a low-impact routine, or a near-certain short-horizon task with one established response. A checklist, a forecast, a standard operating procedure, or a bounded sensitivity analysis is cheaper and clearer. Where estimated SBP cost exceeds 10% of the value at stake, the run is not opened and the cheaper instrument is used instead.

**Exclusion 2, decisions that cannot change**: Where there are no alternative actions, no capacity to hedge, no way to observe triggers, and no authority to replan, scenario generation produces awareness without control. AI agents must escalate the structural limitation rather than generate scenarios.

**Exclusion 3, resolvable ignorance**: Narratives must not substitute for readily available evidence. Where a critical fact can be measured, tested, or retrieved before the decision deadline at a cost below the scenario budget, that retrieval is performed first. Scenarios represent residual uncertainty, not ignorance that inexpensive research removes.

**Exclusion 4, tool-mandated probability**: Probabilities must not be assigned merely because a tool requires them. Under deep uncertainty, probability-weighted expected value conceals catastrophic or unacceptable outcomes and makes invented precision appear rigorous. Ranges, robustness measures, regret measures, thresholds, and explicitly recorded disagreement replace it.

**Exclusion 5, generated content treated as evidence**: Language-model-generated scenarios must never be treated as evidence about prevalence, probability, or human behaviour. Generative multi-agent simulations support interactive exploration, memory, planning, and grounded action, but their outputs remain consequences of prompts, models, memories, and adjudication rules [31][32]. They expose hypotheses and interactions; consequential claims are validated independently.

***

## II. Operational Framework: Constructing a Robust and Adaptive Decision Portfolio

The framework decomposes the method into six sequential phases spanning seventeen steps. Phases 1 through 5 execute once per run under normal conditions; Phase 6 executes continuously until a closure condition is satisfied. Three explicit loops return control to earlier phases: the curation loop from Step 2.3 to Step 1.3 or Step 2.2, the vulnerability loop from Step 4.3 to Step 3.1 or Step 3.2, and the runtime loop from Step 6.2 to Step 1.1, Step 1.3, Step 4.1, or Step 4.3 depending on what changed.

### Phase 1: Decision Framing and Uncertainty Registration

**Objective**: Fix the focal decision, its acceptance thresholds, its controllable levers, and the uncertainty space that could change it, so that all subsequent scenario work is bound to a choice rather than to speculation.

#### Step 1.1: Open the Scenario Run With a Decision Contract

**Required Actions**:

- State the focal decision in a form permitting alternatives, naming who must decide what, by when, over what horizon, and under what authority.
- Record the objective hierarchy, hard constraints, minimum acceptable outcomes, risk tolerances, stakeholders, budget, evidence standard, and the actions classified as irreversible or safety critical.
- Separate the decision deadline from the scenario horizon and record both as distinct dates.
- Classify the uncertainty regime against the selection rule in Section 1.3 and record the classification with its evidentiary justification.
- Define exit conditions before analysis begins, enumerating at minimum: a robust portfolio, a request for additional evidence, escalation to a higher authority, safe deferral, and a finding that no acceptable strategy exists.
- Assign a unique run identifier and link it to any parent run.

**Required Outputs**:

- A decision contract carrying the focal decision, objective hierarchy, hard constraints, and acceptance thresholds.
- A recorded uncertainty regime classification with its justification.
- A dated pair of decision deadline and scenario horizon.
- An enumerated exit-condition set with no fewer than 5 named terminal states.
- A run identifier with parent linkage.

**Quality Checkpoints**:

- The focal decision admits at least 2 materially different alternatives; a decision with 1 alternative terminates the run and escalates under Exclusion 2.
- Hard constraints are recorded separately from preferences, with 100% of safety, legal, and mission constraints marked as infeasibility conditions rather than score penalties.
- Every acceptance threshold carries a numeric value or an explicit categorical test; a threshold stated as producing interesting or useful futures is rejected and the step repeats.
- The decision deadline and the scenario horizon are distinct fields; equality between them is flagged for confirmation before Phase 2 begins.
- The declared uncertainty regime matches at least 1 row of the Section 1.3 selection rule; an unmatched classification halts the run.

***

#### Step 1.2: Establish the Baseline and Enumerate Decision Levers

**Required Actions**:

- Describe the current state, existing commitments, capabilities, dependencies, resource reserves, and approved plans.
- Record any reference forecast in use, labelling its assumptions, its date, and its owner.
- Classify every material variable as controlled, influenced, observed, or outside influence.
- Enumerate candidate levers before any narrative is written, covering at minimum: committing now, staging investment, diversifying suppliers or providers, reserving capacity, changing architecture, purchasing insurance or transfer, piloting, collecting information, delaying, exiting, and pre-authorising a response.
- Record for each lever its cost, lead time, reversibility, and prerequisite.

**Required Outputs**:

- A baseline state description with commitments, capabilities, dependencies, and reserves.
- A dated reference forecast record with labelled assumptions, or an explicit statement that none exists.
- A variable classification table across the controlled, influenced, observed, and external categories.
- A candidate lever inventory of no fewer than 6 entries, each carrying cost, lead time, reversibility, and prerequisite.

**Quality Checkpoints**:

- Every lever in the inventory carries all 4 attributes; entries missing any attribute are removed before Phase 2 or completed within 1 revision pass.
- At least 1 lever is reversible and at least 1 is irreversible; an inventory containing only irreversible levers triggers a staging review before Phase 3.
- The reference forecast, where present, is dated and assumption-labelled; an undated forecast is excluded from the evidence base.
- No variable appears in more than 1 classification category.

***

#### Step 1.3: Build the Uncertainty and Assumption Register

**Required Actions**:

- Gather political, economic, social, technological, environmental, legal, operational, safety, and adversarial drivers capable of changing the decision.
- Record for each driver the present evidence, plausible range or discrete states, direction, time horizon, dependencies, observability, controllability, and owner.
- Classify each factor as relatively predetermined, uncertain but measurable, deeply uncertain, controllable, or endogenous to actor response.
- Rank every factor by decision impact and by uncertainty, and mark the high-impact uncertainties whose different states imply different actions as candidate scenario axes.
- Preserve recorded disagreements between stakeholders rather than averaging them into a consensus value.
- Run an assumption check asking what must remain true for the baseline plan to work, which assumptions are load-bearing, what evidence would falsify each, who benefits from believing each, and which correlated assumptions have been treated as independent.
- Submit the register to a red-team reviewer before scenario generation begins.

**Required Outputs**:

- An uncertainty register with 9 driver categories surveyed and each entry carrying 8 recorded attributes.
- A factor classification across the 5 named categories.
- An impact-by-uncertainty ranking with candidate scenario axes marked.
- A load-bearing assumption list with a named falsifier for each entry.
- A recorded disagreement log preserving unreconciled stakeholder positions.
- A red-team review record with findings and dispositions.

**Quality Checkpoints**:

- All 9 driver categories are surveyed; a category returning no entries carries a recorded justification, and more than 2 unjustified empty categories returns the step for completion.
- At least 3 factors are marked as candidate scenario axes; fewer than 3 indicates insufficient uncertainty to justify SBP and triggers a reconsideration against Exclusion 1.
- Every load-bearing assumption carries at least 1 named falsifier; assumptions without falsifiers are marked unfalsifiable and escalated rather than silently retained.
- Predetermined elements are recorded separately from uncertainties and are carried into every scenario unless a specific breaking mechanism is documented.
- The red team completed its review before Step 2.2 begins; generation started without that review is invalid and the candidate set is discarded.

***

### Phase 2: Scenario Architecture, Generation, and Curation

**Objective**: Convert the uncertainty register into a bounded, diverse, internally consistent, and decision-relevant scenario set under a declared budget and a declared stopping rule.

#### Step 2.1: Choose the Scenario Architecture and Declare the Budget

**Required Actions**:

- Select the generation method or methods from the Section 1.3 selection rule, matching each to the recorded uncertainty regime.
- Declare the number of initial scenarios or simulation samples, the branch depth, the model versions, the random seeds, the evaluation budget, the stopping rule, and the human-review points.
- Set a qualitative core set of 3 to 4 contrasting scenarios where strategic communication is required.
- Set quantitative sample counts by the stability of the decision metric rather than by the smoothness of the output distribution.
- Cap depth, breadth, token consumption, and wall-clock time for any agent-driven search before the search begins.
- Choose a diversity-preserving generation method from among: crossing two independent critical uncertainties, morphological combination, actor-by-actor move sequences, causal mapping, historical analogy, shock injection, backcasting from target states, sampled model parameters, and ensembles of independent generators.
- Record the budget declaration as an immutable field of the run record before generation starts.

**Required Outputs**:

- A declared scenario architecture naming every generation method and its assigned uncertainty or failure mode.
- A budget declaration carrying scenario or sample count, branch depth, seeds, model versions, evaluation budget, stopping rule, and human-review points.
- A generation-method selection with a stated diversity mechanism.

**Quality Checkpoints**:

- Each declared method addresses at least 1 named uncertainty or failure mode from the Step 1.3 register; a method addressing none is removed from the budget.
- Agent-driven search carries explicit caps on all 4 of depth, breadth, tokens, and wall-clock time; an uncapped search is not authorised to start.
- The qualitative core set size falls within 3 to 4 scenarios; a proposed core set above 6 is reduced before generation or is reclassified as a quantitative ensemble.
- At least 2 independent uncertainties inform the generation structure; a single two-by-two matrix that excludes a higher-impact uncertainty from the Step 1.3 ranking is rejected.
- The stopping rule is stated as a measurable marginal-yield condition, not as a scenario count alone.

***

#### Step 2.2: Generate a Broad Candidate Scenario Set

**Required Actions**:

- Create candidate futures independently before negotiating any consensus set.
- Require every candidate to specify an identifier, title, horizon, starting conditions, driving uncertainties, causal sequence, actor incentives and responses, key assumptions, quantitative ranges where defensible, operational consequences, and disconfirming evidence.
- Include favourable, adverse, mixed, and structurally different futures in the candidate pool.
- Add at least 1 scenario that challenges the organisation's preferred strategy and at least 1 that combines stresses rather than isolating failures.
- Reject any token extreme-event scenario lacking a causal path or decision relevance.
- Supply the same decision contract and evidence packet to every generation branch, varying roles or generation methods rather than varying the brief.
- Request explicit assumptions and causal links from every generator, and record generator identity, prompt version, model version, and seed with each candidate.
- Where multi-branch or debate topologies are used, treat disagreement between branches as a signal to preserve rather than a vote to resolve.

**Required Outputs**:

- A candidate scenario pool with 11 recorded fields per candidate.
- Generation provenance per candidate covering generator, prompt version, model version, and seed.
- At least 1 preferred-strategy-challenging candidate and at least 1 compound-stress candidate.
- A recorded disagreement set from independent generation branches.

**Quality Checkpoints**:

- Every candidate carries all 11 required fields; candidates missing more than 2 fields are returned for completion or discarded within 1 pass.
- The candidate pool contains at least 1 favourable, 1 adverse, 1 mixed, and 1 structurally different future; a pool missing any of these 4 classes returns to generation.
- 100% of candidates carry generation provenance; a candidate without provenance is not eligible for curation.
- No candidate is retained whose causal sequence cannot be stated in at least 3 linked steps from starting conditions to end state.
- Candidates generated from a single generator, prompt, and seed do not exceed 60% of the pool; exceeding that share triggers a correlated-generation review under Section III.C.

***

#### Step 2.3: Validate and Curate the Scenario Set

**Required Actions**:

- Evaluate every candidate for plausibility, internal consistency, relevance to the focal decision, distinctness, coverage of major uncertainties, temporal coherence, actor realism, and traceability to evidence.
- Verify that each causal path could produce the stated end state and that linked variables move consistently with one another.
- Reject any scenario violating known physical, legal, temporal, or budget constraints unless that violation is the explicit uncertainty under examination.
- Merge near-duplicates, split scenarios concealing incompatible pathways, and annotate low-evidence assumptions.
- Retain uncomfortable scenarios whose probability is unknown; unknown probability is not grounds for rejection.
- Apply the coverage test: for every high-impact uncertainty and load-bearing assumption from Step 1.3, identify at least 1 retained scenario that stresses it.
- Apply the discrimination test: where 2 scenarios produce the same preferred decision and reveal no different vulnerability, mark 1 as a redundancy candidate.
- Apply the surprise test: ask an independent reviewer which plausible causal mechanism is absent from the set.
- Return to Step 1.3 or Step 2.2 where coverage, diversity, or consistency is inadequate. This is the first explicit loop.
- Stop adding scenarios when new candidates no longer expose a new decision, vulnerability, trigger, or hedge within the authorised budget.

**Required Outputs**:

- A curated scenario set with per-scenario validation results across 8 criteria.
- A coverage matrix mapping high-impact uncertainties and load-bearing assumptions to the scenarios that stress them.
- A discrimination report naming redundancy candidates with their disposition.
- A surprise-test record naming absent mechanisms and their dispositions.
- A retirement log recording every rejected or merged candidate with its reason.

**Quality Checkpoints**:

- Coverage of high-impact uncertainties is 100%; any uncovered uncertainty returns the run to Step 2.2 for at least 1 additional generation pass.
- Coverage of load-bearing assumptions is at least 90%; below that threshold the set is not approved for Phase 3.
- No 2 retained scenarios share the same preferred decision and the same vulnerability profile; such a pair is merged or 1 member is retired.
- Every retained scenario is traceable to at least 1 evidence item from the Step 1.3 register; untraceable scenarios are marked speculative and capped at 25% of the retained set.
- Marginal yield over the last 3 candidates is greater than 0 new decisions, vulnerabilities, triggers, or hedges; a yield of 0 across 3 consecutive candidates satisfies the stopping rule and generation ends.
- Rejected candidates are retained in the retirement log rather than deleted; deletion of a rejected candidate is a logging defect.

***

### Phase 3: Implication Derivation and Strategy Portfolio Construction

**Objective**: Extract comparable consequences from every retained scenario under a uniform question set, then assemble candidate strategies as classified portfolios rather than as competing monolithic plans.

#### Step 3.1: Derive Per-Scenario Implications Without Premature Strategy Selection

**Required Actions**:

- Identify for each curated scenario the opportunities, threats, resource bottlenecks, newly binding constraints, changed stakeholders, likely second-order effects, and indicators visible before the full outcome arrives.
- Distinguish consequences of the scenario itself from consequences of the organisation's response to it.
- Apply an identical question set to every scenario, asking what fails first, what becomes easier, which capability remains scarce, which action becomes impossible if delayed, and what new information would carry the greatest value.
- Record unknowns explicitly rather than filling them with fluent speculation.
- Withhold any strategy preference until Step 3.2; ranking scenarios by desirability at this step is prohibited.

**Required Outputs**:

- A per-scenario implication record covering 7 implication categories.
- A uniform question-set response covering 5 questions per scenario.
- An early-indicator candidate list per scenario, feeding Step 5.2.
- An explicit unknown register listing questions the scenario cannot answer.

**Quality Checkpoints**:

- 100% of retained scenarios receive the identical question set; a scenario receiving a different question set is re-derived.
- Each scenario yields at least 1 early-indicator candidate; a scenario yielding 0 indicators is flagged as unmonitorable and reviewed for retirement.
- Scenario consequences and response consequences are recorded in separate fields; conflation of the two in any scenario returns that record for correction.
- No implication record contains a strategy recommendation; a recommendation appearing at this step is moved to Step 3.2 before the phase closes.

***

#### Step 3.2: Construct the Strategy Portfolio by Component Class

**Required Actions**:

- Generate multiple candidate strategies differing in timing, commitment, architecture, and exposure, with no fewer than 3 candidates.
- Classify every action inside each candidate strategy into exactly 1 of the 6 component classes.
- Record for each component its cost, carrying cost, lead time, reversibility, prerequisite, and expiry where applicable.
- Attach an explicit risk-acceptance record to every big-bet component.
- Attach a named trigger placeholder, an owner, and a lead time to every contingent component, to be completed in Step 5.2.
- Verify that opportunity cost, maintenance cost, and downside have been modelled for every component classified as no-regret.

**Strategy component classification**:

| Component class | Definition | Required attributes | Misclassification test |
| :-- | :-- | :-- | :-- |
| Core or no-regret action | Produces acceptable value across nearly all relevant scenarios | Cost, lead time, prerequisite | Fails if opportunity cost, maintenance cost, or downside is unmodelled |
| Hedge | Reduces downside if an adverse future occurs | Carrying cost, coverage scope, activation condition | Fails if carrying cost is unrecorded |
| Option | Preserves the right but not the obligation to act later | Premium, expiry date, exercise prerequisite | Fails if expiry or exercise prerequisite is absent |
| Big bet | High value in a narrow future, exposure elsewhere | Exposure quantum, recorded risk acceptance, approver | Fails if risk acceptance is not recorded by a named approver |
| Contingent action | Bound to a named trigger and branch playbook | Trigger, owner, lead time, playbook reference | Fails if any of the 4 attributes is missing |
| Exit or safe-state action | Limits loss when no primary strategy remains acceptable | Loss ceiling, activation authority, degraded-mode definition | Fails if no activation authority is named |

**Required Outputs**:

- A candidate strategy set of no fewer than 3 strategies.
- A component classification assigning every action to exactly 1 of the 6 classes.
- A component attribute record covering cost, carrying cost, lead time, reversibility, prerequisite, and expiry.
- Risk-acceptance records for all big-bet components.
- A safe-state definition available to every candidate strategy.

**Quality Checkpoints**:

- At least 3 candidate strategies exist and differ on at least 2 of timing, commitment, architecture, and exposure; strategies differing on fewer than 2 dimensions are merged.
- Every action is classified into exactly 1 component class; unclassified or multiply classified actions block phase closure.
- No-regret components do not exceed 60% of total component count in any candidate strategy; exceeding that share triggers a mandatory opportunity-cost review before Phase 4.
- 100% of big-bet components carry a recorded risk acceptance with a named approver; an unaccepted big bet is removed from its strategy.
- Every candidate strategy includes at least 1 exit or safe-state action; a strategy without one is not admitted to stress testing.

***

### Phase 4: Cross-Scenario Stress Testing and Robustness Measurement

**Objective**: Produce comparable evidence about every strategy in every retained scenario, convert that evidence into robustness, regret, and feasibility measures, and locate the conditions under which each strategy fails.

#### Step 4.1: Stress-Test Every Strategy in Every Scenario

**Required Actions**:

- Evaluate the complete strategy-by-scenario matrix, including cells whose outcome appears obvious in advance.
- Apply a common criterion set to every cell: goal attainment, hard-constraint satisfaction, safety, cost, time, resource consumption, reversibility, adaptability, stakeholder impact, recovery, and residual uncertainty.
- Keep raw model outputs in fields separate from analyst or agent judgements.
- Apply wargaming where actors respond, assigning roles, declaring moves, applying action, reaction, and counteraction, and using a documented adjudication method.
- Distinguish branches, which are contingencies inside the current plan, from sequels, which follow different outcomes, and associate each with a decision point and an information requirement.
- Conduct an immediate post-exercise review capturing decisions, surprises, unresolved disputes, and adjudication assumptions.
- Apply quantitative simulation only where causal and distributional assumptions are defensible, and run sensitivity analysis over model structure as well as over parameters.
- Preserve tails and constraint violations in the recorded results; report distributions rather than means alone.
- Compare simulation output against historical cases, holdout data, extreme-but-plausible tests, and a simple baseline model.
- Commission an independent red team to attack the favoured strategy, its data, its trigger logic, and its recovery claims, keeping that team organisationally and cognitively distinct.

**Stress-test matrix structure**:

| Strategy | Scenario S1 | Scenario S2 | Scenario S3 | Scenario S4 |
| :-- | :-- | :-- | :-- | :-- |
| Strategy A | Constraint status, criterion vector, failure mode, recovery path | Constraint status, criterion vector, failure mode, recovery path | Constraint status, criterion vector, failure mode, recovery path | Constraint status, criterion vector, failure mode, recovery path |
| Strategy B | Constraint status, criterion vector, failure mode, recovery path | Constraint status, criterion vector, failure mode, recovery path | Constraint status, criterion vector, failure mode, recovery path | Constraint status, criterion vector, failure mode, recovery path |
| Strategy C | Constraint status, criterion vector, failure mode, recovery path | Constraint status, criterion vector, failure mode, recovery path | Constraint status, criterion vector, failure mode, recovery path | Constraint status, criterion vector, failure mode, recovery path |

**Required Outputs**:

- A fully populated strategy-by-scenario matrix with no unevaluated cells.
- A criterion-level score vector per cell across 11 named criteria.
- A separated record of raw outputs and interpretive judgements per cell.
- Wargame move logs with adjudication rulings and disputed calls, where wargaming was used.
- A post-exercise review record per exercise.
- Red-team findings with dispositions.

**Quality Checkpoints**:

- Matrix completion is 100%; any unevaluated cell blocks Step 4.2, and a cell skipped on grounds of obviousness is a process defect requiring evaluation.
- All 11 criteria are scored in every cell, or an omission carries a recorded justification; more than 2 unjustified omissions across the matrix returns the step.
- Raw outputs and judgements occupy distinct fields in 100% of cells; merged fields invalidate the cell.
- Every wargame turn records the evidence available at that time; turns adjudicated on hindsight evidence are rerun.
- At least 1 pivotal adjudication per exercise is rerun under an alternative plausible ruling; divergent outcomes are reported rather than reconciled.
- The red team is not staffed from the strategy's authoring group; shared authorship voids the red-team record.

***

#### Step 4.2: Measure Robustness, Regret, and Feasibility

**Required Actions**:

- Enforce hard constraints first, marking any strategy violating an authorised safety, legal, ethical, or mission constraint as infeasible in that scenario rather than as lower scoring.
- Compute the fraction of retained scenarios in which each strategy meets every minimum threshold.
- Compute worst-case performance, maximum regret, and percentile regret relative to the best strategy available in each scenario.
- Compute downside severity, recovery time, switching cost, and remaining resource reserve per strategy.
- Apply probability-weighted expected utility only where probabilities and utilities are credible and have passed sensitivity testing; record the justification alongside the result.
- Test dominance, removing any strategy that is no worse on every authorised criterion and better on at least one, unless it carries unmodelled option value that is then recorded.
- Perturb assumptions, weights, model versions, prompts, and seeds within plausible ranges, and record whether strategy rankings change.
- Report ranking instability as a finding rather than resolving it into a single winner.

**Robustness measure set**:

| Measure | Definition | Reporting rule | Threshold consequence |
| :-- | :-- | :-- | :-- |
| Threshold satisfaction fraction | Share of retained scenarios meeting every minimum threshold | Reported per strategy and per scenario class | Below 0.60 disqualifies the strategy as a standalone core |
| Worst-case outcome | Lowest criterion vector across retained scenarios | Reported per criterion, never aggregated away | A worst case breaching a hard constraint marks infeasibility |
| Maximum regret | Largest shortfall against the best strategy in any single scenario | Reported with the scenario that produced it | Exceeding the authorised regret bound requires a hedge or an option |
| Percentile regret | Regret at the declared percentile of the retained set | Reported at a stated percentile | Used where maximum regret is driven by 1 outlier scenario |
| Hard-constraint violation rate | Share of scenarios in which a constraint is violated | Reported as a count and a share | Any rate above 0 requires an explicit feasibility disposition |
| Recovery time | Time to return to an acceptable state after failure | Reported per failure mode | Exceeding the authorised window requires a prepared branch |
| Switching cost | Cost of moving from this strategy to an alternative | Reported per candidate transition | High switching cost reduces adaptability scoring |
| Resource reserve | Uncommitted resource remaining after execution | Reported as absolute and as share of budget | A reserve of 0 removes the capacity to activate contingent actions |

**Required Outputs**:

- A feasibility determination per strategy-scenario cell separating infeasibility from low score.
- A robustness profile per strategy covering all 8 measures.
- A regret table reporting maximum and percentile regret with source scenarios.
- A dominance analysis with removals and their justifications.
- A stability report recording rank changes under perturbation.

**Quality Checkpoints**:

- Hard-constraint violations are recorded as infeasibility in 100% of affected cells; a violation converted into a score penalty is a scoring defect that invalidates the comparison.
- Every strategy carries all 8 robustness measures; a missing measure blocks selection in Step 5.1.
- Probability-weighted results, where present, carry a recorded credibility justification and a sensitivity test; results without both are removed from the decision basis.
- Rank stability is tested against at least 5 perturbation types covering assumptions, weights, models, prompts, and seeds; fewer than 5 leaves the stability claim unsupported.
- Where ranking changes under any single plausible perturbation, instability is reported explicitly and a single winner is not declared.

***

#### Step 4.3: Discover Vulnerability Regions and Missing Scenarios

**Required Actions**:

- Identify for each strategy the combinations of uncertain conditions under which it fails an acceptance threshold.
- Apply scenario discovery or interpretable clustering over large ensembles, selecting an outcome and a threshold, then finding compact uncertainty ranges that balance coverage of failures against density inside the identified region.
- Express each vulnerability region in terms a decision maker can monitor, naming the variables and the ranges that define it.
- Translate every vulnerability into exactly 1 of 4 responses: modify the core strategy, purchase a hedge, preserve an option, or accept and govern the residual risk.
- Add a scenario and return to Step 3.1 where a discovered failure region is not represented in the curated set.
- Return to Step 3.2 where a strategy is fundamentally brittle across the discovered regions. This is the second explicit loop.

**Required Outputs**:

- A vulnerability region catalogue per strategy, with defining variables and ranges.
- A coverage and density statistic per region.
- A vulnerability disposition record assigning 1 of 4 responses to every region.
- A scenario addition list for uncovered failure regions.
- A brittleness determination per strategy.

**Quality Checkpoints**:

- Every strategy carries at least 1 identified vulnerability region or a recorded statement that no failure was observed within the sampled space; an absent vulnerability analysis blocks Phase 5.
- Every vulnerability region is defined by no more than 4 variables; regions requiring more than 4 are reported as uninterpretable and re-derived at a coarser resolution.
- 100% of vulnerability regions carry a disposition among the 4 authorised responses; an undisposed region blocks selection.
- Every discovered failure region not represented in the curated set produces a new scenario within 1 loop iteration; a second uncovered region after that iteration escalates to human review.
- A strategy failing acceptance thresholds in more than 50% of retained scenarios is marked brittle and returned to Step 3.2 rather than carried into selection.

***

### Phase 5: Portfolio Selection and Adaptive Control Design

**Objective**: Select the portfolio under a pre-authorised decision rule, then equip it with the signposts, triggers, playbooks, and executable branch plans that make adaptation possible before losses become irreversible.

#### Step 5.1: Select the Robust and Adaptive Portfolio

**Required Actions**:

- Apply the decision rule approved in Step 1.1 rather than a rule constructed after the results are known.
- Record why the selected combination is preferable, which scenarios it covers, where it remains weak, which trade-offs were accepted, and which stakeholder made the decision.
- Refuse to manufacture a composite score where stakeholders have not authorised the weights.
- Prefer staged commitments where information will arrive over time: commit now to capabilities common across scenarios, run probes that reduce important uncertainty, reserve resources for contingent moves, and defer irreversible bets to their information deadline rather than indefinitely.
- Assign an information deadline to every deferred commitment, past which deferral becomes a decision by default.
- Express the selection as a conditional policy mapping observed conditions to actions, not as a confidence statement.

**Required Outputs**:

- A selected portfolio with core actions, hedges, options, contingent actions, and safe states enumerated.
- A decision record naming the rule applied, the alternatives considered, the trade-offs accepted, the dissent recorded, and the approver.
- A staged commitment schedule with an information deadline per deferred item.
- A conditional policy statement mapping conditions to actions.

**Quality Checkpoints**:

- The decision rule applied is identical to the rule recorded in Step 1.1; a substituted rule requires re-approval before the portfolio is released.
- Composite scores, where present, use weights authorised by a named stakeholder; unauthorised weights are removed and the comparison is reported by criterion instead.
- Every deferred commitment carries an information deadline; a deferral without a deadline is converted into an option with an expiry or removed.
- Recorded dissent is preserved in the decision record; a unanimous record produced by discarding dissent is a logging defect.
- The portfolio covers at least 1 prepared response for every scenario retained in Step 2.3; an uncovered scenario returns the run to Step 3.2.

***

#### Step 5.2: Define Signposts, Triggers, and Branch Playbooks

**Required Actions**:

- Define each signpost as an observable indicator tied to an uncertainty or a causal transition identified in Step 3.1.
- Record for every trigger the data source, measurement method, direction, threshold, persistence requirement, confidence rule, check frequency, owner, decision authority, lead time, activation window, branch, rollback condition, and fallback if data are unavailable.
- Prefer leading indicators; reclassify any indicator visible only after the response window closes as a postmortem label rather than a control.
- Combine multiple indicators where any single indicator is noisy, and apply hysteresis or persistence rules to prevent oscillation around a threshold.
- Write the branch playbook before activation, specifying prerequisites, tasks, resources, communications, safety checks, handoffs, and success and abort conditions.
- Rehearse every playbook at least once before it is relied upon, and record detection, decision, activation, restoration, and rollback times from the rehearsal.
- Ground playbooks in the essential functions, impacts, and recovery capabilities identified for the decision rather than in improvised reaction.

**Trigger specification template**:

```
TRIGGER_ID:
LINKED_SCENARIO_IDS:
LINKED_UNCERTAINTY_ID:
SIGNPOST_IDS:
DATA_SOURCE:
MEASUREMENT_METHOD:
DIRECTION:
THRESHOLD:
PERSISTENCE_REQUIREMENT:
CONFIDENCE_RULE:
CHECK_FREQUENCY:
OWNER:
DECISION_AUTHORITY:
LEAD_TIME_REQUIRED:
ACTIVATION_WINDOW:
BRANCH_ID:
ROLLBACK_CONDITION:
DATA_UNAVAILABLE_FALLBACK:
LAST_REHEARSAL_DATE:
REHEARSAL_LATENCY_MEASURED:
```

**Required Outputs**:

- A signpost inventory linked to uncertainties and scenarios.
- A trigger specification carrying all 14 required fields per trigger.
- A branch playbook per contingent action, with rehearsal records.
- A measured end-to-end latency record covering detection, decision, activation, restoration, and rollback.

**Quality Checkpoints**:

- Every trigger carries all 14 required fields; a trigger missing an owner, an authority, a data source, or a response window is non-operational and is removed or completed before release.
- Measured signpost lead time exceeds the required action lead time by a margin of at least 1 check interval; a trigger failing this test is replaced with an earlier indicator or its branch is re-scoped.
- Every trigger applies a persistence or hysteresis rule; a single-observation trigger on a noisy source is rejected.
- 100% of contingent actions have a written playbook, and at least 80% have been rehearsed before release; below 80% rehearsal coverage the portfolio is released with a recorded readiness caveat.
- Every playbook terminates in both a success condition and an abort condition; a playbook with only a success condition is incomplete.

***

#### Step 5.3: Convert Branches Into Executable Plans

**Required Actions**:

- Pass each selected branch to goal decomposition and hierarchical task network planning to produce primitive task sequences.
- Apply constraint satisfaction to schedules, allocations, staffing, and routing inside each branch.
- Supply orchestration systems with stable task identifiers, dependencies, leases, retry and compensation rules, and escalation paths.
- Mark each task as preparatory, dormant, active, cancelled, or completed, and keep the marking authoritative in the orchestration store rather than in narrative text.
- Revalidate current facts immediately before any consequential action, since a broadly correct scenario can coexist with a stale operational prerequisite.
- Preserve human approval for actions outside delegated authority, for high-impact commitments, and for cases where trigger evidence is ambiguous.

**Required Outputs**:

- A branch plan per selected branch, decomposed to primitive tasks.
- A feasibility determination per branch from constraint checking.
- An orchestration handoff record with task identifiers, dependencies, retry rules, and escalation paths.
- A task state assignment across the 5 named states.
- A pre-execution validation rule per consequential action.

**Quality Checkpoints**:

- Every selected branch decomposes to primitive tasks with no unexpanded compound task; an unexpanded task blocks activation of that branch.
- Constraint checking returns feasible for 100% of branches under their activating scenario; an infeasible branch is repaired or replaced before release.
- Every consequential action carries a pre-execution validation rule naming the facts to recheck and their maximum acceptable age.
- Actions exceeding delegated authority carry a named human approver; an unapproved high-impact action cannot be dispatched by orchestration.
- Task states are held in the orchestration store; a task whose only state record is narrative text is treated as unknown and blocked.

***

### Phase 6: Execution, Monitoring, Replanning, and Closure

**Objective**: Execute the portfolio, observe the world against the whole scenario set, adapt through pre-authorised transitions, replan when reality leaves the envelope, and close the run with recorded learning.

#### Step 6.1: Execute Probes and Monitor the World

**Required Actions**:

- Begin with reversible actions that either create cross-scenario value or reveal information.
- Monitor signposts at the declared cadence, validate data quality on every reading, and record the specific observation that changed a belief or activated a branch.
- Compare the actual state against every retained scenario, not only against the previously favoured one.
- Select exactly 1 transition at each checkpoint from: continue the current core plan, activate an option, retire an option, switch to a prepared branch, request verification, escalate, pause in a safe state, or replan.
- Confirm authorisation and preconditions before dispatching any playbook when a trigger fires, then monitor execution to completion or abort.
- Gather discriminating evidence where indicators conflict, rather than averaging conflicting readings into false certainty.

**Required Outputs**:

- A probe execution log with reversibility status and information yield per probe.
- A signpost observation series with data-quality flags and latency measurements.
- A scenario-fit assessment per checkpoint, scored against all retained scenarios.
- A transition decision record per checkpoint naming the selected transition among the 8 authorised options.
- A trigger activation record with authorisation, dispatch time, and outcome.

**Quality Checkpoints**:

- The first executed actions are reversible or information-revealing; an irreversible action executed before its information deadline is a sequencing defect requiring escalation.
- Signpost readings occur at or above the declared check frequency; a missed interval exceeding 1 cadence period activates the data-unavailable fallback.
- Every checkpoint scores the observed state against 100% of retained scenarios; scoring against only the favoured scenario invalidates the checkpoint.
- Exactly 1 transition is selected per checkpoint; a checkpoint closing with no recorded transition is reopened.
- Conflicting indicators produce a discriminating-evidence request rather than an averaged value; an averaged reading across conflicting sources is a measurement defect.

***

#### Step 6.2: Update Scenarios and Replan

**Required Actions**:

- Update scenario weights only where probabilistic beliefs are defensible; otherwise update evidence strength, plausibility status, and proximity indicators.
- Record the reason for every update alongside the evidence that prompted it.
- Version each scenario rather than rewriting it in place, so that evaluators can reconstruct what was known at the time of a decision.
- Return to Step 4.1 or Step 4.3 where reality remains inside a modelled scenario but a strategy underperforms, and repair the strategy.
- Return to Step 1.3 where a new causal mechanism appears, constraints change, or no retained scenario fits the observed state, and rebuild the relevant uncertainty space.
- Return to Step 1.1 where the objective, the authority, or the acceptance thresholds change.
- Set refresh dates that apply even when no trigger fires, calibrated so that the refresh interval is shorter than the time needed to observe, decide, and act before a commitment becomes irreversible.

**Required Outputs**:

- A scenario version history with update reasons and evidence links.
- A plausibility and proximity status per scenario, distinct from any probability field.
- A replanning decision record naming the return target among Step 1.1, Step 1.3, Step 4.1, and Step 4.3.
- A refresh schedule with an interval justification.

**Quality Checkpoints**:

- Scenario updates create new versions in 100% of cases; an in-place rewrite destroying prior state is a logging defect that invalidates reproducibility.
- Probability fields are populated only where a defensible basis is recorded; an unjustified probability is replaced with a plausibility status.
- Out-of-envelope observations route to Step 1.3 rather than to the nearest existing scenario; forcing an out-of-envelope observation into an existing scenario is a framing defect.
- The refresh interval is strictly shorter than the observe-decide-act time for the nearest irreversible commitment; an interval equal to or longer than that time is reduced before the next cycle.
- Every replanning decision names exactly 1 return target and its triggering condition.

***

#### Step 6.3: Close the Run and Capture Learning

**Required Actions**:

- Close the run only when the decision horizon ends, the objective is achieved or superseded, the risk is explicitly accepted, or authority transfers.
- Record actual outcomes, which scenario or mixture best described events, which signposts led and which lagged, which triggers fired correctly and incorrectly, which options proved useful, and what costs were incurred.
- Run a process postmortem separately from an outcome judgement, since a sound process can meet a poor outcome and an unsound process can be fortunate.
- Update scenario templates, historical priors, model tests, trigger thresholds, strategy libraries, and owner training from the recorded findings.
- Preserve failed scenarios and unused branches as evidence rather than deleting them.
- Compare the realised process cost and value against a simpler baseline process for the same decision class.

**Required Outputs**:

- A closure record naming the closure reason among the 4 authorised conditions.
- An outcome record with realised results and best-fitting scenario identification.
- A signpost and trigger performance record with lead and lag classification.
- A separated process postmortem and outcome judgement.
- An updated artifact set covering templates, priors, thresholds, libraries, and training.
- A baseline comparison recording process cost and marginal value.

**Quality Checkpoints**:

- The closure reason matches 1 of the 4 authorised conditions; closure for any other reason requires human authorisation before the run is archived.
- Process assessment and outcome assessment are recorded in separate fields; a merged assessment is returned for separation.
- 100% of failed scenarios and unused branches are retained in the archive; deletion of a failed scenario is a governance defect.
- Every trigger receives a correctness classification of true positive, false positive, true negative, or false negative; an unclassified trigger blocks the learning update.
- The baseline comparison records both cost and marginal value; a comparison recording only cost does not satisfy the closure requirement.

***

## III. Implementation Guidance for AI Agents

AI agents executing Scenario-Based Planning must follow systematic protocols that separate scenario construction from evaluation, keep authoritative state outside the conversational context, and route every consequential commitment through an approval gate. The following guidance translates the six-phase framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Supervisor Agent**: Owns the decision contract, holds the budget declaration, authorises phase transitions, and is the only role permitted to declare closure. Enforces the uncertainty-regime rule at every method selection and refuses any method whose evidentiary preconditions are unmet.
2. **Framing Agent**: Owns Phase 1. Produces the decision contract, the baseline, the lever inventory, and the uncertainty and assumption register. Never generates scenarios.
3. **Generation Agent Pool**: Owns Step 2.2. Runs as multiple independent instances receiving the identical decision contract and evidence packet while varying role, generation method, model version, or seed. Instances do not share intermediate output before curation.
4. **Curation Agent**: Owns Step 2.3. Applies plausibility, consistency, distinctness, coverage, discrimination, and surprise tests. Holds authority to retire candidates and to return the run to Step 1.3 or Step 2.2.
5. **Evaluation Agent**: Owns Phase 4. Populates the strategy-by-scenario matrix, computes robustness and regret measures, and keeps raw outputs separate from interpretation. Does not select a portfolio.
6. **Red-Team Agent**: Operates against Phase 1, Phase 2, and Phase 4 outputs. Staffed with a different model version, prompt lineage, or role framing than the agents whose work it attacks. Its findings are recorded with dispositions and cannot be silently dismissed.
7. **Adaptive Control Agent**: Owns Phase 5 signpost, trigger, and playbook construction, and Phase 6 monitoring. Holds the trigger state and issues activation requests to orchestration.
8. **Archivist Agent**: Owns the six record types below. Rejects any phase transition whose required records are absent or incomplete.

**Workflow Execution Pattern**:

```
STATE: Phase_2_Scenario_Generation_And_Curation
PRECONDITIONS:
  - decision_contract_approved == TRUE
  - uncertainty_regime_classified == TRUE
  - red_team_reviewed_register == TRUE
  - budget_declaration_immutable == TRUE
ACTIONS:
  1. Dispatch identical decision contract to N independent generators
  2. Collect candidates with full provenance
  3. Apply coverage, discrimination, and surprise tests
  4. Merge duplicates, split incoherent candidates, log retirements
VALIDATION:
  - high_impact_uncertainty_coverage == 1.00
  - load_bearing_assumption_coverage >= 0.90
  - candidate_provenance_completeness == 1.00
  - single_generator_share <= 0.60
  - marginal_yield_last_3_candidates > 0
TRANSITIONS:
  IF coverage_failure THEN next_state = Phase_2_Generation_Loop
  IF consistency_failure THEN next_state = Phase_1_Register_Rebuild
  IF marginal_yield == 0 AND coverage_pass THEN next_state = Phase_3_Implications
  ELSE next_state = Phase_2_Error_Handling
```

**Three-Phase Action Pattern**:

1. **Plan**: Emit the decision contract, uncertainty register, and budget declaration without generating any scenario narrative.
2. **Validate**: Confirm regime classification, lever inventory completeness, and red-team review while the run is still cheap to reframe.
3. **Execute**: Generate, curate, evaluate, and select only after the framing passes validation, then hold the portfolio behind the approval gate until Step 5.3 pre-execution validation succeeds.

**Approval Gate**: No action classified as irreversible, safety critical, or exceeding delegated authority may be dispatched by an agent without a named human approver recorded in the decision record. The gate additionally triggers where trigger evidence is ambiguous, where a probability field is populated without a recorded credibility justification, or where a strategy's maximum regret exceeds the authorised regret bound.

**Context Management Requirements**:

- Hold the scenario registry, evaluation store, and trigger state in persistent records rather than in the conversational context; recited plan text is a reminder, never the authoritative state.
- Evaluate the strategy-by-scenario matrix one scenario column at a time, appending results to the evaluation store rather than holding the full matrix in working context.
- Where a run exceeds the context available for a single pass, write a handoff record naming the completed phases, the pending cells of the matrix, the current trigger state, and the immutable budget declaration.
- Cap agent-driven scenario search on all 4 of depth, breadth, tokens, and wall-clock time before the search starts; an uncapped search is not authorised.

**Persistent Record Architecture**: Store concise decision records and externally inspectable evidence rather than private reasoning transcripts. A production implementation maintains six linked record types with stable identifiers and versions.

```
RUN_RECORD
RUN_ID:
PARENT_RUN_ID:
FOCAL_DECISION:
OBJECTIVE_VERSION:
ACCEPTANCE_TEST_VERSION:
SCENARIO_HORIZON:
DECISION_DEADLINE:
STAKEHOLDERS:
DECISION_OWNER:
RISK_CLASS:
AUTHORITY_BOUNDARIES:
BUDGET:
UNCERTAINTY_REGIME:
METHOD_SELECTION:
START_TIME:
END_TIME:
STATUS:
CLOSURE_REASON:
SOFTWARE_VERSION:
MODEL_VERSION:
PROMPT_VERSION:
POLICY_VERSION:
DATASET_VERSION:
SIMULATOR_VERSION:
```

```
UNCERTAINTY_AND_ASSUMPTION_RECORD
ITEM_ID:
STATEMENT:
CATEGORY:
ITEM_TYPE:            [MEASURED_FACT | ESTIMATE | STAKEHOLDER_BELIEF | STRESS_ASSUMPTION]
CURRENT_STATE_OR_RANGE:
SOURCE:
RETRIEVAL_DATE:
CONFIDENCE_OR_EVIDENCE_GRADE:
DEPENDENCIES:
CONTROLLABILITY:
OBSERVABILITY:
DECISION_IMPACT:
OWNER:
FALSIFIER:
CHANGE_HISTORY:
```

```
SCENARIO_RECORD
SCENARIO_ID:
VERSION:
PARENT_OR_GENERATION_LINEAGE:
HORIZON:
GENERATION_METHOD:
SEED:
BRANCH_DEPTH:
CONSTITUENT_UNCERTAINTY_IDS:
CAUSAL_PATHWAY:
ACTOR_ASSUMPTIONS:
QUANTITATIVE_RANGES:
EVIDENCE_LINKS:
PROBABILITY_STATUS:   [ASSESSED | NOT_PROBABILITY_ASSESSED]
PLAUSIBILITY_ASSESSMENT:
CONSISTENCY_CHECKS:
COVERAGE_TAGS:
DUPLICATE_CLUSTER:
REVIEWER:
APPROVAL_STATUS:
RETIREMENT_REASON:
```

```
STRATEGY_AND_EVALUATION_RECORD
STRATEGY_ID:
VERSION:
ACTIONS:
COMPONENT_CLASSES:
TIMING:
COMMITMENTS:
REVERSIBILITY:
PREREQUISITES:
COSTS:
HEDGES:
OPTIONS:
BRANCH_DEPENDENCIES:
EVALUATION_ID:
EVALUATED_SCENARIO_ID:
INPUT_VERSIONS:
MODEL_OR_ADJUDICATOR:
SEED:
RAW_OUTPUTS:
CONSTRAINT_VIOLATIONS:
CRITERION_LEVEL_SCORES:
UNCERTAINTY_INTERVALS:
FAILURE_MODE:
RECOVERY_PATH:
REGRET_COMPARATOR:
EVIDENCE_QUALITY:
REVIEWER_OVERRIDE:
OVERRIDE_RATIONALE:
```

```
TRIGGER_AND_EXECUTION_RECORD
SIGNPOST_ID:
TRIGGER_ID:
SOURCE:
THRESHOLD:
PERSISTENCE_RULE:
OBSERVATION_TIME:
EVENT_TIME:
DATA_LATENCY:
MISSINGNESS:
CONFIDENCE:
TRIGGER_STATE:
DECISION_OWNER:
AUTHORIZATION:
BRANCH_SELECTED:
DISPATCH_TIME:
ACTION_RESULT:
ROLLBACK:
CORRECTNESS_CLASS:    [TRUE_POSITIVE | FALSE_POSITIVE | TRUE_NEGATIVE | FALSE_NEGATIVE]
LINKED_SCENARIO_VERSION:
LINKED_STRATEGY_VERSION:
LINKED_TASK_IDS:
LINKED_INCIDENT_IDS:
```

```
DECISION_RECORD
DECISION_ID:
ALTERNATIVES_CONSIDERED:
DECISION_RULE:
TRADE_OFFS_ACCEPTED:
DISSENT_RECORDED:
SELECTED_CORE_ACTIONS:
ACCEPTED_RESIDUAL_RISKS:
DORMANT_OPTIONS:
INFORMATION_DEADLINES:
NEXT_REVIEW:
APPROVER:
EVIDENCE_SNAPSHOT:
```

Records are linked by identifier and version so that any executed task resolves to the scenario version and strategy version that authorised it. The record set must make a choice reproducible without implying that a single hidden reasoning transcript is authoritative.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Decision Frame Integrity (After Phase 1)**

- **Automated Check**: The focal decision admits at least 2 alternatives; hard constraints are separated from preferences; every acceptance threshold carries a numeric value or explicit categorical test; the uncertainty regime matches a row of the Section 1.3 rule; at least 3 candidate scenario axes are marked; every load-bearing assumption carries a falsifier.
- **Agent Action on Pass**: Freeze the decision contract and proceed to architecture selection.
- **Agent Action on Failure**: Halt and return the specific framing defect; no generation is authorised.
- **Human Review Trigger**: Fewer than 3 candidate scenario axes, or any load-bearing assumption marked unfalsifiable, or a decision with only 1 alternative.

**Checkpoint 2: Scenario Set Adequacy (After Phase 2)**

- **Automated Check**: High-impact uncertainty coverage is 1.00; load-bearing assumption coverage is at least 0.90; candidate provenance completeness is 1.00; single-generator share is at most 0.60; no 2 retained scenarios share both preferred decision and vulnerability profile; speculative scenarios are at most 25% of the retained set.
- **Agent Action on Pass**: Freeze the scenario set version and proceed to implication derivation.
- **Agent Action on Failure**: Return to Step 2.2 for a bounded additional generation pass, or to Step 1.3 where the gap is in the register rather than in generation.
- **Human Review Trigger**: Coverage still below threshold after 2 loop iterations, or a surprise-test finding naming an absent mechanism that generation cannot produce.

**Checkpoint 3: Portfolio Construction Validity (After Phase 3)**

- **Automated Check**: At least 3 candidate strategies differing on at least 2 dimensions; every action classified into exactly 1 of 6 component classes; no-regret components at most 60% of any strategy; every big bet carrying a recorded risk acceptance; every strategy carrying at least 1 safe-state action; every scenario carrying an implication record from the identical question set.
- **Agent Action on Pass**: Proceed to stress testing.
- **Agent Action on Failure**: Return the unclassified components and the strategies failing the differentiation test.
- **Human Review Trigger**: A no-regret share above 60% that survives an opportunity-cost review, indicating that downside has not been modelled.

**Checkpoint 4: Evaluation Integrity (After Phase 4)**

- **Automated Check**: Matrix completion is 1.00; all 11 criteria scored or justified per cell; raw outputs separated from judgements in 1.00 of cells; all 8 robustness measures computed per strategy; rank stability tested against at least 5 perturbation types; every vulnerability region defined by at most 4 variables and carrying 1 of 4 dispositions.
- **Agent Action on Pass**: Release the evaluation store to selection.
- **Agent Action on Failure**: Halt selection; return the incomplete cells and the missing measures.
- **Human Review Trigger**: Rankings change under any single plausible perturbation, or a strategy fails acceptance thresholds in more than 50% of retained scenarios, or a probability-weighted result lacks a credibility justification.

**Checkpoint 5: Adaptive Control Readiness (After Phase 5)**

- **Automated Check**: Every trigger carries all 14 required fields; measured lead time exceeds required action lead time by at least 1 check interval for 1.00 of triggers; persistence or hysteresis applied to 1.00 of triggers; playbook coverage of contingent actions is 1.00 and rehearsal coverage is at least 0.80; branch constraint feasibility is 1.00; every consequential action carries a pre-execution validation rule.
- **Agent Action on Pass**: Authorise execution of reversible and information-revealing actions.
- **Agent Action on Failure**: Withhold activation authority for the affected branches while permitting core actions to proceed.
- **Human Review Trigger**: Rehearsal coverage below 0.80 at release, or any trigger whose lead time cannot be made to exceed its action lead time.

**Checkpoint 6: Runtime and Closure Discipline (During and After Phase 6)**

- **Automated Check**: Each checkpoint scores the observed state against 1.00 of retained scenarios and records exactly 1 transition; refresh interval is strictly shorter than the observe-decide-act time for the nearest irreversible commitment; scenario updates create new versions in 1.00 of cases; every trigger carries a correctness classification at closure; process and outcome assessments occupy separate fields.
- **Agent Action on Pass**: Continue the runtime loop, or archive the run at closure.
- **Agent Action on Failure**: Reopen the checkpoint or block archival until the missing record is supplied.
- **Human Review Trigger**: An out-of-envelope observation, a closure reason outside the 4 authorised conditions, or a second branch switch across the same threshold within 1 cooldown period.

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
HUMAN_REVIEW_TRIGGERED:
RESPONSIBLE_AGENT:
LINKED_RUN_ID:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Scenario Set Degeneracy**

- **Symptoms**: Polished narratives with no decisions, thresholds, owners, or resources (scenario theatre); vivid or familiar futures preferred over coherent ones (narrative seduction); apparently diverse scenarios inheriting one data source, prompt, model, or causal assumption (correlated scenarios); every scenario a small deviation from the official forecast (baseline anchoring).
- **Diagnostic Steps**: Test whether each retained scenario changes an action, exposes a vulnerability, or justifies a hedge. Compare assumption overlap across the retained set. Measure the share of scenarios traceable to a single generator, prompt, and seed. Measure the maximum divergence of any scenario from the reference forecast.
- **Resolution Protocol**: Option A, restate the focal decision and retire every scenario that changes no action. Option B, score causal consistency and evidence before any scenario is named or narrated, and apply the identical implication question set to every future. Option C, vary generation methods, model versions, and reviewers, then commission an independent challenge round. Option D, generate at least 1 structural break, 1 reversed actor response, and 1 compound stress before any candidate is shown to the owner of the baseline plan.
- **Escalation Trigger**: More than 30% of retained scenarios fail the action-change test after 2 curation passes, or single-generator share remains above 0.60 after 1 diversification pass.

**Error Type 2: Scenario Explosion**

- **Symptoms**: The evaluation budget is consumed by branching; candidate count grows while coverage statistics remain flat; the strategy-by-scenario matrix cannot be completed within the declared budget.
- **Diagnostic Steps**: Compute marginal scenario yield over the most recent 5 candidates. Compute duplicate rate against the coverage tags. Compare branch depth and breadth against the caps declared in Step 2.1.
- **Resolution Protocol**: Option A, cluster near-duplicates and retire all but 1 member of each cluster. Option B, reduce breadth to the branches whose value or uncertainty justifies expansion, holding depth constant. Option C, allocate a small initial budget with an explicit extension request, so that expansion is a decision rather than a default.
- **Escalation Trigger**: Matrix completion below 0.80 at 100% of budget consumption, or marginal yield of 0 across 5 consecutive candidates while generation continues.

**Error Type 3: Unwarranted Precision**

- **Symptoms**: Exact probabilities assigned without evidence (false precision); simulation frequency or model confidence reported as real-world probability (probability laundering); a single composite score presented in place of a criterion vector.
- **Diagnostic Steps**: Trace every probability field to a recorded credibility justification. Check whether reported frequencies derive from the sampling design rather than from observed prevalence. Check whether composite weights were authorised by a named stakeholder.
- **Resolution Protocol**: Option A, replace point estimates with ranges, sensitivity tests, and alternative models. Option B, record the probability status as not probability assessed, which is a valid and preferred status under deep uncertainty. Option C, report by criterion and by scenario class rather than as a single aggregate. Option D, where a probability is genuinely required, obtain calibration evidence and a valid sampling basis before the field is populated.
- **Escalation Trigger**: Any probability field populated without a credibility justification halts selection; this error is never resolved by re-running the generator.

**Error Type 4: Evaluation Integrity Failure**

- **Symptoms**: A strategy performs well by exploiting simulator error (model exploitation); adjudication consistently favours the sponsor or the friendly plan (adjudication bias); results vary widely across seeds without the variance being reported.
- **Diagnostic Steps**: Compare strategy performance under model ensembles, holdout data, historical replay, and adversarial perturbation. Recompute pivotal adjudications under alternative plausible rulings. Measure repeated-run variance and inter-adjudicator disagreement.
- **Resolution Protocol**: Option A, evaluate against at least 2 independent models or adjudicators and report divergence rather than a reconciled value. Option B, predeclare adjudication rules, record disputed calls, and use multiple adjudicators for consequential turns. Option C, add a real-world probe that tests the specific mechanism the strategy appears to exploit. Option D, discount any performance advantage that disappears under out-of-model testing.
- **Escalation Trigger**: A performance advantage that does not survive out-of-model testing is removed from the decision basis; if the selected portfolio depended on that advantage, the run returns to Step 4.1 for at most 1 re-evaluation cycle before human review.

**Error Type 5: Adaptive Control Failure**

- **Symptoms**: Triggers fire after the response window closes, or fail to fire at all (trigger failure); branches switch repeatedly around a threshold boundary (plan oscillation); a trigger has no owner, authority, data source, or response window.
- **Diagnostic Steps**: Measure end-to-end lead time from observation through decision to activation and compare it against the branch's required lead time. Count switch events per cooldown period. Audit trigger records for the 14 required fields.
- **Resolution Protocol**: Option A, replace the indicator with an earlier one, or re-scope the branch so its required lead time fits the available window. Option B, add persistence, hysteresis, switching costs, or a cooldown period before reversal, while preserving an emergency override path. Option C, define a fallback data source and a default action for the data-unavailable case. Option D, rehearse activation and record measured latencies, then reset the threshold from measurement rather than from estimate.
- **Escalation Trigger**: Any trigger whose measured lead time cannot be made to exceed its required action lead time after 2 redesign attempts is escalated as an uncontrollable risk and its scenario is dispositioned as accepted residual risk.

**Error Type 6: Plan Staleness and Envelope Escape**

- **Symptoms**: A plan remains internally coherent after the environment has changed; observations do not match any retained scenario; branch plans reference stale operational prerequisites.
- **Diagnostic Steps**: Compare observed state against every retained scenario and record the best-fit score for each. Check input versions and retrieval dates against the refresh schedule. Verify pre-execution validation results for the active branch.
- **Resolution Protocol**: Option A, route the out-of-envelope observation to Step 1.3 and rebuild the affected uncertainty space rather than mapping it to the nearest existing scenario. Option B, version all inputs and enforce mandatory refresh dates independent of trigger activity. Option C, pause in a safe state while the scenario set is rebuilt, where the active branch depends on an invalidated prerequisite.
- **Escalation Trigger**: A second out-of-envelope observation within 1 refresh interval returns the run to Step 1.1 for decision-contract review rather than to Step 1.3.

**Troubleshooting Decision Tree**:

```
SBP RUN FAILS A CHECKPOINT
├─ FRAMING DEFECT
│   ├─ Fewer than 2 alternatives → HALT, escalate under Exclusion 2
│   ├─ Unquantified acceptance threshold → Return to Step 1.1, quantify
│   └─ Regime unmatched by Section 1.3 rule → HALT, reclassify before generation
├─ SCENARIO SET DEFECT
│   ├─ Coverage below threshold → Return to Step 2.2, bounded generation pass
│   ├─ Correlated generation above 0.60 → Diversify generator, prompt, model, seed
│   ├─ Marginal yield 0 with coverage pass → Stop generation, proceed to Phase 3
│   └─ Absent mechanism named by surprise test → Return to Step 1.3
├─ EVALUATION DEFECT
│   ├─ Incomplete matrix → Complete cells before any comparison
│   ├─ Constraint violation scored as penalty → Reclassify as infeasible
│   ├─ Unjustified probability field → HALT selection, set NOT_PROBABILITY_ASSESSED
│   └─ Rank unstable under perturbation → Report instability, do not name a winner
├─ CONTROL DEFECT
│   ├─ Trigger lead time below action lead time → Replace indicator or re-scope branch
│   ├─ Trigger missing owner or authority → Non-operational, complete or remove
│   ├─ Oscillation across threshold → Add persistence, hysteresis, cooldown
│   └─ Playbook without abort condition → Complete before activation authority granted
└─ RUNTIME DEFECT
    ├─ Out-of-envelope observation → Return to Step 1.3, rebuild uncertainty space
    ├─ Second escape within one refresh interval → Return to Step 1.1
    ├─ In-place scenario rewrite → Restore version history, log defect
    └─ Deleted failed scenario or branch → Governance defect, HALT archival
```

**Prohibited Practices**: The following are defects regardless of the outcome they produce. Treating a scenario as a prediction and scoring it by whether it came true. Assigning probabilities without defensible evidence. Optimising only for the most likely future. Creating cosmetic variants that differ in name and prose but not in causal structure. Omitting actor reactions from scenarios where competitors, adversaries, users, regulators, or partners can adapt to the plan. Treating simulation frequency, model confidence, or majority vote as real-world likelihood. Allowing a compelling narrative to override a hard constraint or contradictory evidence. Generating more branches than can be evaluated, monitored, or acted upon. Deferring every commitment despite option carrying costs, expiry dates, and prerequisites. Operating a trigger with no owner, authority, data source, or response window. Treating a prepared playbook as completed execution. Deleting failed scenarios or overriding history.

### D. Performance Metrics and Continuous Learning

Metrics exist to improve the process, not to reward the production of more scenarios. AI agents must report metrics by criterion and by scenario class rather than as a single aggregate score.

**Scenario-Set Quality Metrics**:

- **High-impact uncertainty coverage**: Share of Step 1.3 high-impact uncertainties stressed by at least 1 retained scenario (target: 1.00; below 1.00 blocks Phase 3).
- **Load-bearing assumption coverage**: Share of load-bearing assumptions stressed by at least 1 retained scenario (target: at least 0.90).
- **Distinctness**: Share of retained scenario pairs differing in both preferred decision and vulnerability profile (target: 1.00).
- **Internal-consistency pass rate**: Share of retained scenarios passing causal and temporal consistency checks (target: 1.00).
- **Evidence traceability**: Share of retained scenarios linked to at least 1 register evidence item (target: at least 0.75).
- **Unique-yield fraction**: Share of retained scenarios exposing a vulnerability or action not exposed by any other scenario (target: at least 0.75).
- **Duplicate rate and marginal yield**: Duplicate rate rising while marginal yield falls to 0 is the stopping signal for generation.

**Strategy Robustness Metrics**:

- **Threshold satisfaction fraction**: Share of retained scenarios in which the strategy meets every minimum threshold (target: at least 0.60 for a standalone core).
- **Worst-case outcome and downside percentile**: Reported per criterion, never aggregated (no target; reported as evidence).
- **Maximum and percentile regret**: Reported with source scenario (target: within the authorised regret bound; breach requires a hedge or an option).
- **Hard-constraint violation rate**: Share of cells with a violation (target: 0; any violation requires an explicit feasibility disposition).
- **Recovery time, switching cost, option exercise value, and resource reserve**: Reported per strategy (target: recovery within the authorised window; reserve above 0).

**Sensitivity and Stability Metrics**:

- **Rank change rate under perturbation**: Share of perturbations that change the strategy ranking, across assumptions, weights, models, prompts, and seeds (target: at most 0.20; above that the ranking is reported as unstable).
- **Repeated-run variance**: Variance of the decision metric across seeds (target: within the stability band declared in Step 2.1).
- **Adjudicator disagreement**: Share of consequential turns with divergent rulings (target: reported, not minimised; above 0.30 requires rerunning pivotal branches).
- **Out-of-model performance gap**: Difference between in-model and out-of-model performance (target: gap below the authorised tolerance; a larger gap removes the advantage from the decision basis).

**Adaptation Quality Metrics**:

- **Signpost lead time**: Time from observable change to trigger threshold crossing (target: exceeds required action lead time by at least 1 check interval).
- **Observation, decision, and activation latency**: Measured end to end from rehearsals and live activations (target: sum below the activation window).
- **Trigger precision and missed-trigger rate**: Computed from the correctness classification of every trigger (target: precision at least 0.80; missed-trigger rate at most 0.10).
- **Branch readiness**: Share of contingent actions with a rehearsed playbook (target: at least 0.80).
- **Successful switch rate and rollback rate**: Computed per activation (target: rollback rate at most 0.20).
- **Performance delta across adaptation**: Outcome before and after a branch activation, evaluated for whether the trigger arrived early enough to complete its action rather than merely correlating with the event.

**Process Efficiency Metrics**:

- **Elapsed time, human hours, model tokens, tool calls, simulation runs, and scenario count**: Reported against the Step 2.1 budget declaration (target: within declared budget).
- **Cost per new vulnerability found**: Total run cost divided by count of distinct vulnerability regions discovered (target: falling across successive runs in the same decision class).
- **Cost per decision-relevant scenario**: Total generation cost divided by count of scenarios passing the unique-yield test.
- **Marginal robustness improvement per iteration**: Change in threshold satisfaction fraction per loop iteration (target: greater than 0; a value of 0 across 2 iterations ends the loop).
- **Baseline comparison**: Cost and value of the full process against a simpler baseline for the same decision class (target: positive marginal value; a non-positive result reclassifies the decision under Exclusion 1).

**Calibration Metrics**: Calibration applies only where probabilities were declared. Proper scoring rules such as Brier or logarithmic score apply to event forecasts; calibration curves apply across repeated decisions; interval coverage applies to declared ranges. Exploratory scenarios must never be scored as failed predictions; they are scored on whether they were plausible, decision-relevant, monitored, and useful for action.

**Realised Value Metrics**: Avoided loss, opportunity captured, reduced recovery time, reduced surprise, value of information from probes, options exercised or retired, and decision reversals made before rather than after an irreversible commitment. Because counterfactual benefits are uncertain, the estimation method and its range are preserved with every value claim.

**Learning and Adaptation Mechanisms**:

- **Feedback collection**: Record every checkpoint failure with its phase boundary, its cause, and its correction, and link it to the run record.
- **Threshold recalibration**: Reset trigger thresholds from measured rehearsal and activation latencies rather than from estimates, after every closure.
- **Template refinement**: Where the same record field is repeatedly omitted, add it to the archivist's rejection rule rather than relying on drafting discipline.
- **Strategy library maintenance**: Retain failed strategies and retired scenarios as evidence, indexed by the vulnerability region that defeated them, so that later runs in the same decision class inherit the failure knowledge.
- **Regime rule maintenance**: Record every case where the selected method's evidentiary preconditions proved unmet in practice, and refine the Section 1.3 selection rule when 3 or more such cases accumulate in the same regime row.

***

## IV. Domain-Agnostic Application Guidance

The framework is designed for generalisability. Its phases depend on the structure of the decision, not on the subject matter of the domain. The three application profiles below illustrate the method across dissimilar sectors; the adaptation notes that follow generalise it further.

**Application Profile A, commercial launch under regulatory and demand uncertainty**: An organisation must decide whether to launch a high-impact service within a fixed horizon, which compliance architecture to build, and how much capacity to reserve. Hard constraints require safety testing, privacy controls, and legal approval. The critical uncertainties are the timing and scope of regulation, demand growth, the availability and price of scarce capacity, and the incidence of serious failures.

The scenario set contains four futures: gradual regulation with moderate demand; strict sector rules arriving before launch; rapid demand accompanied by capacity scarcity; and a public failure producing customer caution and emergency oversight. Each future specifies regulator, customer, supplier, and competitor responses rather than varying revenue alone. Three strategies are stress-tested: a fast monolithic launch, a modular staged launch, and a delayed launch after regulation stabilises. The monolithic strategy wins in the rapid-demand future but creates unacceptable rework and suspension exposure under strict rules. Delay reduces compliance uncertainty at the cost of learning and market access. The staged strategy is best in no single future yet meets the minimum thresholds in all four, which is the definition of robustness applied in Step 4.2.

The selected portfolio funds shared controls, evaluation infrastructure, audit logging, and a modular policy layer as core actions; pilots with low-impact customers and reserves rather than purchases expansion capacity as options; and pre-negotiates an external assurance review as a hedge. The strict-regulation branch activates when enacted obligations or published guidance cross a defined scope threshold. The capacity branch activates when reservation lead time or price exceeds a threshold. The incident branch pauses expansion and invokes a tested investigation and notification playbook. Monthly checkpoints update evidence without rewriting scenario history, and an observation fitting no retained scenario returns the run to the uncertainty register rather than to the nearest existing story.

**Application Profile B, continuity planning for infrastructure and identity disruption**: A public-service operator must maintain essential functions through a disruption of shared infrastructure or identity services. Impact analysis identifies identity, intake, authorisation, communications, and audit evidence as essential capabilities. The scenario set contains a single-region outage, compromised identity administration, corrupted backups discovered during recovery, and a compound supplier outage combined with a disinformation campaign.

Because adaptive actors are present, the regime rule selects wargaming. Operations, security, legal, communications, and supplier representatives play their own roles while a separate red team controls adversary and rumour behaviour. Each turn records actions, reactions, counteractions, the evidence available at that moment, and the adjudication applied. The nominal failover plan succeeds in the region-outage future but fails when identity credentials are compromised, and fails again when backups cannot be trusted, which is exactly the vulnerability discovery of Step 4.3.

The robust portfolio introduces offline emergency identities with tightly limited privileges, immutable backup evidence, a manual essential-service mode, a second communications channel, supplier escalation agreements, and pre-approved public messaging. Constraint checking confirms that emergency staffing, segregation of duties, and recovery-time targets are simultaneously satisfiable. A dormant restoration branch cannot start until integrity verification passes; if verification fails, the manual-service sequel continues while clean recovery infrastructure is built. Signposts include identity-control anomalies, regional health status, backup-integrity test results, supplier response latency, and misinformation volume, each with a source, an owner, a persistence condition, an activation authority, and a maximum useful lead time. Periodic exercises sample different combinations and log detection, decision, activation, restoration, and rollback times. A scenario is retired only when its causal mechanism ceases to be plausible, never because one exercise succeeded.

**Application Profile C, safety evaluation programme for a multi-agent system**: A research team must choose an evaluation architecture for a system whose agents delegate tools and communicate across organisational boundaries. The objective is to detect unsafe coordination while preserving useful collaboration. The uncertainties include whether agents cooperate honestly, develop correlated errors, conceal intent, exploit a shared world-model flaw, lose access to a critical tool, or encounter an adversarial participant.

The regime is hybrid: a qualitative scenario set communicates the structural futures while a larger simulated ensemble supports vulnerability discovery. Scenarios vary communication topology, memory access, incentives, tool reliability, evaluator visibility, and adversary behaviour. A game-master component enforces environment rules and records actions while independent deterministic validators check tool permissions and safety constraints. Simulated agents are treated as hypothesis generators, never as representative samples of real users, in accordance with Exclusion 5.

Candidate safeguards include centralised approval, peer monitoring, independent critics, least-privilege tool tokens, communication limits, tripwires, immutable event logs, and a safe shutdown path. Parallel branches propose attack paths, a red team mutates prompts, topology, and hidden information, and repeated seeds reveal outcome variance. Strategies are scored on unsafe-action rate, task success, detection lead time, false intervention rate, recovery, and performance when simulator assumptions are perturbed. The analysis finds that majority debate improves ordinary errors but fails when agents share the same mistaken evidence, which is a correlated-scenario failure surfacing as a correlated-strategy failure. The selected portfolio therefore combines independent evidence channels, deterministic permission enforcement, cross-model review for high-impact actions, and human authorisation at defined thresholds. A tool-outage branch degrades to read-only work; a suspected-collusion branch freezes external actions while preserving evidence; and an out-of-envelope signal returns the system to scenario framing rather than asking the same agents to explain themselves. The orchestrator links every action to its scenario, strategy, policy, model, and trigger versions, and the plan is re-evaluated after model upgrades and protocol changes because prior simulation results do not automatically transfer.

**Adaptation across sectors**:

- **Strategy and investment decisions**: Scenario axes are built from market structure, regulation, technology substitution, and competitor response. The portfolio emphasises staged commitment and information deadlines, and the regret bound is expressed in the organisation's own value units.
- **Infrastructure, capacity, and supply-chain design**: Scenario axes are built from demand, input availability, price, and disruption. Hard constraints dominate, so Step 4.2 feasibility enforcement carries more weight than soft-criterion comparison, and options take the form of reserved capacity and qualified alternate sources.
- **Security, safety, and continuity planning**: Scenario axes are built from adversary capability, control failure, and dependency loss. Wargaming is mandatory because the adversary adapts, and playbook rehearsal coverage is the binding readiness metric.
- **Public policy and regulated programmes**: Scenario axes are built from legislative timing, institutional capacity, and public response. Recorded disagreement is a required output rather than a defect, and normative backcast scenarios are used where a statutory end state is fixed.
- **Research and evaluation programmes**: Scenario axes are built from method validity, participant behaviour, and instrument failure. Out-of-model validation is the binding metric, since the evaluation environment is itself a model.
- **Environmental and long-horizon adaptation**: Scenario axes are built from physical trajectory, mitigation response, and settlement pattern. Deep uncertainty is the default regime, so probability weighting is excluded and pathway plus signpost design carries the plan.
- **Agent and automation systems**: Scenario axes are built from tool reliability, policy change, counterpart behaviour, and environment drift. Trigger lead time relative to action lead time is the binding constraint, because agent action windows are short.

**Scale adaptation**:

- **Compact runs** (a single decision, horizon under 1 month): Retain 3 scenarios, 2 candidate strategies, and 1 trigger per scenario. Collapse Phase 4 into a single stress-testing pass, retain the feasibility enforcement rule, and retain all six record types in abbreviated form. Total effort should remain under 5% of the value at stake.
- **Standard runs** (a programme decision, horizon 3 to 24 months): Apply the full six-phase framework with 3 to 5 retained scenarios, 3 to 5 candidate strategies, and a rehearsed playbook per contingent action.
- **Large runs** (portfolio or institutional decisions, horizon beyond 24 months): Apply the hybrid regime with a qualitative core set for communication and a quantitative ensemble for vulnerability discovery. Where the retained scenario count would exceed 8, split the run into linked sub-runs by decision rather than expanding a single scenario set, and record the parent run identifier in each.
- **Continuous runs** (long-running agent workflows): Compress Phases 1 through 5 into a periodic replanning cycle and keep Phase 6 permanently active, with the refresh interval set shorter than the observe-decide-act time for the nearest irreversible action.

***

## V. Limitations and Considerations

**SBP does not reduce uncertainty**: The method exposes assumptions, reveals where strategies fail, reduces premature commitment, makes contingencies executable, and detects when a course change is warranted. It does not remove uncertainty, make surprises impossible, or prove that a plan will succeed. Mitigation: state the narrow operational promise in the decision contract, and measure the run by robustness, timeliness, traceability, and reversibility rather than by predictive accuracy.

**Coverage is bounded by imagination and evidence**: A scenario set can satisfy every coverage statistic in Step 2.3 and still omit the mechanism that actually occurs. The surprise test reduces this risk without eliminating it. Mitigation: retain the out-of-envelope routing rule in Step 6.2 as the primary defence, and treat an unmatched observation as a framing failure to be repaired rather than as noise to be absorbed.

**Model-derived evidence carries model-derived error**: Simulation, wargaming, and learned world models generate the bulk of the evaluation store in quantitative regimes, and a policy can score well by exploiting simulator error [39]. Mitigation: require out-of-model tests, holdout cases, historical replay, and real-world probes before any model-derived advantage enters the decision basis, and discount advantages that do not survive.

**Generated scenarios are not evidence about the world**: Language-model and multi-agent generation produce fluent, internally plausible futures whose distribution reflects prompts, models, and memories rather than reality. Mitigation: record generation provenance on every candidate, cap single-generator share, and validate consequential claims through independent channels before they inform a commitment.

**Probability is often unavailable and frequently faked**: Tools and templates create pressure to populate probability fields that no evidence supports, and probability-weighted expected value can conceal catastrophic outcomes. Mitigation: treat a status of not probability assessed as a valid and preferred value, and make an unjustified probability field a selection-halting defect rather than a stylistic concern.

**Robustness has a cost**: Hedges carry ongoing cost, options carry premiums and expiry, and reserves consume capital that a committed strategy would deploy. A portfolio that defers every commitment can underperform a decisive plan. Mitigation: assign an information deadline to every deferral, record carrying cost on every hedge and option, and compare the full process against a simpler baseline at closure.

**Adaptive control is only as good as its observability**: A trigger with no leading indicator, no owner, no authority, or no response window records history rather than controlling action. Mitigation: measure end-to-end lead time from rehearsal rather than estimating it, and escalate any trigger that cannot be made to lead its action as an accepted residual risk rather than carrying it as a control.

**Organisational and ethical exposure**: Scenario work surfaces disagreement, allocates blame implicitly through failure attribution, and can be used to legitimise a preferred conclusion by constructing a set that favours it. Mitigation: preserve recorded dissent in the decision record, keep the red team organisationally distinct from the strategy's authors, retain failed scenarios as evidence, and make the decision rule immutable from Step 1.1 so that it cannot be selected after the results are known. Where scenarios describe harms to identifiable groups, confidentiality and equity considerations apply to both the scenario content and its distribution.

**Process discipline is not decision quality**: A run can satisfy every checkpoint in Section III.B and still select a poor portfolio, because the checkpoints detect malformation rather than unsoundness. Mitigation: retain the process postmortem as an assessment separate from the outcome judgement, and treat a clean checkpoint record as a necessary condition rather than a sufficient one.

***

## VI. Conclusion and Summary

Scenario-Based Planning is a decision-architecture discipline before it is a scenario-writing exercise. Its value is created at three points: the decision contract that binds every future to a real choice, the stress-testing matrix that produces comparable evidence across all strategies and all scenarios, and the trigger design that converts a prepared branch into a control rather than a document. Everything else in the framework exists to protect those three points from degeneracy, explosion, false precision, and staleness.

The uncertainty-regime rule governs the whole method. A run that selects a method whose evidentiary preconditions are unmet will produce confident output from an unsupported basis, and no downstream discipline recovers from that. AI agents must therefore classify the regime before choosing the method, record the classification, and halt where no row of the selection rule matches the available evidence.

**Minimum production-readiness checklist**: Before a portfolio is released, AI agents confirm that the focal decision and acceptance thresholds are explicit; that hard constraints are separated from preferences; that uncertainty and assumption records are evidence-linked; that the scenario set is plausible, distinct, consistent, and decision-relevant; that every strategy was tested across every retained scenario; that probabilities are either justified or omitted; that vulnerabilities and residual risks are documented with dispositions; that core actions, hedges, options, branches, and safe states are authorised; that every trigger carries observable data, an owner, a lead time, and a rehearsed playbook; that branch plans are feasible and connected to orchestration; that model, prompt, seed, and adjudication versions are logged; that sensitivity and out-of-model checks are complete; that human escalation exists for ambiguous or high-impact decisions; and that refresh and closure rules are scheduled.

**Key Success Factors**:

- **Decision before narrative**: Scenario work opens with a consequential decision, a deadline, and controllable levers; without those, scenario generation produces awareness without control.
- **Regime before method**: The available quality of knowledge selects the method, and a method whose preconditions are unmet is never authorised by the sophistication of its tooling.
- **Uniform evaluation**: Every candidate strategy is evaluated against the same criteria in every retained scenario, with hard constraints enforced as infeasibility and raw evidence kept separate from judgement.
- **Portfolio over plan**: The output combines core actions, hedges, options, and contingent branches, optimising adaptability rather than nominal performance in a favoured future.
- **Triggers that lead**: Every trigger carries an observable source, an owner, an authority, a measured lead time exceeding its action lead time, and a rehearsed playbook.
- **Versioned history**: Scenarios, assumptions, models, evaluations, and decisions are versioned rather than overwritten, and failed scenarios are preserved as evidence rather than deleted.

The final operating rule is to plan for several futures without attempting to predict all of them: use scenarios to find what breaks, choose actions that remain acceptable across the relevant set, preserve the ability to change course, watch the world for evidence, and rebuild the plan when the world no longer fits the model. By following this framework, AI agents can produce decision architectures whose quality is measured not by the elegance of their narratives but by the robustness, timeliness, traceability, and reversibility of the decisions they enable.

***

## VII. References and Further Reading

This guide is a derived operational restructuring of a single originating prose document. The external references listed below are transcribed from that originating prose guide, with titles and locators reproduced as that guide recorded them. They have not been independently re-verified during conversion, and no reference entry is included that the originating document's evidence base does not support.

**Originating document**:

1. `Scenario-Based Planning: An Operational Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the uncertainty-regime rule, the seventeen-step workflow, the scenario architecture and budget discipline, the strategy component taxonomy, the robustness and regret measures, the vulnerability-discovery loop, the signpost and trigger playbook design, the six logging record types, the seven metric families, the failure-mode catalogue, and the three worked applications reproduced in Section IV.

**Related guides in this corpus**:

2. `advanced_task_guides/planning/guide_MetaReasoning.md` — the pattern that decides whether scenario work is warranted, which scenario method to invoke, and when to stop generating. Governs the Step 2.1 budget declaration from outside this framework.
3. `advanced_task_guides/planning/guide_HierarchicalTaskNetworkPlanning.md` — the decomposition method that converts a selected branch into primitive task sequences in Step 5.3.
4. `advanced_task_guides/planning/guide_TaskManagementOrchestration.md` — the runtime layer that executes the active branch, holds task state, and records actual outcomes for Phase 6.
5. `advanced_task_guides/planning/guide_WorldModelSimulationPlanning.md` — the evaluation mechanism used inside Step 4.1 where actions alter a stateful environment.
6. `advanced_task_guides/planning/guide_PlanTodoRecitation.md` — the context-salience mechanism referenced in Section III.A, which supports but never replaces the persistent record architecture.
7. `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — relevant to the observability constraints that bound signpost selection in Step 5.2.
8. `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — relevant to the data-source, latency, and missingness fields of the trigger and execution record.
9. `advanced_task_guides/policy-risk/guide_SystemSpecificRiskAssessment.md` — relevant to the risk-class and residual-risk fields of the decision record.
10. `advanced_task_guides/research-analysis/guide_TemporalEvolutionAnalysisandForecasting.md` — relevant to the reference-forecast handling in Step 1.2 and to the distinction between forecasting and scenario construction in Section 1.2.
11. `advanced_task_guides/research-analysis/guide_BarrierAnalysis.md` — relevant to the control-failure scenario axes described for security, safety, and continuity applications in Section IV.
12. `advanced_task_guides/authoring/guide_guidewriting.md` — the house-style specification governing the structure, register, and conformance envelope of this document.

**External references, scenario planning origins and method statements**:

13. Shell Scenarios — https://www.shell.com/news-and-insights/scenarios.html
14. Galison’s history of scenario futures — https://projects.iq.harvard.edu/files/andrewhsmith/files/galison_futureofscenarios.pdf
15. Wack, “Scenarios: Uncharted Waters Ahead” — https://wiki.santafe.edu/images/d/d9/Wack.pdf
16. WIPO’s catalog record for *The Art of the Long View* — https://tind.wipo.int/record/22383
17. method summary — https://www.charactertowns.org/wp-content/uploads/2024/01/BR-The-Art-of-the-Long-View-8.26.14.pdf
18. Schoemaker, “Scenario Planning: A Tool for Strategic Thinking” — https://sloanreview.mit.edu/article/scenario-planning-a-tool-for-strategic-thinking/

**External references, method boundaries and contingency planning**:

19. RAND’s RDM guide — https://www.rand.org/pubs/tools/TL320/tool/robust-decision-making.html
20. NIST SP 800-34 Rev. 1 — https://csrc.nist.gov/pubs/sp/800/34/r1/upd1/final

**External references, uncertainty regimes and generation methods**:

21. Shell’s scenario history — https://www.shell.com/news-and-insights/scenarios/what-are-the-previous-shell-scenarios.html
22. OpenLearn’s introduction to decision trees under uncertainty — https://www.open.edu/openlearn/money-business/decision-trees-and-dealing-uncertainty/content-section-4.1
23. NIST Monte Carlo Tool — https://www.nist.gov/services-resources/software/monte-carlo-tool
24. RAND scenario discovery — https://www.rand.org/pubs/external_publications/EP201000192.html
25. UK Defence Wargaming Handbook — https://www.gov.uk/government/publications/defence-wargaming-handbook
26. U.S. Army Applied Critical Thinking Handbook — https://www.benning.army.mil/CFDP_INST_HW/content/2E%20Applied%20Critical%20Thinking%20Handbook%20v8%201_Sep'16.pdf
27. World Models — https://arxiv.org/abs/1803.10122
28. MuZero — https://www.nature.com/articles/s41586-020-03051-4

**External references, applicability conditions and exclusions**:

29. RAND’s Monterrey water-planning case — https://www.rand.org/pubs/tools/TL320/tool/case-studies/monterrey.html
30. Tree of Thoughts — https://arxiv.org/abs/2305.10601
31. Generative Agents — https://arxiv.org/abs/2304.03442
32. Concordia — https://deepmind.google/research/publications/64717/

**External references, generation, stress testing, and vulnerability discovery**:

33. LangGraph Graph API — https://docs.langchain.com/oss/python/langgraph/graph-api
34. AutoGen multi-agent debate — https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/multi-agent-debate.html
35. Joint planning and design guidance — https://www.jcs.mil/Portals/36/Documents/Doctrine/fp/design_and_planning_fp.pdf
36. RAND Scenario Discovery Tool — https://www.rand.org/pubs/tools/TL320/tool/scenario-discovery-tool.html

**External references, signposts, triggers, and continuity standards**:

37. FEMA Continuity Guidance Circular — https://www.fema.gov/sites/default/files/documents/fema_continuity-guidance-circular_082024.pdf
38. ISO 22301 — https://www.iso.org/standard/75106.html

**External references, model fidelity and failure modes**:

39. Model-Based Reinforcement Learning survey — https://arxiv.org/pdf/2206.09328.pdf

