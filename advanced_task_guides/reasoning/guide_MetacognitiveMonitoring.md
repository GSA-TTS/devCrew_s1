# Metacognitive Monitoring

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Metacognitive monitoring constitutes the task family of constructing, calibrating, and maintaining the signals by which an in-progress reasoning process is judged from outside itself. This guide provides AI agents with a structured protocol for operating the monitor layer of an object, monitor, and control architecture: which properties of an active reasoning process are actually measurable, how each is computed from an observation record rather than from introspection, how a stated confidence is calibrated against observed outcomes before it is permitted to gate anything, how signal independence is established so that agreement is not mistaken for confirmation, and how a calibrated verdict is handed to the control layer without the monitor changing the process it observes. It fixes an execution tier partition assigning every signal computation, calibration measure, threshold evaluation, and monitoring record to deterministic software, and confining model inference to judgements no deterministic signal covers, in a proposing rather than a deciding role. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures to ensure that a monitor measures what it claims to measure, and is suspended when it does not.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Metacognitive monitoring**: The construction and maintenance of measurements that estimate whether an agent's current answer, plan, evidence, and execution are adequate, carried out by a component that observes the task process without solving the task [1]. Monitoring produces measurements; it does not act on them.

**Monitor layer**: The component that observes progress, evidence, quality, uncertainty, resources, and failures without solving the task and without changing the method. This guide specifies the monitor layer; the control layer that consumes its output is specified separately in the corpus.

**Object layer**: The component that solves the task or acts in the environment, producing candidate answers, plans, tool calls, and observations. It is the subject of measurement, never its author.

**Control layer**: The component that decides whether to continue, verify, repair, switch, branch, escalate, or stop. It alone may change the method in flight.

**Monitored decision**: The specific choice the monitor exists to inform, stated as a pair of materially different actions such as answer against abstain, act against request confirmation, or continue against stop. A monitor with no monitored decision produces measurement without control.

**Observable event**: The future occurrence against which a signal is defined and later scored, such as correctness, claim support, tool completion, or rubric passage. A signal defined against no observable event cannot be calibrated.

**Label source**: The named process that determines whether the observable event occurred, together with its latency, cost, and error rate. Delayed labels are permitted; absent labels disqualify the signal from gating use.

**Signal**: One measured quantity carrying a target event, a direction, a valid range, a source, a version, and a validity flag. A number without those six attributes is not a signal and is rejected at parse time.

**Process signal**: A signal computed by deterministic software from the execution record of the object layer, such as subgoal progress, repetition, or budget consumption. Process signals require no model inference and cannot be manipulated by the object layer's own account of itself.

**Estimator signal**: A signal that estimates the probability of the observable event, obtained by eliciting a model report, by sampling, or by reading provider-returned probabilities. Estimator signals require calibration before use.

**Computable definition**: A statement of a signal as a function over recorded fields, such that two independent implementations reading the same record produce the same value. A definition that requires a model to introspect is not computable and is not admitted.

**Calibration**: The property that predictions carrying a stated probability of p are followed by the observable event in approximately p of cases, for the declared event and population. Calibration is a property of a signal against a population, never a property of one prediction.

**Calibration gap**: The absolute difference between stated probability and observed frequency, computed over declared bins and aggregated by bin weight. It is the measure that certifies or suspends a signal for gating use.

**Discrimination**: The ability of a signal to rank failures above successes, measured independently of calibration. A signal can rank well and be badly calibrated, or be well calibrated and rank no better than chance.

**Selective prediction**: The regime in which a monitored process accepts a subset of cases and abstains on the remainder, characterised by coverage, the accepted fraction, and risk, the loss among accepted cases.

**Source class**: The provenance label attached to every signal, drawn from a closed set: same model, independent model, deterministic test, primary source, environment, or human. It is the input to the independence assessment.

**External signal**: A signal whose value could not have been produced by the object layer, because it originates in a deterministic check, a retrieved primary source, an environment response, an independent model family, or a human. Externality is a property of provenance, not of confidence.

**Correlated failure**: Agreement among signals sharing a common premise, source, or model, mistaken for independent confirmation.

**Monitoring verdict**: The typed record the monitor emits at a checkpoint, carrying measured signals, calibrated probabilities, threshold comparisons, an independence assessment, and a proposed but non-binding classification. It contains no instruction to the object layer.

**Signal certification**: The recorded status permitting a signal to gate an action, granted only after calibration on held-out data and revoked automatically on drift, model change, or prompt change.

**Bundle**: The versioned set of model, prompt, retrieval index, tool schema, calibrator, and threshold that a certification applies to. Certification transfers with the bundle and with nothing else.

### 1.2 The Monitor Layer and Its Boundary Against Control

**Separation is the guide's central constraint**: The monitor measures, the control layer changes, and no component does both. Fusing the two costs the system its ability to judge the work from outside: a component that can act on its own measurement acquires an interest in the measurement, and self-assessment becomes indistinguishable from self-justification. Where one model performs both roles, the monitoring verdict is still emitted as a separate typed record before any control decision reads it, and the two operations are logged as distinct events.

**Monitoring is not control**: The classic account carries information from the task process to a model of that process, while control changes the task process in response [1]. A monitoring specification that names corrective actions has annexed the control layer. A control specification that computes its own progress evidence has annexed the monitor. Both defects are detected by checking whether any single component both wrote a signal value and consumed it as authority.

**Confidence is a decision signal, not a truth certificate**: Competence is performance over a task distribution, confidence concerns one prediction, and calibration matches stated probabilities to observed frequencies. These three properties vary independently, and no one of them substitutes for another. A monitor that reports confidence and calls it competence has reported the wrong quantity.

**Introspection is not measurement**: A model asked how confident it is produces a number that is weakly related to its accuracy, and that number tends to rise with the fluency of the output rather than with the evidence behind it. Appropriately prompted models can estimate the probability that a proposed answer is correct and the probability that an answer is known, but the latter estimate generalised imperfectly to new tasks in the reported study [2], and evidence that models can predict properties of their own behaviour is intervention-dependent and does not license treating a self-report as direct introspection [3]. Stated reasons are likewise not causal reasons: biasing features can change an answer while disappearing from the rationale [24], and acknowledgment of influential hints was low in tested reasoning models [25]. The operational consequence is fixed: every signal admitted to the monitor must have a computable definition over recorded fields, and a self-report is admitted only as one uncalibrated feature pending certification.

**Boundary against neighbouring patterns**:

- **Verification** establishes whether a specific artifact satisfies a specific test. Monitoring decides which verifications are worth running and records what their results imply about the process as a whole.
- **Self-critique** evaluates a candidate against criteria and proposes revisions. Monitoring measures whether the critique carries independent information, and never adopts the critique's verdict as a signal value without a source class label.
- **Evaluation harness** scores a frozen dataset offline. Monitoring runs against live traffic, consumes the harness output as its calibration input, and returns drift evidence that reopens the harness.
- **Guardrail classification** blocks policy classes and injection attempts. Monitoring records guardrail results as one deterministic signal among several; a guardrail score never overrides a deterministic policy violation.
- **Control** selects among continuing, verifying, repairing, switching, branching, escalating, and stopping. Monitoring supplies the evidence for that selection and issues none of it.

### 1.3 The Execution Tier Partition

Monitoring divides across three execution tiers, and the division is load-bearing rather than advisory. A monitor whose arithmetic is performed by the model it observes has no independent measurement to offer.

**Deterministic tier**: Software, scripts, queries, schema validators, and APIs own every signal computation, every calibration arithmetic operation, every threshold evaluation, and the monitoring record itself. These require exactness, reproducibility, and auditability that inference cannot supply: two runs of the same calibration on the same frozen data must return identical numbers, and a risk-coverage curve must be reconstructible from the record years later. The deterministic tier rejects, rather than repairs, any signal that is malformed, out of declared range, missing its version fields, or produced under a bundle whose certification has lapsed.

**Model tier**: Inference owns only the judgements no deterministic signal covers: semantic equivalence between two differently worded answers, entailment between a claim and a retrieved passage where no deterministic matcher applies, classification of an open-vocabulary failure cause, and generation of a candidate confidence report against a named event. In every case the model tier proposes and never decides. Its outputs enter the record as typed values with a source class label, are subject to the same range and validity checks as any other signal, and acquire authority only after the deterministic tier has certified them through calibration.

**Hybrid tier**: The model proposes and software verifies, or software retrieves and the model adjudicates. Authority is fixed in advance and does not depend on the content of the disagreement: where a deterministic check and a model judgement conflict, the deterministic check holds, and the disagreement is recorded as a monitor event rather than resolved by re-prompting. Where two model judgements conflict and no deterministic check exists, neither wins; the case routes to human adjudication and the disagreement is recorded as an unresolved signal.

**Tier Ownership of Monitoring Artifacts**:

| Monitoring artifact | Owning tier | Deterministic tier rejects | Model tier may never decide alone |
| :-- | :-- | :-- | :-- |
| Process signal values | Deterministic | Values absent from the execution record | Any process signal value |
| Elicited confidence report | Hybrid | Unparsed, out-of-range, or unversioned fields | Whether the report may gate an action |
| Semantic equivalence clustering | Hybrid | Clusters lacking membership records | Cluster count reported as an agreement figure |
| Claim-to-evidence entailment | Hybrid | Entailment labels lacking a cited evidence identifier | Support status for a critical claim |
| Calibrator fitting and evaluation | Deterministic | Fitting and evaluation on the same examples | Any calibration parameter |
| Calibration and discrimination measures | Deterministic | Measures computed without declared bins and counts | Any reported measure |
| Threshold selection and evaluation | Deterministic | Thresholds chosen on the final evaluation split | Threshold values or their comparison outcome |
| Independence assessment | Hybrid | Signals lacking a source class label | Whether agreement counts as confirmation |
| Failure-cause classification | Model | Causes outside the closed vocabulary | Any consequent action |
| Monitoring record and verdict | Deterministic | Records lacking bundle identity fields | Verdict contents or their release |

**The monitor never changes the process**: No tier in this partition is permitted to issue a retry, a revision, a strategy change, or a tool call intended to improve the object layer's output. The monitor may call tools to obtain evidence about the output, which is a measurement, and may not call tools to alter it, which is control. Where a monitoring component is observed issuing a corrective instruction, the run halts and the component is re-scoped, because the measurement it produced afterward is no longer independent of the work it measured.

### 1.4 The Monitoring Gate: Conditions for Instrumentation and Suppression

Monitoring is not free, and an unusable measurement is worse than none because it consumes budget and invites reliance. Agents must run a cheap gate, bounded to 2 percent of the direct-execution budget, returning instrument, suppress, or a named lighter substitute.

**Instrumentation conditions**: Instrument where at least one of the following holds: the monitored decision selects among materially different actions; failures are costly or hard to reverse; labels arrive after deployment rather than at generation time; task difficulty varies across the input population; evidence can be missing, stale, or conflicting; tools can fail in ways the object layer cannot detect; or a bounded coverage-risk tradeoff is required by policy.

**Suppression conditions**: Suppress where a deterministic verifier decides correctness outright through a schema, type checker, unit test, solver, signature, constraint, or postcondition, and use the verifier. Suppress where authoritative retrieval plus claim entailment already establishes support. Suppress where one already-calibrated scalar and a binary action fit a stable population, and apply the threshold without a monitoring layer above it. Suppress for low-stakes reversible routine work where monitoring overhead exceeds expected harm.

**Rejection conditions**: Reject monitoring outright, rather than suppressing it pending later use, where no corrective action exists for the control layer to take, because a measurement that cannot change authority, evidence collection, or review adds ceremony without control. Reject it where no label source can define the observable event, where available calibration data is unrelated to the deployment population, or where the interface cannot communicate abstention honestly.

**Numeric gate rules**: Instrument only where at least 1 monitored decision names 2 or more permitted actions, and at least 1 signal with a computable definition is obtainable. Where no label source exists at any latency, suppress and record the missing label source, because no signal can be certified. Where estimated monitoring overhead exceeds 20 percent of the direct-execution budget and the task sits in the lowest risk tier, suppress and record the estimate for the next policy revision. Where the gate suppresses, name the substitute rather than proceeding unmonitored: a deterministic verifier, a retrieval-and-entailment check, or a fixed calibrated threshold.

***

## II. Operational Framework: Calibrated Monitoring Signals for an External Control Layer

The framework assumes the monitoring gate has returned instrument. Phases 1 through 5 run within a task episode, with Phases 2 through 5 repeating at every checkpoint the control layer declares. Phase 6 runs across episodes, consumes the accumulated monitoring record, and returns certification and threshold updates that Phases 3 and 5 read. No phase issues an instruction to the object layer.

### Phase 1: Monitorable Signal Declaration

**Objective**: Fix the monitored decision, its observable event, and the computable definition of every admitted signal before any signal value is read, so the monitor measures a declared target rather than whatever the object layer happens to emit.

#### Step 1.1: Define the Monitored Decision and Its Observable Event

**Required Actions**:

- State the monitored decision as 2 or more materially different actions the control layer is permitted to take, naming each explicitly.
- State the observable event the monitor predicts, such as answer correctness, claim support against a named corpus, tool completion, or rubric passage, and bind it to exactly 1 population.
- Name the label source that will determine whether the event occurred, together with its expected latency, its cost per label, and its known error rate.
- Record the risk tier, the maximum acceptable risk among accepted cases, the target coverage, and the latency and cost limits within which monitoring must operate.
- Halt and route to task redesign or human review where the event cannot be operationalised, rather than substituting a confidence number for a missing definition.

**Required Outputs**:

- A monitored decision record naming every permitted control action.
- An observable event definition bound to a named population and a named label source.
- A risk envelope record carrying risk tier, maximum accepted risk, target coverage, latency limit, and cost limit.

**Quality Checkpoints**:

- The observable event can be labelled after the fact by the named source; an unlabelable event halts instrumentation under Section 1.4.
- The monitored decision names at least 2 permitted actions; a single permitted action means the monitor has no decision to inform.
- Every element of the risk envelope carries a number; an unbounded element halts the phase.

***

#### Step 1.2: Declare the Process Signal Set With Computable Definitions

**Required Actions**:

- Admit only signals expressible as a function over fields already present in the execution record, so two independent implementations reading that record return the same value.
- Declare, for each signal, its target event, direction, valid range, source, bundle version, and the recorded fields it consumes.
- Reject any candidate signal whose definition requires the object layer to report on its own state, since such a signal measures the report rather than the process.
- Declare the checkpoint spacing at which each signal is recomputed, matching the horizon the control layer has set rather than a monitor-chosen interval.
- Record the handling rule for a missing input field: the signal is marked unavailable with a named reason, never imputed and never defaulted to a neutral value.

**Process Signal Definitions**:

| Process signal | Computable definition | Recorded inputs consumed | Direction and range |
| :-- | :-- | :-- | :-- |
| Subgoal progress | Fraction of declared subgoals whose acceptance test returned pass at this checkpoint, minus the same fraction at the previous checkpoint | Declared subgoal list, per-subgoal test verdicts, checkpoint index | Higher is better, minus 1.0 to 1.0 |
| Uncertainty reduction | Open questions closed since the previous checkpoint divided by open questions outstanding at that checkpoint, reported beside the change in unsupported-claim marker count | Open question register, unsupported-claim markers, checkpoint index | Higher is better, minus 1.0 to 1.0 |
| Repetition count | Occurrences in the run of the current state signature, where the signature is a hash over active subgoal, tool name, normalised argument set, and error class | Tool invocation log, error class vocabulary, subgoal identifier | Lower is better, 1 upward |
| Cycle length | Checkpoint distance between the two most recent occurrences of the current state signature, reported as unavailable where the signature has occurred once | State signature index | Longer is better, 1 upward |
| Evidence accumulation rate | Distinct evidence identifiers newly cited since the previous checkpoint, deduplicated by document and chunk identifier, divided by cost consumed over the same interval | Citation records, cost ledger | Higher is better, 0 upward |
| Budget consumption ratio | Consumed divided by planned for each declared budget dimension at this checkpoint | Budget ledger, planned consumption profile | Lower is better, 0 upward |
| Tool fault rate | Invocations failing schema validation, transport, deadline, or post-call plausibility, divided by invocations attempted over the last declared window | Per-invocation verdict records | Lower is better, 0.0 to 1.0 |

**Required Outputs**:

- A process signal register carrying the six declared attributes per entry.
- A computable definition statement per signal, naming the record fields it consumes.
- A missing-input handling rule per signal, naming the unavailability reason code.

**Quality Checkpoints**:

- Every admitted signal names the record fields it reads; a signal naming no fields is not computable and is removed before instrumentation.
- No admitted process signal depends on a model report about the object layer's internal state.
- Every signal carries a checkpoint spacing matching a control-declared horizon, so measurements are comparable across checkpoints.

***

#### Step 1.3: Declare the Estimator Signal Set by Access Level

**Required Actions**:

- Select the smallest estimator set that matches the available access level and the monitored decision, and preregister it before any value is read.
- Ask every elicited estimator a tightly specified question naming the target event and the validator it will be scored against, rather than an unbounded question about confidence.
- Keep the answerability estimate and the answer-correctness estimate as separate signals, since a model may know a topic and still produce a defective answer [2].
- Record the shared-model dependency wherever the same model both generates and evaluates, and pair the result with at least 1 signal of a different source class.
- Pin the sampling policy, equivalence model, entailment rule, clustering algorithm, and sample count for any multi-sample estimator, and treat clustering errors as estimator errors rather than as task errors.

**Estimator Signal Classes**:

| Estimator class | Access required | What it measures | Declared limitation carried from the source |
| :-- | :-- | :-- | :-- |
| Elicited answer-correctness probability | Prompting only | Probability that a proposed answer passes the named validator | Models tend to be overconfident and no elicitation method dominates across tasks [5] |
| Elicited answerability probability | Prompting only | Probability that an answer is knowable before one is committed | Calibration generalised imperfectly to new tasks in the reported study [2] |
| Sample agreement | Repeated sampling | Frequency of the leading cluster over normalised final answers [6] | Correlated samples can repeat one misconception; agreement is not calibrated correctness |
| Semantic entropy | Repeated sampling plus an equivalence model | Uncertainty over meaning-equivalent generation groups [7][8] | Costs multiple generations and does not fit a single-call path |
| Normalised sequence probability | Provider-returned token probabilities | Mean log probability per scored token, stratified by output length [9] | Measures the local next-token distribution, not factual correctness |
| Heterogeneous panel disagreement | 2 or more distinct model families | Epistemic disagreement across genuinely different members [10] | Multiple API aliases backed by one base model are not a panel |
| Conformal prediction set | A held-out calibration set | Set size and abstention policy at a target error level [13] | Validity relies on exchangeability, so drift can break coverage [14] |
| Claim support ratio | Retrieval plus entailment | Atomic claims supported by a cited source, over atomic claims asserted [26] | A document-level score can hide one critical unsupported claim |

**Required Outputs**:

- An estimator register naming each admitted estimator, its access requirement, and its pinned configuration.
- A separate answerability and answer-correctness signal pair where routing and acceptance are both monitored.
- A shared-model dependency record naming every estimator produced by the model that generated the output.

**Quality Checkpoints**:

- Every elicited estimator names its target event and validator in the elicitation itself; an unbounded confidence question is rejected before the value is parsed.
- No estimator is admitted whose access requirement the deployment cannot meet; unavailable estimators are recorded as unavailable rather than approximated by a different method.
- Estimators drawn from the generating model carry a shared-model dependency flag, and at least 1 estimator of a different source class accompanies them for any decision above the lowest risk tier.

***

### Phase 2: Instrumentation and Signal Computation

**Objective**: Produce an observation record complete enough for every declared signal to be computed deterministically from it, and compute those signals without permitting a malformed value into monitoring state.

#### Step 2.1: Establish the Observation Record

**Required Actions**:

- Emit an append-only record carrying run, checkpoint, signal, claim, and decision levels, with a run identifier, event identifier, parent event identifier, timestamp, and sequence number on every event.
- Record the full bundle identity on every event: model and endpoint revision, prompt version, parser version, sampling settings, retrieval index version, tool schema version, calibrator version, and threshold set version.
- Record per-claim provenance for factual output: claim identifier, span offsets, criticality, source requirement, cited document and chunk identifiers, source timestamps and content hashes, and entailment model and version.
- Store concise decision metadata and evidence references in place of private reasoning content, and hold raw prompts and outputs in access-controlled storage referenced by hash rather than inline in high-cardinality fields.
- Redact secrets and sensitive inputs, apply allowlist capture before export, and set a retention class per record level, since a record rich enough to support calibration is rich enough to leak the topics, documents, thresholds, and reviewer decisions it describes.

**Signal Record Template**:

```
RUN_ID:
EVENT_ID:
PARENT_EVENT_ID:
SEQUENCE_NUMBER:
CHECKPOINT_INDEX:
SIGNAL_ID:
SIGNAL_SCOPE:          RUN | CHECKPOINT | CLAIM
TARGET_EVENT:
METHOD_TYPE:           PROCESS | ELICITED | SAMPLED | PROVIDER | RETRIEVAL | DETERMINISTIC
SOURCE_CLASS:          SAME_MODEL | INDEPENDENT_MODEL | DETERMINISTIC_TEST |
                       PRIMARY_SOURCE | ENVIRONMENT | HUMAN
RAW_VALUE:
TRANSFORMED_VALUE:
DIRECTION:             HIGHER_IS_BETTER | LOWER_IS_BETTER
VALID_RANGE:
VALIDITY_FLAG:         VALID | MALFORMED | OUT_OF_RANGE | UNAVAILABLE | UNCERTIFIED
UNAVAILABILITY_REASON:
BUNDLE_ID:
CALIBRATOR_VERSION:
CALIBRATED_PROBABILITY:
CALIBRATION_DOMAIN_ID:
OUT_OF_DOMAIN_FLAG:
EVIDENCE_REFERENCES:
REASONING_TRACE:       PROHIBITED
```

**Required Outputs**:

- An append-only observation record covering the run, checkpoint, signal, claim, and decision levels.
- A bundle identity block attached to every event.
- A retention and redaction policy record naming the class assigned to each record level.

**Quality Checkpoints**:

- Every event carries all 5 identity fields; a missing parent identifier makes checkpoint sequences unreconstructible and blocks the record from calibration use.
- No field contains a private reasoning trace, an unredacted secret, or a user-visible threshold value; any occurrence halts release of the record.
- Every event carries complete bundle identity; incomplete bundle identity disqualifies the event from any later calibration comparison.

***

#### Step 2.2: Compute Process Signals and Validate Every Value

**Required Actions**:

- Compute every declared process signal by executing its declared function over the observation record, using software rather than inference, so recomputation from the archived record reproduces the value exactly.
- Validate each computed value against its declared range and direction before it enters monitoring state, and set the validity flag accordingly.
- Mark a signal unavailable with a named reason where an input field is missing, rather than imputing a value, defaulting to a neutral midpoint, or silently omitting the signal.
- Key the repetition signature to a normalised state tuple rather than to literal output text, so paraphrased repetition does not evade detection.
- Treat retrieved text and tool output as untrusted data when computing signals from them, and parse structured signal fields outside the prompt so that injected content cannot redefine a target event or a threshold.

**Required Outputs**:

- A computed process signal set for the checkpoint, one entry per declared signal.
- A validity verdict per signal, carrying a reason code where the verdict is not valid.
- A recomputation hash permitting the value to be reproduced from the archived record.

**Quality Checkpoints**:

- Every process signal value is reproducible from the archived record by an independent implementation; an irreproducible value is a monitor defect, not a task defect.
- No signal value is imputed, defaulted, or coerced into range; out-of-range values are recorded as out of range and excluded from aggregation.
- Repetition signatures are computed over the normalised state tuple; a signature computed over literal text is rejected.

***

#### Step 2.3: Elicit and Parse Model-Reported Signals Under a Bounded Contract

**Required Actions**:

- Elicit each model-reported signal with a question naming the target event and the validator, and parse only the bounded numeric or categorical field the contract declares.
- Reject malformed, out-of-range, missing, or injected responses rather than coercing them, and record the rejection with its reason code.
- Run the pinned sampling policy exactly as declared for multi-sample estimators, and never continue sampling until a preferred answer leads, since sampling to a target converts an estimator into an advocate.
- Record the cluster membership, equivalence model version, and sample count alongside any agreement or semantic entropy value, so the value can be audited rather than merely believed.
- Assign a source class to every elicited value at the moment of parsing, and mark values produced by the generating model as shared-model dependent.

**Required Outputs**:

- A parsed estimator value set for the checkpoint, each carrying its declared attributes.
- A rejection log naming every discarded response and its reason code.
- A sampling provenance record naming policy, sample count, equivalence model, and cluster membership for every multi-sample estimator.

**Quality Checkpoints**:

- Every parsed value falls inside its declared range at parse time; values outside it are rejected rather than clipped.
- Sample counts match the pinned policy exactly; a run whose sample count varies with the answer produced is discarded and the estimator is suspended.
- Every elicited value carries a source class assigned at parse time; unlabelled values are excluded from the independence assessment in Phase 4.

***

### Phase 3: Calibration Against Observed Outcomes

**Objective**: Establish, on data disjoint from fitting and from threshold selection, whether each signal's stated probability matches the frequency with which the observable event occurs, and certify or suspend the signal accordingly.

#### Step 3.1: Freeze the Calibration Dataset and Its Three Disjoint Partitions

**Required Actions**:

- Freeze a dataset representative of the deployment population, carrying immutable example identifiers, time windows, task and risk slices, adversarial cases, out-of-distribution cases, and authoritative labels.
- Partition it into 3 disjoint parts: a fitting partition for calibrator parameters, a threshold partition for operating point selection, and an untouched evaluation partition read exactly once per release.
- Run the exact production pipeline over the dataset, including the same retrieval index, tool schemas, prompts, and decoding settings, so the calibration population matches the deployment population.
- Keep labels out of model context at every stage, and record the sampling frame, inclusion weights, protected slices, labeler and rubric versions, and adjudication status per example.
- Record a contamination flag per example and exclude flagged examples from reported measures rather than from the dataset, so the exclusion remains auditable.

**Required Outputs**:

- A frozen dataset record carrying a version identifier, a content hash, and per-example identity.
- Three disjoint partition manifests naming every example identifier assigned to each.
- A pipeline execution record confirming the production bundle was used unmodified.

**Quality Checkpoints**:

- The three partitions share 0 example identifiers; any overlap invalidates every measure computed from them.
- Each slice intended for separate reporting carries at least 200 labelled examples in the evaluation partition; slices below that count are reported as provisional and may not support a certification.
- The dataset covers the adversarial and out-of-distribution cases the deployment expects; an uncovered case class is named as an untested condition rather than assumed benign.

***

#### Step 3.2: Fit the Calibrator and Compute Calibration and Discrimination Measures

**Required Actions**:

- Fit calibrator parameters only on the fitting partition, selecting temperature scaling where the underlying scores retain useful relative structure [15] and a logistic or regularised monotonic mapping where the input is an arbitrary scalar.
- Compute calibration and discrimination measures only on the untouched evaluation partition, and never fit and report on the same examples.
- Report expected calibration error in both equal-width and equal-mass forms with bin edges, bin counts, empty-bin handling, and weighting declared, since fixed-width binning can hide local error and rankings shift with measurement choices [16], and equal-mass bins carry lower estimator bias where samples are sparse [17].
- Publish a reliability diagram and per-bin counts beside every reported calibration figure, and report proper scoring rules alongside it, since a signal can improve one measure while degrading sharpness or discrimination.
- Compute selective-prediction behaviour by sorting cases from most to least confident and evaluating each accepted prefix, reporting the production operating point explicitly rather than an aggregate area alone [18].

**Calibration and Discrimination Measures**:

| Measure | Question it answers | Computation from the record | Mandatory reporting companions |
| :-- | :-- | :-- | :-- |
| Reliability diagram | Does stated probability track observed frequency across the range | Plot mean calibrated probability against empirical success per bin | Per-bin counts and bin edges |
| Expected calibration error | How large is the average gap, weighted by bin population | Absolute gap between mean probability and empirical success per bin, weighted by bin count | Equal-width and equal-mass forms, both reported |
| Brier score | How good is the probability overall, calibration and resolution together | Mean squared difference between calibrated probability and binary outcome | Reported beside expected calibration error, never instead of it |
| Log loss | How severely are confident errors penalised | Mean negative log of the probability assigned to the observed outcome | The declared numerical floor applied in place of a zero probability |
| Failure-ranking area | Does the signal rank failures above successes | Area under the receiver operating characteristic with incorrect as the positive class and uncertainty as the score | Explicit statement of positive class and score direction |
| Risk-coverage curve | What loss is accepted at each acceptance rate | Loss among accepted cases for each confidence-sorted prefix | Coverage at maximum tolerated risk and risk at operational coverage |
| Area under the risk-coverage curve | How does selective behaviour compare across candidates | Discrete average risk across the coverage points | Base accuracy of each compared predictor |
| Realised conformal coverage | Did the set-valued procedure achieve its nominal level | Fraction of evaluation cases whose set contained an acceptable answer, with mean set size | The nominal level stated as conditional on exchangeability [14] |

**Required Outputs**:

- A fitted calibrator carrying its parameters, its fitting partition manifest, and a version identifier.
- A measure report covering calibration, proper scoring, discrimination, and selective behaviour, computed once on the untouched partition.
- A per-slice measure block covering every risk tier, task family, and protected slice declared for separate reporting.

**Quality Checkpoints**:

- Calibrator parameters were fitted on the fitting partition only; parameters touched by evaluation data invalidate the certification.
- Every reported calibration figure is accompanied by a reliability diagram, per-bin counts, and at least 1 proper scoring rule; a bare error figure is rejected.
- Aggregate gains that worsen risk in any critical slice are rejected; slice regression outranks aggregate improvement.

***

#### Step 3.3: Certify or Suspend the Signal for Gating Use

**Required Actions**:

- Grant certification to a signal only where its calibration gap on the untouched partition is at or below 10 percentage points in every reported slice, and record the certification against the exact bundle it was measured on.
- Record provisional status where the gap exceeds 10 and remains at or below 20 percentage points in every slice, permitting the signal to gate only reversible actions in the lowest risk tier.
- Suspend the signal for all gating use where the calibration gap exceeds 20 percentage points in any slice, and route decisions in that slice to independent verification or human review until recalibration completes.
- Revoke certification automatically on any change to the model, quantization, provider snapshot, prompt, decoding settings, tool schema, retrieval index, or policy, since certification attaches to a bundle and never to a product name.
- Record the certification status, its measured gap, its bundle identity, its effective date, and its approving role in an immutable registry that the threshold evaluation in Phase 5 reads at decision time.

**Required Outputs**:

- A certification record per signal carrying status, measured gap per slice, bundle identity, effective date, and approver.
- A suspension list naming every signal and slice combination barred from gating use, with the recalibration owner named.
- A revocation rule record naming every bundle field whose change invalidates the certification.

**Quality Checkpoints**:

- No uncertified signal gates any action; an uncertified value may be recorded, reported, and shown to a reviewer, and may not be compared against an action threshold.
- Certification names the exact bundle measured; a certification transferred across model or prompt versions is void and its use is a monitor defect.
- Post-training and alignment changes are treated as calibration-invalidating, since accuracy can hold while calibration degrades [19].
- Every suspended signal has a named recalibration owner and a scheduled recalibration; a suspension with no owner escalates within 1 release cycle.

***

### Phase 4: Independence Assessment

**Objective**: Establish which signals carry information the object layer could not have produced, so that agreement among signals is counted as confirmation only where the agreeing signals could have disagreed.

#### Step 4.1: Classify Every Signal by Source Class

**Required Actions**:

- Assign every signal exactly 1 source class from the closed set: same model, independent model, deterministic test, primary source, environment, or human.
- Classify as genuinely external only those signals whose value could not have been produced by the object layer: deterministic validator and test results, primary sources retrieved with document, chunk, version, and hash provenance, environment responses and tool postconditions, judgements from a materially different model family, and human adjudications.
- Classify as internal every signal produced by the generating model, including its elicited confidence, its self-critique, its own answerability estimate, and any resampling of the same model at a different temperature.
- Record, for each externally classified signal, the specific mechanism that makes it external, so the classification can be audited rather than asserted.
- Order evidence by strength when several classes are present: deterministic validators first, retrieval and entailment checks second, specialised classifiers third, and model judges last.

**Required Outputs**:

- A source class label attached to every signal in the checkpoint's inventory.
- An externality justification per externally classified signal, naming its independence mechanism.
- An evidence ordering record placing each present signal in the declared strength order.

**Quality Checkpoints**:

- Every signal carries exactly 1 source class; unlabelled or multiply-labelled signals are excluded from the independence assessment.
- No signal produced by the generating model is classified as external, whatever its prompt, persona, temperature, or endpoint alias.
- A model panel is classified as external only where its members are materially different model families; aliases resolving to 1 base model are recorded as 1 internal signal.

***

#### Step 4.2: Test Agreement for Shared Models and Shared Premises

**Required Actions**:

- Count agreeing signals that share a model, a prompt lineage, a retrieval result, or an unverified premise once rather than once each.
- Test whether agreement survives removal of the shared premise, and record the result as convergence where it survives and as correlated failure where it does not.
- Control judge-specific biases before treating a judgement as evidence: randomise candidate ordering, normalise length, blind model identity, and include counter-sycophancy probes, since position, verbosity, self-enhancement, and limited-reasoning effects have been documented in judge evaluations [21], evaluators can favour their own generations even where humans see equal quality [22], and preference optimisation can encourage agreement with a stated belief in place of truthfulness [23].
- Record the shared-model dependency explicitly wherever generation and judging use the same model, separate their contexts and prompts, and never treat that pair as a verification.
- Treat unassisted self-correction as an uncertified signal rather than a verification, since models can fail to correct reasoning without external feedback and can degrade an initially correct answer [20].

**Required Outputs**:

- An independence verdict per observed agreement, classified as convergence or correlated failure.
- A deduplicated agreement count treating each shared model, prompt lineage, or premise as 1 source.
- A bias control record naming the ordering, length, blinding, and counter-sycophancy controls applied to every judgement admitted.

**Quality Checkpoints**:

- Agreement among signals sharing a model or premise is recorded as correlated failure, never as confirmation.
- Every admitted judgement carries its bias control record; a judgement without one is recorded as uncontrolled and excluded from agreement counting.
- Sample agreement is never reported as a calibrated probability; it is reported as an agreement frequency with its sample count and clustering provenance attached.

***

#### Step 4.3: Enforce the External Signal Requirement for Consequential Decisions

**Required Actions**:

- Require at least 1 externally classified signal before any monitoring verdict may support a consequential decision, defined as an irreversible action, an action in the highest risk tier, or the release of an unverified critical claim.
- Decompose factual output into atomic claims and record, per claim, its criticality, source requirement, cited evidence identifiers, and support status, so a document-level support figure cannot conceal 1 unsupported critical claim [26].
- Measure retrieval grounding across passage relevance, answer faithfulness, citation entailment, currency, and authority rather than treating retrieval presence as support [27][28].
- Where no knowledge source is available, admit sampling-based contradiction checks as a warning signal only, and record that consistency is not truth [29].
- Emit a blocked verdict, rather than a low-confidence verdict, where a consequential decision is pending and no external signal is obtainable, and route the case to human adjudication.

**Required Outputs**:

- An external signal presence record per consequential decision, naming the signal and its class.
- A claim-level support ledger covering every critical claim with its evidence identifiers and support status.
- A blocked verdict record for every consequential decision lacking an external signal.

**Quality Checkpoints**:

- At least 1 external signal accompanies every consequential decision; its absence blocks the decision and routes to human adjudication rather than lowering the threshold.
- Every critical claim carries an explicit support status; an unmarked critical claim is treated as unsupported.
- A high model score never overrides a failed deterministic check; such a case is recorded as a verifier conflict and escalated.

***

### Phase 5: Threshold Evaluation and Handoff to Control

**Objective**: Convert certified signals into a typed monitoring verdict through thresholds selected on held-out data, and hand that verdict to the control layer without issuing any instruction to the object layer.

#### Step 5.1: Select Operating Thresholds on Held-Out Data

**Required Actions**:

- Select every operating threshold on the threshold partition alone, never on the untouched evaluation partition and never after an incident has been observed.
- Declare the cost of wrong automation, of abstention, of model escalation, of human escalation, of latency, and of tool consumption before selecting, so selection minimises expected cost rather than maximising a single metric.
- Constrain the selection by maximum critical risk, minimum coverage, reviewer capacity, and latency limit, and record which constraint binds at the chosen point.
- Permit slice-specific thresholds only where the slice carries at least 200 labelled examples and a named approver, and otherwise apply the population threshold to that slice.
- Hold every threshold server-side, exclude it from user-visible traces and from any content the model can read, and version it as part of the bundle.

**Required Outputs**:

- A threshold set carrying accept, recover, escalate, and abstain boundaries per risk tier.
- A cost matrix record with a version identifier and a named approver.
- A binding constraint record naming which constraint determined the chosen operating point.

**Quality Checkpoints**:

- No threshold was selected on the untouched evaluation partition; a threshold so selected invalidates the release measures.
- Every slice-specific threshold carries at least 200 labelled examples and a named approver; slices below that count inherit the population threshold.
- No threshold value appears in a prompt, a user-visible trace, or a model-readable field, since a visible threshold is a threshold that can be gamed.

***

#### Step 5.2: Evaluate Thresholds and Emit the Monitoring Verdict

**Required Actions**:

- Evaluate certified calibrated probabilities against the declared thresholds deterministically, and record the comparison inputs and outcome rather than the outcome alone.
- Emit exactly 1 verdict class per checkpoint from the closed vocabulary, resolving ties toward the safer class.
- Attach the failure-cause classification proposed by the model tier from a closed vocabulary covering ambiguity, missing evidence, retrieval failure, model uncertainty, verifier conflict, tool failure, policy uncertainty, suspected shift, and budget exhaustion, and mark it as proposed rather than determined.
- Preserve both the calibrated score and the threshold in the record, since a boolean alone cannot reconstruct a risk-coverage curve after the fact.
- Express any user-facing uncertainty as a category with operational meaning rather than a decorative percentage, name the event and population where a probability is shown, and never present a nominal conformal level as an unconditional guarantee after a distribution change.

**Monitoring Verdict Classes**:

| Verdict class | Triggering condition | Signals that must be present | What the monitor must not do |
| :-- | :-- | :-- | :-- |
| Within tolerance | Calibrated probability at or above the accept threshold and every hard check passed | 1 certified estimator and every declared deterministic check | Authorise release itself |
| Uncertain, evidence gap | Claim support ratio below its threshold or a required source unavailable | Claim-level support ledger | Issue a retrieval instruction |
| Uncertain, model | Calibrated probability between accept and abstain thresholds with all evidence present | 1 certified estimator | Resample until the score improves |
| Verifier conflict | A deterministic check failed while an estimator remains above the accept threshold | Deterministic check result and estimator value | Resolve the conflict by re-prompting |
| Out of domain | Novelty detector fires or the case falls outside the calibration domain | Calibration domain identifier and out-of-domain flag | Stretch an in-domain probability over the case |
| Blocked, no external signal | A consequential decision is pending with 0 externally classified signals | Source class inventory | Substitute an internal signal |
| Blocked, uncertified signal | The only available estimator is suspended or provisional for this slice | Certification registry lookup | Compare an uncertified value to a threshold |
| Budget pressure | A budget dimension is exhausted or projected to exhaust before completion | Budget consumption ratio | Extend or reallocate any budget |

**Required Outputs**:

- One monitoring verdict record per checkpoint carrying the verdict class, the comparison inputs, and the threshold values applied.
- A proposed failure-cause label drawn from the closed vocabulary, marked as proposed.
- A user-facing uncertainty statement expressed at the granularity validation supports.

**Quality Checkpoints**:

- Exactly 1 verdict class is recorded per checkpoint; 0 or 2 or more is a monitor defect that halts the checkpoint.
- Both the calibrated score and the applied threshold are preserved; a record carrying only the comparison outcome is rejected.
- No user-facing uncertainty statement exceeds the granularity the evaluation partition validated; an unsupported percentage is removed rather than rounded.

***

#### Step 5.3: Hand Off to the Control Layer Without Changing the Process

**Required Actions**:

- Transmit the verdict as a typed record to the control layer and take no further action on the object layer, since selecting a corrective action is the control layer's role.
- Exclude every imperative from the verdict: it may carry measurements, classifications, and evidence references, and may not carry a retry, revision, tool call, strategy change, or threshold adjustment.
- Record the control transition the control layer subsequently issued, so monitor quality can later be measured against what the verdict actually influenced.
- Preserve the verdict unchanged after transmission; where new evidence arrives, emit a new verdict at the next checkpoint rather than amending the previous one.
- Halt the run and re-scope the component where any monitoring component is observed issuing a corrective instruction, since measurements taken after that point are no longer independent of the work measured.

**Required Outputs**:

- A transmitted verdict record with an immutability marker and a transmission timestamp.
- A linked control transition record naming the transition the control layer issued and its reason code.
- A boundary violation log recording any instance of a monitoring component instructing the object layer.

**Quality Checkpoints**:

- The verdict contains 0 imperatives; any corrective instruction in a verdict is a layer boundary violation that halts the run.
- Every verdict is linked to the control transition that followed it, or explicitly marked as not consumed.
- No verdict is amended after transmission; amendment is a defect, and a superseding verdict is issued instead.

***

### Phase 6: Monitor-Quality Measurement and Recalibration

**Objective**: Measure whether the monitor still discriminates and remains calibrated on live traffic, and trigger recalibration on observed evidence rather than on a calendar.

#### Step 6.1: Compute the Monitor-Quality Metric Set From the Record

**Required Actions**:

- Compute calibration, proper scoring, and discrimination measures from the deployment record using the same declared bins, floors, and positive-class conventions used at certification, so live and offline figures are comparable.
- Compute selective behaviour from the record by sorting accepted cases by release confidence, and report coverage at maximum tolerated risk and risk at operational coverage beside any aggregate area.
- Compute abstention precision as incorrect predictions among abstentions divided by all labelled abstentions, and abstention recall as incorrect predictions among abstentions divided by all incorrect predictions that would otherwise have been eligible.
- Compute escalation yield as escalations that corrected an upstream error or produced a preregistered material improvement divided by completed escalations, reporting queue time, incremental cost, and residual error separately.
- Report unnecessary-abstention rate, critical-error escape rate, and monitoring overhead as a share of total run cost, with bootstrap intervals and per-slice breakdowns rather than pooled figures.

**Required Outputs**:

- A live calibration and discrimination block computed under the certification conventions.
- A selective behaviour block covering coverage, risk, abstention precision, abstention recall, and unnecessary-abstention rate.
- An operational block covering escalation yield, critical-error escape rate, monitoring overhead, and per-slice intervals.

**Quality Checkpoints**:

- Live measures use the certification conventions exactly; a changed bin count or positive class makes the comparison meaningless and the report is rejected.
- No measure is reported pooled where a slice breakdown was declared; a pooled figure fails the checkpoint.
- Every reported figure carries its sample count and interval; figures below the declared minimum sample rule are marked provisional and excluded from promotion decisions.

***

#### Step 6.2: Detect Drift and Trigger Recalibration

**Required Actions**:

- Monitor input mix, language, task family, corpus and index versions, model revision, calibrated score distributions, agreement, semantic entropy, claim support, abstention rate, escalation rate, tool failures, latency, cost, and delayed outcomes against launch and recent stable references.
- Compare distributions with divergence statistics for binned features and distance statistics for continuous scores, treat population stability index as a coarse dashboard indicator only, and pair every statistic with sample counts and uncertainty intervals.
- Fire an investigation trigger on any unannounced model revision, any prompt, policy, index, or tool-schema change, any feature drift beyond its validated control limit, any calibration, proper-scoring, discrimination, coverage, or critical-error breach once enough labels have accrued, any conformal undercoverage, any protected-slice regression, or any cluster of confidently wrong incidents.
- On trigger, freeze automatic threshold updates, attach the affected bundle version, and enter a named safe mode: preserve the previous route where compatible, raise the abstention rate, narrow the scope, require independent verification, or route the affected risk tier to human review.
- Set no universal drift threshold across features; derive each control limit from the feature's own validated variation and alert only after the declared minimum sample rule or a critical incident trigger, so small-window noise does not cause threshold thrashing.

**Required Outputs**:

- A drift statistic block per monitored feature with its reference window, control limit, and sample count.
- A trigger record naming the fired condition, the affected bundle, and the timestamp.
- A safe mode declaration naming the mode entered and the decisions it re-routes.

**Quality Checkpoints**:

- Every drift alert names its minimum sample rule and satisfies it; alerts below the rule are recorded as observations, not triggers.
- Automatic threshold updates are frozen on trigger; a threshold changed after a trigger without approval is a control-plane defect.
- Automatic recalibration is attempted at most 1 time per trigger; a second failure routes to human review rather than a further attempt.

***

#### Step 6.3: Re-Certify the Bundle and Promote or Roll Back

**Required Actions**:

- Assemble a recent labelled recalibration window while preserving a future holdout, and repeat the fitting, threshold selection, and single evaluation sequence of Phase 3 on the new bundle.
- Shadow the candidate bundle against production traffic without granting it authority, and require the preregistered acceptance bounds together with no material safety regression before promotion.
- Promote the model, calibrator, threshold, and policy bundle atomically, record its effective time, and retain the previous bundle as a rollback target.
- Cap the recalibration effort at 3 fit-and-evaluate rounds per release, and reject the candidate rather than continuing where the cap is reached.
- Retain scheduled periodic review as a backstop only, and never as a substitute for the event-driven triggers in Step 6.2.

**Required Outputs**:

- A recalibration window manifest with a preserved future holdout.
- A shadow evaluation report comparing candidate and incumbent bundles on every preregistered bound.
- An atomic promotion record naming the bundle, its effective time, its approver, and its retained rollback target.

**Quality Checkpoints**:

- The candidate was shadowed without authority before promotion; a candidate promoted directly from offline measures fails the checkpoint.
- Promotion is atomic across model, calibrator, threshold, and policy; a partially promoted bundle is rolled back in full.
- No more than 3 fit-and-evaluate rounds inform a release, and no round tuned on the untouched evaluation split; a further release requires a newly versioned split.
- A bundle remaining in degraded safe mode after recalibration is reported as such rather than promoted with a warning attached.

***

## III. Implementation Guidance for AI Agents

AI agents operating a monitor layer must follow systematic protocols ensuring that every signal is computable, every gating probability is certified, every agreement is tested for independence, and no monitoring component alters the process it measures. The following guidance translates the monitoring procedure into agent-executable instruction.

### A. Structured Execution Protocol

**Monitor Plane Components**:

1. **Declaration Agent**: Owns the monitored decision, the observable event, the label source, and the signal register. It admits a signal only against a computable definition and may refuse instrumentation at the gate.
2. **Instrumentation Service**: Deterministic software that writes the observation record and computes every process signal. It never calls a model, never imputes a missing input, and holds authority over every process signal value.
3. **Estimator Agent**: Issues bounded elicitations, runs pinned sampling policies, and proposes semantic equivalence, entailment, and failure-cause labels. It proposes and never decides, and every output it produces carries a source class assigned by the Instrumentation Service.
4. **Calibration Service**: Deterministic software that owns partition manifests, calibrator fitting, measure computation, certification status, and the certification registry. It alone may certify, suspend, or revoke a signal.
5. **Independence Auditor**: Assigns source classes, deduplicates agreement across shared models and premises, and issues the independence verdict. It may block a consequential decision for want of an external signal and may not select what happens instead.
6. **Verdict Service**: Deterministic software that evaluates thresholds, emits exactly 1 verdict class, transmits the verdict to the control layer, and records the transition that followed. It rejects any verdict containing an imperative.

**Monitoring Disclosure Boundary**: The instrumentation protocol permits decision metadata and prohibits hidden reasoning content. This is a hard constraint applying to every component.

- Log signal values, source classes, calibrated probabilities, threshold comparisons, verdict classes, evidence references, and bundle identity.
- Do not require, request, or persist private chain-of-thought from any model or component; the monitor requires observable outcomes and concise decision records, not internal transcripts.
- Do not place threshold values, cost matrices, or security-relevant parameters in any user-visible trace or model-readable field, since a visible threshold can be targeted.
- Do not log credentials, authentication tokens, unrestricted personal data, or unredacted retrieved documents by default; apply allowlist capture, field-level redaction, tenant isolation, and retention by risk class before export.
- Where a component cannot justify a value without exposing hidden reasoning, record the value as unjustified and route it to human adjudication rather than relaxing the boundary.

**Workflow Execution Pattern**:

```
STATE: Checkpoint_Monitoring
INPUTS:
  1. Observation record slice since the previous checkpoint
  2. Signal register and estimator register from Phase 1
  3. Certification registry entries for the active bundle
ACTIONS:
  1. Compute every declared process signal from the record
  2. Elicit and parse every declared estimator under its bounded contract
  3. Assign a source class to every signal and deduplicate agreement
  4. Apply the pinned calibrator to every certified estimator
  5. Evaluate thresholds and emit exactly one verdict class
VALIDATION:
  - every_signal_has_source_class == TRUE
  - gating_signals_all_certified == TRUE
  - calibration_gap_for_active_slice <= 0.10
  - external_signal_present == TRUE IF decision_is_consequential
  - verdict_class_count == 1
  - verdict_contains_imperative == FALSE
  - reasoning_trace_persisted == FALSE
TRANSITIONS:
  IF all_validations_pass THEN next_state = Transmit_Verdict_To_Control
  IF gating_signals_all_certified == FALSE
     THEN next_state = Emit_Blocked_Uncertified_Signal
  IF external_signal_present == FALSE AND decision_is_consequential
     THEN next_state = Emit_Blocked_No_External_Signal
  IF validation_failed THEN next_state = Monitor_Error_Handling
```

**Two-Phase Action Pattern**: Emit the computed signal set, the certification lookups, and the intended verdict class without transmitting them; confirm the set against the validation block while no decision has been influenced; transmit only after validation passes, recording the verdict and its bundle identity in the same operation.

**Approval Gate**: Human authorisation is required before promoting any calibrator, threshold set, or bundle to production; before granting certification to a signal whose measured calibration gap exceeds 10 percentage points in any slice; before applying a slice-specific threshold; before relaxing the disclosure boundary; and before any consequential decision proceeds with 0 externally classified signals. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the signal register, certification registry, and threshold set in durable state outside working context, since certification must be readable at every checkpoint and may outlive a context window.
- Stream the observation record to durable storage as it is written rather than accumulating it in context, and read back only the slice each signal's definition consumes.
- Summarise superseded checkpoint records into signal values and evidence references once computed, retaining the references and discarding the payloads.
- Count monitoring context consumption toward monitoring overhead rather than treating it as free, and compare it against the 20 percent gate bound in Section 1.4.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Declaration Integrity (After Phase 1)**

- **Automated Check**: The monitored decision names at least 2 permitted actions; the observable event names a label source; every admitted signal names the record fields its definition consumes; every element of the risk envelope carries a number.
- **Agent Action on Pass**: Proceed to instrumentation.
- **Agent Action on Failure**: Halt and return the undeclared element; no signal is computed against an incomplete declaration.
- **Human Review Trigger**: No label source exists at any latency, or the observable event resists operationalisation.

**Checkpoint 2: Record Completeness (After Phase 2)**

- **Automated Check**: Every event carries all 5 identity fields and complete bundle identity; every computed value is reproducible from the archived record; no value was imputed or clipped; no reasoning trace, secret, or threshold value was persisted.
- **Agent Action on Pass**: Proceed to calibration lookup and evaluation.
- **Agent Action on Failure**: Mark the affected signals unavailable with reason codes and continue with the remainder; do not substitute values.
- **Human Review Trigger**: More than 20 percent of declared signals unavailable at a checkpoint, or any disclosure breach.

**Checkpoint 3: Certification Validity (After Phase 3)**

- **Automated Check**: Partitions share 0 example identifiers; calibrator parameters were fitted on the fitting partition only; every reported calibration figure carries a reliability diagram, per-bin counts, and a proper scoring rule; the certification names the active bundle.
- **Agent Action on Pass**: Permit certified signals to gate actions at their recorded status.
- **Agent Action on Failure**: Suspend the affected signal for gating use and record the failing condition.
- **Human Review Trigger**: A measured calibration gap above 10 percentage points in any slice, or a slice carrying fewer than 200 labelled evaluation examples.

**Checkpoint 4: Independence Adequacy (After Phase 4)**

- **Automated Check**: Every signal carries exactly 1 source class; agreeing signals sharing a model or premise are counted once; every admitted judgement carries its bias control record; at least 1 external signal accompanies every consequential decision.
- **Agent Action on Pass**: Proceed to threshold evaluation.
- **Agent Action on Failure**: Emit a blocked verdict naming the missing external signal or the uncontrolled judgement.
- **Human Review Trigger**: No external signal obtainable for a pending consequential decision, or a critical claim whose support status cannot be determined.

**Checkpoint 5: Verdict Validity (After Phase 5)**

- **Automated Check**: Exactly 1 verdict class per checkpoint; both score and threshold preserved; no threshold selected on the untouched partition; the verdict contains 0 imperatives.
- **Agent Action on Pass**: Transmit the verdict and record the control transition that followed.
- **Agent Action on Failure**: Halt the checkpoint; an invalid verdict is never transmitted with a warning attached.
- **Human Review Trigger**: Any verdict containing a corrective instruction, or any threshold value found in a user-visible or model-readable field.

**Checkpoint 6: Monitor Quality and Drift (After Phase 6)**

- **Automated Check**: Live measures use the certification conventions; every reported figure carries sample count and interval; drift alerts satisfy their minimum sample rules; promotion was preceded by shadow evaluation and is atomic across the bundle.
- **Agent Action on Pass**: Release the monitor-quality report and permit promotion of the bundle.
- **Agent Action on Failure**: Withhold promotion, retain the incumbent bundle, and name the missing evidence.
- **Human Review Trigger**: A second recalibration failure against one trigger, a protected-slice regression, or a cluster of confidently wrong incidents.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
BUNDLE_ID:
VALIDATION_CRITERIA:
MEASURED_VALUE:
SAMPLE_COUNT:
PASS_CONDITION:
PASS_ACTION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_COMPONENT:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Uncertified Confidence Used as a Gate**

- **Symptoms**: A threshold comparison references a signal with no certification registry entry; a certification names a bundle other than the active one; confidence rises with output fluency while measured accuracy is flat.
- **Diagnostic Steps**: Look up the certification registry for the exact active bundle, recompute the calibration gap for the affected slice, and confirm whether the fitting and evaluation partitions were disjoint.
- **Resolution Protocol**: Option A, emit a blocked verdict for uncertified signal and route the decision to independent verification. Option B, demote the signal to reporting-only status and gate on a certified deterministic check instead. Option C, run the Phase 3 sequence on a fresh labelled window and re-certify before any further gating.
- **Escalation Trigger**: Any gating action taken on an uncertified signal escalates immediately; this class is never resolved by retrying the comparison.

**Error Type 2: Correlated Confirmation**

- **Symptoms**: Several signals agree while citing one unverified premise; a panel resolves to one base model; a generator and its judge share a prompt lineage.
- **Diagnostic Steps**: Trace every agreeing signal to its source class and premise set, and determine whether agreement survives removal of the shared premise.
- **Resolution Protocol**: Option A, obtain a deterministic check or a primary source with full provenance. Option B, replace one panel member with a materially different model family. Option C, record the conclusion with an explicit unsupported marker and reduce the verdict to uncertain.
- **Escalation Trigger**: A consequential decision resting on agreement that fails the independence test escalates immediately; this class is never resolved by drawing additional samples.

**Error Type 3: Silent Signal Substitution**

- **Symptoms**: A signal reports a plausible value where its input field is absent; unavailability reason codes are missing from the record; recomputation from the archive returns a different value.
- **Diagnostic Steps**: Replay the signal definition against the archived record slice, compare the replayed value against the logged value, and locate the imputation or default in the computation path.
- **Resolution Protocol**: Option A, restore the unavailability path so the signal reports unavailable with a reason code. Option B, remove the signal from the register until its inputs are reliably recorded. Option C, add the missing input field to the observation record and re-certify the signal against it.
- **Escalation Trigger**: Any imputed value found in a record used for calibration invalidates that calibration and escalates to the Calibration Service owner.

**Error Type 4: Calibration Drift and Out-of-Domain Collapse**

- **Symptoms**: Calibration gap rises across releases; conformal sets undercover their nominal level; novelty rates climb; confidently wrong incidents cluster in one slice.
- **Diagnostic Steps**: Recompute measures segmented by task family, risk tier, model version, and protected slice, and determine whether the degradation is confined to one segment or spans the population.
- **Resolution Protocol**: Option A, enter a named safe mode raising abstention or requiring verification in the affected segment. Option B, suspend certification in that segment and route its decisions to human review. Option C, run the recalibration sequence in Step 6.3 on a recent labelled window with a preserved future holdout.
- **Escalation Trigger**: A calibration gap above 20 percentage points in any slice suspends gating there; a second recalibration failure against one trigger routes to human review rather than a further automatic attempt.

**Error Type 5: Monitor Boundary Violation**

- **Symptoms**: A verdict carries an imperative; a monitoring component issues a retry or a revision; a signal value changes after transmission; the same component both wrote and consumed a value as authority.
- **Diagnostic Steps**: Trace the instruction to its emitting component, and determine whether the component holds a monitoring role in the plane inventory.
- **Resolution Protocol**: Option A, strip the imperative and reissue the verdict as measurement only. Option B, re-scope the component to a single role and move the corrective capability to the control layer. Option C, discard every measurement the component produced after the violation, since it is no longer independent of the work measured.
- **Escalation Trigger**: Any boundary violation halts the run; measurements taken after a violation are never rehabilitated by later validation.

**Error Type 6: Confidence Gaming and Signal Injection**

- **Symptoms**: Retrieved content or tool output contains text redefining a target event, a threshold, or a validator; elicited confidence shifts systematically with content the object layer controls; abnormal reasoning-token share or repeated decoy subproblems appear in the record [30].
- **Diagnostic Steps**: Compare signal values on the same inputs with and without the untrusted content, and confirm whether structured signal fields were parsed outside the prompt.
- **Resolution Protocol**: Option A, move signal parsing entirely outside the prompt and re-run the checkpoint. Option B, quarantine the injecting source and recompute claim support without it. Option C, raise abstention in the affected slice and route decisions to human review pending a control review.
- **Escalation Trigger**: Any successful redefinition of a target event or threshold by untrusted content routes to the incident path immediately; retrieval and fine-tuning do not remove this risk on their own [31].

**Troubleshooting Decision Tree**:

```
MONITORING CHECKPOINT FAILS VALIDATION
├─ CERTIFICATION DEFECT
│   ├─ No registry entry for active bundle → Emit blocked, uncertified signal
│   ├─ Gap above 10 points in a slice → Demote to provisional; gate reversible only
│   └─ Gap above 20 points in a slice → Suspend gating; route slice to human review
├─ INDEPENDENCE DEFECT
│   ├─ Agreement shares a model or premise → Record correlated failure; obtain external check
│   ├─ No external signal for consequential decision → Emit blocked; escalate
│   └─ Judgement lacks bias controls → Exclude from agreement count; re-run controlled
├─ RECORD DEFECT
│   ├─ Value not reproducible from archive → Mark unavailable; repair the definition
│   ├─ Imputed or clipped value found → Invalidate dependent calibration; escalate
│   └─ Reasoning trace or secret persisted → HALT release; purge and re-instrument
├─ BOUNDARY DEFECT
│   ├─ Verdict carries an imperative → HALT; reissue as measurement only
│   └─ Monitor instructed the object layer → Discard subsequent measurements; re-scope
└─ DRIFT DEFECT
    ├─ Control limit breached with sample rule met → Freeze thresholds; enter safe mode
    └─ Second recalibration failure → Route to human review; retain incumbent bundle
```

### D. Performance Metrics and Continuous Recalibration

**Calibration and Discrimination Metrics**:

- **Calibration gap**: Stated minus observed success frequency, segmented by task family, risk tier, model version, and protected slice (target: no more than 10 percentage points per slice; above 20 suspends gating in that slice).
- **Proper score improvement**: Brier score and log loss of the calibrated signal against the uncalibrated baseline on the same evaluation split (target: improvement on both, with sharpness reported alongside).
- **Failure-ranking area**: Area under the receiver operating characteristic with incorrect as the positive class (target: at least 0.70; below 0.60 the signal ranks no better than a coin and is removed from the register).
- **Realised conformal coverage**: Fraction of evaluation cases whose set contained an acceptable answer (target: within 3 percentage points of nominal; undercoverage fires a drift trigger).

**Selective Behaviour Metrics**:

- **Coverage at maximum tolerated risk**: Accepted fraction at the declared risk ceiling (target: at or above the coverage declared in Step 1.1).
- **Abstention precision**: Abstentions later adjudicated as correct withholdings (target: at least 90 percent).
- **Abstention recall**: Incorrect predictions captured by abstention over all incorrect predictions otherwise eligible (target: at least 60 percent).
- **Unnecessary-abstention rate**: Abstentions whose withheld answer was later adjudicated correct (target: no more than 10 percent).
- **Critical-error escape rate**: Accepted cases carrying an unsupported critical claim or a failed hard check (target: no more than 1 percent in the highest risk tier).
- **Escalation yield**: Escalations that corrected an upstream error or produced a preregistered material improvement (target: at least 50 percent; below 30 percent indicates the escalation threshold is set too low).

**Monitor Operations Metrics**:

- **Certification currency**: Gating signals certified against the active bundle (target: 100 percent; any shortfall is a gating defect).
- **Signal availability**: Declared signals returning a valid value per checkpoint (target: at least 95 percent).
- **Record reproducibility**: Process signal values reproducible from the archived record by an independent implementation (target: 100 percent).
- **Monitoring overhead**: Monitoring cost over total run cost (target: no more than 20 percent; above 30 percent triggers policy review).
- **Drift detection latency**: Reporting windows between a control-limit breach and a fired trigger (target: no more than 2).

**Learning and Recalibration Mechanisms**:

- **Delayed label capture**: Enqueue a label callback for every monitored decision at emission, since a monitor whose outcomes are never labelled cannot be recalibrated and degrades silently.
- **Signal ablation**: Require each admitted signal to improve selective risk over the best single-signal baseline on held-out data, and remove signals that do not, since an unhelpful signal adds cost and invites double-counting.
- **Combination discipline**: Combine signals only through a versioned rule or model fitted on held-out data, avoiding correlated features that count one source twice.
- **Threshold recalibration**: Recompute every threshold per task class against observed outcomes; the values stated here are deployment defaults, not constants.
- **Incident feedback**: Record every confidently wrong accepted case with its signal vector, verdict class, and bundle identity, and treat a cluster of them as a drift trigger rather than as individual defects.

**Human-in-the-Loop Boundaries**: Granting certification to a signal whose measured gap exceeds 10 percentage points, promoting a calibrator or threshold bundle, approving a slice-specific threshold, relaxing the disclosure boundary, and permitting a consequential decision to proceed with 0 external signals are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how a process is measured rather than what the process reasons about. Its phases hold wherever an observable event can be labelled, a signal can be computed from a record, and a control layer exists to consume the verdict.

### 4.1 Cross-Domain Application Patterns

**Regulated clinical decision support**: The observable event is agreement with an adjudicated clinical determination, labelled by a reviewing clinician at a latency of days. Process signals carry little weight because the reasoning is short; estimator signals and claim-level support carry most of it, and every recommendation decomposes into atomic claims tied to a cited record. Certification is granted per clinical speciality rather than across the population, because a gap acceptable in one speciality can conceal a large gap in a low-volume one. The monitoring record is a regulatory deliverable rather than a diagnostic aid, and the disclosure boundary binds hardest here.

**Financial claims and transaction adjudication**: Labels arrive quickly and in volume, so calibration windows are short and recalibration is frequent. Deterministic checks dominate the evidence order because policy rules, arithmetic, and entitlement constraints are computable, and estimator signals are admitted only for the residual open-vocabulary judgement. Selective prediction is the operating mode: coverage is the automation rate, risk is the loss among automated decisions, and reviewer capacity is a binding constraint on threshold selection rather than an afterthought.

**Software engineering and code generation**: The observable event is test passage or build success, labelled deterministically within minutes at near-zero cost. This is the most favourable monitoring environment in the corpus, and its lesson generalises inversely: where a deterministic verifier decides correctness, Section 1.4 suppresses monitoring and the verifier is used directly. Monitoring is instrumented only for what the tests do not cover, such as whether a change satisfies an under-specified requirement, and process signals carry the load because repeated identical tool calls and flat progress against subgoals are computable from the execution record.

**Scientific and evidence synthesis**: Claim-level support is the primary signal, since the failure that matters is a confident unsupported assertion rather than a wrong overall conclusion. Retrieval grounding is measured across passage relevance, faithfulness, citation entailment, currency, and authority rather than treated as satisfied by retrieval occurring. Labels are expensive and slow, so evaluation partitions are small, slices are provisional more often than not, and most signals remain in reporting-only status with human adjudication gating consequential release.

**Industrial and field operations**: The environment supplies frequent external signals at low cost, so externally classified evidence is abundant and process signals refresh at short horizons. Reversibility varies within a single episode, since a provisional schedule is reversible while a dispatched crew is not, so thresholds bind per action class rather than per episode. Out-of-domain detection matters more than average calibration, because conditions shift with season, site, and equipment revision, and a probability calibrated in one regime should not be stretched over another.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk reversible work**: Retain the observable event, 2 or 3 process signals, and 1 certified estimator, and drop the panel, conformal, and claim-level machinery. Monitoring overhead above 10 percent of direct-execution cost indicates the gate in Section 1.4 should have suppressed instrumentation.
- **High-risk or irreversible work**: Retain every phase, require at least 1 external signal per consequential decision, decompose output to claim level, and prefer abstention over an accepted case whose critical claims are unsupported.
- **Strict latency budgets**: Prefer process signals and provider-returned probabilities, which cost one pass, over multi-sample estimators, which cost several. Where latency forbids any estimator, gate on deterministic checks alone and record the estimator class as unavailable rather than approximating it.
- **Sparse-label deployments**: Where labels arrive slowly or rarely, hold signals in reporting-only status, gate on deterministic checks, and accumulate a labelled window before certification rather than certifying on a small sample and inheriting a false operating point.
- **High-volume deployments**: Compute process signals in the streaming path and estimator signals on a sampled subset, recording the sampling frame so live measures remain unbiased estimates of the population rather than of the sampled tail.

***

## V. Limitations and Considerations

**Stated confidence is weakly related to accuracy**: A model asked how confident it is produces a number that tracks output fluency more reliably than evidence, and elicitation methods that work on one task family do not transfer to another. The consequence is that an uncalibrated confidence figure gating an action produces confident automation of exactly the cases the system understands least. The mitigation is the certification requirement in Step 3.3, which bars any uncertified signal from a threshold comparison, together with the 10 and 20 percentage point gap boundaries that demote and suspend a signal on measured evidence rather than on impression.

**Thresholds here are deployment defaults, not measured constants**: Every numeric bound in this guide, including the 10 and 20 point calibration gaps, the 200-example slice minimum, the 20 percent overhead ceiling, and the metric targets in Section III.D, was chosen to be operable on first deployment rather than derived from a property of reasoning systems. The consequence is that a deployment inheriting them unchanged may gate too permissively or too conservatively for its own cost structure. The mitigation is the threshold recalibration requirement in Section III.D, obliging each deployment to recompute every bound per task class against its own observed outcomes and its own cost matrix.

**Calibration degrades under distribution shift**: Comparisons at scale reported that many uncertainty methods and post-hoc calibration degrade under dataset shift, and that post-hoc calibration is not a complete defence [12]. The consequence is that a signal certified on a representative window can silently lose validity when the input population moves. The mitigation is the drift trigger set in Step 6.2 together with the out-of-domain verdict class, which routes novel cases separately rather than stretching an in-domain probability across them.

**Set-valued guarantees are conditional**: Conformal procedures return coverage guarantees that are marginal rather than per-case, and ordinary conformal validity relies on exchangeability between calibration and test examples [14]. The consequence is that a nominal level presented as an unconditional promise becomes false after a distribution change without any visible failure. The mitigation is the requirement in Step 5.2 to log realised coverage and set size and to present the nominal level as conditional, and the undercoverage drift trigger in Step 6.2.

**Labels are the binding constraint**: No signal can be certified where the observable event cannot be labelled, and label cost and latency bound how often recalibration is possible. The consequence is that the deployments most in need of monitoring, those with expensive expert labels, are the ones least able to certify a signal. The mitigation is the rejection condition in Section 1.4, which declines instrumentation rather than fabricating certification, together with the reporting-only status that permits a signal to inform a human reviewer while gating nothing.

**Externality is a provenance judgement, not a proof of independence**: A retrieved source may share the training data that produced the answer, and two model families may share a common pretraining corpus and a common error. The consequence is that a signal classified as external can still fail in the same direction as the object layer, and correlated failure survives the classification. The mitigation is the evidence ordering in Step 4.1, placing deterministic validators first and model judges last, and the requirement in Step 4.2 to route unresolved model-against-model conflicts to human adjudication rather than to a third model.

**Self-evaluation and judging carry documented biases**: The source records that models can fail to correct reasoning without external feedback and can degrade correct answers [20], that judge evaluations exhibit position, verbosity, self-enhancement, and limited-reasoning effects [21], that evaluators can favour their own generations [22], and that preference optimisation can encourage agreement over truthfulness [23]. These findings are transcribed from the originating prose guide as it cited them and were not independently re-verified during this conversion; they are carried as attributed claims rather than as established fact. The consequence is that a judge admitted without controls contributes bias rather than information. The mitigation is the bias control record required in Step 4.2, without which a judgement is excluded from agreement counting.

**Monitoring data carries its own exposure**: A record rich enough to support calibration reveals user topics, proprietary documents, security thresholds, model weaknesses, and reviewer decisions. The consequence is that the monitor becomes a disclosure surface larger than the system it observes. The mitigation is the disclosure boundary in Section III.A, which prohibits retention of hidden reasoning content and of user-visible thresholds, and requires allowlist capture, field-level redaction, tenant isolation, and retention by risk class.

**Structural conformance is not sound monitoring**: A monitor can satisfy every checkpoint in this guide while measuring an event that does not matter, on a population that does not resemble deployment, for a decision no one acts on. The framework detects a malformed monitor, not a misdirected one, and no automated check substitutes for human review of whether the declared observable event is the one whose failure would actually cause harm.

***

## VI. Conclusion and Summary

Metacognitive monitoring is a measurement discipline before it is a reasoning technique. Its value comes from a small number of properties that can be checked rather than asserted: that every signal has a definition computable from a record, that every gating probability has been compared against observed outcomes on data it never saw during fitting, that agreement counted as confirmation came from sources that could have disagreed, and that the component producing the measurement is not the component acting on it. A monitor holding those four properties improves decisions under a fixed risk, latency, cost, and reviewer-capacity envelope. A monitor holding none of them produces a precise-looking number that cannot be defended.

A team introducing monitoring should instrument before it estimates. Define the observable event and the label source, emit the observation record, and compute process signals, which cost nothing beyond the record and cannot be talked out of their values. Only then add an elicited estimator, hold it in reporting-only status while a labelled window accumulates, and certify it before it gates anything. Add claim-level verification where unsupported assertions are the failure that matters, and add panel and set-valued methods last, because they cost several generations each and their assumptions are the easiest to violate quietly.

**Key Success Factors**:

- **Computable definitions**: Every admitted signal is a function over recorded fields, so two implementations agree and no signal depends on a model reporting on itself.
- **Certification before gating**: A stated confidence is calibrated against observed outcomes on held-out data before it may be compared to any threshold, and certification attaches to a bundle rather than to a product name.
- **Independence before confirmation**: Agreement is counted once per source, judgements carry bias controls, and at least 1 externally classified signal accompanies every consequential decision.
- **Measurement without authorship**: The monitor observes and never changes the process, and a component that both writes a value and acts on it is re-scoped rather than trusted.
- **Deterministic arithmetic**: Signal computation, calibration, threshold evaluation, and the monitoring record belong to software, and model inference proposes only what no deterministic signal covers.
- **Recalibration on evidence**: Drift triggers fire on measured control-limit breaches and label-based regressions, and scheduled review is a backstop rather than the mechanism.

By following this guide, AI agents can produce monitoring signals whose numbers mean what they claim, suspend them the moment the evidence for that claim lapses, and hand a control layer a verdict it can act on without inheriting the blind spots of the process it governs.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; no independent research pass was performed during this conversion, so their titles, labels, and locations are reproduced rather than verified, and every empirical claim attributed to them in the body is carried as a claim of the source rather than as established fact.

**Corpus pointers**:

- `Production Guide to Metacognitive Monitoring` — the originating prose guide from which this operational guide was derived. Source of the monitoring and control distinction, the confidence signal taxonomy by access level, the calibration and selective-prediction measures, the limits of self-evaluation and judging, the drift-triggered recalibration loop, the claim-level evidence monitoring rules, the logging field families, and the deployment acceptance conditions. It carries inline citations to primary literature on metacognition, uncertainty estimation, calibration measurement, judge bias, rationale faithfulness, factual verification, and generative-AI risk; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — the companion guide owning the control layer. It specifies the three-layer architecture, the entry gate, the value-of-computation principle, the eight control transitions, stuck-state and diminishing-returns detection, and the control-quality metric set. This guide supplies the monitor layer that produces the evidence those control decisions consume, and adopts its terminology for layers, source classes, correlated failure, reason codes, and the disclosure boundary.
- `advanced_task_guides/reasoning/guide_SelfConsistency.md` — the companion guide covering diversified sampling toward an adjudicated answer class or a declared abstention. It governs the sampling and adjudication machinery behind the agreement and semantic entropy estimators declared in Step 1.3.
- `advanced_task_guides/reasoning/guide_ChainOfThoughtReasoning.md` — the companion guide covering the object layer this monitor most often observes: the warrant gate for intermediate reasoning, bounded effort configuration, deterministic answer extraction, and the rule that a reasoning trace is not evidence for the claims it contains. That rule is why a trace is admissible here as a process observation and never as a support signal.
- `advanced_task_guides/reasoning/guide_ChainOfVerification.md` — the companion guide covering claim-level verification against admitted evidence under bounded revision loops. It owns the machinery behind the claim support ratio declared in Step 1.3, and supplies the label source that lets a support estimator be scored rather than merely reported.
- `advanced_task_guides/reasoning/guide_TreeOfThought.md` — the companion guide covering bounded search over partial solutions. Its state evaluator is an estimator signal in this guide's sense, and its evaluator admission bar applies the calibration measures and threshold-selection procedure specified here to a search-internal signal before that signal is permitted to prune.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — a telemetry design framework with its own implementation guidance for AI agents, applicable to the observation record and field inventory in Step 2.1.
- `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — an eight-phase methodology for monitoring system design with a domain adaptation section, applicable to the instrumentation and drift detection work in Phases 2 and 6.

**External references**: The numbering below is the numbering used by the inline markers in Sections I through V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Monitoring, control, and self-report foundations*

1. Nelson and Narens — https://sites.socsci.uci.edu/~lnarens/1990/Nelson&Narens_Book_Chapter_1990.pdf
2. Kadavath et al. — https://arxiv.org/abs/2207.05221
3. Binder et al. — https://arxiv.org/abs/2410.13787
4. Wang and Zhao, *Metacognitive Prompting Improves Understanding in Large Language Models* — https://aclanthology.org/2024.naacl-long.106/

*Confidence signals and uncertainty estimators*

5. Xiong et al. — https://arxiv.org/abs/2306.13063
6. Wang et al., self-consistency — https://arxiv.org/abs/2203.11171
7. Kuhn, Gal, and Farquhar, semantic entropy — https://arxiv.org/abs/2302.09664
8. Farquhar et al., indexed by PubMed — https://pubmed.ncbi.nlm.nih.gov/38898292/
9. Malinin and Gales — https://arxiv.org/abs/2002.07650
10. Lakshminarayanan, Pritzel, and Blundell — https://arxiv.org/abs/1612.01474
11. Gal and Ghahramani — https://arxiv.org/abs/1506.02142
12. Ovadia et al. — https://arxiv.org/abs/1906.02530
13. Quach et al., conformal language modeling — https://arxiv.org/abs/2306.10193
14. Barber et al. — https://arxiv.org/html/2202.13415v5

*Calibration measurement and selective prediction*

15. Guo et al., temperature scaling — https://arxiv.org/abs/1706.04599
16. Nixon et al. — https://arxiv.org/abs/1904.01685
17. Roelofs et al. — https://arxiv.org/abs/2012.08668
18. Ding et al. — https://arxiv.org/abs/1903.02050
19. GPT-4 Technical Report — https://cdn.openai.com/papers/gpt-4.pdf

*Limits of self-evaluation, judging, and stated reasons*

20. Huang et al. — https://arxiv.org/abs/2310.01798
21. Zheng et al. — https://arxiv.org/abs/2306.05685
22. Panickssery et al. — https://arxiv.org/abs/2404.13076
23. Sharma et al. — https://arxiv.org/abs/2310.13548
24. Turpin et al. — https://arxiv.org/abs/2305.04388
25. Anthropic faithfulness research — https://www.anthropic.com/research/reasoning-models-dont-say-think

*Claim-level verification and evidence monitoring*

26. Min et al., FActScore — https://arxiv.org/abs/2305.14251
27. Es et al., Ragas — https://arxiv.org/abs/2309.15217
28. Wei et al., SAFE — https://arxiv.org/abs/2403.18802
29. Manakul, Liusie, and Gales, SelfCheckGPT — https://arxiv.org/abs/2303.08896

*Security, instrumentation, and risk guidance*

30. OverThink — https://arxiv.org/abs/2502.02542
31. OWASP Prompt Injection guidance — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
32. OpenTelemetry GenAI registry — https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/registry/attributes/gen-ai.md
33. NIST AI 600-1 — https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
