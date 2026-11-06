# Embedding-Based Routing

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Embedding-based routing constitutes the task family of selecting one destination for an incoming request by encoding the request and a bounded set of labelled destination exemplars into vectors in one compatible space and comparing them by similarity. This guide provides AI agents with a structured protocol for declaring destinations, curating and validating exemplar sets, pinning an embedding revision, calibrating an absolute similarity floor and a separation margin on labelled data, dispatching under those gates with a declared fallback, and detecting drift that decays a fitted threshold. Its central claim is that similarity is not eligibility: a nearest-neighbour lookup always returns a nearest destination however unrelated the request, so the method has no intrinsic way to say none of these, and a router without a calibrated absolute floor routes unrelated traffic confidently. It specifies the tier partition that assigns the exemplar index, embedding version pinning, similarity computation, gate evaluation, fallback selection, and accuracy measurement to deterministic software while leaving the model tier no request-time authority at all, since the embedding call is a reproducible transformation rather than a judgement. It quantifies the labelled-data minimum for threshold fitting, the exemplar-quality tests that expose labelling error, and the refit and full re-embed triggers.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Embedding-based routing**: A control-plane pattern in which a deterministic component encodes an incoming request into a vector, compares it against stored vectors representing a bounded destination set in one compatible embedding space, aggregates the comparisons into one score per destination, and accepts, abstains, clarifies, escalates, or hands off according to calibrated gates. The router selects; it never performs the downstream work it selects among, and it never grants authority because two texts are close in vector space.

**Destination**: One addressable endpoint of routing, carrying a stable identifier, an owner, inclusion criteria, exclusion criteria, named confusing neighbours, accepted languages and modalities, a risk class, an allowed tool and data scope, a latency objective, a cost envelope, and a declared fallback. This term is adopted from the corpus routing guides in place of "route" so that one destination set can serve a rule-based, embedding-based, and model-based router without translation.

**Destination registry**: The versioned, deterministic store holding every destination record and the single source of truth for which identifiers exist. The registry sits outside the vector index, and the index is a derived artifact rebuilt from it. An identifier is never reused for a different meaning.

**Closed destination vocabulary**: The finite enumeration of destination identifiers valid at a stated taxonomy version. A retrieval result naming anything outside this enumeration is invalid by construction, and the dispatcher rejects it rather than repairing it.

**Exemplar**: One labelled text unit stored as evidence for exactly one destination, carrying an immutable exemplar identifier, its canonical text, a text version, a destination identifier, a class label of positive, hard negative, boundary, or synthetic, label provenance, author and reviewer identity, language, source domain, sensitivity class, tenant scope, creation and expiry times, approval state, and deletion lineage. Canonical exemplar text is retained permanently so that every active embedding revision can re-encode the full corpus.

**Exemplar set**: The complete collection of approved exemplars for one destination at one taxonomy version. It is the destination's entire semantic definition for routing purposes, and any property the exemplar set fails to express is invisible to the router regardless of how the destination record is worded.

**Destination representation**: The set of vectors that stand for one destination during retrieval, produced by one of four aggregation strategies: a single encoded description, every exemplar vector, one centroid, or one centroid per discovered subcluster.

**Aggregation rule**: The deterministic function mapping retrieved neighbour similarities to exactly one score per destination. Attested rules are maximum similarity over exemplars, similarity to a centroid, similarity to the nearest of several subcluster centroids, and class-balanced nearest-neighbour voting.

**Similarity floor**: The absolute minimum aggregated similarity a destination must reach before it is eligible for acceptance at all, fitted per destination on labelled calibration data. It is the gate that gives a closed-set method an open-set answer, and a router deployed without it has no mechanism to decline.

**Decision margin**: The difference between the highest and second-highest destination scores. A high top score with a small margin indicates ambiguity between two destinations rather than confidence in one, and margin is therefore evaluated independently of the floor rather than folded into it.

**Neighbour support**: The count of retrieved neighbours belonging to the winning destination within the retrieved candidate set. Three mutually close neighbours from one destination constitute different evidence from one isolated match at the same top score.

**Open-set rejection**: The outcome in which no destination clears its floor, its margin, and its support requirement, and the request is routed to a declared fallback, clarification, escalation, or human review path rather than to the nearest destination. Open-set rejection is a first-class decision type with an owner and a service objective, not an error state.

**Cross-assignment**: The condition in which an exemplar labelled for one destination sits closer to another destination's representation than to its own. It signals either a labelling error on that exemplar or a genuine overlap between two destinations whose criteria cannot be separated, and it is detected by measurement rather than by review alone.

**Exemplar imbalance**: The condition in which destinations hold materially different exemplar counts, which biases maximum-similarity and nearest-neighbour aggregation toward the larger sets because a denser region wins more nearest-neighbour slots at equal semantic fit.

**Embedding revision**: The immutable identifier of the exact encoder that produced a vector, covering weights revision or checksum, tokenizer, pooling, precision, output dimension, normalisation mode, and any query or passage prefix or instruction template. A provider alias that silently changes any of these is a different revision. This term and its pinning discipline are adopted from the corpus guide on unstructured memory rather than re-derived here.

**Index generation**: A monotonically numbered, immutable build of the exemplar index pinned to exactly one embedding revision, one preprocessing version, one exemplar snapshot checksum, one distance metric, and one calibration artifact. Serving traffic addresses a generation only through an alias, and no request is answered from two generations at once.

**Embedding version drift**: The condition in which part of the exemplar corpus is encoded under one revision and the remainder under another, and the two populations are compared as though their distances were calibrated. It raises no error, degrades routing silently, and is detected by comparing each vector's recorded revision against the serving generation's pin.

**Calibration artifact**: The versioned record holding every fitted per-destination floor, every margin threshold, every support minimum, the labelled partition identifiers the fit used, the measured false-route and false-fallback rates at the selected operating point, and the fit timestamp. A calibration artifact is bound to one index generation and transfers with nothing else.

**False-route rate**: The proportion of accepted requests dispatched to a destination other than the adjudicated correct one, computed over labelled accepted requests. It is the risk half of the operating point and is never reported without its coverage.

**False-fallback rate**: The proportion of in-scope requests sent to fallback, clarification, escalation, or human review despite a correct destination existing and being identifiable. It is the cost half of the operating point, and a floor fitted without measuring it produces a router that declines almost everything and reports excellent accuracy.

**Coverage**: The proportion of eligible requests the router accepts automatically. Coverage and false-route rate move against one another as the floor moves, and neither is interpretable alone.

**Deterministic baseline**: The simplest correct non-vector router for the same destination set, built from authenticated metadata fields, exact patterns, and lexical matching. Every embedding router is measured against it, and the baseline wins ties.

**Dispatcher**: The deterministic component that validates a routing decision against the registry, enforces authorization and tenancy, applies budgets, and executes. It never executes an identifier the registry does not currently contain and never treats a similarity value as a permission.

**Misroute**: A dispatched request that reaches a handler unable to complete it, whether because it falls outside the handler's inclusion criteria, requires tools the handler does not hold, or requires data the handler may not access. A misroute is a routing failure even where the handler produces fluent output.

**Handler rejection**: The typed record a handler returns in place of a result when it detects that it received a misroute, carrying a reason code from a closed list, the evidence for the rejection, and zero or more suggested destinations that the dispatcher treats as advisory only.

**Taxonomy version**: The identifier of the destination set in force for a decision, recorded on every routing decision so that a decision made under one vocabulary is never replayed, cached, or scored under another.

**Approximate nearest-neighbour recall**: The fraction of the exact top-k neighbours an approximate index recovers. It is an index-quality measure and not a routing measure: a high recall can still route badly, and a small recall loss near a floor can flip an acceptance into a rejection.

**Exact-search oracle**: The brute-force similarity computation over the same vectors, retained permanently as the correctness reference against which every approximate index, quantization setting, and filter configuration is validated.

### 1.2 Similarity Is Not Eligibility

This subsection states the property that governs every later phase. A nearest-neighbour lookup is a closed-set operation: given any query vector and any non-empty index, it returns a nearest entry. The operation carries no notion of relevance, only of relative proximity. A request about payroll submitted to a router whose destinations are all network-infrastructure queues returns a network destination with a similarity value that looks ordinary, and nothing in the mechanism marks the result as unsupported. This is the characteristic production failure of the method, and it is silent by construction.

**Ranking answers a different question from eligibility**: A ranking states which destination is closest. Eligibility states whether any destination is close enough to act on. A router that publishes only a ranking has answered the first question and left the second unasked, so it routes unrelated traffic with the same apparent confidence it routes ordinary traffic.

**A softmax over similarities does not supply the missing answer**: Applying a temperature and a softmax to a similarity vector normalises mass across the destinations presented, which is a closed-set operation over the same closed set. The result can concentrate above 0.95 on one destination when every destination is wrong, because the normalisation cannot represent the possibility that the correct answer is absent from the candidate list. Published calibration work defines confidence calibration as agreement between predicted probability and empirical correctness and reports that modern neural predictions are frequently poorly calibrated; a normalised similarity therefore carries no probability meaning until it is validated against observed correctness on held-out data [3].

**Three independent gates are required, and all three must hold**: Acceptance requires that the winning destination's aggregated score meets that destination's fitted similarity floor, that the decision margin meets the configured separation threshold, and that neighbour support meets the configured minimum. The floor answers whether the request belongs to the destination set at all. The margin answers whether it belongs to this destination rather than its neighbour. Support answers whether the evidence is a region or a single point. A gate set that omits the floor cannot decline; a set that omits the margin dispatches coin-flips; a set that omits support lets one mislabelled or poisoned exemplar carry a decision.

**Failing the gates is a declared outcome, not an exception**: Where no destination clears all three gates, the router emits open-set rejection and the request proceeds to a named path: a bounded clarification turn, escalation to a model-based router, a default destination with the least privilege in the set, or a human review queue. The path is declared in the destination registry before deployment, holds a named owner and a service objective, and is measured. A router that cannot support a none-of-the-above outcome must not be deployed, because its only available behaviour on unsupported traffic is a confident misroute.

**Fallback never widens authority**: A fallback destination must hold a tool scope, data scope, and side-effect class no broader than the destination it replaces. Escalation to a model-based router may only re-select among the destinations already eligible for the request, and may return clarification, abstention, or human review. Index unavailability may fall back to an exact in-memory snapshot only where that snapshot is current and tenant-correct; it never falls back to the unthresholded top result.

### 1.3 The Execution Tier Partition

The tier partition is this guide's principal structural claim and the property that distinguishes embedding-based routing from model-based routing. In model-based routing an inference call holds a genuine judgement and the deterministic tier constrains it. In embedding-based routing the deterministic tier holds the entire request-time decision.

**Deterministic tier**: Software, schema validators, policy engines, and stores own the destination registry and its closed vocabulary, the exemplar store and its approval workflow, embedding revision pinning and coverage accounting, index generation construction and alias switching, eligibility and tenancy filtering applied before ranking, the similarity computation itself, aggregation, floor and margin and support evaluation, fallback selection, re-route counting, authorization enforcement, cost and latency accounting, and routing-accuracy measurement. These require exactness, reproducibility, and auditability: two evaluations of the same frozen decision set must return identical figures, and a dispatch made two years ago must be reconstructible from its recorded generation identifiers. This tier rejects, rather than repairs, any vector whose recorded revision differs from the serving generation's pin, any retrieval result naming an identifier absent from the registry at the decision's taxonomy version, any result from a deleted or expired or cross-tenant exemplar, any decision whose calibration artifact version does not match the serving generation, and any acceptance where a gate was not evaluated.

**Model tier**: At request time the model tier owns nothing. The embedding call is a deterministic transformation from text to a vector under a pinned revision, not a judgement: the same input under the same revision and preprocessing yields the same vector, and the call has no access to the destination set, the thresholds, or the outcome. This is the property that makes the method reproducible and cheap, and it is also the method's limitation, since nothing in the request path can reason about a novel request that the exemplar sets do not cover. Model inference has genuine authority only outside the request path, in bounded proposal roles: drafting candidate exemplar and hard-negative texts for human review, clustering and labelling error groups during diagnosis, and drafting inclusion and exclusion criteria for destination records. None of these outputs enters a serving index without a recorded human approval.

**Hybrid tier**: The model proposes and software verifies, or software retrieves and a model adjudicates, with authority fixed in advance and independent of the content of the disagreement. Where the router's gates fail and escalation to a model-based router is configured, the model adjudicates among the already-eligible candidate set and software revalidates its answer against the registry and the policy plane; where the model names a destination outside the eligible set, the deterministic tier discards the answer and applies the fallback. Where a handler rejection contradicts an accepted routing decision, the rejection holds and the request enters the bounded re-route path. Where a deterministic policy check and any similarity evidence conflict, the policy check holds without exception and the disagreement is recorded.

**Tier Ownership of Embedding-Routing Artifacts**:

| Routing artifact | Owning tier | Deterministic tier rejects | Model tier may never decide alone |
| :-- | :-- | :-- | :-- |
| Destination registry entries | Deterministic | Records lacking owner, criteria, risk class, or declared fallback | Any registry content |
| Exemplar admission to a serving index | Hybrid | Exemplars lacking provenance, reviewer, or approval state | Whether its own drafted exemplar is admitted |
| Embedding revision pin | Deterministic | Any vector whose recorded revision differs from the generation pin | Any pin or its enforcement |
| Query encoding | Deterministic | Vectors of wrong dimension, wrong dtype, non-finite values, or wrong norm | Nothing; the call is a transformation, not a decision |
| Similarity computation and aggregation | Deterministic | Comparisons spanning two embedding revisions or two generations | Any score |
| Similarity floor, margin, and support values | Deterministic | Thresholds fitted on the final holdout partition | Any threshold or its comparison outcome |
| Gate evaluation and acceptance | Deterministic | Acceptances where any of the three gates was unevaluated | Whether evidence is sufficient |
| Open-set rejection and fallback selection | Deterministic | Fallbacks widening tool scope, data scope, or side-effect class | Which fallback applies |
| Escalation adjudication among eligible candidates | Hybrid | Selections outside the eligible candidate set | Whether escalation is permitted for the risk tier |
| Authorization, tenancy, and residency enforcement | Deterministic | Any dispatch lacking a current authorization decision | Any authorization outcome |
| Approximate index parameters and quantization | Deterministic | Configurations not validated against the exact-search oracle | Any index configuration |
| Routing accuracy and open-set rate measurement | Deterministic | Figures computed on data used for threshold fitting | Any reported figure |
| Cross-assignment and imbalance diagnosis | Hybrid | Diagnoses lacking the underlying similarity evidence | Whether a destination pair is merged or split |

### 1.4 The Method Selection Gate

Embedding routing is one of four routing families and is not the default among them. Agents must run a selection gate before construction begins, returning adopt, suppress with a named substitute, or reject.

**Adoption conditions**: Adopt embedding routing where all of the following hold materially. Destination membership is primarily semantic rather than derivable from trusted structured fields. At least 2 destinations remain after cosmetic duplicates are merged. Each destination can be described by at least 20 reviewed positive exemplars covering its distinct semantic modes. Independent annotators agree on destination labels for at least 85 percent of a representative sample of 200 requests. A labelled corpus of at least 1,000 requests exists or can be built, spanning in-scope, boundary, and out-of-scope cases. A wrong destination is detectable through handler rejection, user correction, or human review. The traffic mix is stable enough that a threshold fitted today remains defensible for at least 30 days.

**Suppression conditions**: Suppress the router and name the substitute where a deterministic predicate over authenticated metadata, an API path, an explicit user selection, a tenant or region attribute, or a stable exact pattern already identifies the destination for at least 98 percent of traffic. Suppress where the decision is an authorization, compliance, residency, entitlement, or payment determination that must bind deterministically. Suppress where destination distinctions turn on numeric constraints, exact identifiers, negation-sensitive policy, or code syntax that similarity cannot represent. Suppress where the deterministic baseline comes within 3 percentage points of the embedding router's routing accuracy on the frozen evaluation set, because the baseline is cheaper, reproducible without an encoder, and auditable by inspection. Suppress where the taxonomy requires compositional reasoning about missing context, and use a model-based router for the residual traffic instead.

**Rejection conditions**: Reject the router outright where no adjudicated label source for routing correctness exists at any latency, because the floor can never be fitted and the false-route rate can never be computed. Reject where the deployment cannot support an open-set rejection outcome, because the only remaining behaviour on unsupported traffic is a confident misroute. Reject where the organisation cannot retain and govern canonical exemplar text, because a corpus that cannot be re-encoded cannot survive an embedding revision change.

**Method Selection Gate Decision Table**:

| Observable condition | Available substitute | Gate verdict |
| :-- | :-- | :-- |
| Destination derivable from an authenticated field for at least 98 percent of traffic | Deterministic rule set | Suppress; deploy the rule |
| Binding authorization, residency, entitlement, or payment determination | Policy engine | Suppress; policy code decides |
| Distinctions turn on exact identifiers, amounts, or negation | Lexical or rule matching | Suppress; similarity cannot represent the distinction |
| Deterministic baseline within 3 percentage points of the vector router | Deterministic baseline | Suppress; the baseline wins ties |
| Stable, high-volume, well-separated semantic classes with 20 or more exemplars each | Exemplar index | Adopt embedding routing |
| Multilingual or paraphrase-heavy traffic over a stable destination set | Exemplar index | Adopt embedding routing |
| Very large labelled corpus, stable labels, latency budget under 50 milliseconds | Supervised classifier | Suppress; the classifier is cheaper per request at scale |
| Nuanced, fast-changing taxonomy needing compositional reasoning | Model-based router | Suppress; use the model router |
| Uncertain middle after floor and margin evaluation | Model-based router | Adopt embedding routing as the first stage and escalate the residual |
| No adjudicated routing label obtainable at any latency | None | Reject; the floor cannot be fitted |
| Open-set rejection outcome cannot be supported | None | Reject; instrument a fallback path first |

**Numeric gate rules**: Where annotator agreement falls below 85 percent on the 200-request sample, halt and repair the taxonomy by merging destinations, sharpening exclusion criteria, or adding decisive trusted context; a taxonomy humans cannot label consistently cannot be encoded consistently. Where any destination holds fewer than 20 reviewed positive exemplars after curation, that destination is excluded from automatic acceptance and routed to human review until its set is complete. Where the labelled corpus holds fewer than 1,000 requests, deploy in shadow mode only and accept no traffic automatically, because a floor fitted on a smaller set has confidence intervals wider than the difference it is meant to detect.

***

## II. Operational Framework: Calibrated Nearest-Exemplar Dispatch Under a Pinned Embedding Generation

The framework produces a versioned routing system comprising a destination registry, an approved exemplar corpus, one pinned index generation, one calibration artifact carrying per-destination floors with their measured error rates, a gated dispatch path with a declared fallback, and a drift monitor with named refit and re-embed triggers. Phases execute in order, and each consumes only artifacts produced by an earlier phase.

### Phase 1: Destination Declaration and Routing Contract Establishment

**Objective**: Fix what the router chooses among, what it may never choose, and what record it emits, so that every later measurement has a stable referent and no similarity result can widen authority.

#### Step 1.1: Declare the Routing Decision and Its Authority Boundary

**Required Actions**:

- Write one sentence stating what the embedding router selects and one sentence stating what it may never select, and record both in the routing contract.
- Enumerate every determination that must bind deterministically, covering authorization, tenancy, residency, entitlement, payment state, write permission, modality support, and content prohibition, and assign each to policy code executing before and after the similarity computation.
- Name the registry owner, the policy owner, the exemplar approval owner, and the human review queue owner, with one accountable owner per role.
- Halt and redesign where any path exists by which a similarity value alone could widen tool scope, widen data scope, bypass a confirmation step, or select a destination the requesting principal is not entitled to reach.

**Required Outputs**:

- A routing contract stating the selection scope and the prohibition scope in one sentence each.
- A deterministic-determination inventory naming every constraint that policy code owns.
- An owner assignment covering registry, policy, exemplar approval, and human review.

**Quality Checkpoints**:

- The prohibition sentence names at least 3 determinations the router may never make.
- Every determination in the inventory has an enforcement point executing outside the similarity path, and 100 percent of them execute before dispatch.
- No path exists by which an accepted routing decision alone authorizes an action; a single such path halts the phase.

***

#### Step 1.2: Publish the Versioned Destination Registry With Separable Criteria

**Required Actions**:

- Create one registry record per destination carrying a stable identifier, owner, purpose, inclusion criteria, exclusion criteria, named confusing neighbours, accepted languages and modalities, required trusted context, handler contract, risk class, allowed tool and data scope, side-effect class, latency objective, and declared fallback.
- Merge any pair of destinations that differ only in wording, that share a handler with identical tool and data scope, or that no annotator pair can separate; record every merge with its evidence.
- Write inclusion and exclusion criteria as prose an independent annotator can apply without access to the exemplar set, since criteria that only make sense alongside examples cannot adjudicate a disputed label.
- Assign a monotonically increasing taxonomy version to the registry and require that every routing decision, exemplar, index generation, and calibration artifact record the version it was produced under.
- Verify criteria separability by having 2 or more qualified reviewers independently label a representative sample of 200 requests against the criteria alone.

**Required Outputs**:

- A destination registry at a stated taxonomy version with one complete record per destination.
- A merge log naming every collapsed destination pair and the evidence for the merge.
- An annotator agreement measurement over the 200-request sample, reported per destination and in aggregate.

**Quality Checkpoints**:

- Every registry record carries all 14 required fields; a record missing any field is not published.
- Aggregate annotator agreement is at least 85 percent, and no single destination falls below 70 percent; a destination below 70 percent is merged, split, or given sharper exclusion criteria before it enters the exemplar phase.
- At least 2 destinations remain after merging; fewer than 2 terminates the routing effort and returns a single parameterised handler.
- No identifier in the current registry has ever carried a different meaning in an earlier taxonomy version.

***

#### Step 1.3: Fix the Routing Decision Record and Measure the Deterministic Baseline

**Required Actions**:

- Define the routing decision record as a typed structure carrying the fields enumerated in the schema template below, and reject any decision emitted without all of them.
- Declare the closed set of decision types: accept single, accept bounded multiple, clarify, abstain to fallback, escalate, deny, and human review.
- Implement the deterministic baseline over the same destination set, built from authenticated metadata predicates, exact patterns, and a lexical index, and measure its routing accuracy, coverage, latency, and cost on the labelled corpus.
- Record the baseline figures in the routing contract as the bar every later configuration must clear.

**Routing Decision Record Schema**:

```
schema_version:
taxonomy_version:
decision_id:
request_id:
tenant_scope:
eligible_destination_count:
decision_type:            one of accept_single | accept_multi | clarify | abstain | escalate | deny | human_review
selected_destination:
ranked_alternatives:      [identifier, aggregated_score] up to 3
top_score:
second_score:
decision_margin:
neighbour_support_count:
aggregation_rule:
floor_applied:
margin_threshold_applied:
support_minimum_applied:
gates_evaluated:          [floor, margin, support] all must be present
embedding_revision:
preprocessing_version:
index_generation:
calibration_artifact_version:
exemplar_snapshot_checksum:
retrieval_mode:           exact | approximate
cache_status:
policy_outcome:
reason_code:              from the closed reason-code list
```

**Required Outputs**:

- A routing decision record schema with every field typed and required-or-optional marked.
- A closed decision-type enumeration with an owner and a service objective per non-accepting type.
- A baseline measurement record with routing accuracy, coverage, median and 95th-percentile latency, and cost per request.

**Quality Checkpoints**:

- The decision record carries the embedding revision, index generation, calibration artifact version, taxonomy version, and preprocessing version on every emission; a decision missing any version field is unreconstructible and is rejected.
- Every non-accepting decision type has a named owner and a stated service objective, so no outcome is an unhandled error.
- The baseline is measured on the same frozen partition later used to evaluate the vector router, so the comparison is like for like.

***

### Phase 2: Exemplar Set Construction and Quality Validation

**Objective**: Build an approved, provenance-bearing exemplar corpus whose sets are balanced, whose boundaries are populated by reviewed hard negatives, and whose cross-assignments have been measured and resolved, so that the index encodes the destination taxonomy rather than an accident of collection.

#### Step 2.1: Curate Positive Exemplars Across Semantic Modes and Balance the Sets

**Required Actions**:

- Collect authentic, privacy-approved requests for each destination, covering its distinct semantic modes, supported languages, input lengths, channels, terminology registers, and ordinary spelling variation.
- Reject an arbitrary equal quota per destination; instead add exemplars in batches of 10 and measure held-out routing accuracy after each batch, stopping when 2 consecutive batches improve accuracy by less than 1 percentage point and boundary coverage adds no new confusion pair.
- Cap the largest exemplar set at no more than 3 times the size of the smallest set that passed the plateau test, or apply class-balanced aggregation, or demonstrate by ablation that imbalance does not shift the winning destination on the boundary slice; adopt exactly one of these three remedies and record which.
- Group exact duplicates, templated near-duplicates, and exemplars from one conversation family into one partition before splitting, so that leakage cannot inflate held-out results.
- Mark every synthetic exemplar with its generator identifier, prompt version, seed, source exemplar, generation time, and reviewer state, and cap synthetic exemplars at no more than 40 percent of any destination's set.

**Required Outputs**:

- An approved positive exemplar corpus with complete metadata per exemplar.
- A learning-curve record per destination showing accuracy against exemplar count in batches of 10.
- An imbalance remedy declaration naming the adopted remedy and its evidence.
- A partition assignment grouping duplicates and conversation families before the split.

**Quality Checkpoints**:

- Every destination holds at least 20 reviewed positive exemplars; a destination below 20 is excluded from automatic acceptance and routed to human review.
- The ratio of the largest to the smallest exemplar set is at most 3 to 1, or a declared remedy is in force with recorded ablation evidence.
- Synthetic exemplars constitute at most 40 percent of any destination's set, and 100 percent of them carry a recorded human reviewer; a synthetic exemplar approved only by its generator is removed.
- No exemplar appears in two partitions, and no conversation family spans a partition boundary.

***

#### Step 2.2: Mine and Review Hard Negatives and Boundary Cases

**Required Actions**:

- Generate easy negatives to establish broad separation and hard negatives by nearest-neighbour search from each destination's representation into the exemplar pools of its named confusing neighbours, using score ranges and margins to select candidates [7].
- Route every mined negative through human review before admission, because a candidate selected for being close to a destination is exactly the candidate most likely to be an unlabelled positive.
- Populate each named confusing-neighbour pair with at least 10 reviewed boundary cases, defined as requests a competent annotator can assign correctly but only after applying an exclusion criterion.
- Collect representative out-of-scope requests spanning at least 3 distinct sources: adjacent business domains, malformed or truncated inputs, and traffic the deployment explicitly does not serve; hold at least 200 such requests for the calibration partition.
- Add adjudicated production errors and human corrections continuously, treating them as higher-value additions than any generated variant.

**Required Outputs**:

- A reviewed hard-negative set attached to each confusing-neighbour pair.
- A boundary-case set of at least 10 reviewed items per confusing-neighbour pair.
- An out-of-scope corpus of at least 200 labelled requests spanning at least 3 sources.
- A production-error intake record showing adjudication status per item.

**Quality Checkpoints**:

- Every confusing-neighbour pair declared in the registry carries at least 10 boundary cases and at least 5 reviewed hard negatives; an unpopulated pair blocks calibration, because the floor and margin cannot be fitted where the boundary is unobserved.
- Mined negatives reclassified as positives during review are recorded with the reclassification reason, and a reclassification rate above 20 percent triggers a taxonomy review rather than a further mining pass.
- The out-of-scope corpus is drawn from real traffic or realistic construction, not from random unrelated text, since trivially distant unknowns produce a floor that passes calibration and fails production.

***

#### Step 2.3: Detect Cross-Assigned Exemplars and Resolve the Cause

**Required Actions**:

- Encode every approved exemplar under the candidate embedding revision and compute, for each exemplar, the similarity to its own destination's representation and to every other destination's representation.
- Flag as cross-assigned any exemplar whose similarity to another destination's representation exceeds the similarity to its own, and record the competing destination and the gap.
- Compute the cross-assignment rate per destination and per destination pair, and rank pairs by their bidirectional rate.
- Adjudicate every flagged exemplar to exactly one of three causes: a labelling error on that exemplar, a criteria defect where the registry's inclusion or exclusion text does not distinguish the pair, or a genuine destination overlap where no criteria wording can separate them.
- Apply the resolution matched to the cause: correct the label and re-run the check; sharpen the exclusion criteria and re-adjudicate the affected exemplars; or merge the destination pair, split it along a different axis, or promote the ambiguous region to a clarification path.

**Required Outputs**:

- A cross-assignment report listing every flagged exemplar with its own-destination similarity, competing-destination similarity, and gap.
- A per-pair cross-assignment rate table ranked by bidirectional rate.
- An adjudication record assigning one of three causes and one applied resolution to every flagged exemplar.

**Quality Checkpoints**:

- Cross-assignment rate is at most 5 percent per destination after resolution; a destination above 5 percent does not enter a serving index, because its exemplar set does not describe a coherent region.
- No destination pair carries a bidirectional cross-assignment rate above 10 percent; a pair above 10 percent is merged, re-split, or given a clarification path, and no threshold value can compensate for it.
- Every flagged exemplar has an adjudicated cause; flagged exemplars silently deleted without a recorded cause constitute an undocumented taxonomy change.
- The check is re-run in full after any exemplar addition, label change, or embedding revision change, since cross-assignment is a property of the exemplar set and the encoder jointly.

***

### Phase 3: Embedding Revision Selection and Index Generation Pinning

**Objective**: Select an encoder on local evidence, pin its complete identity as an immutable revision, and build one immutable index generation whose every vector carries that revision, so that scores remain comparable and an encoder change becomes a planned migration rather than a silent corruption.

#### Step 3.1: Shortlist Candidate Revisions and Benchmark on the Local Frozen Corpus

**Required Actions**:

- Shortlist 3 to 5 candidate encoders using published multi-task benchmark results filtered to the task families that resemble the production geometry, together with language coverage, sequence length, output dimension, licence, hosting model, privacy posture, throughput, and cost.
- Read task-level rather than aggregate benchmark results, since a single overall average conceals that a model strong on long-document retrieval may be weak on the classification and pair-similarity geometry that utterance-to-exemplar routing resembles [1].
- Test every supported language and every code-switching pattern locally rather than relying on a multilingual label, because multilingual benchmark evidence reports that performance varies sharply by task and language and that English-only models rank last outside English [2].
- Benchmark every shortlisted encoder on the frozen local corpus using the exact preprocessing, representation strategy, aggregation rule, and retrieval mode planned for production, and measure routing accuracy per destination, out-of-scope rejection rate, latency by batch size, throughput, memory, storage, and cost per request.
- Treat output dimension as a system parameter rather than a quality score, and truncate only encoders explicitly trained for dimensional truncation, recalibrating every downstream artifact for the chosen dimension [5].

**Required Outputs**:

- A shortlist record of 3 to 5 candidate encoders with the filter criteria applied.
- A local benchmark table reporting routing accuracy, out-of-scope rejection, latency, memory, and cost per candidate.
- A per-language and per-code-switching result set covering 100 percent of supported languages.

**Quality Checkpoints**:

- No candidate is selected on published benchmark position alone; selection cites the local frozen-corpus measurement.
- The selected encoder beats the deterministic baseline by at least 5 percentage points of routing accuracy on the frozen partition, or the baseline is deployed instead.
- Every supported language reaches at least 80 percent of the routing accuracy observed on the highest-performing language; a language below 80 percent is routed to a language-specific path or to human review rather than served silently.
- Where dimensional truncation is applied, the encoder's documentation states that it was trained for truncation; truncating an encoder not trained for it is a defect, not an optimisation.

***

#### Step 3.2: Pin the Representation Identity and Fix the Encoding Contract

**Required Actions**:

- Record for every stored vector the embedding model identifier, an immutable revision or checksum, the tokenizer, the pooling method, the precision, the output dimension, the normalisation mode, the distance metric, any query or passage prefix or instruction template, the input hash, and a vector checksum.
- Treat the revision as immutable rather than as a mutable provider alias, because a provider updating a model behind a stable name changes the space without changing the name and raises no error at any layer.
- Decide symmetric or asymmetric encoding from the encoder's documented training contract rather than by preference: symmetric where both sides are the same kind of object such as an utterance compared with utterance exemplars, asymmetric where the sides differ in role such as a short request compared with a longer destination description, applying the query prefix only to runtime queries and the passage prefix only to stored representations where the encoder specifies them [8].
- Fix the distance metric to the one the encoder prescribes, and make normalisation explicit at exactly one point in the pipeline; for unit-normalised vectors dot-product ranking equals cosine ranking and Euclidean ranking is monotonic with it, so the metric choice must be recorded rather than assumed [4].
- Prohibit any similarity computation spanning two revisions, two dimensions, two prefixes, two normalisation conventions, or two preprocessing versions, and enforce the prohibition in code rather than in documentation.

**Required Outputs**:

- A representation record per vector carrying revision, tokenizer, pooling, precision, dimension, normalisation, metric, prefix version, and checksum.
- An encoding contract declaring symmetric or asymmetric mode with the documentation reference that justifies it.
- A normalisation assertion point with a logged pre-normalisation norm distribution.

**Quality Checkpoints**:

- Recorded revision equals the serving generation's pinned revision for 100 percent of vectors; any non-zero mismatch count blocks the generation from serving.
- Observed vector dimension, dtype, finiteness, and norm are validated on every encode call, and a mismatch fails the request rather than proceeding to comparison.
- Symmetric and asymmetric modes were compared empirically on the frozen corpus, and the selected mode is the one with higher measured routing accuracy, not the one assumed from the encoder's family.
- No two vectors from different revisions are compared as though their distances were calibrated; a cross-revision comparison is a defect, not an approximation.

***

#### Step 3.3: Build the Index Generation and Validate Approximation Against the Exact Oracle

**Required Actions**:

- Build each index generation from a canonical exemplar snapshot rather than from an existing index, and name the generation with its manifest: revision and checksum, tokenizer and preprocessor versions, prefix version, dimension, dtype and quantization, normalisation, metric, exemplar snapshot checksum, index algorithm and parameters, build code version, build time, validation results, tenant scope, and parent generation.
- Retain exact search as the permanent correctness oracle, and deploy exact search alone where the exemplar catalogue is small enough to meet the latency, throughput, and memory objectives, since approximation adds a failure mode without adding accuracy.
- Adopt an approximate index only after exact search demonstrably fails a measured service objective, then tune its parameters against exact ground truth under production-like filters, concurrency, update rates, and tenant partitioning [11].
- Verify whether the engine applies metadata filters before or after graph or list traversal, because post-filtering can return too few candidates and distort recall precisely on the selective queries eligibility filtering produces [12][13].
- Measure quantization impact on top-one destination agreement, decision margin, and accepted-case error rather than on neighbour recall alone, and expose serving traffic to a generation only through an alias pointing to exactly one approved generation.

**Required Outputs**:

- An immutable index generation with a complete manifest and a coverage report stating covered, excluded, and pending exemplar counts.
- An approximation validation report comparing the approximate index to the exact oracle on neighbour recall, top-one agreement, margin shift, and post-gate decision agreement.
- A filter behaviour test report covering selective, compound, and negated predicates under production-like concurrency.

**Quality Checkpoints**:

- Coverage of approved exemplars is 100 percent, or every gap appears in a documented exclusion set with a reason code; an undocumented gap blocks promotion of the generation.
- Approximate top-one destination agreement with the exact oracle is at least 99 percent, and post-gate decision agreement is at least 99.5 percent; below either figure the approximate configuration is retuned or exact search is retained.
- Neighbour recall alone never approves a configuration, because a small recall loss on a neighbour sitting near a floor changes an acceptance into a rejection while leaving recall figures respectable.
- The serving alias points to exactly one generation at a time, so no request is answered from two embedding spaces at once.

***

### Phase 4: Aggregation Selection and Threshold Calibration

**Objective**: Fit the aggregation rule, the per-destination similarity floor, the decision margin, and the neighbour-support minimum on labelled data with false-route and false-fallback rates measured separately, so that acceptance rests on evidence rather than on intuition.

#### Step 4.1: Select the Aggregation Rule Against Exemplar Imbalance

**Required Actions**:

- Evaluate all 4 aggregation rules against the same frozen partition rather than assuming one is best: maximum similarity over exemplars, similarity to a single centroid, similarity to the nearest of several subcluster centroids, and class-balanced nearest-neighbour voting.
- Discover subclusters within each destination's exemplar set before selecting between single and multiple centroids, and record the subcluster identifier on every decision so that a minority mode losing coverage is visible rather than invisible.
- Test each rule specifically on the imbalance slice, comparing decisions for requests whose correct destination holds the smallest exemplar set against those whose correct destination holds the largest.
- Where nearest-neighbour voting is selected, fix the neighbour count, the class-size correction, the tie-break order, and the minimum supporting-neighbour count, and validate each independently rather than as a bundle.
- Report both the winning aggregated score and the evidence concentration on every decision, since three mutually close neighbours from one destination and one isolated match at the same score are different evidential situations.

**Aggregation Rule Selection Properties**:

| Aggregation rule | Preserves minority modes | Sensitivity to one bad exemplar | Sensitivity to set-size imbalance | Preferred where |
| :-- | :-- | :-- | :-- | :-- |
| Maximum similarity over exemplars | Full | High; one poisoned or mislabelled exemplar can decide | High; denser sets win more often | Destinations with distinct sub-intents and a strict exemplar approval path |
| Single centroid | None; distinct modes average away | Low; one exemplar shifts the mean slightly | Low | Narrow destinations whose exemplars form one coherent cluster |
| Multiple subcluster centroids | Partial; one per discovered mode | Low to moderate | Low | Broad destinations that resist splitting into separate registry records |
| Class-balanced nearest-neighbour voting | Partial | Low; requires agreement across neighbours | Low by construction | Sets that cannot be balanced by capping, and high-risk destinations needing support evidence |

**Required Outputs**:

- An aggregation comparison table reporting routing accuracy, out-of-scope rejection, and imbalance-slice accuracy per rule.
- A subcluster map per destination with a stable subcluster identifier per centroid.
- A selected aggregation rule with its parameters fixed and versioned into the calibration artifact.

**Quality Checkpoints**:

- All 4 rules were measured on the identical frozen partition; a selection made without the comparison is unsupported.
- Imbalance-slice accuracy for the smallest exemplar sets is within 5 percentage points of the accuracy for the largest sets; a larger gap means the rule is rewarding exemplar density rather than semantic fit, and either class-balanced aggregation or exemplar capping is applied.
- Where maximum similarity is selected for a destination whose risk class is high, a minimum neighbour support of at least 2 is enforced, because a single exemplar cannot carry a high-impact dispatch.

***

#### Step 4.2: Fit the Similarity Floor and Margin on a Disjoint Labelled Partition

**Required Actions**:

- Partition the labelled corpus into disjoint exemplar-selection, calibration, development, temporal-holdout, and final-holdout sets, grouping duplicates and conversation families before splitting, and seal the final holdout until release.
- Require a calibration partition of at least 300 labelled in-scope requests spanning every destination, at least 30 labelled requests for every destination whose floor is fitted individually, and at least 200 labelled out-of-scope requests; a destination with fewer than 30 calibration requests receives the global conservative floor rather than an individually fitted one.
- Plot, per destination, the aggregated-score distributions for correct positives, wrong-destination negatives, and out-of-scope requests, and select the floor from the separation these three distributions show rather than from a round number or a published default.
- Sweep the floor and the margin jointly across the development partition and record, at every operating point, the false-route rate, the false-fallback rate, and the coverage as three separate figures; never collapse them into a single accuracy number, because a floor that maximises accuracy on a corpus with few unknowns is the floor that forces unknowns into known destinations.
- Fit per-destination floors rather than one global cutoff wherever the calibration data supports it, since score scales differ by destination density, language, and input length, and published open-set classification work uses class-specific thresholds rather than a single global cutoff [14].
- Where a normalised confidence is published alongside the raw score, validate it by comparing predicted probability against observed correctness in predeclared bins with recorded sample counts, marking sparse bins inconclusive, and label the value a calibrated confidence only after that test passes [3].

**Required Outputs**:

- A disjoint partition manifest naming every partition, its size, and its grouping rule.
- Per-destination score distribution records for correct positives, wrong-destination negatives, and out-of-scope requests.
- An operating-point sweep table reporting false-route rate, false-fallback rate, and coverage at each floor and margin combination.
- A calibration artifact carrying every fitted floor, margin, and support minimum with the partition identifiers used.

**Quality Checkpoints**:

- No threshold was fitted, tuned, or selected on the final holdout; a single such use invalidates the holdout and requires a new one.
- Every fitted floor rests on at least 30 labelled calibration requests for its destination; destinations below 30 carry the global conservative floor and are named in the calibration artifact.
- False-route rate and false-fallback rate are reported separately at the selected operating point; a calibration artifact reporting only one of the two is incomplete and does not enter service.
- The out-of-scope partition contains at least 200 requests drawn from realistic sources, since a floor validated only against trivially distant unknowns will not hold against adjacent-domain traffic.

***

#### Step 4.3: Certify the Operating Point and Set Risk-Tiered Acceptance

**Required Actions**:

- Predeclare the accepted-case risk target before selecting the operating point, expressed as a maximum false-route rate over labelled accepted requests, and select the floor and margin that meet it, then report the coverage that results rather than selecting for coverage and reporting the risk that results.
- Set risk-tiered acceptance so that a low-risk read-only destination may accept at a lower floor than a destination with irreversible side effects, and require for high-impact destinations a higher floor, a larger margin, a minimum neighbour support of at least 2, and an independent execution-time confirmation.
- Record the certification status of the calibration artifact, granting it only after the fit completes on held-out data and revoking it automatically whenever the embedding revision, preprocessing version, exemplar snapshot, aggregation rule, index generation, or taxonomy version changes.
- Where no operating point achieves both the risk target and a coverage of at least 50 percent of eligible requests, do not lower the risk target; instead merge the confusable destinations, add decisive trusted context to the routing text, escalate the uncertain band to a model-based router, or keep the decision human.
- Evaluate the frozen configuration exactly once on the final holdout and record the result as the release figure, whether or not it is favourable.

**Required Outputs**:

- A certified calibration artifact with per-destination floors, margins, support minima, risk tier, and certification status.
- A risk-tier assignment covering 100 percent of destinations with the acceptance requirements per tier.
- A single final-holdout evaluation record with the release figures.

**Quality Checkpoints**:

- Accepted-case false-route rate on the final holdout is at or below the predeclared target; above it, the release is blocked rather than the target revised.
- Coverage at the certified operating point is at least 50 percent of eligible requests, or the deployment records the structural remedy adopted instead of accepting a lower coverage silently.
- Certification is bound to the exact tuple of embedding revision, preprocessing version, exemplar snapshot checksum, aggregation rule, index generation, and taxonomy version, and any change to any element revokes it automatically.
- The final holdout was evaluated exactly once; a second evaluation of a revised configuration requires a new holdout.

***

### Phase 5: Gated Routing Execution and Bounded Fallback

**Objective**: Execute one routing decision per request under eligibility filtering applied before ranking, all three acceptance gates evaluated, and a declared fallback that never widens authority, so that an unsupported request receives a refusal rather than a confident misroute.

#### Step 5.1: Establish Eligibility and Normalise the Input Before Retrieval

**Required Actions**:

- Authenticate the principal, load the minimum current conversation state, and apply tenant, region, entitlement, modality, data-sensitivity, and risk policy to the destination registry, so that only eligible destination identifiers and their exemplar vectors enter retrieval.
- Emit the terminal decision immediately and stop where policy requires denial or human review, and abstain through the declared support path where no destination is eligible.
- Apply the versioned preprocessing pipeline covering Unicode normalisation, control-character and zero-width-character removal, whitespace collapsing, redaction, language detection, and truncation, and record its version on the decision.
- Extract trusted exact identifiers, product codes, and amounts separately and route them through lexical or rule matching rather than through similarity, since similarity does not represent exactness.
- Choose clarification, a rule path, or abstention rather than encoding where the request is empty, shorter than the configured minimum of 3 content tokens after normalisation, malformed, or dependent on unresolved conversation state; never pad a short request with invented context to manufacture semantic evidence.

**Required Outputs**:

- An eligible destination set computed before any similarity computation.
- A normalised routing text with its preprocessing version and truncation status recorded.
- An extracted exact-identifier set routed to the lexical or rule path.

**Quality Checkpoints**:

- Eligibility filtering precedes ranking on 100 percent of requests; a filter applied after ranking is a defect, because approximate retrieval can exhaust its candidate budget on ineligible entries and return too few eligible ones.
- Preprocessing is applied identically to runtime queries and to stored exemplars under the same version; a version mismatch between the two blocks the request.
- No request shorter than the configured minimum reaches the similarity path; such requests are clarified, matched lexically, or abstained.

***

#### Step 5.2: Encode, Retrieve, Aggregate, and Evaluate the Three Gates

**Required Actions**:

- Construct the documented symmetric input or asymmetric query instruction, call the pinned encoder within its deadline, and validate the returned vector's dimension, dtype, finiteness, and norm before any comparison.
- Retrieve candidates within the eligible, tenant-filtered corpus using the serving generation only, requesting enough neighbours for the configured aggregation and support evaluation while obeying candidate, time, and cost budgets, and reject stale, deleted, expired, ineligible, or cross-tenant results.
- Run lexical retrieval alongside dense retrieval where exact tokens and semantics both matter, preserve each ranking and score independently, and fuse only after eligibility filtering using a rank-based fusion method that does not require the two score scales to be comparable [9][10]; recalibrate the floor after fusion rather than reusing a dense-only floor.
- Compute the aggregated score per eligible destination using the certified aggregation rule, then evaluate all 3 gates explicitly and record each outcome: the winning score against its destination's floor, the decision margin against the margin threshold, and the neighbour support against the support minimum.
- Apply a reranking stage only where the decision falls inside the configured rerank band, restricting it to a bounded shortlist and including its latency and cost in the routing budget [6].

**Required Outputs**:

- A validated query vector with its recorded revision and preprocessing version.
- A per-destination aggregated score set with neighbour identifiers, scores, and support counts.
- A gate evaluation record naming each of the 3 gates with its threshold, its measured value, and its pass or fail outcome.

**Quality Checkpoints**:

- The gate evaluation record shows all 3 gates evaluated on 100 percent of accepted decisions; an acceptance recorded with any gate unevaluated is rejected by the dispatcher.
- The query vector's revision equals the serving generation's pinned revision; a mismatch fails the request rather than proceeding to a comparison across two spaces.
- No aggregated score is presented as a probability of correctness anywhere in the decision record, in telemetry, or in a user-facing message unless its calibration was certified under Step 4.2.
- Retrieval returns only currently eligible identifiers; a single ineligible identifier surviving into the candidate set is an eligibility-filter defect and halts serving.

***

#### Step 5.3: Execute the Declared Fallback or Escalation Without Widening Authority

**Required Actions**:

- Dispatch only where all 3 gates pass, and re-authorize the selected destination at execution time against the current principal, target resource, side-effect class, and policy, treating the routing decision as evidence about language rather than as permission.
- Ask exactly 1 bounded clarification question where the floor passes but the margin fails and a single missing fact would separate the top candidates; on the answer, reload trusted state, recompute eligibility, invalidate stale decision caches, re-encode, and re-evaluate every gate.
- Escalate to a model-based router where configured and where the uncertain band applies, passing the bounded eligible candidate set, sanitised context, and reason code, and permitting the escalated router to select only among the already-eligible candidates or to return clarification, abstention, or human review.
- Route to the declared fallback where the floor fails, selecting a destination whose tool scope, data scope, and side-effect class are no broader than any candidate it replaces, and never to the unthresholded nearest destination.
- Bound the uncertainty loop by a maximum of 2 clarification turns, 1 escalation attempt, and 3 total dispatch attempts including handler rejections, maintaining a visited-destination set so a request cannot circulate, and terminate in abstention or human review when any bound is reached; never lower a threshold at request time to complete a decision.

**Required Outputs**:

- A dispatch record with an independent execution-time authorization decision.
- A terminal decision record for every request, carrying exactly one decision type and one reason code.
- A fallback chain record naming each attempted path, its outcome, and the bound that terminated the loop.

**Quality Checkpoints**:

- Every request terminates in exactly 1 decision type; a request with no terminal record is a telemetry defect and is treated as an incident.
- No fallback or escalation path increases tool scope, data scope, side-effect class, residency, or candidate breadth relative to the path it replaces; a single widening path blocks release.
- Thresholds are never modified at request time; a runtime threshold change is a configuration change requiring a new calibration artifact version.
- The visited-destination set is enforced, and no request exceeds 3 dispatch attempts; exceeding the bound routes to human review with the full attempt history.

***

### Phase 6: Drift Detection, Threshold Refit, and Re-Embedding Migration

**Objective**: Detect the three drift classes separately, fire a refit on a named numeric trigger before quality degrades, and execute any encoder change as a full versioned re-embed, so that a fitted threshold does not decay unobserved and a revision change does not corrupt the space.

#### Step 6.1: Measure Routing Quality With Explicit Denominators

**Required Actions**:

- Define and publish the denominators before computing any metric: original request, eligible request, accepted request, labelled request, in-scope request, out-of-scope request, and index query, and report the time window, traffic slice, taxonomy version, embedding revision, index generation, and calibration artifact version alongside every figure.
- Report routing accuracy as correct top-one decisions over labelled single-destination requests, disaggregated per destination as macro and traffic-weighted precision, recall, and confusion pairs, rather than as an aggregate alone.
- Report the operating point as three separate figures on every cycle: coverage as accepted over eligible requests, false-route rate as incorrectly routed over labelled accepted requests, and false-fallback rate as in-scope requests sent to fallback, clarification, escalation, or human review despite an identifiable correct destination.
- Report out-of-scope recall as correctly rejected out-of-scope requests over labelled out-of-scope requests, and out-of-scope false-accept rate as out-of-scope requests accepted into a known destination over labelled out-of-scope requests.
- Measure routing correctness separately from downstream task success, since a correct destination with a failed handler is a handler failure and an incorrect destination with a fortunate result is still a routing error.
- Sample for adjudication across 6 strata every cycle: low-score cases, low-margin cases, clarified cases, abstained cases, escalated cases, and a random sample of at least 100 high-confidence accepted decisions, because only the random stratum detects confident systematic error.

**Required Outputs**:

- A denominator definition record published alongside every metric report.
- A per-destination quality report with macro and traffic-weighted figures and the confusion-pair table.
- An operating-point report carrying coverage, false-route rate, and false-fallback rate as three named figures.
- A stratified adjudication sample covering all 6 strata with recorded sample counts and sampling probabilities.

**Quality Checkpoints**:

- Every published metric names its denominator; a figure without a denominator is not published.
- The random high-confidence stratum contains at least 100 adjudicated decisions per cycle; below 100 the sample cannot detect a systematic error rate of 2 percent with useful precision.
- Requests with unknown outcomes remain unknown in every report rather than being counted as successes or failures.
- Telemetry carries destination identifiers, version identifiers, reason-code enumerations, and coarse buckets as dimensions, and never raw vectors, raw request text, or full neighbour lists, which are held in an access-controlled store [15][17].

***

#### Step 6.2: Detect the Three Drift Classes and Fire the Refit Trigger

**Required Actions**:

- Monitor and diagnose the 3 drift classes separately, since their remedies differ: data drift changes the incoming language mix, input length, or destination prevalence; concept drift changes what a destination means while its identifier stays constant; representation drift changes the vectors because the encoder, tokenizer, preprocessing, prefix, precision, dimension, normalisation, or provider behaviour changed.
- Track a fixed monitoring panel against an approved reference window: per-destination request volume share, per-destination top-one score distribution, decision margin distribution, neighbour-label entropy, distance to destination centroid, embedding norm distribution, abstention share, escalation share, clarification share, and confusion-pair distribution.
- Fire the threshold refit trigger where any of the following holds over a rolling 14-day window: the false-route rate on adjudicated accepted decisions rises by at least 2 percentage points above the certified figure; the abstention or escalation share rises by at least 25 percent relative to the reference window; any destination's median top-one score falls by at least 0.05 in the metric's own units; or the confusion-pair distribution adds a pair that carried under 1 percent of errors and now carries at least 5 percent.
- Fire the taxonomy review trigger, which is distinct from a refit, where a destination's volume share changes by at least 50 percent relative to the reference window, where a new intent appears in at least 2 percent of adjudicated abstentions, or where annotator agreement on a fresh 200-request sample falls below 85 percent.
- Fire the mandatory full re-embed trigger on any change to the embedding revision, tokenizer, pooling, precision, dimension, normalisation mode, prefix or instruction template, or preprocessing version, treating a provider's silent update as such a change once detected by checksum comparison.
- Treat a geometric shift with no measured quality loss as a warning that raises sampling density rather than as a refit trigger, and treat a stable embedding distribution as no evidence that destination semantics remain correct.

**Required Outputs**:

- A drift monitoring panel with one reference window per signal and a stated comparison method.
- A drift classification record assigning every alarm to data, concept, or representation drift.
- A trigger log recording every fired trigger, its measured value, its threshold, and the action taken.

**Quality Checkpoints**:

- Every alarm is classified into exactly 1 of the 3 drift classes before any remedy is applied, since refitting a threshold cannot repair a concept change and re-embedding cannot repair a taxonomy change.
- A fired refit trigger produces a new calibration artifact within 14 days or an explicit recorded acceptance of the degraded operating point by the policy owner; an unactioned trigger older than 14 days is an operational defect.
- Recalibration reuses the fitting procedure of Step 4.2 in full, including a fresh out-of-scope partition of at least 200 requests, rather than adjusting a floor by inspection.
- No threshold is transferred numerically from one embedding revision to another; a floor is a property of a space and does not survive a change of space.

***

#### Step 6.3: Execute an Encoder Change as a Full Re-Embed and Versioned Cutover

**Required Actions**:

- Re-embed the complete canonical exemplar corpus into a new index generation built beside the existing one, never in place and never partially, since a corpus split across two revisions produces incomparable distances with no error raised at any layer.
- Freeze the outgoing generation at the start of the migration, dual-write or replay every exemplar change that arrives during the build, and re-verify coverage after the replay completes.
- Fit a new calibration artifact on the incoming generation from the labelled partitions rather than translating the outgoing thresholds numerically, and evaluate the incoming generation on routing accuracy per destination, out-of-scope recall and false-accept rate, coverage at the risk target, score and norm distributions, top-one agreement with the outgoing generation, margin shift, latency, and cost.
- Run both generations in parallel on the frozen corpus and on shadow traffic, investigate every top-one disagreement by adjudication rather than assuming the newer generation is correct, and switch the serving alias atomically only after coverage and evaluation gates pass.
- Retain the outgoing generation intact and addressable for rollback for at least 14 days after cutover, and reject any request whose query vector, index generation, calibration artifact, and registry version are not all from one generation.
- Leave canonical exemplar text untouched during a migration, because editing an exemplar to change its vector destroys provenance for a reason unrelated to its content.

**Required Outputs**:

- A migration record naming the outgoing revision, the incoming revision, coverage figures, and the evaluation deltas per destination.
- A new calibration artifact fitted on the incoming generation with its own certification status.
- An atomic alias switch event with its timestamp, the generation it selected, and the retained rollback generation with its expiry date.

**Quality Checkpoints**:

- The incoming generation reaches 100 percent coverage of approved exemplars before the alias switches; a partial cutover is the drift failure this step exists to prevent.
- Routing accuracy on the incoming generation is within 2 percentage points of the outgoing generation or better on every destination; a larger per-destination regression blocks the switch even where the aggregate improves.
- Mixed-generation requests are rejected rather than served; a single served request combining a query vector from one revision with exemplar vectors from another is a correctness incident.
- The rollback generation remains intact for at least 14 days; deleting it earlier removes the only remedy for a regression discovered in production.

***

## III. Implementation Guidance for AI Agents

AI agents operating an embedding router must hold the entire request-time decision in deterministic components and must never treat a similarity value as a permission, a probability, or a substitute for an evaluated gate. The following guidance translates the framework above into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Routing Supervisor Agent**: Owns the routing contract, the taxonomy version, the risk-tier assignment, and release authorisation. Holds the prohibition that no similarity result may widen authority, and enforces it at every phase handoff.
2. **Registry and Exemplar Agent**: Owns Phases 1 and 2. Maintains the destination registry, drafts inclusion and exclusion criteria for human approval, mines hard-negative candidates, runs the cross-assignment check, and quarantines every proposed exemplar until review completes. Never admits an exemplar it drafted without a recorded human reviewer.
3. **Representation Agent**: Owns Phase 3. Benchmarks candidate encoders on the local frozen corpus, pins the revision tuple, builds index generations from canonical snapshots, and validates every approximate configuration against the exact-search oracle. Never compares vectors across two revisions.
4. **Calibration Agent**: Owns Phase 4. Fits per-destination floors, margins, and support minima on the disjoint calibration partition, produces the operating-point sweep with false-route and false-fallback rates reported separately, and issues the calibration artifact with its certification status. Never touches the final holdout during fitting.
5. **Dispatch Agent**: Owns Phase 5. Applies eligibility before ranking, evaluates all three gates, selects the fallback, enforces the visited-destination set and the attempt bound, and re-authorizes at execution time. Never modifies a threshold at request time.
6. **Drift and Migration Agent**: Owns Phase 6. Maintains the monitoring panel, classifies alarms into the three drift classes, fires refit and re-embed triggers, and executes migrations as full re-embeds with dual generations and a retained rollback.

**Workflow Execution Pattern**:

```
STATE: Phase_4_Threshold_Calibration
ACTIONS:
  1. Load the disjoint calibration and development partitions
  2. Compute per-destination score distributions for positives,
     wrong-destination negatives, and out-of-scope requests
  3. Sweep floor and margin jointly across the development partition
  4. Record false_route_rate, false_fallback_rate, coverage per point
  5. Select the operating point meeting the predeclared risk target
  6. Emit the calibration artifact with certification status
VALIDATION:
  - final_holdout_untouched == TRUE
  - calibration_requests_per_destination >= 30 OR global_floor_applied == TRUE
  - out_of_scope_partition_size >= 200
  - false_route_rate AND false_fallback_rate BOTH reported == TRUE
  - coverage_at_risk_target >= 0.50 OR structural_remedy_recorded == TRUE
TRANSITIONS:
  IF all_validations_pass THEN next_state = Phase_5_Gated_Execution
  IF coverage_below_target THEN next_state = Phase_1_Taxonomy_Revision
  ELSE next_state = Phase_4_Error_Handling
```

**Two-Phase Action Pattern**:

1. **Plan**: Emit the destination registry, the exemplar inventory, and the intended index and calibration manifests without building anything.
2. **Validate**: Confirm annotator agreement, exemplar minima, and cross-assignment rates while correction is still cheap.
3. **Execute**: Build the index generation, fit thresholds, and serve traffic only after the validation gates pass.

**Approval Gate**: Human authorisation is required before any of the following, and agents halt rather than proceed: promoting an index generation to the serving alias; admitting an agent-drafted or synthetic exemplar into a serving index; changing any threshold for a destination whose risk class is high or whose side effects are irreversible; provisioning paid vector infrastructure or issuing credentials; changing retention, residency, or export scope for exemplar text or vectors; and deleting a rollback generation before its 14-day expiry. The numeric trigger for mandatory human review of an otherwise automatic release is a projected coverage change of more than 10 percentage points or a projected false-route change of more than 1 percentage point relative to the certified artifact.

**Context Management Requirements**:

- Process exemplar encoding, re-embedding, and evaluation in bounded batches with a recorded resume point, so an interrupted migration resumes rather than restarts.
- Hold only the destination registry and the calibration artifact in working context at request time; the exemplar corpus is addressed through the index rather than loaded.
- Write a handoff record naming the completed phases, the pending phases, and the frozen artifact versions wherever a migration spans more than one working pass.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract and Taxonomy Integrity (After Phase 1)**

- **Automated Check**: Every registry record carries all 14 required fields; aggregate annotator agreement is at least 85 percent with no destination below 70 percent; at least 2 destinations remain after merging; no similarity-only authorisation path exists.
- **Agent Action on Pass**: Proceed to exemplar construction.
- **Agent Action on Failure**: Halt and return the specific defect; a taxonomy defect is never corrected downstream by a threshold.
- **Human Review Trigger**: Any destination below 70 percent agreement, or any identified path by which a similarity result could widen authority.

**Checkpoint 2: Exemplar Set Quality (After Phase 2)**

- **Automated Check**: Every destination holds at least 20 reviewed positives; the largest-to-smallest set ratio is at most 3 to 1 or a remedy is declared; cross-assignment rate is at most 5 percent per destination and at most 10 percent per pair; every confusing-neighbour pair holds at least 10 boundary cases.
- **Agent Action on Pass**: Release the exemplar snapshot to encoding.
- **Agent Action on Failure**: Return the failing destinations and pairs; destinations below 20 exemplars are excluded from automatic acceptance rather than served.
- **Human Review Trigger**: A pair cross-assignment rate above 10 percent, or a hard-negative reclassification rate above 20 percent.

**Checkpoint 3: Representation and Generation Integrity (After Phase 3)**

- **Automated Check**: Recorded revision equals the generation pin for 100 percent of vectors; exemplar coverage is 100 percent or fully documented; approximate top-one agreement with the exact oracle is at least 99 percent and post-gate decision agreement at least 99.5 percent; the alias points to exactly one generation.
- **Agent Action on Pass**: Proceed to calibration.
- **Agent Action on Failure**: Block the generation from serving and rebuild from the canonical snapshot.
- **Human Review Trigger**: Any non-zero cross-revision vector count, or an approximate configuration that cannot reach the agreement thresholds after one retuning pass.

**Checkpoint 4: Calibration Sufficiency (After Phase 4)**

- **Automated Check**: The final holdout is untouched; every individually fitted floor rests on at least 30 labelled requests; the out-of-scope partition holds at least 200 requests; false-route and false-fallback rates are both reported; coverage at the risk target is at least 50 percent or a structural remedy is recorded.
- **Agent Action on Pass**: Certify the calibration artifact and proceed to gated execution.
- **Agent Action on Failure**: Return to exemplar curation or taxonomy revision for the failing destinations only; do not relax the risk target.
- **Human Review Trigger**: Coverage below 50 percent at the risk target, or any destination whose floor rests on fewer than 30 labelled requests being proposed for automatic acceptance.

**Checkpoint 5: Execution Integrity (Continuous During Phase 5)**

- **Automated Check**: All 3 gates evaluated on 100 percent of accepted decisions; eligibility applied before ranking on 100 percent of requests; no fallback widens scope; no request exceeds 3 dispatch attempts; every request carries exactly 1 terminal decision type.
- **Agent Action on Pass**: Continue serving and emit the routing span.
- **Agent Action on Failure**: Fail the individual request to the declared fallback, and disable automatic acceptance where the failure is systemic rather than per-request.
- **Human Review Trigger**: Any accepted decision with an unevaluated gate, any ineligible identifier surviving into a candidate set, or an unterminated request.

**Checkpoint 6: Drift and Migration Control (Each Monitoring Cycle and Before Each Cutover)**

- **Automated Check**: Every alarm is classified into one of the 3 drift classes; every fired refit trigger has an action or a recorded acceptance within 14 days; the incoming generation reaches 100 percent coverage and per-destination accuracy within 2 percentage points before cutover; the rollback generation is intact.
- **Agent Action on Pass**: Switch the alias atomically and begin the canary window.
- **Agent Action on Failure**: Block the cutover and retain the outgoing generation as the serving alias.
- **Human Review Trigger**: A per-destination accuracy regression above 2 percentage points, an unactioned refit trigger older than 14 days, or a taxonomy review trigger firing on any destination.

**Checkpoint Documentation Template**:

```
CHECKPOINT_ID:
CHECKPOINT_NAME:
PHASE_BOUNDARY:
TRIGGER:
VALIDATION_CRITERIA:
MEASURED_VALUE:
PASS_CONDITION:
FAIL_ACTION:
HUMAN_REVIEW_TRIGGER:
RESPONSIBLE_AGENT:
ARTIFACT_VERSIONS:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Confident Misroute of Unsupported Traffic**

- **Symptoms**: Out-of-scope false-accept rate above the certified figure; adjudicated errors concentrated in requests whose content matches no destination's criteria; user corrections and handler rejections rising while top-one scores remain in the normal range.
- **Diagnostic Steps**: Confirm the floor gate was evaluated on the affected decisions rather than assumed; compare the affected requests' scores against the out-of-scope distribution recorded at calibration; check whether the out-of-scope calibration partition contained adjacent-domain traffic or only trivially distant unknowns.
- **Resolution Protocol**: Option A, raise the affected destinations' floors to the level the recorded out-of-scope distribution supports and accept the coverage loss. Option B, rebuild the out-of-scope calibration partition from real adjacent-domain traffic and refit, where the original partition was unrepresentative. Option C, add an explicit out-of-scope destination with its own exemplar set so the unsupported region is represented positively rather than only by rejection.
- **Escalation Trigger**: Out-of-scope false-accept rate above the certified figure by more than 5 percentage points, or any accepted decision found with an unevaluated floor gate, halts automatic acceptance immediately.

**Error Type 2: Embedding Version Drift Across the Exemplar Corpus**

- **Symptoms**: Routing accuracy degrades with no configuration change recorded; score distributions shift for a subset of destinations only; no error appears in any log because the comparison remains arithmetically valid.
- **Diagnostic Steps**: Compare every vector's recorded revision against the serving generation's pin and count mismatches; determine whether the mismatch originates in a partial re-embedding run, a provider updating a model behind a stable alias, or a write that reached one generation only.
- **Resolution Protocol**: Option A, block the mixed generation from serving, complete a full re-embed into a separate generation from the canonical snapshot, refit calibration, and switch the alias atomically. Option B, where a provider alias changed silently, pin to an immutable revision or checksum and treat the change as a mandatory migration. Option C, roll back the alias to the retained generation while the migration is rebuilt.
- **Escalation Trigger**: Any non-zero cross-revision vector count in a serving generation halts serving on that generation; this error is never resolved by retry.

**Error Type 3: Exemplar Imbalance or Cross-Assignment Distorting Selection**

- **Symptoms**: Confusion pairs concentrated on one direction between two destinations; the destination with the largest exemplar set wins disproportionately on boundary cases; imbalance-slice accuracy diverges from aggregate accuracy by more than 5 percentage points.
- **Diagnostic Steps**: Recompute cross-assignment rates per destination and per pair; compare the winning destination's exemplar count against the losing destination's on the affected requests; inspect the winning exemplar on a sample of at least 30 affected decisions.
- **Resolution Protocol**: Option A, switch to class-balanced nearest-neighbour voting or centroid aggregation, which are insensitive to set size by construction. Option B, cap and stratify the oversized sets to the declared ratio and rebuild the generation. Option C, where cross-assignment is bidirectional above 10 percent, merge the destination pair or re-split it on a different axis, since no aggregation rule or threshold separates genuinely overlapping destinations.
- **Escalation Trigger**: A bidirectional pair cross-assignment rate above 10 percent after one remediation pass escalates to a taxonomy review rather than a further tuning pass.

**Error Type 4: Threshold Decay Under Distribution Shift**

- **Symptoms**: Abstention or escalation share rising while adjudicated accuracy on accepted decisions holds; a destination's median top-one score falling steadily; a new confusion pair appearing and growing.
- **Diagnostic Steps**: Classify the alarm into data, concept, or representation drift before acting; compare the current input length, language mix, and destination prevalence against the reference window; check whether any destination's inclusion criteria changed in practice without a taxonomy version increment.
- **Resolution Protocol**: Option A, for data drift, refit floors and margins on a calibration partition drawn from the current window using the full Step 4.2 procedure. Option B, for concept drift, revise the registry criteria, re-adjudicate the affected exemplars, increment the taxonomy version, and refit. Option C, for representation drift, treat the change as a mandatory full re-embed under Step 6.3.
- **Escalation Trigger**: An unactioned refit trigger older than 14 days, or a second refit fired within 30 days of the previous one, escalates to a taxonomy review because repeated refits indicate the destination set rather than the thresholds is unstable.

**Error Type 5: Approximation or Filter Defect Changing Decisions Near a Floor**

- **Symptoms**: Decision disagreement with the exact-search oracle concentrated just above and just below the floor; recall figures acceptable while accepted-case error rises; selective filters returning fewer candidates than the eligible set contains.
- **Diagnostic Steps**: Re-run the affected requests against the exact oracle and compare gate outcomes rather than neighbour lists; determine whether the engine applies metadata filters before or after traversal; measure candidate counts returned under the most selective production filters.
- **Resolution Protocol**: Option A, increase the search-effort parameter until post-gate decision agreement reaches 99.5 percent, accepting the latency cost. Option B, use an exact path for filtered queries where post-filtering is the cause, retaining approximation only for unfiltered traffic. Option C, revert to exact search entirely where the catalogue size permits, since approximation is optional and correctness is not.
- **Escalation Trigger**: Post-gate decision agreement below 99.5 percent after one retuning pass reverts the deployment to exact search rather than accepting a second tuning attempt.

**Error Type 6: Exemplar Store Compromise or Semantic Collision**

- **Symptoms**: A sudden exemplar addition, label change, or centroid movement outside the approval workflow; one exemplar winning an unusual share of traffic; repeated near-boundary probing from one principal; requests containing zero-width characters, Unicode confusables, transliteration, or duplicated trigger phrases aimed at a privileged destination [16].
- **Diagnostic Steps**: Compare the exemplar snapshot checksum against the approved manifest; identify the writer and approval record for every exemplar added since the last verified snapshot; inspect the winning exemplar and its nearest neighbours for the affected requests.
- **Resolution Protocol**: Option A, roll the alias back to the last checksum-verified generation and quarantine every unapproved exemplar. Option B, tighten the versioned preprocessor to normalise Unicode and strip disallowed control characters while retaining the original text for forensic review, then re-encode and re-evaluate. Option C, activate the independent kill switch and route all traffic to the deterministic baseline while the store is rebuilt from approved records.
- **Escalation Trigger**: Any exemplar present in a serving generation without a recorded approval halts serving and triggers an incident; the exemplar store is a control-plane asset and a compromise of it is a compromise of routing authority.

**Troubleshooting Decision Tree**:

```
ROUTING QUALITY DEGRADED
├─ ACCEPTED-CASE ERROR ROSE
│   ├─ Errors are out-of-scope requests → Raise floor / rebuild unknown partition (Error 1)
│   ├─ Errors concentrate on one destination pair → Cross-assignment check (Error 3)
│   │   ├─ Pair rate <= 10% → Rebalance sets or switch aggregation rule
│   │   └─ Pair rate > 10% → ESCALATE to taxonomy review; merge or re-split
│   └─ Errors sit near the floor only → Compare against exact oracle (Error 5)
│       ├─ Disagreement > 0.5% → Retune once, then revert to exact search
│       └─ Disagreement <= 0.5% → Refit thresholds (Error 4)
├─ NO CONFIGURATION CHANGE RECORDED
│   ├─ Revision mismatch count > 0 → HALT generation; full re-embed (Error 2)
│   ├─ Exemplar checksum mismatch → HALT; roll back alias; incident (Error 6)
│   └─ All versions consistent → Classify drift class, then refit (Error 4)
├─ ABSTENTION OR ESCALATION SHARE ROSE
│   ├─ Adjudicated accuracy holds → Refit floors on current window (Error 4)
│   ├─ New intent in >= 2% of abstentions → ESCALATE to taxonomy review
│   └─ Language-specific → Route that language to its own path or human review
└─ GATE OR AUTHORIZATION ANOMALY
    ├─ Accepted decision with unevaluated gate → HALT automatic acceptance
    ├─ Ineligible identifier in candidate set → HALT; repair eligibility filter
    └─ Fallback widened scope → HALT; revert fallback declaration
```

### D. Performance Metrics and Continuous Learning

**Decision Quality Metrics**:

- **Routing accuracy per destination**: Correct top-one decisions over labelled single-destination requests, reported macro and traffic-weighted (target: at least 5 percentage points above the deterministic baseline on every destination).
- **False-route rate on accepted decisions**: Incorrect dispatches over labelled accepted requests (target: at or below the predeclared risk target, reported with its coverage).
- **False-fallback rate**: In-scope requests declined despite an identifiable correct destination, over labelled in-scope requests (target: at most 15 percent, since a router that declines a sixth of serviceable traffic is not repaying its cost).
- **Out-of-scope false-accept rate**: Out-of-scope requests accepted into a known destination over labelled out-of-scope requests (target: at most 5 percent; this is the metric that detects the method's characteristic failure).
- **Coverage**: Accepted requests over eligible requests (target: at least 50 percent at the certified risk target).

**Integrity Metrics**:

- **Revision consistency**: Vectors whose recorded revision equals the serving generation's pin, over all serving vectors (target: 100 percent; any shortfall halts the generation).
- **Gate completeness**: Accepted decisions with all 3 gates evaluated and recorded, over all accepted decisions (target: 100 percent).
- **Exact-oracle decision agreement**: Post-gate decisions matching exact search, over sampled decisions (target: at least 99.5 percent).
- **Cross-assignment rate**: Exemplars closer to another destination's representation than their own, per destination (target: at most 5 percent).

**Efficiency Metrics**:

- **Router overhead share**: Added routing latency and cost as a share of median end-to-end destination cost, including retries, reranking, escalation, and failed attempts (target: at most 10 percent; above 25 percent the router is replaced by the deterministic baseline).
- **Cost per correctly routed request**: Total encoding, retrieval, reranking, escalation, and human-review cost over correctly accepted decisions (target: below the deterministic baseline's cost per correctly routed request).
- **Refit interval**: Days between fired refit triggers (target: at least 90; below 30 indicates taxonomy instability rather than threshold decay).

**Learning and Adaptation Mechanisms**:

- **Adjudicated error intake**: Route every adjudicated misroute, user correction, and handler rejection into the exemplar corpus as a candidate, since production errors carry more information per item than any generated variant.
- **Confusion-pair curation**: Where a confusion pair persists across 2 consecutive cycles, add reviewed boundary cases specifically to that pair rather than adding exemplars uniformly.
- **Stratified sampling maintenance**: Recompute the 6 sampling strata each cycle so that the random high-confidence stratum remains at least 100 decisions as traffic grows, since that stratum alone detects confident systematic error.
- **Simplification review**: Re-run the method selection gate every 180 days, and remove the embedding router where the deterministic baseline, a lexical index, or a supervised classifier now matches its accuracy at lower complexity.

***

## IV. Domain-Agnostic Application Guidance

The framework holds wherever a bounded set of destinations can be described by labelled example requests and a wrong destination is detectable. The destination set, the exemplar sources, and the fallback path change by sector; the gate structure and the calibration procedure do not.

### 4.1 Cross-Domain Application Patterns

**Contact-centre and service-desk operations**: Destinations are queues, workflows, and self-service paths; exemplars are historical contacts already labelled by the queue that resolved them, which makes the labelled corpus a by-product of operations rather than a project. The characteristic risk is that queue labels record where a contact went rather than where it belonged, so adjudication must re-label a sample rather than trusting the operational label, and transferred contacts are treated as misroutes rather than as successes.

**Clinical and healthcare intake**: Destinations are care pathways, specialties, and urgency tiers; exemplars are de-identified intake descriptions. Floors are set higher and margins wider than in any commercial deployment because a misroute has clinical consequence, and every high-urgency destination requires neighbour support of at least 2 plus clinician confirmation before dispatch. The exemplar corpus falls under health-data governance, so canonical text retention, tenant scoping, and deletion propagation are compliance obligations rather than engineering preferences.

**Industrial field service and maintenance**: Destinations are technician skill groups, parts workflows, and safety escalations; exemplars are work-order descriptions carrying heavy jargon, equipment codes, and abbreviations. Exact identifiers and equipment codes are extracted to the lexical path before encoding, because a model number is an exact token that similarity blurs, and the dense path decides only the residual semantic question of which fault class the description describes.

**Financial services and regulated intake**: Destinations are product teams, dispute workflows, and compliance queues. Eligibility, entitlement, residency, and payment-state determinations bind deterministically before ranking, and no similarity value participates in them. Requests naming amounts, account states, or regulatory triggers are routed by rule; the vector router decides only among destinations the policy plane has already declared eligible.

**Public-sector benefits and citizen services**: Destinations are programme intake paths and eligibility assessment queues; traffic is multilingual and includes many short, underspecified requests. The short-input minimum and the language-specific accuracy floor matter more here than anywhere else, and a language falling below 80 percent of the best-performing language's accuracy is routed to a language-specific path or to human review rather than served silently.

**Software incident and change triage**: Destinations are owning teams and runbooks; exemplars are historical incident summaries. Taxonomy churn is high because teams and services reorganise, so the taxonomy review trigger fires more often than the refit trigger, and the registry's identifier-reuse prohibition is load-bearing: a team identifier reassigned to a different service silently invalidates every historical decision recorded under it.

### 4.2 Scale, Risk, and Latency Adaptation

**Small catalogues under 500 exemplars**: Deploy exact search alone and retain it permanently. Approximation adds a failure mode, an index build, and a tuning burden without adding accuracy at this size. One centroid per destination and a single global floor are acceptable where per-destination calibration data is unavailable, provided the global floor is set conservatively and the per-destination shortfall is named in the calibration artifact.

**Large catalogues above 50,000 exemplars or high concurrency**: Approximate indexing becomes justified, and its validation burden rises with it: post-gate decision agreement against the exact oracle must be measured under production-like filters, concurrency, update rates, and tenant partitioning rather than on single-query benchmarks. Metadata filter ordering must be verified explicitly, since post-filtering degrades precisely on the selective queries that eligibility filtering produces.

**High-risk and irreversible destinations**: Raise the floor, widen the margin, require neighbour support of at least 2, require an independent execution-time confirmation, and never permit a fallback path into such a destination. Where a destination's side effects cannot be reversed and no independent guard exists, keep the decision human regardless of measured accuracy.

**Tight latency budgets under 50 milliseconds**: A remote encoder call rarely fits. Adopt a local encoder runtime with a warmed cache of exemplar vectors, or suppress the vector router in favour of a supervised classifier or a rule set. Where the budget is tighter than one encode plus one lookup, the method selection gate returns suppress rather than a tuned configuration.

**Multi-tenant deployments**: Partition exemplars by tenant scope in the index and enforce the partition in the eligibility filter rather than relying on the store's isolation features alone, since database tenancy features are a performance and organisation mechanism and not an authorization test. Never share a decision cache, a query-embedding cache, or a calibration artifact across tenants or authorization scopes.

***

## V. Limitations and Considerations

**A closed-set method cannot reason about a novel request**: The router's entire semantic knowledge is the exemplar corpus, so a genuinely new request type is represented only by its distance from existing exemplars. The consequence is that the method's ceiling is the corpus's coverage, and no threshold setting converts absence of evidence into correct handling. The mitigation is the floor gate, which converts an unrepresented request into a declared rejection rather than a confident misroute, together with escalation to a model-based router for the uncertain band and continuous intake of adjudicated production errors into the corpus.

**Every numeric threshold in this guide is a deployment default, not a measured finding**: The floor and margin values are not stated numerically here precisely because they are properties of a specific embedding space and destination set; but the surrounding defaults are stated as operable starting points rather than as evidence. The 20-exemplar minimum, the 3-to-1 imbalance ratio, the 5 percent and 10 percent cross-assignment ceilings, the 30-request per-destination calibration minimum, the 300-request and 200-request partition sizes, the 85 percent annotator agreement bar, the 99 percent and 99.5 percent oracle agreement figures, the 50 percent coverage floor, the 2-percentage-point regression gate, the 14-day rollback window, and the 90-day and 180-day review intervals are defaults chosen to be operable on first deployment. The consequence of treating them as findings is a false sense of empirical grounding. The mitigation is to record each as a local configuration value, measure the outcome it produces, and revise it from local evidence at the first refit.

**Threshold calibration consumes labelled data that many deployments do not have**: Fitting per-destination floors with separately measured false-route and false-fallback rates requires a labelled corpus with realistic out-of-scope traffic, which is expensive and is the most common reason a deployment ships with an uncalibrated global cutoff. The consequence is a router whose operating point is unknown and whose failure mode is invisible. The mitigation is the staged path in Section 1.4: below 1,000 labelled requests the router runs in shadow mode and accepts nothing, and destinations below 30 calibration requests carry the conservative global floor and are named rather than silently individually fitted.

**Annotator agreement bounds achievable accuracy**: Where qualified reviewers agree on only 85 percent of labels, no router can exceed roughly that figure on the same taxonomy, and measured accuracy above the agreement ceiling indicates the evaluation is scoring against one annotator's convention rather than against truth. The consequence is over-confident release decisions. The mitigation is the Phase 1 agreement gate, adjudication of every disagreement, and treating persistent disagreement as evidence of a defective taxonomy to be merged or re-split rather than as annotator noise.

**Vectors are sensitive derived data rather than anonymised text**: Published work reports a generative inversion attack that reconstructs input sequences from sentence embeddings and produces sentences coherent and contextually similar to the originals [15]. The consequence is that treating a vector store as a lower-sensitivity tier than the source text understates exposure. The mitigation is to apply to vectors the same minimisation, encryption, tenant scoping, retention limit, deletion propagation, export restriction, and regional control applied to the source text, and to keep raw vectors and full neighbour lists out of general telemetry.

**The exemplar store is a control-plane asset**: An unreviewed exemplar admitted to a serving index changes routing behaviour with the same authority as a configuration change, and under maximum-similarity aggregation a single exemplar can decide a destination. The consequence of a compromise is a routing-authority compromise rather than a data-quality problem. The mitigation is authenticated writers, mandatory review, quarantine before activation, checksum-verified snapshots, immutable audit history, neighbour inspection of every proposed exemplar before admission, and alerting on centroid movement and on any exemplar winning an unusual traffic share.

**Approximation and quantization change decisions without changing recall figures**: A configuration can preserve neighbour recall while shifting a score across a floor, and recall-based approval therefore passes configurations that alter acceptance. The consequence is a quality regression invisible to the metric used to approve the change. The mitigation is the exact-search oracle retained permanently, post-gate decision agreement measured rather than neighbour recall alone, and reversion to exact search after one failed retuning pass rather than a second attempt.

**External claims are carried as the originating prose source stated them**: This guide is an operational restructuring of a prose source, and most of its external citations were transcribed rather than re-retrieved. Three entries were fetched and confirmed during conversion and are marked as such in Section VII. The consequence is that a transcribed figure could be stale or mis-stated at the source. The mitigation is that no transcribed claim carries a threshold used in this guide's procedure: every operational number here is either a stated default or a locally measured value, and the citations support framing rather than acceptance criteria.

***

## VI. Conclusion and Summary

Embedding-based routing is the cheapest and most reproducible of the routing families, and its cost is that it cannot decline on its own. A nearest-neighbour lookup returns a nearest destination for every request that reaches it, and the returned similarity value looks the same whether the request belongs to the destination set or not. Everything in this guide follows from that single property: the absolute floor exists to supply the answer the ranking cannot give, the margin exists because a high score with two close candidates is ambiguity rather than confidence, and neighbour support exists because a single exemplar is a point rather than a region.

The method's second silent failure is version drift. Re-encoding part of a corpus under a different revision, or a provider updating a model behind a stable alias, makes new query vectors incomparable to stored exemplars while every layer continues to compute valid arithmetic and raise no error. Pinning the complete revision identity on every vector, refusing every cross-revision comparison, and treating any encoder change as a full re-embed into a fresh generation are the only defences, and none of them is optional.

Both failures are properties of the mechanism rather than of any particular deployment, and both are detectable only by measurement that a working system does not produce on its own. The tier partition is what makes that measurement possible: because the model tier holds no request-time authority, every decision is reproducible from its recorded generation identifiers, and two evaluations of the same frozen set return the same figures.

**Key Success Factors**:

- **A calibrated absolute floor, not only a ranking**: Similarity is not eligibility, and a router without a fitted floor has no mechanism to say none of these.
- **Both error rates measured separately**: A floor fitted on false-route rate alone produces a router that declines almost everything; a floor fitted on coverage alone produces confident misroutes.
- **A pinned embedding revision on every stored vector**: A partial re-embed and a silent provider update are the same failure, and neither raises an error.
- **Exemplar sets that are balanced, bounded, and checked for cross-assignment**: The exemplar corpus is the destination taxonomy, and a labelling error in it is a routing defect no threshold can repair.
- **A declared fallback that never widens authority**: Every non-accepting outcome is a destination with an owner and a service objective, not an error state.
- **A refit trigger fired by measurement rather than by schedule**: A threshold fitted once decays as traffic moves, and the decay is visible in the monitoring panel before it is visible in outcomes.

Applied consistently, this framework yields a routing layer whose decisions are cheap, reproducible, and auditable, whose refusals are as trustworthy as its acceptances, and whose degradation is detected by a named trigger rather than discovered in an incident.

***

## VII. References and Further Reading

This guide is an operational restructuring of a prose production guide on embedding-based routing. Its external references are transcribed from that originating prose guide as it cited them, and, except where an entry is marked verified during conversion, they were not independently re-verified. Three entries were retrieved during conversion and their titles, authors, and headline claims confirmed; those entries are marked. Where the originating guide cited a work by a short label only, that label is reproduced rather than expanded. No entry was added to raise citation density, and no reference supplies a numeric acceptance criterion used in this guide's procedure.

**Corpus pointers**:

- Robust Embedding-Based Routing: A Production Guide for Humans and AI Agents — the originating prose guide from which this operational guide was restructured.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification governing this guide's structure, register, conformance envelope, and prohibition list.
- `advanced_task_guides/routing/guide_LLMBasedRouting.md` — the sibling guide covering constrained model routing under a versioned destination registry; source of the destination, destination registry, closed destination vocabulary, dispatcher, misroute, handler rejection, taxonomy version, and deterministic baseline terminology adopted here, and the destination of the escalation path this guide's uncertain band feeds.
- `advanced_task_guides/routing/guide_RuleBasedRouting.md` — the sibling guide covering verified routing tables with total coverage and a reversible change path; the owner of every destination derivable from trusted structured data, which this guide's method selection gate suppresses in favour of.
- `advanced_task_guides/routing/guide_CapabilityRouting.md` — the sibling guide covering requirement-matched handler selection with explicit non-selection; the adjacent mechanism where destination choice turns on declared handler capabilities and constraints rather than on semantic similarity to exemplars.
- `advanced_task_guides/routing/guide_ContentBasedRouting.md` — the sibling guide covering bounded payload inspection; it is a consumer of this method, invoking it as the fourth tier of its detection cascade on normalised extracted text rather than raw bytes.
- `advanced_task_guides/memory-management/guide_UnstructuredMemory.md` — the corpus specification for embedding version pinning, index generations, alias switching, and versioned re-embedding cutovers; this guide adopts its embedding revision, index generation, and embedding version drift terminology rather than re-deriving it.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — the corpus treatment of calibration gap computation and signal certification, referenced where a normalised similarity is proposed as a gating confidence value.

**External references**:

1. MTEB repository — https://github.com/embeddings-benchmark/mteb/
2. *MMTEB: Massive Multilingual Text Embedding Benchmark* — https://arxiv.org/html/2502.13595v3 (verified during conversion: the benchmark covers more than 500 quality-controlled evaluation tasks across over 250 languages, and reports English-only models ranking last on the multilingual task set).
3. Guo, Pleiss, Sun, and Weinberger, *On Calibration of Modern Neural Networks* — https://arxiv.org/abs/1706.04599 (verified during conversion: ICML 2017; reports that modern neural networks are poorly calibrated and that temperature scaling, a single-parameter variant of Platt scaling, is effective at calibrating predictions).
4. Sentence Transformers, *Semantic Textual Similarity* — https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html
5. Sentence Transformers, *Matryoshka Embeddings* — https://sbert.net/examples/sentence_transformer/training/matryoshka/README.html
6. Sentence Transformers, *Retrieve and Re-Rank* — https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
7. Sentence Transformers, hard-negative mining documentation — https://www.sbert.net/docs/package_reference/util/hard_negatives.html
8. OpenSearch, *Asymmetric model support: optimizing semantic search for queries and documents* — https://opensearch.org/blog/asymmetric-model-support-optimizing-semantic-search-for-queries-and-documents/
9. Cormack, Clarke, and Büttcher — https://research.google/pubs/reciprocal-rank-fusion-outperforms-condorcet-and-individual-rank-learning-methods/
10. Elasticsearch, *Reciprocal rank fusion* — https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
11. pgvector documentation — https://github.com/pgvector/pgvector
12. Qdrant, *Multitenancy* — https://qdrant.tech/documentation/manage-data/multitenancy/
13. Milvus, *Multi-tenancy* — https://milvus.io/docs/multi_tenancy.md
14. *Deep Open Classification* — https://www.cs.uic.edu/~liub/publications/emnlp17-camera-ready.pdf
15. Li, Xu, and Song, *Sentence Embedding Leaks More Information than You Expect: Generative Embedding Inversion Attack to Recover the Whole Sentence* — https://arxiv.org/abs/2305.03010 (verified during conversion: 2023; proposes a generative inversion attack reconstructing input sequences from sentence embeddings alone).
16. *Bad Characters* — https://www.computer.org/csdl/proceedings-article/sp/2022/131600a773/1FlQDZp8Ec8
17. OpenTelemetry, GenAI attribute registry — https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/
18. Semantic Router — https://github.com/aurelio-labs/semantic-router
