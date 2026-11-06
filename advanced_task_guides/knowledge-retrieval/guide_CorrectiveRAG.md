# Corrective Retrieval-Augmented Generation

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Corrective retrieval-augmented generation constitutes the task family of inserting an explicit evaluation step between retrieval and generation, so that retrieved evidence is graded before a generator receives it and the grade, rather than the retrieval score, selects what happens next. This guide provides AI agents with a structured protocol for operating a closed verdict vocabulary of three values, correct, incorrect, and ambiguous, each bound to exactly one corrective action: proceed with the retrieved set, discard it and fall back to an alternative source, or blend, decomposing the retrieved set to keep supported fragments and supplementing the remainder. It specifies a calibration discipline that qualifies the evaluator against precision, recall, and calibration-error gates on a labelled set before the evaluator is permitted to gate anything; a numeric threshold pair separating the verdicts, fitted by expected decision loss rather than assumed; a trust class carried with every piece of evidence so that fallback content is marked in the answer's provenance and barred from durable promotion without review; a bounded correction loop whose exhaustion produces an abstention rather than an answer built from content the evaluator already rejected; and an evaluation harness measuring evaluator, corrector, and answer separately. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures to ensure that correction improves evidence rather than merely consuming budget.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Corrective retrieval-augmented generation**: A retrieval architecture that places a grading step between retrieval and generation, scores the retrieved set against the query, maps the score pattern to one verdict from a closed vocabulary, and lets the verdict select a corrective action. The generator is unchanged; the correction operates entirely on the evidence bundle [1].

**Retrieval evaluator**: The scoring component that consumes a query and one retrieved passage and emits a relevance-and-support score on a declared scale. It is a versioned endpoint, not a free-form reasoning step, and it is itself a fallible judge subject to the qualification gates in Phase 2.

**Relevance score**: A per-passage numeric output of the evaluator, calibrated to the interval from 0 to 1 where the value is interpretable as the probability that the passage supports at least one required element of the answer. Raw evaluator outputs on other scales must pass through a calibration transform before any threshold is applied.

**Verdict**: One value drawn from the closed vocabulary {correct, incorrect, ambiguous}, produced by applying the threshold pair to the aggregated passage scores. A verdict is a categorical routing token, not a confidence figure.

**Verdict vocabulary**: The closed three-value set defined in Section 1.2. No fourth value may be introduced at runtime, and no verdict may be emitted outside the set; an out-of-vocabulary value is a fault, not a degraded verdict.

**Threshold pair**: The two numbers, an upper threshold and a lower threshold, that partition the calibrated score range into the three verdict bands. The pair carries a minimum separation so that the ambiguous band cannot collapse to zero width.

**Corrective action**: The single operation the router executes on a verdict: proceed, fall back, or blend. Exactly one primary corrective action executes per attempt, so its effect on evidence is attributable.

**Knowledge strip**: A provenance-bearing fragment of a retrieved document, bounded by a structural boundary such as a sentence, paragraph, heading, list item, or table row, carrying a stable identifier and exact source offsets.

**Decomposition**: Segmentation of a retrieved document into knowledge strips followed by per-strip scoring, so that a partially useful document contributes only its supported fragments.

**Recomposition**: Reassembly of retained strips in source order within each document and in authority-aware order across documents, preserving separators and source identifiers so every claim maps back to an exact span.

**Trust class**: An ordinal label recorded with every piece of retrieved content naming the class of source it came from, ranging from a system of record to sanitised open-web content. The trust class travels with the content into provenance and into the answer's citations.

**Fallback source**: Any evidence route invoked after the primary curated corpus fails, including a faithful query rewrite against the same index, an approved secondary corpus, a structured tool lookup, or an open web search. Fallback routes differ in trust class, and the cheapest safe route is preferred over the broadest one.

**Admissibility**: The deterministic verdict on whether authorisation, authority, freshness, and integrity permit a passage to be used at all. Admissibility is evaluated before relevance and can override a model-derived verdict downward but never upward.

**Evidence sufficiency**: The deterministic verdict on whether the retained evidence set covers every required subquestion of the query. Passage relevance does not imply sufficiency, and a set of individually relevant strips may still fail this gate.

**Evidence gain**: The measured increment produced by one correction attempt, counted in newly covered required subquestions, newly admissible evidence identifiers, newly supported material claims, resolved contradictions, and improved freshness. Paraphrases, duplicate passages, and higher evaluator confidence over unchanged evidence count as zero.

**Correction attempt**: One bounded pass through diagnosis, action selection, acquisition, and re-evaluation. Attempts are counted by a deterministic counter that no model output and no retrieved content may modify.

**State hash**: A digest over the canonical query, subquery set, source route, filters, retrieval parameters, ordered evidence identifiers, verdict, and unresolved requirement set, used to detect repetition and oscillation.

**Abstention**: A declared terminal outcome stating what is known, what is unsupported, which routes were attempted, and what would be required to answer. Abstention is a success of the control discipline, not a failure of the task.

**Over-correction**: The condition in which a case that would have passed on the initial retrieval is made worse by a correction, measured against a frozen paired baseline.

### 1.2 The Verdict Vocabulary and Its Action Binding

The method is carried by the evaluator and by the closed vocabulary its scores resolve to. The vocabulary holds exactly three values, and each value binds to exactly one corrective action. A system that emits a fourth value, or that lets one verdict select among several actions at runtime, is no longer executing this method and loses the attributability that justifies the evaluation step.

**Entry conditions**: The verdict is computed from the aggregated per-passage scores and the threshold pair, after admissibility filtering has removed ineligible passages.

- **Correct**: At least 1 admissible passage scores at or above the upper threshold.
- **Incorrect**: Every admissible passage scores strictly below the lower threshold, or no admissible passage remains.
- **Ambiguous**: Neither of the preceding conditions holds, meaning the highest admissible score falls in the band between the two thresholds.

**Action binding**: Each verdict selects one action and no other.

- **Correct binds to proceed**: The retrieved set is decomposed into strips, filtered, recomposed with provenance, and passed to the sufficiency gate. No new acquisition occurs on this path.
- **Incorrect binds to fall back**: The retrieved set is discarded from generation context while its identifiers, scores, and failure reasons are retained in the trace, and evidence is acquired from an alternative source in a different route.
- **Ambiguous binds to blend**: The retrieved set is decomposed so that supported fragments are kept, and the unresolved remainder is supplemented from at most 1 eligible alternate route, with contradictions reconciled and route labels preserved.

**Verdict Routing Table**:

| Verdict | Entry condition on calibrated scores | Bound corrective action | Acquisition permitted |
| :-- | :-- | :-- | :-- |
| Correct | Maximum admissible score at or above the upper threshold | Proceed with the retrieved set | None |
| Incorrect | Maximum admissible score below the lower threshold | Discard and fall back to an alternative source | Exactly 1 route per attempt |
| Ambiguous | Maximum admissible score between the two thresholds | Blend retained fragments with supplementary evidence | At most 1 route per attempt |

**Default threshold pair**: On the calibrated interval from 0 to 1, the deployment defaults are an upper threshold of 0.70 and a lower threshold of 0.30, with a minimum separation of 0.20 between them and a strip retention threshold of 0.50. These are defaults for first deployment, replaced by the values that Phase 2 fits; a deployment that has not run the fit must record the defaults as unfitted and must not operate in the highest risk tier.

**Reproduction settings are not defaults**: The originating research reports upper and lower thresholds of 0.59 and -0.99 for PopQA, 0.5 and -0.91 for the health-claim and ARC-Challenge settings, and 0.95 and -0.91 for the biography setting, with 5 retained strips and a strip filter threshold of -0.5, all on an evaluator emitting scores in the interval from -1 to 1 [1]. Those values depend on that evaluator, corpus, retriever, passage length, and negative-sampling policy. They are reproduction settings and must never be copied into a deployment as operating thresholds.

**Band-width discipline**: The ambiguous band must cover between 10 percent and 35 percent of scored cases on the development split. Coverage below 10 percent indicates the band is too narrow to absorb evaluator error and forces brittle binary routing. Coverage above 35 percent indicates evaluator collapse or a miscalibrated transform, doubles acquisition cost on a third of traffic, and blocks release until the evaluator is requalified.

### 1.3 The Execution Tier Partition

Every unit of work in this method belongs to exactly one execution tier, and the assignment is what separates an auditable corrective pipeline from a model asked to grade its own inputs and act on its own grade.

**Deterministic tier**: Software, queries, schema validators, and policy engines own everything that must be exact, reproducible, and countable. This tier applies the calibration transform, applies the threshold pair, routes the verdict to its bound action, evaluates admissibility, tags trust class, counts correction attempts, computes state hashes, enforces every budget, resolves citations to exact source spans, enforces egress allowlists, and sanitises fetched content. None of this work is delegated to inference.

**Model tier**: An LLM call owns the open-vocabulary judgement no deterministic rule covers. This tier produces the raw relevance-and-support score for a query-passage pair, produces per-strip relevance judgements, proposes a failure diagnosis, proposes a faithful query rewrite or decomposition, proposes contradiction candidates between passages, and generates the final answer from the recomposed bundle.

**Hybrid tier**: The model proposes and software disposes. The evaluator proposes a score and the router disposes the verdict. The diagnoser proposes a failure class and the action selector disposes the route from the approved route manifest. The rewriter proposes a query and the constraint-preservation validator disposes whether it is issued. The generator proposes claims and the citation resolver disposes whether each claim maps to a retained span.

**Authority on disagreement**: The deterministic tier holds authority in every disagreement without exception. It may lower a verdict, never raise one: an admissibility failure demotes a model-derived correct verdict to incorrect, while no model score promotes an inadmissible passage. Where the model proposes an action the route manifest does not contain, the deterministic router rejects the proposal and selects the highest-ranked permitted route instead. Where the two tiers disagree on whether a claim is supported, the unsupported verdict stands.

**Tier Ownership of the Method's Artifacts**:

| Artifact | Owning tier | Rejection rule enforced deterministically |
| :-- | :-- | :-- |
| Raw relevance score | Model | A score outside the declared range is a fault, not a low score |
| Calibrated score | Deterministic | Uncalibrated scores never reach a threshold comparison |
| Verdict | Deterministic | Any value outside the closed vocabulary halts the run |
| Corrective action selection | Deterministic | Any route absent from the approved manifest is refused |
| Failure diagnosis | Hybrid | A diagnosis with no matching route falls back to the default route |
| Query rewrite | Hybrid | A rewrite dropping an entity, negation, date, unit, or quoted phrase is refused |
| Knowledge strip boundaries | Deterministic | Strips without exact offsets are discarded before scoring |
| Strip retention | Hybrid | Retention below the strip threshold is refused regardless of model preference |
| Trust class label | Deterministic | Content with no assignable trust class is quarantined |
| Correction attempt count | Deterministic | No model output and no retrieved content may increment or extend the counter |
| Citation to source span | Deterministic | A claim whose citation resolves to no retained span is stripped or abstained |
| Answer text | Model | Text asserting a claim with no resolved citation fails release |

**What the model tier is never permitted to decide alone**: whether a source is authorised, whether a source is authoritative, whether a budget may be extended, whether a correction attempt may be repeated, whether fallback content may be promoted into a durable store, and whether an answer may be released. Each of those decisions is deterministic or escalated.

### 1.4 Trust Classes, Invocation Conditions, and Method Boundaries

Falling back moves evidence acquisition into a different, usually lower, trust class than the curated corpus the primary retrieval served. Recording that class is therefore not bookkeeping; it is the control that stops a correction from silently degrading the evidence base it was invoked to repair.

**The trust-class ladder**: Every retrieved item carries exactly one ordinal trust class, assigned deterministically from the route that produced it, before the evaluator scores it. Content with no assignable class is quarantined rather than defaulted.

| Trust class | Source type | Sole support for a material claim | Promotion into durable memory |
| :-- | :-- | :-- | :-- |
| TC0 | Designated system of record for the fact class | Permitted in every risk tier | Permitted, recorded with version |
| TC1 | Curated, access-controlled internal corpus | Permitted below the highest risk tier | Permitted after a freshness check |
| TC2 | Approved secondary corpus or first-party external source | Permitted only with 1 corroborating TC0 or TC1 item | Requires a recorded review decision |
| TC3 | Open-web content fetched through egress control and sanitised | Never permitted above the lowest risk tier | Prohibited without human review |

**Prohibitions on fallback content**: TC3 content is never written into a durable index, vector store, knowledge cache, or agent long-term memory without a recorded human review decision, because a single correction would otherwise contaminate every later retrieval. TC3 content never modifies prompts, rubrics, thresholds, budgets, tool selection, credentials, or fetch destinations; it enters the context as data, delimited and labelled. TC3 content never appears in an answer without a provenance marker naming its trust class, its source identifier, and its retrieval time. Two TC3 items do not corroborate each other where both resolve to the same origin domain or the same syndication source; that agreement is recorded as correlated and does not satisfy a corroboration requirement.

**Invocation conditions**: The correction layer is warranted where all of the following hold: measured retrieval failure on the target query slice is at least 10 percent of cases; retrieval failure causes a measured downstream answer failure rather than being absorbed by the generator; at least 1 alternate route can add admissible evidence; a labelled set exists or can be built to qualify the evaluator; and the added latency and cost fit the service objective.

**Suppression conditions**: The layer is withheld where a one-pass retriever already meets the target quality on the slice, where a deterministic source rule or a structured lookup resolves the query exactly, where every query must be answered from one designated authoritative source, where no alternate evidence route exists, where the only available correction is external search and egress policy forbids it, or where the latency budget cannot absorb a single evaluator call. Where the layer is suppressed, the substitute is named rather than left implicit: a stricter admissibility filter, a mandatory structured lookup, or a routing rule to a designated source.

**Numeric gate rule**: Invoke only where at least 1 alternate route is approved and the evaluator has passed the qualification gates in Phase 2. Where fewer than 1 alternate route exists, suppress and record the missing route, because a verdict with no bound action available is an observation without a lever. Where the projected evaluator and correction overhead exceeds 40 percent of the direct one-pass cost on the lowest risk tier, suppress and record the estimate for the next policy revision.

**Method boundaries**: This guide covers the evaluation step between retrieval and generation and the bounded correction it triggers. It does not cover the general control loop that decides how many retrieval turns an agent takes, how a multi-step search is planned, or how sub-agents are orchestrated across turns; that material belongs to agentic retrieval control-loop guidance and is deliberately not duplicated here, because this method fixes the loop shape to a verdict-keyed bounded correction. It does not cover the procedure for selecting among the retrieval-augmentation family members; that selection procedure is a separate task family, and this guide assumes the selection has already returned corrective retrieval. It does not cover corpus construction, chunking, hybrid retrieval, reranking, or index security, which are prerequisites the method assumes are already sound; a broken corpus or a broken access-control list is repaired before correction is added, never by adding correction. It does not cover generator-side reflection, critique, or claim verification, which are handled once at the release gate rather than as an unbounded self-critique loop inside the correction.

**Distinction from adjacent retrieval methods**: Self-reflective generation trains or prompts the generator to emit control tokens governing retrieval and support, whereas this method places an external evaluator between retrieval and generation and leaves the generator unchanged [4]. Complexity-based adaptive routing classifies the incoming question and selects a retrieval depth before any retrieval occurs, whereas this method acts on the observed quality of what was actually retrieved [5]; the two compose as front-door routing followed by post-retrieval correction, and a complexity prediction is never treated as an evidence-quality judgement. Active retrieval during generation triggers new retrieval when upcoming generated text carries low token confidence [6], which is a generation-time trigger rather than a retrieval-time grade. Trained multi-step search policies learn retrieval trajectories rather than executing a fixed three-verdict graph [7][8]; a learned search trajectory is not this method, and egress, authorisation, source eligibility, call limits, and stop rules remain outside any learned policy.

**Acronym collision**: The abbreviation this method shares with a widely used factual question-answering benchmark refers to two unrelated artifacts [9]. Written records must name the method in full or attribute it to its originating authors, and must name the benchmark in full where the dataset is meant. The bare acronym is never used as an artifact type in metadata, evaluation reports, or release notes.

***

## II. Operational Framework: Verdict-Gated Evidence Correction Under Bounded Attempts

The framework assumes the entry gate in Section 1.4 has returned invoke. Phases 1 and 2 run once per deployment or per evaluator change and produce a qualified evaluator with fitted thresholds. Phases 3 through 6 run once per request and form the correction loop, which either terminates through a declared exit or returns to Phase 3 with one changed input. Phase 7 runs against a frozen case set before any release.

### Phase 1: Contract Establishment and Evaluator Commissioning

**Objective**: Fix the run contract, select a scoring component that can be versioned and measured, and assemble the labelled evidence needed to qualify it, so that no evaluator gates production traffic on unmeasured behaviour.

#### Step 1.1: Define the Run Contract and Budget Ledger

**Required Actions**:

- Record the user intent, the required answer form, the set of required subquestions, the source boundary, the authority hierarchy, the freshness requirement, the authorisation context, the definition of a material claim, and the risk tier.
- Set numeric limits for correction attempts, query variants per attempt, total retrieval calls, external searches, fetches, input tokens, output tokens, monetary cost, and wall-clock deadline.
- Apply the deployment defaults of 2 correction attempts, 2 query variants per attempt, 1 external search route, and 3 total retrieval calls, raising any limit only from measured evidence-gain data on the affected slice.
- Declare the verdict thresholds, the strip retention threshold, the sufficiency threshold, the minimum evidence-gain delta, and the abstention and escalation conditions that will apply to this run.
- Reserve the measured 95th-percentile time and token cost of final verification and answer assembly, so that correction cannot consume the budget the release gate requires.

**Required Outputs**:

- A run contract record naming intent, required subquestions, source boundary, authority hierarchy, and risk tier.
- A budget ledger with a numeric limit on every bounded dimension.
- A threshold record naming the verdict, strip, sufficiency, and evidence-gain values in force for the run.

**Quality Checkpoints**:

- Every budget dimension carries a numeric limit; an unbounded dimension halts the run before retrieval.
- Every required subquestion is stated separately, so that partial coverage is detectable rather than absorbed into one composite question.
- The verification reserve is subtracted from the correction budget rather than shared with it.

***

#### Step 1.2: Select and Pin the Retrieval Evaluator

**Required Actions**:

- Select the evaluator implementation from the approved options: a hosted cross-encoder scorer already serving query-passage relevance, a calibrated feature classifier over retrieval and source signals, a model judge constrained to a versioned verdict schema, or a cascade in which a cheap scorer handles clear cases and a model judge handles a bounded uncertainty band.
- Require the evaluator to expose a numeric score rather than a categorical label alone, since a label without a score cannot be calibrated or threshold-swept.
- Constrain a model judge to a versioned output schema requiring a score, a cited evidence span, and a reason code, and hide generator identity, ranking position, and irrelevant metadata from its input.
- Pin the evaluator model version, artifact digest, tokenizer version, prompt or rubric version, decoding settings, and score range, and record them on every decision the evaluator produces.
- Record whether the deployment reproduces the originating trained evaluator or substitutes an agent-layer scorer, and label the deployment accordingly in release documentation.

**Required Outputs**:

- An evaluator selection record naming the implementation, its cost per call, and its measured latency at the 95th percentile.
- A pinned version manifest covering model, artifact digest, tokenizer, rubric, decoding settings, and declared score range.
- A declared fidelity statement distinguishing reproduction from agent-layer substitution.

**Quality Checkpoints**:

- The evaluator emits a numeric score inside the declared range on 100 percent of qualification calls; any out-of-range value is recorded as a fault rather than clipped.
- Ranking position is never passed to the evaluator as a feature or as confidence.
- The version manifest is complete, so that a later score can be attributed to an exact configuration.

***

#### Step 1.3: Assemble the Labelled Calibration Set

**Required Actions**:

- Collect at least 300 labelled query-passage pairs and at least 150 labelled query-level cases carrying an expected verdict, drawn from the deployment's own retrieval outputs rather than from a public benchmark.
- Populate every required content class: direct positives carrying the answer-bearing span; partial positives answering only 1 required subquestion; same-entity and same-topic hard negatives mined from actual retrieval results; lexically dissimilar but semantically relevant positives; plausible falsehoods, contradictions, superseded versions, and stale policies; high-relevance but unauthorised or low-authority documents; empty, malformed, duplicated, overlong, multilingual, and injected items; and queries that must be refused because the premise is false or the evidence does not exist.
- Ensure at least 100 pairs per verdict class and at least 30 cases per critical slice, where slices are defined by query class, source route, language, and risk tier.
- Have at least 2 qualified annotators label at least 20 percent of the set independently, adjudicate disagreements, and record the agreement statistic.
- Split by query, entity, time, and source family rather than at random, and freeze a held-out regression split before any threshold is fitted.

**Required Outputs**:

- A versioned calibration set with one record per pair carrying query, passage, source metadata, route, raw retriever score, human relevance label, answer-bearing span, authority, freshness, authorisation state, contradiction status, and slice labels.
- A split manifest naming the training, development, and held-out partitions and the splitting key used.
- An annotation quality record naming annotator count, double-labelled proportion, and the agreement statistic.

**Quality Checkpoints**:

- The set holds at least 300 pairs and at least 150 query-level cases; a smaller set blocks qualification and the evaluator may not gate production traffic.
- Inter-annotator agreement reaches at least 0.70 on the double-labelled portion; below that the rubric is revised and the affected labels are recollected.
- No query, entity, or source family appears in more than 1 split, so that near-duplicate leakage cannot inflate measured performance.

***

### Phase 2: Evaluator Calibration and Threshold Fitting

**Objective**: Convert raw evaluator output into a calibrated score, fit the threshold pair by expected decision loss rather than by assumption, and qualify the evaluator against explicit precision, recall, and calibration gates before it is permitted to gate any traffic.

#### Step 2.1: Fit the Calibration Transform on the Development Split

**Required Actions**:

- Fit the calibration transform on the development split only, never on the training split that produced the scores and never on the frozen held-out split.
- Compare at least 2 transform families, taking temperature scaling as the baseline for logit-shaped outputs and comparing it against Platt scaling or isotonic regression on the actual workload distribution [10].
- Map every calibrated output onto the interval from 0 to 1, so that the threshold pair, the strip threshold, and the reliability plots all read on one scale.
- Fit separate transforms per calibration slice where score distributions differ materially between slices, and record the slice identifier on every calibrated score.
- Reject a transform whose fit inverts the ordering of any adjudicated positive and negative pair, since a calibration that reorders evidence is repairing the wrong defect.

**Required Outputs**:

- A versioned calibration transform per slice, with its family, parameters, and fitting split recorded.
- A reliability record giving expected calibration error, maximum calibration error, and Brier score per slice.
- A calibrated score column added to every development and held-out record.

**Quality Checkpoints**:

- The transform was fitted on the development split alone; any use of held-out data in fitting voids the qualification.
- Expected calibration error on the development split is at most 0.10; a larger error blocks progression to threshold fitting.
- Every calibrated score falls inside the interval from 0 to 1, and every score carries its slice identifier.

***

#### Step 2.2: Fit the Threshold Pair by Expected Decision Loss

**Required Actions**:

- Declare the cost terms before the sweep: the loss of a false correct verdict, the loss of a false incorrect verdict, the cost of an unnecessary ambiguous dual-route acquisition, the cost of an internal retry, the cost of an external search, the cost of human review, and the abstention cost per risk tier.
- Sweep candidate lower and upper thresholds across the calibrated range in increments no coarser than 0.05, preserving a separation of at least 0.20 between them at every candidate pair.
- Compute for every candidate pair the per-verdict precision and recall, the macro-averaged score, the calibration error, the downstream correction success rate, the over-correction rate, the added latency, the added cost, and the count of policy violations.
- Select the least expensive pair that satisfies every hard gate in Step 2.3 and minimises expected decision loss, rather than the pair that maximises accuracy.
- Fit a stricter upper threshold for the highest risk tier and a stricter eligibility rule for external search where the query class is sensitive, so that one threshold is not shared across risk tiers.
- Freeze the held-out regression split before the sweep begins and evaluate the selected pair on it exactly once.

**Required Outputs**:

- A cost matrix naming every declared loss and cost term with its numeric value.
- A threshold sweep record holding one row per candidate pair with all computed metrics.
- A selected threshold set, versioned, with per-risk-tier variants and a recorded expected decision loss.

**Quality Checkpoints**:

- The separation between the selected thresholds is at least 0.20; a narrower band is rejected because it cannot absorb evaluator error.
- The ambiguous band covers between 10 percent and 35 percent of development cases; outside that range the fit is rejected and the evaluator is requalified.
- The held-out split was evaluated once after selection; repeated evaluation against it converts the regression set into a second development set and voids its evidence.

***

#### Step 2.3: Qualify the Evaluator Against Precision, Recall, and Calibration Gates

**Required Actions**:

- Measure precision and recall for each of the 3 verdicts separately on the held-out split, and report the full confusion matrix rather than aggregate accuracy alone.
- Apply the qualification gates: precision of the correct verdict at least 0.90 overall and at least 0.95 in the highest risk tier; recall of the incorrect verdict at least 0.85; macro-averaged score across the 3 verdicts at least 0.75; expected calibration error at most 0.10 overall and at most 0.05 in the highest risk tier; Brier score at most 0.20; and agreement with adjudicated human labels at least 0.75.
- Measure per-slice performance and apply the floor that no critical slice may carry correct-verdict precision below 0.80, since an aggregate pass can conceal a failing slice.
- Measure transfer performance on at least 1 corpus or query distribution absent from the fitting data, and record the drop, because evaluator behaviour is known to degrade across domains and reproduction analysis has shown one published evaluator relying on entity alignment rather than semantic support [2].
- Record the qualification verdict and bind it to the pinned evaluator version, so that any version change invalidates the qualification.

**Required Outputs**:

- A qualification report with per-verdict precision, recall, confusion matrix, calibration error, Brier score, and per-slice breakdown.
- A transfer record naming the out-of-fit distribution tested and the measured performance drop.
- A qualification verdict bound to the evaluator version manifest, stating pass or fail per gate.

**Quality Checkpoints**:

- Every qualification gate is measured on the held-out split, not estimated; an unmeasured gate counts as a failure.
- An evaluator failing any gate does not gate production traffic; traffic routes to the conservative policy in which every case is treated as ambiguous or escalated, and the failure is recorded.
- The qualification verdict names the exact evaluator version; an unversioned verdict is void.

***

### Phase 3: Primary Retrieval, Scoring, and Verdict Routing

**Objective**: Retrieve once from the primary source under deterministic admissibility filters, score the admissible passages with the qualified evaluator, and route the resulting verdict to exactly one bound corrective action.

#### Step 3.1: Retrieve Once Under Admissibility Filters

**Required Actions**:

- Issue the original query or a faithfully canonicalised form of it against the primary retriever, recording the normalised query digest.
- Apply authorisation, source-boundary, freshness, and integrity filters before any scoring, so that inadmissible content never consumes evaluator budget or enters a score distribution.
- Retrieve and rerank a bounded candidate set, recording candidate identifiers, source identifiers, raw and reranked scores, ranks, content hashes, corpus version, and index version.
- Assign the trust class deterministically from the route that produced each candidate, and quarantine any candidate whose class cannot be assigned.
- Fail closed where retrieval fails for a security or authorisation reason, rather than widening the source boundary to recover recall.

**Required Outputs**:

- An immutable candidate set with identifiers, scores, ranks, hashes, versions, and trust classes.
- An admissibility record naming every rejected candidate and its rejection reason.
- A normalised query record with the canonicalisation applied.

**Quality Checkpoints**:

- Admissibility is evaluated before relevance on 100 percent of candidates; a candidate scored before filtering is a tier violation.
- Every retained candidate carries exactly 1 trust class; unclassified content is quarantined rather than admitted at a default class.
- An authorisation failure produces a closed failure, never a broadened retrieval.

***

#### Step 3.2: Score Passages and Aggregate to One Verdict

**Required Actions**:

- Score every admissible passage with the pinned, qualified evaluator, and apply the slice-matched calibration transform to each raw score.
- Aggregate the calibrated scores under the declared policy, taking the maximum admissible score as the aggregate statistic so that the verdict is comparable to the originating formulation.
- Compare the aggregate against the threshold pair in force for the run's risk tier and emit exactly 1 verdict from the closed vocabulary.
- Override a model-derived correct verdict downward where source admissibility fails or where required-subquestion coverage is incomplete, and record the override with its reason code.
- Route a malformed, out-of-range, version-mismatched, or out-of-slice evaluator output to the conservative uncertainty policy rather than substituting an invented score.

**Required Outputs**:

- A per-passage decision record with raw score, calibrated score, slice identifier, admissibility verdict, and trust class.
- One aggregate score and one verdict per run, with the threshold values applied.
- An override record where the deterministic tier lowered a model-derived verdict.

**Quality Checkpoints**:

- Exactly 1 verdict is emitted per evaluation; zero verdicts or multiple verdicts halt the run.
- Every threshold comparison uses a calibrated score; comparing a raw score to a threshold is a defect that voids the routing decision.
- Every override lowers a verdict; an override raising a verdict is rejected without exception.

***

#### Step 3.3: Route the Verdict to Its Bound Corrective Action

**Required Actions**:

- Look up the bound action for the emitted verdict in the routing table and execute that action alone, without consulting the model on which action to take.
- Refuse any action the approved route manifest does not contain, and select the highest-ranked permitted route in its place.
- Increment the correction-attempt counter deterministically where the selected action performs any acquisition, and check the counter against the contract limit before the acquisition is issued.
- Record the routing decision with verdict, bound action, selected route, trust class of the target route, attempt index, and remaining budget on every dimension.
- Halt and escalate where the verdict is correct but admissibility has demoted every passage, since the run has no admissible evidence and no route left within the contract.

**Required Outputs**:

- A routing record naming verdict, bound action, selected route, attempt index, and remaining budget.
- An updated attempt counter and budget ledger.

**Quality Checkpoints**:

- The executed action is the one bound to the emitted verdict; any other action is a routing defect that halts the run.
- The attempt counter is incremented by deterministic code only; no model output and no retrieved content has modified it.
- Every acquisition is preceded by a budget check that passed, never followed by one.

***

### Phase 4: Knowledge Decomposition and Recomposition

**Objective**: Reduce a partially useful retrieved set to its supported fragments and reassemble them with provenance intact, so that document noise does not reach the generator and every claim remains traceable to an exact source span.

#### Step 4.1: Segment Documents into Provenance-Bearing Strips

**Required Actions**:

- Preserve the immutable original evidence object with its source identifier, document identifier, version, content hash, byte offsets, admissibility decision, trust class, and retrieval score, so that refinement never destroys the record it derives from.
- Segment on structure-aware boundaries, taking a sentence, paragraph, heading, list item, or table row as the unit, and treat a passage of 1 or 2 sentences as a single strip rather than splitting it further.
- Apply fixed-size segmentation only where no structural boundary is recoverable, and record that the fallback segmentation was used.
- Assign every strip a stable identifier and exact source offsets, and discard any strip whose offsets cannot be resolved back into the original document.
- Suppress segmentation entirely where the surrounding context is legally or scientifically material, or where tables, code, formulas, contracts, or safety procedures cannot be divided without loss, retaining the complete bounded section and citing exact spans instead.

**Required Outputs**:

- A strip inventory with identifier, offsets, parent document identifier, trust class, and segmentation mode per strip.
- A suppression record naming documents retained whole and the reason segmentation was withheld.

**Quality Checkpoints**:

- Every strip resolves to exact offsets in its parent document; strips without resolvable offsets are discarded before scoring.
- No strip crosses a document boundary, and no strip carries a trust class different from its parent document.
- Documents whose meaning depends on surrounding context were retained whole rather than segmented.

***

#### Step 4.2: Filter Strips and Recompose in Authority-Aware Order

**Required Actions**:

- Score each strip against the original user intent and against each required subquestion separately, so that a strip serving one subquestion is not discarded for failing another.
- Reject unauthorised, expired, malformed, injected, or integrity-failed strips before relevance scoring rather than after it.
- Retain strips scoring at or above the strip retention threshold, and additionally retain any strip supplying a required contradiction, qualification, or corroboration even where its relevance score falls below that threshold.
- Deduplicate near-identical strips while preserving every provenance link, so that a deduplicated strip still records each source that carried it.
- Recompose retained strips in source order within each document and in trust-class order across documents, keeping explicit separators, source identifiers, and trust-class labels between segments.
- Prohibit generative rewriting of retained evidence; where a generated summary is produced as an aid, label it a derivative and exclude it from the citable evidence set.

**Required Outputs**:

- A retained strip set with per-strip scores, retention reasons, and subquestion assignments.
- A recomposed evidence bundle with separators, source identifiers, and trust-class labels intact.
- A discarded strip record with rejection reasons preserved in the trace.

**Quality Checkpoints**:

- No contradictory strip was discarded solely because it lowers answer confidence.
- Every segment of the recomposed bundle maps back to exactly 1 source span; blended text with no resolvable origin is a defect that blocks generation.
- No generated summary appears in the citable evidence set.

***

#### Step 4.3: Run the Evidence Sufficiency Gate

**Required Actions**:

- Test the recomposed bundle against every required subquestion declared in the run contract, marking each as covered by at least 1 admissible strip or as uncovered.
- Test whether every prospective material claim has at least 1 supporting strip whose trust class permits it to serve as sole support at the run's risk tier.
- Require corroboration by a second independent item for any material claim supported only by a TC2 or TC3 strip, and record correlated agreement where two corroborating items share an origin domain or a syndication source.
- Emit a pass verdict only where 100 percent of required subquestions are covered and every material claim satisfies its trust-class support rule.
- On failure, enter the correction loop with the diagnosis recorded as partial coverage rather than relabelling the evidence as an incorrect verdict, since the retrieved set was not wrong but incomplete.

**Required Outputs**:

- A coverage matrix mapping each required subquestion to its covering strips or to an uncovered marker.
- A sufficiency verdict with the uncovered set named where the verdict is fail.
- A corroboration record for every claim supported only at TC2 or TC3.

**Quality Checkpoints**:

- Sufficiency is computed from subquestion coverage, never inferred from the aggregate relevance score.
- A partial-coverage failure enters the loop under its own diagnosis and never rewrites the emitted verdict.
- No material claim rests on a TC3 item alone above the lowest risk tier.

***

### Phase 5: Fallback Acquisition Under Trust Classing

**Objective**: Acquire replacement or supplementary evidence from the least risky eligible route, through a controlled boundary, with the trust class recorded on acquisition and carried unchanged into the answer's provenance.

#### Step 5.1: Diagnose the Failure and Select the Least Risky Eligible Route

**Required Actions**:

- Diagnose the failure into exactly 1 class: query mismatch, retrieval-parameter miss, index coverage gap, wrong source family, stale source, policy-restricted source, or partial coverage.
- Select the route bound to that diagnosis from the approved route manifest, walking the ladder from the least risky eligible entry upward and stopping at the first entry that can plausibly close the gap.
- Apply the route ladder in this order: a structured or tool lookup against a designated system of record; a faithful query rewrite against the primary index; a re-retrieval with exactly 1 changed parameter family; a query decomposition with per-subquery retrieval; an approved secondary corpus; an open web search and fetch; and human escalation.
- Validate a proposed query rewrite against the constraint-preservation rule, refusing any rewrite that drops or alters a named entity, a negation, a date, a unit, a jurisdiction, a quoted phrase, or an access constraint.
- Refuse to repeat the same combination of normalised query, filters, retriever, index, and result depth, and refuse to widen authorisation or tenant scope in order to improve recall.

**Required Outputs**:

- A diagnosis record naming exactly 1 failure class and the evidence that selected it.
- A route selection record naming the chosen route, its ladder position, its trust class, and the routes skipped with reasons.
- A constraint-preservation verdict for any rewritten query.

**Quality Checkpoints**:

- Exactly 1 primary correction executes per attempt, so its effect on evidence is attributable.
- The selected route is the lowest-risk eligible entry that matches the diagnosis; a higher-risk route chosen while a lower-risk one remains untried is a routing defect.
- No attempt repeats a prior query, filter, retriever, index, and depth combination, and no attempt widens authorisation scope.

***

#### Step 5.2: Acquire Fallback Content Through a Controlled Boundary

**Required Actions**:

- Confirm before any external call that tenant policy permits egress, geographic transfer, and provider retention for this query class, and stop and route internally or to a human where the intent cannot survive the required redaction.
- Allowlist providers, protocols, ports, domains or domain classes, response content types, maximum response size, redirect count, and timeouts, and resolve and validate every destination before and after redirects, blocking loopback, private address space, link-local ranges, metadata endpoints, unsupported schemes, and rebinding.
- Search first with a bounded result count, rank results by separate relevance and authority scores, and fetch only selected destinations through an egress-controlled service rather than directly from the generator.
- Validate status, content type, size, encoding, malware state, and content hash; strip executable content and active elements; normalise visible text while retaining offsets and structure; and scan for direct and indirect injection, hidden text, exfiltration requests, and tool-control language, treating detection as a signal rather than a complete defence [11][12].
- Quarantine any item failing integrity or injection policy so that it never reaches the evaluator or the generator, and delimit every admitted item as data that cannot modify prompts, rubrics, thresholds, budgets, tools, or destinations.
- Respect provider contracts, site terms, access controls, rate limits, retention policy, and automated-client directives, treating those directives as requested controls rather than as an authorisation mechanism [13].

**Required Outputs**:

- A fetch record per destination with resolved address, redirect chain, status, content type, byte count, content hash, and sanitiser verdict.
- A quarantine record naming every excluded item and the policy it failed.
- A sanitised content set carrying preserved offsets and structure.

**Quality Checkpoints**:

- Zero external calls occurred without a passing egress policy check; a single unchecked call is a release-blocking violation.
- Every fetched item carries a sanitiser verdict and an injection-detection verdict; an item missing either verdict is quarantined.
- No fetched content modified any prompt, threshold, budget, credential, tool selection, or destination.

***

#### Step 5.3: Tag Trust Class and Merge Without Flattening Provenance

**Required Actions**:

- Assign the trust class deterministically from the acquiring route at the moment of acquisition, and attach source identifier, retrieval time, publication or update time where available, content hash, authority rationale code, and sanitiser verdict to every admitted item.
- Score newly acquired content with the same evaluator, thresholds, admissibility rules, and strip discipline applied to the primary set, so that fallback evidence is not admitted on weaker terms than the evidence it replaces.
- Merge internal and fallback evidence while preserving route labels and trust classes as separate fields, never flattening them into one undifferentiated context.
- Detect contradictions between merged items and resolve them by trust-class precedence where the classes differ, escalating where two items of equal class contradict on a material claim.
- Mark every fallback-derived segment in the answer's provenance with its trust class, and block promotion of any TC3 item into a durable index, vector store, knowledge cache, or long-term memory without a recorded human review decision.

**Required Outputs**:

- A merged evidence bundle with per-item trust class, route label, and provenance fields.
- A contradiction register naming each conflict, the classes involved, and its resolution or escalation.
- A provenance marking record showing which answer segments derive from fallback content.

**Quality Checkpoints**:

- Every fallback item carries a trust class assigned at acquisition; a class assigned later, or inferred from content, is a defect.
- Internal and fallback evidence remain distinguishable in the merged bundle and in the answer's provenance.
- Zero TC3 items were written to a durable store without a recorded review decision.

***

### Phase 6: Bounded Correction, Oscillation Control, and Termination

**Objective**: Bound the number of corrective attempts, stop the loop the moment it stops producing evidence, and terminate through a declared exit so that exhausting the bound yields an abstention rather than an answer assembled from rejected content.

#### Step 6.1: Compute Evidence Gain and Decide Continuation

**Required Actions**:

- Compute the evidence gain of the completed attempt from newly covered required subquestions, newly admissible evidence identifiers supporting a previously unsupported material claim, resolved contradictions, and improved freshness on a claim whose freshness had failed.
- Count as zero gain every duplicate passage, every paraphrase of an already retained strip, every generated rewrite, every stylistic change, and every increase in evaluator confidence over unchanged evidence.
- Require a gain of at least 1 unit on any of the counted dimensions to permit a further attempt; a zero-gain attempt terminates the loop regardless of remaining budget.
- Compare the expected value of a further attempt against its latency, cost, and trust-class risk, and stop where the expected value is not positive, since remaining budget is never on its own a reason to continue.
- Enforce the contract limit of 2 correction attempts by default, raising it only from measured evidence-gain data on the affected slice, and never on the basis of a model request, a retrieved instruction, or a framework default.

**Required Outputs**:

- An evidence-gain record per attempt with each counted dimension and its increment.
- A continuation decision naming continue, exit, or abstain, with its trigger.
- An updated attempt counter and budget ledger.

**Quality Checkpoints**:

- Every continuation is justified by a measured gain of at least 1 unit; continuation on confidence alone is a defect.
- The attempt limit was enforced by deterministic code, and no retrieved content or model output raised it.
- Attempt 2 applies a different eligible route from attempt 1 against the unresolved gap.

***

#### Step 6.2: Detect Oscillation and Degenerate States

**Required Actions**:

- Compute a state hash after every attempt over the canonical query, the subquery set, the source route, the filters, the retrieval parameters, the ordered evidence identifiers and hashes, the emitted verdict, and the unresolved requirement set.
- Halt immediately on any of these conditions: the state hash repeats; the verdict alternates between correct and incorrect without new evidence; 2 consecutive attempts add no admissible evidence; the same sources return under paraphrased queries; evidence coverage or aggregate trust class decreases; contradictions, injection alerts, or policy violations increase; or the evaluator score changes materially while the evidence is unchanged.
- Halt on exhaustion of any hard budget for calls, tokens, cost, fetches, attempts, or wall-clock time, and halt where remaining time falls below the measured 95th-percentile verification reserve.
- Record the halt condition as a reason code from a closed vocabulary, so that degenerate-loop rates are countable across runs rather than reconstructed from prose.
- Refuse any extension of these limits proposed by a model, a retrieved page, a remote tool, or a framework default.

**Required Outputs**:

- A state-hash chain covering every attempt in the run.
- A halt record naming the triggering condition and its reason code.
- An oscillation flag and a repeated-state flag on the run record.

**Quality Checkpoints**:

- A repeated state hash halts the loop on detection, never after a further attempt.
- Every halt carries a reason code from the closed vocabulary; an uncoded halt is a logging defect that blocks release.
- No limit in force at run start was raised during the run.

***

#### Step 6.3: Execute a Declared Exit or Abstention

**Required Actions**:

- Exit successfully only where admissible evidence covers 100 percent of required subquestions, every material claim satisfies its trust-class support rule, and a further attempt carries non-positive expected value.
- Exit with a supported partial answer where the output contract permits partial completion, naming exactly which subquestions remain uncovered and why.
- Abstain where a required material claim remains unsupported, every eligible route is exhausted, a required source is unavailable, external search is prohibited, or the risk threshold for the tier is exceeded, and state in the abstention what is known, what is unsupported, which routes were attempted, and what would be required to answer.
- Prohibit generation from content the evaluator rejected: exhausting the attempt bound produces an abstention or a supported partial answer, never an answer assembled from discarded passages or from generator recollection presented as retrieval.
- Escalate to a human for unresolved contradictions between equally authoritative sources, high-impact unresolved gaps, suspected poisoning or injection, evaluator malfunction, or policy uncertainty, supplying the query, the immutable evidence snapshot, the evaluator outputs, and the correction history.

**Required Outputs**:

- An outcome record naming the exit condition, the coverage achieved, and the trust-class distribution of the cited evidence.
- An abstention or escalation package where the exit is not a success, carrying the state a reviewer needs without reconstruction.
- A final citation set resolving every material claim to an exact retained span.

**Quality Checkpoints**:

- The exit is 1 of the declared conditions; an undeclared exit is recorded as a bounded failure.
- Zero answers were generated from rejected content or from generator recollection substituted for retrieval.
- Every material claim in a released answer resolves to a retained span whose trust class permits that support.

***

### Phase 7: End-to-End Evaluation of the Corrected Pipeline

**Objective**: Measure the evaluator, the corrector, and the final answer as three separate quantities against a frozen case set, so that an aggregate improvement cannot conceal over-correction, fallback harm, or a failing slice.

#### Step 7.1: Build the Frozen Correction Evaluation Set

**Required Actions**:

- Store per case the query, the authorised corpus snapshot, the primary retrieval, the document and strip labels, the source authority and freshness, the expected verdict, the acceptable correction routes, the required evidence, the expected answer or required abstention, the risk tier, and the slice labels.
- Populate the required case classes: clean correct cases that must not be changed; clear incorrect cases with and without a recoverable alternate source; genuine ambiguous cases sitting near both thresholds; and partial-coverage, multi-hop, stale, contradictory, unanswerable, multilingual, exact-match, and long-document cases.
- Include adversarial cases: intent-preserving rewrites paired with drifting rewrites; external pages carrying indirect injection, hidden text, spoofed authority, duplicated content, and malicious redirects; and fallback cases where the internal source is more authoritative than the external one.
- Include failure-injection cases covering search-provider failure, fetch timeout, sanitiser failure, budget exhaustion, and evaluator outage.
- Freeze the set and its corpus and index snapshots before any tuning, and version it so that a later comparison is paired rather than approximate.

**Required Outputs**:

- A frozen, versioned evaluation set with the case classes above represented.
- A snapshot manifest pinning corpus version, index version, retriever version, and route manifest.

**Quality Checkpoints**:

- Every required case class holds at least 20 cases; a class below that count cannot support a rate estimate and blocks the release gate.
- The set was frozen before tuning began; a set extended during tuning is treated as a development set, not as evidence.
- Adversarial and failure-injection cases are present, since a set holding only clean cases measures nothing about correction safety.

***

#### Step 7.2: Measure Evaluator, Corrector, and Answer Quality Separately

**Required Actions**:

- Report evaluator quality as per-verdict precision, recall, and confusion matrix, false-correct rate, false-incorrect rate, ambiguous coverage and precision, calibration error, Brier score, threshold stability by slice, and transfer performance on an unfitted corpus.
- Report corrector quality as correction success rate, action-conditional success per route, over-correction rate, regression rate, unnecessary fallback rate, fallback harm rate, evidence gain by attempt and route, query-drift rate, repeated-state and oscillation rates, and budget-exhaustion rate.
- Report answer quality as correctness, groundedness, material-claim coverage, citation precision and recall, authority compliance, freshness compliance, abstention precision, abstention recall, and supported-partial rate.
- Report security and robustness as unauthorised-source rate, unapproved-egress rate, injection-detection recall on the adversarial set, quarantine rate, unsafe-content pass-through rate, worst critical-slice score, and perturbation stability.
- Apply the release thresholds: correction success at least 0.50 of entered cases; over-correction at most 0.05; regression at most 0.03; unnecessary fallback at most 0.20; fallback harm at most 0.02; abstention precision at least 0.90; citation precision at least 0.95; injection-detection recall at least 0.90; unauthorised-source and unapproved-egress rates exactly 0; and worst critical-slice score at least 0.80 of the aggregate.

**Required Outputs**:

- Three separate metric reports covering evaluator, corrector, and answer, each with per-slice breakdowns.
- A security and robustness report with the adversarial and failure-injection results.
- A threshold comparison table stating measured value and release threshold per metric.

**Quality Checkpoints**:

- Aggregate answer quality is never reported without the over-correction, fallback harm, latency, cost, and abstention figures beside it.
- Every zero-tolerance metric measures exactly 0; a single unauthorised source or unapproved egress event blocks release.
- No critical slice falls below 0.80 of the aggregate score; a failing slice blocks release for that slice even where the aggregate passes.

***

#### Step 7.3: Run the Required Ablations and the Release Gate

**Required Actions**:

- Run paired ablations on the frozen set covering at minimum: one-pass retrieval with no evaluator; the evaluator with no correction; a binary vocabulary with the ambiguous verdict removed; the full three-verdict method; strip refinement removed; query rewriting removed; fallback acquisition removed; fallback acquisition always applied; raw scores against calibrated scores; and 1 correction attempt against 2.
- Attribute the measured gain to a named component, and reject any component whose gain is not practically meaningful once latency, cost, abstention rate, security exposure, and over-correction are priced in.
- Gate release on the evaluator qualification from Step 2.3, the release thresholds from Step 7.2, a tested rollback, and passing egress, sanitiser, and authorisation checks.
- Cap threshold tuning at 5 cycles on the development set, revising the hypothesis rather than continuing to tune after the fifth, since further sweeps fit the development split rather than the workload.
- Retain the approved baseline where the evidence is inconclusive, and require an explicit recorded risk acceptance rather than weakening an authorisation, egress, integrity, groundedness, or abstention gate.

**Required Outputs**:

- An ablation table with one row per configuration and paired deltas against the frozen baseline.
- A release decision record naming every gate, its measured value, and its verdict.
- A rollback test record demonstrating restoration of the prior threshold set and evaluator version.

**Quality Checkpoints**:

- Every ablation ran against the same frozen cases and snapshots as the baseline; an unpaired comparison is not evidence.
- No hard gate was weakened to achieve a release; a gate that cannot be met produces an escalation with recorded risk acceptance.
- Rollback was executed and verified, not merely documented.

***

## III. Implementation Guidance for AI Agents

AI agents operating a corrective retrieval pipeline must follow systematic protocols ensuring that every verdict is calibrated, every corrective action is bound and counted, every piece of evidence carries a trust class, and every termination is declared. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Agent**: Owns the run contract, the budget ledger, and the threshold record in force. It alone may amend a limit, every amendment is versioned, and it refuses any amendment originating in retrieved content or model output.
2. **Retrieval Agent**: Issues the primary retrieval and every re-retrieval against approved indexes, applies admissibility filters before scoring, and records candidate identifiers, scores, ranks, hashes, and versions. It never selects a corrective action.
3. **Evaluator Service**: Scores query-passage and query-strip pairs with the pinned, qualified model and returns a score, a cited span, and a reason code under a versioned schema. It never emits a verdict and never selects an action.
4. **Routing Controller**: Applies the calibration transform, applies the threshold pair, emits exactly 1 verdict, selects the bound corrective action from the approved route manifest, increments the attempt counter, computes state hashes, and enforces every budget. It is deterministic software and holds authority over every model proposal.
5. **Acquisition Agent**: Executes the selected fallback route through the egress boundary, validates destinations, sanitises content, runs injection detection, quarantines failures, and assigns the trust class at the moment of acquisition.
6. **Refinement Agent**: Segments documents into strips, scores retention against the strip threshold, deduplicates, recomposes in trust-class order, and runs the sufficiency gate against the required subquestions.
7. **Instrumentation Agent**: Writes the append-only trace, enforces the content-logging policy, and computes the metric set. It may veto release where a zero-tolerance metric is non-zero.

**Evidence Disclosure and Logging Boundary**: The trace records decision metadata in full and raw content only under an approved policy. Log run and trace identifiers, evaluator version and score, verdict, thresholds in force, bound action, route, trust class, attempt index, state hash, evidence gain, sanitiser and injection verdicts, tokens, latency, and cost. Retain hashes, stable identifiers, redacted excerpts, and secure pointers in place of raw queries, pages, prompts, and outputs wherever the content-logging policy does not explicitly permit retention. Never persist a passing injection verdict as permanently valid; revalidate integrity, authority, and freshness on every reuse of cached external content.

**Workflow Execution Pattern**:

```
STATE: Verdict_Routing
INPUTS:
  1. Admissible candidate set with trust classes from Step 3.1
  2. Calibrated per-passage scores from Step 3.2
  3. Threshold set for the run risk tier from Step 1.1
  4. Attempt counter and budget ledger from the Contract Agent
ACTIONS:
  1. Aggregate calibrated scores to the maximum admissible score
  2. Compare aggregate against lower and upper thresholds
  3. Emit exactly one verdict from {CORRECT, INCORRECT, AMBIGUOUS}
  4. Apply admissibility and coverage overrides in the downward direction only
  5. Look up the bound action and select the route from the manifest
VALIDATION:
  - verdict_count == 1
  - verdict IN closed_vocabulary
  - score_is_calibrated == TRUE
  - threshold_separation >= 0.20
  - override_direction != UPWARD
  - selected_route IN approved_route_manifest
  - attempt_index < max_correction_attempts
  - remaining_budget_all_dimensions > 0
TRANSITIONS:
  IF verdict == CORRECT THEN next_state = Strip_Refinement
  IF verdict == AMBIGUOUS THEN next_state = Blend_Acquisition
  IF verdict == INCORRECT THEN next_state = Fallback_Acquisition
  IF attempt_index >= max_correction_attempts THEN next_state = Declared_Exit
  IF validation_failed THEN next_state = Routing_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended corrective action with its diagnosis, selected route, trust class, and projected cost without executing it; confirm it against the validation block while no call has been issued and no budget consumed; execute it only after validation passes, recording the routing event in the same operation.

**Approval Gate**: Human authorisation is required before any acquisition at trust class TC3 in the highest risk tier, before any promotion of TC3 content into a durable index or long-term memory, before any raise of the correction-attempt limit above 2, before release of a configuration whose evaluator failed any qualification gate in Step 2.3, and before any attempt projected to consume more than 40 percent of the remaining budget on any dimension. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the run contract, budget ledger, attempt counter, and state-hash chain in durable state outside the model context, since the loop may outlive one context window.
- Pass the recomposed evidence bundle to the generator rather than the raw candidate set, and count evidence tokens separately from instruction tokens so that correction cost is attributable.
- Summarise discarded candidates to identifier, score, and failure reason, retaining the reference and discarding the bulk.
- Write a handoff record at every context boundary naming the contract, the verdict history, the state-hash chain, the remaining budget, and the unresolved requirement set.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Commission Integrity (After Phase 1)**

- **Automated Check**: Every budget dimension carries a numeric limit; the evaluator version manifest is complete; the calibration set holds at least 300 pairs and at least 150 query-level cases with at least 100 per verdict class.
- **Agent Action on Pass**: Proceed to calibration and threshold fitting.
- **Agent Action on Failure**: Halt and return the missing artifact; no evaluator gates traffic on an incomplete commission.
- **Human Review Trigger**: Inter-annotator agreement below 0.70, or fewer than 30 cases in any critical slice.

**Checkpoint 2: Evaluator Qualification (After Phase 2)**

- **Automated Check**: Correct-verdict precision at least 0.90, incorrect-verdict recall at least 0.85, macro score at least 0.75, expected calibration error at most 0.10, ambiguous band coverage between 10 and 35 percent, threshold separation at least 0.20.
- **Agent Action on Pass**: Permit the evaluator to gate traffic at the qualified risk tiers.
- **Agent Action on Failure**: Route all traffic to the conservative policy in which every case is treated as ambiguous or escalated, and record the failing gate.
- **Human Review Trigger**: Any critical slice with correct-verdict precision below 0.80, or a transfer drop above 20 percentage points on the unfitted corpus.

**Checkpoint 3: Routing Validity (After Phase 3)**

- **Automated Check**: Exactly 1 verdict from the closed vocabulary; the comparison used a calibrated score; every override lowered rather than raised; the executed action is the one bound to the verdict; the attempt counter was incremented deterministically.
- **Agent Action on Pass**: Proceed to refinement or acquisition as bound.
- **Agent Action on Failure**: Halt the run; an invalid routing decision is never executed with a warning attached.
- **Human Review Trigger**: The same verdict emitted at 3 consecutive attempts without measured evidence gain.

**Checkpoint 4: Evidence Integrity (After Phase 4)**

- **Automated Check**: 100 percent of retained strips resolve to exact offsets; every bundle segment maps to exactly 1 source span; no generated summary is in the citable set; the coverage matrix is complete.
- **Agent Action on Pass**: Proceed to generation where sufficiency passed, or to the correction loop where it failed.
- **Agent Action on Failure**: Quarantine the unresolvable strips and recompose from the remainder; do not generate from a bundle with unmapped segments.
- **Human Review Trigger**: More than 20 percent of strips failing offset resolution, which indicates a segmentation or parsing defect rather than a content problem.

**Checkpoint 5: Fallback Safety (After Phase 5)**

- **Automated Check**: Zero external calls without a passing egress check; every fetched item carries sanitiser and injection verdicts; every item carries a trust class assigned at acquisition; zero TC3 items written to durable stores.
- **Agent Action on Pass**: Merge the acquired evidence with route labels preserved.
- **Agent Action on Failure**: Quarantine the affected items and re-run acquisition validation only, not the whole attempt.
- **Human Review Trigger**: Any injection detection on admitted content, any unapproved egress event, or any contradiction between two equally authoritative sources on a material claim.

**Checkpoint 6: Termination Validity (After Phase 6)**

- **Automated Check**: The exit is 1 of the declared conditions; the attempt count is within the contract limit; every material claim resolves to a retained span at a permitted trust class; no content the evaluator rejected appears in the answer.
- **Agent Action on Pass**: Release the outcome record and the citation set.
- **Agent Action on Failure**: Reclassify the exit as a bounded failure and abstain, reporting the uncovered requirements.
- **Human Review Trigger**: Any escalation condition, or an abstention rate above 25 percent on a slice that previously answered.

**Checkpoint 7: Release Conformance (After Phase 7)**

- **Automated Check**: All release thresholds in Step 7.2 met; unauthorised-source and unapproved-egress rates exactly 0; all required ablations run on the frozen set; rollback verified.
- **Agent Action on Pass**: Promote the configuration and record the approved threshold set and evaluator version.
- **Agent Action on Failure**: Withhold promotion and retain the approved baseline; no configuration is promoted on aggregate improvement alone.
- **Human Review Trigger**: Any zero-tolerance metric above 0, or an over-correction rate above 0.05.

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
EVALUATOR_VERSION:
THRESHOLD_SET_VERSION:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Evaluator Miscalibration or Drift**

- **Symptoms**: Reliability curves depart from the diagonal on the development split; the false-correct rate rises across releases without a threshold change; scores shift while the underlying corpus and retriever are unchanged; verdict distribution moves more than 10 percentage points week over week.
- **Diagnostic Steps**: Recompute calibration segmented by query class, source route, language, and risk tier to determine whether drift is confined to one segment; confirm the pinned evaluator version and rubric version match the qualification record; compare current score distributions against the distribution recorded at qualification.
- **Resolution Protocol**: Option A, refit the calibration transform on freshly labelled development data and re-run Step 2.3 before restoring the evaluator to gating duty. Option B, revert to the last approved threshold set and evaluator version while relabelling proceeds. Option C, restrict the evaluator to the segments where calibration still passes and route the remaining segments to the conservative policy. Option D, replace the evaluator implementation where the drift follows a provider model change outside the deployment's control.
- **Escalation Trigger**: A calibration gap above 20 percentage points in any segment suspends gating in that segment immediately; a generic threshold is never reused across slices, risk tiers, or evaluator versions.

**Error Type 2: Verdict Collapse into One Class**

- **Symptoms**: The ambiguous band covers more than 35 percent or less than 10 percent of traffic; nearly every run emits the same verdict; correction entry rate approaches 0 or 1.
- **Diagnostic Steps**: Inspect the calibrated score histogram for compression against one end of the range; confirm the threshold separation is at least 0.20; check whether admissibility filtering is removing so many candidates that the aggregate is computed over an almost empty set.
- **Resolution Protocol**: Option A, refit the threshold pair by expected decision loss on current data rather than adjusting a single threshold by hand. Option B, repair the retrieval stage where the score compression originates upstream, since correction cannot fix a retriever that returns nothing admissible. Option C, split the calibration slice where one slice's distribution is masking another's.
- **Escalation Trigger**: Collapse persisting after 1 refit cycle blocks release and returns the deployment to the approved baseline; further threshold adjustment on the same data is prohibited.

**Error Type 3: Correction Loop Without Evidence Gain**

- **Symptoms**: The state hash repeats; verdicts alternate without new evidence; 2 consecutive attempts add no admissible evidence; paraphrased queries return the same sources; budget drains while coverage is flat.
- **Diagnostic Steps**: Compare the state-hash chain across attempts to locate the repetition; confirm the diagnosis differed between attempts; verify the second attempt changed a different parameter family from the first.
- **Resolution Protocol**: Option A, change the source route rather than the query, since a query change against an index with a coverage gap cannot produce gain. Option B, decompose the query and retrieve per subquestion where the failure is partial coverage rather than total mismatch. Option C, terminate through an abstention naming the uncovered requirements. Option D, escalate with the state-hash chain attached where the gap is high-impact.
- **Escalation Trigger**: An identical state hash halts the loop on first repeat; more than 2 attempts against 1 unresolved requirement escalates regardless of remaining budget.

**Error Type 4: Fallback Content Harm**

- **Symptoms**: Injection detection fires on admitted content; an answer cites a lower-authority external source in place of an available internal one; contradictions increase after acquisition; external content appears in a durable store without a review record.
- **Diagnostic Steps**: Trace each admitted external item to its acquisition record, sanitiser verdict, and trust class; determine whether the route ladder was walked or skipped; check whether two corroborating items share an origin domain.
- **Resolution Protocol**: Option A, quarantine the affected items, purge them from the bundle, and regenerate from the remaining admissible evidence. Option B, disable the external route for the affected query class and fall back to internal or structured routes only. Option C, purge the durable store of the improperly promoted content and re-index from the approved snapshot. Option D, abstain where removing the affected items leaves a material claim unsupported.
- **Escalation Trigger**: Any unapproved egress event, any injection reaching the generator, and any TC3 promotion without review escalate immediately; this class is never resolved by retrying the fetch.

**Error Type 5: Over-Correction of Passing Cases**

- **Symptoms**: Cases that passed on the initial retrieval fail after correction; citation precision falls while correction entry rate rises; the unnecessary fallback rate exceeds 0.20.
- **Diagnostic Steps**: Recompute the paired baseline on the frozen set to separate genuine regression from evaluation noise; check whether the upper threshold sits too high for the slice; check whether the sufficiency gate is rejecting adequate bundles.
- **Resolution Protocol**: Option A, lower the upper threshold for the slice by refitting under the declared cost matrix, so that adequate evidence stops entering the loop. Option B, add a conservative pre-loop sufficiency check that exits before any acquisition where the initial bundle already covers every requirement. Option C, disable the correction layer for the slice where historical marginal utility is non-positive.
- **Escalation Trigger**: An over-correction rate above 0.05 blocks release; above 0.10 the correction layer is disabled for the affected slice pending refit.

**Error Type 6: Budget Exhaustion Before Sufficiency**

- **Symptoms**: Remaining budget cannot fund the next attempt; latency rises while coverage is flat; remaining time falls below the verification reserve.
- **Diagnostic Steps**: Attribute consumption across evaluator inference, retrieval, external search, fetch, sanitisation, and generation to locate the overrun; compare against the planned profile for the slice.
- **Resolution Protocol**: Option A, exit with a supported partial answer naming the uncovered requirements where the output contract permits partial completion. Option B, abstain and state what is known, unsupported, attempted, and required. Option C, reduce the candidate set size or the strip count for the slice so that the evaluator cost per run falls below the profile.
- **Escalation Trigger**: Correction cost above 40 percent of total run cost escalates for policy review; the loop is never continued on the expectation that remaining budget alone justifies another attempt.

**Troubleshooting Decision Tree**:

```
CHECKPOINT DETECTS A PROBLEM
├─ EVALUATOR DEFECT
│   ├─ Calibration gap above 20 points in a segment → Suspend gating in that segment; refit
│   ├─ Verdict collapse beyond the 10-35 percent band → Refit threshold pair; if it persists, revert to baseline
│   └─ Score outside declared range → Record as fault; route to conservative policy
├─ ROUTING DEFECT
│   ├─ Zero or multiple verdicts → HALT; reissue exactly one verdict
│   ├─ Action not bound to the verdict → HALT; execute the bound action only
│   ├─ Override raised a verdict → Reject the override; retain the lower verdict
│   └─ Route absent from the manifest → Refuse; select the highest-ranked permitted route
├─ LOOP DEFECT
│   ├─ State hash repeats → HALT the loop; abstain or escalate
│   ├─ Two attempts with zero evidence gain → Terminate; do not spend remaining budget
│   └─ Attempt limit reached → Exit through abstention or supported partial answer
├─ EVIDENCE DEFECT
│   ├─ Strip offsets unresolvable → Discard the strip; recompose from the remainder
│   ├─ Bundle segment maps to no source → Block generation; repair provenance
│   └─ Material claim unsupported at its trust class → Require corroboration or abstain
└─ FALLBACK DEFECT
    ├─ Injection detected on admitted content → Quarantine; purge; regenerate or abstain
    ├─ Unapproved egress event → HALT release; escalate immediately
    └─ TC3 promoted without review → Purge the durable store; re-index from snapshot
```

### D. Performance Metrics and Continuous Learning

**Evaluator Metrics**:

- **Correct-verdict precision**: Correct verdicts whose evidence genuinely sufficed (target: at least 0.90 overall, at least 0.95 in the highest risk tier).
- **Incorrect-verdict recall**: Genuinely failed retrievals the evaluator caught (target: at least 0.85; below this, correction never fires on cases that need it).
- **Expected calibration error**: Divergence between stated and observed support frequency per slice (target: at most 0.10 overall, at most 0.05 in the highest risk tier).
- **Ambiguous band coverage**: Share of traffic in the middle band (target: 0.10 to 0.35; outside this range the evaluator is requalified).
- **Transfer drop**: Performance loss on a corpus absent from the fitting data (target: at most 20 percentage points; a larger drop restricts the evaluator to fitted slices) [2].

**Correction Metrics**:

- **Correction success rate**: Entered cases passing every final gate after correction (target: at least 0.50).
- **Over-correction rate**: Initially passing cases made worse (target: at most 0.05).
- **Regression rate**: Cases whose correctness, groundedness, authority, freshness, or citation score fell (target: at most 0.03).
- **Unnecessary fallback rate**: Acquisitions that added nothing the initial bundle lacked (target: at most 0.20).
- **Fallback harm rate**: Acquisitions introducing a wrong, lower-authority, injected, stale, or contradictory source (target: at most 0.02).
- **Evidence gain per attempt**: Counted units added per attempt (target: at least 1 on attempt 1; a second attempt averaging below 0.5 indicates the limit should fall to 1) [3].

**Safety and Efficiency Metrics**:

- **Unauthorised-source rate and unapproved-egress rate**: Zero-tolerance counts (target: exactly 0; any occurrence blocks release).
- **Injection-detection recall**: Adversarial items caught before the generator (target: at least 0.90 on the adversarial set).
- **Citation precision**: Material claims resolving to a retained span that supports them (target: at least 0.95).
- **Abstention precision**: Abstentions correct under later adjudication (target: at least 0.90).
- **Correction overhead**: Correction cost over total run cost (target: at most 25 percent; above 40 percent triggers policy review).
- **Latency by verdict**: The 50th, 95th, and 99th percentiles reported per verdict and per attempt, with time to first token reported separately where correction delays generation.

**Log-Pattern Failure Detection**: A rising ambiguous share with flat correction success indicates evaluator collapse rather than genuine uncertainty. Repeated identical state hashes indicate a retry loop that the gain check failed to catch. External-source share rising while citation precision falls indicates the route ladder is being skipped. High correct-verdict rates alongside falling groundedness indicate a false-correct problem that aggregate accuracy conceals. Quarantine counts concentrated on one domain class indicate a source that belongs on a block list rather than in the ranking.

**Learning and Adaptation Mechanisms**:

- **Slice-bound recalibration**: Recompute the calibration transform and threshold pair per slice on a fixed cadence and after any corpus, retriever, evaluator, or query-distribution change; the numbers in this guide are deployment defaults, not constants.
- **Hard-negative replenishment**: Mine new hard negatives from production retrievals that produced false-correct verdicts, and add them to the labelled set rather than adjusting thresholds to hide them.
- **Route-performance memory**: Retain diagnosis, selected route, trust class, evidence gain, cost, and outcome per attempt, so that route ranking improves against observed history rather than assumption.
- **Sampled human review**: Adjudicate a random sample of at least 50 production traces per week against the rubric, and treat systematic disagreement as evidence that the rubric or the evaluator requires revision.
- **Version-paired evaluation**: Version every threshold set and evaluator together and evaluate any change on the frozen set before promotion, so that an improvement is attributable to a named component.

**Human-in-the-Loop Boundaries**: Promotion of external content into durable memory, amendment of an authorisation or egress policy, release of a configuration whose evaluator failed a qualification gate, resolution of a contradiction between equally authoritative sources on a material claim, and any raise of the correction-attempt limit are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the admission of evidence rather than the content of any particular evidence. Its phases hold wherever retrieval quality varies by query, more than 1 evidence route exists, and a wrong answer costs more than an abstention.

### 4.1 Cross-Domain Application Patterns

**Clinical and biomedical evidence**: The trust-class ladder is steep and the risk tier is high, so the upper threshold is tightened and TC3 content is barred from supporting any clinical claim. Segmentation is suppressed for dosing tables, contraindication lists, and protocol steps, which are retained whole and cited by span, because removing surrounding text can invert the meaning of a qualification. The fallback ladder terminates at approved literature indexes and structured registries rather than open search, and an exhausted ladder produces an abstention with the uncovered requirement named, since a plausible unsupported answer is the most expensive outcome available.

**Legal and contractual analysis**: Materiality is defined by clause rather than by sentence, so the strip boundary follows the clause and the sufficiency gate tests coverage of every element of the legal test. Contradictory strips are retained by rule, since a carve-out that lowers answer confidence is often the operative provision. Version and jurisdiction enter admissibility rather than relevance: a superseded clause with a high relevance score is inadmissible, not merely lower ranked, and the deterministic tier demotes it regardless of the evaluator's score.

**Software engineering and technical support**: Retrieval failures are frequently version failures, so freshness and version filters run before scoring and the diagnosis vocabulary carries a stale-source class that routes to a version-pinned index rather than to a query rewrite. The structured lookup sits at the top of the route ladder because build metadata, dependency graphs, and issue trackers are systems of record for their fact classes. External community content is admitted at TC3 with corroboration required, since it is often correct, often stale, and rarely authoritative.

**Financial and market operations**: Freshness dominates authority for price-like facts and authority dominates freshness for policy-like facts, so the admissibility rule is keyed to the fact class rather than applied uniformly. External acquisition carries a residency and retention check before the query leaves the boundary, and a query that cannot survive redaction routes internally or to a human rather than being sent in reduced form. Abstention is preferred over a supported partial answer where a partial figure would be acted upon as complete.

**Scientific and technical research synthesis**: Corroboration requirements are stricter than trust classes alone imply, because two secondary summaries of one primary result are correlated rather than independent, and the corroboration check therefore resolves each item to its primary source before counting it. Query decomposition is the default correction for multi-part questions rather than a rewrite, and the sufficiency gate tests each subquestion separately so that a well-covered subquestion cannot mask an uncovered one.

**Customer-facing knowledge operations**: Volume makes evaluator cost the dominant term, so the cascade configuration handles clear cases with a cheap scorer and reserves the model judge for the calibrated uncertainty band. Latency budgets are tight, so the attempt limit falls to 1 and the ambiguous band is narrowed toward 0.10 rather than widened. Abstention is expressed as a routed handoff rather than a refusal, since the operational cost of an escalation is low relative to a confidently wrong answer.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk, high-volume work**: Set the attempt limit to 1, narrow the ambiguous band toward 0.10, run a cheap scorer with a model judge only inside the band, and disable external acquisition entirely. Correction overhead above 25 percent of direct one-pass cost indicates the entry gate should have suppressed the layer for the slice.
- **High-risk or irreversible work**: Retain every phase, tighten the upper threshold, require corroboration for every material claim above TC1, bind the approval gate before any TC3 acquisition, and prefer abstention over a supported partial answer. Evaluator qualification is re-run per risk tier rather than inherited from the aggregate.
- **Strict latency budgets**: Reduce the candidate set and the strip count rather than removing the evaluator, since removing the evaluator removes the method while reducing its input merely lowers its cost. Where the budget cannot absorb 1 evaluator call, the entry gate suppresses the layer and a deterministic source rule runs with a declared fallback.
- **Small corpora and prototypes**: Run the layer with a constrained model judge, deterministic source and freshness rules applied first, 1 rewrite and 1 alternate local route permitted, and 1 record per run and attempt written to a flat log. Label the deployment as an agent-layer substitution rather than a reproduction, and make no claim of calibrated probability until a labelled set exists.
- **Multi-tenant deployments**: Fit and version the calibration transform and threshold pair per tenant policy class where score distributions differ, keep the route manifest and the egress allowlist per tenant, and never let a cache entry cross a tenant or policy boundary.

***

## V. Limitations and Considerations

**The evaluator is itself a fallible judge**: The component that decides whether evidence is good is subject to the same errors as the system it guards, and an uncalibrated evaluator either passes bad documents into generation or discards good ones and triggers unnecessary fallback. The mitigation is the qualification discipline in Phase 2: a labelled set of stated minimum size, a calibration transform fitted on a separate split, precision and recall gates that must be met before the evaluator gates anything, and a conservative routing policy that takes over the moment a gate fails.

**Model judges are systematically overconfident**: Verbal confidence from a model judge is not a probability, and published analysis documents overconfidence and calibration instability in judge configurations [14][15]. The mitigation is to require a numeric score rather than a verbal label, to pass every score through a fitted calibration transform before any threshold comparison, and to prohibit a model judge from serving as the sole release authority for high-risk evidence.

**Thresholds here are defaults, not measured constants**: The threshold pair of 0.70 and 0.30, the strip threshold of 0.50, the band-coverage range of 0.10 to 0.35, and the release thresholds in Step 7.2 were chosen to be operable on first deployment, not derived from a property of retrieval systems. The mitigation is the fitting procedure in Step 2.2 and the recalibration requirement in Section III.D, which oblige each deployment to replace them with values fitted against its own cost matrix and to record any unfitted deployment as such.

**Reported research figures do not transfer**: The originating evaluator accuracy figure, the dataset-specific thresholds, and the reported overhead were measured on one evaluator, one corpus, and one hardware configuration, and reproduction analysis has since shown the published evaluator relying on entity alignment rather than semantic support and degrading on out-of-domain science questions [1][2]. The mitigation is Section 1.2, which carries those numbers explicitly as reproduction settings, and Step 2.3, which requires a transfer measurement on an unfitted corpus before qualification.

**Fallback expands the attack surface it was invoked to repair**: External acquisition admits content from a lower trust class, and retrieved documents are a recognised indirect prompt-injection channel that retrieval architecture alone does not close [11][12]. The mitigation is the controlled boundary in Step 5.2, the trust-class ladder and its prohibitions in Section 1.4, and the zero-tolerance release metrics for unauthorised sources and unapproved egress.

**Correction can cost more than it saves**: The layer adds evaluator inference, extra retrieval, acquisition, sanitisation, and verification to every query it enters, and on slices where one-pass retrieval already succeeds it consumes budget and adds risk without adding evidence. The mitigation is the entry gate in Section 1.4, the unnecessary-fallback and over-correction metrics in Section III.D, and the option to disable the layer per slice where historical marginal utility is non-positive.

**The middle band is a cost multiplier**: Widening the ambiguous band absorbs evaluator error but doubles acquisition on every case it covers, and a band widened to hide uncertainty converts a calibration problem into a budget problem. The mitigation is the 0.10 to 0.35 coverage rule, enforced at Checkpoint 2 and re-measured at every recalibration, together with the requirement that band width be selected under the declared cost matrix rather than adjusted by hand.

**Available implementations diverge from the method**: Widely used workflow scaffolds implement document grading and query rewriting while simplifying or omitting the three-verdict aggregate policy, the strip refinement, and the bounded acquisition boundary, and their permissive default loop limits exceed what this guide permits [16][17][18][19][20]. The mitigation is to treat such scaffolds as orchestration only, to add the aggregate policy, refinement, safe-fetch boundary, evidence-gain test, and attempt budget explicitly, and to describe the result as an agent-layer implementation rather than a reproduction.

**Structural conformance is not evidence quality**: A run can satisfy every checkpoint here and still answer from a corpus that is stale, incomplete, or wrong, because the framework governs admission and correction rather than the contents of the index. The mitigation is the prerequisite stated in Section 1.4: corpus, access control, and index lifecycle defects are repaired before the correction layer is added, never by adding it.

***

## VI. Conclusion and Summary

Corrective retrieval-augmented generation is an admission discipline before it is a retrieval technique. Its value comes from a small number of explicit, auditable decisions: whether the correction layer is warranted at all, what score the evidence receives, which verdict that score resolves to, which single action the verdict binds, what trust class the resulting evidence carries, and whether the loop has earned another attempt. A system that makes those decisions explicitly and records them can be measured and improved; a system that grades evidence informally and reacts to the grade with whatever action seems appropriate has added cost without adding control.

The two components that carry the method are the evaluator and the closed verdict vocabulary. The evaluator must be treated as a fallible judge that earns its gating authority through measured precision, recall, and calibration on a labelled set, not as an oracle whose score is trusted because it is numeric. The vocabulary must stay closed and each verdict must stay bound to exactly one action, because the moment a verdict can select among several actions the effect of a correction stops being attributable and the evaluation in Phase 7 stops meaning anything.

A team introducing this layer should instrument a baseline before building a corrector. Measure one-pass retrieval quality per slice, identify the slices where retrieval failure actually causes answer failure, and build the labelled set against those slices. Add the evaluator and the threshold pair with correction disabled, and confirm the verdicts predict downstream failure before any action is bound to them. Add exactly 1 correction route, usually a structured lookup or a faithful rewrite, and measure evidence gain, over-correction, and cost against the frozen baseline. Only then add a second attempt, a secondary corpus, or an external route, and add the external route last because it carries the trust-class and security exposure the earlier routes do not.

**Key Success Factors**:

- **Calibration before gating**: The evaluator earns its authority on a labelled set of stated minimum size, against precision, recall, and calibration targets, and loses that authority the moment a gate fails.
- **A closed vocabulary with bound actions**: Three verdicts, one action each, exactly one primary correction per attempt, and a deterministic router that selects the action once a verdict exists.
- **Fitted thresholds, not assumed ones**: The threshold pair is selected by expected decision loss under a declared cost matrix, refitted per slice, and never copied from a research reproduction setting.
- **Trust class carried end to end**: Every item is classed at acquisition, the class travels into provenance and citations, and fallback content is never promoted into durable memory without review.
- **Bounded correction with honest exhaustion**: Attempts are counted deterministically, zero evidence gain terminates the loop, and exhausting the bound produces an abstention rather than an answer built from rejected content.
- **Separate measurement of evaluator, corrector, and answer**: Aggregate answer quality is never reported without over-correction, fallback harm, cost, and abstention beside it.

By following this guide, AI agents can place a measured evaluation step between retrieval and generation, correct poor evidence through the least risky route that can close the gap, and terminate through a declared exit that a reviewer can audit rather than through an unbounded loop or a confidently unsupported answer.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them; except where an entry is marked as verified or located during conversion, they were not independently re-verified, and their titles and locations are reproduced rather than checked. Entry 2 was retrieved and its title confirmed during conversion research. Entries 3 and 28 were located during conversion research through search listings and are cited at the locations those listings gave.

**Corpus pointers**:

- `Corrective RAG: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the three-action mechanism and its entry conditions, the reproduction threshold settings and the warning against reusing them, the decompose-filter-recompose refinement procedure, the evaluator selection options and training-data construction, the threshold selection procedure by decision loss, the correction route ladder, the external-source pipeline, the bounded workflow and its oscillation stop rules, the graceful degradation rules, the evaluation and ablation inventories, the logging field inventory, and the framework fidelity assessments. Its inline citations to primary literature supply the external references listed below.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/knowledge-retrieval/guide_AdvancedKnowledgeRetrieval.md` — the family-selection guide Section 1.4 defers to, which places corrective retrieval at rung 8 and owns the corpus construction, chunking, hybrid retrieval, reranking, and index security this method assumes are already sound.
- `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md` — the agentic control-loop guidance Section 1.4 declines to duplicate, which invokes this method as one bounded action inside an iteration rather than restating its verdict routing.
- `advanced_task_guides/knowledge-retrieval/guide_SelfRAG.md` — the generator-side reflection and claim-verification guidance Section 1.4 excludes, applicable at the release gate rather than as a self-critique loop inside the correction.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — companion guidance on faithful rewriting and decomposition, applicable to the rewrite and decomposition rungs of the route ladder in Step 5.1 and to the constraint-preservation validation they must pass.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control loops, stuck-state detection, and declared exits, applicable to the correction loop in Phase 6.
- `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md` — companion guidance on provenance and evidence tracking, applicable to the strip provenance in Phase 4 and the trust-class record in Phase 5.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design and instrumentation, applicable to the trace and metric requirements in Section III.
- `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guidance on monitoring under constraint, applicable to the drift and calibration monitoring in Section III.D.
- `advanced_task_guides/policy-risk/guide_InformationDependencyDisclosureRiskAnalysis.md` — companion guidance on disclosure and dependency risk, applicable to the egress and residency checks in Step 5.2.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, III, IV, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*The method, its reproduction, and its record*

1. Yan et al., *Corrective Retrieval Augmented Generation* — https://arxiv.org/html/2401.15884
2. Yalavarthi, *Open-Source Reproduction and Explainability Analysis of Corrective Retrieval Augmented Generation* — https://arxiv.org/abs/2603.16169 (retrieved and verified during conversion)
3. *A corrective agentic hybrid RAG and an operations-grounded evaluation for a scientific facility* — https://arxiv.org/html/2607.24663v1 (located during conversion research; source of the finding that gains concentrate in the first corrective round, supporting a two-attempt cap)
4. Asai et al., *Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection* — https://arxiv.org/abs/2310.11511
5. Jeong et al., *Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity* — https://aclanthology.org/2024.naacl-long.389/
6. Jiang et al., *Active Retrieval Augmented Generation* — https://arxiv.org/abs/2305.06983
7. Jin et al., *Search-R1: Training LLMs to Reason and Leverage Search Engines with Reinforcement Learning* — https://arxiv.org/abs/2503.09516
8. Song et al., *R1-Searcher: Incentivizing the Search Capability in LLMs via Reinforcement Learning* — https://arxiv.org/abs/2503.05592
9. Yang et al., *CRAG—Comprehensive RAG Benchmark* — https://arxiv.org/abs/2406.04744

*Calibration and judge reliability*

10. Guo et al., *On Calibration of Modern Neural Networks* — https://arxiv.org/abs/1706.04599
14. Tian et al., *Overconfidence in LLM-as-a-Judge: Diagnosis and Confidence-Driven Solution* — https://arxiv.org/abs/2508.06225
15. Fiedler, *Bias and Uncertainty in LLM-as-a-Judge Estimation* — https://arxiv.org/abs/2605.06939

*External-source security*

11. OWASP, *LLM01:2025 Prompt Injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
12. OWASP, *Retrieval-Augmented Generation Security Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html
13. RFC 9309, *Robots Exclusion Protocol* — https://www.rfc-editor.org/rfc/rfc9309

*Implementation scaffolds assessed for fidelity*

16. LangGraph, *Corrective RAG (CRAG)* legacy tutorial — https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/
17. LangGraph, *Build a custom RAG agent with LangGraph* — https://docs.langchain.com/oss/python/langgraph/agentic-rag
18. LlamaIndex, *Corrective RAG Workflow* — https://developers.llamaindex.ai/python/examples/workflow/corrective_rag_pack/
19. LlamaIndex CorrectiveRAGPack — https://github.com/run-llama/llama_index/tree/v0.10.29/llama-index-packs/llama-index-packs-corrective-rag
20. Haystack, *Pipeline Loops* — https://docs.haystack.deepset.ai/docs/pipeline-loops

*Supporting material carried without an inline marker*

21. Official Corrective RAG repository — https://github.com/HuskyInSalt/CRAG
22. ICLR 2025 withdrawn submission record — https://openreview.net/forum?id=JnWJbrnaUE
23. Wang et al., *Chain-of-Retrieval Augmented Generation* — http://arxiv.org/pdf/2501.14342.pdf
24. Jiang et al., *Harness-1: Reinforcement Learning for Search Agents with State-Externalizing Harnesses* — https://arxiv.org/abs/2606.02373
25. Kumar et al., *Search-GRT: Guided Retrieval Training of Search Agents to Optimize for Complex Question Answering* — https://arxiv.org/abs/2608.00974
26. Official Comprehensive RAG Benchmark repository — https://github.com/facebookresearch/CRAG
27. Li et al., *RAGPerf: An End-to-End Benchmarking Framework for Retrieval-Augmented Generation Systems* — https://arxiv.org/abs/2603.10765
28. *Curated retrieval versus open web search in public AI information services: a coverage-trust trade-off* — https://arxiv.org/pdf/2607.05217 (located during conversion research; bears on the trust-class ladder in Section 1.4)
