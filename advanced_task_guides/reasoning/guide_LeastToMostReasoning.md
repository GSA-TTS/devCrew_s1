# Least-to-Most Reasoning

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Least-to-most reasoning constitutes the task family of answering a question too compositional to answer directly by decomposing it into an ordered set of answerable subproblems, solving them in dependency order, and feeding each verified answer forward so that later subproblems consume earlier results rather than re-deriving them. This guide provides AI agents with a structured protocol covering the decision not to decompose, bounded decomposition generation gated on ordering and completeness, derivation of a typed dependency graph that permits parallel execution of independent nodes, sequential solving with a verification ladder run before any answer is committed, invalidation and bounded re-decomposition when a node fails, and composition of the terminal answer under an external release gate. The property the protocol exists to govern is error propagation: because each step consumes the previous answer, a wrong early answer corrupts every descendant, and the corruption is silent because later steps operate correctly on bad input. The framework therefore prohibits feeding an unverified answer forward, rejects rather than patches a decomposition failing the ordering or completeness check, bounds every retry numerically, and attributes each failed run to its earliest bad ancestor so that decomposition quality and solver quality are measured separately.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Least-to-most reasoning**: A two-stage inference pattern in which a decomposition stage generates an ordered list of subproblems and a solving stage answers them in order, accumulating prior question-answer pairs so that each subproblem is answered in the presence of its prerequisites, with the original question appearing as the final subproblem [1]. The pattern is top-down reduction followed by bottom-up construction.

**Subproblem**: One answerable question derived from the original question, carrying a contract, a declared answer type, a set of permitted evidence sources, a verifier, and a dependency set. A subproblem is a question to answer, not a task to execute. Text that merely names a stage of work without an answer type is a plan step, not a subproblem.

**Node**: One versioned subproblem instance in the executable graph, carrying identity, logical-node identifier, version, type, canonical contract hash, depth, topological position, optionality, readiness, lease, answer, evidence identifiers, verification state, cache disposition, and terminal status.

**Node contract**: The metadata record attached to a single node, comprising the question text, the declared answer schema and units, the required ancestor fields consumed, the permitted evidence sources, the authorised tools, the verifier assignment, and the local token allocation. Descendants consume the node contract and the accepted answer, never the node's working draft.

**Dependency edge**: A typed directed relationship from a producer node to a consumer node, classified as hard where the consumer cannot be answered without the producer's accepted answer, and soft where the producer's answer improves but does not determine the consumer. Only hard edges constrain execution order; soft edges constrain context assembly.

**Dependency graph**: The acyclic directed graph formed by nodes and their hard edges, from which execution order is computed. Least-to-most does not imply a single linear chain; it implies that prerequisites precede consumers.

**Terminal node**: The node carrying the original question, appended as the last node of every accepted decomposition. A decomposition whose terminal node is not the original objective has not preserved the question being answered.

**Ready frontier**: The deterministically computed set of unsolved nodes whose hard parents all hold accepted answers. The frontier is a data structure owned by the scheduler, not a judgement made by a model.

**Answer propagation**: The release of a node's accepted answer into the context of its consumers. Propagation occurs only after commit, and only the accepted version and its compact contract propagate.

**Commit**: The irreversible transition of a node from solved to accepted, permitted only when every hard verification check has passed. Commit is the sole event that makes an answer load-bearing.

**Error propagation**: The corruption of every descendant of a node whose accepted answer is wrong. Propagation is silent, because descendants operate correctly on bad input and produce fluent, internally consistent, wrong results.

**Invalidation wave**: The set of nodes marked stale when an ancestor's accepted version is superseded or reversed, computed by transitive hard-edge traversal from the changed node. Cached descendant results do not survive an upstream version change.

**Localization distance**: The number of executed nodes between the first incorrect accepted answer and the point at which a verifier detected a defect. A large localization distance means verification is happening too far downstream of the error.

**Error amplification**: The count of invalid descendant nodes attributable to one first bad ancestor. It is the direct measure of how much a single false accept cost the run.

**Decomposition-Need Gate**: The deterministic decision, taken after cheaper baselines have run and before any decomposition is generated, returning decompose, suppress, or route to a named alternative technique.

**Decomposition-Quality Gate**: The gate applied to a candidate decomposition, combining deterministic graph checks with a calibrated judge over residual criteria, and returning accept, repair with named defects, or reject.

**Ordering check**: The deterministic test that no subproblem references a result produced by a later subproblem, established by confirming every referenced field resolves to an ancestor and that the graph is acyclic under topological sort.

**Completeness check**: The deterministic test that the accepted node set covers every information item and operation the terminal answer requires, established against a declared required-item set rather than against an impression of thoroughness.

**Verification ladder**: The ordered sequence of checks a node's answer must pass before commit, running cheapest and most deterministic first: schema, type, unit, range, identity, access, and invariant checks, then authorised retrieval or sandboxed tool execution, then an independent model verifier restricted to criteria the earlier rungs left unresolved.

**Re-decomposition**: The bounded replacement of a failed node and its descendants with a new subgraph, preserving verified ancestors, validated by the same gates as the original decomposition, and counted against a run-wide cap.

**Decision contract**: The declared objective, output schema, hard constraints, permitted evidence, tool permissions, risk tier, acceptance tests, abstention tests, and every numeric cap, fixed before the first model call.

**Budget ledger**: The run-wide record naming every bounded resource and its numeric limit, decremented atomically at reservation rather than at completion: subproblems, depth, decomposition candidates, repairs, re-decompositions, model calls, tool calls, tokens, currency cost, wall time, retained bytes, and concurrency.

**Source class**: The label attached to every verification signal naming its origin: deterministic function, executed program, schema validator, retrieved primary source, tool postcondition, independent model verifier, or human adjudication. Signals sharing a source class are not independent.

**Correlated failure**: Agreement among solvers, samples, or verifiers sharing a generator, prompt, premise, or evidence source, mistaken for independent confirmation.

**Reason code**: A normalised categorical label recorded with every gate verdict, commit, suspension, invalidation, re-decomposition, and exit, drawn from a closed vocabulary.

**Disclosure boundary**: The rule permitting the logging of decision metadata while prohibiting retention or exposure of private chain-of-thought, unrestricted subproblem drafts, credentials, hidden security policy, and injected instruction text.

**Exit condition**: A declared terminal state that alone may end a run: verified success, labelled verified partial result, safe abstention, human takeover, budget exhaustion, unrecoverable dependency defect, or safety violation.

### 1.2 Boundary Against Neighbouring Decomposition and Search Patterns

Decomposition appears in several corpus patterns, and the distinctions are load-bearing because they determine which artifact carries state and which component holds authority.

**Against goal decomposition**: `advanced_task_guides/planning/guide_IntelligentGoalDecomposition.md` owns the decomposition of an objective into subgoals and tasks, producing a goal tree of desired states that a downstream planner or executor consumes. Least-to-most owns the decomposition of a question into subquestions, producing answers that feed forward into later subquestions within one reasoning run. A goal node is satisfied by work performed in the world; a least-to-most node is satisfied by an answer verified against evidence. Where a run must both restructure an objective and answer a composed question, the goal decomposition runs first and supplies the objective that this pattern's decision contract records.

**Against hierarchical task network planning**: `advanced_task_guides/planning/guide_HierarchicalTaskNetworkPlanning.md` owns the refinement of compound tasks into primitive tasks using a versioned library of authored methods, with backtracking across choice points. Its decomposition is drawn from a curated domain model; least-to-most decomposition is generated per run by a model and must therefore be evaluated as output rather than trusted as a library artifact. Where the workflow graph is known in advance and a model-generated decomposition adds no value, a fixed network or plain directed acyclic workflow is the correct pattern and this one is suppressed.

**Against modular subtask routing**: Decomposed Prompting routes subproblems to modular handlers such as prompts, functions, retrieval, or specialised models, emphasising heterogeneous subtask types rather than sequential accumulation [4]. Stable heterogeneous modules favour that pattern; a per-run generated dependency sequence favours this one.

**Against incremental question generation**: Successive Prompting generates and answers the next question iteratively instead of planning all subproblems first, separating question generation from answer supervision, and reported an improvement of approximately 5 absolute F1 points on a few-shot version of the DROP dataset [5]. Use it where each answer reveals what the next question must be; use full-plan least-to-most where global coverage can be validated before solving begins.

**Against plan-then-execute prompting**: Plan-and-Solve creates and executes a plan to reduce missing-step and calculation errors in zero-shot chain-of-thought [6]. Plan steps need not be answerable nodes; least-to-most nodes require contracts, dependencies, answers, and verifiers. Externalising the decomposition is justified only where intermediates need caching, audit, invalidation, authorisation, or failure localisation.

**Against parallel skeleton expansion**: Skeleton-of-Thought generates an answer skeleton and expands its points in parallel to reduce latency [7]. Independent skeleton points are not a least-to-most sequence; that pattern serves presentation, not dependency resolution.

**Against search patterns**: `advanced_task_guides/reasoning/guide_TreeOfThought.md` owns bounded search over competing partial solutions with scoring and backtracking, and is the correct route where the dominant uncertainty is which alternative path to pursue [15]. Graph-of-Thought permits shared descendants, many-parent merges, and revision [16], and is the correct route where results must merge, be reused by several consumers, or be invalidated across a network. Least-to-most may be implemented as a narrow acyclic graph but should remain mostly monotonic and low-branching.

**Against post-hoc verification**: `advanced_task_guides/reasoning/guide_ChainOfVerification.md` owns auditing a frozen draft by decomposing it into claims and testing each independently [14]. That pattern verifies after the answer exists; this one verifies before descendants consume a result. The two combine only at the final assembly of a fact-dense answer.

**Against single-chain reasoning and sampling**: `advanced_task_guides/reasoning/guide_ChainOfThoughtReasoning.md` owns intermediate reasoning within one chain and supplies the baseline this pattern must beat. `advanced_task_guides/reasoning/guide_SelfConsistency.md` owns diversified sampling toward an adjudicated answer, and is preferable where complete attempts are cheap and decomposition is unstable [20].

### 1.3 The Decomposition-Need Gate

Decomposition is not free. Each node costs at least one model call, one context assembly, and one verification pass, and a decomposition that produces subproblems no easier than the original converts one hard question into several hard questions plus bookkeeping. Agents must run the gate after cheaper baselines have executed and before any decomposition prompt is issued.

**Decompose only where all four conditions hold**: a cheaper baseline failed for a named reason recorded as a failure hypothesis; the question admits 2 or more separately answerable subproblems; verified earlier answers materially reduce the difficulty of later ones; and a mostly acyclic dependency order exists over those subproblems. Strong candidates include multi-hop evidence synthesis, layered calculations, modular defect isolation, policy application requiring prerequisite findings, and long compositional transformations whose test depth exceeds demonstration depth.

**Suppress and route elsewhere** for direct retrieval, extraction, summarization, classification, rewriting, and single-function calculations. Route to plain chain-of-thought for a few tightly coupled steps, to self-consistency where complete attempts are cheap and decomposition is unstable, to tree search where the uncertainty is which branch to take, to a merging graph pattern where results have several consumers, to a fixed workflow where the operations are predetermined, and to a direct reasoning-model call where a single response passes verification without needing externalised state.

**Decomposition-Need Gate Decision Table**:

| Observed baseline outcome | Structural condition | Gate verdict |
| :-- | :-- | :-- |
| Deterministic or direct baseline passes verification | Not applicable | Suppress; return the baseline answer |
| Baseline omits a required prerequisite | 2 or more answerable subproblems exist | Decompose |
| Baseline loses track of an intermediate value | Prerequisites materially simplify consumers | Decompose |
| Baseline fails only at longer composition length | Acyclic prerequisite order exists | Decompose |
| Baseline output varies across samples, structure stable | Complete attempts are cheap | Route to self-consistency |
| Several competing solution paths, one must be chosen | Branch evaluation available | Route to tree search |
| One result consumed by several later results | Merge and revision required | Route to a merging graph pattern |
| Operation sequence known before the run | No model-generated plan adds value | Route to a fixed workflow |
| Nearly every candidate subproblem is independent | No hard edges between them | Route to parallel prompting and aggregation |
| No verifier stronger than self-assertion exists | Node would be load-bearing | Suppress; route to human review |

**Numeric gate rules**: Decompose only where at least 1 cheaper baseline has run and failed under the same outcome rubric that will judge the final answer, and where the projected worst-case resource use fits inside every cap in the budget ledger. Where the projected node count is 1, suppress, because a one-node decomposition is a restatement. Where more than 80 percent of candidate nodes carry no hard parent, suppress and route to parallel prompting and aggregation, because the pattern's ordering machinery adds cost without adding control. Where projected cost exceeds 5 times the direct baseline cost, suppress unless a pre-run policy raised the multiplier for the task class.

### 1.4 Execution Tier Partition

The partition below is binding on every phase of Section II. It exists because least-to-most fails in a specific way: a model that generates a decomposition and then solves it will also judge its own ordering, its own completeness, and its own answers, and every one of those judgements is exactly where the pattern breaks.

**Deterministic tier**: Software, scripts, graph algorithms, schema validators, and typed stores own dependency-order validation by cycle detection and topological sort; the ancestor-reference check confirming no node consumes a later node's result; the completeness check against the declared required-item set; the node state store with immutable versions and append-only status events; the ready-frontier computation; answer propagation, which releases a value to consumers only from a committed version; execution of every deterministic rung of the verification ladder; retry and repair counting; atomic budget-ledger reservation and cancellation; cache key construction and invalidation-wave computation; provenance capture; and the release gate. The deterministic tier rejects a decomposition containing a cycle, an orphan reference, a duplicate intent, an unauthorised tool, a node count above the declared cap, or a depth above the declared cap, and it rejects the commit of any node whose hard checks did not all pass.

**Model tier**: LLM calls own generation of candidate decompositions, generation of replacement subgraphs during re-decomposition, solving of each subproblem under an assembled context, and adjudication of residual verification criteria that no deterministic check covers. The model tier is never permitted to decide alone that a decomposition is ordered, that it is complete, that a node's answer is correct, that a budget may be extended, that a tool privilege may be widened, or that a stale cache entry is still valid.

**Hybrid tier**: Three handoffs mix tiers, and each names its authority. Decomposition quality scoring runs deterministic graph checks first and a calibrated judge only over residual criteria such as necessity and downstream utility; where the two disagree, the deterministic verdict is final and a judge score never overrides a graph violation. Node verification runs the deterministic rungs first and an independent model verifier only for criteria left unresolved; where they disagree, deterministic failure is final and a model pass never rescues a failed deterministic check. Final assembly has a model compose the answer from accepted node outputs while a deterministic release gate decides whether it ships; where they disagree, the release gate is final.

***

## II. Operational Framework: Verified Subproblem Chains From Decomposition to Released Answer

The framework assumes the Decomposition-Need Gate has returned decompose. Phases 1 through 3 run once per run. Phase 4 repeats until the terminal node is accepted or a cap is reached. Phase 5 is entered only from a named node failure and returns control to Phase 3 or Phase 4. Phase 6 closes the run.

### Phase 1: Contract Formation and Baseline Displacement

**Objective**: Fix the decision contract and every numeric cap, prove that a cheaper method fails, and record the specific failure the decomposition is intended to repair, so that decomposition is entered as a remedy rather than as a default.

#### Step 1.1: Establish the Decision Contract and Budget Ledger

**Required Actions**:

- Record the objective, output schema, hard constraints, risk tier, evidence policy, tool permissions, acceptance tests, and abstention tests before the first model call.
- Populate the budget ledger with a numeric limit for every bounded resource: subproblems, depth, decomposition candidates, validation repairs, re-decompositions, malformed-output retries, assembly repairs, model calls, tool calls, tokens, currency cost, wall time, retained bytes, and concurrency.
- Apply the conservative default caps where the contract does not override them: 12 subproblems, depth 4, 3 decomposition candidates, 2 validation repairs, 2 re-decompositions, 1 malformed-output retry per node, 2 assembly repairs, 32 model calls, 20 tool calls, 60,000 total tokens, 120 seconds wall time, and cost no greater than 5 times the direct baseline.
- Declare the outcome rubric that will judge the final answer, and confirm it is the same rubric that will judge the baselines.
- Halt and request clarification where a mandatory contract field is absent and no documented conservative default covers it.

**Required Outputs**:

- A decision contract record with objective, output schema, risk tier, evidence policy, and tool permissions.
- A budget ledger in which every named resource carries a numeric limit.
- One declared outcome rubric applying identically to baselines and to the final answer.

**Quality Checkpoints**:

- Every budget dimension carries a numeric limit; an unbounded dimension halts the run before any call is made.
- Acceptance and abstention tests return pass or fail without interpretation.
- The rubric judging the baseline is byte-identical to the rubric judging the final answer; a differing rubric invalidates the comparison.

***

#### Step 1.2: Run Cheaper Baselines and Record the Failure Hypothesis

**Required Actions**:

- Run a deterministic function or direct workhorse-model baseline first, and verify its output under the declared rubric.
- Run a direct reasoning-model or plain chain-of-thought baseline second where the task class warrants it, and verify it under the same rubric.
- Exit the run immediately and return the baseline answer where any cheaper method passes.
- Record a failure hypothesis naming which of three defects the baseline exhibited: an omitted prerequisite, a lost intermediate value, or failure to generalize to a longer composition.
- Pin provider revision, model settings, reasoning effort, and prompt version for every baseline so the later comparison is reproducible.

**Required Outputs**:

- A baseline result record per baseline, with its rubric verdict and its cost, token, and latency figures.
- A failure hypothesis naming the specific defect, or a terminal success record.
- A pinned configuration record covering provider revision, settings, and prompt versions.

**Quality Checkpoints**:

- At least 1 cheaper baseline has run and been verified before any decomposition prompt is issued.
- The failure hypothesis names one of the three declared defects; a hypothesis reading only that the baseline was wrong is rejected.
- No baseline was skipped for expected failure; expectation is not evidence.

***

#### Step 1.3: Issue the Decomposition-Need Verdict

**Required Actions**:

- Evaluate the four decompose conditions in Section 1.3 against the recorded baseline outcome and the task structure.
- Estimate node count, depth, model calls, tool calls, tokens, cost, and critical-path latency for the projected decomposition, and compare each against the budget ledger.
- Return decompose, suppress, or route to a named alternative technique, recording a reason code with the verdict.
- Suppress where the projected node count is 1, where more than 80 percent of projected nodes carry no hard parent, or where projected cost exceeds 5 times the direct baseline without a pre-run policy override.
- Name the alternative explicitly on suppression rather than proceeding unmonitored.

**Required Outputs**:

- A gate verdict record carrying the verdict, the reason code, and the projected resource estimates.
- A named routing target where the verdict is suppress.

**Quality Checkpoints**:

- Every projected resource estimate sits within its ledger limit; an estimate exceeding a cap forces suppression rather than an optimistic start.
- The verdict carries a reason code drawn from the closed vocabulary.
- No suppression verdict leaves the request unrouted.

***

### Phase 2: Decomposition Generation and Quality Gating

**Objective**: Produce a candidate decomposition and admit it only where it is ordered, complete, non-redundant, answerable, and grounded, so that no solving effort is spent against a plan that cannot compose back to the original question.

#### Step 2.1: Generate Bounded Decomposition Candidates

**Required Actions**:

- Supply the decomposer a domain schema, worked exemplars, the declared answer types, the authorised evidence sources, and the node and depth caps, rather than an open request to break the problem down.
- Generate exactly 1 candidate first, and generate up to 2 additional candidates only where the first fails a gate or where ambiguity in the question is material.
- Require each candidate to emit typed nodes and explicit hard dependency declarations, not an unordered prose list.
- Append the original objective as the terminal node of every candidate.
- Prefer a hybrid construction where a reviewed template exists: supply the template as the schema and validate the model's instantiation of it.

**Required Outputs**:

- Between 1 and 3 candidate decompositions, each with typed nodes and declared hard dependencies.
- One terminal node per candidate carrying the original objective verbatim.
- A generation record per candidate naming prompt version, demonstration set version, model revision, seed, and candidate index.

**Quality Checkpoints**:

- Every node declares an answer type and a permitted evidence source; a node declaring neither is malformed.
- The terminal node restates the original objective without narrowing or widening it.
- Candidate count does not exceed 3; a fourth candidate is never generated inside the loop.

***

#### Step 2.2: Run the Ordering and Completeness Checks

**Required Actions**:

- Canonicalize duplicate nodes by normalised contract hash before any structural check runs.
- Run cycle detection and topological sort over the declared hard edges, and reject any candidate whose graph is cyclic.
- Run the ancestor-reference check: confirm every field a node consumes is produced by one of its ancestors, and reject any candidate where a node references a result produced later.
- Run the completeness check: derive the required-item set from the terminal answer schema and the contract, and confirm every required information item and operation is produced by at least one node.
- Score the residual criteria a graph algorithm cannot decide, using a judge calibrated against human labels and deterministic fixtures: necessity, granularity, groundedness, and downstream utility.

**Decomposition-Quality Criteria and Their Owning Tier**:

| Criterion | Test applied | Owning tier |
| :-- | :-- | :-- |
| Dependency correctness | Cycle detection and topological sort over hard edges | Deterministic |
| Ordering | Every consumed field resolves to an ancestor | Deterministic |
| Completeness | Required-item set covered by at least one node | Deterministic |
| Non-redundancy | Canonical contract hash collision and intent overlap | Deterministic |
| Answerability | Declared inputs present and an authorised method exists | Deterministic |
| Size and depth | Node count at or below 12, depth at or below 4 | Deterministic |
| Authorisation | Every named tool inside the permitted set | Deterministic |
| Necessity | Removing the node changes solvability | Hybrid |
| Granularity | Node verifiable in one pass and larger than bookkeeping cost | Hybrid |
| Groundedness | Evidence or authorised tools can support the node | Hybrid |
| Downstream utility | The answer reduces uncertainty for a named consumer | Hybrid |

**Required Outputs**:

- A structural verdict per candidate covering ordering, acyclicity, completeness, redundancy, size, and authorisation.
- A residual score set per candidate covering necessity, granularity, groundedness, and downstream utility.
- A canonical graph hash per candidate.

**Quality Checkpoints**:

- No candidate passes with an unresolved ancestor reference; ordering is a hard criterion and is never traded against a high judge score.
- The required-item set is derived from the contract, not from the candidate itself; deriving it from the candidate makes the completeness check vacuous.
- Every judge score carries the rubric version and calibration record under which it was produced.

***

#### Step 2.3: Repair Under Bound, or Reject and Route

**Required Actions**:

- Return only named defects to the decomposer where failures are local, and request a repaired graph rather than a new one.
- Permit at most 2 repairs per candidate, and never reset the repair counter inside the loop.
- Reject the candidate outright where a hard criterion fails after the repair bound, rather than lowering the rubric or hand-editing the graph to make it pass.
- Accept and exit the loop where every hard criterion passes and projected worst-case use remains inside every ledger cap.
- Route to manual decomposition, plain chain-of-thought, tree search, a merging graph pattern, a fixed workflow, or abstention where no candidate passes.

**Required Outputs**:

- One accepted decomposition with its canonical graph hash and its full gate record, or a routing decision naming the alternative.
- A rejection record per failed candidate naming the failing criterion and the repair count consumed.

**Quality Checkpoints**:

- No accepted decomposition carries a waived hard criterion; a waiver is a defect, not a decision.
- Repair counts and candidate counts are never reset within the phase.
- The accepted decomposition is immutable from acceptance onward and is superseded only through Phase 5.

***

### Phase 3: Dependency Structure and Execution Scheduling

**Objective**: Convert the accepted decomposition into an executable typed graph, derive the execution order and the parallelism it permits, and materialise immutable state and root evidence before the first node is solved.

#### Step 3.1: Derive the Typed Dependency Graph

**Required Actions**:

- Classify every declared edge as hard where the consumer cannot produce a typed answer without the producer's accepted value, and as soft where the producer's answer only improves the consumer's context.
- Record on each hard edge the specific prerequisite fields the consumer consumes, so that invalidation can be scoped to the fields that actually changed.
- Discard declared edges that no consumer field references, because an unreferenced edge serialises work without cause.
- Re-run cycle detection over the hard-edge set after classification, since classification can expose a cycle the declared set concealed.
- Compute and store the topological order, the depth of every node, and the transitive ancestor set of the terminal node.

**Required Outputs**:

- A typed edge set in which every edge carries a hard or soft classification and its consumed field list.
- A stored topological order with per-node depth and topological position.
- A transitive required-ancestor set for the terminal node.

**Quality Checkpoints**:

- The hard-edge graph is acyclic; a cycle detected here halts the run and routes to Phase 5 classification rather than being broken by choosing an answer arbitrarily.
- Every hard edge names at least 1 consumed field; an edge naming none is downgraded to soft.
- Maximum depth does not exceed the declared cap of 4 unless a pre-run policy raised it.

***

#### Step 3.2: Compute the Ready Frontier and the Parallelism Plan

**Required Actions**:

- Compute the ready frontier as every unsolved node whose hard parents all hold accepted answers, and recompute it after every commit rather than assuming the list order.
- Schedule all ready nodes concurrently up to the declared concurrency cap; sequencing exists to respect prerequisites, not to respect the order in which the decomposer happened to list nodes.
- Reserve budget atomically at dispatch so that concurrent nodes cannot collectively exceed a ledger limit.
- Compute the critical path over hard edges and record it, so that serialised independent work appears later as avoidable latency rather than as unexplained slowness.
- Issue a lease and an idempotency key per dispatched node so a retried dispatch cannot double-commit.

**Required Outputs**:

- A ready frontier recomputed after every state change.
- A parallelism plan naming the concurrency cap, the scheduled node set, and the computed critical path.
- One lease and one idempotency key per dispatched node.

**Quality Checkpoints**:

- No node with an unaccepted hard parent appears in the frontier; frontier membership is computed, never asserted by a model.
- Independent ready nodes are dispatched together up to the cap; serialising them is a scheduling defect and is recorded as one.
- Budget reservation precedes dispatch; a node dispatched against unreserved budget is cancelled.

***

#### Step 3.3: Initialise Immutable State and Retrieve Root Evidence

**Required Actions**:

- Create immutable records for the accepted decomposition, every node, every edge, every prompt version, and the budget ledger, with append-only status events thereafter.
- Retrieve evidence for root nodes, label every external string as untrusted data rather than instruction, and attach source provenance covering query, corpus and index version, filters, document and chunk identifiers, rank, score, location, timestamp, content hash, and access decision.
- Revise retrieval queries until coverage passes, the retrieval cap is reached, or 2 consecutive rounds add no unique relevant evidence.
- Construct cache keys from the normalised node contract, canonical parent-result hashes, evidence and index versions, prompt and model versions, inference parameters, tool and policy versions, authorisation scope, and output schema.
- Narrow the objective or abstain where evidence coverage fails for a node the terminal answer requires.

**Required Outputs**:

- An immutable run state holding decomposition, nodes, edges, prompt versions, and ledger.
- A provenance-preserving evidence set attached to root nodes, with every external string marked untrusted.
- A cache key per node built from the full version tuple.

**Quality Checkpoints**:

- No cache key is derived from question text alone; a text-only key permits reuse across incompatible evidence, prompt, model, and authorisation versions and is rejected.
- Every retrieved passage carries provenance sufficient to reopen it; a passage without a resolvable location is not admitted as evidence.
- Retrieval stops at the declared cap or after 2 non-productive rounds; unbounded retrieval is a budget defect.

***

### Phase 4: Bounded Solving With Per-Subproblem Verification

**Objective**: Answer each ready node under a minimal dependency-specific context and prove the answer correct before any descendant can see it, so that a wrong intermediate is caught at its origin rather than inherited by everything downstream.

#### Step 4.1: Assemble Minimal Context and Solve One Ready Node

**Required Actions**:

- Assemble the node's context from the decision contract, the node contract, the accepted answers of its transitive required hard ancestors, the declared assumptions, the evidence references, the tool policy, the output schema, and the local token allocation.
- Carry identifiers, normalised values, units, and provenance rather than prose restatements, and reference large artifacts by location and content hash.
- Exclude unrelated siblings, discarded candidate plans, judge rationales, and duplicated evidence text; the accumulated transcript is never passed wholesale to every node.
- Keep the current question and the binding constraints at the boundaries of the assembled context rather than buried inside it, because information placed in the middle of a long context is used least reliably [21].
- Solve with the configured solving-stage prompt, parse the typed result against the declared schema, and retry malformed output at most 1 time before suspending the node.
- Record a context manifest naming every included field and every omission or compression applied.

**Required Outputs**:

- One assembled context per dispatched node, with a recorded context manifest.
- One typed candidate answer per node, parsed against the declared schema, with its units and assumptions.
- A solver call record naming prompt version, model revision, sampling parameters, seed, token counts, and cost.

**Quality Checkpoints**:

- The assembled context contains no unaccepted ancestor value; an unverified draft in context is a propagation defect regardless of the outcome.
- Malformed output is retried at most 1 time; a second malformed parse suspends the node and enters Phase 5.
- Every omission from the context is recorded; silent truncation makes a later failure unattributable.

***

#### Step 4.2: Run the Verification Ladder Before Commit

**Required Actions**:

- Run the deterministic rungs first and in this order: schema, type, unit, range, identity, access, and invariant checks against the node contract.
- Run the evidence and execution rungs next: authorised retrieval with citation resolution, sandboxed computation, compilers, calculators, test suites, or simulators, according to the node type.
- Run an independent model verifier last and only for criteria the earlier rungs left unresolved, and record its source class so its agreement with the solver is never counted as independent confirmation.
- Apply the verification standard for the node's declared type rather than one generic standard: a retrieved-fact node requires a resolvable citation in an admitted source; a computed-quantity node requires reproduction by a deterministic runtime with matching units; an entity-resolution node requires an identity check against an authoritative record; a lemma or intermediate-claim node requires either a deterministic proof step or two source-class-distinct supporting signals; a code or patch node requires a passing executable test; a policy-application node requires the cited clause to resolve and its conditions to be individually satisfied.
- Sample 3 alternative answers for a single node only where the node is measurably unstable or the verifier returned an unresolved verdict, and never sample across both the decomposition axis and the answer axis in the same run.

**Node Type Verification Standards**:

| Node type | Hard verification standard | Escalation on failure |
| :-- | :-- | :-- |
| Retrieved fact | Citation resolves in an admitted source and the span supports the value | Re-retrieve once, then suspend |
| Computed quantity | Deterministic runtime reproduces the value with matching units | Re-run in sandbox once, then suspend |
| Entity resolution | Identity match against an authoritative record | Suspend; identity is never inferred |
| Intermediate claim | Deterministic proof step, or 2 signals of distinct source class | Suspend and enter re-decomposition |
| Code or patch | Executable test passes in an ephemeral sandbox | Suspend after 1 retry |
| Policy application | Cited clause resolves and every condition is individually satisfied | Suspend and route to human review |
| Aggregation or summary | Every aggregated input is an accepted version and totals reconcile | Suspend; recompute from accepted versions |

**Required Outputs**:

- A verification record per node naming each rung run, its verdict, its source class, its cost, and any defect code.
- A pass or fail decision per hard criterion, with unresolved criteria named explicitly rather than defaulted to pass.
- An individual judgement record per verifier, retained rather than reduced to an average.

**Quality Checkpoints**:

- A deterministic failure is final; no model verifier, judge score, or learned process score overrides it, since such scores address residual qualities and remain learned proxies [19].
- Every externally checkable node was checked by a signal stronger than self-assertion; a node without one is not committed and is routed to human review or made non-load-bearing.
- Agreement between the solver and a verifier sharing its generator, prompt, or premise is recorded as correlated and does not satisfy a hard criterion [20].

***

#### Step 4.3: Commit and Propagate, or Suspend

**Required Actions**:

- Commit the node only where every hard check passed, writing an immutable accepted version and a status event in one operation.
- Release the node's dependents only after commit, and propagate the accepted version and its compact contract, never the working draft or the verifier's rationale.
- Cache the accepted result under its full version-tuple key and checkpoint the trace.
- Mark an optional node skipped only with a recorded necessity decision and the deciding evidence; never solve a node for plan conformity and never invent an answer to preserve the listed sequence.
- Suspend the node and enter Phase 5 where it fails semantically, is impossible with the available evidence, exposes a missing prerequisite, or contradicts a verified ancestor; follow the platform retry policy without resetting run counters where the failure is a transient service fault.
- Terminate the phase when the terminal node is accepted, when the frontier is empty, or when any token, cost, latency, model-call, tool-call, subproblem, depth, or safety cap is reached.

**Required Outputs**:

- An accepted immutable version per committed node, with its cache entry and status event.
- A suspension record per failed node naming the failure class and the evidence for it.
- A phase exit record naming the terminating condition and, on resource exhaustion, the exact limiting cap.

**Quality Checkpoints**:

- No descendant consumed a value that was not an accepted version at the moment of consumption.
- An empty frontier with unresolved nodes is treated as a dependency defect and routed to Phase 5, never as completion.
- A safety failure stops the run immediately and is never traded against remaining budget.

***

### Phase 5: Failure Classification, Invalidation, and Bounded Re-Decomposition

**Objective**: Locate the true origin of a failure, replace only the affected subgraph, and invalidate everything that consumed the reversed result, so that repair is scoped and bounded rather than becoming a second unplanned run.

#### Step 5.1: Classify the Failure and Freeze Valid Ancestors

**Required Actions**:

- Enter only on a named trigger: a failed node, an impossible node, a missing prerequisite, a verified contradiction, a dependency deadlock, or a repeated no-progress result.
- Classify the failure into exactly one of five classes: bad decomposition, bad evidence, bad solver, bad tool, or unsatisfiable objective.
- Freeze every ancestor whose accepted version the failure does not implicate, and record the frozen version set so the replacement cannot silently re-derive settled values.
- Trace the terminal lineage backward to the earliest incorrect or invalid accepted answer, and record that node as the first bad ancestor with the count of descendants that consumed it.
- Record the localization distance as the number of executed nodes between the first bad ancestor and the point of detection.

**Required Outputs**:

- A failure classification record naming the trigger node, the trigger type, and one of the five failure classes.
- A frozen ancestor version set.
- A first-bad-ancestor record with error amplification and localization distance.

**Quality Checkpoints**:

- The failure carries exactly 1 classification; an unclassified failure is never handed to the decomposer, because a request for a better plan produces an unbounded rewrite.
- The frozen set contains every ancestor the failure does not implicate; freezing too little converts a local repair into a full re-run.
- Localization distance is recorded for every failure, since a rising distance indicates verification is placed too far downstream.

***

#### Step 5.2: Request and Gate a Replacement Subgraph

**Required Actions**:

- Request a replacement subgraph covering the failed node and its descendants only, supplying the failure classification, the frozen ancestor set, and the accepted values those ancestors hold.
- Require the replacement to identify explicitly which nodes are added, removed, split, merged, reordered, and made optional relative to the superseded subgraph.
- Validate the replacement with the same ordering, completeness, non-redundancy, answerability, size, and authorisation checks that gated the original decomposition, and with the same repair bound of 2.
- Refuse any replacement that widens a budget, widens a tool privilege, or alters the decision contract; the controller replaces structure, not policy.
- Reject a replacement whose node set overlaps a frozen ancestor's intent without evidence that the ancestor is invalid.

**Required Outputs**:

- One replacement subgraph with an explicit add, remove, split, merge, reorder, and optionality diff.
- A gate record for the replacement covering every hard criterion.
- A new canonical graph hash for the amended run graph.

**Quality Checkpoints**:

- The replacement passes every hard criterion that gated the original decomposition; a lower bar for repairs reintroduces the defect the gate exists to catch.
- No replacement widened a budget, a tool privilege, or the contract.
- The diff is explicit; a replacement presented as a whole new plan is rejected because its effect on frozen ancestors cannot be audited.

***

#### Step 5.3: Propagate Invalidation and Resume or Exit

**Required Actions**:

- Compute the invalidation wave by transitive hard-edge traversal from the changed node, and mark every affected descendant stale with its invalidation cause and wave identifier.
- Evict every cache entry whose key includes a changed parent-result hash, a changed evidence version, or a changed prompt or model version.
- Cancel pending work on invalidated nodes and release their leases and reserved budget.
- Return to evidence retrieval where the replacement introduced new root nodes, or to solving where a ready node already exists.
- Exit the loop when the replacement passes and exposes a ready node, when the objective is proven unsatisfiable, or when the run-wide cap of 2 re-decompositions is reached; never reset a token, cost, time, depth, or call counter on entry or exit.
- Route to human review, a search pattern, a labelled partial answer, or abstention on cap, according to the contract.

**Required Outputs**:

- An invalidation record naming the wave, the affected descendants, the cause, and the evicted cache entries.
- A resumption target naming the phase control returns to, or a terminal routing decision.
- An updated budget ledger reflecting cancelled reservations and consumed repair counts.

**Quality Checkpoints**:

- No cached descendant survives an upstream version change; a surviving entry is a silent propagation channel.
- Counters are never reset across a re-decomposition; a reset converts a bounded repair into an unbounded one.
- History is appended, never edited in place; a superseded version remains readable for attribution.

***

### Phase 6: Composition, Release, and Measurement

**Objective**: Reassemble the terminal answer from accepted versions, release it only through an external gate, and compute the propagation and decomposition measurements that determine whether the pattern earned its cost.

#### Step 6.1: Compose the Terminal Answer From Accepted Versions

**Required Actions**:

- Enter only when every mandatory terminal dependency holds a current accepted version; a stale ancestor blocks composition.
- Assemble the answer from accepted node outputs, preserving units, scope qualifications, exceptions, residual uncertainty, and evidence lineage.
- Re-derive nothing from raw prose that an accepted node already settled; re-derivation reintroduces the error the node's verification eliminated.
- Confirm that composition actually answers the original objective as recorded in the terminal node, not a narrowed or widened variant of it.
- Produce a verified structured summary linked to the full artifact where the answer is long, and check mandatory claims, exceptions, units, and citations against that summary.

**Required Outputs**:

- One composed terminal answer carrying units, scope, exceptions, uncertainty, and evidence lineage.
- A composition manifest mapping every element of the answer to the accepted node versions that produced it.
- A structured summary linked to the full artifact where the answer exceeds the declared length threshold.

**Quality Checkpoints**:

- Every element of the answer resolves to an accepted node version in the composition manifest; an unmapped element is an unattributed assertion.
- No settled value was re-derived during composition.
- The composed answer addresses the terminal node's objective verbatim; a drifted objective fails composition.

***

#### Step 6.2: Run the Release Gate and Bounded Assembly Repair

**Required Actions**:

- Run the release gate in deterministic order: output schema and policy checks, deterministic outcome checks under the declared rubric, citation opening and claim-to-evidence validation, contradiction checks across accepted answers, and privacy review.
- Repair only the named local defect where the gate reports one, and re-run the full gate afterward rather than only the failing check.
- Return to Phase 5 and invalidate descendants where the gate exposes a bad ancestor rather than a local assembly defect.
- Permit at most 2 assembly repairs and count each against the global budget ledger.
- Exit successfully only where every release criterion passes; exit unsuccessfully on an unresolved critical claim, a stale ancestor, a safety violation, or an exhausted cap, returning a clearly labelled verified partial result or a declared abstention.
- Return the answer, the material evidence, the residual uncertainty, and a concise statement of the checks performed, withholding private chain-of-thought, unrestricted subproblem drafts, credentials, hidden security policy, and any injected instruction text.

**Required Outputs**:

- A release gate record with a verdict per criterion.
- A released answer, a labelled verified partial result, or a declared abstention with its reason code.
- A disclosure-compliant response payload naming the checks performed.

**Quality Checkpoints**:

- The release gate is deterministic and holds final authority; a model assertion that the answer is complete never substitutes for it.
- Assembly repairs do not exceed 2 and are counted against the global ledger; a third defect terminates the run as a partial result.
- No response element breaches the disclosure boundary.

***

#### Step 6.3: Compute Propagation and Decomposition Measurements

**Required Actions**:

- Compute end-to-end verified accuracy as eligible runs whose terminal output passes the independent outcome rubric divided by eligible runs, stratified by task family, composition length, dependency depth, model, prompt version, budget, and seed.
- Compute per-node accuracy and conditional accuracy by depth, defined as correct nodes among those whose hard parents were correct, then multiply the empirical conditional accuracies along each required depth to obtain an expected all-correct rate and compare it against the observed rate.
- Attribute every failed run to its earliest incorrect accepted ancestor on the terminal lineage, and report error amplification as invalid descendants per first bad ancestor and localization distance as executed nodes between first error and detection.
- Separate the failure taxonomy into decomposition miss, dependency error, evidence miss, solver error, verifier false accept, context omission, tool error, assembly error, and budget exhaustion.
- Measure downstream utility by ablation: remove or mask one node from a replay while respecting dependency semantics, and record the change in terminal verification, reporting necessary-node share, average marginal gain, and any case where removing a node improved accuracy or cost.
- Compute parallel efficiency from total worker time, wall time, concurrency, fan-in wait, and cancelled work, so that independent nodes that were serialised appear as avoidable critical-path delay.
- Compare against the direct, plain chain-of-thought, direct reasoning-model, self-consistency, and fixed-workflow baselines on paired examples at matched cost and latency.

**Compounding Illustration**: Under independent conditional accuracy, all-step accuracy is the product of step accuracies, so 10 nodes at 95 percent yield roughly 60 percent probability that every node is correct. Real errors correlate, because one wrong premise poisons its descendants, so the product is a diagnostic that bounds expectations, not a forecast of observed performance.

**Required Outputs**:

- A quality record covering end-to-end verified accuracy, per-node accuracy, and conditional accuracy by depth.
- A propagation record covering first bad ancestor, error amplification, localization distance, and the failure taxonomy counts.
- A decomposition-quality record covering coverage, node precision, non-redundancy, answerability, groundedness, dependency precision and recall, and graph edit distance across seeds.
- An efficiency record covering tokens, cost, calls, end-to-end and critical-path latency, verification share, wasted work, and parallel efficiency, reported at median, p90, p95, and p99.

**Quality Checkpoints**:

- Every failed run carries a first-bad-ancestor attribution; an unattributed failure cannot distinguish a decomposition defect from a solver defect.
- Decomposition quality is scored separately from final accuracy, because final-answer accuracy alone conceals poor subquestions [17].
- A decomposition with high judge scores and no positive measured downstream utility is not promoted.

***

## III. Implementation Guidance for AI Agents

AI agents executing least-to-most reasoning must follow systematic protocols ensuring that no unverified answer becomes load-bearing, that decomposition structure is validated by software rather than asserted by a model, and that every repair is bounded and counted. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract and Gate Agent**: Owns the decision contract, the budget ledger, the baseline runs, and the Decomposition-Need Gate verdict. It alone may amend a cap, and every amendment is versioned and recorded before the run resumes.
2. **Decomposer Agent**: Model tier. Generates candidate decompositions and replacement subgraphs under a supplied schema, exemplar set, and cap list. It never scores its own output and never dispatches work.
3. **Decomposition Evaluator**: Hybrid tier with deterministic authority. Runs cycle detection, topological sort, the ancestor-reference check, the completeness check, canonicalisation, and authorisation checks, then invokes a calibrated judge for residual criteria only. It returns accept, repair with named defects, or reject.
4. **Dependency Scheduler**: Deterministic tier. Owns the typed edge set, the topological order, the ready frontier, the concurrency cap, leases, idempotency keys, atomic budget reservation, cancellation, and the critical-path computation. No model influences frontier membership.
5. **Node Solver**: Model tier. Answers exactly one node under the assembled context. It may not extend a horizon, admit an unvalidated tool result, change its own node contract, or read an unaccepted ancestor value.
6. **Node Verifier**: Hybrid tier with deterministic authority. Runs the verification ladder in order, records source classes and individual judgements, and holds sole commit authority. It never solves the node it verifies.
7. **Re-Decomposition Controller**: Classifies failures, freezes ancestors, requests scoped replacements, and computes invalidation waves. It may replace structure but may never widen a budget, a tool privilege, or the contract.

**Instrumentation Obligations**: Every component writes to one append-only trace per run, with one span per routing decision, decomposition attempt, graph validation, solver call, verifier call, retrieval, tool call, cache decision, re-decomposition, assembly, and release. Spans carry run identity, node identity and version, prompt and model versions, token and cost figures, verdicts, reason codes, and content hashes. High-cardinality or sensitive payloads are stored in protected storage and referenced by location and hash rather than written into span attributes. Instrumentation follows a pinned and logged telemetry convention version [29], and source artifacts, transformations, and actors are represented as entities, activities, and agents for interoperable provenance [28].

**Disclosure Boundary**: Credentials, raw authentication material, unrestricted personal data, and private chain-of-thought are never logged by default. Intermediate results can reveal user secrets, inferred sensitive attributes, proprietary documents, and security policy, so capture is allowlisted, exports are redacted before release, storage is encrypted per tenant, access is role-based, raw drafts carry short retention, and deletion propagates through cache, trace, object store, and backup layers [31].

**Workflow Execution Pattern**:

```
STATE: Node_Commit_Decision
INPUTS:
  1. Typed candidate answer from Step 4.1
  2. Verification record with per-rung verdicts and source classes
  3. Node contract with declared type and hard criteria
  4. Budget ledger with reservations for this node
ACTIONS:
  1. Confirm every hard criterion returned an explicit pass
  2. Confirm at least one signal of a source class distinct from the solver
  3. Write the immutable accepted version and its status event atomically
  4. Recompute the ready frontier and release dependents
  5. Write the cache entry under the full version-tuple key
VALIDATION:
  - hard_criteria_unresolved_count == 0
  - deterministic_rung_failures == 0
  - distinct_source_class_signal_present == TRUE
  - consumed_ancestor_versions_all_accepted == TRUE
  - cache_key_includes_parent_hashes AND evidence_version AND model_version
TRANSITIONS:
  IF all_validations_pass THEN next_state = Schedule_Ready_Frontier
  IF deterministic_rung_failures > 0 THEN next_state = Node_Suspension
  IF unresolved_criteria > 0 AND retries_remaining > 0
     THEN next_state = Node_Retry_Bounded
  IF unresolved_criteria > 0 AND retries_remaining == 0
     THEN next_state = Failure_Classification
  IF safety_violation THEN next_state = Immediate_Stop
```

**Two-Phase Action Pattern**: Emit the intended commit with its verification record and its dependent-release list without executing it; confirm it against the validation block while no dependent has been released; execute the commit and the release in one atomic operation only after validation passes. The same pattern governs decomposition acceptance and replacement-subgraph acceptance.

**Approval Gate**: Human authorisation is required before releasing an answer in the highest risk tier, before committing any node whose only passing signal shares a source class with its solver, before any consequential tool action, and before any single node projected to consume more than 40 percent of the remaining token or currency budget. Authorisation and human confirmation sit outside the reasoning pipeline: a verified informational answer never grants permission for a consequential action, and tool output never authorises an action.

**Context Management Requirements**:

- Hold the contract, graph, accepted versions, and budget ledger in durable state, since a run may outlive one context window.
- Assemble each node's context from the transitive required ancestor set rather than from the accumulated transcript, and record every omission and compression in a context manifest.
- Keep instructions separate from data, label every external string with its trust class and provenance, and constrain tool arguments through typed schemas, because injection can enter through the user, retrieved text, tool observations, cached answers, or a compromised node that later appears in a descendant's context [30].
- Write a handoff record naming accepted versions, the frontier, remaining budget, and consumed counters at every context boundary.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract and Baseline Integrity (After Phase 1)**

- **Automated Check**: Every budget dimension carries a numeric limit; at least 1 cheaper baseline ran and was verified under the declared rubric; the failure hypothesis names one of the three declared defects.
- **Agent Action on Pass**: Proceed to decomposition generation.
- **Agent Action on Failure**: Halt and return the contract or baseline defect; no decomposition prompt is issued against an incomplete contract.
- **Human Review Trigger**: A task in the highest risk tier, an acceptance test not statable in machine-evaluable terms, or more than 2 contract fields filled by conservative default.

**Checkpoint 2: Decomposition Admission (After Phase 2)**

- **Automated Check**: Hard-edge graph is acyclic; every consumed field resolves to an ancestor; the required-item set is fully covered; node count is at or below 12 and depth at or below 4; every named tool is authorised; repair count is at or below 2 and candidate count at or below 3.
- **Agent Action on Pass**: Proceed to dependency derivation.
- **Agent Action on Failure**: Reject the candidate and route to the named alternative technique; a hard criterion is never waived to admit a candidate.
- **Human Review Trigger**: All 3 candidates rejected, or a judge score contradicting a deterministic verdict.

**Checkpoint 3: Schedule Validity (After Phase 3)**

- **Automated Check**: Every hard edge names at least 1 consumed field; the frontier contains no node with an unaccepted hard parent; budget is reserved before dispatch; every cache key carries parent-result, evidence, prompt, model, policy, and authorisation versions.
- **Agent Action on Pass**: Proceed to solving.
- **Agent Action on Failure**: Halt dispatch and rebuild the schedule; a defective schedule is never executed with a warning attached.
- **Human Review Trigger**: A cycle exposed by edge classification that the declared edge set concealed, or more than 30 percent of declared hard edges downgraded to soft during classification.

**Checkpoint 4: Commit Validity (After Each Node in Phase 4)**

- **Automated Check**: Zero unresolved hard criteria; zero deterministic rung failures; at least 1 signal of a source class distinct from the solver; every consumed ancestor value was an accepted version; malformed-output retries at or below 1.
- **Agent Action on Pass**: Commit, cache, and release dependents.
- **Agent Action on Failure**: Suspend the node and enter failure classification; an unverified answer is never released to a descendant under any circumstance.
- **Human Review Trigger**: Verifier false-accept rate above 5 percent in the task class, or a node whose only passing signal shares its solver's source class.

**Checkpoint 5: Repair Boundedness (After Phase 5)**

- **Automated Check**: Failure carries exactly 1 classification; the replacement passes every gate that admitted the original decomposition; no counter was reset; the invalidation wave evicted every cache entry keyed on a changed parent hash.
- **Agent Action on Pass**: Resume at the named phase.
- **Agent Action on Failure**: Terminate the loop and route to human review, a search pattern, a labelled partial result, or abstention.
- **Human Review Trigger**: The re-decomposition cap of 2 reached, or the same node failing across 2 consecutive replacements.

**Checkpoint 6: Release Integrity (After Phase 6)**

- **Automated Check**: Every answer element maps to an accepted node version; every citation opens and supports its claim; zero stale ancestors; assembly repairs at or below 2; zero disclosure-boundary breaches.
- **Agent Action on Pass**: Release the answer and close the run.
- **Agent Action on Failure**: Downgrade to a labelled verified partial result or a declared abstention and report the uncovered criteria.
- **Human Review Trigger**: Any safety violation, any privacy finding, more than 5 percent of citations failing to open, or a composition manifest carrying 1 or more unmapped elements.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
OWNING_TIER:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Degenerate Decomposition**

- **Symptoms**: A single node restating the original question; many trivial token-level fragments; nodes whose answers no consumer references; verification cost per node exceeding solving cost.
- **Diagnostic Steps**: Compare node count and depth against the caps, compute the share of nodes with no hard parent and no hard child, and compare projected total cost against the direct baseline.
- **Resolution Protocol**: Option A, regenerate with an explicit granularity instruction naming one fact set, one quantity, one lemma, one testable patch, or one policy clause as the unit. Option B, merge trivial siblings into one node and re-run the gate. Option C, suppress the pattern and return to the baseline, since a decomposition producing no useful intermediate contract has no reason to exist.
- **Escalation Trigger**: Three rejected candidates, or a projected cost above 5 times the direct baseline, terminates the pattern and routes to the named alternative.

**Error Type 2: Silent Error Propagation From a False Accept**

- **Symptoms**: A fluent, internally consistent final answer that fails the external rubric; several descendants agreeing on a value traceable to one unverified ancestor; a late verifier reversing a value many nodes after it was committed.
- **Diagnostic Steps**: Trace the terminal lineage backward to the earliest incorrect accepted answer, count its consuming descendants, and compute localization distance; check whether that node's only passing signal shared a source class with its solver.
- **Resolution Protocol**: Option A, strengthen the node type's verification standard by adding a deterministic rung ahead of the model verifier. Option B, move verification upstream by splitting the node so the fallible step is checked in isolation. Option C, mark the node non-load-bearing and route its criterion to human review where no signal stronger than self-assertion exists.
- **Escalation Trigger**: A verifier false-accept rate above 5 percent in any task class suspends autonomous release in that class; this error is never resolved by re-running the same solver, because a fluent wrong answer reproduces reliably.

**Error Type 3: Circular or Deadlocked Dependency Structure**

- **Symptoms**: Cycle detection failing after edge classification; an empty ready frontier with unresolved nodes; two nodes each declaring the other as a prerequisite.
- **Diagnostic Steps**: Determine whether the cycle is a genuine mutual constraint or a prerequisite mistakenly declared in both directions, and inspect which consumed fields each direction names.
- **Resolution Protocol**: Option A, reformulate the coupled pair as one joint node whose answer resolves both values together. Option B, introduce a solver for the coupled system where the coupling is numeric or constraint-shaped. Option C, route to a merging graph pattern where results genuinely have several consumers and require revision.
- **Escalation Trigger**: A cycle surviving 1 reformulation attempt terminates the run; a cycle is never broken by choosing one side's answer arbitrarily, because that fabricates a prerequisite.

**Error Type 4: Re-Decomposition Thrashing**

- **Symptoms**: The same nodes repeatedly split and merged across attempts; dependency edges reversed between attempts; each replacement failing at the same node; graph edit distance across attempts rising without accuracy improvement.
- **Diagnostic Steps**: Compare successive graph hashes and diffs, and confirm whether each replacement addressed the recorded failure classification or restated the plan.
- **Resolution Protocol**: Option A, re-classify the failure, since repeated structural churn usually indicates a bad-evidence or bad-tool failure misclassified as bad decomposition. Option B, freeze the disputed subgraph and route only its criterion to a deterministic method or a human. Option C, abandon the pattern and return the best verified partial result with the unresolved node named.
- **Escalation Trigger**: The run-wide cap of 2 re-decompositions, or repair precision below 50 percent across the last 10 runs in the task class, halts re-decomposition for that class pending policy review.

**Error Type 5: Serialised Independent Work and Budget Blow-Up**

- **Symptoms**: Wall time approaching total worker time; a critical path containing nodes with no consumed-field relationship; token consumption rising through repeated context rather than through new evidence; nested sampling across both the decomposition and answer axes.
- **Diagnostic Steps**: Recompute parallel efficiency from worker time, wall time, concurrency, fan-in wait, and cancelled work, then inspect the hard-edge justification for every consecutive pair on the critical path.
- **Resolution Protocol**: Option A, downgrade unjustified hard edges to soft and re-dispatch the widened frontier. Option B, reduce each node's context to its transitive required ancestor set and re-measure token consumption. Option C, disable sampling on all but the single measurably unstable node.
- **Escalation Trigger**: Parallel efficiency below 50 percent where more than 2 frontier-eligible nodes existed, or token consumption above 80 percent of the ledger before the terminal node is reachable, halts dispatch for re-planning.

**Error Type 6: Context Contamination and Instruction Injection**

- **Symptoms**: A node's answer restating instructions found in retrieved text; a tool argument outside the declared schema; a cached answer carrying directive language; a descendant behaving differently after an unrelated ancestor changed.
- **Diagnostic Steps**: Inspect the context manifest for the affected node, check the trust label and provenance of every included external string, and confirm whether the directive text entered through user input, retrieval, a tool observation, or a cached ancestor answer.
- **Resolution Protocol**: Option A, quarantine the contaminated evidence identifier, invalidate every node that consumed it, and re-retrieve under a narrowed filter. Option B, re-run the node with instruction and data separated into distinct context regions and external strings sanitised. Option C, remove the affected source from the permitted evidence set for the run and record the exclusion.
- **Escalation Trigger**: Any contaminated value that reached a committed node halts release and triggers a full invalidation wave; authorisation is never granted on the basis of node content, and this class is never resolved by re-prompting alone.

**Troubleshooting Decision Tree**:

```
RUN FAILS OR A NODE IS SUSPENDED
├─ DECOMPOSITION DEFECT
│   ├─ One node restating the objective → Suppress; return the baseline
│   ├─ Consumed field with no ancestor → REJECT candidate; never repair by hand
│   ├─ Required item uncovered → Return named defect; at most 2 repairs
│   └─ Cycle after edge classification → Reformulate as a joint node or route to a merging pattern
├─ PROPAGATION DEFECT
│   ├─ Unverified value found in a descendant context → HALT; invalidate the wave
│   ├─ Late reversal of a committed value → Recompute from the changed node; evict caches
│   ├─ Only passing signal shares the solver's source class → Block commit; escalate
│   └─ Stale cache entry served → HALT release; rebuild the key with full version tuple
├─ SCHEDULING DEFECT
│   ├─ Empty frontier with unresolved nodes → Enter failure classification
│   ├─ Independent nodes executed serially → Downgrade unjustified hard edges
│   └─ Dispatch without reserved budget → Cancel the node; re-reserve atomically
├─ REPAIR DEFECT
│   ├─ Replacement widens budget or privilege → REJECT; controller may not amend policy
│   ├─ Counter reset across re-decomposition → HALT; restore counters and re-evaluate
│   └─ Cap of 2 re-decompositions reached → Return partial result or abstain
└─ SAFETY OR DISCLOSURE DEFECT
    ├─ Injected instruction in a committed node → HALT; quarantine and invalidate
    ├─ Node content used to authorise an action → HALT; authorisation sits outside the pipeline
    └─ Private draft or credential in the trace → HALT release; purge and re-instrument
```

### D. Performance Metrics and Continuous Learning

**Outcome and Propagation Metrics**:

- **End-to-end verified accuracy**: Eligible runs whose terminal output passes the independent outcome rubric (target: above the best cheaper baseline at matched cost and latency; parity blocks promotion).
- **Conditional accuracy by depth**: Correct nodes among those whose hard parents were correct (target: at least 90 percent at every depth; below 90 percent at depth 3 or beyond indicates verification is too weak to sustain the chain).
- **Verifier false-accept rate**: Committed nodes later shown incorrect, divided by committed nodes (target: no more than 5 percent; above 5 percent suspends autonomous release in the class).
- **Verifier false-reject rate**: Correct nodes suspended by a verifier, divided by correct nodes (target: no more than 10 percent; above 10 percent inflates re-decomposition cost).
- **Error amplification**: Invalid descendants per first bad ancestor (target: no more than 1.5; a higher figure means verification sits too far downstream).
- **Localization distance**: Executed nodes between the first error and its detection (target: no more than 1; a distance of 0 means the error was caught at its own node).

**Decomposition-Quality Metrics**:

- **Coverage**: Required reference items represented by at least 1 valid node, divided by required reference items (target: 100 percent for mandatory items).
- **Node precision**: Necessary valid nodes divided by proposed nodes (target: at least 80 percent; below 60 percent indicates over-decomposition).
- **Dependency precision and recall**: Declared hard edges matched against a reference graph where one exists (target: at least 90 percent precision, since a false hard edge serialises work and a missing one permits an unverified consumption).
- **Graph stability across seeds**: Graph edit distance across a preregistered seed set (target: no more than 20 percent of node count; higher instability makes the decomposition unpromotable).
- **Downstream utility**: Nodes whose ablation degrades terminal verification, divided by accepted nodes (target: at least 70 percent; a node whose removal improves cost without harming accuracy is removed from the template).

**Efficiency and Robustness Metrics**:

- **Marginal yield over baseline**: Additional verified successes per additional thousand tokens, currency unit, model call, and second (target: positive; a non-positive figure returns the class to its baseline).
- **Parallel efficiency**: Total worker time over wall time against concurrency (target: at least 70 percent where 2 or more frontier-eligible nodes existed).
- **Verification share**: Verification cost over total run cost (target: 20 to 40 percent; below 20 percent indicates under-verification, above 40 percent indicates node granularity that is too fine).
- **Cache hit and stale-hit rate**: Accepted results served from cache, and the share of those later invalidated (target: stale-hit rate 0 percent, since a stale hit is a silent propagation channel).
- **Clean-to-perturbed degradation**: Accuracy difference under perturbed prompt wording, evidence order, irrelevant context, entity aliases, tool timeouts, missing evidence, and injected instructions (target: no more than 20 percentage points; a larger gap blocks promotion).

**Learning and Adaptation Mechanisms**:

- **First-error triage**: Queue every failed, expensive, re-decomposed, high-disagreement, safety-relevant, and seed-unstable run for offline attribution to its first bad ancestor, and promote the resulting corrections into the decomposition schema rather than into ad hoc prompt text.
- **Template promotion**: Promote a decomposition template only through paired, budget-matched evaluation against the baselines, and only where measured downstream utility is positive.
- **Verifier calibration**: Recalibrate every model judge against human labels and deterministic fixtures per task class, since judges exhibit position, style, and related biases [18], and hold each judge's individual verdicts rather than only their average.
- **Threshold recomputation**: Recompute every numeric bound in this guide per deployment against observed outcomes, since the defaults are operable starting points rather than measured constants.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the structure of a question and the verification of its parts rather than the content of any particular subject. Its phases hold wherever a question decomposes into separately answerable parts, at least one part can be checked by something other than the model that answered it, and a wrong part would corrupt the parts that follow.

### 4.1 Cross-Domain Application Patterns

**Multi-hop evidence synthesis**: The gate returns decompose because the direct baseline omitted a prerequisite entity. Nodes resolve entities, retrieve their attributes, and combine them; every retrieved-fact node requires a citation that opens and supports the value, and entity-resolution nodes require an identity match against an authoritative record rather than an inferred one. The dependency structure is shallow and wide, so most retrieval nodes execute in parallel and only the combining nodes serialise. The characteristic failure is an entity resolved to the wrong record early, which every downstream attribute then describes correctly for the wrong subject; the first-bad-ancestor attribution exists to make that failure visible rather than to leave it as an unexplained wrong answer.

**Layered quantitative analysis**: Nodes compute rates, adjustments, and aggregates that later nodes consume. Every computed-quantity node is reproduced by a deterministic runtime in an ephemeral, credential-free sandbox with denied egress by default, allowlisted packages, read-only inputs, and explicit processor, memory, output, filesystem, and wall-time limits. Units are part of the node contract, since a unit mismatch is the most common propagation channel in this domain and is caught deterministically rather than by inspection. Aggregation nodes reconcile totals against their accepted inputs before commit.

**Software defect isolation**: Nodes narrow a failure to a component, then to a function, then to a condition, and finally to a patch. The verification standard for a code node is a passing executable test, which makes this the domain where deterministic verification is strongest and the model verifier is used least. Interleaved reasoning and action can be embedded inside a single tool-dependent node under a capped loop [11], but the controlling graph retains dependencies, budgets, and invalidation, and a tool observation never authorises a change.

**Regulated policy application**: Nodes establish prerequisite findings, then apply clauses to them. Every policy-application node requires the cited clause to resolve and each of its conditions to be individually satisfied, and the approval gate binds before release because most actions in this domain are irreversible in practice. The trace becomes a deliverable rather than a diagnostic aid, so provenance capture, individual verifier judgements, and the composition manifest are retained rather than summarised.

**Compositional transformation and long-form derivation**: Nodes handle progressively longer prefixes or successive derivation stages, and the pattern's advantage concentrates where test depth exceeds demonstration depth [1]. Fluency is weak evidence of systematic competence in this domain, since models can score near-perfectly in distribution and far lower on novel structural combinations [3], so evaluation must cover longer chains, unseen operator combinations, reordered evidence, distractors, paraphrases, and seed dispersion rather than in-distribution accuracy alone.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk reversible work**: Cap the graph at 4 nodes and depth 2, run only the deterministic rungs of the verification ladder, and skip the model verifier entirely. Overhead above 2 times the direct baseline indicates the gate should have suppressed the pattern.
- **High-risk or irreversible work**: Retain every phase, require at least 1 signal of a source class distinct from the solver on every committed node, bind the approval gate before release, and prefer a labelled partial result or a declared abstention over an unverified completion.
- **Strict latency budgets**: Widen concurrency and shorten the graph rather than removing verification, since removing verification removes the pattern's only defence against propagation. Where latency forbids per-node verification, the gate suppresses the pattern and a single verified direct call runs instead.
- **Large graphs approaching the caps**: Split the question into two runs joined by an explicit interface rather than raising the node cap, because verification cost, context assembly cost, and invalidation blast radius all grow faster than node count.
- **Multi-tenant or cross-jurisdiction deployments**: Include authorisation scope and region in every cache key, prohibit reuse across tenants and authorisation scopes, minimise each node's context, tokenize identities where the domain permits, and test deletion through cache, trace, object store, and backup layers.

***

## V. Limitations and Considerations

**Decomposition generation is the dominant bottleneck**: The originating research states that decomposition prompts do not generalize well across domains and can fail within one, and reports that manually supplied decompositions rescued almost all sampled failures on a grade-school mathematics benchmark [1]. The consequence is that a deployment tuned on one task family can fail on an adjacent one for reasons invisible in the final answer. The mitigation is Phase 2, which treats the decomposition as evaluated output rather than an infallible plan, and the separate decomposition-quality metric set in Section III.D, which prevents a template from being promoted on final accuracy alone.

**The benchmark advantage is narrow and task-dependent**: The reported gains are large where test composition length exceeds demonstration length and small or negative otherwise. On a compositional grammar benchmark the reported figure was 99.7 percent against 16.2 percent for chain-of-thought and 16.7 percent for standard prompting on the length split, and that benchmark has unusually straightforward decompositions; on grade-school mathematics the one-shot figures were 62.39 percent against 60.87 percent, rising to 45.23 percent against 39.07 percent on problems needing at least 5 steps, while an engineered chain-of-thought prompt reached 68.613 percent against 68.01 percent for the best least-to-most configuration, and two-step problems were slightly worse. The consequence is that adopting the pattern by reputation rather than by measurement can reduce accuracy while raising cost. The mitigation is Step 1.2, which requires a verified cheaper baseline before the pattern is entered, and the marginal-yield metric, which returns a task class to its baseline where the yield is non-positive.

**Verification coverage is unequal across node types**: Computed quantities and code changes admit strong deterministic checks; intermediate claims and qualitative judgements often do not. The consequence is that the pattern's guarantee is strongest exactly where it is least needed and weakest where propagation does the most damage. The mitigation is the node-type verification table in Step 4.2, which requires 2 signals of distinct source class where no deterministic check exists, and the rule that a node with no signal stronger than self-assertion is made non-load-bearing or routed to human review rather than committed.

**The compounding product is a diagnostic, not a forecast**: Multiplying per-node accuracies assumes independence that real runs violate, because one wrong premise poisons its descendants and errors therefore correlate. The consequence is that the product understates some failure regimes and overstates others. The mitigation is to report it beside the observed all-nodes-correct rate and the first-bad-ancestor attribution, so that the gap between them is itself the measurement rather than the product being treated as a prediction.

**Self-assessment does not substitute for external evidence**: A model can degrade an initially correct answer without external feedback [22], and a coherent stated rationale can be causally unfaithful to the computation that produced the answer [23][24]. The consequence is that a node's own explanation of why its answer is right carries no verification weight. The mitigation is the verification ladder's ordering, which places deterministic and evidence rungs ahead of any model verifier, and the source-class rule, which prevents solver-verifier agreement from satisfying a hard criterion.

**Decomposition multiplies privacy exposure**: The pattern replicates sensitive facts across prompts, caches, traces, and verifier calls, and intermediate results can reveal user secrets, inferred sensitive attributes, proprietary documents, and security policy [31]. The consequence is that a system with acceptable exposure as a single call can become unacceptable as a graph. The mitigation is the disclosure boundary in Section III.A, minimal per-node context, short retention for raw drafts, restricted cross-region and cross-provider transfer, and tested deletion propagation through every storage layer.

**Every threshold here is a deployment default**: The caps of 12 subproblems, depth 4, 3 candidates, 2 repairs, 2 re-decompositions, 1 malformed-output retry, 2 assembly repairs, 32 model calls, 20 tool calls, 60,000 tokens, 120 seconds, and 5 times baseline cost are conservative starting values transcribed from the originating prose source, not measured optima. The metric targets in Section III.D were selected to be operable on first deployment. The consequence is that a deployment inheriting them unchanged may be simultaneously too permissive for one task class and too restrictive for another. The mitigation is the threshold-recomputation requirement in Section III.D, obliging each deployment to recompute bounds per task class against observed outcomes before treating them as policy.

**External figures were transcribed rather than re-derived**: The benchmark figures, failure-analysis counts, and reported improvements in this guide come from the originating prose source's citations. Three were confirmed against the cited pages during conversion: the least-to-most paper's title, authors, and its reported compositional-grammar result of at least 99 percent against roughly 16 percent for chain-of-thought; the compositional-generalization benchmark's 96 to 99 percent in-distribution against 16 to 35 percent generalization accuracy with 6 to 8 percentage points of seed sensitivity; and the successive-prompting improvement of approximately 5 absolute F1 points on a few-shot version of a reading-comprehension benchmark. The remaining figures were not independently re-verified. The consequence is that a figure could be misattributed without any check in this guide detecting it. The mitigation is that every such figure is carried as a claim of the cited work rather than asserted as a property of the pattern, and that no numeric threshold in Section II depends on an unverified figure.

**Structural conformance is not correctness**: A run can satisfy every checkpoint here, commit every node with a passing verifier, and still answer a question the requester did not ask, because the decomposition was faithful to a misread objective. The consequence is that the framework detects propagation and structural defects, not misdirected purpose. The mitigation is Step 6.1's requirement that the composed answer address the terminal node's objective verbatim, and the human review trigger on the highest risk tier; neither substitutes for review of the objective itself.

***

## VI. Conclusion and Summary

Least-to-most reasoning is a propagation-control discipline before it is a decomposition technique. Its distinguishing property is that every step consumes the previous answer, which means a wrong early answer corrupts everything after it and does so silently, because later steps operate correctly on bad input and produce fluent, internally consistent, wrong results. The framework's centre of gravity is therefore not the decomposition prompt but the commit rule: an answer becomes visible to its consumers only after every hard check has passed, a decomposition failing the ordering or completeness check is rejected rather than patched, and every repair is scoped, counted, and bounded.

The partition between tiers is what makes that rule enforceable. Software owns dependency-order validation, node state, answer propagation, verification execution, retry counting, and completeness checking, because each of those requires exactness that inference cannot supply and would otherwise be delegated to the same model whose output is under examination. A model owns decomposition and solving, which are open-vocabulary judgements no deterministic rule covers. Where the tiers disagree at any of the three named handoffs, the deterministic verdict is final.

A team introducing this pattern should instrument the baseline before building the graph. Measure the direct and single-chain baselines under the outcome rubric that will judge the final answer, then add decomposition with deterministic gating and per-node verification but no re-decomposition, and evaluate that configuration on paired, budget-matched data. Only then add bounded re-decomposition, caching, and parallel dispatch. A decomposition that raises cost without raising verified accuracy at matched budget is a regression regardless of how well-structured its subquestions read.

**Key Success Factors**:

- **Baseline displacement before decomposition**: The pattern is entered only after a cheaper method has failed under the same rubric, with the specific failure recorded as a hypothesis the decomposition is meant to repair.
- **Structural gating by software**: Ordering and completeness are decided by cycle detection, ancestor-reference checking, and coverage against a contract-derived required-item set, never by a model's assessment of its own plan.
- **No unverified answer feeds forward**: Commit is the sole event that makes an answer load-bearing, and a deterministic failure is never overridden by a model verifier, a judge score, or a learned process score.
- **Dependency structure, not sequence**: Only hard edges constrain order, independent ready nodes execute in parallel up to the cap, and a graph in which nearly every node is independent is the wrong pattern rather than a wide one.
- **Bounded and scoped repair**: Failures are classified before replacement, ancestors are frozen, invalidation is computed transitively, counters are never reset, and the caps on repairs and re-decompositions terminate the run rather than being renegotiated inside it.
- **Attribution over aggregate accuracy**: Every failed run is traced to its earliest bad ancestor, and decomposition quality is measured separately from final accuracy, because a good final answer can conceal subquestions that contributed nothing.

By following this guide, AI agents can convert a question too compositional to answer directly into an ordered set of verified answers, prevent a single bad intermediate from corrupting everything downstream, and terminate through a declared exit that a reviewer can audit rather than through a fluent answer nobody checked.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them and were not independently re-verified during conversion, with three exceptions noted inline as verified: entries 1, 3, and 5 were retrieved from their cited locations during this conversion, and their titles, authors, and the figures this guide relies on were confirmed against those pages.

**Corpus pointers**:

- `Production Guide to Least-to-Most Reasoning` — the originating prose guide from which this operational guide was derived. Source of the two-stage structure, the decomposition-need criteria, the decomposition-quality criteria, the verification-before-commit rule, the invalidation and re-decomposition semantics, the default numeric caps, the cache-key composition, the logging field inventory, the metric definitions, and the failure-mode inventory. Its inline citations to primary literature supply the external references listed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/planning/guide_IntelligentGoalDecomposition.md` — owns decomposition of an objective into subgoals and tasks, producing a goal tree consumed by a planner or executor. Source of the node contract and dependency edge terminology adopted here, and the boundary stated in Section 1.2.
- `advanced_task_guides/planning/guide_HierarchicalTaskNetworkPlanning.md` — owns refinement of compound tasks into primitive tasks against a versioned domain model with authored methods. The boundary against generated per-run decomposition is stated in Section 1.2.
- `advanced_task_guides/reasoning/guide_ChainOfThoughtReasoning.md` — owns intermediate reasoning inside one chain, and supplies the baseline that Step 1.2 requires before this pattern is entered.
- `advanced_task_guides/reasoning/guide_SelfConsistency.md` — owns diversified sampling toward an adjudicated answer, and is the routing target where complete attempts are cheap and decomposition is unstable.
- `advanced_task_guides/reasoning/guide_ChainOfVerification.md` — owns post-draft claim auditing, and is the companion pattern for a fact-dense final assembly in Step 6.2.
- `advanced_task_guides/reasoning/guide_TreeOfThought.md` — owns bounded search over competing partial solutions, and is the routing target where the dominant uncertainty is which alternative path to pursue.
- `advanced_task_guides/reasoning/guide_MetacognitiveMonitoring.md` — owns calibrated monitoring signals for an external control layer, applicable to the confidence and stability signals used in Step 4.2.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — owns the control loop that decides whether a further computation is worth its cost, applicable to the Decomposition-Need Gate in Section 1.3.
- `advanced_task_guides/reasoning/guide_GraphOfThought.md` — owns reasoning over a dependency graph of typed intermediate results in which a node may have several parents, including the merge admission check, incremental cycle prevention, dependency-fingerprint caching, and invalidation propagated through hard edges. It is the routing target named in Section 1.2 where subproblem results must be merged and reused rather than each consumed once in order. The dependency graph derived here is a plan fixed before solving; its graph is a derivation that grows and is revised during the run.
- `advanced_task_guides/reasoning/guide_SkeletonOfThought.md` — owns independent decomposition for concurrent expansion, including the outline quality gate for coverage and non-overlap, the four independence tests, bounded fan-out under a concurrency cap, and deterministic assembly with contradiction reconciliation. It is the parallel-expansion contrast named in Section 1.2: its points are chosen so that none consumes another's answer, and its objective is latency rather than the error containment this guide exists to enforce.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, III, IV, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*The method and its compositional-generalization setting*

1. Zhou and colleagues, *Least-to-Most Prompting Enables Complex Reasoning in Large Language Models* — https://arxiv.org/abs/2205.10625 (verified during conversion)
2. Lake and Baroni, SCAN — https://arxiv.org/abs/1711.00350
3. Kim and Linzen, *COGS: A Compositional Generalization Challenge Based on Semantic Interpretation* — https://arxiv.org/abs/2010.05465 (verified during conversion)

*Related decomposition and planning patterns*

4. Khot and colleagues, Decomposed Prompting — https://arxiv.org/abs/2210.02406
5. Dua and colleagues, *Successive Prompting for Decomposing Complex Questions* — https://arxiv.org/abs/2212.04092 (verified during conversion)
6. Wang and colleagues, Plan-and-Solve — https://arxiv.org/abs/2305.04091
7. Ning and colleagues, Skeleton-of-Thought — https://arxiv.org/abs/2307.15337
8. Press and colleagues, Self-Ask — https://arxiv.org/abs/2210.03350
9. Yang and colleagues, HotpotQA — https://aclanthology.org/D18-1259/
10. Min and colleagues, multi-hop question decomposition — https://aclanthology.org/P19-1613/

*Tool use, computation, and verification*

11. Yao and colleagues, ReAct — https://arxiv.org/abs/2210.03629
12. Gao and colleagues, Program-Aided Language Models — https://arxiv.org/abs/2211.10435
13. Chen and colleagues, Program-of-Thought — https://arxiv.org/abs/2211.12588
14. Dhuliawala and colleagues, Chain-of-Verification — https://aclanthology.org/2024.findings-acl.212/
15. Yao and colleagues, Tree of Thoughts — https://arxiv.org/abs/2305.10601
16. Besta and colleagues, Graph of Thoughts — https://arxiv.org/abs/2308.09687

*Decomposition quality, judges, and process supervision*

17. Zhang and colleagues, visual question decomposition — https://aclanthology.org/2024.findings-emnlp.107/
18. Chen and colleagues, judge bias in large language model evaluation — https://aclanthology.org/2024.emnlp-main.474/
19. Lightman and colleagues, process supervision — https://arxiv.org/abs/2305.20050
20. Wang and colleagues, self-consistency — https://arxiv.org/abs/2203.11171

*Context use, self-correction, and rationale faithfulness*

21. Liu and colleagues, lost in the middle — https://arxiv.org/abs/2307.03172
22. Huang and colleagues, limits of self-correction — https://arxiv.org/abs/2310.01798
23. Turpin and colleagues, unfaithful stated reasoning — https://arxiv.org/abs/2305.04388
24. Lanham and colleagues, measuring reasoning faithfulness — https://arxiv.org/abs/2307.13702

*Reasoning-model baselines*

25. OpenAI reasoning guidance — https://developers.openai.com/api/docs/guides/reasoning-best-practices
26. DeepSeek-R1 report — https://arxiv.org/abs/2501.12948
27. Anthropic extended-thinking documentation — https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking

*Provenance, instrumentation, and application security*

28. W3C, PROV-O — https://www.w3.org/TR/prov-o/
29. OpenTelemetry GenAI semantic conventions — https://opentelemetry.io/docs/specs/semconv/gen-ai/
30. OWASP prompt-injection guidance — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
31. OWASP sensitive-information guidance — https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/
