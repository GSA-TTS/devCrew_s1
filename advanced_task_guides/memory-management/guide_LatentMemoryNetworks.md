# Latent Memory Networks

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Latent memory networks constitute the task family of storing and addressing agent experience through learned continuous representations rather than through canonical text or typed records. This guide provides AI agents with a structured protocol for operating the agent-layer subset of that family: retrieval embeddings that index evidence which still survives, and bounded latent compression that replaces evidence only under measured loss. It re-scopes the wider subject deliberately, because learned memory modules, recurrent memory architectures, and soft prompts require weight training or hidden-state access that no agent reaches at runtime; those categories enter here only through an admissibility gate that declares them out of execution scope. It specifies a representation fingerprint that makes mixed-revision contamination detectable, an exact-search reference against which every approximation is measured, filtered-recall testing inside eligible subsets, dual-index migration with atomic alias swap and a declared rollback window, erasure verification spanning generations and restored backups, and an execution tier partition assigning every phase to deterministic software, to model inference, or to a hybrid in which software holds authority. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that vector memory remains auditable rather than merely fast.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Latent memory**: Experience stored or addressed through learned continuous representations rather than through readable text or typed fields. The class includes retrieval embeddings, compressed hidden states, soft tokens, memory slots, and recurrent states.

**Explicit memory**: Canonical text, media, records, and typed claims that remain readable, citeable, correctable, and deletable in their original form. Explicit memory is the evidence base that latent memory addresses.

**Parametric memory**: Knowledge absorbed into base-model weights. It is excluded from this guide because no agent-layer operation reads, writes, or erases it.

**Retrieval embedding**: A learned vector used to locate an explicit source that still survives [1][2]. The vector is an index key and never the authoritative content. This is the default production category.

**Compressed latent**: A condensed representation, such as a gist token set or a learned summary vector, that replaces longer input rather than pointing at it [3][4]. It is admissible only where the canonical source is retained and measured loss stays inside declared bounds.

**Learned memory module**: A trainable read, write, erase, or update mechanism coupled to a controller or attention stack [5][6][7][8][9][10][11][12][13]. It is architectural memory and sits below the agent layer.

**Soft prompt**: A learned set of continuous input embeddings or layer prefixes trained against a frozen base model [14][15]. It conditions behaviour and is not an evidence store.

**Canonical record**: The immutable, versioned explicit artifact from which a representation was derived, addressed by a source identifier, a version identifier, and a content hash.

**Representation fingerprint**: A hash over encoder model identifier, model revision, tokenizer, input role, preprocessing version, dimension, post-hoc transform, normalization, numeric type, and distance metric. Two vectors may share an index only where their fingerprints are byte-identical.

**Index generation**: An immutable, separately named population of vectors sharing one fingerprint, one source snapshot, and one build configuration. Generations are never edited in place.

**Routing alias**: The single indirection through which queries reach exactly one serving generation. Promotion is an alias change, never a partial repopulation.

**Exact search**: Brute-force nearest-neighbor computation over the full vector set. It is the reference oracle against which every approximation is measured, not a production serving path.

**Approximate nearest-neighbor search**: Graph, partitioned, or quantized search that trades recall for latency, throughput, and memory [22][23][24][25].

**ANN gap**: The difference between exact top-k neighbors and the neighbors an approximate index returns for the same query, reported separately from embedding-model error.

**Filtered recall**: Recall measured inside the exact set of records a metadata, tenant, date, or authorization filter leaves eligible [26][27]. It collapses independently of unfiltered recall.

**Hubness**: The high-dimensional pathology in which a small set of vectors appears among the nearest neighbors of disproportionately many queries, allowing generic or frequent content to dominate results.

**Tombstone**: A serving-level deletion marker recorded before physical removal completes, making a record ineligible while cleanup proceeds.

**Re-embedding migration**: The construction of a new generation from a canonical snapshot, with post-snapshot writes, corrections, and tombstones replayed, evaluated in shadow before promotion.

**Deletion graph**: The recorded dependency set naming every artifact derived from a subject's canonical records, spanning chunks, vectors, latents, quantizer training samples, caches, replicas, snapshots, evaluation fixtures, and retired generations.

**Answer preservation**: The proportion of adjudicated questions a compressed latent still answers correctly relative to the canonical source. It is the gate on category-two adoption, and a compression ratio is never a substitute for it.

**Citation support**: The verified existence of the cited span in the canonical record at the recorded version and offsets. A latent cannot itself supply this.

**Evidence contract**: The declared statement of supported tasks, consequence class, required authority, citation obligation, languages, modalities, tenant boundaries, deletion objective, latency objective, and cost ceiling, fixed before any representation is selected.

### 1.2 The Four Representation Categories and the Agent-Layer Boundary

The subject divides into four categories with materially different storage, training, and assurance properties. Collapsing them into a single notion of a vector database is the primary source of production error, because each category carries a different erasure path, a different portability claim, and a different verification burden.

**Category one, retrieval embeddings over retained content**: A vector locates explicit evidence that still exists. Governance is ordinary, because the returned artifact remains inspectable and deletable. This category is executable entirely at the agent layer through an encoder endpoint, an external index, and a canonical store.

**Category two, compressed latents that replace content**: A condensed representation stands in for longer input, saving tokens and repeated compute at the cost of exact wording, qualifiers, minority facts, and citations. It is executable at the agent layer where the compressor is reachable through an inference call and the consumer model accepts the resulting tokens, and only where the canonical source is retained.

**Category three, learned memory modules and recurrent states**: Differentiable read, write, erase, and update mechanisms, retrieval over stored hidden representations, bounded compressive memory updated across segments, and test-time learned long-term memory. These require a modified architecture, gradient training, or access to hidden states.

**Category four, soft prompts and prefixes**: Continuous input embeddings or layer prefixes trained against a frozen base model. These require a training pipeline, an immutable base checkpoint, and a serving stack that loads the artifact.

**Representation category properties**:

| Category | Evidence survives | Agent-layer executable | Erasure path | Primary verification |
| :-- | :-- | :-- | :-- | :-- |
| One: retrieval embeddings | Yes, canonical record retained | Yes, through encoder API and external index | Delete and rebuild the vector | Labeled recall, ANN gap, filtered recall |
| Two: compressed latents | Only where a canonical copy is deliberately kept | Yes, where compressor and consumer are reachable by inference call | Delete only where the dependency set is recorded | Answer preservation, citation recovery, rare-fact retention |
| Three: learned memory modules | No, state is the artifact | No, requires training or architecture change | Isolated adapter deletion, certified unlearning, or retraining | Long-horizon retention, reset replay, poisoning recovery |
| Four: soft prompts and prefixes | No, conditioning is not evidence | No, requires a training pipeline and a controlled serving stack | Artifact retirement and retraining | Task confusion, injection resistance, scope containment |

**The re-scoping this guide applies**: Categories three and four are not operable through prompting, tool calls, HTTP APIs, command-line invocation, file operations, sub-agent orchestration, external data stores, or any inference parameter a model API exposes. Their mechanisms are differentiable memory access, gradient updates to memory slots, and continuous vectors injected at layer boundaries. Instructing an agent to build one would be instructing it to do something it cannot do. This guide therefore treats them as gated selections rather than as executable procedures: Section 1.4 states the conditions under which either may be chosen, Step 1.3 records the choice and its justification, and a selection of category three or four terminates this framework and hands the work to a model-engineering process the guide does not carry.

**Why the embedding-space surrogate is the executable form**: The property a practitioner wants from latent memory is associative recall over accumulated experience without the cost of re-reading everything. Category one supplies that property using only components an agent can invoke: an encoder call converts a record or a query into a vector, an external index answers a similarity query, and the returned identifier resolves to a canonical record the agent can read, cite, correct, or delete. The recall is approximate rather than differentiable, the memory is external rather than architectural, and the addressing is learned while the content is not. That combination is weaker than a trained memory module in adaptation and stronger in every assurance property this guide measures: the evidence remains readable, erasure is a delete rather than a retraining, and the representation is rebuildable from inputs the deployment already retains.

**Scope exclusions**: This guide begins at the vector derived from an explicit record and ends at the identifier returned to the caller. Chunking policy, canonical text and media storage, read and write admission policy, compaction and summarisation of explicit records, symbolic claim modelling and entity identity, retention scheduling, serving-state and key-value cache mechanics, and cross-node sharding are all owned by companion guides in this category and are not restated here. An embedding neighbourhood is a candidate relation and never a symbolic fact.

### 1.3 Execution Tier Partition and Authority Boundaries

Every unit of work in this framework belongs to exactly one execution tier. The partition is load-bearing rather than descriptive, because the recurring production failure in latent memory is a model-tier judgement accepted where a deterministic verdict was required.

**Deterministic tier**: Work that must be performed by software, queries, schema validators, or APIs because it requires exactness, reproducibility, auditability, or a scale that model inference cannot supply. This tier owns fingerprint computation and enforcement, exact nearest-neighbor reference search, recall and gap arithmetic, filter evaluation and access prefilters, index build and generation naming, routing alias state, tombstone accounting, deletion propagation and residual-match queries, checksum and idempotency handling, cost and latency measurement, and the pass or fail verdict on every declared gate.

**Model tier**: Work that must be performed by an inference call because it requires open-vocabulary judgement, natural-language understanding, synthesis, or generation that no deterministic rule covers. This tier owns embedding production for records and queries, latent compression encoding, candidate reranking, proposal of graded relevance labels, generation of adversarial and post-freeze question sets, triage narratives for drift and anomaly alerts, and answer synthesis over retrieved evidence.

**Hybrid tier**: Work in which the model tier proposes and the deterministic tier verifies, or the deterministic tier retrieves and the model tier adjudicates. In every hybrid step in this guide the deterministic component holds authority when the two disagree. A model-proposed relevance label is superseded by the adjudicated label; a reranker may reorder only within the eligible set the filter produced and may never promote an item the filter rejected; a model assertion of citation support is overridden by a span-existence check against the canonical record; a model recommendation to adopt compression is overridden by the answer-preservation gate.

**What the deterministic tier rejects outright**: A write or query whose representation fingerprint differs from the target generation's fingerprint; a vector published before its canonical record commits; a result whose source identifier does not resolve to an authorized canonical record at the recorded version; a promotion whose shadow evaluation is incomplete; an erasure claim with a residual match count above zero; a compressed latent whose canonical copy is absent where the evidence contract requires citation; a batch write carrying a silent truncation flag.

**What the model tier is never permitted to decide alone**: That a retrieved result is relevant enough to authorize a consequential action; that erasure is complete; that an approximate index configuration passes its recall gate; that a latent may become the only surviving artifact for a record; that vectors from different fingerprints may share an index; that a citation is supported; that a drift alert may be closed without a measurement.

**Tier assignment by phase**:

| Phase | Owning tier | Model-tier contribution | Deterministic authority |
| :-- | :-- | :-- | :-- |
| 1: Contract and category admissibility | Hybrid | Task characterisation and category proposal | Gate table decides admissibility and records refusal |
| 2: Corpus and adversarial set construction | Hybrid | Candidate labels, hard negatives, attack queries | Adjudication rule and holdout partition bind |
| 3: Encoder calibration and fingerprint definition | Hybrid | Vector production for every candidate configuration | Exact-search comparison selects; the fingerprint is computed, not asserted |
| 4: Index construction and approximation tuning | Deterministic | None beyond query vectors already fixed in Phase 3 | Recall arithmetic and gate verdicts |
| 5: Lifecycle enforcement and compression gating | Hybrid | Latent encoding and post-freeze question generation | Generation immutability and the bounded-loss gate |
| 6: Adversarial, privacy, and erasure verification | Hybrid | Attack execution and probe generation | Threshold verdicts and residual-match counts |
| 7: Migration, shadow release, and operation | Deterministic | Answer synthesis on shadow traffic for task-success measurement | Alias swap, rollback, deletion propagation, telemetry |

**Handoff discipline**: Where a step mixes tiers the handoff is explicit. The model tier writes its proposal to a named artifact carrying the model identifier and revision that produced it; the deterministic tier reads that artifact, applies its rule, and writes a verdict record that supersedes the proposal. No step permits a model output to enter serving state without an intervening deterministic verdict.

### 1.4 The Admissibility Gate: Selecting a Representation Category

The gate runs before any encoder is chosen and returns exactly one admitted category or a refusal. It is bounded to 2 percent of the projected build budget; a gate consuming more indicates the evidence contract in Step 1.1 is underspecified.

**Category one is admitted by default** wherever explicit records exist, may be retained, and can be returned to the caller. No further justification is required. A deployment unable to state why it is not using category one has already chosen wrongly.

**Category two is admitted only where all five conditions hold**: repeated context cost is measured rather than assumed, at a minimum 4-fold effective compression on the target workload; the canonical source is retained and reachable at query time; the supported tasks do not require the system to quote and cite its basis; answer preservation clears the gate in Step 5.2; and the compressor and consumer model revisions are pinned as one artifact bundle. Failing any condition returns category one.

**Category three is refused at this layer** in all cases, and the refusal is recorded with the requirement that motivated the request. Where external retrieval, hybrid lexical search, explicit summaries, and a larger bounded context have all been measured against a requirement and all fail it, the gate emits a referral naming the unmet requirement, the baselines already excluded, and the assurance obligations the receiving process must discharge: long-horizon retention, update-order sensitivity, reset reproducibility, cross-session leakage, poisoning recovery, and deletion or retraining completeness.

**Category four is refused at this layer** on the same terms. Where conditioning behaviour is the actual requirement, the gate returns explicit system instructions as the agent-layer substitute, which are more inspectable, more portable across providers, and editable without a training run.

**Admissibility Decision Table**:

| Observable condition | Evidence obligation | Gate verdict |
| :-- | :-- | :-- |
| Explicit records exist and may be retained | Citation required or permitted | Admit category one |
| Exact identifiers, codes, or quotations dominate queries | Lexical baseline compared on the frozen corpus | Admit category one with hybrid retrieval; dense alone is refused |
| Repeated stable context with measured token cost | Compression at least 4-fold and canonical copy retained | Admit category two under the Step 5.2 gate |
| Legal, numeric, safety-critical, or disputed content | Citation obligation present | Refuse category two; admit category one |
| Differentiable or streaming adaptation claimed necessary | All 4 counterfactual baselines measured and failing | Refuse; emit a category-three referral |
| Stable task conditioning across many tasks | Explicit instructions measured as insufficient | Refuse; emit a category-four referral and adopt explicit instructions |
| Required auditability exceeds the category's capability | Any | Refuse the design and halt |

**Numeric gate rules**: Admit a category only where at least 1 counterfactual baseline has been measured on the target corpus. Where fewer than 2 distinct retrieval configurations have been evaluated the gate returns refusal and the run halts, because no comparison exists. Where projected re-embedding cost for the admitted configuration exceeds 25 percent of the annual retrieval budget, the gate escalates for human authorisation rather than proceeding.

***

## II. Operational Framework: Versioned Latent Representations Over Retained Canonical Evidence

The framework assumes the admissibility gate in Section 1.4 has returned category one, or category one with a bounded category-two extension. Phases 1 through 6 build and qualify a candidate representation generation; Phase 7 promotes it, operates it, and returns control to Phase 2 whenever corpus composition, encoder revision, preprocessing, metric, index software, filter schema, quantization, regulation, or threat evidence changes. Each phase declares its owning execution tier, and no phase advances while a mandatory gate from its predecessor is unmet.

### Phase 1: Contract Definition and Category Admissibility

**Objective**: Fix what the memory is for, what evidence it must produce, and which representation category is permitted, before any encoder, index, or corpus expenditure occurs.

**Execution tier**: Hybrid. The model tier characterises tasks and proposes a category; the deterministic gate table decides admissibility and records every refusal.

#### Step 1.1: Establish the Decision and Evidence Contract

**Required Actions**:

- Enumerate the supported tasks, and assign each a consequence class from reversible, costly-reversible, and irreversible.
- Declare for each task whether an answer must quote and cite a canonical source, and whether abstention is a permitted outcome.
- Record the eligible corpus, source granularity, languages, modalities, maximum input size, update frequency, sensitivity class, and tenant boundaries.
- Declare the deletion objective as a maximum interval from request to verified physical removal, the latency objective as a percentile bound, and the cost ceiling per query and per rebuild.
- Declare every release gate as a named metric with a numeric threshold and the action taken on breach, covering labeled recall at k, normalized discounted cumulative gain, mean reciprocal rank, ANN gap, filtered recall, citation support, task success, drift, inversion and membership risk, compression preservation where category two is in scope, latency percentiles, and rebuild cost.
- Represent the contract as structured state a validator can read, not as prose an operator interprets.

**Required Outputs**:

- An evidence contract record naming tasks, consequence classes, citation obligations, and abstention permissions.
- A corpus and boundary record naming languages, modalities, sensitivity classes, and tenant partitions.
- A gate table with one row per metric, its threshold, and its breach consequence.
- An objective record carrying deletion interval, latency percentile bound, and cost ceilings.

**Quality Checkpoints**:

- Every gate row carries a numeric threshold and a named breach consequence; a row without both halts the run before corpus construction.
- Every task carries a consequence class and a citation obligation; an unclassified task is treated as irreversible and citation-obligated by default.
- The deletion objective is stated as an interval rather than as a commitment to delete, since an interval is testable and a commitment is not.
- Abstention is declared as a distinct outcome from failure, so a supported refusal is not scored as a retrieval miss.

***

#### Step 1.2: Freeze Counterfactual Baselines

**Required Actions**:

- Freeze a no-memory baseline that answers from the model alone, establishing the floor any representation must beat.
- Freeze a lexical baseline over the same eligible corpus and the same authorization filters, retaining it permanently as a fault detector for encoder drift and as the recovery path during re-embedding.
- Freeze an exact dense baseline that performs brute-force similarity over the full vector set, which becomes the reference oracle for every approximation measurement in Phase 4.
- Freeze a hybrid baseline fusing lexical and dense candidates, since document memory usually requires both.
- Freeze an explicit-summary or bounded-long-context baseline wherever category two is under consideration, so compression is compared against the cheapest alternative that preserves readable text.
- Pin every baseline to the same corpus snapshot identifier, authorization policy version, and reranker revision, so later differences are attributable to the representation rather than to the environment.

**Required Outputs**:

- A baseline inventory of at least 4 frozen configurations with their snapshot and policy versions recorded.
- A baseline result set per configuration over the development query set.
- A pinning record naming corpus snapshot, authorization policy version, and reranker revision shared by all baselines.

**Quality Checkpoints**:

- At least 4 baselines are frozen; fewer removes the comparison the admissibility gate requires and halts the run.
- Every baseline shares one corpus snapshot and one authorization policy version; a mismatched baseline is rebuilt rather than adjusted.
- The lexical baseline remains in the deployment plan after dense retrieval is adopted, since its removal eliminates the independent signal used to detect silent recall degradation.
- The exact dense baseline is reproducible from stored vectors and query identifiers without re-encoding, so later comparisons isolate index error from encoder change.

***

#### Step 1.3: Record the Admitted Category and Its Justification

**Required Actions**:

- Run the admissibility gate in Section 1.4 against the contract and the baseline results, and record the single admitted category.
- Record, for each refused category, the requirement that motivated the request and the baseline evidence that defeated it.
- Emit a referral record rather than an implementation plan wherever category three or category four is requested, naming the unmet requirement and the assurance obligations the receiving process must discharge.
- Where category two is admitted, bind the compressor identifier and revision, the consumer model identifier and revision, the prompt template version, the latent length, and the decoding procedure into one artifact bundle identifier, and record that the bundle is invalidated by any base-model change.
- Record the residual risk accepted by the admitted category, covering interpretability, portability, erasure complexity, and evaluation burden.

**Required Outputs**:

- A category admission record naming exactly 1 admitted category and its justification.
- A refusal record per rejected category with its motivating requirement and defeating evidence.
- A referral record where a below-layer category was requested, carrying the assurance obligation list.
- An artifact bundle identifier where category two is admitted.

**Quality Checkpoints**:

- Exactly 1 category is admitted; a plan carrying two admitted categories in one index is rejected outright.
- Every refusal names the evidence that defeated the request, so the decision is auditable rather than assertive.
- No referral record contains an implementation instruction, since the receiving process operates below the layer this framework executes at.
- The residual risk record names all 4 declared dimensions; an unnamed dimension is treated as unaccepted risk and blocks advancement.

***

### Phase 2: Evaluation Corpus and Adversarial Set Construction

**Objective**: Build the frozen labeled, adversarial, and held-out material against which every later configuration is judged, so that selection rests on measurement over the target corpus rather than on a public leaderboard rank.

**Execution tier**: Hybrid. The model tier proposes candidate labels, hard negatives, and attack queries; the adjudication rule and the holdout partition are deterministic and bind the result.

#### Step 2.1: Adjudicate the Labeled Relevance Corpus

**Required Actions**:

- Collect production-like queries covering exact identifiers, paraphrases, rare concepts, negation, temporal questions, conflicting sources, multilingual cases, and questions with no relevant result.
- Generate candidate relevance judgements by model inference over pooled results from every frozen baseline, so the pool is not biased toward one retrieval method.
- Adjudicate every candidate judgement deterministically against a written relevance rubric, recording graded relevance rather than a binary flag.
- Record for every judged pair the source identifier, source version, and the lawful offsets of the supporting span, so citation support becomes machine-checkable.
- Record the adjudicator identity, the rubric version, and the inter-adjudicator agreement rate for a sampled subset.

**Required Outputs**:

- A labeled query set with graded relevance judgements and pooled provenance per judgement.
- A supporting-span record per judged relevant pair carrying source version and offsets.
- An adjudication record naming rubric version, adjudicator identity, and sampled agreement rate.

**Quality Checkpoints**:

- Every judgement traces to a pooled candidate from at least 2 baselines, so single-method pooling bias is bounded.
- Every relevant pair carries a resolvable supporting span; a pair without one is demoted to unjudged rather than counted as relevant.
- Sampled inter-adjudicator agreement is at least 0.70; below that the rubric is revised and the affected judgements are re-adjudicated.
- No model-proposed judgement enters the labeled set without a deterministic adjudication verdict recorded against it.

***

#### Step 2.2: Construct Adversarial, Cohort, and Poisoning Slices

**Required Actions**:

- Construct hard negatives that are semantically near the query while contradicting, superseding, or lacking authority for the answer.
- Construct cohort slices by language, modality, tenant size, query type, term rarity, and filter selectivity, so worst-slice behaviour is measurable rather than averaged away.
- Construct a poisoning candidate set of records crafted to dominate a target query's neighbourhood, modelled on documented retrieval-corpus poisoning [30].
- Construct a personal-data slice whose records are known to be subject to erasure, so deletion verification in Phase 6 has a defined target.
- Construct an inversion probe set of short records, since inversion effectiveness is strongest at short lengths [28].
- Record the generator model identifier and revision for every synthesised query or record, and mark synthesised material distinctly from observed material.

**Required Outputs**:

- A hard-negative set linked to the queries it opposes.
- A cohort slice definition covering at least 6 declared dimensions.
- A poisoning candidate set, a personal-data slice, and an inversion probe set, each with a defined target.
- A provenance record separating synthesised from observed material.

**Quality Checkpoints**:

- Every cohort dimension carries at least 30 queries; a thinner slice is reported as an untested cohort rather than as a passing one.
- Synthesised material never exceeds 50 percent of any cohort slice, since a slice made entirely of generated text measures the generator rather than the corpus.
- Every poisoning candidate names the query whose neighbourhood it targets, so a null result is distinguishable from an unexecuted test.
- The inversion probe set contains records short enough to represent the strongest documented attack condition, and this is recorded as an attack assumption rather than an average case.

***

#### Step 2.3: Partition Development, Holdout, and Attack Sets

**Required Actions**:

- Split the labeled corpus into a development partition used for tuning and a holdout partition used only for release decisions.
- Separate the holdout by time and by source, so a configuration tuned on one period or one publisher is not validated on the same material.
- Verify that no source identifier, near-duplicate cluster, or template family appears in both partitions.
- Keep the attack sets outside both partitions, so red-team results cannot be optimised against during tuning.
- Compute and record a content hash over each partition, and treat any change to a hash as a new corpus version requiring re-baselining.
- Restrict holdout access to the release gate, and record every holdout evaluation with its timestamp and configuration identifier.

**Required Outputs**:

- A partition manifest naming development, holdout, and attack sets with their content hashes.
- A leakage report listing overlapping identifiers, duplicate clusters, and template families, with the resolution applied to each.
- A holdout access log carrying one entry per release evaluation.

**Quality Checkpoints**:

- The holdout is separated by both time and source; separation on one dimension alone is recorded as a weaker validation claim.
- Overlap between partitions is zero after resolution; any residual overlap halts release rather than being noted as a caveat.
- Holdout evaluations per candidate configuration do not exceed 3, above which the holdout is treated as contaminated and rebuilt.
- Every partition carries a content hash, since an unhashed partition cannot support a reproducible release claim.

***

### Phase 3: Encoder Calibration and Representation Fingerprint Definition

**Objective**: Select the encoder configuration that clears every relevance and cohort gate on the target corpus under exact search, and freeze it into an enforceable fingerprint.

**Execution tier**: Hybrid. The model tier produces vectors for every candidate configuration; the deterministic tier performs exact-search comparison, selects the configuration, and computes the fingerprint rather than accepting an asserted one.

#### Step 3.1: Screen Candidate Encoders Against Exact Search

**Required Actions**:

- Use public multi-task and zero-shot retrieval benchmarks to screen broad competence and to bound the candidate list, never to choose the production configuration [19][20].
- Reproduce every surviving candidate on the frozen development corpus using exact search, so index approximation cannot contaminate the encoder comparison.
- Measure recall at k, normalized discounted cumulative gain, and mean reciprocal rank against the adjudicated labels, and measure end-to-end task success alongside them, since a configuration that improves generic relevance can still return unciteable spans or miss exact codes.
- Compare each candidate against the lexical, hybrid, and no-memory baselines on the same queries and the same authorization filters.
- Report every cohort slice separately with interval estimates, and record the worst slice rather than the pooled mean as the selection figure.
- Treat similarity scores as ordinal within one configuration and never as probabilities or as comparable across models, languages, corpora, or revisions.

**Required Outputs**:

- A candidate screening record naming excluded models and the benchmark evidence that excluded them.
- An exact-search result set per candidate over the development partition.
- A relevance and task-success report per candidate with per-cohort intervals and a named worst slice.
- A baseline comparison table placing every candidate against lexical, hybrid, and no-memory results.

**Quality Checkpoints**:

- No candidate is selected on benchmark rank alone; selection without a target-corpus reproduction is rejected.
- Every reported figure comes from exact search, so encoder error is isolated from approximation error at this stage.
- The worst cohort slice sits no more than 10 percentage points below the pooled figure; a larger spread blocks selection until the failing cohort is addressed or declared out of scope.
- A candidate that does not beat the lexical baseline on exact-identifier queries is adopted only inside a hybrid configuration, never as a sole retrieval path.

***

#### Step 3.2: Fix Input Role, Dimension, Normalization, and Metric

**Required Actions**:

- Apply the documented asymmetric input roles for queries and for documents where the encoder exposes them, since embedding both sides as generic text silently reduces retrieval [1].
- Sweep candidate dimensions and select the smallest that clears every quality gate at the target latency and storage, comparing each truncation against the full vector on exact recall, cohort recall, and worst slice.
- Apply nested-representation truncation only where the model was trained or documented for shortening, and treat any post-hoc reduction learned after generation as a separate transform carrying its own immutable version [21].
- Fix the distance metric to the one the encoder documents, and record whether vectors are unit-normalized, since a provider that normalizes to unit length permits a dot product to stand for cosine similarity [18].
- Fit score calibration on adjudicated production pairs and retain an abstention region, rather than declaring a universal similarity threshold.
- Record the deterministic preprocessing pipeline: normalization, redaction, chunk selection, role selection, and length handling, each with a version identifier.

**Required Outputs**:

- A role assignment record naming the query mode and the document mode used at both build and serving time.
- A dimension selection record with per-dimension comparison against the full vector.
- A metric and normalization declaration bound to the encoder revision.
- A score calibration function with its fitting set identifier and a declared abstention band.
- A preprocessing manifest with one version identifier per stage.

**Quality Checkpoints**:

- Query and document roles at serving time match the roles used at build time; a mismatch invalidates the generation rather than degrading it gracefully.
- Every reduced dimension was compared against the full vector on the worst cohort, not on the pooled mean.
- No fixed similarity threshold is declared as universally meaningful; thresholds appear only as fitted calibration outputs with a stated fitting set.
- Silent truncation is rejected at write time rather than logged, since a truncated input produces a vector for content the record does not contain.

***

#### Step 3.3: Define and Enforce the Representation Fingerprint

**Required Actions**:

- Compute the fingerprint as a hash over encoder identifier, encoder revision, tokenizer identifier and revision, input role, preprocessing version, redaction version, full dimension, served dimension, reduction method and version, normalization, numeric type, and distance metric.
- Encode the generation in physical namespace, index name, access policy, and query route, rather than in optional metadata a query may omit.
- Reject at write time any vector whose fingerprint differs from the target generation's fingerprint, and reject at query time any query vector whose fingerprint differs from the served generation's.
- Bind every vector to its canonical record through a source identifier, a source version identifier, and a source content hash, and publish the vector only after the canonical record commits.
- Make writes idempotent through a stable idempotency key, and record write sequence, commit status, visibility time, and replica acknowledgement count.
- Record the vector checksum, sensitivity class, and retention class alongside every stored representation.

**Required Outputs**:

- A fingerprint specification naming all 13 constituent fields and the hash function over them.
- A namespace and routing map binding each fingerprint to exactly 1 physical generation.
- A write contract record covering idempotency key, commit ordering, and visibility semantics.
- A per-vector provenance record carrying source identifier, source version, content hash, checksum, sensitivity class, and retention class.

**Quality Checkpoints**:

- Mixed-fingerprint writes accepted into any generation total exactly 0; a non-zero count halts the index and triggers a rebuild of the affected generation.
- Every vector resolves to an authorized canonical record at the recorded version; an unresolvable vector is quarantined rather than served.
- No vector becomes visible before its canonical record commits, so a search result can never precede the evidence it points at.
- Equal dimension between two configurations is never accepted as evidence of compatible coordinates.

***

### Phase 4: Index Construction and Approximation Tuning

**Objective**: Establish how much recall the serving index sacrifices relative to exact search, under real concurrency and real filter selectivity, and bound that sacrifice by a declared gate.

**Execution tier**: Deterministic throughout. Vectors are already fixed by Phase 3, and every decision in this phase is arithmetic over retrieved identifier sets.

#### Step 4.1: Establish the Exact-Search Reference and Measure the ANN Gap

**Required Actions**:

- Build an exact flat reference over the same vectors, the same metric, and the same eligible set as the candidate index.
- Measure ANN recall at k as the fraction of exact top-k neighbors the approximate index returns, on a representative query sample.
- Measure labeled recall at k separately, since reproducing exact neighbors does not establish that those neighbors are relevant.
- Report the ANN gap as a distinct quantity from embedding-model error, so a regression can be attributed to the index or to the representation but not ambiguously to both.
- Prefer exact search outright wherever the eligible set is small enough that brute force meets the latency objective, since exactness removes an entire class of failure.
- Record index algorithm, library, library version, build host class, peak memory, build duration, index bytes, and replica count for every build.

**Index Family Selection**:

| Family | Primary tradeoff | Selection signal | Principal risk |
| :-- | :-- | :-- | :-- |
| Exact flat | No approximation error, linear scan cost | Eligible set small or latency budget generous | Cost grows with corpus size |
| Proximity graph | High recall at low latency, higher memory and slower build [22][23] | Large corpus, high query concurrency | Tombstone accumulation, insertion-order sensitivity |
| Inverted file partitioning | Lower memory, recall varies with probe count [23] | Corpus stable, memory constrained | Quantizer training drift as distribution shifts |
| Product quantization | Large memory reduction, added distance error [23] | Raw vectors exceed memory envelope | Catastrophic loss on low-frequency cohorts |
| Partitioned and reordered scoring | Recall and throughput tuned jointly [24] | Throughput-bound workloads | Configuration complexity |
| Disk-backed graph | Billion-scale search on secondary storage [25] | Corpus exceeds memory at any precision | Latency tail sensitivity |

**Required Outputs**:

- An exact reference result set per sampled query.
- An ANN recall report at the declared k with its sample size.
- A labeled recall report at the same k, reported separately from the ANN figure.
- A build record per index carrying algorithm, library version, resource use, and validation sample identifier.

**Quality Checkpoints**:

- ANN recall at k is at least 0.95 against the exact reference; below 0.90 the configuration is rejected rather than released with a warning.
- The ANN gap and the embedding-model error are reported as separate figures; a single combined quality number fails this checkpoint.
- The recall sample contains at least 1,000 queries drawn across every cohort slice, since a pooled sample conceals cohort collapse.
- Exact search is adopted wherever it meets the latency objective, and a decision to approximate anyway is recorded with its justification.

***

#### Step 4.2: Tune Index Parameters Under Filter-Selectivity Bands

**Required Actions**:

- Sweep construction connectivity, construction candidate list, search candidate list, partition count, and probe count at production concurrency and on the real corpus geometry, rather than adopting library defaults.
- Repeat every sweep inside declared filter-selectivity bands, measuring recall against the exact neighbors of the eligible subset rather than of the whole corpus.
- Measure result shortfall as the rate at which a filtered query returns fewer than k eligible results, since candidate generation before filtering discards most candidates when the filter is restrictive [26][27].
- Enable engine-supported iterative or continued scanning where filtered queries fall short, and record the scan limit as part of the configuration.
- Partition highly selective or high-security tenants into their own namespaces rather than relying on oversampling, and use exact search inside small eligible sets.
- Record search parameters per query in telemetry, so a latency or recall regression can be attributed to a configuration change.

**Required Outputs**:

- A parameter sweep record covering build and search parameters at production concurrency.
- A filtered recall report per selectivity band with result shortfall rates.
- A partitioning decision record naming tenants moved to dedicated namespaces and the selectivity that motivated the move.
- A per-query search parameter telemetry field set.

**Quality Checkpoints**:

- Filtered recall inside the exact eligible subset is at least 0.95 in every declared selectivity band; a failing band blocks release for the tenants it covers.
- Result shortfall does not exceed 1 percent of filtered queries; above that the band is served by exact search or by a dedicated partition.
- At least 4 selectivity bands are measured, spanning from permissive to highly restrictive, since a single band cannot detect the collapse.
- No filter is applied after candidate selection for a tenant in the highest sensitivity class; prefiltering or partitioning is mandatory there.

***

#### Step 4.3: Apply Quantization and Dimension Reduction Under Paired Ablation

**Required Actions**:

- Apply lower precision, scalar or product quantization, binary representations, or nested truncation only where raw and index memory prevent the required corpus size, concurrency, or latency.
- Begin with the least lossy change available, and pair every compressed run with a full-dimension, full-precision exact and approximate baseline under identical queries and identical filters.
- Ablate each lossy transform in isolation before combining any two, since stacked reduction, quantization, and low search effort mask one another's contribution.
- Withhold quantization entirely where small neighborhood differences drive consequential decisions, where relevance labels are sparse, where multilingual or rare-query cohorts are already weak, or where reranking cannot recover candidates the first stage lost.
- Record raw dimension, served dimension, numeric type, codebook or transform version, training sample hash, and measured reconstruction or distance error for every compressed configuration.
- Model storage explicitly as vector count multiplied by served dimension and bytes per component, then add identifiers, metadata, graph or list overhead, codebooks, tombstones, replicas, snapshots, allocator slack, caches, and dual generations.

**Required Outputs**:

- A paired ablation report with one isolated result per lossy transform.
- A compressed configuration record carrying dimension, numeric type, transform version, and training sample hash.
- A storage model naming every overhead component beyond raw vector bytes.
- A cohort loss report identifying the worst-affected slice for each transform.

**Quality Checkpoints**:

- Worst-cohort recall loss from any single lossy transform does not exceed 3 percentage points; a larger loss reverts that transform.
- No two lossy transforms are combined before each has an isolated ablation result; a combined-only result fails this checkpoint.
- Storage saving alone never satisfies a release gate; labeled recall, ANN gap, filtered recall, citation support, task success, latency, and worst-slice robustness must all clear simultaneously.
- The storage model accounts for dual generations, since a migration that cannot hold two generations at once cannot be rolled back.

***

### Phase 5: Lifecycle Enforcement and Latent Compression Gating

**Objective**: Make every representation belong to an immutable generation with a recorded dependency set, and permit a latent to stand in for evidence only where measured loss is bounded.

**Execution tier**: Hybrid. Latent encoding and post-freeze question generation are model-tier work; generation immutability, dependency recording, and the bounded-loss gate are deterministic and hold authority.

#### Step 5.1: Enforce Immutable Generations and Canonical Lineage

**Required Actions**:

- Treat every generation as append-only until sealed, and never edit a sealed generation in place.
- Route all queries through exactly 1 routing alias, so no caller addresses a physical generation directly.
- Publish a generation as complete only after built vector count, expected vector count, and canonical coverage reconcile; never expose a partially populated index as complete.
- Record parent generation, source snapshot identifier, source snapshot time, expected count, built count, missing count, and duplicate count for every build.
- During any rebuild, serve either one immutable old generation plus a live delta or a fully synchronised new generation, and never a mixture of the two.
- Schedule tombstone cleanup and compaction against declared limits on tombstone fraction, insertion-order skew, distribution shift, quantizer staleness, and measured recall degradation, since graph indexes accumulate deletion markers and very large cleanup jobs consume serving resources [26].

**Required Outputs**:

- A generation manifest per build with reconciliation counts and a sealed or open status.
- A routing alias record naming the single serving generation and its change history.
- A maintenance policy naming the declared limits that trigger cleanup or rebuild.
- A delta-serving record covering every interval in which a rebuild was in progress.

**Quality Checkpoints**:

- Canonical coverage of a sealed generation is at least 99.9 percent of the eligible snapshot; below that the generation stays open and is never aliased.
- Missing and duplicate vector counts are both reported; an unreported count blocks sealing.
- Exactly 1 generation is reachable through the alias at any instant; concurrent reachability of two generations is a defect that halts serving.
- Tombstone fraction stays below 20 percent of the generation; above that a rebuild is scheduled rather than deferred.

***

#### Step 5.2: Gate Latent Compression on Bounded-Loss Evidence

**Required Actions**:

- Compute effective compression as original tokens divided by latent tokens, and report it separately from every preservation measure, since a reported ratio is not an information-preservation guarantee [3][4].
- Measure answer preservation on the adjudicated question set, and separately on questions written after the compressor was frozen, so preservation is not confined to anticipated queries.
- Measure exact-fact retention for names, quantities, dates, and identifiers; negation retention; chronology retention; and contradiction exposure, since averages do not identify which details disappeared.
- Measure citation support by resolving the latent's answer back to the canonical source and verifying the cited span exists at the recorded version and offsets; never accept the nearest passage as a post-hoc rationalisation.
- Measure reconstruction quality where a decoder exists, and record its absence as a reduced verification capability where it does not.
- Retain the canonical explicit copy for every compressed latent, and record the expiry time and the dependency set that a deletion must traverse.
- Disable lossy serving entirely for legal evidence, precise quantities, commitments, safety constraints, medical or financial determinations, disputed claims, and any output that must quote its basis.

**Required Outputs**:

- A compression report naming effective ratio, answer preservation, post-freeze preservation, rare-fact retention, negation retention, and citation support.
- A reconstruction result where a decoder exists, or an explicit record of its absence.
- An artifact bundle record binding compressor revision, consumer revision, prompt template version, latent length, and decoding procedure.
- A canonical retention record and a deletion dependency set per latent.

**Quality Checkpoints**:

- Answer preservation is at least 95 percent on the frozen question set and at least 90 percent on post-freeze questions; failing either reverts the workload to category one.
- Rare-fact and negation retention are each at least 90 percent; a shortfall on either blocks adoption regardless of the average.
- Effective compression is at least 4-fold; below that the token saving does not repay the lost auditability and the latent is not adopted.
- A canonical copy exists for every compressed latent; a latent that is the only surviving artifact for a citation-obligated task fails this checkpoint outright.

***

#### Step 5.3: Register Artifacts and Record Deletion Dependencies

**Required Actions**:

- Register every encoder, transform, quantizer, compressor, evaluator, and index build as a versioned artifact with a checksum, a registry location, and an intended scope [34].
- Record for every artifact the inputs it consumed and the artifacts derived from it, so a deletion request can be resolved into a dependency traversal rather than a search.
- Record for every subject the canonical records, chunks, embeddings, latents, quantizer training samples, caches, replicas, snapshots, evaluation fixtures, and retired generations that depend on their data.
- Record the backup class and expiry for every store holding derived representations, since a restorable backup that returns a deleted vector defeats an erasure claim.
- Record whether a deletion is satisfiable by removal and rebuild, or requires a broader remediation, and record that a latent is deletable only where its dependency set is known.
- Treat any embedding or latent derived from personal or confidential content as sensitive by default, since regulatory classification follows identifiability and context rather than file format [29].

**Required Outputs**:

- An artifact registry entry per versioned component with checksum and scope.
- A derivation graph linking every artifact to its inputs and its dependents.
- A per-subject deletion dependency set naming every store that must be traversed.
- A backup class and expiry record per store holding derived representations.

**Quality Checkpoints**:

- Every stored representation resolves to a registry entry; an unregistered artifact cannot be released.
- Every subject in the personal-data slice resolves to a complete dependency set before that slice is admitted to the corpus.
- No latent is admitted whose dependency set is unknown, since it could not later be deleted.
- Backup expiry is recorded for 100 percent of stores holding derived representations; an unrecorded store is treated as an unbounded retention and blocks admission of sensitive data.

***

### Phase 6: Adversarial, Privacy, and Erasure Verification

**Objective**: Establish by measurement, before release, that the representation does not leak its sources, cannot be dominated by injected records, and can be erased verifiably.

**Execution tier**: Hybrid. Attack execution and probe generation are model-tier work; every threshold verdict and every residual-match count is deterministic and binding.

#### Step 6.1: Run Inversion, Membership, and Attribute Probes

**Required Actions**:

- Run an inversion attack against the probe set built in Step 2.2, and record exact recovery rate and partial token overlap, since iterative inversion has recovered a large majority of short inputs exactly for targeted encoders and has recovered names from clinical text [28].
- Run a membership inference test over held-out and in-corpus records, reporting the attack area under the curve and the false positive rate.
- Run attribute inference probes for sensitive attributes, and record probe success as an indication of encoded information rather than as a complete explanation of the representation.
- Record attacker knowledge, query budget, and attack model identity for every run, since a result without an attacker model is not a risk statement.
- Restrict raw-vector export, rate-limit similarity probing, and remove raw vectors and reconstructed text from ordinary telemetry, since aggregate timing and result-count differences alone can leak membership.
- Reduce exposed numeric precision only after utility testing, never as a first mitigation.

**Required Outputs**:

- An inversion result set with exact recovery rate, token overlap, and the attacker model recorded.
- A membership inference result with area under the curve and false positive rate.
- An attribute probe result per tested attribute.
- A control record naming export restrictions, probe rate limits, and telemetry redactions applied.

**Quality Checkpoints**:

- Exact inversion recovery on the probe set does not exceed 5 percent; above that the corpus is not admitted at the declared sensitivity class.
- Membership inference area under the curve does not exceed 0.60; above that the store is partitioned or the sensitivity class is raised.
- Every attack result records attacker knowledge and query budget; a result without both is treated as unmeasured.
- Raw vectors and reconstructed text appear in 0 ordinary telemetry records; a single occurrence halts log release.

***

#### Step 6.2: Run Poisoning, Hubness, and Cross-Tenant Isolation Tests

**Required Actions**:

- Inject the poisoning candidate set and measure whether a small number of crafted records can drive attacker-chosen answers for targeted queries, since this has been demonstrated in evaluated retrieval corpora [30].
- Require authenticated sources, quarantine unauthenticated ingestion, enforce per-source caps, and diversify results, so no single source can dominate a neighbourhood.
- Measure result-frequency concentration to detect hubness, and measure per-language and per-cohort score distributions and neighbourhood purity.
- Compare dense results against the retained lexical baseline and record disagreement rate, since divergence is an early detector of a poisoned or drifted neighbourhood.
- Execute cross-tenant negative queries that must return zero results, and verify that a missed prefilter cannot expose another tenant's records.
- Re-authorize every consequential action outside the model and outside the retrieval content, so a retrieved instruction can never authorize itself.

**Required Outputs**:

- A poisoning result naming injected record count, targeted queries, and attacker success rate.
- A hubness report with result-frequency concentration and duplicate cluster caps applied.
- A lexical disagreement report per cohort.
- A cross-tenant isolation result covering every declared tenant boundary.

**Quality Checkpoints**:

- No single record appears in more than 2 percent of top-10 result sets; above that a duplicate cap or diversification rule is applied and the test is rerun.
- Attacker success under the declared injection budget does not exceed 5 percent of targeted queries; above that ingestion authentication and per-source caps are tightened before release.
- Cross-tenant negative queries return exactly 0 results; a single leak halts release and triggers physical partitioning.
- Lexical disagreement above 30 percent in any cohort is investigated before release rather than recorded as expected variance.

***

#### Step 6.3: Verify Erasure Across Generations, Replicas, and Backups

**Required Actions**:

- Write a serving tombstone immediately on request, so the record becomes ineligible before physical removal completes.
- Traverse the dependency set recorded in Step 5.3, removing canonical text, chunks, embeddings, latents, graph entries, quantizer training samples where material, caches, replicas, snapshots, evaluation fixtures, and retired generations.
- Verify erasure by executing the original nearest-neighbor queries against every retained generation and counting residual matches.
- Restore a backup into an isolated environment, execute the same verification queries, and record whether the deleted representation returns.
- Rerun inversion and membership probes restricted to the deleted subject, so a claim of removal is supported by attack evidence and not only by an absent row.
- Record the residual risk that survives verification, and never assert erasure on the basis that the canonical source row is gone.

**Required Outputs**:

- A deletion record per request naming tombstone time, serving-ineligible time, physical completion time, and every generation traversed.
- A verification record carrying the queries executed, the generations searched, and the residual match count.
- A backup restoration test result from an isolated environment.
- A residual risk statement per deletion class.

**Quality Checkpoints**:

- Serving ineligibility is achieved within 60 seconds of the request; a longer interval is a contract breach that escalates.
- Residual match count across all retained generations is exactly 0; any non-zero count blocks the erasure claim and reopens the traversal.
- A backup restoration test is executed at least once per quarter and after every change to the backup class; an untested backup invalidates the erasure claim for the records it holds.
- Physical removal completes within the declared deletion objective, defaulting to 30 days; an overrun escalates rather than extending the objective silently.

***

### Phase 7: Migration, Shadow Release, and Steady-State Operation

**Objective**: Promote a qualified generation without exposing a partially validated index, and operate the running system so that degradation is detected by measurement rather than by complaint.

**Execution tier**: Deterministic. The model tier contributes only answer synthesis on shadow traffic for task-success measurement; alias swap, rollback, deletion propagation, and telemetry are software decisions.

#### Step 7.1: Rehearse Dual-Index Migration and Rollback

**Required Actions**:

- Build the new generation from the same eligible canonical snapshot, then replay every write, correction, and tombstone that arrived after the snapshot cursor.
- Reserve write capacity for the live delta throughout the rebuild, so ingestion is not paused for the duration of a capital migration.
- Test a representative shard before committing the full corpus, and extrapolate cost from measured shard results rather than from list prices.
- Rehearse the atomic alias swap and the rollback in a non-production environment, and rehearse a deletion executed across both generations simultaneously.
- Corrupt or stop an encoder worker, an index shard, a registry dependency, and a replica in turn, and verify that degradation is bounded and observable rather than silent.
- Re-embed only where the incumbent materially fails a new language, modality, domain, input length, security requirement, or quality gate; where a revision is retired; or where dimension savings repay the migration cost. Remain on a validated incumbent where gains are leaderboard-small, where target-corpus improvement is absent, where the rebuild cannot finish inside the freshness or deletion objective, or where consumers depend on the incumbent's calibrated scores.

**Required Outputs**:

- A migration record naming reason, source generation, target generation, snapshot cursor, delta replay cursor, eligible count, embedded count, failed count, and replayed tombstone count.
- A pilot shard cost measurement with its extrapolation to the full corpus.
- A rehearsal record covering alias swap, rollback, cross-generation deletion, and 4 injected fault classes.
- A capacity plan covering old generation, new generation, and live delta held simultaneously.

**Quality Checkpoints**:

- Full-corpus cost is extrapolated from a measured shard of at least 1 percent of eligible records; an unmeasured estimate blocks commitment.
- Delta replay reaches the alias swap point with 0 unreplayed tombstones; an unreplayed tombstone would resurrect deleted content and halts the swap.
- All 4 injected fault classes produce bounded and observable degradation; a silent failure blocks release.
- Rollback is rehearsed successfully before the first production swap, since a rollback first attempted under incident conditions is not a rollback.

***

#### Step 7.2: Shadow and Canary Against the Live Alias

**Required Actions**:

- Run production queries against the candidate generation without affecting served answers or authorized actions.
- Compare neighbor churn at k, lexical disagreement, filtered shortfall, citation support, task success, latency percentiles, and cost between incumbent and candidate on the same traffic.
- Evaluate the candidate on the holdout partition exactly once for the release decision, and record that evaluation in the holdout access log.
- Canary by low-risk tenant or by low-risk task class, and never by mixing representations inside one index.
- Swap the routing alias atomically only after coverage and every mandatory gate pass, and retain the incumbent generation for the declared rollback window.
- Roll back on any mandatory gate breach or any unexplained cohort shift, without waiting for a root cause.

**Required Outputs**:

- A shadow comparison report covering all 7 declared comparison dimensions.
- A single holdout evaluation record for the release decision.
- A canary plan naming the tenant or task class, the traffic fraction, and the abort condition.
- An alias swap record naming approval identity, swap time, rollback deadline, and rollback trigger.

**Quality Checkpoints**:

- The shadow window covers at least 10,000 production queries or 7 days, whichever completes later; a shorter window is recorded as provisional and blocks promotion for the highest sensitivity class.
- Labeled recall at k does not regress more than 2 percentage points against the incumbent on the holdout; a larger regression blocks the swap.
- The incumbent generation is retained for at least 14 days after the swap, and deletion is enforced across both generations throughout that window.
- No canary mixes fingerprints inside one index; a mixed index is rebuilt rather than corrected.

***

#### Step 7.3: Operate the Telemetry Contract and Reopen the Loop

**Required Actions**:

- Emit append-only events for embedding generation, vector write, index build, generation swap, migration step, deletion, query, filtered search, rerank, compression, and drift test, using a vendor-neutral trace and metric pipeline [35].
- Attach to every event the identity, timing, cost, and outcome fields required for later attribution, and attach the representation fingerprint to every write and query event so mixed revisions are detectable in retrospect.
- Attach adjudicated labels to sampled queries after the fact, so recall at k, ANN gap, normalized discounted cumulative gain, mean reciprocal rank, calibration, and end-to-end utility remain computable from stored telemetry.
- Sample exact-search comparisons continuously against live traffic, rather than only at release, since drift arrives between releases.
- Monitor centroid shift, neighbor churn at k, hub frequency change, lexical disagreement, per-cohort score distribution, and labeled recall change against a declared baseline window.
- Reopen the loop at Phase 2 whenever corpus composition, encoder revision, preprocessing, metric, index software, filter schema, quantization, regulation, or threat evidence changes, and never compensate for drift by adjusting a global similarity threshold.

**Telemetry Event Template**:

```
EVENT_ID:
EVENT_TYPE:              EMBED | WRITE | BUILD | SWAP | MIGRATE |
                         DELETE | QUERY | FILTER | RERANK |
                         COMPRESS | DRIFT_TEST
EVENT_TIME:
TRACE_ID:
TENANT_ID:               pseudonymous
REPRESENTATION_FINGERPRINT:
INDEX_NAME:
INDEX_GENERATION:
SOURCE_ID:
SOURCE_VERSION_ID:
SOURCE_CONTENT_HASH:
EXACT_OR_ANN:
SEARCH_PARAMETERS:
FILTER_EXPRESSION_HASH:
FILTER_SELECTIVITY_ESTIMATE:
ELIGIBLE_COUNT_EXACT:
TOP_K_REQUESTED:
TOP_K_RETURNED:
RESULT_SHORTFALL:
CALIBRATION_VERSION:
LATENCY_MS:
ESTIMATED_COST:
OUTCOME:
ERROR_CLASS:
RAW_VECTOR:              PROHIBITED
RECONSTRUCTED_TEXT:      PROHIBITED
```

**Required Outputs**:

- An append-only event stream covering all 11 declared event types.
- A continuous exact-search sampling record with its sample rate and its measured gap over time.
- A drift monitoring report per cohort against a declared baseline window.
- A reopen trigger log naming the change that returned the system to Phase 2.

**Quality Checkpoints**:

- Every write and query event carries a representation fingerprint; an event without one cannot support a contamination investigation and fails this checkpoint.
- Continuous exact-search sampling covers at least 0.1 percent of production queries; a lower rate is insufficient to detect gap growth before a release boundary.
- Raw vectors and reconstructed text appear in 0 telemetry records.
- A drift alert is closed only by a measurement, never by a threshold adjustment; a closed alert without a measurement is reopened automatically.

***

## III. Implementation Guidance for AI Agents

AI agents operating latent memory must follow systematic protocols ensuring that every representation is fingerprinted, every approximation is measured against an exact reference, and every consequential answer resolves to canonical evidence. The following guidance translates the framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Agent**: Owns the evidence contract, the gate table, and the admissibility decision. It alone admits or refuses a representation category, and it records every refusal with its defeating evidence. It may halt a run whose contract lacks a numeric gate.
2. **Corpus Agent**: Builds the labeled, adversarial, and cohort material, and owns the development, holdout, and attack partitions. It never exposes the holdout during tuning and never accepts a model-proposed label without a deterministic adjudication verdict.
3. **Representation Agent**: Invokes encoders and compressors, produces vectors and latents, and computes fingerprints. It may not select a configuration, because selection belongs to measurement rather than to inference.
4. **Index Agent**: Builds generations, maintains the exact-search reference, tunes approximation parameters, and owns the routing alias. It rejects every mixed-fingerprint write and every incomplete generation.
5. **Assurance Agent**: Executes inversion, membership, attribute, poisoning, hubness, isolation, and erasure verification. It holds a veto over release that no other component may override.
6. **Operations Agent**: Executes migration, shadow comparison, canary, rollback, deletion propagation, and telemetry. It owns the rollback trigger and may act on it without a root cause.

**Evidence Resolution Boundary**: A latent alone never authorizes a consequential action. This is a hard constraint applying to every component.

- Rehydrate the canonical record, verify its authority and freshness, verify the cited span exists at the recorded version and offsets, and apply deterministic policy before any action outside the retrieval boundary.
- Return source passages rather than raw latent values to the generator and to the caller.
- Never infer identity, duplicate status, protected attributes, or factual relations from proximity alone.
- Where a latent answer triggers evidence retrieval afterward, verify that the retrieved source actually supports the claim, and abstain rather than promoting the nearest passage into a citation.

**Workflow Execution Pattern**:

```
STATE: Generation_Promotion_Decision
INPUTS:
  1. Candidate generation manifest from Step 5.1
  2. ANN and filtered recall reports from Phase 4
  3. Assurance verdicts from Phase 6
  4. Shadow comparison report from Step 7.2
ACTIONS:
  1. Reconcile canonical coverage against the eligible snapshot
  2. Compute ANN gap and filtered recall per selectivity band
  3. Compare candidate against incumbent on the single holdout evaluation
  4. Collect the assurance veto state
VALIDATION:
  - mixed_fingerprint_writes == 0
  - canonical_coverage >= 0.999
  - ann_recall_at_k >= 0.95
  - filtered_recall_all_bands >= 0.95
  - result_shortfall_rate <= 0.01
  - labeled_recall_regression <= 0.02
  - unreplayed_tombstones == 0
  - assurance_veto == FALSE
TRANSITIONS:
  IF all_validations_pass AND approval_required == FALSE
     THEN next_state = Atomic_Alias_Swap
  IF all_validations_pass AND approval_required == TRUE
     THEN next_state = Await_Human_Authorisation
  IF validation_failed THEN next_state = Generation_Error_Handling
```

**Two-Phase Action Pattern**: Emit the intended generation change with its manifest, gate values, and rollback deadline without executing it; confirm it against the validation block while the incumbent alias still serves; commit the alias swap only after validation passes, writing the swap record in the same operation.

**Approval Gate**: Human authorisation is required before any alias swap serving a tenant in the highest sensitivity class; before adopting any compressed latent as the sole surviving artifact for a record; before accepting an erasure claim in which a residual match count above 0 is waived; before admitting a corpus whose inversion recovery rate exceeds 5 percent or whose membership inference area under the curve exceeds 0.60; and before any migration projected to exceed 25 percent of the annual retrieval budget. Agents halt at these gates rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the contract, gate table, partition manifest, and artifact registry in durable state, since a build outlives any single working context.
- Process embedding and index work in bounded batches keyed by compatible fingerprint and input size, preserving per-item identifiers across every batch boundary.
- Write a handoff record naming the sealed generations, the open generation, the replay cursor, the outstanding gates, and the rollback deadline at every context boundary.
- Count agent-side context consumption toward the cost ceiling rather than treating it as free.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract and Admissibility Integrity (After Phase 1)**

- **Automated Check**: Every gate row carries a numeric threshold and a breach consequence; at least 4 baselines are frozen against one snapshot; exactly 1 category is admitted; every refusal names defeating evidence.
- **Agent Action on Pass**: Proceed to corpus construction.
- **Agent Action on Failure**: Halt and return the specific contract defect; no corpus expenditure occurs against an incomplete contract.
- **Human Review Trigger**: Any request for a category-three or category-four referral, or a projected rebuild cost above 25 percent of the annual retrieval budget.

**Checkpoint 2: Corpus Integrity (After Phase 2)**

- **Automated Check**: Every relevant pair carries a resolvable supporting span; partition overlap is 0; every partition carries a content hash; every cohort dimension carries at least 30 queries.
- **Agent Action on Pass**: Proceed to encoder calibration.
- **Agent Action on Failure**: Rebuild the affected partition only, and re-adjudicate the affected judgements.
- **Human Review Trigger**: Sampled inter-adjudicator agreement below 0.70, or synthesised material above 50 percent in any cohort.

**Checkpoint 3: Representation Integrity (After Phase 3)**

- **Automated Check**: Worst cohort sits no more than 10 percentage points below the pooled figure; roles match between build and serving; the fingerprint covers all 13 constituent fields; mixed-fingerprint writes total 0.
- **Agent Action on Pass**: Proceed to index construction.
- **Agent Action on Failure**: Halt; a representation defect corrected after index build requires a full rebuild and is never patched.
- **Human Review Trigger**: A cohort spread above 20 percentage points, or a decision to serve a cohort the encoder fails.

**Checkpoint 4: Approximation Integrity (After Phase 4)**

- **Automated Check**: ANN recall at k at least 0.95; filtered recall at least 0.95 in every band; result shortfall no more than 1 percent; worst-cohort loss per lossy transform no more than 3 percentage points.
- **Agent Action on Pass**: Proceed to lifecycle enforcement.
- **Agent Action on Failure**: Revert the most recently added lossy transform and re-measure, rather than raising search effort to mask the loss.
- **Human Review Trigger**: ANN recall below 0.90, or any selectivity band failing after 2 tuning passes.

**Checkpoint 5: Lifecycle and Compression Integrity (After Phase 5)**

- **Automated Check**: Canonical coverage at least 0.999; exactly 1 generation reachable through the alias; answer preservation at least 95 percent frozen and 90 percent post-freeze; a canonical copy exists for every latent.
- **Agent Action on Pass**: Proceed to assurance verification.
- **Agent Action on Failure**: Return the workload to category one and seal the generation without the latent extension.
- **Human Review Trigger**: Any proposal to retain a latent as the sole surviving artifact for a record.

**Checkpoint 6: Assurance Integrity (After Phase 6)**

- **Automated Check**: Inversion exact recovery no more than 5 percent; membership area under the curve no more than 0.60; cross-tenant negatives return 0 results; residual match count 0 after deletion; no record above 2 percent of top-10 result sets.
- **Agent Action on Pass**: Release the generation for shadow comparison.
- **Agent Action on Failure**: Withhold release and name the failing probe; the assurance veto is not overridable by another component.
- **Human Review Trigger**: Any cross-tenant leak, or any residual match after a completed traversal.

**Checkpoint 7: Promotion Integrity (After Phase 7)**

- **Automated Check**: Shadow window at least 10,000 queries or 7 days; labeled recall regression no more than 2 percentage points; unreplayed tombstones 0; rollback rehearsed; incumbent retained at least 14 days.
- **Agent Action on Pass**: Execute the atomic alias swap and open the rollback window.
- **Agent Action on Failure**: Abort the swap and retain the incumbent; a partially validated generation is never promoted with a warning.
- **Human Review Trigger**: Any unexplained cohort shift above 10 percentage points, or a latency percentile breach above 20 percent of the objective.

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

**Error Type 1: Mixed-Fingerprint Contamination**

- **Symptoms**: Neighborhoods look plausible but relevance collapses for a subset of queries; recall degrades without any index parameter change; two vectors of equal dimension return incoherent distances.
- **Diagnostic Steps**: Recompute the fingerprint for a sample of stored vectors and compare against the generation's declared fingerprint; check whether an encoder alias silently moved to a new revision; check whether a preprocessing or redaction version changed without a generation bump.
- **Resolution Protocol**: Option A, quarantine the contaminated generation, rebuild from the canonical snapshot under a single fingerprint, and replay the delta. Option B, where contamination is confined to an identifiable write window, delete that window's vectors and re-embed only those records. Option C, pin the encoder to an explicit revision rather than an alias and rebuild.
- **Escalation Trigger**: Any non-zero mixed-fingerprint count halts serving from that generation immediately; this class is never resolved by retry, and a second occurrence after pinning escalates the encoder supply arrangement for review.

**Error Type 2: Silent Recall Degradation**

- **Symptoms**: Task success falls while index metrics appear nominal; lexical disagreement rises; neighbor churn against the last baseline window increases without a release.
- **Diagnostic Steps**: Run the continuous exact-search sample and separate the ANN gap from embedding-model error; compare per-cohort score distributions against the baseline window; determine whether corpus composition, source population, or document style changed.
- **Resolution Protocol**: Option A, where the ANN gap widened, restore search effort or rebuild the index and re-measure. Option B, where embedding error grew, relabel a sample and re-run encoder screening on the changed cohort. Option C, where corpus composition changed, reopen the loop at Phase 2 and rebuild the labeled corpus before any tuning.
- **Escalation Trigger**: A labeled recall drop above 5 percentage points against the baseline window escalates within 1 monitoring interval; the alert is never closed by adjusting a global similarity threshold.

**Error Type 3: Filtered-Search Recall Collapse**

- **Symptoms**: Queries carrying a restrictive tenant, date, or access filter return fewer than k results; small tenants report missing records that exact search finds; recall appears healthy in aggregate and fails per tenant.
- **Diagnostic Steps**: Measure eligible set size exactly for the failing filter; compare candidates before and after filtering; determine whether filtering is applied before or after candidate generation.
- **Resolution Protocol**: Option A, enable engine-supported iterative or continued scanning and declare a scan limit. Option B, move the affected tenant or scope to a dedicated partition with its own index. Option C, serve exact search for eligible sets below a declared size, since brute force removes the failure entirely at small scale.
- **Escalation Trigger**: Result shortfall above 1 percent in any band escalates after 2 tuning passes; oversampling alone is never accepted as the resolution for a tenant in the highest sensitivity class.

**Error Type 4: Unciteable or Unsupported Answer**

- **Symptoms**: An answer cannot resolve to a canonical span; a citation points at a passage that does not support the claim; a compressed latent answers a question the canonical source does not confirm.
- **Diagnostic Steps**: Resolve the cited source identifier and version and verify span existence at the recorded offsets; determine whether the latent replaced the evidence or merely addressed it; check whether the canonical copy was retained.
- **Resolution Protocol**: Option A, abstain and return the unsupported marker rather than the answer. Option B, rehydrate the canonical record and re-answer from the explicit source. Option C, disable lossy serving for the affected task class and revert it to category one.
- **Escalation Trigger**: Citation support below 95 percent for any citation-obligated task suspends autonomous answering for that task class; a nearby passage is never promoted into a citation, and this class is never resolved by resampling.

**Error Type 5: Unverifiable Erasure Claim**

- **Symptoms**: A deleted subject returns from a retired generation, a replica, a cache, or a restored backup; a dependency set cannot be resolved for a latent; physical completion time is absent from the deletion record.
- **Diagnostic Steps**: Traverse the derivation graph for the subject and list every store not covered by the completed traversal; execute the verification queries against every retained generation and against a restored backup in isolation.
- **Resolution Protocol**: Option A, extend the traversal to the uncovered stores, re-verify, and record the new completion time. Option B, where a latent's dependency set is unknown, delete the enclosing artifact bundle and rebuild it from retained canonical inputs. Option C, where a backup class cannot be traversed, shorten its expiry and record the residual risk until expiry passes.
- **Escalation Trigger**: Any residual match after a completed traversal escalates immediately and blocks admission of further sensitive data; an erasure claim is never asserted on the basis that the canonical row is gone.

**Error Type 6: Neighborhood Domination and Corpus Poisoning**

- **Symptoms**: A small set of records appears across unrelated queries; a newly ingested source dominates a target neighbourhood; answers shift toward one source without a corpus growth that explains it.
- **Diagnostic Steps**: Compute result-frequency concentration and duplicate cluster membership; trace dominating records to their ingestion path and authentication status; compare against the lexical baseline for the same queries.
- **Resolution Protocol**: Option A, apply per-source caps and duplicate cluster diversification, then re-measure concentration. Option B, quarantine the ingestion path and require authenticated sources before readmission. Option C, where domination is a geometric hubness artifact rather than an injection, apply a versioned hubness reduction transform and revalidate it as a representation change.
- **Escalation Trigger**: A single record above 2 percent of top-10 result sets escalates after 1 unsuccessful mitigation pass; an unauthenticated ingestion path implicated in domination is closed rather than rate-limited.

**Troubleshooting Decision Tree**:

```
RETRIEVAL QUALITY OR SAFETY GATE FAILS
├─ REPRESENTATION DEFECT
│   ├─ Fingerprint mismatch in stored vectors → HALT generation; rebuild under one fingerprint
│   ├─ Encoder alias moved revision → Pin explicit revision; rebuild and replay delta
│   └─ Build and serving roles differ → Invalidate generation; re-embed with documented roles
├─ APPROXIMATION DEFECT
│   ├─ ANN recall below gate → Raise search effort or rebuild; re-measure against exact
│   ├─ Filtered shortfall above 1 percent → Enable iterative scan, partition, or serve exact
│   └─ Stacked lossy transforms → Revert last transform; ablate in isolation
├─ EVIDENCE DEFECT
│   ├─ Span does not resolve → Abstain; return unsupported marker
│   ├─ Latent is sole artifact for cited task → Revert task class to category one
│   └─ Nearest passage offered as citation → Reject answer; escalate task class
├─ PRIVACY AND ERASURE DEFECT
│   ├─ Residual match after traversal → HALT sensitive ingestion; extend traversal; escalate
│   ├─ Inversion or membership above gate → Partition store; raise sensitivity class
│   └─ Raw vector found in telemetry → HALT log release; purge and re-instrument
└─ CORPUS DEFECT
    ├─ Single record dominates results → Apply source caps and diversification; re-measure
    ├─ Unauthenticated ingestion implicated → Close the path; quarantine and re-verify
    └─ Corpus composition changed → Reopen at Phase 2; rebuild labels before tuning
```

### D. Performance Metrics and Continuous Learning

**Retrieval Quality Metrics**:

- **Labeled recall at k**: Adjudicated relevant sources returned in the top k under exact search (target: declared per deployment, with regression against the incumbent no more than 2 percentage points).
- **ANN gap**: Exact top-k neighbors missed by the serving index (target: no more than 5 percentage points; above 10 blocks release).
- **Filtered recall**: Recall inside the exact eligible subset per selectivity band (target: at least 95 percent in every band).
- **Result shortfall rate**: Filtered queries returning fewer than k eligible results (target: no more than 1 percent).
- **Worst-cohort spread**: Gap between pooled and worst cohort recall (target: no more than 10 percentage points).
- **Citation support**: Answers whose cited span resolves and supports the claim (target: at least 95 percent for citation-obligated tasks).

**Integrity and Safety Metrics**:

- **Mixed-fingerprint write count**: Vectors admitted under a foreign fingerprint (target: exactly 0).
- **Canonical resolution rate**: Returned identifiers resolving to an authorized canonical record at the recorded version (target: 100 percent).
- **Inversion exact recovery**: Probe records recovered exactly by an inversion attack (target: no more than 5 percent).
- **Membership inference area under the curve**: Attack discrimination between in-corpus and held-out records (target: no more than 0.60).
- **Hub concentration**: Share of top-10 result sets containing any single record (target: no more than 2 percent).
- **Residual match count after deletion**: Deleted representations still returned by verification queries (target: exactly 0).

**Efficiency and Cost Metrics**:

- **Query latency percentiles**: Reported at the fiftieth, ninety-fifth, and ninety-ninth percentile by corpus size, filter selectivity, top k, generation, and concurrency (target: within the declared objective; a breach above 20 percent triggers rollback).
- **Cost per query**: Embedding, vector read, rerank, database input and output, and generation combined (target: within the declared ceiling).
- **Rebuild capital cost**: Corpus embedding, quantizer training, build and validation, dual storage, replicas, and delta replay (target: within 20 percent of the pilot shard extrapolation).
- **Effective compression**: Original tokens divided by latent tokens where category two is adopted (target: at least 4-fold, reported alongside preservation rather than instead of it).

**Learning and Adaptation Mechanisms**:

- **Evidence-bound thresholds**: Recompute every threshold per corpus and per cohort against observed outcomes; the values stated here are deployment defaults rather than measured constants.
- **Label replenishment**: Adjudicate a continuous sample of production queries so the labeled corpus tracks corpus composition rather than the composition at first build.
- **Generation memory**: Retain per generation the fingerprint, gate values, cost, and observed production behaviour, so encoder and index decisions improve against measured history rather than against benchmark rank.
- **Attack cadence**: Re-run inversion, membership, and poisoning probes after every representation change and at a fixed interval between changes, since a passing result is specific to the configuration that produced it.

**Human-in-the-Loop Boundaries**: Waiving a residual match in an erasure claim, adopting a latent as the sole surviving artifact for a record, admitting a corpus whose inversion or membership results exceed the gates, promoting a generation for a highest-sensitivity tenant, and relaxing the evidence resolution boundary are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the lifecycle of a derived representation rather than the meaning of any particular content. Its phases hold wherever explicit records exist, similarity is a useful address, and a wrong retrieval carries a cost.

### 4.1 Cross-Domain Application Patterns

**Clinical and health records**: The evidence contract classifies most tasks as citation-obligated and irreversible, so category two is refused for anything bearing on a determination. Cohort slices are built by clinical speciality, abbreviation density, and document type, because domain abbreviations and coded identifiers have geometry unlike the encoder's training distribution. The inversion probe set carries short note fragments, since short clinical text is the strongest documented recovery condition, and the personal-data slice drives a quarterly backup restoration test. Filtered recall is measured per care setting, because a restrictive site or consent filter is the normal case rather than the exception.

**Financial regulation and compliance filings**: Exact identifiers, statutory references, and quoted phrases dominate queries, so the admissibility gate returns hybrid retrieval and refuses dense-only serving. Temporal compatibility is a first-class filter, because a superseded rule is semantically near its replacement and materially wrong. Score calibration is fitted per filing type rather than globally, and the retained lexical baseline is the detector that catches an encoder revision quietly degrading identifier matching.

**Industrial maintenance and field engineering**: The corpus mixes procedures, part numbers, sensor logs, and photographs, so modality and language cohorts are measured separately and cross-modal proximity is never used to infer counts, spatial relations, or text visible in an image. Category two is admitted for repeated stable procedural context where the canonical manual is retained, because the compression saving is measurable and the citation obligation is satisfied by rehydration. Disk-backed or partitioned indexes are usual, since corpora exceed memory before they exceed relevance.

**Public-sector records and legal discovery**: Erasure verification is the binding constraint rather than recall, so the deletion graph, the backup class register, and the restoration test carry release authority. Retired generations are retained only for the declared rollback window, because a longer window enlarges the traversal a deletion must cover. Result diversification and per-source caps are mandatory, since a single voluminous producer otherwise dominates neighbourhoods and displaces sparse but decisive material.

**Multilingual commerce and customer support**: Every supported language is evaluated separately, because a multilingual encoder may align high-resource languages well and code-switched or low-resource text poorly. Hub concentration is monitored closely, since generic product and policy text is frequent, short, and geometrically central. Tenant partitioning is applied by merchant, and cross-tenant negative queries run continuously rather than only at release.

### 4.2 Scale, Risk, and Latency Adaptation

- **Small corpora and low-risk work**: Serve exact search and skip approximation tuning entirely, retaining the fingerprint, generation, and deletion discipline. An approximate index adopted below the size at which brute force meets the latency objective adds a failure class for no measured gain.
- **Large corpora under memory pressure**: Adopt the least lossy transform that fits the envelope, ablate each in isolation, and hold the exact reference on a sampled subset rather than abandoning it. Losing the reference removes the only means of attributing a regression to the index.
- **High-risk or irreversible decisions**: Refuse category two outright, mandate citation resolution before every action, partition high-sensitivity tenants physically, and bind the approval gate to every promotion. Abstention is preferred over an unverified completion.
- **Strict latency budgets**: Shorten candidate lists and reranking depth rather than removing the exact-search sample, since the sample is measurement rather than serving cost. Where latency forbids reranking, tighten first-stage recall gates instead of accepting the loss silently.
- **High write volume and short freshness objectives**: Reserve delta capacity before any rebuild, treat re-embedding as recurring capital rather than an exception, and reject any migration whose projected duration exceeds the freshness or deletion objective.
- **Multi-tenant deployments**: Partition by tenant wherever selectivity is high or sensitivity is elevated, prefilter rather than postfilter for the highest class, and keep high-risk tenants out of shared quantizer training unless lawful and recorded.

***

## V. Limitations and Considerations

**Overlap with ordinary vector retrieval**: Much of this framework is indistinguishable from a disciplined retrieval-augmented generation practice, and a reader who already operates encoder selection, hybrid retrieval, and reranking will find those parts familiar. The consequence is a risk of duplicated effort across guides and of readers treating this material as a second retrieval tutorial. The mitigation is the scope boundary in Section 1.2: this guide owns the representation lifecycle, meaning the fingerprint, the immutable generation, the exact-search reference, filtered recall, the migration and rollback contract, and the deletion graph, and it explicitly defers chunking, query construction, prompt assembly, answer generation, retention policy, and symbolic modelling to the companion guides that own them.

**Two of four categories are not executable at this layer**: Learned memory modules and soft prompts require gradient training, an immutable base checkpoint, or hidden-state access, none of which an agent reaches at runtime. The consequence is that a reader seeking those techniques will not find an implementation here. The mitigation is the admissibility gate in Section 1.4, which refuses them explicitly and emits a referral naming the unmet requirement and the assurance obligations a receiving process must discharge, rather than silently omitting the categories or offering instructions an agent cannot execute.

**Most thresholds are deployment defaults rather than measured findings**: The recall, shortfall, preservation, concentration, inversion, and membership figures in this guide were chosen to be operable on first deployment, not derived from a property of embedding spaces. The consequence is that a deployment adopting them unchanged may gate too tightly in one cohort and too loosely in another. The mitigation is the recalibration requirement in Section III.D, which obliges each deployment to recompute every threshold per corpus and per cohort against observed outcomes, and to record the default it replaced.

**Cited attack and compression figures are setting-specific**: The reported inversion recovery rate applies to short inputs against targeted encoders under a stated attacker model, and reported compression ratios were measured on studied prompt tasks whose averages do not identify which details disappeared. The consequence is that treating either figure as a general property will produce a false risk estimate in both directions. The mitigation is Step 6.1 and Step 5.2, which require each deployment to run its own probes with a recorded attacker model and its own preservation tests on post-freeze questions.

**Erasure verification bounds risk rather than eliminating it**: Verification queries, restoration tests, and post-deletion probes establish that a representation does not return under the conditions tested, not that no derivative survives anywhere. The consequence is that an erasure claim is always narrower than the plain meaning of the word. The mitigation is the residual risk statement required in Step 6.3, which records what was traversed, what was tested, and what remains unverified, so the claim is auditable rather than absolute.

**Labeled corpus adjudication is the binding cost**: Every gate in this framework rests on adjudicated relevance, and adjudication is slow, expensive, and requires domain knowledge the deployment may not hold. The consequence is a temptation to substitute model-proposed labels wholesale, which measures the labelling model rather than the retrieval system. The mitigation is the hybrid authority rule in Section 1.3 and the agreement floor in Step 2.1, which permit model proposals while requiring a deterministic adjudication verdict and a sampled agreement measurement behind every label.

**The cost model is an estimate until a shard is measured**: Storage, build, replication, and re-embedding costs depend on engine behaviour, overhead, and distribution effects that list prices do not capture. The consequence is that a migration budgeted from raw vector arithmetic will be understated. The mitigation is Step 7.1, which requires extrapolation from a measured pilot shard of at least 1 percent of eligible records before full-corpus commitment.

**Structural conformance is not retrieval quality**: A generation can clear every checkpoint here and still serve a corpus that answers the wrong questions, because the framework verifies the representation lifecycle rather than the adequacy of the evidence base. The mitigation is the end-to-end task success measurement carried alongside every relevance figure in Phase 3 and Step 7.2, and the acknowledgement that no checkpoint substitutes for human review of whether the corpus contains what the tasks require.

***

## VI. Conclusion and Summary

Latent memory is best understood as a spectrum running from safe, rebuildable addresses over explicit evidence to opaque state that replaces evidence and changes behaviour. The agent layer reaches only the first part of that spectrum, and reaches it fully. An encoder call, an external index, a canonical store, and a routing alias are sufficient to give an agent associative recall over accumulated experience while keeping every retrieved artifact readable, citeable, correctable, and deletable. Nothing further along the spectrum is invocable at runtime, and a guide that pretended otherwise would instruct an agent to perform work it cannot perform.

The discipline that makes the reachable part safe is version control over representations. A vector is meaningful only under one encoder revision, one tokenizer, one input role, one preprocessing pipeline, one dimension, one normalization, and one metric, and the fingerprint that binds those together is what converts an undetectable contamination into a rejected write. An approximate index is a correctness decision rather than a performance tuning exercise, because its error is invisible without an exact reference held alongside it. A latent that replaces its source is a liability priced in lost citations, and it is worth accepting only where measured preservation says so.

A team adopting this framework should build the exact reference and the labeled corpus before building the index. Freeze the baselines, adjudicate the labels, fix the fingerprint, then measure how much recall the serving path gives away and inside which filters it gives away the most. Add compression only after preservation clears its gate, and rehearse the migration and the deletion before either is needed under incident conditions.

**Key Success Factors**:

- **Evidence survives the representation**: A canonical record is retained for every vector and for every latent, so a result can always resolve to something a person can read.
- **One fingerprint per generation**: Vectors from different revisions, roles, pipelines, dimensions, normalizations, or metrics never share an index, and a mismatch is rejected rather than logged.
- **Approximation measured against exactness**: The ANN gap is reported separately from embedding error, inside filter-selectivity bands, and never inferred from aggregate quality.
- **Deterministic authority at every handoff**: Models produce vectors, latents, rankings, and proposals; software decides admissibility, passage, promotion, and erasure.
- **Migration and deletion rehearsed before they are needed**: Dual generations, delta replay, atomic alias swap, rollback, and a verified traversal are exercised in advance rather than improvised.
- **Thresholds recomputed, not inherited**: Every numeric gate is recalibrated per corpus and per cohort, and the default it replaced is recorded.

By following this guide, AI agents can operate embedding-space memory as versioned retrieval infrastructure whose approximation, geometry, and lifecycle are measured rather than assumed, and can refuse the representation categories that lie beyond their reach instead of simulating them.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; except where noted, they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. Five entries were verified directly during conversion and are marked as such. One entry carried by the prose source was omitted rather than reproduced: the source attributed the Differentiable Neural Computer to an arXiv identifier that resolves to a different 2016 memory-augmented network paper, so the citation was removed instead of being corrected on assumption.

**Corpus pointers**:

- `Latent Memory Networks for AI Agents: A Production Guide` — the originating prose guide from which this operational guide was derived. Source of the four-category taxonomy, the representation-geometry cautions, the embedding lifecycle and generation rules, the approximate-nearest-neighbor and filtered-search treatment, the quantization discipline, the bounded-loss compression conditions, the privacy and erasure requirements, the failure-mode inventory, the metadata logging contract, and the thirteen-step operational workflow that this framework reorganises into seven phases.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — the category-level companion covering agent memory as a whole, within which this guide owns only the derived-representation lifecycle.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on compaction and summarisation of explicit records, which owns the minority-detail loss this guide measures only for latent compression.
- `advanced_task_guides/memory-management/guide_AttentionBasedMemoryRetrieval.md` — companion guidance on relevance scoring and serving-state mechanics, which owns the material this guide deliberately excludes.
- `advanced_task_guides/memory-management/guide_MemoryForgetting.md` — owns retention policy, the separation of utility forgetting from obligation erasure, and the coverage proof a case requires. This guide owns the representation-side obligation only: the deletion dependencies registered in Step 5.3 and the erasure verification across generations, replicas, and backups in Step 6.3.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — owns the operation contract for a single read and a single write against a durable store, including gate ordering and terminal states; applicable to the alias cutover in Step 7.2, where a read must be served from exactly one committed generation.
- `advanced_task_guides/memory-management/guide_HierarchicalMemory.md` — owns tier declaration, promotion and demotion, and the choice between eviction and summarisation as reclamation modes; applicable wherever bounded latent compression under Step 5.2 is being weighed against simply demoting a record to a cheaper tier.
- `advanced_task_guides/memory-management/guide_UnstructuredMemory.md` — owns free-form bodies, chunking, and the governed metadata envelope over which these representations are computed; this guide owns the encoder, the index, and the generation lifecycle rather than the content being encoded.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the telemetry contract in Step 7.3.
- `advanced_task_guides/design-architecture/guide_SchemaFlexibilityandEvolution.md` — companion guidance on versioned schema change, applicable to generation immutability and migration in Phase 5 and Phase 7.
- `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guidance on monitoring under constraint, applicable to the drift and concentration monitoring in Step 7.3.
- `advanced_task_guides/policy-risk/guide_InformationDependencyDisclosureRiskAnalysis.md` — companion guidance on disclosure exposure, applicable to the inversion, membership, and isolation testing in Phase 6.
- `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md` — companion guidance on provenance and evidence lineage, applicable to the canonical lineage and deletion graph in Phase 5.
- `advanced_task_guides/knowledge-graphs/guide_KG_EntityResolutionDedup.md` — companion guidance on duplicate detection, applicable to the duplicate cluster caps and hubness controls in Step 6.2.

**External references**: The numbering below is the numbering used by the inline markers in Sections I and II. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim.

*Retrieval embeddings and latent compression*

1. *Dense Passage Retrieval for Open-Domain Question Answering* — https://arxiv.org/abs/2004.04906
2. *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* — https://arxiv.org/abs/2005.11401
3. *Learning to Compress Prompts with Gist Tokens* — https://arxiv.org/abs/2304.08467
4. *Adapting Language Models to Compress Contexts* — https://arxiv.org/abs/2305.14788

*Learned memory modules, recurrent states, and soft prompts*

5. *Neural Turing Machines* — https://arxiv.org/abs/1410.5401
6. *Memory Networks* — https://arxiv.org/abs/1410.3916
7. *End-to-End Memory Networks* — https://arxiv.org/abs/1503.08895
8. *Generalization through Memorization: Nearest Neighbor Language Models* — https://openreview.net/forum?id=HklBjCEKvH
9. *Memorizing Transformers* — https://arxiv.org/abs/2203.08913
10. *Leave No Context Behind: Efficient Infinite Context Transformers with Infini-attention* — https://arxiv.org/abs/2404.07143
11. *Titans: Learning to Memorize at Test Time* — https://arxiv.org/abs/2501.00663
12. *Memory Layers at Scale* — https://arxiv.org/abs/2412.09764
13. *Mamba: Linear-Time Sequence Modeling with Selective State Spaces* — https://arxiv.org/abs/2312.00752
14. *The Power of Scale for Parameter-Efficient Prompt Tuning* — https://arxiv.org/abs/2104.08691
15. *Prefix-Tuning: Optimizing Continuous Prompts for Generation* — https://arxiv.org/abs/2101.00190

*Recent surveys and multi-agent latent memory*

16. *Memory-Augmented Transformers: A Systematic Review from Neuroscience Principles to Enhanced Model Architectures* — https://arxiv.org/abs/2508.10824 (verified during conversion; the full title is reproduced here in place of the short form the prose source used)
17. *LatentMem: Customizing Latent Memory for Multi-Agent Systems* — https://arxiv.org/abs/2602.03036 (verified during conversion; the full title is reproduced here in place of the short form the prose source used)

*Embedding geometry, benchmarking, and dimension control*

18. OpenAI, *Embeddings guide* — https://developers.openai.com/api/docs/guides/embeddings (verified during conversion; the page documents unit-length normalization and the dimension-shortening parameter)
19. *MTEB: Massive Text Embedding Benchmark* — https://arxiv.org/abs/2210.07316
20. *BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models* — https://arxiv.org/abs/2104.08663
21. *Matryoshka Representation Learning* — https://arxiv.org/abs/2205.13147

*Approximate nearest-neighbor indexing and filtered search*

22. pgvector, *Open-source vector similarity search for Postgres* — https://github.com/pgvector/pgvector (verified during conversion; documents the search candidate-list default and the iterative scan behaviour relied on in Step 4.2)
23. Faiss, *Faiss indexes* — https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
24. *Accelerating Large-Scale Inference with Anisotropic Vector Quantization* — https://arxiv.org/abs/2007.01401
25. *DiskANN: Fast Accurate Billion-point Nearest Neighbor Search on a Single Node* — https://proceedings.neurips.cc/paper/2019/hash/09853c7fb1d3f8ee67a61b6bf4a7f8e6-Abstract.html
26. Weaviate, *Vector index configuration reference* — https://docs.weaviate.io/weaviate/config-refs/indexing/vector-index
27. *Filtered Approximate Nearest Neighbor Search in Vector Databases: System Design and Performance Analysis* — https://arxiv.org/abs/2602.11443 (retrieved during conversion research rather than transcribed from the prose source)

*Privacy, inversion, and retrieval-corpus poisoning*

28. *Text Embeddings Reveal (Almost) As Much As Text* — https://arxiv.org/abs/2310.06816 (verified during conversion)
29. European Data Protection Board, *Opinion on AI models and GDPR principles* — https://www.edpb.europa.eu/news/edpb-opinion-on-ai-models-gdpr-principles-support-responsible-ai_en
30. *PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models* — https://arxiv.org/abs/2402.07867

*Serving, adaptation tooling, registry, and instrumentation*

31. SentenceTransformers, *Documentation* — https://sbert.net/
32. Hugging Face, *Text Embeddings Inference* — https://huggingface.co/docs/text-embeddings-inference/index
33. Hugging Face, *PEFT* — https://huggingface.co/docs/peft/index
34. MLflow, *Model Registry* — https://mlflow.org/docs/latest/ml/model-registry/
35. OpenTelemetry, *Documentation* — https://opentelemetry.io/docs/

