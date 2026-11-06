# Agentic Retrieval-Augmented Generation

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Agentic retrieval-augmented generation constitutes the task family of retrieval in which an agent decides whether to retrieve at all, what to retrieve, how to reformulate a query when results are poor, when to retrieve again, and when to stop, rather than executing one fixed retrieve-then-generate pass. This guide provides AI agents with a structured protocol for operating that decision as a bounded control loop. It specifies a retrieval-decision gate that suppresses retrieval where the answer is already available from supplied context, a query plan validated before execution, a retrieval loop carrying an explicit iteration ceiling and a per-iteration progress test that must show measurable evidence gain, a reformulation bound that caps how many query variants are attempted, an evidence sufficiency condition stated as a checkable predicate rather than as confidence, and a stopping rule terminating on convergence, budget exhaustion, or a declared abstention. It partitions the work across a deterministic tier owning iteration counting, budget enforcement, progress arithmetic, repetition detection, citation resolution, and the stopping rule, and a model tier owning the retrieve-or-answer decision, reformulation, relevance judgement, and sufficiency assessment. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that an agent able to retrieve again does not retrieve forever.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Agentic retrieval-augmented generation**: Retrieval organised as a sequential decision process in which the next retrieval, reformulation, verification, or stopping action depends on observed state. A pipeline that issues several retrieval calls in a fixed order is not agentic; adaptation to observation is the distinguishing property.

**Retrieval-decision gate**: The bounded test executed before any retrieval action, returning answer-from-context, retrieve, or abstain. It exists because retrieving for a question answerable from supplied context spends budget and injects distractors.

**Run contract**: The declared goal, required answer form, source policy, authority hierarchy, freshness requirement, risk tier, authorization context, output requirements, and every numeric budget ceiling, fixed before the first retrieval action and never weakened by a later revision. It is the per-run instance of the retrieval contract that the category's architecture-selection guidance declares before any method is chosen; the two are the same object at different scopes, and where they disagree the retrieval contract binds.

**Query plan**: The decomposition of the goal into sub-questions, each carrying a stable identifier, a required or optional flag, prerequisites, an admissible-evidence definition, an eligible tool set, a join rule, and a budget allocation.

**Retrieval iteration**: One bounded cycle of issue-query, admit-results, compute-progress, decide-continue. The iteration, not the tool call, is the unit the iteration bound counts.

**Iteration bound**: The declared maximum number of retrieval iterations permitted per sub-question and per run. It is enforced by a deterministic counter that no model output may raise.

**Progress test**: The per-iteration arithmetic deciding whether an iteration produced measurable gain. It computes an evidence-gain delta and a novel-evidence ratio from the admitted evidence, not from the model's report of its own progress.

**Evidence-gain delta**: The count of newly covered required sub-questions, newly supported material claims, newly admitted authoritative evidence identifiers, and resolved contradictions produced by one iteration. Rephrased queries, duplicate spans, summaries of already-held evidence, and confidence changes contribute zero.

**Novel-evidence ratio**: Eligible non-duplicate evidence admitted in an iteration divided by eligible evidence inspected in that iteration. It measures whether the retrieval surface is still yielding new material.

**Query reformulation**: A diagnosed change to the query, its parameters, or its route, issued in response to a named retrieval failure class. An undiagnosed rewrite is not a reformulation and does not reset any counter.

**Reformulation bound**: The declared maximum number of query variants attempted per sub-question, counted inclusive of the original query.

**Evidence sufficiency**: The checkable condition deciding whether the loop may exit to synthesis. It is a predicate over the evidence ledger, evaluated by deterministic checks over model-assigned labels, never a self-reported confidence score.

**Stopping rule**: The deterministic rule terminating the loop, admitting exactly three terminal outcomes: convergence on a sufficient evidence set, budget exhaustion, or a declared abstention.

**Declared abstention**: A terminal outcome in which the agent states what is known, what remains unknown, what was attempted, and what would be required, in place of an answer. Abstention is a success of the control loop, not a failure of the task.

**Non-converging loop**: A loop whose measured gain has fallen below the declared floor while its budget remains unexhausted. Its numeric signature is stated in Section 1.2 and it triggers a mandatory transition rather than a further iteration.

**State hash**: The normalised digest of goal, constraints, sub-question, canonical query, source route, filters, parameters, and ordered admitted evidence identifiers. Repetition of a state hash is proof that an iteration cannot add information.

**Evidence ledger**: The append-only record of admitted evidence, each entry carrying source identity, content hash, exact span, retrieval time, authority tier, freshness, authorization decision, injection verdict, and the sub-questions it supports.

**Verification reserve**: The portion of time, tokens, and money withheld from retrieval and spent only on final sufficiency evaluation, synthesis, and citation verification.

### 1.2 The Bounded Retrieval Control Loop

**The discipline this guide imposes**: An agent that can decide to retrieve again can retrieve forever. The dominant production failure of agentic retrieval is not poor retrieval quality but unbounded retrieval that exhausts budget without converging. Every control in this guide exists to bound the loop: an iteration ceiling, a per-iteration progress test that must show measurable gain, a reformulation ceiling, and a stopping rule with exactly three terminal outcomes.

**Loop structure**: The loop runs gate, plan, retrieve, measure, decide. The gate decides whether retrieval is warranted at all. The plan converts the goal into bounded sub-questions. The retrieval iteration issues exactly one action and admits its results under validation. The progress test computes gain from admitted evidence. The decision issues exactly one transition: continue, reformulate, change route, synthesize, escalate, or abstain.

**Numeric signature of a non-converging loop**: Any one of the following, measured over admitted evidence, establishes non-convergence. Evidence-gain delta of 0 for 2 consecutive iterations. Novel-evidence ratio below 0.30 for 2 consecutive iterations. Repetition of a state hash already recorded in the run. Alternation between 2 query variants or 2 source routes across 3 consecutive iterations without an intervening gain above 0. Sufficiency score unchanged across 2 consecutive iterations.

**Mandatory response to non-convergence**: The controller must not issue a further iteration on the same sub-question and the same route. It must issue exactly one of three transitions: a diagnosed reformulation, where the reformulation bound is not yet exhausted and a named failure class was identified; a route change to a different approved source class, where one remains eligible; or termination of that sub-question as unresolved, which propagates to the sufficiency test and may force a declared abstention. Continuing because budget remains is prohibited: remaining budget is never a justification for a further iteration.

**The repetition prohibition**: An identical query must never be reissued against an identical route after an identical failure. The controller computes the canonical query digest before dispatch and rejects any digest already present in the run's dispatch log for the same route and filters. This rejection is deterministic and is not subject to model override.

**Retrieval is not free**: Each additional iteration adds latency, tokens, and money, and admits further material into context that may distract rather than inform. The loop therefore treats an iteration as an expenditure requiring a positive expected return, not as a default behaviour to be stopped only on failure.

**Re-scoping from below the agent layer**: Part of the literature this method draws on trains the retrieval policy or a stopping value function into model weights, learning when further retrieval will improve the answer. Weight training is not reachable by an agent at runtime and is therefore outside this guide's scope. The executable surrogate specified here is a deterministic controller that measures realised gain per iteration and refuses a model-proposed continuation whose measured gain falls below a numeric floor. The surrogate approximates a learned stopping policy using observed evidence rather than a learned value estimate, and Section V records what that substitution costs.

**Boundary against neighbouring patterns**: This guide owns the control loop. Retrieval quality mechanics such as parsing, chunking, hybrid fusion, and reranking belong to general retrieval engineering and are consumed here as tool behaviour rather than specified. Evidence-quality routing that classifies a retrieval result and repairs it belongs to corrective retrieval, which this guide invokes as a bounded action inside one iteration rather than as an outer loop. Segment-level self-assessment of generated text belongs to self-assessing retrieval, which this guide consumes as one signal feeding the sufficiency predicate. Where the failure is poor evidence quality repairable by one bounded correction, or where the need is generation critique without novel planning, the loop specified here is not warranted.

### 1.3 The Retrieval-Decision Gate

The loop is not free, and neither is the first retrieval. Agents must run a cheap gate, bounded to 2 percent of the run's token and time budget, returning answer-from-context, retrieve, or abstain.

**Answer-from-context conditions**: Return answer-from-context where the supplied context already contains an exact span supporting every material claim the answer requires; where the task is purely transformational and all evidence is supplied; where a designated record, deterministic calculation, or rules engine yields the exact answer without search; or where the question concerns the conversation's own prior turns. Retrieving under these conditions spends budget and admits distractors that compete with evidence already held.

**Retrieve conditions**: Return retrieve where at least one material claim lacks a supporting span in context; where the answer depends on facts outside the model's declared knowledge boundary; where the freshness requirement exceeds the age of the supplied context; or where the source policy requires an authoritative citation regardless of whether the model reports knowing the answer.

**Abstain conditions**: Return abstain without retrieving where no eligible tool can reach the required source class; where the request would send restricted content to an external destination; where the authorization context does not cover the required corpus; or where the remaining deadline is already below the verification reserve.

**Loop-escalation conditions**: Return retrieve with the full loop only where the sequence of retrieval actions cannot be predetermined. Where the valid path is known, a fixed sequence executes it more cheaply and more auditably than a planner. Where one retrieval pass already meets the correctness, citation, latency, and cost gates on a measured slice, the loop adds cost without benefit.

**Retrieval-Decision Gate Table**:

| Observable condition | Evidence state | Gate verdict |
| :-- | :-- | :-- |
| Every material claim has a supporting span in context | Complete | Answer from context |
| Task is transformation of supplied material | Complete | Answer from context |
| Designated record or deterministic computation applies | Reachable exactly | Direct lookup, no loop |
| One material claim unsupported, path known | Incomplete, path fixed | Single-pass retrieval |
| Several claims unsupported, path depends on findings | Incomplete, path unknown | Invoke the bounded loop |
| Freshness requirement exceeds context age | Stale | Invoke retrieval under a freshness filter |
| Required corpus outside authorization scope | Unreachable | Abstain, record the missing scope |
| Remaining deadline below verification reserve | Any | Abstain or answer from context only |

**Numeric gate rules**: Invoke the loop only where at least 1 material claim lacks a context span and at least 2 distinct eligible retrieval routes exist, since a single route removes the controller's reformulation lever. Where gate execution would exceed 2 percent of the run budget, default to single-pass retrieval and record the overrun. Where a single-pass baseline meets all output gates on the measured slice, suppress the loop, because complexity retained without a measured failure slice is a recurring cost.

### 1.4 Execution Tier Partition and Authority

The partition below is binding. Every phase of Section II is assignable to a tier, and every step mixing tiers names its handoff.

**Deterministic tier**: Software, counters, schema validators, digests, and budget services own the following, because each requires exactness, reproducibility, and auditability that model inference cannot supply. Iteration counting per sub-question and per run. Budget ledger enforcement across steps, tool calls, tokens, context, fetch bytes, cost, concurrency, and wall clock. Progress-test arithmetic, including evidence-gain delta and novel-evidence ratio. Query-repetition detection through canonical query digests and state hashes. Citation resolution, including span matching, source identity verification, and link resolution. Execution of the stopping rule. Authorization, egress, freshness, and approval gates. Reformulation counting against the declared ceiling.

**Model tier**: LLM calls own the following, because each requires open-vocabulary judgement no deterministic rule covers. The retrieve-or-answer decision at the gate. Goal decomposition into sub-questions. Query reformulation, including the diagnosis of the failure class that licenses it. Relevance judgement over retrieved candidates. Sufficiency assessment, expressed as per-claim support labels rather than as a global confidence figure. Conflict classification across contradictory evidence. Answer synthesis constrained to the accepted evidence ledger.

**Hybrid tier and the authority rule**: The model proposes and the deterministic controller disposes. The model proposes continuation, a reformulation, a route change, or a sufficiency verdict; the controller admits the proposal only where the iteration bound, the reformulation bound, the progress floor, the repetition check, and the budget ledger all permit it. Where the two disagree, the deterministic tier holds authority without exception. A model may shorten a loop, lower a bound, or declare an abstention early; a model may never raise a ceiling, reset a counter, override a repetition rejection, or convert budget exhaustion into a further iteration.

**Budget exhaustion produces abstention, not a guess**: Where the budget ledger reports exhaustion before the sufficiency predicate is satisfied, the controller terminates the loop and emits a declared abstention carrying the supported partial result. Synthesising an unsupported answer under exhaustion is prohibited, because it converts a detectable control failure into an undetectable content failure.

**Artifact ownership**: The deterministic tier owns the budget ledger, the dispatch log, the state-hash set, the iteration counters, the citation-resolution report, and the termination record. The model tier owns the sub-question set, the query variants, the relevance labels, the support labels, and the draft. The evidence ledger is written by the deterministic tier from model-proposed admissions that passed validation, so neither tier owns it alone.

***

## II. Operational Framework: Bounded Retrieval Control Under an Evidence-Gain Budget

The framework assumes the retrieval-decision gate has returned retrieve with the full loop. Phases 1 through 5 form the control loop: Phase 5 either terminates the run through a declared outcome or returns control to Phase 3 with updated state. Phase 6 runs after termination on convergence. Phase 7 runs alongside the loop and completes before the run is closed.

### Phase 1: Run Contract and Retrieval-Decision Gating

**Objective**: Fix the immutable run contract and every numeric ceiling, and confirm through the gate and a frozen baseline that a bounded retrieval loop is warranted before any iteration is spent.

#### Step 1.1: Fix the Immutable Run Contract and Budget Ledger

**Required Actions**:

- Record the goal, required answer form, audience, source boundaries, authority hierarchy, freshness requirement, jurisdiction, material-claim policy, risk tier, and authorization context as immutable run state.
- Set every ceiling numerically, covering retrieval iterations per sub-question, retrieval iterations per run, query variants per sub-question, plan revisions, verification rounds, and input, output, evidence, and context token limits.
- Apply the deployment defaults where no measured value exists: 2 retrieval iterations per sub-question plus 1 declared alternate route, 12 retrieval iterations per run, 3 query variants per sub-question inclusive of the original, 2 plan revisions, 2 verification rounds, and 8 required sub-questions.
- Reserve the measured p95 time, tokens, and cost for sufficiency evaluation, synthesis, and citation verification, defaulting to 20 percent of the run budget where no measurement exists.
- Define the evidence-gain function, the novel-evidence floor, the sufficiency predicate, the abstention conditions, and the escalation gates before the first retrieval action.

**Required Outputs**:

- An immutable run contract record carrying goal, source policy, risk tier, and output requirements.
- A budget ledger naming every bounded resource with its numeric ceiling and its consumed value.
- A declared verification reserve expressed as a percentage of each budget dimension.
- A stated evidence-gain function, novel-evidence floor, and sufficiency predicate.

**Quality Checkpoints**:

- Every budget dimension carries a numeric ceiling; an unbounded dimension halts the run before the first iteration.
- The verification reserve is subtracted from the retrieval budget rather than assumed available at the end.
- The sufficiency predicate is evaluable by a deterministic check over labelled evidence, not by a confidence figure.
- The contract distinguishes unresolved from failed, so a declared abstention is recorded as a supported outcome.

***

#### Step 1.2: Execute the Retrieve-or-Answer Decision

**Required Actions**:

- Enumerate the material claims the required answer form obliges, and test each against the spans already present in supplied context.
- Return answer-from-context where every material claim has a supporting span, and terminate the run without any retrieval action.
- Return retrieve where at least 1 material claim lacks a span, recording which claims are unsupported so the plan inherits them as required sub-questions.
- Return abstain where the required source class is unreachable, unauthorized, or prohibited, and record the missing capability rather than substituting a reachable but inadequate source.
- Cap the gate at 2 percent of the run token and time budget, and record the measured gate cost against the ledger.

**Required Outputs**:

- A gate verdict of answer-from-context, retrieve, or abstain, with its triggering condition named.
- An unsupported-claim list carrying one entry per material claim lacking a context span.
- A recorded gate cost expressed as a percentage of the run budget.

**Quality Checkpoints**:

- The verdict names a specific condition from Section 1.3 rather than a general judgement of difficulty.
- Retrieval is not invoked where every material claim already carries a context span; a retrieval issued under that condition is a defect and is charged to the ledger as waste.
- Gate cost does not exceed 2 percent of the run budget; an overrun downgrades the run to single-pass retrieval.
- The handoff is explicit: the model tier issues the verdict and the deterministic tier records it, debits the gate cost, and enforces the downgrade.

***

#### Step 1.3: Establish and Freeze the Baseline Route

**Required Actions**:

- Execute the cheapest adequate baseline once, selecting direct structured lookup, full authorized context reading, or a single hybrid retrieval pass.
- Evaluate the baseline output against the contract's support, citation, latency, and cost gates before any loop iteration is authorised.
- Terminate the run at the baseline where all gates pass, and record that agentic control was suppressed with the measured evidence.
- Record the exact failure class where a gate fails, naming the unsupported claims or the missing sub-questions that justify the loop.
- Freeze the baseline output and its measurements as the comparison record for the run's marginal-value assessment.

**Required Outputs**:

- A baseline output with per-gate pass or fail verdicts.
- A named failure class justifying the loop, or a suppression record closing the run.
- A frozen baseline measurement set covering support coverage, citation coverage, latency, and cost.

**Quality Checkpoints**:

- The loop is entered only against a named, recorded baseline failure; entry without one is a defect.
- The baseline measurement set is frozen before the first iteration, so later marginal-value claims are comparable.
- The baseline route remains available as a fallback for the remainder of the run.

***

### Phase 2: Query Planning and Decomposition

**Objective**: Convert the goal into a bounded, validated set of sub-questions with eligible routes and allocated budgets, so that iteration counting has a well-defined scope and coverage is measurable.

#### Step 2.1: Decompose the Goal Into Bounded Sub-Questions

**Required Actions**:

- Decompose the goal only where it requires multiple facts, sources, hops, time periods, entities, or domains; leave a simple lookup undecomposed.
- Assign each sub-question a stable identifier, a testable answer criterion, and a classification of required, optional, or exploratory.
- Record prerequisites and dependents for each sub-question, and define the join as an exact key, entity identity, time interval, jurisdiction, unit, relation, or aggregation rule.
- Define admissible evidence and the required source authority tier per sub-question, and define what an unresolved outcome looks like for that sub-question.
- Merge or drop sub-questions that are semantic duplicates, cannot affect the answer, or have no eligible evidence route, and cap the required set at 8 entries.

**Required Outputs**:

- A sub-question set of 1 to 8 required entries, each with identifier, criterion, classification, dependencies, join rule, and admissible-evidence definition.
- A dependency graph confirming a bounded acyclic order, with any repair loop declared explicitly.
- A merge-and-drop record naming each removed candidate and its reason.

**Quality Checkpoints**:

- Every unsupported claim from Step 1.2 maps to at least 1 required sub-question.
- Every sub-question carries a testable answer criterion; entries without one are removed before execution.
- Required sub-question count does not exceed 8; a larger decomposition halts for re-scoping, since iteration ceilings multiply across sub-questions.
- Each sub-question carries a defined unresolved outcome, so no branch is forced to produce an answer.

***

#### Step 2.2: Validate the Plan Before Any Retrieval Action

**Required Actions**:

- Confirm that every required output requirement maps to at least 1 sub-question, and that no sub-question weakens an authorization, source, freshness, or output constraint.
- Confirm that every sub-question can be answered, disproved, or marked unresolved by at least 1 approved route.
- Confirm that the sum of per-sub-question budget allocations plus the verification reserve does not exceed the run ceiling on any dimension.
- Reject and revise a plan failing any validation, and count the revision against the plan-revision ceiling of 2.
- Require that a plan revision produce measurable gain: new coverage of a required output, a previously blocked sub-question made executable, removal of an impossible or duplicate branch, resolution of a dependency, or reduced expected cost at equal coverage. New wording alone counts as zero gain and does not license a revision.

**Required Outputs**:

- A plan validation report with a pass or fail verdict per validation rule.
- A budget allocation table assigning each sub-question its iteration, token, and cost share.
- A plan revision record naming the diagnosed defect and the measured gain of each revision.

**Quality Checkpoints**:

- Allocated budgets plus the verification reserve sum to no more than 100 percent of each run ceiling.
- Plan revisions do not exceed 2; a third required revision halts the run for escalation.
- No revision is admitted whose only change is rewording, since a revision without gain is an iteration spent on nothing.
- The plan hash is recorded so that a repeated plan is detectable as oscillation.

***

#### Step 2.3: Bind Each Sub-Question to an Eligible Route Set

**Required Actions**:

- Filter candidate routes by authorization, purpose, data classification, tenant, and region before any capability comparison.
- Prefer an exact system of record over unstructured retrieval where one answers the sub-question directly.
- Rank the remaining routes by source authority, freshness, and required modality, then by remaining budget, then by expected evidence gain per unit cost.
- Record at least 2 eligible routes per required sub-question where the corpus permits, since a single route removes the route-change lever the stopping rule depends on.
- Record rejected routes with their rejection reasons, so a later route change does not re-propose a rejected option.

**Required Outputs**:

- A per-sub-question eligible route list ordered by expected gain per unit cost.
- A rejected-route record with one reason per rejection.
- A declared alternate route per required sub-question, or an explicit record that none exists.

**Quality Checkpoints**:

- Every required sub-question carries at least 1 eligible route; an entry with none is marked unresolved before execution rather than attempted.
- Sub-questions with exactly 1 eligible route are flagged, because their iteration bound cannot be extended by a route change.
- Route ordering is computed by the deterministic tier from recorded authority, freshness, cost, and latency attributes, not asserted by the model.

***

### Phase 3: Bounded Retrieval Iteration and the Progress Test

**Objective**: Advance exactly one sub-question by exactly one retrieval iteration, admit its results under validation, and compute from the admitted evidence whether the iteration produced measurable gain.

#### Step 3.1: Issue One Retrieval Action and Admit Its Results

**Required Actions**:

- Compute the canonical query digest from the normalised query, sub-question, route, filters, and parameters, and reject dispatch where that digest already appears in the run's dispatch log for the same route.
- Debit the iteration counter and the reserved budget atomically before dispatch, so a failed call still consumes its iteration.
- Issue exactly 1 retrieval action per iteration, preserving entities, dates, units, negation, jurisdiction, and source constraints from the sub-question.
- Validate every returned item for authorization, integrity, injection, relevance, authority tier, freshness, and exact-span support before admission, and admit only items passing all checks.
- Append admitted items to the evidence ledger with source identity, content hash, exact span, retrieval time, authority tier, freshness, and the sub-questions they support.

**Required Outputs**:

- A dispatch record carrying the canonical query digest, route, filters, parameters, and iteration index.
- An admitted-evidence set appended to the ledger, with one validation verdict per item.
- A rejected-candidate record naming each rejection class and its count.
- An updated iteration counter and budget ledger reflecting the debit.

**Quality Checkpoints**:

- No dispatch repeats a canonical query digest already recorded for the same route; a repeat is rejected deterministically and is never overridden by the model.
- Every ledger entry carries an exact span; an entry admitted without a span is a defect and is quarantined.
- The iteration counter is debited before dispatch, so a timeout or an empty result still consumes its iteration and cannot produce an unbounded retry.
- The handoff is explicit: the model tier proposes the query and labels relevance, and the deterministic tier owns the digest check, the counter, and the admission gate.

***

#### Step 3.2: Compute the Per-Iteration Progress Test

**Required Actions**:

- Compute the evidence-gain delta as the count of newly covered required sub-questions, newly supported material claims, newly admitted authoritative evidence identifiers, and resolved contradictions attributable to this iteration.
- Compute the novel-evidence ratio as eligible non-duplicate evidence admitted divided by eligible evidence inspected in this iteration.
- Score rephrased queries, duplicate spans, near-duplicate pages, summaries of already-held evidence, and changes in stated confidence as zero gain, without exception.
- Record the iteration as productive where the evidence-gain delta is at least 1 and the novel-evidence ratio is at least 0.30; record it as unproductive otherwise.
- Append the gain figures to the run's gain curve, so the marginal return of successive iterations is measurable rather than inferred.

**Progress Test Thresholds**:

| Measured quantity | Productive threshold | Consequence of breach |
| :-- | :-- | :-- |
| Evidence-gain delta | At least 1 per iteration | Iteration recorded unproductive |
| Novel-evidence ratio | At least 0.30 per iteration | Iteration recorded unproductive |
| Consecutive unproductive iterations | No more than 1 | Non-convergence declared at 2 |
| Duplicate-evidence ratio | No more than 0.50 per iteration | Route flagged as exhausted |
| Sufficiency score change | Above 0 across 2 iterations | Non-convergence declared at 0 |

**Required Outputs**:

- A per-iteration progress record carrying evidence-gain delta, novel-evidence ratio, and a productive or unproductive verdict.
- An updated gain curve indexed by iteration for the sub-question and for the run.
- A consecutive-unproductive counter per sub-question.

**Quality Checkpoints**:

- Gain is computed by the deterministic tier from ledger deltas; a model's report of its own progress is never accepted as the gain figure.
- Every iteration receives a verdict; an iteration without a computed progress record halts the loop.
- Zero-gain categories are applied literally, so a fluent summary of held evidence never registers as progress.

***

#### Step 3.3: Detect Non-Convergence and Enforce the Repetition Prohibition

**Required Actions**:

- Compute the state hash over goal, constraints, sub-question, canonical query, route, filters, parameters, and ordered admitted evidence identifiers after every iteration.
- Declare non-convergence on any of the following: evidence-gain delta of 0 for 2 consecutive iterations; novel-evidence ratio below 0.30 for 2 consecutive iterations; repetition of a state hash already recorded in the run; alternation between 2 query variants or 2 routes across 3 consecutive iterations without an intervening gain above 0; sufficiency score unchanged across 2 consecutive iterations.
- Block any further iteration on the same sub-question and the same route once non-convergence is declared, regardless of remaining budget.
- Issue exactly 1 of 3 mandatory responses: a diagnosed reformulation where the reformulation bound permits it, a route change where an unrejected eligible route remains, or termination of the sub-question as unresolved.
- Record the declaration, its triggering signature, and the response, so repeated non-convergence in a class becomes visible to threshold recalibration.

**Required Outputs**:

- A non-convergence record naming the triggering signature and its measured values.
- A state-hash set for the run, with any repetition flagged.
- Exactly 1 issued response drawn from reformulate, change route, or terminate unresolved.

**Quality Checkpoints**:

- Remaining budget is never accepted as a justification for a further iteration; a continuation citing budget alone is rejected.
- An identical query is never reissued against an identical route after an identical failure.
- Exactly 1 response is issued per declaration; zero responses or multiple responses halt the loop as a control defect.
- Termination as unresolved propagates to the sufficiency predicate rather than being silently absorbed.

***

### Phase 4: Query Reformulation Under a Reformulation Bound

**Objective**: Convert a diagnosed retrieval failure into exactly one bounded query change, and stop reformulating once the declared variant ceiling is reached.

#### Step 4.1: Diagnose the Retrieval Failure Class

**Required Actions**:

- Classify the failure into exactly 1 named class: vocabulary mismatch, over-broad query, over-narrow query, wrong source class, wrong time window, wrong entity resolution, missing filter, or corpus absence.
- Distinguish corpus absence, where no eligible route holds the evidence, from query defect, where the evidence exists but the query does not reach it.
- Support the classification with observable evidence from the iteration, such as candidate counts, rejection classes, rank distributions, or span mismatch patterns.
- Terminate the sub-question as unresolved where the class is corpus absence, since reformulation cannot retrieve evidence a corpus does not hold.
- Record the diagnosis before any reformulation is proposed, so an undiagnosed rewrite cannot be issued.

**Required Outputs**:

- A failure class assignment with its supporting observations.
- A corpus-absence verdict where applicable, terminating the sub-question.
- A diagnosis record linked to the iteration that produced the failure.

**Quality Checkpoints**:

- Exactly 1 failure class is assigned; an unassigned or multiply-assigned failure blocks reformulation.
- A reformulation issued without a recorded diagnosis is rejected and does not consume a variant slot, because it must not be issued at all.
- Corpus absence terminates the sub-question rather than consuming remaining variants against an empty corpus.

***

#### Step 4.2: Apply Exactly One Bounded Reformulation

**Required Actions**:

- Apply the single change the diagnosis licenses: a faithful lexical rewrite for vocabulary mismatch, a narrowing filter for over-broad results, a relaxed filter for over-narrow results, a corrected time window, a corrected entity form, or a decomposition into a narrower sub-question.
- Preserve every constraint the sub-question carries, since a reformulation that drops a jurisdiction, a date bound, or a negation retrieves evidence for a different question.
- Reject a reformulation whose canonical digest matches a variant already dispatched for the sub-question and route.
- Increment the variant counter for the sub-question, counting the original query as variant 1.
- Record the expected gain the reformulation targets, so its realised gain can be compared against the expectation at the next progress test.

**Required Outputs**:

- One reformulated query with its licensing diagnosis and the single change applied.
- A constraint-preservation verdict comparing the reformulated query against the sub-question's constraints.
- An updated variant counter and a recorded expected gain.

**Quality Checkpoints**:

- Exactly 1 change is applied per reformulation; a rewrite changing several dimensions at once destroys attribution of the resulting gain.
- Constraint preservation passes on every dimension the sub-question declares; a dropped constraint rejects the reformulation.
- The variant counter is incremented by the deterministic tier and cannot be reset by any model output.

***

#### Step 4.3: Enforce the Reformulation Ceiling

**Required Actions**:

- Block any further reformulation once the sub-question has dispatched 3 query variants inclusive of the original.
- Permit exactly 1 route change per sub-question after the variant ceiling is reached, drawn from the eligible route list and excluding rejected routes.
- Reset the variant counter to 1 on a route change, since a different corpus admits a different vocabulary, and record the reset with its licensing route change.
- Terminate the sub-question as unresolved once both the variant ceiling and the route-change allowance are exhausted.
- Record every ceiling enforcement with its measured counters, so ceiling breaches attempted by the model tier are visible in the trace.

**Required Outputs**:

- A ceiling enforcement record per sub-question carrying variant count, route changes used, and the enforcement verdict.
- An unresolved termination record where both allowances are exhausted.
- A reset record where a route change reset the variant counter.

**Quality Checkpoints**:

- Variant count per route does not exceed 3; a fourth variant is rejected deterministically.
- Route changes per sub-question do not exceed 1 by default; a second route change requires an explicit contract amendment recorded before the run.
- Exhaustion of both allowances produces an unresolved termination, never a further attempt under a renamed query.

***

### Phase 5: Evidence Sufficiency and the Stopping Rule

**Objective**: Evaluate a checkable sufficiency condition over the evidence ledger and terminate the loop through exactly one of three declared outcomes: convergence, budget exhaustion, or declared abstention.

#### Step 5.1: Evaluate the Sufficiency Predicate

**Required Actions**:

- Evaluate sufficiency as a predicate over the evidence ledger, not as a confidence report: every required sub-question carries at least 1 admitted evidence span meeting its declared authority tier and freshness bound; every material claim the answer form obliges maps to at least 1 admitted span; no material claim rests on evidence marked contradicted and unresolved; and the join rule for every dependency is satisfied by resolved values.
- Compute a sufficiency score as the proportion of required sub-questions meeting all four conditions, and record it per iteration.
- Treat a sub-question terminated as unresolved as failing the predicate, and propagate that failure to the run rather than substituting a weaker source.
- Reject any sufficiency verdict expressed as a scalar confidence, a judge score, or a model assertion of adequacy, since none is checkable against the ledger.
- Record which conditions failed and for which sub-questions, so the next transition is diagnosed rather than guessed.

**Sufficiency Conditions and Their Checks**:

| Condition | Deterministic check | Failure consequence |
| :-- | :-- | :-- |
| Span coverage | Every required sub-question has at least 1 admitted span | Sub-question returns to Phase 3 or terminates unresolved |
| Claim support | Every material claim maps to at least 1 span | Claim removed, narrowed, or retrieved again |
| Contradiction closure | No material claim rests on unresolved contradiction | Conflict handling, then abstention if unresolved |
| Join satisfaction | Every declared join resolves on admitted values | Dependent sub-question marked unresolved |
| Authority and freshness | Every span meets its declared tier and bound | Span rejected, coverage recomputed |

**Required Outputs**:

- A sufficiency verdict of satisfied or unsatisfied, with per-condition results.
- A sufficiency score expressed as a proportion of required sub-questions.
- A failed-condition list naming the sub-questions and claims responsible.

**Quality Checkpoints**:

- The verdict is derived from ledger checks; a verdict asserted without per-condition results is rejected.
- An unresolved sub-question never satisfies the predicate, so silent substitution of a weaker source is detectable.
- The sufficiency score is recorded per iteration, so a score unchanged across 2 iterations triggers the non-convergence signature in Step 3.3.

***

#### Step 5.2: Issue Exactly One Loop Transition

**Required Actions**:

- Issue exactly 1 transition per evaluation, drawn from continue, reformulate, change route, synthesize, escalate, or abstain.
- Admit continue only where the sufficiency predicate is unsatisfied, the last iteration was productive, the iteration bound is not exhausted, no non-convergence signature is active, and the remaining budget exceeds the verification reserve.
- Refuse a model-proposed continue that fails any admission condition, and substitute the mandatory response from Step 3.3, since the deterministic controller holds authority on disagreement.
- Issue synthesize where the sufficiency predicate is satisfied, and escalate where an approval gate, a policy ambiguity, an authoritative contradiction, or a suspected integrity failure blocks progress.
- Record the transition, its triggering condition, the measured counters, and the refusal where a proposal was overridden.

**Required Outputs**:

- Exactly 1 issued transition with its triggering condition named.
- A refusal record where a model-proposed continuation was rejected, naming the failed admission condition.
- An updated control record carrying iteration counts, variant counts, gain figures, and remaining budget.

**Quality Checkpoints**:

- Exactly 1 transition is issued per evaluation; zero or multiple transitions halt the loop as a control defect.
- Every continue satisfies all 5 admission conditions; a continue admitted on fewer is a defect regardless of outcome quality.
- Refusals are recorded rather than silently applied, so the frequency of model-controller disagreement is measurable.

***

#### Step 5.3: Execute a Declared Termination

**Required Actions**:

- Terminate on convergence where the sufficiency predicate is satisfied, and pass the accepted evidence ledger to synthesis.
- Terminate on budget exhaustion where any ceiling is reached before sufficiency, and emit a declared abstention carrying the supported partial result rather than an unsupported answer.
- Terminate on declared abstention where required evidence is unavailable, prohibited, stale beyond policy, or contradicted without resolution after the bounds are exhausted.
- Compose the abstention record to state what is known with citations, what remains unknown, what was attempted with its counters, and what capability or source would be required.
- Record the termination reason from a closed vocabulary, and never record exhaustion as convergence.

**Required Outputs**:

- A termination record naming exactly 1 of convergence, budget exhaustion, or declared abstention.
- An accepted evidence ledger where the outcome is convergence.
- An abstention record carrying known, unknown, attempted, and required, where the outcome is abstention or exhaustion.

**Quality Checkpoints**:

- The termination reason comes from the closed vocabulary; an uncategorised termination halts release.
- Budget exhaustion never produces a synthesised answer for unsupported claims; the supported subset is emitted instead.
- The abstention record names the specific missing capability or source, so the gap is actionable rather than a refusal.
- Convergence is recorded only where the sufficiency predicate returned satisfied on all conditions.

***

### Phase 6: Answer Synthesis With Citation Verification

**Objective**: Produce an answer whose every material claim resolves to an admitted span, and verify that resolution deterministically before release.

#### Step 6.1: Synthesize Only From the Accepted Evidence Ledger

**Required Actions**:

- Build the answer outline from the required sub-questions and their resolved joins, so structure follows coverage rather than fluency.
- Generate only claims that map to an evidence identifier, or that are explicitly labelled as analysis derived from named cited facts.
- Attach citations during drafting, binding each material claim to its evidence identifier and exact span at the point of generation.
- Keep source wording, agent inference, and residual uncertainty typographically and structurally distinct in the output.
- State every unresolved sub-question explicitly in the output rather than bridging it with a transition, since an omitted gap is indistinguishable from a covered one.

**Required Outputs**:

- A draft in which every material claim carries an evidence identifier and span reference.
- A claim inventory labelling each claim as material, non-material, analysis, or recommendation.
- An explicit unresolved-items statement listing every sub-question terminated unresolved.

**Quality Checkpoints**:

- No material claim lacks an evidence identifier; an unbound claim is removed or narrowed before verification.
- Analysis is labelled as analysis and names the cited facts it derives from.
- Unresolved sub-questions appear in the output; their omission is a defect even where the remaining answer is correct.

***

#### Step 6.2: Verify Citations Against Exact Source Spans

**Required Actions**:

- Atomise the draft into claims and verify each material claim against its cited span by deterministic string or structural comparison, not by a model judgement of plausibility.
- Verify that every cited source identifier resolves, that its recorded title and date match the ledger entry, and that the span still occurs in the source content hash recorded at retrieval.
- Check uncited factual claims across the whole answer, since citation presence is not proof of support and absence of a citation is not proof of an unsupported claim being absent.
- Repair only affected claims on failure, and re-enter retrieval only for an identified evidence gap and only where the retrieval budget outside the verification reserve remains.
- Bound verification at 2 rounds and 1 retrieval re-entry charged to the relevant sub-question, and abstain on any required material claim still unsupported.

**Required Outputs**:

- A citation verification report with a per-claim support verdict and a per-source resolution verdict.
- A repair record naming each claim changed and the gap that licensed the change.
- A release verdict of pass, partial with qualified claims, or abstain.

**Quality Checkpoints**:

- Span matching is performed deterministically; a model assertion of support never substitutes for the comparison.
- Citation precision across material claims is at least 0.95; below that threshold the release verdict is partial or abstain, never pass.
- Verification rounds do not exceed 2; a third round is refused and the run abstains on the remaining unsupported claims.
- A higher judge score with no newly supported claim counts as zero gain and does not license a further verification round.

***

### Phase 7: Loop Instrumentation and Convergence Metrics

**Objective**: Record every control decision with the counters that produced it, compute the convergence metric set, and recalibrate the bounds from observed gain curves rather than from assumption.

#### Step 7.1: Record the Per-Iteration Control Record

**Required Actions**:

- Write one append-only record per iteration carrying run identifier, trace identifier, sub-question identifier, iteration index, canonical query digest, route, filters, and state hash.
- Record the progress figures alongside them: evidence-gain delta, novel-evidence ratio, duplicate ratio, newly covered sub-questions, newly supported claims, and contradiction delta.
- Record the control figures: iteration counter, variant counter, route changes used, budget consumed against ceiling per dimension, remaining verification reserve, transition issued, and any refusal of a model-proposed continuation.
- Record decision metadata and evidence provenance only; do not require, request, or persist hidden reasoning traces, and replace raw sensitive payloads with hashes or content references.
- Record the termination record once per run, carrying the closed-vocabulary reason, the final sufficiency score, and the counters at termination.

**Iteration Control Record Template**:

```
RUN_ID:
TRACE_ID:
SUBQUESTION_ID:
ITERATION_INDEX:
CANONICAL_QUERY_DIGEST:
ROUTE:
STATE_HASH:
EVIDENCE_GAIN_DELTA:
NOVEL_EVIDENCE_RATIO:
PRODUCTIVE_VERDICT:
VARIANT_COUNT:
ROUTE_CHANGES_USED:
BUDGET_CONSUMED_VS_CEILING:
VERIFICATION_RESERVE_REMAINING:
PROPOSED_TRANSITION:
ISSUED_TRANSITION:
REFUSAL_REASON:
```

**Required Outputs**:

- An append-only iteration log with one complete record per iteration.
- A run-level termination record with the closed-vocabulary reason and final counters.
- A disclosure verdict confirming no hidden reasoning trace was persisted.

**Quality Checkpoints**:

- Every iteration has exactly 1 record; a missing record makes the run unauditable and blocks release.
- Every record carries both the proposed and the issued transition, so controller refusals are countable.
- No record contains a hidden reasoning trace or an unhashed sensitive payload; a breach halts log release.

***

#### Step 7.2: Compute the Convergence Metric Set

**Required Actions**:

- Compute convergence rate as the proportion of runs terminating on satisfied sufficiency before the iteration ceiling, and report median and ninety-fifth-percentile iteration counts alongside it.
- Compute the gain curve by iteration index, so the iteration at which marginal gain falls below the floor is observable rather than assumed.
- Compute non-convergence rate, repeated-state rate, oscillation rate, reformulation exhaustion rate, and refused-continuation rate.
- Compute over-retrieval waste as the proportion of iterations recorded unproductive, and gate waste as the proportion of runs where retrieval was invoked but every material claim already had a context span.
- Compute cost per grounded answer, cost per newly solved baseline failure, and time to first admitted evidence, separating parallel compute cost from user-visible wall time.

**Required Outputs**:

- A convergence metric report covering rate, iteration distribution, and gain curve.
- A loop-pathology report covering non-convergence, repetition, oscillation, and refusal rates.
- An efficiency report covering waste, cost per grounded answer, and latency percentiles.

**Quality Checkpoints**:

- Every metric is computed from the iteration log rather than estimated from sampled runs.
- The gain curve is reported by iteration index, so a bound set above the point of diminishing return is visible.
- Waste metrics are reported alongside quality metrics, so an accuracy gain purchased by unbounded retrieval is not reported as an improvement.

***

#### Step 7.3: Recalibrate the Bounds From Observed Gain

**Required Actions**:

- Set the iteration bound per task class to the iteration index beyond which the observed gain curve contributes less than 5 percent of total realised gain.
- Set the novel-evidence floor per task class to the value separating productive from unproductive iterations in the observed distribution, and record the measured separation rather than reusing the default.
- Set the reformulation ceiling per task class from the observed variant index at which reformulations stop producing gain.
- Re-derive every bound whenever the corpus, the retrieval service, the model version, or the task mix changes, since a bound calibrated against a different retrieval surface is not transferable.
- Version each bound set, evaluate it on held-out runs, and record the comparison against the previous set before promotion.

**Required Outputs**:

- A per-task-class bound set carrying iteration bound, novel-evidence floor, and reformulation ceiling with their supporting measurements.
- A version record linking each bound set to the corpus, service, and model versions it was derived against.
- A held-out comparison report supporting or rejecting promotion.

**Quality Checkpoints**:

- No bound is promoted without a held-out comparison; a bound tuned on the runs that produced it is not evidence.
- Every promoted bound names the corpus, retrieval service, and model version it was derived against.
- Defaults remain in force for a task class until a measured replacement passes the comparison, so an unmeasured class is never unbounded.

***

## III. Implementation Guidance for AI Agents

AI agents operating a bounded retrieval loop must follow systematic protocols ensuring that every iteration is counted, every continuation is licensed by measured gain, and every termination is declared rather than reached by exhaustion. The following guidance translates the control loop into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Gate Agent**: Executes the retrieve-or-answer decision within 2 percent of the run budget and returns answer-from-context, retrieve, or abstain. It may suppress the loop entirely and owns the unsupported-claim list.
2. **Planner Agent**: Decomposes the goal into bounded sub-questions, binds each to an eligible route list, and proposes plan revisions. It may not exceed 8 required sub-questions or 2 plan revisions.
3. **Retriever Agent**: Issues exactly 1 retrieval action per iteration and labels candidate relevance. It may not change route, reset a counter, or admit an unvalidated item.
4. **Loop Controller**: Owns iteration counters, variant counters, canonical query digests, state hashes, the budget ledger, and the stopping rule. It alone issues transitions and alone may refuse a proposed continuation. It is deterministic software, not a model call.
5. **Sufficiency Assessor**: Applies support labels per claim and per sub-question against the ledger. It reports labels, never a global adequacy verdict, and never issues a transition.
6. **Synthesizer Agent**: Composes the answer from the accepted evidence ledger only, binding citations during drafting.
7. **Verification Agent**: Resolves citations against exact spans deterministically, checks uncited claims, and returns pass, partial, or abstain.

**Authority Rule**: The Loop Controller holds authority over every other component on any question of continuation, bound, counter, or termination. A model-tier component may propose a continuation, request a reformulation, or recommend a route change; only the Loop Controller admits it. Where a model-tier component and the Loop Controller disagree, the Loop Controller's verdict executes and the disagreement is logged as a refusal.

**Workflow Execution Pattern**:

```
STATE: Iteration_Decision
INPUTS:
  1. Progress record from Step 3.2
  2. Iteration and variant counters from the Loop Controller
  3. Sufficiency verdict from Step 5.1
  4. Budget ledger with remaining verification reserve
ACTIONS:
  1. Recompute state hash and compare against the run's hash set
  2. Evaluate the five non-convergence signatures
  3. Evaluate the five continue admission conditions
  4. Select exactly one transition
VALIDATION:
  - issued_transition_count == 1
  - iterations_used < iteration_bound
  - variants_used <= variant_ceiling
  - state_hash NOT IN recorded_hash_set
  - evidence_gain_delta >= 1 OR transition != CONTINUE
  - novel_evidence_ratio >= 0.30 OR transition != CONTINUE
  - remaining_budget > verification_reserve
  - reasoning_trace_persisted == FALSE
TRANSITIONS:
  IF transition == CONTINUE THEN next_state = Retrieval_Iteration
  IF transition IN {REFORMULATE, CHANGE_ROUTE} THEN next_state = Reformulation
  IF transition == SYNTHESIZE THEN next_state = Answer_Synthesis
  IF transition == ESCALATE THEN next_state = Await_Human_Response
  IF transition == ABSTAIN THEN next_state = Declared_Termination
  IF validation_failed THEN next_state = Loop_Error_Handling
```

**Two-Phase Action Pattern**: Emit the proposed transition with its trigger, counters, and expected gain without executing it; validate it against the block above while no budget is committed; commit it only after validation passes, debiting the counter and the reserved budget in the same operation.

**Approval Gate**: Human authorisation is required before any raise of an iteration bound, variant ceiling, or budget ceiling; before release of an answer in the highest risk tier carrying any claim with citation precision below 0.95; before any retrieval that would send restricted content to an external destination; and before any run exceeding 150 percent of the task class's median iteration count. Agents halt at these gates rather than proceeding with a recorded warning. An approved extension records a new ceiling with its approver, scope, and expiry; it never mutates the original ceiling in place.

**Context Management Requirements**:

- Hold the run contract, budget ledger, iteration counters, state-hash set, and evidence ledger in durable state outside the model context, since the loop may outlive a single context window.
- Cap admitted evidence at 50 percent of the usable context, and replace superseded observations with evidence pointers and verified summaries rather than accumulating raw text.
- Preserve exact source spans outside the model context and rehydrate only the spans the next decision requires.
- Write a handoff record at every context boundary naming contract, counters, ledger state, unresolved sub-questions, and the next transition.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Gate and Contract Integrity (After Phase 1)**

- **Automated Check**: Every budget dimension carries a numeric ceiling; the verification reserve is subtracted from the retrieval budget; the gate verdict names a condition from Section 1.3; gate cost is at most 2 percent of the run budget; a baseline failure class is recorded where the loop is entered.
- **Agent Action on Pass**: Proceed to planning.
- **Agent Action on Failure**: Halt before the first iteration; no retrieval is spent against an incomplete contract.
- **Human Review Trigger**: Loop entry proposed without a recorded baseline failure, or a task in the highest risk tier.

**Checkpoint 2: Plan Validity (After Phase 2)**

- **Automated Check**: Required sub-questions number 1 to 8; every unsupported claim maps to at least 1 sub-question; dependencies are acyclic; allocated budgets plus reserve sum to no more than 100 percent per dimension; every required sub-question has at least 1 eligible route.
- **Agent Action on Pass**: Proceed to the retrieval loop.
- **Agent Action on Failure**: Revise the diagnosed defect only, counting the revision against the ceiling of 2.
- **Human Review Trigger**: A third plan revision required, or a required sub-question with no eligible route.

**Checkpoint 3: Iteration Integrity (Every Iteration in Phase 3)**

- **Automated Check**: The canonical query digest is new for its route; the iteration counter was debited before dispatch; every admitted item carries an exact span; a progress record exists carrying gain delta and novel-evidence ratio.
- **Agent Action on Pass**: Proceed to the transition decision.
- **Agent Action on Failure**: Reject the dispatch or quarantine the admission; a missing progress record halts the loop.
- **Human Review Trigger**: More than 20 percent of iterations in a run rejected for digest repetition.

**Checkpoint 4: Reformulation Bound (After Phase 4)**

- **Automated Check**: Every reformulation carries a recorded diagnosis and applies exactly 1 change; constraint preservation passes on every declared dimension; variant count per route is at most 3; route changes per sub-question are at most 1.
- **Agent Action on Pass**: Return to the retrieval loop with the reformulated query.
- **Agent Action on Failure**: Refuse the reformulation and terminate the sub-question as unresolved.
- **Human Review Trigger**: More than 30 percent of required sub-questions exhausting both the variant ceiling and the route allowance.

**Checkpoint 5: Termination Validity (After Phase 5)**

- **Automated Check**: Exactly 1 transition issued; the termination reason comes from the closed vocabulary; convergence is recorded only where every sufficiency condition passed; budget exhaustion produced an abstention record rather than a synthesised answer.
- **Agent Action on Pass**: Proceed to synthesis or close the run on the declared outcome.
- **Agent Action on Failure**: Halt the run; an invalid termination is never released with a warning attached.
- **Human Review Trigger**: Exhaustion terminations exceeding 25 percent of runs in a task class.

**Checkpoint 6: Citation and Release Integrity (After Phase 6)**

- **Automated Check**: Every material claim resolves to an admitted span by deterministic comparison; citation precision across material claims is at least 0.95; every cited source resolves and matches its ledger entry; unresolved sub-questions appear in the output.
- **Agent Action on Pass**: Release under the recorded verdict.
- **Agent Action on Failure**: Downgrade the verdict to partial or abstain and name the unsupported claims.
- **Human Review Trigger**: Any required material claim unsupported after 2 verification rounds.

**Checkpoint 7: Instrumentation Completeness (After Phase 7)**

- **Automated Check**: One complete record per iteration; both proposed and issued transitions recorded; no hidden reasoning trace persisted; convergence and waste metrics computed from the log.
- **Agent Action on Pass**: Release the metric report and permit bound recalibration.
- **Agent Action on Failure**: Withhold the report and name the missing records; no bound is promoted on an incomplete log.
- **Human Review Trigger**: Any disclosure breach, or a refused-continuation rate above 40 percent indicating the model tier is systematically proposing unlicensed iterations.

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

**Error Type 1: Non-Converging Retrieval Loop**

- **Symptoms**: Evidence-gain delta of 0 across consecutive iterations; novel-evidence ratio below the floor; sufficiency score flat; budget draining while the ledger stops growing.
- **Diagnostic Steps**: Recompute gain from ledger deltas rather than from the model's report; determine whether the cause is corpus absence, query defect, or route exhaustion by comparing candidate counts and rejection classes across the iterations.
- **Resolution Protocol**: Option A, issue 1 diagnosed reformulation where the variant ceiling permits it. Option B, change to an unrejected eligible route and reset the variant counter. Option C, terminate the sub-question as unresolved and propagate the failure to the sufficiency predicate. Option D, terminate the run through a declared abstention where the sub-question is required and no option remains.
- **Escalation Trigger**: Non-convergence declared on more than 50 percent of required sub-questions in a run escalates for plan review. This class is never resolved by a further iteration on the same route, regardless of remaining budget.

**Error Type 2: Query Repetition and Oscillation**

- **Symptoms**: A canonical query digest recurs for the same route; 2 query variants alternate across iterations; the state hash matches a recorded hash; route selection alternates without an intervening gain.
- **Diagnostic Steps**: Compare the rejected digest against the dispatch log to confirm exact repetition; determine whether the alternation follows a diagnosis or is undiagnosed churn.
- **Resolution Protocol**: Option A, reject the dispatch deterministically and require a diagnosis before any further variant. Option B, freeze the sub-question's route to the highest-authority eligible entry for the remainder of the run. Option C, terminate the sub-question as unresolved where both variants have been exhausted.
- **Escalation Trigger**: A third repetition rejection on one sub-question terminates that sub-question; an identical query is never reissued after an identical failure.

**Error Type 3: Unwarranted Retrieval**

- **Symptoms**: Retrieval invoked where every material claim already carried a context span; answer quality falling after retrieval; distractor spans outranking held evidence; gate cost recorded as zero.
- **Diagnostic Steps**: Replay the gate against the supplied context and recompute the unsupported-claim list; compare answer quality with and without the retrieved material on the frozen baseline.
- **Resolution Protocol**: Option A, tighten the gate by requiring an explicit unsupported-claim list before retrieval is authorised. Option B, route the task class to single-pass retrieval or to direct answering. Option C, cap admitted evidence for the class so distractors cannot displace held context.
- **Escalation Trigger**: Gate waste above 15 percent of runs in a task class suspends the loop for that class pending gate recalibration.

**Error Type 4: Sufficiency Asserted Without Evidence**

- **Symptoms**: A satisfied verdict with unresolved sub-questions; a scalar confidence submitted in place of per-condition results; material claims mapping to spans that fail resolution at verification.
- **Diagnostic Steps**: Recompute the predicate from the ledger; identify which condition the asserted verdict skipped; check whether the failing spans were admitted without validation.
- **Resolution Protocol**: Option A, reject the verdict and recompute deterministically from the ledger. Option B, quarantine the unvalidated admissions and recompute coverage. Option C, downgrade the release verdict to partial and qualify the affected claims. Option D, abstain where a required material claim remains unsupported.
- **Escalation Trigger**: Any required high-risk claim released on an asserted rather than computed verdict is a release defect and halts the run; this class is never resolved by a further model judgement.

**Error Type 5: Budget Exhaustion Before Sufficiency**

- **Symptoms**: A ceiling reached with the predicate unsatisfied; remaining time below the verification reserve; iteration counts above the task class ninety-fifth percentile.
- **Diagnostic Steps**: Attribute consumption across gate, planning, retrieval, reformulation, and verification; determine whether the overrun arose from too many sub-questions, too many variants, or an oversized iteration bound.
- **Resolution Protocol**: Option A, emit the supported partial result with an explicit unresolved list. Option B, emit a declared abstention naming the missing evidence and the capability required. Option C, request an authorised ceiling extension recording a new ceiling with approver, scope, and expiry.
- **Escalation Trigger**: Exhaustion terminations above 25 percent of runs in a class escalate for bound recalibration. Synthesising an unsupported answer under exhaustion is prohibited without exception.

**Error Type 6: Untrusted Content Steering the Loop**

- **Symptoms**: Retrieved text or tool metadata carrying instructions; a proposed query containing restricted content; a proposed route to an undeclared destination; a proposal to raise a ceiling originating from retrieved material.
- **Diagnostic Steps**: Trace the proposal to its originating span; check the injection verdict recorded at admission; confirm whether the destination and scope appear in the approved registry.
- **Resolution Protocol**: Option A, quarantine the span, remove it from the ledger, and recompute coverage without it. Option B, reject the proposed action and hold the route to the approved registry entry. Option C, halt the run and escalate where credentials, cross-tenant content, or an egress attempt is implicated.
- **Escalation Trigger**: Any confirmed instruction-following from retrieved content, any restricted content in an outbound query, and any ceiling-raise proposal originating outside the approval path halt the run immediately.

**Troubleshooting Decision Tree**:

```
LOOP CONTROLLER DETECTS A PROBLEM
├─ PROGRESS DEFECT
│   ├─ Gain zero for two iterations → Declare non-convergence; reformulate, reroute, or terminate
│   ├─ Novel-evidence ratio below floor → Flag route exhausted; change route or terminate
│   └─ Sufficiency score flat across two iterations → Terminate sub-question as unresolved
├─ REPETITION DEFECT
│   ├─ Canonical query digest repeats → Reject dispatch; require a diagnosis first
│   ├─ State hash repeats → Block further iteration on this route
│   └─ Variants alternate without gain → Freeze route; consume no further variants
├─ BOUND DEFECT
│   ├─ Iteration bound reached → Terminate; never continue on remaining budget
│   ├─ Variant ceiling reached → Permit one route change; then terminate unresolved
│   └─ Model proposes a ceiling raise → REFUSE; route to the approval gate
├─ SUFFICIENCY DEFECT
│   ├─ Verdict asserted without per-condition results → Recompute from the ledger
│   ├─ Required sub-question unresolved → Predicate fails; abstain or emit partial
│   └─ Span fails deterministic resolution → Quarantine; recompute coverage
├─ BUDGET DEFECT
│   ├─ Reserve breached → Stop retrieval; spend only on verification and response
│   └─ Ceiling reached before sufficiency → Declared abstention; never a synthesised guess
└─ TRUST DEFECT
    ├─ Instruction found in retrieved span → Quarantine; recompute without it
    └─ Restricted content in outbound query → HALT; escalate to the named authority
```

### D. Performance Metrics and Continuous Learning

**Convergence and Control Metrics**:

- **Convergence rate**: Runs terminating on satisfied sufficiency before the iteration ceiling (target: at least 85 percent, with median and ninety-fifth-percentile iteration counts reported alongside).
- **Iterations per grounded answer**: Retrieval iterations consumed per released answer meeting the citation threshold (target: at or below the task class median, with the gain curve reported).
- **Non-convergence rate**: Runs in which a non-convergence signature fired at least once (target: no more than 20 percent; above 35 percent indicates the iteration bound exceeds the point of diminishing return).
- **Refused-continuation rate**: Model-proposed continuations refused by the controller (target: no more than 20 percent; above 40 percent indicates the model tier is systematically proposing unlicensed iterations).
- **Repeated-state rate**: Iterations rejected for digest or state-hash repetition (target: no more than 5 percent).
- **Abstention precision**: Declared abstentions confirmed correct under later adjudication (target: at least 90 percent).

**Evidence and Answer Metrics**:

- **Citation precision on material claims**: Material claims whose cited span resolves and supports them (target: at least 0.95; below this the release verdict is partial or abstain).
- **Required coverage**: Required sub-questions carrying at least 1 admitted span meeting authority and freshness (target: 100 percent for a convergence termination).
- **Novel-evidence ratio at termination**: Ratio on the final productive iteration (target: reported, not optimised, since a high value at termination indicates the bound stopped a still-productive loop).
- **Unsupported-claim leakage**: Released material claims failing deterministic span resolution (target: 0; any occurrence halts release).

**Efficiency and Waste Metrics**:

- **Over-retrieval waste**: Iterations recorded unproductive over total iterations (target: no more than 25 percent).
- **Gate waste**: Runs invoking retrieval where every material claim already had a context span (target: no more than 5 percent).
- **Cost per grounded answer**: Total run cost over released answers meeting the citation threshold (target: below the frozen baseline at matched quality).
- **Time to first admitted evidence**: Elapsed time from gate verdict to the first ledger admission (target: reported by route, since a slow first admission predicts exhaustion terminations).

**Log-Pattern Failure Detection**: A recurring canonical query digest indicates a repetition loop. Rising cost with a flat ledger indicates over-retrieval. Alternating variants without gain indicates reformulation churn. A satisfied verdict alongside unresolved sub-questions indicates asserted rather than computed sufficiency. High refused-continuation rates indicate a model tier calibrated to continue by default. Exhaustion terminations concentrated in one task class indicate a bound set against the wrong retrieval surface.

**Learning and Adaptation Mechanisms**:

- **Gain-curve calibration**: Recompute each iteration bound from the observed gain curve per task class, rather than reusing the deployment default.
- **Failure-class memory**: Retain the diagnosis, the reformulation applied, and its realised gain per sub-question class, so reformulation selection improves against observed history.
- **Frozen regression cases**: Convert every non-convergence, exhaustion, and unsupported-claim leakage into a frozen case with its expected control behaviour and its observable signal.
- **Bound versioning**: Version every bound set against the corpus, retrieval service, and model version it was derived from, and evaluate a new set on held-out runs before promotion.

**Human-in-the-Loop Boundaries**: Raising an iteration bound, variant ceiling, or budget ceiling; releasing an answer in the highest risk tier whose citation precision falls below 0.95; authorising an outbound query carrying restricted content; and converting a declared abstention into a released answer are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs when evidence acquisition continues and when it stops, not what the evidence is about. Its phases hold wherever a question admits more than one retrieval route, produces observable intermediate evidence, and carries a cost for continuing.

### 4.1 Cross-Domain Application Patterns

**Regulatory and compliance research**: The gate returns retrieve because obligations depend on jurisdiction and effective date, neither of which is in supplied context. The plan decomposes into jurisdiction, instrument, effective date, and exemption sub-questions with an explicit jurisdiction join. Authority tiers are strict: an official register outranks a commentary summary, and a commentary span never satisfies a sub-question whose declared tier is primary. The loop typically converges in 2 to 4 iterations, and the stopping rule fires on convergence. Where an instrument is withdrawn or superseded without a replacement, the sub-question terminates unresolved and the run abstains rather than citing the superseded text, because a plausible compliance answer is more damaging than a declared gap.

**Clinical and scientific evidence synthesis**: Sub-questions carry population, intervention, comparator, and outcome constraints that a reformulation must preserve, since a rewrite that relaxes the comparator retrieves evidence for a different question. Contradiction closure dominates the sufficiency predicate: two admitted spans disagreeing on an effect direction block satisfaction until a superseding source, a methodological distinction, or an explicit both-hold statement resolves them. The reformulation bound binds tightly here because vocabulary variation is wide, so the route change to a structured index is often more productive than a third free-text variant.

**Software incident investigation**: Evidence lives in logs, traces, configuration, and change records rather than documents, so routes are heterogeneous and the exact system of record usually outranks search. The loop is short and the iteration bound is low, because an incident's cost of delay is high and the answer is usually reachable in 1 to 3 iterations against the right route. Non-convergence here most often signals corpus absence, since a signal that was never emitted cannot be retrieved, and the correct response is termination as unresolved with the missing instrumentation named.

**Financial due diligence**: Entity resolution dominates: a reformulation correcting an entity form is the single most productive change class, and an unresolved entity contaminates every downstream join. Authority and freshness bind together, since a filing superseded by a later filing fails the freshness bound even where its span supports the claim. Budget exhaustion is common because the corpus is large, so the verification reserve is set higher than the default and the abstention record names the specific filing or period that could not be reached.

**Customer and product support**: Most traffic is answerable from supplied context or from a single-pass retrieval, so the gate suppresses the loop on the majority of requests and the loop is reserved for the hard tail. Gate waste is the metric that matters most in this domain, because invoking a multi-iteration loop for a question the documentation already answers multiplies latency for no gain. Bounds are tight, typically 2 iterations, and the release verdict on failure is an escalation to a human rather than an abstention.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk reversible questions**: Collapse the loop to 1 iteration per sub-question and 2 query variants, retaining the gate, the progress test, and the termination vocabulary. Where over-retrieval waste exceeds 25 percent in this class, the gate should have suppressed the loop.
- **High-risk or irreversible decisions**: Retain every phase, raise the citation precision threshold to 1.00 on required material claims, require an independent verification route for each such claim, and prefer abstention over a partial release. Bounds are not relaxed for importance; a higher-stakes question receives a stricter sufficiency predicate, not more iterations.
- **Strict latency budgets**: Reduce the iteration bound rather than removing the progress test, since removing the test removes control while reducing the bound raises its frequency of enforcement. Where latency forbids any iteration beyond the first, the gate routes to single-pass retrieval with a declared fallback.
- **Large heterogeneous corpora**: Raise the route count per sub-question rather than the iteration bound, because a second route usually yields more than a third variant on an exhausted route. Track duplicate-evidence ratio per route to detect route exhaustion early.
- **Long-horizon research runs**: Persist contract, counters, ledger, and state-hash set outside working context, write a handoff record at every context boundary, and re-evaluate the sufficiency predicate at each handoff so coverage drift is detected rather than inherited.
- **Multi-agent deployments**: Assign the Loop Controller to deterministic software distinct from every model-tier component, deduplicate normalised sub-questions before dispatch, and cap concurrent branches at 3 by default. Agreement among branches sharing a route and a base model is not independent corroboration and does not satisfy contradiction closure.

***

## V. Limitations and Considerations

**The bounds stated here are deployment defaults, not measured findings**: The iteration bound of 2 per sub-question and 12 per run, the variant ceiling of 3, the novel-evidence floor of 0.30, the reserve of 20 percent, the citation precision threshold of 0.95, and the sub-question cap of 8 were chosen to be operable on first deployment. They are not derived from a universal property of retrieval systems. The mitigation is Step 7.3, which obliges each deployment to recompute every bound from its own observed gain curves and to keep the default in force only until a measured replacement passes a held-out comparison.

**A deterministic gain test approximates a learned stopping policy imperfectly**: Research controllers estimate whether continuing will help by learning a value function over trajectories, which looks forward; the progress test specified here looks backward at realised gain. A backward test stops a loop that would have paid off on the next iteration, and continues a loop whose next iteration is worthless but whose last one was productive. The mitigation is the gain curve in Step 7.2, which makes both error directions measurable per task class, and the bound recalibration that shifts the ceiling toward the observed point of diminishing return.

**Evidence gain is a proxy for answer improvement**: Newly admitted spans can raise the gain delta without improving the answer, and a single decisive span can settle a question while scoring the same as a redundant one. The metric counts admissions, not their value. The mitigation is the sufficiency predicate, which gates termination on coverage and support rather than on accumulated gain, so a high-gain run with unresolved required sub-questions still cannot converge.

**Sufficiency checking inherits the labeller's blind spots**: The predicate is deterministic, but the support labels it consumes are produced by a model that shares the generator's failure modes. A claim the labeller misreads as supported passes the predicate and fails only at deterministic span resolution. The mitigation is Step 6.2, which resolves every material claim against its span by string or structural comparison rather than by model judgement, and downgrades the release verdict on any failure.

**The retrieval-decision gate can be wrong in both directions**: Suppressing retrieval for a question the context does not actually answer produces a confident unsupported answer, which is worse than the waste it saved. Invoking retrieval unnecessarily costs budget and admits distractors. The mitigation is the paired metrics in Section III.D, gate waste and unsupported-claim leakage, which must be reported together, since optimising either alone degrades the other.

**Bounds are not transferable across retrieval surfaces**: A bound calibrated against one corpus, retrieval service, or model version does not hold against another, because the point of diminishing return is a property of the retrieval surface rather than of the method. The mitigation is the version record in Step 7.3, which ties every promoted bound to the corpus, service, and model version it was derived against and forces re-derivation on change.

**Instrumentation carries its own exposure**: A log rich enough to support loop analysis records queries, spans, and source identities, and queries are themselves an outbound channel. The mitigation is the disclosure boundary in Step 7.1, which prohibits persisting hidden reasoning traces, replaces raw sensitive payloads with hashes or content references, and treats a proposed outbound query carrying restricted content as a halting condition rather than a warning.

**A bounded loop is not a correct loop**: A run can satisfy every checkpoint here, terminate on convergence, and still answer a poorly framed question from an inappropriate corpus. The framework detects unbounded and unsupported retrieval, not misdirected inquiry, and no checkpoint substitutes for human review of the question and the source policy.

***

## VI. Conclusion and Summary

Agentic retrieval-augmented generation is a control discipline before it is a retrieval technique. Its value comes from a small number of explicit, auditable decisions: whether to retrieve at all, how to decompose the question, what one iteration is permitted to cost, whether that iteration produced measurable gain, whether the evidence held now satisfies a checkable condition, and how the loop ends. A system that makes those decisions explicitly and records them converges; a system that leaves them to a model's sense of whether it has looked hard enough retrieves until its budget is gone.

The dominant production failure is not poor retrieval. It is unbounded retrieval: a loop that can decide to retrieve again, deciding to retrieve again, indefinitely, on the strength of remaining budget rather than measured progress. Every control specified here exists to close that failure. The iteration ceiling caps the loop. The progress test proves each iteration paid for itself. The repetition prohibition ensures an identical query is never reissued after an identical failure. The reformulation bound caps how many ways one question is asked. The stopping rule admits exactly three endings, one of which is a declared abstention, so exhaustion is reported rather than disguised as an answer.

A team introducing this loop should instrument the baseline before building the controller. Freeze a single-pass route and measure its support coverage, citation precision, latency, and cost on the target slice. Add the retrieval-decision gate and measure how much traffic it suppresses. Add exactly 1 bounded iteration with a progress test and measure the gain curve. Only then raise the bound, and raise it to the observed point of diminishing return rather than to a figure chosen in advance.

**Key Success Factors**:

- **Bound before autonomy**: An iteration ceiling, a variant ceiling, and a budget ledger are declared before the first retrieval action, and no model output may raise any of them.
- **Measured gain, not activity**: Continuation is licensed by a computed evidence-gain delta and novel-evidence ratio, never by a model's report of its own progress and never by remaining budget.
- **Deterministic authority**: The model proposes continuation and the controller disposes; where the two disagree the controller executes and the disagreement is logged.
- **Checkable sufficiency**: The decision to answer rests on a predicate over the evidence ledger, evaluated by deterministic checks, not on a confidence figure.
- **No repetition after failure**: An identical query is never reissued against an identical route after an identical failure, and a repeated state hash blocks a further iteration outright.
- **Honest termination**: Budget exhaustion produces a declared abstention naming what is known, unknown, attempted, and required, never a synthesised guess.

By following this guide, AI agents can decide whether retrieval is warranted, pursue evidence only while it is still arriving, and terminate through a declared outcome a reviewer can audit rather than through exhaustion or fluent confidence.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. One entry, marked as such, was retrieved during this conversion rather than taken from the prose source.

**Corpus pointers**:

- `Agentic RAG: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the retrieval-justification conditions, the escalation ladder, the control-architecture taxonomy, the plan validation gate, the per-loop entry, gain, maximum, oscillation, and exit structure, the evidence-gain and novel-evidence definitions, the termination and escalation vocabulary, the trace field inventory, the failure-mode catalogue, and the evaluation and ablation design. It carries inline citations to primary literature on agentic retrieval taxonomy, reasoning-and-acting control, multi-agent frameworks, reinforcement-learning-trained search, context degradation, memory poisoning, agent benchmarks, and agent security; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/knowledge-retrieval/guide_AdvancedKnowledgeRetrieval.md` — the category's architecture-selection guide, which places this loop at rung 11 and owns the parsing, chunking, hybrid fusion, and reranking mechanics that Section 1.2 consumes as tool behaviour rather than specifying.
- `advanced_task_guides/knowledge-retrieval/guide_CorrectiveRAG.md` — companion guidance on grading a retrieval result and repairing it, the evidence-quality routing that Section 1.2 invokes as a bounded action inside one iteration rather than as an outer loop.
- `advanced_task_guides/knowledge-retrieval/guide_SelfRAG.md` — companion guidance on segment-level self-assessment of generated text, which Section 1.2 consumes as one signal feeding the evidence-sufficiency predicate rather than restating.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — companion guidance on the transformation catalogue a diagnosed reformulation selects from; this guide owns the reformulation bound and the failure diagnosis, that guide owns the treatments the bound counts.
- `advanced_task_guides/knowledge-retrieval/guide_ModularRAG.md` — companion guidance on module contracts and approved subgraphs, applicable where this loop is one topology inside a composed pipeline rather than the whole system.
- `advanced_task_guides/knowledge-retrieval/guide_DeepResearchAgent.md` — companion guidance on long-horizon investigation across a versioned question tree, applicable where one run's iteration and reformulation bounds are too narrow for the task.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on monitoring an active process and deciding whether a further computation is worth its cost, applicable to the transition decision in Step 5.2 and to the tier authority rule in Section 1.4.
- `advanced_task_guides/planning/guide_IntelligentGoalDecomposition.md` — companion guidance on decomposing a goal into bounded units, applicable to the sub-question construction in Step 2.1.
- `advanced_task_guides/planning/guide_PlanExecuteDecoupling.md` — companion guidance on separating plan construction from plan execution, applicable to the plan validation gate in Step 2.2.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the iteration control record in Step 7.1.
- `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guidance on monitoring under constraint, applicable to the convergence metric set in Step 7.2.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — companion guidance on state and memory boundaries, applicable to the context management requirements in Section III.A.
- `advanced_task_guides/research-analysis/guide_ArxivResearch.md` — companion guidance on literature retrieval and source handling, applicable to the evidence synthesis patterns in Section IV.

**External references**:

*Agentic retrieval taxonomy and control patterns*

1. Singh and colleagues, *Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG* — https://arxiv.org/abs/2501.09136
2. Mishra and colleagues, *SoK: Agentic Retrieval-Augmented Generation (RAG): Taxonomy, Architectures, Evaluation, and Research Directions* — https://arxiv.org/abs/2603.07379
3. Yao and colleagues, *ReAct: Synergizing Reasoning and Acting in Language Models* — https://arxiv.org/abs/2210.03629
4. Wu and colleagues, *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation* — https://arxiv.org/abs/2308.08155

*Stopping control, context degradation, and memory integrity*

5. Park and colleagues, *Stop-RAG: Value-Based Retrieval Control for Iterative RAG* — https://arxiv.org/abs/2510.14337. Retrieved during this conversion; cited in Section 1.2 as the learned-controller mechanism for which the deterministic progress test is the agent-layer surrogate.
6. Xia and colleagues, *Diagnosing and Mitigating Context Rot in Long-horizon Search* — https://arxiv.org/html/2606.29718v1
7. Sunil and colleagues, *Memory Poisoning Attack and Defense on Memory Based LLM-Agents* — https://arxiv.org/abs/2601.05504

*Reinforcement-learning-trained search policies, retained as background below the agent layer*

8. Jin and colleagues, *Search-R1: Training LLMs to Reason and Leverage Search Engines with Reinforcement Learning* — https://arxiv.org/abs/2503.09516
9. Song and colleagues, *R1-Searcher: Incentivizing the Search Capability in LLMs via Reinforcement Learning* — https://arxiv.org/abs/2503.05592
10. *R1-Searcher++: Incentivizing the Dynamic Knowledge Acquisition of LLMs via Reinforcement Learning* — https://arxiv.org/abs/2505.17005
11. Zheng and colleagues, *DeepResearcher: Scaling Deep Research via Reinforcement Learning in Real-world Environments* — https://arxiv.org/abs/2504.03160
12. Luo and colleagues, *Agent Lightning: Train ANY AI Agents with Reinforcement Learning* — https://arxiv.org/abs/2508.03680
13. Jiang and colleagues, *Harness-1: Reinforcement Learning for Search Agents with State-Externalizing Harnesses* — https://arxiv.org/abs/2606.02373
14. Kumar and colleagues, *Search-GRT: Guided Retrieval Training of Search Agents to Optimize for Complex Question Answering* — https://arxiv.org/abs/2608.00974

*Benchmarks for multi-hop retrieval, browsing, and deep research*

15. Yang and colleagues, *HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering* — https://arxiv.org/abs/1809.09600
16. Mialon and colleagues, *GAIA: a benchmark for General AI Assistants* — https://arxiv.org/abs/2311.12983
17. Froger and colleagues, *Gaia2: Benchmarking LLM Agents on Dynamic and Asynchronous Environments* — https://arxiv.org/abs/2602.11964
18. OpenAI, *BrowseComp: a benchmark for browsing agents* — https://openai.com/index/browsecomp/
19. Lù and colleagues, *AgentRewardBench: Evaluating Automatic Evaluations of Web Agent Trajectories* — https://arxiv.org/abs/2504.08942
20. Du and colleagues, *DeepResearch Bench: A Comprehensive Benchmark for Deep Research Agents* — https://arxiv.org/abs/2506.11763
21. Li and colleagues, *DeepResearch Bench II: Diagnosing Deep Research Agents via Rubrics from Expert Report* — https://arxiv.org/abs/2601.08536
22. Han and colleagues, *DEER: A Benchmark for Evaluating Deep Research Agents on Expert Report Generation* — https://arxiv.org/abs/2512.17776
23. Li and colleagues, *ReportBench: Evaluating Deep Research Agents via Academic Survey Tasks* — https://arxiv.org/abs/2508.15804
24. Zhong and colleagues, *DRACO: a Cross-Domain Benchmark for Deep Research Accuracy, Completeness, and Objectivity* — https://arxiv.org/abs/2602.11685
25. Wu and colleagues, *AgentSearchBench: A Benchmark for AI Agent Search in the Wild* — https://arxiv.org/abs/2604.22436

*Security, trust boundaries, and instrumentation*

26. OWASP, *LLM01:2025 Prompt Injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
27. OWASP, *AI Agent Security Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html
28. OWASP, *MCP (Model Context Protocol) Security Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html
29. Model Context Protocol, *Security Best Practices* — https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
30. A2A Protocol Working Group, *Agent2Agent (A2A) Protocol Specification* — https://github.com/a2aproject/A2A/blob/main/docs/specification.md
31. OpenTelemetry, *Generative AI semantic conventions repository* — https://github.com/open-telemetry/semantic-conventions-genai/tree/main/docs/gen-ai

*Orchestration runtime documentation*

32. LangChain, *Workflows and agents* — https://docs.langchain.com/oss/python/langgraph/workflows-agents
33. LangChain, *Persistence* — https://docs.langchain.com/oss/python/langgraph/persistence
34. LangChain, *Interrupts* — https://docs.langchain.com/oss/python/langgraph/interrupts
