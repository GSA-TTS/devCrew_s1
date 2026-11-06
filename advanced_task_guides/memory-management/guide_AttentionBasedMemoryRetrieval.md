# Attention-Based Memory Retrieval

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Attention-based memory retrieval constitutes the task family of deciding which stored memory records become visible to a model call, in what order, and under what token budget. This guide provides AI agents with a structured protocol for scoring a bounded candidate set of memory records against the current query, admitting only records that clear a calibrated threshold, and placing the admitted set into a prompt whose stable region supports cache reuse and whose volatile region supports salience. It re-scopes the transformer attention mechanism, which no agent can read or modify at runtime, onto an agent-layer surrogate: an explicit, logged, auditable salience function whose components are declared, whose weights are calibrated on a labelled admission set rather than assumed, and whose output is a ranking input to a deterministic context assembler that alone holds the tokenizer and the budget veto. It specifies a six-phase framework covering contract and budget declaration, candidate generation, salience scoring and weight calibration, bounded admission and two-zone placement, utilization and position verification, and recalibration under drift. It partitions every unit of work across a deterministic tier, a model tier, and a hybrid tier, naming which component holds authority when the two disagree, so that admission remains reproducible and a full context window is never mistaken for a used one.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Memory record**: The atomic unit of stored information eligible for admission, carrying content, an identifier, a version, a source, a trust class, a sensitivity class, a creation time, and a token count. A record is not a chunk of raw text; a chunk without provenance and token accounting cannot be scored, budgeted, or audited.

**Candidate pool**: The bounded set of memory records returned by first-stage retrieval for one query, before scoring and admission. The pool is capped by construction, since an unbounded pool makes reranking cost unpredictable.

**Salience score**: The scalar assigned to a candidate record for one query, computed as a weighted combination of normalized components minus a redundancy penalty against the already-admitted set. The score orders candidates; it does not admit them.

**Salience component**: One declared, separately computed, separately logged input to the salience score, such as semantic relevance, lexical match, recency, importance, authority, access frequency, or redundancy.

**Component weight vector**: The ordered set of coefficients applied to the normalized components. The vector is versioned, and every admission log entry records the version that produced it.

**Admission threshold**: The per-query-normalized score floor a candidate must clear to be eligible for admission, paired with a top-N cap. A floor without a cap admits the whole pool on a degenerate query; a cap without a floor admits noise on a query with no good candidates.

**Context assembler**: The deterministic component that holds the deployed tokenizer, the reservation ledger, and the sole authority to place a record into the outgoing prompt. No model call writes into the prompt directly.

**Token budget**: The hard input limit for one call, minus reserved output tokens, minus reserved tool-call and safety headroom, expressed in tokens counted by the deployed tokenizer rather than estimated from characters.

**Stable prefix**: The leading region of the prompt whose serialization is byte-identical across calls within a reuse window, carrying policy, tool contracts, response schema, and broadly shared static material.

**Salience suffix**: The trailing region of the prompt carrying the current goal, live constraints, admitted evidence, conflicts, and the final request, ordered by salience rather than by reuse.

**Cache boundary**: The declared point separating the stable prefix from the salience suffix, expressed as a provider cache breakpoint where the provider supports one, and as a hash checkpoint in the assembly record in every case.

**Assembly record**: The immutable per-call log of what was considered, what was admitted, where it was placed, why, and at what token cost. It is the primary artifact this method produces.

**Context utilization**: The fraction of admitted evidence tokens associated with a supported answer claim. It is reported both at token level and at item level, because one used sentence inside a long admitted passage inflates the token-level figure.

**Citation support**: The fraction of checked citations whose cited span actually supports the claim attached to it, judged against the admitted text rather than against the model's assertion.

**Position sweep**: The controlled experiment that moves identical decisive evidence through declared relative positions while holding token count, distractor density, and template fixed, to measure placement sensitivity for a named model revision.

**Effective context length**: The greatest tested input length at which every predeclared capability gate passes for a named model revision, tokenizer, template, task suite, and score gate. It is not the advertised context window.

**Distractor**: An admitted or injected record that is irrelevant to the decisive question but shares entities, dates, terminology, or answer form with the truth. Plausible distractors damage more than random padding because they compete on meaning.

**Duplicate cluster**: A group of candidate records whose contents are exact or near-identical, collapsed to one admitted representative so repetition does not manufacture apparent corroboration.

**Conflict group**: A set of admitted records making mutually inconsistent claims about the same subject, surfaced adjacently with authority and time rather than resolved silently by ranking.

**Truncation verdict**: The typed decision the assembler returns before inference, drawn from pass, compact, drop, route, or reject. Silent truncation is prohibited; every reduction names what was removed.

**Calibration set**: The held-out collection of query and record pairs carrying human or adjudicated labels for decisiveness, used to fit and to verify the component weight vector and the admission threshold.

### 1.2 Re-Scoping From Model-Internal Attention to Agent-Layer Salience

The mechanism this task family is named for is transformer self-attention. Every prompt token produces key and value representations, the current computation produces a query, and learned heads mix values according to query and key compatibility, at every layer, across the whole visible context. That mechanism is not reachable from the agent layer. An agent cannot read an attention matrix, cannot inspect a hidden state, cannot resize or repartition a key-value cache, and cannot substitute an attention variant at runtime. Instructions that depend on those capabilities are not executable by an agent and are therefore excluded from this guide.

What survives is an agent-layer surrogate with the same job description and different mechanics. Internal attention decides how admitted tokens are combined; the surrogate decides which records become tokens at all. The surrogate is an explicit scoring, thresholding, and placement stage that runs before the model call, produces a written record of every decision, and is calibrated against measured outcomes. It is executable because every one of its inputs is a stored field, every one of its computations is either arithmetic or a bounded model call, and every one of its outputs is a file, a log row, or a prompt.

The two mechanisms must not be conflated. Internal attention does not first select a few records and then read them; it mixes all visible tokens, so a record that scored well externally may still be ignored, and a record with low external score may still change the answer. This asymmetry is the reason Phase 5 exists: the surrogate's quality is established by measuring whether admitted evidence was used, never by asserting that a high score implies use.

**Mechanism re-scoping map**:

| Model-internal mechanism | Agent-layer surrogate | What the surrogate does not reproduce |
| :-- | :-- | :-- |
| Query and key compatibility across all visible tokens | Scored ranking of candidate records against the query | Internal mixing still reads every admitted token, so the surrogate governs visibility, not reading |
| Softmax competition among values | Per-query score normalization, an admission cap, and a redundancy penalty | Dilution still occurs among admitted records and cannot be prevented by scoring alone |
| Positional encoding of token index | Declared placement zones and a logged ordering rank | Position effects remain model-specific and must be measured per revision, not assumed |
| Multi-head specialization | Multiple declared salience components combined by a versioned weight vector | Components are chosen and auditable; heads are learned and neither |
| Key-value cache as serving state | Provider prefix cache boundary and cached-token telemetry | The cache is computation reuse, not a memory store, and carries no provenance or deletability |
| Retrieval-like head behaviour | Cross-encoder or model-tier adjudication over candidates | An external relevance verdict does not predict internal causal use |

Three classes of below-agent-layer configuration are retained in this guide as facts rather than levers. Attention architecture and positional scaling, key-value cache precision and eviction policy, and kernel or serving-engine version all change how admitted tokens behave, and a change in any of them invalidates a calibration produced under the previous configuration. Agents must record these values in the assembly record and treat a change in any of them as a recalibration trigger under Step 6.1. Agents must not attempt to set them.

### 1.3 The Salience Function and the Provenance of Its Weights

The salience score for one candidate record against one query is the weighted sum of its normalized components, minus a redundancy penalty computed against the set already admitted for that query. The function is stated in this form because every term is separately computable, separately loggable, and separately ablatable. A score whose components cannot be recovered from the log cannot be diagnosed when admission goes wrong.

**Salience component inventory**:

| Component | Computed by | Normalization | Calibration evidence required |
| :-- | :-- | :-- | :-- |
| Semantic relevance | Deterministic vector similarity over the candidate pool | Min-max across the pool for the current query | Labelled decisive-record judgements on the calibration set |
| Lexical and identifier match | Deterministic index or exact-match lookup | Binary for identifiers, min-max for scored lexical match | Recall on identifier-bearing queries |
| Adjudicated relevance | Model-tier reranker over the reduced candidate set | Z-score across the pool for the current query | Agreement with human decisiveness labels |
| Recency | Deterministic exponential decay over record age | Already bounded to the zero-to-one interval | Half-life fitted to observed staleness in the store |
| Importance | Model-tier scoring at write time on a bounded integer scale | Divided by the scale maximum | Inter-rater agreement against a human-labelled sample |
| Authority and trust class | Deterministic lookup on the record's source | Ordinal map to the zero-to-one interval | Policy declaration, not measurement |
| Access frequency | Deterministic counter over admission history | Logarithmic, then min-max across the pool | Correlation with realized utilization |
| Redundancy penalty | Deterministic similarity against the admitted set | Subtractive, bounded to the zero-to-one interval | Duplicate-collapse precision on the calibration set |

The weight vector has exactly three admissible origins, and the assembly record must name which one produced the vector in force.

**Published default**: The generative-agent retrieval function combines recency, importance, and relevance as a weighted sum in which all three weights are set to 1 and recency decays exponentially at a factor of 0.995 per hour of elapsed time. This vector is admissible as a first configuration on day one and nothing more. It was fitted to a simulation corpus with different record semantics, different staleness dynamics, and no authority model, so carrying it into production unchanged is a deployment default, not a measured finding.

**Coordinate sweep on a labelled admission set**: Sweep each weight across the range 0 to 2 in steps of 0.25 while holding the remaining weights fixed, iterate the sweep until no single-coordinate move improves the objective, and select the vector maximizing admission precision at a fixed decisive-record recall of 0.95. The sweep requires a calibration set of at least 200 labelled query and record pairs spanning every task class in scope; below 200 pairs the selected vector is reported as provisional and does not gate a promotion.

**Ranker fitted to logged admission outcomes**: Fit a ranking model whose targets are the realized outcome fields of the assembly record, specifically per-item ablation effect and citation support, over at least 2,000 logged admissions, and evaluate it on a held-out time-forward split rather than a random split. A random split leaks future store state into the training window and inflates the estimate.

Two properties of the scoring stage are non-negotiable regardless of origin. First, scores must be normalized within the candidate pool for the current query before any threshold is applied. Reranker scores produced by listwise-trained cross-encoders constrain ordering within one query's candidate list and not absolute level, so the same numeric score carries no common meaning across queries and a fixed global cutoff silently admits too much on one query distribution and too little on another. Second, every score floor is paired with a top-N cap and every top-N cap is paired with a floor, so that neither a degenerate query with uniformly high scores nor a query with no acceptable candidate can defeat the admission stage.

The scoring function holds no admission authority. It emits an ordered list with per-component scores attached. The context assembler, a deterministic component, applies the threshold, applies the caps, applies the token budget, and returns a typed verdict. Where the assembler's budget conflicts with the score ordering, the budget wins and the displaced records are logged as dropped with a reason code. This separation is what makes the method reproducible: the same store, query, weight vector, and budget must produce the same admitted set on every run.

### 1.4 Execution Tier Partition

Every unit of work in this method belongs to exactly one execution tier, and every handoff between tiers is named. The partition is load-bearing rather than descriptive: it establishes what may never be delegated to model inference and what may never be reduced to a rule.

**Deterministic tier**: Work that must be done by software, scripts, queries, or schema validators because it requires exactness, reproducibility, auditability, or scale that model inference cannot supply. Token counting, budget arithmetic, authorization filtering, recency and frequency computation, hash-based deduplication, placement, prefix hashing, log emission, threshold application, and metric computation all sit here. The deterministic tier can reject any candidate for any reason and cannot be overridden by a model verdict.

**Model tier**: Work that must be done by a model call because it requires open-vocabulary judgement, natural-language understanding, or synthesis that no deterministic rule covers. Importance scoring at write time, adjudicated relevance on semantically near-miss candidates, conflict detection across differently worded records, chunk header synthesis, and answer generation with citations sit here. The model tier proposes; it never commits.

**Hybrid tier**: Work in which a model proposes and software verifies, or software retrieves and a model adjudicates. Admission, conflict resolution, and citation verification sit here, and each names an authority holder.

**Tier assignment and authority**:

| Work unit | Tier | Authority when tiers disagree |
| :-- | :-- | :-- |
| Token counting and budget reservation | Deterministic | Deterministic; a model estimate is never substituted for a tokenizer count |
| Authorization and sensitivity filtering | Deterministic | Deterministic; a model relevance verdict never overrides an authorization denial |
| Recency, frequency, and authority component computation | Deterministic | Deterministic |
| Exact and near-duplicate clustering | Deterministic | Deterministic |
| Importance scoring at write time | Model | Model, bounded by a fixed integer scale and a schema validator |
| Adjudicated relevance on the reduced pool | Model | Model, bounded by per-query normalization and a top-N cap |
| Conflict detection across records | Model | Model proposes the conflict group; a deterministic schema check rejects malformed groups |
| Conflict resolution and canonical selection | Hybrid | Deterministic; the authority-and-time policy decides, or the call abstains |
| Admission of a scored candidate | Hybrid | Deterministic; the assembler's budget and threshold bind over the score ordering |
| Placement, ordering, and cache boundary emission | Deterministic | Deterministic |
| Citation emission in the answer | Model | Model |
| Citation span verification | Hybrid | Deterministic; a cited span that does not resolve in the admitted text is unsupported regardless of the model's claim |
| Per-item ablation utilization | Deterministic | Deterministic |
| Weight and threshold calibration | Deterministic | Deterministic |
| Drift detection against the frozen baseline | Deterministic | Deterministic |

Three handoffs carry the method's risk and must be instrumented explicitly. The retrieval-to-scoring handoff passes a bounded pool with per-candidate metadata and receives per-component scores; a candidate missing metadata is rejected before scoring rather than scored on defaults. The scoring-to-assembly handoff passes an ordered list with normalized scores and receives a typed admission verdict per candidate; the assembler never re-runs the scorer. The assembly-to-verification handoff passes the assembly record and the model output and receives utilization and citation-support figures; verification never modifies the assembly it is measuring.

***

## II. Operational Framework: Calibrated Salience Admission Into a Bounded Context

The framework produces one artifact per model call, the assembly record, and one artifact per configuration, the calibration record. Phases 1 through 4 execute on every call once calibrated, with Phases 1 and 3 collapsing to a lookup of the current contract and weight vector at runtime. Phases 5 and 6 execute on an evaluation cadence and return control to Phase 3 when a gate fails or a configuration fact changes.

### Phase 1: Retrieval Contract and Budget Declaration

**Objective**: Fix what the admitted context must achieve, what it may cost, and what counts as evidence, before any candidate is retrieved, so that admission is judged against declared targets rather than against apparent relevance.

#### Step 1.1: Declare the Decision Contract and Evidence Standard

**Required Actions**:

- Name every task class in scope and, for each, the facts an answer must carry, the form a correct answer takes, and the conditions under which abstention is the correct outcome.
- Declare the authority ordering that resolves conflicting records, naming source precedence and recency precedence separately, since a newer record from a weaker source is not automatically canonical.
- Declare the evidence standard, stating whether a claim requires a cited record identifier, a quoted span, or both, and which claim types may rest on model synthesis.
- Declare the numeric gate for each of context utilization, citation support, position-sensitivity range, effective context length, truncation incidence, cached-token ratio, and per-task cost.
- Record the consequence attached to each gate, naming whether a breach blocks promotion, forces a rollback, or raises a review.

**Required Outputs**:

- A decision contract record naming task classes, required facts, abstention conditions, and evidence standard.
- An authority ordering specification separating source precedence from recency precedence.
- A gate register carrying one numeric threshold and one breach consequence per gate.

**Quality Checkpoints**:

- Every gate in the register carries a number and a named consequence; a gate without a consequence is removed rather than retained as an aspiration.
- Abstention is declarable as a successful outcome for at least 1 task class; a contract in which abstention is always a failure forces unsupported answers.
- The authority ordering resolves every pair of source classes present in the store, so no conflict resolves by retrieval rank alone.

***

#### Step 1.2: Compute the Token Budget and Reserve Headroom

**Required Actions**:

- Count every prompt component with the deployed tokenizer or the provider's official counting endpoint; character-based and word-based estimation is prohibited because it fails at exactly the boundary where the budget binds.
- Reserve the requested output tokens plus a safety margin of 5 percent of the hard input limit before any evidence is admitted, and reserve a separate allowance for tool-call and tool-result tokens where the call may invoke tools.
- Compute the admissible evidence budget as the hard input limit minus the stable prefix, minus the reservations, minus the fixed goal and instruction block.
- Cap admitted evidence at 40 percent of the hard input limit by default, and record the cap as a deployment default subject to recalibration in Phase 6.
- Emit a typed budget verdict before inference, drawn from pass, compact, drop, route, and reject, and halt the call on reject rather than allowing the provider to truncate.

**Required Outputs**:

- A budget ledger naming the hard input limit, each reservation, and the residual evidence budget in tokens.
- A reservation record identifying which components are protected from truncation.
- A typed budget verdict attached to every assembly record.

**Quality Checkpoints**:

- Intended input tokens and sent input tokens are both recorded and equal on a passing call; a divergence indicates silent truncation and halts release of the call.
- No protected component appears in a removal list; a truncation that cuts a policy block, an evidence span, a structured record, or a code unit is rejected.
- The budget verdict precedes inference in the log ordering; a verdict written after the call cannot have gated it.

***

#### Step 1.3: Freeze Counterfactual Baselines

**Required Actions**:

- Build a no-memory baseline, a retrieval-only baseline that answers from the top record without synthesis, a fixed-top-k baseline that admits a constant number of records without scoring, and a maximum-context baseline that admits everything the budget allows.
- Freeze the corpus snapshot, query set, template version, seed policy, model revision, tokenizer identifier, and scoring code, and record each identifier in the evaluation manifest.
- Record the configuration facts named in Section 1.2, specifically the attention architecture, positional scaling, cache precision and eviction policy, and serving engine version reported by the provider or operator.
- Size the query set at no fewer than 100 queries per task class and run no fewer than 5 seeds per configuration, reporting the worst seed alongside the median.
- Hold the eligible corpus and authorization policy identical across every baseline, so differences measure admission rather than reachability.

**Required Outputs**:

- A baseline configuration set of at least 4 named variants with results recorded per task class.
- A frozen evaluation manifest carrying every identifier needed to reproduce a run.
- A configuration fact record covering the below-agent-layer settings in force.

**Quality Checkpoints**:

- The retrieval-only baseline is present, since without it a reading failure cannot be distinguished from a retrieval failure.
- Every baseline result carries a seed count of at least 5; results from fewer seeds are marked provisional and excluded from gate decisions.
- The manifest reproduces a prior run to identical admitted sets when replayed; a non-reproducing manifest blocks Phase 3.

***

### Phase 2: Candidate Generation and Eligibility Filtering

**Objective**: Produce a bounded, authorized, deduplicated candidate pool in which every record carries the metadata the scoring stage requires, so that scoring never operates on defaults.

#### Step 2.1: Assemble the Bounded Candidate Pool

**Required Actions**:

- Run exact and lexical lookup first, and admit vector retrieval only where a measured recall gap on the calibration set justifies its cost.
- Cap the candidate pool at 200 records by default, and record both the eligible candidate count and the retrieved candidate count so pool truncation is visible.
- Attach to every candidate its record identifier, version identifier, source identifier, source type, trust class, sensitivity class, content hash, creation time, and token count, computed by the deployed tokenizer.
- Reject any candidate missing a required metadata field before scoring, and log the rejection with a reason code rather than substituting a default value.
- Preserve the full rejected-candidate list for the calibration window, since admission precision and missed-evidence analysis cannot be computed from admitted records alone.

**Required Outputs**:

- A candidate pool of at most 200 records with complete metadata per record.
- A retrieval run record naming retriever versions, query hash, and candidate counts.
- A rejected-candidate list retained for the calibration window.

**Quality Checkpoints**:

- Every candidate carries all 9 required metadata fields; a candidate scored on a defaulted field is a calibration contaminant and is removed.
- Pool truncation is recorded whenever the eligible candidate count exceeds the cap, so a systematically truncated pool is detectable.
- Vector retrieval is present only where a recall gap was measured; an unjustified retrieval stage is removed at the next recalibration.

***

#### Step 2.2: Apply Authorization, Sensitivity, and Freshness Gates

**Required Actions**:

- Evaluate authorization for the requesting principal against every candidate before any score is computed, so that an unauthorized record never reaches a model call even as a reranking input.
- Drop superseded record versions where the store carries versioning, retaining lineage outside the active view rather than admitting both versions as a conflict.
- Apply sensitivity-class rules, blocking admission of records whose class forbids the current destination, and record the block with its rule identifier.
- Apply a freshness gate per task class where staleness has a declared operational meaning, expressed as a maximum record age rather than as a recency weight, since a weight can be outvoted and a gate cannot.
- Record the authorization result, the sensitivity verdict, and the freshness verdict per candidate in the retrieval run record.

**Required Outputs**:

- An eligibility verdict per candidate covering authorization, sensitivity, and freshness.
- A blocked-record register naming the rule that blocked each record.
- An active-version candidate set with superseded versions excluded.

**Quality Checkpoints**:

- No record with a denied authorization result appears anywhere downstream, including in reranking inputs and in logs holding content rather than references.
- Superseded versions are absent from the active set; their presence produces a fabricated conflict group and fails the checkpoint.
- Every block carries a rule identifier; an unattributed block cannot be reviewed and is treated as a defect.

***

#### Step 2.3: Collapse Duplicates and Form Conflict Groups

**Required Actions**:

- Collapse exact duplicates by content hash, retaining the representative with the strongest authority and recording the collapsed identifiers in a duplicate cluster.
- Cluster near-duplicates at a similarity threshold of 0.95 by default, and retain one representative per cluster unless the records originate from genuinely independent sources.
- Preserve independent corroboration explicitly, since collapsing two independent confirmations into one removes evidence rather than redundancy.
- Invoke a model-tier pass to detect claims that are mutually inconsistent across differently worded records, and validate every proposed conflict group against a schema before it is carried forward.
- Apply diversity caps of at most 3 records per source and at most 2 records per episode by default, recording every capped exclusion.

**Required Outputs**:

- A duplicate cluster register naming the representative and the collapsed identifiers per cluster.
- A conflict group register naming the subject, the inconsistent records, and their authority and time values.
- A diversity-capped candidate set with exclusions recorded.

**Quality Checkpoints**:

- Every collapsed cluster names its representative and the rule that selected it, so a collapse can be reversed under review.
- Conflict groups carry authority and time per member, since a group without them cannot be resolved by the Step 1.1 ordering.
- Independent corroboration survives collapse; a cluster spanning more than 1 source class without a recorded independence check fails the checkpoint.

***

### Phase 3: Salience Scoring and Weight Calibration

**Objective**: Assign each eligible candidate a per-query-normalized salience score from declared components, using a weight vector and a threshold whose provenance and calibration evidence are recorded rather than assumed.

#### Step 3.1: Compute and Log the Salience Components

**Required Actions**:

- Compute every deterministic component first, specifically lexical and identifier match, recency decay, authority mapping, and access frequency, and log each raw value before normalization.
- Invoke the model-tier reranker only over the reduced pool where first-stage precision was measured as the binding constraint, and cap that invocation at 50 candidates by default to bound latency and cost.
- Normalize every component within the candidate pool for the current query, using min-max for bounded components and z-score for reranker output, and log both raw and normalized values.
- Compute the redundancy penalty against the provisionally admitted set rather than against the whole pool, so the penalty reflects what would actually be seen together.
- Emit the ordered candidate list with the full component vector attached to every entry, and never emit a bare scalar, since a bare score cannot be diagnosed or ablated.

**Required Outputs**:

- A per-candidate component vector carrying raw and normalized values for every declared component.
- An ordered candidate list with salience scores and the weight vector version that produced them.
- A reranker invocation record naming the model, the version, and the candidate count.

**Quality Checkpoints**:

- Normalization is computed within the current query's pool; a component normalized against a global fixed range fails the checkpoint because it reintroduces cross-query incomparability.
- Every scored candidate carries a complete component vector; a missing component is logged as absent rather than imputed as zero, since zero is a meaningful score.
- The reranker candidate count does not exceed the cap; an uncapped reranking stage makes per-call latency unbounded.

***

#### Step 3.2: Calibrate the Component Weight Vector

**Required Actions**:

- Assemble a calibration set of at least 200 labelled query and record pairs spanning every task class, labelling each record as decisive, supportive, or irrelevant for its query.
- Select the weight origin from the three admissible origins in Section 1.3, and record the origin, the date, and the evidence supporting it in the calibration record.
- Where the coordinate sweep is used, sweep each weight across 0 to 2 in steps of 0.25 holding the others fixed, iterate until no single-coordinate move improves the objective, and maximize admission precision at a fixed decisive-record recall of 0.95.
- Verify the selected vector on the downstream task metric, not only on the ranking metric, because a vector that improves ranking precision can still lower context utilization by admitting long low-density records.
- Hold out at least 20 percent of the calibration set for verification, and split time-forward rather than at random wherever the store accumulates over time.

**Required Outputs**:

- A calibration record naming the weight origin, the objective, the sweep range, the selected vector, and its version identifier.
- A held-out verification result reporting admission precision, decisive-record recall, and context utilization.
- A rejected-vector log naming the candidate vectors evaluated and their scores.

**Quality Checkpoints**:

- The calibration set carries at least 200 labelled pairs; below that count the vector is marked provisional and may not gate a promotion.
- The verification split is time-forward wherever the store is append-only; a random split on an append-only store inflates the estimate and fails the checkpoint.
- The selected vector improves at least 1 downstream metric over the published default; a vector that improves only the ranking metric is not promoted.

***

#### Step 3.3: Set, Version, and Bound the Admission Threshold

**Required Actions**:

- Set the admission floor on the per-query-normalized score rather than on the raw score, and record the normalization method alongside the floor.
- Pair the floor with a top-N cap of at most 12 admitted evidence records by default, so a query whose candidates all score highly cannot consume the whole budget.
- Pair the cap with the floor in the opposite direction, so a query with no candidate above the floor admits nothing and the call proceeds to the declared abstention path rather than admitting the least bad record.
- Version the threshold and the cap together, since a threshold calibrated against one cap does not transfer to another, and record the version in every assembly record.
- Declare the marginal-utility rule that stops admission early, stating the point at which an additional record's expected contribution no longer justifies its token cost, and record the estimate per admitted record.

**Required Outputs**:

- An admission policy record carrying the floor, the cap, the normalization method, and a shared version identifier.
- A per-record marginal-utility estimate attached to every admission decision.
- An abstention path specification for queries admitting zero records.

**Quality Checkpoints**:

- The floor and the cap carry the same version identifier; a mismatched pair invalidates the calibration and blocks the call.
- A query admitting zero records routes to the declared abstention path; admitting a below-floor record to avoid an empty context fails the checkpoint.
- Every admission decision carries a marginal-utility estimate, so admissions that never pay for themselves are detectable in aggregate.

***

### Phase 4: Bounded Admission and Two-Zone Placement

**Objective**: Convert the scored candidate list into a serialized prompt whose token count is exact, whose stable region is byte-identical across calls, and whose every placement decision is recorded with a reason.

#### Step 4.1: Execute Admission Under the Deterministic Budget Enforcer

**Required Actions**:

- Walk the ordered candidate list once, admitting each record only where it clears the floor, the running count is below the cap, and its token count fits the residual evidence budget.
- Recompute the redundancy penalty after each admission, so a record that duplicates what was just admitted loses priority rather than being admitted on a stale score.
- Admit records labelled decisive before records labelled supportive, even where a supportive record scores higher, since the contract in Step 1.1 defines decisiveness and the score only estimates it.
- Stop admission when the residual budget cannot hold the next candidate, and log every remaining candidate as dropped with a reason code drawn from below-floor, cap-reached, budget-exhausted, redundancy-collapsed, or diversity-capped.
- Return the typed budget verdict and halt on reject, so that a call whose decisive evidence does not fit is re-scoped or routed rather than answered from a partial view.

**Required Outputs**:

- An admitted record set with an admission decision, a reason code, and a token count per record.
- A dropped-candidate list carrying one reason code per entry.
- A residual budget figure recorded after the final admission.

**Quality Checkpoints**:

- The sum of admitted record tokens plus fixed blocks plus reservations equals the sent input token count exactly; any discrepancy halts the call.
- Every dropped candidate carries exactly 1 reason code from the closed vocabulary; free-text reasons defeat aggregate admission analysis and are rejected.
- No record is admitted below the floor; a below-floor admission indicates the enforcer was bypassed and blocks release of the assembly.

***

#### Step 4.2: Partition the Assembly Into Stable Prefix and Salience Suffix

**Required Actions**:

- Serialize the stable prefix in a fixed canonical order with canonicalized whitespace, fixed field order, fixed tool order, and a recorded template version, so that a semantically identical prompt is also byte-identical.
- Place every volatile element after the cache boundary, specifically timestamps, request identifiers, per-principal memory, retrieved evidence, and conversation deltas, since a single token change before the boundary invalidates reuse downstream of it.
- Order the suffix so that supportive background sits early, conflict groups sit adjacent to the evidence they affect, and decisive evidence and current state sit nearest the final request.
- Assign delimiters, section titles, and source labels from a trusted template rather than accepting structure supplied by a record, and mark every admitted record with its identifier, source, time scope, and trust class.
- Rebuild the current-state block from canonical state on every call in long loops rather than appending the transcript, restating goal, constraints, current step, unresolved variables, and latest verified evidence.

**Placement zone contract**:

| Zone | Content admitted | Ordering rule | Serialization constraint |
| :-- | :-- | :-- | :-- |
| Stable prefix | Policy, tool contracts, response schema, shared static material | Fixed canonical order | Byte-identical across calls in the reuse window; no timestamps, identifiers, or per-principal content |
| Background evidence | Supportive records and long shared documents | Descending salience | Self-sufficient chunks carrying an assembler-assigned header and source label |
| Conflict block | Conflict groups from Step 2.3 | Grouped by subject, adjacent to the affected evidence | Authority and time stated per member; no silent selection of one value |
| Current state | Goal, live constraints, current step, unresolved variables | Canonical state regenerated per call | Restatements labelled as reminders, never as new authority |
| Decisive evidence | Records labelled decisive by the contract | Ascending salience, highest nearest the request | Quoted spans preserved verbatim with their identifiers |
| Final request | Instruction and response contract | Fixed | Untrusted record content never appears in this zone |

**Required Outputs**:

- A serialized prompt with a recorded zone assignment and ordering rank per admitted record.
- A stable prefix hash and a template version identifier.
- A normalized relative position per admitted record, computed as the item midpoint divided by the sent input length.

**Quality Checkpoints**:

- The stable prefix hash is identical across two calls whose stable content is semantically identical; a differing hash indicates a canonicalization defect and blocks cache enablement.
- No volatile field appears before the cache boundary; a timestamp or request identifier in the prefix fails the checkpoint.
- Every admitted record carries a zone, an ordering rank, and a relative position, since position analysis in Phase 5 is impossible without them.

***

#### Step 4.3: Emit the Assembly Record and Cache Boundaries

**Required Actions**:

- Emit one immutable assembly record per model call, carrying a single assembly identifier that links the retrieval run, the scoring run, the admission decisions, the placement, and the downstream answer.
- Declare the cache boundary at the prefix-suffix transition, using the provider's breakpoint mechanism where one exists, and record the boundary position in the assembly record in every case.
- Verify that the stable prefix meets the provider's minimum cacheable length before declaring a breakpoint, since a prefix below the minimum is processed without caching and returns no error to signal the miss.
- Namespace every reusable prefix by tenant or principal trust boundary, and never derive a cache namespace from a public or guessable identifier.
- Record the cache lookup result, cached tokens read, cache write tokens, uncached input tokens, and the uncached counterfactual cost, so net savings can be computed rather than inferred from a hit rate.

**Assembly record template**:

```
ASSEMBLY_ID:
TRACE_ID:
TASK_CLASS:
PRINCIPAL_SCOPE:
MODEL_ID:
MODEL_REVISION:
TOKENIZER_ID:
TEMPLATE_VERSION:
WEIGHT_VECTOR_VERSION:
ADMISSION_POLICY_VERSION:
HARD_INPUT_LIMIT_TOKENS:
OUTPUT_RESERVATION_TOKENS:
SAFETY_MARGIN_TOKENS:
EVIDENCE_BUDGET_TOKENS:
INTENDED_INPUT_TOKENS:
SENT_INPUT_TOKENS:
BUDGET_VERDICT:          PASS | COMPACT | DROP | ROUTE | REJECT
CANDIDATE_POOL_SIZE:
RERANKED_COUNT:
ADMITTED_COUNT:
ADMITTED_ITEMS:          record_id, version, source, trust_class,
                         component_vector, normalized_score, zone,
                         ordering_rank, relative_position, item_tokens,
                         marginal_utility_estimate
DROPPED_ITEMS:           record_id, reason_code
DROP_REASON_CODES:       BELOW_FLOOR | CAP_REACHED | BUDGET_EXHAUSTED |
                         REDUNDANCY_COLLAPSED | DIVERSITY_CAPPED |
                         AUTHORIZATION_DENIED | STALE | SUPERSEDED
DUPLICATE_CLUSTERS:
CONFLICT_GROUPS:
STABLE_PREFIX_HASH:
CACHE_NAMESPACE:
CACHE_BOUNDARY_POSITION:
CACHE_LOOKUP_RESULT:
CACHED_TOKENS_READ:
CACHE_WRITE_TOKENS:
UNCACHED_COUNTERFACTUAL_COST:
CONFIGURATION_FACTS:     attention_architecture, positional_scaling,
                         cache_precision, eviction_policy, engine_version
RECORD_CONTENT:          REFERENCE_ONLY
```

**Required Outputs**:

- One immutable assembly record per call linking retrieval, scoring, admission, placement, and outcome.
- A cache boundary declaration with a namespace scoped to a trust boundary.
- A cache economics record carrying read, write, and counterfactual figures.

**Quality Checkpoints**:

- The assembly record references record content by identifier and hash rather than embedding it, so the log does not become a second uncontrolled copy of sensitive memory.
- Every cache namespace is scoped to a trust boundary and derived from a secret rather than a public identifier; a guessable namespace fails the checkpoint.
- Request hit rate and cached-token ratio are reported separately, since a high hit rate over a small prefix is not a saving.

***

### Phase 5: Utilization Measurement and Position Verification

**Objective**: Establish whether the admitted evidence was actually used, at which positions the model uses it, and up to what input length every declared capability still passes its gate.

#### Step 5.1: Measure Citation Support and Item-Level Utilization

**Required Actions**:

- Require the answer to cite record identifiers and, where exactness binds, quoted spans, and reject an answer whose citations do not resolve against the admitted set.
- Verify every cited span deterministically by matching it against the admitted text, and label a citation unsupported where the span does not resolve or does not contain the claim's asserted content.
- Compute token-level utilization as admitted evidence tokens associated with supported claims divided by admitted evidence tokens, and compute item-level utilization separately, since a long record containing one used sentence inflates the token-level figure.
- Run per-item ablation on a sampled subset, removing one admitted record at a time and recording whether the answer changed, so records that were admitted but never causally used become visible.
- Distinguish claims sourced from admitted records from claims produced by synthesis, and report the unsupported-claim rate for each separately.

**Required Outputs**:

- A citation verification result per claim carrying supported, unsupported, or unresolvable.
- A utilization report carrying token-level and item-level figures per task class.
- A per-item ablation record naming records admitted without measurable effect.

**Quality Checkpoints**:

- Citation support is at or above 90 percent per task class; below that the admission policy is returned to Phase 3 rather than the instruction being reworded.
- Item-level utilization is at or above 60 percent; below that the cap in Step 3.3 is lowered before any budget increase is considered.
- Span verification is deterministic; a citation accepted on the model's assertion that it is supported fails the checkpoint.

***

#### Step 5.2: Run the Position and Distractor Sweep

**Required Actions**:

- Place identical decisive evidence at early, quartile, middle, three-quarter, and late relative positions while holding token count, distractor density, template, and seed policy fixed.
- Repeat the sweep for single-fact retrieval, multi-fact composition, aggregation, contradiction handling, and citation generation, since single-fact retrieval degrades later than composition and reports an optimistic picture alone.
- Add random padding first and plausible distractors second, constructing distractors that share entities, dates, terminology, and answer form with the truth, and record distractor density as distractor tokens divided by evidence-plus-distractor tokens.
- Report the worst position, the range across positions, and the variance, and never report a single averaged figure, since averaging conceals the placement that fails.
- Include adversarial placement in the sweep, specifically instruction-like text positioned immediately before the final request and record content that mimics the assembler's own headers.

**Required Outputs**:

- A position-sensitivity report carrying scores at 5 declared relative positions per task type.
- A distractor-density curve per task type with random and plausible distractors reported separately.
- An adversarial placement result covering header mimicry and late-position instruction injection.

**Quality Checkpoints**:

- The range between the best and worst position score is at or below 10 points; a wider range forces a placement change in Step 4.2 before promotion.
- Plausible distractors are tested separately from random padding; a sweep using only random padding is marked incomplete and does not satisfy the gate.
- Record content placed in the final-request zone is detected and rejected in the adversarial run; a successful header mimicry blocks promotion.

***

#### Step 5.3: Establish the Effective Context Length

**Required Actions**:

- Test at increasing input-length buckets drawn from the production distribution rather than from the advertised window, and run every declared capability at every bucket.
- Declare the effective context length as the greatest bucket at which every mandatory capability gate passes, and stop extending when any mandatory capability fails its gate twice across independent seeds.
- Report the effective context length bound to a named model revision, tokenizer, template version, task suite, score gate, and configuration fact set, since it does not transfer across any of them.
- Set the supported operating length below the first unstable bucket rather than at it, and record the margin.
- Compare the smallest passing configuration against the largest, and select the smallest, since a larger admitted context that meets the same gates costs more in prefill and in per-token decode without a measured benefit.

**Required Outputs**:

- An effective context length figure bound to its full configuration identifier set.
- A per-bucket capability matrix showing pass or fail per task type.
- A supported operating length with a stated margin below the first unstable bucket.

**Quality Checkpoints**:

- The effective context length is reported with every binding identifier attached; a bare token figure is not a usable result and fails the checkpoint.
- No mandatory capability is averaged with a passing capability to produce an overall verdict; a failed aggregation task blocks the bucket regardless of retrieval score.
- The supported operating length sits strictly below the first unstable bucket; equality provides no margin against distribution shift.

***

### Phase 6: Drift Detection and Recalibration

**Objective**: Detect when the calibration in force has stopped describing the deployment, recalibrate against fresh evidence, and promote a new configuration only against paired controls.

#### Step 6.1: Detect Configuration and Distribution Drift

**Required Actions**:

- Monitor the configuration fact set continuously and raise a recalibration trigger on any change of model revision, tokenizer, chat template, positional scaling, cache precision, eviction policy, serving engine version, retriever version, or reranker version.
- Monitor the admission distribution, specifically admitted count per call, drop reason mix, floor clearance rate, and pool truncation rate, and raise a trigger where any shifts materially against the frozen baseline.
- Monitor the outcome metrics, specifically utilization, citation support, truncation incidence, cached-token ratio, and per-task cost, and raise a trigger on a decline of 10 percentage points or more in any of them.
- Monitor distractor density in production traffic, since a store that accumulates near-duplicate or semantically adjacent records raises dilution without any configuration change.
- Record every trigger with its evidence and its detection time, so recalibration latency is measurable rather than anecdotal.

**Required Outputs**:

- A drift register naming each trigger, its evidence, and its detection time.
- A configuration fact comparison against the frozen baseline.
- An admission distribution report covering counts, drop reason mix, and clearance rate.

**Quality Checkpoints**:

- Every configuration fact in the frozen baseline is monitored; an unmonitored fact allows a silent invalidation of the calibration and fails the checkpoint.
- A decline of 10 percentage points or more in any gate metric raises a trigger within 1 evaluation cycle; a longer detection latency is itself recorded as a defect.
- Drift triggers are recorded even where no recalibration follows, so suppressed triggers remain auditable.

***

#### Step 6.2: Recalibrate Weights, Thresholds, and Budgets

**Required Actions**:

- Refresh the calibration set with recent labelled pairs before refitting, since a vector refitted on a stale set reproduces the drift it was meant to correct.
- Refit the weight vector by the same procedure declared in Step 3.2, and re-derive the floor and the cap together as a versioned pair.
- Re-derive the evidence budget cap from measured utilization rather than from the previous value, lowering it where item-level utilization fell and raising it only where a measured recall gap justifies the additional tokens.
- Change exactly one element per recalibration cycle, testing weight vector, threshold pair, budget cap, and placement order separately, so a regression can be attributed.
- Pair every recalibrated configuration with the frozen baseline on the same query set, seeds, and template, and reject any configuration that improves an average while degrading the worst slice.

**Required Outputs**:

- A refreshed calibration set with its collection window recorded.
- A new versioned weight vector, threshold pair, and budget cap with paired baseline results.
- A change log naming the single element changed per cycle.

**Quality Checkpoints**:

- Exactly 1 element changed per cycle; a multi-element change that regresses cannot be attributed and is reverted in full.
- Every recalibrated result is paired with the frozen baseline on identical inputs; an unpaired result does not satisfy a gate.
- Worst-slice performance is reported alongside the mean; a configuration improving the mean while degrading the worst position, worst task type, or worst length bucket is rejected.

***

#### Step 6.3: Shadow, Canary, and Promote

**Required Actions**:

- Replay production assembly records against the candidate configuration without serving its output, and compare admitted sets, token counts, and projected costs against the configuration in force.
- Canary by task class, input-length bucket, and risk tier rather than by uniform traffic share, since position and length effects concentrate in specific buckets.
- Hold the canary until every gate in the Step 1.1 register has passed on 2 consecutive frozen runs, and roll back on any mandatory quality, security, latency, or cost regression.
- Promote the simplest passing configuration, preferring fewer components, a smaller cap, and a shorter admitted context wherever gates are equally met.
- Where no configuration passes, reduce scope, improve source quality, route the failing task class to a different method, or require human review, and never resolve the failure by raising the budget.

**Required Outputs**:

- A shadow comparison report covering admitted-set divergence and cost projection.
- A canary result per task class, length bucket, and risk tier.
- A promotion decision naming the selected configuration and the gates it passed.

**Quality Checkpoints**:

- Promotion follows 2 consecutive passing frozen runs; a single passing run is provisional and does not authorize promotion.
- The promoted configuration is the simplest among those passing; promoting a more complex configuration requires a recorded measured advantage.
- No promotion is authorized on the basis of a raised token budget alone; a budget increase without a utilization improvement is recorded as a failure to resolve.

***

## III. Implementation Guidance for AI Agents

AI agents operating an attention-based memory retrieval pipeline must follow systematic protocols ensuring that admission is deterministic given the same inputs, that every admitted record is attributable, and that no model call is permitted to write into its own context. The following guidance translates the admission pipeline into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Agent**: Owns the decision contract, the authority ordering, the gate register, and the budget ledger. It alone may amend a gate, and every amendment is versioned. It refuses execution against an incomplete contract.
2. **Retrieval Agent**: Executes first-stage lookup, enforces the candidate pool cap, and attaches required metadata. It may not score, may not admit, and may not substitute a default for a missing metadata field.
3. **Eligibility Agent**: Applies authorization, sensitivity, freshness, versioning, deduplication, and diversity caps. Its denials are final and cannot be overridden by any downstream score.
4. **Scoring Agent**: Computes deterministic components, invokes the bounded model-tier reranker, normalizes per query, and emits the ordered list with full component vectors. It proposes an ordering and never commits an admission.
5. **Context Assembler**: Holds the deployed tokenizer, the reservation ledger, and the sole authority to place a record into the prompt. It applies the floor, the cap, and the budget, emits the typed verdict, and serializes the two zones.
6. **Verification and Calibration Agent**: Measures citation support, utilization, and position sensitivity, maintains the drift register, refits weights and thresholds, and holds a veto over promotion. It never modifies an assembly it is measuring.

**Admission Authority Boundary**: No component other than the Context Assembler places content into an outgoing prompt. A model call receives an assembled context and returns text; it never receives the ability to request additional records mid-generation without re-entering Phase 2 under a fresh assembly identifier. Where a component cannot justify an admission without exposing content it is not authorized to hold, the admission is refused and the call routes to the abstention path.

**Workflow Execution Pattern**:

```
STATE: Admission_And_Assembly
INPUTS:
  1. Ordered candidate list with component vectors from Phase 3
  2. Budget ledger and reservation record from Step 1.2
  3. Admission policy record from Step 3.3
ACTIONS:
  1. Walk the ordered list once, applying floor then cap then budget
  2. Recompute the redundancy penalty after each admission
  3. Assign zone, ordering rank, and relative position per admitted record
  4. Serialize the stable prefix and compute its hash
  5. Emit the assembly record and the typed budget verdict
VALIDATION:
  - sent_input_tokens == intended_input_tokens
  - admitted_count <= admission_cap
  - min(normalized_score of admitted) >= admission_floor
  - protected_block_removed == FALSE
  - volatile_field_before_cache_boundary == FALSE
  - weight_vector_version == admission_policy_version_pair
  - record_content_in_log == FALSE
TRANSITIONS:
  IF budget_verdict == PASS THEN next_state = Model_Invocation
  IF budget_verdict IN {COMPACT, DROP} THEN next_state = Re_Admission_Pass
  IF budget_verdict == ROUTE THEN next_state = Task_Routing
  IF budget_verdict == REJECT THEN next_state = Abstention_Path
  IF validation_failed THEN next_state = Assembly_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended admitted set, its token accounting, and its placement without serializing a prompt; confirm the plan against the validation block while no call has been issued; serialize and invoke only after validation passes, writing the assembly record in the same operation that issues the call.

**Approval Gate**: Human authorization is required before enabling prefix reuse across principals or tenants, before admitting any record whose sensitivity class is marked restricted for the current destination, before raising the evidence budget cap above 40 percent of the hard input limit, and before promoting any configuration whose position-sensitivity range exceeds 10 points. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the contract, gate register, weight vector, and admission policy in durable state, since a long-running loop outlives any single context window.
- Rebuild the current-state block from canonical state at every call rather than appending prior turns, and retain superseded values in lineage storage outside the active view.
- Write a handoff record at every context boundary naming the contract version, the admission policy version, the admitted-set history, and the open conflict groups.
- Count the retrieval, reranking, and assembly cost toward the task budget rather than treating the admission pipeline as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract and Budget Integrity (After Phase 1)**

- **Automated Check**: Every gate carries a number and a consequence; every budget dimension carries a token limit computed by the deployed tokenizer; at least 4 baselines are frozen with at least 5 seeds each.
- **Agent Action on Pass**: Proceed to candidate generation.
- **Agent Action on Failure**: Halt and return the contract or budget defect; no retrieval runs against an incomplete contract.
- **Human Review Trigger**: Any task class in which abstention is not declarable, or any gate whose consequence cannot be automated.

**Checkpoint 2: Pool Eligibility (After Phase 2)**

- **Automated Check**: Every candidate carries all 9 metadata fields; no denied-authorization record survives; every duplicate cluster names a representative and a selection rule; pool size is at or below the cap.
- **Agent Action on Pass**: Proceed to scoring.
- **Agent Action on Failure**: Remove the defective candidates and re-run eligibility only, not the whole retrieval.
- **Human Review Trigger**: Pool truncation on more than 20 percent of calls in a task class, which indicates the cap is binding on real recall rather than on noise.

**Checkpoint 3: Calibration Validity (After Phase 3)**

- **Automated Check**: The calibration set holds at least 200 labelled pairs; the verification split is time-forward on an append-only store; the floor and the cap share one version identifier; normalization is per query.
- **Agent Action on Pass**: Proceed to admission.
- **Agent Action on Failure**: Halt promotion of the vector and continue serving the previously promoted configuration.
- **Human Review Trigger**: A selected vector that improves the ranking metric while degrading item-level utilization by more than 5 percentage points.

**Checkpoint 4: Assembly Integrity (After Phase 4)**

- **Automated Check**: Sent input tokens equal intended input tokens; no protected block appears in a removal list; the stable prefix hash is stable across semantically identical calls; the cache namespace is scoped to a trust boundary; the log holds references rather than record content.
- **Agent Action on Pass**: Issue the model call.
- **Agent Action on Failure**: Halt the call; an assembly defect is never served with a warning attached.
- **Human Review Trigger**: Truncation incidence above 1 percent of eligible calls in any task class.

**Checkpoint 5: Utilization and Position Validity (After Phase 5)**

- **Automated Check**: Citation support at or above 90 percent; item-level utilization at or above 60 percent; position range at or below 10 points; effective context length reported with every binding identifier.
- **Agent Action on Pass**: Release the evaluation report and permit a promotion decision.
- **Agent Action on Failure**: Withhold the report, name the failing gate, and return control to Phase 3.
- **Human Review Trigger**: A citation-support figure below 75 percent, or any successful adversarial placement in the sweep.

**Checkpoint 6: Promotion Readiness (After Phase 6)**

- **Automated Check**: Exactly 1 element changed since the previous configuration; every result paired with the frozen baseline on identical inputs; 2 consecutive passing frozen runs recorded; worst-slice results reported alongside means.
- **Agent Action on Pass**: Promote the simplest passing configuration and version the change.
- **Agent Action on Failure**: Roll back to the configuration in force and record the failing gate.
- **Human Review Trigger**: Any regression in a security gate, or a proposal to promote on the basis of an increased token budget.

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
CONFIGURATION_FACT_SET:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Silent Truncation and Budget Overflow**

- **Symptoms**: Sent input tokens diverge from intended input tokens; answers omit facts that were recorded as admitted; a protected policy block is absent from the served prompt; the provider returns a shorter completion than requested.
- **Diagnostic Steps**: Recount every component with the deployed tokenizer rather than the counting method in use; compare the reservation ledger against the served prompt; determine whether the overflow originated in an unbounded evidence block, an unreserved tool result, or a template change that added fixed tokens.
- **Resolution Protocol**: Option A, lower the admission cap and re-run admission under the same scores. Option B, compact the lowest-utilization admitted records into references and re-admit. Option C, route the call to a task-specific configuration with a larger reservation. Option D, return the reject verdict and take the abstention path.
- **Escalation Trigger**: Truncation incidence above 1 percent of eligible calls in any task class escalates for contract review; a truncation that removed a protected block escalates immediately and is never resolved by retry.

**Error Type 2: Admission Miscalibration and Utilization Collapse**

- **Symptoms**: Item-level utilization falls while retrieval recall holds; admitted counts cluster at the cap on most queries; the floor clearance rate approaches either zero or one; ablation shows most admitted records have no measurable effect.
- **Diagnostic Steps**: Confirm normalization is computed within the current query's pool; compare the score distribution across query classes for a location shift; separate a scoring defect from a labelling defect by re-scoring the calibration set under the previous vector.
- **Resolution Protocol**: Option A, re-normalize per query and re-derive the floor against the new distribution. Option B, refit the weight vector on a refreshed calibration set. Option C, lower the cap until item-level utilization recovers, accepting a recall reduction that the gate register admits. Option D, split the admission policy by task class where a single vector cannot serve both.
- **Escalation Trigger**: Item-level utilization below 40 percent escalates for policy review; the failure is never resolved by raising the evidence budget, which increases cost while lowering utilization further.

**Error Type 3: Dilution by Duplicate and Plausible Records**

- **Symptoms**: Answers cite one of several near-identical records as though it were corroborated; accuracy falls as the store grows without any configuration change; adding a record lowers task success on a paired comparison.
- **Diagnostic Steps**: Measure production distractor density against the frozen baseline; inspect duplicate cluster sizes and the source distribution of admitted sets; run a paired ablation removing the plausible distractors while holding token count fixed.
- **Resolution Protocol**: Option A, lower the near-duplicate similarity threshold so more records collapse. Option B, tighten the per-source and per-episode diversity caps. Option C, raise the redundancy penalty weight and recalibrate the floor against it. Option D, move the collapse upstream into the write path so the store stops accumulating near-duplicates.
- **Escalation Trigger**: A paired comparison in which admitting an additional record lowers task success escalates the admission policy for review; an increased budget is never the response to a dilution finding.

**Error Type 4: Prefix Instability and Cross-Principal Cache Exposure**

- **Symptoms**: The cached-token ratio falls while the request hit rate holds; the stable prefix hash changes between semantically identical calls; a cache namespace resolves across principals; timing differs measurably between a guessed prefix and a novel one.
- **Diagnostic Steps**: Diff two serialized prefixes byte by byte to locate the volatile field; confirm the prefix meets the provider's minimum cacheable length, since a shorter prefix is processed without caching and returns no error; audit namespace derivation for a public or guessable input.
- **Resolution Protocol**: Option A, canonicalize the offending field and move it after the boundary. Option B, version the template so a changed prefix produces a new namespace rather than a partial match. Option C, partition namespaces per principal and accept a lower global hit rate. Option D, disable reuse for the affected prefix class entirely.
- **Escalation Trigger**: Any observed cross-principal reuse escalates immediately and disables reuse for the affected class pending review; this class is never resolved by retry or by a larger cache.

**Error Type 5: Placement-Based Injection and Header Mimicry**

- **Symptoms**: Record content appears to alter policy or tool authorization; a record reproduces the assembler's delimiters or section titles; instruction-like text appears immediately before the final request; a source consumes a disproportionate share of the admitted set.
- **Diagnostic Steps**: Confirm delimiters and section titles are assembler-assigned rather than record-supplied; locate the offending content's zone and relative position; check whether a source cap was exceeded or a diversity cap was bypassed.
- **Resolution Protocol**: Option A, sanitize record-supplied structure and re-serialize with assembler-assigned delimiters. Option B, restrict the offending source class to the background zone and bar it from the decisive and final-request zones. Option C, lower the per-source cap for the class. Option D, revoke the source's trust class and re-run eligibility.
- **Escalation Trigger**: Any case in which record content changed a tool authorization or a policy interpretation escalates immediately; tool authorization is enforced outside model text and is never restored by prompt wording.

**Troubleshooting Decision Tree**:

```
ADMISSION PIPELINE FAILS A CHECKPOINT
├─ BUDGET DEFECT
│   ├─ Sent tokens exceed intended → HALT; recount with deployed tokenizer
│   ├─ Protected block removed → HALT; escalate; never retry
│   └─ Reject verdict on decisive evidence → Route or abstain; never partial-answer
├─ SCORING DEFECT
│   ├─ Global cutoff on raw scores → Re-normalize per query; re-derive floor
│   ├─ Floor and cap version mismatch → Block call; restore the versioned pair
│   └─ Component missing from vector → Log as absent; never impute zero
├─ UTILIZATION DEFECT
│   ├─ Utilization falls, recall holds → Lower cap; refit weights
│   ├─ Ablation shows no effect for most items → Tighten floor; split by task class
│   └─ Adding a record lowers success → Record dilution; never raise the budget
├─ PLACEMENT DEFECT
│   ├─ Position range above 10 points → Move decisive evidence; re-sweep
│   ├─ Volatile field before cache boundary → Canonicalize; move after boundary
│   └─ Record-supplied delimiter accepted → Sanitize; reassign from template
└─ SECURITY DEFECT
    ├─ Cross-principal reuse observed → HALT reuse; escalate; partition namespaces
    ├─ Record content altered authorization → HALT; enforce tools outside model text
    └─ Log holds record content → Purge; replace with identifiers and hashes
```

### D. Performance Metrics and Continuous Learning

**Admission Quality Metrics**:

- **Admission precision**: Admitted records labelled decisive or supportive over admitted records (target: at least 70 percent; below 50 percent forces a floor increase).
- **Decisive-record recall**: Decisive records admitted over decisive records eligible (target: at least 95 percent; a breach blocks promotion regardless of precision).
- **Item-level utilization**: Admitted records associated with a supported claim or a measured ablation effect over admitted records (target: at least 60 percent; below 40 percent escalates).
- **Citation support**: Supported citations over checked citations (target: at least 90 percent; below 75 percent triggers human review).

**Placement and Capacity Metrics**:

- **Position-sensitivity range**: Best-position score minus worst-position score across the 5 declared positions (target: at most 10 points; above 10 blocks promotion).
- **Effective context length**: Greatest bucket passing every mandatory capability gate, reported with its binding identifiers (target: at or above the ninety-fifth percentile of production input length).
- **Truncation incidence**: Calls with any truncation over eligible calls (target: at most 1 percent; above 1 percent escalates for contract review).
- **Distractor tolerance**: Task success at production distractor density minus success at zero distractor density (target: at most 10 points).

**Efficiency Metrics**:

- **Cached-token ratio**: Cached tokens read over total input tokens where a stable prefix exists (target: at least 60 percent; reported separately from request hit rate).
- **Net cache saving**: Uncached counterfactual cost minus read, write, storage, and routing cost (target: positive; a negative figure disables the boundary rather than adjusting the target).
- **Per-task cost**: Retrieval, reranking, assembly, cache, and model cost for a completed task (target: below the maximum-context baseline at matched quality).
- **Admission overhead**: Retrieval, scoring, and assembly latency over end-to-end latency (target: at most 25 percent; above 40 percent triggers a component review).

**Learning and Adaptation Mechanisms**:

- **Outcome-linked labelling**: Convert verified citations and measured ablation effects into calibration labels automatically, so the calibration set grows from production rather than from a one-time labelling campaign.
- **Rejected-candidate retention**: Retain rejected candidates for the calibration window, since admission precision improves only where the counterfactual is observable.
- **Policy versioning**: Version every weight vector, threshold pair, and budget cap, and evaluate a new version on a time-forward split so the history that produced it does not also verify it.
- **Threshold recalibration**: Recompute every numeric bound per task class and per model revision; the values stated in this guide are deployment defaults, not measured constants.

**Human-in-the-Loop Boundaries**: Enabling cross-principal prefix reuse, admitting a record whose sensitivity class is restricted for the destination, amending an authority ordering, raising the evidence budget cap, and promoting a configuration whose advantage appears only at the mean are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs which stored records become visible to a model call rather than what those records contain. Its phases hold wherever a memory store exceeds the token budget, records carry provenance and time, and the cost of admitting a wrong record is measurable.

### 4.1 Cross-Domain Application Patterns

**Clinical and care decision support**: Authority ordering dominates the salience function, because a superseded medication record scoring highly on relevance is more dangerous than an omitted one. The freshness gate is expressed as a hard maximum record age per record type rather than as a recency weight, since a weight can be outvoted by relevance. Conflict groups are surfaced rather than resolved, and the contract declares abstention as the correct outcome wherever an unresolved conflict bears on the decision. Citation support carries a higher gate than elsewhere, and unsupported synthesis is reported separately rather than folded into an accuracy figure.

**Legal and regulatory research**: Records carry jurisdiction, effective date, and instrument hierarchy, so the authority ordering is multidimensional and the deterministic tier resolves it before scoring rather than after. Near-duplicate collapse is delicate, since two instruments with near-identical text may differ in one operative clause; the similarity threshold is set higher than the default and independence checks bind on every cluster. Position sensitivity matters more than usual because decisive language is often a single clause inside a long admitted document, so the sweep runs at clause granularity.

**Industrial operations and field maintenance**: Access frequency carries real signal, since the procedures technicians open most often are usually the ones that apply. Recency decay is fast for sensor-derived records and slow for procedure records, so the half-life is set per record type rather than globally. Latency budgets are tight, so the model-tier reranker is invoked only where first-stage precision was measured as binding, and the candidate pool cap is lower than the default.

**Customer account and support history**: Sensitivity classification and per-principal scoping dominate, since the store holds personal data and the cache namespace must never resolve across accounts. Deduplication is heavy because repeated contacts generate near-identical records, and diversity caps by episode prevent one long thread from consuming the admitted set. Utilization is measured per item rather than per token, since a long transcript admitted for one sentence inflates every token-level figure.

**Software engineering agents**: Records are code units, test results, and configuration files whose exactness matters, so lexical and identifier match carries more weight than semantic similarity and identifiers are never subject to reranking. Truncation that cuts a code unit is a protected-block violation rather than a compaction. The stable prefix is large and highly reusable, so cache boundary discipline yields more here than in domains where every call is unique.

**Scientific literature synthesis**: Independent corroboration must survive deduplication, since two independent replications collapsed into one representative destroy the evidence the task exists to find. Distractor construction is easy and important, because the literature supplies plausible near-misses naturally. Effective context length is measured on aggregation and contradiction tasks rather than on single-fact retrieval, since synthesis degrades well before retrieval does.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small stores below the budget**: Where the entire eligible store fits within the evidence budget with headroom, suppress scoring and admit everything, retaining deduplication, conflict grouping, and the assembly record. Scoring a set that need not be reduced adds cost and a failure mode without a benefit.
- **Large stores with sparse relevance**: Retain the full pipeline, lower the candidate pool cap to bound reranking cost, and invest the saved budget in first-stage recall rather than in a larger admitted set.
- **High-risk or irreversible decisions**: Raise the citation-support gate, require quoted spans rather than identifiers alone, surface every conflict group, and make abstention the default outcome where a mandatory fact is missing. Bind the approval gate before any admission from a restricted sensitivity class.
- **Strict latency budgets**: Remove the model-tier reranker before removing deterministic components, since the reranker dominates admission latency. Where latency forbids reranking entirely, lower the cap and raise the floor, and record the recall loss rather than hiding it.
- **Multi-principal deployments**: Partition cache namespaces per principal, derive namespaces from secrets rather than identifiers, and treat a global hit-rate target as a threat rather than a goal. Evaluate admission precision per principal class, since a policy calibrated on the majority class silently underserves the rest.
- **Long-horizon autonomous loops**: Rebuild the current-state block from canonical state at every call, retain lineage outside the active view, and re-run the contract check at every context handoff so drift is detected rather than inherited.

***

## V. Limitations and Considerations

**The surrogate is not the mechanism**: The salience function governs which records become visible; it does not govern how the model reads them. A record admitted with a high score may be ignored, and a record admitted with a low score may change the answer. The mitigation is Phase 5, which establishes admission quality by measured citation support and per-item ablation rather than by score, and Checkpoint 5, which withholds promotion where utilization fails its gate however good the ranking metric appears.

**Thresholds here are deployment defaults, not measured constants**: The candidate pool cap of 200, the reranked cap of 50, the admission cap of 12 records, the evidence budget cap of 40 percent, the near-duplicate threshold of 0.95, the diversity caps of 3 per source and 2 per episode, the utilization gate of 60 percent, the citation-support gate of 90 percent, and the position-range gate of 10 points were chosen to be operable on first deployment. None is derived from a universal property of memory stores. The mitigation is the recalibration requirement in Phase 6 and in Section III.D, obliging each deployment to recompute every bound per task class and per model revision against observed outcomes.

**The published weight default was fitted elsewhere**: The uniform weighting of recency, importance, and relevance with an hourly decay factor of 0.995 comes from a simulation architecture with different record semantics, no authority model, and no token budget. It is admissible as a first configuration and as nothing more. The mitigation is Step 3.2, which requires a calibrated replacement before the configuration gates a promotion and marks any uncalibrated vector as provisional.

**Score normalization reduces but does not remove incomparability**: Per-query normalization corrects the level-shift problem in listwise-trained reranker scores, but a reranker applied to a distribution far from its training data can score relevant and irrelevant records almost identically, in which case normalization spreads noise rather than signal. The mitigation is the paired floor and cap in Step 3.3, which bounds the damage in both directions, and the drift monitoring in Step 6.1, which raises a trigger when the floor clearance rate approaches zero or one.

**Calibration labelling is expensive and decays**: A calibration set of 200 labelled pairs per task class is a real annotation cost, and the labels age as the store and the task distribution change. The mitigation is the outcome-linked labelling mechanism in Section III.D, which converts verified citations and measured ablation effects into labels automatically, and the refreshed-set requirement in Step 6.2, which forbids refitting on a stale set.

**Below-agent-layer changes invalidate calibration silently**: A model revision, positional scaling change, cache precision change, eviction policy change, or kernel substitution can move position sensitivity and exact recall without changing any agent-layer configuration and without producing an error. The mitigation is the configuration fact record in Step 1.3 and the drift monitoring in Step 6.1, which treat any change in these values as a recalibration trigger, and the reporting rule in Step 5.3, which binds every effective-context-length figure to the configuration that produced it.

**The assembly record carries its own exposure**: A log rich enough to diagnose admission is rich enough to become a second uncontrolled copy of the memory store. The mitigation is the reference-only rule in Step 4.3, which stores identifiers, hashes, and token spans rather than record content, together with the access controls and redaction the sensitivity classification in Step 2.2 already establishes.

**Verification cost is real and tends to be deferred**: Position sweeps, distractor sweeps, length-bucket testing, and per-item ablation multiply evaluation cost, and deployments under schedule pressure report clean-condition results. The mitigation is Checkpoint 5, which withholds the evaluation report where any sweep is incomplete, and the sampling allowance in Step 5.1, which permits ablation on a sampled subset rather than on every call.

**Conflict surfacing can be mistaken for indecision**: Presenting conflict groups rather than resolving them produces answers that state disagreement, which reads as a weaker result than a confident wrong answer. The mitigation is the contract in Step 1.1, which declares abstention a successful outcome for named task classes, and the separate reporting of unsupported-claim rate in Step 5.1, so confidence bought by suppressing conflict is visible in the metrics.

**Structural conformance is not admission quality**: A pipeline can satisfy every checkpoint here and still admit the wrong records, because the gates detect malformed admission rather than a poorly specified contract. The framework does not verify that the declared decisive facts are the facts the task actually needs, and no checkpoint substitutes for human review of the contract itself.

***

## VI. Conclusion and Summary

Attention-based memory retrieval at the agent layer is an admission discipline before it is a scoring technique. Its value comes from a small number of explicit, auditable decisions: which records are eligible, how they are scored, which clear the threshold, where they sit in the prompt, and whether anything admitted was used. A pipeline that records those decisions can be calibrated and improved; a pipeline that fills the window and hopes cannot, because it has no counterfactual to learn from.

A team introducing this method should instrument before scoring. Build the deterministic assembler, the token-exact budget ledger, and the assembly record first, and run a fixed-top-k admission policy against them until the logs are trustworthy. Add the salience components next, one at a time, measuring item-level utilization after each. Add calibration only once a labelled set exists, and add the model-tier reranker last and only where first-stage precision has been measured as the binding constraint. Every one of those steps is cheaper than the alternative it replaces, which is a larger context window bought to compensate for an unmeasured admission policy.

**Key Success Factors**:

- **Deterministic budget authority**: One component holds the tokenizer and the admission veto, so the same store, query, weights, and budget always produce the same admitted set.
- **Declared and calibrated weights**: Every salience component is named, normalized within the query's own candidate pool, and weighted by a versioned vector whose origin and calibration evidence are recorded rather than assumed.
- **Paired floor and cap**: A score threshold never operates without a count cap and a count cap never operates without a threshold, so neither a degenerate query nor an empty pool can defeat admission.
- **Two-zone placement**: Reuse lives in a byte-stable prefix and salience lives in a volatile suffix, so cache economics and evidence placement stop competing for the same ordering decision.
- **Measured utilization, not assumed relevance**: Admission quality is established by verified citations and per-item ablation, and a full context window with low utilization is evidence to admit less rather than to buy more.
- **Recalibration on configuration change**: Any change below the agent layer invalidates the calibration above it, and the drift register makes that invalidation visible before the metrics degrade.

By following this guide, AI agents can decide what enters a model call deliberately, prove afterwards whether the decision paid for itself, and keep the smallest context that meets its declared gates rather than the largest the interface accepts.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them and were not independently re-verified during conversion, except where an entry is marked as retrieved during this conversion, in which case the reference was located and read in the course of the research described in Phase 3 and Section 1.3.

**Corpus pointers**:

- `Attention Mechanisms for Agent Memory: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the practitioner lever boundary, the ten prompt-construction procedures, the two-zone resolution of salience against cache reuse, the failure-mode inventory, the placement and cache security material, the metadata logging contract from which the assembly record is derived, the evaluation and cost program, and the end-to-end workflow. Its material on transformer internals, key-value cache sizing, quantization, eviction, kernels, serving architecture, and alternative attention architectures was excluded as below the agent layer, and is retained here only as the configuration fact set whose change invalidates a calibration.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — the category overview covering the two-axis memory taxonomy and the strategy selection ladder. It owns which store a record belongs in and the policy behind the retrieval eligibility gate; this guide owns what happens after eligibility, namely scoring, admission, and placement.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — owns the read and write operation contract on the durable store, including gate ordering and terminal states. This guide begins where a read returns, taking the bounded candidate pool of Step 2.1 as its input.
- `advanced_task_guides/memory-management/guide_HierarchicalMemory.md` — owns tier placement, promotion, and reclamation, which determine what is cheaply reachable; applicable to the pool assembly in Step 2.1 and the budget precedence order in Step 1.2.
- `advanced_task_guides/memory-management/guide_LatentMemoryNetworks.md` — owns embedding versioning and index generations; applicable to the similarity component in Step 3.1 and to the representation drift that Step 6.1 must distinguish from query drift.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — owns episode boundaries, outcome labelling, and trajectory-level reranking, including the rule that a bundle sheds whole trajectories rather than truncating one. This guide owns the token budget, the admission threshold, and the placement of whatever that ranking produces.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — owns the task-scoped state object and its protected atoms. This guide owns the retrieved-evidence portion of the assembly; the two-zone partition in Step 4.2 places serialized working state in the stable prefix without governing its content.
- `advanced_task_guides/memory-management/guide_GenerativeAgentMemory.md` — owns the recency, importance, and relevance stream architecture whose published retrieval function supplies the default weight vector discussed in Section 1.3. Its retrieval phase stops at an ordered candidate list, which this guide's admission and placement steps consume.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design and instrumentation, applicable to the assembly record in Step 4.3 and the drift register in Step 6.1.
- `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guidance on monitoring under constraint, applicable to the gate register in Step 1.1 and the metric families in Section III.D.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control loops, applicable to the abstention path in Step 3.3 and the promotion decision in Step 6.3.
- `advanced_task_guides/scoring/guide_complexityScoring.md` — a compact scoring rubric usable as a model for the component inventory and weight treatment in Section 1.3.
- `advanced_task_guides/knowledge-graphs/guide_KG_EntityResolutionDedup.md` — companion guidance on duplicate detection and clustering, applicable to the collapse and independence checks in Step 2.3.
- `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md` — companion guidance on provenance and evidence tracking, applicable to the record metadata requirements in Step 2.1 and the citation verification in Step 5.1.

**External references**: Titles are reproduced as the originating prose guide rendered them, which in most cases is a short label rather than a full publication title. Author attribution is supplied only where it was confirmed during this conversion.

*Position sensitivity, effective context length, and distraction*

1. *Lost in the Middle* — https://arxiv.org/abs/2307.03172
2. *RULER* — https://arxiv.org/html/2404.06654v3
3. *HELMET* — https://arxiv.org/abs/2410.02694 (retrieved during this conversion; its reported separation between recall and retrieval-augmented generation on one side and re-ranking and citation generation on the other supports the capability separation required in Step 5.3)
4. *LongBench* — https://arxiv.org/abs/2308.14508
5. *LongBench v2* — https://arxiv.org/abs/2412.15204
6. *LongBench Pro* — https://arxiv.org/html/2601.02872v1 (carried from the originating prose guide, which marks it as recent research pending target-workload reproduction)
7. *Reducing Distraction in Long-Context LMs* — https://arxiv.org/html/2411.05928v1

*Memory scoring and retrieval-time selection*

8. Park and colleagues, *Generative Agents: Interactive Simulacra of Human Behavior* — https://arxiv.org/abs/2304.03442 (retrieved during this conversion; source of the weighted recency, importance, and relevance retrieval function and its hourly decay factor of 0.995, cited in Section 1.3 as the published default weight origin)
9. *Cross-Encoder Rerankers in Production RAG: Architecture, Score Calibration, Latency Budgets, and Model Trade-Offs* — https://www.llms.blog/posts/cross-encoder-rerankers-in-production-rag-architecture-score-calibration-latency-budgets-and-model-trade-offs (retrieved during this conversion; source of the requirement in Section 1.3 that scores be normalized within the current query's candidate pool before any threshold is applied)

*Prompt caching, reuse boundaries, and cache isolation*

10. Anthropic, *Prompt caching* — https://platform.claude.com/docs/en/build-with-claude/prompt-caching (retrieved during this conversion; source of the exact-prefix-match requirement, the bounded number of cache breakpoints, and the model-dependent minimum cacheable prefix length below which a prefix is processed without caching and returns no error)
11. OpenAI, *Prompt caching* — https://developers.openai.com/api/docs/guides/prompt-caching
12. Google, *Gemini context caching* — https://ai.google.dev/gemini-api/docs/generate-content/caching
13. vLLM, *Prefix caching* — https://docs.vllm.ai/en/stable/design/prefix_caching/
14. vLLM, *Security* — https://docs.vllm.ai/en/latest/usage/security/
15. *Selective KV-Cache Sharing* — https://arxiv.org/html/2508.08438v1

*Attention weights as evidence*

16. *Attention is not Explanation* — https://arxiv.org/abs/1902.10186
17. *Attention is not not Explanation* — https://arxiv.org/abs/1908.04626
