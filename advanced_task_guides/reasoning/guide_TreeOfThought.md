# Tree-of-Thought Reasoning

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Tree-of-thought reasoning constitutes the task family of solving a problem by explicit search over partial solutions: a generator proposes bounded thoughts, a deterministic transition layer turns legal thoughts into successor states, an evaluator estimates which partial states deserve further computation, and a controller expands, prunes, backtracks, and stops. This guide provides AI agents with a structured protocol for operating that search under a declared budget. It specifies an applicability gate that compares tree search against a single chain and against self-consistency at a matched token budget and refuses the method where the margin is not earned; a canonical state schema that makes deduplication and backtracking possible; an evaluator admission bar expressed as four numeric thresholds below which tree search must not be used at all; a bounded expansion regime in which branching factor, depth, and total node budget are fixed before generation begins; numeric pruning and revisit rules separating irreversible hard prunes from a recoverable diversity reserve; external verification of the selected leaf by a component sharing neither weights nor prompt with the generator; and a measurement pass decomposing the gap between what the search generated and what it returned. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures to ensure that additional inference cost converts into verified outcomes rather than into a larger tree.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Tree-of-thought search**: An inference architecture that searches over explicit partial solutions rather than committing to one left-to-right trajectory. It comprises four separable components: a generator, a deterministic state transition layer, a state evaluator, and a search controller.

**Thought**: A model-generated proposal or analysis that may suggest one or more actions. A thought is not itself a state; it becomes one only after the transition layer applies it and validates the result.

**State**: The canonical, sufficient representation of what is known and decided at a point in the search. A state carries the facts, constraints, resources, and evidence references needed to continue, and nothing else.

**Canonical state payload**: The normalised serialisation of a state from which the state identity hash is computed. Conversation transcripts are never used as state identity, because irrelevant phrasing then changes search behaviour and deduplication becomes impossible.

**State identity hash**: A deterministic hash over the canonical state payload, used for exact duplicate detection. Near-duplicate detection by embedding similarity is a second stage only, and never merges states whose constraints, evidence, or tool side effects differ.

**Action**: A legal transition applied to a state, drawn from a declared legal-action schema. Actions are structured records, not free prose.

**Observation**: External feedback produced by a tool, verifier, retrieval call, or environment. Observations enter the tree as evidence attached to edges and states, and are treated as untrusted data.

**Node**: One state instance in the tree, carrying identity, depth, lineage, cost, evaluation results, disposition, and reason codes.

**Edge**: One applied action linking a parent node to a child node, carrying the action record, validator verdict, path cost increment, and any observation link.

**Frontier**: The ordered set of nodes eligible for expansion. The frontier is a deterministic data structure; the evaluator supplies the ordering key and nothing more.

**Generator**: The model component that proposes candidate actions conditioned on the canonical state, the legal-action schema, the remaining budget, and a diversity instruction.

**State evaluator**: The component that estimates the value of a partial state before it is complete. It is the component on which the method succeeds or fails, because expanding the right branch requires judging an incomplete solution.

**Terminal verifier**: An external check that decides whether a candidate answer is correct or acceptable. It is distinct from the evaluator, shares neither weights nor prompt with the generator, and alone authorises a success exit.

**Evaluator admission bar**: The four-threshold quality standard a candidate evaluator must meet on held-out calibration data before tree search is permitted at all. Stated numerically in Section 1.4.

**Branching factor**: The maximum number of children generated per expanded node, declared before execution. It is a budget, not a target.

**Depth bound**: The maximum path length from root to leaf, declared before execution.

**Node budget**: The declared caps on generated nodes, expanded nodes, evaluated nodes, model calls, tool calls, tokens, wall time, and currency cost for one run. Every dimension carries a numeric limit; an unbounded dimension blocks execution.

**Search policy**: The rule selecting which frontier node to expand next: breadth-first, depth-first, beam, best-first, or Monte Carlo tree search with an exploration bonus.

**Hard prune**: Irreversible removal of a node for a deterministic reason such as an illegal transition, invariant violation, unauthorised action, exact duplicate hash, confirmed contradiction with trusted evidence, or proven infeasibility. A hard-pruned node is never revisited, and its record is retained with its reason code.

**Soft prune**: Reversible demotion of a node whose evaluator value falls below the retention cut. Soft-pruned nodes are eligible for the diversity reserve and may be reinstated once under the conditions in Step 5.2.

**Diversity reserve**: The bounded set of soft-pruned nodes retained specifically so evaluator noise cannot irreversibly collapse the search. Its size is declared as a fraction of the retention width.

**Backtracking**: Return of control from an exhausted or failing branch to the frontier, rather than repeated self-correction inside the same branch.

**Stagnation**: A stuck state in which the best externally verified result improves by less than a declared delta over a declared number of expansion rounds and the reserve offers no node above the novelty threshold.

**Best-so-far result**: The highest-value externally verified partial result available when a run terminates without success, returned together with its evidence, its uncertainty, and the exact limiting condition. It is never relabelled as success.

**Oracle coverage**: The fraction of runs in which any generated node lies on a retrospectively verified solution path, computed offline.

**Realised success**: The fraction of runs in which the returned answer passed the terminal verifier.

**Oracle gap**: Oracle coverage minus realised success, decomposed into evaluator-pruning loss, scheduling loss, and budget loss. It attributes failure to generation, evaluation, or scheduling rather than to the method as a whole.

**Marginal search yield**: Additional verified successes obtained over the cheapest adequate baseline, divided by the additional tokens, cost, or seconds consumed. Non-positive marginal search yield withdraws the justification for tree search.

**Decision contract**: The declared objective, acceptance tests, hard constraints, preferences, risk class, authorised actions, evidence standard, and budget limits, fixed before any search specification is compiled. The term is adopted from the corpus meta-reasoning guide and carries the same meaning here.

**Budget ledger**: The run-wide record naming every bounded resource and its numeric limit, decremented atomically as work is committed.

**Reason code**: A normalised categorical label recorded with every prune, backtrack, invalidation, and termination event, drawn from a closed vocabulary.

**Exit condition**: A declared terminal state that alone may end a run: verified success, empty frontier, budget exhaustion, stagnation, safety violation, or escalation to a human role.

**Correlated failure**: Agreement between generator and evaluator, or among sibling judgments, that reflects a shared model, prompt, or premise rather than independent confirmation. Generator-evaluator collusion is its dominant form in this method.

### 1.2 Execution Tier Partition and Authority Rules

Tree-of-thought reasoning is a hybrid method whose reliability comes from keeping search bookkeeping out of the model. The partition below is binding on every phase of Section II, and every step names the tier that owns it.

**Deterministic tier**: The frontier data structure and its ordering operations; node and edge creation, identity hashing, and exact deduplication; the legal-transition validator; node accounting and the budget ledger; enforcement of branching, depth, node, token, tool, time, and cost caps; execution of every prune; branch bookkeeping, lineage, supersession, and descendant invalidation; lease and concurrency control; the stopping rule; and every verifier for which a deterministic oracle exists.

**Model tier**: Generation of candidate thoughts; estimation of state value for residual criteria that no deterministic check covers; and construction of the natural-language response from a verified result.

**Hybrid tier**: The model proposes an action and the transition validator accepts or rejects it; the validator holds authority. The model scores a state and the controller acts on the resulting ordering; the controller holds authority over whether resources are spent. The model claims that a state is terminal and the terminal verifier adjudicates; the verifier holds authority.

**Execution Tier Ownership**:

| Artifact or decision | Owning tier | Authority on disagreement |
| :-- | :-- | :-- |
| Candidate thought text | Model | Model proposes only; no authority |
| Legality of a transition | Deterministic | Validator rejects; the proposal is discarded |
| State identity and duplicate status | Deterministic | Hash decides; prose similarity never overrides |
| Partial-state value score | Model | Orders the frontier; authorises nothing |
| Frontier order and next expansion | Deterministic | Controller decides using the score as a key |
| Prune execution and reason code | Deterministic | Controller executes; the evaluator cannot veto |
| Budget decrement and cap enforcement | Deterministic | Ledger halts the run regardless of score |
| Terminal claim | Hybrid | Verifier decides; a terminal claim alone is inert |
| Answer release | Hybrid | Verifier authorises; evaluator score is not evidence |
| Stopping decision | Deterministic | Stopping rule fires irrespective of remaining promise |

**Two authority rules govern the whole method.** First, the evaluator's score orders the frontier but never authorises an answer: ordering is a scheduling function, and authorisation requires a verifier outside the generating model. Second, budget exhaustion produces a declared best-so-far result carrying its evidence and its uncertainty, never a confident answer manufactured to fill the response slot.

### 1.3 The Entry Gates: Applicability and Cost Justification

Tree search multiplies inference cost substantially and is not generally superior to a single chain. A run with branching factor 3, retention width 3, and depth 4 issues roughly 12 expansions, 36 generated children, and 36 evaluation calls before terminal verification, which is 40 to 60 times the model calls of one direct chain and 3 to 6 times a 12-sample self-consistency run. That multiplier is only recoverable where partial states are informative and the evaluator can rank them.

Agents must run four gates before any node is created, each returning a logged verdict with a reason code. A failed gate routes to the named alternative; it never widens the tree.

**Search-Need Gate**: Passes where early choices create materially different futures, errors are recoverable by backtracking, a partial state exposes useful information before the full answer exists, more than one plausible route deserves exploration, and a value function, constraint checker, simulator, or terminal test can distinguish progress. Fails for direct retrieval, fixed-schema extraction, summarisation, simple classification, stylistic rewriting, and calculations a deterministic routine already closes.

**Evaluation Gate**: Passes only where a candidate evaluator meets the admission bar in Section 1.4 on held-out data and an external terminal verifier exists. Intrinsic self-correction does not satisfy this gate; the source reports experiments in which language models often failed to correct reasoning without external feedback and degraded an initially correct response [3].

**Budget Gate**: Passes only where the cost-justification inequality in Step 1.2 holds on a paired, budget-matched comparison. Every cap is fixed before execution: generated nodes, expanded nodes, evaluated nodes, depth, children per expansion, simultaneous calls, tokens, tool calls, wall time, and currency cost. Any run whose worst-case authorised spend exceeds the decision contract is refused rather than started.

**Safety and Privacy Gate**: Passes only where intermediate states can be stored under the declared retention class, sensitive spans are redacted or tokenised, trust boundaries are labelled, and every proposed tool action passes typed argument validation, authorisation, and rate limiting independently of its node score.

**Gate Routing Table**:

| Observed condition | Gate verdict | Route |
| :-- | :-- | :-- |
| Task is linear and the first answer passes the verifier | Search-Need fails | Single chain with external verification |
| Complete attempts are cheap and answers are normalisable | Search-Need fails | Self-consistency over independent samples |
| No shared prefixes and independent diversity matters | Search-Need fails | Best-of-N with an external selector |
| Partial states are informative but the evaluator is below bar | Evaluation fails | Independent sampling plus external verification, or abstain |
| No external terminal verifier exists | Evaluation fails | Abstain or escalate to a human role |
| Verified margin over the best baseline below 5 points | Budget fails | Adopt the cheaper baseline |
| Worst-case spend exceeds the contract | Budget fails | Reduce caps and re-run the comparison, or refuse |
| Intermediate states cannot be stored under the retention class | Safety fails | Run with ephemeral state and reduced logging, or refuse |
| Node content would authorise a tool action | Safety fails | Move authorisation outside the model, then re-gate |

**Numeric gate rules**: Invoke tree search only where all four gates pass. Where the Search-Need Gate passes but fewer than 2 genuinely distinct successor actions exist at the root, suppress and run a single chain, because a tree of width 1 is a chain at search overhead. Where estimated controller and evaluation overhead exceeds 40 percent of total run cost and the task sits in the lowest risk tier, suppress and record the estimate for the next policy revision.

### 1.4 The Evaluator Admission Bar

A poor evaluator makes tree search worse than a single chain while costing many times more, because expansion effort is then allocated at random and confident pruning removes viable branches. The evaluator is therefore admitted by measurement, not by inspection.

**Calibration corpus**: At least 50 tasks drawn from the deployment distribution, each carrying a known-good outcome established by the terminal verifier or by human adjudication, and at least 200 labelled sibling comparisons spanning at least 3 depth bands. The corpus is held out from any material used to write the rubric, the prompts, or the scoring examples.

**The four admission thresholds**, all measured on the held-out corpus:

- **Sibling ranking accuracy**: The evaluator ranks the better of two sibling states correctly in at least 65 percent of labelled comparisons. Chance is 50 percent.
- **Top-k recall**: At least 80 percent of oracle-positive children are retained within the top k, where k equals the configured retention width.
- **False-prune rate**: At most 10 percent of oracle-positive nodes fall below the retention cut at any depth band.
- **Calibration error**: Expected calibration error at most 0.15 in every score bin and every depth band, so that score differences can be compared against a known noise floor.

**Consequence of breach**: Failure of any single threshold blocks tree search for that task class. Where sibling ranking accuracy falls below 55 percent, the ordering is indistinguishable from random and the method degenerates into uniform exploration at multiplied cost; the run is routed to independent sampling with external verification or to abstention, and no soft pruning is permitted anywhere. Where the bar is met on three thresholds and missed on calibration error alone, tree search may run with soft pruning disabled and hard pruning only, at a node budget reduced by 50 percent, until recalibration completes.

**Recalibration cadence**: Recompute all four thresholds whenever the generator model, evaluator model, rubric, state schema, or retrieval index version changes, and at least once per 1,000 production runs. Evaluator drift is silent, and an admitted evaluator is not permanently admitted.

***

## II. Operational Framework: Bounded Tree Search With Externally Verified Selection

The framework assumes the four gates in Section 1.3 have returned pass. Phases 1 through 3 run once per configuration and produce the search specification. Phases 4 and 5 form the expansion loop, which either reaches an exit condition or returns to Phase 4 with updated state. Phase 6 converts a terminal candidate into a released answer. Phase 7 runs after the response and governs whether the configuration is retained.

### Phase 1: Applicability Gating and Baseline Cost Justification

**Objective**: Establish the decision contract, measure the cheaper alternatives on the same task distribution, and admit tree search only where its verified margin at a matched budget is earned rather than assumed.

**Tier ownership**: Deterministic tier owns the contract record, the budget ledger, and the paired comparison arithmetic; model tier produces only the baseline attempts being measured.

#### Step 1.1: Establish the Decision Contract and Budget Ledger

**Required Actions**:

- Record the objective, output schema, hard constraints, preferences, evidence policy, tool permissions, risk tier, and abstention behaviour before any search component is configured.
- State the acceptance test as a check an external verifier or a named human role can evaluate without interpretation.
- Enter a numeric limit for every bounded dimension: generated nodes, expanded nodes, evaluated nodes, depth, children per expansion, concurrent calls, tokens, tool calls, wall time, and currency cost.
- Define the operational meanings of success, bounded failure, partial completion, and abstention, so that a best-so-far result is reportable rather than forced into a success label.
- Refuse to proceed where any mandatory field is absent, and apply a documented conservative default only where the contract names one.

**Required Outputs**:

- A decision contract record with objective, acceptance test, evidence standard, and risk tier.
- A budget ledger with one numeric limit per bounded dimension.
- A declared abstention and partial-completion behaviour.

**Quality Checkpoints**:

- Every acceptance test returns pass or fail without interpretation; an untestable criterion halts the run before any node is created.
- Every one of the 10 budget dimensions carries a numeric limit; a single unbounded dimension halts the run.
- The contract distinguishes bounded failure from abstention, so an unverified answer is never released as a success.

***

#### Step 1.2: Run the Baseline Ladder and Test the Cost-Justification Inequality

**Required Actions**:

- Run the cheapest deterministic or direct baseline first, and exit immediately where it passes the acceptance test.
- Run a single-chain baseline and a self-consistency baseline over the same task sample, holding the total token budget equal across all arms rather than equal per call.
- Record verified success rate, total tokens, total cost, and p95 latency for every arm on at least 50 paired tasks from the deployment distribution.
- Compute the verified margin of tree search over the best baseline and the marginal search yield in verified successes per additional 1,000 tokens.
- Refuse tree search where the margin is below 5 percentage points, where marginal search yield is not positive, or where self-consistency is within 2 percentage points of tree search at the matched budget.

**Baseline Comparison Ledger**:

| Arm | What is held equal | Metric that decides | Refusal condition |
| :-- | :-- | :-- | :-- |
| Deterministic or direct | Task sample | Verified success rate | Passes the acceptance test; tree search is not run |
| Single chain | Total token budget | Verified success rate | Tree search margin below 5 points |
| Self-consistency | Total token budget | Verified success rate | Tree search within 2 points of it |
| Best-of-N with external selector | Total token budget | Verified success rate | Tree search margin below 5 points |
| Tree search | Total token budget | Marginal search yield | Yield not positive at any tested budget |

**Required Outputs**:

- A paired comparison table covering at least 4 arms over at least 50 tasks.
- A computed verified margin and marginal search yield with the budget at which each was measured.
- A Budget Gate verdict with its reason code.

**Quality Checkpoints**:

- Every arm consumed the same total token budget; an arm compared at an unmatched budget invalidates the comparison and blocks admission.
- The sample size is at least 50 paired tasks; smaller samples are reported as indicative and never used to admit the method.
- The refusal conditions were evaluated and recorded, including where they did not fire.

***

#### Step 1.3: Record the Gate Verdicts and the Search Hypothesis

**Required Actions**:

- Evaluate the Search-Need, Evaluation, Budget, and Safety and Privacy Gates in that order, halting at the first failure.
- Record each verdict with its reason code, the observed evidence, and the alternative route taken on failure.
- State one falsifiable hypothesis naming the reversible decision whose misjudgement causes baseline failure, since tree search recovers only from decisions a backtrack can revisit.
- Bind the run to the alternative named in the routing table where any gate fails, rather than proceeding with a recorded warning.

**Required Outputs**:

- A gate verdict record with 4 entries, each carrying a reason code.
- A stated search hypothesis naming the recoverable decision under test.
- A named routed alternative for every failed gate.

**Quality Checkpoints**:

- All 4 gates carry a recorded verdict; an unevaluated gate blocks execution.
- The search hypothesis names a decision reachable by backtracking; a hypothesis naming an irreversible commitment fails the Search-Need Gate.
- No run proceeds past a failed gate; proceeding with a warning is a defect, not a degraded mode.

***

### Phase 2: State, Thought, and Transition Specification

**Objective**: Fix a canonical state representation, a thought granularity, and a legal-action schema such that any node can be created, validated, evaluated, hashed, and serialised deterministically before a single model call is spent.

**Tier ownership**: Deterministic tier owns the schema, the hash, the validator, and the dry run; model tier contributes nothing until the specification passes its dry run without an LLM in the loop.

#### Step 2.1: Define the Canonical State Schema and Identity Hash

**Required Actions**:

- Specify the state as the minimum sufficient record of what is known and decided, naming its fields, their types, and their normalisation rules.
- Exclude conversation transcripts, phrasing, and generator commentary from state identity, since including them prevents deduplication and lets irrelevant wording change search behaviour.
- Define a deterministic normalisation and hash over the canonical payload, and confirm that two semantically equivalent derivation paths produce one hash.
- Define domain equivalence rules for near-duplicate detection as a strictly second stage, and prohibit merging nodes whose constraints, evidence identifiers, or tool side effects differ.
- Attach provenance to every field sourced externally, recording document, chunk, access-control, timestamp, and content-hash references.

**Required Outputs**:

- A versioned canonical state schema with normalisation rules per field.
- A state identity hash function with a documented collision and equivalence policy.
- A near-duplicate rule stating the conditions under which merging is prohibited.

**Quality Checkpoints**:

- Two hand-constructed equivalent states hash identically, and two states differing in one constraint hash differently.
- No field of state identity derives from free prose or conversation history.
- Every externally sourced field carries provenance; a field without provenance is unusable as evidence in evaluation.

***

#### Step 2.2: Fix Thought Granularity and the Legal-Action Schema

**Required Actions**:

- Choose the largest thought that still permits meaningful partial evaluation and the smallest that avoids token-level micromanagement, starting from natural domain operations such as one transformation, one move, one lemma, one tool-backed subgoal, or one plan decision.
- Reject granularity that produces a near-complete answer in one thought, because early search then cannot redirect the trajectory.
- Reject granularity whose children differ only lexically, because depth grows without adding decision content.
- Define the legal-action schema as structured fields: proposed action, expected successor facts, required evidence or tool, claimed preconditions, and stated uncertainty.
- Validate granularity offline against 4 measurements: successor diversity, evaluator agreement, depth-to-solution, and duplicate-state rate.

**Required Outputs**:

- A declared thought granularity with the domain operation it corresponds to.
- A legal-action schema with 5 structured fields and their validation rules.
- A granularity validation record carrying the 4 offline measurements.

**Quality Checkpoints**:

- Median depth-to-solution on the calibration corpus falls between 3 and 12; below 3 the task is closer to a single decision, and above 12 the branching budget cannot cover the space.
- Duplicate-state rate among generated children is at most 25 percent; above that, granularity is too fine and is coarsened before the run.
- Unique canonical states divided by accepted children is at least 0.60; below that, children are paraphrases and generation is diversified before the run.

***

#### Step 2.3: Compile and Dry-Run the Search Specification

**Required Actions**:

- Compile one specification record naming the initial state, legal transitions, hash, equivalence rule, thought granularity, generator configuration, evaluator rubric, terminal verifier, search policy, priority formula, diversity rule, prune rules, backtrack triggers, termination criteria, and fallback.
- Select the search policy from the selection matrix below and record why the alternatives were rejected.
- Dry-run parsing, transition validation, hashing, serialisation, and budget decrement on synthetic states with no model call in the loop.
- Version every component of the specification, including prompts, rubrics, schemas, policies, retrieval indexes, sandbox images, and model snapshots.
- Refuse to start a run where the dry run cannot create, validate, evaluate, and serialise a node deterministically.

**Search Policy Selection Matrix**:

| Policy | Use when | Dominant failure mode | Required guard |
| :-- | :-- | :-- | :-- |
| Breadth-first | Solutions are shallow and path lengths comparable | Frontier growth exhausts memory and budget | Per-depth cap on retained nodes |
| Depth-first | Memory is tight and constraints expose dead ends fast | One poor first ranking consumes the whole budget | Randomised or diversified child ordering per seed |
| Beam | Staged problems of roughly uniform depth | Discarded states are unrecoverable | Diversity reserve and periodic checkpoint |
| Best-first | Depths vary and scores are calibrated across depths | Fluent partial states outrank viable rougher ones | Depth-aware calibration and novelty term |
| Monte Carlo tree search | Actions carry delayed consequences and rollouts exist | World-model error simulates impossible futures | Bounded rewards, reserved visits, virtual loss |

**Required Outputs**:

- A versioned search specification record with all 15 named components populated.
- A dry-run report confirming deterministic node lifecycle without model calls.
- A policy selection rationale naming the rejected alternatives.

**Quality Checkpoints**:

- The dry run creates, validates, hashes, serialises, and deserialises a node with byte-identical results across 2 executions.
- Every specification component carries a version identifier; an unversioned component blocks the run because its results cannot be attributed later.
- The selected policy's required guard is configured; a policy running without its guard is a specification defect.

***

### Phase 3: Evaluator Construction and Calibration

**Objective**: Construct a layered state evaluator, measure it against known-good outcomes, and admit it only where it clears the four thresholds in Section 1.4, so that expansion effort is allocated by evidence rather than by fluency.

**Tier ownership**: Deterministic tier owns the legality, invariant, and tool layers and the calibration arithmetic; model tier owns only residual criteria no tool can measure; the hybrid handoff is that a model score enters the frontier ordering and a deterministic cut decides what is spent.

#### Step 3.1: Build the Layered Evaluator and the Structured Verdict

**Required Actions**:

- Run deterministic checks first: schema conformance, legality, invariants, access control, and safety. Record every violation with its reason code.
- Run domain tools second, where they exist: compilers, unit tests, symbolic algebra, simulators, database constraints, citation retrieval, or policy engines.
- Invoke model-based scoring third and only for residual criteria the earlier layers cannot measure, so that expensive judgment is never spent on states already proven invalid.
- Emit a structured verdict carrying validity, terminal status, per-criterion scores, uncertainty, evidence identifiers, and a calibrated priority, rather than a single scalar.
- Give the evaluator the canonical state and its evidence only, withholding generator prose, generator identity, and any self-awarded confidence.

**Required Outputs**:

- A three-layer evaluator specification naming which checks run at which layer.
- A structured verdict schema with 6 fields per evaluated node.
- An evaluator context specification stating what the evaluator is not permitted to see.

**Quality Checkpoints**:

- No model-based scoring call is issued for a state already rejected by a deterministic layer; a violation of this ordering is a cost defect.
- A state violating a hard constraint is pruned irrespective of its prose-quality score.
- The evaluator context contains no generator identity, no generator confidence, and no unstructured generator narrative.

***

#### Step 3.2: Calibrate the Evaluator Against Known-Good Outcomes

**Required Actions**:

- Assemble the calibration corpus specified in Section 1.4: at least 50 tasks with verified outcomes and at least 200 labelled sibling comparisons across at least 3 depth bands.
- Construct the oracle labelling by retrospectively marking any node whose descendants contain a verified solution, then compare the production evaluator's ranking against that oracle.
- Measure the four admission thresholds: sibling ranking accuracy, top-k recall at the configured retention width, false-prune rate, and expected calibration error per score bin and depth band.
- Decide between absolute value prompting and pairwise sibling voting by measured calibration, randomising presentation order and blinding generator identity in both.
- Aggregate multiple judgments per node only where measured disagreement exceeds 0.20 on the normalised score, since aggregation otherwise multiplies cost without changing rankings.

**Required Outputs**:

- A calibration report carrying all 4 admission measurements with their depth-band breakdowns.
- An oracle-versus-production ranking comparison over the calibration corpus.
- A scoring-method decision recording why absolute or pairwise scoring was selected.

**Quality Checkpoints**:

- Sibling ranking accuracy is at least 65 percent; below 55 percent the run is routed away from tree search entirely.
- Top-k recall is at least 80 percent and false-prune rate at most 10 percent in every depth band, not only in aggregate.
- Expected calibration error is at most 0.15 in every depth band; where it is not, soft pruning is disabled and the node budget is halved until recalibration completes.

***

#### Step 3.3: Guard Against Collusion and Proxy Overoptimisation

**Required Actions**:

- Test generator-evaluator collusion by swapping generators against blinded evaluators and by normalising state style, and record whether same-family judges favour their own signatures.
- Track proxy overoptimisation by plotting externally verified outcome against internal evaluator value as the node budget rises, and stop increasing exploitation where internal score rises while verified outcomes plateau or fall.
- Cap how strongly the controller exploits small score differences by refusing to act on a score gap smaller than the measured calibration error.
- Retain an untouched outcome set that no rubric revision, prompt change, or threshold adjustment is fitted against.
- Override the model evaluator with a deterministic oracle wherever one exists for the criterion in question.

**Required Outputs**:

- A collusion test report covering at least 2 distinct generator families.
- An internal-value against verified-outcome curve across at least 3 node budgets.
- A declared exploitation cap expressed as a minimum actionable score gap.

**Quality Checkpoints**:

- The evaluator's ranking advantage survives style normalisation; an advantage that disappears under normalisation is a fluency artefact and blocks admission.
- Verified outcome does not decline as internal value rises across the tested budgets; a decline halts budget increases and triggers rubric review.
- No pruning or ordering decision acts on a score gap below the measured calibration error; ties within that band route to the diversity reserve.

***

### Phase 4: Bounded Expansion Under a Declared Budget

**Objective**: Expand the frontier in bounded batches under caps fixed before generation, so that node count, depth, and cost remain governed by the ledger rather than by the apparent promise of the tree.

**Tier ownership**: Deterministic tier owns frontier selection, lease management, transition validation, hashing, node accounting, and every budget decrement; model tier owns candidate proposal and residual scoring; the handoff is that a proposal becomes a node only after the validator accepts it and the ledger admits its cost.

#### Step 4.1: Initialise the Frontier and the Node Ledger

**Required Actions**:

- Create the root node from sanitised inputs and provenance-linked evidence, and evaluate root feasibility before any expansion.
- Return the root immediately where it is terminal and passes the external verifier, spending no search budget.
- Abstain or retrieve permitted evidence where the root is invalid or unsupported, rather than expanding an unsupported state.
- Initialise every counter in the budget ledger to its declared cap and bind decrements to an atomic operation shared across all concurrent workers.
- Declare the branching factor, depth bound, retention width, diversity reserve size, and total node budget as immutable for the run, and record them in the trace before the first expansion.

**Required Outputs**:

- A root node record with provenance-linked evidence and a feasibility verdict.
- An initialised budget ledger with atomic decrement semantics.
- An immutable bound declaration covering branching, depth, retention width, reserve size, and node budget.

**Quality Checkpoints**:

- The declared bounds are written to the trace before the first child is generated; bounds set after generation begins invalidate the run's cost accounting.
- Concurrent workers cannot jointly exceed any cap, verified by an atomic-decrement test under the configured concurrency.
- A terminal, verified root exits without expansion; expanding a solved root is a cost defect.

***

#### Step 4.2: Select Work and Generate Validated Children

**Required Actions**:

- Select up to the concurrency cap from the frontier using the configured policy, acquire a node lease per selection, and apply virtual loss where Monte Carlo tree search is in use.
- Skip nodes already terminal, superseded, leased, or over their local caps, so that parallel workers do not duplicate expansion.
- Request no more than the node's remaining branch allowance, beginning at 2 or 3 children per selected node and raising toward a maximum of 5 only where sibling diversity is low, top scores are within the calibration error, and the ledger supports it.
- Parse proposals against the legal-action schema, sanitise untrusted content, apply the transition, run deterministic checks, compute canonical hashes, and attach evidence and tool requirements.
- Retry malformed model output at most once per node, then mark the parent exhausted; drop invalid, illegal, duplicate, unsafe, and no-op children while logging a reason code for each, and never charge a rejected proposal as a successful expansion.

**Required Outputs**:

- An expansion batch with one lease per selected node.
- A set of validated unique children with canonical hashes and attached evidence references.
- A rejection log with one reason code per discarded proposal.

**Quality Checkpoints**:

- Branching never exceeds 5 children per expansion, and the raise conditions are recorded whenever branching exceeds 3.
- Every accepted child passed the deterministic transition validator; a child admitted on model assertion alone is a tier violation.
- Malformed output is retried at most 1 time per node; a second malformed response exhausts the parent rather than looping.

***

#### Step 4.3: Evaluate, Order, and Account for the Batch

**Required Actions**:

- Run the layered evaluator on each validated child in the cheapest-first order specified in Step 3.1.
- Run the independent terminal verifier for any child claiming terminal status, and treat the claim as inert until the verifier returns.
- Convert verified outcomes or calibrated estimates into bounded rewards and back them up through immutable ancestor links where Monte Carlo tree search is in use, recording normalisation, discounting, and backup semantics.
- Decrement every affected ledger dimension atomically as each call completes, counting evaluator and controller overhead against the run rather than treating it as free.
- Order the frontier by the priority formula, combining value, path cost, uncertainty, novelty, and a depth penalty as declared in the specification.

**Required Outputs**:

- A structured verdict per child with validity, terminal status, per-criterion scores, uncertainty, evidence, and priority.
- An updated budget ledger with per-dimension consumption and remaining headroom.
- A reordered frontier with the priority key recorded per node.

**Quality Checkpoints**:

- Every child carries all 6 verdict fields; a child missing a field is not enqueued.
- Evaluation and controller cost appear in the ledger; overhead excluded from accounting invalidates the marginal search yield computed in Phase 7.
- The frontier ordering is reproducible from the recorded priority keys; an ordering that cannot be reconstructed blocks the oracle-gap decomposition in Step 7.2.

***

### Phase 5: Pruning, Backtracking, and Bounded Termination

**Objective**: Remove branches under stated numeric rules, return control to the frontier rather than loop inside a failing branch, and terminate on a declared exit condition that yields either a verified answer or a best-so-far result with its evidence.

**Tier ownership**: Deterministic tier owns prune execution, reinstatement accounting, lineage invalidation, and the stopping rule; model tier supplies only the value estimates that soft pruning consumes.

#### Step 5.1: Execute Hard and Soft Pruning With Reason Codes

**Required Actions**:

- Hard-prune immediately and irreversibly for illegal transitions, invariant violations, unauthorised actions, exact duplicate hashes, confirmed contradiction with trusted evidence, and proven infeasibility.
- Soft-prune a state only after the evaluator has cleared the admission bar, and only where its value falls below the retention cut by more than the measured calibration error.
- Retain a diversity reserve sized at no less than 20 percent of the retention width and no fewer than 2 nodes, selected for novelty and uncertainty rather than for value.
- Record a reason code, the score at the time of pruning, the lineage, and the disposition for every pruned node, and never delete the record needed to diagnose the prune.
- Disable soft pruning entirely where expected calibration error exceeds 0.15 in the relevant depth band, leaving only hard prunes in force.

**Prune and Reinstatement Rules**:

| Prune class | Trigger | Reversible | Reinstatement limit |
| :-- | :-- | :-- | :-- |
| Illegality | Transition validator rejects the action | No | Not applicable |
| Invariant violation | Hard constraint broken by the successor state | No | Not applicable |
| Duplicate | Canonical hash already present in the tree | No | Not applicable |
| Evidence contradiction | Trusted source contradicts a state assertion | No | Not applicable |
| Infeasibility | No legal action exists from the state | No | Not applicable |
| Low value | Score below the retention cut by more than 0.15 | Yes | 1 reinstatement per node |
| Beam overflow | Retention width exceeded at the depth | Yes | 1 reinstatement per node |
| Stagnant subtree | 3 expansions without measurable progress | Yes | 1 reinstatement per node |

**Required Outputs**:

- A prune log with one reason code, score, and lineage entry per pruned node.
- A populated diversity reserve meeting the declared size floor.
- A soft-pruning enablement flag recording whether calibration permitted it.

**Quality Checkpoints**:

- No node is soft-pruned on a score gap at or below 0.15; gaps inside the calibration error route to the reserve instead.
- The diversity reserve is at least 20 percent of the retention width and at least 2 nodes at every depth; a smaller reserve is a configuration defect.
- Every pruned node retains its record; deletion of a pruned branch blocks the false-prune measurement in Step 7.2.

***

#### Step 5.2: Backtrack and Govern Reinstatement

**Required Actions**:

- Backtrack when a terminal verifier fails, a branch has no legal actions, a new observation invalidates an ancestor assumption, two consecutive expansions produce no measurable progress, or the branch reaches its local cap.
- Return control to the frontier rather than asking the same node to self-correct, since repeated self-correction inside one branch reproduces the failure that search exists to escape.
- Invalidate descendants when an ancestor state changes, cancel their in-flight work, and append a superseding state rather than editing history in place.
- Reinstate a soft-pruned or reserve node only where the best verified progress has not improved over the last 3 expansion rounds, or where a new observation invalidated the ancestor that outranked it.
- Permit at most 1 reinstatement per node; a node reinstated once and pruned again becomes a hard prune with the reason code recorded.

**Required Outputs**:

- A backtrack log with one trigger and reason code per event.
- A supersession record preserving lineage for every invalidated ancestor.
- A reinstatement ledger recording each node's single permitted revisit.

**Quality Checkpoints**:

- No node is reinstated more than 1 time; a second reinstatement is a control defect and halts the run.
- Descendant invalidation cancels in-flight work within the same expansion round; work continuing on an invalidated subtree is wasted budget.
- No state record is edited in place; history rewriting blocks replay and invalidates the trace.

***

#### Step 5.3: Enforce the Stopping Rule and the Exhaustion Policy

**Required Actions**:

- Terminate successfully only where the goal test and every mandatory external check pass; a high evaluator score never terminates a run.
- Terminate with an empty-frontier exit where no expandable node remains, reporting no solution found under the specification.
- Terminate on resource exhaustion where any declared cap on nodes, expansions, depth, children, tokens, tool calls, wall time, or cost is reached, and never reset a counter after a backtrack.
- Terminate for stagnation where the best externally verified score improves by less than 0.02 on the normalised scale over 3 consecutive expansion rounds and no reserve node exceeds the novelty threshold of 0.30 pairwise state dissimilarity.
- Return, on every non-success exit, the best externally verified partial result with its evidence, its stated uncertainty, the exact limiting condition, and the reason code; never relabel the highest heuristic score as a success.

**Required Outputs**:

- A termination record naming the exit condition, its reason code, and the ledger state at exit.
- A best-so-far result package with evidence, uncertainty, and limiting condition on every non-success exit.
- A counter audit confirming no cap was reset during the run.

**Quality Checkpoints**:

- Exactly 1 exit condition is recorded per run; a run closing without a declared exit is a control defect.
- Every non-success exit carries a best-so-far package including uncertainty; a bare failure message is an incomplete output.
- No counter was reset after backtracking, verified against the atomic ledger history.

***

### Phase 6: External Verification and Response Construction

**Objective**: Establish that the selected leaf is correct by a check outside the generating model, then release only what the disclosure boundary permits.

**Tier ownership**: Hybrid, with authority held by the verifier; the model may compose the response but may not certify it, and the deterministic tier gates release on schema, privacy, and policy checks.

#### Step 6.1: Verify the Selected Leaf Outside the Generating Model

**Required Actions**:

- Submit the highest-priority terminal candidate to a verifier that shares neither model weights nor prompt template with the generator and the evaluator, since a shared model carries shared blind spots.
- Prefer a deterministic verifier where the domain admits one: an executable test, a constraint solver, a recomputation, a schema validator, or a primary-source retrieval that confirms every material claim.
- Where no deterministic verifier exists, require an independent model of a different family under a blinded rubric plus at least 1 external evidence source, and record the arrangement as weaker verification in the trace.
- Treat agreement between the evaluator and the verifier as correlated where they share a base model, and record the correlated-failure reason code rather than counting the agreement as confirmation.
- Return the run to Phase 5 for backtracking on verification failure, recording the failure against the branch rather than requesting self-correction from the same node.

**Required Outputs**:

- A verification record naming the verifier, its independence class, and its verdict.
- An independence assessment stating whether verifier and generator share weights, prompts, or evidence.
- A backtrack event where verification failed, carrying the failing check.

**Quality Checkpoints**:

- The verifier shares no model weights and no prompt template with the generator; a shared-model verifier is recorded as weaker verification and never satisfies a high-risk acceptance test.
- No answer is released on evaluator score alone; the evaluator's ordering role does not extend to authorisation.
- Every verification failure produces a backtrack event rather than an in-branch retry.

***

#### Step 6.2: Construct the Disclosure-Bounded Response

**Required Actions**:

- Return the verified answer, its material evidence, its stated uncertainty, and a concise search summary limited to branches explored, checks passed, and budget consumed.
- Withhold unrestricted intermediate reasoning, sensitive node payloads, security deliberation, and any adversarial instruction encountered inside retrieved content.
- Attach the exact limiting condition and the reason code where the response carries a best-so-far result rather than a verified success.
- Run output schema, privacy classification, citation, and policy checks before release, and block release on any failure.
- Record the released artifact's hash and its retention class so that later deletion propagates to every derived record.

**Required Outputs**:

- A released response conforming to the declared output schema.
- A search summary carrying branch, check, and budget counts without node payloads.
- A release record with artifact hash, retention class, and policy check results.

**Quality Checkpoints**:

- No unrestricted intermediate reasoning appears in the released response; a disclosure breach blocks release and triggers re-instrumentation.
- Every material claim in the response carries an evidence identifier or an explicit unsupported marker.
- A best-so-far response states its limiting condition; a partial result presented without one is a reporting defect.

***

### Phase 7: Measurement Against Baselines and Policy Correction

**Objective**: Recompute the method's justification from the run trace, attribute failure to generation, evaluation, or scheduling, and correct the configuration or withdraw the method.

**Tier ownership**: Deterministic tier owns metric computation, the oracle decomposition, and the promotion gate; model tier contributes only to human-reviewed adjudication samples.

#### Step 7.1: Compute the Search-Quality and Efficiency Metric Set

**Required Actions**:

- Compute verified success rate stratified by task class, difficulty band, model, algorithm, and budget, reporting median, p90, p95, and p99 latency and cost rather than means alone.
- Compute nodes generated, nodes expanded, valid-child rate, duplicate rate, mean and maximum depth, frontier peak, backtrack count, tokens, tool calls, and cost per attempted task and per solved task.
- Compute branch efficiency as verified solution-path edges over all expanded edges, and report the complementary wasted-expansion share.
- Compute budget utilisation per cap as actual use over authorised use, and compute marginal search yield against the cheapest adequate baseline at matched budget.
- Compute branch diversity from unique canonical states over accepted children, and search concentration from the expansion share of the most-visited subtree.

**Required Outputs**:

- A stratified quality and efficiency report with tail percentiles.
- A branch efficiency figure with the wasted-expansion share.
- A recomputed marginal search yield against the current baseline.

**Quality Checkpoints**:

- Marginal search yield remains positive; a non-positive yield withdraws the Budget Gate pass and routes subsequent runs to the baseline.
- Branch efficiency is at least 0.15; below that, more than 85 percent of expansions were wasted and branching or evaluation is corrected before the configuration continues.
- Search concentration is below 0.70 while branch diversity is at least 0.60; concentration above 0.70 with diversity below 0.60 indicates generator collapse or over-exploitation.

***

#### Step 7.2: Decompose the Oracle-Versus-Realised Gap

**Required Actions**:

- Compute oracle coverage by retrospectively marking any generated node lying on a verified solution path, using the retained prune records.
- Compute realised success separately, and take the oracle gap as coverage minus realised success.
- Decompose the gap into evaluator-pruning loss, scheduling loss, and budget loss using lineage, prune reason codes, and retrospective expansion of pruned subtrees.
- Route the correction by the dominant loss term: fix generation where successful subtrees never appear, fix evaluation or the diversity reserve where they appear and are pruned, and fix scheduling or budgets where they appear, rank well, and remain unexpanded.
- Compute top-k evaluator recall, ranking correlation with eventual outcome, false-prune rate, and calibration error by score bin and depth on production traces, not only on the calibration corpus.

**Required Outputs**:

- An oracle gap figure with its three-way decomposition.
- A named dominant loss term with the correction it routes to.
- A production-trace recomputation of the 4 admission measurements.

**Quality Checkpoints**:

- The three loss terms account for at least 90 percent of the oracle gap; an unexplained remainder above 10 percent indicates missing lineage and blocks the correction decision.
- Production-trace admission measurements are compared against the calibration corpus; a drop of more than 10 percentage points in any measurement triggers recalibration.
- The correction routed matches the dominant loss term; correcting evaluation where generation is the dominant loss is a misattribution defect.

***

#### Step 7.3: Run Robustness Trials and Issue a Policy Correction

**Required Actions**:

- Repeat each evaluated configuration across at least 5 preregistered seeds, reporting mean, standard deviation, worst-seed score, best-minus-worst range, and flip rate.
- Perturb prompts, option order, irrelevant context, evidence order, evaluator order, timeouts, and injected instructions, and report degradation and safety violations per perturbation class.
- Compare generator-only, evaluator-only, and full-system changes on identical examples, so that an improvement is attributed to the component that produced it.
- Queue failed, expensive, safety-relevant, high-disagreement, and large-oracle-gap cases for offline human review, and record adjudication outcomes rather than model-written lessons.
- Promote a configuration only on a paired, budget-matched comparison against the cheaper baselines; withdraw the method where the margin has fallen below 5 percentage points since admission.

**Required Outputs**:

- A seed-variance report over at least 5 seeds per configuration.
- A perturbation report covering all 7 perturbation classes.
- A promotion or withdrawal decision with its supporting paired comparison.

**Quality Checkpoints**:

- The robustness gap between clean and perturbed conditions is at most 20 percentage points; a larger gap blocks promotion.
- No promotion rests on a single seed or an unpaired benchmark score; unpaired evidence is recorded as indicative only.
- Model-generated lessons are never written to shared configuration without adjudication; automatic promotion of a self-authored lesson is a governance defect.

***

## III. Implementation Guidance for AI Agents

AI agents operating a tree-of-thought search must follow systematic protocols ensuring that search bookkeeping stays deterministic, that model judgment orders work without authorising it, and that every run terminates on a declared exit condition. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Gate Agent**: Evaluates the four gates in Section 1.3 and returns invoke, a named alternative, or abstain. Owns the cost-justification arithmetic and may refuse the method outright.
2. **Specification Agent**: Owns the canonical state schema, legal-action schema, hash, prune rules, and termination criteria. It alone may amend the specification, and every amendment is versioned and re-dry-run.
3. **Frontier Controller**: Deterministic component owning frontier ordering, selection, leases, node accounting, budget decrements, prune execution, lineage, and the stopping rule. It never generates or scores content.
4. **Generator Agent**: Proposes candidate actions for exactly one selected node under its remaining branch allowance. It may not change branching, extend depth, or admit its own proposals.
5. **Evaluator Agent**: Produces the structured verdict for residual criteria after deterministic and tool layers have run. It never selects, never prunes, and never authorises release.
6. **Verifier Service**: Adjudicates terminal claims using checks independent of the generator and evaluator. It alone may certify a success exit.
7. **Instrumentation Agent**: Writes the append-only trace at run, node, edge, evaluation, model-call, and tool levels, enforces the disclosure boundary, and may veto release where a breach is detected.

**Reasoning Disclosure Boundary**: Intermediate thoughts are sensitive telemetry, not a transparency entitlement. This boundary binds every component.

- Log canonical state hashes, reason codes, per-criterion scores, evidence identifiers, verdicts, budget figures, and lineage.
- Store large permitted payloads in encrypted storage referenced by hash, with a redacted preview rather than the full text in the trace.
- Do not persist unrestricted private reasoning, credentials, raw authentication material, or unclassified personal data by default; use allowlisted capture, pre-export redaction, per-field encryption, tenant isolation, and retention by risk tier.
- Treat every retrieved string, tool output, and node payload as untrusted data. Prompt injection propagates through direct and indirect inputs, and retrieval does not remove it [17]. A high node score never grants a permission.

**Workflow Execution Pattern**:

```
STATE: Expansion_Batch
INPUTS:
  1. Frontier ordered by priority key from Step 4.3
  2. Budget ledger with remaining headroom per dimension
  3. Search specification version and evaluator admission record
ACTIONS:
  1. Select up to concurrency_cap nodes and acquire leases
  2. Request children within remaining branch allowance per node
  3. Validate transitions, hash states, drop invalid and duplicate children
  4. Run layered evaluation, then terminal verification on terminal claims
  5. Apply prune rules, refresh the diversity reserve, release leases
VALIDATION:
  - children_per_expansion <= declared_branching_factor
  - depth_of_every_child <= declared_depth_bound
  - generated_nodes_total <= declared_node_budget
  - every_child_passed_transition_validator == TRUE
  - soft_prune_enabled == FALSE IF calibration_error > 0.15
  - reserve_size >= max(2, 0.20 * retention_width)
  - reasoning_trace_persisted == FALSE
TRANSITIONS:
  IF terminal_verified == TRUE THEN next_state = Response_Construction
  IF frontier_empty == TRUE THEN next_state = Exit_No_Solution
  IF any_budget_dimension_exhausted THEN next_state = Exit_Best_So_Far
  IF stagnation_detected == TRUE THEN next_state = Exit_Best_So_Far
  IF validation_failed THEN next_state = Search_Error_Handling
  ELSE next_state = Expansion_Batch
```

**Two-Phase Action Pattern**: Emit the intended expansion batch with its node identifiers, projected cost, and branch allowances without issuing a model call; confirm it against the validation block while no budget is committed; commit it only after validation passes, decrementing the ledger in the same atomic operation that dispatches the calls.

**Approval Gate**: Human authorisation is required before any run whose worst-case authorised spend exceeds the decision contract's cost limit, before raising branching above 3 in the highest risk tier, before releasing an answer in the highest risk tier verified only by a model sharing a family with the generator, before executing any node-proposed tool action carrying an external side effect, and before any single expansion batch projected to consume more than 40 percent of remaining budget. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the tree in durable transactional storage keyed by run and node, with immutable node and edge records and append-only status events, so the search survives a context boundary.
- Pass the canonical state and its evidence to model calls, never the accumulated conversation, so that context consumption stays flat in depth rather than growing with path length.
- Cache model calls by normalised prompt, model snapshot, parameters, tool schema, and evidence version, and never reuse a cached judgment across a changed policy, rubric, or fact.
- Count controller, evaluator, and instrumentation context consumption against the run budget rather than treating it as free.
- Write a handoff record naming the specification version, ledger state, frontier, reserve, and exit conditions at every context boundary.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract and Justification Integrity (After Phase 1)**

- **Automated Check**: Every acceptance test is machine-evaluable or assigned to a named role; all 10 budget dimensions carry numeric limits; the paired comparison covers at least 4 arms over at least 50 tasks at a matched token budget; the verified margin is at least 5 percentage points.
- **Agent Action on Pass**: Proceed to specification.
- **Agent Action on Failure**: Halt and route to the baseline named in the gate routing table; no search budget is spent against an unjustified method.
- **Human Review Trigger**: A verified margin between 3 and 5 percentage points, or any task in the highest risk tier.

**Checkpoint 2: Specification Determinism (After Phase 2)**

- **Automated Check**: The dry run creates, validates, hashes, serialises, and deserialises nodes identically across 2 executions with no model call; all 15 specification components are populated and versioned; duplicate-state rate is at most 25 percent.
- **Agent Action on Pass**: Proceed to evaluator construction.
- **Agent Action on Failure**: Halt; a non-deterministic node lifecycle makes every later measurement unattributable.
- **Human Review Trigger**: Median depth-to-solution outside the 3 to 12 band on the calibration corpus.

**Checkpoint 3: Evaluator Admission (After Phase 3)**

- **Automated Check**: Sibling ranking accuracy at least 65 percent; top-k recall at least 80 percent; false-prune rate at most 10 percent; expected calibration error at most 0.15 in every depth band; the collusion test survives style normalisation.
- **Agent Action on Pass**: Proceed to expansion with soft pruning enabled.
- **Agent Action on Failure**: Route to independent sampling with external verification where ranking accuracy is below 55 percent; otherwise run with soft pruning disabled and the node budget halved.
- **Human Review Trigger**: Any threshold missed by more than 10 percentage points, or a ranking advantage that disappears under style normalisation.

**Checkpoint 4: Expansion Bound Integrity (After Phase 4)**

- **Automated Check**: Children per expansion at most 5; depth within the declared bound; generated nodes within the node budget; every accepted child passed the transition validator; every child carries all 6 verdict fields.
- **Agent Action on Pass**: Proceed to pruning and termination control.
- **Agent Action on Failure**: Cancel the batch, release leases, and restore the ledger to its pre-batch state before retrying with corrected bounds.
- **Human Review Trigger**: More than 20 percent of proposals rejected by the transition validator across 3 consecutive batches.

**Checkpoint 5: Prune and Termination Validity (After Phase 5)**

- **Automated Check**: No soft prune on a score gap at or below 0.15; diversity reserve at or above the floor at every depth; at most 1 reinstatement per node; exactly 1 recorded exit condition; no counter reset after a backtrack.
- **Agent Action on Pass**: Proceed to verification.
- **Agent Action on Failure**: Halt the run; an invalid prune or termination is never executed with a warning attached.
- **Human Review Trigger**: A run exiting on stagnation with oracle-positive nodes present in the reserve.

**Checkpoint 6: Verification and Release (After Phase 6)**

- **Automated Check**: The verifier shares no weights and no prompt template with the generator; every material claim carries an evidence identifier or an unsupported marker; output schema, privacy, citation, and policy checks pass; no unrestricted reasoning appears in the release.
- **Agent Action on Pass**: Release the response and close the run.
- **Agent Action on Failure**: Block release, backtrack on verification failure, and re-instrument on a disclosure breach.
- **Human Review Trigger**: Any highest-risk-tier answer resting on a same-family verifier, or any detected disclosure breach.

**Checkpoint 7: Measurement and Promotion (After Phase 7)**

- **Automated Check**: Marginal search yield positive; branch efficiency at least 0.15; the three loss terms account for at least 90 percent of the oracle gap; at least 5 seeds and all 7 perturbation classes covered; robustness gap at most 20 percentage points.
- **Agent Action on Pass**: Promote the configuration and record its supporting paired comparison.
- **Agent Action on Failure**: Withhold promotion and name the missing evidence; a configuration is never promoted on clean-condition, single-seed, or unpaired results.
- **Human Review Trigger**: A verified margin that has fallen below 5 percentage points since admission, or any recorded safety violation during perturbation testing.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
SPECIFICATION_VERSION:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Evaluator Noise Prunes the Only Viable Branch**

- **Symptoms**: Oracle coverage substantially exceeds realised success; pruned subtrees contain verified solution paths; false-prune rate rises with depth.
- **Diagnostic Steps**: Retrospectively expand pruned subtrees from the retained records, recompute top-k recall and calibration error per depth band, and confirm whether the losses concentrate in one band.
- **Resolution Protocol**: Option A, enlarge the diversity reserve to at least 40 percent of the retention width. Option B, disable soft pruning and run with hard prunes only until recalibration completes. Option C, raise the minimum actionable score gap above the measured calibration error. Option D, replace absolute scoring with blinded pairwise sibling voting.
- **Escalation Trigger**: An evaluator-pruning loss above 30 percent of the oracle gap across 3 consecutive measurement windows withdraws the Evaluation Gate pass; the method is suspended for that task class pending recalibration.

**Error Type 2: Generator-Evaluator Collusion**

- **Symptoms**: Persuasive shared mistakes rank highest; the evaluator's advantage disappears under style normalisation; same-family judges prefer their own verbose signatures; confidence rises without new evidence.
- **Diagnostic Steps**: Swap generator families against blinded evaluators, normalise state style, and determine whether the ranking advantage survives both changes independently.
- **Resolution Protocol**: Option A, blind generator identity and withhold generator confidence from the evaluator context. Option B, replace the evaluator with a different model family. Option C, move the deciding criterion to a deterministic tool where one exists. Option D, retain an independent outcome verifier and demote the model evaluator to ordering only.
- **Escalation Trigger**: A high-risk conclusion resting on agreement that fails the independence test escalates immediately; this class is never resolved by adding more judgments from the same family.

**Error Type 3: Search Explosion and Budget Overrun**

- **Symptoms**: Frontier peak grows monotonically; branching and depth compound; concurrent workers expand duplicates; cost rises while verified progress stays flat.
- **Diagnostic Steps**: Compare consumption per dimension against the declared caps, locate the overrun in generation, evaluation, tool calls, or controller overhead, and check lease and virtual-loss coverage under the configured concurrency.
- **Resolution Protocol**: Option A, reduce branching to 2 and enforce a per-depth retention cap. Option B, enable difficulty routing so that easy cases exit after the baseline and unsupported cases abstain. Option C, cancel all descendants immediately on verified success rather than draining in-flight work. Option D, tighten deduplication by lowering the near-duplicate threshold at the same constraint set.
- **Escalation Trigger**: Any hard cap breached during a run halts the run and blocks the configuration; budget overrun is never resolved by raising the cap mid-run.

**Error Type 4: Heuristic Trap and World-Model Hallucination**

- **Symptoms**: Fluent but unfinishable states repeatedly outrank rougher viable paths; simulated rollouts describe outcomes the environment cannot produce; verified terminal checks fail at high evaluator confidence.
- **Diagnostic Steps**: Compare evaluator scores against terminal outcomes by depth band, and compare simulated observations against real environment feedback on a sample of at least 20 rollouts.
- **Resolution Protocol**: Option A, add invariant and terminal feasibility checks at every depth rather than only at leaves. Option B, apply depth-aware calibration so scores are comparable across depths. Option C, add a novelty term to the priority formula and reserve visits for unexplored children. Option D, switch to shallower planning with real observations where world-model error compounds faster than search improves outcomes.
- **Escalation Trigger**: Simulated and real observations diverging on more than 20 percent of sampled rollouts suspends rollout-based value estimation for that environment.

**Error Type 5: Injection Propagating Through Node Content**

- **Symptoms**: Instructions appear inside retrieved content, observations, or node payloads; a descendant attempts an unauthorised tool action; an evaluator context contains directive text originating outside the specification.
- **Diagnostic Steps**: Trace the directive text to its originating node and evidence identifier, and determine which descendants and evaluations inherited it.
- **Resolution Protocol**: Option A, quarantine the originating node, invalidate its descendants, and re-expand from the nearest clean ancestor. Option B, enforce instruction-data separation by passing retrieved content only as typed evidence fields. Option C, move tool authorisation entirely outside the model so node content cannot grant permission. Option D, sanitise evaluator context to canonical state and evidence identifiers only.
- **Escalation Trigger**: Any executed tool action traceable to injected content stops the loop immediately and enters incident handling; the run is not resumed.

**Error Type 6: Cost Without Margin**

- **Symptoms**: Marginal search yield falls to zero or below; the baseline matches tree search at the same token budget; branch efficiency falls below 0.15; wasted-expansion share exceeds 85 percent.
- **Diagnostic Steps**: Re-run the paired budget-matched comparison on current traffic, and decompose the oracle gap to determine whether the loss is generation, evaluation, or scheduling.
- **Resolution Protocol**: Option A, reduce the node budget to the smallest setting that preserved the margin historically. Option B, restrict tree search to the difficulty band where the margin was measured and route the remainder to the baseline. Option C, withdraw the method for the task class and adopt the cheaper baseline. Option D, replace external search with a direct reasoning-model attempt where a single response already passes the verifier within budget.
- **Escalation Trigger**: A verified margin below 5 percentage points on 2 consecutive measurement windows withdraws the Budget Gate pass; the method is not retained on the expectation that a future configuration will recover it.

**Troubleshooting Decision Tree**:

```
RUN FAILS OR RETURNS AN UNJUSTIFIED RESULT
├─ SELECTION DEFECT
│   ├─ Oracle-positive nodes pruned → Enlarge reserve; disable soft prune; recalibrate
│   ├─ Oracle-positive nodes ranked well but unexpanded → Fix scheduling or raise node budget
│   └─ Oracle-positive nodes never generated → Fix generation: diversity, granularity, prompts
├─ EVIDENCE DEFECT
│   ├─ Evaluator and generator share a model family → Demote to ordering; add external verifier
│   ├─ Terminal claim released without verification → HALT release; backtrack and re-verify
│   └─ Agreement shares one premise → Record correlated failure; commission a different check
├─ BUDGET DEFECT
│   ├─ Hard cap breached mid-run → HALT; block configuration; never raise the cap in flight
│   ├─ Marginal yield not positive → Withdraw Budget Gate pass; route to the baseline
│   └─ Wasted-expansion share above 85 percent → Reduce branching; enforce per-depth caps
├─ CONTROL DEFECT
│   ├─ No declared exit condition recorded → HALT; classify as bounded failure
│   ├─ Counter reset after backtracking → Restore ledger; invalidate the run's cost figures
│   └─ Node reinstated more than once → HALT; hard-prune the node and record the code
└─ SAFETY DEFECT
    ├─ Injected instruction executed a tool → STOP; incident handling; run not resumed
    ├─ Unrestricted reasoning found in release → Block release; purge and re-instrument
    └─ Sensitive payload retained beyond class → Replace with hash reference; propagate deletion
```

### D. Performance Metrics and Continuous Learning

**Search Quality Metrics**:

- **Verified success rate**: Runs whose released answer passed the terminal verifier, stratified by task class and difficulty band (target: at least 5 percentage points above the best baseline at a matched token budget).
- **Top-k evaluator recall**: Oracle-positive children retained within the top k at the configured retention width (target: at least 80 percent; below 70 percent suspends soft pruning).
- **False-prune rate**: Oracle-positive nodes falling below the retention cut (target: at most 10 percent in every depth band).
- **Oracle gap**: Oracle coverage minus realised success (target: at most 15 percentage points; a larger gap routes correction by its dominant loss term).

**Efficiency Metrics**:

- **Branch efficiency**: Verified solution-path edges over all expanded edges (target: at least 0.15; below that, more than 85 percent of expansions were wasted).
- **Marginal search yield**: Additional verified successes per additional 1,000 tokens over the cheapest adequate baseline (target: positive at every tested budget).
- **Budget utilisation**: Actual use over authorised use per cap (target: between 0.40 and 0.95; below 0.40 the caps are over-provisioned and the comparison is unmatched).
- **Duplicate rate**: Duplicate canonical states among generated children (target: at most 25 percent; above that, granularity or deduplication is corrected).
- **Controller overhead**: Controller, evaluator, and instrumentation cost over total run cost (target: at most 40 percent; above that triggers policy review).

**Robustness and Calibration Metrics**:

- **Seed variance**: Best-minus-worst success across at least 5 preregistered seeds (target: at most 15 percentage points).
- **Robustness gap**: Success difference between clean and perturbed conditions across all 7 perturbation classes (target: at most 20 percentage points; a larger gap blocks promotion).
- **Expected calibration error**: Measured per score bin and per depth band (target: at most 0.15; above that disables soft pruning).
- **Search concentration**: Expansion share of the most-visited subtree (target: below 0.70 where branch diversity is at least 0.60).

**Log-Pattern Failure Detection**: A rising frontier peak with flat verified progress indicates search explosion. High evaluator scores followed by terminal verification failures indicate a heuristic trap. Low branch diversity with high search concentration indicates generator collapse. Repeated identical canonical hashes across workers indicates lease or virtual-loss failure. Internal value rising while verified outcomes plateau indicates proxy overoptimisation and stops further budget increases. Directive text appearing in evaluator contexts indicates injection propagation and quarantines the originating subtree.

**Learning and Adaptation Mechanisms**:

- **Adjudicated cases only**: Queue failed, expensive, safety-relevant, high-disagreement, and large-oracle-gap runs for human review, and record adjudicated outcomes rather than model-authored lessons.
- **Paired promotion**: Promote a search-policy change only after a paired, budget-matched comparison against the cheaper baselines on held-out tasks.
- **Component attribution**: Evaluate generator-only, evaluator-only, and full-system changes on identical examples, so an improvement is attributed to the component that produced it.
- **Threshold recalibration**: Recompute every threshold per task class; the values stated in this guide are deployment defaults, not measured constants.

**Human-in-the-Loop Boundaries**: Amendment of a hard constraint, release of a highest-risk-tier answer verified only by a same-family model, promotion of a configuration whose advantage appears only under clean conditions, authorisation of a node-proposed tool action with an external side effect, and relaxation of the disclosure boundary are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how search over partial solutions is bounded, scored, and verified rather than what any particular solution contains. Its phases hold wherever a task exposes informative partial states, admits legal transitions between them, and carries an external check on completion.

### 4.1 Cross-Domain Application Patterns

**Software engineering with executable checks**: The canonical state is a patch hash with test results and unresolved failures, and the legal actions are bounded edits. The deterministic tier is unusually strong here because compilation and test execution supply an exact terminal verifier and a partial-progress signal, so the evaluator carries less weight and the admission bar is easier to clear. Branching stays at 2 or 3, depth tracks the number of distinct failing assertions, and every prune of a failing branch is a hard prune backed by a test result. The dominant risk is search explosion across a large edit space, controlled by difficulty routing and immediate cancellation on a passing suite.

**Scientific design and optimisation**: The canonical state is a candidate design with its evaluated properties, constraints, and provenance-linked measurements. Simulation supplies a partial-value signal, but simulation error is a world-model hallucination risk, so rollout-based estimates are checked against real measurements on a sample and suspended where divergence exceeds 20 percent. The oracle analysis is affordable because verified outcomes accumulate slowly and can be reused across configurations. Backtracking matters more than branching here, since a promising design family is frequently abandoned and later reinstated by a new measurement.

**Regulated investigation and evidence analysis**: The canonical state is a set of established findings, outstanding questions, and evidence identifiers with access-control provenance. Actions are alternative evidence routes rather than answer attempts, and the terminal verifier is a primary-source confirmation for every material claim. Risk is high and most conclusions are difficult to retract, so the approval gate binds before release, the reserve is enlarged to preserve dissenting lines of inquiry, and the trace becomes a deliverable rather than a diagnostic aid.

**Operations and logistics planning**: The canonical state carries achieved commitments, outstanding constraints, resource consumption, and reversibility class per action. Reversibility varies within one run, since a provisional allocation is reversible while a dispatched shipment is not, so verification thresholds bind per action class rather than per run. Latency dominates the stopping decision, because a marginally better plan delivered late is worth less than an adequate plan delivered on time, and stagnation exits are common and expected.

**Interactive agents in feedback environments**: The canonical state carries environment observations, achieved predicates, and tool side effects. Real observations replace simulated rollouts wherever they are affordable, since environment feedback is the only signal not subject to the generator's blind spots. Node-proposed tool actions pass authorisation outside the model, and any action with an external side effect halts at the approval gate. Depth is bounded tightly because side effects accumulate and backtracking cannot undo them.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk reversible work**: Collapse to branching 2, depth at most 4, a retention width of 2, and a reserve of 2 nodes, retaining the contract, the terminal verifier, and the exit conditions. Controller overhead above 40 percent of run cost indicates the gates should have suppressed the method.
- **High-risk or irreversible work**: Retain every phase, require a deterministic or cross-family verifier for every released answer, enlarge the reserve to at least 40 percent of the retention width, and bind the approval gate before release and before any side-effecting action. Abstention is preferred over an unverified answer.
- **Strict latency budgets**: Reduce depth and retention width rather than removing verification, since removing verification removes the only external authority in the method. Where latency forbids even one expansion round, the gates suppress tree search and a single chain runs with external verification and a declared fallback.
- **Large-scale batch deployment**: Route by difficulty so that easy cases exit after the baseline, unsupported cases abstain, and only the middle band receives search. Recompute the paired budget-matched comparison per traffic segment, because a margin measured on one segment does not transfer to another.
- **Multi-worker deployments**: Assign the frontier controller, generator, evaluator, and verifier to distinct components, enforce leases and virtual loss to prevent duplicate expansion, and treat agreement between components sharing a base model as correlated until an independence test says otherwise.

***

## V. Limitations and Considerations

**Cost multiplication is the default outcome, not the exception**: A bounded run at branching 3, retention width 3, and depth 4 issues roughly 40 to 60 times the model calls of a single chain, and the majority of expansions never touch the solution path. The consequence is that a deployment adopting tree search by reputation rather than by measurement will overspend without improving verified outcomes. The mitigation is the Budget Gate in Section 1.3 and the paired, budget-matched comparison in Step 1.2, which refuse the method below a 5 percentage point verified margin and withdraw it when the margin later erodes.

**The evaluator is the single point of failure**: Expanding the right branch requires judging an incomplete solution, and an evaluator near chance allocates effort at random while confidently removing viable branches. The consequence is a method that is worse than a single chain at many times the cost. The mitigation is the admission bar in Section 1.4, which blocks tree search outright below 65 percent sibling ranking accuracy and routes to independent sampling below 55 percent, together with the reserve and reinstatement rules that keep evaluator noise from being irreversible.

**Evaluator and generator share blind spots**: The evaluator commonly runs on the same model family as the generator, so its agreement is correlated rather than independent, and style can substitute for substance in its rankings. The consequence is fluent wrong answers scoring highest and passing unchallenged. The mitigation is the independence requirement in Step 6.1, the collusion tests in Step 3.3, and the standing rule that the evaluator's score orders the frontier and never authorises an answer.

**Reported benchmark gains are transcribed, not re-verified**: The originating prose source reports figures including a 74 percent success rate against 4 percent for a single chain on a deliberately search-heavy puzzle benchmark [1], substantial coverage gains from repeated sampling that plateaued once automatic verifiers were unavailable [9], and compute-optimal allocation improving test-time compute efficiency by more than four times relative to best-of-N [10]. No research pass was performed during this conversion, so these figures are carried as claims attributed to the source rather than as independently confirmed results, and they describe specific systems, models, and task regimes. The consequence of treating them as portable is systematic overestimation of the expected margin. The mitigation is that no threshold in this guide depends on them, and every deployment computes its own margin under Step 1.2.

**Numeric thresholds here are deployment defaults**: The branching ceiling of 5, the depth band of 3 to 12, the 0.15 calibration error, the 20 percent reserve floor, the 0.02 stagnation delta, the 0.30 novelty threshold, and the 5 percentage point admission margin were chosen to be operable on first deployment, not derived from a measured property of reasoning systems. The consequence is that a deployment inheriting them unchanged may prune too aggressively or expand too long for its task class. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute every threshold per task class against observed outcomes.

**Oracle analysis is retrospective and expensive**: Determining which pruned nodes lay on a solution path requires retaining prune records and re-expanding discarded subtrees offline, which multiplies evaluation cost and cannot be done in flight. The consequence is that the most informative diagnostic is also the one most likely to be skipped under schedule pressure. The mitigation is Checkpoint 7, which withholds promotion where the three loss terms fail to account for at least 90 percent of the oracle gap, making the analysis a release condition rather than an optional study.

**External verification is frequently unavailable**: Many valuable tasks admit no deterministic terminal check, and a cross-family model verifier is weaker evidence than an executable test. The consequence is that the method's central safeguard degrades exactly where the task is hardest. The mitigation is to record the verification arrangement in the trace, to treat a same-family verifier as insufficient for the highest risk tier, and to prefer abstention or escalation over releasing an answer certified only by the family that produced it.

**Intermediate state carries privacy exposure**: The tree retains partial reasoning, retrieved evidence, and tool observations at a granularity richer than any released answer, and that material may contain user secrets, inferred sensitive attributes, or instructions copied from untrusted content. The consequence is that a trace rich enough to diagnose search is rich enough to leak. The mitigation is the disclosure boundary in Section III.A, which stores payloads by hash reference under a declared retention class, redacts before export, and treats intermediate reasoning as sensitive telemetry rather than as an explanation owed to the reader.

**Structural conformance is not sound search**: A run can satisfy every checkpoint here, remain inside every cap, and still search a badly chosen space with a well-calibrated evaluator. The framework detects malformed search, not a misdirected objective. The consequence is a well-instrumented failure. No checkpoint substitutes for review of the decision contract itself against the problem it claims to solve.

***

## VI. Conclusion and Summary

Tree-of-thought reasoning is a search discipline before it is a prompting technique. Its value comes from a small number of explicit commitments made before the first branch exists: whether search is warranted against a measured baseline, what a state is and when two states are the same, how a partial solution is judged and how well that judgment has been shown to work, how many nodes may be spent, when a branch is abandoned and whether it may return, and what outside the generating model decides that the answer is correct. A system making those commitments will convert additional inference cost into verified outcomes. A system that asks a model to consider several options and calls the result a tree will multiply cost without a mechanism to recover the difference.

A team introducing the method should instrument the baselines before building a controller. Measure a direct attempt, a single chain, and self-consistency sampling on the same task distribution at a matched token budget, and record verified success, cost, latency, and failure modes. Build the deterministic layer next, since state identity, transition validation, node accounting, and budget enforcement are what make later measurement possible at all. Calibrate the evaluator against known-good outcomes and admit it only on measurement. Add search last, at the smallest branching and depth that clear the margin, and grow the budget only where marginal search yield stays positive. Frameworks and schedulers supply the plumbing; none of them supplies a calibrated evaluator or an external verifier, and neither of those can be substituted by a larger tree.

**Key Success Factors**:

- **Justification before search**: The method is admitted by a paired, budget-matched comparison against the single chain and the sampling baselines, and withdrawn when the margin erodes.
- **Canonical state before generation**: State identity, legal transitions, hashing, and serialisation are deterministic and dry-run without a model in the loop, so deduplication, backtracking, and replay are possible.
- **A measured evaluator or no search at all**: Sibling ranking accuracy, top-k recall, false-prune rate, and calibration error clear declared thresholds on held-out data before a single branch is expanded.
- **Bounds declared in advance**: Branching factor, depth, and total node budget are fixed before generation and enforced atomically, and exhaustion produces a best-so-far result with its evidence rather than nothing.
- **Numeric pruning with a way back**: Hard prunes are irreversible and deterministic, soft prunes require calibration and never act inside the noise floor, and a bounded reserve carries one reinstatement per node.
- **External authority over release**: The evaluator's score orders the frontier and never authorises an answer; a verifier sharing neither weights nor prompt with the generator decides that the run succeeded.

By following this guide, AI agents can spend additional inference compute on search only where search has been shown to pay, bound that search so its cost is knowable in advance, and terminate through a declared exit that a reviewer can audit rather than through a confident answer the tree never verified.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; no research pass was performed during this conversion, so their titles and locations are reproduced rather than independently re-verified, and the quantitative findings attributed to them in Section V are carried as claims of the source rather than as confirmed results.

**Corpus pointers**:

- `Production Guide to Tree-of-Thought Reasoning` — the originating prose guide from which this operational guide was derived. Source of the generator, transition, evaluator, and controller decomposition; the state, thought, action, and observation separation; the layered evaluator and the oracle-versus-realised analysis; the search policy comparison; the pruning, backtracking, and termination rules; the production loop; the metadata inventory; the failure-mode catalogue; and the deployment acceptance checklist. Its inline citations to primary literature supply the external references listed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — the control-layer companion. It governs whether deliberate search is warranted at all, the value-of-computation rule, and the stopping decision at the meta level; this guide specifies the search itself once that gate returns invoke. The terms decision contract, budget ledger, reason code, exit condition, stuck state, source class, and correlated failure are adopted from it unchanged.
- `advanced_task_guides/reasoning/guide_SelfConsistency.md` — the principal sampling baseline against which tree search must be justified in Step 1.2. It covers independence tiers, equivalence-class aggregation, duplicate collapse, and release thresholds for repeated independent attempts, and supplies the correlated-failure and source-class vocabulary shared with this guide.
- `advanced_task_guides/reasoning/guide_ChainOfThoughtReasoning.md` — the single-chain baseline named in Step 1.2 and in the gate routing table. It covers the warrant gate for intermediate reasoning, the technique ladder, bounded effort configuration, deterministic answer extraction, and the non-evidential status of a reasoning trace, and it applies the same execution tier partition and external-authorisation rule used here.
- `advanced_task_guides/reasoning/guide_GraphOfThought.md` — the sibling generalisation in which a node may have several parents, so partial results merge and are reused rather than only branching. It owns the typed edge vocabulary, the admitted-merge check, incremental cycle prevention, and dependency-fingerprint caching, and reuses the frontier, node budget, hard prune, and terminal verifier terms defined here. Route to it where aggregation and reuse are measurably present rather than where alternatives must be compared.
- `advanced_task_guides/reasoning/guide_ForestOfThought.md` — the sibling that runs several instances of this procedure concurrently under one budget. It owns the two-level budget partition, the isolation contract between trees, the deactivation test that returns an unproductive tree's allocation to the reserve, and the correlation-cluster adjustment on the cross-tree tally. Its per-tree step invokes this guide's procedure unchanged; it adds nothing inside a tree and this guide adds nothing across trees.
- `advanced_task_guides/reasoning/guide_ReflectiveMonteCarloTreeSearch.md` — the sibling covering the Monte Carlo variant of this search over environment states, adding visit counts, the selection rule, return backup, progressive widening, and a scoped lesson store. It adopts the evaluator admission bar, the calibration thresholds, the pruning and reinstatement rules, and the oracle-versus-realised vocabulary defined here rather than re-deriving them, and is the applicable route where rollouts rather than state scores carry the evaluation signal.
- `advanced_task_guides/reasoning/guide_ChainOfVerification.md` — companion guidance on claim-level verification against admitted evidence under bounded revision loops, applicable to the external terminal verifier the Evaluation Gate in Section 1.4 requires and without which this method must not be used.
- `advanced_task_guides/reasoning/guide_MetacognitiveMonitoring.md` — companion guidance on constructing and calibrating a signal before it is permitted to gate anything. The evaluator admission bar in Section 1.4 and the calibration pass in Step 3.2 apply its calibration measures and threshold-selection procedure to the state evaluator.
- `advanced_task_guides/planning/guide_WorldModelSimulationPlanning.md` — companion guidance on simulation-based planning, applicable to the rollout and world-model hallucination controls in Error Type 4 and to Monte Carlo tree search configuration in Step 2.3.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on instrumentation and event schema design, applicable to the run, node, edge, evaluation, model-call, and tool records required by the Instrumentation Agent in Section III.A.
- `advanced_task_guides/scoring/guide_complexityScoring.md` — a compact scoring rubric usable as an input to the difficulty routing described in Error Type 3 and in Section 4.2.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, III, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Tree search formulations and controller decompositions*

1. Yao and colleagues, *Tree of Thoughts* — https://arxiv.org/abs/2305.10601
2. Long — https://arxiv.org/abs/2305.08291
3. Huang and colleagues — https://arxiv.org/abs/2310.01798
4. Chen and colleagues — https://arxiv.org/abs/2410.17820

*Evaluators, reward models, and search-guided planning*

5. Gao and colleagues — https://arxiv.org/abs/2210.10760
6. Hao and colleagues, *Reasoning via Planning* — https://aclanthology.org/2023.emnlp-main.507/
7. Zhou and colleagues, *Language Agent Tree Search* — https://arxiv.org/abs/2310.04406
8. Sprueill and colleagues, *Monte Carlo Thought Search* — https://aclanthology.org/2023.findings-emnlp.560/

*Test-time compute allocation and reasoning models*

9. Brown and colleagues — https://arxiv.org/abs/2407.21787
10. Snell and colleagues — https://arxiv.org/abs/2408.03314
11. OpenAI, *reasoning best practices* — https://developers.openai.com/api/docs/guides/reasoning-best-practices
12. DeepSeek-R1 report — https://arxiv.org/abs/2501.12948
13. Anthropic, *extended-thinking documentation* — https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking

*Alternative generalisations of tree search*

14. Besta and colleagues, *Graph-of-Thought* — https://arxiv.org/abs/2308.09687
15. Sel and colleagues, *Algorithm-of-Thoughts* — https://arxiv.org/abs/2308.10379

*Instrumentation, injection, and disclosure*

16. OpenTelemetry, *GenAI semantic conventions* — https://opentelemetry.io/docs/specs/semconv/gen-ai/
17. OWASP, *prompt-injection guidance* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
18. OWASP, *sensitive-information guidance* — https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/
