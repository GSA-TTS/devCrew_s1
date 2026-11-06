# Latent Knowledge Retrieval

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Latent knowledge retrieval constitutes the task family of deciding which knowledge source may answer a given factual claim, and of operating that decision when one of the candidate sources is the model itself rather than a record that can be cited. The label is overloaded across seven distinct senses, and treating it as a single architecture is the primary production failure it produces. This guide provides AI agents with a structured protocol for the agent-layer subset: semantic retrieval whose returned artifact remains inspectable, generated identifiers resolved against a canonical store, reusable context caches revalidated before every hit, and calibrated parametric answering under an explicit non-citability marking. Senses that read activations, train probes or sparse autoencoders, edit weights, or run recurrence in hidden state require access no agent holds at runtime; they enter only through an admissibility gate that refuses them and emits a referral. The framework specifies a knowledge source contract, hard routing rules applied before any estimate, class-fitted thresholds validated on an untouched holdout, a fixed authority order for parametric-versus-retrieved conflicts, staleness and memorization exposure testing, and an execution tier partition in which deterministic software holds authority over every gate verdict.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Latent knowledge retrieval**: The family label covering any method in which knowledge is located, represented, or produced through a learned continuous representation rather than through a literal lexical match against stored text. The label names a family and never a sufficient architecture description. A design document that states only this label has specified nothing that can be built or verified.

**Sense**: One of the seven mutually distinguishable methods the family label covers, each with a different artifact, a different assurance burden, and a different execution layer. Exactly one primary sense governs a deployment; additional senses are secondary and carry separate artifact identifiers, metrics, authorization, and failure decisions.

**Parametric knowledge**: Knowledge absorbed into base-model weights during training and produced without any external record present in the request. It is fast, free of retrieval latency, and structurally non-attributable: no agent-layer operation maps a generated fact back to the training record that produced it.

**Attributable evidence**: Content held in an external record that carries a source identifier, a version, a timestamp, and an exact span, and that survives after the answer is produced. A citation is a pointer into attributable evidence and cannot point at anything else.

**Canonical record**: The immutable, versioned explicit artifact that attributable evidence resolves to, addressed by source identifier, version identifier, and content hash. This guide adopts the term as used across the corpus.

**Knowledge source contract**: The declared statement of which sources may answer which claim classes, fixed before any request is served. It extends the evidence contract named in companion guides with the source-eligibility fields this method requires: permitted routes, citation obligation per claim class, declared knowledge cutoff, volatility ceilings, abstention policy, and the consequence class above which parametric answering is prohibited outright.

**Route**: The selected answering path for one claim, drawn from a closed vocabulary of `parametric`, `retrieved`, `hybrid`, `generative_index`, `cache`, and `abstain`. A route is a deterministic assignment, never a model preference.

**Hybrid route**: The path in which parametric knowledge formulates or interprets the query while the answer is produced from retrieved evidence. Parametric content on a hybrid route is an instrument and never a source.

**Declared cutoff**: The knowledge cutoff a model provider publishes for a pinned model revision. It is metadata rather than a guarantee, and it is recorded as `unknown` where no provider statement exists.

**Effective cutoff**: The date beyond which a model's recall for a specific topic, resource, or subdomain degrades in measurement, which may fall earlier or later than the declared cutoff [1]. Volatility classes are set against measured effective cutoffs where measurement exists and against the declared cutoff otherwise.

**Cutoff exposure**: The property of a claim whose correct answer may have changed after the declared or effective cutoff. Cutoff exposure is a hard routing input and is evaluated before any confidence estimate.

**Volatility class**: The declared rate at which the correct answer to a claim class changes, expressed as a maximum acceptable answer age in days. It is a property of the claim, not of the model.

**Citation availability**: A boolean recorded per claim, true only where an external span in a canonical record supports the claim at a recorded version and offset. A parametric claim carries `citation_availability=false` unconditionally, and no self-generated bibliography changes that value.

**Generated identifier**: A document identifier a model emits rather than retrieves, produced by a learned index that stores the retrieval mapping in parameters. It is a pointer and never evidence; an unresolved, unauthorized, retired, or collided identifier is discarded rather than repaired.

**Reusable context cache**: Preloaded serving state, prefix reuse, or a provider cache-control artifact that lets a bounded authorized corpus be consumed repeatedly without re-retrieval. A cache is defined by its key fingerprint and is invalid the moment any fingerprint component changes.

**Cache key fingerprint**: A hash over model identifier, model revision, tokenizer version, prompt or context version, source content hashes, policy version, tenant or authorization fingerprint, cache format version, and invalidation epoch. Two requests may share a cache entry only where their fingerprints are byte-identical.

**Knowledge conflict**: A disagreement between the parametric answer and retrieved evidence, between two retrieved sources, or between a cached artifact and its current canonical record [2]. Conflicts are adjudicated by a declared authority order and are never resolved by whichever answer the model states more fluently.

**Apparent conflict**: A disagreement that dissolves under normalization of entity identity, effective date, jurisdiction, unit, negation, source version, or question interpretation. Apparent conflicts are separated from real conflicts before any authority order is applied, because adjudicating an apparent conflict discards a correct claim.

**Evidence gain**: The measured increase in answerable content produced by one additional attempt, counted as a new verified atomic fact, a newly supported claim, a resolved conflict, or a narrowed calibrated interval. Restated prose, a higher self-reported confidence, and a repeated generation are zero gain, and a loop iteration returning zero gain terminates the loop.

**Selective risk**: The error rate measured over answered requests only, reported jointly with coverage. Accuracy reported without coverage is not interpretable for this method, because an abstention path can raise accuracy arbitrarily by answering less.

**Abstention gate**: The deterministic rule that converts a route to `abstain` where no eligible source meets its class threshold. The gate holds authority over any model assertion that an answer is good enough.

**Admissibility gate**: The bounded pre-execution decision that returns exactly one admitted sense or a refusal with a referral. This guide adopts the term and the refusal-plus-referral pattern from the corpus.

**Referral**: The structured record emitted when a requested sense is refused at this layer, naming the unmet requirement, the agent-layer substitutes already measured and excluded, and the assurance obligations the receiving process must discharge.

### 1.2 The Seven Senses and the Agent-Layer Boundary

The family label covers seven senses that differ in what the latent object is, in whether the returned knowledge survives as an inspectable artifact, and in what access the method requires. Conflating them is the failure mode this section exists to prevent, because each sense carries a different erasure path, a different provenance claim, and a different verification burden.

**Sense one, semantic external retrieval**: A query, document, or concept is represented in a learned continuous space, and the returned knowledge remains external text or another inspectable artifact. The latent object is an index key. This is the default sense and the default production answer.

**Sense two, compressed runtime state**: Knowledge is represented as reusable serving state or condensed representations rather than as readable source text. The agent-layer portion is a provider-exposed context cache or preloaded bounded corpus. The remainder, covering learned soft tokens, activation compression, memory layers, and cross-agent hidden-state transfer, is not agent-layer.

**Sense three, generative retrieval over a learned index**: A model emits document identifiers directly, storing the retrieval mapping in parameters rather than in an external index. The agent-layer portion is constrained decoding over a valid-identifier registry followed by resolution against a canonical store. Training the index is not agent-layer.

**Sense four, parametric knowledge**: The model answers from weights with no external record in the request. This is agent-layer in full, because prompting is the entire mechanism, and it is the sense that carries the heaviest assurance burden precisely because it is the easiest to invoke.

**Sense five, model-internal probing and elicitation of latent knowledge**: An analyst reads activations, logits, or learned features to estimate what a model internally represents, including where the model's stated output is untrusted. This requires residual-stream and layer hooks, probe training, and sparse-autoencoder tooling.

**Sense six, knowledge editing and injection into weights**: Facts or behaviours are added, replaced, or specialised through direct weight edits, adapters, or continued training. This requires a controlled base checkpoint and a training pipeline.

**Sense seven, latent reasoning and implicit search**: Intermediate computation is carried in continuous hidden states rather than in decoded tokens. This requires a model architected or trained for latent recurrence.

**Sense Properties and Execution Layer**:

| Sense | Latent object | Returned knowledge survives | Agent-layer executable | Citable |
| :-- | :-- | :-- | :-- | :-- |
| One: semantic external retrieval | Query and document vectors | Yes, the source record is returned | Yes, through an encoder endpoint and an external index | Yes, through the resolved record |
| Two: compressed runtime state | Serving state or condensed representation | Only where the canonical source is retained | Partly, provider cache controls only | Only through the retained canonical source |
| Three: generative retrieval | A decoded identifier | Yes, after resolution against a canonical store | Partly, decode and resolve only | Yes, through the resolved record |
| Four: parametric knowledge | Model weights | No | Yes, prompting is the whole mechanism | No, unconditionally |
| Five: internal probing and elicitation | Activations and learned features | No, a score is not a record | No, requires hooks and probe training | No |
| Six: knowledge editing | Edited parameters or adapters | No | No, requires a training pipeline | No |
| Seven: latent reasoning | Hidden-state recurrence | No | No, requires a trained architecture | No |

**The re-scoping this guide applies**: Senses five, six, and seven, and the learned portion of sense two, are not reachable through prompting, tool calls, HTTP APIs, command-line invocation, file operations, sub-agent orchestration, external data stores, or any inference parameter a model API exposes. Their mechanisms are layer and residual-stream reads, gradient updates to weights or memory slots, and continuous vectors injected at layer boundaries. Instructing an agent to build one would be instructing it to do something it cannot do. This guide therefore treats them as gated selections rather than executable procedures: Section 1.4 states the refusal conditions, Step 1.2 records the verdict and its justification, and a request for one of them terminates this framework and hands the work to a model-engineering process the guide does not carry.

**Why the source-routing surrogate is the executable form**: The property a practitioner wants from latent knowledge is an answer that does not require a literal lexical match and does not always require a retrieval round trip. The agent-layer form supplies that property using components an agent can invoke: an encoder call and an index answer conceptual queries, a pinned model answers stable low-consequence claims from weights, a decoded identifier resolves to a record, and a cache serves a bounded corpus without re-retrieval. What is lost relative to the model-internal senses is any ability to inspect why the model believes a claim. The compensation is that every route in this guide either produces a citable record or is explicitly marked non-citable and held to a calibrated eligibility threshold, so an unattributable answer is never mistaken for a supported one.

**Naming discipline**: A system built to this guide performs calibrated knowledge source routing over inspectable artifacts. It must not be described as retrieving knowledge from model internals, as probing what the model knows, or as eliciting latent knowledge, because none of those operations occurs. Dense retrieval is not model-internal knowledge, self-consistency across samples is not introspection, and a confident closed-book answer is not evidence.

### 1.3 Execution Tier Partition and Authority Boundaries

Every unit of work in this framework belongs to exactly one execution tier. The partition is load-bearing rather than descriptive, because the recurring production failure in this method is a model-tier confidence signal accepted where a deterministic source-eligibility verdict was required.

**Deterministic tier**: Software, queries, schema validators, policy code, and APIs own everything requiring exactness, reproducibility, auditability, or a scale that inference cannot supply. This tier owns the knowledge source contract and its budget ledger, hard routing rules, claim-class assignment from declared metadata, cutoff and volatility arithmetic, threshold comparison, cache key fingerprint computation and validation, identifier validity and authorization checks, citation resolution against the canonical store, evidence-gain arithmetic, the abstention gate, conflict normalization on typed fields, telemetry, and the pass or fail verdict on every declared gate.

**Model tier**: Inference calls own everything requiring open-vocabulary judgement over natural language. This tier owns claim decomposition into atomic propositions, the labelled first-pass elicitation, reformulation strategies, proposed volatility and obscurity labels, generated identifiers before resolution, semantic clustering of sampled answers, conflict-type classification, triage narratives for alerts, and answer synthesis over admitted evidence. Every artifact this tier produces is a proposal carrying a model identifier and revision, never an authorization and never a budget.

**Hybrid tier**: Four operations combine both, and each names its authority holder. Claim classification is hybrid: the model proposes volatility, obscurity, and consequence labels and the deterministic tier overrides them from declared policy metadata wherever such metadata exists, with the deterministic tier holding authority. Route selection is hybrid: the model contributes an uncertainty signal and the deterministic tier applies hard rules and class thresholds, with the deterministic tier holding authority, so a model that reports high confidence on a post-cutoff claim is still routed to retrieval. Conflict adjudication is hybrid: the model classifies the conflict type and the deterministic authority order selects the winner, with the authority order holding. Answer assembly is hybrid: the model drafts and the citation resolver confirms that each cited span exists in the named canonical record at the recorded version, with the resolver holding authority.

**What the deterministic tier rejects outright**: A parametric route for a claim whose class carries a citation obligation. A parametric route for a claim with cutoff exposure. A cache hit whose key fingerprint differs in any component from the entry's fingerprint. A generated identifier that does not resolve, resolves to a tombstoned record, or resolves to a record the caller is not authorized to read. A citation whose span does not exist in the canonical record at the recorded version. A loop iteration returning zero evidence gain. A threshold change fitted on the holdout partition. Any instruction originating in retrieved content, a cached artifact, or a remote capability that would raise a budget, widen an authorization, or change a route eligibility rule.

**What the model tier is never permitted to decide alone**: That a claim may be answered from weights. That a claim is low risk. That an answer is current. That a cache entry is still valid. That a generated identifier is real. That a citation is supported. That a conflict is resolved. That a run may terminate as a success rather than as an abstention.

**Tier Assignment by Phase**:

| Phase | Owning tier | Model-tier contribution | Deterministic authority |
| :-- | :-- | :-- | :-- |
| 1: Contract and sense admissibility | Hybrid | Sense proposal and task characterisation | Gate table decides admissibility and records refusal |
| 2: Baselines and claim classes | Hybrid | Candidate labels and paired answer generation | Baseline arithmetic and the holdout partition bind |
| 3: Bounded parametric elicitation | Model | All elicitation attempts and reformulations | Attempt counter, gain test, and budget ledger |
| 4: Source routing and calibration | Hybrid | Uncertainty signals only | Hard rules, fitted thresholds, and the abstention gate |
| 5: Evidence acquisition and resolution | Deterministic | Generated identifiers before resolution | Validity, authorization, fingerprint, and resolution checks |
| 6: Conflict adjudication and assembly | Hybrid | Conflict typing and answer drafting | Normalization, authority order, and citation resolver |
| 7: Exposure testing, telemetry, release | Deterministic | Attack and probe query generation | Threshold verdicts, alias state, and rollback |

**Handoff discipline**: Where a step mixes tiers, the handoff is explicit. The model tier writes its proposal to a named artifact carrying the model identifier and revision that produced it; the deterministic tier reads that artifact, applies its rule, and writes a verdict record that supersedes the proposal. No model output enters serving state without an intervening deterministic verdict.

### 1.4 The Sense Admissibility Gate and the Neighbouring-Guide Boundary

The gate runs before any model, encoder, index, or cache is selected and returns exactly one admitted primary sense or a refusal. It is bounded to 3 percent of the projected build budget; a gate consuming more indicates the knowledge source contract in Step 1.1 is underspecified and the run halts pending contract completion.

**Sense one is admitted by default** wherever external records exist, may be retained, and can be returned to the caller. A deployment unable to state why it is not using sense one has already chosen wrongly. Where the request is ambiguous and supplies insufficient information to choose, the gate assigns sense one, records the ambiguity, and does not infer access to model internals.

**Sense four is admitted only where all five conditions hold**: the claim class carries no citation obligation; the claim class has no cutoff exposure under the declared or measured effective cutoff; the consequence class sits at or below the contract's parametric ceiling; a class-specific calibrated threshold has been fitted on development data and validated on an untouched holdout; and an abstention path exists and is reachable at serving time. Failing any condition returns sense one for that claim class.

**Sense three is admitted only where all four conditions hold**: a valid-identifier registry exists and is versioned; decoding is constrained to that registry; every decoded identifier is resolved against a canonical store before the answer is assembled; and the configuration has been benchmarked against lexical, dense, and hybrid retrieval at the target corpus scale. Reported results on small corpora do not transfer, and scaling to millions of passages remains unresolved in the published record [3].

**The agent-layer portion of sense two is admitted only where all four conditions hold**: the authorized corpus is bounded, stable, and small enough to preload within the model's context limit after reserving output and system tokens; repeated-prefix cost is measured rather than assumed; the cache key fingerprint is computed and enforced on every hit; and the canonical source is retained so that citation remains possible. The learned portion of sense two is refused on the same terms as senses five through seven.

**Senses five, six, and seven are refused at this layer** in all cases, and each refusal is recorded with the requirement that motivated the request. Where external retrieval, hybrid lexical search, explicit instructions, deterministic tooling, and a larger bounded context have all been measured against the requirement and all fail it, the gate emits a referral naming the unmet requirement, the baselines already excluded, and the assurance obligations the receiving process must discharge: for sense five, probe transfer across topics, prompts, languages, layers, and model revisions, adversarial and deception robustness, causal-intervention validity, and false-assurance rate; for sense six, edit locality, paraphrase and multi-hop generalisation, ripple effects on related facts, unrelated-capability regression, cumulative-edit interference, rollback, and verified deletion; for sense seven, separation of reasoning efficiency from evidence acquisition, and deterministic verification of every factual premise and calculation the latent path produces.

**Substitutes returned on refusal**: Where auditing what a model represents is the actual requirement, the gate returns behavioural evaluation over inputs and outputs, which is inspectable, reproducible, and portable across providers. Where changing a fact the model states is the requirement, the gate returns an external record correction plus mandatory retrieval for that claim class, which is transparent, reversible, and verifiable without a training run. Where reasoning efficiency is the requirement, the gate returns bounded decomposition and deterministic tool use.

**Sense Admissibility Decision Table**:

| Observable condition | Evidence obligation | Gate verdict |
| :-- | :-- | :-- |
| External records exist and may be returned | Citation required or permitted | Admit sense one |
| Claim class is stable, low consequence, and citation-free | Class threshold fitted and holdout-validated | Admit sense four for that class only |
| Bounded stable corpus reused across requests | Repeated-prefix cost measured and fingerprint enforced | Admit sense two, agent-layer portion, under the Step 5.3 gate |
| Constrained corpus with a versioned identifier registry | Benchmarked against lexical, dense, and hybrid at target scale | Admit sense three under the Step 5.2 gate |
| Medical, legal, financial, safety, identity, eligibility, or compliance decision | Any | Refuse sense four; require attributable evidence and human review |
| Activation reads, probes, or feature analysis claimed necessary | All 5 counterfactual baselines measured and failing | Refuse; emit a sense-five referral |
| Weight edits or adapters claimed necessary | External correction measured as insufficient | Refuse; emit a sense-six referral and adopt external correction |
| Latent recurrence claimed necessary | Reasoning efficiency separated from evidence acquisition | Refuse; emit a sense-seven referral |
| Required auditability exceeds the sense's capability | Any | Refuse the design and halt |

**Numeric gate rules**: Admit a sense only where at least 2 counterfactual baselines have been measured on the target corpus. Where fewer than 2 distinct source configurations have been evaluated, the gate returns refusal and the run halts, because no comparison exists. Where the projected parametric route share exceeds 40 percent of consequential requests, the gate escalates for human authorisation rather than proceeding. Where more than 1 primary sense is proposed, the gate returns refusal until the requester designates one primary and declares the rest secondary with separate artifact identifiers.

**Boundary against companion guides**: Retrieval architecture selection, index construction, hybrid fusion, reranking, chunking, and provenance mechanics belong to the advanced knowledge retrieval guide; this guide supplies the admission rule for that ladder's no-retrieval rung and does not restate the rungs above it. Query abstraction, hypothetical document generation, step-back formulation, and decomposition belong to the query transformation guide; those outputs are retrieval instruments and never evidence, and this guide consumes that rule without restating the catalogue. The per-segment retrieval-need, relevance, support, and utility verdicts inside a generation loop belong to the self-reflective retrieval guide; this guide governs which source may hold authority for a claim and consumes that guide's support verdict as an input. Grading and repairing low-quality retrieved evidence belongs to the corrective retrieval guide. Embedding representation, fingerprinting, index generations, migration, and erasure verification belong to the latent memory networks guide in the memory-management category. The distinctive subject retained here is source eligibility: which knowledge source may answer a claim, on what calibrated evidence, and under what non-citability marking.

***

## II. Operational Framework: Calibrated Source Routing Between Parametric Recall and Attributable Evidence

The framework assumes the admissibility gate in Section 1.4 has returned sense one, sense one with a bounded sense-four extension for named claim classes, or sense one with a sense-two or sense-three extension. Phases 1 through 4 fix the contract, the baselines, and the routing thresholds; Phases 5 and 6 execute one request; Phase 7 tests exposure, operates telemetry, and stages release, returning control to Phase 2 whenever the model revision, the declared cutoff, the corpus composition, the policy metadata, the volatility classes, or the threat evidence changes. Each phase declares its owning execution tier, and no phase advances while a mandatory gate from its predecessor is unmet.

### Phase 1: Knowledge Source Contract and Sense Admissibility

**Objective**: Fix which sources may answer which claim classes, and record exactly one admitted primary sense with its justification, before any model, index, or cache is selected.

#### Step 1.1: Establish the Knowledge Source Contract

**Required Actions**:

- Enumerate the supported task types and, for each, the claim classes the answers will contain.
- Declare per claim class the citation obligation as mandatory, permitted, or not applicable, and the consequence class on a 4-point scale from informational through advisory and operational to consequential.
- Declare the parametric ceiling as the highest consequence class at which a `parametric` route may be selected, defaulting to advisory.
- Declare the volatility class per claim class as a maximum acceptable answer age in days, and declare the abstention policy, the latency objective, the cost ceiling per answered request, and the tenant and jurisdiction boundaries.
- Declare the permitted route vocabulary for the deployment as a subset of the closed route list, and record any route the contract excludes with the reason.

**Required Outputs**:

- A versioned knowledge source contract carrying one row per claim class with citation obligation, consequence class, volatility ceiling, and permitted routes.
- A declared parametric ceiling with its escalation owner.
- A budget ledger specification with per-request attempt, sample, token, latency, and cost limits held outside the model.

**Quality Checkpoints**:

- Every supported task type maps to at least 1 claim class, and every claim class carries all 4 declared fields.
- The parametric ceiling is stated as a consequence class rather than as a confidence value.
- No claim class carries a mandatory citation obligation and a permitted `parametric` route simultaneously.
- The budget ledger is enforceable by software with no model call required to read it.

***

#### Step 1.2: Resolve the Sense and Record the Admissibility Verdict

**Required Actions**:

- Run the admissibility gate in Section 1.4 against the contract, spending no more than 3 percent of the projected build budget.
- Assign exactly one primary sense and zero or more secondary senses, each with its own artifact identifier, metric set, authorization scope, and failure decision.
- Record a refusal and emit a referral for every requested sense the gate declines, naming the unmet requirement, the counterfactual baselines already measured, and the assurance obligations the receiving process inherits.
- Default to sense one and record the ambiguity where the request supplies insufficient information to choose, and infer no access to model internals.

**Required Outputs**:

- An admissibility verdict record naming the admitted primary sense, the secondary senses, and the justification for each.
- A referral record for every refused sense, or an explicit statement that none was requested.
- A counterfactual baseline inventory listing at least 2 measured source configurations.

**Quality Checkpoints**:

- Exactly 1 primary sense is recorded, and every secondary sense carries a distinct artifact identifier.
- Every refusal carries a referral, and no referral is emitted without a named unmet requirement.
- No admitted sense requires activation access, probe training, or weight modification.
- At least 2 counterfactual baselines are measured, and the gate consumed no more than 3 percent of the build budget.

***

#### Step 1.3: Pin Model Identity, Cutoff, and Route Vocabulary

**Required Actions**:

- Pin the model endpoint by identifier, revision or weights hash, tokenizer version, provider, and decoding settings, and record the provider-declared knowledge cutoff or `unknown` where none is published.
- Record the prompt version, the sampling parameters, and whether sequence or token log probabilities are exposed by the interface, marking uncertainty as unavailable where they are not.
- Bind the route vocabulary to the contract, disabling any route whose infrastructure dependency is classified as unavailable rather than degrading silently.
- Classify each infrastructure dependency as available, provisionable, requires approval, or unavailable, and record the selected serving tier.

**Required Outputs**:

- A pinned model manifest carrying identifier, revision, tokenizer, cutoff, prompt version, and decoding settings.
- A route eligibility record naming each disabled route and its blocking dependency.
- An infrastructure dependency classification with the selected serving tier.

**Quality Checkpoints**:

- The declared cutoff is recorded as a date or as `unknown`, and it is never inferred from a model release date.
- Every disabled route names its blocking dependency, and no disabled route is silently substituted at serving time.
- Uncertainty availability is recorded as a fact about the interface rather than assumed.
- No dependency remains unclassified.

***

### Phase 2: Paired Baselines and Claim Class Construction

**Objective**: Build the labelled corpus and the frozen baselines against which every later routing threshold is fitted and judged, so that route selection is decided by measurement rather than by preference.

#### Step 2.1: Build the Paired Closed-Book and Open-Book Evaluation Corpus

**Required Actions**:

- Assemble evaluation cases carrying a case identifier, the question, the atomic answers, acceptable answer variants, the authoritative source and its date, the volatility class, the consequence class, the citation requirement, and the correct abstention label.
- Run every case under all 3 conditions: closed-book with abstention enabled, open-book against the authorized corpus, and hybrid.
- Populate named slices covering post-cutoff events, stale sources, contradictory sources, counterfactual context, ambiguous questions, unanswerable questions, private-data questions, paraphrases, adversarial rephrasings, and low-frequency entities.
- Set a minimum of 60 cases per claim class and a minimum of 30 cases per named slice, and record the actual counts where a class or slice falls short.

**Required Outputs**:

- A versioned paired evaluation corpus with all 3 conditions populated per case.
- A slice inventory with per-slice case counts and the shortfall record.
- An abstention label per case stating whether abstention is the correct outcome.

**Quality Checkpoints**:

- Every case carries an authoritative source with a date, and no case is labelled from model output alone.
- All 3 conditions are populated for every case, so paired per-case deltas are computable.
- Every named slice carries at least 30 cases or an explicit shortfall record naming the consequence for threshold confidence.
- No case appears in more than 1 partition.

***

#### Step 2.2: Freeze the Counterfactual Baselines

**Required Actions**:

- Measure and freeze the never-retrieve baseline, the always-retrieve baseline, and the incumbent production configuration on the same corpus and the same pinned model manifest.
- Record for each baseline the accuracy, the selective accuracy at the contract's target coverage, the citation availability rate, the p50 and p95 latency, and the cost per correct non-abstained answer.
- Compute the paired per-case difference between open-book and closed-book accuracy per claim class, and record the classes where the difference is at or below 2 percentage points.
- Declare a baseline freeze, after which no baseline is recomputed except through a full Phase 2 re-entry recorded in the change log.

**Required Outputs**:

- A frozen baseline record carrying all 3 configurations with the full metric set per claim class.
- A per-class paired accuracy delta table naming the classes where retrieval adds no measured accuracy.
- A baseline freeze declaration with a timestamp and the model manifest it binds to.

**Quality Checkpoints**:

- All 3 baselines run on the identical corpus, model manifest, and prompt version.
- Every accuracy figure is reported jointly with coverage, and no accuracy stands alone.
- The paired delta is computed per case rather than as a difference of aggregate means.
- The freeze declaration names the exact model revision, so a revision change invalidates the baselines automatically.

***

#### Step 2.3: Partition Claim Classes and Reserve the Holdout

**Required Actions**:

- Assign every case to exactly one claim class using the contract's declared fields, overriding any model-proposed label wherever declared policy metadata exists.
- Partition each class into development, holdout, and attack sets in a 60 percent, 25 percent, and 15 percent split, stratified by slice membership.
- Seal the holdout partition against all threshold fitting, and record the seal so that any fit touching it is detectable.
- Record for each class the measured effective cutoff where topic-level probing is feasible, and fall back to the declared cutoff with an explicit note where it is not [1].

**Required Outputs**:

- A claim class assignment with the override provenance recorded per case.
- A three-way partition per class with stratification counts.
- A sealed holdout manifest carrying a content hash.
- A per-class cutoff record naming whether the value is measured or declared.

**Quality Checkpoints**:

- Every case carries exactly 1 claim class, and every model-proposed label that policy metadata contradicted is recorded as overridden.
- The holdout partition holds at least 25 percent of each class and is hashed.
- Stratification preserves slice proportions within 5 percentage points across partitions.
- No cutoff value is recorded as measured without the probing evidence that produced it.

***

### Phase 3: Bounded Parametric Elicitation

**Objective**: Extract whatever the pinned model can state about a claim within a hard attempt budget, producing labelled propositions and an uncertainty signal, without any assertion that the process inspects the model.

#### Step 3.1: Run the Labelled First-Pass Elicitation

**Required Actions**:

- Decompose the request into atomic material claims, each independently checkable and each carrying its claim class.
- Issue one first-pass call requesting a concise answer in which every proposition is labelled `known`, `inferred`, or `unknown`, with abstention explicitly permitted.
- Record the response hash, the extracted propositions with their labels, the self-reported confidence, and the log-probability summary where the interface exposes one.
- Charge the attempt against the budget ledger before the result is read, so a budget breach halts the loop regardless of the result.

**Required Outputs**:

- An atomic claim inventory with a claim class per entry.
- A first-pass elicitation record carrying labelled propositions, response hash, and available uncertainty signals.
- A budget ledger entry showing the charge and the remaining allowance.

**Quality Checkpoints**:

- Every proposition carries exactly 1 of the 3 labels, and unlabelled propositions are discarded rather than assumed known.
- Self-reported confidence is recorded as a feature and is never recorded as a probability.
- The attempt is charged before the result is read.
- No proposition labelled `inferred` or `unknown` is promoted to a factual claim at this step.

***

#### Step 3.2: Apply One Independent Reformulation Under an Evidence-Gain Test

**Required Actions**:

- Select exactly one reformulation strategy by diagnosis from decomposition, paraphrase, discriminating-alternative elicitation, opposite-proposition query, or bounded multi-sample generation, and record the diagnosis that licensed it.
- Issue the reformulated call without revealing the first-pass answer or any desired outcome.
- Compute evidence gain as the count of new atomic propositions plus resolved ambiguities plus reductions in semantic disagreement across sampled answers, and record the gain value with its components.
- Where log probabilities are unavailable, derive the disagreement signal from semantic clustering across at most 5 samples rather than from any invented token uncertainty.

**Required Outputs**:

- A reformulation record naming the strategy, the licensing diagnosis, and the prompt hash.
- An evidence-gain value with its component counts.
- A semantic disagreement measure with its sample count and clustering method version.

**Quality Checkpoints**:

- Exactly 1 strategy is applied per attempt, and the licensing diagnosis is recorded before the call.
- The reformulation prompt contains no restatement of the prior answer.
- Evidence gain is computed from proposition counts rather than from confidence movement.
- Sample count for disagreement measurement does not exceed 5.

***

#### Step 3.3: Terminate the Loop on Gain, Budget, or Escalation

**Required Actions**:

- Terminate the loop at 3 elicitation attempts by default, or earlier where evidence gain reaches 0 on any attempt.
- Emit one of the 4 declared exits: success where the class threshold is met and the claim is parametric-eligible, retrieval where uncertainty, disagreement, cutoff exposure, or citation need is present, abstention where no source route exists and calibrated confidence falls below the class threshold, or escalation.
- Escalate to a named human authority on suspected policy conflict, on a consequential claim above the parametric ceiling, or on any output reproducing sensitive or memorised content.
- Record the exit reason, the remaining budget, and the state hash so that a repeated state is detected rather than re-explored.

**Required Outputs**:

- A loop termination record naming the exit, the attempt count, and the exit reason.
- A state hash sequence demonstrating that no state repeated.
- An escalation record where escalation fired, naming the authority and the trigger.

**Quality Checkpoints**:

- Attempt count never exceeds 3 without a recorded contract exception.
- Every loop terminates in exactly 1 of the 4 declared exits, and no loop terminates by exhaustion without an exit record.
- A zero-gain attempt terminates the loop rather than triggering a further attempt.
- No exit is recorded as success for a claim whose consequence class exceeds the parametric ceiling.

***

### Phase 4: Source Routing and Threshold Calibration

**Objective**: Assign every atomic claim to exactly one route using hard rules first and class-fitted calibrated thresholds second, so that no confidence signal can override a policy obligation.

#### Step 4.1: Apply the Hard Routing Rules Before Any Estimate

**Required Actions**:

- Evaluate the hard rules in declared order against each claim's typed metadata, before any uncertainty signal is read.
- Route to `retrieved` or `hybrid` every claim that is current, private, consequential above the parametric ceiling, disputed, source-required, exact-quotation, jurisdiction-specific, or exposed to the cutoff.
- Route to a structured lookup, an authoritative database, an API, or a rules engine any claim whose answer is an exact record, and record that the retrieval and parametric routes were both bypassed.
- Route to `abstain` any claim whose class carries a mandatory citation obligation where no authorized evidence path is reachable.

**Required Outputs**:

- A hard-rule evaluation record per claim naming which rules fired and in what order.
- A pre-estimate route assignment for every claim the hard rules decide.
- A residual claim set carrying only claims no hard rule decided.

**Quality Checkpoints**:

- Hard rules are evaluated before any uncertainty signal is read for the same claim.
- Every claim with cutoff exposure carries a `retrieved` or `hybrid` route regardless of reported confidence.
- No claim reaches the residual set carrying a mandatory citation obligation.
- The rule firing order is recorded and matches the declared order.

***

#### Step 4.2: Fit Route Thresholds by Claim Class on Development Data

**Required Actions**:

- Fit one threshold per claim class on the development partition only, using the available feature set of self-reported confidence, log-probability summary, semantic disagreement, retrieval score, and claim-class priors.
- Evaluate reliability diagrams, expected calibration error, Brier score, selective accuracy, coverage, and the false-answer cost against the class's declared consequence weighting.
- Adjust exactly 1 feature, threshold, or class boundary per development cycle, and cap development at 5 cycles per hypothesis.
- Refuse to fit any class whose development partition holds fewer than 36 cases, and route that class to `retrieved` by default with the shortfall recorded.

**Required Outputs**:

- A per-class threshold record with the feature set, the fitted value, and the cycle count that produced it.
- A calibration report carrying reliability, expected calibration error, Brier score, selective accuracy, and coverage per class.
- A default-route record for every class whose data was insufficient to fit.

**Quality Checkpoints**:

- No threshold is fitted using any case from the holdout or attack partitions.
- Exactly 1 change is made per development cycle, and cycle count per hypothesis does not exceed 5.
- Every class with fewer than 36 development cases carries a `retrieved` default rather than an unfitted threshold.
- Self-reported confidence is used only as one feature among several and never as the sole feature for a consequential class.

***

#### Step 4.3: Hold the Held-Out Selective-Risk Gate

**Required Actions**:

- Evaluate the fitted thresholds once against the sealed holdout partition, at declared checkpoints only, and never iteratively.
- Require the routed configuration to match or exceed the always-retrieve baseline on selective accuracy at the contract's target coverage, and to beat the never-retrieve baseline by at least 3 percentage points on the classes it routes parametrically.
- Require worst-slice selective accuracy to fall no more than 5 percentage points below the aggregate, and revert the affected class to `retrieved` where it does.
- Revert the whole threshold set and re-enter Phase 4 where the holdout shows no practically meaningful gain or any critical-slice regression.

**Required Outputs**:

- A holdout evaluation record with the aggregate and per-slice selective-risk curves.
- A gate verdict per claim class naming pass, revert-to-retrieved, or revert-and-refit.
- A revision record naming the exact model manifest and corpus version the verdict binds to.

**Quality Checkpoints**:

- The holdout is evaluated exactly once per threshold set, and the evaluation count is logged.
- Every passing class beats the never-retrieve baseline by at least 3 percentage points on selective accuracy.
- No class passes while its worst slice trails the aggregate by more than 5 percentage points.
- The verdict names the model revision, so a revision change invalidates it automatically.

***

### Phase 5: Evidence Acquisition and Artifact Resolution

**Objective**: Convert every non-parametric route into an inspectable canonical record, rejecting identifiers and cache hits that cannot be resolved or revalidated.

#### Step 5.1: Dispatch the Retrieved Route Against the Authorized Corpus

**Required Actions**:

- Dispatch retrieval for every claim routed `retrieved` or `hybrid`, honouring tenant, authorization, jurisdiction, and freshness filters as server-side constraints rather than as post-filters.
- Treat any generated abstraction used to reach the corpus as a retrieval instrument and never as evidence, so that generated text is never cited, never displayed as a source, and never counted toward support.
- Record for each admitted passage the source identifier, the version, the content hash, the timestamp, and the exact offsets of the span retained.
- Reject and log any passage whose source age exceeds the claim class's volatility ceiling, and re-dispatch once against a freshness-constrained query before abstaining.

**Required Outputs**:

- An admitted evidence set with identifier, version, hash, timestamp, and offsets per passage.
- A rejection log naming each excluded passage and the failing check.
- A freshness verdict per admitted passage against the claim class volatility ceiling.

**Quality Checkpoints**:

- Authorization and jurisdiction filters are applied inside the query rather than after ranking.
- No generated text appears in the admitted evidence set.
- Every admitted passage carries all 5 provenance fields.
- At most 1 freshness re-dispatch occurs per claim before abstention.

***

#### Step 5.2: Resolve Generated Identifiers to Canonical Records

**Required Actions**:

- Constrain decoding to the versioned valid-identifier registry, so that an identifier outside the registry cannot be emitted rather than being emitted and then filtered.
- Resolve every decoded identifier against the canonical store, and confirm the target is active, authorized for the caller, and not tombstoned.
- Discard without repair any identifier that fails to resolve, resolves to a tombstoned record, collides across registry versions, or resolves outside the caller's authorization scope, and record the discard reason.
- Compare the generative route against the frozen lexical, dense, and hybrid baselines at the live corpus scale on every corpus growth of 25 percent or more, and retire the route where it no longer leads [3].

**Required Outputs**:

- A resolved record set carrying the canonical identifier, version, and hash for every accepted decode.
- A discard log with a reason code per rejected identifier.
- A scale comparison record against the 3 frozen retrieval baselines at the current corpus size.

**Quality Checkpoints**:

- Decoding is constrained to the registry, and the registry version is recorded with each decode.
- Every accepted identifier resolves to an active, authorized canonical record.
- No discarded identifier is regenerated or repaired within the same request.
- The scale comparison is re-run at every 25 percent corpus growth and the route is retired where it trails.

***

#### Step 5.3: Validate Reusable Context Caches Before Any Hit Is Served

**Required Actions**:

- Compute the cache key fingerprint over model identifier, model revision, tokenizer version, prompt or context version, source content hashes, policy version, tenant or authorization fingerprint, cache format version, and invalidation epoch.
- Compare the request fingerprint byte-for-byte against the entry fingerprint, and treat any difference in any component as a miss rather than as a degraded hit.
- Reauthorize and freshness-check every hit against the current canonical records, and invalidate the entry where any source, access rule, model, tokenizer, prompt, or policy has changed since creation.
- Confine cache entries to a single tenant and authorization scope, and never share cache state across a trust boundary without an explicit documented security validation, because reconstruction attacks against serving caches have been demonstrated under published threat models [4].

**Required Outputs**:

- A fingerprint comparison record per cache lookup with the component-level match result.
- A reauthorization and freshness verdict per hit.
- An invalidation log naming the triggering component change and the entries evicted.

**Quality Checkpoints**:

- Every cache hit carries a byte-identical fingerprint across all 9 components.
- No hit is served without a reauthorization verdict computed at request time.
- Cache entries carry a tenant and authorization fingerprint, and no entry is readable outside its scope.
- A key match alone never establishes freshness or authorization.

***

### Phase 6: Conflict Adjudication and Answer Assembly

**Objective**: Resolve disagreements between sources under a fixed authority order and assemble an answer whose every claim carries an accurate citation-availability value.

#### Step 6.1: Normalize the Claim Before Declaring a Conflict

**Required Actions**:

- Normalize entity identity, effective date, jurisdiction, unit, currency, negation, source version, and question interpretation across the parametric answer and every admitted passage.
- Classify the disagreement as apparent or real, and dissolve apparent conflicts by recording the normalizing qualifier that makes both statements conditionally true.
- Record the conflict type as context-memory, inter-context, or intra-memory, because the three carry different resolutions and collapsing them discards the diagnosis [2].
- Cap automated conflict rounds at 2, and route to abstention or escalation rather than opening a third.

**Required Outputs**:

- A normalization record naming each field normalized and the transformation applied.
- A conflict classification per disagreement with apparent or real and the conflict type.
- A qualifier record for every apparent conflict dissolved.

**Quality Checkpoints**:

- Normalization runs before any authority order is applied.
- Every disagreement carries both an apparent-or-real verdict and a conflict type.
- No apparent conflict is adjudicated as a real conflict.
- Automated conflict rounds do not exceed 2 per claim.

***

#### Step 6.2: Apply the Authority Order and Record the Resolution

**Required Actions**:

- Apply the declared authority order in sequence: an authorized system of record outranks current primary evidence, current primary evidence outranks older evidence, and any attributable evidence outranks the parametric answer.
- Treat parametric familiarity as zero evidential weight against current attributable evidence, and never let fluency, repetition, or a high self-reported confidence promote a parametric claim above a retrieved one.
- Test the deployment's context-following behaviour directly on the counterfactual-context slice rather than assuming an instruction-tuned model prefers supplied context over its weights, since instruction tuning has been shown capable of reducing context reliance under conflict [5].
- Record the winning claim, the rule that selected it, the losing alternatives, the residual uncertainty, and any unresolved qualifier.

**Required Outputs**:

- A resolution record per conflict naming the winner, the applied rule, and the losing alternatives.
- A context-following measurement on the counterfactual slice for the pinned model revision.
- An unresolved-conflict list carrying claims routed to abstention or escalation.

**Quality Checkpoints**:

- The authority order is applied as declared, and no resolution cites a model preference as its rule.
- Every resolution records at least 1 losing alternative or states that none existed.
- The counterfactual-context measurement exists for the current model revision and is not inherited from a prior revision.
- Every high-consequence claim left unresolved after 2 rounds terminates in abstention or escalation.

***

#### Step 6.3: Assemble the Answer Under the Citation-Availability Gate

**Required Actions**:

- Atomize the draft answer into material claims, and map every claim routed `retrieved`, `hybrid`, `generative_index`, or `cache` to an exact span in a named canonical record at a recorded version and offset.
- Resolve every citation deterministically against the canonical store, and mark unsupported any claim whose cited span does not exist at the recorded version, regardless of any model assertion of support.
- Set `citation_availability=false` on every claim answered from weights, label the answer unverified, and disclose the declared cutoff or `unknown` where the claim carries any temporal component.
- Retrieve, qualify, omit, or abstain for any material claim that cannot meet its route-specific gate, and route calculations and structured facts to deterministic tools wherever such a tool exists.

**Required Outputs**:

- An assembled answer with one citation-availability value and one route label per material claim.
- A citation resolution record naming each verified span and each failure.
- A cutoff disclosure attached to every temporally exposed parametric claim.

**Quality Checkpoints**:

- Every material claim carries exactly 1 route label and exactly 1 citation-availability value.
- No parametric claim carries `citation_availability=true`, and no self-generated bibliography appears in the citation record.
- Every citation resolves to an existing span at the recorded version, and unresolved citations mark their claims unsupported.
- No calculation is answered from weights where a deterministic tool is available.

***

### Phase 7: Exposure Testing, Telemetry, and Staged Release

**Objective**: Measure the exposures unique to non-attributable answering, operate a telemetry contract that makes route quality auditable, and stage every change behind shadow, canary, and rollback.

#### Step 7.1: Run Staleness, Memorization, and Integrity Exposure Tests

**Required Actions**:

- Sample closed-book answers against current authoritative records on a recurring schedule, and compute the staleness exposure rate as the share of parametric answers contradicted by a current record.
- Test memorization exposure with synthetic canaries, prompted extraction attempts, near-verbatim reproduction checks, and secret-completion probes, since verbatim training content has been recovered from production models under published attacks [6][7].
- Rate-limit and monitor high-volume sampling, divergence prompts, repeated-prefix probing, and cache probing, and never infer non-membership from a failed membership-inference attempt, because many such attacks perform near chance in broad settings [8].
- Authenticate every cache-population and registry-population input, hash and version every artifact, and quarantine anomalous entries; never allow model output or retrieved content to raise a budget, widen an authorization, approve a change, or select a new trust root.

**Required Outputs**:

- A staleness exposure rate per claim class with the sampling schedule that produced it.
- A memorization test record covering canary exposure, extraction success, and near-verbatim rate.
- An integrity record naming quarantined artifacts and the anomaly that triggered quarantine.

**Quality Checkpoints**:

- Staleness sampling covers every claim class with a permitted parametric route at least monthly.
- Canary tests run on every model revision change, and results are not inherited across revisions.
- No non-membership conclusion is recorded from a failed attack.
- No budget, authorization, or trust-root change traces to content the system retrieved or generated.

***

#### Step 7.2: Operate the Telemetry Contract

**Required Actions**:

- Create one run identifier per evaluation or deployment run and one trace identifier per request, and propagate both through routing, elicitation, retrieval, resolution, cache, conflict, and assembly spans.
- Log per request the pinned model manifest, the admitted sense, the permitted and selected routes with the route reason, the rejected routes with their reasons, the decision margin, the budget consumption, and the final abstention flag with its reason.
- Log per claim the class, the volatility ceiling, the cutoff exposure, the hard rules that fired, the calibrated confidence, the citation-availability value, the conflict identifiers, and the correctness verdict where a label exists.
- Withhold raw prompts, raw outputs, and any sensitive span from the log unless the declared content-logging policy permits them, and record hashes in their place.

**Required Outputs**:

- A per-request trace carrying the manifest, the route decisions, and the budget ledger state.
- A per-claim record carrying class, exposures, thresholds, citation availability, and verdicts.
- A content-logging policy record naming which fields are stored raw and which are hashed.

**Quality Checkpoints**:

- Every request carries exactly 1 trace identifier, and every span references it.
- Every route decision records both the chosen route and at least 1 rejected route with a reason.
- No raw sensitive span appears in the log where the policy withholds it.
- Aggregates are computable by model revision, route, claim class, slice, and tenant without re-processing raw content.

***

#### Step 7.3: Stage Shadow, Canary, and Rollback

**Required Actions**:

- Run the candidate configuration in shadow against production traffic with no user-visible effect, comparing paired closed-book, open-book, and incumbent outcomes on the same requests.
- Promote to a canary cohort of at most 5 percent of eligible traffic only where shadow shows no hard-gate regression, and hold the canary for a minimum of 3 measurement windows.
- Define automatic rollback triggers on selective accuracy, citation availability, staleness exposure, unauthorized-hit count, and abstention rate, and bind rollback to a single alias change rather than to a partial reconfiguration.
- Cap release at 3 stages with at most 1 remediation cycle per failed stage, and re-enter Phase 2 rather than opening a fourth stage.

**Required Outputs**:

- A shadow comparison record with paired per-request deltas across all 3 conditions.
- A canary record naming the cohort size, the window count, and the trigger thresholds.
- A release manifest naming the owner, the expiry, the rollback pointer, and the monitoring thresholds.

**Quality Checkpoints**:

- Shadow comparison is paired per request rather than aggregate, and it covers every named slice.
- Canary cohort does not exceed 5 percent, and the canary holds for at least 3 windows.
- Every rollback trigger names a numeric threshold and executes as a single alias change.
- Release stages do not exceed 3, and no stage proceeds while a hard gate is unmet.

***

## III. Implementation Guidance for AI Agents

AI agents operating this framework must hold every source-eligibility decision in deterministic software and treat model output as a proposal at every point where a route, an authorization, a budget, or a citation is decided. The following guidance translates the framework above into agent-executable orchestration, verification, and recovery.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Agent**: Owns the knowledge source contract, the claim class table, the parametric ceiling, and the budget ledger. Holds the admissibility gate and emits referrals. Capabilities required: policy metadata access, schema validation, and write access to the contract registry. Owns Phase 1.
2. **Evaluation Agent**: Builds the paired corpus, freezes the counterfactual baselines, and seals the holdout. Capabilities required: corpus assembly, authoritative source access, partition hashing, and paired metric computation. Owns Phase 2 and re-runs it on every model revision change.
3. **Elicitation Agent**: Runs bounded parametric elicitation and produces labelled propositions with uncertainty signals. Capabilities required: model invocation, semantic clustering, and evidence-gain arithmetic. Owns Phase 3 and holds no authority over any route.
4. **Routing Agent**: Applies hard rules, reads fitted thresholds, and assigns exactly one route per claim. Capabilities required: typed metadata evaluation, threshold lookup, and abstention-gate enforcement. Owns Phase 4 and is the only component permitted to write a route.
5. **Resolution Agent**: Dispatches retrieval, resolves generated identifiers, and validates cache fingerprints. Capabilities required: authorized corpus query, canonical store resolution, registry lookup, and fingerprint computation. Owns Phase 5.
6. **Adjudication Agent**: Normalizes claims, classifies conflicts, applies the authority order, and runs the citation resolver. Capabilities required: field normalization, canonical span verification, and conflict logging. Owns Phase 6.
7. **Assurance Agent**: Runs exposure tests, operates telemetry, and gates staged release. Capabilities required: scheduled sampling, canary control, alias management, and rollback execution. Owns Phase 7 and holds veto authority over promotion.

**Workflow Execution Pattern**:

```
STATE: Phase_4_Source_Routing
ACTIONS:
  1. Evaluate hard routing rules against typed claim metadata
  2. Emit pre-estimate routes for every claim a hard rule decides
  3. Read class thresholds for the residual claim set
  4. Apply abstention gate where no eligible source meets its threshold
  5. Write exactly one route per claim with rule provenance
VALIDATION:
  - hard_rules_evaluated_before_uncertainty_read == TRUE
  - claims_with_cutoff_exposure_routed_parametric == 0
  - claims_with_mandatory_citation_routed_parametric == 0
  - thresholds_fitted_on_holdout == FALSE
  - route_count_per_claim == 1
TRANSITIONS:
  IF all_validations_pass AND route != abstain THEN next_state = Phase_5_Resolution
  IF all_validations_pass AND route == abstain THEN next_state = Phase_6_Assembly
  IF thresholds_fitted_on_holdout == TRUE THEN next_state = Phase_4_Refit_Halt
  ELSE next_state = Phase_4_Error_Handling
```

**Two-Phase Action Pattern**:

1. **Plan**: The Routing Agent emits the full route assignment with rule provenance before any retrieval, decode, or cache lookup is issued.
2. **Validate**: The Contract Agent confirms every route against the contract's permitted vocabulary, the parametric ceiling, and the citation obligations while no external call has yet been made.
3. **Execute**: The Resolution Agent acts only on a validated route set, and a route the Contract Agent rejected is never executed under a fallback.

**Approval gate**: Human authorisation is required before execution wherever any of the following triggers fires: the projected parametric route share exceeds 40 percent of consequential requests; a claim above the declared parametric ceiling is proposed for a `parametric` route; a sense refusal referral is overridden; the staleness exposure rate for any claim class exceeds 5 percent; a cache is proposed for sharing across a tenant boundary; or a canary rollback trigger fires twice within 3 measurement windows. Below every trigger, agents proceed autonomously and log the decision.

**Context management requirements**: Agents must process one claim class per working pass rather than holding the whole corpus in working context, must read the paired evaluation corpus in bounded slices, and must persist route decisions to the trace store rather than carrying them across passes in context. Where a run exceeds the available context, the agent writes a handoff record naming the completed phases, the sealed holdout hash, the fitted thresholds, and the pending claim classes.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract and Sense Integrity (After Phase 1)**

- **Automated Check**: Every claim class carries citation obligation, consequence class, volatility ceiling, and permitted routes; exactly 1 primary sense is admitted; every refusal carries a referral; at least 2 counterfactual baselines are recorded.
- **Agent Action on Pass**: Proceed to corpus construction.
- **Agent Action on Failure**: Halt and return the incomplete contract rows and the missing referrals.
- **Human Review Trigger**: Any claim class carrying a mandatory citation obligation and a permitted parametric route, or a proposed override of a sense refusal.

**Checkpoint 2: Corpus and Baseline Validity (After Phase 2)**

- **Automated Check**: All 3 conditions populated for every case; every named slice at or above 30 cases or carrying a shortfall record; holdout at or above 25 percent per class and hashed; baselines bound to the current model revision.
- **Agent Action on Pass**: Proceed to elicitation.
- **Agent Action on Failure**: Return the classes and slices below threshold and re-enter corpus construction for those only.
- **Human Review Trigger**: More than 20 percent of claim classes fall below the 60-case minimum.

**Checkpoint 3: Elicitation Discipline (After Phase 3)**

- **Automated Check**: Attempt count at or below 3 per claim; every proposition labelled; every loop terminating in 1 of the 4 declared exits; no state hash repeated.
- **Agent Action on Pass**: Proceed to routing.
- **Agent Action on Failure**: Terminate the loop at the current attempt and record the exit as budget exhaustion.
- **Human Review Trigger**: Escalation exit fires on more than 10 percent of claims in any class.

**Checkpoint 4: Routing and Calibration Integrity (After Phase 4)**

- **Automated Check**: Hard rules evaluated before uncertainty reads; zero claims with cutoff exposure or mandatory citation obligation on a parametric route; holdout evaluated exactly once; every passing class beating never-retrieve by at least 3 percentage points.
- **Agent Action on Pass**: Proceed to resolution.
- **Agent Action on Failure**: Halt; a routing defect must be corrected before any external call is issued.
- **Human Review Trigger**: Any evidence that a threshold was fitted against holdout cases, which invalidates the entire threshold set.

**Checkpoint 5: Artifact Resolution Integrity (After Phase 5)**

- **Automated Check**: Every admitted passage carrying all 5 provenance fields; every accepted identifier resolving to an active authorized record; every cache hit fingerprint byte-identical across all 9 components.
- **Agent Action on Pass**: Proceed to adjudication.
- **Agent Action on Failure**: Discard the failing artifacts, record the reason codes, and re-enter the affected route once before abstaining.
- **Human Review Trigger**: Unauthorized-hit count above 0, or any cross-tenant fingerprint match.

**Checkpoint 6: Adjudication and Assembly Integrity (After Phase 6)**

- **Automated Check**: Normalization preceding every authority-order application; conflict rounds at or below 2; every material claim carrying exactly 1 route label and 1 citation-availability value; every citation resolving to an existing span.
- **Agent Action on Pass**: Deliver the answer and record the trace.
- **Agent Action on Failure**: Mark the affected claims unsupported, then re-run the citation-availability gate; abstain where the answer no longer meets its class gate.
- **Human Review Trigger**: An unresolved conflict on any claim at the consequential class.

**Checkpoint 7: Release Conformance (After Phase 7)**

- **Automated Check**: Shadow comparison paired and slice-complete; canary at or below 5 percent held for at least 3 windows; every rollback trigger carrying a numeric threshold; staleness exposure within class limits.
- **Agent Action on Pass**: Promote by alias change and record the release manifest.
- **Agent Action on Failure**: Hold at the current stage, run at most 1 remediation cycle, then revert.
- **Human Review Trigger**: Any privacy incident, memorised-secret reproduction, deletion failure, or hard-gate regression above 20 percent of its threshold.

**Aggregate quality threshold**: A configuration is promotable only where all 7 checkpoints pass, worst-slice selective accuracy trails the aggregate by no more than 5 percentage points, and citation availability on claim classes carrying a mandatory obligation is 100 percent. A configuration failing any one of the three is held regardless of aggregate accuracy.

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
MODEL_REVISION_BOUND:
```

### C. Error Handling and Troubleshooting

**Error Type 1: Silent Parametric Substitution**

- **Symptoms**: Claims answered without citations in a class whose contract requires them; citation availability falling below its class target while accuracy appears stable; a rise in answers containing dates or figures with no resolved span.
- **Diagnostic Steps**: Compare the route label on each unsupported claim against the contract's permitted vocabulary for its class; check whether a retrieval dependency was classified unavailable and a fallback fired; verify that the hard-rule evaluation record exists for the affected claims.
- **Resolution Protocol**: Option A, restore the hard-rule ordering so route assignment precedes any uncertainty read, and re-run the affected requests. Option B, disable the parametric route for the affected class entirely and route to `retrieved` until the defect is closed. Option C, where the retrieval dependency is genuinely unavailable, convert the class to `abstain` rather than permitting an unattributable answer.
- **Escalation Trigger**: More than 2 percent of claims in a mandatory-citation class carry `citation_availability=false`, or the defect recurs after 1 remediation cycle.

**Error Type 2: Calibration Collapse After a Model or Prompt Change**

- **Symptoms**: Selective accuracy falling while coverage holds; expected calibration error rising above its baseline; a class that previously beat never-retrieve now trailing it.
- **Diagnostic Steps**: Compare the current model manifest against the manifest bound to the frozen baselines; confirm whether the prompt version, decoding settings, or tokenizer changed; check whether any threshold was refitted between the two measurements.
- **Resolution Protocol**: Option A, revert to the prior pinned manifest and restore the previously validated thresholds. Option B, re-enter Phase 2, rebuild the baselines against the new manifest, and refit thresholds on development data only. Option C, route every affected class to `retrieved` as an interim posture while refitting proceeds.
- **Escalation Trigger**: Two consecutive refits fail the held-out selective-risk gate, or calibration collapse affects more than 3 claim classes simultaneously.

**Error Type 3: Stale or Unauthorized Cache Service**

- **Symptoms**: Answers contradicting a canonical record that was updated after the cache entry was created; unauthorized-hit count above 0; identical answers served to callers in different authorization scopes.
- **Diagnostic Steps**: Recompute the fingerprint for the served entries and identify which of the 9 components diverged; check whether an invalidation epoch was advanced without eviction; confirm that the tenant fingerprint is part of the key rather than a post-filter.
- **Resolution Protocol**: Option A, advance the invalidation epoch, evict the affected generation, and re-serve from live retrieval. Option B, disable the cache route for the affected tenant and record the disablement in the route eligibility record. Option C, where cross-scope service is confirmed, disable the cache route globally and open a security review before any re-enablement.
- **Escalation Trigger**: Any cross-tenant fingerprint match, any served entry whose source record changed before the hit, or an unauthorized-hit count above 0 in a single measurement window.

**Error Type 4: Unresolvable or Colliding Generated Identifiers**

- **Symptoms**: Decoded identifiers failing resolution; identifiers resolving to tombstoned records; the same identifier resolving differently across registry versions; recall degrading as the corpus grows.
- **Diagnostic Steps**: Confirm that decoding is constrained to the registry rather than filtered after generation; compare the registry version recorded at decode against the current version; re-run the scale comparison against the frozen lexical, dense, and hybrid baselines at the live corpus size.
- **Resolution Protocol**: Option A, rebuild and re-version the identifier registry, then re-run the constrained decode. Option B, where the corpus has grown past the configuration's demonstrated scale, retire the generative route for the affected corpus and fall back to the winning frozen baseline. Option C, where collisions persist across registry versions, disable the route and record the identifier scheme as unfit for the corpus.
- **Escalation Trigger**: Unresolved-identifier rate above 1 percent of decodes, or 2 consecutive scale comparisons in which the generative route trails the best frozen baseline.

**Error Type 5: Persistent Knowledge Conflict**

- **Symptoms**: Conflict rounds reaching the cap of 2 on a rising share of requests; authoritative sources disagreeing with each other; the model overriding supplied context on the counterfactual slice.
- **Diagnostic Steps**: Verify that normalization ran and inspect which fields it touched; recheck the conflict-type classification, since context-memory, inter-context, and intra-memory conflicts resolve differently; re-measure context-following on the counterfactual slice for the current revision.
- **Resolution Protocol**: Option A, extend normalization to the field that generated the apparent conflict and re-run the adjudication once. Option B, where two authoritative sources genuinely disagree, present both bounded interpretations with their qualifiers if the task permits, and abstain otherwise. Option C, where the model overrides supplied context materially, route the affected classes to structured lookup or deterministic tooling instead of generation.
- **Escalation Trigger**: Unresolved conflicts on more than 5 percent of requests in any class, or any unresolved conflict at the consequential class.

**Error Type 6: Budget or Trust Boundary Violation**

- **Symptoms**: Attempt counts exceeding declared caps; a budget raised mid-run; an authorization widened during execution; instructions appearing in retrieved or cached content that name system parameters.
- **Diagnostic Steps**: Read the budget ledger's write history and identify the writing component; confirm that every ledger write originates in the deterministic tier; scan admitted passages and cache entries for imperative content addressed to the executing system.
- **Resolution Protocol**: Option A, revert the ledger to its contract value, terminate the run as budget exhaustion, and quarantine the originating artifact. Option B, disable the affected corpus segment or cache generation pending an integrity review. Option C, where the violation traces to a component rather than to content, revoke that component's ledger write capability and re-run under the corrected control plane.
- **Escalation Trigger**: Any budget, authorization, or trust-root change traceable to model output or retrieved content, escalated immediately with no retry.

**Troubleshooting Decision Tree**:

```
Answer or configuration failed a gate
│
├─ Is a material claim missing a resolved citation?
│  ├─ YES → Is the claim's class citation-mandatory?
│  │        ├─ YES → Force route = retrieved; re-run once
│  │        │        └─ Still unresolved → ABSTAIN and log Error Type 1
│  │        └─ NO  → Set citation_availability=false; label unverified → RESOLVED
│  └─ NO → continue
│
├─ Did selective accuracy fall while coverage held?
│  ├─ YES → Does the model manifest match the frozen baseline manifest?
│  │        ├─ NO  → Revert manifest or re-enter Phase 2 → RESOLVED
│  │        └─ YES → Refit thresholds on development data only
│  │                 └─ Second refit fails holdout gate → ESCALATE (Error Type 2)
│  └─ NO → continue
│
├─ Did a served artifact fail revalidation?
│  ├─ YES → Was it a cache hit?
│  │        ├─ YES → Advance invalidation epoch and evict
│  │        │        └─ Cross-tenant match found → ESCALATE (Error Type 3)
│  │        └─ NO  → Discard identifier; re-run scale comparison
│  │                 └─ Route trails best baseline twice → ESCALATE (Error Type 4)
│  └─ NO → continue
│
├─ Did conflict rounds reach the cap of 2?
│  ├─ YES → Did normalization run on all typed fields?
│  │        ├─ NO  → Extend normalization; re-adjudicate once → RESOLVED
│  │        └─ YES → Consequence class consequential?
│  │                 ├─ YES → ESCALATE (Error Type 5)
│  │                 └─ NO  → Present bounded interpretations or ABSTAIN
│  └─ NO → continue
│
└─ Did a budget, authorization, or trust root change during the run?
   ├─ YES → ESCALATE immediately, quarantine the artifact (Error Type 6)
   └─ NO  → Re-run the failing checkpoint once; on second failure ESCALATE
```

### D. Performance Metrics and Continuous Learning

**Routing quality metrics**: Routing accuracy measures the share of claims whose selected route matched the retrospectively correct route, with a target of at least 85 percent per claim class. Excess retrieval rate measures retrievals issued where the parametric route would have answered correctly, with a target below 20 percent. Missed retrieval rate measures parametric answers that were wrong where retrieval would have been right, with a target below 3 percent for advisory classes and 0 for anything above the parametric ceiling. Route utility measures expected value relative to both the always-retrieve and never-retrieve baselines, and a configuration that beats neither is removed at the next release gate.

**Answer quality metrics**: Selective accuracy is reported jointly with coverage at 3 declared operating points, never alone. Expected calibration error carries a target at or below 0.10 per claim class, and Brier score is tracked per class rather than in aggregate. Citation availability carries a target of 100 percent on mandatory-citation classes and is reported separately from citation precision, which measures whether resolved spans actually support their claims. Conflict-resolution correctness is measured on the labelled conflict slice with a target of at least 90 percent. Abstention precision measures the share of abstentions that were correct, and abstention recall measures the share of unanswerable cases that produced one.

**Exposure and cost metrics**: Staleness exposure rate carries a class-level ceiling of 5 percent, above which the class loses its parametric route until the next calibration cycle. Unauthorized-hit count and cross-tenant leakage count carry ceilings of 0. Canary exposure, extraction success, and near-verbatim rate are tracked per model revision and never inherited across revisions. Cost is reported as cost per correct non-abstained answer rather than cost per request, alongside p50, p95, and p99 latency and the token, retrieval, and cache-byte consumption per answered request.

**Continuous learning discipline**: Every logged request contributes to a gain ledger recording the route taken, the outcome, and the counterfactual outcome wherever both routes ran. Thresholds are refitted from that ledger on a fixed cadence of at most 1 refit per model revision or per 90 days, whichever comes first, and never opportunistically after a bad week. Route eligibility, the parametric ceiling, authorization scopes, budget caps, and human approval triggers remain outside any fitted policy in every case, because a policy learned from outcomes must never acquire the ability to widen its own permissions. New claim classes enter through Phase 1 rather than being inferred from traffic, and a class whose volatility ceiling proves wrong is corrected in the contract rather than compensated for in a threshold.

**Robustness monitoring**: Every metric is recomputed across model revisions, prompt versions, sampling seeds, temperatures, languages, and named slices, and the worst slice rather than the mean governs promotion. Paired per-case deltas are the reporting unit for every comparison, and a report presenting only aggregate answer accuracy is non-conforming.

***

## IV. Domain-Agnostic Application Guidance

The framework transfers across domains because its primitives are a claim class, a citation obligation, a volatility ceiling, and a consequence class, all of which exist in any setting where a system answers factual questions. What changes across domains is which claim classes carry a mandatory citation obligation, how short the volatility ceilings are, and where the parametric ceiling sits.

### 4.1 Cross-Domain Application Patterns

**Clinical and health information**: Citation obligations are mandatory for anything touching dosage, interaction, contraindication, eligibility, or guideline text, and the parametric ceiling sits at the informational class. Volatility ceilings are short for formulary, recall, and guideline content and long for settled physiology. The counterfactual-context slice matters more here than almost anywhere, because a model that overrides a supplied current guideline with an older memorised one produces a plausible and dangerous answer. Abstention with a referral to the authoritative source is the correct outcome far more often than in other domains, and the abstention path must therefore be a first-class product surface rather than an error state.

**Financial services and regulatory reporting**: Rates, limits, thresholds, filing deadlines, instrument terms, and counterparty data all carry cutoff exposure by construction, so the hard routing rules dispose of most claims before any threshold is consulted. The parametric route survives only for stable definitional content such as what an instrument class is. Jurisdiction is a normalization field of first importance, since the same question resolves differently by venue and an unnormalized jurisdiction produces an apparent conflict that adjudication then resolves wrongly. Deterministic tooling owns every calculation without exception.

**Legal and compliance research**: Exact quotation is the dominant requirement, which disqualifies the parametric route across nearly all claim classes and also disqualifies any latent representation that replaces the source text rather than pointing at it. Effective-date normalization is mandatory, because a superseded provision and its replacement are both true statements about different periods and are trivially misclassified as a conflict. Generated citation strings are the characteristic failure, and the citation resolver's span-existence check is the only control that reliably catches them.

**Industrial operations and field engineering**: Equipment revisions, part numbers, torque values, and procedure steps carry mandatory citation obligations tied to a specific document revision, while general engineering principles sit comfortably on the parametric route. Reusable context caches are unusually attractive here, because a bounded manual set is consumed repeatedly, and the fingerprint discipline is correspondingly load-bearing: a cached procedure served after a revision change is an operational hazard rather than a stale answer.

**Public-sector benefits and eligibility determination**: Eligibility rules change on legislative and administrative cycles, are jurisdiction-specific, and carry both a citation obligation and an appealable-decision requirement, so the parametric ceiling sits at informational and every determinative claim routes to a system of record. Private applicant data must never enter a shared cache scope, and the tenant fingerprint is a legal control rather than an efficiency measure.

**Software engineering support**: Library and interface behaviour is high-volatility and version-specific, so the declared cutoff is a poor guide and effective-cutoff measurement per library is worth its cost. Structured retrieval over a symbol graph or a package index outranks both parametric recall and similarity search for exact interface questions, and the hard routing rules should route to that structured path before either. Conceptual explanation is the claim class where the parametric route genuinely earns its place.

### 4.2 Scale, Risk, and Latency Adaptation

**Small-scope deployments**: Where the corpus is bounded and traffic is low, the entire framework runs with a single model endpoint, one authorized retrieval path, a file-based evaluation corpus, and a spreadsheet-grade threshold table. The minimum viable configuration is a pinned manifest, hard routing rules, a 60-case-per-class paired corpus, and an abstention path. Threshold fitting may be deferred by routing every class to `retrieved` until enough labelled traffic accumulates, and that posture is correct rather than a compromise.

**Large-scope deployments**: Where traffic is high and many claim classes exist, thresholds are fitted and stored per class rather than globally, cache generations are versioned and aliased, and the identifier registry is maintained on its own release cadence. The cost of the framework falls as scale rises, because the paired baselines are computed once per model revision while their benefit applies to every request. Shadow evaluation replaces sampling as the primary evidence source at scale, since paired per-request comparison becomes affordable.

**High-risk and low-latency adaptation**: Risk and latency pull in opposite directions, and the resolution is always to move the parametric ceiling rather than to weaken a gate. Where risk is high, the ceiling drops to informational, coverage falls, abstention rises, and the deployment accepts lower coverage in exchange for attributable answers. Where latency is binding, the cache route and the parametric route both become attractive, and the correct response is to shrink the claim classes eligible for them rather than to relax the fingerprint check or the citation gate. A deployment that cannot meet its latency objective without weakening a gate has an infrastructure problem rather than a routing problem, and must report it as such.

***

## V. Limitations and Considerations

**Calibrated confidence is not knowledge presence**: A calibrated threshold predicts whether an answer from a given class is likely correct; it says nothing about whether the model holds the knowledge, whether it is being truthful, or whether it would report what it holds. A model can be confidently and consistently wrong, so low disagreement across samples is not evidence of correctness. The mitigation is that no calibrated signal ever overrides a hard routing rule, every consequential claim routes to attributable evidence regardless of confidence, and the guide requires external verification wherever an error's consequence exceeds the retrieval cost.

**Parametric provenance does not exist at this layer**: No agent-layer operation maps a generated fact back to the training record that produced it, and a model-generated bibliography is not provenance. The consequence is that any answer produced from weights is structurally unauditable. The mitigation is the unconditional `citation_availability=false` marking, the unverified label on parametric answers, and the contract rule that no claim class carrying a mandatory citation obligation may permit a parametric route.

**The refused senses may be genuinely necessary**: Where auditing what a model internally represents, or changing a fact it states, is the actual requirement, this guide refuses rather than solves. The consequence is that some legitimate needs leave the framework unmet. The mitigation is the referral, which names the unmet requirement, the agent-layer substitutes already measured and excluded, and the assurance obligations the receiving model-engineering process must discharge, so the work is handed over intact rather than abandoned or faked.

**Declared cutoffs are unreliable and effective cutoffs are expensive**: A provider-declared cutoff can diverge from the date beyond which recall actually degrades for a given topic or resource, and measuring effective cutoffs per topic costs labelled data the deployment may not have [1]. The consequence is that cutoff exposure is sometimes assessed against a wrong date. The mitigation is that a cutoff is recorded as `unknown` where none is published, is never inferred from a release date, and that any class where the cutoff is uncertain defaults to `retrieved`.

**Threshold numbers in this guide are deployment defaults, not measured findings**: The 3-attempt elicitation cap, the 60-case class minimum, the 30-case slice minimum, the 60/25/15 partition split, the 3-percentage-point improvement requirement over never-retrieve, the 5-percentage-point worst-slice tolerance, the 5-percent staleness ceiling, the 5-percent canary cohort, the 40-percent parametric share escalation trigger, the 85-percent routing accuracy target, and the 0.10 expected calibration error target are operable starting points chosen to be enforceable on first deployment. None is a measured result transferable across corpora, models, or risk postures. The mitigation is that each is recorded in the contract as a declared default with an owner, is reviewed at the first release gate against observed distributions, and is tightened or loosened with the change recorded rather than silently.

**Evaluation labels lag the world**: A paired corpus is correct as of its construction date, and volatile claim classes drift out from under it. The consequence is that a passing holdout can certify a configuration that is already wrong in production. The mitigation is the recurring staleness sampling in Step 7.1, the requirement that a class exceeding its staleness ceiling loses its parametric route immediately rather than at the next calibration cycle, and the rule that baselines are invalidated automatically by a model revision change.

**Selective risk trades coverage for safety and someone must own the trade**: Raising a threshold lowers the error rate on answered requests and raises the abstention rate, and no purely technical criterion selects the operating point. The consequence is that an unowned threshold drifts toward whichever failure is less visible, which is usually the silent wrong answer. The mitigation is the contract's requirement that a named risk owner sets the acceptable false-answer and false-abstention costs per claim class before thresholds are fitted, and that the abstention rate is a monitored metric with its own rollback trigger rather than a residual.

**Privacy exposure is created by the method itself**: Parametric answering can reproduce memorised training content, and reusable caches are sensitive derivatives of user input that have been shown vulnerable to reconstruction under published threat models [4][6][7]. The consequence is that adopting either route enlarges the privacy surface. The mitigation is canary and extraction testing on every model revision, cache confinement to a single tenant and authorization scope with encryption and secure eviction, rate limiting on divergence and repeated-prefix probing, and a hard refusal to share cache state across a trust boundary without a documented security validation. Deletion of a source record, a vector, or a cache entry must never be described as erasure of influence from model weights, and any claim of erasure requires legal and technical verification outside this framework.

***

## VI. Conclusion and Summary

Latent knowledge retrieval names a family rather than an architecture, and the first operational act in the method is to refuse the label as a specification. Seven senses hide behind it, they differ in what the latent object is and in what access it demands, and four of them are not reachable by an agent at runtime. The admissibility gate makes that distinction a recorded decision with a referral rather than a silent assumption, so a deployment either knows it is doing semantic retrieval over inspectable records or knows exactly which unmet requirement drove it elsewhere.

What remains after the gate is a source-eligibility discipline, and its central assertion is narrow: an answer produced from model weights is fast, cheap, and structurally unattributable, and the third property is not compensated by the first two. Hard rules therefore dispose of every claim carrying a citation obligation or cutoff exposure before any confidence signal is consulted, calibrated thresholds govern only the residue, and a generated identifier or a cache hit becomes usable only after it resolves to a canonical record that still exists. Conflicts between what the model recalls and what the record says are adjudicated by a declared authority order in which the record wins, and the deployment measures whether its model actually honours that order rather than assuming instruction tuning delivers it.

The execution tier partition is what keeps the discipline honest under load. Model inference proposes claims, labels, conflicts, and drafts; deterministic software owns every gate verdict, every fingerprint comparison, every citation resolution, and every budget. Where the two disagree, software wins, and no model output raises a budget, widens an authorization, or certifies its own support.

**Key Success Factors**:

- **Sense resolution before tooling**: Exactly one primary sense is admitted and recorded, every refusal carries a referral, and no design proceeds on the family label alone.
- **Hard rules before estimates**: Citation obligation, cutoff exposure, consequence class, and privacy are evaluated on typed metadata before any confidence signal is read, so no calibrated number can override a policy obligation.
- **Sealed holdout calibration**: Thresholds are fitted on development data only, evaluated once against a hashed holdout, and invalidated automatically by a model revision change.
- **Resolution before use**: Every generated identifier and every cache hit resolves to an active, authorized canonical record at a byte-identical fingerprint, and an artifact that fails resolution is discarded rather than repaired.
- **Unconditional non-citability marking**: Every parametric claim carries `citation_availability=false` and an unverified label, and no self-generated bibliography is ever admitted as provenance.
- **Coverage reported with accuracy**: Selective accuracy is reported jointly with coverage at declared operating points, worst-slice performance governs promotion, and a named risk owner sets the false-answer and false-abstention costs.

Applied consistently, the framework lets a deployment take the genuine cost and latency benefit of answering from model weights on the narrow set of claims where that is defensible, while making it structurally impossible for an unattributable answer to be mistaken for a supported one.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular phases. The external references that follow are transcribed from the originating prose guide as it cited them; except where an entry is explicitly marked as verified during conversion, they were not independently re-verified, and their titles and locations are reproduced rather than checked.

**Corpus pointers**:

- `Latent Knowledge Retrieval: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the seven-sense taxonomy, the sense-assignment default, the ordered use-decision rules, the infrastructure tier declaration, the run contract fields, the ten bounded loops with their evidence-gain and exit conditions, the reliability, provenance, freshness, and security sections, the evaluation corpus and metric inventory, and the logging schema. The external references listed below are transcribed from its inline citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/knowledge-retrieval/guide_AdvancedKnowledgeRetrieval.md` — owns the retrieval selection ladder, index construction, hybrid fusion, reranking, and provenance mechanics. This guide supplies the admission rule for that ladder's no-retrieval rung and does not restate the rungs above it.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — owns hypothetical document generation, step-back formulation, decomposition, and the rule that a generated abstraction is a retrieval instrument and never evidence, adopted here in Step 5.1.
- `advanced_task_guides/knowledge-retrieval/guide_SelfRAG.md` — owns the per-segment retrieval-need, relevance, support, and utility verdicts inside a generation loop, and the adjudicated-verdict pattern this guide's citation resolver follows.
- `advanced_task_guides/knowledge-retrieval/guide_CorrectiveRAG.md` — owns grading and repair of low-quality retrieved evidence, applicable where Step 5.1 admits a weak evidence set.
- `advanced_task_guides/knowledge-retrieval/guide_ModularRAG.md` — owns typed component contracts, registries, versioned manifests, and fallback boundaries, applicable to the route eligibility record in Step 1.3.
- `advanced_task_guides/knowledge-retrieval/guide_GraphRAG.md` — owns explicit entity, relation, path, and ontology substrates, applicable where a structured lookup outranks both routes in Step 4.1.
- `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md` — owns multi-step planning, tool orchestration, and trajectory controls for evidence acquisition beyond a single retrieval round.
- `advanced_task_guides/knowledge-retrieval/guide_MultimodalRAG.md` — owns evidence residing in images, layout, tables, audio, and video, applicable where a claim class's canonical record is not text.
- `advanced_task_guides/knowledge-retrieval/guide_HierarchicalIndexRetrieval.md` — owns parent-child expansion and hierarchical summarisation of a corpus, applicable to the evidence acquisition step.
- `advanced_task_guides/knowledge-retrieval/guide_CodebaseStructureRetrieval.md` — owns structural retrieval over symbol graphs and package indexes, applicable to the software engineering pattern in Section 4.1.
- `advanced_task_guides/knowledge-retrieval/guide_DeepResearchAgent.md` — owns open-ended investigation with no bounded query set, applicable where a claim class cannot be enumerated in advance.
- `advanced_task_guides/memory-management/guide_LatentMemoryNetworks.md` — owns embedding representation, representation fingerprints, index generations, migration, and erasure verification. This guide adopts its admissibility-gate and referral pattern and does not restate its index mechanics.

**External references**: The numbering below is the numbering used by the inline markers in Sections I, II, III, and V. Entries carrying no inline marker support material of the prose source that this operational restructuring did not retain as a separately attributable claim, principally the four senses refused at the agent layer.

*Knowledge cutoff, knowledge conflict, and source routing*

1. Jeffrey Cheng and colleagues, *Dated Data: Tracing Knowledge Cutoffs in Large Language Models* — https://arxiv.org/abs/2403.12958 (retrieved and verified during conversion; not carried by the originating prose guide)
2. *Knowledge Conflicts for LLMs: A Survey* — https://arxiv.org/abs/2403.08319 (retrieved and verified during conversion; not carried by the originating prose guide)
3. Ronak Pradeep et al., *How Does Generative Retrieval Scale to Millions of Passages?* — https://aclanthology.org/2023.emnlp-main.83/
4. Zhifan Luo et al., *Shadow in the Cache: Unveiling and Mitigating Privacy Risks of KV-cache in LLM Inference* — https://arxiv.org/abs/2508.09442
5. Sachin Goyal et al., *Context-Parametric Inversion: Why Instruction Finetuning May Not Actually Improve Context Reliance* — https://iclr.cc/virtual/2025/oral/31843
6. Nicholas Carlini et al., *Extracting Training Data from Large Language Models* — https://arxiv.org/abs/2012.07805
7. Milad Nasr et al., *Scalable Extraction of Training Data from (Production) Language Models* — https://arxiv.org/abs/2311.17035
8. Michael Duan et al., *Do Membership Inference Attacks Work on Large Language Models?* — https://arxiv.org/abs/2402.07841

*Semantic external retrieval, generative indexes, and selective retrieval*

9. Luyu Gao et al., *Precise Zero-Shot Dense Retrieval without Relevance Labels* — https://arxiv.org/abs/2212.10496
10. Yi Tay et al., *Transformer Memory as a Differentiable Search Index* — https://arxiv.org/abs/2202.06991
11. Di Wu et al., *Self-Routing RAG: Binding Selective Retrieval with Knowledge Verbalization* — https://arxiv.org/abs/2504.01018
12. Ha Lan N.T et al., *Latent Abstraction for Retrieval-Augmented Generation* — https://arxiv.org/abs/2604.17866
13. Fabio Petroni et al., *Language Models as Knowledge Bases?* — https://arxiv.org/abs/1909.01066

*Parametric answering, truthfulness, and uncertainty*

14. Stephanie Lin et al., *TruthfulQA: Measuring How Models Mimic Human Falsehoods* — https://arxiv.org/abs/2109.07958
15. Sebastian Farquhar et al., *Detecting Hallucinations in Large Language Models Using Semantic Entropy* — https://www.nature.com/articles/s41586-024-07421-0

*Compressed runtime state and cache-augmented generation*

16. Brian J. Chan et al., *Don't Do RAG: When Cache-Augmented Generation is All You Need for Knowledge Tasks* — https://arxiv.org/abs/2412.15605
17. Jesse Mu et al., *Learning to Compress Prompts with Gist Tokens* — https://arxiv.org/abs/2304.08467
18. Alexis Chevalier et al., *Adapting Language Models to Compress Contexts* — https://arxiv.org/abs/2305.14788
19. Peitian Zhang et al., *Long Context Compression with Activation Beacon* — https://arxiv.org/abs/2401.03462
20. Guillaume Lample et al., *Large Memory Layers with Product Keys* — https://arxiv.org/abs/1907.05242
21. Vincent-Pierre Berges et al., *Memory Layers at Scale* — https://arxiv.org/abs/2412.09764
22. Jiaru Zou et al., *Latent Collaboration in Multi-Agent Systems* — https://arxiv.org/abs/2511.20639

*Senses refused at the agent layer: internal probing, editing, and latent reasoning*

23. Alex Mallen et al., *Eliciting Latent Knowledge from Quirky Language Models* — https://arxiv.org/abs/2312.01037
24. Collin Burns et al., *Discovering Latent Knowledge in Language Models Without Supervision* — https://arxiv.org/abs/2212.03827
25. Samuel Marks and Max Tegmark, *The Geometry of Truth: Emergent Linear Structure in Large Language Model Representations of True/False Datasets* — https://arxiv.org/abs/2310.06824
26. Hoagy Cunningham et al., *Sparse Autoencoders Find Highly Interpretable Features in Language Models* — https://arxiv.org/abs/2309.08600
27. Andy Zou et al., *Representation Engineering: A Top-Down Approach to AI Transparency* — https://arxiv.org/abs/2310.01405
28. Alexander Matt Turner et al., *Steering Language Models With Activation Engineering* — https://arxiv.org/abs/2308.10248
29. Evan Hubinger et al., *Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training* — https://arxiv.org/abs/2401.05566
30. Kevin Meng et al., *Locating and Editing Factual Associations in GPT* — https://arxiv.org/abs/2202.05262
31. Kevin Meng et al., *Mass-Editing Memory in a Transformer* — https://arxiv.org/abs/2210.07229
32. Roi Cohen et al., *Evaluating the Ripple Effects of Knowledge Editing in Language Models* — https://arxiv.org/abs/2307.12976
33. Edward J. Hu et al., *LoRA: Low-Rank Adaptation of Large Language Models* — https://arxiv.org/abs/2106.09685
34. Oded Ovadia et al., *Fine-Tuning or Retrieval? Comparing Knowledge Injection in LLMs* — https://arxiv.org/abs/2312.05934
35. Shibo Hao et al., *Training Large Language Models to Reason in a Continuous Latent Space* — https://arxiv.org/abs/2412.06769

*Data-subject rights and erasure*

36. European Data Protection Board, *Effective Implementation of Data Subjects' Rights* — https://www.edpb.europa.eu/system/files/2025-01/d2-ai-effective-implementation-of-data-subjects-rights_en.pdf

