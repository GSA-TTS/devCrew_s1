# Chain-of-Thought Reasoning

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Chain-of-thought reasoning constitutes the task family of deciding whether a task warrants intermediate reasoning before an answer, configuring that reasoning to a bounded effort budget, and verifying the resulting answer against evidence external to the reasoning itself. This guide provides AI agents with a structured protocol spanning seven phases: contract establishment and warrant determination, technique selection from an ordered ladder, prompt and effort configuration, bounded generation with deterministic answer extraction, external verification and action authorisation, disclosure-bounded response and metadata logging, and outcome measurement with policy correction. It treats a reasoning trace as an inference-time workspace rather than as evidence, because a fluent chain can accompany a wrong answer and can omit the influences that actually determined it. No conclusion is accepted on the internal consistency of its own chain, and no chain authorises an action. The guide specifies a warrant gate that suppresses intermediate reasoning wherever a direct answer or a deterministic function suffices, an execution tier partition assigning effort budgeting, step bounds, answer extraction, verification execution, and metadata logging to deterministic software while the model proposes reasoning and answers, and a metric set covering verified accuracy, effort efficiency, calibration, and faithfulness.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Intermediate reasoning**: Model-generated content produced between the prompt and the answer, intended to decompose a task into steps that are individually easier than the whole. It is a family of inference strategies, not a general instruction to make a model verbose.

**Chain**: One ordered sequence of intermediate reasoning terminating in exactly one candidate answer. A run may produce several chains.

**Reasoning trace**: The recorded text of a chain. A trace is an inference-time workspace or an explanation artifact; it is never a record of the computation that produced the answer.

**Candidate answer**: The typed value a deterministic extractor recovers from a chain. A chain that yields no parseable candidate is a generation failure, not a partial success.

**Answer extraction**: The deterministic parsing and normalisation of a chain into a typed candidate answer under a declared output schema. Extraction is owned by software, never by a second model call, wherever the schema is expressible.

**External verification**: A check whose verdict is computed from something outside the chain being checked: a deterministic function, an executed program, a schema validator, a retrieved primary source, a tool postcondition, or an independent human judgement.

**Internal consistency**: Agreement of a chain with itself, or agreement among chains sharing a generator, prompt, and evidence set. Internal consistency is a diagnostic signal and is explicitly not verification.

**Faithfulness**: The degree to which a stated trace reflects the influences that actually determined the answer. Low faithfulness means the trace is a plausible reconstruction rather than a causal record.

**Reasoning model**: A model that allocates internal test-time computation without being prompted to do so, exposing an effort or thinking budget rather than requiring an explicit reasoning instruction.

**Workhorse model**: A lower-latency model used for well-defined execution where the task contract does not require intermediate reasoning.

**Decision contract**: The declared objective, output schema, hard constraints, allowed evidence, tool permissions, risk tier, acceptance tests, quality threshold, latency limit, cost limit, and abstention behaviour, fixed before any technique is selected. The originating prose source names this artifact the task contract; this guide adopts the corpus term.

**Budget ledger**: The record naming every bounded resource for the run, each with a numeric limit: output tokens, reasoning tokens, candidates, chain steps, search nodes, tool calls, retries, wall-clock latency, and money.

**Effort budget**: The subset of the budget ledger governing intermediate reasoning specifically, expressed as a reasoning-token ceiling, a chain-step ceiling, a candidate count, and a search depth and breadth where applicable.

**Warrant gate**: The deterministic decision, taken before any technique is selected, that returns use intermediate reasoning, suppress it, or route the task to a deterministic function. Its verdict and reason code are recorded in run metadata.

**Selection ladder**: The ordered inventory of reasoning techniques, each paired with the observable condition that indicates it and the incremental cost it adds over the rung below.

**Reason code**: A normalised categorical label recorded with every gate verdict, technique selection, bound breach, verification outcome, and exit, drawn from a closed vocabulary.

**Disclosure boundary**: The rule permitting the logging of decision metadata while prohibiting the retention, exposure, or contractual requirement of hidden reasoning content.

**Authorisation artifact**: The verified record that permits an action to proceed: a passing deterministic check, an executed tool postcondition, a retrieved source, or a recorded human approval. A chain is never an authorisation artifact.

**Correlated failure**: Agreement among chains, candidates, or verifiers sharing a generator, prompt, premise, or evidence source, mistaken for independent confirmation.

**Source class**: The label attached to every verification signal naming its origin: deterministic function, executed program, schema validator, retrieved primary source, external tool, independent model, same model, or human.

**Exit condition**: A declared terminal state that alone may end a run: verified success, acceptable partial completion under the contract, safe abstention, human takeover, budget exhaustion, deadline, unrecoverable constraint violation, or diminishing returns.

**Overthinking**: Expenditure of reasoning effort disproportionate to task difficulty, including revision of an already correct answer until it changes. It is a quality problem and an availability problem at once.

### 1.2 The Non-Evidential Status of a Reasoning Trace

This is the guide's central discipline and it constrains every phase that follows.

**Three products, never interchangeable**: A deployment produces three distinct artifacts and must keep them separate in storage, in access control, and in reasoning about correctness. The first is the intermediate reasoning used to solve the task. The second is the evidence and verification record used to audit the outcome. The third is the concise explanation returned to the requester. Treating the first as though it were the second is the failure this guide exists to prevent.

**A chain is not a causal record**: A model can emit a coherent chain that does not reflect the computation producing its answer. The originating source cites work showing that models may rely on biased hints while omitting those hints from stated reasoning, and work proposing interventions such as truncating, corrupting, or paraphrasing a chain to measure how much the answer actually depends on it. It further reports measured hint acknowledgment rates of 25 percent and 39 percent across hint types for two tested reasoning models, and below 2 percent acknowledgment in most reward-hacking scenarios studied, while noting the limitations of contrived multiple-choice settings. These figures are transcribed from the source and were not re-verified during conversion; they are cited here to establish that low acknowledgment is observed, not to fix a numeric expectation.

**Persuasion hazard**: A plausible chain terminating in a wrong answer is more persuasive to a human reviewer and to a downstream model than a bare wrong answer. Visible steps therefore raise the cost of an undetected error rather than lowering it. Agents must never elicit a visible rationale for the purpose of creating confidence, and must never present a chain as a justification artifact.

**Internal consistency is not verification**: A chain that contradicts nothing in itself has demonstrated nothing about the world. Agreement among candidate chains is likewise not correctness, because correlated candidates can unanimously repeat one misconception. Every acceptance decision must rest on at least 1 signal whose source class lies outside the generating model, prompt, and evidence set that produced the chain.

**Monitoring is a signal, not a proof**: Reading a trace can reveal an unsafe plan, a fabricated intermediate fact, or an attempt at exploitation, and that value is real. The absence of suspicious text in a trace establishes nothing about the absence of suspicious computation. Trace monitoring may therefore raise an alarm but may never clear a risk.

**The authorisation rule**: A chain is never the artifact that authorises an action. An action proceeds only against an authorisation artifact: a passing deterministic check, an executed tool postcondition confirmed against its declared result, a retrieved primary source, or a recorded human approval. This rule holds regardless of chain length, chain fluency, or the number of agreeing candidates.

### 1.3 The Warrant Gate: Conditions for Intermediate Reasoning and Its Suppression

Intermediate reasoning costs output tokens, reasoning tokens, and latency, and it does not help uniformly. On direct retrieval and mechanical transformation it adds cost and can introduce error by inventing connective material where none was required. The warrant gate is a deterministic classifier evaluated before any technique is selected, bounded to 1 percent of the task's declared token budget, returning one of three verdicts with a reason code.

**Warrant conditions**: Intermediate reasoning is warranted where at least 1 of the following is observably present. The answer depends on 2 or more nontrivial dependencies that cannot be resolved in a single lookup. Decomposition changes what evidence must be collected. At least 2 plausible solution paths compete and the choice between them is not determined by the input alone. A plan must coordinate 2 or more tool calls whose ordering matters. The cost of an unsupported answer is high because the action it triggers is irreversible, regulated, or safety-relevant. Mathematical derivation, code debugging, policy application to a concrete fact pattern, multi-document synthesis, constraint satisfaction, hypothesis comparison, and agent planning are the recurring task classes that satisfy these conditions.

**Suppression conditions**: Intermediate reasoning is suppressed where the task is direct retrieval of a stated fact, extraction into a fixed schema, classification over a closed label set, stylistic rewriting that preserves content, or a calculation a deterministic function computes exactly. It is also suppressed where the direct baseline already passes 100 percent of the contract's acceptance tests, since the only remaining effect of added reasoning is cost. Easy work routes to a workhorse model or to a deterministic tool rather than to a reasoning configuration.

**The baseline precondition**: No reasoning configuration is enabled without a measured direct baseline on the same immutable evaluation set. The default requirement is a set of at least 30 examples, a verified accuracy gain of at least 5 percentage points over the direct baseline, and a lower bound of the 95 percent bootstrap interval on that gain above 0. A configuration failing any of the three is not promoted, and the task reverts to the baseline.

**Numeric suppression rules**: Suppress where the task presents fewer than 2 nontrivial dependencies and fewer than 2 competing solution paths. Suppress where the p95 end-to-end latency of the reasoning configuration exceeds the contract's latency limit, since a correct answer delivered after the deadline fails the contract. Suppress where the reasoning configuration's cost per successful outcome exceeds the baseline's by more than 100 percent at matched verified accuracy. Record the suppression reason code in every case, because suppressions are the data that later corrects the gate.

**Warrant Gate Decision Table**:

| Observable condition | Verification available | Gate verdict |
| :-- | :-- | :-- |
| 2 or more nontrivial dependencies, baseline fails acceptance | Deterministic test or retrieved source | Use intermediate reasoning |
| 2 or more competing solution paths, no input-determined choice | Normalisable answer space | Use intermediate reasoning; consider sampled candidates |
| Plan coordinates 2 or more ordered tool calls | Tool postconditions | Use intermediate reasoning; interleave with actions |
| Irreversible or regulated action pending | Independent external signal | Use intermediate reasoning; verify before acting |
| Exact arithmetic, date logic, or symbolic transformation | Executable runtime | Suppress; route to a deterministic function |
| Single-hop retrieval or fixed-schema extraction | Schema validator | Suppress; execute directly |
| Closed-label classification, stylistic rewriting | Schema validator | Suppress; execute directly on a workhorse model |
| Baseline passes 100 percent of acceptance tests | Already established | Suppress; record the baseline sufficiency code |
| Task turns on current facts or proprietary documents | Retrieval index with provenance | Retrieve first; reasoning does not substitute for evidence |
| Latency limit below measured p95 of the configuration | Not applicable | Suppress; route to the baseline with a declared fallback |

**Evidence precedence**: Where a task turns on current facts, proprietary documents, or exact citations, retrieval precedes reasoning and constrains it. Reasoning never substitutes for evidence. Where required evidence is unavailable after the retrieval budget is exhausted, the run returns an uncertainty-qualified answer or abstains; it does not spend further reasoning tokens manufacturing connective tissue between facts it does not hold.

**Safety precedence**: Where inputs may contain secrets, personal data, credentials, privileged material, or adversarial instructions, the gate applies redaction, tokenisation of sensitive spans, and isolation of untrusted content before any chain is elicited, and it reduces trace capture to a protected structured record. Where the trace itself would expose security policy or exploitable internal decisions, no trace is retained.

### 1.4 Execution Tier Partition and the Authorisation Rule

Every unit of work in this method belongs to exactly one execution tier, and every phase boundary that crosses tiers names its handoff. The partition is what separates an operational reasoning deployment from a prompt that asks a model to think.

**Deterministic tier**: Software, scripts, schema validators, executable runtimes, and APIs own the work requiring exactness, reproducibility, auditability, or scale. This tier owns the warrant gate evaluation, the effort budget and every bound in the budget ledger, step-count and depth enforcement, candidate scheduling and cancellation, answer extraction and normalisation, verification execution, disagreement adjudication against declared precedence, the disclosure boundary, and the logging of decision metadata. This tier rejects any output that fails schema validation, any candidate exceeding a declared bound, any action lacking an authorisation artifact, and any log record containing hidden reasoning content.

**Model tier**: LLM calls own the work requiring open-vocabulary judgement, natural-language understanding, synthesis, and generation. This tier owns the intermediate reasoning itself, the answer proposal, the decomposition of a problem into subproblems, the drafting of verification questions, the critique of a draft against a stated rubric, and the interpretation of retrieved text. This tier is never permitted to decide alone whether its own answer is correct, whether a bound may be extended, whether an action is authorised, or what is written to the audit record.

**Hybrid tier**: Work in which the model proposes and software verifies, or software retrieves and the model adjudicates. Technique selection is hybrid: the model may characterise the failure mode, and a deterministic rule maps that characterisation to a ladder rung. Claim checking is hybrid: the model drafts the verification questions, and deterministic tools or retrieval answer them. Rubric scoring is hybrid: the model scores, and software enforces blinding, order randomisation, and threshold comparison.

**Authority on disagreement**: Where the deterministic tier and the model tier disagree, the deterministic tier holds authority without exception. An executed calculation overrides a stated calculation. A schema validator overrides a claimed conformance. A retrieved source overrides a recalled fact. A tool postcondition overrides a narrated outcome. Where a deterministic check is unavailable for a claim, the claim carries an unsupported marker into the response rather than inheriting the chain's confidence.

**Tier Ownership of the Reasoning Pipeline**:

| Work unit | Owning tier | Authority on disagreement |
| :-- | :-- | :-- |
| Warrant gate verdict and reason code | Deterministic | Deterministic; a model may not overturn a suppression |
| Baseline execution and comparison | Deterministic | Deterministic |
| Failure-mode characterisation | Model | Deterministic rule maps the characterisation to a rung |
| Technique selection from the ladder | Hybrid | Deterministic; the rule binds the selection |
| Effort budget, step and depth bounds | Deterministic | Deterministic; bounds are never extended in flight by a model |
| Intermediate reasoning generation | Model | Not applicable; the tier proposes only |
| Answer proposal | Model | Not applicable; the tier proposes only |
| Answer extraction and normalisation | Deterministic | Deterministic; an unparseable chain is a failure |
| Candidate equivalence class assignment and winning share | Deterministic | Deterministic |
| Verification question drafting | Model | Deterministic tools answer the questions |
| Verification execution and verdict | Deterministic | Deterministic without exception |
| Rubric scoring where no oracle exists | Hybrid | Deterministic enforces blinding and thresholds |
| Action authorisation | Deterministic | Deterministic; a chain never authorises |
| Disclosure boundary enforcement | Deterministic | Deterministic; enforcement may veto a release |
| Metric computation and policy correction | Deterministic | Deterministic |

**Boundary against meta-reasoning**: This guide owns the decision taken before and around a reasoning run: whether intermediate reasoning is used at all, which technique is configured, what effort it may consume, and what external check its conclusion must pass. The corpus guide on meta-reasoning owns the in-flight control loop that monitors an active reasoning process and decides at each checkpoint whether to continue, verify, repair, switch, branch, escalate, or stop. Agents running long or adaptive reasoning episodes should invoke that loop for in-flight control and treat the phases here as the configuration and verification envelope surrounding it. The two are complementary; neither restates the other.

***

## II. Operational Framework: Warranted, Bounded, and Externally Verified Reasoning

The framework assumes a request, an authorised operating context, and access to a deterministic execution tier. Phases 1 through 3 configure the run, Phases 4 and 5 execute and verify it, Phase 6 releases it, and Phase 7 corrects the policy that produced it. Phase 5 may return control to Phase 4 exactly once per acceptance failure, under the bounds declared in Phase 3.

### Phase 1: Contract Establishment and Reasoning-Warrant Determination

**Objective**: Fix the decision contract, measure the direct baseline, and decide whether intermediate reasoning is warranted at all, so that reasoning effort is spent only against a named failure it might repair.

#### Step 1.1: Establish the Decision Contract and Budget Ledger

**Required Actions**:

- State the objective, output schema, hard constraints, allowed evidence sources, tool permissions, and risk tier as structured fields a validator can inspect.
- Define acceptance tests that return pass or fail without interpretation, and name the role or function that evaluates each.
- Declare the abstention behaviour, so that unknown remains a reportable outcome distinct from failure.
- Record a numeric limit for every bounded resource: output tokens, reasoning tokens, candidates, chain steps, search nodes, tool calls, retries, wall-clock latency, and money.
- Reject the run where any mandatory contract field is unpopulated, obtaining clarification or applying a documented conservative default rather than proceeding on an inferred requirement.

**Required Outputs**:

- A decision contract record with objective, output schema, acceptance tests, evidence standard, and risk tier.
- A budget ledger naming every bounded resource and its numeric limit.
- A declared abstention behaviour and a declared fallback path.

**Quality Checkpoints**:

- Every acceptance test returns pass or fail without interpretation; an untestable criterion halts the run before any inference is spent.
- Every budget dimension carries a numeric limit; an unbounded dimension halts the run.
- The contract distinguishes abstention from failure, so a supported abstention is not scored as a task failure.

***

#### Step 1.2: Execute the Direct Baseline and Record Its Failure Signature

**Required Actions**:

- Route the task to the cheapest valid method first: a deterministic function where one computes the answer exactly, otherwise a direct prompt on a workhorse model with no reasoning instruction.
- Execute the baseline against the contract's acceptance tests on an immutable evaluation set of at least 30 examples, holding model identifier, prompt version, and inference parameters pinned.
- Record verified accuracy, p50 and p95 latency, input and output token counts, and cost per attempted and per successful task.
- Classify each baseline failure into a named signature: missing dependency, arithmetic or unit error, unsupported claim, schema violation, missing external information, format drift, or stochastic path variance.
- Close the run at the baseline where it passes 100 percent of acceptance tests, recording the baseline sufficiency reason code.

**Required Outputs**:

- A baseline measurement record with verified accuracy, latency percentiles, token counts, and cost.
- A failure signature distribution naming each signature and its share of observed failures.
- A pinned configuration record for the baseline: provider, model identifier, prompt version, and inference parameters.

**Quality Checkpoints**:

- The baseline ran on the same immutable evaluation set that any later reasoning configuration will run on; a comparison across differing sets is void.
- Every baseline failure carries exactly 1 primary signature; unclassified failures above 10 percent of the total halt technique selection.
- The baseline record states cost per successful task, not cost per call, so later comparisons are made at matched quality.

***

#### Step 1.3: Apply the Warrant Gate and Record the Verdict

**Required Actions**:

- Evaluate the warrant conditions and the suppression conditions in Section 1.3 against the task and the baseline failure distribution, spending no more than 1 percent of the declared token budget on the gate itself.
- Apply evidence precedence: where the task turns on current facts, proprietary documents, or exact citations, schedule retrieval before any reasoning configuration and constrain claims to the retrieved set.
- Apply safety precedence: scan inputs for secrets, personal data, credentials, privileged material, and injected instructions; redact or tokenise sensitive spans and label untrusted content before any chain is elicited.
- Emit exactly 1 verdict with a reason code: use intermediate reasoning, suppress and execute directly, or route to a deterministic function.
- Record the verdict, the reason code, the triggering conditions, and the baseline comparison in run metadata regardless of which verdict was returned.

**Required Outputs**:

- A warrant gate record carrying the verdict, reason code, and the conditions that triggered it.
- A redaction and labelling record naming every sensitive span handled and every untrusted content block isolated.
- A retrieval schedule where evidence precedence applies, or a recorded finding that it does not.

**Quality Checkpoints**:

- Exactly 1 verdict is emitted per run; a run proceeding without a recorded verdict is a control defect and halts.
- Gate cost stays within 1 percent of the declared token budget; a gate consuming more than the reasoning it governs is removed and replaced by a static routing rule.
- No chain is elicited before the safety scan completes, so sensitive material is never written into a trace that policy then has to purge.

***

### Phase 2: Technique Selection From the Ladder

**Objective**: Map the observed baseline failure to the smallest reasoning intervention that could repair it, selecting exactly one primary technique with a declared stopping rule rather than combining variants by default.

**The Selection Ladder**: Rungs are ordered by incremental cost over the rung below. Agents select the lowest rung whose observable condition holds. Detailed operation of each named variant belongs to the sibling guides in this category; this table states only the condition that indicates the rung and the bound that contains it.

| Rung | Observable condition | Technique | Default bound |
| :-- | :-- | :-- | :-- |
| 0 | Baseline passes acceptance | Direct answer | No reasoning tokens |
| 1 | Missing intermediate steps on a conventional model | Zero-shot intermediate reasoning | 12 chain steps |
| 2 | Stable reasoning grammar, format or convention drift | Few-shot exemplars, versioned as data | 3 to 8 exemplars |
| 3 | Dependencies form a mostly linear partial order | Least-to-most or plan-and-solve decomposition | 8 subproblems |
| 4 | Exact arithmetic, date logic, or symbolic transformation | Program-aided reasoning in a sandbox | 2 program attempts |
| 5 | Answer requires external information or side effects | Tool-interleaved reasoning | 8 authorised actions |
| 6 | Stochastic path variance, answers normalisable | Sampled candidates with agreement aggregation | 3 candidates, expanding to 9 |
| 7 | Local choices create distinct futures, recovery matters | Tree or graph structured search | Breadth 3, depth 5, 40 nodes |
| 8 | Fact-dense output with unsupported claims | Verification-question drafting and revision | 1 verification round |
| 9 | Rubric-correctable defects in a draft | Critique and revision with separated roles | 3 revision cycles |
| 10 | Surface detail obscures a governing principle | Abstraction before instantiation | 1 abstraction step |

#### Step 2.1: Classify the Failure Mode and Locate the Matching Rung

**Required Actions**:

- Take the dominant failure signature from Step 1.2 as the selection input; where no signature exceeds 40 percent of failures, treat the distribution as mixed and split the task by class rather than selecting one technique for all of it.
- Match the signature to a ladder rung using the deterministic mapping rule, allowing a model call only to characterise an ambiguous signature, never to choose the rung.
- Record a failure hypothesis in one sentence stating why the selected rung should repair the observed signature and what measurement would falsify it.
- Reject any selection whose hypothesis cannot name a measurable prediction, since an unfalsifiable selection cannot be corrected by Phase 7.

**Required Outputs**:

- A dominant failure signature with its measured share of failures.
- A selected ladder rung with the deterministic rule that produced the selection.
- A one-sentence falsifiable failure hypothesis.

**Quality Checkpoints**:

- The selection derives from a measured failure distribution, not from an impression of task difficulty.
- Exactly 1 primary technique is selected; a second technique may be added only after Phase 7 measures the first and records an unrepaired residual signature.
- The failure hypothesis names a measurement that would show the technique did not help.

***

#### Step 2.2: Configure the Rung and Declare Its Stopping Rule

**Required Actions**:

- Take the rung's declared bounds from the selection ladder and write them into the budget ledger as hard limits, never as guidance.
- Declare the stopping rule for the rung before any generation: the condition that ends the technique successfully, the condition that ends it in fallback, and the bound that ends it in truncation.
- Name the fallback path for every stopping condition, defaulting to the direct baseline answer carried with an explicit limitation statement.
- Record the technique, its configuration, and its stopping rule in the versioned configuration registry, so the run is reproducible and the policy is correctable.

**Required Outputs**:

- A technique configuration record with every bound expressed numerically.
- A declared stopping rule with success, fallback, and truncation conditions.
- A registry entry pinning technique, configuration, and prompt version.

**Quality Checkpoints**:

- Every loop in the selected technique has an entry condition, an exit condition, and a numeric cap; an uncapped loop halts the run before generation.
- The stopping rule was declared before any output was observed; a rule adjusted after seeing outputs invalidates the run's acceptance decision.
- The fallback path is executable without further model calls, so a failed technique degrades to a known answer rather than to no answer.

***

### Phase 3: Prompt and Effort Configuration

**Objective**: Configure the prompt to the model class actually being called and bind the run to a numeric effort budget whose breach behaviour is declared in advance.

#### Step 3.1: Determine the Model Class and Set the Prompt Contract

**Required Actions**:

- Classify the served model as a reasoning model that allocates internal test-time computation without prompting, or as a conventional model that does not, using the provider's documented behaviour for the exact served checkpoint rather than a family name.
- For a conventional model on a warranted task, state the objective, constraints, evidence boundary, and required output schema, and request that dependencies be worked through and the result checked before the answer is returned.
- For a reasoning model, keep the prompt simple and direct, state the end state and constraints, attempt zero-shot first, and omit explicit step-by-step reasoning instructions, which the originating source reports may fail to help and can degrade performance on such models.
- Request the answer, the evidence, the checks performed, and a concise decision record; never request disclosure of hidden reasoning content from any model class.
- Prohibit stacking a legacy reasoning template onto a reasoning-trained model until a paired evaluation on the immutable set shows a gain whose 95 percent interval lower bound exceeds 0.

**Required Outputs**:

- A model class determination naming the exact served checkpoint, quantisation where known, and inference settings.
- A prompt contract stating objective, constraints, evidence boundary, output schema, and requested artifacts.
- A recorded prohibition or authorisation for explicit reasoning instructions on the selected model.

**Quality Checkpoints**:

- The prompt requests verifiable artifacts and a concise decision record, never a transcript of private reasoning.
- No explicit reasoning instruction is present on a reasoning model without a recorded paired-evaluation result authorising it.
- The model class determination names a served checkpoint and its settings; a family label alone is treated as unknown and blocks promotion.

***

#### Step 3.2: Set the Effort Budget and Declare Its Breach Behaviour

**Required Actions**:

- Write the rung's bounds into an effort budget: a reasoning-token or thinking-token ceiling, a chain-step ceiling, a candidate count, a search breadth and depth where applicable, an action count, and a retry count.
- Treat any provider-exposed reasoning or thinking budget as a tunable parameter rather than a quality guarantee, since the originating source reports task-dependent diminishing returns and increased latency as the budget grows.
- Set the default ceilings where the task class supplies no measured value: 12 chain steps for unstructured reasoning, reasoning tokens at no more than 4 times the baseline output token count, 3 sampled candidates expanding to no more than 9, search breadth 3 and depth 5 within 40 nodes, 8 authorised actions, 3 revision cycles, and 2 retries for malformed output.
- Declare the breach behaviour for every ceiling before generation: truncate the chain at the bound, extract whatever candidate the truncated chain yields, mark the run bound-limited, and route it to verification rather than extending the bound.
- Prohibit in-flight bound extension by any model-tier component; a bound is changed only by a versioned policy revision informed by Phase 7 measurement.

**Required Outputs**:

- An effort budget record with a numeric ceiling for every dimension the technique consumes.
- A declared breach behaviour per ceiling, naming truncation, fallback, or abstention.
- A bound-limited flag definition that later metric computation can group on.

**Quality Checkpoints**:

- Every dimension the selected technique consumes carries a ceiling; a consumed dimension without a ceiling halts the run.
- Breach behaviour terminates in truncation, fallback, or abstention; no breach behaviour permits continuing past a bound.
- No component below the deterministic tier holds the authority to raise a ceiling during a run.

***

#### Step 3.3: Construct and Validate the Context Under the Trust Boundary

**Required Actions**:

- Retrieve the evidence the contract admits, deduplicate it, attach provenance identifiers, and fit it within the context budget alongside the prompt contract.
- Delimit trusted instructions from untrusted content with an explicit boundary marker, and label every retrieved document, tool observation, prior memory, and candidate chain fed back into another model as data rather than instruction.
- Scan the assembled context for secrets, personal data, and injected instructions before dispatch, and reject the assembly on any hit rather than relying on the model to ignore the content.
- Store exemplars, tool schemas, rubrics, and routing rules as versioned data in a registry rather than inline in application logic, and pin the version used for the run.
- Return to retrieval where evidence coverage fails the contract's standard, repeating until coverage passes or the retrieval budget is exhausted; on exhaustion, narrow the answer or abstain.

**Required Outputs**:

- A validated context assembly with provenance identifiers on every evidence item.
- A trust boundary record naming every untrusted block and the label applied to it.
- Pinned versions for prompt, exemplar set, tool schema, rubric, retrieval index, and policy.

**Quality Checkpoints**:

- Every evidence item carries a provenance identifier and a content hash; an unattributed item is removed before dispatch.
- Retrieved and observed content is labelled as data in 100 percent of cases; an unlabelled untrusted block halts dispatch.
- Every configuration element the run depends on carries a pinned version, so the run is reproducible to the extent the provider permits.

***

### Phase 4: Bounded Generation and Answer Extraction

**Objective**: Produce candidate work within the declared bounds and reduce it to a typed candidate answer by deterministic extraction, so that the chain is consumed as a workspace rather than accepted as a result.

#### Step 4.1: Execute One Bounded Generation Tranche

**Required Actions**:

- Dispatch the configured call with pinned model and prompt versions, the declared effort budget, explicit success criteria, and a structured output contract.
- Launch only the initial candidate set for sampled or search techniques, deferring expansion to Step 5.3 and never fanning out beyond the declared breadth in a single tranche.
- Enforce every ceiling in the deterministic tier through cancellation and deadline mechanisms, not through instructions in the prompt, since a prompt cannot bind a bound.
- Halt the tranche the moment a ceiling is reached, marking the run bound-limited and recording which dimension bound it.
- Retry a malformed output at most 2 times, then execute the declared fallback rather than reformulating the request a third time.

**Required Outputs**:

- A candidate set with one record per chain, carrying candidate identifier, parent identifier, depth, and branch index where applicable.
- A consumption record per dimension: reasoning tokens, output tokens, steps, nodes, actions, retries, and latency.
- A bound-limited flag with the binding dimension named where a ceiling was reached.

**Quality Checkpoints**:

- No dimension exceeds its declared ceiling; an overrun indicates enforcement sits in the prompt rather than in software and halts the configuration.
- Every candidate carries a stable identifier and a parent reference, so aggregation and pruning decisions are auditable.
- Retries stop at the declared count; an unbounded retry loop is a control defect, not a robustness feature.

***

#### Step 4.2: Extract and Normalise the Candidate Answer

**Required Actions**:

- Parse each chain with a deterministic extractor bound to the contract's output schema, recovering a typed candidate answer and discarding the remainder of the chain from the acceptance path.
- Normalise units, numeric precision, date formats, casing, and enumerations before any comparison, so that formatting variance is not counted as semantic disagreement.
- Compute an answer hash per candidate and group semantically equivalent candidates into equivalence classes, recording class size and the winning share of the leading class over eligible candidates.
- Mark any chain yielding no parseable candidate as a generation failure and exclude it from the eligible-candidate denominator rather than treating it as a dissenting vote.
- Record, for every candidate, the evidence identifiers it cites and the tool call identifiers it invoked, so verification can be targeted at claims rather than at prose.

**Required Outputs**:

- A typed candidate answer per chain, with normalised value and answer hash.
- An equivalence class inventory with class sizes and the winning share computed as the leading class over eligible candidates.
- A generation failure count with the parse defect named for each.

**Quality Checkpoints**:

- Extraction is performed by software in 100 percent of cases where the schema is expressible; a model call used as the extractor is a tier violation.
- Normalisation precedes class assignment, so no class split is attributable to formatting alone.
- Winning share is reported over eligible candidates, and is recorded as a diagnostic signal rather than as a correctness verdict.

***

#### Step 4.3: Detect Overthinking and Enforce the Direct-Solve Route

**Required Actions**:

- Compute the reasoning-token share as reasoning tokens over total output tokens for the run, and raise an anomaly where it exceeds 60 percent on a task class whose measured median is below 30 percent.
- Detect answer oscillation by comparing the candidate answer at each declared checkpoint against the prior one, and flag any run whose answer changes more than 2 times without a new external signal arriving between changes.
- Compare consumed effort against the task class's measured median, and route any run exceeding 3 times that median to truncation and verification rather than to continued generation.
- Treat disproportionate effort on an easy task as a possible induced-slowdown condition, since the originating source records demonstrated slowdown attacks against reasoning models, and apply the deadline and the direct-solve route rather than raising the budget.
- Preserve the direct-solve route as an always-available fallback that returns the baseline answer with an explicit limitation statement.

**Required Outputs**:

- A reasoning-token share figure with its task-class median for comparison.
- An oscillation count with the checkpoint indices at which the answer changed.
- An overthinking anomaly record where any threshold was crossed, naming the threshold and the action taken.

**Quality Checkpoints**:

- Every anomaly terminates in truncation, fallback, or abstention; no anomaly is resolved by extending the effort budget.
- The direct-solve route is reachable at every point in the run without a further configuration decision.
- Effort anomalies are recorded with their task-class baseline, so a class whose median genuinely rose is corrected by policy rather than by suppressing the alert.

***

### Phase 5: External Verification and Action Authorisation

**Objective**: Establish the answer against signals outside the chain that produced it, adjudicate disagreement in favour of the deterministic tier, and permit an action only against an authorisation artifact.

#### Step 5.1: Assemble the External Check Set by Claim Class

**Required Actions**:

- Decompose the candidate answer into claims and classify each as arithmetic or symbolic, factual and attributable, structural, procedural with a side effect, or subjective without a deterministic oracle.
- Assign each class its check: execute arithmetic and symbolic claims in a sandboxed runtime; check factual claims against retrieved evidence and open every citation; validate structural claims against the output schema; check procedural claims against declared tool postconditions; score subjective claims against a rubric under blinded presentation.
- Prefer retrieval and deterministic tools over model self-verification wherever a deterministic check exists for the claim class, since self-verification shares the blind spots that produced the claim.
- Label every check with its source class, and require at least 1 check whose source class lies outside the generating model, prompt, and evidence set for every claim the contract designates critical.
- Mark a claim unsupported where no check of an admissible source class is available, and carry that marker into the response rather than allowing chain confidence to stand in for it.

**Required Outputs**:

- A claim inventory with a class label and an assigned check per claim.
- A check set with a source class recorded per check.
- An unsupported-claim list naming every claim for which no admissible check existed.

**Quality Checkpoints**:

- 100 percent of claims the contract designates critical carry at least 1 external check; a critical claim without one blocks release.
- No claim is accepted on internal consistency of its chain, on agreement among chains sharing a generator, or on a self-verification pass alone.
- Sandbox constraints hold for every executed check: network egress denied, no mounted secrets, restricted packages and system calls, and capped processor, memory, output, and wall time.

***

#### Step 5.2: Execute Verification and Adjudicate Disagreement

**Required Actions**:

- Run every assigned check and record its verdict, its source class, and the artifact it produced, keeping the verdict separate from the chain that proposed the claim.
- Apply the deterministic precedence rule on any disagreement: an executed calculation overrides a stated one, a schema validator overrides a claimed conformance, a retrieved source overrides a recalled fact, and a tool postcondition overrides a narrated outcome.
- Test agreement for independence before treating it as confirmation, tracing every agreeing signal to its generator, prompt, premise set, and evidence source, and recording a correlated failure where a shared origin is found.
- Treat a successful program exit status as evidence of execution and not of semantic correctness, adding invariants or tests that the expected result must satisfy.
- Route a verification failure by its cause: a local diagnosable defect proceeds to Step 5.3, a coverage gap returns to Step 3.3 for further retrieval, and a safety violation halts the run immediately with no revision attempt.

**Required Outputs**:

- A verification record per claim with verdict, source class, and produced artifact.
- An independence assessment for every observed agreement, with correlated failures named.
- A routed disposition per failure: revise, retrieve, or halt.

**Quality Checkpoints**:

- The deterministic verdict prevails in 100 percent of recorded disagreements; a model-tier override is a tier violation and voids the run.
- Every agreement used as confirmation carries an independence assessment; agreement among same-generator candidates is never counted as independent confirmation.
- A safety violation halts without revision; this class is never resolved by another generation pass.

***

#### Step 5.3: Revise or Expand Once, Then Authorise or Withhold

**Required Actions**:

- Supply the reviser with the failing criterion, the failing artifact, and the evidence that established the failure, never a generic instruction to improve the answer.
- Expand a sampled candidate set by a small batch only where the winning share remains below the preregistered agreement threshold, defaulting to 0.67, and only where the effort budget permits; expand a search only at the best externally verified frontier states.
- Take exactly 1 additional authorised action in a tool-interleaved run, and only where that action is expected to reduce a named uncertainty.
- Repeat generation and verification only until acceptance passes, no metric improves by the declared minimum delta for 2 consecutive cycles, or any declared cap is reached; the second condition triggers fallback or escalation and the third returns the best verified partial answer with limitations.
- Authorise an action only against an authorisation artifact, and withhold the action where none exists, recording a safe abstention rather than proceeding on chain confidence.

**Required Outputs**:

- A revision record naming the failing criterion supplied and the change produced.
- An authorisation decision per pending action, citing the specific authorisation artifact or recording its absence.
- An exit record naming which of the declared exit conditions terminated the run.

**Quality Checkpoints**:

- No acceptance criterion is relaxed inside the loop; a threshold changed after outputs were observed voids the acceptance decision.
- Every authorised action cites an authorisation artifact whose source class is external to the chain; a chain cited as an authorisation artifact halts release.
- The run terminates on exactly 1 declared exit condition; termination by exhaustion without a recorded condition is a control defect.

***

### Phase 6: Disclosure-Bounded Release and Instrumentation

**Objective**: Return the answer, its material evidence, and its uncertainty within the disclosure boundary, and record the decision metadata that later measurement and audit require without persisting reasoning content.

#### Step 6.1: Produce the Response Within the Disclosure Boundary

**Required Actions**:

- Return the requested answer under the contract's output schema, together with the material evidence identifiers, the stated uncertainty, and a concise verification summary naming which checks ran and what they returned.
- Withhold hidden reasoning content, raw security deliberation, credentials, personal data, and untrusted instruction text from the response in every case.
- Present unsupported claims with their marker intact, and present a bound-limited run as bound-limited rather than as a complete result.
- Keep the explanation concise and evidence-based, and never present it as a record of how the answer was computed.
- Run the release checks before returning: schema conformance, citation resolution, privacy scan, and disclosure scan, halting release on any failure.

**Required Outputs**:

- A response conforming to the contract's output schema.
- A verification summary naming each executed check and its verdict.
- A release check record with a verdict per check.

**Quality Checkpoints**:

- The response contains 0 tokens of hidden reasoning content and 0 unredacted sensitive spans.
- Every citation in the response resolves to a retrieved evidence identifier; an unresolvable citation halts release.
- The response distinguishes verified claims, unsupported claims, and abstentions, so a reader cannot mistake one for another.

***

#### Step 6.2: Record Decision Metadata Under the Disclosure Boundary

**Required Actions**:

- Record one trace per user-visible task with child records for the warrant gate, retrieval, each model call, each candidate, each search node, each tool call, each verification, aggregation, and formatting.
- Record at run level the task class, risk tier, dataset name and version, example identifier, input content hash, gate verdict and reason code, selected rung, technique configuration, exit condition, abstention flag, error class, fallback path, human review status, and retention class.
- Record at call level the provider, endpoint, requested and returned model identifiers, response identifier, inference parameters, seed, effort or thinking budget setting, input, cached, output, reasoning, and total token counts, first-token and total latency, finish reason, retry count, and computed cost.
- Record at candidate level the candidate and parent identifiers, depth, branch index, normalised answer, answer hash, cited evidence identifiers, tool call identifiers, verifier outputs and source classes, scores with the scoring configuration that produced them, confidence, calibration bin, safety flags, and pruning reason.
- Enforce the disclosure boundary at write time: log reason codes, evidence references, verdicts, and cost figures; do not persist private chain-of-thought by default, do not log credentials or unrestricted personal data, and replace raw payloads with content hashes and access-controlled references.

**Required Outputs**:

- A complete trace with stable identifiers linking every child record to its parent.
- A run-level, call-level, and candidate-level metadata record populated to the declared field inventory.
- A retention class assignment per record, with deletion propagation defined across the trace store and any referenced object store.

**Quality Checkpoints**:

- 0 reasoning traces are persisted where policy does not explicitly permit them; a detected trace in the log halts release and triggers purge and re-instrumentation.
- Every score recorded carries the identity, version, and settings of whatever produced it; a score without them is not reproducible and is excluded from measurement.
- Capture is allowlist-based with field-level redaction applied before export, and safety events are preserved ahead of any sampling.

***

### Phase 7: Outcome Measurement and Policy Correction

**Objective**: Compute quality, efficiency, calibration, and faithfulness from the recorded metadata, and correct the warrant gate, ladder, and bounds from measured outcomes rather than from single cases.

#### Step 7.1: Compute the Quality, Efficiency, and Calibration Metric Set

**Required Actions**:

- Compute verified accuracy as passing examples over eligible examples, stratified by task class, risk tier, dataset version, model revision, and prompt version, and never pooled across strata.
- Compute effort efficiency as tokens and cost per attempted task, per successful task, and per accuracy point gained over the direct baseline, reporting reasoning-token share and cache-hit rate alongside.
- Compute latency at median, p90, p95, and p99 for end-to-end runs and for each span type, and report retry rate, tool-error rate, timeout rate, and wasted effort from pruned or cancelled branches.
- Compute calibration by binning stated confidence against observed accuracy, deriving confidence from candidate frequencies, verifier scores, or a separately evaluated confidence estimator rather than from the model's prose.
- Report agreement statistics as diagnostics: equivalence class entropy, the share of runs reaching the agreement threshold, accuracy conditional on agreement, and the count of high-agreement wrong answers, which is the statistic that falsifies agreement as a correctness proxy.

**Required Outputs**:

- A stratified quality report with verified accuracy per stratum.
- An efficiency report with cost per successful outcome and cost per accuracy point over baseline.
- A calibration report with the confidence source named and the observed gap per segment.

**Quality Checkpoints**:

- No accuracy figure is reported without its stratification; a pooled figure across model revisions or prompt versions is void.
- Sampled-technique comparisons hold the candidate budget fixed; comparing results generated under different budgets as though they measured equal cost is a measurement defect.
- Confidence is never derived solely from model prose; a prose-derived confidence is excluded from the calibration report.

***

#### Step 7.2: Run Faithfulness Interventions and Robustness Trials

**Required Actions**:

- Run faithfulness interventions offline on a held-out set of at least 50 examples per release: insert controlled hints, truncate the chain at varying depths, corrupt or paraphrase steps, reorder independent steps, and substitute one chain for another while holding the question fixed.
- Measure how often the answer changes under each intervention and how often the trace acknowledges an influence that demonstrably changed the answer, recording both as reported rates rather than as pass or fail verdicts.
- Treat a low acknowledgment rate as the expected condition rather than as an anomaly, since the originating source reports acknowledgment rates of 25 percent and 39 percent across hint types for two tested models and below 2 percent in most reward-hacking scenarios studied.
- Run robustness trials across a preregistered set of at least 5 seeds and 5 perturbation classes: irrelevant text, reordered options, paraphrases, missing evidence, and injected adversarial instructions, reporting mean, standard deviation, worst-seed score, best-minus-worst range, and flip rate.
- Report paired evaluations on identical examples for any configuration change, with win, loss, and tie counts, bootstrap intervals, and per-slice regression, since a mean improvement can conceal a protected-slice regression.

**Required Outputs**:

- A faithfulness report with per-intervention answer-change rates and acknowledgment rates.
- A robustness report with per-seed and per-perturbation results, including flip rate and clean-to-perturbed degradation.
- A paired evaluation record for every configuration change proposed for promotion.

**Quality Checkpoints**:

- Faithfulness results are reported as measurements and are never used to certify a chain as trustworthy; no acknowledgment rate authorises trusting a trace as evidence.
- Robustness is reported across all 5 perturbation classes and at least 5 seeds; a clean-condition-only result blocks promotion.
- Clean-to-perturbed degradation above 20 percentage points blocks promotion regardless of clean-condition performance.

***

#### Step 7.3: Correct the Policy and Promote, Demote, or Retire the Configuration

**Required Actions**:

- Compare the measured outcome against the failure hypothesis recorded in Step 2.1, and record the hypothesis as confirmed, disconfirmed, or unresolved.
- Correct the warrant gate where suppression records show tasks that would have benefited, or where warranted runs show no gain over baseline: move the affected condition, do not add a case-specific exception.
- Correct the effort budget from measured effort distributions per task class rather than from a single expensive run, and version every threshold change.
- Promote a configuration only where its verified accuracy gain over baseline has a 95 percent interval lower bound above 0, its cost per successful outcome is within the declared envelope, its p95 latency is within the contract limit, and no protected slice regresses materially.
- Demote or retire a configuration whose incremental verified quality is smaller than its latency, cost, or safety penalty, and record the retirement reason code so the ladder rung is not reselected for the same signature.

**Required Outputs**:

- A hypothesis adjudication record per configuration.
- A versioned policy revision naming every gate condition, ladder mapping, and threshold changed.
- A promotion, demotion, or retirement decision with the measurements that justified it.

**Quality Checkpoints**:

- No policy change derives from a single run; promotion requires the immutable evaluation set and the declared interval condition.
- Every threshold in the deployed configuration carries a recorded provenance: measured from a named dataset, or marked as a deployment default awaiting measurement.
- A retired configuration is recorded with its reason code, so the same rung is not reselected for the same failure signature without new evidence.

***

## III. Implementation Guidance for AI Agents

AI agents operating a reasoning configuration must follow systematic protocols ensuring that reasoning effort is warranted, bounded, externally verified, and disclosed within policy. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Warrant Agent**: Evaluates the warrant gate and returns use, suppress, or route to a deterministic function, with a reason code. It owns the gate cost estimate and may refuse a reasoning configuration outright. It never generates a chain.
2. **Contract Agent**: Owns the decision contract, the budget ledger, and the effort budget. It alone may amend a bound, and every amendment is a versioned policy revision rather than an in-flight decision.
3. **Reasoning Executor**: Runs the configured model call for exactly one bounded tranche, producing chains and candidate answers. It may not change technique, extend a bound, authorise an action, or write to the audit record.
4. **Extraction Service**: Parses chains into typed candidate answers, normalises values, computes answer hashes, groups candidates into equivalence classes, and reports the winning share as a diagnostic. It is deterministic software and never a model call where the schema is expressible.
5. **Verification Agent**: Assembles the check set by claim class, executes checks in a sandboxed runtime or against retrieval, labels every signal with a source class, applies deterministic precedence on disagreement, and issues the authorisation artifact or withholds it.
6. **Instrumentation Agent**: Writes the append-only trace, enforces the disclosure boundary at write time, computes the metric set, and may veto release where a boundary breach is detected.

**Reasoning Disclosure Boundary**: The instrumentation protocol permits decision metadata and prohibits hidden reasoning content. This is a hard constraint binding every component.

- Log gate verdicts, reason codes, evidence references, verification verdicts with source classes, bound consumption, cost figures, and exit conditions.
- Do not require, request, or persist private chain-of-thought from any model or component; the verification path requires typed answers, evidence, and observable check results, not internal transcripts.
- Preserve provider-required reasoning blocks across tool calls only where the interface mandates it, and do not expose, index, or forward them to any downstream tool, retrieval corpus, or trace viewer.
- Do not store raw prompts, outputs, or payloads where a content hash and an access-controlled reference suffice; maintain any human-readable preview in redacted form only.
- Where a component cannot justify a decision without exposing hidden reasoning, record the decision as unjustified and escalate rather than relaxing the boundary.

**Workflow Execution Pattern**:

```
STATE: Verification_And_Authorisation
INPUTS:
  1. Candidate equivalence class inventory from Step 4.2
  2. Claim inventory with assigned checks from Step 5.1
  3. Effort consumption record from Step 4.1
ACTIONS:
  1. Execute every assigned check and record verdict with source class
  2. Apply deterministic precedence to every recorded disagreement
  3. Compute the independence verdict for every observed agreement
  4. Issue or withhold the authorisation artifact for each pending action
VALIDATION:
  - critical_claims_with_external_check == critical_claims_total
  - deterministic_verdict_prevailed_on_disagreement == TRUE
  - chain_cited_as_authorisation_artifact == FALSE
  - reasoning_trace_persisted == FALSE
  - all_bound_dimensions_within_ceiling == TRUE
TRANSITIONS:
  IF all_checks_pass THEN next_state = Disclosure_Bounded_Release
  IF failure_class == LOCAL_DEFECT AND revision_cycles_used < cap
     THEN next_state = Bounded_Revision
  IF failure_class == COVERAGE_GAP AND retrieval_budget_remaining > 0
     THEN next_state = Context_Construction
  IF failure_class == SAFETY_VIOLATION THEN next_state = Halt_And_Report
  IF validation_failed THEN next_state = Verification_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended authorisation with its citing artifact and source class without executing the action; confirm it against the validation block while no side effect is committed; commit it only after validation passes, recording the authorisation event in the same operation.

**Approval Gate**: Human authorisation is required before any action that is irreversible, before release of any answer in the highest risk tier whose critical claims lack an external check of a source class outside the generating model, before promotion of any configuration whose advantage appears only under clean conditions, and before any tranche projected to consume more than 40 percent of the remaining budget ledger. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the decision contract, budget ledger, and consumption record in durable state, since a run may outlive a single context window.
- Summarise superseded chains into evidence references and typed answers once verification completes, retaining the references and discarding the prose.
- Never feed a raw chain into an untrusted tool, a retrieval index, or a shared memory store; a chain re-entering a prompt is untrusted content and carries the same labelling requirement as retrieved text.
- Write a handoff record naming contract, selected rung, consumed budget, open claims, and next action at every context boundary.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract and Warrant Integrity (After Phase 1)**

- **Automated Check**: Every acceptance test is machine-evaluable or assigned to a named role; every budget dimension carries a numeric limit; the baseline ran on at least 30 examples of the immutable set; exactly 1 gate verdict is recorded with a reason code.
- **Agent Action on Pass**: Proceed to technique selection.
- **Agent Action on Failure**: Halt and return the contract or gate defect; no reasoning effort is spent against an incomplete contract.
- **Human Review Trigger**: A task in the highest risk tier, or a warrant verdict contradicting a suppression condition.

**Checkpoint 2: Selection Justification (After Phase 2)**

- **Automated Check**: Exactly 1 primary technique selected; the selection traces to a failure signature holding at least 40 percent of observed failures; a falsifiable hypothesis is recorded; every loop carries a numeric cap.
- **Agent Action on Pass**: Proceed to configuration.
- **Agent Action on Failure**: Return to failure classification; a selection without a signature is not executed.
- **Human Review Trigger**: A mixed failure distribution with no signature above 40 percent, or a request to combine 2 or more techniques in one configuration.

**Checkpoint 3: Configuration Validity (After Phase 3)**

- **Automated Check**: Model class determined from a served checkpoint identifier; every consumed dimension carries a ceiling and a declared breach behaviour; every evidence item carries provenance; every untrusted block is labelled.
- **Agent Action on Pass**: Proceed to bounded generation.
- **Agent Action on Failure**: Halt; an unbounded dimension or an unlabelled untrusted block is never dispatched.
- **Human Review Trigger**: An explicit reasoning instruction proposed for a reasoning model without a paired-evaluation authorisation.

**Checkpoint 4: Generation and Extraction Integrity (After Phase 4)**

- **Automated Check**: No dimension exceeded its ceiling; extraction was performed deterministically; every candidate carries an identifier and a parent reference; the reasoning-token share is below 60 percent or an anomaly is recorded.
- **Agent Action on Pass**: Proceed to verification.
- **Agent Action on Failure**: Truncate, mark the run bound-limited, and route to verification; never extend a ceiling to recover a tranche.
- **Human Review Trigger**: More than 20 percent of chains yielding no parseable candidate, or an overthinking anomaly on more than 10 percent of runs in a task class.

**Checkpoint 5: Verification Sufficiency (After Phase 5)**

- **Automated Check**: 100 percent of critical claims carry at least 1 external check whose source class lies outside the generating model; every agreement used as confirmation carries an independence assessment; every authorised action cites an authorisation artifact.
- **Agent Action on Pass**: Proceed to release.
- **Agent Action on Failure**: Withhold the answer or carry the affected claims with unsupported markers; a chain is never accepted in place of a missing check.
- **Human Review Trigger**: No external check obtainable for a critical claim in a run whose pending action is irreversible.

**Checkpoint 6: Disclosure and Instrumentation Integrity (After Phase 6)**

- **Automated Check**: 0 reasoning traces persisted outside explicit policy permission; 0 credentials or unredacted personal data in the response or log; every citation resolves; every score carries the identity and version of its producer.
- **Agent Action on Pass**: Release the response and close the trace.
- **Agent Action on Failure**: Halt release, purge the offending records, and re-instrument before any further run in that configuration.
- **Human Review Trigger**: Any disclosure breach, without exception.

**Checkpoint 7: Measurement and Promotion Integrity (After Phase 7)**

- **Automated Check**: Accuracy reported per stratum; robustness reported across at least 5 seeds and all 5 perturbation classes; the promotion interval condition evaluated; every deployed threshold carries a recorded provenance.
- **Agent Action on Pass**: Release the metric report and permit the promotion decision.
- **Agent Action on Failure**: Withhold promotion and name the missing evidence; a configuration is never promoted on clean-condition results alone.
- **Human Review Trigger**: A clean-to-perturbed degradation above 20 percentage points, or a protected-slice regression of any magnitude.

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

**Error Type 1: Fluent Chain With a Failing Answer**

- **Symptoms**: A well-formed chain passes internal review while an external check fails; reviewers rate the run highly on presentation and low on correctness; the failure concentrates on claims no deterministic check covered.
- **Diagnostic Steps**: Locate the first step whose output an external check contradicts; determine whether the defect is a fabricated intermediate fact, an invalid deduction over correct premises, an arithmetic or unit slip, or an early error propagated downstream.
- **Resolution Protocol**: Option A, move the failing claim class to a rung with an executable oracle, replacing narrated computation with executed computation. Option B, insert a deterministic check at the step where the defect first appears rather than only at the final answer. Option C, split the task so the fabrication-prone segment is answered from retrieval rather than from generation. Option D, return the baseline answer with an explicit limitation statement.
- **Escalation Trigger**: A third occurrence of the same defect location in one task class escalates for policy revision; the class is never resolved by requesting a longer or more careful chain.

**Error Type 2: Critical Claim With No Admissible Check**

- **Symptoms**: A claim the contract designates critical has no deterministic function, retrievable source, tool postcondition, or human reviewer available; the verification record shows the claim resting on the chain alone.
- **Diagnostic Steps**: Confirm the claim is genuinely critical under the contract; determine whether the gap is missing evidence, an unavailable tool, an unexpressible schema, or an inherently subjective judgement.
- **Resolution Protocol**: Option A, return to retrieval and acquire an admissible source within the remaining budget. Option B, restate the claim at a coarser granularity that an available check does cover. Option C, carry the claim with an unsupported marker and withhold any action it would have authorised. Option D, escalate to a named human reviewer where the contract permits human adjudication.
- **Escalation Trigger**: A critical claim with no admissible check blocks release immediately where an irreversible action is pending; this class is never resolved by additional generation.

**Error Type 3: Correlated Agreement Mistaken for Confirmation**

- **Symptoms**: Candidates agree unanimously while sharing a generator, prompt, or premise; agreement is high and accuracy conditional on agreement is low; independent-model signals resolve to one base model or one retrieved document.
- **Diagnostic Steps**: Trace every agreeing signal to its generator, prompt version, premise set, and evidence identifier; determine whether agreement survives removal of the shared premise or the shared source.
- **Resolution Protocol**: Option A, commission a deliberately different method such as executed computation, formal checking, or simulation. Option B, retrieve a primary source in place of a model recollection. Option C, increase candidate diversity through a different prompt formulation and re-measure, accepting the result only where the shared origin is broken. Option D, carry the conclusion with an unsupported marker.
- **Escalation Trigger**: A high-risk conclusion resting on agreement that fails the independence test escalates immediately; this class is never resolved by sampling more candidates from the same configuration.

**Error Type 4: Effort Overrun and Overthinking**

- **Symptoms**: Reasoning-token share above 60 percent on a class whose median is below 30 percent; answer oscillation across checkpoints without new external signals; consumed effort above 3 times the class median; latency breaching the contract limit on easy inputs.
- **Diagnostic Steps**: Compare consumption per dimension against the planned profile; determine whether the overrun sits in the reasoning budget, in candidate fan-out, in search expansion, or in tool retries; check whether the input pattern indicates an induced-slowdown attempt.
- **Resolution Protocol**: Option A, truncate at the bound, extract, and route to verification as a bound-limited run. Option B, drop to a lower ladder rung whose bound the class fits. Option C, route the input class to the direct-solve path with a declared fallback. Option D, tighten the class ceiling by policy revision after measuring the class effort distribution.
- **Escalation Trigger**: Effort anomalies on more than 10 percent of runs in a task class escalate for policy review; the class is never resolved by raising a ceiling in flight.

**Error Type 5: Injected Instruction Entering Through the Reasoning Path**

- **Symptoms**: A chain adopts an objective the contract did not state; a tool call is proposed with arguments traceable to retrieved text; a candidate chain re-entering a prompt carries directive language; an observation is treated as higher-priority than the contract.
- **Diagnostic Steps**: Trace the injected directive to its entry point among user text, retrieved documents, tool observations, stored memories, and re-entered chains; confirm whether the trust boundary marker was present and whether the content was labelled as data.
- **Resolution Protocol**: Option A, restore the trust boundary, relabel the content as data, and re-run the tranche with the injected block isolated. Option B, remove the entry point from the evidence set and re-retrieve under a stricter filter. Option C, constrain the tool surface so the proposed action is not invocable from the affected path. Option D, halt and report where the injection reached an action proposal in a run with authorised side effects.
- **Escalation Trigger**: Any injection that reaches an action proposal escalates immediately and suspends the affected retrieval source or tool binding until the entry point is closed; injection is never resolved by instructing the model to ignore the content.

**Error Type 6: Chain Treated as Evidence or as Authorisation**

- **Symptoms**: A response presents the chain as a justification for its answer; an action record cites a chain rather than an authorisation artifact; a log contains a persisted reasoning trace; a downstream component consumes a trace as a trusted input.
- **Diagnostic Steps**: Inspect the authorisation record for each executed action and identify the cited artifact and its source class; scan the trace store for persisted reasoning content; identify which component consumed the chain and under what label.
- **Resolution Protocol**: Option A, withdraw the authorisation, re-run verification against an admissible artifact, and re-issue or withhold the action. Option B, purge the persisted trace, re-instrument the write path with allowlist capture, and re-run the disclosure scan. Option C, replace the justification in the response with the verification summary. Option D, sever the downstream consumption path and label the chain as untrusted content wherever it must be retained.
- **Escalation Trigger**: Any occurrence blocks release and suspends the configuration until re-instrumentation passes; this class is never resolved by retry and never accepted with a recorded warning.

**Troubleshooting Decision Tree**:

```
VERIFICATION OR RELEASE DETECTS A PROBLEM
├─ CORRECTNESS DEFECT
│   ├─ External check contradicts a step → Move claim class to an executable oracle
│   ├─ Defect repeats at one step location → Escalate for policy revision
│   └─ No parseable candidate from the chain → Retry to the cap, then fall back to baseline
├─ EVIDENCE DEFECT
│   ├─ Critical claim has no admissible check → Retrieve, coarsen, or mark unsupported
│   ├─ Unsupported claim with irreversible action pending → HALT; escalate to human review
│   └─ Agreement shares a generator or premise → Record correlated failure; commission a different method
├─ EFFORT DEFECT
│   ├─ Ceiling reached → Truncate, extract, mark bound-limited, verify
│   ├─ Reasoning-token share above class threshold → Drop a rung or route to direct solve
│   └─ Answer oscillates without new signal → Stop generation; verify the current candidate
├─ TRUST DEFECT
│   ├─ Directive found in labelled data → Restore boundary; re-run tranche isolated
│   └─ Injection reached an action proposal → HALT; suspend the source or tool binding
└─ DISCLOSURE DEFECT
    ├─ Reasoning trace found in log → HALT release; purge and re-instrument
    ├─ Chain cited as authorisation → Withdraw authorisation; re-verify against an artifact
    └─ Sensitive payload retained → Replace with content hash and access-controlled reference
```

### D. Performance Metrics and Continuous Learning

**Quality Metrics**:

- **Verified accuracy over baseline**: Percentage-point gain in externally verified accuracy against the direct baseline on the immutable set (target: at least 5 points, with the 95 percent interval lower bound above 0; below this the configuration is not promoted).
- **Critical claim coverage**: Critical claims carrying at least 1 external check (target: 100 percent; any shortfall blocks release).
- **Unsupported claim rate**: Released claims carrying an unsupported marker (target: no more than 10 percent; a higher rate indicates the evidence standard, not the reasoning, is the binding constraint).
- **Accuracy conditional on agreement**: Verified accuracy among runs meeting the agreement threshold (target: at least 15 points above accuracy among runs below it; a smaller gap means agreement carries no signal for the class).
- **High-agreement wrong-answer rate**: Runs where agreement exceeded the threshold and verification failed (target: no more than 5 percent; this is the statistic that falsifies agreement as a correctness proxy).

**Efficiency Metrics**:

- **Cost per successful outcome**: Total cost over externally verified successes (target: within 100 percent of the direct baseline at matched verified accuracy).
- **Cost per accuracy point gained**: Incremental cost divided by percentage points gained over baseline (target: declared per task class and enforced as a promotion condition).
- **Reasoning-token share**: Reasoning tokens over total output tokens (target: below 60 percent; above it an overthinking anomaly is raised).
- **Wasted effort**: Tokens consumed by pruned, cancelled, or unparseable candidates over total tokens (target: no more than 20 percent).
- **Bound-limited run rate**: Runs terminating on a ceiling rather than on a stopping condition (target: no more than 15 percent; a higher rate means the ceiling or the rung is mismatched to the class).

**Robustness and Calibration Metrics**:

- **Flip rate**: Example pairs whose pass or fail result changes across the preregistered seed set (target: no more than 10 percent).
- **Clean-to-perturbed degradation**: Verified accuracy difference between clean and perturbed conditions across all 5 perturbation classes (target: no more than 20 percentage points; a larger gap blocks promotion).
- **Calibration gap**: Stated minus observed success frequency per segment, with the confidence source named (target: no more than 10 percentage points per segment).
- **Answer-change rate under intervention**: Answers changing when a chain is truncated, corrupted, or replaced (recorded as a measurement; a low rate indicates the chain contributed little to the answer and the configuration should drop a rung).

**Learning and Adaptation Mechanisms**:

- **Signature-keyed correction**: Record every failure with its signature, selected rung, and outcome, and correct the ladder mapping for the signature rather than adding a case-specific exception.
- **Threshold recalibration**: Recompute every threshold per task class against observed effort and outcome distributions; the values stated here are deployment defaults, not constants.
- **Configuration versioning**: Version every prompt, exemplar set, rubric, tool schema, and bound, and evaluate any revision on held-out or future examples so the evaluation is not contaminated by the history that produced it.
- **Contamination control**: Separate public benchmark sets, private held-out sets, adversarial sets, and recent production samples, and never place hidden labels in model context.

**Human-in-the-Loop Boundaries**: Amendment of a hard constraint, authorisation of an irreversible action lacking an external check, relaxation of the disclosure boundary, and promotion of a configuration whose advantage appears only under clean conditions are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs whether and how intermediate reasoning is used, not what any particular reasoning is about. Its phases hold wherever a task admits a direct baseline, produces a normalisable answer, and permits at least 1 check computed outside the chain.

### 4.1 Cross-Domain Application Patterns

**Quantitative research and data analysis**: The warrant gate returns use because derivations chain several dependent transformations and competing analytical paths exist. The ladder selects program-aided reasoning, since execution is a stronger oracle than narrated arithmetic. Verification executes the derivation, checks units and dimensional consistency, and reproduces summary statistics from the source data rather than from the chain. The unsupported marker attaches to any interpretive claim no computation covers. Promotion requires the gain to survive re-running the analysis across the preregistered seed set, because a result that flips across seeds is a sampling artifact rather than a finding.

**Software engineering and defect diagnosis**: Failures concentrate in the missing-dependency and unsupported-claim signatures, so the ladder selects decomposition first and tool-interleaved reasoning where the diagnosis requires reading code, running tests, or querying logs. Verification is the test suite, the type checker, and the schema validator, all of which return verdicts independent of the chain. An action with a side effect, such as applying a change or restarting a service, proceeds only against a passing check, never against a convincing explanation of why the change is correct. Sandbox constraints bind every executed candidate.

**Regulated compliance determination**: Risk is high and most determinations are effectively irreversible once communicated, so the evidence standard tightens and the approval gate binds before release. The ladder favours decomposition and verification-question drafting over search, because an auditable path from provision to conclusion matters more than exploring alternatives. Every element of the determination cites a retrieved provision by identifier and version. The event log becomes a deliverable rather than a diagnostic aid, and the disclosure boundary is enforced as a records-management obligation, since a retained reasoning trace would enter the evidentiary record as though it recorded the determination's basis.

**Clinical and other safety-critical decision support**: The gate returns use for differential reasoning and returns suppress for lookups of dosage tables, code sets, and eligibility rules, which route to deterministic functions. No recommendation is released whose critical claims lack a source of admissible class, and the system abstains in preference to completing an unverified recommendation. The persuasion hazard is at its most acute here: a fluent chain raises reviewer confidence without raising correctness, so the interface presents the verification summary and the unsupported markers rather than the reasoning.

**Industrial operations and scheduling**: The environment supplies frequent external signals, so bounds are short and verification is cheap. Reversibility varies within one run, since a provisional allocation is reversible while a dispatched movement is not, and the authorisation rule binds per action class rather than per run. Diminishing returns dominate the stopping decision, because a marginally better schedule produced after the dispatch window has closed is worth less than an adequate one produced inside it. Search rungs are used sparingly and always under a node budget, since the state space is large enough to absorb any budget offered.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk reversible work**: Collapse the framework to the gate, one bounded generation tranche, deterministic extraction, and schema validation. Reasoning overhead above 25 percent of direct-execution cost indicates the gate should have suppressed the run.
- **High-risk or irreversible work**: Retain every phase, require at least 1 external check of a source class outside the generating model for 100 percent of critical claims, bind the approval gate before every irreversible action, and prefer abstention over unverified completion.
- **Strict latency budgets**: Reduce bounds rather than removing verification, since removing verification removes the only thing that makes the answer acceptable. Where latency forbids any external check, the gate suppresses the reasoning configuration and the baseline runs with a declared fallback.
- **High-volume low-value work**: Suppress by default and sample. Enable reasoning on a measured subset, compare against the baseline on the immutable set, and promote only where the interval condition holds; a per-request reasoning decision at this volume costs more in gate evaluation than it returns.
- **Long-horizon autonomous runs**: Persist contract, consumed budget, and open claims outside working context, write a handoff record at every context boundary, and re-run the critical-claim coverage check at each handoff so an unsupported claim is not inherited as though it had been verified.
- **Multi-agent deployments**: Assign extraction, verification, and instrumentation to components distinct from the generator, and treat agreement among components sharing a base model as correlated until an independence assessment says otherwise. A reviewing agent is never granted broader tool privileges than the acting agent.

***

## V. Limitations and Considerations

**A trace remains unusable as evidence even under this framework**: Nothing in these phases makes a chain into a record of the computation that produced an answer, and the faithfulness interventions in Step 7.2 measure only how sensitive an answer is to its stated reasoning. The consequence is that a deployment can satisfy every checkpoint here and still be unable to explain why an answer was produced. The mitigation is to treat the verification record, not the chain, as the explanation artifact, and to release only the verification summary and the evidence identifiers to any consumer who might otherwise read a chain as a justification.

**Numeric thresholds are deployment defaults, not measured findings**: The chain-step ceiling of 12, the candidate progression of 3 to 9, the search bounds of breadth 3 and depth 5 within 40 nodes, the 8-action budget, the 3-cycle revision cap, the 60 percent reasoning-token share alert, the 5-point promotion gain, and the 30-example minimum evaluation set were chosen to be operable on first deployment. Presenting them as evidence would misstate their status. The mitigation is the recalibration requirement in Step 7.3, obliging each deployment to recompute every threshold per task class against observed distributions and to record each threshold's provenance as measured or default.

**Claims carried from the source were not independently re-verified**: This conversion was performed without a research pass, so every empirical claim reproduced here is attributed to the originating prose source rather than asserted. This applies specifically to the reported hint acknowledgment rates of 25 percent and 39 percent across hint types and below 2 percent in most reward-hacking scenarios, to the reported existence of demonstrated slowdown attacks against reasoning models, to the reported guidance that explicit step-by-step instructions may not help and can hinder performance on certain reasoning models, and to the reported task-dependent diminishing returns from larger thinking budgets. The consequence is that a deployment reading these as measurements of its own models would be misled. The mitigation is to treat each as a hypothesis to re-measure locally under Step 7.2 before any policy depends on it.

**Some critical claims admit no external check**: Subjective judgements, forecasts, and novel syntheses often have no deterministic oracle, no retrievable source, and no tool postcondition. The consequence is that the framework's central requirement cannot be satisfied for them, and a rubric score from a model is not a substitute, since it shares the blind spots of the generator. The mitigation is Error Type 2: coarsen the claim until an available check covers it, carry it with an unsupported marker, withhold any action it would authorise, or route it to a named human reviewer.

**Verification can cost more than the reasoning it validates**: Executing checks, opening citations, and running blinded rubric scoring consume tokens, tool calls, and latency, and on cheap tasks the verification path can dominate total cost. The consequence is that a deployment under cost pressure will be tempted to accept chains unverified. The mitigation is the warrant gate itself: a task whose verification cost is unaffordable is a task that should have been suppressed and routed to a deterministic function or to the baseline, not a task that should proceed unverified.

**Suppression can withhold reasoning that would have helped**: The gate decides on observable conditions and on a baseline measured before the task arrives, so it will suppress some tasks that intermediate reasoning would have improved. The consequence is a quiet loss of quality that no per-run signal reveals. The mitigation is the suppression record required in Step 1.3 and the gate correction in Step 7.3: suppressed tasks are sampled, run under a reasoning configuration offline, and compared, so the gate condition is moved on evidence rather than on complaint.

**Reproducibility is bounded by the provider**: Pinning model identifiers, prompt versions, parameters, and seeds does not guarantee identical outputs on hosted inference, and a family label such as a model series name does not fix behaviour across served checkpoints, quantisations, and system prompts. The consequence is that a measured gain may not persist across an unannounced provider change. The mitigation is to record the returned model identifier, response identifier, and semantic-convention version on every call, to evaluate the exact served checkpoint rather than the family, and to treat any change in the returned identifier as a trigger for re-measurement.

**Agreement statistics can mislead in both directions**: A low winning share can reflect formatting variance rather than genuine disagreement, and a high winning share can reflect a shared misconception. The consequence is that agreement used as a decision variable will sometimes reject correct answers and sometimes accept wrong ones. The mitigation is normalisation before class assignment in Step 4.2, the independence assessment in Step 5.2, and the high-agreement wrong-answer metric in Section III.D, which makes the failure mode visible rather than assumed away.

**Structural conformance is not sound reasoning**: A run can pass every checkpoint here against a poorly chosen objective, an inadequate evidence standard, or an acceptance test that does not test what matters. The framework detects unwarranted, unbounded, and unverified reasoning; it does not detect a misdirected purpose. The mitigation is the human review triggers in Section III.B and the explicit statement here that no checkpoint substitutes for review of the contract itself.

***

## VI. Conclusion and Summary

Chain-of-thought reasoning is a routing and verification discipline before it is a prompting technique. Its value comes from a small number of explicit decisions recorded per run: whether intermediate reasoning is warranted at all, which rung of the ladder the observed failure indicates, what effort that rung may consume, what external check its conclusion must pass, and what artifact authorises any action the conclusion implies. A deployment making those decisions explicitly can measure and correct them; a deployment that instructs a model to think step by step and accepts what returns has no mechanism to discover that the instruction cost tokens and bought nothing.

The single discipline that governs every other part of this guide is that a reasoning trace is not evidence. A chain can be fluent, internally consistent, and wrong, and its fluency raises rather than lowers the cost of the error, because it persuades reviewers and downstream components that were not persuaded by the bare answer. Internal consistency establishes nothing about the world, agreement among candidates from one generator establishes nothing about independence, and the absence of suspicious text in a monitored trace establishes nothing about the computation behind it. Conclusions are accepted against deterministic checks, executed programs, retrieved sources, and tool postconditions, and actions proceed against those artifacts alone.

A team adopting this framework should instrument the baseline before configuring any reasoning. Measure the direct baseline on an immutable set, classify its failures into signatures, and enable exactly 1 ladder rung against the dominant signature under declared bounds. Verify externally, log decision metadata within the disclosure boundary, and compare on the same set. Only then consider a second rung, and retire any configuration whose verified gain is smaller than its latency, cost, or safety penalty.

**Key Success Factors**:

- **Warrant before technique**: Intermediate reasoning is enabled only against a measured baseline failure it might repair, and suppressed wherever a deterministic function or a direct answer suffices.
- **The smallest adequate rung**: Selection targets the observed failure signature rather than task difficulty as impression, and rungs are not combined until measurement shows an unrepaired residual.
- **Bounds enforced in software**: Every dimension the technique consumes carries a numeric ceiling enforced by cancellation and deadline, never by an instruction in a prompt, and a breach terminates in truncation, fallback, or abstention.
- **External verification without exception**: Every critical claim carries at least 1 check whose source class lies outside the generating model, prompt, and evidence set, and the deterministic verdict prevails on every disagreement.
- **The chain authorises nothing**: Actions proceed against a passing check, an executed postcondition, a retrieved source, or a recorded human approval, and a chain is never cited in their place.
- **Disclosure-bounded instrumentation**: Decision metadata is logged in full and reasoning content is not persisted, so the run is auditable without the trace becoming a justification artifact or a disclosure liability.

By following this guide, AI agents can spend reasoning effort only where a measured failure justifies it, bound that effort to limits that hold under adversarial and degenerate inputs, and release conclusions that rest on evidence a reviewer can re-check rather than on a chain that merely reads as though it had been checked.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular rungs and steps. The external references that follow are transcribed from the originating prose guide as it cited them, using the labels and locations that source carried; they were not independently re-verified during this conversion, and no additional research pass was performed. Where an entry appears as a bare label rather than a full title, that is the form the source used and it is reproduced rather than expanded.

**Corpus pointers**:

- `Production Guide to Chain-of-Thought Reasoning` — the originating prose guide from which this operational guide was derived. Source of the warrant, evidence, and safety gating structure, the technique inventory that became the selection ladder, the reasoning-model prompting distinction, the nine-step production workflow with entry and exit criteria, the metadata field inventory, the metric definitions, the faithfulness and monitorability material, and the deployment acceptance conditions. Its external citations are transcribed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — the adjacent control discipline. It owns the in-flight monitor and control loop that decides at each checkpoint whether to continue, verify, repair, switch, branch, escalate, or stop. This guide adopts its terminology for the decision contract, budget ledger, source class, correlated failure, reason code, disclosure boundary, and exit condition, and defers in-flight control to it rather than restating it.
- `advanced_task_guides/reasoning/guide_LeastToMostReasoning.md` — the sibling guide owning rung 3 of the selection ladder: ordered decomposition into answerable subproblems, dependency-ordered solving, the prohibition on feeding an unverified answer forward, and bounded re-decomposition when a node fails. This guide names the rung and its subproblem bound only.
- `advanced_task_guides/reasoning/guide_SelfConsistency.md` — the sibling guide owning rung 6 of the selection ladder in full: sample diversification, answer normalisation, equivalence classes, winning share and top-two margin, independence tiers, and the abstention rule on non-resolution. This guide adopts its terminology for answer extraction, answer normalisation, equivalence class, winning share, source class, and independence assessment.
- `advanced_task_guides/reasoning/guide_TreeOfThought.md` — the sibling guide owning rung 7 of the selection ladder: explicit search over partial solutions with a generator, a deterministic transition layer, an evaluator, and a controller that expands, prunes, backtracks, and stops under a declared budget. This guide names the rung and its bounds only.
- `advanced_task_guides/reasoning/guide_GraphOfThought.md` — the sibling guide owning the graph variant of rung 7, where a partial result may have several parents so that intermediate products merge and are reused rather than only branching. It covers the typed edge vocabulary, the admitted-merge check, incremental cycle prevention, and dependency-fingerprint caching. Rung 7 names tree or graph search; the choice between them belongs to that guide and to the tree guide above.
- `advanced_task_guides/reasoning/guide_ChainOfVerification.md` — the sibling guide owning rung 8 of the selection ladder in full: the draft, plan, verify, and revise stages; the claim ledger and its atomicity rules; decontextualised verification questions answered in isolated contexts; the evidence hierarchy and conflict-resolution procedure; and the bounded revision loop with its no-improvement and anti-oscillation stops. This guide names the rung and its single-round default bound only.
- `advanced_task_guides/reasoning/guide_StepBackPrompting.md` — the sibling guide owning rung 10 of the selection ladder: deriving a strictly more general question from the original, answering it under an evidence standard that marks a recall-only general answer unsupported, and composing that answer back onto the specific case under a clause-ablation check. This guide names the rung and its single abstraction step only.
- `advanced_task_guides/reasoning/guide_MetacognitiveMonitoring.md` — the sibling guide owning the monitor layer: which properties of an in-progress run are measurable, how each is computed from an observation record rather than from introspection, and how a stated confidence is calibrated against observed outcomes before it is permitted to gate anything. The calibration measurement in Phase 6 defers to its threshold-selection and held-out-calibration procedure rather than restating it.
- `advanced_task_guides/planning/guide_PlanExecuteDecoupling.md` — companion guidance on separating plan construction from plan execution, applicable to rung 3 of the selection ladder where a plan is checked before costly actions are taken.
- `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md` — companion guidance on retrieval under agent control, applicable to the evidence precedence rule in Step 1.3 and the context construction step in Step 3.3.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design and instrumentation, applicable to the metadata record in Step 6.2.
- `advanced_task_guides/scoring/guide_complexityScoring.md` — a compact scoring rubric usable as an input to the warrant gate in Section 1.3 and to the failure classification in Step 2.1.

**External references**: The following entries are transcribed from the originating prose guide. Grouping is editorial; labels and locations are the source's.

*Foundational prompting results*

1. Wei et al. — https://arxiv.org/abs/2201.11903
2. Kojima et al. — https://arxiv.org/abs/2205.11916

*Sampling, decomposition, and search variants*

3. Wang et al., self-consistency — https://arxiv.org/abs/2203.11171
4. Zhou et al., least-to-most — https://arxiv.org/abs/2205.10625
5. Wang et al., plan-and-solve — https://arxiv.org/abs/2305.04091
6. Yao et al., tree-of-thought — https://arxiv.org/abs/2305.10601
7. Besta et al., graph-of-thought — https://arxiv.org/abs/2308.09687

*Tool use, program-aided reasoning, refinement, and verification*

8. Yao et al., ReAct — https://arxiv.org/abs/2210.03629
9. Gao et al., program-aided language models — https://arxiv.org/abs/2211.10435
10. Chen et al., Program-of-Thought — https://arxiv.org/abs/2211.12588
11. Madaan et al., Self-Refine — https://arxiv.org/abs/2303.17651
12. Shinn et al., Reflexion — https://arxiv.org/abs/2303.11366
13. Dhuliawala et al., chain-of-verification — https://aclanthology.org/2024.findings-acl.212.xml
14. Zheng et al., step-back prompting — https://arxiv.org/abs/2310.06117

*Reasoning models and provider guidance*

15. OpenAI reasoning best practices — https://developers.openai.com/api/docs/guides/reasoning-best-practices
16. DeepSeek-R1 report — https://arxiv.org/abs/2501.12948
17. Claude extended thinking documentation — https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking

*Faithfulness, monitorability, and adversarial effort*

18. *Language Models Don't Always Say What They Think* — https://arxiv.org/abs/2305.04388
19. *Measuring Faithfulness in Chain-of-Thought Reasoning* — https://arxiv.org/abs/2307.13702
20. Anthropic reasoning-faithfulness research — https://www.anthropic.com/research/reasoning-models-dont-say-think
21. *Chain-of-Thought Monitorability* — https://arxiv.org/abs/2507.11473
22. OverThink — https://arxiv.org/abs/2502.02542

*Security risks in LLM applications*

23. OWASP prompt injection guidance — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
24. OWASP sensitive information disclosure guidance — https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/

*Evaluation, scoring, and reproducibility*

25. Chen et al., HumanEval pass@k estimator — https://arxiv.org/abs/2107.03374
26. Process reward model lessons — https://arxiv.org/abs/2501.07301
27. EMNLP study of LLM judge bias — https://aclanthology.org/2024.emnlp-main.474/
28. vLLM reproducibility documentation — https://docs.vllm.ai/en/latest/usage/reproducibility/

*Tracing, observability, and instrumentation*

29. LangSmith observability documentation — https://docs.langchain.com/langsmith/observability
30. Langfuse data model — https://langfuse.com/docs/observability/data-model
31. Phoenix tracing concepts — https://arize.com/docs/phoenix/tracing/concepts-tracing/otel-openinference/signals
32. OpenTelemetry GenAI span conventions — https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/gen-ai-spans.md
33. OpenTelemetry GenAI registry — https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/registry/attributes/gen-ai.md
