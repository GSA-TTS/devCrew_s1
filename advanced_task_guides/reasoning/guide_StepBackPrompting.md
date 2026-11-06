# Step-Back Prompting

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Step-back prompting constitutes the task family of answering a specific question by first deriving a more general question or principle from it, answering that general question, and composing the general answer back onto the original case. This guide provides AI agents with a structured protocol across seven phases. It specifies an applicability gate that suppresses the method wherever the question is already concrete and its difficulty lies in a local fact, a computation, or a format rather than in selecting a governing rule. It specifies a two-sided generality test that rejects a derived question which is not strictly more general than the original, and equally rejects one whose answer cannot change the original's answer. It fixes an evidence standard under which a general answer resting on model recall alone is marked unsupported, capping the confidence of every specific answer derived from it. It specifies a composition check establishing that the specific answer follows from the general one by ablating each cited clause, rather than accepting a narrative merely adjacent to it. It closes with a bounded re-derivation path and a measurement pass comparing the method against a direct-answer baseline at matched token, cost, call, and latency budgets, so that abstraction is paid for in verified outcomes rather than in longer output.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Step-back prompting**: A two-stage inference procedure in which a model first derives a question or principle at a higher level of abstraction than the request, then answers the request using that material. The defining move is upward abstraction followed by downward application. It is distinct from adding intermediate reasoning steps, from decomposing a problem into subproblems, and from requesting a longer explanation.

**Original question**: The request as received, together with its authorized context, output schema, and acceptance tests. It is never discarded, never paraphrased into the derived question, and never replaced by the general answer.

**Derived general question**: The question produced by the abstraction stage. It sits above the original in generality and below the enclosing domain, and it is admitted only after passing the generality test in Section 1.2.

**General answer**: The answer to the derived general question, expressed as one or more numbered principle clauses, each carrying a scope, an assumption set, and an exception set. It is a hypothesis until grounded.

**Principle clause**: One atomic, independently checkable statement inside the general answer, addressable by identifier so that a mapping row, a grounding artifact, and an ablation can each refer to it exactly.

**Composition**: The stage in which the general answer is applied to the original question to produce the specific answer, accompanied by an explicit mapping from principle clauses to case facts.

**Specific answer**: The released response to the original question, carrying the mapping, the cited evidence, the addressed exceptions, and a declared confidence band.

**Generality band**: The interval of abstraction that is simultaneously above the original question and still determinative of it. A derived question outside the band on either side is rejected.

**Over-abstraction**: The failure in which the derived question is so general that its answer constrains nothing about the original case. Its signature is a general answer that remains true under every candidate specific answer.

**Under-abstraction**: The failure in which the derived question restates the original at unchanged specificity. Its signature is a derived question that admits no concrete instance other than the original.

**Determinativeness**: The property that the answer to the derived question, if changed, changes the answer to the original question. It is the lower boundary of the generality band and is established by substitution, not asserted.

**Grounding**: The act of establishing a principle clause against an artifact outside the model that produced it, being a retrieved source span or a reproducible deterministic execution record.

**Evidence class**: The three-way classification of what supports a principle clause: an authoritative retrieved source, a deterministic derivation, or model recall alone. The third class never closes a material clause.

**Unsupported mark**: A deterministic stamp applied to any principle clause whose only support is model recall. The mark propagates to every specific answer derived from that clause and caps its confidence band. The model tier may not remove it.

**Mapping row**: One record binding a principle clause identifier, a case fact identifier, and a relation drawn from a closed vocabulary: activates, limits, defeats, or not applicable.

**Load-bearing clause**: A cited principle clause whose removal or negation changes the specific answer. A cited clause that is not load-bearing is decorative and indicates an unfaithful composition.

**Principle channel and case channel**: The two labelled, separately budgeted regions of assembled context. The principle channel holds the general answer and its grounding artifacts; the case channel holds the evidence specific to the original question. They are never merged, and neither substitutes for the other.

**Re-derivation**: One bounded attempt to replace a rejected derived question after a named trigger, executed without resetting any counter or budget.

**Direct-answer baseline**: The cheapest valid route that answers the original question without abstraction, being a deterministic function, a single retrieval, or a single direct model call. It is run first and it is the comparison against which the method is measured.

**Matched-budget control**: A baseline run given the same token, cost, model-call, or latency budget as the step-back route, so that a measured advantage is attributable to abstraction rather than to additional computation.

**Abstraction-attributable gain**: The paired outcome difference between the full step-back route and a masked route receiving the identical original question and case evidence with the derived question and general answer removed.

**Defect code**: A categorical label from a closed vocabulary recorded whenever a gate rejects an artifact, naming the criterion that failed so that repair is targeted rather than open-ended.

**Applicability gate**: The deterministic decision, taken before any abstraction call, returning invoke, suppress, or a named cheaper route.

### 1.2 The Generality Band and the Two Failure Modes of Abstraction

Abstraction is lossy compression performed for a purpose. It maps several surface forms onto a schema, law, invariant, mechanism, or policy rule that supports transfer. It is useful only where what it discards is irrelevant variation and what it retains is the structure that decides the case. Both boundaries of that interval are failure modes, and neither is detectable by inspecting the derived question alone.

**Over-abstraction**: A derived question can be lifted so far that its answer is compatible with every candidate answer to the original. A request about the pressure of an ideal gas under a specified temperature change, lifted to a question about the concepts of physics, produces a general answer that no reasoning can convert into a specific one. The signature is a general answer that survives unchanged under substitution of the specific answer, and the consequence is a route spending two model calls and a retrieval round to return the baseline's answer with additional preamble. Over-abstraction also erases decisive exceptions: a clinical guideline stripped of its contraindications, or a compliance rule stripped of its thresholds and safe harbours, reads as correct and licenses a wrong specific answer.

**Under-abstraction**: A derived question can fail to rise at all, restating the original with synonyms or with one particular removed. The signature is a question governing no concrete instance other than the original, and the consequence is the same cost with no recall gain and no principle to ground.

**The band is relative, not absolute**: The same derived question can be over-abstract for one request and correctly abstract for another, because the band is defined by the original question rather than by a fixed level of the subject matter. No cached generality judgement transfers across task families.

**Admission is two-sided and mechanical**: A candidate is admitted only where it passes every criterion below. The model tier proposes the evidence each criterion consumes; the deterministic tier evaluates the criterion and records the verdict. A candidate failing any criterion is rejected with its defect code and is never repaired by an unbounded instruction to abstract better.

**Generality Test Criteria and Their Defect Codes**:

| Criterion | Deterministic admission test | Defect code | Action on failure |
| :-- | :-- | :-- | :-- |
| Instance breadth | At least 3 concrete instances besides the original, distinct after normalization of entity and relation signature | TOO_NARROW | Reject; request 1 targeted repair naming the criterion |
| Determinativeness | Two mutually exclusive candidate general answers yield 2 different specific answers under the output schema | NOT_DETERMINATIVE | Reject; the candidate is above the band and is not repaired at the same level |
| Scope preservation | Every decision-relevant scope dimension in the contract appears in the derived question or its declared filter set | SCOPE_ERASED | Reject; request 1 repair restoring the named dimensions |
| Non-leadingness | The derived question contains no value from the original's answer slot and no baseline answer token | ANSWER_LEAKED | Reject; the candidate presupposes the answer it is meant to establish |
| Answerability | At least 1 permitted source class or deterministic tool can in principle answer the derived question | UNANSWERABLE | Reject; a question no permitted source can close cannot be grounded |
| Retrieval utility | Dispatching the derived question returns at least 1 candidate absent from the original question's results at equal depth | NO_RETRIEVAL_GAIN | Reject where retrieval is permitted; the abstraction added no reachable material |

**Consequence of a failed test**: Rejection is bounded. At most 2 candidate derived questions are generated per request and at most 2 repairs are permitted across them. Where both candidates fail, or where 2 successive candidates introduce no concept absent from the first, the applicability gate's verdict is overturned in retrospect: the request is routed to the direct baseline, the outcome is recorded as a dominated step-back attempt, and the failure hypothesis that licensed the route is logged for policy revision. A request is never carried forward on a candidate that failed a hard criterion, and a NOT_DETERMINATIVE candidate is never repaired by widening it further.

### 1.3 Applicability Determination: Observable Condition and Its Converse

The method helps where the difficulty of a question lies in retrieving or selecting the right governing principle. It adds cost with no benefit where the question is already concrete. Both conditions are observable before the abstraction call, and the gate evaluates them deterministically at a cost not exceeding 2 percent of the direct-execution budget.

**Invocation condition**: The direct-answer baseline has been run and has failed its acceptance tests, and the failure is attributable to principle selection rather than to a local defect. The attributable signals are: a baseline error classified as wrong governing rule or no rule applied, rather than missing local fact, arithmetic error, extraction error, or schema violation; a retrieval profile in which the original query returns fewer than 3 candidates above the match floor while a category-level probe returns at least 3, which is the abstraction gap the retrieval corpus exposes; a task-family log in which at least 3 surface-variant requests resolve to one answer schema, indicating a reusable rule exists; and the availability of at least 1 permitted principle source or deterministic tool able to establish that rule.

**Converse condition**: The request is already concrete, meaning its answer turns on one retrievable local fact, a deterministic computation, an extraction, a classification, a summarization, or a format transformation; or the original question already states the governing principle it would be lifted toward; or the decisive evidence is a quoted clause, a current value, or a named exception that a general statement cannot supply. In these cases the derived question is not merely unhelpful, it is negative: it consumes 1 to 2 additional model calls and up to 3 retrieval rounds, and its general answer competes for context with the case evidence that actually decides the request.

**Applicability Gate Decision Table**:

| Observable condition | Available principle source | Gate verdict |
| :-- | :-- | :-- |
| Baseline fails; error classified as wrong or absent governing rule | At least 1 authoritative source or tool | Invoke the full route |
| Original query recall low, category-level probe recall adequate | Retrieval index permitted for the tenant | Invoke; issue the derived question alongside the original |
| At least 3 surface variants resolve to one answer schema | Schema documented or derivable | Invoke; the schema is the target of abstraction |
| Baseline passes acceptance tests | Any | Suppress; release the baseline answer |
| Answer turns on one local fact or quoted clause | Any | Suppress; route to direct retrieval |
| Answer computable by a deterministic function or query | Tool available | Suppress; route to the tool |
| Question states its own governing principle | Any | Suppress; apply the stated principle directly |
| Risk tier requires authoritative guidance, no such source permitted | None | Suppress; abstain or escalate for human review |
| Contract latency ceiling below 2 model stages | Any | Suppress; record the ceiling as the reason |
| Baseline fails on arithmetic, extraction, or schema | Any | Suppress; repair the failing component |

**Numeric gate rules**: Invoke only where at least 1 invocation signal holds and at least 1 permitted principle source exists; where no principle source exists, the general answer could only be model recall, and the route is suppressed rather than run to produce an unsupported result. Suppress in the lowest risk tier where estimated total route cost exceeds 3 times the direct baseline cost. Suppress where estimated added latency exceeds the contract's stated p95 ceiling. Suppress where the derived question would cross a tenant, jurisdiction, or authorization boundary that the original question does not, because a broader query can reach material the narrower one was not permitted to see.

**Default budget caps**: Fix every cap before inference and never reset a counter after re-derivation. The deployment defaults are 2 abstraction candidates, 2 abstraction repairs, 3 principle-retrieval rounds, 8 principle chunks and 8 case chunks admitted before reranking, 1 global re-derivation, 2 composition attempts, 2 composition repairs, 16 model calls, 12 retrieval calls, 30,000 total tokens, 60 seconds wall-clock, and total cost no greater than 3 times the best cheaper baseline. Exhaustion of any cap terminates the route through a declared exit rather than through an extension.

### 1.4 Execution Tier Partition and Authority

Step-back prompting fails most often at the boundary between what software must decide and what a model may decide, because both of its stages produce fluent text whose defects are invisible to inspection. The partition below is binding on every phase of Section II, and every step names the tier that owns it.

**Deterministic tier**: Software, scripts, schema validators, index queries, and tools own everything requiring exactness, reproducibility, auditability, or arithmetic. This tier evaluates the applicability gate and its numeric rules; keeps the generality test bookkeeping, being the instance enumeration and its duplicate detection, the scope dimension checklist, the answer-leak scan, the substitution comparison for determinativeness, the candidate counter, and the repair counter; executes retrieval for grounding, including authorization enforcement, query dispatch, deduplication by stable chunk identity, rank fusion arithmetic, and capture of corpus version, chunk identifier, effective date, authority class, and content hash; classifies the evidence class of every principle clause and applies the unsupported mark; assembles the context manifest and enforces the separate token budgets of the principle and case channels; performs composition verification, being mapping coverage arithmetic, orchestration of the clause ablations, tallying of independent entailment verdicts, and exception coverage accounting; and performs cost accounting, being the budget ledger, the matched-budget controls, the paired baseline comparison, and every metric reported in Sections II and III.

**Model tier**: LLM calls own work requiring open-vocabulary judgement that no deterministic rule covers. This tier derives the candidate general question; enumerates the concrete instances the generality test consumes; states the mutually exclusive candidate general answers the determinativeness substitution consumes; answers the derived general question as numbered principle clauses with declared scope, assumptions, and exceptions; extracts principle clauses from retrieved spans; composes the specific answer with its mapping rows; and adjudicates residual semantic criteria that no deterministic checker covers. This tier never enforces authorization, never counts its own attempts, never computes a value a gate depends on, never removes an unsupported mark, and never declares its own composition faithful.

**Hybrid tier**: Every stage of this method is hybrid in one specific sense: the model proposes an artifact and a deterministic check admits it. Abstraction is hybrid because the model writes the derived question and the generality test admits it. Grounding is hybrid because the model extracts clauses and the deterministic tier verifies each against a retrieved span, a tool execution record, or neither. Composition is hybrid because the model writes the mapping and the ablation harness determines whether the cited clauses were load-bearing.

**Authority on disagreement**: The deterministic tier holds authority in every conflict. Where the model asserts a derived question is more general and the instance enumeration yields fewer than 3 distinct instances, the candidate is rejected. Where the model asserts a principle is established and no source span or execution record supports it, the clause carries the unsupported mark regardless of the stated confidence. Where the model asserts the specific answer follows from the general one and the ablation finds no load-bearing clause, the composition is rejected. Where the model proposes a further attempt and a counter is exhausted, the route exits.

**A general answer accepted without grounding is marked, not discarded**: The unsupported mark is a recorded state, not a deletion. An unsupported clause may still organise a response where the risk tier permits, but the deterministic tier caps the confidence band of every specific answer derived from it, forbids that answer from closing a material claim, and requires the response to state plainly that the principle is model-generated rather than sourced. Suppression of that statement is a release defect.

**Tier Ownership by Artifact**:

| Artifact | Owning tier | Rejection rule enforced deterministically |
| :-- | :-- | :-- |
| Task contract and budget ledger | Deterministic | A missing cap or an unbounded dimension halts the route before the baseline |
| Direct-answer baseline result and error class | Deterministic | An unrun baseline blocks the applicability gate |
| Applicability verdict | Deterministic | Invoke without a permitted principle source is refused |
| Candidate derived question | Model proposes, deterministic admits | Any hard criterion in Section 1.2 rejects with its defect code |
| Instance enumeration and substitution pair | Model proposes, deterministic counts | Duplicate instances after normalization do not count toward the floor of 3 |
| Retrieval dispatch and provenance record | Deterministic | A span without corpus version, identifier, date, and hash is not admissible |
| Principle clause set | Model proposes, deterministic classifies | A clause with no scope or no exception field is not admitted |
| Grounding verdict and unsupported mark | Deterministic | Model recall alone never yields a grounded verdict |
| Context manifest and channel budgets | Deterministic | Principle content in the case channel voids the manifest |
| Specific answer and mapping rows | Model proposes, deterministic verifies | A material conclusion with 0 mapping rows is rejected |
| Clause ablation results | Deterministic | Zero load-bearing clauses rejects the composition |
| Cost and matched-budget ledger | Deterministic | An unmeasured control blocks the release verdict |

### 1.5 Boundary Against Retrieval-Side Step-Back and Neighbouring Reasoning Patterns

**Retrieval-side step-back**: Step-back also exists as a query transformation, where a broader query is issued alongside the original to repair an abstraction gap between a category-level information need and a corpus indexed at case level. That role is owned by the corpus guide named in Section VII, and its terminology is adopted here without modification: the artifact is a step-back formulation, it treats the abstraction-gap failure class, it is issued alongside the original query and never instead of it, and its generated text is a retrieval instrument that is never cited, never displayed as a source, and never counted toward support. This guide owns the reasoning role, in which the derived question's answer is load-bearing content rather than an instrument, and therefore must be grounded before any conclusion rests on it. Where a request needs both, the retrieval guide governs dispatch, authorization, deduplication, fusion, and intent preservation for the queries, and this guide governs the grounding of the general answer and its composition onto the case. The original query is never dropped from retrieval under either guide.

**Chain-of-thought reasoning**: Intermediate reasoning proceeds through the instance at unchanged representational level. Step-back changes the level first and only then reasons. The two combine only where a derived question has been admitted and the application still requires several dependent steps; the combination doubles the failure surface and is justified by a separate ablation rather than by expectation.

**Self-consistency sampling**: Repeated sampling concentrates support for one answer across attempts at one task. It is orthogonal to abstraction and is applied, where warranted, to the composition stage rather than to the abstraction stage, because agreement among derived questions drawn from one model measures the model's habit rather than the correctness of the principle.

**Chain-of-verification**: Claim-level verification of a produced answer belongs after composition and never substitutes for grounding. Verification tests whether the released claims survive independent questioning; grounding tests whether the principle they rest on was ever established. An answer that passes verification while its principle carries the unsupported mark is an answer whose claims are consistent with an unestablished rule.

**Tree-of-thought reasoning**: Search over partial solutions addresses problems whose difficulty is exploring alternatives under lookahead. Step-back is not a search: it produces one derived question, tests it, and either proceeds or exits. Where the difficulty is comparing alternatives rather than selecting a governing rule, the search method is the correct route.

**Metacognitive monitoring**: The applicability gate consumes signals rather than producing them. Where a deployment already operates a monitor layer, the baseline error class, the retrieval recall profile, and the calibration record are read from it rather than recomputed.

**Self-correction without external feedback**: A model asked to correct its own principle or composition, with no external test and no new evidence, can degrade a correct result. Every repair path here supplies a named defect code and the evidence that produced it, and no repair is licensed by an instruction to reconsider.

**Reported magnitudes and their boundary**: For one instruction-tuned model family the original work reported high-school Physics accuracy rising from 66.4 percent to 73.2 percent and Chemistry from 70.9 percent to 81.8 percent; on a grade-school arithmetic benchmark it reported 84.3 percent against 84.4 percent for zero-shot chain-of-thought and 84.5 percent for one-shot standard prompting, which is no gain. On a temporal question-answering benchmark it reported 41.5 percent for the baseline, 57.4 percent with retrieval, 66.0 percent with step-back, and 68.7 percent with both. Its error analysis reported more than 90 percent of remaining Physics errors at the reasoning step rather than the abstraction step, 45 percent of remaining temporal-question errors as retrieval failures despite an on-target abstraction, and correction of 39.9 percent of baseline errors while turning 5.6 percent of previously correct predictions wrong. These figures were verified during conversion against the paper's public rendering. They are prompt-specific and model-specific results, not an expected deployment lift, and the last establishes that the intervention is asymmetric rather than harmless.

***

## II. Operational Framework: Grounded Abstraction and Verified Composition

The framework runs only where the applicability gate in Section 1.3 returns invoke. Phases 1 through 5 are sequential. Phase 6 is entered only on a named trigger and returns control to Phase 2 exactly once. Phase 7 runs after release and governs whether the route is retained. Every counter a phase increments is held by the deterministic tier.

### Phase 1: Contract Establishment and Applicability Determination

**Objective**: Fix the task contract and the budget ledger, establish what the cheapest valid route already achieves, and decide whether abstraction is warranted, before any abstraction call is issued.

#### Step 1.1: Establish the Task Contract and Budget Ledger

**Required Actions**:

- Record the objective, output schema, acceptance tests, domain, risk tier, and abstention rule, so that every later verdict is evaluated against a declared target rather than an impression.
- Record the scope dimensions that are decision-relevant for this request, drawn from entity type, relation type, effective date, jurisdiction, unit system, population, and tenant, since these are the dimensions the generality test protects.
- Record the permitted principle source classes, the prohibited sources, the tool permissions, and the authorization scope that any broader query must not exceed.
- Populate the budget ledger with every cap in Section 1.3, assigning a numeric limit to each of model calls, retrieval calls, tokens, wall-clock seconds, cost, candidates, repairs, retrieval rounds, and re-derivations.
- Halt and request clarification, or apply a documented conservative default, where a mandatory contract field cannot be populated.

**Required Outputs**:

- A task contract record with objective, output schema, acceptance tests, risk tier, and abstention rule.
- A scope dimension list naming every dimension the derived question must preserve.
- A permitted source and tool inventory with its authorization scope.
- A budget ledger with a numeric limit against every bounded dimension.

**Quality Checkpoints**:

- Every acceptance test returns pass or fail without interpretation; an untestable criterion halts the route before the baseline runs.
- Every budget dimension carries a numeric limit; an unbounded dimension halts the route.
- The scope dimension list is non-empty, since a request with no decision-relevant scope has nothing for abstraction to preserve.
- The authorization scope of the permitted sources is recorded, so that a later broader query can be checked against it rather than assumed compliant.

***

#### Step 1.2: Execute the Direct-Answer Baseline and Classify Its Failure

**Required Actions**:

- Execute the cheapest valid route that answers the original question without abstraction, selecting a deterministic function or database query where one decides the request, otherwise a single retrieval, otherwise a single direct model call.
- Evaluate the baseline output against the contract's acceptance tests and release it immediately where every test passes.
- Classify any failure into exactly 1 error class from the closed vocabulary: wrong governing rule, no rule applied, missing local fact, arithmetic error, extraction error, schema violation, or refusal.
- Record the baseline's token count, cost, model calls, retrieval calls, and latency, since these become the matched-budget reference in Phase 7.
- Record a retrieval recall profile where retrieval is permitted, comparing candidates returned by the original query against candidates returned by a category-level probe at equal depth.

**Required Outputs**:

- A baseline result record with its acceptance verdict per test.
- A single error class assignment where the baseline failed, with the evidence that produced it.
- A baseline cost record covering tokens, calls, cost, and latency.
- A retrieval recall profile where retrieval is permitted, or a recorded exemption where it is not.

**Quality Checkpoints**:

- The baseline was executed and measured; an estimated baseline is not admissible as the comparison reference.
- Exactly 1 error class is assigned; a multi-class assignment is resolved before the gate is evaluated.
- A passing baseline terminates the route with a release, and no abstraction call follows it.
- The cost record is complete on all 4 dimensions, since a missing dimension makes the matched-budget control in Phase 7 uncomputable.

***

#### Step 1.3: Evaluate the Applicability Gate and Bind the Route

**Required Actions**:

- Evaluate every row of the applicability gate decision table against the recorded error class, recall profile, task-family log, and permitted source inventory.
- Bind the verdict to one of three outcomes: invoke the step-back route, suppress and name the cheaper route taken instead, or suppress and abstain where the risk tier forbids model-generated guidance and no authoritative source is permitted.
- Record the failure hypothesis that licenses an invoke verdict, naming the governing rule believed to be missing and the source class expected to establish it.
- Confirm the gate's own cost did not exceed 2 percent of the direct-execution budget, and reduce the gate to its deterministic signals where it did.
- Confirm that the derived question, once generated, would remain inside the authorization scope recorded in Step 1.1.

**Required Outputs**:

- A gate verdict record with the rows that fired and the numeric rule that decided it.
- A named failure hypothesis where the verdict is invoke.
- A named substitute route where the verdict is suppress.
- A gate overhead measurement expressed as a percentage of the direct-execution budget.

**Quality Checkpoints**:

- An invoke verdict names at least 1 permitted principle source; a verdict naming none is converted to suppress.
- The failure hypothesis names a specific missing rule, not a general observation that the task is hard.
- A suppress verdict names the substitute route explicitly rather than leaving the request unrouted.
- Gate overhead is at or below 2 percent of the direct-execution budget.

***

### Phase 2: General-Question Derivation and the Generality Test

**Objective**: Produce exactly 1 derived general question that is strictly more general than the original and still determinative of it, or exit to the direct route with a recorded dominance verdict.

#### Step 2.1: Derive the Candidate General Question

**Required Actions**:

- Issue 1 abstraction call producing 1 candidate derived question, its declared target artifact type from law, schema, mechanism, taxonomy, history, or invariant, and its declared scope filter set.
- Require the candidate to be answerable from the permitted source classes recorded in Step 1.1 and to preserve every scope dimension on that step's list.
- Require the candidate to be phrased without presupposing the answer to the original question, and without naming the entity or value that occupies the original's answer slot.
- Require the model tier to accompany the candidate with at least 3 concrete instances other than the original that the candidate governs, and with 2 mutually exclusive candidate general answers for use in the determinativeness substitution.
- Increment the candidate counter and refuse generation where it stands at its cap of 2.

**Required Outputs**:

- One candidate derived question with its target artifact type and scope filter set.
- An instance list of at least 3 concrete instances besides the original.
- A substitution pair of 2 mutually exclusive candidate general answers.
- An updated candidate counter reading against its cap.

**Quality Checkpoints**:

- The candidate is a question or a principle target, not a topic label; a bare subject name carries no answer to ground.
- The instance list contains at least 3 entries and the substitution pair contains exactly 2 entries; a short list fails the test rather than triggering an unbounded regeneration.
- The candidate names every scope dimension on the Step 1.1 list or places it in the declared filter set.
- The candidate counter does not exceed 2.

***

#### Step 2.2: Apply the Two-Sided Generality Test

**Required Actions**:

- Normalize the instance list by entity and relation signature, discard duplicates and near-duplicates of the original, and count the survivors against the floor of 3.
- Derive the specific answer implied by each member of the substitution pair, holding the case evidence fixed, and compare the 2 results under the output schema.
- Scan the candidate against the original's answer slot vocabulary and against the baseline answer where one was produced, recording any hit as an answer leak.
- Confirm each scope dimension on the Step 1.1 list appears in the candidate or its filter set, and record every dimension that does not.
- Dispatch the candidate to retrieval where retrieval is permitted, at the same depth as the original query, and count candidates returned by the derived question that the original question did not return.
- Record the verdict per criterion together with its defect code, and never record a composite pass that conceals a failed criterion.

**Required Outputs**:

- A per-criterion verdict record covering all 6 criteria of Section 1.2.
- A defect code list naming every criterion that failed.
- A distinct-instance count, a substitution comparison result, a scope dimension coverage list, and a retrieval novelty count.

**Quality Checkpoints**:

- The distinct-instance count is at least 3 after normalization; a lower count fires TOO_NARROW.
- The 2 derived specific answers differ under the output schema; identical results fire NOT_DETERMINATIVE.
- The answer-leak scan returns 0 hits; any hit fires ANSWER_LEAKED.
- The retrieval novelty count is at least 1 where retrieval is permitted; 0 fires NO_RETRIEVAL_GAIN.
- Every criterion carries an explicit verdict; an unevaluated criterion is treated as a failure.

***

#### Step 2.3: Admit One Candidate or Exit to the Direct Route

**Required Actions**:

- Admit the candidate where every criterion passed, and freeze it as the accepted derived question for the remainder of the route.
- Request exactly 1 targeted repair where the failures are confined to SCOPE_ERASED, TOO_NARROW, or ANSWER_LEAKED, supplying the defect codes and the measured values rather than an instruction to abstract differently.
- Refuse repair at the same level where NOT_DETERMINATIVE fired, and generate the second candidate at a lower level of abstraction instead, since widening a non-determinative question moves it further outside the band.
- Exit to the direct route where 2 candidates have failed, where 2 repairs have been consumed, or where a second candidate introduces no concept absent from the first.
- Record the dominance verdict on exit, naming the failure hypothesis from Step 1.3 that the outcome did not support.

**Derived Question Record Template**:

```
DERIVED_QUESTION_ID:
PARENT_REQUEST_ID:
CANDIDATE_INDEX:
TARGET_ARTIFACT_TYPE:
SCOPE_FILTER_SET:
DISTINCT_INSTANCE_COUNT:
SUBSTITUTION_RESULT:
SCOPE_DIMENSIONS_COVERED:
ANSWER_LEAK_HITS:
RETRIEVAL_NOVELTY_COUNT:
CRITERION_VERDICTS:
DEFECT_CODES:
REPAIR_COUNT:
ADMISSION_STATUS:
EXIT_ROUTE_ON_REJECTION:
```

**Required Outputs**:

- One accepted derived question, or a recorded exit with its dominance verdict.
- A derived question record populated for every candidate generated, admitted or rejected.
- An updated repair counter reading against its cap of 2.

**Quality Checkpoints**:

- Exactly 1 derived question is carried forward; a route holding 2 accepted questions is halted and reduced to 1.
- No candidate that failed a hard criterion is carried forward under any confidence statement.
- A NOT_DETERMINATIVE candidate was not repaired by further widening.
- The exit path records a dominance verdict, so that the applicability gate's licensing signal can be corrected in Phase 7.

***

### Phase 3: Grounding the General Answer

**Objective**: Establish each principle clause against an artifact outside the model that produced it, or mark the clause unsupported and cap the confidence of every conclusion that will rest on it.

#### Step 3.1: Answer the Derived Question as Numbered Principle Clauses

**Required Actions**:

- Issue 1 call answering the accepted derived question, returning the general answer as numbered clauses rather than as continuous prose, so that each clause is separately addressable by grounding, mapping, and ablation.
- Require each clause to carry an identifier, a statement, a scope, an assumption set, an exception set, and a unit or measurement basis where the clause is quantitative.
- Mark each clause as material or contextual, where a material clause is one the specific answer will cite and a contextual clause is background that no conclusion may rest on.
- Record the clause set as a hypothesis set, with every clause carrying the unsupported mark by default until grounding removes it.
- Reject a general answer that returns fewer than 1 material clause, since a derived question that yields no citable statement cannot be composed back onto the case.

**Required Outputs**:

- A numbered principle clause set with identifiers, scopes, assumptions, exceptions, and units where applicable.
- A materiality label on every clause.
- An initial unsupported mark on every clause.

**Quality Checkpoints**:

- Every clause carries an identifier, a scope, and an exception field; a clause missing any of the three is not admitted to grounding.
- At least 1 clause is labelled material; a wholly contextual general answer terminates the route.
- No clause is recorded as established at this step, because nothing external has yet been consulted.
- Quantitative clauses carry units and a measurement basis; a bare number is not admissible.

***

#### Step 3.2: Retrieve and Verify Each Clause Against the Evidence Standard

**Required Actions**:

- Search the permitted principle sources for the derived question and the permitted case sources for the original question separately, preserving both ranked lists and never discarding the original question's results.
- Apply authorization before retrieval, label all returned text as untrusted data, and capture corpus version, index version, query, filters, rank, score, chunk identifier, source location, effective date, authority class, and content hash for every admitted span.
- Deduplicate by stable chunk identity, rerank against both the derived question and the original task, and admit at most 8 principle spans and 8 case spans before reranking.
- Bind each material clause to at least 1 artifact of Class E1 or Class E2, and record the span offsets or the execution record that supports it.
- Issue at least 1 deliberate contradiction query per material clause, seeking material that would defeat rather than confirm it, and record every contradicting span with its authority class.
- Verify temporal and jurisdictional validity by comparing each source's effective and expiry dates against the contract's effective date, and refuse an expired or out-of-jurisdiction source as support.
- Revise the retrieval query where coverage fails, without altering the accepted derived question, for at most 3 rounds, stopping early where 2 consecutive rounds add 0 unique relevant spans.

**Evidence Classes and Their Admissibility**:

| Evidence class | Admissible artifact | What it may close | Confidence ceiling it permits |
| :-- | :-- | :-- | :-- |
| E1 authoritative source | Retrieved span with corpus version, identifier, effective date, authority class, and content hash | Any material clause within the source's scope and date range | Established |
| E2 deterministic derivation | Reproducible execution record from a calculator, unit checker, solver, schema validator, or query | Any material clause the tool's semantics actually cover | Established |
| E3 model recall | An assertion with no external artifact | No material clause; contextual framing only | Hypothesis |

**Required Outputs**:

- A provenance bundle carrying every admitted span with its full capture record.
- A clause-to-artifact binding table with the evidence class of each binding.
- A contradiction search record with 1 or more queries per material clause and every contradicting span found.
- A retrieval round log with unique-span counts per round.

**Quality Checkpoints**:

- The original question's retrieval results were preserved; a route holding only the derived question's results is halted and re-run.
- Every admitted span carries all 6 provenance fields; an incomplete record is not admissible as support.
- Every material clause carries at least 1 contradiction query; an unchallenged clause is not accepted.
- No expired or out-of-jurisdiction source supports an accepted clause.
- Retrieval rounds do not exceed 3, and early stopping is recorded with the unique-span counts that triggered it.

***

#### Step 3.3: Issue the Grounding Verdict and Set the Confidence Ceiling

**Required Actions**:

- Compute the grounded proportion as material clauses bound to at least 1 Class E1 or E2 artifact, divided by all material clauses.
- Assign the grounding verdict from the closed vocabulary: GROUNDED at a grounded proportion of at least 0.90 with 0 unresolved contradictions; PARTIALLY_GROUNDED between 0.50 and 0.89; UNSUPPORTED below 0.50; and CONTRADICTED where any material clause is opposed by a span of equal or higher authority class that the grounding did not resolve.
- Remove the unsupported mark from each clause that acquired a Class E1 or E2 binding, and leave it in place on every other clause.
- Set the confidence ceiling for the whole route from the verdict: established under GROUNDED, qualified under PARTIALLY_GROUNDED, and hypothesis under UNSUPPORTED, with CONTRADICTED blocking composition entirely.
- Count enumerated exceptions lacking their own supporting artifact and record them as unenumerated, capping the ceiling at qualified where the count exceeds 0.
- Enter Phase 6 on a CONTRADICTED or UNSUPPORTED verdict where the re-derivation cap remains and the risk tier requires authoritative support; otherwise proceed under the assigned ceiling or exit through abstention.

**Required Outputs**:

- A grounded proportion expressed to 2 decimal places with its numerator and denominator.
- A grounding verdict drawn from the 4-value vocabulary.
- A route confidence ceiling drawn from the 3-value band vocabulary.
- An unenumerated exception count with the clause identifiers it attaches to.

**Quality Checkpoints**:

- The grounded proportion is computed from the binding table rather than asserted by the model tier.
- Every clause retaining the unsupported mark is flagged for disclosure in the released response.
- A CONTRADICTED verdict blocks composition; it is never downgraded to a warning attached to a released answer.
- The confidence ceiling is recorded before composition begins, so that no later stage can raise it.
- Where the risk tier requires authoritative guidance, an UNSUPPORTED verdict terminates the route in abstention or escalation rather than in a qualified release.

***

### Phase 4: Context Assembly and Channel Separation

**Objective**: Assemble a context in which the grounded general answer and the case evidence occupy separate, separately budgeted channels, and in which retrieved text can act as data but never as instruction.

#### Step 4.1: Assemble the Two-Channel Context

**Required Actions**:

- Build a typed context manifest carrying the original question, the accepted derived question, the principle clause set with its grounding artifacts, the case evidence with its provenance, the conflict set, the output schema, the confidence ceiling, and the remaining local budget.
- Place principle content in the principle channel and case content in the case channel, labelling each channel explicitly and never merging them, so that the composition stage can be required to relate one to the other rather than to blend them.
- Attach the mapping contract to the manifest, obliging the composing call to state which case facts activate, limit, or defeat each cited clause.
- Exclude rejected candidate derived questions, duplicate spans, verifier rationales, and broad context unrelated to either channel.
- Position the governing constraints and the exception set at the head and foot of the principle channel rather than in its interior, since material buried mid-context is the material most often ignored.
- Record every span the assembly omitted, with the reason, so that a later grounding failure can distinguish absent evidence from discarded evidence.

**Required Outputs**:

- A context manifest with a stable identifier and a content hash.
- Two labelled channels with their contents and their token counts.
- An omission log naming every excluded span and its reason.

**Quality Checkpoints**:

- The two channels are separately labelled and separately counted; a merged context voids the manifest and halts the route.
- Every case fact carries an identifier, since the mapping rows in Phase 5 reference facts by identifier rather than by quotation.
- The exception set appears in the manifest even where it is empty, recorded as an explicit empty set rather than omitted.
- The omission log is present; an assembly that dropped spans without recording them is re-run.

***

#### Step 4.2: Enforce the Budget Reservation and the Untrusted-Data Boundary

**Required Actions**:

- Reserve at least 40 percent of the assembled context budget for the case channel and cap the principle channel at 40 percent, leaving the remainder for the request, the schema, and the mapping contract.
- Reserve at least 10 percent of the principle channel for the exception set, and truncate general statements rather than exceptions where the channel overflows.
- Strip active content from every retrieved span, neutralize instruction-like constructions inside untrusted text, and confirm that no retrieved span can alter policy, widen tool permissions, or change the output schema.
- Route every tool call through typed authorization derived from the contract rather than from anything present in the retrieved text.
- Confirm the derived question and its retrieved material did not cross the tenant, jurisdiction, or authorization boundary recorded in Step 1.1, and quarantine the whole manifest where they did.
- Halt assembly and return a budget defect where the case channel cannot be filled to its reservation, since a principle applied to insufficient case evidence produces a confident answer about a case that was never read.

**Required Outputs**:

- A channel budget record with reserved, used, and available tokens per channel.
- A sanitization record naming the neutralization applied to each untrusted span.
- An authorization check result covering tenant, jurisdiction, and source scope.

**Quality Checkpoints**:

- The case channel holds at least 40 percent of the assembled context budget; a shortfall halts composition.
- The exception reserve is intact; exceptions were never the content truncated to fit.
- No retrieved span occupies an instruction position, and no tool permission derives from retrieved text.
- The authorization check passes on all 3 dimensions; a failure quarantines the manifest rather than annotating it.

***

### Phase 5: Composition and Faithfulness Verification

**Objective**: Produce the specific answer from the general answer and establish that it follows from the cited clauses rather than merely accompanying them.

#### Step 5.1: Compose the Specific Answer With an Explicit Mapping

**Required Actions**:

- Issue 1 composition call returning the specific answer in the contract's output schema, together with the mapping rows, the assumptions relied on, the exceptions addressed, the citations, and a stated uncertainty.
- Require 1 mapping row per material conclusion at minimum, each binding a principle clause identifier, a case fact identifier, and a relation from the closed vocabulary of activates, limits, defeats, and not applicable.
- Require every enumerated exception to receive an explicit verdict of triggered, not triggered, or indeterminate, with the case fact identifier that decided it.
- Forbid the request for a private reasoning transcript; the auditable artifact is the mapping, the citations, and the verification results, not an account of the model's internal process.
- Increment the composition attempt counter and refuse a further attempt where it stands at its cap of 2.

**Required Outputs**:

- A specific answer conforming to the output schema.
- A mapping table with at least 1 row per material conclusion.
- An exception verdict list covering every enumerated exception.
- A citation list resolving to spans present in the context manifest.

**Quality Checkpoints**:

- Every material conclusion carries at least 1 mapping row; a conclusion with 0 rows is an adjacency defect and is rejected.
- Every cited span resolves to the manifest; a citation to material absent from the manifest is a fabrication and halts release.
- Every enumerated exception carries a verdict; an unaddressed exception blocks release.
- No private reasoning transcript was requested, produced, or retained.

***

#### Step 5.2: Run the Entailment, Ablation, and Sensitivity Checks

**Required Actions**:

- Run the deterministic checks first, covering output schema conformance, arithmetic, unit consistency, date arithmetic, citation resolution, and policy constraints, and reject the composition on any failure before spending a model call on semantic checks.
- Submit each material conclusion, its cited clause, and its cited facts to an independent entailment check performed without the composition's narrative in context, returning entailed, not entailed, or underdetermined.
- Ablate each cited clause in turn by removing it from the principle channel and re-composing with the case channel held fixed, recording whether the specific answer changes under the output schema; cap the ablation at 4 calls and sample the highest-cited clauses where more are cited.
- Count load-bearing clauses as those whose ablation changed the specific answer, and record the count with the identifiers.
- Test case sensitivity by substituting a counterfactual value for at least 1 decisive case fact per material conclusion, and record whether the answer changes in the direction the cited clause predicts.
- Confirm that every clause carrying the unsupported mark is absent from the citation list of any conclusion the contract treats as material at the established band.

**Composition Verification Record Template**:

```
COMPOSITION_ID:
CONTEXT_MANIFEST_ID:
MATERIAL_CONCLUSION_COUNT:
MAPPING_ROWS_PER_CONCLUSION:
DETERMINISTIC_CHECK_RESULTS:
ENTAILMENT_VERDICTS:
ABLATED_CLAUSE_IDS:
LOAD_BEARING_CLAUSE_COUNT:
CASE_SENSITIVITY_RESULTS:
EXCEPTION_VERDICTS:
UNSUPPORTED_CLAUSES_CITED:
DEFECT_CODES:
COMPOSITION_VERDICT:
```

**Required Outputs**:

- A deterministic check result set with a verdict per check.
- An entailment verdict per material conclusion.
- An ablation result per cited clause with the load-bearing count.
- A case sensitivity result per material conclusion.

**Quality Checkpoints**:

- Every material conclusion returns entailed; a not-entailed conclusion is removed from the answer rather than qualified, and an underdetermined conclusion is treated as not entailed.
- The load-bearing clause count is at least 1; a count of 0 fires UNFAITHFUL_COMPOSITION, because an answer unchanged by removing every cited principle did not derive from any of them.
- Case sensitivity fires for at least 1 fact per material conclusion; a conclusion invariant to its own decisive facts fires INSENSITIVE_TO_CASE.
- No clause carrying the unsupported mark supports a conclusion released at the established band.

***

#### Step 5.3: Adjudicate the Composition Verdict and Apply Bounded Repair

**Required Actions**:

- Assign the composition verdict from the closed vocabulary: FAITHFUL where every check passed; REPAIRABLE where the failures are local and confined to schema, arithmetic, citation, mapping coverage, or a single unaddressed exception; UNFAITHFUL where the load-bearing count is 0 or a material conclusion is not entailed; and UNSAFE where a policy or safety check failed.
- Issue at most 2 repairs on a REPAIRABLE verdict, each supplying the exact failed criterion and the evidence that produced it, never an instruction to try again.
- Return to Phase 3 where the defect is a factual gap and retrieval rounds remain, revising the retrieval query without altering the accepted derived question.
- Enter Phase 6 where the principle is correct but irrelevant, where case evidence defeats it, where the mapping requires an exception the general answer never enumerated, or where the verdict is UNFAITHFUL and the re-derivation cap remains.
- Exit on an UNSAFE verdict, on an unresolved contradiction, on 2 consecutive checks producing no change in the defect set, or on exhaustion of any cap, returning the best verified partial answer with its stated limitations or abstaining.
- Release only where the verdict is FAITHFUL and every released claim sits at or below the confidence ceiling set in Step 3.3.

**Required Outputs**:

- A composition verdict from the 4-value vocabulary with its deciding defect codes.
- A repair log with the criterion and evidence supplied to each attempt.
- A release decision recording either the released answer or the named exit condition.

**Quality Checkpoints**:

- Repairs do not exceed 2, and no repair was licensed without a named failed criterion.
- An UNFAITHFUL verdict never releases; it enters re-derivation or exits, and is never downgraded by adding a caveat.
- Stagnation is detected by comparing consecutive defect sets, so an unchanging failure consumes at most 2 checks.
- Every released claim carries a confidence band at or below the ceiling, and every claim resting on an unsupported clause is disclosed as such.

***

### Phase 6: Failure Handling and Bounded Re-Derivation

**Objective**: Convert a named failure into exactly 1 replacement attempt or 1 declared exit, without resetting a counter and without discarding case evidence that remains valid.

#### Step 6.1: Classify the Failure and Invalidate by Lineage

**Required Actions**:

- Require a named trigger before entry, drawn from the closed vocabulary: ungrounded principle, contradicted principle, non-determinative abstraction, trivial abstraction, principle-answer mismatch, decisive case contradiction, unenumerated exception, retrieval dead end, or no measured utility against the baseline.
- Refuse entry where the trigger is a local defect that Step 5.3 can repair, since re-derivation is the most expensive recovery available and is not the first response to a citation error or a schema violation.
- Freeze the case evidence bound to the original question, since case spans retrieved against the original request remain valid when the abstraction is discarded.
- Invalidate by lineage in one operation: the rejected derived question, every principle clause derived from it, every retrieval result keyed to it, every context manifest containing it, every composition citing it, and every cache entry whose key includes it.
- Record the invalidation cause on each invalidated artifact, so that a later analysis can distinguish artifacts discarded for a defect from artifacts discarded for budget.
- Confirm the counters for candidates, repairs, retrieval rounds, model calls, tokens, cost, and time carry forward unchanged.

**Required Outputs**:

- A trigger record naming exactly 1 entry condition with the evidence that fired it.
- An invalidation set listing every artifact removed and its cause.
- A preserved case evidence set with its provenance intact.
- A counter continuity record showing pre-entry and post-entry values as equal.

**Quality Checkpoints**:

- Exactly 1 trigger is named; an entry justified by a general sense that the answer is poor is refused.
- No counter was reset; a reset counter voids the run and halts the route.
- Case evidence keyed to the original question survived invalidation.
- Every invalidated artifact carries a cause, and no artifact derived from the rejected question survives in a cache.

***

#### Step 6.2: Execute One Bounded Re-Derivation or Bail Out

**Required Actions**:

- Generate exactly 1 replacement derived question that corrects the named failure explicitly, preserving the scope dimensions of Step 1.1 and moving in the direction the trigger indicates: downward for a non-determinative failure, upward for a trivial restatement, and laterally toward a different target artifact type for a retrieval dead end.
- Re-run the full generality test of Step 2.2 and the grounding procedure of Phase 3 against the replacement, with no criterion relaxed on the ground that this is a second attempt.
- Permit exactly 1 global re-derivation per request under the default cap, and refuse a second regardless of remaining tokens.
- Bail out to the direct route, to plain intermediate reasoning, or to case-specific retrieval where the replacement fails, and verify that fallback route against the same acceptance tests before releasing it.
- Abstain or escalate for human review where no fallback route can be verified and the risk tier forbids an unsupported release.
- Record the re-derivation outcome as recovered, dominated, or abstained, and attach it to the failure hypothesis from Step 1.3.

**Required Outputs**:

- One replacement derived question with its correction rationale, or a recorded bail-out.
- A re-run generality test verdict and grounding verdict for the replacement.
- A re-derivation outcome label from the 3-value vocabulary.
- A verified fallback result where the route bailed out.

**Quality Checkpoints**:

- Exactly 1 re-derivation was executed; a second attempt halts the route.
- No generality criterion was relaxed for the replacement.
- The bail-out route was verified against the acceptance tests before release, not assumed adequate.
- The re-derivation outcome is recorded against the original failure hypothesis, so that repeated dominated outcomes can retire the route for that task family.

***

### Phase 7: Measurement Against the Direct-Answer Baseline

**Objective**: Establish whether abstraction rather than additional computation produced any measured advantage, and issue a retention verdict for the route in this task family.

#### Step 7.1: Compute Abstraction-Attributable Gain Under Matched-Budget Controls

**Required Actions**:

- Stratify the evaluation set by difficulty before analysis, using reference solution depth, retrieval hop count, principle rarity, distractor count, exception density, or calibrated baseline confidence, and require at least 3 strata with at least 100 paired examples each.
- Run the full step-back route and each control condition on the identical example set with the identical model configuration, so that every comparison is paired rather than aggregate.
- Compute abstraction-attributable gain as the paired outcome difference between the full route and the masked condition, and report the placebo difference separately rather than folded into the same figure.
- Compute the margin against the strongest matched-budget control rather than against the cheapest baseline, since a comparison against a shorter baseline measures compute, not abstraction.
- Report paired win, loss, and tie counts with a 95 percent bootstrap confidence interval per stratum, not a single aggregate percentage.
- Classify the result as abstraction gain only where the placebo condition reproduces no more than 30 percent of the measured difference; otherwise classify it as extra-compute gain.

**Matched-Budget Controls and What Each Rules Out**:

| Control condition | Construction | Confound it removes | Release rule |
| :-- | :-- | :-- | :-- |
| Masked | Identical original question and case evidence, derived question and general answer removed | Gain arising from case evidence gathered along the way | Full route must exceed masked by at least 3 percentage points |
| Placebo | Token-matched generic or irrelevant general answer in the principle channel | Gain arising from context length or from any preamble | Placebo must reproduce at most 30 percent of the measured gain |
| Matched-token | Direct route given equal total input and output tokens, spent on longer direct reasoning or a second independent attempt | Gain arising from additional computation | Full route must exceed the matched-token baseline |
| Matched-call | Direct route given an equal count of model calls | Gain arising from repeated sampling of one route | Full route must exceed the matched-call baseline |
| Matched-latency | Direct route given equal wall-clock budget | Gain purchased with latency the contract cannot afford | Reported per stratum; a loss blocks latency-sensitive deployment |
| Principle-only | Grounded principle supplied without the derived question | Attribution of retrieval gain to the reasoning context | Reported separately; it partitions the gain rather than gating release |

**Required Outputs**:

- A stratified paired result set with win, loss, and tie counts per stratum.
- An abstraction-attributable gain figure with its bootstrap confidence interval.
- A control result per condition in the table.
- A gain classification of abstraction gain or extra-compute gain.

**Quality Checkpoints**:

- Every stratum carries at least 100 paired examples; a thinner stratum is reported as unmeasured rather than pooled into another.
- The 95 percent confidence interval lower bound exceeds 0 in at least 1 stratum; a route with no stratum clearing this is not promoted.
- The placebo condition was run; a gain reported without it is not admissible evidence.
- The comparison reference is the strongest matched control, and the cheapest baseline is not substituted for it.

***

#### Step 7.2: Compute Route Metrics and Issue the Retention Verdict

**Required Actions**:

- Compute the abstraction metric family: candidate admission rate, trivial-restatement rate keyed to TOO_NARROW, over-abstraction rate keyed to NOT_DETERMINATIVE, scope-erasure rate, repair rate, and re-derivation recovery rate.
- Compute the grounding metric family: grounding rate, principle correctness rate against an independent adjudication, principle relevance rate, exception coverage rate, contradiction detection recall, and the proportion of released answers carrying an unsupported clause.
- Compute the composition metric family: mapping coverage, entailment pass rate, load-bearing rate, adjacency defect rate, and case sensitivity firing rate.
- Compute the efficiency family: median, p90, and p95 latency; tokens and cost per attempt and per verified success; and incremental verified success per added token, call, and second.
- Measure seed robustness across at least 5 preregistered repetitions, reporting mean, worst seed, best-minus-worst range, pass-fail flip rate, derived-concept stability, and retrieval-set overlap.
- Issue the retention verdict as promote, retain with restriction, or retire, and bind it to the task family and difficulty stratum rather than to the deployment as a whole.

**Required Outputs**:

- A metric report covering all 4 metric families with a value per metric.
- A seed robustness report over at least 5 repetitions.
- A retention verdict per task family and stratum with the metrics that decided it.

**Quality Checkpoints**:

- Load-bearing rate is at least 0.80 across released answers; a lower rate indicates the principle channel is decorative and the route is retained with restriction at most.
- Grounding rate is at least 0.90 for task families in a risk tier requiring authoritative guidance; below that the route is retired for that family.
- Pass-fail flip rate across seeds is at most 10 percent and derived-concept stability is at least 0.80; a route failing either is not promoted.
- The verdict is bound to a named task family and stratum; a deployment-wide promotion from one family's evidence is refused.
- Cost per verified success is compared against the direct baseline's, and a route more expensive at equal quality is retired regardless of its accuracy figure.

***

## III. Implementation Guidance for AI Agents

AI agents operating step-back prompting must follow systematic protocols ensuring that the abstraction is tested rather than admired, that the general answer is grounded rather than recalled, and that the composition is verified rather than narrated. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Gate Agent**: Owns the task contract, the budget ledger, the direct-answer baseline, and the applicability verdict. It alone may issue an invoke verdict, and it refuses one where no permitted principle source exists.
2. **Abstraction Agent**: Model-tier component producing candidate derived questions, instance enumerations, and substitution pairs against a closed output schema. It may not evaluate its own candidate, extend its own counter, or select its own route.
3. **Generality Test Harness**: Deterministic component evaluating all 6 admission criteria, normalizing instance lists, running the substitution comparison, scanning for answer leaks, and holding the candidate and repair counters.
4. **Grounding Agent**: Hybrid component dispatching authorized retrieval for the derived and original questions, binding clauses to artifacts, classifying evidence class, running contradiction queries, and applying the unsupported mark. The mark is written by its deterministic half and is not removable by any model call.
5. **Composition Agent**: Model-tier component producing the specific answer, the mapping rows, and the exception verdicts. It may not declare its own composition faithful and may not cite material absent from the context manifest.
6. **Verification Harness**: Deterministic component running the schema, arithmetic, unit, date, and citation checks, orchestrating the independent entailment checks and the clause ablations, and computing mapping coverage and exception coverage.
7. **Measurement Agent**: Deterministic component running the matched-budget controls, computing the metric families, and issuing the retention verdict per task family and stratum. It may withhold promotion.

**Disclosure and Privacy Boundary**: The instrumentation protocol permits decision metadata and prohibits hidden reasoning content, and it applies to every component.

- Log defect codes, criterion verdicts, evidence classes, provenance fields, mapping rows, ablation results, cost figures, and gate outcomes.
- Do not require, request, or persist a private reasoning transcript from any model or component; the auditable artifact is the mapping from clause to fact, not an account of the model's internal process.
- Do not log credentials, raw authentication material, unrestricted personal data, or sensitive source text by default; retain content references and hashes instead.
- Treat the derived question as sensitive, since a broader question can disclose the diagnosis, investigation, or legal position the narrower original concealed, and apply the original request's authorization, tenancy, and retention rules to it unchanged.
- Ensure deletion propagates to caches, traces, index-derived artifacts, and object storage, since the route creates derived copies of the request at three stages.

**Workflow Execution Pattern**:

```
STATE: Generality_Test_Evaluation
INPUTS:
  1. Candidate derived question from the Abstraction Agent
  2. Instance list and substitution pair
  3. Scope dimension list from Step 1.1
  4. Original question retrieval results from Step 1.2
ACTIONS:
  1. Normalize instances and count distinct survivors
  2. Derive a specific answer under each member of the substitution pair
  3. Scan the candidate for answer-slot leakage
  4. Check scope dimension coverage
  5. Dispatch the candidate and count novel retrieval candidates
VALIDATION:
  - distinct_instance_count >= 3
  - substitution_answers_differ == TRUE
  - answer_leak_hits == 0
  - uncovered_scope_dimensions == 0
  - retrieval_novelty_count >= 1 IF retrieval_permitted
  - candidate_counter <= 2 AND repair_counter <= 2
TRANSITIONS:
  IF all_validations_pass THEN next_state = Principle_Grounding
  IF defect IN {TOO_NARROW, SCOPE_ERASED, ANSWER_LEAKED}
     AND repair_counter < 2 THEN next_state = Targeted_Repair
  IF defect == NOT_DETERMINATIVE THEN next_state = Lower_Level_Candidate
  IF counters_exhausted THEN next_state = Direct_Route_Exit
```

**Two-Phase Action Pattern**: Emit the candidate derived question, its instance list, and its substitution pair without dispatching any retrieval; validate them against the criteria while no retrieval budget is committed; dispatch and ground only after admission. The same pattern governs composition: emit the mapping and the citations, validate coverage and citation resolution deterministically, and only then spend model calls on entailment and ablation.

**Approval Gate**: Human authorisation is required before releasing any answer whose confidence ceiling is the hypothesis band in a risk tier requiring authoritative guidance; before any release where the grounding verdict is CONTRADICTED; before any derived question whose retrieval would widen the authorization, tenancy, or jurisdiction scope of the original request; and before any route projected to exceed 3 times the direct baseline cost. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the contract, the budget ledger, the counter set, and the provenance bundle in durable state, since a re-derivation may cross a context boundary.
- Summarise superseded artifacts into references once their verdicts are recorded, retaining identifiers, hashes, and defect codes and discarding the bulk.
- Never carry a rejected derived question or an invalidated clause into a later context window, since a rejected artifact reintroduced as background is indistinguishable from an accepted one.
- Count the abstraction and grounding stages against the composition's budget, so that overhead is visible rather than distributed across separate ledgers.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract and Route Integrity (After Phase 1)**

- **Automated Check**: Every acceptance test is machine-evaluable or assigned to a named role; every budget dimension carries a numeric limit; the baseline was executed and measured on all 4 cost dimensions; exactly 1 error class is assigned; the invoke verdict names at least 1 permitted principle source.
- **Agent Action on Pass**: Proceed to abstraction.
- **Agent Action on Failure**: Halt and return the contract or routing defect; no abstraction call is issued against an incomplete contract.
- **Human Review Trigger**: A request in the highest risk tier with no authoritative principle source permitted, or a gate overhead measurement above 5 percent of the direct-execution budget.

**Checkpoint 2: Abstraction Admission (After Phase 2)**

- **Automated Check**: All 6 generality criteria carry explicit verdicts; distinct instances at least 3; substitution answers differ; answer leaks 0; uncovered scope dimensions 0; retrieval novelty at least 1 where retrieval is permitted; exactly 1 derived question is carried forward.
- **Agent Action on Pass**: Proceed to grounding.
- **Agent Action on Failure**: Apply the defect-specific action from Step 2.3, or exit to the direct route with a dominance verdict.
- **Human Review Trigger**: Admission rate below 40 percent across the last 50 requests in a task family, which indicates the applicability gate is licensing the route where it does not apply.

**Checkpoint 3: Grounding Adequacy (After Phase 3)**

- **Automated Check**: Every material clause carries a binding record; every admitted span carries all 6 provenance fields; every material clause carries at least 1 contradiction query; the grounded proportion is computed from the binding table; the confidence ceiling is recorded.
- **Agent Action on Pass**: Proceed to context assembly.
- **Agent Action on Failure**: Revise the retrieval query within the 3-round cap, or record the verdict as UNSUPPORTED and apply its ceiling.
- **Human Review Trigger**: A CONTRADICTED verdict in any risk tier, or a grounded proportion below 0.50 where the contract requires authoritative guidance.

**Checkpoint 4: Context Integrity (After Phase 4)**

- **Automated Check**: Two channels labelled and separately counted; case channel at or above 40 percent of the assembled budget; exception reserve intact; omission log present; authorization check passing on tenant, jurisdiction, and source scope; no retrieved span in an instruction position.
- **Agent Action on Pass**: Proceed to composition.
- **Agent Action on Failure**: Halt assembly and return the budget or boundary defect; quarantine the manifest on an authorization failure.
- **Human Review Trigger**: Any authorization failure, or any case where the case channel cannot be filled to its reservation for the same task family more than twice.

**Checkpoint 5: Composition Faithfulness (After Phase 5)**

- **Automated Check**: Mapping coverage 100 percent of material conclusions; every citation resolves to the manifest; every entailment verdict is entailed; load-bearing clause count at least 1; case sensitivity fires for at least 1 fact per material conclusion; every enumerated exception carries a verdict; no unsupported clause supports an established-band conclusion.
- **Agent Action on Pass**: Release under the recorded confidence ceiling.
- **Agent Action on Failure**: Apply bounded repair on a REPAIRABLE verdict, enter Phase 6 on an UNFAITHFUL verdict, and exit on an UNSAFE verdict.
- **Human Review Trigger**: A load-bearing count of 0 on 2 consecutive requests in a task family, or any UNSAFE verdict.

**Checkpoint 6: Recovery Boundedness (After Phase 6)**

- **Automated Check**: Exactly 1 named trigger; exactly 1 re-derivation executed; counters unchanged across entry; case evidence preserved; no generality criterion relaxed; the bail-out route verified against the acceptance tests.
- **Agent Action on Pass**: Resume the framework at Phase 2 with the replacement, or release the verified fallback.
- **Agent Action on Failure**: Halt the route; a second re-derivation or a reset counter voids the run.
- **Human Review Trigger**: A dominated re-derivation outcome on more than 30 percent of invoked requests in a task family.

**Checkpoint 7: Measurement Validity (After Phase 7)**

- **Automated Check**: At least 3 strata with at least 100 paired examples each; the masked, placebo, matched-token, and matched-call controls all executed; the 95 percent confidence interval computed; the gain classification recorded; at least 5 seed repetitions.
- **Agent Action on Pass**: Issue the retention verdict and permit promotion within its named task family and stratum.
- **Agent Action on Failure**: Withhold the verdict and name the missing control; no route is promoted on unmatched-budget results.
- **Human Review Trigger**: A promotion request where the placebo condition reproduces more than 30 percent of the measured gain, which classifies the result as extra-compute gain.

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

**Error Type 1: Over-Abstraction**

- **Symptoms**: The substitution pair yields identical specific answers; the general answer names a discipline, a topic, or a category rather than a rule; the composition cites the clause but the ablation shows no change; enumerated exceptions are absent where the domain is known to carry them.
- **Diagnostic Steps**: Confirm the substitution comparison was run under the output schema rather than on free text; inspect whether the derived question names a scope dimension from the Step 1.1 list; check whether the general answer contains any quantifier, threshold, or condition that could discriminate between candidate specific answers.
- **Resolution Protocol**: Option A, generate the second candidate one level lower, targeting a named mechanism, invariant, or policy rule rather than a field of study. Option B, restore the scope dimensions the candidate erased and re-run the generality test. Option C, exit to the direct route and record the dominance verdict, since a question above the band is not repaired by further abstraction.
- **Escalation Trigger**: NOT_DETERMINATIVE firing on both candidates exits the route immediately; over-abstraction on more than 30 percent of requests in a task family escalates the applicability gate's licensing signals for policy review.

**Error Type 2: Under-Abstraction**

- **Symptoms**: Fewer than 3 distinct instances survive normalization; the derived question shares its entity and relation signature with the original; retrieval on the derived question returns the same candidates at the same ranks; the general answer restates the request.
- **Diagnostic Steps**: Compare the normalized signatures of the derived and original questions; check whether the instance list contains paraphrases of the original rather than distinct cases; check whether the derived question merely deleted a particular rather than generalising the relation.
- **Resolution Protocol**: Option A, request 1 targeted repair supplying the TOO_NARROW code and the measured instance count. Option B, change the target artifact type, since a schema or taxonomy target often generalises where a mechanism target did not. Option C, exit to the direct route, since a restatement adds cost with no recall gain.
- **Escalation Trigger**: A second candidate that introduces no concept absent from the first exits the route; the repair counter is never raised above 2 to accommodate this class.

**Error Type 3: Ungrounded or Contradicted Principle**

- **Symptoms**: Material clauses bound only to Class E3 evidence; contradiction queries returning equal or higher authority material; sources whose effective dates do not cover the contract date; the grounded proportion below 0.50.
- **Diagnostic Steps**: Determine whether the failure is retrieval reach, source permission, or genuine absence of an authority; check whether the retrieval query rather than the derived question was at fault; verify that the contradiction is between sources rather than between a source and a model recollection.
- **Resolution Protocol**: Option A, revise the retrieval query within the 3-round cap without altering the accepted derived question. Option B, substitute a deterministic derivation where the clause is computable, converting Class E3 support to Class E2. Option C, retain the clause with the unsupported mark, cap the route at the hypothesis band, and disclose the status in the response. Option D, abstain or escalate where the risk tier forbids an unsupported release.
- **Escalation Trigger**: A CONTRADICTED verdict escalates immediately and is never resolved by additional retrieval rounds; this class is never closed by a further model assertion, since the failing evidence class is exactly the one a further assertion would supply.

**Error Type 4: Unfaithful Composition**

- **Symptoms**: A load-bearing clause count of 0; a material conclusion with 0 mapping rows; entailment verdicts of underdetermined; the specific answer identical to the masked condition's answer; case sensitivity failing to fire.
- **Diagnostic Steps**: Confirm the ablation removed the clause from the principle channel rather than only from the citation list; check whether the conclusion derives from case evidence alone, which would mean the principle channel is decorative; check whether the mapping relation vocabulary was used or narrative text was returned in its place.
- **Resolution Protocol**: Option A, issue 1 repair supplying the specific unentailed conclusion and its cited clause. Option B, remove the unentailed conclusion from the answer, since a conclusion that does not follow is deleted rather than qualified. Option C, enter re-derivation where the principle is correct but irrelevant to every conclusion. Option D, release the masked route's answer and record the step-back route as dominated for this request.
- **Escalation Trigger**: A load-bearing count of 0 on 2 consecutive requests in a task family suspends the route for that family pending review; composition repairs are never raised above 2.

**Error Type 5: Dominated Route**

- **Symptoms**: The matched-token baseline equals or exceeds the full route; the placebo condition reproduces most of the measured gain; cost per verified success exceeds the baseline's at equal quality; the difficulty stratum showing the gain contains fewer than 100 paired examples.
- **Diagnostic Steps**: Recompute the comparison against the strongest matched control rather than the cheapest baseline; segment the result by stratum to determine whether the gain is confined to one difficulty band; check whether the gain survives the masked condition.
- **Resolution Protocol**: Option A, restrict the route to the strata where the confidence interval excludes 0 and retire it elsewhere. Option B, reclassify the outcome as extra-compute gain and reallocate the budget to the baseline. Option C, retire the route for the task family and record the applicability signals that mislicensed it.
- **Escalation Trigger**: A promotion request without a placebo condition is refused outright; a route retained on unmatched-budget evidence escalates for policy review rather than being corrected in place.

**Error Type 6: Boundary Breach in the Derived Question**

- **Symptoms**: The derived question reaches material the original request was not authorized to see; a cached artifact is served across tenants, dates, or jurisdictions; retrieved text appears in an instruction position; the broader question itself discloses sensitive context.
- **Diagnostic Steps**: Compare the derived question's authorization scope against the Step 1.1 record; inspect the cache key for the validity dimensions it omits; trace whether any tool permission or schema change originated in retrieved text.
- **Resolution Protocol**: Option A, quarantine the manifest, purge the derived artifacts by lineage, and re-run under the correct scope. Option B, narrow the derived question to the original's authorization scope and re-run the generality test against the narrowed form. Option C, suppress the route for the request and answer from case evidence alone.
- **Escalation Trigger**: Any breach halts the route and blocks release; it is never traded against a retrieval improvement and never carried forward as a known issue.

**Troubleshooting Decision Tree**:

```
A CHECKPOINT REJECTS AN ARTIFACT
├─ ABSTRACTION DEFECT
│   ├─ Substitution answers identical → Generate one level lower; on second failure exit to direct route
│   ├─ Fewer than 3 distinct instances → One targeted repair; then exit to direct route
│   ├─ Scope dimension erased → One repair restoring the dimension; then exit to direct route
│   └─ Answer slot present in the question → Reject candidate; regenerate without the answer token
├─ GROUNDING DEFECT
│   ├─ Material clause on model recall only → Apply unsupported mark; cap at hypothesis band
│   ├─ Contradicting source of equal or higher authority → HALT; escalate for review
│   ├─ Source outside effective date or jurisdiction → Refuse as support; revise retrieval query
│   └─ Three rounds without unique spans → Declare retrieval dead end; enter re-derivation once
├─ COMPOSITION DEFECT
│   ├─ Zero load-bearing clauses → Reject; enter re-derivation or release the masked answer
│   ├─ Conclusion not entailed → Delete the conclusion; never qualify it
│   ├─ Exception unaddressed → One repair supplying the exception; then block release
│   └─ Citation absent from manifest → HALT release; treat as fabrication
├─ BOUNDARY DEFECT
│   ├─ Authorization scope widened → Quarantine manifest; purge by lineage; escalate
│   └─ Retrieved text in instruction position → Strip and re-assemble; block tool calls
└─ MEASUREMENT DEFECT
    ├─ Placebo reproduces most of the gain → Reclassify as extra-compute gain; refuse promotion
    ├─ Stratum below 100 paired examples → Report unmeasured; do not pool
    └─ Cost per success above baseline → Retire the route for the task family
```

### D. Performance Metrics and Continuous Learning

**Abstraction Metrics**:

- **Candidate admission rate**: Candidates passing all 6 generality criteria on the first attempt (target: at least 0.60; below 0.40 indicates the applicability gate is mislicensing the route).
- **Over-abstraction rate**: Requests in which NOT_DETERMINATIVE fired at least once (target: at most 0.15).
- **Trivial-restatement rate**: Requests in which TOO_NARROW fired at least once (target: at most 0.15).
- **Derived-concept stability**: Agreement on the derived concept across at least 5 seeds (target: at least 0.80).

**Grounding and Composition Metrics**:

- **Grounding rate**: Material clauses bound to Class E1 or E2 evidence (target: at least 0.90 in risk tiers requiring authoritative guidance; at least 0.70 elsewhere).
- **Principle correctness rate**: Accepted clauses judged correct under independent adjudication within their declared scope (target: at least 0.95).
- **Exception coverage rate**: Enumerated exceptions carrying their own supporting artifact (target: at least 0.90).
- **Load-bearing rate**: Released answers in which at least 1 cited clause changed the answer under ablation (target: at least 0.80).
- **Adjacency defect rate**: Material conclusions released with 0 mapping rows (target: 0, since this defect blocks release).
- **Unsupported disclosure rate**: Released answers resting on an unsupported clause that state that status explicitly (target: 1.00).

**Efficiency Metrics**:

- **Route overhead**: Step-back route cost over direct baseline cost (target: at most 3.0; above that the applicability gate suppresses).
- **Cost per verified success**: Total cost over accepted successes (target: below the matched-budget baseline at equal quality).
- **Incremental verified success**: Additional verified successes per added 1,000 tokens, per added model call, and per added second (target: positive in at least 1 difficulty stratum).
- **Pass-fail flip rate**: Outcome changes across at least 5 seed repetitions (target: at most 0.10).

**Learning and Adaptation Mechanisms**:

- **Applicability policy correction**: Feed every dominated outcome back to the gate, retiring the invocation signal that licensed it where the signal's dominated rate exceeds 0.30 in a task family.
- **Cache discipline**: Cache only admitted derived questions and grounded clauses, and key every entry on task family, concept signature, scope dimensions, jurisdiction, effective interval, tenant, prompt and demonstration version, model revision, policy version, and output schema. Never cache an unverified draft and never reuse an entry across tenants, dates, or jurisdictions.
- **Prompt and demonstration versioning**: Version the abstraction, repair, extraction, composition, and verification prompts independently, and version demonstrations separately, since a change to an example alters abstraction granularity without any change to the instruction.
- **Threshold recalibration**: Recompute every numeric threshold in this guide per task family against observed outcomes, since the values stated here are deployment defaults rather than measured constants.

**Human-in-the-Loop Boundaries**: Removal of an unsupported mark, release of a hypothesis-band answer in a risk tier requiring authoritative guidance, widening of the derived question's authorization scope, promotion of a route whose advantage appears only against an unmatched baseline, and relaxation of the disclosure boundary are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the relationship between a general statement and a specific case rather than the content of either. Its phases hold wherever a request can be answered by a rule that also governs other requests, wherever that rule can be established outside the model, and wherever the case carries facts that can defeat it.

### 4.1 Cross-Domain Application Patterns

**Scientific and engineering analysis**: The request names a concrete configuration while the governing relation is a law or invariant stated at the level of the phenomenon. The derived question targets the mechanism rather than the discipline, and the determinativeness substitution is cheap because two candidate general answers imply numerically different specific answers. Grounding prefers Class E2 evidence, since a solver or unit checker establishes a relation more reliably than a retrieved narrative.

**Legal and regulatory decision support**: The derived question targets the governing instrument, the displacing authority, and the exception structure rather than the area of law. Grounding requires Class E1 evidence with effective dates and jurisdiction filters, and a source outside the contract's effective interval is refused as support. The case channel dominates the budget because a quoted clause, a date, or a party identity commonly defeats the general rule. Every released answer states that the derived principle identifies candidate governing material rather than establishing it, and human review precedes release.

**Clinical guideline application**: The derived question targets the guideline's population, indication, and contraindication structure. The exception reserve is load-bearing rather than ornamental, since pregnancy, renal impairment, paediatric status, and comorbidity commonly displace a general recommendation, and an unenumerated exception caps the route at the qualified band. An UNSUPPORTED verdict terminates the route in escalation rather than in a qualified release.

**Financial and compliance analysis**: The derived question targets thresholds, definitions, precedence rules, and safe harbours. Grounding combines Class E1 policy text with Class E2 computation, because a threshold is established by a document and applied by arithmetic. Case sensitivity is tested against the value nearest a threshold, since an answer insensitive to a value on the boundary of its own rule has not applied the rule.

**Software engineering diagnosis**: The gate returns invoke where repeated fixes address symptoms while a system invariant is being violated. The derived question targets the invariant, the protocol contract, or the resource discipline rather than the failing component. Grounding prefers Class E2 evidence from a reproducible test over retrieved documentation, and the ablation is cheap because removing the cited invariant produces a visibly different remediation.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk reversible work**: Collapse the route to 1 candidate, 0 repairs, 1 retrieval round, and 0 re-derivations, retaining the generality test and the load-bearing check, which are the two checks that distinguish the method from a longer preamble. Route overhead above 1.5 times the baseline indicates the gate should have suppressed.
- **High-risk or irreversible work**: Retain every phase, require Class E1 or E2 evidence for every material clause, forbid release at the hypothesis band, bind the approval gate before release, and prefer abstention over a qualified answer whose principle carries the unsupported mark.
- **Strict latency budgets**: Suppress rather than shorten. The route requires at least 2 model stages plus a grounding round, and removing the grounding round to fit a latency ceiling converts the method into an unverified assertion at higher cost than the baseline.
- **High-volume low-margin traffic**: Cache admitted derived questions and grounded clauses under the full validity key, and measure the stale-hit rate alongside the hit rate, since a cache serving an expired principle produces a confident wrong answer at negligible cost.
- **Long-horizon or multi-turn requests**: Persist the contract, the counters, and the provenance bundle outside working context, and re-run the authorization check at every context boundary.
- **Multi-component deployments**: Assign the generality test, the grounding classification, and the verification harness to components distinct from the abstraction and composition models, since a component that both writes and admits an artifact supplies no independent check.

***

## V. Limitations and Considerations

**Applicability is narrow**: Most requests are already concrete, and for those the method adds 1 to 2 model calls and up to 3 retrieval rounds with no expected quality gain, while competing with the case evidence for context. The consequence is a deployment that measures worse than its own baseline while appearing more thorough. The mitigation is the applicability gate in Section 1.3, bounded to 2 percent of the direct-execution budget, together with the retention verdict in Phase 7 that retires the route per task family rather than deployment-wide.

**The reported gains are benchmark-specific and the intervention is asymmetric**: The published figures cover selected reasoning and retrieval benchmarks under one prompt design and a small set of model families, and the same analysis reported that combining the method with retrieval turned 5.6 percent of previously correct predictions wrong while correcting 39.9 percent of previously wrong ones. The consequence is that a net gain on an aggregate figure can conceal a population of newly broken cases. The mitigation is the paired, stratified measurement in Step 7.1, which reports win, loss, and tie counts per stratum rather than a single aggregate, and the retention verdict that restricts the route to strata where the interval excludes 0.

**Every threshold here is a deployment default**: The instance floor of 3, the grounded proportion boundaries of 0.90 and 0.50, the channel reservations of 40 percent, the ablation cap of 4, the seed count of 5, the paired-example floor of 100, and the placebo tolerance of 30 percent were chosen to be operable on first deployment, not derived from a measured property of reasoning systems. The consequence is that a deployment inheriting them unchanged will hold gates in the wrong place for its own distribution. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute every threshold per task family against observed outcomes.

**Grounding is bounded by corpus reach**: Where no permitted source can establish the derived question's answer, the unsupported mark records the situation honestly but does not repair it, and the route degrades to a model recollection presented with a disclosure. The consequence is that domains with thin authoritative corpora gain the method's cost and little of its benefit. The mitigation is the gate rule that suppresses the route where no permitted principle source exists, so that the degraded case is refused at entry rather than discovered at release.

**Ablation is attribution evidence, not a causal account**: A clause whose removal changes the answer was load-bearing for that composition under that configuration. It does not establish that the model's internal process used the clause, and a fluent rule-to-fact mapping is not evidence of faithfulness on its own. The consequence is a risk of over-claiming that the released explanation describes how the answer was produced. The mitigation is to report the ablation as attribution evidence, to release the mapping as a checkable relation between cited artifacts rather than as an account of internal reasoning, and to never request or retain a private reasoning transcript.

**Verification cost scales with the clause count**: Each cited clause costs 1 ablation call, and each material conclusion costs 1 independent entailment check, so a general answer with many clauses can consume more budget than the composition it verifies. The consequence is either a truncated verification or a route that exceeds its cost ceiling. The mitigation is the ablation cap of 4 calls with sampling of the most-cited clauses, together with the materiality label that excludes contextual clauses from verification entirely.

**The derived question widens exposure**: Abstraction produces a second representation of the request, dispatches it to retrieval, and may cache it, so a request that was safe at its original specificity can reach material or reveal context that the original could not. The consequence is a boundary breach that no accuracy metric detects. The mitigation is the authorization check in Step 4.2, the cache key requirements in Section III.D, and the treatment of the derived question as carrying the original request's sensitivity classification unchanged.

**Evidence provenance in this guide**: The benchmark figures quoted in Section 1.5 were verified during conversion against the paper's public rendering. Every other claim carried from the originating prose source, including its infrastructure recommendations and its characterisation of neighbouring methods, was transcribed rather than independently re-verified, and no reference entry was added that was not either present in that source or retrieved during conversion. The consequence is that a reader should treat the transcribed material as attributable to the source rather than as established here. The mitigation is the reference treatment in Section VII, which states the provenance of each entry explicitly.

**Structural conformance is not correctness**: A route can pass the generality test, ground its principle, compose faithfully, and still answer a question that was the wrong one to ask. The framework detects malformed abstraction and unfaithful composition, not misdirected purpose, and no checkpoint here substitutes for human review of the objective in a consequential domain.

***

## VI. Conclusion and Summary

Step-back prompting is a narrow technique with three points of failure, and its value depends entirely on whether those three points are instrumented. The abstraction can land outside the generality band, above it where the principle constrains nothing and below it where the question was never generalised; the general answer can be a fluent recollection that no source supports; and the composition can produce an answer that sits beside the principle rather than following from it. Each failure produces output that reads as competent work. None is detected by inspecting the response, and none is repaired by an instruction to think more broadly.

The three corresponding tests are cheap relative to the route they govern. A derived question is admitted only where it governs at least 3 distinct instances and where two mutually exclusive answers to it imply two different answers to the original. A general answer is grounded only against a retrieved span or a reproducible execution record. A composition is faithful only where removing a cited clause changes the answer. A deployment running these three tests against a matched-budget baseline will know whether abstraction is paying for itself; one running the two model stages without them has bought cost and a more confident presentation.

**Key Success Factors**:

- **Two-sided admission**: The derived question is tested for being more general than the original and for still determining it, and a failure on either side rejects the candidate rather than qualifying it.
- **Grounding before load-bearing use**: A principle is a hypothesis until an artifact outside the generating model supports it, and an unsupported principle is marked and disclosed rather than quietly promoted.
- **Composition proved by ablation**: A cited clause earns its place by changing the answer when removed, so that adjacency is separated from derivation mechanically.
- **Channel separation**: Principle evidence and case evidence occupy separate, separately budgeted regions, and the case that can defeat the rule is never the content truncated to fit.
- **Bounded recovery**: Candidates, repairs, retrieval rounds, and re-derivations carry hard caps, no counter resets, and exhaustion terminates through a declared exit rather than an extension.
- **Matched-budget measurement**: The route is retained only where it beats a baseline given the same tokens, calls, cost, and latency, in a named task family and difficulty stratum.

By following this guide, AI agents can determine when a question's difficulty genuinely lies in selecting a governing principle, establish that principle against evidence rather than recall, and demonstrate that the specific answer follows from it.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references are the citations the originating prose source attached to the material retained here, transcribed as that source carried them and not independently re-verified during conversion, with one exception noted in the list. Bare labels are reproduced as bare labels rather than expanded into reconstructed titles.

**Corpus pointers**:

- `Production Guide to Step-Back Prompting` — the originating prose guide from which this operational guide was derived. Source of the two-stage abstraction and abstraction-grounded reasoning structure, the warranted and unwarranted use conditions, the loop structure with entry and exit conditions, the default budget caps, the abstraction quality criteria, the principle grounding and context assembly requirements, the re-abstraction triggers, the logging field inventory, the paired and matched-budget evaluation design, and the failure and safety taxonomy.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — owns step-back as a retrieval query transformation, including the abstraction-gap failure class, the step-back formulation issued alongside the original query, and the rule that generated query text is a retrieval instrument and never evidence. Its terminology is adopted unchanged in Section 1.5, which states the boundary between that role and the reasoning role owned here.
- `advanced_task_guides/reasoning/guide_ChainOfThoughtReasoning.md` — companion guidance on deciding whether intermediate reasoning is warranted and verifying an answer against evidence external to the reasoning, applicable to the baseline routing in Step 1.2.
- `advanced_task_guides/reasoning/guide_ChainOfVerification.md` — companion guidance on claim-level verification of a produced answer, applicable after composition in Phase 5 and distinct from the grounding of the general answer in Phase 3.
- `advanced_task_guides/reasoning/guide_SelfConsistency.md` — companion guidance on sampling and agreement thresholds, applicable to the composition stage where repeated attempts are warranted.
- `advanced_task_guides/reasoning/guide_TreeOfThought.md` — companion guidance on search over partial solutions, the correct route where the difficulty is comparing alternatives rather than selecting a governing rule.
- `advanced_task_guides/reasoning/guide_MetacognitiveMonitoring.md` — companion guidance on constructing and calibrating monitoring signals, applicable to the signals the applicability gate consumes in Step 1.3.
- `advanced_task_guides/reasoning/guide_LeastToMostReasoning.md` — companion guidance on decomposing a compositional question into ordered subproblems, the correct route where prerequisites and intermediate state are the bottleneck.
- `advanced_task_guides/reasoning/guide_BufferOfThoughts.md` — companion guidance on distilling a problem into a normalised description and retrieving a governed, reusable template against it. Its problem distillation is this guide's abstraction made persistent: the general question derived here is produced per run and discarded, while a template there is promoted into a library under a gate and retrieved for later problems. Route there where the same abstraction recurs often enough to be worth storing, versioned and governed, rather than re-derived each time.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on control decisions over an active reasoning process, applicable to the route binding and exit conditions in Phases 1 and 6.

**External references**:

1. Zheng, Mishra, Chen, Cheng, Chi, Le, and Zhou, *Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models*, ICLR 2024; title, authors, venue, and the benchmark and error-analysis figures quoted in Section 1.5 were verified during conversion — https://arxiv.org/abs/2310.06117
2. *ICLR paper* — https://proceedings.iclr.cc/paper_files/paper/2024/file/592da1445a51e54a3987958b5831948f-Paper-Conference.pdf
3. *MMLU* — https://arxiv.org/abs/2009.03300
4. Wei and colleagues — https://arxiv.org/abs/2201.11903
5. Kojima and colleagues — https://arxiv.org/abs/2205.11916
6. *Generated Knowledge Prompting* — https://arxiv.org/abs/2110.08387
7. Dhuliawala and colleagues — https://aclanthology.org/2024.findings-acl.212/
8. Huang and colleagues — https://arxiv.org/abs/2310.01798
9. Turpin and colleagues — https://arxiv.org/abs/2305.04388
10. *CoT faithfulness interventions* — https://arxiv.org/abs/2307.13702
11. *Lost in the Middle* — https://arxiv.org/abs/2307.03172
12. *OWASP prompt injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
13. *OWASP sensitive-information disclosure* — https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/
14. *W3C PROV-O* — https://www.w3.org/TR/prov-o/

