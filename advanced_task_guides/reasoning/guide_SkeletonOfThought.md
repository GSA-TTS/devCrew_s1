# Skeleton-of-Thought

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Skeleton-of-Thought constitutes the task family of restructuring a long answer into a short outline of independent points, expanding those points concurrently, and assembling the expansions in outline order. Its purpose is latency: the expansions do not depend on one another, so they can be generated at the same time instead of one after another. It is not a reasoning-quality technique, and this guide states that plainly. Its measured quality effects are mixed, improving diversity and relevance while harming coherence and immersion. This guide provides AI agents with a structured protocol covering an applicability gate that routes only genuinely parallel answers, a skeleton quality gate enforcing full coverage and non-overlap before any content exists, a dependency analysis that partitions points into a concurrently expandable set and a sequentially expanded remainder, bounded fan-out under explicit concurrency and budget caps, deterministic assembly with contradiction and duplication reconciliation, and paired measurement of latency, cost, and quality against a sequential baseline. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures to ensure that concurrency is applied only where independence holds and that the latency gain is measured rather than assumed.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Skeleton-of-Thought**: A two-stage generation method in which a model first emits a short numbered outline of the answer's points, then receives one expansion request per point, and the expansions are concatenated in outline order. The canonical name is singular; the plural form is a naming error [1].

**Skeleton**: The ordered set of answer points produced by the first stage. Each point carries a stable identifier, a scope statement, an expected output type, and the evidence it is permitted to consume. The skeleton is committed before any content exists.

**Point**: One unit of the skeleton. A point is the atomic unit of concurrent expansion and the atomic unit of failure; a point either passes validation and enters assembly, or it is recorded as an omission.

**Expansion**: The prose, list, or structured output generated for exactly one point. Each expansion request carries the original request, the complete skeleton, the shared context, the target point's identifier and scope, and an instruction not to answer any other point.

**Independence**: The property that a point's correctness does not require any sibling point's generated content. Independence is semantic, not lexical: two differently named points that share a definition, a variable, an evidence selection, or a conclusion are dependent.

**Dependency edge**: A recorded directed relation stating that one point consumes a value, decision, definition, or ordering produced by another. Dependency edges are computed before dispatch and determine expansion mode.

**Expansion mode**: One of two dispositions assigned to every point: parallel, where the point has no inbound dependency edge, or sequential, where at least one inbound edge is unresolved.

**Shared context**: The immutable block of global facts, terminology, units, timeframe, audience, citation set, and voice hoisted out of the points and supplied identically to every expansion request. Hoisting a shared term into this block is the standard remedy for a dependency edge.

**Fan-out**: The number of expansion requests dispatched concurrently. Fan-out is bounded by the lower of the run cap, the provider concurrency cap, and the live capacity allowance.

**Assembly contract**: The deterministic rule that reconstructs the final answer from accepted expansions in skeleton order using stable identifiers, never completion order, and never by asking a model to recreate missing content.

**Reconciliation**: The bounded pass that removes duplication, resolves contradiction, normalises terminology, and repairs transitions across independently generated sections without changing any supported claim.

**Sequential baseline**: A single-call answer to the same request under the same model, evidence, output budget, and verifier, measured before any routing decision and used as the comparison for every latency, cost, and quality figure.

**Time to final verified answer**: Release timestamp minus run start. This is the latency figure the method targets, and it is distinct from time to first token, time to first useful content, and time to first complete point.

**Straggler**: A dispatched expansion that has not completed when the fan-in deadline arrives. Straggler handling, not average expansion time, controls the achieved speed-up, because the slowest mandatory point governs fan-in.

**Prefill amplification**: The ratio of input tokens consumed by the parallel route to input tokens consumed by the sequential route, caused by repeating the request, skeleton, and shared context in every expansion call.

**Omission**: A mandatory point with no accepted expansion. An omission is disclosed in the released answer or triggers fallback; it is never filled with connective prose.

### 1.2 Method Scope: Latency and Structure, Not Reasoning Quality

**What the method optimises**: The method is data-level parallelism applied to answer text. It restructures an answer so independent semantic units are generated at the same time, and it changes an application's request schedule rather than a model's token sampler [1]. The originating source reports the canonical evaluation covering 12 models with a headline end-to-end speed-up of up to 2.39 times and more than two times on eight of them; knowledge, generic, common-sense, roleplay, and counterfactual questions showed 1.89 to 2.33 times.

**What the method does not optimise**: Concurrency does not make an answer more correct. Agreement among expansions is not corroboration, because every expansion shares the same question, the same skeleton, the same prompt family, and the same model biases. A guide, a report, or an agent that presents parallel structure as evidence of correctness has misread the method.

**The mixed quality record**: The originating source reports that two evaluators disagreed substantially on how often the method was strictly better, at 45.8 percent and 29.5 percent, while both placed it at no worse than sequential generation in roughly 60 percent of cases. The method tended to improve diversity and relevance while harming coherence and immersion. The favourable categories were generic, common-sense, knowledge, roleplay, and counterfactual; the weak categories were writing, Fermi estimation, mathematics, and coding.

**Why an outline can help and can hurt**: An outline committed before content forces explicit coverage and prevents the omission of a required topic, which is the coverage benefit. The same outline fixes a structure before any content exists, so a wrong decomposition cannot be repaired downstream: no amount of detail in a branch recovers work that was never assigned to a point, and no expansion can undo an overlap the skeleton created. The skeleton is therefore gated in Phase 2 rather than trusted.

**Latency is a claim, not a property**: Point count is not the speed-up multiplier. The skeleton stage is serial, the slowest mandatory expansion controls fan-in, expansion lengths vary, every request adds queue and prefill overhead, and repeated context inflates input tokens. The originating source reports prefill-token ratios of 85.79, 60.46, and 89.20 for three hosted models on manually suitable items, and reports one open-source model showing no gain at all because its expansions were as long as a full answer. On a saturated backend the expansions become additional requests competing for scheduler slots, and one user's latency improves by consuming capacity from others. Every deployment measures the gain against the sequential baseline in Phase 7 rather than assuming it.

**The honest summary**: The method reduces wall time on suitable requests while increasing request count, input tokens, and price. Latency and cost move in opposite directions, and a deployment that cannot state which one it is buying has not justified the route.

### 1.3 The Applicability Gate and the Independence Condition

The route is not free and is not general. Agents must run a deterministic gate, bounded to 3 percent of the sequential baseline's measured cost, returning parallel, sequential, or a named alternative method.

**The independence condition**: A point is independent only where all of its inputs are already present in the shared context, it consumes no sibling's generated detail, and reconciliation changes no sibling's substance. Four tests establish this, and every one must pass:

- **Order reversal**: Reversing the generation order of two points changes neither point's correctness.
- **Value consumption**: Neither point requires a value, decision, selection, or definition that the other produces.
- **Shared state mutation**: Neither point writes to state the other reads, including assumption sets, running totals, variable bindings, and evidence selections.
- **Interpretive prerequisite**: Neither point becomes ambiguous or incorrect when read without the other.

Soft presentation order is acceptable, because it constrains only the reading sequence. Hard information dependency is not. Where a term, unit, assumption, or citation is shared across points, hoist it into immutable shared context before dispatch; where the dependency is a generated value rather than a fixed fact, hoisting cannot resolve it and the dependent subset must be expanded sequentially.

**Hard exclusions**: Route to sequential generation without further analysis where the request involves dependent derivation, multi-step calculation, formal proof, code whose components must compile or share interfaces and invariants, stateful debugging, chronological narrative, persuasive argument requiring a single connected line, or contract clauses carrying cross-references. The originating source records the mechanism of harm in these categories: independent branches forget assumptions, emit prose in place of code, duplicate whole programs, and produce disconnected writing, and one reported measurement showed mathematics questions averaging only 1.20 times with no absolute latency reduction.

**Positive conditions**: Route to parallel expansion where the answer decomposes into factored explanations, independent comparisons, risk registers, multi-aspect reviews, catalogues of recommendations, or reports whose sections share a fixed terminology and evidence manifest, and where at least 2 points contain meaningful work.

**Applicability Gate Decision Table**:

| Observable condition | Structural consequence | Gate verdict |
| :-- | :-- | :-- |
| Answer decomposes into 2 or more disjoint aspects sharing fixed terminology | No dependency edges after hoisting | Route parallel |
| One point requires a value another point computes | Unresolvable dependency edge | Route sequential; ordered decomposition applies |
| Every answer sentence derives from the prior sentence | Single connected argument | Route sequential; outline fragments the reasoning |
| Predicted answer under 300 words | Fan-out overhead exceeds generation time | Route sequential |
| Backend saturated or quota headroom below reservation | Fan-out adds queue depth without capacity | Route sequential; record capacity refusal |
| Cost ceiling below the prefill-amplified estimate | Input tokens dominate the trade | Route sequential |
| Sequential baseline already meets the deadline | No latency to recover | Release the baseline |
| Repeated context carries restricted data across providers | Disclosure surface multiplied by fan-out | Route sequential |
| Points independent but predicted speed-up below margin | Gain does not clear measurement noise | Route sequential; record the estimate |

**Numeric gate rules**: Route parallel only where all four independence tests pass for every pair in the candidate set, at least 2 points carry meaningful work, no more than 8 points are proposed, the predicted end-to-end speed-up is at least 1.30 times the measured sequential baseline, the projected total cost stays within 3 times the verified sequential baseline, and capacity admission succeeds. Where the predicted speed-up falls below 1.30 times, route sequential and record the estimate, because a smaller predicted margin does not survive queue variance. Where any hard exclusion fires, route sequential without adjudication; a router is never re-queried until it returns a favourable verdict.

**Boundary against neighbouring methods**: This method owns independent decomposition for parallel expansion, in which points are generated concurrently and assembled in a fixed order. Ordered decomposition, in which subproblems are solved in sequence and each answer feeds the next, belongs to least-to-most reasoning and is out of scope here. Sequential derivation, where the intermediate steps are the object of interest, belongs to chain-of-thought reasoning. An explicit dependency structure with merges belongs to graph-structured reasoning or an external workflow graph. Repeated independent attempts at the same question, adjudicated by agreement, belong to self-consistency sampling; those attempts are redundant by design, while the points here are disjoint by design.

### 1.4 Execution Tier Partition

Every operation in this method belongs to exactly one execution tier, and the assignment is not discretionary. The deterministic tier owns everything that must be exact, reproducible, and auditable. The model tier owns only the open-vocabulary generation and judgement no deterministic rule covers. The hybrid tier covers operations where a model proposes and software decides, and in every such operation the deterministic component holds authority.

**Tier Assignment by Operation**:

| Operation | Owning tier | Authority when tiers disagree |
| :-- | :-- | :-- |
| Skeleton generation | Model | Model tier proposes an outline; it never admits it |
| Skeleton parsing, identifier assignment, order freeze | Deterministic | Deterministic; an unparseable skeleton is rejected, never coerced |
| Coverage accounting against required deliverables | Deterministic | Deterministic; a checklist match is not a judgement call |
| Semantic overlap proposal between two point scopes | Hybrid | Deterministic threshold decides; the model proposes only |
| Dependency edge detection and the four independence tests | Deterministic | Deterministic; a detected edge is never overridden by a model |
| Expansion-mode assignment for every point | Deterministic | Deterministic; the model never selects its own concurrency |
| Shared-context hoisting decision | Hybrid | Model proposes the shared term; deterministic hoisting is verified |
| Capacity reservation, concurrency limits, admission control | Deterministic | Deterministic; enforced outside the model |
| Point expansion generation | Model | Model tier generates content only; it decides nothing |
| Schema, scope, evidence, truncation, and length validation | Deterministic | Deterministic; a truncated expansion is a failure, not a style |
| Straggler detection, cancellation, deadline enforcement | Deterministic | Deterministic; no model waits on its own behalf |
| Assembly ordering by stable identifier | Deterministic | Deterministic; completion order is never used |
| Duplication detection across expansions | Deterministic | Deterministic; computed over a versioned clustering rule |
| Contradiction detection across sections | Hybrid | Deterministic checks first; the model adjudicates residual pairs |
| Reconciliation drafting for presentation defects | Model | Model tier drafts; it may not change a supported claim |
| Substantive conflict resolution between two expansions | Deterministic | Deterministic routing to verification or fallback; never a merge guess |
| Budget, token, request, and latency accounting | Deterministic | Deterministic; counters never reset within a run |
| Fallback trigger and reason-code assignment | Deterministic | Deterministic; fallback is a rule, not a judgement |
| Release decision against the verification set | Deterministic | Deterministic; this decision is never delegated to a model |

**The prohibition that defines the boundary**: Points carrying an unresolved dependency edge are never expanded concurrently. This is the single rule the method exists to enforce, and no confidence statement, model assertion, or schedule pressure overrides it. A model is never permitted to set its own fan-out, to declare its own points independent without deterministic confirmation, to reorder assembly, to invent content for a missing point, or to resolve a substantive contradiction between two expansions by choosing one. Where a model tier component and a deterministic tier component disagree about independence, coverage, overlap, truncation, or ordering, the deterministic component wins and the disagreement is logged.

**Where the model tier is indispensable**: Producing a skeleton is open-vocabulary decomposition no deterministic rule replaces, and it is the reason the method exists. Expanding a point into prose is the second model-owned operation. Drafting a reconciliation edit for a presentation defect is the third. All three are proposal operations, and none carries decision authority.

***

## II. Operational Framework: Bounded Parallel Expansion Under a Deterministic Assembly Contract

The framework assumes the applicability gate in Section 1.3 has returned parallel. Phases 1 through 5 run in sequence. Phase 6 is entered from any failure exit in Phases 2 through 5 and terminates the run. Phase 7 runs after release and feeds the gate's calibration. Every counter declared in Phase 1 persists across phase transitions and is never reset by a retry, a repair, or a fallback.

### Phase 1: Contract Establishment and Applicability Determination

**Objective**: Fix the run contract and hard caps, measure a sequential baseline, and decide whether the request is expanded in parallel at all, before any skeleton is generated.

#### Step 1.1: Establish the Run Contract and Hard Caps

**Required Actions**:

- Record the objective, required deliverables, output structure, evidence policy, risk class, privacy class, deadline, latency target, cost ceiling, model and provider, tool authorisations, success criteria, and fallback method.
- Set the hard caps before any model call: at most 8 skeleton points, at most 2 skeleton candidates, at most 2 repairs per candidate, concurrency at most 4, at most 1 transient retry per point, at most 2 semantic re-expansions per run, at most 2 merge repairs, exactly 1 fallback, at most 20 model calls, at most 30,000 tokens, at most 90 seconds wall time, and at most 3 times the verified sequential cost.
- Declare which deliverables are mandatory and which are optional, since only optional points may be released as a labelled omission.
- Instantiate a budget ledger with one counter per bounded dimension, and declare that no counter resets on retry, repair, or fallback.
- Declare the reason-code vocabulary used by every exit in this framework, drawn from a closed list.

**Required Outputs**:

- A run contract record naming objective, deliverables, risk class, privacy class, deadline, and cost ceiling.
- A hard-cap table with a numeric limit on every bounded dimension.
- A mandatory and optional deliverable partition.
- A budget ledger with monotonic counters.

**Quality Checkpoints**:

- Every bounded dimension carries a numeric limit; an unbounded dimension halts the run before the first model call.
- Every deliverable is classified mandatory or optional; an unclassified deliverable is treated as mandatory.
- The contract states the fallback method by name, so a failure exit has a declared destination.

***

#### Step 1.2: Measure the Sequential Baseline

**Required Actions**:

- Execute one sequential answer to the same request under the same model, evidence set, output budget, and verifier that the parallel route will use.
- Record its end-to-end latency, time to first token, total input tokens, cached input tokens, output tokens, reasoning tokens where the provider reports them, request count, and itemised cost.
- Score the baseline against the release verification set, so a quality comparison exists before any routing decision.
- Release the baseline immediately and terminate the run where it satisfies the deadline and the verification set, since no latency remains to recover.
- Where a reasoning-capable model is authorised, measure a direct reasoning-model call as a second baseline, since it raises the sequential floor without creating any observable per-section concurrency.

**Required Outputs**:

- A sequential baseline record carrying latency, token, cost, and request-count figures.
- A baseline verification score against the release set.
- A baseline disposition of released or retained for comparison.

**Quality Checkpoints**:

- The baseline uses the same model, evidence, output budget, and verifier as the planned parallel route; an unmatched baseline is invalid as a comparator.
- The baseline cost figure is itemised, so the 3 times cost ceiling is enforceable rather than notional.
- A baseline meeting the deadline and the verification set is released, and the parallel route is not attempted.

***

#### Step 1.3: Apply the Applicability Gate and Record the Verdict

**Required Actions**:

- Apply every hard exclusion from Section 1.3 first, and route sequential without further analysis where any exclusion fires.
- Predict point count, expansion length distribution, straggler risk, prefill amplification, latency delta, and total cost ratio from the request features and current backend telemetry.
- Query capacity admission for the projected reservation, and refuse the parallel route where quota headroom, provider concurrency, or queue depth cannot absorb the fan-out.
- Permit at most 1 model adjudication where the deterministic features are inconclusive, and compare its verdict against those features rather than substituting for them.
- Record the verdict, the deciding features, the predicted speed-up, and the predicted cost ratio, whichever way the gate resolves.

**Required Outputs**:

- A gate verdict of parallel, sequential, or a named alternative method.
- A prediction record carrying point count, latency delta, and cost ratio estimates.
- A capacity admission result with the reserved quantities.

**Quality Checkpoints**:

- No hard exclusion is present in a request routed parallel; a single exclusion is decisive on its own.
- The predicted speed-up is at least 1.30 times, and the predicted cost ratio is at most 3 times; a route failing either bound is refused.
- At most 1 model adjudication was consumed, and no router was re-queried after an unfavourable verdict.

***

### Phase 2: Skeleton Generation and Quality Gating

**Objective**: Produce and admit one skeleton whose points cover every mandatory deliverable exactly once, since the outline is committed before any content exists and a defective outline cannot be repaired by better expansions.

#### Step 2.1: Generate the Candidate Skeleton

**Required Actions**:

- Request one compact skeleton in which each point states a disjoint scope, the evidence it may consume, its expected output type, and its expected length, without expanding any answer content.
- Constrain the response to a parseable numbered structure, and reject a free-prose reply rather than salvaging it.
- Parse the response into stable point identifiers, and freeze the order at parse time so later assembly cannot depend on completion order.
- Record the generating call, the prompt version, the sampling parameters, the model revision, and the content hash of the accepted skeleton.
- Generate a second candidate only where the first cannot be locally repaired or where material ambiguity about the request's scope remains.

**Required Outputs**:

- A parsed skeleton record with stable identifiers and a frozen order.
- A per-point scope, evidence allowance, output type, and expected length.
- A generation provenance record naming prompt version, model revision, and content hash.

**Quality Checkpoints**:

- Every point carries a stable identifier assigned by the deterministic tier, not by the model's own numbering text.
- No point contains expanded answer content; a skeleton that already answers the request is rejected as a one-call sequential answer in disguise.
- At most 2 candidates were generated across the run.

***

#### Step 2.2: Gate Coverage, Non-Overlap, and Granularity

**Required Actions**:

- Match every mandatory deliverable from Step 1.1 against the point set, and require that each is assigned to exactly 1 point.
- Compute pairwise scope overlap across all point pairs using a versioned intent-and-evidence intersection rule, and reject the candidate where any pair exceeds the overlap threshold.
- Reject points that are sentence fragments, restatements of the request, or containers too coarse to expand within their declared length.
- Confirm the point count falls within 2 and 8, and that at least 2 points carry meaningful work rather than a title and a stub.
- Confirm every point is answerable from the shared context and its own evidence allowance, without consulting a sibling's output.

**Skeleton Defect Codes and Their Dispositions**:

| Defect code | Detection rule | Disposition |
| :-- | :-- | :-- |
| Coverage gap | A mandatory deliverable maps to 0 points | Local repair; 1 attempt |
| Coverage duplication | A mandatory deliverable maps to 2 or more points | Local repair; 1 attempt |
| Scope overlap | Pairwise intent-and-evidence intersection above 20 percent | Local repair; 1 attempt |
| Fragment point | Point scope under 5 words or lacking an output type | Local repair; 1 attempt |
| Coarse point | Declared length above 40 percent of total answer budget | Local repair; 1 attempt |
| Dependent calculation | Point requires a sibling's computed value | New candidate or sequential route |
| Contradictory scope | Two points assert incompatible framings of one deliverable | New candidate or sequential route |
| Count breach | Point count above 8 or below 2 | New candidate or sequential route |
| Embedded answer | Any point contains expanded prose | New candidate or sequential route |
| Safety breach | A point directs prohibited content or unauthorised tool use | Immediate sequential route |

**Required Outputs**:

- A coverage matrix mapping every mandatory deliverable to exactly 1 point.
- A pairwise overlap score matrix with the threshold applied.
- A defect list carrying one code per detected defect.

**Quality Checkpoints**:

- Coverage of mandatory deliverables is 100 percent, and no deliverable is assigned twice.
- Every pairwise overlap score is at or below 20 percent; a single breach blocks admission.
- Point count is within 2 and 8, and at least 2 points carry meaningful work.

***

#### Step 2.3: Bound Skeleton Revision and Admit or Exit

**Required Actions**:

- Return only defect codes and the affected point identifiers to the generator, never a rewritten skeleton, so the repair addresses the diagnosed defect rather than the reviewer's preference.
- Permit at most 2 repairs per candidate, and permit a second repair only where it targets a different concrete defect from the first.
- Re-run the full coverage, overlap, granularity, and safety checks after every repair, not only the checks that previously failed.
- Admit the skeleton where every mandatory check passes and the projected worst-case resource consumption fits inside every cap from Step 1.1.
- Exit to Phase 6 after 2 candidates, 2 repairs on the surviving candidate, a repeated overlap defect, a safety breach, or any cap.

**Required Outputs**:

- An admitted skeleton with an admission record naming the checks passed and the repair count consumed.
- A projected worst-case resource estimate covering calls, tokens, cost, and wall time.
- A revision history listing every defect code and its repair outcome.

**Quality Checkpoints**:

- The revision bound of 2 candidates and 2 repairs per candidate was not exceeded; exhaustion routes to fallback rather than to a third attempt.
- No check threshold was lowered to admit a skeleton; the rubric is fixed before the first candidate.
- The projected worst-case consumption fits every cap; a projection that does not fit blocks admission.

***

### Phase 3: Dependency Analysis and Expansion-Mode Selection

**Objective**: Compute the dependency structure over the admitted skeleton and assign every point an expansion mode, so that concurrency is applied only where independence has been established rather than assumed from the outline's flat appearance.

#### Step 3.1: Build the Point Dependency Graph

**Required Actions**:

- Apply the four independence tests from Section 1.3 to every ordered pair of points, and record a directed dependency edge for each test that fails.
- Classify each detected edge as a value dependency, a definition dependency, a state dependency, or an interpretive dependency, since the class determines the available remedy.
- Extract every term, unit, assumption, timeframe, audience constraint, and citation referenced by more than 1 point, and record it as a shared-context candidate.
- Record the edge set, its class labels, and the evidence for each edge, so the dispatch decision is auditable after the run.
- Treat a flat numbered outline as no evidence of independence; the model that produced it was not asked to guarantee the property.

**Required Outputs**:

- A dependency edge set with a class label and supporting evidence per edge.
- A shared-context candidate list of terms referenced by 2 or more points.
- An edge-count figure per point, distinguishing inbound from outbound edges.

**Quality Checkpoints**:

- Every ordered point pair was tested; a partial sweep is treated as an untested graph and blocks dispatch.
- Every recorded edge carries a class label; an unclassified edge is treated as a value dependency, which is the most restrictive class.
- No edge was removed on a model's assertion that two points are independent.

***

#### Step 3.2: Partition Points Into Parallel and Sequential Sets

**Required Actions**:

- Resolve definition and interpretive edges by hoisting the shared term into immutable shared context, then re-run the affected tests and delete the edge only where it now passes.
- Leave value and state edges in place, because a generated value cannot be hoisted before it exists.
- Assign parallel mode to every point with 0 inbound edges after hoisting, and sequential mode to every point retaining at least 1 inbound edge.
- Order the sequential subset by topological sort over the residual edge set, and route to Phase 6 where the residual graph contains a cycle.
- Route the whole request to Phase 6 where more than 40 percent of points retain an inbound edge, since the remaining concurrency cannot recover the coordination cost.

**Required Outputs**:

- A parallel point set with 0 inbound edges per member.
- A sequential point set with a topological execution order.
- A hoisting record naming every term moved into shared context and the edges it resolved.

**Quality Checkpoints**:

- No point carrying an unresolved inbound dependency edge is assigned parallel mode; this assignment is the method's defining constraint and admits no exception.
- The residual edge set is acyclic; a cycle routes to fallback rather than to an arbitrary ordering.
- At most 40 percent of points are sequential; a larger dependent subset refutes the applicability verdict from Step 1.3.

***

#### Step 3.3: Freeze Shared Context and Execution State

**Required Actions**:

- Assemble the immutable shared context from the hoisted terms, global facts, units, timeframe, audience, citation set, and voice, and record its content hash.
- Construct one point contract per point carrying its identifier, scope, evidence subset, expected output type, length bound, prohibited scope, and the instruction not to answer any other point.
- Delimit every block of untrusted or retrieved data inside each contract, and forbid point text from altering policy, authorising tools, or granting privileges to another point.
- Reserve cost, token, request, and concurrency capacity atomically for the full projected run, and create idempotency keys and absolute deadlines per point.
- Shrink optional depth, merge points through a validated non-overlapping combination, or exit to Phase 6 where the reservation fails; never launch a partial fan-out.

**Required Outputs**:

- An immutable shared-context block with a content hash.
- One point contract per point, carrying scope, evidence, length, and prohibitions.
- An atomic capacity reservation with idempotency keys and absolute deadlines.

**Quality Checkpoints**:

- The shared context is immutable and identical across every expansion request; a per-point variant reintroduces the dependency the hoist removed.
- Every point contract names its prohibited scope explicitly, so a scope breach is detectable rather than a matter of interpretation.
- The reservation is atomic and covers the whole projected run; a partial reservation blocks dispatch.

***

### Phase 4: Bounded Parallel Expansion

**Objective**: Generate every point's content under explicit concurrency, retry, and deadline bounds, expanding the parallel set concurrently and the sequential set in topological order.

#### Step 4.1: Dispatch Under Concurrency and Rate Limits

**Required Actions**:

- Dispatch the parallel set through a semaphore, worker pool, or queue whose limit is the lower of the run concurrency cap, the provider concurrency cap, and the live capacity allowance.
- Dispatch the sequential set strictly in topological order, supplying each point the accepted output of its predecessors, and never overlapping two points joined by an edge.
- Send each request with the original objective, the immutable skeleton, the shared context, the point contract, and its evidence subset, and nothing produced by a sibling that the contract does not authorise.
- Account for every provider rate dimension separately, including request-rate and token-rate limits and any shorter-interval enforcement that rejects a burst even where a per-minute average appears safe.
- Record scheduled, enqueued, dequeued, request-sent, first-token, last-token, and completed timestamps per attempt, since the latency measurement in Phase 7 is computed from them.

**Expansion Request Contract**:

```
POINT_ID:
SKELETON_HASH:
SHARED_CONTEXT_HASH:
POINT_SCOPE:
EVIDENCE_SUBSET:
EXPECTED_OUTPUT_TYPE:
LENGTH_BOUND:
PROHIBITED_SCOPE:
SIBLING_CONTENT_PERMITTED: FALSE
IDEMPOTENCY_KEY:
ABSOLUTE_DEADLINE:
```

**Required Outputs**:

- One dispatch record per point carrying its concurrency slot, reservation key, and absolute deadline.
- A timestamp series per attempt covering queue, request, first token, and completion.
- A live fan-out figure never exceeding the effective concurrency limit.

**Quality Checkpoints**:

- Observed concurrent in-flight requests never exceed the effective limit; a breach halts dispatch and releases the reservation.
- No two points joined by a residual dependency edge were in flight at the same time.
- Every request carries the same shared-context hash; a mismatch invalidates the run.

***

#### Step 4.2: Validate and Repair Individual Expansions

**Required Actions**:

- Validate every completed expansion against its schema, declared scope, evidence allowance, expected output type, length bound, and safety policy before it is eligible for assembly.
- Treat a length-termination finish reason as a failed expansion rather than a stylistic variation, since a syntactically complete final sentence can conceal a missing tail.
- Reject any expansion that answers a sibling point, invents a sibling's result, cites evidence outside its allowance, or alters policy.
- Retry a transient transport or rate-limit failure at most 1 time per point with exponential backoff and randomised jitter, preserving the idempotency key and incrementing the global counters.
- Issue at most 2 targeted re-expansions per run for semantic defects, and only where the defect is confined to a single point and its deadline still permits.

**Required Outputs**:

- A validation verdict per expansion covering schema, scope, evidence, length, truncation, and safety.
- A retry record naming the failure class, the backoff applied, and the counter state.
- An accepted expansion set with content hashes.

**Quality Checkpoints**:

- Every accepted expansion passed all six validation dimensions; a partial pass is a failure.
- Transient retries per point do not exceed 1, and semantic re-expansions per run do not exceed 2.
- No expansion contains content assigned to another point; a scope breach is rejected, not trimmed at merge.

***

#### Step 4.3: Handle Stragglers, Failures, and Partial Results

**Required Actions**:

- Cancel any expansion still in flight at the fan-in deadline, and release its reserved capacity immediately rather than waiting for a provider timeout.
- Mark an optional point with no accepted expansion as a labelled omission and continue, disclosing the omission in the released answer.
- Route a mandatory point with no accepted expansion to Phase 6 where the remaining deadline admits a sequential call for that scope, and otherwise release a verified partial result or abstain.
- Terminate the loop when all mandatory points are accepted, a mandatory point fails without a fallback window, the deadline arrives, no point makes progress for one scheduling interval, or any cap is reached.
- Apply the same validation floor and the same retry allowance to every point regardless of completion order, so a late point is not silently given a weaker budget or a weaker model.

**Required Outputs**:

- A per-point disposition of accepted, retried and accepted, omitted, or failed, with a reason code.
- A cancellation record naming released reservations and discarded work.
- A partial-result authorisation where any mandatory point is unfilled.

**Quality Checkpoints**:

- No straggler is awaited beyond the fan-in deadline; an unbounded wait is a defect, not patience.
- Every point received the same validation floor and the same retry allowance; a recorded asymmetry is disclosed rather than averaged away.
- No missing point is filled with connective prose; the gap is disclosed, filled sequentially, or the run abstains.

***

### Phase 5: Deterministic Assembly and Coherence Reconciliation

**Objective**: Reconstruct one answer from independently generated sections in a fixed order, and bring cross-section duplication, contradiction, and terminology drift within declared tolerances without changing any supported claim.

#### Step 5.1: Assemble Under the Deterministic Assembly Contract

**Required Actions**:

- Concatenate accepted expansions strictly in skeleton order using stable point identifiers, never in completion order and never in a model-chosen order.
- Preserve each expansion's evidence references, uncertainty markers, and content hash through assembly, so a later claim-level diff is possible.
- Run deterministic structural checks for duplicate headings, missing point identifiers, schema conformance, citation integrity, length bounds, silent truncation, and stable ordering.
- Insert an explicit omission marker at the position of every omitted optional point rather than closing the gap invisibly.
- Refuse to pass any missing content to a model for regeneration during assembly; a gap is a Phase 4 or Phase 6 concern, not a merge concern.

**Required Outputs**:

- An assembled draft in frozen skeleton order with per-section identifiers retained.
- A structural check report covering ordering, identifiers, schema, citations, truncation, and length.
- An omission marker at each optional gap.

**Quality Checkpoints**:

- Assembly order equals skeleton order for 100 percent of sections; a single reorder invalidates the assembly.
- Every accepted section's content hash matches its Phase 4 record; a mismatch halts the run.
- No content was generated during assembly; the assembler is deterministic software, not a model call.

***

#### Step 5.2: Detect Duplication, Contradiction, and Terminology Drift

**Required Actions**:

- Segment every section into semantic units under a versioned clustering rule, and compute pairwise redundancy across all section pairs.
- Compute duplicated-token share as duplicated semantic units over total semantic units, and record pairwise overlap incidence separately, since one large repetition and many small ones require different repairs.
- Detect contradiction by comparing asserted facts, figures, dates, units, recommendations, and conclusions across sections, resolving each disagreement to the specific claims that conflict.
- Detect terminology drift by matching every term in the shared glossary against its use in each section, and flag any synonym, abbreviation, or redefinition introduced independently.
- Detect broken transitions, unsupported cross-references between sections, register variation, and depth imbalance across accepted expansions.

**Reconciliation Tolerances**:

| Coherence defect | Measurement | Tolerance | Breach action |
| :-- | :-- | :-- | :-- |
| Cross-section contradiction | Conflicting claim pairs after adjudication | 0 | Route the affected points to verification or fallback |
| Duplicated content | Duplicated-token share across sections | At most 5 percent | Local deduplication repair |
| Pairwise overlap incidence | Section pairs with any duplicated unit | At most 10 percent of pairs | Local deduplication repair |
| Terminology drift | Glossary terms used inconsistently | 0 | Local normalisation repair |
| Unsupported cross-reference | References to another section's content that is absent | 0 | Remove the reference or route to fallback |
| Depth imbalance | Longest to shortest mandatory section length ratio | At most 3 to 1 | Local rebalancing repair |
| Register variation | Sections deviating from the declared voice | At most 1 section | Local normalisation repair |
| Silent truncation | Sections with a length-termination finish reason | 0 | Treat as a failed expansion, not a merge defect |

**Required Outputs**:

- A redundancy report carrying duplicated-token share and pairwise overlap incidence.
- A contradiction list resolved to specific conflicting claims and their section identifiers.
- A terminology drift list naming each glossary term and its divergent uses.

**Quality Checkpoints**:

- Every tolerance in the table was measured, not estimated; an unmeasured dimension is treated as a breach.
- Contradiction detection compared every section pair, not only adjacent sections.
- Duplication is measured over semantic units under a versioned rule, so the figure is reproducible across runs.

***

#### Step 5.3: Reconcile Under a Bounded Repair Cap

**Required Actions**:

- Repair only presentation defects and explicitly diagnosed conflicts: deduplicate repeated units, normalise glossary terminology, add transitions, rebalance depth, and remove unsupported cross-references.
- Prohibit any repair that changes a supported claim, alters a citation, adds a fact absent from the accepted expansions, or resolves a substantive disagreement by selecting one side.
- Route every substantive conflict, meaning a disagreement about which expansion is factually correct, to verification or to Phase 6, since a merge component that chooses is guessing.
- Permit at most 2 merge repairs per run, and re-run every failed check plus coverage and safety after each repair rather than only the checks that were repaired.
- Exit to Phase 6 on an unresolved contradiction, lost coverage, a dependency discovered during merge, repeated terminology drift after 2 repairs, silent truncation, or an exhausted repair cap.

**Required Outputs**:

- A reconciled answer meeting every tolerance in the Step 5.2 table.
- A repair log listing each edit, its defect code, and a claim-level diff showing no supported claim changed.
- An exit disposition of reconciled or routed to fallback with a reason code.

**Quality Checkpoints**:

- The claim-level diff shows 0 changed supported claims across all repairs; a changed claim voids the reconciliation.
- Merge repairs do not exceed 2; exhaustion routes to fallback rather than a third pass.
- A dependency discovered during merge always routes to fallback, because its discovery falsifies the Phase 3 partition.

***

### Phase 6: Sequential Fallback and Release Verification

**Objective**: Recover a verified answer through a single bounded sequential attempt after any parallel failure, and release only what the verification set accepts, with every material limitation disclosed.

#### Step 6.1: Reset the Run State and Select the Fallback Method

**Required Actions**:

- Discard provisional point prose and every assumption introduced only by the failed parallel route, retaining the original request, the authorised evidence, the accepted shared definitions, and the concrete defect record.
- Cancel all in-flight expansions and release their reservations before the fallback call is issued, so the fallback competes with nothing from its own run.
- Select exactly 1 sequential method keyed to the recorded failure: a direct call where the failure was capacity, a reasoning-model call where the failure was expansion quality, an ordered decomposition where a value dependency was discovered, a sequential derivation where the answer proved to be one connected argument, or a deterministic workflow where the structure is fixed and known.
- Carry every budget counter forward unchanged, since the fallback consumes the same ledger the parallel route drew from.
- Prohibit any return from the fallback to the parallel route within the same run.

**Required Outputs**:

- A reset state record naming what was discarded and what was retained.
- A selected fallback method with the failure reason code that determined it.
- A carried-forward budget ledger showing remaining headroom per dimension.

**Quality Checkpoints**:

- No provisional parallel content survives into the fallback context; a leaked expansion reintroduces the defect that caused the exit.
- Exactly 1 fallback method is selected, and the run never re-enters the parallel route.
- Budget counters were carried forward without reset; a reset ledger voids every cost comparison.

***

#### Step 6.2: Execute One Bounded Fallback Generation

**Required Actions**:

- Permit exactly 1 fallback generation and at most 1 verifier-directed local repair of that generation.
- Compare the fallback output against any complete parallel candidate under the same release rubric, so a usable parallel result is not discarded merely because a later stage failed.
- Select the first output that satisfies safety, quality, cost, and deadline constraints, preferring the parallel candidate only where it matches or exceeds the fallback on every release criterion.
- Return a clearly labelled verified partial result, abstain, or escalate to a named human role where neither output passes.
- Record the fallback outcome, its latency, its cost, and the reason the selected output was preferred.

**Required Outputs**:

- A fallback output with its verification score and cost record.
- A selection decision naming the released candidate and the criteria that decided it.
- An escalation package where neither candidate passes, stating what is known, what is missing, and what was attempted.

**Quality Checkpoints**:

- Fallback generations do not exceed 1, and fallback repairs do not exceed 1.
- The comparison used one rubric for both candidates; a candidate scored under a different rubric is not comparable.
- An abstention or escalation is a recorded outcome, not a silent degradation to a partial answer.

***

#### Step 6.3: Verify and Release Against the Original Request

**Required Actions**:

- Run the release verification set against the selected output, covering claim-to-evidence support, factual checks appropriate to the task, policy and privacy compliance, prompt-injection screening, completeness against the mandatory deliverables, coherence, and the user contract.
- Release only where every critical check passes; a non-critical failure is released with an explicit statement of the limitation.
- Disclose material omissions, partial failures, a sequential fallback, and any unusual latency and cost trade-off in terms a reader can act on.
- State that sections were developed independently where that fact bears on the reader's trust, and never present concurrency, agreement between sections, or the visible skeleton as evidence of correctness or as a view of any internal reasoning.
- Finalise telemetry, preserve lineage, and queue the run for offline evaluation where it carried a false-positive route, a failed skeleton, a straggler, high redundancy, a contradiction, a truncation, a quota failure, an expensive win, or a quality regression.

**Required Outputs**:

- A verification report with a verdict per check and a critical or non-critical classification.
- A released answer carrying its disclosure statements.
- A queued evaluation record for every run matching a review trigger.

**Quality Checkpoints**:

- Every critical check passed; a single critical failure blocks release regardless of remaining deadline.
- Every material omission and every fallback is disclosed in the released output.
- No release claims that parallel generation, section agreement, or the skeleton itself establishes correctness.

***

### Phase 7: Latency and Quality Measurement Against the Sequential Baseline

**Objective**: Establish from recorded evidence whether the parallel route delivered a latency gain that justified its cost and its quality effect, so the applicability gate is calibrated on measurement rather than on the method's reputation.

#### Step 7.1: Compute Paired Latency, Throughput, and Cost Ratios

**Required Actions**:

- Compute end-to-end latency as release time minus run start, and compute time to first token, time to first useful content, and time to first complete point from their recorded timestamps.
- Compute the speed-up ratio as sequential end-to-end latency divided by parallel end-to-end latency on paired runs of the same request under the same model, evidence, output budget, and verifier.
- Report median, 90th, 95th, and 99th percentile latency stratified by task family, point count, model, provider, backend utilisation band, and gate verdict.
- Compute total cost ratio as the parallel route's billed input, cached-input, output, and reasoning cost across routing, skeleton, every expansion, every retry, merge, and verification, divided by the sequential total, and report raw token ratio and request-count ratio alongside it because pricing changes.
- Report throughput, queue wait, fan-in wait, slowest-point share of the critical path, merge share, cancelled work, and backend utilisation, since a lower single-run latency that reduces aggregate throughput is a transfer of capacity rather than a gain.

**Required Outputs**:

- A paired latency record with speed-up ratio and tail percentiles per stratum.
- A cost record with total cost ratio, token ratio, and request-count ratio.
- A critical-path decomposition attributing time to skeleton, queue, slowest expansion, merge, and verification.

**Quality Checkpoints**:

- Every speed-up figure is computed from a paired run; an unpaired comparison is not reported as a speed-up.
- Tail latency is reported alongside the median, because fan-in is governed by the slowest point rather than the average one.
- Cost is reported whenever latency is reported; a latency claim without its cost ratio is incomplete.

***

#### Step 7.2: Compute Quality, Coverage, and Coherence Deltas

**Required Actions**:

- Compute the quality delta as the parallel route's verified score minus the sequential score on paired examples, stratified by category, and never averaged across categories with opposite effects.
- Compute point coverage as required deliverables assigned to a valid point and present in the released answer divided by all required deliverables, and point precision as necessary non-duplicate point intents divided by proposed points.
- Compute redundancy rate, contradiction rate, terminology-drift rate, depth imbalance, unsupported cross-reference rate, and silent-truncation rate from the Phase 5 measurements.
- Compute partial-failure rate as runs carrying at least 1 failed, timed-out, cancelled, or missing expansion divided by all parallel runs, separating optional from mandatory points, and report retry recovery, fallback recovery, straggler rate, deadline miss rate, rate-limit rejection rate, and reservation rejection rate.
- Measure fairness across points by reporting quality against point position, topic, evidence availability, predicted length, language, and assigned model, so an unequal budget is evaluated rather than hidden in an aggregate.

**Required Outputs**:

- A stratified quality delta table with one row per task category.
- Coverage, precision, redundancy, contradiction, and drift figures per stratum.
- A partial-failure and recovery profile with fairness figures by point position and topic.

**Quality Checkpoints**:

- No deployment claim averages mathematics, coding, writing, and independent-list categories into one figure.
- Coverage is measured against the mandatory deliverable list from Step 1.1, not against the skeleton's own points.
- Every quality figure is paired with the same verifier used for the sequential baseline.

***

#### Step 7.3: Evaluate Router Performance and Recalibrate the Gate

**Required Actions**:

- Define a positive as a run where the parallel route met or exceeded the sequential quality floor and achieved the configured latency utility under the actual serving envelope, and label every historical run against that definition.
- Compute router precision as beneficial parallel routes over all parallel routes, recall as beneficial parallel routes over all beneficial opportunities, and report specificity, false-positive quality harm, false-negative latency opportunity, calibration error, and net utility rather than accuracy alone.
- Weight false positives above false negatives, since an unnecessary parallel route can damage quality while a missed route forfeits only speed.
- Measure robustness by perturbing evidence order, skeleton wording, point order, concurrency limit, timeout, single-point failure, context length, rate pressure, injected instructions, and backend utilisation, and report route flip rate, skeleton edit distance, coverage stability, claim stability, and the clean-to-perturbed degradation in both quality and latency.
- Recompute every gate threshold and every router label after any change to model revision, prompt version, provider, pricing, or serving configuration, and update router training data only after independent adjudication rather than from the online system's own preference.

**Required Outputs**:

- A router performance record with precision, recall, calibration error, and net utility per stratum.
- A robustness report covering all 10 perturbation classes with degradation figures.
- A recalibrated threshold set with its effective date and the change that triggered it.

**Quality Checkpoints**:

- Router performance is reported as precision and recall with an asymmetric cost, never as a single accuracy figure.
- Robustness covers all 10 perturbation classes; an uncovered class blocks promotion of the configuration.
- No threshold survives a model, provider, pricing, or serving change without recomputation.

***

## III. Implementation Guidance for AI Agents

AI agents executing this method must follow systematic protocols ensuring that concurrency is authorised by a computed dependency result rather than by an outline's appearance, that assembly is deterministic, and that every latency claim is paired with a measured baseline. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Gate Agent**: Runs the applicability gate, owns the hard exclusions and the predicted speed-up estimate, and may refuse the parallel route. It never generates content and never re-queries a router after an unfavourable verdict.
2. **Skeleton Agent**: Requests and parses the skeleton, assigns stable identifiers, freezes order, and computes coverage, overlap, and granularity verdicts. It owns the 2-candidate and 2-repair bounds and may not lower a rubric to admit a candidate.
3. **Dependency Analyser**: Applies the four independence tests to every point pair, classifies edges, executes shared-context hoisting, and assigns expansion mode. It alone may mark a point parallel, and its verdict is not appealable by a generating model.
4. **Dispatch Controller**: Holds the capacity reservation, the concurrency semaphore, the rate-limit accounting, the idempotency keys, and the absolute deadlines. It cancels stragglers and releases reservations, and it never waits past the fan-in deadline.
5. **Expansion Workers**: Generate exactly 1 point each under a point contract. A worker may not read a sibling's output, extend its own deadline, retry beyond its allowance, or answer outside its scope.
6. **Assembly and Reconciliation Agent**: Concatenates in skeleton order by identifier, computes duplication, contradiction, and drift measurements, and drafts presentation repairs only. It may not change a supported claim or select between conflicting substantive expansions.
7. **Verification and Release Agent**: Runs the release verification set, decides release or fallback, owns the disclosure statements, and writes the run record. It alone authorises release.

**Workflow Execution Pattern**:

```
STATE: Expansion_Mode_Assignment
INPUTS:
  1. Admitted skeleton with frozen order from Step 2.3
  2. Dependency edge set with class labels from Step 3.1
  3. Shared-context hoisting record from Step 3.2
  4. Capacity reservation and budget ledger from Step 1.1
ACTIONS:
  1. Recompute the four independence tests for every point pair
  2. Delete only definition and interpretive edges resolved by hoisting
  3. Assign parallel mode where inbound_edge_count == 0
  4. Topologically order the residual dependent subset
  5. Emit the dispatch plan with per-point concurrency slots
VALIDATION:
  - all_pairs_tested == TRUE
  - parallel_set_inbound_edges == 0
  - residual_graph_is_acyclic == TRUE
  - sequential_point_share <= 0.40
  - shared_context_hash_identical_across_points == TRUE
  - reserved_capacity >= projected_worst_case
TRANSITIONS:
  IF all_validations_pass THEN next_state = Phase_4_Bounded_Dispatch
  IF residual_graph_is_acyclic == FALSE THEN next_state = Phase_6_Fallback
  IF sequential_point_share > 0.40 THEN next_state = Phase_6_Fallback
  IF reserved_capacity < projected_worst_case THEN next_state = Reservation_Retry
  IF validation_failed THEN next_state = Phase_3_Error_Handling
```

**Two-Phase Action Pattern**: Emit the dispatch plan naming every point, its mode, its slot, its budget, and its deadline without issuing a single request; confirm the plan against the validation block while no capacity is committed; commit the fan-out only after validation passes, recording the reservation in the same operation. A partial fan-out issued before validation cannot be recalled and consumes budget that the fallback will need.

**Approval Gate**: Human authorisation is required before any parallel route in the highest risk tier, before any route whose repeated context carries restricted data across a provider boundary, before any run projected to consume more than 40 percent of the remaining tenant quota, and before promoting any configuration whose measured speed-up falls below 1.30 times or whose quality delta is negative in any evaluated category. Agents halt at these gates rather than proceeding with a recorded warning.

**Context and State Management Requirements**:

- Hold the run contract, the budget ledger, the frozen skeleton, and the shared-context hash in durable state, since a fan-out may outlive a single context window.
- Supply each expansion worker the minimum context its point contract authorises, because the shared block is repeated once per point and prefill amplification scales with it.
- Version every prompt separately for routing, skeleton generation, skeleton repair, expansion, re-expansion, assembly, reconciliation repair, and verification, and pin model revision, sampling settings, maximum output, reasoning effort, and output schema.
- Cache only verified expansions, keyed on the normalised objective, the point contract, the skeleton and shared-context hashes, the evidence versions, the model and prompt versions, the authorisation scope, and the output schema; never reuse a point because its heading resembles another.
- Set reasoning effort low or adaptive for independent descriptive points and reserve higher effort for routing, skeleton validation, and a single difficult verified point, since each expansion may otherwise invoke extended reasoning independently and multiply hidden work.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract and Baseline Integrity (After Phase 1)**

- **Automated Check**: Every bounded dimension carries a numeric limit; every deliverable is classified mandatory or optional; the sequential baseline was executed under the same model, evidence, output budget, and verifier; the gate verdict records a predicted speed-up of at least 1.30 times and a predicted cost ratio of at most 3 times.
- **Agent Action on Pass**: Proceed to skeleton generation.
- **Agent Action on Failure**: Halt before any skeleton call; an unbounded ledger or an unmatched baseline makes every later measurement uninterpretable.
- **Human Review Trigger**: A request in the highest risk tier, or restricted data repeated across a provider boundary.

**Checkpoint 2: Skeleton Admission (After Phase 2)**

- **Automated Check**: Mandatory deliverable coverage is 100 percent with no deliverable assigned twice; every pairwise overlap score is at or below 20 percent; point count is within 2 and 8; candidates consumed are at most 2 and repairs at most 2 per candidate.
- **Agent Action on Pass**: Proceed to dependency analysis.
- **Agent Action on Failure**: Route to Phase 6; a defective skeleton is never carried forward on the expectation that expansions will compensate.
- **Human Review Trigger**: A coverage gap on a mandatory deliverable surviving 2 repairs.

**Checkpoint 3: Independence Verification (After Phase 3)**

- **Automated Check**: Every ordered point pair was tested; the parallel set has 0 inbound edges; the residual graph is acyclic; the sequential share is at most 40 percent; the shared-context hash is identical across all point contracts; the capacity reservation is atomic and covers the projected worst case.
- **Agent Action on Pass**: Proceed to dispatch.
- **Agent Action on Failure**: Halt dispatch and route to Phase 6; this is the one checkpoint that is never passed with a warning, because a wrongly parallelised dependent point produces incoherence that reconciliation cannot repair.
- **Human Review Trigger**: A sequential share above 40 percent recurring across more than 20 percent of runs in one task family, which indicates the gate is mis-routing that family.

**Checkpoint 4: Expansion Integrity (After Phase 4)**

- **Automated Check**: Observed concurrency never exceeded the effective limit; no two edge-joined points were in flight together; every accepted expansion passed all 6 validation dimensions; transient retries per point are at most 1; semantic re-expansions per run are at most 2; every mandatory point is accepted or explicitly dispositioned.
- **Agent Action on Pass**: Proceed to assembly.
- **Agent Action on Failure**: Cancel in-flight work, release reservations, and route the missing scope to Phase 6.
- **Human Review Trigger**: More than 20 percent of expansions failing validation in one run, or a straggler rate above 15 percent across the last 50 runs.

**Checkpoint 5: Assembly and Coherence (After Phase 5)**

- **Automated Check**: Assembly order equals skeleton order for 100 percent of sections; content hashes match the Phase 4 record; contradictions are 0; duplicated-token share is at most 5 percent; terminology drift is 0; unsupported cross-references are 0; depth imbalance is at most 3 to 1; merge repairs are at most 2; the claim-level diff shows 0 changed supported claims.
- **Agent Action on Pass**: Proceed to release verification.
- **Agent Action on Failure**: Route to Phase 6; an unresolved contradiction is never released with a warning attached.
- **Human Review Trigger**: A contradiction whose resolution requires deciding which of two expansions is factually correct.

**Checkpoint 6: Release Validity (After Phase 6)**

- **Automated Check**: Every critical verification check passed; every mandatory deliverable is present or disclosed as an omission; fallback generations are at most 1; the disclosure statement names any fallback, omission, or unusual cost trade-off.
- **Agent Action on Pass**: Release the answer and close the run record.
- **Agent Action on Failure**: Reclassify the run as a bounded failure and return the verified partial result, an abstention, or an escalation package.
- **Human Review Trigger**: Any released answer carrying a mandatory omission, or any abstention in a task family whose abstention rate exceeds 10 percent.

**Checkpoint 7: Measurement Adequacy (After Phase 7)**

- **Automated Check**: Every speed-up figure derives from a paired run; tail percentiles accompany every median; cost ratio accompanies every latency claim; quality deltas are stratified by category; all 10 perturbation classes were exercised; router figures are precision and recall rather than accuracy.
- **Agent Action on Pass**: Release the measurement report and permit promotion of the configuration.
- **Agent Action on Failure**: Withhold the report and name the missing evidence; no configuration is promoted on unpaired or unstratified results.
- **Human Review Trigger**: A measured speed-up below 1.30 times, or a negative quality delta in any evaluated category.

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

**Error Type 1: Dependency Discovered After Dispatch**

- **Symptoms**: Two sections assert different values for the same quantity; a section refers to a definition, assumption, or result no other section states; sections restate the same premise in incompatible forms; a section's correctness changes when read in isolation.
- **Diagnostic Steps**: Locate the shared quantity, definition, or state in the conflicting sections, trace it to the point pair, and determine whether the missed edge was a definition edge that hoisting should have resolved or a value edge that should have forced sequential mode.
- **Resolution Protocol**: Option A, where the edge is a definition edge, hoist the term into shared context and re-expand only the affected points, consuming the semantic re-expansion allowance. Option B, where the edge is a value edge, discard the affected expansions and expand that subset sequentially in topological order. Option C, route the whole run to Phase 6 where more than 40 percent of points prove dependent.
- **Escalation Trigger**: A dependency discovered after dispatch in more than 10 percent of runs in one task family suspends the parallel route for that family until the independence tests are revised; this class is never resolved by re-running the same fan-out.

**Error Type 2: Skeleton Defect Persisting After Repair**

- **Symptoms**: The same defect code returns after a repair; overlap scores stay above threshold across candidates; a mandatory deliverable maps to no point; the generator returns a fuller answer instead of a tighter outline.
- **Diagnostic Steps**: Confirm the defect codes returned to the generator named specific point identifiers, and check whether the request decomposes into disjoint aspects at all or is a single connected argument the gate should have excluded.
- **Resolution Protocol**: Option A, generate the second candidate with the deliverable list supplied explicitly as required coverage. Option B, reduce point count by merging two overlapping points through a validated non-overlapping combination. Option C, route to Phase 6 and record a gate false positive for the task family.
- **Escalation Trigger**: Exhaustion of 2 candidates and 2 repairs each routes to fallback immediately; the rubric is never lowered and a third candidate is never generated.

**Error Type 3: Straggler and Partial Fan-Out Failure**

- **Symptoms**: One mandatory expansion dominates the critical path; rate-limit rejections cluster at dispatch; reservations fail midway; the run holds accepted expansions it cannot assemble.
- **Diagnostic Steps**: Compare per-point queue wait, first-token latency, and output length against their predictions, and determine whether the cause is a length misprediction, a rate-limit dimension the scheduler ignored, or backend saturation that arrived after admission.
- **Resolution Protocol**: Option A, cancel the straggler at the fan-in deadline and expand its scope sequentially where the remaining deadline permits. Option B, release a verified partial result with the omission disclosed where the point is optional. Option C, abstain and record the deadline miss where the point is mandatory and no window remains.
- **Escalation Trigger**: A straggler rate above 15 percent across the last 50 runs in a task family, or a rate-limit rejection rate above 5 percent, halts parallel routing for that family pending a concurrency-limit revision.

**Error Type 4: Assembly Incoherence Beyond Tolerance**

- **Symptoms**: Duplicated-token share above 5 percent; a contradiction between sections; a glossary term used inconsistently; a section referring to content another section does not contain; one section several times longer than another.
- **Diagnostic Steps**: Classify each defect as presentation or substance, since presentation defects are repairable in place and substantive ones are not, and confirm whether the duplication traces to a skeleton overlap the Phase 2 gate should have rejected.
- **Resolution Protocol**: Option A, apply a bounded presentation repair for duplication, terminology, transitions, and depth, then re-run every check. Option B, route the conflicting points to verification where the disagreement is factual. Option C, route the run to Phase 6 where the duplication traces to a skeleton overlap, because the defect is upstream of the merge.
- **Escalation Trigger**: Any contradiction requiring a choice between two substantive expansions escalates rather than resolving; merge repairs above 2 route to fallback.

**Error Type 5: Cross-Branch Contamination and Disclosure Amplification**

- **Symptoms**: One expansion instructs the assembler or another expansion; policy text appears inside point prose; a cached point is reused across authorisation scopes; restricted context appears in more provider calls, regions, or logs than the sequential route would have produced.
- **Diagnostic Steps**: Trace the instruction to its entry point among the request, the skeleton, retrieved evidence, a single expansion, or a cached point, and enumerate every call and store that received the repeated context.
- **Resolution Protocol**: Option A, quarantine the contaminated expansion, re-expand its point from the untainted contract, and pass only accepted content into assembly. Option B, invalidate the cache entry and re-key it on the full authorisation scope. Option C, route to Phase 6 and reduce the disclosure surface to a single sequential call.
- **Escalation Trigger**: Any confirmed cross-branch instruction or any restricted context crossing a provider boundary without authorisation halts the run and is reported; this class is never resolved by retry.

**Error Type 6: Absent or Negative Latency Gain**

- **Symptoms**: Measured speed-up below 1.30 times; aggregate throughput falling while single-run latency improves; cost ratio above 3 times; time to first useful content worse than the sequential route.
- **Diagnostic Steps**: Decompose the critical path into skeleton, queue, slowest expansion, merge, and verification shares, and determine whether the loss is serial skeleton time, fan-in on a slow point, prefill amplification, or capacity taken from other tenants.
- **Resolution Protocol**: Option A, raise the gate's predicted-speed-up margin for the task family. Option B, reduce point count so the slowest expansion no longer dominates, or shrink the shared context so prefill amplification falls. Option C, retire the parallel route for the family and record the measurement that retired it.
- **Escalation Trigger**: Two consecutive measurement windows below 1.30 times retire the parallel route for the task family; a route is never retained on the expectation that a future serving change will rescue it.

**Troubleshooting Decision Tree**:

```
PARALLEL RUN FAILS A CHECKPOINT
├─ INDEPENDENCE DEFECT
│   ├─ Definition edge missed → Hoist term; re-expand affected points only
│   ├─ Value edge missed → Discard affected work; expand that subset sequentially
│   └─ Dependent share above 40 percent → HALT fan-out; route to sequential fallback
├─ SKELETON DEFECT
│   ├─ Coverage gap after 2 repairs → Route to fallback; record gate false positive
│   ├─ Overlap above 20 percent → Merge points or generate second candidate
│   └─ Embedded answer in a point → Reject candidate; never expand it
├─ DISPATCH DEFECT
│   ├─ Concurrency limit exceeded → HALT dispatch; release reservation
│   ├─ Straggler past fan-in deadline → Cancel; sequential fill or disclose omission
│   └─ Reservation failed midway → Shrink optional depth or route to fallback
├─ ASSEMBLY DEFECT
│   ├─ Duplication above 5 percent → Bounded deduplication repair; re-run all checks
│   ├─ Contradiction present → Route conflicting points to verification, never guess
│   └─ Terminology drift → Normalise against the shared glossary
├─ TRUST DEFECT
│   ├─ Cross-branch instruction found → HALT; quarantine and re-expand from contract
│   └─ Restricted context crossed a provider boundary → HALT; report and escalate
└─ VALUE DEFECT
    ├─ Speed-up below 1.30 times → Raise gate margin or retire the route
    └─ Throughput fell while latency improved → Record capacity transfer; re-admit under load
```

### D. Performance Metrics and Continuous Learning

**Latency and Efficiency Metrics**:

- **End-to-end speed-up**: Sequential latency over parallel latency on paired runs (target: at least 1.30 times median; below that for 2 consecutive windows retires the route).
- **Tail speed-up**: The same ratio at the 95th percentile (target: at least 1.10 times; a median gain with no tail gain means the slowest point governs and point count should fall).
- **Slowest-point share**: The slowest mandatory expansion's share of the critical path (target: at most 60 percent; above it, rebalance point lengths).
- **Prefill amplification**: Parallel input tokens over sequential input tokens (target: at most 8 times; the originating source records hosted-model ratios of 85.79, 60.46, and 89.20 on suitable items, which is why this dimension is capped explicitly rather than assumed small).
- **Total cost ratio**: Parallel billed cost over sequential billed cost (target: at most 3 times; a breach blocks release).
- **Throughput delta**: Aggregate served requests under load with and without the route enabled (target: no decrease; a decrease is a capacity transfer, not a gain).

**Quality and Structure Metrics**:

- **Quality delta by category**: Parallel verified score minus sequential verified score on paired examples (target: at least 0 in every evaluated category; negative in any category blocks promotion for that category).
- **Point coverage**: Mandatory deliverables present in the released answer over all mandatory deliverables (target: 100 percent).
- **Point precision**: Necessary non-duplicate point intents over proposed points (target: at least 90 percent).
- **Redundancy rate**: Duplicated-token share across sections (target: at most 5 percent).
- **Contradiction rate**: Runs releasing a cross-section contradiction (target: 0).
- **Terminology drift rate**: Runs releasing an inconsistent glossary term (target: 0).

**Reliability and Routing Metrics**:

- **Partial-failure rate**: Runs with at least 1 failed, timed-out, cancelled, or missing expansion over all parallel runs (target: at most 10 percent, reported separately for optional and mandatory points).
- **Straggler rate**: Runs where a mandatory expansion missed the fan-in deadline (target: at most 15 percent).
- **Fallback recovery rate**: Fallback runs producing a released verified answer (target: at least 90 percent).
- **Router precision**: Beneficial parallel routes over all parallel routes (target: at least 85 percent, weighted so a false positive costs more than a false negative).
- **Router recall**: Beneficial parallel routes over all beneficial opportunities (target: at least 60 percent; recall is deliberately subordinate to precision because a missed route forfeits only speed).
- **Robustness degradation**: Clean-condition minus perturbed-condition quality and speed-up (target: at most 20 percentage points on quality and at most 0.30 times on speed-up).

**Log-Pattern Failure Detection**: Sections asserting different values for one quantity indicate a missed value dependency. Repeated premises across sections indicate a skeleton overlap the gate admitted. A high median speed-up with a flat tail indicates one dominant expansion. Rising cost with flat latency indicates prefill amplification without concurrency benefit. Rate-limit rejections clustered at dispatch indicate a concurrency limit above the provider's shorter-interval enforcement. Quality falling with point position indicates that later points received a smaller residual budget.

**Learning and Adaptation Mechanisms**:

- **Adjudicated router labels**: Update router training data only from independently adjudicated outcomes, never from the online system's own preference, since a router trained on its own routing decisions confirms its bias.
- **Per-family thresholds**: Recompute the speed-up margin, the overlap threshold, the concurrency cap, and the point-count bound per task family, since a single global setting is simultaneously too permissive for connected arguments and too strict for factored catalogues.
- **Skeleton defect memory**: Record every defect code with its task family and repair outcome, and promote a recurring defect into a constraint in the skeleton prompt rather than relying on repeated repair.
- **Retirement discipline**: Retire the parallel route for a family on 2 consecutive measurement windows below the speed-up margin, and record the measurement that retired it so a later serving change can be tested against the same evidence.

**Human-in-the-Loop Boundaries**: Overriding an independence verdict, admitting a skeleton that fails coverage, resolving a substantive contradiction between two expansions, releasing an answer with a mandatory omission, and promoting a configuration whose quality delta is negative in any category are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the structure of an answer and the schedule of its generation rather than the content of any particular answer. Its phases hold wherever a deliverable decomposes into disjoint sections that share a fixed vocabulary and evidence set, and wherever latency has a stated value.

### 4.1 Cross-Domain Application Patterns

**Regulatory and compliance reporting**: A control assessment decomposes into one section per control, each drawing on the same framework definitions, scope statement, and evidence manifest. The gate routes parallel because no control's assessment consumes another's conclusion. Terminology drift is the binding coherence risk, since independently generated sections rename the same control family, so the glossary hoist covers the framework's terms and the drift tolerance is 0. The event log is a deliverable rather than a diagnostic aid, and the approval gate binds before any release carrying a mandatory omission.

**Clinical and scientific literature summarisation**: A multi-aspect review decomposes into mechanism, evidence quality, population, outcomes, and limitations. Each section consumes an assigned subset of a fixed evidence manifest, so points are independent by construction. The dominant risk is a section drawing a conclusion another section contradicts, which makes contradiction detection across every section pair mandatory rather than adjacent-pair only. Where any section must consume another's synthesised estimate, that subset expands sequentially.

**Software architecture and design review**: A review decomposes into availability, security, cost, operability, and data-handling aspects over one fixed design description. This is suitable, and the boundary is sharp: reviewing a design in parallel aspects is independent, while writing the code the design implies is not, because components share interfaces and invariants. A design review that begins to specify implementation has crossed the boundary and routes sequential.

**Operations and incident response**: A situation report decomposes into impact, affected systems, current mitigations, and open questions. Latency has direct operational value here, so the route is attractive, but the dependency risk is high because a mitigation section frequently consumes an impact section's assessment. The remedy is to hoist the confirmed impact assessment into shared context before dispatch, converting a value dependency into a shared fact.

**Financial and market analysis**: A sector review decomposes into one section per company or instrument over a shared period, currency, and data cut. This is suitable, but any comparative conclusion that ranks the sections is itself a dependent point and expands sequentially after the independent sections complete. A quantitative valuation belongs to the excluded category and never enters the parallel set.

**Education and curriculum material**: A topic overview decomposes into definition, worked context, common misconceptions, and further reading. Coverage is the binding constraint because a missing point silently removes a learning objective, so the mandatory deliverable list is the curriculum's objective list rather than the skeleton's own points. A graduated sequence in which each concept builds on the previous one is excluded.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-latency interactive work**: Keep point count at or below 4, stream the skeleton first and completed points into stable placeholders, and label every streamed fragment provisional until assembly. Streaming improves perceived latency and does not change completion latency, so it never substitutes for a measured speed-up.
- **High-risk or regulated work**: Retain every phase, raise the verification set, bind the approval gate before release, and prefer a disclosed sequential answer over an unverified parallel one. Where repeated context carries restricted data, the disclosure surface multiplied by fan-out can outweigh the latency benefit on its own.
- **Saturated or shared infrastructure**: Apply weighted fair queuing so one multi-point run cannot starve unrelated tenants, keep separate limits for global, per-provider, per-model, per-tenant, and per-run concurrency, and apply backpressure that delays or refuses new parallel runs before capacity collapse.
- **Batch and offline work**: Do not route latency-motivated fan-out through an asynchronous batch interface whose completion window is measured in hours; such interfaces suit evaluation and bulk processing, and the interactive critical path requires online concurrent requests or a self-hosted scheduler.
- **Long or many-point deliverables**: Above 8 points, split the deliverable into separate runs with their own contracts rather than raising the point cap, since fan-in risk, prefill amplification, and reconciliation cost all grow faster than the latency saving.

***

## V. Limitations and Considerations

**The method does not improve reasoning**: Concurrency changes when text is produced, not how well a problem is solved, and the reported quality record is mixed rather than favourable: improved diversity and relevance, harmed coherence and immersion, and two evaluators disagreeing on strict improvement at 45.8 percent and 29.5 percent. The mitigation is the scope statement in Section 1.2 and the release rule in Step 6.3, which prohibit presenting concurrency, section agreement, or the visible skeleton as evidence of correctness, and the quality delta target of at least 0 in every evaluated category, which blocks promotion where the route degrades an answer.

**The skeleton is committed before any content exists**: A wrong or incomplete outline cannot be repaired downstream, because no expansion recovers a deliverable that was never assigned and no reconciliation removes an overlap the skeleton created. The mitigation is the Phase 2 quality gate with 100 percent mandatory coverage, a 20 percent pairwise overlap ceiling, and a hard revision bound of 2 candidates and 2 repairs per candidate, after which the run routes to sequential fallback rather than lowering the rubric.

**Independence detection is a test, not a proof**: The four independence tests are applied by software over recorded scopes and evidence allowances, and a semantic dependency can hide inside two points that share a definition neither states. The mitigation is the hoisting rule, which converts every detected definition dependency into shared context, the 40 percent dependent-share ceiling that refutes the route rather than working around it, and Error Type 1, which suspends the parallel route for a task family where post-dispatch dependency discovery exceeds 10 percent of runs.

**Reconciliation cannot repair substance**: A merge component can deduplicate, normalise terminology, and add transitions, but a component that decides which of two conflicting expansions is factually correct is guessing under the appearance of editing. The mitigation is the tier partition, which assigns substantive conflict resolution to deterministic routing rather than to the reconciler, and the claim-level diff requirement of 0 changed supported claims.

**Latency gain is conditional on serving capacity**: Point count is not the speed-up multiplier, the skeleton stage is serial, fan-in is governed by the slowest expansion, and on a saturated backend the expansions become additional requests competing for the same scheduler slots, so one user's latency can improve by consuming capacity from others. The mitigation is Phase 7, which requires a paired measurement, tail percentiles, and a throughput delta before any speed-up is claimed, and the retirement rule that removes the route after 2 consecutive windows below 1.30 times.

**Latency and cost move in opposite directions**: Repeating the request, skeleton, and shared context in every expansion inflates input tokens, and the originating source records hosted-model prefill ratios of 85.79, 60.46, and 89.20 on manually suitable items. The mitigation is the explicit prefill amplification cap of 8 times, the total cost ceiling of 3 times the verified sequential baseline, and the reporting rule that a latency claim without its cost ratio is incomplete.

**Fan-out multiplies the disclosure surface**: The same request, skeleton, and shared context traverse many provider calls, logs, caches, and regions, and each additional call is another place restricted data can be retained or leaked. The mitigation is minimum-context point contracts, cache keys bound to the full authorisation scope, the approval gate before any restricted context crosses a provider boundary, and Error Type 5, which halts rather than retries on a confirmed breach.

**Every branch is an injection surface**: A compromised expansion can instruct the assembler or attempt to alter another section's policy, and a cached point can carry that instruction into a later run. The mitigation is the prohibition on point text altering policy or granting privileges, delimited untrusted data inside every contract, passing only accepted content into assembly, and cache invalidation on any authorisation-scope change.

**The empirical record is narrow and dated**: The figures transcribed here come from an evaluation of 12 models, several of them 2023-era open-source releases, judged by a model rather than by humans, over a small prompt set, with the originating source recording few prompts, judge bias, and the absence of human quality evaluation as stated limitations. Those figures were transcribed from the originating prose source and, apart from the paper's title, venue, and the successor system's reported figures, were not independently re-verified during this conversion. The mitigation is that no threshold in this guide depends on those figures being current: every operating threshold is recomputed per task family from the deployment's own paired measurements in Phase 7.

**Most numeric thresholds here are deployment defaults**: The 1.30 times speed-up margin, the 20 percent overlap ceiling, the 40 percent dependent-share ceiling, the 5 percent duplication tolerance, the 10 percent pairwise overlap incidence, the 3 to 1 depth ratio, the 8 times prefill cap, the 60 percent slowest-point share, the 15 percent straggler rate, the 85 percent router precision target, and the 20 percentage point robustness bound were chosen to be operable on first deployment rather than derived from a measured property of any model. The caps carried from the originating source, including 8 points, 4 concurrency, 2 candidates, 2 repairs, 1 retry per point, 2 re-expansions, 2 merge repairs, 1 fallback, 20 calls, 30,000 tokens, 90 seconds, and 3 times cost, are that source's stated production defaults rather than measured findings. Every one of them must be recalibrated against observed outcomes per task family, and none should be cited as evidence.

**Serving-level and model-level acceleration are out of scope**: Token-level decoding optimisations, key-value cache management, continuous batching, and successor systems that move parallel structure into model weights or a decoder are not agent-invocable and are excluded from the framework. They matter only as an explanation of why a client-side latency gain is conditional: a serving stack that already saturates its batches leaves less headroom for fan-out, and a successor system's reported advantage over this method is that system's claim, not evidence that a client-side implementation acquires dependency safety. The mitigation is the empirical requirement in Phase 7, which decides the route on the deployment's own measurements rather than on any published comparison.

**Structural conformance is not a good answer**: A run can satisfy every checkpoint here, release inside its deadline, and still answer a poorly framed request or decompose it into the wrong points. The framework detects malformed parallelism, not misdirected purpose, and no checkpoint substitutes for review of the deliverable list itself.

***

## VI. Conclusion and Summary

Skeleton-of-Thought is a scheduling discipline applied to answer text. It buys wall-clock time by generating independent sections at the same time, and it buys nothing else. Every difficulty the method presents follows from that single trade: the outline must be right before any content exists, the points must be genuinely independent before they are dispatched, the sections must be reconciled after they are written separately, and the latency gain must be measured because it is conditional on capacity the deployment does not control.

The three commitments that make the method safe are narrow and mechanical. Independence is computed by software over every point pair and is never inferred from an outline's flat appearance, because a point that consumes a sibling's generated value produces incoherence or duplication that no reconciliation pass repairs. The skeleton is gated on full coverage and bounded overlap under a fixed revision bound, because it is the only artifact that cannot be corrected later. Assembly is deterministic, ordered by stable identifier, and forbidden from inventing content, because the alternative is a merge component silently deciding what the answer says.

A team introducing the method should measure a sequential baseline first and keep measuring it. Route a single task family, hold the gate margin at a level that survives queue variance, and compare paired runs on latency, tail latency, cost, throughput, and category-stratified quality before enabling a second family. Where the measurement does not show a gain, retire the route for that family and record the evidence, since a method whose whole purpose is latency is refuted by a latency measurement rather than defended by its structure.

**Key Success Factors**:

- **Independence before concurrency**: Points carrying an unresolved dependency edge are never expanded concurrently, and the dependent subset expands sequentially in topological order.
- **Skeleton gated before content**: Coverage is complete, overlap is bounded, and revision is capped, because the outline is committed before any expansion exists and cannot be repaired afterwards.
- **Deterministic assembly**: Sections are ordered by stable identifier, never by completion order, and no missing content is regenerated at merge time.
- **Bounded reconciliation**: Duplication, contradiction, and terminology drift are measured against stated tolerances, and a substantive conflict routes to verification rather than to an editorial guess.
- **Measured latency, disclosed cost**: Every speed-up claim comes from a paired run with tail percentiles and a cost ratio beside it, and a throughput loss is reported as a capacity transfer.
- **Honest framing**: Parallel structure, section agreement, and the visible skeleton are never presented as evidence of correctness or as a view of any internal reasoning.

By following this guide, AI agents can apply concurrency only where an answer genuinely decomposes into independent parts, reconstruct one coherent response from separately generated sections, and retire the route on evidence when the latency it exists to buy does not arrive.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; except where an entry is marked verified, they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. Two entries were retrieved and confirmed during conversion and are marked accordingly.

**Corpus pointers**:

- `Production Guide to Skeleton-of-Thought` — the originating prose guide from which this operational guide was derived. Source of the two-stage method description, the independence condition and its four tests, the category exclusions, the routing discipline and its false-positive asymmetry, the eight-step production workflow and its hard caps, the assembly and coherence-repair rules, the failure-mode inventory covering coverage gaps, overlap, injection, non-deterministic assembly, silent truncation, uneven branch quality, and disclosure amplification, and the metric definitions for speed-up, cost ratio, coverage, redundancy, partial failure, and router performance. It carries inline citations to the primary literature and to provider and standards documentation; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/reasoning/guide_LeastToMostReasoning.md` — companion guidance on ordered decomposition, in which subproblems are solved in sequence and each answer feeds the next. It owns the dependent case that Section 1.3 excludes from this guide; this guide owns independent decomposition for parallel expansion, and the two are complementary rather than overlapping.
- `advanced_task_guides/reasoning/guide_ChainOfThoughtReasoning.md` — companion guidance on sequential derivation, applicable wherever the applicability gate in Section 1.3 rejects a request as a single connected argument.
- `advanced_task_guides/reasoning/guide_ChainOfVerification.md` — companion guidance on independently verified claim revision, applicable to the release verification set in Step 6.3 and to the routing of substantive contradictions in Step 5.3.
- `advanced_task_guides/reasoning/guide_SelfConsistency.md` — companion guidance on repeated independent attempts adjudicated by agreement. Its samples are redundant by design where the points here are disjoint by design, and its independence-tier vocabulary is the reason this guide never treats section agreement as corroboration.
- `advanced_task_guides/reasoning/guide_MetacognitiveMonitoring.md` — companion guidance on calibrated signals for an external control layer, applicable to the router calibration and abstention decisions in Step 7.3.
- `advanced_task_guides/reasoning/guide_TreeOfThought.md` — companion guidance on bounded search under a declared budget, applicable to the budget ledger and cap discipline in Step 1.1.
- `advanced_task_guides/reasoning/guide_GraphOfThought.md` — companion guidance on reasoning over a dependency graph of typed intermediate results in which a node may have several parents, covering the typed edge vocabulary, the merge admission check, incremental cycle prevention, and invalidation propagated through hard edges. That guide names this method as the fan-out and fan-in subpattern usable inside such a graph, and the boundary holds in both directions: the independence tests in Section 1.3 here decide which nodes may expand at the same time, while merging their results and reconciling conflicting evidence belongs to it rather than to the assembly step in Phase 5.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on control decisions over an active reasoning process, applicable to the gate verdicts in Phase 1 and the fallback selection in Step 6.1.

**External references**: The numbering below is the numbering used by the inline markers in Section I. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*The method, its evaluation, and its successors*

1. Ning et al., *Skeleton-of-Thought: Prompting LLMs for Efficient Parallel Generation* — https://arxiv.org/abs/2307.15337 — title, authors, and ICLR 2024 venue verified during conversion.
2. Skeleton-of-Thought, full paper text — https://arxiv.org/html/2307.15337
3. LIMA — https://arxiv.org/abs/2305.11206
4. FastChat — https://github.com/lm-sys/FastChat
5. APAR — https://arxiv.org/abs/2401.06761
6. Jin et al. — https://proceedings.mlr.press/v267/jin25a.html
7. *Plato: Plan to Efficiently Decode for Large Language Model Inference* — https://arxiv.org/abs/2402.12280 — title and its reported 68 percent throughput improvement and 90 percent quality net-win rate verified during conversion.

*Neighbouring reasoning methods and their boundaries*

8. Zhou et al. — https://arxiv.org/abs/2205.10625
9. Wei et al. — https://arxiv.org/abs/2201.11903
10. Besta et al. — https://arxiv.org/abs/2308.09687
11. DeepSeek-R1 — https://arxiv.org/abs/2501.12948

*Decoding and serving acceleration, recorded as context rather than as method*

12. Leviathan et al. — https://arxiv.org/abs/2211.17192
13. Chen et al. — https://arxiv.org/abs/2302.01318
14. Kwon et al. — https://arxiv.org/abs/2309.06180

*Provider limits, latency, and reasoning-effort documentation*

15. OpenAI, *Rate limits* — https://platform.openai.com/docs/guides/rate-limits
16. Anthropic, *Rate limits* — https://docs.anthropic.com/en/api/rate-limits
17. OpenAI, *Latency optimization* — https://platform.openai.com/docs/guides/latency-optimization
18. OpenAI, *Batch API* — https://platform.openai.com/docs/guides/batch
19. OpenAI, *Reasoning best practices* — https://developers.openai.com/api/docs/guides/reasoning-best-practices
20. Anthropic, *Extended thinking* — https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking

*Concurrency, streaming, telemetry, and lineage*

21. Python, *asyncio tasks and coroutines* — https://docs.python.org/3/library/asyncio-task.html
22. Ray, *Limiting concurrently running tasks* — https://docs.ray.io/en/latest/ray-core/patterns/limit-running-tasks.html
23. MDN, *Using server-sent events* — https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
24. OpenTelemetry, *GenAI model spans* — https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md
25. OpenTelemetry, *GenAI agent spans* — https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md
26. W3C, *PROV-O: The PROV Ontology* — https://www.w3.org/TR/prov-o/

*Application security risks amplified by fan-out*

27. OWASP, *Prompt injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
28. OWASP, *Sensitive information disclosure* — https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/
