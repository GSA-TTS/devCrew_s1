# Context Selection Patterns

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Context selection constitutes the task family of deciding which candidate units cross from durable stores into a bounded context window for one model call, and which are excluded. This guide provides AI agents with an admission procedure rather than a ranking recipe. Ranking orders candidates; admission decides which of them are serialized, and the two are held apart because a scoring function that admits its own top entries has silently taken the budget away from the component accountable for it. The guide declares a partition per candidate type, since instructions, tool definitions, memory records, retrieved evidence, and history turns are not comparable on one scale, and it sizes those partitions against each other before any candidate is scored. It places eligibility and authorization filtering ahead of relevance, so a unit whose eligibility cannot be established is excluded rather than admitted with a warning. It treats tool selection as a distinct problem at scale, naming the catalog size at which retrieval must replace wholesale admission. It requires utilization measurement, because admitting more relevant-looking content is not monotonically better, and it drives the admission policy down when measured admission precision falls below its gate. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that every admitted token carries evidence of its own necessity.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Context selection**: The read-time operation of choosing which units held in durable stores are serialized into the context window for one model call. Selection consumes the outputs of retrieval, memory, tool-registry, and state services; it does not produce them, and it never writes to them.

**Candidate unit**: The atomic element eligible for admission, carrying content or a fetch pointer, a stable identifier, a version, a source, a partition assignment, a trust class, a sensitivity class, an observation time, an expiry time, and a tokenizer-exact token count. A text fragment lacking provenance and token accounting cannot be scored, budgeted, or audited, and is rejected before scoring rather than scored on defaults.

**Candidate pool**: The bounded set of candidate units returned by first-stage retrieval for one partition and one decision, capped by construction. This term is adopted unchanged from the attention-based retrieval guidance in the memory-management category, and pools are formed per partition rather than globally.

**Partition**: A named region of the context budget reserved for one purpose, carrying a maximum token count, a floor where the purpose is protected, an admission rule naming which trust classes may enter, and an eviction order. The definition and the default partition table are adopted from the umbrella context-management guidance and are not restated here.

**Ranking**: The ordering of candidates within one partition by a scalar score. Ranking is a proposal. It changes which unit is considered next; it admits nothing.

**Admission**: The decision that a ranked candidate is serialized into the context package, taken by the context assembler against a partition bound, an admission threshold, and a top-N cap. Admission is the only operation that consumes budget.

**Admission cut**: The point in a partition's ranked list at which the partition's token maximum, score floor, or top-N cap is first violated. Every unit below the cut is excluded with a reason code, and no score raises a unit above the cut.

**Context assembler**: The deterministic component holding the deployed tokenizer, the partition ledger, and the sole authority to place a unit into the outgoing prompt. It is the budget holder. No model call writes into the prompt directly, and no model preference exceeds a partition bound.

**Selection contract**: The declaration, fixed before any candidate is gathered, of the decision to be supported, the requirements an answer or action must satisfy, the partition set with a numeric bound on each, the protected set, the eligibility policy version, the admission thresholds and caps per partition, the sufficiency standard, the round budget, and the terminal states permitted when the budget cannot be satisfied. It extends the context contract defined in the umbrella guidance with the requirement decomposition and the per-partition admission parameters.

**Requirement**: One atomic claim, decision input, or action precondition that the decision needs in order to succeed. Requirements are enumerated before retrieval, and coverage is measured against them rather than against apparent topical relevance.

**Eligibility filter**: The deterministic stage of the admission gate that evaluates tenant, principal, purpose, sensitivity, retention, legal hold, validity interval, integrity, and instruction-versus-data typing. It runs before any relevance computation, and it emits allow, deny, redact, transform, pointer-only, or quarantine.

**Admission threshold**: The per-partition, per-decision normalized score floor a candidate must clear to be eligible for admission, paired with a top-N cap. A floor without a cap admits an entire pool on a degenerate query; a cap without a floor admits noise where no candidate is acceptable. This pairing is adopted unchanged from the memory-management sibling.

**Marginal utility per token**: The estimated contribution of a candidate unit to requirement coverage divided by the tokens it consumes, recomputed after each admission because redundancy and residual coverage change with the admitted set. It is the contested-admission criterion named in the umbrella guidance.

**Negative selection**: The deliberate exclusion of units that are eligible and topically similar but expected to reduce decision quality, including superseded records, mirrored duplicates, prior model assertions carrying no evidence, and units whose marginal utility is negative once token and distraction cost are charged.

**Distractor**: An admitted or candidate unit irrelevant to the decisive requirement that shares entities, dates, terminology, or answer form with the material that is relevant. Plausible distractors damage more than random padding because they compete on meaning.

**Sufficiency verdict**: The typed classification of the admitted set against the requirement list, drawn from sufficient, sufficient with declared uncertainty, insufficient and recoverable, blocked on external input, and insufficient and exhausted. Budget exhaustion never converts into a sufficiency claim.

**Residual gap**: The set of requirements still uncovered after an admission cut, expressed as the requirement identifiers rather than as the original request. Re-query rounds are formulated from the residual gap.

**Tool loadout**: The set of tool definitions admitted into the tool-definition partition for the current step, distinguished from the tool catalog, which is the full authorized inventory the agent may reach through retrieval without serializing.

**Deferred definition**: A tool definition present in the catalog and reachable by search but excluded from the context window until the agent retrieves it, so that catalog size drives retrieval cost rather than prompt cost.

**Navigation unit**: An identifier, path, manifest row, index entry, or summary admitted so the agent knows an object exists and can fetch it, in place of the object itself. Progressive disclosure is the practice of admitting navigation units first and fetching content only against a named residual gap.

**Assembly record**: The immutable per-call log of what was considered, what was admitted, where it was placed, why, and at what token cost. It is the primary artifact this method produces, and the term is adopted from the memory-management sibling rather than renamed.

**Utilization**: The proportion of admitted units that a supported output claim, a tool call, or a state update actually cited or consumed, measured per partition and per admission rule. Utilization is the only evidence that corrects an admission policy.

**Admission precision**: Admitted flexible units judged decisive or supporting for a requirement, divided by all admitted flexible units, computed per partition. It is the gate that drives the admission policy down when unmet.

**Reason code**: A normalised categorical label recorded with every admission, exclusion, transformation, and fetch event, drawn from a closed vocabulary so admission policy is analysable without reading prose logs.

**Protected atom**: A content element that survives every admission cut, eviction, and compaction without loss: the active goal, the success criteria, the standing and safety constraints, the current plan step, the latest value of every open variable, the unresolved error state, the outstanding approvals, and the side-effect ledger. The term and its membership list are adopted unchanged from the working-memory guidance and are never subject to a relevance score.

### 1.2 Selection as Bounded Admission, and the Boundary With Sibling Operations

**Ranking and admission are different decisions**: A ranking function consumes a decision and a candidate pool and emits an ordered list with per-component scores attached. An admission function consumes that ordered list, a partition bound, a threshold, a cap, and a tokenizer, and emits a typed verdict per candidate. Conflating them is the most common defect in deployed selectors, and it presents as a system whose prompt length is whatever the retriever returned. The separation is enforced by construction: the scoring stage holds no write access to the context package, and the assembler never re-runs the scorer. Where the assembler's budget conflicts with the score ordering, the budget wins and the displaced units are logged as excluded with a reason code. This is the same discipline the memory-management sibling specifies for memory records, generalised here across every candidate type.

**A score never admits anything by itself**: Scores are normalised within one partition for one decision before any threshold is applied, because listwise-trained rerankers constrain ordering within a candidate list and not absolute level, so the same numeric score carries no common meaning across decisions. A fixed global cutoff therefore admits too much on one decision distribution and too little on another. Every score floor is paired with a top-N cap, every top-N cap is paired with a floor, and both are subordinate to the partition's token maximum. The assembler is the deterministic budget holder in all three cases.

**Selection is read-time only**: Admitting a unit changes no durable store. Access counts, inferred summaries, and promoted facts are writes and belong to the write-side operation, not to selection. A selector that increments a frequency counter as a side effect of admission has created a feedback loop in which popularity manufactures its own evidence.

**Boundary with the sibling operations in this category**: The umbrella guidance in this category, `guide_ContextManagement.md`, owns the context contract, the partition table, the four failure modes, and the ladder that decides which operation family to enter. This guide owns exactly one of those families. It assumes the budget has been computed and partitioned and specifies what crosses into each partition. It does not specify what is written out of the window, what is compacted once inside it, or how work is split across separate windows; those are the write, compress, and isolate operations, and this guide references them rather than restating them. Where a partition cannot be satisfied by selection because the eligible material genuinely exceeds the bound, this guide returns an overflow verdict and returns control to the umbrella ladder rather than compressing on its own authority.

**Boundary with the memory-management category**: `guide_AttentionBasedMemoryRetrieval.md` specifies scoring components, weight-vector provenance, threshold calibration, and bounded admission for memory records in depth, including the coordinate sweep and the labelled calibration set. This guide adopts that specification for the memory partition rather than deriving a parallel scheme under different names, and extends it to the partitions that guide does not cover. Where a term is defined in both places, the memory-management definition governs.

**Boundary with the knowledge-retrieval category**: Candidate generation, chunking, hybrid lexical and semantic search, query transformation, and reranking implementation belong to that category. This guide treats those services as candidate producers and requires only that each candidate arrive with the metadata named in Section 1.1. A selector that re-implements retrieval inside itself makes both stages untestable.

**The model-internal mechanism and its agent-layer surrogate**: The reason position and admitted volume matter at all is transformer self-attention, which mixes every visible token rather than reading a selected subset. That mechanism is not reachable from the agent layer: an agent cannot read an attention matrix, cannot inspect a hidden state, and cannot direct the serving-side key-value cache. What survives is a surrogate with the same job description and different mechanics, namely explicit eligibility filtering, per-partition scoring, bounded admission, declared placement, and measured utilization, all executed before the call and all recorded. The asymmetry between the two is load-bearing: a unit that scored well externally may still be ignored internally, and a unit with a low external score may still change the answer. Phase 6 exists because of that asymmetry, and no phase in this guide asserts that a high score implies use.

### 1.3 Heterogeneous Candidate Types and Relative Partition Sizing

Instructions, tool definitions, working state, memory records, retrieved evidence, tool results, and conversation turns differ in what makes them valuable, in how their absence fails, and in how their scores are produced. A standing safety constraint has no meaningful semantic similarity to the current request and would rank last on a relevance score; a tool definition is valuable only if the next action needs it, which no retrieval score measures; a conversation turn is valuable for its exact wording rather than its topical fit. Scoring these on one scale and taking a global top-N is the failure this guide exists to prevent, because it reliably drops the cheapest indispensable units in favour of the most similar-looking ones.

The rule is therefore absolute. Each candidate type occupies its own partition. Selection runs independently within each partition against that partition's own components, its own normalization, and its own threshold. No cross-partition comparison of scores is performed, and no unit is admitted into a partition other than the one its type assigns.

**Relative partition sizing**: Partitions are sized against each other before candidates are gathered, in this order and by these rules.

| Sizing rule | Statement | Consequence when breached |
| :-- | :-- | :-- |
| Protected first | Instructions, policy, and the protected atoms are serialized and counted before any flexible partition receives an allocation | Where protected content alone exceeds the input budget, the call is not issued and the umbrella ladder is entered |
| Floors before shares | Every partition with a protected purpose receives its floor before any partition receives a percentage share | A partition whose floor cannot be met blocks the call rather than being silently zeroed |
| Shares from the remainder | The remaining budget is divided by the default shares in the umbrella partition table, adjusted per task class | An adjustment without a recorded task class and a measured utilization basis is rejected |
| Task-class skew is bounded | A task class may move any partition's share by at most 15 percentage points from the default | A larger move requires a recalibration record naming the utilization evidence that justifies it |
| Borrowing is one-directional and logged | Unused capacity may be lent only to partitions declared as borrowers in the contract, never to instructions or output reserve | An unlogged borrow is a contract violation and fails the assembly check |
| No partition is filled for its own sake | A partition under its maximum is left under it where no candidate clears the threshold | Filling spare capacity with sub-threshold units is a distraction defect, not thoroughness |

**Sizing defaults by task class**: The shares below are deployment defaults, expressed as adjustments to the umbrella table rather than as independent values, and are recalibrated per deployment under Phase 6. A code-modification task shifts toward working state and tool definitions, since the decisive material is the current file state and the next action's schema. A research synthesis task shifts toward retrieved evidence and away from tool definitions, since the decisive material is source text and one or two retrieval tools suffice. A long-running conversational task shifts toward conversation history and memory, since the decisive material is prior commitment and correction. An incident-response task shifts toward tool results and freshness-gated evidence, since material older than the incident is usually a distractor. In every case the instruction partition and the protected atoms are unchanged, because their size is set by policy rather than by task.

### 1.4 Execution Tier Partition

Selection is a hybrid capability, and its production failures are overwhelmingly misassignments of work across three execution tiers. The partition below is load-bearing rather than descriptive: it establishes what may never be delegated to model inference and what may never be reduced to a rule.

**Deterministic tier**: Work requiring exactness, reproducibility, auditability, or scale that model inference cannot supply. Partition declaration and budget allocation, eligibility and authorization filtering, freshness and supersession evaluation, hash-based and near-duplicate deduplication, tokenizer-exact counting, per-partition score normalization, threshold and cap application, the admission cut, assembly order, cache-boundary emission, assembly-record logging, and utilization measurement all sit here. The deterministic tier may exclude any candidate for any recorded reason and is never overridden by a model verdict.

**Model tier**: Work requiring open-vocabulary judgement that no deterministic rule covers. Requirement decomposition into atomic claims and preconditions, relevance and decisiveness adjudication over an already eligible reduced pool, detection of conflict between differently worded records, interpretation of tool descriptions against a capability need, and the drafting of a residual-gap query all sit here. The model tier proposes; it never commits.

**Hybrid tier**: Work in which a model proposes and software verifies. Admission, sufficiency assessment, conflict resolution, and citation verification sit here, and each names an authority holder.

Two rules govern every disagreement. A model preference never exceeds a partition bound: an assertion that a unit is important is an input to ranking and never an exemption from accounting. A unit whose eligibility cannot be established is excluded rather than admitted with a warning: an unresolvable authorization, tenancy, validity, or integrity check is a denial, not an uncertainty to be carried into the prompt.

**Tier assignment and authority**:

| Work unit | Tier | Authority when tiers disagree |
| :-- | :-- | :-- |
| Partition declaration, budget allocation, and floors | Deterministic | Deterministic; a model estimate of remaining budget is advisory only |
| Requirement decomposition into atomic requirements | Model | Model proposes; a schema validator rejects requirements carrying no verifiable coverage test |
| Authorization, tenancy, sensitivity, and purpose filtering | Deterministic | Deterministic; a relevance verdict never overrides a denial or an unresolved check |
| Freshness, validity interval, and supersession evaluation | Deterministic | Deterministic; a model claim that a value is current is not evidence |
| Exact and near-duplicate clustering | Deterministic | Deterministic |
| Recency, authority, and frequency component computation | Deterministic | Deterministic |
| Semantic relevance and decisiveness adjudication | Model | Model, bounded by per-partition normalization and a top-N cap |
| Capability-to-tool interpretation from descriptions | Model | Model proposes; the authorization filter and the loadout cap bind |
| Conflict detection across differently worded units | Model | Model proposes the conflict group; a deterministic schema check rejects malformed groups |
| Conflict resolution and canonical selection | Hybrid | Deterministic; the declared authority-and-time policy decides, or the conflict is admitted unresolved and disclosed |
| Admission of a scored candidate | Hybrid | Deterministic; the assembler's partition bound and threshold bind over the score ordering |
| Assembly order and placement of protected atoms | Deterministic | Deterministic; ordering is policy, not a model preference |
| Sufficiency verdict | Hybrid | Deterministic for structured preconditions; model claim-level reasons required for the remainder, and exhaustion is never reported as sufficiency |
| Utilization and citation-span verification | Hybrid | Deterministic; a cited span that does not resolve in the admitted text is unsupported regardless of the model's claim |
| Admission-policy correction and threshold recalibration | Deterministic | Deterministic |

Three handoffs carry the method's risk and must be instrumented explicitly. The retrieval-to-eligibility handoff passes a bounded pool with per-candidate metadata and receives an eligibility verdict per candidate; a candidate missing metadata is rejected before scoring rather than scored on defaults. The scoring-to-assembly handoff passes a per-partition ordered list with normalized scores and receives a typed admission verdict; the assembler never re-runs the scorer. The assembly-to-measurement handoff passes the assembly record and the model output and receives utilization and admission-precision figures; measurement never modifies the assembly it is measuring.

***

## II. Operational Framework: Budgeted Admission Across Heterogeneous Context Partitions

The framework produces two artifacts: the assembly record, emitted once per model call, and the admission-policy record, emitted once per calibration cycle. Phases 1 through 5 execute on every call once calibrated, with Phase 1 collapsing to a lookup of the current selection contract at runtime. Phase 6 executes on an evaluation cadence and returns control to Phase 3 when a gate fails or a configuration fact changes.

### Phase 1: Selection Contract and Partition Budget Declaration

**Objective**: Fix the decision to be supported, the requirements that constitute coverage, and the numeric bound on every partition before any candidate is gathered, so that admission is judged against declared targets rather than against apparent relevance.

#### Step 1.1: Declare the Decision and Decompose It Into Requirements

**Required Actions**:

- Name the exact decision the context must support, drawn from answer, plan, tool choice, action, verification, or delegation, and record the parent trace, principal, tenant, model revision, tokenizer, and contract version.
- Decompose the decision into atomic requirements, each stating one claim, decision input, or action precondition, and each carrying a coverage test that is machine-evaluable or assigned to a named role.
- Mark every requirement already satisfied by protected content, so that retrieval is not commissioned for material already present.
- Declare the evidence standard per requirement class, stating whether coverage requires a cited unit identifier, a quoted span, corroboration from an independently provenanced source, or model synthesis.
- Declare the authority ordering that resolves conflicting units, naming source precedence and recency precedence separately, since a newer unit from a weaker source is not automatically canonical.

**Required Outputs**:

- A decision specification with identity fields and contract version.
- A requirement list with a coverage test and an evidence standard per entry.
- A satisfied-by-protected-content marking across the requirement list.
- An authority ordering statement separating source precedence from recency precedence.

**Quality Checkpoints**:

- Every requirement carries a coverage test that a reviewer can evaluate as covered or uncovered.
- No requirement is stated as a topic; each names a claim, an input, or a precondition.
- The requirement list is non-empty, and a decision producing an empty list is routed to direct execution without selection.

***

#### Step 1.2: Allocate Partition Budgets, Floors, and Caps

**Required Actions**:

- Retrieve the context budget and default partition table from the governing context contract rather than recomputing them, and record the contract version in force.
- Serialize the protected set and the instruction partition first, count them with the deployed tokenizer, and subtract them before any flexible partition receives an allocation.
- Assign every flexible partition a token maximum, a floor where its purpose is protected, an admissible trust-class list, and a top-N cap, applying the task-class adjustment within the 15 percentage point bound stated in Section 1.3.
- Declare the borrowing rules, naming which partitions may lend, which may borrow, and the maximum borrowable fraction, defaulting to no more than 25 percent of the lending partition's unused capacity.
- Reserve a re-query allowance of at least 10 percent of the flexible budget where the decision is classified as iterative, and record zero where it is classified as single-pass.

**Required Outputs**:

- A partition ledger with maximum, floor, trust-class list, and top-N cap per partition.
- A protected-set token count computed with the deployed tokenizer.
- A declared borrowing rule set with numeric bounds.
- A re-query reserve figure with its iterative or single-pass classification.

**Quality Checkpoints**:

- Partition maxima plus the output reserve plus operational headroom sum to no more than 100 percent of window capacity.
- Every token figure derives from a tokenizer count on serialized text, never from a character-count estimate.
- No partition floor is set below the size of the protected atoms it is declared to carry.

***

#### Step 1.3: Freeze Baselines and Declare the Admission Gates

**Required Actions**:

- Freeze at least 3 counterfactual baselines for later comparison: protected content only, a fixed recency window with no scoring, and unfiltered top-N retrieval at the same token cost.
- Declare the numeric gate for admission precision, item-level utilization, requirement coverage, conflict disclosure, unauthorized-admission incidence, and per-decision selection latency and cost.
- Record the consequence attached to each gate, naming whether a breach blocks promotion, forces a rollback of the admission policy, or raises a review.
- Version the admission policy, comprising thresholds, caps, component weights, and partition shares, and bind that version into every assembly record it produces.

**Required Outputs**:

- A frozen baseline set of at least 3 named configurations.
- A gate table with a numeric target and a stated consequence per metric.
- An admission-policy version identifier bound into the assembly record schema.

**Quality Checkpoints**:

- Every declared gate carries both a number and a consequence.
- Unauthorized admission and trust-class escape carry a zero-tolerance gate and an automatic rollback consequence.
- The baseline set includes at least 1 configuration that admits more tokens than the proposed policy, so that over-admission is falsifiable.

***

### Phase 2: Candidate Generation and Eligibility Filtering

**Objective**: Produce a bounded, fully attributed candidate pool per partition and reduce it to the units that are eligible for the current principal, purpose, and validity window, before any relevance judgement is made.

#### Step 2.1: Assemble Bounded Per-Partition Candidate Pools

**Required Actions**:

- Map every uncovered requirement to the partitions that could satisfy it, and commission candidate generation only against those partitions.
- Query only authorized source adapters, and request metadata and navigation units before full payloads for any object above 2,000 tokens.
- Cap each partition's pool by construction at no more than 5 times its top-N cap, and stop gathering when the cap, the round latency bound, or the round cost bound is reached.
- Require every returned candidate to carry the metadata named in Section 1.1, and reject candidates missing any required field before scoring rather than scoring them on default values.
- Record per candidate the generating query, source adapter, initial rank, retrieval timestamp, latency, and monetary cost, together with the pool revision identifier.

**Required Outputs**:

- One bounded candidate pool per partition with a recorded cap and an achieved size.
- A per-candidate provenance record with generation query and cost fields.
- A rejected-on-metadata list with the missing field named per entry.

**Quality Checkpoints**:

- Every pool size is at or below its declared cap, and no pool was gathered for a partition with no uncovered requirement mapped to it.
- Every candidate carries a tokenizer-exact token count computed on its serialized form, including wrappers and citation metadata.
- A source adapter that returned an error is recorded as unavailable rather than as an empty result.

***

#### Step 2.2: Apply Authorization, Freshness, and Trust Gates Before Relevance

**Required Actions**:

- Evaluate tenant, principal, purpose, sensitivity, retention, legal hold, and deletion state for every candidate, and emit allow, deny, redact, transform, pointer-only, or quarantine with a policy version attached.
- Evaluate the validity interval and supersession state, and deny any candidate past expiry or superseded by a newer authoritative version of the same unit.
- Assign a trust class and an instruction-versus-data type to every surviving candidate, and deny admission into the instruction partition to any unit not originating in trusted configuration.
- Scan externally sourced candidates for instruction-shaped content, and mark detected spans as data rather than removing the candidate, so the evidence survives while its authority does not.
- Exclude any candidate whose eligibility check cannot be completed, recording the unresolved check as the reason code, and never carry an unresolved check forward as an admitted unit with a warning.
- Create a new candidate with its own identifier and provenance for every redaction, summarisation, or pointer-only transformation, rather than mutating the original in place.

**Required Outputs**:

- An eligibility verdict per candidate with policy version and reason code.
- A trust-class and instruction-versus-data label per surviving candidate.
- A transformed-candidate set carrying independent identifiers and provenance links to their originals.

**Quality Checkpoints**:

- No relevance score exists for any candidate that has not passed the eligibility filter.
- Zero candidates are admitted with an incomplete or unresolved eligibility check.
- Every transformation produces a distinct identifier, so that the transformed unit's utilization is measurable separately from the original.

***

#### Step 2.3: Collapse Duplicates and Form Conflict Groups

**Required Actions**:

- Cluster exact duplicates by content hash and near-duplicates by similarity above a declared threshold of 0.95, and retain one representative per cluster with pointers to the alternates held outside the window.
- Distinguish independent corroboration from redundancy by comparing provenance chains, and never collapse two units whose provenance is independent merely because their embeddings are close.
- Refuse to collapse units differing in entity, time period, jurisdiction, version, or confidence level, and split the requirement instead where the difference explains the disagreement.
- Detect candidates asserting mutually inconsistent values for the same subject, field, scope, and validity interval, and form a conflict group carrying authority and time metadata for each member.
- Reserve tokens for the conflict groups the contract requires to be disclosed, so that a conflict is not eliminated by the admission cut that follows.

**Required Outputs**:

- A duplicate-cluster map with one retained representative and a pointer list per cluster.
- An independence marking distinguishing corroborating units from redundant ones.
- A conflict-group inventory with authority and time metadata per member and a reserved token allocation.

**Quality Checkpoints**:

- No conflict group is reduced to a single member by deduplication.
- Every collapsed cluster names the criterion that established equivalence, and no cluster spans differing entities, times, jurisdictions, or versions.
- Reserved conflict tokens are subtracted from the partition maximum before the admission cut runs, not after.

***

### Phase 3: Per-Partition Candidate Scoring

**Objective**: Produce an ordered, explainable candidate list inside each partition using components appropriate to that partition's candidate type, without ever comparing scores across partitions.

#### Step 3.1: Compute and Log Per-Partition Score Components

**Required Actions**:

- Compute each partition's declared components separately, log each component separately, and never log only a composite score, since a score whose components cannot be recovered cannot be diagnosed when admission goes wrong.
- Apply the memory-management sibling's component inventory unchanged for the memory partition, comprising semantic relevance, lexical and identifier match, adjudicated relevance, recency, importance, authority, access frequency, and the redundancy penalty.
- Score retrieved evidence on requirement coverage, source authority, freshness relative to the fact's volatility, provenance independence, and the redundancy penalty against the provisionally admitted set.
- Score tool definitions on capability match to the next action, least privilege, side-effect class, health, and schema token cost, and never on semantic similarity to the user's phrasing alone.
- Represent every missing component with an explicit missing-value indicator rather than substituting zero, since a silent zero is indistinguishable from a measured absence.

**Required Outputs**:

- A per-candidate component vector with one entry per declared component and explicit missing-value indicators.
- A component-weight vector version recorded per partition.
- A per-partition ordered list with composite scores and their component decomposition attached.

**Quality Checkpoints**:

- No composite score is recorded without its component decomposition.
- No partition's list contains a candidate scored under another partition's component set.
- Every missing component is flagged, and no missing component was replaced by a default value.

***

#### Step 3.2: Normalize Within Partition and Set Thresholds and Caps

**Required Actions**:

- Normalize every component within the partition's pool for the current decision before any threshold is applied, using min-max for bounded components and z-score for reranker outputs.
- Apply an admission threshold consisting of a score floor and a top-N cap for every partition, and reject any configuration carrying one without the other.
- Set the initial weight vector from one of exactly 3 admissible origins, naming the origin in the assembly record: a published default carried unchanged on first deployment, a coordinate sweep over a labelled admission set of at least 200 pairs, or a ranker fitted to at least 2,000 logged admissions on a time-forward split.
- Subtract a redundancy penalty against the provisionally admitted set after each admission rather than once at the start, since novelty and residual coverage change with every unit admitted.
- Bound the top-N cap for every partition at a value the partition's token maximum can accommodate at the observed median unit size, so that the cap and the bound cannot contradict each other.

**Required Outputs**:

- Per-partition normalized scores with the normalization method recorded.
- A threshold and cap pair per partition with the weight-vector origin named.
- A recomputed redundancy penalty per admission iteration.

**Quality Checkpoints**:

- No global cutoff is applied across partitions, and no partition uses an absolute score level carried over from a prior decision.
- Every floor is paired with a cap and every cap with a floor.
- Where the weight vector is a published default carried unchanged, the assembly record marks it as a deployment default rather than a calibrated value.

***

#### Step 3.3: Score Conversation History Under Recency and Relevance

**Required Actions**:

- Lift every protected atom out of the history partition before scoring, admitting the active goal, the binding constraints, the current plan step, the latest value of every open variable, the unresolved error state, the outstanding approvals, and the side-effect ledger regardless of their age or position.
- Score the remaining turns on unresolved commitment, correction or supersession of an earlier instruction, definition of a referent needed to interpret the current request, exact wording required for consent or a negotiated constraint, and open question, rather than on position in the transcript.
- Apply recency as a bounded component rather than as an ordering, capping its weight at no more than 30 percent of the history partition's composite score, so that a socially recent turn cannot displace an older binding constraint.
- Exclude turns whose content is fully captured by the durable state projection, together with social turns with no task effect, superseded plans, repeated explanations, abandoned branches, tool chatter already reflected in validated state, and prior model assertions carrying no evidence.
- Prefer a compact state projection plus the specific source turns needed for exact language or provenance over a contiguous recency window, and record which turns were retained for wording rather than for content.

**Required Outputs**:

- A protected-atom extraction admitted outside history scoring.
- A scored turn list with the retention reason named per retained turn.
- An exclusion list with reason codes covering every dropped turn.

**Quality Checkpoints**:

- No protected atom is dropped by any history policy at any transcript length.
- Recency contributes no more than 30 percent of any history composite score.
- Every retained turn names a retention reason other than recency alone.

***

### Phase 4: Tool Selection at Scale

**Objective**: Hold the tool-definition partition to a working loadout retrieved against the next action, rather than admitting a catalog whose size degrades both the budget and the model's selection accuracy.

#### Step 4.1: Classify the Catalog and Choose the Tool Selection Regime

**Required Actions**:

- Count the authorized tool catalog for the current principal and serialize its definitions to obtain an exact token total, rather than estimating from tool count alone.
- Apply the regime rule: admit the full catalog only where it holds fewer than 10 tools and its serialized definitions total under 10,000 tokens; otherwise operate a retrieval-based loadout.
- Treat 30 tools as the point above which wholesale admission is prohibited regardless of token total, since reported selection accuracy degrades once available tools exceed the 30 to 50 range [22], and treat an aggregation of multiple servers, commonly 200 or more tools, as requiring retrieval without further analysis.
- Record the regime decision, the catalog size, the serialized token total, and the model revision in the assembly record, since the accuracy threshold is model-specific and a model change is a re-evaluation trigger.
- Retain between 3 and 5 always-resident definitions for the tools invoked in the majority of decisions in the task class, and defer every other definition.

**Required Outputs**:

- A catalog census with tool count and serialized token total.
- A regime verdict of full admission or retrieval-based loadout with the triggering rule named.
- An always-resident tool list of 3 to 5 entries with the invocation-frequency evidence supporting it.

**Quality Checkpoints**:

- The regime verdict follows the stated thresholds, and any deviation carries a recorded justification and a measured selection-accuracy figure.
- The always-resident list holds no more than 5 entries, and every entry is justified by observed invocation frequency rather than by assumption.
- No tool definition is admitted for a principal not authorized to invoke it, since a visible definition is itself a disclosure.

***

#### Step 4.2: Retrieve and Admit a Bounded Working Loadout

**Required Actions**:

- Derive the required capability from the next action, drawn from search, read, calculate, execute, communicate, mutate, or verify, before any tool is retrieved.
- Filter the catalog by authorization, environment, side-effect class, data boundary, health, and version, and score only the filtered remainder.
- Retrieve definitions by lexical or semantic match over tool names, descriptions, argument names, and argument descriptions, using namespace prefixes so that one query resolves a related group.
- Admit no more than 5 retrieved definitions per retrieval round by default, expanding the limit only where the action demonstrably requires more, and penalise overlapping tools so that the least-privileged tool able to complete the action is preferred.
- Reopen selection after each observation where the next required capability changes, and admit the newly required definitions rather than carrying the whole prior loadout forward.
- Bind authorization again at execution time, since a definition admitted under a selection-time check may be invoked after the underlying permission has changed.

**Required Outputs**:

- A capability statement for the next action.
- A retrieved loadout of no more than 5 definitions per round with retrieval query and match scores recorded.
- An execution-time authorization verdict per invoked tool, recorded separately from the selection-time verdict.

**Quality Checkpoints**:

- The tool-definition partition remains within its token maximum at every round, and no round admits more than its declared retrieval limit.
- Every admitted definition traces to a stated capability requirement for the current or next action.
- No retrieved tool description is treated as instruction; descriptions are indexed as data and carry no authority to raise a unit's trust class.

***

#### Step 4.3: Maintain Catalog Freshness and Measure Selection Outcomes

**Required Actions**:

- Scope every cached catalog listing to the authorization context that produced it, and refresh on a list-change notification, a version mismatch, a permission change, or the declared cache lifetime, whichever occurs first.
- Canonicalize catalog ordering deterministically so that identical inputs produce identical prompts and the stable prefix is not invalidated by listing order alone.
- Record server identity, tool identity, schema hash, list revision, and authorization decision for every admitted definition.
- Measure tool selection outcomes per decision, computing retrieval hit rate at the declared limit, invoked-tool execution success, and missed-tool regret, defined as decisions in which an authorized tool that would have succeeded was never retrieved.
- Add a lexical alias or an improved description for every missed tool identified, and re-measure rather than raising the retrieval limit as a first response.

**Required Outputs**:

- A catalog cache record with scope, revision, and refresh trigger.
- A per-decision tool outcome record with hit rate, execution success, and missed-tool regret.
- An alias and description revision list derived from measured misses.

**Quality Checkpoints**:

- Retrieval hit rate at the declared limit meets or exceeds 0.90 for the task class; below that figure the descriptions are revised before the limit is raised.
- Missed-tool regret is at or below 2 percent of decisions in the task class, and a higher figure blocks promotion of the tool selection policy.
- No catalog listing is served across an authorization boundary, and a permission change invalidates the listing immediately rather than at expiry.

***

### Phase 5: Bounded Admission, Sufficiency, and Assembly

**Objective**: Convert per-partition ranked lists into a serialized context package that fits the declared bounds, covers the requirement list or declares that it does not, and records every inclusion and exclusion.

#### Step 5.1: Execute the Admission Cut Under the Deterministic Budget Holder

**Required Actions**:

- Admit protected atoms and partition-floor units first, outside score competition, and charge their tokens to their partitions before any scored candidate is considered.
- Iterate each partition independently, admitting the highest marginal utility per token among candidates that clear the floor, fit the remaining partition tokens, and satisfy their dependency requirements, recomputing redundancy and residual coverage after each admission.
- Stop each partition at its admission cut, defined as the first violation of its token maximum, score floor, or top-N cap, and exclude every remaining candidate with a reason code drawn from the closed vocabulary.
- Attempt bounded local improvement at most twice per partition, swapping one large admitted unit for smaller units that raise requirement coverage at equal or lower token cost, and record each swap.
- Serialize the provisional package and recount with the deployed tokenizer, since wrappers, delimiters, role markers, and citation metadata are not free, and re-run the cut where the recount exceeds any bound.
- Return an overflow verdict carrying the per-partition ledger where a floor cannot be satisfied after every partition has run its cut, and return control to the governing context-management ladder rather than truncating.

**Required Outputs**:

- An admitted set per partition with admission order, token positions, and marginal utility recorded.
- An exclusion list carrying a reason code and the binding constraint per excluded candidate.
- A serialized token recount per partition and a typed verdict of pass or overflow.

**Quality Checkpoints**:

- No partition exceeds its token maximum or its top-N cap in the recounted package.
- Every exclusion carries a reason code from the closed vocabulary, and no candidate is excluded silently.
- No unit crosses a partition boundary to consume another partition's capacity except through a logged borrow within its declared bound.

***

#### Step 5.2: Assess Sufficiency and Bound the Re-Query Loop

**Required Actions**:

- Evaluate every requirement against the admitted set, asking whether it is covered, whether the supporting unit meets the declared evidence standard, whether it is current for the fact's volatility, whether required dependencies are present, and whether corroboration is independent where required.
- Emit exactly 1 sufficiency verdict from the 5 declared classes, requiring claim-level reasons for every uncovered requirement and using deterministic checks for structured preconditions rather than a model assertion.
- Formulate any re-query from the residual gap identifiers rather than from the original request, and change the source, formulation, entity, time range, or dependency path where the prior route returned nothing eligible.
- Bound the loop at no more than 3 re-query rounds by default, and stop earlier where incremental requirement coverage across a round falls below 5 percent, where the same query returns no novel eligible candidate, or where the re-query reserve is exhausted.
- Record an exhaustion stop as insufficient and exhausted, never as sufficient, and never evict an admitted unit covering a requirement in order to fund a speculative round without recording the trade.

**Required Outputs**:

- A requirement coverage table with a covered or uncovered verdict and a supporting unit identifier per entry.
- One sufficiency verdict with claim-level reasons for every uncovered requirement.
- A re-query log with round count, query change, incremental coverage, and stop reason.

**Quality Checkpoints**:

- Exactly 1 sufficiency verdict is emitted per decision, drawn from the 5 declared classes.
- No round repeats a prior query without a material change to source, formulation, entity, time range, or dependency path.
- A stop caused by budget or round exhaustion is never recorded as sufficiency, and the downstream behaviour is a qualified partial result, a request for input, or an abstention.

***

#### Step 5.3: Fix the Assembly Order and Emit the Assembly Record

**Required Actions**:

- Serialize partitions in the declared order: stable policy and instructions, tool definitions for the next action, working state and protected atoms, admitted memory and evidence grouped by requirement, conflict groups with authority and time adjacent, then the current request.
- Place prerequisite units before dependent units within a partition, keep each claim adjacent to its citation and qualifier, and order tied candidates by a deterministic canonical key so that identical inputs produce identical prompts.
- Declare the cache boundary separating the stable prefix from the decision-specific suffix, expressed as a provider breakpoint where one exists and as a prefix hash in the assembly record in every case, and never retain an irrelevant unit inside the prefix to preserve a cache hit.
- Verify placement empirically per model revision rather than assuming a fixed position effect, treating any position policy carried across a model change as unverified until re-measured.
- Emit the assembly record carrying the contract version, admission-policy version, model and tokenizer identity, per-partition ledger, every considered candidate with its components and verdict, the admitted order and token positions, the sufficiency verdict, and the prefix hash.

**Required Outputs**:

- A serialized context package in declared assembly order with a recorded cache boundary.
- A placement verification record naming the model revision it was measured against.
- One assembly record per decision conforming to the declared schema.

**Quality Checkpoints**:

- The assembly record accounts for 100 percent of considered candidates, admitted and excluded alike, since selection recall cannot be measured from admissions only.
- The stable prefix holds no unit admitted for this decision alone.
- Reordering or wrapper changes that alter the token count trigger a return to the admission cut rather than a silent overflow.

***

### Phase 6: Utilization Measurement and Admission-Policy Correction

**Objective**: Establish which admitted units were actually used, quantify the cost of the units that were not, and drive the admission policy down where measured precision fails its gate.

#### Step 6.1: Measure Item-Level and Token-Level Utilization

**Required Actions**:

- Bind every supported output claim, tool call, and state update to the identifiers of the admitted units it consumed, and treat a claim carrying no binding as unsupported rather than as supported by the whole context.
- Compute item utilization as utilized flexible units over admitted flexible units, and token utilization as utilized spans over admitted flexible tokens, reporting both because one used sentence inside a long admitted passage inflates the token-level figure.
- Verify every cited span against the admitted text rather than against the model's assertion, and count a span that does not resolve in the admitted text as unsupported regardless of the claim attached to it.
- Report protected-partition utilization separately, since a standing constraint that is never cited is not thereby waste, and excluding it from the aggregate prevents the metric from penalising policy.
- Segment every utilization figure by partition, admission rule, task class, source, and model revision, since an aggregate figure conceals the partition where the loss actually occurs.

**Required Outputs**:

- A per-unit utilization record with binding evidence and a verified or unverified span verdict.
- Item-level and token-level utilization figures per partition.
- A segmented utilization report with protected partitions reported separately.

**Quality Checkpoints**:

- Utilization is computed from resolved citation identifiers, never asserted by the generating model.
- Item-level utilization for the evidence partition meets or exceeds 0.60; a lower figure triggers Step 6.3.
- Every unsupported claim is recorded, and no claim is counted as supported on the basis of the whole admitted set.

***

#### Step 6.2: Compute Admission Precision and Isolate the Distraction Effect

**Required Actions**:

- Compute admission precision per partition as admitted flexible units judged decisive or supporting for a requirement over all admitted flexible units, using adjudicated labels rather than the selector's own scores.
- Run paired ablation on a representative sample of at least 30 decisions per task class, removing one admitted unit, one duplicate cluster, or one partition at a time and re-running the downstream task under fixed model, template, and evaluation procedure.
- Classify each admitted unit by measured lift as positive, neutral, negative, or interaction-dependent, and treat a negative-lift unit as a distractor irrespective of its relevance score.
- Add grouped ablations for units whose individual lift is neutral, since a set of individually neutral units can carry a joint negative effect that single-unit ablation cannot detect.
- Compare against the frozen baselines from Step 1.3, and report the comparison against the baseline that admits more tokens as the primary evidence that the policy is not merely admitting more.

**Required Outputs**:

- An admission-precision figure per partition with the adjudication basis named.
- A per-unit lift classification across the ablation sample.
- A baseline comparison table reporting quality, token cost, and latency against each frozen baseline.

**Quality Checkpoints**:

- Admission precision meets or exceeds 0.70 per flexible partition; below that figure the admission policy is corrected under Step 6.3 before the configuration is promoted.
- Negative-lift units constitute no more than 5 percent of admitted flexible units; a higher share is a distraction defect and blocks promotion.
- Every ablation figure rests on at least 3 repeated runs, so that variance is estimated rather than assumed.

***

#### Step 6.3: Correct the Admission Policy and Re-Promote

**Required Actions**:

- Reduce first and expand second: on an admission-precision breach, lower the offending partition's top-N cap by 20 percent and raise its score floor to the level that would have excluded the measured negative-lift units, then re-measure before considering any expansion.
- Raise the redundancy penalty and tighten the duplicate threshold where the negative-lift units cluster on near-identical content, and tighten freshness and supersession gates where they cluster on age.
- Recalibrate the component weight vector by coordinate sweep on the labelled admission set, selecting the vector that maximizes admission precision at a fixed decisive-unit recall of 0.95, and version the result.
- Treat a change of model revision, tokenizer, prompt template, retrieval index, corpus size, tool catalog, or policy version as a recalibration trigger, since a calibration produced under a prior configuration does not carry across it.
- Shadow the corrected policy against the current one on live traffic, canary it on no more than 10 percent of decisions, and promote only where every declared gate passes and no zero-tolerance gate has been touched.

**Required Outputs**:

- A corrected admission policy with a new version identifier and a change record naming each adjustment and its measured basis.
- A recalibration trigger log naming the configuration fact that changed.
- A shadow and canary report with per-gate verdicts and a promotion or rollback decision.

**Quality Checkpoints**:

- Every correction reduces admitted volume or tightens a gate before any correction increases it.
- No policy is promoted on a measurement produced under a configuration that has since changed.
- Any unauthorized admission or trust-class escape observed during shadow or canary halts promotion immediately and is never resolved by threshold adjustment.

***

## III. Implementation Guidance for AI Agents

AI agents operating a context selector must follow systematic protocols ensuring that every admitted token is accounted, every exclusion is explained, and no relevance judgement acquires authority over a budget or an authorization decision. The following guidance translates the admission procedure into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Agent**: Owns the selection contract, the requirement list, the partition ledger, and the admission-policy version. It alone may amend a partition bound or a threshold, and every amendment is versioned and recorded.
2. **Candidate Agent**: Commissions bounded candidate generation from authorized source adapters, one pool per partition, and enforces the pool caps. It never expands a pool beyond its cap to compensate for a poor query and never fabricates an empty result for an unavailable adapter.
3. **Eligibility Agent**: Evaluates authorization, tenancy, purpose, sensitivity, retention, validity, integrity, and instruction-versus-data typing, and emits a typed verdict with a policy version. It may deny any candidate and is never overridden by a relevance verdict.
4. **Scoring Agent**: Computes per-partition components, normalizes within the partition and decision, and emits an ordered list with component decomposition attached. It holds no write access to the context package.
5. **Context Assembler**: Holds the tokenizer, the partition ledger, and the sole authority to place a unit into the outgoing prompt. It is the budget holder, applies the admission cut, fixes assembly order, and returns a typed verdict of pass or overflow.
6. **Sufficiency Agent**: Evaluates the admitted set against the requirement list, emits exactly 1 sufficiency verdict, and authorizes at most the declared number of re-query rounds. It may not convert exhaustion into sufficiency.
7. **Measurement Agent**: Binds outputs to admitted identifiers, computes utilization and admission precision, runs ablations, and may withhold promotion of an admission policy. It never modifies the assembly it measures.

**Trust and Authority Boundary**: Retrieved text, tool descriptions, memory records, and tool results are data in every partition they may enter. None of them may raise its own trust class, select a more privileged tool, alter a partition bound, or place itself in the instruction partition. This is a hard constraint applying to every component, and a violation halts the decision rather than downgrading to a warning.

**Workflow Execution Pattern**:

```
STATE: Admission_Cut
INPUTS:
  1. Partition ledger with maxima, floors, and caps from Step 1.2
  2. Per-partition ordered lists with normalized scores from Step 3.2
  3. Eligibility verdicts and conflict groups from Phase 2
  4. Tool loadout verdict from Phase 4
ACTIONS:
  1. Admit protected atoms and floor units outside score competition
  2. Iterate each partition by marginal utility per token to its cut
  3. Recompute redundancy and residual coverage after each admission
  4. Serialize the package and recount with the deployed tokenizer
VALIDATION:
  - partition_tokens <= partition_maximum FOR EVERY partition
  - admitted_count <= top_n_cap FOR EVERY partition
  - unresolved_eligibility_admitted == 0
  - protected_atoms_present == TRUE
  - every_exclusion_has_reason_code == TRUE
  - conflict_group_members_admitted >= 2 FOR EVERY disclosed group
TRANSITIONS:
  IF all_validations_pass THEN next_state = Sufficiency_Assessment
  IF recount_exceeds_bound THEN next_state = Admission_Cut
  IF floor_unsatisfiable THEN next_state = Overflow_Verdict_Return
  IF validation_failed THEN next_state = Selection_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended admitted set with its per-partition ledger, reason codes, and projected token counts without serializing it; confirm it against the validation block while no call has been issued; serialize and issue only after validation passes, writing the assembly record in the same operation.

**Approval Gate**: Human authorisation is required before admitting any unit whose eligibility verdict is redact or transform in a partition governed by a regulated-data policy, before promoting an admission policy whose canary shows any unauthorized admission, and before any single decision projected to consume more than 40 percent of the account's remaining cost budget for the task class. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the selection contract, partition ledger, and requirement coverage table in durable state, since a decision may span several calls and a context boundary discards the window.
- Carry pointers and navigation units in place of payloads wherever the residual gap does not yet name a specific object, and fetch only against a named gap.
- Write a handoff record naming the contract version, the covered and uncovered requirements, the admitted identifiers, the remaining round and cost budget, and the next decision at every context boundary.
- Count the selector's own retrieval, scoring, and adjudication calls toward the decision's cost budget rather than treating selection as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract Integrity (After Phase 1)**

- **Automated Check**: Every requirement carries a machine-evaluable coverage test or a named role; every partition carries a maximum, a floor, a trust-class list, and a top-N cap; partition maxima plus reserves sum to no more than 100 percent of capacity; at least 3 baselines are frozen.
- **Agent Action on Pass**: Proceed to candidate generation.
- **Agent Action on Failure**: Halt and return the contract defect; no retrieval is commissioned against an incomplete contract.
- **Human Review Trigger**: A requirement not statable as an evaluable coverage test, or a task class requesting a partition-share move above 15 percentage points.

**Checkpoint 2: Eligibility Integrity (After Phase 2)**

- **Automated Check**: Every candidate carries an eligibility verdict with a policy version; zero candidates carry an unresolved check; every transformation produced a distinct identifier; no conflict group was reduced below 2 members.
- **Agent Action on Pass**: Proceed to scoring.
- **Agent Action on Failure**: Return the candidates with unresolved checks to the eligibility filter; scoring does not begin on a partially filtered pool.
- **Human Review Trigger**: More than 10 percent of candidates denied for an unresolved rather than a decided check, which indicates a policy service fault rather than a policy outcome.

**Checkpoint 3: Scoring Integrity (After Phase 3)**

- **Automated Check**: Every composite score carries its component decomposition; every partition normalized within itself for this decision; every floor is paired with a cap; recency contributes no more than 30 percent of any history score; the weight-vector origin is named.
- **Agent Action on Pass**: Proceed to tool selection.
- **Agent Action on Failure**: Recompute the affected partition only; a defective partition never propagates into a global re-score.
- **Human Review Trigger**: A weight vector carried unchanged from a published default into a task class with a declared high-consequence risk tier.

**Checkpoint 4: Loadout Integrity (After Phase 4)**

- **Automated Check**: The regime verdict matches the catalog census against the stated thresholds; the always-resident list holds no more than 5 entries; every admitted definition traces to a stated capability; retrieval hit rate at the declared limit is at or above 0.90.
- **Agent Action on Pass**: Proceed to admission.
- **Agent Action on Failure**: Revise descriptions and aliases and re-retrieve; the retrieval limit is not raised as a first response.
- **Human Review Trigger**: Missed-tool regret above 2 percent of decisions in the task class, or any tool definition admitted for an unauthorized principal.

**Checkpoint 5: Admission and Sufficiency Integrity (After Phase 5)**

- **Automated Check**: No partition exceeds its maximum or cap in the recounted package; every exclusion carries a reason code; exactly 1 sufficiency verdict is emitted; the assembly record accounts for 100 percent of considered candidates.
- **Agent Action on Pass**: Issue the call and proceed to measurement.
- **Agent Action on Failure**: Halt; an over-budget or unaccounted package is never issued with a warning attached.
- **Human Review Trigger**: An exhaustion stop on a decision in the highest risk tier, or a sufficiency verdict of blocked on external input recurring for the same requirement 3 times.

**Checkpoint 6: Measurement Integrity (After Phase 6)**

- **Automated Check**: Utilization computed from resolved identifiers; admission precision at or above 0.70 per flexible partition; item utilization at or above 0.60 for the evidence partition; negative-lift units at or below 5 percent; at least 30 sampled decisions and 3 repeated runs behind every ablation figure.
- **Agent Action on Pass**: Release the measurement report and permit promotion of the admission policy.
- **Agent Action on Failure**: Withhold promotion and apply the reduce-first correction in Step 6.3; no policy is promoted on unmeasured utilization.
- **Human Review Trigger**: Any unauthorized admission or trust-class escape, or an admission-precision drop above 10 percentage points between consecutive measurement cycles.

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

**Error Type 1: Over-Admission and Distraction**

- **Symptoms**: Item-level utilization below 0.60; admitted tokens near the partition maximum on most decisions; quality lower than a smaller ablation of the same set; the model citing a plausible but wrong unit that shares entities or dates with the correct one.
- **Diagnostic Steps**: Segment utilization by partition and admission rule to locate the partition carrying the unused tokens; run paired ablation on the unutilized units to distinguish neutral from negative lift; compare against the frozen baseline that admits more tokens.
- **Resolution Protocol**: Option A, lower the offending partition's top-N cap by 20 percent and raise its floor to exclude the measured negative-lift units. Option B, raise the redundancy penalty and tighten the duplicate threshold where the negative-lift units cluster on near-identical content. Option C, replace payloads with navigation units and fetch only against a named residual gap.
- **Escalation Trigger**: Admission precision below 0.55 in any flexible partition suspends autonomous admission in that partition and routes its decisions to the reduced baseline until recalibration completes.

**Error Type 2: Under-Admission and Missing Prerequisite**

- **Symptoms**: Requirement coverage below the declared gate; confident answers resting on premises no admitted unit supports; repeated user correction on the same requirement; an action failing on a precondition that was available and eligible.
- **Diagnostic Steps**: Compare the requirement list against the exclusion list to determine whether the missing unit was never retrieved, retrieved and denied, or retrieved and cut; check whether the cut was caused by a cap, a floor, or a token bound.
- **Resolution Protocol**: Option A, expand dependency handling so that a unit required by an admitted unit is admitted with it rather than competing against it. Option B, raise the partition floor for the requirement class and fund it from a declared lender. Option C, lower the continue threshold for the re-query loop in the affected task class.
- **Escalation Trigger**: A requirement uncovered on 3 consecutive decisions of the same class escalates for contract review; the round budget is not raised as a substitute for a missing source.

**Error Type 3: Cross-Partition Score Contamination**

- **Symptoms**: A standing constraint, a state field, or a required tool definition excluded in favour of a topically similar document; scores comparable across partitions in the log; a single global top-N in the assembly record.
- **Diagnostic Steps**: Inspect the assembly record for a normalization scope spanning more than one partition, and check whether any partition's floor was satisfied from another partition's ranked list.
- **Resolution Protocol**: Option A, restore per-partition normalization and re-run the cut. Option B, move the misplaced candidate type into its own partition with its own components. Option C, promote the affected content to a protected atom where its absence fails the decision outright.
- **Escalation Trigger**: Any admission of a unit into a partition other than the one its type assigns halts the decision; this class is never resolved by re-scoring.

**Error Type 4: Tool Overload or Tool Selection Miss**

- **Symptoms**: Tool definitions consuming more than their partition maximum; the wrong tool invoked among overlapping names; an authorized tool that would have succeeded never entering the loadout; retrieval hit rate below 0.90.
- **Diagnostic Steps**: Recount the serialized catalog against the regime thresholds; log the full candidate universe for the missed decision and determine whether the miss was a retrieval failure, a description failure, or an authorization filter outcome.
- **Resolution Protocol**: Option A, defer all but 3 to 5 always-resident definitions and retrieve the remainder per action. Option B, add lexical aliases and task-phrased keywords to the descriptions of missed tools and re-measure. Option C, split an overlapping pair into one least-privileged tool and remove the redundant definition from the catalog.
- **Escalation Trigger**: Missed-tool regret above 2 percent of decisions, or wholesale admission of a catalog above 30 tools, blocks the configuration; the retrieval limit is never raised more than once without a description revision between raises.

**Error Type 5: Trust-Class Escape Through Admitted Content**

- **Symptoms**: Retrieved text or a tool description altering instruction-following; a more privileged tool selected immediately after an external document was admitted; disclosure of content outside the principal's scope; instruction-shaped spans present in an evidence partition without a data label.
- **Diagnostic Steps**: Trace the affected decision's assembly record to the admitted unit whose position precedes the behaviour change; confirm whether the unit carried an instruction-versus-data label and whether structural separation survived its transformation.
- **Resolution Protocol**: Option A, quarantine the decision, preserve the assembly record, and re-run with the suspect unit excluded. Option B, re-label the affected source class as data and enforce the label through the wrapper as well as the partition. Option C, reduce the loadout to the least-privileged set able to complete the action and require execution-time authorization on every invocation.
- **Escalation Trigger**: Any confirmed escape halts autonomous selection for the affected source class immediately and adds the case to the adversarial regression set; this class is never resolved by retry.

**Error Type 6: Selection Drift as Corpora and Catalogs Grow**

- **Symptoms**: Admission precision or niche requirement coverage falling with no change to selector code; rising concentration on a small set of frequently admitted units; stale units retained because access frequency keeps refreshing their rank.
- **Diagnostic Steps**: Compare score and component distributions against the frozen baseline; plot admission rate against measured ablation lift after controlling for candidate availability; plot admission probability against validity age.
- **Resolution Protocol**: Option A, recalibrate weights and thresholds on the current candidate distribution and version the result. Option B, cap the frequency component's contribution and add per-source admission caps. Option C, enforce hard validity gates so that access never refreshes factual currency.
- **Escalation Trigger**: An admission-precision drop above 10 percentage points between consecutive cycles rolls the admission policy back to its last passing version; a drift finding is never accepted as a new normal without a recalibration record.

**Troubleshooting Decision Tree**:

```
SELECTION CHECKPOINT DETECTS A PROBLEM
├─ ADMISSION VOLUME DEFECT
│   ├─ Utilization below gate → Lower cap 20 percent; raise floor; re-measure
│   ├─ Negative-lift units above 5 percent → Raise redundancy penalty; tighten freshness gate
│   └─ Requirement uncovered though candidate existed → Add dependency expansion; raise floor
├─ PARTITION DEFECT
│   ├─ Scores compared across partitions → HALT; restore per-partition normalization
│   ├─ Floor filled from another partition's list → Reject package; re-run the cut
│   └─ Protected atom dropped by a history policy → HALT; lift atoms before scoring
├─ TOOL DEFECT
│   ├─ Catalog above 30 tools admitted whole → Defer all but 3 to 5; retrieve per action
│   ├─ Retrieval hit rate below 0.90 → Revise descriptions and aliases before raising the limit
│   └─ Definition admitted for unauthorized principal → HALT; treat as disclosure incident
├─ ELIGIBILITY DEFECT
│   ├─ Unresolved check admitted → Exclude the unit; record policy service fault
│   ├─ Expired or superseded unit admitted → Enforce hard validity gate; re-run the cut
│   └─ Conflict group collapsed to one member → Restore members; reserve disclosure tokens
└─ TRUST DEFECT
    ├─ Instruction-shaped span unlabelled in evidence → Label as data; re-issue
    └─ Privilege raised after external admission → Quarantine; reduce loadout; escalate
```

### D. Performance Metrics and Continuous Learning

**Admission Quality Metrics**:

- **Admission precision**: Admitted flexible units judged decisive or supporting over all admitted flexible units, per partition (target: at least 0.70; below 0.55 suspends autonomous admission in that partition).
- **Requirement coverage**: Requirements covered at their declared evidence standard over all requirements (target: at least 0.90 for standard task classes and 1.00 for the highest risk tier).
- **Item utilization**: Utilized flexible units over admitted flexible units (target: at least 0.60 for the evidence partition, reported separately from protected partitions).
- **Wasted-token share**: Tokens in unutilized flexible units over admitted flexible tokens (target: no more than 0.35; a higher figure triggers the reduce-first correction).
- **False-sufficiency rate**: Decisions judged sufficient before generation whose required evidence was in fact missing (target: no more than 0.05, and no more than 0.01 in the highest risk tier).
- **Conflict disclosure rate**: Detected conflict groups surfaced with at least 2 members over all detected conflict groups (target: 1.00; silent resolution is a defect, not an optimisation).

**Efficiency and Stability Metrics**:

- **Selection overhead**: Selector retrieval, scoring, and adjudication cost over total decision cost (target: no more than 20 percent; above 35 percent triggers policy review).
- **Selection latency**: End-to-end selection time reported at median, 95th percentile, and 99th percentile, with candidate generation, eligibility, scoring, and assembly timed separately.
- **Cost per successful decision**: Total cost over accepted successful decisions, reported instead of cost per selection call, since a cheap selection that forces a re-query is not cheap.
- **Selection stability under paraphrase**: Overlap of the admitted set across paraphrases of one request (target: at least 0.80; lower overlap indicates the score is reading phrasing rather than requirement).
- **Source and tool concentration**: Share of admissions taken by the top 5 sources and the top 5 tools (target: monitored per corpus, with a per-source cap applied where one source exceeds 40 percent without a matching lift).
- **Overflow and re-query incidence**: Decisions returning an overflow verdict or entering a second re-query round (target: no more than 10 percent combined; a higher figure indicates a partition sizing defect rather than a retrieval defect).

**Log-Pattern Failure Detection**: A rising admitted token count with a flat utilization figure indicates over-admission. Repeated identical residual-gap queries indicate a source gap rather than a query defect. A high admission rate for units with neutral or negative ablation lift indicates popularity bias. Frequently admitted units whose validity age keeps increasing indicate stale pinning. Rising exclusion counts under the budget reason code with stable pool sizes indicate a partition sized below its workload. Utilization high on protected partitions and low everywhere else indicates that flexible admission is contributing nothing and should be compared against the protected-only baseline.

**Learning and Adaptation Mechanisms**:

- **Reason-code analysis**: Aggregate exclusion reason codes per partition and task class, since selection recall and policy overreach are visible only in the excluded population.
- **Outcome-linked relabelling**: Feed adjudicated per-unit lift back into the labelled admission set, and refresh the set whenever the corpus grows by more than 25 percent.
- **Policy versioning**: Version every threshold, cap, weight vector, and partition share together, and evaluate a new version on a time-forward split rather than a random split, since a random split leaks future store state into the training window.
- **Threshold recalibration**: Recompute every numeric bound per task class and model revision; the values stated in this guide are deployment defaults, not constants.

**Human-in-the-Loop Boundaries**: Amendment of a partition bound or a zero-tolerance gate, promotion of an admission policy whose canary showed an unauthorized admission, admission of transformed regulated content, and acceptance of a drift finding as a new baseline are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the admission of information into a bounded resource rather than the content of any particular information. Its phases hold wherever candidates exceed capacity, candidate types are heterogeneous, and admitting the wrong candidate carries a cost.

### 4.1 Cross-Domain Application Patterns

**Software engineering and code modification**: Requirements are the symbol definitions, callers, interface contracts, and failing test outputs the change depends on. The workspace partition is sized above the default because the decisive material is current file state, and the evidence partition is sized below it. Navigation units dominate the first round: repository manifest, changed-file list, and symbol index enter the window, and file contents are fetched only against a named residual gap [1]. The tool partition runs a retrieved loadout because a development environment aggregating several servers routinely exceeds the wholesale-admission threshold [22]. Utilization is measured against which admitted files the accepted diff actually touched, which makes over-admission unusually easy to detect in this domain.

**Clinical decision support**: Requirements are the specific findings, medication interactions, and contraindications a recommendation depends on. Eligibility filtering carries the heaviest weight of any domain: consent scope, purpose limitation, and record segmentation are decided before relevance, and a candidate whose consent scope cannot be established is excluded rather than admitted with a caveat. Freshness gates are per fact rather than global, since an allergy record and a laboratory value have different volatilities. Conflict groups are always disclosed rather than resolved by ranking, because a superseded and a current value for one field must both reach the reviewing clinician with their timestamps attached.

**Legal and regulatory research**: Requirements are the governing provisions, their effective dates, and the jurisdiction each applies to. Deduplication is the dominant risk: two texts that differ only in effective date or jurisdiction are near-identical by similarity and must never be collapsed. Independent corroboration is retained rather than penalised as redundancy, because a second source confirming a governing provision is evidence rather than repetition. Primary sources are preferred over commentary through the authority component, and enough surrounding text is admitted with each quotation to prevent distortion.

**Industrial operations and field maintenance**: Requirements are the asset's current state, its applicable procedure version, and the preconditions of the next action. The procedural partition is gated hard on environment, equipment model, and tool version, since a procedure applicable to a different revision is a distractor of the most dangerous kind. Recency is weighted higher than in other domains for telemetry and lower for procedures. Latency bounds are tight, so the loop is usually single-pass with the re-query reserve set to zero and a conservative sufficiency threshold in its place.

**Financial compliance and audit support**: Requirements are the transactions, control statements, and policy provisions a finding depends on. The assembly record is a deliverable rather than a diagnostic aid, because a finding must be traceable to the exact units that supported it. Exclusion logging carries the same weight as admission logging, since an auditor asks what was not considered as often as what was. Per-source admission caps are enforced strictly so that one system of record cannot dominate a sample.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small candidate universes**: Where every partition's authorized pool holds fewer than 20 units and the total serialized size fits the budget, collapse scoring to deterministic eligibility filtering and canonical ordering. Retain the requirement list, the assembly record, and utilization measurement, since these detect the point at which the universe outgrows the simplification.
- **Large or growing corpora**: Retain every phase, add per-source admission caps, and treat corpus growth above 25 percent as a recalibration trigger, since popular units accumulate access history and near-duplicates crowd out niche evidence while the selector code remains unchanged.
- **High-risk or irreversible decisions**: Require requirement coverage of 1.00 at the declared evidence standard, mandate independent corroboration for every decisive claim, disclose every conflict group, and prefer abstention over an admitted set that is sufficient only with declared uncertainty.
- **Strict latency budgets**: Reduce the number of re-query rounds rather than removing the eligibility filter or the sufficiency verdict, since removing those removes the guarantees while reducing rounds only reduces recall. Where latency forbids any round, set the re-query reserve to zero, raise the floor, and declare the reduced sufficiency standard in the contract.
- **Long-running autonomous work**: Persist the contract, the requirement coverage table, and the admitted identifiers outside the window, write a handoff record at every context boundary, and re-run coverage assessment at each handoff so that a requirement covered before a compaction is not assumed covered after it.
- **Multi-agent delegation**: Give a sub-agent a delegation packet holding a bounded objective, the applicable constraints, its permitted tools and data scopes, the specific admitted units or authorized pointers, and its own token and round budgets, rather than the parent's transcript. A sub-agent lacking context returns a structured request naming the unmet requirement; the supervisor authorizes or denies it with a reason rather than widening the child's scope by default.

***

## V. Limitations and Considerations

**Thresholds here are deployment defaults, not measured constants**: The numeric bounds in this guide, including admission precision at 0.70, item utilization at 0.60, the 30 percent recency weight cap, the 15 percentage point partition-share bound, the 0.95 duplicate threshold, the 3-round re-query limit, and the sampling minimums of 30 decisions and 3 runs, were chosen to be operable on first deployment. They are not derived from a universal property of selection systems. The mitigation is the recalibration requirement in Phase 6 and Section III.D, obliging each deployment to recompute every bound per task class and model revision against observed outcomes before treating any of them as evidence.

**Tool-count thresholds are vendor-reported and model-specific**: The regime rule in Step 4.1 rests on provider documentation reporting that selection accuracy degrades once available tools exceed roughly 30 to 50, together with guidance to enable retrieval-based tool selection at 10 or more tools or above 10,000 tokens of definitions [22]. Independent work reports a comparable effect and a large accuracy gain from retrieval over wholesale admission, but on one benchmark and one model family [23]. The mitigation is Step 4.3, which requires each deployment to measure hit rate, execution success, and missed-tool regret on its own catalog, and Checkpoint 4, which blocks a configuration whose measured regret exceeds its gate.

**Utilization is a conservative proxy for use, not a measurement of attention**: The attention computation that determines what an admitted token contributes is not observable from the agent layer. Citation binding and span verification under-count units that prevented an error without being cited, and they cannot detect a unit that was read and correctly ignored. The mitigation is the paired ablation in Step 6.2, which measures effect rather than citation, together with the rule that protected-partition utilization is reported separately so that policy is not penalised for going uncited.

**Per-partition isolation forfeits some cross-partition optimality**: Selecting independently within partitions can admit a weak evidence unit while excluding a strong history turn that would have served the same requirement better. This is a deliberate trade. The mitigation is requirement-level coverage assessment in Step 5.2, which detects a requirement left uncovered by the partition that was supposed to carry it and permits a declared borrow, and the 15 percentage point task-class adjustment that resizes partitions where the pattern recurs.

**Long inputs degrade in task-specific and model-specific ways**: Reported evaluations find that information positioned near the beginning or end of a long input is used more reliably than information in the middle [4], that measured degradation grows with input length within advertised limits rather than at them [2], and that accuracy can fall substantially at longer inputs even where every required piece of evidence is present [24]. These findings do not license a single universal position rule or a single length limit. The mitigation is Step 5.3, which requires placement to be verified per model revision and treats any position policy carried across a model change as unverified.

**Eligibility filtering depends on an external policy service**: Where the policy decision point is unavailable, no candidate's eligibility can be established, and the rule that an unestablished check is a denial degrades the selector to protected content only. The mitigation is the documented fallback in Checkpoint 2 and Error Type 5, which marks degraded decisions, excludes them from normal quality aggregates, and fails closed rather than admitting on a cached or assumed verdict.

**Selection cannot repair a corpus that lacks the evidence**: A perfect admission policy over a store that does not contain the required material produces a correct insufficiency verdict and nothing more. Repeated insufficiency in one requirement class is a sourcing problem, not a selection problem. The mitigation is the escalation trigger in Error Type 2, which routes a requirement uncovered on 3 consecutive decisions to contract review rather than to further rounds.

**Measurement is expensive and is the first thing cut**: Ablation multiplies evaluation cost, and deployments under schedule pressure report utilization without lift. The mitigation is Checkpoint 6, which withholds promotion of an admission policy whose gains have not been demonstrated against the frozen baseline that admits more tokens, so that a policy cannot be promoted for admitting more.

**External citations were not independently re-verified**: The external references in Section VII are transcribed from the originating prose source as it cited them, except for the small number retrieved during this conversion and marked as such. Their claims are reported as the source reported them. The mitigation is that no numeric bound in this guide's Operational Framework depends on an unverified external claim; the two figures that do rest on external evidence are marked in this section as vendor-reported and are gated by local measurement.

***

## VI. Conclusion and Summary

Context selection is an accounting discipline before it is a relevance problem. Its value comes from a small number of explicit decisions taken in a fixed order: what the decision actually requires, what each partition may spend, which candidates are eligible at all, how each partition orders its own candidates, where the admission cut falls, and whether the admitted set covered the requirements. A system taking those decisions explicitly can be corrected by measurement. A system that ranks candidates and serializes whatever fits cannot be corrected at all, because it has no record of what it excluded or why.

A team introducing a selector should instrument before optimising. Declare the requirement list and the assembly-record schema, run the protected-only and unfiltered top-N baselines, and measure utilization against both. Add per-partition budgets and eligibility filtering next, since these remove the two failure classes that no amount of ranking improvement addresses. Add scoring, thresholds, and calibration only after the assembly record can account for every candidate considered. Retrieval frameworks and tool-search facilities supply the plumbing for candidate generation and deferred definitions, but none of them supplies a partition bound, an eligibility policy, or a utilization figure, and a selector without those three is an unobservable prototype regardless of how good its ranker is.

**Key Success Factors**:

- **Admission separated from ranking**: The scoring stage proposes an order and the deterministic assembler decides what crosses into the window; a score never admits anything by itself, and the budget wins every disagreement.
- **One partition per candidate type**: Instructions, tool definitions, working state, memory, evidence, tool results, and history are selected independently against their own components, because a single score across incomparable types drops the cheapest indispensable units first.
- **Eligibility before relevance**: Authorization, tenancy, purpose, validity, and trust typing are decided before any candidate is scored, and a check that cannot be completed is a denial rather than a caveat.
- **Protected atoms are never at risk**: The active goal, the binding constraints, the current plan step, and the open state survive every cut at every transcript length and are never subject to a relevance score.
- **Less is a valid correction**: Admitting more relevant-looking content is not monotonically better; the policy reduces caps and raises floors before it expands anything, and a partition under its maximum is left there.
- **Measured, not asserted**: Utilization, admission precision, and ablation lift are computed from resolved identifiers and repeated runs, and no admission policy is promoted on a configuration whose measurement no longer applies.

By following this guide, AI agents can decide what enters a bounded context window through an accounted admission process, exclude the rest with reasons a reviewer can audit, and correct the policy from evidence of what the admitted content actually did.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. The three entries marked as retrieved during conversion were fetched or returned by search while this guide was being written, and their figures are reported from the pages actually retrieved.

**Corpus pointers**:

- `Context Select Patterns: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the candidate class taxonomy, the eligibility-before-relevance rule, the expected marginal utility formulation, the category floor and cap scheme, the staged tool-selection policy, the progressive-disclosure treatment, the deduplication and conflict rules, the negative-selection reject vocabulary, the trust-tier controls, the twelve-stage workflow, the logging contract, and the metric definitions. It carries inline citations to vendor engineering documentation, protocol specifications, retrieval framework documentation, and primary literature on diversity reranking, adaptive retrieval, memory retrieval, and long-context degradation; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/context-management/guide_ContextManagement.md` — the umbrella guidance for this category. Source of the context contract, the context budget, the default partition table, the admission gate, the four context failure modes, and the operation-family ladder this guide returns control to on an overflow verdict.
- `advanced_task_guides/context-management/guide_ContextWritePatterns.md` — the sibling owning the write operation. Governs persistence, write authorization, idempotency, and durable provenance, none of which selection performs.
- `advanced_task_guides/context-management/guide_ContextCompression.md` — the sibling owning the compress operation. Governs lossy reduction of content already inside the window and the preservation manifest that validates it.
- `advanced_task_guides/context-management/guide_ContextIsolation.md` — the sibling owning the isolate operation. Governs splitting work across separate windows and the scoping of a delegation packet referenced in Section 4.2.
- `advanced_task_guides/context-management/guide_ContextFailurePrevention.md` — the sibling owning detection, containment, and prevention of the context failure modes in depth. Negative selection here is the admission-time prevention of distraction, and that guide owns the detection budget, the per-mode signals, and the attribution of a non-utilized unit back to the admission rule that admitted it.
- `advanced_task_guides/context-management/guide_KVCacheAwarePromptConstruction.md` — the sibling owning exact-prefix reuse, cache-family keys, and the closed vocabulary of invalidation causes. The cache boundary recorded with the serialized package in Step 5.3 is priced there, and the deterministic tie-breaking required of ranking here is what prevents an ordering-only change from forcing a prefix rebuild.
- `advanced_task_guides/memory-management/guide_AttentionBasedMemoryRetrieval.md` — the specification adopted for the memory partition. Source of the salience component inventory, the weight-vector origins, the floor-and-cap pairing, the per-query normalization rule, the context assembler's budget authority, and the assembly record.
- `advanced_task_guides/memory-management/guide_WorkingMemory.md` — source of the protected atom definition and its membership list, adopted unchanged in Section 1.1 and Step 3.3.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — companion guidance on the read and write boundary, applicable to the read-time-only constraint in Section 1.2.
- `advanced_task_guides/knowledge-retrieval/guide_AdvancedKnowledgeRetrieval.md` — companion guidance on candidate generation, applicable to the pools consumed in Step 2.1.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — companion guidance on query formulation, applicable to the residual-gap queries in Step 5.2.
- `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md` — companion guidance on model-directed retrieval loops, applicable to the bounded re-query loop and its stopping criteria.

**External references**: The numbering below is the numbering used by the inline markers in Sections II, IV, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Context engineering, long-context behaviour, and caching*

1. Anthropic, *Effective context engineering for AI agents* — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
2. Chroma, *Context Rot* — https://www.trychroma.com/research/context-rot
3. OpenAI, *The Instruction Hierarchy* — https://openai.com/index/the-instruction-hierarchy/
4. Liu and colleagues, *Lost in the Middle* — https://arxiv.org/abs/2307.03172
5. Anthropic, *Prompt caching* — https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
6. OpenAI, *Prompt caching* — https://developers.openai.com/api/docs/guides/prompt-caching.md

*Tool selection, tool catalogs, and protocol surfaces*

7. Anthropic, *Writing tools for agents* — https://www.anthropic.com/engineering/writing-tools-for-agents
8. OpenAI, *A practical guide to building agents* — https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
9. OpenAI, *Tool search* — https://developers.openai.com/api/docs/guides/tools-tool-search
10. Model Context Protocol, *Tools specification, 2026-07-28* — https://modelcontextprotocol.io/specification/2026-07-28/server/tools
11. *Semantic Tool Discovery for Large-Scale MCP Environments* — https://arxiv.org/abs/2603.20313
12. *Efficient Tool Selection for LLM Agents* — https://arxiv.org/html/2511.14650v1

*Selection, diversity, routing, and stopping*

13. Park and colleagues, *Generative Agents* — https://dl.acm.org/doi/fullHtml/10.1145/3586183.3606763
14. Carbonell and Goldstein, *The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries* — https://storage.ghost.io/c/97/88/97889716-a759-46f4-b63f-4f5c46a13333/content/files/~jgc/publication/the_use_mmr_diversity_based_ltmir_1998.pdf
15. Jeong and colleagues, *Adaptive-RAG* — https://arxiv.org/abs/2403.14403
16. *When to Stop Searching: Efficient Multi-round Retrieval for RAG* — https://arxiv.org/html/2608.13237
17. LangGraph, *Build a custom RAG agent* — https://docs.langchain.com/oss/javascript/langgraph/agentic-rag
18. LlamaIndex, *Router* — https://developers.llamaindex.ai/python/framework/module_guides/querying/router/

*Security and evaluation metrics*

19. OWASP, *LLM01:2025 Prompt Injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
20. RAGAS, *Context Precision* — https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/
21. RAGAS, *Context Recall* — https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/

*Retrieved during conversion*

22. Anthropic, *Tool search tool* — https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool (retrieved and read during this conversion; source of the regime thresholds in Step 4.1, namely retrieval-based selection at 10 or more tools or above 10,000 tokens of definitions, degradation of selection accuracy above 30 to 50 available tools, 3 to 5 always-resident definitions, and a default of 5 returned definitions per search)
23. *RAG-MCP: Mitigating Prompt Bloat in LLM Tool Selection via Retrieval-Augmented Generation* — https://arxiv.org/abs/2505.03275 (located by search during this conversion; reported figures are as summarised by the retrieved abstract rather than from the full text)
24. *Context Length Alone Hurts LLM Performance Despite Perfect Retrieval* — https://arxiv.org/html/2510.05381v1 (located by search during this conversion; cited in Section V for the finding that accuracy can fall at longer inputs even where the required evidence is present)
