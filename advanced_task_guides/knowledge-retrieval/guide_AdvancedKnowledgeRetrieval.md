# Advanced Knowledge Retrieval

**Status**: Beta

**Change logs**:

- [09/08/2026] - Initialization

***

## Executive Summary

Advanced knowledge retrieval constitutes the task family of selecting, assembling, and proving out the retrieval architecture that a given answering task requires, rather than of implementing any one retrieval technique. This guide provides AI agents with a structured protocol that begins from a declared retrieval contract, builds a frozen evaluation set before any architecture is chosen, establishes the cheapest adequate baseline, attributes every observed failure to exactly one of four classes, and escalates along a cost-ordered ladder of retrieval methods only where a measured gap justifies the added expense. It specifies component-level metrics computed separately from end-to-end metrics, because a system can retrieve well and answer badly or answer well while retrieving badly, and only separated measurement distinguishes those states. It partitions the work across a deterministic tier that owns index construction, candidate retrieval, filtering, scoring arithmetic, budget enforcement, citation resolution, and metric computation, and a model tier that owns query interpretation, open-vocabulary relevance judgement, and answer synthesis. It emphasizes structured execution protocols, quality assurance checkpoints, and error handling procedures so that retrieval systems are promoted on evidence rather than on impression.

***

## I. Foundational Concepts and Definitions

### 1.1 Core Terminology

**Knowledge retrieval system**: The full path from an authorized source to a supported claim, comprising ingestion, indexing, query planning, candidate retrieval, ranking, evidence assembly, generation, and verification. The path, not the vector index, is the unit of design and of measurement.

**Retrieval contract**: The declared statement of what question class the system must answer, at what evidence standard, within what latency, cost, and freshness budget, and what an acceptable abstention looks like. The contract is fixed before any retrieval method is selected, and progress is judged against it rather than against impressions of answer quality.

**Evidence standard**: The rule stating what counts as support for a material claim, expressed as a required authority tier, a required number of independent sources, and a required citation granularity such as sentence, passage, page region, or table cell.

**Material claim**: An assertion in the answer whose falsity would change the reader's decision. Material claims require citation support; incidental phrasing does not.

**Admitted text**: The exact span of authorized source content placed into the generation context after filtering, deduplication, expansion, and ordering. A claim is supported only where its citation resolves to admitted text.

**Citation resolution**: The deterministic check that a citation key emitted by the generator maps to an evidence unit present in the admitted set, that the cited character or region offsets exist, and that the cited span is not a generated artifact such as a summary, a hypothetical document, or an inferred graph edge.

**Evaluation set**: A versioned collection of labelled cases, each carrying a query, the authoritative sources, the answer-bearing spans, an acceptable answer or a required abstention, a risk tier, and slice labels. It is split into a tuning portion and a frozen held-out portion.

**Answer-bearing span**: The character range in an original source document that contains the information required to answer a labelled case. Component-level retrieval metrics are computed against these spans, not against whole documents.

**Slice**: A named subset of the evaluation set sharing a property that retrieval methods treat differently, such as exact identifiers, multilingual queries, tables, recent updates, multi-hop questions, access-controlled documents, or adversarial inputs. Aggregate scores are reported alongside per-slice scores because an average conceals total failure on a slice.

**Selection ladder**: The cost-ordered sequence of retrieval architectures, from no retrieval through structured lookup, lexical retrieval, dense retrieval, hybrid fusion, reranking, query transformation, hierarchical indexing, corrective and self-critical loops, modular and agentic composition, graph-backed retrieval, multimodal retrieval, latent and memory-backed retrieval, and deep research agents. Each rung is admitted only against an observable condition measured on the prior rung.

**Failure class**: One of four mutually exclusive attributions for a failed case, defined in Section 1.4. Each class carries a different remedy, and retrieval quality expressed as one number cannot direct any of them.

**Rung admission trial**: A bounded comparison in which a candidate architecture is measured against the incumbent on the tuning portion of the evaluation set, with a declared improvement threshold, a declared cost ceiling, and a declared maximum number of tuning cycles.

**Index manifest**: The versioned record naming every component that can change results, including parser, chunker, embedding model, sparse analyzer, fusion parameters, reranker, graph schema, prompt template, generator, and policy version. Manifests make a retrieval result reproducible and a regression attributable.

**Provenance chain**: The unbroken link from source version to document to chunk to admitted text to cited claim. A break anywhere in the chain converts a supported claim into an unsupported one.

**Marginal evidence gain**: The increase in covered answer-bearing spans produced by one additional retrieval round, measured against the round's token, latency, and monetary cost. It is the stopping signal for every iterative retrieval loop.

**Abstention**: A declared terminal outcome in which the system states what is known, what is missing, and what would resolve the gap, rather than answering. An abstention permitted by the contract is not a failure.

**Drift**: A measured change in metric values attributable to a change in corpus composition, query distribution, model version, or policy, rather than to a change in the retrieval architecture.

### 1.2 The Execution Tier Partition

Retrieval systems fail most often at the boundary between what software must decide and what a model may decide. The partition below is binding on every phase of Section II, and every step names the tier that owns it.

**Deterministic tier**: Software, scripts, queries, schema validators, and APIs own everything that requires exactness, reproducibility, auditability, or scale. This tier constructs indexes and assigns stable identifiers; enforces tenant, access-control, validity-interval, and classification filters before ranking and again before context assembly; executes candidate retrieval against sparse, dense, graph, and structured stores; performs all scoring arithmetic including rank fusion, threshold comparison, deduplication, and diversity selection; enforces token, latency, monetary, round-count, and tool-call budgets; resolves every citation key against admitted text; and computes every metric reported in Sections II and III. Results produced by this tier are reproducible from the index manifest and the query.

**Model tier**: LLM calls own work requiring open-vocabulary judgement that no deterministic rule covers. This tier interprets an ambiguous query into an explicit information need; proposes rewrites, decompositions, and expansions; judges topical relevance and sufficiency beyond lexical overlap; adjudicates whether a passage entails a claim; and synthesises the answer. This tier never enforces authorization, never computes a score that a gate depends on, and never declares its own output supported.

**Hybrid tier**: Work where the model proposes and software verifies, or software retrieves and the model adjudicates. Query rewriting is a model proposal that a deterministic constraint checker accepts or rejects on entity, negation, date, unit, scope, and access-constraint preservation. Relevance grading is a model judgement over a deterministically retrieved candidate set whose membership the model may not extend. Answer synthesis is a model output whose citations a deterministic resolver admits or rejects.

**Authority on disagreement**: The deterministic tier holds authority in every conflict. Where a model judges a passage relevant that the policy filter excluded, the passage stays excluded. Where a model asserts a claim is supported but the citation does not resolve to admitted text, the claim is unsupported regardless of the model's stated confidence, and the system either retrieves again, qualifies the statement, or abstains.

**Tier Ownership by Artifact**:

| Artifact | Owning tier | Rejection rule enforced deterministically |
| :-- | :-- | :-- |
| Index manifest and chunk identifiers | Deterministic | Identifiers derived from array position are rejected |
| Access-control and validity filtering | Deterministic | Any candidate lacking a resolved policy decision is dropped |
| Candidate set and rank fusion | Deterministic | Fusion over score scales without a declared normalisation is rejected |
| Query interpretation and rewrite | Hybrid | A rewrite altering entity, negation, date, unit, or scope is rejected |
| Relevance and sufficiency grading | Hybrid | A grade over a candidate the model added itself is rejected |
| Evidence assembly and ordering | Deterministic | Expansion beyond the declared token cap is truncated at a section boundary |
| Answer synthesis | Model | Not applicable |
| Citation resolution | Deterministic | A citation not resolving to admitted text marks the claim unsupported |
| Metric computation and gate verdicts | Deterministic | A gate verdict produced by a model judge without a calibrated label set is rejected |

### 1.3 The Selection Ladder

The ladder orders retrieval architectures by total cost of ownership, counting index build cost, per-query latency, per-query monetary cost, operational surface, and the evidence burden required to keep the rung honest. Agents begin at the lowest rung whose measured performance satisfies the contract, and climb only where a named failure class, measured on the frozen evaluation set, is not remediable at the current rung.

**Climbing rule**: A rung is entered only where the dominant failure class on the incumbent architecture maps to that rung in the table below, the rung's admission trial shows at least a 5 percentage point improvement on the primary component metric for the affected slice, and the resulting latency and cost remain inside the contract budget. A rung entered without a measured gap is removed at the next release gate.

**Descending rule**: Where a higher rung is retained for a slice that a lower rung now satisfies, because a corpus change, a model change, or a chunking change closed the gap, the higher rung is retired. Complexity that no longer earns its place is a defect rather than a legacy.

**Retrieval Selection Ladder**:

| Rung | Architecture | Observable condition that justifies entry | Dominant added cost |
| :-- | :-- | :-- | :-- |
| 0 | No retrieval | All required information is present in the request; the task is transformational | None |
| 1 | Structured lookup | The answer is an exact record in a database, API, or rules engine | Connector maintenance |
| 2 | Lexical retrieval | Answers live in prose; identifiers, names, codes, and quotations dominate | Index build and analyzer tuning |
| 3 | Dense retrieval | Paraphrase and conceptual queries miss at the lexical rung | Embedding cost and reindex on model change |
| 4 | Hybrid sparse-dense fusion | Lexical-only and dense-only cohorts each carry unique wins | Dual index and fusion parameters |
| 5 | Reranking over a bounded pool | Answer-bearing spans are retrieved but ranked below the admitted cut | Per-query reranker latency and cost |
| 6 | Query transformation | Recall fails on conversational, underspecified, or multi-constraint queries | Extra model calls and rewrite validation |
| 7 | Hierarchical index retrieval | Precise matches lack the surrounding definitions needed to answer | Parent-child index and expansion caps |
| 8 | Corrective retrieval | A measurable share of retrievals is insufficient and detectable before generation | Grading calls and a bounded second round |
| 9 | Self-critical retrieval | Drafts carry unsupported claims that a critique pass detects reliably | Verification calls and regeneration |
| 10 | Modular composition | Distinct query classes need distinct pipelines and a router separates them | Router error surface and per-branch evaluation |
| 11 | Agentic retrieval | Multi-step evidence gathering with tool selection beats any single fixed plan | Loop budget, cycle detection, and non-determinism |
| 12 | Graph-backed retrieval | Multi-hop relations, entity disambiguation, or corpus-wide synthesis dominate | Extraction cost, schema maintenance, and audit burden |
| 13 | Multimodal retrieval | Answers depend on charts, layout, handwriting, audio, or table structure | Parsing services, region storage, and modality-specific attacks |
| 14 | Latent and memory-backed retrieval | Recurring workflows need durable derived state beyond the corpus | Write gates, consolidation, contradiction handling, and privacy exposure |
| 15 | Deep research agents | The task is an open-ended investigation with no bounded query set | Long-horizon budget, orchestration, and result variance |

**Lateral option**: Long-context routing is not a rung but an alternative to rungs 2 through 15 for requests whose authorized corpus fits below a tested occupancy threshold, initially 50 to 70 percent of the model context limit after reserving output and system tokens. It is selected per request by a router, never adopted as a permanent architecture, and it is compared on tokens, time to first token, end-to-end latency, cost, citation precision, and worst-slice reliability rather than on answer accuracy alone.

**Structured-corpus specialisation**: Where the corpus carries a machine-parseable structure such as a symbol graph, a database schema, or a filesystem hierarchy, the structural index is a substitute for rung 1 or rung 2 rather than an addition to them, because the structure supplies exact retrieval that similarity search only approximates. Codebase retrieval is the common instance: agents evaluate the structural path before any embedding path on such corpora.

### 1.4 The Failure Taxonomy

Every failed evaluation case is attributed to exactly one class. Attribution is deterministic, computed from the labelled answer-bearing spans, the logged candidate set, the admitted set, and the resolved citations. Classes are ordered so that the first matching condition wins.

**Class F1, retrieval miss**: The case is answerable from the authorized corpus, and no candidate returned by any retriever overlaps an answer-bearing span. The defect lies in the index, the chunking, the analyzer, the embedding, or the corpus itself. Remedies live at rungs 2, 3, 4, 6, 7, and 12, and at ingestion. Adding a reranker to an F1-dominated system cannot help, because the reranker never sees the missing passage.

**Class F2, ranking miss**: A candidate overlapping an answer-bearing span was retrieved but fell below the admitted cut. The defect lies in ranking, fusion, or cut depth. Remedies live at rungs 4 and 5, and in raising candidate pool depth within the budget. Expanding the corpus or replacing the embedding model in an F2-dominated system spends money on the wrong stage.

**Class F3, utilisation failure**: An answer-bearing span was present in the admitted text, and the answer nonetheless failed. The defect lies in context assembly, ordering, compression, evidence delimitation, token budgeting, or generation. Remedies include reordering so that the strongest evidence is not predictably buried mid-context, capping parent expansion, removing duplicate passages that crowd out diversity, preserving qualifications and negation through compression, and tightening the citation-constrained prompt. No retrieval change addresses F3.

**Class F4, unsupported success**: The answer was correct and no citation resolved to admitted text supporting it. The system answered from parametric knowledge, from a generated artifact such as a summary or a hypothetical document, or by chance. This class is invisible to correctness metrics, and it is the reason component metrics are computed separately from end-to-end metrics. Remedies are the citation resolution gate, the abstention path, and evaluation-set decontamination.

**Failure Class Attribution and Remedy Map**:

| Class | Deterministic attribution test | Rungs that can remedy it | Rungs that cannot |
| :-- | :-- | :-- | :-- |
| F1 retrieval miss | Zero candidates overlap an answer-bearing span | 2, 3, 4, 6, 7, 12, ingestion repair | 5, 9 |
| F2 ranking miss | Overlap exists in the candidate set, not in the admitted set | 4, 5, deeper candidate pool | 3 alone, 12 |
| F3 utilisation failure | Overlap exists in the admitted set, answer fails | Assembly, ordering, compression, prompt repair | Any retrieval rung |
| F4 unsupported success | Answer correct, zero resolving citations | Citation gate, abstention, decontamination | Any retrieval rung |

**Blocking defect, not a failure class**: An authorization defect, meaning any case in which unauthorized content reached the candidate set, the admitted set, the response, or a cache entry, halts all quality work until policy enforcement is repaired. It is never traded against a quality improvement and never carried as a known issue.

***

## II. Operational Framework: Contract-Bound Selection and Verification of a Retrieval Architecture

The framework produces one artifact: a retrieval architecture whose every component is justified by a measured gap, whose behaviour is reproducible from an index manifest, and whose quality is expressed as separated component and end-to-end metrics over a frozen evaluation set. Phases 1 through 5 run in order. Phase 6 runs continuously after release and returns control to Phase 4 when drift crosses a declared threshold.

### Phase 1: Retrieval Contract and Budget Declaration

**Objective**: Fix what the system must answer, at what evidence standard, and inside what budget, before any retrieval method is named, so that architecture selection is a measurement decision rather than a preference.

#### Step 1.1: Declare the Question Class and Evidence Standard

**Required Actions**:

- Enumerate the question classes the system must answer, each stated as a query pattern with an expected answer form, and mark every class the system is not required to answer.
- Name the authorized source boundary for each class, listing source systems, tenants, classifications, and the authority tier ordering that resolves conflicts between sources.
- State the evidence standard per class: the minimum authority tier admissible as support, the number of independent sources required for a material claim, and the citation granularity required, chosen from sentence, passage, page region, timestamp, or table cell.
- Declare the freshness service-level objective per source type, expressed as the maximum permitted lag between a source change and its visibility in retrieval results.
- Record the contract in structured state that a validator can read, rather than in prose, so that later gates evaluate the contract instead of interpreting it.

**Required Outputs**:

- A question class inventory with an answer form and an out-of-scope marker per class.
- A source boundary record naming systems, tenants, classifications, and the authority tier ordering.
- An evidence standard record carrying authority tier, source count, and citation granularity per class.
- A freshness objective table with one numeric lag limit per source type.

**Quality Checkpoints**:

- Every question class carries an evidence standard; a class without one halts the run before any index is built.
- Authority tier ordering is total, so that any two conflicting sources resolve deterministically.
- Every freshness objective carries a numeric limit in time units; an unbounded objective is rejected.
- The out-of-scope list is non-empty, because a contract that claims every question is answerable cannot be evaluated.

***

#### Step 1.2: Set the Latency, Cost, and Budget Envelope

**Required Actions**:

- Declare the p95 end-to-end latency budget and allocate it across planning, retrieval, fusion, reranking, assembly, generation, and verification, so that a stage overrun is attributable.
- Declare the monetary budget per answered request and the token budget for admitted context, counting retrieved-context tokens separately from input and output tokens.
- Declare the maximum retrieval rounds, generated query variants per round, tool calls, and verification rounds a single request may consume.
- Record the risk tier per question class, and set a tighter verification threshold and a lower autonomy ceiling for the highest tier.
- Register every budget dimension in a ledger the deterministic tier enforces at runtime, rather than as a design intention.

**Required Outputs**:

- A latency budget with a per-stage allocation summing to the declared p95 total.
- A cost budget stating monetary and token limits per answered request.
- A loop budget stating maximum rounds, variants, tool calls, and verification passes.
- A risk tier assignment covering every question class.

**Quality Checkpoints**:

- Every budget dimension carries a numeric limit; an unbounded dimension halts the run.
- The per-stage latency allocation sums to the declared total, with no unallocated remainder above 10 percent.
- The loop budget is enforceable by the deterministic tier without reference to model output.
- Highest-tier classes carry a stricter evidence standard than the lowest tier; identical thresholds across tiers are rejected as simultaneously too permissive and too costly.

***

#### Step 1.3: Define the Abstention Path and the Material-Claim Boundary

**Required Actions**:

- State the operational test that separates a material claim from incidental phrasing, so that citation coverage is computable rather than judged case by case.
- Define the abstention output form: what is known, what is missing, what source would resolve the gap, and what the requester may do next.
- Declare the conditions that require abstention, including an unresolved citation on a material claim in the highest risk tier, a required subquestion with no authoritative support, and exhaustion of the loop budget without sufficiency.
- State that a supported abstention is scored as a correct outcome rather than as a task failure, and record the abstention precision target.
- Declare the human escalation path, naming the evidence bundle attached and the role that receives it.

**Required Outputs**:

- A material-claim test statable as a deterministic rule over the answer's atomic claims.
- An abstention template with named fields.
- An abstention trigger list with one condition per line.
- An escalation specification naming the receiving role and the attached artifacts.

**Quality Checkpoints**:

- The material-claim test partitions every claim in a sample answer without leaving an unclassified remainder.
- Abstention is representable in the evaluation set as a required outcome, not only as a fallback.
- Every abstention trigger names a measurable condition rather than a judgement of confidence.
- The escalation bundle carries the trace identifier and the admitted evidence, so a reviewer can reproduce the decision.

***

### Phase 2: Corpus Preparation and Evaluation Set Construction

**Objective**: Produce an authorized, provenance-complete corpus and a frozen labelled evaluation set, so that every later architecture decision is justified by measurement rather than by preference.

#### Step 2.1: Establish the Corpus and Provenance Contract

**Required Actions**:

- Admit only approved sources through authenticated connectors, and validate type, size, and content hash before parsing.
- Parse into a canonical representation that preserves headings, section paths, page and region coordinates, tables, captions, and modality, retaining the original artifact or an immutable pointer to it.
- Extract security labels, tenant identity, access-control principals, classification, retention policy, and validity interval before chunk creation, never after it.
- Assign document and chunk identifiers derived from source identity, source version, and offsets, and reject any identifier derived from array position.
- Deduplicate exact copies by hash and near-duplicates by a reviewed threshold, keeping one canonical version with provenance links to the rest.
- Quarantine malformed, unsigned, unlabelled, or policy-violating documents rather than indexing them partially.
- Record an index manifest for every build, and propagate deletion to the text index, vector index, graph, caches, evaluation samples, and backups under the declared retention policy.

**Required Outputs**:

- A corpus manifest naming sources, versions, parser version, and document counts.
- A per-chunk provenance record carrying source, version, offsets, section path, modality, language, and policy labels.
- A quarantine register naming every rejected document and its rejection reason.
- A deletion propagation record listing every derivative store and its confirmation state.

**Quality Checkpoints**:

- Required access-control fields are present on 100 percent of indexed chunks; any gap halts the build.
- Stable source links resolve for 100 percent of sampled chunks, so that every retrieved passage traces to an original.
- Parse success reaches at least 99 percent for supported formats, with the remainder explicitly quarantined rather than silently dropped.
- Zero cross-tenant identifier collisions are observed in the sampled build.
- Sampled chunks are human-readable and traceable to their originals without reference to the index.

***

#### Step 2.2: Construct the Frozen Evaluation Set

**Required Actions**:

- Label each case with a query, the conversation context where applicable, the requesting identity and tenant, the authoritative sources, the answer-bearing spans at character granularity, an acceptable answer or a required abstention, a risk tier, and slice labels.
- Populate every case category in the composition table below, including categories whose expected outcome is an abstention or a refusal.
- Draw real production examples under the applicable privacy policy, and add synthetic edge cases only where a real example is unobtainable.
- Include hard negatives drawn from the same entity, time period, or terminology as the positive case, so that ranking quality is separable from topical proximity.
- Split the set into a tuning portion and a held-out regression portion, freeze the held-out portion before any architecture trial begins, and version both.

**Evaluation Set Composition Minimums**:

| Case category | Purpose | Minimum count |
| :-- | :-- | :-- |
| Answerable single-hop | Establishes the baseline recall floor | 40 |
| Answerable multi-hop | Detects decomposition and relation gaps | 20 |
| Exact identifier or quotation | Detects lexical analyzer regressions | 20 |
| Unanswerable from the corpus | Measures abstention precision | 20 |
| Contradictory or superseded sources | Measures conflict handling and temporal correctness | 15 |
| Stale or recently updated | Measures freshness compliance | 15 |
| Access-controlled negative | Measures authorization enforcement | 15 |
| Adversarial or injected content | Measures instruction-following resistance | 15 |

**Required Outputs**:

- A versioned evaluation set of at least 160 labelled cases meeting every category minimum.
- A slice label inventory naming at least 8 slices, each carrying at least 20 cases.
- A frozen held-out split comprising at least 40 percent of cases, with its hash recorded.
- A labelling provenance record naming who or what produced each label and how disagreements were resolved.

**Quality Checkpoints**:

- Every case carries at least one answer-bearing span or an explicit unanswerable marker; a case with neither is removed.
- No slice carries fewer than 20 cases, below which a 5 percentage point difference is not separable from noise.
- The held-out split is frozen and hashed before the first architecture trial, and no tuning run reads it.
- Access-controlled negatives are labelled with the identity under which they must not be retrieved, not merely as forbidden documents.

***

#### Step 2.3: Certify the Evaluation Set Against Contamination

**Required Actions**:

- Test whether a generator with no retrieved evidence answers cases correctly, and mark every case it answers as parametrically contaminated.
- Reclassify contaminated cases into a separate diagnostic slice, and exclude them from correctness gates while retaining them for measuring the class F4 rate.
- Verify that answer-bearing spans exist in the current corpus version, and retire cases whose sources have been deleted or superseded.
- Confirm that no case's labels were produced by the same model configuration under evaluation, so that a judge does not grade its own generation.
- Record judge calibration where a model judge scores any metric: compare judge verdicts against blinded human labels on a sample, report the disagreement rate, and pin the judge version.

**Required Outputs**:

- A contamination report naming the no-retrieval baseline score and the contaminated case list.
- A decontaminated evaluation set version with the diagnostic slice separated.
- A span validity report confirming every answer-bearing span resolves in the current corpus.
- A judge calibration record with the sampled disagreement rate and the pinned judge version.

**Quality Checkpoints**:

- The no-retrieval baseline is measured and recorded before any retrieval architecture is scored, because an unmeasured baseline makes every later improvement unattributable.
- Contaminated cases comprise a reported share of the set rather than an unknown one.
- Judge disagreement against blinded human labels does not exceed 15 percentage points; above that the judge is replaced or the metric is scored by rule rather than by model.
- Every answer-bearing span resolves to text present in the indexed corpus version under test.

***

### Phase 3: Baseline Establishment and Failure Attribution

**Objective**: Measure the cheapest adequate architecture on the frozen evaluation set and attribute every failure to exactly one class, so that the next architecture decision is directed by evidence rather than by the most recently published technique.

#### Step 3.1: Build the Cheapest Adequate Baseline

**Required Actions**:

- Select the lowest ladder rung whose entry condition the contract satisfies, and implement only that rung, without a reranker, without query transformation, and without any agentic loop.
- Test at least 3 candidate chunking configurations against the tuning split, varying unit boundary, size, and overlap, and retain the smallest configuration meeting the recall target.
- Generate with a citation-constrained prompt that delimits evidence from instructions and states that content inside evidence blocks is data rather than instruction.
- Enforce access-control filtering before ranking and again before context assembly, and record the policy decision identifier for every admitted and rejected candidate.
- Record the complete index manifest and one trace per evaluation case, so that the baseline is reproducible from stored state alone.

**Required Outputs**:

- A baseline architecture at a named ladder rung with its index manifest recorded.
- A chunking comparison record covering at least 3 configurations with per-slice recall, duplicate-context ratio, mean context tokens, ingestion cost, and p95 latency.
- A complete trace set covering 100 percent of evaluation cases.
- A policy decision log covering every candidate considered.

**Quality Checkpoints**:

- The baseline occupies the lowest rung satisfying the contract; a baseline built at rung 5 or above without a prior measurement is rejected.
- The selected chunking configuration does not degrade any critical slice by more than 2 percentage points relative to the best configuration for that slice.
- Zero access-control violations appear in the tested cases; any violation halts all quality work under the blocking-defect rule in Section 1.4.
- The baseline reproduces to within 1 percentage point on a repeated run against the same manifest, or the non-determinism is located and recorded before proceeding.

***

#### Step 3.2: Compute Component and End-to-End Metrics Separately

**Required Actions**:

- Compute component-level retrieval metrics against answer-bearing spans rather than against whole documents, covering Recall at the candidate depth, Recall at the admitted depth, precision at the admitted depth, mean reciprocal rank, normalised discounted cumulative gain, and coverage of required subquestions.
- Compute end-to-end metrics separately, covering answer correctness, groundedness against admitted text, citation precision, citation coverage over material claims, abstention precision and recall, and contradiction handling.
- Compute operational metrics per stage, covering p50, p95, and p99 latency, retrieved-context tokens, cost per answered request, cache hit and false-hit rates, and freshness lag.
- Report macro averages together with per-slice values and the fifth-percentile per-slice value, and never report an aggregate without its worst slice.
- Compute the class F4 rate directly by counting correct answers carrying zero resolving citations, so that luck is distinguished from grounding.

**Required Outputs**:

- A component metric report with per-slice values for every retrieval metric.
- An end-to-end metric report with per-slice values for every generation and citation metric.
- An operational metric report with per-stage latency and cost.
- A worst-slice summary naming the lowest-scoring slice for each metric family.

**Quality Checkpoints**:

- Component and end-to-end metrics are reported as separate families; a single combined quality figure is rejected.
- Every metric carries both a macro average and a per-slice breakdown.
- The class F4 rate is reported explicitly rather than folded into correctness.
- The measured access-control violation rate is exactly zero; a non-zero rate halts the phase.

***

#### Step 3.3: Attribute Every Failure to Exactly One Class

**Required Actions**:

- Apply the deterministic attribution tests in Section 1.4 in order, assigning each failed case to the first matching class.
- Aggregate class counts per slice, and identify the dominant class overall and the dominant class within each critical slice.
- Separate cases that fail because the corpus does not contain the answer from class F1, and route them to ingestion rather than to retrieval, since no ranking change can retrieve absent content.
- Record every case that resists attribution, and cap the unattributed share, since an unattributed remainder conceals the defect that the next phase must target.
- Publish the attribution table as the sole input to architecture selection in Phase 4, so that no rung is proposed without a class it addresses.

**Required Outputs**:

- A failure attribution table with one row per class and one column per slice.
- A dominant class statement for the overall set and for each critical slice.
- A corpus gap list naming cases whose answer is absent from the authorized corpus.
- An unattributed case list with the reason each resisted classification.

**Quality Checkpoints**:

- Every failed case carries exactly one class or appears on the unattributed list; a case in two classes indicates the attribution tests were applied out of order.
- Unattributed cases do not exceed 5 percent of failures; above that the attribution logic is repaired before Phase 4 begins.
- Corpus gaps are separated from class F1, since their remedy is ingestion rather than retrieval.
- The dominant class is stated per critical slice, not only in aggregate, because a slice-level dominant class often differs from the overall one.

***

### Phase 4: Architecture Selection Against Measured Gaps

**Objective**: Choose the next ladder rung from the measured failure attribution, prove its value in a bounded trial, and admit it only where the improvement, the latency, and the cost all clear declared thresholds.

#### Step 4.1: Map the Dominant Failure Class to a Ladder Rung

**Required Actions**:

- Read the dominant class per slice from the Phase 3 attribution table, and select candidate rungs only from the remedy column of the failure map in Section 1.4.
- Reject every candidate rung whose remedy column excludes the dominant class, and record the rejection with the class that disqualified it.
- Where the dominant class is F3, route the work to context assembly, ordering, compression, or prompt repair, and select no retrieval rung at all.
- Where the dominant class is F4, route the work to the citation gate, the abstention path, and evaluation-set decontamination, and select no retrieval rung at all.
- Where two slices carry different dominant classes and their remedies conflict, prefer a modular route that applies each remedy to its own query class over a single compromise architecture.
- State, before the trial begins, the primary component metric the rung is expected to move and the slice on which the movement must appear.

**Required Outputs**:

- A candidate rung shortlist of no more than 3 entries, each mapped to the class it remedies.
- A rejection record naming every excluded rung and its disqualifying class.
- A declared success hypothesis naming the primary metric, the target slice, and the expected direction.

**Quality Checkpoints**:

- Every shortlisted rung appears in the remedy column of the dominant class; a rung selected outside that column is rejected without trial.
- The shortlist contains no more than 3 entries, above which trial cost exceeds the value of the comparison.
- The success hypothesis names one primary metric and one target slice, so that a trial cannot be declared successful on a metric chosen after the result.
- No retrieval rung is shortlisted where the dominant class is F3 or F4.

***

#### Step 4.2: Run the Bounded Admission Trial

**Required Actions**:

- Implement each shortlisted rung as a variant of the baseline, holding the corpus version, the chunking configuration, the prompt, and the generator constant, so that the measured difference is attributable to the rung alone.
- Run every variant against the tuning split only, and never against the frozen held-out split.
- Cap tuning cycles at 5 per proposed change; after the fifth cycle, reformulate the hypothesis rather than continuing, since further cycles overfit the tuning split.
- Measure the same component, end-to-end, and operational metric families computed in Step 3.2, at the same slice granularity.
- Record for each variant the latency delta per stage, the token delta for admitted context, and the monetary delta per answered request.
- Re-run the attribution in Step 3.3 on each variant, so that a rung which converts F1 failures into F2 failures is visible as a partial remedy rather than as a success.

**Required Outputs**:

- A per-variant metric report at the same slice granularity as the baseline.
- A per-variant cost and latency delta record.
- A post-trial attribution table per variant showing the class distribution after the change.
- A tuning cycle log recording each cycle's change and its result.

**Quality Checkpoints**:

- The frozen held-out split was not read during any trial; a read of the held-out split invalidates the trial and requires a new split.
- Exactly one component differs between each variant and the baseline; multiple simultaneous changes make the result unattributable.
- Tuning cycles per change do not exceed 5; the sixth cycle halts the trial and returns to hypothesis formulation.
- Post-trial attribution is computed for every variant, so that class conversion is distinguished from class elimination.

***

#### Step 4.3: Admit or Reject the Rung Against the Budget

**Required Actions**:

- Admit a rung only where it improves the declared primary metric on the declared target slice by at least 5 percentage points, degrades no critical slice by more than 2 percentage points, and leaves p95 latency and cost per answered request inside the Phase 1 budget.
- Confirm the improvement on the frozen held-out split once, after admission on the tuning split, and reject the rung where the held-out improvement falls below half the tuning improvement.
- Reject any rung whose benefit appears only in the aggregate while a critical slice, a security metric, a freshness metric, or a tail-latency metric regresses.
- Record the admitted rung in the index manifest together with its justification, naming the failure class, the slice, the measured delta, and the trial identifier.
- Return to Step 4.1 with the post-admission attribution table where the contract is still unmet, and stop climbing where every class is inside target.

**Required Outputs**:

- An admission decision record per candidate rung, carrying the verdict and the measured deltas.
- An updated index manifest naming the admitted architecture and its justification.
- A held-out confirmation record for every admitted rung.
- A residual gap statement naming the classes still outside target and the slices in which they appear.

**Quality Checkpoints**:

- Every admitted rung carries a recorded failure class, target slice, and measured delta; a rung admitted without them is removed.
- No admitted rung degrades a critical slice by more than 2 percentage points.
- Held-out improvement reaches at least half the tuning improvement; a smaller ratio indicates tuning-split overfitting and rejects the rung.
- The architecture climbs at most one rung per admission cycle, so that attribution remains possible.

***

### Phase 5: Assembly, Citation Enforcement, and Loop Bounding

**Objective**: Convert an admitted candidate set into an evidence bundle whose every claim resolves to admitted text, and bound every iterative path so that the system terminates through a declared exit rather than through exhaustion.

#### Step 5.1: Assemble the Evidence Bundle Under Deterministic Control

**Required Actions**:

- Remove inaccessible, expired, quarantined, and superseded chunks before any ranking result is shown to a model, and recheck the policy decision immediately before assembly because identity, policy, or document state may have changed since retrieval.
- Deduplicate exact and near-duplicate passages, and preserve source diversity where the evidence standard requires corroboration from independent sources.
- Expand only the parent section or sentence window needed to interpret the matched span, capping expansion by a declared token limit and stopping at a section boundary.
- Detect contradictions in dates, versions, and asserted values, and retain both sides where the conflict is material rather than silently selecting one.
- Allocate the admitted token budget by subquestion and evidence priority, and order units so that the strongest evidence is not predictably placed mid-context.
- Attach a machine-readable citation key to every evidence unit, delimit evidence from instructions, and mark evidence content as untrusted data that never carries instructions.
- Apply compression only where evidence is relevant but verbose, and never to legal clauses, safety constraints, numeric tables, or code unless a verified lossless representation exists.

**Evidence Bundle Record**:

```
BUNDLE_ID:
TRACE_ID:
POLICY_VERSION:
INDEX_MANIFEST:
UNITS:
  - CITATION_KEY:
    CHUNK_ID:
    SOURCE_ID:
    SOURCE_VERSION:
    OFFSETS:
    SECTION_PATH:
    MODALITY:
    AUTHORITY_TIER:
    VALID_FROM:
    VALID_TO:
    POLICY_DECISION_ID:
    EXPANSION_TOKENS:
    CONTENT_HASH:
ADMITTED_TOKENS:
DROPPED_UNITS_WITH_REASON:
CONTRADICTION_PAIRS:
UNTRUSTED_CONTENT_FLAG:
```

**Required Outputs**:

- An evidence bundle record populated for every field named in the template.
- A dropped-unit register naming each removed candidate and its removal reason.
- A contradiction register naming retained conflicting pairs.
- An ordering record stating the position assigned to each unit and the rule that assigned it.

**Quality Checkpoints**:

- Every admitted unit carries a resolved policy decision identifier dated at or after the assembly time.
- Admitted tokens do not exceed the Phase 1 context budget; an overrun truncates at a section boundary rather than mid-unit.
- Duplicate-context ratio stays inside the value measured for the selected chunking configuration.
- The untrusted-content flag is set for every unit whose text originates outside the system's own policy documents.

***

#### Step 5.2: Enforce Citation Resolution and the Abstention Path

**Required Actions**:

- Split the draft answer into atomic claims, classify each as material or incidental using the Step 1.3 test, and map each material claim to its citation keys.
- Resolve every citation key deterministically against the evidence bundle, confirming the key exists, the offsets exist, and the cited unit is original source content rather than a generated summary, a hypothetical document, or an inferred graph edge.
- Mark as unsupported every material claim whose citation fails to resolve, regardless of the generator's stated confidence, and never accept model assertion as a substitute for resolution.
- Adjudicate entailment for resolved citations, checking that the cited span supports the specific claim rather than merely sharing its topic.
- For unsupported or contradicted material claims, retrieve once more using the claim and its missing qualifier, and regenerate only the affected passage.
- Where unsupported material claims remain in the highest risk tier, abstain using the Step 1.3 template and attach the trace and evidence bundle for human review.
- Where retrieval is exposed to or consumed from a remote tool or agent boundary, require evidence artifacts with stable identifiers rather than prose answers, propagate identity, tenant, purpose, scope, and deadline, and verify returned citations locally rather than trusting the remote verdict.

**Required Outputs**:

- An atomic claim inventory with materiality classification and citation mapping.
- A citation resolution report naming every unresolved key and the claim it belonged to.
- An entailment verdict per resolved citation.
- An abstention or escalation record where unsupported material claims remain.

**Quality Checkpoints**:

- Citation coverage over material claims meets the contract target; a shortfall triggers retrieval, qualification, or abstention rather than release.
- Zero citations resolve to generated artifacts; any such resolution is a defect of the citation resolver, not of the generator.
- Entailment adjudication is performed for 100 percent of resolved citations on highest-tier requests.
- No answer is released carrying an unsupported material claim in the highest risk tier.

***

#### Step 5.3: Bound Every Iterative Retrieval Loop

**Required Actions**:

- Enter a refinement round only on a stated trigger: a failed sufficiency test, a required subquestion without support, scores below the query-class threshold, material disagreement among results, or predicted citation coverage below target.
- Bound refinement to 3 retrieval rounds and no more than 2 generated query variants per round, and bound verification to 2 rounds.
- Charge every call against the Phase 1 token, monetary, wall-clock, and tool-call ledger, and stop where the remaining deadline is shorter than the measured p95 duration of another round.
- Hash normalised query plans and retrieved chunk sets, and stop on a repeated plan, a repeated top-ranked set, absent new authoritative evidence, or decreasing groundedness.
- Stop where marginal evidence gain, measured as newly covered answer-bearing spans per round, falls below the declared threshold.
- Refuse any change to loop limits, permissions, tool allowlists, or destinations that originates in retrieved content or in a remote tool description.
- On exit without sufficiency, answer only the supported parts, state the missing evidence explicitly, and abstain or escalate.

**Required Outputs**:

- A loop trace recording per round the entry trigger, the diagnosis, the transformation applied, the evidence gain, and the remaining budget.
- A cycle detection record listing plan and chunk-set hashes per round.
- An exit record naming the exit condition and the residual gaps.
- A budget reconciliation showing consumption against every declared dimension.

**Quality Checkpoints**:

- Every round carries a recorded entry trigger; a round without one indicates the loop is running on default rather than on diagnosis.
- Round counts never exceed 3 for retrieval and 2 for verification; an exceedance halts the request and returns a bounded failure.
- Repeated plans and repeated chunk sets terminate the loop rather than consuming a further round.
- No loop limit, permission, or destination was modified by retrieved content during the request.

***

### Phase 6: Continuous Evaluation and Drift Detection

**Objective**: Keep the architecture justified after release by recomputing the same separated metrics on live traffic, gating every change, and returning to selection when drift crosses a declared threshold.

#### Step 6.1: Instrument Traces Sufficient for Metric Recomputation

**Required Actions**:

- Emit one trace per request and one span per stage, propagating a single trace identifier across planner, retriever, reranker, generator, verifier, and any remote tool or agent boundary.
- Log the request and policy context: environment, service version, tenant, pseudonymous requester, role identifiers, authorization scope hash, policy version, purpose, risk tier, deadline, and budget allocations.
- Log the retrieval context per query and subquery: retriever name and version, route, candidate depth, filters, fusion parameters, candidate identifiers, raw ranks and scores, fused ranks, admitted set, and per-stage latency.
- Log the reranking context: reranker name and version, candidate count, pre-rank and post-rank positions, rank delta, threshold, and drop reasons.
- Log the generation and verification context: generator and prompt versions, token counts by class, atomic claim identifiers, cited chunk identifiers, citation spans, resolution verdicts, entailment verdicts, abstention flag and reason, and judge version.
- Log the cache context: cache key hash, tier, hit or miss, entry age, manifest match, and reauthorization verdict, so that a cached answer is never counted as a fresh one.
- Redact by default, logging a query hash and token counts rather than raw text unless an explicit content-logging policy permits otherwise.

**Required Outputs**:

- A trace schema covering every field family named above.
- A per-request trace store from which every Phase 3 metric can be recomputed without re-running retrieval.
- A redaction policy record naming which fields are stored raw and under what authority.

**Quality Checkpoints**:

- Every Phase 3 metric is recomputable from stored traces alone; a metric requiring re-execution is not instrumented.
- Trace identifiers propagate across 100 percent of remote tool and agent boundaries.
- No raw query text or retrieved content is stored outside the declared content-logging policy.
- Cache hits are distinguishable from fresh retrievals in every trace.

***

#### Step 6.2: Operate the Release Gate

**Required Actions**:

- Trigger the gate on any change to parser, chunker, embedding model, index, fusion, reranker, prompt, generator, policy, source mix, or infrastructure.
- Run the gate in stages: unit and smoke tests with authorization checks first, the full offline suite by slice second, shadow traffic third, and a canary at a small authorized share with automatic rollback fourth.
- Apply hard gates that no aggregate improvement overrides: zero access-control violations, zero citations resolving to the wrong source in the critical set, no groundedness regression beyond the declared tolerance, no p95 latency budget breach, and no result staler than its source freshness objective.
- Compare candidate against baseline by slice, reporting paired deltas and, where sample size permits, confidence intervals, and store both run identifiers with their manifests and seeds.
- Reject or redesign any change that improves the aggregate while violating a security, freshness, high-risk quality, or tail-latency gate.
- Run index and model migrations in shadow against the same query set before cutover, and never overwrite an index in place without a rollback manifest.

**Required Outputs**:

- A gate result record per stage with a pass or fail verdict and the measured values.
- A paired comparison report against the production baseline by slice.
- A rollback manifest for every index, model, parser, or schema migration.
- An approval decision record naming the approver role and the evidence considered.

**Quality Checkpoints**:

- Every hard gate returns a pass before promotion; a single hard-gate failure blocks release regardless of aggregate gains.
- Slice-level regressions are reported even where the aggregate improves.
- Every migration carries a rollback manifest verified by an executed restore test.
- No promotion occurs on shadow or canary evidence alone without the offline suite having passed.

***

#### Step 6.3: Detect Drift and Re-enter Selection

**Required Actions**:

- Recompute the separated metric families on a sampled share of production traffic at a fixed cadence, and on the frozen evaluation set at every release.
- Alert on worst-slice recall falling by 5 percentage points or more, citation coverage falling by 3 percentage points or more, abstention precision falling below its target, freshness compliance falling below its objective, or any non-zero access-control violation.
- Distinguish drift from regression by checking whether the index manifest changed: an unchanged manifest with degraded metrics indicates corpus or query distribution drift rather than an architecture defect.
- Sample failed and abstained requests for adjudication, and convert every confirmed failure into a new evaluation case, refreshing the frozen split on a declared schedule rather than continuously.
- Re-enter Phase 4 with a fresh attribution table when drift persists across 2 consecutive measurement windows, and retire any rung whose remedied class has disappeared.
- Recompute every numeric threshold in this guide per deployment when source mix, requester behaviour, or model versions change, since the values here are starting points rather than constants.

**Required Outputs**:

- A drift report per measurement window with per-slice metric trends.
- A drift-versus-regression classification for every alert.
- An evaluation set growth record naming added cases and their originating failures.
- A rung retirement record for architectures no longer justified.

**Quality Checkpoints**:

- Every alert carries a drift or regression classification before remediation begins.
- The frozen split is refreshed on a schedule and re-frozen, never edited in place during an active trial.
- Rungs whose remedied class has fallen below 2 percent of failures for 2 consecutive windows are proposed for retirement.
- Threshold recalibration is recorded with its evidence, so that a changed number is auditable.

***

## III. Implementation Guidance for AI Agents

AI agents building and operating knowledge retrieval systems must follow systematic protocols ensuring that every architectural component is justified by a measured failure class, that authorization is enforced by software rather than by judgement, and that no claim is released whose citation does not resolve to admitted text. The following guidance translates the selection and verification framework into agent-executable instruction.

### A. Structured Execution Protocol

**Control Plane Components**:

1. **Contract Agent**: Owns the retrieval contract, the evidence standard, the budget ledger, and the abstention specification. It alone may amend a contract term, and every amendment is versioned. It refuses architecture work against an incomplete contract.
2. **Corpus and Index Agent**: Owns ingestion, parsing, chunking, identifier assignment, policy label extraction, index builds, manifests, deletion propagation, and quarantine. It operates entirely in the deterministic tier and never consults a model for an admission decision.
3. **Evaluation Agent**: Owns the labelled evaluation set, the frozen split, the contamination report, judge calibration, and all metric computation. It holds the only read path to the frozen split and refuses reads during an active trial.
4. **Retrieval Executor**: Runs candidate retrieval, filtering, fusion, reranking, and assembly for exactly one request or one trial variant. It may not change the architecture, extend a loop budget, or admit a candidate lacking a policy decision.
5. **Adjudication Agent**: Performs open-vocabulary judgement, covering query interpretation, rewrite proposal, relevance and sufficiency grading, and entailment verdicts. It operates in the model tier, may not extend a candidate set, and may not declare its own output supported.
6. **Verification and Metrics Agent**: Resolves citations, computes failure attribution, evaluates hard gates, and writes the trace record. It may veto a release and may veto a log emission that breaches the redaction policy.

**Workflow Execution Pattern**:

```
STATE: Rung_Admission_Trial
INPUTS:
  1. Failure attribution table from Step 3.3
  2. Candidate rung shortlist and success hypothesis from Step 4.1
  3. Frozen index manifest and tuning split identifier
ACTIONS:
  1. Instantiate one variant per shortlisted rung, one component changed
  2. Execute the tuning split against each variant
  3. Compute component, end-to-end, and operational metric families
  4. Recompute failure attribution per variant
  5. Compute latency, token, and cost deltas per variant
VALIDATION:
  - held_out_split_reads == 0
  - components_changed_per_variant == 1
  - tuning_cycles_for_change <= 5
  - acl_violations == 0
  - primary_metric_named_before_trial == TRUE
TRANSITIONS:
  IF best_variant_delta >= 5.0 AND worst_critical_slice_delta >= -2.0
     AND p95_latency <= budget AND cost_per_answer <= budget
     THEN next_state = Held_Out_Confirmation
  IF best_variant_delta < 5.0 THEN next_state = Hypothesis_Reformulation
  IF acl_violations > 0 THEN next_state = Authorization_Remediation
  IF validation_failed THEN next_state = Trial_Error_Handling
```

**Two-Phase Action Pattern**: Emit the proposed architecture change with its failure class, target slice, primary metric, and expected delta before any index is built or any endpoint is provisioned; confirm the proposal against the validation block while no resource is committed; execute the trial only after validation passes, and write the admission decision in the same operation that updates the manifest.

**Approval Gate**: Human authorisation is required before promotion of any change that raises cost per answered request by more than 20 percent, before any index or embedding migration without an executed rollback restore test, before any relaxation of an evidence standard or an abstention trigger, and before any exposure of a retrieval capability across an organisational trust boundary. Any non-zero access-control violation halts promotion and escalates immediately rather than proceeding with a recorded warning.

**Context Management Requirements**:

- Hold the contract, budget ledger, index manifest, and attribution table in durable state, since a selection cycle spans more work than one context window holds.
- Process the evaluation set in bounded batches, writing per-case results to durable storage rather than accumulating them in working context.
- Summarise superseded trial results to their metric rows once the admission decision is recorded, retaining run identifiers and discarding per-case bulk.
- Write a handoff record at every context boundary naming the contract version, the current rung, the attribution table, the open hypothesis, and the remaining budget.

### B. Quality Assurance Checkpoints

**Checkpoint 1: Contract Completeness (After Phase 1)**

- **Automated Check**: Every question class carries an evidence standard and a risk tier; every budget dimension carries a numeric limit; the per-stage latency allocation sums to the declared total with no more than 10 percent unallocated; the abstention template and trigger list are populated.
- **Agent Action on Pass**: Proceed to corpus preparation.
- **Agent Action on Failure**: Halt and return the incomplete contract term; no index is built against an incomplete contract.
- **Human Review Trigger**: Any question class in the highest risk tier whose evidence standard cannot be stated as a deterministic rule.

**Checkpoint 2: Corpus and Evaluation Readiness (After Phase 2)**

- **Automated Check**: Required access-control fields present on 100 percent of chunks; parse success at or above 99 percent with the remainder quarantined; at least 160 labelled cases meeting every category minimum; at least 8 slices with at least 20 cases each; frozen split hashed at or above 40 percent of cases; contamination report produced.
- **Agent Action on Pass**: Proceed to baseline establishment.
- **Agent Action on Failure**: Return the deficient category or field; labelling continues before any architecture work begins.
- **Human Review Trigger**: Contaminated cases exceeding 25 percent of the set, or judge disagreement above 15 percentage points against blinded human labels.

**Checkpoint 3: Baseline and Attribution Validity (After Phase 3)**

- **Automated Check**: Baseline occupies the lowest satisfying rung; component and end-to-end metrics reported separately with per-slice values; access-control violations at zero; unattributed failures at or below 5 percent; class F4 rate reported explicitly.
- **Agent Action on Pass**: Proceed to architecture selection.
- **Agent Action on Failure**: Repair attribution logic or instrumentation; selection is not attempted against an incomplete attribution table.
- **Human Review Trigger**: Any non-zero access-control violation, or a class F4 rate above 20 percent indicating widespread evaluation contamination.

**Checkpoint 4: Admission Validity (After Phase 4)**

- **Automated Check**: Exactly one component changed per variant; held-out reads at zero during tuning; tuning cycles at or below 5 per change; admitted rungs improving the declared primary metric by at least 5 percentage points with no critical slice degraded by more than 2; held-out improvement at least half the tuning improvement.
- **Agent Action on Pass**: Proceed to assembly and enforcement.
- **Agent Action on Failure**: Reject the rung and return to hypothesis formulation; a rung is never admitted with a warning attached.
- **Human Review Trigger**: A cost increase above 20 percent per answered request, or a rung proposed for a class its remedy column excludes.

**Checkpoint 5: Release Readiness (After Phase 5)**

- **Automated Check**: Every admitted unit carries a policy decision dated at or after assembly; zero citations resolve to generated artifacts; citation coverage over material claims meets the contract target; loop rounds within 3 retrieval and 2 verification; no loop parameter modified by retrieved content.
- **Agent Action on Pass**: Enter the staged release gate.
- **Agent Action on Failure**: Withhold release and return the unresolved claims and the units that failed policy revalidation.
- **Human Review Trigger**: Any unsupported material claim in the highest risk tier, or any evidence unit admitted from a remote boundary whose citations could not be verified locally.

**Checkpoint 6: Operating Integrity (After Phase 6)**

- **Automated Check**: All Phase 3 metrics recomputable from stored traces; trace identifiers propagated across 100 percent of remote boundaries; every hard gate passing; every alert classified as drift or regression; rollback manifest present for every migration.
- **Agent Action on Pass**: Continue operation and schedule the next measurement window.
- **Agent Action on Failure**: Suspend promotion and name the missing instrumentation or gate evidence.
- **Human Review Trigger**: Drift persisting across 2 consecutive windows, or any freshness objective breached on a highest-tier question class.

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

**Error Type 1: Failure Class Misdiagnosis**

- **Symptoms**: An admitted rung produces no measured improvement; a reranker is added and worst-slice recall does not move; embedding changes are made repeatedly with flat results.
- **Diagnostic Steps**: Recompute the attribution tests in order against the logged candidate set rather than against the admitted set only, and confirm whether answer-bearing spans appear anywhere in the candidates. Check whether the labelled spans resolve in the corpus version under test.
- **Resolution Protocol**: Option A, where no candidate overlaps a span, treat the case as class F1 and act on the index, chunking, analyzer, or corpus rather than on ranking. Option B, where overlap exists in candidates but not in the admitted set, treat the case as class F2 and act on fusion, reranking, or cut depth. Option C, where overlap exists in the admitted set, treat the case as class F3 and act on assembly, ordering, compression, or prompt, changing no retrieval component. Option D, where the answer is absent from the corpus, route to ingestion and remove the case from the retrieval attribution table.
- **Escalation Trigger**: Two consecutive admitted rungs producing less than a 2 percentage point movement on their declared primary metric escalate for attribution review; a third rung is not attempted on the same diagnosis.

**Error Type 2: Evaluation Set Contamination or Overfitting**

- **Symptoms**: Tuning-split improvements do not reproduce on the held-out split; the no-retrieval baseline scores unexpectedly well; gains shrink at each successive release.
- **Diagnostic Steps**: Re-run the no-retrieval baseline, recount contaminated cases, and compare the number of tuning cycles consumed against the declared cap. Verify that the frozen split hash matches its recorded value.
- **Resolution Protocol**: Option A, move contaminated cases to the diagnostic slice and rescore without them. Option B, discard the current tuning results and rebuild the tuning split from newly labelled cases, retaining the frozen split. Option C, where the frozen split hash has changed, treat every result derived from it as void and re-freeze a new split from unused cases.
- **Escalation Trigger**: Any detected read of the frozen split during an active trial voids the trial immediately; this class is never resolved by re-running the same comparison.

**Error Type 3: Unresolvable or Misattributed Citation**

- **Symptoms**: Citation keys that do not exist in the evidence bundle; offsets outside the cited chunk; citations pointing to summaries, hypothetical documents, generated representations, or inferred graph edges.
- **Diagnostic Steps**: Trace each failing key back through the bundle record to its chunk identifier and source version, and determine whether the resolver rejected the key or accepted a derived artifact.
- **Resolution Protocol**: Option A, mark the claim unsupported and re-retrieve using the claim and its missing qualifier, regenerating only the affected passage. Option B, where derived artifacts are being cited, restrict the citable set to original source content and re-run resolution. Option C, where the claim cannot be supported within the loop budget, qualify it explicitly or remove it. Option D, where the claim is material and in the highest risk tier, abstain and escalate with the bundle attached.
- **Escalation Trigger**: Any citation resolving to a generated artifact halts release and triggers a resolver defect review; the release is never permitted on the generator's assurance that the claim is correct.

**Error Type 4: Unbounded or Cycling Retrieval Loop**

- **Symptoms**: Budget consumed with flat evidence gain; identical query plans repeating; identical top-ranked chunk sets across rounds; groundedness decreasing as rounds increase.
- **Diagnostic Steps**: Compare plan and chunk-set hashes across rounds, and compute newly covered answer-bearing spans per round against the round's cost.
- **Resolution Protocol**: Option A, terminate on the repeated hash and answer only the supported parts with the missing evidence stated. Option B, change the transformation class rather than repeating one, selecting lexical expansion for terminology mismatch, decomposition for multi-hop structure, or alternate source routing for missing authority. Option C, reduce scope to a declared partial completion the contract admits. Option D, abstain and escalate with the loop trace attached.
- **Escalation Trigger**: A fourth retrieval round or a third verification round halts the request and returns a bounded failure; no loop continues on the expectation that remaining budget alone justifies it.

**Error Type 5: Authorization Leak Through Retrieval or Cache**

- **Symptoms**: Unauthorized identifiers, titles, snippets, counts, or score distributions in a response; a cache hit served across permission sets; cross-tenant evidence in a bundle.
- **Diagnostic Steps**: Determine whether policy was evaluated before ranking, whether it was re-evaluated before assembly, and whether the cache key bound tenant, authorization scope, policy version, and index manifest.
- **Resolution Protocol**: Option A, stop generation and tool execution, revoke the affected bundle, and invalidate every derived cache entry. Option B, restore the last trusted index manifest where the leak originated in an index build. Option C, re-run the authorization and adversarial suites before any further quality work resumes.
- **Escalation Trigger**: One automated remediation attempt is permitted; every confirmed authorization breach escalates to the security owner and the data owner regardless of remediation success.

**Error Type 6: Aggregate Gain Masking Slice Regression**

- **Symptoms**: Macro metrics improve while a named slice degrades; tail latency rises while p50 falls; stale-answer rate rises while correctness rises.
- **Diagnostic Steps**: Recompute per-slice deltas and the fifth-percentile per-slice value, and separate the change's effect on each critical slice from its effect on the aggregate.
- **Resolution Protocol**: Option A, reject the change and return to hypothesis formulation. Option B, adopt a modular route that applies the change only to the slices it helps. Option C, accept the change with a compensating control where the degraded slice is low risk and the degradation stays inside 2 percentage points, recording the tradeoff in the admission decision.
- **Escalation Trigger**: Any regression on a security, freshness, or highest-risk-tier slice blocks promotion outright and is never traded against an aggregate gain.

**Troubleshooting Decision Tree**:

```
RETRIEVAL SYSTEM FAILS A CHECKPOINT
├─ AUTHORIZATION DEFECT
│   ├─ Unauthorized content in candidates → HALT quality work; repair policy filter
│   ├─ Cache served across permission sets → Invalidate; rekey on scope and policy version
│   └─ Cross-tenant evidence observed → Roll back manifest; escalate to security owner
├─ ATTRIBUTION DEFECT
│   ├─ No candidate overlaps a span → Class F1; act on index, chunking, or corpus
│   ├─ Overlap in candidates only → Class F2; act on fusion, reranking, or cut depth
│   ├─ Overlap in admitted text → Class F3; act on assembly, ordering, or prompt
│   └─ Correct answer, zero citations → Class F4; act on citation gate and decontamination
├─ SELECTION DEFECT
│   ├─ Rung outside the remedy column → Reject without trial
│   ├─ More than one component changed → Rerun with one change per variant
│   └─ Tuning cycles above five → Reformulate the hypothesis
├─ EVIDENCE DEFECT
│   ├─ Citation resolves to a generated artifact → HALT release; restrict citable set
│   ├─ Citation key absent from bundle → Mark unsupported; re-retrieve or qualify
│   └─ Entailment fails on a resolved citation → Treat claim as unsupported
├─ LOOP DEFECT
│   ├─ Repeated plan or chunk-set hash → Terminate; answer supported parts only
│   ├─ Evidence gain below threshold → Stop; state missing evidence
│   └─ Round cap exceeded → Return bounded failure; escalate if high risk
└─ MEASUREMENT DEFECT
    ├─ Frozen split read during trial → Void the trial; re-freeze a new split
    ├─ Aggregate improves, slice regresses → Reject or route modularly
    └─ Metric not recomputable from traces → Instrument before promoting
```

### D. Performance Metrics and Continuous Learning

**Component Retrieval Metrics**:

- **Recall at candidate depth**: Cases whose candidate set contains an answer-bearing span (target: at least 90 percent overall, at least 80 percent on every critical slice).
- **Recall at admitted depth**: Cases whose admitted set contains an answer-bearing span (target: within 5 percentage points of recall at candidate depth; a larger gap indicates a class F2 problem).
- **Worst-slice recall**: Minimum per-slice recall at admitted depth, reported alongside the fifth-percentile per-slice value (target: no more than 15 percentage points below the macro average).
- **Subquestion coverage**: Required subquestions carrying at least one authoritative supporting passage (target: at least 95 percent).
- **Rerank lift**: Post-rerank ranking quality minus pre-rerank ranking quality, reported with its latency and cost deltas (target: positive and at least 5 percentage points, else the rung is retired).

**Generation, Citation, and Grounding Metrics**:

- **Citation coverage**: Material claims carrying a resolving citation, over all material claims (target: at least 95 percent; the remainder must be qualified or abstained).
- **Citation precision**: Resolved citations whose cited span entails the attached claim (target: at least 90 percent).
- **Groundedness**: Responses passing the entailment threshold over eligible responses (target: at least 90 percent).
- **Class F4 rate**: Correct answers carrying zero resolving citations (target: no more than 5 percent; a higher rate indicates the system is answering from parametric knowledge).
- **Abstention precision**: Abstentions confirmed correct under adjudication (target: at least 90 percent).
- **Access-control violation rate**: Unauthorized content reaching candidates, admitted text, responses, or caches (target: exactly zero, with any non-zero value blocking release).

**Operational and Robustness Metrics**:

- **Stage latency**: p50, p95, and p99 per stage against the Phase 1 allocation (target: p95 within budget for every stage, not only end to end).
- **Cost per answered request**: Total stage cost over accepted answers (target: within the declared budget; an increase above 20 percent requires human approval).
- **Evidence efficiency**: Supported material claims per thousand retrieved-context tokens (target: non-decreasing across releases).
- **Freshness compliance**: Answers whose newest required evidence sits inside the source freshness objective (target: at least 99 percent, with p95 visibility and deletion lag reported).
- **Perturbation stability**: Overlap of admitted evidence and answer consistency across paraphrase, typo, word-order, and language variants (target: at least 80 percent overlap).
- **Loop efficiency**: Success gain attributable to rounds beyond the first, average rounds per request, and budget exhaustion rate (target: positive gain per additional round, exhaustion below 5 percent).

**Log-Pattern Failure Detection**: Repeated identical query plans indicate a cycling loop. Rising cost with flat evidence gain indicates diminishing returns. High citation coverage with low citation precision indicates the resolver is admitting topically adjacent spans. Correctness rising while the class F4 rate rises indicates evaluation contamination rather than improvement. Recall stable while worst-slice recall falls indicates a slice-specific regression concealed by the aggregate. Cache hit rate rising while freshness compliance falls indicates cache keys omitting the index manifest or the policy version.

**Learning and Adaptation Mechanisms**:

- **Failure-to-case conversion**: Every adjudicated production failure becomes a labelled evaluation case with its slice labels attached, so that the set grows toward the observed failure distribution.
- **Rung justification review**: Each release re-examines whether every admitted rung still remedies a class above the retirement threshold, and retires the ones that do not.
- **Judge recalibration**: Model judges are recalibrated against blinded human labels whenever the judge version, the generator version, or the corpus mix changes.
- **Threshold recalibration**: Every numeric threshold is recomputed per deployment against observed outcomes; the values in this guide are deployment defaults rather than measured constants.

**Human-in-the-Loop Boundaries**: Relaxation of an evidence standard, relaxation of an abstention trigger, promotion of an architecture whose advantage appears only in the aggregate, approval of a cost increase above 20 percent per answered request, authorisation of retrieval exposure across an organisational trust boundary, and closure of any confirmed authorization breach are never automated.

***

## IV. Domain-Agnostic Application Guidance

This framework generalises across sectors because it governs the selection and verification of a retrieval architecture rather than the subject matter of any corpus. Its phases hold wherever a question class must be answered from an authorized body of evidence under a budget, and wherever an answer's support can be checked against retrieved text.

### 4.1 Cross-Domain Application Patterns

**Regulated financial and legal work**: The evidence standard is the binding constraint, not recall. Authority tier ordering separates enacted instruments from commentary, and a highly similar secondary source never outranks an authoritative record. Citation granularity is set at the provision or clause level, and compression is prohibited on clauses and numeric tables. The baseline sits at rung 2 because provisions, citations, and defined terms are lexical objects, and the dominant early failure class is F2 rather than F1. Abstention is preferred over an unverified completion, and the evidence bundle is a deliverable rather than a diagnostic artifact.

**Clinical and biomedical evidence synthesis**: Freshness objectives are short for guidance documents and long for foundational literature, so the freshness table carries per-source-type limits rather than one global limit. Contradiction retention is mandatory, since superseded and current recommendations must both surface with their validity intervals. Multi-hop questions relating a population, an intervention, and an outcome push the dominant class toward F1 on the multi-hop slice, which is the observable condition justifying rung 6 or rung 12. Access-controlled negatives dominate the evaluation set where records carry patient identity, and the blocking-defect rule applies without exception.

**Software engineering and codebase retrieval**: The corpus carries machine-parseable structure, so the structural index substitutes for the embedding path rather than supplementing it. Symbol definitions, call relations, and file hierarchies supply exact retrieval, and the answer-bearing span is a definition or a call site rather than a paragraph. The dominant early failure class is F3, because the matched symbol is retrieved while the surrounding contract, invariant, or caller expectation is not admitted, which is the observable condition justifying rung 7. Freshness objectives are measured in commits rather than in days.

**Industrial operations and field maintenance**: Multimodal evidence dominates, since answers depend on schematics, wiring diagrams, torque tables, and equipment photographs whose meaning does not survive text extraction. The evaluation set carries a table and figure slice with its own recall target, and citations resolve to page regions rather than to extracted sentences. Latency budgets are tight because a technician is waiting, so the loop budget is set to one retrieval round with escalation to a human rather than to a second round. Extracted numeric values are compared against the rendered source before admission.

**Customer-facing support and knowledge assistance**: Query volume is high, budgets per request are small, and the corpus changes continuously, so caching and freshness interact directly. Cache keys bind the canonical query, the filters, the authorization scope, the index manifest, the retrieval parameters, and the policy version, and a cached answer is reauthorized before release. Semantic caching is confined to low-risk stable intents with a similarity threshold calibrated on false-hit cost, and cache entries are never shared across tenants or permission sets. Abstention is cheap here and is preferred to a confident wrong answer, since the cost of a false answer exceeds the cost of an escalation.

### 4.2 Scale, Risk, and Latency Adaptation

- **Exploratory and single-session scope**: Operate without persistent infrastructure by reading a bounded set of authorized files at request time, matching lexically in process, and evaluating a small labelled set locally. Retain the contract, the evaluation set, and the failure attribution; drop only the durable index. This tier is unsuitable where persistence, concurrency, strict deletion, tenant isolation, or continuous freshness is required.
- **Default production scope**: Provision ingestion, a parser preserving structure, a chunking and identifier stage, one pinned embedding endpoint, one index supporting vector search and metadata filtering, a lexical index where identifiers matter, rank-based fusion, one reranker endpoint where first-stage precision is insufficient, citation-constrained generation, a versioned evaluation set with an executable harness, structured traces, and a refresh job with deletion support. This tier supports rungs 2 through 7 without a graph store or an agentic loop.
- **High-assurance scope**: Add a policy decision point for document-level and chunk-level authorization, an evaluation service supporting golden sets and judge calibration, a tracing backend, shadow and blue-green index cutover, and audit storage. Add a graph store, a multimodal parsing service, or a remote agent boundary only where a named query class has justified the corresponding rung.
- **Strict latency budgets**: Shorten the candidate pool and the reranked pool rather than removing the citation resolution gate, since removing the gate removes the only guarantee the system offers. Where latency forbids reranking, prefer rung 4 with a deeper first stage over rung 5 with a shallow pool.
- **High-risk and irreversible decisions**: Tighten the evidence standard to require independent corroboration, require entailment adjudication on 100 percent of resolved citations, bind the approval gate before release, and prefer abstention to an unverified answer. A single evidence standard across risk tiers is simultaneously too permissive for consequential answers and too costly for routine ones.

***

## V. Limitations and Considerations

**Selection depends on evaluation set quality**: The ladder directs architecture choice from measured failure attribution, and attribution is only as good as the labelled spans behind it. A set whose answer-bearing spans are labelled loosely will attribute class F1 failures as class F2 and send effort to the wrong stage. The mitigation is character-granular span labelling, the contamination certification in Step 2.3, and the requirement that unattributed failures stay at or below 5 percent before any selection decision is taken.

**Most thresholds here are deployment defaults**: The 5 percentage point admission threshold, the 2 percentage point critical-slice tolerance, the 160-case evaluation minimum, the 20-case slice minimum, the 40 percent frozen split, the 20 percent cost approval trigger, the 15 percentage point judge disagreement limit, and the retirement thresholds were chosen to be operable on first deployment rather than derived from a measured property of retrieval systems. The mitigation is the recalibration requirement in Step 6.3 and in Section III.D, which obliges each deployment to recompute thresholds against observed outcomes and to record the evidence for each change.

**Component metrics can be gamed by the labelling process**: Recall computed against spans that were themselves discovered by an early version of the retrieval system will favour that system. The mitigation is to source labels from adjudicated production failures and from sources located independently of the system under test, and to record labelling provenance so that a self-confirming set is detectable.

**Model judges are measurement instruments with their own error**: Groundedness, entailment, and relevance verdicts produced by a model carry disagreement against human labels that varies with domain and with model version. The mitigation is the calibration record in Step 2.3, the 15 percentage point disagreement ceiling, pinned judge versions, and the rule that a gate verdict from an uncalibrated judge is rejected.

**Retrieved content is an attack surface, and detection is incomplete**: Instructions can be embedded in text, in document layers, and in non-text modalities, and published evaluations of poisoning defences report that current protections are partial rather than complete. The mitigation is defence in depth rather than detection alone: evidence is delimited and marked untrusted, retrieval tools are separated from action tools, consequential actions require a policy decision or confirmation, adversarial cases sit in the evaluation set as a permanent slice, and no retrieved content may alter loop limits, permissions, or destinations.

**Cited benchmark figures were measured under specific conditions**: The improvement figures carried in the retrieval literature, including reported reductions in failed retrievals from contextual embedding and reported gains from pseudo-document expansion, were obtained on particular corpora with particular models. The mitigation is the admission trial in Phase 4, which requires the improvement to be reproduced on the deployment's own evaluation set before the rung is admitted; a published figure is a reason to run a trial, never a substitute for one.

**The ladder does not order every architecture unambiguously**: Cost ordering between graph-backed retrieval, multimodal retrieval, and memory-backed retrieval depends on corpus composition, and a deployment may find rung 13 cheaper than rung 12. The mitigation is that the climbing rule keys on the failure class remedy column rather than on the rung number, so rungs may be entered out of numeric order where the remedy map supports it; the numeric order encodes typical cost, not a mandatory sequence.

**Structural conformance is not evidential soundness**: A system can satisfy every checkpoint here, resolve every citation, and still answer from a corpus that is incomplete, biased, or wrong. The framework detects unsupported answers, not unsound sources. The mitigation is the authority tier ordering in Step 1.1 and the corpus gap list in Step 3.3, neither of which substitutes for human review of the corpus itself.

***

## VI. Conclusion and Summary

Advanced knowledge retrieval is a selection discipline before it is an implementation discipline. The determining question is not which retrieval technique is most capable but which one the measured failure distribution justifies, and that question cannot be answered without a declared contract and a frozen evaluation set that both exist before the first architecture is chosen. A team that establishes the contract, labels answer-bearing spans, measures the cheapest adequate baseline, and attributes every failure to exactly one class will climb the ladder only where climbing pays; a team that begins from a preferred architecture will accumulate components whose contribution nobody can state.

The two measurement disciplines that carry the most weight are the separation of component metrics from end-to-end metrics and the deterministic resolution of citations. Separation is what distinguishes a system that retrieves well and answers badly from one that answers well while retrieving badly, and no single quality figure can direct a remedy for either. Citation resolution is what converts a confident answer into a supported one: a citation that does not resolve to admitted text leaves its claim unsupported, whatever the generator asserts, and the correct responses are to retrieve again, qualify, or abstain.

A deployment introducing this framework should sequence the work rather than build the target architecture first. Declare the contract, build and freeze the evaluation set, measure the no-retrieval baseline, then measure the lowest satisfying rung with full tracing. Attribute failures, admit exactly one rung, and confirm it on the held-out split. Only then consider transformation, correction, graph, multimodal, memory, or agentic paths, each against a named class. Tooling supplies indexes, rerankers, and harnesses, but none of it substitutes for a contract, a labelled set, or an attribution table.

**Key Success Factors**:

- **Contract before architecture**: The question class, evidence standard, budget, and abstention path are declared before any retrieval method is named, so that selection is measurement rather than preference.
- **Evaluation before selection**: A frozen, decontaminated, span-labelled evaluation set exists before the first architecture trial, because a selection made without one cannot be justified or reversed on evidence.
- **Separated measurement**: Component retrieval metrics and end-to-end answer metrics are computed and reported apart, with per-slice values and worst-slice figures beside every aggregate.
- **One class, one remedy**: Every failure is attributed to exactly one of four classes, and every admitted component names the class it remedies, the slice it moves, and the measured delta.
- **Cheapest adequate rung**: The ladder is climbed one rung at a time against a measured gap and descended when the gap closes, since complexity that no longer earns its place is a defect.
- **Deterministic authority**: Software owns filtering, scoring arithmetic, budget enforcement, citation resolution, and metric computation, and an unresolved citation marks a claim unsupported regardless of model confidence.

By following this guide, AI agents can assemble retrieval systems whose every component is justified by evidence, whose answers carry support that resolves to authorized text, and whose degradation is detected as drift before it is reported as failure.

***

## VII. References and Further Reading

This guide is an operational restructuring of a single prose source. The corpus pointers below identify that source and the sibling guides bearing on particular steps. The external references that follow are transcribed from the originating prose guide as it cited them; they were not independently re-verified in the course of this conversion, and their titles and locations are reproduced rather than checked. Bounded searches performed during conversion confirmed that three positions in the source remain current practice: rank-based fusion of sparse and dense candidates followed by cross-encoder reranking over a bounded pool, the separation of component retrieval metrics from end-to-end answer metrics, and per-request routing between retrieval and long-context paths rather than a permanent choice between them. Those searches did not re-verify any individual entry below.

**Corpus pointers**:

- `Advanced Knowledge Retrieval: A Production Guide for Humans and AI Agents` — the originating prose guide from which this operational guide was derived. Source of the retrieval-need decision ladder, the infrastructure tiers, the corpus and provenance contract, the chunking and retrieval method inventories, the reranking and context assembly sequence, the graph construction requirements, the refinement and verification loops with their iteration caps, the long-context routing conditions, the multimodal and memory controls, the security and index lifecycle disciplines, the evaluation metric families and release gates, the logging field inventory, and the ten-step end-to-end workflow. It carries inline citations to primary literature and standards on contextual retrieval, rank fusion, query expansion, late interaction, graph retrieval, self-corrective retrieval, long-context tradeoffs, multimodal retrieval, agentic memory, evaluation frameworks, adversarial machine learning, and protocol security; the external references listed below are transcribed from those citations.
- `advanced_task_guides/authoring/guide_guidewriting.md` — the normative house-style specification. Source of the archetype, the step slot template, the mandatory Implementation Guidance subsection names, and the conformance envelope this guide was written against.
- `advanced_task_guides/knowledge-retrieval/guide_QueryTransformationRetrieval.md` — the rung 6 implementation guide. Owns the transformation catalogue, the diagnosis-to-treatment binding, and the intent-preservation check that this guide's rung 6 entry condition assumes.
- `advanced_task_guides/knowledge-retrieval/guide_HierarchicalIndexRetrieval.md` — the rung 7 implementation guide. Owns multi-level index construction, level descent, and the parent-child expansion caps this guide requires at that rung.
- `advanced_task_guides/knowledge-retrieval/guide_CorrectiveRAG.md` — the rung 8 implementation guide. Owns evaluator calibration, the verdict-to-action binding, and the bounded second round this guide's rung 8 entry condition assumes.
- `advanced_task_guides/knowledge-retrieval/guide_SelfRAG.md` — the rung 9 implementation guide. Owns the four reflection verdicts, claim-level support verification, and the abstention gate that carries the Class F4 remedy.
- `advanced_task_guides/knowledge-retrieval/guide_ModularRAG.md` — the rung 10 implementation guide. Owns module contracts, the versioned pipeline manifest, and the per-stage change isolation that makes rung-by-rung attribution reproducible.
- `advanced_task_guides/knowledge-retrieval/guide_AgenticRAG.md` — the rung 11 implementation guide. Owns the bounded control loop, the per-iteration progress test, and the stopping rules behind the loop budget and cycle detection named at that rung.
- `advanced_task_guides/knowledge-retrieval/guide_GraphRAG.md` — the rung 12 implementation guide. Owns graph construction, the query mode router, and the evidence serialisation rules behind the extraction cost and audit burden named at that rung.
- `advanced_task_guides/knowledge-retrieval/guide_MultimodalRAG.md` — the rung 13 implementation guide. Owns per-modality representation choice, citation granularity, and the parsing, region storage, and modality-specific attack surface named at that rung.
- `advanced_task_guides/knowledge-retrieval/guide_LatentKnowledgeRetrieval.md` — the latent side of rung 14. Owns the sense taxonomy separating derived latent state from parametric recall, and the admission rule governing the rung 0 no-retrieval option.
- `advanced_task_guides/knowledge-retrieval/guide_DeepResearchAgent.md` — the rung 15 implementation guide. Owns the research brief, the versioned question tree, credibility tiering, and the long-horizon budget control named at that rung.
- `advanced_task_guides/knowledge-retrieval/guide_CodebaseStructureRetrieval.md` — the structured-corpus specialisation, where a symbol graph and version history substitute for the lowest rungs rather than adding to them.
- `advanced_task_guides/planning/guide_MetaReasoning.md` — companion guidance on bounded control loops, stuck-state detection, and value-of-computation stopping rules, applicable to the loop bounding in Step 5.3.
- `advanced_task_guides/design-architecture/guide_TelemetryDesign.md` — companion guidance on event schema design, applicable to the trace instrumentation in Step 6.1.
- `advanced_task_guides/design-architecture/guide_MonitoringDesignConstraintAnalysis.md` — companion guidance on monitoring under constraint, applicable to the drift detection in Step 6.3.
- `advanced_task_guides/policy-risk/guide_InformationDependencyDisclosureRiskAnalysis.md` — companion guidance on disclosure exposure, applicable to the authorization and redaction requirements in Steps 2.1, 5.1, and 6.1.
- `advanced_task_guides/memory-management/guide_AgentMemoryManagement.md` — companion guidance on the memory tier that rung 14 introduces, including the boundary between retrieved corpus evidence and durable derived state.
- `advanced_task_guides/memory-management/guide_MemoryReadWriteOperations.md` — companion guidance on write gates, read-time revalidation, and admission control, applicable wherever retrieval results are promoted into durable memory.
- `advanced_task_guides/memory-management/guide_SemanticMemory.md` — companion guidance on durable factual state derived from validated evidence, applicable to rung 14 selection.
- `advanced_task_guides/memory-management/guide_EpisodicMemory.md` — companion guidance on interaction-scoped records with actor, time, outcome, and consent, applicable to longitudinal retrieval workflows.
- `advanced_task_guides/memory-management/guide_MemoryConsolidation.md` — companion guidance on consolidating repeated or authoritative support, applicable to the promotion rules that rung 14 requires.
- `advanced_task_guides/memory-management/guide_HierarchicalMemory.md` — companion guidance on tiered storage and expansion bounds, applicable to the parent-child expansion caps in rung 7.
- `advanced_task_guides/memory-management/guide_LatentMemoryNetworks.md` — companion guidance on derived latent state, applicable to the latent retrieval option within rung 14.
- `advanced_task_guides/knowledge-graphs/guide_KG_SchemaDesign.md` — companion guidance on schema definition before extraction, applicable to the graph construction prerequisites of rung 12.
- `advanced_task_guides/knowledge-graphs/guide_KG_EntityResolutionDedup.md` — companion guidance on conservative entity resolution and alias preservation, applicable to rung 12.
- `advanced_task_guides/knowledge-graphs/guide_KG_DataProvenanceEvidenceTracking.md` — companion guidance on edge-level provenance, applicable to the requirement that graph answers cite source passages rather than nodes or generated summaries.

**External references**: The entries below are transcribed from the originating prose guide's inline citations and are retained for auditability. This guide carries no inline numeric markers; the grouping is thematic.

*Chunking, fusion, and query transformation*

1. Anthropic, *Contextual Retrieval* — https://www.anthropic.com/engineering/contextual-retrieval
2. Elasticsearch, *RRF retriever* — https://www.elastic.co/docs/reference/elasticsearch/rest-apis/retrievers/rrf-retriever
3. Gao et al., *Precise Zero-Shot Dense Retrieval without Relevance Labels* (HyDE) — https://arxiv.org/abs/2212.10496
4. Wang et al., *Query2doc: Query Expansion with Large Language Models* — https://arxiv.org/abs/2303.07678
5. Santhanam et al., *ColBERTv2* — https://people.eecs.berkeley.edu/~matei/papers/2022/naacl_colbert_v2.pdf
6. MTEB repository — https://github.com/embeddings-benchmark/mteb/

*Graph, corrective, and multimodal retrieval*

7. Edge et al., *From Local to Global: A Graph RAG Approach to Query-Focused Summarization* — https://arxiv.org/abs/2404.16130
8. Microsoft Research, *Project GraphRAG* — https://www.microsoft.com/en-us/research/project/graphrag/
9. Asai et al., *Self-RAG* — https://arxiv.org/abs/2310.11511
10. Yan et al., *Corrective Retrieval Augmented Generation* — https://openreview.net/pdf/39c7f80044f08ddfc2afc7d551801965d7fef562.pdf
11. REAL-MM-RAG — https://aclanthology.org/2025.acl-long.1528/
12. VisRAG — https://arxiv.org/html/2410.10594
13. Xu et al., *A-MEM: Agentic Memory for LLM Agents* — https://arxiv.org/abs/2502.12110

*Context assembly and long-context routing*

14. Liu et al., *Lost in the Middle* — https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00638/119630/Lost-in-the-Middle-How-Language-Models-Use-Long
15. Li et al., *Retrieval Augmented Generation or Long-Context LLMs?* — https://arxiv.org/abs/2407.16833
16. Jiang et al., *LongLLMLingua* — https://arxiv.org/abs/2310.06839

*Evaluation frameworks and benchmarks*

17. RAGAS documentation — https://docs.ragas.io/en/stable/howtos/cli/rag_eval/
18. Saad-Falcon et al., *ARES* — https://arxiv.org/abs/2311.09476
19. Ru et al., *RAGChecker* — https://arxiv.org/abs/2408.08067
20. NIST, *Overview of the TREC 2025 Retrieval Augmented Generation Track* — https://trec.nist.gov/pubs/trec34/papers/Overview_rag.pdf
21. Li et al., *RAGPerf: An End-to-End Benchmarking Framework for Retrieval-Augmented Generation Systems* — https://arxiv.org/html/2603.10765v1

*Security, privacy, and isolation*

22. OWASP, *LLM01:2025 Prompt Injection* — https://genai.owasp.org/llmrisk/llm01-prompt-injection/
23. OWASP, *RAG Security Cheat Sheet* — https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html
24. Zou et al., *Benchmarking Poisoning Attacks against Retrieval-Augmented Generation* — https://arxiv.org/abs/2505.18543
25. Pinecone, *Implement multitenancy* — https://docs.pinecone.io/guides/index-data/implement-multitenancy
26. NIST, *Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations*, AI 100-2e2025 — https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-2e2025.pdf

*Instrumentation and interoperability protocols*

27. OpenTelemetry, *Generative AI semantic conventions* — https://opentelemetry.io/docs/specs/semconv/gen-ai/
28. Model Context Protocol specification, version 2026-07-28 — https://modelcontextprotocol.io/specification/2026-07-28
29. NSA, *Model Context Protocol Security Design Considerations for AI-Driven Automation*, May 2026 — https://media.defense.gov/2026/Jun/02/2003943289/-1/-1/0/CSI_MCP_SECURITY.PDF
30. Google, *Announcing the Agent2Agent Protocol* — https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/

