# Generative Agent Memory

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Generative agent memory constitutes the task family of operating an append-oriented stream of timestamped natural-language experience, retrieving from that stream by a weighted combination of recency, importance, and relevance, synthesising higher-level inferences from accumulated records, and feeding both retrieved evidence and synthesised inference into a revisable plan. This guide provides AI agents with a structured protocol for running that architecture in task-completion deployments rather than in the simulated social sandbox where it was first demonstrated. It separates what transfers, namely the typed stream, evidence-cited inference, and memory-informed replanning, from what does not, namely the published weighting constants, the comprehensive observation policy, and believability as the evaluation objective. It specifies a six-phase framework covering stream contract and observation admission, importance scoring and calibration, retrieval scoring and weight calibration, reflection triggering and gated admission, plan coupling and revision, and maintenance through decay, audit, and verified deletion. It treats reflection as the principal production hazard, requiring that every synthesised inference be typed distinctly from an observation, retain resolvable links to the records that produced it, carry a confidence no higher than its evidence supports, and terminate at a bounded derivation depth. It partitions every unit of work across a deterministic tier, a model tier, and a hybrid tier in which a model proposes a reflection and deterministic software admits it.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Memory stream**: The durable, append-oriented store holding the agent's record of experience as typed records in creation order. Every record carries a description, a creation timestamp, a last-access timestamp, a type, and a provenance envelope. The stream is the system of record; every derived structure, including embeddings, summaries, and indexes, is a rebuildable projection of it.

**Observation**: A record of something perceived, comprising an external state change, a tool response, a human utterance, an authenticated system event, or the agent's own completed action. An observation is created only by an authenticated source and preserves the source payload or a reference to it. Model interpretation of a payload is never an observation.

**Reflection**: A model-authored inference over other memory records, stating an abstraction, a pattern, a relationship, or a lesson that no single record states directly. A reflection is a hypothesis with citations, not a fact, and it is typed distinctly from an observation everywhere in the store, in every index, and in every assembled prompt.

**Plan**: A versioned control artifact holding a goal, ordered steps, dependencies, assumptions, deadlines, tool permissions, status, and links to the memory records that justify each step. A plan states intended future action; it is never evidence about the world.

**Derivation depth**: The integer distance from a record to the observations beneath it. An observation has depth 0. A reflection citing only observations has depth 1. A reflection citing at least one reflection has depth equal to one plus the maximum depth among its cited supports.

**Leaf observation**: An observation reachable from a reflection by following citation edges downward. Leaf count, not citation count, measures how much evidence a reflection actually rests on, because one observation cited by three ancestors contributes one leaf.

**Provenance family**: The set of records sharing an originating source, actor, or upstream document. Two records from one provenance family are one piece of evidence for independence purposes regardless of how differently they are worded.

**Retrieval score**: The weighted sum of normalized recency, importance, and relevance components computed for one candidate record against one query. The score is a ranking hypothesis, not an authorisation and not a truth claim.

**Importance**: A score assigned at write time expressing the expected future decision value of a record. In the published architecture it is a single model-assigned integer from 1 to 10 expressing narrative poignancy. In production it is decomposed into named components and calibrated against realized utility.

**Reflection gate**: The deterministic component that accepts or rejects a candidate reflection proposed by the model tier. It resolves every citation, computes derivation depth and independent-leaf count, detects citation cycles, enforces the confidence ceiling, and emits a typed verdict. The gate alone admits a reflection to the stream.

**Synthetic ancestry fraction**: The proportion of a reflection's cited support that is itself model-authored. A value of 0 means the reflection rests entirely on observations; a value approaching 1 means the reflection is an inference about inferences.

**Replan trigger**: A declared condition under which the active plan is revised, drawn from a closed vocabulary: failed precondition, high-importance contradicting observation, deadline breach, tool error, human correction, conflicting evidence, or no-progress threshold breach.

**Plan-memory divergence**: The condition in which a plan cites memory records that have been superseded, invalidated, or deleted, or in which a step is marked complete without a corresponding completion observation.

**Realized utility label**: A delayed label attached to a memory record recording whether it was retrieved, cited, and materially changed a later decision. It is the only calibration target that survives contact with a production workload.

### 1.2 The Simulation Boundary: What Transfers and What Does Not

The architecture was demonstrated in a game-like sandbox town populated by 25 agents running an end-to-end scenario over two simulated days, with a controlled evaluation in which human raters watched a replay and ranked the full system against progressive ablations on believability [1]. That evidence establishes that the coupled loop produces coherent long-horizon behaviour in a small observable world. It does not establish factual correctness, task completion, safety, latency, or cost behaviour in a production task system, and the published ablation compared interview answers drawn from an equivalent accumulated state rather than independently re-run worlds. Agents deploying this pattern must carry the boundary explicitly rather than inheriting the constants and the objective together.

**Transfers without modification**: Heterogeneous retrieval, in which more than one signal ranks candidates so that a rare consequential record is not buried by a semantically closer trivial one. Explicit evidence pointers beneath every higher-level inference, which make the inference inspectable and invalidatable when a source is corrected or erased. Memory-informed replanning, in which accumulated experience revises a commitment rather than merely narrating it. Typed coexistence of observation, inference, and plan in one retrieval pool, provided the types remain distinguishable at retrieval time.

**Transfers only after calibration**: The three-component retrieval function transfers as a shape, not as a parameterisation. The published configuration sets all three weights to 1, normalizes each component by min-max across the candidate set, and decays recency exponentially at 0.995 per elapsed hour measured from last retrieval [1]. Those values are defaults fitted to a simulation corpus with different record semantics, different staleness dynamics, and no authority model. The published reflection trigger fires when accumulated importance since the last reflection exceeds 150, which produced roughly two to three reflections per agent-day in the reported simulation, and the reflection run presents the 100 most recent records, asks for 3 salient questions, and generates 5 cited insights [1]. Every one of those seven numbers is a starting point in a sweep, not a validated production value. Phase 2, Phase 3, and Phase 4 give the calibration procedures that replace them.

**Does not transfer**: Believability as the evaluation objective. The published evaluation measured ranked believability by human raters, and a critical review of 35 generative agent-based modelling studies found that 15 were validated solely by subjective assessment and 22 used subjective judgement as their only primary technique, concluding that believability, internal consistency, and resemblance do not establish operational validity for a scientific or operational use [4]. A task system replaces believability with task success under policy, citation support, and reflection groundedness as primary outcomes.

**Does not transfer**: Comprehensive observation. The published stream was described as a comprehensive natural-language record, which was appropriate to a small fully observable game world. Production environments emit logs, polling results, interface mutations, and repeated statuses at volumes where comprehensive capture raises stream growth, embedding spend, privacy exposure, and retrieval noise simultaneously. Phase 1 replaces comprehensiveness with declared admissible classes and event-driven capture.

**Does not transfer**: Full-day schedule decomposition, continuous per-tick perception, a social message bus, and persona-consistency optimisation as the primary objective. Each is mandatory for a social or embodied simulation and unnecessary for an ordinary support, research, engineering, or workflow agent. A stable character can be consistently wrong, and a system optimising persona stability over correctness will produce fluent incorrect action.

**Cost as a boundary condition**: The two-day, 25-agent run consumed multiple days of wall-clock time and thousands of dollars in token credits [1]. Later platforms that scaled the pattern to larger populations continued to identify model inference as the throughput bottleneck despite distributed execution [2][3]. Naive per-perception inference is therefore the default economic failure of this architecture, and Phase 1 admission control is the primary lever against it.

### 1.3 The Reflection Hazard and the Typed-Inference Discipline

Reflection is the component most likely to cause harm in production. It generates confident higher-order claims from lower-confidence observations, writes them into the same store the observations occupy, and thereafter serves them to retrieval on the same terms. A downstream consumer that cannot distinguish a record stating what a tool returned from a record stating what the model concluded will treat both as established, and a benchmark evaluating hallucination at the operation level rather than end to end found that memory systems generate and accumulate fabrications, errors, conflicts, and omissions during extraction and updating, which then propagate into answering [7]. Five controls are mandatory and are enforced by the deterministic reflection gate in Step 4.3.

**Distinct typing**: A reflection carries `record_type` of `reflection` in the stream, in every index, and in every assembled prompt. It is never rendered to a model or a human in a form indistinguishable from an observation. A retrieval result set reports the type mix, and a consumer requiring observed fact filters to `record_type` of `observation` rather than trusting rank order.

**Retained lineage**: Every claim inside a reflection carries the identifiers of the records supporting it. Claim-level citation is required; one valid citation attached to a multi-claim paragraph supports only the claim it accompanies, and remaining claims are marked unsupported. Every citation must resolve to a live record at admission time and must remain resolvable, so that correction or deletion of a source propagates to its descendants under Step 6.3.

**Bounded confidence**: A reflection's confidence never exceeds the minimum confidence among its cited supports, and a depth penalty of 0.15 per derivation level applies on top of that bound. A depth-1 reflection is therefore capped at 0.85 of its weakest support and a depth-2 reflection at 0.70. A general claim about a pattern, trait, or standing property is additionally capped at 0.80 until validated against an external outcome under Step 4.3, because a general claim asserts more than the union of its instances.

**Bounded derivation depth**: The maximum admissible derivation depth is 2. An observation is depth 0. A reflection citing only observations is depth 1. A reflection citing at least one depth-1 reflection is depth 2 and is the deepest record the gate admits. A candidate computing to depth 3 or greater is rejected, and the correct remedy is re-derivation from leaf observations rather than summarisation of the parent. Without this bound the store fills with inferences about inferences, each one further from evidence and each one indistinguishable in the index from the layer below it.

**Independence of support**: A reflection asserting a general claim requires at least 3 independent leaf observations drawn from at least 2 distinct provenance families. A reflection asserting a specific event may rest on 1 authoritative observation. Row count is not evidence count: duplicates, restatements, and messages relayed by the same actor collapse to one provenance family before the count is taken. A depth-2 reflection carries a synthetic ancestry fraction of at most 0.50, and a depth-1 reflection carries a synthetic ancestry fraction of exactly 0 by construction.

The governing rule is that a reflection proposes a planning abstraction and never proves itself. No reflection may be its own sole support, directly or through a citation cycle, and no reflection acquires authority by being retrieved frequently.

### 1.4 Boundary Against Sibling Methods

This guide owns the coupled architecture: the typed stream and its write path, importance scoring at write time, the three-component retrieval scoring over the stream, the reflection process and its admission gate, and the plan coupling that consumes both. Four boundaries against sibling guides in this corpus prevent duplicated and conflicting instruction.

**Against attention-based memory retrieval**: That guide owns salience scoring and bounded admission into the context window, including the token budget, the admission threshold, placement within the assembled prompt, and the calibration of a salience weight vector for that admission decision. This guide's Phase 3 stops at an ordered candidate list with per-component scores attached. The handoff is explicit: Phase 3 emits the ranked list, and the deterministic context assembler governed by the sibling guide applies the threshold, the caps, and the token budget. The recency decay default of 0.995 per hour appears in both guides because both inherit it from the same published source; each calibrates it against its own objective, and neither may assume the other's fitted value.

**Against episodic memory**: That guide owns episode boundary definition, episode schema, and outcome labelling. This guide treats an admitted observation as the atomic unit and does not redefine episode segmentation.

**Against memory consolidation**: That guide owns general promotion governance, contradiction detection across accumulated records, and the evidence gate for converting episodes into durable semantic claims. This guide owns only the reflection path, which is one specific promotion mechanism operating inline against a live stream on a salience trigger rather than as a batch consolidation job.

**Against working memory**: That guide owns the bounded task-scoped state governing a single reasoning episode. This guide's plan artifact is durable, versioned, and outlives the episode; transient status, current subgoal, and intermediate results remain working-memory state and are never appended to the stream.

### 1.5 Execution Tier Partition

Every unit of work in this method belongs to exactly one execution tier, and every handoff between tiers is named. The partition is load-bearing: it establishes what may never be delegated to model inference and what may never be reduced to a rule.

**Deterministic tier**: Work requiring exactness, reproducibility, auditability, or scale that model inference cannot supply. The memory stream append, timestamping, idempotent write under content hash, exact and near-duplicate detection, authorisation and sensitivity filtering, the recency decay computation, component normalization, the weighted-sum retrieval arithmetic and ranking, citation resolution, derivation-depth accounting, independent-leaf counting, citation-cycle detection, confidence-ceiling enforcement, plan version pointers, staleness detection, decay and eviction, tombstone propagation, and every metric computation sit here. The deterministic tier may reject any candidate record, reflection, or plan revision for any declared reason and is never overridden by a model verdict.

**Model tier**: Work requiring open-vocabulary judgement, natural-language understanding, or synthesis that no deterministic rule covers. Importance scoring for events that deterministic rules leave ambiguous, adjudicated relevance over a reduced candidate pool, reflection question generation, reflection synthesis with citations, plan step generation, and replan drafting sit here. The model tier proposes; it never commits a record to the stream.

**Hybrid tier**: Work in which a model proposes and software verifies, or software retrieves and a model adjudicates. Reflection admission, importance assignment, observation-versus-inference classification, and replan authorisation sit here, and each names an authority holder.

**Tier assignment and authority**:

| Work unit | Tier | Authority when tiers disagree |
| :-- | :-- | :-- |
| Stream append, timestamping, and idempotent write | Deterministic | Deterministic; a record without a resolved provenance envelope is never appended |
| Observation class assignment from source type | Deterministic | Deterministic; a model may not reclassify a model output as an observation |
| Exact and near-duplicate collapse | Deterministic | Deterministic |
| Authorisation, sensitivity, and retention filtering | Deterministic | Deterministic; a relevance verdict never overrides an authorisation denial |
| Importance scoring on ambiguous events | Model | Deterministic; rule-derived floors and ceilings bind over the model score |
| Recency decay and last-access accounting | Deterministic | Deterministic |
| Relevance computation over embeddings | Deterministic | Deterministic |
| Adjudicated relevance on the reduced pool | Model | Model, bounded by per-query normalization and a top-N cap |
| Component normalization, weighting, and ranking | Deterministic | Deterministic |
| Reflection trigger evaluation | Deterministic | Deterministic; cooldown, cap, and budget bind absolutely |
| Reflection question generation | Model | Model, bounded by a maximum question count |
| Reflection synthesis with citations | Model | Model proposes only |
| Citation resolution and depth accounting | Deterministic | Deterministic |
| Reflection admission | Hybrid | Deterministic; the gate's verdict is final and is never appealed to a model |
| Plan step generation and replan drafting | Model | Model proposes only |
| Replan trigger evaluation and authorisation | Hybrid | Deterministic; the trigger vocabulary and the permission set bind |
| Plan-memory divergence detection | Deterministic | Deterministic |
| Decay, archival, eviction, and tombstoning | Deterministic | Deterministic |
| Invalidation propagation to descendants | Deterministic | Deterministic |
| Calibration of weights, thresholds, and scales | Deterministic | Deterministic |

Four handoffs carry the method's risk and must be instrumented explicitly. The capture-to-admission handoff passes a raw source event with its authenticated origin and receives an admission verdict; an event whose origin cannot be authenticated is rejected rather than admitted with a low trust label. The scoring-to-ranking handoff passes per-component raw scores and receives a normalized ordered list; a candidate missing a component score is rejected before ranking rather than scored on a default. The synthesis-to-gate handoff passes candidate reflections with claim-level citations and receives a per-candidate typed verdict; the gate never re-runs the synthesiser and the synthesiser never retries a rejected candidate without new evidence. The gate-to-planning handoff passes only admitted reflections with their depth and confidence attached; a planner receiving a reflection without those fields treats it as unavailable.

***

## II. Operational Framework: A Typed Memory Stream With Gated Reflection and Coupled Planning

The framework assumes a decision has been identified that persistent experience, abstraction, and plan revision jointly improve, and that no-memory, bounded-recent-context, and simple-retrieval baselines have been frozen for comparison under Phase 1. Phases 1 through 3 establish the write and read paths. Phase 4 adds reflection only after retrieval is calibrated. Phase 5 couples memory to plans. Phase 6 runs alongside the others and gates every promotion of a configuration.

### Phase 1: Stream Contract and Observation Admission

**Objective**: Establish the record type system, the provenance envelope, and the admission policy that determine what enters the stream, so that capture volume is a declared decision rather than a consequence of what the environment happens to emit.

#### Step 1.1: Declare the Record Type System and Provenance Envelope

**Required Actions**:

- Define exactly three record types in the stream, observation, reflection, and plan version, and forbid a fourth type from being introduced without a schema version increment.
- Attach to every record a provenance envelope carrying source type, source actor identifier, source record identifier, content hash, authenticated origin flag, trust class, purpose, sensitivity class, and retention class.
- Attach to every record a lineage block carrying derivation depth, cited record identifiers, cited leaf observation identifiers, independent leaf count, and synthetic ancestry fraction, populating depth 0 and empty citation sets for observations.
- Assign every record a stable identifier and a version identifier, and treat observations as immutable after append while reflections and plans carry versions.
- Declare the retrieval-time type filter, naming which record types each consumer of the stream is permitted to receive.
- Freeze the three counterfactual baselines, no memory, bounded recent context, and simple lexical or vector retrieval, as named configurations that later phases measure against.

**Record schema contract**:

```
RECORD_ID
RECORD_VERSION_ID
RECORD_TYPE:            observation | reflection | plan_version
DESCRIPTION_REF
CONTENT_HASH
CREATED_AT
LAST_ACCESSED_AT
EVENT_TIME
PROVENANCE:
  SOURCE_TYPE           authenticated_tool | human_utterance | system_event |
                        agent_completed_action | external_record
  SOURCE_ACTOR_ID
  SOURCE_RECORD_ID
  AUTHENTICATED_ORIGIN  TRUE | FALSE
  TRUST_CLASS
  PURPOSE
  SENSITIVITY_CLASS
  RETENTION_CLASS
LINEAGE:
  DERIVATION_DEPTH
  CITED_RECORD_IDS
  CITED_LEAF_OBSERVATION_IDS
  INDEPENDENT_LEAF_COUNT
  SYNTHETIC_ANCESTRY_FRACTION
SCORES:
  IMPORTANCE_RAW
  IMPORTANCE_COMPONENTS
  IMPORTANCE_SCALE_VERSION
CONFIDENCE
VALIDITY_INTERVAL
EXPIRES_AT
INVALIDATED_BY_ID
```

**Required Outputs**:

- A record type specification naming three types and their permitted transitions.
- A provenance envelope schema with every field marked required or optional.
- A lineage block schema carrying depth, citations, leaf identifiers, and synthetic ancestry fraction.
- Three frozen baseline configurations with their identifiers recorded.

**Quality Checkpoints**:

- Every record type is distinguishable by a single field read without inspecting the description text.
- No record can be appended without an authenticated origin flag resolved to true or false.
- Every baseline configuration is executable against the same evaluation corpus as the full architecture.

***

#### Step 1.2: Define Admissible Observation Classes and the Capture Mode

**Required Actions**:

- Enumerate the admissible observation classes before capture begins, restricting them to externally verified state change, human instruction or correction, consequential tool result, plan deviation, decision outcome, policy or authorisation event, and novel relationship.
- Declare the exclusion list explicitly, covering model reasoning traces, rendering and interface noise, unchanged polling results, duplicate notifications, heartbeat events, and content outside the declared purpose.
- Select event-driven capture as the default, subscribing to state transitions, messages, approvals, errors, and environment deltas, and permit polling only where the source cannot emit events or where elapsed time itself changes the decision.
- Set a per-agent capture ceiling, defaulting to 200 admitted observations per active hour, and route excess to a sampled overflow class rather than dropping it silently.
- Label a corpus of at least 300 candidate events across accept, reject, deduplicate, quarantine, and correct verdicts, spanning every declared class.
- Separate raw evidence from interpretation at the point of capture, so that a tool response is an observation while a characterisation of that response is a reflection candidate.

**Required Outputs**:

- An admissible observation class list with one worked example per class.
- An exclusion list naming every category that never enters the stream.
- A capture mode assignment per source, marked event-driven or polled with a justification for each polled source.
- A labelled admission corpus of at least 300 events with per-class coverage recorded.

**Quality Checkpoints**:

- Every declared class names an observable event type that some source actually emits.
- No source is marked polled without a recorded justification naming why events are unavailable.
- The labelled corpus contains at least 20 examples of each verdict, below which admission precision cannot be estimated.
- Model-authored text appears in no admissible class.

***

#### Step 1.3: Apply Policy, Deduplicate, and Append Under Idempotent Write

**Required Actions**:

- Apply authorisation, sensitivity, and retention policy before any embedding call or importance call, so that rejected content incurs no enrichment cost and leaves no derivative.
- Quarantine content carrying instruction-like structure that originates from a non-authoritative source, and route it to a review queue rather than to the stream, because a memory stream converts observed content into a delayed-execution channel.
- Collapse exact duplicates by source identifier and content hash, and cluster near-duplicates within a bounded window defaulting to 15 minutes, retaining occurrence count with first and last timestamps.
- Append admitted observations idempotently, keyed on source identifier and content hash, so that a retried delivery produces no second record.
- Record an admission decision event for every candidate, admitted or rejected, carrying the reason codes that produced the verdict.
- Measure useful-write precision as the fraction of admitted observations retrieved at least once within 30 days, and tighten the class list where it falls below 0.40.

**Required Outputs**:

- An admission decision log with one entry per candidate event and its reason codes.
- A duplicate cluster index with occurrence counts and time bounds.
- An appended stream in which every record carries a resolved provenance envelope.
- A useful-write precision figure computed over a rolling 30-day window.

**Quality Checkpoints**:

- No embedding or importance call is issued for a record that policy later rejects.
- Retrying an identical source delivery produces zero additional stream records.
- Every rejected candidate carries at least one reason code from the closed vocabulary.
- Useful-write precision is at or above 0.40; below that value the class list is tightened before further capture proceeds.
- Instruction-like content from a non-authoritative source appears in the quarantine queue and not in the stream.

***

### Phase 2: Importance Scoring and Calibration

**Objective**: Replace a single model-assigned poignancy number with a decomposed importance score whose deterministic components bind, whose model-scored component is bounded, and whose scale is calibrated against realized utility rather than assumed.

#### Step 2.1: Decompose Importance Into Named Components

**Required Actions**:

- Decompose importance into six named components, risk, outcome magnitude, novelty, explicit human priority, irreversibility, and expected reuse, and record each component separately alongside the aggregate.
- Score each component on a bounded integer scale from 0 to 10 and record the scale version with the score, so that a later scale change does not silently reinterpret historical records.
- Declare the aggregation function as a weighted sum whose weights sum to exactly 1.0, and default the weights to equal shares of 0.167 across the six components pending calibration.
- Record for every score the scorer type, model identifier, model revision, and prompt version, so that a scorer change is detectable as a distribution shift rather than mistaken for a workload change.
- Forbid the acting model from scoring the importance of its own generated text, because that arrangement rewards dramatic language and inflates the salience of the agent's own output.

**Importance component definitions**:

| Component | Scored by | Definition | Deterministic override available |
| :-- | :-- | :-- | :-- |
| Risk | Deterministic where a severity code exists | Potential harm from acting on or missing the record | Severity code sets a floor |
| Outcome magnitude | Model | Size of the consequence the record reports | None |
| Novelty | Deterministic | Distance from the nearest existing record in the store | Full override |
| Human priority | Deterministic | Explicit pin, escalation, or stated priority by a person | Pin sets the maximum |
| Irreversibility | Deterministic where an action class is declared | Whether the reported action can be undone | Action class sets a floor |
| Expected reuse | Model | Likelihood the record informs a later decision | None |

**Required Outputs**:

- A six-component importance schema with a bounded scale and a versioned scale identifier.
- An aggregation function with declared weights summing to 1.0.
- A scorer provenance record attached to every importance score.

**Quality Checkpoints**:

- Every stored importance score decomposes into six component values and an aggregate.
- Aggregation weights sum to 1.0 within a tolerance of 0.001; a set that does not sum halts scoring.
- No importance score exists without a recorded scale version and scorer revision.
- No record is scored for importance by the model that generated it.

***

#### Step 2.2: Route Scoring Between the Rule Tier and the Model Tier

**Required Actions**:

- Route to deterministic rules every record carrying an explicit severity code, an irreversible action class, a human pin, a contractual deadline, a security incident marker, a verified failure, or a heartbeat classification, and issue no model call for these.
- Route to the model tier only records that deterministic rules leave ambiguous, and cap model-scored records at 30 percent of admitted volume, above which the rule coverage is extended rather than the cap raised.
- Apply deterministic floors and ceilings after every model score, so that a rule-derived floor raises a low model score and a rule-derived ceiling lowers a high one.
- Use the cheapest model tier that meets the agreement threshold in Step 2.3, and escalate to a stronger model only for records whose ambiguity persists after the cheap pass.
- Batch model scoring asynchronously where the record does not gate an immediate decision, and cache by content hash and prompt version so identical content is never scored twice.

**Required Outputs**:

- A routing table mapping every record class to rule tier or model tier.
- A floor and ceiling specification per deterministic rule.
- A model-scored volume fraction measured over a rolling 7-day window.
- A scoring cache keyed by content hash and prompt version.

**Quality Checkpoints**:

- Model-scored records are at or below 30 percent of admitted volume; above that value rule coverage is extended before the next capture window.
- Every deterministic floor and ceiling applies after the model score and is recorded as an override event when it binds.
- Identical content scored twice within one prompt version produces one model call and one cache hit.

***

#### Step 2.3: Calibrate the Scale Against Realized Utility

**Required Actions**:

- Attach a realized utility label to every scored record after a delay defaulting to 30 days, recording whether the record was retrieved, whether it was cited, and whether it materially changed a decision.
- Compare score buckets against those labels and report calibration error per bucket, requiring the observed utility rate to be monotonic in the score bucket.
- Measure inter-run variance by re-scoring a fixed sample of at least 100 records 5 times under a pinned model and prompt, and treat a standard deviation above 1.0 scale point as an unstable scorer.
- Measure agreement against a human-labelled sample of at least 150 records, requiring a rank correlation of at least 0.60 before the scorer gates any retention decision.
- Map raw scores to empirical retention priority buckets rather than treating the raw integer as a probability, because a bounded integer scale is ordinal until calibration proves otherwise.
- Recalibrate on any change of scorer model, scorer revision, prompt version, or admitted class list, and version the resulting scale.

**Required Outputs**:

- A realized utility label set covering at least 500 records per task class.
- A calibration report with per-bucket observed utility rates and a monotonicity verdict.
- An inter-run variance figure per scorer configuration.
- A rank correlation figure against human labels.
- A versioned mapping from raw score to retention priority bucket.

**Quality Checkpoints**:

- Observed utility is monotonic across score buckets; a non-monotonic bucket sequence blocks use of the scorer for retention decisions.
- Inter-run standard deviation is at or below 1.0 scale point; above that value the scorer is pinned to a lower temperature or replaced by rules for the affected class.
- Rank correlation against human labels is at or above 0.60; below that value the model tier is removed from the scoring path.
- The false-high rate on mundane records carrying dramatic wording is at or below 0.10; above that value the model prompt is revised to score consequence rather than expression.

***

### Phase 3: Retrieval Scoring and Weight Calibration

**Objective**: Produce an ordered candidate list from the stream by combining recency, importance, and relevance under a calibrated weight vector, and hand that list to the context assembler without asserting admission authority over it.

#### Step 3.1: Compute the Three Components Deterministically

**Required Actions**:

- Compute recency as exponential decay over elapsed time, defaulting the time basis to event time rather than last-access time, so that repeated retrieval cannot make a record immortal.
- Retain last-access time as a separate weak signal capped at 20 percent of the recency component's contribution, and record both bases so the choice can be ablated.
- Compute relevance as vector similarity between the query embedding and the record embedding under a pinned embedding model and revision, and retain lexical matching alongside it for identifiers, codes, and exact terms.
- Read importance from the stored calibrated aggregate produced in Phase 2 rather than recomputing it at query time, because query-time importance scoring makes the score query-dependent and destroys comparability.
- Apply the policy filter, the type filter, and the validity-interval filter before scoring, and record candidate counts before and after filtering.
- Reject any candidate missing a component score rather than substituting a default, because a defaulted component silently promotes a record whose evidence for that component is absent.

**Retrieval component parameters**:

| Component | Time or model basis | Published default | Replacement procedure |
| :-- | :-- | :-- | :-- |
| Recency | Exponential decay per elapsed hour | Decay factor 0.995 per hour, measured from last retrieval | Fit the half-life to observed staleness per query class in Step 3.3 |
| Importance | Stored aggregate from Phase 2 | Single model integer from 1 to 10 | Six-component calibrated aggregate on a versioned scale |
| Relevance | Cosine similarity over embeddings | Query-to-description similarity | Pinned model plus lexical retrieval for identifiers |
| Normalization | Per-query transform | Min-max across the candidate set | Compare min-max, fixed transform, and reference percentile in Step 3.2 |
| Weights | Linear combination | 1.0 on each of three components | Coordinate sweep against a labelled retrieval set in Step 3.3 |

**Required Outputs**:

- A per-candidate component record carrying raw recency, importance, and relevance scores with their bases and versions.
- Candidate counts before and after policy, type, and validity filtering.
- A rejection list naming candidates dropped for missing component scores.

**Quality Checkpoints**:

- Every scored candidate carries three raw component values, each with a recorded basis or model version.
- No candidate enters ranking with a defaulted or imputed component score.
- The type filter is applied before scoring, so a consumer restricted to observations never pays to score reflections.

***

#### Step 3.2: Normalize the Components and Apply the Weight Vector

**Required Actions**:

- Normalize each component within the candidate pool for the current query before any weighting, because raw component scales are not comparable across components or across queries.
- Evaluate at least three normalization transforms, min-max across the pool, a fixed monotone transform with declared bounds, and a reference-percentile transform fitted to a frozen sample, and select on stability rather than on convenience.
- Measure normalization instability by injecting a single outlier candidate into a fixed pool and recording the resulting rank displacement, rejecting any transform whose median displacement exceeds 2 positions.
- Apply the weight vector as a linear combination of normalized components and retain the raw and normalized component values in the retrieval log, so every rank is reconstructible.
- Emit the ordered candidate list with per-component scores attached and assert no admission verdict, since the deterministic context assembler holds the threshold, the caps, and the token budget.

**Required Outputs**:

- A normalization transform selection record naming the three transforms compared and the instability figures for each.
- A retrieval log carrying raw and normalized component scores, weights, and final score per candidate.
- An ordered candidate list with no admission verdict attached.

**Quality Checkpoints**:

- Normalization occurs within the candidate pool for the current query; a global fixed cutoff applied to unnormalized scores is a defect.
- Median rank displacement under single-outlier injection is at or below 2 positions.
- The ranking stage emits no admission decision, and the assembler never re-runs the scorer.
- The same store, query, weight vector, and filter set reproduce an identical ordered list on repeated execution.

***

#### Step 3.3: Calibrate the Weight Vector and Detect Recency Dominance

**Required Actions**:

- Build a labelled retrieval set of at least 200 query and record pairs spanning every task class in scope, marking for each query which records were decisive.
- Sweep each weight across the range 0 to 2 in steps of 0.25 while holding the others fixed, iterate until no single-coordinate move improves the objective, and select the vector maximising retrieval precision at a fixed decisive-record recall of 0.95.
- Sweep the recency half-life across at least 5 values spanning one order of magnitude, and select the value minimising retrieval of records already superseded by a later record on the same subject.
- Ablate each component to zero in turn and record the change in downstream task success, retaining a component only where its removal degrades a declared slice.
- Measure recency dominance as the fraction of queries in which recency is the largest contributor to the top-ranked record's score, and cap the recency weight, shorten its eligible window, or route continuity queries separately where that fraction exceeds 0.60.
- Audit importance dominance for reflection inflation, checking whether model-authored records occupy a rising share of top-ranked results, and cap the reflection share of any result set at 0.40.
- Report the selected vector as provisional where the labelled set holds fewer than 200 pairs, and forbid a provisional vector from gating a promotion.

**Required Outputs**:

- A labelled retrieval set of at least 200 query and record pairs with decisive-record annotations.
- A weight sweep record with the objective value at every evaluated coordinate.
- A half-life selection record naming the values swept and the superseded-record retrieval rate for each.
- Per-component ablation results against downstream task success.
- Recency dominance and reflection share figures per query class.

**Quality Checkpoints**:

- The labelled set holds at least 200 pairs and covers every task class; a smaller set yields a provisional vector that gates nothing.
- Every retained component degrades a declared slice when ablated; a component whose removal changes nothing is removed.
- Recency dominance is at or below 0.60 per query class; above that value the recency weight is capped before the configuration is promoted.
- Reflection share of any returned result set is at or below 0.40; above that value the type filter is tightened.
- The published weight vector of 1.0 on each component appears only as the day-one configuration and never as a promoted vector.

***

### Phase 4: Reflection Triggering, Generation, and Gated Admission

**Objective**: Produce higher-level inferences from accumulated records under a bounded trigger, and admit them to the stream only through a deterministic gate that resolves every citation, bounds derivation depth, and caps confidence at what the evidence supports.

#### Step 4.1: Evaluate the Reflection Trigger Under Cooldown, Cap, and Budget

**Required Actions**:

- Evaluate a composite trigger rather than a single accumulated-importance threshold, drawing conditions from task boundary reached, unresolved contradiction detected, plan failure recorded, novelty above threshold, and accumulated calibrated importance above threshold.
- Set the accumulated-importance threshold from the deployment's own importance distribution rather than adopting the published value of 150, which was fitted to a scale and an event volume that a production workload does not share.
- Enforce a cooldown of at least 30 minutes of wall-clock time or 20 admitted observations since the previous reflection run, whichever elapses later, and add hysteresis so that a threshold hovering at its boundary does not fire repeatedly.
- Cap reflection runs at 6 per agent-day and cap reflection spend at 15 percent of the agent's total inference cost over a rolling 7-day window, suspending reflection when either cap binds.
- Bound the question window to the smaller of 100 recent eligible records or 8,000 tokens, and record the snapshot identifier so the run is reproducible.
- Log every trigger evaluation, fired or not, with the trigger type, the window bounds, the eligible record count, the measured value, the threshold in force, the remaining cooldown, and the decision reason.

**Required Outputs**:

- A composite trigger specification with a threshold and a version per condition.
- A trigger evaluation log with one entry per evaluation and its decision reason.
- A cooldown and cap state record per agent.
- A reflection spend figure over a rolling 7-day window.

**Quality Checkpoints**:

- Reflection runs are at or below 6 per agent-day; a seventh evaluation in one day returns suppressed regardless of the measured value.
- No reflection run begins with a remaining cooldown above zero.
- Reflection spend is at or below 15 percent of total inference cost; above that value reflection is suspended until the window clears.
- The question window never exceeds 8,000 tokens, and its snapshot identifier is recorded before generation begins.

***

#### Step 4.2: Generate Questions and Cited Candidate Insights

**Required Actions**:

- Generate at most 3 salient questions from the record snapshot, and reduce the count where the snapshot spans fewer than 20 distinct records, because a sparse window cannot support 3 independent lines of inference.
- Issue each question as a retrieval query through Phase 3, and record the retrieval identifiers so the evidence set behind each candidate is reconstructible.
- Generate at most 5 candidate insights per run, and require each candidate to state its claims separately, with the supporting record identifiers attached to each claim rather than to the candidate as a whole.
- Require each candidate to state its scope, its validity interval, its confidence, and any counterexample the generator identified, and reject a candidate that omits any of these fields before the gate is reached.
- Run an explicit counterevidence retrieval for every candidate, querying for records that contradict the claim or that postdate its supporting evidence, and attach the result set to the candidate whether or not contradictions are found.
- Forbid the generator from citing a record it did not receive in a retrieval result for this run, and forbid it from citing a candidate produced in the same run.

**Required Outputs**:

- A question set of at most 3 entries with its generating snapshot identifier.
- A retrieval identifier per question linking to the evidence set that answered it.
- A candidate insight set of at most 5 entries, each carrying claim-level citations, scope, validity interval, confidence, and counterexamples.
- A counterevidence result set attached to every candidate.

**Quality Checkpoints**:

- Every claim in every candidate carries at least one cited record identifier; a claim without one is marked unsupported rather than inheriting a sibling's citation.
- Every candidate carries scope, validity interval, confidence, and a counterevidence result set.
- No candidate cites a record absent from this run's retrieval results.
- No candidate cites another candidate from the same run.

***

#### Step 4.3: Admit or Reject Each Candidate at the Deterministic Gate

**Required Actions**:

- Resolve every cited identifier against the live store, and reject the candidate where any citation fails to resolve, points to an invalidated record, or points to a record outside the agent's authorisation scope.
- Compute derivation depth as one plus the maximum depth among cited supports, and reject any candidate computing to depth 3 or greater, returning a re-derivation instruction naming the leaf observations rather than permitting a summary of the parent.
- Traverse citation edges to enumerate leaf observations, collapse leaves sharing a provenance family, and count the survivors as the independent leaf count.
- Enforce the evidence minimum by claim class, requiring at least 3 independent leaf observations from at least 2 provenance families for a general claim and permitting 1 authoritative observation for a specific event claim.
- Compute the synthetic ancestry fraction and reject any depth-2 candidate above 0.50, and confirm that every depth-1 candidate carries a fraction of exactly 0.
- Detect direct and indirect citation cycles by traversing the proposed edge set against the existing lineage graph, and reject any candidate whose admission would close a cycle.
- Apply the confidence ceiling, setting admitted confidence to the minimum of the stated confidence, the minimum confidence among cited supports, and that minimum reduced by 0.15 per derivation level, with a further cap of 0.80 on any general claim not yet validated against an external outcome.
- Emit a typed verdict per candidate carrying admitted, rejected, or held-for-review, with the reason codes that produced it, and append only admitted candidates to the stream with `record_type` of `reflection`.

**Reflection admission gate criteria**:

| Gate check | Rejection condition | Remedy on rejection |
| :-- | :-- | :-- |
| Citation resolution | Any cited identifier fails to resolve or is invalidated | Reject; regenerate only with a fresh retrieval |
| Authorisation scope | Any cited record is outside the agent's scope | Reject; record an authorisation event |
| Derivation depth | Computed depth is 3 or greater | Reject; re-derive from named leaf observations |
| Independent leaves | General claim supported by fewer than 3 independent leaves | Reject; narrow the claim to a specific event or gather evidence |
| Provenance diversity | General claim drawn from fewer than 2 provenance families | Reject; treat as single-source and narrow the scope |
| Synthetic ancestry | Depth-2 candidate above 0.50, or depth-1 candidate above 0 | Reject; re-derive from observations |
| Citation cycle | Admission would close a direct or indirect cycle | Reject permanently; the claim proves itself |
| Confidence ceiling | Stated confidence exceeds the computed ceiling | Admit at the ceiling and log the reduction |
| Required fields | Scope, validity interval, or counterevidence set absent | Reject; the generator supplies the missing field |
| Contradiction found | Counterevidence retrieval returned a contradicting record | Hold for review; never admit silently |

**Required Outputs**:

- A per-candidate gate verdict with reason codes and the computed depth, leaf count, provenance family count, and synthetic ancestry fraction.
- An admitted reflection set appended to the stream with lineage populated.
- A rejection record retaining the candidate text for audit without indexing it for retrieval.
- A held-for-review queue containing every candidate whose counterevidence retrieval returned a contradiction.

**Quality Checkpoints**:

- No reflection exists in the stream at derivation depth 3 or greater.
- Every admitted reflection resolves 100 percent of its citations at admission time.
- Admitted confidence never exceeds the computed ceiling for any reflection.
- Rejected candidate text is never retrievable by any consumer of the stream.
- Citation support rate, measured as the fraction of claims whose cited records entail the claim under blinded review, is at or above 0.85; below that value reflection is suspended pending prompt revision.
- A candidate rejected for a citation cycle is never resubmitted under a renamed identifier.

***

### Phase 5: Plan Coupling and Bounded Revision

**Objective**: Consume retrieved evidence and admitted reflections in a versioned plan whose assumptions are linked to the records that justify them, and revise that plan only on declared triggers so that revision remains attributable rather than continuous.

#### Step 5.1: Create the Versioned Plan With Linked Assumptions

**Required Actions**:

- Store the plan outside any assembled prompt as a versioned artifact carrying plan identifier, current version, goal, ordered steps, dependencies, assumptions, start and due times, status, owner, tool permission set, and evidence links.
- Record for every step which memory records justify it and which observable outcome marks it complete, so that completion is verified against an observation rather than asserted by the planner.
- Record for every assumption the record identifiers supporting it, the record type of each, and the confidence attached, so that an assumption resting on a reflection is visibly weaker than one resting on an observation.
- Forbid a plan step whose sole justification is a reflection from authorising an irreversible action, and require at least 1 supporting observation for any step in the highest risk class.
- Retain historical plan versions for replay and retrieve only the active version by default, so a superseded commitment cannot rank as current.
- Produce goal-directed plans with deadlines and checkpoints rather than time-blocked daily schedules, since calendar-style decomposition is a property of the simulation setting and not of task work.

**Required Outputs**:

- A versioned plan artifact with an active-version pointer.
- A per-step justification record linking memory identifiers to steps.
- A per-step completion criterion naming the observation that marks it done.
- An assumption register carrying supporting record identifiers, types, and confidences.

**Quality Checkpoints**:

- Every step carries at least one justifying record identifier and one completion criterion.
- No step in the highest risk class rests solely on reflections.
- Retrieval returns the active plan version only; superseded versions are reachable by replay and by no other path.
- Plan artifacts are never appended to the stream as observations.

***

#### Step 5.2: Evaluate Reaction and Replan Triggers

**Required Actions**:

- Evaluate the replan trigger vocabulary on each admitted observation, restricting triggers to failed precondition, contradicting observation above the importance threshold, deadline breach, tool error, human correction, conflicting evidence, and no-progress threshold breach.
- Set the no-progress threshold at 3 consecutive steps producing no completion observation, and escalate rather than replanning a fourth time against the same signature.
- Suppress replanning on observations that fire no declared trigger, because replanning on every perception destroys attribution and multiplies cost without changing the outcome.
- Revise only the affected suffix of the plan where the completed prefix remains valid, classifying every step as completed, invalid, blocked, or still valid before revision.
- Record the trigger, the prior version, the new version, the changed step identifiers, the invalidated assumptions, and a semantic diff score for every revision.
- Cap plan revisions at 5 per active plan per day, and route the sixth trigger to human review rather than to another revision.

**Required Outputs**:

- A trigger evaluation record per admitted observation with its verdict.
- A step classification record covering every step at each revision.
- A plan revision record carrying trigger, versions, changed steps, invalidated assumptions, and semantic diff score.
- A revision count per plan per day.

**Quality Checkpoints**:

- Every revision names exactly one trigger from the closed vocabulary.
- No revision occurs without a fired trigger; a revision without one is a defect and is rolled back.
- Plan revisions are at or below 5 per plan per day; the sixth trigger escalates.
- Replan trigger precision, measured as the fraction of revisions followed by an improvement in the declared outcome, is at or above 0.50; below that value the trigger thresholds are raised.

***

#### Step 5.3: Reconcile Plan-Memory Divergence Before Consequential Action

**Required Actions**:

- Detect divergence before every consequential step by checking whether any cited record is superseded, invalidated, deleted, expired, or outside the current authorisation scope, and whether any step marked complete lacks a completion observation.
- Halt the step on any detected divergence, reconcile the plan against current state, and record the reconciliation before proceeding rather than proceeding with a warning attached.
- Re-authorise every tool action at execution time against the current permission set, treating the plan's recorded permissions as a historical record and never as a live grant.
- Treat remembered instructions as untrusted data, so that no text retrieved from the stream can widen a permission, authorise a tool, or alter the trigger vocabulary.
- Expire plans whose horizon has passed, and forbid retrieval frequency from keeping an expired plan ranked as current.
- Measure stale-plan exposure as the fraction of consequential actions executed while the active plan cited at least one superseded record, and treat any value above 0.02 as a release blocker.

**Required Outputs**:

- A divergence check record preceding every consequential step.
- A reconciliation record naming the divergence class and the correction applied.
- A re-authorisation verdict per executed tool action.
- A stale-plan exposure figure computed over a rolling 7-day window.

**Quality Checkpoints**:

- No consequential step executes without a divergence check recorded in the same transaction.
- Every executed tool action carries a re-authorisation verdict issued at execution time.
- Stale-plan exposure is at or below 0.02; above that value the configuration is not promoted.
- No permission change originates from text retrieved out of the memory stream.

***

### Phase 6: Maintenance, Audit, and Verified Retirement

**Objective**: Hold the stream at a size and a composition the deployment can afford and defend, detect derivation-depth and self-confirmation violations before they accumulate, and propagate correction and deletion through every derivative.

#### Step 6.1: Apply Decay, Archival, and Bounded Eviction

**Required Actions**:

- Assign every record a retention class at admission and an expiry timestamp derived from it, so that retention is a declared property rather than a consequence of storage capacity.
- Apply decay to the recency component only, and never let decay silently delete a record; expiry, archival, and eviction are separate decisions with separate reason codes.
- Archive rather than delete records whose expiry has passed but whose retention class permits retention, keeping them out of the retrieval index while preserving them for lineage resolution.
- Evict a derived artifact, such as an embedding or a summary, only where a durable copy of its source is proven present, and record the proof identifier with the eviction.
- Cap stream growth per completed task and alert where the measured rate exceeds 2.0 times the frozen baseline, because unbounded growth is the default outcome of an unenforced admission policy.
- Compact near-duplicate clusters older than the deduplication window into a single record carrying occurrence count and time bounds, retaining separate instances only where frequency is itself the signal.

**Required Outputs**:

- A retention class assignment and expiry timestamp on every record.
- A lifecycle decision log carrying decision type, prior and new recency scores, policy version, reason codes, and recoverability window.
- An eviction record with the durable-copy proof identifier for every evicted derivative.
- A stream growth figure expressed as records per completed task against the frozen baseline.

**Quality Checkpoints**:

- Every record carries a retention class and an expiry timestamp at admission.
- No record is deleted by a decay computation; decay changes rank and nothing else.
- Every evicted derivative names a durable source copy that resolves.
- Stream growth per completed task is at or below 2.0 times baseline; above that value admission policy is tightened before capture continues.

***

#### Step 6.2: Run the Derivation-Depth and Self-Confirmation Audit

**Required Actions**:

- Traverse the lineage graph on a schedule of at least once every 7 days, computing derivation depth, independent leaf count, provenance family count, and synthetic ancestry fraction for every stored reflection.
- Quarantine within 24 hours any reflection measuring depth 3 or greater, any reflection whose citations no longer resolve, and any reflection participating in a citation cycle, removing each from the retrieval index while preserving it for audit.
- Measure the depth distribution and hold depth-2 reflections at or below 20 percent of stored reflections, since a store whose inference layer is mostly second-order has drifted from its evidence.
- Measure generation loss from leaves to each parent on a sample of at least 50 reflections per audit, testing citation entailment, temporal ordering, exception retention, and answer preservation against the leaf set.
- Measure self-confirmation exposure as the fraction of retrieved evidence that is model-authored across a sample of at least 200 retrievals, and cap that fraction at 0.40.
- Validate a sample of at least 30 reflections per audit against external outcomes such as completed tasks, tool state, human corrections, or authoritative records, and invalidate those the outcome contradicts.
- Report every audit result against the prior audit so that drift is visible as a trend rather than as a single measurement.

**Required Outputs**:

- A depth distribution report covering 100 percent of stored reflections.
- A quarantine list with the violation class and quarantine timestamp per entry.
- A generation loss report over a sample of at least 50 reflections.
- A self-confirmation exposure figure over at least 200 sampled retrievals.
- An external validation result set over at least 30 sampled reflections.

**Quality Checkpoints**:

- Zero stored reflections measure derivation depth 3 or greater after the audit completes.
- Depth-2 reflections are at or below 20 percent of stored reflections; above that value reflection admission is restricted to depth 1 until the share recovers.
- Self-confirmation exposure is at or below 0.40; above that value the reflection share of retrieval results is capped further.
- Citation entailment on the sampled reflections is at or above 0.85; below that value the affected reflections are invalidated in bulk.
- Every audit reports its figures against the prior audit's figures.

***

#### Step 6.3: Propagate Invalidation and Verified Deletion Through Derivatives

**Required Actions**:

- Maintain a dependency graph from every record to its derivatives, covering embeddings, index entries, duplicate cluster members, reflections that cite it, plans that cite it, caches, checkpoints, exports, and evaluation datasets.
- On correction or invalidation of a source record, mark every descendant reflection for re-evaluation within 24 hours, and re-run the Step 4.3 gate against the corrected evidence rather than editing the descendant in place.
- On a deletion request, tombstone the record within 60 seconds so that no serving path returns it, then purge asynchronously and verify across every serving path before closing the request.
- Traverse the dependency graph on deletion so that removal reaches every derivative, and record a deletion status, a verification method, and a verification timestamp per target.
- Retain a deletion lineage record carrying the request identifier, the tombstone identifier, the dependency path, the attempt count, and any exception with its residual risk, so that an incomplete deletion is visible rather than assumed complete.
- Run a deletion test at least once per release, deleting a leaf observation that supports an active reflection and an active plan, and confirming that both descendants are re-evaluated and that neither serves the deleted content.

**Required Outputs**:

- A dependency graph covering every derivative class.
- An invalidation propagation record per corrected source with descendant re-evaluation verdicts.
- A deletion lineage record per request with per-target verification.
- A per-release deletion test result covering reflection and plan descendants.

**Quality Checkpoints**:

- Serving tombstones take effect within 60 seconds of a deletion request; a longer interval is a release blocker.
- Every descendant of a corrected record is re-evaluated within 24 hours through the admission gate rather than edited in place.
- Deletion verification covers 100 percent of derivative classes named in the dependency graph.
- The per-release deletion test passes with zero serving paths returning deleted content.

***

## III. Implementation Guidance for AI Agents

AI agents operating a generative agent memory system must follow systematic protocols ensuring that every record's type and provenance survive every transformation, that inference is admitted only through a deterministic gate, and that a plan never treats a hypothesis as an observed fact. The following guidance translates the six-phase framework into agent-executable instruction.

### A. Structured Execution Protocol

**Component Roles**:

1. **Capture Agent**: Subscribes to declared sources, applies policy, deduplicates, and appends admitted observations idempotently. It may reject any candidate and may never create a record whose source it cannot authenticate.
2. **Scoring Agent**: Assigns importance by routing between deterministic rules and a bounded model call, applies floors and ceilings, and writes the six-component score with its scale version. It never scores text generated by the acting model.
3. **Retrieval Agent**: Applies filters, computes the three components, normalizes within the candidate pool, and emits an ordered candidate list with component scores attached. It holds no admission authority over the context window.
4. **Reflection Proposer**: Generates questions, issues them as retrieval queries, and synthesises candidate insights with claim-level citations, scope, validity interval, confidence, and counterevidence. It proposes only and writes nothing to the stream.
5. **Reflection Gate**: Resolves citations, computes depth, leaves, provenance families, and synthetic ancestry, detects cycles, applies the confidence ceiling, and emits a typed verdict. Its verdict is final and is never appealed to a model.
6. **Planner Agent**: Creates and revises versioned plans, links assumptions to records, evaluates the closed trigger vocabulary, and requests re-authorisation for every tool action at execution time.
7. **Maintenance Agent**: Runs decay, archival, eviction, the depth and self-confirmation audit, invalidation propagation, and verified deletion. It may quarantine any record and may block a release.

**Type Integrity Boundary**: The distinction between an observed record and an inferred record is a hard constraint applying to every component and every interface.

- Carry `record_type`, `derivation_depth`, and `confidence` on every record returned by every retrieval path, including cached and summarised paths.
- Render reflections to a model or a human under an explicit inference label, never in a form typographically or structurally identical to an observation.
- Refuse any request that asks a component to convert a reflection into an observation, and record the refusal as a policy event.
- Where a consumer cannot represent the type distinction, restrict that consumer to observations rather than sending it a mixed set.

**Workflow Execution Pattern**:

```
STATE: Reflection_Admission
INPUTS:
  1. Candidate insight set from Step 4.2 with claim-level citations
  2. Counterevidence result set per candidate
  3. Existing lineage graph and authorisation scope
ACTIONS:
  1. Resolve every cited identifier against the live store
  2. Compute derivation_depth, independent_leaf_count, provenance_family_count
  3. Compute synthetic_ancestry_fraction and traverse for citation cycles
  4. Apply the confidence ceiling and emit one verdict per candidate
VALIDATION:
  - unresolved_citation_count == 0
  - derivation_depth <= 2
  - independent_leaf_count >= 3 IF claim_class == GENERAL
  - provenance_family_count >= 2 IF claim_class == GENERAL
  - synthetic_ancestry_fraction <= 0.50 IF derivation_depth == 2
  - synthetic_ancestry_fraction == 0 IF derivation_depth == 1
  - citation_cycle_detected == FALSE
  - admitted_confidence <= computed_ceiling
TRANSITIONS:
  IF all validations pass THEN next_state = Append_Typed_Reflection
  IF contradiction_found == TRUE THEN next_state = Hold_For_Human_Review
  IF derivation_depth >= 3 THEN next_state = Re_Derive_From_Leaves
  IF citation_cycle_detected == TRUE THEN next_state = Permanent_Rejection
  IF any other validation fails THEN next_state = Reject_With_Reason_Codes
```

**Two-Phase Write Pattern**: Emit the candidate record with its computed lineage fields and its verdict without committing it; confirm the verdict against the validation block while no index write has occurred; commit the append and the index write in the same operation so that a record can never exist in the retrieval index without its lineage.

**Approval Gate**: Human authorisation is required before admitting any reflection whose counterevidence retrieval returned a contradicting record, before any plan step in the highest risk class whose justification rests solely on reflections, before promoting any configuration whose weight vector was selected on fewer than 200 labelled pairs, before raising the derivation-depth bound above 2, and before any deletion exception that leaves residual risk above zero. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the stream, the lineage graph, the active plan pointer, and the calibration manifests in durable storage, since the loop outlives any single context window.
- Pin embedding model, scorer model, prompt versions, policy version, schema version, and index generation in a manifest, and treat any change as a recalibration trigger.
- Write a handoff record at every context boundary naming the active plan version, the open triggers, the last reflection run, and the remaining reflection budget.
- Count reflection and scoring inference against the agent's budget rather than treating background work as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Stream Contract Integrity (After Phase 1)**

- **Automated Check**: Every record carries a resolved provenance envelope and a lineage block; the labelled admission corpus holds at least 300 events with at least 20 per verdict; useful-write precision is at or above 0.40.
- **Agent Action on Pass**: Proceed to importance scoring.
- **Agent Action on Failure**: Halt capture and tighten the admissible class list; no scoring or embedding cost is incurred against an unresolved contract.
- **Human Review Trigger**: Any admitted record whose source could not be authenticated, or any quarantine queue exceeding 50 pending items.

**Checkpoint 2: Importance Calibration (After Phase 2)**

- **Automated Check**: Aggregation weights sum to 1.0; observed utility is monotonic across score buckets; inter-run standard deviation is at or below 1.0 scale point; rank correlation against human labels is at or above 0.60.
- **Agent Action on Pass**: Proceed to retrieval calibration.
- **Agent Action on Failure**: Remove the model tier from the scoring path for the affected class and fall back to deterministic rules.
- **Human Review Trigger**: A false-high rate above 0.10 on mundane records carrying dramatic wording.

**Checkpoint 3: Retrieval Calibration (After Phase 3)**

- **Automated Check**: The labelled retrieval set holds at least 200 pairs; recency dominance is at or below 0.60; reflection share of results is at or below 0.40; every retained component degrades a slice when ablated.
- **Agent Action on Pass**: Permit reflection to be enabled.
- **Agent Action on Failure**: Hold reflection disabled and re-sweep the weight vector; reflection is never enabled over an uncalibrated retrieval path.
- **Human Review Trigger**: A provisional weight vector proposed for promotion, or recency dominance above 0.75 in any query class.

**Checkpoint 4: Reflection Admission Integrity (After Phase 4)**

- **Automated Check**: Zero admitted reflections above depth 2; 100 percent citation resolution at admission; admitted confidence at or below the computed ceiling for every record; citation support rate at or above 0.85.
- **Agent Action on Pass**: Release admitted reflections to the retrieval index.
- **Agent Action on Failure**: Suspend reflection admission and quarantine the run's output; a failing gate is never bypassed to unblock a task.
- **Human Review Trigger**: Any candidate held for contradiction, or a citation support rate below 0.85 across 2 consecutive audits.

**Checkpoint 5: Plan Coupling Integrity (After Phase 5)**

- **Automated Check**: Every revision names one trigger from the closed vocabulary; revisions are at or below 5 per plan per day; stale-plan exposure is at or below 0.02; every executed action carries an execution-time re-authorisation verdict.
- **Agent Action on Pass**: Permit consequential action under the active plan.
- **Agent Action on Failure**: Block consequential action and reconcile the plan against current state.
- **Human Review Trigger**: A sixth revision trigger on one plan in one day, or replan trigger precision below 0.50.

**Checkpoint 6: Maintenance and Audit (After Phase 6)**

- **Automated Check**: Zero stored reflections at depth 3 or greater; depth-2 share at or below 20 percent; self-confirmation exposure at or below 0.40; stream growth at or below 2.0 times baseline; deletion verification covering 100 percent of derivative classes.
- **Agent Action on Pass**: Release the audit report and permit configuration promotion.
- **Agent Action on Failure**: Withhold promotion and restrict reflection admission to depth 1 until the next audit clears.
- **Human Review Trigger**: Any deletion exception with residual risk above zero, or any serving path returning tombstoned content.

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
CONFIGURATION_MANIFEST_ID:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Derivation Depth Inflation and Self-Confirmation**

- **Symptoms**: Depth-2 reflections rise above 20 percent of stored reflections; model-authored records occupy a rising share of retrieved evidence; reflections restate one another in different words; citation entailment falls while confidence stays flat.
- **Diagnostic Steps**: Traverse the lineage graph and recompute depth, independent leaf count, provenance family count, and synthetic ancestry fraction for every stored reflection, then segment the depth distribution by trigger type to locate which trigger produces the deepest output.
- **Resolution Protocol**: Option A, restrict admission to depth 1 until the depth-2 share falls to 20 percent or below. Option B, re-derive the affected depth-2 reflections from their leaf observations and discard the parents. Option C, cap the reflection share of retrieval results below 0.40 so second-order records cannot supply the evidence for third-order ones. Option D, disable the trigger type producing the deepest output and re-enable it only after a held-out task-success improvement is measured.
- **Escalation Trigger**: Any record measuring depth 3 or greater escalates immediately and is quarantined within 24 hours; a request to raise the depth bound above 2 is never granted by an agent and always escalates to human review.

**Error Type 2: Fabricated Observation**

- **Symptoms**: Records typed as observations describe interpretation rather than state; a source payload cannot be produced for a record; a claim appears in the stream that no tool, human, or system event reported.
- **Diagnostic Steps**: Sample observations by source type and attempt to resolve each to its source payload or source record identifier, then check whether the acting model was in the write path for any class that produced unresolvable records.
- **Resolution Protocol**: Option A, remove the acting model from the write path for the affected class so only authenticated tools and explicit human statements create observations. Option B, require a resolvable source payload reference as a schema-level write condition and reject writes lacking one. Option C, reclassify the affected records as reflections and route them through the Step 4.3 gate, admitting only those the gate accepts.
- **Escalation Trigger**: More than 1 percent of sampled observations failing source resolution suspends capture for the affected class; a fabricated observation that reached a consequential action escalates immediately.

**Error Type 3: Recency Dominance and Access Refresh Loops**

- **Symptoms**: Recency is the largest contributor for more than 60 percent of queries; a small set of records appears in most result sets; older decisive evidence stops being retrieved; retrieval share concentrates on records with high access counts.
- **Diagnostic Steps**: Ablate each component to zero and measure the change in retrieval precision, then compare a last-access recency basis against an event-time basis on the same labelled set.
- **Resolution Protocol**: Option A, switch the recency basis to event time and cap the last-access signal at 20 percent of the component's contribution. Option B, cap the recency weight and shorten the eligible window. Option C, route continuity queries to a separate bounded recent-window retriever so they stop competing with evidence queries. Option D, add a diversity constraint that limits how many results may share a provenance family.
- **Escalation Trigger**: Recency dominance above 0.75 in any query class blocks promotion; 3 consecutive calibration cycles failing to bring dominance to 0.60 or below escalates for architecture review.

**Error Type 4: Plan-Memory Divergence**

- **Symptoms**: A plan cites superseded, invalidated, or deleted records; steps are marked complete with no completion observation; revisions exceed the daily cap; replan trigger precision falls below 0.50.
- **Diagnostic Steps**: Resolve every cited record on the active plan version, classify each as live, superseded, invalidated, or deleted, and compare the completed-step set against the completion observation set.
- **Resolution Protocol**: Option A, halt the pending step, reconcile the plan against current state, and record the reconciliation before proceeding. Option B, revise only the affected suffix where the completed prefix remains valid. Option C, expire the plan and re-plan from current state where more than half its assumptions are invalidated. Option D, raise the trigger thresholds where churn rather than staleness is the cause.
- **Escalation Trigger**: Stale-plan exposure above 0.02 blocks promotion; a sixth revision trigger on one plan in one day escalates rather than producing a sixth revision.

**Error Type 5: Poisoned Observation Reaching Action Authority**

- **Symptoms**: Retrieved content contains instruction-like structure; a permission change or tool invocation traces to remembered text rather than to a live grant; a low-frequency source produces records that rank highly across unrelated queries.
- **Diagnostic Steps**: Trace the provenance chain of every record supporting the action, identify records whose origin is non-authoritative, and test whether the same trigger content reproduces the behaviour from a clean store.
- **Resolution Protocol**: Option A, quarantine the source and every record derived from it, then re-run the reflection gate against the remaining evidence. Option B, tighten the admission policy for the affected source class and re-authorise every action the affected records supported. Option C, restrict the affected consumer to observations from authenticated tools only until the source is cleared.
- **Escalation Trigger**: Any permission change or tool invocation traceable to remembered text escalates immediately and halts autonomous action for the agent; this class is never resolved by re-running the same retrieval.

**Error Type 6: Cost and Volume Blowout**

- **Symptoms**: Stream growth per completed task exceeds 2.0 times baseline; importance calls track admitted volume one to one; reflection runs cluster in bursts; queue age and p95 latency rise together.
- **Diagnostic Steps**: Attribute spend across admission, importance scoring, embedding, retrieval, reflection, and planning, then compare admitted volume against useful-write precision to determine whether the cause is over-capture or under-batching.
- **Resolution Protocol**: Option A, tighten the admissible class list and lower the per-hour capture ceiling. Option B, extend deterministic rule coverage so the model-scored fraction falls below 30 percent. Option C, batch asynchronous scoring and embedding and cache by content hash and prompt version. Option D, lower the reflection day cap and lengthen the cooldown.
- **Escalation Trigger**: Reflection spend above 15 percent of total inference cost suspends reflection; cost per successful task exceeding the simple-retrieval baseline across 2 consecutive evaluation cycles escalates for a decision on retiring the architecture.

**Troubleshooting Decision Tree**:

```
AUDIT OR CHECKPOINT DETECTS A PROBLEM
├─ INFERENCE DEFECT
│   ├─ Record at depth 3 or greater → Quarantine in 24h; re-derive from leaves
│   ├─ Depth-2 share above 20 percent → Restrict admission to depth 1
│   ├─ Citation fails to resolve → Reject; regenerate only with fresh retrieval
│   └─ Citation cycle detected → Permanent rejection; never resubmit
├─ EVIDENCE DEFECT
│   ├─ Observation without resolvable source → Reclassify as reflection; gate it
│   ├─ General claim on fewer than 3 leaves → Narrow the claim to a specific event
│   └─ Support from one provenance family → Treat as single-source; cap scope
├─ RETRIEVAL DEFECT
│   ├─ Recency dominance above 0.60 → Cap weight; switch to event-time basis
│   ├─ Reflection share above 0.40 → Tighten the type filter
│   └─ Component missing on a candidate → Reject candidate; never default a score
├─ PLAN DEFECT
│   ├─ Cited record superseded or deleted → Halt step; reconcile before acting
│   ├─ Step complete without observation → Reopen the step; require the observation
│   └─ Sixth revision trigger in one day → Escalate; do not revise again
├─ SECURITY DEFECT
│   ├─ Instruction-like text from untrusted source → Quarantine; do not index
│   └─ Permission change traced to memory → HALT autonomous action; escalate
└─ ECONOMIC DEFECT
    ├─ Reflection spend above 15 percent → Suspend reflection for the window
    └─ Cost per success above baseline twice → Escalate for retirement decision
```

### D. Performance Metrics and Continuous Learning

**Evidence and Inference Quality Metrics**:

- **Useful-write precision**: Admitted observations retrieved at least once within 30 days (target: at or above 0.40; below that value the admissible class list is tightened).
- **Retrieval precision at fixed recall**: Decisive records ranked above the cut at a decisive-record recall of 0.95 (target: above the simple-retrieval baseline by a confidence-bounded margin).
- **Citation support rate**: Reflection claims whose cited records entail the claim under blinded review (target: at or above 0.85).
- **Reflection groundedness**: Admitted reflections surviving external outcome validation (target: at or above 0.80 on the sampled set).
- **Generation loss**: Reflections preserving citation entailment, temporal order, exceptions, and answers relative to their leaves (target: at or above 0.85).
- **Self-confirmation exposure**: Retrieved evidence that is model-authored (target: at or below 0.40).
- **Depth-2 share**: Stored reflections at derivation depth 2 (target: at or below 0.20; depth 3 or greater is always 0).

**Task, Safety, and Economic Metrics**:

- **Task success under policy**: Completed tasks meeting acceptance tests without a policy violation (target: above every frozen baseline by a confidence-bounded margin).
- **Replan trigger precision**: Revisions followed by an improvement in the declared outcome (target: at or above 0.50).
- **Stale-plan exposure**: Consequential actions executed under a plan citing a superseded record (target: at or below 0.02).
- **Source resolution rate**: Sampled observations resolving to a source payload or record (target: at or above 0.99).
- **Deletion verification latency**: Time from request to verified purge across every derivative class (target: tombstone within 60 seconds, verified purge within 30 days).
- **Stream growth**: Records appended per completed task against the frozen baseline (target: at or below 2.0 times baseline).
- **Cost per successful task**: Fully loaded spend across admission, scoring, embedding, retrieval, reflection, planning, and retries divided by accepted successes (target: below the simple-retrieval baseline at matched quality).

**Log-Pattern Failure Detection**: A rising depth-2 share with flat citation support indicates the reflection prompt is summarising rather than inferring. Importance calls tracking admitted volume one to one indicate the deterministic rule tier is not being reached. A small record set appearing in most result sets indicates an access-refresh loop. Revisions clustering immediately after reflection runs indicate reflections are driving churn rather than correction. Rising reflection admission alongside falling task success indicates the inference layer is displacing evidence rather than summarising it. Quarantine volume concentrated in one source class indicates a poisoning attempt rather than a policy misconfiguration.

**Learning and Adaptation Mechanisms**:

- **Delayed utility labelling**: Attach realized utility labels on a 30-day delay and recalibrate importance against them, so the scale tracks the workload rather than the scorer's prior.
- **Ablation before retention**: Retain a component, a trigger type, or a reflection class only where its removal degrades a declared slice under identical budgets and identical accumulated state.
- **Manifest versioning**: Version the weight vector, the decay half-life, the importance scale, the trigger thresholds, the prompt set, and the policy, and evaluate any update on a time-forward split rather than a random split.
- **Threshold recalibration on change**: Recompute every threshold on any change of scorer model, embedding model, prompt version, admitted class list, or traffic mix; the values in this guide are deployment defaults rather than constants.
- **Reflection retirement**: Where reflection does not improve replan quality or held-out task success, remove it from the online path and retain the stream and retrieval alone, since the architecture's components are separable.

**Human-in-the-Loop Boundaries**: Raising the derivation-depth bound above 2, admitting a reflection whose counterevidence retrieval returned a contradiction, authorising a highest-risk plan step justified solely by reflections, granting a deletion exception with residual risk above zero, and promoting a configuration whose weight vector was fitted on fewer than 200 labelled pairs are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs how experience is typed, ranked, abstracted, and consumed, not what the experience is about. Its phases hold wherever an agent accumulates records over a horizon longer than one task, where those records change later decisions, and where a mistaken inference carries a cost.

### 4.1 Cross-Domain Application Patterns

**Clinical care coordination**: Observations are authenticated clinical events such as results returned, orders placed, medications administered, and documented patient statements. The type boundary is the load-bearing control, because a reflection stating a pattern across encounters must never be retrieved as a documented finding. Importance is dominated by deterministic components: severity codes, irreversibility of an intervention, and explicit clinician priority set floors that no model score may lower. Reflection is restricted to depth 1, and every general claim about a standing condition is held for human review rather than admitted, since the evidence minimum of 3 independent leaves is necessary but not sufficient where the claim would enter a care decision. Plans carry completion observations drawn from the record system rather than from the agent's assertion.

**Financial-crime investigation and regulated advisory**: The stream is an audit artifact before it is a retrieval store, so provenance and deletion lineage become deliverables. Retrieval favours authority and lexical identifier matching over semantic proximity, because an account identifier or an instrument code must match exactly. Reflection is valuable here precisely because investigators repeatedly rediscover the same relationship patterns, but every admitted reflection carries its validity interval and its leaf citations into the case file, and confidence is capped so that an inference never enters a filing at the same weight as a transaction record. Approval gates bind before any reflection informs a reportable conclusion.

**Industrial field service and asset maintenance**: Observations arrive as telemetry state transitions, work order completions, and technician statements, and the volume argument for event-driven capture is at its strongest. Unchanged polling results are excluded outright, and near-duplicate clustering with occurrence counts carries the frequency signal that repeated identical readings would otherwise flood the stream to express. Reflection earns its cost by producing failure-mode abstractions across assets, and those abstractions are validated against subsequent failures as external outcomes rather than against rater judgement. Plans are goal-directed with deadlines rather than time-blocked, because dispatch is reversible while a component replacement is not.

**Software engineering and incident response**: The stream holds commits, deployments, test outcomes, alert transitions, and human corrections, all of which arrive as events with authenticated origins. Reflection over accumulated incidents produces the reusable lessons that raw retrieval forces the agent to rediscover, and citation to the specific incidents is what makes a lesson auditable rather than folkloric. Plan coupling is the dominant value: a failed precondition or a tool error revises the remaining plan suffix, and the completed prefix is preserved. Re-authorisation at execution time is mandatory, because a plan drafted before an access change must not act on the permissions it recorded.

**Social-science and organisational simulation research**: This is the setting the architecture was built for, and it is the setting where its published constants come closest to applying. Even here, the constants are starting points: a study adopting them must report them as inherited defaults and run the sensitivity analysis that a validity claim requires. Believability may remain a legitimate secondary measure, but a validity claim requires comparison against real-world data, repeated runs under recorded seeds, sensitivity analysis, and a bounded validity domain declared in advance [4]. Where the simulated subjects are real people, consent, withdrawal, correction rights, synthetic-output labelling, and a prohibition on consequential decisions taken from the proxy are preconditions rather than refinements.

### 4.2 Scale, Risk, and Latency Adaptation

- **Low-risk reversible work**: Collapse the architecture to the typed stream plus retrieval, disable reflection entirely, and retain the type boundary and the admission policy. Reflection is the most expensive and most hazardous component, and it earns its place only where the same synthesis is repeatedly needed.
- **High-risk or irreversible work**: Retain every phase, restrict reflection admission to depth 1, require at least 1 supporting observation for every highest-risk plan step, and bind the approval gate before any action a reflection alone justifies. Abstention is preferred over action on an inference.
- **Strict latency budgets**: Move importance scoring, embedding, and reflection entirely off the foreground path and serve retrieval from precomputed component scores. Where the foreground budget cannot absorb a retrieval call, fall back to the bounded recent-context baseline rather than serving a partially scored candidate set.
- **High-volume low-margin operations**: Extend deterministic rule coverage until the model-scored fraction falls below 10 percent, lengthen the reflection cooldown, and evaluate whether simple retrieval reaches the same task success; where it does, retire the architecture rather than tuning it.
- **Long-horizon autonomous runs**: Persist the stream, lineage graph, active plan pointer, and calibration manifests outside working context, write a handoff record at every context boundary, and re-run the depth and self-confirmation audit at each handoff so that inference drift is detected rather than inherited.
- **Multi-agent deployments**: Treat another agent's message as an observation from a non-authoritative source unless the sender is authenticated and in scope, keep per-agent and per-tenant indexes isolated, and count records relayed through a shared channel as one provenance family regardless of how many agents restate them.

***

## V. Limitations and Considerations

**The evidence base is a simulation, not a production deployment**: The architecture's published support comes from a 25-agent sandbox run over two simulated days, evaluated by human raters ranking believability across progressive ablations [1]. Consequently, no figure in that evaluation predicts factual correctness, task completion, safety, latency, or cost in a task system, and the ablation compared answers drawn from an equivalent accumulated state rather than independently re-run worlds. The mitigation is the frozen baseline requirement in Step 1.1 and the ablation requirement in Step 3.3, which oblige each deployment to demonstrate component value against no-memory, recent-context, and simple-retrieval configurations on its own workload.

**The published constants are defaults fitted to a simulation corpus**: The decay factor of 0.995 per hour, equal component weights of 1, the 1-to-10 importance scale, the accumulated-importance threshold of 150, the 100-record question window, 3 questions, and 5 insights were all fitted to a game world with different record semantics and different staleness dynamics [1]. Carrying them unchanged produces a configuration that is operable but unmeasured. The mitigation is the calibration procedure in Phase 2 and Phase 3 and the prohibition in Step 3.3 on promoting a configuration whose weight vector was fitted on fewer than 200 labelled pairs.

**Reflection remains hazardous even when gated**: The gate enforces citation, depth, leaf count, and confidence, but it cannot detect an inference that is well-cited and wrong. A benchmark evaluating memory systems at the operation level found that fabrications, errors, conflicts, and omissions accumulate during extraction and updating and then propagate into answering [7]. The mitigation is the external outcome validation in Step 6.2, the contradiction hold in Step 4.3, and the rule in Step 5.1 that no highest-risk step rests solely on reflections; residual risk is reduced by these controls rather than eliminated.

**The depth bound of 2 is a deployment default**: The bound was selected so that a single layer of abstraction over observations and a single layer over that abstraction remain available while inferences about inferences about inferences do not. It is not derived from a measured property of language models. The mitigation is the depth distribution audit in Step 6.2, which reports the share at each depth against the prior audit, and the human-review requirement before any deployment raises the bound.

**Thresholds throughout are operable defaults, not measured findings**: The values for useful-write precision, model-scored volume fraction, recency dominance, reflection share, citation support rate, revision caps, and spend caps were chosen to be operable on first deployment. The mitigation is the recalibration requirement in Section III.D, obliging each deployment to recompute every threshold against observed outcomes per task class and to version the result.

**Memory is a delayed-execution channel**: Content admitted to the stream can be retrieved later, enter a reflection, and influence a plan, and a backdoor attack on agent memory has been demonstrated to reach a high attack success rate at a poisoning rate below 0.1 percent of the store [5]. The consequence is that admission policy is a security control and not merely a cost control. The mitigation is the pre-enrichment policy filter and quarantine in Step 1.3, the provenance preservation through every lineage edge, and the execution-time re-authorisation in Step 5.3.

**Privacy exposure scales with capture**: A stream of human interaction accumulates identities, relationships, locations, health information, private messages, and inferred traits, and inference multiplies exposure because a reflection can state something no observation stated. The mitigation is the pre-capture purpose declaration and sensitivity classification in Step 1.2, the dependency graph and verified deletion traversal in Step 6.3, and the prohibition on inferring sensitive traits from behaviour.

**Simulating a real person carries risk beyond data protection**: Person-grounded agents have been shown to replicate survey responses at 85 percent of a participant's own two-week consistency, against 74 percent for demographics-only agents [6], which makes the proxy good enough to be mistaken for the person. The consequence is exposure to impersonation, persuasion, reputational harm, and decisions taken about a person without participation. The mitigation is specific consent for collection, simulation, evaluation, and reuse, rights of inspection, correction, withdrawal, and deletion, labelling of synthetic output, and a standing prohibition on consequential decisions taken from the proxy alone.

**Reproducibility is bounded by the model tier**: Pinning a seed does not make a remote model deterministic, and the retrieval path, the reflection output, and the plan revision all depend on model calls. The consequence is that a replay reproduces the deterministic tier exactly and the model tier only approximately. The mitigation is the manifest requirement in Section III.A, recorded provider responses where exact replay is required, and explicit reporting of residual nondeterminism rather than a claim of full reproducibility.

**Structural conformance is not correctness**: A deployment can satisfy every checkpoint in this guide and still accumulate a store of well-cited, correctly typed, shallowly derived inferences that are collectively unhelpful. The framework detects malformed memory, not misdirected purpose. The mitigation is the primacy of task success under policy in Section III.D and the retirement rule in Step 6.1 and Section 4.2: where the architecture does not beat its baselines on fully loaded cost, it is removed rather than tuned.

***

## VI. Conclusion and Summary

Generative agent memory is a typing discipline before it is a retrieval technique. Its durable contribution is the insistence that experience be preserved as attributable records, that higher-level inference carry pointers to the records beneath it, and that accumulated experience revise a commitment rather than merely narrate it. Its hazard is that the same store holds observations and inferences, serves them through the same retrieval path, and returns them to a consumer that will treat both as established unless the architecture forces the distinction at every interface. A deployment that enforces the distinction will improve as its store grows; a deployment that does not will accumulate confident claims at increasing distance from evidence and will have no mechanism to notice.

A team introducing this architecture should build it in the order the phases give and stop as soon as the measured benefit does. Establish the typed stream and the admission policy first, then a simple retrieval path measured against no-memory and simple-retrieval baselines, then importance and recency added one component at a time with an ablation behind each. Add reflection only after retrieval is calibrated, start it at depth 1 with leaf-only citations and no autonomous publication to high-authority memory, and widen it only where held-out task success improves. Couple plans last, and remove reflection from the online path where it does not improve revision quality. The components are separable, and the discipline lies in retaining only those that pay.

**Key Success Factors**:

- **Typed records with resolvable provenance**: Observation, reflection, and plan remain distinguishable by a single field read at every interface, and no record enters the stream whose origin cannot be authenticated.
- **Inference admitted by a deterministic gate**: The model proposes a reflection and software admits it, resolving every citation, computing derivation depth and independent leaf count, detecting cycles, and capping confidence at what the evidence supports.
- **Bounded derivation depth**: The store terminates at depth 2, the audit quarantines anything deeper within 24 hours, and the remedy for excess depth is re-derivation from leaf observations rather than summarisation of a parent.
- **Calibrated parameters rather than inherited constants**: Every weight, decay rate, importance scale, and trigger threshold is fitted on labelled data from the target workload, and the published values serve only as a day-one configuration.
- **Selective admission as a cost and security control**: Capture is event-driven, policy is applied before enrichment, and the admissible class list is the primary lever against both spend and delayed-execution attack.
- **Measured value against simpler baselines**: Every retained component degrades a declared slice when ablated, and an architecture that does not beat recent context and simple retrieval on fully loaded cost is retired rather than tuned.

By following this guide, AI agents can accumulate experience that later decisions can rely on, produce abstractions a reviewer can trace to evidence, and revise plans against what actually happened rather than against what the store has come to assert.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them, and were not independently re-verified in the course of this conversion except where noted. Entries 1, 4, 5, 6, and 7 were confirmed against their published records during conversion; the remainder are reproduced as the prose source carried them.

**Corpus pointers**:

- `Generative Agents Memory for AI Agents: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the memory stream description, the three-component retrieval function and its published constants, the reflection trigger and reflection tree, the plan and reaction loop, the observation-admission discipline, the parameter calibration guidance, the failure mode inventory, the metadata field inventory, and the release sequence. It carries inline citations to primary literature on generative agents, large-scale social simulation, generative agent-based modelling validation, agent memory poisoning, and judge calibration; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AttentionBasedMemoryRetrieval.md` — companion guidance owning salience scoring and bounded admission into the context window. Phase 3 of this guide stops at an ordered candidate list and hands it to the context assembler that guide governs.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — companion guidance on episode boundaries, episode schema, and outcome labelling, applicable upstream of the observation admission in Phase 1.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on general promotion governance and contradiction handling, applicable wherever batch consolidation rather than inline reflection is the correct mechanism.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — companion guidance on bounded task-scoped state, applicable to the transient status that Phase 5 keeps out of the stream.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — companion guidance on selecting the least powerful adequate memory strategy, applicable to the decision in Section 4.2 on whether this architecture is warranted at all.
- `advanced_task_guides/memory-management/guide_HierarchicalMemory.md` — companion guidance on tiered storage and promotion policy, applicable to the archival and eviction decisions in Step 6.1.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — owns retention policy, the separation of utility forgetting from obligation erasure, and the coverage proof a case requires; applicable to the decay and bounded eviction in Step 6.1 and the verified deletion through derivatives in Step 6.3.
- `advanced_task_guides/memory-management/guide_UnstructuredMemory.md` — owns free-form bodies, chunking, and similarity retrieval under a governed metadata envelope, which is the storage layer beneath this stream; this guide owns the record type system, the importance and retrieval scoring, and the reflection gate that operate over it.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on monitored control and stopping rules, applicable to the trigger evaluation in Step 4.1 and the replan triggers in Step 5.2.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, IV, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Sources carrying the inline markers in Sections I, IV, and V*

1. Park and colleagues, *Generative Agents: Interactive Simulacra of Human Behavior* — https://arxiv.org/abs/2304.03442
2. *AgentSociety* — https://arxiv.org/abs/2502.08691
3. *OASIS* — https://arxiv.org/abs/2411.11581
4. Larooij and Törnberg, *Do Large Language Models Solve the Problems of Agent-Based Modeling? A Critical Review of Generative Social Simulations* — https://arxiv.org/abs/2504.03274
5. *AgentPoison: Red-teaming LLM Agents via Poisoning Memory or Knowledge Bases* — https://arxiv.org/abs/2407.12784
6. Park and colleagues, *LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals* — https://arxiv.org/abs/2411.10109
7. *HaluMem: Evaluating Hallucinations in Memory Systems of Agents* — https://arxiv.org/abs/2511.03506

*Further references transcribed from the prose source*

8. Official Generative Agents repository — https://github.com/joonspk-research/generative_agents
9. *GenSim* — https://arxiv.org/abs/2410.04360
10. *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* — https://arxiv.org/abs/2306.05685
11. *MINJA: Memory Injection Attack* — https://arxiv.org/abs/2503.03704
12. OpenAI, *Batch API guide* — https://developers.openai.com/api/docs/guides/batch
13. Anthropic, *Message Batches* — https://docs.anthropic.com/en/docs/build-with-claude/batch-processing
14. OpenTelemetry, *Semantic conventions for generative AI* — https://opentelemetry.io/docs/specs/semconv/gen-ai/
