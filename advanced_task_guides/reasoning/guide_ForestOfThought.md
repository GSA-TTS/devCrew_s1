# Forest-of-Thought Reasoning

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Forest-of-thought reasoning constitutes the task family of allocating a fixed inference budget across several concurrent, independently stateful reasoning trees, deciding after each one whether another tree is worth activating, and combining the trees' frozen candidates into a released answer or a declared non-resolution. This guide provides AI agents with a structured protocol for the decisions belonging to the forest rather than to any single tree: a two-level budget partition separating the run-wide reserve from per-tree allocations; a breadth-versus-depth split fixed before the first tree launches; an isolation contract forbidding one tree from observing another's intermediate state, because trees that share information agree for reasons unrelated to the answer being correct; a deactivation test that ends an unproductive tree and returns its unspent allocation to the reserve; a correlation-cluster adjustment capping the combined voting weight of near-identical tree policies before the cross-tree tally meets a release threshold; and a measurement pass that must show gain over both a single-tree and a sampling baseline at matched worst-case budget. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that additional trees convert into complementary verified coverage rather than into correlated unanimity at multiplied cost.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Forest-of-thought reasoning**: A test-time-compute architecture that runs several reasoning trees under one run contract, activates only trees whose expected verified gain justifies their cost, repairs selected trajectories where grounded feedback localises a defect, and selects a final result through cross-tree consensus combined with verifier or expert adjudication [1].

**Forest**: The set of trees authorised for one run, comprising launched, suspended, deactivated, and unactivated slots. The forest, not the tree and not the node, is the unit of budget accounting in this guide.

**Tree**: One bounded reasoning worker with a unique declared policy and its own namespace, carrying a tree identifier, a method, a model, prompt and decomposition versions, sampling parameters, an evidence partition, a local budget, a state schema, an evaluator, a correction policy, and a terminal output contract. Repeated samples are not trees; a tree has explicit internal state transitions or search behaviour.

**Tree policy**: The declared configuration that makes one tree different from another, spanning search algorithm, decomposition template, role objective, model family, evidence partition, and sampling parameters. Two trees differing only in random seed carry one policy, not two.

**Forest specification**: The compiled, versioned record of every tree policy, the shared immutable inputs, the namespace assignments, the normaliser version, the correction triggers, the aggregation rule, the cluster limits, the activation priority function, the stopping thresholds, and the fallback route. It is dry-run before any generation occurs.

**Run budget**: The declared caps for the whole run across trees, nodes, depth, corrections, model calls, tool calls, tokens, simultaneous calls, wall time, and currency cost. Every dimension carries a numeric limit; an unbounded dimension blocks execution.

**Forest reserve**: The portion of the run budget held back from the initially launched trees and available only to the activation decision. It is what makes sequential activation possible rather than nominal.

**Per-tree allocation**: The share of the run budget assigned to one tree at launch, decremented atomically as that tree works. No tree may consume another tree's allocation without a recorded controller grant from the reserve.

**Breadth-versus-depth split**: The declared partition of the run budget between the number of trees authorised and the node budget assigned to each. It is fixed before launch and changed only by a recorded reallocation.

**Isolation contract**: The declared rule set governing what one tree may observe of another. Under this guide's default, the answer is nothing until every candidate is frozen.

**Freeze point**: The moment a tree's terminal candidate becomes immutable and eligible for the consensus layer. Before its own freeze point, a tree may not observe any peer output.

**Sharing event**: Any recorded instance in which content originating inside one tree reached another tree, whether by design, by a permitted cross-pollination round, or by defect. Every sharing event is logged with its source tree, destination tree, content hash, and authorisation status.

**Correlation cluster**: A group of tree policies whose errors are empirically or structurally correlated, formed from measured conditional error on labelled data or from declared policy similarity. The combined voting weight of one cluster is capped.

**Activation decision**: The controller decision taken when no candidate has cleared the release gate, selecting exactly one of: activate an additional tree, resume a suspended tree, continue an active tree, correct a defective node, aggregate and verify, or stop.

**Deactivation**: Termination of one tree before its local budget is exhausted, on validity failure, infeasibility, stagnation, or a safety verdict. Deactivation returns the tree's unspent allocation to the forest reserve and records a reason code.

**Suspension**: Reversible halting of a tree at a durable checkpoint, retaining its remaining allocation for a possible resume. Suspension is not deactivation and does not release budget.

**Cross-tree candidate**: One tree's frozen terminal output after answer extraction, carrying its raw form, its normalised form, its equivalence-class identifier, its provenance, and its validity flags.

**Cluster-capped support**: Support for one equivalence class after cluster weight limits and duplicate collapse have been applied. It is the quantity compared against the release threshold; the raw count is retained but is never the decision quantity.

**Oracle coverage**: The proportion of runs in which any tree generated a retrospectively correct candidate. **Realised success**: the proportion in which the released answer was correct. Their difference is the **oracle gap**, decomposed in this guide across trees rather than only across nodes. The separation matters because coverage can keep rising with additional attempts while selection plateaus wherever the verifier is weak [5].

**Marginal tree value**: Verified success at an activated-tree cap of N minus verified success at a cap of N minus one, measured on the same examples under preregistered seeds. Non-positive marginal tree value withdraws the justification for the additional tree.

**Decision contract**: The declared objective, acceptance tests, hard constraints, preferences, risk class, authorised actions, evidence standard, and budget limits, fixed before the forest specification is compiled. Adopted unchanged from the corpus meta-reasoning guide.

**Budget ledger**: The run-wide record naming every bounded resource and its numeric limit, decremented atomically as work is committed. Adopted unchanged from the corpus tree-of-thought guide.

**Independence tier**: The categorical label recording how one candidate was diversified relative to the others, supplying the numeric independence factor applied before the release threshold is compared. The scale, its factors, and its release weights are defined in the corpus self-consistency guide and adopted here without modification.

**Independence assessment**: The procedure tracing every agreeing candidate to its source class and diversification tier and returning one verdict for the observed agreement. Adopted unchanged from the same guide, with the sharing ledger added as an input.

**Correlated failure**: Agreement among signals sharing a common premise, source, or model, mistaken for independent confirmation. In this method its dominant forms are shared base models across tree policies and unlogged sharing events between trees.

**Source class**: The provenance label attached to every signal, naming the model family, prompt variant, evidence bundle, and tool set that produced it. Two signals sharing a source class are treated as correlated until an independence test says otherwise.

**Reason code**: A normalised categorical label drawn from a closed vocabulary, recorded with every activation, deactivation, correction, tie-break, abstention, and stopping decision.

**Non-resolution**: The state in which no equivalence class clears the release threshold within the activated-tree cap. Non-resolution terminates in a verified partial result, an escalation, or an abstention, never in release of the plurality class.

**Exit condition**: A declared terminal state that alone may end a run: verified success, consensus release above threshold, forest exhaustion, budget exhaustion, futility, safety violation, or escalation to a named human role.

### 1.2 What This Guide Owns and What Its Siblings Own

Forest-of-thought sits close to the composition of two corpus siblings, and the boundary must be stated before the method is read. The corpus tree-of-thought guide owns everything inside one tree: thought generation, the canonical state schema, the transition validator, the state evaluator and its admission bar, frontier ordering, pruning, backtracking, and within-tree termination. The corpus self-consistency guide owns everything about combining several independent attempts: the diversification ladder, independence tiers and factors, answer extraction, normalisation, equivalence classing, duplicate collapse, tallying, the independence assessment, release thresholds, and abstention. This guide re-derives none of that; it adopts both vocabularies verbatim and cites the owning guide wherever a mechanism is invoked rather than defined.

**What remains, and why it is not covered by the composition**: Five decisions belong to the forest and appear in neither sibling.

- **Two-level budget allocation**: The self-consistency guide allocates a flat sample count and the tree-of-thought guide allocates a node budget inside one tree. Neither partitions a run budget between a set of trees and the interior of each. The forest decides that split before launch and holds a reserve the activation decision alone may spend.
- **The breadth-versus-depth trade**: Neither sibling faces the question of whether the next unit of budget buys another tree or a deeper search inside an existing one. Step 2.2 fixes that split numerically and revises it only through a recorded reallocation.
- **Tree-level early termination with budget reclamation**: Pruning in the tree-of-thought guide removes a node and the budget stays inside that tree. Deactivation here ends a whole tree and returns its unspent allocation to the reserve, changing what the rest of the run can afford. The reclamation, not the pruning, is the contribution.
- **The isolation contract**: Self-consistency samples are independent by construction, because a sample has no mutable state another sample could read. A forest runs several stateful searches concurrently, opening a channel that exists in neither sibling. Closing it, and recording every instance where it was opened, is this guide's central obligation.
- **Correlation clusters over heterogeneous policies**: An independence tier describes one candidate's diversification. A forest carries whole policies whose errors can be measured against one another on labelled data, permitting grouping and a cap on combined cluster weight. This extends the sibling's scale rather than replacing it.

**The sharing rule, stated explicitly**: Trees must not exchange intermediate state, drafts, scores, tool observations, or peer identities before their own freeze point. The reason is not tidiness. Cross-tree consensus carries evidential weight only because the agreeing trees reached their answers from separate premises; a tree that has seen a peer's draft has been conditioned on it, so its agreement measures the strength of that conditioning and not the strength of the answer. **Agreement among trees between which any sharing event is recorded before the freeze point is classified as correlated rather than confirming, is capped at the independence factor of a single tree, and can never satisfy a release threshold above the low-risk tier.** This rule is enforced by the sharing ledger in Step 3.3 and is not waivable by a model.

**Permitted sharing, and its cost**: Three categories may be shared without triggering the rule. Sanitised, provenance-linked task inputs and the immutable policy are inputs to every tree by definition. A common trusted retrieval core may be shared for cost, at the acknowledged price of correlated blindness, which is why Step 3.1 requires deliberately different query formulations or evidence partitions on top of it. Redacted answer records may be compared after every candidate is frozen, which is the consensus layer itself. A cross-pollination round is permitted only by creating a new descendant tree linked to every source tree, never by rewriting one, and the descendant inherits its sources' correlation clusters.

**Where the boundary is thin**: The correction loop in Phase 4 overlaps the tree-of-thought guide's backtracking and revision machinery. This guide owns only the run-wide correction budget, the anti-thrash caps expressed per tree, and the choice between correcting a tree and abandoning it. Localising a defect and re-running regressions inside a tree belong to the sibling and are invoked rather than restated.

### 1.3 The Entry Gates: Applicability and Cost Justification Against Both Baselines

A forest multiplies the cost of the method it wraps. The corpus tree-of-thought guide records that one bounded tree at branching factor 3, retention width 3, and depth 4 costs roughly 40 to 60 times a direct chain. A forest of 3 such trees therefore costs roughly 120 to 180 times a direct chain, and the default cap of 8 activated trees roughly 320 to 480 times it. That multiplier is recoverable only where trees produce complementary coverage a selector can recognise.

Agents must run five gates before any tree is launched, each returning a logged verdict with a reason code. A failed gate routes to a named cheaper method, to additional evidence, to human review, or to abstention; it never widens the forest.

**Forest-Need Gate**: Passes where task failures arise from missing the right strategy rather than from executing one known strategy poorly, where at least 2 materially different decompositions or search policies are plausible, where terminal candidates can be normalised and externally checked, and where the additional calls fit the latency and cost terms of the decision contract. Fails for retrieval, extraction, summarisation, classification, translation, stylistic rewriting, deterministic calculation, and any task whose direct answer already passes acceptance.

**Diversity Gate**: Passes only where at least 2 genuinely different tree policies are defined, differing in decomposition template, search algorithm, evidence partition, model family, or verifier-guided objective. Temperature variation alone does not pass; it alters surface samples while retaining the failure mode. Where pilot trees produce the same canonical intermediate states, the same citations, the same tool plan, and the same answer, the gate fails and the run routes to one tree with stronger verification.

**Selection Gate**: Passes only where a deterministic answer normaliser with passing regression cases exists and at least one outcome verifier, trusted tool, calibrated judge, or human review path is available. Cross-tree majority is useful only where the votes represent diverse evidence, and neither agreement nor model-reported confidence is ground truth.

**Budget Gate**: Passes only where the two-sided cost-justification inequality in Step 1.2 holds and every cap is fixed before execution: initial trees, maximum activated trees, nodes and depth per tree, simultaneous calls, correction rounds, evaluator calls, tool calls, input and output tokens, wall time, and currency cost. A configuration whose maximum authorised spend exceeds the decision contract is refused even where its expected spend is lower, because parallel fan-out makes worst-case and expected spend diverge sharply.

**Privacy and Tool-Safety Gate**: Passes only where the multiplied intermediate text, retrieved evidence, and tool observations can be stored under the declared retention class, where trees hold minimum sufficient structured state rather than unrestricted private rationales, and where every tool action passes schema validation, authorisation, confirmation policy, and sandbox controls independently of any tree's score or majority status.

**Gate Routing Table**:

| Observed condition | Failing gate | Route |
| :-- | :-- | :-- |
| Direct answer already passes the release verifier | Forest-Need | Release the direct answer |
| Reasoning is sequential and one decomposition is stable | Forest-Need | Single chain with external verification |
| Complete attempts are cheap and answer equivalence is easy | Forest-Need | Diversified sampling over independent attempts |
| One tree with shared state, pruning, and backtracking covers the space | Forest-Need | Single bounded tree search |
| Intermediate products must merge or be revised by several parents | Forest-Need | Graph-structured reasoning, not a forest |
| Only temperature separates the candidate policies | Diversity | One tree plus stronger verification |
| Pilot trees agree on states, citations, tool plan, and answer | Diversity | One tree plus stronger verification |
| No validated answer normaliser exists for the answer type | Selection | Constrain the answer schema, then re-gate |
| No outcome verifier, trusted tool, or human path exists | Selection | Abstain or escalate |
| Worst-case forest spend exceeds the decision contract | Budget | Reduce caps and re-run the comparison, or refuse |
| Verified margin over the better baseline below the minimum delta | Budget | Adopt the cheaper baseline |
| Multiplied intermediate state cannot be retained lawfully | Privacy and Tool-Safety | Run with ephemeral state and reduced logging, or refuse |
| A tree's score would grant a tool permission | Privacy and Tool-Safety | Move authorisation outside the model, then re-gate |

**Numeric gate rules**: Launch a forest only where all 5 gates pass. Where the Forest-Need Gate passes but fewer than 2 distinct tree policies survive the Diversity Gate, suppress and run a single tree, because a forest of 1 policy is one tree at forest overhead. Set an absolute default cap of 8 activated trees unless offline evidence on the deployment distribution authorises another value. Where estimated controller, aggregation, and evaluation overhead exceeds 30 percent of total run cost and the task sits in the lowest risk tier, suppress and record the estimate for the next policy revision.

**The two-sided cost-justification rule**: A forest is promoted only where the lower confidence bound on its verified-accuracy gain, measured on held-out data at matched worst-case budget, exceeds the deployment minimum delta against both the best single-tree configuration and the best diversified-sampling configuration. Beating one baseline while losing the other fails the gate. The default minimum delta is 3 percentage points at a cost multiple of no more than 3 relative to the better baseline, rising to 5 percentage points above a multiple of 3; above a multiple of 8, promotion requires a named per-item value justifying the spend case by case. The source reports one paper measuring 96.84 percent success with 8 activated subtrees at 25.64 average model invocations against 74.00 percent for its own tree baseline at 13.74 invocations on a 95-problem set [1]; that is a favourable instance on a verifiable-mathematics task, not a general expectation.

### 1.4 Execution Tier Partition and Authority Rules

Every operation in this method belongs to exactly one execution tier, and the assignment is not discretionary. The deterministic tier owns everything that must be exact, reproducible, and auditable, which in a forest means all budget accounting at both levels, all isolation enforcement, all aggregation, and every termination rule. The model tier owns only the open-vocabulary work no deterministic rule covers, which in a forest means generating thoughts and evaluating partial states inside a tree. The hybrid tier covers operations where the model proposes and software decides, and in every such operation the deterministic component holds authority.

**Deterministic tier**: Per-tree allocation and run-wide budget accounting, including atomic decrement, reservation before launch, reclamation on deactivation, and cap enforcement; namespace assignment and isolation enforcement, including the freeze point and the sharing ledger; answer extraction, normalisation, equivalence classing, duplicate collapse, and cross-tree tallying; correlation-cluster construction, cluster weight capping, and the independence assessment; the activation priority computation and the selection of exactly one forest transition; every termination rule, including deactivation, suspension, futility, convergence, and hard-cap exits; cancellation propagation; and every verifier for which a deterministic oracle exists.

**Model tier**: Generation of candidate thoughts inside a tree; estimation of partial-state value for residual criteria no deterministic check covers; proposal of semantic equivalence where mechanical matching fails; and construction of the natural-language response from a verified result.

**Hybrid tier**: The model proposes a candidate and the terminal verifier adjudicates, and the verifier holds authority. The model scores a partial state and the controller decides whether resources are spent, and the controller holds authority. An expert judge ranks non-equivalent candidates and a deterministic verifier or a human role decides release, and the verifier or the human role holds authority.

**Tier Assignment by Operation**:

| Operation | Owning tier | Authority when tiers disagree |
| :-- | :-- | :-- |
| Run budget partition and per-tree allocation | Deterministic | Ledger decides; no model sets its own allocation |
| Breadth-versus-depth split and its revision | Deterministic | Ledger decides; reallocation is a recorded event |
| Namespace assignment and isolation enforcement | Deterministic | Isolation enforced outside the model; no waiver exists |
| Freeze-point enforcement and sharing-ledger entry | Deterministic | Deterministic; an unlogged sharing event halts the run |
| Thought generation inside a tree | Model | Model proposes only; no authority |
| Partial-state evaluation inside a tree | Model | Orders work; authorises nothing |
| Legality of a transition inside a tree | Deterministic | Validator rejects; the proposal is discarded |
| Tree deactivation and budget reclamation | Deterministic | Controller executes; the evaluator cannot veto |
| Correction trigger detection | Deterministic | A grounded checker fires the trigger, never a prompt |
| Correction content within the permitted edit scope | Model | Model drafts; regressions decide acceptance |
| Answer extraction and normalisation | Deterministic | Unparseable candidates are invalid, not coerced |
| Free-form semantic equivalence proposal | Hybrid | Deterministic adjudication; the model proposes only |
| Cross-tree tallying and duplicate collapse | Deterministic | No model inspects or adjusts a tally |
| Correlation-cluster assignment and weight capping | Deterministic | Computed from recorded provenance and labelled error |
| Independence assessment and verdict | Deterministic | Computed, never asserted |
| Expert adjudication of a residual disagreement | Hybrid | Advisory; a deterministic verifier outranks it |
| Activation decision and forest transition | Deterministic | Exactly 1 transition per decision point |
| Release-gate evaluation and abstention trigger | Deterministic | Release is a rule, not a judgement |
| Cost, token, latency, and cancellation accounting | Deterministic | Enforced outside the model |

**Three authority rules govern the whole method.** First, no model may observe a peer tree's state, a vote total, or a cluster weight before its own candidate is frozen; a model that has seen any of these has been conditioned by them and its output is recorded as correlated. Second, cross-tree agreement never establishes correctness and never authorises an action; a deterministic verifier outranks any tally, and a verified minority candidate outranks an unverified majority. Third, exhaustion of the run budget produces a declared non-resolution carrying the best verified partial result, its evidence, and its limiting condition, never a confident answer manufactured to fill the response slot.

***

## II. Operational Framework: Budgeted Multi-Tree Search Toward Cross-Tree Consensus Under Enforced Isolation

The framework assumes the 5 gates in Section 1.3 have returned pass. Phases 1 through 3 run once per configuration and produce the forest specification, the budget partition, and the isolation contract. Phases 4 through 6 form the forest loop: Phase 6 either terminates the run through a declared exit condition or returns control to Phase 4 with one additional or resumed tree. Phase 7 runs offline and gates promotion of any configuration change.

### Phase 1: Applicability Gating and Baseline Cost Justification

**Objective**: Fix the run contract and prove by paired measurement that a forest earns its multiplier over both the single-tree baseline and the sampling baseline, before any tree policy is written.

#### Step 1.1: Establish the Run Contract and the Forest Budget Ledger

**Required Actions**:

- Record the objective, output schema, hard constraints, risk tier, evidence policy, answer-equivalence rule, success verifier, abstention behaviour, tool permissions, and retention class.
- Enter a numeric hard cap for every bounded dimension: initial trees, maximum activated trees, nodes per tree, depth per tree, corrections per node and per tree, model calls, tool calls, input and output tokens, simultaneous calls, wall time, and currency cost.
- Declare the exit conditions the run may terminate through, drawn from the closed list in Section 1.1, and the fallback route for each.
- Represent the ledger in durable structured state that decrements atomically, so concurrent trees cannot overspend a shared dimension between reads.
- Halt and either clarify or apply a logged conservative default where any mandatory field is absent.

**Required Outputs**:

- A run contract record carrying objective, acceptance tests, evidence standard, risk tier, and retention class.
- A budget ledger naming every bounded dimension and its numeric limit.
- A declared exit-condition list with a fallback route per condition.

**Quality Checkpoints**:

- Every acceptance test returns pass or fail without interpretation; an untestable criterion halts the run before any tree launches.
- Every budget dimension carries a numeric limit; an unbounded dimension halts the run.
- The ledger supports atomic decrement under the declared concurrency cap; a ledger that permits a read-then-write race halts the run.

***

#### Step 1.2: Run the Baseline Ladder and Test the Two-Sided Cost-Justification Inequality

**Required Actions**:

- Execute the ladder in ascending cost order on a held-out set of at least 50 representative tasks: deterministic logic or retrieval, one direct model response, one reasoning-model response where the class is available, chain-of-thought, diversified sampling, and one single-tree search.
- Stop at the first rung whose verified accuracy meets the acceptance target at an acceptable cost, and record that rung as the released method.
- Record for every rung its verified accuracy, its worst-case authorised spend, its realised spend, and its p95 latency, so the comparison is budget-matched rather than accuracy-only.
- Compute the projected forest cost multiple against the better of the single-tree and sampling baselines, using worst-case authorised spend on both sides.
- Compare the lower confidence bound on the projected forest gain against the minimum delta for that cost multiple, computed by paired bootstrap over the held-out set.

**Required Outputs**:

- A baseline ladder record carrying accuracy, worst-case spend, realised spend, and latency per rung.
- A projected forest cost multiple against each of the 2 binding baselines.
- A two-sided inequality verdict with its confidence bound and its bootstrap parameters.

**Quality Checkpoints**:

- Both baselines were measured on the same held-out set at matched worst-case budget; an accuracy comparison at unmatched budget is rejected.
- The gain figure is a lower confidence bound, not a best observed point; a point estimate fails the checkpoint.
- The forest is refused where either side of the inequality fails, and the failing side is named in the verdict.

***

#### Step 1.3: Record the Gate Verdicts and the Forest Hypothesis

**Required Actions**:

- Record a verdict, a reason code, and the supporting measurement for each of the 5 gates in Section 1.3.
- State the forest hypothesis in one sentence naming the specific failure of the single-tree baseline that separate policies are expected to repair, drawn from decomposition uncertainty, search-policy sensitivity, or evidence-route ambiguity.
- Name the observable that will confirm or refute the hypothesis, expressed as a measurable quantity available from the run record.
- Route any failed gate to its named alternative and close the run there rather than proceeding with a recorded warning.

**Required Outputs**:

- A gate verdict record with 5 entries, each carrying a reason code and its evidence.
- A forest hypothesis naming the target failure mode and its confirming observable.

**Quality Checkpoints**:

- All 5 gates carry an explicit verdict; an unrecorded gate blocks launch.
- The hypothesis names a failure mode of the single-tree baseline, not a general expectation that more compute helps.
- The confirming observable is computable from the fields declared in Step 7.1; an observable the log cannot produce fails the checkpoint.

***

### Phase 2: Budget Allocation Across and Within Trees

**Objective**: Partition the run budget between the forest reserve and the individual trees, and fix the breadth-versus-depth split, so that the activation decision in Phase 6 has resources to spend and no tree can silently consume the run.

#### Step 2.1: Partition the Run Budget Into Reserve and Per-Tree Allocations

**Required Actions**:

- Reserve at least 40 percent of every bounded dimension for the activation decision where the maximum activated-tree cap exceeds the initial tree count, so sequential activation is funded rather than nominal.
- Divide the remaining budget equally across the initial trees by default, and record any unequal division with the evidence that justifies it, such as measured per-policy cost on the held-out set.
- Attach to every allocation a per-tree floor below which the tree cannot reach an informative first checkpoint, computed as the branching factor multiplied by the minimum informative depth, and refuse a partition that puts any tree below its floor.
- Declare the reclamation rule: a deactivated tree returns 100 percent of its unspent allocation to the reserve, and a suspended tree retains its allocation until its suspension expires.
- Declare the grant rule: no tree may draw from the reserve or from a peer's allocation except through a controller grant recorded with its reason code and its amount.

**Budget Partition Defaults**:

| Dimension | Reserve share | Per-tree share of the remainder | Floor per tree |
| :-- | :-- | :-- | :-- |
| Activated trees | Cap minus initial count | Not applicable | 1 |
| Generated nodes | 40 percent | Equal division | Branching factor times minimum depth |
| Model calls | 40 percent | Equal division | Nodes floor plus 1 evaluation per node |
| Output tokens | 40 percent | Equal division | Model-call floor times declared maximum output |
| Corrections | 50 percent | 3 per tree, 2 per node | 0 |
| Tool calls | 30 percent | Equal division | 1 where the policy requires a tool |
| Wall time | 20 percent | Full concurrent share | Slowest-tree estimate at p95 |
| Currency cost | 40 percent | Equal division | Sum of the dimension floors above |

**Required Outputs**:

- A budget partition record naming the reserve share and the per-tree allocation for every dimension.
- A per-tree floor record with the computation that produced each floor.
- A declared reclamation rule and a declared grant rule with their reason-code vocabulary.

**Quality Checkpoints**:

- The reserve is at least 40 percent on every dimension where sequential activation is authorised; a smaller reserve makes the activation decision unfundable and fails the checkpoint.
- No initial tree is allocated below its floor; a partition violating a floor is rejected before launch.
- Allocations plus reserve sum to no more than the run cap on every dimension; an over-committed partition halts the run.

***

#### Step 2.2: Fix the Breadth-Versus-Depth Split

**Required Actions**:

- Compute the evaluator's sibling ranking accuracy on the held-out corpus for each candidate tree policy, using the admission bar defined in the corpus tree-of-thought guide.
- Allocate toward depth where sibling ranking accuracy is at or above 65 percent, because a competent evaluator converts additional nodes inside a tree into better-ordered search; allocate toward breadth where it falls between 55 and 65 percent, because a weak evaluator wastes depth and separate policies still expand coverage.
- Refuse the forest and route to diversified sampling with external verification where sibling ranking accuracy is below 55 percent for every candidate policy, because ordering is then indistinguishable from random inside every tree.
- Cap any single tree at 50 percent of the non-reserve node budget, so no policy can consume the forest before the second policy has run.
- Record the split as an explicit pair of numbers, the initial tree count and the nodes per tree, and record the reallocation procedure that may change it mid-run.

**Breadth-Versus-Depth Allocation Rule**:

| Measured sibling ranking accuracy | Initial trees | Nodes per tree relative to the single-tree baseline | Rationale |
| :-- | :-- | :-- | :-- |
| At or above 80 percent | 2 | 100 percent | Depth converts reliably; breadth adds correlated cost |
| 65 to 80 percent | 3 | 70 percent | Balanced; both levers pay at reduced rates |
| 55 to 65 percent | 4 | 50 percent | Ordering is noisy; coverage comes from policy diversity |
| Below 55 percent | 0 | Not applicable | Refuse the forest; route to sampling plus verification |

**Required Outputs**:

- A measured sibling ranking accuracy per candidate tree policy.
- A declared breadth-versus-depth split expressed as an initial tree count and a per-tree node budget.
- A recorded reallocation procedure naming who may change the split and under what trigger.

**Quality Checkpoints**:

- The split is derived from a measured evaluator figure, not chosen by preference; an unmeasured split fails the checkpoint.
- No tree holds more than 50 percent of the non-reserve node budget.
- The reallocation procedure names a numeric trigger; a discretionary reallocation right fails the checkpoint.

***

#### Step 2.3: Compile and Dry-Run the Forest Specification

**Required Actions**:

- Compile the tree policies, tree-state schema, shared immutable inputs, namespace map, permitted evidence, generator and evaluator versions, answer normaliser, correction triggers, aggregation rule, correlation-cluster limits, activation priority function, stopping thresholds, and fallback into one versioned specification.
- Dry-run serialisation, budget accounting, cancellation propagation, checkpoint and resume, and verifier invocation with generation disabled, so control-plane defects surface before any token is spent.
- Confirm that every tree in the specification can be started, paused, resumed, corrected, deactivated, and replayed deterministically from its checkpoint.
- Verify that the answer normaliser passes its regression cases for the declared answer type before the specification is admitted.
- Assign a specification version identifier and bind it to every record the run will emit.

**Required Outputs**:

- A versioned forest specification covering all 14 declared fields.
- A dry-run report covering serialisation, accounting, cancellation, checkpointing, and verification.
- A normaliser regression result with a pass or fail verdict per case.

**Quality Checkpoints**:

- Every tree in the specification survives a start, pause, resume, deactivate, and replay cycle in the dry run; a tree failing any transition blocks launch.
- Cancellation propagates to queued model and tool calls within the declared cancellation window; leaked work after cancellation fails the checkpoint.
- The normaliser passes 100 percent of its regression cases; any failure blocks launch, because a silent class split or merge invalidates every later tally.

***

### Phase 3: Tree Isolation and the Sharing Contract

**Objective**: Enforce mutable-state isolation between trees up to the freeze point and record every sharing event, so that cross-tree agreement carries the independence its release threshold assumes.

#### Step 3.1: Assign Namespaces and Declare the Shared Immutable Inputs

**Required Actions**:

- Assign every tree a distinct namespace holding its own state, drafts, scores, evidence, tool observations, and traces, with no read path to a peer namespace.
- Enumerate the shared immutable inputs each tree receives: the sanitised task input with its provenance links, the run contract, the immutable policy, the authorised evidence scope, and the common schemas. Nothing else crosses a namespace boundary before the freeze point.
- Where a common retrieval core is shared for cost, require at least 2 deliberately different query formulations, evidence partitions, or retrieval methods across the forest, and record the shared core as a declared source of correlated blindness.
- Preserve for every retrieved item its document and chunk identifiers, its location, its access-control decision, its rank, its retrieval time, and its content hash, so a later independence assessment can trace evidence overlap.
- Treat every retrieved and tool-produced string as untrusted data; retrieved text may never alter the forest's rules, budgets, voters, or tool permissions [8].

**Required Outputs**:

- A namespace map binding each tree identifier to an isolated state container.
- A shared immutable input inventory naming every artifact that crosses a namespace boundary before the freeze point.
- An evidence provenance record for every retrieved item available to any tree.

**Quality Checkpoints**:

- No read path exists from one tree's namespace to another's; a discovered path halts the run rather than being recorded as a warning.
- The shared input inventory contains only sanitised, immutable, provenance-linked artifacts; any mutable shared artifact fails the checkpoint.
- Where retrieval is shared, at least 2 distinct query formulations or evidence partitions are in force; a single shared query set fails the checkpoint.

***

#### Step 3.2: Declare the Freeze Point and the Sanitised Consensus Record

**Required Actions**:

- Define the freeze point for each tree as the moment its terminal candidate is written to immutable storage with its content hash, after which the tree may not revise that candidate.
- Prohibit any exposure of peer output, vote totals, cluster weights, or peer identities to a tree before that tree's own freeze point, and enforce the prohibition in the orchestrator rather than in a prompt instruction.
- Define the sanitised consensus record as the only representation of a candidate that crosses into the aggregation layer: the normalised answer, its equivalence-class key, its validity flags, its provenance references, and its verifier results, with the raw trajectory retained under hash and not forwarded.
- Prohibit copying a full peer transcript into a judge or an expert adjudicator, since injected instructions and persuasive style then propagate into the selection decision.
- Where a cross-pollination round is authorised, create a new descendant tree with links to every source tree, assign it the union of its sources' correlation clusters, and never rewrite an original tree.

**Isolation Boundary Specification**:

```
NAMESPACE: tree_<id>
READABLE_BEFORE_FREEZE:
  1. Sanitised task input with provenance links
  2. Run contract, immutable policy, and output schema
  3. Authorised evidence scope for this tree's partition
  4. This tree's own state, scores, and observations
PROHIBITED_BEFORE_FREEZE:
  1. Any peer tree's state, draft, score, or observation
  2. Any vote total, support figure, or cluster weight
  3. Any peer tree identity, count, or activation order
  4. Any raw peer transcript forwarded to a judge
FREEZE_EVENT:
  - Write candidate to immutable storage with content hash
  - Emit sanitised consensus record to the aggregation layer
  - Mark tree ineligible for further revision of that candidate
READABLE_AFTER_FREEZE:
  1. Sanitised consensus records of frozen peer candidates
  2. Verifier results attached to those records
VIOLATION_ACTION:
  - Record a sharing event with source, destination, and hash
  - Reclassify the affected agreement as correlated
  - Cap the affected trees at the independence factor of one tree
```

**Required Outputs**:

- A declared freeze point per tree with its enforcement location in the orchestrator.
- A sanitised consensus record schema naming every forwarded field.
- A cross-pollination policy stating whether descendant trees are authorised and how they inherit clusters.

**Quality Checkpoints**:

- The freeze prohibition is enforced by the orchestrator; a prohibition stated only in a prompt fails the checkpoint, because a prompt instruction is not an access control.
- The consensus record carries no raw trajectory and no peer identity; a record forwarding either fails the checkpoint.
- Every descendant tree created by cross-pollination inherits the union of its sources' correlation clusters; an uninherited cluster fails the checkpoint.

***

#### Step 3.3: Open the Sharing Ledger and Assign Independence Tiers

**Required Actions**:

- Open an append-only sharing ledger recording every sharing event with its source tree, destination tree, content hash, timestamp, authorisation status, and detection method.
- Assign every tree policy an independence tier using the scale defined in the corpus self-consistency guide, mapping algorithmic diversity and disjoint evidence partitions to the tier that guide assigns to a different model family or a disjoint evidence partition, and mapping seed-only variation to its weakest sampling tier.
- Record for every tree its source class, naming the model family, the prompt variant, the evidence bundle, and the tool set that produced it.
- Downgrade to the independence factor of a single tree any pair of trees between which an unauthorised sharing event is recorded before either freeze point, and mark the affected agreement as correlated rather than confirming.
- Halt the run where the sharing ledger records an event whose detection method is absent, since an undetectable channel invalidates every independence claim the run will make.

**Required Outputs**:

- An append-only sharing ledger with one entry per detected sharing event.
- An independence tier assignment per tree policy, referencing the sibling guide's scale.
- A source class record per tree naming model family, prompt variant, evidence bundle, and tool set.

**Quality Checkpoints**:

- Every tree carries exactly 1 independence tier and exactly 1 source class before launch; an unassigned tree blocks launch.
- The ledger is append-only and its entries are content-addressed; a mutable ledger fails the checkpoint.
- No agreement between trees carrying a pre-freeze sharing event is counted at more than the independence factor of one tree, and the downgrade is applied by the deterministic tier without model involvement.

***

### Phase 4: Per-Tree Execution With Early Termination

**Objective**: Advance each active tree inside its own allocation, deactivate trees that stop earning their budget, and return their unspent allocation to the forest reserve.

#### Step 4.1: Launch the Minimum Forest Under the Concurrency Cap

**Required Actions**:

- Launch the initial tree count fixed in Step 2.2, never more, and hold every further tree for the activation decision in Phase 6.
- Assign each launched tree its namespace, its allocation, a distinct seed, and a distinct policy identifier, and record that seeds are a bookkeeping device rather than a diversity mechanism.
- Reserve each tree's allocation against the ledger before its first model call, so a launch that cannot be funded fails before it consumes anything.
- Retry parsing once where a tree returns malformed output, then deactivate it with a reason code rather than retrying generation.
- Bound simultaneous calls to the declared concurrency cap and apply worker leases with heartbeats, so a stalled tree releases its slot rather than holding the forest.

**Required Outputs**:

- A launch record per tree carrying namespace, allocation, seed, policy identifier, and reservation confirmation.
- A concurrency state record naming active slots, queued work, and lease expiries.

**Quality Checkpoints**:

- The launched tree count equals the initial count from Step 2.2; a larger launch fails the checkpoint because it consumes the reserve the activation decision depends on.
- Every launched tree holds a confirmed reservation; an unreserved launch halts the run.
- No tree policy differs from another only by seed; a seed-only pair is collapsed to one policy before launch.

***

#### Step 4.2: Advance Each Active Tree and Apply the Deactivation Test

**Required Actions**:

- Advance each active tree under its own declared search controller, following the expansion, evaluation, and pruning procedure specified in the corpus tree-of-thought guide rather than a procedure restated here.
- Run the cheap deterministic checks after every expansion, in this order: schema validity, safety and authorisation, invariant satisfaction, provenance presence, and budget headroom, before any expensive evaluation is invoked.
- Apply the deactivation test at every within-tree checkpoint and deactivate on the first condition that holds: no valid output extractable at the current layer, proven infeasibility, stagnation against the declared delta, allocation exhaustion, or a safety verdict.
- Return 100 percent of a deactivated tree's unspent allocation to the forest reserve in the same atomic operation that records the deactivation, so the reserve reflects reality before the next activation decision reads it.
- Suspend rather than deactivate where the tree has produced verified partial progress and its stagnation is attributable to a missing evidence item that another tree may supply, and retain its allocation for the declared suspension window.

**Deactivation Conditions and Their Consequences**:

| Condition | Numeric trigger | Budget consequence |
| :-- | :-- | :-- |
| No valid output extractable at a layer | 2 consecutive layers | Reclaim 100 percent of unspent allocation |
| Proven infeasibility under a hard constraint | 1 occurrence | Reclaim 100 percent of unspent allocation |
| Stagnation in verified progress | Improvement below delta over 3 expansion rounds | Reclaim 100 percent of unspent allocation |
| Allocation exhausted on any dimension | 1 occurrence | Nothing to reclaim; record exhaustion |
| Safety or authorisation verdict | 1 occurrence | Reclaim and quarantine the tree record |
| Verified partial progress blocked on evidence | Improvement below delta over 2 rounds | Suspend; retain allocation for the window |

**Required Outputs**:

- A per-tree progress record carrying nodes generated, nodes expanded, maximum depth, verified progress, and remaining allocation.
- A deactivation or suspension record per terminated tree with its condition, its reason code, and its reclaimed amount.
- An updated forest reserve balance per dimension.

**Quality Checkpoints**:

- Deterministic checks precede every expensive evaluation call; an evaluation invoked on a schema-invalid state fails the checkpoint.
- Every deactivation is paired with an atomic reclamation entry; a deactivation without a reclamation entry halts the run, because the reserve then overstates or understates what remains.
- No tree consumes another tree's allocation without a recorded controller grant.

***

#### Step 4.3: Run the Bounded Correction Loop Under Anti-Thrash Guards

**Required Actions**:

- Begin a correction only where a grounded trigger has fired: a failed invariant, a failed test, a contradiction with trusted evidence, a malformed output, a low calibrated process score, or a verifier-localised defect. A generic instruction to review the answer is not a trigger.
- Create each correction as a new immutable revision linked to the defective node, supplying the defect class, the relevant observation, the permitted edit scope, and the constraints that must remain unchanged.
- Re-run the triggering checker and every regression check the change could affect, and accept the revision only where it clears the trigger without reducing a protected criterion; otherwise revert to the prior revision and increment the failed-correction count.
- Enforce the anti-thrash guards: at most 2 corrections per node and 3 per tree, no repetition of a correction signature already attempted, and a measurable progress requirement after each accepted revision.
- Exit the loop and backtrack, suspend, or deactivate where 2 consecutive revisions fail the same check, where revisions alternate between equivalent states, where a revision reduces the verifier score, or where the local correction budget is spent. Corrections never reset node, token, tool, time, or cost counters.

**Required Outputs**:

- A correction record per attempt carrying trigger type, failed checker, defect signature, edit scope, before and after scores, regression results, and the accept or revert verdict.
- An anti-thrash counter set per node and per tree.
- A loop exit record naming the terminating condition and the follow-on action.

**Quality Checkpoints**:

- Every correction traces to a named grounded trigger; a correction without one is rejected before it is drafted, because unprompted self-revision degrades initially correct answers [4].
- No node exceeds 2 corrections and no tree exceeds 3; a breach halts that tree rather than the run.
- No counter is reset by a correction; a reset counter halts the run, since it removes the only bound on correction spend.

***

### Phase 5: Cross-Tree Aggregation Under Independence Assessment

**Objective**: Convert frozen candidates into cluster-capped support for equivalence classes and return one independence verdict, so that agreement is weighted by the diversity of the evidence behind it rather than by tree count.

#### Step 5.1: Freeze Candidates, Class Them, and Build Correlation Clusters

**Required Actions**:

- Collect the frozen terminal candidate from every active and completed tree, and reject as ineligible any candidate that failed schema parsing, safety validation, or a hard constraint. An invalid candidate receives no vote rather than a low vote.
- Extract, normalise, and class every eligible candidate using the answer extraction, normalisation, and equivalence procedures defined in the corpus self-consistency guide, retaining the raw candidate under its content hash.
- Apply duplicate collapse so that canonically identical candidates from one tree policy contribute a single unit of support.
- Build correlation clusters from measured pairwise conditional error on the labelled held-out set, grouping any pair of policies whose conditional error exceeds 0.70 into one cluster, and grouping by declared policy similarity where labelled data is unavailable for that pair.
- Record for every cluster its member policies, its formation basis, its measured joint-wrong rate, its double-fault rate, and its disagreement rate.

**Correlation Cluster Formation Rule**:

```
INPUT: labelled held-out error vectors per tree policy
COMPUTE per policy pair (A, B):
  1. joint_wrong_rate  = P(A wrong AND B wrong)
  2. double_fault_rate = P(A wrong AND B wrong AND same wrong class)
  3. disagreement_rate = P(A class != B class)
  4. conditional_error = P(A wrong | B wrong)
CLUSTER:
  IF conditional_error > 0.70 IN EITHER DIRECTION
     THEN place A and B in one cluster
  IF labelled data absent for the pair
     THEN cluster by declared policy similarity: same model family
          AND same decomposition template AND same evidence partition
  IF a pre-freeze sharing event links A and B
     THEN place A and B in one cluster regardless of measured error
OUTPUT: cluster assignment per policy, with formation basis recorded
```

**Required Outputs**:

- An eligible candidate set with normalised answers, class keys, and provenance references.
- An ineligibility record naming every rejected candidate and its rejection reason.
- A correlation cluster assignment per tree policy with its formation basis and its measured rates.

**Quality Checkpoints**:

- Every candidate carries a class key produced by the versioned normaliser; a class key written by a model fails the checkpoint.
- Every tree policy belongs to exactly 1 correlation cluster; an unassigned policy blocks aggregation.
- Every pair linked by a pre-freeze sharing event shares a cluster, irrespective of measured error.

***

#### Step 5.2: Compute Cluster-Capped Support and the Independence Verdict

**Required Actions**:

- Compute raw support per equivalence class, then apply the cluster cap: no single correlation cluster may contribute more than 40 percent of total eligible support, and any excess is discarded rather than redistributed to other classes.
- Compute the effective independence of the run as the highest independence tier represented by at least 2 supporting trees drawn from distinct correlation clusters, and select the release threshold for that tier from the scale in the corpus self-consistency guide.
- Compute winning share and top-two margin on the cluster-capped support, and record the raw support alongside them without ever releasing on the raw figure.
- Run the independence assessment over the supporting trees, taking the sharing ledger, the source class records, and the cluster assignments as inputs, and return one verdict for the observed agreement.
- Record accuracy conditional on agreement for the task slice where ground truth is available offline, since high agreement with poor conditional accuracy is a correlated-error alarm rather than confidence.

**Required Outputs**:

- A support table per equivalence class carrying raw support, cluster-capped support, winning share, and top-two margin.
- An effective independence figure with the tier and the clusters that established it.
- One independence verdict for the observed agreement, with its inputs named.

**Quality Checkpoints**:

- The release comparison uses cluster-capped support; a comparison against raw support fails the checkpoint.
- No cluster contributes more than 40 percent of total eligible support after capping.
- Where all supporting trees fall in 1 cluster, the effective independence is that of a single tree and the run cannot release above the low-risk tier, irrespective of how many trees agreed.

***

#### Step 5.3: Adjudicate Verified Minority Overrides and Residual Disagreement

**Required Actions**:

- Mark provisional success where exactly 1 candidate passes a decisive external verifier, irrespective of which class holds the majority, because a deterministic verdict outranks a tally.
- Rank by task utility and declared risk where more than 1 candidate passes a decisive verifier, and record the ranking criterion.
- Preserve every minority candidate that satisfies an external check, and record a minority-verifier win where such a candidate is released over a larger unverified class.
- Route residual disagreement to an expert adjudicator only where no deterministic verifier applies, presenting blinded, sanitised consensus records with randomised order, and record the adjudicator identity, rubric version, and score.
- Escalate to external verification or a named human role rather than to an expert adjudicator where the task sits in the highest risk tier or authorises an irreversible action, since an adjudicator lacking new evidence can reproduce the shared misconception that produced the disagreement.

**Required Outputs**:

- A provisional selection record naming the chosen candidate, its class, and its selection basis.
- A minority-override record where a verified minority candidate was released.
- An adjudication record carrying blinding, presentation order, rubric version, and rationale hash where an expert path was used.

**Quality Checkpoints**:

- No majority class is released over a candidate that passed a decisive deterministic verifier.
- Every expert adjudication was presented blinded and order-randomised; an unblinded adjudication fails the checkpoint because it admits positional and style bias.
- No expert adjudication decides a highest-risk-tier or irreversible-action case; such cases route to external verification or a human role.

***

### Phase 6: The Activation Decision and Bounded Termination

**Objective**: Decide once per aggregation cycle whether another tree is worth its cost, issue exactly one forest transition, and terminate through a declared exit condition rather than through exhaustion.

#### Step 6.1: Estimate the Expected Verified Gain of One Additional Tree

**Required Actions**:

- Compute the activation priority for each unactivated policy and each suspended tree from six recorded components: historical verified success for this task slice, current cross-class disagreement, uncovered strategy relative to the active clusters, novelty against generated state hashes, correlation with the active policies, and estimated remaining cost.
- Estimate expected verified gain per unit cost, and rank candidates on that ratio rather than on raw expected gain, so a cheap complementary policy outranks an expensive marginal one.
- Compare the remaining forest reserve against the candidate's worst-case allocation, and reject any candidate whose worst case the reserve cannot cover.
- Apply the diversity reserve rule: retain capacity for at least 1 candidate from a correlation cluster not yet represented, so a run cannot spend its whole reserve inside one cluster.
- Set the activation delta from the lower confidence bound of the offline marginal-tree-value curve for this slice, never from its best observed point.

**Required Outputs**:

- An activation priority table with all 6 components populated per candidate.
- An expected verified gain per unit cost per candidate, with its reserve feasibility verdict.
- A declared activation delta with its provenance in the offline curve.

**Quality Checkpoints**:

- Every candidate carries all 6 priority components; a missing component blocks the activation decision.
- No candidate is activated whose worst-case allocation exceeds the remaining reserve.
- The activation delta derives from a lower confidence bound; a delta set from a best observed point fails the checkpoint.

***

#### Step 6.2: Issue Exactly One Forest Transition

**Required Actions**:

- Select exactly 1 transition from the closed set: activate an additional tree, resume a suspended tree, continue an active tree, correct a defective node, aggregate and verify, or stop.
- Authorise an activation only where all 4 conditions hold: the reserve covers the candidate's worst case, predicted marginal gain is at least the activation delta, the candidate adds a correlation cluster or an evidence route not yet represented, and the safety and privacy gates pass for it.
- Stop for futility where the last 2 activated trees added no new answer class, no new verified evidence, and no verifier-score improvement above the delta.
- Stop for convergence where the cluster-capped support clears the release threshold for the run's effective independence and the recorded accuracy conditional on agreement is acceptable for the task slice.
- Stop immediately on any hard cap, on any safety violation, or where cancellation has left no viable work, and never reset a counter between iterations of the loop.

**Forest Transition Vocabulary**:

| Transition | Precondition | Budget effect |
| :-- | :-- | :-- |
| ACTIVATE_TREE | All 4 activation conditions hold | Reserve debited by the worst-case allocation |
| RESUME_TREE | Suspension window open; blocking evidence now available | Retained allocation released to the tree |
| CONTINUE_TREE | Active tree improving above delta within its allocation | No reserve movement |
| CORRECT_NODE | Grounded trigger fired; anti-thrash caps not reached | Correction budget debited |
| AGGREGATE_AND_VERIFY | At least 2 frozen candidates present | Verifier budget debited |
| STOP_VERIFIED | Candidate passed every mandatory verifier | Remaining budget released |
| STOP_CONSENSUS | Threshold cleared at the effective independence tier | Remaining budget released |
| STOP_FUTILITY | Last 2 activations added nothing above delta | Remaining budget released |
| STOP_CAP | Any hard cap, safety violation, or cancellation | Remaining budget released |

**Required Outputs**:

- Exactly 1 recorded transition per decision point, with its reason code and its precondition evidence.
- An updated reserve balance reflecting the transition's budget effect.

**Quality Checkpoints**:

- Exactly 1 primary transition is issued per decision point; 0 or more than 1 halts the run.
- No activation occurs merely because capacity remains; an activation lacking any of the 4 conditions fails the checkpoint.
- No counter is reset between loop iterations; a reset halts the run.

***

#### Step 6.3: Apply the Release Gate or the Declared Non-Resolution Exit

**Required Actions**:

- Evaluate the release gate on 6 criteria: schema validity, domain or factual verification, evidence provenance, safety and authorisation, privacy redaction, and calibrated uncertainty.
- Require human approval for a consequential or irreversible action even where the forest agrees unanimously, since unanimity across correlated trees is not verification.
- Return the best verified partial result with its explicit limitations, escalate, or abstain where the gate fails, and never relabel majority agreement as verification.
- Construct the response within the disclosure boundary: the answer, the material evidence, the uncertainty, and a concise decision summary naming trees activated, cluster-capped support, and checks passed. Unrestricted intermediate reasoning, sensitive branches, security analysis, and adversarially retrieved text are never disclosed.
- Close every span, compute the run metrics, and queue high-cost, high-disagreement, safety-relevant, and oracle-gap cases for offline review.

**Required Outputs**:

- A release gate record with a verdict per criterion.
- A released response or a non-resolution record carrying its reason code and its limiting condition.
- A review queue entry for every case meeting a declared review trigger.

**Quality Checkpoints**:

- All 6 release criteria carry a verdict; an unevaluated criterion blocks release.
- No consequential or irreversible action is released on agreement alone; a missing human approval blocks release.
- The response discloses no unrestricted intermediate reasoning and no unsanitised retrieved text.

***

### Phase 7: Measurement Against Both Baselines and Policy Correction

**Objective**: Convert accumulated run records into a decision about whether the forest, its tree count, and its policies are retained, promoted, or withdrawn.

#### Step 7.1: Maintain the Run, Tree, Cluster, and Vote Record

**Required Actions**:

- Record at run level the trace and run identifiers, task type, risk tier, dataset and example versions, input hash, all 5 gate outcomes, baseline candidates and their verifier results, forest specification version, normaliser version, aggregation rule, thresholds, every hard budget, final status, winning class, contributing tree identifiers, fallback, abstention, human review, and retention class.
- Record at tree level the tree identifier, policy, method, correlation cluster, model and prompt versions, seed, evidence partition, namespace, activation order and trigger, all 6 activation priority components, allocation and usage, nodes generated and expanded, maximum depth, corrections, answer class, verifier result, deactivation reason, reclaimed amount, tokens, tool calls, cost, and latency.
- Record at aggregation level the vote event identifier, candidate hashes, class keys, eligibility and exclusion reasons, raw support, cluster-capped support, cluster contributions, independence tier and verdict, adjudicator identity and rubric where used, disagreement entropy, tie-break action, chosen candidate, and override source. Preserve every vote rather than only the aggregate.
- Record every sharing event and every controller grant, since these are the two channels by which the isolation contract and the budget partition can be violated without any single record looking anomalous.
- Apply the disclosure boundary to the whole record: log identifiers, classifications, verdicts, hashes, and provenance; do not persist credentials, unrestricted personal data, private reasoning, or full proprietary documents, and keep permitted payloads in protected storage referenced by content hash [10].

**Required Outputs**:

- A run record, a per-tree record, and a per-vote-event record for every executed run.
- A sharing ledger and a grant ledger for every executed run.
- A retention classification per record class with its expiry.

**Quality Checkpoints**:

- Every released answer traces to the tree identifiers, cluster assignments, and verifier results that produced it; an untraceable release fails the checkpoint.
- The record contains no unrestricted reasoning transcript and no unredacted sensitive payload; a breach withholds the record from export.
- Every activated tree carries all 6 priority components as recorded at its activation time, not as recomputed afterwards.

***

#### Step 7.2: Decompose the Oracle Gap Across Trees

**Required Actions**:

- Compute oracle coverage as the proportion of runs in which any tree generated a retrospectively correct candidate, and realised success as the proportion in which the released answer was correct.
- Attribute the difference to exactly one cause per run using lineage: normalisation failure, verifier false negative, vote failure, adjudicator failure, premature deactivation of the generating tree, scheduling, cancellation, or budget exhaustion.
- Report premature deactivation separately from the other causes, because it is the failure mode this method introduces and neither sibling measures it.
- Route the correction by the dominant cause: low oracle coverage indicates a generation and diversity problem addressed by policy changes in Step 2.2; a high gap at adequate coverage indicates a selection problem addressed by normalisation, verification, or cluster capping.
- Compute diversity from canonical answer-class count, unique-state ratio, action-type entropy, evidence overlap, tool-sequence overlap, and pairwise semantic similarity, and read high answer diversity with high invalidity as noise rather than as coverage.

**Oracle Gap Attribution Categories**: Normalisation failure, detected where the correct answer sits under a distinct class key, corrected by extending normaliser cases. Verifier false negative, where a verifier rejected a retrospectively correct candidate, corrected by recalibration on held-out outcomes. Vote failure, where the correct class was present but below threshold, corrected by revisiting cluster caps and the independence tier. Adjudicator failure, where a wrong class was ranked above a correct one, corrected by blinding, randomising, or withdrawing the adjudicator. Premature deactivation, where a deactivated tree's lineage held the correct path, corrected by relaxing the stagnation delta or widening the diversity reserve. Scheduling or cancellation, where the correct path was unexpanded at stop, corrected by revisiting activation priority or the concurrency cap. Budget exhaustion, where a hard cap fired with the correct path on the frontier, corrected by revisiting the breadth-versus-depth split.

**Required Outputs**:

- An oracle coverage figure, a realised success figure, and their gap per task slice.
- A gap attribution distribution with exactly 1 category assigned per gap run.
- A diversity measurement set with all 6 quantities per run.

**Quality Checkpoints**:

- Every gap run carries exactly 1 attributed cause; an unattributed gap run fails the checkpoint.
- Premature deactivation is reported as its own category and is never folded into budget exhaustion.
- Diversity is reported alongside validity; an answer-class count reported without an invalidity rate fails the checkpoint.

***

#### Step 7.3: Compute Marginal Tree Value and Issue the Promotion Decision

**Required Actions**:

- Compute marginal tree value at each cap from 2 to the configured maximum as verified success at cap N minus verified success at cap N minus 1 on the same examples under preregistered seeds, with paired bootstrap confidence intervals.
- Report alongside it the incremental tokens, cost, and latency per additional tree, and divide incremental successes by each resource increment so the diminishing-return curve is recoverable.
- Set the deployed activated-tree cap at the largest N whose lower confidence bound on marginal value remains positive, never at the largest N observed to help once.
- Run the required ablations before any promotion: the forest against the single-tree baseline, the forest against the sampling baseline, the forest with correction disabled, the forest with early deactivation disabled, and the forest with cluster capping disabled, all at matched worst-case budget.
- Measure seed and perturbation robustness across at least 5 preregistered seeds and all 5 perturbation classes: prompt wording, example order, evidence order, tree launch order, and injected instructions in retrieved content. Withhold promotion where the clean-to-stressed gap exceeds 20 percentage points.

**Required Outputs**:

- A marginal tree value curve with confidence intervals and per-resource increments.
- A deployed activated-tree cap with the bound that justified it.
- An ablation result set covering all 5 required comparisons and a robustness result set covering all 5 perturbation classes.

**Quality Checkpoints**:

- The deployed cap derives from a positive lower confidence bound; a cap set from a best observed point fails the checkpoint.
- All 5 ablations are present; a promotion decision missing any ablation is withheld.
- No configuration is promoted on clean-condition results alone, and a robustness gap above 20 percentage points blocks promotion.

***

## III. Implementation Guidance for AI Agents

AI agents operating a forest must follow systematic protocols ensuring that budget movement, isolation, and aggregation are performed outside the models whose outputs they govern. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Gate Agent**: Evaluates the 5 gates in Section 1.3 and returns launch, suppress, or a named cheaper route. It owns the overhead estimate and may refuse the forest.
2. **Budget Allocator**: Owns the partition, the reserve, per-tree allocations, atomic decrement, reclamation, and grants. No other component may move budget.
3. **Isolation Warden**: Assigns namespaces, enforces the freeze point in the orchestrator, writes the sharing ledger, and halts the run on an unlogged sharing event. It vetoes any read crossing a namespace boundary.
4. **Tree Executor**: One instance per tree. Runs its search controller inside its allocation, applies the deactivation test, and freezes its candidate. It may not observe a peer, extend its allocation, or change its policy.
5. **Forest Controller**: Computes activation priority and issues exactly 1 transition per decision point. It alone may activate, resume, suspend, deactivate, or stop.
6. **Aggregation Agent**: Extracts, normalises, classes, collapses duplicates, builds clusters, applies caps, computes the independence verdict, and evaluates the release gate. It never generates a candidate.
7. **Instrumentation Agent**: Writes the append-only records, enforces the disclosure boundary, and computes metrics. It may withhold export where a disclosure breach is detected.

**Separation requirement**: Generator, process evaluator, outcome verifier, aggregation, retrieval, and tool services run as separate components. Fusing them permits shared-context contamination the sharing ledger cannot detect, because no boundary was crossed to record.

**Workflow Execution Pattern**:

```
STATE: Forest_Activation_Decision
INPUTS:
  1. Frozen candidate set with class keys from Step 5.1
  2. Cluster-capped support and independence verdict from Step 5.2
  3. Forest reserve balance per dimension from the Budget Allocator
  4. Activation priority table from Step 6.1
  5. Sharing ledger and grant ledger entries for this run
ACTIONS:
  1. Test the release threshold at the run's effective independence tier
  2. Rank unactivated policies by expected verified gain per unit cost
  3. Test the 4 activation conditions against the highest-ranked candidate
  4. Select exactly one transition from the closed vocabulary
VALIDATION:
  - primary_transition_count == 1
  - reason_code IN closed_vocabulary
  - reserve_covers_worst_case == TRUE IF transition == ACTIVATE_TREE
  - new_correlation_cluster == TRUE IF transition == ACTIVATE_TREE
  - distinct_clusters_supporting_leader >= 2 IF transition == STOP_CONSENSUS
  - unlogged_sharing_events == 0
  - counters_reset_since_last_cycle == FALSE
TRANSITIONS:
  IF transition IN {ACTIVATE_TREE, RESUME_TREE, CONTINUE_TREE, CORRECT_NODE}
     THEN next_state = Per_Tree_Execution
  IF transition == AGGREGATE_AND_VERIFY THEN next_state = Cross_Tree_Aggregation
  IF transition IN {STOP_VERIFIED, STOP_CONSENSUS} THEN next_state = Release_Gate
  IF transition IN {STOP_FUTILITY, STOP_CAP} THEN next_state = Non_Resolution_Exit
  IF validation_failed THEN next_state = Forest_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended transition with its priority components, reserve check, and cluster check without executing it; confirm it against the validation block while no resource is committed; commit it only after validation passes, debiting the reserve in the operation that records it.

**Approval Gate**: Human authorisation is required before releasing any irreversible or consequential action irrespective of support, before activating a tree whose worst-case allocation exceeds 40 percent of the remaining reserve, before any release whose effective independence rests on a single cluster, and before any relaxation of the isolation contract. Agents halt at these gates rather than proceed with a recorded warning.

**Context Management Requirements**:

- Hold the run contract, budget ledger, sharing ledger, and cluster assignments in durable state outside any model context, since the forest outlives a context window.
- Give each tree only its own namespace contents; never assemble a shared context holding several trees' intermediate states, because one context reintroduces the channel the isolation contract closes.
- Summarise a completed tree to its sanitised consensus record, retaining the trajectory under hash.
- Count controller, aggregation, and instrumentation context consumption toward run overhead.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Gate and Justification Integrity (After Phase 1)**

- **Automated Check**: All 5 gates carry a verdict; both sides of the cost-justification inequality pass at matched worst-case budget; every budget dimension carries a numeric limit.
- **Agent Action on Pass**: Proceed to budget allocation.
- **Agent Action on Failure**: Halt and route to the named cheaper baseline; no tree is launched against a failed gate.
- **Human Review Trigger**: A projected cost multiple above 8 relative to the better baseline, or a task in the highest risk tier.

**Checkpoint 2: Partition Validity (After Phase 2)**

- **Automated Check**: Reserve at least 40 percent on every dimension where sequential activation is authorised; no tree below its floor; no tree above 50 percent of the non-reserve node budget; allocations plus reserve within every cap.
- **Agent Action on Pass**: Proceed to isolation setup.
- **Agent Action on Failure**: Recompute the partition; an over-committed partition is never launched with a warning.
- **Human Review Trigger**: A measured sibling ranking accuracy below 65 percent for every candidate policy.

**Checkpoint 3: Isolation Integrity (After Phase 3)**

- **Automated Check**: No cross-namespace read path; freeze enforcement located in the orchestrator; every tree carries 1 independence tier and 1 source class; the sharing ledger is append-only with a named detection method.
- **Agent Action on Pass**: Proceed to launch.
- **Agent Action on Failure**: Halt the run; an isolation defect is never mitigated by a prompt instruction.
- **Human Review Trigger**: Any authorised cross-pollination round, or any shared retrieval core without 2 distinct query formulations.

**Checkpoint 4: Execution and Reclamation Integrity (After Phase 4)**

- **Automated Check**: Every deactivation paired with an atomic reclamation entry; no tree over 3 corrections and no node over 2; no counter reset; no tree consuming a peer allocation without a recorded grant.
- **Agent Action on Pass**: Proceed to aggregation.
- **Agent Action on Failure**: Quarantine the affected tree and re-run reclamation accounting only, not the whole forest.
- **Human Review Trigger**: More than 30 percent of launched trees deactivated for no-valid-output within one run.

**Checkpoint 5: Aggregation Integrity (After Phase 5)**

- **Automated Check**: Every candidate classed by the versioned normaliser; every policy in exactly 1 cluster; no cluster above 40 percent of eligible support; the release comparison performed on cluster-capped support.
- **Agent Action on Pass**: Proceed to the activation decision.
- **Agent Action on Failure**: Halt aggregation and return the specific defect; a tally is never released with a known classing defect.
- **Human Review Trigger**: Effective independence resting on a single correlation cluster, or a verified minority overriding a majority.

**Checkpoint 6: Transition and Release Validity (After Phase 6)**

- **Automated Check**: Exactly 1 transition; reason code in the closed vocabulary; all 4 activation conditions where an activation occurred; all 6 release criteria evaluated; human approval present where required.
- **Agent Action on Pass**: Release the response and close the run.
- **Agent Action on Failure**: Halt; an invalid transition is never executed with a warning attached.
- **Human Review Trigger**: The same transition issued at 3 consecutive decision points without measured improvement.

**Checkpoint 7: Measurement Sufficiency (After Phase 7)**

- **Automated Check**: Every gap run attributed to exactly 1 cause; all 5 ablations present; at least 5 preregistered seeds and all 5 perturbation classes covered; the deployed cap justified by a positive lower confidence bound.
- **Agent Action on Pass**: Permit promotion of the configuration.
- **Agent Action on Failure**: Withhold promotion and name the missing evidence.
- **Human Review Trigger**: A robustness gap above 20 percentage points, or premature deactivation exceeding 20 percent of the attributed oracle gap.

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
```

### C. Error Handling and Troubleshooting

**Error Type 1: Correlated Unanimity Across Trees**

- **Symptoms**: Every tree returns one answer class; agreement is high while accuracy conditional on agreement is low on the labelled slice; supporting trees resolve to one correlation cluster; disagreement entropy is near zero at high cost.
- **Diagnostic Steps**: Trace every supporting tree to its source class, cluster, and evidence partition, and determine whether agreement survives removal of the shared base model, the shared retrieval core, or the shared decomposition template.
- **Resolution Protocol**: Option A, commission a policy in an unrepresented cluster, changing model family or evidence route rather than temperature. Option B, replace the tally with a deterministic verifier where one exists for the answer type. Option C, release with an explicit correlated-agreement marker at no more than the low-risk tier. Option D, abstain and record the missing lever.
- **Escalation Trigger**: A highest-risk-tier conclusion resting on single-cluster agreement escalates immediately; this class is never resolved by activating more trees inside the same cluster.

**Error Type 2: Isolation Breach and Cross-Tree Contamination**

- **Symptoms**: A tree's output contains content it had no authorised path to; canonical state hashes converge across namespaces; an injected instruction from retrieved content appears in a peer tree or in an adjudicator prompt.
- **Diagnostic Steps**: Read the sharing ledger for events preceding the affected freeze points; confirm whether the channel was an authorised cross-pollination round, a shared cache key, a shared context assembly, or an unlogged path.
- **Resolution Protocol**: Option A, cluster the affected trees together and recompute support under the cap. Option B, discard the contaminated candidates and re-launch those policies in fresh namespaces. Option C, halt the run where the channel is unlogged, since an undetected channel invalidates every independence claim in the run.
- **Escalation Trigger**: Any sharing event with no recorded detection method halts the run and escalates; this class is never resolved by recording the event after the fact.

**Error Type 3: Budget Overrun From Concurrent Trees**

- **Symptoms**: Consumed cost exceeds the run cap; calls complete after a verified success; a correction or retry appears to have restored a counter; the reserve balance disagrees with the sum of reclamations.
- **Diagnostic Steps**: Reconcile the budget ledger against the grant ledger and the reclamation entries per dimension, and locate the overrun in concurrent retries, post-success calls, nested internal reasoning, or a non-atomic decrement.
- **Resolution Protocol**: Option A, replace the read-then-write decrement with an atomic counter and reserve allocations before launch. Option B, propagate cancellation to queued calls on verified success. Option C, reduce the concurrency cap so worst-case simultaneous spend fits the reserve.
- **Escalation Trigger**: A second overrun after an accounting correction escalates for policy review; the forest is never continued on remaining budget alone.

**Error Type 4: Correction Thrashing Inside a Tree**

- **Symptoms**: Revisions alternate between equivalent states; the same defect signature recurs; verifier score falls after an accepted revision; correction spend rises with flat verified progress.
- **Diagnostic Steps**: Compare correction attempts against accepted revisions and against verified progress per tree, and confirm whether each trigger was grounded in a checker result rather than in a generic review instruction.
- **Resolution Protocol**: Option A, tighten the trigger set to failed checkers and contradictions with trusted evidence only. Option B, lower the per-tree correction cap to 1 for the affected policy. Option C, abandon correction for that tree and spend the reserve on a policy in a different cluster.
- **Escalation Trigger**: Two consecutive revisions failing the same check terminates the loop; a third attempt against one defect signature is prohibited regardless of remaining correction budget.

**Error Type 5: Premature Deactivation of the Generating Tree**

- **Symptoms**: The oracle gap attributes to premature deactivation; a deactivated tree's lineage contained a retrospectively correct path; deactivation rate rises while realised success falls.
- **Diagnostic Steps**: Replay the deactivated trees from their checkpoints against the labelled slice, and determine whether the trigger was validity failure, an evaluator score, or a stagnation delta set too tight.
- **Resolution Protocol**: Option A, widen the stagnation delta and lengthen the rounds before deactivation fires. Option B, convert deactivation to suspension for trees carrying verified partial progress. Option C, retain a bounded diversity reserve so a low-scoring policy is never the last of its cluster to be deactivated.
- **Escalation Trigger**: Premature deactivation exceeding 20 percent of the attributed oracle gap suspends the current deactivation policy for that task slice pending recalibration.

**Error Type 6: Latency Blowup From the Slowest Tree**

- **Symptoms**: p95 and p99 wall time greatly exceed the median; aggregation waits on one tree; serial adjudication dominates the tail.
- **Diagnostic Steps**: Decompose wall time into per-tree execution, fan-in wait, verification, and adjudication, and identify whether the tail sits in one policy or in the aggregation layer.
- **Resolution Protocol**: Option A, launch the minimum viable forest and activate sequentially rather than launching the cap. Option B, apply a per-tree deadline that suspends rather than waits. Option C, adjudicate only genuine disagreement and run cheap deterministic checks first.
- **Escalation Trigger**: A p99 above the contract deadline in 2 consecutive measurement windows withdraws the configuration from latency-bound routes.

**Troubleshooting Decision Tree**:

```
FOREST RUN FAILS A CHECKPOINT
├─ INDEPENDENCE DEFECT
│   ├─ All supporting trees in one cluster → Cap at one tree; activate a new cluster or abstain
│   ├─ Unlogged sharing event detected → HALT run; escalate; no post-hoc recording
│   └─ Authorised cross-pollination present → Create descendant tree; inherit source clusters
├─ BUDGET DEFECT
│   ├─ Reserve balance disagrees with reclamations → HALT; reconcile ledgers atomically
│   ├─ Calls complete after verified success → Propagate cancellation; reduce concurrency
│   └─ Counter reset by a correction → HALT; corrections never restore counters
├─ EXECUTION DEFECT
│   ├─ Same defect signature twice → Terminate correction loop; backtrack or deactivate
│   ├─ Tree deactivated with correct lineage → Widen stagnation delta; prefer suspension
│   └─ Malformed output after one reparse → Deactivate with reason code; do not regenerate
├─ AGGREGATION DEFECT
│   ├─ Class key written outside the normaliser → Reject; re-class deterministically
│   ├─ Cluster above 40 percent of support → Scale down; discard excess, never redistribute
│   └─ Majority above a verified minority → Release the verified candidate; record override
└─ DISCLOSURE DEFECT
    ├─ Raw trajectory in a consensus record → Withhold export; forward hashes only
    └─ Peer transcript forwarded to a judge → Reject adjudication; re-run blinded
```

### D. Performance Metrics and Continuous Learning

**Outcome and Selection Metrics**:

- **Verified success rate**: Eligible runs releasing a candidate that passed every mandatory verifier, stratified by task, difficulty, model, policy, and budget (target: above both baselines by the minimum delta for the cost multiple).
- **Consensus rate**: Runs meeting the support threshold at their effective independence tier (target: at least 60 percent; below 40 percent indicates a forest too small or too diverse to resolve).
- **Accuracy conditional on agreement**: Correctness among agreed runs carrying ground truth (target: at least 90 percent; less, at high agreement, is a correlated-error alarm).
- **Oracle gap**: Oracle coverage minus realised success (target: no more than 10 percentage points; a larger gap directs effort to selection rather than to generation).
- **Minority-verifier win rate**: Runs where a verified minority candidate was released over a larger unverified class (target: reported, not minimised, since suppressing it means the verifier is being overruled).

**Allocation and Efficiency Metrics**:

- **Marginal tree value at the deployed cap**: Verified success gain from the last authorised tree (target: lower confidence bound above zero; non-positive withdraws the cap).
- **Activation efficiency**: Verified successes attributable to the forest over activated-tree cost above the cheapest adequate baseline (target: positive median).
- **Reclamation accuracy**: Reserve balance agreement with allocations, grants, and reclamations (target: exact; any divergence halts the run).
- **Forest overhead**: Controller, aggregation, and instrumentation cost over run cost (target: no more than 30 percent; above 40 percent triggers policy review).
- **Cost per solved task**: Total cost over verified successes, with median, p90, p95, and p99 (target: below both baselines at matched quality).
- **Premature deactivation share**: Oracle gap attributed to deactivating a tree whose lineage held a correct path (target: no more than 20 percent).

**Diversity and Correlation Metrics**:

- **Cluster count at release**: Distinct clusters supporting the released class (target: at least 2 above the low-risk tier).
- **Pairwise conditional error**: Probability one policy is wrong given another is wrong, per pair and slice (target: below 0.70 for policies intended as distinct).
- **Evidence and tool-sequence overlap**: Shared retrieved items and tool sequences across policies (target: reported per cluster; rising overlap predicts cluster collapse).
- **Sharing event count**: Recorded pre-freeze sharing events per run (target: 0; any non-zero value is investigated before the run's independence figures are used).

**Learning and Adaptation Mechanisms**:

- **Slice-level policy memory**: Retain task features, activated policies, clusters, cost, outcome, and failure mode per run, so activation priority improves against observed history.
- **Cluster remeasurement**: Recompute pairwise conditional error whenever a model, prompt, decomposition template, or retrieval index version changes, since a stale cluster map understates correlation.
- **Threshold recalibration**: Recompute the activation delta, the stagnation delta, and the cluster cap per task class; the values stated here are deployment defaults, not constants.
- **Paired promotion**: Promote a policy or weight change only after paired, seed-repeated, budget-matched evaluation against both baselines, never on an aggregate benchmark score.

**Human-in-the-Loop Boundaries**: Relaxation of the isolation contract, release of an irreversible action on agreement alone, promotion of a configuration whose advantage appears only under clean conditions, and any increase to the activated-tree cap beyond the offline curve's positive bound are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the allocation of budget across isolated searches rather than the content of any particular search. Its phases hold wherever a task admits more than one solution strategy, produces candidates that can be normalised and externally checked, and carries a cost for activating another attempt.

### 4.1 Cross-Domain Application Patterns

**Quantitative and symbolic analysis**: Answer equivalence is mechanical and a symbolic checker supplies the strongest independence signal, so release rests on verification rather than on the tally. Policies differ by decomposition: forward construction, backward reasoning from the target, and program-aided evaluation. The deployed activated-tree cap is set from the marginal-value curve, because additional trees stop paying earlier than intuition suggests.

**Software defect repair**: A test suite is the decisive verifier, so a minority candidate passing the suite is released over any majority. Policies differ by repair strategy: minimal patch, root-cause refactor, and test-first reconstruction. Sandboxed execution is mandatory, and the isolation contract matters most here, because one tree observing another's patch converges the forest on the first plausible fix rather than the correct one.

**Evidence-based investigation**: No deterministic verifier exists for the conclusion, so the forest carries disjoint evidence partitions and different retrieval methods, and clusters form on shared sources rather than on shared models. The dominant failure is a shared retrieval core producing correlated blindness, which is why Step 3.1 requires distinct query formulations.

**Regulated decision support**: Risk is high and most actions are irreversible, so the approval gate binds before any recommendation, an expert adjudicator may never decide, and the record becomes a deliverable rather than a diagnostic aid. Policies are chosen for externally auditable evidence, and abstention is preferred over an unverified release.

**Operations and constraint planning**: A simulator supplies frequent external signals, so per-tree checkpoints are short and deactivation fires early. Reversibility varies within one run, so thresholds bind per action class. Latency dominates, so the forest launches its minimum and activates sequentially rather than waiting on the slowest of a full cap.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk reversible work**: Launch 2 trees, hold no reserve beyond one activation, and accept release at the low-risk threshold. Forest overhead above 15 percent of direct-execution cost indicates the gate should have suppressed the forest.
- **High-risk or irreversible work**: Retain every phase, require at least 2 distinct clusters supporting the released class and at least 1 deterministic verification signal, and bind the approval gate before release; abstention is preferred over unverified completion.
- **Strict latency budgets**: Reduce the initial tree count rather than removing the aggregation layer, since removing aggregation removes what makes a forest more than parallel guessing. Apply per-tree deadlines that suspend rather than block fan-in.
- **Long-horizon autonomous runs**: Persist the contract, ledgers, checkpoints, and cluster map outside working context, and re-run the reclamation reconciliation at every context boundary so accounting drift is detected rather than inherited.
- **Multi-tenant deployments**: Enforce tenant isolation on namespaces, caches, traces, and object storage, and never share a cache entry across changed facts, permissions, rubrics, or model snapshots, since a shared cache is a channel the ledger will not see.

***

## V. Limitations and Considerations

**The multiplier compounds**: A forest multiplies an already expensive method, and the default cap of 8 activated trees can reach several hundred times the cost of a direct response. The consequence is that a favourable accuracy comparison can conceal an unaffordable deployment. The mitigation is the two-sided cost-justification rule in Step 1.2 and the marginal-value curve in Step 7.3, which sets the cap from a positive lower confidence bound.

**Isolation is enforceable only where the orchestrator sees the boundary**: Shared caches, shared context assembly, shared evaluator services, and shared retrieval indexes cross namespaces without generating a boundary crossing to record. The consequence is that a sharing ledger can read zero while trees are in fact correlated. The mitigation is the separation requirement in Section III.A, the cache-key rule in Section 4.2, and the treatment of a shared retrieval core as a declared correlation source in Step 3.1.

**Independence is measured, not guaranteed**: Correlation clusters are fitted on labelled held-out data that may not represent the deployment distribution, and membership drifts whenever a model, prompt, or index version changes. The consequence is a cluster map that understates correlation and a threshold cleared on false diversity. The mitigation is the remeasurement cadence in Section III.D and the fallback to declared policy similarity where labelled data for a pair is unavailable.

**The source's quantitative claims are benchmark-specific and were not re-verified**: The success rates, invocation counts, and ablation figures attributed to the primary paper are transcribed from the originating prose guide as it reported them, and only that paper's title and authorship were confirmed during conversion. The source further records that the paper's main table and its narrative disagree on one baseline figure for one benchmark. The consequence is that these figures orient rather than predict, and that any decision resting on the inconsistent comparison is unsafe. The mitigation is that no threshold here derives from them, that Step 1.2 requires a measurement on the deployment distribution before promotion, and that the tabulated value is used with an explicit discrepancy flag as the source recommends.

**Benchmark coverage is narrow**: The evidence behind this method is dominated by verifiable mathematics and puzzles, where answer equivalence is mechanical and ground truth is available. The consequence is that open-ended research, policy, and agent-action tasks inherit noisier equivalence and weaker verification than the reported results assume. The mitigation is the Selection Gate, which refuses the method where no validated normaliser and no outcome verifier exist.

**Correction can destroy a correct answer**: Revision without a localised external signal degrades initially correct responses [4], and the primary paper's correction combines score thresholds with embedded domain rules rather than free-form reflection [1]. The consequence is that a production replica retaining only the reflection language will lose accuracy it would otherwise have kept. The mitigation is the grounded-trigger requirement and the anti-thrash caps in Step 4.3.

**Early deactivation was demonstrated as efficiency, not accuracy**: The source reports an ablation in which sparse activation left accuracy unchanged while reducing average invocations [1]. The consequence is that deploying it in the expectation of an accuracy gain misallocates improvement effort. The mitigation is to judge deactivation by the premature-deactivation share in Step 7.2 rather than by accuracy.

**Thresholds here are deployment defaults**: Every numeric bound in this guide, including the 40 percent reserve, the 40 percent cluster cap, the 0.70 conditional-error boundary, the correction caps, and the 8-tree cap, was chosen to be operable on first deployment rather than derived from a measured property of forests. The consequence is that a deployment inheriting them unchanged will be mis-tuned for its slice. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute them per task class against observed outcomes.

**Multiplied state multiplies exposure**: A forest generates several times the intermediate text, retrieved evidence, and tool observations of a single tree, each a retention and leakage surface. The consequence is that a logging configuration adequate for one tree becomes a disclosure risk at forest scale. The mitigation is the disclosure boundary in Step 7.1 and the Privacy and Tool-Safety Gate.

**Structural conformance is not sound selection**: A run can satisfy every checkpoint here and still release a wrong answer every tree reached for the same reason. The framework detects malformed allocation, broken isolation, and uncapped correlation; it does not detect a premise all policies inherited. The mitigation is the external-signal requirement above the low-risk tier, and no checkpoint substitutes for human review of the premise.

***

## VI. Conclusion and Summary

Forest-of-thought reasoning is an allocation discipline before it is a reasoning technique. Its trees are ordinary bounded searches and its tally is an ordinary equivalence-class vote; what the forest adds is the decision about where the next unit of budget goes, the contract that keeps trees from informing one another before their answers are fixed, and the accounting that returns an unproductive tree's budget to the pool. A deployment getting those three right converts additional trees into complementary verified coverage; one getting them wrong pays several hundred times a direct response for a unanimity manufactured by shared premises.

A team introducing a forest should instrument both baselines first, then add exactly 1 tree in a deliberately different correlation cluster behind an explicit activation delta. Measure that tree's marginal value at matched worst-case budget before authorising a third, and read the oracle gap before enlarging the forest, because a gap at adequate coverage is a selection problem that more trees make worse. Only then add correction, early deactivation, and expert adjudication, each measured by its own ablation.

**Key Success Factors**:

- **Isolation before consensus**: Trees do not observe one another before their freeze points, and any agreement across a recorded sharing event is classified as correlated rather than confirming.
- **Two-level budget accounting**: A reserve funds the activation decision, per-tree allocations are reserved before launch, deactivation returns unspent budget atomically, and no correction resets a counter.
- **Diversity that is measured, not asserted**: Correlation clusters are fitted on labelled data, cluster weight is capped, and seeds are never accepted as a diversity mechanism.
- **Verification outranks agreement**: A deterministic verifier decides over any tally, a verified minority is released over an unverified majority, and no agreement authorises an irreversible action.
- **Bounded termination**: Every loop carries entry, exit, stagnation, and hard-cap conditions, and the activated-tree cap is set from a positive lower confidence bound rather than from a best observed point.
- **Justification against both baselines**: The forest is promoted only where it beats the single-tree and the sampling configuration at matched worst-case budget, and is withdrawn when either comparison fails.

By following this guide, AI agents can spend a multiplied inference budget on the smallest set of isolated, auditable searches that produces a verified answer, and can stop when the next tree no longer earns its cost.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides that own mechanisms invoked rather than defined here. The external references are transcribed from the originating prose guide as it cited them. Four entries were retrieved during conversion and are marked as verified; for those, the title and first author were confirmed against the retrieved page, and for entries 5 and 6 the figures the source attributes to them were confirmed as well. The remaining entries were not independently re-verified, and every empirical figure attributed to them is carried as a claim of the source rather than as an asserted fact.

**Corpus pointers**:

- `Production Guide to Forest-of-Thought Reasoning` — the originating prose guide from which this operational guide was derived. Source of the tree identity and isolation rules, the diversity measurement inventory, the sparse activation and allocation logic, the consensus and selection rules, the correction loop and its anti-thrash guards, the production workflow, the logging inventories, the metric definitions, the failure-mode catalogue, and the deployment acceptance checklist.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/reasoning/guide_TreeOfThought.md` — owns everything inside one tree: the canonical state schema, the transition validator, the evaluator admission bar, frontier ordering, pruning, backtracking, and within-tree termination. Step 4.2 invokes that procedure, and its budget ledger, reason code, and exit condition vocabulary are adopted unchanged. It is also the single-tree baseline of Step 1.2.
- `advanced_task_guides/reasoning/guide_ReflectiveMonteCarloTreeSearch.md` — the Monte Carlo variant of the within-tree procedure, adding visit counts, a selection rule, return backup, progressive widening, and a scoped lesson store to the tree guide above, whose evaluator and pruning rules it adopts unchanged. It is the applicable variant where the evaluation signal comes from rollouts rather than from state scores. Its lesson store is scoped to one search, so a lesson raised inside one tree may not be retrieved by another without breaching the isolation contract this guide imposes.
- `advanced_task_guides/reasoning/guide_SelfConsistency.md` — owns the diversification ladder, the independence tier scale and its release weights, answer extraction, normalisation, equivalence classing, duplicate collapse, tallying, the independence assessment, and abstention. That vocabulary is adopted without modification; this guide adds only the correlation-cluster layer and the sharing ledger. It is the sampling baseline of Step 1.2.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — the control-layer companion, owning correlated failure, source class, value-of-computation control, the decision contract, and abstention as a declared exit. Those terms are adopted unchanged.
- `advanced_task_guides/reasoning/guide_GraphOfThought.md` — the alternative named in the gate routing table, covering aggregated reasoning over an acyclic dependency graph with verified provenance, applicable where intermediate products must merge rather than remain isolated.
- `advanced_task_guides/reasoning/guide_ChainOfThoughtReasoning.md` — the single-chain baseline named in the Step 1.2 ladder, covering the warrant gate for intermediate reasoning and the non-evidential status of a reasoning trace.
- `advanced_task_guides/reasoning/guide_ChainOfVerification.md` — companion guidance on independently verified claim revision, applicable to Step 5.3 and the release gate in Step 6.3.
- `advanced_task_guides/reasoning/guide_MetacognitiveMonitoring.md` — companion guidance on calibrated monitoring signals, applicable to the evaluator calibration in Step 2.2 and the conditional-accuracy measurement in Step 5.2.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the records required by Step 7.1.
- `advanced_task_guides/scoring/guide_complexityScoring.md` — a compact scoring rubric usable as an input to the difficulty routing in Section 4.2.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, II, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Forest-of-thought and adjacent multi-path architectures*

1. Bi and colleagues, *Forest-of-Thought: Scaling Test-Time Compute for Enhancing LLM Reasoning* — https://arxiv.org/abs/2412.09078 (title and first author verified during conversion)
2. Wang and colleagues — https://arxiv.org/abs/2203.11171
3. Besta and colleagues, the graph-of-thought framework — https://arxiv.org/abs/2308.09687

*Self-correction, repeated sampling, and test-time compute allocation*

4. Huang and colleagues, *Large Language Models Cannot Self-Correct Reasoning Yet* — https://arxiv.org/abs/2310.01798 (title and first author verified during conversion)
5. Brown and colleagues, *Large Language Monkeys: Scaling Inference Compute with Repeated Sampling* — https://arxiv.org/abs/2407.21787 (title, first author, and the coverage figures cited by the source verified during conversion)
6. Snell and colleagues, *Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters* — https://arxiv.org/abs/2408.03314 (title, first author, and the efficiency figures cited by the source verified during conversion)
7. DeepSeek-R1 report — https://arxiv.org/abs/2501.12948

*Provider guidance, instrumentation, and injection*

8. OWASP, *prompt-injection guidance* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
9. OpenAI, *reasoning guidance* — https://developers.openai.com/api/docs/guides/reasoning-best-practices
10. OpenTelemetry, *GenAI semantic conventions* — https://opentelemetry.io/docs/specs/semconv/gen-ai/
