# Reflective Monte Carlo Tree Search

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Reflective Monte Carlo tree search constitutes the task family of allocating bounded test-time computation across an explicit tree of environment states, and of converting the search's own prediction errors into scoped lessons that condition later action proposal and state evaluation. This guide provides AI agents with a structured protocol covering six phases: gating the method against cheaper baselines under an explicit node budget; specifying the canonical state, the value representation, and the lesson store; running the selection, expansion, simulation, and backpropagation loop under bounded expansion; obtaining and calibrating value estimates where no trained value network exists; capturing and applying scoped reflections; and committing one externally verified action under contamination-controlled evaluation. It partitions every phase across a deterministic tier that owns the tree, the visit counts, the selection arithmetic, the budget ledger, lesson storage, and scope matching, and a model tier that owns action proposal, state evaluation, and reflection generation. It fixes three authority rules: a value estimate is a proposal that orders search and never authorises a release, a lesson is retrievable only where it names the conditions under which it applies, and an evaluation reusing a warm lesson store measures the store rather than the method.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Reflective Monte Carlo tree search**: A search architecture that repeats selection, expansion, simulation, and backpropagation over an explicit tree, and additionally attributes prediction errors to a policy or value failure, writes a scoped lesson recording the attribution, and retrieves that lesson into later policy and value calls. The reflection loop is what distinguishes it from Monte Carlo tree search; the tree bookkeeping is unchanged.

**Canonical state**: The normalised, sufficient representation of what is known and decided at a point in the search, carrying facts, constraints, resources, permissions, and evidence references and nothing else. The term is adopted from the corpus tree-of-thought guide and carries the same meaning here.

**State identity hash**: A deterministic hash over the canonical state payload, used for exact duplicate detection and for transposition lookup. Conversation transcripts are never used as state identity.

**Node**: One state instance in the tree, carrying identity, depth, lineage, visit count, backed-up value statistics, cost, disposition, and reason codes.

**Edge**: One applied action linking a parent node to a child node, carrying the structured action record, the validator verdict, the policy prior, the immediate reward, the side-effect class, and any observation link.

**Visit count**: The number of completed rollouts whose backup path traversed a node or edge. Visit counts are integers maintained by the deterministic tier and are never produced, estimated, or adjusted by a model.

**Backed-up value**: The running sum, mean, variance, minimum, and maximum of returns propagated through a node from completed rollouts. The mean is the exploitation term of the selection rule.

**Selection rule**: The deterministic arithmetic choosing which child to descend to at each level. Two forms are in scope. The upper-confidence form adds to a child's normalised mean value an exploration term equal to the exploration constant multiplied by the square root of the natural logarithm of parent visits divided by child visits. The prior-guided form adds to the mean value an exploration term equal to the exploration constant multiplied by the child's policy prior multiplied by the square root of parent visits divided by one plus child visits.

**Exploration constant**: The scalar weighting the exploration term against the exploitation term, tuned on reward-normalised held-out episodes and stress-tested across seeds. It is meaningful only after rewards are normalised to a declared bounded interval.

**Policy prior**: A normalised score over a node's candidate actions supplied by the generator, used only as the prior factor of the prior-guided selection rule. A prior orders candidates; it never removes an action permanently.

**Progressive widening**: The rule permitting the number of admitted children at a node to grow sublinearly with that node's visit count, rather than enumerating every legal action. Double progressive widening applies the same bound to distinct stochastic successor states of one action.

**Rollout**: One simulated trajectory from a newly expanded child to a terminal state, a depth bound, an unsafe transition, or a value boundary. A rollout occurs inside a forked simulator or replay fixture and never executes an irreversible action.

**Backpropagation**: Propagation of a terminal reward or a calibrated leaf value along the path traversed by one completed rollout, updating visit counts and value statistics exactly once per rollout per node.

**Layered evaluator**: The composite that produces a leaf value: deterministic checks first, a model-produced scalar for residual criteria no deterministic check covers, and an uncertainty-triggered adversarial evaluation stage. Its construction and admission bar are owned by the corpus tree-of-thought guide.

**Value estimate**: A bounded scalar proposal about a state's promise, produced by the layered evaluator. It is a proposal, not a measurement: it orders the frontier and weights backup, and it authorises nothing.

**Terminal verifier**: An external check deciding whether a candidate result is correct or acceptable. It shares neither weights nor prompt with the generator or the evaluator, and it alone authorises a success exit.

**Surprise trigger**: A declared condition under which reflection is permitted to run: a confident prediction followed by failure, an unexpected success, divergence between sibling backed-up values above a declared threshold, a terminal verifier rejection, or a repeated error signature.

**Reflection record**: The structured artifact a reflection call produces, carrying a situation signature, task scope, triggering prediction, attempted action, expected observation, actual trusted observation, error type, sibling or later-action contrast, the lesson text, evidence references, confidence, model and prompt versions, creation time, expiry, permitted trust domains, and validation status.

**Lesson**: The actionable clause inside a reflection record, stating what to prefer or avoid and under which conditions. A lesson that does not name its conditions is malformed and is rejected at write time.

**Lesson scope**: The predicate set restricting where a lesson may be retrieved: state signature class, task family, environment and tool schema version, model and prompt version, and trust domain. Scope matching is deterministic and precedes any similarity ranking.

**Lesson store**: The versioned, tenant-partitioned repository holding validated reflection records at one of three scope tiers: episode-local, task-family, or global.

**Hypothesis status**: The status of a lesson derived from a failure with no successful comparator. A hypothesis lesson is confined to episode-local scope and is never retrievable outside the episode that produced it.

**Warm store**: A lesson store carrying lessons produced by tasks that overlap the evaluation set. Measurements taken against a warm store describe the store, not the method.

**Node budget**: The declared caps for one episode on generated nodes, expanded nodes, rollouts, depth, children per node, reflections, memory reads and writes, model calls, tool calls, tokens, environment steps, wall time, concurrency, and currency cost. Every dimension carries a numeric limit; an unbounded dimension blocks execution.

**Marginal search yield**: Additional externally verified successes obtained over the cheapest adequate baseline, divided by the additional tokens, currency, or seconds consumed. Non-positive marginal search yield withdraws the justification for the method.

**Transposition**: Reuse of an existing node's statistics for a newly reached state carrying the same identity hash. Merging is permitted only where environment version, permissions, evidence, and side-effect history also match.

**Virtual loss**: A temporary penalty applied to a leased path so that concurrent workers do not select it simultaneously. Virtual loss is scheduling pressure and is never recorded as reward evidence.

**Reason code**: A normalised categorical label recorded with every expansion refusal, prune, invalidation, reflection write, retrieval rejection, and termination event, drawn from a closed vocabulary. The term is adopted from the corpus meta-reasoning guide.

**Exit condition**: A declared terminal state that alone may end a search: verified success, exhausted frontier, budget exhaustion, stagnation, safety violation, or escalation to a human role.

### 1.2 Execution Tier Partition and Authority Rules

The method's reliability comes from keeping the tree out of the model. The partition below is binding on every phase of Section II, and every step names the tier that owns it.

**Deterministic tier**: The tree data structure and its node and edge records; state canonicalisation, identity hashing, exact deduplication, and transposition lookup; the legal-transition validator; visit counts and all backed-up value statistics; the selection rule arithmetic; the progressive-widening allowance; the budget ledger and enforcement of every cap; lease and virtual-loss management; lesson storage, scope predicate evaluation, expiry, and retrieval admission; the stopping rule; the authorisation gate on committed actions; and every verifier for which a deterministic oracle exists.

**Model tier**: Proposal of candidate actions conditioned on the canonical state, the legal-action schema, the remaining budget, and any retrieved lessons; estimation of state value for residual criteria no deterministic check covers; generation of reflection text from a reconstructed contrast; and construction of the natural-language response from an already verified result.

**Hybrid tier**: The model proposes an action and the transition validator accepts or rejects it, and the validator holds authority. The model produces a leaf value and the controller uses it as a backup input and an ordering key, and the controller holds authority over whether resources are spent. The model writes a lesson and the store's schema and scope validator decides whether it is admitted, and the validator holds authority. The model claims a state is terminal and the terminal verifier adjudicates, and the verifier holds authority.

**Execution Tier Ownership**:

| Artifact or decision | Owning tier | Authority on disagreement |
| :-- | :-- | :-- |
| Candidate action text and policy prior | Model | Proposes only; no authority |
| Legality and canonical form of a transition | Deterministic | Validator rejects; the proposal is discarded |
| Node identity, duplicate status, transposition | Deterministic | Hash decides; prose similarity never overrides |
| Visit counts and backed-up value statistics | Deterministic | Computed from completed rollouts only |
| Leaf value estimate | Model | Orders search and weights backup; authorises nothing |
| Selection rule arithmetic and next descent | Deterministic | Controller decides using the estimate as a key |
| Progressive-widening allowance | Deterministic | Allowance binds regardless of proposal quality |
| Budget decrement and cap enforcement | Deterministic | Ledger halts the run regardless of promise |
| Reflection text | Model | Proposes only; admission is validated |
| Lesson scope match and retrieval admission | Deterministic | Predicate decides; embedding similarity never overrides |
| Terminal claim and answer release | Hybrid | Verifier authorises; value estimate is not evidence |
| Stopping decision | Deterministic | Stopping rule fires irrespective of remaining promise |

**Three authority rules govern the whole method.** First, a value estimate never authorises an answer: authorisation requires external verification of the selected result by a component sharing neither weights nor prompt with the generator or the evaluator, and a search that terminates without such verification returns a best-so-far result with its limiting condition rather than a confident answer. Second, a retrieved lesson may condition generation and valuation and may never modify system instructions, tool definitions, budgets, acceptance tests, or access rights. Third, budget exhaustion is a declared exit, not a signal to relax a cap.

### 1.3 Agent-Layer Scope and the Boundary Against Sibling Guides

**Declared re-scoping of the offline learning stage**: The originating prose source presents nine workflow steps, of which eight run at inference time and one does not. That one describes an outer exploratory-learning loop that collects completed episodes, filters them, and trains or fine-tunes candidate policy, value, or retrieval components on the resulting corpus before promoting them behind an offline gate. The source itself classifies that stage as search distillation rather than inference-time reflective search. Training foundation model weights sits below the AI Agent layer: an agent cannot perform it through prompting, tool calls, filesystem operations, or sub-agent orchestration at runtime. That stage is therefore out of scope for this guide, and no phase below instructs an agent to train, fine-tune, distil, or edit model weights. The agent-layer surrogate for the same objective is the lesson store specified in Phase 2 and Phase 5: a versioned, scoped, expiring memory that conditions policy and value prompts at inference time and achieves error reduction without touching weights. Deployments that additionally run the offline stage must treat it as a separate machine-learning workflow with its own promotion gate and its own held-out evaluation, and must never let a newly trained component label its own promotion set.

**Boundary against the corpus tree-of-thought guide**: That guide owns evaluator construction, the four-threshold evaluator admission bar, evaluator calibration procedure, hard and soft pruning with reason codes, the diversity reserve, backtracking and reinstatement, and bounded expansion under a declared branching factor. This guide does not re-derive any of them. It requires that the evaluator admitted under that bar is the same evaluator supplying leaf values here, and it adds only what Monte Carlo allocation introduces: visit counts, the selection rule, backup of returns along a path, progressive widening as a visit-dependent generalisation of a fixed branching factor, and calibration of a leaf estimate against the return that is eventually backed up through it.

**Boundary against the corpus meta-reasoning guide**: That guide owns value-of-computation control, the entry gate deciding whether deliberate search is warranted at all, the control transitions, and the stopping decision at the meta level. This guide specifies the search once that gate has returned invoke, and its stopping rule in Step 6.1 is the object-level instance of that meta-level decision. The terms decision contract, budget ledger, reason code, exit condition, stuck state, and correlated failure are adopted from it unchanged.

**Boundary against episodic retry patterns**: Verbal reflection over whole episodes without a tree, visit counts, confidence bounds, or value backup is a distinct method. It applies where complete attempts are cheap and sequential retry suffices. This method applies where within-decision resource allocation and prefix reuse matter, and where a partial state is informative before any complete attempt exists.

### 1.4 Entry Gates and the Cost-Justification Bar

This is the most expensive method in the reasoning family. The originating source reports a published evaluation in which reflective search consumed 7.4, 9.7, and 10.1 times the tokens of a single-trajectory baseline on three web-task subsets, for absolute success gains of 12.4, 14.9, and 9.1 percentage points [1]. That multiplier is recoverable only where partial states are informative, prefixes are reusable, and an external signal can distinguish progress. Agents must run five gates before any node is created, each returning a logged verdict with a reason code. A failed gate routes to the named cheaper or safer alternative; it never widens the tree.

**Search-Need Gate**: Passes where several actions carry delayed consequences, revisiting a prefix is informative, failures teach reusable distinctions, and calibrated value or terminal verification exists. Fails for linear derivations, fixed-schema extraction, single-lookup retrieval, and any task a deterministic routine already closes.

**Simulator Gate**: Passes only where rollouts run against replay fixtures, a snapshot-capable sandbox, or a symbolic model supporting snapshot, fork, restore, and deterministic seeding. Fails for any transition whose effects cannot be undone by discarding a node, including messages, orders, payments, grants, publications, production writes, and consumption of a scarce resource. On failure, search over non-executing proposals only and authorise at most one real action afterward.

**Value Gate**: Passes only where the evaluator meets the admission bar of the corpus tree-of-thought guide on held-out data and an external terminal verifier exists. Intrinsic self-critique does not satisfy this gate; the source reports experiments in which language models often failed to correct reasoning without external feedback and degraded initially correct responses [2].

**Reflection Gate**: Passes only where retrieved lessons improve policy or value ranking on a quarantined evaluation set by at least 3 percentage points at matched budget. Where the gate fails, run the search without retrieval and record the verdict; reflection is an addition that must pay for itself, not a default.

**Budget Gate**: Passes only where the cost-justification inequality in Step 1.2 holds on a paired, budget-matched comparison against both named baselines, and where every cap in the node budget carries a numeric limit. Any episode whose worst-case authorised spend exceeds the decision contract is refused rather than started.

**Gate Routing Table**:

| Observed condition | Failing gate | Route |
| :-- | :-- | :-- |
| Task is linear and the first answer passes the verifier | Search-Need | Single chain with external verification |
| Complete attempts are cheap and answers are normalisable | Search-Need | Self-consistency over independent samples |
| Partial scores are stable and prefixes are not reused | Search-Need | Tree-of-thought beam search |
| No snapshot, fork, or restore capability exists | Simulator | Proposal-only planning, then one authorised action |
| Evaluator below the admission bar | Value | Independent sampling with external verification, or abstain |
| No external terminal verifier exists | Value | Abstain or escalate to a human role |
| Retrieved lessons yield below 3 points on held-out tasks | Reflection | Run the search with retrieval disabled |
| Verified margin over the best baseline below 5 points | Budget | Adopt the cheaper baseline |
| Worst-case spend exceeds the decision contract | Budget | Reduce caps and re-run the comparison, or refuse |

**Numeric gate rules**: Invoke the method only where all five gates pass. Where fewer than 2 genuinely distinct legal actions exist at the root, suppress and run a single chain, because a tree of width 1 is a chain at search overhead. Where controller, evaluation, and reflection overhead is estimated above 40 percent of total episode cost and the task sits in the lowest risk tier, suppress and record the estimate for the next policy revision.

***

## II. Operational Framework: Reflection-Conditioned Tree Search Under a Fixed Node Budget

The framework assumes the five gates of Section 1.4 have all returned pass. Phases 3 through 5 form the inner loop: Phase 3 runs one search iteration, Phase 5 runs at most the declared number of reflections triggered by that iteration, and control returns to Phase 3 until a stopping condition fires. Phase 6 commits one action, advances the root, and closes the episode under contamination-controlled measurement.

### Phase 1: Applicability Gating and Cost Justification Against Baselines

**Objective**: Establish the decision contract, prove on paired budget-matched evidence that reflective search outperforms the cheaper named baselines, and fix every cap before any node exists.

#### Step 1.1: Establish the Decision Contract and the Node Budget Ledger

**Required Actions**:

- State the objective, the acceptance tests, the evidence standard, and the risk class so an automated validator or a named human role can evaluate them without interpretation.
- Enumerate the legal action classes and mark each as reversible, reversible under compensation, or irreversible, and record which classes the episode is authorised to commit.
- Name the external terminal verifier, its independence from the generator and evaluator, and the partial-result policy applied when it rejects every candidate.
- Populate the node budget ledger with a numeric limit for each of the 14 dimensions named in Section 1.1, and refuse the episode where any dimension is unbounded.
- Reserve worst-case spend against every dimension before dispatching any work, and reject work whose reservation would exceed a remaining allowance.

**Required Outputs**:

- A decision contract record carrying objective, acceptance tests, evidence standard, risk class, and abstention policy.
- An action-class inventory with a reversibility label and an authorisation flag per class.
- A node budget ledger with 14 numeric limits and a reservation column.

**Quality Checkpoints**:

- Every acceptance test returns pass or fail without interpretation; an untestable criterion halts the episode before any node is created.
- Every budget dimension carries a numeric limit; an unbounded dimension blocks execution.
- The terminal verifier shares neither weights nor prompt with the generator or the evaluator; shared provenance fails the Value Gate.

***

#### Step 1.2: Run the Baseline Ladder and Test the Cost-Justification Inequality

**Required Actions**:

- Run the baseline ladder in ascending cost order on at least 30 held-out tasks from the deployment distribution: a deterministic or direct solution, a single chain with external verification, self-consistency over independent samples with external selection, and tree-of-thought beam search under the corpus tree-of-thought guide.
- Record for each rung the externally verified success rate, the median and 90th-percentile token cost, the tool-call count, and the wall-clock latency.
- Run reflective search at a budget matched to the most expensive baseline rung, using an identical task set, an identical verifier, and at least 5 preregistered seeds.
- Compute marginal search yield as additional verified successes over the best baseline rung divided by additional tokens, currency, and seconds, reported separately for each denominator.
- Record the cost multiplier of reflective search over each baseline rung, so the comparison states both the gain and its price.

**Required Outputs**:

- A baseline ladder record with verified success, cost, and latency per rung.
- A budget-matched comparison record for reflective search across at least 5 seeds.
- A marginal search yield figure per cost denominator, with its sign.

**Quality Checkpoints**:

- The verified success margin of reflective search over the best baseline rung is at least 5 percentage points at matched budget; below that margin the Budget Gate fails and the cheaper rung is adopted.
- Marginal search yield is positive on every cost denominator; a non-positive figure on any denominator withdraws the justification for the method.
- The comparison uses the same verifier and the same task set for every rung; a comparison across differing verifiers is discarded and re-run.

***

#### Step 1.3: Record the Gate Verdicts and the Search Hypothesis

**Required Actions**:

- Record each of the five gate verdicts with its reason code, its measured evidence, and the route taken on failure.
- State the search hypothesis in one sentence naming the reversible branch structure, the delayed reward, or the repeatable error class that the tree is expected to exploit.
- State the condition under which the method is not justified for this task class, expressed as a numeric threshold on verified margin, on marginal search yield, or on simulator fidelity.
- Declare the reflection policy for the episode: the surprise triggers admitted, the per-iteration reflection cap, the retrieval top-k cap, and the scope tiers readable and writable.
- Declare the evaluation mode that will be used to measure this configuration, choosing cold-store, frozen-store, or paired enable-and-withhold as specified in Step 6.3.

**Required Outputs**:

- A gate verdict record with 5 entries, each carrying evidence and a reason code.
- A one-sentence search hypothesis naming the structure the tree exploits.
- A declared non-justification condition with a numeric threshold.
- A reflection policy record and a declared evaluation mode.

**Quality Checkpoints**:

- All 5 gate verdicts are recorded before the root node is created; a missing verdict blocks initialisation.
- The search hypothesis names a structural property of the task, not a general expectation that more computation helps.
- The reflection policy caps per-iteration reflections at no more than 3 and retrieval at no more than 2 records, above which reflection cost grows faster than its measured benefit.

***

### Phase 2: Tree, Value, and Lesson Store Specification

**Objective**: Compile a search specification a deterministic component can execute without a model, and a lesson store whose every record carries a scope predicate and an expiry.

#### Step 2.1: Define the Canonical State, the Legal-Action Schema, and the Transition Layer

**Required Actions**:

- Define the canonical state payload, its normalisation rules, and the identity hash computed over it, excluding conversational phrasing and any field that does not change what may legally happen next.
- Define the legal-action schema as structured records with typed arguments, and define the validator that accepts, canonicalises, or rejects a proposed action with a reason code.
- Define the transition function, the terminal test, the transposition rule, and the conditions under which two nodes with equal hashes may share statistics.
- Define the snapshot, fork, restore, and deterministic seed operations the simulator must expose, and the versioned identifier recorded with every rollout.
- Dry-run the specification on at least 10 recorded episodes, confirming that a state can be forked, advanced, tested, restored, and compared without invoking a model.

**Required Outputs**:

- A canonical state schema with a normalisation rule per field and a stated identity hash.
- A legal-action schema with typed arguments, a validator, and a closed rejection reason vocabulary.
- A transition, terminal, and transposition specification with a merge predicate.
- A dry-run record covering at least 10 episodes with no model invocation.

**Quality Checkpoints**:

- The dry-run completes for 10 of 10 episodes with zero model calls; any model dependency in the transition layer blocks the phase.
- The transposition merge predicate compares environment version, permissions, evidence set, and side-effect history; merging on state hash alone is a defect that blocks the phase.
- No field excluded from the canonical payload can change which actions are legal; a counterexample returns the schema to redefinition.

***

#### Step 2.2: Specify the Value Representation and the Node Statistic Set

**Required Actions**:

- Separate four quantities and forbid their conflation: an outcome reward scored by the terminal verifier, a process value estimating contribution toward success, a policy prior over candidate actions, and an authorisation decision made outside the model.
- Normalise every reward and value to the closed interval from 0 to 1, and declare the perspective, the discount factor, terminal bonuses, penalties, and the backup rule before any rollout runs.
- Declare the node statistic set maintained by the deterministic tier: visit count, virtual loss, reward sum, mean, variance, minimum, maximum, prior mass, admitted children, widening allowance, uncertainty, and disposition.
- Record hard validity separately from scalar value, so an invalid state is never represented as a low-scoring valid one.
- Declare the exploration constant, the widening coefficient, and the widening exponent, and record the held-out episode set on which the exploration constant was tuned after reward normalisation.

**Required Outputs**:

- A four-quantity separation record naming the owner and the authority of each quantity.
- A normalised reward specification with interval, discount, bonuses, penalties, and backup rule.
- A node statistic schema with 12 named fields.
- A declared exploration constant, widening coefficient, and widening exponent with a tuning record.

**Quality Checkpoints**:

- Only the terminal verifier may declare success; a process value or a leaf estimate that authorises release is a design defect that blocks the phase.
- Every reward and value falls within the declared bounded interval; an out-of-interval figure halts backup and quarantines the rollout.
- The exploration constant was tuned after reward normalisation on held-out episodes; a constant carried over from an unnormalised reward scale is rejected.

***

#### Step 2.3: Specify the Reflection Record Schema and the Lesson Store Partition

**Required Actions**:

- Define the reflection record schema with every field required for scope matching, validation, expiry, and audit, rejecting at write time any record missing a scope predicate or an expiry.
- Partition the store into policy memory, value memory, and environment memory, and hold safety policy outside all three as governed configuration that no reflection may write.
- Partition the store by tenant and trust domain, and forbid retrieval across a tenant or security boundary under every configuration.
- Define the three scope tiers and their promotion rules: episode-local by default, task-family after at least 3 independent supporting observations from distinct episodes, and global only after offline human review.
- Define the default expiry as 30 days from creation, and define immediate invalidation on any change to the environment version, tool schema, model version, prompt version, reward definition, or authorisation policy named in the record.

**Reflection Record Schema**:

```
REFLECTION_ID:
TRIGGER_TYPE:                 confident_failure | unexpected_success |
                              sibling_divergence | verifier_rejection | repeated_error
TARGET:                       policy | value
SITUATION_SIGNATURE:          canonical state signature class
SCOPE_TASK_FAMILY:
SCOPE_ENVIRONMENT_VERSION:
SCOPE_TOOL_SCHEMA_VERSION:
SCOPE_MODEL_AND_PROMPT_VERSION:
SCOPE_TRUST_DOMAIN:
TRIGGERING_PREDICTION:
ATTEMPTED_ACTION:
EXPECTED_OBSERVATION:
ACTUAL_TRUSTED_OBSERVATION:
ERROR_TYPE:
CONTRAST_REFERENCE:           sibling node id | later successful action id | NONE
LESSON_TEXT:                  conditional clause naming when it applies
EVIDENCE_IDS:
CONFIDENCE:                   0.00 to 1.00
STATUS:                       hypothesis | validated | contradicted | expired
SCOPE_TIER:                   episode | task_family | global
CREATED_AT:
EXPIRES_AT:
RETRIEVAL_COUNT:
MEASURED_UTILITY:
CONTRADICTION_LINKS:
```

**Required Outputs**:

- A reflection record schema with a write-time validator enforcing every mandatory field.
- A store partition specification covering memory type, tenant, and trust domain.
- A promotion rule set with numeric support thresholds per scope tier.
- An expiry and invalidation policy keyed to 6 named version fields.

**Quality Checkpoints**:

- A record whose contrast reference is NONE carries hypothesis status and episode scope tier; any other combination is rejected at write time.
- A record with no expiry timestamp is rejected at write time; there is no permanent lesson.
- No reflection record may write to safety policy, tool definitions, budgets, or acceptance tests; a schema permitting it blocks the phase.

***

### Phase 3: The Four-Phase Search Loop Under Bounded Expansion

**Objective**: Advance the tree by exactly one iteration of selection, expansion, simulation, and backpropagation, leaving every statistic updated exactly once and every cap decremented atomically.

#### Step 3.1: Select a Leaf by the Deterministic Exploration-Exploitation Rule

**Required Actions**:

- Refuse to begin the iteration unless no root child has met the acceptance rule, the frontier is non-empty, and every ledger dimension retains allowance for the worst-case cost of one iteration.
- Descend from the root by evaluating the declared selection rule at each level, computing the exploitation term from backed-up statistics and the exploration term from visit counts, never from a model call issued during descent.
- Prioritise unvisited legal children over the rule's arithmetic, so that each admitted action receives at least 1 rollout before any sibling receives a second.
- Skip terminal, invalid, superseded, over-depth, and currently leased nodes, recording a reason code for each skip.
- Apply a lease and a virtual loss to the selected path before dispatch, so concurrent workers descend to distinct leaves.

**Attribution of the selection rules**: The upper-confidence bound rule originated with Auer, Cesa-Bianchi, and Fischer as a bandit algorithm attaining logarithmic regret for bounded rewards [4]; its recursive application to planning trees, and the consistency result for finite-horizon and discounted planning, are due to Kocsis and Szepesvári [5]. The prior-guided form replacing uninformed expansion with a policy prior and a learned leaf evaluation belongs to the policy-and-value-guided family [6]. The four-phase decomposition and its variant family are organised in the Browne survey [3]. Agents must not attribute the bandit rule to the planning-tree authors, and must not present the prior-guided form as requiring a trained value network in an agent deployment.

**Required Outputs**:

- One selected leaf node with its full descent path recorded.
- A per-level selection record carrying exploitation term, exploration term, and chosen child.
- A lease record with owner, expiry, and the virtual loss applied to each path edge.

**Quality Checkpoints**:

- Every unvisited legal child at a descended node receives a rollout before any sibling receives a second; a violation indicates the prioritisation rule was bypassed.
- No model call was issued during descent; a model call in the selection path is a tier violation that quarantines the iteration.
- Every skipped node carries a reason code from the closed vocabulary; an uncoded skip fails the iteration.

***

#### Step 3.2: Expand Within the Progressive-Widening Allowance

**Required Actions**:

- Compute the widening allowance for the selected node as the widening coefficient multiplied by the node's visit count raised to the widening exponent, rounded down, and expand only where admitted children fall below that allowance [7].
- Request candidate actions from the generator conditioned on the canonical state, the legal-action schema, the remaining budget, and at most the declared number of retrieved lessons.
- Parse, authorise, canonicalise, and validate every candidate, rejecting illegal, duplicate, no-op, and unauthorised proposals with reason codes and never counting a rejected candidate against the widening allowance as an admitted child.
- Admit the surviving candidates as children with their policy priors recorded, and preserve an exploration floor so that no legal action class is permanently excluded by a low prior.
- Mark the node exhausted when no legal unique child remains, and return control to selection rather than widening past the allowance.

**Required Outputs**:

- A set of admitted child nodes with edges, structured action records, and policy priors.
- A rejection record listing every discarded candidate with its reason code.
- An updated widening allowance and admitted-child count for the expanded node.

**Quality Checkpoints**:

- Admitted children never exceed the computed widening allowance; an overflow halts expansion and quarantines the node.
- Every admitted action passed typed argument validation and authorisation independently of its policy prior; a prior never substitutes for validation.
- The exploration floor retains at least 1 candidate from each legal action class present at the node across the episode, so a low prior demotes rather than deletes.

***

#### Step 3.3: Simulate to a Value Boundary and Backpropagate the Return

**Required Actions**:

- Restore the child snapshot and set the declared seed before every rollout, so alternative rollouts from one child differ only by the intended variation.
- Simulate inside the fork until a terminal state, the rollout depth cap, an unsafe transition, a model uncertainty threshold, or the value-estimation boundary is reached, and never execute an irreversible tool during simulation.
- End simulation at any proposed irreversible action and value the resulting state from pre-execution evidence, never from an imagined successful outcome.
- Obtain a terminal reward from the deterministic verifier where a terminal state was reached, and otherwise obtain a bounded leaf value from the layered evaluator specified in Phase 4.
- Backpropagate the return along the recorded path exactly once per completed rollout, updating visits, sum, mean, variance, minimum, and maximum, then release the virtual loss and the lease.

**Required Outputs**:

- A rollout record carrying path, leaf, seed, simulator version, stop reason, transition provenance, and cost.
- A backup record naming every node updated and the return applied.
- A released lease and a cleared virtual loss for every edge on the path.

**Quality Checkpoints**:

- Every rollout record labels each transition as model-simulated, fixture-replayed, sandbox-executed, or real; an unlabelled transition quarantines the rollout and blocks its backup.
- Each node on the path is updated exactly once per completed rollout; a double update invalidates the iteration and triggers statistic recomputation from the rollout log.
- Recovery from a worker failure removes stranded virtual loss without creating visits; a recovery path that increments a visit count is a defect.

***

### Phase 4: Value Estimation and Calibration Without a Trained Value Network

**Objective**: Supply every non-terminal leaf with a bounded value estimate whose provenance, uncertainty, and non-authorising status are recorded, and calibrate those estimates against the returns and verdicts subsequently observed.

#### Step 4.1: Produce a Bounded Leaf Value From the Layered Evaluator

**Required Actions**:

- Run the deterministic layer first: constraint satisfaction, invariant checks, progress measures against declared subgoals, resource feasibility, and any partial credit the terminal verifier can award on an incomplete state. Record its result as hard validity plus a bounded deterministic component.
- Route to the model layer only the residual criteria no deterministic check covers, presenting the canonical state, the evidence references, the rubric, and at most the declared number of retrieved value lessons, with candidate order randomised and generator identity withheld.
- Require the model layer to return a structured verdict carrying a bounded scalar, a confidence figure, the criteria it judged, and the evidence identifiers it used, and reject a free-prose verdict at parse time.
- Invoke the adversarial layer only where the model layer's uncertainty exceeds the declared threshold or where the top two sibling estimates differ by less than the declared separation margin; run one advocate role, one challenger role, and one judge that aggregates to a bounded scalar.
- Combine the layers by the declared aggregation rule, preserve every individual vote rather than only the aggregate, and record the estimate as a proposal with its layer provenance rather than as a measurement of the state's worth.

**Required Outputs**:

- A value estimate record per leaf carrying bounded scalar, hard validity, layer provenance, confidence, uncertainty, and evidence identifiers.
- A preserved vote set for every adversarial evaluation, including dissenting positions.
- An invocation record showing which layers ran and which trigger admitted the adversarial layer.

**Quality Checkpoints**:

- Every estimate falls within the declared bounded interval and carries hard validity as a separate field; an invalid state never enters backup as a low-scoring valid one.
- The adversarial layer runs on no more than 15 percent of value calls per episode; above that share its cost is not recoverable, and the source's own difficulty analysis found adversarial evaluation helped medium and hard tasks while slightly reducing easy-task performance [1].
- No value estimate authorises an answer, a tool call, or a release; any path from an estimate to an authorisation without external verification is a tier violation that halts the episode.

***

#### Step 4.2: Calibrate Estimates Against Backed-Up and Terminal Outcomes

**Required Actions**:

- Pair every leaf estimate with the return eventually backed up through that node and with the terminal verifier verdict of any descendant, and retain the pairs as the calibration corpus for the task class.
- Compute expected calibration error per score bin and per depth band, Brier score, rank correlation between estimate and eventual return, sibling ranking accuracy, and top-k recall of oracle-positive children, using out-of-sample outcomes and task-clustered intervals because siblings correlate.
- Compute the high-confidence error rate as the share of estimates above the confidence threshold whose eventual outcome contradicted them, segmented by depth band and task class.
- Apply the correction where a band fails: recalibrate the mapping from raw verdict to bounded scalar, widen the uncertainty floor for that band, or reduce the weight of the model layer relative to the deterministic layer.
- Monitor externally verified success as the node budget rises, and stop the episode where the internal value improves across iterations while verified success does not, which is the observable signature of proxy overoptimisation [18].

**Required Outputs**:

- A calibration corpus of estimate-and-outcome pairs, segmented by depth band and task class.
- A calibration metric record carrying expected calibration error, Brier score, rank correlation, sibling ranking accuracy, top-k recall, and high-confidence error rate.
- A correction record naming every band that failed and the correction applied.

**Quality Checkpoints**:

- Expected calibration error is at most 0.15 in every score bin and every depth band; a failing band disables soft demotion for that band and reduces its node budget by 50 percent until recalibration completes.
- Sibling ranking accuracy is at least 65 percent against a 50 percent chance level; below 55 percent the ordering is indistinguishable from random, the episode routes to independent sampling with external verification, and no branch is demoted on estimate alone.
- Top-k recall of oracle-positive children is at least 80 percent at the configured retention width; below that figure the widening allowance is raised rather than the estimate being trusted further.
- Estimates are recalibrated whenever the generator model, evaluator model, rubric, state schema, or retrieval index version changes, and at least once per 1,000 episodes; evaluator drift is silent and an admitted evaluator is not permanently admitted.

***

### Phase 5: Scoped Reflection Capture and Lesson Application

**Objective**: Convert a bounded number of evidence-backed prediction errors into lessons that name the conditions under which they apply, and admit those lessons into later policy and value calls only where a deterministic scope predicate matches.

#### Step 5.1: Trigger Reflection Only on Evidence-Backed Surprise

**Required Actions**:

- Enter reflection only after a completed rollout or a committed environment step produces one of the five declared surprise triggers, and only while the episode's reflection budget retains allowance.
- Rank candidate policy and value errors by the magnitude of prediction-outcome disagreement, the number of descendants the error influenced, the number of times the same error signature has recurred, and the trust level of the observation establishing it.
- Select at most the declared per-iteration reflection cap from the ranked list, and never reflect on a node whose only evidence is another model's estimate.
- Classify each selected error as a policy error, where the wrong action was preferred, or a value error, where the state's promise was misjudged, and route it to the corresponding memory partition.
- Record a no-reflection verdict with its reason code where no trigger fired, so that the absence of reflection is auditable rather than silent.

**Required Outputs**:

- A ranked error candidate list with disagreement magnitude, downstream impact, recurrence count, and evidence trust per entry.
- A selection record naming the errors admitted to reflection and those declined.
- A policy-or-value classification per admitted error with its target memory partition.

**Quality Checkpoints**:

- Reflections generated per iteration do not exceed the declared cap of at most 3; reflecting at every node is the dominant cost failure of this method and is blocked by the cap.
- Every admitted error rests on a trusted observation, a terminal verdict, or a backed-up return; an error established only by a second model estimate is declined with a reason code.
- The reflection budget is decremented atomically before the generation call; a call dispatched without a decrement is a ledger violation that halts the episode.

***

#### Step 5.2: Generate and Admit a Scoped, Falsifiable Lesson

**Required Actions**:

- Reconstruct the contrast before generating: for a policy error, the state, the attempted action, the predicted and actual successors, and a better sibling or a later successful action; for a value error, the original estimate, the backed-up or terminal evidence contradicting it, and the observable feature that was overweighted or missed.
- Require the generated lesson to be a conditional clause naming the situation signature, the task family, and the observable feature that discriminates, and reject an unconditional imperative at admission.
- Require the lesson to be falsifiable, in that a later episode matching its scope can produce evidence contradicting it, and reject a lesson no observation could refute.
- Assign hypothesis status and episode-local scope to any lesson whose contrast reference is absent, because a single failure with no successful comparator does not establish which feature discriminated.
- Validate the record before write: schema completeness, scope predicate presence, expiry presence, evidence identifier resolution, absence of credentials, and absence of any instruction directed at the executing system.
- Write the admitted record to episode-local memory, and never edit a historical estimate in place; recompute or invalidate only the priors and leaf values of descendants whose inputs actually change.

**Lesson Scope and Promotion Rules**:

| Property | Episode-local tier | Task-family tier | Global tier |
| :-- | :-- | :-- | :-- |
| Admission requirement | Trigger fired and schema valid | 3 or more independent supports from distinct episodes | Offline human review recorded |
| Contrast reference | Optional; absence forces hypothesis status | Mandatory sibling or later-action contrast | Mandatory, with 2 or more distinct contrasts |
| Default expiry | End of episode | 30 days from last supporting observation | 90 days, renewed by review only |
| Retrievable outside origin episode | No | Yes, within task family and trust domain | Yes, within trust domain |
| Invalidation on version change | Immediate | Immediate | Immediate |
| Measured utility required | Not applicable | Positive over at least 20 paired retrievals | Positive over at least 100 paired retrievals |

**Required Outputs**:

- One reflection record per admitted error, complete against the Phase 2 schema.
- A validation verdict per record covering schema, scope, expiry, evidence, and injection checks.
- An invalidation list naming the descendant nodes whose priors or values were recomputed.

**Quality Checkpoints**:

- Every admitted lesson names the conditions under which it applies; an unconditional lesson is rejected at write time, because a lesson derived from one failure and applied universally degrades search rather than improving it.
- Every lesson lacking a contrast reference carries hypothesis status and remains confined to its originating episode; promotion of a hypothesis lesson is blocked by the store.
- No historical estimate was edited in place; recomputation touched only descendants whose inputs changed.
- The reflection loop stops on repeated paraphrases, contradictory lessons without adjudication, no measurable ranking change, a privacy validation failure, or budget exhaustion, and records which condition fired.

***

#### Step 5.3: Apply Lessons by Deterministic Scope Match

**Required Actions**:

- Evaluate the scope predicate deterministically before any similarity computation: task family, environment version, tool schema version, model and prompt version, trust domain, and expiry must all match, and a record failing any predicate is excluded regardless of how similar its situation signature appears.
- Rank the surviving records by situation-signature similarity, then re-rank by measured utility, recency, and evidence quality, and admit at most the declared retrieval cap of 2 records per call.
- Strip every imperative directed at the executing system from a retrieved record before it enters a prompt, and present the lesson as advisory context labelled untrusted, alongside its confidence and its status.
- Attach a lineage identifier to every retrieval so that the downstream nodes, estimates, and actions a lesson influenced are recoverable for later utility measurement.
- Refuse retrieval across a tenant or trust-domain boundary under every configuration, and rate-limit writes and reads per episode so a poisoned store cannot dominate a search.

**Required Outputs**:

- A retrieval record per call listing candidates excluded by predicate, candidates ranked, and records admitted.
- A sanitised lesson payload carrying advisory text, confidence, status, and untrusted labelling.
- A lineage record linking each retrieved lesson to the nodes and estimates it influenced.

**Quality Checkpoints**:

- Every admitted record passed all 6 scope predicates; embedding similarity never overrides a failed predicate, and a single override is a store defect that quarantines the tier.
- Retrieved records per call number at most 2; a larger cap increases prompt length faster than measured ranking gain.
- No retrieved text modified system instructions, tool definitions, budgets, acceptance tests, or access rights; observations and stored reflections are treated as untrusted input throughout [29].
- Every retrieval carries a lineage identifier; an unlinked retrieval cannot be measured and is treated as a logging failure.

***

### Phase 6: Stopping, Committed Action, and Contamination-Controlled Evaluation

**Objective**: Terminate the search on a declared condition, commit at most one externally authorised action, and measure the configuration in a way that separates the method's contribution from the lesson store's contribution.

#### Step 6.1: Enforce the Stopping Rule and Select the Root Action

**Required Actions**:

- Stop the loop on the first of these conditions: a root child meets the configured visit and verification threshold; any ledger dimension is exhausted; the frontier is empty; the best root action changes by less than the stagnation delta across the stagnation window; or safety monitoring halts the run.
- Never reset a counter, extend a cap, or restart a ledger dimension mid-episode; a cap that is raised during execution invalidates every comparison the episode was authorised against.
- Select the root action by the preregistered rule, which is highest visit count subject to a minimum backed-up value floor, and record the runner-up and the margin between them.
- Return, where the loop exhausted without meeting the acceptance rule, the best externally verified partial state together with its evidence, its uncertainty, and the exact limiting condition, and never relabel the highest unverified estimate as a success.
- Record the exit condition, its reason code, and the ledger state at termination.

**Required Outputs**:

- A termination record naming the exit condition, its reason code, and the exhausted or unexhausted state of all 14 ledger dimensions.
- A selected root action with its visit count, backed-up value, runner-up, and margin.
- A best-so-far record where the exit was not a verified success.

**Quality Checkpoints**:

- Exactly 1 exit condition is recorded per episode; zero or multiple recorded exits invalidate the termination record.
- Stagnation fires where the best root action is unchanged and its visit share moves by less than 2 percentage points across 20 consecutive iterations; continuing past that point consumes budget without changing the decision.
- The selected root action satisfies the minimum backed-up value floor; where no action does, the episode exits with a best-so-far record rather than a selection.
- No counter was reset and no cap was raised during the episode; either event voids the budget-matched comparison from Step 1.2.

***

#### Step 6.2: Authorise and Commit One Action, Then Advance the Root

**Required Actions**:

- Run the authorisation gate outside the model: revalidate the structured arguments, the originating request, the current environment state, the policy, the rate limits, and any required confirmation, independently of the node's visit count or backed-up value.
- Execute a reversible action exactly once under an idempotency key, and require recorded human approval before any privileged or irreversible action.
- Compare the real successor state against the simulated successor, record the mismatch by action class and horizon, and shorten the rollout horizon or return to the real environment where mismatch exceeds the declared threshold.
- Advance the root by reusing a matching transposition node only where environment version, state hash, permissions, and evidence all remain valid, and otherwise create a new root and invalidate stale descendants.
- Repeat Phases 3 through 6 until the goal is externally verified, an authorised stop is emitted, the maximum committed-action count is reached, the request is cancelled, no safe action exists, or any hard cap fires; exit immediately to incident handling on any authorisation or safety failure.
- Release a final result only where the independent goal verifier, the privacy policy, the evidence policy, the tool postconditions, and the output schema all pass, and disclose the answer, its material evidence, its uncertainty, and a concise operational summary rather than intermediate reasoning, private lessons, or adversarial observations [30].

**Required Outputs**:

- An authorisation record per committed action carrying the revalidation result, the idempotency key, and any human approval.
- A simulation-versus-reality mismatch record per committed action, keyed by action class and horizon.
- A root advancement record naming the reused transposition node or the newly created root and the invalidated descendants.

**Quality Checkpoints**:

- Exactly 1 action is committed per search episode; a second committed action without a re-run of the loop is a control defect that halts the run.
- No committed action was authorised by a node score; authorisation is computed outside the model in every case.
- Simulator-versus-reality mismatch above 20 percent by action class shortens the rollout horizon before the next episode; sustained mismatch above 40 percent fails the Simulator Gate and suspends the method for that environment.
- Transposition reuse compared permissions and side-effect history; states with differing side-effect histories are never merged because their observations look similar.

***

#### Step 6.3: Measure Under Contamination Control

**Required Actions**:

- Treat any measurement taken against a warm store as a measurement of the store, and never report it as a measurement of the method; a store built from tasks overlapping the evaluation set makes the two indistinguishable.
- Run cold-store evaluation by resetting the lesson store to empty at episode start, which measures the within-episode reflection loop alone and establishes the floor.
- Run frozen-store evaluation by pinning the store at a declared version with writes disabled for the duration, and verify before the run that the evaluation task identifiers and state signatures are disjoint from those that produced any record in the store.
- Run paired enable-and-withhold trials on identical tasks with identical seeds, retrieval enabled in one arm and withheld in the other, and attribute the difference to lesson utility rather than inferring utility from the presence of reflections.
- Compute the metric set per configuration: verified success rate, oracle coverage, realised success, the decomposed oracle gap, branch efficiency, rollout efficiency, marginal search yield, and reflection utility, reporting medians, tails, and task-clustered intervals.
- Report robustness across at least 5 preregistered seeds with mean, standard deviation, worst seed, and outcome flip rate, and perturb candidate order, observation order, irrelevant content, simulator seeds, and injected instructions.

**Required Outputs**:

- A contamination check record proving task-identifier and state-signature disjointness for every frozen-store run.
- A metric record per evaluation mode, with cold-store and frozen-store figures reported alongside any warm-store figure.
- A robustness record across at least 5 seeds and all 5 perturbation classes.

**Quality Checkpoints**:

- Task-identifier overlap between the evaluation set and the lesson-producing set is exactly 0; any overlap invalidates the frozen-store run.
- State-signature overlap between the evaluation set and the store is at most 5 percent; above that figure the run is discarded and the store is re-partitioned.
- Cold-store and frozen-store figures are both reported; a headline citing only warm-store performance is a reporting defect that blocks promotion of the configuration.
- Reflection utility is computed from paired enable-and-withhold trials, not from the count of reflections generated; causality is never inferred from reflection presence.
- Negative transfer, stale-hit rate, contradiction rate, and utility by lesson age and scope tier are reported; a negative transfer rate above 10 percent suspends the affected scope tier.

***

## III. Implementation Guidance for AI Agents

AI agents running reflective tree search must follow systematic protocols ensuring that the tree, the counters, and the memory remain outside the model, that every estimate is recorded as a proposal, and that every released result carries an external verification. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Gate Agent**: Evaluates the five gates of Section 1.4 and returns invoke, suppress, or a named cheaper route. Owns the baseline ladder record and the overhead estimate, and may refuse the method outright.
2. **Search Controller**: Owns the tree, the node and edge records, the visit counts, the backed-up statistics, the selection rule arithmetic, the widening allowance, the leases and virtual loss, the budget ledger, the stopping rule, and the append-only event log. It issues no model calls and accepts no model-supplied counter.
3. **Proposal Agent**: Generates candidate actions and policy priors conditioned on the canonical state, the legal-action schema, the remaining budget, and admitted lessons. It never applies an action and never writes a statistic.
4. **Evaluation Agent**: Runs the layered evaluator and returns a structured verdict with a bounded scalar, confidence, criteria, and evidence identifiers. It authorises nothing and may not declare a state terminal.
5. **Reflection Agent**: Reconstructs a contrast and drafts a scoped, falsifiable lesson. It proposes a record; it never writes to the store directly and never assigns a scope tier above episode-local.
6. **Memory Custodian**: Validates reflection records against the schema, evaluates scope predicates, enforces expiry and invalidation, executes promotion under the numeric support thresholds, and admits or rejects every retrieval. It is deterministic and holds authority over the store.
7. **Authorisation and Release Agent**: Revalidates arguments, intent, state, policy, and rate limits outside the model, executes committed actions under idempotency keys, and gates release on the independent terminal verifier, the privacy policy, and the output schema.

**Workflow Execution Pattern**:

```
STATE: Search_Iteration
INPUTS:
  1. Tree state with visit counts and backed-up statistics
  2. Budget ledger with remaining allowance per dimension
  3. Lesson candidates admitted by the Memory Custodian
ACTIONS:
  1. Descend by the selection rule; apply lease and virtual loss
  2. Compute widening allowance; request and validate candidate actions
  3. Fork, seed, simulate to the value boundary; obtain terminal reward or leaf estimate
  4. Backpropagate once; release virtual loss and lease
  5. Evaluate surprise triggers; dispatch at most the reflection cap
VALIDATION:
  - model_calls_in_selection_path == 0
  - admitted_children <= widening_allowance
  - backup_updates_per_node_per_rollout == 1
  - transition_provenance_labelled == TRUE
  - reflections_this_iteration <= 3
  - retrieved_records_per_call <= 2
  - all_ledger_dimensions_remaining > 0
TRANSITIONS:
  IF stopping_condition_met THEN next_state = Root_Action_Selection
  IF validation_failed THEN next_state = Iteration_Quarantine
  ELSE next_state = Search_Iteration
```

**Two-Phase Action Pattern**: Emit the intended iteration with its selected path, its worst-case cost reservation, and its validation block before any resource is committed; confirm the reservation against the ledger while nothing is spent; execute only after the reservation succeeds, recording the iteration and its decrement in the same operation.

**Approval Gate**: Human authorisation is required before any committed action in the irreversible class, before promotion of any lesson to the global scope tier, before any episode whose worst-case authorised spend exceeds 40 percent of the deployment's daily budget, and before any configuration change that raises a node budget dimension by more than 50 percent. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the tree, the ledger, and the lesson store in durable transactional storage keyed by run, since a search episode may outlive a single context window.
- Pass node identifiers, evidence references, and content hashes between components rather than full state payloads, and store large payloads encrypted by hash.
- Write a handoff record naming the tree version, the ledger state, the open frontier, the active leases, and the reflection budget at every context boundary.
- Count controller, evaluation, and reflection context consumption toward overhead rather than treating it as free, and compare it against the 40 percent suppression threshold in Section 1.4.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Gate and Budget Integrity (After Phase 1)**

- **Automated Check**: All 5 gate verdicts recorded with reason codes; all 14 ledger dimensions carry numeric limits; verified margin over the best baseline rung is at least 5 percentage points across at least 5 seeds; marginal search yield is positive on every cost denominator.
- **Agent Action on Pass**: Proceed to specification.
- **Agent Action on Failure**: Halt and route to the cheaper baseline named by the failing gate; no node is created against a failed gate.
- **Human Review Trigger**: Verified margin between 3 and 5 percentage points, where the method's value is contested rather than settled.

**Checkpoint 2: Specification Executability (After Phase 2)**

- **Automated Check**: Dry-run completes on 10 of 10 recorded episodes with zero model calls; the transposition merge predicate compares version, permissions, evidence, and side-effect history; every reflection schema field has a write-time validator; no lesson may be written without a scope predicate and an expiry.
- **Agent Action on Pass**: Proceed to the search loop.
- **Agent Action on Failure**: Halt; a specification requiring a model to advance or compare a state is not executable and is returned for redefinition.
- **Human Review Trigger**: Any proposal to merge nodes on state hash alone, or to store a lesson without an expiry.

**Checkpoint 3: Iteration Integrity (After Phase 3)**

- **Automated Check**: Zero model calls in the selection path; admitted children within the widening allowance; exactly 1 backup update per node per completed rollout; every transition labelled with its provenance; virtual loss released on every terminated lease.
- **Agent Action on Pass**: Proceed to value calibration.
- **Agent Action on Failure**: Quarantine the iteration, recompute statistics from the rollout log, and resume from the last consistent tree version.
- **Human Review Trigger**: More than 5 percent of iterations quarantined within one episode.

**Checkpoint 4: Estimator Admissibility (After Phase 4)**

- **Automated Check**: Expected calibration error at most 0.15 per bin and per depth band; sibling ranking accuracy at least 65 percent; top-k recall at least 80 percent; adversarial evaluation on at most 15 percent of value calls; no path from an estimate to an authorisation.
- **Agent Action on Pass**: Proceed to reflection.
- **Agent Action on Failure**: Disable soft demotion for the failing band, reduce its node budget by 50 percent, and continue with hard validity checks only until recalibration completes.
- **Human Review Trigger**: Sibling ranking accuracy below 55 percent, at which point the ordering is indistinguishable from random.

**Checkpoint 5: Lesson Admissibility (After Phase 5)**

- **Automated Check**: Every admitted lesson names its conditions; every contrast-free lesson carries hypothesis status and episode scope; all 6 scope predicates evaluated before similarity ranking; at most 2 records retrieved per call; no retrieved text reached system instructions, tools, budgets, or acceptance tests.
- **Agent Action on Pass**: Proceed to commitment.
- **Agent Action on Failure**: Reject the record, quarantine the affected scope tier, and re-run the iteration with retrieval disabled.
- **Human Review Trigger**: Any promotion to the global scope tier, or any detected injection attempt originating in a stored record.

**Checkpoint 6: Termination and Measurement Validity (After Phase 6)**

- **Automated Check**: Exactly 1 exit condition recorded; at most 1 committed action per episode; no counter reset and no cap raised; task-identifier overlap with the lesson-producing set exactly 0; state-signature overlap at most 5 percent; cold-store and frozen-store figures both present.
- **Agent Action on Pass**: Release the outcome record and permit promotion of the configuration.
- **Agent Action on Failure**: Withhold the report, name the missing evidence, and block promotion; a configuration is never promoted on warm-store results alone.
- **Human Review Trigger**: Any recorded safety incident, any irreversible action executed inside a rollout, or a robustness gap above 20 percentage points across seeds.

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
LEDGER_STATE_AT_CHECK:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Value Noise Dominates Selection**

- **Symptoms**: One root child accumulates most visits within the first 20 iterations; the visit distribution is more concentrated than the backed-up value separation justifies; oracle coverage far exceeds realised success with the loss attributed to value ranking.
- **Diagnostic Steps**: Recompute sibling ranking accuracy and top-k recall on the depth bands where concentration appeared, and determine whether the concentration followed a single high-variance early estimate.
- **Resolution Protocol**: Option A, raise the uncertainty floor for the affected depth band so that a single estimate cannot separate siblings. Option B, reserve a fixed novelty share of iterations for children below the retention cut. Option C, raise the exploration constant after re-normalising rewards, then re-tune on held-out episodes. Option D, disable soft demotion and run with hard validity checks only until recalibration completes.
- **Escalation Trigger**: Sibling ranking accuracy below 55 percent suspends the method for that task class; this error class is never resolved by increasing the node budget.

**Error Type 2: Reflection Overgeneralisation and Negative Transfer**

- **Symptoms**: A lesson is retrieved across visibly dissimilar situations; success falls in the enabled arm of paired enable-and-withhold trials; contradiction links accumulate against one record; the same lesson appears under multiple paraphrases.
- **Diagnostic Steps**: Trace every retrieval of the record through its lineage identifiers, and determine whether the scope predicate was too broad, the situation signature too coarse, or the lesson unconditional.
- **Resolution Protocol**: Option A, narrow the scope predicate to the discriminating feature and re-admit the record at episode-local tier. Option B, demote the record to hypothesis status pending a sibling contrast. Option C, expire the record and deduplicate its paraphrases. Option D, adjudicate contradictory records and retain at most one, recording the adjudication.
- **Escalation Trigger**: Negative transfer above 10 percent for a scope tier suspends retrieval from that tier; a lesson with 3 or more unadjudicated contradictions is expired rather than retried.

**Error Type 3: Search Explosion and Budget Overshoot**

- **Symptoms**: Generated nodes rise faster than the widening allowance predicts; the frontier grows monotonically; reservations are refused; wall-clock cost exceeds the projection while verified success is flat.
- **Diagnostic Steps**: Compare admitted children against the computed allowance per node, check the transposition hit rate, and locate the overrun in expansion, rollout length, evaluation, or reflection.
- **Resolution Protocol**: Option A, reduce the widening coefficient or exponent and re-run the budget-matched comparison. Option B, shorten the rollout depth cap and value earlier from the layered evaluator. Option C, enable transposition reuse where the merge predicate permits it. Option D, route the task class to the cheaper baseline named by the Budget Gate.
- **Escalation Trigger**: Two consecutive episodes exceeding any ledger dimension escalate for policy review; a cap is never raised mid-episode to resolve this class.

**Error Type 4: Simulator Infidelity or Execution During Simulation**

- **Symptoms**: Real successor states diverge from simulated ones; mismatch grows with horizon; a rollout worker records a side effect; an outbound call succeeds from a rollout context.
- **Diagnostic Steps**: Replay recorded real transitions against the simulator by action class and horizon, and audit rollout worker credentials, network policy, and side-effect identifiers.
- **Resolution Protocol**: Option A, shorten the rollout horizon to the depth at which mismatch remains below the threshold. Option B, replace model-simulated transitions with fixture replay for the affected action classes. Option C, revoke rollout worker credentials and outbound access, then re-test the denials continuously. Option D, fail the Simulator Gate and route to proposal-only planning.
- **Escalation Trigger**: Any irreversible action executed inside a rollout is a severity-one incident that halts the deployment immediately; mismatch above 40 percent by action class suspends the method for that environment.

**Error Type 5: Lesson Store Poisoning**

- **Symptoms**: A stored record carries an imperative directed at the executing system; retrieval frequency spikes for one record; a record's evidence identifiers do not resolve; write volume exceeds the per-episode rate limit.
- **Diagnostic Steps**: Re-run the write-time validator over the affected partition, resolve every evidence identifier, and trace the record's provenance to the observation that produced it.
- **Resolution Protocol**: Option A, quarantine the record and the partition, and disable retrieval from that tier. Option B, strip instructions and re-admit only the advisory clause where provenance resolves. Option C, roll the store back to the last validated version and replay admissions. Option D, tighten the trust-domain partition so that the originating observation class cannot write.
- **Escalation Trigger**: Any confirmed injection originating in a stored record escalates to human review and blocks global promotion for 30 days; this class is never resolved by re-running retrieval [29].

**Error Type 6: Correlated Rollouts and False Certainty**

- **Symptoms**: Rollouts from one child paraphrase a single trajectory; action and state overlap between rollouts is high; return variance is far below the variance implied by the nominal rollout count.
- **Diagnostic Steps**: Compute action overlap, state overlap, and return correlation across rollouts from the same child, and estimate effective sample size against nominal rollout count.
- **Resolution Protocol**: Option A, vary rollout seeds and sampling parameters and re-measure overlap. Option B, use a distinct generator or prompt for a share of rollouts. Option C, normalise duplicate trajectories so they contribute one backup rather than several. Option D, replace additional rollouts with an external evidence call, since more identical samples add cost without information.
- **Escalation Trigger**: Effective sample size below 40 percent of nominal for two consecutive episodes suspends the visit-count root rule in favour of externally verified value; this class is never resolved by raising the rollout cap.

**Troubleshooting Decision Tree**:

```
SEARCH EPISODE FAILS A CHECKPOINT
├─ ALLOCATION DEFECT
│   ├─ Visits concentrate beyond value separation → Raise uncertainty floor; reserve novelty share
│   ├─ Sibling ranking accuracy below 55 percent → HALT method for the task class
│   └─ Effective sample size below 40 percent → Vary seeds and generators; normalise duplicates
├─ BUDGET DEFECT
│   ├─ Admitted children exceed allowance → Quarantine node; recompute allowance
│   ├─ Ledger dimension exhausted → Exit with best-so-far; never raise the cap
│   └─ Overhead above 40 percent of episode cost → Route to the cheaper baseline
├─ MEMORY DEFECT
│   ├─ Lesson retrieved outside its conditions → Narrow scope predicate; demote to hypothesis
│   ├─ Negative transfer above 10 percent → Suspend retrieval from the scope tier
│   └─ Imperative found in a stored record → HALT retrieval; quarantine partition; escalate
├─ ENVIRONMENT DEFECT
│   ├─ Simulator mismatch above 20 percent → Shorten horizon; replay fixtures
│   └─ Side effect recorded in a rollout → HALT deployment; revoke credentials; incident review
└─ MEASUREMENT DEFECT
    ├─ Evaluation set overlaps the lesson store → Discard run; re-partition; re-measure cold
    └─ Only warm-store figures reported → Block promotion; report cold and frozen figures
```

### D. Performance Metrics and Continuous Learning

**Search Quality Metrics**:

- **Verified success rate**: Externally verified successes over eligible episodes, stratified by task class, difficulty, model, risk tier, and budget (target: at least 5 percentage points above the best baseline rung at matched budget).
- **Oracle gap**: Oracle coverage minus realised success, decomposed into generation, value, pruning, scheduling, budget, execution, and release loss (target: no single component above 40 percent of the gap, so attribution remains actionable).
- **Branch efficiency**: Expanded edges on the solution path over all expanded edges (target: at least 0.15; below 0.05 indicates the allocation adds little over uniform expansion).
- **Root selection margin**: Visit-share difference between the selected root action and the runner-up (target: at least 10 percentage points; a smaller margin routes to external verification before commitment).

**Cost and Calibration Metrics**:

- **Marginal search yield**: Additional verified successes over the cheapest adequate baseline per additional token, unit of currency, and second (target: positive on all 3 denominators).
- **Cost multiplier**: Tokens, currency, and latency relative to each baseline rung, reported alongside every success figure so gain is never quoted without its price.
- **Expected calibration error**: Visit-weighted absolute gap between predicted and observed success frequency per bin and depth band (target: at most 0.15).
- **High-confidence error rate**: Estimates above the confidence threshold contradicted by the eventual outcome (target: at most 10 percent).

**Reflection and Robustness Metrics**:

- **Reflection utility**: Paired change in action recall, value error, nodes to solution, and verified success between retrieval-enabled and retrieval-withheld arms (target: positive on at least 3 of 4 measures).
- **Negative transfer rate**: Retrievals followed by a worse outcome than the withheld arm (target: at most 10 percent per scope tier).
- **Stale-hit rate**: Retrievals of records invalidated by a version change but not yet expired (target: 0; a non-zero figure indicates the invalidation hook is not wired).
- **Robustness gap**: Verified success difference between clean and perturbed conditions across at least 5 seeds (target: at most 20 percentage points; a larger gap blocks promotion).

**Learning and Adaptation Mechanisms**:

- **Evidence-bound promotion**: A lesson rises a scope tier only on the numeric support thresholds in Step 5.2, never on apparent generality.
- **Utility-weighted retention**: Records whose measured utility is non-positive over 20 paired retrievals expire on schedule rather than being renewed.
- **Threshold recalibration**: Every numeric bound here is recomputed per task class against observed outcomes; the values stated are deployment defaults, not constants.
- **Configuration versioning**: The exploration constant, widening parameters, reflection policy, and store version are versioned together, and any change re-opens the budget-matched comparison of Step 1.2.

**Human-in-the-Loop Boundaries**: Promotion of a lesson to global scope, authorisation of an irreversible action, relaxation of the disclosure boundary, raising a node budget dimension by more than 50 percent, and promotion of a configuration whose advantage appears only under a warm store are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how bounded computation is allocated over reversible alternatives and how the resulting errors are recorded, not the content of any particular decision. Its phases hold wherever states can be snapshotted and restored, several actions carry delayed consequences, and an external signal can distinguish progress.

### 4.1 Cross-Domain Application Patterns

**Interface and workflow automation**: States are page or application states, actions are structured interactions, and the simulator is a replayable environment with synthetic accounts and disposable data. The Simulator Gate is usually satisfiable, which is why this is the setting in which the method has been most reported. Policy lessons take the form of preferring one navigation route over another under a named interface condition; value lessons record which observable feature signalled that a route was a dead end. Irreversible transitions such as placing an order or sending a message are searched as non-executing proposals and authorised exactly once at commitment.

**Sandboxed software repair**: States are repository and test states, actions are edits and commands, and the simulator is a disposable container with resource and network limits. Terminal verification is unusually strong here because a test suite is a deterministic oracle, so the Value Gate is easy to satisfy and value estimates can be calibrated against a crisp outcome. Reflection captures which failure signature implies which class of fix, scoped to the language, framework version, and test harness, and expires on any dependency upgrade.

**Formal and quantitative reasoning**: States are partial derivations or proof states, actions are inference or transformation steps, and verification is a checker rather than a judgement. The dominant risk is proxy overoptimisation, where a process value rises while verified correctness does not [18]. Deployments must monitor externally verified success as the node budget rises and stop on the divergence signature in Step 4.2 rather than continuing while the internal score improves.

**Operations and logistics planning**: States are schedules, allocations, and resource positions, and the simulator is a digital twin whose fidelity is measured rather than assumed. Reversibility varies within one episode, since a provisional allocation is reversible while a dispatched shipment is not, so the action-class inventory of Step 1.1 carries the load and the authorisation gate binds per class. Simulator mismatch measurement is the binding constraint, because a twin that drifts silently turns search into confident misallocation.

**Regulated decision support**: Most actions are irreversible in practice, so the Simulator Gate fails for the actions themselves and the method is applied to non-executing proposals only. The tree becomes an auditable record of which alternatives were considered, at what cost, and on what evidence, and the event log becomes a deliverable rather than a diagnostic aid. Lesson stores in this setting are partitioned per tenant and per jurisdiction, and global promotion is generally withheld because a lesson learned under one regime is not evidence under another.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small-scope reversible work**: Reduce to a depth bound of 2, a widening allowance capped at 3 children, and 20 to 50 rollouts, retaining the ledger, the stopping rule, and cold-store reflection. Where total overhead exceeds 25 percent of the direct-execution cost, the Search-Need Gate should have suppressed the method.
- **Large-scope or long-horizon work**: Retain every phase, persist the tree and ledger in transactional storage, run parallel workers under leases and virtual loss, and write a handoff record at every context boundary so the episode survives a context reset.
- **High-risk or irreversible work**: Search proposals only, require recorded human approval at the authorisation gate, raise the minimum backed-up value floor for root selection, and prefer abstention with a best-so-far record over commitment on an unverified estimate.
- **Strict latency budgets**: Reduce the rollout depth cap and value earlier from the layered evaluator rather than removing checkpoints, since removing them removes control while shortening them raises its frequency. Where latency forbids any search iteration, route to the baseline named by the Budget Gate.
- **Multi-tenant deployments**: Partition the lesson store per tenant and per trust domain, forbid cross-partition retrieval under every configuration, and run cold-store evaluation per tenant so one tenant's accumulated store never inflates another's reported performance.
- **Difficulty-aware routing**: Route easy cases to direct solution, middle cases to bounded search, and unsupported cases to abstention, rather than spending the maximum budget on every request; the source reports compute-optimal allocation substantially outperforming uniform best-of-N spending [20].

***

## V. Limitations and Considerations

**Cost is the dominant limitation**: This is the most expensive method in the reasoning family, and the published evidence the source transcribes reports token multipliers between 7.4 and 10.1 relative to a single-trajectory baseline for absolute success gains between 9.1 and 14.9 percentage points on three web-task subsets [1]. The consequence is that a deployment which skips the baseline ladder will usually pay a large multiplier for a gain a cheaper rung already delivers. The mitigation is the Budget Gate in Section 1.4 and the paired budget-matched comparison in Step 1.2, which withdraw the justification wherever the verified margin falls below 5 percentage points or marginal search yield is non-positive on any denominator.

**The offline learning stage is out of scope**: The originating source pairs inference-time reflective search with an offline stage that fine-tunes a policy on filtered search traces, and reports that a learned policy recovered a large share of search performance at substantially lower token cost. The consequence is that a reader expecting weight-level internalisation will not find it here. The mitigation is the declared re-scoping in Section 1.3: that stage trains foundation model weights, sits below the AI Agent layer, and must be run as a separate machine-learning workflow with its own promotion gate; the agent-layer surrogate specified here is the scoped lesson store, which reduces repeated error without touching weights.

**A value estimate is a proposal, not a measurement**: No trained value network is assumed, so leaf values come from deterministic checks plus a model judgement, and a model judgement correlates with the generator that produced the state. The consequence is that confident early estimates can absorb the visit budget and make search worse than a single chain while costing many times more. The mitigation is the layered evaluator in Step 4.1, the calibration thresholds and their breach consequences in Step 4.2, and the authority rule in Section 1.2 that no estimate authorises a release without external verification.

**Adversarial evaluation is structured argument, not ground truth**: The advocate, challenger, and judge roles remain correlated, and a judge can favour a fluent case over a correct one. The consequence is that universal adversarial evaluation raises cost and can reduce performance on easy tasks, which the source's own difficulty analysis reports [1]. The mitigation is the uncertainty trigger and the 15 percent cap on adversarial value calls in Step 4.1, together with preservation of every vote rather than only the aggregate.

**A lesson store contaminates its own evaluation**: Reflections from earlier episodes influence later ones, so any measurement taken against a store built from overlapping tasks describes the store rather than the method. The consequence is that warm-store figures systematically overstate what a fresh deployment will achieve. The mitigation is Step 6.3: cold-store and frozen-store figures must both be reported, task-identifier overlap must be exactly 0, state-signature overlap at most 5 percent, and lesson utility must come from paired enable-and-withhold trials rather than from the presence of reflections.

**An unconditional lesson degrades search**: A lesson derived from one failure and applied wherever it appears superficially relevant will misdirect expansion in situations it never described. The consequence is negative transfer that is difficult to detect because the search still completes. The mitigation is the scope predicate requirement in Phase 2, the hypothesis status assigned to contrast-free lessons in Step 5.2, the deterministic scope match preceding similarity ranking in Step 5.3, and the 10 percent negative transfer threshold that suspends a scope tier.

**The method depends entirely on a faithful, resettable simulator**: Rollouts have no value where the environment cannot be snapshotted, forked, restored, and seeded, and a world model that invents plausible futures makes search actively worse than not searching. The consequence is that infidelity produces confident allocation toward states that do not exist. The mitigation is the Simulator Gate in Section 1.4, the mismatch measurement and horizon-shortening rule in Step 6.2, and the severity-one escalation for any side effect recorded inside a rollout.

**Stored reflections and intermediate states carry disclosure exposure**: Tree states, observations, and lessons may contain personal, financial, credential, or proprietary content, and a store rich enough to help search is rich enough to leak. The consequence is that retention defaults chosen for search quality can violate a retention policy. The mitigation is compact structured records rather than unrestricted reasoning, tenant and trust-domain partitioning, redaction before export, propagated deletion, short default retention, and the disclosure rule in Step 6.2 that releases evidence and uncertainty rather than intermediate reasoning [30].

**Numeric thresholds here are deployment defaults**: The widening coefficient and exponent, the exploration constant, the 30-day lesson expiry, the 2-record retrieval cap, the 3-reflection per-iteration cap, the 15 percent adversarial share, the 5-point verified margin, the 20-iteration stagnation window, the 2-percentage-point visit-share delta, the 10 percent negative transfer ceiling, the 5 percent state-signature overlap ceiling, and the 20 and 40 percent simulator mismatch thresholds were chosen to be operable on first deployment. Only the search configuration figures transcribed from the source and marked as such are measured findings. The consequence is that a deployment treating them as constants will mis-tune. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute every threshold per task class against observed outcomes.

**External claims are transcribed rather than independently established**: The quantitative figures attributed to the source in Sections 1.4, IV, and V are reproduced as the source cited them. During conversion the reference at entry 1 was retrieved and its title, its per-subset success rates, its token multipliers, its reflection ablation figures, and its search configuration parameters were confirmed against the transcription; the remaining entries were not re-verified. The consequence is that a figure carried from an unverified entry may be misattributed or superseded. The mitigation is to treat every unverified figure as a claim of the source rather than an established result, and to re-run the baseline ladder locally before relying on any of them.

**Structural conformance is not sound search**: An episode can satisfy every checkpoint here and still search toward a poorly chosen objective under a verifier that measures the wrong thing. The framework detects malformed search, not misdirected purpose. The mitigation is human review of the decision contract and the terminal verifier, which no checkpoint in this guide replaces.

***

## VI. Conclusion and Summary

Reflective Monte Carlo tree search is an accounting discipline before it is a reasoning technique. Its value comes from a small number of quantities that software owns and a model never touches: visit counts, backed-up returns, a widening allowance, a budget ledger, and a scope predicate. The model contributes proposals, judgements, and lessons, and every one of them is a proposal that some deterministic component admits or rejects. A deployment that keeps that partition will be able to say why a branch was expanded and what the extra computation bought; a deployment that lets estimates and reflections flow directly into decisions will produce an expensive search whose failures cannot be attributed.

The method's two additions over ordinary tree search carry its two characteristic risks. A leaf value obtained without a trained value network is a correlated judgement that can concentrate the visit budget on an early confident error, which is why calibration against backed-up and terminal outcomes is a phase rather than a diagnostic. A lesson written from one failure and retrieved wherever it looks relevant will misdirect later search silently, which is why a lesson without stated conditions is rejected at write time and why any evaluation reusing a warm store is treated as a measurement of the store.

A team adopting the method should instrument the baseline ladder before building a tree. Establish the terminal verifier and the simulator first, measure the cheaper rungs, and only then run a budget-matched comparison across preregistered seeds. Add reflection last, behind its own gate, and measure it by withholding retrieval rather than by counting reflections produced.

**Key Success Factors**:

- **The tree stays outside the model**: Visit counts, backed-up statistics, the selection arithmetic, the widening allowance, the ledger, and the scope predicate are computed by software, and no model-supplied counter is ever accepted.
- **Cost is justified before it is spent**: The method runs only where a paired budget-matched comparison shows at least a 5-point verified margin over the cheapest adequate baseline and positive marginal search yield on every denominator.
- **Estimates order search and authorise nothing**: Release requires a terminal verifier sharing neither weights nor prompt with the generator or the evaluator, and budget exhaustion returns a best-so-far result rather than a manufactured answer.
- **Lessons name their conditions**: Every stored lesson carries a scope predicate, an expiry, and a contrast, and a lesson without a comparator stays a hypothesis confined to the episode that produced it.
- **Simulation and execution stay separated**: Rollouts run in forks with credentials and outbound access denied, irreversible proposals are valued from pre-execution evidence, and one authorised action is committed outside the model.
- **Measurement is contamination-controlled**: Cold-store and frozen-store figures are reported alongside any warm-store figure, and lesson utility comes from paired enable-and-withhold trials.

By following this guide, AI agents can spend a large search budget deliberately, record why each expansion was made, and convert their own prediction errors into scoped memory that improves later search without being mistaken for the method's own performance.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them, and their titles and locations are reproduced rather than reconstructed. A bounded verification pass was performed during conversion: entry 1 was retrieved and its title, per-subset success rates, token multipliers, reflection ablation figures, and search configuration parameters were confirmed to match the transcription, and that entry is marked verified below. No search pass was performed and no other entry was independently re-verified, so the quantitative findings attributed to the remaining entries in Sections 1.4, IV, and V are carried as claims of the source rather than as confirmed results.

**Corpus pointers**:

- `Production Guide to Reflective Monte Carlo Tree Search` — the originating prose guide from which this operational guide was derived. Source of the four-phase loop and its reflective extension, the gate structure, the value and reward separation, the reflection record inventory, the retrieval and expiry rules, the production workflow, the environment safety and search engineering rules, the metadata logging inventory, the log-derived metric definitions, the failure-mode catalogue, and the deployment acceptance checklist. Its inline citations to primary literature supply the external references listed below. Its offline exploratory-learning stage is declared out of scope in Section 1.3.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/reasoning/guide_TreeOfThought.md` — the search-construction companion. It owns evaluator construction, the evaluator admission bar, evaluator calibration procedure, hard and soft pruning with reason codes, the diversity reserve, backtracking and reinstatement, and bounded expansion under a declared branching factor; this guide adopts them by reference rather than re-deriving them, and adds visit counts, the selection rule, return backup, and progressive widening. The terms canonical state, state identity hash, node, edge, layered evaluator, terminal verifier, oracle coverage, realised success, oracle gap, and marginal search yield are adopted from it unchanged.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — the control-layer companion. It owns value-of-computation control and the meta-level decision to stop; this guide specifies the search once that decision returns invoke. The terms decision contract, budget ledger, reason code, exit condition, stuck state, and correlated failure are adopted from it unchanged.
- `advanced_task_guides/reasoning/guide_SelfConsistency.md` — the independent-sampling baseline named in the baseline ladder of Step 1.2 and in the gate routing table of Section 1.4.
- `advanced_task_guides/reasoning/guide_ChainOfThoughtReasoning.md` — the single-chain baseline named in the baseline ladder of Step 1.2 and in the gate routing table of Section 1.4.
- `advanced_task_guides/reasoning/guide_MetacognitiveMonitoring.md` — the corpus guide covering calibration and abstention, applicable to the confidence and abstention decisions referenced in Step 1.1 and Step 6.1.
- `advanced_task_guides/planning/guide_WorldModelSimulationPlanning.md` — the corpus guide covering simulation-based planning, applicable to the simulator fidelity and rollout controls in Step 3.3 and Error Type 4.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — the corpus guide covering event schema design and instrumentation, applicable to the run, node, edge, rollout, reflection, and value-estimate records this guide requires.
- `advanced_task_guides/scoring/guide_complexityScoring.md` — a compact scoring rubric usable as an input to the difficulty-aware routing described in Section 4.2.
- `advanced_task_guides/reasoning/guide_BufferOfThoughts.md` — the sibling guide owning a governed, cross-run library of reasoning templates distilled from verified solutions, with a fixed abstraction policy, hybrid retrieval under authorization filters, a fit check that discards rather than forces a poor match, and a promotion gate that software closes. Its library and the lesson store specified here answer the same hazard from opposite ends: a template is a reusable procedure retrieved before work begins, while a lesson is a scoped correction retrieved during search that conditions proposal and evaluation and never authorises a release. Its promotion-gate and error-propagation discipline is the applicable model wherever lessons are persisted beyond one run.
- `advanced_task_guides/reasoning/guide_AnalogicalReasoning.md` — companion guidance owning source-to-target transfer as an auditable mapping with an explicit register of where the correspondence breaks. It defines the negative-transfer measure this guide reports per scope tier, and its rule that a conclusion resting on an unmapped element must be rejected is the same discipline the scope predicate enforces on lesson retrieval here.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, II, III, IV, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Reflective search, classical foundations, and the benchmark setting*

1. Yu and colleagues, *ExACT: Teaching AI Agents to Explore with Reflective-MCTS and Exploratory Learning* — https://arxiv.org/html/2410.02052v3 (title and quantitative figures verified against the arXiv record during conversion)
2. Huang and colleagues — https://arxiv.org/abs/2310.01798
3. Browne and colleagues — https://repository.essex.ac.uk/4117/
4. Auer, Cesa-Bianchi, and Fischer — https://link.springer.com/article/10.1023/A:1013689704352
5. Kocsis and Szepesvári — https://eprints.sztaki.hu/4634/
6. Silver and colleagues, *AlphaZero* — https://arxiv.org/abs/1712.01815
7. Lee and colleagues — https://ojs.aaai.org/index.php/AAAI/article/view/5885/5741
8. Koh and colleagues, *VisualWebArena* — https://arxiv.org/abs/2401.13649

*Search-guided language agents and episodic reflection*

9. Zhou and colleagues, *Language Agent Tree Search* — https://arxiv.org/abs/2310.04406
10. Hao and colleagues, *Reasoning via Planning* — https://aclanthology.org/2023.emnlp-main.507/
11. Yao and colleagues — https://arxiv.org/abs/2305.10601
12. Shinn and colleagues, *Reflexion* — https://arxiv.org/abs/2303.11366
13. *MCTSr* — https://arxiv.org/abs/2406.07394

*Process supervision, reward modelling, and mathematical search systems*

14. Qi and colleagues, *rStar* — https://arxiv.org/abs/2408.06195
15. Guan and colleagues, *rStar-Math* — https://arxiv.org/abs/2501.04519
16. Chen and colleagues, *AlphaMath* — https://arxiv.org/abs/2405.03553
17. Zhang and colleagues, *ReST-MCTS star* — https://proceedings.neurips.cc/paper_files/paper/2024/file/76ec4dc30e9faaf0e4b6093eaa377218-Paper-Conference.pdf
18. Gao and colleagues — https://arxiv.org/abs/2210.10760

*Test-time compute allocation and reasoning models*

19. Brown and colleagues — https://arxiv.org/abs/2407.21787
20. Snell and colleagues — https://arxiv.org/abs/2408.03314
21. *DeepSeek-R1 report* — https://arxiv.org/abs/2501.12948
22. OpenAI, *reasoning guidance* — https://developers.openai.com/api/docs/guides/reasoning-best-practices
23. Anthropic, *extended-thinking documentation* — https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking

*Execution infrastructure and reproducible environments*

24. *Temporal documentation* — https://docs.temporal.io/
25. *Ray Core* — https://docs.ray.io/en/latest/ray-core/walkthrough.html
26. *OpenSpiel* — https://github.com/google-deepmind/open_spiel
27. *Gymnasium* — https://gymnasium.farama.org/

*Instrumentation, injection, and disclosure*

28. OpenTelemetry, *GenAI agent-span conventions* — https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md
29. OWASP, *prompt-injection guidance* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
30. OWASP, *sensitive-information guidance* — https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/
